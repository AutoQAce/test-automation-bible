# Design review checklist (test automation framework)

## HLD
- [ ] Quality attributes measurable (duration, flake rate, diagnosability, portability, security)
- [ ] Every layer has one responsibility; dependency direction tests → interaction objects → drivers → engines
- [ ] `docs/design/layers.toml` encodes the layers and library ownership
- [ ] Ports defined per capability; each adapter has a contract suite
- [ ] Execution model covers parallelism, desktop session limits, destructive tests, timeouts
- [ ] Data, environments, secrets, evidence, and failure modes designed explicitly
- [ ] Tool choices recorded as ADRs with spike evidence

## LLD
- [ ] Interaction objects model intent, own locators/endpoints, contain no assertions
- [ ] Protocols small (interface segregation); fakes are easy to write
- [ ] Models typed and validated; illegal states unrepresentable
- [ ] Fixtures: narrowest scope, cleanup, parallel safety stated
- [ ] Synchronization centralized and condition-based
- [ ] Dependencies injected via fixtures/composition point, never constructed in tests or objects

## SOLID
- [ ] S: page/screen/service objects change only when their screen/API changes
- [ ] O: new engine, browser, auth scheme, or report sink added without editing branches
- [ ] L: all adapters pass the same contract tests
- [ ] I: capability Protocols, not one giant driver interface
- [ ] D: tests depend on interaction objects; engines only in drivers

## Simplicity
- [ ] No framework layer, base class, or plugin point without a present second use
- [ ] No deep inheritance of pages or tests; composition instead
- [ ] Builders/factories only where defaults and overrides are genuinely needed

## Smells
- [ ] God BasePage / god fixture module · locators in tests · global driver · sleeps · retries-to-green · assertions in page objects · magic timeouts · UI used for data setup · swallowed exceptions · string comparison of XML/JSON documents
