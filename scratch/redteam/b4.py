from raw import *
import sys
e = sys.argv[1]
req = request([mr("m1", FREQ_DAILY + ", " + ROUTE_ORAL + ", " + dose_block("500"), extra='"unused": %s,' % e)], "Take {{drug:m1}}.")
rc, out, err, t = run(req, timeout=int(sys.argv[2]))
print("unused_field exp", e, "rc=", rc, "t=", t, out[:150], err[:150])
