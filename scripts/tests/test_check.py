"""Gate selection in check.py: which gates run in full, fast, and red-phase mode."""

import check
import pytest

pytestmark = pytest.mark.unit


def names(fast: bool, red_phase: bool) -> list[str]:
    return [name for name, _ in check.select_gates(fast=fast, red_phase=red_phase)]


def test_full_runs_coverage_and_scans() -> None:
    selected = names(fast=False, red_phase=False)
    assert "framework self-tests + coverage" in selected
    assert "vulnerable dependencies" in selected


def test_fast_runs_self_tests_without_scans() -> None:
    selected = names(fast=True, red_phase=False)
    assert "framework self-tests" in selected
    assert "vulnerable dependencies" not in selected


def test_red_phase_is_fast_without_self_tests() -> None:
    selected = names(fast=False, red_phase=True)
    assert selected == [n for n in names(fast=True, red_phase=False) if n != "framework self-tests"]
    assert "architecture rules (layers.toml)" in selected
    assert "test hygiene" in selected
