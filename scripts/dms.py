"""Data Service CLI (semantic name ``dms``).

Authority: ``guides/data-services.md`` (Data Service catalogue, CLI contract,
canonical output) over ``guides/csi1000-5d-analysis-data.md`` (Raw artifacts) and
``guides/csi1000-5d-analysis-snapshot.md`` (Snapshot Definition).

Semantics:

    dms list
    dms get <service_id> --date YYYY-MM-DD

First-version implementation surface, without becoming a Python package:

    poetry run python scripts/dms.py list
    poetry run python scripts/dms.py get csi1000-5d-analysis --date 2026-09-18

The catalogue is explicit and static; it is never discovered by scanning
directories.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _common  # noqa: E402
import build_snapshot  # noqa: E402
import fetch_csi1000_index_history as index_history  # noqa: E402
import fetch_im_futures_basic as im_futures_basic  # noqa: E402
import fetch_im_futures_daily as im_futures_daily  # noqa: E402
import fetch_mo_option_basic as mo_option_basic  # noqa: E402
import fetch_mo_option_daily as mo_option_daily  # noqa: E402

# The Snapshot Assembly module, reached through a binding so the CLI can be
# tested against a patched Builder.
_builder: ModuleType = build_snapshot

# The per-service implementation binding of a catalogue entry.
Orchestration = Callable[[_common.TushareApi, str], Path]


class DataServiceError(Exception):
    """Raised when a Data Service request cannot be completed as requested."""


@dataclass(frozen=True)
class DataService:
    """One catalogue entry: what the service is and how to execute it."""

    service_id: str
    description: str
    run: Orchestration


@dataclass(frozen=True)
class Stage:
    """One collection stage: the name it is reported under and its Raw artifact.

    ``raw_dataset`` is the Raw artifact name, which is not always the stage name:
    the CSI1000 history stage writes the ``index_daily_history`` artifact of the
    ``index_daily`` Dataset (see ``guides/csi1000-5d-analysis-data.md`` 8).
    """

    name: str
    raw_dataset: str
    collect: Callable[[], list[_common.RawRecord]]


def stage_query(api: _common.TushareApi, endpoint: str, **params: str) -> Any:
    """Bind one Source endpoint call so a Collector can query it.

    Tushare resolves endpoints dynamically, so the endpoint is looked up on the
    client instead of being named as a method of the protocol. ``params`` is the
    shared part of the request; a Collector that supplies its own value for one
    of those keys (the MO and IM collectors pass their product limit
    themselves) keeps the last word.
    """
    return lambda **kwargs: getattr(api, endpoint)(**(params | kwargs))


def collect_csi1000_5d_analysis(
    api: _common.TushareApi, target_trade_date: str, raw_root: Path
) -> Path:
    """Run the five CSI1000 analysis collection stages for one target trade date.

    Authority order (``guides/data-services.md`` section 5):

        CSI1000 history -> MO option basic -> MO option daily ->
        IM futures basic -> IM futures daily

    Each stage writes its own Raw artifact, named after its Dataset. A stage that
    raises ``CollectionError`` is reported as the failed stage and stops the
    chain, so no later Dataset is collected and no Snapshot is assembled.
    ``raw_root`` is passed in so a test can keep every Raw artifact in a
    temporary directory.
    """
    # The two contract universes are Source facts both the basic and the daily
    # Dataset of their product need, so they are read once here instead of being
    # requested twice. Both are part of the first stages of the chain, so a
    # failure is still reported before any Dataset is written.
    basic_options = mo_option_basic.query_opt_basic(api, mo_option_basic.EXCHANGE)
    basic_futures = im_futures_basic.query_fut_basic(
        api,
        exchange=im_futures_basic.EXCHANGE,
        fut_type=im_futures_basic.FUTURES_TYPE_ORDINARY,
        fut_code=im_futures_basic.PRODUCT,
    )

    # The stages of Guide section 5, in order. They run one at a time: a failing
    # stage must stop the chain before any later Dataset is collected.
    stages: tuple[Stage, ...] = (
        Stage(
            "csi1000_history",
            index_history.DATASET,
            lambda: index_history.collect_index_daily_history(
                target_trade_date, stage_query(api, "index_daily")
            ),
        ),
        Stage(
            "mo_option_basic",
            mo_option_basic.DATASET,
            lambda: mo_option_basic.collect_mo_option_basic(
                target_trade_date,
                stage_query(api, "opt_basic", exchange=mo_option_basic.EXCHANGE),
            ),
        ),
        Stage(
            "mo_option_daily",
            mo_option_daily.DATASET,
            lambda: mo_option_daily.collect_mo_option_daily(
                target_trade_date,
                basic_options,
                stage_query(api, "opt_daily", exchange=mo_option_basic.EXCHANGE),
            ),
        ),
        Stage(
            "im_futures_basic",
            im_futures_basic.DATASET,
            lambda: im_futures_basic.collect_im_futures_basic(
                target_trade_date,
                stage_query(
                    api,
                    "fut_basic",
                    exchange=im_futures_basic.EXCHANGE,
                    fut_type=im_futures_basic.FUTURES_TYPE_ORDINARY,
                    fut_code=im_futures_basic.PRODUCT,
                ),
            ),
        ),
        Stage(
            "im_futures_daily",
            im_futures_daily.DATASET,
            lambda: im_futures_daily.collect_im_futures_daily(
                target_trade_date, basic_futures, stage_query(api, "fut_daily")
            ),
        ),
    )

    dataset_dir = raw_root / _common.CSI1000_RAW_SUBDIR / target_trade_date
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for stage in stages:
        try:
            records = stage.collect()
        except _common.CollectionError as exc:
            raise DataServiceError(f"stage={stage.name} error={exc}") from exc
        _common.write_raw_dataset(records, dataset_dir, stage.raw_dataset)
    return dataset_dir


def run_csi1000_5d_analysis(api: _common.TushareApi, target_trade_date: str) -> Path:
    """Collect the five Raw artifacts and assemble the canonical Snapshot.

    Returns the path of the canonical Data Service artifact,
    ``output/csi1000-5d-analysis/<target_trade_date>/snapshot.json``.
    """
    return orchestrate_csi1000_5d_analysis(
        api, target_trade_date, _common.RAW_DIR, _common.OUTPUT_DIR
    )


def orchestrate_csi1000_5d_analysis(
    api: _common.TushareApi,
    target_trade_date: str,
    raw_root: Path,
    output_root: Path,
) -> Path:
    """Run the whole chain against explicit Raw and output roots."""
    dataset_dir = collect_csi1000_5d_analysis(api, target_trade_date, raw_root)
    try:
        snapshot = _builder.build_snapshot(target_trade_date, dataset_dir)
        return _builder.write_snapshot(snapshot, target_trade_date, output_root)
    except _builder.SnapshotError as exc:
        raise DataServiceError(f"stage=snapshot_assembly error={exc}") from exc


# guides/data-services.md section 2: the explicit, static, authority-driven
# catalogue. The first version holds exactly this one Data Service.
CATALOG: tuple[DataService, ...] = (
    DataService(
        service_id=_common.CSI1000_RAW_SUBDIR,
        description=(
            "analysis-ready data product for an external analyzer of the CSI1000 "
            "market state over the next ~5 trading days"
        ),
        run=run_csi1000_5d_analysis,
    ),
)


def find_service(service_id: str) -> DataService | None:
    """Return the catalogue entry of ``service_id``, or ``None`` if unsupported."""
    for service in CATALOG:
        if service.service_id == service_id:
            return service
    return None


def report_failure(service_id: str, target_trade_date: str, message: str) -> None:
    """Report a failed Data Service request on stderr."""
    print(f"service={service_id} date={target_trade_date} {message}", file=sys.stderr)


def command_list() -> int:
    """Print the catalogue: ``service_id`` and description of each entry."""
    for service in CATALOG:
        print(f"{service.service_id}\t{service.description}")
    return 0


def command_get(service_id: str, target_trade_date: str) -> int:
    """Run one explicit Data Service request for one target trade date.

    The date must be an explicit ``YYYY-MM-DD`` target trade date; there is no
    ``today`` / ``latest`` / fallback behaviour. An unsupported service or an
    invalid date fails before any Source execution.
    """
    service = find_service(service_id)
    if service is None:
        supported = ", ".join(entry.service_id for entry in CATALOG)
        report_failure(service_id, target_trade_date, f"unknown service_id; supported: {supported}")
        return 2
    if not _common.is_iso_date(target_trade_date):
        report_failure(
            service_id,
            target_trade_date,
            "invalid date; --date must be an explicit YYYY-MM-DD target_trade_date",
        )
        return 2

    try:
        api = _common.create_tushare_api(_common.get_tushare_token())
        output_path = service.run(api, target_trade_date)
    except (_common.CollectionError, DataServiceError) as exc:
        report_failure(service_id, target_trade_date, f"error={exc}")
        return 1

    print(
        json.dumps(
            {
                "service": service.service_id,
                "target_trade_date": target_trade_date,
                "output_path": str(output_path),
            }
        )
    )
    return 0


def command_for(args: argparse.Namespace) -> int:
    """Dispatch one parsed command."""
    if args.command == "list":
        return command_list()
    return command_get(args.service_id, args.target_trade_date)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dms", description="Request a Data Service for an explicit target trade date."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List the supported Data Services.")

    get_parser = subparsers.add_parser("get", help="Request one Data Service for one date.")
    get_parser.add_argument("service_id", help="Data Service id, as printed by 'dms list'.")
    get_parser.add_argument(
        "--date",
        required=True,
        dest="target_trade_date",
        metavar="YYYY-MM-DD",
        help="Explicit target_trade_date; no today / latest / fallback.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    return command_for(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
