"""Canonical Research UI configuration loading."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
CANONICAL_CONFIG_PATH = REPOSITORY_ROOT / "market-research" / "research.toml"


class ResearchConfigError(ValueError):
    """The canonical Research configuration is unavailable or invalid."""


@dataclass(frozen=True)
class ResearchConfig:
    source: Path
    output_root: Path


def _validate_schema(payload: Any) -> str:
    if not isinstance(payload, dict) or set(payload) != {"output"}:
        raise ResearchConfigError("config must contain only the [output] section.")
    output = payload["output"]
    if not isinstance(output, dict) or set(output) != {"root"}:
        raise ResearchConfigError("[output] must contain only the required root key.")
    root = output["root"]
    if not isinstance(root, str):
        raise ResearchConfigError("output.root must be a string path.")
    root = root.strip()
    if not root:
        raise ResearchConfigError("output.root must not be empty.")
    if "\x00" in root:
        raise ResearchConfigError("output.root is not a valid filesystem path.")
    return root


def load_config() -> ResearchConfig:
    """Load and fully validate the repository's canonical V1 config."""
    try:
        with CANONICAL_CONFIG_PATH.open("rb") as stream:
            payload = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ResearchConfigError(
            f"cannot read {CANONICAL_CONFIG_PATH.resolve()}: {exc}"
        ) from exc

    raw_root = _validate_schema(payload)
    try:
        configured = Path(raw_root)
        output_root = configured if configured.is_absolute() else REPOSITORY_ROOT / configured
        output_root = output_root.resolve(strict=False)
    except (OSError, ValueError) as exc:
        raise ResearchConfigError(f"cannot resolve output.root: {exc}") from exc
    if not output_root.is_absolute():
        raise ResearchConfigError("output.root did not resolve to an absolute path.")
    return ResearchConfig(
        source=CANONICAL_CONFIG_PATH.resolve(strict=False),
        output_root=output_root,
    )
