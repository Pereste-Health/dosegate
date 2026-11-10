#!/usr/bin/env python3
"""Checks the approved number-only word list in data/prose_words.txt.

Usage: python3 tests/check_prose_words.py [BINARY]

The list must be sorted, unique, and lowercase ASCII letters. No word may be
number-like. The binary is the authority on number-like words: every listed word
is sent alone as a sentence through `serve --number-only`, and each must print.
No listed word may equal a one-word drug name in data/rxnorm_names.txt, and no
word from the excluded examples may appear in the list.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BINARY = ROOT / ".lake/build/bin/dosegate"

EXCLUDED = """
first second third last multiple various numerous plenty lot lots bit little large small big
high higher low strong stronger weak full whole part portion piece spoon spoonful cup glass bottle
pack handful pinch sixth tenth dozens pairs zero none same similar equal identical likewise ditto
match other others all both each too also dose doses dosage amount now soon later early late often
sometimes usually always never once up as some several few many much more less extra another
double single half quarter total enough change time times timing before after until when then
dos tres uno una cinco seis ocho nueve diez un une deux trois quatre cinq huit neuf dix
ein eins zwei drei vier funf sechs sieben acht neun zehn due tre
won ate tu fore tin
bd tds qds ods nocte mane gr lbs ct tabl
one two three four five six seven eight nine ten twice thrice dozen
""".split()


def fail(problems, message):
    problems.append(message)


def main():
    binary = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BINARY
    problems = []
    words = (ROOT / "data/prose_words.txt").read_text().split("\n")
    if words and words[-1] == "":
        words.pop()

    if words != sorted(set(words)):
        fail(problems, "the list is not sorted or has a repeated word")
    for w in words:
        if not re.fullmatch(r"[a-z]+", w):
            fail(problems, f"'{w}' is not lowercase ASCII letters")
        if len(w) == 1 and w not in ("a", "i"):
            fail(problems, f"'{w}' is a single letter other than a or i")

    rxnorm = {line.strip() for line in (ROOT / "data/rxnorm_names.txt").read_text().split("\n")
              if line.strip() and " " not in line.strip()}
    for w in words:
        if w in rxnorm:
            fail(problems, f"'{w}' is a one-word drug name in data/rxnorm_names.txt")

    excluded = set(EXCLUDED)
    for w in words:
        if w in excluded:
            fail(problems, f"'{w}' is on the excluded list")

    requests = "".join(json.dumps({"medicationRequests": [], "output": f"{w}."}) + "\n" for w in words)
    result = subprocess.run([str(binary), "serve", "--number-only"], input=requests,
                            capture_output=True, text=True)
    replies = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(replies) != len(words):
        fail(problems, f"expected {len(words)} replies, got {len(replies)}")
    for w, reply in zip(words, replies):
        if reply.get("status") != "ok":
            fail(problems, f"'{w}' is blocked in number-only mode: {reply.get('detail', reply)}")

    for problem in problems:
        print("  " + problem)
    print(f"prose words: {len(words)} listed, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
