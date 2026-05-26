"""
MISSION 04

False Positive Test

Network:

cluster ---- corridor ---- cluster
            |
      rami strani laterali

MA:

i rami hanno molte connessioni ridondanti

Quindi:

sembrano fragili geometricamente
ma NON lo sono realmente
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os

FIG="benchmarks/structural_fragility/figures"

os.makedirs(FIG,exist_ok=True)

rng=np.random.default_rng(7)

G=nx.Graph()
pos={}

left=[]
right=[]
branch=[]

# -----------------------
# clusters
# -----------------------

for i in range(25):

    n=f"L{i}"

    left.append(n)

    pos[n]=(
        rng.normal(-2,.5),
        rng.normal(0,.5)
    )

    G.add_node(n)

for i in range(25):

    n=f"R{i}"

    right.append(n)

    pos[n]=(
        rng.normal(2,.5),
        rng.normal(0,.5)
    )

    G.add_node(n)

# corridor

corr=[]

for i in range(8):

    n=f"C{i}"

    corr.append(n)

    pos[n]=(
        -1.4+i*.4,
        rng.normal(0,.05)
    )

    G.add_node(n)

# fake fragile branch

for i in range(8):

    n=f"F{i}"

    branch.append(n)

    pos[n]=(
        -0.8+i*.25,
        1+rng.normal(0,.1)
    )

    G.add_node(n)

# -----------------------
# local dense links
# -----------------------

for block in [left,right]:

    for i in range(len(block)):
        for j in range(i+1,len(block)):

            d=np.linalg.norm(
                np.array(pos[block[i]])
                -
                np.array(pos[block[j]])
            )

            if d<.8:

                G.add_edge(
                    block[i],
                    block[j]
                )

# corridor

for i in range(len(corr)-1):

    G.add_edge(
        corr[i],
        corr[i+1]
    )

# connect

G.add_edge(left[0],corr[0])
G.add_edge(right[0],corr[-1])

# branch chain

for i in range(len(branch)-1):

    G.add_edge(
        branch[i],
        branch[i+1]
    )

# MANY redundant links
# makes branch robust

for i in range(len(branch)-2):

    G.add_edge(
        branch[i],
        branch[i+2]
    )

for i in range(4):

    G.add_edge(
        branch[i],
        corr[i+2]
    )

# -----------------------
# STRUX proxy
# -----------------------

bet=nx.betweenness_centrality(G)

cl=nx.clustering(G)

art=set(
    nx.articulation_points(G)
)

score={}

for n in G.nodes():

    score[n]=(
        .4*bet[n]
        +
        .4*(1-cl[n])
        +
        .2*(n in art)
    )

rank=sorted(
    score,
    key=score.get,
    reverse=True
)

print()
print("="*60)
print("MISSION 04 FALSE POSITIVE")
print("="*60)

print()
print(
"Top STRUX:"
)

print(
rank[:12]
)

fake_detected=len(
[
n for n in rank[:8]
if n.startswith("F")
]
)

print()
print(
"Fake branch detected:",
fake_detected
)

if fake_detected<=2:

    print()
    print(
    "PASS: STRUX ignores fake geometry"
    )

else:

    print()
    print(
    "FAIL: STRUX hallucinating fragility"
    )

plt.figure(figsize=(8,6))

scores=np.array(
[
score[n]
for n in G.nodes()
]
)

nx.draw_networkx_edges(
G,pos,alpha=.3
)

nx.draw_networkx_nodes(
G,
pos,
node_color=scores,
cmap="magma",
node_size=100
)

plt.axis("off")

plt.savefig(
f"{FIG}/false_positive_04.png",
dpi=220
)

plt.close()