import collections, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
BIN = {"layer": [os.path.join(ROOT, ".lake/build/bin/dosegate"), "serve"],
       "baseline": [os.path.join(ROOT, ".lake/build/bin/dosegate-baseline")]}


def run(cmd, requests):
    p = subprocess.run(cmd, input="".join(json.dumps(json.loads(r)) + "\n" for r in requests),
                       capture_output=True, text=True)
    return [json.loads(l) for l in p.stdout.splitlines()]


def main():
    attacks = [json.loads(l) for l in open(os.path.join(DATA, "attacks.jsonl"))]
    reqs = [a["request"] for a in attacks]
    res = {k: run(v, reqs) for k, v in BIN.items()}
    out = []
    for a, l, b in zip(attacks, res["layer"], res["baseline"]):
        out.append({"id": a["id"], "round": a["round"], "class": a["class"], "layer": l, "baseline": b})
    with open(os.path.join(DATA, "attack_results.jsonl"), "w") as f:
        for o in out:
            f.write(json.dumps(o) + "\n")
    c = collections.Counter((o["layer"]["status"], o["baseline"]["status"]) for o in out)
    print("n", len(out))
    for k, v in sorted(c.items()):
        print("layer", k[0], "baseline", k[1], v)


if __name__ == "__main__":
    main()
