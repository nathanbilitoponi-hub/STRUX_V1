import numpy as np
from scipy.spatial import cKDTree


def get_dimension_configs(base_radius: float = 0.6):
    return {
        "small": {
            "cluster_radius": base_radius,
            "min_mass": 6,
            "cut_ratio_max": 0.35,
        },
        "medium": {
            "cluster_radius": base_radius * 1.8,
            "min_mass": 3,
            "cut_ratio_max": 0.45,
        },
        "large": {
            "cluster_radius": base_radius * 3.2,
            "min_mass": 2,
            "cut_ratio_max": 0.55,
        },
    }


def radius_clusters(points: np.ndarray, radius: float):
    tree = cKDTree(points)

    n = len(points)
    visited = np.zeros(n, dtype=bool)

    clusters = []

    for i in range(n):
        if visited[i]:
            continue

        stack = [i]
        comp = []

        while stack:
            j = stack.pop()

            if visited[j]:
                continue

            visited[j] = True
            comp.append(j)

            neigh = tree.query_ball_point(points[j], r=radius)

            for k in neigh:
                if not visited[k]:
                    stack.append(k)

        clusters.append(sorted(comp))

    return clusters


def compute_group_center(group_points: np.ndarray):
    return np.mean(group_points, axis=0)


def compute_compactness(group_points: np.ndarray):
    if len(group_points) < 5:
        return 0.0

    X = group_points - group_points.mean(axis=0, keepdims=True)

    C = np.cov(X.T)

    vals = np.linalg.eigvalsh(C)
    vals = np.sort(vals)[::-1]

    if vals[0] <= 1e-12:
        return 0.0

    compactness = 1.0 - (vals[0] - vals[-1]) / vals[0]

    return float(np.clip(compactness, 0.0, 1.0))


def compute_branch_degree(group_points: np.ndarray):
    if len(group_points) < 10:
        return 1

    center = group_points.mean(axis=0)

    vecs = group_points - center

    norms = np.linalg.norm(vecs, axis=1)

    if np.all(norms < 1e-8):
        return 1

    mask = norms > np.percentile(norms, 65)

    outer = vecs[mask]

    if len(outer) < 8:
        return 1

    outer = outer / (
        np.linalg.norm(outer, axis=1, keepdims=True) + 1e-8
    )

    dirs = []

    for v in outer:
        matched = False

        for d in dirs:
            if np.dot(v, d) > 0.82:
                matched = True
                break

        if not matched:
            dirs.append(v)

    return int(max(1, len(dirs)))


def compute_cut_ratio(
    points: np.ndarray,
    cluster_indices,
    neighbor_radius: float,
):
    if len(cluster_indices) == 0:
        return 1e9, 0, 0

    tree = cKDTree(points)

    cluster_set = set(cluster_indices)

    internal_edges = 0
    external_edges = 0

    for i in cluster_indices:
        neigh = tree.query_ball_point(points[i], r=neighbor_radius)

        for j in neigh:
            if j == i:
                continue

            if j in cluster_set:
                internal_edges += 1
            else:
                external_edges += 1

    internal_edges = internal_edges / 2.0

    cut_ratio = external_edges / (internal_edges + 1e-8)

    return (
        float(cut_ratio),
        int(internal_edges),
        int(external_edges),
    )


def summarize_dimension(
    points: np.ndarray,
    clusters,
    dimension_name: str,
    neighbor_radius: float,
):
    summaries = []

    for idx, comp in enumerate(clusters):
        grp = points[np.array(comp, dtype=int)]

        center = compute_group_center(grp)

        compactness = compute_compactness(grp)

        branch_degree = compute_branch_degree(grp)

        cut_ratio, internal_edges, external_edges = compute_cut_ratio(
            points=points,
            cluster_indices=comp,
            neighbor_radius=neighbor_radius,
        )

        summaries.append({
            "dimension": dimension_name,
            "cluster_id": idx,
            "indices": comp,
            "mass": int(len(comp)),
            "center": center,
            "compactness": compactness,
            "branch_degree": branch_degree,
            "cut_ratio": cut_ratio,
            "internal_edges": internal_edges,
            "external_edges": external_edges,
        })

    return summaries


def promote_dimension_groups(
    cluster_summaries,
    min_mass: int,
    cut_ratio_max: float,
):
    promoted = []

    for c in cluster_summaries:
        mass = c["mass"]
        compactness = c["compactness"]
        branch_degree = c["branch_degree"]
        cut_ratio = c["cut_ratio"]

        rule_A = (
            mass >= min_mass
            and branch_degree >= 3
            and compactness >= 0.10
            and cut_ratio <= cut_ratio_max
        )

        rule_B = (
            mass >= min_mass
            and compactness >= 0.45
            and branch_degree >= 2
            and cut_ratio <= cut_ratio_max
        )

        rule_C = (
            mass >= (min_mass + 2)
            and branch_degree >= 2
            and cut_ratio <= (cut_ratio_max * 0.75)
        )

        promote = bool(rule_A or rule_B or rule_C)

        promoted.append({
            **c,
            "min_mass": min_mass,
            "cut_ratio_max": cut_ratio_max,
            "rule_A": rule_A,
            "rule_B": rule_B,
            "rule_C": rule_C,
            "promote": promote,
        })

    return promoted


