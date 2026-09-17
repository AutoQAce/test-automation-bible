"""Command-line entry points of the gate scripts: exit codes are the contract CI relies on."""

from pathlib import Path

import architecture_check
import flaky_report
import hygiene_check
import pytest

pytestmark = pytest.mark.unit


def junit(passed: bool) -> str:
    body = "" if passed else '<failure message="timeout"/>'
    case = f'<testcase classname="t" name="test_a">{body}</testcase>'
    return f"<testsuites><testsuite>{case}</testsuite></testsuites>"


def run_main(monkeypatch: pytest.MonkeyPatch, module: object, *args: str) -> int:
    monkeypatch.setattr("sys.argv", ["prog", *args])
    return int(module.main())  # type: ignore[attr-defined]


def test_flaky_report_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run1, run2 = tmp_path / "run1.xml", tmp_path / "run2.xml"
    run1.write_text(junit(passed=True), encoding="utf-8")
    run2.write_text(junit(passed=False), encoding="utf-8")
    out = tmp_path / "flaky.json"

    assert run_main(monkeypatch, flaky_report, str(run1)) == 2
    assert run_main(monkeypatch, flaky_report, str(run1), str(run2), "--out", str(out)) == 0
    assert (
        run_main(monkeypatch, flaky_report, str(run1), str(run2), "--out", str(out), "--fail-on-flaky") == 1
    )
    assert '"test_id": "t::test_a"' in out.read_text(encoding="utf-8")


def test_hygiene_main_skips_without_tests_and_fails_on_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert run_main(monkeypatch, hygiene_check) == 0

    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "helpers.py").write_text("import time\ntime.sleep(1)\n", encoding="utf-8")
    (tests / "test_bad.py").write_text("def test_it():\n    pass\n", encoding="utf-8")
    assert run_main(monkeypatch, hygiene_check) == 1
    assert run_main(monkeypatch, hygiene_check, "tests/helpers.py") == 0


def test_architecture_main_skips_without_config_and_enforces_with_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert run_main(monkeypatch, architecture_check) == 0

    config = tmp_path / "layers.toml"
    config.write_text(
        '[layers.tests]\npaths = ["tests/"]\n[library_owners]\nselenium = ["web_driver"]\n',
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("import selenium\n", encoding="utf-8")
    assert run_main(monkeypatch, architecture_check, "--config", str(config)) == 1
