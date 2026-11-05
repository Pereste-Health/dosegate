# Response to the third round of review

Health literacy reviewer:

1. Same-ingredient pairs: Table 3 now reports "One ingredient under two names" as its own outcome column, and those outputs are no longer counted as faithful (version 2: 54 faithful and 19 pairs; comparison filter: 81 and 19; version 2.1 replay: 33 and 17). The caption says the column is a separate outcome assessed after labeling. The Abstract states the 17 and that the version 2.1 numbers are a replay.
2. Scope of the readers' check: the Abstract says the scoring script checked all 867 releases and two readers found no misstatement in a random sample of 60; the Results say the other 807 were checked only by the script.
3. Label doses: the thresholds are now sourced to US prescribing information on DailyMed (reference 30, with the amlodipine set ID), each with its label basis stated; the count is produced by a new script, eval/maxima.py, from the final decision files; and the paragraph says that fidelity to an order is not clinical safety.
4. "Split regimen": corrected. The Limits paragraph now distinguishes one drug written as two orders from two different drugs that share a word, and says these are blocked, so the cost is a missing instruction.
5. Fallback: the Design and Discussion now state its limits (no heading, no daily total, same-ingredient pairs remain, no reason for use on as-needed orders, a digit in any drug name blocks it, not tested with patients) and that the theorems hold for the lines it prints.
Recommended items applied: Abstract free-text counts are "at least" and name the two models; the comparison-filter sentence for Qwen3.5-4B is rewritten; blocked shares are given per model; completeness is stated to hold only for the orders in the request; the Table 2 caption is clarified; the 2,764 layer decisions are broken into 2,160 first outputs and 604 rewrites.

Math reviewer:

1. Causes of the nine round-h2 misstatements: the event-list cause covers two outputs, and the sentence now gives a count per cause (1, 1, 2, 1, 1 for the reader; 2 for the sign; 1 omission).
2. Table 1 "Fail closed" row: now states the related-name hypothesis of `renderSeg_missing`.
3. Theorem and axiom counts: rerun after the build (see the build log in the commit that follows this response).
Recommended items applied: the sign sentence now says a minus sign directly or after spaces is blocked, that "-(" is not, and that a plus sign is blocked by the character rule; planted errors exclude the 19 released attack outputs; latency and the decision counts are described as layer decisions with their composition; the Abstract says "slot outputs".
