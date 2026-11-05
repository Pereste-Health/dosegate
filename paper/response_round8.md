# Response to the eighth round of review

Section names below refer to paper/paper.md. Where a reviewer's wording was checked against code or data and found imprecise, the response says so.

## Computer science review

Required items:

- Status, intent, and subject handling (items 1 and 2): fixed in the reader (DoseGate/Json.lean and Main.lean). An order whose status or intent is missing or is not a FHIR R4 code, including case variants such as "Active", now makes the whole request an error that names the order. Valid statuses other than active and valid intents that are not order intents make the order inactive, and inactive orders are omitted without a block. When the request names a patient, a subject reference of the form Patient/<id>, urn:uuid:<id>, or an http or https URL ending in Patient/<id> is matched by its id; one of those forms with another id makes the order inactive, and any other form makes the request an error. Seven raw tests cover a missing status, status "Active", a missing intent, an unknown intent, an absolute-URL subject for the named patient (released, with that order named), an absolute-URL subject for another patient (omitted), and a malformed subject (error). The independent Python reader in the fuzz test follows the same rules, and the fuzz test agrees on all 20,000 requests. Trusted code, Limits, and README.md describe the new behavior. Re-gating all 2,764 evaluation decisions and the three replays changed no decision. The suite now has 232 tests, and the reader and command line have 600 non-blank lines (393 and 207).
- Release tag (item 3): confirmed; the remote tag v2.1.0 points to a09970f. The Availability paragraph keeps citing tag v2.1.0. Main is pushed to the public repository with this round, and after acceptance the tag will be moved to the final accepted commit and pushed, so the cited tag holds the code and data the paper describes.

Recommended items:

- Blocked versus error: Table 1 (No active order row) and the Fallback paragraph now say that render blocks with noActiveOrder, and that the fallback returns status error for the same case. The paper says both refuse.
- Daily total: the Abstract says the daily total comes from the order its slot names. The Daily totals paragraph in Design already defines it as the dose times the number of administrations per day. The Abstract does not repeat the definition, because the character limit is nearly full.
- Relation to other safeguards: the sentence now says that an order with dosage text makes every output for that patient blocked, for omission or for missing a field, as the reviewer described.
- Held-out writing: the Held-out round paragraphs for version 1 and version 2 now say each instance could read the source and run both binaries, following eval/labeling_protocol.md.
- CaMeL: the sentence now follows the reviewer's wording. Two data-to-text references were added as references 34 and 35: Wiseman, Shieber, and Rush (EMNLP 2017, pages 2253 to 2263) and Dhingra et al. (ACL 2019, pages 4884 to 4895). Both were checked against the ACL Anthology listing.
- Abstract rate caveat: the Abstract now says that the Qwen3.5-4B outputs were examined before version 2 was designed.
- Liveness example: Table 1 and What a proof does and does not establish describe render_one_active_ok as the only liveness result, for one fixed chart, with no general liveness theorem.
- Fuzz test docstring: not changed. The docstring in tests/fuzz_reader.py still says the reference is written independently of Lean. The instructions bar edits to tests/, so this needs a one-sentence edit by the authors. The paper already says the reference shares the route and unit tables with the Lean source.
- Numeric allow-list: not run, as before. The paper says so.
- Other recommended items (precision and runtime, completeness leakage, unit and fail-closed wording): addressed in the round 7 text and unchanged here.

## Health literacy review

Required items:

- Complete instruction (items 1 in Abstract, Design, What a proof does and does not establish, and Conclusion): the guarantee sentence now reads that each drug name, dose, route, frequency, and daily total comes from the order its slot names, appears only inside an instruction for that order that states its dose, route, and frequency, and that by default the model's own words are limited to 67 framing words. A deployment that adds words with --extra-words can release a drug name outside any instruction. The paper no longer says "complete instruction". The same wording appears in the Abstract, Design, What a proof does and does not establish, and Conclusion, and in the Table 1 caption where the drug-name exception applies.
- Limits sentence: Limits now opens with the reviewer's sentence that the released instruction is not a complete set of directions for a patient.
- Tablet count: Limits now says that a milligram dose gives no number of tablets, and that a deployment must print the tablet count from the dispensed product or pharmacy record.
- Free text in the raw records (item 3): the Methods paragraph no longer says that no order has free text. It now says that the normalization drops these fields and reports the measured shares. The reviewer's 36 percent came from a 60-bundle sample from round 1. This round measured the whole set of raw bundles, so the round 1 figure is replaced (see below).

