"""Transport failures must never prove empty facts or expose provider text."""

import json
import logging
from email.message import Message
from typing import Any
from urllib.error import HTTPError, URLError

import pytest

from data_lake._domain import ExecutionFailure
from data_lake.providers.tushare import TushareExecutor, _client, _executor


class Response:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> "Response":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


@pytest.fixture
def runtime(monkeypatch: pytest.MonkeyPatch) -> TushareExecutor:
    monkeypatch.setattr(_executor, "_states", {})
    monkeypatch.setenv("TUSHARE_TOKEN", "fake-secret-token")
    return TushareExecutor()


@pytest.mark.parametrize("items", [[], [["IF2609.CFX", None]]])
def test_checked_success_preserves_empty_and_null(
    monkeypatch: pytest.MonkeyPatch, runtime: TushareExecutor, items: list[Any]
) -> None:
    monkeypatch.setattr(
        _client,
        "urlopen",
        lambda *args, **kwargs: Response(
            {"code": 0, "data": {"fields": ["ts_code", "pre_close"], "items": items}}
        ),
    )
    result = runtime.call("fut_daily")
    assert result.to_dict(orient="records") == (
        [] if not items else [{"ts_code": "IF2609.CFX", "pre_close": None}]
    )


@pytest.mark.parametrize(
    "message,kind",
    [
        ("每分钟最多访问该接口200次 fake-secret-token", "rate_limit"),
        ("每天最多访问100000次 private", "quota"),
        ("没有访问权限 fake-secret-token", "permission"),
        ("private unrecognized message fake-secret-token", "permission"),
        ("系统内部错误 private", "provider"),
    ],
)
def test_rejection_has_safe_actionable_classification(
    monkeypatch: pytest.MonkeyPatch,
    runtime: TushareExecutor,
    caplog: pytest.LogCaptureFixture,
    message: str,
    kind: str,
) -> None:
    caplog.set_level(logging.DEBUG, logger="data_lake")
    monkeypatch.setattr(
        _client, "urlopen", lambda *args, **kwargs: Response({"code": 2002, "msg": message})
    )
    with pytest.raises(ExecutionFailure) as caught:
        runtime.call("opt_daily", ts_code="fake-secret-token", unlisted="private")
    assert caught.value.code == "source_request"
    assert kind in caught.value.reason and "opt_daily" in caught.value.reason
    assert "fake-secret-token" not in caught.value.reason + caplog.text
    assert message not in caplog.text and "unlisted" not in caplog.text


@pytest.mark.parametrize(
    "error,kind",
    [
        (HTTPError("http://test", 500, "private", Message(), None), "http"),
        (HTTPError("http://test", 429, "private", Message(), None), "rate_limit"),
        (HTTPError("http://test", 403, "private", Message(), None), "permission"),
        (URLError("private"), "network"),
        (TimeoutError("private"), "timeout"),
    ],
)
def test_transport_failure_cannot_be_empty_page(
    monkeypatch: pytest.MonkeyPatch, runtime: TushareExecutor, error: Exception, kind: str
) -> None:
    calls = []

    def broken(*args: Any, **kwargs: Any) -> Response:
        calls.append(1)
        raise error

    monkeypatch.setattr(_client, "urlopen", broken)
    with pytest.raises(ExecutionFailure, match=kind):
        runtime.call("opt_basic")
    assert calls == [1]  # no hidden retry


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"code": "0"},
        {"code": 0, "data": None},
        {"code": 0, "data": {"fields": ["x", "x"], "items": []}},
        {"code": 0, "data": {"fields": ["x"], "items": [[1, 2]]}},
    ],
)
def test_bad_envelope_cannot_prove_catalog_exhaustion(
    monkeypatch: pytest.MonkeyPatch, runtime: TushareExecutor, payload: object
) -> None:
    monkeypatch.setattr(_client, "urlopen", lambda *args, **kwargs: Response(payload))
    with pytest.raises(ExecutionFailure, match="response"):
        runtime.call("fut_basic")
