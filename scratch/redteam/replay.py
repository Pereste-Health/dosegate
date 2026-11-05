import json, subprocess, time
BIN = "/Volumes/T7/Dosing_formal_verification/.lake/build/bin/dosegate"
CHART = json.load(open("/Volumes/T7/Dosing_formal_verification/scratch/redteam/chart.json"))

def send(req_text, timeout=60):
    t = time.time()
    try:
        p = subprocess.run([BIN, "render"], input=req_text.encode("utf-8"), capture_output=True, timeout=timeout)
        out = p.stdout.decode("utf-8", "replace").strip()
        return p.returncode, out, round(time.time() - t, 2)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", timeout

TEXT = [
 ("text_fivemg_glued", "lexicon bug", "Take {{drug:m1}} fivemg."),
 ("text_tenmg_glued", "lexicon bug", "Take {{drug:m1}} {{dose:m1}}, tenmg total."),
 ("text_tenunits_glued", "lexicon bug", "Take {{drug:m2}} {{dose:m2}} and tenunits."),
 ("text_dbl", "lexicon boundary", "Take {{drug:m5}} {{dose:m5}}, dbl."),
 ("text_tripled", "lexicon boundary", "Take {{drug:m1}} {{dose:m1}}, tripled on Sunday."),
 ("text_roman_ii_before_dose", "lexicon boundary", "Take {{drug:m1}} ii {{dose:m1}}."),
 ("text_gms", "lexicon boundary", "Take {{drug:m1}} {{dose:m1}} gms."),
 ("text_IUs", "lexicon boundary", "Take {{drug:m2}} IUs."),
 ("text_ampoules", "lexicon boundary", "Take {{drug:m2}} ampoules."),
 ("text_IV_for_SC_insulin", "meaning, route", "Take {{drug:m2}} {{dose:m2}} IV."),
 ("text_by_mouth_for_SC_heparin", "meaning, route", "Take {{drug:m6}} {{dose:m6}} by mouth."),
 ("text_intravenously_for_SC_insulin", "meaning, route", "Take {{drug:m2}} {{dose:m2}} intravenously."),
 ("text_IV_route_missing_in_chart", "meaning, route", "Give {{drug:m5}} {{dose:m5}} IV."),
 ("text_every_hour_frequency_missing_in_chart", "meaning, frequency", "Take {{drug:m5}} {{dose:m5}} every hour."),
 ("text_daily_for_twice_daily_metformin", "meaning, frequency", "Take {{drug:m1}} {{dose:m1}} {{route:m1}} daily."),
 ("text_daily_for_weekly_alendronate", "meaning, frequency", "Take {{drug:m8}} {{dose:m8}} {{route:m8}} every day."),
 ("text_hourly_for_q4h_prn", "meaning, frequency", "Take {{drug:m4}} {{dose:m4}} hourly."),
 ("text_as_needed_added_to_scheduled_insulin", "meaning, frequency", "Take {{drug:m2}} {{dose:m2}} as needed."),
 ("text_every_other_day_metformin", "meaning, frequency", "Take {{drug:m1}} {{dose:m1}} every other day."),
 ("text_drug_name_before_slot", "meaning, drug", "Take Coumadin {{drug:m1}} {{dose:m1}}."),
 ("text_restart_stopped_lisinopril", "meaning, drug", "Restart lisinopril as before, then {{drug:m1}} {{dose:m1}}."),
 ("text_do_not_take_inverts", "meaning, negation", "Do not take {{drug:m2}} {{dose:m2}}."),
 ("text_as_much_as_you_like", "meaning, qualifier", "Take {{drug:m1}} {{dose:m1}}, as much as you like."),
 ("text_at_most", "meaning, qualifier", "Take at most {{drug:m1}} {{dose:m1}}."),
]

def chart_with(mod):
    c = json.loads(json.dumps(CHART))
    mod(c)
    return c

def m(c, id_):
    return [e["resource"] for e in c["entry"] if e["resource"]["id"] == id_][0]

