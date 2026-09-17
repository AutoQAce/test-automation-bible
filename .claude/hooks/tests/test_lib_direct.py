"""Direct tests of the hook library (subprocess tests prove wiring; these prove each branch)."""

import io
import json
import subprocess
import urllib.error
from pathlib import Path
from typing import Any

import pytest
from lib import common, deps_guard, secrets_guard

pytestmark = pytest.mark.unit
FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"


def test_read_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_name": "Edit"})))
    assert common.read_payload() == {"tool_name": "Edit"}
    monkeypatch.setattr("sys.stdin", io.StringIO("   "))
    assert common.read_payload() == {}


def test_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    root = common.project_root({"cwd": str(tmp_path)})
    assert root == tmp_path.resolve()
    assert common.state_dir(root, "traces").is_dir()
    assert common.target_path({}, root) is None
    assert common.target_path({"file_path": "tests/a.py"}, root) == root / "tests/a.py"
    assert common.relative(root / "tests" / "a.py", root) == "tests/a.py"
    assert common.relative(Path("/elsewhere/x.py"), root).endswith("x.py")
    assert common.read_existing(root / "missing.py") == ""


def test_before_after_and_apply_edit(tmp_path: Path) -> None:
    path = tmp_path / "f.py"
    path.write_text("a = 1\nb = 1\n", encoding="utf-8")
    multi = {"edits": [{"old_string": "1", "new_string": "2", "replace_all": True}]}
    assert common.before_after("Write", {"content": "x"}, path) == ("a = 1\nb = 1\n", "x")
    assert common.before_after("Edit", {"old_string": "a", "new_string": "c"}, path) == ("a", "c")
    assert common.before_after("MultiEdit", multi, path) == ("1", "2")
    assert common.before_after("Read", {}, path) == ("", "")
    assert common.apply_edit("MultiEdit", multi, "a = 1\nb = 1\n") == "a = 2\nb = 2\n"
    assert common.apply_edit("Edit", {"old_string": "1", "new_string": "3"}, "1 1") == "3 1"
    assert common.apply_edit("Write", {"content": "z"}, "old") == "z"


@pytest.mark.parametrize(
    ("tool", "tool_input", "blocked"),
    [
        ("Write", {"content": FAKE_AWS}, True),
        ("Edit", {"new_string": FAKE_AWS}, True),
        ("MultiEdit", {"edits": [{"new_string": FAKE_AWS}]}, True),
        ("Bash", {"command": f"echo {FAKE_AWS}"}, True),
        ("Bash", {"command": "uv run pytest"}, False),
        ("Read", {"file_path": "x"}, False),
    ],
)
def test_secrets_check_per_tool(tmp_path: Path, tool: str, tool_input: dict[str, Any], blocked: bool) -> None:
    assert secrets_guard.check(tool, tool_input, tmp_path).block is blocked


def git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    return tmp_path


def test_staged_and_diff_scans(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    (repo / "ok.txt").write_text("fine\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    (repo / "leak.txt").write_text(f"key={FAKE_AWS}\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)

    assert secrets_guard.scan_staged(repo) == ["AWS access key"]
    assert FAKE_AWS in secrets_guard.pending_commit_text(repo)
    assert secrets_guard.scan_diff(repo, "no-such-branch") is None


def test_git_missing_is_tolerated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(*_: object, **__: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", missing)
    assert secrets_guard.git(tmp_path, "status") is None


class FakeResponse(io.StringIO):
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None


def test_pypi_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    releases = {"releases": {"1.0": [{"upload_time_iso_8601": "2020-01-02T00:00:00Z"}], "0.1": []}}
    monkeypatch.setattr("urllib.request.urlopen", lambda *_a, **_k: FakeResponse(json.dumps(releases)))
    assert deps_guard.pypi_first_upload("requests") == "2020-01-02T00:00:00Z"

    def not_found(*_a: object, **_k: object) -> None:
        raise urllib.error.HTTPError("u", 404, "nf", None, None)  # type: ignore[arg-type]

    monkeypatch.setattr("urllib.request.urlopen", not_found)
    assert deps_guard.pypi_first_upload("nope") is None


def test_deps_check_respects_allow_list_and_ignores_other_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SDLC_ALLOW_PACKAGES", "brand-new-internal")
    assert not deps_guard.check("Bash", {"command": "uv add brand-new-internal"}, lookup=lambda _: None).block
    assert not deps_guard.check("Write", {"content": "uv add x"}, lookup=lambda _: None).block
    assert deps_guard.problem_with("x", lambda _: "", 30) is None
