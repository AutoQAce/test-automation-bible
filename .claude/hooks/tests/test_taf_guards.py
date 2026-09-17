"""Test-automation guards: secrets in test assets, flaky masking, sleeps, weakened oracles."""

from pathlib import Path

import pytest
from lib import quality_guard, test_guard
from lib.secrets_guard import find_secrets

pytestmark = pytest.mark.unit


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "tests" / "web").mkdir(parents=True)
    return tmp_path


def edit(path: Path, old: str, new: str) -> dict[str, str]:
    return {"file_path": str(path), "old_string": old, "new_string": new}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('BASE_URL = "https://qa_user:' + 'S3cr3tPass@qa.example.com"', ["credentials in URL"]),
        ('headers = {"Authorization": "Basic ' + 'cWFfdXNlcjpTM2NyM3Q="}', ["Basic auth header"]),
        ("<wsse:Password>" + "S3cr3tPass</wsse:Password>", ["XML password element"]),
        ("<wsse:Password>${SOAP_PASSWORD}</wsse:Password>", []),
        ("<Password>{{ password }}</Password>", []),
        ('DSN = "Server=db;User Id=qa;Password=' + 'S3cr3tPass;"', ["connection string password"]),
        ('"https://api.example.com/v1/orders"', []),
        ('{"Authorization": "Bearer ' + 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2ln"}', ["Bearer token"]),
        ('headers = {"Authorization": f"Bearer {token}"}', []),
        ('"Authorization": "Bearer ${ORDERS_TOKEN}"', []),
        ("Authorization: Bearer <token>", []),
    ],
)
def test_test_automation_secret_patterns(text: str, expected: list[str]) -> None:
    assert find_secrets(text) == expected


@pytest.mark.parametrize(
    "marker",
    [
        "@pytest.mark.flaky(reruns=3)",
        "@pytest.mark.order(2)",
        "@pytest.mark.dependency(depends=['test_a'])",
    ],
)
def test_flaky_masking_and_ordering_markers_are_blocked(repo: Path, marker: str) -> None:
    path = repo / "tests" / "test_a.py"
    new = marker + chr(10) + "def test_b(): ..."
    assert quality_guard.check("Edit", edit(path, "x = 1", new), path, repo).block


def write_test(repo: Path, body: str) -> Path:
    path = repo / "tests" / "web" / "test_login.py"
    path.write_text(body, encoding="utf-8")
    return path


def lines(*parts: str) -> str:
    return chr(10).join(parts) + chr(10)


def test_hard_sleep_in_test_code_is_blocked(repo: Path) -> None:
    path = write_test(repo, lines("def test_login(page):", "    page.login()", "    assert page.ok()"))
    change = edit(path, "    page.login()", lines("    page.login()", "    time.sleep(3)"))
    assert test_guard.check("Edit", change, path, repo).block


def test_sleep_outside_test_code_is_not_this_guards_business(repo: Path) -> None:
    path = repo / "src" / "taf" / "wait.py"
    assert not test_guard.check("Edit", edit(path, "pass", "time.sleep(interval)"), path, repo).block


def test_removing_assertions_is_blocked_unless_justified(repo: Path) -> None:
    body = lines(
        "def test_total(cart):",
        "    assert cart.total() == 42",
        "    expect(cart.badge).to_have_text('2')",
    )
    path = write_test(repo, body)
    weakened = edit(path, body, lines("def test_total(cart):", "    assert cart.total()"))
    justified = edit(
        path,
        lines("    expect(cart.badge).to_have_text('2')"),
        lines("    # sdlc: justified badge removed in REQ-481"),
    )
    assert test_guard.check("Edit", weakened, path, repo).block
    assert not test_guard.check("Edit", justified, path, repo).block


def test_changing_an_expected_value_is_blocked(repo: Path) -> None:
    path = write_test(repo, lines("def test_total(cart):", "    assert cart.total() == 42"))
    change = edit(path, "    assert cart.total() == 42", "    assert cart.total() == 41")
    decision = test_guard.check("Edit", change, path, repo)
    assert decision.block
    assert "`assert cart.total() == 42`" in decision.message


def test_loosening_an_assertion_is_blocked(repo: Path) -> None:
    path = write_test(repo, lines("def test_total(cart):", "    assert cart.total() == 42"))
    change = edit(path, "    assert cart.total() == 42", "    assert cart.total() > 0")
    assert test_guard.check("Edit", change, path, repo).block


def test_reformatting_an_assertion_is_allowed(repo: Path) -> None:
    path = write_test(repo, lines("def test_total(cart):", "    assert cart.total()==42"))
    change = edit(path, "    assert cart.total()==42", "    assert cart.total() == 42")
    assert not test_guard.check("Edit", change, path, repo).block


def test_proof_of_failure_round_trip_is_allowed_with_marker(repo: Path) -> None:
    original = '    assert order.status == "PENDING"'
    temporary = '    assert order.status == "CONFIRMED"  # sdlc: justified proof of failure, revert'
    path = write_test(repo, lines("def test_status(order):", original))
    assert not test_guard.check("Edit", edit(path, original, temporary), path, repo).block
    assert not test_guard.check("Edit", edit(path, temporary, original), path, repo).block


def test_adding_assertions_is_fine(repo: Path) -> None:
    path = write_test(repo, lines("def test_a(x):", "    assert x"))
    change = edit(path, "    assert x", lines("    assert x", "    assert x.valid()"))
    assert not test_guard.check("Edit", change, path, repo).block
