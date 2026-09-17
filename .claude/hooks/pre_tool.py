"""PreToolUse dispatcher: one process, every guard, first block wins (exit 2 feeds the reason back).

Order: cheap and certain first (bypass, secrets, quality, test integrity), network last (dependencies),
investigation gate at the end so it only fires on edits that would otherwise be allowed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import bypass_guard, deps_guard, fact_force, quality_guard, secrets_guard, test_guard
from lib.common import project_root, read_payload, target_path


def main() -> int:
    payload = read_payload()
    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    root = project_root(payload)
    path = target_path(tool_input, root)

    decisions = (
        lambda: bypass_guard.check(tool, tool_input),
        lambda: secrets_guard.check(tool, tool_input, root),
        lambda: quality_guard.check(tool, tool_input, path, root),
        lambda: test_guard.check(tool, tool_input, path, root),
        lambda: deps_guard.check(tool, tool_input),
        lambda: fact_force.check(tool, path, root, str(payload.get("session_id", ""))),
    )
    for decide in decisions:
        decision = decide()
        if decision.block:
            print(decision.message, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
