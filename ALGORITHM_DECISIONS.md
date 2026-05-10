# STRUX_V1 — Algorithm Decisions Log

This file records why each algorithmic choice exists in STRUX_V1.

Purpose:
- avoid re-discussing the same decisions repeatedly;
- help external AI/reviewers understand what is intentional, provisional, or known-limited;
- keep STRUX_V1 technically honest.

---

## 1. Why STRUX_V1 uses a minimal operational pipeline

STRUX_V1 is not the final STRUX theory.

It is a frozen operational baseline.

Current pipeline:

```txt
point cloud
→ multiscale grouping
→ region centers
→ filament connection scoring
→ MST backbone
→ persistence estimate
→ visualization / report
````

Reason:

Before adding advanced theory, STRUX needed one reproducible end-to-end pipeline that actually runs.

This version prioritizes:

* reproducibility;
* interpretability;
* modularity;
* simple debugging;
* external review.

Do not interpret STRUX_V1 as the final scientific architecture.

---

## 2. Why radius-based multiscale clustering is used

File:

```txt
core/multiscale/multiscale_life.py
```

Decision:

STRUX_V1 uses radius-based clustering through `cKDTree`.

Reason:

It is simple, deterministic, fast, and easy to inspect.

Why not use a more advanced method yet?

Because in V1 we needed a transparent baseline before adding:

* adaptive kNN;
* density-aware clustering;
* persistent clustering;
* learned clustering;
* void-aware clustering.

Known limitation:

The result depends strongly on `base_radius`.

Current status:

Useful operational baseline, not final scale theory.

V2 should replace fixed radius logic with adaptive scale detection.

---

## 3. Why `compute_branch_degree` is provisional

File:

```txt
core/multiscale/multiscale_life.py
```

Decision:

`compute_branch_degree` estimates directional spread using outer vectors from the cluster center.

Reason:

It gives a quick proxy for whether a cluster is blob-like, branch-like, or multi-directional.

Known limitation:

It is heuristic and can overestimate branches in noisy clouds.

Do not overclaim it as true topology.

Current status:

Diagnostic only.

V2 should replace it with a more stable local graph-based or PCA/angle-based branch estimator.

---

## 4. Why tube-based filament scoring is used

File:

```txt
core/connection_scoring/connection_scoring.py
```

Decision:

Connections between regions are scored using a tube around the segment connecting two centers.

Metrics:

* support points inside tube;
* continuity along the segment;
* coverage;
* central density ratio.

Reason:

This is the strongest operational module in STRUX_V1.

It checks whether a proposed connection is geometrically supported by actual points, not only by distance between centers.

Why this matters:

Two regions can be close but not structurally connected.
Tube scoring checks whether there is material/path support between them.

Known limitation:

`tube_radius` is fixed and dataset-dependent.

Current status:

Core STRUX_V1 operational component.

V2 should make `tube_radius` adaptive to local density/scale.

---

## 5. Why strong/weak filament labels are used

File:

```txt
core/connection_scoring/connection_scoring.py
```

Decision:

Connections are classified as:

```txt
strong filament
weak filament
none
```

Reason:

STRUX_V1 needs interpretable output, not only numbers.

A strong filament requires:

* sufficient continuity;
* sufficient coverage;
* nonzero central density support.

Known limitation:

Thresholds are heuristic:

```txt
strong_continuity_thr = 0.6
weak_continuity_thr = 0.4
strong_coverage_thr = 0.5
strong_central_ratio_thr = 0.08
```

Current status:

Useful for V1 benchmarking.

V2 should calibrate thresholds on synthetic ground-truth datasets and real datasets.

---

## 6. Why MST is used for backbone extraction

File:

```txt
core/backbone/backbone_mst.py
```

Decision:

STRUX_V1 uses Minimum Spanning Tree as the first backbone reducer.

Reason:

MST provides a minimal, deterministic, reproducible backbone baseline.

It is used because V1 needed a stable topology reduction method.

Important:

MST is NOT claimed as the final or best STRUX backbone.

Known limitation:

MST removes cycles and therefore removes redundancy.

This is dangerous if the goal is redundancy analysis.

Current status:

Baseline only.

V2 should compare MST with:

* confidence-weighted backbone;
* k-core / 2-core extraction;
* persistent backbone;
* cycle-preserving skeleton;
* graph sparsification methods.

Do not claim novelty from MST.

---

## 7. Why persistence currently uses midpoint clustering

File:

```txt
core/persistence/persistence.py
```

Decision:

Edge persistence is estimated by repeatedly sampling edges and clustering their midpoints with DBSCAN.

Reason:

A robust topological edge-matching method was not yet available.

Midpoint clustering gives a quick operational proxy for whether similar edges repeatedly appear.

Known limitation:

This is not true topological persistence.

It ignores:

* edge orientation;
* endpoint identity;
* local topology;
* graph role;
* equivalence of alternative paths.

Current status:

Prototype persistence diagnostic.

V2 should replace this with a richer edge signature:

```txt
midpoint
+ direction
+ length
+ endpoint roles
+ local degree
+ edge confidence
+ graph context
```

Do not overclaim current persistence as rigorous topology.

---

## 8. Why structure comparison uses greedy node matching

File:

```txt
core/compare/structure_compare.py
```

Decision:

`match_nodes` uses nearest-node greedy matching under tolerance.

Reason:

It is simple and sufficient for V1 comparison tests.

Use cases:

* compare STRUX vs VOID;
* compare run A vs run B;
* compare predicted vs observed nodes;
* compare two structural readings.

Known limitation:

Greedy matching is not globally optimal.

It can fail when nodes are dense or ambiguous.

Current status:

Diagnostic only.

V2 should replace with:

* Hungarian matching;
* graph-aware matching;
* local signature matching;
* topology-preserving matching.

---

## 9. Why reconnect logic is excluded from V1

Decision:

Reconnect/component merge is not included in STRUX_V1.

Reason:

Reconnect can invent structure if too aggressive.

In earlier experiments, reconnect was useful but risky.

Current rule:

V1 must not automatically reconnect fragmented structures unless connection support is explicitly scored.

Reconnect belongs in V2 only if:

* every inferred edge is marked as inferred;
* confidence is reported;
* geometry support is checked;
* false reconnect tests are included.

---

## 10. Why VOID-first logic is excluded from V1

Decision:

VOID-first modules are not included in STRUX_V1.

Reason:

VOID-first is a larger theoretical direction and would change the core interpretation.

STRUX_V1 is an operational point-cloud/backbone baseline.

VOID-first should remain separate until validated.

Future structure:

```txt
STRUX_V1      = operational backbone/scoring baseline
STRUX_VOID    = void/cavity-first experimental branch
STRUX_BENCH   = validation benchmarks
STRUX_THEORY  = formal pathway/redundancy theory
```

Do not merge VOID-first into V1 without controlled validation.

---

## 11. What STRUX_V1 does not claim

STRUX_V1 does NOT claim:

* new physics;
* universal collapse law;
* final STRUX theory;
* best backbone extraction algorithm;
* rigorous topological persistence;
* validated real-world predictive power;
* replacement for spectral graph theory;
* replacement for percolation theory;
* replacement for Ricci curvature methods.

STRUX_V1 claims only:

```txt
a minimal reproducible operational pipeline for
multiscale grouping, filament scoring, backbone extraction,
persistence estimation, and structural comparison.
```

---

## 12. What was verified

Current verified first-pass benchmark:

```txt
dataset points: 740
large regions: 2
strong filaments: 1
MST edges: 1
persistent clusters: 1
persistent core: 1
```

This verifies that the pipeline runs end-to-end.

It does NOT verify scientific generalization.

---

## 13. What must be tested next

Before STRUX_V1 becomes scientifically stronger, it needs:

1. Synthetic ground-truth benchmark

   * known filaments;
   * known noise;
   * known voids;
   * precision/recall.

2. Robustness benchmark

   * remove 10%, 20%, 30% points;
   * measure backbone stability.

3. Parameter sensitivity

   * base_radius sweep;
   * tube_radius sweep;
   * threshold sweep.

4. Real dataset test

   * SDSS point cloud;
   * OSM/transport network;
   * floorplan/skeleton dataset.

5. Comparison baselines

   * MST alone;
   * kNN graph;
   * DBSCAN;
   * betweenness;
   * λ₂;
   * Ricci proxy.

---

## 14. What V2 should improve

STRUX_V2 should focus only on verified improvements:

* adaptive scale selection;
* adaptive tube radius;
* better branch degree estimator;
* robust edge persistence;
* topology-aware structure comparison;
* optional conservative reconnect;
* quantitative benchmarks;
* export/report improvements.

Do not add speculative theory before these are tested.

---

## 15. Review rule for external AI

When reviewing STRUX_V1, do not ask:

```txt
Is STRUX a new theory of physics?
```

Ask instead:

```txt
Is this pipeline coherent, reproducible, and useful as an operational baseline?
Which algorithmic choices are weak?
Which choices are justified?
Which modules should be replaced first?
What benchmark would falsify the current approach?
```

STRUX_V1 should be criticized as an experimental computational framework.

---

## 16. Current scientific center

The broader STRUX research direction is:

```txt
pathway dynamics may contain structural information
not encoded in final topology alone.
```

But STRUX_V1 does not prove that yet.

STRUX_V1 only provides the first operational base needed to test that claim.

````