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

## Abstract (1764 characters, under the 1,920-character limit)

This is the same text as the abstract in the paper.

Language models that explain medications to patients reproduce doses and compute daily totals by generating tokens, so a correct order in the prompt does not guarantee a correct number in the output. We describe a layer, written in the Lean 4 theorem prover, that sits between any language model and the reader. The model writes each medication instruction as references to fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest, and the layer either fills every reference from the orders it receives or blocks the output. In 197 machine-checked theorems, released text states each drug name, dose, route, frequency, and daily total exactly as the single active order named, and every amount in it comes from the orders. Each value appears only within a complete instruction for its own order, and every other sentence contains no medication content. The code that reads FHIR records is tested, not proved. An earlier version passed five rounds of red-team testing but released 41 misstatements in 74 releases on a held-out round. After redesign, a second held-out round of 138 attacks yielded 9 misstatements in 86 releases, against 22 in 128 for a filter that filled the same slots but blocked only digits and unit words. Six came from record fields the reader ignored, two from a minus sign beside an amount, and one from an omitted order; a later version blocks all nine but the omission, which an option blocks. With three open models, Qwen3.5-4B, MedGemma 4B, and Llama 3.2 3B, the layer released 98.3%, 83.3%, and 1.7% of greedy outputs on 120 test cases. No released text contained a misstatement the scoring script could detect. Asked for daily totals in free text, the models misstated an amount in 16, 69, and 19 of 120 outputs.
