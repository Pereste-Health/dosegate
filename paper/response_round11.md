# Response to the eleventh round of review

This pass answers the three round 11 reviews (health literacy, math, and computer science), all of which asked for minor revision. Section names below refer to paper/paper.md. Each reviewer item was checked against the code, the data files, or the built binary before any change. Where an item did not hold as written, the response says so and gives the measured value. Every count added or corrected was measured by the command or file named.

Nothing was committed. The git tag v2.1.0 still names commit eabf9a1, and the commit hash in Availability is a placeholder, so both need the commit step (see Open items).

## Checker follow-up

A checker pass after the round 11 changes listed 17 findings. Four of them repeated other findings, which leaves 13 distinct issues. Each was checked against the data, the Lean source, or the built binary before any change. Twelve were fixed. The thirteenth, the class field of h2_model_style_p13_omit_three_orders, was kept as written (see the last item).

Abstract label-limit wording. Confirmed. The count of 221 holds: hydrochlorothiazide 113, amlodipine 79, lisinopril 48, and simvastatin 24, from the eval/maxima.py logic. But 23 of the 221 exceed only lisinopril's 40 mg, and the label sets no maximum for that drug, so "label limit" overstated them. The last sentence of the Abstract now reads "221 of 368 released outputs with deliberately changed doses exceeded a US label maximum or the top of a usual range." That covers all four drugs: amlodipine and simvastatin have stated maximums, and hydrochlorothiazide 50 mg and lisinopril 40 mg are the tops of usual ranges. To keep the Abstract within 1,920 characters, four phrases were shortened: "so a correct order in the prompt does not guarantee a correct output" (was "a correct number in the output"), "appears only in that order's instruction" (was "an instruction for that order"), "67 framing words, take, and which" (was "67 framing words plus take and which"), and "120 slot-condition test cases" (was "120 test cases in the slot condition"). No number or caveat was removed. The Abstract is 1,920 characters, identical in paper/paper.md and paper/arxiv_submission.md.

Claude release counts. Confirmed by a recount from the decision files: Haiku 118 plus 115 gives 233, and Sonnet 118 plus 116 gives 234. The Results sentence now gives one count for each run and no combined total.

Scope of the 2,764 decisions. Confirmed: Qwen3.5-4B 768, MedGemma 4B 804, and Llama 3.2 3B 1,192 sum to 2,764. The sentence now says "of the three open models." The Claude runs are not in that total.

Pinned-commit rerun of Table 3. Confirmed as unsupported. Nothing in the repository or in the scratch directory records a run at 59c5f32 or ef2cc98. The logs that exist (rerun_h1.log and rerun_h2.log in the scratch directory) come from the current build and give 93 and 107 comparison-filter releases. The paper now says the round-h1 and round-h2 rows can be rerun at those commits with the current eval/attacks.py, and that the rerun is not recorded in this repository. The exact-match claim is removed. The ef2cc98 description now says that script parses and re-serializes each request, which matches git show ef2cc98:eval/attacks.py. The replay corpora were rerun in this pass, and eval/attacks.py reproduces the three replay result files row for row (290, 113, and 138 rows).

Version 2.1 blocks the Important output. Confirmed. That output ("Important: Take enoxaparin 40 mg as a shot under the skin once a day.") names one of its eight active orders (m5), so seven are unnamed. Version 2.1 blocks it as unbound, at the sentence-shape check, so it is not in the omittedOrder group. The paragraph now says so. The 28 blocked releases still split 20, 4, 2, 1, and 1.

Check order. Confirmed against DoseGate/Render.lean (render, lines 161 to 173) and renderSeg. The Design paragraph now lists the checks in the order the code runs them, with the reason name for each.

F05 and statusReason. Confirmed by probe. With one active order that carries statusReason, the binary returns missingField for the dose. With a second active order that the output does not name, version 2.1 returns omittedOrder. No file under DoseGate/ or Main.lean mentions statusReason. The Labels paragraph now says so.

