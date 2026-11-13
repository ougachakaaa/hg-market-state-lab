"""Local immutable publication snapshots and read-only granular access."""

import os
import uuid
from functools import wraps
from pathlib import Path
from typing import Any

from market_research.descriptive.execution import BatchResult

from ._paths import directories, path_value, regular, same
from ._records import (
    _analysis_id,
    _coverage_summary,
    _decode_result,
    _entry,
    _id,
    _json,
    _schema,
    _shape,
    _uuid,
    _validate_manifest,
    _verified,
    _verify_source_associations,
)
from ._sqlite import SQLiteStorage
from .errors import (
    InconsistentPublication,
    InvalidPublicationInput,
    PublicationCollision,
    PublicationCorrupt,
    PublicationNotFound,
    PublicationUnavailable,
    VerificationBudgetExceeded,
)
from .source import SourceReference, canonical_json, digest, encode, source_bytes
from .visualization import materialize, project, validate_layer


def _source(ref: SourceReference, expected: bytes) -> bytes:
    if (
        type(ref) is not SourceReference
        or type(ref.location) is not str
        or not os.path.isabs(ref.location)
    ):
        raise InvalidPublicationInput("invalid source reference")
    location = path_value(ref.location)
    try:
        directories(location.parent)
        before = regular(location)
        with location.open("rb") as stream:
            same(before, os.fstat(stream.fileno()))
            if before.st_size != len(expected):
                raise InconsistentPublication("source evidence size mismatch")
            data = stream.read(len(expected) + 1)
        same(before, regular(location))
    except OSError as exc:
        raise PublicationUnavailable("source evidence unavailable") from exc
    if (
        type(ref.size) is not int
        or type(ref.sha256) is not str
        or len(data) != ref.size
        or digest(data) != ref.sha256
        or data != expected
    ):
        raise InconsistentPublication("source evidence does not match the completed Batch")
    return data


def _snapshot(method: Any) -> Any:
    @wraps(method)
    def read(self: Any, *args: Any, **kwargs: Any) -> Any:
        with self._storage.connection():
            return method(self, *args, **kwargs)

    return read


