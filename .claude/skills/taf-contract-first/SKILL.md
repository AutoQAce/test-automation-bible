---
name: taf-contract-first
description: Write tests before code: framework unit tests with fakes and contract tests for every adapter before implementing framework capabilities; test-case specs with explicit oracles and a proof-of-failure plan before automating application features. Use when starting any framework capability, adapter, or automated test, or when the user says "TDD", "tests first", "contract tests", or "test cases".
---

# Contract first

## Framework code
1. From the LLD, write **unit tests** (`@pytest.mark.unit`) against public interfaces using fakes of ports: success, not found, timeout, stale/changed state, malformed response, redaction applied, evidence captured.
2. Write **contract tests** (`@pytest.mark.contract`) once per port and parametrize over every adapter (fake adapter now, real adapters as they arrive). Contract tests needing a real engine run in the platform CI job, not in `check.py`.
3. Run them; they must fail for the right reason. Then implement (`framework-implementer`). While only test files have changed, the Stop hook lets the turn end as a "red phase" if every other fast gate passes; never mark the tests skip/xfail to get there.

## Automated test cases
1. Write/confirm the test case in `docs/test-cases/` from `_TEMPLATE.md`: id, requirement, preconditions, data, steps at user/API intent level, **oracle**, platform, level.
2. The oracle is concrete: exact values, state transitions, side effects (record created, email queued, file exported), error codes and messages.
3. Plan the **proof of failure**: how you will show the automated test fails when the behavior is wrong (wrong expected value, stubbed faulty response, feature flag off, known-bad build).
4. Only then automate (`test-author`). A test whose failure was never observed is unverified.

## Never
Write the implementation first and then tests that mirror its current output; copy the application's actual output into expectations without checking the requirement.
