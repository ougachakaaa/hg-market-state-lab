"""Versioned R01-A evidence and strict canonical public-input replay."""

import hashlib
import json
import re
from dataclasses import fields, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any, cast

from data_lake import CoverageResult
from data_lake.datasets.tushare_equity_index_futures import (
    FuturesDailyExport,
    FuturesDailyRow,
    FuturesDailyScope,
)
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRow, IndexDailyScope
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord

from .construction import construct_observations
from .inputs import PROFILE, FuturesBasisRequest, InputAttempt, PreparedFuturesBasisInputs
from .report import LIMITATIONS, ReportRequest, ReportResult, compose_report, project_history
from .statistics import METRICS
from .validation import CalendarScope, Window

PROFILE_REPORT = "futures_basis_report_evidence_v1"
PROFILE_MANIFEST = "futures_basis_report_manifest_v1"


def safe_reason(value: str) -> str:
    value = re.sub(r"https?://\S+|(?:/[^\s]+){2,}", "[redacted-location]", value)
    return re.sub(r"(?i)(token|password|secret|authorization)[=: ]+\S+", r"\1=[redacted]", value)


def encode(value: Any) -> Any:
    """Lossless JSON projection of this case's public carriers (not a class loader)."""
    if type(value) is date:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return encode({f.name: getattr(value, f.name) for f in fields(value)})
    if isinstance(value, tuple | list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        return {
            k: safe_reason(v) if k == "reason" and isinstance(v, str) else encode(v)
            for k, v in value.items()
        }
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise ValueError("Unsupported case evidence value")


def json_bytes(value: Any) -> bytes:
    return json.dumps(
        encode(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json_bytes(value))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact(raw: Any, names: set[str]) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != names:
        raise ValueError("Unexpected canonical evidence fields")
    return raw


def load_prepared_inputs(path: Path, request: FuturesBasisRequest) -> PreparedFuturesBasisInputs:
    data = path.read_bytes()
    raw = json.loads(data)
    _exact(raw, {"profile", "calendar_cffex", "calendar_sse", "futures", "index"})
    if raw["profile"] != PROFILE:
        raise ValueError("Unknown input profile")

    def decode(value: Any, name: str = "") -> Any:
        if isinstance(value, list):
            if len(value) == 2 and value[0] == "float64":
                return float.fromhex(value[1])
            return tuple(decode(v) for v in value)
        if isinstance(value, dict):
            return {k: decode(v, k) for k, v in value.items()}
        if name.endswith("date") and value is not None:
            return date.fromisoformat(value)
        return value

    def export(name: str, cls: Any, row_cls: Any, scope_cls: Any) -> Any:
        item = decode(raw[name])
        _exact(
            item,
            {"dataset", "view", "export_schema_version", "scope", "window", "coverage", "records"},
        )
        for row in item["records"]:
            _exact(row, {f.name for f in fields(row_cls)})
        return cls(
            item["dataset"],
            item["view"],
            item["export_schema_version"],
            scope_cls(**item["scope"]),
            Window(**item["window"]),
            CoverageResult(**item["coverage"]),
            tuple(row_cls(**r) for r in item["records"]),
        )

    exports = {
        "CFFEX": export("calendar_cffex", TradeCalendarExport, TradeCalendarRecord, CalendarScope),
        "SSE": export("calendar_sse", TradeCalendarExport, TradeCalendarRecord, CalendarScope),
        "futures": export("futures", FuturesDailyExport, FuturesDailyRow, FuturesDailyScope),
        "index": export("index", IndexDailyExport, IndexDailyRow, IndexDailyScope),
    }

    # A partial Index must be validated without triggering prepare_inputs' ensure.
    # The same existing public validation is used for all four final envelopes.
    from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRange
    from data_lake.datasets.tushare_index_daily import IndexDailyRange
    from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange

    from .inputs import UNDERLYING
    from .validation import input_identity, validate_export, validate_request

    validate_request(request)
    cffex = cast(
        TradeCalendarExport,
        validate_export(
            exports["CFFEX"], TradeCalendarRange("CFFEX", request.start_date, request.end_date)
        ),
    )
    sse = cast(
        TradeCalendarExport,
        validate_export(
            exports["SSE"], TradeCalendarRange("SSE", request.start_date, request.end_date)
        ),
    )
    candidates = tuple(r.cal_date for r in cffex.records if r.is_open == 1)
    sessions = tuple(r.cal_date for r in sse.records if r.is_open == 1)
    fut = cast(
        FuturesDailyExport,
        validate_export(
            exports["futures"],
            FuturesDailyRange((request.product_code,), request.start_date, request.end_date),
            candidates,
        ),
    )
    idx = cast(
        IndexDailyExport,
        validate_export(
            exports["index"],
            IndexDailyRange(
                (UNDERLYING[request.product_code],), request.start_date, request.end_date
            ),
            sessions,
        ),
    )
    if not cffex.coverage.complete or not sse.coverage.complete or not fut.coverage.complete:
        raise ValueError("Offline inputs require complete Calendar/Futures")
    canonical, fingerprint = input_identity(cffex, sse, fut, idx)
    if canonical != data:
        raise ValueError("Canonical input bytes differ after public validation")
    # Construction revalidates the complete prepared handoff, including associations.
    return PreparedFuturesBasisInputs(
        request,
        cffex,
        sse,
        fut,
        idx,
        candidates,
        sessions,
        (
            InputAttempt(
                "calendar_cffex",
                TradeCalendarRange("CFFEX", request.start_date, request.end_date),
                final_export=cffex,
            ),
            InputAttempt(
                "calendar_sse",
                TradeCalendarRange("SSE", request.start_date, request.end_date),
                final_export=sse,
            ),
            InputAttempt(
                "futures",
                FuturesDailyRange((request.product_code,), request.start_date, request.end_date),
                final_export=fut,
            ),
            InputAttempt(
                "index",
                IndexDailyRange(
                    (UNDERLYING[request.product_code],), request.start_date, request.end_date
                ),
                final_export=idx,
            ),
        ),
        data,
        fingerprint,
    )


def _refs(rows: Any) -> Any:
    return [encode(r.identity) if hasattr(r, "identity") else _refs(r) for r in rows]


def scientific_payload(
    report: ReportResult,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = report.source
    observations = {
        f.name: encode(getattr(source, f.name)) for f in fields(source) if f.name != "prepared"
    }
    distributions = []
    comparisons = []
    for result in report.distributions:
        distributions.append(
            dict(
                request=encode(result.request),
                candidates=_refs(result.candidates),
                binding=_refs(result.binding),
                methods=encode(result.methods),
            )
        )
    for comparison in report.comparisons:
        comparisons.append(
            dict(
                request=encode(comparison.request),
                candidates=_refs(comparison.candidates),
                binding=_refs(comparison.binding),
                dropped=_refs(comparison.dropped),
                common_dates=encode(comparison.common_dates),
                dropped_details=[
                    dict(
                        date=a.trade_date,
                        left=dict(
                            slot=a.slot, outcome=encode(a.outcome(comparison.request.metric))
                        ),
                        right=dict(
                            slot=b.slot, outcome=encode(b.outcome(comparison.request.metric))
                        ),
                    )
                    for a, b in comparison.dropped
                ],
                left_methods=encode(comparison.left_methods),
                right_methods=encode(comparison.right_methods),
            )
        )
    persistence = []
    for summary in report.persistence:

        def runs(items: Any) -> Any:
            return [
                dict(
                    slot=r.slot,
                    references=_refs(r.references),
                    transitions=encode(r.transitions),
                    start=r.start.isoformat(),
                    end=r.end.isoformat(),
                    observed_trading_sessions=r.observed_trading_sessions,
                    left_boundary=r.left_boundary,
                    right_boundary=r.right_boundary,
                )
                for r in items
            ]

        persistence.append(
            dict(
                slot=summary.slot,
                start_date=summary.start_date.isoformat(),
                end_date=summary.end_date.isoformat(),
                complete=runs(summary.complete),
                censored=runs(summary.censored),
            )
        )
    science = dict(
        request=encode(report.request),
        observations=observations,
        distributions=distributions,
        comparisons=comparisons,
        persistence=persistence,
    )
    views: dict[str, Any] = {"history": {}, "histograms": {}}
    associations: dict[str, Any] = {}
    for metric in METRICS:
        view, assoc = project_history(source, metric)
        views["history"][metric] = view
        associations[metric] = encode(assoc)
    for result in report.distributions:
        outcome = result.methods[2]
        if outcome.failure_category is not None or outcome.result is None:
            continue
        histogram = encode(outcome.result)
        labels = (
            [f"< {histogram['edges'][0]!r}"]
            + [
                f"{'[' if b['left_inclusive'] else '('}{b['left']!r}, "
                f"{b['right']!r}{']' if b['right_inclusive'] else ')'}"
                for b in histogram["bins"]
            ]
            + [f"> {histogram['edges'][-1]!r}"]
        )
        for measure in ("count", "frequency"):
            values = (
                [histogram[f"underflow_{measure}"]]
                + [b[measure] for b in histogram["bins"]]
                + [histogram[f"overflow_{measure}"]]
            )
            unit = "count" if measure == "count" else "frequency"
            views["histograms"][result.request.analysis_id + "/" + measure] = dict(
                version=1,
                axes=[
                    dict(
                        id="interval",
                        orientation="x",
                        coordinate=dict(kind="category", unit="category"),
                    ),
                    dict(id="value", orientation="y", coordinate=dict(kind="number", unit=unit)),
                ],
                layers=[
                    dict(
                        id="histogram",
                        x_axis="interval",
                        y_axis="value",
                        layer=dict(
                            type="bar",
                            version=1,
                            x=dict(kind="category", unit="category"),
                            y=dict(kind="number", unit=unit),
                            data=[dict(x=x, y=y) for x, y in zip(labels, values, strict=True)],
                        ),
                    )
                ],
                layout=dict(title=f"{result.request.analysis_id} · {measure}"),
                presentation=dict(show_legend=False),
            )
    prepared = source.prepared
    reader = dict(
        profile=PROFILE_REPORT,
        status=report.status,
        request=encode(report.request),
        fingerprint=prepared.input_fingerprint,
        definition_version=prepared.definition_version,
        coverage={
            name: encode(getattr(prepared, name).coverage)
            for name in ("calendar_cffex", "calendar_sse", "futures", "index")
        },
        accounting=encode(source.accounting),
        candidate_dates=encode(prepared.candidate_dates),
        formulas=[
            "basis_value = F_close − S_close (index_points)",
            "basis_ratio = (F_close − S_close) / S_close (decimal_ratio)",
            "annualized_basis_ratio = (365 / DTE) × ln(F_close / S_close) "
            "(decimal_ratio); DTE=0 不适用",
        ],
        sources=(
            "Tushare public DataLake Exports · CFFEX futures / SSE CSI index "
            f"{cast(IndexDailyScope, prepared.index.scope).index_codes[0]} · 同日 Close"
        ),
        summary=(
            f"研究问题：{prepared.request.product_code} 各相对期限 Slot 的同日基差如何变化，"
            "其分布、共同日期期限差异与贴水持续区间是什么？"
        ),
        limitations=LIMITATIONS,
        distributions=distributions,
        comparisons=comparisons,
        persistence=persistence,
        views=encode(views),
    )
    return encode(science), encode(views), associations, encode(reader)


def write_evidence(report: ReportResult, output: Path, *, runtime: dict[str, Any]) -> None:
    science, views, associations, reader = scientific_payload(report)
    reader["runtime"] = runtime
    write_json(
        output / "evidence.json",
        dict(
            profile=PROFILE_REPORT,
            status=report.status,
            definition_version=report.source.prepared.definition_version,
            input_fingerprint=report.source.prepared.input_fingerprint,
            science=science,
            attempts=encode(report.source.prepared.attempts),
            runtime=runtime,
        ),
    )
    (output / "inputs.canonical.json").write_bytes(report.source.prepared.canonical_bytes)
    write_json(output / "views.json", views)
    write_json(output / "associations.json", associations)
    write_json(output / "report-data.json", reader)


def seal_delivery(output: Path, status: str, fingerprint: str | None) -> None:
    files = {
        p.name: dict(size=p.stat().st_size, sha256=digest(p.read_bytes()))
        for p in sorted(output.iterdir())
        if p.is_file() and p.name not in ("manifest.json", "SHA256SUMS")
    }
    write_json(
        output / "manifest.json",
        dict(profile=PROFILE_MANIFEST, status=status, input_fingerprint=fingerprint, files=files),
    )
    files["manifest.json"] = dict(sha256=digest((output / "manifest.json").read_bytes()))
    (output / "SHA256SUMS").write_text(
        "".join(f"{item['sha256']}  {name}\n" for name, item in sorted(files.items()))
    )


def verify_delivery(output: Path) -> dict[str, Any]:
    if any(p.is_symlink() or not p.is_file() for p in output.iterdir()):
        raise ValueError("Unsafe delivery file")
    manifest = json.loads((output / "manifest.json").read_bytes())
    _exact(manifest, {"profile", "status", "input_fingerprint", "files"})
    if manifest["profile"] != PROFILE_MANIFEST:
        raise ValueError("Unknown manifest profile")
    inventory = set(manifest["files"]) | {"manifest.json", "SHA256SUMS"}
    if {p.name for p in output.iterdir()} != inventory:
        raise ValueError("Unexpected or missing delivery files")
    sums = []
    for name in sorted(inventory - {"SHA256SUMS"}):
        p = output / name
        if Path(name).name != name or p.is_symlink() or not p.is_file():
            raise ValueError("Unsafe delivery file")
        data = p.read_bytes()
        sha = digest(data)
        if name != "manifest.json" and manifest["files"][name] != dict(size=len(data), sha256=sha):
            raise ValueError("File digest/size mismatch: " + name)
        sums.append(f"{sha}  {name}\n")
    if (output / "SHA256SUMS").read_text() != "".join(sums):
        raise ValueError("SHA256SUMS mismatch")
    if manifest["status"] == "failed":
        if manifest["input_fingerprint"] is not None or "failure.json" not in inventory:
            raise ValueError("Malformed failure package")
        return manifest
    required = {
        "evidence.json",
        "report-data.json",
        "inputs.canonical.json",
        "views.json",
        "associations.json",
        "report.html",
        "REPRODUCE.md",
    }
    if not required <= inventory or manifest["status"] not in ("complete", "partial"):
        raise ValueError("Incomplete report package")
    evidence = json.loads((output / "evidence.json").read_bytes())
    reader = json.loads((output / "report-data.json").read_bytes())
    if reader.get("runtime") != evidence["runtime"]:
        raise ValueError("Runtime context association mismatch")
    if evidence["profile"] != PROFILE_REPORT or reader["profile"] != PROFILE_REPORT:
        raise ValueError("Unknown evidence profile")
    if not manifest["status"] == evidence["status"] == reader["status"]:
        raise ValueError("Report status association mismatch")
    request_from_json(evidence["science"]["request"])
    fingerprint = digest((output / "inputs.canonical.json").read_bytes())
    if (
        not fingerprint
        == manifest["input_fingerprint"]
        == evidence["input_fingerprint"]
        == reader["fingerprint"]
    ):
        raise ValueError("Input fingerprint mismatch")
    if reader["views"] != json.loads((output / "views.json").read_bytes()):
        raise ValueError("View association mismatch")
    if evidence["science"]["request"] != reader["request"]:
        raise ValueError("Request association mismatch")
    embedded = re.search(
        r'<script id="report-data" type="application/json">(.*?)</script>',
        (output / "report.html").read_text(encoding="utf-8"),
        re.DOTALL,
    )
    if embedded is None or json.loads(embedded.group(1)) != reader:
        raise ValueError("HTML reader payload association mismatch")
    _verify_associations(evidence, reader, json.loads((output / "associations.json").read_bytes()))
    return manifest


def _verify_associations(evidence: Any, reader: Any, associations: Any) -> None:
    science = evidence["science"]
    rows = science["observations"]["slot_days"]
    by_key = {(r["product_code"], r["trade_date"], r["slot"]): r for r in rows}
    if len(by_key) != len(rows):
        raise ValueError("Duplicate Slot-day identity")
    for name in ("distributions", "comparisons", "persistence"):
        if science[name] != reader[name]:
            raise ValueError("Reader result association mismatch")
    for result in science["distributions"] + science["comparisons"]:
        for field in ("candidates", "binding", "dropped"):
            for ref in result.get(field, []):
                refs = [ref] if field != "dropped" and "slots" not in result["request"] else ref
                if any(tuple(key) not in by_key for key in refs):
                    raise ValueError("Unknown analysis Slot-day reference")
    transitions = science["observations"]["transitions"]["transitions"]
    for metric in METRICS:
        assoc = associations[metric]
        view = reader["views"]["history"][metric]
        if len(assoc["points"]) != len(rows) or len(view["events"]) != len(transitions):
            raise ValueError("Chart source association count mismatch")
        for binding in view["layers"]:
            for mark in binding["layer"]["data"]:
                ref = f"{metric}/{binding['id']}/{mark['x']}"
                association = assoc["points"][ref]
                row = by_key[tuple(association["slot_day"])]
                obs = row["observation"]
                outcome = obs[metric] if obs else {"value": None}
                if (
                    mark["y"] != outcome["value"]
                    or row["slot"] != binding["id"]
                    or row["trade_date"] != mark["x"]
                ):
                    raise ValueError("Chart point association mismatch")
                if association["contract_day"] != (
                    [obs["contract"]["contract_code"], row["trade_date"]] if obs else None
                ):
                    raise ValueError("Contract-day association mismatch")
                for field in ("futures_source", "underlying_source"):
                    if association[field] != (obs[field] if obs else None):
                        raise ValueError("Source reference mismatch")
        for i, event in enumerate(view["events"]):
            if (
                assoc["events"][event["id"]] != transitions[i]
                or event["x"] != transitions[i]["trade_date"]
            ):
                raise ValueError("Transition association mismatch")


def request_from_json(raw: Any) -> ReportRequest:
    from market_statistics import IntervalCountSpec, QuantileSpec

    obs = raw["observation"]
    _exact(obs, {"product_code", "start_date", "end_date", "case"})
    request = ReportRequest(
        FuturesBasisRequest(
            obs["product_code"],
            date.fromisoformat(obs["start_date"]),
            date.fromisoformat(obs["end_date"]),
            obs["case"],
        ),
        QuantileSpec(raw["quantile"]["points"]),
        tuple(IntervalCountSpec(h["edges"], h["unit"]) for h in raw["histograms"]),
    )
    if encode(request) != raw:
        raise ValueError("Unexpected report request encoding")
    request.validate()
    return request


def replay_delivery(output: Path) -> dict[str, Any]:
    manifest = verify_delivery(output)
    if manifest["status"] == "failed":
        raise ValueError("Failed acquisition has no successful inputs to replay")
    evidence = json.loads((output / "evidence.json").read_bytes())
    request = request_from_json(evidence["science"]["request"])
    prepared = load_prepared_inputs(output / "inputs.canonical.json", request.observation)
    report = compose_report(construct_observations(request.observation, prepared), request)
    science, views, associations, reader = scientific_payload(report)
    retained_reader = json.loads((output / "report-data.json").read_bytes())
    retained_reader.pop("runtime")
    expected = (
        evidence["science"],
        json.loads((output / "views.json").read_bytes()),
        json.loads((output / "associations.json").read_bytes()),
        retained_reader,
    )
    if json_bytes((science, views, associations, reader)) != json_bytes(expected):
        raise ValueError("Scientific replay mismatch")
    return dict(
        status="PASS",
        input_fingerprint=prepared.input_fingerprint,
        distributions=len(report.distributions),
        comparisons=len(report.comparisons),
    )
