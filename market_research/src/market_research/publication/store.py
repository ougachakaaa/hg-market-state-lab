"""Local immutable publication snapshots and read-only granular access."""

import errno
import json
import math
import os
import re
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from market_research.descriptive.execution import BatchResult
from market_statistics import IntervalBin, IntervalCountResult, QuantileResult

from .errors import (
    InconsistentPublication,
    InvalidPublicationInput,
    PublicationCollision,
    PublicationCorrupt,
    PublicationNotFound,
    PublicationUnavailable,
    UnsupportedPublicationVersion,
    VerificationBudgetExceeded,
)
from .source import SourceReference, canonical_json, digest, encode, source_bytes
from .visualization import materialize, project, validate_layer

_ID = re.compile(r"[0-9a-f]{64}\Z")
_UUID = re.compile(r"[0-9a-f]{32}\Z")
_DIR = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def _uuid(value: object) -> str:
    if type(value) is not str or not _UUID.fullmatch(value):
        raise InvalidPublicationInput("invalid publication identity")
    try:
        if uuid.UUID(hex=value).version != 4:
            raise ValueError
    except ValueError as exc:
        raise InvalidPublicationInput("publication identity must be a UUID4 hex") from exc
    return value


def _id(value: object) -> str:
    if type(value) is not str or not _ID.fullmatch(value):
        raise InvalidPublicationInput("invalid publication-local reference")
    return value


