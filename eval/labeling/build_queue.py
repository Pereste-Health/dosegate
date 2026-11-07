import argparse
import collections
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
DATA = os.path.join(EVAL, "data")
sys.path.insert(0, EVAL)
import score  # noqa: E402

SEED = 20261107
FAITHFUL_SAMPLE = 30
H2_FAMILIES = ["chart", "clinical", "meaning", "model_style", "structure"]
CLAUDE_MODELS = ["claude-haiku-5-5", "claude-sonnet-5-5"]

ROUTE_WORDS = {
    "26643006": "by mouth",
    "34206005": "under the skin",
    "47625008": "into a vein",
    "78421000": "into a muscle",
    "54485002": "in the eye",
    "447694001": "by inhalation",
    "37161004": "by rectum",
    "6064005": "on the skin",
    "46713006": "by nose",
    "10547007": "in the ear",
    "37839007": "under the tongue",
    "45890007": "through a skin patch",
    "16857009": "into the vagina",
}
UNIT_WORDS = {
    "mg": "milligrams", "ug": "micrograms", "mcg": "micrograms", "g": "grams", "mL": "milliliters",
    "[IU]": "international units", "[iU]": "international units", "IU": "international units", "U": "units",
    "{tbl}": "tablets", "{tab}": "tablets", "{cap}": "capsules", "{puff}": "puffs", "[drp]": "drops",
}
PERIOD_WORDS = {"s": "second", "min": "minute", "h": "hour", "d": "day", "wk": "week", "mo": "month", "a": "year"}
MR_COMMON = {"resourceType", "id", "status", "intent", "medicationCodeableConcept", "medicationReference", "dosageInstruction", "subject"}
DOSAGE_COMMON = {"timing", "route", "doseAndRate"}
REPEAT_COMMON = {"frequency", "period", "periodUnit"}

ERROR_TYPES = [
    ["weekly_as_daily", "w", "A weekly dose stated as a daily dose or daily total."],
    ["wrong_daily_arithmetic", "a", "A daily total that does not equal the dose times the number of doses a day."],
    ["sum_of_different_drugs", "s", "Doses of different drugs added into one figure as if it were an amount to take."],
    ["wrong_dose", "d", "A dose that differs from the order."],
    ["wrong_frequency", "q", "A frequency or timing that differs from the order."],
    ["wrong_route", "t", "A route that differs from the order."],
    ["duplicated_instruction", "p", "The same instruction given twice for one order, which a patient can read as a double dose."],
    ["wrong_medicine", "m", "An instruction attached to the wrong medicine, or a medicine the orders do not contain."],
    ["inactive_as_current", "i", "An order that is not active (stopped, cancelled, completed, on hold, draft, or a plan) presented as something to take now."],
    ["conditional_as_fixed", "c", "A conditional or variable order (sliding scale, taper, hold, as needed) presented as one fixed dose."],
    ["other", "o", "Any other misstatement; say what it is in the note."],
]


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def unit_text(code):
    if code is None:
        return ""
    gloss = UNIT_WORDS.get(code)
    return f"{code} ({gloss})" if gloss and gloss != code else str(code)


def quantity_text(q):
    if not isinstance(q, dict):
        return compact(q)
    value = q.get("value")
    unit = q.get("unit") if q.get("unit") is not None else q.get("code")
    parts = [str(value) if value is not None else "(no value)", unit_text(unit)]
    if q.get("unit") is not None and q.get("code") is not None and q["unit"] != q["code"]:
        parts.append(f"(code {q['code']})")
    extra = {k: v for k, v in q.items() if k not in ("value", "unit", "code", "system")}
    if extra:
        parts.append("with extra fields " + compact(extra))
    return " ".join(p for p in parts if p)


def dose_text(dar):
    if not isinstance(dar, list) or not dar:
        return "(no dose)", True
    pieces, notable = [], len(dar) != 1
    for entry in dar:
        if not isinstance(entry, dict):
            pieces.append(compact(entry))
            notable = True
            continue
        if "doseQuantity" in entry:
            pieces.append(quantity_text(entry["doseQuantity"]))
            if isinstance(entry["doseQuantity"], dict) and set(entry["doseQuantity"]) - {"value", "unit", "code", "system"}:
                notable = True
        if "doseRange" in entry:
            r = entry["doseRange"] or {}
            pieces.append(f"range {quantity_text(r.get('low'))} to {quantity_text(r.get('high'))}")
            notable = True
        for k, v in entry.items():
            if k not in ("doseQuantity", "doseRange"):
                pieces.append(f"{k} {compact(v)}")
                notable = True
    return "; ".join(pieces), notable


