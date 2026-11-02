"""Readiness checks use temporary stores and synthetic Batch evidence only."""

import errno
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from batch_execution_example import run
from market_research.publication import (
    InvalidPublicationInput,
    PublicationCorrupt,
    PublicationNotFound,
    PublicationStore,
    PublicationUnavailable,
    publish,
    retain_source,
)


def test_uninitialized_store_is_empty_read_only(tmp_path: Path) -> None:
    missing = tmp_path / "not-created" / "store"
    store = PublicationStore(missing)
    pid = uuid.uuid4().hex
    assert store.list_publications() == []
    with pytest.raises(PublicationNotFound):
        store.get_publication_manifest(pid)
    assert not (tmp_path / "not-created").exists()
    missing.mkdir(parents=True)
    assert store.list_publications() == []
    assert list(missing.iterdir()) == []
    (missing / "bundles").mkdir()
    (missing / "bundles" / "orphan").mkdir()
    assert store.list_publications() == []
    with pytest.raises(PublicationNotFound):
        store.get_publication_manifest(pid)
    assert sorted(p.name for p in missing.iterdir()) == ["bundles"]


def test_initialized_empty_store_and_pagination(tmp_path: Path) -> None:
    (tmp_path / "bundles").mkdir()
    (tmp_path / "publications").mkdir()
    store = PublicationStore(tmp_path)
    assert store.list_publications(limit=1, after=uuid.uuid4().hex) == []
    with pytest.raises(PublicationNotFound):
        store.get_publication_manifest(uuid.uuid4().hex)
    with pytest.raises(InvalidPublicationInput):
        store.list_publications(limit=0)


@pytest.mark.parametrize(
    "case",
    [
        "stray",
        "missing_bundles",
        "file",
        "root_link",
        "parent_link",
        "bundles_link",
        "publications_link",
    ],
)
def test_malformed_stores_fail_without_returning_empty(tmp_path: Path, case: str) -> None:
    root = tmp_path / "store"
    if case == "file":
        root.write_text("not a directory")
    elif case == "root_link":
        root.symlink_to(tmp_path, target_is_directory=True)
    elif case == "parent_link":
        link = tmp_path / "parent"
        link.symlink_to(tmp_path, target_is_directory=True)
        root = link / "absent"
    else:
        root.mkdir()
        if case == "stray":
            (root / "stray").write_text("unexpected")
        elif case == "missing_bundles":
            (root / "publications").mkdir()
        elif case == "bundles_link":
            (root / "bundles").symlink_to(tmp_path, target_is_directory=True)
        else:
            (root / "bundles").mkdir()
            (root / "publications").symlink_to(tmp_path, target_is_directory=True)
    store = PublicationStore(root)
    with pytest.raises(PublicationCorrupt):
        store.list_publications()
    with pytest.raises(PublicationCorrupt):
        store.get_publication_manifest(uuid.uuid4().hex)


@pytest.mark.parametrize("path", ["", "a/../b", "bad\x00path"])
def test_invalid_store_path_rejected(path: str) -> None:
    with pytest.raises(InvalidPublicationInput):
        PublicationStore(path)


def test_permission_failure_is_unavailable(tmp_path: Path) -> None:
    target = tmp_path / "blocked"
    target.mkdir()
    real_open = os.open

    def failing_open(path: str, flags: int, *args: object, **kwargs: object) -> int:
        if path == "blocked":
            raise PermissionError(errno.EACCES, "denied")
        return real_open(path, flags, *args, **kwargs)  # type: ignore[arg-type]

    with patch("market_research.publication.store.os.open", side_effect=failing_open):
        with pytest.raises(PublicationUnavailable):
            PublicationStore(target).list_publications()


def test_external_source_may_disappear_after_commit(tmp_path: Path) -> None:
    batch = run("stop", inject_failure=True)
    ref = retain_source(batch, "synthetic", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, ref, "synthetic", store)
    manifest = store.get_publication_manifest(pid)
    analysis = manifest["analyses"][0]
    Path(ref.location).unlink()
    assert store.get_analysis(pid, analysis["analysis_id"])["summary"] == analysis
    assert store.get_chart_view(pid, analysis["views"][0]["view_id"])["layers"]
    with pytest.raises(PublicationUnavailable):
        publish(batch, ref, "missing source", store)


