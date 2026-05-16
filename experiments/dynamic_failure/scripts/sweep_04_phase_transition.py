# ============================================================
# sweep_04_phase_transition.py
#
# STRUX Experimental Subsystem
# Dynamic Failure / Adaptive Recovery
#
# Purpose:
# Explore phase-like behavior in constrained flow systems
# with:
# - live/dead particles
# - local collisions
# - residue dynamics
# - adaptive deflection
#
# This module is EXPERIMENTAL and NOT part of core STRUX.
#
# Current focus:
# - robustness
# - reproducibility
# - parameter sensitivity
# - congestion dynamics
#
# No claims of:
# - intelligence
# - universal physics
# - emergent cognition
#
# ============================================================

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt

# ============================================================
# OUTPUT
# ============================================================

EXPORT_DIR = "experiments/dynamic_failure/results"
FIGURE_DIR = "experiments/dynamic_failure/figures"

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(FIGURE_DIR, exist_ok=True)

# ============================================================
# GLOBAL PARAMETERS
# ============================================================

N_SEEDS = 20

CORRIDOR_VALUES = [17, 15, 13, 11, 9]
DEFLECTION_VALUES = [0.10, 0.20, 0.30, 0.40, 0.50]

# ============================================================
# CORE SIMULATION
# ============================================================

def run_dynamic_failure(
    seed=0,
    corridor_radius=15,
    deflection_strength=0.3,
):

    np.random.seed(seed)

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

    yy, xx = np.mgrid[0:H, 0:W]
    free = np.zeros((H, W), dtype=np.uint8)

    # ========================================================
    # GEOMETRY
    # ========================================================

    control = np.array([
        [20, H/2],
        [85, H/2 - 36],
        [145, H/2 + 36],
        [205, H/2 - 36],
        [265, H/2 + 36],
        [340, H/2],
    ], dtype=float)

    pts = []

    for a, b in zip(control[:-1], control[1:]):
        pts.append(np.linspace(a, b, 280))

    centerline = np.vstack(pts)

    for x0, y0 in centerline:
        d2 = (xx - x0)**2 + (yy - y0)**2
        free[d2 <= corridor_radius**2] = 1

    for cx, cy, rr in [
        (SOURCE[0], SOURCE[1], 18),
        (TARGET[0], TARGET[1], 18),
    ]:
        d2 = (xx - cx)**2 + (yy - cy)**2
        free[d2 <= rr**2] = 1

    # ========================================================
    # DISTANCE FIELD
    # ========================================================

    dist = distance_transform_edt(free)

    gy, gx = np.gradient(dist.astype(float))

    norm = np.sqrt(gx**2 + gy**2) + 1e-9

    gx = gx / norm
    gy = gy / norm

    # ========================================================
    # HELPERS
    # ========================================================

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

    # ========================================================
    # INITIALIZATION
    # ========================================================

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

    arrival_steps = np.full(N_PARTICLES, np.nan)
    death_steps = np.full(N_PARTICLES, np.nan)

    # ========================================================
    # MAIN LOOP
    # ========================================================

    for step_i in range(MAX_STEPS):

        dead_idx = np.where(dead)[0]
        live_idx = np.where(alive)[0]

        # ----------------------------------------------------
        # LIVE-DEAD INTERACTION
        # ----------------------------------------------------

        for i in live_idx:

            for j in dead_idx:

                d = pos[i] - pos[j]

                dist_ij = np.linalg.norm(d) + 1e-9

                if dist_ij < COLLISION_RADIUS:

                    n = d / dist_ij

                    vel[i] = (
                        (1.0 - deflection_strength) * vel[i]
                        + deflection_strength * n
                    )

                    vel[i] += 0.04 * np.random.randn(2)

                    vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                    vel[j] += DEAD_PUSH_STRENGTH * (-n)

                    vel[j] *= DEAD_DRAG

                    vel[j] /= np.linalg.norm(vel[j]) + 1e-9

        # ----------------------------------------------------
        # PARTICLE UPDATE
        # ----------------------------------------------------

        for i in range(N_PARTICLES):

            if reached[i]:
                continue

            # ------------------------------------------------
            # ALIVE
            # ------------------------------------------------

            if alive[i]:

                to_target = TARGET - pos[i]

                to_target /= np.linalg.norm(to_target) + 1e-9

                x = int(np.clip(round(pos[i,0]), 0, W - 1))
                y = int(np.clip(round(pos[i,1]), 0, H - 1))

                G = np.array([gx[y, x], gy[y, x]])

                desired = 0.84 * to_target + 0.16 * G

                desired += NOISE_LIVE * np.random.randn(2)

                desired /= np.linalg.norm(desired) + 1e-9

                vel[i] = 0.86 * vel[i] + 0.14 * desired

                vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                new = pos[i] + STEP * vel[i]

                # --------------------------------------------
                # WALL COLLISION
                # --------------------------------------------

                if not inside_free(new):

                    n = local_normal(pos[i])

                    vel[i] = reflect(vel[i], n)

                    vel[i] += 0.04 * np.random.randn(2)

                    vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                    new = pos[i] + STEP * vel[i]

                    if not inside_free(new):

                        alive[i] = False
                        dead[i] = True

                        death_steps[i] = step_i

                        continue

                pos[i] = new

                # --------------------------------------------
                # TARGET REACHED
                # --------------------------------------------

                if np.linalg.norm(pos[i] - TARGET) < HIT_RADIUS:

                    alive[i] = False
                    reached[i] = True

                    arrival_steps[i] = step_i

                    continue

                # --------------------------------------------
                # PROGRESS FAILURE
                # --------------------------------------------

                if step_i - last_progress_step[i] >= PROGRESS_WINDOW:

                    progress_gain = (
                        pos[i,0] - last_progress_pos[i,0]
                    )

                    if (
                        progress_gain < MIN_PROGRESS
                        or step_i > FAIL_TIMEOUT
                    ):

                        alive[i] = False
                        dead[i] = True

                        death_steps[i] = step_i

                        continue

                    last_progress_pos[i] = pos[i].copy()
                    last_progress_step[i] = step_i

            # ------------------------------------------------
            # DEAD
            # ------------------------------------------------

            elif dead[i]:

                vel[i] *= DEAD_DRAG

                vel[i] += NOISE_DEAD * np.random.randn(2)

                vel[i] /= np.linalg.norm(vel[i]) + 1e-9

                new = pos[i] + 0.35 * STEP * vel[i]

                if inside_free(new):
                    pos[i] = new

    # ========================================================
    # METRICS
    # ========================================================

    success_rate = float(np.mean(reached))
    death_rate = float(np.mean(dead))

    valid_arrivals = arrival_steps[np.isfinite(arrival_steps)]

    if len(valid_arrivals) > 1:

        mean_arrival = float(np.mean(valid_arrivals))

        temporal_jitter = float(
            np.std(valid_arrivals)
            / (mean_arrival + 1e-9)
        )

    else:

        mean_arrival = np.nan
        temporal_jitter = np.nan

    valid_deaths = death_steps[np.isfinite(death_steps)]

    first_death_step = (
        float(np.min(valid_deaths))
        if len(valid_deaths)
        else np.nan
    )

    return {
        "seed": seed,
        "corridor_radius": corridor_radius,
        "deflection": deflection_strength,
        "success_rate": success_rate,
        "death_rate": death_rate,
        "temporal_jitter": temporal_jitter,
        "mean_arrival": mean_arrival,
        "first_death_step": first_death_step,
    }

