# Adapter guide

Ordered Validity separates archive specific molecule extraction from the decision engine. An adapter must emit either raw candidates or classified positions without changing order, denominators or target membership.

## Raw candidate adapter

Emit these columns:

| Column | Contract |
| --- | --- |
| `method` | Stable method identifier declared in the protocol. |
| `target_id` | Stable target identifier declared in the protocol. |
| `position` | Original requested output position. |
| `smiles` | Released molecule, blank only when no molecule was delivered. |
| `source_valid` | Source defined success flag, encoded as `0` or `1`. |

The built in RDKit backend determines molecular validity and identity. CSV, JSON, SDF or directory layouts from a provider should be converted into this interchange table by a small provider adapter.

## Classified ledger adapter

For archives requiring a specialized chemistry cascade, emit the seven column position ledger defined in `benchmark-contract.md`. Document the parser, sanitization version, allowed chemistry and identity relation alongside the adapter. The evaluator uses these classifications to construct the ordered decision ledger.
