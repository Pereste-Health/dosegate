import json, sys, urllib.request

URL = "https://rxnav.nlm.nih.gov/REST/allconcepts.json?tty=IN+PIN+MIN+BN"
VERSION_URL = "https://rxnav.nlm.nih.gov/REST/version.json"


def fetch(url):
    with urllib.request.urlopen(url, timeout=300) as r:
        return json.load(r)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "data/rxnorm_names.txt"
    version = fetch(VERSION_URL)
    concepts = fetch(URL)["minConceptGroup"]["minConcept"]
    names = sorted({c["name"].strip().lower() for c in concepts if c["name"].strip()})
    with open(out, "w") as f:
        for n in names:
            f.write(n + "\n")
    by_tty = {}
    for c in concepts:
        by_tty[c["tty"]] = by_tty.get(c["tty"], 0) + 1
    print("RxNorm release", version.get("version"), "RxNav API", version.get("apiVersion"))
    print("concepts", len(concepts), by_tty, "distinct lowercase names", len(names))


if __name__ == "__main__":
    main()
