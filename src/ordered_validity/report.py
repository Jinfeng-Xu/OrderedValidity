from __future__ import annotations

from pathlib import Path
from typing import Any


def write_markdown_report(result: dict[str, Any], output: str | Path, title: str) -> Path:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    metadata = result["metadata"]
    rows = result["method_summaries"]
    lines = [
        f"# {title}",
        "",
        f"Evaluated {metadata['methods']} methods across {metadata['targets']} targets and "
        f"{metadata['positions']} expected positions.",
        "",
        f"Selection weighting: `{metadata['selection_weighting']}`.",
        "",
        "| Method | Source successes | Ordered successes | Changed targets | "
        "Ordered target rate | Ordered programme rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        programme = row["equal_programme_rate"]
        programme_text = f"{programme:.3f}" if isinstance(programme, float) else "—"
        lines.append(
            f"| {row['method']} | {row['source_successful_targets']} | "
            f"{row['ordered_successful_targets']} | {row['changed_targets']} | "
            f"{row['equal_target_rate']:.3f} | {programme_text} |"
        )
    lines += [
        "",
        "Selected under the source rule: "
        + ", ".join(metadata["source_selected_methods"]),
        "",
        "Selected after ordered evaluation: "
        + ", ".join(metadata["ordered_selected_methods"]),
        "",
    ]
    path = output / "report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
