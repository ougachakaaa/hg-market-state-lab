"""Financial observation construction and complete public entry."""

from dataclasses import replace
from datetime import date
from math import log
from typing import Any

import pytest

from market_research.algorithm.pip import PipResult
from market_research.descriptive.cases.price_segmentation import (
    ObservationConstructionError,
    SegmentationRequest,
    construct_observations,
    construction,
    observe_price_segments,
    prepare_inputs,
)
from observation_fixtures import CODE, DAYS, CalendarFake, IndexFake


def prepare(prices: tuple[float, ...], epsilon: float = 0.001) -> Any:
    days = DAYS[: len(prices)]
    request = SegmentationRequest(CODE, days[0], days[-1], epsilon)
    cal, idx = CalendarFake(days), IndexFake(days, dict(zip(days, prices, strict=True)))
    return request, prepare_inputs(request, calendar_service=cal, index_service=idx)


@pytest.mark.parametrize(
    ("prices", "amplitude", "direction"),
    [((100.0, 120.0), 0.2, "up"), ((100.0, 80.0), -0.2, "down"), ((100.0, 100.0), 0.0, "flat")],
)
def test_two_points(prices: tuple[float, ...], amplitude: float, direction: str) -> None:
    request, inputs = prepare(prices)
    result = construct_observations(request, inputs)
    assert [(p.index, p.date, p.close) for p in result.important_points] == [
        (0, DAYS[0], prices[0]),
        (1, DAYS[1], prices[1]),
    ]
    (segment,) = result.segments
    assert segment.segment_identity == (request, 0, 1)
    assert (segment.start_date, segment.end_date, segment.start_close, segment.end_close) == (
        DAYS[0],
        DAYS[1],
        *prices,
    )
    assert segment.duration_sessions == 1
    assert segment.amplitude_ratio == pytest.approx(amplitude)
    assert segment.direction == direction
    assert segment.touches_start_boundary and segment.touches_end_boundary
    assert result.provenance is inputs
    assert result.diagnostics.max_reconstruction_error == 0


def test_multiple_segments_same_direction_and_diagnostics() -> None:
    request, inputs = prepare((100.0, 110.0, 200.0, 210.0), 0.01)
    result = construct_observations(request, inputs)
    assert [p.index for p in result.important_points] == [0, 1, 2, 3]
    assert [s.direction for s in result.segments] == ["up", "up", "up"]
    assert [s.duration_sessions for s in result.segments] == [1, 1, 1]
    assert [s.amplitude_ratio for s in result.segments] == pytest.approx([0.1, 200 / 110 - 1, 0.05])
    assert sum(s.duration_sessions for s in result.segments) == len(inputs.closes) - 1
    assert all(
        a.end_index == b.start_index
        for a, b in zip(result.segments, result.segments[1:], strict=False)
    )
    assert result.diagnostics.input_point_count == 4
    assert result.diagnostics.important_point_count == 4
    assert result.diagnostics.segment_count == 3
    assert result.diagnostics.algorithm_id == request.algorithm_id
    assert result.diagnostics.epsilon == request.epsilon
    assert result == construct_observations(request, inputs)


def test_actual_error_and_fingerprint_independent_of_epsilon() -> None:
    req, inputs = prepare((100.0, 110.0, 121.0), 0.1)
    result = construct_observations(req, inputs)
    expected = abs(log(110.0) - (log(100.0) + (log(121.0) - log(100.0)) / 2))
    assert result.diagnostics.max_reconstruction_error == expected
    req2, inputs2 = prepare((100.0, 110.0, 121.0), 0.0000001)
    assert inputs2.input_fingerprint == inputs.input_fingerprint
    assert construct_observations(req2, inputs2).request_identity != result.request_identity
    _, changed = prepare((100.0, 111.0, 121.0), 0.1)
    assert changed.input_fingerprint != inputs.input_fingerprint


