"""verify_wiki.py: OpenWiki claims must match the code they cite; the wiki should be OKF v0.2."""

import base64
import json
from pathlib import Path

import pytest
import verify_wiki as vw

pytestmark = pytest.mark.unit

SOURCE = "a\nb\nc\nd\n"
INDEX = '---\nokf_version: "0.2"\n---\n\n# Index\n'
PAGE = '---\ntype: "Architecture"\ntitle: "App"\n---\n# App\n'


def range_version(content: str, lines: int) -> str:
    meta = base64.urlsafe_b64encode(json.dumps({"selectedLineCount": lines}).encode()).decode()
    return f"{vw.RANGE_PREFIX}{vw.sha(content)}:{meta.rstrip('=')}"


def claim(claim_id: str, resource: str, version: str) -> dict[str, object]:
    return {
        "id": claim_id,
        "statement": claim_id,
        "evidence": [{"resource": resource, "version": version}],
    }


def write_wiki(root: Path, claims: list[dict[str, object]], **sidecar: object) -> Path:
    wiki = root / "openwiki"
    (wiki / ".claims").mkdir(parents=True)
    (wiki / "index.md").write_text(INDEX, encoding="utf-8")
    (wiki / "app.md").write_text(PAGE, encoding="utf-8")
    body = {"schemaVersion": 1, "verification": {"by": "openwiki"}, "claims": claims, **sidecar}
    (wiki / ".claims" / "app.json").write_text(json.dumps(body), encoding="utf-8")
    return wiki


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text(SOURCE, encoding="utf-8", newline="")
    write_wiki(
        tmp_path,
        [
            claim("c1", "repo://app.py#L2-L3", range_version("b\nc\n", 2)),
            claim("c2", "repo://app.py", vw.FILE_PREFIX + vw.sha(SOURCE)),
        ],
    )
    return tmp_path


def stale(root: Path) -> list[str]:
    return vw.check_wiki(root, root / "openwiki")[0]


def test_unchanged_code_keeps_every_claim_fresh(repo: Path) -> None:
    assert vw.check_wiki(repo, repo / "openwiki") == ([], [], 2)


def test_moved_but_unchanged_lines_stay_fresh(repo: Path) -> None:
    (repo / "app.py").write_text("z\n" + SOURCE, encoding="utf-8", newline="")
    findings = stale(repo)
    assert len(findings) == 1
    assert "[c2] cited file changed" in findings[0]


def test_edited_cited_lines_are_stale(repo: Path) -> None:
    (repo / "app.py").write_text("a\nB\nc\nd\n", encoding="utf-8", newline="")
    assert any("[c1] cited lines changed" in f for f in stale(repo))


def test_deleted_file_is_stale(repo: Path) -> None:
    (repo / "app.py").unlink()
    assert all("cited file no longer exists" in f for f in stale(repo))


def test_crlf_checkout_counts_as_changed(repo: Path) -> None:
    (repo / "app.py").write_text(SOURCE.replace("\n", "\r\n"), encoding="utf-8", newline="")
    assert len(stale(repo)) == 2


@pytest.mark.parametrize(
    ("evidence", "problem"),
    [
        ({"resource": "repo://../outside.py", "version": "x"}, "escapes the repository"),
        ({"resource": "https://example.com", "version": "x"}, "unsupported evidence resource"),
        ({"resource": "repo://app.py#L9-L2x", "version": "x"}, "bad line range"),
        ({"resource": "repo://app.py"}, "needs string `resource` and `version`"),
        ({"resource": "repo://app.py#L1", "version": "repo-lines-v1:sha256:abc:!!"}, "cited lines"),
    ],
)
def test_bad_or_escaping_evidence_is_stale(repo: Path, evidence: object, problem: str) -> None:
    (repo / "openwiki" / ".claims" / "app.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "verification": {},
                "claims": [{"id": "x", "evidence": [evidence]}],
            }
        ),
        encoding="utf-8",
    )
    assert problem in stale(repo)[0]


def test_sidecar_problems(tmp_path: Path) -> None:
    wiki = write_wiki(tmp_path, [], schemaVersion=2)
    assert vw.check_wiki(tmp_path, wiki) == (
        [],
        ["app.md: claims sidecar is not schema v1; skipped"],
        0,
    )
    (wiki / ".claims" / "app.json").write_text("{not json", encoding="utf-8")
    assert "unreadable claims sidecar" in vw.check_wiki(tmp_path, wiki)[0][0]
    (wiki / ".claims" / "app.json").write_text(json.dumps({"schemaVersion": 1}), encoding="utf-8")
    assert vw.check_wiki(tmp_path, wiki)[1] == ["app.md: claims never verified by OpenWiki"]


def test_okf_and_grounding_warnings(repo: Path) -> None:
    wiki = repo / "openwiki"
    (wiki / "index.md").write_text("---\nokf_version: 0.1\n---\n", encoding="utf-8")
    (wiki / "orphan.md").write_text("# no front matter\n", encoding="utf-8")
    warnings = vw.check_wiki(repo, wiki)[1]
    assert "index.md: okf_version is '0.1'" in warnings
    assert "orphan.md: no OKF `type` in front matter" in warnings
    assert "orphan.md: no claims sidecar (ungrounded page)" in warnings


def test_front_matter_reads_top_level_scalars() -> None:
    text = '---\r\ntype: "ADR"\r\nstatus: draft   # note\r\nurl: "a # b"\r\nverified:\r\n  - by: x\r\n---\r\n'
    assert vw.front_matter(text) == {
        "type": "ADR",
        "status": "draft",
        "url": "a # b",
        "verified": "",
    }
    assert vw.front_matter("# no front matter\n---\n") == {}


def test_main_exit_codes(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["verify_wiki.py"])
    monkeypatch.chdir(repo)
    assert vw.main() == 0
    (repo / "app.py").write_text("changed\n", encoding="utf-8")
    assert vw.main() == 1
    monkeypatch.chdir(repo / "openwiki")
    assert vw.main() == 0  # no openwiki/ below this directory: nothing to check