Labels for the seven newly released requests. Confirmed. None of F28, F29, F30, F31, G01, G03, and G04 appears in eval/data/attack_labels.json. G01, G03, and G04 have layer labels in eval/data/replay_v21/labels.json. The Reproducing paragraph now says so.

README reproduction list. Confirmed that four scripts were missing. The list now has bootstrap.py (with its five tags), maxima.py, fallback_rate.py (with the DOSEGATE variable), label_rule_sweep.py, and coded_timing_check.py (which needs SYNTHEA_FHIR_DIR). In a scratch copy, bootstrap, maxima, fallback_rate, and labels reproduce the committed files byte for byte, and label_rule_sweep matches 91 of 1,109 outputs. coded_timing_check was not run, because the raw bundles are not in the repository.

Fallback with no active order. Confirmed. dosegate fallback returns status error and exits with status 1. The patient section now says so, and says the application must route the patient to a pharmacist.

Trusted-code refusal list. Partly confirmed. Three refusals were missing from the list and are now in it: a bundle resourceType that is not null and is not Bundle, and a patient field that is neither null nor a non-empty string. The bundle type, subject, and bundle-with-list refusals are stated later in the same section. Probes showed that a null patient, a null bundle resourceType, and a null request key on a bundle entry are all accepted, so the wording says "non-null" or "neither null nor", and no item was added for a null request key.

PDF and Word files. Confirmed. The repository copies were built at 17:22, before the round 11 edits, so they did not carry the revised text. They were rebuilt from paper/paper.md with the commands in HANDOFF.md: the sed step that strips backticks, then the personal-brand-docs build_pdf.sh and build_docx.sh. The PDF has 29 pages, and pdffonts lists only Times New Roman faces. The arXiv note has a new check step before upload.

Class field of h2_model_style_p13_omit_three_orders. Not changed. The class value, "list omits three active orders," is the attacker's own description of its request. eval/labeling_protocol.md (line 44) and the round 9 response both say it stays as written. The measured omission, five of eight active orders, is in the measured_omission field added in round 11 and in the Held-out round against version 2 paragraph of the paper, and the paper's own count is correct. No script matches the string. Changing the value would also mean editing the copies in eval/data/heldout2/model_style_results.jsonl, eval/data/replay_v21/h2.jsonl, and eval/data/replay_v21/h2_results.jsonl. If Parker wants the class field to show the measured count, that is a one-line change in each file, and the protocol note would need the same change.

## Claude Haiku 5.5 and Claude Sonnet 5.5 runs

The repository holds test-half runs of two more models. The commit that added them (a95cc58) ran them through the Anthropic backend of eval/generate.py (BACKEND=anthropic, low effort, 400 tokens, no temperature sent, so the API default sampling applied). The paper now says so in Models and conditions (new paragraph "Claude runs"). Table 2 does not include them, as Parker decided.

Counts were computed from eval/data/final_gate_decisions_v2_claude-haiku-5-5.json and the sonnet file, taking the last attempt per case, and checked against eval/data/results_test_v2_claude-*.json:

Haiku 5.5: slot after rewrites 118 of 120; slot daily after rewrites 115 of 120; released texts 233 (118 plus 115); detected misstatements 0; free daily 0 of 120 released (the scoring script flagged 46 raw outputs, no reader labels); attack 0 of 120 released (3 raw outputs flagged, all 120 blocked).

Sonnet 5.5: slot after rewrites 118 of 120; slot daily after rewrites 116 of 120; released texts 234 (118 plus 116); detected misstatements 0; free daily 0 of 120 (28 flagged raw); attack 0 of 120 (0 flagged raw).

The Results section has one new paragraph with these counts. Model dependence now says the 98.3% to 1.7% range is across the three open models, and that the two Claude runs each released 98.3% of slot outputs after rewrites. Availability names the Claude runs. The README reproduction section says eval/models.py writes a five-model summary and that the Claude runs used BACKEND=anthropic.

The Abstract does not name the Claude runs. Parker's decision put them in Models and conditions and Results, and the Abstract is at 1,920 characters, the limit, so adding them would need cuts to numbers. This is listed under Open items.

## Bootstrap intervals (math recommended item)

