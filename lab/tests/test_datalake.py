"""CLI parsing, public service delegation, error mapping and file delivery."""

import json
import logging
from dataclasses import asdict, fields
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from data_lake import CoverageResult, EnsureResult, InvalidRequestError, OperationError, UnitFailure
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
)
from data_lake.datasets.tushare_trade_calendar._models import CalendarWindow, TradeCalendarScope
from lab import cli, datalake

DAY = date(2024, 1, 1)
INCOMPLETE = CoverageResult(2, 1, 1, 0, 0, False)


class Service:
    def __init__(self) -> None:
        self.requests: list[TradeCalendarRange] = []
        self.result = EnsureResult(
            2, 0, 2, 1, 1, 1, False, (UnitFailure(("SSE", DAY), "Missing Source date"),)
        )
        self.error: Exception | None = None

    def accept(self, request: TradeCalendarRange) -> None:
        self.requests.append(request)
        if self.error is not None:
            raise self.error

    def coverage(self, request: TradeCalendarRange) -> CoverageResult:
        self.accept(request)
        return INCOMPLETE

    def ensure(self, request: TradeCalendarRange) -> EnsureResult:
        self.accept(request)
        return self.result

    def export(self, request: TradeCalendarRange) -> TradeCalendarExport:
        self.accept(request)
        return TradeCalendarExport(
            "tushare_trade_calendar",
            "calendar",
            1,
            TradeCalendarScope(request.exchange),
            CalendarWindow(request.start_date, request.end_date),
            INCOMPLETE,
            (TradeCalendarRecord("SSE", DAY, 0, None),),
        )


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Service:
    fake = Service()
    monkeypatch.setattr(datalake, "create_service", lambda: fake)
    return fake


def args(operation: str = "coverage") -> list[str]:
    return [
        "datalake",
        operation,
        "tushare_trade_calendar",
        "--exchange",
        "SSE",
        "--start-date",
        "2024-01-01",
        "--end-date",
        "2024-01-02",
    ]


