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
BACKEND_API_ROOT = REPOSITORY_ROOT / "backend-api"

sys.path.insert(0, str(BACKEND_API_ROOT / "src"))

from backend_api.products.mo_option_chain.app import (  # noqa: E402
    create_app as create_chain_app,
)
from backend_api.products.mo_option_premium.app import (  # noqa: E402
    create_app as create_premium_app,
)


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
