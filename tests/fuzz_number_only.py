#!/usr/bin/env python3
"""Differential fuzz test of the number-only mode of `dosegate serve`.

A separate Python reference predicts each reply of `dosegate serve --number-only`
for a fixed three-order chart. The reference is written from DoseGate/Render.lean,
DoseGate/Tokens.lean, and DoseGate/Template.lean, and it reads the approved word
list from data/prose_words.txt. It is not a copy of the binary's code. Random
outputs are built from approved words, unapproved words, number-like words,
numbers, value sentence shapes, slots (valid, unknown, and malformed), signs,
punctuation, and missing separators. Each reply must match the reference: the
status and the reason for a block, or the text for an ok reply.

For every ok reply, the check also requires that each digit and each number-like
word in the released text appears in a value from the chart, so no number can come
from the model's own words.

Usage: python3 tests/fuzz_number_only.py [--binary PATH] [--count N] [--seed S]
"""

import argparse
import json
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BINARY = ROOT / ".lake/build/bin/dosegate"
PROSE_FILE = ROOT / "data/prose_words.txt"

NUMBER_WORDS = set("""zero one two three four five six seven eight nine ten eleven twelve thirteen
fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty
ninety hundred thousand million half halves quarter quarters third thirds once twice thrice double
doubled triple tripled dbl dozen couple pair single both several few many much ii iii iv vi x
tenfold extra another all some any""".split())
PLAIN_QUANTIFIERS = {"all", "some", "any", "both"}
UNIT_WORDS = set("""mcgs oz ounce ounces gtt gtts mg mgs mcg ug g gm gms gram grams milligram
milligrams microgram micrograms kg ml mls milliliter milliliters millilitre millilitres l liter
liters litre litres cc u iu ius unit units meq mmol tablet tablets tab tabs pill pills capsule
capsules cap caps puff puffs spray sprays drop drops patch patches teaspoon teaspoons tsp
tablespoon tablespoons tbsp vial vials ampule ampules ampoule ampoules scoop scoops dose doses
dosage amount amounts strength strengths""".split())
DOSE_NOUNS = {"dose", "doses", "dosage"}
SCHEDULE_WORDS = set("""every each per daily nightly weekly monthly hourly times bid tid qid qd qod
qhs prn qam qpm qw q h hs ac pc morning mornings evening evenings night nights noon bedtime
breakfast lunch dinner supper meal meals hour hours minute minutes day days week weeks month months
year today tonight tomorrow again""".split())
QUANTITY_CHANGE_WORDS = set("""more less fewer increase increased decrease decreased reduce lower
lowered raise adjust max maximum min minimum most least""".split())
ROMAN_WORDS = {"ii", "iii", "iv", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xv", "xx"}
NUMBER_PREFIXES = ("four", "five", "seven", "nine", "twelve", "twenty", "thirty", "forty", "fifty",
                   "sixty", "eighty", "ninety", "hundred", "thousand", "million")
NUMBER_SUFFIXES = ("mg", "mcg", "ml")
DIGITS = set("0123456789")
ASCII_ALNUM = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
TEXT_CHARS = ASCII_ALNUM | set(" \n.,;:()'\"-/?")
SENTENCE_ENDS = set(".!?;:\n")
FIELDS = {"drug", "dose", "route", "frequency", "sig", "daily"}
VALUE_FIELDS = FIELDS - {"drug"}
ID_CHARS = ASCII_ALNUM | set("-.")
EXTRA_WORDS = ["clinic", "bananas", "twice"]


def tokens(text):
    return [t.lower() for t in re.findall(r"[A-Za-z0-9]+", text)]


def number_like(tok):
    return (any(c in DIGITS for c in tok)
            or (tok in NUMBER_WORDS and tok not in PLAIN_QUANTIFIERS)
            or (tok in UNIT_WORDS and tok not in DOSE_NOUNS)
            or tok in SCHEDULE_WORDS or tok in QUANTITY_CHANGE_WORDS
            or (len(tok) == 1 and tok not in ("a", "i"))
            or tok in ROMAN_WORDS
            or tok.startswith(NUMBER_PREFIXES)
            or tok.endswith(NUMBER_SUFFIXES))


ORDERS = {"m1": ("Metformin", 500), "m2": ("Lisinopril", 10), "m3": ("Atorvastatin", 250)}
ROUTE_TEXT = "by mouth"
FREQUENCY_TEXT = "twice a day"


def field_text(field, name, dose):
    if field == "drug":
        return name
    if field == "dose":
        return f"{dose} mg"
    if field == "route":
        return ROUTE_TEXT
    if field == "frequency":
        return FREQUENCY_TEXT
    if field == "daily":
        return f"{2 * dose} mg a day"
    if field == "sig":
        return f"{dose} mg {ROUTE_TEXT}, {FREQUENCY_TEXT}"
    return None


def parse_template(text):
    segs = []
    cur = ""
    i = 0
    while i < len(text):
        if text.startswith("{{", i):
            rest = text[i + 2:]
            close = rest.find("}")
            if close < 0 or not rest[close:].startswith("}}"):
                return None
            inside = rest[:close]
            colon = inside.find(":")
            if colon < 0:
                return None
            name, ident = inside[:colon], inside[colon + 1:]
            if name not in FIELDS or not ident or not set(ident) <= ID_CHARS:
                return None
            if cur:
                segs.append(("text", cur))
            cur = ""
            segs.append(("slot", name, ident))
            i += 2 + close + 2
        elif text[i] in "{}":
            return None
        else:
            cur += text[i]
            i += 1
    if cur:
        segs.append(("text", cur))
    return segs


def sentences(segs):
    out = [[]]
    for seg in segs:
        if seg[0] == "slot":
            out[-1].append(seg)
            continue
        parts = re.split(r"[.!?;:\n]", seg[1])
        out[-1].append(("text", parts[0]))
        for part in parts[1:]:
            out.append([("text", part)])
    return out


SHAPES = [
    [("w", "take"), ("s", "drug"), ("s", "dose"), ("s", "route"), ("s", "frequency")],
    [("w", "take"), ("s", "drug"), ("s", "sig")],
    [("w", "take"), ("s", "drug"), ("s", "dose"), ("s", "route"), ("s", "frequency"),
     ("w", "which"), ("w", "is"), ("s", "daily")],
    [("w", "take"), ("s", "drug"), ("s", "sig"), ("w", "which"), ("w", "is"), ("s", "daily")],
    [("w", "take"), ("s", "drug"), ("s", "dose")],
    [("w", "take"), ("s", "drug"), ("s", "route")],
    [("w", "take"), ("s", "drug"), ("s", "frequency")],
    [("w", "your"), ("w", "dose"), ("w", "of"), ("s", "drug"), ("w", "is"), ("s", "dose")],
    [("w", "your"), ("w", "total"), ("w", "of"), ("s", "drug"), ("w", "is"), ("s", "daily")],
]


def items_of(sentence):
    items = []
    for seg in sentence:
        if seg[0] == "text":
            items += [("w", t) for t in tokens(seg[1])]
        else:
            items.append(("s", seg[1]))
    return items


def sentence_ok(sentence, prose, extra):
    slots = [seg for seg in sentence if seg[0] == "slot"]
    ids = {seg[2] for seg in slots}
    if len(ids) > 1:
        return False
    if any(seg[1] in VALUE_FIELDS for seg in slots):
        return items_of(sentence) in SHAPES
    if slots:
        return False
    return all(not number_like(w) and (w in prose or w in extra)
               for seg in sentence for w in tokens(seg[1]))


def no_repeated_value(segs):
    values = [(seg[1], seg[2]) for seg in segs if seg[0] == "slot" and seg[1] in VALUE_FIELDS]
    if len(values) != len(set(values)):
        return False
    for field, ident in values:
        if field == "sig":
            for other_field, other_id in values:
                if other_id == ident and other_field in ("dose", "route", "frequency"):
                    return False
    return True


def ends_sign(text):
    run = []
    for c in reversed(text):
        if c in ASCII_ALNUM:
            break
        run.append(c)
    return any(c in "-+/" for c in run)


def has_sign_before_slot(segs):
    return any(segs[i][0] == "text" and segs[i + 1][0] == "slot" and ends_sign(segs[i][1])
               for i in range(len(segs) - 1))


def separated(a, b):
    return (a[-1] not in ASCII_ALNUM) or (b[0] not in ASCII_ALNUM)


def all_separated(pieces):
    kept = [p for p in pieces if p]
    return all(separated(a, b) for a, b in zip(kept, kept[1:]))


def reference(chart, out, prose, extra):
    segs = parse_template(out)
    if segs is None:
        return ("blocked", "malformed")
    if not all(sentence_ok(g, prose, extra) for g in sentences(segs)):
        return ("blocked", "unbound")
    if not no_repeated_value(segs):
        return ("blocked", "repeatedValue")
    if has_sign_before_slot(segs):
        return ("blocked", "signBeforeSlot")
    pieces = []
    for seg in segs:
        if seg[0] == "text":
            if not all(c in TEXT_CHARS for c in seg[1]):
                return ("blocked", "disallowedCharacter")
            pieces.append(seg[1])
            continue
        order = next((o for o in chart if o["id"] == seg[2]), None)
        if order is None:
            return ("blocked", "unknownRef")
        if not order["active"]:
            return ("blocked", "inactiveOrder")
        piece = field_text(seg[1], order["name"], order["dose"])
        if piece is None:
            return ("blocked", "missingField")
        pieces.append(piece)
    if not all_separated(pieces):
        return ("blocked", "unseparated")
    return ("ok", "".join(pieces))


def chart_json(chart):
    orders = []
    for o in chart:
        orders.append({
            "resourceType": "MedicationRequest", "id": o["id"],
            "status": "active" if o["active"] else "stopped", "intent": "order",
            "medicationCodeableConcept": {"text": o["name"]},
            "subject": {"reference": "Patient/pat1"},
            "dosageInstruction": [{
                "timing": {"repeat": {"frequency": 2, "period": 1, "periodUnit": "d"}},
                "route": {"coding": [{"system": "http://snomed.info/sct", "code": "26643006",
                                      "display": "Oral route"}]},
                "doseAndRate": [{"doseQuantity": {"value": o["dose"], "unit": "mg",
                                                  "system": "http://unitsofmeasure.org", "code": "mg"}}],
            }],
        })
    return orders


def full_chart(active=None):
    active = active or {}
    return [{"id": i, "name": name, "dose": dose, "active": active.get(i, True)}
            for i, (name, dose) in ORDERS.items()]


SHAPE_PHRASES = ["Take", "Your total of", "which is", "your dose of", "is", "of", "take", "Your"]
BAD_WORDS = ["metformin", "twofold", "sixth", "tome", "dos", "bd", "twice", "pills", "eyesight",
             "same", "other", "more", "day", "mg", "one", "two", "x", "iii", "d", "t", "daily",
             "dose", "lisinopril", "bananas", "a", "i", "no", "yes"]
MALFORMED = ["{{drug:m1", "{drug:m1}", "}}", "{{x:m1}}", "{{drug:}}", "{{drug:m1}}}", "{{dose:m1}}}}"]
SEPARATORS = [" "] * 14 + ["", "", ". ", ", ", "-", "+", "/", "\n", "; ", "(", "?"]


def random_part(rng, prose):
    r = rng.random()
    if r < 0.45:
        return rng.choice(prose)
    if r < 0.55:
        return rng.choice(BAD_WORDS)
    if r < 0.62:
        return str(rng.randint(1, 9999))
    if r < 0.80:
        return "{{%s:%s}}" % (rng.choice(sorted(FIELDS)), rng.choice(["m1", "m2", "m3", "m1", "m2", "m3", "m4"]))
    if r < 0.85:
        return rng.choice(SHAPE_PHRASES)
    if r < 0.91:
        return rng.choice(MALFORMED)
    return rng.choice(["911", "0.5", "1,000", "#", "%", "!", "?", "--"])


def messy_output(rng, prose):
    parts = [random_part(rng, prose) for _ in range(rng.randint(1, 9))]
    out = parts[0]
    for part in parts[1:]:
        out += rng.choice(SEPARATORS) + part
    if rng.random() < 0.6:
        out += "."
    return out


def clean_sentence(rng, prose):
    ident = rng.choice(["m1", "m2", "m3"])
    r = rng.random()
    if r < 0.12:
        return "Take {{drug:%s}} {{dose:%s}}." % (ident, ident)
    if r < 0.22:
        return "Take {{drug:%s}} {{route:%s}}." % (ident, ident)
    if r < 0.30:
        return "Take {{drug:%s}} {{frequency:%s}}." % (ident, ident)
    if r < 0.38:
        return "Take {{drug:%s}} {{dose:%s}} {{route:%s}} {{frequency:%s}}." % ((ident,) * 4)
    if r < 0.46:
        return "Your dose of {{drug:%s}} is {{dose:%s}}." % (ident, ident)
    if r < 0.54:
        return "Your total of {{drug:%s}} is {{daily:%s}}." % (ident, ident)
    if r < 0.60:
        return "Take {{drug:%s}} {{dose:%s}} {{route:%s}} {{frequency:%s}} which is {{daily:%s}}." % ((ident,) * 5)
    if r < 0.66:
        return "Take {{drug:%s}} {{sig:%s}}." % (ident, ident)
    if r < 0.70:
        return "Take {{drug:%s}} {{dose:%s}} {{dose:%s}}." % (ident, ident, ident)
    words = [rng.choice(prose) for _ in range(rng.randint(1, 7))]
    return " ".join(words).capitalize() + rng.choice([".", ".", "!", "?", ""])


def clean_output(rng, prose):
    return " ".join(clean_sentence(rng, prose) for _ in range(rng.randint(1, 3)))


def mutated_output(rng, prose):
    out = clean_output(rng, prose)
    r = rng.random()
    if r < 0.2:
        return out.replace("m1", "m4", 1) if "m1" in out else out + " Take {{drug:m4}} {{dose:m4}}."
    if r < 0.4:
        return out.replace("{{", "-{{", 1) if "{{" in out else out + "-{{dose:m1}}"
    if r < 0.5:
        return out.replace("}} {{", "}}{{", 1) if "}} {{" in out else out.replace("}}", "}}abc", 1)
    if r < 0.6:
        return out.replace("}}", "}}abc", 1) if "}}" in out else out + "{{drug:m1}}x"
    if r < 0.75:
        return out.replace(".", "#", 1) if "." in out else out + "%"
    return out.replace("{{", "{{", 1) + " Take {{drug:%s}} {{dose:%s}}." % (rng.choice(["m2", "m3"]), rng.choice(["m1", "m2"]))


def random_chart(rng):
    return full_chart({i: rng.random() < 0.85 for i in ORDERS})


def probe(binary, extra_path):
    requests = []
    expected = []
    for i, (name, dose) in ORDERS.items():
        requests.append({"medicationRequests": chart_json(full_chart()),
                         "output": "Take {{drug:%s}} {{dose:%s}} {{route:%s}} {{frequency:%s}}." % ((i,) * 4)})
        expected.append(f"Take {name} {dose} mg {ROUTE_TEXT} {FREQUENCY_TEXT}.")
        requests.append({"medicationRequests": chart_json(full_chart()),
                         "output": "Your total of {{drug:%s}} is {{daily:%s}}." % (i, i)})
        expected.append(f"Your total of {name} is {2 * dose} mg a day.")
    replies = run_serve(binary, requests, extra_path)
    for reply, text in zip(replies, expected):
        if reply.get("status") != "ok" or reply.get("text") != text:
            print(f"probe mismatch: expected {text!r}, got {reply}")
            sys.exit(1)


def run_serve(binary, requests, extra_path):
    lines = "".join(json.dumps(r) + "\n" for r in requests)
    result = subprocess.run([str(binary), "serve", "--number-only", "--extra-words", str(extra_path)],
                            input=lines, capture_output=True, text=True)
    replies = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(replies) != len(requests):
        print(f"expected {len(requests)} replies, got {len(replies)}")
        print(result.stderr[-2000:])
        sys.exit(1)
    return replies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", default=str(DEFAULT_BINARY))
    parser.add_argument("--count", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    prose = set(line for line in PROSE_FILE.read_text().split("\n") if line)
    rng = random.Random(args.seed)
    prose_list = sorted(prose)

    with tempfile.TemporaryDirectory(prefix="fuzz-number-only-") as tmp:
        extra_path = Path(tmp) / "extra.words"
        extra_path.write_text("".join(w + "\n" for w in EXTRA_WORDS))
        extra = set(EXTRA_WORDS)
        probe(args.binary, extra_path)

        cases = []
        for _ in range(args.count):
            chart = random_chart(rng)
            kind = rng.random()
            if kind < 0.3:
                out = clean_output(rng, prose_list)
            elif kind < 0.5:
                out = mutated_output(rng, prose_list)
            else:
                out = messy_output(rng, prose_list)
            cases.append((chart, out))

        requests = [{"medicationRequests": chart_json(chart), "output": out} for chart, out in cases]
        replies = run_serve(args.binary, requests, extra_path)

    failures = []
    outcomes = {}
    for (chart, out), reply in zip(cases, replies):
        expected = reference(chart, out, prose, extra)
        if expected[0] == "ok":
            outcomes["ok"] = outcomes.get("ok", 0) + 1
        else:
            outcomes["blocked: " + expected[1]] = outcomes.get("blocked: " + expected[1], 0) + 1
        status = reply.get("status")
        if status == "ok":
            actual = ("ok", reply.get("text"))
        elif status == "blocked":
            actual = ("blocked", reply.get("reason"))
        else:
            actual = ("error", reply)
        if actual[0] != expected[0] or actual[1] != expected[1]:
            failures.append((out, expected, actual))
            continue
        if status == "ok":
            values = set()
            for o in chart:
                for field in ("drug", "dose", "route", "frequency", "sig", "daily"):
                    piece = field_text(field, o["name"], o["dose"])
                    values.update(tokens(piece))
            for tok in tokens(reply["text"]):
                if (any(c in DIGITS for c in tok) or number_like(tok)) and tok not in values:
                    failures.append((out, ("number", tok), ("released", reply["text"])))
                    break

    print(f"cases: {args.count}, seed: {args.seed}")
    for name in sorted(outcomes):
        print(f"  {name}: {outcomes[name]}")
    print(f"mismatches: {len(failures)}")
    for out, expected, actual in failures[:10]:
        print(f"  output: {out!r}")
        print(f"    reference: {expected}")
        print(f"    binary:    {actual}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
