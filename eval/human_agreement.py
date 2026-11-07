import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MANIFEST = os.path.join(HERE, "labeling", "queue_manifest.json")
HUMAN = os.path.join(DATA, "human_labels", "parker_labels.json")
CATS = ["faithful", "misstates_order", "unsupported_claim"]
MODEL_NAMES = {"claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5-5": "Claude Sonnet 5.5"}
WORDS = {"faithful": "faithful", "misstates_order": "misstates order", "unsupported_claim": "unsupported claim"}


def cohen_kappa(pairs, cats):
    n = len(pairs)
    if n == 0:
        return None
    po = sum(a == b for a, b in pairs) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[c] * cb[c] for c in cats) / (n * n)
    return None if pe == 1 else (po - pe) / (1 - pe)


def binary(label):
    return "misstates_order" if label == "misstates_order" else "not_misstatement"


def load_human(path, invalid=None):
    obj = json.load(open(path))
    if isinstance(obj, dict) and isinstance(obj.get("labels"), list):
        rows = obj["labels"]
    elif isinstance(obj, list):
        rows = obj
    elif isinstance(obj, dict):
        rows = [v for v in obj.values() if isinstance(v, dict)]
    else:
        sys.exit(f"{path}: not a labels file")
    out = {}
    for r in rows:
        if not isinstance(r, dict) or not r.get("item_id"):
            continue
        if r.get("label") in CATS:
            out[r["item_id"]] = r
        elif r.get("label") is not None and invalid is not None:
            invalid.append((r["item_id"], r.get("label")))
    return out


def load_adopted(manifest):
    h2 = {r["id"]: r for r in json.load(open(os.path.join(DATA, "heldout2", "labels_h2.json"))) if r["filter"] == "layer"}
    review = {r["item"]: r for r in json.load(open(os.path.join(DATA, "v2_review", "labels.json")))}
    adopted = {}
    for it in manifest["items"]:
        s, src = it["stratum"], it["source"]
        if s in ("h2", "pair"):
            r = h2[src["h2_id"]]
            adopted[it["id"]] = {"label": r["label"], "error_type": None, "stratum": "h2_" + r["label"] if s == "h2" else "pair", "ref": src["h2_id"],
                                 "contested": r.get("reader1") != r.get("reader2"), "same_ingredient": "yes" if s == "pair" else None}
        elif s == "open_model":
            r = review[src["item"]]
            et = (r.get("error_type") or "none").split("|")[0]
            adopted[it["id"]] = {"label": r["label"], "error_type": None if et == "none" else et, "stratum": "open_model", "ref": src["item"],
                                 "model": src["model"], "contested": r.get("reader1") != r.get("reader2")}
        elif s == "claude_free_daily":
            adopted[it["id"]] = {"label": None, "error_type": None, "stratum": "claude_" + src["model"], "ref": f"{src['model']} {src['case_id']}",
                                 "model": MODEL_NAMES[src["model"]], "flag": True, "contested": False}
        else:
            sys.exit(f"unknown stratum {s}")
    return adopted


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"


def fmt_kappa(k):
    return "n/a" if k is None else f"{k:.2f}"


def stratum_report(ids, adopted, human):
    labeled = [i for i in ids if i in human]
    counts = collections.Counter(human[i]["label"] for i in labeled)
    with_adopted = [i for i in labeled if adopted[i]["label"]]
    adopted_counts = collections.Counter(adopted[i]["label"] for i in with_adopted)
    agree = sum(human[i]["label"] == adopted[i]["label"] for i in with_adopted)
    pairs3 = [(adopted[i]["label"], human[i]["label"]) for i in with_adopted]
    pairs2 = [(binary(a), binary(b)) for a, b in pairs3]
    both_miss = [i for i in with_adopted if adopted[i]["label"] == "misstates_order" == human[i]["label"]]
    with_et = [i for i in both_miss if adopted[i]["error_type"]]
    sure = [i for i in with_adopted if human[i].get("confidence") != "unsure"]
    contested = [i for i in with_adopted if adopted[i].get("contested")]
    return {"n": len(ids), "n_labeled": len(labeled), "human_labels": dict(counts), "adopted_labels": dict(adopted_counts),
            "n_with_adopted_label": len(with_adopted), "agree": agree, "percent_agreement": round(100 * agree / len(with_adopted), 1) if with_adopted else None,
            "adopted_label_varies": len(adopted_counts) > 1,
            "kappa_three_labels": cohen_kappa(pairs3, CATS),
            "kappa_misstatement_binary": cohen_kappa(pairs2, ["misstates_order", "not_misstatement"]),
            "both_misstates_order": len(both_miss), "n_with_adopted_error_type": len(with_et),
            "error_type_agree": sum(adopted[i]["error_type"] == human[i].get("error_type") for i in with_et) if with_et else None,
            "n_sure": len(sure), "agree_among_sure": sum(human[i]["label"] == adopted[i]["label"] for i in sure),
            "unsure": sum(human[i].get("confidence") == "unsure" for i in labeled),
            "n_contested": len(contested), "agree_among_contested": sum(human[i]["label"] == adopted[i]["label"] for i in contested)}


