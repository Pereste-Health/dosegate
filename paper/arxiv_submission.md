# arXiv submission notes

These notes are for the arXiv form. They are not part of the paper.

## Before posting

1. Create the public repository named in the paper's Availability paragraph, https://github.com/Pereste-Health/dosegate, and push the `main` branch. Check that the link opens when you are logged out. The paper cites that address, so it must work before the preprint goes up.
2. Confirm that you have endorsement for the primary category. A first-time submitter to cs.LO may need an endorser.
3. Upload `paper/dosegate.pdf`. arXiv accepts a PDF that was not made from TeX. Ancillary files are not supported for PDF-only submissions, which is why the code and data live in the repository.

## Form fields

- Title: A model-agnostic, formally verified output layer that keeps language model medication instructions faithful to medication orders
- Authors: Parker Smith (Pereste Health)
- Primary category: cs.LO (Logic in Computer Science)
- Cross-lists: cs.CL (Computation and Language), cs.AI (Artificial Intelligence)
- Comments: @@PAGES pages, 3 tables. Code, data, and model outputs: https://github.com/Pereste-Health/dosegate
- License: CC BY 4.0 for the paper (the code is Apache-2.0 in the repository)

## Abstract (1918 characters, under the 1,920-character limit)

This is the same text as the abstract in the paper.

Language models generate numbers token by token, so a correct order in the prompt does not guarantee a correct number in the output. We describe a Lean 4 layer between any language model and the reader. The model writes each instruction as references to fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest, and the layer fills each reference or blocks the output. In 200 proved theorems, each drug name, dose, route, frequency, and daily total comes from the order its slot names and appears only in an instruction for that order that states its dose, route, and frequency. By default every active order gets an instruction, and the model's own words are limited to 67 framing words plus take and which; a deployment that adds words with --extra-words can release a drug name outside any instruction. The FHIR reader is tested, not proved. An earlier version released two misstatements in 44 development outputs (one, F05, relabeled against the labeling protocol), then 41 in 74 on a held-out round. A redesigned version released 9 in 86 on a second held-out round of 138 attacks, against 22 in 128 for a filter with the same slots and only digit and unit checks. On replay, version 2.1 returns no text for all nine, but by the author's unchecked reading, 16 of its 46 replay releases give one ingredient under two names. With three open models on 120 normalized slot-condition test cases, the layer released 98.3%, 83.3%, and 1.7% of outputs after rewrites (Qwen3.5-4B outputs were examined before version 2). A scoring script found no misstated dose, daily total, or frequency in 867 released texts, and readers found none in 60 sampled. Asked for daily totals in free text, Qwen3.5-4B, MedGemma 4B, and Llama 3.2 3B misstated an order in at least 16, 71, and 20 of 120 test outputs. 221 of 368 released perturbed-order outputs exceeded a usual US label maximum or the top of usual range.
