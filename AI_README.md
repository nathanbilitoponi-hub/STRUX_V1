\# STRUX\_V1 — AI README

## Current Working Definition

STRUX_V1 is an experimental geometric stress-response framework.

Instead of describing geometry only through static topology or shortest paths,
STRUX probes constrained geometries using ensembles of oriented trajectories
and measures how geometry affects:

- completion viability
- directional coherence
- local mode structure
- clearance viability

Current observables:
- success_rate
- direction_coherence
- gate_mode_count
- clearance_ratio

STRUX_V1 does NOT currently claim:
- universal transport laws
- cosmology
- physical flux modeling
- superiority over A*, RRT, diffusion, or porous-media models

Current goal:
identify whether constrained geometries with identical connectivity
can still produce measurably different transport responses.



IMPORTANT:

Before proposing new metrics, theories, or modules,

read the following files first:



\- PROJECT\_MAP.md

\- STATUS.md

\- FAILED\_OBSERVABLES.md

\- OPEN\_PROBLEMS.md

\- ALGORITHM\_DECISIONS.md



STRUX is NOT:

\- a theory of everything,

\- a final cosmology framework,

\- a complete TDA replacement,

\- a unified physics theory.



Current practical direction:

STRUX is a structural diagnosis framework for:

\- geometry-constrained systems,

\- transport structures,

\- backbone extraction,

\- branching/coherence analysis,

\- void and corridor organization.



Current validated concepts:

\- backbone extraction,

\- transport completion,

\- directional coherence,

\- gate mode count / branching diagnosis.



Current validated transport classes:

\- SINGLE COHERENT CHANNEL

\- MULTI-CHANNEL / BRAIDED

\- TRAPPED / INCOMPLETE



IMPORTANT FAILED OBSERVABLES:

\- persistence

\- endpoint compactness

\- endpoint entropy

\- gate entropy



Reason:

These observables measure survival or dispersion,

not transport branching topology.



Current working observable:

\- gate mode count / branching detection



Rules:

1\. Do not reintroduce failed observables without explaining why previous failures no longer apply.

2\. Separate:

&#x20;  - completion,

&#x20;  - coherence,

&#x20;  - branching.

3\. Prefer falsifiable benchmarks over broad theoretical claims.

4\. Keep synthetic benchmarks separate from real-world validation.

5\. Every module must declare:

&#x20;  - PURPOSE

&#x20;  - INPUT

&#x20;  - OUTPUT

&#x20;  - LIMITATIONS

&#x20;  - STATUS



Repository philosophy:

GitHub = dynamic technical memory

Zenodo = frozen scientific snapshots



Main goal:

Build an AI-readable and scientifically auditable structural analysis framework.

