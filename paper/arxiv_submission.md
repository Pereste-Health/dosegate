# arXiv submission notes

These notes are for the arXiv form. They are not part of the paper.

## Before posting

1. Create the public repository named in the paper's Availability paragraph, https://github.com/Pereste-Health/dosegate, and push the `main` branch. Check that the link opens when you are logged out. The paper cites that address, so it must work before the preprint goes up.
2. Confirm that you have endorsement for the primary category. A first-time submitter to cs.LO may need an endorser.
3. Upload `paper/dosegate.pdf`. arXiv accepts a PDF that was not made from TeX. Ancillary files are not supported for PDF-only submissions, which is why the code and data live in the repository.

## Form fields

- Title: A formally verified output layer that keeps language model medication instructions faithful to medication orders
- Authors: Parker Smith (Pereste Health)
- Primary category: cs.LO (Logic in Computer Science)
- Cross-lists: cs.CL (Computation and Language), cs.AI (Artificial Intelligence)
- Comments: 16 pages, 3 tables. Code, data, and model outputs: https://github.com/Pereste-Health/dosegate
- License: CC BY 4.0 for the paper (the code is Apache-2.0 in the repository)

## Abstract (under the 1,920-character limit)

Language models that explain medications to patients reproduce doses, frequencies, and daily totals by generating tokens, so a correct order in the prompt does not guarantee a correct number in the output. We describe a verified layer, written in the Lean 4 theorem prover and proved to meet a written specification, that sits between any language model and the reader. The model writes text in which every drug name, dose, route, frequency, and daily total is a reference to a field of a FHIR MedicationRequest, and the layer either fills each reference from the orders it receives or blocks the whole output. Machine-checked theorems (170) establish that released text states exactly the values of the single active order each reference names, that every amount, route, and timing word comes from such a value, that a dose appears only in a complete instruction for its own order, and that daily totals are exact and exist only when they are well defined. The FHIR reader is tested, not proved, and sentences about what a medicine is for are not checked. With a four-billion-parameter open model on 240 synthetic cases, the model stated a weekly dose as a daily total in 30 of 40 outputs whose case had a weekly order, and stated a doubled dose under instruction in 239 of 240; the layer blocked all of these. It released 91.3% of greedy slotted outputs after up to two rewrites and 24.8% of samples at temperature 1.0, and none of the 551 released texts misstated an order. On 290 adversarial outputs, a filter that filled the same slots but blocked only digits and unit words released 89 misstatements; the layer released one, which repeated a drug name field. The layer was revised against these outputs, so that comparison is not held out.