def _json(data: bytes) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    def finite_float(text: str) -> float:
        value = float(text)
        if not math.isfinite(value):
            raise ValueError("non-finite JSON number")
        return value

    try:
        return json.loads(
            data,
            parse_float=finite_float,
            object_pairs_hook=pairs,
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise PublicationCorrupt("invalid JSON") from exc


def _shape(obj: Any, keys: set[str], description: str) -> dict[str, Any]:
    if type(obj) is not dict or set(obj) != keys:
        raise PublicationCorrupt(f"invalid {description} structure")
    return obj


def _schema(obj: dict[str, Any], expected: str) -> None:
    if obj.get("schema") != expected:
        raise UnsupportedPublicationVersion(f"unsupported {expected} schema")


@contextmanager
def _directory(parent: int, name: str) -> Iterator[int]:
    try:
        fd = os.open(name, _DIR, dir_fd=parent)
    except FileNotFoundError as exc:
        raise PublicationCorrupt(f"missing directory {name}") from exc
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise PublicationCorrupt(f"invalid directory {name}") from exc
        raise PublicationUnavailable(f"cannot open directory {name}") from exc
    try:
        yield fd
    finally:
        os.close(fd)


def _mkdir(parent: int, name: str) -> None:
    try:
        os.mkdir(name, mode=0o700, dir_fd=parent)
    except FileExistsError:
        with _directory(parent, name):
            pass


def _read(parent: int, name: str, limit: int | None = None) -> bytes:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise PublicationCorrupt(f"not a regular file: {name}")
            if limit is not None and os.fstat(stream.fileno()).st_size > limit:
                raise VerificationBudgetExceeded("source verification capacity exceeded")
            data = stream.read() if limit is None else stream.read(limit + 1)
            if limit is not None and len(data) > limit:
                raise VerificationBudgetExceeded("source verification capacity exceeded")
            return data
    except FileNotFoundError as exc:
        raise PublicationCorrupt(f"missing file: {name}") from exc
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            raise PublicationCorrupt(f"invalid file: {name}") from exc
        raise PublicationUnavailable(f"cannot read file: {name}") from exc


def _write(parent: int, name: str, content: bytes) -> None:
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _entry(data: bytes) -> dict[str, Any]:
    return {"sha256": digest(data), "size": len(data)}


def _verified(data: bytes, metadata: object) -> None:
    info = _shape(metadata, {"sha256", "size"}, "integrity entry")
    if (
        type(info["sha256"]) is not str
        or not _ID.fullmatch(info["sha256"])
        or type(info["size"]) is not int
        or info["size"] < 0
    ):
        raise PublicationCorrupt("invalid integrity entry")
    if len(data) != info["size"] or digest(data) != info["sha256"]:
        raise PublicationCorrupt("content integrity mismatch")


def _source(ref: SourceReference, expected: bytes) -> bytes:
    if (
        type(ref) is not SourceReference
        or type(ref.location) is not str
        or not os.path.isabs(ref.location)
    ):
        raise InvalidPublicationInput("invalid source reference")
    try:
        fd = os.open(ref.location, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise PublicationUnavailable("source is not a regular file")
            data = stream.read()
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


class PublicationStore:
    """A configurable local store. Constructing it does not create or modify files."""

    def __init__(self, root: str | Path):
        raw = os.fspath(root)
        if not raw or "\x00" in raw or ".." in Path(raw).parts:
            raise InvalidPublicationInput("invalid publication store path")
        self.root = Path(raw).absolute()

    @contextmanager
    def _existing_root(self) -> Iterator[int | None]:
        """Open every existing component without following symlinks; never create paths."""
        try:
            fd = os.open(self.root.anchor, _DIR)
        except OSError as exc:
            raise PublicationUnavailable("publication store path unavailable") from exc
        try:
            for part in self.root.parts[1:]:
                try:
                    child = os.open(part, _DIR, dir_fd=fd)
                except FileNotFoundError:
                    yield None
                    return
                except OSError as exc:
                    if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                        raise PublicationCorrupt("invalid or symlink store path") from exc
                    raise PublicationUnavailable("publication store path unavailable") from exc
                os.close(fd)
                fd = child
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def _index(self) -> Iterator[int | None]:
        """Inspect one read-only snapshot of the index initialization state."""
        with self._existing_root() as root:
            if root is None:
                yield None
                return
            try:
                names = set(os.listdir(root))
            except OSError as exc:
                raise PublicationUnavailable("cannot inspect publication store") from exc
            if "publications" not in names:
                if names - {"bundles"}:
                    raise PublicationCorrupt("invalid uninitialized store structure")
                if "bundles" in names:
                    with _directory(root, "bundles"):
                        pass
                yield None
                return
            if "bundles" not in names:
                raise PublicationCorrupt("publication store has no bundles directory")
            with _directory(root, "bundles"), _directory(root, "publications") as pubs:
                yield pubs

    @contextmanager
    def _root(self, *, create: bool = False) -> Iterator[int]:
        if not create:
            with self._existing_root() as fd:
                if fd is None:
                    raise PublicationUnavailable("publication store unavailable")
                yield fd
            return
        try:
            fd = os.open(self.root.anchor, _DIR)
        except OSError as exc:
            raise PublicationUnavailable("publication store unavailable") from exc
        try:
            for part in self.root.parts[1:]:
                try:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                    child = os.open(part, _DIR, dir_fd=fd)
                except OSError as exc:
                    if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                        raise PublicationCorrupt("invalid or symlink store path") from exc
                    raise PublicationUnavailable("publication store unavailable") from exc
                os.close(fd)
                fd = child
            yield fd
        finally:
            os.close(fd)

    def list_publications(
        self, *, limit: int = 50, after: str | None = None
    ) -> list[dict[str, Any]]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise InvalidPublicationInput("limit must be between 1 and 100")
        if after is not None:
            _uuid(after)
        with self._index() as pubs:
            if pubs is None:
                return []
            try:
                names = []
                for name in os.listdir(pubs):
                    if re.fullmatch(r"[0-9a-f]{32}\.json", name):
                        try:
                            _uuid(name[:-5])
                        except InvalidPublicationInput as exc:
                            raise PublicationCorrupt("invalid publication filename") from exc
                        try:
                            mode = os.stat(name, dir_fd=pubs, follow_symlinks=False).st_mode
                        except FileNotFoundError as exc:
                            raise PublicationCorrupt("publication entry disappeared") from exc
                        if not stat.S_ISREG(mode):
                            raise PublicationCorrupt("invalid publication file")
                        names.append(name[:-5])
                    elif re.fullmatch(r"\.tmp-[0-9a-f]{32}", name):
                        try:
                            _uuid(name[5:])
                            mode = os.stat(name, dir_fd=pubs, follow_symlinks=False).st_mode
                        except FileNotFoundError:
                            # An in-progress publisher may have removed its temporary name.
                            continue
                        except InvalidPublicationInput as exc:
                            raise PublicationCorrupt("invalid staging filename") from exc
                        if not stat.S_ISREG(mode):
                            raise PublicationCorrupt("invalid staging file")
                    else:
                        raise PublicationCorrupt("unexpected publication index entry")
                names.sort()
            except OSError as exc:
                raise PublicationUnavailable("cannot list publications") from exc
        selected = [name for name in names if after is None or name > after][:limit]
        return [self.get_publication_manifest(name) for name in selected]

    def _envelope(self, publication_id: str) -> dict[str, Any]:
        _uuid(publication_id)
        try:
            with self._index() as pubs:
                if pubs is None:
                    raise PublicationNotFound("publication not found")
                try:
                    raw = _read(pubs, f"{publication_id}.json")
                except PublicationCorrupt as exc:
                    try:
                        os.stat(f"{publication_id}.json", dir_fd=pubs, follow_symlinks=False)
                    except FileNotFoundError:
                        raise PublicationNotFound("publication not found") from exc
                    except OSError as stat_error:
                        raise PublicationUnavailable("cannot inspect publication") from stat_error
                    raise
        except PublicationCorrupt:
            raise
        envelope = _shape(
            _json(raw), {"schema", "manifest", "manifest_sha256", "bundle", "payloads"}, "envelope"
        )
        _schema(envelope, "publication-envelope-v1")
        manifest = envelope["manifest"]
        if digest(canonical_json(manifest)) != envelope["manifest_sha256"]:
            raise PublicationCorrupt("manifest integrity mismatch")
        try:
            _uuid(envelope["bundle"])
        except InvalidPublicationInput as exc:
            raise PublicationCorrupt("invalid bundle identity") from exc
        _shape(envelope["payloads"], {"source", "analyses", "views", "layers"}, "payload index")
        _validate_manifest(manifest, publication_id, envelope["payloads"])
        return envelope

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
        with (
            self._root() as root,
            _directory(root, "bundles") as bundles,
            _directory(bundles, env["bundle"]) as bundle,
        ):
            if group == "source":
                data = (
                    _read(bundle, "source.json")
                    if source_limit is None
                    else _read(bundle, "source.json", source_limit)
                )
                metadata = env["payloads"]["source"]
            else:
                assert identity is not None
                _id(identity)
                metadata = env["payloads"][group].get(identity)
                if metadata is None:
                    raise InconsistentPublication(f"undeclared {group} reference")
                with _directory(bundle, group) as directory:
                    data = _read(directory, f"{identity}.json")
        _verified(data, metadata)
        return _json(data)

    def _check_source(
        self, env: dict[str, Any], source_limit: int | None = None
    ) -> dict[str, dict[str, Any]]:
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


def _carrier(value: object, type_name: str) -> dict[str, Any]:
    obj = _shape(value, {"$type", "fields"}, f"{type_name} source carrier")
    if obj["$type"] != type_name or type(obj["fields"]) is not dict:
        raise InconsistentPublication(f"wrong {type_name} source carrier")
    return obj["fields"]


def _tuple(value: object) -> list[Any]:
    obj = _shape(value, {"$tuple"}, "source tuple")
    if type(obj["$tuple"]) is not list:
        raise PublicationCorrupt("invalid source tuple")
    return obj["$tuple"]


def _coverage_summary(job: dict[str, Any]) -> dict[str, Any] | None:
    if "observation_set" not in job:
        raise PublicationCorrupt("missing observation context")
    if job["observation_set"] is None:
        return None
    try:
        obs = _carrier(job["observation_set"], "ObservationSet")
        if obs["job_identity"] != job["job_identity"]:
            raise InconsistentPublication("observation identity mismatch")
        counts = [
            len(_tuple(obs[k]))
            for k in (
                "candidate_anchors",
                "eligible_observations",
                "unavailable_observations",
                "excluded_observations",
            )
        ]
        candidate, eligible, unavailable, excluded = counts
        if candidate != eligible + unavailable + excluded:
            raise InconsistentPublication("observation population mismatch")
        market = _carrier(obs["market_fact_coverage"], "MarketFactCoverage")
        facts = {}
        for name in ("overall", "warm_up", "sample"):
            part = _carrier(market[name], "FactCoverage")
            expected, available = (
                len(_tuple(part[k])) for k in ("expected_keys", "available_keys")
            )
            if available > expected:
                raise InconsistentPublication("fact coverage mismatch")
            facts[name] = {
                "expected_fact_count": expected,
                "available_fact_count": available,
                "coverage_ratio": available / expected if expected else None,
            }
        definition = _carrier(obs["observation_definition"], "ObservationDefinition")
        provenance = _carrier(obs["provenance"], "TrailingReturnProvenance")
        unit, profile, fingerprint = (
            definition["unit"],
            provenance["input_profile"],
            provenance["input_fingerprint"],
        )
        if (
            unit != "decimal_ratio"
            or profile != "trailing_return_inputs_v2"
            or not isinstance(fingerprint, str)
            or not _ID.fullmatch(fingerprint)
        ):
            raise InconsistentPublication("invalid coverage provenance")
        return {
            "candidate_count": candidate,
            "eligible_count": eligible,
            "unavailable_count": unavailable,
            "excluded_count": excluded,
            "observation_coverage": eligible / candidate if candidate else None,
            "unavailable_ratio": unavailable / candidate if candidate else None,
            "excluded_ratio": excluded / candidate if candidate else None,
            "market_facts": facts,
            "observation_unit": unit,
            "input_profile": profile,
            "input_fingerprint": fingerprint,
        }
    except (KeyError, TypeError, IndexError) as exc:
        raise PublicationCorrupt("malformed observation coverage") from exc


def _verify_source_associations(
    source: dict[str, Any], manifest: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    batch = _carrier(source["batch"], "BatchResult")
    if batch.get("plan") != manifest["scope"]:
        raise InconsistentPublication("manifest scope differs from retained source")
    jobs = _tuple(batch.get("job_results"))
    if len(jobs) != len(manifest["jobs"]):
        raise InconsistentPublication("source job count mismatch")
    records: dict[str, dict[str, Any]] = {}
    statuses = []
    for encoded_job, summary_job in zip(jobs, manifest["jobs"], strict=True):
        job = _carrier(encoded_job, "JobResult")
        for field in (
            "job_identity",
            "status",
            "skip_reason",
            "triggering_failed_job_identity",
        ):
            if job.get(field) != summary_job[field]:
                raise InconsistentPublication("source job association mismatch")
        if job.get("projection") is not None:
            projection = _carrier(job["projection"], "SampleProjection")
            binding = _carrier(projection.get("binding"), "SampleBinding")
            if job.get("observation_set") is None or (
                binding.get("source_observation_reference") != job["observation_set"]
            ):
                raise InconsistentPublication("projection observation association mismatch")
        elif job["status"] == "Success":
            raise InconsistentPublication("successful job missing projection")
        failure_summaries = []
        for encoded_failure in _tuple(job.get("failures")):
            failure = _carrier(encoded_failure, "FailureRecord")
            failure_summaries.append(
                {
                    key: failure.get(key)
                    for key in ("failure_stage", "failure_category", "reason", "request_id")
                }
            )
        if failure_summaries != summary_job["failures"]:
            raise InconsistentPublication("source job failure association mismatch")
        statuses.append(job["status"])
        outcomes = _tuple(job.get("analysis_outcomes"))
        if len(outcomes) != len(summary_job["analyses"]):
            raise InconsistentPublication("source outcome count mismatch")
        for encoded_outcome, aid in zip(outcomes, summary_job["analyses"], strict=True):
            outcome = _carrier(encoded_outcome, "AnalysisOutcome")
            request = _carrier(outcome.get("request"), "AnalysisRequest")
            summary = next(a for a in manifest["analyses"] if a["analysis_id"] == aid)
            if (
                request.get("request_id") != summary["request_id"]
                or request.get("spec") != summary["spec"]
                or outcome.get("status") != summary["status"]
            ):
                raise InconsistentPublication("source request or outcome association mismatch")
            if outcome["status"] == "success":
                evidence = _carrier(outcome.get("associated_evidence"), "ResearchAnalysisEvidence")
                if (
                    evidence.get("request") != outcome["request"]
                    or evidence.get("statistical_result") != outcome["statistical_result"]
                    or evidence.get("projection") != job.get("projection")
                ):
                    raise InconsistentPublication("source successful evidence mismatch")
            records[aid] = {"outcome": outcome, "job": job}
    actual_status = (
        "success"
        if "Failed" not in statuses
        else ("partial_success" if "Success" in statuses else "failed")
    )
    if actual_status != manifest["status"]:
        raise InconsistentPublication("source batch status mismatch")
    return records


def _decode_result(value: object) -> QuantileResult | IntervalCountResult:
    """Read only the two explicit result variants; never dynamically import types."""
    try:
        obj = _shape(value, {"$type", "fields"}, "statistical result")
        if obj["$type"] == "QuantileResult":
            fields = _shape(
                obj["fields"],
                {"method", "estimator", "points_and_values", "sample_count", "unit"},
                "quantile result",
            )
            pairs = tuple(tuple(_tuple(pair)) for pair in _tuple(fields["points_and_values"]))
            if (
                fields["method"] != "quantile"
                or fields["estimator"] != "type7_linear_v1"
                or any(len(pair) != 2 for pair in pairs)
            ):
                raise PublicationCorrupt("invalid retained quantile result")
            return QuantileResult(pairs, fields["sample_count"], fields["unit"])
        if obj["$type"] == "IntervalCountResult":
            fields = _shape(
                obj["fields"],
                {
                    "method",
                    "edges",
                    "bins",
                    "underflow_count",
                    "overflow_count",
                    "underflow_frequency",
                    "overflow_frequency",
                    "sample_count",
                    "unit",
                },
                "interval result",
            )
            if fields["method"] != "interval_count":
                raise PublicationCorrupt("invalid retained interval result")
            bins = []
            for encoded in _tuple(fields["bins"]):
                data = _carrier(encoded, "IntervalBin")
                _shape(
                    data,
                    {"left", "right", "left_inclusive", "right_inclusive", "count", "frequency"},
                    "interval bin",
                )
                bins.append(IntervalBin(**data))
            return IntervalCountResult(
                tuple(_tuple(fields["edges"])),
                tuple(bins),
                fields["underflow_count"],
                fields["overflow_count"],
                fields["underflow_frequency"],
                fields["overflow_frequency"],
                fields["sample_count"],
                fields["unit"],
            )
        raise UnsupportedPublicationVersion("unsupported statistical result")
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise PublicationCorrupt("malformed retained statistical result") from exc


def _analysis_id(source_id: str, job_identity: Any, request_id: str, spec: Any) -> str:
    return digest(canonical_json(["analysis-v1", source_id, job_identity, request_id, spec]))


def _validate_manifest(manifest: object, publication_id: str, payloads: dict[str, Any]) -> None:
    m = _shape(
        manifest,
        {"schema", "publication_id", "context", "scope", "status", "source", "jobs", "analyses"},
        "manifest",
    )
    _schema(m, "publication-manifest-v1")
    if m["publication_id"] != publication_id or type(m["context"]) is not str or not m["context"]:
        raise InconsistentPublication("publication identity/context mismatch")
    if (
        m["status"] not in ("success", "partial_success", "failed")
        or type(m["jobs"]) is not list
        or type(m["analyses"]) is not list
    ):
        raise PublicationCorrupt("invalid manifest status or lists")
    source = _shape(m["source"], {"source_id", "location", "sha256", "size"}, "source reference")
    if (
        type(source["source_id"]) is not str
        or not source["source_id"]
        or type(source["location"]) is not str
        or not os.path.isabs(source["location"])
    ):
        raise PublicationCorrupt("invalid source reference")
    if (
        type(source["sha256"]) is not str
        or not _ID.fullmatch(source["sha256"])
        or type(source["size"]) is not int
        or source["size"] < 0
        or payloads["source"] != {"sha256": source["sha256"], "size": source["size"]}
    ):
        raise InconsistentPublication("invalid source integrity reference")
    for group in ("analyses", "views", "layers"):
        if type(payloads[group]) is not dict or any(
            not isinstance(key, str) or not _ID.fullmatch(key) for key in payloads[group]
        ):
            raise PublicationCorrupt("invalid payload index")
    seen_analyses: set[str] = set()
    seen_views: set[str] = set()
    seen_layers: set[str] = set()
    for summary in m["analyses"]:
        _shape(
            summary,
            {"analysis_id", "job_identity", "request_id", "spec", "status", "source_id", "views"},
            "analysis summary",
        )
        aid = summary["analysis_id"]
        if not isinstance(aid, str) or not _ID.fullmatch(aid) or aid in seen_analyses:
            raise PublicationCorrupt("invalid or duplicate analysis identity")
        if (
            type(summary["request_id"]) is not str
            or not summary["request_id"]
            or summary["source_id"] != source["source_id"]
        ):
            raise InconsistentPublication("invalid analysis source/request")
        if aid != _analysis_id(
            source["source_id"], summary["job_identity"], summary["request_id"], summary["spec"]
        ):
            raise InconsistentPublication("analysis identity mismatch")
        if (
            summary["status"] not in ("success", "failed", "not_attempted")
            or type(summary["views"]) is not list
        ):
            raise PublicationCorrupt("invalid analysis status/views")
        seen_analyses.add(aid)
        for view in summary["views"]:
            _shape(view, {"view_id", "layer_id", "measure"}, "view reference")
            vid, lid, measure = view["view_id"], view["layer_id"], view["measure"]
            if (
                measure not in ("quantile", "count", "frequency")
                or vid != digest(canonical_json(["view-v1", publication_id, aid, measure]))
                or lid != digest(canonical_json(["layer-v1", publication_id, aid, measure]))
                or vid in seen_views
                or lid in seen_layers
            ):
                raise InconsistentPublication("invalid or duplicate view identity")
            seen_views.add(vid)
            seen_layers.add(lid)
        if summary["status"] != "success" and summary["views"]:
            raise InconsistentPublication("unsuccessful analysis has a view")
        spec = _shape(summary["spec"], {"$type", "fields"}, "statistical spec")
        if spec["$type"] not in ("QuantileSpec", "IntervalCountSpec"):
            raise UnsupportedPublicationVersion("unsupported statistical spec")
        expected_measures = (
            ["quantile"] if spec["$type"] == "QuantileSpec" else ["count", "frequency"]
        )
        if (
            summary["status"] == "success"
            and [v["measure"] for v in summary["views"]] != expected_measures
        ):
            raise InconsistentPublication("successful analysis projections are incomplete")
    if (
        seen_analyses != set(payloads["analyses"])
        or seen_views != set(payloads["views"])
        or seen_layers != set(payloads["layers"])
    ):
        raise InconsistentPublication("manifest and payload index disagree")
    linked: list[str] = []
    for job in m["jobs"]:
        _shape(
            job,
            {
                "job_identity",
                "status",
                "failures",
                "skip_reason",
                "triggering_failed_job_identity",
                "analyses",
            },
            "job summary",
        )
        if (
            job["status"] not in ("Success", "Failed", "Skipped")
            or type(job["analyses"]) is not list
        ):
            raise PublicationCorrupt("invalid job summary")
        for aid in job["analyses"]:
            matches = [
                a
                for a in m["analyses"]
                if a["analysis_id"] == aid and a["job_identity"] == job["job_identity"]
            ]
            if len(matches) != 1:
                raise InconsistentPublication("job/analysis association mismatch")
            linked.append(aid)
    if len(linked) != len(seen_analyses) or set(linked) != seen_analyses:
        raise InconsistentPublication("incomplete job/analysis associations")


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
    bundle_id = uuid.uuid4().hex
    env = {
        "schema": "publication-envelope-v1",
        "manifest": manifest,
        "manifest_sha256": digest(canonical_json(manifest)),
        "bundle": bundle_id,
        "payloads": payloads,
    }
    try:
        # Do not turn an already malformed root into an apparently valid store.
        with store._index():
            pass
        with store._root(create=True) as root:
            _mkdir(root, "bundles")
            _mkdir(root, "publications")
            with _directory(root, "bundles") as bundles, _directory(root, "publications") as pubs:
                os.mkdir(bundle_id, 0o700, dir_fd=bundles)
                with _directory(bundles, bundle_id) as bundle:
                    _write(bundle, "source.json", retained)
                    for group, objects in content.items():
                        os.mkdir(group, 0o700, dir_fd=bundle)
                        with _directory(bundle, group) as directory:
                            for identity, raw in objects.items():
                                _write(directory, f"{identity}.json", raw)
                temp = f".tmp-{uuid.uuid4().hex}"
                _write(pubs, temp, canonical_json(env))
                try:
                    os.link(
                        temp, f"{pid}.json", src_dir_fd=pubs, dst_dir_fd=pubs, follow_symlinks=False
                    )
                finally:
                    os.unlink(temp, dir_fd=pubs)
    except FileExistsError as exc:
        raise PublicationCollision("publication identity already exists") from exc
    except OSError as exc:
        raise PublicationUnavailable("cannot atomically commit publication") from exc
    return pid
