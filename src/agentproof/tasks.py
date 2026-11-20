"""Tasks: discovery, parsing and scaffolding."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentproof import frontmatter
from agentproof.assets import asset_path

STATUSES = ("draft", "ready", "in-progress", "blocked", "done", "failed", "cancelled")
OPEN_STATUSES = ("in-progress", "blocked")
TIERS = (0, 1, 2)
FRONT_MATTER_KEYS = ["id", "title", "status", "tier", "product", "created", "updated", "owner"]
ID_RE = re.compile(r"^TASK-(\d{8})-(\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass
class Task:
    path: Path  # path to task.md
    meta: dict[str, Any] | None
    body: str
    error: str | None = None
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def folder(self) -> Path:
        return self.path.parent

    @property
    def id(self) -> str:
        if self.meta and isinstance(self.meta.get("id"), str):
            return self.meta["id"]
        return self.folder.name

    @property
    def status(self) -> str | None:
        return self.meta.get("status") if self.meta else None

    @property
    def tier(self) -> Any:
        return self.meta.get("tier") if self.meta else None


def parse_sections(body: str) -> dict[str, str]:
    """Map each `## Heading` to the text under it (until the next `## `)."""
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def load_task(path: Path) -> Task:
    text = path.read_text(encoding="utf-8")
    try:
        meta, body = frontmatter.split(text)
    except frontmatter.FrontMatterError as exc:
        return Task(path=path, meta=None, body=text, error=str(exc))
    return Task(path=path, meta=meta, body=body, sections=parse_sections(body))


def tasks_dir(root: Path) -> Path:
    return root / "tasks"


def discover(root: Path) -> list[Task]:
    """Every tasks/**/TASK-*/task.md, including tasks in grouping subfolders."""
    base = tasks_dir(root)
    if not base.is_dir():
        return []
    found = [p for p in base.rglob("task.md") if p.parent.name.startswith("TASK-")]
    return [load_task(p) for p in sorted(found)]


def next_id(root: Path, slug: str, today: dt.date) -> str:
    stamp = today.strftime("%Y%m%d")
    used = []
    for task in discover(root):
        for candidate in {task.id, task.folder.name}:
            m = ID_RE.match(candidate)
            if m and m.group(1) == stamp:
                used.append(int(m.group(2)))
    return f"TASK-{stamp}-{(max(used) + 1 if used else 1):02d}-{slug}"


def new_task(
    root: Path,
    slug: str,
    *,
    title: str | None = None,
    product: str = "general",
    tier: int = 1,
    owner: str = "unassigned",
    today: dt.date | None = None,
) -> Path:
    """Scaffold tasks/<id>/task.md and evidence/evidence.md from the templates. Returns the task folder."""
    if not SLUG_RE.match(slug):
        raise ValueError(f"slug must be kebab-case (a-z, 0-9, dashes): {slug!r}")
    if tier not in TIERS:
        raise ValueError(f"tier must be 0, 1 or 2, got {tier!r}")
    today = today or dt.date.today()
    task_id = next_id(root, slug, today)
    folder = tasks_dir(root) / task_id
    folder.mkdir(parents=True, exist_ok=False)
    title = title or slug.replace("-", " ").capitalize()

    template = template_text(root, "task.md")
    _, body = frontmatter.split(template)
    body = body.replace("# <title>", f"# {title}", 1)
    meta = {
        "id": task_id,
        "title": title,
        "status": "draft",
        "tier": tier,
        "product": product,
        "created": today.isoformat(),
        "updated": today.isoformat(),
        "owner": owner,
    }
    (folder / "task.md").write_text(frontmatter.render(meta, FRONT_MATTER_KEYS) + body, encoding="utf-8")

    evidence = template_text(root, "evidence.md").replace("TASK-YYYYMMDD-NN-slug", task_id)
    (folder / "evidence").mkdir()
    (folder / "evidence" / "evidence.md").write_text(evidence, encoding="utf-8")
    return folder


def template_text(root: Path, name: str) -> str:
    """Prefer the project's own templates/ (they may be customised); fall back to the packaged ones."""
    local = root / "templates" / name
    if local.is_file():
        return local.read_text(encoding="utf-8")
    return (asset_path("templates") / name).read_text(encoding="utf-8")


def find_task(root: Path, task_id: str) -> Task:
    for task in discover(root):
        if task.id == task_id or task.folder.name == task_id:
            return task
    raise LookupError(f"no task {task_id!r} under {tasks_dir(root)}")


def field_value(section_text: str, label: str) -> str:
    """Value after `- Label:` in a section, or '' if missing or still a template placeholder."""
    for line in section_text.splitlines():
        stripped = line.strip().lstrip("-").strip()
        if stripped.lower().startswith(label.lower() + ":"):
            value = stripped[len(label) + 1 :].strip()
            return "" if value.startswith("<") else value
    return ""


def has_approval(task: Task) -> bool:
    approvals = task.sections.get("Approvals", "")
    return all(field_value(approvals, label) for label in ("Approved by", "When", "Exact scope"))
