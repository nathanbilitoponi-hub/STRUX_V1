\# STRUX Observer Compression



\## Status



Internal research benchmark.



This module is not part of the public/product STRUX positioning yet.



\## Core question



Can STRUX identify an observer node from which the structural signal appears closer than it does from random observers?



In this benchmark, each observer induces signed graph levels:



```text

... -2.5 -1.5 -0.5 | +0.5 +1.5 +2.5 ...

```



The observer itself is treated as level `0`, interpreted as an observation membrane rather than a structural level.



\## Main metric



```text

observer compression gain =

median random |peak level| / STRUX observer |peak level|

```



A high gain means that STRUX found an observer from which the structure appears at a much smaller graph-level distance than from random observers.



\## SDSS graph-only benchmark



Dataset:



```text

SDSS sample

3000 graph nodes

17405 graph edges

```



Result:



```text

STRUX observer |peak| = 0.5

Random median |peak| = 5.5

Median compression gain = 11.0x

Verdict = PASS\_STRONG

```



Interpretation:



```text

STRUX compresses the observed structural peak to the first observable half-level.

```



\## Null model benchmark



| Graph model      |   Gain |

| ---------------- | -----: |

| Erdos-Renyi      |  0.33x |

| Barabasi-Albert  |  1.00x |

| Grid 32x32       | 23.00x |

| Random geometric | 12.00x |

| Balanced tree    | 11.00x |



Interpretation:



Observer compression does not appear strongly in unstructured random graph null models.



It appears in graphs with geometric, spatial, hierarchical, or constrained organization.



\## Current interpretation



Observer compression is not yet a validated universal STRUX law.



Current conservative interpretation:



```text

STRUX can identify privileged observer nodes in structured graphs.

From these observers, the main structural signal appears closer than from random observers.

```



\## Scripts



```text

scripts/observer\_compression\_sdss.py

scripts/observer\_compression\_null\_models.py

```



\## Outputs



```text

results/

figures/

```



\## Public positioning



Do not present this yet as:



```text

new physics

4D proof

cosmology result

universal law

```



For now, present it only as:



```text

advanced internal research on graph observability

```



