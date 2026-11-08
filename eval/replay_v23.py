import collections, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
REPLAY = os.path.join(DATA, "replay_v23")
sys.path.insert(0, os.path.join(ROOT, "tests"))
import fuzz_reader as fz  # noqa: E402

CORPORA = ["development", "h1", "h2", "h3", "h4"]
LABEL_FILES = ["attack_labels.json", "heldout/labels_h1.json", "heldout2/labels_h2.json", "heldout3/labels_h3.json",
               "heldout4/labels_h4.json", "replay_v21/labels.json", "replay_v22/labels.json"]
PRIOR_RESULTS = {c: ["replay_v22/%s_results.jsonl" % c] for c in ["development", "h1", "h2", "h3"]}
PRIOR_RESULTS["h4"] = sorted(glob.glob(os.path.join(DATA, "heldout4", "*_results.jsonl")))
RAW_NUMBER = re.compile(r'"\\u0000NUM(.*?)\\u0000NUM"')
ROLE_WORDS = {"doctor", "doctors", "nurse", "nurses", "pharmacist", "pharmacists"}
CFG = fz.CORES["v2"]


def rows(path):
    return [json.loads(l) for l in open(path) if l.strip()]


def load_labels():
    labels = {}
    for rel in LABEL_FILES:
        for r in json.load(open(os.path.join(DATA, rel))):
            if r.get("text") is None:
                continue
            labels[(r["id"], r["text"])] = r
    return labels


def orders_of(req):
    bundle = req.get("bundle")
    if isinstance(bundle, dict):
        entries = bundle.get("entry") if isinstance(bundle.get("entry"), list) else []
        return [e["resource"] for e in entries if isinstance(e, dict) and isinstance(e.get("resource"), dict)
                and e["resource"].get("resourceType") == "MedicationRequest"]
    mrs = req.get("medicationRequests")
    return [m for m in mrs if isinstance(m, dict)] if isinstance(mrs, list) else []


def opaque(value):
    return isinstance(value, str) and fz.opaque_id_ok(value)


def id_reasons(req):
    reasons = []
    bundle = req.get("bundle")
    if isinstance(bundle, dict):
        if bundle.get("id") is not None and not opaque(bundle.get("id")):
            reasons.append("bundle id outside the opaque identifier grammar: %r" % (bundle.get("id"),))
        meta = bundle.get("meta")
        if isinstance(meta, dict) and meta.get("versionId") is not None and not opaque(meta.get("versionId")):
            reasons.append("bundle meta versionId outside the opaque identifier grammar: %r" % (meta.get("versionId"),))
        for e in bundle.get("entry") if isinstance(bundle.get("entry"), list) else []:
            if not isinstance(e, dict):
                continue
            r = e.get("resource") if isinstance(e.get("resource"), dict) else {}
            t = r.get("resourceType")
            if t in ("Patient", "Medication"):
                if r.get("id") is not None and not opaque(r.get("id")):
                    reasons.append("%s id outside the opaque identifier grammar: %r" % (t, r.get("id")))
                meta = r.get("meta")
                if isinstance(meta, dict) and meta.get("versionId") is not None and not opaque(meta.get("versionId")):
                    reasons.append("%s meta versionId outside the opaque identifier grammar: %r" % (t, meta.get("versionId")))
            full = e.get("fullUrl")
            if isinstance(full, str) and fz.full_url_ok(full) and not fz.full_url_consistent(e):
                if full.startswith("urn:uuid:"):
                    reasons.append("entry fullUrl id outside the opaque identifier grammar: %r" % (full,))
                else:
                    reasons.append("entry fullUrl does not end with its resource's type and id: %r" % (full,))
    for o in orders_of(req):
        oid = o.get("id")
        if oid is not None and not opaque(oid):
            reasons.append("MedicationRequest id outside the opaque identifier grammar: %r" % (oid,))
        if not fz.version_id_ok(o):
            reasons.append("%s: meta versionId outside the opaque identifier grammar: %r" % (oid, o.get("meta", {}).get("versionId")))
        for k in fz.CHECKED_REFERENCE_KEYS:
            v = o.get(k)
            ref = v.get("reference") if isinstance(v, dict) else None
            rid = fz.reference_id_of(ref) if isinstance(ref, str) else None
            if rid is not None and not fz.opaque_id_ok(rid):
                reasons.append("%s: %s reference id outside the opaque identifier grammar: %r" % (oid, k, ref))
        for k in fz.REFERENCE_LIST_KEYS:
            v = o.get(k)
            for item in v if isinstance(v, list) else []:
                ref = item.get("reference") if isinstance(item, dict) else None
                rid = fz.reference_id_of(ref) if isinstance(ref, str) else None
                if rid is not None and not fz.opaque_id_ok(rid):
                    reasons.append("%s: %s reference id outside the opaque identifier grammar: %r" % (oid, k, ref))
        ref = fz.subject_ref(o)
        sid = fz.subject_id_of(ref) if isinstance(ref, str) else None
        if sid is not None and not fz.opaque_id_ok(sid):
            reasons.append("%s: subject id outside the opaque identifier grammar: %r" % (oid, ref))
    patient = req.get("patient")
    if isinstance(patient, str) and patient != "" and not fz.opaque_id_ok(patient):
        reasons.append("patient field outside the opaque identifier grammar: %r" % (patient,))
    return reasons


