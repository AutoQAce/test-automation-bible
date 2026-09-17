from pathlib import Path

import pytest
from architecture_check import check_repository, load_rules, violations_in

pytestmark = pytest.mark.unit

RULES = load_rules(
    """
[layers.tests]
paths = ["tests/"]
may_import = ["pages", "services", "data"]

[layers.pages]
paths = ["src/taf/pages/"]
may_import = ["core"]

[layers.web_driver]
paths = ["src/taf/drivers/web/"]
may_import = ["core"]

[layers.core]
paths = ["src/taf/core/"]

[library_owners]
playwright = ["web_driver"]
selenium = ["web_driver"]
"""
)


def test_allowed_imports_pass() -> None:
    source = "from taf.pages.login import LoginPage\nfrom taf.data.users import new_user\n"
    assert violations_in("tests/web/test_login.py", source, RULES) == []


def test_test_importing_driver_layer_is_a_violation() -> None:
    found = violations_in("tests/test_x.py", "from taf.drivers.web.session import Browser\n", RULES)
    assert found == [
        "tests/test_x.py:1: layer 'tests' may not import layer 'web_driver' (taf.drivers.web.session)"
    ]


@pytest.mark.parametrize("path", ["tests/test_x.py", "src/taf/pages/login.py"])
def test_engine_library_only_in_its_driver_layer(path: str) -> None:
    found = violations_in(path, "from playwright.sync_api import Page\n", RULES)
    assert found
    assert "owned by ['web_driver']" in found[0]


def test_driver_layer_may_use_its_engine() -> None:
    assert violations_in("src/taf/drivers/web/session.py", "import selenium.webdriver\n", RULES) == []


def test_unmapped_files_are_ignored() -> None:
    assert violations_in("tools/helper.py", "import playwright\n", RULES) == []


def test_repository_scan(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("import selenium\n", encoding="utf-8")
    assert len(check_repository(tmp_path, RULES)) == 1