def build_report(manifest, adopted, human):
    by_stratum = collections.defaultdict(list)
    for it in manifest["items"]:
        by_stratum[adopted[it["id"]]["stratum"]].append(it["id"])
    order = ["h2_misstates_order", "h2_unsupported_claim", "h2_faithful", "pair", "open_model", "claude_claude-haiku-5-5", "claude_claude-sonnet-5-5"]
    report = {"n_items": len(manifest["items"]), "n_labeled": sum(1 for it in manifest["items"] if it["id"] in human), "strata": {}, "pooled": {}}
    for s in order:
        report["strata"][s] = stratum_report(by_stratum.get(s, []), adopted, human)
    pooled = {"h2": [i for s in order[:3] for i in by_stratum.get(s, [])],
              "open_model": by_stratum.get("open_model", []),
              "pair": by_stratum.get("pair", []),
              "all_with_adopted_label": [i for s in order[:5] for i in by_stratum.get(s, [])],
              "claude_flagged": [i for s in order[5:] for i in by_stratum.get(s, [])]}
    for name, ids in pooled.items():
        report["pooled"][name] = stratum_report(ids, adopted, human)
    pair_ids = [i for i in by_stratum.get("pair", []) if i in human]
    report["pairs"] = {"n": len(by_stratum.get("pair", [])), "n_labeled": len(pair_ids),
                       "n_contested_model_label": sum(adopted[i].get("contested", False) for i in by_stratum.get("pair", [])),
                       "same_ingredient": dict(collections.Counter(human[i].get("same_ingredient") or "unanswered" for i in pair_ids)),
                       "double_dose_risk": dict(collections.Counter(human[i].get("double_dose_risk") or "unanswered" for i in pair_ids)),
                       "labels": dict(collections.Counter(human[i]["label"] for i in pair_ids))}
    report["disagreements"] = [
        {"item_id": i, "stratum": adopted[i]["stratum"], "ref": adopted[i]["ref"], "adopted": adopted[i]["label"], "human": human[i]["label"],
         "human_error_type": human[i].get("error_type"), "confidence": human[i].get("confidence"), "model_readers_disagreed": adopted[i].get("contested", False),
         "note": human[i].get("note", "")}
        for it in manifest["items"] for i in [it["id"]] if i in human and adopted[i]["label"] and human[i]["label"] != adopted[i]["label"]]
    report["claude_by_model"] = {}
    for s in order[5:]:
        ids = [i for i in by_stratum.get(s, []) if i in human]
        c = collections.Counter(human[i]["label"] for i in ids)
        report["claude_by_model"][s.replace("claude_", "")] = {"flagged": len(by_stratum.get(s, [])), "labeled": len(ids), "misstates_order": c["misstates_order"],
                                                               "unsupported_claim": c["unsupported_claim"], "faithful": c["faithful"],
                                                               "error_types": dict(collections.Counter(human[i].get("error_type") or "none" for i in ids if human[i]["label"] == "misstates_order"))}
    return report


def of(n_labeled, n_total):
    return str(n_total) if n_labeled == n_total else f"{n_labeled} of {n_total} labeled so far"


def kappa_phrase(s):
    k3, k2 = s["kappa_three_labels"], s["kappa_misstatement_binary"]
    if k3 is None and k2 is None:
        return "Cohen's kappa is undefined because both raters used one label"
    parts = []
    if k3 is not None:
        parts.append(f"Cohen's kappa {k3:.2f} over the three labels")
    if k2 is not None:
        parts.append(f"{k2:.2f} for misstatement against not" if parts else f"Cohen's kappa {k2:.2f} for misstatement against not")
    phrase = " and ".join(parts)
    if not s["adopted_label_varies"]:
        phrase += ", which is 0 by construction because the model label does not vary in this set"
    return phrase


