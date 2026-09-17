"""Enforce the layer rules your HLD defines, without prescribing a folder structure.

The HLD phase writes `docs/design/layers.toml` (start from `docs/design/_layers.example.toml`).
Until it exists this check reports SKIP and passes. Once it exists, every rule is a CI gate:

* layer dependencies point only where the HLD allows (e.g. tests -> page objects, never -> drivers)
* third-party libraries (Playwright, Selenium, pywinauto, zeep, ...) are imported only by the
  layers that own them (e.g. only the web driver layer imports the browser engine)

    python scripts/architecture_check.py [--config docs/design/layers.toml]
"""

import argparse
import ast
import sys
import tomllib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = Path("docs/design/layers.toml")


@dataclass(frozen=True, slots=True)
class Layer:
    name: str
    paths: tuple[str, ...]
    may_import: frozenset[str]


@dataclass(frozen=True, slots=True)
class Rules:
    layers: tuple[Layer, ...]
    library_owners: dict[str, frozenset[str]]  # top-level library -> layers allowed to import it


def load_rules(text: str) -> Rules:
    data = tomllib.loads(text)
    layers = tuple(
        Layer(
            name=name,
            paths=tuple(spec["paths"]),
            may_import=frozenset(spec.get("may_import", [])),
        )
        for name, spec in data.get("layers", {}).items()
    )
    owners = {lib: frozenset(names) for lib, names in data.get("library_owners", {}).items()}
    return Rules(layers=layers, library_owners=owners)


def layer_for(path: str, layers: tuple[Layer, ...]) -> Layer | None:
    """Most specific (longest) matching path prefix wins."""
    matches = [(len(p), layer) for layer in layers for p in layer.paths if path.startswith(p)]
    return max(matches, key=lambda m: m[0])[1] if matches else None


def module_to_path(module: str) -> str:
    return module.replace(".", "/")


def imports_of(source: str) -> Iterator[tuple[int, str]]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            yield from ((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.lineno, node.module


def violations_in(rel: str, source: str, rules: Rules) -> list[str]:
    owner = layer_for(rel, rules.layers)
    if owner is None:
        return []
    found: list[str] = []
    for line, module in imports_of(source):
        library = module.split(".")[0]
        allowed_layers = rules.library_owners.get(library)
        if allowed_layers is not None and owner.name not in allowed_layers:
            found.append(
                f"{rel}:{line}: layer '{owner.name}' imports '{library}' (owned by {sorted(allowed_layers)})"
            )
            continue
        target = layer_for(module_to_path(module), rules.layers) or layer_for(
            f"src/{module_to_path(module)}", rules.layers
        )
        if target and target.name != owner.name and target.name not in owner.may_import:
            found.append(
                f"{rel}:{line}: layer '{owner.name}' may not import layer '{target.name}' ({module})"
            )
    return found


def check_repository(root: Path, rules: Rules) -> list[str]:
    results: list[str] = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith((".venv/", ".claude/", "scripts/")):
            continue
        results += violations_in(rel, path.read_text(encoding="utf-8"), rules)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    if not args.config.exists():
        print(f"SKIP: {args.config} not found. Create it during the HLD phase (skill system-design-hld).")
        return 0
    violations = check_repository(Path.cwd(), load_rules(args.config.read_text(encoding="utf-8")))
    for violation in violations:
        print(violation)
    print(f"{len(violations)} architecture violation(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
