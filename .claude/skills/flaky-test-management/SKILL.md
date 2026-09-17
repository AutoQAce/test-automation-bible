---
name: flaky-test-management
description: Detect, triage, quarantine, and fix flaky tests without masking them: repeated-run detection with scripts/flaky_report.py, root-cause taxonomy, quarantine marker with ticket and expiry, exit criteria, and prevention. Use when a test fails intermittently, when the nightly flaky report is red, or when someone proposes retries or reruns.
---

# Flaky test management

A flaky test is a bug: in the test, the framework, the environment, or the product. Retrying it to green hides the bug and trains everyone to ignore red.

## Detect
- Nightly: run the regression suite twice on the same commit, then `python scripts/flaky_report.py run1.xml run2.xml --fail-on-flaky`.
- On demand: run a suspect test N times, in parallel and in random order, locally or in CI.

## Triage (agent `flaky-test-investigator`)
| Root cause | Typical signal | Real fix |
|---|---|---|
| Synchronization | Fails fast on slow runs; passes on rerun | Wait on the right condition; centralize the wait |
| Data collision | Fails only in parallel | Unique data per worker; cleanup |
| Order dependence / leaked state | Fails only after certain tests | Isolate setup; narrow fixture scope |
| Environment / infrastructure | Clusters by runner, time, or service | Fix or stub the dependency; health checks before the suite |
| Locator fragility | Breaks on minor UI changes | Stable test attributes; interaction-object ownership |
| Product race condition | Real users could hit it | File a product bug with evidence; keep the test |

## Quarantine (the only accepted stopgap)
```python
@pytest.mark.quarantine(reason="QA-1234 intermittent timeout on invoice export", until="2026-10-15")
```
- Requires a ticket and an expiry (`hygiene_check.py` H008 fails expired quarantines).
- Excluded from gating runs (`-m "not quarantine"`), still run nightly in a non-gating job so the fix can be verified.
- Exit: passes 20 consecutive runs, including in parallel, after the root-cause fix. Then remove the marker in a PR that links the fix.
- Quarantine count and age are team metrics; a growing list is a process failure.

## Prevent
Condition-based waits only, unique data, function-scoped fixtures by default, no shared state, hygiene checks in pre-commit, repeated runs for every new test (`test-author` step).
