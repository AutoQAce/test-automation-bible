# Patterns and anti-patterns in test automation

## Patterns (use when they solve a present problem)
| Pattern | Use for |
|---|---|
| Page Object / Component Object (web) | User-level intent for a page or reusable component; owns locators |
| Screen Object (desktop) | Same idea for windows/dialogs; owns automation ids and window lifecycle |
| Service Object (REST / SOAP) | One per resource or service; builds requests, parses responses into typed models |
| Ports and adapters | Isolate each engine library behind small Protocols |
| Factory (fixtures) / composition point | Build drivers and clients from configuration in one place |
| Builder / factory for test data | Valid-by-default data with explicit overrides; unique per worker |
| Strategy | Wait conditions, locator strategies, auth schemes, report sinks |
| Decorator / hook | Evidence capture, timing, redaction around actions |
| Typed models (Pydantic/dataclasses) | Parse API responses once; assert on fields, not raw strings |
| Contract tests | Prove adapters are substitutable |

## Anti-patterns → refactoring
| Anti-pattern | Why it hurts | Refactoring |
|---|---|---|
| Hard sleeps | Slow and still flaky | Condition-based waits with timeout and clear message |
| Locators/XPaths in tests | UI change breaks many tests | Move into interaction objects; prefer stable attributes |
| God `BasePage` inherited everywhere | Every change touches everything | Composition of small components and capabilities |
| Assertions inside page objects | Hides the oracle, couples intent to checks | Return state; assert in the test or a verification helper |
| Global/singleton driver | Breaks parallel runs, leaks state | Per-test or per-worker fixture with the narrowest scope |
| Tests depending on order or each other | Random failures, can't run subsets | Independent setup via factories/API |
| Retries/reruns to green | Hides real races and product bugs | Root-cause fix or quarantine with ticket and expiry |
| UI setup for data | Slow, flaky | Create state through API or data layer |
| `assert response.ok` only | Oracle too weak | Assert status, schema, and business fields |
| Swallowed exceptions in helpers | Failures appear elsewhere | Let them propagate with context |
| Magic timeouts scattered | Inconsistent, untunable | Named, configurable timeouts per environment |
| Parsing XML with the stdlib parser | XXE / entity expansion | defusedxml or hardened parser |
