"""Study bindings, failure continuation, CLI admission and owned-only boundaries."""

import ast
import subprocess
import sys
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import pytest

from market_research.observations import ObservationOperationError
from market_research.observations.cffex_option_expiry_dte_chain import (
    ExpiryDteChainRequest,
    ExpiryDteChainService,
)
from market_research.observations.cffex_option_expiry_universe import (
    ExpiryUniverseRequest,
    ExpiryUniverseService,
)
from market_research.studies.cffex_option_expiry_dte_collection import (
    CollectionRequest,
    cli,
    run,
)
from market_research.studies.cffex_option_expiry_dte_collection.study import (
    CollectionInvalidRequestError,
)
from observation_support import CalendarDouble, OptionsDouble, row
from test_observation_runtime import make_chain, make_universe

ROOT = Path(__file__).resolve().parents[2]
START, END = date(2025, 10, 1), date(2025, 12, 31)
EXPIRIES = (date(2025, 10, 23), date(2025, 11, 20), date(2025, 12, 19))
REQUEST = CollectionRequest("MO", START, END, 15)
ARGS = [
    "--product-code",
    "MO",
    "--expiry-start-date",
    "2025-10-01",
    "--expiry-end-date",
    "2025-12-31",
    "--target-dte",
    "15",
]


def forbidden() -> Any:
    pytest.fail("unneeded dependency factory must not run")


def artifacts(tmp_path: Path, expiries: tuple[date, ...] = EXPIRIES) -> tuple[Any, dict[date, Any]]:
    discovery = OptionsDouble((START,), tuple(row(expiry, START) for expiry in expiries))
    universe = make_universe(tmp_path / "u.sqlite3", discovery).ensure(
        ExpiryUniverseRequest("MO", START, END),
    )
    values = {}
    for expiry in expiries:
        values[expiry] = make_chain(
            tmp_path / "c.sqlite3",
            OptionsDouble((START,), (row(expiry, START),)),
            CalendarDouble((START,)),
        ).ensure(
            ExpiryDteChainRequest("MO", expiry, 15),
        )
    return universe, values


class UniverseDouble:
    def __init__(self, value: Any):
        self.value = value
        self.calls: list[ExpiryUniverseRequest] = []

    def ensure(self, request: ExpiryUniverseRequest) -> Any:
        self.calls.append(request)
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


class ChainDouble:
    def __init__(self, values: dict[date, Any]):
        self.values = values
        self.calls: list[ExpiryDteChainRequest] = []

    def ensure(self, request: ExpiryDteChainRequest) -> Any:
        self.calls.append(request)
        value = self.values[request.expiry_date]
        if isinstance(value, Exception):
            raise value
        return value


def execute(universe: UniverseDouble, chain: ChainDouble) -> Any:
    return run(
        REQUEST,
        universe_factory=lambda: cast(ExpiryUniverseService, universe),
        chain_factory=lambda: cast(ExpiryDteChainService, chain),
    )


def test_exact_bindings_and_success_outcome(tmp_path: Path) -> None:
    universe, values = artifacts(tmp_path)
    u, c = UniverseDouble(universe), ChainDouble(values)
    outcome = execute(u, c)
    assert u.calls == [ExpiryUniverseRequest("MO", START, END)]
    assert c.calls == [ExpiryDteChainRequest("MO", expiry, 15) for expiry in EXPIRIES]
    assert (
        outcome.status,
        outcome.discovered_expiry_count,
        outcome.planned_observation_count,
        outcome.completed_observation_count,
        outcome.failed_observation_count,
    ) == (
        "success",
        3,
        3,
        3,
        0,
    )
    assert outcome.product_code == "MO" and outcome.target_dte == 15
    assert outcome.failures == () and not hasattr(outcome, "rows")
    assert REQUEST == CollectionRequest("MO", START, END, 15)


def test_empty_universe_never_constructs_chain(tmp_path: Path) -> None:
    universe, _ = artifacts(tmp_path, ())
    u = UniverseDouble(universe)
    outcome = run(
        REQUEST, universe_factory=lambda: cast(ExpiryUniverseService, u), chain_factory=forbidden
    )
    assert outcome.status == "success"
    assert (
        outcome.discovered_expiry_count,
        outcome.planned_observation_count,
        outcome.completed_observation_count,
        outcome.failed_observation_count,
    ) == (0, 0, 0, 0)