def medication_reasons(req):
    reasons = []
    if not isinstance(req.get("bundle"), dict):
        return reasons
    orders = orders_of(req)
    meds = fz.medication_entries(req)
    refs = []
    for o in orders:
        v = o.get("medicationReference")
        if isinstance(v, dict) and isinstance(v.get("reference"), str):
            refs.append((o.get("id"), v["reference"]))
    for oid, ref in refs:
        n = sum(1 for m in meds if fz.medication_matches(ref, m))
        if n > 1:
            reasons.append("%s: medicationReference %s matches %d Medication resources" % (oid, ref, n))
    for m in meds:
        if not any(fz.medication_matches(ref, m) for _, ref in refs):
            reasons.append("a Medication resource with id %r that no MedicationRequest references" % (m[1].get("id"),))
    return reasons


def role_word_reasons(req):
    out = req.get("output")
    if not isinstance(out, str):
        return []
    words = set(fz.tokens(re.sub(r"\{\{[^}]*\}\}", " ", out)))
    hit = sorted(words & ROLE_WORDS)
    return ["output uses a word removed from the vocabulary: %s" % ", ".join(hit)] if hit else []


def concept_reason(order, meds):
    cc, ref = order.get("medicationCodeableConcept"), order.get("medicationReference")
    if cc is not None and ref is not None:
        return "medicationReference beside medicationCodeableConcept"
    if cc is None and ref is not None:
        return "medicationReference not resolved to a Medication resource"
    text = cc.get("text") if isinstance(cc, dict) else None
    displays = fz.displays_of(cc) if isinstance(cc, dict) else []
    bad = [d for d in displays if text is None or not fz.display_matches(text, d)]
    if bad:
        return "coding display outside the name-plus-strength grammar: " + repr(bad[0])
    if isinstance(cc, dict) and not all(fz.med_coding_ok(c) for c in cc.get("coding", [])):
        return "medication coding with an unknown system, a code of the wrong shape, or an extra key"
    return "medication concept with an extra key"


