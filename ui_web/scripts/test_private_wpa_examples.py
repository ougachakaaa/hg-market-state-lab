"""Tool boundary tests: no market inputs, provider calls or default caches."""

import socket
import sqlite3

import private_wpa_examples as tool
import pytest

import lab_config


def test_repository_output_rejected():
    with pytest.raises(ValueError, match="outside all worktrees"):
        tool.isolation(tool.REPO / "private-test-output")


def test_existing_output_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr("sys.argv", ["private_wpa_examples.py", "w2", "--output", str(tmp_path)])
    with pytest.raises(ValueError, match="no overwrite"):
        tool.main()


def test_offline_guard_blocks_all_dependencies(tmp_path):
    with tool.offline_guard():
        for invoke in (
            lab_config.tushare_token,
            lambda: sqlite3.connect(tmp_path / "cache.sqlite3"),
            lambda: socket.create_connection(("127.0.0.1", 1)),
        ):
            with pytest.raises(AssertionError, match="offline verification"):
                invoke()
    assert not (tmp_path / "cache.sqlite3").exists()


def test_dataset_audit_accepts_readonly_uri_and_rejects_other_roots(tmp_path):
    cache = tmp_path / "dataset-cache"
    cache.mkdir()
    path = cache / "audit.sqlite3"
    with tool.isolated_datasets(tmp_path):
        with sqlite3.connect(path):
            pass
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True):
            pass
        with pytest.raises(ValueError, match="outside isolated root"):
            sqlite3.connect(tmp_path / "wrong.sqlite3")


def seal(root):
    tool.write(root / "example-index.json", {
        "profile": "wp-a-private-example-index-v1", "classification": "real_market",
        "publication_rights": "BLOCKED", "files": tool.file_inventory(root),
    })
    (root / "example-index.sha256").write_text(tool.digest(root / "example-index.json"))


def test_changed_index_rejected(tmp_path):
    seal(tmp_path)
    (tmp_path / "example-index.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        tool.verify(tmp_path)


@pytest.mark.parametrize("mutation", ["changed", "missing"])
def test_changed_or_missing_evidence_rejected(tmp_path, mutation):
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}")
    seal(tmp_path)
    if mutation == "changed":
        evidence.write_text('{"changed":true}')
    else:
        evidence.unlink()
    with pytest.raises(ValueError, match="inventory"):
        tool.verify(tmp_path)


def test_stale_pass_cannot_hide_incomplete_stage(tmp_path):
    tool.write(tmp_path / "w2-stage.json", {"status": "RUNNING"})
    tool.write(tmp_path / "research-stage.json", {"status": "PASS"})
    seal(tmp_path)
    with pytest.raises(ValueError, match="incomplete stage"):
        tool.verify(tmp_path)


def test_missing_required_result_fails_offline_replay(tmp_path):
    with pytest.raises(ValueError, match="missing or symlinked evidence"):
        tool.replay_w2(tmp_path)


def test_research_preview_has_exact_scope():
    from market_research.descriptive.execution import preview_plan

    preview = preview_plan(tool.plan())
    assert (preview.planned_count, preview.analysis_attempt_count) == (2, 4)
    assert [j.fixed_job_spec.horizon for j in preview.jobs] == [20, 60]
    assert preview.plan.on_job_failure == "continue"


def test_sqlite_publication_export_is_offline_readonly_and_matches_formal_reader(
    tmp_path, monkeypatch
):
    """Synthetic engineering regression, never real WP-A acceptance."""
    monkeypatch.syspath_prepend(str(tool.REPO / "market_research/tests"))
    from batch_execution_example import run
    from market_research.publication import PublicationStore, publish, retain_source

    batch = run("continue", inject_failure=False)
    output = tmp_path / "research"
    output.mkdir()
    source = retain_source(batch, "synthetic-integration-regression", output / "source.json")
    root = output / "publications"
    store = PublicationStore(root)
    pid = publish(batch, source, "synthetic test only", store)
    monkeypatch.setattr(tool, "plan", lambda: batch.plan)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    with tool.offline_guard(root):
        exported = tool.publication_export(tmp_path)
        assert exported["manifests"][0]["publication_id"] == pid
        assert exported["views"]
        for analysis in exported["analyses"]:
            assert analysis["publication_id"] == pid
        with sqlite3.connect((root / "publications.sqlite3").as_uri() + "?mode=rw", uri=True) as db:
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                db.execute("DELETE FROM publications")
        with pytest.raises(ValueError, match="another SQLite"):
            sqlite3.connect(tmp_path / "dataset-cache.sqlite3")
        # Nested W2 replay guard must retain its strict no-SQLite boundary.
        with tool.offline_guard():
            with pytest.raises(AssertionError, match="offline verification"):
                sqlite3.connect((root / "publications.sqlite3").as_uri() + "?mode=rw", uri=True)
        with pytest.raises(AssertionError, match="offline verification"):
            lab_config.tushare_token()
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before
    assert not (tmp_path / "dataset-cache.sqlite3").exists()


def test_legacy_publication_is_not_opened_or_migrated(tmp_path):
    root = tmp_path / "research/publications"
    root.mkdir(parents=True)
    legacy = root / "legacy-manifest.json"
    legacy.write_text('{}')
    with tool.offline_guard(root):
        with pytest.raises(ValueError, match="expected one actual publication"):
            tool.publication_export(tmp_path)
    assert list(root.iterdir()) == [legacy]
