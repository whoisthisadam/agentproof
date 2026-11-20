"""Mask secrets in text headed for journals and evidence.

A safety net only: the rule is that secret values never become printable text in the first place.
"""

from __future__ import annotations

import os
import re

# Environment variables whose values are treated as secret.
SECRET_NAME_RE = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PASSWD|PASSPHRASE|API_KEY|PRIVATE_KEY|ACCESS_KEY|CREDENTIALS?|_DSN|DB_URL"
    r"|DATABASE_URL|CONNECTION_STRING)$",
    re.IGNORECASE,
)
MIN_SECRET_LEN = 6

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
        "***REDACTED:PRIVATE_KEY***",
    ),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]{12,}=*"), "Bearer ***REDACTED***"),
    (re.compile(r"(?i)\b(authorization|x-api-key)\s*:\s*\S+"), r"\1: ***REDACTED***"),
    (
        re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|client[_-]?secret)\s*[=:]\s*\S+"),
        r"\1=***REDACTED***",
    ),
    (re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^\s:/@]+):[^\s@/]+@"), r"\1:***REDACTED***@"),
    (re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}"), "***REDACTED:GITHUB_TOKEN***"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "***REDACTED:SLACK_TOKEN***"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "***REDACTED:AWS_KEY_ID***"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"), "***REDACTED:JWT***"),
    (re.compile(r"(?i)\bsig=[A-Za-z0-9%_\-+/=]{8,}"), "sig=***REDACTED***"),
]


def secret_values(environ: dict[str, str] | None = None) -> dict[str, str]:
    environ = dict(os.environ) if environ is None else environ
    return {
        name: value
        for name, value in environ.items()
        if SECRET_NAME_RE.search(name) and value and len(value) >= MIN_SECRET_LEN
    }


def redact(text: str, environ: dict[str, str] | None = None) -> str:
    out = text
    # Longest values first so a value containing another is masked whole.
    for name, value in sorted(secret_values(environ).items(), key=lambda kv: -len(kv[1])):
        out = out.replace(value, f"***REDACTED:{name}***")
    for pattern, replacement in _PATTERNS:
        out = pattern.sub(replacement, out)
    return out
