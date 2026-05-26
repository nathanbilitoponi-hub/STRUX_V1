"""
MISSION 06

Noisy Hidden Fragility Multi-Seed

Goal:
Test whether STRUX detects hidden fragile zones under noise
better than Betweenness across many random seeds.
"""

import os
import random
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

OUT = "benchmarks/structural_fragility/results"
FIG = "benchmarks/structural_fragility/figures"

os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)


def make_network(seed=7, n_noise_edges=30):
    rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)

    G = nx.Graph()
    pos = {}

    left = []
    right = []
    weak = []

    for i in range(25):
        n = f"L{i}"
        left.append(n)
        pos[n] = (
            float(rng.normal(-2, 0.6)),
            float(rng.normal(0, 0.6))
        )
        G.add_node(n)

    for i in range(25):
        n = f"R{i}"
        right.append(n)
        pos[n] = (
            float(rng.normal(2, 0.6)),
            float(rng.normal(0, 0.6))
        )
        G.add_node(n)

    for i in range(6):
        n = f"W{i}"
        weak.append(n)
        pos[n] = (
            float(-0.7 + i * 0.35 + rng.normal(0, 0.05)),
            float(1.1 + rng.normal(0, 0.15))
        )
        G.add_node(n)

    truth = set(weak)

    nodes = list(G.nodes())

    # local geometric edges
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            p1 = np.array(pos[nodes[i]])
            p2 = np.array(pos[nodes[j]])
            d = np.linalg.norm(p1 - p2)

            if d < 0.7:
                G.add_edge(nodes[i], nodes[j])

    # weak chain
    for i in range(len(weak) - 1):
        G.add_edge(weak[i], weak[i + 1])

    # attach weak zone
    G.add_edge(left[4], weak[0])
    G.add_edge(weak[-1], right[4])

    # random noise edges
    all_nodes = list(G.nodes())

    for _ in range(n_noise_edges):
        a = py_rng.choice(all_nodes)
        b = py_rng.choice(all_nodes)

        if a != b:
            G.add_edge(a, b)

    return G, pos, truth


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


def betweenness_score(G):
    return nx.betweenness_centrality(G)


def precision_recall(scores, truth, k):
    rank = sorted(scores, key=scores.get, reverse=True)
    top = set(rank[:k])

    tp = len(top & truth)

    precision = tp / max(k, 1)
    recall = tp / max(len(truth), 1)

    return precision, recall, rank


def largest_component_fraction(G):
    if G.number_of_nodes() == 0:
        return 0.0

    comps = list(nx.connected_components(G))
    return max(len(c) for c in comps) / G.number_of_nodes()


def attack_final_lcc(G, ranking, nremove=12):
    H = G.copy()

    for node in ranking[:nremove]:
        if H.has_node(node):
            H.remove_node(node)

    return largest_component_fraction(H)


def run_one(seed, noise_edges=30):
    G, pos, truth = make_network(seed=seed, n_noise_edges=noise_edges)

    s_score = strux_score(G, pos)
    b_score = betweenness_score(G)

    p_s, r_s, rank_s = precision_recall(s_score, truth, len(truth))
    p_b, r_b, rank_b = precision_recall(b_score, truth, len(truth))

    py_rng = random.Random(seed)
    random_rank = list(G.nodes())
    py_rng.shuffle(random_rank)

    lcc_s = attack_final_lcc(G, rank_s)
    lcc_b = attack_final_lcc(G, rank_b)
    lcc_r = attack_final_lcc(G, random_rank)

    return {
        "seed": seed,
        "noise_edges": noise_edges,
        "strux_precision": p_s,
        "strux_recall": r_s,
        "bet_precision": p_b,
        "bet_recall": r_b,
        "strux_final_lcc": lcc_s,
        "bet_final_lcc": lcc_b,
        "random_final_lcc": lcc_r,
        "strux_beats_bet": p_s > p_b,
        "strux_equals_bet": p_s == p_b,
    }


def main():
    seeds = list(range(40))
    noise_edges = 30

    rows = []

    for seed in seeds:
        print(f"Running seed {seed}...")
        rows.append(run_one(seed, noise_edges=noise_edges))

    df = pd.DataFrame(rows)

    out_csv = os.path.join(OUT, "noisy_hidden_fragility_06_multiseed.csv")
    df.to_csv(out_csv, index=False)

    print()
    print("=" * 70)
    print("MISSION 06 — NOISY HIDDEN FRAGILITY MULTI-SEED")
    print("=" * 70)

    print()
    print("Mean precision:")
    print("STRUX:", round(df["strux_precision"].mean(), 3))
    print("Betweenness:", round(df["bet_precision"].mean(), 3))

    print()
    print("Mean recall:")
    print("STRUX:", round(df["strux_recall"].mean(), 3))
    print("Betweenness:", round(df["bet_recall"].mean(), 3))

    print()
    print("Win rate:")
    print("STRUX > Betweenness:", round(df["strux_beats_bet"].mean(), 3))
    print("STRUX = Betweenness:", round(df["strux_equals_bet"].mean(), 3))

    print()
    print("Mean final LCC after attack:")
    print("STRUX:", round(df["strux_final_lcc"].mean(), 3))
    print("Betweenness:", round(df["bet_final_lcc"].mean(), 3))
    print("Random:", round(df["random_final_lcc"].mean(), 3))

    # plots
    plt.figure(figsize=(9, 5))
    plt.plot(df["seed"], df["strux_precision"], "-o", label="STRUX")
    plt.plot(df["seed"], df["bet_precision"], "-o", label="Betweenness")
    plt.xlabel("seed")
    plt.ylabel("precision")
    plt.title("Mission 06 — hidden fragility under noise")
    plt.legend()
    plt.savefig(os.path.join(FIG, "noisy_hidden_fragility_06_precision.png"), dpi=220, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.bar(
        ["STRUX", "Betweenness"],
        [df["strux_precision"].mean(), df["bet_precision"].mean()]
    )
    plt.ylabel("mean precision")
    plt.title("Mission 06 — mean localization precision")
    plt.savefig(os.path.join(FIG, "noisy_hidden_fragility_06_mean_precision.png"), dpi=220, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.bar(
        ["STRUX", "Betweenness", "Random"],
        [
            df["strux_final_lcc"].mean(),
            df["bet_final_lcc"].mean(),
            df["random_final_lcc"].mean()
        ]
    )
    plt.ylabel("mean final LCC")
    plt.title("Mission 06 — attack impact")
    plt.savefig(os.path.join(FIG, "noisy_hidden_fragility_06_lcc.png"), dpi=220, bbox_inches="tight")
    plt.close()

    print()
    print("Saved:")
    print(out_csv)
    print(os.path.join(FIG, "noisy_hidden_fragility_06_precision.png"))
    print(os.path.join(FIG, "noisy_hidden_fragility_06_mean_precision.png"))
    print(os.path.join(FIG, "noisy_hidden_fragility_06_lcc.png"))

    print()
    if df["strux_precision"].mean() > df["bet_precision"].mean():
        print("VERDICT: PASS — STRUX outperforms Betweenness under noise")
    elif df["strux_precision"].mean() == df["bet_precision"].mean():
        print("VERDICT: AMBIGUOUS — STRUX equals Betweenness under noise")
    else:
        print("VERDICT: FAIL — Betweenness outperforms STRUX under noise")


if __name__ == "__main__":
    main()