"""Export or check the product-local OpenAPI documents consumed by ui_web."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WEB_UI_ROOT = REPOSITORY_ROOT / "ui_web"
BACKEND_API_ROOT = REPOSITORY_ROOT / "ui_http"

sys.path.insert(0, str(BACKEND_API_ROOT / "src"))

from ui_http.app import create_app as create_application  # noqa: E402
from ui_http.products.mo_option_chain.app import (  # noqa: E402
    create_app as create_chain_app,
)
from ui_http.products.mo_option_premium.app import (  # noqa: E402
    create_app as create_premium_app,
)


def create_projection(paths: set[str]) -> FastAPI:
    """Project selected operations and their transitive schemas from the offline runtime."""
    app = create_application()
    document = app.openapi()
    document["paths"] = {
        path: operations for path, operations in document["paths"].items()
        if path in paths
    }
    schemas = document["components"]["schemas"]
    needed: set[str] = set()

    def collect(value: object) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref", "")
            prefix = "#/components/schemas/"
            if isinstance(ref, str) and ref.startswith(prefix):
                name = ref.removeprefix(prefix)
                if name not in needed:
                    needed.add(name)
                    collect(schemas[name])
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(document["paths"])
    # FastAPI qualifies colliding model names across sibling products. Keep local
    # names stable when the selected operation closure contains only one such title;
    # this is a ref-preserving projection, never a competing schema definition.
    titles = [schemas[name].get("title", name) for name in needed]
    names = {
        name: schemas[name].get("title", name)
        if "__" in name and titles.count(schemas[name].get("title", name)) == 1
        and schemas[name].get("title", name) not in needed else name
        for name in needed
    }

    def local_refs(value: object) -> object:
        if isinstance(value, dict):
            result = {key: local_refs(child) for key, child in value.items()}
            ref = value.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                result["$ref"] = "#/components/schemas/" + names[ref.rsplit("/", 1)[1]]
            return result
        if isinstance(value, list):
            return [local_refs(child) for child in value]
        return value

    document["paths"] = local_refs(document["paths"])
    projected = {names[name]: local_refs(schemas[name]) for name in needed}
    document["components"]["schemas"] = dict(sorted(projected.items()))
    app.openapi = lambda: document  # type: ignore[method-assign]
    return app


def create_auth_app() -> FastAPI:
    return create_projection({
        "/auth/mode",
        "/auth/register",
        "/auth/login",
        "/auth/me",
        "/auth/logout",
    })


def create_research_app() -> FastAPI:
    return create_projection({
        "/research/publications",
        "/research/publications/{publication_id}",
        "/research/publications/{publication_id}/analyses/{analysis_id}",
        "/research/publications/{publication_id}/views/{view_id}",
    })


def create_research_catalog_app() -> FastAPI:
    return create_projection({
        "/research/capabilities",
        "/research/capabilities/{id}",
    })


def create_futures_basis_app() -> FastAPI:
    return create_projection({
        "/research/futures-basis/preflight",
        "/research/futures-basis/runs",
        "/research/futures-basis/runs/{run_id}",
        "/research/futures-basis/runs/{run_id}/report",
    })


def create_backtesting_app() -> FastAPI:
    return create_projection({
        "/backtesting/futures-roll/preflight",
        "/backtesting/futures-roll/runs",
        "/backtesting/futures-roll/runs/{run_id}",
        "/backtesting/futures-roll/runs/{run_id}/result",
    })


def create_calendar_spread_daily_app() -> FastAPI:
    return create_projection({
        "/data/futures-calendar-spread", "/data/futures-calendar-spread/query",
    })


def create_calendar_spread_relative_value_app() -> FastAPI:
    return create_projection({"/research/calendar-spread-relative-value/query"})


CONTRACTS: tuple[tuple[str, Callable[[], FastAPI], Path], ...] = (
    ("Futures Calendar Spread", create_calendar_spread_daily_app,
     WEB_UI_ROOT / "src/features/futures_calendar_spread/api/calendarSpread.openapi.json"),
    ("Calendar Spread Relative Value", create_calendar_spread_relative_value_app,
     WEB_UI_ROOT / "src/features/calendar_spread_relative_value/api/relativeValue.openapi.json"),
    (
        "Backtesting",
        create_backtesting_app,
        WEB_UI_ROOT / "src/features/backtesting/api/backtesting.openapi.json",
    ),
    (
        "Futures Basis Research",
        create_futures_basis_app,
        WEB_UI_ROOT / "src/features/futures_basis_research/api/futuresBasis.openapi.json",
    ),
    (
        "Application Authentication",
        create_auth_app,
        WEB_UI_ROOT / "src/app/auth/api/auth.openapi.json",
    ),
    (
        "Research Publication",
        create_research_app,
        WEB_UI_ROOT / "src/features/research_explorer/api/research.openapi.json",
    ),
    (
        "Research Catalog",
        create_research_catalog_app,
        WEB_UI_ROOT / "src/features/research_catalog/api/catalog.openapi.json",
    ),
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
        description="Export or check every OpenAPI document consumed by ui_web."
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
