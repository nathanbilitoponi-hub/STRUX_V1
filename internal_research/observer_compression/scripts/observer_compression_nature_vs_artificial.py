import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.neighbors import NearestNeighbors


OUTDIR = Path("internal_research/observer_compression/results")
FIGDIR = Path("internal_research/observer_compression/figures")
OUTDIR.mkdir(parents=True, exist_ok=True)
FIGDIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# BASIC STRUX OBSERVER COMPRESSION FUNCTIONS
# ============================================================

def largest_component(G):
    if G.number_of_nodes() == 0:
        return G
    if nx.is_connected(G):
        return nx.convert_node_labels_to_integers(G.copy())
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


def run_signature(name, family, G, seed=42, n_random=100):
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

    random_median = np.median(np.abs(peaks))
    random_mean = np.mean(np.abs(peaks))

    gain_median = random_median / abs_strux
    gain_mean = random_mean / abs_strux

    return {
        "name": name,
        "family": family,
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "strux_peak": strux_peak,
        "strux_abs_peak": abs(strux_peak),
        "random_median_abs_peak": random_median,
        "random_mean_abs_peak": random_mean,
        "gain_median": gain_median,
        "gain_mean": gain_mean,
        "random_valid": len(peaks),
    }


# ============================================================
# GRAPH BUILDERS
# ============================================================

def knn_graph(points, k=8):
    nbr = NearestNeighbors(n_neighbors=k + 1).fit(points)
    _, nn = nbr.kneighbors(points)

    G = nx.Graph()

    for i in range(len(points)):
        G.add_node(i)
        for j in nn[i, 1:]:
            G.add_edge(i, int(j))

    return G


