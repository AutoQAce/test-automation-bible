"""Block commands that skip or destroy the quality gates themselves."""

import re
from typing import Any

from .common import ALLOW, Decision, deny

# [^;&|]* keeps each check inside one command of a chained shell line.
BYPASSES: dict[str, re.Pattern[str]] = {
    "--no-verify skips git hooks": re.compile(r"\bgit\b[^;&|]*\s--no-verify\b"),
    "git commit -n skips git hooks": re.compile(r"\bgit\s+commit\b[^;&|]*\s-[a-mo-zA-Z]*n[a-zA-Z]*(?=\s|$)"),
    "overriding core.hooksPath disables git hooks": re.compile(r"(?i)-c\s+core\.hookspath\s*="),
    "SKIP= disables pre-commit hooks": re.compile(r"(?:^|[\s;&|])SKIP=\S+"),
    "PRE_COMMIT_ALLOW_NO_CONFIG bypasses pre-commit": re.compile(r"\bPRE_COMMIT_ALLOW_NO_CONFIG\b"),
    "force push rewrites shared history": re.compile(r"\bgit\s+push\b[^;&|]*\s(?:--force(?![-\w])|-f\b)"),
    "hard reset discards work": re.compile(r"\bgit\s+reset\b[^;&|]*--hard\b"),
    "deleting git hooks": re.compile(r"\brm\b[^;&|]*\.git[/\\]hooks"),
    "deleting tests": re.compile(
        r"\b(?:rm|git\s+rm|del|Remove-Item)\b[^;&|]*(?:\btests?[/\\]|\btest_\w+\.py\b|_test\.py\b)"
    ),
}


def check(tool: str, tool_input: dict[str, Any]) -> Decision:
    if tool not in ("Bash", "PowerShell"):
        return ALLOW
    command = str(tool_input.get("command", ""))
    reasons = [reason for reason, rx in BYPASSES.items() if rx.search(command)]
    if not reasons:
        return ALLOW
    return deny(
        f"BLOCKED: {'; '.join(reasons)}. Fix the underlying failure instead of bypassing the gate. "
        "If a human explicitly asked for this, they can run it themselves."
    )
