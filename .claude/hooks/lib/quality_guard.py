"""Stop agents from making checks pass by weakening them.

Three moves are blocked: editing lint/type/test/coverage config, adding suppression markers
(noqa, type: ignore, pragma: no cover, nosec, skip/xfail) without a written justification, and
lowering the bar inside pyproject.toml's [tool.*] quality sections.
"""

import re
import tomllib
from pathlib import Path
from typing import Any

from .common import ALLOW, Decision, apply_edit, before_after, deny, read_existing, relative

PROTECTED_FILES = frozenset(
    {
        "ruff.toml",
        ".ruff.toml",
        "mypy.ini",
        ".mypy.ini",
        "setup.cfg",
        "pytest.ini",
        ".coveragerc",
        "tox.ini",
        ".pre-commit-config.yaml",
    }
)
QUALITY_TOOL_SECTIONS = ("ruff", "mypy", "pytest", "coverage", "bandit", "pyright")
JUSTIFIED = "sdlc: justified"
SUPPRESSIONS: dict[str, re.Pattern[str]] = {
    "# noqa": re.compile(r"#\s*noqa\b", re.IGNORECASE),
    "# type: ignore": re.compile(r"#\s*type:\s*ignore\b"),
    "# pragma: no cover": re.compile(r"#\s*pragma:\s*no\s*cover\b"),
    "# nosec": re.compile(r"#\s*nosec\b"),
    "pytest skip/xfail": re.compile(r"(@pytest\.mark\.(?:skip|skipif|xfail)\b|\bpytest\.(?:skip|xfail)\()"),
    # Retries hide flakiness instead of fixing it; quarantine is the only accepted path.
    "retry/flaky masking": re.compile(
        r"(@pytest\.mark\.flaky\b|\breruns\s*=|--reruns\b|\bpytest_rerunfailures\b)"
    ),
    # Tests must be independent; ordering and dependency markers hide shared state.
    "test ordering/dependency": re.compile(r"@pytest\.mark\.(?:order|dependency|run)\b"),
}


def count_unjustified(text: str) -> dict[str, int]:
    counts = dict.fromkeys(SUPPRESSIONS, 0)
    for line in text.splitlines():
        if JUSTIFIED in line:
            continue
        for name, rx in SUPPRESSIONS.items():
            counts[name] += bool(rx.search(line))
    return counts


def quality_sections(toml_text: str) -> dict[str, Any] | None:
    try:
        tools = tomllib.loads(toml_text).get("tool", {})
    except tomllib.TOMLDecodeError:
        return None
    return {name: tools.get(name) for name in QUALITY_TOOL_SECTIONS}


def check(tool: str, tool_input: dict[str, Any], path: Path | None, root: Path) -> Decision:
    if tool not in ("Write", "Edit", "MultiEdit") or path is None:
        return ALLOW
    rel = relative(path, root)

    if path.name in PROTECTED_FILES and path.exists():
        return deny(
            f"BLOCKED: {rel} configures a quality gate. Fix the code so the check passes; "
            "changing the gate needs a human-approved PR."
        )

    if path.name == "pyproject.toml" and path.exists():
        current = read_existing(path)
        before, after = (
            quality_sections(current),
            quality_sections(apply_edit(tool, tool_input, current)),
        )
        if before is not None and after is not None and before != after:
            changed = [name for name in QUALITY_TOOL_SECTIONS if before[name] != after[name]]
            return deny(
                f"BLOCKED: this edit changes [tool.{', tool.'.join(changed)}] in pyproject.toml. "
                "Dependency and metadata edits are fine; "
                "quality-gate settings need a human-approved PR."
            )

    if path.suffix == ".py":
        old, new = before_after(tool, tool_input, path)
        old_counts, new_counts = count_unjustified(old), count_unjustified(new)
        added = [name for name in SUPPRESSIONS if new_counts[name] > old_counts[name]]
        if added:
            return deny(
                f"BLOCKED: adds {', '.join(added)} in {rel}. Fix the root cause instead. If the "
                f"suppression is truly correct, keep it on one line with '{JUSTIFIED} <reason>' "
                "so reviewers can judge it."
            )
    return ALLOW
