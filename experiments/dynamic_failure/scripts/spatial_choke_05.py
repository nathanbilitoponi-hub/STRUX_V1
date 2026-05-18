"""
spatial_choke_05.py

STRUX Experimental Subsystem
Dynamic Failure / Spatial Choke Localization

Purpose:
Test whether death locations are spatially concentrated near
high-curvature regions of the S-shaped corridor.

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

N_SEEDS = 30
CORRIDOR_RADIUS = 15
DEFLECTION = 0.30

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

    curvature_points = control[1:-1]

    return free, centerline, curvature_points


def run_dynamic(seed):
    np.random.seed(seed)

    free, centerline, curvature_points = build_corridor()

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

    death_rows = []

    for step_i in range(MAX_STEPS):
        dead_idx = np.where(dead)[0]
        live_idx = np.where(alive)[0]

        for i in live_idx:
            for j in dead_idx:
                d = pos[i] - pos[j]
                dist_ij = np.linalg.norm(d) + 1e-9

                if dist_ij < COLLISION_RADIUS:
                    n = d / dist_ij

                    vel[i] = (1.0 - DEFLECTION) * vel[i] + DEFLECTION * n
                    vel[i] += 0.04 * np.random.randn(2)
                    vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                    vel[j] += DEAD_PUSH_STRENGTH * (-n)
                    vel[j] *= DEAD_DRAG
                    vel[j] /= np.linalg.norm(vel[j]) + 1e-9

        for i in range(N_PARTICLES):
            if reached[i]:
                continue

            if alive[i]:
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

                        death_rows.append({
                            "seed": seed,
                            "particle": i,
                            "death_step": step_i,
                            "x": float(pos[i, 0]),
                            "y": float(pos[i, 1]),
                            "death_type": "wall_failure",
                        })
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

                        death_rows.append({
                            "seed": seed,
                            "particle": i,
                            "death_step": step_i,
                            "x": float(pos[i, 0]),
                            "y": float(pos[i, 1]),
                            "death_type": "progress_failure",
                        })
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

    return death_rows, free, centerline, curvature_points


all_deaths = []
free_ref = None
centerline_ref = None
curvature_ref = None

print("\n=== SPATIAL CHOKE 05 ===\n")

for seed in range(N_SEEDS):
    deaths, free, centerline, curvature_points = run_dynamic(seed)

    all_deaths.extend(deaths)
    free_ref = free
    centerline_ref = centerline
    curvature_ref = curvature_points

    print(f"seed {seed:02d}: deaths={len(deaths)}")

df = pd.DataFrame(all_deaths)

death_csv = os.path.join(EXPORT_DIR, "spatial_choke_deaths.csv")
df.to_csv(death_csv, index=False)

# ------------------------------------------------------------
# distance to nearest curvature point
# ------------------------------------------------------------

if len(df) > 0:
    death_xy = df[["x", "y"]].values
    distances = []

    for p in death_xy:
        d = np.linalg.norm(curvature_ref - p, axis=1)
        distances.append(float(np.min(d)))

    df["distance_to_nearest_curvature"] = distances

    enriched_csv = os.path.join(EXPORT_DIR, "spatial_choke_deaths_enriched.csv")
    df.to_csv(enriched_csv, index=False)

    summary = {
        "n_deaths": len(df),
        "mean_distance_to_curvature": float(np.mean(distances)),
        "median_distance_to_curvature": float(np.median(distances)),
        "pct_within_20px": float(np.mean(np.array(distances) <= 20)),
        "pct_within_30px": float(np.mean(np.array(distances) <= 30)),
        "pct_within_40px": float(np.mean(np.array(distances) <= 40)),
    }

    summary_df = pd.DataFrame([summary])
    summary_path = os.path.join(EXPORT_DIR, "spatial_choke_summary.csv")
    summary_df.to_csv(summary_path, index=False)

else:
    enriched_csv = os.path.join(EXPORT_DIR, "spatial_choke_deaths_enriched.csv")
    summary_path = os.path.join(EXPORT_DIR, "spatial_choke_summary.csv")
    pd.DataFrame().to_csv(enriched_csv, index=False)
    pd.DataFrame().to_csv(summary_path, index=False)


# ------------------------------------------------------------
# plot
# ------------------------------------------------------------

plt.figure(figsize=(10, 5))
plt.imshow(free_ref, cmap="gray", origin="lower")

plt.plot(
    centerline_ref[:, 0],
    centerline_ref[:, 1],
    color="cyan",
    linewidth=1.0,
    alpha=0.7,
    label="centerline",
)

plt.scatter(
    curvature_ref[:, 0],
    curvature_ref[:, 1],
    c="yellow",
    s=90,
    edgecolor="black",
    label="curvature control points",
)

if len(df) > 0:
    plt.scatter(
        df["x"],
        df["y"],
        c="red",
        s=8,
        alpha=0.35,
        label="death locations",
    )

plt.title("Spatial Choke Localization — Deaths vs Curvature Points")
plt.legend(loc="upper right")
plt.axis("off")
plt.tight_layout()

fig_path = os.path.join(FIGURE_DIR, "spatial_choke_death_locations.png")
plt.savefig(fig_path, dpi=180)
plt.show()

print("\nSaved:")
print(death_csv)
print(enriched_csv)
print(summary_path)
print(fig_path)