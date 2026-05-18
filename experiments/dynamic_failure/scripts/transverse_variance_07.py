"""
transverse_variance_07.py

Experimental dynamic_failure analysis.

Purpose:
Measure whether downstream temporal jitter corresponds to spatial
transverse spread of particle trajectories.

This is NOT STRUX core.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt

EXPORT_DIR = "experiments/dynamic_failure/results"
FIGURE_DIR = "experiments/dynamic_failure/figures"

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

N_SEEDS = 20
DEFLECTION_VALUES = [0.10, 0.30, 0.50]

CORRIDOR_RADIUS = 15

H, W = 180, 360
SOURCE = np.array([20, H // 2], dtype=float)
TARGET = np.array([W - 20, H // 2], dtype=float)

N_PARTICLES = 70
MAX_STEPS = 1000
STEP = 1.0

NOISE_LIVE = 0.025
NOISE_DEAD = 0.018

HIT_RADIUS = 13
COLLISION_RADIUS = 5.0

FAIL_TIMEOUT = 760
PROGRESS_WINDOW = 120
MIN_PROGRESS = 10.0

DEAD_DRAG = 0.992
DEAD_PUSH_STRENGTH = 0.06

ZONES = {
    "A_entry": (0, 110),
    "B_transition": (110, 235),
    "C_downstream": (235, W),
}


def build_corridor():
    yy, xx = np.mgrid[0:H, 0:W]
    free = np.zeros((H, W), dtype=np.uint8)

    control = np.array([
        [20, H / 2],
        [85, H / 2 - 36],
        [145, H / 2 + 36],
        [205, H / 2 - 36],
        [265, H / 2 + 36],
        [340, H / 2],
    ], dtype=float)

    pts = []
    for a, b in zip(control[:-1], control[1:]):
        pts.append(np.linspace(a, b, 280))

    centerline = np.vstack(pts)

    for x0, y0 in centerline:
        d2 = (xx - x0) ** 2 + (yy - y0) ** 2
        free[d2 <= CORRIDOR_RADIUS ** 2] = 1

    for cx, cy, rr in [(SOURCE[0], SOURCE[1], 18), (TARGET[0], TARGET[1], 18)]:
        d2 = (xx - cx) ** 2 + (yy - cy) ** 2
        free[d2 <= rr ** 2] = 1

    return free, centerline


def run_dynamic(seed, deflection):
    np.random.seed(seed)

    free, centerline = build_corridor()

    dist = distance_transform_edt(free)
    gy, gx = np.gradient(dist.astype(float))
    norm = np.sqrt(gx ** 2 + gy ** 2) + 1e-9
    gx = gx / norm
    gy = gy / norm

    def inside_free(p):
        x = int(np.clip(round(p[0]), 0, W - 1))
        y = int(np.clip(round(p[1]), 0, H - 1))
        return free[y, x] == 1

    def local_normal(p):
        x = int(np.clip(round(p[0]), 0, W - 1))
        y = int(np.clip(round(p[1]), 0, H - 1))
        n = np.array([gx[y, x], gy[y, x]], dtype=float)
        n /= np.linalg.norm(n) + 1e-9
        return n

    def reflect(v, n):
        return v - 2 * np.dot(v, n) * n

    pos = np.zeros((N_PARTICLES, 2), dtype=float)
    vel = np.zeros((N_PARTICLES, 2), dtype=float)

    for i in range(N_PARTICLES):
        pos[i] = SOURCE + np.random.randn(2) * np.array([1.0, 2.0])
        angle = np.random.uniform(-0.10, 0.10)
        vel[i] = np.array([1.0, angle])
        vel[i] /= np.linalg.norm(vel[i]) + 1e-9

    alive = np.ones(N_PARTICLES, dtype=bool)
    dead = np.zeros(N_PARTICLES, dtype=bool)
    reached = np.zeros(N_PARTICLES, dtype=bool)

    last_progress_pos = pos.copy()
    last_progress_step = np.zeros(N_PARTICLES, dtype=int)

    samples = []

    for step_i in range(MAX_STEPS):
        dead_idx = np.where(dead)[0]
        live_idx = np.where(alive)[0]

        for i in live_idx:
            for j in dead_idx:
                d = pos[i] - pos[j]
                dist_ij = np.linalg.norm(d) + 1e-9

                if dist_ij < COLLISION_RADIUS:
                    n = d / dist_ij

                    vel[i] = (1.0 - deflection) * vel[i] + deflection * n
                    vel[i] += 0.04 * np.random.randn(2)
                    vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                    vel[j] += DEAD_PUSH_STRENGTH * (-n)
                    vel[j] *= DEAD_DRAG
                    vel[j] /= np.linalg.norm(vel[j]) + 1e-9

        for i in range(N_PARTICLES):
            if reached[i]:
                continue

            if alive[i]:
                x_now = pos[i, 0]
                y_now = pos[i, 1]

                for zone, (x0, x1) in ZONES.items():
                    if x0 <= x_now < x1:
                        samples.append({
                            "seed": seed,
                            "deflection": deflection,
                            "step": step_i,
                            "particle": i,
                            "zone": zone,
                            "x": float(x_now),
                            "y": float(y_now),
                        })

                to_target = TARGET - pos[i]
                to_target /= np.linalg.norm(to_target) + 1e-9

                x = int(np.clip(round(pos[i, 0]), 0, W - 1))
                y = int(np.clip(round(pos[i, 1]), 0, H - 1))

                G = np.array([gx[y, x], gy[y, x]])

                desired = 0.84 * to_target + 0.16 * G
                desired += NOISE_LIVE * np.random.randn(2)
                desired /= np.linalg.norm(desired) + 1e-9

                vel[i] = 0.86 * vel[i] + 0.14 * desired
                vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                new = pos[i] + STEP * vel[i]

                if not inside_free(new):
                    n = local_normal(pos[i])
                    vel[i] = reflect(vel[i], n)
                    vel[i] += 0.04 * np.random.randn(2)
                    vel[i] /= np.linalg.norm(vel[i]) + 1e-9
                    new = pos[i] + STEP * vel[i]

                    if not inside_free(new):
                        alive[i] = False
                        dead[i] = True
                        continue

                pos[i] = new

                if np.linalg.norm(pos[i] - TARGET) < HIT_RADIUS:
                    alive[i] = False
                    reached[i] = True
                    continue

                if step_i - last_progress_step[i] >= PROGRESS_WINDOW:
                    progress_gain = pos[i, 0] - last_progress_pos[i, 0]

                    if progress_gain < MIN_PROGRESS or step_i > FAIL_TIMEOUT:
                        alive[i] = False
                        dead[i] = True
                        continue

                    last_progress_pos[i] = pos[i].copy()
                    last_progress_step[i] = step_i

            elif dead[i]:
                vel[i] *= DEAD_DRAG
                vel[i] += NOISE_DEAD * np.random.randn(2)
                vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                new = pos[i] + 0.35 * STEP * vel[i]

                if inside_free(new):
                    pos[i] = new

    return samples


all_samples = []

print("\n=== TRANSVERSE VARIANCE 07 ===\n")

for deflection in DEFLECTION_VALUES:
    print(f"DEFLECTION = {deflection}")

    for seed in range(N_SEEDS):
        samples = run_dynamic(seed, deflection)
        all_samples.extend(samples)

    print("  done")

df = pd.DataFrame(all_samples)

sample_path = os.path.join(EXPORT_DIR, "transverse_variance_samples.csv")
df.to_csv(sample_path, index=False)

summary = df.groupby(["deflection", "zone"]).agg(
    n_samples=("y", "count"),
    y_mean=("y", "mean"),
    y_std=("y", "std"),
    y_var=("y", "var"),
).reset_index()

summary_path = os.path.join(EXPORT_DIR, "transverse_variance_summary.csv")
summary.to_csv(summary_path, index=False)

print("\nSummary:")
print(summary)

plt.figure(figsize=(8, 5))

for deflection in DEFLECTION_VALUES:
    part = summary[summary["deflection"] == deflection]
    plt.plot(
        part["zone"],
        part["y_std"],
        marker="o",
        label=f"D={deflection}",
    )

plt.ylabel("transverse spread: std(y)")
plt.xlabel("corridor zone")
plt.title("Transverse Spread Across Corridor Zones")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()

fig_path = os.path.join(FIGURE_DIR, "transverse_variance_07.png")
plt.savefig(fig_path, dpi=180)
plt.show()

print("\nSaved:")
print(sample_path)
print(summary_path)
print(fig_path)