class PublicationStore:
    """A configurable local store. Constructing it does not create or modify files."""

    def __init__(self, root: str | Path):
        self.root = path_value(root)
        self._storage = SQLiteStorage(self.root)

    def list_publications(
        self, *, limit: int = 50, after: str | None = None
    ) -> list[dict[str, Any]]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise InvalidPublicationInput("limit must be between 1 and 100")
        if after is not None:
            _uuid(after)
        with self._storage.connection() as connection:
            if connection is None:
                return []
            ids = connection.execute(
                (
                    "SELECT publication_id FROM publications WHERE publication_id > ? "
                    "ORDER BY publication_id LIMIT ?"
                ),
                (after or "", limit),
            ).fetchall()
            try:
                return [self._envelope(row[0], connection)["manifest"] for row in ids]
            except InvalidPublicationInput as exc:
                raise PublicationCorrupt("invalid stored publication identity") from exc

    def _envelope(self, publication_id: str, connection: Any = None) -> dict[str, Any]:
        _uuid(publication_id)
        if connection is None:
            with self._storage.connection() as opened:
                if opened is None:
                    raise PublicationNotFound("publication not found")
                return self._envelope(publication_id, opened)
        info = connection.execute(
            (
                "SELECT typeof(manifest), length(manifest), size, sha256, "
                "typeof(integrity) FROM publications WHERE publication_id=?"
            ),
            (publication_id,),
        ).fetchone()
        if info is None:
            raise PublicationNotFound("publication not found")
        if info[0] != "blob" or type(info[2]) is not int or info[1] != info[2] or info[4] != "blob":
            raise PublicationCorrupt("invalid manifest metadata")
        raw, integrity = connection.execute(
            "SELECT manifest, integrity FROM publications WHERE publication_id=?", (publication_id,)
        ).fetchone()
        _verified(raw, {"size": info[2], "sha256": info[3]})
        manifest, payloads = _json(raw), _json(integrity)
        _shape(payloads, {"source", "analyses", "views", "layers"}, "payload index")
        _validate_manifest(manifest, publication_id, payloads)
        return {"manifest": manifest, "payloads": payloads}

    def get_publication_manifest(self, publication_id: str) -> dict[str, Any]:
        return self._envelope(publication_id)["manifest"]

    def _payload(
        self,
        env: dict[str, Any],
        group: str,
        identity: str | None = None,
        *,
        source_limit: int | None = None,
    ) -> Any:
        if source_limit is not None and (type(source_limit) is not int or source_limit < 0):
            raise InvalidPublicationInput("invalid source byte budget")
        if group == "source":
            metadata = env["payloads"]["source"]
        else:
            assert identity is not None
            _id(identity)
            metadata = env["payloads"][group].get(identity)
            if metadata is None:
                raise InconsistentPublication("undeclared publication reference")
        with self._storage.connection() as connection:
            if connection is None:
                raise PublicationCorrupt("publication database disappeared")
            data = self._storage.blob(
                connection,
                env["manifest"]["publication_id"],
                group,
                identity or "",
                source_limit,
                metadata["size"],
            )
        _verified(data, metadata)
        return _json(data)

    def _check_source(
        self, env: dict[str, Any], source_limit: int | None = None
    ) -> dict[str, dict[str, Any]]:
        if source_limit is not None and (type(source_limit) is not int or source_limit < 0):
            raise InvalidPublicationInput("invalid source byte budget")
        if source_limit is not None and env["manifest"]["source"]["size"] > source_limit:
            raise VerificationBudgetExceeded("source verification capacity exceeded")
        source = self._payload(env, "source", source_limit=source_limit)
        _shape(source, {"schema", "source_id", "batch"}, "source")
        _schema(source, "research-source-v1")
        summary = env["manifest"]["source"]
        if source["source_id"] != summary["source_id"] or env["payloads"]["source"] != {
            "sha256": summary["sha256"],
            "size": summary["size"],
        }:
            raise InconsistentPublication("source association mismatch")
        try:
            return _verify_source_associations(source, env["manifest"])
        except (KeyError, TypeError, IndexError, StopIteration) as exc:
            raise PublicationCorrupt("malformed retained source evidence") from exc

    @_snapshot
    def get_analysis(
        self, publication_id: str, analysis_id: str, *, source_limit: int | None = None
    ) -> dict[str, Any]:
        _id(analysis_id)
        env = self._envelope(publication_id)
        summary = next(
            (a for a in env["manifest"]["analyses"] if a["analysis_id"] == analysis_id), None
        )
        if summary is None:
            raise PublicationNotFound("analysis not found")
        source_records = self._check_source(env, source_limit)
        payload = self._payload(env, "analyses", analysis_id)
        _shape(
            payload,
            {"schema", "publication_id", "summary", "result", "failure", "not_attempted_reason"},
            "analysis",
        )
        _schema(payload, "publication-analysis-v1")
        if payload["publication_id"] != publication_id or payload["summary"] != summary:
            raise InconsistentPublication("analysis association mismatch")
        source_outcome = source_records[analysis_id]["outcome"]
        if canonical_json(
            [payload["result"], payload["failure"], payload["not_attempted_reason"]]
        ) != canonical_json(
            [
                source_outcome["statistical_result"],
                source_outcome["failure"],
                source_outcome["not_attempted_reason"],
            ]
        ):
            raise InconsistentPublication("analysis differs from retained source evidence")
        if summary["status"] == "success" and (
            payload["result"] is None
            or payload["failure"] is not None
            or payload["not_attempted_reason"] is not None
        ):
            raise InconsistentPublication("invalid successful analysis")
        if summary["status"] != "success" and summary["views"]:
            raise InconsistentPublication("unsuccessful analysis has views")
        return {**payload, "coverage": _coverage_summary(source_records[analysis_id]["job"])}

    @_snapshot
    def get_chart_view(
        self, publication_id: str, chart_view_ref: str, *, source_limit: int | None = None
    ) -> dict[str, Any]:
        _id(chart_view_ref)
        env = self._envelope(publication_id)
        found = [
            (a, v)
            for a in env["manifest"]["analyses"]
            for v in a["views"]
            if v["view_id"] == chart_view_ref
        ]
        if not found:
            raise PublicationNotFound("chart view not found")
        if len(found) != 1:
            raise InconsistentPublication("duplicate view reference")
        analysis, ref = found[0]
        if analysis["status"] != "success":
            raise InconsistentPublication("view belongs to unsuccessful analysis")
        source_records = self._check_source(env, source_limit)
        definition = self._payload(env, "views", chart_view_ref)
        _shape(
            definition,
            {"schema", "publication_id", "analysis_id", "view_id", "layer_id", "measure"},
            "view definition",
        )
        _schema(definition, "publication-view-v1")
        expected = {
            "schema": "publication-view-v1",
            "publication_id": publication_id,
            "analysis_id": analysis["analysis_id"],
            **ref,
        }
        if definition != expected:
            raise InconsistentPublication("view association mismatch")
        layer_payload = self._payload(env, "layers", ref["layer_id"])
        _shape(
            layer_payload,
            {"schema", "publication_id", "analysis_id", "layer_id", "measure", "layer"},
            "layer",
        )
        _schema(layer_payload, "publication-layer-v1")
        expected_layer = {
            "schema": "publication-layer-v1",
            "publication_id": publication_id,
            "analysis_id": analysis["analysis_id"],
            "layer_id": ref["layer_id"],
            "measure": ref["measure"],
        }
        if {k: v for k, v in layer_payload.items() if k != "layer"} != expected_layer:
            raise InconsistentPublication("layer association mismatch")
        try:
            validate_layer(layer_payload["layer"])
            source_result = _decode_result(
                source_records[analysis["analysis_id"]]["outcome"]["statistical_result"]
            )
            expected_layer = project(source_result)[ref["measure"]]
            if canonical_json(layer_payload["layer"]) != canonical_json(expected_layer):
                raise InconsistentPublication("visualization differs from retained source result")
            return materialize(layer_payload["layer"], analysis["analysis_id"])
        except InvalidPublicationInput as exc:
            raise PublicationCorrupt("invalid stored visualization") from exc


