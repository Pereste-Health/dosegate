# arXiv submission notes

These notes are for the arXiv form. They are not part of the paper.

## Before posting

1. Create the public repository named in the paper's Availability paragraph, https://github.com/Pereste-Health/dosegate, and push the `main` branch. Check that the link opens when you are logged out. The paper cites that address, so it must work before the preprint goes up.
2. Confirm that you have endorsement for the primary category. A first-time submitter to cs.LO may need an endorser.
3. Check the PDF before upload. Rebuild `paper/dosegate.pdf` from `paper/paper.md` if the manuscript changed after its last build (the commands are in HANDOFF.md), and confirm with `pdftotext` that the Abstract matches the current text.
4. Confirm that the tag v2.1.0 names the commit you are posting. The tag is moved to the final commit of each review round, so after the final revision is committed and pushed, run `git rev-parse v2.1.0^{}`, `git ls-remote origin 'refs/tags/v2.1.0^{}'`, and `git rev-parse origin/main`, and check that all three print the same full hash; that commit holds the layer, the evaluation data, and this manuscript, as the Availability paragraph says. When committing, stage only this project's files (not eval/generate.py, eval/models.py, .gitignore, paper/dosegate_jamia*, or docs/) and confirm the staged set with `git diff --cached --name-only`. Do not move the tag after posting, because a changed commit under the same tag would change the version the arXiv paper names.
5. Upload `paper/dosegate.pdf`. arXiv accepts a PDF that was not made from TeX. Ancillary files are not supported for PDF-only submissions, which is why the code and data live in the repository.

## Form fields

- Title: A model-agnostic, formally verified output layer that keeps language model medication instructions faithful to medication orders
- Authors: Parker Smith (Pereste Health)
- Primary category: cs.LO (Logic in Computer Science)
- Cross-lists: cs.CL (Computation and Language), cs.AI (Artificial Intelligence)
- Comments: 36 pages, 4 tables. Code, data, and model outputs: https://github.com/Pereste-Health/dosegate
- License: CC BY 4.0 for the paper (the code is Apache-2.0 in the repository)

## Abstract (1,917 characters, under the 1,920-character limit)

This is the same text as the abstract in the paper.

Language models can misstate doses that the prompt gives correctly. We describe a Lean 4 layer between a model and the patient: the model writes slots naming fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest, and the layer fills them or blocks output. In 200 proved theorems, each drug name, dose, route, frequency, and daily total filled from a slot is the named order's value and appears only in that order's instruction, and by default every active order gets one. That model words (take, which, and 67 framing words) hold no drug name is a judgment no theorem checks; --extra-words lifts that limit. The FHIR input reader is tested, not proved. Released lines are dose statements, not complete directions: weekly and as-needed lines need a pharmacist check, and wording is untested with patients. A first version released 2 misstatements in 44 development outputs (1 under the written protocol), then 38 in 74 on a held-out round. A redesign released 9 in 86 on a second round of 138 attacks, 6 through input-reader fields, against 23 in 128 for a slot filter checking only digits and units (version 2 build). On replay, version 2.1 blocks all 9, but 16 of its 45 round-h2 releases give one ingredient under two names, a possible double dose found by one author and unchecked by clinicians. On 120 normalized cases it released 98.3%, 83.3%, and 1.7% of slot outputs from three open models after rewrites; by default no raw Synthea bundle gets output. A lenient script found no misstated dose, total, or frequency in 867 released texts, and Claude instances none in 60 sampled; no clinician reviewed outputs. In free-text daily totals, the open models misstated an order in at least 16, 71, and 20 of 120 outputs; two Claude runs had 46 and 28 unlabeled flags. 221 of 368 released outputs with synthetic perturbed doses exceeded a US label maximum or usual range (four drugs checked).