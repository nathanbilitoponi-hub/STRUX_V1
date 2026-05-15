"""
STRUX_TRANSPORT_GIF

Generate a simple animated visualization
for constrained transport propagation.

Scenes:
- STRAIGHT
- MILD_CURVE
- ZIGZAG

Output:
exports/STRUX_TRANSPORT_GIF/transport.gif
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from scipy.ndimage import distance_transform_edt

np.random.seed(42)

# ============================================================
# CONFIG
# ============================================================

H, W = 180, 340

SOURCE = np.array([20, H // 2])
TARGET = np.array([W - 20, H // 2])

N_PARTICLES = 180
MAX_STEPS = 520

STEP = 1.0
NOISE = 0.030
HIT_RADIUS = 14
CORRIDOR_RADIUS = 8

EXPORT_DIR = "exports/STRUX_TRANSPORT_GIF"
os.makedirs(EXPORT_DIR, exist_ok=True)

yy, xx = np.mgrid[0:H, 0:W]


# ============================================================
# GEOMETRY
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
    "STRAIGHT": carve_corridor(centerline_straight()),
    "MILD_CURVE": carve_corridor(centerline_mild_curve()),
    "ZIGZAG": carve_corridor(centerline_zigzag()),
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
# SIMULATION
# ============================================================

def simulate(free):
    gx, gy = local_field(free)

    positions = np.zeros((N_PARTICLES, 2), dtype=float)

    for i in range(N_PARTICLES):
        positions[i] = SOURCE.astype(float)

    alive = np.ones(N_PARTICLES, dtype=bool)

    history = []

    for step_i in range(MAX_STEPS):

        current = []

        for i in range(N_PARTICLES):

            if not alive[i]:
                current.append(positions[i].copy())
                continue

            pos = positions[i]

            x = int(np.clip(round(pos[0]), 0, W - 1))
            y = int(np.clip(round(pos[1]), 0, H - 1))

            if free[y, x] == 0:
                alive[i] = False
                current.append(pos.copy())
                continue

            G = np.array([gx[y, x], gy[y, x]])

            to_target = TARGET - pos
            to_target /= np.linalg.norm(to_target) + 1e-9

            D = 0.85 * to_target + 0.15 * G
            D += NOISE * np.random.randn(2)
            D /= np.linalg.norm(D) + 1e-9

            new = pos + STEP * D

            nx = int(np.clip(round(new[0]), 0, W - 1))
            ny = int(np.clip(round(new[1]), 0, H - 1))

            if free[ny, nx] == 0:
                alive[i] = False
                current.append(pos.copy())
                continue

            positions[i] = new
            current.append(new.copy())

            if np.linalg.norm(new - TARGET) < HIT_RADIUS:
                alive[i] = False

        history.append(np.array(current))

    return history


# ============================================================
# RUN
# ============================================================

scene_histories = {}

for name, free in SCENES.items():
    print(f"Simulating {name}...")
    scene_histories[name] = simulate(free)


# ============================================================
# BUILD FRAMES
# ============================================================

frames = []

for t in range(MAX_STEPS):

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, (name, free) in zip(axes, SCENES.items()):

        ax.imshow(free, cmap="gray", origin="lower")

        pts = scene_histories[name][t]

        ax.scatter(
            pts[:, 0],
            pts[:, 1],
            s=8,
            c="dodgerblue",
            alpha=0.75,
        )

        ax.scatter(
            SOURCE[0],
            SOURCE[1],
            c="lime",
            s=80,
            edgecolor="black",
        )

        ax.scatter(
            TARGET[0],
            TARGET[1],
            c="cyan",
            s=100,
            marker="*",
            edgecolor="black",
        )

        ax.set_title(name)
        ax.axis("off")

    plt.tight_layout()

    frame_path = os.path.join(EXPORT_DIR, f"frame_{t:04d}.png")
    plt.savefig(frame_path, dpi=120)

    plt.close(fig)

    frames.append(imageio.imread(frame_path))


# ============================================================
# SAVE GIF
# ============================================================

gif_path = os.path.join(EXPORT_DIR, "transport.gif")

imageio.mimsave(
    gif_path,
    frames,
    duration=0.045,
    loop=0,
)

print(f"\nSaved GIF : {gif_path}")