import tempfile
import unittest
from pathlib import Path

from ordered_validity.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_cli_evaluate_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evaluation"
            code = main(
                [
                    "evaluate-ledger",
                    str(ROOT / "examples/position_ledger.csv"),
                    "--protocol",
                    str(ROOT / "configs/example-protocol.json"),
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(code, 0)
            self.assertTrue((output / "first_outcome_ledger.csv").exists())
            self.assertTrue((output / "cell_summary.csv").exists())
            self.assertTrue((output / "method_summary.csv").exists())
            self.assertTrue((output / "metadata.json").exists())
            self.assertTrue((output / "report.md").exists())

    def test_cli_validate_protocol(self) -> None:
        self.assertEqual(
            main(["validate-protocol", str(ROOT / "configs/example-protocol.json")]), 0
        )
