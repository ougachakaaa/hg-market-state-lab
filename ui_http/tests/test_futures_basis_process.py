"""Real process death/restart with isolated Auth and synthetic public facts."""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from ui_http.auth import create_service


def test_process_restart_preserves_completed_and_interrupts_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    monkeypatch.setenv("LAB_AUTH_MODE", "loopback-http")
    monkeypatch.setenv("LAB_AUTH_ORIGIN", origin)
    monkeypatch.setenv("LAB_RESEARCH_PUBLICATION_ROOT", str(tmp_path / "publications"))
    service = create_service()
    service.register("restart_user", "synthetic-test-password")
    service.approve(service.list_pending()[0].id)
    command = [
        sys.executable, "-m", "uvicorn", "--app-dir", "ui_web/scripts",
        "futures_basis_browser_app:create_app", "--factory", "--host", "127.0.0.1",
        "--port", str(port), "--no-proxy-headers",
    ]

    def start() -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            command, env=os.environ.copy(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def ready(client: httpx.Client, server: subprocess.Popen[bytes]) -> None:
        for _ in range(200):
            assert server.poll() is None, "Synthetic backend exited before readiness"
            try:
                if client.get("/auth/me").status_code in (200, 401):
                    return
            except httpx.TransportError:
                # A restarted server can reset the first probe while binding.
                pass
            time.sleep(0.05)
        pytest.fail("Synthetic backend did not start")

    path = "/research/futures-basis/runs"
    body = {"product_code": "IM", "start_date": "2024-10-18", "end_date": "2024-10-21"}
    server = start()
    try:
        with httpx.Client(
            base_url=origin, headers={"Origin": origin}, trust_env=False, timeout=2
        ) as client:
            ready(client, server)
            assert client.post("/auth/login", json={
                "username": "restart_user", "password": "synthetic-test-password",
            }).status_code == 200
            accepted = client.post(path, json=body)
            assert accepted.status_code == 202
            completed_id = accepted.json()["run_id"]
            for _ in range(200):
                completed = client.get(f"{path}/{completed_id}").json()
                if completed["status"] == "COMPLETED":
                    break
                time.sleep(0.05)
            else:
                pytest.fail("Synthetic run did not complete")
            before = client.get(f"{path}/{completed_id}/report")
            assert before.status_code == 200
            # The completed worker may still be releasing its process permit.
            for _ in range(100):
                accepted = client.post(path, json=body)
                if accepted.status_code != 409:
                    break
                assert accepted.json()["error"]["kind"] == "run_busy"
                time.sleep(0.01)
            assert accepted.status_code == 202
            interrupted_id = accepted.json()["run_id"]
            for _ in range(100):
                if client.get(f"{path}/{interrupted_id}").json()["status"] == "RUNNING":
                    break
                time.sleep(0.01)
            else:
                pytest.fail("Synthetic worker did not enter RUNNING")
            # Kill the actual backend, not a replacement application in this process.
            server.kill()
            server.wait(timeout=10)
            server = start()
            ready(client, server)
            recovered = client.get(f"{path}/{interrupted_id}")
            assert recovered.status_code == 200
            assert recovered.json()["status"] == "INTERRUPTED"
            assert recovered.json()["failure"]["category"] == "interrupted"
            assert recovered.json()["finished_at"] is not None
            assert recovered.json()["result_available"] is False
            denied = client.get(f"{path}/{interrupted_id}/report")
            assert denied.status_code == 409
            assert denied.json()["error"]["kind"] == "result_unavailable"
            assert client.get(f"{path}/{completed_id}").json() == completed
            after = client.get(f"{path}/{completed_id}/report")
            assert after.status_code == 200 and after.json() == before.json()
            assert after.headers["cache-control"] == "no-store"
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait(timeout=10)
