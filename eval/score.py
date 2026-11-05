import collections, json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MASS = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(mg|milligrams?|mcg|micrograms?|g|grams?)\b", re.I)
FREQ = [
    (re.compile(r"\b(once (a|per|each) day|once daily|every day|each day|daily)\b", re.I), (1, 1, "d")),
    (re.compile(r"\b(twice (a|per|each) day|twice daily|two times (a|per|each) day)\b", re.I), (2, 1, "d")),
    (re.compile(r"\b(three times (a|per|each) day)\b", re.I), (3, 1, "d")),
    (re.compile(r"\bevery 8 hours\b|\bevery eight hours\b", re.I), (1, 8, "h")),
    (re.compile(r"\bevery 12 hours\b|\bevery twelve hours\b", re.I), (1, 12, "h")),
    (re.compile(r"\b(once (a|per|each) week|weekly|every week)\b", re.I), (1, 1, "wk")),
]


def to_mg(num, unit):
    v = float(num.replace(",", ""))
    u = unit.lower()
    if u.startswith("mc") or u.startswith("micro"):
        return v / 1000
    if u in ("g", "gram", "grams"):
        return v * 1000
    return v


def orders(case):
    out = []
    for m in case["medicationRequests"]:
        d = m["dosageInstruction"][0]
        r = d["timing"]["repeat"]
        out.append({"id": m["id"], "drug": m["medicationCodeableConcept"]["text"],
                    "mg": float(d["doseAndRate"][0]["doseQuantity"]["value"]),
                    "timing": (r["frequency"], r["period"], r["periodUnit"])})
    return out


def name_key(drug):
    words = [w for w in re.findall(r"[a-z]+", drug) if w not in ("hr", "abuse", "deterrent", "hydrochloride", "sodium", "potassium", "bitartrate")]
    return max(words, key=len) if words else drug


def units_mentioning(text, ords):
    chunks = [c for c in re.split(r"(?<=[.!?])\s+|\n+", text) if c.strip()]
    return {o["id"]: [c for c in chunks if name_key(o["drug"]) in c.lower()] for o in ords}


def audit_text(text, ords):
    chart_mg = {o["mg"] for o in ords}
    spans = [to_mg(n, u) for n, u in MASS.findall(text)]
    unsupported = [s for s in spans if not any(abs(s - c) < 1e-9 for c in chart_mg)]
    by_order = units_mentioning(text, ords)
    dose_wrong, freq_wrong, missing = [], [], []
    for o in ords:
        chunks = by_order[o["id"]]
        if not chunks:
            missing.append(o["id"])
            continue
        vals = [to_mg(n, u) for c in chunks for n, u in MASS.findall(c)]
        if vals and not any(abs(v - o["mg"]) < 1e-9 for v in vals):
            dose_wrong.append(o["id"])
        freqs = {t for c in chunks for rx, t in FREQ if rx.search(c)}
        if freqs and o["timing"] not in freqs:
            freq_wrong.append(o["id"])
    return {"spans": len(spans), "unsupported": len(unsupported), "dose_wrong": dose_wrong,
            "freq_wrong": freq_wrong, "missing": missing}


def pct(a, b):
    return f"{a}/{b} ({100 * a / b:.1f}%)" if b else "0/0"


def main():
    cases = {c["case_id"]: c for c in map(json.loads, open(os.path.join(DATA, "cases.jsonl")))}
    gens = [json.loads(l) for l in open(os.path.join(DATA, "generations.jsonl"))]
    report, rows = {}, []
    groups = collections.defaultdict(list)
    for g in gens:
        groups[g["condition"]].append(g)
    final_slot = {}
    for g in groups["slot"]:
        k = g["case_id"]
        if k not in final_slot or g["attempt"] > final_slot[k]["attempt"]:
            final_slot[k] = g
    views = {
        "free": groups["free"],
        "slot_first_attempt": [g for g in groups["slot"] if g["attempt"] == 0],
        "slot_after_one_retry": list(final_slot.values()),
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
    ms = [g["gate"]["gate_ms"] for g in gens]
    report["gate_ms"] = {"n": len(ms), "median": statistics.median(ms), "p99": sorted(ms)[int(0.99 * (len(ms) - 1))], "max": max(ms)}
    json.dump(report, open(os.path.join(DATA, "results.json"), "w"), indent=1)
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
