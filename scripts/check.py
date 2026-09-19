"""Every quality gate for the test automation framework in one command.

CI, pre-push, and the agent's Stop hook all run this.

    uv run python scripts/check.py          # full
    uv run python scripts/check.py --fast   # agent loop (fail fast)
    uv run python scripts/check.py --red-phase   # fast gates except self-tests (Stop hook, tests first)

Gating tests are framework self-tests (markers `unit`, `contract`). Suites that drive a real
browser, desktop app or API (markers `web`, `desktop`, `api`) run in CI jobs with environments.
"""

import argparse
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC_CONTEXT_MAX_LINES = 150  # AGENTS.md is loaded on every agent turn; keep it lean
MAX_MODULE_LINES = 400  # a module this long almost always holds more than one responsibility
SIZE_CHECKED_DIRS = ("src", "tests", ".claude/hooks", "scripts")
NO_TESTS_COLLECTED = 5  # pytest exit code
UV = shutil.which("uv") or "uv"

type Gate = Callable[[], tuple[bool, str]]


def uv_run(*args: str) -> list[str]:
    return [UV, "run", "--no-sync", *args]


SELF_TESTS = ("pytest", "-q", "-m", "unit or contract", "-p", "no:cacheprovider")
FULL = (
    ("format", uv_run("ruff", "format", "--check", ".")),
    ("lint + design rules", uv_run("ruff", "check", ".")),
    ("types", uv_run("mypy")),
    (
        "framework self-tests + coverage",
        uv_run(*SELF_TESTS, "--cov", "--cov-report=term-missing:skip-covered"),
    ),
    ("architecture rules (layers.toml)", uv_run("python", "scripts/architecture_check.py")),
    ("test hygiene", uv_run("python", "scripts/hygiene_check.py")),
    ("hidden unicode", uv_run("python", ".claude/hooks/scan.py", "hidden-unicode")),
    ("docs match code (OpenWiki claims)", uv_run("python", "scripts/verify_wiki.py")),
    ("vulnerable dependencies", uv_run("pip-audit", "--skip-editable", "--progress-spinner", "off")),
)
FAST = (
    ("lint + design rules", uv_run("ruff", "check", ".")),
    ("types", uv_run("mypy")),
    ("framework self-tests", uv_run(*SELF_TESTS, "-x")),
    ("architecture rules (layers.toml)", uv_run("python", "scripts/architecture_check.py")),
    ("test hygiene", uv_run("python", "scripts/hygiene_check.py")),
)


def static_context_budget() -> tuple[bool, str]:
    lines = len((ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines())
    return lines <= STATIC_CONTEXT_MAX_LINES, (
        f"AGENTS.md has {lines} lines (max {STATIC_CONTEXT_MAX_LINES}); move procedures into skills."
    )


def module_size() -> tuple[bool, str]:
    oversized = [
        f"{path.relative_to(ROOT).as_posix()} ({lines} lines)"
        for folder in SIZE_CHECKED_DIRS
        if (ROOT / folder).exists()
        for path in (ROOT / folder).rglob("*.py")
        if (lines := len(path.read_text(encoding="utf-8").splitlines())) > MAX_MODULE_LINES
    ]
    return not oversized, f"Modules over {MAX_MODULE_LINES} lines; split by responsibility: {oversized}"


IN_PROCESS: tuple[tuple[str, Gate], ...] = (
    ("static context budget", static_context_budget),
    ("module size (single responsibility)", module_size),
)


def select_gates(*, fast: bool, red_phase: bool) -> tuple[tuple[str, list[str]], ...]:
    """Red phase = fast gates minus the self-tests: tests written first are expected to fail."""
    if not red_phase:
        return FAST if fast else FULL
    return tuple((name, command) for name, command in FAST if "pytest" not in command)


def report(name: str, ok: bool, detail: str, elapsed: float = 0.0) -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {name} ({elapsed:.1f}s)")
    if not ok:
        print(detail.strip()[-6000:])
    return ok


def run_gate(name: str, gate: Gate) -> bool:
    return report(name, *gate())


def run_command(name: str, command: list[str]) -> bool:
    started = time.monotonic()
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    ok = result.returncode in (0, NO_TESTS_COLLECTED) if "pytest" in command else result.returncode == 0
    return report(name, ok, result.stdout + result.stderr, time.monotonic() - started)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true")
    parser.add_argument(
        "--red-phase", action="store_true", help="fast gates except self-tests (tests written before code)"
    )
    args = parser.parse_args()
    fast = args.fast or args.red_phase
    checks: list[tuple[str, Callable[[], bool]]] = [
        (name, partial(run_gate, name, gate)) for name, gate in IN_PROCESS
    ]
    gates = select_gates(fast=args.fast, red_phase=args.red_phase)
    checks += [(name, partial(run_command, name, cmd)) for name, cmd in gates]
    failed: list[str] = []
    for name, check in checks:
        if not check():
            failed.append(name)
            if fast:
                break
    if failed:
        print(f"\nFailed gates: {', '.join(failed)}")
        return 1
    print("\nAll gates passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
