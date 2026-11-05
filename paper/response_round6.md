# Response to the sixth round of review

Required items:

- Fallback and duplicate therapy (health literacy 1): the Design and Discussion now say the fallback does not check for duplicate therapy, so Lantus and insulin glargine reach the patient as two lines, and that a deployment must check for one ingredient under two names and withhold the fallback when it finds one.
- No warnings in released text (health literacy 2): the Limits now say released text cannot carry any warning or direction beyond dose, route, frequency, and daily total, give the blocked words and examples ("Do not stop", "Take with food"), and say a deployment must add such warnings from clinician-written text.
- Free-text default (health literacy 3): the Limits now say that orders with dosage text, instructions, or notes yield no dose under the default, that the release rate on real records is unknown, and name --ignore-free-text with its clinical trade-off.
- Replay labels file (math 1): the Labels paragraph now says the file holds 27 labels, 11 for texts the final version 2.1 releases and 16 for texts it blocks.
- Rubrics (math 2): the Labels paragraph now describes the round-h2 rubric and the model-output rubric separately.
- Round-h2 omission precedent (math 3): reworded as proposed.
- Agreement count (computer science 1): the sentence now gives 360 of 379, the 19 disagreements, and the one item with no first-reader label, 20 third-reader items in all.
- Named patient and missing subject (computer science 2): fixed in the reader. A request that names a patient is now an error if any order lacks a subject.reference (DoseGate/Json.lean subjectProblem; the fuzz reference follows). The test blocked_patient_no_subject became error_patient_no_subject, and tests/raw/error_patient_named_order_without_subject reproduces the reviewer's probe. 220 tests pass, 20,000 fuzz requests agree, no model-output decision changes, and one development replay (E06) changes from blocked to error in both filters, so no release count changes; the Table 3 caption error count is updated. The reader is now 368 lines.

The release is tagged v2.1.0, and the paper cites the tag instead of a commit hash.
