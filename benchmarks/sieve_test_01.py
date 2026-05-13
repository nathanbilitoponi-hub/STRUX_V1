"""
STRUX_APERTURE_TEST_01

Purpose
-------
Measure the minimum viable transport aperture.

Core question
-------------
Does STRUX measure simple binary connectivity,
or effective geometric transport viability?

Setup
-----
A single wall separates source and target.
Only one aperture exists.
We vary aperture height and measure:

- success_rate
- direction_coherence
- gate mode count
- transport_class

Expected behavior
-----------------
Small aperture:
    low success / trapped

Large aperture:
    high success / single coherent channel

This test estimates a critical aperture threshold.
"""

import os
import csv
import numpy as np
import matplotlib.pyplot as plt

from scipy.ndimage import distance_transform_edt

from core.transport.transport_diagnosis_v1 import diagnose_transport


np.random.seed(42)

H, W = 180, 340
SOURCE = np.array([18, H // 2])
TARGET = np.array([W - 18, H // 2])

N_PARTICLES = 500
MAX_STEPS = 1200
STEP = 1.0
NOISE = 0.035
HIT_RADIUS = 14

X_GATE = W // 2

APERTURE_HEIGHTS = [2, 4, 6, 8, 12, 16, 22, 30, 44, 60]

EXPORT_DIR = "exports/STRUX_APERTURE_TEST_01"
os.makedirs(EXPORT_DIR, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W]


def make_base_room():
    free = np.ones((H, W), dtype=np.uint8)
    free[:8, :] = 0
    free[-8:, :] = 0
    free[:, :8] = 0
    free[:, -8:] = 0
    return free


def make_aperture_scene(aperture_height):
    free = make_base_room()

    wall_x1, wall_x2 = W // 2 - 10, W // 2 + 10
    free[:, wall_x1:wall_x2] = 0

    y1 = H // 2 - aperture_height // 2
    y2 = H // 2 + aperture_height // 2

    free[y1:y2, wall_x1:wall_x2] = 1

    return free


def local_field(free):
    dist = distance_transform_edt(free)
    gy, gx = np.gradient(dist.astype(float))
    norm = np.sqrt(gx * gx + gy * gy) + 1e-9
    return gx / norm, gy / norm


def interpolate_gate_crossing(p0, p1, x_gate):
    x0, y0 = p0
    x1, y1 = p1

    if (x0 - x_gate) * (x1 - x_gate) > 0:
        return None

    if abs(x1 - x0) < 1e-12:
        return None

    t = (x_gate - x0) / (x1 - x0)

    if t < 0 or t > 1:
        return None

    return float(y0 + t * (y1 - y0))


def run_transport(free):
    gx, gy = local_field(free)

    trajectories = []
    successes = []
    coherences = []
    gate_values = []

    for _ in range(N_PARTICLES):
        pos = SOURCE.astype(float).copy()

        a = np.random.uniform(-0.18, 0.18)
        D = np.array([1.0, a])
        D /= np.linalg.norm(D) + 1e-9

        path = [pos.copy()]
        local_align = []
        success = False
        gate_y = None

        for _ in range(MAX_STEPS):
            x = int(np.clip(round(pos[0]), 0, W - 1))
            y = int(np.clip(round(pos[1]), 0, H - 1))

            if free[y, x] == 0:
                break

            G = np.array([gx[y, x], gy[y, x]])

            if np.linalg.norm(G) > 1e-6:
                D = 0.88 * D + 0.12 * G

            to_target = TARGET - pos
            to_target /= np.linalg.norm(to_target) + 1e-9

            D = 0.90 * D + 0.10 * to_target
            D += NOISE * np.random.randn(2)
            D /= np.linalg.norm(D) + 1e-9

            new = pos + STEP * D

            nx = int(np.clip(round(new[0]), 0, W - 1))
            ny = int(np.clip(round(new[1]), 0, H - 1))

            if free[ny, nx] == 0:
                N = np.array([gx[y, x], gy[y, x]])

                if np.linalg.norm(N) < 1e-6:
                    break

                D = D - 2 * np.dot(D, N) * N
                D /= np.linalg.norm(D) + 1e-9

                new = pos + STEP * D

                nx = int(np.clip(round(new[0]), 0, W - 1))
                ny = int(np.clip(round(new[1]), 0, H - 1))

                if free[ny, nx] == 0:
                    break

            if gate_y is None:
                gy_cross = interpolate_gate_crossing(pos, new, X_GATE)
                if gy_cross is not None:
                    gate_y = gy_cross

            pos = new
            path.append(pos.copy())
            local_align.append(np.dot(D, to_target))

            if np.linalg.norm(pos - TARGET) < HIT_RADIUS:
                success = True
                break

        trajectories.append(np.array(path))
        successes.append(success)
        coherences.append(np.mean(local_align) if len(local_align) else 0)

        if success and gate_y is not None:
            gate_values.append(gate_y)

    success_rate = float(np.mean(successes))
    direction_coherence = float(np.mean(coherences))

    diagnosis = diagnose_transport(
        success_rate=success_rate,
        direction_coherence=direction_coherence,
        gate_values=np.array(gate_values),
        height=H,
    )

    diagnosis["trajectories"] = trajectories
    diagnosis["successes"] = successes
    diagnosis["gate_values"] = gate_values

    return diagnosis


results = {}

print("\n=== STRUX_APERTURE_TEST_01 ===\n")

for aperture in APERTURE_HEIGHTS:
    free = make_aperture_scene(aperture)
    metrics = run_transport(free)

    results[aperture] = {
        "free": free,
        "metrics": metrics,
    }

    print(f"aperture_height = {aperture}")
    print(f"  success_rate        : {metrics['success_rate']:.4f}")
    print(f"  direction_coherence : {metrics['direction_coherence']:.4f}")
    print(f"  detected_modes      : {metrics['n_modes']}")
    print(f"  transport_class     : {metrics['transport_class']}")
    print()


csv_path = os.path.join(EXPORT_DIR, "metrics.csv")

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "aperture_height",
        "success_rate",
        "direction_coherence",
        "detected_modes",
        "transport_class",
        "n_gate_values",
    ])

    for aperture, r in results.items():
        m = r["metrics"]
        writer.writerow([
            aperture,
            m["success_rate"],
            m["direction_coherence"],
            m["n_modes"],
            m["transport_class"],
            len(m["gate_values"]),
        ])


# Plot: aperture vs success
apertures = np.array(list(results.keys()))
successes = np.array([results[a]["metrics"]["success_rate"] for a in apertures])
coherences = np.array([results[a]["metrics"]["direction_coherence"] for a in apertures])
modes = np.array([results[a]["metrics"]["n_modes"] for a in apertures])

plt.figure(figsize=(9, 5))
plt.plot(apertures, successes, marker="o", label="success_rate")
plt.plot(apertures, coherences, marker="o", label="direction_coherence")
plt.plot(apertures, modes / max(1, modes.max()), marker="o", label="n_modes normalized")
plt.xlabel("aperture height")
plt.ylabel("metric value")
plt.title("STRUX_APERTURE_TEST_01 — Critical Aperture Threshold")
plt.grid(alpha=0.25)
plt.legend()
plt.tight_layout()

plot_path = os.path.join(EXPORT_DIR, "aperture_metrics.png")
plt.savefig(plot_path, dpi=180)
plt.show()


# Visualize selected apertures
selected = [2, 8, 16, 30, 60]
fig, axes = plt.subplots(1, len(selected), figsize=(4 * len(selected), 4))

for ax, aperture in zip(axes, selected):
    r = results[aperture]
    free = r["free"]
    m = r["metrics"]

    ax.imshow(free, cmap="gray", origin="lower")
    ax.axvline(X_GATE, color="yellow", linewidth=2)

    ax.set_title(
        f"h={aperture}\n"
        f"sr={m['success_rate']:.2f}, modes={m['n_modes']}"
    )

    ax.axis("off")

    for path, success in zip(m["trajectories"], m["successes"]):
        if len(path) < 2:
            continue

        color = "dodgerblue" if success else "red"
        alpha = 0.50 if success else 0.06

        ax.plot(
            path[:, 0],
            path[:, 1],
            color=color,
            linewidth=0.5,
            alpha=alpha,
        )

    if len(m["gate_values"]) > 0:
        ax.scatter(
            np.full_like(m["gate_values"], X_GATE),
            m["gate_values"],
            c="orange",
            s=10,
            edgecolor="black",
            linewidth=0.2,
            zorder=5,
        )

    ax.scatter(SOURCE[0], SOURCE[1], c="lime", s=50, edgecolor="black")
    ax.scatter(TARGET[0], TARGET[1], c="cyan", marker="*", s=80, edgecolor="black")

plt.tight_layout()

viz_path = os.path.join(EXPORT_DIR, "aperture_selected.png")
plt.savefig(viz_path, dpi=180)
plt.show()


summary_path = os.path.join(EXPORT_DIR, "summary.txt")

with open(summary_path, "w") as f:
    f.write("STRUX_APERTURE_TEST_01\n\n")
    f.write("Purpose: estimate minimum viable transport aperture.\n\n")

    for aperture, r in results.items():
        m = r["metrics"]
        f.write(f"aperture_height = {aperture}\n")
        f.write(f"  success_rate        : {m['success_rate']:.4f}\n")
        f.write(f"  direction_coherence : {m['direction_coherence']:.4f}\n")
        f.write(f"  detected_modes      : {m['n_modes']}\n")
        f.write(f"  transport_class     : {m['transport_class']}\n\n")

print(f"Saved CSV     : {csv_path}")
print(f"Saved plot    : {plot_path}")
print(f"Saved viz     : {viz_path}")
print(f"Saved summary : {summary_path}")