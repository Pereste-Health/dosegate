import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load(name):
    with open(os.path.join(ROOT, name)) as f:
        return json.load(f)


def misstates(records):
    return sum(1 for r in records if r["label"] == "misstates_order")


def note_has(record, text):
    return text in (record.get("relabel_note") or "")


dev = load("attack_labels.json")
h1 = load("heldout/labels_h1.json")
h2 = load("heldout2/labels_h2.json")
replay = load("replay_v21/labels.json")
review = load("v2_review/labels.json")

llama = [r for r in review if r["item"].startswith("bo|v2_llama3.2-3b|")]
llama_round18 = [r for r in llama if note_has(r, "Round 18")]
llama_round10 = [r for r in llama if r["label"] == "misstates_order" and r.get("third_reader_before_round10") == "faithful" and not note_has(r, "Round 18")]
t_round10 = [r for r in dev if r["filter"] == "baseline" and r.get("third_reader_before_round10") == "faithful" and r["label"] == "misstates_order"]
h1_round10 = [r for r in h1 if note_has(r, "round 10 labeling addendum")]
h2_round10 = [r for r in h2 if note_has(r, "round 10 labeling addendum")]
f05 = [r for r in dev if r["id"] == "F05"]

def filt(records, name):
    return [r for r in records if r["filter"] == name]

adopted = {
    "development version 1": misstates(filt(dev, "layer")),
    "development comparison": misstates(filt(dev, "baseline")),
    "round h1 version 1": misstates(filt(h1, "layer")),
    "round h1 comparison": misstates(filt(h1, "baseline")),
    "round h2 version 2": misstates(filt(h2, "layer")),
    "round h2 comparison": misstates(filt(h2, "baseline")),
    "Llama 3.2 3B comparison": misstates(llama),
}

print("Adopted misstatement counts")
for name, value in adopted.items():
    print(f"  {name}: {value}")

print("Round 10 addendum relabels")
print(f"  development comparison records: {len(t_round10)}")
print(f"  Llama 3.2 3B comparison records: {len(llama_round10)}")
print(f"  round h1 records relabeled to faithful: {sum(1 for r in h1_round10 if r['label'] == 'faithful')}")
print(f"  round h2 comparison records relabeled to misstates_order: {sum(1 for r in h2_round10 if r['label'] == 'misstates_order')}")

print("Round 18 clarification relabels (Llama 3.2 3B comparison)")
print(f"  records: {len(llama_round18)}")

print("F05 replay relabel")
print(f"  records: {len(f05)} (" + ", ".join(f"{r['filter']} {r['label']}" for r in f05) + ")")

print("Counts with every change reverted (protocol as written, F05 faithful)")
reverted = {
    "development version 1": misstates(filt(dev, "layer")) - 1,
    "development comparison": misstates(filt(dev, "baseline")) - 1 - len(t_round10),
    "round h1 version 1": misstates(filt(h1, "layer")) + sum(1 for r in h1_round10 if r["label"] == "faithful" and r["filter"] == "layer"),
    "round h1 comparison": misstates(filt(h1, "baseline")) + sum(1 for r in h1_round10 if r["label"] == "faithful" and r["filter"] == "baseline"),
    "round h2 version 2": misstates(filt(h2, "layer")),
    "round h2 comparison": misstates(filt(h2, "baseline")) - sum(1 for r in h2_round10 if r["label"] == "misstates_order"),
    "Llama 3.2 3B comparison": misstates(llama) - len(llama_round18) - len(llama_round10),
}
for name, value in reverted.items():
    print(f"  {name}: {value}")
