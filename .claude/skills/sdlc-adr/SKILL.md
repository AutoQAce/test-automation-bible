---
name: sdlc-adr
description: Record an architecture decision for the test automation framework in docs/adr/, especially tool and structure choices from docs/adr/DECISION_BACKLOG.md (web engine, desktop automation technology, REST client, XML/SOAP client and schema validation, reporting, parallelism, test data, environments and secrets, grid/infrastructure, repository layout). Use when a trade-off must be decided or when the user says "ADR", "which tool", "decide", or "compare options".
---

# Architecture decision records

Tool choices shape the framework for years. Decide them explicitly, with evidence from a spike, not by habit.

1. Number it: the highest existing `docs/adr/NNNN-*.md` plus one, four digits; the first ADR is `0001` (`_TEMPLATE.md` and `DECISION_BACKLOG.md` don't count). Copy `_TEMPLATE.md` and link the backlog item.
2. **Context**: the platforms, applications under test, team skills, CI/infrastructure, licensing, security constraints, and the quality attributes from the HLD.
3. **Options**: at least two real ones. For tool decisions run a **time-boxed spike on a `spike/*` branch** against the real application: one representative flow, run in CI, in parallel, with evidence capture. Record measured results (stability over N runs, execution time, setup effort, diagnosability), not marketing claims.
4. **Decision** as a trade-off ("we choose X, accepting Y, to get Z"). Status stays `Proposed` until a human accepts.
5. **Design principles impact**: how the choice is isolated behind a port so it can be replaced (dependency inversion), and how that is enforced (`library_owners` in `layers.toml`).
6. **Consequences and rules** every future change must follow (e.g. "only `drivers/web` imports the browser engine").
7. On acceptance: update AGENTS.md Stack line, `layers.toml`, and the backlog status.
