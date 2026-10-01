"""DataLake shared kernel and module dependency boundaries."""

import ast
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data-lake/src"
DATASETS = ROOT / "data-lake/datasets"


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
    for source_root in (SOURCE, *(DATASETS.glob("*/src"))):
        for path in source_root.rglob("*.py"):
            assert not any(
                name.split(".")[0] in forbidden for name in imports(path, source_root)
            ), path


def test_shared_kernel_has_no_dataset_or_provider_dependencies() -> None:
    assert not list((SOURCE / "data_lake/datasets").rglob("*.py"))
    for path in SOURCE.rglob("*.py"):
        assert not any(
            name == "data_lake.datasets"
            or name.startswith("data_lake.datasets.")
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
                for name in imports(path, source_root)
            ), path


def test_no_consumer_imports_datalake_internals() -> None:
    for directory in ("lab", "backend-api/src", "market-snapshot/src", "market-research/src"):
        scan_root = ROOT / directory
        source_root = ROOT if directory == "lab" else scan_root
        for path in scan_root.rglob("*.py"):
            if "tests" in path.parts:
                continue
            assert not any(
                name.startswith("data_lake.")
                and any(part.startswith("_") for part in name.split(".")[1:])
                for name in imports(path, source_root)
            ), path


def test_owned_runtime_directories_are_ignored() -> None:
    paths = [
        "data-lake/data/legacy.sqlite3",
        "data-lake/datasets/tushare_trade_calendar/data/tushare_trade_calendar.sqlite3",
        "data-lake/datasets/tushare_trade_calendar/data/tushare_trade_calendar.sqlite3-wal",
        "data-lake/datasets/tushare_trade_calendar/data/tushare_trade_calendar.sqlite3-shm",
    ]
    result = subprocess.run(
        ["git", "check-ignore", "-z", "--stdin"],
        input="\0".join(paths) + "\0",
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.rstrip("\0").split("\0") == paths
