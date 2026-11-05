# Response to the first round of review

The first round reviewed the version 1 manuscript. Since then, the three additions were completed and the layer changed twice (versions 2 and 2.1), so the manuscript was rewritten. This note maps each required issue from the first round to the change that addresses it. Recommended issues are addressed where noted.

## Health literacy reviewer

1. Disease and outcome words in the free vocabulary allowed false indication claims. Version 2 replaced the 123-word vocabulary with 70 framing words that contain no drug, disease, body part, route, timing, quantity, or negation word, and a sentence without a value slot may contain no slot at all (theorem `sentenceOk_free_no_slot`). The prompt example no longer contains an indication sentence. Design section and Appendix.
2. Conditional regimens such as a sliding scale were not treated as misstatements. The round-h2 rubric and the model-output rubric count a conditional or variable order presented as a fixed dose as a misstatement, and the drug-name rule now refuses names containing instruction words such as "sliding", "scale", and "taper", so "insulin sliding scale" is no longer printed. Labels section; Design section.
3. Brand and generic duplicates. The daily total now ends the instruction for its own order ("..., which is 1000 mg a day."), so it states the total of that instruction, not of the drug. The Discussion states the consequence for duplicate therapy and that a deployment must check it with ingredient codes. Design (Daily totals) and Discussion (Limits).
4. What the patient sees when output is blocked. New Discussion paragraph, and the README gives the fallback.
5. Drug coverage of the evaluation. Methods list all 11 drug names with counts and state that every order is oral; the Discussion names this as a limit.
6. Raw Synthea records. Methods state that no raw Synthea order yields a complete instruction under the default reader, and why the normalization was needed.
7. Distinct-text counts. Labels are now defined per output (a text with its orders) and counted per output; `eval/labels.py` reports distinct texts and kappa. Results (Agreement) and `eval/labeling_protocol.md`.
8. The test half was not held out from the vocabulary change. Version 2's vocabulary is a fixed list not derived from model outputs, all version 2 results are on the test half, and version 2.1 changed no decision on any model output. Methods.

Recommended: reading grade is now reported (Results); hourly timings given more than once per period are no longer printed; dosage site, method, and rate fields fail closed; the effect of digit-bearing drug names is stated (Discussion).

## Math reviewer

1. Distinct-text and agreement counts. Fixed as above, with kappa for every corpus.
2. One text with two labels. A label belongs to a text together with its orders; the same text can be faithful for one request and a misstatement for another. Labels section.
3. The claim that every free, free daily, and attack output contained a digit. Removed; Results say each free daily output contained words outside the slot grammar.
4. "Planted errors in every text." Rewritten: one error in each released text where the error could be applied, with counts per model.
5. The test half and the vessels change. Resolved by version 2 (item 8 above).

Recommended: the repeated-value wording in Table 1 and the Design now matches `noRepeatedValue`; Wilson intervals are described as better than Wald near 0% and 100%, with the clustering caveat; rounding is stated as half up; the subject sentence is corrected; the reader now checks the dose code system; the scoring script's leniencies are stated; the round labels r1 to r4 are defined; the outputs released only by the comparison filter were labeled by two readers; the Synthea version and the SHA-256 of `cases.jsonl` are given; the labeling protocol is published.

## Computer science reviewer

1. Rate fields read as a bolus. Dosage, dose, and rate keys are now allowlisted, so rateQuantity, rateRatio, and rateRange fail closed (tests `blocked_reader_rate_*`).
2. Distinct texts. Fixed as above.
3. Single-reader judgments. The model-output flags for MedGemma 4B and Llama 3.2 3B were read blind by two readers with a third on disagreement; Qwen3.5-4B's free daily flags come from the version 1 study, as stated.
4. The comparison filter's formatting. The Methods now say it prints drug names without the drug-name rule.
5. DoseBench figures. The figures match version 2 of arXiv:2606.04262 (230 questions, eight models), and the reference names that version.
6. Abstract mismatch and length. The abstract is 1,764 characters and is identical in the paper and in `arxiv_submission.md`.
7. Uncommitted scripts. All scripts and data are committed; the README has reproduction steps; the paper gives the layer's commit.
8. Held-out wording. Every held-out claim now names the version it was held out from, and the paper states that no held-out round has tested version 2.1.
9. Table 1's repeated-value statement. Corrected.

Recommended: latency is measured on the binary alone; related work now covers template generation, Synchromesh, LMQL, and NeMo Guardrails (references checked); the drug-name field is named in the threat model; the deployment fallback is discussed; the labels are stated to be model-assisted. A human pharmacist sample was not done and is named as a limit.

## The three additions

- Second and third models: MedGemma 4B and Llama 3.2 3B, quantized through Ollama, on the 120 test cases, with Qwen3.5-4B rerun on the same cases; runtime and quantization vary with model, as the Methods state.
- Differential fuzz test of the reader: `tests/fuzz_reader.py`, an independent Python reader written from the specification, 20,000 requests over 52 mutation kinds, all agreeing.
- Held-out adversarial rounds: round h1 against version 1 and round h2 against version 2, each frozen by commit with checksums, reported in Table 3.
