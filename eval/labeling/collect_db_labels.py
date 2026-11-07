import argparse
import datetime
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.dirname(HERE)
OUT = os.path.join(EVAL, "data", "human_labels", "parker_labels.json")
CATS = {"faithful", "misstates_order", "unsupported_claim"}


def records_from(obj):
    if isinstance(obj, list):
        for x in obj:
            yield from records_from(x)
    elif isinstance(obj, dict):
        if "item_id" in obj and "label" in obj:
            yield obj
        elif isinstance(obj.get("data"), dict):
            yield from records_from(obj["data"])
        elif isinstance(obj.get("labels"), list):
            yield from records_from(obj["labels"])
        else:
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    yield from records_from(v)


def main():
    ap = argparse.ArgumentParser(description="Collect label documents read back from the artifact database into the canonical label file.")
    ap.add_argument("sources", nargs="+", help="JSON files, or directories holding <collection>/<doc_id>.json files as ArtifactData's out_dir writes them")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--n-items", type=int, default=None)
    args = ap.parse_args()
    files = []
    for s in args.sources:
        files.extend(sorted(glob.glob(os.path.join(s, "**", "*.json"), recursive=True)) if os.path.isdir(s) else [s])
    by_id = {}
    for f in files:
        for r in records_from(json.load(open(f))):
            if r.get("label") not in CATS or not isinstance(r.get("item_id"), str):
                continue
            have = by_id.get(r["item_id"])
            if not have or (r.get("labeled_at") or "") > (have.get("labeled_at") or ""):
                by_id[r["item_id"]] = r
    rows = [by_id[k] for k in sorted(by_id)]
    manifest_path = os.path.join(HERE, "queue_manifest.json")
    n_items = args.n_items or (json.load(open(manifest_path))["n_items"] if os.path.exists(manifest_path) else len(rows))
    out = {"schema": "dosegate-human-labels-1", "labeler": "Parker Smith",
           "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "source": "artifact-db", "n_items": n_items, "n_labeled": len(rows), "labels": rows}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    print(f"{len(rows)} labels from {len(files)} files written to {args.out}")


if __name__ == "__main__":
    main()
