"""Export or check the product-local OpenAPI documents consumed by web-ui."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WEB_UI_ROOT = REPOSITORY_ROOT / "web-ui"
MARKET_SNAPSHOT_ROOT = REPOSITORY_ROOT / "market-snapshot"

sys.path.insert(0, str(MARKET_SNAPSHOT_ROOT / "src"))

from daily_market_snapshot.api.app import contract_openapi  # noqa: E402
from daily_market_snapshot.products.mo_option_chain.api.app import (  # noqa: E402
    create_app as create_chain_app,
)
from daily_market_snapshot.products.mo_option_premium.api.endpoint import (  # noqa: E402
    router as premium_router,
)


def create_premium_app() -> FastAPI:
    """Build an OpenAPI-only application around the backend-owned Premium router."""
    application = FastAPI(
        title="hg-market-state-lab MO Premium Plane API",
        version="0.1.0",
        summary="Minimal HTTP delivery adapter for the MO Premium Plane contract.",
    )
    application.openapi = contract_openapi(application)  # type: ignore[method-assign]
    application.include_router(premium_router)
    return application


CONTRACTS: tuple[tuple[str, Callable[[], FastAPI], Path], ...] = (
    (
        "MO Option Chain",
        create_chain_app,
        WEB_UI_ROOT
        / "src/features/mo_option_chain/api/moOptionChain.openapi.json",
    ),
    (
        "MO Premium Plane",
        create_premium_app,
        WEB_UI_ROOT
        / "src/features/mo_option_premium/api/moOptionPremium.openapi.json",
    ),
)


def serialized_openapi(create_app: Callable[[], FastAPI]) -> str:
    return json.dumps(
        create_app().openapi(), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export or check every OpenAPI document consumed by web-ui."
    )
    parser.add_argument(
        "--check", action="store_true", help="Fail if any committed document is stale."
    )
    args = parser.parse_args(argv)

    stale = False
    for name, create_app, output in CONTRACTS:
        content = serialized_openapi(create_app)
        if args.check:
            if not output.is_file() or output.read_text(encoding="utf-8") != content:
                print(f"Stale {name} OpenAPI: {output}", file=sys.stderr)
                stale = True
            else:
                print(f"{name} OpenAPI is current: {output}")
            continue

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8", newline="\n")
        print(f"Wrote {name} OpenAPI: {output}")

    return int(stale)


if __name__ == "__main__":
    raise SystemExit(main())
