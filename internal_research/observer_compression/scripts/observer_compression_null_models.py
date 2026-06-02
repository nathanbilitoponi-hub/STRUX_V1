import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path


OUTDIR = Path("internal_research/observer_compression/results")
FIGDIR = Path("internal_research/observer_compression/figures")
OUTDIR.mkdir(parents=True, exist_ok=True)
FIGDIR.mkdir(parents=True, exist_ok=True)


def largest_component(G):
    if nx.is_connected(G):
        return G.copy()
    nodes = max(nx.connected_components(G), key=len)
    H = G.subgraph(nodes).copy()
    return nx.convert_node_labels_to_integers(H)


def strux_score(G, seed=42, k_betweenness=200):
    bc = nx.betweenness_centrality(
        G,
        k=min(k_betweenness, G.number_of_nodes()),
        normalized=True,
        seed=seed,
    )

    score = {}

    for n in G.nodes():
        neigh = list(G.neighbors(n))

        if len(neigh) == 0:
            score[n] = 0.0
            continue

        links = 0
        for i, a in enumerate(neigh):
            for b in neigh[i + 1:]:
                if G.has_edge(a, b):
                    links += 1

        redundancy = links / (len(neigh) + 1e-12)
        score[n] = bc[n] / (1.0 + redundancy)

    return score


def observer_peak_level(G, score, obs, cutoff=12):
    d0 = nx.single_source_shortest_path_length(G, obs, cutoff=cutoff)
    reach = list(d0.keys())

    if len(reach) < 30:
        return np.nan

    A = max(reach, key=lambda n: d0[n])
    dA = nx.single_source_shortest_path_length(G, A)

    B = max(dA.keys(), key=lambda n: dA[n])
    dB = nx.single_source_shortest_path_length(G, B)

    levels = {}

    for n, d in d0.items():
        if d == 0:
            continue

        sign = 1 if dB.get(n, 999999) < dA.get(n, 999999) else -1
        level = sign * (d - 0.5)
        levels.setdefault(level, []).append(n)

    xs = []
    ys = []

    for level, nodes in levels.items():
        xs.append(level)
        ys.append(np.mean([score[n] for n in nodes]))

    if len(xs) == 0:
        return np.nan

    xs = np.array(xs)
    ys = np.array(ys)

    return xs[np.argmax(ys)]


def run_model(name, G, seed=42, n_random=100):
    G = largest_component(G)

    score = strux_score(G, seed=seed)

    strux_obs = max(score, key=score.get)
    strux_peak = observer_peak_level(G, score, strux_obs)

    rng = np.random.default_rng(seed)
    nodes = list(G.nodes())

    peaks = []

    for obs in rng.choice(nodes, size=min(n_random, len(nodes)), replace=False):
        p = observer_peak_level(G, score, int(obs))
        if np.isfinite(p):
            peaks.append(p)

    peaks = np.array(peaks)

    abs_strux = abs(strux_peak)
    if abs_strux == 0:
        abs_strux = 0.5

    median_abs = np.median(np.abs(peaks))
    mean_abs = np.mean(np.abs(peaks))

    gain_median = median_abs / abs_strux
    gain_mean = mean_abs / abs_strux

    return {
        "model": name,
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "strux_peak": strux_peak,
        "strux_abs_peak": abs(strux_peak),
        "random_median_abs_peak": median_abs,
        "random_mean_abs_peak": mean_abs,
        "gain_median": gain_median,
        "gain_mean": gain_mean,
        "random_valid": len(peaks),
    }


def main():
    np.random.seed(42)

    graphs = {}

    graphs["erdos_renyi"] = nx.erdos_renyi_graph(1000, 0.008, seed=42)
    graphs["barabasi_albert"] = nx.barabasi_albert_graph(1000, 4, seed=42)
    graphs["grid_32x32"] = nx.grid_2d_graph(32, 32)
    graphs["grid_32x32"] = nx.convert_node_labels_to_integers(graphs["grid_32x32"])
    graphs["random_geometric"] = nx.random_geometric_graph(1000, 0.065, seed=42)
    graphs["balanced_tree"] = nx.balanced_tree(r=3, h=6)

    rows = []

    print("=" * 80)
    print("STRUX OBSERVER COMPRESSION — NULL MODEL TEST")
    print("=" * 80)

    for name, G in graphs.items():
        print(f"\nRunning: {name}")
        row = run_model(name, G, seed=42, n_random=100)
        rows.append(row)

        print(
            f"{name:18s} | "
            f"nodes={row['nodes']:4d} edges={row['edges']:5d} | "
            f"STRUX |peak|={row['strux_abs_peak']:.1f} | "
            f"random median={row['random_median_abs_peak']:.1f} | "
            f"gain={row['gain_median']:.2f}x"
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUTDIR / "observer_compression_null_models.csv", index=False)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(df)

    plt.figure(figsize=(9, 5))
    plt.bar(df["model"], df["gain_median"])
    plt.axhline(11.0, linestyle="--", color="red", label="SDSS reference ≈ 11x")
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("median compression gain")
    plt.title("Observer compression gain on null / synthetic graph families")
    plt.grid(axis="y")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGDIR / "observer_compression_null_models.png", dpi=200)
    plt.close()

    print("\nSaved:")
    print(OUTDIR / "observer_compression_null_models.csv")
    print(FIGDIR / "observer_compression_null_models.png")


if __name__ == "__main__":
    main()