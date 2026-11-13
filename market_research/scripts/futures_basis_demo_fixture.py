"""Generate the public synthetic Futures Basis demo fixture (no market I/O).

The fixture is deterministic producer output: a fixed synthetic public-fact universe
is fed through the unchanged preparation, observation and report composition path with
the canonical online ReportRequest. Only the reader's ``sources`` label is replaced
with an explicit Synthetic Demo provenance statement, and ``runtime`` is omitted
because the fixture is not a sealed computation evidence package.

Run from the repository root::

    poetry run python market_research/scripts/futures_basis_demo_fixture.py
    poetry run python market_research/scripts/futures_basis_demo_fixture.py --check
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from dataclasses import fields
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from data_lake import CoverageResult, EnsureResult
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRow
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord
from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest,
    compose_report,
    construct_observations,
    prepare_inputs,
    standard_report_request,
)
from market_research.descriptive.cases.futures_basis.evidence import scientific_payload

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "ui_web/src/demo/futures_basis/report.v1.json"

FIXTURE_PROFILE = "futures_basis_demo_fixture_v1"
REPORT_PROFILE = "futures_basis_report_evidence_v1"
GENERATOR = "market_research/scripts/futures_basis_demo_fixture.py"
WINDOW = (date(2024, 9, 2), date(2024, 10, 31))

DISCLOSURE = {
    "label": "Synthetic Demo",
    "data_source": (
        "Deterministic synthetic public-fact fixtures generated in this repository; "
        "no Tushare or other market data is included."
    ),
    "notice": (
        "本页为 Synthetic Demo：数据由确定性合成事实经现有 Research Producer 生成，"
        "不是实时行情、真实交易表现或投资建议。"
    ),
}
SYNTHETIC_SOURCES = (
    "Synthetic Demo 合成事实 · CFFEX 期货 / SSE CSI 1000（000852.SH）· 同交易日 Close · 非真实行情"
)


def proof(units: int) -> CoverageResult:
    return CoverageResult(units, units, 0, 0, 0, True)


def third_friday(year: int, month: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(4 - first.weekday()) % 7 + 14)


def maturity(year: int, month: int) -> int:
    return year * 12 + month - 1


def from_maturity(value: int) -> tuple[int, int]:
    year, month = divmod(value, 12)
    return year, month + 1


def first_quarter_after(value: int) -> int:
    return value + (3 - ((value + 1) % 3))


def active_months(day: date) -> tuple[int, int, int, int]:
    """Return the four delivery months required by the published Slot resolution."""
    front = maturity(day.year, day.month)
    if third_friday(day.year, day.month) < day:
        front = maturity(*from_maturity(front + 1))
    near = front + 1
    quarter = first_quarter_after(near)
    return front, near, quarter, quarter + 3


def contract_code(value: int) -> str:
    year, month = from_maturity(value)
    return f"IM{year % 100:02d}{month:02d}.CFX"


def delivery_month(value: int) -> str:
    year, month = from_maturity(value)
    return f"{year:04d}{month:02d}"


def delist_date(value: int) -> date:
    year, month = from_maturity(value)
    return third_friday(year, month)


def basis_ratio(day_index: int, month_value: int, front_value: int) -> float:
    """Deterministic discount/premium cycle with a mild term slope; no randomness."""
    phase = day_index % 26
    if phase < 8:
        base = -0.012 - 0.0008 * phase
    elif phase < 13:
        base = 0.003 + 0.0004 * phase
    elif phase < 21:
        base = -0.008 - 0.0004 * phase
    else:
        base = 0.002
    return base - 0.0015 * (month_value - front_value)


def index_close(day_index: int) -> float:
    return round(100.0 + 3.0 * math.sin(2 * math.pi * day_index / 23.0) + 0.05 * day_index, 6)


def futures_row(day: date, month_value: int, close: float) -> FuturesDailyRow:
    values: dict[str, Any] = {field.name: 1.0 for field in fields(FuturesDailyRow)}
    values.update(
        contract_code=contract_code(month_value),
        product_code="IM",
        symbol=f"IM{delivery_month(month_value)[2:]}",
        name="synthetic demo",
        exchange="CFFEX",
        underlying_index_code="000852.SH",
        trade_unit="lot",
        quote_unit="points",
        delivery_month=delivery_month(month_value),
        list_date=date(2023, 1, 1),
        delist_date=delist_date(month_value),
        last_delivery_date=delist_date(month_value) + timedelta(days=3),
        trade_date=day,
        close=close,
    )
    return FuturesDailyRow(**values)


class DemoServices:
    """Public DataLake service doubles exposing only exports of deterministic facts."""

    request: FuturesBasisRequest

    def __init__(self, request: FuturesBasisRequest) -> None:
        self.request = request
        days = tuple(
            request.start_date + timedelta(days=offset)
            for offset in range((request.end_date - request.start_date).days + 1)
        )
        self.calendars = {
            exchange: TradeCalendarExport(
                "tushare_trade_calendar",
                "calendar",
                1,
                cast(Any, SimpleNamespace(exchange=exchange)),
                cast(
                    Any,
                    SimpleNamespace(start_date=request.start_date, end_date=request.end_date),
                ),
                proof(len(days)),
                tuple(
                    TradeCalendarRecord(exchange, day, int(day.weekday() < 5), None) for day in days
                ),
            )
            for exchange in ("CFFEX", "SSE")
        }
        sessions = tuple(day for day in days if day.weekday() < 5)
        futures_rows: list[FuturesDailyRow] = []
        index_rows: list[IndexDailyRow] = []
        for day_index, day in enumerate(sessions):
            front, near, quarter, quarter3 = active_months(day)
            spot = index_close(day_index)
            index_rows.append(
                IndexDailyRow(
                    "000852.SH",
                    "000852",
                    "synthetic demo",
                    "SSE",
                    None,
                    None,
                    day,
                    spot,
                    spot,
                    spot,
                    spot,
                    spot,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                )
            )
            for month_value in (front, near, quarter, quarter3):
                ratio = basis_ratio(day_index, month_value, front)
                futures_rows.append(futures_row(day, month_value, round(spot * (1 + ratio), 6)))
        window = SimpleNamespace(start_date=request.start_date, end_date=request.end_date)
        self.futures = FuturesDailyExport(
            "tushare_equity_index_futures",
            "futures_daily",
            2,
            SimpleNamespace(product_codes=("IM",)),
            window,
            proof(len(sessions)),
            tuple(futures_rows),
        )
        self.index = IndexDailyExport(
            "tushare_index_daily",
            "index_daily",
            1,
            SimpleNamespace(index_codes=("000852.SH",)),
            window,
            proof(len(sessions)),
            tuple(index_rows),
        )

    def export(self, request: Any) -> Any:
        name = getattr(
            request, "exchange", "futures" if hasattr(request, "product_codes") else "index"
        )
        return getattr(self, name) if name not in self.calendars else self.calendars[name]

    def ensure(self, request: Any) -> EnsureResult:  # pragma: no cover - complete coverage
        raise AssertionError("demo facts are complete; ensure must not be called")

    def prepare(self) -> Any:
        return prepare_inputs(
            self.request, calendar_service=self, futures_service=self, index_service=self
        )


def producer_reader() -> dict[str, Any]:
    """Compose the unchanged producer reader projection for the demo window."""
    services = DemoServices(FuturesBasisRequest("IM", *WINDOW))
    source = construct_observations(services.request, services.prepare())
    report = compose_report(source, standard_report_request(services.request))
    _science, _views, _associations, reader = scientific_payload(report)
    return cast(dict[str, Any], reader)


def build_fixture() -> dict[str, Any]:
    reader = producer_reader()
    # The only replaced producer field: a synthetic provenance label instead of the
    # production DataLake source description. Every scientific field stays unchanged.
    reader["sources"] = SYNTHETIC_SOURCES
    return {
        "fixture_profile": FIXTURE_PROFILE,
        "classification": "synthetic",
        "generated_by": GENERATOR,
        "report_profile": REPORT_PROFILE,
        "disclosure": dict(DISCLOSURE),
        "report": reader,
    }


def fixture_bytes() -> bytes:
    return (json.dumps(build_fixture(), ensure_ascii=False, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def assert_fixture_matches(current: dict[str, Any], expected: dict[str, Any]) -> None:
    """V1-only libm tolerance; all fields outside annualized history remain exact."""
    normalized = copy.deepcopy(current)
    actual_layers = normalized["report"]["views"]["history"]["annualized_basis_ratio"]["layers"]
    expected_layers = expected["report"]["views"]["history"]["annualized_basis_ratio"]["layers"]
    assert len(actual_layers) == len(expected_layers), "History layer count drift"
    for actual, target in zip(actual_layers, expected_layers, strict=True):
        marks, targets = actual["layer"]["data"], target["layer"]["data"]
        assert len(marks) == len(targets), "History point count drift"
        for mark, point in zip(marks, targets, strict=True):
            a, b = mark["y"], point["y"]
            if type(a) is float and type(b) is float and math.isfinite(a) and math.isfinite(b):
                assert (
                    a == 0.0
                    and a.hex() == b.hex()
                    or a != 0.0
                    and b != 0.0
                    and abs(a - b) <= 2 * min(math.ulp(a), math.ulp(b))
                ), "Annualized history drift"
                for item in mark["details"]:
                    if item["label"] == "结果":
                        assert item["value"] == repr(a), "History detail disagrees with point"
                        item["value"] = repr(b)
                mark["y"] = b
    assert json.dumps(normalized, ensure_ascii=False, separators=(",", ":")) == json.dumps(
        expected, ensure_ascii=False, separators=(",", ":")
    ), "Fixture structure or scientific content drift"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="verify the committed fixture")
    args = parser.parse_args()
    output = args.output.resolve()
    expected = fixture_bytes()
    if args.check:
        if not output.exists():
            raise SystemExit(f"Missing demo fixture: {output}")
        current = output.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
        try:
            parsed = json.loads(current)
            canonical = (
                json.dumps(parsed, ensure_ascii=False, separators=(",", ":")) + "\n"
            ).encode("utf-8")
            assert current == canonical, "Noncanonical fixture serialization"
            assert_fixture_matches(parsed, json.loads(expected))
        except (AssertionError, KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"Demo fixture is stale: {output}: {exc}") from exc
        print(f"Demo fixture is current: {output}")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(expected)
    print(f"Demo fixture written: {output} ({len(expected)} bytes)")


if __name__ == "__main__":
    main()
