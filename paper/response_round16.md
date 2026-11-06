# Response to the sixteenth round of review

Section names refer to paper/paper.md. The health literacy and math reviewers accepted the manuscript. The computer science reviewer asked for minor revision with two required items, and both are resolved below. The health literacy reviewer's five recommended items are also made.

## Computer science review

Required items:

- Tag and hash in the arXiv notes and the round 15 response: confirmed. The notes named commit 6685af2, which was the round 14 commit, while the tag named the round 15 commit, 1100662. A committed file cannot name its own commit hash, so the notes no longer name any hash. Step 4 of paper/arxiv_submission.md now says to run `git rev-parse v2.1.0^{}`, `git ls-remote origin 'refs/tags/v2.1.0^{}'`, and `git rev-parse origin/main` and to check that all three print the same hash, and that this commit holds the layer, the evaluation data, and the manuscript, which agrees with the Availability paragraph. The two statements in paper/response_round15.md that the tag named 6685af2 are corrected. The Availability paragraph keeps citing the tag and the `git ls-remote` command instead of a hash, for the same reason. The tag was moved to the final commit of each review round during review, before posting, and the notes say not to move it after posting.
- Drug names in the Abstract: confirmed. The Abstract now says the guarantee covers each drug name, dose, route, frequency, and daily total "filled from a slot", and that model words are limited to take, which, and 67 framing words "judged free of drug names", so the drug-name half of the claim is shown to rest on a judgment. In Table 1, the drug-name row now reads "none alone; supporting:" before the three theorems. The Conclusion already limits the guarantee to values "that the layer fills from a slot" and states the vocabulary judgment, so it is unchanged. To stay within 1,920 characters, the Abstract now says "between a model and the patient", "slots naming fields of a ... MedicationRequest; the layer fills them or blocks output", "a slot filter that checks only digits and units", and "version 2.1 blocks all 9". No number or caveat was removed. The Abstract is 1,914 characters and identical in paper/arxiv_submission.md.

## Health literacy review (accept)

Recommended items, all made:

- Regular insulin timing: the sentence now cites the Humulin R U-100 label for the 30-minute timing and tells the deployment to check the label for the product and concentration it dispenses, instead of stating the timing for all regular insulin.
- Insulin concentration: Exact quantities now gives the size of the difference: 20 units of U-500 contains as much insulin as 100 units of U-100 (wrong; corrected in the Round 21 note below).
- Same-ingredient pairs: "so they show the size of the harm" became "so a deployment that does not check for duplicate therapy would send them to patients".
- Superseded orders: Limits now says that a deployment using `--allow-omissions` must rewrite every priorPrescription reference to the exact form, or block any output that names a superseded order.
- Conclusion scope: the release range now says it is the share of slot outputs released after rewrites, on 120 normalized synthetic test cases, across three small open models.

## Math review (accept)

The recommended items are noted for a later revision. The proposed theorem `dailyDose_none_long`, which the reviewer compiled against DoseGate.Proofs, is not added in this round, so the theorem count stays at 200.

## Changes made

- paper/paper.md: Abstract, Table 1 drug-name row, Exact quantities, Limits (insulin timing, same-ingredient pairs, superseded orders), Conclusion.
- paper/arxiv_submission.md: Abstract (identical to paper.md, 1,914 characters) and step 4.
- paper/response_round15.md: two corrected statements about the tagged commit.

## Correction, round 21

The insulin sentence in Exact quantities that this section lists as made (the item on insulin concentration) says that 20 units of U-500 insulin contains as much insulin as 100 units of U-100. That is wrong. A unit is the same amount of insulin at either concentration, and only the volume differs: 20 units is 0.2 mL of U-100 and 0.04 mL of U-500. Round 21 replaces the sentences, and paper/response_round21.md gives the details.