def route_text(route):
    if route is None:
        return "(no route)", True
    if not isinstance(route, dict):
        return compact(route), True
    out, notable = [], False
    for c in route.get("coding") or []:
        if not isinstance(c, dict):
            out.append(compact(c))
            notable = True
            continue
        code = str(c.get("code")) if c.get("code") is not None else None
        words = ROUTE_WORDS.get(code)
        label = words or c.get("display") or "(unknown route)"
        detail = []
        if c.get("display") and words:
            detail.append(c["display"])
        if code:
            detail.append(f"code {code}")
        if not words:
            notable = True
        out.append(label + (f" ({', '.join(detail)})" if detail else ""))
    if route.get("text"):
        out.append(f"text: {route['text']}")
    extra = {k: v for k, v in route.items() if k not in ("coding", "text")}
    if extra:
        out.append(compact(extra))
        notable = True
    return "; ".join(out) or "(empty route)", notable


def timing_text(timing):
    if timing is None:
        return "(no timing)", True, []
    if not isinstance(timing, dict):
        return compact(timing), True, []
    rep = timing.get("repeat")
    lines, notable = [], False
    words = "(no repeat)"
    raw = ""
    if isinstance(rep, dict):
        f, p, u = rep.get("frequency"), rep.get("period"), rep.get("periodUnit")
        raw = f"frequency {f}, period {p}, periodUnit {u}"
        unit = PERIOD_WORDS.get(u)
        words = None
        if unit and p == 1 and f == 1:
            words = f"once a {unit}"
        elif unit and p == 1 and f == 2 and u == "d":
            words = "twice a day"
        elif unit and p == 1 and isinstance(f, int) and f > 0:
            words = f"{f} times a {unit}"
        elif unit and f == 1 and isinstance(p, (int, float)) and p > 1:
            words = f"every {p:g} {unit}s"
        elif unit and isinstance(f, int) and isinstance(p, (int, float)):
            words = f"{f} times every {p:g} {unit}s"
        if words is None:
            words = "unusual timing"
            notable = True
        for k, v in rep.items():
            if k not in REPEAT_COMMON:
                lines.append(f"timing.repeat.{k}: {compact(v)}")
                notable = True
    elif rep is not None:
        words, notable = compact(rep), True
    for k, v in timing.items():
        if k != "repeat":
            lines.append(f"timing.{k}: {compact(v)}")
            notable = True
    text = f"{words} ({raw})" if raw else words
    return text, notable, lines


def name_text(m):
    cc = m.get("medicationCodeableConcept")
    if isinstance(cc, dict):
        name = cc.get("text")
        details = []
        for c in cc.get("coding") or []:
            if isinstance(c, dict):
                bits = [c.get("display"), f"code {c.get('code')}" if c.get("code") is not None else None,
                        c.get("system", "").split("/")[-1] if c.get("system") else None]
                details.append(", ".join(b for b in bits if b))
                if name is None:
                    name = c.get("display")
            else:
                details.append(compact(c))
        extra = {k: v for k, v in cc.items() if k not in ("text", "coding")}
        if extra:
            details.append(compact(extra))
        return name or "(no name)", "; ".join(d for d in details if d)
    if "medicationReference" in m:
        return "(reference) " + compact(m["medicationReference"]), ""
    if cc is not None:
        return compact(cc), ""
    return "(no medication)", ""


def render_order(m):
    name, name_detail = name_text(m)
    status = m.get("status")
    intent = m.get("intent")
    lines, notable_lines = [], []
    subject = m.get("subject")
    subject_text = None
    if isinstance(subject, dict):
        subject_text = subject.get("reference") or subject.get("display") or compact(subject)
    elif subject is not None:
        subject_text = compact(subject)
    dosages = m.get("dosageInstruction")
    doses = []
    if isinstance(dosages, list) and dosages:
        for n, d in enumerate(dosages, 1):
            if not isinstance(d, dict):
                doses.append({"dose": compact(d), "route": "", "timing": "", "notable": True, "lines": []})
                continue
            dose, dose_notable = dose_text(d.get("doseAndRate"))
            route, route_notable = route_text(d.get("route"))
            timing, timing_notable, timing_lines = timing_text(d.get("timing"))
            extra_lines = [f"{k}: {compact(v)}" for k, v in d.items() if k not in DOSAGE_COMMON]
            doses.append({"n": n if len(dosages) > 1 else None, "dose": dose, "route": route, "timing": timing,
                          "notable": dose_notable or route_notable or timing_notable or bool(extra_lines),
                          "lines": timing_lines + extra_lines})
    else:
        doses.append({"dose": "(no dosageInstruction)", "route": "", "timing": "", "notable": True, "lines": []})
    for k, v in m.items():
        if k not in MR_COMMON:
            notable_lines.append(f"{k}: {compact(v)}")
    return {"id": m.get("id"), "name": name, "name_detail": name_detail, "status": status, "intent": intent,
            "status_notable": status != "active", "intent_notable": intent != "order",
            "subject": subject_text, "doses": doses, "lines": lines, "notable_lines": notable_lines}


