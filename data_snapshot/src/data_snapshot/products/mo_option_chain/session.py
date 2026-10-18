"""Public MO historical sessions, date acquisition and verified checkpoint reuse."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import time
from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from threading import Event, Lock, local
from types import TracebackType
from typing import Any

from ... import artifacts
from ...capture import (
    common,
    im_futures_basic,
    im_futures_daily,
    index_daily,
    mo_option_basic,
    mo_option_daily,
)
from ...sources import tushare
from ...sources.session_execution import SessionExecution
from . import checkpoint, preparation
from .service import (
    ChainQuery,
    ChainReadError,
    ChainReadResult,
    DateNotAvailableError,
    InvalidQueryError,
    OptionChainUnavailableError,
    OptionProduct,
    PriceType,
    to_read_model,
)

VERSION = 1
BASIC_NAMES = ("mo_option_basic", "im_futures_basic")
DAILY_NAMES = (
    "index_daily",
    "mo_option_basic",
    "mo_option_daily",
    "im_futures_basic",
    "im_futures_daily",
)


class ChainSession:
    """Product-owned context; use the public factory in service.py."""

    def __init__(
        self,
        dates: Sequence[str],
        *,
        resume: bool = False,
        raw_root: Path | None = None,
        api_factory: Callable[[], tushare.TushareApi] | None = None,
        execution: SessionExecution | None = None,
    ) -> None:
        self.dates = tuple(sorted(set(dates)))
        if not self.dates or any(not tushare.is_iso_date(day) for day in self.dates):
            raise InvalidQueryError("session needs nonempty explicit ISO dates")
        self.identity = {"product": "MO", "dates": self.dates, "version": VERSION}
        self.key = hashlib.sha256(
            json.dumps(self.identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        root = artifacts.RAW_DIR if raw_root is None else raw_root
        self.directory = root / "mo-option-chain" / "sessions" / self.key
        self.lock = checkpoint.SessionLock(self.directory.parent / ".locks" / f"{self.key}.lock")
        self.resume = resume
        self.factory = api_factory
        self.execution = SessionExecution() if execution is None else execution
        self.clients = local()
        self.state_lock = Lock()
        self.date_locks = {day: Lock() for day in self.dates}
        self.stop = Event()
        self.failure: tuple[str, ChainReadError] | None = None
        self.pool: ThreadPoolExecutor | None = None
        self.active = False
        self.basic: dict[str, list[artifacts.RawRecord]] = {}
        self.basic_digests: dict[str, str] = {}
        self.reused: set[str] = set()
        self.fetched: set[str] = set()
        self.day_digests: dict[str, dict[str, str]] = {}
        self.started = time.monotonic()

    def _api(self) -> tushare.TushareApi:
        if not hasattr(self.clients, "api"):
            if self.factory is None:
                api = tushare.create_tushare_api(tushare.get_tushare_token())
            else:
                api = self.factory()
            self.clients.api = self.execution.wrap(api)
        result: tushare.TushareApi = self.clients.api
        return result

    def __enter__(self) -> ChainSession:
        try:
            self.lock.acquire()
            self._initialize()
            self.active = True
            return self
        except BaseException as exc:
            self.lock.release()
            if not isinstance(exc, Exception):
                raise
            if isinstance(exc, ChainReadError):
                raise
            if isinstance(exc, tushare.TushareSourceError | OSError):
                raise OptionChainUnavailableError(f"session initialization: {exc}") from None
            raise OptionChainUnavailableError(
                f"session initialization: {type(exc).__name__}"
            ) from None

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.stop.set()
        if self.pool is not None:
            self.pool.shutdown(wait=True, cancel_futures=True)
        self.active = False
        self.lock.release()

    def _initialize(self) -> None:
        manifest_path = self.directory / "manifest.json"
        if self.resume:
            try:
                manifest = checkpoint.read_json(manifest_path)
                if manifest.get("identity") != json.loads(json.dumps(self.identity)):
                    raise ValueError("identity/version mismatch")
                digests = manifest.get("basic_digests")
                if not checkpoint.verified_files(self.directory, digests, BASIC_NAMES):
                    raise ValueError("basic facts are incomplete or corrupt")
                assert isinstance(digests, dict)
                self.basic_digests = dict(digests)
                self.basic = {
                    name: self._rows(self.directory / f"{name}.json") for name in BASIC_NAMES
                }
            except (OSError, ValueError, TypeError) as exc:
                raise OptionChainUnavailableError(f"checkpoint cannot resume: {exc}") from None
        else:
            if self.directory.exists():
                shutil.rmtree(self.directory)
            self.directory.mkdir(parents=True)
            api = self._api()
            frame = api.opt_basic(exchange="CFFEX")
            mo = [
                row
                for row in common.to_raw_records(frame)
                if row.get("exchange") == "CFFEX" and mo_option_basic.is_mo_option(row)
            ]
            if not mo:
                raise OptionChainUnavailableError("opt_basic: no MO contract facts")
            for row in mo:
                mo_option_basic.require_mo_lifecycle(row)
            im = im_futures_basic.collect_active_im_contracts(
                lambda **kwargs: api.fut_basic(**kwargs)
            )
            self.basic = {"mo_option_basic": mo, "im_futures_basic": im}
            for name, rows in self.basic.items():
                artifacts.write_raw_artifact(rows, self.directory, name)
            self.basic_digests = {
                name: checkpoint.digest_file(self.directory / f"{name}.json")
                for name in BASIC_NAMES
            }
            checkpoint.write_json(
                manifest_path,
                {
                    "identity": self.identity,
                    "basic_digests": self.basic_digests,
                },
            )

    @staticmethod
    def _rows(path: Path) -> list[artifacts.RawRecord]:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
            raise ValueError("Raw must be a list of records")
        return value

    def _prepared(
        self,
        date: str,
        kinds: tuple[PriceType, ...],
        directory: Path,
    ) -> dict[PriceType, ChainReadResult]:
        results = {}
        for kind in dict.fromkeys((PriceType.HIGH, PriceType.LOW, *kinds)):
            query = ChainQuery(date, OptionProduct.MO, kind)
            chain = to_read_model(query, preparation.build_chain(date, kind.value, directory))
            results[kind] = ChainReadResult(chain=chain)
        return {kind: results[kind] for kind in kinds}

    def _reuse(
        self,
        date: str,
        kinds: tuple[PriceType, ...],
        directory: Path,
    ) -> dict[PriceType, ChainReadResult] | None:
        if not self.resume and date not in self.fetched:
            return None
        try:
            manifest = checkpoint.read_json(directory / "complete.json")
            digests = manifest.get("digests")
            if (
                manifest.get("date") != date
                or manifest.get("basic_digests") != self.basic_digests
                or not checkpoint.verified_files(directory, digests, DAILY_NAMES)
            ):
                return None
            results = self._prepared(date, kinds, directory)
            assert isinstance(digests, dict)
            with self.state_lock:
                if date not in self.fetched:
                    self.reused.add(date)
                self.day_digests[date] = dict(digests)
            return results
        except (OSError, ValueError, TypeError, preparation.PreparationError):
            return None

    def read_date(
        self,
        date: str,
        price_types: Sequence[PriceType],
    ) -> dict[PriceType, ChainReadResult]:
        if date not in self.dates:
            raise InvalidQueryError("undeclared session date")
        with self.date_locks[date]:
            return self._read_date(date, price_types)

    def _read_date(
        self,
        date: str,
        price_types: Sequence[PriceType],
    ) -> dict[PriceType, ChainReadResult]:
        kinds = tuple(dict.fromkeys(price_types))
        if not self.active or date not in self.dates or not kinds:
            raise InvalidQueryError("inactive session, undeclared date or empty prices")
        if any(not isinstance(kind, PriceType) for kind in kinds):
            raise InvalidQueryError("unsupported session price type")
        if self.stop.is_set():
            return {
                kind: ChainReadResult(error=OptionChainUnavailableError("acquisition stopped"))
                for kind in kinds
            }
        directory = self.directory / date
        stage: Path | None = None
        try:
            reused = self._reuse(date, kinds, directory)
            if reused is not None:
                return reused
            stage = Path(tempfile.mkdtemp(prefix=f".{date}-", dir=self.directory))
            api = self._api()
            mo = mo_option_basic.select_active_mo_universe(self.basic["mo_option_basic"], date)
            facts = {
                "index_daily": index_daily.collect_index_daily(
                    date, lambda **kw: api.index_daily(**kw), (preparation.UNDERLYING_ID,)
                ),
                "mo_option_basic": mo,
                "mo_option_daily": mo_option_daily.capture(api, date, mo),
                "im_futures_basic": self.basic["im_futures_basic"],
                "im_futures_daily": im_futures_daily.capture_bulk_target_date(
                    api, date, self.basic["im_futures_basic"]
                ),
            }
            for name, rows in facts.items():
                artifacts.write_raw_artifact(rows, stage, name)
            results = self._prepared(date, kinds, stage)
            digests = {name: checkpoint.digest_file(stage / f"{name}.json") for name in DAILY_NAMES}
            checkpoint.write_json(
                stage / "complete.json",
                {
                    "date": date,
                    "basic_digests": self.basic_digests,
                    "digests": digests,
                },
            )
            if directory.exists():
                shutil.rmtree(directory)
            stage.replace(directory)
            stage = None
            with self.state_lock:
                self.fetched.add(date)
                self.day_digests[date] = digests
            return results
        except Exception as exc:
            safe_reason = (
                str(exc)
                if isinstance(
                    exc,
                    OSError
                    | ValueError
                    | common.CollectionError
                    | preparation.PreparationError
                    | tushare.TushareSourceError,
                )
                else type(exc).__name__
            )
            error = (
                DateNotAvailableError
                if isinstance(exc, index_daily.NoIndexDataError)
                else OptionChainUnavailableError
            )(f"MO Chain {date}: {safe_reason}")
            with self.state_lock:
                if self.failure is None:
                    self.failure = date, error
                self.stop.set()
            return {kind: ChainReadResult(error=error) for kind in kinds}
        finally:
            if stage is not None:
                shutil.rmtree(stage, ignore_errors=True)

    def iter_dates(
        self,
        price_types: Sequence[PriceType],
        *,
        workers: int = 4,
    ) -> Iterator[tuple[str, dict[PriceType, ChainReadResult]]]:
        if workers < 1 or workers > 4:
            raise InvalidQueryError("workers must be between 1 and 4")
        with ThreadPoolExecutor(max_workers=workers) as pool:
            self.pool = pool
            pending: dict[int, Future[dict[PriceType, ChainReadResult]]] = {}
            next_submit = 0
            for i, date in enumerate(self.dates):
                while next_submit < min(len(self.dates), i + workers) and not self.stop.is_set():
                    day = self.dates[next_submit]
                    pending[next_submit] = pool.submit(self.read_date, day, price_types)
                    next_submit += 1
                if i not in pending:
                    break
                results = pending.pop(i).result()
                if any(result.error is not None for result in results.values()):
                    self.stop.set()
                    pool.shutdown(wait=True, cancel_futures=True)
                    if self.failure is not None:
                        failed_date, error = self.failure
                        yield (
                            failed_date,
                            {kind: ChainReadResult(error=error) for kind in price_types},
                        )
                    else:
                        yield date, results
                    break
                yield date, results

    def metrics(self) -> dict[str, Any]:
        return {**self.execution.metrics(), "elapsed_seconds": time.monotonic() - self.started}

    def provenance(self) -> dict[str, Any]:
        with self.state_lock:
            return {
                "identity_sha256": self.key,
                "version": VERSION,
                "basic_digests": dict(self.basic_digests),
                "daily_digests": {
                    day: dict(digests) for day, digests in sorted(self.day_digests.items())
                },
                "reused_dates": sorted(self.reused),
                "fetched_dates": sorted(self.fetched),
                "metrics": self.metrics(),
            }