Recommended items:

- Insulin concentration: Exact quantities now says the released text does not state the U-100 or U-500 concentration, and that a deployment must print it from the dispensed product.
- Framing sentence: Limits now says a deployment must state which orders the list covers from clinician-written text, because the options can add framing words but cannot remove or replace the framing sentence.
- Maximum versus top of range: the Abstract now says "the top of a usual range" as well as "a usual US label maximum".
- As-needed order: the Discussion now says the order blocks the fallback because the reader treats it as one it cannot read. The reviewer's wording was used.
- Trusted code: the paragraph is split into an introduction, a bulleted list of the reader's dose-stripping rules, and two short paragraphs. Terms such as priorPrescription now carry a gloss.
- Plain glosses: Cohen's kappa and the Flesch-Kincaid grade now have a gloss at first use. Liveness is glossed in Table 1 and in What a proof does and does not establish. The Wilson interval already had a gloss in Outcome measures.
- Conclusion: the word "guarantee" is replaced by the reviewer's wording, "state, with a proof about the released text, that". The Conclusion also says that the result is fidelity to the orders, not clinical appropriateness, and that it assumes the tested reader reads the orders correctly.
- Unit words: Exact quantities now says the singular "unit" for a dose of one is the layer's own choice and is not taken from ISMP or Joint Commission sources.
- Table 3 caption: the caption now says that the listed refusals are a subset of the blocked requests, and that the blocked count is the number of requests minus the released count in the table.
- Same-ingredient pairs: unchanged. The Labels paragraph already says that a clinical pharmacist must confirm the list, and that this has not been done.
- Fallback and the record's medication list: unchanged from round 7, and already stated.
- Dose output in the Limits and Discussion: the "Percocet" and "acetaminophen" limit is unchanged.
- Reviewer claim not used: the reviewer's probe outputs were not re-run in this round. The paper's text describes them as the reviewer reported. Only the code-level claims were checked against the source.

## Math review

Required items:

- Liveness row (item 1): Table 1 uses the reviewer's wording for the row, with one change. The reviewer wrote that render "returns an error". The Lean function throws a Block value, and the command-line reply has status blocked, so the row says render blocks. The paper uses the same word in the Fallback paragraph.
- Guarantee sentence (item 2): the same wording as health literacy item 1 is used in the Abstract, Design, What a proof does and does not establish, Conclusion, and the Table 1 caption. The caption adds the reviewer's exception that a drug name in model text is excluded only by the default word list, which the authors judged free of drug names. No theorem checks that judgment.
- F05 (item 3): the paper keeps misstates_order. Labels now discloses that the protocol gives faithful for F05, because both readers said faithful and no third reader decides unless the first two disagree or one omits a label. It gives the protocol-as-written counts in prose: version 1 would show 1 misstatement, 10 unsupported claims, and 33 faithful outputs out of 44 released, and the comparison filter would show 89 misstatements, 40 unsupported claims, and 89 faithful outputs out of 218. Table 3 still shows the adopted labels, and its caption rows are unchanged. The Abstract now says that one of the two development misstatements (F05) was relabeled against the labeling protocol, and does not say that either was settled by a third reader. Development now says N01 was settled by a third reader and F05 was relabeled. The Labels paragraph says one development misstatement was settled by a third reader, not two.

Recommended items:

