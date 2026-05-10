\# STRUX\_V1 — Parameter Stability Benchmark



\## Goal



Evaluate how sensitive STRUX\_V1 filament scoring is to changes in the geometric tube radius parameter.



This benchmark tests whether the detected filament structure remains stable under moderate parameter variation.



The objective is to evaluate whether STRUX behaves as:



```txt

robust structural detection



or merely as:



parameter fine-tuning

Benchmark Structure



The synthetic dataset contains:



blob A

blob B

a real noisy corridor connecting them

off-axis noise



A filament connection is evaluated between the two blobs.



The tube radius parameter is then varied across a broad range.



Tested Parameter Range

tube\_radius =

0.10

0.15

0.20

0.25

0.30

0.35

0.45

0.60



For each value, STRUX evaluates:



continuity

coverage

central density ratio

filament classification

Expected Behavior



A robust filament detector should preserve:



strong filament



classification across moderate parameter changes.



A fragile detector would rapidly change classification under small parameter variation.



Observed Result



Observed benchmark output:



tube\_radius=0.10 -> strong filament

tube\_radius=0.15 -> strong filament

tube\_radius=0.20 -> strong filament

tube\_radius=0.25 -> strong filament

tube\_radius=0.30 -> strong filament

tube\_radius=0.35 -> strong filament

tube\_radius=0.45 -> strong filament

tube\_radius=0.60 -> strong filament



Most important observation:



continuity remained equal to 1.000

across the entire tested parameter range.



Coverage and central density increased progressively with larger tube radius, as expected.



Interpretation



This benchmark suggests that the STRUX\_V1 tube-based filament scoring is NOT catastrophically unstable under moderate parameter variation in a clean corridor-supported synthetic scenario.



Observed behavior:



tube radius changes

→ support density changes

→ continuity remains stable



This is an important distinction.



The structural interpretation remained stable while geometric support statistics evolved smoothly.



What This Benchmark Demonstrates



This benchmark demonstrates:



stable continuity occupancy;

smooth geometric response to parameter variation;

non-fragile filament classification in a clean synthetic scenario.

What This Benchmark Does NOT Demonstrate



This benchmark does NOT demonstrate:



universal parameter invariance;

robustness in adversarial geometry;

robustness under bifurcations;

robustness under curved corridors;

robustness under competing nearby corridors;

real-world dataset stability;

superiority over TDA baselines.



This is only a controlled synthetic parameter-sensitivity benchmark.



Important Limitation



The tested geometry is relatively easy:



single corridor

no branching

low ambiguity

clean topology



Future tests should include:



bifurcations;

near-parallel corridors;

partial bridges;

noisy competing structures;

curved filaments;

adversarial clutter.

Related Files

benchmarks/test\_parameter\_stability.py

core/connection\_scoring/connection\_scoring.py

ALGORITHM\_DECISIONS.md

Current Status



Benchmark status:



PASS STRONG



Reason:



The corridor-supported structure remained classified as:



strong filament



across the full tested parameter range while continuity remained stable.

