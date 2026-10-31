"""Deterministic public-service acceptance for segmentation input preparation."""

import hashlib
import math
from dataclasses import FrozenInstanceError, replace
from datetime import date
from typing import Any

import pytest

from data_lake import CoverageResult, EnsureResult, OperationError, UnitFailure
from market_research.descriptive.cases.price_segmentation import (
    InputPreparationError,
    SegmentationRequest,
    prepare_inputs,
)
from observation_fixtures import CODE, DAYS, CalendarFake, IndexFake, altered


def request(**changes: Any) -> SegmentationRequest:
    return replace(SegmentationRequest(CODE, DAYS[0], DAYS[2], 0.03), **changes)


def services() -> tuple[CalendarFake, IndexFake]:
    return CalendarFake(DAYS[:3]), IndexFake(
        DAYS[:3], {DAYS[0]: 100.0, DAYS[1]: 110.0, DAYS[2]: 121.0}
    )


def test_complete_and_fingerprint_fixture() -> None:
    cal, idx = services()
    result = prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert result.session_dates == DAYS[:3]
    assert result.closes == (100.0, 110.0, 121.0)
    assert result.log_prices == tuple(map(math.log, result.closes))
    assert result.input_point_count == 3
    canonical = (
        b'["price_segmentation_inputs_v1","tushare_index_daily","index_daily",1,'
        b'"000001.SH",[["2024-01-08","0x1.9000000000000p+6"],'
        b'["2024-01-09","0x1.b800000000000p+6"],'
        b'["2024-01-10","0x1.e400000000000p+6"]]]'
    )
    expected_digest = "1f9b75ad2c6f09d5e6203646a4d59e694b900c38b6dacb60c5e31c9c3048b3ab"
    assert hashlib.sha256(canonical).hexdigest() == expected_digest
    assert result.input_fingerprint == expected_digest
    assert result.input_provenance[0].final_export is not None
    assert result.input_provenance[1].final_export is not None
    assert result.input_provenance[0].request == cal.calls[0][1]
    assert result.input_provenance[1].request == idx.calls[0][1]
    assert result == prepare_inputs(request(), calendar_service=cal, index_service=idx)
    with pytest.raises(FrozenInstanceError):
        result.closes = ()  # type: ignore[misc]


def test_incomplete_calendar_ensure_once_and_failure() -> None:
    cal, idx = services()
    cal.transform = lambda v: replace(
        v, records=v.records[:-1], coverage=CoverageResult(3, 2, 1, 0, 0, False)
    )
    cal.ensure_value = EnsureResult(
        3, 2, 1, 0, 1, 0, False, (UnitFailure(("SSE", DAYS[2]), "missing"),)
    )
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "incomplete_calendar"
    assert [op for op, _ in cal.calls] == ["export", "ensure", "export"]
    assert len({r for _, r in cal.calls}) == 1
    assert exc.value.evidence[0].ensure_result == cal.ensure_value
    assert not idx.calls


def test_incomplete_index_ensure_once_and_failure() -> None:
    cal, idx = services()
    del idx.closes[DAYS[1]]
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "incomplete_price_series"
    assert [op for op, _ in idx.calls] == ["export", "ensure", "export"]
    assert len({r for _, r in idx.calls}) == 1
    assert exc.value.evidence[-1].final_export is not None


def test_ensure_diagnostics_do_not_change_fingerprint() -> None:
    cal, idx = services()
    baseline = prepare_inputs(request(), calendar_service=cal, index_service=idx)
    cal2, idx2 = services()
    cal2.transform = lambda v: replace(
        v, records=v.records[:-1], coverage=CoverageResult(3, 2, 1, 0, 0, False)
    )
    cal2.ensure_value = EnsureResult(3, 2, 1, 1, 0, 1, True, ())
    cal2.after_ensure = lambda v: v
    changed = prepare_inputs(request(epsilon=0.1), calendar_service=cal2, index_service=idx2)
    assert changed.input_fingerprint == baseline.input_fingerprint
    assert changed.request_identity != baseline.request_identity
    assert changed.input_provenance[0].ensure_result == cal2.ensure_value


def test_fingerprint_changes_with_fact_identity() -> None:
    cal, idx = services()
    base = prepare_inputs(request(), calendar_service=cal, index_service=idx)
    cal, idx = services()
    idx.closes[DAYS[1]] = 111.0
    assert (
        prepare_inputs(request(), calendar_service=cal, index_service=idx).input_fingerprint
        != base.input_fingerprint
    )
    cal = CalendarFake((DAYS[0], DAYS[2], DAYS[3]))
    idx = IndexFake((DAYS[0], DAYS[2], DAYS[3]), {DAYS[0]: 100.0, DAYS[2]: 110.0, DAYS[3]: 121.0})
    assert (
        prepare_inputs(
            request(end_date=DAYS[3]), calendar_service=cal, index_service=idx
        ).input_fingerprint
        != base.input_fingerprint
    )
    cal, idx = services()
    idx.transform = lambda v: replace(
        v, records=tuple(replace(row, index_code="000002.SZ", symbol="000002") for row in v.records)
    )
    assert (
        prepare_inputs(
            request(index_code="000002.SZ"), calendar_service=cal, index_service=idx
        ).input_fingerprint
        != base.input_fingerprint
    )


