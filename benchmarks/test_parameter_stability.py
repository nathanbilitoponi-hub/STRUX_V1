"""
STRUX_V1 — Parameter Stability Benchmark

Goal:
Evaluate how sensitive STRUX filament scoring is to changes in:

- base_radius
- tube_radius

This benchmark checks whether the detected structure is stable
or heavily dependent on parameter tuning.

This is NOT a proof of universal robustness.
It is a controlled parameter-sensitivity benchmark.
"""

# ============================================================
# Imports
# ============================================================

import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# STRUX connection scoring core
# ============================================================

def _point_segment_projection(points, p1, p2):
    axis = p2 - p1
    seg_len = float(np.linalg.norm(axis))

    if seg_len < 1e-12:
        return 0.0, np.zeros(len(points)), np.full(len(points), np.inf)

    u = axis / seg_len

    rel = points - p1[None, :]
    t = rel @ u

    t_clamped = np.clip(t, 0.0, seg_len)

    proj = p1[None, :] + t_clamped[:, None] * u[None, :]
    dist_to_axis = np.linalg.norm(points - proj, axis=1)

    return seg_len, t_clamped, dist_to_axis


def _continuity_score(t_along_support, seg_len, n_bins=20):
    if seg_len < 1e-12 or len(t_along_support) == 0:
        return 0.0

    bins = np.linspace(0.0, seg_len, n_bins + 1)

    hist, _ = np.histogram(
        t_along_support,
        bins=bins,
    )

    occupied = hist > 0

    return float(np.mean(occupied))


def _coverage_score(n_support_points, seg_len):
    if seg_len < 1e-12:
        return 0.0

    return float(n_support_points / seg_len)


def _central_density_ratio(
    points_support,
    p1,
    p2,
    tube_radius,
    center_fraction=0.35,
):
    if len(points_support) == 0:
        return 0.0

    seg_len, _, dist_to_axis = _point_segment_projection(
        points_support,
        p1,
        p2,
    )

    if seg_len < 1e-12:
        return 0.0

    inner_radius = max(
        tube_radius * center_fraction,
        1e-12,
    )

    n_inner = np.sum(dist_to_axis <= inner_radius)

    return float(n_inner / max(len(points_support), 1))


def score_pair_connection(
    points,
    p1,
    p2,
    tube_radius=0.35,
    n_bins=20,
    strong_continuity_thr=0.6,
    weak_continuity_thr=0.4,
    strong_coverage_thr=0.5,
    strong_central_ratio_thr=0.08,
):
    points = np.asarray(points, dtype=float)

    seg_len, t_along, dist_to_axis = _point_segment_projection(
        points,
        p1,
        p2,
    )

    mask = (
        (t_along >= 0.0)
        & (t_along <= seg_len)
        & (dist_to_axis <= tube_radius)
    )

    support_points = points[mask]
    t_support = t_along[mask]

    continuity = _continuity_score(
        t_support,
        seg_len,
        n_bins=n_bins,
    )

    coverage = _coverage_score(
        len(support_points),
        seg_len,
    )

    central_density_ratio = _central_density_ratio(
        support_points,
        p1,
        p2,
        tube_radius,
    )

    if (
        continuity >= strong_continuity_thr
        and coverage >= strong_coverage_thr
        and central_density_ratio >= strong_central_ratio_thr
    ):
        label = "strong filament"

    elif continuity >= weak_continuity_thr:
        label = "weak filament"

    else:
        label = "none"

    return {
        "class": label,
        "continuity": continuity,
        "coverage": coverage,
        "central_density_ratio": central_density_ratio,
        "n_support_points": len(support_points),
    }


# ============================================================
# Synthetic dataset
# ============================================================

rng = np.random.default_rng(42)

n_blob = 180
n_corridor = 140

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


# ============================================================
# Parameter sweep
# ============================================================

tube_radius_values = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.45,
    0.60,
]

rows = []

print("=== STRUX PARAMETER STABILITY TEST ===")
print()

for tr in tube_radius_values:

    score = score_pair_connection(
        points,
        p1,
        p2,
        tube_radius=tr,
    )

    row = {
        "tube_radius": tr,
        "class": score["class"],
        "continuity": score["continuity"],
        "coverage": score["coverage"],
        "central_density_ratio": score["central_density_ratio"],
        "support": score["n_support_points"],
    }

    rows.append(row)

    print(
        f"tube_radius={tr:.2f} | "
        f"class={row['class']} | "
        f"continuity={row['continuity']:.3f} | "
        f"coverage={row['coverage']:.3f} | "
        f"central_density={row['central_density_ratio']:.3f} | "
        f"support={row['support']}"
    )


# ============================================================
# Stability analysis
# ============================================================

classes = [r["class"] for r in rows]

strong_count = sum(c == "strong filament" for c in classes)

print()
print("=== STABILITY VERDICT ===")

if strong_count >= 6:
    print("PASS STRONG")
    print(
        "Filament classification remains stable across "
        "a broad tube_radius range."
    )

elif strong_count >= 4:
    print("PASS PARTIAL")
    print(
        "Filament detection is moderately stable "
        "but parameter-sensitive."
    )

else:
    print("FRAGILE")
    print(
        "Filament classification strongly depends "
        "on parameter tuning."
    )


# ============================================================
# Plot
# ============================================================

x = [r["tube_radius"] for r in rows]

continuity = [r["continuity"] for r in rows]
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

plt.xlabel("tube_radius")
plt.ylabel("score")
plt.title("STRUX_V1 Parameter Stability Benchmark")

plt.grid(True, alpha=0.3)
plt.legend()

plt.show()

plt.savefig(
    "benchmarks/test_parameter_stability_result.png",
    dpi=220,
    bbox_inches="tight",
)