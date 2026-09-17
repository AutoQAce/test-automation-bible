"""Static hygiene rules for automated tests (AST-based, framework-agnostic).

Catches the defects that make test suites slow, flaky, brittle, or meaningless, especially the
ones AI assistants introduce. A finding can be accepted on its line with `sdlc: justified <reason>`.

    python scripts/hygiene_check.py [paths ...]      # default: tests/

Rules
  H001 hard sleep in a test                         -> use explicit waits
  H002 raw locator (XPath/CSS) in a test            -> belongs in a page/screen object
  H003 skip/skipif/xfail without reason=            -> say why, link a ticket
  H004 missing markers: framework self-tests need unit|contract; automated tests need a platform
       (web|desktop|api) and a level (smoke|regression), or no CI job ever selects them
  H005 ordering/dependency marker                   -> tests must be independent
  H006 test with no oracle (no assert/expect/verify) -> a test that cannot fail is not a test
  H007 hard-coded http(s) URL in a test             -> environment config
  H008 quarantine marker missing reason/until, or expired
"""

import argparse
import ast
import datetime as dt
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

JUSTIFIED = "sdlc: justified"
SELF_TEST_MARKERS = frozenset({"unit", "contract"})
PLATFORM_MARKERS = frozenset({"web", "desktop", "api"})
LEVEL_MARKERS = frozenset({"smoke", "regression"})
FORBIDDEN_MARKERS = frozenset({"order", "dependency", "run"})
SKIP_MARKERS = frozenset({"skip", "skipif", "xfail"})
ORACLE_CALL = re.compile(r"^(?:expect|assert_\w*|verify\w*|should\w*|check_that)$")
LOCATOR = re.compile(r"^(?:\(?//|xpath=|css=|#[\w-]+[\s.>\[]|\.[\w-]+\s*[>+~]|\[data-[\w-]+=)")
URL = re.compile(r"^https?://", re.IGNORECASE)


@dataclass(frozen=True, slots=True, order=True)
class Finding:
    path: str
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule} {self.message}"


def marker_name(decorator: ast.expr) -> str | None:
    """`pytest.mark.web` or `pytest.mark.skip(reason=...)` -> 'web' / 'skip'."""
    node = decorator.func if isinstance(decorator, ast.Call) else decorator
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "mark"
    ):
        return node.attr
    return None


def keyword(decorator: ast.expr, name: str) -> ast.expr | None:
    if isinstance(decorator, ast.Call):
        return next((k.value for k in decorator.keywords if k.arg == name), None)
    return None


def module_markers(tree: ast.Module) -> set[str]:
    markers: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets
        ):
            values = node.value.elts if isinstance(node.value, ast.List | ast.Tuple) else [node.value]
            markers.update(m for v in values if (m := marker_name(v)))
    return markers


def test_functions(
    tree: ast.Module,
) -> Iterator[tuple[ast.FunctionDef | ast.AsyncFunctionDef, list[ast.expr]]]:
    """Yield each test function with the decorators that apply to it (its own + its class's)."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test"):
            yield node, list(node.decorator_list)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name.startswith("test"):
                    yield item, [*node.decorator_list, *item.decorator_list]


def has_oracle(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(function):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if ORACLE_CALL.match(name) or name == "raises":
                return True
    return False


def decorator_findings(rel: str, decorators: list[ast.expr], today: dt.date) -> Iterator[Finding]:
    for decorator in decorators:
        name = marker_name(decorator)
        if name in SKIP_MARKERS and keyword(decorator, "reason") is None:
            yield Finding(rel, decorator.lineno, "H003", f"@pytest.mark.{name} needs reason=")
        elif name in FORBIDDEN_MARKERS:
            yield Finding(rel, decorator.lineno, "H005", f"@pytest.mark.{name}: tests must be independent")
        elif name == "quarantine":
            yield from quarantine_findings(rel, decorator, today)


def quarantine_findings(rel: str, decorator: ast.expr, today: dt.date) -> Iterator[Finding]:
    reason, until = keyword(decorator, "reason"), keyword(decorator, "until")
    if reason is None or not isinstance(until, ast.Constant) or not isinstance(until.value, str):
        yield Finding(
            rel, decorator.lineno, "H008", 'quarantine needs reason="TICKET-123 ..." and until="YYYY-MM-DD"'
        )
        return
    try:
        expired = dt.date.fromisoformat(until.value) < today
    except ValueError:
        yield Finding(rel, decorator.lineno, "H008", f"quarantine until={until.value!r} is not YYYY-MM-DD")
        return
    if expired:
        yield Finding(
            rel, decorator.lineno, "H008", f"quarantine expired on {until.value}: fix or delete the test"
        )


def body_findings(rel: str, function: ast.FunctionDef | ast.AsyncFunctionDef) -> Iterator[Finding]:
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if name == "sleep":
                yield Finding(rel, node.lineno, "H001", "hard sleep: wait for a condition instead")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if LOCATOR.match(node.value.strip()):
                yield Finding(
                    rel, node.lineno, "H002", "raw locator in a test: move it to a page/screen object"
                )
            elif URL.match(node.value):
                yield Finding(rel, node.lineno, "H007", "hard-coded URL: read it from environment config")


def marker_problem(markers: set[str]) -> str | None:
    if markers & SELF_TEST_MARKERS:
        return None
    missing = [
        f"no {kind} marker ({'|'.join(sorted(options))})"
        for kind, options in (("platform", PLATFORM_MARKERS), ("level", LEVEL_MARKERS))
        if not markers & options
    ]
    return " and ".join(missing) or None


def check_source(rel: str, source: str, today: dt.date) -> list[Finding]:
    tree = ast.parse(source)
    lines = source.splitlines()
    inherited = module_markers(tree)
    findings: list[Finding] = []
    for function, decorators in test_functions(tree):
        markers = inherited | {m for d in decorators if (m := marker_name(d))}
        findings += decorator_findings(rel, decorators, today)
        if problem := marker_problem(markers):
            findings.append(Finding(rel, function.lineno, "H004", f"{function.name} {problem}"))
        if not has_oracle(function):
            findings.append(
                Finding(rel, function.lineno, "H006", f"{function.name} has no assertion or expect/verify")
            )
        findings += body_findings(rel, function)
    return sorted(f for f in set(findings) if JUSTIFIED not in lines[f.line - 1])


def test_files(paths: list[Path]) -> Iterator[Path]:
    for base in paths:
        candidates = [base] if base.is_file() else sorted(base.rglob("*.py"))
        yield from (p for p in candidates if p.name.startswith("test_") or p.name.endswith("_test.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("tests")])
    args = parser.parse_args()
    existing = [p for p in args.paths if p.exists()]
    if not existing:
        print("SKIP: no test paths found yet.")
        return 0
    today = dt.datetime.now(dt.UTC).date()
    findings = [
        f
        for path in test_files(existing)
        for f in check_source(path.as_posix(), path.read_text(encoding="utf-8"), today)
    ]
    for finding in findings:
        print(finding)
    print(f"{len(findings)} test hygiene finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
