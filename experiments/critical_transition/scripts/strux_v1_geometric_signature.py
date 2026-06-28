#!/usr/bin/env python3
"""Reproduce the frozen STRUX_V1 differential geometric-signature analysis.

The script reads existing campaign CSV files; it never generates synthetic input.
At every matched (shock, radial point), it computes the difference between the
STRUCTURED_SHOCK mean and VECTOR_SHUFFLE mean in units of the sample standard
deviation of VECTOR_SHUFFLE.

Accepted case-insensitive column aliases:
  condition: condition, control, sample_type, scenario, experiment, method
  shock:     shock, shock_level, disorder, disorder_level
  point:     radial_point, radial_bin, radius, bin, point
  value:     value, mean_vort, vort, vorticity, observable, score

A combined file needs a condition column. A separate file can omit it when its
name contains "structured_shock" or "vector_shuffle". Condition values are
normalized in the same way. Replicate/seed columns are allowed but not needed;
each CSV row is one observation.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np


CONDITION_ALIASES = ("condition", "control", "sample_type", "scenario", "experiment", "method")
SHOCK_ALIASES = ("shock", "shock_level", "disorder", "disorder_level")
POINT_ALIASES = ("radial_point", "radial_bin", "radius", "bin", "point")
VALUE_ALIASES = ("value", "mean_vort", "vort", "vorticity", "observable", "score")
CONDITIONS = ("STRUCTURED_SHOCK", "VECTOR_SHUFFLE")


def normalized_name(value: str) -> str:
    """Return a case-insensitive, punctuation-insensitive identifier."""
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def find_column(fieldnames: Sequence[str], aliases: Sequence[str]) -> str | None:
    by_normalized = {normalized_name(name): name for name in fieldnames}
    return next((by_normalized[alias] for alias in aliases if alias in by_normalized), None)


def condition_from_text(value: str) -> str | None:
    normalized = normalized_name(value)
    if "structured_shock" in normalized or normalized in {"structured", "shock_structured"}:
        return "STRUCTURED_SHOCK"
    if "vector_shuffle" in normalized or normalized in {"shuffle", "shuffled", "vector_shuffled"}:
        return "VECTOR_SHUFFLE"
    return None


def numeric(value: str, label: str, path: Path, row_number: int) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path}:{row_number}: non-numeric {label}: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{path}:{row_number}: non-finite {label}: {value!r}")
    return result


def load_csv(path: Path) -> list[tuple[str, float, float, float]]:
    """Load compatible observations from one CSV, or return [] if incompatible."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        shock_column = find_column(fields, SHOCK_ALIASES)
        point_column = find_column(fields, POINT_ALIASES)
        value_column = find_column(fields, VALUE_ALIASES)
        condition_column = find_column(fields, CONDITION_ALIASES)
        inferred_condition = condition_from_text(path.stem)

        if not (shock_column and point_column and value_column):
            return []
        if not condition_column and not inferred_condition:
            return []

        observations: list[tuple[str, float, float, float]] = []
        for row_number, row in enumerate(reader, start=2):
            raw_condition = row.get(condition_column, "") if condition_column else ""
            condition = condition_from_text(raw_condition) or inferred_condition
            if condition not in CONDITIONS:
                continue
            shock = numeric(row[shock_column], "shock", path, row_number)
            point = numeric(row[point_column], "radial point", path, row_number)
            value = numeric(row[value_column], "value", path, row_number)
            observations.append((condition, shock, point, value))
        return observations


def collect_inputs(paths: Sequence[Path]) -> tuple[list[tuple[str, float, float, float]], list[Path]]:
    csv_paths: list[Path] = []
    for path in paths:
        if path.is_dir():
            csv_paths.extend(sorted(path.rglob("*.csv")))
        elif path.suffix.lower() == ".csv":
            csv_paths.append(path)
        else:
            raise ValueError(f"Input is not a CSV file or directory: {path}")

    observations: list[tuple[str, float, float, float]] = []
    compatible: list[Path] = []
    for path in dict.fromkeys(csv_paths):
        loaded = load_csv(path)
        if loaded:
            observations.extend(loaded)
            compatible.append(path)
    return observations, compatible


