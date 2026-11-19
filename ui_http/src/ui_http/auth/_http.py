"""One HTTP access gate for composed apps, product apps and framework routes."""

import ipaddress
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

import jwt
from fastapi import APIRouter, FastAPI, Request, Response, Security
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.security import APIKeyCookie
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from . import AuthFailureKind, AuthServiceError, UserIdentity, _limiter, create_service
from ._http_models import (
    ACCESS_RESPONSES,
    Accepted,
    ActiveIdentity,
    AuthErrorResponse,
    AuthHttpError,
    Credentials,
)
from ._session import (
    COOKIE,
    LOCAL_WEB_ORIGIN,
    TTL,
    AuthConfig,
    LocalAccess,
    loopback_address,
    origin,
    serving_config,
)

MODE_PATH = "/auth/mode"
ACCOUNT_PATHS = frozenset(f"/auth/{name}" for name in ("register", "login", "logout", "me"))
PUBLIC = frozenset(
    {
        ("GET", MODE_PATH),
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("POST", "/auth/logout"),
    }
)
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
AuthMode = Literal["local", "authenticated"]
cookie_security = APIKeyCookie(name=COOKIE, auto_error=False, scheme_name="CookieSession")


def service_error(error: AuthServiceError, *, login: bool = False) -> AuthHttpError:
    if error.kind == AuthFailureKind.OPERATIONAL_FAILURE:
        return AuthHttpError("internal_error")
    if error.kind == AuthFailureKind.INVALID_INPUT:
        return AuthHttpError("invalid_request")
    return AuthHttpError("invalid_credentials" if login else "authentication_required")


class AuthRuntime:
    def __init__(self, config: AuthConfig) -> None:
        self.config = config
        self.service = create_service()


def runtime(application: FastAPI) -> LocalAccess | AuthRuntime:
    # Also protects ASGI consumers that don't run lifespan. No unconfigured serving path.
    if getattr(application.state, "auth", None) is None:
        config = serving_config()
        application.state.auth = config if isinstance(config, LocalAccess) else AuthRuntime(config)
    result: LocalAccess | AuthRuntime = application.state.auth
    return result


def authenticated_runtime(application: FastAPI) -> AuthRuntime:
    auth = runtime(application)
    if isinstance(auth, LocalAccess):
        raise AuthHttpError("authentication_required")
    return auth


async def require_user(
    request: Request,
    token: Annotated[str | None, Security(cookie_security)],
) -> UserIdentity | None:
    if getattr(request.state, "local_access_granted", False):
        return None
    if (request.method, request.scope["path"]) in PUBLIC:
        return None
    if hasattr(request.state, "auth_user"):
        user: UserIdentity = request.state.auth_user
        return user
    if token is None or len(token) > 4096:
        raise AuthHttpError("authentication_required")
    auth = authenticated_runtime(request.app)
    try:
        subject = auth.config.subject(token)
    except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError):
        raise AuthHttpError("authentication_required") from None
    try:
        user = await run_in_threadpool(auth.service.get_active_user, subject)
    except AuthServiceError as error:
        raise service_error(error) from None
    request.state.auth_user = user
    return user


def check_origin(
    request: Request, expected: tuple[str, str, int], *, local: bool = False
) -> None:
    safe = request.method in SAFE_METHODS
    if safe and not local:
        return
    values = request.headers.getlist("origin")
    referer = not values
    if referer:
        values = request.headers.getlist("referer")
    if safe and not values:
        return
    try:
        if len(values) != 1 or origin(values[0], referer=referer) != expected:
            raise ValueError
    except ValueError:
        raise AuthHttpError("origin_forbidden") from None


def check_local_access(request: Request) -> None:
    server = request.scope.get("server")
    peer = request.scope.get("client")
    hosts = request.headers.getlist("host")
    fetch_site = request.headers.getlist("sec-fetch-site")
    if (
        not server
        or not loopback_address(server[0])
        or not peer
        or not loopback_address(peer[0])
        or request.scope.get("scheme") != "http"
        or len(hosts) != 1
        or any(character in hosts[0] for character in "/?#")
        or fetch_site not in ([], ["same-origin"], ["none"])
        or any(
            name.startswith("x-forwarded-") or name in {"forwarded", "via", "x-real-ip"}
            for name in request.headers
        )
    ):
        raise AuthHttpError("origin_forbidden")
    try:
        target = origin(f"http://{hosts[0]}")
    except ValueError:
        raise AuthHttpError("origin_forbidden") from None
    listener = ("http", str(ipaddress.ip_address(server[0])), server[1])
    if target not in (listener, LOCAL_WEB_ORIGIN):
        raise AuthHttpError("origin_forbidden")
    check_origin(request, target, local=True)


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("Duplicate JSON key")
        result[name] = value
    return result


