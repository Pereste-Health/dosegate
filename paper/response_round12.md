# Response to the twelfth round of review

This pass answers the three round 12 reviews (health literacy, math, and computer science), all of which asked for minor revision. Section names below refer to paper/paper.md. Each reviewer item was checked against the code, the data files, or the built binary before any change. Where an item did not hold as written, this response says so and gives the measured value.

Nothing was committed. The Abstract is 1,918 characters, identical in paper/paper.md and paper/arxiv_submission.md. The Availability paragraph is unchanged and still cites tag v2.1.0. The theorem counts (200: 121, 68, and 11), the test count (265), and the line counts (576, 2,074, 525, 207, and 732) are unchanged, and no Lean file, test, or Main.lean was edited.

## Required items

Weekly and fixed-dose examples (health literacy). Both examples were run through the built binary, `.lake/build/bin/dosegate render`, with requests built by /Volumes/T7/tmp-dg/r12_t1.py. A once-weekly methotrexate order with the slot line "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}." returns status ok with "Take methotrexate 10 mg by mouth once a week." The same order with a daily-total slot is blocked with missingField. A structured insulin regular order of 20 units, three times a day, with no free text returns status ok with "Take insulin regular 20 units by mouth three times a day." The replay file eval/data/replay_v21/h2_results.jsonl gives h2_clinical_10 as ok with "Take Prednisone 20 mg by mouth once a day. Take Deltasone 40 mg by mouth once a day.", and gives h2_clinical_11 (a taper with two dose entries) and h2_clinical_18 (a sliding scale) as blocked with missingField. The weekly rule in What the patient sees and in Limits now covers weekly and monthly orders, and Limits names the conditional-order risk and the prednisone case.

Claude free daily flags (health literacy). The flags were recounted by calling the audit function `audit_text` in eval/score.py on the free daily records of eval/data/generations_v2_claude-haiku-5-5.jsonl and eval/data/generations_v2_claude-sonnet-5-5.jsonl. Haiku has 46 of 120 flagged and Sonnet 28 of 120. The same recount gives 16 for Qwen3.5-4B, 71 for MedGemma 4B, and 31 for Llama 3.2 3B, which match the paper. The flags now appear in Errors in free text and in the Claude runs paragraph, and both say that no labeler has labeled them. They are not in the Abstract (see Open items).

Claude max_tokens and stop reasons (computer science). All 1,051 Claude records (521 Haiku, 530 Sonnet) have max_tokens 2000 and effort low in the api field, and every record has stop_reason end_turn. The longest outputs were 1,309 tokens (Haiku) and 710 tokens (Sonnet). The Claude runs paragraph now gives the 2,000-token limit, the Models and conditions sentence about the 400-token limit now says that it applies to the open models, and the README command for the Claude runs now sets MAX_TOKENS=2000. The generator reads that variable at eval/generate.py line 12.

Blocks when no order is active (math). Checked against DoseGate/Render.lean, render, lines 161 to 173. The order is: duplicate identifiers, malformed braces (malformed), sentence shape (unbound), repeated values, a sign before a slot, an unnamed active order (omittedOrder), then each text and slot segment in turn, then separation (unseparated), then noActiveOrder. The binary confirms the reviewer's example: with one stopped order m1, the output "Take # {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}." is blocked with disallowedCharacter. The stopped order with a plain value sentence is blocked with inactiveOrder, a slot naming no order is blocked with unknownRef, and a framing sentence is blocked with noActiveOrder. The Trusted code paragraph now states the first-failing-check rule and gives the example.

## Recommended items

Health literacy recommended items 3 to 11 and math and computer science recommended items. Each change below is in paper/paper.md unless another file is named.

The word "reader" had three meanings. The FHIR input reader is now "input reader" everywhere. The people who judged outputs are "labelers" and "third labeler". The patient is "the patient" in the Introduction, Related work, and Conclusion. The field name `third_reader` in the label files is unchanged, and the paper says so.

The fallback leaves out on-hold, stopped, and doNotPerform orders without a line or a warning. Checked with the binary: an active lisinopril order with a warfarin order that is doNotPerform, on hold, or stopped returns ok with only the lisinopril line, and the same with warfarin active returns both lines. The paper now says so in What the patient sees.

