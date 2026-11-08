#!/usr/bin/env python3
"""Differential fuzz test of the DoseGate reader and render checks.

A separate Python reference predicts each reply of `dosegate serve`. The
reference is written from the specification and FHIR R4, but it copies the route
and unit tables from the Lean source and encodes the same reader policy, so it
checks agreement with that policy, not with an outside standard. Realistic
orders and output templates are mutated, sent as one JSON request per line through
a single serve process, and each reply is compared with the prediction: the status,
and the reason for a block or the text for an ok. An error reply must be an error.

--core v2 (default) judges the binary against version 2.2, the current layer. Its shape rules
reject a wrong JSON type, an empty string, or an unknown key in a request, bundle, or bundle entry
wherever the reader would otherwise skip or default the value, and its version 2.2 rules refuse
nested bundles, medication event resources, and foreign subjects, fail closed on every text-bearing
order field the reader does not interpret, hold coding displays to a strength and dose-form grammar,
and print a drug name only when it is in the RxNorm lexicon (data/rxnorm_names.txt). The v1 core has
none of these rules.
--core v1 judges it against the layer before version 2 (no 2.1 or 2.2 rules).
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
STATUS_CODES = ("active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown")
INTENT_CODES = ("proposal", "plan", "order", "original-order", "reflex-order", "filler-order", "instance-order",
                "option")
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
COUNT_UNITS = {"tablet", "capsule", "puff", "drop"}
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
questions please thank thanks hello hi information read carefully what who how why""".split())
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

TEXT_CHARS_V1 = set(string.ascii_letters + string.digits + " \n.,;:!?()'\"-/")
TEXT_CHARS_V2 = set(string.ascii_letters + string.digits + " \n.,;:()'\"-/")
CORES = {
    "v1": {"vocab": VOCAB_V1, "total": TOTAL_WORDS_V1, "shapes": V1_SHAPES, "free_drug_slot": True,
           "related": "token", "ambiguity_all_fields": False, "name_rules": "v1", "hours_rule": False,
           "daily_needs_timing": False, "ambiguous_reason": "ambiguousDaily",
           "gate_2_1": False, "gate_2_2": False, "require_all": False, "text_chars": TEXT_CHARS_V1,
           "strict": False},
    "v2": {"vocab": VOCAB_V2, "total": TOTAL_WORDS_V2, "shapes": V2_SHAPES, "free_drug_slot": False,
           "related": "conservative", "ambiguity_all_fields": True, "name_rules": "v2", "hours_rule": True,
           "daily_needs_timing": True, "ambiguous_reason": "ambiguousDrug",
           "gate_2_1": True, "gate_2_2": True, "require_all": True, "text_chars": TEXT_CHARS_V2,
           "strict": True},
}
REQUEST_KEYS = ("output", "bundle", "medicationRequests", "patient")
BUNDLE_KEYS = ("resourceType", "id", "meta", "type", "timestamp", "total", "link", "entry")
ENTRY_KEYS = ("fullUrl", "resource", "search")
FHIR_R4_RESOURCE_TYPES = (
    "Account", "ActivityDefinition", "AdverseEvent", "AllergyIntolerance", "Appointment",
    "AppointmentResponse", "AuditEvent", "Basic", "Binary", "BiologicallyDerivedProduct",
    "BodyStructure", "Bundle", "CapabilityStatement", "CarePlan", "CareTeam", "CatalogEntry",
    "ChargeItem", "ChargeItemDefinition", "Claim", "ClaimResponse", "ClinicalImpression",
    "CodeSystem", "Communication", "CommunicationRequest", "CompartmentDefinition", "Composition",
    "ConceptMap", "Condition", "Consent", "Contract", "Coverage", "CoverageEligibilityRequest",
    "CoverageEligibilityResponse", "DetectedIssue", "Device", "DeviceDefinition", "DeviceMetric",
    "DeviceRequest", "DeviceUseStatement", "DiagnosticReport", "DocumentManifest",
    "DocumentReference", "EffectEvidenceSynthesis", "Encounter", "Endpoint", "EnrollmentRequest",
    "EnrollmentResponse", "EpisodeOfCare", "EventDefinition", "Evidence", "EvidenceVariable",
    "ExampleScenario", "ExplanationOfBenefit", "FamilyMemberHistory", "Flag", "Goal",
    "GraphDefinition", "Group", "GuidanceResponse", "HealthcareService", "ImagingStudy",
    "Immunization", "ImmunizationEvaluation", "ImmunizationRecommendation", "ImplementationGuide",
    "InsurancePlan", "Invoice", "Library", "Linkage", "List", "Location", "Measure",
    "MeasureReport", "Media", "Medication", "MedicationAdministration", "MedicationDispense",
    "MedicationKnowledge", "MedicationRequest", "MedicationStatement", "MedicinalProduct",
    "MedicinalProductAuthorization", "MedicinalProductContraindication",
    "MedicinalProductIndication", "MedicinalProductIngredient", "MedicinalProductInteraction",
    "MedicinalProductManufactured", "MedicinalProductPackaged", "MedicinalProductPharmaceutical",
    "MedicinalProductUndesirableEffect", "MessageDefinition", "MessageHeader", "MolecularSequence",
    "NamingSystem", "NutritionOrder", "Observation", "ObservationDefinition", "OperationDefinition",
    "OperationOutcome", "Organization", "OrganizationAffiliation", "Parameters", "Patient",
    "PaymentNotice", "PaymentReconciliation", "Person", "PlanDefinition", "Practitioner",
    "PractitionerRole", "Procedure", "Provenance", "Questionnaire", "QuestionnaireResponse",
    "RelatedPerson", "RequestGroup", "ResearchDefinition", "ResearchElementDefinition",
    "ResearchStudy", "ResearchSubject", "RiskAssessment", "RiskEvidenceSynthesis", "Schedule",
    "SearchParameter", "ServiceRequest", "Slot", "Specimen", "SpecimenDefinition",
    "StructureDefinition", "StructureMap", "Subscription", "Substance", "SubstancePolymer",
    "SubstanceProtein", "SubstanceReferenceInformation", "SubstanceSpecification",
    "SubstanceSourceMaterial", "SupplyDelivery", "SupplyRequest", "Task", "TerminologyCapabilities",
    "TestReport", "TestScript", "ValueSet", "VerificationResult", "VisionPrescription",
)
FHIR_PERIOD_UNITS = ("s", "min", "h", "d", "wk", "mo", "a")
PRIORITY_CODES = ("routine", "urgent", "asap", "stat")
LINK_RELATIONS = ("self", "next", "previous", "prev", "first", "last")
SEARCH_MODES = ("match", "include", "outcome")
EVENT_RESOURCE_TYPES = ("MedicationStatement", "MedicationDispense", "MedicationAdministration")
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
NDC = "http://hl7.org/fhir/sid/ndc"
ICD10CM = "http://hl7.org/fhir/sid/icd-10-cm"
ICD10 = "http://hl7.org/fhir/sid/icd-10"
CATEGORY_SYSTEM = "http://terminology.hl7.org/CodeSystem/medicationrequest-category"
COURSE_SYSTEM = "http://terminology.hl7.org/CodeSystem/medicationrequest-course-of-therapy"
US_CORE_PROFILE = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest"
REASON_SYSTEMS = (SNOMED, ICD10CM, ICD10)
MEDICATION_SYSTEMS = (RXNORM, NDC, SNOMED)
CATEGORY_TERMS = {"inpatient": "Inpatient", "outpatient": "Outpatient", "community": "Community",
                  "discharge": "Discharge"}
COURSE_TERMS = {"continuous": "Continuous long term therapy", "acute": "Short course (acute) therapy",
                "seasonal": "Seasonal"}
