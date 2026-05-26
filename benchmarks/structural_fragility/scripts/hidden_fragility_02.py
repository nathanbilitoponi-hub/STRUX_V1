"""
STRUX Mission 02 — Hidden Fragility Benchmark

Goal:
Create a network where the obvious central bridge is NOT the only important
structural weakness.

Question:
Can STRUX detect a lateral geometric fragility that betweenness tends to miss?

Interpretation:
- Mission 01 was a sanity check: STRUX = Betweenness on obvious bridge.
- Mission 02 tests whether STRUX can identify non-central geometric fragility.
"""

import os
import random
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


OUT = "benchmarks/structural_fragility/results"
FIG = "benchmarks/structural_fragility/figures"

os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)


def make_hidden_fragility_network(seed=11):
    rng = np.random.default_rng(seed)

    G = nx.Graph()
    pos = {}

    left = []
    right = []
    central = []
    weak = []

    # left cluster
    for i in range(24):
        n = f"L{i}"
        left.append(n)
        pos[n] = (
            float(rng.normal(-2.2, 0.45)),
            float(rng.normal(0.0, 0.55))
        )
        G.add_node(n, zone="left")

    # right cluster
    for i in range(24):
        n = f"R{i}"
        right.append(n)
        pos[n] = (
            float(rng.normal(2.2, 0.45)),
            float(rng.normal(0.0, 0.55))
        )
        G.add_node(n, zone="right")

    # central obvious corridor
    for i in range(8):
        n = f"C{i}"
        central.append(n)
        pos[n] = (
            float(-1.4 + i * 0.4),
            float(rng.normal(0.0, 0.05))
        )
        G.add_node(n, zone="central")

    # hidden lateral fragile branch
    # geometrically thin, low redundancy, not globally central
    for i in range(6):
        n = f"W{i}"
        weak.append(n)
        pos[n] = (
            float(-0.8 + i * 0.32),
            float(1.15 + rng.normal(0.0, 0.04))
        )
        G.add_node(n, zone="weak_lateral")

    # dense local cluster edges
    for block in [left, right]:
        for i in range(len(block)):
            for j in range(i + 1, len(block)):
                d = np.linalg.norm(np.array(pos[block[i]]) - np.array(pos[block[j]]))
                if d < 0.75:
                    G.add_edge(block[i], block[j])

    # central corridor chain
    for i in range(len(central) - 1):
        G.add_edge(central[i], central[i + 1])

    # connect central corridor strongly to both clusters
    for u in [left[0], left[1], left[2]]:
        G.add_edge(u, central[0])

    for u in [right[0], right[1], right[2]]:
        G.add_edge(u, central[-1])

    # lateral weak branch chain
    for i in range(len(weak) - 1):
        G.add_edge(weak[i], weak[i + 1])

    # weak branch attached at two sparse points
    G.add_edge(left[7], weak[0])
    G.add_edge(weak[-1], right[7])

    # add a few edges around central corridor to make it less trivially fragile
    G.add_edge(left[5], central[1])
    G.add_edge(left[6], central[2])
    G.add_edge(right[5], central[-2])
    G.add_edge(right[6], central[-3])

    # weak branch is ground-truth hidden fragility
    truth = set(weak)

    return G, pos, truth


def strux_score(G, pos):
    """
    STRUX proxy for hidden fragility:
    - betweenness component
    - low local clustering
    - articulation-like weakness
    - geometric thinness / sparse spatial support
    """

    bet = nx.betweenness_centrality(G)
    clustering = nx.clustering(G)
    arts = set(nx.articulation_points(G))

    nodes = list(G.nodes())
    coords = np.array([pos[n] for n in nodes])

    density = {}
    for i, n in enumerate(nodes):
        d = np.linalg.norm(coords - coords[i], axis=1)
        density[n] = np.sum(d < 0.65) - 1

    max_b = max(bet.values()) + 1e-12
    max_density = max(density.values()) + 1e-12

    score = {}

    for n in nodes:
        b = bet[n] / max_b
        low_cluster = 1.0 - clustering[n]
        art = 1.0 if n in arts else 0.0
        sparse = 1.0 - density[n] / max_density

        score[n] = (
            0.20 * b +
            0.30 * low_cluster +
            0.25 * art +
            0.25 * sparse
        )

    return score


def largest_component_fraction(G):
    if G.number_of_nodes() == 0:
        return 0.0

    comps = list(nx.connected_components(G))
    return max(len(c) for c in comps) / G.number_of_nodes()


