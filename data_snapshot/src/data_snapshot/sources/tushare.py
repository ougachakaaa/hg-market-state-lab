"""The thin Tushare Source integration of this project.

The module only carries what belongs to the Source boundary:

* credential / token loading;
* Tushare client creation, plus the protocol of the endpoints this project reads;
* Source date / representation conversion.

Concrete endpoint calls, query parameters and Capture scope belong to
``capture/``. There is deliberately no base data source, provider framework or
registry here (see ``ARCHITECTURE.md`` 9 and 10).
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from datetime import datetime
from threading import Lock
from typing import Protocol

import pandas as pd

import lab_config

TOKEN_ENV_VAR = lab_config.TUSHARE_TOKEN_ENV

TRADE_DATE_FIELD = "trade_date"
TRADE_DATE_ISO_FORMAT = "%Y-%m-%d"
TRADE_DATE_TUSHARE_FORMAT = "%Y%m%d"
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
FUT_DAILY_MIN_INTERVAL_SECONDS = 0.25
FUT_DAILY_RATE_LIMIT_RETRY_SECONDS = 60.0
_fut_daily_lock = Lock()
_last_fut_daily_start: float | None = None
_monotonic = time.monotonic
_sleep = time.sleep


class TushareSourceError(Exception):
    """Raised when the Tushare Source boundary is not usable as required.

    Capture and Product callers use this project-level failure to classify a
    provider request failure without handling a provider-library exception.
    """


class TushareCredentialError(TushareSourceError):
    """Raised when no usable Tushare credential is configured."""


class TushareDateError(TushareSourceError):
    """Raised when a date does not use the representation the Source requires."""


class TushareApi(Protocol):
    """The Tushare endpoints this project reads.

    ``tushare.pro.client.DataApi`` resolves endpoints dynamically and ships no
    type information, so only the endpoints actually used are described here.
    """

    def index_daily(
        self,
        *,
        ts_code: str,
        trade_date: str | None = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
    ) -> pd.DataFrame: ...

    def opt_basic(
        self, *, exchange: str, list_date: str | None = ..., fields: str | None = ...
    ) -> pd.DataFrame: ...

    def opt_daily(
        self,
        *,
        trade_date: str | None = ...,
        exchange: str | None = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
    ) -> pd.DataFrame: ...

    def fut_basic(
        self,
        *,
        exchange: str,
        fut_type: str | None = ...,
        fut_code: str | None = ...,
        fields: str | None = ...,
    ) -> pd.DataFrame: ...

    def fut_daily(
        self,
        *,
        ts_code: str | None = ...,
        exchange: str | None = ...,
        trade_date: str | None = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
    ) -> pd.DataFrame: ...


def call_provider(endpoint: str, call: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """Keep provider-library failures inside the Tushare Source boundary."""
    try:
        return call()
    except TushareSourceError:
        raise
    except Exception as exc:
        raise TushareSourceError(f"Tushare {endpoint} request failed: {exc}") from exc


def _pace_fut_daily() -> None:
    """Reserve a request start while the caller holds the process-local lock."""
    global _last_fut_daily_start
    now = _monotonic()
    if _last_fut_daily_start is not None:
        remaining = FUT_DAILY_MIN_INTERVAL_SECONDS - (now - _last_fut_daily_start)
        if remaining > 0:
            _sleep(remaining)
    _last_fut_daily_start = _monotonic()


def _is_fut_daily_rate_limit(exc: Exception) -> bool:
    message = str(exc).lower()
    return "fut_daily" in message and (
        "频率超限" in message or "rate limit" in message
    )


def call_fut_daily(call: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """Pace every attempt and retry one explicit endpoint rate-limit response."""
    def request_once() -> pd.DataFrame:
        with _fut_daily_lock:
            _pace_fut_daily()
            return call_provider("fut_daily", call)

    try:
        return request_once()
    except TushareSourceError as exc:
        if not _is_fut_daily_rate_limit(exc):
            raise
    _sleep(FUT_DAILY_RATE_LIMIT_RETRY_SECONDS)
    return request_once()


def get_tushare_token() -> str:
    """Return ``TUSHARE_TOKEN`` from the environment or repository-root ``.env``.

    Raises ``TushareCredentialError`` instead of returning an empty token, so a
    missing credential fails before any Source request is made.
    """
    try:
        token = lab_config.tushare_token()
    except lab_config.ConfigError as exc:
        raise TushareCredentialError(str(exc)) from None
    if not token:
        raise TushareCredentialError(
            f"{TOKEN_ENV_VAR} is not set. Set it in the environment or in "
            f"{lab_config.ENV_FILE}."
        )
    return token


def create_tushare_api(token: str) -> TushareApi:
    """Create the Tushare API client for the given token."""
    import tushare as ts

    api: TushareApi = ts.pro_api(token)
    return api


def to_tushare_date(trade_date: str) -> str:
    """Convert a project-level ``YYYY-MM-DD`` date to Tushare ``YYYYMMDD``.

    The input must be exactly ``YYYY-MM-DD``; ``strptime`` alone would also
    accept forms such as ``2026-9-17``, which are not the project-level format
    defined by the shared Capture contract (``capture/common-contract.md``
    section 2).
    """
    if not ISO_DATE_PATTERN.fullmatch(trade_date):
        raise TushareDateError(f"trade_date must use YYYY-MM-DD, got {trade_date!r}.")
    try:
        parsed = datetime.strptime(trade_date, TRADE_DATE_ISO_FORMAT)
    except ValueError as exc:
        raise TushareDateError(f"trade_date is not a valid date: {trade_date!r}.") from exc
    return parsed.date().isoformat().replace("-", "")


def to_iso_date(trade_date: str) -> str:
    """Convert a Source ``YYYYMMDD`` date to ``YYYY-MM-DD``.

    The eight-digit form is checked explicitly: ``strptime`` accepts a shorter
    string such as ``2026092`` by reading a one-digit day, which would silently
    turn a truncated Source fact into a valid-looking date.
    """
    if len(trade_date) != 8 or not trade_date.isdigit():
        raise TushareDateError(
            f"source {TRADE_DATE_FIELD} must use YYYYMMDD, got {trade_date!r}."
        )
    try:
        parsed = datetime.strptime(trade_date, TRADE_DATE_TUSHARE_FORMAT)
    except ValueError as exc:
        raise TushareDateError(
            f"source {TRADE_DATE_FIELD} must use YYYYMMDD, got {trade_date!r}."
        ) from exc
    return parsed.date().isoformat()


def is_iso_date(value: object) -> bool:
    """Report whether a value is already a valid ``YYYY-MM-DD`` date."""
    if not isinstance(value, str) or not ISO_DATE_PATTERN.fullmatch(value):
        return False
    try:
        datetime.strptime(value, TRADE_DATE_ISO_FORMAT)
    except ValueError:
        return False
    return True


def to_iso_date_or_none(value: object) -> str | None:
    """Convert an optional Source ``YYYYMMDD`` value to ``YYYY-MM-DD``.

    Contract lifecycle facts (``list_date`` / ``delist_date``) are optional in
    the Source, so missing values stay ``None`` instead of failing: the
    Captures treat such a contract as having no lifecycle bound on that side.
    A value that already uses the Raw form is kept as it is, so both a Source
    frame and an already-normalized Raw record give the same date.
    """
    if value is None or (isinstance(value, float) and value != value):
        return None
    if is_iso_date(value):
        return str(value)
    text = str(value).strip()
    if not text:
        return None
    return to_iso_date(text)
