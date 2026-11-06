# Response to the fourteenth round of review

This pass answers the three round 14 reviews (health literacy, math, and computer science). All three asked for minor revision. Section names below refer to paper/paper.md. Each reviewer item was checked against the code, the data files, or the built binary, `.lake/build/bin/dosegate`, before any change. The binary was checked to be newer than DoseGate/Json.lean (binary built 01:23:48, Json.lean last saved 01:23:33). Where an item could not be done, this response says why.

Nothing was committed. Files this pass changed: paper/paper.md, paper/arxiv_submission.md, paper/response_round14.md, README.md, eval/pinned_rerun.sh (a comment only), and eval/data/replay_v21/labels.json (one note added to h1_chart_reported_by_patient). Round 14 changed these other files before this pass, and they belong in the round 14 commit: DoseGate/Json.lean, tests/fuzz_reader.py, eval/data/replay_v21/h1_results.jsonl, eval/data/pinned_reruns.json, and the ten files in tests/raw/. This pass edited none of them. This pass also edited no Lean file, no test, no Claude data file, and none of eval/generate.py, eval/models.py, .gitignore, paper/dosegate_jamia*, or docs/. The PDF and Word files were not rebuilt, and paper/dosegate.pdf and paper/dosegate.docx were already modified before this pass.

Corrections to round 13. The round 13 response said the Abstract was 1,920 characters. Python's len() on the Abstract gave 1,911 characters, which the round 13 header in paper/arxiv_submission.md correctly stated. The response text was wrong. The Abstract is now exactly 1,920 characters by len(), identical in paper/paper.md and paper/arxiv_submission.md. The round 13 response also left the fuzz mutation count at 52. The fuzz run this pass reports 53 distinct mutation kinds, and the paper now says 53.

## Verification run in this pass

Regression tests: `bash tests/run.sh` passes 270 of 270 (from 265).

Fuzz test: `python3 tests/fuzz_reader.py --core v2 --seed 7 --count 20000` gives 20,000 agreements, 0 unexplained disagreements, and 53 distinct mutation kinds.

Reader line counts: `grep -c .` (non-blank lines) gives 532 for DoseGate/Json.lean (from 525) and 207 for Main.lean (unchanged). The sum is 739 (from 732). README.md carries no line or test count, so nothing there needed the new numbers.

Theorems: 200 theorems in DoseGate/Proofs (grep for `^theorem`), unchanged. The axiom split (121, 68, 11) was not rerun, because no proof file changed.

Replay: `eval/data/replay_v21/h1_results.jsonl` changed on one line, `h1_chart_reported_by_patient`. The layer now returns missingField, and the development and h2 replays are unchanged. Round h1 version 2.1 releases 7 requests (from 8). Development still releases 6 and round h2 still releases 45.

Pinned reruns: I checked the nine rerun output files in /Volumes/T7/tmp-dg/pinned/out against the stored files in eval/data/heldout and eval/data/heldout2 with `cmp`. All nine are byte-identical. Both build logs end with "Build completed successfully", and lean-toolchain pins leanprover/lean4:v4.35.0.

## Required items

Health literacy, required 1 (reported orders, priority, and intents). Trusted code and Limits now state the reported-order rule. An order with reportedBoolean true, or with any reportedReference key, keeps its drug name and yields no dose, timing, or route. A null reportedReference still counts as present, and a null reportedBoolean counts as absent. A reportedBoolean that is neither a boolean nor null makes the request an error. Trusted code also now says that the order intents are order, original-order, reflex-order, filler-order, and instance-order, and that priority is read and ignored. The binary checks used for these statements are in the table below.

| Input | Default output | Source |
|---|---|---|
| metformin 500 mg, twice a day, reportedBoolean true | blocked, missingField | probe.py, first case |
| reportedBoolean false | ok, "Take metformin 500 mg by mouth twice a day, which is 1000 mg a day." | probe.py |
| reportedBoolean null | ok (same text) | probe.py |
| reportedBoolean "yes" | error, "needs reportedBoolean to be true or false when present" | probe.py |
| reportedReference present | blocked, missingField | probe.py |
| reportedReference null | blocked, missingField | probe.py |
| priority stat only | ok (same text) | probe.py |
| intent reflex-order, filler-order, instance-order, original-order | ok (same text) | probe.py |
| intent plan | blocked, inactiveOrder | probe.py |
| reportedBoolean true, intent reflex-order, priority stat, reportedReference | blocked, missingField | probe.py |

