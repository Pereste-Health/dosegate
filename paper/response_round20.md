# Response to the twentieth round of review

Section names refer to paper/paper.md. All three reviewers accepted round 20. The author asked for the recommended items to be applied before posting, so every item in the three reviews is addressed below. Where a reviewer's wording did not match the code, data, or built binary, the response says what was checked and what was written.

## Health literacy review

Recommended item 1, simvastatin label limits: made. The Results paragraph on released doses above label doses now gives the co-medication limits: 20 mg a day with amiodarone, amlodipine, or ranolazine, and 10 mg a day with verapamil, diltiazem, or dronedarone. The simvastatin label was read on DailyMed on November 6, 2026 (set ID e4d8ebf3-7f9f-4725-a104-1d1bf6e6f768, revised March 2026). Section 2.1 gives the 40 mg maximum, and section 2.5 gives the two lower limits. Reference 45 records the read date. The amlodipine label section the reviewer cited was not checked, and the new text does not depend on it.

Recommended item 2, raw coded-timing orders in Limits: made. The sentence now says that none of the raw records prints under --ignore-free-text, because each lacks a route and a usable dose and blocks with missingField. It also says the 455 orders print only after the evaluation's normalization. The counts match eval/data/coded_timing_check.json: 0 raw orders print, and 455 normalized orders print.

Recommended item 3, the 455 orders in Results: made. The released-text paragraph now states that, under --ignore-free-text, in the normalized evaluation records, the 455 orders with one milligram strength print as four times a day with a daily total of 1,300 or 1,600 mg a day (376 and 79 orders). Limits gives the detail.

Recommended item 4, release as written in the Abstract: made. The Abstract now ends its label-limit sentence with "the layer releases them as written." The built binary confirms the example in Design: an amlodipine order of 100 mg prints "Take amlodipine 100 mg by mouth once a day, which is 100 mg a day." To keep the Abstract at 1,920 characters, the parenthetical "(version 2 build)" was deleted, as the reviewer proposed. Earlier rounds had asked for that parenthetical, so the author should confirm the deletion.

Recommended item 5, monthly orders: made. The Abstract and Conclusion now list monthly lines with weekly and as-needed lines. The built binary confirms the behavior: a monthly order with a daily total slot is blocked with missingField, and a frequency sentence prints "Take medroxyprogesterone 10 mg by mouth once a month."

## Math review

Item 1, the repeated-instruction example: made. The built binary returns unbound with the detail "does not match a valid sentence shape" for the literal text "Take lisinopril 10 mg by mouth once a day. Take lisinopril 10 mg by mouth, once a day." The same repetition written with slots returns repeatedValue. The Results sentence now gives both reasons.

Item 2, question and exclamation marks: made. The layer divides sentences at question marks and exclamation marks, as it does at periods, so the Design paragraph now lists both marks as sentence-split marks. The built binary returns disallowedCharacter when the mark follows a complete value sentence or sits in framing text. Inside a value sentence, the mark splits the sentence, the sentence-shape check fails first, and the reason is unbound (for example, "Take {{drug:m1}}? {{dose:m1}} {{route:m1}} {{frequency:m1}}."). Every case tested with the binary blocked the mark, so the paper's statement that the mark is never allowed in model text holds for the cases tested.

Item 3, framing sentences and the vocabulary: made. The Lean statements sentenceOk_free_no_slot and sentenceOk_free_words (DoseGate/Proofs/Shape.lean:56 and :24) take any extra word list, so the reviewer's reading is correct. The sentence now separates the Lean claim, which holds for any vocabulary, from the medical-content claim, which is the authors' judgment.

Item 4, the daily total with a weekly or monthly timing: made. A theorem dailyDose_none_long was added after dosesPerDay_none_long in DoseGate/Proofs/Daily.lean, and its axiom line was added to tests/Axioms.lean. The Table 1 row "No daily total" now cites it. The counts were rechecked: 201 theorems (grep -rhE "^theorem " DoseGate), 2,082 non-blank proof lines (was 2,074 at commit a236ca1), and the axiom run (lake env lean tests/Axioms.lean, exit 0, 201 result lines) gives 122 theorems on the three standard axioms, 68 on a proper subset, and 11 on none. The Abstract, Specification, Conclusion, README, and arXiv Abstract all carry these counts.

