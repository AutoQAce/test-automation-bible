"""Docs drift gate: every OpenWiki claim must still match the code it cites.

OpenWiki (github.com/langchain-ai/openwiki) grounds each wiki fact in a Claim whose evidence is a
line range such as `repo://src/app.py#L40-L82` plus a sha256 of those lines. This re-hashes the
cited code without any model call and fails when evidence changed or vanished, so a PR that changes
documented behavior cannot merge with a silently wrong wiki. Fix: `openwiki --update`, then commit.
Also warns (never fails) when the wiki is not Open Knowledge Format v0.2: the root index.md must
declare okf_version "0.2" and every concept page needs a front-matter `type` agents can filter on.

    python scripts/verify_wiki.py [--wiki openwiki]

No wiki directory: nothing to check (exit 0). Mirrors OpenWiki 0.5.x (Claims schema v1).
"""

import argparse
import base64
import hashlib
import json
import re
import sys
import urllib.parse
from pathlib import Path

RANGE_PREFIX = "repo-lines-v1:sha256:"
FILE_PREFIX = "repo-file-v1:sha256:"
CLAIMS_SCHEMA_VERSION = 1
OKF_VERSION = "0.2"
CLAIMS_DIR = ".claims"
RESERVED_PAGES = frozenset({"index.md", "log.md", "instructions.md"})
STATEMENT_PREVIEW_CHARS = 160
BASE64_BLOCK = 4
LINE = re.compile(r"[^\n]*\n|[^\n]+\Z")
LINE_RANGE = re.compile(r"L([1-9]\d*)(?:-L([1-9]\d*))?")
FRONT_MATTER = re.compile(r"---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
FRONT_MATTER_KEY = re.compile(r"([A-Za-z_][\w-]*):(?:\s+(.*))?$")

type Span = tuple[int, int]
type Findings = tuple[list[str], list[str], int]  # (stale, warnings, claim count)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_lines(source: str) -> list[str]:
    """Lines keep their newline; a trailing newline adds no phantom line (as OpenWiki splits)."""
    return LINE.findall(source)


def parse_resource(resource: str) -> tuple[str, Span | None]:
    """`repo://path#L1-L5` -> ("path", (1, 5)). Whole-file evidence has no span."""
    if not resource.startswith("repo://"):
        raise ValueError(f"unsupported evidence resource: {resource}")
    body, _, fragment = resource.removeprefix("repo://").partition("#")
    path = urllib.parse.unquote(body)
    if not fragment:
        return path, None
    match = LINE_RANGE.fullmatch(urllib.parse.unquote(fragment))
    if not match:
        raise ValueError(f"bad line range: {resource}")
    start = int(match.group(1))
    return path, (start, int(match.group(2) or start))


def selected_line_count(metadata: str) -> int | None:
    """Line count stored in a range version's base64url relocation metadata."""
    padded = metadata + "=" * (-len(metadata) % BASE64_BLOCK)
    try:
        decoded = json.loads(base64.urlsafe_b64decode(padded))
    except ValueError:
        return None
    count = decoded.get("selectedLineCount") if isinstance(decoded, dict) else None
    return count if isinstance(count, int) and count > 0 else None


def range_is_fresh(lines: list[str], span: Span, version: str) -> bool:
    """Unchanged at the cited lines, or moved but byte-identical elsewhere in the file."""
    content_hash, _, metadata = version.removeprefix(RANGE_PREFIX).partition(":")
    count = selected_line_count(metadata) if version.startswith(RANGE_PREFIX) else None
    if count is None:
        return False
    start, end = span
    at_hint = "".join(lines[start - 1 : end])
    if end <= len(lines) and end - start + 1 == count and sha(at_hint) == content_hash:
        return True
    # Accepts any identical copy; OpenWiki additionally requires the copy to be unique.
    windows = range(len(lines) - count + 1)
    return any(sha("".join(lines[i : i + count])) == content_hash for i in windows)


def check_evidence(root: Path, resource: str, version: str) -> str | None:
    """None when the cited source is unchanged, else why the claim is stale."""
    path, span = parse_resource(resource)
    target = (root / path).resolve()
    if root.resolve() not in target.parents:
        return "evidence escapes the repository"
    if not target.is_file():
        return "cited file no longer exists"
    source = target.read_bytes().decode("utf-8", errors="replace")
    if span is None:
        return None if version == FILE_PREFIX + sha(source) else "cited file changed"
    return None if range_is_fresh(split_lines(source), span, version) else "cited lines changed"


def evidence_problem(root: Path, evidence: object) -> str | None:
    resource = evidence.get("resource") if isinstance(evidence, dict) else None
    version = evidence.get("version") if isinstance(evidence, dict) else None
    if not isinstance(resource, str) or not isinstance(version, str):
        return "bad evidence (needs string `resource` and `version`)"
    try:
        return check_evidence(root, resource, version)
    except (ValueError, OSError) as exc:
        return f"bad evidence ({exc})"


def claim_findings(root: Path, page: str, claim: dict[str, object]) -> list[str]:
    evidence = claim.get("evidence")
    statement = str(claim.get("statement", ""))[:STATEMENT_PREVIEW_CHARS]
    findings = []
    for item in evidence if isinstance(evidence, list) else []:
        problem = evidence_problem(root, item)
        if problem:
            cited = item.get("resource") if isinstance(item, dict) else item
            findings.append(f"{page} [{claim.get('id')}] {problem}: {cited}\n    claim: {statement}")
    return findings


def check_page(root: Path, wiki: Path, page: Path) -> Findings:
    rel = page.relative_to(wiki).as_posix()
    sidecar = wiki / CLAIMS_DIR / Path(rel).with_suffix(".json")
    if not sidecar.is_file():
        return [], [f"{rel}: no claims sidecar (ungrounded page)"], 0
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{rel}: unreadable claims sidecar ({exc})"], [], 0
    if not isinstance(data, dict) or data.get("schemaVersion") != CLAIMS_SCHEMA_VERSION:
        return [], [f"{rel}: claims sidecar is not schema v{CLAIMS_SCHEMA_VERSION}; skipped"], 0
    warnings = [] if "verification" in data else [f"{rel}: claims never verified by OpenWiki"]
    raw = data.get("claims")
    claims = [c for c in raw if isinstance(c, dict)] if isinstance(raw, list) else []
    stale = [finding for claim in claims for finding in claim_findings(root, rel, claim)]
    return stale, warnings, len(claims)


def scalar(raw: str) -> str:
    """One YAML scalar: unquote a quoted value, else drop a trailing `# comment`."""
    raw = raw.strip()
    if raw[:1] in ("'", '"'):
        end = raw.find(raw[0], 1)
        return raw[1:end] if end > 0 else raw[1:]
    return raw.split(" #", 1)[0].strip()


def front_matter(text: str) -> dict[str, str]:
    """Top-level front-matter keys (no YAML dependency); a nested block value maps to ""."""
    match = FRONT_MATTER.match(text)
    if not match:
        return {}
    pairs = (FRONT_MATTER_KEY.match(line) for line in match.group(1).splitlines())
    return {p.group(1): scalar(p.group(2) or "") for p in pairs if p}


def concept_pages(wiki: Path) -> list[Path]:
    """Wiki pages that carry facts: not index/log/instructions, not claims sidecars."""
    return [
        page
        for page in sorted(wiki.rglob("*.md"))
        if CLAIMS_DIR not in page.relative_to(wiki).parts and page.name.lower() not in RESERVED_PAGES
    ]


def okf_warnings(wiki: Path, pages: list[Path]) -> list[str]:
    """OKF v0.2: the root index declares the version; every concept page has a `type`."""
    index = wiki / "index.md"
    text = index.read_text(encoding="utf-8") if index.is_file() else ""
    version = front_matter(text).get("okf_version")
    warnings = [] if version == OKF_VERSION else [f"index.md: okf_version is {version!r}"]
    warnings += [
        f"{page.relative_to(wiki).as_posix()}: no OKF `type` in front matter"
        for page in pages
        if not front_matter(page.read_text(encoding="utf-8", errors="replace")).get("type")
    ]
    return warnings


def check_wiki(root: Path, wiki: Path) -> Findings:
    pages = concept_pages(wiki)
    stale: list[str] = []
    warnings = okf_warnings(wiki, pages)
    total = 0
    for page in pages:
        page_stale, page_warnings, count = check_page(root, wiki, page)
        stale += page_stale
        warnings += page_warnings
        total += count
    return stale, warnings, total


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail when OpenWiki claims no longer match code.")
    parser.add_argument("--wiki", type=Path, default=Path("openwiki"))
    wiki = parser.parse_args().wiki
    if not wiki.is_dir():
        print(f"verify_wiki: no {wiki.as_posix()}/ directory; nothing to check.")
        return 0
    stale, warnings, total = check_wiki(Path.cwd(), wiki)
    for warning in warnings:
        print(f"WARN  {warning}")
    for finding in stale:
        print(f"STALE {finding}")
    print(f"verify_wiki: {total} claims, {len(stale)} stale, {len(warnings)} warnings")
    if stale:
        print("Docs drifted from code: run `openwiki --update` (or fix the code), then commit.")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
