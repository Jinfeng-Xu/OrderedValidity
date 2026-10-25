from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .chemistry import ChemistryBackend, RDKitBackend
from .schema import Position, ValidationError


@dataclass(frozen=True)
class Candidate:
    method: str
    target_id: str
    position: int
    smiles: str
    source_valid: bool


def load_candidate_csv(path: str | Path) -> list[Candidate]:
    """Load the portable raw-candidate interchange format."""
    path = Path(path)
    required = {"method", "target_id", "position", "smiles", "source_valid"}
    result: list[Candidate] = []
    keys: set[tuple[str, str, int]] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValidationError(f"raw candidate file missing columns: {', '.join(missing)}")
        for line, row in enumerate(reader, start=2):
            method, target = row["method"].strip(), row["target_id"].strip()
            try:
                position = int(row["position"])
            except ValueError as error:
                raise ValidationError(f"line {line}: position must be an integer") from error
            source = row["source_valid"].strip()
            if source not in {"0", "1"}:
                raise ValidationError(f"line {line}: source_valid must be 0 or 1")
            if not method or not target or position < 0:
                raise ValidationError(f"line {line}: invalid method, target_id or position")
            key = (method, target, position)
            if key in keys:
                raise ValidationError(f"line {line}: duplicate position key {key}")
            keys.add(key)
            result.append(Candidate(method, target, position, row["smiles"].strip(), source == "1"))
    if not result:
        raise ValidationError("raw candidate file is empty")
    return result


def candidates_to_positions(
    candidates: list[Candidate],
    identity_mode: str,
    backend: ChemistryBackend | None = None,
) -> list[Position]:
    backend = backend or RDKitBackend()
    positions: list[Position] = []
    for row in candidates:
        delivered = bool(row.smiles)
        if row.source_valid and not delivered:
            key = (row.method, row.target_id, row.position)
            raise ValidationError(
                f"source-valid candidate has no molecule: {key}"
            )
        identity = (
            backend.identity(row.smiles, identity_mode)
            if delivered and row.source_valid
            else None
        )
        positions.append(
            Position(
                row.method,
                row.target_id,
                row.position,
                delivered,
                row.source_valid,
                identity is not None,
                identity or "",
            )
        )
    return positions
