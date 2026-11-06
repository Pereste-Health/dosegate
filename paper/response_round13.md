# Response to the thirteenth round of review

This pass answers the three round 13 reviews (health literacy, math, and computer science). The math review accepted the paper with recommended changes. The health literacy and computer science reviews asked for minor revision. Section names below refer to paper/paper.md. Each reviewer item was checked against the code, the data files, or the built binary, `.lake/build/bin/dosegate`, before any change. Where an item could not be done, this response says why.

Nothing was committed. The Abstract is 1,920 characters, identical in paper/paper.md and paper/arxiv_submission.md, which is at the 1,920-character limit. The Availability paragraph is unchanged and still cites tag v2.1.0. The theorem counts (200: 121, 68, and 11), the test count (265), and the line counts (576, 2,074, 525, 207, and 732) are unchanged. No Lean file, Main.lean, test, Claude data file, eval/generate.py, or eval/models.py was edited. The PDF and Word files were not rebuilt. paper/dosegate.pdf and paper/dosegate.docx were already modified before this pass, and the rebuild commands are in HANDOFF.md.

The binary checks used the scripts in /Volumes/T7/tmp-dg/r13: bin13.py (request builder and runner) and t1.py, t2.py, and t3.py (the cases). Each case is named below.

## Required items

Computer science, --ignore-free-text and as-needed wording. Both facts are now stated in Limits, in Relation to other safeguards, and in README.md.

The first fact is that the 193 raw orders with the text "Every twelve hours as required" and asNeededBoolean false still block under the option. An earlier inspection of the raw bundles found that each has a drug name with digits, no route, and a dose with no unit, and that its doseAndRate element carries a type key, which makes the dose unusable. The bundles are not on this machine, so that field-level description was not rechecked in round 13. The stored result is eval/data/coded_timing_check.json, where raw_orders_as_recorded lists 193 orders, all blocked with missingField. The Synthea source bundles are not on this machine (SYNTHEA_FHIR_DIR is unset and no fhir folder exists under /Volumes/T7), so the raw check was not rerun. The binary test below uses a metformin order with the same fields and free text, not the Synthea records themselves.

The second fact is that an order of this kind with usable structured fields prints as a scheduled dose. A metformin order of 500 mg by mouth, once every 12 hours, with asNeededBoolean false and that free text, blocks by default with missingField and returns "Take metformin 500 mg by mouth every 12 hours." with --ignore-free-text (t3.py, case A). The option therefore must not be used on records of this kind unless each order's free text has been checked against its structured fields.

One test in this pass gave a misleading result. The first run put asNeededBoolean at the top level of the order, where the reader does not read it and an unlisted order key removes the dose. The reader takes that field from the dosageInstruction element (DoseGate/Json.lean, jAsNeeded), and the test was rebuilt that way. Case A in t1.py now uses the same nested placement, so the default blocks with missingField and --ignore-free-text prints the metformin line, matching t3.py case A.

Health literacy, insulin route. The insulin example in Limits used the oral route, which printed "by mouth" for insulin. It now uses the subcutaneous route (SNOMED CT 34206005). With the built binary, insulin regular 20 units, three times a day, subcutaneous, returns ok with "Take insulin regular 20 units as a shot under the skin three times a day." (t1.py, case B). The same order by mouth returns "by mouth", as expected, so the example now says which route the record gives.

Health literacy, Claude flags in the Abstract. The Abstract now gives the 46 and 28 Claude free-text flags. The old sentence read "Asked for daily totals in free text, Qwen3.5-4B, MedGemma 4B, and Llama 3.2 3B misstated an order in at least 16, 71, and 20 of 120 test outputs." The new sentence reads "Asked for daily totals in free text, three open models misstated an order in at least 16, 71, and 20 of 120 test outputs, and two Claude models had 46 and 28 unlabeled flags." The model names remain in Results. To stay at 1,920 characters, these other Abstract changes were made, and each is listed under Changes made. The clinician caveat is kept as "(unchecked by a clinician)". The flag counts (46 and 28) come from the audit function in eval/score.py. The round 13 math and computer science reviews both reproduced them from the stored Claude generation files.

