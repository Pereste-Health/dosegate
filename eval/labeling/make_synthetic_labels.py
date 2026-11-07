import argparse
import datetime
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
sys.path.insert(0, EVAL)
from human_agreement import CATS, load_adopted  # noqa: E402

ERROR_TYPES = ["weekly_as_daily", "wrong_daily_arithmetic", "sum_of_different_drugs", "wrong_dose", "wrong_frequency", "wrong_route",
               "duplicated_instruction", "wrong_medicine", "inactive_as_current", "conditional_as_fixed", "other"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=os.path.join(HERE, "queue_manifest.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--agreement", type=float, default=0.85, help="probability of repeating the adopted label")
    ap.add_argument("--flag-confirm", type=float, default=0.6, help="probability that a flagged Claude output is labeled misstates_order")
    ap.add_argument("--fraction", type=float, default=1.0, help="fraction of the queue that is labeled")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    manifest = json.load(open(args.manifest))
    adopted = load_adopted(manifest)
    rows = []
    t0 = datetime.datetime(2026, 11, 8, 9, 0, 0)
    for n, it in enumerate(manifest["items"]):
        if rng.random() > args.fraction:
            continue
        a = adopted[it["id"]]
        if a["label"]:
            label = a["label"] if rng.random() < args.agreement else rng.choice([c for c in CATS if c != a["label"]])
        else:
            r = rng.random()
            label = "misstates_order" if r < args.flag_confirm else "unsupported_claim" if r < args.flag_confirm + 0.2 else "faithful"
        rec = {"item_id": it["id"], "kind": it["kind"], "label": label,
               "error_type": (a["error_type"] or rng.choice(ERROR_TYPES)) if label == "misstates_order" else None,
               "same_ingredient": rng.choice(["yes", "yes", "yes", "no", "unsure"]) if it["kind"] == "pair" else None,
               "double_dose_risk": rng.choice(["yes", "no", "no", "unsure"]) if it["kind"] == "pair" else None,
               "confidence": "unsure" if rng.random() < 0.1 else "sure",
               "note": "synthetic label" if rng.random() < 0.2 else "",
               "labeled_at": (t0 + datetime.timedelta(seconds=40 * n)).isoformat() + "Z"}
        rows.append(rec)
    out = {"schema": "dosegate-human-labels-1", "labeler": "synthetic", "exported_at": t0.isoformat() + "Z", "source": "synthetic",
           "n_items": len(manifest["items"]), "n_labeled": len(rows), "labels": rows}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(f"wrote {len(rows)} synthetic labels to {args.out}")


if __name__ == "__main__":
    main()
