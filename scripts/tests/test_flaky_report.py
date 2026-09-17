import pytest
from flaky_report import find_flaky, outcomes

pytestmark = pytest.mark.unit


def junit(*cases: str) -> str:
    return f"<testsuites><testsuite>{''.join(cases)}</testsuite></testsuites>"


PASS = '<testcase classname="t.web" name="test_login"/>'
FAIL = '<testcase classname="t.web" name="test_login"><failure message="timeout"/></testcase>'
STABLE = '<testcase classname="t.api" name="test_orders"/>'
SKIPPED = '<testcase classname="t.api" name="test_skip"><skipped/></testcase>'


def test_outcomes_parse_pass_fail_and_ignore_skips() -> None:
    assert outcomes(junit(FAIL, STABLE, SKIPPED)) == {
        "t.web::test_login": False,
        "t.api::test_orders": True,
    }


def test_mixed_results_across_runs_are_flaky() -> None:
    runs = [outcomes(junit(PASS, STABLE)), outcomes(junit(FAIL, STABLE)), outcomes(junit(PASS, STABLE))]

    flaky = find_flaky(runs)

    assert [f.test_id for f in flaky] == ["t.web::test_login"]
    assert (flaky[0].passed, flaky[0].failed, flaky[0].flake_rate) == (2, 1, 0.333)


def test_consistently_failing_test_is_not_flaky() -> None:
    assert find_flaky([outcomes(junit(FAIL)), outcomes(junit(FAIL))]) == []


def test_xml_entity_attacks_are_rejected() -> None:
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><testsuites>&a;</testsuites>'
    with pytest.raises(Exception, match=r"(?i)entit"):
        outcomes(bomb)
