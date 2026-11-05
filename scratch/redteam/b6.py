from raw import *
import sys, json
kind = sys.argv[1]; n = int(sys.argv[2])
if kind == "longtext":
    out = "word " * n
    body = '{"bundle": {"resourceType": "Bundle", "entry": []}, "output": %s}' % json.dumps(out)
elif kind == "manysent":
    out = "Take {{drug:m1}} {{dose:m1}}. " * n
    body = '{"bundle": {"resourceType": "Bundle", "entry": [%s]}, "output": %s}' % (mr("m1", FREQ_DAILY + ", " + ROUTE_ORAL + ", " + dose_block("500")), json.dumps(out))
elif kind == "deepjson":
    body = '{"bundle": {"resourceType": "Bundle", "entry": []}, "x": %s1%s, "output": "hi"}' % ("[" * n, "]" * n)
elif kind == "deepjson_obj":
    body = '{"bundle": {"resourceType": "Bundle", "entry": []}, "x": %s1%s, "output": "hi"}' % ('{"a":' * n, '}' * n)
rc, o, err, t = run(body, timeout=60)
print(kind, n, "rc=", rc, "t=", t, o[:120], err[:200])
