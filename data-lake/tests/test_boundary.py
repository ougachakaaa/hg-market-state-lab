"""DataLake shared kernel and module dependency boundaries."""

import ast
import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data-lake/src"
DATASETS = ROOT / "data-lake/datasets"
PROVIDERS = ROOT / "data-lake/providers"


def imports(path: Path, source_root: Path) -> set[str]:
    """Resolve absolute and relative imports, including from-import aliases."""
    parts = path.relative_to(source_root).with_suffix("").parts
    package = ".".join(parts[:-1])
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = (
                importlib.util.resolve_name("." * node.level + (node.module or ""), package)
                if node.level
                else node.module
            )
            if base:
                names.add(base)
                names.update(f"{base}.{alias.name}" for alias in node.names)
    return names


def test_datalake_has_no_consumer_dependencies() -> None:
    forbidden = {
        "market_snapshot",
        "market_research",
        "market_modeling",
        "backend_api",
        "lab",
        "fastapi",
    }
    for source_root in (SOURCE, *PROVIDERS.glob("*/src"), *DATASETS.glob("*/src")):
        for path in source_root.rglob("*.py"):
            assert not any(
                name.split(".")[0] in forbidden for name in imports(path, source_root)
            ), path


def test_shared_kernel_has_no_dataset_or_provider_dependencies() -> None:
    assert not list((SOURCE / "data_lake/datasets").rglob("*.py"))
    assert not (SOURCE / "data_lake/providers").exists()
    for path in SOURCE.rglob("*.py"):
        assert not any(
            name == "data_lake.datasets"
            or name.startswith("data_lake.datasets.")
            or name.startswith("data_lake.providers")
            or name.split(".")[0] == "tushare"
            for name in imports(path, SOURCE)
        ), path


def test_datasets_do_not_import_siblings() -> None:
    for dataset in DATASETS.iterdir():
        source_root = dataset / "src"
        if not source_root.is_dir():
            continue
        own = f"data_lake.datasets.{dataset.name}"
        for path in source_root.rglob("*.py"):
            assert not any(
                name.startswith("data_lake.datasets.")
                and name != own
                and not name.startswith(own + ".")
                and not (
                    dataset.name
                    in {
                        "tushare_index_daily",
                        "tushare_equity_index_futures",
                        "tushare_equity_index_options",
                    }
                    and name
                    in {
                        "data_lake.datasets.tushare_trade_calendar",
                        *(
                            f"data_lake.datasets.tushare_trade_calendar.{symbol}"
                            for symbol in (
                                "TradeCalendarRange",
                                "TradeCalendarService",
                                "TradeCalendarRecord",
                                "TradeCalendarExport",
                                "create_service",
                            )
                        ),
                    }
                )
                for name in imports(path, source_root)
            ), path


def test_no_consumer_imports_datalake_internals() -> None:
    for directory in (
        "lab",
        "backend-api/src",
        "market-snapshot/src",
        *(path.relative_to(ROOT).as_posix() for path in (ROOT / "market-research").glob("**/src")),
    ):
        scan_root = ROOT / directory
        source_root = ROOT if directory == "lab" else scan_root
        for path in scan_root.rglob("*.py"):
            if "tests" in path.parts:
                continue
            assert not any(
                name.startswith("data_lake.")
                and (
                    any(part.startswith("_") for part in name.split(".")[1:])
                    or name.startswith("data_lake.providers")
                    or name.split(".")[1] in {"domain", "application", "ports", "adapters"}
                )
                for name in imports(path, source_root)
            ), path


def test_owned_runtime_directories_are_ignored() -> None:
    paths = [
        "data-lake/data/legacy.sqlite3",
        "data-lake/datasets/tushare_trade_calendar/data/tushare_trade_calendar.sqlite3",
        "data-lake/datasets/tushare_trade_calendar/data/tushare_trade_calendar.sqlite3-wal",
        "data-lake/datasets/tushare_trade_calendar/data/tushare_trade_calendar.sqlite3-shm",
    ]
    for dataset in DATASETS.iterdir():
        paths.extend(
            f"data-lake/datasets/{dataset.name}/data/{dataset.name}.sqlite3{suffix}"
            for suffix in ("", "-wal", "-shm")
        )
    result = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        input="\0".join(paths) + "\0",
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.rstrip("\0").split("\0") == paths


def test_provider_is_separate_from_kernel_and_dataset_semantics() -> None:
    for source_root in PROVIDERS.glob("*/src"):
        for path in source_root.rglob("*.py"):
            names = imports(path, source_root)
            assert all(
                not name.startswith("data_lake.")
                or name.startswith("data_lake.providers.")
                or name
                in {
                    "data_lake.domain",
                    "data_lake.domain.ExecutionFailure",
                    "data_lake.results",
                    "data_lake.results.OperationError",
                }
                for name in names
            ), path
    for source_root in DATASETS.glob("*/src"):
        for path in source_root.rglob("*.py"):
            names = imports(path, source_root)
            assert not any(name.split(".")[0] in {"tushare", "dotenv"} for name in names), path
            assert "TUSHARE_TOKEN" not in path.read_text(), path
            if any(name.startswith("data_lake.providers") for name in names):
                assert path.name in {"_source.py", "_composition.py"}, path


@pytest.mark.parametrize(
    ("boundary", "allowed"),
    [
        ("domain", {"domain", "_serialization"}),
        ("ports", {"domain", "ports", "results"}),
        ("application", {"domain", "ports", "application", "results"}),
        ("adapters", {"domain", "ports", "adapters", "results", "_serialization"}),
    ],
)
def test_kernel_hexagonal_dependency_direction(boundary: str, allowed: set[str]) -> None:
    for path in (SOURCE / "data_lake" / boundary).rglob("*.py"):
        names = imports(path, SOURCE)
        assert all(
            name.split(".")[1] in allowed for name in names if name.startswith("data_lake.")
        ), path
        if boundary != "adapters":
            assert not any(
                name.split(".")[0] in {"sqlite3", "tushare", "requests", "httpx", "dotenv"}
                for name in names
            ), path


def test_dataset_domains_are_pure_and_sources_do_not_access_persistence() -> None:
    for dataset in DATASETS.iterdir():
        source_root = dataset / "src"
        package = source_root / "data_lake/datasets" / dataset.name
        if not package.is_dir():
            continue
        own = f"data_lake.datasets.{dataset.name}"
        for filename in ("_domain.py", "_models.py"):
            path = package / filename
            names = imports(path, source_root)
            assert all(
                not name.startswith("data_lake.")
                or name.split(".")[1] in {"domain", "results", "_serialization"}
                or name
                in {
                    "data_lake.CoverageResult",
                    "data_lake.ExportEnvelope",
                    "data_lake.InvalidRequestError",
                }
                or name == f"{own}._models"
                or name.startswith(f"{own}._models.")
                for name in names
            ), path
            assert not any(
                name.split(".")[0]
                in {"sqlite3", "tushare", "requests", "httpx", "dotenv", "os", "pathlib"}
                for name in names
            ), path
        names = imports(package / "_source.py", source_root)
        assert not any(
            name.startswith(("data_lake.adapters", "data_lake.application"))
            or name.split(".")[0] == "sqlite3"
            or name.startswith((f"{own}._service", f"{own}._composition"))
            or name == "data_lake.ports.Repository"
            for name in names
        ), package
