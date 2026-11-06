# Response to the twenty-second round of review

Section names refer to paper/paper.md. The math reviewer accepted the manuscript. The health literacy and computer science reviewers asked for minor revision, with three required items in all. All three are resolved below. The author decided before this round to stop after it, so the recommended items are noted for a later revision and not made, with one exception that was checked because it concerned a citation.

## Health literacy review

Required items:

- Weekly methotrexate coded as seven times a day: made. The request h2_clinical_02 is released by version 2 (eval/data/heldout2/labels_h2.json, both labelers faithful) and by version 2.1 (eval/data/replay_v21/h2_results.jsonl) as "Take Methotrexate 15 mg by mouth 7 times a day." Limits, in the paragraph that begins "The layer prints the orders it receives, including chart errors", now reports the case, gives the daily amount the line would instruct (105 mg a day in place of 15 mg once a week), and says a deployment must check each order's timing against the drug's labeled schedule before calling the layer. The round h2 paragraph in Development now says that this request was released as written, and the Introduction lists a chart error such as weekly methotrexate coded as daily among the cases a deployment must handle.
- Conditional and taper orders in the Abstract and Introduction: made. The Abstract now reads "weekly, monthly, as-needed, conditional, and taper orders need a pharmacist check". To stay within the limit, it uses the reviewer's proposed shortenings: "not full directions", "(4 drugs)", "In 201 theorems", and "a judgment no proof checks". The Abstract is 1,918 characters by script and identical in paper/arxiv_submission.md. The Introduction now says that a conditional order prints as one fixed dose and that a taper written as two orders prints as two daily doses at once.

Recommended items (the "unrelated names" wording, the duplicated description of the temperature 1.0 samples, and the two as-needed round h2 lines): noted for a later revision.

## Computer science review

Required item:

- Tag and working tree: made. The theorem dailyDose_none_long, its line in tests/Axioms.lean, eval/label_change_counts.py, eval/vocab_rxnorm_check.py, and eval/data/vocab_rxnorm_check.json are committed with this revision, and tag v2.1.0 is moved to that commit, so the tagged tree holds the 201 theorems and the scripts the paper cites.

Recommended items: noted for a later revision. One was checked because it concerned a citation. The reviewer wrote that reference 3 gives the version 1 title. The arXiv record for 2606.04262 checked on November 6, 2026 gives the current version's title as "Can I Take Another Dose? DoseBench: Evaluating LLM Decision-Making in OTC Dosing QA", which is the title in reference 3, and gives "Can I Take Another Dose? Evaluating LLM Decision-Making Under Temporal Uncertainty in OTC Dosing QA" for version 1. Reference 3 is unchanged.

## Math review (accept)

The recommended items (the sweep's zero-conflict count holding by construction, naming the paired test as McNemar's exact test, the third-labeler decision behind one round h2 discordant request, and periods in days other than one in the "No daily total" row) are noted for a later revision.

## Changes made

- paper/paper.md: Abstract (1,918 characters), Introduction (conditional, taper, and chart-error cases), Development (round h2 methotrexate outcome), Limits (h2_clinical_02).
- paper/arxiv_submission.md: Abstract, identical to paper.md.
