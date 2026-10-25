"""Independent canonical byte fixture and input/evidence identity separation."""

import hashlib
import json
from dataclasses import replace
from datetime import date

import pytest

from data_lake import CoverageResult, EnsureResult, UnitFailure
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from market_research.descriptive.cases.trailing_return import (
    CalendarInput,
    InvalidPublicInput,
    construct_observations,
    prepare_inputs,
)
from observation_fixtures import (
    CODE,
    DAYS,
    CalendarFake,
    IndexFake,
    calendar_view,
    execute,
    index_view,
    job,
    pure_fixture,
)


def test_k_exact_v2_canonical_bytes_against_independently_written_payload() -> None:
    # A two-session fixture keeps this golden payload independently reviewable.
    days = (date(2024, 1, 8), date(2024, 1, 9))
    spec = job(days[1], days[1], 1)
    calendar = CalendarFake(days)
    index = IndexFake(days, {day: 100.0 for day in days})
    index.transform = lambda view: replace(
        view, records=tuple(replace(row, name="Demo", category=None) for row in view.records)
    )
    result = construct_observations(
        spec, prepare_inputs(spec, calendar_service=calendar, index_service=index)
    )
    golden = (
        '["trailing_return_inputs_v2","descriptive_missing_tolerant_v1",'
        '["trailing_cumulative_return_v1","000001.SH",[],1,"trading_sessions",'
        '"2024-01-09","2024-01-09","end_session","inclusive"],'
        '[["tushare_trade_calendar","calendar",1,"SSE","2024-01-08","2024-01-08",'
        '[1,1,0,0,0,true],[["SSE","2024-01-08",1,null]]],'
        '["tushare_trade_calendar","calendar",1,"SSE","2024-01-09","2024-01-09",'
        '[1,1,0,0,0,true],[["SSE","2024-01-09",1,null]]]],'
        '["tushare_index_daily","index_daily",1,["000001.SH"],"2024-01-08","2024-01-09",'
        "[2,2,0,0,0,true],"
        '[["000001.SH","000001","Demo","SSE",null,null,"2024-01-08",'
        '"0x1.9000000000000p+6","0x1.9000000000000p+6","0x1.9000000000000p+6",'
        '"0x1.9000000000000p+6","0x1.9000000000000p+6","0x0.0p+0","0x0.0p+0",'
        '"0x1.4000000000000p+3","0x1.4000000000000p+4"],'
        '["000001.SH","000001","Demo","SSE",null,null,"2024-01-09",'
        '"0x1.9000000000000p+6","0x1.9000000000000p+6","0x1.9000000000000p+6",'
        '"0x1.9000000000000p+6","0x1.9000000000000p+6","0x0.0p+0","0x0.0p+0",'
        '"0x1.4000000000000p+3","0x1.4000000000000p+4"]]],'
        '[["000001.SH","2024-01-08"],["000001.SH","2024-01-09"]],[],'
        '[["2024-01-09",["000001.SH","2024-01-09"],["000001.SH","2024-01-08"],[]]]]'
    ).encode("ascii")
    assert result.provenance.canonical_input_bytes == golden
    assert result.provenance.input_fingerprint == hashlib.sha256(golden).hexdigest()
    assert not golden.startswith(b"\xef\xbb\xbf")


def test_equivalent_calendar_collection_arrival_order_has_identical_bytes() -> None:
    spec, prepared = pure_fixture()
    first = construct_observations(spec, prepared)
    second = construct_observations(
        spec, replace(prepared, calendar_slices=tuple(reversed(prepared.calendar_slices)))
    )
    assert first.provenance.canonical_input_bytes == second.provenance.canonical_input_bytes
    assert first.provenance.input_fingerprint == second.provenance.input_fingerprint


def test_illegal_producer_row_order_is_rejected_before_canonicalization() -> None:
    spec, prepared = pure_fixture()
    item = prepared.calendar_slices[0]
    view = replace(item.final_export, records=tuple(reversed(item.final_export.records)))
    with pytest.raises(InvalidPublicInput):
        construct_observations(
            spec,
            replace(
                prepared,
                calendar_slices=(replace(item, final_export=view), *prepared.calendar_slices[1:]),
            ),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("close", 101.0),
        ("open", 99.0),
        ("volume", 11.0),
        ("pre_close", 20.0),
        ("name", "Changed metadata"),
        ("publisher", "Publisher"),
        ("category", None),
        ("change", -0.0),
    ],
)
def test_every_consumed_public_fact_and_metadata_changes_identity(
    field: str, value: object
) -> None:
    from observation_fixtures import altered

    spec, prepared = pure_fixture()
    assert prepared.index_slice is not None
    item = prepared.index_slice
    changed = replace(
        item.final_export,
        records=(
            altered(item.final_export.records[0], **{field: value}),
            *item.final_export.records[1:],
        ),
    )
    first = construct_observations(spec, prepared)
    second = construct_observations(
        spec, replace(prepared, index_slice=replace(item, final_export=changed))
    )
    assert first.job_identity == second.job_identity
    assert first.provenance.input_fingerprint != second.provenance.input_fingerprint