The probe script is /Volumes/T7/tmp-dg/r14/probe.py. Five raw tests in tests/raw/, added earlier in round 14, cover the same cases (the test files are blocked_reader_reported_boolean_true, blocked_reader_reported_reference, blocked_reader_reported_boolean_unnamed, ok_reader_reported_boolean_false, and error_reader_reported_boolean_string). Limits adds the rule, the priority and intent statements, and a deployment duty to confirm that each order is a prescriber's order and to check for reflex and filler orders. README.md states the wrong-typed field rule and the reported-order rule.

Computer science, required 1 (glued strengths in drug names). The Design paragraph and Limits now say that the drug-name rule tests whole words. A name that joins a spelled-out strength to a unit is printed as written. The binary check: metformin 500 mg by mouth twice a day, with the name "Metformin fivemg", returns "Take Metformin fivemg 500 mg by mouth twice a day." with the basic template, and "Take Metformin fivemg 500 mg by mouth twice a day, which is 1000 mg a day." with the daily slot. The name "Metformin kilograms" also prints. The name "Lisinopril 10 MG Oral Tablet" is blocked (missingField, no usable drug), so the rule still stops a second strength when a digit or a unit word appears as a separate word. Table 1, Design, and Limits give the disclosure. No code was changed, as instructed. The proposed rejection of number and unit words inside a name would need a Lean change, so it is left for a later round.

Computer science, required 2 (stored comparison-filter run in the Abstract). The pinned reruns reproduced the stored rows exactly: round h1 gives 74 and 104 releases, and round h2 gives 86 and 128, with 0 mismatches in 113 and 138 records (eval/data/pinned_reruns.json). The Reproducing Table 2 paragraph and the Table 2 caption now give this result and the files eval/pinned_rerun.sh and eval/data/pinned_reruns.json. The Abstract sentence keeps 23 in 128 and adds the words "version 2 build", so it says that the 128 is the run of the version 2 build. The current build's figure of 107 of 138 on that filter appears in Results, the Table 2 caption, and Reproducing Table 2, not in the Abstract sentence.

Math, required 1 (three reopened items). Labels now lists all three items that the replay relabeling reopened: F05, F03, and h1_chart_reported_by_patient. I checked each against the three label files. In eval/data/attack_labels.json, the original labelers gave F05 and F03 faithful, and F05 has a relabel note. In eval/data/heldout/labels_h1.json, h1_chart_reported_by_patient is faithful and faithful. In eval/data/replay_v21/labels.json, F05 is misstates_order, faithful, and misstates_order (the third labeler gave misstates_order). F03 is misstates_order, faithful, and faithful (final faithful). h1_chart_reported_by_patient is unsupported_claim, faithful, and faithful (final faithful). The paper also discloses that four round-h1 records (h1_structure_14, _21, _22, and _23) have a first-labeler value in the replay file that the held-out file lacks, and their third-labeler values are absent from the replay file. Their final labels are faithful in both files. The text also says what separates F05 from F03 (the statusReason of order m1 in F05 against a patient instruction in F03), and that this separation was chosen after the outcome was known. The Development paragraph refers to Labels for the other reopened items.

## Recommended items

Health literacy, Abstract wording. The Abstract now says "Claude instances, not clinicians, found none in 60 sampled" and "221 of 368 released outputs with test-altered doses".

Health literacy, blocked output in the Introduction. The Introduction now says what the patient receives when the layer blocks an output, and that the deployment must show a fallback, show a list checked by a pharmacist, or route the patient to a pharmacist.

Health literacy, as-needed rule. Results now says the default rule is not monotone in the record's information. The bare "Take as needed." blocks, and the same order with no free text releases "Take oxycodone hydrochloride 5 mg by mouth once a day as needed." (checked with the binary, using asNeededBoolean inside the dosageInstruction element). Whether the bare phrase should block is a clinical decision.

Health literacy, acetaminophen. The Limits sentence now says "Version 2.1 releases these texts, so they show the size of the harm under the adopted version." The acetaminophen label maximum was not checked, so no number was added, as before.

Health literacy, same-ingredient pairs. Limits now gives the lisinopril and Zestoretic example, and says that the Zestoretic line does not show its hydrochlorothiazide. It also says that Toprol-XL is extended-release metoprolol succinate, which differs from metoprolol tartrate in salt form and release type. The Toprol-XL fact is a standard pharmacology fact and was not checked against a label in this pass.

Computer science, drug names in Table 1. The drug-name row now says that the rule tests whole words, so a name such as `Metformin fivemg` passes.

