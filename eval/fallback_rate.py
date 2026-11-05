import collections, json, os, subprocess

from score import DATA, HERE

GATE = os.environ.get("DOSEGATE", os.path.join(HERE, "..", ".lake", "build", "bin", "dosegate"))


def main():
    cases = [json.loads(l) for l in open(os.path.join(DATA, "cases.jsonl"))][120:]
    reasons = collections.Counter()
    released = []
    for c in cases:
        mrs = [dict(m, subject={"reference": "Patient/p1"}) for m in c["medicationRequests"]]
        req = json.dumps({"medicationRequests": mrs, "output": ""})
        r = subprocess.run([GATE, "fallback"], input=req, capture_output=True, text=True)
        res = json.loads(r.stdout)
        if res["status"] == "ok":
            released.append(c["case_id"])
        else:
            reasons[(res["status"], res.get("reason") or res.get("message", "")[:60])] += 1
    out = {"test_cases": len(cases), "released": len(released), "blocked": dict((f"{s}:{r}", n) for (s, r), n in reasons.items())}
    print(json.dumps(out, indent=1))
    json.dump(out, open(os.path.join(DATA, "fallback_rate.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
