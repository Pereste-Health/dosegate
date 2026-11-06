# Response to the twenty-first round of review

Section names refer to paper/paper.md. Two reviewers asked for minor revision and one accepted the manuscript. The required item, the insulin concentration sentences, is fixed, and every recommended item is addressed below. Where a reviewer's wording did not match the code, data, or reference page, the response says what was checked and what was written.

## Health literacy review

Required item, insulin units: made. The two sentences in Exact quantities now say that a unit is the same amount of insulin at either concentration, and that only the volume differs: 20 units is 0.2 mL of U-100 and 0.04 mL of U-500. A dose of 20 units drawn on a U-100 syringe from a U-500 vial delivers 100 units, five times the printed dose. The arithmetic is 20 units divided by 500 units per mL is 0.04 mL, and 0.2 mL at 500 units per mL is 100 units. A search of the paper, README.md, and the response files found one other statement of the wrong fact, in paper/response_round16.md. That file is a record of an earlier round, so it keeps its text and gets a correction note at the end. paper/response_round8.md describes the concentration rule without a wrong number, and it is unchanged.

Recommended item 1, the taper: made. The Limits sentence now says that the record shows two ordinary orders, so the labelers counted the pair faithful, and that the pair may have been meant as a taper. Taking both orders gives 60 mg of prednisone a day. The request class in eval/data/heldout2/clinical.jsonl reads "both active as taper steps", which supports the reviewer's reading, and the paper says that the taper use is known only from the test design. The same paragraph now also names the three other round-h2 requests with two active orders for one ingredient (h2_clinical_13, h2_clinical_15, h2_clinical_20), which the earlier wording left out.

Recommended item 2, the "which is 100 mg a day" clause: made. The Limits paragraph now says that the clause does not state that the figure is the day's total, so a patient may read it as an additional dose, and that the wording is untested. The reviewer proposed "omit it" for once-daily orders. That changes a template, not the layer, so the paper says "use a template without it".

Recommended item 3, appointment times: made. The Relation to other safeguards sentence now says the design "may apply" to laboratory thresholds, and that the evaluation does not test this. The appointment-time example is gone.

Recommended item 4, "would be taken twice": made. The sentence now says that a patient who follows both lines could take the shared ingredient twice.

Recommended item 5, the Tylenol 650 mg order: made. The parenthetical now says that h2_clinical_20 is a test input and that the paper does not claim a 650 mg every 4 hour interval is a labeled regimen. The record in eval/data/heldout2/clinical.jsonl matches the Limits text, and the 5,900 mg total is 2,000 mg scheduled plus 3,900 mg as needed.

Recommended item 6, the Introduction: made. The sentence now says that the model produces each number token by token, so a number in the prompt is reproduced by generation rather than copied from its source.