Computer science, levothyroxine unit. Results now says that the fidelity measurement takes each order as given, so the released 0.075 mg text is faithful to an order that is wrong for microgram tablets.

Computer science, free daily row. Table 3 and Results now say that the free daily row is zero by construction under the default settings. A released output must name every active order in a value slot, and a free daily output has no slot, so the layer cannot release it. The Results sentence that said the layer blocked every free daily output because of words outside the slot grammar was replaced.

Computer science, record-number filter. The Introduction now says that the evaluation shows the result for a filter with slot substitution and digit and unit checks. The paragraph already says that a filter accepting numbers from the record was not tested, and that the Results give only the design argument.

Computer science, Messages API default. The Claude runs paragraph no longer says what the Messages API parameter list contains. A WebFetch read in this pass covered only the first 100,000 of the page's 1,296,513 characters, so it could not support a statement about the whole list. The paragraph now says that the runs sent no temperature field, and that the paper does not state the API's numeric default temperature or whether the runs were greedy.

Computer science, PAL reference. Reference 23 now gives the venue. The ICML 2023 proceedings page (PMLR 202, pages 10764 to 10799) lists the paper by the same eight authors, so the reference reads "In: Proceedings of the 40th International Conference on Machine Learning. PMLR 202; 2023:10764–10799."

Computer science, the free daily and rerun sentences in the Table 2 caption. The Table 2 caption now says the round-h1 and round-h2 comparison-filter rows reproduce exactly at commits 59c5f32 and ef2cc98, and that the current build releases 92 of 113 and 107 of 138. The development row still comes from an earlier build (215 of 290 on the current build).

Computer science, drug-name rule in Limits. Limits repeats the glued-strength example next to the penicillin G potassium sentence.

Computer science, the 193 raw orders in README.md. The README now says those orders still block under --ignore-free-text because their dose, route, or unit is unusable, and that the option must not be used on records of this kind without checking each order.

Computer science, the Abstract lower bound and the script. The Abstract says the scoring script's count is a lower bound, and says that Claude instances, not clinicians, reviewed 60 of the 867 texts and found none. Results already said the script counts are lower bounds, and Outcome measures says what the script checks.

Computer science, the 16 pairs and the Abstract framing. The Abstract now says that six of the nine round-h2 layer misstatements came through input-reader fields. The Abstract also says "unchecked by clinicians" for the 16 pairs, and the Results and Limits already gave the input-reader and window details.

Computer science, the Abstract numbers on the current build. Results already states the normalized-record framing (52 of 120 patients, 43.3%, have free text in the raw records). The Abstract could not take this framing without going past 1,920 characters, so it stays in Results and Limits.

Computer science, the unit-word claim in Design. Design now gives the glued-strength case with the built binary output.

Math, labels counts. Labels now gives the revised counts. Ten of the 27 labels made before round 10 are for texts version 2.1 releases, and 17 are for texts version 2.1 blocks. The count of labels for released texts is 13 of 30, from 14, because h1_chart_reported_by_patient is now blocked. I checked these counts with the replay results and the labels file.

Math, the labeler identities. The Labels and Limits paragraphs say that the replay relabels were made by new labelers whose instance identifiers and exposure to the version 2.1 output the repository does not record. The adopted labels for F05, F03, and h1_chart_reported_by_patient carry that limitation.

Math, Table 2 counts. The round h1 version 2.1 replay row changed from 8 released to 7 released. The Table 2 caption and the Version 2.1 paragraph say the same.

Math, Table 1 daily totals. The statement that a weekly or monthly order has no daily total now cites dosesPerDay_none_long, which exists in DoseGate/Proofs/Daily.lean, and says dailyDose? is defined through dosesPerDay?. The one-line theorem the reviewer proposed was not added, because Lean files may not be edited in this pass.

Math, the Specification paragraph. The Specification paragraph now says that the fidelity predicate is SegRendersTo with its list lifting Forall₂, both defined in DoseGate/Spec.lean. The other Table 1 properties are conclusions of theorems in DoseGate/Proofs, and no single predicate combines them. I checked the names in Spec.lean.

Math, the conjunction sentence. The Table 1 paragraph now adds "Each row is proved separately." The conjunction theorem was not written, because Lean files may not be edited in this pass.

Math, the reruns. The Reproducing Table 2 paragraph now records the rerun results (see the required items above).

