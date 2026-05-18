# Dynamic Failure / Congestion Experimental Subsystem

## Status

Experimental subsystem separated from core STRUX_V1.

This module explores transport degradation inside constrained geometric corridors using lightweight particle-based simulations.

The subsystem is NOT considered part of the validated STRUX core.

Current purpose:
- robustness exploration,
- transport diagnostics,
- congestion analysis,
- interaction-driven degradation,
- parameter sensitivity,
- falsifiable experimental testing.

---

# Current Experimental Components

Implemented mechanisms include:

- constrained S-shaped corridors,
- goal-directed particles,
- local collision interactions,
- dead particle residue dynamics,
- adaptive local deflection,
- spatial choke analysis,
- temporal jitter propagation,
- multi-seed parameter sweeps,
- baseline comparison tests.

---

# Main Observations

## 1. Non-monotonic transport behavior

The full interaction system exhibits a tradeoff between:

- throughput / success rate,
- downstream temporal coherence.

Observed pattern:

Low deflection:
- lower temporal jitter,
- higher collapse probability,
- localized congestion.

High deflection:
- higher success rate,
- stronger downstream dispersion,
- turbulence-like propagation.

Current interpretation:
the system appears to exhibit a tradeoff between:

- "stable but fragile"
vs
- "resilient but turbulent"

---

## 2. Spatial choke localization

Failure events are not concentrated at a single curvature point.

Instead:
degradation zones emerge across transition regions and inclined downstream segments.

This suggests that:
- curvature may inject instability,
- while collapse propagates downstream through interaction feedback.

Current status:
suggestive but not yet mechanistically identified.

---

## 3. Local jitter propagation

Temporal jitter was measured across corridor regions:

- entry zone,
- transition zone,
- downstream zone.

Observed behavior:
- jitter is minimal at entry,
- increases across transition regions,
- becomes largest downstream.

This indicates:
transport degradation propagates spatially through the corridor.

---

# Critical Baseline Result

## Ballistic No-Interaction Baseline

A dedicated baseline was implemented removing:

- particle-particle collisions,
- dead residue accumulation,
- interaction feedback.

Geometry remained identical.

Result:

High deflection in the ballistic baseline:
- increases success,
- decreases downstream jitter.

This is the opposite of the full interaction system.

Interpretation:
geometry alone does NOT generate downstream turbulence-like dispersion.

The observed tradeoff appears to depend on:
- local interactions,
- collision feedback,
- passive obstacle accumulation,
- adaptive deflection coupling.

This is currently the strongest result of the subsystem.

---

# Current Limitations

The subsystem remains exploratory.

The following have NOT yet been established:

- mechanism identification,
- scaling laws,
- universality,
- robustness across arbitrary geometries,
- correspondence with physical turbulence,
- correspondence with hydrodynamic instability.

Current results apply ONLY to:
- the tested S-shaped corridor family,
- the tested parameter ranges.

---

# Existing Baselines

Implemented:
- random walk baseline,
- simple social-force baseline,
- ballistic no-interaction baseline.

Planned:
- Vicsek alignment baseline,
- frictional social-force baseline,
- density scaling analysis,
- geometry perturbation tests.

---

# Repository Policy

This subsystem is intentionally isolated from the core STRUX framework.

Experimental modules:
- must remain reproducible,
- must remain falsifiable,
- must avoid speculative claims,
- must not be presented as validated physical theory.

The subsystem is intended as:
- an experimental transport diagnostics sandbox,
- a constrained geometry degradation study,
- a lightweight interaction-flow research prototype.

---

# Current Interpretation

Current evidence suggests that:

- constrained geometry organizes flow,
- interaction dynamics generate degradation,
- local avoidance can improve throughput,
- interaction feedback can amplify downstream temporal dispersion.

The exact mechanism remains unknown.

Possible candidate interpretations include:
- hydrodynamic dispersion analogies,
- delayed downstream instability,
- interaction-driven transport disorder,
- active-matter-style congestion transitions.

These interpretations remain hypothetical until validated through additional baselines and scaling studies.