# DoseGate

DoseGate is a small program, written and proved correct in Lean 4, that sits between a language model and a reader. The model writes medication instructions with slots such as `{{dose:m1}}` instead of numbers. DoseGate fills each slot from the patient's FHIR MedicationRequest or blocks the whole output. The proofs guarantee that every drug name, dose, daily total, route, and frequency in released text is the corresponding value of the single active order named by the slot, for every model and every output.

## Layout

- `DoseGate/*.lean`: definitions (exact decimals, units, the FHIR subset, the slot parser, word classes, the renderer, the specification).
- `DoseGate/Proofs/*.lean`: the proofs. `lake build DoseGate.Proofs` checks all of them.
- `DoseGate/Json.lean`, `Main.lean`: the command-line tool and FHIR reader. This code is tested, not proved.
- `tests/`: regression tests for the tool (`bash tests/run.sh`).
- `eval/`: the evaluation with Qwen3.5-4B on Synthea patients (`build_cases.py`, `generate.py`, `score.py`) and its data.
- `paper/`: the manuscript.

## Build

Install Lean with elan (the toolchain is pinned in `lean-toolchain`), then:

```bash
lake build DoseGate.Proofs
```

```bash
lake build dosegate
```

## Use

```bash
echo '{"medicationRequests": [...], "output": "Take {{drug:m1}} {{dose:m1}} {{route:m1}} {{frequency:m1}}."}' | .lake/build/bin/dosegate render
```

The reply is `{"status":"ok","text":...}`, `{"status":"blocked","reason":...,"detail":...}`, or `{"status":"error","message":...}`. `dosegate serve` reads one JSON request per line. Every MedicationRequest must carry the same `subject.reference`, or the request must name a `patient`.

## License

Apache-2.0.
