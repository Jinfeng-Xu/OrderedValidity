# Ordered Validity

Ordered Validity is an open source evaluator for finite molecular generation benchmarks. It preserves every requested output position, including missing and invalid generations, before applying molecular validity, targetwise identity and explicit dependence rules.

The package answers a practical question: **Does a benchmark conclusion still hold when the released generation population is evaluated in its declared order, with failures retained and correlated targets weighted explicitly?**

## What the software provides

- A JSON protocol for methods, targets, quotas, identity, dependence units and the aggregation rule used for selection
- A portable CSV format for raw candidates
- RDKit parsing, sanitization and four molecular identity relations
- Completion of absent output positions as delivery failures
- First outcome ledgers with mutually exclusive failure labels
- Decision summaries at target, method and programme levels
- Machine readable CSV and JSON outputs with a compact Markdown report
- A Python API, command line interface and tested extension points

The evaluator applies the protocol to released molecular generations and produces a complete decision ledger.

## Install

```bash
python -m pip install -e ".[chem]"
```

For development:

```bash
python -m pip install -e ".[chem,dev]"
pytest
```

## Evaluate raw generations

The protocol defines the complete method and target frame, expected positions, quota, programme membership and molecular identity relation. The included example uses four positions per cell, a quota of three and canonical isomeric SMILES identity.

```bash
ordered-validity validate-protocol configs/example-protocol.json
ordered-validity evaluate examples/raw_candidates.csv \
  --protocol configs/example-protocol.json \
  --output build/example
```

Raw input has one row per delivered position:

```text
method,target_id,position,smiles,source_valid
```

The evaluator fills omitted positions as `delivery_failure`. Equivalent valid molecules receive the same RDKit identity, and only their first occurrence for each target passes.

If molecular identities have already been computed by a benchmark specific pipeline, use the ledger interface:

```bash
ordered-validity evaluate-ledger examples/position_ledger.csv \
  --protocol configs/example-protocol.json \
  --output build/example-ledger
```

## Outputs

Each run writes:

- `first_outcome_ledger.csv`: one retained outcome per expected position
- `cell_summary.csv`: loss decomposition and action change for each method and target
- `method_summary.csv`: equal target and equal programme summaries
- `metadata.json`: protocol dimensions and selected methods
- `report.md`: human readable result table

See [the benchmark contract](docs/benchmark-contract.md) for definitions and [the adapter guide](docs/adapters.md) for integrating a public release.

## Included cohort

The [Kumar cohort](datasets/kumar/README.md) contains 116,400 requested molecular generation positions across 12 methods and 97 targets. The compressed position ledger and its protocol reproduce the population accounting and target quota decisions reported in the paper.

```bash
ordered-validity evaluate-ledger datasets/kumar/positions.csv.gz \
  --protocol datasets/kumar/protocol.json \
  --output build/kumar
```

## Python API

```python
from ordered_validity import evaluate, load_positions, load_protocol

protocol = load_protocol("configs/example-protocol.json")
result = evaluate(
    load_positions("examples/position_ledger.csv"),
    quota=protocol.quota,
    expected_slots=protocol.expected_slots,
    position_base=protocol.position_base,
    target_manifest=protocol.targets,
    expected_methods=protocol.methods,
    top_k=protocol.top_k,
    selection_weighting=protocol.aggregation,
)
```

## Repository layout

```text
configs/                  protocol examples
datasets/kumar/           complete 116,400-position Kumar cohort
docs/                     contract and adapter documentation
examples/                 minimal raw and classified inputs
src/ordered_validity/     chemistry, adapters, evaluator, reports and CLI
tests/                    unit and integration tests
```

## Citation and licence

Citation metadata are in `CITATION.cff`. Code is released under the MIT License. Benchmark providers retain the rights to their original datasets.
