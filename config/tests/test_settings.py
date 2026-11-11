"""Repository configuration source precedence and validation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import lab_config

ENV_NAMES = (
    lab_config.TUSHARE_TOKEN_ENV,
    lab_config.TUSHARE_CALLS_PER_MINUTE_ENV,
    lab_config.LAB_AUTH_JWT_SECRET_ENV,
    lab_config.LAB_AUTH_MODE_ENV,
    lab_config.LAB_AUTH_ORIGIN_ENV,
    lab_config.LAB_AUTH_DB_PATH_ENV,
    lab_config.LAB_RESEARCH_PUBLICATION_ROOT_ENV,
)


@pytest.fixture(autouse=True)
def clean_configuration_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / ".env"
    monkeypatch.setattr(lab_config, "ENV_FILE", path)
    return path


def test_repository_paths_are_anchored_to_the_repository_root() -> None:
    assert (lab_config.REPO_ROOT / "pyproject.toml").is_file()
    assert lab_config.DEFAULT_ENV_FILE == lab_config.REPO_ROOT / ".env"
    assert lab_config.ENV_EXAMPLE_FILE == lab_config.REPO_ROOT / ".env.example"


def test_token_reads_root_env_file(env_file: Path) -> None:
    env_file.write_text("TUSHARE_TOKEN=file-token\n", encoding="utf-8")

    assert lab_config.tushare_token() == "file-token"


def test_process_environment_precedes_root_env_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("TUSHARE_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setenv(lab_config.TUSHARE_TOKEN_ENV, "environment-token")

    assert lab_config.tushare_token() == "environment-token"


def test_blank_environment_token_does_not_fall_back(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("TUSHARE_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setenv(lab_config.TUSHARE_TOKEN_ENV, "   ")

    assert lab_config.tushare_token() is None


def test_token_is_trimmed(env_file: Path) -> None:
    env_file.write_text("TUSHARE_TOKEN=  padded-token  \n", encoding="utf-8")

    assert lab_config.tushare_token() == "padded-token"


def test_reading_token_does_not_mutate_the_process_environment(env_file: Path) -> None:
    env_file.write_text("TUSHARE_TOKEN=file-token\n", encoding="utf-8")

    assert lab_config.tushare_token() == "file-token"
    assert lab_config.TUSHARE_TOKEN_ENV not in os.environ


def test_missing_env_file_uses_defaults(env_file: Path) -> None:
    assert not env_file.exists()
    assert lab_config.tushare_token() is None
    assert lab_config.tushare_calls_per_minute() == 180
    auth = lab_config.auth_settings()
    assert auth.lab_auth_jwt_secret is None
    assert auth.lab_auth_mode == "production"
    assert auth.lab_auth_origin is None
    assert auth.lab_auth_db_path is None
    assert lab_config.publication_root() is None


def test_rate_reads_root_env_file(env_file: Path) -> None:
    env_file.write_text("TUSHARE_CALLS_PER_MINUTE=200\n", encoding="utf-8")

    assert lab_config.tushare_calls_per_minute() == 200


def test_rate_process_environment_precedes_root_env_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("TUSHARE_CALLS_PER_MINUTE=200\n", encoding="utf-8")
    monkeypatch.setenv(lab_config.TUSHARE_CALLS_PER_MINUTE_ENV, "300")

    assert lab_config.tushare_calls_per_minute() == 300


@pytest.mark.parametrize("value", ["0", "501", "abc", "200.0", ""])
def test_invalid_rate_is_a_configuration_error(
    env_file: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv(lab_config.TUSHARE_CALLS_PER_MINUTE_ENV, value)

    with pytest.raises(lab_config.ConfigError, match=r"must be an integer in 1\.\.500"):
        lab_config.tushare_calls_per_minute()


def test_auth_settings_read_root_env_file(env_file: Path) -> None:
    env_file.write_text(
        "\n".join(
            (
                "LAB_AUTH_JWT_SECRET=secret-value",
                "LAB_AUTH_MODE=loopback-http",
                "LAB_AUTH_ORIGIN=http://127.0.0.1:5173",
                "LAB_AUTH_DB_PATH=C:\\absolute\\auth.sqlite3",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    auth = lab_config.auth_settings()
    assert auth.lab_auth_jwt_secret == "secret-value"
    assert auth.lab_auth_mode == "loopback-http"
    assert auth.lab_auth_origin == "http://127.0.0.1:5173"
    assert auth.lab_auth_db_path == "C:\\absolute\\auth.sqlite3"


def test_auth_process_environment_precedes_root_env_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("LAB_AUTH_MODE=loopback-http\n", encoding="utf-8")
    monkeypatch.setenv(lab_config.LAB_AUTH_MODE_ENV, "production")

    assert lab_config.auth_settings().lab_auth_mode == "production"


def test_publication_root_reads_root_env_file(env_file: Path) -> None:
    env_file.write_text(
        "LAB_RESEARCH_PUBLICATION_ROOT=C:\\absolute\\publication\n", encoding="utf-8"
    )

    assert lab_config.publication_root() == "C:\\absolute\\publication"


def test_publication_root_process_environment_precedes_root_env_file(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("LAB_RESEARCH_PUBLICATION_ROOT=C:\\file\\publication\n", encoding="utf-8")
    monkeypatch.setenv(
        lab_config.LAB_RESEARCH_PUBLICATION_ROOT_ENV, "C:\\environment\\publication"
    )

    assert lab_config.publication_root() == "C:\\environment\\publication"


def test_settings_repr_does_not_expose_secrets() -> None:
    token = lab_config.TushareTokenSettings(tushare_token="top-secret-token")
    auth = lab_config.AuthSettings(lab_auth_jwt_secret="top-secret-jwt")

    assert "top-secret-token" not in repr(token)
    assert "top-secret-jwt" not in repr(auth)


def test_unreadable_configuration_is_a_safe_configuration_error(env_file: Path) -> None:
    env_file.mkdir()

    with pytest.raises(lab_config.ConfigError) as failure:
        lab_config.tushare_token()
    assert "top-secret" not in str(failure.value)
    assert str(env_file) in str(failure.value)


def test_working_directory_does_not_change_the_configuration_path(
    env_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("TUSHARE_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert lab_config.tushare_token() == "file-token"


def test_backtesting_root_configuration_precedence(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(lab_config.LAB_BACKTESTING_RUN_ROOT_ENV, raising=False)
    assert lab_config.backtesting_run_root() is None
    env_file.write_text("LAB_BACKTESTING_RUN_ROOT=/example/file/runs\n", encoding="utf-8")
    assert lab_config.backtesting_run_root() == "/example/file/runs"
    monkeypatch.setenv(lab_config.LAB_BACKTESTING_RUN_ROOT_ENV, "/example/process/runs")
    assert lab_config.backtesting_run_root() == "/example/process/runs"
    monkeypatch.setenv(lab_config.LAB_BACKTESTING_RUN_ROOT_ENV, "")
    assert lab_config.backtesting_run_root() == ""
