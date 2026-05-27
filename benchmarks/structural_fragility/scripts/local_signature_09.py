"""
MISSION 09 — Local Structural Signature

Question:
STRUX and Betweenness select different nodes in Florence.
But what structural properties do they select?

Compare local signatures of:

- STRUX nodes
- Betweenness nodes
- Random nodes

Metrics:
- degree
- clustering
- local density
- local redundancy
- bridge/articulation proximity
- mean incident edge length

Goal:
Define what STRUX is actually measuring.
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
TOP_N_EDGES = 40

print("=" * 70)
print("MISSION 09 — LOCAL STRUCTURAL SIGNATURE")
print("=" * 70)

# ------------------------------------------------------------
# Load graph once
# ------------------------------------------------------------

G = ox.graph_from_point(
    CENTER,
    dist=DIST,
    network_type=NETWORK_TYPE,
    simplify=True
)

G = ox.project_graph(G)
# Convert projected OSM MultiDiGraph to simple undirected Graph
Gu_multi = G.to_undirected()

Gu = nx.Graph()
for u, v, data in Gu_multi.edges(data=True):
    length = float(data.get("length", 1.0))
    if Gu.has_edge(u, v):
        if length < Gu[u][v].get("length", 1.0):
            Gu[u][v]["length"] = length
    else:
        Gu.add_edge(u, v, length=length)

for n, data in G.nodes(data=True):
    Gu.add_node(n, **data)

print("Nodes:", Gu.number_of_nodes())
print("Edges:", Gu.number_of_edges())

nodes_df, _ = ox.graph_to_gdfs(G)

node_coords = nodes_df[["x", "y"]].to_numpy()
node_ids = nodes_df.index.tolist()
node_id_to_idx = {nid: i for i, nid in enumerate(node_ids)}

pos = {
    n: (float(data["x"]), float(data["y"]))
    for n, data in Gu.nodes(data=True)
}

# ------------------------------------------------------------
# STRUX corridor score
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

    return float(continuity * np.log1p(support))


edge_scores = {}

for u, v, k in G.edges(keys=True):
    edge_scores[(u, v, k)] = calculate_corridor_score(u, v)

top_edges = sorted(
    edge_scores,
    key=edge_scores.get,
    reverse=True
)[:TOP_N_EDGES]

strux_nodes = []

for u, v, k in top_edges:
    strux_nodes.append(u)
    strux_nodes.append(v)

strux_nodes = list(dict.fromkeys(strux_nodes))

# ------------------------------------------------------------
# Betweenness nodes
# ------------------------------------------------------------

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
# Random nodes
# ------------------------------------------------------------

rng = np.random.default_rng(7)
all_nodes = list(Gu.nodes())
random_nodes = list(rng.choice(all_nodes, size=len(strux_nodes), replace=False))

# ------------------------------------------------------------
# Local signature metrics
# ------------------------------------------------------------

clustering = nx.clustering(Gu)
degree = dict(Gu.degree())
articulations = set(nx.articulation_points(Gu))

coords = np.array([pos[n] for n in all_nodes])
node_to_i = {n: i for i, n in enumerate(all_nodes)}

def local_density(n, radius=120):
    i = node_to_i[n]
    d = np.linalg.norm(coords - coords[i], axis=1)
    return int(np.sum(d < radius) - 1)

def mean_edge_length(n):
    lengths = []
    for nbr in Gu.neighbors(n):
        data = Gu.get_edge_data(n, nbr)
        if isinstance(data, dict):
            vals = list(data.values()) if all(isinstance(v, dict) for v in data.values()) else [data]
            for item in vals:
                if isinstance(item, dict) and "length" in item:
                    lengths.append(float(item["length"]))
        else:
            pass
    if len(lengths) == 0:
        return np.nan
    return float(np.mean(lengths))

def redundancy_score(n):
    """
    Local redundancy proxy:
    clustering + degree-normalized neighbor interconnection.
    Higher = more locally redundant.
    """
    return float(clustering.get(n, 0.0))

def signature_for_group(name, nodes):
    rows = []

    for n in nodes:
        if n not in Gu:
            continue

        rows.append({
            "group": name,
            "node": n,
            "degree": degree.get(n, 0),
            "clustering": clustering.get(n, 0.0),
            "local_density": local_density(n),
            "redundancy": redundancy_score(n),
            "is_articulation": 1 if n in articulations else 0,
            "betweenness": bet.get(n, 0.0),
            "mean_edge_length": mean_edge_length(n),
        })

    return rows


rows = []
rows += signature_for_group("STRUX", strux_nodes)
rows += signature_for_group("Betweenness", bet_nodes)
rows += signature_for_group("Random", random_nodes)

sig = pd.DataFrame(rows)

out_csv = os.path.join(
    RES,
    "local_signature_09.csv"
)

sig.to_csv(out_csv, index=False)

summary = sig.groupby("group").agg({
    "degree": ["mean", "std"],
    "clustering": ["mean", "std"],
    "local_density": ["mean", "std"],
    "redundancy": ["mean", "std"],
    "is_articulation": ["mean"],
    "betweenness": ["mean", "std"],
    "mean_edge_length": ["mean", "std"],
})

summary_path = os.path.join(
    RES,
    "local_signature_09_summary.csv"
)

summary.to_csv(summary_path)

print()
print("Group sizes:")
print(sig.groupby("group").size())

print()
print("Summary:")
print(summary)

# ------------------------------------------------------------
# Plots
# ------------------------------------------------------------

metrics = [
    "degree",
    "clustering",
    "local_density",
    "redundancy",
    "is_articulation",
    "betweenness",
    "mean_edge_length",
]

for metric in metrics:
    plt.figure(figsize=(7, 5))

    means = sig.groupby("group")[metric].mean()
    stds = sig.groupby("group")[metric].std()

    order = ["STRUX", "Betweenness", "Random"]
    vals = [means.get(g, np.nan) for g in order]
    errs = [stds.get(g, 0.0) for g in order]

    plt.bar(order, vals, yerr=errs, capsize=5)
    plt.ylabel(metric)
    plt.title(f"Mission 09 — {metric}")

    path = os.path.join(
        FIG,
        f"local_signature_09_{metric}.png"
    )

    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()

# ------------------------------------------------------------
# Compact multi-panel style summary
# ------------------------------------------------------------

selected = [
    "degree",
    "clustering",
    "local_density",
    "betweenness",
    "mean_edge_length",
]

fig, axes = plt.subplots(1, len(selected), figsize=(18, 4))

for ax, metric in zip(axes, selected):
    means = sig.groupby("group")[metric].mean()
    order = ["STRUX", "Betweenness", "Random"]
    vals = [means.get(g, np.nan) for g in order]

    ax.bar(order, vals)
    ax.set_title(metric)
    ax.tick_params(axis="x", rotation=30)

plt.tight_layout()

panel_path = os.path.join(
    FIG,
    "local_signature_09_panel.png"
)

plt.savefig(panel_path, dpi=240, bbox_inches="tight")
plt.close()

# ------------------------------------------------------------
# Verdict
# ------------------------------------------------------------

s_mean_bet = sig[sig.group == "STRUX"]["betweenness"].mean()
b_mean_bet = sig[sig.group == "Betweenness"]["betweenness"].mean()

s_clust = sig[sig.group == "STRUX"]["clustering"].mean()
b_clust = sig[sig.group == "Betweenness"]["clustering"].mean()

s_density = sig[sig.group == "STRUX"]["local_density"].mean()
b_density = sig[sig.group == "Betweenness"]["local_density"].mean()

print()
print("=" * 70)
print("MISSION 09 VERDICT")
print("=" * 70)

print("STRUX mean betweenness:", round(s_mean_bet, 6))
print("Betweenness mean betweenness:", round(b_mean_bet, 6))
print("STRUX mean clustering:", round(s_clust, 4))
print("Betweenness mean clustering:", round(b_clust, 4))
print("STRUX mean local density:", round(s_density, 2))
print("Betweenness mean local density:", round(b_density, 2))

print()
if s_mean_bet < b_mean_bet and abs(s_clust - b_clust) > 0.01:
    print("VERDICT: STRUX selects a structurally distinct local signature.")
else:
    print("VERDICT: Signature difference weak or ambiguous.")

print()
print("Saved:")
print(out_csv)
print(summary_path)
print(panel_path)