---
name: api-xml-soap-automation
description: Design and write XML and SOAP API automation: SOAP client adapter behind ports, service objects per operation, envelope and namespace handling, WS-Security and auth, XSD/WSDL schema validation, SOAP fault assertions, safe XML parsing (no XXE or entity expansion), and redacted evidence. Use when building the XML/SOAP client layer, service objects, or XML/SOAP test cases.
---

# XML / SOAP API automation

## Client layer (only place the SOAP/XML libraries are imported)
- Build the client from the WSDL or a pinned local copy (a pinned copy makes contract drift visible in code review). Endpoint, timeouts, and TLS verification from environment config.
- **Safe parsing is mandatory**: parse with `defusedxml` or a parser configured to forbid DTDs, external entities, and entity expansion. Never parse response XML with a default stdlib parser. Never load schemas or stylesheets referenced by a response.
- WS-Security / auth headers built centrally from the secret store; passwords never appear in templates, test data, or logs.
- Evidence: request and response envelopes logged with security headers and sensitive elements redacted.

## Service objects
- One per service or operation group: `billing.create_invoice(invoice)`. They build envelopes from typed models (not string concatenation), handle namespaces in one place, and parse responses into typed models or return the parsed tree for XPath assertions.
- No assertions inside service objects.

## What to assert
- Response validated against the XSD/WSDL types; operation result fields by namespace-aware XPath or typed model.
- **SOAP faults** as first-class outcomes: fault code, fault string, and detail elements for invalid input, auth failures, and business rule violations.
- HTTP status alongside the SOAP envelope (some stacks return 500 with a fault, others 200).
- Namespaces and element order where the contract requires them; do not compare whole documents as strings (whitespace, attribute order, and prefixes vary). Use canonicalized or semantic comparison.

## Plain XML over HTTP (non-SOAP)
Same rules: typed request building, schema validation, safe parsing, namespace-aware assertions, redaction.

## Data
Unique identifiers per worker, cleanup through the service or data layer, controlled seeds only.
