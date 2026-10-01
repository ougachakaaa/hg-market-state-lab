"""MO historical public results, request reduction and recoverable acquisition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from market_snapshot.products.mo_option_chain import service
from market_snapshot.products.mo_option_chain.session import ChainSession
from market_snapshot.sources.session_execution import RequestBudget, SessionExecution
from test_mo_option_chain_real_provider import TARGET, fake_source

KINDS = (service.PriceType.HIGH, service.PriceType.LOW)


def execution() -> SessionExecution:
    clock = [1.0]

    def sleep(seconds: float) -> None:
        clock[0] += seconds

    return SessionExecution(RequestBudget(clock=lambda: clock[0], sleep=sleep))


def test_pair_equals_legacy_and_requests_are_reduced(tmp_path: Path) -> None:
    api = fake_source()
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        pair = session.read_date(TARGET, KINDS)
        assert session.metrics()["attempts"] == 5
        assert [name for name, _ in api.calls] == [
            "opt_basic",
            "fut_basic",
            "index_daily",
            "opt_daily",
            "fut_daily",
        ]
        assert api.fut_daily_calls[0]["exchange"] == "CFFEX"
        assert all(result.error is None for result in pair.values())
        assert session.provenance()["fetched_dates"] == [TARGET]
        directory = session.directory
    for kind in KINDS:
        expected = service.read_chain_with_api(
            fake_source(),
            service.ChainQuery(TARGET, service.OptionProduct.MO, kind),
            tmp_path / "legacy",
        )
        assert pair[kind] == expected
    assert (directory / TARGET / "complete.json").exists()


def test_resume_reuses_all_facts_and_corrupt_day_refetches(tmp_path: Path) -> None:
    api = fake_source()
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as first:
        expected = first.read_date(TARGET, KINDS)
        directory = first.directory
    calls = len(api.calls)
    with ChainSession(
        [TARGET], resume=True, api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as resumed:
        assert resumed.read_date(TARGET, KINDS) == expected
        assert resumed.metrics()["attempts"] == 0
        assert resumed.provenance()["reused_dates"] == [TARGET]
    assert len(api.calls) == calls
    (directory / TARGET / "mo_option_daily.json").write_text("[]")
    with ChainSession(
        [TARGET], resume=True, api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as repaired:
        assert repaired.read_date(TARGET, KINDS) == expected
        assert repaired.metrics()["attempts"] == 3
        assert repaired.provenance()["fetched_dates"] == [TARGET]
    assert len(api.opt_basic_calls) == len(api.fut_basic_calls) == 1


def test_incomplete_date_refetched_and_fresh_run_never_reuses(tmp_path: Path) -> None:
    api = fake_source()
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as first:
        first.read_date(TARGET, KINDS)
        directory = first.directory
    (directory / TARGET / "complete.json").unlink()
    for resume in (True, False):
        with ChainSession(
            [TARGET],
            resume=resume,
            api_factory=lambda: api,
            raw_root=tmp_path,
            execution=execution(),
        ) as session:
            assert session.read_date(TARGET, KINDS)[KINDS[0]].error is None
            assert session.provenance()["reused_dates"] == []
    assert len(api.opt_basic_calls) == 2
    assert len(api.opt_daily_calls) == 3


@pytest.mark.parametrize("damage", ["version", "basic", "missing"])
def test_bad_checkpoint_fails_before_provider(tmp_path: Path, damage: str) -> None:
    api = fake_source()
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        directory = session.directory
    if damage == "version":
        path = directory / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["identity"]["version"] = 999
        path.write_text(json.dumps(manifest))
    elif damage == "basic":
        (directory / "mo_option_basic.json").write_text("[]")
    else:
        (directory / "manifest.json").unlink()
    calls = len(api.calls)
    with pytest.raises(service.OptionChainUnavailableError, match="checkpoint cannot resume"):
        with ChainSession(
            [TARGET], resume=True, api_factory=lambda: api, raw_root=tmp_path, execution=execution()
        ):
            pass
    assert len(api.calls) == calls


def test_duplicate_session_locked_and_released_on_exit(tmp_path: Path) -> None:
    api = fake_source()
    kwargs: dict[str, Any] = dict(api_factory=lambda: api, raw_root=tmp_path, execution=execution())
    with ChainSession([TARGET], **kwargs):
        with pytest.raises(service.OptionChainUnavailableError, match="already running"):
            with ChainSession([TARGET], **kwargs):
                pass
    with ChainSession([TARGET], resume=True, **kwargs):
        pass


def test_missing_option_row_fails_without_complete_manifest(tmp_path: Path) -> None:
    api = fake_source()
    api.option_daily = api.option_daily.iloc[:1]
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        pair = session.read_date(TARGET, KINDS)
        assert all(result.error is not None for result in pair.values())
        assert TARGET in str(pair[KINDS[0]].error)
        assert not (session.directory / TARGET / "complete.json").exists()
        assert session.provenance()["fetched_dates"] == []


@pytest.mark.parametrize("damage", ["duplicate", "wrong_date", "truncated", "unsupported"])
def test_bulk_contract_errors_do_not_fallback(tmp_path: Path, damage: str) -> None:
    import pandas as pd

    api = fake_source()
    original = api.fut_daily

    def bulk(**kwargs: Any) -> pd.DataFrame:
        if damage == "unsupported":
            raise ValueError("unsupported exchange")
        frame = original(**kwargs)
        if damage == "duplicate":
            return pd.concat([frame, frame], ignore_index=True)
        if damage == "wrong_date":
            frame = frame.copy()
            frame["trade_date"] = "20260916"
        if damage == "truncated":
            return pd.concat([frame] * 1000, ignore_index=True)
        return frame

    api.fut_daily = bulk  # type: ignore[method-assign]
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        pair = session.read_date(TARGET, KINDS)
        assert pair[KINDS[0]].error is not None
        assert session.metrics()["endpoints"]["fut_daily"]["attempts"] == 1


def test_same_date_read_twice_does_not_recapture(tmp_path: Path) -> None:
    api = fake_source()
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        first = session.read_date(TARGET, KINDS)
        assert session.read_date(TARGET, KINDS) == first
        assert session.metrics()["attempts"] == 5
        assert session.provenance()["reused_dates"] == []


def test_concurrent_dates_are_ordered_with_independent_clients(tmp_path: Path) -> None:
    import pandas as pd

    from support.fake_source import FakeTushareApi

    dates = ("2026-09-17", "2026-09-18", "2026-09-21", "2026-09-22", "2026-09-23")
    clients: list[FakeTushareApi] = []

    def expand(frame: pd.DataFrame) -> pd.DataFrame:
        frames = []
        for day in dates:
            copy = frame.iloc[-1:].copy() if len(frame) > 1 else frame.copy()
            copy["trade_date"] = day.replace("-", "")
            frames.append(copy)
        return pd.concat(frames, ignore_index=True)

    def factory() -> FakeTushareApi:
        api = fake_source()
        api.index_frames = {code: expand(frame) for code, frame in api.index_frames.items()}
        # Retain all contracts, only replace the date of each quote.
        daily = []
        for day in dates:
            copy = api.option_daily.copy()
            copy["trade_date"] = day.replace("-", "")
            daily.append(copy)
        api.option_daily = pd.concat(daily, ignore_index=True)
        api.futures_daily = {code: expand(frame) for code, frame in api.futures_daily.items()}
        clients.append(api)
        return api

    with ChainSession(
        dates[::-1], api_factory=factory, raw_root=tmp_path, execution=execution()
    ) as session:
        results = list(session.iter_dates(KINDS))
        assert [day for day, _ in results] == list(dates)
        assert all(pair[kind].error is None for _, pair in results for kind in KINDS)
        assert session.metrics()["attempts"] == 3 * len(dates) + 2
    assert len(clients) > 1
    assert sum(len(api.opt_basic_calls) for api in clients) == 1
    assert sum(len(api.fut_basic_calls) for api in clients) == 1


def test_failure_stops_rolling_window_and_waits_before_yield(tmp_path: Path) -> None:
    from threading import Event, Lock

    from market_snapshot.products.mo_option_chain.service import ChainReadResult

    dates = tuple(f"2026-09-{day:02d}" for day in range(17, 25))
    calls: list[str] = []
    call_lock = Lock()
    slow_finished = Event()
    failed = Event()

    successful = {
        kind: service.read_chain_with_api(
            fake_source(),
            service.ChainQuery(TARGET, service.OptionProduct.MO, kind),
            tmp_path / "reference",
        )
        for kind in KINDS
    }

    class SchedulingSession(ChainSession):
        def read_date(self, date: str, price_types: Any) -> dict[Any, ChainReadResult]:
            with call_lock:
                calls.append(date)
            if date == dates[0]:
                assert failed.wait(2)
                slow_finished.set()
                return successful
            if date == dates[1]:
                self.stop.set()
                failed.set()
                return {
                    kind: ChainReadResult(error=service.OptionChainUnavailableError("bad"))
                    for kind in price_types
                }
            return successful

    api = fake_source()
    with SchedulingSession(
        dates, api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        results = list(session.iter_dates(KINDS))
        assert results[-1][0] == dates[1]
        assert slow_finished.is_set()
        assert len(calls) <= 4


def test_failed_low_never_commits_and_missing_matched_future_fails(tmp_path: Path) -> None:
    api = fake_source()
    api.index_frames["000852.SH"]["low"] = None
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        assert all(result.error is not None for result in session.read_date(TARGET, KINDS).values())
        assert not (session.directory / TARGET / "complete.json").exists()
    api = fake_source()
    api.futures_daily.pop("IM2609.CFE")
    with ChainSession(
        [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        assert session.read_date(TARGET, KINDS)[KINDS[0]].error is not None
        assert not (session.directory / TARGET / "complete.json").exists()


def test_lock_excludes_another_process_and_recovers_after_crash(tmp_path: Path) -> None:
    import subprocess
    import sys

    from market_snapshot.products.mo_option_chain.checkpoint import SessionLock

    path = tmp_path / "session.lock"
    script = (
        "import sys; from pathlib import Path; "
        "from market_snapshot.products.mo_option_chain.checkpoint import SessionLock; "
        "lock=SessionLock(Path(sys.argv[1])); lock.acquire(); "
        "print('locked',flush=True); sys.stdin.read()"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "locked"
        with pytest.raises(service.OptionChainUnavailableError, match="already running"):
            SessionLock(path).acquire()
        process.kill()
        process.wait(timeout=5)
        lock = SessionLock(path)
        lock.acquire()
        lock.release()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()


def test_interrupted_commit_never_reuses_unmarked_facts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from market_snapshot.products.mo_option_chain import checkpoint

    api = fake_source()
    original = checkpoint.write_json

    def interrupted(path: Path, value: object) -> None:
        if path.name == "complete.json":
            raise OSError("interrupted before publication")
        original(path, value)

    with monkeypatch.context() as patch:
        patch.setattr(checkpoint, "write_json", interrupted)
        with ChainSession(
            [TARGET], api_factory=lambda: api, raw_root=tmp_path, execution=execution()
        ) as session:
            assert session.read_date(TARGET, KINDS)[KINDS[0]].error is not None
            assert not (session.directory / TARGET / "complete.json").exists()
            assert not list(session.directory.glob(f".{TARGET}-*"))
    with ChainSession(
        [TARGET], resume=True, api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        assert session.read_date(TARGET, KINDS)[KINDS[0]].error is None
        assert session.provenance()["fetched_dates"] == [TARGET]
        assert session.metrics()["attempts"] == 3


def test_concurrent_failure_reports_original_endpoint_instead_of_cancelled_date(
    tmp_path: Path,
) -> None:
    from threading import Event

    dates = ("2026-09-17", "2026-09-18", "2026-09-21")
    failed = Event()
    api = fake_source()
    successful = {
        kind: service.read_chain_with_api(
            fake_source(),
            service.ChainQuery(TARGET, service.OptionProduct.MO, kind),
            tmp_path / "reference",
        )
        for kind in KINDS
    }

    class FailureSession(ChainSession):
        def read_date(self, date: str, price_types: Any) -> dict[Any, service.ChainReadResult]:
            if date == dates[2]:
                error = service.OptionChainUnavailableError(
                    f"MO Chain {date}: fut_daily connection"
                )
                self.failure = date, error
                self.stop.set()
                failed.set()
                return {kind: service.ChainReadResult(error=error) for kind in price_types}
            assert failed.wait(2)
            if date == dates[0]:
                return successful
            return {
                kind: service.ChainReadResult(
                    error=service.OptionChainUnavailableError("acquisition stopped")
                )
                for kind in price_types
            }

    with FailureSession(
        dates, api_factory=lambda: api, raw_root=tmp_path, execution=execution()
    ) as session:
        results = list(session.iter_dates(KINDS))
        assert results[-1][0] == dates[2]
        assert "fut_daily connection" in str(results[-1][1][KINDS[0]].error)
