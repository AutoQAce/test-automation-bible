---
name: sdlc-delegate
description: Orchestrator mode for framework and suite work: decompose an approved spec and LLD into agent-sized task files and dispatch them to parallel subagents, worktrees, or background agents. Use for well-defined work such as automating many test cases on established interaction objects, adding adapters behind an existing port, or migrating tests, or when the user says "delegate", "parallelize", or "break this down".
---

# Delegate

| Keep in conductor mode | Delegate |
|---|---|
| First design of a port, adapter, or fixture family | Automating approved test cases on existing interaction objects |
| Synchronization and flakiness investigations | Adding a second adapter behind a proven port with contract tests |
| Security and environment configuration | Migrating tests to new interaction objects behind green tests |

Each task (`docs/tasks/_TEMPLATE.md`): one dominant risk, binary done condition (named tests pass N times, hygiene clean), declared files, must-NOT list, and its LLD. Tasks touching the same interaction object run sequentially.

Dispatch: `framework-implementer` / `test-author` subagents for small independent tasks; `git worktree add` per task for long ones; background agents for paragraph-sized tasks.

Judge independently: CI green, `automation-reviewer` clean, `design-reviewer` for structural changes, stability runs reported, human review.
