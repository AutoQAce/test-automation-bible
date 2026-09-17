## What and why
Spec: docs/specs/        Test cases: docs/test-cases/        Task: docs/tasks/        ADR:

## Kind of change
- [ ] Framework capability    - [ ] Automated tests    - [ ] Harness / CI    - [ ] Design docs only

## Mode
- [ ] Engineering (feat/fix/test → main)    - [ ] Exploration (must not target main)

## How it was built
- [ ] Agent-generated    - [ ] Human-written    - [ ] Mixed        Agents/models:

## Design
- [ ] No structural change
- [ ] HLD / LLD: `docs/design/`        `design-reviewer` verdict: ___
- [ ] `layers.toml` updated if layers changed; architecture check passes

## Test integrity
- [ ] No assertions removed or loosened (or each change cites a requirement)
- [ ] No sleeps, retries, reruns, ordering, or skip/xfail without reason
- [ ] New tests: run ≥ 3 times incl. parallel; proof of failure recorded
- [ ] Quarantine changes: ticket + expiry; removals link the fix

## Verification
- [ ] `uv run python scripts/check.py` passes
- [ ] Smoke jobs green (API/web, desktop)
- [ ] `automation-reviewer` pass; `test-quality-reviewer` for new suites; `automation-security-reviewer` for config/auth/data/evidence/XML/CI

## Risk
Environments touched:        Destructive tests:        Evidence/PII exposure:
