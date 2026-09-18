from pathlib import Path

import pytest

import _common


def test_to_tushare_date_converts_iso_to_source_form() -> None:
    assert _common.to_tushare_date("2026-09-17") == "20260917"


def test_to_iso_date_converts_source_form_to_iso() -> None:
    assert _common.to_iso_date("20260917") == "2026-09-17"


def test_date_conversion_round_trip() -> None:
    assert _common.to_iso_date(_common.to_tushare_date("2026-01-05")) == "2026-01-05"


@pytest.mark.parametrize(
    "trade_date",
    ["20260917", "2026/09/17", "2026-9-17", "2026-09-17T00:00:00", "", "not-a-date"],
)
def test_to_tushare_date_rejects_non_iso_input(trade_date: str) -> None:
    with pytest.raises(_common.CollectionError):
        _common.to_tushare_date(trade_date)


def test_get_tushare_token_returns_configured_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_common.TOKEN_ENV_VAR, "local-token")

    assert _common.get_tushare_token() == "local-token"


@pytest.mark.parametrize("value", ["", "   "])
def test_get_tushare_token_fails_without_token(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv(_common.TOKEN_ENV_VAR, value)

    with pytest.raises(_common.CollectionError, match=_common.TOKEN_ENV_VAR):
        _common.get_tushare_token()


def test_get_tushare_token_fails_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_common.TOKEN_ENV_VAR, raising=False)

    with pytest.raises(_common.CollectionError, match=_common.TOKEN_ENV_VAR):
        _common.get_tushare_token()


def test_to_raw_records_normalizes_numpy_scalars_and_trade_date() -> None:
    import numpy as np
    import pandas as pd

    frame = pd.DataFrame(
        [
            {
                "ts_code": "000001.SZ",
                "trade_date": "20260917",
                "close": np.float64(10.5),
                "vol": np.int64(100),
            }
        ]
    )

    records = _common.to_raw_records(frame)

    assert records == [
        {"ts_code": "000001.SZ", "trade_date": "2026-09-17", "close": 10.5, "vol": 100}
    ]
    assert isinstance(records[0]["close"], float)
    assert isinstance(records[0]["vol"], int)


def test_to_raw_records_keeps_records_with_missing_source_values() -> None:
    import numpy as np
    import pandas as pd

    frame = pd.DataFrame([{"ts_code": "000001.SZ", "trade_date": "20260917", "pct_chg": np.nan}])

    records = _common.to_raw_records(frame)

    assert records == [{"ts_code": "000001.SZ", "trade_date": "2026-09-17", "pct_chg": None}]


def test_write_raw_dataset_writes_json_array(test_workdir: Path) -> None:
    import json

    dataset_dir = test_workdir / "2026-09-17"
    records = [{"ts_code": "000016.SH", "trade_date": "2026-09-17"}]

    path = _common.write_raw_dataset(records, dataset_dir, "index_daily")

    assert path.name == "index_daily.json"
    assert json.loads(path.read_text(encoding="utf-8")) == records


@pytest.mark.parametrize("value", [None, "", "  ", float("nan")])
def test_to_iso_date_or_none_keeps_missing_source_dates(value: object) -> None:
    assert _common.to_iso_date_or_none(value) is None


def test_to_iso_date_or_none_converts_source_form() -> None:
    assert _common.to_iso_date_or_none("20260917") == "2026-09-17"


def test_to_iso_date_or_none_keeps_already_normalized_dates() -> None:
    assert _common.to_iso_date_or_none("2026-06-22") == "2026-06-22"


@pytest.mark.parametrize("value", ["2026-6-22", "20261301", "22/06/2026"])
def test_to_iso_date_or_none_rejects_other_forms(value: str) -> None:
    with pytest.raises(_common.CollectionError):
        _common.to_iso_date_or_none(value)


def test_to_raw_records_normalizes_source_date_facts() -> None:
    import pandas as pd

    frame = pd.DataFrame(
        [{"ts_code": "MO2609-C-7000.CFE", "list_date": "20260622", "delist_date": "20260925"}]
    )

    records = _common.to_raw_records(frame)

    assert records == [
        {
            "ts_code": "MO2609-C-7000.CFE",
            "list_date": "2026-06-22",
            "delist_date": "2026-09-25",
        }
    ]


def test_to_raw_records_is_stable_for_already_normalized_dates() -> None:
    import pandas as pd

    frame = pd.DataFrame([{"ts_code": "MO2609-C-7000.CFE", "list_date": "2026-06-22"}])

    records = _common.to_raw_records(frame)

    assert records[0]["list_date"] == "2026-06-22"


def test_to_raw_records_rejects_malformed_source_date_facts() -> None:
    import pandas as pd

    frame = pd.DataFrame([{"ts_code": "MO2609-C-7000.CFE", "list_date": "2026-6-22"}])

    with pytest.raises(_common.CollectionError):
        _common.to_raw_records(frame)


def test_in_date_range_uses_inclusive_iso_bounds() -> None:
    record = {"trade_date": "2026-09-17"}

    assert _common.in_date_range(record, "trade_date", "2026-09-17", "2026-09-17")
    assert not _common.in_date_range(record, "trade_date", "2026-01-01", "2026-09-16")
    assert not _common.in_date_range({"trade_date": None}, "trade_date", "2026-01-01", "2026-12-31")


def test_fetch_source_frames_keeps_the_requested_code() -> None:
    import pandas as pd

    def query(*, ts_code: str, start_date: str) -> pd.DataFrame:
        return pd.DataFrame([{"ts_code": ts_code, "start_date": start_date}])

    frames = list(_common.fetch_source_frames(query, ["B", "A"], start_date="20260101"))

    assert [code for code, _ in frames] == ["A", "B"]
    assert [frame.iloc[0]["ts_code"] for _, frame in frames] == ["A", "B"]
