import json, os, random, sys

from score import DATA

ROWS = {"slot_first_attempt": ("slot", "first"), "slot_after_retries": ("slot", "last"),
        "slot_daily_first_attempt": ("slot_daily", "first"), "slot_daily_after_retries": ("slot_daily", "last"),
        "slot_hot": ("slot_hot", "all"), "attack": ("attack", "all")}


def patient(case_id):
    return case_id.split(":")[0]


def rows_for(tag):
    dec = json.load(open(os.path.join(DATA, f"final_gate_decisions_{tag}.json")))
    out = {}
    for name, (cond, which) in ROWS.items():
        items = [d for d in dec if d["condition"] == cond]
        if which == "first":
            items = [d for d in items if d["attempt"] == 0]
        elif which == "last":
            best = {}
            for d in items:
                k = (d["case_id"], d["sample"])
                if k not in best or d["attempt"] > best[k]["attempt"]:
                    best[k] = d
            items = list(best.values())
        if items:
            out[name] = [(patient(d["case_id"]), d["gate"]["status"] == "ok") for d in items]
    return out


def bootstrap(pairs, reps, rng):
    by = {}
    for p, ok in pairs:
        by.setdefault(p, []).append(ok)
    patients = sorted(by)
    rates = []
    for _ in range(reps):
        draw = [by[rng.choice(patients)] for _ in patients]
        n = sum(len(x) for x in draw)
        rates.append(sum(sum(x) for x in draw) / n)
    rates.sort()
    return rates[int(0.025 * reps)], rates[int(0.975 * reps) - 1]


def main():
    reps = 2000
    out = {}
    for tag in sys.argv[1:]:
        rng = random.Random(20261105)
        out[tag] = {}
        for name, pairs in rows_for(tag).items():
            lo, hi = bootstrap(pairs, reps, rng)
            k, n = sum(ok for _, ok in pairs), len(pairs)
            out[tag][name] = {"released": k, "n": n, "pct": round(100 * k / n, 1), "patients": len({p for p, _ in pairs}),
                              "cluster_ci": [round(100 * lo, 1), round(100 * hi, 1)]}
            print(f"{tag} {name}: {k}/{n} ({out[tag][name]['pct']}%) cluster 95% CI {out[tag][name]['cluster_ci']}")
    json.dump({"reps": reps, "seed": 20261105, "method": "percentile bootstrap resampling patients with replacement", "rows": out},
              open(os.path.join(DATA, "bootstrap.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