@pytest.mark.parametrize(
    "change",
    [
        {"session_dates": (DAYS[1], DAYS[0], DAYS[2])},
        {"session_dates": (DAYS[0], date(2024, 1, 9))},
        {"closes": (100.0, float("nan"), 121.0)},
        {"closes": (100.0, -1.0, 121.0)},
        {"log_prices": (1.0, 2.0, 3.0)},
        {"input_fingerprint": ""},
        {"input_provenance": ()},
        {"input_point_count": 2},
    ],
)
def test_invalid_inputs(change: dict[str, object]) -> None:
    request, inputs = prepare((100.0, 110.0, 121.0))
    with pytest.raises(ObservationConstructionError) as exc:
        construct_observations(request, replace(inputs, **change))
    assert exc.value.category == "invalid_prepared_inputs"
    assert exc.value.stage == "input validation"
    assert exc.value.prepared_inputs is not None


def test_request_mismatch() -> None:
    request, inputs = prepare((100.0, 110.0))
    with pytest.raises(ObservationConstructionError):
        construct_observations(replace(request, epsilon=0.3), inputs)


@pytest.mark.parametrize(
    "result",
    [
        PipResult((1, 2), 0.0),
        PipResult((0, 1, 1, 2), 0.0),
        PipResult((0, 2, 1), 0.0),
        PipResult((0, 3), 0.0),
        PipResult((0, 2), 0.0, "other"),
        PipResult((0, 2), float("nan")),
        PipResult((0, 2), 1.0),
    ],
)
def test_invalid_pip_result(monkeypatch: pytest.MonkeyPatch, result: PipResult) -> None:
    request, inputs = prepare((100.0, 110.0, 121.0))
    monkeypatch.setattr(construction, "find_pips", lambda *args, **kwargs: result)
    with pytest.raises(ObservationConstructionError) as exc:
        construct_observations(request, inputs)
    assert exc.value.category == "invalid_algorithm_result"


def test_public_entry_uses_services() -> None:
    request = SegmentationRequest(CODE, DAYS[0], DAYS[2], 0.01)
    cal = CalendarFake(DAYS[:3])
    idx = IndexFake(DAYS[:3], {DAYS[0]: 100.0, DAYS[1]: 120.0, DAYS[2]: 90.0})
    result = observe_price_segments(request, calendar_service=cal, index_service=idx)
    assert [op for op, _ in cal.calls] == ["export"]
    assert [op for op, _ in idx.calls] == ["export"]
    assert [s.direction for s in result.segments] == ["up", "down"]
    assert result.provenance.input_provenance[0].final_export is not None
    assert result.provenance.input_provenance[1].final_export is not None


def test_changed_facts_do_not_match_retained_evidence() -> None:
    request, inputs = prepare((100.0, 110.0, 121.0))
    with pytest.raises(ObservationConstructionError, match="differ from retained evidence"):
        construct_observations(
            request,
            replace(
                inputs,
                closes=(100.0, 111.0, 121.0),
                log_prices=tuple(map(log, (100.0, 111.0, 121.0))),
            ),
        )


def test_pip_failure_preserves_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    request, inputs = prepare((100.0, 110.0))
    error = ArithmeticError("bad calculation")

    def fail(*args: object, **kwargs: object) -> None:
        raise error

    monkeypatch.setattr(construction, "find_pips", fail)
    with pytest.raises(ObservationConstructionError) as exc:
        construct_observations(request, inputs)
    assert exc.value.category == "algorithm_failure"
    assert exc.value.__cause__ is error


def test_nonfinite_amplitude_is_rejected() -> None:
    request, inputs = prepare((1e-308, 1e308))
    with pytest.raises(ObservationConstructionError) as exc:
        construct_observations(request, inputs)
    assert exc.value.category == "numerical_failure"


def test_case_dependency_and_pure_construction_boundaries() -> None:
    import ast
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src/market_research/descriptive/cases/price_segmentation"
    )
    for path in source.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ] + [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any(
            forbidden in name
            for name in imports
            for forbidden in (
                "trailing_return",
                "market_statistics",
                "data_snapshot",
                "ui_http",
                "ui_cli",
                "workbench",
            )
        )
        if path.name == "construction.py":
            assert not any(
                name in imports
                for name in (
                    "preparation",
                    "service",
                    "socket",
                    "requests",
                    "http",
                    "sqlite3",
                    "pathlib",
                )
            )
