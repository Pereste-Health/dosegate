# Human labeling of a blind sample

This folder holds the tool Parker uses to label a blind sample of released texts, so the JAMIA draft can report human agreement with the model labels. Every label in the evaluation before this was assigned by an instance of Claude.

## The sample

`build_queue.py` draws the sample with a fixed seed (20261107) and shuffles it, so the strata are mixed. The queue has 193 items:

| Stratum | Items | Source |
| --- | --- | --- |
| Round h2 releases labeled misstates_order | 9 (all) | `eval/data/heldout2/labels_h2.json`, filter `layer` |
| Round h2 releases labeled unsupported_claim | 4 (all) | same |
| Round h2 releases labeled faithful | 30, drawn at random from the 54 faithful releases that are not on the same-ingredient list | same |
| Same-ingredient pairs that version 2.1 releases | 16 of the 19 listed | `eval/data/heldout2/same_ingredient_pairs.json`, texts from `eval/data/replay_v21/h2_results.jsonl` |
| Open-model releases in the blind review sample | 60 (the `lr` items, 20 per model, all labeled faithful by the model readers) | `eval/data/v2_review/items.jsonl` |
| Claude free daily outputs the scoring script flagged | 74 (46 Claude Haiku 5.5, 28 Claude Sonnet 5.5) | `eval/data/generations_v2_claude-*.jsonl`, flags recomputed with `eval/score.py` |

`queue_manifest.json` maps each queue id (`q001` to `q193`) to its source. It holds no labels, but the source ids name the attack classes, so do not read it while labeling. The page embeds, per item, only the queue id, whether the item carries the pair questions, the rendered orders, the raw FHIR request (without the attacker's output template), and the released text, plus the rubric text and the error-type glosses. No label, flag, model name, stratum, source id, or seed is in the page.

What the page cannot hide: the texts themselves differ in style between the layer's template sentences, the open models' slot outputs, and the Claude free-text outputs (bold markdown, length), and only the adversarial requests carry unusual FHIR fields or Bundle wrappers, so a reader can often tell what kind of source produced an item. The labels are still blind to the model readers' labels and to the script flags, which is what the agreement compares. One item is a 60,000-character flood of one phrase; it stays in the sample because it is a release the model readers labeled.

## Labeling

Open `label_tool.html` in a browser on the Mac (double-click it), or open the private claude.ai artifact on the phone or the Mac: https://claude.ai/artifact/M9iRx6K3Ye3cNHwre1n9Xr (owned by Parker's account; the same page with the same queue). Each item shows the orders rendered readably, with anything unusual (a status other than active, an intent other than order, an as-needed flag, timing events, extensions, dispense requests, notes, a different subject) in a highlighted line, the raw FHIR JSON behind "Raw FHIR JSON", and the released text. Label each text, then tap Next. The rubric, the two addenda, and the error-type glosses are behind the Rubric button.

Schema per item: `label` (faithful, misstates_order, unsupported_claim); `error_type` for misstates_order (weekly_as_daily, wrong_daily_arithmetic, sum_of_different_drugs, wrong_dose, wrong_frequency, wrong_route, duplicated_instruction, wrong_medicine, inactive_as_current, conditional_as_fixed, other); for the 16 pair items, `same_ingredient` and `double_dose_risk` (yes, no, unsure); `confidence` (sure, unsure); a free-text `note`; and `labeled_at`, the time of the last change.

Keyboard: 1, 2, 3 set the label; the letter on each chip sets the error type; 7, 8, 9 and y, x, z answer the pair questions; u toggles unsure; right arrow or j is next, left arrow or k is back, n is the next unlabeled item; / writes a note; f opens the raw FHIR; r the rubric; g the queue.

Labels save on every change. In the local file they live in the browser's localStorage, so export before clearing site data or switching browsers. In the artifact they also go to the page's shared database, so the phone and the Mac see the same labels, and a Claude session can read them back with the ArtifactData tool.

## Export and the numbers

1. Export, then Save `parker_labels.json` (or Copy JSON and paste it into a file).
2. Put the file at `eval/data/human_labels/parker_labels.json`. If the labels were made in the artifact, a Claude session can instead read the `labels` collection of the artifact's database with the ArtifactData tool (action `list`, with `out_dir` pointing at a scratch folder) and run `python3 eval/labeling/collect_db_labels.py <that folder>`, which writes the same file.
3. Run `python3 eval/human_agreement.py`. It prints percent agreement and Cohen's kappa for each stratum and pooled, the disagreements with the adopted labels, and the sentences the draft needs. `--json PATH` writes the full report; `--labels PATH` reads a different file.

Within a stratum whose adopted label does not vary (for example the 9 misstatements, or the 60 open-model releases, all labeled faithful), Cohen's kappa is 0 by construction whenever the human's labels vary, because expected agreement then equals observed agreement; the table marks those rows with an asterisk, and the pooled h2 and all-items rows carry the kappa information. The 74 Claude flags have no model label, so the script reports how many the human confirmed as misstatements or unsupported claims.

## Files

- `build_queue.py` draws the sample and writes `label_tool.html` and `queue_manifest.json`; `--artifact-body PATH` also writes the page without the document skeleton, for publishing as an artifact.
- `label_tool_template.html` is the page; the build inserts the queue data.
- `make_synthetic_labels.py --out PATH` writes a synthetic label file for testing the agreement script.
- `collect_db_labels.py SOURCE...` turns label documents read back from the artifact's database into `eval/data/human_labels/parker_labels.json`, keeping the newest record per item.
- `../human_agreement.py` computes the agreement; `tests/test_human_agreement.py` tests it (`uv run --with pytest python -m pytest tests/test_human_agreement.py`).