Recommended item 7, the model for the eleven free-text outputs: made. All eleven are Qwen3.5-4B outputs. Each of the eleven matches the Qwen3.5-4B free daily output in eval/data/generations.jsonl, which is the version 1 run (the generation script's default model), or in eval/data/generations_v2_qwen3.5-4b.jsonl. The reviewer wrote that all ten unflagged outputs and the one flagged output are labeled faithful. That is not so. The flagged output (Terina405, development) is labeled misstates_order and is one of the 16 development misstatements already counted. The Errors in free text paragraph and the Labels paragraph say so. The reviewer's sentence that none of the eleven changes a count is replaced with that statement.

Recommended item 8, the 467 Claude released texts: made. eval/data/v2_review/items.jsonl has 380 items, and every item is from Llama 3.2 3B, MedGemma 4B, or Qwen3.5-4B. No Claude released text was labeled, so the paper now says that no labeler read the 467 texts and that the scoring script result rests on the script alone.

## Math review

Required item, insulin units: made, as in the health literacy section. The mechanism, a volume difference that a U-100 syringe marked in units turns into five times the insulin, is stated as the reviewer gave it.

Recommended item 1, the third-labeler count: the reviewer's count is right, and the paper's count was wrong. eval/data/v2_review/labels.json has 21 items with a third-labeler decision: the 19 disagreements, the one item whose first label was not recorded (lr|v2_llama3.2-3b, Carleen42), and one comparison-filter output (bo|v2_llama3.2-3b, King743, perturbed, slot_daily). The King743 output had both readers at faithful, and the Round 18 clarification set the third labeler's label to misstates_order. The Agreement paragraph now says 21 items, and it names all three groups.

Recommended item 2, the Abstract and Conclusion daily total: made. The Abstract and the Conclusion now say that each daily total is the order's dose times its daily count, not a value of the order. The daily-total row of Table 1 and the theorem dailyDose_exact already state this. The Abstract is 1,920 characters, as the Abstract item below explains.

Recommended item 3, the sign test: made. The script that computed the counts read eval/data/heldout/labels_h1.json and eval/data/heldout2/labels_h2.json, using the adopted label of each record and pairing the layer and comparison-filter rows by request identifier. Every layer misstatement is also a comparison misstatement: 38 of 38 in round h1 and 9 of 9 in round h2. The discordant requests, where only the comparison filter misstated an order, are 13 in round h1 and 14 in round h2, and in each case the layer returned no text. There are no requests in the other direction. The exact two-sided sign test gives p = 0.00024 for 13 to 0 and p = 0.00012 for 14 to 0 (the script computed the binomial tail directly). The new sentence states that these counts describe the requests tested and do not estimate a rate. The version 1 and version 2 labels were used as stored.

Recommended item 4, the Table 2 caption: made. The caption now says that seven requests have no comparison-filter label and that G01, G03, and G04 have layer labels in eval/data/replay_v21/labels.json. I checked that those three identifiers are in that file.

Recommended item 5, the doubled-dose counts: made after reading eval/controls.py. The count is the number of outputs that contain at least one number followed by a mass unit (mg, milligram, mcg, microgram, g, or gram) whose value in milligrams equals twice the dose of the first order in the case record. A doubled amount written in words or without a mass unit is not counted. The counts 100, 37, and 114 for the three models, and 21, 6, and 20 among the 21 cases with a twice-daily first order, match eval/data/controls_v2_qwen3.5-4b.json, controls_v2_medgemma-4b.json, and controls_v2_llama3.2-3b.json.

Recommended item 6, the Claude temperature sentences: made. The Messages API reference (https://platform.claude.com/docs/en/api/http/messages/create) was read in full on November 6, 2026, in two parts. Its body parameters do not include temperature, and it states no default for one. The reference's example uses the header anthropic-version 2026-10-21. The paragraph now says the default could not be confirmed, and it does not repeat the point. The sentences were merged into two.

## Abstract (math item 2 and computer science item 1)

Both items asked for changes to the Abstract, and the Abstract must stay at 1,920 characters or fewer. The new Abstract says each dose, route, and frequency filled from a slot is the named order's value, that each daily total is dose times daily count, and that each appears only in its instruction. It says a drug name from a slot appears only in its instruction if the model's words hold no drug name, a judgment no theorem checks, and that --extra-words adds unchecked words. Every number and caveat in the old Abstract remains, and so does the lead sentence, now "Language models can misstate doses their prompt gives correctly." To make room, the Abstract names the versions directly ("Version 1 released" and "Version 2 released 9 in 86 on 138 attacks written against it" in place of "A first version" and "A redesign ... adversarial attacks against version 2"), calls the comparison a digit-and-unit filter, says "releases" for released texts and outputs, "prints" for "gets output", "via" for "through", and "4 drugs checked". It is 1,918 characters by script, and paper/arxiv_submission.md holds the same paragraph.

## Computer science review

Item 1, the drug-name claim in the Abstract: made, as in math item 2 above. The Abstract no longer states the drug-name part as a theorem result without its proviso.

Item 2, ambiguousDaily: made. A grep of the Lean sources (DoseGate and Main.lean) finds no ambiguousDaily. The string appears in eval/data/attack_results.jsonl (6 layer records) and eval/data/heldout/structure_results.jsonl (3 layer records, h1_structure_06, 09, and 10), so the stored version 1 results contain it. The grep also finds it in tests/fuzz_reader.py at line 163, in the Python reference. That file is a test, not Lean source, and the sentence says "Lean source", so the paper is accurate. The sentence was added to the Table 2 caption.

Item 3, the whitelist difference: made as a disclosure only. No whitelist-only filter was built, as the author instructed. The Comparison filter paragraph now says the layer differs from the comparison filter by its word whitelist, whose medical content is a judgment and not a proof, and that a filter with only that whitelist and the digit rule was not built. The gap therefore does not show how much comes from the proofs and how much from the whitelist. Baseline.lean line 19 confirms that the comparison filter checks digits and unit words only.

Item 4, the anthropic library version: the version is not recorded, so the paper says so and does not give one. A search of the repository found no lock file, requirements file, or pyproject that names the anthropic package. eval/generate.py imports anthropic without a version check. The run records (eval/data/generations_v2_claude-haiku-5-5.jsonl and the Sonnet file) store the model, the stop reason, the effort, the token limit, the sampling note, and the token counts, but not a library version. The generate logs do not name one either. The system Python has no anthropic package, and a bounded search of /Volumes/T7 found none. The uv cache at /Users/parker/.cache/uv does hold anthropic 2.6.0, whose dist-info directory is dated November 5, 2026, 15:36, before the Haiku run wrote its last file at 16:25 and the Sonnet run at 16:46. The run records do not show whether the runs imported that copy, so the Claude runs paragraph now gives the cache fact and still says the version is not recorded. The reference's example header (2026-10-21, see math item 6) is cited as the example on the page, and the paper says it may not match the header the runs sent.

Item 5, scripts that overwrite eval/data: made. I checked the default output path of each script the reviewer named. Most write into eval/data when run with default arguments (bootstrap.py, controls.py, fallback_rate.py, free_text_share.py, labels.py, latency.py, maxima.py, models.py, score.py, describe.py, build_cases.py, coded_timing_check.py, label_rule_sweep.py, and vocab_rxnorm_check.py). The text says so and recommends a fresh copy of the repository. vocab_rxnorm_check.py calls https://rxnav.nlm.nih.gov/REST, so it needs network access, and its stored output is eval/data/vocab_rxnorm_check.json.

## Changes made

paper/paper.md: Abstract (1,918 characters, the two new clauses added, shorter wording elsewhere). Introduction (number-generation sentence). Design, Exact quantities (insulin units). Development, Table 2 caption (ambiguousDaily sentence) and Adversarial round against version 2 (sign test). Results: Claude runs (temperature and library version sentences), Released text (no labeler read the 467 texts), Errors in free text (Qwen3.5-4B, one flagged output counted among the 16), Attack (counting rule), Agreement (21 third-labeler items), Table 2 caption (G01, G03, G04 labels), Comparison filter (whitelist disclosure), Reproducing Table 2 (fresh-copy advice, RxNav note), Limits (taper, clause, two instructions, Tylenol test input, label clause), Relation to other safeguards (may apply), Labels (Qwen3.5-4B for the eleven outputs), Conclusion (daily total definition).

paper/arxiv_submission.md: Abstract copied from paper.md, 1,918 characters.

paper/response_round16.md: correction note appended.

paper/response_round21.md: this response (new file).

Not changed: Lean sources, tests, eval scripts, data files, README.md (no statement of the wrong fact and no mention of any changed number), HANDOFF.md, docs/, paper/dosegate_jamia* files.

## Checks

The theorem count is 201 (122, 68, 11) on the working tree. On November 6, 2026, lake build DoseGate.Proofs passed and lake env lean tests/Axioms.lean printed axioms for 201 theorems, with 122, 68, and 11 in the three groups. That count is not yet in a commit: DoseGate/Proofs/Daily.lean and tests/Axioms.lean are uncommitted, and tag v2.1.0 names a commit with 200 theorems, so the commit must come before the arXiv submission. The paper contains no em dashes. Availability still cites tag v2.1.0. The PDF and Word files were not rebuilt, so they still carry round 20 text. Nothing was committed.
