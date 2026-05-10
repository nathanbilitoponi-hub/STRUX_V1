import numpy as np


def match_nodes(strux_nodes, void_nodes, tol=1.75):
    strux_nodes = np.asarray(strux_nodes, dtype=float)
    void_nodes = np.asarray(void_nodes, dtype=float)

    matches = []
    used_void = set()

    if len(strux_nodes) == 0 or len(void_nodes) == 0:
        return matches

    for i, s in enumerate(strux_nodes):
        d = np.linalg.norm(void_nodes - s[None, :], axis=1)

        j = int(np.argmin(d))

        if d[j] <= tol and j not in used_void:
            matches.append((i, j, float(d[j])))
            used_void.add(j)

    return matches


def run_brain_v2(
    strux_nodes,
    void_nodes,
    strux_backbone_edges,
    void_backbone_edges=None,
    tol=1.75,
):
    strux_nodes = np.asarray(strux_nodes, dtype=float)
    void_nodes = np.asarray(void_nodes, dtype=float)

    strux_backbone_edges = [
        (int(u), int(v))
        for (u, v) in strux_backbone_edges
    ]

    void_backbone_edges = void_backbone_edges or []

    void_backbone_edges = [
        (int(u), int(v))
        for (u, v) in void_backbone_edges
    ]

    matches = match_nodes(
        strux_nodes,
        void_nodes,
        tol=tol,
    )

    matched_strux = set(i for i, _, _ in matches)
    matched_void = set(j for _, j, _ in matches)

    void_to_strux = {
        j: i
        for i, j, _ in matches
    }

    node_status = []

    for i in range(len(strux_nodes)):
        if i in matched_strux:
            dist = next(
                d for (si, _, d) in matches
                if si == i
            )

            node_status.append({
                "node_id": i,
                "status": "matched",
                "distance": float(dist),
            })

        else:
            node_status.append({
                "node_id": i,
                "status": "strux_only",
                "distance": None,
            })

    for j in range(len(void_nodes)):
        if j not in matched_void:
            node_status.append({
                "node_id": f"void_{j}",
                "status": "void_only",
                "distance": None,
            })

    strux_edge_set = set(
        tuple(sorted(e))
        for e in strux_backbone_edges
    )

    mapped_void_edges = set()
    unmapped_void_edges = []

    for (u, v) in void_backbone_edges:
        if u in void_to_strux and v in void_to_strux:
            su = void_to_strux[u]
            sv = void_to_strux[v]

            mapped_void_edges.add(
                tuple(sorted((su, sv)))
            )

        else:
            unmapped_void_edges.append((u, v))

    edge_status = []

    for e in sorted(strux_edge_set):
        if e in mapped_void_edges:
            edge_status.append({
                "edge": e,
                "status": "confirmed",
            })

        else:
            edge_status.append({
                "edge": e,
                "status": "strux_only",
            })

    for e in sorted(mapped_void_edges):
        if e not in strux_edge_set:
            edge_status.append({
                "edge": e,
                "status": "void_only",
            })

    node_total = {
        i: 0
        for i in range(len(strux_nodes))
    }

    node_confirmed = {
        i: 0
        for i in range(len(strux_nodes))
    }

    for e in edge_status:
        u, v = e["edge"]

        if u not in node_total or v not in node_total:
            continue

        node_total[u] += 1
        node_total[v] += 1

        if e["status"] == "confirmed":
            node_confirmed[u] += 1
            node_confirmed[v] += 1

    local_scores = {}

    for i in range(len(strux_nodes)):
        if node_total[i] > 0:
            score = node_confirmed[i] / node_total[i]
        else:
            score = 0.0

        local_scores[i] = float(score)

    scores = list(local_scores.values())

    local_mean = (
        float(np.mean(scores))
        if scores else 0.0
    )

    local_median = (
        float(np.median(scores))
        if scores else 0.0
    )

    top_low_nodes = sorted(
        local_scores.items(),
        key=lambda x: x[1]
    )[:5]

    top_high_nodes = sorted(
        local_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    node_counts = {
        "matched": sum(
            1 for n in node_status
            if n["status"] == "matched"
        ),
        "strux_only": sum(
            1 for n in node_status
            if n["status"] == "strux_only"
        ),
        "void_only": sum(
            1 for n in node_status
            if n["status"] == "void_only"
        ),
    }

    edge_counts = {
        "confirmed": sum(
            1 for e in edge_status
            if e["status"] == "confirmed"
        ),
        "strux_only": sum(
            1 for e in edge_status
            if e["status"] == "strux_only"
        ),
        "void_only": sum(
            1 for e in edge_status
            if e["status"] == "void_only"
        ),
    }

    return {
        "matches": matches,
        "node_status": node_status,
        "edge_status": edge_status,
        "node_counts": node_counts,
        "edge_counts": edge_counts,
        "local_scores": local_scores,
        "local_mean": local_mean,
        "local_median": local_median,
        "top_low_nodes": top_low_nodes,
        "top_high_nodes": top_high_nodes,
        "unmapped_void_edges": unmapped_void_edges,
    }