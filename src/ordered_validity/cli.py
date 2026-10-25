from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import candidates_to_positions, load_candidate_csv
from .core import evaluate, write_evaluation
from .protocol import load_protocol
from .report import write_markdown_report
from .schema import ValidationError, load_positions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ordered-validity")
    sub = parser.add_subparsers(dest="command", required=True)

    raw = sub.add_parser("evaluate", help="evaluate raw SMILES under a protocol")
    raw.add_argument("candidates", type=Path)
    raw.add_argument("--protocol", type=Path, required=True)
    raw.add_argument("--output", type=Path, required=True)

    validate = sub.add_parser("validate-protocol", help="validate and display a protocol")
    validate.add_argument("protocol", type=Path)

    evaluate_parser = sub.add_parser(
        "evaluate-ledger", help="evaluate an already classified position ledger"
    )
    evaluate_parser.add_argument("ledger", type=Path)
    evaluate_parser.add_argument("--protocol", type=Path, required=True)
    evaluate_parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate-protocol":
            protocol = load_protocol(args.protocol)
            print(json.dumps(protocol.__dict__, indent=2, sort_keys=True))
            return 0
        protocol = load_protocol(args.protocol)
        if args.command == "evaluate":
            positions = candidates_to_positions(
                load_candidate_csv(args.candidates), protocol.identity
            )
        else:
            positions = load_positions(args.ledger)
        result = evaluate(
            positions,
            quota=protocol.quota,
            expected_slots=protocol.expected_slots,
            position_base=protocol.position_base,
            target_manifest=protocol.targets,
            expected_methods=protocol.methods,
            top_k=protocol.top_k,
            selection_weighting=protocol.aggregation,
        )
        write_evaluation(result, args.output)
        write_markdown_report(result, args.output, protocol.name)
        print(json.dumps(result["metadata"], indent=2, sort_keys=True))
        return 0
    except (ValidationError, FileNotFoundError, RuntimeError) as error:
        print(f"error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

