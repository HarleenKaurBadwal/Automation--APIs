#!/usr/bin/env python3
"""Example adapter for the existing Aha/GitLab/QuickBooks report script.

Replace this file with your current script, or keep this shape and move your
API calls into `build_report`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Example CSV-to-Excel report script.")
    parser.add_argument("--input-csv", required=True, type=Path)
    parser.add_argument("--output-xlsx", required=True, type=Path)
    return parser.parse_args()


def build_report(input_csv: Path, output_xlsx: Path) -> None:
    uploaded_csv = pd.read_csv(input_csv)

    # Move the real Aha, GitLab, and QuickBooks API calls into this area.
    metadata = pd.DataFrame(
        [
            {
                "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
                "source_csv": str(input_csv),
                "status": "Replace this example with the real report script.",
            }
        ]
    )

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        uploaded_csv.to_excel(writer, sheet_name="Uploaded CSV", index=False)
        metadata.to_excel(writer, sheet_name="Report Metadata", index=False)


def main() -> int:
    args = parse_args()
    build_report(args.input_csv, args.output_xlsx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
