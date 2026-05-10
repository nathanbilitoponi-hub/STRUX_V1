\# STRUX\_V1



Initial frozen public release of STRUX.



DOI:

https://doi.org/10.5281/zenodo.20113740



GitHub:

https://github.com/nathanbilitoponi-hub/STRUX\_V1



\---



\## What is STRUX?



STRUX is an experimental geometric-topological framework for extracting structural organization from point clouds and graph-like systems.



The goal is not classical density estimation, but structural interpretation through:



\* multiscale grouping

\* filament continuity

\* backbone extraction

\* persistence

\* structural comparison



This release is intentionally lightweight and frozen for reproducibility.



\---



\## Included modules



\### 1. Multiscale structural grouping



File:



core/multiscale/multiscale\_life.py



Main function:



run\_strux\_life(...)



Features:



\* radius clustering

\* compactness estimation

\* cut-ratio analysis

\* multiscale promotion

\* hierarchical compression



\---



\### 2. Filament connection scoring



File:



core/connection\_scoring/connection\_scoring.py



Main function:



score\_region\_connections(...)



Features:



\* tube support estimation

\* continuity analysis

\* coverage scoring

\* central density ratio

\* strong/weak filament classification



\---



\### 3. Backbone extraction



File:



core/backbone/backbone\_mst.py



Main function:



extract\_backbone(...)



Features:



\* sparse graph construction

\* MST topology reduction

\* minimal backbone extraction



\---



\### 4. Persistence estimation



File:



core/persistence/persistence.py



Main function:



compute\_edge\_persistence\_advanced(...)



Features:



\* bootstrap edge sampling

\* DBSCAN persistence clustering

\* persistent core extraction



\---



\### 5. Structural comparison



File:



core/compare/structure\_compare.py



Main function:



run\_brain\_v2(...)



Features:



\* node matching

\* edge confirmation

\* local agreement scoring

\* structure comparison



\---



\## Minimal benchmark



Example benchmark:



benchmarks/test\_strux\_v1.py



Current synthetic test:



\* two structural regions

\* filament support

\* backbone extraction

\* persistence detection



\---



\## Install



pip install -r requirements.txt



\---



\## Run benchmark



python benchmarks/test\_strux\_v1.py



\---



\## Status



Experimental research framework.



This repository is a frozen V1 release and does not represent the final STRUX architecture.



\---



\## Author



Nathan Bilitoponi



2026



