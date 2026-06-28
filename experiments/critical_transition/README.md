# STRUX_V1 critical-transition milestone

## Purpose

This directory freezes the latest STRUX_V1 controlled synthetic experiment on the loss of local geometric organization under increasing disorder. It preserves the interpretation, analysis procedure, and expected outputs without changing the STRUX_V1 core, benchmarks, or public APIs.

This is **STRUX_V1**, not STRUX_V2.

## Relation to earlier turbulence experiments

Earlier turbulence-oriented experiments examined radial summaries such as `Best_Bin` and raw `Mean_Vort`. The null-control campaign showed that an absolute radial maximum was not a robust discriminator: a large peak could reflect distributional properties or peak selection rather than persistent local organization.

The frozen analysis therefore compares the structured-shock condition point by point with a control at the same shock level and radial coordinate. It does not reinterpret or alter the earlier benchmark implementations.

## Why the analysis is differential

Absolute metrics do not isolate the contribution of local organization. The archived observable is the differential Z-score

```text
Z_diff(shock, point) =
    (mean(STRUCTURED_SHOCK) - mean(VECTOR_SHUFFLE))
    / std(VECTOR_SHUFFLE)
```

computed from matched pointwise samples. The Vector Shuffle standard deviation is the sample standard deviation across available control realizations. Points with fewer than two Vector Shuffle samples, or zero control variance, remain undefined rather than being assigned an artificial value.

## Why Vector Shuffle is the reference

Gaussian Noise provides a flat null baseline. Vector Shuffle is the more targeted reference because it removes local organization while preserving distributional properties of the vectors. The difference from Vector Shuffle therefore operationally isolates structure that depends on local arrangement within this synthetic setup.

## Frozen result

For the tested synthetic configuration, the local differential signature was observed only within a limited critical window, approximately `Shock <= 0.4`. The frozen result consists of:

- this scope and interpretation;
- the reproducible pointwise analysis script;
- the internal scientific milestone report; and
- the output contract documented under `results/`.

The source CSV files from the campaign are not present in this repository snapshot. The script loads them when supplied, validates the required fields, and does not synthesize replacements.

## Claims intentionally not made

This archive does not claim:

- a universal law or a new physical theory;
- validation on real-world data;
- correspondence with physical turbulence;
- that `Best_Bin` is a stable geometric observable;
- that the approximate `Shock <= 0.4` window generalizes beyond the tested configuration; or
- that a shuffle baseline is a purely local invariant.

See [the report](reports/STRUX_V1_GEOMETRIC_SIGNATURE_REPORT.md) for the full milestone statement and [the results guide](results/README.md) for reproducibility instructions.
