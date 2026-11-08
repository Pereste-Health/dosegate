import json, os, subprocess

OUT = "/Volumes/T7/tmp-dg/s15_checks"
BIN = "/Volumes/T7/Dosing_formal_verification/.lake/build/bin/dosegate"
T_ONE = "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}."
T_TWO = "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}. Take {{drug:m2}} {{dose:m2}} {{route:m2}} {{frequency:m2}}."
T_NONE = "Here is your medicine list."
ORAL = {"coding": [{"system": "http://snomed.info/sct", "code": "26643006", "display": "Oral route"}]}
SUBQ = {"coding": [{"system": "http://snomed.info/sct", "code": "34206005", "display": "Subcutaneous route"}]}


def order(rid, name, value, unit="mg", freq=1, period_unit="d", status="active", route=ORAL, **extra):
    dosage = {
        "timing": {"repeat": {"frequency": freq, "period": 1, "periodUnit": period_unit}},
        "doseAndRate": [{"doseQuantity": {"value": value, "unit": unit, "system": "http://unitsofmeasure.org", "code": unit}}],
    }
    if route is not None:
        dosage["route"] = route
    if "asNeededBoolean" in extra:
        dosage["asNeededBoolean"] = extra.pop("asNeededBoolean")
    dosage.update(extra.pop("dosage_extra", {}))
    r = {"resourceType": "MedicationRequest", "id": rid, "status": status, "intent": "order",
         "medicationCodeableConcept": {"text": name}, "subject": {"reference": "Patient/pat1"},
         "dosageInstruction": [dosage]}
    r.update(extra)
    return r


CASES = []


def case(name, meds, output, flags=(), mode="render"):
    CASES.append((name, meds, output, list(flags), mode))


# 1. Superseded orders (priorPrescription): m1 replaces m2
lis_old = lambda: order("m2", "lisinopril", 10, freq=2)
for form, ref in [("exact", "MedicationRequest/m2"), ("urn", "urn:uuid:m2"), ("bare", "m2")]:
    new = lambda ref=ref: order("m1", "lisinopril", 20, freq=1, priorPrescription={"reference": ref})
    for tname, tmpl in [("two", T_TWO), ("m1only", T_ONE), ("none", T_NONE)]:
        for fl in [(), ("--allow-omissions",)]:
            case(f"sup_{form}_{tname}_{'omit' if fl else 'default'}", [new(), lis_old()], tmpl, fl)
    case(f"sup_{form}_fallback", [new(), lis_old()], T_TWO, (), "fallback")

# 2. Held and stopped orders
warf_dnp = order("m2", "warfarin", 5, freq=1, doNotPerform=True)
warf_hold = order("m2", "warfarin", 5, freq=1, status="on-hold")
warf_stop = order("m2", "warfarin", 5, freq=1, status="stopped")
met = lambda: order("m1", "metformin", 500, freq=2)
for label, w in [("donotperform", warf_dnp), ("onhold", warf_hold), ("stopped", warf_stop)]:
    case(f"held_{label}_m1only", [met(), w], T_ONE)
    case(f"held_{label}_m1only_omit", [met(), w], T_ONE, ("--allow-omissions",))
    case(f"held_{label}_fallback", [met(), w], T_ONE, (), "fallback")
case("held_donotperform_slot_on_held", [met(), warf_dnp], "Take {{drug:m2}} {{dose:m2}} {{route:m2}} {{frequency:m2}}.")
case("held_donotperform_default_none", [met(), warf_dnp], T_NONE)

# 3. Reported orders
rep_bool = order("m2", "warfarin", 5, freq=1, reportedBoolean=True)
rep_ref = order("m2", "warfarin", 5, freq=1, reportedReference={"reference": "Patient/pat1"})
for label, w in [("boolean", rep_bool), ("reference", rep_ref)]:
    case(f"reported_{label}_m1only", [met(), w], T_ONE)
    case(f"reported_{label}_m1only_omit", [met(), w], T_ONE, ("--allow-omissions",))
    case(f"reported_{label}_none_omit", [met(), w], T_NONE, ("--allow-omissions",))
    case(f"reported_{label}_fallback", [met(), w], T_ONE, (), "fallback")

