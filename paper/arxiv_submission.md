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

## Abstract (1911 characters, under the 1,920-character limit)

This is the same text as the abstract in the paper.

Language models reproduce doses and compute daily totals by generating tokens, so a correct order in the prompt does not guarantee a correct number in the output. We describe a layer written in Lean 4 between any language model and the reader. The model writes each instruction as references to fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest, and the layer fills each reference from the orders or blocks the output. In 200 machine-checked theorems, released text states each drug name as the active order gives it and each dose, route, frequency, and daily total as the same quantity or coded route as that order, only inside a complete instruction for that order; by default it gives an instruction for every active order, and otherwise uses only 67 framing words. The FHIR reader is tested, not proved. An earlier version released two misstatements in 44 red-team development outputs, each settled by a third reader, then 41 in 74 on a held-out round. A redesigned version released 9 in 86 on a second held-out round of 138 attacks, against 22 in 128 for a filter that filled the same slots but blocked only digits and units. The final version returns no text for all nine on replay, a test that is not held out; it cannot tell a brand name from its generic name, and 16 of its 46 replay releases instruct the patient to take one ingredient under two names. With three open models on 120 slot-condition test cases, the layer released 98.3%, 83.3%, and 1.7% of outputs after rewrites; a scoring script found no misstated dose, daily total, or frequency in any of the 867 released texts, and two instances of Claude found none in a random sample of 60. Asked for daily totals in free text, Qwen3.5-4B, MedGemma 4B, and Llama 3.2 3B misstated an order in at least 16, 71, and 20 of 120 test outputs. Of 368 released perturbed-order outputs, 221 exceeded a usual US label maximum.
