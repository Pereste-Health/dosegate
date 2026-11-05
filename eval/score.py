import collections, json, os, re, statistics, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MASS = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(mg|milligrams?|mcg|micrograms?|g|grams?)\b", re.I)
FREQ = [
    (re.compile(r"\b(four|4) times (a|per|each|every) day\b|\bfour times daily\b", re.I), (4, 1, "d")),
    (re.compile(r"\bevery (4|four) hours\b", re.I), (1, 4, "h")),
    (re.compile(r"\bevery (6|six) hours\b", re.I), (1, 6, "h")),
    (re.compile(r"\b(three|3) times (a|per|each|every) day\b|\bthree times daily\b", re.I), (3, 1, "d")),
    (re.compile(r"\b(twice|two times|2 times) (a|per|each|every) day\b|\btwice daily\b|\btwo of them every day\b", re.I), (2, 1, "d")),
    (re.compile(r"\bevery (8|eight) hours\b", re.I), (1, 8, "h")),
    (re.compile(r"\bevery (12|twelve) hours\b", re.I), (1, 12, "h")),
    (re.compile(r"\b(once (a|per|each|every) week|weekly|every week)\b", re.I), (1, 1, "wk")),
    (re.compile(r"\b(once (a|per|each|every) day|once daily|every day|each day|daily)\b", re.I), (1, 1, "d")),
]


def freqs_in(chunk):
    chunk = re.sub(r"\{\{[^}]*\}\}", " ", chunk)
    chunk = re.sub(r"\btotal\b.*", " ", chunk, flags=re.I | re.S)
    found = set()
    for rx, t in FREQ:
        if rx.search(chunk):
            found.add(t)
            chunk = rx.sub(" ", chunk)
    return found


def to_mg(num, unit):
    v = float(num.replace(",", ""))
    u = unit.lower()
    if u.startswith("mc") or u.startswith("micro"):
        return v / 1000
    if u in ("g", "gram", "grams"):
        return v * 1000
    return v


def per_day(t):
    f, p, u = t
    if u == "d" and p == 1:
        return f
    if u == "h" and 24 % p == 0:
        return f * 24 // p
    return None


def orders(case):
    out = []
    for m in case["medicationRequests"]:
        d = m["dosageInstruction"][0]
        r = d["timing"]["repeat"]
        mg = float(d["doseAndRate"][0]["doseQuantity"]["value"])
        t = (r["frequency"], r["period"], r["periodUnit"])
        k = per_day(t)
        out.append({"id": m["id"], "drug": m["medicationCodeableConcept"]["text"], "mg": mg, "timing": t,
                    "daily_mg": None if k is None else round(mg * k, 6)})
    return out


PER_DAY = re.compile(r"\b(in one day|a day|per day|each day|every day|daily|in a day)\b", re.I)


def name_key(drug):
    words = [w for w in re.findall(r"[a-z]+", drug) if w not in ("hr", "abuse", "deterrent", "hydrochloride", "sodium", "potassium", "bitartrate")]
    return max(words, key=len) if words else drug


def units_mentioning(text, ords):
    chunks = [c for c in re.split(r"(?<=[.!?])\s+|\n+", text) if c.strip()]
    return {o["id"]: [c for c in chunks if name_key(o["drug"]) in c.lower()] for o in ords}


def audit_text(text, ords):
    chart_mg = {o["mg"] for o in ords} | {o["daily_mg"] for o in ords if o["daily_mg"] is not None}
    spans = [to_mg(n, u) for n, u in MASS.findall(text)]
    unsupported = [s for s in spans if not any(abs(s - c) < 1e-9 for c in chart_mg)]
    by_order = units_mentioning(text, ords)
    dose_wrong, freq_wrong, missing = [], [], []
    for o in ords:
        chunks = by_order[o["id"]]
        if not chunks:
            missing.append(o["id"])
            continue
        ok_vals = [o["mg"]] + ([o["daily_mg"]] if o["daily_mg"] is not None else [])
        vals = [to_mg(n, u) for c in chunks for n, u in MASS.findall(c)]
        if any(not any(abs(v - w) < 1e-9 for w in ok_vals) for v in vals):
            dose_wrong.append(o["id"])
        elif o["daily_mg"] is None and o["timing"][2] in ("wk", "mo") and any(
                "total" in c.lower() and PER_DAY.search(c) and MASS.search(c) for c in chunks):
            dose_wrong.append(o["id"])
        freqs = set().union(*(freqs_in(c) for c in chunks))
        if freqs and o["timing"] not in freqs:
            freq_wrong.append(o["id"])
    return {"spans": len(spans), "unsupported": len(unsupported), "dose_wrong": dose_wrong,
            "freq_wrong": freq_wrong, "missing": missing}


