"""
MISSION 07

Damage progression
"""

import numpy as np
import networkx as nx
import random

rng=np.random.default_rng(7)

G=nx.barabasi_albert_graph(
    120,
    3,
    seed=7
)

# baseline

base=nx.betweenness_centrality(G)

scores=[]

print()
print("="*60)
print("MISSION 07 DAMAGE PROGRESSION")
print("="*60)

for damage in range(0,31):

    H=G.copy()

    edges=list(H.edges())

    random.seed(damage)

    remove=random.sample(
        edges,
        damage
    )

    H.remove_edges_from(
        remove
    )

    if H.number_of_edges()==0:
        continue

    bet=nx.betweenness_centrality(H)

    # STRUX proxy:
    # instability in topology

    delta=[]

    for n in H.nodes():

        if n in base:

            delta.append(
                abs(
                    bet.get(n,0)
                    -
                    base[n]
                )
            )

    signal=np.mean(delta)

    lcc=max(
        len(c)
        for c in nx.connected_components(H)
    )/H.number_of_nodes()

    scores.append(
        (
            damage,
            signal,
            lcc
        )
    )

scores=np.array(scores)

peak_damage=scores[
np.argmax(scores[:,1]),
0
]

collapse_damage=scores[
np.argmin(scores[:,2]),
0
]

print()
print(
"Peak STRUX signal:",
peak_damage
)

print(
"Strongest LCC damage:",
collapse_damage
)

print()

if peak_damage<collapse_damage:

    print(
    "PASS: STRUX reacts before collapse"
    )

else:

    print(
    "FAIL: STRUX reacts after collapse"
    )