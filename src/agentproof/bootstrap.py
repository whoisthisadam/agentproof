"""`agentproof init`: add the protocol to an existing project without overwriting anything."""

from __future__ import annotations

from pathlib import Path

from agentproof import ledger
from agentproof.assets import asset_path

KNOWLEDGE_INDEX = """# Knowledge index

One row per product. Read the product's docs before working on it (PROTOCOL.md §8).

| Product | Start here | Words people use for it |
|---|---|---|
"""

HOSTS = """# inventory/hosts.yaml: identity and intent only. See docs/agentproof/remote-access.md.
# Never put users, ports, key paths, passwords or tokens here.

hosts: []
"""

ENV_EXAMPLE = """# Names and purposes only. Values come from your secret manager at runtime.
AGENTPROOF_ENV=lab                 # lab | production
AGENTPROOF_OPERATOR=changeme
"""


def _write(path: Path, text: str, created: list[str], skipped: list[str], root: Path) -> None:
    rel = path.relative_to(root).as_posix()
    if path.exists():
        skipped.append(rel)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    created.append(rel)


def _copy_tree(src: Path, dest: Path, created: list[str], skipped: list[str], root: Path, fix=None) -> None:
    for item in sorted(src.rglob("*")):
        if item.is_dir():
            continue
        text = item.read_text(encoding="utf-8")
        _write(dest / item.relative_to(src), fix(text) if fix else text, created, skipped, root)


def init(target: Path) -> tuple[list[str], list[str]]:
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[str] = []

    def protocol_links(text: str) -> str:
        return text.replace("](docs/", "](docs/agentproof/")

    def doc_links(text: str) -> str:
        return text.replace("](../templates/", "](../../templates/").replace(
            "](../PROTOCOL.md", "](../../PROTOCOL.md"
        )

    for name in ("AGENTS.md", "CLAUDE.md"):
        _write(target / name, asset_path(name).read_text(encoding="utf-8"), created, skipped, target)
    _write(
        target / "PROTOCOL.md",
        protocol_links(asset_path("PROTOCOL.md").read_text(encoding="utf-8")),
        created,
        skipped,
        target,
    )
    _copy_tree(asset_path("docs"), target / "docs" / "agentproof", created, skipped, target, doc_links)
    _copy_tree(asset_path("templates"), target / "templates", created, skipped, target)
    _write(
        target / ".claude" / "settings.json",
        asset_path("claude/settings.json").read_text(encoding="utf-8"),
        created,
        skipped,
        target,
    )
    _copy_tree(asset_path("claude/skills"), target / ".claude" / "skills", created, skipped, target)
    _copy_tree(asset_path("claude/agents"), target / ".claude" / "agents", created, skipped, target)
    _write(target / "knowledge" / "INDEX.md", KNOWLEDGE_INDEX, created, skipped, target)
    _write(target / "inventory" / "hosts.yaml", HOSTS, created, skipped, target)
    _write(target / ".env.example", ENV_EXAMPLE, created, skipped, target)
    if not ledger.ledger_path(target).exists():
        ledger.write(target)
        created.append("tasks/README.md")
    return created, skipped


def merge_hint(skipped: list[str]) -> str:
    hints = []
    if "AGENTS.md" in skipped or "CLAUDE.md" in skipped:
        hints.append(
            "You already have AGENTS.md / CLAUDE.md. Add this line near the top:\n"
            "  This repository follows the agentproof protocol: read PROTOCOL.md before your first change."
        )
    if ".claude/settings.json" in skipped:
        hints.append(
            "You already have .claude/settings.json. Merge the `deny` list from the agentproof one by hand."
        )
    return "\n\n".join(hints)
