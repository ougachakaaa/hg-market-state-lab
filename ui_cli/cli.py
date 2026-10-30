"""Canonical repository command topology and dispatch."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import auth, datalake_parser, doctor, serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description="Repository operator commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check local development prerequisites.")
    serve_parser = subparsers.add_parser("serve", help="Run a development server.")
    serve_subparsers = serve_parser.add_subparsers(dest="service", required=True)
    serve_subparsers.add_parser("backend", help="Run the backend development server.")
    serve_subparsers.add_parser("frontend", help="Run the frontend development server.")

    datalake_parser.add_parser(subparsers)
    auth.add_parser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "auth":
        return auth.run(args)
    if args.command == "datalake":
        from . import datalake

        return datalake.run(args)
    if args.command == "serve":
        return {"backend": serve.backend, "frontend": serve.frontend}[args.service]()
    return doctor.doctor()


if __name__ == "__main__":
    raise SystemExit(main())
