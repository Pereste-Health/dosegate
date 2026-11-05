# DoseGate

DoseGate is a small program, written in Lean 4 and proved to meet a written specification, that sits between a language model and a reader. The model writes medication instructions with slots such as `{{dose:m1}}` instead of numbers. DoseGate fills each slot from the FHIR MedicationRequest it receives or blocks the whole output. The proofs guarantee that every drug name, dose, daily total, route, and frequency in released text is the corresponding value of the single active order named by the slot, for every model and every output. The code that reads FHIR JSON into Lean values is tested, not proved.

## Layout

- `DoseGate/*.lean`: definitions (exact decimals, units, the FHIR subset, the slot parser, word classes, the renderer, the specification).
- `DoseGate/Proofs/*.lean`: the proofs. `lake build DoseGate.Proofs` checks all of them.
- `DoseGate/Json.lean`, `Main.lean`: the command-line tool and FHIR reader. This code is tested, not proved.
- `Baseline.lean`: a comparison filter used only in the evaluation. It uses the same reader and slot formatting but checks model text only for digits and unit words.
- `tests/`: regression tests for the tool (`bash tests/run.sh`) and `tests/Axioms.lean`, which prints the axioms every theorem depends on (`lake env lean tests/Axioms.lean`).
- `eval/`: the evaluation with Qwen3.5-4B on Synthea patients (`build_cases.py`, `generate.py`, `score.py`), the comparison filter and mutation test (`controls.py`), the adversarial corpus run (`attacks.py`), and their data in `eval/data/`.
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
echo '{"medicationRequests": [...], "output": "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}."}' | .lake/build/bin/dosegate render
```

The reply is `{"status":"ok","text":...}`, `{"status":"blocked","reason":...,"detail":...}`, or `{"status":"error","message":...}`. `dosegate serve` reads one JSON request per line. Every MedicationRequest must carry the same `subject.reference`, or the request must name a `patient`.

Options:

- `--extra-words FILE` adds lowercase words, one per line, to the vocabulary for free sentences. Forbidden words stay forbidden.
- `--ignore-free-text` reads the dose, timing, and route of an order even when the order has a `note` or its dosage has `text`, `additionalInstruction`, or `patientInstruction`. By default such an order has no usable dose, timing, or route, because free text can hold or limit the structured dose. Use this option only when the free text is generated from the structured fields.

## License

Apache-2.0.