Temperature of the Claude runs (task item 4). eval/generate.py sends no temperature on the Anthropic path (anthropic_backend, lines 104 to 118, where messages.create is called without a temperature argument), and it records "api default (temperature not sent)" as the sampling. The Messages API reference (platform.claude.com/docs/en/api/messages) was read in full from its Markdown source, 1,296,513 characters, and it has no temperature entry: the words temperature, top_p, and sampling do not appear in it. The Anthropic glossary (platform.claude.com/docs/en/about-claude/glossary) says only that temperature controls randomness, with no numeric default. So this paper does not state a numeric default, and the reviewer's value of 1.0 is not confirmed. The Claude runs paragraph now says that each Claude output is one sample at the API's default sampling, and it does not say whether the runs were greedy, because the default is not stated in the pages checked. The Models and conditions sentence that said "All other generations used greedy decoding" now says "All other open-model generations used greedy decoding; the Claude runs are described below." The temp field in the two Claude data files reads 0.0, and the paper and README say it is a placeholder.

## Recommended items

Health literacy, daily totals with the option. Limits now gives the daily total for the 455 orders printed under the option. At six doses a day, which an interval of four hours would give, the 376 orders with a 325 mg dose would total 1,950 mg a day, and the 79 orders with a 400 mg dose would total 2,400 mg a day. Binary: a 325 mg dose at six times a day prints "which is 1950 mg a day," and a 400 mg dose prints "which is 2400 mg a day" (t1.py, case D). The four-dose total of 1,300 mg (325 mg at four doses) was checked (case D4). The counts 376 and 79 come from eval/data/coded_timing_check.json.

Health literacy, basal and mealtime insulin. Limits now says that insulin glargine with insulin lispro returns ambiguousDrug on both the model-text path and the fallback, so the layer gives that patient no text by either path, and the deployment must route the patient to a pharmacist (t1.py, case C).

Health literacy, the taper pair. Labels now says why h2_clinical_10 (prednisone 20 mg and Deltasone 40 mg, both once a day) is labeled faithful. The request has two ordinary orders with no taper marker. The file eval/data/heldout2/clinical.jsonl gives the request, and the taper appears only in the class label.

Health literacy, labeler for the Errors in free text flags. The Errors in free text paragraph now says that one of the 16 development flags was labeled by the author's main session, which was not blind. It also gives the 11 single readings in eval/data/free_text_labels.json, which are one development flag and ten unflagged outputs with a weekly order. The MedGemma 4B and Llama 3.2 3B labels are described as two labelers with a third labeler settling each disagreement, as eval/data/v2_review/labels.json shows.

Health literacy, Introduction caveat. The Introduction now says that the printed wording has not been tested with patients, and that it uses clinician abbreviations such as mg and mcg (see Conclusion).

Health literacy, bare "Take as needed." The Released text paragraph now says that the default rule treats the bare phrase "Take as needed." with asNeededBoolean true as free text, so a patient with one such order receives no output, and that a deployment may accept the exact phrase after clinical review. The statement was checked with the binary: default blocks with missingField (t3.py, case P1). The paper does not compute the share of bundles that would remain blocked under that rule. The 4,066 count comes from eval/data/free_text_share.json, all_bundles, where asNeededBoolean_true is 4,066.

Health literacy, acetaminophen label maximum. No DailyMed label was checked in this pass, so no number was added. Limits now states that the authors have not checked the US acetaminophen label maximum and that the 5,900 mg figure has no labeled reference point. The old parenthetical read "(together these can exceed the daily maximum on the acetaminophen label, which this paper does not cite)". The new one reads "(together these can exceed a daily acetaminophen maximum; the authors have not checked the US acetaminophen label maximum, so the 5,900 mg figure below has no labeled reference point)".

Math, F05 counts. Labels now says that the 89 and 89 comparison-filter counts give F05 labeled faithful and also revert the addendum relabels of T29 and T30. F05 alone gives 91 misstatements and 87 faithful, from the 92 and 86 in Table 2, and reverting the T29 and T30 addendum changes alone gives 90 and 88. The parenthetical now names the adopted starting point and gives both figures. The version 1 development count is also given in Table 2's caption: 2 under the adopted labels and 1 under the protocol as written.