def publish(
    batch: BatchResult,
    source: SourceReference,
    context: str,
    store: PublicationStore,
    *,
    publication_id: str | None = None,
) -> str:
    """Publish a retained completed Batch without execution or numerical recomputation."""
    if type(context) is not str or not context:
        raise InvalidPublicationInput("publication context must be a nonempty string")
    if type(store) is not PublicationStore or type(source) is not SourceReference:
        raise InvalidPublicationInput("expected PublicationStore and SourceReference")
    pid = _uuid(publication_id) if publication_id is not None else uuid.uuid4().hex
    retained = _source(source, source_bytes(batch, source.source_id))
    payloads: dict[str, Any] = {
        "source": _entry(retained),
        "analyses": {},
        "views": {},
        "layers": {},
    }
    content: dict[str, dict[str, bytes]] = {"analyses": {}, "views": {}, "layers": {}}
    analyses: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    for job in batch.job_results:
        identity = encode(job.job_identity)
        job_ids = []
        for outcome in job.analysis_outcomes:
            spec = encode(outcome.spec)
            aid = _analysis_id(source.source_id, identity, outcome.request_id, spec)
            if aid in payloads["analyses"]:
                raise PublicationCollision("duplicate or colliding analysis identity")
            views = []
            if outcome.status == "success":
                assert outcome.statistical_result is not None
                for measure, layer in project(outcome.statistical_result).items():
                    vid = digest(canonical_json(["view-v1", pid, aid, measure]))
                    lid = digest(canonical_json(["layer-v1", pid, aid, measure]))
                    ref = {"view_id": vid, "layer_id": lid, "measure": measure}
                    views.append(ref)
                    layer_data = canonical_json(
                        {
                            "schema": "publication-layer-v1",
                            "publication_id": pid,
                            "analysis_id": aid,
                            "layer_id": lid,
                            "measure": measure,
                            "layer": layer,
                        }
                    )
                    view_data = canonical_json(
                        {
                            "schema": "publication-view-v1",
                            "publication_id": pid,
                            "analysis_id": aid,
                            **ref,
                        }
                    )
                    content["layers"][lid], content["views"][vid] = layer_data, view_data
                    payloads["layers"][lid], payloads["views"][vid] = (
                        _entry(layer_data),
                        _entry(view_data),
                    )
            summary = {
                "analysis_id": aid,
                "job_identity": identity,
                "request_id": outcome.request_id,
                "spec": spec,
                "status": outcome.status,
                "source_id": source.source_id,
                "views": views,
            }
            analysis = canonical_json(
                {
                    "schema": "publication-analysis-v1",
                    "publication_id": pid,
                    "summary": summary,
                    "result": encode(outcome.statistical_result),
                    "failure": encode(outcome.failure),
                    "not_attempted_reason": outcome.not_attempted_reason,
                }
            )
            analyses.append(summary)
            job_ids.append(aid)
            content["analyses"][aid] = analysis
            payloads["analyses"][aid] = _entry(analysis)
        jobs.append(
            {
                "job_identity": identity,
                "status": job.status,
                "failures": [
                    {
                        "failure_stage": failure.failure_stage,
                        "failure_category": failure.failure_category,
                        "reason": failure.reason,
                        "request_id": failure.request_id,
                    }
                    for failure in job.failures
                ],
                "skip_reason": job.skip_reason,
                "triggering_failed_job_identity": encode(job.triggering_failed_job_identity),
                "analyses": job_ids,
            }
        )
    manifest = {
        "schema": "publication-manifest-v1",
        "publication_id": pid,
        "context": context,
        "scope": encode(batch.plan),
        "status": batch.status,
        "source": {
            "source_id": source.source_id,
            "location": source.location,
            "sha256": source.sha256,
            "size": source.size,
        },
        "jobs": jobs,
        "analyses": analyses,
    }
    _validate_manifest(manifest, pid, payloads)
    # Validate all source associations before a short immutable write transaction.
    _verify_source_associations(_json(retained), manifest)
    raw = canonical_json(manifest)
    with store._storage.connection(write=True) as connection:
        assert connection is not None
        connection.execute(
            "INSERT INTO publications VALUES (?,?,?,?,?)",
            (pid, raw, digest(raw), len(raw), canonical_json(payloads)),
        )
        connection.execute("INSERT INTO records VALUES (?,?,?,?)", (pid, "source", "", retained))
        for group, objects in content.items():
            for identity, data in objects.items():
                connection.execute(
                    "INSERT INTO records VALUES (?,?,?,?)", (pid, group, identity, data)
                )
    return pid
