# DoseGate

DoseGate is a small program, written in Lean 4 and proved to meet a written specification, that sits between a language model and a reader. The model writes each medication instruction with slots such as `{{dose:m1}}` instead of values. DoseGate fills each slot from the FHIR MedicationRequest it receives or blocks the whole output. The proofs guarantee, for every model and every output, that every drug name, dose, daily total, route, and frequency in released text is the corresponding value of the single active order the slot names, that each value appears only inside a complete instruction for its own order, and that every other sentence uses only a small vocabulary of framing words. The code that reads FHIR JSON into Lean values is tested, not proved.

This is version 2.1. The history of versions 1, 2, and 2.1, and the held-out adversarial rounds that led to them, is described in the paper.

## Layout

- `DoseGate/*.lean`: definitions (exact decimals, units, the FHIR subset, the slot parser, word classes, the renderer, the specification).
- `DoseGate/Proofs/*.lean`: the proofs. `lake build DoseGate.Proofs` checks all 197 theorems.
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

The reply is `{"status":"ok","text":...}`, `{"status":"blocked","reason":...,"detail":...}`, or `{"status":"error","message":...}`. `dosegate serve` reads one JSON request per line. Every MedicationRequest must carry the same `subject.reference`, or the request must name a `patient`.

Options:

- `--require-all-orders` blocks any output that does not give an instruction for every active order.
- `--extra-words FILE` adds lowercase words, one per line, to the vocabulary for framing sentences. Forbidden words stay forbidden.
- `--ignore-free-text` reads the dose, timing, and route of an order even when the order has a `note` or its dosage has `text`, `additionalInstruction`, or `patientInstruction`. By default such an order has no usable dose, timing, or route, because free text can hold or limit the structured dose. Use this option only when the free text is generated from the structured fields.

When the layer blocks, the application must show something else, for example a list rendered by DoseGate itself from the orders with no model text, or a message to contact the pharmacist.

## Reproducing the evaluation

All commands run from the repository root with Python 3 (standard library) after building. Model generation needs MLX LM 0.32.2 for Qwen3.5-4B and Ollama for the other two models.

- `eval/build_cases.py` rebuilds `eval/data/cases.jsonl` from the Synthea bundles (not distributed).
- `eval/generate.py` generates model outputs. Version 2 runs used `HALF=test` with `MODEL`, `BACKEND`, `OUT`, and `CONDITIONS` set as in the paper; outputs are `eval/data/generations_v2_*.jsonl`.
- `TAG=v2_qwen3.5-4b python3 eval/score.py` (and likewise for `v2_medgemma-4b` and `v2_llama3.2-3b`) re-gates every stored output with the built binary and writes `results_all_<tag>.json` and `final_gate_decisions_<tag>.json`.
- `TAG=<tag> python3 eval/controls.py` runs the comparison filter, the planted-error test, and the attack counts (`controls_<tag>.json`).
- `python3 eval/models.py` writes the cross-model table (`models_summary.json`); `python3 eval/describe.py v2_qwen3.5-4b v2_medgemma-4b v2_llama3.2-3b` writes case counts and reading grades (`describe.json`); `python3 eval/latency.py v2_qwen3.5-4b` times the binary.
- `python3 eval/attacks.py IN OUT` runs an adversarial corpus through both filters. Corpora: `eval/data/attacks.jsonl` (development), `eval/data/heldout/` (round h1, against version 1), `eval/data/heldout2/` (round h2, against version 2), and `eval/data/replay_v21/` (all corpora replayed through version 2.1). `python3 eval/labels.py` summarizes the labels. The protocol is in `eval/labeling_protocol.md`.
- `eval/data/v2_review/` holds the blinded reader labels of model outputs.

Files without a `v2` tag (`generations.jsonl`, `results_all.json`, and so on) are the version 1 study; files in `eval/data/pilot/` are from an earlier pilot and are not reported.

## License

Apache-2.0.
