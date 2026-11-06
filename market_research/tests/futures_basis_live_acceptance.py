"""Explicit bounded WP3 real-market gate; never collected by ordinary pytest.

Only test infrastructure redirects Dataset composition paths and audits SQLite.
Research receives unmodified public services. No credentials are read by this harness.
Run from root with --live --output-dir /absolute/path/outside/repository.
"""

import argparse
import json
import math
import sqlite3
from collections import Counter
from contextlib import ExitStack, contextmanager
from dataclasses import fields, is_dataclass
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from data_lake.datasets.tushare_equity_index_futures import _composition as futures_composition
from data_lake.datasets.tushare_index_daily import _composition as index_composition
from data_lake.datasets.tushare_trade_calendar import _composition as calendar_composition
from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest,
    FuturesBasisResult,
    InputPreparationError,
    ObservationConstructionError,
    construct_observations,
    prepare_inputs,
)

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ("tushare_trade_calendar", "tushare_equity_index_futures", "tushare_index_daily")
REQUEST = FuturesBasisRequest("IM", date(2026, 10, 12), date(2026, 10, 23))


def public(value: Any) -> Any:
    if type(value) is date:
        return value.isoformat()
    if isinstance(value, bytes):
        return {"canonical_bytes_file": "inputs.canonical.json", "byte_count": len(value)}
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: public(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, tuple | list):
        return [public(item) for item in value]
    if isinstance(value, dict):
        return {key: public(item) for key, item in value.items()}
    return value


def cache_state() -> dict[str, tuple[int, int]]:
    return {
        str(p.relative_to(ROOT)): (p.stat().st_size, p.stat().st_mtime_ns)
        for name in DATASETS
        for p in (ROOT / "data_lake" / "datasets" / name / "data").glob("*")
        if p.is_file()
    }


@contextmanager
def isolated_storage(directory: Path):
    if not directory.is_absolute() or directory == ROOT or ROOT in directory.parents:
        raise ValueError("External absolute storage directory required")
    directory.mkdir()
    paths = {name: directory / (name + ".sqlite3") for name in DATASETS}
    connections: Counter[str] = Counter()
    original = sqlite3.connect
    before = cache_state()
    audit: dict[str, Any] = {"isolated_before_source": True}

    def location(dataset, storage_root):
        if dataset not in paths:
            raise AssertionError("Unexpected Dataset")
        return paths[dataset]

    def connect(database, *args, **kwargs):
        value = str(database)
        if value.startswith("file:"):
            value = unquote(urlsplit(value).path)
        target = Path(value).resolve()
        if target not in paths.values():
            raise AssertionError("SQLite connection escaped isolation")
        connections[target.name] += 1
        return original(database, *args, **kwargs)

    with ExitStack() as stack:
        for module in (calendar_composition, futures_composition, index_composition):
            stack.enter_context(patch.object(module, "database_path", location))
        stack.enter_context(patch.object(sqlite3, "connect", connect))
        try:
            yield audit
        finally:
            audit["connections"] = dict(connections)
            audit["default_caches_unchanged"] = cache_state() == before
            if not audit["default_caches_unchanged"]:
                raise AssertionError("Default Dataset cache metadata changed")