PROFILE_ALLOWLIST = (US_CORE_PROFILE, "http://hl7.org/fhir/StructureDefinition/MedicationRequest")
STRENGTH_UNITS = {"mg", "mcg", "ug", "g", "ml", "l", "u", "iu", "unit", "units", "unt"}
STRENGTH_DENOMINATORS = {"ml", "l", "g", "mg", "hr", "actuat"}
FORM_WORDS = set("""oral orally tablet tablets capsule capsules solution suspension injectable injection extended
release delayed chewable disintegrating film coated prefilled syringe pen injector auto cartridge inhaler inhalant
metered powder topical cream ointment gel lotion patch transdermal system nasal spray ophthalmic otic rectal
suppository sublingual lozenge granules packet liquid elixir syrup vaginal buccal enteric effervescent aerosol dry
vial ampule implant""".split())
REFERENCE_KEYS = ("subject", "encounter", "requester", "performer", "recorder")
REFERENCE_LIST_KEYS = ("reasonReference", "supportingInformation", "basedOn", "insurance", "eventHistory")
LEXICON = frozenset(line for line in (ROOT / "data/rxnorm_names.txt").read_text(encoding="utf-8").split("\n")
                    if line != "")
ASCII_ALNUM_CHARS = set(string.ascii_letters + string.digits)
DIGITS = set("0123456789")
DATE_TIME = re.compile(r"[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2}))?)?)?")
LANGUAGE = re.compile(r"[a-z]{2,3}(-[A-Z]{2})?")
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


def patient_id_of(ref, cfg):
    segs = ref.split("/")
    if ref.startswith("urn:uuid:"):
        ident = ref[len("urn:uuid:"):]
    elif len(segs) == 2 and segs[0] == "Patient":
        ident = segs[1]
    elif not cfg["gate_2_2"] and (ref.startswith("http://") or ref.startswith("https://")) and len(segs) >= 2 \
            and segs[-2] == "Patient":
        ident = segs[-1]
    else:
        return None
    if cfg["gate_2_2"]:
        return ident if fhir_id_ok(ident) else None
    if ident == "" or any(c in ident for c in "/?#"):
        return None
    return ident


def fhir_id_ok(s):
    return 0 < len(s) <= 64 and all(c in ASCII_ALNUM_CHARS or c in "-." for c in s)


def date_time_ok(s):
    return DATE_TIME.fullmatch(s) is not None


def language_ok(s):
    return LANGUAGE.fullmatch(s) is not None


def str_ok(ok):
    return lambda value: isinstance(value, str) and ok(value)


def is_boolean(value):
    return isinstance(value, bool)


def reference_ok(r):
    if r.startswith("urn:uuid:"):
        return fhir_id_ok(r[len("urn:uuid:"):])
    parts = r.split("/")
    return len(parts) == 2 and parts[0] in FHIR_R4_RESOURCE_TYPES and fhir_id_ok(parts[1])


def ref_obj_ok(j):
    return within(j, ("reference",)) and isinstance(j.get("reference"), str) and reference_ok(j["reference"])


def digits_only(s):
    return len(s) > 0 and all(c in DIGITS for c in s)


def icd_head_ok(a):
    return len(a) == 3 and a[0] in string.ascii_uppercase and a[1] in DIGITS \
        and (a[2] in DIGITS or a[2] in string.ascii_uppercase)


def icd_ok(code):
    parts = code.split(".")
    if len(parts) == 1:
        return icd_head_ok(parts[0])
    if len(parts) == 2:
        return icd_head_ok(parts[0]) and 1 <= len(parts[1]) <= 4 \
            and all(c in DIGITS or c in string.ascii_uppercase for c in parts[1])
    return False


def code_shape_ok(system, code):
    if system == SNOMED:
        return 6 <= len(code) <= 18 and digits_only(code)
    if system == RXNORM:
        return len(code) <= 8 and digits_only(code)
    if system == NDC:
        return 10 <= len(code) <= 13 and all(c in DIGITS or c == "-" for c in code)
    if system in (ICD10CM, ICD10):
        return icd_ok(code)
    if system == CATEGORY_SYSTEM:
        return code in CATEGORY_TERMS
    if system == COURSE_SYSTEM:
        return code in COURSE_TERMS
    return False


def displays_for(system, code):
    if system == CATEGORY_SYSTEM:
        return [CATEGORY_TERMS[code]] if code in CATEGORY_TERMS else []
    if system == COURSE_SYSTEM:
        return [COURSE_TERMS[code]] if code in COURSE_TERMS else []
    return []


def coded_coding_ok(systems, c):
    if not within(c, ("system", "code", "display", "userSelected")):
        return False
    system, code = c.get("system"), c.get("code")
    if not (isinstance(system, str) and isinstance(code, str)):
        return False
    if system not in systems or not code_shape_ok(system, code):
        return False
    display = c.get("display")
    if display is not None and not (isinstance(display, str)
                                    and any(same_text(display, d) for d in displays_for(system, code))):
        return False
    return field_ok(c, "userSelected", is_boolean)


def coded_concept_ok(systems, cc):
    return within(cc, ("coding",)) and field_ok(cc, "coding", list_of(lambda c: coded_coding_ok(systems, c)))


def profile_ok(p):
    if not isinstance(p, str):
        return False
    for a in PROFILE_ALLOWLIST:
        if p == a:
            return True
        if p.startswith(a + "|"):
            v = p[len(a) + 1:]
            if v != "" and all(c in DIGITS or c == "." for c in v):
                return True
    return False


def meta_ok(m):
    return within(m, ("versionId", "lastUpdated", "profile", "security")) \
        and field_ok(m, "versionId", str_ok(fhir_id_ok)) and field_ok(m, "lastUpdated", str_ok(date_time_ok)) \
        and field_ok(m, "profile", list_of(profile_ok)) and not non_empty(m.get("security"))


def dispense_quantity_ok(q):
    if not (quantity_ok_shape(q) and within(q, ("value", "unit", "code", "system")) and quantity_ok(q)):
        return False
    code, unit = q.get("code"), q.get("unit")
    if isinstance(code, str):
        return code in UNIT_OF_CODE
    if isinstance(unit, str):
        return unit in UNIT_OF_CODE
    return True


def dispense_ok(d):
    return within(d, ("numberOfRepeatsAllowed", "quantity")) and field_ok(d, "numberOfRepeatsAllowed", is_whole) \
        and field_ok(d, "quantity", dispense_quantity_ok)


def substitution_ok(s):
    return within(s, ("allowedBoolean",)) and field_ok(s, "allowedBoolean", is_boolean)


def number_tok(t):
    return t != "" and all(c in DIGITS or c == "." for c in t) and t[0] in DIGITS and t[-1] in DIGITS \
        and t.count(".") <= 1


def unit_tok(t):
    parts = t.split("/")
    if len(parts) == 1:
        return ascii_lower(parts[0]) in STRENGTH_UNITS
    if len(parts) == 2:
        return ascii_lower(parts[0]) in STRENGTH_UNITS and ascii_lower(parts[1]) in STRENGTH_DENOMINATORS
    return False


def form_tok(t):
    return all(ascii_lower(w) in FORM_WORDS for w in t.split("-"))


def remainder_tok(t):
    return number_tok(t) or unit_tok(t) or form_tok(t)


def in_lexicon(name):
    return ascii_lower(trim(name)) in LEXICON


def bracket_ok(b):
    return b.startswith("[") and b.endswith("]") and in_lexicon(b[1:-1])


def remainder_ok(r):
    parts = r.split("[")
    if len(parts) == 1:
        body, brand = parts[0], None
    elif len(parts) == 2:
        body, brand = parts[0], "[" + parts[1]
    else:
        body, brand = "", ""
    return all(remainder_tok(t) for t in body.split(" ") if t != "") and (brand is None or bracket_ok(brand))