# ============================================================
# PARAMETER SWEEP
# ============================================================

all_results = []

for corridor in CORRIDOR_VALUES:

    for deflection in DEFLECTION_VALUES:

        print("\n===================================")
        print(f"CORRIDOR_RADIUS = {corridor}")
        print(f"DEFLECTION      = {deflection}")
        print("===================================")

        local_results = []

        for seed in range(N_SEEDS):

            r = run_dynamic_failure(
                seed=seed,
                corridor_radius=corridor,
                deflection_strength=deflection,
            )

            local_results.append(r)
            all_results.append(r)

        temp = pd.DataFrame(local_results)

        print(
            "success:",
            round(temp["success_rate"].mean(), 4),
            "death:",
            round(temp["death_rate"].mean(), 4),
            "jitter:",
            round(temp["temporal_jitter"].mean(), 4),
        )

# ============================================================
# SAVE RESULTS
# ============================================================

df = pd.DataFrame(all_results)

csv_path = os.path.join(
    EXPORT_DIR,
    "phase_sweep_results.csv"
)

df.to_csv(csv_path, index=False)

summary = df.groupby(
    ["corridor_radius", "deflection"]
).agg(
    success_mean=("success_rate", "mean"),
    death_mean=("death_rate", "mean"),
    jitter_mean=("temporal_jitter", "mean"),
    first_death_mean=("first_death_step", "mean"),
).reset_index()

summary_path = os.path.join(
    EXPORT_DIR,
    "sweep_summary.csv"
)

summary.to_csv(summary_path, index=False)

print("\nSaved:")
print(csv_path)
print(summary_path)