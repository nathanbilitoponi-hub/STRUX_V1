import os
import random
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

OUT = "benchmarks/structural_fragility/results"
FIG = "benchmarks/structural_fragility/figures"

os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)


def make_bridge_network(seed=7):
    rng = np.random.default_rng(seed)

    G = nx.Graph()
    pos = {}

    left = []
    right = []
    bridge = []

    for i in range(20):
        n = f"L{i}"
        left.append(n)
        pos[n] = (float(rng.normal(-2, 0.5)), float(rng.normal(0, 0.5)))
        G.add_node(n)

    for i in range(20):
        n = f"R{i}"
        right.append(n)
        pos[n] = (float(rng.normal(2, 0.5)), float(rng.normal(0, 0.5)))
        G.add_node(n)

    for i in range(7):
        n = f"B{i}"
        bridge.append(n)
        pos[n] = (float(-1.2 + i * 0.4), float(rng.normal(0, 0.05)))
        G.add_node(n)

    for block in [left, right]:
        for i in range(len(block)):
            for j in range(i + 1, len(block)):
                p1 = np.array(pos[block[i]])
                p2 = np.array(pos[block[j]])
                d = np.linalg.norm(p1 - p2)
                if d < 0.8:
                    G.add_edge(block[i], block[j])

    for i in range(len(bridge) - 1):
        G.add_edge(bridge[i], bridge[i + 1])

    G.add_edge(left[0], bridge[0])
    G.add_edge(left[1], bridge[0])
    G.add_edge(right[0], bridge[-1])
    G.add_edge(right[1], bridge[-1])

    truth = set(bridge)
    return G, pos, truth


def strux_score(G):
    bet = nx.betweenness_centrality(G)
    clustering = nx.clustering(G)
    arts = set(nx.articulation_points(G))

    score = {}

    for n in G.nodes():
        b = bet[n]
        c = 1.0 - clustering[n]
        a = 1.0 if n in arts else 0.0
        score[n] = 0.4 * b + 0.4 * c + 0.2 * a

    return score


def largest_component_fraction(G):
    if G.number_of_nodes() == 0:
        return 0.0
    comps = list(nx.connected_components(G))
    return max(len(c) for c in comps) / G.number_of_nodes()


def attack_curve(G, ranking, nremove=12):
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


def main():
    G, pos, truth = make_bridge_network(seed=7)

    strux = strux_score(G)
    bet = nx.betweenness_centrality(G)

    rng = random.Random(7)
    random_nodes = list(G.nodes())
    rng.shuffle(random_nodes)

    p_s, r_s, rank_strux = precision_recall_top(strux, truth, len(truth))
    p_b, r_b, rank_bet = precision_recall_top(bet, truth, len(truth))

    x1, y1 = attack_curve(G, rank_strux)
    x2, y2 = attack_curve(G, rank_bet)
    x3, y3 = attack_curve(G, random_nodes)

    print()
    print("=" * 60)
    print("STRUX MISSION 01 — CONTROLLED DEGENERATION")
    print("=" * 60)
    print("Ground truth bridge nodes:", sorted(truth))
    print()
    print("STRUX top nodes:", rank_strux[:10])
    print("Betweenness top nodes:", rank_bet[:10])
    print()
    print("STRUX precision:", round(p_s, 3), "recall:", round(r_s, 3))
    print("Betweenness precision:", round(p_b, 3), "recall:", round(r_b, 3))
    print()
    print("Final LCC:")
    print("STRUX:", round(y1[-1], 3))
    print("Betweenness:", round(y2[-1], 3))
    print("Random:", round(y3[-1], 3))

    with open(os.path.join(OUT, "controlled_degeneration_01_summary.csv"), "w", encoding="utf-8") as f:
        f.write("method,precision,recall,final_lcc\n")
        f.write(f"STRUX,{p_s},{r_s},{y1[-1]}\n")
        f.write(f"Betweenness,{p_b},{r_b},{y2[-1]}\n")
        f.write(f"Random,,,{y3[-1]}\n")

    plt.figure(figsize=(8, 6))

    node_scores = np.array([strux[n] for n in G.nodes()])

    nx.draw_networkx_edges(G, pos, alpha=0.3)
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=list(G.nodes()),
        node_color=node_scores,
        cmap="magma",
        node_size=120
    )

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=list(truth),
        node_color="none",
        edgecolors="cyan",
        linewidths=2,
        node_size=250
    )

    plt.title("STRUX fragility score")
    plt.axis("off")
    plt.savefig(os.path.join(FIG, "controlled_degeneration_01_network.png"), dpi=220, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.plot(x1, y1, "-o", label="STRUX")
    plt.plot(x2, y2, "-o", label="Betweenness")
    plt.plot(x3, y3, "-o", label="Random")
    plt.xlabel("Removed nodes")
    plt.ylabel("Largest connected component")
    plt.title("Progressive failure curve")
    plt.legend()
    plt.savefig(os.path.join(FIG, "controlled_degeneration_01_lcc.png"), dpi=220, bbox_inches="tight")
    plt.close()

    print()
    print("Saved:")
    print(os.path.join(OUT, "controlled_degeneration_01_summary.csv"))
    print(os.path.join(FIG, "controlled_degeneration_01_network.png"))
    print(os.path.join(FIG, "controlled_degeneration_01_lcc.png"))


if __name__ == "__main__":
    main()
