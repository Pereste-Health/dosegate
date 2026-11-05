import json, math, os

from score import DATA

MODELS = [("v2_qwen3.5-4b", "Qwen3.5-4B"), ("v2_medgemma-4b", "MedGemma 4B"), ("v2_llama3.2-3b", "Llama 3.2 3B"),
          ("v2_claude-haiku-5-5", "Claude Haiku 5.5"), ("v2_claude-sonnet-5-5", "Claude Sonnet 5.5")]
ROWS = [("slot_first_attempt", "Slot, first attempt"), ("slot_after_retries", "Slot, after rewrites"),
        ("slot_daily_first_attempt", "Slot daily, first attempt"), ("slot_daily_after_retries", "Slot daily, after rewrites"),
        ("slot_hot", "Slot, temperature 1.0"), ("free", "Free"), ("free_daily", "Free daily"), ("attack", "Attack")]


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def r1(x):
    return math.floor(x * 10 + 0.5 + 1e-9) / 10


def load(tag, half):
    s = f"_{tag}" if tag else ""
    p = os.path.join(DATA, f"results_{half}{s}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    out = {}
    for tag, name in MODELS:
        a, t = load(tag, "all"), load(tag, "test")
        if a is None:
            continue
        rows = {}
        for key, label in ROWS:
            r = a[key]
            if r["n"] == 0:
                continue
            lo, hi = wilson(r["passed"], r["n"])
            shown = r["text_shown_after_gate"]
            raw = r["raw_model_text"]
            rows[key] = {"label": label, "n": r["n"], "released": r["passed"], "pct": r1(100 * r["passed"] / r["n"]),
                         "ci": [r1(100 * lo), r1(100 * hi)],
                         "test_released": t[key]["passed"] if t else None, "test_n": t[key]["n"] if t else None,
                         "block_reasons": r["block_reasons"],
                         "released_outputs_with_error": shown["outputs_any_error"], "released_orders": shown["orders"],
                         "raw_outputs_with_error": raw["outputs_any_error"]}
        released = sum(rows[k]["released"] for k in ("slot_after_retries", "slot_daily_after_retries", "slot_hot") if k in rows)
        errs = sum(rows[k]["released_outputs_with_error"] for k in ("slot_after_retries", "slot_daily_after_retries", "slot_hot") if k in rows)
        lo, hi = wilson(errs, released)
        out[name] = {"rows": rows, "released_total": released, "released_with_error": errs,
                     "error_ci": [r1(100 * lo), r1(100 * hi)], "gate_ms": a["gate_ms"]}
        print(f"\n{name}: released {released}, with detected error {errs} (CI {out[name]['error_ci']})")
        for key, r in rows.items():
            print(f"  {r['label']}: {r['released']}/{r['n']} ({r['pct']}%, {r['ci'][0]}-{r['ci'][1]}) "
                  f"test {r['test_released']}/{r['test_n']} raw errors {r['raw_outputs_with_error']} blocks {r['block_reasons']}")
    json.dump(out, open(os.path.join(DATA, "models_summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
