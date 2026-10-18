"""Provider ownership and installed imports across the repository source roots."""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from data_lake.providers import tushare

PROVIDER_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROVIDER_ROOT.parents[2]
SOURCE = PROVIDER_ROOT / "src/data_lake/providers/tushare"


def test_provider_physically_owns_authority_source_and_tests() -> None:
    assert (PROVIDER_ROOT / "ARCHITECTURE.md").is_file()
    assert Path(tushare.__file__).resolve() == SOURCE / "__init__.py"
    assert not (ROOT / "data_lake/src/data_lake/providers").exists()
    assert not (ROOT / "data_lake/providers/TUSHARE.md").exists()
    for name in ("test_tushare_runtime.py", "test_tushare_http.py"):
        assert (PROVIDER_ROOT / "tests" / name).is_file()
        assert not (ROOT / "data_lake/tests" / name).exists()


def test_root_tools_cover_provider_source_and_tests() -> None:
    tools = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]
    source = (PROVIDER_ROOT / "src").relative_to(ROOT).as_posix()
    tests = (PROVIDER_ROOT / "tests").relative_to(ROOT).as_posix()
    assert {"include": "data_lake", "from": source} in tools["poetry"]["packages"]
    assert source in tools["pytest"]["ini_options"]["pythonpath"]
    assert tests in tools["pytest"]["ini_options"]["testpaths"]
    assert {source, tests} <= set(tools["ruff"]["src"])
    assert {source, tests} <= set(tools["mypy"]["files"])
    assert source in tools["mypy"]["mypy_path"]


def test_installed_provider_and_dataset_imports_and_fallback_from_independent_cwd(
    tmp_path: Path,
) -> None:
    script = """
import importlib
import json
import os
import data_lake
from data_lake.providers import tushare
from data_lake.providers.tushare import _client, _executor

datasets = [importlib.import_module('data_lake.datasets.' + name) for name in (
    'tushare_trade_calendar', 'tushare_index_daily',
    'tushare_equity_index_futures', 'tushare_equity_index_options',
)]
paths = []
def fake_dotenv(path):
    paths.append(str(path))
    return {'TUSHARE_TOKEN': 'test-fallback'}
os.environ.pop('TUSHARE_TOKEN', None)
_executor.dotenv_values = fake_dotenv
assert _executor.resolve_credential() == 'test-fallback'
assert tushare.TushareExecutor is _executor.TushareExecutor
assert tushare.Executor is _executor.Executor
assert not _executor._states
assert all(callable(module.create_service) for module in datasets)
print(json.dumps({
    'kernel': data_lake.__file__,
    'provider': [tushare.__file__, _executor.__file__, _client.__file__],
    'datasets': [module.__file__ for module in datasets],
    'fallback': paths,
}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    paths = json.loads(result.stdout)
    assert Path(paths["kernel"]).resolve() == ROOT / "data_lake/src/data_lake/__init__.py"
    assert [Path(path).resolve() for path in paths["provider"]] == [
        SOURCE / name for name in ("__init__.py", "_executor.py", "_client.py")
    ]
    assert [Path(path).resolve() for path in paths["datasets"]] == [
        ROOT / f"data_lake/datasets/{name}/src/data_lake/datasets/{name}/__init__.py"
        for name in (
            "tushare_trade_calendar",
            "tushare_index_daily",
            "tushare_equity_index_futures",
            "tushare_equity_index_options",
        )
    ]
    assert paths["fallback"] == [str(ROOT / "data_snapshot/.env")]
