import json, glob, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ORDER_INTENTS = {"order", "original-order", "reflex-order", "filler-order", "instance-order"}
SLOT = re.compile(r"\{\{(\w+):([^}]+)\}\}")
VALUE_FIELDS = ("dose", "route", "frequency", "sig", "daily")


def load_requests():
    reqs = {}
    for f in glob.glob(os.path.join(DATA, "heldout", "*.jsonl")) + glob.glob(os.path.join(DATA, "heldout2", "*.jsonl")):
        for line in open(f):
            r = json.loads(line)
            if "request" in r:
                reqs[r["id"]] = json.loads(r["request"])
    return reqs


def entries(req):
    if "bundle" in req:
        return [e["resource"] for e in req["bundle"].get("entry", []) if e.get("resource", {}).get("resourceType") == "MedicationRequest"]
    return req.get("medicationRequests", [])


def actives(req):
    out = []
    for m in entries(req):
        if m.get("status") == "active" and m.get("intent") in ORDER_INTENTS and m.get("doNotPerform") is not True:
            out.append((m.get("id"), (m.get("subject") or {}).get("reference")))
    return out


def omitted(req):
    named = {i for f, i in SLOT.findall(req.get("output", "")) if f in VALUE_FIELDS}
    subjects = collections.Counter(s for _, s in actives(req))
    main = subjects.most_common(1)[0][0] if subjects else None
    return [i for i, s in actives(req) if s == main and i not in named]


def main():
    reqs = load_requests()
    one_ingredient = set(json.load(open(os.path.join(DATA, "heldout2", "same_ingredient_pairs.json"))))
    replay = {}
    for name in ["replay_v21/h1_results.jsonl", "replay_v21/h2_results.jsonl"]:
        for line in open(os.path.join(DATA, name)):
            r = json.loads(line)
            replay[r["id"]] = r
    for label_file, rnd in [("heldout/labels_h1.json", "h1"), ("heldout2/labels_h2.json", "h2")]:
        rows = json.load(open(os.path.join(DATA, label_file)))
        for flt in ["layer", "baseline"]:
            faithful = [r for r in rows if r["filter"] == flt and r["label"] == "faithful" and r["id"] not in one_ingredient]
            omitting = [r for r in faithful if omitted(reqs[r["id"]])]
            outcome = collections.Counter(replay.get(r["id"], {}).get("layer", {}).get("reason", "ok") for r in omitting)
            print(rnd, flt, "faithful", len(faithful), "omitting an active order", len(omitting), "version 2.1 reasons", dict(outcome))


if __name__ == "__main__":
    main()
