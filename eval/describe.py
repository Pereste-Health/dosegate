import collections, json, os, re, statistics, sys

from score import DATA

VOWELS = re.compile(r"[aeiouy]+")


def syllables(word):
    w = word.lower()
    n = len(VOWELS.findall(w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def fk_grade(text):
    sents = [s for s in re.split(r"[.!?:;\n]+", text) if re.search(r"[A-Za-z]", s)]
    words = re.findall(r"[A-Za-z]+(?:'[a-z]+)?|\d+(?:\.\d+)?", text)
    if not sents or not words:
        return None
    syl = sum(syllables(w) if w[0].isalpha() else 1 for w in words)
    return 0.39 * len(words) / len(sents) + 11.8 * syl / len(words) - 15.59


def cases():
    cs = [json.loads(l) for l in open(os.path.join(DATA, "cases.jsonl"))]
    drugs = collections.Counter()
    routes = collections.Counter()
    for c in cs:
        for m in c["medicationRequests"]:
            drugs[m["medicationCodeableConcept"]["text"]] += 1
            routes[m["dosageInstruction"][0]["route"]["coding"][0]["code"]] += 1
    return {"cases": len(cs), "orders": sum(drugs.values()), "names": dict(drugs.most_common()),
            "routes": dict(routes)}


def readability(tag):
    s = f"_{tag}" if tag else ""
    gens = [json.loads(l) for l in open(os.path.join(DATA, f"generations{s}.jsonl"))]
    dec = {(d["case_id"], d["condition"], d["sample"], d["attempt"]): d["gate"]
           for d in json.load(open(os.path.join(DATA, f"final_gate_decisions{s}.json")))}
    out = {}
    for cond in ("free", "free_daily", "slot", "slot_daily", "slot_hot"):
        grades = []
        for g in gens:
            if g["condition"] != cond:
                continue
            gate = dec[(g["case_id"], g["condition"], g["sample"], g["attempt"])]
            text = gate["text"] if gate["status"] == "ok" else (g["output"] if cond.startswith("free") else None)
            if text:
                k = fk_grade(text)
                if k is not None:
                    grades.append(k)
        if grades:
            out[cond] = {"n": len(grades), "median_grade": round(statistics.median(grades), 1),
                         "iqr": [round(q, 1) for q in statistics.quantiles(grades, n=4)[::2]]}
    return out


def main():
    report = {"cases": cases(), "readability": {}}
    for tag in sys.argv[1:]:
        report["readability"][tag or "v1"] = readability("" if tag == "v1" else tag)
    json.dump(report, open(os.path.join(DATA, "describe.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
