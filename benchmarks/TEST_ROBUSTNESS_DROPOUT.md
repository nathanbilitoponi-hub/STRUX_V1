\# STRUX\_V1 — Robustness Dropout Benchmark



\## Goal



Evaluate whether STRUX\_V1 filament scoring remains stable under random point removal.



This benchmark tests whether a real corridor-supported structure continues to be classified as a strong filament when increasing fractions of points are randomly removed.



This is a controlled synthetic robustness test.



It is NOT a real-world validation benchmark.



\---



\# Benchmark Structure



The synthetic dataset contains:



\- blob A

\- blob B

\- a real noisy corridor connecting them

\- additional off-axis noise



A filament connection is evaluated between the two blobs.



Random dropout is then applied globally to the point cloud.



\---



\# Dropout Levels



The following random point removal levels are tested:



```txt

0%

10%

20%

30%

40%

50%



For each level, STRUX evaluates:



continuity

coverage

central density ratio

filament class

Expected Behavior



The corridor-supported structure should remain detectable as:



strong filament



under moderate dropout.



If the structure collapses too early, the scoring method is considered fragile.



Observed Result



Observed benchmark output:



dropout=0.0 -> strong filament

dropout=0.1 -> strong filament

dropout=0.2 -> strong filament

dropout=0.3 -> strong filament

dropout=0.4 -> strong filament

dropout=0.5 -> strong filament



Important observation:



continuity remained equal to 1.000

across all tested dropout levels.



Coverage decreased progressively, as expected.



Interpretation



This benchmark suggests that the STRUX\_V1 tube-based scoring remains stable under substantial random point removal in a controlled synthetic corridor setting.



The result indicates that:



distributed corridor occupancy

is robust to random sparsification

in this synthetic scenario.

What This Benchmark Demonstrates



This benchmark demonstrates:



robustness of continuity occupancy under random dropout;

stability of tube-supported filament detection;

graceful degradation of coverage under sparsification.

What This Benchmark Does NOT Demonstrate



This benchmark does NOT demonstrate:



universal robustness;

robustness to structured adversarial damage;

real-world predictive validity;

topological persistence;

superiority over graph-theoretic baselines;

robustness under anisotropic collapse;

correctness on SDSS or transport datasets.



This is only a controlled synthetic robustness benchmark.



Important Limitation



The current benchmark removes points uniformly at random.



This is easier than:



corridor-targeted attacks;

bridge destruction;

directional collapse;

structured fragmentation.



Future robustness tests should include:



corridor-targeted dropout;

local bridge removal;

anisotropic degradation;

clustered noise.

Related Files

benchmarks/test\_robustness\_dropout.py

core/connection\_scoring/connection\_scoring.py

ALGORITHM\_DECISIONS.md

Current Status



Benchmark status:



PASS



Reason:



The corridor-supported structure remained classified as:



strong filament



even under 50% random point dropout.