@pytest.mark.parametrize("failure", ["construction", "operation", "partial", "mismatch", "invalid"])
def test_universe_failure_has_unknown_counts_and_no_chain(tmp_path: Path, failure: str) -> None:
    artifact, _ = artifacts(tmp_path, ())
    value = {
        "operation": ObservationOperationError("universe unavailable"),
        "partial": replace(artifact, complete=False),
        "mismatch": replace(artifact, product_code="IO"),
        "invalid": object(),
    }.get(failure)

    def factory() -> ExpiryUniverseService:
        if failure == "construction":
            raise ObservationOperationError("construction failed")
        return cast(ExpiryUniverseService, UniverseDouble(value))

    outcome = run(REQUEST, universe_factory=factory, chain_factory=forbidden)
    assert outcome.status == "failure"
    assert outcome.discovered_expiry_count is None and outcome.planned_observation_count is None
    assert outcome.completed_observation_count == outcome.failed_observation_count == 0
    assert outcome.failures[0].stage == "ensure_expiry_universe"
    assert outcome.failures[0].expiry_date is None


def test_plan_failure_preserves_discovered_count(tmp_path: Path) -> None:
    artifact, _ = artifacts(tmp_path)
    u = UniverseDouble(replace(artifact, expiries=tuple(reversed(EXPIRIES))))
    outcome = run(
        REQUEST, universe_factory=lambda: cast(ExpiryUniverseService, u), chain_factory=forbidden
    )
    assert outcome.status == "failure" and outcome.discovered_expiry_count == 3
    assert outcome.planned_observation_count is None
    assert outcome.failures[0].stage == "build_runtime_expiry_plan"


@pytest.mark.parametrize("failure", ["operation", "partial", "mismatch", "invalid"])
def test_chain_failures_continue_every_entry_once(tmp_path: Path, failure: str) -> None:
    universe, values = artifacts(tmp_path)
    for expiry in EXPIRIES[:2]:
        artifact = values[expiry]
        values[expiry] = {
            "operation": ObservationOperationError(f"failed {expiry}"),
            "partial": replace(artifact, complete=False),
            "mismatch": replace(artifact, target_dte=30),
            "invalid": object(),
        }[failure]
    u, c = UniverseDouble(universe), ChainDouble(values)
    outcome = execute(u, c)
    assert outcome.status == "failure"
    assert outcome.planned_observation_count == 3
    assert outcome.completed_observation_count == 1 and outcome.failed_observation_count == 2
    assert [request.expiry_date for request in c.calls] == list(EXPIRIES)
    assert [failure.expiry_date for failure in outcome.failures] == list(EXPIRIES[:2])
    assert all(failure.stage == "ensure_expiry_chains" for failure in outcome.failures)
    assert all(failure.reason for failure in outcome.failures)


def test_chain_factory_failure_continues_different_requests(tmp_path: Path) -> None:
    artifact, values = artifacts(tmp_path)
    u, c = UniverseDouble(artifact), ChainDouble(values)
    attempts = []

    def factory() -> ExpiryDteChainService:
        attempts.append(True)
        if len(attempts) == 1:
            raise ObservationOperationError("chain construction failed")
        return cast(ExpiryDteChainService, c)

    outcome = run(
        REQUEST, universe_factory=lambda: cast(ExpiryUniverseService, u), chain_factory=factory
    )
    assert len(attempts) == 2
    assert [request.expiry_date for request in c.calls] == list(EXPIRIES[1:])
    assert outcome.failed_observation_count == 1 and outcome.completed_observation_count == 2
    assert outcome.failures[0].expiry_date == EXPIRIES[0]


def test_interruption_propagates(tmp_path: Path) -> None:
    def interrupt() -> ExpiryUniverseService:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run(REQUEST, universe_factory=interrupt, chain_factory=forbidden)


