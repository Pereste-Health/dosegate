#!/usr/bin/env bash
# Rebuilds the DoseGate layer at the two pinned held-out commits, reruns the
# held-out corpora through both filters with the current eval/attacks.py, and
# compares each output with the stored results. Writes eval/data/pinned_reruns.json.
# Usage, from the repository root: bash eval/pinned_rerun.sh SCRATCH_DIR (from elsewhere, pass the full path to the script).
set -euo pipefail

SCRATCH=${1:?usage: bash eval/pinned_rerun.sh SCRATCH_DIR}
mkdir -p "$SCRATCH"
SCRATCH=$(cd "$SCRATCH" && pwd)
cd "$(dirname "$0")/.."

H1=59c5f32
H2=ef2cc98
OUT="$SCRATCH/out"
mkdir -p "$OUT"

for c in "$H1" "$H2"; do
    dir="$SCRATCH/$c"
    if [ -e "$dir" ]; then
        echo "$dir already exists; remove it before rerunning" >&2
        exit 1
    fi
    mkdir -p "$dir"
    git archive "$c" | tar -x -C "$dir"
    (cd "$dir" && lake build dosegate dosegate-baseline) > "$SCRATCH/build_$c.log" 2>&1
done

run_corpus () {
    local commit=$1 corpus=$2 tag=$3 f name
    for f in "$corpus"/*.jsonl; do
        case "$f" in *_results.jsonl) continue ;; esac
        name=$(basename "$f" .jsonl)
        BINDIR="$SCRATCH/$commit/.lake/build/bin" python3 eval/attacks.py "$f" "$OUT/${tag}_${name}_results.jsonl" > "$OUT/${tag}_${name}.log"
    done
}

run_corpus "$H1" eval/data/heldout h1
run_corpus "$H2" eval/data/heldout2 h2

python3 - "$OUT" "$H1" "$H2" <<'PY'
import glob, json, os, subprocess, sys

out, h1, h2 = sys.argv[1:4]
FIELDS = ("status", "text", "reason", "detail", "message")
SIDES = ("layer", "baseline")
PAPER = {"h1": (74, 104), "h2": (86, 128)}


def read(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


def releases(records, side):
    return sum(r[side]["status"] == "ok" for r in records)


report = {"fields_compared": [f"{s}.{f}" for s in SIDES for f in FIELDS], "rounds": {}}
for tag, version, commit, corpus in (("h1", 1, h1, "eval/data/heldout"), ("h2", 2, h2, "eval/data/heldout2")):
    sha = subprocess.run(["git", "rev-parse", commit], capture_output=True, text=True, check=True).stdout.strip()
    per_file, mismatches = {}, []
    totals = {"records": 0, "records_compared": 0, "layer_releases": 0, "baseline_releases": 0,
              "stored_layer_releases": 0, "stored_baseline_releases": 0}
    corpus_files = sorted(p for p in glob.glob(f"{corpus}/*.jsonl") if not p.endswith("_results.jsonl"))
    for path in corpus_files:
        name = os.path.basename(path)[: -len(".jsonl")]
        ids = [r["id"] for r in read(path)]
        rerun = read(os.path.join(out, f"{tag}_{name}_results.jsonl"))
        stored = read(os.path.join(corpus, f"{name}_results.jsonl"))
        rerun_by_id = {r["id"]: r for r in rerun}
        stored_by_id = {r["id"]: r for r in stored}
        compared, file_mismatches = 0, []
        for rid in ids:
            if rid not in rerun_by_id or rid not in stored_by_id:
                file_mismatches.append({"id": rid, "file": name, "differs": ["missing record"]})
                continue
            compared += 1
            differs = [f"{side}.{field}" for side in SIDES for field in FIELDS
                       if rerun_by_id[rid][side].get(field) != stored_by_id[rid][side].get(field)]
            if differs:
                file_mismatches.append({"id": rid, "file": name, "differs": differs})
        mismatches += file_mismatches
        per_file[name] = {
            "records": len(ids),
            "records_compared": compared,
            "layer_releases": releases(rerun, "layer"),
            "baseline_releases": releases(rerun, "baseline"),
            "stored_layer_releases": releases(stored, "layer"),
            "stored_baseline_releases": releases(stored, "baseline"),
            "mismatches": len(file_mismatches),
        }
        totals["records"] += len(ids)
        totals["records_compared"] += compared
        totals["layer_releases"] += releases(rerun, "layer")
        totals["baseline_releases"] += releases(rerun, "baseline")
        totals["stored_layer_releases"] += releases(stored, "layer")
        totals["stored_baseline_releases"] += releases(stored, "baseline")

    report["rounds"][tag] = {
        "version": version,
        "commit": sha,
        "corpus_files": corpus_files,
        **totals,
        "paper_layer_releases": PAPER[tag][0],
        "paper_baseline_releases": PAPER[tag][1],
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "per_file": per_file,
    }

with open("eval/data/pinned_reruns.json", "w") as f:
    json.dump(report, f, indent=2)
    f.write("\n")

for tag, r in report["rounds"].items():
    print(f"{tag} commit {r['commit'][:7]} records {r['records']} compared {r['records_compared']} "
          f"layer releases {r['layer_releases']} (paper {r['paper_layer_releases']}, stored {r['stored_layer_releases']}) "
          f"baseline releases {r['baseline_releases']} (paper {r['paper_baseline_releases']}, stored {r['stored_baseline_releases']}) "
          f"mismatches {r['mismatch_count']}")
    for m in r["mismatches"]:
        print("  ", m["id"], m["differs"])
PY
