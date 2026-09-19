"""Thin executable shim that runs the HTTP delivery adapter.

The application lives in ``daily_market_snapshot.api.app``; this script only makes
it runnable without packaging the project, exactly like ``scripts/dms.py`` does
for the CLI.

Authority: ``guides/mo-option-chain-http-contract.md``.

The adapter binds ``127.0.0.1:8011`` by default, which the repository README
documents as the local HTTP API address. The bind address is a launcher detail,
not part of the HTTP transport contract: it can be overridden with ``--host`` /
``--port``, and ``guides/mo-option-chain-http-contract.md`` section 8 leaves
server deployment to V1 non-goals.

    poetry run python scripts/api.py
    poetry run python scripts/api.py --host 127.0.0.1 --port 8011
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import uvicorn  # noqa: E402

from daily_market_snapshot.api import app  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="api", description="Serve the MO Option Chain HTTP API.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=8011, help="Bind port.")
    args = parser.parse_args(argv)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
