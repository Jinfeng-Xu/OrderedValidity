# Kumar cohort

This dataset contains the complete indexed population used for the Kumar analysis.

| Methods | Targets | Positions per cell | Total positions | Target action |
| ---: | ---: | ---: | ---: | --- |
| 12 | 97 | 100 | 116,400 | At least 90 distinct valid molecules |

`positions.csv.gz` stores one row for every requested position. Missing deliveries remain explicit rows. `protocol.json` defines the complete method and target frame, canonical isomeric SMILES identity, equal target aggregation and the top three selection with ties.

Each row records the method, target, original position, delivery state, source validity, molecular validity, targetwise identity and released record identifier. Local filesystem paths are not included.

```bash
ordered-validity evaluate-ledger datasets/kumar/positions.csv.gz \
  --protocol datasets/kumar/protocol.json \
  --output build/kumar
```

The evaluation assigns 4,042 delivery failures, 3 source validity failures, 767 molecular validity failures, 388 repeated identities and 111,200 distinct valid passes.
