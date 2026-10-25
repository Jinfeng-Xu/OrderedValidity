import importlib.util
import unittest

from ordered_validity.chemistry import RDKitBackend


@unittest.skipUnless(importlib.util.find_spec("rdkit"), "RDKit optional dependency not installed")
class ChemistryTests(unittest.TestCase):
    def test_canonical_identity_and_invalid_smiles(self) -> None:
        backend = RDKitBackend()
        self.assertEqual(
            backend.identity("CCO", "canonical_isomeric_smiles"),
            backend.identity("OCC", "canonical_isomeric_smiles"),
        )
        self.assertIsNone(backend.identity("not-a-smiles", "canonical_isomeric_smiles"))
