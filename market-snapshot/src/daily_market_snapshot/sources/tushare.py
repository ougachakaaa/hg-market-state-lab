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

import os
import re
from datetime import datetime
from typing import Protocol

import pandas as pd
from dotenv import load_dotenv

from ..artifacts import REPO_ROOT

ENV_FILE = REPO_ROOT / ".env"

TOKEN_ENV_VAR = "TUSHARE_TOKEN"

TRADE_DATE_FIELD = "trade_date"
TRADE_DATE_ISO_FORMAT = "%Y-%m-%d"
TRADE_DATE_TUSHARE_FORMAT = "%Y%m%d"
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class TushareSourceError(Exception):
    """Raised when the Tushare Source boundary is not usable as required.

    This is the Source-level failure the Capture layer translates into its own
    ``CollectionError``, so a Capture never leaks a Source-specific exception to
    its callers.
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

    def daily(self, *, trade_date: str) -> pd.DataFrame: ...

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
        trade_date: str | None = ...,
        start_date: str | None = ...,
        end_date: str | None = ...,
    ) -> pd.DataFrame: ...


def get_tushare_token() -> str:
    """Return ``TUSHARE_TOKEN``, loading the local ``.env`` if present.

    Raises ``TushareCredentialError`` instead of returning an empty token, so a
    missing credential fails before any Source request is made.
    """
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE, override=False)

    token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if not token:
        raise TushareCredentialError(
            f"{TOKEN_ENV_VAR} is not set. Set it in the environment or in {ENV_FILE}."
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
    defined in ``guides/daily-market-snapshot.md`` section 3.
    """
    if not ISO_DATE_PATTERN.fullmatch(trade_date):
        raise TushareDateError(f"trade_date must use YYYY-MM-DD, got {trade_date!r}.")
    try:
        parsed = datetime.strptime(trade_date, TRADE_DATE_ISO_FORMAT)
    except ValueError as exc:
        raise TushareDateError(f"trade_date is not a valid date: {trade_date!r}.") from exc
    return parsed.strftime(TRADE_DATE_TUSHARE_FORMAT)


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
    return parsed.strftime(TRADE_DATE_ISO_FORMAT)


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
