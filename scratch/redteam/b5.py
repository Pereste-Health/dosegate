from raw import *
import sys
for e in [1000, 3000, 10000, 30000, 100000]:
    fields = ", ".join([FREQ_DAILY, ROUTE_ORAL, dose_block("1e%d" % e)])
    req = request([mr("m1", fields)], "Take {{drug:m1}} {{dose:m1}}.")
    rc, out, err, t = run(req, timeout=20)
    print("dose exp", e, "rc=", rc, "t=", t, "outlen=", len(out))
for e in [1000, 10000, 100000]:
    fields = ", ".join(['"timing": {"repeat": {"frequency": 1e%d, "period": 1, "periodUnit": "d"}}' % e, ROUTE_ORAL, dose_block("500")])
    req = request([mr("m1", fields)], "Take {{drug:m1}} {{frequency:m1}}.")
    rc, out, err, t = run(req, timeout=20)
    print("freq exp", e, "rc=", rc, "t=", t, "outlen=", len(out), out[:80])