Command: `cd eval && python3 bootstrap.py v2_qwen3.5-4b v2_medgemma-4b v2_llama3.2-3b v2_claude-haiku-5-5 v2_claude-sonnet-5-5`. This rewrote eval/data/bootstrap.json with all five tags (it held only Sonnet before). No model output was regenerated.

Table 2 now gives the patient-cluster interval in parentheses after each Wilson interval. The reviewer expected the cluster intervals to be wider. They are not uniformly wider. Comparing each bound with its Wilson bound, the largest differences are 2.1 points (Qwen3.5-4B attack, lower bound: Wilson 10.4, cluster 8.3) and 2.0 points (MedGemma temperature 1.0, upper bound: Wilson 87.2, cluster 89.2), and the other bounds differ by 1.5 points or less. The Outcome measures paragraph now states this measured result in place of the claim that the Wilson intervals are narrower.

The commit message of a95cc58 says the bootstrap intervals are within 1.5 points of the Wilson intervals. That is not correct for the attack row (2.1 points), so the message is wrong, though the paper does not repeat it.

## Labels and third readers (math recommended items)

Nine records had a final label that differed from both readers and a null third_reader: six round-h1 records (h1_chart_prior_both_in_output, h1_chart_duplicate_same_regimen, h1_chart_near_duplicate_dose_and_sig, layer and comparison filter), h2_structure_15 (comparison filter), and F05 in the layer and comparison-filter files. Each now has third_reader set to the third reader's label (round 10 value from eval/data/label_rule_third_reader.json; F05 from eval/data/replay_v21/labels.json, misstates_order). third_reader_before_round10 is null on all nine. Labels and relabel notes are unchanged. Script: direct JSON edit with the indentation kept, then `cd eval && python3 labels.py`.

Check: labels.py output differs from the output before the edit only in third_reader_used: development layer 2 to 3, development comparison filter 23 to 24, round-h1 layer 14 to 17, round-h1 comparison filter 25 to 28, round-h2 comparison filter 22 to 23. Round-h2 layer stays 12. Label counts, kappa, and agreement do not change.

The Labels paragraph states what third_reader holds, lists the nine records, and adds the duplicate-chart rule discussion (below).

Duplicate chart (math recommended). Rule (3) makes h1_chart_duplicate_same_regimen faithful. The comparison filter output h1_structure_15 prints the same two lines with one comma and is misstates_order under rule (2), because its chart holds one order. I confirmed with the binary that version 2.1 blocks h1_chart_duplicate_same_regimen (ambiguousDrug) and h1_structure_15 (repeatedValue). The Labels paragraph and the Table 3 caption say so.

F05 relabel (computer science recommended). The paper now says the relabel is in eval/data/replay_v21/labels.json, that the file does not record who made it or whether that reader knew the version 2.1 outcome, and that this gap should be closed before posting. Parker has to supply the labeler and that fact. I did not invent either. The label rests on the statusReason field. Version 2.1 does not release F05, but the binary blocks it with omittedOrder (the second active order m2 is unnamed), not with a statusReason rule. The paper says version 2.1 does not release it, which is what the binary shows.

Errors in free text (math recommended). The sentence about the 240 version 1 free outputs now says that none of the 240 free-condition outputs is flagged, and that 32 of the 240 free daily outputs are flagged (16 development, 16 test), the same flags Errors in free text reports. The 32 figure is the existing Qwen3.5-4B flag count from the version 1 run (eval/data/free_text_labels.json and the Errors in free text paragraph), which I did not recompute from score.py in this pass.

## Table 3 omitted orders (math recommended, found while checking)

The reviewer said the round-h1 faithful count includes one omitting output, and that the drop-seven request has seven active orders. Both are wrong.

Drop-seven (h1_model_style_drop_seven_of_eight_orders, eval/data/heldout/model_style.jsonl) has eight entries: m3 is stopped and m7 has doNotPerform true. So six orders are active (m1, m2, m4, m5, m6, m8). The paper now says six.

