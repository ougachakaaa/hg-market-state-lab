"""Enforce the isolated pure numerical module and root installation boundary."""

import ast
import subprocess
import sys
import tomllib
from dataclasses import fields
from pathlib import Path

from market_statistics import NumericSample

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "market_statistics/src/market_statistics"


def test_statistics_imports_only_approved_numerical_and_standard_dependencies() -> None:
    allowed = {"collections", "dataclasses", "math", "typing", "warnings", "numpy"}
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                assert node.attr != "random", path
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in allowed for alias in node.names), path
            elif isinstance(node, ast.ImportFrom) and not node.level:
                assert node.module is not None and node.module.split(".")[0] in allowed, path
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in {"open", "eval", "exec", "__import__"}, path
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in {
                        "load",
                        "save",
                        "loadtxt",
                        "savetxt",
                        "fromfile",
                        "tofile",
                        "memmap",
                        "random",
                        "default_rng",
                        "seed",
                    }, path
            elif isinstance(node, ast.ClassDef):
                forbidden = ("Registry", "Provider", "Engine")
                assert not any(word in node.name for word in forbidden), path
    assert {field.name for field in fields(NumericSample)} == {"values", "unit"}
    assert not (ROOT / "market_analyze").exists()


def test_root_packaging_and_all_tool_registrations() -> None:
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert {"include": "market_statistics", "from": "market_statistics/src"} in (
        manifest["tool"]["poetry"]["packages"]
    )
    assert any(dep.startswith("numpy (") for dep in manifest["project"]["dependencies"])
    pytest_config = manifest["tool"]["pytest"]["ini_options"]
    assert "market_statistics/tests" in pytest_config["testpaths"]
    assert "market_statistics/src" in pytest_config["pythonpath"]
    for config, key in ((manifest["tool"]["ruff"], "src"), (manifest["tool"]["mypy"], "files")):
        assert {"market_statistics/src", "market_statistics/tests"} <= set(config[key])
    assert "market_statistics/src" in manifest["tool"]["mypy"]["mypy_path"]


def test_installed_package_imports_without_application_modules() -> None:
    # Isolated mode ignores pytest's pythonpath and the current-directory namespace.
    program = """
import sys
import market_statistics as s
r = s.compute(s.NumericSample([1, 3], 'u'), s.QuantileSpec([.25]))
assert r.points_and_values == ((.25, 1.5),)
r = s.compute(s.NumericSample([0, 1, 2], 'u'), s.IntervalCountSpec([0, 2], 'u'))
assert r.bins[0].count == 3
for name in ('market_research', 'data_lake', 'data_snapshot', 'market_modeling',
             'ui_cli', 'ui_http', 'sqlite3'):
    assert name not in sys.modules, name
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", program], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
