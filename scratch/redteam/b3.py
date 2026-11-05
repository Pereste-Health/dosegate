from raw import *
import sys
OUT = "Take {{drug:m1}} {{dose:m1}} {{frequency:m1}}."
def one(dose_val, timing=FREQ_DAILY):
    fields = ", ".join([timing, ROUTE_ORAL, dose_block(dose_val)])
    return request([mr("m1", fields)], OUT)
CASES = {
 "dose_exp_1e6": lambda: one("1e1000000"),
 "dose_exp_1e8": lambda: one("1e100000000"),
 "dose_exp_1e9": lambda: one("1e1000000000"),
 "freq_exp_1e6": lambda: one("500", timing='"timing": {"repeat": {"frequency": 1e1000000, "period": 1, "periodUnit": "d"}}'),
 "freq_exp_1e9": lambda: one("500", timing='"timing": {"repeat": {"frequency": 1e1000000000, "period": 1, "periodUnit": "d"}}'),
}
name = sys.argv[1]
rc, out, err, t = run(CASES[name](), timeout=int(sys.argv[2]))
print(name, "rc=", rc, "t=", t, out[:200], err[:200])
