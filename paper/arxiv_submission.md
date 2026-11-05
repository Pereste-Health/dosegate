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

## Abstract (1854 characters, under the 1,920-character limit)

This is the same text as the abstract in the paper.

Language models that explain medications to patients reproduce doses and compute daily totals by generating tokens, so a correct order in the prompt does not guarantee a correct number in the output. We describe a layer, written in the Lean 4 theorem prover, that sits between any language model and the reader. The model writes each instruction as references to fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest, and the layer fills every reference from the orders or blocks the output. In 197 machine-checked theorems, released text states each drug name, dose, route, frequency, and daily total exactly as the active order named, only inside a complete instruction for that order, by default gives an instruction for every active order, and otherwise uses only a fixed list of 67 framing words. The code that reads FHIR records is tested, not proved. An earlier version released one misstatement in 44 outputs during red-team development, then 41 in 74 on a held-out round. A redesigned version released 9 misstatements in 86 outputs on a second held-out round of 138 attacks, against 22 in 128 for a filter that filled the same slots but blocked only digits and unit words. The final version, built after that round, blocks all nine on replay, which is not a held-out test; it cannot tell a brand name from its generic name, and 17 of its 50 releases on the replay instruct the patient to take one ingredient under two names. With three open models on 120 test cases, the layer released 98.3%, 83.3%, and 1.7% of slot outputs after rewrites; a scoring script found no misstated dose, daily total, or frequency in any of the 867 released texts, and two readers found none in a random sample of 60. Asked for daily totals in free text, MedGemma 4B and Llama 3.2 3B misstated an amount in at least 71 and 20 of 120 outputs.