Health literacy, the Abstract and the Introduction. The Abstract is unchanged in structure. Length was kept at 1,920 characters by removing the parenthetical "(Qwen3.5-4B outputs were examined before version 2)" from the Abstract. The Results and Methods still state that Qwen3.5-4B's outputs were examined before version 2 was designed, so its rates are not held-out estimates.

## Not done

Lean changes. Four recommended items need Lean changes that this pass may not make. These are the one-line theorem for dailyDose? on weekly and monthly timings, the single conjunction theorem for the default policy, the rejection of drug-name words that contain a number or unit word as a substring (with a regression test), and any Lean test. The prose versions are in the paper, and the proposed theorems were not added.

Availability commit hash. The reviewer asked for the commit hash to go with tag v2.1.0. Nothing is committed in this pass, so no hash exists yet for the arXiv version. Availability still cites the tag v2.1.0 only. When the round 14 commit is made, the tag must move to it, following the practice in HANDOFF.md, and then the hash can be added.

Claude data files. The temp field in eval/data/generations_v2_claude-haiku-5-5.jsonl and eval/data/generations_v2_claude-sonnet-5-5.jsonl still reads 0.0. Those files may not be edited in this pass. The paper and README say the field is a placeholder.

Replay label file. eval/data/replay_v21/labels.json, the entry for h1_chart_reported_by_patient, still lists the original released text and the reasons for the faithful label. The file now has a relabel_note on that entry saying that version 2.1 blocks the request, so no version 2.1 output carries the label. The reasons field was not rewritten.

Labeler identity for F05. The replay file names no labeler and does not record whether the labelers saw the version 2.1 output. Answering this needs the labelers' records, which are not in the repository.

## Open items

Tag v2.1.0. The tag points to the round 13 commit (ccc1d1f). The round 14 changes include a reader change, so the layer described in the paper differs from that commit. Commit and move the tag before posting.

Word and PDF files. paper/dosegate.pdf and paper/dosegate.docx must be rebuilt from paper/paper.md before the arXiv upload. The commands are in HANDOFF.md.

Messages API default. The Claude runs paragraph no longer makes a claim about the Messages API parameter list, so no further read is needed for this item.

## Changes made

paper/paper.md, Abstract. Replaced with the 1,920-character version. Changed clauses: "Language models generate numbers token by token, so a correct prompt order does not guarantee a correct output" became "so a correct prompt does not guarantee correct output"; "We describe a Lean 4 layer between any language model" became "between a language model"; "(one, F05, relabeled against protocol)" became "(F05 relabeled against protocol)"; "every drug name ... stating its dose, route, and frequency" became "stating dose, route, and frequency"; "six of the nine through input-reader fields the layer does not prove" became "six of the nine through input-reader fields" (the word "proves" was removed for length); "(version 2 build)" was added after 23 in 128; "On replay ... a possible double dose (unchecked by a clinician)" became "(unchecked by clinicians)"; "With three open models on 120 slot-condition test cases" became "120 slot-condition cases"; the parenthetical "(Qwen3.5-4B outputs were examined before version 2)" was removed; "labelers found none in 60 sampled" became "Claude instances, not clinicians, found none in 60 sampled"; "A scoring script found no misstated ... in 867 released texts" gained ", a lower bound"; "221 of 368 released outputs with changed doses" became "with test-altered doses". Count: `len()` on the paragraph, 1,920. Check: /Volumes/T7/tmp-dg/r14/abstract_draft.py.

paper/paper.md, Introduction. Added the blocked-output sentence (patient gets no model text; deployment must show a fallback, a pharmacist-checked list, or route to a pharmacist). The filter sentence now reads "a filter with slot substitution and digit and unit checks releases outputs that misstate an order."

paper/paper.md, Specification and proofs. "What is proved" rewritten to name SegRendersTo and Forall₂ in DoseGate/Spec.lean and state that no single predicate combines the Table 1 properties (names checked in DoseGate/Spec.lean).

paper/paper.md, Table 1. The intro gained "Each row is proved separately." The Drug names row gained the whole-word note with `Metformin fivemg`.

paper/paper.md, Trusted code. Line counts: "732 non-blank lines ... 525 in the input reader" became "739 ... 532". The wrong-typed clause now covers reportedBoolean ("an order's `doNotPerform` or `reportedBoolean` is present and is neither a boolean nor null"). Added the order-intent list and priority sentence after the active-order sentence. Added the reported-order bullet to the closed-order list. Test count "265 regression tests" became "270". Fuzz count "52 kinds of mutation" became "53 kinds".

