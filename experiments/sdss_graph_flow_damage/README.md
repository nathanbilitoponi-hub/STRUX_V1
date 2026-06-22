# Graph Flow Damage Test on SDSS-derived kNN Networks

This experiment tests graph-level flow-damage signatures on kNN graphs derived from SDSS-like point data. It measures selective path degradation events where single-node removal increases source-target distance while preserving global connectivity.

This is an existence proof only. Frequency and cosmological relevance untested.

## Scope

This experiment is a non-cosmological graph stress test.

It is not a cosmological validation.
It is not a void-finder benchmark.
It is not a comparison with VIDE/ZOBOV.
It does not measure void statistics or cosmic web topology.
It does not estimate event frequency in the full graph.

## Known Result To Preserve

`SDSS_MIN_PROOF_04_MULTISEED_REPLICATION`

| Field | Result |
| --- | --- |
| seeds tested | 10 |
| events found | 10/10 |
| verified class | PATH_OPTIMIZER |
| delta range | +2 to +4 |
| components_after | 1 in all cases |
| orphan_count | 0 in all cases |
| off-path controls | 100% NO_FLOW_EFFECT |
| verdict | PASS_MULTISEED_REPLICATION_STRONG |

## Run

From the repository root:

```bash
python experiments/sdss_graph_flow_damage/sdss_graph_flow_damage_min_proof.py \
  --input datasets/sdss_galaxies.csv \
  --output-dir experiments/sdss_graph_flow_damage/results \
  --n-sample 3000 \
  --k 4 \
  --seed-start 40 \
  --seed-end 49 \
  --n-controls 100
```

## Outputs

The script writes:

- `sdss_graph_flow_damage_results.csv`
- `sdss_graph_flow_damage_summary.json`

The CSV contains per-seed event and negative-control measurements. The JSON contains aggregate counts, rates, verdict, safe claim, and forbidden claims.

## Classification Rules

- `PATH_OPTIMIZER`: source-target connected after removal and `dist_after > dist_before`.
- `NO_FLOW_EFFECT`: source-target connected after removal and `dist_after == dist_before`.
- `MANDATORY_CONSTRAINT`: source-target disconnected after removal.

No cosmology interpretation is added.
