"""Public proof validation, legal partial acquisition and explicit failure evidence."""

from collections.abc import Callable
from datetime import date
from types import SimpleNamespace

import pytest

from data_lake import CoverageResult, EnsureResult, InvalidRequestError, OperationError, UnitFailure
from data_lake.datasets.tushare_index_daily import (
    IndexDailyExport,
    IndexDailyRange,
    IndexDailyScope,
)
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport
from market_research.descriptive.cases.trailing_return import (
    IncompleteInput,
    InvalidPublicInput,
    UpstreamFailure,
    construct_observations,
    prepare_inputs,
)
from market_research.descriptive.observation import DateWindow
from observation_fixtures import CODE, DAYS, CalendarFake, IndexFake, job
from observation_fixtures import altered as replace


def partial_calendar(view: TradeCalendarExport) -> TradeCalendarExport:
    count = len(view.records)
    return replace(
        view, records=view.records[:-1], coverage=CoverageResult(count, count - 1, 1, 0, 0, False)
    )


def test_e_incomplete_final_calendar_fails_after_exactly_one_ensure_and_final_export() -> None:
    calendar = CalendarFake(DAYS)
    calendar.transform = partial_calendar
    calendar.ensure_value = EnsureResult(
        3, 2, 1, 0, 1, 0, False, (UnitFailure(("SSE", DAYS[4]), "unpublished calendar"),)
    )
    index = IndexFake(DAYS, {})
    with pytest.raises(IncompleteInput) as caught:
        prepare_inputs(job(), calendar_service=calendar, index_service=index)
    assert [op for op, _ in calendar.calls] == ["export", "ensure", "export"]
    assert len({request for _, request in calendar.calls}) == 1
    assert caught.value.evidence[0].ensure_result is calendar.ensure_value
    assert caught.value.evidence[0].final_export is not None
    assert index.calls == []


def test_final_calendar_proof_is_used_even_when_ensure_diagnostics_are_partial() -> None:
    calendar = CalendarFake(DAYS)
    calendar.transform = partial_calendar
    calendar.after_ensure = lambda view: view
    calendar.ensure_value = EnsureResult(
        3, 2, 1, 0, 1, 0, False, (UnitFailure(("SSE", DAYS[4]), "earlier failure"),)
    )
    prepared = prepare_inputs(
        job(),
        calendar_service=calendar,
        index_service=IndexFake(DAYS, {day: 100.0 for day in DAYS}),
    )
    assert prepared.calendar_slices[0].final_export.coverage.complete
    assert prepared.attempts[0].ensure_result is calendar.ensure_value


def test_legal_partial_index_ensure_diagnostics_retained_final_export_is_actual_proof() -> None:
    index = IndexFake(DAYS[:5], {DAYS[0]: 100.0})
    # Final proof may have a different public state distribution, independently of Ensure.
    index.after_ensure = lambda view: replace(view, coverage=CoverageResult(5, 1, 1, 1, 2, False))
    prepared = prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    result = construct_observations(job(), prepared)
    assert [op for op, _ in index.calls] == ["export", "ensure", "export"]
    assert all(request == index.calls[0][1] for _, request in index.calls)
    assert prepared.index_slice is not None
    proof = prepared.index_slice.final_export.coverage
    assert proof == CoverageResult(5, 1, 1, 1, 2, False)
    assert result.market_fact_coverage.overall.available_fact_units == 1
    assert result.unavailable_count == 3
    assert prepared.attempts[-1].ensure_result is not None


INDEX_ENVELOPE_MUTATIONS: list[dict[str, object]] = [
    {"dataset": "other"},
    {"view": "other"},
    {"export_schema_version": 2},
    {"export_schema_version": True},
    {"scope": IndexDailyScope(("000002.SZ",))},
    {"scope": SimpleNamespace(index_codes=CODE)},
    {"window": DateWindow(DAYS[0], DAYS[3])},
    {"window": SimpleNamespace(start_date=DAYS[0].isoformat(), end_date=DAYS[4])},
    {"coverage": CoverageResult(5, 5, 1, 0, 0, True)},
    {"coverage": CoverageResult(5, 5, 0, 0, 0, False)},
    {"coverage": CoverageResult(True, 1, 0, 0, 0, True)},
    {"coverage": replace(CoverageResult(5, 5, 0, 0, 0, True), complete=1)},
    {"coverage": CoverageResult(5, 5, -1, 1, 0, True)},
    {"coverage": CoverageResult(6, 5, 1, 0, 0, False)},
    {"coverage": None},
    {"records": None},
]


@pytest.mark.parametrize("changes", INDEX_ENVELOPE_MUTATIONS)
def test_g_invalid_index_envelope_is_not_missing_and_never_triggers_ensure(
    changes: dict[str, object],
) -> None:
    index = IndexFake(DAYS[:5], {day: 100.0 for day in DAYS[:5]})
    index.transform = lambda view: replace(view, **changes)
    with pytest.raises(InvalidPublicInput) as caught:
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    assert [op for op, _ in index.calls] == ["export"]
    assert caught.value.stage == "input_preparation"
    assert caught.value.evidence[-1].preliminary_export is not None


