"""Investigate and design before editing (a lightweight port of ECC's GateGuard).

Self-evaluation ("are you sure?") does not change model behavior. Demanding concrete facts
does: the first edit of each source file per session is denied once with the facts to state,
including the design facts (layer, single responsibility, dependency direction). The retry
goes through. Disable with SDLC_FACT_FORCE=0.
"""

import json
import os
from pathlib import Path

from .common import ALLOW, EDIT_TOOLS, Decision, deny, relative, state_dir

FULL_DENIALS = 3  # afterwards messages are condensed so they don't flood the context window

EXISTING_FILE_FACTS = (
    "1. Every module that imports {rel} (search for it).\n"
    "2. The public functions/classes whose behavior this edit changes.\n"
    "3. Data shapes it reads or writes (field names and types; synthetic values only).\n"
    "4. Design check: does the change keep this module's single responsibility and the layer "
    "rules in docs/design/layers.toml (e.g. no driver library outside the driver layer, no "
    "locators or driver calls in tests)? If not, what should be extracted or moved?\n"
    "5. The user's current instruction, quoted verbatim."
)
NEW_FILE_FACTS = (
    "1. Which layer {rel} belongs to and its single responsibility, in one sentence.\n"
    "2. Evidence that no existing module already does this (search for it).\n"
    "3. Which module will import it, and which abstractions (ports/Protocols) it depends on.\n"
    "4. The LLD or task section it implements (docs/design or docs/tasks), if one exists.\n"
    "5. The user's current instruction, quoted verbatim."
)


def gated_prefixes() -> tuple[str, ...]:
    # Default "src/"; set to the framework and test roots chosen in the HLD.
    raw = os.environ.get("SDLC_FACT_FORCE_PATHS", "src/")
    return tuple(p.strip() for p in raw.split(",") if p.strip())


def check(tool: str, path: Path | None, root: Path, session_id: str) -> Decision:
    rel = _gated_path(tool, path, root)
    if rel is None or path is None:
        return ALLOW
    denials = _record_first_edit(root, session_id, rel)
    if denials is None:
        return ALLOW
    return deny(_message(path, rel, denials))


def _gated_path(tool: str, path: Path | None, root: Path) -> str | None:
    if os.environ.get("SDLC_FACT_FORCE", "1") == "0" or tool not in EDIT_TOOLS:
        return None
    if path is None or path.suffix != ".py":
        return None
    rel = relative(path, root)
    return rel if rel.startswith(gated_prefixes()) else None


def _record_first_edit(root: Path, session_id: str, rel: str) -> int | None:
    """Returns the denial count for a first edit, or None if this file was already checked."""
    state_file = state_dir(root, "fact_force") / f"{session_id or 'unknown'}.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"files": [], "denials": 0}
    if rel in state["files"]:
        return None
    state = {"files": [*state["files"], rel], "denials": state["denials"] + 1}
    state_file.write_text(json.dumps(state))
    return int(state["denials"])


def _message(path: Path, rel: str, denials: int) -> str:
    if denials > FULL_DENIALS:
        return (
            f"Fact check #{denials} for {rel}: state importers, affected API, data shapes, "
            "and the design check (layer, single responsibility), then retry."
        )
    facts = (EXISTING_FILE_FACTS if path.exists() else NEW_FILE_FACTS).format(rel=rel)
    return f"Before changing {rel}, state these facts in your reply, then retry the edit:\n{facts}"
