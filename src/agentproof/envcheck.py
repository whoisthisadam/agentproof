"""`agentproof env-check`: which variables are set, by name only. Values are never printed."""

from __future__ import annotations

import os
import re
from pathlib import Path

NAME_RE = re.compile(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=")


def declared_names(example: Path) -> list[str]:
    if not example.is_file():
        return []
    names = []
    for line in example.read_text(encoding="utf-8").splitlines():
        m = NAME_RE.match(line)
        if m and m.group(1) not in names:
            names.append(m.group(1))
    return names


def env_file_names(path: Path) -> set[str]:
    """Names that have a non-empty value in an env file. Values are read here and discarded."""
    if not path.is_file():
        return set()
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = NAME_RE.match(line)
        if m:
            value = line.split("=", 1)[1].strip().strip("'\"")
            if value and value != "changeme":
                found.add(m.group(1))
    return found


def check(root: Path, environ: dict[str, str] | None = None) -> list[tuple[str, bool]]:
    environ = dict(os.environ) if environ is None else environ
    profile = environ.get("AGENTPROOF_ENV", "lab")
    from_file = env_file_names(root / f".env.{profile}") | env_file_names(root / ".env")
    return [
        (name, bool(environ.get(name)) or name in from_file) for name in declared_names(root / ".env.example")
    ]
