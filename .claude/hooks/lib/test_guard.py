"""Test-code integrity at write time: the two classic ways an AI "fixes" a failing test.

1. Hard sleeps: `time.sleep` in test code trades a real synchronization problem for slowness and
   flakiness. Use the framework's explicit wait / polling utilities.
2. Weakened oracles: removing or changing an assertion line (or an `expect`/`verify` call) makes a
   test pass by checking less or checking something else, e.g. an expected value edited to match the
   application. Blocked unless the edit carries `sdlc: justified <reason>`. Lines that already carry
   the marker (such as a temporary proof-of-failure assertion) may be changed back freely.
   Only the first line of a multi-line assertion is compared.
"""

import re
from collections import Counter
from pathlib import Path
from typing import Any

from .common import ALLOW, EDIT_TOOLS, Decision, before_after, deny, relative

JUSTIFIED = "sdlc: justified"
SLEEP = re.compile(r"\b(?:time\.)?sleep\s*\(")
ASSERTION = re.compile(
    r"^\s*(?:assert\b|(?:await\s+)?(?:\w+\.)*(?:expect|assert_\w+|verify\w*|should\w*|check_that)\s*\()"
)
WHITESPACE = re.compile(r"\s+")


def is_test_code(path: Path, root: Path) -> bool:
    rel = relative(path, root)
    name = path.name
    in_tests = "/tests/" in f"/{rel}" or rel.startswith("tests/")
    return path.suffix == ".py" and (
        in_tests or name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
    )


def count(pattern: re.Pattern[str], text: str) -> int:
    return sum(1 for line in text.splitlines() if JUSTIFIED not in line and pattern.search(line))


def assertion_lines(text: str) -> Counter[str]:
    """Unjustified assertion lines, whitespace-insensitive so reformatting is not a change."""
    return Counter(
        WHITESPACE.sub("", line)
        for line in text.splitlines()
        if JUSTIFIED not in line and ASSERTION.search(line)
    )


def check(tool: str, tool_input: dict[str, Any], path: Path | None, root: Path) -> Decision:
    if tool not in EDIT_TOOLS or path is None or not is_test_code(path, root):
        return ALLOW
    old, new = before_after(tool, tool_input, path)
    rel = relative(path, root)
    if count(SLEEP, new) > count(SLEEP, old):
        return deny(
            f"BLOCKED: adds a hard sleep in test code ({rel}). Synchronize on a condition with the "
            "framework's explicit wait (element state, response, file, process), never on time."
        )
    if JUSTIFIED in new:
        return ALLOW
    lost = assertion_lines(old) - assertion_lines(new)
    if lost:
        example = next(line.strip() for line in old.splitlines() if WHITESPACE.sub("", line) in lost)
        return deny(
            f"BLOCKED: this edit removes or changes assertions in {rel} (`{example}`). "
            "Making a test pass by checking less, or by changing the expected value to match the "
            "application, is not a fix. If the expected behavior really changed, cite the requirement "
            f"or ticket with '{JUSTIFIED} <reason>' on the changed line."
        )
    return ALLOW
