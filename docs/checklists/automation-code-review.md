# Automation code review checklist

## Tests
- [ ] One behavior per test; name states the behavior
- [ ] One platform marker and one level marker (`hygiene_check.py` H004; framework self-tests: `unit` or `contract`)
- [ ] Oracle is concrete (values, state, side effects, errors), not "no exception" or "status ok"
- [ ] No assertions removed or loosened in this diff (`git diff main...HEAD -- tests/`)
- [ ] Proof of failure recorded for new tests
- [ ] Independent: no ordering, no reliance on other tests' data, runs alone and in parallel
- [ ] Data unique per worker, created through API/data layer, cleaned up
- [ ] No sleeps, retries, skip/xfail without reason, no quarantine without ticket and expiry
- [ ] No locators, endpoints, URLs, or credentials in tests

## Interaction objects (page / screen / service)
- [ ] Methods express user or API intent; no assertions inside
- [ ] Locators/endpoints owned here, one place per concept, stable strategy
- [ ] No engine library imports (only via ports)

## Framework code
- [ ] Engine libraries only in their driver layer (`scripts/architecture_check.py`)
- [ ] Condition-based waits with named, configurable timeouts and clear messages
- [ ] No global/session-scoped mutable state; parallel-safe
- [ ] Errors propagate with context; nothing swallowed
- [ ] Evidence captured on failure and redacted
- [ ] Typed, `mypy --strict` clean without new ignores

## Security
- [ ] No secrets in code, data files, templates, SOAP envelopes, CI files, or reports
- [ ] XML parsed with defusedxml/hardened parser; TLS verification on
- [ ] Environment allow-list respected; no production targets

## Design
- [ ] Passes `docs/checklists/design-review.md`; code matches its LLD
