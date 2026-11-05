#!/usr/bin/env python3
"""Differential fuzz test of the DoseGate reader and render checks.

An independent Python reference predicts each reply of `dosegate serve`. The
reference is written from the specification and FHIR R4, not from Lean. Realistic
orders and output templates are mutated, sent as one JSON request per line through
a single serve process, and each reply is compared with the prediction: the status,
and the reason for a block or the text for an ok. An error reply must be an error.

--core v2 (default) judges the binary against version 2 of the layer.
--core v1 judges it against the layer before version 2.
--pre-merge accepts a disagreement when the reply matches the version 1 prediction
exactly: the binary still has the version 1 core, and the difference comes from a
version 2 core change. Without it, every disagreement fails the run.

Usage: python3 tests/fuzz_reader.py [--binary PATH] [--count N] [--seed S]
           [--core v1|v2] [--pre-merge] [--examples K]
"""

import argparse
import json
import random
import re
import string
import subprocess
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BINARY = ROOT / ".lake/build/bin/dosegate"
CASES = ROOT / "eval/data/cases.jsonl"
BUNDLE = ROOT / "tests/bundle.json"

MAX_REQUEST_BYTES = 2_000_000
MAX_LITERAL = 1000
MAX_EXPONENT_DIGITS = 2
MAX_NUMBERS = 20000
MAX_DEPTH = 64
MAX_COUNT = 1000
MAX_ORDERS = 5000
MAX_OUTPUT = 65536
MAX_SLOTS = 400
MAX_SCALE = 9
MAX_NAME_LENGTH = 60
MAX_NAME_WORDS = 5
RESERVED_KEYS = ("allow", "extraWords")
ORDER_INTENTS = ("order", "original-order", "reflex-order", "filler-order", "instance-order")
PERIOD_UNITS = ("h", "d", "wk", "mo")
SNOMED = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
ROUTE_TERMS = [
    ("26643006", "Oral route"), ("26643006", "Oral use"), ("37839007", "Sublingual route"),
    ("34206005", "Subcutaneous route"), ("78421000", "Intramuscular route"),
    ("47625008", "Intravenous route"), ("447694001", "Inhalation route"), ("6064005", "Topical route"),
    ("45890007", "Transdermal route"), ("37161004", "Rectal route"), ("54485002", "Ophthalmic route"),
    ("10547007", "Otic route"), ("46713006", "Nasal route"),
]
ROUTE_PHRASE = {
    "26643006": "by mouth", "37839007": "under the tongue", "34206005": "as a shot under the skin",
    "78421000": "as a shot into a muscle", "47625008": "into a vein", "447694001": "breathed in",
    "6064005": "on the skin", "45890007": "as a skin patch", "37161004": "in the rectum",
    "54485002": "in the eye", "10547007": "in the ear", "46713006": "in the nose",
}
UNIT_NAMES = {
    "mcg": ("mcg", "mcg"), "mg": ("mg", "mg"), "g": ("g", "g"), "mL": ("mL", "mL"), "L": ("L", "L"),
    "unit": ("unit", "units"), "tablet": ("tablet", "tablets"), "capsule": ("capsule", "capsules"),
    "puff": ("puff", "puffs"), "drop": ("drop", "drops"),
}
UNIT_ABBREVIATIONS = {
    "mcg": ["ug"], "unit": ["u", "iu"], "tablet": ["tab", "tabs"], "capsule": ["cap", "caps"],
    "drop": ["gtt", "gtts"],
}
UNIT_OF_CODE = {
    "ug": "mcg", "mcg": "mcg", "mg": "mg", "g": "g", "mL": "mL", "ml": "mL", "L": "L", "l": "L",
    "U": "unit", "[iU]": "unit", "[IU]": "unit", "unit": "unit", "units": "unit",
    "{tbl}": "tablet", "TAB": "tablet", "tablet": "tablet", "tablets": "tablet",
    "{cap}": "capsule", "{capsule}": "capsule", "CAP": "capsule", "capsule": "capsule", "capsules": "capsule",
    "{puff}": "puff", "puff": "puff", "puffs": "puff",
    "[drp]": "drop", "{drop}": "drop", "drop": "drop", "drops": "drop",
}
TIMES = {1: "once", 2: "twice", 3: "three times", 4: "four times"}

NUMBER_WORDS = set("""zero one two three four five six seven eight nine ten eleven twelve thirteen
fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty
ninety hundred thousand million half halves quarter quarters third thirds once twice thrice double
doubled triple tripled dbl dozen couple pair single both several few many much ii iii iv vi x
tenfold extra another all some any""".split())
UNIT_WORDS = set("""mcgs oz ounce ounces gtt gtts mg mgs mcg ug g gm gms gram grams milligram milligrams
microgram micrograms kg ml mls milliliter milliliters millilitre millilitres l liter liters litre litres
cc u iu ius unit units meq mmol tablet tablets tab tabs pill pills capsule capsules cap caps puff puffs
spray sprays drop drops patch patches teaspoon teaspoons tsp tablespoon tablespoons tbsp vial vials
ampule ampules ampoule ampoules scoop scoops dose doses dosage amount amounts strength strengths""".split())
ROUTE_WORDS = set("""sl pr pv it intrathecal intranasal into mouth oral orally po tongue sublingual
sublingually skin subcutaneous subcutaneously sc sq subq shot shots inject injected injection injections
needle vein iv intravenous intravenously muscle im intramuscular intramuscularly inhale inhaled inhaler
breathe nose nasal eye eyes ear ears rectal rectum rectally topical topically transdermal swallow chew
crush dissolve apply rub tube drip infusion route""".split())
FREQUENCY_WORDS = set("""qam qpm qw stat immediately promptly asap sleep sleeping meal meals food feel
feeling daily day days nightly night nights morning mornings evening evenings noon bedtime breakfast
lunch dinner supper hour hours hourly minute minutes week weeks weekly month months monthly year every
each per times bid tid qid qd qod qhs prn q h hs ac pc needed directed regularly often frequency
schedule scheduled today tonight tomorrow always again until before after while during when whenever
then later now""".split())
NEGATION_WORDS = set("""may might can could should would as keep keeping continue lower lowered raise
adjust exactly not no never don dont doesn t stop stopped skip skipped hold pause quit avoid without
instead only if unless except but or nor cancel discontinue discontinued restart resume change increase
increased decrease decreased reduce more less fewer most least max maximum min minimum up approximately
about around roughly usual normal other else same replace""".split())
FORBIDDEN_WORDS = NUMBER_WORDS | UNIT_WORDS | ROUTE_WORDS | FREQUENCY_WORDS | NEGATION_WORDS

VOCAB_V1 = set("""a an the and to of for on at with by from this that these those its they them their you
your yours we our us is are be been being was were will also so because which who what how why here
there help helps helping control controls controlling prevent prevents preventing protect protects
protecting relax relaxes relaxing manage manages managing treat treats treating support supports medicine
medicines medication medications heart blood pressure sugar cholesterol pain breathing swelling fluid
water salt health doctor nurse pharmacist care team question questions side effect effects stroke strokes
attack attacks infection infections thyroid mood condition conditions level levels risk plan list clots
clot inflammation fever allergies anxiety depression seizures diabetes asthma healthy important symptoms
symptom life""".split())
VOCAB_V2 = set("""a an the and or to of for about on at by from here there this that these those it its
they them their you your yours we our us is are be been being was were will also so ask have has medicine
medicines medication medications list doctor doctors nurse nurses pharmacist pharmacists care team question
questions health plan please thank thanks hello hi important information read carefully what who how why""".split())
VOCAB_V2 -= {"about", "or", "it"}
INSTR_WORDS = {"take"}
TOTAL_WORDS_V1 = {"that", "is", "a", "total", "of"}
TOTAL_WORDS_V2 = {"which", "is"}
NAME_STOP_V2 = set("""see call get help helps medical first milk water bleeding sliding scale taper tapering
titrate titration protocol per until then do does go contact emergency urgent check monitor wait give use
instructions instruction note refer label package insert phone office clinic hospital appointment visit start
starting begin increase decrease reduce change switch new old prior previous replace replaced discontinue
discontinued cancel cancelled canceled error wrong void sample placeholder unknown other misc test result
results inr level levels""".split())

