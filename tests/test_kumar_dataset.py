import unittest
from collections import Counter
from pathlib import Path

from ordered_validity import evaluate, load_positions, load_protocol


ROOT = Path(__file__).resolve().parents[1]


class KumarDatasetTests(unittest.TestCase):
    def test_complete_position_population_and_decisions(self) -> None:
        protocol = load_protocol(ROOT / "datasets/kumar/protocol.json")
        result = evaluate(
            load_positions(ROOT / "datasets/kumar/positions.csv.gz"),
            quota=protocol.quota,
            expected_slots=protocol.expected_slots,
            position_base=protocol.position_base,
            target_manifest=protocol.targets,
            expected_methods=protocol.methods,
            top_k=protocol.top_k,
            selection_weighting=protocol.aggregation,
        )
        outcomes = Counter(row["first_outcome"] for row in result["first_outcomes"])
        self.assertEqual(result["metadata"]["positions"], 116400)
        self.assertEqual(
            outcomes,
            {
                "delivery_failure": 4042,
                "source_invalid": 3,
                "molecular_invalid": 767,
                "duplicate_identity": 388,
                "distinct_valid_pass": 111200,
            },
        )
        methods = {row["method"]: row for row in result["method_summaries"]}
        self.assertEqual(methods["moljo"]["source_successful_targets"], 97)
        self.assertEqual(methods["moljo"]["ordered_successful_targets"], 91)
        self.assertEqual(methods["shepherd"]["source_successful_targets"], 95)
        self.assertEqual(methods["shepherd"]["ordered_successful_targets"], 95)
        self.assertEqual(sum(row["changed_targets"] for row in methods.values()), 28)
        self.assertEqual(
            result["metadata"]["source_selected_methods"],
            ["flowmol", "flowr", "moljo", "pocket2mol"],
        )
        self.assertEqual(
            result["metadata"]["ordered_selected_methods"],
            ["flowmol", "flowr", "pocket2mol"],
        )
