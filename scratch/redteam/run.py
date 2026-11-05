import json, subprocess, sys
BIN = "/Volumes/T7/Dosing_formal_verification/.lake/build/bin/dosegate"
CHART = json.load(open("/Volumes/T7/Dosing_formal_verification/scratch/redteam/chart.json"))

def run(output, chart=None, allow=None, raw=None, extra=None):
    req = {"bundle": chart if chart is not None else CHART, "output": output}
    if allow is not None:
        req["allow"] = allow
    if extra:
        req.update(extra)
    data = raw if raw is not None else json.dumps(req, ensure_ascii=False)
    try:
        p = subprocess.run([BIN, "render"], input=data.encode("utf-8"), capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None, None
    out = p.stdout.decode("utf-8", "replace").strip()
    return p.returncode, out, p.stderr.decode("utf-8", "replace")[:300]

if __name__ == "__main__":
    cases = json.load(open(sys.argv[1]))
    for name, c in cases:
        rc, out, err = run(c["output"], chart=c.get("chart"), allow=c.get("allow"))
        print(f"[{name}] exit={rc}\n  out: {out}" + (f"\n  err: {err}" if err else ""))