FLOAT_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_change",
    "volume",
    "amount",
)


@pytest.mark.parametrize("field", FLOAT_FIELDS)
@pytest.mark.parametrize("illegal", [None, True, 1, float("nan"), float("inf"), "100.0"])
def test_all_public_numeric_fields_are_validated_even_when_not_used_in_formula(
    field: str,
    illegal: object,
) -> None:
    index = IndexFake(DAYS[:5], {day: 100.0 for day in DAYS[:5]})
    index.transform = lambda view: replace(
        view, records=(replace(view.records[0], **{field: illegal}), *view.records[1:])
    )
    with pytest.raises(InvalidPublicInput):
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    assert [op for op, _ in index.calls] == ["export"]


@pytest.mark.parametrize(
    "changes",
    [
        {"volume": -1.0},
        {"amount": -1.0},
        {"index_code": "000002.SZ"},
        {"symbol": "wrong"},
        {"name": ""},
        {"market": " "},
        {"publisher": 123},
        {"category": ""},
        {"trade_date": DAYS[5]},
        {"trade_date": "2024-01-08"},
    ],
)
def test_record_metadata_identity_and_nonnegative_fields(changes: dict[str, object]) -> None:
    index = IndexFake(DAYS[:5], {day: 100.0 for day in DAYS[:5]})
    index.transform = lambda view: replace(
        view, records=(replace(view.records[0], **changes), *view.records[1:])
    )
    with pytest.raises(InvalidPublicInput):
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)


@pytest.mark.parametrize(
    "transform",
    [
        lambda view: replace(view, records=tuple(reversed(view.records))),
        lambda view: replace(view, records=(view.records[0], view.records[0], *view.records[2:])),
        lambda view: replace(view, records=view.records[:-1]),
    ],
)
def test_record_order_duplicates_and_success_count_disagreement(
    transform: Callable[[IndexDailyExport], IndexDailyExport],
) -> None:
    index = IndexFake(DAYS[:5], {day: 100.0 for day in DAYS[:5]})
    index.transform = transform
    with pytest.raises(InvalidPublicInput):
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)


CALENDAR_MUTATIONS: list[Callable[[TradeCalendarExport], TradeCalendarExport]] = [
    lambda v: replace(v, dataset="wrong"),
    lambda v: replace(v, view="wrong"),
    lambda v: replace(v, export_schema_version=True),
    lambda v: replace(v, scope=SimpleNamespace(exchange="SZSE")),
    lambda v: replace(v, window=DateWindow(DAYS[0], DAYS[1])),
    lambda v: replace(v, coverage=CoverageResult(3, 2, 0, 0, 0, False)),
    lambda v: replace(v, coverage=CoverageResult(3, True, 2, 0, 0, False)),
    lambda v: replace(v, records=(replace(v.records[0], is_open=True), *v.records[1:])),
    lambda v: replace(v, records=(replace(v.records[0], is_open=2), *v.records[1:])),
    lambda v: replace(v, records=(replace(v.records[0], exchange="SZSE"), *v.records[1:])),
    lambda v: replace(v, records=(replace(v.records[0], pretrade_date="20240101"), *v.records[1:])),
    lambda v: replace(v, records=(replace(v.records[0], cal_date=DAYS[0]), *v.records[1:])),
    lambda v: replace(v, records=(v.records[0], v.records[0], *v.records[2:])),
    lambda v: replace(v, records=tuple(reversed(v.records))),
    lambda v: replace(v, records=v.records[:-1]),
]


@pytest.mark.parametrize("transform", CALENDAR_MUTATIONS)
def test_malformed_calendar_rejected_before_any_ensure(
    transform: Callable[[TradeCalendarExport], TradeCalendarExport],
) -> None:
    calendar = CalendarFake(DAYS)
    calendar.transform = transform
    with pytest.raises(InvalidPublicInput):
        prepare_inputs(job(), calendar_service=calendar, index_service=IndexFake(DAYS, {}))
    assert [op for op, _ in calendar.calls] == ["export"]


def test_malformed_partial_view_is_rejected_before_ensure() -> None:
    index = IndexFake(DAYS[:5], {})
    index.transform = lambda view: replace(view, coverage=CoverageResult(5, 0, 4, 0, 0, False))
    with pytest.raises(InvalidPublicInput):
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    assert [op for op, _ in index.calls] == ["export"]