async def auth_body(request: Request) -> bytes:
    if request.query_params:
        raise AuthHttpError("invalid_request")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > 4096:
            raise AuthHttpError("invalid_request")
        data.extend(chunk)
    raw = bytes(data)
    if request.url.path in {"/auth/me", "/auth/logout"}:
        if raw:
            raise AuthHttpError("invalid_request")
        return raw
    content_types = request.headers.getlist("content-type")
    if (
        len(content_types) != 1
        or content_types[0].split(";", 1)[0].strip().lower() != "application/json"
        or "content-encoding" in request.headers
    ):
        raise AuthHttpError("invalid_request")
    try:
        # Decode explicitly; JSON's UTF-16/32 autodetection is not an accepted wire encoding.
        body = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)
        Credentials.model_validate(body)
    except (ValueError, UnicodeError, ValidationError, RecursionError):
        raise AuthHttpError("invalid_request") from None
    return raw


def set_cookie(response: Response, config: AuthConfig, user_id: str) -> None:
    try:
        token, expires = config.issue(user_id)
        response.set_cookie(
            COOKIE,
            token,
            max_age=TTL,
            expires=datetime.fromtimestamp(expires, UTC),
            path="/",
            secure=config.secure,
            httponly=True,
            samesite="strict",
        )
    except Exception:
        raise AuthHttpError("internal_error") from None


class AccessGate:
    """Authenticate before routing/body parsing; renew only at final response start."""

    def __init__(self, app: ASGIApp, application: FastAPI) -> None:
        self.app, self.application = app, application

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)
        path = scope["path"]
        public = (request.method, path) in PUBLIC
        is_auth = path in ACCOUNT_PATHS
        downstream_receive: Receive
        try:
            auth = runtime(self.application)
        except (RuntimeError, AuthServiceError):
            await AuthHttpError("internal_error").response()(scope, receive, send)
            return

        if isinstance(auth, LocalAccess):
            try:
                check_local_access(request)
            except AuthHttpError as error:
                await error.response()(scope, receive, send)
                return
            if path.rstrip("/") in ACCOUNT_PATHS:
                await Response(status_code=404, headers={"Cache-Control": "no-store"})(
                    scope, receive, send
                )
                return
            request.state.local_access_granted = True
            await self.app(scope, receive, send)
            return

        try:
            auth.config.validate_listener((scope.get("server") or ("", 0))[0])
            if (request.method, path) in {
                ("POST", "/auth/register"),
                ("POST", "/auth/login"),
            }:
                peer = scope.get("client")
                retry = _limiter.limiter.reserve(
                    path.rsplit("/", 1)[1], peer[0] if peer else "unknown"
                )
                if retry is not None:
                    raise AuthHttpError("rate_limited", retry)
            if not public:
                await require_user(request, await cookie_security(request))
            check_origin(request, auth.config.browser_origin)
            if is_auth:
                raw = await auth_body(request)
                delivered = False

                async def replay() -> Message:
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": raw, "more_body": False}
                    return await receive()

                downstream_receive = replay
            else:
                downstream_receive = receive
        except AuthHttpError as error:
            await error.response()(scope, receive, send)
            return
        except (RuntimeError, AuthServiceError):
            await AuthHttpError("internal_error").response()(scope, receive, send)
            return

        signing_failed = False

        async def final_send(message: Message) -> None:
            nonlocal signing_failed
            if signing_failed:
                return
            if message["type"] == "http.response.start":
                response = Response()
                response.raw_headers = list(message.get("headers", []))
                if is_auth or hasattr(request.state, "auth_user"):
                    response.headers["Cache-Control"] = "no-store"
                if not public and 200 <= message["status"] < 300:
                    try:
                        set_cookie(response, auth.config, request.state.auth_user.id)
                    except AuthHttpError as error:
                        signing_failed = True
                        await error.response()(scope, receive, send)
                        return
                message["headers"] = response.raw_headers
            await send(message)

        try:
            await self.app(scope, downstream_receive, final_send)
        except AuthHttpError as error:
            await error.response()(scope, receive, send)


router = APIRouter(prefix="/auth", tags=["Authentication"])
AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    **{status: value for status, value in ACCESS_RESPONSES.items() if status != 401},
    400: {"model": AuthErrorResponse},
    429: {"model": AuthErrorResponse, "headers": {"Retry-After": {"schema": {"type": "integer"}}}},
}
LOCAL_DISABLED: dict[int | str, dict[str, Any]] = {
    404: {"description": "Account operation unavailable in local mode"}
}


