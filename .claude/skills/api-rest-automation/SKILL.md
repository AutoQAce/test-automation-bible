---
name: api-rest-automation
description: Design and write REST/JSON API automation: HTTP client adapter behind ports, service objects per resource, typed request/response models, schema and contract validation (OpenAPI/JSON Schema), auth, negative and boundary testing, idempotent data setup and cleanup, and redacted request/response evidence. Use when building the REST client layer, service objects, or API test cases.
---

# REST API automation

## Client layer (only place the HTTP client library is imported)
- One configured client per API: base URL from environment config, timeouts, TLS verification on, connection reuse, correlation id header, retries **only** for infrastructure-level transient errors (connect errors), never for assertion failures or 5xx under test.
- Auth handled centrally (token acquisition, refresh, per-role identities from the secret store).
- Every request/response logged to evidence with headers and bodies redacted (Authorization, cookies, tokens, PII fields).

## Service objects
- One per resource or bounded API area: `orders.create(order)`, `orders.get(order_id)`. They build requests and parse responses into typed models; they return a result object that exposes status, headers, and the parsed body so tests can assert on any of them.
- No assertions inside service objects (except parsing failures raised as clear errors).

## What to assert (strong oracles)
- Status code **and** error body shape for failures; response schema validated against the OpenAPI/JSON Schema contract; business fields and their types; headers that matter (content type, caching, location); side effects verified through a read call or data layer.
- Negative and boundary: missing/invalid fields, wrong types, limits, unauthorized (401) vs forbidden (403), not found, conflict/idempotency, pagination edges, large payloads.
- Response time assertions only against agreed budgets and only in environments where they are meaningful.

## Data
- Create what a test needs through the API or data factories with unique identifiers per worker; clean up in fixtures (and tolerate cleanup of already-deleted data).
- Never depend on pre-existing records unless they are part of a controlled seed.

## Contract testing
- Validate responses against the published contract on every call in contract/smoke suites; fail with a readable diff.
- Track contract changes: a schema change without a version/ADR is a defect report, not a test update.
