"""
social_force_baseline.py

Baseline for STRUX dynamic_failure subsystem.

Purpose:
Test whether a simple social-force / local avoidance model
can reproduce transport through the same S-shaped constrained corridor.

This baseline includes:
- target attraction
- wall repulsion
- particle-particle repulsion
- no dead residue dynamics
- no STRUX adaptive deflection rules

This is NOT STRUX core.
"""

import os
import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt

EXPORT_DIR = "experiments/dynamic_failure/results"
os.makedirs(EXPORT_DIR, exist_ok=True)

N_SEEDS = 20
CORRIDOR_RADIUS = 15
N_PARTICLES = 70
MAX_STEPS = 1000

H, W = 180, 360
SOURCE = np.array([20, H // 2], dtype=float)
TARGET = np.array([W - 20, H // 2], dtype=float)

STEP = 1.0
HIT_RADIUS = 13

REPULSION_VALUES = [0.05, 0.10, 0.20, 0.35]
NOISE = 0.025
INTERACTION_RADIUS = 8.0


def build_corridor(corridor_radius):
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
        free[d2 <= corridor_radius ** 2] = 1

    for cx, cy, rr in [(SOURCE[0], SOURCE[1], 18), (TARGET[0], TARGET[1], 18)]:
        d2 = (xx - cx) ** 2 + (yy - cy) ** 2
        free[d2 <= rr ** 2] = 1

    return free


def run_social_force(seed, repulsion_strength):
    np.random.seed(seed)

    free = build_corridor(CORRIDOR_RADIUS)

    dist = distance_transform_edt(free)
    gy, gx = np.gradient(dist.astype(float))
    norm = np.sqrt(gx ** 2 + gy ** 2) + 1e-9
    gx = gx / norm
    gy = gy / norm

    def inside_free(p):
        x = int(np.clip(round(p[0]), 0, W - 1))
        y = int(np.clip(round(p[1]), 0, H - 1))
        return free[y, x] == 1

    pos = np.zeros((N_PARTICLES, 2), dtype=float)
    vel = np.zeros((N_PARTICLES, 2), dtype=float)

    reached = np.zeros(N_PARTICLES, dtype=bool)
    dead = np.zeros(N_PARTICLES, dtype=bool)
    arrival_steps = np.full(N_PARTICLES, np.nan)

    for i in range(N_PARTICLES):
        pos[i] = SOURCE + np.random.randn(2) * np.array([1.0, 2.0])
        angle = np.random.uniform(-0.10, 0.10)
        vel[i] = np.array([1.0, angle])
        vel[i] /= np.linalg.norm(vel[i]) + 1e-9

    for step_i in range(MAX_STEPS):
        active = np.where(~reached & ~dead)[0]

        for i in active:
            to_target = TARGET - pos[i]
            to_target /= np.linalg.norm(to_target) + 1e-9

            x = int(np.clip(round(pos[i, 0]), 0, W - 1))
            y = int(np.clip(round(pos[i, 1]), 0, H - 1))

            wall_push = np.array([gx[y, x], gy[y, x]])

            particle_push = np.zeros(2, dtype=float)

            for j in active:
                if i == j:
                    continue

                d = pos[i] - pos[j]
                dij = np.linalg.norm(d) + 1e-9

                if dij < INTERACTION_RADIUS:
                    particle_push += (d / dij) * (1.0 - dij / INTERACTION_RADIUS)

            desired = (
                0.82 * to_target
                + 0.12 * wall_push
                + repulsion_strength * particle_push
            )

            desired += NOISE * np.random.randn(2)
            desired /= np.linalg.norm(desired) + 1e-9

            vel[i] = 0.80 * vel[i] + 0.20 * desired
            vel[i] /= np.linalg.norm(vel[i]) + 1e-9

            new = pos[i] + STEP * vel[i]

            if not inside_free(new):
                dead[i] = True
                continue

            pos[i] = new

            if np.linalg.norm(pos[i] - TARGET) < HIT_RADIUS:
                reached[i] = True
                arrival_steps[i] = step_i

    valid_arrivals = arrival_steps[np.isfinite(arrival_steps)]

    success_rate = float(np.mean(reached))
    death_rate = float(np.mean(dead))

    if len(valid_arrivals) > 1:
        mean_arrival = float(np.mean(valid_arrivals))
        temporal_jitter = float(np.std(valid_arrivals) / (mean_arrival + 1e-9))
    else:
        mean_arrival = np.nan
        temporal_jitter = np.nan

    return {
        "seed": seed,
        "repulsion_strength": repulsion_strength,
        "success_rate": success_rate,
        "death_rate": death_rate,
        "mean_arrival": mean_arrival,
        "temporal_jitter": temporal_jitter,
    }


rows = []

print("\n=== SOCIAL FORCE BASELINE ===\n")

for repulsion in REPULSION_VALUES:
    local = []

    for seed in range(N_SEEDS):
        r = run_social_force(seed=seed, repulsion_strength=repulsion)
        rows.append(r)
        local.append(r)

    df_local = pd.DataFrame(local)

    print(f"repulsion = {repulsion}")
    print(f"  success_mean : {df_local['success_rate'].mean():.4f}")
    print(f"  death_mean   : {df_local['death_rate'].mean():.4f}")
    print(f"  jitter_mean  : {df_local['temporal_jitter'].mean():.4f}")
    print()

df = pd.DataFrame(rows)

csv_path = os.path.join(EXPORT_DIR, "social_force_baseline_results.csv")
df.to_csv(csv_path, index=False)

summary = df.groupby("repulsion_strength").agg(
    success_mean=("success_rate", "mean"),
    death_mean=("death_rate", "mean"),
    jitter_mean=("temporal_jitter", "mean"),
).reset_index()

summary_path = os.path.join(EXPORT_DIR, "social_force_baseline_summary.csv")
summary.to_csv(summary_path, index=False)

print("Saved:")
print(csv_path)
print(summary_path)