"""Stop hook = the self-correction loop: the agent cannot declare done while gates fail.

Runs SDLC_TEST_CMD (default: scripts/check.py --fast) when the working tree changed. On failure
the output goes back to the agent (exit 2), at most SDLC_MAX_FIX_ATTEMPTS times per task; then a
human takes over. Set SDLC_TEST_CMD=off to disable.

Red phase (tests written before the code they specify): if the only changed Python files are test
code and SDLC_RED_PHASE_CMD (default: check.py --red-phase, every fast gate except the self-tests)
passes, the agent may stop and the user is told the tests are red. Pre-push and CI still require
green tests. Set SDLC_RED_PHASE_CMD=off to disable.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import project_root, read_payload, state_dir
from lib.test_guard import is_test_code

DEFAULT_CMD = "uv run --no-sync python scripts/check.py --fast"
RED_PHASE_CMD = "uv run --no-sync python scripts/check.py --red-phase"
RED_PHASE_MESSAGE = (
    "Red phase: framework self-tests are failing, only test files changed, and every other fast gate "
    "passes. Stopping is allowed so the implementation can follow; pre-push and CI still require "
    "green tests. If you did not intend to write failing tests first, fix them now."
)
OUTPUT_TAIL_CHARS = 4000
TIMEOUT_S = 570  # under the 600s hook timeout in settings.json


def run_gates(command: str, root: Path) -> tuple[bool, str]:
    try:
        # Command comes from project settings, not from the model.
        result = subprocess.run(  # noqa: S602  sdlc: justified trusted settings value
            command,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return False, f"Quality gates timed out after {TIMEOUT_S}s."
    return result.returncode == 0, result.stdout + result.stderr


def changed_paths(root: Path) -> list[str] | None:
    """Changed and untracked files relative to root, or None when git cannot tell."""
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return None  # no git: cannot tell what changed, so verify anyway
    if status.returncode != 0:
        return None
    # "XY path" or "XY old -> new"; quoted paths (unusual characters) never count as test code.
    return [line[3:].split(" -> ")[-1] for line in status.stdout.splitlines() if line.strip()]


def is_red_phase(root: Path, paths: list[str]) -> bool:
    command = os.environ.get("SDLC_RED_PHASE_CMD", "").strip() or RED_PHASE_CMD
    python_files = [root / path for path in paths if path.endswith(".py")]
    test_files = [path for path in python_files if is_test_code(path, root)]
    if command == "off" or not test_files or len(test_files) != len(python_files):
        return False
    return run_gates(command, root)[0]


def fix_or_hand_over(counter: Path, command: str, output: str) -> int:
    """Feed the failure back (exit 2) until the retry cap, then let a human take over."""
    attempts = int(counter.read_text()) if counter.exists() else 0
    limit = int(os.environ.get("SDLC_MAX_FIX_ATTEMPTS", "3"))
    if attempts >= limit:
        counter.unlink(missing_ok=True)  # fresh budget for the next human-directed attempt
        message = (
            f"Quality gates still failing after {limit} automatic fix attempts. Human needed: "
            "usually an ambiguous spec, a wrong assumption, or an architectural issue."
        )
        print(json.dumps({"systemMessage": message}))
        return 0
    counter.write_text(str(attempts + 1))
    print(
        f"Quality gates failed (`{command}`), fix attempt {attempts + 1}/{limit}. "
        "Diagnose the root cause and fix the code. "
        "Do not weaken, skip, or delete tests or checks. "
        f"If the spec is ambiguous, stop and ask.\n\n{output[-OUTPUT_TAIL_CHARS:]}",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    command = os.environ.get("SDLC_TEST_CMD", "").strip() or DEFAULT_CMD
    if command == "off":
        return 0
    payload = read_payload()
    root = project_root(payload)
    paths = changed_paths(root)
    if paths == []:
        return 0  # nothing changed, nothing to verify

    counter = state_dir(root, "fix_attempts") / str(payload.get("session_id", "unknown"))
    passed, output = run_gates(command, root)
    if passed:
        counter.unlink(missing_ok=True)
        return 0
    if paths and is_red_phase(root, paths):
        print(json.dumps({"systemMessage": RED_PHASE_MESSAGE}))
        return 0
    return fix_or_hand_over(counter, command, output)


if __name__ == "__main__":
    sys.exit(main())