@router.get(
    "/mode",
    response_model=AuthMode,
    operation_id="get_auth_mode",
)
def get_mode(request: Request, response: Response) -> AuthMode:
    response.headers["Cache-Control"] = "no-store"
    return "local" if isinstance(runtime(request.app), LocalAccess) else "authenticated"


@router.post(
    "/register",
    status_code=202,
    response_model=Accepted,
    operation_id="register_auth_user",
    responses={**AUTH_RESPONSES, **LOCAL_DISABLED},
)
def register(credentials: Credentials, request: Request) -> Accepted:
    auth = authenticated_runtime(request.app)
    try:
        auth.service.register(credentials.username, credentials.password)
    except AuthServiceError as error:
        raise service_error(error) from None
    return Accepted()


@router.post(
    "/login",
    response_model=ActiveIdentity,
    operation_id="login_auth_user",
    responses={**AUTH_RESPONSES, **LOCAL_DISABLED, 401: {"model": AuthErrorResponse}},
)
def login(credentials: Credentials, request: Request, response: Response) -> ActiveIdentity:
    auth = authenticated_runtime(request.app)
    try:
        user = auth.service.verify_credentials(credentials.username, credentials.password)
    except AuthServiceError as error:
        raise service_error(error, login=True) from None
    set_cookie(response, auth.config, user.id)
    return ActiveIdentity(**asdict(user))


@router.get(
    "/me",
    response_model=ActiveIdentity,
    operation_id="get_auth_user",
    responses={**ACCESS_RESPONSES, **LOCAL_DISABLED, 400: {"model": AuthErrorResponse}},
)
def me(request: Request) -> ActiveIdentity:
    return ActiveIdentity(**asdict(request.state.auth_user))


@router.post(
    "/logout",
    status_code=204,
    operation_id="logout_auth_user",
    responses={
        **LOCAL_DISABLED,
        400: {"model": AuthErrorResponse},
        403: {"model": AuthErrorResponse},
        500: {"model": AuthErrorResponse},
    },
)
def logout(request: Request) -> Response:
    response = Response(status_code=204)
    response.delete_cookie(
        COOKIE,
        path="/",
        secure=authenticated_runtime(request.app).config.secure,
        httponly=True,
        samesite="strict",
    )
    return response


def install_auth(application: FastAPI, *, auth_routes: bool = False) -> None:
    """Install the identical policy on every serveable factory; schema remains offline."""
    from fastapi import Depends

    application.router.dependencies.append(Depends(require_user))
    application.add_middleware(AccessGate, application=application)
    original_lifespan = application.router.lifespan_context

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[Any]:
        runtime(app)
        async with original_lifespan(app) as state:
            yield state

    application.router.lifespan_context = lifespan

    @application.exception_handler(AuthHttpError)
    async def handle_auth_error(_request: Request, error: AuthHttpError) -> Response:
        return error.response()

    @application.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, _error: Exception) -> Response:
        # Preserve the framework's default 500 body while preventing identity-response caching.
        return PlainTextResponse(
            "Internal Server Error", status_code=500, headers={"Cache-Control": "no-store"}
        )

    original_validation = application.exception_handlers.get(RequestValidationError)

    @application.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, error: RequestValidationError) -> Response:
        if request.url.path.startswith("/auth/"):
            return AuthHttpError("invalid_request").response()
        assert original_validation is not None
        from inspect import isawaitable

        pending = original_validation(request, error)
        result: Response = await pending if isawaitable(pending) else pending
        return result

    if auth_routes:
        application.include_router(router)
    build = application.openapi

    def openapi() -> dict[str, Any]:
        document = build()
        # Access errors have their own schema even on product-only offline builders.
        definitions = AuthErrorResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        schemas = document.setdefault("components", {}).setdefault("schemas", {})
        schemas.update(definitions.pop("$defs", {}))
        schemas["AuthErrorResponse"] = definitions
        for path, methods in document["paths"].items():
            for method, operation in methods.items():
                public = (method.upper(), path) in PUBLIC
                if public:
                    operation["security"] = []
                for status in ["403", "500"] if public else ["401", "403", "500"]:
                    # A product's own 500 remains documented, with Auth as an alternative.
                    ref = {"$ref": "#/components/schemas/AuthErrorResponse"}
                    existing = operation["responses"].get(status)
                    if existing:
                        schema = (
                            existing.get("content", {}).get("application/json", {}).get("schema")
                        )
                        if schema and schema != ref:
                            existing["content"]["application/json"]["schema"] = {
                                "anyOf": [schema, ref]
                            }
                            continue
                    operation["responses"][status] = {
                        "description": "HTTP access error",
                        "content": {"application/json": {"schema": ref}},
                    }
        return document

    application.openapi = openapi  # type: ignore[method-assign]
