"""Block hard-coded credentials before they are written, committed, or merged.

Test automation leaks secrets in places app code rarely does: test-account passwords, Basic-auth
headers in API tests, `<wsse:Password>` in SOAP envelopes, credentials inside base URLs, and
database connection strings used for test-data setup. All of them are covered here.
"""

import re
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .common import ALLOW, Decision, deny

ALLOW_MARKER = "sdlc:allow-secret"
MAX_UNTRACKED_BYTES = 1_000_000

PATTERNS: dict[str, re.Pattern[str]] = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}"),
    "LLM API key": re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}"),
    "Slack token": re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
}
# Patterns whose group(1) is the secret value, so obvious placeholders can be skipped.
VALUE_PATTERNS: dict[str, re.Pattern[str]] = {
    "hard-coded credential": re.compile(
        r"(?i)\w*(?:password|passwd|pwd|secret|api[_-]?key|token)\w*"
        r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']"
    ),
    "credentials in URL": re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@]+:([^/\s@]{4,})@"),
    "Basic auth header": re.compile(r"(?i)authorization[\"']?\s*[:=]\s*[\"']?basic\s+([A-Za-z0-9+/=]{8,})"),
    # Literal token after "Bearer"; f-strings, ${VAR} and <token> placeholders don't match the class.
    "Bearer token": re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._~+/-]{16,}=*)"),
    "XML password element": re.compile(
        r"(?i)<(?:[\w-]+:)?password\b[^>]*>([^<\s]{4,})</(?:[\w-]+:)?password>"
    ),
    "connection string password": re.compile(r"(?i)\b(?:password|pwd)\s*=\s*([^;\s'\"]{6,})\s*;"),
}
PLACEHOLDER = re.compile(
    r"(?i)^(?:replace[_-]?me|change[_-]?me|your[_-].*|<.*>|\$\{.*\}|\{\{.*\}\}|\$\w+|%\(\w+\)s|"
    r"x{4,}|\*{4,}|(?:dummy|example|placeholder|fake|test|secret)[_-]?\w*|not[_-]?(?:a[_-]?)?real\w*)$"
)


def find_secrets(text: str) -> list[str]:
    hits: set[str] = set()
    for line in text.splitlines():
        if ALLOW_MARKER in line:
            continue
        hits.update(name for name, rx in PATTERNS.items() if rx.search(line))
        for name, rx in VALUE_PATTERNS.items():
            match = rx.search(line)
            if match and not PLACEHOLDER.match(match.group(1)):
                hits.add(name)
    return sorted(hits)


def git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:  # git not installed: scan what we can see, never crash the hook
        return None
    return result.stdout if result.returncode == 0 else None


def added_lines(diff: str) -> str:
    return "\n".join(
        line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")
    )


def pending_commit_text(root: Path) -> str:
    """Everything a commit in this command could include: tracked changes and untracked files."""
    diff = git(root, "diff", "HEAD", "-U0")
    if diff is None:  # no commits yet
        diff = git(root, "diff", "--cached", "-U0") or ""
    parts = [added_lines(diff)]
    for rel in (git(root, "ls-files", "--others", "--exclude-standard") or "").splitlines():
        path = root / rel
        if path.is_file() and path.stat().st_size <= MAX_UNTRACKED_BYTES:
            parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(parts)


EXTRACTORS: dict[str, Callable[[dict[str, Any]], str]] = {
    "Write": lambda i: str(i.get("content", "")),
    "Edit": lambda i: str(i.get("new_string", "")),
    "MultiEdit": lambda i: "\n".join(str(e.get("new_string", "")) for e in i.get("edits") or []),
}


def text_of(tool: str, tool_input: dict[str, Any], root: Path) -> str | None:
    if tool == "Bash":
        command = str(tool_input.get("command", ""))
        if re.search(r"\bgit\b[^;&|]*\bcommit\b", command):
            return command + "\n" + pending_commit_text(root)
        return command
    extract = EXTRACTORS.get(tool)
    return extract(tool_input) if extract else None


def check(tool: str, tool_input: dict[str, Any], root: Path) -> Decision:
    text = text_of(tool, tool_input, root)
    hits = find_secrets(text) if text else []
    if not hits:
        return ALLOW
    return deny(
        f"BLOCKED: possible {', '.join(hits)} in this {tool} call. Test credentials are real "
        "credentials: read them from the environment or the secret manager through the framework's "
        f"configuration layer. For a genuine false positive, put '{ALLOW_MARKER}' on that line."
    )


def scan_diff(root: Path, base: str) -> list[str] | None:
    diff = git(root, "diff", f"{base}...HEAD", "-U0")
    return None if diff is None else find_secrets(added_lines(diff))


def scan_staged(root: Path) -> list[str]:
    return find_secrets(added_lines(git(root, "diff", "--cached", "-U0") or ""))
