from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import ValidationError


IDENTITY_MODES = {
    "canonical_smiles",
    "canonical_isomeric_smiles",
    "inchikey",
    "connectivity_inchikey",
}
AGGREGATION_MODES = {"equal_target", "equal_dependence_unit"}


@dataclass(frozen=True)
class Protocol:
    name: str
    methods: tuple[str, ...]
    targets: dict[str, str]
    expected_slots: int
    quota: int
    position_base: int
    top_k: int
    identity: str
    aggregation: str

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Protocol":
        required = {
            "name",
            "methods",
            "targets",
            "expected_slots",
            "quota",
            "identity",
            "aggregation",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ValidationError(f"protocol missing fields: {', '.join(missing)}")
        name = str(value["name"]).strip()
        raw_methods = value["methods"]
        raw_targets = value["targets"]
        if not isinstance(raw_methods, list) or not isinstance(raw_targets, list):
            raise ValidationError("protocol methods and targets must be lists")
        methods = tuple(str(item).strip() for item in raw_methods)
        targets: dict[str, str] = {}
        for item in raw_targets:
            try:
                target_id = str(item["target_id"]).strip()
                unit = str(item["dependence_unit"]).strip()
            except (KeyError, TypeError) as error:
                raise ValidationError(
                    "each protocol target requires target_id and dependence_unit"
                ) from error
            if not target_id or not unit:
                raise ValidationError("protocol target fields must be non-empty")
            if target_id in targets:
                raise ValidationError(f"duplicate protocol target: {target_id}")
            targets[target_id] = unit
        try:
            expected_slots = int(value["expected_slots"])
            quota = int(value["quota"])
            position_base = int(value.get("position_base", 0))
            top_k = int(value.get("top_k", 1))
        except (TypeError, ValueError) as error:
            raise ValidationError("protocol count fields must be integers") from error
        identity = str(value["identity"])
        aggregation = str(value["aggregation"])
        if not name or not methods or any(not item for item in methods):
            raise ValidationError("protocol name and methods must be non-empty")
        if len(set(methods)) != len(methods):
            raise ValidationError("protocol methods must be unique")
        if not targets:
            raise ValidationError("protocol requires at least one target")
        if expected_slots < 1 or quota < 1 or quota > expected_slots:
            raise ValidationError("protocol quota must lie within expected slots")
        if position_base not in {0, 1} or top_k < 1:
            raise ValidationError("position_base must be 0 or 1 and top_k must be positive")
        if identity not in IDENTITY_MODES:
            raise ValidationError(
                f"unsupported identity mode {identity!r}; choose from {sorted(IDENTITY_MODES)}"
            )
        if aggregation not in AGGREGATION_MODES:
            raise ValidationError(
                f"unsupported aggregation {aggregation!r}; choose from {sorted(AGGREGATION_MODES)}"
            )
        return cls(
            name,
            methods,
            targets,
            expected_slots,
            quota,
            position_base,
            top_k,
            identity,
            aggregation,
        )


def load_protocol(path: str | Path) -> Protocol:
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(f"invalid protocol JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValidationError("protocol root must be a JSON object")
    return Protocol.from_dict(value)
