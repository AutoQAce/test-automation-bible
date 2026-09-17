# ADR decision backlog

Decisions a Python + pytest enterprise test automation framework must make **before** building the affected layer. Each becomes an ADR with a spike on the real application. Status: Open | Spiking | Decided (ADR-NNNN).

| Id | Decision | Blocks | Evaluate against | Status |
|---|---|---|---|---|
| D-01 | Web automation engine | web driver, page objects, web CI | stability over N runs on the real app, auto-waiting, cross-browser needs, tracing/evidence, parallel isolation, team skills, grid/cloud support | Open |
| D-02 | Desktop automation technology per application UI framework | desktop driver, screen objects, Windows runners | element identification on the real app, supported UI frameworks, stability, runner/session requirements, maintenance and support status | Open |
| D-03 | REST client library | API clients, service objects | timeouts, TLS, auth hooks, async need, logging/redaction hooks, typing | Open |
| D-04 | XML/SOAP client and schema validation | SOAP clients, XML service objects | WSDL support, WS-Security, namespace handling, safe parsing, XSD validation | Open |
| D-05 | Contract/schema validation approach (OpenAPI/JSON Schema, XSD) | API assertions | contract source of truth, error readability | Open |
| D-06 | Reporting and evidence store | evidence layer, CI | per-platform artifacts, redaction hooks, traceability, retention, access control | Open |
| D-07 | Parallel execution and infrastructure (xdist, grid, cloud browsers, Windows desktop runners) | execution model | capacity, isolation, cost, security | Open |
| D-08 | Test data strategy per system (API seeding, DB, virtualization) | data layer | speed, isolation, cleanup, compliance | Open |
| D-09 | Configuration and secrets (config format, secret store integration, environment allow-list) | core | security, simplicity, CI integration | Open |
| D-10 | Repository and packaging layout (framework and suites together or separate; versioning) | everything | team structure, release cadence, reuse across products | Open |
| D-11 | Test management / traceability integration | reporting | requirement mapping, audit needs | Open |
| D-12 | AI usage in the lifecycle (generation, self-healing suggestions, triage) and its guardrails | agent loops | skill `agent-loop-design`, security review | Open |
