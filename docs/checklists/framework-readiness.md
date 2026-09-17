# Framework readiness (before suites gate releases)

## Reliability
- [ ] Flake rate below target for 2 consecutive weeks (nightly flaky report)
- [ ] Quarantine list small, every item with ticket and expiry
- [ ] Environment health checks run before suites

## Diagnosability
- [ ] Every platform attaches redacted evidence on failure
- [ ] Failure messages state expected vs actual in domain terms
- [ ] Results and artifacts reachable from CI in one click; retention defined

## Scale and speed
- [ ] Smoke within budget on every PR; regression within budget nightly
- [ ] Parallel runs verified; desktop runners provisioned and documented

## Security
- [ ] Secrets in store, identities least-privilege, rotation documented
- [ ] Environment allow-list enforced; production excluded
- [ ] XML parsing hardened; TLS verification on; artifacts access-controlled
- [ ] automation-security-reviewer sign-off

## Maintainability
- [ ] HLD, ADRs, layers.toml current; architecture check green
- [ ] Mutation score of framework core tracked; contract suites cover every adapter
- [ ] Onboarding guide: how to add a page object, a service object, a test, a new environment

## Governance
- [ ] CODEOWNERS for framework core, suites, harness, and designs
- [ ] Traceability from requirements to tests available in reports