Item 5, the Claude temperature: made as the math reviewer proposed. The Create a Message reference (https://platform.claude.com/docs/en/api/http/messages/create) was searched in full on November 6, 2026. Its text has no temperature parameter and states no default, so the paper says the default is not stated in the reference. The page does not say that newer models reject a temperature parameter, so the paper does not say it. The generation script (eval/generate.py) sets no API version, so the paper also says that the client library's default version applied and that the version is not recorded. The computer science reviewer's web-search excerpt (default 1.0) could not be confirmed on the page and is not used. The runs' temp field still reads 0.0 as a placeholder, and no data file changed.

Item 6, the Abstract phrase about Claude instances: made. The Abstract now says "labelers found none in 60 sampled open-model releases."

Item 7, the simvastatin and coded-timing wording: made as item 2 of this section.

Item 8, the Table 1 row for repeated instructions: made. The new row "No repeated instruction" cites render_decomp_full (the released-output side, DoseGate/Proofs/Render.lean:399) and render_repeated_eq (the blocking side, Render.lean:295). The reviewer cited render_repeated_eq alone, but that theorem only states that a repeated value gives the reason repeatedValue. The released-output side comes from render_decomp_full, which includes noRepeatedValue segs = true. The row says the value-shape rule then allows at most one value instruction per order.

Item 9, a single ReleasedOk predicate: not done, as the author decided. The Conclusion and the Table 1 text keep "no single Lean theorem states that conjunction."

## Computer science review

Item 1, the model-words sentence in the Abstract: made, in shorter form to fit the 1,920-character limit. The Abstract now reads "Whether the model's words (take, which, and 67 framing words) hold a drug name is a judgment no theorem checks; --extra-words adds unchecked words."

Item 2, the Claude instances phrase: made, as in math item 6.

Item 3, Table 3 caption: made. The caption now says the test half is not held out for every row, and it gives the reason.

Item 4, Claude temperature: made, as in math item 5.

Item 5, the round-h1 nesting: made. Checked against eval/data/heldout/labels_h1.json. All 74 version 1 releases are among the 104 comparison-filter releases. The comparison filter released 30 more, and 13 of those 30 misstate an order (13 faithful, 4 unsupported claims). The reviewer's last sentence, that the block reasons are version 1 reasons, was left out because it adds no fact.

Item 6, the number-matching filter: no new experiment, as the author decided. The Introduction, the comparison filter methods, and the Results now say that the comparison is a digit-and-unit filter and that a filter accepting only numbers from the same order is untested. The phrase "the part attributable to the checks beyond slot substitution" is now "the joint effect of the text checks and the drug-name rule."

Item 7, the RxNorm check: made. The Design section reports the check from eval/data/vocab_rxnorm_check.json. RxNorm version 02-Nov-2026 (RxNav API 3.1.357), accessed November 6, 2026. The check searched 146 words: the 67 framing words, the shape words take and which, and the 77 name stop words. Three words had hits, covering 22 RxNorm concepts. "hi", a framing word, matched histidine (RXCUI 5340) by approximate name search. "milk", a name stop word, matched cow milk allergenic extract (RXCUI 892665) and two clinical products. "water", also a name stop word, matched the ingredient water (RXCUI 11295) and 17 products, 15 of them ophthalmic irrigation solutions. The code report gave 18 products for water, but the data file lists 18 concepts in all, including the ingredient, so the paper says 17. No word was removed. The paper says the United States Pharmacopeia list was not checked, because it is not freely available, and that the vocabulary claim remains the authors' judgment.

Item 8, punctuation between the items of a value sentence: made. The built binary releases "Take metformin (500 mg) by mouth twice a day." and "Take metformin / 500 mg / by mouth / twice a day." The paragraph lists the marks that may appear between items (comma, parentheses, apostrophe, quotation mark, hyphen, and slash), and it says the sentence-end marks cannot appear inside a value sentence. The reviewer's list also included period, semicolon, and colon, which divide sentences, so the paper leaves them out of the list of allowed marks.

Item 9, three missing references: made. Crossref metadata (https://api.crossref.org) confirms: Portet F, Reiter E, Gatt A, Hunter J, Sripada S, Freer Y, Sykes C, Artificial Intelligence 173(7-8):789–816, 2009, doi:10.1016/j.artint.2008.12.002; Maynez J, Narayan S, Bohnet B, McDonald R, Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics, pages 1906–1919, 2020, doi:10.18653/v1/2020.acl-main.173; Necula GC, Proof-carrying code, Proceedings of POPL 1997, pages 106–119, doi:10.1145/263699.263712. The Portet publisher page returned HTTP 403, so the reviewer's claim that Portet et al. used templates and checked output against the data could not be verified. The sentence states only what the title supports. The Maynez sentence uses wording from the ACL Anthology abstract ("unfaithful to the input document," and "faithful and factual summaries"). The Necula sentence describes the pattern, and its content was not checked against the POPL paper, because only the bibliographic record was verified. The references are renumbered in order of first citation: 1 to 11 unchanged, 12 to 46 shifted, and the new entries are 12, 15, and 28.

Item 10, the held-out term: made. Held out is defined at its first use in the Introduction, as the reviewer proposed. The Abstract uses the term before that point, and it has no room for a definition. The round against version 2 is called an adversarial round written against version 2 in the Abstract, the Introduction, the Table 2 caption, the Development heading and text, the Results, and the Conclusion. "Held-out" stays only for round h1, which the definition covers.

Item 11, the Faithful column in Table 2: made. The column header is "Faithful, not one ingredient under two names," and the caption says that faithful excludes the one-ingredient outputs, which have their own column. Round h2, version 2: 54 faithful, 19 one-ingredient, 73 faithful labels in all.

Item 12, a table of label changes: made as Table 2A in Labels. Each count was computed from the label files by eval/label_change_counts.py, which also gives the counts with all changes reverted. The adopted counts are 2 (development version 1), 92 (development comparison), 38 and 51 (round h1 version 1 and comparison), 9 and 23 (round h2 version 2 and comparison), and 56 (Llama 3.2 3B comparison). With all changes reverted, the counts are 1, 89, 41, 54, 9, 22, and 48. These match the figures the paper already gave for the protocol as written.

## Changes made

paper/paper.md: Abstract rewritten to 1,920 characters, with the wording in items above. Introduction (comparison filter sentence, two rounds sentence). Design (value-sentence punctuation, question and exclamation marks, framing vocabulary claim, RxNorm check). Table 1 (new row for repeated instructions, the No daily total row now cites dailyDose_none_long). Specification (201 theorems, 2,082 proof lines, 122 on three axioms). Development (held-out definition, round-h1 nesting, round-h2 adversarial wording). Table 2 caption and header. Table 3 caption. Results (released doses and simvastatin, coded timing and the 455 orders, the repeated-value example, the comparison filter limits, the Claude temperature sentences, the joint-effect phrase, the adversarial round). Labels (Table 2A and its summary). Limits (coded-timing sentence). Conclusion (2,082 lines, monthly lines, adversarial round). References (new 12, 15, 28; list renumbered; the DailyMed reference, formerly 42, now 45 with the simvastatin read date).

paper/arxiv_submission.md: Abstract copied from paper.md, character count line now 1,920, and the table count is 5.

README.md: 201 theorems, and two new script entries under eval.

eval/label_change_counts.py: new file (standard library only).

paper/response_round20.md: new file (this response).

## Not done in this round

The PDF and Word files (paper/dosegate.pdf, paper/dosegate.docx) were not rebuilt, so they still carry the round 19 text. The arXiv comments say 36 pages, which should be checked after the rebuild. The file tests/axioms_2026-11-05.txt still lists 200 theorems, because tests/ was out of scope this round. The paper does not cite that file by name. The Lean code changes (DoseGate/Proofs/Daily.lean, tests/Axioms.lean) were made in the earlier code step and not committed here. Nothing was committed.
