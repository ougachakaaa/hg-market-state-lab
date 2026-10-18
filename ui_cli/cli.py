"""Canonical repository command topology and dispatch."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import datalake, doctor, research, serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description="Repository operator commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check local development prerequisites.")
    serve_parser = subparsers.add_parser("serve", help="Run a development server.")
    serve_subparsers = serve_parser.add_subparsers(dest="service", required=True)
    serve_subparsers.add_parser("backend", help="Run the backend development server.")
    serve_subparsers.add_parser("frontend", help="Run the frontend development server.")

    research_parser = subparsers.add_parser(
        "research", help="Discover and run retained Research Studies."
    )
    research_subparsers = research_parser.add_subparsers(
        dest="research_command", required=True
    )
    research_subparsers.add_parser("list", help="List runnable retained Studies.")
    research_run_parser = research_subparsers.add_parser(
        "run",
        add_help=False,
        help="Forward execution to a study-local CLI.",
    )
    research_run_parser.add_argument("study_id", help="Stable retained Study ID.")
    research_run_parser.add_argument("study_args", nargs=argparse.REMAINDER)
    datalake.add_parser(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "datalake":
        return datalake.run(args)
    if args.command == "research":
        if args.research_command == "list":
            return research.research_list()
        return research.research_run(args.study_id, args.study_args)
    if args.command == "serve":
        return {"backend": serve.backend, "frontend": serve.frontend}[args.service]()
    return doctor.doctor()


if __name__ == "__main__":
    raise SystemExit(main())
