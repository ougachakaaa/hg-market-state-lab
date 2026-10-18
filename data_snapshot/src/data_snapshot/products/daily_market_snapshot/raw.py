"""Daily Market Snapshot Raw path identity."""

from pathlib import Path

from ... import artifacts


def raw_dir(trade_date: str) -> Path:
    return artifacts.RAW_DIR / trade_date
