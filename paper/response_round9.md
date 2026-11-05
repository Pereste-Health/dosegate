# Response to the ninth round of review

Section names below refer to paper/paper.md. Where a reviewer's wording was checked against code or data and found imprecise, the response says so. Every number added in this round was measured by the command named, and the file that holds it is named too.

## Computer science review

The computer science review failed this round (it returned a schema test), so there is no computer science item to answer. No computer science change was made.

## Health literacy review

Required items:

- Release rate on raw records (item 1): measured. eval/free_text_share.py now tallies, for the 120 evaluation patients and for all 5,980 bundles, the active orders with free text, with their distinct dosageInstruction.text and additionalInstruction pairs, the count of each pair, the count with asNeededBoolean true, and the orders with free text whose text says "as required" or "as needed" while the flag is absent or false. The script was run with SYNTHEA_FHIR_DIR set to the bundles folder, from the eval folder. The results are in eval/data/free_text_share.json. The existing fields are unchanged, and source_directory still gives only the folder name.

The measured counts are these. For the 120 patients, 52 (43.3%) have an active order with free text, and 118 of 548 active orders carry free text. For all bundles, 2,685 of 5,980 (44.9%) have one, and 6,013 of 26,800 active orders carry free text. Of the 6,013, 4,066 (67.6%) say only "Take as needed." with the as-needed flag true. The other 1,946 (32.4%) repeat one of five coded timing phrases, and 193 of those carry the text "Every twelve hours as required (qualifier value)" with the flag false. One order gives a course note, "Take at regular intervals. Complete the prescribed course unless otherwise directed". There are seven distinct text and additional-instruction pairs in all, and none states a hold, a food instruction, or a dose limit. The reviewer's proposed figures for these counts match the measurement, and the proposed sentences were used with the measured numbers. Results (Released text), Relation to other safeguards, and Limits were changed. The Abstract now says "120 normalized slot-condition test cases", and the Abstract stays at 1,918 characters, under the 1,920 limit.

- Fallback for as-needed and weekly orders (item 2): checked with the built binary. The fallback takes no options. A run with --extra-words, --ignore-free-text, or --allow-omissions prints the usage line and exits with status 1. An as-needed oxycodone order (5 mg, once a day, asNeededBoolean true) prints "Take oxycodone hydrochloride 5 mg by mouth, once a day as needed." A weekly methotrexate order (10 mg, once a week) prints "Take methotrexate 10 mg by mouth, once a week." The guidance now appears in Fallback, What the patient sees, and Limits. The reviewer called methotrexate and oxycodone high-alert drugs. The paper does not check any high-alert list, so the text names weekly orders in general and gives methotrexate only as an example.

Recommended items:

- Unit codes for insulin: tested with the binary. The codes U, [iU], and [IU] print as "units" (and "unit" for a dose of one). The bare code IU is refused with missingField. Unit text IU with no code is refused with missingField. Unit text IU with the code [iU] prints as units. The Design sentence now lists the accepted codes and the two refused forms, using the reviewer's wording.
- Shape words: the reviewer's list named take, which, and is as extra words. Checked in DoseGate/Tokens.lean, the 67-word framing vocabulary already contains "is", and the value shapes add only "take" (instrWords) and "which" (totalWords, with "is"). The Abstract now says "plus take and which", and Design says the shape words are "take" and "which", with "is" already among the 67. The Appendix sentence was corrected in the same way.
- Table 1, No active order row: the row now cites render_no_active_default as the proof that some block occurs, and render_noActive_eq for the reason noActiveOrder when the earlier checks pass. The statement of render_noActive_eq was read in DoseGate/Proofs/Render.lean and matches.
- Table 3 caption: the caption now notes that the development rows use the adopted F05 label, which departs from the labeling protocol, and points to the Labels paragraph for the protocol counts.
- "Exactly as ordered": tested with the binary. A dose of 1.0 prints as 1 mg, 10.0 as 10 mg, 0.50 as 0.5 mg, and 1.50 as 1.5 mg. The two sentences that said "exactly as ordered" now say the value is unchanged and printed in the normal form, with the trailing zero rule stated.
- "Evaluative word" and "carefully": the vocabulary contains "carefully" (in "read carefully"), which is a manner word. Design now says so, and says that the authors judged it free of medical content, with no theorem checking that judgment.
- Per-model bound: the 3.1 percent bound now says it applies to each model, since 0 of the 120 test cases of each model has a released misstatement.
- MedGemma block count: verified from eval/data/final_gate_decisions_v2_medgemma-4b.json. All 167 missing-field blocks come from the slot conditions (slot 60, slot daily 66, temperature 1.0 41). Of these, 151 (90%) have a block detail that names a daily total, and 16 name a drug ("no usable drug"). The reviewer wrote that the other 16 were missing-dose or missing-route blocks, which the file does not show. The earlier sentence "nearly all of its blocks were daily slots" was also wrong for the whole file: MedGemma's 240 free-daily and attack blocks are all unbound or malformed. The sentence now gives the 167 and 151 counts and says that the 151 is a text match on the block detail.
- Llama 858 of 913: verified. The 913 blocked slot outputs are in eval/data/final_gate_decisions_v2_llama3.2-3b.json (885 unbound, 18 unknownRef, 10 missingField). The count of 858 comes from the generation file eval/data/generations_v2_llama3.2-3b.jsonl, which contains a drug name from the case's order list. The Results sentence now says this is a containment count, and it no longer says that each name replaced a slot.
- --allow-omissions: Design now says what the released text may leave out with the option, and that a framing sentence such as "Here is your medicine list." would then claim a complete list.
- Levothyroxine: the evaluation has one levothyroxine order, which appears once as a natural case and once as a perturbed case. Its dose is 0.075 mg in the natural case (every 60 days) and 0.0375 mg in the perturbed case (once a week). Both were printed by the binary as 0.075 mg and 0.0375 mg. The Methods sentence gave only the natural strength, so it now names the one order in its natural case.
- Same-ingredient pairs (16): Limits now says the count rests on one author's reading that no clinician has checked. The clinical pharmacist check has not been done. That check must happen before posting, and Labels still says so.
- Conclusion: the Conclusion now says that the released text has not been tested for patient comprehension, and that its reading grade came from a formula the paper calls unstable for short texts.
- Glosses: SNOMED CT is glossed as the clinical terminology that codes routes at first use in the Trusted code section. Course of therapy and repeat are glossed at their first use in the Trusted code list.

