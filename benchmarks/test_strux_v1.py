import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import numpy as np
import matplotlib.pyplot as plt

from core.multiscale.multiscale_life import run_strux_life
from core.connection_scoring.connection_scoring import score_region_connections
from core.backbone.backbone_mst import extract_backbone
from core.persistence.persistence import compute_edge_persistence_advanced


# ============================================================
# SYNTHETIC DATASET
# ============================================================

rng = np.random.default_rng(7)

n_filament = 500

t = np.linspace(0, 10, n_filament)

x = t
y = 0.4 * np.sin(t)
z = 0.25 * np.cos(0.7 * t)

filament = np.column_stack([x, y, z])

noise = rng.normal(scale=0.18, size=filament.shape)

filament = filament + noise

blob_1 = rng.normal(
    loc=[2.0, 0.0, 0.0],
    scale=0.35,
    size=(120, 3),
)

blob_2 = rng.normal(
    loc=[8.0, 0.0, 0.0],
    scale=0.35,
    size=(120, 3),
)

points = np.vstack([
    filament,
    blob_1,
    blob_2,
])

print()
print("DATASET")
print("points:", len(points))


# ============================================================
# STRUX LIFE
# ============================================================

life = run_strux_life(
    points,
    base_radius=0.22,
    verbose=True,
)

large_regions = life["large_summary"]

if len(large_regions) == 0:
    large_regions = life["medium_seed_nodes"]

if len(large_regions) == 0:
    large_regions = life["small_summary"]

print()
print("LARGE REGIONS:", len(large_regions))


# ============================================================
# CONNECTION SCORING
# ============================================================

conn = score_region_connections(
    points=points,
    large_regions=large_regions,
    tube_radius=0.65,
)

strong_edges = conn["strong_edges"]

print()
print("STRONG FILAMENTS:", len(strong_edges))


# ============================================================
# BACKBONE
# ============================================================

graph_edges = []

for e in strong_edges:
    graph_edges.append({
        "u": e["source"],
        "v": e["target"],
        "length": e["segment_length"],
        "score": e["continuity"],
    })

nodes, mst_edges = extract_backbone(
    graph_edges,
    verbose=True,
)

print()
print("MST EDGES:", len(mst_edges))


# ============================================================
# PERSISTENCE
# ============================================================

persistent = compute_edge_persistence_advanced(
    graph=graph_edges,
    node_positions=np.array([
        r["center"]
        for r in large_regions
    ]),
    iterations=20,
    sample_ratio=0.8,
    eps=0.8,
    persistence_threshold=0.5,
)

print()
print("PERSISTENT CLUSTERS:",
      persistent["total_clusters"])

print("PERSISTENT CORE:",
      len(persistent["persistent_core"]))


# ============================================================
# VISUALIZATION
# ============================================================

fig = plt.figure(figsize=(10, 8))

ax = fig.add_subplot(111, projection="3d")

ax.scatter(
    points[:, 0],
    points[:, 1],
    points[:, 2],
    s=3,
    alpha=0.35,
)

centers = np.array([
    r["center"]
    for r in large_regions
])

if len(centers) > 0:
    ax.scatter(
        centers[:, 0],
        centers[:, 1],
        centers[:, 2],
        s=80,
    )

for e in strong_edges:
    p1 = centers[e["source"]]
    p2 = centers[e["target"]]

    ax.plot(
        [p1[0], p2[0]],
        [p1[1], p2[1]],
        [p1[2], p2[2]],
        linewidth=2,
    )

ax.set_title("STRUX V1")

plt.tight_layout()
plt.show()