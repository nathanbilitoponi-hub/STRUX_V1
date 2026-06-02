````md

\# Florence OSM Example



Real-world STRUX\_V1 test on the Florence (Italy) road network using OpenStreetMap data.



This example compares:



\- STRUX geometric corridor continuity

\- edge betweenness centrality baseline



The goal is not to replace betweenness centrality, but to test whether

geometric continuity and distributed corridor support reveal different

structural information.



\---



\## Outputs



The script generates:



\- `output/firenze\_strux\_corridor\_test.png`

\- `output/firenze\_top20\_strux\_edges.csv`

\- `output/firenze\_overlap\_summary.csv`



\---



\## What STRUX measures here



For each road segment:



1\. a geometric tube is constructed around the edge axis;

2\. nearby nodes are projected along the corridor direction;

3\. continuity is estimated using:

&#x20;  - maximum-gap continuity,

&#x20;  - KS-based uniformity continuity;

4\. the final corridor score is:



```text

score = continuity \* log(1 + support\_count)

````



where:



```text

continuity = min(continuity\_gap, continuity\_KS)

```



This penalizes:



\* local dense clusters,

\* discontinuous corridors,

\* fragmented support.



\---



\## Comparison with Betweenness



The right panel of the figure shows standard edge betweenness centrality.



Betweenness measures:



\* shortest-path flow concentration.



STRUX measures:



\* geometric corridor support and continuity.



Overlap between the two rankings is exported in:



```text

output/firenze\_overlap\_summary.csv

```



\---



\## Run



```bash

pip install osmnx networkx geopandas scipy pandas matplotlib

python florence\_analysis.py

```



\---



\## Notes



This is an experimental STRUX\_V1 example.



It does NOT represent:



\* a complete STRUX pipeline,

\* an urban-planning tool,

\* or a validated infrastructure risk system.



The purpose is to provide:



\* a real-world benchmark,

\* a reproducible geometric experiment,

\* and a comparison against standard network metrics.



\---



\## Project



STRUX\_V1 — Axial Support Framework



GitHub:

\[https://github.com/nathanbilitoponi-hub/STRUX\_V1](https://github.com/nathanbilitoponi-hub/STRUX\_V1)



DOI:

\[https://doi.org/10.5281/zenodo.20113740](https://doi.org/10.5281/zenodo.20113740)



Data:

© OpenStreetMap contributors



```

```



