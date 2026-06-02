# ============================================================
# STRUX_V1 — FLORENCE OSM CORRIDOR CONTINUITY TEST
# Autonomous real-world demo using OpenStreetMap data
# ============================================================

import os
import warnings
import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from scipy.stats import ks_2samp

warnings.filterwarnings("ignore")

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

CENTER_POINT = (43.7696, 11.2558)   # Florence center
DIST = 1800                         # meters
NETWORK_TYPE = "drive"
TUBE_RADIUS = 150                   # meters
TOP_FRACTION = 0.12                 # top 12% STRUX edges
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ------------------------------------------------------------
# 1. DOWNLOAD DATA
# ------------------------------------------------------------

def download_graph():
    print("Scaricamento rete di Firenze centro...")

    G = ox.graph_from_point(
        CENTER_POINT,
        dist=DIST,
        network_type=NETWORK_TYPE,
        simplify=True
    )

    G = ox.project_graph(G)

    print(f"Nodi: {G.number_of_nodes()}")
    print(f"Edge: {G.number_of_edges()}")

    return G


# ------------------------------------------------------------
# 2. BETWENNESS BASELINE
# ------------------------------------------------------------

def compute_edge_betweenness(G):
    print("Calcolo edge betweenness...")

    try:
        ebc = nx.edge_betweenness_centrality(
            G,
            weight="length",
            normalized=True
        )
    except Exception:
        ebc = nx.edge_betweenness_centrality(
            G.to_undirected(),
            weight="length",
            normalized=True
        )

    return ebc


def get_ebc(ebc, u, v, k=None):
    return (
        ebc.get((u, v, k),
        ebc.get((u, v),
        ebc.get((v, u), 0.0)))
    )


# ------------------------------------------------------------
# 3. STRUX CORRIDOR CONTINUITY SCORE
# ------------------------------------------------------------

def calculate_continuity_score(u, v, node_coords, node_id_to_idx, radius=TUBE_RADIUS):
    """
    STRUX proxy:
    - geometric tube around edge axis
    - node projection along axis
    - continuity_gap
    - continuity_KS
    - final continuity = min(gap, KS)
    - score = continuity * log1p(support_count)
    """

    p1 = node_coords[node_id_to_idx[u]]
    p2 = node_coords[node_id_to_idx[v]]

    edge_vec = p2 - p1
    edge_len = np.linalg.norm(edge_vec)

    if edge_len < 1e-9:
        return {
            "score": 0.0,
            "support": 0,
            "gap": 0.0,
            "ks": 0.0,
            "continuity": 0.0,
            "length": 0.0,
        }

    unit_vec = edge_vec / edge_len

    relative_coords = node_coords - p1
    projections = np.dot(relative_coords, unit_vec)

    ortho_dist = np.linalg.norm(
        relative_coords - np.outer(projections, unit_vec),
        axis=1
    )

    mask = (
        (ortho_dist <= radius) &
        (projections >= 0) &
        (projections <= edge_len)
    )

    edge_projections = projections[mask] / edge_len
    support_count = len(edge_projections)

    if support_count < 3:
        return {
            "score": 0.0,
            "support": support_count,
            "gap": 0.0,
            "ks": 0.0,
            "continuity": 0.0,
            "length": float(edge_len),
        }

    edge_projections.sort()

    gaps = np.diff(np.concatenate(([0], edge_projections, [1])))
    continuity_gap = 1.0 - np.max(gaps)

    uniform_ref = np.linspace(0, 1, support_count)
    ks_stat, _ = ks_2samp(edge_projections, uniform_ref)
    continuity_ks = 1.0 - ks_stat

    continuity = min(continuity_gap, continuity_ks)
    score = continuity * np.log1p(support_count)

    return {
        "score": float(score),
        "support": int(support_count),
        "gap": float(continuity_gap),
        "ks": float(continuity_ks),
        "continuity": float(continuity),
        "length": float(edge_len),
    }


def compute_strux_scores(G):
    print("Analisi corridoi STRUX...")

    nodes_df, _ = ox.graph_to_gdfs(G)

    node_coords = nodes_df[["x", "y"]].to_numpy()
    node_ids = nodes_df.index.tolist()
    node_id_to_idx = {nid: i for i, nid in enumerate(node_ids)}

    edge_metrics = {}

    for u, v, k in G.edges(keys=True):
        edge_metrics[(u, v, k)] = calculate_continuity_score(
            u, v,
            node_coords=node_coords,
            node_id_to_idx=node_id_to_idx,
            radius=TUBE_RADIUS
        )

    scores = sorted(
        edge_metrics.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )

    top_n = max(1, int(len(scores) * TOP_FRACTION))
    top_edges = set([edge for edge, _ in scores[:top_n]])

    print(f"Top edges visualizzati: {top_n} / {len(scores)}")

    return edge_metrics, scores, top_edges


# ------------------------------------------------------------
# 4. FIGURE
# ------------------------------------------------------------

