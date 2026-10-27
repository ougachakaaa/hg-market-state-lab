"""Explicit LIVE-E2E-01 harness; never collected by ordinary pytest.

Run from the repository root with --live --output <JSON evidence file>.
Private imports below configure/audit Dataset composition only. Facts are obtained
exclusively by the unmodified public Research and Dataset operations.
"""

import argparse
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
from collections import Counter
from contextlib import ExitStack, contextmanager
from dataclasses import fields, is_dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from data_lake import OperationError
from data_lake.adapters.outbound.sqlite import SCHEMA_VERSION, Repository
from data_lake.datasets.tushare_index_daily import _composition as index_composition
from data_lake.datasets.tushare_index_daily import create_service as index_service
from data_lake.datasets.tushare_trade_calendar import _composition as calendar_composition
from data_lake.datasets.tushare_trade_calendar import create_service as calendar_service
from data_lake.providers.tushare import TushareExecutor
from data_lake.providers.tushare._executor import request_interval, resolve_credential
from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.execution import ResearchPlan, execute_batch, execute_job
from market_research.descriptive.observation import DateWindow, ObservationJobSpec
from market_statistics import IntervalCountResult, IntervalCountSpec, QuantileResult, QuantileSpec

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ("tushare_trade_calendar", "tushare_index_daily")
WINDOW = DateWindow(date(2024, 1, 10), date(2024, 1, 16))


