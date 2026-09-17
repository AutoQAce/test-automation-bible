"""Shared hook plumbing: decisions, paths, and what a tool call is about to write."""

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EDIT_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})


@dataclass(frozen=True, slots=True)
class Decision:
    block: bool
    message: str = ""


ALLOW = Decision(block=False)


def deny(message: str) -> Decision:
    return Decision(block=True, message=message)


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}


def project_root(payload: dict[str, Any]) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()


def state_dir(root: Path, *parts: str) -> Path:
    path = root.joinpath(".sdlc", *parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


def target_path(tool_input: dict[str, Any], root: Path) -> Path | None:
    raw = tool_input.get("file_path")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_absolute() else root / path


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_existing(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def before_after(tool: str, tool_input: dict[str, Any], path: Path | None) -> tuple[str, str]:
    """Return (text before, text after) for the part of the file this call changes.

    Edit/MultiEdit return only the replaced fragments; Write returns whole files.
    """
    if tool == "Write":
        return read_existing(path), str(tool_input.get("content", ""))
    if tool == "Edit":
        return str(tool_input.get("old_string", "")), str(tool_input.get("new_string", ""))
    if tool == "MultiEdit":
        edits = tool_input.get("edits") or []
        old = "\n".join(str(e.get("old_string", "")) for e in edits)
        new = "\n".join(str(e.get("new_string", "")) for e in edits)
        return old, new
    return "", ""


def apply_edit(tool: str, tool_input: dict[str, Any], current: str) -> str:
    """Simulate the whole file after this call (used where a fragment is not enough)."""
    if tool == "Write":
        return str(tool_input.get("content", ""))
    edits = tool_input.get("edits") if tool == "MultiEdit" else [tool_input]
    result = current
    for edit in edits or []:
        old, new = str(edit.get("old_string", "")), str(edit.get("new_string", ""))
        result = result.replace(old, new) if edit.get("replace_all") else result.replace(old, new, 1)
    return result
