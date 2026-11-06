# Response to the nineteenth round of review

Section names refer to paper/paper.md. All three reviewers asked for minor revision. The four required items are resolved below, and the Abstract was rewritten as a whole so that every caveat earlier rounds required stays in it.

## Health literacy review

Required items:

- Abstract, weekly and as-needed lines and the one-ingredient pairs: made. The Abstract now says "Released lines are dose statements, not complete directions: weekly and as-needed lines need a pharmacist check, and wording is untested with patients", and it describes the 16 round-h2 releases as "a possible double dose found by one author and unchecked by clinicians". The reviewer proposed making room by deleting "(version 2 build)", "and by default no raw Synthea bundle gets output", and the protocol count for the first version. Earlier rounds required all three, so they are kept; the room comes from rewording the whole Abstract without removing any number or caveat. It is 1,917 characters and identical in paper/arxiv_submission.md.
- Reference 42, the Humulin R version: corrected after checking the DailyMed version history for set ID b519bd83-038c-4ec5-a231-a51ec5cc291f on November 6, 2026. The current label is SPL version 35, published September 7, 2026, and its text carries the revision stamp "Revised: 6/2023". That is the text that was read. The earlier sentence, that a later version dated September 7, 2026 was not read, was wrong, and the reviewer's date of June 16, 2026 does not appear in the version history either. Reference 42 now names version 35 and its revision stamp. The label contains both "approximately 30 minutes before meals" and "30 minutes before a meal", so the Limits wording is unchanged.

Recommended items made: the readability paragraph now says that a grade near 3 measures sentence and word length only and does not show that a patient understands mg, mL, mcg, or by mouth; the Abstract says "synthetic perturbed doses". The other recommended items are noted for a later revision.

## Math review

Required item:

- Two label states: confirmed. Two sentences written before the fifth round 18 relabel were left in place. The Labels paragraph now says that after the round 18 relabeling no match conflicts with the rule, and that the rerun sweep has 119 matches and no conflict with the adopted labels. The sentence calling Louetta798 perturbed an open decision is removed; its final label is misstates_order, as eval/data/v2_review/labels.json records.

## Computer science review

Required item:

- Drug names in the Abstract: made. The Abstract now states the vocabulary judgment as its own sentence: "That model words (take, which, and 67 framing words) hold no drug name is a judgment no theorem checks; --extra-words lifts that limit." The sentence before it claims proof only for values filled from a slot ("each drug name, dose, route, frequency, and daily total filled from a slot is the named order's value and appears only in that order's instruction"), which `render_fidelity`, `render_value_sentence`, and the completeness theorems establish.

## Changes made

- paper/paper.md: Abstract (rewritten, 1,917 characters), Labels (two stale sentences), Results (readability caveat), reference 42.
- paper/arxiv_submission.md: Abstract, identical to paper.md.
