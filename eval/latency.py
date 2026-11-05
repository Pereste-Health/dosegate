import json, os, statistics, subprocess, sys, time

from score import DATA, HERE


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else ""
    s = f"_{tag}" if tag else ""
    cases = {json.loads(l)["case_id"]: json.loads(l) for l in open(os.path.join(DATA, "cases.jsonl"))}
    gens = [json.loads(l) for l in open(os.path.join(DATA, f"generations{s}.jsonl"))]
    lines = []
    for g in gens:
        mrs = [dict(m, subject={"reference": "Patient/p1"}) for m in cases[g["case_id"]]["medicationRequests"]]
        lines.append(json.dumps({"medicationRequests": mrs, "output": g["output"]}))
    binary = os.path.join(HERE, "..", ".lake", "build", "bin", "dosegate")
    body = "\n".join(lines) + "\n"
    runs = []
    for _ in range(5):
        t = time.perf_counter()
        p = subprocess.run([binary, "serve"], input=body, capture_output=True, text=True)
        runs.append((time.perf_counter() - t) * 1000 / len(lines))
        assert len(p.stdout.splitlines()) == len(lines)
    empty = []
    for _ in range(5):
        t = time.perf_counter()
        subprocess.run([binary, "serve"], input="", capture_output=True, text=True)
        empty.append((time.perf_counter() - t) * 1000)
    report = {"outputs": len(lines), "runs": 5, "mean_ms_per_output_each_run": [round(r, 3) for r in runs],
              "process_start_ms_median": round(statistics.median(empty), 2)}
    print(json.dumps(report, indent=1))
    json.dump(report, open(os.path.join(DATA, f"latency{s}.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