def render_request(req):
    context, orders = [], []
    top_patient = req.get("patient")
    mrs = []
    if "bundle" in req:
        b = req["bundle"]
        entries = b.get("entry") if isinstance(b, dict) else None
        entries = entries if isinstance(entries, list) else []
        others = collections.Counter()
        for e in entries:
            res = e.get("resource") if isinstance(e, dict) else None
            if isinstance(res, dict) and res.get("resourceType") == "MedicationRequest":
                mrs.append(res)
            else:
                others[(res or {}).get("resourceType", "(no resource)") if isinstance(res, dict) else "(no resource)"] += 1
        btype = b.get("type") if isinstance(b, dict) else None
        context.append(f"The request is a FHIR Bundle (type {btype}) with {len(entries)} entries, {len(mrs)} of them MedicationRequests.")
        if others:
            context.append("Other resources in the bundle: " + ", ".join(f"{k} ({v})" for k, v in sorted(others.items())) + ".")
        for k, v in (b.items() if isinstance(b, dict) else []):
            if k not in ("resourceType", "type", "entry"):
                context.append(f"bundle.{k}: {compact(v)}")
    if "medicationRequests" in req:
        for m in req["medicationRequests"]:
            if isinstance(m, dict):
                mrs.append(m)
            else:
                context.append("A medicationRequests entry is not an object: " + compact(m))
    if top_patient is not None:
        context.append(f"The request names the patient as {compact(top_patient)}; compare with each order's subject.")
    for k, v in req.items():
        if k not in ("output", "medicationRequests", "bundle", "patient"):
            context.append(f"Request field {k}: {compact(v)}")
    for m in mrs:
        if m.get("resourceType") != "MedicationRequest":
            context.append(f"Entry {m.get('id')} has resourceType {m.get('resourceType')!r}.")
        orders.append(render_order(m))
    subjects = {o["subject"] for o in orders}
    if len(subjects) > 1:
        context.append("The orders name different subjects: " + ", ".join(sorted(str(s) for s in subjects)) + ".")
    if len(subjects) <= 1 and top_patient is None:
        for o in orders:
            o["subject"] = None
    return context, orders


def case_request(case):
    return {"medicationRequests": [dict(m, subject={"reference": "Patient/p1"}) for m in case["medicationRequests"]]}


def raw_view(req):
    return {k: v for k, v in req.items() if k != "output"}


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def h2_rows():
    requests, results = {}, {}
    for fam in H2_FAMILIES:
        for r in load_jsonl(os.path.join(DATA, "heldout2", f"{fam}.jsonl")):
            requests[r["id"]] = (fam, json.loads(r["request"]))
        for r in load_jsonl(os.path.join(DATA, "heldout2", f"{fam}_results.jsonl")):
            results[r["id"]] = r
    return requests, results


