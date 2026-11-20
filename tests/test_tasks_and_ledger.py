import datetime as dt

import pytest
from conftest import write_task

from agentproof import ledger, tasks


def test_new_task_scaffolds_contract_and_evidence(project):
    folder = tasks.new_task(project, "pulse-fix-thing", product="pulse", tier=2, today=dt.date(2026, 9, 14))
    assert folder.name == "TASK-20260914-01-pulse-fix-thing"
    task = tasks.load_task(folder / "task.md")
    assert task.meta["status"] == "draft"
    assert task.meta["tier"] == 2
    assert task.meta["product"] == "pulse"
    assert "Approvals" in task.sections
    evidence = (folder / "evidence" / "evidence.md").read_text(encoding="utf-8")
    assert "TASK-20260914-01-pulse-fix-thing" in evidence


def test_next_id_sees_tasks_in_grouping_subfolders(project):
    # Regression: the sequence number must account for tasks moved into subfolders.
    write_task(project, "TASK-20260914-03-old", folder=project / "tasks" / "group" / "TASK-20260914-03-old")
    folder = tasks.new_task(project, "next-one", today=dt.date(2026, 9, 14))
    assert folder.name == "TASK-20260914-04-next-one"


@pytest.mark.parametrize("slug", ["Bad Slug", "under_score", "-lead", ""])
def test_new_task_rejects_bad_slugs(project, slug):
    with pytest.raises(ValueError):
        tasks.new_task(project, slug)


def test_ledger_is_generated_newest_first_and_checked(project):
    write_task(project, "TASK-20260901-01-older")
    write_task(
        project, "TASK-20260902-01-newer", status="in-progress", extra="\n## Handoff\n\n- Next step: x\n"
    )
    assert not ledger.is_current(project)
    ledger.write(project)
    text = ledger.ledger_path(project).read_text(encoding="utf-8")
    assert text.index("newer") < text.index("older")
    assert "| in-progress |" in text
    assert ledger.is_current(project)
    write_task(project, "TASK-20260903-01-another")
    assert not ledger.is_current(project)


def test_ledger_escapes_pipes_in_titles(project):
    folder = write_task(project)
    path = folder / "task.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("title: Demo task", 'title: "a | b"'), encoding="utf-8"
    )
    assert "a \\| b" in ledger.render(project)
