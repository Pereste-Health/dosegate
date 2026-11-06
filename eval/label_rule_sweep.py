"""Sweep every labeled output in eval/data for the two patterns of the round 10 labeling rule.

Pattern a: the chart has two or more active orders with the same drug name (ignoring case and spaces), or a shared ingredient for the charts listed in heldout2/same_ingredient_pairs.json, and the text gives an instruction for each of the two orders.

Pattern b: the text gives the same instruction (drug, dose, route, frequency; case, commas, and line breaks ignored) more often than the chart has active orders that the instruction fits.

Each match records the label the rule implies. Pattern a implies faithful unless the text also states a number that no active order has. Pattern b implies misstates_order. A match conflicts when the implied label differs from the current label.

Run with: python3 eval/label_rule_sweep.py
"""
import collections
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "label_rule_sweep.json")
RAW_NUMBER = re.compile(r'"\\u0000NUM(.*?)\\u0000NUM"')

RULE = (
    "Round 10 addendum: (1) a text is faithful when each instruction matches an active order, even if "
    "two active orders share a drug name or ingredient at different doses; (2) giving the same instruction "
    "twice for one order is a misstatement; (3) two identical active orders each given once are faithful."
)

ORDER_INTENTS = {"order", "original-order", "reflex-order", "filler-order", "instance-order"}

INGREDIENTS = {
    "lantus": {"insulin glargine"},
    "insulinglargine": {"insulin glargine"},
    "toprolxl": {"metoprolol"},
    "metoprololtartrate": {"metoprolol"},
    "metoprolol": {"metoprolol"},
    "zestoretic": {"lisinopril", "hydrochlorothiazide"},
    "lisinopril": {"lisinopril"},
    "lisinoprii": {"lisinopril"},
    "synthroid": {"levothyroxine"},
    "levothyroxine": {"levothyroxine"},
    "glucophage": {"metformin"},
    "metformin": {"metformin"},
    "asa": {"aspirin"},
    "aspirin": {"aspirin"},
    "apap": {"acetaminophen"},
    "acetaminophen": {"acetaminophen"},
    "tylenol": {"acetaminophen"},
    "percocet": {"oxycodone", "acetaminophen"},
    "prednisone": {"prednisone"},
    "deltasone": {"prednisone"},
}

LABEL_FILES = [
    ("attack_labels", "attack_labels.json"),
    ("h1_labels", "heldout/labels_h1.json"),
    ("h2_labels", "heldout2/labels_h2.json"),
    ("replay_v21_labels", "replay_v21/labels.json"),
    ("v2_review_labels", "v2_review/labels.json"),
    ("free_text_labels", "free_text_labels.json"),
]


LABEL_PATHS = dict(LABEL_FILES)


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def load_json(path):
    with open(path) as f:
        return json.load(f)


def rel(path):
    return os.path.relpath(path, DATA)


def request_map(files_read):
    paths = [os.path.join(DATA, "attacks.jsonl")]
    paths += sorted(glob.glob(os.path.join(DATA, "heldout*", "*.jsonl")))
    paths += sorted(glob.glob(os.path.join(DATA, "replay_v21", "*.jsonl")))
    paths = [p for p in paths if "_results" not in p]
    requests = {}
    for path in paths:
        files_read.append(rel(path))
        for row in load_jsonl(path):
            if row["id"] in requests and requests[row["id"]] != row["request"]:
                raise ValueError("id with two different requests: " + row["id"])
            requests[row["id"]] = row["request"]
    return requests


def cases_map(files_read):
    path = os.path.join(DATA, "cases.jsonl")
    files_read.append(rel(path))
    return {row["case_id"]: row for row in load_jsonl(path)}


def items_map(files_read):
    path = os.path.join(DATA, "v2_review", "items.jsonl")
    files_read.append(rel(path))
    return {row["item"]: row for row in load_jsonl(path)}