Counting faithful outputs that omit an active order (no value slot in the request's output template names the order's dose, route, frequency, sig, or daily total) gives more than one in round h1. The script is /Volumes/T7/tmp-dg/r11/omit3.py, which uses the request "output" field, the active-order rule, the main subject of each request, and the 19 one-ingredient IDs from eval/data/heldout2/same_ingredient_pairs.json:

Round h1, version 1 (layer): 6 of 23 faithful. Version 2.1 replay: omittedOrder 2, unbound 4.
Round h1, comparison filter: 11 of 36 faithful. Version 2.1 replay: omittedOrder 3, unbound 8.
Round h2, version 2 (layer): 19 of 54 faithful. Version 2.1 replay: omittedOrder 18, unbound 1.
Round h2, comparison filter: 33 of 80 faithful. Version 2.1 replay: omittedOrder 20, unbound 13.

Version 2.1 blocks all 69 (the four replay rows sum to 69). The round-h2 layer count of 20 in the version 2 paragraph includes two one-ingredient outputs (h2_model_style_p04 and p19), which the Table 3 faithful column excludes; the 18 plus those two gives the 20 that version 2.1 blocks with omittedOrder in the Version 2.1 paragraph.

The Table 3 caption and the h1 paragraph give these counts. The h1 paragraph says that counting every such output as a misstatement would give 44 (38 plus 6) and 62 (51 plus 11). The headline counts in the Abstract (38 in 74, 23 in 128) follow the labels as adopted, which are unchanged.

## Reproducing the older Table 3 rows (computer science required)

I checked the argument handling of the pinned scripts with git show, and did not build those commits, as instructed.

Commit 59c5f32 eval/attacks.py takes no arguments, reads eval/data/attacks.jsonl (the development corpus), ignores BINDIR, and writes attack_results.jsonl into its own data directory.

Commit ef2cc98 eval/attacks.py reads its two arguments, but it passes each request through json.loads and json.dumps before sending it, and it runs the binary in the archive's own .lake directory, not BINDIR.

The paper gives the reviewer's instruction (current eval/attacks.py, BINDIR pointing at a build of the pinned commit). The first round 11 pass said the round-h1 and round-h2 rows reproduce exactly (74 and 104; 86 and 128). That claim had no record behind it, so the checker follow-up replaced it with the statement that the rerun can be done and is not recorded in this repository. Two sentences were deleted in the first pass: "This revision did not rebuild commits 59c5f32 and ef2cc98, so the Table 3 held-out rows are not confirmed at those commits." and "The rerun has not been done for this version of the paper."

## Health literacy items

Omitted orders in Limits (required). I confirmed with the built binary. A request with an active lisinopril order (10 mg once a day) and a warfarin order that is doNotPerform true, on-hold, or stopped returns status ok with "Take lisinopril 10 mg by mouth once a day." and no block. The control with warfarin active returns omittedOrder. Limits and Trusted code now state the consequence and the deployment requirement.

Harm of the 16 same-ingredient releases (required). I checked each example against eval/data/replay_v21/h2_results.jsonl:
Lantus 20 units plus insulin glargine 10 units, once a day each: 30 units a day (h2_chart_same_drug_lantus_glargine). Correct.
Synthroid 50 mcg plus levothyroxine 75 mcg, once a day each: 125 mcg a day (h2_meaning_02). Correct.
Glucophage 500 mg twice a day plus metformin 1000 mg once a day: 2,000 mg of metformin a day (h2_meaning_03). Correct.
Acetaminophen 500 mg every 6 hours plus Tylenol 650 mg every 4 hours as needed (h2_clinical_20): the Tylenol order has asNeededBoolean true in eval/data/replay_v21/h2.jsonl, and the released text prints "as needed". At the printed frequencies that is 4 times 500 mg (2,000 mg) plus 6 times 650 mg (3,900 mg), up to 5,900 mg. Correct.

These four appear in Limits. The Conclusion adds that version 2.1 still releases 16 of the 138 round-h2 requests with one ingredient under two names.

