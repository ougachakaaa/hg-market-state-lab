"""Exit-semantics acceptance for the opt-in WP8 harness; no Tushare token or network."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from market_backtesting.cases.futures_roll_long import (
    FuturesRollApplicationError,
    build_backtest_result,
    build_evidence_package,
    encode_evidence_package,
)
from public_input_fixtures import fake_services, request

MODULE_PATH = Path(__file__).with_name("wp8_real_acceptance.py")


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "wp8_real_acceptance_under_test", MODULE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def acceptance() -> ModuleType:
    return load_module()


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    path = tmp_path / "artifacts"
    path.mkdir()
    return path


@dataclass(frozen=True)
class _Preflight:
    state: str = "unknown"


class _UnavailableService:
    def preflight(self, request: Any) -> _Preflight:
        return _Preflight()

    def run(self, request: Any) -> Any:
        raise FuturesRollApplicationError(
            "upstream_operation",
            "source_credential_unavailable",
            stage="prepare",
            dependency="futures",
        )


class _InvalidService(_UnavailableService):
    def run(self, request: Any) -> Any:
        raise FuturesRollApplicationError(
            "invalid_numeric", "nonfinite_close", stage="replay", dependency="futures"
        )


def _acceptance_report(root: Path) -> dict[str, Any]:
    return json.loads((root / "python-acceptance.json").read_text(encoding="utf-8"))


def _reproduction_report(root: Path) -> dict[str, Any]:
    return json.loads((root / "offline-reproduction.json").read_text(encoding="utf-8"))


def test_exit_code_is_zero_only_for_pass(acceptance: ModuleType) -> None:
    assert acceptance.exit_code("PASS") == 0
    for status in ("FAIL", "PARTIAL", "NOT RUN", "UNKNOWN"):
        assert acceptance.exit_code(status) > 0


def test_overall_status_never_upgrades_failure_or_missing_stage(
    acceptance: ModuleType,
) -> None:
    assert acceptance.overall_status(["PASS", "PASS"]) == "PASS"
    assert acceptance.overall_status(["PASS", "FAIL"]) == "FAIL"
    assert acceptance.overall_status(["PASS", "NOT RUN"]) == "PARTIAL"
    assert acceptance.overall_status(["NOT RUN", "NOT RUN"]) == "NOT RUN"
    assert acceptance.overall_status([]) == "NOT RUN"


@pytest.mark.parametrize("status,code", [("PASS", 0), ("FAIL", 1), ("PARTIAL", 2), ("NOT RUN", 3)])
def test_python_mode_exit_code_comes_from_the_artifact(
    acceptance: ModuleType,
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    code: int,
) -> None:
    def final(path: Path) -> str:
        acceptance.write_json(path / "python-acceptance.json", {"status": status})
        return str(status)

    monkeypatch.setattr(acceptance, "accept_python", final)
    assert acceptance.run(["--root", str(root), "--mode", "python"]) == code


def test_unavailable_upstream_is_not_run_and_nonzero(
    acceptance: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(acceptance, "create_futures_roll_service", lambda: _UnavailableService())
    monkeypatch.setattr(acceptance, "coverage_snapshot", dict)
    assert acceptance.run(["--root", str(root), "--mode", "python"]) == 3
    report = _acceptance_report(root)
    assert report["status"] == "NOT RUN"
    assert all(item["status"] == "NOT RUN" for item in report["profiles"].values())


def test_product_failure_is_fail_and_nonzero(
    acceptance: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(acceptance, "create_futures_roll_service", lambda: _InvalidService())
    monkeypatch.setattr(acceptance, "coverage_snapshot", dict)
    assert acceptance.run(["--root", str(root), "--mode", "python"]) == 1
    report = _acceptance_report(root)
    assert report["status"] == "FAIL"
    assert next(iter(report["profiles"].values()))["status"] == "FAIL"


def test_failed_round_never_keeps_a_previous_pass(
    acceptance: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    acceptance.write_json(root / "python-acceptance.json", {"status": "PASS", "profiles": {}})
    for profile in acceptance.STRATEGY_PROFILES:
        (root / f"{profile}-result.json").write_text("{}", encoding="utf-8")
        (root / f"{profile}-evidence.json").write_text("{}", encoding="utf-8")
    (root / "offline-reproduction.json").write_text('{"status": "PASS"}\n', encoding="utf-8")

    def unavailable() -> Any:
        raise RuntimeError("public service unavailable")

    monkeypatch.setattr(acceptance, "create_futures_roll_service", unavailable)
    assert acceptance.run(["--root", str(root), "--mode", "python"]) == 1
    report = _acceptance_report(root)
    assert report["status"] == "FAIL"
    assert report["run_id"]
    assert all(
        not (root / f"{profile}-result.json").exists()
        for profile in acceptance.STRATEGY_PROFILES
    )
    assert not (root / "offline-reproduction.json").exists()


def test_missing_evidence_is_not_run_and_nonzero(acceptance: ModuleType, root: Path) -> None:
    assert acceptance.run(["--root", str(root), "--mode", "reproduce"]) == 3
    report = _reproduction_report(root)
    assert report["status"] == "NOT RUN"
    assert all(item["status"] == "NOT RUN" for item in report["profiles"].values())


def test_corrupt_evidence_is_fail_and_nonzero(acceptance: ModuleType, root: Path) -> None:
    acceptance.write_json(
        root / "python-acceptance.json",
        {
            "status": "PASS",
            "same_input": True,
            "run_id": "round-1",
            "profiles": {
                profile: {"status": "PASS", "fingerprint": "f" * 64}
                for profile in acceptance.STRATEGY_PROFILES
            },
        },
    )
    for profile in acceptance.STRATEGY_PROFILES:
        (root / f"{profile}-evidence.json").write_bytes(b"not-evidence")
        (root / f"{profile}-result.json").write_text("{}", encoding="utf-8")
    assert acceptance.run(["--root", str(root), "--mode", "reproduce"]) == 1
    report = _reproduction_report(root)
    assert report["status"] == "FAIL"
    assert all(item["status"] == "FAIL" for item in report["profiles"].values())


def test_reproduction_passes_against_retained_evidence_without_credentials(
    acceptance: ModuleType, root: Path
) -> None:
    service = fake_services()[0]
    profiles: dict[str, Any] = {}
    for profile in acceptance.STRATEGY_PROFILES:
        execution = service.run(request(profile))
        result = build_backtest_result(execution)
        payload = encode_evidence_package(build_evidence_package(execution, result))
        (root / f"{profile}-evidence.json").write_bytes(payload)
        acceptance.write_json(root / f"{profile}-result.json", asdict(result))
        profiles[profile] = {"status": "PASS", "fingerprint": result.evidence.input_fingerprint}
    acceptance.write_json(
        root / "python-acceptance.json",
        {"status": "PASS", "same_input": True, "run_id": "synthetic-round", "profiles": profiles},
    )
    assert acceptance.run(["--root", str(root), "--mode", "reproduce"]) == 0
    report = _reproduction_report(root)
    assert report["status"] == "PASS"
    assert report["acceptance_run_id"] == "synthetic-round"
    assert all(item["reproduction"] == "verified" for item in report["profiles"].values())


def test_partial_reproduction_is_nonzero(acceptance: ModuleType, root: Path) -> None:
    service = fake_services()[0]
    profile = acceptance.STRATEGY_PROFILES[0]
    execution = service.run(request(profile))
    result = build_backtest_result(execution)
    (root / f"{profile}-evidence.json").write_bytes(
        encode_evidence_package(build_evidence_package(execution, result))
    )
    acceptance.write_json(root / f"{profile}-result.json", asdict(result))
    acceptance.write_json(
        root / "python-acceptance.json",
        {
            "status": "PASS",
            "same_input": True,
            "run_id": "partial-round",
            "profiles": {
                profile: {"status": "PASS", "fingerprint": result.evidence.input_fingerprint},
                acceptance.STRATEGY_PROFILES[1]: {"status": "PASS", "fingerprint": "f" * 64},
            },
        },
    )
    assert acceptance.run(["--root", str(root), "--mode", "reproduce"]) == 2
    report = _reproduction_report(root)
    assert report["status"] == "PARTIAL"
    assert report["profiles"][acceptance.STRATEGY_PROFILES[1]]["status"] == "NOT RUN"
