"""Direct dependencies must exist on PyPI and not be brand new (slopsquatting defense in CI).

`uv lock` already fails on packages that do not exist; this adds the age check and a clear
report, and runs before anything is installed.

    python scripts/verify_deps.py [--min-age-days 30]
"""

import argparse
import datetime as dt
import re
import sys
import tomllib
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from lib.deps_guard import (
    pypi_first_upload,
)

NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def direct_dependencies(pyproject: dict[str, object]) -> list[str]:
    project = pyproject.get("project", {})
    assert isinstance(project, dict)  # noqa: S101  sdlc: justified pyproject schema
    specs: list[str] = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        specs += extra
    groups = pyproject.get("dependency-groups", {})
    assert isinstance(groups, dict)  # noqa: S101  sdlc: justified pyproject schema
    for group in groups.values():
        specs += [s for s in group if isinstance(s, str)]
    names = {m.group(1).lower() for s in specs if (m := NAME.match(s))}
    return sorted(names)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-age-days", type=int, default=30)
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    args = parser.parse_args()

    names = direct_dependencies(tomllib.loads(args.pyproject.read_text(encoding="utf-8")))
    failed = False
    for name in names:
        try:
            first_upload = pypi_first_upload(name)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"UNVERIFIED {name}: {exc}")
            failed = True
            continue
        if first_upload is None:
            print(f"MISSING    {name}: not on PyPI (hallucinated or misspelled?)")
            failed = True
            continue
        created = dt.datetime.fromisoformat(first_upload.replace("Z", "+00:00")) if first_upload else None
        age = (dt.datetime.now(dt.UTC) - created).days if created else None
        if age is not None and age < args.min_age_days:
            print(f"NEW        {name}: first published {age} days ago; needs human review")
            failed = True
        else:
            print(f"ok         {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
