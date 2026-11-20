"""Locate the protocol files: inside the wheel (_assets/) or in a source checkout."""

from __future__ import annotations

from pathlib import Path

# asset key -> path in a source checkout (relative to the repository root)
SOURCES = {
    "PROTOCOL.md": "PROTOCOL.md",
    "AGENTS.md": "AGENTS.md",
    "CLAUDE.md": "CLAUDE.md",
    "docs": "docs",
    "templates": "templates",
    "claude/settings.json": ".claude/settings.json",
    "claude/skills": ".claude/skills",
    "claude/agents": ".claude/agents",
}


def _packaged() -> Path:
    return Path(__file__).resolve().parent / "_assets"


def _checkout_root() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        if (parent / "PROTOCOL.md").is_file() and (parent / "templates").is_dir():
            return parent
    return None


def asset_path(key: str) -> Path:
    if key not in SOURCES:
        raise KeyError(key)
    packaged = _packaged() / key
    if packaged.exists():
        return packaged
    root = _checkout_root()
    if root is not None and (root / SOURCES[key]).exists():
        return root / SOURCES[key]
    raise FileNotFoundError(f"agentproof asset {key!r} not found; is the package installed correctly?")
