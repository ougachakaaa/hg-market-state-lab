"""Repository-level runtime configuration.

The canonical local configuration file is the repository-root ``.env``. Process
environment values always take precedence over the file. This package owns only
loading and validation; consuming modules keep their own error classification and
runtime semantics.

The package deliberately imports no repository module. Business modules may import
this package, but it must never acquire a business dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENV_FILE = REPO_ROOT / ".env"
# Mutable module global: tests and tooling may point it at an isolated file.
ENV_FILE = DEFAULT_ENV_FILE
ENV_EXAMPLE_FILE = REPO_ROOT / ".env.example"

TUSHARE_TOKEN_ENV = "TUSHARE_TOKEN"
TUSHARE_CALLS_PER_MINUTE_ENV = "TUSHARE_CALLS_PER_MINUTE"
LAB_AUTH_JWT_SECRET_ENV = "LAB_AUTH_JWT_SECRET"
LAB_AUTH_MODE_ENV = "LAB_AUTH_MODE"
LAB_AUTH_ORIGIN_ENV = "LAB_AUTH_ORIGIN"
LAB_AUTH_DB_PATH_ENV = "LAB_AUTH_DB_PATH"
LAB_RESEARCH_PUBLICATION_ROOT_ENV = "LAB_RESEARCH_PUBLICATION_ROOT"
LAB_BACKTESTING_RUN_ROOT_ENV = "LAB_BACKTESTING_RUN_ROOT"
LAB_FUTURES_BASIS_RUN_ROOT_ENV = "LAB_FUTURES_BASIS_RUN_ROOT"


class ConfigError(Exception):
    """Repository configuration could not be read or validated."""


class _RepositorySettings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
        env_ignore_empty=False,
        frozen=True,
        env_file_encoding="utf-8",
    )


class TushareTokenSettings(_RepositorySettings):
    tushare_token: str | None = Field(default=None, repr=False)


class TushareRateSettings(_RepositorySettings):
    tushare_calls_per_minute: int = Field(default=180, ge=1, le=500)

    @field_validator("tushare_calls_per_minute", mode="before")
    @classmethod
    def _parse_integer(cls, value: object) -> object:
        # Keep the previous int() semantics: reject "200.0" while accepting
        # surrounding whitespace around an integer string.
        return int(value) if isinstance(value, str) else value


class AuthSettings(_RepositorySettings):
    lab_auth_jwt_secret: str | None = Field(default=None, repr=False)
    lab_auth_mode: str = "production"
    lab_auth_origin: str | None = None
    lab_auth_db_path: str | None = None


class PublicationSettings(_RepositorySettings):
    lab_research_publication_root: str | None = None


class BacktestingRunSettings(_RepositorySettings):
    lab_backtesting_run_root: str | None = None


class FuturesBasisRunSettings(_RepositorySettings):
    lab_futures_basis_run_root: str | None = None


_SettingsT = TypeVar("_SettingsT", bound=_RepositorySettings)


def _load(model: type[_SettingsT]) -> _SettingsT:
    if ENV_FILE.exists() and not ENV_FILE.is_file():
        raise ConfigError(f"Repository configuration is not a regular file: {ENV_FILE}")
    try:
        return model(_env_file=ENV_FILE if ENV_FILE.is_file() else None)  # type: ignore[call-arg]
    except ValidationError:
        raise
    except (OSError, SettingsError, UnicodeError):
        raise ConfigError(
            f"Repository configuration file could not be read: {ENV_FILE}"
        ) from None


def tushare_token() -> str | None:
    """Return the Tushare token from the process environment or root ``.env``.

    A blank token (including an explicitly blank environment value) is reported as
    missing; it never falls back to another source.
    """
    token = _load(TushareTokenSettings).tushare_token
    if token is None:
        return None
    token = token.strip()
    return token or None


def tushare_calls_per_minute() -> int:
    """Return the configured Tushare request-start limit (1..500).

    Raises ``ConfigError`` for an invalid value. The message intentionally keeps the
    provider-facing wording used before configuration was centralized.
    """
    try:
        return _load(TushareRateSettings).tushare_calls_per_minute
    except ValidationError:
        raise ConfigError(
            f"{TUSHARE_CALLS_PER_MINUTE_ENV} must be an integer in 1..500"
        ) from None


def auth_settings() -> AuthSettings:
    """Return Auth serving configuration; semantic validation stays in ui_http."""
    return _load(AuthSettings)


def publication_root() -> str | None:
    """Return the optional Publication storage root."""
    return _load(PublicationSettings).lab_research_publication_root


def futures_basis_run_root() -> str | None:
    """Return the optional case-owned run storage root."""
    return _load(FuturesBasisRunSettings).lab_futures_basis_run_root


def backtesting_run_root() -> str | None:
    """Return optional case-owned backtesting runtime root."""
    return _load(BacktestingRunSettings).lab_backtesting_run_root


__all__ = [
    "AuthSettings",
    "ConfigError",
    "DEFAULT_ENV_FILE",
    "ENV_EXAMPLE_FILE",
    "ENV_FILE",
    "LAB_AUTH_DB_PATH_ENV",
    "LAB_AUTH_JWT_SECRET_ENV",
    "LAB_AUTH_MODE_ENV",
    "LAB_BACKTESTING_RUN_ROOT_ENV",
    "LAB_AUTH_ORIGIN_ENV",
    "LAB_RESEARCH_PUBLICATION_ROOT_ENV",
    "LAB_FUTURES_BASIS_RUN_ROOT_ENV",
    "PublicationSettings",
    "REPO_ROOT",
    "TUSHARE_CALLS_PER_MINUTE_ENV",
    "TUSHARE_TOKEN_ENV",
    "TushareRateSettings",
    "TushareTokenSettings",
    "auth_settings",
    "backtesting_run_root",
    "publication_root",
    "futures_basis_run_root",
    "tushare_calls_per_minute",
    "tushare_token",
]
