import json, os, random, sys

if not os.environ.get("SYNTHEA_FHIR_DIR"):
    sys.exit("set SYNTHEA_FHIR_DIR to the folder of Synthea FHIR bundles")
import build_cases as bc

SRC = os.environ["SYNTHEA_FHIR_DIR"]
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "free_text_share.json")
CASES = os.path.join(HERE, "data", "cases.jsonl")
N_PATIENTS = 120
FIELDS = ("note", "dosageInstruction.text", "dosageInstruction.additionalInstruction",
          "dosageInstruction.patientInstruction")
PHRASES = ("as required", "as needed")


def free_text(mr):
    di = mr.get("dosageInstruction", [])
    return {
        "note": bool(mr.get("note")),
        "dosageInstruction.text": any(bool(d.get("text")) for d in di),
        "dosageInstruction.additionalInstruction": any(bool(d.get("additionalInstruction")) for d in di),
        "dosageInstruction.patientInstruction": any(bool(d.get("patientInstruction")) for d in di),
    }


def has_as_needed_phrase(di):
    return any(any(p in (d.get("text") or "").lower() for p in PHRASES) for d in di)


def tally(bundles):
    t = {"bundles": 0, "bundles_with_active_mr_with_free_text": 0, "active_mr": 0,
         "active_mr_with_free_text": 0, "active_single_dosage_mr": 0,
         "active_single_dosage_mr_with_free_text": 0,
         "active_mr_by_field": {f: 0 for f in FIELDS},
         "flagged_orders_with_more_than_one_dosage_instruction": 0,
         "flagged_orders_with_as_needed_phrase_without_flag": 0}
    rows = {}
    for bundle in bundles:
        t["bundles"] += 1
        bundle_flag = False
        for e in bundle.get("entry", []):
            mr = e.get("resource", {})
            if mr.get("resourceType") != "MedicationRequest" or mr.get("status") != "active":
                continue
            t["active_mr"] += 1
            found = free_text(mr)
            for f in FIELDS:
                t["active_mr_by_field"][f] += found[f]
            flagged = any(found.values())
            t["active_mr_with_free_text"] += flagged
            bundle_flag = bundle_flag or flagged
            if len(mr.get("dosageInstruction", [])) == 1:
                t["active_single_dosage_mr"] += 1
                t["active_single_dosage_mr_with_free_text"] += flagged
            if not flagged:
                continue
            di = mr.get("dosageInstruction", [])
            if len(di) > 1:
                t["flagged_orders_with_more_than_one_dosage_instruction"] += 1
            if has_as_needed_phrase(di) and not any(d.get("asNeededBoolean") is True for d in di):
                t["flagged_orders_with_as_needed_phrase_without_flag"] += 1
            for d in di:
                text, addl = d.get("text"), d.get("additionalInstruction")
                key = json.dumps([text, addl], sort_keys=True)
                row = rows.setdefault(key, {"dosageInstruction.text": text,
                                            "dosageInstruction.additionalInstruction": addl,
                                            "orders": 0, "asNeededBoolean_true": 0})
                row["orders"] += 1
                row["asNeededBoolean_true"] += d.get("asNeededBoolean") is True
        t["bundles_with_active_mr_with_free_text"] += bundle_flag
    t["share_of_bundles_with_active_mr_with_free_text"] = round(
        t["bundles_with_active_mr_with_free_text"] / t["bundles"], 4)
    t["share_of_active_mr_with_free_text"] = round(t["active_mr_with_free_text"] / t["active_mr"], 4)
    t["share_of_active_single_dosage_mr_with_free_text"] = round(
        t["active_single_dosage_mr_with_free_text"] / t["active_single_dosage_mr"], 4)
    t["flagged_order_texts"] = sorted(
        ({**row, "asNeededBoolean_absent_or_false": row["orders"] - row["asNeededBoolean_true"]}
         for row in rows.values()),
        key=lambda row: (-row["orders"], str(row["dosageInstruction.text"])))
    return t


def load(name):
    with open(os.path.join(SRC, name)) as f:
        return json.load(f)


files = sorted(x for x in os.listdir(SRC) if x.endswith(".json") and not x.startswith("._"))
random.Random(20261104).shuffle(files)

selected_names, selected = [], []
for name in files:
    bundle = load(name)
    if any(bc.normalize(e["resource"]) for e in bundle.get("entry", [])):
        selected_names.append(name)
        selected.append(bundle)
        if len(selected) == N_PATIENTS:
            break

with open(CASES) as f:
    case_names = {json.loads(line)["source_bundle"] for line in f}

result = {
    "source_directory": os.path.basename(os.path.normpath(SRC)),
    "bundle_files": len(files),
    "patients": {
        "selection": "first 120 bundles, in build_cases.py shuffle order (seed 20261104), with at least one order that the normalization keeps",
        "same_bundles_as_cases_jsonl": set(selected_names) == case_names,
        **tally(selected),
    },
    "all_bundles": tally(load(name) for name in files),
}

with open(OUT, "w") as f:
    json.dump(result, f, indent=2)
    f.write("\n")

for key in ("patients", "all_bundles"):
    t = result[key]
    print(key, {k: v for k, v in t.items() if k not in ("active_mr_by_field", "flagged_order_texts")}, file=sys.stdout)
    print(key, "by field", t["active_mr_by_field"], file=sys.stdout)
    for row in t["flagged_order_texts"]:
        print(key, row, file=sys.stdout)
print("same_bundles_as_cases_jsonl", result["patients"]["same_bundles_as_cases_jsonl"])
