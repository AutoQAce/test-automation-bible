"""Slopsquatting defense at install time.

Agents hallucinate package names and attackers register them. Before `uv add` / `pip install`
runs, every named package must exist on PyPI and be older than SDLC_MIN_PACKAGE_AGE_DAYS.
Fails closed: if PyPI cannot be reached, the install is blocked.
"""

import datetime as dt
import json
import os
import re
import shlex
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from .common import ALLOW, Decision, deny

INSTALL = re.compile(
    r"\b(?:uv\s+add|uv\s+pip\s+install|pip3?\s+install|python3?\s+-m\s+pip\s+install|poetry\s+add|pipx\s+install)\b([^;&|]*)"
)
FLAGS_WITH_VALUE = frozenset(
    {
        "-r",
        "--requirement",
        "-c",
        "--constraint",
        "-e",
        "--editable",
        "--group",
        "--extra",
        "--optional",
        "-i",
        "--index-url",
        "--extra-index-url",
        "--index",
        "--python",
        "-p",
        "--source",
        "--package",
        "--tag",
        "--branch",
        "--rev",
        "--marker",
        "-m",
        "--target",
    }
)
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")
HTTP_NOT_FOUND = 404

# name -> ISO date of first upload, or None when the package does not exist.
type Lookup = Callable[[str], str | None]


def pypi_first_upload(name: str) -> str | None:
    url = f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == HTTP_NOT_FOUND:
            return None
        raise
    uploads = [f["upload_time_iso_8601"] for files in data.get("releases", {}).values() for f in files]
    return min(uploads) if uploads else ""


def package_names(command: str) -> list[str]:
    names: list[str] = []
    for match in INSTALL.finditer(command):
        try:
            tokens = shlex.split(match.group(1))
        except ValueError:
            tokens = match.group(1).split()
        skip_next = False
        for token in tokens:
            if skip_next:
                skip_next = False
                continue
            if token.startswith("-"):
                skip_next = token in FLAGS_WITH_VALUE
                continue
            if token.startswith((".", "/", "\\", "git+", "http://", "https://", "file:")) or token.endswith(
                (".whl", ".tar.gz", ".txt")
            ):
                continue
            found = NAME.match(token)
            if found:
                names.append(found.group(0).lower())
    return names


def problem_with(name: str, lookup: Lookup, min_age_days: int) -> str | None:
    """Why this package must not be installed, or None if it is fine."""
    try:
        first_upload = lookup(name)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return f"{name}: could not verify on PyPI ({exc})"
    if first_upload is None:
        return f"{name}: does not exist on PyPI (hallucinated or misspelled?)"
    if not first_upload:
        return None
    created = dt.datetime.fromisoformat(first_upload.replace("Z", "+00:00"))
    age = (dt.datetime.now(dt.UTC) - created).days
    return f"{name}: first published {age} days ago (< {min_age_days})" if age < min_age_days else None


def check(tool: str, tool_input: dict[str, Any], lookup: Lookup = pypi_first_upload) -> Decision:
    if tool not in ("Bash", "PowerShell"):
        return ALLOW
    allowed = {p.strip().lower() for p in os.environ.get("SDLC_ALLOW_PACKAGES", "").split(",") if p.strip()}
    min_age = int(os.environ.get("SDLC_MIN_PACKAGE_AGE_DAYS", "30"))
    names = [n for n in package_names(str(tool_input.get("command", ""))) if n not in allowed]
    problems = [p for n in names if (p := problem_with(n, lookup, min_age))]
    if not problems:
        return ALLOW
    return deny(
        "BLOCKED dependency install: " + "; ".join(problems) + ". Check the exact package name. "
        "A human can approve a new package by adding it to SDLC_ALLOW_PACKAGES."
    )