def build_figure(G, edge_metrics, top_edges, ebc):
    print("Generazione figura...")

    fig, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(22, 11),
        facecolor="black"
    )

    # ---------------- STRUX PANEL ----------------

    max_score = max([m["score"] for m in edge_metrics.values()]) + 1e-12

    edge_colors_strux = []
    edge_widths_strux = []

    for u, v, k in G.edges(keys=True):
        m = edge_metrics[(u, v, k)]
        s = m["score"] / max_score

        if (u, v, k) in top_edges:
            edge_colors_strux.append(
                mcolors.to_hex(plt.cm.plasma(0.45 + 0.55 * s))
            )
            edge_widths_strux.append(float(1.2 + 4.0 * s))
        else:
            edge_colors_strux.append("#252525")
            edge_widths_strux.append(0.35)

    ox.plot_graph(
        G,
        ax=ax1,
        edge_color=edge_colors_strux,
        edge_linewidth=edge_widths_strux,
        node_size=0,
        show=False,
        close=False,
        bgcolor="black"
    )

    ax1.set_title(
        "STRUX — Geometric Corridor Continuity",
        color="white",
        fontsize=16
    )

    # ---------------- BETWENNESS PANEL ----------------

    ebc_values = np.array([
        get_ebc(ebc, u, v, k) for u, v, k in G.edges(keys=True)
    ])

    max_ebc = max(ebc_values.max(), 1e-12)
    ebc_threshold = np.quantile(ebc_values, 0.88)

    edge_colors_ebc = []
    edge_widths_ebc = []

    for u, v, k in G.edges(keys=True):
        b_raw = get_ebc(ebc, u, v, k)
        b = b_raw / max_ebc

        if b_raw >= ebc_threshold:
            edge_colors_ebc.append(
                mcolors.to_hex(plt.cm.viridis(0.35 + 0.65 * b))
            )
            edge_widths_ebc.append(float(1.2 + 4.0 * b))
        else:
            edge_colors_ebc.append("#252525")
            edge_widths_ebc.append(0.35)

    ox.plot_graph(
        G,
        ax=ax2,
        edge_color=edge_colors_ebc,
        edge_linewidth=edge_widths_ebc,
        node_size=0,
        show=False,
        close=False,
        bgcolor="black"
    )

    ax2.set_title(
        "Baseline — Edge Betweenness Centrality",
        color="white",
        fontsize=16
    )

    plt.tight_layout()

    fig_path = os.path.join(OUTPUT_DIR, "firenze_strux_corridor_test.png")
    plt.savefig(fig_path, dpi=300, facecolor="black")
    plt.close()

    print(f"Figura salvata: {fig_path}")

    return fig_path


# ------------------------------------------------------------
# 5. EXPORT CSV
# ------------------------------------------------------------

def export_top_edges(G, scores, ebc, top_n=20):
    rows = []

    for rank, ((u, v, k), m) in enumerate(scores[:top_n], start=1):
        edge_data = G.get_edge_data(u, v, k)
        name = edge_data.get("name", "N/A")

        if isinstance(name, list):
            name = " / ".join(map(str, name))

        rows.append({
            "rank": rank,
            "street_name": name,
            "u": u,
            "v": v,
            "key": k,
            "strux_score": round(m["score"], 5),
            "support_count": m["support"],
            "continuity_gap": round(m["gap"], 5),
            "continuity_KS": round(m["ks"], 5),
            "continuity_final": round(m["continuity"], 5),
            "length_m": round(m["length"], 2),
            "edge_betweenness": round(get_ebc(ebc, u, v, k), 8),
        })

    df = pd.DataFrame(rows)

    csv_path = os.path.join(OUTPUT_DIR, "firenze_top20_strux_edges.csv")
    df.to_csv(csv_path, index=False)

    print(f"CSV salvato: {csv_path}")

    return df


# ------------------------------------------------------------
# 6. OVERLAP TEST
# ------------------------------------------------------------

def compute_overlap(G, edge_metrics, ebc):
    print("Calcolo overlap STRUX vs betweenness...")

    edges = list(G.edges(keys=True))

    strux_sorted = sorted(
        edges,
        key=lambda e: edge_metrics[e]["score"],
        reverse=True
    )

    ebc_sorted = sorted(
        edges,
        key=lambda e: get_ebc(ebc, e[0], e[1], e[2]),
        reverse=True
    )

    n = max(1, int(len(edges) * TOP_FRACTION))

    top_strux = set(strux_sorted[:n])
    top_ebc = set(ebc_sorted[:n])

    intersection = top_strux.intersection(top_ebc)
    union = top_strux.union(top_ebc)

    overlap_ratio = len(intersection) / n
    jaccard = len(intersection) / len(union)

    summary = {
        "top_fraction": TOP_FRACTION,
        "top_n": n,
        "strux_top_edges": len(top_strux),
        "ebc_top_edges": len(top_ebc),
        "intersection": len(intersection),
        "overlap_ratio": overlap_ratio,
        "jaccard": jaccard,
    }

    df = pd.DataFrame([summary])

    path = os.path.join(OUTPUT_DIR, "firenze_overlap_summary.csv")
    df.to_csv(path, index=False)

    print("\n=== OVERLAP STRUX vs BETWEENNESS ===")
    print(df.to_string(index=False))
    print(f"Overlap CSV salvato: {path}")

    return df


# ------------------------------------------------------------
# 7. MAIN
# ------------------------------------------------------------

def main():
    print("=" * 70)
    print("STRUX_V1 — Florence OSM Corridor Continuity Test")
    print("=" * 70)

    G = download_graph()

    ebc = compute_edge_betweenness(G)

    edge_metrics, scores, top_edges = compute_strux_scores(G)

    fig_path = build_figure(G, edge_metrics, top_edges, ebc)

    df_top = export_top_edges(G, scores, ebc, top_n=20)

    df_overlap = compute_overlap(G, edge_metrics, ebc)

    print("\n=== TOP 20 STRUX EDGES ===")
    print(df_top.to_string(index=False))

    print("\nAnalisi completata.")
    print(f"Figura: {fig_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()