def test_list_never_creates_service(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def forbidden() -> None:
        pytest.fail("list must not compose a service")

    monkeypatch.setattr(datalake, "create_service", forbidden)
    assert cli.main(["datalake", "list"]) == 0
    assert capsys.readouterr().out.strip().splitlines() == list(datalake.DATASETS)


def test_log_file_and_handler_restoration(service: Service, tmp_path: Path) -> None:
    logger = logging.getLogger("data_lake")
    before = logger.handlers[:], logger.level, logger.propagate
    logfile = tmp_path / "diagnostic.log"
    with datalake._logging(
        cli.build_parser().parse_args(
            ["datalake", "--log-level", "DEBUG", "--log-file", str(logfile), "list"]
        )
    ):
        logging.getLogger("data_lake.test").debug("safe diagnostic 中文")
    assert (logger.handlers, logger.level, logger.propagate) == before
    assert "safe diagnostic 中文" in logfile.read_text(encoding="utf-8")
    # A closed FileHandler leaves no Windows file lock after the invocation.
    logfile.unlink()


def test_log_delivery_failure_prevents_source_operation(service: Service, tmp_path: Path) -> None:
    logfile = tmp_path / "missing-parent" / "run.log"
    assert cli.main(["datalake", "--log-file", str(logfile), *args("ensure")[1:]]) == 1
    assert service.requests == []


def test_coverage_constructs_semantic_range_and_accepts_incomplete(
    service: Service,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(args()) == 0
    assert service.requests == [TradeCalendarRange("SSE", DAY, date(2024, 1, 2))]
    output = capsys.readouterr().out
    for field in fields(INCOMPLETE):
        assert field.name in output
    assert "False" in output


def test_ensure_exit_codes_and_failures(
    service: Service, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(args("ensure")) == 1
    output = capsys.readouterr().out
    assert "Missing Source date" in output and "incomplete" in output
    assert "SSE" in output and "2024" in output
    service.result = EnsureResult(2, 2, 0, 0, 0, 0, True, ())
    assert cli.main(args("ensure")) == 0


def test_export_delivers_wire_types_without_terminal_records(
    service: Service,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "交易日历.json"
    assert cli.main(args("export") + ["--output", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload == {
        "dataset": "tushare_trade_calendar",
        "view": "calendar",
        "export_schema_version": 1,
        "scope": {"exchange": "SSE"},
        "window": {"start_date": "2024-01-01", "end_date": "2024-01-02"},
        "coverage": {
            "requested_units": 2,
            "successful_units": 1,
            "missing_units": 1,
            "pending_units": 0,
            "failed_units": 0,
            "complete": False,
        },
        "records": [
            {"exchange": "SSE", "cal_date": "2024-01-01", "is_open": 0, "pretrade_date": None}
        ],
    }
    assert type(payload["records"][0]["is_open"]) is int
    assert len(service.requests) == 1
    terminal = capsys.readouterr().out
    assert "1 records" in terminal and str(output) in terminal and "cal_date" not in terminal


@pytest.mark.parametrize("operation", ["coverage", "ensure", "export"])
@pytest.mark.parametrize(
    "error,code",
    [
        (InvalidRequestError("invalid range"), 2),
        (OperationError("cache unavailable"), 1),
    ],
)
def test_public_error_mapping(
    service: Service,
    operation: str,
    error: Exception,
    code: int,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    service.error = error
    arguments = args(operation)
    if operation == "export":
        arguments += ["--output", str(tmp_path / "calendar.json")]
    assert cli.main(arguments) == code
    assert str(error) in capsys.readouterr().err
    assert not (tmp_path / "calendar.json").exists()


def test_semantic_validation_before_service_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden() -> None:
        pytest.fail("invalid range must fail before service composition")

    monkeypatch.setattr(datalake, "create_service", forbidden)
    assert cli.main(args()[:-1] + ["2023-12-31"]) == 2


@pytest.mark.parametrize(
    "value",
    [
        "20240101",
        "2024-1-01",
        "2024-02-30",
        "2024-01-01T00:00:00",
        " 2024-01-01",
        "２０２４-01-01",
        "2024-W01-1",
    ],
)
def test_strict_dates_fail_parsing(service: Service, value: str) -> None:
    arguments = args()
    arguments[arguments.index("--start-date") + 1] = value
    with pytest.raises(SystemExit) as exc:
        cli.main(arguments)
    assert exc.value.code == 2 and not service.requests


@pytest.mark.parametrize(
    "arguments",
    [
        ["datalake", "coverage", "unknown"],
        args("export"),
        args() + ["--db", "database"],
        args() + ["--token", "secret"],
        ["datalake", "coverage", "tushare_trade_calendar"],
    ],
)
def test_invalid_cli_arguments(service: Service, arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(arguments)
    assert exc.value.code == 2 and not service.requests


def test_delivery_failure_is_nonzero(
    service: Service, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(args("export") + ["--output", str(tmp_path)]) == 1
    output = capsys.readouterr()
    assert "could not be delivered" in output.err and "Exported" not in output.out


def test_datalake_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="0"):
        cli.main(["datalake", "--help"])
    assert "{list,coverage,ensure,export}" in capsys.readouterr().out


def test_incremental_delivery_preserves_wire_and_replaces_existing_output(
    service: Service,
    tmp_path: Path,
) -> None:
    view = service.export(TradeCalendarRange("SSE", DAY, DAY))
    output = tmp_path / "output.json"
    output.write_text("previous", encoding="utf-8")
    datalake._deliver(view, output)
    expected = json.dumps(asdict(view), default=datalake._json_date, ensure_ascii=False, indent=2)
    assert output.read_text(encoding="utf-8") == expected + "\n"
    assert list(tmp_path.iterdir()) == [output]


@pytest.mark.parametrize("stage", ["encoding", "flush", "replace"])
def test_delivery_failure_preserves_output_and_removes_temporary_file(
    service: Service,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    view = service.export(TradeCalendarRange("SSE", DAY, DAY))
    output = tmp_path / "output.json"
    output.write_bytes(b"previous")
    if stage == "encoding":
        original = datalake.json.dump

        def fail(*args: Any, **kwargs: Any) -> None:
            original(*args, **kwargs)
            raise TypeError("injected encoding error")

        monkeypatch.setattr(datalake.json, "dump", fail)
    else:

        def fail(*args: Any, **kwargs: Any) -> None:
            raise OSError("injected delivery error")

        monkeypatch.setattr(datalake.os, "fsync" if stage == "flush" else "replace", fail)
    with pytest.raises((OSError, TypeError)):
        datalake._deliver(view, output)
    assert output.read_bytes() == b"previous"
    assert list(tmp_path.iterdir()) == [output]