V1_SHAPES = [
    (("w", "take"), ("s", "drug"), ("s", "dose"), ("s", "route"), ("s", "frequency")),
    (("w", "take"), ("s", "drug"), ("s", "sig")),
    (("w", "that"), ("w", "is"), ("w", "a"), ("w", "total"), ("w", "of"), ("s", "daily"), ("w", "of"), ("s", "drug")),
]
V2_SHAPES = [
    (("w", "take"), ("s", "drug"), ("s", "dose"), ("s", "route"), ("s", "frequency")),
    (("w", "take"), ("s", "drug"), ("s", "sig")),
    (("w", "take"), ("s", "drug"), ("s", "dose"), ("s", "route"), ("s", "frequency"),
     ("w", "which"), ("w", "is"), ("s", "daily")),
    (("w", "take"), ("s", "drug"), ("s", "sig"), ("w", "which"), ("w", "is"), ("s", "daily")),
]

CORES = {
    "v1": {"vocab": VOCAB_V1, "total": TOTAL_WORDS_V1, "shapes": V1_SHAPES, "free_drug_slot": True,
           "related": "token", "ambiguity_all_fields": False, "name_rules": "v1", "hours_rule": False,
           "daily_needs_timing": False, "ambiguous_reason": "ambiguousDaily"},
    "v2": {"vocab": VOCAB_V2, "total": TOTAL_WORDS_V2, "shapes": V2_SHAPES, "free_drug_slot": False,
           "related": "conservative", "ambiguity_all_fields": True, "name_rules": "v2", "hours_rule": True,
           "daily_needs_timing": True, "ambiguous_reason": "ambiguousDrug"},
}
TEXT_CHARS = set(string.ascii_letters + string.digits + " \n.,;:!?()'\"-/")
ASCII_LETTERS = set(string.ascii_letters)
SLOT = re.compile(r"\{\{(drug|dose|frequency|route|sig|daily):([A-Za-z0-9.\-]+)\}\}")
SENTENCE_END = re.compile(r"[.!?;:\n]")


class Reject(Exception):
    pass


def parse_request(text):
    count = [0]

    def pairs_hook(pairs):
        keys = [key for key, _ in pairs]
        if len(set(keys)) != len(keys):
            raise Reject("duplicate key")
        if any(key in RESERVED_KEYS for key in keys):
            raise Reject("reserved key")
        return dict(pairs)

    def number(literal):
        count[0] += 1
        if count[0] > MAX_NUMBERS or len(literal) > MAX_LITERAL:
            raise Reject("number limit")
        exponent = re.search(r"[eE]", literal)
        if exponent and len(re.sub(r"^[+-]*", "", literal[exponent.end():])) > MAX_EXPONENT_DIGITS:
            raise Reject("exponent digits")
        return Decimal(literal)

    def constant(name):
        raise Reject("constant")

    return json.loads(text, object_pairs_hook=pairs_hook, parse_int=number, parse_float=number,
                      parse_constant=constant)