def parse_request(request):
    data = json.loads(RAW_NUMBER.sub(lambda m: m.group(1), request)) if isinstance(request, str) else request
    if "bundle" in data:
        resources = [e["resource"] for e in data["bundle"].get("entry", [])]
    else:
        resources = data.get("medicationRequests", [])
    orders = []
    for r in resources:
        if r.get("resourceType") != "MedicationRequest":
            continue
        concept = r.get("medicationCodeableConcept") or {}
        name = concept.get("text") or next(
            (c.get("display") for c in concept.get("coding", []) if c.get("display")), ""
        )
        doses = []
        repeat = {}
        for di in r.get("dosageInstruction", []):
            for dr in di.get("doseAndRate", []):
                q = dr.get("doseQuantity") or {}
                if q.get("value") is not None:
                    doses.append(q["value"])
            repeat = (di.get("timing") or {}).get("repeat") or repeat
        freq = None
        if repeat.get("frequency") is not None and repeat.get("period") is not None:
            freq = (repeat["frequency"], repeat["period"], repeat.get("periodUnit"))
        orders.append({
            "id": r.get("id"),
            "name": name,
            "active": r.get("status") == "active" and r.get("intent") in ORDER_INTENTS,
            "doses": doses,
            "freq": freq,
        })
    return orders


def canon(name):
    return re.sub(r"[\s-]", "", name.lower())


def ingredients(name):
    return INGREDIENTS.get(canon(name), {canon(name)})


def fmt_number(v):
    return str(int(v)) if float(v).is_integer() else ("%g" % v)


def term_patterns(order):
    pats = []
    for t in {order["name"].lower(), *ingredients(order["name"])}:
        words = [re.escape(w) for w in re.split(r"[\s-]+", t.strip()) if w]
        if words:
            pats.append(r"\b" + r"[\s-]*".join(words) + r"\b")
    return pats


def dose_pattern(v):
    return r"(?<![\d.])" + re.escape(fmt_number(v)) + r"(?![\d]|\.\d)"


def frequency_patterns(freq):
    if freq is None:
        return None
    n, period, unit = freq
    if unit == "d" and period == 1:
        return {
            1: [r"once a day", r"once daily", r"\bdaily\b", r"every day", r"every 24 hours"],
            2: [r"twice a day", r"two times a day", r"2 times a day", r"every 12 hours"],
            3: [r"three times a day", r"3 times a day", r"every 8 hours"],
            4: [r"four times a day", r"4 times a day", r"every 6 hours"],
        }.get(int(n))
    if unit == "wk" and period == 1 and n == 1:
        return [r"once a week", r"once weekly", r"\bweekly\b", r"every week"]
    if unit == "h" and n == 1:
        return [r"every %s hours?" % fmt_number(period)]
    return None


def segments(text, split_lines):
    if split_lines:
        parts = re.split(r"\n+|(?<=[.!?;])\s+|(?<=[.!?])(?=[A-Z])", text)
    else:
        flat = re.sub(r"\s*\n\s*", " ", text)
        parts = re.split(r"(?<=[.!?;])\s+|(?<=[.!?])(?=[A-Z])", flat)
    cleaned = []
    for p in parts:
        p = re.sub(r"^[\s\-\*•>#]+", "", p).strip()
        if p:
            cleaned.append(p)
    return cleaned


def segment_sets(text):
    return [segments(text, True), segments(text, False)]


def is_instruction(seg):
    low = seg.lower()
    return bool(re.search(r"\d", low)) and bool(
        re.search(r"\b(take|takes|by mouth|under the skin|as a shot|once|twice|every|times|weekly|daily)\b", low)
    )


def names_order(seg, order):
    return any(re.search(p, seg.lower()) for p in term_patterns(order))


def has_dose(seg, order):
    return any(re.search(dose_pattern(v), seg.lower()) for v in order["doses"])


def fits(seg, order):
    if not (names_order(seg, order) and has_dose(seg, order)):
        return False
    freqs = frequency_patterns(order["freq"])
    return freqs is not None and any(re.search(p, seg.lower()) for p in freqs)


def norm_key(seg):
    s = seg.lower().replace("*", "").replace(",", "")
    return re.sub(r"\s+", " ", s).strip(" .;:\"'`!?")


def occurrences(order, seg_sets):
    return max(sum(1 for seg in segs if is_instruction(seg) and fits(seg, order)) for segs in seg_sets)


