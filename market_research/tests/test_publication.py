"""Synthetic public Research evidence; no network, Workbench, or default caches."""

import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from batch_execution_example import run
from market_research.publication import (
    InconsistentPublication,
    InvalidPublicationInput,
    PublicationCollision,
    PublicationCorrupt,
    PublicationNotFound,
    PublicationStore,
    PublicationUnavailable,
    UnsupportedPublicationVersion,
    publish,
    retain_source,
)
from market_research.publication._platform import supports_descriptor_relative_io
from market_research.publication.source import canonical_json, digest

pytestmark = pytest.mark.skipif(
    not supports_descriptor_relative_io(),
    reason="Publication storage requires POSIX descriptor-relative operations",
)


@pytest.fixture(scope="module")
def batch():
    return run("stop", inject_failure=True)


@pytest.fixture
def published(tmp_path, batch):
    source = retain_source(batch, "synthetic-run", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "synthetic test data", store)
    return batch, source, store, pid


def envelope(store, pid):
    return json.loads((store.root / "publications" / f"{pid}.json").read_text())


def bundle(store, pid):
    return store.root / "bundles" / envelope(store, pid)["bundle"]


def rewrite_envelope(store, pid, data):
    (store.root / "publications" / f"{pid}.json").write_bytes(canonical_json(data))


def test_publish_read_reopen_and_scope(published):
    batch, _, store, pid = published
    fresh = PublicationStore(store.root)
    manifest = fresh.get_publication_manifest(pid)
    assert manifest["status"] == "partial_success"
    assert len(manifest["jobs"]) == 8 and len(manifest["analyses"]) == 16
    assert manifest["jobs"][0]["status"] == "Success"
    assert manifest["jobs"][1]["status"] == "Failed"
    assert all(j["status"] == "Skipped" for j in manifest["jobs"][2:])
    assert fresh.list_publications() == [manifest]
    same_request = [a for a in manifest["analyses"] if a["request_id"] == "quantiles"]
    assert len({a["analysis_id"] for a in same_request}) == 8
    assert len({json.dumps(a["job_identity"], sort_keys=True) for a in same_request}) == 8
    for a in manifest["analyses"]:
        detail = fresh.get_analysis(pid, a["analysis_id"])
        assert detail["summary"] == a
        assert len(a["views"]) == (
            1
            if a["status"] == "success" and a["request_id"] == "quantiles"
            else 2
            if a["status"] == "success"
            else 0
        )
        for ref in a["views"]:
            view = fresh.get_chart_view(pid, ref["view_id"])
            assert view["layers"][0]["layer"]["type"] in ("line", "bar")
    assert batch.status == "partial_success"
    failed = next(a for a in manifest["analyses"] if a["status"] == "failed")
    assert (
        fresh.get_analysis(pid, failed["analysis_id"])["failure"]["fields"]["error"]["$error"]
        == "CalculationFailure"
    )
    with pytest.raises(PublicationNotFound):
        fresh.get_analysis(pid, "0" * 64)


def test_collision_and_changed_source(published):
    batch, source, store, pid = published
    with pytest.raises(PublicationCollision):
        publish(batch, source, "changed content", store, publication_id=pid)
    Path(source.location).write_bytes(b"modified")
    with pytest.raises(InconsistentPublication):
        publish(batch, source, "test", store)
    Path(source.location).unlink()
    with pytest.raises(PublicationUnavailable):
        publish(batch, source, "test", store)


def test_invalid_association_is_rejected(tmp_path, batch):
    job = batch.job_results[0]
    outcome = job.analysis_outcomes[0]
    evidence = replace(
        outcome.associated_evidence,
        statistical_result=batch.job_results[0].analysis_outcomes[1].statistical_result,
    )
    malformed = replace(outcome, associated_evidence=evidence)
    bad_job = replace(job, analysis_outcomes=(malformed, *job.analysis_outcomes[1:]))
    with pytest.raises(ValueError):
        replace(batch, job_results=(bad_job, *batch.job_results[1:]))
    with pytest.raises(InvalidPublicationInput):
        retain_source(batch, "", tmp_path / "bad")


def test_missing_corrupt_payload_and_read_isolation(published):
    _, _, store, pid = published
    manifest = store.get_publication_manifest(pid)
    first, second = manifest["analyses"][:2]
    path = bundle(store, pid) / "analyses" / f"{second['analysis_id']}.json"
    path.unlink()
    assert store.get_publication_manifest(pid) == manifest
    assert store.get_analysis(pid, first["analysis_id"])["summary"] == first
    with pytest.raises(PublicationCorrupt):
        store.get_analysis(pid, second["analysis_id"])
    layer = bundle(store, pid) / "layers" / f"{second['views'][1]['layer_id']}.json"
    layer.write_text("{}")
    assert store.get_chart_view(pid, first["views"][0]["view_id"])
    with pytest.raises(PublicationCorrupt):
        store.get_chart_view(pid, second["views"][1]["view_id"])