def compress_to_next_dimension(
    points: np.ndarray,
    promoted_clusters,
    next_dimension_name: str,
):
    new_points = []
    new_nodes = []

    out_id = 0

    for c in promoted_clusters:
        if not c["promote"]:
            continue

        center = np.asarray(c["center"], dtype=float)

        new_points.append(center)

        new_nodes.append({
            "node_id": out_id,
            "source_dimension": c["dimension"],
            "target_dimension": next_dimension_name,
            "center": center,
            "mass": c["mass"],
            "compactness": c["compactness"],
            "branch_degree": c["branch_degree"],
            "cut_ratio": c["cut_ratio"],
            "internal_edges": c["internal_edges"],
            "external_edges": c["external_edges"],
            "member_indices": c["indices"],
        })

        out_id += 1

    if len(new_points) == 0:
        new_points = np.empty(
            (0, points.shape[1]),
            dtype=float,
        )
    else:
        new_points = np.vstack(new_points)

    return new_points, new_nodes


def run_strux_life(
    points: np.ndarray,
    base_radius: float = 0.6,
    verbose: bool = True,
):
    if points is None or len(points) == 0:
        raise ValueError("run_strux_life: input points vuoto.")

    points = np.asarray(points, dtype=float)

    if points.ndim != 2:
        raise ValueError("run_strux_life: points deve essere array 2D.")

    cfg = get_dimension_configs(base_radius=base_radius)

    small_clusters = radius_clusters(
        points,
        cfg["small"]["cluster_radius"],
    )

    small_summary = summarize_dimension(
        points,
        small_clusters,
        "small",
        neighbor_radius=cfg["small"]["cluster_radius"],
    )

    promoted_small = promote_dimension_groups(
        small_summary,
        min_mass=cfg["small"]["min_mass"],
        cut_ratio_max=cfg["small"]["cut_ratio_max"],
    )

    medium_points, medium_seed_nodes = compress_to_next_dimension(
        points,
        promoted_small,
        next_dimension_name="medium",
    )

    if len(medium_points) > 0:
        medium_clusters = radius_clusters(
            medium_points,
            cfg["medium"]["cluster_radius"],
        )

        medium_summary = summarize_dimension(
            medium_points,
            medium_clusters,
            "medium",
            neighbor_radius=cfg["medium"]["cluster_radius"],
        )

        promoted_medium = promote_dimension_groups(
            medium_summary,
            min_mass=cfg["medium"]["min_mass"],
            cut_ratio_max=cfg["medium"]["cut_ratio_max"],
        )

        large_points, large_seed_nodes = compress_to_next_dimension(
            medium_points,
            promoted_medium,
            next_dimension_name="large",
        )

    else:
        medium_clusters = []
        medium_summary = []
        promoted_medium = []

        large_points = np.empty(
            (0, points.shape[1]),
            dtype=float,
        )

        large_seed_nodes = []

    if len(large_points) > 0:
        large_clusters = radius_clusters(
            large_points,
            cfg["large"]["cluster_radius"],
        )

        large_summary = summarize_dimension(
            large_points,
            large_clusters,
            "large",
            neighbor_radius=cfg["large"]["cluster_radius"],
        )

        promoted_large = promote_dimension_groups(
            large_summary,
            min_mass=cfg["large"]["min_mass"],
            cut_ratio_max=cfg["large"]["cut_ratio_max"],
        )

        next_life_points, next_life_nodes = compress_to_next_dimension(
            large_points,
            promoted_large,
            next_dimension_name="next_life",
        )

    else:
        large_clusters = []
        large_summary = []
        promoted_large = []

        next_life_points = np.empty(
            (0, points.shape[1]),
            dtype=float,
        )

        next_life_nodes = []

    if verbose:
        print("STRUX LIFE")
        print(f"input points        : {len(points)}")
        print(f"small groups        : {len(small_clusters)}")
        print(f"small promoted      : {sum(int(x['promote']) for x in promoted_small)}")
        print(f"medium input points : {len(medium_points)}")
        print(f"medium groups       : {len(medium_clusters)}")
        print(f"medium promoted     : {sum(int(x['promote']) for x in promoted_medium)}")
        print(f"large input points  : {len(large_points)}")
        print(f"large groups        : {len(large_clusters)}")
        print(f"large promoted      : {sum(int(x['promote']) for x in promoted_large)}")
        print(f"next life nodes     : {len(next_life_nodes)}")

    return {
        "input_points": points,
        "configs": cfg,
        "small_clusters": small_clusters,
        "small_summary": small_summary,
        "promoted_small": promoted_small,
        "medium_points": medium_points,
        "medium_seed_nodes": medium_seed_nodes,
        "medium_clusters": medium_clusters,
        "medium_summary": medium_summary,
        "promoted_medium": promoted_medium,
        "large_points": large_points,
        "large_seed_nodes": large_seed_nodes,
        "large_clusters": large_clusters,
        "large_summary": large_summary,
        "promoted_large": promoted_large,
        "next_life_points": next_life_points,
        "next_life_nodes": next_life_nodes,
    }