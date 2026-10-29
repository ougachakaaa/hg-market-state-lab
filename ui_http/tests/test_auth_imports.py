"""Fresh-process compatibility of the lazy HTTP facade in both import orders."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize("first", [
    "import ui_http.auth",
    "import importlib; importlib.import_module('ui_http.app')",
    "from ui_http import create_app",
])
def test_existing_http_public_entry_remains_compatible(first: str) -> None:
    code = first + """
import importlib
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ui_http import app, create_app
runtime = importlib.import_module('ui_http.app')
assert isinstance(app, FastAPI)
assert app is runtime.app
assert create_app is runtime.create_app
assert TestClient(app).get('/openapi.json').status_code == 200
assert create_app().openapi() == app.openapi()
"""
    result = subprocess.run(
        [sys.executable, "-c", code], text=True, capture_output=True, check=False, timeout=20,
    )
    assert result.returncode == 0, result.stderr