paper/paper.md, Design. Drug-name sentence rewritten (glued-strength example, binary output for "Take Metformin fivemg 500 mg by mouth twice a day.").

paper/paper.md, Development (Version 1). The F05 reopening sentence now refers to Labels for the other reopened items.

paper/paper.md, Evaluation methods. Labels: rewritten reopening paragraph for F05, F03, and h1_chart_reported_by_patient, with the h1_structure disclosure and the F05 separation sentence. Added the labeler-identity limitation sentence. The count of labels for released texts changed: "Eleven ... (eight round-h1 texts)" became "Ten ... (seven round-h1 texts)"; "sixteen ... (fifteen development texts and one round-h1 text)" became "seventeen ... (fifteen development texts and two round-h1 texts ...)"; "Version 2.1 produced no text for the sixteen" became "seventeen"; "14 of the 30" became "13 of the 30". Claude runs paragraph: the sentence on the Messages API parameter list was removed. The paragraph now says that the paper does not state the API's numeric default temperature or whether the runs were greedy.

paper/paper.md, Version 2.1. The change list gained the reported-order rule. "It releases 8 round-h1 requests and 6 development requests" became "7 round-h1 requests and 6 development requests", with one sentence on h1_chart_reported_by_patient.

paper/paper.md, Table 2 caption. The comparison-filter sentence now says the round-h1 and round-h2 rows reproduce at commits 59c5f32 and ef2cc98 (92 of 113 and 107 of 138 on the current build). The caption also now says the stored run sent 11 requests whose numbers were strings. The F05 sentence now also names F03 and h1_chart_reported_by_patient as reopened items that kept faithful labels.

paper/paper.md, Table 2. The round h1 version 2.1 replay row changed from 8 released and 8 faithful to 7 released and 7 faithful (eval/data/replay_v21/h1_results.jsonl, status ok count 7).

paper/paper.md, Reproducing Table 2. The final sentence now records the rerun: eval/pinned_rerun.sh, eval/data/pinned_reruns.json, and 0 mismatches in 113 and 138 records.

paper/paper.md, Results. Added the levothyroxine fidelity sentence after the planted-error counts. Added the as-needed monotonicity paragraph after the 2,685 and 4,066 counts. Replaced "The layer blocked every free daily output, because each contained words outside the slot grammar" with the default-settings explanation. Table 3 caption gained the free daily zero-by-construction sentence.

paper/paper.md, Limits. Added the reported-order rule, the priority and intent statements, and the deployment duty (after the doNotPerform sentence). Replaced "The released texts show the size of the harm" with "Version 2.1 releases these texts, so they show the size of the harm under the adopted version." Zestoretic example gained the shared-ingredient clause and the Toprol-XL clause. The drug-name rule gained the glued-strength example. The end of Limits gained the replay-relabel limitation.

paper/paper.md, Conclusion. "732 non-blank lines" became "739 non-blank lines".

paper/paper.md, References. Reference 23 (PAL) now gives PMLR 202, 2023, pages 10764 to 10799, and the arXiv number. The verified page is proceedings.mlr.press/v202/gao23f.html.

paper/arxiv_submission.md. Abstract header now reads "1,920 characters, at the 1,920-character limit". The Abstract is identical to paper/paper.md (checked by string equality).

README.md. The wrong-typed clause covers reportedBoolean. Added the reported-order sentence after the inactive-order sentence. The --ignore-free-text sentence now says the 193 orders still block under the option and the option must not be used on records of this kind without checking each order.

README.md. Added a bullet for eval/pinned_rerun.sh under Reproducing the evaluation.

eval/pinned_rerun.sh. The usage comment says to run it from the repository root.

eval/data/replay_v21/labels.json. Added a relabel_note to h1_chart_reported_by_patient saying that version 2.1 blocks the request, so no version 2.1 output carries the label.

paper/arxiv_submission.md, Before posting. Added step 4 for committing the round 14 files and moving tag v2.1.0 before upload. Former step 4 is now step 5.

## Checker pass

Each changed number was checked against a file or the binary. Counts were rechecked with Python: 270 tests (`bash tests/run.sh`), 53 fuzz mutation kinds and 20,000 agreements (`python3 tests/fuzz_reader.py --core v2 --seed 7 --count 20000`), 532 and 207 reader and command-line lines (`grep -c .`), 7 round-h1 releases, 10 and 17 labels, and 13 of 30. The pinned rerun outputs were compared with `cmp`. The paper contains no em dashes, and the Abstract is 1,920 characters in both files.
