import collections, json, os, re, subprocess, sys

if not os.environ.get("SYNTHEA_FHIR_DIR"):
    sys.exit("set SYNTHEA_FHIR_DIR to the folder of Synthea FHIR bundles")
SRC = os.environ["SYNTHEA_FHIR_DIR"]
HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.environ.get("DOSEGATE", os.path.join(HERE, "..", ".lake", "build", "bin", "dosegate"))
OUT = os.path.join(HERE, "data", "coded_timing_check.json")
PHRASES = ("Every four to six hours (qualifier value)", "Every six hours (qualifier value)",
           "Every seventy two hours (qualifier value)", "Every twelve hours as required (qualifier value)",
           "Every four hours (qualifier value)")
STRENGTH = re.compile(r"(\d+(?:\.\d+)?) MG\b")
ORAL = {"system": "http://snomed.info/sct", "code": "26643006"}
TEMPLATE = "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}, which is {{daily:m1}}."


def render(order, flags):
    req = {"medicationRequests": [order], "output": TEMPLATE}
    r = subprocess.run([GATE, "render"] + flags, input=json.dumps(req), capture_output=True, text=True)
    res = json.loads(r.stdout)
    return res["status"], res.get("reason"), res.get("text")


def as_raw(resource):
    order = json.loads(json.dumps(resource))
    order["id"] = "m1"
    order["subject"] = {"reference": "Patient/p1"}
    return order


def as_structured(resource):
    disp = (resource.get("medicationCodeableConcept") or {}).get("coding", [{}])[0].get("display", "")
    found = STRENGTH.findall(disp)
    if len(found) != 1:
        return None
    order = as_raw(resource)
    order["medicationCodeableConcept"] = {"text": STRENGTH.split(disp)[0].strip().lower()}
    dosage = order["dosageInstruction"][0]
    dosage["route"] = {"coding": [ORAL]}
    dosage["doseAndRate"] = [{"doseQuantity": {"value": float(found[0]), "unit": "mg", "code": "mg"}}]
    return order


def main():
    files = sorted(x for x in os.listdir(SRC) if x.endswith(".json") and not x.startswith("._"))
    raw_by_phrase = collections.defaultdict(lambda: {"orders": 0, "printed": 0, "reasons": collections.Counter()})
    struct_by_phrase = collections.defaultdict(lambda: {"orders": 0, "printed": 0, "reasons": collections.Counter(),
                                                        "default_mode_printed": 0,
                                                        "printed_phrases": collections.Counter()})
    unstructured = collections.Counter()
    for name in files:
        with open(os.path.join(SRC, name)) as f:
            bundle = json.load(f)
        for e in bundle.get("entry", []):
            r = e.get("resource", {})
            if r.get("resourceType") != "MedicationRequest" or r.get("status") != "active":
                continue
            di = r.get("dosageInstruction", [])
            if len(di) != 1 or di[0].get("text") not in PHRASES:
                continue
            phrase = di[0]["text"]
            status, reason, text = render(as_raw(r), ["--ignore-free-text"])
            raw = raw_by_phrase[phrase]
            raw["orders"] += 1
            if status == "ok":
                raw["printed"] += 1
            else:
                raw["reasons"][reason] += 1
            s = as_structured(r)
            if s is None:
                unstructured[phrase] += 1
                continue
            status, reason, text = render(s, ["--ignore-free-text"])
            row = struct_by_phrase[phrase]
            row["orders"] += 1
            if status == "ok":
                row["printed"] += 1
                row["printed_phrases"][text.split(" by mouth ", 1)[1] if " by mouth " in text else text] += 1
                if render(s, [])[0] == "ok":
                    row["default_mode_printed"] += 1
            else:
                row["reasons"][reason] += 1
    result = {
        "source_directory": os.path.basename(os.path.normpath(SRC)),
        "template": TEMPLATE,
        "flags": "--ignore-free-text (structured orders also tested without the flag)",
        "one_order_per_request": True,
        "raw_orders_as_recorded": {p: {"orders": v["orders"], "printed": v["printed"],
                                       "blocked_by_reason": dict(v["reasons"])}
                                   for p, v in raw_by_phrase.items()},
        "structured_orders_with_one_strength_in_mg": {p: {"orders": v["orders"], "printed": v["printed"],
                                                          "blocked_by_reason": dict(v["reasons"]),
                                                          "printed_without_flag": v["default_mode_printed"],
                                                          "printed_phrases_after_route": dict(v["printed_phrases"].most_common())}
                                                      for p, v in struct_by_phrase.items()},
        "structured_orders_not_normalizable": dict(unstructured),
    }
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