def explain(req):
    reasons = []
    bundle = req.get("bundle")
    if isinstance(bundle, dict):
        for e in bundle.get("entry") if isinstance(bundle.get("entry"), list) else []:
            r = e.get("resource") if isinstance(e, dict) else None
            t = r.get("resourceType") if isinstance(r, dict) else None
            if t == "Bundle":
                reasons.append("a bundle entry is itself a Bundle")
            elif t in fz.EVENT_RESOURCE_TYPES:
                reasons.append("a %s resource in the bundle" % t)
            elif isinstance(t, str) and t not in fz.ALLOWED_RESOURCE_TYPES:
                reasons.append("a %s resource in the bundle (only Patient, MedicationRequest, and Medication are accepted)" % t)
    reasons += id_reasons(req)
    reasons += medication_reasons(req)
    reasons += role_word_reasons(req)
    orders = orders_of(req)
    refs = [fz.subject_ref(o) for o in orders]
    if any(r is not None and (r.startswith("http://") or r.startswith("https://")) for r in refs):
        reasons.append("a subject.reference that is an absolute URL")
    elif any(r is not None and fz.subject_id_of(r) is None for r in refs):
        reasons.append("a subject.reference that is not Patient/id or urn:uuid:id")
    elif len({r for r in refs if r is not None}) > 1:
        reasons.append("subjects that are not all the same string")
    patient = req.get("patient")
    if isinstance(patient, str) and refs and refs[0] is not None and fz.patient_id_of(refs[0], CFG) not in (None, patient):
        reasons.append("subject is not the patient named by the patient field")
    meds = fz.medication_entries(req)
    for o in orders:
        if not fz.is_active(o, patient if isinstance(patient, str) else None, CFG):
            continue
        oid = o.get("id")
        name, ok = fz.medication_named(meds, o)
        if not ok:
            reasons.append("%s: %s" % (oid, concept_reason(o, meds)))
        elif name == "":
            cc = fz.order_concept(meds, o)
            text = cc.get("text") if isinstance(cc, dict) else None
            shown = text if isinstance(text, str) else (fz.displays_of(cc) or [""])[0]
            reasons.append("%s: name not in the lexicon: %r" % (oid, shown.strip()))
        if fz.closed_fields(o):
            for key in ("statusReason", "identifier", "groupIdentifier", "instantiatesUri", "instantiatesCanonical",
                        "implicitRules"):
                if fz.present(o, key):
                    reasons.append("%s: %s present" % (oid, key))
            checks = [("reasonCode", fz.list_of(lambda cc: fz.coded_concept_ok(fz.REASON_SYSTEMS, cc))),
                      ("category", fz.list_of(lambda cc: fz.coded_concept_ok((fz.CATEGORY_SYSTEM,), cc))),
                      ("performerType", lambda cc: fz.coded_concept_ok((fz.SNOMED,), cc)),
                      ("priority", fz.str_ok(lambda v: v in fz.PRIORITY_CODES)), ("language", fz.str_ok(fz.language_ok)),
                      ("authoredOn", fz.str_ok(fz.date_time_ok)), ("meta", fz.meta_ok),
                      ("dispenseRequest", fz.dispense_ok), ("substitution", fz.substitution_ok)]
            checks += [(k, fz.ref_obj_ok) for k in fz.REFERENCE_KEYS]
            checks += [(k, fz.list_of(fz.ref_obj_ok)) for k in fz.REFERENCE_LIST_KEYS]
            for key, check in checks:
                if not fz.field_ok(o, key, check):
                    reasons.append("%s: %s carries text or a form the reader does not interpret" % (oid, key))
        if not fz.course_of_therapy_ok(o, CFG) and o.get("courseOfTherapyType") is not None:
            reasons.append("%s: courseOfTherapyType not a coded continuous course" % oid)
        dosages = o.get("dosageInstruction")
        if isinstance(dosages, list) and len(dosages) == 1 and isinstance(dosages[0], dict):
            route = dosages[0].get("route")
            if route is not None and not fz.route_codings_known(route):
                reasons.append("%s: route coding not a known SNOMED CT route" % oid)
    return reasons


