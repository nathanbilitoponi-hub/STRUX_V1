"""
MISSION 08C FIX

Florence STRUX vs Betweenness spatial overlap.

Important:
This script recomputes STRUX and Betweenness on the SAME downloaded graph,
so node IDs are consistent.

Question:
Do STRUX and Betweenness identify the same urban zones or different ones?
"""

import os
import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp

FIG = "benchmarks/structural_fragility/figures"
RES = "benchmarks/structural_fragility/results"

os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

CENTER = (43.7696, 11.2558)
DIST = 1800
NETWORK_TYPE = "drive"
TUBE_RADIUS = 150
TOP_N = 40

print("=" * 70)
print("MISSION 08C FIX — FLORENCE SPATIAL OVERLAP")
print("=" * 70)

# ------------------------------------------------------------
# 1. Load graph once
# ------------------------------------------------------------

G = ox.graph_from_point(
    CENTER,
    dist=DIST,
    network_type=NETWORK_TYPE,
    simplify=True
)

G = ox.project_graph(G)

print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())

nodes_df, _ = ox.graph_to_gdfs(G)

node_coords = nodes_df[["x", "y"]].to_numpy()
node_ids = nodes_df.index.tolist()
node_id_to_idx = {nid: i for i, nid in enumerate(node_ids)}

pos = {
    n: (float(data["x"]), float(data["y"]))
    for n, data in G.nodes(data=True)
}

# ------------------------------------------------------------
# 2. STRUX corridor score per edge
# ------------------------------------------------------------

def calculate_corridor_score(u, v):
    if u not in node_id_to_idx or v not in node_id_to_idx:
        return 0.0

    p1 = node_coords[node_id_to_idx[u]]
    p2 = node_coords[node_id_to_idx[v]]

    edge_vec = p2 - p1
    edge_len = np.linalg.norm(edge_vec)

    if edge_len < 1e-9:
        return 0.0

    unit_vec = edge_vec / edge_len

    rel = node_coords - p1
    proj = rel @ unit_vec

    ortho = np.linalg.norm(
        rel - np.outer(proj, unit_vec),
        axis=1
    )

    mask = (
        (ortho <= TUBE_RADIUS) &
        (proj >= 0) &
        (proj <= edge_len)
    )

    edge_proj = proj[mask] / edge_len
    support = len(edge_proj)

    if support < 3:
        return 0.0

    edge_proj.sort()

    gaps = np.diff(np.concatenate(([0], edge_proj, [1])))
    continuity_gap = 1.0 - np.max(gaps)

    ref = np.linspace(0, 1, support)
    ks_stat, _ = ks_2samp(edge_proj, ref)
    continuity_ks = 1.0 - ks_stat

    continuity = min(continuity_gap, continuity_ks)
    score = continuity * np.log1p(support)

    return float(score)


edge_scores = {}

for u, v, k in G.edges(keys=True):
    edge_scores[(u, v, k)] = calculate_corridor_score(u, v)

strux_sorted_edges = sorted(
    edge_scores,
    key=edge_scores.get,
    reverse=True
)

top_strux_edges = strux_sorted_edges[:TOP_N]

strux_nodes = []

for u, v, k in top_strux_edges:
    strux_nodes.append(u)
    strux_nodes.append(v)

strux_nodes = list(dict.fromkeys(strux_nodes))

# ------------------------------------------------------------
# 3. Betweenness
# ------------------------------------------------------------

Gu = G.to_undirected()

bet = nx.betweenness_centrality(
    Gu,
    weight="length",
    normalized=True
)

bet_nodes = sorted(
    bet,
    key=bet.get,
    reverse=True
)[:len(strux_nodes)]

# ------------------------------------------------------------
# 4. Overlap
# ------------------------------------------------------------

S = set(strux_nodes)
B = set(bet_nodes)

overlap = S & B
only_strux = S - overlap
only_bet = B - overlap

overlap_ratio = len(overlap) / max(len(S), 1)

print()
print("STRUX nodes:", len(S))
print("Betweenness nodes:", len(B))
print("Overlap:", len(overlap))
print("Overlap ratio:", round(overlap_ratio, 4))

# ------------------------------------------------------------
# 5. Save CSV
# ------------------------------------------------------------

summary = pd.DataFrame([{
    "top_edges": TOP_N,
    "strux_nodes": len(S),
    "betweenness_nodes": len(B),
    "overlap": len(overlap),
    "overlap_ratio": overlap_ratio,
    "only_strux": len(only_strux),
    "only_betweenness": len(only_bet),
}])

csv_path = os.path.join(
    RES,
    "real_florence_overlap_fix_08C.csv"
)

summary.to_csv(csv_path, index=False)

# ------------------------------------------------------------
# 6. Plot
# ------------------------------------------------------------

plt.figure(figsize=(11, 9))

nx.draw_networkx_edges(
    Gu,
    pos,
    alpha=0.05,
    width=0.6
)

nx.draw_networkx_nodes(
    Gu,
    pos,
    nodelist=list(only_strux),
    node_color="red",
    node_size=35,
    label="STRUX only"
)

nx.draw_networkx_nodes(
    Gu,
    pos,
    nodelist=list(only_bet),
    node_color="blue",
    node_size=35,
    label="Betweenness only"
)

nx.draw_networkx_nodes(
    Gu,
    pos,
    nodelist=list(overlap),
    node_color="lime",
    node_size=70,
    label="Overlap"
)

plt.legend()
plt.title("Florence OSM — STRUX vs Betweenness spatial overlap")
plt.axis("off")

fig_path = os.path.join(
    FIG,
    "real_florence_overlap_fix_08C.png"
)

plt.savefig(fig_path, dpi=240, bbox_inches="tight")
plt.close()

print()
print("Saved:")
print(csv_path)
print(fig_path)

print()
if overlap_ratio < 0.2:
    print("VERDICT: STRUX and Betweenness identify mostly different zones")
elif overlap_ratio < 0.5:
    print("VERDICT: partial overlap")
else:
    print("VERDICT: strong overlap")