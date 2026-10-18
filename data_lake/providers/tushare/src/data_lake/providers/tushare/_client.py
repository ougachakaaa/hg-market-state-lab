"""Checked Tushare HTTP envelope; never treat transport failure as empty facts."""

import json
from collections.abc import Callable
from contextlib import AbstractContextManager
from functools import partial
from http.client import HTTPConnection, HTTPSConnection
from ssl import SSLContext
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPHandler, HTTPSHandler, Request, build_opener

import pandas as pd

Dispatch = Callable[[], AbstractContextManager[None]]


class _SendingHTTPConnection(HTTPConnection):
    def __init__(self, host: str, *, dispatch: Dispatch, **kwargs: Any) -> None:
        super().__init__(host, **kwargs)
        self._dispatch = dispatch

    def endheaders(self, message_body: Any = None, *, encode_chunked: bool = False) -> None:
        # Establish the connection before reserving a send slot; responses never hold it.
        if self.sock is None:
            self.connect()
        with self._dispatch():
            super().endheaders(message_body, encode_chunked=encode_chunked)


class _SendingHTTPSConnection(_SendingHTTPConnection, HTTPSConnection):
    """Cooperative MRO retains HTTPS initialization/connect and the same send gate."""


class _HTTPHandler(HTTPHandler):
    def __init__(self, dispatch: Dispatch) -> None:
        super().__init__()
        self._dispatch = dispatch

    def http_open(self, request: Request) -> Any:
        return self.do_open(partial(_SendingHTTPConnection, dispatch=self._dispatch), request)


class _HTTPSHandler(HTTPSHandler):
    _context: SSLContext

    def __init__(self, dispatch: Dispatch) -> None:
        super().__init__()
        self._dispatch = dispatch

    def https_open(self, request: Request) -> Any:
        return self.do_open(
            partial(_SendingHTTPSConnection, dispatch=self._dispatch),
            request,
            context=self._context,
        )


class RequestFailure(Exception):
    def __init__(self, kind: str, code: int | None = None) -> None:
        super().__init__(kind)
        self.kind = kind
        self.code = code


def rejection(message: object) -> str:
    # Classification only: remote text never reaches logs or public exceptions.
    text = message.lower() if isinstance(message, str) else ""
    if any(word in text for word in ("每分钟", "频次", "频率", "rate limit", "too many")):
        return "rate_limit"
    if any(word in text for word in ("每天", "每日", "总量", "daily limit")):
        return "quota"
    if any(word in text for word in ("权限", "积分", "token", "permission", "授权")):
        return "permission"
    return "provider"


class Client:
    def __init__(self, token: str) -> None:
        self._token = token

    def __getattr__(self, endpoint: str) -> Any:
        return partial(self.query, endpoint)

    def query(
        self, endpoint: str, fields: str = "", *, dispatch: Dispatch, **parameters: object
    ) -> Any:
        # Same endpoint/protocol used by the installed SDK, with checked failures.
        request = Request(
            f"http://api.waditu.com/dataapi/{endpoint}",
            json.dumps(
                {"api_name": endpoint, "token": self._token, "params": parameters, "fields": fields}
            ).encode("utf-8"),
            {"Content-Type": "application/json"},
            method="POST",
        )
        opener = build_opener(_HTTPHandler(dispatch), _HTTPSHandler(dispatch))
        try:
            with opener.open(request, timeout=30) as response:
                payload = json.loads(response.read())
        except HTTPError as exc:
            kind = (
                "rate_limit"
                if exc.code == 429
                else ("permission" if exc.code in (401, 403) else "http")
            )
            raise RequestFailure(kind, exc.code) from None
        except TimeoutError:
            raise RequestFailure("timeout") from None
        except URLError as exc:
            kind = "timeout" if isinstance(exc.reason, TimeoutError) else "network"
            raise RequestFailure(kind) from None
        except (ValueError, UnicodeError):
            raise RequestFailure("response") from None
        except OSError:
            raise RequestFailure("network") from None
        if not isinstance(payload, dict) or type(payload.get("code")) is not int:
            raise RequestFailure("response")
        if payload["code"] != 0:
            raise RequestFailure(rejection(payload.get("msg")), payload["code"])
        data = payload.get("data")
        if not isinstance(data, dict):
            raise RequestFailure("response")
        columns, items = data.get("fields"), data.get("items")
        if (
            not isinstance(columns, list)
            or not all(isinstance(c, str) for c in columns)
            or len(columns) != len(set(columns))
            or not isinstance(items, list)
            or any(not isinstance(row, list) or len(row) != len(columns) for row in items)
        ):
            raise RequestFailure("response")
        return pd.DataFrame(items, columns=columns)
