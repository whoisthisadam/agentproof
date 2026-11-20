"""`agentproof validate`: the paperwork can't drift if CI checks it."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

from agentproof import frontmatter, ledger
from agentproof.inventory import check_hosts, hosts_path
from agentproof.tasks import (
    FRONT_MATTER_KEYS,
    ID_RE,
    OPEN_STATUSES,
    STATUSES,
    TIERS,
    Task,
    discover,
    field_value,
    has_approval,
    parse_sections,
)

CONTRACT_SECTIONS = ["Goal", "Scope", "Targets", "Plan", "Rollback", "Acceptance criteria", "Verification"]
EVIDENCE_SECTIONS = [
    "Summary",
    "Commands and observations",
    "Acceptance criteria",
    "Negative checks",
    "Not verified",
    "Knowledge updated",
]
DOC_KEYS = ["last-verified", "verified-by", "verified-against"]
DOC_DIRS = ["knowledge", "runbooks"]
DOC_SKIP = {"INDEX.md", "README.md"}


@dataclass
class Issue:
    level: str  # "error" | "warn"
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.level.upper():5} {self.path}: {self.message}"


def _date(value: object) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        return None


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def check_task(root: Path, task: Task, today: dt.date, stale_days: int) -> list[Issue]:
    p = _rel(root, task.path)
    if task.error:
        return [Issue("error", p, task.error)]
    if task.meta is None:
        return [Issue("error", p, "missing front matter (see templates/task.md)")]
    meta = task.meta
    issues = [Issue("error", p, f"front matter is missing `{k}`") for k in FRONT_MATTER_KEYS if k not in meta]

    task_id = str(meta.get("id", ""))
    if task_id and not ID_RE.match(task_id):
        issues.append(Issue("error", p, f"id {task_id!r} is not TASK-YYYYMMDD-NN-slug"))
    if task_id and task_id != task.folder.name:
        issues.append(Issue("error", p, f"id {task_id!r} does not match folder name {task.folder.name!r}"))
    status = meta.get("status")
    if "status" in meta and status not in STATUSES:
        issues.append(Issue("error", p, f"status {status!r} is not one of: {', '.join(STATUSES)}"))
    if "tier" in meta and meta.get("tier") not in TIERS:
        issues.append(Issue("error", p, f"tier {meta.get('tier')!r} must be 0, 1 or 2"))
    created, updated = _date(meta.get("created")), _date(meta.get("updated"))
    for key, value in (("created", created), ("updated", updated)):
        if key in meta and value is None:
            issues.append(Issue("error", p, f"{key} must be YYYY-MM-DD"))
    if created and updated and updated < created:
        issues.append(Issue("error", p, "updated is earlier than created"))

    if status in STATUSES and status not in ("draft", "cancelled"):
        for name in CONTRACT_SECTIONS:
            if not task.sections.get(name):
                issues.append(Issue("error", p, f"status {status} needs a filled `## {name}` section"))
        if "TASK-YYYYMMDD" in task.body or "<One or two sentences" in task.body:
            issues.append(Issue("error", p, "template placeholders left in a non-draft task"))

    if meta.get("tier") == 2 and status in ("ready", "in-progress", "blocked", "done", "failed"):
        if not has_approval(task):
            issues.append(
                Issue("error", p, "tier 2 needs `## Approvals` with Approved by / When / Exact scope filled")
            )

    if status in OPEN_STATUSES:
        handoff = task.sections.get("Handoff", "")
        if not field_value(handoff, "Next step"):
            issues.append(Issue("error", p, f"status {status} needs `## Handoff` with a Next step"))
        if updated and (today - updated).days > stale_days:
            issues.append(
                Issue(
                    "warn",
                    p,
                    f"{status} and not updated for {(today - updated).days} days: close, block or cancel",
                )
            )

    if status == "cancelled" and not (task.sections.get("Handoff") or task.sections.get("Goal")):
        issues.append(Issue("error", p, "cancelled tasks need a reason in Handoff or Goal"))

    if status in ("done", "failed"):
        issues.extend(check_evidence(root, task))
    return issues


def check_evidence(root: Path, task: Task) -> list[Issue]:
    path = task.folder / "evidence" / "evidence.md"
    p = _rel(root, path)
    if not path.is_file():
        return [Issue("error", p, f"status {task.status} needs evidence/evidence.md")]
    sections = parse_sections(path.read_text(encoding="utf-8"))
    issues = [
        Issue("error", p, f"evidence needs a filled `## {name}` section")
        for name in EVIDENCE_SECTIONS
        if not sections.get(name) or sections[name].lstrip().startswith("<")
    ]
    results = _result_cells(sections.get("Acceptance criteria", ""))
    if sections.get("Acceptance criteria") and not results:
        issues.append(Issue("error", p, "acceptance criteria table has no pass/fail results"))
    for cell in results:
        if not re.match(r"(pass|fail|n/a)\b", cell, re.IGNORECASE):
            issues.append(Issue("error", p, f"acceptance criteria result {cell!r} is not PASS, FAIL or N/A"))
    if task.status == "failed" and "TASK-" not in sections.get("Follow-ups", ""):
        issues.append(Issue("error", p, "a failed task names its follow-up task under `## Follow-ups`"))
    return issues


def _result_cells(table: str) -> list[str]:
    """Last cell of each data row of a markdown table (header and separator rows skipped)."""
    rows = [line.strip() for line in table.splitlines() if line.strip().startswith("|")]
    cells = []
    for row in rows[2:]:
        parts = [c.strip() for c in row.strip("|").split("|")]
        if parts and parts[-1]:
            cells.append(parts[-1])
    return cells


def check_docs(root: Path, task_ids: set[str], today: dt.date, max_age: int) -> list[Issue]:
    issues: list[Issue] = []
    for dirname in DOC_DIRS:
        base = root / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.name in DOC_SKIP:
                continue
            p = _rel(root, path)
            try:
                meta, _ = frontmatter.split(path.read_text(encoding="utf-8"))
            except frontmatter.FrontMatterError as exc:
                issues.append(Issue("error", p, str(exc)))
                continue
            if meta is None:
                issues.append(
                    Issue("error", p, "knowledge docs need last-verified / verified-by / verified-against")
                )
                continue
            for key in DOC_KEYS:
                if not meta.get(key):
                    issues.append(Issue("error", p, f"front matter is missing `{key}`"))
            verified = _date(meta.get("last-verified"))
            if meta.get("last-verified") and verified is None:
                issues.append(Issue("error", p, "last-verified must be YYYY-MM-DD"))
            elif verified and (today - verified).days > max_age:
                issues.append(
                    Issue(
                        "warn",
                        p,
                        f"last verified {(today - verified).days} days ago: re-check before relying on it",
                    )
                )
            by = str(meta.get("verified-by", ""))
            if by.startswith("TASK-") and by not in task_ids:
                issues.append(Issue("error", p, f"verified-by names a task that does not exist: {by}"))
    return issues


def check_numbering(root: Path) -> list[Issue]:
    issues = []
    for dirname, prefix in (("runbooks", "RB"), ("decisions", "ADR")):
        base = root / dirname
        if not base.is_dir():
            continue
        seen: dict[str, str] = {}
        for path in sorted(base.glob(f"{prefix}-*.md")):
            m = re.match(rf"({prefix}-\d+)", path.name)
            if not m:
                continue
            if m.group(1) in seen:
                issues.append(
                    Issue("error", _rel(root, path), f"{m.group(1)} is also used by {seen[m.group(1)]}")
                )
            seen.setdefault(m.group(1), path.name)
    return issues


def validate(
    root: Path, *, today: dt.date | None = None, stale_days: int = 14, max_doc_age: int = 90
) -> list[Issue]:
    today = today or dt.date.today()
    tasks = discover(root)
    issues: list[Issue] = []
    ids: dict[str, str] = {}
    for task in tasks:
        issues.extend(check_task(root, task, today, stale_days))
        if task.id in ids:
            issues.append(Issue("error", _rel(root, task.path), f"duplicate task id, also {ids[task.id]}"))
        ids.setdefault(task.id, _rel(root, task.path))
    if tasks and not ledger.is_current(root):
        issues.append(Issue("error", "tasks/README.md", "ledger is out of date: run `agentproof ledger`"))
    issues.extend(check_docs(root, set(ids), today, max_doc_age))
    issues.extend(check_numbering(root))
    if hosts_path(root).is_file():
        issues.extend(Issue("error", "inventory/hosts.yaml", msg) for msg in check_hosts(root))
    return issues
