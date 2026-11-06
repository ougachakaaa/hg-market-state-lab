"""Explicit WP5 live gate in isolated external storage, never default user caches."""

import argparse
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

from futures_basis_live_acceptance import isolated_storage
from market_research.descriptive.cases.futures_basis.evidence import write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report_output = args.output / "delivery"
    command = [
        "market_research/scripts/futures_basis_report.py",
        "--product",
        "IM",
        "--start",
        "2024-01-01",
        "--end",
        "2026-10-30",
        "--quantile-points",
        "[0,0.25,0.5,0.75,1]",
        "--basis-value-edges",
        "[-1000,-500,-100,0,100,500,1000]",
        "--basis-ratio-edges",
        "[-1,-0.1,-0.01,0,0.01,0.1,1]",
        "--annualized-basis-ratio-edges",
        "[-10,-1,-0.1,0,0.1,1,10]",
        "--output",
        str(report_output),
    ]
    exit_code = 0
    with (
        isolated_storage(args.output / "dataset-cache") as audit,
        patch.object(sys, "argv", command),
    ):
        try:
            runpy.run_path(command[0], run_name="__main__")
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 1
    write_json(
        args.output / "acceptance.json",
        dict(
            status="PASS" if exit_code == 0 else "BLOCKED",
            exit_code=exit_code,
            window="2024-01-01..2026-10-30",
            isolation=audit,
            delivery=str(report_output),
        ),
    )


if __name__ == "__main__":
    main()