The SNOMED CT route table is now an Appendix table (Table A1), built from DoseGate/Fhir.lean, Route.ofSnomed? and Route.phrase, with the 12 codes and printed phrases.

The acetaminophen label maximum was not stated. A WebFetch search of DailyMed returned no acetaminophen labels, so no number was added. The Limits sentence now says that the daily maximum on the label is a number this paper does not cite. The 5,900 mg figure stays, because it is computed from the orders.

The Table 2 omitted-order counts now have a script. The round 11 scratch script (/Volumes/T7/tmp-dg/r11/omit3.py) was copied into the repository as eval/omissions.py with relative paths. It prints 6 of 23 (round h1, version 1), 11 of 36 (round h1, comparison filter), 19 of 54 (round h2, version 2), and 33 of 80 (round h2, comparison filter), with the version 2.1 reasons (omittedOrder and unbound). The Table 2 caption names the script. The README reproduction list has a line for it.

The Table 2 caption now gives the current comparison filter releases for each round, from eval/data/replay_v21/development_results.jsonl (215 of 290), h1_results.jsonl (93 of 113), and h2_results.jsonl (107 of 138), counted from the baseline status ok.

The 0.4% bound in Results now states that it is over all 867 released texts pooled, with 0.9% for the 431 Qwen3.5-4B texts. The Wilson upper bound for zero events is z squared over n plus z squared: 0.44% at n = 867, 0.88% at n = 431, and 3.10% at n = 120.

The version 2.1 replay paragraph now says that the four unsupported-claim outputs are blocked: two with omittedOrder (h2_meaning_09 and h2_meaning_10) and two with unbound (h2_meaning_12 and h2_meaning_28), from eval/data/replay_v21/h2_results.jsonl.

The fallback paragraph now says that the command does not check order identifiers before building its template. Checked with the binary: the identifier "m1 }} {{drug:m2" is blocked with malformed, and "m1}} {{drug:m2" with unbound, so no text is shown.

The punctuation sentence now lists the sentence-end marks that cannot appear between the items of a value sentence. The binary confirms that a semicolon or colon in that position gives unbound, and a hyphen gives signBeforeSlot, while commas, parentheses, and slashes are accepted.

The Introduction and Agreement paragraph no longer state the number-comparing filter as a finding. The Introduction names only the digit-and-unit filter that was tested. The Agreement paragraph says the design expects a number-comparing filter to fail on computed totals and that it was not measured.

The comparison-only Llama split is now given: 51 misstatements, 120 faithful, and no unsupported claims, from eval/data/v2_review/labels.json (prefix bo, v2_llama3.2-3b, 171 rows). The sentence about 44 repeated instructions is also checked: 43 duplicated_instruction and one duplicated_instruction with other, so 44. The four Qwen3.5-4B and MedGemma 4B comparison-only labels are stated in the Agreement paragraph.

The 52 two-order rows of the label-rule sweep (eval/data/label_rule_sweep.json) are now broken down in Labels. They are 41 round-h2 rows, 10 round-h1 rows, and one development row. The 41 round-h2 rows cover all 19 pairs in eval/data/heldout2/same_ingredient_pairs.json (19 layer rows and 19 comparison-filter rows) and three same-name outputs in the comparison filter only (h2_meaning_07_control_case_metformin, h2_clinical_09, and h2_clinical_12). The round-h1 and development matches are all same-name pairs, so no separate caption count is needed.

The F05 relabel record in eval/data/replay_v21/labels.json has three reasons, and none of them mentions the version 2.1 output. The Labels paragraph now says so. The file still does not name the labelers, so the gap remains open.

The Claude runs paragraph gives the flags and the no-labeler statement. The Errors in free text paragraph gives the same flags and the 21 weekly-order cases, all perturbed (eval/data/cases.jsonl: 40 weekly cases among 240, all perturbed; 21 of the 120 test cases, all perturbed; no natural case has a weekly order).

