---
name: sdlc-harness-fix
description: Fix the development harness after a coding agent does something wrong in framework or test code so it cannot recur (added a sleep, weakened an assertion, put a locator in a test, imported an engine in a test, hard-coded a credential, masked a flaky test, broke parallel safety). Use when the user says "don't do that again", "why did the agent do X", or "add a rule".
---

# Harness post-mortem

| Symptom | Cause | Fix at |
|---|---|---|
| Didn't know a convention | missing instruction | AGENTS.md line or platform skill |
| Knew the rule, broke it again | prose, not enforcement | hook in `.claude/hooks/lib/` or rule in `scripts/hygiene_check.py`, with a test |
| Imported an engine or driver in the wrong layer | layer rule missing | `docs/design/layers.toml` (`may_import`, `library_owners`) |
| Guessed an expected value | oracle not specified | test-case spec + "ask when unclear" |
| Made a flaky test green with retries | no quarantine path known | `flaky-test-management` skill + quality guard |
| Broke parallel runs | fixture scope/state not designed | LLD fixture section + design review |
| Graded its own tests as effective | no independent proof | proof-of-failure step, `test-quality-reviewer`, mutation job |
| Forgot rules in a long session | context rot | trim AGENTS.md, move procedures to skills, fresh session per task |

Cheapest reliable layer: never-break rules → hooks/hygiene/architecture checks; every-task rules → one AGENTS.md line; procedures → skills.
Record: `- YYYY-MM-DD: <rule>. (why: <what happened>)` in AGENTS.md Lessons, plus a test that reproduces it. Harness changes go through CODEOWNERS.
