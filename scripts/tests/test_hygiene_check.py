import datetime as dt

import pytest
from hygiene_check import check_source

pytestmark = pytest.mark.unit
TODAY = dt.date(2026, 9, 18)


def rules(source: str) -> list[str]:
    return [f.rule for f in check_source("tests/test_x.py", source, TODAY)]


def test_clean_test_has_no_findings() -> None:
    source = (
        "import pytest\n"
        "pytestmark = [pytest.mark.web, pytest.mark.smoke]\n"
        "def test_login(login_page):\n"
        "    login_page.sign_in('ana')\n"
        "    assert login_page.greeting() == 'Hi Ana'\n"
    )
    assert rules(source) == []


@pytest.mark.parametrize(
    ("body", "rule"),
    [
        ("    time.sleep(2)\n    assert x\n", "H001"),
        ("    page.click('//button[@id=\"go\"]')\n    assert x\n", "H002"),
        ("    page.click('#submit .btn')\n    assert x\n", "H002"),
        ("    client.get('https://qa.example.com/api')\n    assert x\n", "H007"),
        ("    page.open()\n", "H006"),
    ],
)
def test_body_rules(body: str, rule: str) -> None:
    source = f"import pytest, time\n@pytest.mark.web\ndef test_it(page, client):\n{body}"
    assert rule in rules(source)


def test_oracle_via_expect_or_raises_counts() -> None:
    source = (
        "import pytest\n@pytest.mark.api\ndef test_a(r):\n    expect(r).to_have_status(200)\n"
        "@pytest.mark.api\ndef test_b(c):\n    with pytest.raises(ValueError):\n        c.call()\n"
    )
    assert "H006" not in rules(source)


@pytest.mark.parametrize(
    ("decorator", "rule"),
    [
        ("@pytest.mark.skip", "H003"),
        ("@pytest.mark.xfail()", "H003"),
        ("@pytest.mark.order(1)", "H005"),
        ("@pytest.mark.quarantine(reason='BUG-1')", "H008"),
        ("@pytest.mark.quarantine(reason='BUG-1', until='2026-01-01')", "H008"),
        ("@pytest.mark.quarantine(reason='BUG-1', until='soon')", "H008"),
    ],
)
def test_marker_rules(decorator: str, rule: str) -> None:
    source = f"import pytest\n@pytest.mark.web\n{decorator}\ndef test_it():\n    assert True\n"
    assert rule in rules(source)


def test_valid_quarantine_and_class_markers_pass() -> None:
    source = (
        "import pytest\n@pytest.mark.desktop\n@pytest.mark.regression\nclass TestInvoices:\n"
        "    @pytest.mark.quarantine(reason='BUG-7 focus race', until='2026-10-30')\n"
        "    def test_print(self, app):\n        assert app.printed()\n"
    )
    assert rules(source) == []


def test_missing_platform_marker() -> None:
    assert "H004" in rules("def test_it():\n    assert 1\n")


@pytest.mark.parametrize(
    ("markers", "has_h004"),
    [
        ("pytest.mark.api", True),  # platform without level: CI never selects it
        ("pytest.mark.smoke", True),  # level without platform
        ("pytest.mark.api, pytest.mark.smoke", False),
        ("pytest.mark.web, pytest.mark.regression", False),
        ("pytest.mark.unit", False),  # framework self-tests need no platform or smoke/regression
        ("pytest.mark.contract", False),
    ],
)
def test_platform_and_level_markers(markers: str, has_h004: bool) -> None:
    source = f"import pytest\npytestmark = [{markers}]\ndef test_it():\n    assert 1\n"
    assert ("H004" in rules(source)) is has_h004


def test_justified_line_is_accepted() -> None:
    source = (
        "import pytest, time\n@pytest.mark.desktop\n@pytest.mark.smoke\ndef test_it(app):\n"
        "    time.sleep(1)  # sdlc: justified vendor dialog has no observable ready state (BUG-9)\n"
        "    assert app.ready()\n"
    )
    assert rules(source) == []
