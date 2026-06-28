# Generated results

This directory is the default output location for `scripts/strux_v1_geometric_signature.py`.

## Expected outputs

- `strux_v1_geometric_signature_report.csv`: pointwise table containing the matched shock level and radial point, condition sample counts, condition means and standard deviations, the Vector Shuffle reference statistics, the mean difference, and the differential Z-score.
- `strux_v1_geometric_signature_summary.csv`: per-shock summary table containing the number of valid points and descriptive magnitude statistics. It does not impose a survival threshold.
- `strux_v1_geometric_signature_heatmap.png`: differential Z-score over shock level and radial point when the input forms a complete grid.
- `strux_v1_geometric_signature_by_shock.png`: per-shock mean and maximum absolute differential Z-score.

The script also prints the per-shock summary table to the console.

## Input contract

Run from the repository root, for example:

```bash
python experiments/critical_transition/scripts/strux_v1_geometric_signature.py \
  --input path/to/structured_shock.csv path/to/vector_shuffle.csv
```

A combined CSV may instead identify both conditions in a condition column. Column matching is case-insensitive and accepts the aliases documented by `--help`. Separate files without a condition column must contain `structured_shock` or `vector_shuffle` in their file names.

Each row must provide a shock level, a radial point/bin, and the measured value. Replicate or seed columns may be present but are not required because each row is treated as one observation at its `(condition, shock, point)` coordinate.

If `--input` is omitted, the script searches CSV files below `experiments/critical_transition/input/`. It exits with an explanatory error when no compatible input is found.

Generated data and plots should not be committed unless they are being intentionally archived as part of a reviewed frozen snapshot. This README is the only result artifact committed by default.