## Math review

Required items: none. The math review accepted the manuscript.

Recommended items:

- Abstract and Design shape words: see the health literacy item on shape words above. The Abstract stays at 1,918 characters, and paper/arxiv_submission.md holds the same text.
- Llama containment count: see the health literacy item above.
- MedGemma sentence: see the health literacy item above.
- The 3.1 percent bound: see above.
- Trusted frequency words: the Trusted code section now names timesWord, unitWord, and the phrase "every hour" as trusted words. It cites the proofs tw_inj and unitWord_inj, and says no theorem checks their English meaning.
- Exactly as ordered: see above.
- Table 1 and Table 3: see above.
- Evaluative word and carefully: see above.
- Round h2 metformin output: the reviewer wrote that h2_meaning_07_control_case_metformin is in neither the faithful column nor the one-ingredient column. The table is not that. The comparison filter released 128 outputs in round h2, and the labels file has 100 faithful labels for them. Subtracting the 19 one-ingredient outputs leaves 81 faithful, which is the Table 3 value. This output carries a faithful label and is not one of the 19, so it is among the 81. The Labels paragraph now says so, and says that the layer blocks it with the reason ambiguousDrug (eval/data/heldout2/meaning_results.jsonl). The issue the reviewer raised stands: a faithful label does not cover two active orders of one drug at different doses.
- Data record h2_model_style_p13_omit_three_orders: not edited, as instructed. The class field, "list omits three active orders", is the attacker's own description of the case. The paper reports the measured omission instead. The request has nine active orders, and the released text names three, so six are omitted (eval/data/heldout2/model_style_results.jsonl). The paper text already says six of nine and is unchanged on this point.

## Changes made

- paper/paper.md: Abstract (normalized cases, proved theorems, take and which, version 2.1, 867 released texts, before version 2; 1,918 characters), Design (shape words, carefully, --allow-omissions, fallback options, unit codes, normal form of doses), Methods (levothyroxine doses, raw-record free-text counts), Trusted code (glosses for SNOMED CT, course of therapy, and repeat; trusted frequency words), Results (released text with raw-record counts, bounds per model, MedGemma and Llama block counts), Table 1 (No active order row), Table 3 caption (F05 note), Labels (metformin output), Limits (same-ingredient count, as-needed fallback, weekly and extended-release orders, ignore-free-text and 193 orders, the 44.9% figure), What the patient sees (fallback for as-needed and weekly orders), Conclusion (comprehension and the 576-line count), Specification (the 576-line count), Appendix (shape words), and the raw-record percentages in Methods, Results, and Relation to other safeguards.
- paper/arxiv_submission.md: the Abstract is replaced with the new text, and the character count line now says 1918.
- eval/free_text_share.py and eval/data/free_text_share.json: the script now writes the tables of orders with free text and the as-needed phrase counts. Run with SYNTHEA_FHIR_DIR set to the bundles folder, from the eval folder.
- paper/response_round9.md: this file.
- Renumbering: the references in paper/paper.md are numbered in order of first citation. The superscript numbers and the reference list were changed together, so no reference text changed.

Not changed: no Lean file, no test file under tests/, the built binary, the data records (including h2_model_style_p13_omit_three_orders), and no commit. The PDF and Word files in paper/ were not rebuilt. The clinical pharmacist check of the 16 same-ingredient pairs has not been done.
