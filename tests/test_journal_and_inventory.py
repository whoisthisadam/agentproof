import subprocess
import sys

import pytest
from conftest import write_task

from agentproof import inventory, journal

HOSTS = """hosts:
  - alias: lab-01
    role: lab box
    environment: lab
    protected: false
    fingerprint: {via: local, command: "python -c \\"print('lab-01')\\"", expected: lab-01}
  - alias: prod-01
    role: prod box
    environment: production
    protected: true
    fingerprint: {via: ssh, command: cat /etc/agentproof/host-id, expected: prod-01}
"""

PRINT = [sys.executable, "-c", "print('hello')"]


@pytest.fixture
def infra(project):
    (project / "inventory").mkdir()
    (project / "inventory" / "hosts.yaml").write_text(HOSTS, encoding="utf-8")
    write_task(project, status="in-progress", evidence=None, extra="\n## Handoff\n\n- Next step: run\n")
    return project


def test_mutating_without_task_is_refused(infra):
    with pytest.raises(journal.ProtocolError, match="without a task"):
        journal.run(infra, PRINT, mutating=True)


def test_mutating_needs_in_progress(project):
    write_task(project, status="ready", evidence=None)
    with pytest.raises(journal.ProtocolError, match="in-progress"):
        journal.run(project, PRINT, task_id="TASK-20260901-01-demo", mutating=True)


def test_tier2_without_approval_is_refused(project):
    write_task(project, status="in-progress", tier=2, evidence=None, extra="\n## Handoff\n\n- Next step: x\n")
    with pytest.raises(journal.ProtocolError, match="approval"):
        journal.run(project, PRINT, task_id="TASK-20260901-01-demo", mutating=True)


def test_production_host_needs_production_session(infra, monkeypatch):
    monkeypatch.setenv("AGENTPROOF_ENV", "lab")
    with pytest.raises(journal.ProtocolError, match="production"):
        journal.run(infra, PRINT, task_id="TASK-20260901-01-demo", mutating=True, host="prod-01")


def test_unknown_host_fails_closed(infra):
    with pytest.raises(LookupError):
        journal.run(infra, PRINT, task_id="TASK-20260901-01-demo", mutating=True, host="nope")


def test_journal_is_written_and_redacted(infra, monkeypatch):
    secret = "journal-secret-" + "9" * 8
    monkeypatch.setenv("DEMO_API_TOKEN", secret)
    cmd = [sys.executable, "-c", f"print('token is {secret}')"]
    result = journal.run(infra, cmd, task_id="TASK-20260901-01-demo", mutating=True, host="lab-01")
    assert result.exit_code == 0
    text = (infra / "tasks" / "TASK-20260901-01-demo" / "evidence" / "journal.md").read_text(encoding="utf-8")
    assert "mutating · host lab-01 · exit 0" in text
    assert secret not in text
    assert "***REDACTED:DEMO_API_TOKEN***" in text


def test_fingerprint_ok_and_mismatch(infra):
    assert inventory.fingerprint(infra, "lab-01").ok

    def fake(cmd):
        assert cmd[:2] == ["ssh", "-o"] and "prod-01" in cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="someone-else\n", stderr="")

    result = inventory.fingerprint(infra, "prod-01", runner=fake)
    assert not result.ok and not result.could_not_check
    assert result.observed == "someone-else"


def test_fingerprint_failure_is_not_a_match(infra):
    def failing(cmd):
        return subprocess.CompletedProcess(cmd, 255, stdout="", stderr="timeout")

    result = inventory.fingerprint(infra, "prod-01", runner=failing)
    assert result.could_not_check and not result.ok
