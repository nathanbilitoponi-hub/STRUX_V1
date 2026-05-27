"""
MISSION 08B

Progressive attack on Florence OSM

Compare:

STRUX
Betweenness
Random

Metrics:

LCC curve
Efficiency curve
"""

import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import os
import osmnx as ox

FIG="benchmarks/structural_fragility/figures"
RES="benchmarks/structural_fragility/results"

os.makedirs(FIG,exist_ok=True)
os.makedirs(RES,exist_ok=True)

print("="*60)
print("MISSION 08B REAL FLORENCE")
print("="*60)

# ------------------------------------------------
# load STRUX top edges
# ------------------------------------------------

df=pd.read_csv(
    "examples/florence_osm/output/firenze_top20_strux_edges.csv"
)

# ------------------------------------------------
# load graph
# ------------------------------------------------

CENTER=(43.7696,11.2558)

G=ox.graph_from_point(
    CENTER,
    dist=1800,
    network_type="drive",
    simplify=True
)

G=ox.project_graph(G)
G=G.to_undirected()

print(
f"Nodes:{G.number_of_nodes()}"
)

print(
f"Edges:{G.number_of_edges()}"
)

# ------------------------------------------------
# STRUX nodes
# ------------------------------------------------

strux_nodes=[]

for _,r in df.iterrows():

    strux_nodes.append(r["u"])
    strux_nodes.append(r["v"])

strux_nodes=list(
dict.fromkeys(strux_nodes)
)

# ------------------------------------------------
# Betweenness
# ------------------------------------------------

bet=nx.betweenness_centrality(
    G,
    weight="length"
)

bet_nodes=sorted(
    bet,
    key=bet.get,
    reverse=True
)

# ------------------------------------------------
# Random
# ------------------------------------------------

rng=np.random.default_rng(7)

rand_nodes=list(
G.nodes()
)

rng.shuffle(
rand_nodes
)

# ------------------------------------------------

def metrics(H):

    comps=list(
        nx.connected_components(H)
    )

    lcc=max(
        len(c)
        for c in comps
    )/H.number_of_nodes()

    try:

        eff=nx.global_efficiency(H)

    except:

        eff=0

    return lcc,eff


# ------------------------------------------------

damage_levels=[
5,
10,
20,
40,
60,
80
]

rows=[]

for nremove in damage_levels:

    print()
    print(
    "Damage:",
    nremove
    )

    for method,nodes in [

        ("STRUX",strux_nodes),
        ("Betweenness",bet_nodes),
        ("Random",rand_nodes)

    ]:

        H=G.copy()

        for n in nodes[:nremove]:

            if H.has_node(n):

                H.remove_node(
                    n
                )

        L,E=metrics(H)

        rows.append({

            "damage":nremove,
            "method":method,
            "LCC":L,
            "efficiency":E

        })

        print(
        method,
        "LCC=",
        round(L,4),
        "EFF=",
        round(E,4)
        )

# ------------------------------------------------

res=pd.DataFrame(rows)

res.to_csv(

os.path.join(
RES,
"real_florence_attack_08B.csv"
),

index=False
)

# ------------------------------------------------

plt.figure(figsize=(8,5))

for m in res.method.unique():

    sub=res[
        res.method==m
    ]

    plt.plot(
        sub.damage,
        sub.LCC,
        "-o",
        label=m
    )

plt.xlabel(
"nodes removed"
)

plt.ylabel(
"LCC"
)

plt.legend()

plt.savefig(

os.path.join(
FIG,
"real_florence_attack_08B_lcc.png"
),

dpi=220
)

plt.close()

# ------------------------------------------------

plt.figure(figsize=(8,5))

for m in res.method.unique():

    sub=res[
        res.method==m
    ]

    plt.plot(
        sub.damage,
        sub.efficiency,
        "-o",
        label=m
    )

plt.xlabel(
"nodes removed"
)

plt.ylabel(
"global efficiency"
)

plt.legend()

plt.savefig(

os.path.join(
FIG,
"real_florence_attack_08B_efficiency.png"
),

dpi=220
)

plt.close()

print()
print("="*60)
print("Saved")
print("="*60)

print(
"real_florence_attack_08B.csv"
)

print(
"real_florence_attack_08B_lcc.png"
)

print(
"real_florence_attack_08B_efficiency.png"
)