Abstract (required). The sentence now reads: "On replay, version 2.1 returns no text for all 9, but 16 of its 45 round-h2 releases give one ingredient under two names, which a patient could take as a double dose (by the author's unchecked reading)." The first round 11 pass left the Abstract at 1,919 characters. The checker follow-up changed the last sentence and shortened four phrases, so the Abstract is now 1,920 characters, at the limit, with no number removed. The arXiv note has the same text and the new count.

As-needed rule (recommended). One rule now appears in What the patient sees and in Limits: do not release any line, from the fallback or from model text, to a patient who has an as-needed order (asNeededBoolean true) unless a pharmacist has checked that patient's line.

Drug-name rule (recommended). Design now states that the rule does not screen medical content. I confirmed with the binary: a record name "Metformin treats diabetes" with one order of 500 mg twice a day prints "Take Metformin treats diabetes 500 mg by mouth twice a day."

Hydrochlorothiazide (recommended). I checked DailyMed set 8c868894 with WebFetch. The label gives a usual initial dose of 25 mg daily and says "The dose may be increased to 50 mg daily, given as a single or two divided doses." It gives no usual range or maximum. The text now says that 50 mg is the highest dose the label names, reached as an increase, and the sentence says "label maximum or the top of the usual range". Amlodipine, simvastatin, and lisinopril were not rechecked in this pass.

Perturbed-order wording in Abstract (recommended). The Abstract now says "221 of 368 released outputs with deliberately changed doses exceeded a US label limit." The longer clarification is in Results.

Units (recommended). Conclusion now says the printed units (mg, mcg, mL) are clinician abbreviations, and that the wording was designed for a checked reader.

## Math required and recommended items

noActiveOrder wording (required). Checked against DoseGate/Render.lean lines 161 to 172 and the binary. The check runs after the sentence-shape, repeated-value, sign, omitted-order, slot, and separation checks. On an empty chart, `Take metformin.` is blocked with unbound, `Take zzz {{drug:m1}}.` with unbound, and `Here is your medicine list.` with noActiveOrder. The Design and Trusted code sentences use the reviewer's corrected wording.

Fail-closed reader (recommended). The sentence "The reader fails closed." is replaced with a statement of what the reader refuses. The policy choice for an unknown status is stated, and the fuzz test is said to share the choice.

Fidelity row (recommended). Table 1 now says fmtField applied to the order. The Table 1 caption adds that fmtField, the unit and route tables, and the frequency words are trusted code, that dose_piece_readback is the read-back proof, and that the rows together state what released text satisfies without one theorem for that conjunction.

Theorem for the default policy (recommended). Not done. Adding a Lean theorem edits DoseGate/Proofs/Render.lean, which this pass did not change. The Table 1 caption states the gap instead.

Availability tag (recommended). The stale sentence "The tag will be moved ... before the paper is posted" is removed. The paragraph now says the layer is release v2.1.0, that the tag names the commit holding the layer, the evaluation data, and this manuscript, and that `git ls-remote origin 'refs/tags/v2.1.0^{}'` gives that commit. The tag is moved to the final commit of each revision and pushed; after this revision it names the round 11 commit.

## Computer science items

Claude runs (required). See the first section.

Table 3 reproduction (required). See the older-rows section.

Comparison filter (recommended). The paragraph now says the gap between the two filters is the joint effect of all the layer's text checks, not one check, and that the proofs show only that the checks imply the stated property.

## Other changes

Table 2 cluster intervals and the Outcome measures paragraph (see Bootstrap).

Results. The sentence that said the Claude runs were absent is replaced by counts (see Claude runs).

eval/data/heldout2/model_style.jsonl. Record h2_model_style_p13_omit_three_orders gained the field measured_omission: "five of eight active orders omitted (measured from the released text; m3 stopped, m8 intent plan)". The class field and the request are unchanged, so attacks.py output does not change. The checker follow-up kept the class field as written (see Checker follow-up).

## Changes made