# 4. Coded timing and free text
q46 = "Every four to six hours (qualifier value)"
ft_struct = order("m1", "acetaminophen", 325, freq=4, dosage_extra={"text": q46})
ft_struct_nonote = order("m1", "acetaminophen", 325, freq=4, dosage_extra={})
ft_note = order("m1", "acetaminophen", 325, freq=4, note=[{"text": "Take with food"}])
case("ft_q46_default", [ft_struct], T_ONE)
case("ft_q46_ignore", [ft_struct], T_ONE, ("--ignore-free-text",))
case("ft_q46_ignore_rdaily", [ft_struct], "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}, which is {{daily:m1}}.", ("--ignore-free-text",))
case("ft_q46_nofreetext_ignore", [ft_struct_nonote], T_ONE, ("--ignore-free-text",))
case("ft_note_default", [ft_note], T_ONE)
case("ft_note_ignore", [ft_note], T_ONE, ("--ignore-free-text",))
raw12 = {"resourceType": "MedicationRequest", "id": "m1", "status": "active", "intent": "order",
         "medicationCodeableConcept": {"text": "acetaminophen"}, "subject": {"reference": "Patient/pat1"},
         "dosageInstruction": [{"text": "Every twelve hours as required (qualifier value)", "asNeededBoolean": False}]}
case("ft_raw12_ignore", [raw12], T_ONE, ("--ignore-free-text",))
struct12 = order("m1", "acetaminophen", 500, freq=2, dosage_extra={"text": "Every twelve hours as required (qualifier value)", "asNeededBoolean": False})
case("ft_struct12_ignore", [struct12], T_ONE, ("--ignore-free-text",))
case("ft_struct12_default", [struct12], T_ONE)

# 5. Weekly and as-needed lines
mtx = order("m1", "methotrexate", 10, freq=1, period_unit="wk")
case("weekly_render", [mtx], T_ONE)
case("weekly_render_daily", [mtx], "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}, which is {{daily:m1}}.")
case("weekly_fallback", [mtx], T_ONE, (), "fallback")
oxy = order("m1", "oxycodone hydrochloride", 5, freq=1, asNeededBoolean=True)
case("prn_fallback", [oxy], T_ONE, (), "fallback")
case("prn_render", [oxy], T_ONE)
oxy_reason = order("m1", "oxycodone hydrochloride", 5, freq=1, asNeededBoolean=True,
                   dosage_extra={"asNeededCodeableConcept": {"text": "pain"}})
case("prn_reason_fallback", [oxy_reason], T_ONE, (), "fallback")
apap = order("m1", "acetaminophen", 500, freq=4, asNeededBoolean=True)
case("prn_apap_fallback", [apap], T_ONE, (), "fallback")
case("prn_apap_render", [apap], T_ONE)

# 6. Insulin
reg = order("m1", "insulin, regular, human", 20, unit="units", freq=3, route=SUBQ)
case("insulin_regular_render", [reg], T_ONE)
case("insulin_regular_fallback", [reg], T_ONE, (), "fallback")
glar = order("m1", "insulin glargine", 20, unit="units", freq=1, route=SUBQ)
lisp = order("m2", "insulin lispro", 6, unit="units", freq=3, route=SUBQ)
case("insulin_basal_mealtime_render", [glar, lisp], T_TWO)
case("insulin_basal_mealtime_fallback", [glar, lisp], T_TWO, (), "fallback")

# 7. Metformin fallback punctuation
mf = order("m1", "metformin", 500, freq=2)
case("metformin_render", [mf], T_ONE)
case("metformin_fallback", [mf], T_ONE, (), "fallback")

# 8. Counts
cnt = order("m1", "lisinopril", 1, unit="{tablet}", freq=1)
case("count_render", [cnt], T_ONE)

# 9. Superseded orders with names that differ
lis_old2 = lambda: order("m2", "lisinopril", 10, freq=2)
for form, ref in [("exact", "MedicationRequest/m2"), ("urn", "urn:uuid:m2")]:
    aml = lambda ref=ref: order("m1", "amlodipine", 5, freq=1, priorPrescription={"reference": ref})
    case(f"supdiff_{form}_two_default", [aml(), lis_old2()], T_TWO)
    case(f"supdiff_{form}_two_omit", [aml(), lis_old2()], T_TWO, ("--allow-omissions",))
    case(f"supdiff_{form}_m2only_omit", [aml(), lis_old2()], "Take {{drug:m2}} {{dose:m2}} {{route:m2}} {{frequency:m2}}.", ("--allow-omissions",))
    case(f"supdiff_{form}_m2only_default", [aml(), lis_old2()], "Take {{drug:m2}} {{dose:m2}} {{route:m2}} {{frequency:m2}}.")
    case(f"supdiff_{form}_fallback", [aml(), lis_old2()], T_TWO, (), "fallback")

