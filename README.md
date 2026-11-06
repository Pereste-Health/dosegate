# DoseGate

DoseGate is a small program, written in Lean 4 and proved to meet a written specification, that sits between a language model and a reader. The model writes each medication instruction with slots such as `{{dose:m1}}` instead of values. DoseGate fills each slot from the FHIR MedicationRequest it receives or blocks the whole output. The proofs guarantee, for every model and every output, that every drug name, dose, daily total, route, and frequency the layer fills from a slot is the corresponding value of the single active order the slot names, and that each filled value appears only inside an instruction for its own order that states its dose, route, and frequency. With the default vocabulary, every other sentence uses only a small set of framing words; a deployment that adds words with `--extra-words` can release a drug name outside any instruction. The code that reads FHIR JSON into Lean values is tested, not proved.

This is version 2.1. The history of versions 1, 2, and 2.1, and the held-out adversarial rounds that led to them, is described in the paper.

## Layout

- `DoseGate/*.lean`: definitions (exact decimals, units, the FHIR subset, the slot parser, word classes, the renderer, the specification).
- `DoseGate/Proofs/*.lean`: the proofs. `lake build DoseGate.Proofs` checks all 200 theorems.
- `DoseGate/Json.lean`, `Main.lean`: the FHIR reader and command-line tool. This code is tested, not proved.
- `Baseline.lean`: the comparison filter used in the evaluation. It uses the same reader and slot formatting but checks model text only for braces, digits, and unit words.
- `tests/`: regression tests (`bash tests/run.sh`), the differential fuzz test of the reader (`python3 tests/fuzz_reader.py --core v2 --seed 7 --count 20000`), and `tests/Axioms.lean`, which prints the axioms of every theorem (`lake env lean tests/Axioms.lean`).
- `eval/`: the evaluation scripts and data (below).
- `paper/`: the manuscript.

## Build

Install Lean with elan (the toolchain, Lean 4.35.0, is pinned in `lean-toolchain`), then:

```bash
lake build DoseGate.Proofs
```

```bash
lake build dosegate dosegate-baseline
```

## Use

```bash
echo '{"medicationRequests": [...], "output": "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}, which is {{daily:m1}}."}' | .lake/build/bin/dosegate render
```

The reply is `{"status":"ok","text":...}`, `{"status":"blocked","reason":...,"detail":...}`, or `{"status":"error","message":...}`. `dosegate serve` reads one JSON request per line. Every MedicationRequest must carry a `subject.reference`. Without a `patient` field, all of them must carry the same reference. An order whose `status` or `intent` is missing or is not a FHIR R4 code (case variants such as `Active` included) makes the whole request an error. Valid statuses other than active (on-hold, cancelled, completed, entered-in-error, stopped, draft, unknown) and valid intents that are not order intents (proposal, plan, option) make the order inactive, and inactive orders are omitted without a block. With a `patient` field, an order is for that patient when its subject reference is `Patient/<id>`, `urn:uuid:<id>`, or an http or https URL ending in `Patient/<id>`; a reference in one of those forms with another id makes the order inactive; any other form makes the request an error. The reader also refuses the whole request with an error reply when a request, bundle, or bundle entry has a key the reader does not accept (an unknown key with a null value is ignored), when the `bundle` or `medicationRequests` key is null, when a bundle entry is not an object, has no `resource`, or has a `resource` without a non-empty string `resourceType`, when an order has an empty `id` or a `doNotPerform` that is present and is neither a boolean nor null, or when an order has a wrong-typed `medicationCodeableConcept`, `dosageInstruction`, timing, route, dose, `asNeededBoolean`, `dispenseRequest`, or `meta` field, such as a `frequency` or `period` that is not a whole number. Fields such as `authoredOn`, `reasonCode`, `category`, and `identifier` are not type-checked. Elsewhere, a key with a null value still counts as present: an order or dosage key outside the allowlist removes the dose even when its value is null. A bundle entry whose `resourceType` is not one of the 145 FHIR R4 resource type names (for example a lowercase `medicationrequest` or `MedicationRequests`) makes the request an error; an entry of another valid type, such as `Patient` or `MedicationStatement`, is skipped, so send each order as a MedicationRequest.

