import json, os, subprocess, sys
sys.path.insert(0, "/Volumes/T7/tmp-dg/s15_checks")
import importlib.util
spec = importlib.util.spec_from_file_location("ct", "/Volumes/T7/tmp-dg/s15_checks/coded_timing_check_v23_stripped.py")
ct = importlib.util.module_from_spec(spec); spec.loader.exec_module(ct)
SRC = "/Volumes/T7/hearth-datasets/synthea/bundles_v1/fhir"
n = 0
for name in sorted(os.listdir(SRC)):
    if not name.endswith(".json") or name.startswith("._"): continue
    b = json.load(open(os.path.join(SRC, name)))
    for e in b.get("entry", []):
        r = e.get("resource", {})
        if r.get("resourceType") != "MedicationRequest" or r.get("status") != "active": continue
        di = r.get("dosageInstruction", [])
        if len(di) == 1 and di[0].get("text") == "Every twelve hours as required (qualifier value)":
            s = ct.as_structured(r)
            if s is None: continue
            print(json.dumps(s, indent=1)[:1800])
            print("KEYS", sorted(r.keys()))
            st, reason, text = ct.render(s, ["--ignore-free-text"])
            print(st, reason, text); print(json.dumps(ct.as_raw(r)["dosageInstruction"], indent=0)[:900]); print(ct.as_structured(r)["dosageInstruction"]); print(json.dumps(r.get("medicationCodeableConcept"))[:300]); sys.exit(0)
            sys.exit(0)