def display_matches(t, d):
    tl, dl = ascii_lower(trim(t)), ascii_lower(trim(d))
    if not dl.startswith(tl):
        return False
    rest = dl[len(tl):]
    if rest and rest[0] in string.ascii_letters:
        return False
    return remainder_ok(rest)


def med_coding_ok(c):
    if not within(c, ("system", "code", "display", "userSelected")):
        return False
    system, code = c.get("system"), c.get("code")
    if system is None and code is None:
        ok = True
    elif isinstance(system, str) and isinstance(code, str):
        ok = system in MEDICATION_SYSTEMS and code_shape_ok(system, code)
    else:
        ok = False
    return ok and field_ok(c, "userSelected", is_boolean)


def displays_of(cc):
    codings = cc.get("coding")
    out = []
    for coding in codings if isinstance(codings, list) else []:
        if isinstance(coding, dict) and isinstance(coding.get("display"), str):
            d = trim(coding["display"])
            if d:
                out.append(d)
    return out


def concept_named(cc):
    if not within(cc, ("text", "coding")):
        return ("", False)
    codings = cc.get("coding")
    codings = codings if isinstance(codings, list) else []
    codings_ok = all(med_coding_ok(c) for c in codings)
    text = cc.get("text")
    if isinstance(text, str):
        t = trim(text)
        if t == "":
            return ("", False)
        ok = codings_ok and all(display_matches(t, c["display"]) for c in codings
                                if isinstance(c, dict) and isinstance(c.get("display"), str))
        return (t if ok and in_lexicon(t) else "", ok)
    displays = displays_of(cc)
    if not displays:
        return ("", False)
    d = displays[0]
    ok = codings_ok and all(same_text(x, d) for x in displays[1:]) and all(in_lexicon(x) for x in displays)
    return (d if ok else "", ok)


def medication_entries(request):
    bundle = request.get("bundle")
    out = []
    if isinstance(bundle, dict):
        entries = bundle.get("entry")
        for e in entries if isinstance(entries, list) else []:
            if not isinstance(e, dict):
                continue
            r = e.get("resource")
            if isinstance(r, dict) and r.get("resourceType") == "Medication":
                full = e.get("fullUrl")
                out.append((full if isinstance(full, str) else None, r))
    return out


def medication_resource_ok(r):
    return within(r, ("resourceType", "id", "meta", "code", "status")) \
        and field_ok(r, "status", lambda v: v == "active") and field_ok(r, "meta", meta_ok) \
        and isinstance(r.get("code"), dict)


def resolve_medication(meds, ref):
    if ref.startswith("Medication/"):
        ident = ref[len("Medication/"):]
        hits = [m for m in meds if isinstance(m[1].get("id"), str) and m[1]["id"] == ident]
    else:
        hits = [m for m in meds if m[0] == ref]
    if len(hits) != 1:
        return None
    r = hits[0][1]
    return r.get("code") if medication_resource_ok(r) else None


def order_concept(meds, order):
    cc, ref = order.get("medicationCodeableConcept"), order.get("medicationReference")
    if cc is not None and ref is None:
        return cc
    if cc is None and ref is not None:
        if not ref_obj_ok(ref):
            return None
        return resolve_medication(meds, ref["reference"])
    return None


def medication_named(meds, order):
    cc = order_concept(meds, order)
    if cc is None or not concept_ok(cc):
        return ("", False)
    return concept_named(cc)


def route_codings_known(route):
    codings = route.get("coding") if isinstance(route, dict) else None
    for c in codings if isinstance(codings, list) else []:
        if not (isinstance(c, dict) and c.get("system") == SNOMED and isinstance(c.get("code"), str)
                and c["code"] in ROUTE_PHRASE and field_ok(c, "userSelected", is_boolean)):
            return False
    return True


def closed_fields(order):
    if any(present(order, k) for k in ("statusReason", "identifier", "groupIdentifier", "instantiatesUri",
                                        "instantiatesCanonical", "implicitRules")):
        return True
    if not field_ok(order, "reasonCode", list_of(lambda cc: coded_concept_ok(REASON_SYSTEMS, cc))):
        return True
    if not field_ok(order, "category", list_of(lambda cc: coded_concept_ok((CATEGORY_SYSTEM,), cc))):
        return True
    if not field_ok(order, "performerType", lambda cc: coded_concept_ok((SNOMED,), cc)):
        return True
    if not field_ok(order, "priority", str_ok(lambda v: v in PRIORITY_CODES)):
        return True
    if not field_ok(order, "language", str_ok(language_ok)):
        return True
    if not field_ok(order, "authoredOn", str_ok(date_time_ok)):
        return True
    if not field_ok(order, "meta", meta_ok):
        return True
    if not field_ok(order, "dispenseRequest", dispense_ok):
        return True
    if not field_ok(order, "substitution", substitution_ok):
        return True
    if not all(field_ok(order, k, ref_obj_ok) for k in REFERENCE_KEYS):
        return True
    if not all(field_ok(order, k, list_of(ref_obj_ok)) for k in REFERENCE_LIST_KEYS):
        return True
    return False


def is_active(order, patient, cfg):
    if order.get("status") != "active":
        return False
    intent = order.get("intent")
    if not (isinstance(intent, str) and intent in ORDER_INTENTS):
        return False
    not_performed = order.get("doNotPerform")
    if not_performed is not None and not_performed is not False:
        return False
    if patient is not None and patient_id_of(subject_ref(order), cfg) != patient:
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
    if key is None or key in COUNT_UNITS:
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


