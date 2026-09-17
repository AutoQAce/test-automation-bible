"""Detect flaky tests by comparing JUnit XML results of repeated runs of the same commit.

A test that both passed and failed across runs is flaky. Quarantined tests are excluded from
gating runs (`-m "not quarantine"`), so any flaky test reported here is unmanaged and fails the gate.

    python scripts/flaky_report.py run1.xml run2.xml [--out .sdlc/flaky.json] [--fail-on-flaky]
"""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from defusedxml import ElementTree

FAILED_TAGS = frozenset({"failure", "error"})
MIN_RUNS = 2


@dataclass(frozen=True, slots=True)
class FlakyTest:
    test_id: str
    runs: int
    passed: int
    failed: int

    @property
    def flake_rate(self) -> float:
        return round(min(self.passed, self.failed) / self.runs, 3)


def outcomes(junit_xml: str) -> dict[str, bool]:
    """test id -> passed? Skipped tests are ignored."""
    results: dict[str, bool] = {}
    for case in ElementTree.fromstring(junit_xml).iter("testcase"):
        tags = {child.tag for child in case}
        if "skipped" in tags:
            continue
        test_id = f"{case.get('classname', '')}::{case.get('name', '')}"
        results[test_id] = not tags & FAILED_TAGS
    return results


def find_flaky(runs: list[dict[str, bool]]) -> list[FlakyTest]:
    history: dict[str, list[bool]] = defaultdict(list)
    for run in runs:
        for test_id, passed in run.items():
            history[test_id].append(passed)
    flaky = [
        FlakyTest(test_id, len(results), results.count(True), results.count(False))
        for test_id, results in history.items()
        if True in results and False in results
    ]
    return sorted(flaky, key=lambda f: (-f.flake_rate, f.test_id))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, default=Path(".sdlc/flaky.json"))
    parser.add_argument("--fail-on-flaky", action="store_true")
    args = parser.parse_args()
    if len(args.reports) < MIN_RUNS:
        print(f"Need at least {MIN_RUNS} JUnit reports of the same commit.")
        return 2
    flaky = find_flaky([outcomes(path.read_text(encoding="utf-8")) for path in args.reports])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = [{**asdict(f), "flake_rate": f.flake_rate} for f in flaky]
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for test in flaky:
        print(f"FLAKY {test.test_id}  passed {test.passed}/{test.runs}")
    print(f"{len(flaky)} flaky test(s) -> {args.out}")
    return 1 if flaky and args.fail_on_flaky else 0


if __name__ == "__main__":
    sys.exit(main())
