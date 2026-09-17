---
name: test-quality-and-mutation
description: Measure whether tests actually catch defects: oracle strength, mutation testing of framework code, fault injection and proof-of-failure for automated suites (especially AI-generated tests), requirement and risk coverage, pyramid balance, and duplication. Use when reviewing new suites, before releases, when coverage looks high but bugs escape, or when the user says "are these tests good", "mutation testing", or "test effectiveness".
---

# Test quality and mutation

Code coverage says what ran, not what was checked. For a test automation framework, the question is: **would this test fail if the behavior were wrong?**

## Framework code: mutation testing
- Run mutation testing on framework core (configuration, data factories, waits, parsers, redaction, report logic) weekly in CI on Linux (`.github/workflows/weekly-mutation.yml`); set `[tool.mutmut]` paths to the framework package once the HLD names it.
- Surviving mutants in core logic become new unit tests or reveal dead code. Track the mutation score trend, not a vanity target.

## Automated suites: proof of failure
For each new or AI-generated test, record at least one way its failure was observed:
- wrong expected value temporarily asserted (line marked `# sdlc: justified proof of failure, revert`, which the test-integrity hook requires), then restored;
- stubbed faulty response (API) or feature flag toggled (UI);
- run against a known-bad build or seeded defect in a test environment.
A test never observed failing is unverified.

## Oracle strength checklist
- Asserts business outcomes (values, states, side effects), not just "no exception", "status 200", or "element visible".
- Checks the negative space: error messages, faults, permissions, and that forbidden side effects did not happen.
- Failure messages say expected vs actual in domain terms.

## Coverage that matters
- Map test-suite spec risks → tests; report uncovered high-risk items explicitly.
- Pyramid balance: UI tests for flows and integration; API/unit for rules and variations.
- Remove duplicates that check the same behavior the same way; they cost run time and maintenance.

## AI-generated tests
Treat them like generated code: review oracles line by line, require proof of failure, reject tests that restate the implementation, and never let an agent update expected values to match current application output without a cited requirement.
