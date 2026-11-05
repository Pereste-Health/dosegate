from raw import *
OUT = "Take {{drug:m1}} {{dose:m1}} {{frequency:m1}}."
def one(dose_val, timing=FREQ_DAILY, extra_dosage="", code="mg", status='"active"', route=ROUTE_ORAL, ext=""):
    fields = ", ".join(x for x in [timing, route, dose_block(dose_val, code), extra_dosage] if x)
    return request([mr("m1", fields, status, ext)], OUT)
cases = [
 ("value_5e2", one("5e2")),
 ("value_1e-3", one("1e-3")),
 ("value_0.5e1", one("0.5e1")),
 ("value_1E+3", one("1E+3")),
 ("value_neg0", one("-0")),
 ("value_0", one("0")),
 ("value_big", one("123456789012345678901234567890.5")),
 ("value_1e400", one("1e400")),
 ("value_1e-400", one("1e-400")),
 ("value_2.50", one("2.50")),
 ("value_str", one('"500"')),
 ("value_neg", one("-5")),
 ("freq_1e1", one("500", timing='"timing": {"repeat": {"frequency": 1e1, "period": 1, "periodUnit": "d"}}')),
 ("freq_2.0", one("500", timing='"timing": {"repeat": {"frequency": 2.0, "period": 1, "periodUnit": "d"}}')),
 ("freq_2.5", one("500", timing='"timing": {"repeat": {"frequency": 2.5, "period": 1, "periodUnit": "d"}}')),
 ("freq_0", one("500", timing='"timing": {"repeat": {"frequency": 0, "period": 1, "periodUnit": "d"}}')),
 ("period_0.5", one("500", timing='"timing": {"repeat": {"frequency": 1, "period": 0.5, "periodUnit": "d"}}')),
 ("period_0", one("500", timing='"timing": {"repeat": {"frequency": 1, "period": 0, "periodUnit": "d"}}')),
 ("period_1e9", one("500", timing='"timing": {"repeat": {"frequency": 1, "period": 1e9, "periodUnit": "d"}}')),
 ("freq_1e9", one("500", timing='"timing": {"repeat": {"frequency": 1e9, "period": 1, "periodUnit": "d"}}')),
 ("freq_huge_mantissa", one("500", timing='"timing": {"repeat": {"frequency": 1e400, "period": 1, "periodUnit": "d"}}')),
 ("status_dup_keys", request([mr("m1", FREQ_DAILY + ", " + ROUTE_ORAL + ", " + dose_block("500"), '"stopped", "status": "active"')], OUT)),
 ("status_missing", request([mr("m1", FREQ_DAILY + ", " + ROUTE_ORAL + ", " + dose_block("500"), '"active"').replace('"status": "active", ', '')], OUT)),
 ("status_on-hold", one("500", status='"on-hold"')),
]
for name, body in cases:
    rc, out, err, t = run(body)
    print(f"[{name}] rc={rc} t={t}s\n  {out}\n  {err}")