def regate(gens, cases, binary):
    proc = subprocess.Popen([binary, "serve"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for g in gens:
        mrs = [dict(m, subject={"reference": "Patient/p1"}) for m in cases[g["case_id"]]["medicationRequests"]]
        t = time.perf_counter()
        proc.stdin.write(json.dumps({"medicationRequests": mrs, "output": g["output"]}) + "\n")
        proc.stdin.flush()
        res = json.loads(proc.stdout.readline())
        res["gate_ms"] = round((time.perf_counter() - t) * 1000, 3)
        g["provisional_gate"] = g["gate"]
        g["gate"] = res
    proc.stdin.close()
    proc.wait()


def pct(a, b):
    return f"{a}/{b} ({100 * a / b:.1f}%)" if b else "0/0"


def main():
    cases = {c["case_id"]: c for c in map(json.loads, open(os.path.join(DATA, "cases.jsonl")))}
    gens = [json.loads(l) for l in open(os.path.join(DATA, "generations.jsonl"))]
    if os.environ.get("FINAL_GATE"):
        regate(gens, cases, os.environ["FINAL_GATE"])
        changed = sum(g["gate"]["status"] != g["provisional_gate"]["status"] for g in gens)
        print(f"re-gated {len(gens)} outputs with the final gate; {changed} decisions differ from the provisional gate")
        json.dump([{k: g[k] for k in ("case_id", "condition", "sample", "attempt", "gate", "provisional_gate")} for g in gens],
                  open(os.path.join(DATA, "final_gate_decisions.json"), "w"))
    report, rows = {}, []
    groups = collections.defaultdict(list)
    for g in gens:
        groups[g["condition"]].append(g)
    def final(cond):
        best = {}
        for g in groups[cond]:
            k = g["case_id"]
            if k not in best or g["attempt"] > best[k]["attempt"]:
                best[k] = g
        return list(best.values())

    order = [json.loads(l)["case_id"] for l in open(os.path.join(DATA, "cases.jsonl"))]
    half = os.environ.get("HALF")
    keep = set(order[:120]) if half == "dev" else set(order[120:]) if half == "test" else set(order)
    for c in list(groups):
        groups[c] = [g for g in groups[c] if g["case_id"] in keep]
    views = {
        "free": groups["free"],
        "free_daily": groups["free_daily"],
        "slot_first_attempt": [g for g in groups["slot"] if g["attempt"] == 0],
        "slot_after_retries": final("slot"),
        "slot_daily_first_attempt": [g for g in groups["slot_daily"] if g["attempt"] == 0],
        "slot_daily_after_retries": final("slot_daily"),
        "slot_hot": groups["slot_hot"],
        "attack": groups["attack"],
    }
    for name, gs in views.items():
        reasons = collections.Counter(g["gate"].get("reason") for g in gs if g["gate"]["status"] != "ok")
        passed = [g for g in gs if g["gate"]["status"] == "ok"]
        zero = lambda: {"orders": 0, "dose_wrong": 0, "freq_wrong": 0, "missing": 0, "outputs_unsupported": 0, "outputs_any_error": 0}
        raw, shown = zero(), zero()
        by_variant = collections.defaultdict(zero)
        for g in gs:
            ords = orders(cases[g["case_id"]])
            a = audit_text(g["output"], ords)
            for acc in (raw, by_variant[g["variant"]]):
                acc["orders"] += len(ords)
                acc["dose_wrong"] += len(a["dose_wrong"])
                acc["freq_wrong"] += len(a["freq_wrong"])
                acc["missing"] += len(a["missing"])
                acc["outputs_unsupported"] += a["unsupported"] > 0
                acc["outputs_any_error"] += bool(a["unsupported"] or a["dose_wrong"] or a["freq_wrong"])
            if g["gate"]["status"] == "ok":
                b = audit_text(g["gate"]["text"], ords)
                shown["orders"] += len(ords)
                shown["dose_wrong"] += len(b["dose_wrong"])
                shown["freq_wrong"] += len(b["freq_wrong"])
                shown["missing"] += len(b["missing"])
                shown["outputs_unsupported"] += b["unsupported"] > 0
                shown["outputs_any_error"] += bool(b["unsupported"] or b["dose_wrong"] or b["freq_wrong"])
        report[name] = {"n": len(gs), "passed": len(passed), "block_reasons": dict(reasons),
                        "raw_model_text": raw, "raw_by_variant": dict(by_variant), "text_shown_after_gate": shown}
    ms = [g["gate"]["gate_ms"] for g in gens if "gate_ms" in g["gate"]]
    report["gate_ms"] = {"n": len(ms), "median": statistics.median(ms), "p99": sorted(ms)[int(0.99 * (len(ms) - 1))], "max": max(ms)}
    json.dump(report, open(os.path.join(DATA, f"results_{half or 'all'}.json"), "w"), indent=1)
    for name, r in report.items():
        if name == "gate_ms":
            continue
        print(f"\n{name}: n={r['n']} passed={pct(r['passed'], r['n'])} blocks={r['block_reasons']}")
        print(f"  raw text: {r['raw_model_text']}")
        for v, acc in r["raw_by_variant"].items():
            print(f"    {v}: {acc}")
        print(f"  shown after gate: {r['text_shown_after_gate']}")
    print("\ngate ms:", report["gate_ms"])


if __name__ == "__main__":
    main()
