import collections, glob, json, math, os, sys

from score import DATA

ROUNDS = {"h2": ("heldout2", "labels_h2.json", "same_ingredient_pairs.json"),
          "h3": ("heldout3", "labels_h3.json", "same_ingredient_pairs.json"),
          "h4": ("heldout4", "labels_h4.json", "same_ingredient_pairs.json")}
CATS = ["faithful", "misstates_order", "unsupported_claim"]
FILTERS = ("layer", "baseline")


def kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in CATS) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 2)


def sign_test(b, c):
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p)


def load_round(d):
    requests, results = {}, {}
    for path in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
        name = os.path.basename(path)[:-6]
        if name.endswith("_results"):
            continue
        for line in open(path):
            if line.strip():
                row = json.loads(line)
                requests[row["id"]] = name
        for line in open(path[:-6] + "_results.jsonl"):
            if line.strip():
                row = json.loads(line)
                results[row["id"]] = row
    return requests, results


def filter_row(ids, results, labels, pairs, flt):
    released = [i for i in ids if results[i][flt]["status"] == "ok"]
    lab = {i: labels[(i, flt)]["label"] for i in released if (i, flt) in labels}
    missing = [i for i in released if i not in lab]
    counts = collections.Counter(lab.values())
    same = [i for i in released if i in pairs]
    rows = [labels[(i, flt)] for i in released if (i, flt) in labels]
    reader_pairs = [(r["reader1"], r["reader2"]) for r in rows if r.get("reader1") and r.get("reader2")]
    return {"requests": len(ids), "released": len(released),
            "table2_columns": "misstates_order, one_ingredient_two_names_faithful, unsupported_claim, faithful_not_one_ingredient_two_names (Table 2 counts the two-names column over faithful outputs only)",
            "misstates_order": counts["misstates_order"],
            "one_ingredient_two_names": len(same),
            "one_ingredient_two_names_faithful": sum(1 for i in same if lab.get(i) == "faithful"),
            "unsupported_claim": counts["unsupported_claim"],
            "faithful": counts["faithful"],
            "faithful_not_one_ingredient_two_names": sum(1 for i in released if lab.get(i) == "faithful" and i not in pairs),
            "one_ingredient_two_names_and_misstates_order": sum(1 for i in same if lab.get(i) == "misstates_order"),
            "one_ingredient_two_names_and_unsupported_claim": sum(1 for i in same if lab.get(i) == "unsupported_claim"),
            "refused_as_error": sum(1 for i in ids if results[i][flt]["status"] == "error"),
            "blocked": sum(1 for i in ids if results[i][flt]["status"] == "blocked"),
            "block_reasons": dict(collections.Counter(results[i][flt].get("reason") for i in ids
                                                      if results[i][flt]["status"] == "blocked")),
            "released_without_label": missing,
            "readers_agree": sum(a == b for a, b in reader_pairs), "reader_pairs": len(reader_pairs),
            "kappa": kappa(reader_pairs),
            "third_reader_used": sum(1 for r in rows if r.get("third_reader"))}


def misstated(i, results, labels, flt):
    return results[i][flt]["status"] == "ok" and labels.get((i, flt), {}).get("label") == "misstates_order"


def summarize(name):
    sub, label_file, pairs_file = ROUNDS[name]
    d = os.path.join(DATA, sub)
    requests, results = load_round(d)
    labels = {(r["id"], r["filter"]): r for r in json.load(open(os.path.join(d, label_file)))}
    pairs = set(json.load(open(os.path.join(d, pairs_file))))
    ids = sorted(requests)
    out = {"round": name, "requests": len(ids)}
    for flt in FILTERS:
        out[flt] = filter_row(ids, results, labels, pairs, flt)
    out["by_family"] = {}
    for fam in sorted(set(requests.values())):
        fids = [i for i in ids if requests[i] == fam]
        out["by_family"][fam] = {flt: filter_row(fids, results, labels, pairs, flt) for flt in FILTERS}
    layer_only = [i for i in ids if misstated(i, results, labels, "layer") and not misstated(i, results, labels, "baseline")]
    baseline_only = [i for i in ids if misstated(i, results, labels, "baseline") and not misstated(i, results, labels, "layer")]
    both = [i for i in ids if misstated(i, results, labels, "layer") and misstated(i, results, labels, "baseline")]
    out["discordant_misstatements"] = {
        "comparison_filter_only": len(baseline_only), "layer_only": len(layer_only), "both": len(both),
        "comparison_filter_only_ids": baseline_only, "layer_only_ids": layer_only,
        "exact_two_sided_sign_test_p": sign_test(len(baseline_only), len(layer_only))}
    reader_pairs = [(r["reader1"], r["reader2"]) for r in labels.values() if r.get("reader1") and r.get("reader2")]
    out["both_filters_kappa"] = kappa(reader_pairs)
    out["layer_released_misstatements"] = [
        {"id": i, "family": requests[i], "text": results[i]["layer"]["text"],
         "comparison_filter_released_same_text": results[i]["baseline"]["status"] == "ok"
         and results[i]["baseline"]["text"] == results[i]["layer"]["text"]}
        for i in ids if misstated(i, results, labels, "layer")]
    out["layer_released_unsupported_claims"] = [
        {"id": i, "family": requests[i], "text": results[i]["layer"]["text"]}
        for i in ids if results[i]["layer"]["status"] == "ok"
        and labels.get((i, "layer"), {}).get("label") == "unsupported_claim"]
    return d, out


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "h3"
    d, out = summarize(name)
    json.dump(out, open(os.path.join(d, "summary.json"), "w"), indent=1)
    for flt in FILTERS:
        r = out[flt]
        print(name, flt, "requests", r["requests"], "released", r["released"], "misstates", r["misstates_order"],
              "two_names", r["one_ingredient_two_names"], "unsupported", r["unsupported_claim"],
              "faithful", r["faithful"], "faithful_not_two_names", r["faithful_not_one_ingredient_two_names"],
              "kappa", r["kappa"], "unlabeled", len(r["released_without_label"]))
    dm = out["discordant_misstatements"]
    print("discordant comparison-only", dm["comparison_filter_only"], "layer-only", dm["layer_only"],
          "both", dm["both"], "p", dm["exact_two_sided_sign_test_p"])


if __name__ == "__main__":
    main()
