from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import fmean
from typing import Any

from .schema import Position, ValidationError


def _complete_frame(
    positions: list[Position],
    expected_slots: int,
    position_base: int,
    target_manifest: dict[str, str] | None,
    expected_methods: list[str] | tuple[str, ...] | None,
) -> list[Position]:
    if expected_slots < 1:
        raise ValidationError("expected_slots must be positive")
    if position_base not in {0, 1}:
        raise ValidationError("position_base must be 0 or 1")
    observed_methods = {row.method for row in positions}
    methods = sorted(expected_methods) if expected_methods else sorted(observed_methods)
    if expected_methods and not observed_methods.issubset(set(expected_methods)):
        extra = sorted(observed_methods - set(expected_methods))
        raise ValidationError(f"ledger contains methods absent from protocol: {extra}")
    observed_targets = {row.target_id for row in positions}
    targets = sorted(target_manifest) if target_manifest else sorted(observed_targets)
    if target_manifest and not observed_targets.issubset(target_manifest):
        extra = sorted(observed_targets - set(target_manifest))
        raise ValidationError(f"ledger contains targets absent from manifest: {extra}")
    lookup = {(row.method, row.target_id, row.position): row for row in positions}
    allowed = set(range(position_base, position_base + expected_slots))
    for row in positions:
        if row.position not in allowed:
            raise ValidationError(
                f"position {row.position} for {(row.method, row.target_id)} is outside "
                f"[{position_base}, {position_base + expected_slots - 1}]"
            )
    completed: list[Position] = []
    for method in methods:
        for target in targets:
            for position in sorted(allowed):
                completed.append(
                    lookup.get(
                        (method, target, position),
                        Position(method, target, position, False, False, False, ""),
                    )
                )
    return completed


def _select_top_with_ties(scores: dict[str, float], top_k: int) -> list[str]:
    if top_k < 1:
        raise ValidationError("top_k must be positive")
    if not scores:
        return []
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    boundary = ordered[min(top_k, len(ordered)) - 1][1]
    return sorted(method for method, score in ordered if score >= boundary)


def evaluate(
    positions: list[Position],
    *,
    quota: int,
    expected_slots: int,
    position_base: int = 0,
    target_manifest: dict[str, str] | None = None,
    expected_methods: list[str] | tuple[str, ...] | None = None,
    top_k: int = 1,
    selection_weighting: str = "equal_target",
) -> dict[str, Any]:
    """Evaluate a fixed finite position population under ordered validity."""
    if quota < 1 or quota > expected_slots:
        raise ValidationError("quota must lie between 1 and expected_slots")
    if selection_weighting not in {"equal_target", "equal_dependence_unit"}:
        raise ValidationError("selection_weighting must be equal_target or equal_dependence_unit")
    if selection_weighting == "equal_dependence_unit" and not target_manifest:
        raise ValidationError("equal_dependence_unit selection requires a target manifest")
    frame = _complete_frame(
        positions, expected_slots, position_base, target_manifest, expected_methods
    )
    cells: dict[tuple[str, str], list[Position]] = defaultdict(list)
    for row in frame:
        cells[(row.method, row.target_id)].append(row)

    first_outcomes: list[dict[str, Any]] = []
    cell_summaries: list[dict[str, Any]] = []
    for (method, target), rows in sorted(cells.items()):
        seen: set[str] = set()
        source_count = molecular_count = distinct_count = 0
        for row in sorted(rows, key=lambda item: item.position):
            if not row.delivered:
                outcome = "delivery_failure"
            elif not row.source_valid:
                outcome = "source_invalid"
            elif not row.molecular_valid:
                source_count += 1
                outcome = "molecular_invalid"
            else:
                source_count += 1
                molecular_count += 1
                if row.identity in seen:
                    outcome = "duplicate_identity"
                else:
                    seen.add(row.identity)
                    distinct_count += 1
                    outcome = "distinct_valid_pass"
            first_outcomes.append(
                {
                    "method": method,
                    "target_id": target,
                    "position": row.position,
                    "first_outcome": outcome,
                    "identity": row.identity,
                }
            )
        source_success = source_count >= quota
        ordered_success = distinct_count >= quota
        cell_summaries.append(
            {
                "method": method,
                "target_id": target,
                "dependence_unit": target_manifest.get(target, "") if target_manifest else "",
                "source_valid_count": source_count,
                "molecular_valid_count": molecular_count,
                "distinct_valid_count": distinct_count,
                "chemistry_loss": source_count - molecular_count,
                "identity_loss": molecular_count - distinct_count,
                "source_margin": source_count - quota,
                "ordered_loss": source_count - distinct_count,
                "source_success": int(source_success),
                "ordered_success": int(ordered_success),
                "action_changed": int(source_success and not ordered_success),
            }
        )

    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cell_summaries:
        by_method[row["method"]].append(row)
    method_summaries: list[dict[str, Any]] = []
    method_scores: dict[str, float] = {}
    source_scores: dict[str, float] = {}
    for method, rows in sorted(by_method.items()):
        source_successes = sum(row["source_success"] for row in rows)
        ordered_successes = sum(row["ordered_success"] for row in rows)
        source_equal_target_rate = source_successes / len(rows)
        equal_target_rate = ordered_successes / len(rows)
        source_programme_rate: float | str = ""
        programme_rate: float | str = ""
        if target_manifest:
            source_grouped: dict[str, list[int]] = defaultdict(list)
            ordered_grouped: dict[str, list[int]] = defaultdict(list)
            for row in rows:
                source_grouped[row["dependence_unit"]].append(row["source_success"])
                ordered_grouped[row["dependence_unit"]].append(row["ordered_success"])
            source_programme_rate = fmean(
                fmean(values) for values in source_grouped.values()
            )
            programme_rate = fmean(fmean(values) for values in ordered_grouped.values())
        method_summaries.append(
            {
                "method": method,
                "targets": len(rows),
                "source_successful_targets": source_successes,
                "ordered_successful_targets": ordered_successes,
                "changed_targets": sum(row["action_changed"] for row in rows),
                "source_equal_target_rate": source_equal_target_rate,
                "equal_target_rate": equal_target_rate,
                "source_equal_programme_rate": source_programme_rate,
                "equal_programme_rate": programme_rate,
            }
        )
        if selection_weighting == "equal_dependence_unit":
            source_scores[method] = float(source_programme_rate)
            method_scores[method] = float(programme_rate)
        else:
            source_scores[method] = source_equal_target_rate
            method_scores[method] = equal_target_rate

    return {
        "metadata": {
            "methods": len(by_method),
            "targets": len({row["target_id"] for row in cell_summaries}),
            "positions": len(frame),
            "expected_slots_per_cell": expected_slots,
            "position_base": position_base,
            "quota": quota,
            "selection_weighting": selection_weighting,
            "top_k_with_ties": top_k,
            "source_selected_methods": _select_top_with_ties(source_scores, top_k),
            "ordered_selected_methods": _select_top_with_ties(method_scores, top_k),
        },
        "first_outcomes": first_outcomes,
        "cell_summaries": cell_summaries,
        "method_summaries": method_summaries,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_evaluation(result: dict[str, Any], output: str | Path) -> None:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    _write_csv(output / "first_outcome_ledger.csv", result["first_outcomes"])
    _write_csv(output / "cell_summary.csv", result["cell_summaries"])
    _write_csv(output / "method_summary.csv", result["method_summaries"])
    (output / "metadata.json").write_text(
        json.dumps(result["metadata"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

