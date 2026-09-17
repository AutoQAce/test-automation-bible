---
name: code-design-lld
description: Produce or review the low-level design and code structure of framework components and test code: SOLID for test automation, interaction objects, ports and adapters, fixtures and scopes, data builders, typed models, wait/evidence design, patterns and anti-patterns, complexity budget, and testability. Use before writing any new module, class, Protocol, fixture family, or data model, when refactoring, or when the user says "LLD", "SOLID", "page object design", "refactor", or "clean code".
---

# Low-level design for framework and test code

Write `docs/design/NNNN-<name>-lld.md` (NNNN = highest existing `docs/design/NNNN-*.md` plus one; templates and `layers.toml` don't count) from `_LLD_TEMPLATE.md` (or an LLD section in the task; `LLD: N/A, <reason>` for changes inside one function).

## Procedure
1. **Locate**: HLD layer and `layers.toml` rules; neighbors to follow.
2. **Module map**: one responsibility per file (page object, service object, adapter, factory, fixture module).
3. **Interfaces first**: Protocols for ports; public methods of interaction objects named in user/API language (`submit_order`, not `click_button_3`).
4. **Models**: typed request/response models and value objects (order ids, money, dates) with validation; frozen by default.
5. **Fixtures**: name, scope (function by default), what they yield, cleanup, parallel safety (xdist worker isolation).
6. **Synchronization and errors**: which conditions are awaited, timeouts, exceptions raised, failure messages, evidence captured.
7. **SOLID and simplicity checks** with evidence (`references/solid-for-test-automation.md`).
8. **Tests**: unit tests with fakes for framework logic; contract tests for adapters; which test cases will use it.
9. **Review** with `design-reviewer`; keep code and LLD consistent.

## Complexity budget (machine-enforced)
Complexity ≤ 8 · ≤ 40 statements · ≤ 5 params (use a parameter object) · ≤ 5 returns · modules ≤ 400 lines · no magic numbers · no private-member access · layer rules from `layers.toml` · `mypy --strict`.

References: `references/solid-for-test-automation.md`, `references/patterns-and-antipatterns.md`.
