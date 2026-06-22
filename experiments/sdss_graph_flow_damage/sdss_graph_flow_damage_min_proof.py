"""Graph-level flow-damage stress test on SDSS-derived kNN networks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm


CSV_COLUMNS = [
    "seed",
    "event_found",
    "verified_class",
    "delta",
    "dist_before",
    "dist_after",
    "components_after",
    "orphan_count",
    "controls_no_effect",
    "frac_controls_ge_verified",
    "node_id_removed",
    "source",
    "target",
    "k",
    "score",
]

FORBIDDEN_CLAIMS = [
    "cosmological validation",
    "void-finder benchmark",
    "VIDE/ZOBOV comparison",
    "void statistics",
    "cosmic web topology",
    "full-graph event frequency",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a graph-level flow-damage stress test on SDSS-derived kNN networks."
    )
    parser.add_argument("--input", required=True, help="Input CSV path.")
    parser.add_argument("--output-dir", required=True, help="Directory for CSV and JSON outputs.")
    parser.add_argument("--n-sample", type=int, default=3000, help="Points to sample per seed.")
    parser.add_argument("--k", type=int, default=4, help="Number of nearest neighbors.")
    parser.add_argument("--seed-start", type=int, default=40, help="First seed, inclusive.")
    parser.add_argument("--seed-end", type=int, default=49, help="Last seed, inclusive.")
    parser.add_argument("--n-controls", type=int, default=100, help="Off-path controls per verified event.")
    return parser.parse_args()


def detect_coordinate_columns(df: pd.DataFrame) -> list[str]:
    lower_to_original = {col.lower(): col for col in df.columns}
    if {"x", "y", "z"}.issubset(lower_to_original):
        return [lower_to_original["x"], lower_to_original["y"], lower_to_original["z"]]

    if {"ra", "dec", "z"}.issubset(lower_to_original):
        return [lower_to_original["ra"], lower_to_original["dec"], lower_to_original["z"]]

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 3:
        raise ValueError("Input CSV must contain X,Y,Z; ra,dec,z; or at least 3 numeric columns.")
    return numeric_cols[:3]


def load_coordinates(csv_path: Path) -> np.ndarray:
    df = pd.read_csv(csv_path)
    coord_cols = detect_coordinate_columns(df)
    coords = df[coord_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    finite_mask = np.isfinite(coords).all(axis=1)
    coords = coords[finite_mask]
    if coords.shape[0] < 3:
        raise ValueError("Need at least 3 rows with finite coordinates.")
    return coords


def sample_and_standardize(coords: np.ndarray, n_sample: int, seed: int) -> np.ndarray:
    if n_sample > coords.shape[0]:
        raise ValueError(f"Requested n_sample={n_sample}, but only {coords.shape[0]} finite rows exist.")
    rng = np.random.default_rng(seed)
    sample_idx = rng.choice(coords.shape[0], size=n_sample, replace=False)
    sampled = coords[sample_idx]
    return StandardScaler().fit_transform(sampled)


def build_symmetric_knn_graph(points: np.ndarray, k: int) -> nx.Graph:
    if k < 1:
        raise ValueError("k must be at least 1.")
    if k >= points.shape[0]:
        raise ValueError("k must be smaller than the sampled node count.")

    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="auto")
    nbrs.fit(points)
    distances, indices = nbrs.kneighbors(points)

    graph = nx.Graph()
    graph.add_nodes_from(range(points.shape[0]))
    for src in range(points.shape[0]):
        for dist, dst in zip(distances[src][1:], indices[src][1:]):
            graph.add_edge(int(src), int(dst), weight=float(dist))
    return graph


def largest_connected_component(graph: nx.Graph, points: np.ndarray) -> tuple[nx.Graph, np.ndarray]:
    if graph.number_of_nodes() == 0:
        return graph.copy(), points[:0]
    component_nodes = max(nx.connected_components(graph), key=len)
    ordered_nodes = sorted(component_nodes)
    subgraph = graph.subgraph(component_nodes).copy()
    mapping = {node: idx for idx, node in enumerate(ordered_nodes)}
    return nx.relabel_nodes(subgraph, mapping, copy=True), points[ordered_nodes]


def pca_extreme_pairs(points: np.ndarray, n_extremes: int = 12) -> list[tuple[int, int]]:
    if points.shape[0] < 2:
        return []
    n_components = min(3, points.shape[1])
    scores = PCA(n_components=n_components, random_state=0).fit_transform(points)
    pairs: set[tuple[int, int]] = set()
    n_take = min(n_extremes, points.shape[0])
    for axis in range(scores.shape[1]):
        order = np.argsort(scores[:, axis])
        lows = order[:n_take]
        highs = order[-n_take:]
        for low, high in zip(lows, highs[::-1]):
            if low != high:
                pairs.add(tuple(sorted((int(low), int(high)))))
    return list(pairs)


def far_pairs(points: np.ndarray, rng: np.random.Generator, n_anchor: int = 20) -> list[tuple[int, int]]:
    n_nodes = points.shape[0]
    if n_nodes < 2:
        return []
    anchors = rng.choice(n_nodes, size=min(n_anchor, n_nodes), replace=False)
    pairs: set[tuple[int, int]] = set()
    for anchor in anchors:
        diffs = points - points[int(anchor)]
        far = int(np.argmax(np.einsum("ij,ij->i", diffs, diffs)))
        if int(anchor) != far:
            pairs.add(tuple(sorted((int(anchor), far))))
    return list(pairs)


def candidate_source_target_pairs(points: np.ndarray, rng: np.random.Generator) -> list[tuple[int, int]]:
    pairs = pca_extreme_pairs(points)
    pairs.extend(far_pairs(points, rng))
    return list(dict.fromkeys(pairs))


def remove_and_measure(
    graph: nx.Graph, source: int, target: int, removed_node: int, dist_before: int
) -> dict[str, object]:
    damaged = graph.copy()
    damaged.remove_node(removed_node)
    components_after = nx.number_connected_components(damaged) if damaged.number_of_nodes() else 0
    orphan_count = sum(1 for _, degree in damaged.degree() if degree == 0)

    if source not in damaged or target not in damaged or not nx.has_path(damaged, source, target):
        return {
            "classification": "MANDATORY_CONSTRAINT",
            "dist_after": np.nan,
            "delta": np.nan,
            "components_after": components_after,
            "orphan_count": orphan_count,
        }

    dist_after = nx.shortest_path_length(damaged, source=source, target=target)
    delta = dist_after - dist_before
    if delta > 0:
        classification = "PATH_OPTIMIZER"
    elif delta == 0:
        classification = "NO_FLOW_EFFECT"
    else:
        classification = "SHORTER_AFTER_REMOVAL"

    return {
        "classification": classification,
        "dist_after": int(dist_after),
        "delta": int(delta),
        "components_after": int(components_after),
        "orphan_count": int(orphan_count),
    }


def candidate_removed_nodes(path_before: list[int]) -> Iterable[int]:
    if len(path_before) <= 2:
        return []
    return path_before[1:-1]


def score_event(delta: int, dist_before: int, dist_after: int) -> float:
    return float(delta + 0.01 * dist_after + 0.001 * dist_before)


def search_best_event(graph: nx.Graph, points: np.ndarray, rng: np.random.Generator) -> dict[str, object] | None:
    best_event: dict[str, object] | None = None
    for source, target in candidate_source_target_pairs(points, rng):
        if source == target or not nx.has_path(graph, source, target):
            continue
        path_before = nx.shortest_path(graph, source=source, target=target)
        dist_before = len(path_before) - 1
        for removed_node in candidate_removed_nodes(path_before):
            measured = remove_and_measure(graph, source, target, removed_node, dist_before)
            if (
                measured["classification"] == "PATH_OPTIMIZER"
                and measured["components_after"] == 1
                and measured["orphan_count"] == 0
            ):
                dist_after = int(measured["dist_after"])
                delta = int(measured["delta"])
                event = {
                    "source": int(source),
                    "target": int(target),
                    "node_id_removed": int(removed_node),
                    "dist_before": int(dist_before),
                    "dist_after": dist_after,
                    "delta": delta,
                    "components_after": int(measured["components_after"]),
                    "orphan_count": int(measured["orphan_count"]),
                    "path_before": path_before,
                    "path_after": nx.shortest_path(
                        graph.copy().subgraph([n for n in graph.nodes if n != removed_node]),
                        source=source,
                        target=target,
                    ),
                    "score": score_event(delta, dist_before, dist_after),
                }
                if best_event is None or event["score"] > best_event["score"]:
                    best_event = event
    return best_event


def run_controls(
    graph: nx.Graph,
    event: dict[str, object],
    n_controls: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    blocked_nodes = set(event["path_before"])
    blocked_nodes.update(event["path_after"])
    blocked_nodes.update([event["source"], event["target"], event["node_id_removed"]])
    candidates = np.array([node for node in graph.nodes if node not in blocked_nodes], dtype=int)
    if candidates.size == 0 or n_controls <= 0:
        return float("nan"), float("nan")

    chosen = rng.choice(candidates, size=min(n_controls, candidates.size), replace=False)
    no_effect = 0
    ge_verified = 0
    for removed_node in chosen:
        measured = remove_and_measure(
            graph,
            int(event["source"]),
            int(event["target"]),
            int(removed_node),
            int(event["dist_before"]),
        )
        if measured["classification"] == "NO_FLOW_EFFECT":
            no_effect += 1
        delta = measured["delta"]
        if np.isfinite(delta) and int(delta) >= int(event["delta"]):
            ge_verified += 1

    total = int(chosen.size)
    return no_effect / total, ge_verified / total


def empty_result(seed: int, k: int) -> dict[str, object]:
    return {
        "seed": seed,
        "event_found": False,
        "verified_class": "",
        "delta": np.nan,
        "dist_before": np.nan,
        "dist_after": np.nan,
        "components_after": np.nan,
        "orphan_count": np.nan,
        "controls_no_effect": np.nan,
        "frac_controls_ge_verified": np.nan,
        "node_id_removed": np.nan,
        "source": np.nan,
        "target": np.nan,
        "k": k,
        "score": np.nan,
    }


def run_seed(coords: np.ndarray, n_sample: int, k: int, seed: int, n_controls: int) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    points = sample_and_standardize(coords, n_sample, seed)
    graph, component_points = largest_connected_component(build_symmetric_knn_graph(points, k), points)

    event = search_best_event(graph, component_points, rng)
    if event is None:
        return empty_result(seed, k)

    controls_no_effect, frac_controls_ge_verified = run_controls(graph, event, n_controls, rng)
    return {
        "seed": seed,
        "event_found": True,
        "verified_class": "PATH_OPTIMIZER",
        "delta": event["delta"],
        "dist_before": event["dist_before"],
        "dist_after": event["dist_after"],
        "components_after": event["components_after"],
        "orphan_count": event["orphan_count"],
        "controls_no_effect": controls_no_effect,
        "frac_controls_ge_verified": frac_controls_ge_verified,
        "node_id_removed": event["node_id_removed"],
        "source": event["source"],
        "target": event["target"],
        "k": k,
        "score": event["score"],
    }


def build_summary(results: pd.DataFrame) -> dict[str, object]:
    seeds_tested = int(len(results))
    events_found = int(results["event_found"].sum())
    event_rate = events_found / seeds_tested if seeds_tested else 0.0

    path_optimizer_like = int((results["verified_class"] == "PATH_OPTIMIZER").sum())
    mandatory_like = int((results["verified_class"] == "MANDATORY_CONSTRAINT").sum())
    good_negative_controls = int((results["controls_no_effect"] >= 0.7).sum())
    good_negative_rate = good_negative_controls / seeds_tested if seeds_tested else 0.0

    deltas = pd.to_numeric(results.loc[results["event_found"], "delta"], errors="coerce").dropna()
    if good_negative_rate >= 0.7:
        verdict = "PASS_MULTISEED_REPLICATION_STRONG"
    elif good_negative_rate >= 0.4:
        verdict = "PASS_MULTISEED_REPLICATION_WEAK"
    elif event_rate > 0:
        verdict = "WEAK_SINGLE_OR_SPARSE_SIGNAL"
    else:
        verdict = "FAIL_MULTISEED_REPLICATION"

    return {
        "test": "SDSS_GRAPH_FLOW_DAMAGE_MIN_PROOF",
        "seeds_tested": seeds_tested,
        "events_found": events_found,
        "path_optimizer_like": path_optimizer_like,
        "mandatory_like": mandatory_like,
        "good_negative_controls": good_negative_controls,
        "event_rate": event_rate,
        "good_negative_rate": good_negative_rate,
        "delta_min": int(deltas.min()) if not deltas.empty else None,
        "delta_max": int(deltas.max()) if not deltas.empty else None,
        "verdict": verdict,
        "safe_claim": "Existence proof only. Frequency and cosmological relevance untested.",
        "forbidden_claims": FORBIDDEN_CLAIMS,
    }


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    coords = load_coordinates(input_path)
    seeds = range(args.seed_start, args.seed_end + 1)
    rows = [
        run_seed(coords, args.n_sample, args.k, seed, args.n_controls)
        for seed in tqdm(seeds, desc="seeds")
    ]
    results = pd.DataFrame(rows, columns=CSV_COLUMNS)
    summary = build_summary(results)

    results_path = output_dir / "sdss_graph_flow_damage_results.csv"
    summary_path = output_dir / "sdss_graph_flow_damage_summary.json"
    results.to_csv(results_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {results_path}")
    print(f"Wrote {summary_path}")
    print(f"Verdict: {summary['verdict']}")


if __name__ == "__main__":
    main()
