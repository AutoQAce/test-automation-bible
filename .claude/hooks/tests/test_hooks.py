"""Harness hooks, tested the way Claude Code runs them: JSON payload on stdin, exit code out."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from lib import deps_guard, quality_guard
from lib.secrets_guard import find_secrets

HOOKS = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.unit

FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"


def run_hook(
    script: str, payload: dict[str, object], root: Path, **env: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps({"cwd": str(root), "session_id": "s1", **payload}),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(root), "SDLC_TEST_CMD": "off", **env},
        check=False,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = []\n\n[tool.coverage.report]\nfail_under = 80\n',
        encoding="utf-8",
    )
    return tmp_path


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (f"key = '{FAKE_AWS}'", ["AWS access key"]),
        ('DB_PASSWORD = "' + 'k3yk3yk3yk3y"', ["hard-coded credential"]),
        ('"auth_token": "' + 'zzzzzzzzzzzz"', ["hard-coded credential"]),
        ('api_key = "' + 'your-api-key-here"', []),  # placeholder
        ('password = "' + 'changeme"', []),  # placeholder
        ('password = os.environ["DB_PASSWORD"]', []),
        ('token = "' + 'zzzzzzzzzzzz"  # sdlc:allow-secret', []),
    ],
)
def test_find_secrets(text: str, expected: list[str]) -> None:
    assert find_secrets(text) == expected


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("git commit --no-verify -m wip", True),
        ("git commit -n -m wip", True),
        ("git -c core.hooksPath=/dev/null commit -m x", True),
        ("SKIP=ruff git commit -m x", True),
        ("git push --force origin main", True),
        ("git push --force-with-lease origin feat/x", False),
        ("git reset --hard HEAD~1", True),
        ("rm -rf tests/unit", True),
        ("git rm tests/test_api.py", True),
        ("git commit -m 'feat: add refund tool'", False),
        ("uv run pytest -q", False),
    ],
)
def test_bypass_guard(repo: Path, command: str, blocked: bool) -> None:
    result = run_hook("pre_tool.py", {"tool_name": "Bash", "tool_input": {"command": command}}, repo)
    assert (result.returncode == 2) is blocked, result.stderr


def test_secret_in_write_is_blocked(repo: Path) -> None:
    payload = {"tool_name": "Write", "tool_input": {"file_path": "docs/x.md", "content": FAKE_AWS}}
    result = run_hook("pre_tool.py", payload, repo, SDLC_FACT_FORCE="0")
    assert result.returncode == 2
    assert "AWS access key" in result.stderr


def test_secret_in_untracked_file_blocks_commit(repo: Path) -> None:
    (repo / "leak.py").write_text('SECRET_TOKEN = "' + 'zzzzzzzzzzzz"\n', encoding="utf-8")
    payload = {"tool_name": "Bash", "tool_input": {"command": "git add . && git commit -m x"}}
    assert run_hook("pre_tool.py", payload, repo).returncode == 2


def test_protected_config_file_cannot_be_modified(repo: Path) -> None:
    (repo / "ruff.toml").write_text("line-length = 100\n", encoding="utf-8")
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "ruff.toml", "content": "line-length = 200\n"},
    }
    assert run_hook("pre_tool.py", payload, repo).returncode == 2


def test_pyproject_quality_section_change_is_blocked_but_dependency_change_is_not(
    repo: Path,
) -> None:
    lower_bar = {
        "file_path": "pyproject.toml",
        "old_string": "fail_under = 80",
        "new_string": "fail_under = 50",
    }
    add_dep = {
        "file_path": "pyproject.toml",
        "old_string": "dependencies = []",
        "new_string": 'dependencies = ["httpx"]',
    }
    path = repo / "pyproject.toml"
    assert quality_guard.check("Edit", lower_bar, path, repo).block
    assert not quality_guard.check("Edit", add_dep, path, repo).block


@pytest.mark.parametrize(
    ("new_string", "blocked"),
    [
        ("x = f()  # type: ignore", True),
        ("import os  # noqa: F401", True),
        ("@pytest.mark.skip\ndef test_a(): ...", True),
        ("x = f()  # type: ignore[attr-defined]  sdlc: justified stub lacks attr", False),
        ("x = f()", False),
    ],
)
def test_suppression_markers_need_justification(repo: Path, new_string: str, blocked: bool) -> None:
    edit = {"file_path": "tests/test_a.py", "old_string": "x = 1", "new_string": new_string}
    assert quality_guard.check("Edit", edit, repo / "tests" / "test_a.py", repo).block is blocked


def test_deps_guard_parses_install_commands() -> None:
    command = "uv add 'httpx[http2]>=0.27' --group dev pytest-cov && pip install -r reqs.txt -e . requestz"
    assert deps_guard.package_names(command) == ["httpx", "pytest-cov", "requestz"]


@pytest.mark.parametrize(
    ("first_upload", "blocked"),
    [(None, True), ("2026-09-10T00:00:00Z", True), ("2019-01-01T00:00:00Z", False)],
)
def test_deps_guard_blocks_missing_and_brand_new_packages(first_upload: str | None, blocked: bool) -> None:
    decision = deps_guard.check("Bash", {"command": "uv add some-package"}, lookup=lambda _: first_upload)
    assert decision.block is blocked


def test_deps_guard_fails_closed_when_offline() -> None:
    def offline(_: str) -> str | None:
        raise OSError("network down")

    assert deps_guard.check("Bash", {"command": "pip install requests"}, lookup=offline).block


def test_fact_force_denies_first_edit_per_file_only(repo: Path) -> None:
    (repo / "src" / "core.py").write_text("x = 1\n", encoding="utf-8")
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "src/core.py", "old_string": "x = 1", "new_string": "x = 2"},
    }

    first = run_hook("pre_tool.py", payload, repo)
    second = run_hook("pre_tool.py", payload, repo)

    assert first.returncode == 2
    assert "imports src/core.py" in first.stderr
    assert second.returncode == 0


def test_post_tool_writes_redacted_trace(repo: Path) -> None:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": f"echo {FAKE_AWS}"},
        "tool_response": {"ok": True},
    }
    assert run_hook("post_tool.py", payload, repo).returncode == 0
    trace = (repo / ".sdlc" / "traces" / "s1.jsonl").read_text(encoding="utf-8")
    assert FAKE_AWS not in trace
    assert "[REDACTED]" in trace


def test_stop_hook_loops_on_failure_then_hands_over(repo: Path) -> None:
    (repo / "changed.txt").write_text("dirty", encoding="utf-8")
    env = {
        "SDLC_TEST_CMD": f'"{sys.executable}" -c "raise SystemExit(1)"',
        "SDLC_MAX_FIX_ATTEMPTS": "1",
    }

    first = run_hook("stop.py", {}, repo, **env)
    second = run_hook("stop.py", {}, repo, **env)

    assert first.returncode == 2
    assert second.returncode == 0
    assert "Human needed" in second.stdout


FAIL_CMD = f'"{sys.executable}" -c "raise SystemExit(1)"'
PASS_CMD = f'"{sys.executable}" -c "raise SystemExit(0)"'


def add_file(repo: Path, rel: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x = 1\n", encoding="utf-8")


def test_stop_hook_allows_red_phase_when_only_tests_changed(repo: Path) -> None:
    add_file(repo, "tests/unit/test_orders.py")
    result = run_hook("stop.py", {}, repo, SDLC_TEST_CMD=FAIL_CMD, SDLC_RED_PHASE_CMD=PASS_CMD)
    assert result.returncode == 0
    assert "Red phase" in result.stdout


@pytest.mark.parametrize(
    ("files", "red_phase_cmd"),
    [
        (["tests/unit/test_orders.py", "src/taf/orders.py"], PASS_CMD),  # implementation changed too
        (["tests/unit/test_orders.py"], FAIL_CMD),  # another fast gate fails
        (["tests/unit/test_orders.py"], "off"),
        (["notes.md"], PASS_CMD),  # no test changed: not a red phase
    ],
)
def test_stop_hook_blocks_when_not_a_clean_red_phase(
    repo: Path, files: list[str], red_phase_cmd: str
) -> None:
    for rel in files:
        add_file(repo, rel)
    result = run_hook("stop.py", {}, repo, SDLC_TEST_CMD=FAIL_CMD, SDLC_RED_PHASE_CMD=red_phase_cmd)
    assert result.returncode == 2


def test_hidden_unicode_scan_finds_zero_width_chars(repo: Path) -> None:
    (repo / "AGENTS.md").write_text("safe" + chr(0x200B) + "rule\n", encoding="utf-8")
    subprocess.run(["git", "add", "AGENTS.md"], cwd=repo, check=True)
    result = subprocess.run(
        [sys.executable, str(HOOKS / "scan.py"), "hidden-unicode"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "AGENTS.md:1: U+200B" in result.stderr
