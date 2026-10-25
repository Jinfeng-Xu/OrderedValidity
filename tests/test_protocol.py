import unittest
from pathlib import Path

from ordered_validity.protocol import Protocol, load_protocol
from ordered_validity.schema import ValidationError


ROOT = Path(__file__).resolve().parents[1]


class ProtocolTests(unittest.TestCase):
    def test_example_protocol(self) -> None:
        protocol = load_protocol(ROOT / "configs/example-protocol.json")
        self.assertEqual(protocol.expected_slots, 4)
        self.assertEqual(protocol.targets["target_1"], "programme_alpha")
        self.assertEqual(protocol.aggregation, "equal_dependence_unit")

    def test_unknown_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "unsupported identity"):
            Protocol.from_dict(
                {
                    "name": "bad",
                    "methods": ["m"],
                    "targets": [{"target_id": "t", "dependence_unit": "p"}],
                    "expected_slots": 1,
                    "quota": 1,
                    "identity": "invented",
                    "aggregation": "equal_target",
                }
            )