@pytest.mark.parametrize(
    "change",
    [
        {"index_code": "000001"},
        {"start_date": "2024-01-01"},
        {"end_date": date(9999, 1, 1)},
        {"epsilon": 0},
        {"epsilon": True},
        {"epsilon": float("nan")},
        {"research": "other"},
        {"algorithm_id": "other"},
        {"transform": "other"},
        {"time_axis": "other"},
        {"price_field": "other"},
    ],
)
def test_invalid_request_before_io(change: dict[str, object]) -> None:
    cal, idx = services()
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(**change), calendar_service=cal, index_service=idx)
    assert exc.value.category == "invalid_request"
    assert not cal.calls and not idx.calls


@pytest.mark.parametrize(
    "changes",
    [
        {"dataset": "wrong"},
        {"view": "wrong"},
        {"export_schema_version": True},
        {"coverage": CoverageResult(3, 3, 1, 0, 0, True)},
        {"records": ()},
    ],
)
def test_malformed_calendar_fails_without_ensure(changes: dict[str, object]) -> None:
    cal, idx = services()
    cal.transform = lambda v: altered(v, **changes)
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "invalid_public_export"
    assert [op for op, _ in cal.calls] == ["export"]
    assert not idx.calls


@pytest.mark.parametrize(
    "changes",
    [
        {"close": 0.0},
        {"close": -1.0},
        {"close": float("nan")},
        {"close": float("inf")},
        {"volume": -1.0},
        {"high": float("inf")},
        {"symbol": "bad"},
        {"name": ""},
        {"trade_date": DAYS[4]},
    ],
)
def test_illegal_index_rows_fail(changes: dict[str, object]) -> None:
    cal, idx = services()
    idx.transform = lambda v: replace(v, records=(altered(v.records[0], **changes), *v.records[1:]))
    with pytest.raises(InputPreparationError):
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert [op for op, _ in idx.calls] == ["export"]


@pytest.mark.parametrize("mutation", ["duplicate", "reverse", "missing"])
def test_invalid_index_order_and_count(mutation: str) -> None:
    cal, idx = services()

    def transform(v: Any) -> Any:
        rows = v.records
        if mutation == "duplicate":
            rows = (rows[0], rows[0], rows[2])
        elif mutation == "reverse":
            rows = tuple(reversed(rows))
        else:
            rows = rows[:-1]
        return replace(v, records=rows)

    idx.transform = transform
    with pytest.raises(InputPreparationError):
        prepare_inputs(request(), calendar_service=cal, index_service=idx)


def test_operation_failure_keeps_cause_and_previous_evidence() -> None:
    cal, idx = services()
    error = OperationError("unavailable")
    idx.ensure_value = error
    idx.closes.clear()
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "upstream_operation_failure"
    assert exc.value.stage == "index ensure"
    assert exc.value.__cause__ is error
    assert exc.value.evidence[0].final_export is not None
    assert exc.value.evidence[1].preliminary_export is not None


@pytest.mark.parametrize(
    "field",
    ["open", "high", "low", "close", "pre_close", "change", "pct_change", "volume", "amount"],
)
@pytest.mark.parametrize("bad", [None, True, 1, float("nan"), float("inf")])
def test_all_numeric_public_fields(field: str, bad: object) -> None:
    cal, idx = services()
    idx.transform = lambda v: replace(
        v, records=(altered(v.records[0], **{field: bad}), *v.records[1:])
    )
    with pytest.raises(InputPreparationError):
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert [op for op, _ in idx.calls] == ["export"]


@pytest.mark.parametrize("where", ["calendar", "index"])
@pytest.mark.parametrize("kind", ["scope", "window", "order", "duplicate", "counter", "schema"])
def test_invalid_public_proofs(where: str, kind: str) -> None:
    from types import SimpleNamespace

    cal, idx = services()

    def transform(v: Any) -> Any:
        if kind == "scope":
            return replace(
                v,
                scope=SimpleNamespace(exchange="SZSE")
                if where == "calendar"
                else SimpleNamespace(index_codes=("000002.SZ",)),
            )
        if kind == "window":
            return replace(v, window=SimpleNamespace(start_date=DAYS[1], end_date=DAYS[2]))
        if kind == "order":
            return replace(v, records=tuple(reversed(v.records)))
        if kind == "duplicate":
            return replace(v, records=(v.records[0], v.records[0], v.records[2]))
        if kind == "counter":
            return replace(v, coverage=CoverageResult(3, 2, 0, 0, 0, False))
        return replace(v, export_schema_version=2)

    if where == "calendar":
        cal.transform = transform
    else:
        idx.transform = transform
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "invalid_public_export"
    assert [op for op, _ in (cal.calls if where == "calendar" else idx.calls)] == ["export"]


