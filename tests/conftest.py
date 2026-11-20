from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

CONTRACT = """
## Goal

Make the thing work. Request: "make it work"

## Scope

Touch:
- src/thing.py

## Targets

| Target | Kind | Expected fingerprint | Checked |
|---|---|---|---|
| app@main | repo | n/a | yes |

## Plan

1. Change it (tier 1).

## Rollback

- How: git revert
- Tested: no, trivial
- Point of no return: none

## Acceptance criteria

- [x] tests pass

## Verification

- Boundary checks: pytest
"""

EVIDENCE = """# Evidence

## Summary

Changed it.

## Commands and observations

$ pytest -> 3 passed

## Acceptance criteria

| # | Criterion | Check | Expected | Observed | Result |
|---|---|---|---|---|---|
| 1 | tests pass | pytest | pass | 3 passed | PASS |

## Negative checks

| What | Check | Observed |
|---|---|---|
| other tests | pytest | green |

## Not verified

- Nothing.

## Knowledge updated

- none

## Follow-ups

- none
"""


def write_task(
    root: Path,
    task_id: str = "TASK-20260901-01-demo",
    *,
    status: str = "done",
    tier: int = 1,
    updated: str = "2026-09-02",
    extra: str = "",
    evidence: str | None = EVIDENCE,
    folder: Path | None = None,
) -> Path:
    folder = folder or (root / "tasks" / task_id)
    folder.mkdir(parents=True, exist_ok=True)
    fm = textwrap.dedent(
        f"""\
        ---
        id: {task_id}
        title: Demo task
        status: {status}
        tier: {tier}
        product: demo
        created: 2026-09-01
        updated: {updated}
        owner: adam
        ---

        # Demo task
        """
    )
    (folder / "task.md").write_text(fm + CONTRACT + extra, encoding="utf-8")
    if evidence is not None:
        (folder / "evidence").mkdir(exist_ok=True)
        (folder / "evidence" / "evidence.md").write_text(evidence, encoding="utf-8")
    return folder


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "tasks").mkdir()
    return tmp_path
