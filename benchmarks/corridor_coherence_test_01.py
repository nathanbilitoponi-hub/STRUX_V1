"""
STRUX_CORRIDOR_COHERENCE_TEST_01

Purpose
-------
Test whether STRUX measures only aperture width
or also global corridor coherence.

Setup
-----
All cases use approximately the same corridor width.
We vary only the corridor shape:

A_STRAIGHT
B_MILD_CURVE
C_STRONG_CURVE
D_ZIGZAG

Core question
-------------
If width is constant, does success_rate change with curvature/tortuosity?

Expected behavior
-----------------
STRAIGHT:
    high success

MILD_CURVE:
    slightly lower success

STRONG_CURVE:
    lower success

ZIGZAG:
    fragile / lower success

This tests whether STRUX measures corridor coherence,
not just binary path existence or hole width.
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

H, W = 180, 340

SOURCE = np.array([18, H // 2])
TARGET = np.array([W - 18, H // 2])

N_PARTICLES = 500
MAX_STEPS = 1400
STEP = 1.0
NOISE = 0.035
HIT_RADIUS = 14

CORRIDOR_RADIUS = 8
X_GATE = W // 2

EXPORT_DIR = "exports/STRUX_CORRIDOR_COHERENCE_TEST_01"
os.makedirs(EXPORT_DIR, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W]


# ============================================================
# GEOMETRY HELPERS
# ============================================================

def carve_disk(free, cx, cy, r):
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    free[d2 <= r * r] = 1
    return free


def make_empty_world():
    free = np.zeros((H, W), dtype=np.uint8)
    return free


def carve_corridor_from_centerline(centerline, radius=CORRIDOR_RADIUS):
    free = make_empty_world()

    for x0, y0 in centerline:
        free = carve_disk(free, x0, y0, radius)

    free = carve_disk(free, *SOURCE, 14)
    free = carve_disk(free, *TARGET, 14)

    return free


# ============================================================
# CENTERLINES
# ============================================================

def centerline_straight():
    xs = np.linspace(25, W - 25, 600)
    ys = np.full_like(xs, H / 2)
    return np.vstack([xs, ys]).T


def centerline_mild_curve():
    xs = np.linspace(25, W - 25, 700)
    ys = H / 2 + 22 * np.sin((xs - 25) / (W - 50) * 2 * np.pi)
    return np.vstack([xs, ys]).T


def centerline_strong_curve():
    xs = np.linspace(25, W - 25, 850)
    ys = H / 2 + 48 * np.sin((xs - 25) / (W - 50) * 2 * np.pi)
    return np.vstack([xs, ys]).T


def centerline_zigzag():
    control = np.array([
        [25, H / 2],
        [75, H / 2 - 48],
        [125, H / 2 + 48],
        [175, H / 2 - 48],
        [225, H / 2 + 48],
        [275, H / 2 - 40],
        [W - 25, H / 2],
    ], dtype=float)

    pts = []

    for a, b in zip(control[:-1], control[1:]):
        seg = np.linspace(a, b, 160)
        pts.append(seg)

    return np.vstack(pts)


SCENES = {
    "A_STRAIGHT": carve_corridor_from_centerline(centerline_straight()),
    "B_MILD_CURVE": carve_corridor_from_centerline(centerline_mild_curve()),
    "C_STRONG_CURVE": carve_corridor_from_centerline(centerline_strong_curve()),
    "D_ZIGZAG": carve_corridor_from_centerline(centerline_zigzag()),
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


# ============================================================
# TRANSPORT
# ============================================================

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


# ============================================================
# RUN
# ============================================================

results = {}

print("\n=== STRUX_CORRIDOR_COHERENCE_TEST_01 ===\n")

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
# PLOT METRICS
# ============================================================

scene_names = list(results.keys())
successes = np.array([results[s]["metrics"]["success_rate"] for s in scene_names])
coherences = np.array([results[s]["metrics"]["direction_coherence"] for s in scene_names])
modes = np.array([results[s]["metrics"]["n_modes"] for s in scene_names])

x = np.arange(len(scene_names))

plt.figure(figsize=(11, 5))
plt.bar(x - 0.25, successes, width=0.25, label="success_rate")
plt.bar(x, coherences, width=0.25, label="direction_coherence")
plt.bar(x + 0.25, modes / max(1, modes.max()), width=0.25, label="n_modes normalized")

plt.xticks(x, scene_names, rotation=20)
plt.ylim(0, 1.05)
plt.grid(axis="y", alpha=0.25)
plt.legend()
plt.title("STRUX_CORRIDOR_COHERENCE_TEST_01 — Width Constant, Shape Variable")
plt.tight_layout()

plot_path = os.path.join(EXPORT_DIR, "corridor_coherence_metrics.png")
plt.savefig(plot_path, dpi=180)
plt.show()


# ============================================================
# VISUALIZE TRAJECTORIES
# ============================================================

fig, axes = plt.subplots(1, 4, figsize=(22, 5))

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

viz_path = os.path.join(EXPORT_DIR, "corridor_coherence_trajectories.png")
plt.savefig(viz_path, dpi=180)
plt.show()


# ============================================================
# SUMMARY
# ============================================================

summary_path = os.path.join(EXPORT_DIR, "summary.txt")

with open(summary_path, "w") as f:
    f.write("STRUX_CORRIDOR_COHERENCE_TEST_01\n\n")
    f.write("Purpose: constant-width corridor, variable global geometry.\n\n")

    for name, r in results.items():
        m = r["metrics"]
        f.write(f"{name}\n")
        f.write(f"  success_rate        : {m['success_rate']:.4f}\n")
        f.write(f"  direction_coherence : {m['direction_coherence']:.4f}\n")
        f.write(f"  detected_modes      : {m['n_modes']}\n")
        f.write(f"  transport_class     : {m['transport_class']}\n\n")

print(f"Saved CSV     : {csv_path}")
print(f"Saved plot    : {plot_path}")
print(f"Saved viz     : {viz_path}")
print(f"Saved summary : {summary_path}")