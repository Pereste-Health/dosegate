# arXiv submission notes

These notes are for the arXiv form. They are not part of the paper.

## Before posting

1. Create the public repository named in the paper's Availability paragraph, https://github.com/Pereste-Health/dosegate, and push the `main` branch. Check that the link opens when you are logged out. The paper cites that address, so it must work before the preprint goes up.
2. Confirm that you have endorsement for the primary category. A first-time submitter to cs.LO may need an endorser.
3. Check the PDF before upload. Rebuild `paper/dosegate.pdf` from `paper/paper.md` if the manuscript changed after its last build (the commands are in HANDOFF.md), and confirm with `pdftotext` that the Abstract matches the current text.
4. Confirm that the tag v2.1.0 names commit 6685af2e33ba5c2d51205c79d46d08e3076b1a6b locally and on origin. Run `git rev-parse v2.1.0^{}` and `git ls-remote origin 'refs/tags/v2.1.0^{}'`, and check that both print that full hash. The Availability paragraph cites v2.1.0 only for the layer and the evaluation data, which that tag holds, and not for this manuscript. Before posting, stage only paper/paper.md, the rebuilt paper/dosegate.pdf, and paper/dosegate.docx (do not stage eval/generate.py, eval/models.py, .gitignore, paper/dosegate_jamia*, or docs/), confirm the staged set with `git diff --cached --name-only`, commit, push main, and tag that commit as a new release (for example v2.1.1) using the same two commands with the new tag name. Do not move any tag after posting, because a changed commit under the same tag would change the version the arXiv paper names.
5. Upload `paper/dosegate.pdf`. arXiv accepts a PDF that was not made from TeX. Ancillary files are not supported for PDF-only submissions, which is why the code and data live in the repository.

## Form fields

- Title: A model-agnostic, formally verified output layer that keeps language model medication instructions faithful to medication orders
- Authors: Parker Smith (Pereste Health)
- Primary category: cs.LO (Logic in Computer Science)
- Cross-lists: cs.CL (Computation and Language), cs.AI (Artificial Intelligence)
- Comments: @@PAGES pages, 4 tables. Code, data, and model outputs: https://github.com/Pereste-Health/dosegate
- License: CC BY 4.0 for the paper (the code is Apache-2.0 in the repository)

## Abstract (1,912 characters, under the 1,920-character limit)

This is the same text as the abstract in the paper.

Language models can misstate doses that the prompt gives correctly. We describe a Lean 4 layer between a language model and the patient. The model writes each instruction as references to fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest; the layer fills each reference or blocks output. In 200 proved theorems, each drug name, dose, route, frequency, and daily total comes from the order its slot names and appears only in that order's instruction stating dose, route, and frequency. By default each active order gets an instruction, and model words are limited to 67 framing words, take, and which; adding --extra-words can release a drug name outside an instruction. The FHIR input reader is tested, not proved. A first version released two misstatements in 44 development outputs (one under the written protocol), then 38 in 74 on a held-out round. A redesigned version released 9 in 86 on a second held-out round of 138 attacks, six of the nine through input-reader fields, against 23 in 128 for a filter with the same slots and only digit and unit checks (version 2 build). On replay, version 2.1 gives no text for all 9, but 16 of its 45 round-h2 releases give one ingredient under two names, a possible double dose (unchecked by clinicians). Across three open models on 120 slot-condition cases from normalized records, the layer released 98.3%, 83.3%, and 1.7% of outputs after rewrites, and by default no raw Synthea bundle gets output. A lenient scoring script found no misstated dose, daily total, or frequency in 867 released texts; Claude instances, not clinicians, found none in 60 sampled. In free-text daily totals, three open models misstated an order in at least 16, 71, and 20 of 120 test outputs; two Claude runs had 46 and 28 unlabeled flags. 221 of 368 released outputs with test-altered doses exceeded a US label maximum or usual range for one of four drugs.