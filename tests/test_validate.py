import datetime as dt

from conftest import EVIDENCE, write_task

from agentproof import ledger
from agentproof.validate import validate

TODAY = dt.date(2026, 9, 10)


def errors(root):
    return [i for i in validate(root, today=TODAY) if i.level == "error"]


def messages(root, level="error"):
    return " ".join(i.message for i in validate(root, today=TODAY) if i.level == level)


def test_clean_done_task_passes(project):
    write_task(project)
    ledger.write(project)
    assert errors(project) == []


def test_unknown_status_and_tier(project):
    write_task(project, status="DONE-PASS", tier=3)
    ledger.write(project)
    text = messages(project)
    assert "status 'DONE-PASS'" in text
    assert "tier 3" in text


def test_id_must_match_folder(project):
    folder = write_task(project)
    folder.rename(project / "tasks" / "TASK-20260901-02-renamed")
    ledger.write(project)
    assert "does not match folder name" in messages(project)


def test_missing_rollback_section_is_an_error(project):
    folder = write_task(project)
    path = folder / "task.md"
    path.write_text(path.read_text(encoding="utf-8").replace("## Rollback", "## Undo"), encoding="utf-8")
    ledger.write(project)
    assert "## Rollback" in messages(project)


def test_tier2_without_approval_fails(project):
    write_task(project, tier=2)
    ledger.write(project)
    assert "tier 2 needs `## Approvals`" in messages(project)


def test_tier2_with_approval_passes(project):
    write_task(
        project,
        tier=2,
        extra="\n## Approvals\n\n- Approved by: Adam\n- When: 2026-09-01 10:00 UTC\n- Exact scope: step 1\n",
    )
    ledger.write(project)
    assert errors(project) == []


def test_in_progress_needs_handoff_and_goes_stale(project):
    write_task(project, status="in-progress", updated="2026-08-01", evidence=None)
    ledger.write(project)
    assert "needs `## Handoff`" in messages(project)
    assert "not updated for 40 days" in messages(project, "warn")


def test_done_needs_evidence_with_results(project):
    write_task(project, evidence=None)
    ledger.write(project)
    assert "needs evidence/evidence.md" in messages(project)


def test_evidence_without_pass_fail_is_an_error(project):
    write_task(project, evidence=EVIDENCE.replace("| PASS |", "| ok |"))
    ledger.write(project)
    assert "is not PASS, FAIL or N/A" in messages(project)


def test_failed_task_needs_follow_up(project):
    write_task(project, status="failed")
    ledger.write(project)
    assert "follow-up" in messages(project)


def test_duplicate_ids_are_rejected(project):
    write_task(project)
    write_task(project, folder=project / "tasks" / "archive" / "TASK-20260901-01-demo")
    ledger.write(project)
    assert "duplicate task id" in messages(project)


def test_stale_ledger_is_an_error(project):
    write_task(project)
    assert "ledger is out of date" in messages(project)


def test_knowledge_doc_stamp(project):
    write_task(project)
    ledger.write(project)
    docs = project / "knowledge" / "demo"
    docs.mkdir(parents=True)
    (docs / "00-overview.md").write_text(
        "---\nlast-verified: 2026-01-01\nverified-by: TASK-20990101-01-missing\nverified-against: demo@abc1234 (main)\n---\n",
        encoding="utf-8",
    )
    (docs / "10-no-stamp.md").write_text("# no stamp\n", encoding="utf-8")
    text = messages(project)
    assert "verified-by names a task that does not exist" in text
    assert "knowledge docs need" in text
    assert "re-check before relying on it" in messages(project, "warn")


def test_duplicate_runbook_numbers(project):
    (project / "runbooks").mkdir()
    stamp = "---\nlast-verified: 2026-09-01\nverified-by: manual\nverified-against: n/a\n---\n"
    (project / "runbooks" / "RB-01-a.md").write_text(stamp, encoding="utf-8")
    (project / "runbooks" / "RB-01-b.md").write_text(stamp, encoding="utf-8")
    assert "RB-01 is also used by" in messages(project)


def test_inventory_rejects_connection_details(project):
    (project / "inventory").mkdir()
    (project / "inventory" / "hosts.yaml").write_text(
        "hosts:\n"
        "  - alias: web-01\n"
        "    role: web\n"
        "    environment: lab\n"
        "    protected: false\n"
        "    user: root\n"
        "    fingerprint: {via: ssh, command: hostname, expected: web-01}\n",
        encoding="utf-8",
    )
    assert "`user` does not belong in the inventory" in messages(project)