class IsolationError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def public(value: Any) -> Any:
    """Serialize selected public carriers, without exception chains or private paths."""
    if isinstance(value, date):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: public(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [public(item) for item in value]
    if isinstance(value, dict):
        return {key: public(item) for key, item in value.items()}
    return value


def default_state() -> dict[str, tuple[int, int]]:
    """Only stat default storage files; never open an existing user database."""
    result = {}
    for dataset in DATASETS:
        directory = ROOT / "data_lake" / "datasets" / dataset / "data"
        for path in directory.glob("*"):
            if path.is_file():
                stat = path.stat()
                result[str(path.relative_to(ROOT))] = (stat.st_size, stat.st_mtime_ns)
    return result


@contextmanager
def isolated_storage(root: Path):
    """Redirect both owning roots, including every implicit Calendar factory."""
    root = root.resolve()
    if root == ROOT or ROOT in root.parents or not root.is_dir() or any(root.iterdir()):
        raise IsolationError("Live Gate Blocked - Isolation not established")
    paths = {dataset: root / f"{dataset}.sqlite3" for dataset in DATASETS}
    constructed: list[str] = []
    connected: list[str] = []
    original_init = Repository.__init__
    original_connect = sqlite3.connect
    before = default_state()

    def location(dataset: str, storage_root: Path) -> Path:
        if dataset not in paths:
            raise IsolationError("Unexpected Dataset storage identity")
        return paths[dataset]

    def checked_init(self, path, dataset, source):
        if dataset not in paths or Path(path).resolve() != paths[dataset]:
            raise IsolationError("Repository escaped isolated Dataset storage")
        constructed.append(dataset)
        original_init(self, path, dataset, source)

    def checked_connect(database, *args, **kwargs):
        text = os.fspath(database)
        if text.startswith("file:"):
            text = unquote(urlsplit(text).path)
            if os.name == "nt" and text.startswith("/"):
                text = text[1:]
        target = Path(text).resolve()
        if target not in paths.values():
            raise IsolationError("SQLite connection escaped isolated Dataset storage")
        connected.append(target.name)
        return original_connect(database, *args, **kwargs)

    with ExitStack() as stack:
        stack.enter_context(patch.object(calendar_composition, "database_path", location))
        stack.enter_context(patch.object(index_composition, "database_path", location))
        stack.enter_context(patch.object(Repository, "__init__", checked_init))
        stack.enter_context(patch.object(sqlite3, "connect", checked_connect))
        calendar = cast(Any, calendar_service())
        index = cast(Any, index_service())
        require(calendar._core._repository.path == paths[DATASETS[0]], "Calendar isolation")
        require(index._repository.path == paths[DATASETS[1]], "Index isolation")
        require(
            index._calendar._core._repository.path == paths[DATASETS[0]], "Dependency isolation"
        )
        require(not any(root.iterdir()), "Factories must not materialize storage")
        audit: dict[str, Any] = {
            "established_before_source": True,
            "fresh_external_temporary_directory": True,
            "separate_dataset_files": True,
            "index_calendar_dependency_isolated": True,
            "factory_storage_free": True,
            "runtime_schema_generation": SCHEMA_VERSION,
        }
        try:
            yield audit
        finally:
            audit["repository_bindings"] = dict(Counter(constructed))
            audit["sqlite_connections"] = dict(Counter(connected))
            audit["materialized_files"] = sorted(p.name for p in root.iterdir())
            audit["default_cache_metadata_unchanged"] = before == default_state()
            require(audit["default_cache_metadata_unchanged"], "Default cache metadata changed")


def check_statistics(values, outcomes) -> None:
    """Independent Python oracle; no Statistics compute or NumPy call."""
    ordered = sorted(values)
    for outcome in outcomes:
        result, spec = outcome.statistical_result, outcome.request.spec
        require(result.sample_count == len(values), "Statistics sample count")
        require(result.unit == "decimal_ratio", "Statistics unit")
        if isinstance(result, QuantileResult):
            require(result.estimator == "type7_linear_v1", "Quantile estimator")
            expected = []
            for point in spec.points:
                h = (len(values) - 1) * point
                j = int(h)
                g = h - j
                value = ordered[j] if g == 0 else ordered[j] + g * (ordered[j + 1] - ordered[j])
                expected.append((point, value))
            require(result.points_and_values == tuple(expected), "Independent Type 7 quantiles")
        else:
            require(isinstance(result, IntervalCountResult), "Interval result variant")
            require(result.edges == spec.edges, "Interval edges")
            require(len(result.bins) == len(spec.edges) - 1, "Interval geometry")
            for i, item in enumerate(result.bins):
                left, right = spec.edges[i : i + 2]
                final = i == len(result.bins) - 1
                count = sum(left <= x and (x <= right if final else x < right) for x in values)
                require((item.left, item.right) == (left, right), "Bin boundaries")
                require(item.left_inclusive and item.right_inclusive == final, "Bin closure")
                require((item.count, item.frequency) == (count, count / len(values)), "Bin count")
            under = sum(x < spec.edges[0] for x in values)
            over = sum(x > spec.edges[-1] for x in values)
            require(
                result.underflow_count == under and result.overflow_count == over, "Outside counts"
            )
            require(result.underflow_frequency == under / len(values), "Underflow frequency")
            require(result.overflow_frequency == over / len(values), "Overflow frequency")
            require(sum(b.count for b in result.bins) + under + over == len(values), "Conservation")


def verify_job(result, requests) -> dict[str, Any]:
    """Derive population, endpoints and statistics from retained public Exports."""
    prepared, obs, projection = result.prepared_inputs, result.observation_set, result.projection
    require(prepared is not None and obs is not None and projection is not None, "Complete chain")
    job = result.fixed_job_spec
    days: dict[date, Any] = {}
    for item in prepared.calendar_slices:
        view = item.final_export
        c = view.coverage
        count = (item.request.end_date - item.request.start_date).days + 1
        require(c.complete and c.requested_units == c.successful_units == count, "Full Calendar")
        require(c.missing_units == c.pending_units == c.failed_units == 0, "Calendar accounting")
        require(len(view.records) == count, "Calendar records")
        require(
            [r.cal_date.toordinal() for r in view.records]
            == list(
                range(item.request.start_date.toordinal(), item.request.end_date.toordinal() + 1)
            ),
            "Every natural day",
        )
        for row in view.records:
            require(
                row.exchange == "SSE" and type(row.is_open) is int and row.is_open in (0, 1),
                "Calendar fact identity",
            )
            require(row.cal_date not in days or days[row.cal_date] == row, "Calendar overlap")
            days[row.cal_date] = row
    opens = sorted(d for d, row in days.items() if row.is_open == 1)
    anchors = tuple(d for d in opens if WINDOW.start_date <= d <= WINDOW.end_date)
    require(obs.candidate_anchors == anchors and bool(anchors), "Full candidate population")
    first = opens.index(anchors[0]) - job.horizon
    require(first >= 0, "H prior sessions")
    sessions = opens[first : opens.index(anchors[-1]) + 1]
    view = prepared.index_slice.final_export
    require(prepared.index_slice.request.start_date == sessions[0], "Exact warm-up bound")
    require(prepared.index_slice.request.end_date == anchors[-1], "No window truncation")
    rows = {r.trade_date: r for r in view.records}
    require(len(rows) == len(view.records) == view.coverage.successful_units, "Fact count")
    require(
        all(r.index_code == job.subject and d in sessions for d, r in rows.items()), "Fact identity"
    )
    require(view.coverage.requested_units == len(sessions), "Index population")
    require(
        sum(
            (
                view.coverage.successful_units,
                view.coverage.missing_units,
                view.coverage.pending_units,
                view.coverage.failed_units,
            )
        )
        == len(sessions),
        "Index accounting",
    )
    require(view.coverage.complete == (len(rows) == len(sessions)), "Index completeness")
    metadata = {
        (r.index_code, r.symbol, r.name, r.market, r.publisher, r.category) for r in view.records
    }
    require(len(metadata) == 1, "Consistent provider-backed instrument metadata")
    observed_metadata = next(iter(metadata))
    require(
        observed_metadata[0] == "000852.SH"
        and observed_metadata[1] == "000852"
        and observed_metadata[2] == "中证1000",
        "CSI1000 metadata unresolved",
    )
    expected_values, expected_keys, endpoints = [], [], []
    unavailable = excluded = 0
    for anchor in anchors:
        lookback = opens[opens.index(anchor) - job.horizon]
        missing = [
            (role, d) for role, d in (("anchor", anchor), ("lookback", lookback)) if d not in rows
        ]
        key = (obs.job_identity, anchor)
        if missing:
            item = next(o for o in obs.unavailable_observations if o.anchor == anchor)
            require(
                [(m.endpoint_role, m.fact.trade_date) for m in item.missing_dependencies]
                == missing,
                "Missing endpoint evidence",
            )
            unavailable += 1
            endpoints.append({"anchor": anchor, "lookback": lookback, "outcome": "Unavailable"})
        elif rows[anchor].close <= 0 or rows[lookback].close <= 0:
            item = next(o for o in obs.excluded_observations if o.anchor == anchor)
            require(item.reason_code == "non_positive_close", "Exclusion reason")
            excluded += 1
            endpoints.append({"anchor": anchor, "lookback": lookback, "outcome": "Excluded"})
        else:
            value = rows[anchor].close / rows[lookback].close - 1
            expected_values.append(value)
            expected_keys.append(key)
            endpoints.append(
                {
                    "anchor": anchor,
                    "lookback": lookback,
                    "anchor_close": rows[anchor].close,
                    "lookback_close": rows[lookback].close,
                    "return": value,
                }
            )
    require(
        obs.candidate_count == len(anchors) == len(expected_values) + unavailable + excluded,
        "Candidate conservation",
    )
    require(
        (obs.eligible_count, obs.unavailable_count, obs.excluded_count)
        == (len(expected_values), unavailable, excluded),
        "Outcome counts",
    )
    require(
        [o.scalar_value.hex() for o in obs.eligible_observations]
        == [v.hex() for v in expected_values],
        "Every trailing return",
    )
    require(obs.observation_coverage == len(expected_values) / len(anchors), "Observation coverage")
    require(obs.unavailable_ratio == unavailable / len(anchors), "Unavailable ratio")
    require(obs.excluded_ratio == excluded / len(anchors), "Excluded ratio")
    for coverage, subset in (
        (obs.market_fact_coverage.overall, sessions),
        (obs.market_fact_coverage.warm_up, [d for d in sessions if d < anchors[0]]),
        (obs.market_fact_coverage.sample, list(anchors)),
    ):
        expected = tuple((job.subject, d) for d in subset)
        available = tuple(k for k in expected if k[1] in rows)
        require(
            coverage.expected_keys == expected and coverage.available_keys == available,
            "Exact fact coverage keys",
        )
        require(
            coverage.ratio == (len(available) / len(expected) if expected else None), "Fact ratio"
        )
    sample, binding = projection.numeric_sample, projection.binding
    require(
        [x.hex() for x in sample.values] == [x.hex() for x in expected_values], "Sample binary64"
    )
    require(
        sample.unit == "decimal_ratio" and sample.sample_count == len(expected_values), "Sample"
    )
    require(binding.ordered_observation_keys == tuple(expected_keys), "Positional keys")
    require(binding.source_observation_reference is obs, "Actual originating ObservationSet")
    provenance = obs.provenance
    require(provenance.prepared_inputs is prepared, "Original prepared inputs")
    require(result.input_attempts is prepared.attempts, "Original InputAttempts")
    require(provenance.input_profile == "trailing_return_inputs_v2", "Input profile")
    # Verify the retained bytes, without implementing a competing fingerprint serializer.
    require(
        hashlib.sha256(provenance.canonical_input_bytes).hexdigest()
        == provenance.input_fingerprint,
        "Retained bytes SHA-256",
    )
    payload = json.loads(provenance.canonical_input_bytes)
    require(
        payload[0:2] == ["trailing_return_inputs_v2", "descriptive_missing_tolerant_v1"],
        "Published identity profile",
    )
    require(len(result.analysis_outcomes) == len(requests) == 2, "Ordered required analyses")
    for outcome, request in zip(result.analysis_outcomes, requests, strict=True):
        evidence = outcome.associated_evidence
        require(outcome.status == "success" and outcome.request is request, "Original request")
        require(evidence.request is request and evidence.request.spec is request.spec, "Exact spec")
        require(evidence.statistical_result is outcome.statistical_result, "Original raw result")
        require(
            evidence.projection is projection and evidence.source_observation_reference is obs,
            "Original evidence chain",
        )
        require(
            binding.business_provenance is provenance
            and binding.coverage_context is obs.market_fact_coverage
            and binding.sample_dependence_context is obs.sample_dependence_context,
            "Original context",
        )
    check_statistics(sample.values, result.analysis_outcomes)
    require(result.status == "Success" and not result.failures, "Job Success")
    return {
        "metadata": dict(
            zip(
                ("index_code", "symbol", "name", "market", "publisher", "category"),
                observed_metadata,
                strict=True,
            )
        ),
        "open_sessions": public(sessions),
        "endpoints": public(endpoints),
        "counts": {
            "candidate": obs.candidate_count,
            "eligible": obs.eligible_count,
            "unavailable": unavailable,
            "excluded": excluded,
        },
        "market_fact_coverage": public(obs.market_fact_coverage),
        "numeric_sample": public(sample),
        "binding_keys": public(binding.ordered_observation_keys),
        "input_profile": provenance.input_profile,
        "input_fingerprint": provenance.input_fingerprint,
        "public_input_attempts": public(prepared.attempts),
        "statistical_results": [public(o.statistical_result) for o in result.analysis_outcomes],
        "independent_checks": "passed",
        "association_reference_checks": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Explicitly authorize bounded Source I/O"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report: dict[str, Any] = {
        "goal": "LIVE-E2E-01",
        "verdict": "Blocked",
        "tested_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "executed_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "root_poetry_environment": Path(sys.prefix) == ROOT / ".venv",
        "target": "000852.SH",
        "window": public(WINDOW),
        "horizon": 2,
        "historical_default_cache_repaired": False,
    }
    calls: Counter[str] = Counter()
    original_call = TushareExecutor.call

    def bounded_call(self, endpoint, **parameters):
        if sum(calls.values()) >= 24:
            raise RuntimeError("Acceptance Source call bound reached")
        calls[endpoint] += 1
        return original_call(self, endpoint, **parameters)

    try:
        with TemporaryDirectory(prefix="research-live-e2e-") as temporary:
            with isolated_storage(Path(temporary)) as audit:
                report["isolation"] = audit
                if not args.live:
                    report["blocker"] = "Source I/O not requested; isolation check only"
                else:
                    require(report["root_poetry_environment"], "Use the root Poetry environment")
                    # Resolve once via the existing provider mechanism; never serialize its value.
                    credential = resolve_credential()
                    require(bool(credential.strip()), "Credential available")
                    del credential
                    report["credential_available"] = True
                    report["configured_calls_per_minute"] = 60 / request_interval()
                    requests = (
                        AnalysisRequest("live_quantiles", QuantileSpec([0.1, 0.5, 0.9])),
                        AnalysisRequest(
                            "live_distribution",
                            IntervalCountSpec([-0.2, 0.0, 0.2], "decimal_ratio"),
                        ),
                    )
                    fixed = ObservationJobSpec(
                        "000852.SH", "trailing_cumulative_return_v1", {}, 2, WINDOW
                    )
                    with patch.object(TushareExecutor, "call", bounded_call):
                        single = execute_job(fixed, requests)
                        report["single_job_status"] = single.status
                        report["single_analysis_statuses"] = [
                            o.status for o in single.analysis_outcomes
                        ]
                        report["public_input_attempts"] = public(single.input_attempts)
                        report["single_statistical_results"] = [
                            public(o.statistical_result) for o in single.analysis_outcomes
                        ]
                        if single.status != "Success":
                            report["failures"] = [
                                {
                                    "stage": f.failure_stage,
                                    "category": f.failure_category,
                                    "reason": f.reason,
                                }
                                for f in single.failures
                            ]
                            report["blocker"] = "Single Job did not reach successful live analysis"
                            external = all(
                                f.failure_category
                                in {
                                    "IncompleteInput",
                                    "HistoryInsufficient",
                                    "NoEligibleObservations",
                                }
                                or (
                                    f.failure_category == "UpstreamFailure"
                                    and any(
                                        word in f.reason
                                        for word in (
                                            "credential",
                                            "Source could not be initialized",
                                            "permission",
                                            "network",
                                            "timeout",
                                            "quota",
                                            "rate_limit",
                                        )
                                    )
                                )
                                for f in single.failures
                            )
                            report["verdict"] = "Blocked" if external else "Failed"
                            report["batch_status"] = "not_attempted_to_avoid_source_retry"
                        else:
                            report["single"] = verify_job(single, requests)
                            plan = ResearchPlan(
                                fixed.metric,
                                {},
                                [fixed.subject],
                                [2],
                                [WINDOW],
                                requests,
                                "continue",
                            )
                            batch = execute_batch(plan)
                            report["batch"] = {
                                "status": batch.status,
                                "planned": batch.planned_count,
                                "success": batch.success_count,
                                "failed": batch.failed_count,
                                "skipped": batch.skipped_count,
                            }
                            require(
                                len(batch.job_results) == batch.planned_count == 1,
                                "One planned Job",
                            )
                            report["batch_job"] = verify_job(
                                batch.job_results[0], plan.analysis_requests
                            )
                            require(
                                (
                                    batch.status,
                                    batch.success_count,
                                    batch.failed_count,
                                    batch.skipped_count,
                                )
                                == ("success", 1, 0, 0),
                                "Batch accounting",
                            )
                            require(
                                report["single"]["input_fingerprint"]
                                == report["batch_job"]["input_fingerprint"],
                                "Retained inputs stable",
                            )
                            report["verdict"] = "Verified"
    except IsolationError:
        report["blocker"] = "Live Gate Blocked - Isolation not established"
    except OperationError:
        report["blocker"] = "Provider credential or runtime configuration unavailable at preflight"
    except AssertionError as exc:
        report["verdict"] = "Blocked" if str(exc) == "CSI1000 metadata unresolved" else "Failed"
        report["verification_error"] = str(exc)
    except Exception as exc:
        report["verdict"] = "Failed"
        report["harness_error_type"] = type(exc).__name__
    finally:
        report["provider_calls"] = dict(calls)
        args.output.write_text(
            json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({"verdict": report["verdict"], "provider_calls": dict(calls)}, sort_keys=True))
    return 0 if report["verdict"] == "Verified" or not args.live else 1


if __name__ == "__main__":
    raise SystemExit(main())