Math, Table 2 and the 69 blocked outputs. The caption said "Version 2.1 blocks all 69 of these outputs on replay." It now says that version 2.1 blocks the request behind each of these 69 outputs, with the reason omittedOrder or unbound. eval/omissions.py prints 6 (round h1, version 1 layer), 11 (round h1 comparison filter), 19 (round h2 layer), and 33 (round h2 comparison filter), which sum to 69. The round h1 and round h2 reasons are omittedOrder or unbound, and no output is released.

Math, Abstract stored count. The Abstract now says "against 23 in 128 (stored) for a filter". The current build releases 107 of 138 for that filter (replay_v21/h2_results.jsonl), so the 128 is a stored run.

Math, Table 1 daily totals. The statement cell now says "A daily slot lies in a sentence that also contains that order's dose, route, and frequency or its sig". The old phrase was "A daily slot occurs only in a sentence that also contains". The Lean theorem render_daily_sentence proves only that some such sentence exists, so the statement now matches it.

Math, Table 1 no daily total. The reviewer asked for a Lean theorem that dailyDose? is none for weekly and monthly timings. Lean files may not be edited in this pass, so the row now gives the link instead. The statement cell adds: "For weekly or monthly timings, dosesPerDay? is none (dosesPerDay_none_long), and dailyDose? is none because it is defined through dosesPerDay?." The definition is in DoseGate/Fhir.lean, function dailyDose?, which calls dosesPerDay? first.

Math, the replay relabel of F05. The reviewer's data check was correct. In eval/data/attack_labels.json both original readers labeled F05 faithful. In eval/data/replay_v21/labels.json, reader 1 gave misstates_order, reader 2 gave faithful, and the third labeler gave misstates_order. Labels and the Development paragraph now say so. The old sentence read "the replay relabeling with a third labeler gave misstates_order", and the new one reads "a later replay relabeling reopened it, with two new labelers splitting and a third labeler giving misstates_order".

Math, F05 labelers and whether they saw the version 2.1 outcome. Not resolved. The replay label file names no labeler and does not say whether the labelers saw the version 2.1 output. Labels now says that the file names no labeler. The question whether the labelers saw the output needs the labelers' record, which is not in the repository. The Abstract already says "one, F05, relabeled against protocol," which states the departure.

Math, pinned reruns at commits 59c5f32 and ef2cc98. Not done. The rerun needs builds of two older commits and a rerun of both held-out rounds, which is a new experiment. The sentence "that rerun is not recorded in this repository" is unchanged.

Math, conjunction theorem for the default policy. Not done. It needs a Lean theorem in DoseGate/Proofs/Render.lean, which this pass may not change.

Computer science, free-text labels. Covered in the Errors in free text item above. The labels for the Qwen3.5-4B flags, the MedGemma 4B flags, and the Llama 3.2 3B flags are stated separately.

Computer science, comparison-only outputs. The Agreement paragraph no longer says the comparison filter "did as well as the layer" on outputs that the labelers did not all label. It now says the labelers found no misstatement in the 7 comparison-only outputs they labeled (3 Qwen3.5-4B and 4 MedGemma 4B), that one further Qwen3.5-4B output omits the 12 hr hydrocodone bitartrate order and is unlabeled, and that the comparison filter released 51 misstatements from Llama 3.2 3B. The counts come from eval/data/v2_review/labels.json as already stated in Results.

Computer science, four drugs in the Abstract. The Abstract now says "for one of four drugs", and the body names the four (amlodipine, simvastatin, hydrochlorothiazide, and lisinopril). The count comes from eval/data/maxima.json.

Computer science, Availability commit hash. Not done. The constraint for this pass says to keep the Availability paragraph citing tag v2.1.0 as it is now. The paragraph is unchanged.

Computer science, priorPrescription. The Trusted code bullet now says "another order's priorPrescription reference is exactly MedicationRequest/<id>". The old bullet read "or another order's priorPrescription names it". The new bullet was checked with the built binary (t3.py, prior cases). With the exact form, the superseded order has no dose, and the output that names it is blocked with missingField under --allow-omissions. With the form MedicationRequest/<id>/_history/1 or urn:uuid:<id>, the superseded order keeps its dose and prints ("Take alphazol 500 mg by mouth once a day.") under --allow-omissions. In default mode each form blocks with omittedOrder, because the replacement order loses its dose. Limits gives these details, and says that no regression test uses the history form in a priorPrescription reference (grep finds no priorPrescription with a _history reference in tests/; one test, tests/raw/error_patient_named_subject_other_form.request.json, has a _history subject reference, which is a different element).

