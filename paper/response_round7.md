# Response to the seventh round of review

Section names below refer to paper/paper.md. Where a reviewer's wording was checked against code or data and found wrong, the response says so.

## Computer science review

Required items:

- Empty active list (render released framing text): render now blocks with the reason noActiveOrder when the default policy requires every active order and no order is active, including an empty MedicationRequest list. The check runs last in render (DoseGate/Render.lean), so every earlier block reason is unchanged. Theorems render_no_active_default, render_noActive_eq, and render_one_active_ok are in DoseGate/Proofs/Render.lean. The paper now says this in Design (Verified layer), Table 1 (new row "No active order"), Trusted code, and Fallback. The fallback still returns an error for the same case, and the paper says both refuse.
- Active definition omitted the subject rule: the Trusted code paragraph now gives the full definition (status, intent, doNotPerform, and subject reference when the request names a patient), and says that orders that are not active, including on hold, planned, stopped, or for another patient, are omitted without a block. It also says the output blocks when no order is active at all.
- Regression test count (219): changed to 225 in Trusted code.

Recommended items:

- README Use section: now says every MedicationRequest must carry a subject.reference, and that a named patient does not waive it. The README also gets the noActiveOrder and count-dose refusals, and the theorem count (200).
- Completeness-by-default leakage: Models and conditions now says the completeness default and placeholder handling in version 2.1 followed a test-half output released under version 2, so the test-half release rates for version 2.1 are not held-out estimates.
- Precision and runtime confound: Model dependence now says the three models differed in weight precision, runtime, and reasoning setting, so the difference cannot be attributed to the model alone.
- Completeness and framing sentences: covered by the required item on the empty list and the active definition.
- Fuzz test independence: Trusted code now says the Python reference shares the route and unit tables with the Lean source, so the fuzz test checks agreement with the specification, not the specification itself, and would not detect a policy choice such as silently dropping on-hold orders. The phrase "independent Python reader" is removed.
- Related work: CaMeL (reference 32) and LLM-Modulo (reference 33) are added to Verified guards, with how this layer differs. Both were checked on the web. CaMeL is arXiv:2503.18813 (Debenedetti et al., 2025). LLM-Modulo is "Position: LLMs Can't Plan, but Can Help Planning in LLM-Modulo Frameworks" (Kambhampati et al., ICML 2024, PMLR 235, pages 22895 to 22907, arXiv:2402.01817). The author lists in both references are abbreviated with "et al." and should be checked against the PDFs before posting.
- Attack sentence: now says the layer blocked every output that stated the doubled amount.
- Numeric allow-list: not run. Running it needs a new analysis that is outside this round. Attack now says that the filter was not run and the release count it would give is an expectation from the design, not a measurement.
- Abstract rate wording: the Abstract now says the 98.3%, 83.3%, and 1.7% rates are for 120 slot-condition test cases after rewrites. The statement that the Qwen outputs were examined before version 2 was designed is in Results, Released text, because the Abstract has no room for it within the character limit.
- Liveness example: added. Table 1 has a row for the liveness example, and What a proof does and does not establish says the theorems do not show that text is released, and cites render_one_active_ok, a one-order aspirin chart that releases "Take aspirin 81 mg by mouth once a day."

## Health literacy review

Required items:

- Metformin with meals: Limits now says that by default a food, time-of-day, or hold instruction blocks the output for the whole patient. The option --ignore-free-text drops the instruction and prints the line without it. A drug requiring a meal therefore prints without that instruction only when the record does not carry it or the option is set.
- Count doses (tablet with no strength): doses given as counts are refused in the reader (DoseGate/Json.lean jDose?), so the output blocks with missingField. Exact quantities and Limits both say a deployment must send strengths. The evaluation had no count doses (every strength was converted to milligrams), and the paper says so.
- Levothyroxine microgram form: Methods now says the RxNorm name gives the two levothyroxine orders as 0.075 mg, although US levothyroxine tablets are labeled in micrograms, and that a deployment must send the unit printed on the dispensed label. Exact quantities says the authors did not check the microgram rules against the ISMP or Joint Commission sources.

Recommended items:

