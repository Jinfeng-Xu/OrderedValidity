from __future__ import annotations

import tempfile
import unittest
import gzip
from pathlib import Path

from ordered_validity import Position, ValidationError, evaluate, load_positions


ROOT = Path(__file__).resolve().parents[1]


class CoreTests(unittest.TestCase):
    def test_example_retains_failures_and_first_identity(self) -> None:
        result = evaluate(
            load_positions(ROOT / "examples/position_ledger.csv"),
            quota=3,
            expected_slots=4,
            target_manifest={"target_1": "programme_alpha", "target_2": "programme_beta"},
        )
        cells = {(row["method"], row["target_id"]): row for row in result["cell_summaries"]}
        self.assertEqual(cells[("model_a", "target_1")]["identity_loss"], 1)
        self.assertEqual(cells[("model_a", "target_1")]["ordered_success"], 0)
        self.assertEqual(cells[("model_b", "target_2")]["chemistry_loss"], 1)
        self.assertEqual(result["metadata"]["positions"], 16)
        self.assertEqual(result["metadata"]["ordered_selected_methods"], ["model_a", "model_b"])

    def test_sparse_cell_is_completed_with_delivery_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sparse.csv"
            path.write_text(
                "method,target_id,position,delivered,source_valid,molecular_valid,identity\n"
                "a,t,0,1,1,1,CCO\n",
                encoding="utf-8",
            )
            result = evaluate(load_positions(path), quota=2, expected_slots=3)
        outcomes = [row["first_outcome"] for row in result["first_outcomes"]]
        self.assertEqual(outcomes, ["distinct_valid_pass", "delivery_failure", "delivery_failure"])

    def test_duplicate_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text(
                "method,target_id,position,delivered,source_valid,molecular_valid,identity\n"
                "a,t,0,1,1,1,CCO\n"
                "a,t,0,1,1,1,CCN\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValidationError, "duplicate position key"):
                load_positions(path)

    def test_non_nested_validity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text(
                "method,target_id,position,delivered,source_valid,molecular_valid,identity\n"
                "a,t,0,1,0,1,CCO\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValidationError, "molecular_valid requires source_valid"):
                load_positions(path)

    def test_gzip_position_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "positions.csv.gz"
            with gzip.open(path, "wt", newline="", encoding="utf-8") as handle:
                handle.write(
                    "method,target_id,position,delivered,source_valid,molecular_valid,identity\n"
                    "a,t,0,1,1,1,CCO\n"
                )
            positions = load_positions(path)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].identity, "CCO")

    def test_protocol_retains_wholly_missing_method(self) -> None:
        result = evaluate(
            load_positions(ROOT / "examples/position_ledger.csv"),
            quota=3,
            expected_slots=4,
            target_manifest={"target_1": "a", "target_2": "b"},
            expected_methods=["model_a", "model_b", "missing_model"],
        )
        missing = next(
            row for row in result["method_summaries"] if row["method"] == "missing_model"
        )
        self.assertEqual(missing["ordered_successful_targets"], 0)
        self.assertEqual(result["metadata"]["positions"], 24)

    def test_dependence_weighting_can_change_selection(self) -> None:
        units = {"a1": "large", "a2": "large", "a3": "large", "a4": "large", "b": "small"}
        success = {
            "method_a": {"a1", "a2", "a3"},
            "method_b": {"a1", "b"},
        }
        positions = [
            Position(
                method,
                target,
                0,
                True,
                True,
                target in passed,
                target if target in passed else "",
            )
            for method, passed in success.items()
            for target in units
        ]
        target_result = evaluate(
            positions,
            quota=1,
            expected_slots=1,
            target_manifest=units,
            expected_methods=["method_a", "method_b"],
            selection_weighting="equal_target",
        )
        unit_result = evaluate(
            positions,
            quota=1,
            expected_slots=1,
            target_manifest=units,
            expected_methods=["method_a", "method_b"],
            selection_weighting="equal_dependence_unit",
        )
        self.assertEqual(target_result["metadata"]["ordered_selected_methods"], ["method_a"])
        self.assertEqual(unit_result["metadata"]["ordered_selected_methods"], ["method_b"])

