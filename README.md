# test-automation-bible

The AI-led SDLC kit for **architecting and developing an enterprise test automation framework from scratch** in
**Python + pytest**, covering **Web, Desktop, and API (REST/JSON, XML/SOAP)**.

It contains no framework code or folder structure. It gives your team and its coding agents:
- **Doctrine**: [`BIBLE.md`](BIBLE.md), a phase-by-phase runbook where every practice is labelled BIBLE, ECC, or NEW
- **Static context**: `AGENTS.md` with test-automation hard rules (imported by `CLAUDE.md`, `GEMINI.md`)
- **Hooks** that block credentials (incl. SOAP/URL/DSN), sleeps and weakened assertions in tests, retries/ordering markers, gate weakening, hook bypasses, and hallucinated packages
- **10 agents** and **18 skills** for planning, design, framework building, test authoring, review, security, flakiness, and triage
- **Templates**: capability and suite specs, test cases with oracles, HLD/LLD, `layers.toml`, ADR decision backlog, tasks, checklists
- **Gates**: `scripts/check.py` (lint + design rules, strict types, self-tests, architecture rules, test hygiene, scans, audit), flaky detection, CI for PR smoke, nightly regression ×2, weekly mutation

## Start
```bash
uv sync
uv run python scripts/check.py
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```
Then follow `BIBLE.md` §0: walking-skeleton spec → ADRs with spikes → HLD + `layers.toml` → LLDs → contract-first → build.
See [`docs/FEATURE_WALKTHROUGH.md`](docs/FEATURE_WALKTHROUGH.md) for one feature traced from an empty kit to a merged PR, step by step.

## Everyday commands
| Task | Command |
|---|---|
| All gates | `uv run python scripts/check.py` |
| Agent loop | `uv run python scripts/check.py --fast` |
| Test hygiene on files | `uv run python scripts/hygiene_check.py tests/web` |
| Architecture rules | `uv run python scripts/architecture_check.py` |
| Flaky detection | `uv run python scripts/flaky_report.py run1.xml run2.xml --fail-on-flaky` |
| Harness evals (needs `claude` CLI) | `uv run python scripts/harness_eval.py` |
| Security scan of the harness | `npx --yes ecc-agentshield@1.6.0 scan --path .claude` |
