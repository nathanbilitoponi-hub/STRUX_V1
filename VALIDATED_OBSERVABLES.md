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