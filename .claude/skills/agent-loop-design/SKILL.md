---
name: agent-loop-design
description: Design or review AI loops in the test automation lifecycle so they cannot spin, game their verifier, or silently weaken tests: AI test generation from specs or recordings, self-healing locator suggestions, failure auto-triage, self-correction on red tests, and scheduled autonomous maintenance. Use when adding any AI-driven or autonomous loop to building, running, or maintaining tests.
---

# AI loops in test automation

## The Goodhart trap specific to testing
"Make the tests pass" is trivially satisfied by weakening the tests. Every loop needs a goal **and** boundaries that make cheating impossible or visible.

## Write a loop
1. **Should it exist?** Repeating task, automatable verification, affordable token budget, and the agent can actually run tests and see results.
2. **Decidable goal** tied to external truth: "test passes on the fixed build **and** fails on the known-bad build", not "test passes".
3. **Boundaries** (enforced by hooks and checks here): no removed/loosened assertions, no sleeps/retries/skip, no changed expected values without a cited requirement, no edits to quality config.
4. **Independent judge**: CI and `test-quality-reviewer`, never the agent that wrote the change.
5. **Damping**: retry cap (Stop hook `SDLC_MAX_FIX_ATTEMPTS`), time and cost caps, then a human.
6. **Front-load ambiguity**: unclear oracle = stop before generating.

## Loop-specific rules
| Loop | Rule |
|---|---|
| Test generation from specs or recordings | Output is a draft PR with proof-of-failure notes; human reviews oracles |
| Self-healing locators | Propose a locator change with before/after evidence; human approves; never at runtime in gating suites |
| Failure auto-triage | Classifies and routes; never quarantines or edits tests on its own |
| Nightly autonomous maintenance | Opens PRs only; never merges; never updates baselines or expected values |

## Red lines
Final acceptance of tests, expected-value changes, quarantine decisions, and anything touching production stay with humans.
