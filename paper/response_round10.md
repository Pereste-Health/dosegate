# Response to the tenth round of review

This pass also covers two changes that landed after the first pass: the reader rules that refuse malformed orders, bundle entries, and unknown keys (commit f8003e6), and the restoration of raw numbers in the development replays (an uncommitted change to eval/attacks.py). The sections "Reader change", "Raw numbers and replays", and "New labels" describe both changes and the three new labels. The first-pass items that these changes affect are updated in place.

Section names below refer to paper/paper.md. Each reviewer item was checked against the code, the data files, or the built binary before any change. Where an item did not hold, the response says so and gives the reason. Every count added or corrected in this round was measured by the command or file named.

## Reader change (commit f8003e6)

Commit f8003e6 makes the reader refuse, rather than skip or default, the malformed shapes listed in Trusted code of paper/paper.md. The checks are in DoseGate/Json.lean: orderShapeProblem (line 460) for wrong-typed order fields and a doNotPerform that is not a boolean or null, keyProblem (line 477) for keys outside the allowlists at the request, bundle, and bundle entry levels, resourceProblem (line 482) and entryProblem (line 489) for bundle entries, bundleEntriesProblem (line 493), orderProblem (line 498) for the empty id and the subject checks, and shapeProblem (line 552), which runs them in order. The diff of f8003e6 to DoseGate/Json.lean removes no line, so the change only adds refusals. Every request that the earlier reader accepted gets the same reply unless one of the new checks fails.

Probes on the built binary (a Python script that sends one request to `dosegate render` for each case) confirm the rules. A doNotPerform of "yes" returns error. A doNotPerform of null and a doNotPerform of false both return ok. An unknown request key returns error, and the same key with a null value returns ok. An empty id returns error. A list element with resourceType MedicationStatement returns error. A frequency of 2.5 returns error, and a frequency of 1001 returns blocked with missingField, as the paper's timing rule says. A string asNeededBoolean, a string dispenseRequest, a string meta, a string medicationCodeableConcept, a string doseQuantity value, and a string route each return error. A bundle entry with no resource, a resource of null, a resource without resourceType, a resourceType of 5, a resourceType of the empty string, or a non-object entry each return error. A bundle entry with an unknown key returns error. A bundle entry with a Patient resource is skipped, and the order in the same bundle is released.

The evaluation is unchanged by these rules. Each of the 240 case requests in eval/data/cases.jsonl, with the subject Patient/p1 added as the scripts add it, was sent to `dosegate render` with a placeholder output. None returned an error, so no decision in the evaluation changes. The paper says so in Models and conditions.

