# Framework capability spec: <capability>

Status: Draft | Approved        Owner: <human>        Related: ADR-NNNN, HLD-NNNN
Platforms: web | desktop | rest | soap | cross-cutting

## Problem and consumers
<!-- Which test authors/suites need this, what hurts today. -->

## Intended usage (the test code this enables)
```python
# Sketch of how a test author will use it. Interaction-level, no engine calls.
```

## Acceptance criteria (binary, testable)
- AC-1:

## Variants in scope
<!-- browsers / OS / desktop technologies / REST or SOAP versions / auth schemes / environments -->

## Quality attributes (measurable)
| Attribute | Target | How measured |
|---|---|---|
| Execution overhead | | |
| Flake contribution | 0 known | repeated runs, flaky_report |
| Diagnosability | failure evidence answers "what and why" without rerun | review of failing sample |
| Parallel safety | N workers without interference | parallel contract run |
| Security | no secrets/PII in artifacts | redaction test |

## Failure behavior
| Situation | What the test author sees (exception, message, evidence) |
|---|---|
| Timeout | |
| Not found / unexpected state | |
| Environment unreachable | |
| Malformed response | |

## Design
- HLD required? yes/no (new platform, integration, or cross-cutting service → yes)
- LLD: one per task that adds or changes a module, class, Protocol, fixture family, or model

## Out of scope

## Open questions (cannot be Approved while any remain)
- [ ]