Computer science, noActiveOrder under --allow-omissions. The Design paragraph now says that the option also turns off the noActiveOrder check, so an empty or fully inactive chart can release a framing sentence, and that a deployment that uses the option must block empty charts itself. Checked with the binary: an empty list, and a single stopped order, each with "Here is your medicine list. Please ask your doctor and pharmacist your questions.", return noActiveOrder by default and ok with --allow-omissions (t2.py).

Computer science, Table 2 footnote. The footnote now separates the stored counts from the current build for the comparison filter. The old footnote read "for the comparison filter, 18 development, 1 round-h1, and 1 round-h2." The new footnote reads "for the comparison filter, as stored in the earlier run, 18 development, 1 round-h1, and 1 round-h2; on the current build, 22 development, 2 round-h1, and 2 round-h2." The current counts come from the baseline error rows of eval/data/replay_v21/development_results.jsonl (22), h1_results.jsonl (2), and h2_results.jsonl (2). The layer counts in the same footnote (26, 3, and 5) also match the layer error rows of those files.

Computer science, related work. Four references were added after checking each on its arXiv or venue page. The reviewer's list was checked, and the Vancomycert title was corrected to the title on the arXiv page.

Vancomycert (arXiv:2606.19532, Sirman et al., cs.LO, June 2026) is now in the Formal methods paragraph as reference 10. It verifies a neural network controller for automated vancomycin dosing in Rocq, with Vehicle as a back end.

PICARD (arXiv:2109.05093, Scholak, Schucher, and Bahdanau, EMNLP 2021) is now reference 19, in the Templates paragraph, for rejecting inadmissible tokens at each decoding step.

Grammar-constrained decoding (arXiv:2305.13971, Geng et al., accepted at EMNLP 2023) is now reference 20, in the same paragraph.

PAL (arXiv:2211.10435, Gao et al., arXiv preprint) is now reference 23, in the same paragraph. The arXiv page does not name a venue, so the reference gives the arXiv identifier and year only. Page numbers and DOIs were not added for any of the four, since the pages checked did not give them.

Renumbering. The other 38 references were renumbered to 1 to 9, 11 to 18, 21, 22, 24 to 42. Each citation marker was rewritten by a script (edit_paper.py in /Volumes/T7/tmp-dg/r13), and the check passed: the markers first appear in the order 1 to 42, every number from 1 to 42 is cited, and the reference list has 42 entries.

Computer science, held-out round 2 caveat. The paragraph now says that the round-h2 requests were written with the version 2 source in view, so they probe the checks as implemented. It also says that the difference between the filters (23 misstatements against 9) is 14, which is the part attributable to the text checks. Six of the nine layer misstatements came from the input reader, which the comparison filter shares, and the paragraph already said so.

Computer science, temp field in the Claude data files. The field is 0.0 in eval/data/generations_v2_claude-haiku-5-5.jsonl and eval/data/generations_v2_claude-sonnet-5-5.jsonl. Those files may not be edited in this pass, so they were not changed. The paper and README say the field is a placeholder.

## Not done

Lean changes. The math reviewer's conjunction theorem and the dailyDose? theorem were not written, because Lean files may not be edited in this pass. Table 1 uses the link to dosesPerDay? instead.

Reruns at commits 59c5f32 and ef2cc98. This needs builds of older commits and new runs of both held-out rounds. The sentence is unchanged.

Availability commit hash. The constraint for this pass keeps the Availability paragraph as it is.

Acetaminophen label maximum. No label was checked in this pass.

Claude temperature default. The full Messages API reference has no temperature entry and the glossary gives no default, so the paper states no numeric default and does not call the Claude runs greedy or not greedy.

## Open items

The F05 labelers. The replay file names no labeler and does not record whether the labelers saw the version 2.1 output. Answering this needs the labeler records or a new labeling run.

The temp field in the two Claude data files reads 0.0. Correcting it needs an edit to those files, which this pass did not make.

The Word and PDF files need a rebuild from paper/paper.md before the arXiv upload. The commands are in HANDOFF.md.