def test_concurrent_initialization_is_not_a_fabricated_commit(tmp_path: Path) -> None:
    root = tmp_path / "store"
    root.mkdir()
    store = PublicationStore(root)
    original_listdir = os.listdir

    def create_during_scan(fd: int):
        result = original_listdir(fd)
        if not result:
            (root / "bundles").mkdir(exist_ok=True)
            (root / "publications").mkdir(exist_ok=True)
        return result

    with patch("market_research.publication.store.os.listdir", side_effect=create_during_scan):
        assert store.list_publications() == []
    assert store.list_publications() == []


def test_reads_only_selected_payload_files(tmp_path: Path) -> None:
    from publication_read_cost_example import inspect

    batch = run("continue", inject_failure=False)
    source = retain_source(batch, "synthetic", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "synthetic", store)
    metrics = inspect(store, pid)["operations"]
    assert metrics["list"]["file_reads"] == metrics["manifest"]["file_reads"] == 1
    assert metrics["manifest"]["source_json_parses"] == 0
    assert metrics["analysis"]["read_groups"] == {
        "manifest": 1,
        "source": 1,
        "analysis": 1,
        "view": 0,
        "layer": 0,
    }
    assert metrics["view"]["read_groups"] == {
        "manifest": 1,
        "source": 1,
        "analysis": 0,
        "view": 1,
        "layer": 1,
    }
    assert metrics["analysis"]["file_reads"] == 3
    assert metrics["view"]["file_reads"] == 4
    assert metrics["analysis"]["source_json_parses"] == 1
    assert metrics["view"]["source_json_parses"] == 1


def test_invalid_or_symlink_index_entries_are_not_empty(tmp_path: Path) -> None:
    (tmp_path / "bundles").mkdir()
    index = tmp_path / "publications"
    index.mkdir()
    store = PublicationStore(tmp_path)
    (index / "unexpected.json").write_text("{}")
    with pytest.raises(PublicationCorrupt):
        store.list_publications()
    (index / "unexpected.json").unlink()
    temp = index / f".tmp-{uuid.uuid4().hex}"
    temp.symlink_to(tmp_path / "missing")
    with pytest.raises(PublicationCorrupt):
        store.list_publications()
    temp.unlink()
    temp.write_text("uncommitted")
    assert store.list_publications() == []
    temp.unlink()
    bad_commit = index / f"{uuid.UUID(int=1 << 78, version=4).hex}.json"
    bad_commit.symlink_to(tmp_path / "missing")
    with pytest.raises(PublicationCorrupt):
        store.list_publications(after=uuid.UUID(int=(1 << 128) - 1, version=4).hex)


def test_publish_does_not_repair_a_corrupt_root(tmp_path: Path) -> None:
    batch = run("continue", inject_failure=False)
    source = retain_source(batch, "synthetic", tmp_path / "source.json")
    root = tmp_path / "store"
    root.mkdir()
    (root / "stray").write_text("invalid")
    with pytest.raises(PublicationCorrupt):
        publish(batch, source, "synthetic", PublicationStore(root))
    assert [p.name for p in root.iterdir()] == ["stray"]


def test_read_during_atomic_publish_sees_only_committed_state(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from market_research.publication import store as storage

    batch = run("continue", inject_failure=False)
    source = retain_source(batch, "synthetic", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = uuid.uuid4().hex
    ready, release = Event(), Event()
    original_write = storage._write

    def hold_before_commit(parent: int, name: str, content: bytes) -> None:
        original_write(parent, name, content)
        if name.startswith(".tmp-"):
            ready.set()
            if not release.wait(10):
                raise TimeoutError("test did not release publisher")

    with patch.object(storage, "_write", side_effect=hold_before_commit):
        with ThreadPoolExecutor(max_workers=1) as executor:
            pending = executor.submit(
                publish, batch, source, "synthetic", store, publication_id=pid
            )
            try:
                assert ready.wait(10)
                assert store.list_publications() == []
                with pytest.raises(PublicationNotFound):
                    store.get_publication_manifest(pid)
            finally:
                release.set()
            assert pending.result(timeout=10) == pid
    assert [m["publication_id"] for m in store.list_publications()] == [pid]