def test_closed_date_cannot_be_an_index_record() -> None:
    cal, idx = services()
    cal.opens = (DAYS[0], DAYS[2])
    idx.sessions = cal.opens
    idx.transform = lambda v: replace(
        v, records=(replace(v.records[0], trade_date=DAYS[1]), v.records[1])
    )
    with pytest.raises(InputPreparationError, match="Unexpected trading date"):
        prepare_inputs(request(), calendar_service=cal, index_service=idx)


def test_fewer_than_two_sessions_fails_before_index_io() -> None:
    cal, idx = services()
    cal.opens = (DAYS[0],)
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "incomplete_calendar"
    assert not idx.calls


def test_bad_ensure_fails_without_reexport() -> None:
    cal, idx = services()
    idx.closes.clear()
    idx.ensure_value = EnsureResult(3, 0, 3, 0, 3, 0, False, ())
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "invalid_public_export"
    assert [op for op, _ in idx.calls] == ["export", "ensure"]
    assert exc.value.evidence[-1].preliminary_export is not None


def test_evidence_is_a_detached_immutable_snapshot() -> None:
    from types import SimpleNamespace

    cal, idx = services()
    rows: list[Any] = []
    scope = SimpleNamespace(exchange="SSE")

    def mutable(v: Any) -> Any:
        rows.extend(v.records)
        return replace(v, records=rows, scope=scope)

    cal.transform = mutable
    result = prepare_inputs(request(), calendar_service=cal, index_service=idx)
    rows.clear()
    scope.exchange = "other"
    evidence = result.input_provenance[0].final_export
    assert evidence is not None
    assert len(evidence.records) == 3 and evidence.scope == ("SSE",)
    with pytest.raises(FrozenInstanceError):
        evidence.coverage.complete = False  # type: ignore[misc]


def test_transformation_failure_preserves_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    from market_research.descriptive.cases.price_segmentation import preparation

    cal, idx = services()
    monkeypatch.setattr(preparation, "log", lambda _: float("inf"))
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert exc.value.category == "numerical_transformation_failure"
    assert len(exc.value.evidence) == 2
    assert exc.value.evidence[-1].final_export is not None


def test_index_ensure_success_retains_final_proof() -> None:
    cal, idx = services()
    idx.transform = lambda v: replace(
        v, records=v.records[:-1], coverage=CoverageResult(3, 2, 1, 0, 0, False)
    )
    idx.ensure_value = EnsureResult(3, 2, 1, 1, 0, 1, True, ())
    idx.after_ensure = lambda v: v
    result = prepare_inputs(request(), calendar_service=cal, index_service=idx)
    assert [op for op, _ in idx.calls] == ["export", "ensure", "export"]
    assert result.input_provenance[-1].ensure_result == idx.ensure_value
    assert result.input_provenance[-1].final_export is not None
    assert result.closes == (100.0, 110.0, 121.0)


def test_no_dependencies_on_other_cases_algorithm_or_statistics() -> None:
    import ast
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "src/market_research/descriptive/cases/price_segmentation"
    )
    forbidden = (
        "trailing_return",
        "market_statistics",
        "market_research.algorithm",
        "data_snapshot",
        "ui_http",
        "ui_cli",
        "workbench",
    )
    for path in source.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imports = [node.module or ""]
            else:
                continue
            assert not any(part in name for name in imports for part in forbidden)


def test_service_creation_never_precedes_request_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from market_research.descriptive.cases.price_segmentation import preparation

    def unexpected() -> Any:
        raise AssertionError("service factory called")

    monkeypatch.setattr(preparation, "create_calendar_service", unexpected)
    monkeypatch.setattr(preparation, "create_index_service", unexpected)
    with pytest.raises(InputPreparationError) as exc:
        prepare_inputs(request(index_code="bad"))
    assert exc.value.category == "invalid_request"


def test_conflicting_index_metadata_is_rejected() -> None:
    cal, idx = services()
    idx.transform = lambda v: replace(
        v, records=(v.records[0], replace(v.records[1], name="different"), v.records[2])
    )
    with pytest.raises(InputPreparationError, match="Conflicting index metadata"):
        prepare_inputs(request(), calendar_service=cal, index_service=idx)
