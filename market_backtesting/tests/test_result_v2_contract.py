"""Real frontend validator conformance, isolated from Web application code."""

import os
import subprocess
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest

from market_backtesting.cases.futures_roll_long import FuturesRollError, build_backtest_result
from market_backtesting.cases.futures_roll_long.evidence import _json
from market_backtesting.cases.futures_roll_long.visualization import validate_view_v2
from public_input_fixtures import fake_services, request

ROOT = Path(__file__).resolve().parents[2]


def test_generated_views_pass_canonical_frontend_validator(tmp_path: Path) -> None:
    fixtures = {}
    for profile in ("expiry_to_M1_v1", "expiry_to_Q1_v1"):
        result = build_backtest_result(fake_services()[0].run(request(profile)))  # type: ignore[arg-type]
        for name in ("returns", "drawdown"):
            fixtures[f"{profile}-{name}"] = asdict(getattr(result.views, name))
    destination = tmp_path / "views.json"
    destination.write_bytes(_json(fixtures))
    completed = subprocess.run(
        [
            "node_modules/.bin/vitest",
            "run",
            "--config",
            "../market_backtesting/tests/v2_contract.vitest.mjs",
        ],
        cwd=ROOT / "ui_web",
        env={**os.environ, "W2_V2_FIXTURE": str(destination)},
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.parametrize(
    "fault",
    [
        "version",
        "type",
        "x_unit",
        "y_unit",
        "duplicate_date",
        "date",
        "segment",
        "nonfinite",
        "bool",
        "axis",
        "binding",
        "event",
        "event_date",
        "details",
        "presentation",
        "mutable",
    ],
)
def test_producer_rejects_invalid_v2(fault: str) -> None:
    view = build_backtest_result(fake_services()[0].run(request())).views.returns
    binding = view.layers[0]
    line = binding.layer
    marks = line.data
    if fault == "version":
        view = replace(view, version=True)  # type: ignore[arg-type]
    elif fault == "type":
        line = replace(line, type="bar")
    elif fault == "x_unit":
        line = replace(line, x=replace(line.x, unit="timestamp"))
    elif fault == "y_unit":
        line = replace(line, y=replace(line.y, unit="percent"))
    elif fault in ("duplicate_date", "date", "segment", "nonfinite", "bool"):
        if fault == "duplicate_date":
            marks = (marks[0], marks[0], *marks[2:])
        elif fault == "date":
            marks = (replace(marks[0], x="2025-02-30"), *marks[1:])
        elif fault == "segment":
            marks = (marks[0], replace(marks[1], segment_id="other"), *marks[2:])
        else:
            bad: Any = float("nan") if fault == "nonfinite" else True
            marks = (replace(marks[0], y=bad), *marks[1:])
        line = replace(line, data=marks)
    elif fault == "axis":
        binding = replace(binding, x_axis="missing")
    elif fault == "binding":
        binding = replace(binding, id=view.layers[1].id)
    elif fault == "event":
        view = replace(view, events=(view.events[0], view.events[0]))
    elif fault == "event_date":
        view = replace(view, events=(replace(view.events[0], x="0000-01-01"),))
    elif fault == "details":
        view = replace(view, events=(replace(view.events[0], details=({"value": "bad"},)),))  # type: ignore[arg-type]
    elif fault == "presentation":
        view = replace(view, presentation=replace(view.presentation, zoom=1))  # type: ignore[arg-type]
    else:
        line = replace(line, data=list(marks))  # type: ignore[arg-type]
    view = replace(view, layers=(replace(binding, layer=line), *view.layers[1:]))
    with pytest.raises(FuturesRollError):
        validate_view_v2(view)