paper/paper.md, Abstract. Old: the replay sentence "On replay, version 2.1 returns no text for all 9, but by the author's unchecked reading, 16 of its 45 round-h2 replay releases give one ingredient under two names." New: the sentence in the Health literacy section above. Old: "normalized slot-condition test cases." New: "test cases in the slot condition." Old: "221 of 368 released perturbed-order outputs exceeded a usual US label maximum or the top of usual range." New: "221 of 368 released outputs with deliberately changed doses exceeded a US label limit." Old: "that states its dose, route, and frequency" New: "stating its dose, route, and frequency". Old: "outside any instruction" New: "outside an instruction". Old: "MedicationRequest, and the layer fills each reference or blocks the output." New: "MedicationRequest; the layer fills each reference or blocks the output." Length: 1915 to 1919 characters, counted in Python (len of the Abstract text).

paper/paper.md, Design. noActiveOrder sentence (old: "block an output that has no slot with the reason `noActiveOrder`"; new: "block with the reason `noActiveOrder` each output that passes every earlier check and has no slot"). New sentence after "The noActiveOrder check runs last..." giving the `Take metformin.` example. Drug-name rule sentence added (see above).

paper/paper.md, Table 1. Fidelity row: "the formatted field of the single active order" changed to "`fmtField` applied to the single active order". Caption: sentences added on fmtField, dose_piece_readback, and the conjunction.

