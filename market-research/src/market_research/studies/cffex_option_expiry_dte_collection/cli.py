"""Four-input inbound adapter; no Study output configuration or persistence."""

import argparse
import re
import sys
from collections.abc import Sequence
from datetime import date

from market_research.observations.cffex_option_expiry_dte_chain import (
    create_service as create_chain_service,
)
from market_research.observations.cffex_option_expiry_universe import (
    create_service as create_universe_service,
)

from .study import CollectionInvalidRequestError, CollectionRequest, run


def _date(text: str) -> date:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text) is not None:
        try:
            return date.fromisoformat(text)
        except ValueError:
            pass
    raise argparse.ArgumentTypeError("date must be valid YYYY-MM-DD")


def _positive_integer(text: str) -> int:
    if re.fullmatch(r"[0-9]+", text) is not None:
        try:
            value = int(text)
            if value > 0:
                return value
        except ValueError:
            pass
    raise argparse.ArgumentTypeError("target-dte must be positive integer text")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lab research run cffex-option-expiry-dte-collection",
        description="Ensure durable option chains for all observed expiries in an expiry window.",
        allow_abbrev=False,
    )
    parser.add_argument("--product-code", required=True)
    parser.add_argument("--expiry-start-date", required=True, type=_date)
    parser.add_argument("--expiry-end-date", required=True, type=_date)
    parser.add_argument("--target-dte", required=True, type=_positive_integer)
    args = parser.parse_args(argv)
    try:
        request = CollectionRequest(
            args.product_code, args.expiry_start_date, args.expiry_end_date, args.target_dte
        )
    except CollectionInvalidRequestError as error:
        print(f"invalid Study request: {error}", file=sys.stderr)
        return 2
    outcome = run(
        request, universe_factory=create_universe_service, chain_factory=create_chain_service
    )
    print(
        f"product_code={outcome.product_code} "
        f"expiry_start_date={outcome.expiry_start_date.isoformat()} "
        f"expiry_end_date={outcome.expiry_end_date.isoformat()} target_dte={outcome.target_dte}"
    )
    print(f"status={outcome.status}")
    for name in (
        "discovered_expiry_count",
        "planned_observation_count",
        "completed_observation_count",
        "failed_observation_count",
    ):
        value = getattr(outcome, name)
        print(f"{name}={value if value is not None else 'unavailable'}")
    for failure in outcome.failures:
        expiry = (
            "" if failure.expiry_date is None else f" expiry_date={failure.expiry_date.isoformat()}"
        )
        print(f"stage={failure.stage}{expiry}: {failure.reason}")
    return 0 if outcome.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
