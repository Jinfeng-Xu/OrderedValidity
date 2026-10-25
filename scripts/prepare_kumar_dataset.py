from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
from pathlib import Path


OUTCOME_FLAGS = {
    "delivery_failure": ("0", "0"),
    "source_validity_failure": ("1", "0"),
    "chemistry_failure": ("1", "0"),
    "duplicate_failure": ("1", "1"),
    "distinct_valid_pass": ("1", "1"),
}


def prepare(source: Path, output: Path, protocol_path: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    protocol_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    methods: list[str] = []
    targets: list[str] = []
    seen_methods: set[str] = set()
    seen_targets: set[str] = set()

    with source.open(newline="", encoding="utf-8") as source_handle:
        reader = csv.DictReader(source_handle)
        required = {
            "method",
            "target_id",
            "slot",
            "molecule_id",
            "source_valid",
            "recanonical_smiles",
            "first_failure",
        }
        missing = sorted(required - set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"source ledger missing columns: {', '.join(missing)}")

        with temporary.open("wb") as raw_handle:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                compresslevel=9,
                fileobj=raw_handle,
                mtime=0,
            ) as gzip_handle:
                with io.TextIOWrapper(gzip_handle, encoding="utf-8", newline="") as text_handle:
                    fields = [
                        "method",
                        "target_id",
                        "position",
                        "delivered",
                        "source_valid",
                        "molecular_valid",
                        "identity",
                        "record_id",
                    ]
                    writer = csv.DictWriter(text_handle, fieldnames=fields, lineterminator="\n")
                    writer.writeheader()
                    for row in reader:
                        outcome = row["first_failure"]
                        if outcome not in OUTCOME_FLAGS:
                            raise ValueError(f"unknown first outcome: {outcome}")
                        delivered, molecular_valid = OUTCOME_FLAGS[outcome]
                        source_valid = row["source_valid"]
                        identity = row["recanonical_smiles"] if molecular_valid == "1" else ""
                        writer.writerow(
                            {
                                "method": row["method"],
                                "target_id": row["target_id"],
                                "position": row["slot"],
                                "delivered": delivered,
                                "source_valid": source_valid,
                                "molecular_valid": molecular_valid,
                                "identity": identity,
                                "record_id": row["molecule_id"],
                            }
                        )
                        if row["method"] not in seen_methods:
                            seen_methods.add(row["method"])
                            methods.append(row["method"])
                        if row["target_id"] not in seen_targets:
                            seen_targets.add(row["target_id"])
                            targets.append(row["target_id"])
    os.replace(temporary, output)

    protocol = {
        "name": "Kumar molecular generation cohort",
        "methods": methods,
        "targets": [
            {"target_id": target, "dependence_unit": target} for target in targets
        ],
        "expected_slots": 100,
        "quota": 90,
        "position_base": 1,
        "top_k": 3,
        "identity": "canonical_isomeric_smiles",
        "aggregation": "equal_target",
    }
    protocol_path.write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare the public Kumar position ledger")
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    args = parser.parse_args()
    prepare(args.source, args.output, args.protocol)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
