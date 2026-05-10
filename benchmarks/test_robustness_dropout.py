"""
STRUX_V1 — Robustness Dropout Benchmark

Goal:
Test whether STRUX filament scoring remains stable when random points
are removed from a synthetic corridor-supported structure.

This benchmark checks whether the detected strong filament survives
under increasing random dropout.

It does NOT prove real-world robustness.
It only tests controlled synthetic dropout stability.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import numpy as np
import matplotlib.pyplot as plt

from core.connection_scoring.connection_scoring import score_pair_connection


def make_corridor_dataset(seed=21):
    rng = np.random.default_rng(seed)

    n_blob = 180
    n_corridor = 160

    blob_A = rng.normal(
        loc=[0.0, 0.0, 0.0],
        scale=0.22,
        size=(n_blob, 3),
    )

    blob_B = rng.normal(
        loc=[3.0, 0.0, 0.0],
        scale=0.22,
        size=(n_blob, 3),
    )

    p1 = blob_A.mean(axis=0)
    p2 = blob_B.mean(axis=0)

    t = np.linspace(0, 1, n_corridor)

    corridor = (
        p1[None, :] * (1 - t[:, None])
        + p2[None, :] * t[:, None]
    )

    corridor += rng.normal(
        scale=0.08,
        size=corridor.shape,
    )

    noise = rng.uniform(
        low=[-0.5, 0.8, -0.4],
        high=[3.5, 1.6, 0.4],
        size=(80, 3),
    )

    points = np.vstack([
        blob_A,
        blob_B,
        corridor,
        noise,
    ])

    return points, p1, p2


def apply_dropout(points, dropout_rate, seed=0):
    rng = np.random.default_rng(seed)

    n = len(points)
    keep_n = int(round(n * (1.0 - dropout_rate)))

    idx = rng.choice(
        n,
        size=keep_n,
        replace=False,
    )

    return points[np.sort(idx)]


def run_dropout_test():
    points, p1, p2 = make_corridor_dataset(seed=21)

    dropout_rates = [
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
    ]

    rows = []

    for i, dropout in enumerate(dropout_rates):
        dropped = apply_dropout(
            points,
            dropout_rate=dropout,
            seed=100 + i,
        )

        score = score_pair_connection(
            dropped,
            p1,
            p2,
            tube_radius=0.30,
        )

        row = {
            "dropout": dropout,
            "remaining_points": len(dropped),
            "class": score["class"],
            "continuity": score["continuity"],
            "coverage": score["coverage"],
            "central_density_ratio": score["central_density_ratio"],
            "n_support_points": score["n_support_points"],
        }

        rows.append(row)

    return rows


def print_report(rows):
    print("=== STRUX ROBUSTNESS DROPOUT TEST ===")
    print()

    for r in rows:
        print(
            f"dropout={r['dropout']:.1f} | "
            f"remaining={r['remaining_points']} | "
            f"class={r['class']} | "
            f"continuity={r['continuity']:.3f} | "
            f"coverage={r['coverage']:.3f} | "
            f"central_density={r['central_density_ratio']:.3f} | "
            f"support={r['n_support_points']}"
        )

    print()
    print("=== VERDICT ===")

    strong_until = [
        r["dropout"]
        for r in rows
        if r["class"] == "strong filament"
    ]

    if len(strong_until) == 0:
        print("FAIL")
        print("The real corridor is not detected even without dropout.")
        return

    max_strong = max(strong_until)

    if max_strong >= 0.3:
        print("PASS")
        print(
            "The supported filament remains classified as strong "
            "under at least 30% random point dropout."
        )
    elif max_strong >= 0.2:
        print("PASS PARTIAL")
        print(
            "The supported filament remains strong up to 20% dropout, "
            "but degrades before 30%."
        )
    else:
        print("WEAK")
        print(
            "The supported filament is sensitive to small random dropout."
        )


def plot_results(rows):
    x = [r["dropout"] for r in rows]

    continuity = [r["continuity"] for r in rows]
    coverage = [r["coverage"] for r in rows]
    central = [r["central_density_ratio"] for r in rows]

    plt.figure(figsize=(9, 6))

    plt.plot(
        x,
        continuity,
        marker="o",
        label="continuity",
    )

    plt.plot(
        x,
        central,
        marker="o",
        label="central_density_ratio",
    )

    plt.xlabel("Random dropout rate")
    plt.ylabel("Score")
    plt.title("STRUX_V1 Robustness Dropout Benchmark")

    plt.grid(True, alpha=0.3)
    plt.legend()

    out_path = Path(__file__).resolve().parent / "test_robustness_dropout_result.png"

    plt.savefig(
        out_path,
        dpi=220,
        bbox_inches="tight",
    )

    plt.show()


if __name__ == "__main__":
    rows = run_dropout_test()
    print_report(rows)
    plot_results(rows)