def verify(result: FuturesBasisResult) -> list[dict[str, Any]]:
    """Independent Decimal oracle and associations, using retained public source rows."""
    p = result.prepared
    futures = {(r.contract_code, r.trade_date): r for r in p.futures.records}
    indices = {r.trade_date: r for r in p.index.records}
    eligible = [r for r in result.contract_days if r.base.status == "eligible"]
    if len(eligible) < 3:
        raise AssertionError("Fewer than three eligible real Contract-days")
    chosen = [eligible[0]]
    expiries = [r for r in eligible if r.days_to_expiry == 0]
    if expiries and expiries[0] not in chosen:
        chosen.append(expiries[0])
    if result.transitions.transitions:
        event = result.transitions.transitions[0]
        match = [
            r
            for r in eligible
            if r.trade_date == event.trade_date and r.contract_code == event.contract_code
        ]
        if match and match[0] not in chosen:
            chosen.append(match[0])
    for row in eligible:
        if len(chosen) >= 3:
            break
        if row not in chosen:
            chosen.append(row)
    samples = []
    for row in chosen:
        source = futures[row.identity]
        spot = indices[row.trade_date].close
        assert row.futures_close == source.close and row.underlying_close == spot
        dte = (source.delist_date - source.trade_date).days
        assert row.days_to_expiry == dte
        with localcontext() as ctx:
            ctx.prec = 60
            f, s = Decimal.from_float(source.close), Decimal.from_float(spot)
            delta, ratio = f - s, (f - s) / s
            assert row.basis_value.value is not None and row.basis_ratio.value is not None
            assert math.isclose(row.basis_value.value, float(delta), rel_tol=1e-12, abs_tol=1e-10)
            assert math.isclose(row.basis_ratio.value, float(ratio), rel_tol=1e-12, abs_tol=1e-14)
            annual = None if dte == 0 else float(Decimal(365) / Decimal(dte) * (f / s).ln())
            if annual is None:
                assert row.annualized_basis_ratio.reason == "expiry_day"
            else:
                assert row.annualized_basis_ratio.value is not None
                assert math.isclose(
                    row.annualized_basis_ratio.value, annual, rel_tol=1e-11, abs_tol=1e-13
                )
        samples.append(
            {
                "identity": public(row.identity),
                "futures_close": source.close,
                "underlying_close": spot,
                "days_to_expiry": dte,
                "independent_basis_value": float(delta),
                "independent_basis_ratio": float(ratio),
                "independent_annualized_basis_ratio": annual,
            }
        )
    assert len(result.slot_days) == 4 * len(p.candidate_dates)
    assert len({r.identity for r in result.contract_days}) == len(result.contract_days)
    for slot in result.slot_days:
        if slot.observation:
            assert slot.observation in result.contract_days
            assert slot.observation.contract_code == slot.contract_code
    for a in result.accounting:
        assert sum(c.count for c in a.outcomes) == a.candidate_count
    for event in result.transitions.transitions:
        endpoints = [
            r
            for r in result.slot_days
            if r.slot == event.slot and r.trade_date in (event.previous_date, event.trade_date)
        ]
        assert [r.contract_code for r in endpoints] == [
            event.previous_contract_code,
            event.contract_code,
        ]
    return samples


def run(output: Path) -> dict[str, Any]:
    output = output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Evidence must be outside repository")
    output.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {"request": public(REQUEST), "real_market_acceptance": "BLOCKED"}
    try:
        with isolated_storage(output / "dataset-cache") as audit:
            report["isolation"] = audit
            prepared = prepare_inputs(REQUEST)
            (output / "inputs.canonical.json").write_bytes(prepared.canonical_bytes)
            (output / "inputs.json").write_text(
                json.dumps(public(prepared), ensure_ascii=True, allow_nan=False), encoding="utf-8"
            )
            result = construct_observations(REQUEST, prepared)
            (output / "result.json").write_text(
                json.dumps(public(result), ensure_ascii=True, allow_nan=False), encoding="utf-8"
            )
            report.update(
                input_fingerprint=prepared.input_fingerprint,
                definition_version=prepared.definition_version,
                candidate_dates=len(prepared.candidate_dates),
                contract_days=len(result.contract_days),
                slot_days=len(result.slot_days),
                base_eligible=sum(r.base.status == "eligible" for r in result.contract_days),
                transitions=public(result.transitions),
                accounting=public(result.accounting),
                coverage={
                    name: public(getattr(prepared, name).coverage)
                    for name in ("calendar_cffex", "calendar_sse", "futures", "index")
                },
            )
            report["independent_samples"] = verify(result)
            report["real_market_acceptance"] = (
                "PASS" if prepared.index.coverage.complete else "PARTIAL"
            )
    except InputPreparationError as exc:
        report.update(
            failure_stage=exc.stage,
            failure_category=exc.category,
            dependency=exc.dependency,
            reason=exc.reason,
            obtained_evidence=public(exc.evidence),
        )
    except ObservationConstructionError as exc:
        report.update(
            failure_stage=exc.stage,
            failure_category=exc.category,
            reason=exc.reason,
            identity=public(exc.identity),
        )
    except AssertionError as exc:
        report.update(
            real_market_acceptance="FAIL", failure_stage="independent_acceptance", reason=str(exc)
        )
    (output / "acceptance.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False), encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output_dir)
    print(
        json.dumps(
            {
                "real_market_acceptance": result["real_market_acceptance"],
                "evidence": str(args.output_dir),
            },
            ensure_ascii=True,
        )
    )
    return 0 if result["real_market_acceptance"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
