"""
MISSION 08C

Spatial difference:
STRUX vs Betweenness

Question:

Do they identify different regions
of the city?
"""

import os
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import osmnx as ox

FIG="benchmarks/structural_fragility/figures"
RES="benchmarks/structural_fragility/results"

os.makedirs(FIG,exist_ok=True)
os.makedirs(RES,exist_ok=True)

print("="*60)
print("MISSION 08C")
print("="*60)

# ------------------------------------------------
# graph
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

# node positions

pos={}

for n,data in G.nodes(data=True):

    pos[n]=(
        data["x"],
        data["y"]
    )

# ------------------------------------------------
# STRUX nodes
# ------------------------------------------------

df=pd.read_csv(
"examples/florence_osm/output/firenze_top20_strux_edges.csv"
)

strux_nodes=[]

for _,r in df.iterrows():

    strux_nodes.append(r["u"])
    strux_nodes.append(r["v"])

strux_nodes=list(
dict.fromkeys(strux_nodes)
)

# ------------------------------------------------
# Betweenness nodes
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

bet_nodes=bet_nodes[:len(strux_nodes)]

# ------------------------------------------------

overlap=set(
strux_nodes
)&set(
bet_nodes
)

only_strux=set(
strux_nodes
)-overlap

only_bet=set(
bet_nodes
)-overlap

print()

print(
"STRUX nodes:",
len(strux_nodes)
)

print(
"Betweenness nodes:",
len(bet_nodes)
)

print(
"Overlap:",
len(overlap)
)

print(
"Overlap ratio:",
round(
len(overlap)/len(strux_nodes),
3
)
)

# ------------------------------------------------

plt.figure(
figsize=(11,9)
)

nx.draw_networkx_edges(
G,
pos,
alpha=0.05
)

# only STRUX

nx.draw_networkx_nodes(
G,
pos,
nodelist=list(
only_strux
),
node_color="red",
node_size=35,
label="STRUX only"
)

# only bet

nx.draw_networkx_nodes(
G,
pos,
nodelist=list(
only_bet
),
node_color="blue",
node_size=35,
label="Betweenness only"
)

# overlap

nx.draw_networkx_nodes(
G,
pos,
nodelist=list(
overlap
),
node_color="lime",
node_size=55,
label="Overlap"
)

plt.legend()

plt.title(
"MISSION 08C STRUX vs Betweenness"
)

plt.axis(
"off"
)

outfile=os.path.join(
FIG,
"real_florence_overlap_08C.png"
)

plt.savefig(
outfile,
dpi=220,
bbox_inches="tight"
)

plt.close()

pd.DataFrame({

"metric":[
"strux_nodes",
"bet_nodes",
"overlap",
"overlap_ratio"
],

"value":[
len(strux_nodes),
len(bet_nodes),
len(overlap),
len(overlap)/len(strux_nodes)
]

}).to_csv(

os.path.join(
RES,
"real_florence_overlap_08C.csv"
),

index=False
)

print()
print("Saved:")
print(outfile)