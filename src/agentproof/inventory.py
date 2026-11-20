"""inventory/hosts.yaml: host identity and intent. Never connection details or secrets."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ENVIRONMENTS = ("lab", "staging", "production")
FORBIDDEN_KEYS = {
    "user",
    "username",
    "port",
    "identity_file",
    "identityfile",
    "key_path",
    "password",
    "passwd",
    "private_key",
    "token",
    "secret",
    "api_key",
}


def hosts_path(root: Path) -> Path:
    return root / "inventory" / "hosts.yaml"


def load_hosts(root: Path) -> list[dict[str, Any]]:
    path = hosts_path(root)
    if not path.is_file():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    hosts = data.get("hosts") or []
    if not isinstance(hosts, list):
        raise ValueError("inventory/hosts.yaml: `hosts` must be a list")
    return hosts


def get_host(root: Path, alias: str) -> dict[str, Any]:
    for host in load_hosts(root):
        if isinstance(host, dict) and host.get("alias") == alias:
            return host
    raise LookupError(f"host {alias!r} is not in {hosts_path(root)}")


def _forbidden(node: Any, trail: str = "") -> list[str]:
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{trail}.{key}" if trail else str(key)
            if str(key).lower() in FORBIDDEN_KEYS:
                found.append(here)
            found.extend(_forbidden(value, here))
    elif isinstance(node, list):
        for i, item in enumerate(node):
            found.extend(_forbidden(item, f"{trail}[{i}]"))
    return found


def check_hosts(root: Path) -> list[str]:
    """Problems with inventory/hosts.yaml, as messages. Empty list means valid."""
    try:
        hosts = load_hosts(root)
    except (ValueError, yaml.YAMLError) as exc:
        return [str(exc)]
    problems = []
    seen: set[str] = set()
    for i, host in enumerate(hosts):
        if not isinstance(host, dict):
            problems.append(f"hosts[{i}] must be a mapping")
            continue
        alias = host.get("alias")
        label = alias or f"hosts[{i}]"
        if not alias:
            problems.append(f"{label}: missing alias")
        elif alias in seen:
            problems.append(f"{label}: duplicate alias")
        else:
            seen.add(alias)
        for key in ("role", "environment"):
            if not host.get(key):
                problems.append(f"{label}: missing {key}")
        if host.get("environment") and host["environment"] not in ENVIRONMENTS:
            problems.append(f"{label}: environment must be one of {', '.join(ENVIRONMENTS)}")
        if not isinstance(host.get("protected"), bool):
            problems.append(f"{label}: protected must be true or false")
        fp = host.get("fingerprint")
        if not isinstance(fp, dict) or not fp.get("command") or not fp.get("expected"):
            problems.append(f"{label}: fingerprint needs command and expected")
        elif fp.get("via", "ssh") not in ("ssh", "local"):
            problems.append(f"{label}: fingerprint.via must be ssh or local")
        for path in _forbidden(host):
            problems.append(
                f"{label}: `{path}` does not belong in the inventory "
                "(connection details live in ~/.ssh/config, secrets in your secret manager)"
            )
    return problems


@dataclass
class FingerprintResult:
    alias: str
    expected: str
    observed: str | None
    ok: bool
    could_not_check: bool
    detail: str = ""


Runner = Callable[[list[str]], subprocess.CompletedProcess]


def _default_runner(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def fingerprint(root: Path, alias: str, runner: Runner | None = None) -> FingerprintResult:
    host = get_host(root, alias)
    fp = host.get("fingerprint") or {}
    expected = str(fp.get("expected", "")).strip()
    command = str(fp.get("command", ""))
    if fp.get("via", "ssh") == "ssh":
        cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", alias, command]
    else:
        cmd = shlex.split(command)
    runner = runner or _default_runner
    try:
        proc = runner(cmd)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return FingerprintResult(alias, expected, None, False, True, str(exc))
    if proc.returncode != 0:
        return FingerprintResult(alias, expected, None, False, True, f"exit {proc.returncode}")
    observed = (proc.stdout or "").strip()
    return FingerprintResult(alias, expected, observed, observed == expected, False)
