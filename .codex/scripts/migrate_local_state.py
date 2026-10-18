"""Explicit no-overwrite copy of ignored state; see LOCAL_MIGRATION.md."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def assets(root: Path) -> list[tuple[Path, Path]]:
    pairs = [
        ("market-snapshot/.env", "data_snapshot/.env"),
        ("market-snapshot/data", "data_snapshot/data"),
        ("data-lake/data", "data_lake/data"),
        ("market-research/output", "market_research/output"),
    ]
    for owner in (root / "data-lake/datasets").glob("*/data"):
        pairs.append((owner.relative_to(root).as_posix(),
                      "data_lake/datasets/" + owner.parent.name + "/data"))
    for folder in ("data", "output"):
        for owner in (root / "market-research/observations").glob(f"*/{folder}"):
            pairs.append((owner.relative_to(root).as_posix(),
                          "market_research/observations/" + owner.parent.name + f"/{folder}"))
    files = []
    for old, new in pairs:
        source, target = root / old, root / new
        candidates = [source, *source.rglob("*")] if source.is_dir() else [source]
        for path in candidates:
            if any(p.is_symlink() for p in (path, *path.parents)):
                raise ValueError("Symlink in legacy assets; inspect and migrate manually")
            if path.is_file():
                destination = target if path == source else target / path.relative_to(source)
                if not destination.resolve().is_relative_to(root.resolve()):
                    raise ValueError("Destination escapes checkout")
                files.append((path, destination))
    return files


def digest(path: Path) -> bytes:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").digest()


def migrate(root: Path, *, apply: bool = False) -> int:
    files = assets(root)
    # Check all conflicts before creating any destination.
    for source, target in files:
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise ValueError("Symlink in destination; inspect and migrate manually")
        if target.exists() and (not target.is_file() or digest(source) != digest(target)):
            raise ValueError("Conflicting destination; preserve both copies and resolve manually")
    if apply:
        for source, target in files:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open("rb") as incoming, target.open("xb") as outgoing:
                    while chunk := incoming.read(1024 * 1024):
                        outgoing.write(chunk)
            if digest(source) != digest(target):
                raise ValueError("Copy verification failed; preserve sources and inspect")
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Copy and verify; never delete sources"
    )
    args = parser.parse_args()
    try:
        count = migrate(ROOT, apply=args.apply)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Local migration stopped: {error}\n")
    print(f"Legacy asset files: {count}. " +
          ("Copies verified; archive legacy sources outside checkout." if args.apply else
           "See LOCAL_MIGRATION.md before running operations."))
    return int(count > 0 and not args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
