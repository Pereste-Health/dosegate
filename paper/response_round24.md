# Response to the twenty-fourth round of review

Only the health literacy reviewer reviewed this round. The reviewer found the round 23 required item resolved and asked for minor revision with one new required item, the superseded-order paragraph in Limits. This revision makes that required item and three of the recommended items. Two recommended items are noted for a later revision.

## Health literacy review

Required item:

- Superseded orders: made, with corrections to the reviewer's proposed sentence. We tested each claim with the built binary on 73 requests. The main matrix has 48 render requests and 6 fallback requests. It uses two drug-name pairs (the same name, and two different names), three reference forms (the exact form `MedicationRequest/m1`, the history form `MedicationRequest/m1/_history/1`, and `urn:uuid:m1`), four outputs (naming only the superseded order, only the replacement, both, or neither), and the default settings and `--allow-omissions`. The other 19 requests are 6 controls with no priorPrescription, 12 requests with a superseded order whose status is completed or stopped, and 1 request with a superseded order that has its own priorPrescription. The reviewer's point that the default settings block every output for that patient holds. Three details were wrong and one was missing. A dose change closes the replacement order in every reference form, and it closes the superseded order only in the exact form. The fallback returns missingField, not ambiguousDrug, when the two drug names differ. Under `--allow-omissions`, the exact form blocks with missingField when the names differ, and the history and `urn:uuid` forms print the superseded order's old dose when the output names only that order and the names differ. The paragraph now states each result. The closure rule in Trusted code and the deployment rule were corrected to match. The README, Results, Design, and Conclusion do not state the old effect, so they did not change. The supplement does state it. Section S2 in `paper/dosegate_jamia.md` still lists a superseded order named by a history-form or `urn:uuid` reference as yielding no dose, and that file was not edited in this round (see Changes made).

Recommended items made in this revision:

- Unrelated names: made with the reviewer's wording. The sentence is in Results, under "What the patient sees when output is blocked," not in Limits as the review said. It now reads "Two orders whose names the rule does not relate, such as Lantus and insulin glargine, remain two lines, although they may be one drug, because the fallback does not check for duplicate therapy."
- Temperature 1.0 samples: the second description of the two samples is removed. The sentence now reads "The two temperature 1.0 slot samples per case used nucleus sampling (top-p 0.95) and were not rewritten." The reviewer's deletion of "and two slot samples at temperature 1.0" from the earlier list was not made, because that list gives the count of six generations per case. Without the phrase, the list would name four generations against a count of six. The count still agrees: six generations per case (four greedy generations and two temperature 1.0 samples), 720 first-attempt generations per model (120 cases times six), and 240 temperature 1.0 outputs per model in Table 3 (120 cases times two).
- As-needed lines: made. Limits now quotes two round-h2 released texts exactly as they appear in eval/data/replay_v21/h2_results.jsonl. Both are labeled faithful in eval/data/heldout2/labels_h2.json. The texts are h2_clinical_21, "Take Lantus 20 units as a shot under the skin once a day. Take Humalog 4 units as a shot under the skin three times a day as needed.", and h2_clinical_19, "Take Oxycodone 5 mg by mouth every 4 hours as needed."

Recommended items noted for a later revision:

- A consolidated list of the conditions under which a deployment must not show the fallback or model text. The conditions are spread across about eight paragraphs in Limits and Results, and writing the list needs a decision on how each item cites its paragraph.
- The framing sentences. Limits does not yet say that the framing wording is untested with patients. The sentence "Please ask your doctor and pharmacist your questions." is a form the default vocabulary allows, not a form tested for clarity.

## Changes made

- paper/paper.md, Specification and proofs, the Trusted code closure bullet: the bullet now says a priorPrescription closes the order in any reference form, and that the history and `urn:uuid` forms do not close the superseded order.
- paper/paper.md, Evaluation methods, Models and conditions: the sentence on the two temperature 1.0 samples now gives their sampling once.
- paper/paper.md, Results, What the patient sees when output is blocked: the sentence on Lantus and insulin glargine now says the two orders may be one drug.
- paper/paper.md, Limits, the superseded-order paragraph: the first sentences and the statement of the default and `--allow-omissions` results are rewritten. The deployment rule is corrected.
- paper/paper.md, Limits, the as-needed paragraph: two round-h2 released texts are quoted, with the pharmacist-review requirement.
- paper/dosegate_jamia.md, Supplementary Section S2, line 219: not changed. The file is outside this round's edit scope. The sentence should read "a `priorPrescription`, or is named by another order's `priorPrescription` reference that is exactly `MedicationRequest/<id>`," in place of "a `priorPrescription` or is named by one,". The round h1 table row at line 237 (exact form, default settings, omittedOrder) is still correct.

## Round 25 review

The health literacy reviewer confirmed the round 24 changes against the built binary and asked for minor revision with one required item. The author had decided to release after this review, so the required item and two precision points were made directly, and the other recommended items are noted for a later revision.

- Framing-only outputs under `--allow-omissions` (required): made. Design now says that the layer cannot stop a model from writing "Here is your medicine list." unasked and releases an output made only of framing sentences, so a deployment that uses the option must block or replace any output that names no order. It gives the usual dose-change record (superseded order stopped, replacement active with an exact priorPrescription reference) as a case where the patient would receive that sentence with no medicine named.
- Acetaminophen label wording: corrected. The label warns that most cases of liver injury occur at doses above 4,000 mg a day; the paper no longer says the label advises against that amount.
- Superseded orders: "Both orders stay active in every form" now applies only while the superseded order is active in the record.
