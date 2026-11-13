"""Portable SQLite publication integrity, interruption and bounded-read acceptance."""

import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from batch_execution_example import run
from market_research.publication import (
    InvalidPublicationInput,
    PublicationCollision,
    PublicationCorrupt,
    PublicationNotFound,
    PublicationStore,
    PublicationUnavailable,
    VerificationBudgetExceeded,
    publish,
    retain_source,
)
from market_research.publication._sqlite import SQLiteStorage


@pytest.fixture(scope="module")
def batch():
    return run("stop", inject_failure=True)


def test_uninitialized_and_legacy_reads_create_nothing(tmp_path):
    root = tmp_path / "missing" / "store"
    store = PublicationStore(root)
    assert store.list_publications() == []
    with pytest.raises(PublicationNotFound):
        store.get_publication_manifest(uuid.uuid4().hex)
    assert not root.parent.exists()
    root.mkdir(parents=True)
    (root / "bundles").mkdir()
    (root / "publications").write_text("legacy")
    assert store.list_publications() == []
    assert not (root / "publications.sqlite3").exists()


def test_source_deleted_after_publish_and_legacy_ignored(tmp_path, batch):
    root = tmp_path / "store"
    root.mkdir()
    (root / "publications").write_text("untouched legacy")
    source = retain_source(batch, "source", tmp_path / "source.json")
    store = PublicationStore(root)
    pid = publish(batch, source, "test", store)
    Path(source.location).unlink()
    manifest = store.get_publication_manifest(pid)
    first = manifest["analyses"][0]
    assert store.get_analysis(pid, first["analysis_id"])
    assert store.get_chart_view(pid, first["views"][0]["view_id"])
    assert (root / "publications").read_text() == "untouched legacy"


@pytest.mark.parametrize("raw", [b"", b"not sqlite"])
def test_existing_bad_database_never_recreated(tmp_path, raw):
    path = tmp_path / "publications.sqlite3"
    path.write_bytes(raw)
    with pytest.raises(PublicationCorrupt):
        PublicationStore(tmp_path).list_publications()
    assert path.read_bytes() == raw


@pytest.mark.parametrize("value", ["", "../escape", "bad\x00path"])
def test_invalid_paths(value):
    with pytest.raises(InvalidPublicationInput):
        PublicationStore(value)


@pytest.mark.parametrize("name", ["CON", "trail.", "source:stream"])
def test_windows_reserved_and_stream_names_rejected(tmp_path, batch, name):
    if os.name != "nt":
        pytest.skip("Windows path-name test")
    path = Path(str(tmp_path) + "\\" + name)
    with pytest.raises(InvalidPublicationInput):
        PublicationStore(path)
    with pytest.raises(InvalidPublicationInput):
        retain_source(batch, "source", path)


def test_source_exclusive_and_aliases(tmp_path, batch):
    path = tmp_path / "source.json"
    source = retain_source(batch, "source", path)
    before = path.read_bytes()
    with pytest.raises(PublicationCollision):
        retain_source(batch, "source", path)
    alias = tmp_path / "alias.json"
    os.link(path, alias)
    with pytest.raises(PublicationCorrupt):
        publish(batch, source, "test", PublicationStore(tmp_path / "store"))
    assert path.read_bytes() == before


@pytest.mark.parametrize("suffix", ["", "-journal", "-wal", "-shm"])
def test_hard_link_database_and_sidecars_rejected(tmp_path, batch, suffix):
    source = retain_source(batch, "source", tmp_path / "source.json")
    root = tmp_path / "store"
    store = PublicationStore(root)
    publish(batch, source, "test", store)
    target = Path(str(root / "publications.sqlite3") + suffix)
    if suffix:
        target.write_bytes(b"unsafe")
    os.link(target, tmp_path / "alias")
    with pytest.raises(PublicationCorrupt):
        store.list_publications()


