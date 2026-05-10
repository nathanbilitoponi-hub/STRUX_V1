"""
STRUX_V1 — False Filament Test

Goal:
Verify that tube-based filament scoring does NOT automatically
create strong filaments between nearby unsupported regions.

Test:
- FALSE CASE:
  two nearby blobs without a corridor

- TRUE CASE:
  two blobs connected by a real corridor

Expected:
FALSE CASE -> not "strong filament"
TRUE CASE  -> "strong filament"

This benchmark validates that continuity occupancy contributes
to filament classification beyond simple proximity.
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
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)

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
        "segment_length": float(seg_len),
        "n_support_points": int(len(support_points)),
        "continuity": float(continuity),
        "coverage": float(coverage),
        "central_density_ratio": float(central_density_ratio),
        "support_points": support_points,
        "t_support": t_support,
    }


# ============================================================
# Synthetic dataset
# FALSE CASE:
# two blobs without corridor
# ============================================================

rng = np.random.default_rng(11)

n_blob = 180

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

# Noise away from corridor
noise = rng.uniform(
    low=[-0.5, 0.8, -0.4],
    high=[3.5, 1.6, 0.4],
    size=(80, 3),
)

points_false = np.vstack([
    blob_A,
    blob_B,
    noise,
])

p1 = blob_A.mean(axis=0)
p2 = blob_B.mean(axis=0)


# ============================================================
# TRUE CASE:
# add real corridor
# ============================================================

n_corridor = 120

t = np.linspace(0, 1, n_corridor)

corridor = (
    p1[None, :] * (1 - t[:, None])
    + p2[None, :] * t[:, None]
)

corridor += rng.normal(
    scale=0.08,
    size=corridor.shape,
)

points_true = np.vstack([
    blob_A,
    blob_B,
    corridor,
    noise,
])


# ============================================================
# Run scoring
# ============================================================

tube_radius = 0.30

false_score = score_pair_connection(
    points_false,
    p1,
    p2,
    tube_radius=tube_radius,
)

true_score = score_pair_connection(
    points_true,
    p1,
    p2,
    tube_radius=tube_radius,
)


# ============================================================
# Print results
# ============================================================

print("=== STRUX FALSE FILAMENT TEST ===")
print()

print("FALSE CASE — two blobs, no corridor")
print()

for k, v in false_score.items():
    if k not in ["support_points", "t_support"]:
        print(f"{k}: {v}")

print()
print("TRUE CASE — two blobs with real corridor")
print()

for k, v in true_score.items():
    if k not in ["support_points", "t_support"]:
        print(f"{k}: {v}")

print()
print("=== VERDICT ===")

if (
    false_score["class"] != "strong filament"
    and true_score["class"] == "strong filament"
):
    print("PASS")
    print(
        "Tube scoring distinguishes unsupported proximity "
        "from true corridor support."
    )

elif false_score["class"] == "strong filament":
    print("FAIL")
    print(
        "STRUX creates a false strong filament "
        "between unsupported blobs."
    )

elif true_score["class"] != "strong filament":
    print("PASS PARTIAL / TOO CONSERVATIVE")
    print(
        "STRUX avoids false positive, "
        "but also misses the real corridor."
    )

else:
    print("AMBIGUOUS")


# ============================================================
# Visualization
# ============================================================

fig = plt.figure(figsize=(14, 6))

# FALSE CASE
ax1 = fig.add_subplot(121, projection="3d")

ax1.scatter(
    points_false[:, 0],
    points_false[:, 1],
    points_false[:, 2],
    s=8,
    alpha=0.35,
)

ax1.scatter(
    [p1[0], p2[0]],
    [p1[1], p2[1]],
    [p1[2], p2[2]],
    s=80,
)

ax1.plot(
    [p1[0], p2[0]],
    [p1[1], p2[1]],
    [p1[2], p2[2]],
    linewidth=3,
)

ax1.set_title(
    f"FALSE CASE: {false_score['class']}"
)

# TRUE CASE
ax2 = fig.add_subplot(122, projection="3d")

ax2.scatter(
    points_true[:, 0],
    points_true[:, 1],
    points_true[:, 2],
    s=8,
    alpha=0.35,
)

ax2.scatter(
    [p1[0], p2[0]],
    [p1[1], p2[1]],
    [p1[2], p2[2]],
    s=80,
)

ax2.plot(
    [p1[0], p2[0]],
    [p1[1], p2[1]],
    [p1[2], p2[2]],
    linewidth=3,
)

ax2.set_title(
    f"TRUE CASE: {true_score['class']}"
)

plt.tight_layout()

plt.savefig(
    "test_false_filament_result.png",
    dpi=220,
    bbox_inches="tight",
)

plt.show()