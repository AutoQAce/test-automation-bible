---
name: test-data-and-environments
description: Design test data and environment handling for the framework: configuration hierarchy and environment allow-lists, secrets from a secret store, data factories and builders, uniqueness per xdist worker, seeding and cleanup, synthetic PII, and service virtualization boundaries. Use when adding configuration, environments, credentials, fixtures that create data, or data files.
---

# Test data and environments

## Configuration
- One typed configuration object loaded once per run: environment name → base URLs, WSDL locations, application paths, browser settings, timeouts, feature flags.
- **Environment allow-list**: the framework refuses to run against hosts not declared for the chosen environment; production is not declared unless an ADR allows a specific read-only suite.
- Precedence: defaults → environment file (non-secret) → environment variables → CLI options. Log the resolved configuration (redacted) at session start.

## Secrets
- Test identities and keys come from the secret store or CI secrets, per environment and per role, least privilege, rotatable. Never in repository files, data files, templates, or reports.

## Data
- **Factories/builders** produce valid-by-default objects with explicit overrides; tests state only what matters to their behavior.
- **Uniqueness**: include the xdist worker id and a unique suffix in identifiers (usernames, order references) so parallel runs never collide.
- **Setup through the fastest reliable layer** (API or data layer), not through the UI.
- **Cleanup** in fixture teardown, tolerant of partial setup; nightly sweeper for leaked data in shared environments.
- **Synthetic PII only**; never copy production data into tests or fixtures.
- **Static data files** (expected documents, schemas, payload templates) versioned with the tests that use them, reviewed like code.

## Isolation choices (decided per dependency in the HLD)
Real shared environment · ephemeral environment per pipeline · service virtualization/stubs for unstable or costly third parties. Tests using stubs are labeled so they aren't counted as end-to-end coverage.