def test_source_and_manifest_corruption_are_detected(published):
    _, _, store, pid = published
    manifest = store.get_publication_manifest(pid)
    source = bundle(store, pid) / "source.json"
    source.write_bytes(b"{}")
    assert store.get_publication_manifest(pid) == manifest
    with pytest.raises(PublicationCorrupt):
        store.get_analysis(pid, manifest["analyses"][0]["analysis_id"])
    commit = store.root / "publications" / f"{pid}.json"
    commit.write_bytes(b"not json")
    with pytest.raises(PublicationCorrupt):
        store.get_publication_manifest(pid)


def test_versions_paths_symlinks_and_cross_publication(published):
    batch, source, store, pid = published
    m = store.get_publication_manifest(pid)
    other = publish(batch, source, "second", store)
    other_view = store.get_publication_manifest(other)["analyses"][0]["views"][0]["view_id"]
    assert store.get_chart_view(other, other_view)
    with pytest.raises(PublicationNotFound):
        store.get_chart_view(pid, other_view)
    with pytest.raises(InvalidPublicationInput):
        store.get_chart_view(pid, "../source.json")
    view = m["analyses"][0]["views"][0]
    target = bundle(store, pid) / "layers" / f"{view['layer_id']}.json"
    target.unlink()
    target.symlink_to(Path(source.location))
    with pytest.raises(PublicationCorrupt):
        store.get_chart_view(pid, view["view_id"])
    env = envelope(store, pid)
    env["schema"] = "publication-envelope-v99"
    rewrite_envelope(store, pid, env)
    with pytest.raises(UnsupportedPublicationVersion):
        store.get_publication_manifest(pid)


