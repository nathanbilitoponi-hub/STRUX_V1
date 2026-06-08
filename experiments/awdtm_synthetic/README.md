# STRUX AWDTM Synthetic Validation

## Validated Component

```text
W_V5 = rho_hat^2 * omni_inv^4
```

## Main Result Over 10 Seeds

### Unweighted DTM K160

```text
30% contamination = 0.000 ± 0.000
50% contamination = 0.000 ± 0.000
```

### STRUX AWDTM V5 K1200

```text
30% contamination = 0.925 ± 0.087
50% contamination = 0.900 ± 0.099
```

### STRUX Pruned DTM Tau100

```text
30% contamination = 0.963 ± 0.060
50% contamination = 0.912 ± 0.084
```

## Status

PASS: controlled synthetic multi-seed field validation.

## Limits

This benchmark applies only to controlled synthetic void-like point clouds with known ground truth.
It is not a claim about real cosmology, universal geometry, porous materials, or real-world datasets.

## Files

```text
strux_weight_diagnostic_01.py
strux_multiseed_field_validation_04.py
results/strux_multiseed_summary.csv
```

The scripts are self-contained and do not require external datasets.
