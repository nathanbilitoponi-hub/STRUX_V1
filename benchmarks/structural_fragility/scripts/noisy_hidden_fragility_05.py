"""
MISSION 05

Noisy Hidden Fragility
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import random
import os

FIG="benchmarks/structural_fragility/figures"

os.makedirs(FIG,exist_ok=True)

rng=np.random.default_rng(7)

G=nx.Graph()
pos={}

left=[]
right=[]
weak=[]

# ------------------------------------------------
# dense clusters
# ------------------------------------------------

for i in range(25):

    n=f"L{i}"

    left.append(n)

    pos[n]=(
        rng.normal(-2,.6),
        rng.normal(0,.6)
    )

    G.add_node(n)

for i in range(25):

    n=f"R{i}"

    right.append(n)

    pos[n]=(
        rng.normal(2,.6),
        rng.normal(0,.6)
    )

    G.add_node(n)

# ------------------------------------------------
# hidden weak zone
# ------------------------------------------------

for i in range(6):

    n=f"W{i}"

    weak.append(n)

    pos[n]=(
        -0.7+i*.35+rng.normal(0,.05),
        1.1+rng.normal(0,.15)
    )

    G.add_node(n)

truth=set(weak)

# ------------------------------------------------
# local edges
# ------------------------------------------------

nodes=list(G.nodes())

for i in range(len(nodes)):

    for j in range(i+1,len(nodes)):

        p1=np.array(pos[nodes[i]])
        p2=np.array(pos[nodes[j]])

        d=np.linalg.norm(p1-p2)

        if d<.7:

            G.add_edge(
                nodes[i],
                nodes[j]
            )

# weak chain

for i in range(len(weak)-1):

    G.add_edge(
        weak[i],
        weak[i+1]
    )

# attach weak zone

G.add_edge(left[4],weak[0])
G.add_edge(weak[-1],right[4])

# ------------------------------------------------
# noise edges
# ------------------------------------------------

all_nodes=list(G.nodes())

for _ in range(30):

    a=random.choice(all_nodes)
    b=random.choice(all_nodes)

    if a!=b:

        G.add_edge(a,b)

# ------------------------------------------------
# STRUX proxy
# ------------------------------------------------

bet=nx.betweenness_centrality(G)

cl=nx.clustering(G)

art=set(
    nx.articulation_points(G)
)

score={}

for n in G.nodes():

    score[n]=(
        .2*bet[n]
        +
        .4*(1-cl[n])
        +
        .4*(n in art)
    )

rank=sorted(
    score,
    key=score.get,
    reverse=True
)

top=set(rank[:6])

tp=len(
top & truth
)

precision=tp/6
recall=tp/6

print()
print("="*60)
print("MISSION 05")
print("="*60)

print()

print(
"Top nodes:"
)

print(rank[:12])

print()

print(
"precision:",
round(
precision,
3
)
)

print(
"recall:",
round(
recall,
3
)
)

if precision>.15:

    print()
    print(
    "PASS: signal survives noise"
    )

else:

    print()
    print(
    "FAIL: noise destroys signal"
    )

plt.figure(figsize=(8,6))

scores=np.array(
[
score[n]
for n in G.nodes()
]
)

nx.draw_networkx_edges(
G,pos,alpha=.2
)

nx.draw_networkx_nodes(
G,
pos,
node_color=scores,
cmap="magma",
node_size=90
)

nx.draw_networkx_nodes(
G,
pos,
nodelist=list(truth),
node_color="none",
edgecolors="cyan",
linewidths=2,
node_size=250
)

plt.axis("off")

plt.savefig(
f"{FIG}/mission05_noise.png",
dpi=220
)

plt.close()