from __future__ import annotations

from typing import Protocol

from .schema import ValidationError


class ChemistryBackend(Protocol):
    def identity(self, smiles: str, mode: str) -> str | None: ...


class RDKitBackend:
    """Parse, sanitize and identify molecules with a lazily imported RDKit."""

    def __init__(self) -> None:
        try:
            from rdkit import Chem
        except ImportError as error:
            raise RuntimeError(
                "RDKit is required for raw molecule evaluation; install ordered-validity[chem]"
            ) from error
        self.chem = Chem

    def identity(self, smiles: str, mode: str) -> str | None:
        molecule = self.chem.MolFromSmiles(smiles, sanitize=True)
        if molecule is None:
            return None
        if mode == "canonical_smiles":
            return self.chem.MolToSmiles(molecule, canonical=True, isomericSmiles=False)
        if mode == "canonical_isomeric_smiles":
            return self.chem.MolToSmiles(molecule, canonical=True, isomericSmiles=True)
        key = self.chem.MolToInchiKey(molecule)
        if mode == "inchikey":
            return key or None
        if mode == "connectivity_inchikey":
            return key.split("-", 1)[0] if key else None
        raise ValidationError(f"unsupported identity mode: {mode}")
