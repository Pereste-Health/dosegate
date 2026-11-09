# arXiv submission notes

These notes are for the arXiv form. They are not part of the paper.

## Before posting

1. The public repository named in the paper's Availability paragraph, https://github.com/Pereste-Health/dosegate, must hold the `main` branch with the commit that this manuscript describes. Check that the link opens when you are logged out. The paper cites that address, so it must work before the preprint goes up.
2. Confirm that you have endorsement for the primary category. A first-time submitter to cs.LO may need an endorser.
3. Check the PDF before upload. Rebuild `paper/dosegate.pdf` from `paper/paper.md` if the manuscript changed after its last build (`python3 paper/prep_md.py paper/paper.md /Volumes/T7/tmp-dg/dosegate.md`, then `~/.claude/skills/personal-brand-docs/scripts/build_pdf.sh` and `build_docx.sh` on that copy), confirm with `pdffonts` that only Times New Roman is embedded, and confirm with `pdftotext` that the Abstract matches the current text.
4. Confirm that the tag v2.3.0 names the commit that holds the layer and the evaluation data the paper describes. Run `git rev-parse v2.3.0^{}` and `git ls-remote origin 'refs/tags/v2.3.0^{}'` and check that both print the same full hash (6e08a52d665cdb0558ae349d8674fbbf7ebfdc00 at the time of this revision); the manuscript commit itself comes after that tag, which is what the Availability paragraph says. When committing, stage only this project's files (not eval/generate.py, eval/models.py, .gitignore, paper/dosegate_jamia*, or docs/) and confirm the staged set with `git diff --cached --name-only`. Do not move the tag after posting, because a changed commit under the same tag would change the version the arXiv paper names.
5. Upload `paper/dosegate.pdf`. arXiv accepts a PDF that was not made from TeX. Ancillary files are not supported for PDF-only submissions, which is why the code and data live in the repository.

## Form fields

- Title: A model-agnostic, formally verified output layer that keeps language model medication instructions faithful to medication orders
- Authors: Parker Smith (Pereste Health)
- Primary category: cs.LO (Logic in Computer Science)
- Cross-lists: cs.CL (Computation and Language), cs.AI (Artificial Intelligence)
- Comments: 42 pages, 13 tables. Code, data, and model outputs: https://github.com/Pereste-Health/dosegate (release v2.3.0)
- License: CC BY 4.0 for the paper (the code is Apache-2.0 in the repository)

## Abstract (1,904 characters, under the 1,920-character limit)

Language models can misstate doses their prompt gives correctly. A Lean 4 layer sits between model and patient: the model writes slots for fields of a Fast Healthcare Interoperability Resources (FHIR) MedicationRequest, and the layer fills them or blocks output. In 202 theorems, each dose, route, and frequency filled from a slot is the named order's value, each daily total is dose times daily count, and each appears only in its instruction; by default each active order gets one. A drug name prints only if it is one of 27,369 RxNorm names, a trusted list; that the model's words (take, which, 67 framing words) hold no drug name is a judgment no proof checks. The FHIR input reader is tested, not proved. Released lines are dose statements, not full directions: weekly, monthly, as-needed, conditional, and taper orders need a pharmacist check; wording is untested with patients. Five adversarial rounds each targeted a frozen version. Version 1 released 38 misstatements in 74 outputs; versions 2, 2.1, and 2.2 released 9, 35, and 10 in 86, 91, and 107, 51 of those 54 through the input reader or the drug name and 3 through model text; each version then narrowed what the reader accepts. On the held-out round h5, version 2.3 released 95 of 144 outputs, 1 misstating an order and 5 making an unsupported claim; a digit-and-unit filter released 8 misstatements. On 120 normalized synthetic cases, the layer released 98.3% of slot outputs after rewrites from Qwen3.5-4B and four Claude models, 83.3% from MedGemma 4B, and 1.7% from Llama 3.2 3B. A lenient script found no misstated dose, total, or frequency in 1,800 released texts; no clinician reviewed them. Without the layer, the open models misstated an order in at least 16, 71, and 20 of 120 free-text outputs. 221 of 368 open-model releases with perturbed doses exceeded a US label maximum or usual range; the layer prints orders as written.
