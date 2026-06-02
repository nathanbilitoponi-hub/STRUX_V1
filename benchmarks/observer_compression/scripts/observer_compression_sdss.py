"""
STRUX Observer Compression Benchmark — SDSS

Graph-only test:
- Build an abstract kNN graph from SDSS RA/Dec/z.
- Compute STRUX score = approximate betweenness * local non-redundancy.
- Select the max-STRUX node as observer.
- Compare its observed structural peak against random observers.

Expected reference result on 3000 sampled SDSS points:
- STRUX observer peak: 0.5
- Random median |peak|: about 5.5
- Observer compression gain: about 11x
"""

from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors


def build_graph(points, k=10):
    nbr = NearestNeighbors(n_neighbors=k + 1).fit(points)
    _, nn = nbr.kneighbors(points)

    graph = nx.Graph()
    for i in range(len(points)):
        for j in nn[i, 1:]:
            graph.add_edge(i, int(j))

    return graph


def compute_strux_score(graph, seed=42, betweenness_samples=400):
    bc = nx.betweenness_centrality(
        graph,
        k=min(betweenness_samples, graph.number_of_nodes()),
        normalized=True,
        seed=seed,
    )

    score = {}
    for n in graph.nodes():
        neigh = list(graph.neighbors(n))

        links = 0
        for i, a in enumerate(neigh):
            for b in neigh[i + 1:]:
                if graph.has_edge(a, b):
                    links += 1

        redundancy = links / (len(neigh) + 1e-12)
        score[n] = bc[n] / (1.0 + redundancy)

    return score