@pytest.mark.parametrize(
    "values",
    [
        ("mo", START, END, 15),
        ("MO ", START, END, 15),
        ("MO", END, START, 15),
        ("MO", str(START), END, 15),
        ("MO", datetime(2025, 10, 1), END, 15),
        ("MO", START, END, True),
        ("MO", START, END, 0),
        ("MO", START, END, 15.0),
    ],
)
def test_invalid_study_request(values: tuple[Any, ...]) -> None:
    with pytest.raises(CollectionInvalidRequestError):
        CollectionRequest(*values)
    with pytest.raises(CollectionInvalidRequestError):
        run(cast(Any, object()), universe_factory=forbidden, chain_factory=forbidden)


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--help"],
        ARGS[:-2],
        [*ARGS, "--output", "x"],
        [*ARGS, "--overwrite"],
        [*ARGS, "--database", "x"],
        [*ARGS, "--sqlite-path", "x"],
        [*ARGS, "--resume"],
        [*ARGS[:2], "--expiry-start-date", "20251001", *ARGS[4:]],
        [*ARGS[:2], "--expiry-start-date", "2025-02-30", *ARGS[4:]],
        [*ARGS[:-1], "0"],
        [*ARGS[:-1], "1.5"],
        [*ARGS[:-1], "+15"],
    ],
)
def test_cli_help_and_invalid_parse_zero_dependencies(
    args: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "create_universe_service", forbidden)
    monkeypatch.setattr(cli, "create_chain_service", forbidden)
    with pytest.raises(SystemExit) as exited:
        cli.main(args)
    assert exited.value.code == (0 if args == ["--help"] else 2)


def test_cli_semantic_admission_precedes_composition(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "create_universe_service", forbidden)
    monkeypatch.setattr(cli, "create_chain_service", forbidden)
    assert cli.main(["--product-code", "mo", *ARGS[2:]]) == 2
    assert "invalid Study request" in capsys.readouterr().err


@pytest.mark.parametrize("kind", ["success", "empty", "chain_failure", "universe_failure"])
def test_cli_presentation_exit_codes_and_no_output_files(
    tmp_path: Path, kind: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    artifact, values = artifacts(tmp_path, () if kind == "empty" else EXPIRIES)
    before = {path for path in tmp_path.rglob("*")}
    u = UniverseDouble(
        ObservationOperationError("universe unavailable")
        if kind == "universe_failure"
        else artifact
    )
    if kind == "chain_failure":
        values[EXPIRIES[0]] = ObservationOperationError("chain unavailable")
    c = ChainDouble(values)
    monkeypatch.setattr(cli, "create_universe_service", lambda: u)
    monkeypatch.setattr(cli, "create_chain_service", forbidden if kind == "empty" else lambda: c)
    monkeypatch.chdir(tmp_path)
    code = cli.main(ARGS)
    text = capsys.readouterr().out
    assert code == (1 if "failure" in kind else 0)
    assert f"status={'failure' if code else 'success'}" in text
    assert "product_code=MO" in text and "target_dte=15" in text
    if kind == "universe_failure":
        assert "discovered_expiry_count=unavailable" in text
        assert "planned_observation_count=unavailable" in text
        assert "stage=ensure_expiry_universe" in text
    if kind == "chain_failure":
        assert "expiry_date=2025-10-23" in text and "failed_observation_count=1" in text
    assert "Traceback" not in text and "contract_code" not in text
    assert {path for path in tmp_path.rglob("*")} == before


def test_study_source_only_consumes_public_observation_values() -> None:
    source = ROOT / "market-research/src/market_research/studies/cffex_option_expiry_dte_collection"
    assert {path.name for path in source.glob("*.py")} == {"__init__.py", "cli.py", "study.py"}
    allowed = {
        "market_research.observations",
        "market_research.observations.cffex_option_expiry_universe",
        "market_research.observations.cffex_option_expiry_dte_chain",
    }
    forbidden_roots = {"data_lake", "market_snapshot", "sqlite3", "tushare", "pathlib", "json"}
    for path in source.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for name in names:
                assert name.split(".")[0] not in forbidden_roots
                if name.startswith("market_research.observations"):
                    assert name in allowed
        text = path.read_text(encoding="utf-8")
        assert not any(
            word in text for word in ("load_config", "execute_run", "canonical_run_directory")
        )


def test_installed_lab_discovery_help_and_exit_propagation() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "lab.cli", "research", "list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "cffex-option-expiry-dte-collection" in result.stdout.splitlines()
    base = [
        sys.executable,
        "-m",
        "lab.cli",
        "research",
        "run",
        "cffex-option-expiry-dte-collection",
    ]
    help_result = subprocess.run([*base, "--help"], cwd=ROOT, capture_output=True, text=True)
    assert help_result.returncode == 0 and "--target-dte" in help_result.stdout
    invalid = subprocess.run([*base, "--target-dte", "0"], cwd=ROOT, capture_output=True, text=True)
    assert invalid.returncode == 2 and "Traceback" not in invalid.stderr
