"""
ballistic_no_interaction_baseline.py

Baseline D1 for STRUX dynamic_failure subsystem.

Purpose:
Test whether the success/jitter tradeoff appears even without:
- particle-particle collisions
- dead residue dynamics
- local interaction feedback

If this baseline reproduces the same pattern, the effect is mostly geometric.
If it does not, the effect likely depends on interactions/residue dynamics.

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

NOISE = 0.025
HIT_RADIUS = 13

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


def run_baseline(seed, deflection):
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

    reached = np.zeros(N_PARTICLES, dtype=bool)
    failed = np.zeros(N_PARTICLES, dtype=bool)

    arrival_steps = np.full(N_PARTICLES, np.nan)

    zone_entry_steps = {
        zone: np.full(N_PARTICLES, np.nan)
        for zone in ZONES
    }

    for i in range(N_PARTICLES):
        pos[i] = SOURCE + np.random.randn(2) * np.array([1.0, 2.0])
        angle = np.random.uniform(-0.10, 0.10)
        vel[i] = np.array([1.0, angle])
        vel[i] /= np.linalg.norm(vel[i]) + 1e-9

    for step_i in range(MAX_STEPS):

        for i in range(N_PARTICLES):

            if reached[i] or failed[i]:
                continue

            x_now = pos[i, 0]

            for zone, (x0, x1) in ZONES.items():
                if x0 <= x_now < x1 and not np.isfinite(zone_entry_steps[zone][i]):
                    zone_entry_steps[zone][i] = step_i

            to_target = TARGET - pos[i]
            to_target /= np.linalg.norm(to_target) + 1e-9

            x = int(np.clip(round(pos[i, 0]), 0, W - 1))
            y = int(np.clip(round(pos[i, 1]), 0, H - 1))

            wall_field = np.array([gx[y, x], gy[y, x]])

            desired = 0.84 * to_target + 0.16 * wall_field
            desired += NOISE * np.random.randn(2)
            desired /= np.linalg.norm(desired) + 1e-9

            # deflection here only controls how fast velocity adapts
            # to the local desired geometric direction.
            vel[i] = (1.0 - deflection) * vel[i] + deflection * desired
            vel[i] /= np.linalg.norm(vel[i]) + 1e-9

            new = pos[i] + STEP * vel[i]

            if not inside_free(new):
                n = local_normal(pos[i])
                vel[i] = reflect(vel[i], n)
                vel[i] += NOISE * np.random.randn(2)
                vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                new = pos[i] + STEP * vel[i]

                if not inside_free(new):
                    failed[i] = True
                    continue

            pos[i] = new

            if np.linalg.norm(pos[i] - TARGET) < HIT_RADIUS:
                reached[i] = True
                arrival_steps[i] = step_i
                continue

    rows = []

    for zone, values in zone_entry_steps.items():
        valid = values[np.isfinite(values)]

        if len(valid) > 1:
            mean_step = float(np.mean(valid))
            std_step = float(np.std(valid))
            jitter = float(std_step / (mean_step + 1e-9))
        else:
            mean_step = np.nan
            std_step = np.nan
            jitter = np.nan

        rows.append({
            "seed": seed,
            "deflection": deflection,
            "zone": zone,
            "n_entered": int(len(valid)),
            "entry_mean_step": mean_step,
            "entry_std_step": std_step,
            "local_temporal_jitter": jitter,
            "success_rate": float(np.mean(reached)),
            "failure_rate": float(np.mean(failed)),
        })

    return rows


all_rows = []

print("\n=== BALLISTIC NO-INTERACTION BASELINE ===\n")

for deflection in DEFLECTION_VALUES:
    print(f"DEFLECTION = {deflection}")

    for seed in range(N_SEEDS):
        rows = run_baseline(seed, deflection)
        all_rows.extend(rows)

    print("  done")

df = pd.DataFrame(all_rows)

csv_path = os.path.join(EXPORT_DIR, "ballistic_no_interaction_results.csv")
df.to_csv(csv_path, index=False)

summary = df.groupby(["deflection", "zone"]).agg(
    n_entered_mean=("n_entered", "mean"),
    entry_mean_step=("entry_mean_step", "mean"),
    entry_std_step=("entry_std_step", "mean"),
    local_jitter_mean=("local_temporal_jitter", "mean"),
    success_mean=("success_rate", "mean"),
    failure_mean=("failure_rate", "mean"),
).reset_index()

summary_path = os.path.join(EXPORT_DIR, "ballistic_no_interaction_summary.csv")
summary.to_csv(summary_path, index=False)

print("\nSummary:")
print(summary)

plt.figure(figsize=(8, 5))

for deflection in DEFLECTION_VALUES:
    part = summary[summary["deflection"] == deflection]
    plt.plot(
        part["zone"],
        part["local_jitter_mean"],
        marker="o",
        label=f"D={deflection}",
    )

plt.ylabel("local temporal jitter")
plt.xlabel("corridor zone")
plt.title("Ballistic No-Interaction Baseline — Local Jitter")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()

fig_path = os.path.join(FIGURE_DIR, "ballistic_no_interaction_jitter.png")
plt.savefig(fig_path, dpi=180)
plt.show()

print("\nSaved:")
print(csv_path)
print(summary_path)
print(fig_path)