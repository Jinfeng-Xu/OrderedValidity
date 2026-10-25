from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


REQUIRED_COLUMNS = (
    "method",
    "target_id",
    "position",
    "delivered",
    "source_valid",
    "molecular_valid",
    "identity",
)


class ValidationError(ValueError):
    """Raised when a benchmark ledger violates the position ledger contract."""


@dataclass(frozen=True)
class Position:
    method: str
    target_id: str
    position: int
    delivered: bool
    source_valid: bool
    molecular_valid: bool
    identity: str


def _flag(value: str, *, field: str, line: int) -> bool:
    if value not in {"0", "1"}:
        raise ValidationError(f"line {line}: {field} must be 0 or 1")
    return value == "1"


def _open_csv(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode="rt", newline="", encoding="utf-8")
    return path.open(newline="", encoding="utf-8")


def load_positions(path: str | Path) -> list[Position]:
    path = Path(path)
    with _open_csv(path) as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in REQUIRED_COLUMNS if field not in (reader.fieldnames or [])]
        if missing:
            raise ValidationError(f"missing required columns: {', '.join(missing)}")
        positions: list[Position] = []
        keys: set[tuple[str, str, int]] = set()
        for line, row in enumerate(reader, start=2):
            method = row["method"].strip()
            target = row["target_id"].strip()
            if not method or not target:
                raise ValidationError(f"line {line}: method and target_id must be non-empty")
            try:
                position = int(row["position"])
            except ValueError as error:
                raise ValidationError(f"line {line}: position must be an integer") from error
            delivered = _flag(row["delivered"], field="delivered", line=line)
            source_valid = _flag(row["source_valid"], field="source_valid", line=line)
            molecular_valid = _flag(row["molecular_valid"], field="molecular_valid", line=line)
            identity = row["identity"].strip()
            if position < 0:
                raise ValidationError(f"line {line}: position must be non-negative")
            if source_valid and not delivered:
                raise ValidationError(f"line {line}: source_valid requires delivered=1")
            if molecular_valid and not source_valid:
                raise ValidationError(f"line {line}: molecular_valid requires source_valid=1")
            if molecular_valid and not identity:
                raise ValidationError(
                    f"line {line}: molecular_valid requires a molecular identity"
                )
            key = (method, target, position)
            if key in keys:
                raise ValidationError(f"line {line}: duplicate position key {key}")
            keys.add(key)
            positions.append(
                Position(
                    method,
                    target,
                    position,
                    delivered,
                    source_valid,
                    molecular_valid,
                    identity,
                )
            )
    if not positions:
        raise ValidationError("position ledger is empty")
    return positions


def load_target_manifest(path: str | Path) -> dict[str, str]:
    path = Path(path)
    with _open_csv(path) as handle:
        reader = csv.DictReader(handle)
        if not {"target_id", "dependence_unit"}.issubset(reader.fieldnames or []):
            raise ValidationError("target manifest requires target_id and dependence_unit")
        result: dict[str, str] = {}
        for line, row in enumerate(reader, start=2):
            target = row["target_id"].strip()
            unit = row["dependence_unit"].strip()
            if not target or not unit:
                raise ValidationError(
                    f"line {line}: target_id and dependence_unit must be non-empty"
                )
            if target in result:
                raise ValidationError(f"line {line}: duplicate target_id {target}")
            result[target] = unit
    if not result:
        raise ValidationError("target manifest is empty")
    return result

