---
name: system-design-hld
description: Produce or review the high-level design of the test automation framework or a major capability: quality attributes, layers and dependency rules (tests -> interaction objects -> drivers -> engines), platform driver ports, configuration and environments, test data, evidence and reporting, execution and parallelism, CI topology, failure modes. Use for the initial framework architecture, a new platform or integration, or any cross-layer change, or when the user says "HLD", "architecture", "framework design", or "how should the framework be structured".
---

# High-level design for a test automation framework

The HLD decides what the parts are, what each is responsible for, how they depend on each other, and how the framework behaves when the application, environment, or infrastructure misbehaves. Write it in `docs/design/NNNN-<name>-hld.md` (NNNN = highest existing `docs/design/NNNN-*.md` plus one; the first is `0001`; templates and `layers.toml` don't count) from `_HLD_TEMPLATE.md`, and **encode its layer rules in `docs/design/layers.toml`** (start from `_layers.example.toml`) so `scripts/architecture_check.py` enforces them.

## Procedure
1. **Quality attributes first** (measurable): suite execution time, flake rate, parallel scalability (workers, grid), diagnosability (evidence per failure), maintainability (blast radius of a UI change), portability (browsers/OS/desktop tech), security (secrets, evidence, environments).
2. **Context**: application(s) under test per platform, environments, CI, test management/reporting systems, secret store, grids/devices.
3. **Layers and responsibilities** (typical; adapt, don't copy blindly):
   | Layer | Single responsibility |
   |---|---|
   | Tests | Express one behavior and its oracle using the layers below |
   | Interaction objects | Page/component objects (web), screen objects (desktop), service objects (REST/SOAP): user- or API-level intent, own locators/endpoints |
   | Assertions / verification | Domain-meaningful checks with good failure messages |
   | Test data | Factories/builders, unique data per worker, cleanup |
   | Drivers (per platform, behind ports) | Wrap one engine library: session lifecycle, synchronization, evidence hooks |
   | Core | Configuration and environments, logging, redaction, errors, retry policy for infrastructure only |
   | Reporting / evidence | Collect and publish results and artifacts |
   | Composition (fixtures / plugin) | Build drivers and clients from configuration; the only wiring point |
4. **Dependency rule**: inward only. Tests never import drivers or engines; engines are imported only by their driver. Write this into `layers.toml` (`may_import`, `library_owners`).
5. **Ports**: one small Protocol per capability a test needs (navigate, find, act, read, wait, call). Each platform adapter implements them and passes a shared contract suite.
6. **Execution model**: parallelism (xdist workers, grid, desktop sessions that cannot share a screen), isolation per worker, ordering independence, timeouts at every level.
7. **Data and environments**: configuration hierarchy, environment allow-list (never production by default), secrets via store, data lifecycle.
8. **Evidence and reporting**: what is captured on failure per platform, redaction, retention, where results go, traceability to requirements.
9. **Failure modes**: environment down, flaky dependency, grid capacity, desktop session lock, schema drift, auth expiry. Detection and behavior for each.
10. **Alternatives**: summarize; record tool and structure trade-offs as ADRs (`docs/adr/DECISION_BACKLOG.md`).
11. **Review**: `design-reviewer` + human architect. Then LLDs per capability.

## Anti-patterns
Tests calling engine APIs directly · one "BasePage" god class every page inherits · framework layers with one caller · global driver singletons (breaks parallelism) · configuration read ad hoc from `os.environ` everywhere · evidence captured only locally · UI suites doing what API tests should.
