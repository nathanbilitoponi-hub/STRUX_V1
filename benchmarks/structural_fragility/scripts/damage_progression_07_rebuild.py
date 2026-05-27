"""
MISSION 07 REBUILD

Damage Progression Benchmark

Question:
Does STRUX signal increase before global collapse?

Setup:
- hidden weak lateral corridor
- progressive targeted damage around true weak zone
- compare:
  STRUX signal
  Betweenness signal
  LCC collapse

Interpretation:
PASS if STRUX signal peaks before LCC collapse.
"""

import os
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd


OUT = "benchmarks/structural_fragility/results"
FIG = "benchmarks/structural_fragility/figures"

os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)


def make_network(seed=7):
    rng = np.random.default_rng(seed)

    G = nx.Graph()
    pos = {}

    left = []
    right = []
    weak = []

    for i in range(25):
        n = f"L{i}"
        left.append(n)
        pos[n] = (float(rng.normal(-2, 0.55)), float(rng.normal(0, 0.55)))
        G.add_node(n)

    for i in range(25):
        n = f"R{i}"
        right.append(n)
        pos[n] = (float(rng.normal(2, 0.55)), float(rng.normal(0, 0.55)))
        G.add_node(n)

    for i in range(7):
        n = f"W{i}"
        weak.append(n)
        pos[n] = (
            float(-0.9 + i * 0.3 + rng.normal(0, 0.04)),
            float(1.1 + rng.normal(0, 0.08))
        )
        G.add_node(n)

    # local cluster edges
    nodes = list(G.nodes())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            p1 = np.array(pos[nodes[i]])
            p2 = np.array(pos[nodes[j]])
            d = np.linalg.norm(p1 - p2)

            if d < 0.72:
                G.add_edge(nodes[i], nodes[j])

    # weak chain
    for i in range(len(weak) - 1):
        G.add_edge(weak[i], weak[i + 1], weak_edge=True)

    # attach weak zone
    G.add_edge(left[4], weak[0], weak_edge=True)
    G.add_edge(weak[-1], right[4], weak_edge=True)

    # a few noisy shortcuts
    G.add_edge(left[2], right[2])
    G.add_edge(left[10], right[10])
    G.add_edge(left[15], right[12])

    truth = set(weak)

    return G, pos, truth, weak


def strux_score(G, pos):
    bet = nx.betweenness_centrality(G)
    cl = nx.clustering(G)
    arts = set(nx.articulation_points(G))

    nodes = list(G.nodes())
    coords = np.array([pos[n] for n in nodes])

    density = {}
    for i, n in enumerate(nodes):
        d = np.linalg.norm(coords - coords[i], axis=1)
        density[n] = np.sum(d < 0.7) - 1

    max_bet = max(bet.values()) + 1e-12
    max_density = max(density.values()) + 1e-12

    score = {}

    for n in nodes:
        b = bet[n] / max_bet
        low_cluster = 1.0 - cl[n]
        art = 1.0 if n in arts else 0.0
        sparse = 1.0 - density[n] / max_density

        score[n] = (
            0.15 * b +
            0.35 * low_cluster +
            0.30 * art +
            0.20 * sparse
        )

    return score


def lcc_fraction(G):
    if G.number_of_nodes() == 0:
        return 0.0
    comps = list(nx.connected_components(G))
    return max(len(c) for c in comps) / G.number_of_nodes()


def weak_zone_signal(scores, weak_nodes):
    vals = [scores[n] for n in weak_nodes if n in scores]
    if not vals:
        return 0.0
    return float(np.mean(vals))


def global_signal(scores):
    vals = list(scores.values())
    return float(np.mean(vals))


def damage_step(G, weak_nodes, step):
    """
    Progressive damage:
    remove weak-zone edges gradually,
    then remove one weak node later.
    """

    H = G.copy()

    weak_edges = []

    for u, v in H.edges():
        if u in weak_nodes or v in weak_nodes:
            weak_edges.append((u, v))

    weak_edges = sorted(weak_edges)

    # remove more weak edges as step grows
    n_remove_edges = min(step, len(weak_edges))

    H.remove_edges_from(weak_edges[:n_remove_edges])

    # after enough edge damage, remove weak nodes
    if step >= len(weak_edges) + 2:
        idx = step - len(weak_edges) - 2
        if idx < len(weak_nodes):
            node = weak_nodes[idx]
            if H.has_node(node):
                H.remove_node(node)

    return H


