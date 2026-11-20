"""YAML front matter: parse and write the block between leading `---` lines."""

from __future__ import annotations

import datetime as dt
from typing import Any

import yaml


class FrontMatterError(ValueError):
    pass


def split(text: str) -> tuple[dict[str, Any] | None, str]:
    """Return (front matter or None, body). Raises FrontMatterError on malformed YAML."""
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines(keepends=True)
    if lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            raw = "".join(lines[1:i])
            body = "".join(lines[i + 1 :])
            try:
                data = yaml.safe_load(raw) or {}
            except yaml.YAMLError as exc:
                raise FrontMatterError(f"invalid YAML front matter: {exc}") from exc
            if not isinstance(data, dict):
                raise FrontMatterError("front matter must be a mapping")
            return {k: _normalise(v) for k, v in data.items()}, body
    raise FrontMatterError("front matter is not closed with ---")


def _normalise(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()[:10]
    return value


def render(data: dict[str, Any], keys: list[str]) -> str:
    """Render front matter with keys in a fixed order."""
    out = ["---"]
    for key in keys:
        if key not in data:
            continue
        value = data[key]
        if isinstance(value, str) and _needs_quotes(value):
            value_text = yaml.safe_dump(value, default_flow_style=True, width=1000).strip()
            if value_text.endswith("\n..."):
                value_text = value_text[: -len("\n...")]
        else:
            value_text = str(value)
        out.append(f"{key}: {value_text}")
    out.append("---")
    return "\n".join(out) + "\n"


def _needs_quotes(value: str) -> bool:
    if value == "" or value.strip() != value:
        return True
    if any(ch in value for ch in ":#{}[],&*!|>'\"%@`"):
        return True
    return value.lower() in {"yes", "no", "true", "false", "null", "on", "off", "~"}
