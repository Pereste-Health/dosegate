import collections, json, os, re, subprocess

from score import DATA, MASS, audit_text, orders, to_mg

HERE = os.path.dirname(os.path.abspath(__file__))
SLOT = re.compile(r"\{\{(\w+):([^}]*)\}\}")


def word_lists():
    src = open(os.path.join(HERE, "..", "DoseGate", "Tokens.lean")).read()
    def lst(name):
        body = re.search(r"def " + name + r" : List String :=\s*\[(.*?)\]", src, re.S).group(1)
        return set(re.findall(r'"([^"]*)"', body))
    return {n: lst(n) for n in ["numberWords", "unitWords", "routeWords", "frequencyWords", "negationWords"]}


WORDS = word_lists()
UNITS = {"h": "hour", "d": "day", "wk": "week", "mo": "month"}
TIMES = {1: "once", 2: "twice", 3: "three times", 4: "four times"}


def fmt_num(x):
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return s


def fmt_timing(f, p, u):
    t = TIMES.get(f, f"{f} times")
    if p == 1:
        return "every hour" if (f, u) == (1, "h") else f"{t} a {UNITS[u]}"
    return f"every {p} {UNITS[u]}s" if f == 1 else f"{t} every {p} {UNITS[u]}s"


def baseline_texts(cases, gens):
    reqs = []
    for g in gens:
        mrs = [dict(m, subject={"reference": "Patient/p1"}) for m in cases[g["case_id"]]["medicationRequests"]]
        reqs.append(json.dumps({"medicationRequests": mrs, "output": g["output"]}))
    p = subprocess.run([os.path.join(HERE, "..", ".lake/build/bin/dosegate-baseline")],
                       input="\n".join(reqs) + "\n", capture_output=True, text=True)
    res = [json.loads(l) for l in p.stdout.splitlines()]
    return [r["text"] if r["status"] == "ok" else None for r in res]


def model_word_classes(output):
    toks = {t.lower() for t in re.findall(r"[A-Za-z0-9]+", SLOT.sub(" ", output))}
    found = {}
    for name in ["numberWords", "routeWords", "frequencyWords", "negationWords"]:
        hit = sorted(toks & WORDS[name])
        if hit:
            found[name] = hit
    return found


def mutate(text, ords, kind):
    o = ords[0]
    if kind == "dose_x10":
        old, new = f"{fmt_num(o['mg'])} mg", f"{fmt_num(o['mg'] * 10)} mg"
    elif kind == "daily_as_dose":
        if o["daily_mg"] is None or o["daily_mg"] == o["mg"]:
            return None
        old, new = f"{fmt_num(o['daily_mg'])} mg a day", f"{fmt_num(o['mg'])} mg a day"
    else:
        swap = {"once a day": "twice a day", "twice a day": "once a day", "three times a day": "once a day",
                "every 8 hours": "every 12 hours", "every 12 hours": "every 8 hours", "once a week": "once a day",
                "four times a day": "twice a day"}
        old = fmt_timing(*o["timing"])
        if old not in swap:
            return None
        new = swap[old]
    if old not in text:
        return None
    return text.replace(old, new, 1)


def main():
    tag = os.environ.get("TAG", "")
    suffix = f"_{tag}" if tag else ""
    cases = {json.loads(l)["case_id"]: json.loads(l) for l in open(os.path.join(DATA, "cases.jsonl"))}
    gens = [json.loads(l) for l in open(os.path.join(DATA, f"generations{suffix}.jsonl"))]
    final = {(d["case_id"], d["condition"], d["sample"], d["attempt"]): d["gate"]
             for d in json.load(open(os.path.join(DATA, f"final_gate_decisions{suffix}.json")))}
    last = {}
    for g in gens:
        k = (g["case_id"], g["condition"], g["sample"])
        if k not in last or g["attempt"] > last[k]["attempt"]:
            last[k] = g
    report = {}

    released = []
    for g in last.values():
        if g["condition"] in ("slot", "slot_daily", "slot_hot"):
            gate = final[(g["case_id"], g["condition"], g["sample"], g["attempt"])]
            if gate["status"] == "ok":
                released.append((g, gate["text"]))
    named = sum(len({i for _, i in SLOT.findall(g["output"])}) for g, _ in released)
    report["released"] = {"outputs": len(released), "orders_named": named}

    base = collections.Counter()
    base_only = []
    base_errors = []
    finals = list(last.values())
    for g, text in zip(finals, baseline_texts(cases, finals)):
        case = cases[g["case_id"]]
        layer_ok = final[(g["case_id"], g["condition"], g["sample"], g["attempt"])]["status"] == "ok"
        base[(g["condition"], "baseline_released" if text else "baseline_blocked", "layer_released" if layer_ok else "layer_blocked")] += 1
        if text is None:
            continue
        a = audit_text(text, orders(case))
        if a["unsupported"] or a["dose_wrong"] or a["freq_wrong"]:
            base_errors.append({"case_id": g["case_id"], "condition": g["condition"], "sample": g["sample"], "audit": a, "text": text})
        if not layer_ok:
            base_only.append({"case_id": g["case_id"], "condition": g["condition"], "sample": g["sample"],
                              "model_words": model_word_classes(g["output"]),
                              "layer_reason": final[(g["case_id"], g["condition"], g["sample"], g["attempt"])].get("reason"),
                              "text": text})
    report["baseline"] = {"|".join(k): v for k, v in sorted(base.items())}
    report["baseline_only_released"] = len(base_only)
    report["baseline_only_with_model_quantity_words"] = sum(bool(b["model_words"]) for b in base_only)
    cls = collections.Counter(w for b in base_only for ws in b["model_words"].values() for w in ws)
    report["baseline_only_word_counts"] = dict(cls.most_common())
    report["baseline_released_with_audit_error"] = len(base_errors)
    json.dump(base_only, open(os.path.join(DATA, f"baseline_only_released{suffix}.json"), "w"), indent=1)

    mut = {}
    for kind in ("dose_x10", "daily_as_dose", "frequency_swap"):
        tried = caught = 0
        for g, text in released:
            ords = orders(cases[g["case_id"]])
            m = mutate(text, ords, kind)
            if m is None:
                continue
            tried += 1
            a = audit_text(m, ords)
            caught += bool(a["unsupported"] or a["dose_wrong"] or a["freq_wrong"])
        mut[kind] = {"mutated": tried, "flagged": caught}
    report["mutation"] = mut

    attack = [g for g in gens if g["condition"] == "attack"]
    doubled = 0
    twice_daily_first = 0
    doubled_equals_daily = 0
    for g in attack:
        ords = orders(cases[g["case_id"]])
        first = ords[0]
        says = any(abs(to_mg(n, u) - 2 * first["mg"]) < 1e-9 for n, u in MASS.findall(g["output"]))
        doubled += says
        if first["daily_mg"] is not None and abs(first["daily_mg"] - 2 * first["mg"]) < 1e-9:
            twice_daily_first += 1
            doubled_equals_daily += says
    report["attack"] = {"outputs": len(attack), "state_doubled_first_dose_mg": doubled,
                        "cases_first_order_twice_daily": twice_daily_first,
                        "of_those_state_doubled": doubled_equals_daily}
    json.dump(report, open(os.path.join(DATA, f"controls{suffix}.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
