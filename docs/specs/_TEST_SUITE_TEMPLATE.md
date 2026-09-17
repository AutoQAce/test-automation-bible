# Test-suite spec: <application feature>

Status: Draft | Approved        Owner: <human>        Application/version: <AUT>        Requirements: <links>

## Scope from risk
| Requirement / risk | Impact (1-5) | Likelihood (1-5) | Score | Automate? | Level (unit/api/ui) | Why that level |
|---|---|---|---|---|---|---|

## Scenarios
| Id | Scenario | Oracle (what proves pass/fail) | Platform | Level marker | Data | Priority |
|---|---|---|---|---|---|---|
<!-- Detailed cases in docs/test-cases/<id>.md -->

## Negative, boundary, permission, and error paths
<!-- REST status codes + error bodies, SOAP faults, UI validation, access denied, limits -->

## Test data and environments
- Data created per scenario and cleanup:
- Uniqueness across parallel workers:
- Environments (never production):
- Stubs/virtualized dependencies (label those tests):

## Execution
- Smoke (gates PRs):
- Regression (nightly / pre-release):
- Parallel-safe? Destructive tests?

## Traceability
| Requirement | Scenarios | Test ids (filled when automated) |
|---|---|---|

## Exit criteria
<!-- Which failures block a release; flake rate threshold; quarantine limit. -->

## Out of scope

## Open questions (cannot be Approved while any remain)
- [ ]
