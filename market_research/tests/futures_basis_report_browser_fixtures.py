"""Explicit synthetic edge reports for real Chromium, no market I/O."""

import argparse
import runpy
import subprocess
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from futures_basis_observation_fixtures import Services
from market_research.descriptive.cases.futures_basis.evidence import write_evidence
from market_statistics import CalculationFailure
from test_futures_basis_report import report

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    for scenario in ("empty", "failure"):
        services = Services()
        if scenario == "empty":
            services.futures = replace(services.futures, records=())
            result = report(services)
        else:
            with patch(
                "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
                side_effect=CalculationFailure("mean", "synthetic safe failure"),
            ):
                result = report(services)
        output = args.output / scenario
        output.mkdir()
        write_evidence(
            result,
            output,
            runtime=runpy.run_path(str(ROOT / "market_research/scripts/futures_basis_report.py"))[
                "runtime_context"
            ](),
        )
        if scenario == "failure":
            import json

            from market_research.descriptive.cases.futures_basis.evidence import write_json

            reader = json.loads((output / "report-data.json").read_bytes())
            reader["summary"] = (
                "</script><script>window.__wp5Injected=true</script>"
                '<img src=x onerror="window.__wp5Injected=true">'
            )
            write_json(output / "report-data.json", reader)
        subprocess.run(
            ["node", "scripts/package_futures_basis_report.mjs", str(output)],
            cwd=ROOT / "ui_web",
            check=True,
        )
        subprocess.run(
            ["node", "scripts/futures_basis_report_browser.mjs", str(output)],
            cwd=ROOT / "ui_web",
            check=True,
        )


if __name__ == "__main__":
    main()
