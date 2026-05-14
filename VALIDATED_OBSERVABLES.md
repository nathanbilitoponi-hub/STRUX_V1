# STRUX_V1 — VALIDATED OBSERVABLES

Purpose:
Track observables that currently work under controlled benchmarks.

This file separates validated behavior from speculation.

---

# 1. success_rate

STATUS:
VALIDATED ON SYNTHETIC BENCHMARKS

Definition:
Fraction of transported rays that successfully reach the target region.

Operational meaning:
success_rate measures effective transport viability,
not merely binary geometric connectivity.

Validated in:
- STRUX_SINGLE_TRAPPED_TEST_05
- STRUX_APERTURE_TEST_01

Key result from STRUX_APERTURE_TEST_01:

aperture_height = 2
success_rate = 0.1340

aperture_height = 8
success_rate = 0.5960

aperture_height = 12
success_rate = 0.7960

aperture_height = 16
success_rate = 0.9320

aperture_height = 22
success_rate = 0.9940

Interpretation:
A geometric opening may exist, but transport only becomes reliable above a critical aperture scale.

Current estimated transition:
aperture_height approximately 10–12 px.

Limitations:
- synthetic only
- depends on ray dynamics
- depends on noise level
- not yet validated on real-world data

---

# 2. gate_mode_count

STATUS:
VALIDATED ON SYNTHETIC BENCHMARKS

Definition:
Number of coherent transport modes crossing a diagnostic gate.

Operational meaning:
gate_mode_count distinguishes single-channel transport from multi-channel / braided transport.

Validated in:
- STRUX_SINGLE_TRAPPED_TEST_05

Key result:

A_REFERENCE_OPEN:
detected_modes = 1
classification = SINGLE COHERENT CHANNEL

H_BRAIDED:
detected_modes = 2
classification = MULTI-CHANNEL / BRAIDED

I_SINGLE_TRAPPED:
detected_modes = 0
classification = TRAPPED / INCOMPLETE

Interpretation:
The observable measures output branching,
not entropy, endpoint compactness, or persistence.

Limitations:
- gate placement is currently manual
- mode count depends on smoothing parameters
- real-world validation not yet completed

---

# 3. direction_coherence

STATUS:
VALIDATED ON SYNTHETIC CORRIDOR BENCHMARK

Definition:
Mean alignment of ray direction with the target direction during transport.

Operational meaning:
direction_coherence measures corridor alignment / tortuosity sensitivity.
It is NOT a topology metric.

Validated in:
- STRUX_CORRIDOR_COHERENCE_TEST_01

Key result from constant-width corridor test:

A_STRAIGHT:
success_rate = 1.0000
direction_coherence = 0.9954
detected_modes = 1

B_MILD_CURVE:
success_rate = 1.0000
direction_coherence = 0.9351
detected_modes = 1

C_STRONG_CURVE:
success_rate = 1.0000
direction_coherence = 0.8057
detected_modes = 1

D_ZIGZAG:
success_rate = 0.4980
direction_coherence = 0.5625
detected_modes = 1

Interpretation:
With corridor width held approximately constant,
direction_coherence decreases as global corridor geometry becomes more curved or tortuous.

This suggests STRUX is sensitive to corridor coherence,
not only aperture width or binary path existence.

Important distinction:
- gate_mode_count measures number of transport channels.
- success_rate measures transport viability.
- direction_coherence measures geometric alignment / tortuosity.

Limitations:
- synthetic only
- depends on ray dynamics
- depends on noise level
- not yet validated on real-world spatial networks

Additional caution:

direction_coherence is currently validated only as an empirical synthetic diagnostic.

It is NOT yet proven:
- invariant under rotation,
- invariant under scaling,
- invariant under sampling changes,
- independent from ray initialization,
- distinct from standard pathfinding alignment behavior.

Further validation is required before interpreting it as a general geometric observable.
---

# 4. clearance_ratio

STATUS:
VALIDATED ON SYNTHETIC GEOMETRIC BENCHMARK

Definition:
clearance_ratio = aperture_size / body_size

Operational meaning:
clearance_ratio measures whether a body of given size can pass through a geometric opening.

Validated in:
- STRUX_CLEARANCE_TEST_01

Key result:

body_size = 15

aperture = 14
clearance_ratio = 0.93
transport = BLOCKED

aperture = 16
clearance_ratio = 1.07
transport = PASS

Interpretation:
A geometric void is not automatically a usable passage.
A passage becomes useful only when its free clearance is greater than or equal to the body size.

Current threshold:
clearance_ratio ≈ 1.0

Limitations:
- deterministic geometry test
- not yet coupled to stochastic ray transport
- not yet tested with curved, noisy, or irregular apertures

# CURRENT CLAIM

STRUX currently supports this limited claim:

STRUX can classify constrained synthetic transport geometries by combining:
- transport completion / viability,
- gate mode count / output branching.

STRUX does NOT yet support claims about:
- universal physics,
- cosmology,
- physical flux,
- full transport topology,
- replacement for TDA.

---

# NEXT VALIDATION TARGETS

1. Gate placement robustness
2. Noise robustness
3. Sieve / porous barrier benchmark
4. Real-world spatial graph test
5. Automatic export of benchmark results