"""Publication platform capability failures remain classified and side-effect free."""

from __future__ import annotations

import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from batch_execution_example import run
from market_research.publication import (
    InvalidPublicationInput,
    PublicationStore,
    PublicationUnavailable,
    SourceReference,
    _platform,
    publish,
    retain_source,
)


@pytest.fixture(scope="module")
def batch():
    return run("stop", inject_failure=True)


@pytest.fixture
def unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_platform, "supports_descriptor_relative_io", lambda: False)


def test_construction_is_side_effect_free(tmp_path: Path, unsupported: None) -> None:
    root = tmp_path / "store"
    store = PublicationStore(root)
    assert store.root == root.absolute()
    assert not root.exists()


def test_reads_fail_closed_as_unavailable(tmp_path: Path, unsupported: None) -> None:
    root = tmp_path / "store"
    store = PublicationStore(root)

    with pytest.raises(PublicationUnavailable):
        store.list_publications()
    with pytest.raises(PublicationUnavailable):
        store.get_publication_manifest(uuid.uuid4().hex)

    assert not root.exists()


def test_input_validation_precedes_platform_capability(
    tmp_path: Path, unsupported: None
) -> None:
    store = PublicationStore(tmp_path / "store")

    with pytest.raises(InvalidPublicationInput):
        store.list_publications(limit=0)
    with pytest.raises(InvalidPublicationInput):
        store.get_publication_manifest("not-a-uuid")


def test_retain_and_publish_fail_before_writing(
    tmp_path: Path, batch, unsupported: None
) -> None:
    source_path = tmp_path / "source.json"
    with pytest.raises(PublicationUnavailable):
        retain_source(batch, "synthetic", source_path)
    assert not source_path.exists()

    root = tmp_path / "store"
    store = PublicationStore(root)
    source = SourceReference("synthetic", str(tmp_path / "missing.json"), "0" * 64, 0)
    with pytest.raises(PublicationUnavailable):
        publish(batch, source, "synthetic context", store)
    assert not root.exists()


@pytest.mark.skipif(
    _platform.supports_descriptor_relative_io(),
    reason="requires a platform without POSIX descriptor-relative storage",
)
def test_facade_and_http_app_import_on_unsupported_platform() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import market_research.publication; import ui_http.app"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stderr
