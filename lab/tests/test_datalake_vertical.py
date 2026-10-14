"""CLI to real public services, isolated persistence and shared fake SDK boundary."""

import importlib
import json
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest

from data_lake.datasets.tushare_trade_calendar import _composition as calendar
from data_lake.providers.tushare import _executor
from lab.cli import main

IDS = (
    "tushare_trade_calendar",
    "tushare_index_daily",
    "tushare_equity_index_futures",
    "tushare_equity_index_options",
)


class Frame:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def to_dict(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.records


@pytest.mark.parametrize("dataset", IDS)
def test_real_cli_vertical_slice(
    dataset: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Reuse only fixture Source facts; runtime services/adapters are the real composition.
    fixtures: dict[str, Any] = {}
    for kind, identity in zip(("index", "futures", "options"), IDS[1:], strict=False):
        file = (
            Path(__file__).resolve().parents[2]
            / f"data-lake/datasets/{identity}/tests/test_{kind}_runtime.py"
        )
        spec = importlib.util.spec_from_file_location(f"fake_{kind}", file)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fixtures[kind] = module
    calls: list[str] = []

    class Client:
        def __getattr__(self, endpoint: str) -> Any:
            def request(**params: Any) -> Frame:
                with params.pop("dispatch")():
                    calls.append(endpoint)
                if endpoint == "trade_cal":
                    return Frame(
                        [
                            dict(
                                exchange=params["exchange"],
                                cal_date="20240102",
                                is_open=1,
                                pretrade_date="20231229",
                            )
                        ]
                    )
                kind = {"index": "index", "fut": "futures", "opt": "options"}[
                    endpoint.split("_")[0]
                ]
                source = fixtures[kind]
                if endpoint == "index_basic" and params["market"] != "SSE":
                    return Frame([])
                if params.get("fut_type") == "2":
                    return Frame([])
                facts = (
                    source.catalog()
                    if endpoint.endswith("basic")
                    else [source.daily(meta) for meta in source.catalog()]
                )
                offset = int(params.get("offset", 0))
                return Frame(facts[offset : offset + int(params.get("limit", 4000))])

            return request

    monkeypatch.setenv("TUSHARE_TOKEN", "fake")
    monkeypatch.setattr(_executor, "_states", {})
    monkeypatch.setattr(_executor, "create_client", lambda token: Client())
    # This suite tests lifecycle/delegation; real scheduling has a dedicated concurrency suite.
    monkeypatch.setattr(_executor._State, "dispatch", lambda self: nullcontext(0.0))
    modules = [calendar] + [
        importlib.import_module(f"data_lake.datasets.{identity}._composition")
        for identity in IDS[1:]
    ]
    for module in modules:
        monkeypatch.setattr(
            module, "database_path", lambda identity, root: tmp_path / f"{identity}.sqlite3"
        )
    args = {
        IDS[0]: ["--exchange", "SSE"],
        IDS[1]: ["--index-codes", "000300.SH"],
        IDS[2]: ["--product-codes", "IF"],
        IDS[3]: ["--product-codes", "IO"],
    }[dataset]
    args += ["--start-date", "2024-01-02", "--end-date", "2024-01-02"]
    assert main(["datalake", "ensure", dataset, *args]) == 0
    calls_before = list(calls)
    state_before = {path.name: path.read_bytes() for path in tmp_path.glob("*.sqlite3")}
    monkeypatch.delenv("TUSHARE_TOKEN")
    monkeypatch.setattr(
        _executor,
        "resolve_credential",
        lambda: pytest.fail("cached/read operation resolved credential"),
    )
    assert main(["datalake", "coverage", dataset, *args]) == 0
    assert main(["datalake", "ensure", dataset, *args]) == 0
    output = tmp_path / "view.json"
    assert main(["datalake", "export", dataset, *args, "--output", str(output)]) == 0
    view = json.loads(output.read_text(encoding="utf-8"))
    assert view["dataset"] == dataset and view["coverage"]["complete"] is True
    assert view["records"] and view["export_schema_version"] == (2 if dataset in IDS[2:] else 1)
    assert calls == calls_before
    assert {path.name: path.read_bytes() for path in tmp_path.glob("*.sqlite3")} == state_before


def test_all_namespaces_installed_outside_repo(tmp_path: Path) -> None:
    code = "import importlib; " + "; ".join(
        f"assert callable(importlib.import_module('data_lake.datasets.{identity}').create_service)"
        for identity in IDS
    )
    subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path, check=True)
