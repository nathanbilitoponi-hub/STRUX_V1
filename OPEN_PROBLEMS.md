\# STRUX\_V1 — OPEN PROBLEMS



Purpose:

Track active unresolved problems.



This file prevents:

\- circular development,

\- repeated failed directions,

\- loss of conceptual continuity.



\---



\# 1. REAL-WORLD TRANSPORT VALIDATION



STATUS:

OPEN



Problem:

Current transport diagnosis is validated only on synthetic systems.



Need:

Apply:

\- gate mode count,

\- branching diagnosis,

\- coherence/completion logic



to:

\- real transport networks,

\- road systems,

\- biological structures,

\- spatial graphs.



\---



\# 2. AUTOMATIC GATE PLACEMENT



STATUS:

OPEN



Problem:

Current gate-based diagnostics depend on manually selected gate position.



Need:

Automatic detection of:

\- bottlenecks,

\- branching interfaces,

\- transport cross-sections.



\---



\# 3. GENERALIZED BRANCHING METRICS



STATUS:

OPEN



Problem:

Current branching observable counts modes in 1D gate distributions.



Need:

More general:

\- topological branching,

\- persistent transport families,

\- graph-based transport modes.



Possible directions:

\- Reeb-like structures

\- Morse-inspired transport analysis

\- spectral transport decomposition



\---



\# 4. REAL NOISE ROBUSTNESS



STATUS:

PARTIALLY TESTED



Problem:

Synthetic systems remain relatively clean.



Need:

Stress tests under:

\- missing data,

\- outliers,

\- irregular geometry,

\- heavy perturbations.



\---



\# 5. LOCAL ↔ GLOBAL BRIDGE



STATUS:

OPEN



Core scientific question:



Can local geometric organization

predict global transport behavior?



This remains one of the central unresolved questions of STRUX.



\---



\# 6. OBSERVABLE STABILITY



STATUS:

OPEN



Need:

Determine which observables remain:

\- stable,

\- interpretable,

\- reproducible



across:

\- scale,

\- noise,

\- topology variation,

\- dataset type.



\---



\# 7. REAL STRUCTURAL USE CASES



STATUS:

OPEN



Need:

Identify practical applications where STRUX provides information not captured by:

\- betweenness,

\- classical centrality,

\- simple clustering,

\- shortest-path metrics.



Potential domains:

\- infrastructure

\- resilience

\- transport systems

\- spatial diagnosis

\- biological geometry



\---



\# IMPORTANT RULE



Open problems must remain explicit.



Do NOT silently assume:

\- unresolved problems are solved,

\- synthetic success implies universal validity,

\- classification implies theory.

---

# BASELINE COMPARISON NOT YET PERFORMED

STATUS:
OPEN CRITICAL VALIDATION

Current STRUX transport benchmarks have not yet been compared against:

- A* shortest-path
- RRT (Rapidly-exploring Random Trees)
- diffusion/random-walk baselines

Current results validate behavior of the constrained ray propagation model,
but do NOT yet demonstrate superiority or uniqueness relative to standard pathfinding methods.

Critical next step:
compare STRUX observables against baseline transport/pathfinding systems
on identical synthetic geometries.

Main risk:
current observables may partially reflect generic geometric traversal difficulty
rather than STRUX-specific transport structure.