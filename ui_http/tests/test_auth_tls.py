"""Exercise production cookies over a real local TLS connection."""

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from ui_http.auth import create_service


@pytest.mark.skipif(
    shutil.which("openssl") is None, reason="openssl required for local TLS fixture"
)
def test_production_cookie_over_tls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    origin = f"https://127.0.0.1:{port}"
    monkeypatch.setenv("LAB_AUTH_ORIGIN", origin)
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    service = create_service()
    service.register("tls_user", "synthetic-test-password")
    service.approve(service.list_pending()[0].id)
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "ui_http.app:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--ssl-keyfile",
            str(key),
            "--ssl-certfile",
            str(cert),
            "--no-proxy-headers",
        ],
        env=os.environ.copy(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        with httpx.Client(base_url=origin, verify=False, trust_env=False, timeout=2) as client:
            for _ in range(100):
                try:
                    response = client.get("/auth/me")
                    break
                except httpx.ConnectError:
                    if server.poll() is not None:
                        pytest.fail("TLS server exited before becoming ready")
                    time.sleep(0.05)
            else:
                pytest.fail("TLS server did not become ready")
            assert response.status_code == 401
            response = client.post(
                "/auth/login",
                headers={"Origin": origin},
                json={
                    "username": "tls_user",
                    "password": "synthetic-test-password",
                },
            )
            assert response.status_code == 200
            cookie = response.headers["set-cookie"].lower()
            assert all(
                value in cookie for value in ("secure", "httponly", "samesite=strict", "path=/")
            )
            assert response.headers["cache-control"] == "no-store"
            response = client.get("/auth/me")
            assert response.status_code == 200
            assert "secure" in response.headers["set-cookie"].lower()
            assert response.headers["cache-control"] == "no-store"
    finally:
        server.terminate()
        server.wait(timeout=10)
