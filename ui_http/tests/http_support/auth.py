"""Real login credentials for deterministic HTTP consumer tests, never a gate bypass."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ui_http.app import create_app
from ui_http.auth import create_service

PASSWORD = "synthetic-test-password"
ORIGIN = "https://testserver"


def authenticated_client(application: FastAPI) -> TestClient:
    # A module-level app can retain a runtime created under an earlier test's
    # environment. Reset it so login and target requests use the same configuration.
    application.state.auth = None
    service = create_service()
    service.register("consumer", PASSWORD)
    for pending in service.list_pending():
        if pending.username == "consumer":
            service.approve(pending.id)
    login_client = TestClient(create_app(), base_url=ORIGIN, headers={"Origin": ORIGIN})
    response = login_client.post("/auth/login", json={"username": "consumer", "password": PASSWORD})
    assert response.status_code == 200, response.text
    client = TestClient(application, base_url=ORIGIN, headers={"Origin": ORIGIN})
    client.cookies.update(login_client.cookies)
    return client