def main():
    labels = load_labels()
    carried = []
    table = {}
    detail = {}
    for corpus in CORPORA:
        requests = {r["id"]: r for r in rows(os.path.join(REPLAY, corpus + ".jsonl"))}
        results = {r["id"]: r for r in rows(os.path.join(REPLAY, corpus + "_results.jsonl"))}
        prior = {}
        for rel in PRIOR_RESULTS[corpus]:
            path = rel if os.path.isabs(rel) else os.path.join(DATA, rel)
            for r in rows(path):
                prior[r["id"]] = r
        counts = collections.Counter()
        released = [i for i in requests if results[i]["layer"]["status"] == "ok"]
        unlabeled = []
        for i in released:
            text = results[i]["layer"]["text"]
            rec = labels.get((i, text))
            if rec is None:
                counts["released_without_label"] += 1
                unlabeled.append({"id": i, "text": text})
                continue
            counts[rec["label"]] += 1
            carried.append({"id": i, "filter": "layer", "reader1": rec.get("reader1"), "reader2": rec.get("reader2"),
                            "third_reader": rec.get("third_reader"), "label": rec["label"], "corpus": corpus,
                            "text": text})
        prior_faithful = []
        for i in requests:
            p = prior.get(i, {}).get("layer", {})
            if p.get("status") == "ok":
                rec = labels.get((i, p.get("text")))
                if rec is not None and rec["label"] == "faithful":
                    prior_faithful.append(i)
        still = [i for i in prior_faithful if results[i]["layer"]["status"] == "ok"]
        same_text = [i for i in still if results[i]["layer"]["text"] == prior[i]["layer"]["text"]]
        lost = [i for i in prior_faithful if results[i]["layer"]["status"] != "ok"]
        table[corpus] = {"requests": len(requests), "released": len(released),
                         "misstates_order": counts["misstates_order"], "unsupported_claim": counts["unsupported_claim"],
                         "faithful": counts["faithful"], "released_without_label": counts["released_without_label"],
                         "released_without_label_ids": unlabeled,
                         "errors": sum(results[i]["layer"]["status"] == "error" for i in requests),
                         "blocked": sum(results[i]["layer"]["status"] == "blocked" for i in requests),
                         "block_reasons": dict(collections.Counter(results[i]["layer"].get("reason") for i in requests
                                                                   if results[i]["layer"]["status"] == "blocked")),
                         "prior_faithful_releases": len(prior_faithful), "prior_faithful_still_released": len(still),
                         "prior_faithful_same_text": len(same_text), "prior_faithful_now_blocked_or_error": len(lost)}
        detail[corpus] = []
        for i in lost:
            req = fz.parse_request(RAW_NUMBER.sub(lambda m: m.group(1), requests[i]["request"]))
            res = results[i]["layer"]
            detail[corpus].append({"id": i, "class": requests[i].get("class"), "text": prior[i]["layer"]["text"],
                                   "v23": res["status"] + ": " + str(res.get("reason") or res.get("message")),
                                   "why": explain(req)})
    json.dump(carried, open(os.path.join(REPLAY, "labels.json"), "w"), indent=1)
    json.dump({"table": table, "previously_faithful_now_blocked": detail},
              open(os.path.join(REPLAY, "summary.json"), "w"), indent=1)
    for corpus, t in table.items():
        print(corpus, "requests", t["requests"], "released", t["released"], "misstates", t["misstates_order"],
              "unsupported", t["unsupported_claim"], "faithful", t["faithful"], "unlabeled", t["released_without_label"],
              "errors", t["errors"], "| prior faithful", t["prior_faithful_releases"], "still released",
              t["prior_faithful_still_released"], "same text", t["prior_faithful_same_text"],
              "now blocked", t["prior_faithful_now_blocked_or_error"])
    for corpus, items in detail.items():
        print(f"\n== {corpus}: previously faithful, now blocked or refused ({len(items)}) ==")
        for d in items:
            print(f"- {d['id']} | {d['v23']} | {d['text'][:90]!r}")
            for w in d["why"] or ["(no rule of version 2.3 found by the explainer)"]:
                print("    " + w)


if __name__ == "__main__":
    main()
