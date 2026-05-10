\# STRUX\_V1 — Near-Parallel Adversarial Benchmark Specification



\## Status



Specification phase only.



This document defines the benchmark design BEFORE implementation.



The objective is to ensure:

\- falsifiability,

\- metric clarity,

\- controlled geometry,

\- explicit failure criteria,

\- explicit non-claims.



\---



\# Benchmark Name



```txt

Near-Parallel Adversarial Benchmark

Scientific Motivation



The current STRUX\_V1 core relies on:



tube-based filament scoring



A major potential failure mode of tube-based methods is:



spurious bridge formation

between nearby but structurally separate filaments



This benchmark is designed to test whether STRUX\_V1:



preserves separation between nearby structures,

or

collapses them into artificial filament connections.

Core Hypothesis



The tested hypothesis is:



STRUX\_V1 should not classify geometrically separate

near-parallel corridors as strong filament connections

above a critical separation distance.



This is a local operational hypothesis only.



This benchmark does NOT test:



universal structure detection;

anisotropy detection in general;

real-world validity;

superiority over all baseline methods.

Benchmark Geometry



The benchmark contains:



two parallel corridor structures;

same length;

same local point density;

same noise model;

same corridor thickness.



The only controlled variable is:



corridor separation distance

Planned Separation Sweep



The planned geometric sweep is:



0.5 × tube\_radius

1.0 × tube\_radius

1.5 × tube\_radius

2.0 × tube\_radius

3.0 × tube\_radius



Additional intermediate values may be added later.



Planned Parameter Stability Sweep



The benchmark must also test:



±20% variation of tube\_radius



around the nominal parameter value.



Reason:



A result valid only for one exact parameter choice is not considered robust.



Main Failure Mode



The primary failure mode is:



STRUX\_V1 creates strong filament bridges

between distinct parallel corridors.



This would indicate that:



proximity dominates structure;

or

tube support geometry is insufficiently selective.

False Positive Definition



A false positive occurs when:



a connection between the two corridors

is classified as:



"strong filament"



despite the corridors being geometrically separate.



False Negative Definition



A false negative occurs when:



a true corridor segment

inside one corridor

is not preserved

because nearby geometry destabilizes scoring.



This benchmark therefore tests BOTH:



over-merging;

corridor erosion.

Primary Metrics

1\. False Bridge Rate



Definition:



(number of strong inter-corridor bridges)

/

(total tested inter-corridor pairs)



Target behavior:



False Bridge Rate ≈ 0

for sufficiently separated corridors

2\. Separation Fidelity



Definition:



minimum corridor separation distance

at which STRUX\_V1 no longer creates strong bridges



Measured in:



units of tube\_radius



This is the main operational metric.



Secondary Metrics



The following secondary metrics should also be logged:



continuity;

coverage;

central\_density\_ratio;

support point count;

final class label:

strong filament

weak filament

none



These metrics should NOT initially be aggregated into a single score.



Planned Baseline Comparisons



The benchmark is expected to later compare STRUX\_V1 against:



MST proximity connection;

DBSCAN;

kNN graph linkage;

density-only heuristics.



These comparisons are NOT part of the first implementation phase.



Honest PASS Criteria



A strong PASS requires:



No strong bridges

for corridor separation ≥ 1.5 × tube\_radius



under:



at least 5 geometric configurations;

±20% parameter variation.



A single successful configuration is NOT considered sufficient.



Honest FAIL Criteria



A strong FAIL occurs if:



STRUX\_V1 systematically creates strong bridges

between separate corridors

above the defined separation threshold.



This would strongly suggest that:



local proximity dominates scoring;

structural separation is not preserved robustly.

Important Non-Claims



Even if the benchmark passes,

the following claims remain INVALID:



"STRUX detects general geometric organization";

"STRUX solves anisotropy detection";

"STRUX surpasses TDA";

"STRUX is validated on real-world data";

"STRUX universally detects structure";

"STRUX is topology invariant."



This benchmark only evaluates:



false bridge resistance

under controlled near-parallel geometry

Implementation Status



Current status:



SPECIFICATION ONLY



Implementation should begin ONLY after:



geometry review;

metric review;

benchmark control review.

