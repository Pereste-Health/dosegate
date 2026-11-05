from raw import *
import json
OUT = "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}."
def chart_entry(id_="m1", status='"active"', extra="", timing=FREQ_DAILY, route=ROUTE_ORAL, dose=None, drug='"text": "metformin"'):
    dose = dose or dose_block("500")
    fields = ", ".join(x for x in [timing, route, dose] if x)
    top = ", ".join(x for x in ['"resourceType": "MedicationRequest"', '"id": "%s"' % id_, '"status": %s' % status, extra.strip().rstrip(",")] if x)
    return '{"resource": {%s, "medicationCodeableConcept": {%s}, "dosageInstruction": [{%s}]}}' % (top, drug, fields)
def req(entries, out=OUT):
    return '{"bundle": {"resourceType": "Bundle", "entry": [%s]}, "output": %s}' % (", ".join(entries), json.dumps(out))
cases = {
 "doNotPerform_true": req([chart_entry(extra='"doNotPerform": true,')]),
 "intent_proposal": req([chart_entry(extra='"intent": "proposal",')]),
 "frequencyMax_4": req([chart_entry(timing='"timing": {"repeat": {"frequency": 2, "frequencyMax": 4, "period": 1, "periodUnit": "d"}}')]),
 "periodMax_2": req([chart_entry(timing='"timing": {"repeat": {"frequency": 1, "period": 1, "periodMax": 2, "periodUnit": "d"}}')]),
 "doseQuantity_comparator_lt": req([chart_entry(dose='"doseAndRate": [{"doseQuantity": {"value": 500, "comparator": "<", "code": "mg"}}]')]),
 "maxDosePerPeriod_ignored": req([chart_entry(dose='"maxDosePerPeriod": {"numerator": {"value": 3000, "code": "mg"}, "denominator": {"value": 1, "code": "d"}}, "doseAndRate": [{"doseQuantity": {"value": 500, "code": "mg"}}]')]),
 "route_two_codings_IV_first": req([chart_entry(route='"route": {"coding": [{"system": "http://snomed.info/sct", "code": "47625008"}, {"system": "http://snomed.info/sct", "code": "26643006"}]}')]),
 "route_two_codings_oral_first": req([chart_entry(route='"route": {"coding": [{"system": "http://snomed.info/sct", "code": "26643006"}, {"system": "http://snomed.info/sct", "code": "47625008"}]}')]),
 "drug_with_strength_in_name": req([chart_entry(drug='"text": "Metformin 1000 MG Oral Tablet"')]),
 "drug_homoglyph_cyrillic_o": req([chart_entry(drug='"text": "metf\\u043ermin"')]),
 "drug_RTL_override": req([chart_entry(drug='"text": "metformin \\u202e 05 gm"')]),
 "drug_zero_width": req([chart_entry(drug='"text": "met\\u200bformin"')]),
 "dup_status_keys_stopped_then_active": req([chart_entry(status='"stopped", "status": "active"')]),
 "dup_status_keys_active_then_stopped": req([chart_entry(status='"active", "status": "stopped"')]),
 "asNeeded_string_false": req([chart_entry(extra='', timing=FREQ_DAILY + ', "asNeededBoolean": "false"')]),
}
for name, body in cases.items():
    rc, out, err, t = run(body)
    print(f"[{name}] rc={rc} {out[:220]} {err[:100]}")
