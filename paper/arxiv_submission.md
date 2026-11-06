# arXiv submission notes

These notes are for the arXiv form. They are not part of the paper.

## Before posting

1. Create the public repository named in the paper's Availability paragraph, https://github.com/Pereste-Health/dosegate, and push the `main` branch. Check that the link opens when you are logged out. The paper cites that address, so it must work before the preprint goes up.
2. Confirm that you have endorsement for the primary category. A first-time submitter to cs.LO may need an endorser.
3. Check the PDF before upload. Rebuild `paper/dosegate.pdf` from `paper/paper.md` if the manuscript changed after its last build (the commands are in HANDOFF.md), and confirm with `pdftotext` that the Abstract matches the current text.
4. Commit the round 14 files and move the tag. Run `git diff --cached --name-only` before committing, because another session's files (eval/generate.py, eval/models.py, .gitignore, paper/dosegate_jamia*, docs/) must not be in the commit. Then move the tag with `git tag -f -a v2.1.0 -m "Version 2.1.0" <new commit>`, push the branch with `git push origin main`, and push the tag with `git push -f origin v2.1.0`. Confirm with `git ls-remote origin 'refs/tags/v2.1.0^{}'` that the hash equals the new commit. The Availability paragraph says the tag names the commit that holds the layer, the evaluation data, and the manuscript, so this step must be done before the upload.
5. Upload `paper/dosegate.pdf`. arXiv accepts a PDF that was not made from TeX. Ancillary files are not supported for PDF-only submissions, which is why the code and data live in the repository.

## Form fields

- Title: A model-agnostic, formally verified output layer that keeps language model medication instructions faithful to medication orders
- Authors: Parker Smith (Pereste Health)
- Primary category: cs.LO (Logic in Computer Science)
- Cross-lists: cs.CL (Computation and Language), cs.AI (Artificial Intelligence)
- Comments: @@PAGES pages, 4 tables. Code, data, and model outputs: https://github.com/Pereste-Health/dosegate
- License: CC BY 4.0 for the paper (the code is Apache-2.0 in the repository)

## Abstract (1,920 characters, at the 1,920-character limit)

This is the same text as the abstract in the paper.

Language models generate numbers token by token, so a correct prompt does not guarantee correct output. We describe a Lean 4 layer between a language model and the patient. The model writes each instruction as references to fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest; the layer fills each reference or blocks the output. In 200 proved theorems, each drug name, dose, route, frequency, and daily total comes from the order its slot names and appears only in that order's instruction stating dose, route, and frequency. By default every active order gets an instruction, and the model's words are limited to 67 framing words, take, and which; adding words with --extra-words can release a drug name outside an instruction. The FHIR input reader is tested, not proved. An earlier version released two misstatements in 44 development outputs (F05 relabeled against protocol), then 38 in 74 on a held-out round. A redesigned version released 9 in 86 on a second held-out round of 138 attacks, six of the nine through input-reader fields, against 23 in 128 for a filter with the same slots and only digit and unit checks (version 2 build). On replay, version 2.1 gives no text for all 9, but 16 of its 45 round-h2 releases give one ingredient under two names, a possible double dose (unchecked by clinicians). With three open models on 120 slot-condition cases, the layer released 98.3%, 83.3%, and 1.7% of outputs after rewrites. A scoring script found no misstated dose, daily total, or frequency in 867 released texts, a lower bound; Claude instances, not clinicians, found none in 60 sampled. Asked for daily totals in free text, three open models misstated an order in at least 16, 71, and 20 of 120 test outputs, and two Claude models had 46 and 28 unlabeled flags. 221 of 368 released outputs with test-altered doses exceeded a US label maximum or usual range for one of four drugs.