def observer_peak_level(graph, score, observer, cutoff=12):
    d0 = nx.single_source_shortest_path_length(graph, observer, cutoff=cutoff)
    reachable = list(d0.keys())

    if len(reachable) < 50:
        return np.nan, np.nan, len(reachable)

    a = max(reachable, key=lambda n: d0[n])
    da = nx.single_source_shortest_path_length(graph, a)

    b = max(da.keys(), key=lambda n: da[n])
    db = nx.single_source_shortest_path_length(graph, b)

    levels = {}

    for n, d in d0.items():
        if d == 0:
            continue

        sign = 1 if db.get(n, 999999) < da.get(n, 999999) else -1
        level = sign * (d - 0.5)
        levels.setdefault(level, []).append(n)

    xs = []
    ys = []

    for level, nodes in levels.items():
        xs.append(level)
        ys.append(np.mean([score[n] for n in nodes]))

    xs = np.array(xs)
    ys = np.array(ys)

    if len(xs) == 0:
        return np.nan, np.nan, len(reachable)

    peak = xs[np.argmax(ys)]
    peak_score = ys.max()

    return peak, peak_score, len(reachable)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to SDSS CSV with columns ra, dec, z")
    parser.add_argument("--sample-size", type=int, default=3000)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--random-observers", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--outdir", default="benchmarks/observer_compression")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    results_dir = outdir / "results"
    figures_dir = outdir / "figures"

    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    df.columns = [c.lower().strip() for c in df.columns]

    required = {"ra", "dec", "z"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    ra = df["ra"].to_numpy(float)
    dec = df["dec"].to_numpy(float)
    z = df["z"].to_numpy(float)

    mask = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(z) & (z > 0)
    raw = np.vstack([ra[mask], dec[mask], z[mask]]).T

    raw = (raw - raw.mean(axis=0)) / (raw.std(axis=0) + 1e-12)

    rng = np.random.default_rng(args.seed)

    n = min(args.sample_size, len(raw))
    idx = rng.choice(len(raw), n, replace=False)
    points = raw[idx]

    print("=" * 80)
    print("STRUX OBSERVER COMPRESSION BENCHMARK")
    print("=" * 80)
    print("Input:", args.input)
    print("Sample size:", n)

    graph = build_graph(points, k=args.k)

    print("Graph nodes:", graph.number_of_nodes())
    print("Graph edges:", graph.number_of_edges())

    print("Computing STRUX score...")
    score = compute_strux_score(graph, seed=args.seed)

    strux_observer = max(score, key=score.get)
    strux_peak, strux_peak_score, strux_reach = observer_peak_level(
        graph, score, strux_observer
    )

    nodes = list(graph.nodes())
    random_observers = rng.choice(nodes, size=args.random_observers, replace=False)

    rows = []
    for obs in random_observers:
        peak, peak_score, reach = observer_peak_level(graph, score, int(obs))

        if np.isfinite(peak):
            rows.append(
                {
                    "observer": int(obs),
                    "peak": peak,
                    "abs_peak": abs(peak),
                    "peak_score": peak_score,
                    "reach": reach,
                    "type": "random",
                }
            )

    df_random = pd.DataFrame(rows)

    abs_strux = abs(strux_peak)
    if abs_strux == 0:
        abs_strux = 0.5

    median_abs_random = df_random["abs_peak"].median()
    mean_abs_random = df_random["abs_peak"].mean()

    compression_gain_median = median_abs_random / abs_strux
    compression_gain_mean = mean_abs_random / abs_strux

    summary = {
        "sample_size": n,
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "strux_observer": strux_observer,
        "strux_peak": strux_peak,
        "strux_abs_peak": abs(strux_peak),
        "strux_peak_score": strux_peak_score,
        "strux_reach": strux_reach,
        "random_observers": len(df_random),
        "random_mean_abs_peak": mean_abs_random,
        "random_median_abs_peak": median_abs_random,
        "compression_gain_mean": compression_gain_mean,
        "compression_gain_median": compression_gain_median,
    }

    df_summary = pd.DataFrame([summary])

    df_random.to_csv(results_dir / "observer_compression_random_observers.csv", index=False)
    df_summary.to_csv(results_dir / "observer_compression_summary.csv", index=False)

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    for k, v in summary.items():
        print(f"{k}: {v}")

    if abs(strux_peak) <= 0.5 and median_abs_random > 2:
        verdict = "PASS_STRONG"
    elif abs(strux_peak) <= 1.5 and median_abs_random > abs(strux_peak):
        verdict = "PASS_WEAK"
    else:
        verdict = "NO_PASS"

    print("verdict:", verdict)

    # Figure 1
    plt.figure(figsize=(10, 5))
    bins = np.arange(df_random["peak"].min() - 0.5, df_random["peak"].max() + 1.0, 1.0)
    plt.hist(df_random["peak"], bins=bins, alpha=0.75, label="random observers")
    plt.axvline(strux_peak, color="red", linestyle="--", linewidth=2, label=f"STRUX peak={strux_peak}")
    plt.axvline(0, color="black", linestyle=":", label="observer membrane 0")
    plt.axvline(0.5, color="gray", linestyle=":")
    plt.axvline(-0.5, color="gray", linestyle=":")
    plt.xlabel("peak level")
    plt.ylabel("count")
    plt.title("Observer peak distribution: STRUX vs random")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "observer_peak_distribution.png", dpi=200)
    plt.close()

    # Figure 2
    plt.figure(figsize=(8, 4))
    plt.hist(df_random["abs_peak"], bins=np.arange(0, df_random["abs_peak"].max() + 1, 1), alpha=0.75)
    plt.axvline(abs(strux_peak), color="red", linestyle="--", linewidth=2, label=f"STRUX |peak|={abs(strux_peak)}")
    plt.xlabel("|peak level|")
    plt.ylabel("count")
    plt.title("Observer compression distance")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / "observer_compression_histogram.png", dpi=200)
    plt.close()

    print("\nSaved:")
    print(results_dir / "observer_compression_random_observers.csv")
    print(results_dir / "observer_compression_summary.csv")
    print(figures_dir / "observer_peak_distribution.png")
    print(figures_dir / "observer_compression_histogram.png")


if __name__ == "__main__":
    main()