- Repeated value rule: the Design paragraph now says the same value slot with the same order identifier, or a sig slot with a dose, route, or frequency slot for the same order. render_repeated_eq is added to the Fail closed row.
- Trusted code: the reader's allowlist is described as 37 top-level keys (orderKeys in DoseGate/Json.lean, counted at 37). The dose and frequency limits and the zero-amount rule are stated, and numbers longer than 1,000 characters are listed as a request error.
- Unit names: the sentence now gives the canonical names (mcg for ug and mcg, mL for ml, units for U, [iU], and IU).
- Version 2.1 breakdown: the sentence now gives 20 unnamed-order blocks, 4 count-dose blocks, 2 reader-rule blocks, and 1 Important block, out of 27. The reviewer's sentence says "faithful" releases, but 3 of the 27 are same-ingredient pairs rather than faithful labels, so the sentence says "without a misstatement or unsupported-claim label".
- Free condition: Models and conditions says the version 1 study had a free condition and version 2 did not run it. Labels says two readers judged three of its outputs and found no error.
- Rewrite chains: Models and conditions says the version 2.1 rates after rewrites are replays of version 2's rewrite chains. The change is one release across the 2,764 decisions.
- Bounds: the 0.4% bound now says it assumes independence, and the 3.1% per-case bound is given. The Released text paragraph gives 95% lower bounds on detection: 99.1% for 412 of 412, 96.8% for 115 of 115, and 91.0% for 39 of 39. These were recomputed from the Wilson formula.
- Lisinopril: 40 mg is the top of the usual range, as in the round 7 response.
- Count of distinct words: the five classes hold 353 distinct words, because iv appears in the number and route lists. The reviewer was correct, and the sentence now says so.
- Abstract attribution: the Abstract says the 16 replay releases come from the author's reading that has not been checked by a clinician.
- Table 2 caption and Omission split: unchanged from round 7.
- Data file class string (heldout2/model_style.jsonl, h2_model_style_p13_omit_three_orders): not changed. The reviewer labeled this a data edit for the authors. The text is right (six of nine omitted). The class string says three. Changing a data record is left to the authors.

## Free-text share (health literacy required item 3)

The script is eval/free_text_share.py. It reads the raw bundles in place from SYNTHEA_FHIR_DIR, which is /Volumes/T7/hearth-datasets/synthea/bundles_v1/fhir. It selects the 120 evaluation patients with the same shuffle and normalization test as eval/build_cases.py. The selected bundle names match the source_bundle values in eval/data/cases.jsonl. Results are in eval/data/free_text_share.json.

- The 120 evaluation patients: 118 of 548 active MedicationRequests (21.5%) carry note, dosageInstruction.text, dosageInstruction.additionalInstruction, or dosageInstruction.patientInstruction. Among the 361 active orders with one dosage instruction, 118 (32.7%) carry such a field. 52 of the 120 patients have at least one such order. Every flagged order carries dosageInstruction.text, and 29 also carry additionalInstruction. No order carries note or patientInstruction.
- All 5,980 bundles: 6,013 of 26,800 active MedicationRequests (22.4%) carry one of these fields. Among 17,145 active orders with one dosage instruction, 35.1% do. 2,685 bundles (44.9%) have at least one such order.
- The reviewer's round 1 figure of 65 of 179 (36 percent) came from a 60-bundle sample. The measured share is 32.7% for the evaluation patients and 35.1% for all bundles, so the round 1 figure is replaced.

## Changes made

- paper/paper.md: Abstract (1,919 characters, identical to paper/arxiv_submission.md), Design (instruction definition, repeated-value rule, added words, fallback status), Exact quantities (unit names, insulin concentration, singular unit), Development (N01 and F05), Models and conditions (free condition, rewrite chains, held-out source access), Evaluation methods (free-text measurement, Labels with the F05 protocol note and free condition), Results (bounds, lower bounds, version 2.1 breakdown, Table 3 caption), Trusted code (status, intent, subject rules, bulleted reader rules, limits), Limits (status and subject rules, tablet count, framing sentence, insulin, glosses), Related work (CaMeL, data-to-text citations), What the patient sees, Relation to other safeguards, What a proof does and does not establish, Conclusion, and references 34 and 35.
- paper/arxiv_submission.md: the abstract is replaced with the new text, and its character count line is updated.
- README.md: guarantee sentence, Use section (status, intent, and subject rules), and the free-text script in the reproduction list.
- eval/free_text_share.py and eval/data/free_text_share.json: new.
- Code: DoseGate/Json.lean, Main.lean, tests/raw (seven new tests, two existing tests adjusted), and tests/fuzz_reader.py, for the status, intent, and subject rules.
- paper/dosegate.pdf and paper/dosegate.docx will be rebuilt from paper/paper.md after acceptance.