def build(seed):
    rng = random.Random(seed)
    requests, results = h2_rows()
    labels = [r for r in json.load(open(os.path.join(DATA, "heldout2", "labels_h2.json"))) if r["filter"] == "layer"]
    pairs = json.load(open(os.path.join(DATA, "heldout2", "same_ingredient_pairs.json")))
    replay = {r["id"]: r for r in load_jsonl(os.path.join(DATA, "replay_v21", "h2_results.jsonl"))}
    cases = {c["case_id"]: c for c in load_jsonl(os.path.join(DATA, "cases.jsonl"))}
    review_items = load_jsonl(os.path.join(DATA, "v2_review", "items.jsonl"))

    by_label = collections.defaultdict(list)
    for r in labels:
        by_label[r["label"]].append(r["id"])
    faithful_pool = sorted(i for i in by_label["faithful"] if i not in set(pairs))
    chosen = set(sorted(by_label["misstates_order"]) + sorted(by_label["unsupported_claim"]) + rng.sample(faithful_pool, FAITHFUL_SAMPLE))

    items = []
    for h2_id in sorted(chosen):
        fam, req = requests[h2_id]
        context, orders = render_request(req)
        items.append({"kind": "text", "stratum": "h2", "context": context, "orders": orders, "raw": raw_view(req),
                      "text": results[h2_id]["layer"]["text"],
                      "source": {"h2_id": h2_id, "family": fam, "results_file": f"heldout2/{fam}_results.jsonl", "filter": "layer"}})
    released_pairs = [p for p in pairs if replay[p]["layer"]["status"] == "ok"]
    for h2_id in released_pairs:
        fam, req = requests[h2_id]
        context, orders = render_request(req)
        items.append({"kind": "pair", "stratum": "pair", "context": context, "orders": orders, "raw": raw_view(req),
                      "text": replay[h2_id]["layer"]["text"],
                      "source": {"h2_id": h2_id, "family": fam, "results_file": "replay_v21/h2_results.jsonl", "filter": "layer", "layer_version": "2.1"}})
    for it in review_items:
        if not it["item"].startswith("lr|"):
            continue
        parts = it["item"].split("|")
        case = cases[parts[2]]
        req = case_request(case)
        context, orders = render_request(req)
        items.append({"kind": "text", "stratum": "open_model", "context": context, "orders": orders, "raw": req, "text": it["text"],
                      "source": {"item": it["item"], "model": it["model"], "case_id": parts[2], "condition": parts[3]}})
    flagged = collections.Counter()
    for model in CLAUDE_MODELS:
        gens = load_jsonl(os.path.join(DATA, f"generations_v2_{model}.jsonl"))
        for g in gens:
            if g["condition"] != "free_daily":
                continue
            case = cases[g["case_id"]]
            audit = score.audit_text(g["output"], score.orders(case))
            if not (audit["unsupported"] or audit["dose_wrong"] or audit["freq_wrong"]):
                continue
            flagged[model] += 1
            req = case_request(case)
            context, orders = render_request(req)
            items.append({"kind": "text", "stratum": "claude_free_daily", "context": context, "orders": orders, "raw": req, "text": g["output"],
                          "source": {"model": model, "case_id": g["case_id"], "condition": "free_daily", "sample": g["sample"], "attempt": g["attempt"],
                                     "generations_file": f"generations_v2_{model}.jsonl"}})
    rng.shuffle(items)
    for n, it in enumerate(items, 1):
        it["id"] = f"q{n:03d}"
    counts = collections.Counter(it["stratum"] for it in items)
    summary = {"seed": seed, "n_items": len(items), "counts": dict(counts),
               "h2_pool": {"misstates_order": len(by_label["misstates_order"]), "unsupported_claim": len(by_label["unsupported_claim"]),
                           "faithful_total": len(by_label["faithful"]), "faithful_outside_pairs": len(faithful_pool), "faithful_sampled": FAITHFUL_SAMPLE},
               "pairs_listed": len(pairs), "pairs_released_by_v21": len(released_pairs),
               "claude_flagged": dict(flagged)}
    return items, summary


def rubric_sections():
    src = open(os.path.join(EVAL, "labeling_protocol.md")).read()

    def paragraph(anchor):
        i = src.find(anchor)
        if i < 0:
            sys.exit(f"anchor not found in labeling_protocol.md: {anchor!r}")
        j = src.find("\n\n", i)
        text = src[i:j if j > 0 else None].strip()
        return text[2:] if text.startswith("> ") else text

    return [
        {"title": "Round h2 rubric", "text": paragraph("> Label each released text")},
        {"title": "Model-output rubric (defines the error types)", "text": paragraph("> Labels: faithful (no misstatement)")},
        {"title": "Addendum, November 5, 2026", "text": paragraph("> Labeling rule: (1)")},
        {"title": "Clarification, November 6, 2026", "text": paragraph("Round 18 clarification, November 6, 2026")},
    ]


def page_items(items):
    keys = ("id", "kind", "context", "orders", "raw", "text")
    return [{k: it[k] for k in keys} for it in items]


def render_page(items, summary, template_path):
    template = open(template_path).read()
    payload = {"items": page_items(items), "rubric": rubric_sections(), "error_types": ERROR_TYPES}
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    marker = "/*__QUEUE_JSON__*/"
    if template.count(marker) != 1:
        sys.exit("template must contain the queue marker exactly once")
    return template.replace(marker, blob)


def full_document(body):
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<style>html{color-scheme:light}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>\n'
            '</head>\n<body>\n')
    return head + body + "\n</body>\n</html>\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--template", default=os.path.join(HERE, "label_tool_template.html"))
    ap.add_argument("--out", default=os.path.join(HERE, "label_tool.html"))
    ap.add_argument("--manifest", default=os.path.join(HERE, "queue_manifest.json"))
    ap.add_argument("--artifact-body", default=None, help="also write the page without the document skeleton, for publishing as an artifact")
    args = ap.parse_args()
    items, summary = build(args.seed)
    body = render_page(items, summary, args.template)
    with open(args.out, "w") as f:
        f.write(full_document(body))
    if args.artifact_body:
        with open(args.artifact_body, "w") as f:
            f.write(body)
    manifest = dict(summary, items=[{"id": it["id"], "stratum": it["stratum"], "kind": it["kind"], "source": it["source"]} for it in items])
    with open(args.manifest, "w") as f:
        json.dump(manifest, f, indent=1)
        f.write("\n")
    print(json.dumps({k: v for k, v in summary.items()}, indent=1))
    print(f"page: {args.out} ({os.path.getsize(args.out) / 1e6:.2f} MB), manifest: {args.manifest}")


if __name__ == "__main__":
    main()