Counts in the paper now use the current files. Json.lean has 580 lines and 487 non-blank lines (`grep -c '\S' DoseGate/Json.lean`), and Main.lean has 234 lines and 207 non-blank lines, so the reader and command-line total is 694 non-blank lines. The definitions in DoseGate/*.lean, excluding Json.lean and DoseGate/Proofs.lean, have 576 non-blank lines. The proofs in DoseGate/Proofs/*.lean have 2,074 non-blank lines and 200 theorems (`grep -cE '^\s*(theorem|lemma)\s'`). The axiom check (`lake env lean tests/Axioms.lean`) gives 121 theorems on the three standard axioms, 68 on a proper subset, and 11 on none. The regression tests (`bash tests/run.sh`) report 260 passed and 0 failed, up from 232. The differential fuzz test (`python3 tests/fuzz_reader.py --core v2 --seed 7 --count 20000`) reports 20,000 agreements, no unexplained disagreement, and 52 distinct mutation kinds.

Paper changes for this commit: Trusted code states the rules and the counts, Limits drops the sentence that a later version may refuse bundle entries (the current release refuses malformed entries and skips only entries for other resource types), Conclusion uses 694 lines, and README.md's Use section and --allow-omissions option state the same rules.

## Raw numbers and replays

The development corpus has 11 requests whose numbers were stored as the placeholder "\u0000NUM" followed by the number text, for example 1e10000. Those requests are fhir_dose_value_1e10000, fhir_dose_value_1e30000, F28, F29, F30, F31, G01, G03, G04, G11, and G12. Before the fix, every run sent their numbers as JSON strings, including the stored version 1 results in eval/data/attack_results.jsonl, so those attacks tested a string dose and not the number in the request.

The uncommitted change to eval/attacks.py restores each placeholder to a bare JSON number before the request is sent. Compared with the replay before the reader change (commit 1a0edd4), the layer's reply on these 11 changed for six requests: fhir_dose_value_1e10000 and fhir_dose_value_1e30000 from blocked to error, G11 from blocked to error, and G01, G03, and G04 from blocked to released text. F28, F29, F30, F31, and G12 stayed blocked with the reason unbound. Compared with the replay at HEAD, which has the reader change but still sends strings, the fix changed the layer's reply on 10 of the 11: F28, F29, F30, F31, and G12 from error to blocked (unbound), G01, G03, and G04 from error to released text, and the message on fhir_dose_value_1e10000 and fhir_dose_value_1e30000. Only G11 stayed the same, as an error.

The comparison filter on the same replay releases seven of the 11: F28, F29, F30, F31, G01, G03, and G04. The stored development run blocked all seven. The development rows for version 1 and the comparison filter in Table 3 come from eval/data/attack_results.jsonl and were not rerun. The paper says so in the Table 3 caption and in Reproducing Table 3. The comparison filter's development row would change if it were rerun, and the paper does not claim otherwise.

The replay files in eval/data/replay_v21/ were regenerated with the current build. Running `python3 eval/attacks.py eval/data/replay_v21/<name>.jsonl <output file>` on each of development.jsonl, h1.jsonl, and h2.jsonl gives a results file that matches the stored file byte for byte (`cmp`). The paper's Reproducing Table 3 paragraph gives this command.

Replay counts for version 2.1, with the command behind each number (`python3 eval/attacks.py eval/data/replay_v21/<name>.jsonl <output>`, then count the layer status field):

Development, released: 3 changed to 6 (G01, G03, and G04 added). Development, refused as errors: 20 changed to 26. Development, blocked: 267 changed to 258. Development, misstatements 0 and faithful 3 changed to faithful 6.

Round h1, released: 8, unchanged. Round h1, refused as errors: 2 changed to 3 (h1_structure_03 moved from blocked to error). Round h1, blocked: 103 changed to 102.

Round h2, released: 46 changed to 45 (h2_chart_array_resource_type_medicationstatement now refused as an error). Round h2, refused as errors: 3 changed to 5 (that request and h2_chart_control_frequency_string, which moved from blocked to error). Round h2, blocked: 89 changed to 88. The 16 one-ingredient pairs are unchanged, and all 45 releases are byte-identical to version 2's releases of the same requests (checked in Python against eval/data/heldout2/*_results.jsonl). The 16 pairs are the released IDs listed in Labels, and all 16 are still released.

Round h2, the nine misstatements under version 2.1 are still blocked eight times and refused once (h2_chart_bundle_and_array_same_id_conflict), and the four unsupported-claim outputs are still blocked. Of the 73 faithful outputs of version 2, version 2.1 now releases 45, so 28 are not released. Those 28 are the 20 omitted-order blocks, four count-dose blocks, two timing or course blocks, one Important block, and the MedicationStatement refusal. The paper's Version 2.1 paragraph says 28 and gives the breakdown.

## New labels

Three labels were added to eval/data/replay_v21/labels.json, which now holds 30 entries (27 before this pass). The new labels are G01, metformin 0.000000001 mg by mouth once a day; G03, metformin 0.5 mg by mouth twice a day; and G04, metformin 500 mg by mouth once a day. Each has reader1 faithful, reader2 faithful, third_reader null, label faithful, corpus development, a reasons list with both readers' reasons, and a note that the label was set in review round 10 after the raw-number fix. Each chart has one active order, so none of the rule's two patterns applies to them.

Of the 30 labels, 14 are for texts version 2.1 releases (E09, G15, G17, G01, G03, G04, and eight round-h1 texts), 16 are for texts that version 1 released and version 2.1 blocks, and one is misstates_order (F05), as before. The Labels paragraph gives these counts.

eval/label_rule_sweep.py reads that file, and its first run after the label change failed on the G01 chart, because json.loads read the placeholder for 1e-9 as a string. The script now restores the placeholders before parsing, with a RAW_NUMBER pattern that matches the one in eval/attacks.py (command: `python3 eval/label_rule_sweep.py`). The rerun scanned 1,109 labeled outputs, up from 1,106, and returned the same 91 matches as the earlier file (52 with two active orders for one drug name or ingredient, and 39 with one repeated instruction), with 0 in conflict after relabeling. The earlier file eval/data/label_rule_sweep.json was overwritten by this rerun. eval/labels.py does not read replay_v21/labels.json, so eval/data/labels_summary.json was not regenerated.

## Labels

Coded timing counts (confirmed). eval/data/coded_timing_check.json gives 1,069 orders with the phrase "Every four to six hours (qualifier value)". Of these, 455 have one milligram strength in the display name and 614 do not. The 1,077 coded orders without a single strength are the 614 plus 323 six-hour and 140 four-hour orders. The five coded phrases sum to 1,946 raw orders (455 + 614 + 323 + 140 + 221 + 193). Limits uses these groups.

Same-name outputs in round h2 (confirmed). eval/data/label_rule_sweep.json has five round-h2 outputs with reason "same name": h2_meaning_07_control_case_metformin, h2_clinical_09 (prednisone), h2_clinical_12 (levothyroxine), h2_meaning_06_hyphen_split_met_formin, and h2_structure_28. The last two are also among the 16 one-ingredient pairs. The Labels paragraph lists all five and says which two appear in both counts.

Stale PDF and Word files (confirmed in the first pass, stale now). The first pass rebuilt paper/dosegate.pdf and paper/dosegate.docx from paper/paper.md, and those files then said 38 in 74 and 23 in 128. This pass changed paper/paper.md again, so both files are out of date and were not rebuilt. They must be rebuilt before posting.

The Llama relabels and the existing rubric (confirmed). The model-output rubric in eval/labeling_protocol.md already lists "tells the patient to take an instruction twice" as misstates_order. Reader 1 and the third reader labeled Jack927, Corinne382, and Julia241 faithful before this round, so those labels were reader errors under that rubric. The development and held-out rubrics did not list repeated instructions, so rule (2) extends them. The Labels paragraph and the protocol now say this. The 48 figure is described as the count under the labels before this round.

Counts that labels.py did not write (confirmed). eval/labels.py now has a v2_review section. It writes the Llama comparison-filter counts (171 released, 51 misstatements, 48 before this round, 44 with a duplicated instruction) and the free daily counts (MedGemma 4B: 71 flagged with 69 misstatements, 20 unflagged with 2; Llama 3.2 3B: 31 flagged with 19 misstatements, 20 unflagged with 1) to eval/data/labels_summary.json. The existing sections of that file are unchanged after the rerun.

Duplicate sentence (confirmed). The Labels paragraph had "The current script flags none of the 240 version 1 free outputs" twice in a row. One copy is deleted.

The third_reader field in relabeled rows (confirmed). In T29, T30, Jack927, Corinne382, and Julia241, third_reader held the pre-round value, faithful. Each now has third_reader set to the round 10 third reader's label, misstates_order, and the pre-round value in third_reader_before_round10. The relabel note says what each field means. labels.py counts only whether third_reader is set, so the counts do not change.

The sweep (confirmed in part). The sweep script (eval/label_rule_sweep.py) checks two patterns only: two active orders with one drug name or ingredient, and one instruction repeated for one order. Its ingredient table includes misspellings from the attack files, so it was written after those outputs were read. The count of zero conflicts after relabeling is zero by construction. The Labels paragraph and eval/data/label_rule_third_reader.json now say so. I did not check the review's statement about the review notes and the unknown-number rule, and the paper does not rely on it.

The uncommitted change to eval/attacks.py (see Raw numbers and replays). The change is still uncommitted, and it is kept. The paper's Reproducing Table 3 paragraph now describes the string-dose problem, the effect on the development rows, and the replay command.

The Table 3 reproduction command (confirmed). eval/attacks.py reads its first argument as the request file and its second as the output file, and with no arguments it reads the development corpus. The reproduction paragraph now gives the held-out command with an output path that does not overwrite the stored results. It also says that the rerun has not been done for this version.

## Code

doNotPerform and bundle entries (superseded by Reader change). The first pass found that the reader skipped malformed bundle entries and treated a non-boolean doNotPerform as inactive. Commit f8003e6 changed both: a non-boolean doNotPerform, and a bundle entry with no resource or no string resourceType, now refuse the request with an error. A bundle entry for another resource type, such as Patient, is still skipped. The paper's Trusted code and Limits sections describe the current behavior, and the probes are listed in Reader change.

The as-needed frequency sentence (confirmed). fmtFrequency in DoseGate/Fhir.lean (lines 133 to 138) prints the timing followed by " as needed", or only "as needed" when there is no timing. Probes confirm the fallback form "Take metformin 10 mg by mouth, once a day as needed." and the model-path form "Take oxycodone hydrochloride 5 mg by mouth once a day as needed." The paper now gives the rule and both examples.

The omission count in round h2 (confirmed). The request has nine orders with status active, but m8 has intent plan. A probe that named m8 in a slot returned inactiveOrder, so the reader treats m8 as inactive. Eight orders are active, the released text names three, and five of the eight active orders were omitted. The paper, eval/labeling_protocol.md, and the round 4 response (paper/response_round4.md, computer science item 4) now say five of eight. The round 4 response carries a dated correction.

The protocol-as-written counts (confirmed). The figures 90 and 88 use F05 as adopted (misstates_order). The figures 89 and 89 use F05 faithful, which the protocol as written would give. The Labels paragraph names the F05 setting in each sentence.

Line counts (confirmed, updated). Json.lean has 580 lines and 487 non-blank lines, and Main.lean has 234 lines and 207 non-blank lines. The paper now gives 694 non-blank lines for the reader and command-line code together, and 487 and 207 separately. Trusted code and the Conclusion use the non-blank count. The first pass gave 393 for the reader, which was before commit f8003e6.

Repeated sentences in Limits (confirmed). Limits had repeated the doNotPerform rule and the noActiveOrder rule from Trusted code. Those sentences are removed. Limits keeps a pointer to Trusted code and adds the bundle skip as a gap.

The order of block checks (confirmed, with a change to the suggested wording). Render.lean (lines 160 to 172) runs the omittedOrder check before the slot checks. The slot checks give inactiveOrder and unknownRef, and the noActiveOrder check runs last. The suggested sentence left out the omittedOrder step. The Design paragraph now lists the checks in order, and the completeness sentence names omittedOrder as the block reason.

The release tag (confirmed, updated). The first pass cited commit cce8a35 and the tag v2.1.0, which names a09970f. The Availability paragraph now names release v2.1.0, the git tag v2.1.0, and says the tag is moved to the final commit of each revision. The paragraph has no commit hash. The tag itself has not been moved in this pass. The tag v2.1.0 is an annotated tag object (ee8e907) that names commit a09970f, so `git rev-parse v2.1.0` prints the tag object and `git rev-parse v2.1.0^{commit}` prints a09970f. Moving it to the commit that carries this round is part of committing (see Open items).

## Text

Numerals for the round h2 misstatement count (confirmed). The Abstract says "all 9" now, and Results and Limits use 9 where the count is misstatements. The Abstract is 1,915 characters, under the 1,920 limit, and paper/arxiv_submission.md has the same text.

Thousands in prose (confirmed). The Labels paragraph and the Limits metformin split example now read 1,000 mg and 1,500 mg. Printed output is unchanged.

The 99 faithful labels (confirmed). The round h2 comparison filter has 99 faithful labels in eval/data/labels_summary.json. Of these, 19 are one-ingredient outputs, which Table 3 counts separately, so 80 are faithful in Table 3's sense. The response now says so.

The 40 and 53 counts (partly confirmed). The rule change explains 41 to 38 and 54 to 51. It does not explain the reviewer's 40 and 53, and I could not find a basis for those two figures in the labels or the paper. The response no longer says the rule accounts for them. If the reviewer used another rule, the reviewer should name it.

The 455 sentence in the earlier response (confirmed). The earlier version said 455 of 1,069 orders print, which mixed two groups. It now says 455 of the 1,069 have one strength and print, and the other 614 were not tested in that form.

The round 10 wording (confirmed). The Table 3 caption and the Labels paragraph now say "the labeling addendum dated November 5, 2026." The protocol file keeps its own dated heading.

## Build check

The PDF and Word files were not rebuilt in this pass. The first-pass build check is superseded, because paper/paper.md changed again. Rebuild with the personal-brand-docs build scripts before any file is posted.

## Changes made

paper/paper.md: Abstract (46 changed to 45 in the replay sentence, and round-h2 added before the replay releases; "labeling protocol" shortened to "protocol" in the F05 clause so the abstract stays at 1,915 characters). Trusted code (reader refusal rules, 694 non-blank lines, timing rule, 260 regression tests). Evaluation methods (Models and conditions: reader rules change no decision; Labels: 30 labels, 14 released, three new labels; Reproducing Table 3: raw-number change, string-dose disclosure, replay command). Version 2.1 (45 and 29 faithful, 28 blocked or refused with the MedicationStatement refusal, 6 development releases). Table 3 caption (refusal counts 26, 3, and 5; disclosure of the development rows). Table 3 rows (development version 2.1 replay 6 and 6; round h2 version 2.1 replay 45 and 29). Reproducing Table 3 also gives the current-build comparison filter counts: development 215 (7 newly released, 10 newly blocked, 17 changed in all), round h1 93, and round h2 107, against the stored 218, 104, and 128. Trusted code and Limits state the null-key rule, the near-miss resourceType skip, and the bundle type rule, and the wrong-typed reader rule now names the fields it checks. Doses given as counts are described as blocked with missingField, not refused, in the Design and Limits sections, and the 2.1 list names the block. Limits (bundle sentences rewritten, unknown keys added). Conclusion (694 lines). Availability (release v2.1.0 and the tag, no commit hash). Earlier first-pass changes stay in place.

paper/arxiv_submission.md: abstract with 45 in place of 46, round-h2 added before the replay releases, and "against the protocol" in the F05 clause. The abstract is 1,915 characters and identical to the paper's abstract.

README.md: Use section (the reader refusal rules and the null and Patient rules), the --allow-omissions option (the only option that lets an active order go unnamed without a block), and the replay command in Reproducing the evaluation.

eval/data/replay_v21/labels.json: three new entries, G01, G03, and G04, with reasons and a note (30 entries).

eval/label_rule_sweep.py: parse_request restores the raw number placeholders before json.loads (RAW_NUMBER pattern). The sweep output eval/data/label_rule_sweep.json was regenerated: 1,109 outputs scanned, 91 matches, 0 in conflict.

README.md: in this pass, the wrong-typed field list, the count-dose sentence, the null-key rule, and the near-miss resourceType rule in the Use section.

The files below were changed or added in the round as the Labels section describes them. The diff does not show which of them changed in round 10 and which changed earlier, so the author must confirm before staging.

eval/labeling_protocol.md: round 10 addendum dated November 5, 2026 (two active orders for one drug, one repeated instruction, and identical orders each given once).
eval/labels.py: v2_review section.
eval/data/labels_summary.json: regenerated from the label files.
eval/data/attack_labels.json: relabels of T29 and T30 with third_reader_before_round10 fields.
eval/data/v2_review/labels.json: relabels of Jack927, Corinne382, and Julia241 with third_reader_before_round10 fields.
paper/response_round4.md: correction to the round 4 response.
eval/data/label_rule_third_reader.json: new file, third-reader labels and reasons for the 12 relabeled outputs.
eval/coded_timing_check.py and eval/data/coded_timing_check.json: new files for the coded-timing check cited in Limits.

paper/response_round10.md: this file.

Not changed in this pass: the Lean files (DoseGate and Main.lean), tests/, eval/attacks.py (its change was already in the working tree), eval/generate.py, eval/models.py, .gitignore, the paper PDF and Word files (stale, see Open items), the paper's docs/ folder, the held-out and development request files, the stored results, and the replay result files. Nothing is committed or staged.

## Open items

The clinical pharmacist check of the 16 same-ingredient pairs has not been done.

The paper's PDF and Word files are out of date and must be rebuilt (see Build check).

The tag v2.1.0 still names commit a09970f (through the annotated tag object ee8e907). It must move to the commit that carries this round when the round is committed, and then the Availability sentence will be accurate.

The development rows for version 1 and the comparison filter in Table 3 come from a stored run that sent 11 numbers as strings. They were not rerun, and the comparison filter would release seven of those requests if it were rerun.

No held-out round has been run against version 2.1, and the reader rules added in commit f8003e6 were tested only with the probes and the regression tests listed above.

Nothing is committed or staged. The working tree still holds the other sessions' uncommitted changes, which this pass did not touch.


## Final reader change in this round

The round 10 checkers found that a bundle entry whose resourceType was a near miss of MedicationRequest (for example "medicationrequest" or "MedicationRequest " with a trailing space) was skipped as another resource type, so its order was left out without a block. The reader now accepts a bundle entry only when its resourceType is one of the 145 FHIR R4 resource type names (https://hl7.org/fhir/R4/resourcelist.html); any other value makes the request an error, and valid other types such as Patient and MedicationStatement are still skipped. Raw tests cover a lowercase type, a trailing space, the typo MedicationRequests, a Patient entry, and a MedicationStatement entry beside an order. The suite now has 265 tests, the reader has 525 non-blank lines, and the reader and command line together have 732. The fuzz test agrees on all 20,000 requests, the three evaluation re-gates changed no decision, and the replays changed no decision relative to the state described above. These replace the counts of 260, 487, and 694 given earlier in this response.
