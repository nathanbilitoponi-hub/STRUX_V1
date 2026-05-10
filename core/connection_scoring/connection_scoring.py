import numpy as np
from itertools import combinations


def _point_segment_projection(points: np.ndarray, p1: np.ndarray, p2: np.ndarray):
    axis = p2 - p1
    seg_len = float(np.linalg.norm(axis))

    if seg_len < 1e-12:
        return 0.0, np.zeros(len(points)), np.full(len(points), np.inf)

    u = axis / seg_len
    rel = points - p1[None, :]
    t = rel @ u
    t_clamped = np.clip(t, 0.0, seg_len)

    proj = p1[None, :] + t_clamped[:, None] * u[None, :]
    dist_to_axis = np.linalg.norm(points - proj, axis=1)

    return seg_len, t_clamped, dist_to_axis


def _extract_region_centers(large_regions):
    centers = []

    for r in large_regions:
        centers.append(np.asarray(r["center"], dtype=float))

    if len(centers) == 0:
        return np.empty((0, 3), dtype=float)

    return np.vstack(centers)


def _support_mask(points, p1, p2, tube_radius):
    seg_len, t_along, dist_to_axis = _point_segment_projection(points, p1, p2)

    if seg_len < 1e-12:
        return seg_len, t_along, np.zeros(len(points), dtype=bool)

    mask = (
        (t_along >= 0.0)
        & (t_along <= seg_len)
        & (dist_to_axis <= tube_radius)
    )

    return seg_len, t_along, mask


def _continuity_score(t_along_support, seg_len, n_bins=20):
    if seg_len < 1e-12 or len(t_along_support) == 0:
        return 0.0

    bins = np.linspace(0.0, seg_len, n_bins + 1)
    hist, _ = np.histogram(t_along_support, bins=bins)
    occupied = hist > 0

    return float(np.mean(occupied))


def _coverage_score(n_support_points, seg_len):
    if seg_len < 1e-12:
        return 0.0

    return float(n_support_points / seg_len)


def _central_density_ratio(points_support, p1, p2, tube_radius, center_fraction=0.35):
    if len(points_support) == 0:
        return 0.0

    seg_len, _, dist_to_axis = _point_segment_projection(points_support, p1, p2)

    if seg_len < 1e-12:
        return 0.0

    inner_radius = max(tube_radius * center_fraction, 1e-12)
    n_inner = np.sum(dist_to_axis <= inner_radius)

    return float(n_inner / max(len(points_support), 1))


def _classify_connection(
    continuity,
    coverage,
    central_density_ratio,
    strong_continuity_thr=0.6,
    weak_continuity_thr=0.4,
    strong_coverage_thr=0.5,
    strong_central_ratio_thr=0.08,
):
    if (
        continuity >= strong_continuity_thr
        and coverage >= strong_coverage_thr
        and central_density_ratio >= strong_central_ratio_thr
    ):
        return "strong filament"

    if continuity >= weak_continuity_thr:
        return "weak filament"

    return "none"


def score_pair_connection(
    points: np.ndarray,
    p1: np.ndarray,
    p2: np.ndarray,
    tube_radius: float = 0.35,
    n_bins: int = 20,
    strong_continuity_thr: float = 0.6,
    weak_continuity_thr: float = 0.4,
    strong_coverage_thr: float = 0.5,
    strong_central_ratio_thr: float = 0.08,
):
    points = np.asarray(points, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)

    seg_len, t_along, mask = _support_mask(
        points,
        p1,
        p2,
        tube_radius=tube_radius,
    )

    support_points = points[mask]
    t_support = t_along[mask]

    continuity = _continuity_score(
        t_along_support=t_support,
        seg_len=seg_len,
        n_bins=n_bins,
    )

    coverage = _coverage_score(
        n_support_points=len(support_points),
        seg_len=seg_len,
    )

    central_density_ratio = _central_density_ratio(
        points_support=support_points,
        p1=p1,
        p2=p2,
        tube_radius=tube_radius,
    )

    label = _classify_connection(
        continuity=continuity,
        coverage=coverage,
        central_density_ratio=central_density_ratio,
        strong_continuity_thr=strong_continuity_thr,
        weak_continuity_thr=weak_continuity_thr,
        strong_coverage_thr=strong_coverage_thr,
        strong_central_ratio_thr=strong_central_ratio_thr,
    )

    return {
        "class": label,
        "segment_length": float(seg_len),
        "n_support_points": int(len(support_points)),
        "continuity": float(continuity),
        "coverage": float(coverage),
        "central_density_ratio": float(central_density_ratio),
    }


def score_region_connections(
    points: np.ndarray,
    large_regions,
    tube_radius: float = 0.35,
    n_bins: int = 20,
    strong_continuity_thr: float = 0.6,
    weak_continuity_thr: float = 0.4,
    strong_coverage_thr: float = 0.5,
    strong_central_ratio_thr: float = 0.08,
):
    points = np.asarray(points, dtype=float)
    centers = _extract_region_centers(large_regions)

    all_pair_scores = []
    strong_edges = []
    weak_edges = []

    if len(centers) < 2:
        return {
            "strong_edges": strong_edges,
            "weak_edges": weak_edges,
            "all_pair_scores": all_pair_scores,
        }

    for i, j in combinations(range(len(centers)), 2):
        p1 = centers[i]
        p2 = centers[j]

        score = score_pair_connection(
            points=points,
            p1=p1,
            p2=p2,
            tube_radius=tube_radius,
            n_bins=n_bins,
            strong_continuity_thr=strong_continuity_thr,
            weak_continuity_thr=weak_continuity_thr,
            strong_coverage_thr=strong_coverage_thr,
            strong_central_ratio_thr=strong_central_ratio_thr,
        )

        row = {
            "source": int(i),
            "target": int(j),
            **score,
        }

        all_pair_scores.append(row)

        if row["class"] == "strong filament":
            strong_edges.append(row)
        elif row["class"] == "weak filament":
            weak_edges.append(row)

    sort_key = lambda x: (
        -x["central_density_ratio"],
        -x["continuity"],
        -x["coverage"],
    )

    return {
        "strong_edges": sorted(strong_edges, key=sort_key),
        "weak_edges": sorted(weak_edges, key=sort_key),
        "all_pair_scores": sorted(all_pair_scores, key=sort_key),
    }