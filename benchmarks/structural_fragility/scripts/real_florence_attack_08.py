"""
MISSION 08A

Florence OSM attack test

Compare:

STRUX
Betweenness
Random

Metrics:

LCC
Global efficiency
"""

import pandas as pd
import networkx as nx
import numpy as np
import os
import matplotlib.pyplot as plt

print("="*60)
print("MISSION 08A REAL FLORENCE")
print("="*60)

csv="examples/florence_osm/output/firenze_top20_strux_edges.csv"

df=pd.read_csv(csv)

# load graph again
import osmnx as ox

CENTER=(43.7696,11.2558)

G=ox.graph_from_point(
    CENTER,
    dist=1800,
    network_type="drive",
    simplify=True
)

G=ox.project_graph(G)
G=G.to_undirected()

# -------------------------
# STRUX nodes
# -------------------------

strux_nodes=[]

for _,r in df.iterrows():

    strux_nodes.append(r["u"])
    strux_nodes.append(r["v"])

strux_nodes=list(dict.fromkeys(strux_nodes))

# -------------------------
# Betweenness
# -------------------------

bet=nx.betweenness_centrality(
    G,
    weight="length"
)

bet_nodes=sorted(
    bet,
    key=bet.get,
    reverse=True
)

# -------------------------
# Random
# -------------------------

rng=np.random.default_rng(7)

rand_nodes=list(G.nodes())

rng.shuffle(rand_nodes)

# -------------------------

def attack(G,nodes,nremove=20):

    H=G.copy()

    for n in nodes[:nremove]:

        if H.has_node(n):

            H.remove_node(n)

    lcc=max(
        len(c)
        for c in nx.connected_components(H)
    )/H.number_of_nodes()

    try:

        eff=nx.global_efficiency(H)

    except:

        eff=0

    return lcc,eff

# -------------------------

L_s,E_s=attack(
    G,
    strux_nodes
)

L_b,E_b=attack(
    G,
    bet_nodes
)

L_r,E_r=attack(
    G,
    rand_nodes
)

res=pd.DataFrame({

"method":[
"STRUX",
"Betweenness",
"Random"
],

"LCC":[
L_s,
L_b,
L_r
],

"efficiency":[
E_s,
E_b,
E_r
]

})

print()
print(res)

plt.figure(figsize=(8,5))

x=np.arange(3)

plt.bar(
x,
res["LCC"]
)

plt.xticks(
x,
res["method"]
)

plt.ylabel(
"Final LCC"
)

plt.savefig(
"benchmarks/structural_fragility/figures/real_florence_attack_08_lcc.png",
dpi=220
)

plt.close()

print()
print("Saved:")
print("real_florence_attack_08_lcc.png")