def attack_curve(G, ranking, nremove=14):
    H = G.copy()
    xs = [0]
    ys = [largest_component_fraction(H)]

    for i, node in enumerate(ranking[:nremove]):
        if H.has_node(node):
            H.remove_node(node)

        xs.append(i + 1)
        ys.append(largest_component_fraction(H))

    return xs, ys


def precision_recall_top(scores, truth, k):
    ranking = sorted(scores, key=scores.get, reverse=True)
    top = set(ranking[:k])
    tp = len(top & truth)

    precision = tp / max(len(top), 1)
    recall = tp / max(len(truth), 1)

    return precision, recall, ranking


def save_score_network(G, pos, truth, scores, path, title):
    plt.figure(figsize=(9, 6))

    node_scores = np.array([scores[n] for n in G.nodes()])

    nx.draw_networkx_edges(G, pos, alpha=0.25)

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=list(G.nodes()),
        node_color=node_scores,
        cmap="magma",
        node_size=110
    )

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=list(truth),
        node_color="none",
        edgecolors="cyan",
        linewidths=2,
        node_size=260
    )

    plt.title(title)
    plt.axis("off")
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()


def main():
    G, pos, truth = make_hidden_fragility_network(seed=11)

    strux = strux_score(G, pos)
    bet = nx.betweenness_centrality(G)

    rng = random.Random(11)
    random_nodes = list(G.nodes())
    rng.shuffle(random_nodes)

    p_s, r_s, rank_strux = precision_recall_top(strux, truth, len(truth))
    p_b, r_b, rank_bet = precision_recall_top(bet, truth, len(truth))

    x1, y1 = attack_curve(G, rank_strux)
    x2, y2 = attack_curve(G, rank_bet)
    x3, y3 = attack_curve(G, random_nodes)

    final_s = y1[-1]
    final_b = y2[-1]
    final_r = y3[-1]

    print()
    print("=" * 70)
    print("STRUX MISSION 02 — HIDDEN FRAGILITY")
    print("=" * 70)
    print("Ground truth hidden weak nodes:", sorted(truth))
    print()
    print("STRUX top nodes:", rank_strux[:12])
    print("Betweenness top nodes:", rank_bet[:12])
    print()
    print("STRUX precision:", round(p_s, 3), "recall:", round(r_s, 3))
    print("Betweenness precision:", round(p_b, 3), "recall:", round(r_b, 3))
    print()
    print("Final LCC after attack:")
    print("STRUX:", round(final_s, 3))
    print("Betweenness:", round(final_b, 3))
    print("Random:", round(final_r, 3))

    with open(os.path.join(OUT, "hidden_fragility_02_summary.csv"), "w", encoding="utf-8") as f:
        f.write("method,precision,recall,final_lcc\n")
        f.write(f"STRUX,{p_s},{r_s},{final_s}\n")
        f.write(f"Betweenness,{p_b},{r_b},{final_b}\n")
        f.write(f"Random,,,{final_r}\n")

    save_score_network(
        G,
        pos,
        truth,
        strux,
        os.path.join(FIG, "hidden_fragility_02_strux.png"),
        "STRUX score — hidden fragility"
    )

    save_score_network(
        G,
        pos,
        truth,
        bet,
        os.path.join(FIG, "hidden_fragility_02_betweenness.png"),
        "Betweenness score — hidden fragility"
    )

    plt.figure(figsize=(8, 5))
    plt.plot(x1, y1, "-o", label="STRUX")
    plt.plot(x2, y2, "-o", label="Betweenness")
    plt.plot(x3, y3, "-o", label="Random")
    plt.xlabel("Removed nodes")
    plt.ylabel("Largest connected component")
    plt.title("Mission 02 — progressive failure")
    plt.legend()
    plt.savefig(os.path.join(FIG, "hidden_fragility_02_lcc.png"), dpi=220, bbox_inches="tight")
    plt.close()

    print()
    print("Saved:")
    print(os.path.join(OUT, "hidden_fragility_02_summary.csv"))
    print(os.path.join(FIG, "hidden_fragility_02_strux.png"))
    print(os.path.join(FIG, "hidden_fragility_02_betweenness.png"))
    print(os.path.join(FIG, "hidden_fragility_02_lcc.png"))

    print()
    if p_s > p_b:
        print("VERDICT: PASS — STRUX localizes hidden fragility better than betweenness")
    elif p_s == p_b:
        print("VERDICT: AMBIGUOUS — STRUX equals betweenness")
    else:
        print("VERDICT: FAIL — betweenness localizes hidden fragility better")


if __name__ == "__main__":
    main()