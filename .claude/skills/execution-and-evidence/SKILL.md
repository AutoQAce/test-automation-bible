---
name: execution-and-evidence
description: Design execution, CI orchestration, and reporting for the framework: pytest markers and suites (smoke/regression), xdist parallelism and worker isolation, desktop runner constraints, browser/OS matrices, timeouts, test selection, JUnit output, evidence capture and redaction, reporting and traceability, and pipeline quality gates. Use when configuring how and where suites run and what results and artifacts they produce.
---

# Execution and evidence

## Suites
- Markers from `pyproject.toml`: platform (`web`, `desktop`, `api`, `rest`, `soap`), level (`smoke`, `regression`), governance (`quarantine`, `destructive`). Framework self-tests carry `unit` or `contract`; every automated test has one platform (`web`, `desktop`, `api`) and one level marker, otherwise no CI job selects it (`hygiene_check.py` H004).
- **Smoke**: minutes, critical paths, gates every PR. **Regression**: full, nightly and pre-release. Gating runs always add `-m "... and not quarantine"`.

## Parallelism
- `pytest-xdist` for web and API suites; tests must be independent and data-unique per worker. Scope expensive resources per worker, never share mutable state across workers.
- Desktop UI suites run serially per desktop session; scale out with more runners, not more workers.
- `destructive` tests run in a separate serial job.

## Timeouts and failure handling
- Per-action timeouts (framework), per-test timeout, and per-job timeout in CI. A hung test must fail with evidence, not stall the pipeline.
- Infrastructure retries (e.g. grid session creation) are logged and counted; test-level reruns are not used as a gate.

## Evidence and reporting
- JUnit XML from every job (input to `scripts/flaky_report.py` and CI dashboards).
- On failure, per platform: web (screenshot, DOM/trace, console, network), desktop (window + screen capture, element tree, app logs), API (redacted request/response). Attach to the report, keep artifacts for a bounded retention period.
- **Redaction** before artifacts leave the runner. Screens and payloads can contain PII and tokens.
- Traceability: test ids mapped to requirement ids (marker or metadata) so reports show requirement coverage and status.

## CI gates (see `.github/workflows/`)
PR: harness scans + `check.py` + smoke (API/web on Linux, desktop on Windows). Nightly: regression matrix run twice + flaky report. Weekly: mutation testing of framework core.

## Metrics to watch
Pass rate excluding product bugs · flake rate · quarantine count and age · median and p95 suite duration · time from failure to classified root cause · requirement coverage of high-risk items.
