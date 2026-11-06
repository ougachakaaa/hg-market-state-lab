"""R01-A offline operator entry; run from repository root with Poetry."""

import argparse
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest,
    InputPreparationError,
    ObservationConstructionError,
    ReportRequest,
    compose_report,
    construct_observations,
    load_prepared_inputs,
    observe_futures_basis,
    replay_delivery,
    verify_delivery,
    write_evidence,
)
from market_research.descriptive.cases.futures_basis.evidence import (
    digest,
    encode,
    safe_reason,
    seal_delivery,
    write_json,
)
from market_statistics import IntervalCountSpec, QuantileSpec

ROOT = Path(__file__).resolve().parents[2]


def runtime_context() -> dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

    return dict(
        python=platform.python_version(),
        revision=git("rev-parse", "HEAD"),
        dirty=bool(git("status", "--porcelain")),
        packages={
            d.metadata["Name"]: d.version
            for d in importlib.metadata.distributions()
            if d.metadata["Name"]
        },
        frontend_packages={
            name: json.loads((ROOT / "ui_web/node_modules" / name / "package.json").read_bytes())[
                "version"
            ]
            for name in ("react", "react-dom", "antd", "plotly.js", "react-plotly.js", "vite")
        },
        node=subprocess.check_output(["node", "--version"], text=True).strip(),
        locks={
            name: digest((ROOT / name).read_bytes())
            for name in ("poetry.lock", "ui_web/package-lock.json")
        },
    )


def reproduction(output: Path, command: list[str]) -> None:
    import shlex

    (output / "REPRODUCE.md").write_text(
        "# R01-A 历史基差研究复现\n\n在记录的代码 revision 和根 Poetry 环境中操作。"
        "HTML 可直接双击打开；浏览无需服务、网络或相邻文件。相邻证据用于审计和重放。\n\n"
        "原始生成命令（输出须改为新的仓库外目录）：\n\n```bash\n"
        + shlex.join(command)
        + "\n```\n\n"
        "校验文件摘要和关联：\n\n```bash\n"
        "poetry run python market_research/scripts/futures_basis_report.py verify "
        + shlex.quote(str(output))
        + "\n```\n\n"
        "仅从保留的输入重新构建和执行统计，不访问行情 Source 或缓存：\n\n```bash\n"
        "poetry run python market_research/scripts/futures_basis_report.py replay "
        + shlex.quote(str(output))
        + "\n```\n\n"
        "生成需要根 Python 依赖和 ui_web/node_modules；离线浏览只需要 report.html。"
        "失败包没有可重放的成功研究。摘要并不认证行情来源或保证数据最新。\n\n"
        "若原始命令包含 --inputs，可将它替换为本目录的 inputs.canonical.json。"
        "迁移交付目录后，相应更新 verify / replay 的目录参数。\n",
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("verify", "replay"):
        parser = argparse.ArgumentParser()
        parser.add_argument("operation", choices=("verify", "replay"))
        parser.add_argument("directory", type=Path)
        args = parser.parse_args()
        result = (verify_delivery if args.operation == "verify" else replay_delivery)(
            args.directory
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    parser = argparse.ArgumentParser(description="R01-A 独立离线基差报告")
    parser.add_argument("--product", required=True)
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--quantile-points", type=json.loads, required=True)
    for metric in ("basis-value", "basis-ratio", "annualized-basis-ratio"):
        parser.add_argument(f"--{metric}-edges", type=json.loads, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, help="保留的 inputs.canonical.json；禁止行情 I/O")
    args = parser.parse_args()
    request = ReportRequest(
        FuturesBasisRequest(args.product, args.start, args.end),
        QuantileSpec(args.quantile_points),
        (
            IntervalCountSpec(args.basis_value_edges, "index_points"),
            IntervalCountSpec(args.basis_ratio_edges, "decimal_ratio"),
            IntervalCountSpec(args.annualized_basis_ratio_edges, "decimal_ratio"),
        ),
    )
    request.validate()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Output must be outside repository")
    output.mkdir(parents=True, exist_ok=False)
    reproduction(
        output,
        [
            "poetry",
            "run",
            "python",
            "market_research/scripts/futures_basis_report.py",
            *sys.argv[1:],
        ],
    )
    try:
        if args.inputs:
            try:
                prepared = load_prepared_inputs(args.inputs, request.observation)
            except (ValueError, TypeError, KeyError, OSError) as error:
                raise InputPreparationError(
                    "invalid_retained_input", "canonical_inputs", safe_reason(str(error))
                ) from error
            source = construct_observations(request.observation, prepared)
        else:
            source = observe_futures_basis(request.observation)
        report = compose_report(source, request)
        write_evidence(report, output, runtime=runtime_context())
    except (InputPreparationError, ObservationConstructionError) as exc:
        write_json(
            output / "failure.json",
            dict(
                request=encode(request),
                stage=exc.stage,
                category=exc.category,
                dependency=getattr(exc, "dependency", None),
                reason=safe_reason(exc.reason),
                attempts=encode(getattr(exc, "evidence", ())),
                prepared=encode(exc.prepared.attempts)
                if isinstance(exc, ObservationConstructionError)
                else None,
            ),
        )
        seal_delivery(output, "failed", None)
        print(f"研究阻塞：{exc.stage}/{exc.category}，诊断见 {output}", file=sys.stderr)
        return 1
    subprocess.run(
        ["node", "scripts/package_futures_basis_report.mjs", str(output)],
        cwd=ROOT / "ui_web",
        check=True,
    )
    seal_delivery(output, report.status, source.prepared.input_fingerprint)
    verify_delivery(output)
    print(f"{report.status}: {output / 'report.html'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(safe_reason(str(exc)), file=sys.stderr)
        sys.exit(1)
