"""
STRUX_TEMPORAL_JITTER_TEST_01

Purpose
-------
Test whether constrained geometries with similar reachability
produce different temporal dispersion.

Core idea
---------
A geometry may allow transport, but still degrade synchronization.

This benchmark measures:
- success_rate
- mean_arrival_time
- arrival_time_std
- temporal_jitter
- direction_coherence

Interpretation
--------------
Low jitter:
    arrivals are temporally compact.

High jitter:
    arrivals are dispersed in time.

This test is experimental and does not modify the STRUX core.
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

H, W = 180, 340

SOURCE = np.array([20, H // 2])
TARGET = np.array([W - 20, H // 2])

N_PARTICLES = 500
MAX_STEPS = 1600
STEP = 1.0
NOISE = 0.030
HIT_RADIUS = 14

CORRIDOR_RADIUS = 8

EXPORT_DIR = "exports/STRUX_TEMPORAL_JITTER_TEST_01"
os.makedirs(EXPORT_DIR, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W]


# ============================================================
# GEOMETRY HELPERS
# ============================================================

def carve_disk(free, cx, cy, r):
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    free[d2 <= r * r] = 1
    return free


def carve_corridor(centerline, radius=CORRIDOR_RADIUS):
    free = np.zeros((H, W), dtype=np.uint8)

    for x0, y0 in centerline:
        free = carve_disk(free, x0, y0, radius)

    free = carve_disk(free, *SOURCE, 16)
    free = carve_disk(free, *TARGET, 16)

    return free


# ============================================================
# CENTERLINES
# ============================================================

def centerline_straight():
    xs = np.linspace(25, W - 25, 700)
    ys = np.full_like(xs, H / 2)
    return np.vstack([xs, ys]).T


def centerline_mild_curve():
    xs = np.linspace(25, W - 25, 850)
    ys = H / 2 + 22 * np.sin((xs - 25) / (W - 50) * 2 * np.pi)
    return np.vstack([xs, ys]).T


def centerline_zigzag():
    control = np.array([
        [25, H / 2],
        [80, H / 2 - 42],
        [135, H / 2 + 42],
        [190, H / 2 - 42],
        [245, H / 2 + 42],
        [W - 25, H / 2],
    ], dtype=float)

    pts = []

    for a, b in zip(control[:-1], control[1:]):
        seg = np.linspace(a, b, 170)
        pts.append(seg)

    return np.vstack(pts)


SCENES = {
    "A_STRAIGHT": carve_corridor(centerline_straight()),
    "B_MILD_CURVE": carve_corridor(centerline_mild_curve()),
    "C_ZIGZAG": carve_corridor(centerline_zigzag()),
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
# TRANSPORT
# ============================================================

def run_transport(free):
    gx, gy = local_field(free)

    trajectories = []
    successes = []
    arrival_times = []
    coherences = []

    for _ in range(N_PARTICLES):
        pos = SOURCE.astype(float).copy()

        a = np.random.uniform(-0.16, 0.16)
        D = np.array([1.0, a])
        D /= np.linalg.norm(D) + 1e-9

        path = [pos.copy()]
        local_align = []
        success = False
        arrival_time = np.nan

        for step_i in range(MAX_STEPS):
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

            pos = new
            path.append(pos.copy())
            local_align.append(np.dot(D, to_target))

            if np.linalg.norm(pos - TARGET) < HIT_RADIUS:
                success = True
                arrival_time = step_i + 1
                break

        trajectories.append(np.array(path))
        successes.append(success)
        arrival_times.append(arrival_time)
        coherences.append(np.mean(local_align) if len(local_align) else 0)

    successes = np.array(successes, dtype=bool)
    arrival_times = np.array(arrival_times, dtype=float)
    coherences = np.array(coherences, dtype=float)

    valid_arrivals = arrival_times[np.isfinite(arrival_times)]

    success_rate = float(np.mean(successes))

    if len(valid_arrivals) > 0:
        mean_arrival_time = float(np.mean(valid_arrivals))
        arrival_time_std = float(np.std(valid_arrivals))
        temporal_jitter = float(arrival_time_std / (mean_arrival_time + 1e-9))
    else:
        mean_arrival_time = np.nan
        arrival_time_std = np.nan
        temporal_jitter = np.nan

    direction_coherence = float(np.mean(coherences))

    return {
        "success_rate": success_rate,
        "mean_arrival_time": mean_arrival_time,
        "arrival_time_std": arrival_time_std,
        "temporal_jitter": temporal_jitter,
        "direction_coherence": direction_coherence,
        "trajectories": trajectories,
        "successes": successes,
        "arrival_times": arrival_times,
    }


# ============================================================
# RUN
# ============================================================

results = {}

print("\n=== STRUX_TEMPORAL_JITTER_TEST_01 ===\n")

for name, free in SCENES.items():
    metrics = run_transport(free)

    results[name] = {
        "free": free,
        "metrics": metrics,
    }

    print(name)
    print(f"  success_rate        : {metrics['success_rate']:.4f}")
    print(f"  mean_arrival_time   : {metrics['mean_arrival_time']:.4f}")
    print(f"  arrival_time_std    : {metrics['arrival_time_std']:.4f}")
    print(f"  temporal_jitter     : {metrics['temporal_jitter']:.4f}")
    print(f"  direction_coherence : {metrics['direction_coherence']:.4f}")
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
        "mean_arrival_time",
        "arrival_time_std",
        "temporal_jitter",
        "direction_coherence",
    ])

    for name, r in results.items():
        m = r["metrics"]
        writer.writerow([
            name,
            m["success_rate"],
            m["mean_arrival_time"],
            m["arrival_time_std"],
            m["temporal_jitter"],
            m["direction_coherence"],
        ])


# ============================================================
# PLOT METRICS
# ============================================================

scene_names = list(results.keys())

successes = np.array([results[s]["metrics"]["success_rate"] for s in scene_names])
means = np.array([results[s]["metrics"]["mean_arrival_time"] for s in scene_names])
stds = np.array([results[s]["metrics"]["arrival_time_std"] for s in scene_names])
jitters = np.array([results[s]["metrics"]["temporal_jitter"] for s in scene_names])
coherences = np.array([results[s]["metrics"]["direction_coherence"] for s in scene_names])

x = np.arange(len(scene_names))

plt.figure(figsize=(10, 5))
plt.bar(x - 0.2, successes, width=0.2, label="success_rate")
plt.bar(x, coherences, width=0.2, label="direction_coherence")
plt.bar(x + 0.2, jitters / max(1e-9, np.nanmax(jitters)), width=0.2, label="jitter normalized")

plt.xticks(x, scene_names, rotation=20)
plt.ylim(0, 1.05)
plt.grid(axis="y", alpha=0.25)
plt.legend()
plt.title("STRUX_TEMPORAL_JITTER_TEST_01 — Success, Coherence, Jitter")
plt.tight_layout()

plot_path = os.path.join(EXPORT_DIR, "temporal_jitter_metrics.png")
plt.savefig(plot_path, dpi=180)
plt.show()


plt.figure(figsize=(10, 5))
plt.bar(x - 0.15, means, width=0.3, label="mean_arrival_time")
plt.bar(x + 0.15, stds, width=0.3, label="arrival_time_std")

plt.xticks(x, scene_names, rotation=20)
plt.grid(axis="y", alpha=0.25)
plt.legend()
plt.title("Arrival Time Mean and Dispersion")
plt.tight_layout()

time_plot_path = os.path.join(EXPORT_DIR, "arrival_time_stats.png")
plt.savefig(time_plot_path, dpi=180)
plt.show()


# ============================================================
# HISTOGRAMS
# ============================================================

plt.figure(figsize=(10, 5))

for name in scene_names:
    arr = results[name]["metrics"]["arrival_times"]
    arr = arr[np.isfinite(arr)]
    if len(arr) > 0:
        plt.hist(arr, bins=30, alpha=0.45, label=name)

plt.xlabel("arrival time / steps")
plt.ylabel("count")
plt.title("Arrival Time Distributions")
plt.legend()
plt.tight_layout()

hist_path = os.path.join(EXPORT_DIR, "arrival_time_histograms.png")
plt.savefig(hist_path, dpi=180)
plt.show()


# ============================================================
# VISUALIZATION
# ============================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for ax, (name, r) in zip(axes, results.items()):
    free = r["free"]
    m = r["metrics"]

    ax.imshow(free, cmap="gray", origin="lower")

    ax.set_title(
        f"{name}\n"
        f"sr={m['success_rate']:.2f}, "
        f"jitter={m['temporal_jitter']:.3f}"
    )

    ax.axis("off")

    for path, success in zip(m["trajectories"], m["successes"]):
        if len(path) < 2:
            continue

        color = "dodgerblue" if success else "red"
        alpha = 0.40 if success else 0.06

        ax.plot(
            path[:, 0],
            path[:, 1],
            color=color,
            linewidth=0.45,
            alpha=alpha,
        )

    ax.scatter(SOURCE[0], SOURCE[1], c="lime", s=60, edgecolor="black")
    ax.scatter(TARGET[0], TARGET[1], c="cyan", marker="*", s=90, edgecolor="black")

plt.tight_layout()

viz_path = os.path.join(EXPORT_DIR, "temporal_jitter_trajectories.png")
plt.savefig(viz_path, dpi=180)
plt.show()


# ============================================================
# SUMMARY
# ============================================================

summary_path = os.path.join(EXPORT_DIR, "summary.txt")

with open(summary_path, "w") as f:
    f.write("STRUX_TEMPORAL_JITTER_TEST_01\n\n")
    f.write("Purpose: measure arrival-time dispersion in constrained geometries.\n\n")

    for name, r in results.items():
        m = r["metrics"]
        f.write(f"{name}\n")
        f.write(f"  success_rate        : {m['success_rate']:.4f}\n")
        f.write(f"  mean_arrival_time   : {m['mean_arrival_time']:.4f}\n")
        f.write(f"  arrival_time_std    : {m['arrival_time_std']:.4f}\n")
        f.write(f"  temporal_jitter     : {m['temporal_jitter']:.4f}\n")
        f.write(f"  direction_coherence : {m['direction_coherence']:.4f}\n\n")

print(f"Saved CSV       : {csv_path}")
print(f"Saved plot      : {plot_path}")
print(f"Saved time plot : {time_plot_path}")
print(f"Saved histogram : {hist_path}")
print(f"Saved viz       : {viz_path}")
print(f"Saved summary   : {summary_path}")