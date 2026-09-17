---
name: automation-security
description: Secure the test automation framework and its pipelines: secrets for test identities, evidence and log redaction, environment allow-lists and production protection, least-privilege and destructive test isolation, XML attacks (XXE, entity expansion), TLS verification, dependency and binary supply chain, CI artifact exposure, and AI agents exploring the application under test (prompt injection via page content). Use when touching configuration, auth, test data, evidence, XML parsing, CI, or AI-driven exploration or self-healing.
---

# Automation security

Test automation holds powerful credentials, touches many systems, and produces artifacts full of screenshots and payloads. Treat it as a production system.

| Risk | Control |
|---|---|
| Leaked test credentials | Secret store/CI secrets only; secret hooks and CI scans; rotation; per-environment identities |
| Sensitive data in evidence | Redaction of headers, bodies, fields, and screen regions before artifacts leave the runner; bounded retention; restricted artifact access |
| Running against production | Environment allow-list enforced by the framework; production absent by default; read-only exceptions only via ADR |
| Over-privileged test users | Least privilege per role; destructive tests isolated and serialized |
| XML attacks in API testing | `defusedxml` or hardened parsers; never fetch DTDs/schemas referenced by responses |
| Disabled TLS verification | On by default; any exception scoped and recorded in an ADR |
| Supply chain | Locked dependencies, install-time package checks, pinned browser/driver binaries from trusted sources, Dependabot cooldown |
| CI exposure | Secrets never echoed; forks/PRs from outside cannot access secrets; artifacts reviewed for sensitive content |
| AI agents exploring the application (browser/desktop MCP, crawlers) | Page and screen content is untrusted input; agents cannot change expected values, approve their own fixes, or access production; exploration runs in test environments with test identities |
| AI self-healing locators | Suggestions only, reviewed by a human with evidence; never auto-committed |

Minimum bar before the framework runs in shared CI: secrets in store · allow-list active · redaction verified on a failing test of each platform · XML parsing hardened · artifacts access-controlled and retained briefly · `automation-security-reviewer` sign-off.
