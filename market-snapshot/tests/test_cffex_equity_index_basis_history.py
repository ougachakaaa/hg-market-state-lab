"""Four-family Source, product and shared semantic contract tests."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from market_snapshot.capture import im_futures_basic
from market_snapshot.cffex_equity_index_basis.semantics import (
    FAMILY_FACTS,
    CFFEXBasisError,
    assign_contract_slots,
    contract_month,
)
from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryError,
    CFFEXEquityIndexBasisHistoryRequest,
    run_cffex_equity_index_basis_history,
)
from market_snapshot.products.cffex_equity_index_basis_history.service import (
    CFFEXEquityIndexBasisHistoryService,
)
from market_snapshot.sources import tushare
from support.fake_source import (
    FakeTushareApi,
    futures_basic_frame,
    futures_daily_frame,
    im_contract,
    index_history_frame,
)


def weekdays(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    result: list[str] = []
    while len(result) < count:
        if current.weekday() < 5:
            result.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return result


def api_for(family: str, dates: list[str]) -> FakeTushareApi:
    codes = [f"{family}2601.CFX", f"{family}2602.CFX", f"{family}2603.CFX", f"{family}2606.CFX"]
    delist = ["20260130", "20260227", "20260327", "20260626"]
    basics = [
        im_contract(code, fut_code=family, list_date="20250101", delist_date=last)
        for code, last in zip(codes, delist, strict=True)
    ]
    return FakeTushareApi(
        index_frames={FAMILY_FACTS[family][0]: index_history_frame(FAMILY_FACTS[family][0], dates)},
        futures_basic=futures_basic_frame(basics),
        futures_daily={
            code: futures_daily_frame(code, dates, close=102 + i) for i, code in enumerate(codes)
        },
    )


@pytest.mark.parametrize("family", ["IF", "IH", "IC", "IM"])
def test_four_family_capture_and_public_panel(family: str) -> None:
    dates = weekdays("2025-12-01", 3)
    api = api_for(family, dates)
    request = CFFEXEquityIndexBasisHistoryRequest(family, "2025-12-01", "2025-12-03")
    result = CFFEXEquityIndexBasisHistoryService(api).run(request)
    assert len(result.observations) == 12
    assert result.underlying_code == FAMILY_FACTS[family][0]
    assert result.family_listing_date == FAMILY_FACTS[family][1]
    assert result.first_observation_date == "2025-12-01"
    assert [row.contract_slot for row in result.observations[:4]] == ["M0", "M1", "Q1", "Q2"]
    assert result.observations[0].basis_points == 2
    assert result.observations[0].annualized_basis_pct == pytest.approx(
        result.observations[0].basis_pct * 365 / result.observations[0].annualization_days
    )
    assert api.fut_basic_calls == [{"exchange": "CFFEX", "fut_type": "1", "fut_code": family}]
    assert {call["ts_code"] for call in api.fut_daily_calls} == {
        f"{family}2601.CFX",
        f"{family}2602.CFX",
        f"{family}2603.CFX",
        f"{family}2606.CFX",
    }


@pytest.mark.parametrize("family", ["IF", "IH", "IC", "IM"])
def test_listing_boundary_and_empty_effective_range(family: str) -> None:
    listing = FAMILY_FACTS[family][1]
    api = api_for(family, weekdays("2025-12-01", 2))
    with pytest.raises(CFFEXEquityIndexBasisHistoryError) as caught:
        CFFEXEquityIndexBasisHistoryService(api).run(
            CFFEXEquityIndexBasisHistoryRequest(family, "2000-01-01", "2000-01-02")
        )
    assert caught.value.reason == "no_observations"
    assert api.calls == []
    assert listing > "2000-01-02"


def test_contract_filter_and_lifecycle_intersection() -> None:
    family = "IF"
    dates = weekdays("2025-12-01", 2)
    api = api_for(family, dates)
    basics = api.futures_basic.to_dict(orient="records")
    basics.append(
        im_contract("IF.CFX", fut_code=family, list_date="20250101", delist_date="20260130")
    )
    basics.append(
        im_contract("IF2609.CFX", fut_code=family, list_date="20260801", delist_date="20260930")
    )
    api.futures_basic = futures_basic_frame(basics)
    records = im_futures_basic.capture(api, "2025-12-02", family)
    assert "IF.CFX" not in {row["ts_code"] for row in records}
    CFFEXEquityIndexBasisHistoryService(api).run(
        CFFEXEquityIndexBasisHistoryRequest(family, "2025-12-01", "2025-12-02")
    )
    assert "IF2609.CFX" not in {call["ts_code"] for call in api.fut_daily_calls}


def test_slot_and_delivery_day_rules() -> None:
    dates = ["20260130"]
    result = CFFEXEquityIndexBasisHistoryService(api_for("IF", dates)).run(
        CFFEXEquityIndexBasisHistoryRequest("IF", "2026-01-30", "2026-01-30")
    )
    assert result.observations[0].days_to_delist == 0
    assert result.observations[0].annualization_days == 1
    contracts = [
        {
            "ts_code": f"IF{month}.CFX",
            "symbol": f"IF{month}",
            "list_date": "2025-01-01",
            "delist_date": end,
        }
        for month, end in (
            ("2601", "2026-01-30"),
            ("2602", "2026-02-27"),
            ("2603", "2026-03-27"),
            ("2609", "2026-09-25"),
        )
    ]
    with pytest.raises(CFFEXBasisError, match="quarter"):
        assign_contract_slots("2026-01-30", contracts, "IF")


def test_real_tushare_contract_identity_uses_symbol_and_delist_month() -> None:
    contract = {"symbol": "IF1005", "ts_code": "IF1005.CFX", "delist_date": "2010-05-21"}
    assert contract_month(contract, "IF") == (2010, 5)
    assert contract_month({**contract, "ts_code": "IF1005.CFE"}, "IF") == (2010, 5)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"symbol": "IF1006"}, "conflicts with symbol"),
        ({"symbol": "IH1005"}, "does not express a IF delivery month"),
        ({"symbol": "IF1099", "ts_code": "IF1099.CFX"}, "invalid delivery month"),
        ({"delist_date": "2010-06-21"}, "conflicts with delist_date"),
        ({"ts_code": "IF1005"}, "conflicts with symbol"),
        ({"ts_code": "IF1005.CFX "}, "conflicts with symbol"),
        ({"symbol": None}, "symbol must be a non-empty string"),
    ],
)
def test_contract_identity_defects_fail_explicitly(change: dict[str, object], message: str) -> None:
    contract = {"symbol": "IF1005", "ts_code": "IF1005.CFX", "delist_date": "2010-05-21"}
    with pytest.raises(CFFEXBasisError, match=message):
        contract_month({**contract, **change}, "IF")


@pytest.mark.parametrize(
    "defect", ["missing", "duplicate", "invalid_close", "bad_month", "bad_symbol", "bad_lifecycle"]
)
def test_incomplete_panel_is_classified(defect: str) -> None:
    dates = weekdays("2025-12-01", 2)
    api = api_for("IH", dates)
    code = "IH2603.CFX"
    if defect == "missing":
        api.futures_daily[code] = api.futures_daily[code].iloc[:1]
    elif defect == "duplicate":
        frame = api.futures_daily[code]
        api.futures_daily[code] = pd.concat([frame, frame.iloc[[0]]])
    elif defect == "invalid_close":
        api.futures_daily[code]["close"] = pd.Series([float("nan")] * len(dates))
    elif defect == "bad_month":
        api.futures_basic.loc[api.futures_basic["ts_code"] == code, "delist_date"] = "20260427"
    elif defect == "bad_symbol":
        api.futures_basic.loc[api.futures_basic["ts_code"] == code, "symbol"] = "IH2604"
    else:
        api.futures_basic.loc[api.futures_basic["ts_code"] == code, "list_date"] = None
    with pytest.raises(CFFEXEquityIndexBasisHistoryError) as caught:
        CFFEXEquityIndexBasisHistoryService(api).run(
            CFFEXEquityIndexBasisHistoryRequest("IH", "2025-12-01", "2025-12-02")
        )
    assert caught.value.reason == "incomplete_panel"


def test_invalid_request_precedes_source_and_composition(monkeypatch: pytest.MonkeyPatch) -> None:
    api = api_for("IF", weekdays("2025-12-01", 2))
    bad = CFFEXEquityIndexBasisHistoryRequest("XX", "2025-12-01", "2025-12-02")
    with pytest.raises(CFFEXEquityIndexBasisHistoryError) as caught:
        CFFEXEquityIndexBasisHistoryService(api).run(bad)
    assert caught.value.reason == "invalid_request"
    assert api.calls == []
    monkeypatch.setattr(
        tushare, "get_tushare_token", lambda: (_ for _ in ()).throw(AssertionError())
    )
    with pytest.raises(CFFEXEquityIndexBasisHistoryError) as caught:
        run_cffex_equity_index_basis_history(bad)
    assert caught.value.reason == "invalid_request"


def test_production_composition_is_classified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        tushare, "get_tushare_token", lambda: (_ for _ in ()).throw(RuntimeError("unavailable"))
    )
    with pytest.raises(CFFEXEquityIndexBasisHistoryError) as caught:
        run_cffex_equity_index_basis_history(
            CFFEXEquityIndexBasisHistoryRequest("IF", "2025-12-01", "2025-12-02")
        )
    assert caught.value.reason == "source_failure"


def test_source_failure_and_empty_underlying_are_distinct() -> None:
    class FailingSource(FakeTushareApi):
        def index_daily(self, **_kwargs):
            raise tushare.TushareSourceError("unavailable")

    request = CFFEXEquityIndexBasisHistoryRequest("IF", "2025-12-01", "2025-12-02")
    with pytest.raises(CFFEXEquityIndexBasisHistoryError) as failed:
        CFFEXEquityIndexBasisHistoryService(FailingSource()).run(request)
    assert failed.value.reason == "source_failure"

    with pytest.raises(CFFEXEquityIndexBasisHistoryError) as empty:
        CFFEXEquityIndexBasisHistoryService(FakeTushareApi()).run(request)
    assert empty.value.reason == "no_observations"


def test_cli_to_four_public_products_and_retained_evidence(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise CLI -> production composition -> fake Source -> Study -> publication."""
    from market_research.studies.cffex_basis_forward_return_association import cli
    from market_research.ui import configuration

    dates = weekdays("2025-12-01", 35)
    all_basics = []
    all_daily = {}
    index_frames = {}
    for family in FAMILY_FACTS:
        family_api = api_for(family, dates)
        all_basics.extend(family_api.futures_basic.to_dict(orient="records"))
        all_daily.update(family_api.futures_daily)
        index_frames.update(family_api.index_frames)
    api = FakeTushareApi(
        index_frames=index_frames,
        futures_basic=futures_basic_frame(all_basics),
        futures_daily=all_daily,
    )
    monkeypatch.setattr(tushare, "get_tushare_token", lambda: "fake-token")
    monkeypatch.setattr(tushare, "create_tushare_api", lambda _token: api)
    config_path = tmp_path / "market-research" / "research.toml"
    config_path.parent.mkdir()
    output_root = tmp_path / "output"
    config_path.write_text(f"[output]\nroot = '{output_root}'\n")
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", config_path)
    start = pd.Timestamp(dates[0]).strftime("%Y-%m-%d")
    end = pd.Timestamp(dates[-1]).strftime("%Y-%m-%d")
    assert cli.main(["--start", start, "--end", end]) == 0
    run_dir = output_root / "cffex-basis-forward-return-association" / f"{start}__{end}"
    assert (run_dir / "result.json").exists()
    assert (run_dir / "report.md").exists()
    assert len(api.index_calls) == 4
    assert [call["fut_code"] for call in api.fut_basic_calls] == ["IF", "IH", "IC", "IM"]