def cosmic_web_toy(n_filament=700, n_noise=150, seed=42):
    rng = np.random.default_rng(seed)

    lines = [
        ((-1.0, -0.6), (1.0, 0.7)),
        ((-0.9, 0.8), (0.9, -0.5)),
        ((-0.2, -1.0), (0.25, 1.0)),
    ]

    pts = []

    for a, b in lines:
        a = np.array(a)
        b = np.array(b)

        t = rng.random(n_filament // len(lines))
        p = a[None, :] * (1 - t[:, None]) + b[None, :] * t[:, None]
        p += rng.normal(scale=0.035, size=p.shape)

        pts.append(p)

    noise = rng.uniform(-1.1, 1.1, size=(n_noise, 2))
    pts.append(noise)

    P = np.vstack(pts)

    return knn_graph(P, k=8)


def vascular_tree_toy(depth=7, branch=2, extra_edges=30, seed=42):
    rng = np.random.default_rng(seed)

    G = nx.balanced_tree(r=branch, h=depth)
    G = nx.convert_node_labels_to_integers(G)

    leaves = [n for n in G.nodes() if G.degree(n) == 1 and n != 0]

    for _ in range(extra_edges):
        a, b = rng.choice(leaves, size=2, replace=False)
        if not G.has_edge(int(a), int(b)):
            G.add_edge(int(a), int(b))

    return G


def leaf_venation_toy(n=900, seed=42):
    rng = np.random.default_rng(seed)

    # elongated leaf-like point cloud
    x = rng.uniform(-1, 1, size=n)
    max_y = 0.55 * (1 - np.abs(x) ** 1.7) + 0.05
    y = rng.uniform(-1, 1, size=n) * max_y

    P = np.vstack([x, y]).T

    # central vein
    vein = np.vstack([
        np.linspace(-0.95, 0.95, 150),
        rng.normal(scale=0.015, size=150)
    ]).T

    P = np.vstack([P, vein])

    return knn_graph(P, k=7)


def branching_growth_toy(n=1000, seed=42):
    rng = np.random.default_rng(seed)

    G = nx.Graph()
    G.add_node(0)

    tips = [0]
    next_node = 1

    while next_node < n:
        parent = int(rng.choice(tips))

        G.add_node(next_node)
        G.add_edge(parent, next_node)

        tips.append(next_node)

        # sometimes parent stops being a tip, sometimes it branches
        if rng.random() < 0.65 and parent in tips:
            tips.remove(parent)

        next_node += 1

    return G


def ring_lattice(n=1000, k=4):
    G = nx.Graph()
    for i in range(n):
        for d in range(1, k + 1):
            G.add_edge(i, (i + d) % n)
            G.add_edge(i, (i - d) % n)
    return G


def clustered_artificial(n_clusters=8, size=110, seed=42):
    rng = np.random.default_rng(seed)

    G = nx.Graph()
    offset = 0
    centers = []

    for c in range(n_clusters):
        nodes = list(range(offset, offset + size))
        offset += size

        p = 0.12
        H = nx.erdos_renyi_graph(size, p, seed=seed + c)
        H = nx.relabel_nodes(H, {i: nodes[i] for i in range(size)})
        G = nx.compose(G, H)
        centers.append(nodes[0])

    # artificial chain between clusters
    for a, b in zip(centers[:-1], centers[1:]):
        G.add_edge(a, b)

    return G


# ============================================================
# MAIN
# ============================================================

def main():
    seed = 42

    graphs = []

    # Natural-like / growth-like / geometric systems
    graphs.append(("cosmic_web_toy", "natural_like", cosmic_web_toy(seed=seed)))
    graphs.append(("vascular_tree_toy", "natural_like", vascular_tree_toy(seed=seed)))
    graphs.append(("leaf_venation_toy", "natural_like", leaf_venation_toy(seed=seed)))
    graphs.append(("branching_growth_toy", "natural_like", branching_growth_toy(seed=seed)))
    graphs.append(("random_geometric", "natural_like", nx.random_geometric_graph(1000, 0.065, seed=seed)))

    # Artificial / null / engineered controls
    graphs.append(("erdos_renyi", "artificial_null", nx.erdos_renyi_graph(1000, 0.008, seed=seed)))
    graphs.append(("barabasi_albert", "artificial_null", nx.barabasi_albert_graph(1000, 4, seed=seed)))

    grid = nx.grid_2d_graph(32, 32)
    grid = nx.convert_node_labels_to_integers(grid)
    graphs.append(("perfect_grid", "artificial_regular", grid))

    graphs.append(("ring_lattice", "artificial_regular", ring_lattice(n=1000, k=4)))
    graphs.append(("clustered_artificial", "artificial_modular", clustered_artificial(seed=seed)))

    rows = []

    print("=" * 90)
    print("STRUX OBSERVER SIGNATURE — NATURAL VS ARTIFICIAL")
    print("=" * 90)

    for name, family, G in graphs:
        print(f"\nRunning: {name} [{family}]")

        row = run_signature(
            name=name,
            family=family,
            G=G,
            seed=seed,
            n_random=100,
        )

        rows.append(row)

        print(
            f"{name:24s} | "
            f"{family:18s} | "
            f"|peak|={row['strux_abs_peak']:.1f} | "
            f"random_med={row['random_median_abs_peak']:.1f} | "
            f"gain={row['gain_median']:.2f}x"
        )

    df = pd.DataFrame(rows)

    out_csv = OUTDIR / "observer_signature_nature_vs_artificial.csv"
    out_png = FIGDIR / "observer_signature_nature_vs_artificial.png"

    df.to_csv(out_csv, index=False)

    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(df)

    # Plot: signature map
    plt.figure(figsize=(9, 6))

    for family, sub in df.groupby("family"):
        plt.scatter(
            sub["strux_abs_peak"],
            sub["gain_median"],
            s=90,
            label=family,
        )

        for _, r in sub.iterrows():
            plt.text(
                r["strux_abs_peak"] + 0.03,
                r["gain_median"] + 0.3,
                r["name"],
                fontsize=8,
            )

    plt.axvline(0.5, linestyle="--", color="gray", label="first half-level")
    plt.axhline(1.0, linestyle=":", color="black", label="no compression")
    plt.axhline(11.0, linestyle="--", color="red", label="SDSS reference ≈ 11x")

    plt.xlabel("STRUX observer |peak level|")
    plt.ylabel("median compression gain")
    plt.title("STRUX observer signature: natural-like vs artificial graphs")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

    print("\nSaved:")
    print(out_csv)
    print(out_png)


if __name__ == "__main__":
    main()