def depth(value):
    if isinstance(value, dict):
        return 1 + max((depth(v) for v in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((depth(v) for v in value), default=0)
    return 0


def ascii_lower(text):
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def trim(text):
    return text.strip(" \t\r\n")


def name_prefix_of(t, d):
    tl, dl = ascii_lower(trim(t)), ascii_lower(trim(d))
    return dl.startswith(tl) and (len(dl) == len(tl) or not ("a" <= dl[len(tl)] <= "z"))


def same_text(a, b):
    return ascii_lower(trim(a)) == ascii_lower(trim(b))


def tokens(text):
    return [t.lower() for t in re.findall(r"[A-Za-z0-9]+", text)]


def is_forbidden(token):
    return any(c in string.digits for c in token) or token in FORBIDDEN_WORDS


def present(obj, key):
    return isinstance(obj, dict) and obj.get(key) is not None


def non_empty(value):
    if value is None:
        return False
    if isinstance(value, (list, dict, str)):
        return len(value) > 0
    return True


def route_names(code):
    names = [term for c, term in ROUTE_TERMS if c == code]
    if code in ROUTE_PHRASE:
        names.append(ROUTE_PHRASE[code])
    return names


def route_texts_ok(route):
    codings = route.get("coding") if isinstance(route, dict) else None
    codings = codings if isinstance(codings, list) else []
    accepted = []
    for coding in codings:
        if isinstance(coding, dict) and coding.get("system") == SNOMED and isinstance(coding.get("code"), str):
            accepted.extend(route_names(coding["code"]))
    texts = []
    if isinstance(route, dict) and route.get("text") is not None:
        texts.append(route["text"])
    for coding in codings:
        if isinstance(coding, dict) and coding.get("display") is not None:
            texts.append(coding["display"])
    for text in texts:
        if not isinstance(text, str) or not any(same_text(text, name) for name in accepted):
            return False
    return True


def unit_accepted(code, unit):
    spelled = ascii_lower(trim(unit))
    if spelled == ascii_lower(code):
        return True
    key = UNIT_OF_CODE.get(code)
    if key is None:
        return False
    singular, plural = UNIT_NAMES[key]
    return spelled in (ascii_lower(singular), ascii_lower(plural)) or spelled in UNIT_ABBREVIATIONS.get(key, [])


def quantity_ok(quantity):
    system = quantity.get("system")
    if system is not None and not (isinstance(system, str) and system == UCUM):
        return False
    unit, code = quantity.get("unit"), quantity.get("code")
    if unit is not None and code is not None:
        if not (isinstance(unit, str) and isinstance(code, str)):
            return False
        return unit_accepted(code, unit)
    return True


def subject_ref(order):
    subject = order.get("subject")
    ref = subject.get("reference") if isinstance(subject, dict) else None
    return ref if isinstance(ref, str) and ref != "" else None


def drug_of(order):
    concept = order.get("medicationCodeableConcept")
    if not isinstance(concept, dict):
        return ""
    displays = []
    codings = concept.get("coding")
    if isinstance(codings, list):
        for coding in codings:
            if isinstance(coding, dict) and isinstance(coding.get("display"), str):
                display = trim(coding["display"])
                if display:
                    displays.append(display)
    common = displays[0] if displays and all(same_text(d, displays[0]) for d in displays) else ""
    text = concept.get("text")
    if isinstance(text, str):
        spelled = trim(text)
        if spelled == "":
            return common
        return spelled if all(name_prefix_of(spelled, d) for d in displays) else ""
    return common


def is_active(order, patient):
    if order.get("status") != "active":
        return False
    intent = order.get("intent")
    if not (isinstance(intent, str) and intent in ORDER_INTENTS):
        return False
    not_performed = order.get("doNotPerform")
    if not_performed is not None and not_performed is not False:
        return False
    if patient is not None and subject_ref(order) not in ("Patient/" + patient, "urn:uuid:" + patient):
        return False
    return True


def count_of(value):
    if not isinstance(value, Decimal) or value < 0 or value != value.to_integral_value():
        return None
    return int(value) if value <= MAX_COUNT else None


def dose_of(dosage):
    rates = dosage.get("doseAndRate")
    first = rates[0] if isinstance(rates, list) and rates else None
    quantity = first.get("doseQuantity") if isinstance(first, dict) else None
    if not isinstance(quantity, dict):
        return None
    value = quantity.get("value")
    if not isinstance(value, Decimal):
        return None
    sign, digits, exponent = value.as_tuple()
    coefficient = int("".join(map(str, digits)))
    if sign and coefficient:
        return None
    if exponent > 0:
        mantissa, scale = coefficient * 10 ** exponent, 0
    else:
        mantissa, scale = coefficient, -exponent
    if scale > MAX_SCALE or mantissa >= 10 ** 15 or mantissa == 0:
        return None
    if quantity.get("code") is not None:
        code = quantity["code"]
        key = UNIT_OF_CODE.get(code) if isinstance(code, str) else None
    else:
        unit = quantity.get("unit")
        key = UNIT_OF_CODE.get(unit) if isinstance(unit, str) else None
    if key is None:
        return None
    return (mantissa, scale, key)


def timing_of(dosage):
    timing = dosage.get("timing")
    repeat = timing.get("repeat") if isinstance(timing, dict) else None
    if not isinstance(repeat, dict):
        return None
    frequency = count_of(repeat.get("frequency"))
    period = count_of(repeat.get("period"))
    unit = repeat.get("periodUnit")
    if frequency is None or period is None or not (isinstance(unit, str) and unit in PERIOD_UNITS):
        return None
    return (frequency, period, unit)


def route_of(dosage):
    route = dosage.get("route")
    codings = route.get("coding") if isinstance(route, dict) else None
    if not isinstance(codings, list) or not codings:
        return None
    phrases = set()
    for coding in codings:
        if not (isinstance(coding, dict) and coding.get("system") == SNOMED):
            return None
        code = coding.get("code")
        if not (isinstance(code, str) and code in ROUTE_PHRASE):
            return None
        phrases.add(ROUTE_PHRASE[code])
    return phrases.pop() if len(phrases) == 1 else None


def fails_closed(dosage):
    timing = dosage.get("timing")
    if isinstance(timing, dict):
        if timing.get("code") is not None:
            return True
        repeat = timing.get("repeat")
        if isinstance(repeat, dict) and any(repeat.get(k) is not None for k in (
                "frequencyMax", "periodMax", "duration", "durationMax", "durationUnit", "countMax",
                "boundsDuration", "boundsRange", "boundsPeriod", "count", "offset", "dayOfWeek",
                "timeOfDay", "when")):
            return True
    if any(dosage.get(k) is not None for k in (
            "maxDosePerPeriod", "maxDosePerAdministration", "maxDosePerLifetime", "asNeededCodeableConcept")):
        return True
    rates = dosage.get("doseAndRate")
    rates = rates if isinstance(rates, list) else []
    first = rates[0] if rates and isinstance(rates[0], dict) else None
    if first is not None:
        if first.get("doseRange") is not None:
            return True
        quantity = first.get("doseQuantity")
        if isinstance(quantity, dict) and quantity.get("comparator") is not None:
            return True
    as_needed = dosage.get("asNeededBoolean")
    if as_needed is not None and not isinstance(as_needed, bool):
        return True
    return len(rates) > 1


def order_closed(order, oid, refs):
    if any(present(order, k) for k in ("extension", "modifierExtension", "priorPrescription")):
        return True
    if any(present(order.get("medicationCodeableConcept"), k) for k in ("extension", "modifierExtension")):
        return True
    if f"MedicationRequest/{oid}" in refs:
        return True
    meta = order.get("meta")
    if isinstance(meta, dict) and non_empty(meta.get("security")):
        return True
    request = order.get("dispenseRequest")
    return isinstance(request, dict) and present(request, "validityPeriod")


def dosage_closed(dosage):
    if any(present(dosage, k) for k in ("extension", "modifierExtension", "site", "method")):
        return True
    if any(present(dosage.get("timing"), k) for k in ("extension", "modifierExtension")):
        return True
    route = dosage.get("route")
    if any(present(route, k) for k in ("extension", "modifierExtension")):
        return True
    if isinstance(route, dict) and not route_texts_ok(route):
        return True
    rates = dosage.get("doseAndRate")
    first = rates[0] if isinstance(rates, list) and rates else None
    if isinstance(first, dict):
        if any(present(first, k) for k in ("extension", "modifierExtension", "rateQuantity", "rateRatio",
                                            "rateRange", "type")):
            return True
        quantity = first.get("doseQuantity")
        if isinstance(quantity, dict) and not quantity_ok(quantity):
            return True
    return False


def free_text_closed(order, dosage):
    return any(present(dosage, k) for k in ("text", "additionalInstruction", "patientInstruction")) or \
        present(order, "note")


def build_order(order, patient, refs):
    built = {"id": order["id"], "active": is_active(order, patient), "drug": drug_of(order),
             "dose": None, "timing": None, "route": None, "as_needed": False}
    dosages = order.get("dosageInstruction")
    if not isinstance(dosages, list) or len(dosages) != 1 or not isinstance(dosages[0], dict):
        return built
    dosage = dosages[0]
    if fails_closed(dosage) or order_closed(order, order["id"], refs) or dosage_closed(dosage) \
            or free_text_closed(order, dosage):
        return built
    built["dose"] = dose_of(dosage)
    built["timing"] = timing_of(dosage)
    built["route"] = route_of(dosage)
    built["as_needed"] = dosage.get("asNeededBoolean") is True
    return built


def times_word(n):
    return TIMES.get(n) or f"{n} times"


def unit_word(unit, singular):
    return {"h": ("hour", "hours"), "d": ("day", "days"), "wk": ("week", "weeks"),
            "mo": ("month", "months")}[unit][0 if singular else 1]


def fmt_timing(timing, cfg):
    frequency, period, unit = timing
    if frequency == 0 or period == 0:
        return None
    if cfg["hours_rule"] and unit == "h" and frequency > 1:
        return None
    if period == 1:
        if frequency == 1 and unit == "h":
            return "every hour"
        return f"{times_word(frequency)} a {unit_word(unit, True)}"
    if frequency == 1:
        return f"every {period} {unit_word(unit, False)}"
    return f"{times_word(frequency)} every {period} {unit_word(unit, False)}"


def fmt_frequency(built, cfg):
    if built["timing"] is None:
        return "as needed" if built["as_needed"] else None
    text = fmt_timing(built["timing"], cfg)
    if text is None:
        return None
    return text + " as needed" if built["as_needed"] else text


def fmt_decimal(mantissa, scale):
    if scale == 0:
        return str(mantissa)
    digits = str(mantissa).rjust(scale + 1, "0")
    return f"{digits[:-scale]}.{digits[-scale:]}"


def fmt_dose(dose):
    mantissa, scale, key = dose
    while scale > 0 and mantissa % 10 == 0:
        mantissa //= 10
        scale -= 1
    singular, plural = UNIT_NAMES[key]
    name = singular if mantissa == 1 and scale == 0 else plural
    return f"{fmt_decimal(mantissa, scale)} {name}"


def doses_per_day(timing):
    frequency, period, unit = timing
    if unit == "d" and period == 1 and frequency != 0:
        return frequency
    if unit == "h" and period != 0 and 24 % period == 0 and frequency != 0:
        return frequency * (24 // period)
    return None


def daily_dose(built, cfg):
    if built["as_needed"] or built["dose"] is None or built["timing"] is None:
        return None
    per_day = doses_per_day(built["timing"])
    if per_day is None:
        return None
    if cfg["daily_needs_timing"] and fmt_timing(built["timing"], cfg) is None:
        return None
    mantissa, scale, key = built["dose"]
    return (mantissa * per_day, scale, key)


def drug_name_ok(name, cfg):
    words = tokens(name)
    if not any(c in ASCII_LETTERS for c in name) or len(name) > MAX_NAME_LENGTH or len(words) > MAX_NAME_WORDS:
        return False
    if not all(c in ASCII_LETTERS or c in " -" for c in name):
        return False
    if any(is_forbidden(w) for w in words):
        return False
    if cfg["name_rules"] == "v2" and not (name[:1] in ASCII_LETTERS and name[-1:] in ASCII_LETTERS):
        return False
    if cfg["name_rules"] == "v2":
        for w in words:
            if w in cfg["vocab"] or w in INSTR_WORDS or w in cfg["total"] or w in NAME_STOP_V2:
                return False
    return True


def related(a, b, cfg):
    if cfg["related"] == "token":
        return a == b or bool(set(tokens(a)) & set(tokens(b)))
    ta, tb = tokens(a), tokens(b)
    if not any(t.isalpha() for t in ta) or not any(t.isalpha() for t in tb):
        return True
    if any(ord(c) > 127 for c in a + b):
        return True
    if ascii_lower(a) == ascii_lower(b):
        return True
    if set(ta) & set(tb):
        return True
    for x in ta:
        for y in tb:
            short, long_ = (x, y) if len(x) <= len(y) else (y, x)
            if len(short) >= 4 and long_.startswith(short):
                return True
    return False


def fmt_field(field, built, cfg):
    if field == "drug":
        return built["drug"] if drug_name_ok(built["drug"], cfg) else None
    if field == "dose":
        return fmt_dose(built["dose"]) if built["dose"] else None
    if field == "route":
        return built["route"] if built["route"] else None
    if field == "frequency":
        return fmt_frequency(built, cfg)
    if field == "daily":
        total = daily_dose(built, cfg)
        return fmt_dose(total) + " a day" if total else None
    if built["dose"] and built["route"] and fmt_frequency(built, cfg) is not None:
        return f"{fmt_dose(built['dose'])} {built['route']}, {fmt_frequency(built, cfg)}"
    return None


def parse_template(out):
    segs = []
    position = 0
    for match in SLOT.finditer(out):
        text = out[position:match.start()]
        if "{" in text or "}" in text:
            return None
        if text:
            segs.append(("text", text))
        segs.append(("slot", match.group(1), match.group(2)))
        position = match.end()
    tail = out[position:]
    if "{" in tail or "}" in tail:
        return None
    if tail:
        segs.append(("text", tail))
    return segs


def sentences(segs):
    result = [[]]
    for seg in segs:
        if seg[0] == "slot":
            result[-1].append(("s", seg[1], seg[2]))
            continue
        for index, part in enumerate(SENTENCE_END.split(seg[1])):
            if index:
                result.append([])
            result[-1].extend(("w", token) for token in tokens(part))
    return result


def sentence_ok(items, cfg):
    if len({item[2] for item in items if item[0] == "s"}) > 1:
        return False
    shape = tuple((item[0], item[1]) for item in items)
    if any(item[0] == "s" and item[1] != "drug" for item in items):
        return shape in cfg["shapes"]
    if not cfg["free_drug_slot"] and any(item[0] == "s" for item in items):
        return False
    return all(item[1] in cfg["vocab"] for item in items if item[0] == "w")


def no_repeated_value(segs):
    values = [(seg[1], seg[2]) for seg in segs if seg[0] == "slot" and seg[1] != "drug"]
    if len(values) != len(set(values)):
        return False
    for field, sid in values:
        if field == "sig" and any(other in (("dose", sid), ("route", sid), ("frequency", sid))
                                  for other in values):
            return False
    return True


def check_text(text, cfg):
    if any(c not in TEXT_CHARS for c in text):
        return "nonAscii"
    words = tokens(text)
    if any(is_forbidden(w) for w in words):
        return "forbiddenWord"
    if any(not (w in cfg["vocab"] or w in INSTR_WORDS or w in cfg["total"]) for w in words):
        return "unknownWord"
    return None


def separated_all(pieces):
    filled = [p for p in pieces if p]
    return all(not (a[-1] in ASCII_ALNUM and b[0] in ASCII_ALNUM) for a, b in zip(filled, filled[1:]))


ASCII_ALNUM = set(string.ascii_letters + string.digits)


def render(chart, out, cfg):
    ids = [built["id"] for built in chart]
    if len(set(ids)) != len(ids):
        return ("blocked", "duplicateIds")
    segs = parse_template(out)
    if segs is None:
        return ("blocked", "malformed")
    if not all(sentence_ok(items, cfg) for items in sentences(segs)):
        return ("blocked", "unbound")
    if not no_repeated_value(segs):
        return ("blocked", "repeatedValue")
    pieces = []
    for seg in segs:
        if seg[0] == "text":
            problem = check_text(seg[1], cfg)
            if problem:
                return ("blocked", problem)
            pieces.append(seg[1])
            continue
        _, field, sid = seg
        found = [built for built in chart if built["id"] == sid]
        if not found:
            return ("blocked", "unknownRef")
        built = found[0]
        if not built["active"]:
            return ("blocked", "inactiveOrder")
        if (field == "daily" or cfg["ambiguity_all_fields"]) and sum(
                1 for other in chart if other["active"] and related(other["drug"], built["drug"], cfg)) > 1:
            return ("blocked", cfg["ambiguous_reason"])
        piece = fmt_field(field, built, cfg)
        if piece is None:
            return ("blocked", "missingField")
        pieces.append(piece)
    if not separated_all(pieces):
        return ("blocked", "unseparated")
    return ("ok", "".join(pieces))


def predict(line, core):
    cfg = CORES[core]
    text = line.strip(" \t\r\n")
    if len(text.encode("utf-8")) > MAX_REQUEST_BYTES:
        return ("error",)
    try:
        request = parse_request(text)
    except (ValueError, Reject, RecursionError):
        return ("error",)
    if not isinstance(request, dict) or depth(request) > MAX_DEPTH:
        return ("error",)
    out = request.get("output")
    if not isinstance(out, str) or len(out) > MAX_OUTPUT or out.count("{{") > MAX_SLOTS:
        return ("error",)
    if "bundle" in request:
        bundle = request["bundle"]
        if not isinstance(bundle, dict) or not isinstance(bundle.get("entry"), list):
            return ("error",)
        kind = bundle.get("type")
        if kind is not None and not (isinstance(kind, str) and kind in ("searchset", "collection")):
            return ("error",)
        if any(isinstance(entry, dict) and entry.get("request") is not None for entry in bundle["entry"]):
            return ("error",)
        orders = [entry["resource"] for entry in bundle["entry"] if isinstance(entry, dict)
                  and isinstance(entry.get("resource"), dict)
                  and entry["resource"].get("resourceType") == "MedicationRequest"]
    elif "medicationRequests" in request:
        if not isinstance(request["medicationRequests"], list):
            return ("error",)
        orders = request["medicationRequests"]
    else:
        return ("error",)
    if not all(isinstance(order, dict) and isinstance(order.get("id"), str) for order in orders):
        return ("error",)
    patient = request.get("patient")
    if patient is not None and (not isinstance(patient, str) or patient == ""):
        return ("error",)
    if patient is None:
        refs = [subject_ref(order) for order in orders]
        if None in refs or len(set(refs)) > 1:
            return ("error",)
    if len(orders) > MAX_ORDERS:
        return ("error",)
    prior = {order["priorPrescription"]["reference"] for order in orders
             if isinstance(order.get("priorPrescription"), dict)
             and isinstance(order["priorPrescription"].get("reference"), str)}
    chart = [build_order(order, patient, prior) for order in orders]
    result = render(chart, out, cfg)
    if result[0] == "ok" and len(result[1]) > MAX_OUTPUT:
        return ("error",)
    return result


def agrees(prediction, reply):
    if prediction[0] == "error":
        return reply.get("status") == "error"
    if prediction[0] == "ok":
        return reply.get("status") == "ok" and reply.get("text") == prediction[1]
    return reply.get("status") == "blocked" and reply.get("reason") == prediction[1]


def key_of_prediction(prediction):
    if prediction[0] == "blocked":
        return "blocked:" + prediction[1]
    return prediction[0]


def key_of_reply(reply):
    if reply.get("status") == "blocked":
        return "blocked:" + str(reply.get("reason"))
    return str(reply.get("status"))


class O(list):
    """A JSON object as ordered (key, value) pairs, so duplicate keys can be written."""


class Lit(str):
    """A JSON number written exactly as this text."""


class EK(str):
    """A key written with \\u escapes."""


def clone(value):
    if isinstance(value, O):
        return O((k, clone(v)) for k, v in value)
    if isinstance(value, list):
        return [clone(v) for v in value]
    return value


def to_o(value):
    if isinstance(value, dict):
        return O((k, to_o(v)) for k, v in value.items())
    if isinstance(value, list):
        return [to_o(v) for v in value]
    return value


def key_text(key, ascii_only):
    if isinstance(key, EK):
        return '"' + "".join(f"\\u{ord(c):04x}" for c in key) + '"'
    return json.dumps(str(key), ensure_ascii=ascii_only)


def dump(value, ascii_only, sep):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (Lit, int)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(str(value), ensure_ascii=ascii_only)
    if isinstance(value, O):
        items = [key_text(k, ascii_only) + sep[1] + dump(v, ascii_only, sep) for k, v in value]
        return "{" + sep[0].join(items) + "}"
    return "[" + sep[0].join(dump(v, ascii_only, sep) for v in value) + "]"


def children(value):
    if isinstance(value, O):
        return [v for _, v in value]
    if isinstance(value, list):
        return value
    return []


def walk(value):
    yield value
    for child in children(value):
        yield from walk(child)


def objects(root):
    return [node for node in walk(root) if isinstance(node, O)]


def pairs_with_keys(root, names):
    return [(obj, i) for obj in objects(root) for i, (k, _) in enumerate(obj) if k in names]


def has_key(obj, key):
    return any(k == key for k, _ in obj)


def set_key_in(obj, key, value):
    for i, (k, _) in enumerate(obj):
        if k == key:
            obj[i] = (key, value)
            return
    obj.append((key, value))


def set_some(rng, root, key, values):
    hits = pairs_with_keys(root, (key,))
    value = rng.choice(values)
    if hits and rng.random() < 0.8:
        obj, i = rng.choice(hits)
        obj[i] = (key, value)
    else:
        rng.choice(objects(root)).append((key, value))
    return True


def random_value(rng):
    return rng.choice([
        None, True, False, Lit("0"), Lit("2.5"), "", "x", "mg", "Take", [], O(), [O([("reference", "Patient/pat1")])],
        O([("text", "aspirin")]), Lit("1000"),
    ])


NUMBER_EDGES = [
    "0", "-0", "-1", "0.0", "0.5", "1", "1.0", "1.50", "2.0", "2.5", "3", "5", "5.0000000000", "5.000000000",
    "7", "24", "81", "100", "1000", "1000.0", "1001", "1e3", "1E+2", "1e-3", "2.5e-1", "12e-9",
    "0.000000001", "0.0000000001", "0.25", "1.5e1", "0.5e1", "999999999999999", "1000000000000000",
    "999999999999999.9", "1234567890123456", "1e15", "1e99", "1e100", "12345678901234567890",
    "0." + "0" * 20 + "1", "1" * 1001,
]
COUNT_EDGES = ["0", "1", "2", "3", "4", "5", "6", "8", "12", "24", "1000", "1001", "0.5", "2.0", "1e3", "-1", "1.5"]
STRING_POOL = [
    "", " ", "active", "Active", " active", "completed", "order", "proposal", "plan", "aspirin", "Aspirin",
    "metformin hydrochloride", "metformin-hydrochloride", "Metformin", "naproxen sodium",
    "levothyroxine sodium", "insulin glargine", "aspirin 81 MG Oral Tablet", "aspirin mg", "two tablets",
    "daily", "Patient/pat1", "Patient/pat2", "urn:uuid:pat1", "Patient/", "pat1", "café aspirin",
    "aspirin\U0001F600", "b" * 61, "word " * 6, "a-b-c-d-e", "Lisinopril 10 MG Oral Tablet", "drug 1", "mg",
    "units", "Patient", "MedicationRequest", "ASA", "aspirin\u0000", "Take", "Hold until your doctor restarts it",
    "a b", "ab-cd", "warfarin", "Warfarin", "insulin sliding scale", "Take with milk", "Warfarin see doctor first",
    "metformin", "Metformin Hydrochloride", "  aspirin  ", "\taspirin", "aspirin\n", "Oral route",
]
REFS = ["Patient/pat1", "Patient/pat1", "Patient/pat1", "Patient/pat2", "urn:uuid:pat1", "Patient/", "",
        "pat1", "Patient/PAT1", "Patient/pat1 "]
PATIENTS = ["pat1", "pat1", "pat1", "pat2", "urn:uuid:pat1", "Patient/pat1", "", None, Lit("1"), True, "PAT1"]
STATUSES = ["active"] * 8 + ["completed", "on-hold", "entered-in-error", "stopped", "draft", "unknown", "Active",
                             " active", None, Lit("1"), True]
INTENTS = ["order"] * 6 + ["original-order", "reflex-order", "filler-order", "instance-order", "proposal",
                           "plan", "Order", None, Lit("1")]
DNP_VALUES = [False, False, True, None, "no", Lit("0")]
AS_NEEDED_VALUES = [True, False, False, "yes", None, Lit("1")]
UNIT_VALUES = ["mg"] * 5 + ["mcg", "ug", "g", "mL", "ml", "L", "U", "[iU]", "[IU]", "units", "unit", "{tbl}",
                            "TAB", "tablet", "{cap}", "CAP", "capsule", "{puff}", "puff", "[drp]", "drop", "MG",
                            "mg/mL", "xyz", "", None, Lit("5"), True]
UNIT_PAIRS = [("mg", "mg"), ("MG", "mg"), ("milligrams", "mg"), ("tablet", "mg"), ("ug", "mcg"), ("mcg", "ug"),
              ("IU", "[iU]"), ("units", "U"), ("tablet", "{tbl}"), ("tablets", "TAB"), ("drops", "[drp]"),
              ("gtt", "[drp]"), ("cap", "CAP"), ("mL", "ml"), ("ml", "mL"), ("milliliter", "mL"),
              ("Units", "units"), (" mg ", "mg"), ("", "mg"), ("mg", ""), ("g", "mg"), (5, "mg"), ("mg", 5),
              ("mg", None), (None, "mg"), (True, "mg"), ("xyz", "xyz"), ("micrograms", "mcg"), ("puffs", "puff"),
              ("unit", "[IU]"), ("tab", "{tbl}"), ("gram", "g")]
SYSTEM_VALUES = [UCUM] * 6 + ["http://example.org/units", None, "", Lit("5"), UCUM + "/", "HTTP://UNITSOFMEASURE.ORG"]
PERIOD_UNIT_VALUES = ["h", "d", "wk", "mo", "d", "d", "wk", "min", "D", None, Lit("1")]
DRUG_NAMES = ["metformin hydrochloride", "Metformin", "aspirin mg", "naproxen sodium", "insulin glargine",
              "levothyroxine sodium", "Lisinopril 10 MG Oral Tablet", "two tablets", "b" * 61, "a b c d e f",
              "warfarin", "Warfarin", "Take with milk", "Warfarin see doctor first", "insulin sliding scale",
              "aspirin", "Aspirin", "ASPIRIN", "metformin", "  aspirin ", "aspirin.", "ab-cd", "a-b-c-d-e",
              "inhaled", "Oral route", "medicine", "about", "lisinopril", "insulin", "glargine"]
ID_VALUES = ["m2", "m3", "M1", "m 1", "", "m.1", "m-1", "m1", None, Lit("1")]
ID_EXTRA = ["m9", "M1", "m 1", "m.1", "", "m-1", "x"]
NOISE = ["{", "}", "é", "*", "two", "5", "medicine", "x", "\n", "%", "now", "mg", " ", ".", "is", "your",
         "take", "Take", "tablet", "every", "which", "daily", "about", "or", "ask"]
ROUTE_CODES = [code for code, _ in ROUTE_TERMS]
ROUTE_TEXT_VALUES = ["by mouth", "Oral route", "ORAL USE", "Oral use", "under the tongue", "Sublingual route", "",
                     " by mouth ", None, 5, "Oral", "oral route", "into a vein", "Intravenous route"]
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
TIMING_FAIL_KEYS = ["code", "frequencyMax", "periodMax", "duration", "durationMax", "durationUnit", "countMax",
                    "boundsDuration", "boundsRange", "boundsPeriod", "count", "offset", "dayOfWeek", "timeOfDay",
                    "when"]
ADD_KEYS = ["note", "text", "additionalInstruction", "patientInstruction", "doNotPerform", "asNeededBoolean",
            "maxDosePerPeriod", "asNeededCodeableConcept", "comparator", "doseRange", "dispenseRequest", "code",
            "timing", "repeat", "extra", "status", "intent", "boundsRange", "frequencyMax", "count", "when",
            "periodMax", "durationUnit", "subject", "id", "resourceType", "patient", "pad2", "x", "meta",
            "priorPrescription", "extension", "modifierExtension", "site", "method", "rateQuantity", "type",
            "system", "unit", "code", "request"]
KEY_NAMES = ("status", "intent", "id", "subject", "reference", "medicationCodeableConcept", "dosageInstruction",
             "doseAndRate", "doseQuantity", "value", "unit", "code", "system", "coding", "text", "display",
             "timing", "repeat", "frequency", "period", "periodUnit", "route", "resourceType", "entry", "resource",
             "bundle", "medicationRequests", "output", "dispenseRequest", "validityPeriod", "end",
             "asNeededBoolean", "doNotPerform", "meta", "security", "priorPrescription", "extension")
TEMPLATES = [
    "Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}}.",
    "Take {{drug:ID}} {{sig:ID}}.",
    "Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}} which is {{daily:ID}}.",
    "Take {{drug:ID}} {{sig:ID}} which is {{daily:ID}}.",
    "That is a total of {{daily:ID}} of {{drug:ID}}.",
    "Your medicine is {{drug:ID}}.",
    "Take{{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}}.",
    "Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}} now.",
    "Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}}. Take {{drug:ID}} {{sig:ID}}.",
    "Your medicine is {{drug:ID}}. That is a total of {{daily:ID}} of {{drug:ID}}.",
    "Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}} which is {{daily:ID}}. Please ask your doctor.",
    "{{drug:ID}} with water.",
    "Please ask your doctor about this.",
    "Ask your doctor or nurse if you have questions.",
    "Please read carefully: take {{drug:ID}} {{sig:ID}}.",
    "Take {{drug:ID}} {{dose:ID}}, {{route:ID}}, {{frequency:ID}}.",
    "Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}} {{daily:ID}}.",
]
VALUE_TEMPLATES = TEMPLATES[:4] + TEMPLATES[6:9] + TEMPLATES[10:11] + TEMPLATES[14:16]
RAW_CHARS = '{}[],:"\\0123456789eE+-. tfn'


def m_drop_pair(rng, root):
    if rng.random() < 0.5:
        return False
    objs = [o for o in objects(root) if o]
    if not objs:
        return False
    obj = rng.choice(objs)
    del obj[rng.randrange(len(obj))]
    return True


def m_drop_known_key(rng, root):
    hits = pairs_with_keys(root, KEY_NAMES)
    if not hits:
        return False
    obj, i = rng.choice(hits)
    del obj[i]
    return True


def m_duplicate_pair(rng, root):
    if rng.random() < 0.7:
        return False
    objs = [o for o in objects(root) if o]
    if not objs:
        return False
    obj = rng.choice(objs)
    key, value = rng.choice(obj)
    obj.insert(rng.randint(0, len(obj)), (key, value if rng.random() < 0.5 else random_value(rng)))
    return True


def m_add_key(rng, root):
    obj = rng.choice(objects(root))
    obj.insert(rng.randint(0, len(obj)), (rng.choice(ADD_KEYS), random_value(rng)))
    return True


def m_retype_value(rng, root):
    hits = [(o, i) for o in objects(root) for i in range(len(o))]
    if not hits:
        return False
    obj, i = rng.choice(hits)
    obj[i] = (obj[i][0], random_value(rng))
    return True


def m_string_edge(rng, root):
    hits = [(o, i) for o in objects(root) for i, (_, v) in enumerate(o) if type(v) is str]
    if not hits:
        return False
    obj, i = rng.choice(hits)
    obj[i] = (obj[i][0], rng.choice(STRING_POOL))
    return True


def m_number_edge(rng, root):
    hits = [(o, i) for o in objects(root) for i, (_, v) in enumerate(o) if isinstance(v, Lit)]
    if not hits:
        return False
    obj, i = rng.choice(hits)
    obj[i] = (obj[i][0], Lit(rng.choice(NUMBER_EDGES)))
    return True


def m_number_respell(rng, root):
    hits = [(o, i) for o in objects(root) for i, (_, v) in enumerate(o) if isinstance(v, Lit)]
    if not hits:
        return False
    obj, i = rng.choice(hits)
    text = str(obj[i][1])
    spelling = rng.choice([text + ".0", text + "e0", text + "E+0", text + "e-0", "0" + text, "-" + text,
                           text + ".000000000", text + "e1", text + "0"])
    obj[i] = (obj[i][0], Lit(spelling))
    return True


def m_status(rng, root):
    return set_some(rng, root, "status", STATUSES)


def m_intent(rng, root):
    return set_some(rng, root, "intent", INTENTS)


def m_do_not_perform(rng, root):
    return set_some(rng, root, "doNotPerform", DNP_VALUES)


def m_as_needed(rng, root):
    return set_some(rng, root, "asNeededBoolean", AS_NEEDED_VALUES)


def m_subject(rng, root):
    roll = rng.random()
    if roll < 0.6:
        value = O([("reference", rng.choice(REFS))])
    elif roll < 0.8:
        value = None
    else:
        value = rng.choice(["Patient/pat1", Lit("1"), []])
    return set_some(rng, root, "subject", [value])


def m_patient(rng, root):
    set_key_in(root, "patient", rng.choice(PATIENTS))
    return True


def m_resource_type(rng, root):
    return set_some(rng, root, "resourceType", ["Patient", "MedicationStatement", "MedicationRequest",
                                                "MedicationRequest"])


def m_dose_unit(rng, root):
    hits = pairs_with_keys(root, ("code", "unit"))
    if not hits:
        return False
    obj, i = rng.choice(hits)
    obj[i] = (obj[i][0], rng.choice(UNIT_VALUES))
    return True


def m_unit_pair(rng, root):
    hits = pairs_with_keys(root, ("doseQuantity",))
    quantities = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not quantities:
        return False
    unit, code = rng.choice(UNIT_PAIRS)
    quantity = rng.choice(quantities)
    for key, value in (("unit", unit), ("code", code)):
        if value is None:
            quantity[:] = [(k, v) for k, v in quantity if k != key]
        else:
            set_key_in(quantity, key, value)
    return True


def m_quantity_system(rng, root):
    hits = pairs_with_keys(root, ("doseQuantity",))
    quantities = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not quantities:
        return False
    set_key_in(rng.choice(quantities), "system", rng.choice(SYSTEM_VALUES))
    return True


def route_coding(rng):
    system = rng.choice([SNOMED] * 6 + [RXNORM, "http://snomed.info/sct/x"])
    code = rng.choice(ROUTE_CODES + ["99999999", Lit("26643006")])
    return O([("system", system), ("code", code)])


def m_route(rng, root):
    hits = pairs_with_keys(root, ("route",))
    if not hits:
        return False
    obj, i = rng.choice(hits)
    if rng.random() < 0.15:
        del obj[i]
    else:
        obj[i] = ("route", O([("coding", [route_coding(rng) for _ in range(rng.randint(0, 3))])]))
    return True


def m_route_text(rng, root):
    hits = pairs_with_keys(root, ("route",))
    routes = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not routes:
        return False
    route = rng.choice(routes)
    if rng.random() < 0.5:
        set_key_in(route, "text", rng.choice(ROUTE_TEXT_VALUES))
    else:
        codings = [v for k, v in route if k == "coding" and isinstance(v, list) and v and isinstance(v[0], O)]
        if not codings:
            return False
        set_key_in(codings[0][0], "display", rng.choice(ROUTE_TEXT_VALUES))
    return True


def m_timing_repeat(rng, root):
    hits = pairs_with_keys(root, ("repeat",))
    repeats = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not repeats:
        return False
    repeat = rng.choice(repeats)
    key = rng.choice(["frequency", "period", "periodUnit"])
    value = rng.choice(PERIOD_UNIT_VALUES) if key == "periodUnit" else Lit(rng.choice(COUNT_EDGES))
    set_key_in(repeat, key, value)
    return True


def m_timing_fail(rng, root):
    targets = [o for o in objects(root) if has_key(o, "repeat") or has_key(o, "timing")
               or has_key(o, "frequency")]
    if not targets:
        return False
    set_key_in(rng.choice(targets), rng.choice(TIMING_FAIL_KEYS), random_value(rng))
    return True


def m_dosage_count(rng, root):
    hits = pairs_with_keys(root, ("dosageInstruction",))
    if not hits:
        return False
    obj, i = rng.choice(hits)
    value = obj[i][1]
    roll = rng.randrange(4)
    if roll == 0 and isinstance(value, list) and value:
        new = value + clone(value)
    elif roll == 1:
        new = []
    elif roll == 2:
        new = O([("timing", None)])
    elif isinstance(value, list) and value:
        new = value + [clone(value[0])]
    else:
        new = []
    obj[i] = (obj[i][0], new)
    return True


def m_dose_and_rate(rng, root):
    hits = pairs_with_keys(root, ("doseAndRate", "doseQuantity"))
    if not hits:
        return False
    obj, i = rng.choice(hits)
    key, value = obj[i]
    if key == "doseAndRate":
        if isinstance(value, list) and value and rng.random() < 0.5:
            obj[i] = (key, value + [clone(value[0])])
        elif isinstance(value, list) and value and isinstance(value[0], O):
            value[0].append(("doseRange", random_value(rng)))
        else:
            obj[i] = (key, [])
    elif isinstance(value, O):
        value.append(("comparator", rng.choice(["<", ">", Lit("1")])))
    return True


def first_rates(root):
    return [obj[i][1][0] for obj, i in pairs_with_keys(root, ("doseAndRate",))
            if isinstance(obj[i][1], list) and obj[i][1] and isinstance(obj[i][1][0], O)]


def m_rate_keys(rng, root):
    rates = first_rates(root)
    if not rates:
        return False
    key = rng.choice(["rateQuantity", "rateRatio", "rateRange", "type", "extension", "modifierExtension"])
    set_key_in(rng.choice(rates), key, rng.choice([O([("value", Lit("1"))]), None, [], "x", True]))
    return True


def m_dosage_keys(rng, root):
    targets = [o for o in objects(root) if has_key(o, "doseAndRate") or has_key(o, "timing")
               or has_key(o, "route")]
    if not targets:
        return False
    key = rng.choice(["site", "method", "extension", "modifierExtension"])
    set_key_in(rng.choice(targets), key, rng.choice([O([("text", "left arm")]), None, [], "x", True]))
    return True


def m_timing_extension(rng, root):
    hits = pairs_with_keys(root, ("timing", "route", "medicationCodeableConcept"))
    targets = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not targets:
        return False
    key = rng.choice(["extension", "modifierExtension"])
    set_key_in(rng.choice(targets), key, rng.choice([[O([("url", "x")])], None, [], "x"]))
    return True


def m_order_extension(rng, root):
    orders = [o for o in objects(root) if has_key(o, "medicationCodeableConcept")]
    if not orders:
        return False
    key = rng.choice(["extension", "modifierExtension", "priorPrescription", "meta", "dispenseRequest"])
    if key in ("extension", "modifierExtension"):
        value = rng.choice([[O([("url", "x")])], [], None])
    elif key == "priorPrescription":
        value = O([("reference", rng.choice(["MedicationRequest/m1", "MedicationRequest/m2",
                                             "MedicationRequest/m9", "MedicationRequest/", "Medication/m1"]))])
    elif key == "meta":
        value = O([("security", rng.choice([[], [O([("code", "R")])], "R", O(), None, Lit("0"), False, ""]))])
    else:
        value = O([("validityPeriod", rng.choice([O(), O([("start", "2026-01-01")]), None, []]))])
    set_key_in(rng.choice(orders), key, value)
    return True


def m_prior_reference(rng, root):
    orders = [o for o in objects(root) if has_key(o, "medicationCodeableConcept")]
    if len(orders) < 2:
        return False
    target, source = rng.sample(orders, 2)
    ids = [v for k, v in target if k == "id" and isinstance(v, str)]
    if not ids:
        return False
    set_key_in(source, "priorPrescription", O([("reference", "MedicationRequest/" + ids[0])]))
    return True


def m_drug_concept(rng, root):
    hits = pairs_with_keys(root, ("medicationCodeableConcept",))
    concepts = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not concepts:
        return False
    concept = rng.choice(concepts)
    roll = rng.random()
    if roll < 0.35:
        set_key_in(concept, "text", rng.choice(DRUG_NAMES))
    elif roll < 0.5:
        concept[:] = [(k, v) for k, v in concept if k != "text"]
    elif roll < 0.8:
        set_key_in(concept, "coding", [O([("display", rng.choice(DRUG_NAMES))])])
    else:
        set_key_in(concept, "coding", [O([("display", rng.choice(DRUG_NAMES))]),
                                       O([("display", rng.choice(DRUG_NAMES))])])
    return True


def m_free_text(rng, root):
    if rng.random() < 0.5:
        targets = [o for o in objects(root) if has_key(o, "doseAndRate") or has_key(o, "timing")]
        key = rng.choice(["text", "additionalInstruction", "patientInstruction"])
    else:
        targets = [o for o in objects(root) if has_key(o, "medicationCodeableConcept")]
        key = "note"
    if not targets:
        return False
    set_key_in(rng.choice(targets), key, rng.choice(["Hold until your doctor restarts", "", None, [],
                                                     "Take 2 tablets", "x", True]))
    return True


def m_validity(rng, root):
    targets = [o for o in objects(root) if has_key(o, "medicationCodeableConcept")]
    if not targets:
        return False
    value = rng.choice([O([("validityPeriod", O([("end", "2026-12-31")]))]),
                        O([("validityPeriod", O([("start", "2026-01-01")]))]),
                        O([("validityPeriod", O())]), O([("validityPeriod", None)])])
    set_key_in(rng.choice(targets), "dispenseRequest", value)
    return True


def m_bundle_wrap(rng, root):
    orders = [v for k, v in root if k == "medicationRequests"] if isinstance(root, O) else []
    if not orders or not isinstance(orders[0], list):
        return False
    entries = [O([("resource", clone(order))]) for order in orders[0]]
    if rng.random() < 0.5:
        entries.insert(0, O([("resource", O([("resourceType", "Patient"), ("id", "pat1")]))]))
    set_key_in(root, "bundle", O([("resourceType", "Bundle"), ("type", "searchset"), ("entry", entries)]))
    if rng.random() < 0.6:
        root[:] = [(k, v) for k, v in root if k != "medicationRequests"]
    return True


def m_bundle_type(rng, root):
    bundles = [obj[i][1] for obj, i in pairs_with_keys(root, ("bundle",)) if isinstance(obj[i][1], O)]
    if not bundles:
        return False
    bundle = rng.choice(bundles)
    set_key_in(bundle, "type", rng.choice(["searchset", "collection", "document", "transaction", None,
                                           Lit("1"), "Searchset", ""]))
    return True


def m_entry_request(rng, root):
    entries = [v for obj, i in pairs_with_keys(root, ("entry",)) for v in [obj[i][1]]
               if isinstance(v, list) and v and isinstance(v[0], O)]
    if not entries:
        return False
    entry = rng.choice(rng.choice(entries))
    if isinstance(entry, O):
        set_key_in(entry, "request", rng.choice([O([("method", "POST")]), None, "x"]))
    return True


def m_bundle_shape(rng, root):
    if rng.random() < 0.5:
        return False
    set_key_in(root, "bundle", rng.choice([[], "x", O([("entry", None)]), O([("entry", [])]),
                                           O([("entry", Lit("1"))]), None]))
    return True


def m_reserved_key(rng, root):
    if rng.random() < 0.8:
        return False
    obj = rng.choice(objects(root))
    obj.insert(rng.randint(0, len(obj)), (rng.choice(RESERVED_KEYS), random_value(rng)))
    return True


def m_nest(rng, root):
    inner = Lit("1")
    for _ in range(rng.choice([10, 62, 63, 64, 65, 70])):
        inner = O([("n", inner)]) if rng.random() < 0.7 else [inner]
    set_key_in(rng.choice(objects(root)), "deep", inner)
    return True


def m_many_numbers(rng, root):
    set_key_in(root, "pad", [Lit("1")] * rng.choice([1000, 19990, 20001]))
    return True


def m_escape_key(rng, root):
    hits = [(o, i) for o in objects(root) for i, (k, _) in enumerate(o)
            if not isinstance(k, EK) and k and k.isascii()]
    if not hits:
        return False
    obj, i = rng.choice(hits)
    obj[i] = (EK(obj[i][0]), obj[i][1])
    return True


def m_reorder(rng, root):
    objs = [o for o in objects(root) if len(o) > 1]
    if not objs:
        return False
    rng.shuffle(rng.choice(objs))
    return True


def m_duplicate_entry(rng, root):
    lists = [v for o in objects(root) for k, v in o if k in ("medicationRequests", "entry")
             and isinstance(v, list) and v]
    if not lists:
        return False
    chosen = rng.choice(lists)
    chosen.append(clone(rng.choice(chosen)))
    return True


def m_order_id(rng, root):
    hits = pairs_with_keys(root, ("id",))
    if not hits:
        return False
    obj, i = rng.choice(hits)
    obj[i] = ("id", rng.choice(ID_VALUES))
    return True


def root_value(root, key):
    for k, v in root:
        if k == key:
            return v
    return None


def m_output_noise(rng, root):
    text = root_value(root, "output")
    if not isinstance(text, str):
        return False
    position = rng.randint(0, len(text))
    set_key_in(root, "output", text[:position] + rng.choice(NOISE) + text[position:])
    return True


def m_output_retarget(rng, root):
    text = root_value(root, "output")
    if not isinstance(text, str):
        return False
    set_key_in(root, "output", text.replace(rng.choice(["m1", "m2", "m3"]), rng.choice(ID_EXTRA), 1))
    return True


def m_output_long(rng, root):
    if rng.random() < 0.7:
        return False
    set_key_in(root, "output", rng.choice(["a" * 65537, "{{drug:m1}} " * 401]))
    return True


MUTATIONS = [
    ("drop_pair", m_drop_pair), ("drop_known_key", m_drop_known_key), ("duplicate_pair", m_duplicate_pair),
    ("add_key", m_add_key), ("retype_value", m_retype_value), ("string_edge", m_string_edge),
    ("number_edge", m_number_edge), ("number_respell", m_number_respell), ("status", m_status),
    ("intent", m_intent), ("do_not_perform", m_do_not_perform), ("as_needed", m_as_needed),
    ("subject", m_subject), ("patient", m_patient), ("resource_type", m_resource_type),
    ("dose_unit", m_dose_unit), ("unit_pair", m_unit_pair), ("quantity_system", m_quantity_system),
    ("route", m_route), ("route_text", m_route_text), ("timing_repeat", m_timing_repeat),
    ("timing_fail_key", m_timing_fail), ("dosage_count", m_dosage_count), ("dose_and_rate", m_dose_and_rate),
    ("rate_keys", m_rate_keys), ("dosage_keys", m_dosage_keys), ("timing_extension", m_timing_extension),
    ("order_extension", m_order_extension), ("prior_reference", m_prior_reference),
    ("drug_concept", m_drug_concept), ("free_text", m_free_text), ("validity", m_validity),
    ("bundle_wrap", m_bundle_wrap), ("bundle_type", m_bundle_type), ("entry_request", m_entry_request),
    ("bundle_shape", m_bundle_shape), ("nest_depth", m_nest), ("many_numbers", m_many_numbers),
    ("escape_key", m_escape_key), ("reorder_keys", m_reorder), ("duplicate_entry", m_duplicate_entry),
    ("order_id", m_order_id), ("output_noise", m_output_noise), ("output_retarget", m_output_retarget),
    ("output_long", m_output_long), ("reserved_key", m_reserved_key),
]


def raw_edit(rng, text):
    position = rng.randrange(len(text) + 1)
    operation = rng.randrange(3)
    char = rng.choice(RAW_CHARS)
    if operation == 0 and position < len(text):
        return text[:position] + text[position + 1:]
    if operation == 1:
        return text[:position] + char + text[position:]
    if position < len(text):
        return text[:position] + char + text[position + 1:]
    return text


def make_output(rng, ids):
    if rng.random() < 0.3:
        return " ".join(rng.choice(VALUE_TEMPLATES[:2]).replace("ID", i) for i in ids)
    parts = []
    free_ids = list(ids)
    rng.shuffle(free_ids)
    for _ in range(rng.randint(1, 3)):
        if free_ids and rng.random() < 0.85:
            target = free_ids.pop()
        else:
            target = rng.choice(ID_EXTRA)
        pool = VALUE_TEMPLATES if rng.random() < 0.8 else TEMPLATES
        parts.append(rng.choice(pool).replace("ID", target))
    return " ".join(parts)


def load_pools():
    cases = []
    for line in CASES.read_text(encoding="utf-8").splitlines():
        record = json.loads(line, parse_int=Lit, parse_float=Lit)
        orders = record.get("medicationRequests")
        if isinstance(orders, list) and orders:
            cases.append(orders)
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"), parse_int=Lit, parse_float=Lit)
    resources = [entry["resource"] for entry in bundle["entry"] if "resource" in entry]
    orders = [r for r in resources if r.get("resourceType") == "MedicationRequest"]
    return cases, orders


def make_request(rng, pools):
    cases, bundle_orders = pools
    if rng.random() < 0.7:
        source = rng.choice(cases)
        chosen = rng.sample(source, rng.randint(1, min(4, len(source))))
    else:
        chosen = rng.sample(bundle_orders, rng.randint(1, min(4, len(bundle_orders))))
    orders = [to_o(order) for order in chosen]
    for i, order in enumerate(orders):
        if rng.random() < 0.9:
            set_key_in(order, "id", f"m{i + 1}")
        if not has_key(order, "subject") and rng.random() < 0.9:
            order.append(("subject", O([("reference", "Patient/pat1")])))
    ids = [v for order in orders for k, v in order if k == "id"]
    style = rng.random()
    if style < 0.65:
        root = O([("medicationRequests", orders)])
    elif style < 0.85:
        entries = [O([("resource", O([("resourceType", "Patient"), ("id", "pat1")]))])]
        entries += [O([("resource", order)]) for order in orders]
        root = O([("bundle", O([("resourceType", "Bundle"), ("type", "searchset"), ("entry", entries)]))])
    else:
        root = O([("bundle", O([("entry", [O([("resource", order)]) for order in orders])]))])
    if rng.random() < 0.25:
        root.append(("patient", "pat1"))
    root.append(("output", make_output(rng, ids)))
    kinds = []
    for _ in range(rng.choice([0, 0, 0, 1, 1, 1, 2, 2, 3])):
        name, mutate = rng.choice(MUTATIONS)
        if mutate(rng, root):
            kinds.append(name)
    ascii_only = rng.random() < 0.7
    spaced = rng.random() < 0.15
    sep = (", ", ": ") if spaced else (",", ":")
    if not ascii_only:
        kinds.append("raw_unicode")
    if spaced:
        kinds.append("whitespace")
    text = dump(root, ascii_only, sep)
    if rng.random() < 0.02:
        text = " " * rng.randint(1, 3) + text + "\t"
        kinds.append("outer_whitespace")
    if rng.random() < 0.03:
        text = raw_edit(rng, text)
        kinds.append("raw_edit")
    return text, kinds


def layer_replies(binary, lines):
    data = ("\n".join(lines) + "\n").encode("utf-8")
    proc = subprocess.run([str(binary), "serve"], input=data, capture_output=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f"{binary} serve exited {proc.returncode}: {proc.stderr.decode('utf-8', 'replace')}")
    replies = proc.stdout.decode("utf-8").split("\n")
    if replies and replies[-1] == "":
        replies.pop()
    return replies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--core", choices=sorted(CORES), default="v2")
    parser.add_argument("--pre-merge", action="store_true")
    parser.add_argument("--examples", type=int, default=0)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    pools = load_pools()
    requests = []
    while len(requests) < args.count:
        text, kinds = make_request(rng, pools)
        if text.strip(" \t\r\n"):
            requests.append((text, kinds))
    lines = [text for text, _ in requests]
    replies = layer_replies(args.binary, lines)
    if len(replies) != len(lines):
        print(f"layer returned {len(replies)} replies for {len(lines)} requests")
        return 1

    kind_counts = Counter(kind for _, kinds in requests for kind in kinds)
    outcomes = Counter()
    reasons = Counter()
    explained = Counter()
    unexplained = Counter()
    examples = defaultdict(list)
    agreed = 0
    for (text, _), raw in zip(requests, replies):
        reply = json.loads(raw)
        prediction = predict(text, args.core)
        outcomes[prediction[0]] += 1
        reasons[key_of_prediction(prediction)] += 1
        if agrees(prediction, reply):
            agreed += 1
            continue
        key = f"{key_of_prediction(prediction)} | {key_of_reply(reply)}"
        if args.pre_merge and args.core == "v2" and agrees(predict(text, "v1"), reply):
            explained[key] += 1
            label = "v1 core still in binary"
        else:
            unexplained[key] += 1
            label = "UNEXPLAINED"
        if len(examples[key]) < max(args.examples, 1):
            examples[key].append((text, prediction, raw, label))

    print(f"requests run: {len(lines)}")
    print(f"distinct mutation kinds applied: {len(kind_counts)}")
    print(f"reference ({args.core}) outcomes: ok {outcomes['ok']}, blocked {outcomes['blocked']}, "
          f"error {outcomes['error']}")
    for key, count in reasons.most_common():
        print(f"  reference {key}: {count}")
    print(f"agreements: {agreed}")
    print(f"disagreements explained by the version 1 core in the binary: {sum(explained.values())} "
          f"in {len(explained)} keys")
    for key, count in explained.most_common():
        print(f"  [v1 core still in binary] {count} x {key}")
    print(f"unexplained disagreements: {sum(unexplained.values())} in {len(unexplained)} keys")
    for key, count in unexplained.most_common():
        print(f"  [UNEXPLAINED] {count} x {key}")
    if args.examples:
        for key in list(unexplained) + list(explained):
            for text, prediction, raw, label in examples[key]:
                print(f"    {label}: request: {text[:600]}")
                print(f"      reference: {prediction}")
                print(f"      layer: {raw[:400]}")
    return 1 if unexplained else 0


if __name__ == "__main__":
    sys.exit(main())
