import collections, json, os, sys

from score import DATA

SETS = {"development": "attack_labels.json", "h1": "heldout/labels_h1.json", "h2": "heldout2/labels_h2.json",
        "h3": "heldout3/labels_h3.json"}
CATS = ["faithful", "misstates_order", "unsupported_claim"]


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in CATS) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def summarize(labels):
    out = {}
    for flt in ("layer", "baseline"):
        rows = [x for x in labels if x["filter"] == flt]
        by_label = collections.Counter(x["label"] for x in rows)
        distinct = {}
        for x in rows:
            distinct.setdefault(x.get("text"), set()).add(x["label"])
        pairs = [(x["reader1"], x["reader2"]) for x in rows if x.get("reader1") and x.get("reader2")]
        out[flt] = {"released_outputs": len(rows), "labels": dict(by_label), "distinct_texts": len(distinct),
                    "distinct_texts_with_mixed_labels": sum(len(v) > 1 for v in distinct.values()),
                    "readers_agree": sum(a == b for a, b in pairs), "reader_pairs": len(pairs),
                    "kappa": None if kappa(pairs) is None else round(kappa(pairs), 2),
                    "third_reader_used": sum(1 for x in rows if x.get("third_reader"))}
    pairs = [(x["reader1"], x["reader2"]) for x in labels if x.get("reader1") and x.get("reader2")]
    out["both_filters_kappa"] = None if kappa(pairs) is None else round(kappa(pairs), 2)
    return out


def summarize_v2_review():
    v2 = os.path.join(DATA, "v2_review")
    items = [json.loads(l) for l in open(os.path.join(v2, "items.jsonl")) if l.strip()]
    labels = {r["item"]: r for r in json.load(open(os.path.join(v2, "labels.json")))}
    flags = dict(json.load(open(os.path.join(v2, "script_flags.json"))))
    llama_bo = [labels[i["item"]] for i in items if i["item"].startswith("bo|") and i["model"] == "Llama 3.2 3B"]
    relabeled = sum(1 for r in llama_bo if r.get("relabel_note") and r["label"] == "misstates_order")
    misstates = sum(r["label"] == "misstates_order" for r in llama_bo)
    llama = {"released_outputs": len(llama_bo),
             "labels": dict(collections.Counter(r["label"] for r in llama_bo)),
             "misstates_order": misstates,
             "misstates_order_before_round10": misstates - relabeled,
             "relabeled_to_misstates_order": relabeled,
             "misstates_order_duplicated_instruction": sum(
                 r["label"] == "misstates_order" and r.get("error_type", "").startswith("duplicated_instruction")
                 for r in llama_bo)}
    free = {}
    for model in ("MedGemma 4B", "Llama 3.2 3B"):
        rows = [labels[i["item"]] | {"flagged": flags[i["item"]]} for i in items
                if i["kind"] == "free_daily_check" and i["model"] == model]
        flagged = [r for r in rows if r["flagged"]]
        unflagged = [r for r in rows if not r["flagged"]]
        free[model] = {"flagged": len(flagged),
                       "flagged_misstates_order": sum(r["label"] == "misstates_order" for r in flagged),
                       "unflagged": len(unflagged),
                       "unflagged_misstates_order": sum(r["label"] == "misstates_order" for r in unflagged)}
    return {"llama_comparison_filter": llama, "free_daily_check": free}


def main():
    report = {}
    for name, rel in SETS.items():
        p = os.path.join(DATA, rel)
        if os.path.exists(p):
            report[name] = summarize(json.load(open(p)))
    report["v2_review"] = summarize_v2_review()
    json.dump(report, open(os.path.join(DATA, "labels_summary.json"), "w"), indent=1)
    json.dump(report, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
