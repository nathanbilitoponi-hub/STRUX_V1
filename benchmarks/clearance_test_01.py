"""
STRUX_CLEARANCE_TEST_01

Purpose
-------
Measure transport viability as a function of:

    aperture size
    vs
    body size

Core idea
---------
A path is NOT sufficient.

Transport exists only if:
    free clearance >= body diameter

This benchmark introduces:
- effective body size
- geometric clearance threshold
- fragile vs stable passage
"""

import os
import csv
import numpy as np
import matplotlib.pyplot as plt

from scipy.ndimage import distance_transform_edt

np.random.seed(42)

# ============================================================
# CONFIG
# ============================================================

H, W = 180, 320

SOURCE = np.array([25, H // 2])
TARGET = np.array([W - 25, H // 2])

BODY_SIZE = 15

APERTURES = [4, 6, 8, 10, 12, 14, 16, 20, 26]

EXPORT_DIR = "exports/STRUX_CLEARANCE_TEST_01"
os.makedirs(EXPORT_DIR, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W]


# ============================================================
# GEOMETRY
# ============================================================

def build_scene(aperture):

    free = np.ones((H, W), dtype=np.uint8)

    wall_x1 = W // 2 - 10
    wall_x2 = W // 2 + 10

    free[:, wall_x1:wall_x2] = 0

    y0 = H // 2 - aperture // 2
    y1 = H // 2 + aperture // 2

    free[y0:y1, wall_x1:wall_x2] = 1

    return free


# ============================================================
# CLEARANCE FIELD
# ============================================================

def clearance_radius_map(free):
    return distance_transform_edt(free)


# ============================================================
# SIMPLE TRANSPORT TEST
# ============================================================

def can_body_pass(clearance_map, body_radius):

    y = H // 2

    for x in range(W):

        if clearance_map[y, x] < body_radius:
            return False

    return True


# ============================================================
# RUN
# ============================================================

results = []

print("\n=== STRUX_CLEARANCE_TEST_01 ===\n")

BODY_RADIUS = BODY_SIZE / 2

for aperture in APERTURES:

    free = build_scene(aperture)

    clearance = clearance_radius_map(free)

    success = can_body_pass(
        clearance,
        body_radius=BODY_RADIUS,
    )

    clearance_ratio = aperture / BODY_SIZE

    state = (
        "PASS"
        if success
        else "BLOCKED"
    )

    results.append({
        "aperture": aperture,
        "body_size": BODY_SIZE,
        "clearance_ratio": clearance_ratio,
        "success": success,
    })

    print(f"aperture      : {aperture}")
    print(f"body_size     : {BODY_SIZE}")
    print(f"ratio         : {clearance_ratio:.2f}")
    print(f"transport     : {state}")
    print()


# ============================================================
# SAVE CSV
# ============================================================

csv_path = os.path.join(EXPORT_DIR, "metrics.csv")

with open(csv_path, "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "aperture",
        "body_size",
        "clearance_ratio",
        "success",
    ])

    for r in results:
        writer.writerow([
            r["aperture"],
            r["body_size"],
            r["clearance_ratio"],
            r["success"],
        ])


# ============================================================
# PLOT
# ============================================================

xs = [r["clearance_ratio"] for r in results]
ys = [1 if r["success"] else 0 for r in results]

plt.figure(figsize=(7, 5))

plt.plot(xs, ys, marker="o")

plt.axvline(
    1.0,
    linestyle="--",
)

plt.xlabel("clearance_ratio = aperture/body_size")
plt.ylabel("transport success")
plt.title("STRUX Clearance Threshold")

plot_path = os.path.join(
    EXPORT_DIR,
    "clearance_threshold.png",
)

plt.tight_layout()
plt.savefig(plot_path, dpi=180)
plt.show()


# ============================================================
# VISUALIZATION
# ============================================================

fig, axes = plt.subplots(
    1,
    3,
    figsize=(12, 4),
)

sample_apertures = [8, 14, 20]

for ax, aperture in zip(axes, sample_apertures):

    free = build_scene(aperture)

    ax.imshow(free, cmap="gray", origin="lower")

    circ = plt.Circle(
        (W // 2, H // 2),
        BODY_RADIUS,
        fill=False,
        linewidth=2,
    )

    ax.add_patch(circ)

    ax.set_title(
        f"ap={aperture}"
    )

    ax.axis("off")

viz_path = os.path.join(
    EXPORT_DIR,
    "clearance_examples.png",
)

plt.tight_layout()
plt.savefig(viz_path, dpi=180)
plt.show()


# ============================================================
# SUMMARY
# ============================================================

summary_path = os.path.join(
    EXPORT_DIR,
    "summary.txt",
)

with open(summary_path, "w") as f:

    f.write("STRUX_CLEARANCE_TEST_01\n\n")

    f.write(
        "Transport viability based on body size "
        "vs aperture clearance.\n\n"
    )

    for r in results:

        state = (
            "PASS"
            if r["success"]
            else "BLOCKED"
        )

        f.write(
            f"aperture={r['aperture']} "
            f"ratio={r['clearance_ratio']:.2f} "
            f"{state}\n"
        )

print(f"Saved CSV     : {csv_path}")
print(f"Saved plot    : {plot_path}")
print(f"Saved viz     : {viz_path}")
print(f"Saved summary : {summary_path}")