Options:

- By default the layer blocks any output that does not give an instruction for every active order. `--allow-omissions` turns this off. It is the only option that lets an active order go unnamed without a block.
- `--extra-words FILE` adds lowercase words, one per line, to the vocabulary for framing sentences. Forbidden words stay forbidden. The guarantees about framing sentences hold for the default vocabulary only: added words can be medical (for example "treats" or "diabetes"), and the layer does not check them, so the deployment must keep them free of medication names, indications, and quantities.
- `--ignore-free-text` reads the dose, timing, and route of an order even when the order has a `note` or its dosage has `text`, `additionalInstruction`, or `patientInstruction`. By default such an order has no usable dose, timing, or route, because free text can hold or limit the structured dose. Use this option only when the free text is generated from the structured fields.

The reader gives a dose written as a count (tablet, capsule, puff, or drop) no usable dose, so an output that prints that dose is blocked with `missingField`, because a count gives the patient no strength to check; send strengths instead. Under the default settings, the layer blocks with the reason `noActiveOrder` when no order is active, so an empty or fully inactive order list never produces text.

When the layer blocks, the application must show something else and must never show the block detail to a patient, because it can quote model text. `dosegate fallback` reads a request like `render`, ignores its output, and renders one instruction per active order through the same proved code.

## Reproducing the evaluation

All commands run from the repository root with Python 3 (standard library) after building. Model generation needs MLX LM 0.32.2 for Qwen3.5-4B and Ollama for the other two models.

- `eval/build_cases.py` rebuilds `eval/data/cases.jsonl` from the Synthea bundles (not distributed).
- `python3 eval/free_text_share.py` counts the active MedicationRequests and their free-text fields in the raw Synthea bundles, read in place from `SYNTHEA_FHIR_DIR`, and writes `eval/data/free_text_share.json`.
- `eval/generate.py` generates model outputs. Version 2 runs used `HALF=test` with `MODEL`, `BACKEND`, `OUT`, and `CONDITIONS` set as in the paper; outputs are `eval/data/generations_v2_*.jsonl`.
- `TAG=v2_qwen3.5-4b python3 eval/score.py` (and likewise for `v2_medgemma-4b` and `v2_llama3.2-3b`) re-gates every stored output with the built binary and writes `results_all_<tag>.json` and `final_gate_decisions_<tag>.json`.
- `TAG=<tag> python3 eval/controls.py` runs the comparison filter, the planted-error test, and the attack counts (`controls_<tag>.json`).
- `python3 eval/models.py` writes the cross-model table (`models_summary.json`); `python3 eval/describe.py v2_qwen3.5-4b v2_medgemma-4b v2_llama3.2-3b` writes case counts and reading grades (`describe.json`); `python3 eval/latency.py v2_qwen3.5-4b` times the binary.
- `python3 eval/attacks.py IN OUT` runs an adversarial corpus through both filters. Corpora: `eval/data/attacks.jsonl` (development), `eval/data/heldout/` (round h1, against version 1), `eval/data/heldout2/` (round h2, against version 2), and `eval/data/replay_v21/` (all corpora replayed through version 2.1; each results file is the output of `python3 eval/attacks.py` on the `.jsonl` file beside it). `python3 eval/labels.py` summarizes the labels. The protocol is in `eval/labeling_protocol.md`.
- `eval/data/v2_review/` holds the blinded reader labels of model outputs.

Files without a `v2` tag (`generations.jsonl`, `results_all.json`, and so on) are the version 1 study; files in `eval/data/pilot/` are from an earlier pilot and are not reported.

## License

Apache-2.0.
