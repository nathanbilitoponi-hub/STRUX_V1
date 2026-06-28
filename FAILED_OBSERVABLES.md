\# STRUX\_V1 — FAILED OBSERVABLES



Purpose:

Track observables and metrics that failed validation,

including WHY they failed.



This file is critical to avoid repeating invalid directions.



\---



\# TRANSPORT DIAGNOSIS FAILURES



\## 1. Persistence



STATUS:

FAILED



Problem:

High persistence can emerge from trapped systems.



Example:

A sealed corridor can produce long-lived trajectories

without successful transport completion.



Conclusion:

Persistence measures survival time,

NOT successful transport.



\---



\## 2. Endpoint Compactness



STATUS:

FAILED



Problem:

Compact endpoints do not imply coherent transport topology.



Braided systems can still produce relatively compact exits.



Conclusion:

Endpoint compactness measures spatial concentration,

NOT transport branching structure.



\---



\## 3. Endpoint Entropy



STATUS:

FAILED



Problem:

Entropy of final exits near the target

does not distinguish:

\- single-channel transport

from

\- braided transport.



Reason:

Different channels can merge near the final target region.



Conclusion:

Endpoint entropy measures output dispersion,

NOT branching topology.



\---



\## 4. Gate Entropy



STATUS:

FAILED



Problem:

Shannon entropy on gate crossings

still failed to distinguish:

\- coherent curved transport

from

\- braided transport.



Reason:

Entropy measures spread uniformity,

not number of transport families.



Example:

A\_REFERENCE produced broader continuous occupancy,

while H\_BRAIDED produced sharper multimodal occupancy,

leading to inverted ranking.



Conclusion:

Entropy is not equivalent to branching topology.



\---



\# CURRENT WORKING OBSERVABLE



\## Gate Mode Count / Output Branching



STATUS:

WORKING ON SYNTHETIC BENCHMARKS



Purpose:

Estimate number of coherent transport channels

crossing a diagnostic gate.



Validated behavior:

\- A\_REFERENCE\_OPEN -> 1 mode

\- H\_BRAIDED -> multiple modes

\- I\_SINGLE\_TRAPPED -> 0 modes



Interpretation:

Measures branching structure directly,

instead of dispersion or survival.



LIMITATIONS:

\- synthetic only

\- gate-position dependent

\- not validated on real systems yet



\---



\# IMPORTANT RULE



Do NOT reintroduce failed observables

without explicitly explaining:

\- what changed,

\- why the previous failure no longer applies,

\- and how the new formulation avoids the old failure.


\---


\# RADIAL GEOMETRIC-SIGNATURE FAILURES


\## Best_Bin as a stable geometric wall


STATUS:

FAILED


Problem:

`Best_Bin` selects the location of an absolute radial peak. The null-control campaign showed that peak selection is not robust enough to separate local geometric organization from distributional and amplitude effects.


Conclusion:

`Best_Bin` is not considered a stable geometric observable or evidence of a geometric wall. The relevant controlled observable is instead the extinction of the pointwise differential Z-score against Vector Shuffle.


\---


\## Raw Mean_Vort analyzed alone


STATUS:

INSUFFICIENT AS A STANDALONE OBSERVABLE


Problem:

An absolute `Mean_Vort` value does not identify whether the response comes from local organization or from distributional properties preserved by a shuffle.


Conclusion:

`Mean_Vort` may remain an input measurement, but its raw value alone does not support the geometric interpretation. A matched null-control comparison is required in the frozen synthetic analysis.

