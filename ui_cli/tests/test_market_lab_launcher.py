import base64
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from scripts import market_lab_auth

import lab_config


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / ".env"
    monkeypatch.setattr(lab_config, "ENV_FILE", path)
    for name in (
        lab_config.LAB_AUTH_MODE_ENV,
        lab_config.LAB_AUTH_JWT_SECRET_ENV,
        lab_config.LAB_AUTH_ORIGIN_ENV,
    ):
        monkeypatch.delenv(name, raising=False)
    return path


def test_default_launcher_skips_secret_generation_and_reuse(env_file: Path) -> None:
    runtime = env_file.parent
    assert market_lab_auth.prepare(runtime) == ("local", "keep", "keep")
    secret = runtime / "jwt-secret"
    assert not secret.exists()
    secret.mkdir()  # Attempting to read it as a secret file would fail.
    assert market_lab_auth.prepare(runtime) == ("local", "keep", "keep")


def test_explicit_loopback_launcher_reuses_the_managed_secret(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("LAB_AUTH_MODE=loopback-http\n", encoding="utf-8")
    runtime = env_file.parent
    assert market_lab_auth.prepare(runtime) == ("authenticated", "origin", "secret")
    secret = runtime.joinpath("jwt-secret").read_text(encoding="ascii")
    assert market_lab_auth.prepare(runtime) == ("authenticated", "origin", "secret")
    assert runtime.joinpath("jwt-secret").read_text(encoding="ascii") == secret
    monkeypatch.setenv(lab_config.LAB_AUTH_JWT_SECRET_ENV, secret)
    monkeypatch.setenv(lab_config.LAB_AUTH_ORIGIN_ENV, market_lab_auth.FRONTEND_ORIGIN)
    assert market_lab_auth.prepare(runtime) == ("authenticated", "keep", "keep")
    assert len(base64.urlsafe_b64decode(secret + "=")) == 32


@pytest.mark.parametrize("mode", ["production", "", "unknown"])
def test_one_click_rejects_modes_that_cannot_serve_local_http(
    env_file: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    env_file.write_text("LAB_AUTH_MODE=loopback-http\n", encoding="utf-8")
    monkeypatch.setenv(lab_config.LAB_AUTH_MODE_ENV, mode)
    with pytest.raises(RuntimeError):
        market_lab_auth.prepare(env_file.parent)
    assert not env_file.with_name("jwt-secret").exists()


def test_explicit_empty_secret_does_not_fall_back(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("LAB_AUTH_MODE=loopback-http\n", encoding="utf-8")
    monkeypatch.setenv(lab_config.LAB_AUTH_JWT_SECRET_ENV, "")
    with pytest.raises(RuntimeError):
        market_lab_auth.prepare(env_file.parent)
    assert not env_file.with_name("jwt-secret").exists()


@pytest.mark.parametrize(
    ("expected", "reported", "access_status", "access_body", "ready"),
    [
        ("local", "local", 200, [], True),
        ("local", "local", 401, market_lab_auth.AUTH_REQUIRED, False),
        ("local", "authenticated", 200, [], False),
        ("authenticated", "authenticated", 401, market_lab_auth.AUTH_REQUIRED, True),
        ("authenticated", "authenticated", 401, {}, False),
        ("authenticated", "authenticated", 200, [], False),
        ("authenticated", "local", 401, market_lab_auth.AUTH_REQUIRED, False),
    ],
)
def test_shared_readiness_checks_mode_and_anonymous_business_status(
    monkeypatch: pytest.MonkeyPatch,
    expected: str,
    reported: str,
    access_status: int,
    access_body: object,
    ready: bool,
) -> None:
    connection = Mock()
    mode = Mock(status=200)
    mode.read.return_value = json.dumps(reported).encode()
    access = Mock(status=access_status)
    access.read.return_value = json.dumps(access_body).encode()
    connection.getresponse.side_effect = [mode, access]
    monkeypatch.setattr(market_lab_auth, "HTTPConnection", Mock(return_value=connection))

    assert market_lab_auth.backend_ready(expected) is ready
    endpoints = [call.args[1] for call in connection.request.call_args_list]
    assert endpoints == (
        ["/auth/mode", "/research/capabilities"] if reported == expected else ["/auth/mode"]
    )
    connection.close.assert_called_once()
