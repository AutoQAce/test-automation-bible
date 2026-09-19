# Task: <spec>-NN <short imperative title>

Spec: <link>        LLD: <link or inline or "N/A, reason">        ADRs: <links>        depends_on: <ids>
Agent: framework-implementer | test-author        Mode: orchestrator | conductor

## Goal (one paragraph an agent can execute without questions)

## Design (required before dispatch)
- Module/object responsibilities and layer:
- Ports/Protocols touched:
- SOLID and simplicity check (one line each):
- Wiki pages to read (if `openwiki/` exists; links, not pasted code):

## Done when (binary)
- [ ] Tests pass: `<ids>`, each run ≥ 3 times including in parallel
- [ ] Proof of failure recorded for new automated tests
- [ ] `uv run python scripts/check.py` passes (incl. hygiene and architecture rules)
- [ ] `automation-reviewer` no CRITICAL/HIGH; `design-reviewer` approves structural changes

## Must NOT
- Remove or loosen assertions, add sleeps, retries, skip/xfail, or ordering
- Put locators, endpoints, credentials, or URLs in tests
- Touch files outside "Files in scope" or quality-gate config

## Files in scope

## Result (filled by the agent)
