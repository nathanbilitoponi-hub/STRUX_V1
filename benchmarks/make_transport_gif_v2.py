"""
STRUX_TRANSPORT_GIF_V2

Generate a cleaner animated GIF using stable corridor-following trajectories.

This version is designed only for visualization / communication.

Output:
exports/STRUX_TRANSPORT_GIF_V2/transport_v2.gif
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio

np.random.seed(42)

# ============================================================
# CONFIG
# ============================================================

H, W = 180, 340

N_PARTICLES = 80
N_FRAMES = 180

SOURCE_X = 20
TARGET_X = W - 20

CORRIDOR_RADIUS = 8

EXPORT_DIR = "exports/STRUX_TRANSPORT_GIF_V2"
os.makedirs(EXPORT_DIR, exist_ok=True)


# ============================================================
# CENTERLINES
# ============================================================

def straight_centerline(t):
    x = SOURCE_X + t * (TARGET_X - SOURCE_X)
    y = H / 2
    return x, y


def mild_curve_centerline(t):
    x = SOURCE_X + t * (TARGET_X - SOURCE_X)
    y = H / 2 + 22 * np.sin(2 * np.pi * t)
    return x, y


def zigzag_centerline(t):
    control = np.array([
        [SOURCE_X, H / 2],
        [80, H / 2 - 42],
        [135, H / 2 + 42],
        [190, H / 2 - 42],
        [245, H / 2 + 42],
        [TARGET_X, H / 2],
    ], dtype=float)

    seg_count = len(control) - 1

    u = np.clip(t, 0, 1) * seg_count
    idx = int(np.clip(np.floor(u), 0, seg_count - 1))
    local_t = u - idx

    p = (1 - local_t) * control[idx] + local_t * control[idx + 1]

    return p[0], p[1]


SCENES = {
    "STRAIGHT": straight_centerline,
    "MILD CURVE": mild_curve_centerline,
    "ZIGZAG": zigzag_centerline,
}


# ============================================================
# DRAW CORRIDORS
# ============================================================

def sample_centerline(fn, n=900):
    ts = np.linspace(0, 1, n)
    pts = np.array([fn(t) for t in ts], dtype=float)
    return pts


def draw_corridor(ax, fn):
    pts = sample_centerline(fn)

    ax.plot(
        pts[:, 0],
        pts[:, 1],
        color="white",
        linewidth=22,
        solid_capstyle="round",
        zorder=1,
    )

    ax.plot(
        pts[:, 0],
        pts[:, 1],
        color="black",
        linewidth=2,
        alpha=0.35,
        zorder=2,
    )


def tangent_normal(fn, t, eps=1e-4):
    t0 = max(0.0, t - eps)
    t1 = min(1.0, t + eps)

    p0 = np.array(fn(t0), dtype=float)
    p1 = np.array(fn(t1), dtype=float)

    tan = p1 - p0
    tan /= np.linalg.norm(tan) + 1e-9

    normal = np.array([-tan[1], tan[0]])

    return tan, normal


# ============================================================
# PARTICLE OFFSETS
# ============================================================

particle_offsets = {
    name: np.random.normal(
        loc=0.0,
        scale=2.0 if name != "ZIGZAG" else 3.0,
        size=N_PARTICLES,
    )
    for name in SCENES
}

particle_speed_noise = {
    name: np.random.normal(
        loc=0.0,
        scale=0.010 if name == "STRAIGHT" else (0.018 if name == "MILD CURVE" else 0.045),
        size=N_PARTICLES,
    )
    for name in SCENES
}


# ============================================================
# METRIC LABELS
# ============================================================

METRICS = {
    "STRAIGHT": {
        "success": 1.00,
        "jitter": 0.0018,
        "coherence": 0.996,
    },
    "MILD CURVE": {
        "success": 1.00,
        "jitter": 0.0031,
        "coherence": 0.935,
    },
    "ZIGZAG": {
        "success": 0.752,
        "jitter": 0.0313,
        "coherence": 0.642,
    },
}


# ============================================================
# BUILD FRAMES
# ============================================================

frames = []

for frame_i in range(N_FRAMES):

    progress = frame_i / (N_FRAMES - 1)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, (name, fn) in zip(axes, SCENES.items()):

        ax.set_facecolor("black")
        draw_corridor(ax, fn)

        ax.scatter(
            SOURCE_X,
            H / 2,
            c="lime",
            s=80,
            edgecolor="black",
            zorder=5,
        )

        ax.scatter(
            TARGET_X,
            H / 2,
            c="cyan",
            s=110,
            marker="*",
            edgecolor="black",
            zorder=5,
        )

        xs = []
        ys = []

        for i in range(N_PARTICLES):

            # particle-specific progress jitter
            p = progress + particle_speed_noise[name][i] * np.sin(2 * np.pi * progress)

            # zigzag loses / delays some particles visually
            if name == "ZIGZAG":
                p -= 0.10 * np.abs(np.sin(4 * np.pi * progress)) * (i % 5 == 0)

            p = np.clip(p, 0.0, 1.0)

            x, y = fn(p)

            _, normal = tangent_normal(fn, p)

            spread = particle_offsets[name][i]

            # more dispersion in zigzag around corners
            if name == "ZIGZAG":
                spread += np.random.normal(0, 1.2)

            pos = np.array([x, y]) + spread * normal

            xs.append(pos[0])
            ys.append(pos[1])

        ax.scatter(
            xs,
            ys,
            s=10,
            c="dodgerblue",
            alpha=0.75,
            zorder=4,
        )

        m = METRICS[name]

        ax.set_title(
            f"{name}\n"
            f"success={m['success']:.2f} | "
            f"jitter={m['jitter']:.4f} | "
            f"coh={m['coherence']:.3f}",
            color="black",
            fontsize=11,
        )

        ax.set_xlim(0, W)
        ax.set_ylim(20, H - 20)
        ax.axis("off")

    plt.tight_layout()

    frame_path = os.path.join(EXPORT_DIR, f"frame_{frame_i:04d}.png")
    plt.savefig(frame_path, dpi=120)
    plt.close(fig)

    frames.append(imageio.imread(frame_path))


# ============================================================
# SAVE GIF
# ============================================================

gif_path = os.path.join(EXPORT_DIR, "transport_v2.gif")

imageio.mimsave(
    gif_path,
    frames,
    duration=0.055,
    loop=0,
)

print(f"Saved GIF : {gif_path}")