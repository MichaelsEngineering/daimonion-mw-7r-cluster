"""Memo normalization utilities."""

from __future__ import annotations

from pathlib import Path


def normalize_markdown_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    normalized = "\n".join(lines)
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def normalize_markdown_file(source: Path, destination: Path) -> None:
    destination.write_text(
        normalize_markdown_text(source.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
