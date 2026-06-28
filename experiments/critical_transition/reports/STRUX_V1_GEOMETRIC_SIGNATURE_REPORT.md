# STRUX_V1 geometric-signature report

**Milestone type:** frozen internal experimental result  
**Validation scope:** controlled synthetic evidence only  
**Version:** STRUX_V1 (not STRUX_V2)

## 1. Background

The earlier turbulence-oriented campaign used absolute radial summaries, including `Best_Bin`, to locate a dominant response. Subsequent null-control tests showed that the location and magnitude of an absolute peak did not reliably distinguish local geometric organization from distributional effects. This milestone freezes the revised interpretation without modifying the existing STRUX_V1 algorithms or benchmarks.

## 2. Experimental setup

The controlled campaign varied the synthetic shock level and evaluated the response along the radial coordinate. The relevant comparison is matched by shock level and radial point between:

- `STRUCTURED_SHOCK`, which retains the tested local organization; and
- `VECTOR_SHUFFLE`, which removes local organization while retaining vector-level distributional properties.

At each matched point, the analysis computes

```text
Z_diff = (mean(STRUCTURED_SHOCK) - mean(VECTOR_SHUFFLE))
         / std(VECTOR_SHUFFLE)
```

where the denominator is the sample standard deviation across Vector Shuffle realizations. Undefined comparisons are retained as missing values. The analysis script reports descriptive magnitudes but does not introduce a new threshold or classifier.

## 3. Null controls

### Gaussian Noise

Gaussian Noise behaved as a flat baseline in the controlled campaign. It establishes that an unstructured noise condition does not reproduce the organized radial response in the tested configuration. This statement is limited to the synthetic setup used in the campaign.

### Vector Shuffle

Vector Shuffle removes local adjacency or arrangement while preserving the vector distribution. It is therefore the reference baseline for separating local organization from distributional properties. It is a differential control, not evidence for a universal invariant.

## 4. Main observations

- Absolute radial peak selection was not robust under the null-control comparison.
- The pointwise difference from Vector Shuffle captured the decay of the tested local organization as shock increased.
- In the tested synthetic configuration, the differential signature survived only in a limited window, approximately `Shock <= 0.4`.
- Beyond that window, the controlled evidence did not support a distinguishable local signature relative to Vector Shuffle.

## 5. Validated conclusions

Within the current controlled synthetic scope:

1. Vector Shuffle is an appropriate distribution-preserving reference for this campaign.
2. The relevant observable is the extinction of the differential Z-score against Vector Shuffle as disorder increases.
3. The observed transition window is configuration-specific and approximately bounded by `Shock <= 0.4`.

These conclusions validate an experimental diagnostic procedure, not a physical theory.

## 6. Rejected interpretations

`Best_Bin` is not considered a stable geometric observable. Selecting an absolute radial maximum conflates peak location, amplitude, and distributional effects and was not robust to the null controls.

Raw `Mean_Vort` is insufficient when analyzed alone. Without a matched control it cannot determine whether a response originates from local organization or from preserved distributional properties.

The results do not establish physical turbulence, a universal critical point, a universal law, or validation on real-world observations.

## 7. Current limitations

- The evidence is synthetic and configuration-specific.
- The source campaign CSV files are not included in this repository snapshot.
- The approximate transition boundary has not been tested for parameter, resolution, seed-count, or sampling invariance.
- The differential statistic depends on a nonzero, adequately sampled Vector Shuffle variance.
- The method requires a shuffle reference and is not itself a purely local invariant.
- No real-world dataset has been used to validate this result.

## 8. Future work

Future work may test replication across seeds, resolutions, synthetic geometries, and alternative distribution-preserving controls. A central unresolved question is whether a future STRUX version can isolate a purely local invariant without requiring a differential shuffle baseline. Any such work is outside this frozen STRUX_V1 milestone.
