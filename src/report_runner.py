#!/usr/bin/env python3
"""Run the CSV-to-Excel reporting job from n8n.

The preferred production path is to set REPORT_COMMAND to the user's existing
report script. When REPORT_COMMAND is not set, this runner creates a simple
Excel workbook from the uploaded CSV so the n8n flow can be tested end-to-end.
"""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from string import Formatter

import pandas as pd

LOGGER = logging.getLogger("report_runner")


class CommandFormatError(ValueError):
    """Raised when REPORT_COMMAND contains unsupported placeholders."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an Excel report from an uploaded CSV."
    )
    parser.add_argument(
        "--input-csv",
        required=True,
        type=Path,
        help="Path to the CSV uploaded through n8n.",
    )
    parser.add_argument(
        "--output-xlsx",
        required=True,
        type=Path,
        help="Path where the generated Excel report should be written.",
    )
    parser.add_argument(
        "--command",
        default=os.getenv("REPORT_COMMAND"),
        help=(
            "Optional command for the existing report script. Supports "
            "{input_csv}, {output_xlsx}, and {workdir} placeholders."
        ),
    )
    parser.add_argument(
        "--workdir",
        default=os.getenv("REPORT_WORKDIR", os.getcwd()),
        type=Path,
        help="Working directory used when running the report command.",
    )
    parser.add_argument(
        "--shell",
        action="store_true",
        default=os.getenv("REPORT_COMMAND_USE_SHELL", "").lower()
        in {"1", "true", "yes"},
        help="Run the report command through the shell. Prefer placeholders instead.",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity.",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def validate_paths(input_csv: Path, output_xlsx: Path, workdir: Path) -> None:
    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV does not exist: {input_csv}")
    if not input_csv.is_file():
        raise ValueError(f"Input CSV must be a file: {input_csv}")
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    workdir.mkdir(parents=True, exist_ok=True)


def ensure_supported_placeholders(command: str, values: dict[str, str]) -> None:
    allowed = set(values)
    requested = {
        field_name
        for _, field_name, _, _ in Formatter().parse(command)
        if field_name is not None
    }
    unsupported = requested - allowed
    if unsupported:
        unsupported_list = ", ".join(sorted(unsupported))
        allowed_list = ", ".join(sorted(allowed))
        raise CommandFormatError(
            f"Unsupported REPORT_COMMAND placeholder(s): {unsupported_list}. "
            f"Allowed placeholders: {allowed_list}."
        )


def format_command(command: str, input_csv: Path, output_xlsx: Path, workdir: Path) -> str:
    values = {
        "input_csv": str(input_csv),
        "output_xlsx": str(output_xlsx),
        "workdir": str(workdir),
    }
    ensure_supported_placeholders(command, values)
    return command.format(**values)


def run_existing_report_script(
    command: str,
    input_csv: Path,
    output_xlsx: Path,
    workdir: Path,
    use_shell: bool,
) -> None:
    formatted_command = format_command(command, input_csv, output_xlsx, workdir)
    env = os.environ.copy()
    env.update(
        {
            "INPUT_CSV": str(input_csv),
            "OUTPUT_XLSX": str(output_xlsx),
            "REPORT_WORKDIR": str(workdir),
        }
    )

    LOGGER.info("Running configured report command")
    if use_shell:
        completed = subprocess.run(
            formatted_command,
            cwd=workdir,
            env=env,
            shell=True,
            check=False,
        )
    else:
        completed = subprocess.run(
            shlex.split(formatted_command),
            cwd=workdir,
            env=env,
            shell=False,
            check=False,
        )

    if completed.returncode != 0:
        raise subprocess.CalledProcessError(completed.returncode, formatted_command)

    if not output_xlsx.exists():
        raise FileNotFoundError(
            "The report command finished successfully but did not create "
            f"the expected output file: {output_xlsx}"
        )


def set_sheet_widths(writer: pd.ExcelWriter, sheet_name: str, frame: pd.DataFrame) -> None:
    worksheet = writer.sheets[sheet_name]
    for index, column in enumerate(frame.columns, start=1):
        max_cell_length = frame[column].astype(str).map(len).max() if not frame.empty else 0
        width = min(max(max_cell_length, len(str(column))) + 2, 60)
        worksheet.column_dimensions[worksheet.cell(row=1, column=index).column_letter].width = width


def create_smoke_test_workbook(input_csv: Path, output_xlsx: Path) -> None:
    LOGGER.info("REPORT_COMMAND is not set; creating smoke-test workbook")
    data = pd.read_csv(input_csv)
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    summary = pd.DataFrame(
        [
            {"field": "generated_at_utc", "value": generated_at},
            {"field": "source_csv", "value": str(input_csv)},
            {"field": "row_count", "value": len(data)},
            {"field": "column_count", "value": len(data.columns)},
            {
                "field": "next_step",
                "value": "Set REPORT_COMMAND to run the Aha/GitLab/QuickBooks script.",
            },
        ]
    )

    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        data.to_excel(writer, sheet_name="Uploaded CSV", index=False)
        summary.to_excel(writer, sheet_name="Run Summary", index=False)
        set_sheet_widths(writer, "Uploaded CSV", data)
        set_sheet_widths(writer, "Run Summary", summary)


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    input_csv = args.input_csv.expanduser().resolve()
    output_xlsx = args.output_xlsx.expanduser().resolve()
    workdir = args.workdir.expanduser().resolve()

    try:
        validate_paths(input_csv, output_xlsx, workdir)
        if args.command:
            run_existing_report_script(
                args.command,
                input_csv,
                output_xlsx,
                workdir,
                args.shell,
            )
        else:
            create_smoke_test_workbook(input_csv, output_xlsx)
    except Exception:
        LOGGER.exception("Report generation failed")
        return 1

    LOGGER.info("Report created: %s", output_xlsx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
