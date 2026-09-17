"""PostToolUse: record the trajectory, then format and lint any Python file just edited.

Lint findings that ruff cannot auto-fix are fed back to the agent (exit 2) so it fixes them now,
not at the end of the task.
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.common import EDIT_TOOLS, project_root, read_payload, state_dir, target_path
from lib.secrets_guard import PATTERNS

MAX_FIELD_CHARS = 500
LINT_TIMEOUT_S = 60


def redact(text: str) -> str:
    for pattern in PATTERNS.values():
        text = pattern.sub("[REDACTED]", text)
    return text


def trace(payload: dict[str, object], root: Path) -> None:
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tool": payload.get("tool_name"),
        "input": redact(json.dumps(payload.get("tool_input"), default=str))[:MAX_FIELD_CHARS],
        "response": redact(json.dumps(payload.get("tool_response"), default=str))[:MAX_FIELD_CHARS],
    }
    out = state_dir(root, "traces") / f"{payload.get('session_id', 'unknown')}.jsonl"
    with out.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def lint_python(path: Path, root: Path) -> str | None:
    uv = shutil.which("uv")
    if uv is None:
        return None
    ruff = [uv, "run", "--no-sync", "ruff"]
    subprocess.run([*ruff, "format", str(path)], cwd=root, capture_output=True, timeout=LINT_TIMEOUT_S)
    result = subprocess.run(
        [*ruff, "check", "--fix", "--output-format", "concise", str(path)],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=LINT_TIMEOUT_S,
    )
    return result.stdout.strip() if result.returncode != 0 else None


def main() -> int:
    payload = read_payload()
    root = project_root(payload)
    try:
        trace(payload, root)
    except OSError as exc:  # observability must not break the agent loop, but must not hide failure
        print(f"trace hook error: {exc}", file=sys.stderr)

    if payload.get("tool_name") not in EDIT_TOOLS:
        return 0
    path = target_path(payload.get("tool_input") or {}, root)
    if path is None or path.suffix != ".py" or not path.exists():
        return 0
    findings = lint_python(path, root)
    if findings:
        print(f"ruff found issues it could not auto-fix; fix them now:\n{findings}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
