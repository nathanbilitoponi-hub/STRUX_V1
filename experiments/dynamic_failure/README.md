# STRUX Experimental Subsystem — Dynamic Failure

This folder contains an experimental subsystem for studying dynamic congestion, localized failure, and adaptive recovery in constrained corridor simulations.

This module is NOT part of the STRUX core.

## Current status

Experimental / not validated.

## Observed behaviors

- low deflection: localized congestion / collapse
- medium deflection: possible recovery window
- high deflection: distributed turbulence / jitter
- death peaks may localize near corridor curvature changes

## Main validation targets

- multi-seed robustness
- parameter sensitivity
- geometry perturbation
- density scaling
- baseline comparison

## Files

scripts/
- sweep scripts
- choke localization scripts
- robustness tests
- baseline comparison tests

results/
- CSV summaries only

figures/
- selected representative PNG only

notes/
- conservative interpretation notes

## Explicit non-claims

This subsystem does NOT claim:
- new physics
- universal flow laws
- general congestion theory
- integration into STRUX core

It is maintained only as a falsifiable experimental module.