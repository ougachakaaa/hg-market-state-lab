"""Thin executable shim of the Data Service CLI (semantic name ``dms``).

The CLI implementation lives in ``market_snapshot.cli``; this script only
makes it runnable without packaging the project.

Authority: ``services/delivery.md`` section 4.

    poetry run python market-snapshot/scripts/dms.py list
    poetry run python market-snapshot/scripts/dms.py get csi1000-5d-analysis --date 2026-09-18
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from market_snapshot.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
