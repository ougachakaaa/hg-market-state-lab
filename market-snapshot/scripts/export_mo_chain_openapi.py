"""Export or check the MO Option Chain OpenAPI consumed by web-ui.

The FastAPI application is the executable HTTP wire contract. This script only
materializes its generated document; it does not define another schema.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "web-ui/src/features/mo_option_chain/api/moOptionChain.openapi.json"
)

sys.path.insert(0, str(PROJECT_ROOT / "src"))

from daily_market_snapshot.products.mo_option_chain.api.app import create_app  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export or check the MO Chain OpenAPI document.")
    parser.add_argument(
        "--check", action="store_true", help="Fail if the committed document is stale."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    content = json.dumps(
        create_app().openapi(), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    output: Path = args.output
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != content:
            print(f"Stale MO Chain OpenAPI: {output}", file=sys.stderr)
            return 1
        print(f"MO Chain OpenAPI is current: {output}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"Wrote MO Chain OpenAPI: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