@pytest.mark.parametrize(
    "changes",
    [
        {"requested_units": True},
        {"attempted_units": -1},
        {"succeeded_units": 1},
        {"records_written": 1},
        {"complete": True},
        {"complete": 0},
        {"failures": ()},
        {"failures": (UnitFailure((CODE, DAYS[4]), "missing"),) * 5},
        {"failures": tuple(UnitFailure(("wrong", day), "missing") for day in DAYS[:5])},
        {"failures": tuple(UnitFailure((CODE, day), "") for day in DAYS[:5])},
        {"failures": tuple(UnitFailure((CODE, day.isoformat()), "missing") for day in DAYS[:5])},
    ],
)
def test_malformed_ensure_is_explicit_failure_before_final_export(
    changes: dict[str, object],
) -> None:
    index = IndexFake(DAYS[:5], {})
    valid = EnsureResult(
        5, 0, 5, 0, 5, 0, False, tuple(UnitFailure((CODE, day), "missing") for day in DAYS[:5])
    )
    index.ensure_value = replace(valid, **changes)
    with pytest.raises(InvalidPublicInput) as caught:
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    assert [op for op, _ in index.calls] == ["export", "ensure"]
    assert caught.value.evidence[-1].ensure_result is index.ensure_value


@pytest.mark.parametrize(
    "error", [OperationError("operation unavailable"), InvalidRequestError("public rejection")]
)
def test_operation_wide_errors_preserve_cause_and_obtained_evidence(error: Exception) -> None:
    index = IndexFake(DAYS[:5], {})
    index.ensure_value = error
    with pytest.raises(UpstreamFailure) as caught:
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    assert caught.value.__cause__ is error
    assert caught.value.request == index.calls[0][1]
    assert caught.value.evidence[-1].preliminary_export is not None
    assert caught.value.evidence[-1].final_export is None
    assert [op for op, _ in index.calls] == ["export", "ensure"]


def test_invalid_final_export_is_not_overridden_by_successful_ensure() -> None:
    index = IndexFake(DAYS[:5], {})
    index.ensure_value = EnsureResult(5, 0, 5, 5, 0, 5, True, ())
    index.after_ensure = lambda view: replace(view, dataset="wrong")
    with pytest.raises(InvalidPublicInput) as caught:
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    assert caught.value.evidence[-1].ensure_result is index.ensure_value
    assert caught.value.evidence[-1].final_export is not None


def test_unavailable_backward_calendar_block_fails_without_shortening_horizon() -> None:
    calendar = CalendarFake(DAYS)

    def mutate(view: TradeCalendarExport) -> TradeCalendarExport:
        if view.records[0].cal_date < DAYS[2]:
            return partial_calendar(view)
        return view

    calendar.transform = mutate
    calendar.ensure_value = EnsureResult(
        2, 1, 1, 0, 1, 0, False, (UnitFailure(("SSE", DAYS[1]), "calendar unavailable"),)
    )
    with pytest.raises(IncompleteInput):
        prepare_inputs(job(), calendar_service=calendar, index_service=IndexFake(DAYS, {}))


def test_index_units_cannot_include_a_closed_calendar_date() -> None:
    # Jan 9 is formally closed here. Returning it as a successful row is illegal.
    opens = (DAYS[0], DAYS[2], DAYS[3], DAYS[4])
    index = IndexFake(opens, {day: 100.0 for day in opens})
    index.transform = lambda view: replace(
        view, records=(replace(view.records[0], trade_date=DAYS[1]), *view.records[1:])
    )
    with pytest.raises(InvalidPublicInput, match="expected trading session"):
        prepare_inputs(
            job(DAYS[3], DAYS[4]), calendar_service=CalendarFake(opens), index_service=index
        )


def test_overlapping_calendar_slices_cannot_silently_disagree() -> None:
    # Sample begins on Sunday; the first backward block overlaps that closed prefix.
    anchor = date(2024, 1, 15)
    opens = (date(2024, 1, 11), date(2024, 1, 12), anchor)
    calendar = CalendarFake(opens)

    def contradict(view: TradeCalendarExport) -> TradeCalendarExport:
        if view.records[-1].cal_date == date(2024, 1, 14):
            return replace(view, records=(*view.records[:-1], replace(view.records[-1], is_open=1)))
        return view

    calendar.transform = contradict
    index = IndexFake(opens, {day: 100.0 for day in opens})
    with pytest.raises(InvalidPublicInput, match="Contradictory overlapping"):
        prepare_inputs(
            job(date(2024, 1, 14), anchor), calendar_service=calendar, index_service=index
        )
    assert not index.calls


def test_export_operation_error_does_not_trigger_ensure_or_hide_previous_evidence() -> None:
    class UnreadableIndex(IndexFake):
        def export(self, request: IndexDailyRange) -> IndexDailyExport:
            self.calls.append(("export", request))
            raise OperationError("cannot read public Index view")

    index = UnreadableIndex(DAYS, {})
    with pytest.raises(UpstreamFailure) as caught:
        prepare_inputs(job(), calendar_service=CalendarFake(DAYS), index_service=index)
    assert [op for op, _ in index.calls] == ["export"]
    assert len(caught.value.evidence) == 3
    assert caught.value.evidence[0].final_export is not None
    assert caught.value.evidence[-1].preliminary_export is None
