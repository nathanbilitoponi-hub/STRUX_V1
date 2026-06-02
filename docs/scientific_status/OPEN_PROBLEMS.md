# OPEN PROBLEMS

This document tracks the main unresolved scientific and technical limitations of STRUX_V1.

The goal is to explicitly separate:
- validated observables,
- experimental interpretations,
- unresolved behaviors,
- and unsupported claims.

---

# 1. Baseline comparison

Current STRUX transport observables have NOT yet been systematically compared against:

- A*
- shortest-path ensembles
- random walks
- diffusion models
- visibility graph approaches

Open question:

Do STRUX observables provide additional information beyond classical path-based transport methods?

---

# 2. Numerical robustness

Current transport observables still require:

- resolution stability analysis
- sampling convergence tests
- geometric noise robustness
- gate-position sensitivity analysis
- parameter sensitivity analysis

Open question:

Are the current observables stable under perturbation,
or are they partially dependent on sampling artifacts?

---

# 3. Directional coherence interpretation

Current uncertainty:

direction_coherence may reflect:
- genuine geometric degradation
OR
- numerical/sampling effects.

Formal convergence and invariance studies are still missing.

---

# 4. Gate mode interpretation

gate_mode_count currently behaves primarily as a local spatial clustering observable.

Open questions:

- Can sequential gate analysis produce meaningful transport-phase diagnostics?
- Can gate evolution detect merge/split transport behaviors?
- Is gate_mode_count more informative than simple spatial clustering?

---

# 5. Temporal synchronization

The temporal interpretation of constrained propagation remains experimental.

Current hypothesis:

Different geometries may induce:
- different arrival-time dispersion,
- synchronization cost,
- temporal jitter,
even under identical topological connectivity.

This interpretation has not yet been formally validated.

---

# 6. Generalization limits

Current benchmarks are synthetic and low-dimensional.

Open question:

Do the same transport-degradation behaviors remain meaningful in:
- real spatial networks,
- robotic navigation,
- porous media,
- microfluidic systems,
- large-scale geometric systems?

---

# 7. Current scientific scope

STRUX_V1 currently does NOT demonstrate:

- new physics
- cosmology
- universal transport laws
- superiority over shortest-path algorithms
- universal topology inference

Current validated scope is limited to:

experimental geometric transport diagnostics
in constrained synthetic benchmark systems.