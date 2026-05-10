# STRUX_V1 — False Filament Benchmark

## Goal

Verify that STRUX filament scoring does NOT automatically create strong filaments between nearby unsupported regions.

This benchmark tests whether tube-based scoring truly depends on distributed corridor support rather than simple geometric proximity.

---

# Benchmark Structure

Two synthetic cases are generated.

## FALSE CASE

Two nearby point-cloud blobs are created without any real connecting corridor.

Expected behavior

```txt
NOT strong filament

The algorithm may classify the connection as

weak filament
none

but should NOT produce

strong filament
TRUE CASE

The same two blobs are connected using a real noisy corridor of points.

Expected behavior

strong filament
Metrics Used

The filament score combines

continuity occupancy
support coverage
central density ratio

A strong filament requires sufficient values in all three metrics.

Important Result

Observed benchmark result

FALSE CASE
class = weak filament

TRUE CASE
class = strong filament

Interpretation

STRUX_V1 does not automatically connect nearby regions using distance alone.

The continuity metric contributes significantly to filament validation.

What This Benchmark Demonstrates

This benchmark demonstrates

tube-based scoring + continuity occupancy
can discriminate between

(1) nearby unsupported blobs
and
(2) genuinely corridor-supported structures
What This Benchmark Does NOT Demonstrate

This benchmark does NOT demonstrate

universal robustness
optimal filament extraction
topological correctness
superiority over existing methods
real-world validation
final STRUX theory

This is only a controlled synthetic validation test.

Known Limitations

Current limitations include

fixed tube_radius
heuristic thresholds
no adaptive density scaling
no topological persistence
no graph-aware edge reasoning
Related Files
benchmarkstest_false_filament.py
coreconnection_scoringconnection_scoring.py
ALGORITHM_DECISIONS.md
Current Status

Benchmark status

PASS

Reason

The FALSE CASE is rejected as a strong filament,
while the TRUE CASE is accepted as a strong filament.