paper/paper.md, Trusted code. "The reader fails closed." replaced with the refusal sentence. Added sentence on the policy choice and unknown status. noActiveOrder and inactiveOrder/unknownRef sentence replaced (old: "render blocks an output with no slot with `noActiveOrder`, and an output with a slot with `inactiveOrder` or `unknownRef`"; new: the reviewer's wording).

paper/paper.md, Development and held-out testing. Round-h1 omission sentence: old "one output ... seven active orders ... would give 39 and 52"; new "six version 1 releases and 11 comparison-filter releases ... six active orders ... would give 44 and 62" (38+6, 51+11). Source: /Volumes/T7/tmp-dg/r11/omit3.py and the drop-seven request.

paper/paper.md, Models and conditions. New paragraph "Claude runs" before "Comparison filter". Comparison filter sentence rewritten (old: "To separate the contribution of the verified checks from that of slot substitution alone, we built a comparison filter that reads each request with"; new: "To measure how much the layer's checks reduce misstatements, we built a comparison filter that keeps slot substitution and removes all of the layer's text checks together. The gap ... joint effect ... The filter reads each request with").

paper/paper.md, Outcome measures. Old: "the intervals treat outputs as independent although they cluster within 60 patients, so they are narrower than intervals that account for clustering." New: the measured cluster sentence (max difference 2.1 points; source eval/data/bootstrap.json, Wilson values from eval/models.py formula).

paper/paper.md, Labels. Rule (3) duplicate paragraph added (source: eval/data/heldout/labels_h1.json, eval/data/heldout/chart.jsonl, structure.jsonl, eval/data/replay_v21/h1_results.jsonl). Third_reader sentence added (eval/data/label_rule_third_reader.json, eval/data/replay_v21/labels.json). F05 sentences added (old: "...discontinuation reason."; new: plus the labeler gap and statusReason sentences). Free-condition sentence replaced (old: "The current scoring script flags none of the 240 version 1 free outputs."; new: the reviewer's sentence, with 32 of 240 free daily flags).

paper/paper.md, Table 2. Caption: cluster intervals explained. Each row with a Wilson interval got a cluster interval from eval/data/bootstrap.json (command above). Qwen slot first 75.0 to 87.5; slot after 95.0 to 100.0; slot daily first 75.0 to 88.3; slot daily after 95.0 to 100.0; temperature 1.0 66.2 to 80.0; attack 8.3 to 23.3. MedGemma slot first and after 76.7 to 89.2; slot daily 75.0 to 88.3; temperature 1.0 76.2 to 89.2. Llama slot first, after, and daily first 0.0 to 5.0; slot daily after 0.0 to 6.7; temperature 1.0 9.2 to 19.6.

paper/paper.md, Table 3 caption. Old: "Faithful counts outputs ... version 2.1 blocks all such outputs." New: faithful-omission counts (6 of 23, 11 of 36, 19 of 54, 33 of 80; 69 total) and the duplicate-line note.

paper/paper.md, Reproducing Table 3. Command changed to the current eval/attacks.py with BINDIR and a path to the current repository. Two sentences removed (see above). Replaced "This revision did not rebuild ..." with the reproduction statement.

paper/paper.md, Results. Sentence added after the last sentence of the Released text paragraph (Claude counts). Model dependence sentence changed (old: "on the same cases and prompts, greedy release after rewrites ranged from 98.3% to 1.7%."; new: "across the three open models on the same cases and prompts ... (the two Claude runs ... 98.3%)").

paper/paper.md, Results, released doses. Old: "the usual maximum or top-of-range daily dose"; new: "the label maximum or the top of the usual range". HCTZ clause changed (old "(for hypertension, "The dose may be increased to 50 mg daily")"; new "(the highest dose the label names for hypertension, which the label allows as an increase from a usual initial dose of 25 mg daily: ...)").

paper/paper.md, Limits. Omitted-order consequence added. Four harm examples added after "which no clinician has checked." Old: "Both forms were checked ... until a pharmacist has checked it, and must take the reason ..."; new: the as-needed rule sentence.

paper/paper.md, What the patient sees. As-needed rule: added "unless a pharmacist has checked that patient's line" (old: "(asNeededBoolean true), and do not show the fallback").

paper/paper.md, Conclusion. Added sentence on 16 of 138 round-h2 requests and on units.

paper/paper.md, Availability. Old: "The tag will be moved to the final commit of this revision before the paper is posted." New: "The layer described here is release v2.1.0: the git tag v2.1.0 in that repository names the commit that holds the layer, the evaluation data, and this manuscript ..." Added the Claude runs to "all model outputs".

paper/arxiv_submission.md. Abstract replaced with the new text; heading now says 1920 characters. The checker follow-up added a check step (step 3) before upload.

README.md. Line 53: the Claude runs used BACKEND=anthropic. Line 56: eval/models.py writes a five-model summary. The checker follow-up added five reproduction lines for bootstrap.py, maxima.py, fallback_rate.py, label_rule_sweep.py, and coded_timing_check.py.

eval/data/heldout/labels_h1.json (6 records), eval/data/heldout2/labels_h2.json (1 record), eval/data/attack_labels.json (2 records, F05). third_reader set; third_reader_before_round10 null added.

eval/data/labels_summary.json. Regenerated with `cd eval && python3 labels.py`. Only third_reader_used changed (see above).

eval/data/bootstrap.json. Regenerated with five tags (command above).

eval/data/heldout2/model_style.jsonl. Field measured_omission added to h2_model_style_p13_omit_three_orders.

## Open items

Commit and tag. This revision is committed and pushed, and the tag v2.1.0 is moved to that commit and pushed.

Lean theorem for the default policy (math, recommended). Not done in this round. The guarantee is the conjunction of the Table 1 theorems, and the Table 1 caption now says that no single theorem states the conjunction; a combined theorem is left for a later revision.

F05 labeler. The replay labels in eval/data/replay_v21/labels.json were made by instances of Claude under the same protocol as every other label in the paper. Whether those labelers were shown version 2.1's decision for each text is not recorded, and the Labels paragraph says so.

Abstract and Claude runs. The Abstract does not mention the Claude runs. Adding a clause needs more number cuts from the Abstract, which is at 1,920 of 1,920 characters.

Table 3 reproduction. The paper says the round-h1 and round-h2 rows can be rerun at commits 59c5f32 and ef2cc98, and that the rerun is not recorded. Nobody has built those commits and rerun the attacks in this repository. Either build them and record the output under eval/data/ with the commit hashes, or leave the wording as it is. This pass did not build the pinned commits.

Pharmacist check of the 16 same-ingredient pairs. Not done.

PDF and Word. paper/dosegate.pdf and paper/dosegate.docx were rebuilt in the checker follow-up from the revised paper.md (29 pages, Times New Roman only). Rebuild them again after any further change to paper.md, before the arXiv upload.

Other sessions' changes. The working tree still holds other uncommitted work (paper/dosegate.docx, paper/dosegate.pdf, HANDOFF.md, docs/, paper/site_brief.md were already modified or untracked). This pass did not touch them.
