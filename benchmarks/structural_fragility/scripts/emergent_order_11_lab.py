"""
STRUX Emergent Order LAB

Goal:
Do NOT impose a fixed pipeline.

We place minimal geometric forms inside a unit circle.
Then we compute several "digital senses" in parallel:

- occupancy / matter
- void
- membrane
- transition
- continuity
- backbone tendency

Then STRUX reads which signal becomes organized first.

This is a LAB test.
Do not commit unless the result is useful.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt, gaussian_filter, sobel

FIG = "benchmarks/structural_fragility/figures"
RES = "benchmarks/structural_fragility/results"

os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

print("=" * 70)
print("STRUX EMERGENT ORDER LAB")
print("=" * 70)

# ============================================================
# 1. World: unit circle
# ============================================================

N = 220
x = np.linspace(-1, 1, N)
y = np.linspace(-1, 1, N)
X, Y = np.meshgrid(x, y)

R = np.sqrt(X**2 + Y**2)
circle = R <= 1.0

matter = np.zeros((N, N), dtype=float)

# ============================================================
# 2. Minimal shapes as matter strokes
# ============================================================

def add_line(mask, p1, p2, thickness=0.015):
    x1, y1 = p1
    x2, y2 = p2

    vx = x2 - x1
    vy = y2 - y1

    px = X - x1
    py = Y - y1

    L2 = vx*vx + vy*vy + 1e-12
    t = np.clip((px*vx + py*vy) / L2, 0, 1)

    projx = x1 + t*vx
    projy = y1 + t*vy

    d = np.sqrt((X-projx)**2 + (Y-projy)**2)

    mask[d < thickness] = 1.0


def polygon_vertices(n, center, radius, phase=0.0):
    cx, cy = center
    ang = np.linspace(0, 2*np.pi, n, endpoint=False) + phase
    return [(cx + radius*np.cos(a), cy + radius*np.sin(a)) for a in ang]


def add_polygon(mask, n, center, radius, phase=0.0, thickness=0.015):
    pts = polygon_vertices(n, center, radius, phase)
    for i in range(n):
        add_line(mask, pts[i], pts[(i+1) % n], thickness=thickness)


# place minimal forms
add_polygon(matter, 3, center=(-0.35, 0.15), radius=0.22, phase=np.pi/2, thickness=0.014)
add_polygon(matter, 4, center=(0.32, 0.12), radius=0.20, phase=np.pi/4, thickness=0.014)
add_polygon(matter, 6, center=(0.0, -0.35), radius=0.23, phase=0.0, thickness=0.014)

matter *= circle

# ============================================================
# 3. Digital senses, computed in parallel
# ============================================================

# sense A: occupancy / matter density
matter_s = gaussian_filter(matter, sigma=2)

# sense B: void = distance from matter inside circle
void_raw = distance_transform_edt((matter < 0.5) & circle)
void_s = void_raw / (void_raw.max() + 1e-12)

# sense C: membrane = boundary between matter and void
gx = sobel(matter_s, axis=1)
gy = sobel(matter_s, axis=0)
membrane_s = np.sqrt(gx*gx + gy*gy)
membrane_s *= circle
membrane_s /= membrane_s.max() + 1e-12

# sense D: transition = gradient of void field
vgx = sobel(void_s, axis=1)
vgy = sobel(void_s, axis=0)
transition_s = np.sqrt(vgx*vgx + vgy*vgy)
transition_s *= circle
transition_s /= transition_s.max() + 1e-12

# sense E: continuity = smoothed matter pathways
continuity_s = gaussian_filter(matter, sigma=5)
continuity_s *= circle
continuity_s /= continuity_s.max() + 1e-12

# sense F: backbone tendency = overlap of continuity and transition
backbone_s = continuity_s * transition_s
backbone_s *= circle
backbone_s /= backbone_s.max() + 1e-12

senses = {
    "matter": matter_s,
    "void": void_s,
    "membrane": membrane_s,
    "transition": transition_s,
    "continuity": continuity_s,
    "backbone": backbone_s,
}

# ============================================================
# 4. Emergence score
# ============================================================

def emergence_score(A):
    """
    Measures whether a sense is organized:
    high contrast + spatial concentration + non-random structure.
    """
    vals = A[circle]
    vals = vals[np.isfinite(vals)]

    if vals.max() <= 1e-12:
        return 0.0, {}

    mean = float(vals.mean())
    std = float(vals.std())
    p95 = float(np.percentile(vals, 95))
    p50 = float(np.percentile(vals, 50))

    contrast = p95 - p50
    concentration = float(np.mean(vals > p95))
    sharpness = std / (mean + 1e-12)

    score = contrast * sharpness / (concentration + 1e-3)

    details = {
        "mean": mean,
        "std": std,
        "p50": p50,
        "p95": p95,
        "contrast": contrast,
        "concentration": concentration,
        "sharpness": sharpness,
        "score": score,
    }

    return score, details


rows = []

for name, A in senses.items():
    score, details = emergence_score(A)
    details["sense"] = name
    rows.append(details)

rows = sorted(rows, key=lambda r: r["score"], reverse=True)

print()
print("Natural emergence order:")
for i, r in enumerate(rows, start=1):
    print(
        f"{i}. {r['sense']:12s} "
        f"score={r['score']:.4f} "
        f"contrast={r['contrast']:.4f} "
        f"sharpness={r['sharpness']:.4f}"
    )

# ============================================================
# 5. Save figure
# ============================================================

fig, axes = plt.subplots(2, 3, figsize=(12, 8))
axes = axes.ravel()

for ax, (name, A) in zip(axes, senses.items()):
    ax.imshow(A, origin="lower", cmap="magma", extent=(-1, 1, -1, 1))
    ax.contour(circle, levels=[0.5], colors="white", linewidths=0.5, extent=(-1, 1, -1, 1))
    ax.set_title(name)
    ax.axis("off")

plt.tight_layout()

fig_path = os.path.join(FIG, "emergent_order_11_lab_senses.png")
plt.savefig(fig_path, dpi=220, bbox_inches="tight")
plt.close()

# order bar
plt.figure(figsize=(8, 4))
names = [r["sense"] for r in rows]
scores = [r["score"] for r in rows]
plt.bar(names, scores)
plt.ylabel("emergence score")
plt.title("STRUX LAB — natural emergence order")
plt.xticks(rotation=30)
plt.tight_layout()

bar_path = os.path.join(FIG, "emergent_order_11_lab_order.png")
plt.savefig(bar_path, dpi=220, bbox_inches="tight")
plt.close()

print()
print("Saved:")
print(fig_path)
print(bar_path)

print()
print("Interpretation guide:")
print("- matter high first     -> STRUX starts from object/stroke")
print("- void high first       -> STRUX starts from empty-space organization")
print("- membrane high first   -> STRUX starts from boundaries")
print("- transition high first -> STRUX starts from change between regimes")
print("- backbone high first   -> STRUX starts from composed support")