The Vancomycert reference was verified from its arXiv page, which gives the title, authors, and identifier. The page also gives a June 2026 submission date, which is the date given in the reference.

## Changes made

paper/paper.md, Abstract. Four clauses changed, and the length is 1,920 characters. "Qwen3.5-4B, MedGemma 4B, and Llama 3.2 3B" became "three open models", and the two Claude flag counts were added. "(one author's reading, unchecked by a clinician)" became "(unchecked by a clinician)". "the model's own words" became "the model's words". "relabeled against the protocol" became "relabeled against protocol". "returns no text for all 9" became "gives no text for all 9". "deliberately changed doses" became "changed doses". "the top of a usual range" became "usual range for one of four drugs". "against 23 in 128" became "against 23 in 128 (stored)". The Abstract was counted with Python len.

paper/paper.md, Introduction. One sentence added on the printed wording and clinician abbreviations.

paper/paper.md, Related work. The Formal methods paragraph gained the Vancomycert sentence. The Templates paragraph gained the PICARD and grammar-constrained decoding sentence and the PAL sentence.

paper/paper.md, Design. One sentence added on the noActiveOrder check under --allow-omissions.

paper/paper.md, Table 1. The daily slot statement and the no-daily-total statement changed, as described above.

paper/paper.md, Trusted code. The priorPrescription wording changed to "reference is exactly MedicationRequest/<id>".

paper/paper.md, Models and conditions. "All other generations used greedy decoding." became "All other open-model generations used greedy decoding; the Claude runs are described below."

paper/paper.md, Limits. Insulin example now subcutaneous. The 193-order paragraph rewritten with the binary metformin case. The priorPrescription sentences added. The daily-total sentence for the 455 orders gained the 1,950 and 2,400 mg figures. The basal and mealtime insulin sentence added. The acetaminophen parenthetical changed.

paper/paper.md, Relation to other safeguards. One sentence added on the 193 orders and the option.

paper/paper.md, Results. The bare "Take as needed." sentence gained the free-text statement. The Claude runs paragraph gained the sampling statement and the temp placeholder statement.

paper/paper.md, Errors in free text. The labeler parenthetical changed, and a sentence on the single readings and the third labeler was added.

paper/paper.md, Labels. The taper sentence for h2_clinical_10 added. The F05 sentences rewritten to match eval/data/replay_v21/labels.json and eval/data/attack_labels.json. The file naming sentence added. The Development paragraph F05 sentence changed.

paper/paper.md, Agreement. The comparison-only sentence rewritten.

paper/paper.md, Held-out round against version 2. Two sentences added on the version 2 source and the difference of 14.

paper/paper.md, Table 2 caption. The 69-output sentence changed. The footnote gained the current-build counts. The version 1 development count was added.

paper/paper.md, References. Four entries added (10, 19, 20, 23) and the others renumbered. The list has 42 entries.

README.md. The --allow-omissions line gained the noActiveOrder sentence. The --ignore-free-text line gained the warning about the 193 orders.

paper/arxiv_submission.md. The Abstract replaced with the same text as paper/paper.md. The header now reads "1,920 characters, at the 1,920-character limit".

## Checker pass

Each changed number was checked against a file or the binary. The counts were rechecked with Python. The binary cases are in the scratch folder /Volumes/T7/tmp-dg/r13 (t1.py, t2.py, t3.py). The replay counts were computed from eval/data/replay_v21/*_results.jsonl. The omission counts came from eval/omissions.py. The label changes were checked against eval/data/replay_v21/labels.json, eval/data/attack_labels.json, eval/data/free_text_labels.json, and eval/data/heldout2/clinical.jsonl. The four references were checked against their arXiv pages. The paper contains no em dashes. Theorem, test, and line counts were checked with grep and are unchanged. The citation order check passed (markers first appear 1 to 42).


## Corrections after the checkers

The raw Synthea bundles are on this machine (the SYNTHEA_FHIR_DIR folder), so the field-level description of the 193 orders was rechecked directly: all 193 have a drug name with digits, no route, a dose with no unit, a doseAndRate element with a type key, and asNeededBoolean set to false. The Limits sentences now state this without the earlier caveat. The Abstract no longer carries the word "stored" after 23 in 128; the Table 2 caption and the Reproducing paragraph give the current-build counts.
