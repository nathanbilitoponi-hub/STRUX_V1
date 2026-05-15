"""
STRUX_BIFURCATING_CORRIDOR_TEST_01

Purpose
-------
Test whether gate_mode_count detects
multiple independent transport branches.

Core question
-------------
Does gate_mode_count measure:
- true transport branching?
or
- only global connectivity?

Geometry
--------
Single entry corridor splitting into:
- upper branch
- lower branch

Both branches independently reach the exit region.
"""

import os
import csv
import numpy as np
import matplotlib.pyplot as plt

from scipy.ndimage import distance_transform_edt

from core.transport.transport_diagnosis_v1 import diagnose_transport


np.random.seed(42)

# ============================================================
# CONFIG
# ============================================================

H, W = 220, 360

SOURCE = np.array([20, H // 2])
TARGET_A = np.array([W - 25, int(H * 0.72)])
TARGET_B = np.array([W - 25, int(H * 0.28)])

N_PARTICLES = 600

MAX_STEPS = 1500
STEP = 1.0
NOISE = 0.035

HIT_RADIUS = 14
CORRIDOR_RADIUS = 8

X_GATE = int(W * 0.82)

EXPORT_DIR = "exports/STRUX_BIFURCATING_CORRIDOR_TEST_01"
os.makedirs(EXPORT_DIR, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W]


# ============================================================
# HELPERS
# ============================================================

def carve_disk(free, cx, cy, r):
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    free[d2 <= r * r] = 1
    return free


def carve_corridor(centerline, radius=CORRIDOR_RADIUS):
    free = np.zeros((H, W), dtype=np.uint8)

    for x0, y0 in centerline:
        free = carve_disk(free, x0, y0, radius)

    return free


# ============================================================
# GEOMETRY
# ============================================================

# shared trunk
trunk_x = np.linspace(25, 160, 220)
trunk_y = np.full_like(trunk_x, H / 2)

# upper branch
upper_x = np.linspace(160, W - 25, 260)
upper_y = np.linspace(H / 2, H * 0.72, 260)

# lower branch
lower_x = np.linspace(160, W - 25, 260)
lower_y = np.linspace(H / 2, H * 0.28, 260)

trunk = np.vstack([trunk_x, trunk_y]).T
upper = np.vstack([upper_x, upper_y]).T
lower = np.vstack([lower_x, lower_y]).T

centerline = np.vstack([trunk, upper, lower])

free = carve_corridor(centerline)

free = carve_disk(free, *SOURCE, 14)
free = carve_disk(free, *TARGET_A, 14)
free = carve_disk(free, *TARGET_B, 14)


# ============================================================
# FIELD
# ============================================================

def local_field(free):
    dist = distance_transform_edt(free)

    gy, gx = np.gradient(dist.astype(float))

    norm = np.sqrt(gx * gx + gy * gy) + 1e-9

    return gx / norm, gy / norm


# ============================================================
# GATE CROSSING
# ============================================================

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


# ============================================================
# TRANSPORT
# ============================================================

def run_transport():
    gx, gy = local_field(free)

    trajectories = []
    successes = []
    coherences = []
    gate_values = []

    for _ in range(N_PARTICLES):
        pos = SOURCE.astype(float).copy()

        a = np.random.uniform(-0.15, 0.15)

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

            # choose nearest target dynamically
            dA = np.linalg.norm(TARGET_A - pos)
            dB = np.linalg.norm(TARGET_B - pos)

            T = TARGET_A if dA < dB else TARGET_B

            to_target = T - pos
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

            if (
                np.linalg.norm(pos - TARGET_A) < HIT_RADIUS
                or np.linalg.norm(pos - TARGET_B) < HIT_RADIUS
            ):
                success = True
                break

        trajectories.append(np.array(path))
        successes.append(success)

        coherences.append(
            np.mean(local_align) if len(local_align) else 0
        )

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


# ============================================================
# RUN
# ============================================================

print("\n=== STRUX_BIFURCATING_CORRIDOR_TEST_01 ===\n")

metrics = run_transport()

print(f"success_rate        : {metrics['success_rate']:.4f}")
print(f"direction_coherence : {metrics['direction_coherence']:.4f}")
print(f"detected_modes      : {metrics['n_modes']}")
print(f"transport_class     : {metrics['transport_class']}")
print()

# ============================================================
# VISUALIZATION
# ============================================================

plt.figure(figsize=(10, 6))

plt.imshow(free, cmap="gray", origin="lower")

plt.axvline(X_GATE, color="yellow", linewidth=2)

for path, success in zip(metrics["trajectories"], metrics["successes"]):
    if len(path) < 2:
        continue

    color = "dodgerblue" if success else "red"
    alpha = 0.45 if success else 0.05

    plt.plot(
        path[:, 0],
        path[:, 1],
        color=color,
        linewidth=0.5,
        alpha=alpha,
    )

if len(metrics["gate_values"]) > 0:
    plt.scatter(
        np.full_like(metrics["gate_values"], X_GATE),
        metrics["gate_values"],
        c="orange",
        s=10,
        edgecolor="black",
        linewidth=0.2,
        zorder=5,
    )

plt.scatter(SOURCE[0], SOURCE[1], c="lime", s=60, edgecolor="black")

plt.scatter(TARGET_A[0], TARGET_A[1], c="cyan", s=70, marker="*")
plt.scatter(TARGET_B[0], TARGET_B[1], c="cyan", s=70, marker="*")

plt.title(
    f"Modes={metrics['n_modes']} | "
    f"Success={metrics['success_rate']:.2f}"
)

plt.axis("off")
plt.tight_layout()

viz_path = os.path.join(
    EXPORT_DIR,
    "bifurcating_corridor.png",
)

plt.savefig(viz_path, dpi=180)

plt.show()


# ============================================================
# SAVE SUMMARY
# ============================================================

summary_path = os.path.join(EXPORT_DIR, "summary.txt")

with open(summary_path, "w") as f:
    f.write("STRUX_BIFURCATING_CORRIDOR_TEST_01\n\n")

    f.write(
        f"success_rate        : {metrics['success_rate']:.4f}\n"
    )
    f.write(
        f"direction_coherence : {metrics['direction_coherence']:.4f}\n"
    )
    f.write(
        f"detected_modes      : {metrics['n_modes']}\n"
    )
    f.write(
        f"transport_class     : {metrics['transport_class']}\n"
    )

print(f"Saved visualization : {viz_path}")
print(f"Saved summary       : {summary_path}")