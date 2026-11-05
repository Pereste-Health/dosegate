# Response to the fourth round of review

## Required items

- Round-h2 faithful count (health literacy 1, math 1): the paragraph now says 73 were labeled faithful, of which 54 were faithful and 19 gave one ingredient under two names, matching Table 3.
- Replay wording in the Abstract (health literacy 2): the Abstract says the final version was built after round h2 and blocks the nine on replay, which is not a held-out test.
- Label-dose sources (health literacy 3): reference 30 now gives a DailyMed set ID for each of the four labels with the access date, and the Results quote the sentence each threshold comes from (all four checked against the label text through the DailyMed API). The count is split into 122 releases that print the daily total and 83 that state a dose and frequency whose product exceeds the label dose; eval/maxima.py computes both.
- Qwen3.5-4B comparison-only output not labeled (math 2): the Labels paragraph and the Results say this one output was not sent to the readers.
- Rubric by round (math 3): the Labels paragraph gives the development and round-h1 rubric and the round-h2 rubric separately, and says the development and round-h1 misstatement counts are lower bounds with respect to the round-h2 rubric.
- Sign rule with "-(" (math 4, computer science 1): closed in the code (commit 58cdcb3): a slot is now blocked when the run of spaces and punctuation just before it contains a minus or plus sign, so "-(", "-( ", "- (", and "-[" are blocked (four new tests). `render_no_sign_before_slot` is restated for this property and re-proved; the helper lemma `endsSign_false` was removed, so the development has 197 theorems (118 with all three standard axioms, 68 with a subset, 11 with none). No model-output decision, replay decision, or released text changed. The Design and Table 1 describe the new rule.
- Extra words (computer science 2): the Design says that `--extra-words` can let framing sentences carry medical claims and that the framing guarantees hold for the default vocabulary; the Abstract describes the 67-word list.
- Single-read labels (computer science 3): the Labels paragraph names the one flagged output and the 10 unflagged weekly outputs from the version 1 study that one reader judged.
- Omission count (computer science 4): six of the nine active orders, not five of eight.
- Omission rubric (computer science 5): the Labels paragraph says no rubric listed omissions; the round-h1 paragraph reports the round-h1 output that omitted six of seven orders and labeled faithful, and the counts if it were counted as in round h2 (42 and 55); the round-h2 paragraph says the third reader counted its omission as a misstatement.

## Recommended items applied

Digit-name ceiling (118 of 120 greedy, 236 of 240 at temperature 1.0); unknownRef as the reason for the 22 "ID" outputs; "by default" for completeness in the Abstract; split-regimen example corrected; Abstract free-text counts now 71 and 20 (flagged plus unflagged sample); fallback line form; how same-ingredient pairs were identified; same text, different labels; 95% upper bounds for the zero counts (0.4% and 6.0%); the adversarial counts are descriptive; six of the nine round-h2 misstatements came from the shared reader; round parts named r1, r2, r3, r4a, r4p; Table 1 names the `ambiguousDrug` reason; vocabulary provenance wording; slot and slot daily prompts distinguished; latency includes the Python pipe; fuzz command and seed given; tie-breaks in round h2 (5 of 9); Med-PaLM cited.
