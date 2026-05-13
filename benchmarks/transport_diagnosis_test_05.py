"""
STRUX_SINGLE_TRAPPED_TEST_05

Purpose
-------
Validate transport branching diagnosis using gate mode count.

Validated synthetic classes:
- SINGLE COHERENT CHANNEL
- MULTI-CHANNEL / BRAIDED
- TRAPPED / INCOMPLETE

Expected behavior
-----------------
A_REFERENCE_OPEN:
    -> 1 mode

H_BRAIDED:
    -> multiple modes

I_SINGLE_TRAPPED:
    -> 0 modes

This benchmark validates:
- completion
- coherence
- branching

This benchmark does NOT validate:
- physical transport theory
- energy flow
- universal topology laws
"""

import numpy as np
import matplotlib.pyplot as plt

from scipy.ndimage import distance_transform_edt

from core.transport.transport_diagnosis_v1 import (
    diagnose_transport,
)

# ============================================================
# CONFIG
# ============================================================

np.random.seed(88)

H, W = 180, 340

SOURCE = np.array([18, H // 2])
TARGET = np.array([W - 18, H // 2])

X_GATE = W - 85

N_PARTICLES = 260
MAX_STEPS = 950

STEP = 1.0
NOISE = 0.08

HIT_RADIUS = 10

yy, xx = np.mgrid[0:H, 0:W]

# ============================================================
# GEOMETRY HELPERS
# ============================================================


def carve_disk(free, cx, cy, r):

    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    free[d2 <= r * r] = 1

    return free


# ============================================================
# SCENES
# ============================================================


def make_reference():

    free = np.zeros((H, W), dtype=np.uint8)

    xs = np.linspace(25, W - 25, 560)
    ys = H / 2 + 45 * np.sin((xs - 25) / (W - 50) * 2 * np.pi)

    for x0, y0 in zip(xs, ys):
        free = carve_disk(free, x0, y0, 12)

    return free


def make_braided():

    free = np.zeros((H, W), dtype=np.uint8)

    offsets = [-36, -18, 0, 18, 36]

    for k, off in enumerate(offsets):

        xs = np.linspace(25, W - 25, 500)
        ys = H / 2 + off + 10 * np.sin(xs / 35 + k)

        for x0, y0 in zip(xs, ys):
            free = carve_disk(free, x0, y0, 7)

    free = carve_disk(free, *SOURCE, 15)
    free = carve_disk(free, *TARGET, 15)

    return free


def make_single_trapped():

    free = make_reference()

    free[:, W - 70:W - 50] = 0

    free = carve_disk(free, *TARGET, 15)

    return free


SCENES = {
    "A_REFERENCE_OPEN": make_reference(),
    "H_BRAIDED": make_braided(),
    "I_SINGLE_TRAPPED": make_single_trapped(),
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

        a = np.random.uniform(-0.35, 0.35)

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

            D = 0.96 * D + 0.04 * to_target

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

                gy_cross = interpolate_gate_crossing(
                    pos,
                    new,
                    X_GATE,
                )

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

        coherences.append(
            np.mean(local_align) if len(local_align) > 0 else 0
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

results = {}

for name, free in SCENES.items():

    results[name] = {
        "free": free,
        "metrics": run_transport(free),
    }

# ============================================================
# PRINT
# ============================================================

print("\n=== STRUX_SINGLE_TRAPPED_TEST_05 ===\n")

for name, r in results.items():

    m = r["metrics"]

    print(name)
    print(f"  success_rate        : {m['success_rate']:.4f}")
    print(f"  direction_coherence : {m['direction_coherence']:.4f}")
    print(f"  detected_modes      : {m['n_modes']}")
    print(f"  transport_class     : {m['transport_class']}")
    print()

# ============================================================
# VISUALIZATION
# ============================================================

fig, axes = plt.subplots(1, 3, figsize=(21, 5))

for ax, (name, r) in zip(axes, results.items()):

    free = r["free"]

    m = r["metrics"]

    ax.imshow(free, cmap="gray", origin="lower")

    ax.axvline(X_GATE, color="yellow", linewidth=2)

    ax.set_title(
        f"{name}\n"
        f"modes={m['n_modes']}\n"
        f"{m['transport_class']}"
    )

    ax.axis("off")

    for path, success in zip(
        m["trajectories"],
        m["successes"],
    ):

        if len(path) < 2:
            continue

        color = "dodgerblue" if success else "red"

        alpha = 0.55 if success else 0.08

        ax.plot(
            path[:, 0],
            path[:, 1],
            color=color,
            linewidth=0.8,
            alpha=alpha,
        )

    if len(m["gate_values"]) > 0:

        ax.scatter(
            np.full_like(m["gate_values"], X_GATE),
            m["gate_values"],
            c="orange",
            s=20,
            edgecolor="black",
            linewidth=0.3,
            zorder=5,
        )

    ax.scatter(
        SOURCE[0],
        SOURCE[1],
        c="lime",
        s=90,
        edgecolor="black",
    )

    ax.scatter(
        TARGET[0],
        TARGET[1],
        c="cyan",
        marker="*",
        s=130,
        edgecolor="black",
    )

plt.tight_layout()
plt.show()

print(
    """
=== INTERPRETATION ===

Validated behavior:

A_REFERENCE_OPEN:
    SINGLE COHERENT CHANNEL

H_BRAIDED:
    MULTI-CHANNEL / BRAIDED

I_SINGLE_TRAPPED:
    TRAPPED / INCOMPLETE

This benchmark validates:
branching diagnosis using gate mode count.
"""
)