def main():
    G0, pos, truth, weak_nodes = make_network(seed=7)

    rows = []

    max_steps = 18

    base_lcc = lcc_fraction(G0)

    for step in range(max_steps + 1):
        H = damage_step(G0, weak_nodes, step)

        s = strux_score(H, pos)
        b = nx.betweenness_centrality(H)

        row = {
            "step": step,
            "lcc": lcc_fraction(H),
            "lcc_drop": base_lcc - lcc_fraction(H),
            "strux_weak_signal": weak_zone_signal(s, weak_nodes),
            "strux_global_signal": global_signal(s),
            "bet_weak_signal": weak_zone_signal(b, weak_nodes),
            "bet_global_signal": global_signal(b),
            "n_edges": H.number_of_edges(),
            "n_nodes": H.number_of_nodes(),
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    out_csv = os.path.join(OUT, "damage_progression_07_rebuild.csv")
    df.to_csv(out_csv, index=False)

    # normalize for early warning comparison
    def norm(x):
        x = np.asarray(x, dtype=float)
        return (x - x.min()) / (x.max() - x.min() + 1e-12)

    df["strux_norm"] = norm(df["strux_weak_signal"])
    df["bet_norm"] = norm(df["bet_weak_signal"])
    df["collapse_norm"] = norm(df["lcc_drop"])

    # detect first threshold crossing
    threshold = 0.5

    def first_cross(series):
        ids = np.where(np.asarray(series) >= threshold)[0]
        return int(ids[0]) if len(ids) else None

    strux_cross = first_cross(df["strux_norm"])
    bet_cross = first_cross(df["bet_norm"])
    collapse_cross = first_cross(df["collapse_norm"])

    print()
    print("=" * 70)
    print("MISSION 07 REBUILD — DAMAGE PROGRESSION")
    print("=" * 70)

    print("STRUX first signal >= 0.5:", strux_cross)
    print("Betweenness first signal >= 0.5:", bet_cross)
    print("Collapse first >= 0.5:", collapse_cross)

    print()
    print(df[[
        "step",
        "lcc",
        "strux_weak_signal",
        "bet_weak_signal",
        "n_edges",
        "n_nodes"
    ]])

    if strux_cross is not None and collapse_cross is not None and strux_cross < collapse_cross:
        verdict = "PASS — STRUX reacts before collapse"
    elif strux_cross is not None and collapse_cross is not None and strux_cross == collapse_cross:
        verdict = "AMBIGUOUS — STRUX reacts at collapse"
    else:
        verdict = "FAIL — STRUX does not provide early warning"

    print()
    print("VERDICT:", verdict)

    # plot warning curves
    plt.figure(figsize=(9, 5))
    plt.plot(df["step"], df["strux_norm"], "-o", label="STRUX weak-zone signal")
    plt.plot(df["step"], df["bet_norm"], "-o", label="Betweenness weak-zone signal")
    plt.plot(df["step"], df["collapse_norm"], "-o", label="LCC collapse signal")
    plt.axhline(threshold, ls="--")
    plt.xlabel("damage step")
    plt.ylabel("normalized signal")
    plt.title("Mission 07 — early warning vs collapse")
    plt.legend()
    plt.savefig(
        os.path.join(FIG, "damage_progression_07_rebuild_signals.png"),
        dpi=220,
        bbox_inches="tight"
    )
    plt.close()

    # plot initial network
    scores0 = strux_score(G0, pos)

    plt.figure(figsize=(9, 6))
    nx.draw_networkx_edges(G0, pos, alpha=0.25)

    nx.draw_networkx_nodes(
        G0,
        pos,
        nodelist=list(G0.nodes()),
        node_color=[scores0[n] for n in G0.nodes()],
        cmap="magma",
        node_size=100
    )

    nx.draw_networkx_nodes(
        G0,
        pos,
        nodelist=list(truth),
        node_color="none",
        edgecolors="cyan",
        linewidths=2,
        node_size=250
    )

    plt.title("Mission 07 — weak zone and STRUX score")
    plt.axis("off")
    plt.savefig(
        os.path.join(FIG, "damage_progression_07_rebuild_network.png"),
        dpi=220,
        bbox_inches="tight"
    )
    plt.close()

    print()
    print("Saved:")
    print(out_csv)
    print(os.path.join(FIG, "damage_progression_07_rebuild_signals.png"))
    print(os.path.join(FIG, "damage_progression_07_rebuild_network.png"))


if __name__ == "__main__":
    main()