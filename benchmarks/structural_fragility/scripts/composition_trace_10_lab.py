"""
STRUX Composition Trace LAB

Goal:
not only output a score,
but trace how STRUX composes it.

Stages:
1. input graph
2. geometry
3. corridor support
4. local redundancy
5. centrality
6. final composition
"""

import os
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

OUT = "benchmarks/structural_fragility/results"
FIG = "benchmarks/structural_fragility/figures"

os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)


def make_test_graph(seed=7):
    rng = np.random.default_rng(seed)
    G = nx.Graph()
    pos = {}

    left, right, weak = [], [], []

    for i in range(25):
        n = f"L{i}"
        left.append(n)
        pos[n] = (float(rng.normal(-2, .55)), float(rng.normal(0, .55)))
        G.add_node(n)

    for i in range(25):
        n = f"R{i}"
        right.append(n)
        pos[n] = (float(rng.normal(2, .55)), float(rng.normal(0, .55)))
        G.add_node(n)

    for i in range(6):
        n = f"W{i}"
        weak.append(n)
        pos[n] = (float(-.7 + i*.35), float(1.1 + rng.normal(0, .08)))
        G.add_node(n)

    nodes = list(G.nodes())

    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            d = np.linalg.norm(np.array(pos[nodes[i]]) - np.array(pos[nodes[j]]))
            if d < .7:
                G.add_edge(nodes[i], nodes[j])

    for i in range(len(weak)-1):
        G.add_edge(weak[i], weak[i+1])

    G.add_edge(left[4], weak[0])
    G.add_edge(weak[-1], right[4])

    return G, pos, set(weak)


def normalize(d):
    vals = np.array(list(d.values()), dtype=float)
    mn, mx = vals.min(), vals.max()
    return {k: (v-mn)/(mx-mn+1e-12) for k, v in d.items()}


G, pos, truth = make_test_graph()

nodes = list(G.nodes())
coords = np.array([pos[n] for n in nodes])

# ============================================================
# STAGE 1 — GEOMETRY / SPARSITY
# ============================================================

density = {}

for i, n in enumerate(nodes):
    d = np.linalg.norm(coords - coords[i], axis=1)
    density[n] = np.sum(d < .7) - 1

sparsity = normalize({n: -density[n] for n in nodes})

# ============================================================
# STAGE 2 — LOCAL REDUNDANCY
# ============================================================

clustering = nx.clustering(G)
low_redundancy = normalize({n: 1 - clustering[n] for n in nodes})

# ============================================================
# STAGE 3 — ARTICULATION / STRUCTURAL CUT
# ============================================================

arts = set(nx.articulation_points(G))
cut_role = {n: 1.0 if n in arts else 0.0 for n in nodes}

# ============================================================
# STAGE 4 — FLOW CENTRALITY
# ============================================================

bet = nx.betweenness_centrality(G)
flow = normalize(bet)

# ============================================================
# STAGE 5 — COMPOSITION
# ============================================================

weights = {
    "sparsity": 0.25,
    "low_redundancy": 0.30,
    "cut_role": 0.25,
    "flow": 0.20,
}

final = {}

for n in nodes:
    final[n] = (
        weights["sparsity"] * sparsity[n] +
        weights["low_redundancy"] * low_redundancy[n] +
        weights["cut_role"] * cut_role[n] +
        weights["flow"] * flow[n]
    )

rank = sorted(final, key=final.get, reverse=True)

# ============================================================
# TRACE TABLE
# ============================================================

rows = []

for n in rank:
    rows.append({
        "node": n,
        "is_truth": int(n in truth),
        "density_raw": density[n],
        "sparsity_component": sparsity[n],
        "clustering_raw": clustering[n],
        "low_redundancy_component": low_redundancy[n],
        "cut_role_component": cut_role[n],
        "flow_component": flow[n],
        "final_score": final[n],
    })

trace = pd.DataFrame(rows)

trace_path = os.path.join(OUT, "composition_trace_10_lab.csv")
trace.to_csv(trace_path, index=False)

print()
print("="*70)
print("STRUX COMPOSITION TRACE LAB")
print("="*70)

print()
print("Top 12 composed nodes:")
print(trace.head(12).to_string(index=False))

print()
print("Ground truth weak nodes:")
print(sorted(truth))

print()
print("Component weights:")
for k, v in weights.items():
    print(k, "=", v)

# ============================================================
# STAGE SUMMARY
# ============================================================

summary = []

for stage in ["sparsity_component", "low_redundancy_component", "cut_role_component", "flow_component", "final_score"]:
    truth_mean = trace[trace.is_truth == 1][stage].mean()
    other_mean = trace[trace.is_truth == 0][stage].mean()

    summary.append({
        "stage": stage,
        "truth_mean": truth_mean,
        "other_mean": other_mean,
        "contrast_truth_minus_other": truth_mean - other_mean
    })

summary = pd.DataFrame(summary)

summary_path = os.path.join(OUT, "composition_trace_10_lab_summary.csv")
summary.to_csv(summary_path, index=False)

print()
print("Stage contrast:")
print(summary.to_string(index=False))

# ============================================================
# FIGURE
# ============================================================

plt.figure(figsize=(9, 6))

scores = np.array([final[n] for n in G.nodes()])

nx.draw_networkx_edges(G, pos, alpha=.25)

nx.draw_networkx_nodes(
    G, pos,
    nodelist=list(G.nodes()),
    node_color=scores,
    cmap="magma",
    node_size=110
)

nx.draw_networkx_nodes(
    G, pos,
    nodelist=list(truth),
    node_color="none",
    edgecolors="cyan",
    linewidths=2,
    node_size=260
)

plt.title("STRUX Composition Trace — final composed score")
plt.axis("off")

fig_path = os.path.join(FIG, "composition_trace_10_lab.png")
plt.savefig(fig_path, dpi=220, bbox_inches="tight")
plt.close()

print()
print("Saved:")
print(trace_path)
print(summary_path)
print(fig_path)