def sample_std(values: Sequence[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) >= 2 else math.nan


def compute_pointwise(observations: Iterable[tuple[str, float, float, float]]) -> list[dict[str, float | int]]:
    grouped: dict[tuple[float, float, str], list[float]] = defaultdict(list)
    for condition, shock, point, value in observations:
        grouped[(shock, point, condition)].append(value)

    coordinates = sorted({(shock, point) for shock, point, _ in grouped})
    rows: list[dict[str, float | int]] = []
    for shock, point in coordinates:
        structured = grouped.get((shock, point, "STRUCTURED_SHOCK"), [])
        shuffled = grouped.get((shock, point, "VECTOR_SHUFFLE"), [])
        if not structured or not shuffled:
            continue
        structured_mean = float(np.mean(structured))
        shuffled_mean = float(np.mean(shuffled))
        shuffled_std = sample_std(shuffled)
        difference = structured_mean - shuffled_mean
        differential_z = difference / shuffled_std if shuffled_std > 0.0 else math.nan
        rows.append(
            {
                "shock": shock,
                "radial_point": point,
                "n_structured_shock": len(structured),
                "structured_shock_mean": structured_mean,
                "structured_shock_std": sample_std(structured),
                "n_vector_shuffle": len(shuffled),
                "vector_shuffle_mean": shuffled_mean,
                "vector_shuffle_std": shuffled_std,
                "mean_difference": difference,
                "differential_z": differential_z,
            }
        )
    return rows


def compute_summary(rows: Sequence[dict[str, float | int]]) -> list[dict[str, float | int]]:
    grouped: dict[float, list[float]] = defaultdict(list)
    total_points: dict[float, int] = defaultdict(int)
    for row in rows:
        shock = float(row["shock"])
        total_points[shock] += 1
        z_value = float(row["differential_z"])
        if math.isfinite(z_value):
            grouped[shock].append(abs(z_value))

    summary: list[dict[str, float | int]] = []
    for shock in sorted(total_points):
        values = grouped[shock]
        summary.append(
            {
                "shock": shock,
                "n_matched_points": total_points[shock],
                "n_valid_z_points": len(values),
                "mean_abs_differential_z": float(np.mean(values)) if values else math.nan,
                "max_abs_differential_z": max(values) if values else math.nan,
                "rms_differential_z": float(np.sqrt(np.mean(np.square(values)))) if values else math.nan,
            }
        )
    return summary


def write_table(path: Path, rows: Sequence[dict[str, float | int]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty table: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def configure_plotting() -> object:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    return plt


def plot_by_shock(summary: Sequence[dict[str, float | int]], path: Path) -> None:
    plt = configure_plotting()
    shocks = np.array([row["shock"] for row in summary], dtype=float)
    means = np.array([row["mean_abs_differential_z"] for row in summary], dtype=float)
    maxima = np.array([row["max_abs_differential_z"] for row in summary], dtype=float)
    fig, axis = plt.subplots(figsize=(7.2, 4.4), constrained_layout=True)
    axis.plot(shocks, means, marker="o", linewidth=1.8, label="Mean |differential Z|")
    axis.plot(shocks, maxima, marker="s", linewidth=1.4, label="Maximum |differential Z|")
    axis.axhline(0.0, color="black", linewidth=0.7)
    axis.set(xlabel="Shock", ylabel="Differential Z-score magnitude", title="STRUX_V1 local geometric signature")
    axis.legend(frameon=False)
    axis.grid(alpha=0.2)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_heatmap(rows: Sequence[dict[str, float | int]], path: Path) -> bool:
    shocks = sorted({float(row["shock"]) for row in rows})
    points = sorted({float(row["radial_point"]) for row in rows})
    lookup = {(float(row["shock"]), float(row["radial_point"])): float(row["differential_z"]) for row in rows}
    if any((shock, point) not in lookup for shock in shocks for point in points):
        return False
    values = np.array([[lookup[(shock, point)] for point in points] for shock in shocks])
    plt = configure_plotting()
    fig, axis = plt.subplots(figsize=(7.6, 4.8), constrained_layout=True)
    finite = np.abs(values[np.isfinite(values)])
    limit = float(finite.max()) if finite.size else 1.0
    image = axis.imshow(values, aspect="auto", origin="lower", cmap="coolwarm", vmin=-limit, vmax=limit)
    axis.set(
        xlabel="Radial point index",
        ylabel="Shock index",
        title="Pointwise differential Z-score vs Vector Shuffle",
        xticks=np.arange(len(points)),
        yticks=np.arange(len(shocks)),
        xticklabels=[f"{value:g}" for value in points],
        yticklabels=[f"{value:g}" for value in shocks],
    )
    if len(points) > 20:
        for index, label in enumerate(axis.get_xticklabels()):
            label.set_visible(index % max(1, len(points) // 10) == 0)
    fig.colorbar(image, ax=axis, label="Differential Z-score")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return True


def print_summary(summary: Sequence[dict[str, float | int]]) -> None:
    print("\nPer-shock summary (descriptive; no survival threshold applied)")
    print("shock  matched  valid_z  mean_abs_z  max_abs_z  rms_z")
    for row in summary:
        print(
            f"{float(row['shock']):5g}  {int(row['n_matched_points']):7d}  "
            f"{int(row['n_valid_z_points']):7d}  {float(row['mean_abs_differential_z']):10.5g}  "
            f"{float(row['max_abs_differential_z']):9.5g}  {float(row['rms_differential_z']):7.5g}"
        )


def parse_args() -> argparse.Namespace:
    script = Path(__file__).resolve()
    experiment_dir = script.parents[1]
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", nargs="+", type=Path, help="CSV files or directories containing campaign data")
    parser.add_argument("--output-dir", type=Path, default=experiment_dir / "results", help="generated output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    script = Path(__file__).resolve()
    default_input = script.parents[1] / "input"
    inputs = args.input or [default_input]
    missing = [path for path in inputs if not path.exists()]
    if missing:
        print("Input path does not exist: " + ", ".join(str(path) for path in missing), file=sys.stderr)
        print("Supply existing campaign CSVs with --input. No synthetic data were generated.", file=sys.stderr)
        return 2

    try:
        observations, compatible = collect_inputs(inputs)
        if not compatible:
            raise ValueError("No compatible CSV found. Run with --help for the accepted schema and aliases.")
        rows = compute_pointwise(observations)
        if not rows:
            raise ValueError("No matched STRUCTURED_SHOCK and VECTOR_SHUFFLE coordinates were found.")
        summary = compute_summary(rows)
        # Check the plotting dependency before creating any output, so a missing
        # environment requirement cannot leave a partial report behind.
        configure_plotting()
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        write_table(output_dir / "strux_v1_geometric_signature_report.csv", rows)
        write_table(output_dir / "strux_v1_geometric_signature_summary.csv", summary)
        plot_by_shock(summary, output_dir / "strux_v1_geometric_signature_by_shock.png")
        heatmap_written = plot_heatmap(rows, output_dir / "strux_v1_geometric_signature_heatmap.png")
    except (ImportError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print("Loaded compatible inputs:")
    for path in compatible:
        print(f"  {path}")
    print_summary(summary)
    if not heatmap_written:
        print("Heatmap skipped because the matched shock/point coordinates do not form a complete grid.")
    print(f"\nOutputs written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
