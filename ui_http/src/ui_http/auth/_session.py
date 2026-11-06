"""Serving-only Auth configuration and fixed HS256 token contract."""

import base64
import binascii
import ipaddress
import re
import time
from dataclasses import dataclass
from urllib.parse import urlsplit
from uuid import UUID

import jwt

import lab_config

ISSUER = "hg-market-state-lab"
AUDIENCE = "hg-market-state-lab:http"
COOKIE = "lab_access_token"
TTL = 3600


def loopback(host: str) -> bool:
    # localhost is an explicit local development entry; never resolve arbitrary DNS.
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def origin(value: str, *, referer: bool = False) -> tuple[str, str, int]:
    if not value or any(ord(char) <= 32 or ord(char) >= 127 for char in value):
        raise ValueError("Invalid origin")
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or "\\" in value
        or "," in value
        or "%" in parsed.netloc
        or (not referer and (parsed.path or parsed.query or parsed.fragment))
    ):
        raise ValueError("Invalid origin")
    host = parsed.hostname.lower()
    # Disallow ambiguous authorities such as an empty port or invalid DNS labels.
    if parsed.netloc.endswith(":"):
        raise ValueError("Invalid origin")
    if ":" in host:
        host = str(ipaddress.IPv6Address(host))
    elif len(host) > 253 or not all(
        re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split(".")
    ):
        raise ValueError("Invalid origin")
    port = parsed.port
    return (
        parsed.scheme,
        host,
        port if port is not None else (443 if parsed.scheme == "https" else 80),
    )


@dataclass(frozen=True)
class AuthConfig:
    key: bytes
    browser_origin: tuple[str, str, int]
    secure: bool

    @classmethod
    def from_environment(cls) -> "AuthConfig":
        try:
            settings = lab_config.auth_settings()
            secret = settings.lab_auth_jwt_secret
            if secret is None or not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", secret):
                raise ValueError
            key = base64.b64decode(secret + "=" * (-len(secret) % 4), altchars=b"-_", validate=True)
            if len(key) < 32:
                raise ValueError
            origin_value = settings.lab_auth_origin
            if origin_value is None:
                raise ValueError
            target = origin(origin_value)
            mode = settings.lab_auth_mode
            if mode == "production":
                if target[0] != "https":
                    raise ValueError
            elif mode == "loopback-http":
                if target[0] != "http" or not loopback(target[1]):
                    raise ValueError
            else:
                raise ValueError
            return cls(key, target, mode == "production")
        except (lab_config.ConfigError, ValueError, binascii.Error):
            raise RuntimeError("Invalid authentication serving configuration.") from None

    def validate_listener(self, host: str) -> None:
        if not self.secure and not loopback(host):
            raise RuntimeError("Loopback HTTP requires a loopback listener.")

    def issue(self, user_id: str) -> tuple[str, int]:
        issued = int(time.time())
        expires = issued + TTL
        token = jwt.encode(
            {"sub": user_id, "iat": issued, "exp": expires, "iss": ISSUER, "aud": AUDIENCE},
            self.key,
            algorithm="HS256",
        )
        return token, expires

    def subject(self, token: str) -> str:
        claims = jwt.decode(
            token,
            self.key,
            algorithms=["HS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require": ["sub", "iat", "exp", "iss", "aud"],
                "verify_iat": False,
                "verify_exp": False,
                "strict_aud": True,
            },
        )
        issued, expires = claims["iat"], claims["exp"]
        if (
            type(issued) is not int
            or type(expires) is not int
            or expires != issued + TTL
            or not issued <= time.time() < expires
            or str(UUID(claims["sub"])) != claims["sub"]
        ):
            raise ValueError("Invalid token claims")
        return str(claims["sub"])
