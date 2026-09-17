---
name: taf-spec
description: Write a framework capability spec or a test-suite spec for the test automation framework. Use before building any framework capability (driver, waits, data, reporting, configuration) or automating any application feature, or when the user says "spec", "test strategy", "test plan", "what should we automate", or "requirements".
---

# Specs for a test automation framework

Two kinds of spec, because two kinds of product live here.

## A. Framework capability spec (`docs/specs/_FRAMEWORK_CAPABILITY_TEMPLATE.md`)
For anything the framework offers to test authors: a platform driver, synchronization, configuration and environments, test data, evidence and reporting, parallel execution, CI integration.
1. **Consumers**: which test authors or suites need it, and what they will write with it (show the intended test code shape).
2. **Capabilities** as testable acceptance criteria `AC-n` (e.g. "a failed web test attaches a screenshot and trace, with fields matching the redaction list masked").
3. **Platforms and variants** in scope: browsers, OS versions, desktop technologies, REST/SOAP versions, auth schemes.
4. **Quality attributes, measurable**: execution time budget, flake rate target, parallel scalability, failure diagnosability (time to root cause), portability, security.
5. **Failure behavior**: timeouts, unreachable environment, element not found, malformed response. What does the test author see?
6. **Design gate**: HLD required? (new platform, new integration, new cross-cutting service → yes).

## B. Test-suite spec (`docs/specs/_TEST_SUITE_TEMPLATE.md`)
For automating an application feature.
1. **Scope from risk**: list requirements and risks; score impact × likelihood; automate high-risk first.
2. **Right level (pyramid)**: for each check pick the lowest level that can observe the risk (unit/API before UI). UI tests cover user-visible flows and integration, not every validation rule.
3. **Scenarios** with ids, each with an explicit **oracle** (expected value, state, side effect, error), data needs, preconditions, and platform. Detailed cases go to `docs/test-cases/`.
4. **Negative, boundary, permission, and error paths** (REST status codes and error bodies, SOAP faults, UI validation, access denied).
5. **Data and environments**: what data each scenario creates, isolation, cleanup; which environments; no production.
6. **Traceability**: requirement id → scenario ids → test ids (filled as tests are written).
7. **Exit criteria**: which scenarios gate a release (smoke), which run nightly (regression).

Open questions block approval. Unclear expected behavior is never guessed: ask the product owner.
Next: ADRs for tool choices (`sdlc-adr`), HLD/LLD (`system-design-hld`, `code-design-lld`), then `taf-contract-first`.