def test_final_coverage_distribution_changes_fingerprint_without_changing_available_rows() -> None:
    spec = job()
    index = IndexFake(DAYS[:5], {DAYS[0]: 100.0})
    prepared = prepare_inputs(spec, calendar_service=CalendarFake(DAYS), index_service=index)
    assert prepared.index_slice is not None
    item = prepared.index_slice
    changed = replace(item.final_export, coverage=CoverageResult(5, 1, 0, 2, 2, False))
    first = construct_observations(spec, prepared)
    second = construct_observations(
        spec, replace(prepared, index_slice=replace(item, final_export=changed))
    )
    assert first.provenance.available_daily_keys == second.provenance.available_daily_keys
    assert first.provenance.input_fingerprint != second.provenance.input_fingerprint


def test_preliminary_export_and_ensure_history_are_retained_but_excluded_from_hash() -> None:
    spec = job()
    closes = {day: 100.0 for day in DAYS[:5]}
    direct = prepare_inputs(
        spec, calendar_service=CalendarFake(DAYS), index_service=IndexFake(DAYS[:5], closes)
    )
    index = IndexFake(DAYS[:5], {})
    index.ensure_value = EnsureResult(
        5,
        0,
        5,
        0,
        5,
        0,
        False,
        tuple(UnitFailure((CODE, day), "earlier transient reason") for day in DAYS[:5]),
    )
    index.after_ensure = lambda view: index_view(index.calls[-1][1], DAYS[:5], closes)
    attempted = prepare_inputs(spec, calendar_service=CalendarFake(DAYS), index_service=index)
    assert direct.attempts != attempted.attempts
    a = construct_observations(spec, direct).provenance
    b = construct_observations(spec, attempted).provenance
    assert a.input_fingerprint == b.input_fingerprint
    assert a.canonical_input_bytes == b.canonical_input_bytes


def test_zero_candidate_and_all_unavailable_have_distinct_canonical_proofs() -> None:
    zero = execute(job(), (), {}).provenance
    missing = execute(job(), DAYS[:5], {}).provenance
    zero_payload = json.loads(zero.canonical_input_bytes)
    missing_payload = json.loads(missing.canonical_input_bytes)
    assert zero_payload[4] is None
    assert zero_payload[5:] == [[], [], []]
    assert missing_payload[4][-1] == []
    assert len(missing_payload[5]) == len(missing_payload[6]) == 5
    assert zero.input_fingerprint != missing.input_fingerprint
    assert [fact[0] for fact in missing_payload[7][0][3]] == ["anchor", "lookback"]


def test_calendar_padding_and_pretrade_date_are_fingerprinted() -> None:
    # Backward discovery includes a closed padding date. That public fact is consumed too.
    opens = (date(2024, 1, 11), date(2024, 1, 12), date(2024, 1, 15))
    spec = job(opens[-1], opens[-1])
    prepared = prepare_inputs(
        spec,
        calendar_service=CalendarFake(opens),
        index_service=IndexFake(opens, {day: 100.0 for day in opens}),
    )
    first = construct_observations(spec, prepared)
    block = prepared.calendar_slices[-1]
    changed = replace(
        block.final_export,
        records=(
            replace(block.final_export.records[0], pretrade_date=date(2024, 1, 8)),
            *block.final_export.records[1:],
        ),
    )
    second = construct_observations(
        spec,
        replace(
            prepared,
            calendar_slices=(*prepared.calendar_slices[:-1], replace(block, final_export=changed)),
        ),
    )
    assert first.provenance.expected_daily_keys == second.provenance.expected_daily_keys
    assert first.provenance.input_fingerprint != second.provenance.input_fingerprint


def test_profile_separation_unicode_signed_zero_and_no_private_provenance() -> None:
    spec, prepared = pure_fixture()
    provenance = construct_observations(spec, prepared).provenance
    payload = provenance.canonical_input_bytes
    assert json.loads(payload)[0] == "trailing_return_inputs_v2"
    assert b"\\u793a" in payload  # ensure_ascii, text otherwise unchanged.
    retired = payload.replace(b"trailing_return_inputs_v2", b"trailing_return_inputs_v1")
    assert hashlib.sha256(retired).hexdigest() != provenance.input_fingerprint
    for private in (b"unit_id", b"record_id", b"sqlite", b"token", b"timestamp", b"credential"):
        assert private not in payload.lower()
    assert provenance.prepared_inputs.index_slice is not None
    # A legal signed zero in a non-endpoint field is preserved rather than normalized.
    item = prepared.index_slice
    assert item is not None
    changed = replace(
        item.final_export,
        records=(
            replace(item.final_export.records[0], amount=-0.0),
            *item.final_export.records[1:],
        ),
    )
    signed = construct_observations(
        spec, replace(prepared, index_slice=replace(item, final_export=changed))
    )
    assert b"-0x0.0p+0" in signed.provenance.canonical_input_bytes


def test_pure_fixture_calendar_scope_and_dates_are_not_inferred_from_prices() -> None:
    spec, inputs = pure_fixture()
    request = TradeCalendarRange("SSE", DAYS[2], DAYS[4])
    wrong_calendar = calendar_view(request, ())
    with pytest.raises(InvalidPublicInput):
        construct_observations(
            spec,
            replace(
                inputs,
                calendar_slices=(CalendarInput(request, wrong_calendar), inputs.calendar_slices[1]),
            ),
        )
