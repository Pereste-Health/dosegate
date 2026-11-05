import hashlib, json, os, random, re, sys

SRC = os.environ.get("SYNTHEA_FHIR_DIR", "")
OUT = os.path.join(os.path.dirname(__file__), "data")
N_PATIENTS = 120
MAX_ORDERS = 4
ORAL = {"system": "http://snomed.info/sct", "code": "26643006"}
SUBLINGUAL = {"system": "http://snomed.info/sct", "code": "37839007"}
STRENGTH = re.compile(r"(\d+(?:\.\d+)?) MG\b")
PERTURB_FACTORS = ["0.5", "1.5", "2", "3"]
PERTURB_TIMINGS = [(1, 1, "d"), (2, 1, "d"), (3, 1, "d"), (1, 8, "h"), (1, 12, "h"), (1, 1, "wk")]


def ingredient(display):
    return STRENGTH.split(display)[0].strip().lower()


def normalize(r):
    di = r.get("dosageInstruction", [])
    if r.get("status") != "active" or len(di) != 1 or not di[0].get("doseAndRate"):
        return None
    disp = r["medicationCodeableConcept"]["coding"][0]["display"]
    strengths = STRENGTH.findall(disp)
    if len(strengths) != 1 or "Tablet" not in disp and "Capsule" not in disp:
        return None
    rep = di[0].get("timing", {}).get("repeat", {})
    if not all(k in rep for k in ("frequency", "period", "periodUnit")) or rep["period"] != int(rep["period"]):
        return None
    return {
        "drug": ingredient(disp),
        "strength_mg": strengths[0],
        "route": SUBLINGUAL if "Sublingual" in disp else ORAL,
        "timing": (int(rep["frequency"]), int(rep["period"]), rep["periodUnit"]),
        "source_display": disp,
    }


def mul(dec, factor):
    a, b = (dec + ".").split(".")[:2] if "." in dec else (dec, "")
    q = round(float(dec) * float(factor), 6)
    s = f"{q:.6f}".rstrip("0").rstrip(".")
    return s


def to_fhir(oid, o, dose_mg, timing):
    f, p, u = timing
    return {
        "resourceType": "MedicationRequest", "id": oid, "status": "active", "intent": "order",
        "medicationCodeableConcept": {"text": o["drug"]},
        "dosageInstruction": [{
            "route": {"coding": [o["route"]]},
            "timing": {"repeat": {"frequency": f, "period": p, "periodUnit": u}},
            "doseAndRate": [{"doseQuantity": {"value": json.loads(dose_mg), "unit": "mg", "code": "mg"}}],
        }],
    }


def main():
    files = sorted(x for x in os.listdir(SRC) if x.endswith(".json") and not x.startswith("._"))
    random.Random(20261104).shuffle(files)
    cases = []
    for name in files:
        bundle = json.load(open(os.path.join(SRC, name)))
        orders, seen = [], set()
        for e in bundle.get("entry", []):
            o = normalize(e["resource"])
            if o and o["drug"] not in seen:
                seen.add(o["drug"])
                orders.append(o)
        if not orders:
            continue
        orders = orders[:MAX_ORDERS]
        h = int(hashlib.sha256(name.encode()).hexdigest(), 16)
        for variant in ("natural", "perturbed"):
            mrs = []
            for i, o in enumerate(orders):
                oid = f"m{i + 1}"
                if variant == "natural":
                    mrs.append(to_fhir(oid, o, o["strength_mg"], o["timing"]))
                else:
                    k = PERTURB_FACTORS[(h >> (4 * i)) % len(PERTURB_FACTORS)]
                    t = PERTURB_TIMINGS[(h >> (4 * i + 16)) % len(PERTURB_TIMINGS)]
                    mrs.append(to_fhir(oid, o, mul(o["strength_mg"], k), t))
            cases.append({"case_id": f"{name[:-5]}:{variant}", "variant": variant, "source_bundle": name,
                          "medicationRequests": mrs})
        if len(cases) >= 2 * N_PATIENTS:
            break
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "cases.jsonl"), "w") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    n_orders = sum(len(c["medicationRequests"]) for c in cases)
    print(f"{len(cases)} cases, {n_orders} orders", file=sys.stderr)


if __name__ == "__main__":
    main()
