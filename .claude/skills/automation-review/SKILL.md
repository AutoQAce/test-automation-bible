---
name: automation-review
description: Review framework or test-code changes against the automation code review and design checklists before a human sees them. Use before committing, before a PR, when reviewing AI-generated tests, or when the user says "review", "check this test", or "is this ready".
---

# Automation review

1. `git diff main...HEAD`; read the spec, test cases, and LLD it implements.
2. Machines first: `uv run --no-sync python scripts/check.py --fast` (lint, types, self-tests, architecture rules, hygiene).
3. Walk `docs/checklists/automation-code-review.md`, then `docs/checklists/design-review.md` for structural changes.
4. Verify mechanically:
   - `git diff main...HEAD -- tests/` for removed or loosened assertions and new skip/xfail/quarantine markers
   - new tests were run repeatedly and in parallel (ask for the evidence)
   - imports respect `layers.toml`; engine libraries only in drivers
   - new dependencies: `python scripts/verify_deps.py`
5. Report `SEVERITY file:line: problem -> fix`. Request `design-reviewer` (structure), `test-quality-reviewer` (new suites, AI-generated tests), `automation-security-reviewer` (config, auth, data, evidence, XML, CI).
