# STRUX_V1 — Quick Start

## Install

```bash
pip install -r requirements.txt
```

## Run core benchmarks

```bash
python -m benchmarks.transport_diagnosis_test_05
python -m benchmarks.sieve_test_01
python -m benchmarks.corridor_coherence_test_01
python -m benchmarks.clearance_test_01
```

## Current validated observables

- success_rate
- gate_mode_count
- direction_coherence
- clearance_ratio

## Output folders

Benchmark results are saved under:

```text
exports/
```

## Scientific status

STRUX_V1 is an experimental geometric transport diagnostic framework.

It does not yet claim:
- universal physics
- cosmology
- physical flux
- superiority over A*/RRT/diffusion baselines