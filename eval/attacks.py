import collections, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
BINDIR = os.environ.get("BINDIR", os.path.join(ROOT, ".lake/build/bin"))
BIN = {"layer": [os.path.join(BINDIR, "dosegate"), "serve"],
       "baseline": [os.path.join(BINDIR, "dosegate-baseline")]}


RAW_NUMBER = re.compile(r'"\\u0000NUM(.*?)\\u0000NUM"')


def raw_numbers(request):
    return RAW_NUMBER.sub(lambda m: m.group(1), request)


def run(cmd, requests):
    p = subprocess.run(cmd, input="".join(r.replace("\r", " ").replace("\n", " ") + "\n" for r in requests),
                       capture_output=True, text=True)
    return [json.loads(l) for l in p.stdout.splitlines()]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DATA, "attacks.jsonl")
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DATA, "attack_results.jsonl")
    attacks = [json.loads(l) for l in open(src)]
    reqs = [raw_numbers(a["request"]) for a in attacks]
    res = {k: run(v, reqs) for k, v in BIN.items()}
    out = []
    for a, l, b in zip(attacks, res["layer"], res["baseline"]):
        out.append({"id": a["id"], "round": a["round"], "class": a["class"], "layer": l, "baseline": b})
    with open(dst, "w") as f:
        for o in out:
            f.write(json.dumps(o) + "\n")
    c = collections.Counter((o["layer"]["status"], o["baseline"]["status"]) for o in out)
    print("n", len(out))
    for k, v in sorted(c.items()):
        print("layer", k[0], "baseline", k[1], v)


if __name__ == "__main__":
    main()
