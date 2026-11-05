import collections, json, os, sys

from score import DATA

SETS = {"development": "attack_labels.json", "h1": "heldout/labels_h1.json", "h2": "heldout2/labels_h2.json"}
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


def main():
    report = {}
    for name, rel in SETS.items():
        p = os.path.join(DATA, rel)
        if os.path.exists(p):
            report[name] = summarize(json.load(open(p)))
    json.dump(report, open(os.path.join(DATA, "labels_summary.json"), "w"), indent=1)
    json.dump(report, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
