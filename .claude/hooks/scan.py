"""Repository scans for CI and pre-commit.

    python .claude/hooks/scan.py secrets --diff origin/main   # lines added on this branch
    python .claude/hooks/scan.py secrets --staged             # pre-commit
    python .claude/hooks/scan.py hidden-unicode               # all tracked text files

Hidden Unicode (zero-width, bidi overrides) in prompts, skills, rules or code is invisible to
reviewers and fully visible to models: treat it as a supply-chain attack.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib.secrets_guard import scan_diff, scan_staged

TEXT_SUFFIXES = frozenset({".py", ".md", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".txt", ".cfg", ".ini"})
HIDDEN_CODEPOINTS = (
    0x00AD,
    *range(0x200B, 0x2010),
    *range(0x202A, 0x202F),
    *range(0x2060, 0x2065),
    *range(0x2066, 0x206A),
    0xFEFF,
)
HIDDEN = re.compile("[" + "".join(re.escape(chr(c)) for c in HIDDEN_CODEPOINTS) + "]")


def hidden_unicode(root: Path) -> list[str]:
    listed = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True)
    findings = []
    for rel in listed.stdout.splitlines():
        path = root / rel
        if path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for match in HIDDEN.finditer(line):
                findings.append(f"{rel}:{number}: U+{ord(match.group(0)):04X}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="scan", required=True)
    secrets = sub.add_parser("secrets")
    group = secrets.add_mutually_exclusive_group(required=True)
    group.add_argument("--diff", metavar="BASE")
    group.add_argument("--staged", action="store_true")
    sub.add_parser("hidden-unicode")
    args = parser.parse_args()
    root = Path.cwd()

    if args.scan == "hidden-unicode":
        findings = hidden_unicode(root)
        label = "hidden Unicode characters"
    elif args.staged:
        findings = scan_staged(root)
        label = "possible secrets in staged changes"
    else:
        result = scan_diff(root, args.diff)
        if result is None:
            print(f"cannot diff against {args.diff} (fetch full history?)", file=sys.stderr)
            return 1
        findings, label = result, f"possible secrets added since {args.diff}"

    if findings:
        print(f"{label}:\n  " + "\n  ".join(findings), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
