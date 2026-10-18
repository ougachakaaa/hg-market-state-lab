"""Tests for the canonical strict Research UI configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from market_research.ui import configuration


def configure_location(monkeypatch: pytest.MonkeyPatch, root: Path, text: str) -> Path:
    path = root / "market_research" / "research.toml"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", root)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", path)
    return path


def test_canonical_config_resolves_relative_output_from_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = configure_location(
        monkeypatch, tmp_path, '[output]\nroot = "market_research/output"\n'
    )

    result = configuration.load_config()

    assert result.source == source.resolve()
    assert result.output_root == (tmp_path / "market_research/output").resolve()


def test_absolute_output_root_is_normalized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    absolute = tmp_path / "somewhere" / ".." / "retained"
    configure_location(monkeypatch, tmp_path, f"[output]\nroot = '{absolute}'\n")

    assert configuration.load_config().output_root == absolute.resolve()


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("not toml =", "cannot read"),
        ('root = "output"\n', r"only the \[output\]"),
        ("[output]\n", "required root"),
        ("[output]\nroot = 3\n", "string path"),
        ('[output]\nroot = "   "\n', "must not be empty"),
        ('[output]\nroot = "output"\nextra = true\n', "only the required root"),
        ('[output]\nroot = "output"\n[other]\nvalue = 1\n', r"only the \[output\]"),
    ],
)
def test_invalid_config_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    text: str,
    message: str,
) -> None:
    configure_location(monkeypatch, tmp_path, text)

    with pytest.raises(configuration.ResearchConfigError, match=message):
        configuration.load_config()


def test_unreadable_or_missing_canonical_config_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", tmp_path / "missing.toml")

    with pytest.raises(configuration.ResearchConfigError, match="cannot read"):
        configuration.load_config()


def test_invalid_filesystem_representation_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure_location(monkeypatch, tmp_path, '[output]\nroot = "bad\\u0000path"\n')

    with pytest.raises(configuration.ResearchConfigError, match="valid filesystem"):
        configuration.load_config()