def set_field(id_, path, value):
    def f(c):
        r = m(c, id_)
        d = r["dosageInstruction"][0]
        cur = d
        for k in path[:-1]:
            cur = cur.setdefault(k, {})
        cur[path[-1]] = value
    return f

def remove_field(id_, path):
    def f(c):
        r = m(c, id_)
        d = r["dosageInstruction"][0]
        cur = d
        for k in path[:-1]:
            cur = cur[k]
        cur.pop(path[-1], None)
    return f

def rjson(obj, text_out):
    return json.dumps({"bundle": obj, "output": text_out}, ensure_ascii=False)

def fhir_case(name, cls, mod, out):
    c = chart_with(mod)
    return (name, cls, rjson(c, out))

FHIR = []
def addf(*a): FHIR.append(fhir_case(*a))
OUT_F = "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}."
addf("fhir_doNotPerform_true", "spec gap, chart prohibition read as instruction",
     lambda c: m(c, "m1").update({"doNotPerform": True}), OUT_F)
addf("fhir_intent_proposal", "spec gap",
     lambda c: m(c, "m1").update({"intent": "proposal"}), OUT_F)
addf("fhir_frequencyMax_4", "spec gap, range collapsed to minimum",
     set_field("m1", ["timing", "repeat"], {"frequency": 2, "frequencyMax": 4, "period": 1, "periodUnit": "d"}), OUT_F)
addf("fhir_doseQuantity_comparator", "spec gap, comparator dropped",
     set_field("m1", ["doseAndRate"], [{"doseQuantity": {"value": 500, "comparator": "<", "code": "mg"}}]), OUT_F)
addf("fhir_route_conflict_IV_first", "chart ambiguity, first SNOMED coding wins",
     set_field("m1", ["route"], {"coding": [{"system": "http://snomed.info/sct", "code": "47625008"}, {"system": "http://snomed.info/sct", "code": "26643006"}]}), OUT_F)
addf("fhir_drug_name_with_strength", "chart name text, not checked",
     lambda c: m(c, "m1")["medicationCodeableConcept"].update({"text": "Metformin 1000 MG Oral Tablet"}), OUT_F)
addf("fhir_drug_name_bidi_override", "chart name text, not checked",
     lambda c: m(c, "m1")["medicationCodeableConcept"].update({"text": "metformin ‮ 05 gm"}), OUT_F)
addf("fhir_asNeeded_string_false", "coerced to as needed",
     set_field("m2", ["asNeededBoolean"], "false"), "Take {{drug:m2}} {{dose:m2}} {{frequency:m2}}.")

RAW_DOS = []
base = json.dumps({"bundle": CHART, "output": "Take {{drug:m1}} {{dose:m1}}."}, ensure_ascii=False)
for exp in ["1e10000", "1e30000"]:
    raw = base.replace('"value": 500, "code": "mg"', '"value": %s, "code": "mg"' % exp)
    RAW_DOS.append(("fhir_dose_value_" + exp, "DoS, time grows superlinearly with digit count", raw))

results = []
for name, cls, out in TEXT:
    req = json.dumps({"bundle": CHART, "output": out}, ensure_ascii=False)
    rc, resp, t = send(req)
    results.append({"id": name, "class": cls, "request": req, "exit": rc, "response": resp, "seconds": t})
for name, cls, req in FHIR:
    rc, resp, t = send(req)
    results.append({"id": name, "class": cls, "request": req, "exit": rc, "response": resp, "seconds": t})
for name, cls, req in RAW_DOS:
    rc, resp, t = send(req, timeout=120)
    results.append({"id": name, "class": cls, "request": req[:300] + "...", "exit": rc, "response": resp[:200], "seconds": t})
with open("/Volumes/T7/Dosing_formal_verification/scratch/redteam/results.jsonl", "w") as f:
    for r in results:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
for r in results:
    print(r["id"], r["exit"], r["seconds"], r["response"][:150])
