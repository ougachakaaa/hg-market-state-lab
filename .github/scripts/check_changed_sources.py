"""Lightweight CI only: lint and credential scan of changed, existing files."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> None:
    base = os.environ["DIFF_BASE"]
    head = os.environ["DIFF_HEAD"]
    if not base or set(base) == {"0"}:
        print("No comparison base: changed-source checks NOT VERIFIED; no full scan fallback")
        return
    paths = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "-z", base, head]
    ).decode().split("\0")
    paths = [path for path in paths if path and Path(path).is_file()]
    print(f"Checking {len(paths)} changed files", flush=True)
    python = [path for path in paths if path.endswith(".py")]
    web = [
        path for path in paths
        if path.startswith("ui_web/") and path.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs"))
    ]
    if python:
        subprocess.run(["ruff", "check", "--", *python], check=True)
    if web:
        subprocess.run(["npm", "ci", "--ignore-scripts"], cwd="ui_web", check=True)
        subprocess.run(["ui_web/node_modules/.bin/oxlint", "--", *web], check=True)
    # Does not load dependencies, acquire market data, build or check payload hashes.
    subprocess.run(
        ["node", "ui_web/scripts/public_asset_safety.mjs", "--credentials-only", *paths],
        check=True,
    )


if __name__ == "__main__":
    main()
