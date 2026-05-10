from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree, connected_components


def _build_sparse(n, edges):
    rows, cols, vals = [], [], []

    for e in edges:
        u = int(e["u"])
        v = int(e["v"])
        w = float(e["length"])

        rows += [u, v]
        cols += [v, u]
        vals += [w, w]

    return csr_matrix((vals, (rows, cols)), shape=(n, n))


def extract_backbone(graph, verbose=True):
    if len(graph) == 0:
        return [], []

    n = max(max(int(e["u"]), int(e["v"])) for e in graph) + 1

    G = _build_sparse(n, graph)

    n_components, _ = connected_components(G, directed=False)

    T = minimum_spanning_tree(G)
    T = T + T.T

    rr, cc = T.nonzero()

    edges = []
    for a, b in zip(rr, cc):
        if a < b:
            edges.append((int(a), int(b)))

    connected_nodes = len(set(x for e in edges for x in e))
    nodes = list(range(n))

    if verbose:
        print(f"[backbone] components: {n_components}")
        print(f"[backbone] nodes total: {n}")
        print(f"[backbone] nodes in edges: {connected_nodes}")

    return nodes, edges