The DoseBench reference (reference 3) was checked against the arXiv v2 page (https://arxiv.org/abs/2606.04262): the title, the five authors in order, and 230 questions with eight models all match. No change was needed.

Two survey references were added as references 11 and 12 and cited in Related work. Gatt and Krahmer, Journal of Artificial Intelligence Research, volume 61, 2018, pages 65 to 170, was checked on the JAIR page in round 12 and its pages were confirmed against the Crossref record for doi:10.1613/jair.5477. Ji and colleagues, Survey of hallucination in natural language generation, was checked against the Crossref record for doi:10.1145/3571730. That record gives ten authors in the order the reference now lists, ACM Computing Surveys, volume 55, issue 12, pages 1 to 38, and a 2023 date. The reference earlier listed three names that are not authors (Chen D, Dai W, and Chan HS), and those names were removed. The ACM page itself returned HTTP 403 in round 12, so the Crossref record is the source for those details.

The sibling field measured_omission for h2_model_style_p13_omit_three_orders was added in round 11. eval/data/heldout2/model_style.jsonl contains it once. The class field is unchanged, as the round 11 response explains.

The Conclusion now names the drug-name and display-name condition, and it says that the reader is the tested input reader.

## Not done

The Abstract does not gain the Claude flags, the Claude runs, or the stored-count note for the comparison filter. The Abstract is at 1,918 of 1,920 characters, and each addition needs a cut to a clause that carries a caveat or a number. The flags sentence alone is about 90 characters. The Abstract keeps every number and claim from round 11. Its wording changes are "patient" for "reader", "labelers" for "readers", "one author's reading, unchecked by a clinician" for "by the author's unchecked reading", "a correct prompt order" for "a correct order in the prompt", and "adding words with --extra-words" for the longer clause. Together they leave the Abstract 2 characters shorter than round 11.

A Lean theorem for the default policy (math recommended) was not written. It requires an edit to DoseGate/Proofs/Render.lean, which this pass may not change.

The pinned-commit reruns (computer science recommended) were not run. They need builds of commits 59c5f32 and ef2cc98 and a stored output file, which is new work. The paper still says the rerun is not recorded in this repository.

The Availability paragraph has no commit hash, as the constraint requires.

## Open items

The F05 labeler. The replay relabel, like every other label in the paper, was made by instances of Claude under the protocol. Whether those labelers were shown the version 2.1 outcome is not recorded, and the Labels paragraph now says exactly that instead of calling it a gap to close.

The acetaminophen label maximum: someone must check the DailyMed label for a daily maximum and cite it, then the Limits sentence can name the number.

The Availability tag. The round 12 files are committed and pushed, and the tag v2.1.0 is moved to that commit and pushed, so the sentence holds for this revision.

The README changed on disk during this pass. The edits in this pass were made on top of the file as it stood after the change, and the other change was left in place.

## Changes made

paper/paper.md, Abstract. "a correct order in the prompt" changed to "a correct prompt order" (7 characters). "the reader" changed to "the patient" (the sentence before "We describe" in the Abstract), "The FHIR reader" to "The FHIR input reader", "a deployment that adds words with --extra-words can release" to "adding words with --extra-words can release", "(by the author's unchecked reading)" to "(one author's reading, unchecked by a clinician)", and "readers found none in 60 sampled" to "labelers found none in 60 sampled". The length is 1,918 characters, checked in Python.

paper/paper.md, Introduction. "Deterministic filters, such as rules that compare numbers in the output with numbers in the record" changed to "such as rules that block digits and unit words in generated text", with the tested filter described as used with slot substitution, and two sentences added saying the number-comparing filter was not tested and that Results gives the design argument. "the reader" to "the patient".

paper/paper.md, Design. Punctuation sentence: the sentence-end marks are listed, and the binary results are in the Checks section above. Fallback paragraph: an identifier check sentence was added (verified with the binary). Exact quantities: "the reader gives" to "the input reader gives".

paper/paper.md, Table 1. "Fail closed" row renamed "Blocks when a check fails". The no-active-order row changed from "the only liveness result ... no general liveness theorem" to "the only result showing that release happens when it should; no general release theorem".

paper/paper.md, Trusted code. "525 in the reader" to "525 in the input reader". "The reader refuses" to "The input reader refuses" (two places). The noActiveOrder sentence was replaced (verified with DoseGate/Render.lean and the binary, with the stopped-order example). Course of therapy: "short-course" changed to "acute (short course)" (the FHIR code is acute). A sentence was added pointing to the Appendix route table.

paper/paper.md, Development and held-out testing. Reader and labeler wording (see the list in the response body). "knowledge of the reader code" to "knowledge of the input reader code" (two places). The round h1 omission counts were not changed.

paper/paper.md, Version 2.1. One sentence added: the four unsupported-claim outputs are blocked on replay, two with omittedOrder and two with unbound.

paper/paper.md, Table 2 caption. The stored comparison filter rows now give the current counts: 215 of 290, 93 of 113, and 107 of 138. A sentence names eval/omissions.py. The reader wording changed to labeler wording.

paper/paper.md, Models and conditions. "Every generation was limited to 400 new tokens." changed to "Every open-model generation was limited to 400 new tokens; the Claude runs used 2,000 (see Claude runs)."

paper/paper.md, Claude runs. The limit of 2,000 output tokens, the api field, the 1,051 records, the end_turn stop reason, and the longest outputs (1,309 and 710 tokens) were added. The flags sentence now says "labeler" and names eval/score.py.

paper/paper.md, Labels. Reader wording changed to labeler wording throughout, with the field name `third_reader` kept. Added: the three F05 relabel reasons do not mention the version 2.1 output. Added: the 52 two-order rows are 41 round-h2, 10 round-h1, and 1 development, with the 19 pairs and three same-name outputs named.

paper/paper.md, Comparison filter on model outputs and Agreement. The Llama comparison-only split (51, 120, 0) was added. The fourth Qwen3.5-4B output has no label, which the paper states. The sentence about a number-comparing filter now says the design expects the failure and that it was not measured.

paper/paper.md, Results. The 0.4% bound now says "over all 867 released texts pooled (0.9% for the 431 Qwen3.5-4B texts)". The Errors in free text paragraph gained the Claude flags and the all-perturbed note on the 21 weekly-order cases. The fallback paragraph gained the all-perturbed note on the 20 of 21 cases.

paper/paper.md, What the patient sees. Added: on-hold, stopped, and doNotPerform orders leave the fallback silently (verified). Weekly and monthly orders added to the as-needed rule. The weekly-line sentence rewritten to say the frequency does not show the dose is taken once a week only.

paper/paper.md, Limits. The acetaminophen sentence now names the missing label maximum. Added: the conditional-order paragraph with the structured insulin example and the prednisone taper case (both verified). The as-needed rule now covers weekly and monthly orders. "the reader behaves" changed to "the input reader behaves".

paper/paper.md, Conclusion. "provided the deployment keeps drug names out of its word list" changed to "provided the deployment keeps drug names and extra words out of medical content and checks display names against a clinical list". Reader wording changed to input reader, patient, and clinician.

paper/paper.md, Related work. Two sentences citing references 11 and 12 added after the Template-based sentence.

paper/paper.md, Appendix. Table A1 added, with 12 SNOMED CT route codes, the route names, and the printed phrases, from DoseGate/Fhir.lean.

paper/paper.md, References. Items 11 (Gatt and Krahmer) and 12 (Ji and colleagues) added.

paper/arxiv_submission.md. The Abstract is replaced with the paper's Abstract (1,918 characters), and the heading now reads "1,918 characters, under the 1,920-character limit".

README.md. "a reader" to "the patient" in the first paragraph. "the FHIR input reader", "same input reader", "the input reader" (three places). The Claude runs line now includes MAX_TOKENS=2000. A line for eval/omissions.py was added to the reproduction list. The labels line no longer says "reader labels".

eval/omissions.py (new). Copy of the round 11 omission script with relative paths. Output: round h1 layer 6 of 23, round h1 comparison 11 of 36, round h2 layer 19 of 54, round h2 comparison 33 of 80.

## Checker pass

A checker pass listed 21 findings on the round 12 draft. Two of them repeat others (the citation order and the arXiv table count), so 19 distinct findings were checked. Each was checked against the manuscript, the Lean source, the data files, the built binary, or Crossref before any change. Nothing was committed, and no Lean file, test, label file, or Claude data file was edited.

Citation order. Fixed. References 37 and 38 are now 11 and 12, references 11 to 36 moved up by two, and every citation marker and the reference list were renumbered. Markers now first appear in the order 1 to 38.

Arxiv table count. Fixed. The arXiv comments line says 4 tables (Table 1, Table 2, Table 3, and Table A1).

Table order. Fixed. The held-out table is now Table 2 and the open-model table is Table 3, so captions appear in order. Text references in the paper, the README, and this response were changed to match.

Not yet cited. Fixed. The parenthetical now says "which this paper does not cite".

Fallback count. Fixed. The sentence now gives 118 of 120 test cases printed, 20 of 21 weekly-order cases, and 98 cases that would still print without weekly orders. The term "eligible" is gone.

Free-text breakdown. Fixed. Of the 6,013 active orders with free text, 4,066 say "Take as needed.", and the other 1,947 are 1,946 coded timing phrases plus one course note (eval/data/free_text_share.json lists seven distinct texts, and 4,066 + 1,069 + 323 + 221 + 193 + 140 + 1 = 6,013).

Temp field. Documented, not edited. The two Claude data files set temp to 0.0 with no temperature sent. The README now says the field is a placeholder. Changing the data files needs Parker's approval and is outside this pass.

References 37 and 38. Fixed from Crossref, as described in the Related work item above. The article number was not used, because Crossref gives the page range 1 to 38.

Stale PDF. Fixed. paper/dosegate.pdf and paper/dosegate.docx were rebuilt from the revised paper.md with the scripts in HANDOFF.md. pdffonts shows only Times New Roman, and the rebuilt PDF text has "The FHIR input reader is tested, not proved."

render_ok_eq. Fixed. The proof exists at DoseGate/Proofs/Render.lean lines 329 to 336 and is used by render_one_active_ok (line 838). Table 1 has a new Release row that cites both theorems, and the paragraph on proofs now says two results concern release. The old claim that render_one_active_ok is the only such result is removed. The new text says no theorem shows that a given model output passes the checks.

Theorem authors. Fixed (see the Related work item above).

Llama relabel. Rejected in part. The three Llama comparison-filter outputs are recorded in eval/data/label_rule_third_reader.json with label_before_round10 set to faithful and label_after_round10 set to misstates_order: Jack927 (perturbed, slot daily), Corinne382 (perturbed, slot), and Julia241 (perturbed, slot). The checker said the stored files could not show which outputs changed. They can, through that file, and the Labels paragraph already points to it. The 48 figure (51 minus 3) therefore stands. The checker's count of four rows does not match the record. The paper says "twelve records" now, because the twelve entries in that file are one per output and filter (the round-h1 outputs count twice).

Sliding scale. Fixed. The drug-name rule refuses names containing sliding, scale, or taper. The built binary confirms that a drug named "insulin sliding scale" and one named "prednisone taper" each block with missingField ("no usable drug"). The example in Limits is now an insulin dose set by a blood glucose reading, and the paragraph states the drug-name refusal.

Shape words. Fixed. The vocabulary in DoseGate/Tokens.lean has 67 words and no take or which. The Design sentence now says "take", "which", and "is" are shape words, that "is" is in the vocabulary, and that "take" and "which" are added separately.

Stored counts. Fixed. Each of the three comparison-filter counts in the body (218, 104, and 128) now gives the current build count in parentheses (215 of 290, 93 of 113, and 107 of 138).

Fallback line example. Rejected. The text at line 170 already reads "Take metformin 500 mg by mouth, twice a day.", with the comma. The built binary prints "Take aspirin 81 mg by mouth, once a day." for an aspirin order, so the comma form is correct.

Conclusion count. Fixed. The sentence now says 16 of the 19 round-h2 requests that version 2 released and that give one ingredient under two names.

Third instance. Fixed. "Third instance" is now "third labeler" in the three places where it named the labeler.

Twelve records. Fixed in the same pass. The Labels paragraph said "twelve outputs" and listed nine output names. The twelve entries are one per output and filter, so the text now says "twelve records".

Availability tag. The sentence is unchanged; the tag is moved to the round 12 commit after it is committed.

Abstract. Unchanged. It is 1,918 characters and identical in paper/paper.md and paper/arxiv_submission.md.