- Abstract: now names Qwen3.5-4B's 16 test-half free-text misstatements, says two instances of Claude (not clinicians) found none in the 60-output sample, and adds that 221 of 368 released perturbed-order outputs exceed a usual US label maximum. The Abstract is 1,911 characters.
- As-needed order: Limits now gives the fallback form with the comma (the fallback prints the sig, which includes the comma), and says an order whose as-needed reason is coded blocks the output. Reader code (jAsNeeded reads asNeededBoolean only) supports this. The reviewer's comma example is the fallback output, not the render output. The render output of the same order has no comma, as the other reviewer found.
- Percocet with acetaminophen: Limits now describes the two orders together and says they can exceed the daily acetaminophen limit and cause liver injury. Version 2.1 blocks the Percocet request in round h2 only because it is given as one tablet, so the limit still holds for milligram orders.
- Fail closed: Trusted code now says "meaning it blocks the output rather than guess at an order's meaning."
- Fallback and the record's medication list: Discussion now says the record's own list is not checked by the layer and can carry the same names and text, and that a deployment must show a pharmacist-checked list or route the question to a pharmacist.
- Real records: the sentence now says real records may carry such text and the release rate on them is not measured.
- Attack sentence: rewritten as the other reviewer proposed.
- Safe but unusable system: now says a model that cannot follow the format gives a system that blocks most outputs and gives the patient no instruction from it.
- Warfarin misstatement: the Abstract says each of the two development misstatements was settled by a third reader. Development and Labels say so for N01 (Warfarin see doctor first) and F05.
- Released text, under version 2.1: the sentence now says "Under version 2.1, every released output names every active order." Table 3 caption now labels each version 2.1 count by round, and the caption says what faithful means.
- Unit abbreviations: Exact quantities says the layer prints unit abbreviations as ordered, the evaluation does not test patient-facing unit words, and a deployment for patients must decide whether to spell them out (a change to DoseGate/Units.lean and new proofs).
- Same-ingredient pairs: Labels says a clinical pharmacist should confirm the list before publication, and that this check has not been done.

## Math review

Required items:

- F05 label (conflict between eval/data/attack_labels.json and eval/data/replay_v21/labels.json): adopted misstates_order. Both F05 entries in eval/data/attack_labels.json (the layer entry and the comparison filter entry) now have label misstates_order, with a relabel_note field recording that the first labeling gave faithful with both readers, and that the replay relabeling with a third reader gave misstates_order. The comparison filter entry was also changed, because it prints the same text and the label belongs to the output; this goes beyond the single entry the reviewer named. Development, version 1 is now 290 | 44 | 2 | not assessed | 10 | 32, and the comparison filter is 290 | 218 | 90 | not assessed | 40 | 88. The Abstract, Development, Table 3, and Labels paragraph are updated. The derived summary was regenerated with the project's own script, eval/labels.py (`cd eval && python3 labels.py`), which writes eval/data/labels_summary.json. No other derived file counts these labels.
- Replay label provenance sentence: rewritten as the reviewer proposed. The check against the files confirms eleven releases (E09, G15, G17, and eight round-h1 texts) and sixteen blocked texts (fifteen development texts, all found in the version 1 development results, and one round-h1 text found in the version 1 held-out results).
- Qwen3.5-4B development free-text flags: the paper now reports 16 test-half and 16 development-half flags. The reviewer said both readers confirmed all 16 development flags. This is partly wrong: 15 were confirmed by two readers, and the sixteenth by a single reader (eval/data/free_text_labels.json, single_reader_labels, flagged by the final script). The text says so. The Abstract now names Qwen3.5-4B.
- Regression test count (219): changed to 225.

Recommended items:

- Table 1, Fail closed: the row now says renderSeg alone blocks a slot naming no order or an inactive order, and that render reports an earlier failure first.
- Table 1, dose read-back and the tokenizer paragraph: rewritten. Parsing returns a decimal with the same value, and a printed number with a decimal point never ends in 0. The "1.0 mg" statement is changed to say no printed decimal ends in a trailing zero.
- Table 1, Daily totals: lists fmtTiming_hourly_none, and says the hourly case needs a frequency of one.
- Development, version 2.1: the same-decision sentence is replaced. Across the 2,764 decisions, one output changed release (an output that omitted an order), and 23 blocked outputs changed their block reason (22 from unknownRef and one from missingField, both to omittedOrder). Checked against eval/data/final_gate_decisions_v2_*.json.
- Errors in free text, error types: the text now says each output is counted once, under the first error type in its label in eval/data/v2_review/labels.json. The breakdowns reproduce under that rule.
- Trusted code, reader limits: the dose decimal limit (more than nine decimal places, or a mantissa of 10^15 or more) and the frequency and period limit (whole numbers up to 1,000) are added to the list.
- Latency: reported in Results, Released text (0.20 ms per output over five runs, 768 outputs, median process start 22.8 ms). Checked against eval/data/latency_v2_qwen3.5-4b.json.
- Released text bounds: rewritten to say the 0.4% bound covers the kinds of error the script detects, and the 6.0% bound is at the patient level with 0 of 60 test patients.
- Lisinopril: 40 mg is now described as the top of the usual range, not a maximum. I fetched the DailyMed label. It gives 20 to 40 mg per day as the usual range, sets no explicit maximum for hypertension, and says doses up to 80 mg have been used without greater effect. The reviewer's wording is accurate.
- Table 2 caption: adds that rows count outputs, not cases, and that the intervals treat every output as independent.
- Omission split: the sentence now gives the alternative total, 31 of 86 (9 plus the 22 not already counted). Checked against the replay and label files: 25 omission blocks among version 2 releases, labeled 20 faithful, 2 unsupported, and 3 misstatements.

## Changes made to the code and data

No Lean file was edited and no test was run, as instructed. The data changes are the F05 label in eval/data/attack_labels.json and the regenerated eval/data/labels_summary.json. The round-h2 replay file (eval/data/replay_v21/h2_results.jsonl) was regenerated before this round.
