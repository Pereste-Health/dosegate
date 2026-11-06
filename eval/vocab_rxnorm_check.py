import datetime
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKENS = ROOT / "DoseGate" / "Tokens.lean"
OUT = ROOT / "eval" / "data" / "vocab_rxnorm_check.json"
BASE = "https://rxnav.nlm.nih.gov/REST"
PAUSE_SECONDS = 0.1
SEARCH_MODE = 2
LISTS = [
    ("framing", "vocab"),
    ("shape", "instrWords"),
    ("shape", "totalWords"),
    ("name_stop", "nameStopWords"),
]
EXPECTED_COUNTS = {"vocab": 67, "nameStopWords": 77}
NOTES = [
    "The United States Pharmacopeia (USP) drug name list is not freely available, so the words were not checked against it. This check uses RxNorm only.",
    "Each hit is reported as RxNorm returns it. The script does not remove any word from DoseGate/Tokens.lean; the paper reports the hits and the authors' reading of them.",
    "A word is a hit when rxcui.json (name search with search=2, the normalized match this check requests) or drugs.json (name search) returns at least one RXCUI, the RxNorm concept identifier.",
    "Concept names and term types come from rxcui/<rxcui>/properties.json. Term types follow RxNorm, for example IN (ingredient), BN (brand name), SCD (clinical drug).",
]


def lean_string_list(text, name):
    match = re.search(rf"def {name} : List String :=\s*\[(.*?)\]", text, re.S)
    if match is None:
        raise SystemExit(f"{name} not found in {TOKENS}")
    return re.findall(r'"([^"]*)"', match.group(1))


def collect_words(text):
    words = {}
    counts = {}
    for group, name in LISTS:
        listed = lean_string_list(text, name)
        if name in EXPECTED_COUNTS and len(listed) != EXPECTED_COUNTS[name]:
            raise SystemExit(f"{name} has {len(listed)} words, expected {EXPECTED_COUNTS[name]}")
        counts[name] = {"group": group, "count": len(listed)}
        for word in listed:
            entry = words.setdefault(word, {"lean_lists": [], "groups": []})
            entry["lean_lists"].append(name)
            if group not in entry["groups"]:
                entry["groups"].append(group)
    return words, counts


def get_json(url):
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(1 + attempt)
    raise RuntimeError(f"{url}: {last_error}")


def query(path, params=None):
    url = f"{BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    time.sleep(PAUSE_SECONDS)
    return get_json(url)


def concept(rxcui, cache):
    if rxcui not in cache:
        props = query(f"rxcui/{rxcui}/properties.json").get("properties") or {}
        cache[rxcui] = {"rxcui": rxcui, "name": props.get("name"), "tty": props.get("tty")}
    return cache[rxcui]


def check_word(word, cache):
    record = {"word": word, "rxcui_json": [], "drugs_json": [], "concepts": [], "error": None}
    try:
        name_search = query("rxcui.json", {"name": word, "search": SEARCH_MODE})
        record["rxcui_json"] = list(dict.fromkeys(name_search.get("idGroup", {}).get("rxnormId") or []))
        drugs = query("drugs.json", {"name": word})
        record["drugs_json"] = list(dict.fromkeys(
            prop["rxcui"]
            for group in drugs.get("drugGroup", {}).get("conceptGroup") or []
            for prop in group.get("conceptProperties") or []
        ))
        for rxcui in dict.fromkeys(record["rxcui_json"] + record["drugs_json"]):
            found_by = []
            if rxcui in record["rxcui_json"]:
                found_by.append("rxcui.json")
            if rxcui in record["drugs_json"]:
                found_by.append("drugs.json")
            record["concepts"].append({**concept(rxcui, cache), "found_by": found_by})
    except RuntimeError as error:
        record["error"] = str(error)
    record["hit"] = bool(record["rxcui_json"] or record["drugs_json"]) and record["error"] is None
    return record


def main():
    words, lists = collect_words(TOKENS.read_text(encoding="utf-8"))
    version = query("version.json")
    cache = {}
    records = []
    for word, info in words.items():
        record = check_word(word, cache)
        record["groups"] = info["groups"]
        record["lean_lists"] = info["lean_lists"]
        records.append(record)
        status = "HIT" if record["hit"] else ("ERROR" if record["error"] else "none")
        print(f"{status:6} {word}", flush=True)

    hits = [r for r in records if r["hit"]]
    errors = [r for r in records if r["error"]]
    by_group = {}
    for group in ("framing", "shape", "name_stop"):
        group_records = [r for r in records if group in r["groups"]]
        by_group[group] = {
            "words_checked": len(group_records),
            "words_with_hit": sum(1 for r in group_records if r["hit"]),
            "words_with_error": sum(1 for r in group_records if r["error"]),
        }

    result = {
        "rxnorm_version": version.get("version"),
        "rxnav_api_version": version.get("apiVersion"),
        "access_date": datetime.date.today().isoformat(),
        "endpoints": [
            f"{BASE}/version.json",
            f"{BASE}/rxcui.json?name=<word>&search={SEARCH_MODE}",
            f"{BASE}/drugs.json?name=<word>",
            f"{BASE}/rxcui/<rxcui>/properties.json",
        ],
        "pause_seconds_between_requests": PAUSE_SECONDS,
        "source_file": "DoseGate/Tokens.lean",
        "lists": lists,
        "unique_words_checked": len(records),
        "counts": {
            "words_checked": len(records),
            "words_with_hit": len(hits),
            "words_without_hit": len(records) - len(hits) - len(errors),
            "words_with_error": len(errors),
            "words_hit_by_rxcui_json": sum(1 for r in records if r["rxcui_json"]),
            "words_hit_by_drugs_json": sum(1 for r in records if r["drugs_json"]),
            "distinct_rxcuis_in_hits": len({c["rxcui"] for r in hits for c in r["concepts"]}),
            "by_group": by_group,
        },
        "hits": [
            {
                "word": r["word"],
                "groups": r["groups"],
                "concepts": [
                    {"rxcui": c["rxcui"], "name": c["name"], "tty": c["tty"], "found_by": c["found_by"]}
                    for c in r["concepts"]
                ],
            }
            for r in hits
        ],
        "words": records,
        "notes": NOTES,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(result["counts"], indent=2))
    for hit in result["hits"]:
        names = "; ".join(f"{c['name']} ({c['tty']}, {c['rxcui']})" for c in hit["concepts"])
        print(f"HIT {hit['word']}: {names}")


if __name__ == "__main__":
    main()
