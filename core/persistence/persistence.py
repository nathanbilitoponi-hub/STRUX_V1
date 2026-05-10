import numpy as np
from sklearn.cluster import DBSCAN


def compute_edge_persistence_advanced(
    graph,
    node_positions,
    iterations=10,
    sample_ratio=0.8,
    eps=1.5,
    min_samples=2,
    persistence_threshold=0.5,
):
    if len(graph) == 0:
        return {
            "all_clusters": [],
            "persistent_core": [],
            "total_clusters": 0,
            "total_edge_instances": 0,
        }

    node_positions = np.asarray(node_positions, dtype=float)

    all_edge_records = []

    rng = np.random.default_rng(42)

    for run in range(iterations):
        sample_size = max(
            1,
            int(sample_ratio * len(graph))
        )

        sample_idx = rng.choice(
            len(graph),
            size=sample_size,
            replace=False,
        )

        for idx in sample_idx:
            e = graph[idx]

            u = int(e["u"])
            v = int(e["v"])

            p1 = node_positions[u]
            p2 = node_positions[v]

            mid = 0.5 * (p1 + p2)

            length = float(
                np.linalg.norm(p2 - p1)
            )

            rec = dict(e)

            rec["u"] = u
            rec["v"] = v
            rec["run"] = run
            rec["mid"] = mid
            rec["length"] = length

            all_edge_records.append(rec)

    if len(all_edge_records) == 0:
        return {
            "all_clusters": [],
            "persistent_core": [],
            "total_clusters": 0,
            "total_edge_instances": 0,
        }

    midpoints = np.vstack([
        r["mid"]
        for r in all_edge_records
    ])

    clustering = DBSCAN(
        eps=eps,
        min_samples=min_samples,
    )

    labels = clustering.fit_predict(midpoints)

    valid_labels = sorted(
        set(labels[labels >= 0])
    )

    cluster_summary = []

    for cid in valid_labels:
        idxs = np.where(labels == cid)[0]

        group = [
            all_edge_records[k]
            for k in idxs
        ]

        runs_present = sorted(
            set(g["run"] for g in group)
        )

        persistence = (
            len(runs_present)
            / max(iterations, 1)
        )

        mids = np.vstack([
            g["mid"]
            for g in group
        ])

        lengths = np.array([
            g["length"]
            for g in group
        ], dtype=float)

        scores = [
            float(g.get("score", 0.0))
            for g in group
        ]

        supports = [
            float(g.get("support", 0.0))
            for g in group
            if "support" in g
        ]

        cluster_summary.append({
            "cluster_id": int(cid),
            "n_instances": int(len(group)),
            "n_runs": int(len(runs_present)),
            "persistence": float(persistence),
            "mid_mean": mids.mean(axis=0),
            "mid_std": mids.std(axis=0),
            "length_mean": float(lengths.mean()),
            "score_mean": (
                float(np.mean(scores))
                if len(scores) > 0 else 0.0
            ),
            "support_mean": (
                float(np.mean(supports))
                if len(supports) > 0 else 0.0
            ),
            "member_edges": [
                {
                    "u": int(g["u"]),
                    "v": int(g["v"]),
                    "run": int(g["run"]),
                }
                for g in group
            ],
        })

    cluster_summary = sorted(
        cluster_summary,
        key=lambda x: (
            -x["persistence"],
            -x["n_instances"],
        ),
    )

    persistent_core = [
        c for c in cluster_summary
        if c["persistence"] >= persistence_threshold
    ]

    return {
        "all_clusters": cluster_summary,
        "persistent_core": persistent_core,
        "total_clusters": len(cluster_summary),
        "total_edge_instances": len(all_edge_records),
    }