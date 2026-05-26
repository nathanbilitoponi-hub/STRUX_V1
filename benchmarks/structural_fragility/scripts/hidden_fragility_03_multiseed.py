"""
STRUX Mission 03 — Hidden Fragility Multi-Seed Validation

Goal:
Repeat Mission 02 over many random seeds.

Question:
Does STRUX localize hidden fragility better than Betweenness on average?
"""

import os
import random
import numpy as np
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


OUT = "benchmarks/structural_fragility/results"
FIG = "benchmarks/structural_fragility/figures"

os.makedirs(OUT, exist_ok=True)
os.makedirs(FIG, exist_ok=True)


def make_hidden_fragility_network(seed=11):
    rng = np.random.default_rng(seed)

    G = nx.Graph()
    pos = {}

    left, right, central, weak = [], [], [], []

    for i in range(24):
        n = f"L{i}"
        left.append(n)
        pos[n] = (float(rng.normal(-2.2, 0.45)), float(rng.normal(0.0, 0.55)))
        G.add_node(n, zone="left")

    for i in range(24):
        n = f"R{i}"
        right.append(n)
        pos[n] = (float(rng.normal(2.2, 0.45)), float(rng.normal(0.0, 0.55)))
        G.add_node(n, zone="right")

    for i in range(8):
        n = f"C{i}"
        central.append(n)
        pos[n] = (float(-1.4 + i * 0.4), float(rng.normal(0.0, 0.05)))
        G.add_node(n, zone="central")

    for i in range(6):
        n = f"W{i}"
        weak.append(n)
        pos[n] = (float(-0.8 + i * 0.32), float(1.15 + rng.normal(0.0, 0.04)))
        G.add_node(n, zone="weak_lateral")

    for block in [left, right]:
        for i in range(len(block)):
            for j in range(i + 1, len(block)):
                d = np.linalg.norm(np.array(pos[block[i]]) - np.array(pos[block[j]]))
                if d < 0.75:
                    G.add_edge(block[i], block[j])

    for i in range(len(central) - 1):
        G.add_edge(central[i], central[i + 1])

    for u in [left[0], left[1], left[2]]:
        G.add_edge(u, central[0])

    for u in [right[0], right[1], right[2]]:
        G.add_edge(u, central[-1])

    for i in range(len(weak) - 1):
        G.add_edge(weak[i], weak[i + 1])

    G.add_edge(left[7], weak[0])
    G.add_edge(weak[-1], right[7])

    G.add_edge(left[5], central[1])
    G.add_edge(left[6], central[2])
    G.add_edge(right[5], central[-2])
    G.add_edge(right[6], central[-3])

    return G, pos, set(weak)


def strux_score(G, pos):
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


def precision_recall_top(scores, truth, k):
    ranking = sorted(scores, key=scores.get, reverse=True)
    top = set(ranking[:k])
    tp = len(top & truth)
    precision = tp / max(len(top), 1)
    recall = tp / max(len(truth), 1)
    return precision, recall, ranking


def largest_component_fraction(G):
    if G.number_of_nodes() == 0:
        return 0.0
    comps = list(nx.connected_components(G))
    return max(len(c) for c in comps) / G.number_of_nodes()


def attack_final_lcc(G, ranking, nremove=14):
    H = G.copy()
    for node in ranking[:nremove]:
        if H.has_node(node):
            H.remove_node(node)
    return largest_component_fraction(H)


def run(seed):
    G, pos, truth = make_hidden_fragility_network(seed=seed)

    strux = strux_score(G, pos)
    bet = nx.betweenness_centrality(G)

    rng = random.Random(seed)
    random_nodes = list(G.nodes())
    rng.shuffle(random_nodes)

    p_s, r_s, rank_s = precision_recall_top(strux, truth, len(truth))
    p_b, r_b, rank_b = precision_recall_top(bet, truth, len(truth))

    lcc_s = attack_final_lcc(G, rank_s)
    lcc_b = attack_final_lcc(G, rank_b)
    lcc_r = attack_final_lcc(G, random_nodes)

    return {
        "seed": seed,
        "strux_precision": p_s,
        "strux_recall": r_s,
        "bet_precision": p_b,
        "bet_recall": r_b,
        "strux_final_lcc": lcc_s,
        "bet_final_lcc": lcc_b,
        "random_final_lcc": lcc_r,
        "strux_beats_bet_precision": p_s > p_b,
        "strux_equals_bet_precision": p_s == p_b,
    }


def main():
    seeds = list(range(30))
    rows = []

    for seed in seeds:
        print(f"Running seed {seed}...")
        rows.append(run(seed))

    df = pd.DataFrame(rows)

    out_csv = os.path.join(OUT, "hidden_fragility_03_multiseed.csv")
    df.to_csv(out_csv, index=False)

    print()
    print("=" * 70)
    print("STRUX MISSION 03 — MULTI-SEED VALIDATION")
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
    print("Win rate precision:")
    print("STRUX > Betweenness:", round(df["strux_beats_bet_precision"].mean(), 3))
    print("STRUX = Betweenness:", round(df["strux_equals_bet_precision"].mean(), 3))

    print()
    print("Mean final LCC after attack:")
    print("STRUX:", round(df["strux_final_lcc"].mean(), 3))
    print("Betweenness:", round(df["bet_final_lcc"].mean(), 3))
    print("Random:", round(df["random_final_lcc"].mean(), 3))

    # plots
    plt.figure(figsize=(8, 5))
    plt.plot(df["seed"], df["strux_precision"], "-o", label="STRUX")
    plt.plot(df["seed"], df["bet_precision"], "-o", label="Betweenness")
    plt.xlabel("seed")
    plt.ylabel("precision on hidden weak zone")
    plt.title("Mission 03 — localization precision")
    plt.legend()
    plt.savefig(os.path.join(FIG, "hidden_fragility_03_precision.png"), dpi=220, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7, 5))
    means = [
        df["strux_precision"].mean(),
        df["bet_precision"].mean(),
    ]
    plt.bar(["STRUX", "Betweenness"], means)
    plt.ylabel("mean precision")
    plt.title("Mission 03 — mean hidden-fragility localization")
    plt.savefig(os.path.join(FIG, "hidden_fragility_03_mean_precision.png"), dpi=220, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(7, 5))
    means_lcc = [
        df["strux_final_lcc"].mean(),
        df["bet_final_lcc"].mean(),
        df["random_final_lcc"].mean(),
    ]
    plt.bar(["STRUX", "Betweenness", "Random"], means_lcc)
    plt.ylabel("mean final LCC")
    plt.title("Mission 03 — attack impact")
    plt.savefig(os.path.join(FIG, "hidden_fragility_03_lcc.png"), dpi=220, bbox_inches="tight")
    plt.close()

    print()
    print("Saved:")
    print(out_csv)
    print(os.path.join(FIG, "hidden_fragility_03_precision.png"))
    print(os.path.join(FIG, "hidden_fragility_03_mean_precision.png"))
    print(os.path.join(FIG, "hidden_fragility_03_lcc.png"))

    print()
    if df["strux_precision"].mean() > df["bet_precision"].mean():
        print("VERDICT: PASS — STRUX outperforms Betweenness on average")
    elif df["strux_precision"].mean() == df["bet_precision"].mean():
        print("VERDICT: AMBIGUOUS — STRUX equals Betweenness on average")
    else:
        print("VERDICT: FAIL — Betweenness outperforms STRUX")


if __name__ == "__main__":
    main()