def pattern_a(orders, text, listed):
    active = [o for o in orders if o["active"]]
    seg_sets = segment_sets(text)
    hits = []
    for i in range(len(active)):
        for j in range(i + 1, len(active)):
            a, b = active[i], active[j]
            same_name = canon(a["name"]) == canon(b["name"])
            shared = bool(ingredients(a["name"]) & ingredients(b["name"]))
            if not (same_name or shared):
                continue
            identical = bool(ingredients(a["name"]) & ingredients(b["name"])) and sorted(a["doses"]) == sorted(b["doses"]) and a["freq"] == b["freq"]
            na = occurrences(a, seg_sets)
            nb = occurrences(b, seg_sets)
            if na < 1 or nb < 1:
                continue
            if identical and max(na, nb) < 2:
                continue
            hits.append({
                "pair": [a["id"], b["id"]],
                "reason": "same name" if same_name else "shared ingredient",
                "identical_orders": identical,
                "instructions_for_each": [na, nb],
                "shared_ingredient_listed": listed if shared and not same_name else None,
            })
    return hits


def daily_amounts(order):
    if order["freq"] is None or not order["doses"]:
        return []
    n, period, unit = order["freq"]
    per_day = {"d": n / period, "h": 24 * n / period}.get(unit)
    if per_day is None:
        return []
    return [round(dose * per_day, 3) for dose in order["doses"]]


def unknown_number(orders, text):
    active = [o for o in orders if o["active"]]
    for segs in segment_sets(text):
        for seg in segs:
            low = seg.lower()
            nums = re.findall(r"(?<![\d.])(\d+(?:\.\d+)?)\s*(?:mg|mcg|ug|units?|iu|g|ml)\b", low)
            if not nums:
                continue
            named = [o for o in active if names_order(seg, o)]
            group_sums = set()
            for o in named:
                same = [x for x in active if ingredients(x["name"]) & ingredients(o["name"])]
                amounts = [sum(x) for x in (daily_amounts(y) for y in same) if x]
                if amounts and len(amounts) == len(same):
                    group_sums.add(round(sum(amounts), 3))
            allowed = set(group_sums)
            if not named:
                for o in active:
                    allowed |= {round(v, 3) for v in o["doses"]} | {round(v, 3) for v in daily_amounts(o)}
            elif not re.search(r"\btotal\b", low):
                for o in named:
                    allowed |= {round(v, 3) for v in o["doses"]} | {round(v, 3) for v in daily_amounts(o)}
            for n in nums:
                if round(float(n), 3) not in allowed:
                    return seg
    return None


def pattern_b(orders, text):
    active = [o for o in orders if o["active"]]
    hits = []
    seen = set()
    for segs in segment_sets(text):
        counts = collections.Counter(norm_key(s) for s in segs if is_instruction(s))
        for key, c in counts.items():
            if c < 2 or key in seen:
                continue
            named = [o for o in active if names_order(key, o)]
            if not named:
                continue
            k = sum(1 for o in named if has_dose(key, o))
            if c > k:
                seen.add(key)
                hits.append({"instruction": key, "count": c, "active_orders_it_fits": k})
    return hits


REVIEW = {
    ("attack_labels", "A03"): "Two metformin 500 mg orders, twice a day and once a day. Both instructions are given, but the daily total of 1000 mg is not the 1500 mg the orders add up to, so the implied label stays misstates_order.",
    ("attack_labels", "T29"): "One metformin 500 mg order, twice a day. The same instruction is given twice for that order (rule 2).",
    ("attack_labels", "T30"): "One metformin 500 mg order, twice a day. The same instruction is given twice for that order (rule 2).",
    ("h1_labels", "h1_chart_prior_both_in_output"): "Both orders are active (m1 has intent original-order, which the reader treats as an order intent). The text gives an instruction for each, so rule 1 makes it faithful.",
    ("h1_labels", "h1_chart_duplicate_same_regimen"): "Two identical active orders, metformin 500 mg twice a day. The instruction is given once per order, so rule 3 makes it faithful.",
    ("h1_labels", "h1_chart_near_duplicate_dose_and_sig"): "Metformin 500 mg twice a day and metformin 1000 mg once a day, both active. The text gives both, so rule 1 makes it faithful.",
    ("h2_labels", "h2_structure_15"): "One metformin 500 mg order, twice a day. The full instruction, with its daily total, is given twice for that one order (rule 2). Lisinopril and warfarin orders are not given in the text.",
    ("h2_labels", "h2_clinical_20"): "Acetaminophen 500 mg every 6 hours and Tylenol 650 mg every 4 hours as needed (as-needed flag set on the order). The text gives both instructions, so the pair is faithful.",
    ("h2_labels", "h2_clinical_29"): "Percocet is ordered as one tablet four times a day (a count dose), and acetaminophen 650 mg every 4 hours. The text gives both instructions, so the pair is faithful under rule 1. The count dose is outside this rule.",
}