def test_concurrent_publish_one_winner_and_orphans_invisible(tmp_path, batch):
    source = retain_source(batch, "fixture", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = uuid.uuid4().hex

    def attempt():
        try:
            return publish(batch, source, "fixture", store, publication_id=pid)
        except PublicationCollision:
            return "collision"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == sorted([pid, "collision"])
    assert len(store.list_publications()) == 1
    assert len(os.listdir(store.root / "bundles")) == 2


def test_failed_commit_is_invisible(tmp_path, batch):
    source = retain_source(batch, "fixture", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    with patch("market_research.publication.store.os.link", side_effect=OSError("interrupted")):
        with pytest.raises(PublicationUnavailable):
            publish(batch, source, "fixture", store)
    assert store.list_publications() == []


def test_manifest_association_corruption_is_rejected(published):
    _, _, store, pid = published
    env = envelope(store, pid)
    env["manifest"]["analyses"][0]["request_id"] = "other"
    env["manifest_sha256"] = digest(canonical_json(env["manifest"]))
    rewrite_envelope(store, pid, env)
    with pytest.raises(InconsistentPublication):
        store.get_publication_manifest(pid)


def test_retained_input_verifier_rejects_changed_facts(batch):
    from market_research.descriptive.cases.trailing_return import verify_input_provenance

    job = batch.job_results[0]
    provenance = job.observation_set.provenance
    verify_input_provenance(job.fixed_job_spec, provenance)
    index_slice = provenance.prepared_inputs.index_slice
    assert index_slice is not None
    first, *remaining = index_slice.final_export.records
    changed_row = replace(first, close=first.close + 1)
    changed_export = replace(index_slice.final_export, records=(changed_row, *remaining))
    changed_index = replace(index_slice, final_export=changed_export)
    changed_prepared = replace(provenance.prepared_inputs, index_slice=changed_index)
    changed = replace(provenance, prepared_inputs=changed_prepared)
    with pytest.raises(ValueError, match="fingerprint"):
        verify_input_provenance(job.fixed_job_spec, changed)


def test_invalid_statistical_result_is_rejected(tmp_path, batch):
    job = batch.job_results[0]
    outcome = job.analysis_outcomes[0]
    bad_result = replace(outcome.statistical_result, sample_count=999)
    bad_evidence = replace(outcome.associated_evidence, statistical_result=bad_result)
    bad_outcome = replace(outcome, statistical_result=bad_result, associated_evidence=bad_evidence)
    bad_job = replace(job, analysis_outcomes=(bad_outcome, *job.analysis_outcomes[1:]))
    bad_batch = replace(batch, job_results=(bad_job, *batch.job_results[1:]))
    with pytest.raises(InvalidPublicationInput):
        retain_source(bad_batch, "invalid", tmp_path / "invalid.json")


def test_inputs_remain_unchanged_and_no_execution_on_read(published):
    batch, source, store, pid = published
    from market_research.publication.source import source_bytes

    before = source_bytes(batch, source.source_id)
    with (
        patch(
            "market_research.descriptive.execution.batch.execute_job", side_effect=AssertionError
        ),
        patch("market_research.descriptive.execution.api.compute", side_effect=AssertionError),
        patch(
            "market_research.descriptive.execution.api.prepare_inputs", side_effect=AssertionError
        ),
    ):
        manifest = store.get_publication_manifest(pid)
        first = manifest["analyses"][0]
        store.get_analysis(pid, first["analysis_id"])
        store.get_chart_view(pid, first["views"][0]["view_id"])
        publish(batch, source, "second snapshot", store)
    assert source_bytes(batch, source.source_id) == before


def test_unsupported_versioned_payload_and_bundle_symlink(published):
    _, _, store, pid = published
    manifest = store.get_publication_manifest(pid)
    aid = manifest["analyses"][0]["analysis_id"]
    env = envelope(store, pid)
    file = bundle(store, pid) / "analyses" / f"{aid}.json"
    data = json.loads(file.read_text())
    data["schema"] = "publication-analysis-v99"
    content = canonical_json(data)
    file.write_bytes(content)
    env["payloads"]["analyses"][aid] = {"sha256": digest(content), "size": len(content)}
    rewrite_envelope(store, pid, env)
    with pytest.raises(UnsupportedPublicationVersion):
        store.get_analysis(pid, aid)
    actual = bundle(store, pid)
    renamed = actual.with_name("moved")
    actual.rename(renamed)
    actual.symlink_to(renamed, target_is_directory=True)
    with pytest.raises(PublicationCorrupt):
        store.get_analysis(pid, aid)


def test_layer_must_match_retained_result_even_if_digest_is_rewritten(published):
    _, _, store, pid = published
    summary = store.get_publication_manifest(pid)["analyses"][0]
    ref = summary["views"][0]
    env = envelope(store, pid)
    path = bundle(store, pid) / "layers" / f"{ref['layer_id']}.json"
    value = json.loads(path.read_text())
    value["layer"]["data"][0]["y"] += 1
    raw = canonical_json(value)
    path.write_bytes(raw)
    env["payloads"]["layers"][ref["layer_id"]] = {"sha256": digest(raw), "size": len(raw)}
    rewrite_envelope(store, pid, env)
    with pytest.raises(InconsistentPublication, match="retained source result"):
        store.get_chart_view(pid, ref["view_id"])


def test_fresh_process_reopens_the_same_values(published):
    import subprocess
    import sys

    _, _, store, pid = published
    manifest = store.get_publication_manifest(pid)
    first = manifest["analyses"][0]
    expected = store.get_analysis(pid, first["analysis_id"])
    script = (
        "import json,sys; from market_research.publication import PublicationStore; "
        "s=PublicationStore(sys.argv[1]); "
        "print(json.dumps(s.get_analysis(sys.argv[2],sys.argv[3]),sort_keys=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(store.root), pid, first["analysis_id"]],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == expected


def test_navigation_is_sorted_bounded_and_read_only(published):
    batch, source, store, first_id = published
    ids = [
        first_id,
        publish(batch, source, "second", store),
        publish(batch, source, "third", store),
    ]
    ids.sort()
    assert [v["publication_id"] for v in store.list_publications(limit=2)] == ids[:2]
    assert [v["publication_id"] for v in store.list_publications(limit=2, after=ids[1])] == ids[2:]
    with pytest.raises(InvalidPublicationInput):
        store.list_publications(limit=0)


def test_unsupported_failure_is_not_silently_serialized(tmp_path, batch):
    class UnknownFailure(Exception):
        pass

    job = batch.job_results[1]
    old = job.failures[0]
    failure = replace(old, error=UnknownFailure("unsupported"))
    outcomes = tuple(
        replace(o, failure=failure) if o.failure is old else o for o in job.analysis_outcomes
    )
    changed_job = replace(job, failures=(failure,), analysis_outcomes=outcomes)
    changed = replace(
        batch, job_results=(batch.job_results[0], changed_job, *batch.job_results[2:])
    )
    with pytest.raises(InvalidPublicationInput, match="unsupported source type"):
        retain_source(changed, "source", tmp_path / "unknown.json")