def label_counts_phrase(counts):
    return ", ".join(f"{counts.get(c, 0)} {WORDS[c]}" for c in CATS)


def sentences(report, manifest):
    S = report["strata"]
    P = report["pooled"]
    pool = manifest.get("h2_pool", {})
    cb = report["claude_by_model"]
    hk, sn = cb.get("claude-haiku-5-5", {}), cb.get("claude-sonnet-5-5", {})
    out = []
    scope = f"{report['n_items']} sampled outputs: " if report["n_labeled"] == report["n_items"] else f"{report['n_labeled']} of {report['n_items']} sampled outputs so far: "
    out.append(
        "One human labeler (the author), blind to the model labels and the script flags, labeled " + scope
        + f"{P['h2']['n']} round h2 releases (all {S['h2_misstates_order']['n']} that the model readers labeled misstates order, all {S['h2_unsupported_claim']['n']} they labeled unsupported claim, "
        + f"and {S['h2_faithful']['n']} faithful texts drawn at random with a fixed seed from the {pool.get('faithful_outside_pairs', '?')} faithful releases outside the same-ingredient list), "
        + f"the {S['pair']['n']} same-ingredient pairs that version 2.1 releases, the {S['open_model']['n']} open-model releases in the blind review sample (20 per model), "
        + f"and the {P['claude_flagged']['n']} Claude free daily outputs the script flagged ({hk.get('flagged', 0)} Claude Haiku 5.5 and {sn.get('flagged', 0)} Claude Sonnet 5.5). "
        + "The items were shuffled and shown without model names, labels, or flags, and labeled under the round h2 rubric with its two addenda.")
    h2 = P["h2"]
    if h2["n_with_adopted_label"]:
        out.append(
            f"On the round h2 releases ({of(h2['n_labeled'], h2['n'])}), the human agreed with the adopted label on {h2['agree']} of {h2['n_with_adopted_label']} "
            f"({pct(h2['agree'], h2['n_with_adopted_label'])}; {kappa_phrase(h2)}): "
            f"{S['h2_misstates_order']['agree']} of {S['h2_misstates_order']['n_with_adopted_label']} misstatements, "
            f"{S['h2_unsupported_claim']['agree']} of {S['h2_unsupported_claim']['n_with_adopted_label']} unsupported claims, "
            f"and {S['h2_faithful']['agree']} of {S['h2_faithful']['n_with_adopted_label']} faithful texts."
            + (f" On the {h2['n_contested']} of these outputs where the first two model readers had disagreed, the human agreed with the adopted label on {h2['agree_among_contested']}." if h2["n_contested"] else ""))
    pr = report["pairs"]
    if pr["n_labeled"]:
        si, dd = pr["same_ingredient"], pr["double_dose_risk"]
        out.append(
            f"Of the same-ingredient pairs ({of(pr['n_labeled'], pr['n'])}), the human judged {si.get('yes', 0)} to name one ingredient under two names "
            f"({si.get('no', 0)} no, {si.get('unsure', 0)} unsure), saw a double-dose risk in {dd.get('yes', 0)} ({dd.get('no', 0)} no, {dd.get('unsure', 0)} unsure), "
            f"and labeled the texts {label_counts_phrase(pr['labels'])}. The adopted label for all {pr['n']} is faithful under rule 1 of the addendum"
            + (f", a two-of-three majority for {pr['n_contested_model_label']} of them" if pr["n_contested_model_label"] else "")
            + "; the version 2.1 texts are identical to the round h2 texts those labels were given to.")
    om = S["open_model"]
    if om["n_labeled"]:
        ad = om["adopted_labels"]
        adopted_phrase = "all labeled faithful by the model readers" if set(ad) == {"faithful"} else "which the model readers labeled " + label_counts_phrase(ad)
        out.append(
            f"Of the open-model releases in the blind review sample ({of(om['n_labeled'], om['n'])}), {adopted_phrase}, the human labeled "
            f"{label_counts_phrase(om['human_labels'])} ({pct(om['agree'], om['n_with_adopted_label'])} agreement).")
    if hk.get("labeled") or sn.get("labeled"):
        out.append(
            f"Of the flagged Claude Haiku 5.5 outputs ({of(hk.get('labeled', 0), hk.get('flagged', 0))}), the human labeled {hk.get('misstates_order', 0)} as misstating an order, "
            f"{hk.get('unsupported_claim', 0)} as unsupported claims, and {hk.get('faithful', 0)} faithful; of the flagged Claude Sonnet 5.5 outputs ({of(sn.get('labeled', 0), sn.get('flagged', 0))}), "
            f"{sn.get('misstates_order', 0)}, {sn.get('unsupported_claim', 0)}, and {sn.get('faithful', 0)}. "
            f"No model reader labeled these outputs, so the flags are compared with the human labels only.")
    al = P["all_with_adopted_label"]
    if al["n_with_adopted_label"]:
        enriched = S["h2_misstates_order"]["n"] + S["h2_unsupported_claim"]["n"]
        out.append(
            f"Over the {al['n_with_adopted_label']} labeled outputs that have an adopted model label, agreement was {al['agree']} of {al['n_with_adopted_label']} "
            f"({pct(al['agree'], al['n_with_adopted_label'])}; {kappa_phrase(al)}). "
            + (f"The sample includes every round h2 misstatement and unsupported claim ({enriched} outputs), so these figures describe agreement on the sample, not a rate in the released texts. " if enriched else "")
            + f"The human marked {al['unsure']} of these {al['n_with_adopted_label']} labels unsure; among the {al['n_sure']} sure labels, agreement was {al['agree_among_sure']} of {al['n_sure']}.")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=HUMAN)
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument("--json", default=None, help="write the full report here")
    args = ap.parse_args()
    manifest = json.load(open(args.manifest))
    if not os.path.exists(args.labels):
        sys.exit(f"no label file at {args.labels}. Export from the labeling page and save it there, or pass --labels PATH.")
    invalid = []
    human = load_human(args.labels, invalid)
    adopted = load_adopted(manifest)
    unknown = sorted(set(human) - set(adopted))
    if unknown:
        print(f"warning: {len(unknown)} labels have item ids not in the manifest and are ignored: {unknown[:5]}")
        human = {k: v for k, v in human.items() if k in adopted}
    if invalid:
        print(f"warning: {len(invalid)} records have a label outside {CATS} and are treated as unlabeled: {invalid[:5]}")
    report = build_report(manifest, adopted, human)
    report["sentences"] = sentences(report, manifest)
    print(f"items {report['n_items']}, labeled {report['n_labeled']}\n")
    print(f"{'stratum':28} {'n':>4} {'labeled':>8} {'agree':>7} {'pct':>5} {'kappa3':>7} {'kappa2':>7}  human labels")
    for name, s in list(report["strata"].items()) + [("pooled " + k, v) for k, v in report["pooled"].items()]:
        if s["n_with_adopted_label"]:
            agree, p = f"{s['agree']}/{s['n_with_adopted_label']}", pct(s["agree"], s["n_with_adopted_label"])
            star = "" if s["adopted_label_varies"] else "*"
            k3, k2 = fmt_kappa(s["kappa_three_labels"]) + star, fmt_kappa(s["kappa_misstatement_binary"]) + star
        else:
            agree = p = k3 = k2 = "-"
        print(f"{name:28} {s['n']:>4} {s['n_labeled']:>8} {agree:>7} {p:>5} {k3:>7} {k2:>7}  {s['human_labels']}")
    print("\n* the model label does not vary in this set, so kappa is 0 by construction (expected agreement equals observed agreement) or n/a when both raters used one label; the pooled h2 and all rows carry the kappa information.")
    print("\npairs:", json.dumps(report["pairs"]))
    print("claude flags by model:", json.dumps(report["claude_by_model"]))
    if report["disagreements"]:
        print(f"\ndisagreements with the adopted label ({len(report['disagreements'])}):")
        for d in report["disagreements"]:
            print(f"  {d['item_id']} [{d['stratum']}] {d['ref']}: adopted {d['adopted']}, human {d['human']}"
                  + (f" ({d['human_error_type']})" if d["human_error_type"] else "") + (", unsure" if d["confidence"] == "unsure" else "")
                  + (", model readers had disagreed" if d["model_readers_disagreed"] else "") + (f": {d['note']}" if d["note"] else ""))
    print("\nSentences for the draft:\n")
    for s in report["sentences"]:
        print(s + "\n")
    if args.json:
        with open(args.json, "w") as f:
            json.dump(report, f, indent=1)
            f.write("\n")
        print(f"report written to {args.json}")


if __name__ == "__main__":
    main()
