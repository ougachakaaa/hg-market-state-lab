"""Deterministic acceptance tests for the equity index futures basis monitor Task."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from futures_basis_support import (
    RUN_MONITOR,
    RUNTIME,
    TASK_PATH,
    FakeCalendar,
    FakeProduct,
    artifact_json,
    csv_rows,
    explicit_params,
    make_observation,
    make_result,
    read_state,
    relative_params,
    run_case,
    weekdays,
)

from data_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryError,
)

FAMILIES = ("IF", "IH", "IC", "IM")
SESSIONS = weekdays("2026-10-21", "2026-11-03")
CALENDAR_DAYS = weekdays("2026-10-19", "2026-11-03")


def make_products(
    families: tuple[str, ...] = FAMILIES,
    *,
    sessions: list[date] | None = None,
    start: date = date(2026, 10, 21),
    end: date = date(2026, 11, 3),
    overrides: dict[str, object] | None = None,
) -> FakeProduct:
    days = sessions if sessions is not None else SESSIONS
    outcomes: dict[str, object] = {
        family: make_result(family, days, start=start, end=end)
        for family in families
    }
    outcomes.update(overrides or {})
    return FakeProduct(outcomes)


def test_im_two_weeks_complete_success_and_three_outputs(tmp_path):
    open_dates = weekdays("2026-10-19", "2026-11-03")
    window_days = weekdays("2026-10-21", "2026-11-03")
    assert len(window_days) == 10
    calendar = FakeCalendar(open_dates)
    product = FakeProduct(
        {
            "IM": make_result(
                "IM",
                window_days,
                start=date(2026, 10, 21),
                end=date(2026, 11, 3),
            )
        }
    )
    outcome = run_case(
        tmp_path,
        relative_params(
            "最近两周", original="查询 IM 最近两周的年化基差"
        ),
        product=product,
        calendar=calendar,
    )
    assert outcome["status"] == "PASS"
    assert outcome["overall_status"] == "complete"
    assert outcome["coverage_status"] == "verified_complete"
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS", "PASS", "PASS"]
    assert len(product.requests) == 1
    assert product.requests[0].start_trade_date == "2026-10-21"
    assert product.requests[0].end_trade_date == "2026-11-03"

    state = read_state(tmp_path, outcome)
    labels = [item["payload"]["label"] for item in state["artifacts"]]
    assert labels == [
        "CFFEX calendar export",
        "resolution.json",
        "basis_daily.csv",
        "acquisition evidence",
        "result.json",
        "REPORT.md",
        "verification.json",
    ]
    assert all(
        item["payload"]["evidence"]
        for item in state["gate_outcomes"]
        if item["payload"]["status"] == "PASS"
    )
    for item in state["artifacts"]:
        assert not Path(item["payload"]["source_location"]).exists()
        stored = tmp_path / "runs" / outcome["run_id"] / item["payload"]["stored_path"]
        assert stored.is_file()

    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["task_id"] == "equity_index_futures_basis_monitor"
    assert result["task_version"] == "1"
    assert result["task_sha256"] == outcome["task_sha256"]
    assert result["original_request"] == "查询 IM 最近两周的年化基差"
    assert result["requested_window"] == {
        "start_date": "2026-10-21",
        "end_date": "2026-11-03",
    }
    assert result["resolved_inputs"]["resolution"]["anchor_date"] == "2026-11-03"
    assert result["resolved_inputs"]["resolution"]["anchor_rule"] == (
        "latest_cffex_open_date_strictly_before_execution_date"
    )
    assert result["expected_sessions"]["trade_date_count"] == 10
    assert result["families"][0]["status"] == "success"
    assert result["families"][0]["first_observation_date"] == "2026-10-21"
    assert result["families"][0]["last_observation_date"] == "2026-11-03"
    assert result["families"][0]["coverage_status"] == "verified_complete"
    assert result["families"][0]["observation_count"] == 40
    assert result["detail_file"]["artifact_id"] == outcome["csv"]["artifact_id"]
    assert result["detail_file"]["row_count"] == 40
    assert result["overall_status"] == "complete"
    assert result["coverage_status"] == "verified_complete"

    rows = csv_rows(tmp_path, outcome)
    assert rows[0] == [
        "trade_date",
        "futures_family",
        "underlying_code",
        "contract_code",
        "contract_slot",
        "delist_date",
        "days_to_delist",
        "underlying_close",
        "futures_close",
        "basis_pct",
        "annualized_basis_pct",
    ]
    assert len(rows) == 41
    assert [row[4] for row in rows[1:5]] == ["M0", "M1", "Q1", "Q2"]
    assert rows[1][0] == "2026-10-21"
    assert rows[-1][0] == "2026-11-03"
    assert rows[1][1] == "IM"
    assert rows[1][2] == "000852.SH"

    report = (
        tmp_path / "runs" / outcome["run_id"] / outcome["report"]["stored_path"]
    ).read_text(encoding="utf-8")
    for heading in (
        "## Query and actual range",
        "## Latest session by family",
        "## Coverage and failures",
        "## Source, formula and units",
        "## Near-expiry sensitivity",
        "## Limitations",
    ):
        assert heading in report
    assert "Overall status: complete" in report
    assert "Coverage status: verified_complete" in report
    assert "2026-11-03" in report
    assert rows[4][10] in report

    verification = artifact_json(tmp_path, outcome, outcome["verification"])
    assert verification["passed"] is True
    assert verification["gate_decision"]["status"] == "PASS"
    assert all(item["status"] == "pass" for item in verification["checks"])

    manifest = json.loads(
        (tmp_path / "runs" / outcome["run_id"] / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["task"]["task_id"] == "equity_index_futures_basis_monitor"
    assert manifest["resolved_inputs"] == result["resolved_inputs"]
    assert manifest["task_sha256"] == outcome["task_sha256"]


def test_four_family_complete_query_and_csv_order(tmp_path):
    product = make_products()
    outcome = run_case(
        tmp_path,
        explicit_params(FAMILIES),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["status"] == "PASS"
    assert outcome["overall_status"] == "complete"
    assert outcome["coverage_status"] == "verified_complete"
    assert len(product.requests) == 4
    rows = csv_rows(tmp_path, outcome)
    assert len(rows) == 161
    assert [row[1] for row in rows[1:5]] == ["IF", "IF", "IF", "IF"]
    assert [row[4] for row in rows[1:5]] == ["M0", "M1", "Q1", "Q2"]
    assert [row[1] for row in rows[5:9]] == ["IH"] * 4
    assert [row[1] for row in rows[9:13]] == ["IC"] * 4
    assert [row[1] for row in rows[13:17]] == ["IM"] * 4
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert [item["futures_family"] for item in result["families"]] == list(FAMILIES)
    assert sum(item["observation_count"] for item in result["families"]) == 160


def test_csv_contract_code_is_final_tie_breaker():
    sort_key = RUNTIME["_csv_sort_key"]
    later_code = ("2026-11-03", "IC", "000905.SH", "ICZ.CFX", "M0", "2026-12-01")
    earlier_code = ("2026-11-03", "IC", "000905.SH", "ICA.CFX", "M0", "2027-01-01")
    assert sorted([later_code, earlier_code], key=sort_key) == [earlier_code, later_code]


def test_ic_im_twenty_calendar_sessions_and_saved_authorization(tmp_path):
    sessions = weekdays("2026-10-01", "2026-11-03", {"2026-10-01", "2026-10-02"})
    assert len(sessions) > 20
    selected = sessions[-20:]
    calendar = FakeCalendar(sessions)
    product = FakeProduct({
        family: make_result(family, selected, start=selected[0], end=selected[-1])
        for family in ("IC", "IM")
    })
    authorization = "用户授权：IC 和 IM 最近20个 CFFEX 交易日"
    outcome = run_case(
        tmp_path,
        relative_params("最近20个交易日", ("IC", "IM")),
        product=product,
        calendar=calendar,
        authorization=authorization,
    )
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS"] * 3
    assert len(product.requests) == 2
    assert [item.futures_family for item in product.requests] == ["IC", "IM"]
    assert all(item.start_trade_date == selected[0].isoformat() for item in product.requests)
    assert all(item.end_trade_date == selected[-1].isoformat() for item in product.requests)
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["resolved_inputs"]["resolution"]["anchor_date"] == selected[-1].isoformat()
    assert result["resolved_inputs"]["resolution"]["authorization_reference"] == authorization
    assert [item["observation_count"] for item in result["families"]] == [80, 80]
    assert len(csv_rows(tmp_path, outcome)) == 161
    state = read_state(tmp_path, outcome)
    saved_resolution = state["manifest"]["resolved_inputs"]["resolution"]
    assert saved_resolution["authorization_reference"] == authorization
    assert all(item["payload"]["evidence"] for item in state["gate_outcomes"])
    assert any(item["payload"]["details"].get("authorization_reference") == authorization
               for item in state["events"])


def test_saved_acquisition_mismatch_fails_delivery(tmp_path, monkeypatch):
    original = RUNTIME["_acquisition_payload"]

    def altered(**kwargs):
        payload = original(**kwargs)
        payload["families"][0]["result"]["observations"][0]["annualized_basis_pct"] = 999.0
        return payload

    monkeypatch.setitem(RUN_MONITOR.__globals__, "_acquisition_payload", altered)
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=make_products(("IM",)),
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["gates"][-1]["status"] == "FAIL"
    verification = artifact_json(tmp_path, outcome, outcome["verification"])
    assert any(item["check"] == "persisted_artifact_consistency"
               and item["status"] == "fail" for item in verification["checks"])


def test_one_family_failure_preserves_successful_data(tmp_path):
    product = make_products(
        overrides={
            "IC": CFFEXEquityIndexBasisHistoryError(
                "source_failure", "synthetic IC source unavailable"
            )
        }
    )
    outcome = run_case(
        tmp_path,
        explicit_params(FAMILIES),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["status"] == "FAIL"
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS", "FAIL", "BLOCKED"]
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["overall_status"] == "partial"
    assert result["coverage_status"] == "mixed"
    assert result["families"][2]["futures_family"] == "IC"
    assert result["families"][2]["status"] == "failed"
    assert result["families"][2]["product_error_reason"] == "source_failure"
    assert result["families"][2]["source_identity"] is None
    assert result["families"][2]["first_observation_date"] is None
    assert result["families"][2]["observation_count"] == 0
    assert result["families"][0]["status"] == "success"
    assert result["failures"] == [
        {
            "stage": "acquisition",
            "futures_family": "IC",
            "reason": "source_failure",
            "message": "Public product failed (source_failure); see the classified reason.",
            "scope": "family IC requested window 2026-10-21..2026-11-03",
        }
    ]
    rows = csv_rows(tmp_path, outcome)
    assert len(rows) == 121
    assert {row[1] for row in rows[1:]} == {"IF", "IH", "IM"}
    verification = artifact_json(tmp_path, outcome, outcome["verification"])
    assert verification["gate_decision"]["status"] == "BLOCKED"
    assert verification["passed"] is True


def test_all_families_fail_header_only_csv(tmp_path):
    product = FakeProduct(
        {
            family: CFFEXEquityIndexBasisHistoryError(
                "no_observations", f"synthetic {family} has no observations"
            )
            for family in FAMILIES
        }
    )
    outcome = run_case(
        tmp_path,
        explicit_params(FAMILIES),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["status"] == "FAIL"
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS", "FAIL", "BLOCKED"]
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["overall_status"] == "failed"
    assert result["coverage_status"] == "not_applicable"
    assert len(result["failures"]) == 4
    assert all(item["status"] == "failed" for item in result["families"])
    rows = csv_rows(tmp_path, outcome)
    assert len(rows) == 1
    assert rows[0][0] == "trade_date"
    report = (
        tmp_path / "runs" / outcome["run_id"] / outcome["report"]["stored_path"]
    ).read_text(encoding="utf-8")
    assert "Overall status: failed" in report
    assert "Coverage status: not_applicable" in report
    assert "no_observations" in report


def test_missing_latest_expected_session_is_partial_and_reports_recent_gap(tmp_path):
    missing = {(date(2026, 11, 3).isoformat(), slot) for slot in ("M0", "M1", "Q1", "Q2")}
    product = FakeProduct(
        {
            "IM": make_result(
                "IM",
                SESSIONS,
                start=date(2026, 10, 21),
                end=date(2026, 11, 3),
                drop=missing,
            )
        }
    )
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["status"] == "FAIL"
    assert outcome["overall_status"] == "partial"
    assert outcome["coverage_status"] == "verified_partial"
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS", "PASS", "FAIL"]
    result = artifact_json(tmp_path, outcome, outcome["result"])
    family = result["families"][0]
    assert family["coverage_status"] == "verified_partial"
    assert family["missing_expected_trade_dates"] == ["2026-11-03"]
    assert family["latest_expected_trade_date"] == "2026-11-03"
    assert family["latest_expected_session_observed"] is False
    assert family["last_observation_date"] == "2026-11-02"
    assert any("recent gap" in item for item in result["unfinished_scope"])
    assert any("2026-11-03" in item for item in result["unfinished_scope"])
    assert len(csv_rows(tmp_path, outcome)) == 37


def test_unexpected_observed_date_is_partial_and_fails_delivery(tmp_path):
    extra = make_observation("IM", date(2026, 11, 4), "M0")
    product = FakeProduct(
        {
            "IM": make_result(
                "IM",
                SESSIONS,
                start=date(2026, 10, 21),
                end=date(2026, 11, 3),
                extra=[extra],
            )
        }
    )
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["coverage_status"] == "verified_partial"
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS", "PASS", "FAIL"]
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["families"][0]["unexpected_observed_trade_dates"] == ["2026-11-04"]
    assert result["overall_status"] == "partial"
    assert any("2026-11-04" in item for item in result["unfinished_scope"])


def test_incomplete_calendar_leaves_coverage_unverified_and_blocks_delivery(tmp_path):
    product = make_products(("IM",))
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS, complete=False),
    )
    assert outcome["status"] == "BLOCKED"
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS", "PASS", "BLOCKED"]
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["expected_sessions"]["status"] == "unverified"
    assert result["expected_sessions"]["unverified_reason"]
    assert result["families"][0]["coverage_status"] == "unverified"
    assert result["coverage_status"] == "unverified"
    assert result["overall_status"] == "partial"
    assert len(csv_rows(tmp_path, outcome)) == 41


def test_calendar_unavailable_for_relative_input_blocks_resolution(tmp_path):
    product = FakeProduct({})
    calendar = FakeCalendar([], unavailable=True)
    outcome = run_case(
        tmp_path,
        relative_params("最近两周"),
        product=product,
        calendar=calendar,
    )
    assert outcome["status"] == "BLOCKED"
    assert [gate["status"] for gate in outcome["gates"]] == [
        "BLOCKED",
        "BLOCKED",
        "BLOCKED",
    ]
    assert product.requests == []
    assert outcome["result"] is None
    assert outcome["csv"] is None
    assert outcome["report"] is None
    state = read_state(tmp_path, outcome)
    assert [item["payload"]["label"] for item in state["artifacts"]] == [
        "resolution.json"
    ]
    resolution = artifact_json(
        tmp_path,
        outcome,
        {
            "stored_path": state["artifacts"][0]["payload"]["stored_path"],
        },
    )
    assert resolution["resolved_inputs"]["resolution"]["status"] == "BLOCKED"
    assert "calendar" in resolution["resolved_inputs"]["resolution"]


@pytest.mark.parametrize(
    ("expression", "anchor", "start", "end"),
    [
        ("最近两周", None, "2026-10-21", "2026-11-03"),
        ("最近5个交易日", None, "2026-10-28", "2026-11-03"),
        ("最近五个交易日", None, "2026-10-28", "2026-11-03"),
        ("最近10个交易日", None, "2026-10-21", "2026-11-03"),
        ("最近两周", "2026-10-30", "2026-10-17", "2026-10-30"),
        ("最近两周", "2026-11-03", "2026-10-21", "2026-11-03"),
    ],
)
def test_relative_resolution_rules(tmp_path, expression, anchor, start, end):
    start_day = date.fromisoformat(start)
    end_day = date.fromisoformat(end)
    session_days = weekdays(start, end)
    product = FakeProduct(
        {
            "IM": make_result(
                "IM", session_days, start=start_day, end=end_day
            )
        }
    )
    outcome = run_case(
        tmp_path,
        relative_params(expression, anchor=anchor),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["status"] == "PASS", outcome
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["requested_window"] == {"start_date": start, "end_date": end}
    resolution = result["resolved_inputs"]["resolution"]
    expected_rule = (
        "user_supplied_anchor"
        if anchor
        else "latest_cffex_open_date_strictly_before_execution_date"
    )
    assert resolution["anchor_date"] == end
    assert resolution["anchor_rule"] == expected_rule
    assert result["overall_status"] == "complete"


@pytest.mark.parametrize(
    ("params", "status"),
    [
        (explicit_params(("IX",)), "FAIL"),
        (
            {
                "original_request": "查询股指期货基差",
                "futures_families": ["股指期货"],
                "start_date": "2026-10-21",
                "end_date": "2026-11-03",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "查询重复 family",
                "futures_families": ["IM", "IM"],
                "start_date": "2026-10-21",
                "end_date": "2026-11-03",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "查询空 family",
                "futures_families": [],
                "start_date": "2026-10-21",
                "end_date": "2026-11-03",
            },
            "BLOCKED",
        ),
        (
            {
                "original_request": "缺少 family",
                "start_date": "2026-10-21",
                "end_date": "2026-11-03",
            },
            "BLOCKED",
        ),
        (
            {
                "original_request": "非法日期",
                "futures_families": ["IM"],
                "start_date": "2026-02-30",
                "end_date": "2026-11-03",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "起止倒置",
                "futures_families": ["IM"],
                "start_date": "2026-11-03",
                "end_date": "2026-10-21",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "未来日期",
                "futures_families": ["IM"],
                "start_date": "2026-10-21",
                "end_date": "2026-11-05",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "显式和相对混用",
                "futures_families": ["IM"],
                "start_date": "2026-10-21",
                "end_date": "2026-11-03",
                "date_expression": "最近两周",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "不支持的相对表达",
                "futures_families": ["IM"],
                "date_expression": "最近一个月",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "锚点非交易日",
                "futures_families": ["IM"],
                "date_expression": "最近两周",
                "anchor_date": "2026-11-01",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "锚点在未来",
                "futures_families": ["IM"],
                "date_expression": "最近两周",
                "anchor_date": "2026-11-05",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "缺少日期",
                "futures_families": ["IM"],
            },
            "BLOCKED",
        ),
        (
            {
                "original_request": "只有开始日期",
                "futures_families": ["IM"],
                "start_date": "2026-10-21",
            },
            "FAIL",
        ),
        (
            {
                "original_request": "显式日期带锚点",
                "futures_families": ["IM"],
                "start_date": "2026-10-21",
                "end_date": "2026-11-03",
                "anchor_date": "2026-11-03",
            },
            "FAIL",
        ),
    ],
)
def test_invalid_or_missing_inputs_create_run_and_block_market_access(tmp_path, params, status):
    product = FakeProduct({})
    calendar = FakeCalendar(CALENDAR_DAYS)
    outcome = run_case(tmp_path, params, product=product, calendar=calendar)
    assert outcome["status"] == status
    assert outcome["gates"][0]["status"] == status
    assert outcome["gates"][1]["status"] == "BLOCKED"
    assert outcome["gates"][2]["status"] == "BLOCKED"
    assert product.requests == []
    assert outcome["result"] is None
    assert outcome["csv"] is None
    assert outcome["report"] is None
    state = read_state(tmp_path, outcome)
    labels = [item["payload"]["label"] for item in state["artifacts"]]
    assert labels == ["resolution.json"] or labels == [
        "CFFEX calendar export",
        "resolution.json",
    ]
    assert labels[-1] == "resolution.json"


def test_no_authorization_explicit_inputs_resolve_but_no_market_access(tmp_path):
    product = make_products(("IM",))
    calendar = FakeCalendar(CALENDAR_DAYS)
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=product,
        calendar=calendar,
        authorization=None,
    )
    assert outcome["status"] == "BLOCKED"
    assert [gate["status"] for gate in outcome["gates"]] == [
        "PASS",
        "BLOCKED",
        "BLOCKED",
    ]
    assert product.requests == []
    assert calendar.calls == []
    assert outcome["result"] is None
    state = read_state(tmp_path, outcome)
    assert [item["payload"]["label"] for item in state["artifacts"]] == [
        "resolution.json"
    ]
    resolution = artifact_json(
        tmp_path,
        outcome,
        {"stored_path": state["artifacts"][0]["payload"]["stored_path"]},
    )
    assert resolution["resolved_inputs"]["resolution"]["calendar"]["status"] == (
        "not_accessed"
    )
    assert resolution["resolved_inputs"]["resolution"]["authorization_reference"] is None


def test_window_before_listing_uses_effective_window(tmp_path):
    start = date(2022, 1, 1)
    end = date(2022, 7, 25)
    open_dates = weekdays("2022-01-01", "2022-07-25")
    product = FakeProduct(
        {
            "IM": make_result(
                "IM",
                [date(2022, 7, 22), date(2022, 7, 25)],
                start=start,
                end=end,
                listing="2022-07-22",
            )
        }
    )
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",), start="2022-01-01", end="2022-07-25"),
        product=product,
        calendar=FakeCalendar(open_dates),
    )
    assert outcome["status"] == "PASS"
    result = artifact_json(tmp_path, outcome, outcome["result"])
    family = result["families"][0]
    assert family["coverage_status"] == "verified_complete"
    assert family["expected_trade_date_count"] == 2
    assert family["missing_expected_trade_dates"] == []
    assert family["first_observation_date"] == "2022-07-22"
    assert result["expected_sessions"]["trade_date_count"] == len(
        weekdays("2022-01-01", "2022-07-25")
    )


def test_slot_inconsistency_fails_delivery(tmp_path):
    broken = make_result(
        "IM",
        SESSIONS,
        start=date(2026, 10, 21),
        end=date(2026, 11, 3),
        drop={(date(2026, 10, 22).isoformat(), "Q2")},
    )
    product = FakeProduct({"IM": broken})
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert [gate["status"] for gate in outcome["gates"]] == ["PASS", "PASS", "FAIL"]
    verification = artifact_json(tmp_path, outcome, outcome["verification"])
    assert verification["passed"] is False
    assert any(
        item["check"] == "panel_slot_completeness" and item["status"] == "fail"
        for item in verification["checks"]
    )
    assert verification["gate_decision"]["status"] == "FAIL"


def test_signed_zero_and_product_values_are_copied_verbatim(tmp_path):
    base = make_result(
        "IM", SESSIONS, start=date(2026, 10, 21), end=date(2026, 11, 3)
    )
    observations = list(base.observations)
    observations[0] = replace(observations[0], basis_pct=-0.0, annualized_basis_pct=-0.0)
    observations[1] = replace(
        observations[1],
        annualized_basis_pct=1.23456789012345,
    )
    signed = replace(base, observations=tuple(observations))
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=FakeProduct({"IM": signed}),
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    rows = csv_rows(tmp_path, outcome)
    assert rows[1][9] == "-0.0"
    assert rows[1][10] == "-0.0"
    assert rows[2][10] == "1.23456789012345"
    acquisition = artifact_json(
        tmp_path,
        outcome,
        {
            "stored_path": next(
                item["payload"]["stored_path"]
                for item in read_state(tmp_path, outcome)["artifacts"]
                if item["payload"]["label"] == "acquisition evidence"
            )
        },
    )
    assert acquisition["families"][0]["result"]["observations"][0]["basis_pct"] == -0.0
    assert (
        acquisition["families"][0]["result"]["observations"][1][
            "annualized_basis_pct"
        ]
        == 1.23456789012345
    )


def test_unexpected_product_exception_is_safely_classified(tmp_path):
    product = FakeProduct({"IM": RuntimeError("SECRET_TOKEN must not leak")})
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["status"] == "FAIL"
    result = artifact_json(tmp_path, outcome, outcome["result"])
    message = result["failures"][0]["message"]
    assert result["failures"][0]["reason"] == "source_failure"
    assert "SECRET_TOKEN" not in message
    assert "RuntimeError" in message


def test_classified_product_error_does_not_publish_source_message(tmp_path):
    product = FakeProduct({
        "IM": CFFEXEquityIndexBasisHistoryError(
            "source_failure", "credential=SECRET_TOKEN source failed"
        )
    })
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["gates"][-1]["status"] == "BLOCKED"
    run_path = tmp_path / "runs" / outcome["run_id"]
    for path in run_path.rglob("*"):
        if path.is_file():
            assert b"SECRET_TOKEN" not in path.read_bytes()
    result = artifact_json(tmp_path, outcome, outcome["result"])
    assert result["failures"][0]["reason"] == "source_failure"


def test_different_latest_dates_are_explicitly_identified(tmp_path):
    missing = {(date(2026, 11, 3).isoformat(), slot) for slot in ("M0", "M1", "Q1", "Q2")}
    product = FakeProduct(
        {
            "IF": make_result(
                "IF",
                SESSIONS,
                start=date(2026, 10, 21),
                end=date(2026, 11, 3),
                drop=missing,
            ),
            "IM": make_result(
                "IM", SESSIONS, start=date(2026, 10, 21), end=date(2026, 11, 3)
            ),
        }
    )
    outcome = run_case(
        tmp_path,
        explicit_params(("IF", "IM")),
        product=product,
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert outcome["status"] == "FAIL"
    result = artifact_json(tmp_path, outcome, outcome["result"])
    by_family = {item["futures_family"]: item for item in result["families"]}
    assert by_family["IF"]["last_observation_date"] == "2026-11-02"
    assert by_family["IM"]["last_observation_date"] == "2026-11-03"
    report = (
        tmp_path / "runs" / outcome["run_id"] / outcome["report"]["stored_path"]
    ).read_text(encoding="utf-8")
    assert "different sessions" in report
    verification = artifact_json(tmp_path, outcome, outcome["verification"])
    assert any(
        item["check"] == "report_different_sessions" and item["status"] == "pass"
        for item in verification["checks"]
    )


def test_cli_creates_a_run_without_market_access_for_invalid_input(tmp_path):
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(explicit_params(("IX",))), encoding="utf-8"
    )
    code = RUNTIME["main"](
        ["--input", str(request), "--root", str(tmp_path / "runs")]
    )
    assert code == 1
    run_dirs = [item for item in (tmp_path / "runs").iterdir() if item.is_dir()]
    assert len(run_dirs) == 1
    state = RUNTIME["RunStore"](tmp_path / "runs").read(run_dirs[0].name)
    assert state["gate_outcomes"][0]["payload"]["status"] == "FAIL"


def test_task_snapshot_is_not_modified(tmp_path):
    before = TASK_PATH.read_bytes()
    outcome = run_case(
        tmp_path,
        explicit_params(("IM",)),
        product=make_products(("IM",)),
        calendar=FakeCalendar(CALENDAR_DAYS),
    )
    assert TASK_PATH.read_bytes() == before
    manifest = json.loads(
        (tmp_path / "runs" / outcome["run_id"] / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["task"] == json.loads(before)
    assert manifest["created_at"]
    assert outcome["task_sha256"]