# 10. Exact framing from the old held-order example
case("held_example_render", [met(), warf_dnp], "Here is your medicine list. Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}.")
case("held_example_render_omit", [met(), warf_dnp], "Here is your medicine list. Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}.", ("--allow-omissions",))
case("held_example_fallback", [met(), warf_dnp], T_ONE, (), "fallback")
case("reported_boolean_m2_omit", [met(), rep_bool], "Take {{drug:m2}} {{dose:m2}} {{route:m2}} {{frequency:m2}}.", ("--allow-omissions",))
case("reported_boolean_none_default", [met(), rep_bool], T_NONE)

# 11. Extra checks
case("prn_reason_render", [order("m1", "oxycodone hydrochloride", 5, freq=1, asNeededBoolean=True, dosage_extra={"asNeededCodeableConcept": {"text": "pain"}})], T_ONE)
case("prn_plain_fallback_again", [order("m1", "oxycodone hydrochloride", 5, freq=1, asNeededBoolean=True)], T_ONE, (), "fallback")
case("insulin_humulin_render", [order("m1", "humulin r", 20, unit="units", freq=3, route=SUBQ)], T_ONE)
case("insulin_humulin_fallback", [order("m1", "humulin r", 20, unit="units", freq=3, route=SUBQ)], T_ONE, (), "fallback")
case("insulin_humulin_render_units_U", [order("m1", "humulin r", 20, unit="[IU]", freq=3, route=SUBQ)], T_ONE)
case("supdiff_bare_m2only_omit", [order("m1", "amlodipine", 5, freq=1, priorPrescription={"reference": "m2"}), order("m2", "lisinopril", 10, freq=2)], "Take {{drug:m2}} {{dose:m2}} {{route:m2}} {{frequency:m2}}.", ("--allow-omissions",))
case("supdiff_urn_m2only_fallback", [order("m1", "amlodipine", 5, freq=1, priorPrescription={"reference": "urn:uuid:m2"}), order("m2", "lisinopril", 10, freq=2)], T_ONE, (), "fallback")

# 12. Held orders named by a slot, and reference forms
T_M2 = "Take {{drug:m2}} {{dose:m2}} {{route:m2}} {{frequency:m2}}."
case("held_dnp_m2_slot_omit", [met(), warf_dnp], T_M2, ("--allow-omissions",))
case("held_dnp_m2_slot_default", [met(), warf_dnp], T_M2)
case("held_onhold_m2_slot_omit", [met(), warf_hold], T_M2, ("--allow-omissions",))
case("held_stopped_m2_slot_omit", [met(), warf_stop], T_M2, ("--allow-omissions",))
case("held_stopped_m2_slot_default", [met(), warf_stop], T_M2)
enc_query = order("m1", "metformin", 500, freq=2, encounter={"reference": "Encounter?identifier=abc|1"})
enc_hash = order("m1", "metformin", 500, freq=2, encounter={"reference": "#enc1"})
enc_urn = order("m1", "metformin", 500, freq=2, encounter={"reference": "urn:uuid:7c1d5e2a-1f3b-4a6e-9d7c-2b8e4f6a1c3d"})
case("ref_search_query_render", [enc_query], T_ONE)
case("ref_hash_render", [enc_hash], T_ONE)
case("ref_urn_render", [enc_urn], T_ONE)
case("ref_search_query_fallback", [enc_query], T_ONE, (), "fallback")

# 13. Twelve-hour as-needed structured name from the bundles
hyd = order("m1", "12 hr hydrocodone bitartrate", 10, freq=2, asNeededBoolean=False, dosage_extra={"text": "Every twelve hours as required (qualifier value)"})
case("ft_hydrocodone12_ignore", [hyd], T_ONE, ("--ignore-free-text",))
case("ft_hydrocodone12_no_flag_name_only", [order("m1", "hydrocodone bitartrate", 10, freq=2)], T_ONE)

log = []
for name, meds, output, flags, mode in CASES:
    req = {"medicationRequests": meds, "output": output}
    base = os.path.join(OUT, name)
    with open(base + ".request.json", "w") as f:
        json.dump(req, f, indent=2)
        f.write("\n")
    cmd = [BIN, mode] + ([] if mode == "fallback" else flags)
    r = subprocess.run(cmd, input=json.dumps(req), capture_output=True, text=True)
    with open(base + ".out.json", "w") as f:
        f.write(r.stdout)
    log.append({"name": name, "command": " ".join(["dosegate", mode] + ([] if mode == "fallback" else flags)),
                "exit": r.returncode, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()[:300]})
with open(os.path.join(OUT, "run_log.jsonl"), "w") as f:
    for row in log:
        f.write(json.dumps(row) + "\n")
for row in log:
    print(row["name"], "|", row["command"], "|", row["stdout"][:260], "|", row["stderr"][:120])