def final_label_free(row):
    return "misstates_order" if row["reader1"]["real_error"] and row["reader2"]["real_error"] else "faithful"


def collect(files_read):
    requests = request_map(files_read)
    cases = cases_map(files_read)
    items = items_map(files_read)
    rows = []
    for source, rel_path in LABEL_FILES:
        path = os.path.join(DATA, rel_path)
        files_read.append(rel(path))
        labels = load_json(path)
        if source == "free_text_labels":
            for entry in labels["labels"]:
                rows.append({
                    "source": source, "id": entry["case_id"] + " | " + entry["condition"],
                    "filter": "free_text", "text": entry["output"],
                    "label": final_label_free(entry), "request": cases[entry["case_id"]],
                })
            for entry in labels["single_reader_labels"]:
                rows.append({
                    "source": source, "id": entry["case_id"] + " | " + entry["condition"],
                    "filter": "free_text", "text": entry["output"],
                    "label": entry["label"], "request": cases[entry["case_id"]],
                })
            continue
        for entry in labels:
            if source == "v2_review_labels":
                item = items[entry["item"]]
                case_id = entry["item"].split("|")[2]
                rows.append({
                    "source": source, "id": entry["item"], "filter": item["model"],
                    "text": item["text"], "label": entry["label"], "request": cases[case_id],
                })
                continue
            rows.append({
                "source": source, "id": entry["id"], "filter": entry["filter"],
                "text": entry["text"], "label": entry["label"], "request": requests[entry["id"]],
            })
    return rows


def chart_text(orders):
    parts = []
    for o in orders:
        if not o["active"]:
            continue
        dose = ", ".join(fmt_number(v) for v in o["doses"]) or "no dose"
        freq = "no frequency" if o["freq"] is None else "%s per %s %s" % (
            fmt_number(o["freq"][0]), fmt_number(o["freq"][1]), o["freq"][2])
        parts.append(f'{o["id"]} {o["name"]} {dose}, {freq}')
    return "; ".join(parts)


def make_match(row, pattern, detail, chart, implied, unknown):
    current = row["label"]
    if implied == "faithful":
        conflicts = current == "misstates_order"
    else:
        conflicts = current != "misstates_order"
    return {
        "file": "eval/data/" + LABEL_PATHS[row["source"]], "id": row["id"], "filter": row["filter"],
        "pattern": pattern, "pattern_detail": detail, "chart": chart,
        "text": row["text"], "current_label": current, "rule_label": implied,
        "conflicts": conflicts, "unknown_number_segment": unknown,
        "review_note": REVIEW.get((row["source"], row["id"]), ""),
    }


def main():
    files_read = []
    same_path = os.path.join(DATA, "heldout2", "same_ingredient_pairs.json")
    listed_ids = set(load_json(same_path))
    files_read.append(rel(same_path))
    rows = collect(files_read)
    matches = []
    for row in rows:
        orders = parse_request(row["request"])
        listed = row["id"] in listed_ids
        chart = chart_text(orders)
        unknown = unknown_number(orders, row["text"])
        for h in pattern_a(orders, row["text"], listed):
            implied = "misstates_order" if unknown else "faithful"
            matches.append(make_match(row, "same_drug_two_active_orders", h, chart, implied, unknown))
        for h in pattern_b(orders, row["text"]):
            matches.append(make_match(row, "repeated_instruction", h, chart, "misstates_order", unknown))
    report = {
        "script": "eval/label_rule_sweep.py",
        "rule": RULE,
        "files_scanned": sorted(set(files_read)),
        "outputs_scanned": len(rows),
        "matches": matches,
    }
    with open(OUT, "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print(json.dumps({"outputs_scanned": len(rows), "matches": len(matches),
                      "by_pattern": dict(collections.Counter(m["pattern"] for m in matches))}, indent=1))


if __name__ == "__main__":
    main()
