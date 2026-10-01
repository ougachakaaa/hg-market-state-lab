"""Calendar source ownership, provider confinement and installed public imports."""

import ast
import json
import subprocess
import sys
import tomllib
from pathlib import Path

from data_lake.datasets import tushare_trade_calendar as public

DATASET_ROOT = Path(__file__).resolve().parents[1]
ROOT = DATASET_ROOT.parents[2]
SOURCE = DATASET_ROOT / "src/data_lake/datasets/tushare_trade_calendar"


def test_dataset_physically_owns_source_and_depends_on_shared_kernel() -> None:
    assert Path(public.__file__).resolve() == SOURCE / "__init__.py"
    assert not list((ROOT / "data-lake/src/data_lake/datasets").rglob("*.py"))
    names = {
        node.module
        for path in SOURCE.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert {"data_lake._application", "data_lake._repository", "data_lake._runtime"} <= names


def test_provider_dependency_is_confined_to_owned_source_adapter() -> None:
    for path in SOURCE.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module]
                if isinstance(node, ast.ImportFrom) and node.module
                else []
            )
            if any(name.split(".")[0] == "tushare" for name in names):
                assert path == SOURCE / "_source.py"


def test_public_import_works_in_installed_isolated_interpreter(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import json, data_lake; "
            "import data_lake.datasets.tushare_trade_calendar as calendar; "
            "print(json.dumps([data_lake.__file__, calendar.__file__, "
            "calendar.TradeCalendarRange.__module__]))",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    core_path, calendar_path, request_module = json.loads(result.stdout)
    assert Path(core_path).resolve() == ROOT / "data-lake/src/data_lake/__init__.py"
    assert Path(calendar_path).resolve() == SOURCE / "__init__.py"
    assert request_module == "data_lake.datasets.tushare_trade_calendar._models"


def test_root_tools_cover_dataset_source_and_tests() -> None:
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    tools = manifest["tool"]
    source = (DATASET_ROOT / "src").relative_to(ROOT).as_posix()
    tests = (DATASET_ROOT / "tests").relative_to(ROOT).as_posix()
    assert {"include": "data_lake", "from": source} in tools["poetry"]["packages"]
    assert source in tools["pytest"]["ini_options"]["pythonpath"]
    assert tests in tools["pytest"]["ini_options"]["testpaths"]
    assert {source, tests} <= set(tools["ruff"]["src"])
    assert {source, tests} <= set(tools["mypy"]["files"])
    assert source in tools["mypy"]["mypy_path"]
    assert tools["mypy"]["namespace_packages"] and tools["mypy"]["explicit_package_bases"]
