# Benchmark contract

The machine readable version of these choices is a protocol JSON containing `methods`, `targets`, `expected_slots`, `quota`, `position_base`, `top_k`, `identity` and `aggregation`. Targets carry an explicit `dependence_unit`. The protocol is loaded before candidate outcomes and supplies the complete evaluation frame, including methods or targets with no delivered records.

## Required position ledger

Each expected position is identified by `(method, target_id, position)` and has the following fields:

| Field | Meaning |
| --- | --- |
| `method` | Workflow label used for the decision. |
| `target_id` | Target identifier declared in the protocol. |
| `position` | Integer position in the declared release order. |
| `delivered` | `1` when a record exists, otherwise `0`. |
| `source_valid` | Source defined valid state for the comparison action. |
| `molecular_valid` | Pass under the declared molecular cascade. |
| `identity` | Molecular identity used for targetwise deduplication. |

Boolean fields accept only `0` or `1`. A missing position is a delivery failure. A molecularly valid position must also be delivered, pass source validity and carry a nonempty identity. Duplicate keys are rejected.

## Protocol definition

The protocol defines:

1. the complete target and method frame
2. the number and base of expected positions per method and target cell
3. the ordered molecular predicates and first failure rule
4. the molecular identity relation
5. the target quota or other action rule
6. the mapping from targets to programmes and the weighting rule
7. the treatment of ties and failures
8. the sensitivity envelope that will be reported

## Outputs

The evaluator writes one first outcome per position:

- `delivery_failure`
- `source_invalid`
- `molecular_invalid`
- `duplicate_identity`
- `distinct_valid_pass`

For each method and target cell, the evaluator reports source valid, molecularly valid and distinct valid counts, together with source margin, ordered loss, source success, ordered success and action change. Method summaries retain every target. When a target manifest supplies `dependence_unit`, both equal target and equal programme ordered success rates are reported.

## Aggregation

The outputs describe the complete finite release. Alternative order or identity definitions can be evaluated as separate protocol variants.

`aggregation` is either `equal_target` or `equal_dependence_unit`. The second option first averages target success within each declared dependence unit and then weights units equally. The evaluator selects methods under the aggregation rule recorded in the protocol and reports both summaries.

