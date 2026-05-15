"""
STRUX_DIAMOND_COMPONENT_TEST_01

Purpose
-------
Test whether STRUX distinguishes:

A) One connected diamond transport system
B) Two separated transport components
C) One active transport component through selective blockage

Core question
-------------
Does STRUX count visible branches,
or active transport components?

Expected interpretation
-----------------------
A_DIAMOND_CONNECTED:
    one connected transport system

B_DIAMOND_BROKEN:
    two separated systems / two active components if both are fed

C_DIAMOND_SELECTIVE:
    one active channel because one branch is blocked

This test is exploratory.
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

SOURCE_TOP = np.array([22, int(H * 0.35)])
SOURCE_BOTTOM = np.array([22, int(H * 0.65)])

TARGET_TOP = np.array([W - 25, int(H * 0.35)])
TARGET_BOTTOM = np.array([W - 25, int(H * 0.65)])

N_PARTICLES_PER_SOURCE = 300
MAX_STEPS = 1500
STEP = 1.0
NOISE = 0.035
HIT_RADIUS = 14

CORRIDOR_RADIUS = 8
X_GATE = int(W * 0.72)

EXPORT_DIR = "exports/STRUX_DIAMOND_COMPONENT_TEST_01"
os.makedirs(EXPORT_DIR, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W]


# ============================================================
# HELPERS
# ============================================================

def carve_disk(free, cx, cy, r):
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    free[d2 <= r * r] = 1
    return free


def carve_polyline(free, pts, radius=CORRIDOR_RADIUS, n=220):
    pts = np.asarray(pts, dtype=float)

    for a, b in zip(pts[:-1], pts[1:]):
        seg = np.linspace(a, b, n)
        for x0, y0 in seg:
            free = carve_disk(free, x0, y0, radius)

    return free


def empty():
    return np.zeros((H, W), dtype=np.uint8)


def add_source_target_disks(free):
    for p in [SOURCE_TOP, SOURCE_BOTTOM, TARGET_TOP, TARGET_BOTTOM]:
        free = carve_disk(free, *p, 14)
    return free


# ============================================================
# SCENE GENERATORS
# ============================================================

def make_diamond_connected():
    """
    Connected diamond / rhombus-like transport loop.
    Top and bottom paths meet through shared middle nodes.
    """
    free = empty()

    left_mid = np.array([75, H // 2])
    right_mid = np.array([W - 75, H // 2])
    top_mid = np.array([W // 2, int(H * 0.28)])
    bottom_mid = np.array([W // 2, int(H * 0.72)])

    # feed from both sources to left node
    free = carve_polyline(free, [SOURCE_TOP, left_mid])
    free = carve_polyline(free, [SOURCE_BOTTOM, left_mid])

    # diamond loop
    free = carve_polyline(free, [left_mid, top_mid, right_mid])
    free = carve_polyline(free, [left_mid, bottom_mid, right_mid])

    # output to both targets
    free = carve_polyline(free, [right_mid, TARGET_TOP])
    free = carve_polyline(free, [right_mid, TARGET_BOTTOM])

    return add_source_target_disks(free)


def make_diamond_broken():
    """
    Two separated components:
    upper path and lower path do not touch.
    """
    free = empty()

    # upper system
    free = carve_polyline(
        free,
        [
            SOURCE_TOP,
            np.array([90, int(H * 0.35)]),
            np.array([W // 2, int(H * 0.25)]),
            np.array([W - 90, int(H * 0.35)]),
            TARGET_TOP,
        ],
    )

    # lower system
    free = carve_polyline(
        free,
        [
            SOURCE_BOTTOM,
            np.array([90, int(H * 0.65)]),
            np.array([W // 2, int(H * 0.75)]),
            np.array([W - 90, int(H * 0.65)]),
            TARGET_BOTTOM,
        ],
    )

    return add_source_target_disks(free)


def make_diamond_selective():
    """
    Connected-looking diamond, but lower output is blocked.
    Only upper branch should be transport-active.
    """
    free = make_diamond_connected()

    # block lower output with a vertical wall segment
    block_x1 = W - 95
    block_x2 = W - 65
    block_y1 = int(H * 0.58)
    block_y2 = int(H * 0.78)

    free[block_y1:block_y2, block_x1:block_x2] = 0

    # keep target disk visible but disconnected from lower branch
    free = carve_disk(free, *TARGET_BOTTOM, 14)

    return free


SCENES = {
    "A_DIAMOND_CONNECTED": make_diamond_connected(),
    "B_DIAMOND_BROKEN": make_diamond_broken(),
    "C_DIAMOND_SELECTIVE": make_diamond_selective(),
}


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


def nearest_target(pos):
    d_top = np.linalg.norm(TARGET_TOP - pos)
    d_bottom = np.linalg.norm(TARGET_BOTTOM - pos)
    return TARGET_TOP if d_top < d_bottom else TARGET_BOTTOM


# ============================================================
# TRANSPORT
# ============================================================

def run_transport(free):
    gx, gy = local_field(free)

    trajectories = []
    successes = []
    coherences = []
    gate_values = []

    sources = [SOURCE_TOP, SOURCE_BOTTOM]

    for source in sources:
        for _ in range(N_PARTICLES_PER_SOURCE):
            pos = source.astype(float).copy()

            a = np.random.uniform(-0.12, 0.12)
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

                T = nearest_target(pos)
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
                    np.linalg.norm(pos - TARGET_TOP) < HIT_RADIUS
                    or np.linalg.norm(pos - TARGET_BOTTOM) < HIT_RADIUS
                ):
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


# ============================================================
# RUN
# ============================================================

results = {}

print("\n=== STRUX_DIAMOND_COMPONENT_TEST_01 ===\n")

for name, free in SCENES.items():
    metrics = run_transport(free)

    results[name] = {
        "free": free,
        "metrics": metrics,
    }

    print(name)
    print(f"  success_rate        : {metrics['success_rate']:.4f}")
    print(f"  direction_coherence : {metrics['direction_coherence']:.4f}")
    print(f"  detected_modes      : {metrics['n_modes']}")
    print(f"  transport_class     : {metrics['transport_class']}")
    print()


# ============================================================
# SAVE CSV
# ============================================================

csv_path = os.path.join(EXPORT_DIR, "metrics.csv")

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "scene",
        "success_rate",
        "direction_coherence",
        "detected_modes",
        "transport_class",
        "n_gate_values",
    ])

    for name, r in results.items():
        m = r["metrics"]
        writer.writerow([
            name,
            m["success_rate"],
            m["direction_coherence"],
            m["n_modes"],
            m["transport_class"],
            len(m["gate_values"]),
        ])


# ============================================================
# VISUALIZATION
# ============================================================

fig, axes = plt.subplots(1, 3, figsize=(21, 6))

for ax, (name, r) in zip(axes, results.items()):
    free = r["free"]
    m = r["metrics"]

    ax.imshow(free, cmap="gray", origin="lower")
    ax.axvline(X_GATE, color="yellow", linewidth=2)

    ax.set_title(
        f"{name}\n"
        f"sr={m['success_rate']:.2f}, modes={m['n_modes']}"
    )

    ax.axis("off")

    for path, success in zip(m["trajectories"], m["successes"]):
        if len(path) < 2:
            continue

        color = "dodgerblue" if success else "red"
        alpha = 0.45 if success else 0.06

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

    for p in [SOURCE_TOP, SOURCE_BOTTOM]:
        ax.scatter(p[0], p[1], c="lime", s=60, edgecolor="black")

    for p in [TARGET_TOP, TARGET_BOTTOM]:
        ax.scatter(p[0], p[1], c="cyan", marker="*", s=80, edgecolor="black")

plt.tight_layout()

viz_path = os.path.join(EXPORT_DIR, "diamond_component_test_01.png")
plt.savefig(viz_path, dpi=180)
plt.show()


# ============================================================
# SUMMARY
# ============================================================

summary_path = os.path.join(EXPORT_DIR, "summary.txt")

with open(summary_path, "w") as f:
    f.write("STRUX_DIAMOND_COMPONENT_TEST_01\n\n")
    f.write("Purpose: active transport components vs visible branches.\n\n")

    for name, r in results.items():
        m = r["metrics"]
        f.write(f"{name}\n")
        f.write(f"  success_rate        : {m['success_rate']:.4f}\n")
        f.write(f"  direction_coherence : {m['direction_coherence']:.4f}\n")
        f.write(f"  detected_modes      : {m['n_modes']}\n")
        f.write(f"  transport_class     : {m['transport_class']}\n\n")

print(f"Saved CSV     : {csv_path}")
print(f"Saved viz     : {viz_path}")
print(f"Saved summary : {summary_path}")