"""Journaled execution: every mutating command runs through here and lands in the task's evidence."""

from __future__ import annotations

import datetime as dt
import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from agentproof.inventory import get_host
from agentproof.redact import redact
from agentproof.tasks import find_task, has_approval

CLIP = 4000


class ProtocolError(RuntimeError):
    """Running the command would break a protocol rule."""


@dataclass
class RunResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float


def session_env() -> str:
    return os.environ.get("AGENTPROOF_ENV", "lab").strip().lower() or "lab"


def preflight(root: Path, task_id: str | None, mutating: bool, host: str | None) -> Path | None:
    """Check the protocol gates. Returns the journal path, or None for an unjournaled read."""
    if host is not None:
        record = get_host(root, host)  # unknown host -> LookupError (fail closed)
        if mutating and record.get("environment") == "production" and session_env() != "production":
            raise ProtocolError(
                f"{host} is a production host but this session is {session_env()!r}; "
                "the human must set AGENTPROOF_ENV=production for this session"
            )
        if mutating and record.get("protected") is True:
            print(f"note: {host} is protected; destructive changes to it are human-only")
    if task_id is None:
        if mutating:
            raise ProtocolError(
                "mutating command without a task; create one first: agentproof new-task <slug>"
            )
        return None
    task = find_task(root, task_id)
    if mutating:
        if task.status != "in-progress":
            raise ProtocolError(f"task {task.id} is {task.status!r}; mutating commands need in-progress")
        if task.tier == 2 and not has_approval(task):
            raise ProtocolError(f"task {task.id} is tier 2 and has no recorded approval")
    return task.folder / "evidence" / "journal.md"


def run(
    root: Path,
    cmd: list[str],
    *,
    task_id: str | None = None,
    mutating: bool = False,
    host: str | None = None,
    timeout: int = 900,
) -> RunResult:
    if not cmd:
        raise ValueError("no command given")
    journal = preflight(root, task_id, mutating, host)
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        result = RunResult(proc.returncode, proc.stdout or "", proc.stderr or "", time.monotonic() - started)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        result = RunResult(124, out, f"timed out after {timeout} s", time.monotonic() - started)
    except OSError as exc:
        result = RunResult(127, "", str(exc), time.monotonic() - started)
    if journal is not None:
        _append(journal, cmd, result, mutating, host)
    return result


def _clip(text: str) -> str:
    text = redact(text)
    if len(text) > CLIP:
        return text[:CLIP] + f"\n… ({len(text) - CLIP} more characters not journaled)"
    return text


def _append(journal: Path, cmd: list[str], result: RunResult, mutating: bool, host: str | None) -> None:
    journal.parent.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    kind = "mutating" if mutating else "read"
    where = f" · host {host}" if host else ""
    entry = [
        f"### {stamp} · {kind}{where} · exit {result.exit_code} · {result.duration_s:.1f} s",
        "",
        "```text",
        f"$ {redact(shlex.join(cmd))}",
        _clip(result.stdout).rstrip(),
    ]
    if result.stderr.strip():
        entry += ["--- stderr ---", _clip(result.stderr).rstrip()]
    entry += ["```", ""]
    new = not journal.exists()
    with journal.open("a", encoding="utf-8") as fh:
        if new:
            fh.write("# Command journal\n\nWritten by `agentproof run`. Redacted. Do not edit.\n\n")
        fh.write("\n".join(entry) + "\n")