def test_symlink_root_rejected(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(actual, target_is_directory=True)
    except OSError:
        pytest.skip("OS account cannot create symlinks")
    with pytest.raises(PublicationCorrupt):
        PublicationStore(alias).list_publications()


@pytest.mark.parametrize("after", [False, True])
def test_actual_process_exit_at_commit(tmp_path, after):
    root = tmp_path / "store"
    script = """
import os, sys
from pathlib import Path
from batch_execution_example import run
from market_research.publication import PublicationStore, retain_source, publish
from market_research.publication._sqlite import SQLiteStorage
root = Path(sys.argv[1])
batch = run('stop', inject_failure=True)
source = retain_source(batch, 'source', root.parent / 'source.json')
original = SQLiteStorage._commit
def interrupt(self, connection):
    if sys.argv[2] == 'True':
        original(self, connection)
    os._exit(73)
SQLiteStorage._commit = interrupt
publish(batch, source, 'test', PublicationStore(root))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.absolute())
    result = subprocess.run(
        [sys.executable, "-c", script, str(root), str(after)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 73, result.stderr
    store = PublicationStore(root)
    listing = store.list_publications()
    assert len(listing) == int(after)
    with sqlite3.connect(root / "publications.sqlite3") as c:
        assert (
            c.execute("SELECT count(*) FROM records").fetchone()[0] > 0
            if after
            else c.execute("SELECT count(*) FROM records").fetchone()[0] == 0
        )
    if after:
        first = listing[0]["analyses"][0]
        assert store.get_analysis(listing[0]["publication_id"], first["analysis_id"])


def test_bounded_blob_and_selected_payloads(tmp_path, batch):
    source = retain_source(batch, "source", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "test", store)
    first = store.get_publication_manifest(pid)["analyses"][0]
    reads = []
    original = SQLiteStorage.blob

    def track(c, p, kind, identity, *args):
        reads.append((kind, identity))
        return original(c, p, kind, identity, *args)

    with patch.object(SQLiteStorage, "blob", side_effect=track):
        store.list_publications()
        store.get_publication_manifest(pid)
        assert reads == []
        store.get_analysis(pid, first["analysis_id"])
        assert reads == [("source", ""), ("analyses", first["analysis_id"])]
        reads.clear()
        ref = first["views"][0]
        store.get_chart_view(pid, ref["view_id"])
        assert reads == [("source", ""), ("views", ref["view_id"]), ("layers", ref["layer_id"])]
    with sqlite3.connect(store.root / "publications.sqlite3") as c:
        c.execute(
            "UPDATE records SET payload=zeroblob(?) WHERE kind='source'", (source.size + 100,)
        )
    statements = []
    original_connect = sqlite3.connect

    def connect(*args, **kwargs):
        c = original_connect(*args, **kwargs)
        c.set_trace_callback(statements.append)
        return c

    with patch("sqlite3.connect", side_effect=connect):
        with pytest.raises(VerificationBudgetExceeded):
            store.get_analysis(pid, first["analysis_id"], source_limit=source.size + 1)
    assert not any("SELECT payload FROM records" in sql for sql in statements)


def test_permission_failure_classified(tmp_path):
    with patch("pathlib.Path.lstat", side_effect=PermissionError):
        with pytest.raises(PublicationUnavailable):
            PublicationStore(tmp_path).list_publications()


@pytest.mark.parametrize("version", [0, 7])
def test_existing_sqlite_schema_versions(tmp_path, version):
    from market_research.publication import UnsupportedPublicationVersion

    path = tmp_path / "publications.sqlite3"
    with sqlite3.connect(path) as c:
        c.execute("CREATE TABLE foreign_table (id INTEGER)")
        c.execute(f"PRAGMA user_version={version}")
    expected = PublicationCorrupt if version == 0 else UnsupportedPublicationVersion
    with pytest.raises(expected):
        PublicationStore(tmp_path).list_publications()
    with sqlite3.connect(path) as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] == version


def test_incompatible_schema_rejected(tmp_path):
    with sqlite3.connect(tmp_path / "publications.sqlite3") as c:
        c.execute("CREATE TABLE foreign_table (id INTEGER)")
        c.execute("PRAGMA user_version=1")
    with pytest.raises(PublicationCorrupt):
        PublicationStore(tmp_path).list_publications()


def test_sqlite_lock_failure_is_unavailable(tmp_path, batch):
    source = retain_source(batch, "source", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    publish(batch, source, "test", store)
    with sqlite3.connect(store.root / "publications.sqlite3") as c:
        c.execute("BEGIN EXCLUSIVE")
        with pytest.raises(PublicationUnavailable):
            store.list_publications()


def test_junction_root_rejected(tmp_path):
    if os.name != "nt":
        pytest.skip("Windows junction test")
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(alias), str(actual)], capture_output=True, text=True
    )
    if result.returncode:
        pytest.skip("OS account cannot create junctions")
    try:
        with pytest.raises(PublicationCorrupt):
            PublicationStore(alias).list_publications()
    finally:
        alias.rmdir()


def test_signed_zero_roundtrip_and_rewritten_layer_rejected(tmp_path, batch):
    import json
    import math
    from dataclasses import replace

    from market_research.publication import InconsistentPublication
    from market_research.publication.source import canonical_json, digest

    job = batch.job_results[0]
    outcome = job.analysis_outcomes[0]
    original = outcome.statistical_result
    result = replace(
        original, points_and_values=tuple((p, -0.0) for p, v in original.points_and_values)
    )
    evidence = replace(outcome.associated_evidence, statistical_result=result)
    outcome = replace(outcome, statistical_result=result, associated_evidence=evidence)
    job = replace(job, analysis_outcomes=(outcome, *job.analysis_outcomes[1:]))
    batch = replace(batch, job_results=(job, *batch.job_results[1:]))
    source = retain_source(batch, "signed-zero", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "test", store)
    manifest = store.get_publication_manifest(pid)
    first = manifest["analyses"][0]
    ref = first["views"][0]
    view = store.get_chart_view(pid, ref["view_id"])
    assert "-0.0" in canonical_json(view).decode()
    # A numerically equal positive zero is still a different projection.
    with sqlite3.connect(store.root / "publications.sqlite3") as c:
        raw = c.execute(
            "SELECT payload FROM records WHERE kind='layers' AND identity=?", (ref["layer_id"],)
        ).fetchone()[0]
        value = json.loads(raw)
        assert math.copysign(1, value["layer"]["data"][0]["y"]) == -1
        value["layer"]["data"][0]["y"] = 0.0
        raw = canonical_json(value)
        c.execute(
            "UPDATE records SET payload=? WHERE kind='layers' AND identity=?",
            (raw, ref["layer_id"]),
        )
        integrity = json.loads(c.execute("SELECT integrity FROM publications").fetchone()[0])
        integrity["layers"][ref["layer_id"]] = {"sha256": digest(raw), "size": len(raw)}
        c.execute("UPDATE publications SET integrity=?", (canonical_json(integrity),))
    with pytest.raises(InconsistentPublication):
        store.get_chart_view(pid, ref["view_id"])


@pytest.mark.parametrize("status", ["success", "partial_success", "failed"])
def test_original_batch_outcome_and_exact_canonical_records(tmp_path, batch, status):
    from dataclasses import replace

    from market_research.descriptive.execution import BatchResult
    from market_research.publication.source import canonical_json, digest, source_bytes

    if status == "success":
        batch = run("continue", inject_failure=False)
    elif status == "failed":
        plan = replace(
            batch.plan,
            subjects=batch.plan.subjects[:1],
            horizons=batch.plan.horizons[:1],
            windows=batch.plan.windows[1:],
        )
        batch = BatchResult(plan, batch.job_results[1:2])
    assert batch.status == status
    source = retain_source(batch, "source", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "test", store)
    manifest = store.get_publication_manifest(pid)
    assert manifest["status"] == status
    with sqlite3.connect(store.root / "publications.sqlite3") as c:
        raw, sha, size = c.execute("SELECT manifest, sha256, size FROM publications").fetchone()
        assert raw == canonical_json(manifest) and digest(raw) == sha and len(raw) == size
        assert c.execute("SELECT payload FROM records WHERE kind='source'").fetchone()[
            0
        ] == source_bytes(batch, "source")
    for summary in manifest["analyses"]:
        detail = store.get_analysis(pid, summary["analysis_id"])
        assert detail["summary"]["status"] == summary["status"]
    with pytest.raises(PublicationCollision):
        publish(batch, source, "test", store, publication_id=pid)


def test_reader_observes_only_committed_snapshot(tmp_path, batch):
    source = retain_source(batch, "source", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    original = store._storage._commit
    observations = []

    def commit(c):
        # An independent SQLite reader sees the prior committed database.
        observations.append(PublicationStore(store.root).list_publications())
        original(c)

    with patch.object(store._storage, "_commit", side_effect=commit):
        pid = publish(batch, source, "test", store)
    assert observations == [[]]
    assert store.list_publications()[0]["publication_id"] == pid