def has_extension_key(value):
    if isinstance(value, dict):
        return any(key in ("extension", "modifierExtension") or has_extension_key(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(has_extension_key(item) for item in value)
    return False


def within(value, allowed):
    return isinstance(value, dict) and set(value) <= set(allowed)


def optional_within(value, allowed):
    return value is None or within(value, allowed)


DOSAGE_KEYS = ("timing", "route", "doseAndRate", "asNeededBoolean", "sequence", "text",
               "additionalInstruction", "patientInstruction")
CODING_KEYS = ("system", "code", "display", "userSelected")
ORDER_KEYS = ("resourceType", "id", "meta", "implicitRules", "language", "identifier", "status", "intent",
              "category", "priority", "doNotPerform", "reportedBoolean", "reportedReference",
              "medicationCodeableConcept", "medicationReference", "subject", "encounter",
              "supportingInformation", "authoredOn", "requester", "performer", "performerType", "recorder",
              "reasonCode", "reasonReference", "instantiatesCanonical", "instantiatesUri", "basedOn",
              "groupIdentifier", "insurance", "dispenseRequest", "substitution", "eventHistory",
              "dosageInstruction", "note", "courseOfTherapyType", "priorPrescription")


def dosage_keys_ok(dosage):
    if not within(dosage, DOSAGE_KEYS):
        return False
    timing = dosage.get("timing")
    if not optional_within(timing, ("repeat", "code")):
        return False
    if isinstance(timing, dict) and not optional_within(timing.get("repeat"), ("frequency", "period", "periodUnit")):
        return False
    route = dosage.get("route")
    if not optional_within(route, ("coding", "text")):
        return False
    if isinstance(route, dict) and isinstance(route.get("coding"), list) and \
            not all(within(coding, CODING_KEYS) for coding in route["coding"]):
        return False
    rates = dosage.get("doseAndRate")
    for rate in rates if isinstance(rates, list) else []:
        if not within(rate, ("doseQuantity",)):
            return False
        if not optional_within(rate.get("doseQuantity"), ("value", "unit", "code", "system")):
            return False
    return True


def course_of_therapy_ok(order, cfg):
    course = order.get("courseOfTherapyType")
    if course is None:
        return True
    if cfg["gate_2_2"] and not coded_concept_ok((COURSE_SYSTEM,), course):
        return False
    codings = course.get("coding") if isinstance(course, dict) else None
    return isinstance(codings, list) and len(codings) > 0 and \
        all(isinstance(coding, dict) and coding.get("code") == "continuous" for coding in codings)


def reported_by_other(order):
    return order.get("reportedBoolean") is True or "reportedReference" in order


def order_closed(order, oid, refs, cfg):
    if cfg["gate_2_1"]:
        if has_extension_key(order) or not within(order, ORDER_KEYS) or present(order, "priorPrescription") \
                or not course_of_therapy_ok(order, cfg) or reported_by_other(order):
            return True
        if cfg["gate_2_2"] and closed_fields(order):
            return True
    else:
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


def dosage_closed(dosage, cfg):
    if cfg["gate_2_1"]:
        if any(present(dosage, k) for k in ("site", "method")):
            return True
    else:
        if any(present(dosage, k) for k in ("extension", "modifierExtension", "site", "method")):
            return True
        if any(present(dosage.get("timing"), k) for k in ("extension", "modifierExtension")):
            return True
        if any(present(dosage.get("route"), k) for k in ("extension", "modifierExtension")):
            return True
    route = dosage.get("route")
    if isinstance(route, dict) and not route_texts_ok(route):
        return True
    if cfg["gate_2_2"] and route is not None and not route_codings_known(route):
        return True
    rates = dosage.get("doseAndRate")
    first = rates[0] if isinstance(rates, list) and rates else None
    if isinstance(first, dict):
        extension_keys = () if cfg["gate_2_1"] else ("extension", "modifierExtension")
        if any(present(first, k) for k in extension_keys + ("rateQuantity", "rateRatio", "rateRange", "type")):
            return True
        quantity = first.get("doseQuantity")
        if isinstance(quantity, dict) and not quantity_ok(quantity):
            return True
    if cfg["gate_2_1"] and not dosage_keys_ok(dosage):
        return True
    return False


def free_text_closed(order, dosage):
    return any(present(dosage, k) for k in ("text", "additionalInstruction", "patientInstruction")) or \
        present(order, "note")


def build_order(order, patient, refs, meds, cfg):
    if cfg["gate_2_2"]:
        name, named_ok = medication_named(meds, order)
    else:
        name, named_ok = drug_of(order), True
    built = {"id": order["id"], "active": is_active(order, patient, cfg), "drug": name,
             "dose": None, "timing": None, "route": None, "as_needed": False}
    dosages = order.get("dosageInstruction")
    if not isinstance(dosages, list) or len(dosages) != 1 or not isinstance(dosages[0], dict):
        return built
    dosage = dosages[0]
    if fails_closed(dosage) or order_closed(order, order["id"], refs, cfg) or dosage_closed(dosage, cfg) \
            or not named_ok or free_text_closed(order, dosage):
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
    if any(c not in cfg["text_chars"] for c in text):
        return "disallowedCharacter"
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


def ends_sign(text):
    run = []
    for c in reversed(text):
        if c in ASCII_ALNUM:
            break
        run.append(c)
    return any(c in "-+" for c in run)


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
    if cfg["gate_2_1"] and any(segs[i][0] == "text" and ends_sign(segs[i][1])
                               and segs[i + 1][0] == "slot" for i in range(len(segs) - 1)):
        return ("blocked", "signBeforeSlot")
    if cfg["require_all"] and any(
            built["active"] and not any(seg[0] == "slot" and seg[1] != "drug" and seg[2] == built["id"]
                                        for seg in segs)
            for built in chart):
        return ("blocked", "omittedOrder")
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
    if cfg["require_all"] and not any(built["active"] for built in chart):
        return ("blocked", "noActiveOrder")
    return ("ok", "".join(pieces))


def is_text(value):
    return isinstance(value, str) and trim(value) != ""


def is_number(value):
    return isinstance(value, Decimal)


def is_whole(value):
    return isinstance(value, Decimal) and value >= 0 and value == value.to_integral_value()


def field_ok(obj, key, ok):
    value = obj.get(key)
    return value is None or ok(value)


def list_of(ok):
    return lambda value: isinstance(value, list) and all(ok(item) for item in value)


def keys_allowed(obj, allowed):
    return all(key in allowed or obj[key] is None for key in obj)


def code_ok(coding):
    return isinstance(coding, dict) and all(field_ok(coding, k, is_text) for k in ("system", "code", "display"))


def concept_ok(concept):
    return isinstance(concept, dict) and field_ok(concept, "text", is_text) \
        and field_ok(concept, "coding", list_of(code_ok))


def quantity_ok_shape(quantity):
    return isinstance(quantity, dict) and all(field_ok(quantity, k, ok) for k, ok in (
        ("value", is_number), ("unit", is_text), ("code", is_text), ("system", is_text)))


def rate_ok(rate):
    return isinstance(rate, dict) and field_ok(rate, "doseQuantity", quantity_ok_shape)


def timing_ok(timing):
    if not isinstance(timing, dict):
        return False
    repeat = timing.get("repeat")
    if repeat is None:
        return True
    return isinstance(repeat, dict) and field_ok(repeat, "frequency", is_whole) \
        and field_ok(repeat, "period", is_whole) \
        and field_ok(repeat, "periodUnit", lambda u: isinstance(u, str) and u in FHIR_PERIOD_UNITS)


def dosage_ok(dosage):
    return isinstance(dosage, dict) and field_ok(dosage, "timing", timing_ok) \
        and field_ok(dosage, "route", concept_ok) and field_ok(dosage, "doseAndRate", list_of(rate_ok)) \
        and field_ok(dosage, "asNeededBoolean", lambda v: isinstance(v, bool)) \
        and field_ok(dosage, "sequence", is_whole)


def order_ok(order):
    return field_ok(order, "resourceType", lambda v: v == "MedicationRequest") \
        and field_ok(order, "doNotPerform", lambda v: isinstance(v, bool)) \
        and field_ok(order, "reportedBoolean", lambda v: isinstance(v, bool)) \
        and (order.get("medicationCodeableConcept") is not None or order.get("medicationReference") is not None) \
        and field_ok(order, "medicationCodeableConcept", concept_ok) \
        and field_ok(order, "dosageInstruction", list_of(dosage_ok)) \
        and field_ok(order, "dispenseRequest", lambda v: isinstance(v, dict)) \
        and field_ok(order, "meta", lambda v: isinstance(v, dict))


def resource_type_ok(resource):
    t = resource["resourceType"]
    return t in FHIR_R4_RESOURCE_TYPES and t != "Bundle" and t not in EVENT_RESOURCE_TYPES


def url_char(c):
    return c not in " \t\r\n" and c not in '"<>'


def full_url_ok(s):
    return 0 < len(s) <= 512 and all(url_char(c) for c in s) \
        and (s.startswith("urn:uuid:") or s.startswith("http://") or s.startswith("https://"))


def search_ok(s):
    return isinstance(s, dict) and within(s, ("mode", "score")) \
        and field_ok(s, "mode", str_ok(lambda v: v in SEARCH_MODES)) and field_ok(s, "score", is_number)


def entry_ok(entry):
    return isinstance(entry, dict) and keys_allowed(entry, ENTRY_KEYS) \
        and field_ok(entry, "fullUrl", str_ok(full_url_ok)) and field_ok(entry, "search", search_ok) \
        and isinstance(entry.get("resource"), dict) and is_text(entry["resource"].get("resourceType")) \
        and resource_type_ok(entry["resource"])


def link_ok(l):
    return isinstance(l, dict) and within(l, ("relation", "url")) \
        and isinstance(l.get("relation"), str) and l["relation"] in LINK_RELATIONS \
        and isinstance(l.get("url"), str) and (l["url"].startswith("http://") or l["url"].startswith("https://")) \
        and all(url_char(c) for c in l["url"])


def bundle_meta_ok(m):
    return isinstance(m, dict) and within(m, ("versionId", "lastUpdated")) \
        and field_ok(m, "versionId", str_ok(fhir_id_ok)) and field_ok(m, "lastUpdated", str_ok(date_time_ok))


def bundle_ok(bundle):
    return keys_allowed(bundle, BUNDLE_KEYS) and field_ok(bundle, "resourceType", lambda v: v == "Bundle") \
        and field_ok(bundle, "id", str_ok(fhir_id_ok)) and field_ok(bundle, "meta", bundle_meta_ok) \
        and field_ok(bundle, "timestamp", str_ok(date_time_ok)) and field_ok(bundle, "total", is_whole) \
        and field_ok(bundle, "link", list_of(link_ok)) \
        and all(entry_ok(entry) for entry in bundle["entry"])


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
    if cfg["gate_2_1"] and request.get("bundle") is not None and request.get("medicationRequests") is not None:
        return ("error",)
    if cfg["strict"] and not keys_allowed(request, REQUEST_KEYS):
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
        if cfg["strict"] and not bundle_ok(bundle):
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
    if cfg["strict"] and not all(is_text(order["id"]) and order_ok(order) for order in orders):
        return ("error",)
    if cfg["gate_2_2"] and not all(fhir_id_ok(order["id"]) for order in orders):
        return ("error",)
    patient = request.get("patient")
    if patient is not None and (not isinstance(patient, str) or patient == ""):
        return ("error",)
    refs = [subject_ref(order) for order in orders]
    if None in refs:
        return ("error",)
    if cfg["gate_2_2"]:
        if any(ref.startswith("http://") or ref.startswith("https://") for ref in refs):
            return ("error",)
        if any(patient_id_of(ref, cfg) is None for ref in refs):
            return ("error",)
        if len(set(refs)) > 1:
            return ("error",)
        if patient is not None and refs and patient_id_of(refs[0], cfg) != patient:
            return ("error",)
    elif patient is None and len(set(refs)) > 1:
        return ("error",)
    if any(order.get("status") not in STATUS_CODES or order.get("intent") not in INTENT_CODES for order in orders):
        return ("error",)
    if patient is not None and any(patient_id_of(ref, cfg) is None for ref in refs):
        return ("error",)
    if len(orders) > MAX_ORDERS:
        return ("error",)
    prior = {order["priorPrescription"]["reference"] for order in orders
             if isinstance(order.get("priorPrescription"), dict)
             and isinstance(order["priorPrescription"].get("reference"), str)}
    meds = medication_entries(request) if cfg["gate_2_2"] else []
    chart = [build_order(order, patient, prior, meds, cfg) for order in orders]
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
REPORTED_BOOLEAN_VALUES = [True, True, False, None, "yes", Lit("1")]
REPORTED_REFERENCE_VALUES = [O([("reference", "Patient/pat1")]), O([("reference", "RelatedPerson/rp1")]), None,
                             "Patient/pat1"]
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
         "take", "Take", "tablet", "every", "which", "daily", "about", "or", "ask", "?", "!", "-", "+"]
ROUTE_CODES = [code for code, _ in ROUTE_TERMS]
ROUTE_TEXT_VALUES = ["by mouth", "Oral route", "ORAL USE", "Oral use", "under the tongue", "Sublingual route", "",
                     " by mouth ", None, 5, "Oral", "oral route", "into a vein", "Intravenous route"]
TIMING_FAIL_KEYS = ["code", "frequencyMax", "periodMax", "duration", "durationMax", "durationUnit", "countMax",
                    "boundsDuration", "boundsRange", "boundsPeriod", "count", "offset", "dayOfWeek", "timeOfDay",
                    "when"]
ADD_KEYS = ["note", "text", "additionalInstruction", "patientInstruction", "doNotPerform", "asNeededBoolean",
            "maxDosePerPeriod", "asNeededCodeableConcept", "comparator", "doseRange", "dispenseRequest", "code",
            "timing", "repeat", "extra", "status", "intent", "boundsRange", "frequencyMax", "count", "when",
            "periodMax", "durationUnit", "subject", "id", "resourceType", "patient", "pad2", "x", "meta",
            "priorPrescription", "extension", "modifierExtension", "site", "method", "rateQuantity", "type",
            "system", "unit", "code", "request", "courseOfTherapyType", "sequence", "event"]
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
    "Take {{drug:ID}} -{{dose:ID}} {{route:ID}} {{frequency:ID}}.",
    "Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}}, which is -{{daily:ID}}.",
    "Take {{drug:ID}} +{{dose:ID}} {{route:ID}} {{frequency:ID}}.",
    "- Take {{drug:ID}} {{dose:ID}} {{route:ID}} {{frequency:ID}}!",
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


def m_reported(rng, root):
    orders = order_nodes(root)
    if not orders:
        return False
    if rng.random() < 0.5:
        key, values = "reportedBoolean", REPORTED_BOOLEAN_VALUES
    else:
        key, values = "reportedReference", REPORTED_REFERENCE_VALUES
    set_key_in(rng.choice(orders), key, rng.choice(values))
    return True


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


ORDER_KEYS_ALLOWED_EXTRA = ["identifier", "category", "authoredOn", "requester", "reasonCode", "encounter",
                            "priority", "basedOn", "reasonReference", "performer", "recorder", "note", "meta",
                            "insurance", "groupIdentifier", "supportingInformation", "instantiatesUri",
                            "language", "implicitRules"]
ORDER_KEYS_NOT_ALLOWED = ["statusReason", "detectedIssue", "text", "contained", "patientInstruction",
                          "instruction", "reason", "dose", "route", "timing", "frequency", "sig", "daily",
                          "explanation", "comment", "unknownKey"]


def order_nodes(root):
    return [node for node in objects(root)
            if has_key(node, "medicationCodeableConcept") or has_key(node, "dosageInstruction")
            or has_key(node, "status") or has_key(node, "intent")]


def add_order_key(rng, root, names):
    if rng.random() < 0.85:
        return False
    orders = order_nodes(root)
    if not orders:
        return False
    obj = rng.choice(orders)
    fresh = [name for name in names if not has_key(obj, name)]
    if not fresh:
        return False
    obj.insert(rng.randint(0, len(obj)), (rng.choice(fresh), random_value(rng)))
    return True


def m_order_allowed_key(rng, root):
    return add_order_key(rng, root, ORDER_KEYS_ALLOWED_EXTRA)


def m_order_disallowed_key(rng, root):
    return add_order_key(rng, root, ORDER_KEYS_NOT_ALLOWED)


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


REASON_CODE_VALUES = [
    [O([("text", "Hold if INR above 3")])],
    [O([("coding", [O([("system", SNOMED), ("code", "44054006")])])])],
    [O([("coding", [O([("system", SNOMED), ("code", "44054006"), ("display", "Diabetes mellitus type 2")])])])],
    [O([("coding", [O([("system", ICD10CM), ("code", "E11.9")])])])],
    [O([("coding", [O([("system", ICD10CM), ("code", "e11.9")])])])],
    [O([("coding", [O([("system", ICD10), ("code", "I10")])])])],
    [O([("coding", [O([("system", "http://example.org/reasons"), ("code", "x1")])])])],
    [O([("coding", [O([("system", SNOMED), ("code", "4405")])])])],
    [O([("coding", "Hold if INR above 3")])],
    [O([("coding", [O([("system", SNOMED), ("code", "44054006"), ("userSelected", True)])])])],
    [O([("coding", [O([("system", SNOMED), ("code", "44054006"), ("version", "2")])])])],
    [O([("coding", [O([("system", SNOMED), ("code", "44054006")]), O([("text", "taper")])])])],
    [], None, "sliding scale", [O()], [O([("text", None)])], O([("text", "x")]),
]
TEXT_CHANNEL_VALUES = [
    ("identifier", [O([("system", "urn:example:orders"), ("value", "123")])]),
    ("identifier", [O([("value", "prednisone-taper-step-3-of-4")])]), ("identifier", []), ("identifier", None),
    ("groupIdentifier", O([("value", "g1")])),
    ("instantiatesUri", ["https://protocols.example.org/insulin-lispro-sliding-scale"]),
    ("instantiatesCanonical", ["PlanDefinition/p1"]), ("instantiatesUri", None),
    ("statusReason", O([("text", "Discontinued due to adverse reaction")])),
    ("statusReason", O([("coding", [O([("system", SNOMED), ("code", "182840001")])])])),
    ("implicitRules", "http://example.org/rules"), ("note", [O([("text", "hold")])]),
]
PRIORITY_VALUES = ["routine", "urgent", "asap", "stat", "high", "Stat", None, Lit("1"), ""]
LANGUAGE_VALUES = ["en", "en-US", "es", "fra", "english", "EN", "en-us", "en-US-x", "", None, Lit("1")]
AUTHORED_VALUES = ["2026-01-05", "2026-01-05T10:00:00Z", "2026-01-05T10:00:00.123+05:00", "2026-01", "2026",
                   "Jan 5 2026", "2026-1-5", "2026-01-05T10:00", "20260105", "2026-01-05 10:00:00", "", None,
                   Lit("2026"), "2026-01-05T10:00:00", "2026-01-05T10:00:00.Z", "2026-01-05T"]
CATEGORY_VALUES = [
    [O([("coding", [O([("system", CATEGORY_SYSTEM), ("code", "community")])])])],
    [O([("coding", [O([("system", CATEGORY_SYSTEM), ("code", "community"), ("display", "Community")])])])],
    [O([("coding", [O([("system", CATEGORY_SYSTEM), ("code", "community"), ("display", "community ")])])])],
    [O([("coding", [O([("system", CATEGORY_SYSTEM), ("code", "community"), ("display", "Hold")])])])],
    [O([("text", "outpatient")])], [O([("coding", [O([("system", CATEGORY_SYSTEM), ("code", "home")])])])],
    [O([("coding", [O([("code", "community")])])])], [], None, O([("coding", [])]), [O([("coding", [])])],
]
PERFORMER_TYPE_VALUES = [
    O([("coding", [O([("system", SNOMED), ("code", "158965000")])])]), O([("text", "nurse")]),
    O([("coding", [O([("system", SNOMED), ("code", "158965000"), ("display", "Medical practitioner")])])]), None,
]
REF_VALUES = [
    O([("reference", "Practitioner/pr1")]), O([("reference", "Practitioner/pr1"), ("display", "Dr. Hold Warfarin")]),
    O([("reference", "urn:uuid:3f2a0c1e-5b7d-4e8f-9a1b-2c3d4e5f6a7b")]), O([("reference", "Practitioner/")]),
    O([("reference", "https://other.example/fhir/Practitioner/pr1")]), O([("reference", "Practitioner/pr 1")]),
    O([("display", "Dr. X")]), O([("identifier", O([("value", "1")]))]),
    O([("reference", "Practitioner/pr1"), ("type", "Practitioner")]), O([("reference", "Condition/c1")]),
    O([("reference", "practitioner/pr1")]), O(), "Practitioner/pr1", None, O([("reference", "Patient/pat1")]),
    O([("reference", "urn:uuid:")]), O([("reference", "Practitioner/pr1/_history/1")]),
]
META_VALUES = [
    O([("versionId", "1")]), O([("lastUpdated", "2026-01-05T10:00:00Z")]), O([("profile", [US_CORE_PROFILE])]),
    O([("profile", [US_CORE_PROFILE + "|6.1.0"])]), O([("profile", [US_CORE_PROFILE + "|"])]),
    O([("profile", ["http://example.org/StructureDefinition/hold-if-inr-above-3"])]), O([("profile", US_CORE_PROFILE)]),
    O([("tag", [O([("system", "http://example.org"), ("code", "x")])])]), O([("source", "http://example.org/x")]),
    O([("security", [])]), O([("security", [O([("code", "R")])])]), O([("versionId", "a b")]),
    O([("lastUpdated", "yesterday")]), O(), None, O([("versionId", Lit("1"))]), O([("tag", [])]),
]
DISPENSE_VALUES = [
    O([("quantity", O([("value", Lit("30")), ("unit", "tablet")]))]),
    O([("quantity", O([("value", Lit("30")), ("unit", "tablet"), ("code", "{tbl}"), ("system", UCUM)]))]),
    O([("numberOfRepeatsAllowed", Lit("3"))]), O([("numberOfRepeatsAllowed", Lit("1.5"))]),
    O([("expectedSupplyDuration", O([("value", Lit("6")), ("unit", "days")]))]),
    O([("quantity", O([("value", Lit("21")), ("unit", "tablets, taper as directed")]))]),
    O([("quantity", O([("value", "30")]))]), O([("quantity", O([("value", Lit("30")), ("code", "mg")]))]),
    O([("quantity", O([("value", Lit("30")), ("unit", "mg"), ("code", "{tbl}")]))]),
    O([("performer", O([("reference", "Organization/o1")]))]), O([("initialFill", O())]),
    O([("validityPeriod", O([("end", "2026-12-31")]))]), O([("quantity", O([("value", Lit("30")), ("unit", "Tablet")]))]),
    O(), None, O([("quantity", O([("value", Lit("30")), ("unit", "tablet"), ("comparator", "<")]))]),
    O([("quantity", O([("value", Lit("30")), ("code", "{tbl}"), ("system", "http://example.org/units")]))]),
    O([("quantity", O([("value", Lit("30")), ("unit", "tab"), ("code", "{tbl}")]))]),
]
SUBSTITUTION_VALUES = [O([("allowedBoolean", True)]), O([("allowedBoolean", False)]), O([("allowedBoolean", "yes")]),
                       O([("allowedCodeableConcept", O([("text", "generic")]))]),
                       O([("reason", O([("text", "formulary")]))]), O(), None]
COURSE_VALUES = [
    O([("coding", [O([("system", COURSE_SYSTEM), ("code", "continuous")])])]),
    O([("coding", [O([("system", COURSE_SYSTEM), ("code", "continuous"), ("display", "Continuous long term therapy")])])]),
    O([("coding", [O([("system", COURSE_SYSTEM), ("code", "continuous"), ("display", "Taper")])])]),
    O([("coding", [O([("code", "continuous")])])]), O([("coding", [O([("system", COURSE_SYSTEM), ("code", "acute")])])]),
    O([("text", "Short course, stop after 5 days")]), O([("coding", [])]), None,
]
SEQUENCE_VALUES = [Lit("1"), Lit("0"), Lit("2"), Lit("1.5"), Lit("-1"), "1", None, "hold", True]
DISPLAY_SUFFIXES = [
    "", " 10 MG Oral Tablet", " 100 UNT/ML Injectable Solution", " 100 UNT/ML Injectable Solution [Humalog]",
    " 500 MG Extended Release Oral Tablet", " 0.5 MG/ML Oral Solution", " 25 MCG/HR Transdermal System",
    " 5 MG Oral Tablet as needed for pain", " taper: 20 mg, then 10 mg", " sliding scale", "500 MG",
    " 1 % Topical Cream", " 4 MG Oral Tablet [Medrol Dosepak]", " 15 MG Weekly Oral Tablet",
    " Hydrochloride 500 MG Oral Tablet", " 10 MG Oral Tablet, hold if INR above 3", " 2.5 MG Oral Tablet [Coumadin]",
    " 10 MG Extended-Release Oral Tablet", " 10 mg oral tablet", "  10 MG  Oral Tablet", "\t10 MG Oral Tablet",
    " 10 MG Oral Tablet [", " 10 MG [a] [b]", " 1000 Oral Tablet", " MG Oral Tablet", " 10. MG", " 10 MG/",
    " 0.09 MG/ACTUAT Metered Dose Inhaler", " 20 MEQ Extended Release Oral Tablet", " 81 MG Chewable Tablet",
    " 100 UNT/ML Pen Injector", " 100 UNT/ML Prefilled Syringe", "x", " [Humalog]", " 10 MG Oral Tablet ",
]
LEXICON_NAMES = ["aspirin", "warfarin", "Warfarin", "insulin glargine", "Insulin Lispro", "metoprolol tartrate", "Lantus",
                 "Coumadin", "levothyroxine sodium", "lisinopril", "Metformin", "metformin hydrochloride", "acetaminophen",
                 "prednisone", "methotrexate", "heparin", "oxycodone", "methylprednisolone", "humalog"]
NON_LEXICON_NAMES = ["Warfarin Held", "insulin aspart", "regular insulin", "Prednisone tapered", "Methotrexate Mondays",
                     "Warfarin EOD", "Insulin lispro SlidingScale", "asa", "hctz", "warfarinn", "metformin  hydrochloride",
                     " aspirin ", "Heparin weight based", "insulin", "glargine", "Regular insulin SSI",
                     "Insulin Glargine Titrated", "clear days ahead", "fosamax plus d", "alocane max strength",
                     "Toprol-XL", "Toprol XL", "ASPIRIN", "aspirin ", "aspirin."]
MED_CODING_VALUES = [
    O([("system", RXNORM), ("code", "314076")]), O([("system", RXNORM), ("code", "314076a")]),
    O([("system", NDC), ("code", "0071-0155-23")]), O([("system", NDC), ("code", "0071")]),
    O([("system", SNOMED), ("code", "386873009")]), O([("system", "http://example.org/drugs"), ("code", "x")]),
    O([("code", "314076")]), O([("system", RXNORM)]), O([("system", RXNORM), ("code", "314076"), ("version", "2026")]),
    O([("system", RXNORM), ("code", "314076"), ("userSelected", True)]),
    O([("system", RXNORM), ("code", "314076"), ("userSelected", "yes")]), O(), O([("system", RXNORM), ("code", "")]),
]
SUBJECT_VARIANTS = ["https://other-hospital.example/fhir/Patient/pat1", "http://example.org/fhir/Patient/pat2",
                    "Patient/pat2", "Group/g1", "patient/pat1", "Patient/pat1/_history/2", "urn:uuid:pat1",
                    "Patient/pat 1", "Patient/PAT1", "Patient/pat1", "urn:uuid:", "Patient/", "pat1"]
BUNDLE_FIELD_VALUES = [
    ("id", "b1"), ("id", "b 1"), ("id", Lit("1")), ("meta", O([("lastUpdated", "2026-01-05T10:00:00Z")])),
    ("meta", O([("versionId", "2")])), ("meta", O([("profile", ["http://hl7.org/fhir/StructureDefinition/Bundle"])])),
    ("meta", O([("tag", [O([("code", "x")])])])), ("meta", O()), ("timestamp", "2026-01-05T10:00:00Z"),
    ("timestamp", "yesterday"), ("total", Lit("1")), ("total", Lit("1.5")), ("total", "1"),
    ("link", [O([("relation", "self"), ("url", "https://fhir.example.org/MedicationRequest?patient=pat1")])]),
    ("link", [O([("relation", "self"), ("url", "hold if INR above 3")])]),
    ("link", [O([("relation", "hold"), ("url", "https://fhir.example.org/x")])]),
    ("link", [O([("relation", "next"), ("url", "https://fhir.example.org/x"), ("extension", [])])]), ("link", []),
    ("link", O()), ("identifier", O([("value", "1")])), ("language", "en"), ("signature", O()), ("extension", []),
    ("implicitRules", "http://example.org/x"), ("type", "collection"),
]
ENTRY_FIELD_VALUES = [
    ("fullUrl", "urn:uuid:3f2a0c1e-5b7d-4e8f-9a1b-2c3d4e5f6a7b"), ("fullUrl", "https://fhir.example.org/MedicationRequest/m1"),
    ("fullUrl", "hold if INR above 3"), ("fullUrl", "m1"), ("fullUrl", ""), ("fullUrl", Lit("1")),
    ("search", O([("mode", "match")])), ("search", O([("mode", "match"), ("score", Lit("1"))])),
    ("search", O([("mode", "hold")])), ("search", O([("text", "x")])), ("search", O()), ("search", "match"),
    ("response", O([("status", "200")])), ("link", []), ("extension", []),
]
ROUTE_CODING_VARIANTS = [
    O([("system", SNOMED), ("code", "26643006"), ("userSelected", True)]),
    O([("system", SNOMED), ("code", "26643006"), ("userSelected", "yes")]),
    O([("system", SNOMED), ("code", "26643006"), ("version", "20230301")]),
    O([("system", RXNORM), ("code", "26643006")]), O([("system", SNOMED), ("code", "99999999")]),
    O([("system", SNOMED), ("code", "26643006"), ("display", "Oral route")]),
    O([("system", SNOMED), ("code", "26643006"), ("display", "by mouth, hold if vomiting")]),
]
EVENT_ENTRY_TYPES = ["MedicationStatement", "MedicationDispense", "MedicationAdministration", "Medication", "Condition",
                     "Patient", "Practitioner", "OperationOutcome", "Bundle"]


def set_order_key(rng, root, key, values):
    orders = order_nodes(root)
    if not orders:
        return False
    set_key_in(rng.choice(orders), key, clone(rng.choice(values)))
    return True


def m_reason_code(rng, root):
    return set_order_key(rng, root, "reasonCode", REASON_CODE_VALUES)


def m_text_channel(rng, root):
    orders = order_nodes(root)
    if not orders:
        return False
    key, value = rng.choice(TEXT_CHANNEL_VALUES)
    set_key_in(rng.choice(orders), key, clone(value))
    return True


def m_priority_language_date(rng, root):
    key, values = rng.choice([("priority", PRIORITY_VALUES), ("language", LANGUAGE_VALUES),
                              ("authoredOn", AUTHORED_VALUES)])
    return set_order_key(rng, root, key, values)


def m_category_performer(rng, root):
    key, values = rng.choice([("category", CATEGORY_VALUES), ("performerType", PERFORMER_TYPE_VALUES)])
    return set_order_key(rng, root, key, values)


def m_reference_field(rng, root):
    if rng.random() < 0.5:
        return set_order_key(rng, root, rng.choice(REFERENCE_KEYS), REF_VALUES)
    value = rng.choice(REF_VALUES)
    wrapped = [clone(value)] if rng.random() < 0.8 else value
    return set_order_key(rng, root, rng.choice(REFERENCE_LIST_KEYS), [wrapped])


def m_meta(rng, root):
    return set_order_key(rng, root, "meta", META_VALUES)


def m_dispense(rng, root):
    return set_order_key(rng, root, "dispenseRequest", DISPENSE_VALUES)


def m_substitution(rng, root):
    return set_order_key(rng, root, "substitution", SUBSTITUTION_VALUES)


def m_course_of_therapy(rng, root):
    return set_order_key(rng, root, "courseOfTherapyType", COURSE_VALUES)


def m_sequence(rng, root):
    targets = [o for o in objects(root) if has_key(o, "doseAndRate") or has_key(o, "timing")]
    if not targets:
        return False
    set_key_in(rng.choice(targets), "sequence", rng.choice(SEQUENCE_VALUES))
    return True


def m_display_remainder(rng, root):
    hits = pairs_with_keys(root, ("medicationCodeableConcept",))
    concepts = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not concepts:
        return False
    concept = rng.choice(concepts)
    name = rng.choice(LEXICON_NAMES)
    display = name + rng.choice(DISPLAY_SUFFIXES)
    coding = clone(rng.choice(MED_CODING_VALUES)) if rng.random() < 0.5 else O()
    coding.append(("display", display))
    codings = [coding]
    if rng.random() < 0.2:
        codings.append(O([("display", rng.choice([display, name, name + " 10 MG Oral Tablet"]))]))
    roll = rng.random()
    if roll < 0.7:
        set_key_in(concept, "text", name)
    elif roll < 0.85:
        concept[:] = [(k, v) for k, v in concept if k != "text"]
    else:
        set_key_in(concept, "text", rng.choice(["Insulin", "Met", name.upper(), name + " "]))
    set_key_in(concept, "coding", codings)
    return True


def m_lexicon_name(rng, root):
    hits = pairs_with_keys(root, ("medicationCodeableConcept",))
    concepts = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not concepts:
        return False
    concept = rng.choice(concepts)
    set_key_in(concept, "text", rng.choice(LEXICON_NAMES + NON_LEXICON_NAMES))
    if rng.random() < 0.3:
        set_key_in(concept, "coding", [clone(rng.choice(MED_CODING_VALUES))])
    return True


def bundle_of(root):
    bundles = [obj[i][1] for obj, i in pairs_with_keys(root, ("bundle",)) if isinstance(obj[i][1], O)]
    return bundles[0] if bundles else None


def entries_of(bundle):
    for k, v in bundle:
        if k == "entry" and isinstance(v, list):
            return v
    return None


def m_medication_reference(rng, root):
    if bundle_of(root) is None and not m_bundle_wrap(rng, root):
        return False
    bundle = bundle_of(root)
    entries = entries_of(bundle)
    orders = order_nodes(root)
    if entries is None or not orders:
        return False
    order = rng.choice(orders)
    name = rng.choice(LEXICON_NAMES + NON_LEXICON_NAMES[:6])
    ident = rng.choice(["med1", "med2", "med-1"])
    ref = rng.choice([f"Medication/{ident}", f"Medication/{ident}", f"urn:uuid:{ident}", "Medication/missing",
                      f"Medication/{ident}/_history/1", f"#{ident}"])
    reference = O([("reference", ref)])
    if rng.random() < 0.2:
        reference.append(("display", name + " 5 mg tablet"))
    if rng.random() < 0.75:
        order[:] = [(k, v) for k, v in order if k != "medicationCodeableConcept"]
    set_key_in(order, "medicationReference", reference)
    code = rng.choice([O([("text", name)]), O([("text", name), ("coding", [O([("system", RXNORM), ("code", "855332"),
                                                                             ("display", name)])])]),
                       O([("coding", [O([("system", RXNORM), ("code", "855332"), ("display", name)])])]),
                       O([("text", name + " 5 MG Oral Tablet")]), O()])
    medication = O([("resourceType", "Medication"), ("id", ident), ("code", code)])
    extra = rng.random()
    if extra < 0.15:
        medication.append(("status", rng.choice(["active", "inactive", "entered-in-error"])))
    elif extra < 0.25:
        medication.append(("form", O([("text", "tablet")])))
    elif extra < 0.3:
        medication.append(("meta", clone(rng.choice(META_VALUES))))
    elif extra < 0.35:
        medication[:] = [(k, v) for k, v in medication if k != "code"]
    entry = O([("resource", medication)])
    if rng.random() < 0.5:
        entry.insert(0, ("fullUrl", f"urn:uuid:{ident}"))
    entries.append(entry)
    if rng.random() < 0.1:
        entries.append(clone(entry))
    return True


def m_nested_bundle(rng, root):
    if bundle_of(root) is None and not m_bundle_wrap(rng, root):
        return False
    entries = entries_of(bundle_of(root))
    if not entries:
        return False
    i = rng.randrange(len(entries))
    inner = clone(entries[i])
    entries[i] = O([("resource", O([("resourceType", "Bundle"), ("type", "searchset"), ("entry", [inner])]))])
    return True


def m_event_resource(rng, root):
    if bundle_of(root) is None and not m_bundle_wrap(rng, root):
        return False
    entries = entries_of(bundle_of(root))
    if entries is None:
        return False
    kind = rng.choice(EVENT_ENTRY_TYPES)
    resource = O([("resourceType", kind), ("id", "r1"), ("status", "active")])
    if kind in ("MedicationStatement", "Medication"):
        resource.append(("medicationCodeableConcept" if kind == "MedicationStatement" else "code",
                         O([("text", "Ibuprofen")])))
    entries.insert(rng.randint(0, len(entries)), O([("resource", resource)]))
    return True


def m_subject_variant(rng, root):
    orders = order_nodes(root)
    if not orders:
        return False
    roll = rng.random()
    if roll < 0.7:
        set_key_in(rng.choice(orders), "subject", O([("reference", rng.choice(SUBJECT_VARIANTS))]))
    elif roll < 0.85:
        set_key_in(rng.choice(orders), "subject", O([("reference", "Patient/pat1"), ("display", "Pat Example")]))
    else:
        set_key_in(root, "patient", rng.choice(["pat1", "pat2", "PAT1"]))
    return True


def m_bundle_fields(rng, root):
    if bundle_of(root) is None and not m_bundle_wrap(rng, root):
        return False
    bundle = bundle_of(root)
    if rng.random() < 0.5:
        key, value = rng.choice(BUNDLE_FIELD_VALUES)
        set_key_in(bundle, key, clone(value))
        return True
    entries = entries_of(bundle)
    if not entries:
        return False
    entry = rng.choice(entries)
    if not isinstance(entry, O):
        return False
    key, value = rng.choice(ENTRY_FIELD_VALUES)
    set_key_in(entry, key, clone(value))
    return True


def m_route_coding(rng, root):
    hits = pairs_with_keys(root, ("route",))
    routes = [obj[i][1] for obj, i in hits if isinstance(obj[i][1], O)]
    if not routes:
        return False
    set_key_in(rng.choice(routes), "coding", [clone(rng.choice(ROUTE_CODING_VARIANTS))])
    return True


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
    ("intent", m_intent), ("do_not_perform", m_do_not_perform), ("reported", m_reported), ("as_needed", m_as_needed),
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
    ("order_allowed_key", m_order_allowed_key), ("order_disallowed_key", m_order_disallowed_key),
    ("reason_code", m_reason_code), ("text_channel", m_text_channel),
    ("priority_language_date", m_priority_language_date), ("category_performer", m_category_performer),
    ("reference_field", m_reference_field), ("meta", m_meta), ("dispense", m_dispense),
    ("substitution", m_substitution), ("course_of_therapy", m_course_of_therapy), ("sequence", m_sequence),
    ("display_remainder", m_display_remainder), ("lexicon_name", m_lexicon_name),
    ("medication_reference", m_medication_reference), ("nested_bundle", m_nested_bundle),
    ("event_resource", m_event_resource), ("subject_variant", m_subject_variant),
    ("bundle_fields", m_bundle_fields), ("route_coding", m_route_coding),
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
