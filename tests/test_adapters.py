import tempfile
import unittest
from pathlib import Path

from ordered_validity.adapters import Candidate, candidates_to_positions, load_candidate_csv
from ordered_validity.schema import ValidationError


class FakeChemistry:
    def identity(self, smiles: str, mode: str) -> str | None:
        if smiles == "invalid":
            return None
        return {"OCC": "CCO"}.get(smiles, smiles)


class AdapterTests(unittest.TestCase):
    def test_raw_candidates_become_classified_positions(self) -> None:
        rows = [
            Candidate("m", "t", 0, "CCO", True),
            Candidate("m", "t", 1, "OCC", True),
            Candidate("m", "t", 2, "invalid", True),
            Candidate("m", "t", 3, "CCN", False),
        ]
        positions = candidates_to_positions(rows, "canonical_isomeric_smiles", FakeChemistry())
        self.assertEqual([row.identity for row in positions], ["CCO", "CCO", "", ""])
        self.assertEqual([row.molecular_valid for row in positions], [True, True, False, False])

    def test_source_valid_blank_molecule_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "has no molecule"):
            candidates_to_positions(
                [Candidate("m", "t", 0, "", True)],
                "canonical_smiles",
                FakeChemistry(),
            )

    def test_raw_schema_rejects_duplicate_positions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw.csv"
            path.write_text(
                "method,target_id,position,smiles,source_valid\n"
                "m,t,0,CCO,1\n"
                "m,t,0,CCN,1\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValidationError, "duplicate position"):
                load_candidate_csv(path)
