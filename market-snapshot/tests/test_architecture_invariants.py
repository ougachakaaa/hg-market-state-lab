"""Architecture invariants of one ``csi1000-5d-analysis`` request.

Authority: ``market-snapshot/ARCHITECTURE.md`` section 2 (Source Capture owns the
concrete endpoint call, the query parameters and the Source-domain scope, while
the Data Service owns orchestration) and ``products/csi1000_5d_analysis/ARCHITECTURE.md`` section 4
(the Data Service stage order).

These tests lock the reconciled runtime contract of one request:

    CSI1000 history -> MO basic -> MO daily -> IM basic -> IM daily -> Preparation

* every basic Capture reads the Source exactly once, and the daily Capture of the
  same product reuses the Source facts its basic Capture already collected;
* the Source is called in the Data Service stage order, and a failing Capture
  stops the chain before any later Source call;
* the Data Service names no Source endpoint and no Capture query parameter;
* the CLI knows no Capture list and no execution order.

They are deliberately direct: no event framework, no architecture-test harness.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from daily_market_snapshot import artifacts, cli
from daily_market_snapshot.capture import (
    im_futures_basic,
    im_futures_daily,
    mo_option_basic,
    mo_option_daily,
)
from daily_market_snapshot.products.csi1000_5d_analysis import capture as csi1000_index_history
from daily_market_snapshot.products.csi1000_5d_analysis import service as csi1000_5d_analysis
from daily_market_snapshot.services import DataServiceError
from support.fake_source import (
    CSI1000_IM_CONTRACTS,
    CSI1000_TARGET_DATE,
    FakeTushareApi,
    csi1000_5d_analysis_api,
)

TARGET_DATE = CSI1000_TARGET_DATE
SERVICE_ID = "csi1000-5d-analysis"

# The endpoints of the five Captures, in the authority stage order of
# ``products/csi1000_5d_analysis/ARCHITECTURE.md`` section 4.
CAPTURES = (
    (csi1000_index_history, "index_daily"),
    (mo_option_basic, "opt_basic"),
    (mo_option_daily, "opt_daily"),
    (im_futures_basic, "fut_basic"),
    (im_futures_daily, "fut_daily"),
)
# The stage names the Data Service reports a failure under.
CAPTURE_STAGE_NAMES = (
    "csi1000_history",
    "mo_option_basic",
    "mo_option_daily",
    "im_futures_basic",
    "im_futures_daily",
)
# Endpoints the scenario reads once (the fake Source holds one IM contract, so
# the IM daily Capture reads one contract over one range).
EXPECTED_SOURCE_CALLS = ("index_daily", "opt_basic", "opt_daily", "fut_basic", "fut_daily")


def run_request(api: FakeTushareApi) -> Path:
    """Run one complete Data Service request against the fake Source."""
    return csi1000_5d_analysis.run_csi1000_5d_analysis(api, TARGET_DATE)


def source_calls(api: FakeTushareApi) -> list[str]:
    """The Source endpoints ``api`` was asked for, in request order."""
    return [endpoint for endpoint, _ in api.calls]


def module_source(module: ModuleType) -> str:
    """The source text of a module."""
    return Path(str(module.__file__)).read_text(encoding="utf-8")


def raw_records(raw_artifact: str) -> list[artifacts.RawRecord]:
    """Read one Raw Artifact the request wrote."""
    payload: Any = artifacts.read_raw_artifact(
        artifacts.csi1000_raw_dir(TARGET_DATE), raw_artifact
    )
    assert isinstance(payload, list)
    return payload


def codes(raw_artifact: str) -> set[str]:
    return {str(record["ts_code"]) for record in raw_records(raw_artifact)}


# ---------------------------------------------------------------------------
# Source ownership / request count
# ---------------------------------------------------------------------------


def test_source_call_order_matches_the_data_service_stage_order() -> None:
    """CSI1000 history -> MO basic -> MO daily -> IM basic -> IM daily."""
    api = csi1000_5d_analysis_api()

    run_request(api)

    assert source_calls(api) == list(EXPECTED_SOURCE_CALLS)


def test_each_basic_capture_reads_the_source_exactly_once() -> None:
    """One request reads ``opt_basic`` and ``fut_basic`` exactly once each."""
    api = csi1000_5d_analysis_api()

    run_request(api)

    calls = source_calls(api)
    assert calls.count("opt_basic") == 1
    assert calls.count("fut_basic") == 1
    # The other endpoints are not read twice either.
    assert calls.count("index_daily") == 1
    assert calls.count("opt_daily") == 1
    assert calls.count("fut_daily") == len(CSI1000_IM_CONTRACTS)


def test_a_failing_capture_stops_the_request_before_any_later_source_call() -> None:
    """A failed Capture is never skipped: no later Source call, no output."""
    api = csi1000_5d_analysis_api()
    # The Source holds no MO contract, so the second stage cannot succeed.
    api.option_basic = api.option_basic.iloc[0:0]

    with pytest.raises(DataServiceError, match="stage=mo_option_basic"):
        run_request(api)

    assert source_calls(api) == ["index_daily", "opt_basic"]
    assert not (
        artifacts.output_dir(artifacts.OUTPUT_DIR, SERVICE_ID, TARGET_DATE)
        / artifacts.ANALYSIS_READY_FILENAME
    ).exists()


# ---------------------------------------------------------------------------
# Fact reuse inside one request
# ---------------------------------------------------------------------------


def second_read_fails(api: FakeTushareApi, endpoint: str) -> None:
    """Make a second call of ``endpoint`` inside one request fail the test."""
    once = getattr(api, endpoint)
    calls = getattr(api, f"{endpoint}_calls")

    def read_once(**kwargs: Any) -> Any:
        if calls:
            raise AssertionError(f"the daily Capture must reuse the {endpoint} facts")
        return once(**kwargs)

    setattr(api, endpoint, read_once)


def test_mo_daily_scope_reuses_the_captured_basic_facts() -> None:
    """MO daily resolves its universe from the MO basic facts of this request."""
    api = csi1000_5d_analysis_api()
    second_read_fails(api, "opt_basic")

    run_request(api)

    assert codes("mo_option_daily") == codes("mo_option_basic")


def test_im_daily_window_reuses_the_captured_basic_facts() -> None:
    """IM daily resolves its window from the IM basic facts of this request."""
    api = csi1000_5d_analysis_api()
    second_read_fails(api, "fut_basic")

    run_request(api)

    assert codes("im_futures_daily") <= codes("im_futures_basic")
    assert codes("im_futures_daily")


# ---------------------------------------------------------------------------
# Layer boundaries
# ---------------------------------------------------------------------------


def test_each_capture_owns_its_source_endpoint() -> None:
    """Endpoint, query parameters and scope live in the Capture module."""
    for module, endpoint in CAPTURES:
        source = module_source(module)
        assert endpoint in source
        assert "def capture(" in source


def test_the_data_service_names_no_source_endpoint_or_query_parameter() -> None:
    """The Data Service asks for Captures, never for a Source endpoint."""
    source = module_source(csi1000_5d_analysis)

    for _, endpoint in CAPTURES:
        assert endpoint not in source
    assert "getattr" not in source
    for parameter in ("exchange=", "fut_type", "fut_code", "ts_code"):
        assert parameter not in source


def test_the_cli_knows_no_capture_list_or_execution_order() -> None:
    """The CLI resolves a Data Service; the Capture chain is not its business."""
    source = module_source(cli)

    for module, endpoint in CAPTURES:
        assert module.__name__.rsplit(".", 1)[-1] not in source
        assert endpoint not in source
    for stage_name in CAPTURE_STAGE_NAMES:
        assert stage_name not in source
