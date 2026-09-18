# The AI-SDLC Bible: Test Automation Edition

> How to architect and develop an **enterprise test automation framework (TAF)** for **Web, Desktop, and
> API (REST/JSON and XML/SOAP)** in **Python + pytest**, from scratch, with an AI-led SDLC.
> Doctrine from *The New SDLC With Vibe Coding* (Osmani, Saboo, Kartakis, May 2026), hardened with ECC's
> harness practices, and tailored to the failure modes of test automation.
>
> **Generation is solved. Oracles, reliability, and judgment are the new craft.**

This kit contains **no framework code and no folder structure**. It is the SDLC system that makes an AI-assisted
team design and build one well: doctrine, static context, hooks, agents, skills, templates, gates, and CI.

**Source labels used throughout:** **BIBLE** = practice from the paper via the AI-SDLC bible · **ECC** = practice
adapted from ECC · **NEW** = built specifically for test automation.

Contents: 0 Start · 1 Creed · 2 Mental models · 3 Runbook · 3A Knowledge layer (OpenWiki) · 4 Design discipline · 5 Platform playbooks ·
6 Reliability and flakiness · 7 Data, environments, secrets · 8 Execution, evidence, CI · 9 Security ·
10 AI in the test automation lifecycle · 11 Economics and metrics · 12 When the agent gets it wrong ·
13 Playbooks · 14 Keeping it alive · Appendix: kit map

---

## 0. Start

```bash
uv sync                                    # Python 3.12+, dev tools locked
uv run python scripts/check.py             # all gates (green on an empty framework)
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

**Day-1 checklist**
- [ ] Read this bible, `AGENTS.md`, and `docs/adr/DECISION_BACKLOG.md`.
- [ ] CODEOWNERS: real people for harness, test architecture, framework core, suites.
- [ ] GitHub: branch protection on `main` requiring `ci`; `test` environment with test-only secrets; Windows runner plan for desktop.
- [ ] First spec: framework capability spec for the **walking skeleton** (one web, one desktop, one REST, one SOAP happy path end to end, with evidence, in CI).
- [ ] ADRs D-01 to D-10 decided with spikes on the real applications (`sdlc-adr`).
- [ ] HLD with `docs/design/layers.toml` (from `_layers.example.toml`), reviewed by `design-reviewer` + human.
- [ ] Set `SDLC_FACT_FORCE_PATHS` in `.claude/settings.json` and `[tool.mypy] files` in `pyproject.toml` to the framework package the HLD names.
- [ ] Optional, once the framework has code: a grounded code wiki with OpenWiki, then enable `openwiki-update.yml` (section 3A, skill `sdlc-wiki`).
- [ ] Mark this kit's example files as templates only; delete nothing you haven't replaced.

---

## 1. The creed

From the paper (**BIBLE**):
1. **Structure scales, vibes don't.** Explore on `spike/*`; production automation needs specs, oracles, design, gates, and human review.
2. **AI amplifies your engineering culture.** A weak QA culture plus AI produces thousands of tests that can't fail.
3. **The human role moves to judgment**: what to test, what "correct" means, and whether a test really protects the product.

Harness engineering (**ECC**, **BIBLE**):
4. **Hooks over prose.** Never-break rules are code: hooks, checks, CI gates.
5. **The builder never grades itself.** Independent reviewers, CI, and proof of failure.
6. **Lean static context.** Procedures in skills; AGENTS.md ≤ 150 lines.
7. **Every loop has damping.** Retry caps, then a human.

Test automation truths (**NEW**):
8. **A test that cannot fail is worse than no test.** It spends money and creates false confidence.
9. **Flaky tests are bugs.** Quarantine with a ticket and an expiry; never rerun to green.
10. **Tests are production code.** Same design, review, security, and quality bar as the product.
11. **The test is the oracle, not the application.** Expected values change only with a cited requirement.
12. **Design before code, enforced after merge.** Layers, SOLID where it pays, simplicity; machines check the rules.

---

## 2. Mental models

### 2.1 Two harnesses (BIBLE, adapted)
| | Development harness | The TAF itself |
|---|---|---|
| Wraps | the coding agent building the framework and tests | the application under test |
| Instructions | AGENTS.md, skills, agent prompts | test-case specs and oracles |
| Tools | Bash, Edit, MCP | drivers, clients, interaction objects |
| Guardrails | hooks, permissions, hygiene and architecture checks | environment allow-list, redaction, safe XML |
| Feedback loop | Stop hook → `check.py --fast` | test runs, evidence, flaky report |
| Observability | `.sdlc/traces/` | JUnit, evidence artifacts, dashboards |
| Evals | `scripts/harness_eval.py` | proof of failure, mutation testing, flake rate |

### 2.2 The spectrum (BIBLE)
| | Vibe automation | Engineered automation |
|---|---|---|
| Intent | "write tests for the login page" | risk-based suite spec, test cases with oracles |
| Verification | tests pass today | tests proven to fail on wrong behavior, stable over repeated runs |
| Failures | rerun until green | classify, fix root cause, or quarantine with expiry |
| Where | `spike/*`, `proto/*` (blocked from main) | `feat/*`, `test/*`, `fix/*`, `main` |

### 2.3 Tests and "evals" for a TAF (BIBLE concept, NEW mapping)
The paper separates deterministic checks (tests) from judgment of quality (evals). For a TAF:
- **Deterministic**: framework self-tests (unit + contract) and the automated suites' pass/fail.
- **Quality of the tests themselves** (the eval analogue): proof of failure, mutation score, flake rate, requirement/risk coverage, reviewer judgment (`test-quality-reviewer`).

### 2.4 Context engineering (BIBLE)
Static: `AGENTS.md` (stack decisions, layer rule, hard rules). Dynamic: 19 skills, loaded when a task matches (web, desktop, REST, SOAP, data, flakiness, and so on), and the claim-verified code wiki `openwiki/` (section 3A). Treat the boundary as architecture: budgeted, reviewed, versioned.

### 2.5 The factory (BIBLE)
```
HUMANS:   risk + oracles (specs) ─► ADRs + HLD/LLD approval ─► review every shipped line
FACTORY:  taf-planner ─► framework-test-writer / test-case specs ─► framework-implementer / test-author
          ─► check.py (lint, types, self-tests, architecture, hygiene) + smoke ─► reviewers ─► PR
                ▲                                          │ fail (Stop hook, CI, flaky report)
                └───────────────── failure feedback ───────┘
GUARDRAILS: secrets (incl. SOAP/URL/DSN) · test integrity (sleeps, weakened asserts, retries, ordering)
            · quality config · dependencies · fact-force · permissions · AgentShield
```

---

## 3. The runbook

| Phase | Harness role | Human owns | Agent does | Gate to exit | Kit | Source |
|---|---|---|---|---|---|---|
| 1a. Framework requirements | configure | capabilities, quality targets | capability spec with consumers, ACs, failure behavior | spec Approved | `taf-spec`, `taf-planner`, `_FRAMEWORK_CAPABILITY_TEMPLATE.md` | BIBLE + NEW |
| 1b. Suite requirements | configure | risk priorities, expected behavior | risk-scored suite spec, pyramid level per check, oracles, traceability | spec Approved | `taf-spec`, `_TEST_SUITE_TEMPLATE.md`, `docs/test-cases/` | NEW |
| 2a. Tool decisions | configure | accept ADRs | spikes on the real app, measured comparison | ADR Accepted, backlog updated | `sdlc-adr`, `DECISION_BACKLOG.md` | BIBLE + NEW |
| 2b. HLD | configure | architecture approval | layers, ports, execution, data, evidence, failure modes; `layers.toml` | HLD Approved; architecture check active | `system-design-hld`, `_HLD_TEMPLATE.md`, `design-reviewer` | BIBLE + ECC + NEW |
| 2c. LLD | configure | approve interfaces | interaction objects, Protocols, models, fixtures, waits, SOLID/simplicity check | LLD Approved; tasks carry design | `code-design-lld` (+refs), `_LLD_TEMPLATE.md` | ECC + NEW |
| 3. Contract first | feedback loop | review oracles | framework unit + contract tests; test-case oracles + proof-of-failure plan | red for the right reason (Stop hook allows a red phase when only tests changed and other fast gates pass) | `taf-contract-first`, `framework-test-writer` | BIBLE + NEW |
| 4. Implementation | running | mode, decomposition | framework code (LLD), automated tests on interaction objects | `check.py --fast` green (Stop hook); new tests stable ×3 incl. parallel | `framework-implementer`, `test-author`, platform skills, hooks | BIBLE + ECC + NEW |
| 5. Verification | feedback loop | judge effectiveness | full gates, smoke, proof of failure, flaky check | CI green; no unmanaged flakiness | `check.py`, `hygiene_check.py`, `architecture_check.py`, `flaky_report.py` | NEW |
| 6. Review | observing | every shipped line, sign-offs | code, design, test-quality, security review | CODEOWNERS approval | `automation-reviewer`, `design-reviewer`, `test-quality-reviewer`, `automation-security-reviewer` | BIBLE + ECC + NEW |
| 7. Release of framework/suites | observing | release decision | versioned framework, pipelines rolled out | `framework-readiness.md` | CI workflows | BIBLE + NEW |
| 8. Operate and maintain | observing + flywheel | quarantine decisions, product-bug calls | nightly regression ×2, triage, flaky investigation, mutation trend | incidents become tests; quarantines expire | `ci-triage`, `flaky-test-investigator`, `test-quality-and-mutation` | BIBLE + NEW |

---

## 3A. Knowledge layer: agent-maintained docs (BIBLE + NEW, skill `sdlc-wiki`)

Agents write better framework code and tests when they know which interaction objects, drivers, fixtures, and data factories already exist; without that they re-explore the repository every task and duplicate locator and request-building logic (a MEDIUM review finding). Hand-written framework docs rot. Agent-written docs have the same problem as agent-written tests: **generation is solved, verification is not**. A stale wiki is worse than none.

**Tool:** [OpenWiki](https://github.com/langchain-ai/openwiki) (LangChain, MIT, npm `openwiki`). LangChain's thesis: (1) docs for agents, not humans: one self-contained concept per page, predictable headings, cross-linked, with typed OKF v0.2 front matter so agents can *filter*; retrieval is the hard part; (2) trivial setup: one `openwiki --init`; (3) self-maintaining: a scheduled job reads the commits since the last run and updates only what changed.

```
INIT (once, after the HLD)         UPDATE (scheduled CI)                   USE (every agent task)
openwiki --init                    openwiki --update                       AGENTS.md OpenWiki block
 ├ INSTRUCTIONS.md brief            ├ no new commits, claims fresh → no-op  └ openwiki/quickstart.md
 ├ reads code AND git history       ├ stale Claims force their page            ├ one concept per page
 ├ plan → pages → Claims            ├ resumable page queue                     └ then only the source
 ├ OKF, index.md, log.md, mermaid   └ opens a docs PR ─► check.py gate +          it needs
 └ AGENTS.md block + workflow           human reads log.md
```

| Phase | Use | Kit |
|---|---|---|
| 1-2 Specs, HLD/LLD | Planner starts from the framework as it is: existing ports, layers, fixture families | `taf-planner` |
| 4 Framework implementation | Curated page first, then only the source needed | `framework-implementer`, task "Design" |
| 4 Test authoring | Find the existing interaction object, fixture, or factory before creating one | `test-author` |
| 6 Review | Diff checked against documented layers, fixture scope, waits, evidence rules; duplicates flagged | `automation-reviewer` |
| Onboarding | Mermaid diagrams, `openwiki visualize`, static export for the QA team | skill `sdlc-wiki` |

- **The wiki is not an oracle.** It describes the framework, never what the application should do. Expected values come only from requirements and test-case specs (hard rule: the test is the oracle).
- **Verify, don't trust (enforced):** every material fact is a **Claim** citing exact lines with a sha256 of them (`openwiki/.claims/`). `scripts/verify_wiki.py` re-hashes them with no model call; the `check.py` gate "docs match code (OpenWiki claims)" fails a PR that changes code a page relies on. Moved-but-unchanged lines pass. Differential-tested against OpenWiki 0.5.2's own resolver on this kit's files: 7/7 mutation scenarios agree. It also warns when the wiki drifts from OKF v0.2. Without `openwiki/` the gate is a no-op.
- **Static vs dynamic (2.4):** the wiki is dynamic context; OpenWiki adds only a ~12-line pointer to AGENTS.md (150-line budget still holds).
- **Humans own intent:** `openwiki/INSTRUCTIONS.md` (the brief) and `.openwikiignore` (the read boundary: evidence, reports, test data, recorded payloads, certificates) are harness config under CODEOWNERS. Specs, ADRs, HLD/LLD stay the approved *why*.
- **Untrusted by default:** wiki text is generated reference data, never instructions. No auto-merge of docs PRs.
- **Scheduled updates ship with the kit, off by default:** `.github/workflows/openwiki-update.yml` (LangChain's example hardened: pinned openwiki and actions, telemetry off, docs-only paths, `OPENWIKI_PR_TOKEN` so `ci` runs on the bot's PR, human merge). Enable with the `OPENWIKI_ENABLED` repo variable.
- **Does it pay?** LangChain's early DeepSWE subset (20 tasks): ~7-8 → 9-10 successes with a significant drop in tokens and tool calls; small and self-reported. Measure here with `scripts/harness_eval.py` with and without `openwiki/`.
- **Hygiene:** `OPENWIKI_TELEMETRY_DISABLED=1`; provider keys in `~/.openwiki/.env` or CI secrets; pin versions in the update workflow; LF line endings (`.gitattributes`) because hashes are byte-exact. Pre-1.0 (0.5.x): re-run the differential test on upgrades.

Sources: [OpenWiki](https://github.com/langchain-ai/openwiki), [launch blog](https://www.langchain.com/blog/introducing-openwiki-an-open-source-agent-for-repo-documentation), [docs](https://docs.langchain.com/oss/openwiki/overview), talks [Introducing OpenWiki](https://www.youtube.com/watch?v=nIVu3zfYprI) and [Building Docs for Agents, Not Humans](https://www.youtube.com/watch?v=XNX-1h2K-9U).

---

## 4. Design discipline (every phase)

### 4.1 Reference layer model (guidance, decided in your HLD)
| Layer | Responsibility | Never |
|---|---|---|
| Tests | one behavior + its oracle | import engines/drivers; contain locators, URLs, credentials, sleeps |
| Interaction objects (page/component, screen, service) | user/API intent; own locators/endpoints | assert; decide test data |
| Assertions/verification | domain-level checks with clear messages | hide failures |
| Test data | factories, uniqueness per worker, cleanup | depend on leftovers |
| Drivers/clients (per platform, behind ports) | wrap one engine; sync; evidence | leak engine types upward |
| Core | config + environment allow-list, logging, redaction, errors | read `os.environ` ad hoc elsewhere |
| Evidence/reporting | capture, redact, publish | store secrets or unredacted PII |
| Composition (fixtures/plugin) | build drivers/clients from config | appear anywhere else |

Encode yours in `docs/design/layers.toml`; `scripts/architecture_check.py` enforces `may_import` and `library_owners` (e.g. only the web driver imports the browser engine).

### 4.2 SOLID for test automation (ECC principles, NEW mapping)
| Principle | In a TAF | Enforced / proven by |
|---|---|---|
| S | Page/screen/service object changes only when its screen/API changes | design review, module size gate |
| O | New engine, browser, auth scheme, report sink = new adapter/strategy | registries/strategies in LLD |
| L | Every adapter passes the same contract tests | `@pytest.mark.contract` |
| I | Small capability Protocols (act, read, wait, call) | LLD review; easy fakes |
| D | Tests → interaction objects → ports ← adapters | `layers.toml` + architecture check |

**Balance:** no base class, plugin point, or framework layer without a present second use. God `BasePage`, deep test inheritance, and "universal frameworks" are defects.

### 4.3 Machine-enforced rules
| Rule | Where | Source |
|---|---|---|
| Complexity ≤ 8, ≤ 40 statements, ≤ 5 params, ≤ 5 returns, no magic numbers, no private access | ruff (`pyproject.toml`) | ECC + NEW |
| Modules ≤ 400 lines | `check.py` | NEW |
| Layer and library ownership | `architecture_check.py` + `layers.toml` | NEW |
| Hygiene H001–H008 (sleep, locator in test, skip reason, markers, ordering, no oracle, URL, quarantine) | `hygiene_check.py` | NEW |
| Types | `mypy --strict` | BIBLE |
| Static context budget | `check.py` | BIBLE |

---

## 5. Platform playbooks (details in skills)

| Platform | Non-negotiables | Skill |
|---|---|---|
| **Web** | stable locator strategy (test attributes → role/name → ids → scoped CSS → XPath last); condition-based waits; fresh context per test; state via API not UI; evidence (screenshot, trace, console, network) redacted; risk-based browser matrix | `web-automation` |
| **Desktop** | automation ids from developers; clean app launch and process-tree teardown; central popup watchdog; interactive unlocked Windows session with pinned DPI/resolution; serial per desktop, scale with runners; window + element-tree evidence | `desktop-automation` |
| **REST/JSON** | configured client with timeouts and TLS; service objects returning typed results; assert status + schema + business fields + side effects; negative/authz/boundary cases; redacted request/response evidence; contract drift is a defect | `api-rest-automation` |
| **XML/SOAP** | **defusedxml / hardened parsing only**; envelopes from typed models; namespaces centralized; XSD/WSDL validation; SOAP faults asserted as first-class outcomes; semantic (not string) XML comparison; WS-Security from secret store, redacted | `api-xml-soap-automation` |

---

## 6. Reliability and flakiness (NEW, with ECC loop design)
- **Detect**: nightly regression runs twice on the same commit; `scripts/flaky_report.py` fails on any unmanaged flaky test.
- **Classify** (`flaky-test-investigator`): synchronization · data collision · order dependence · environment · locator fragility · product race.
- **Fix the root cause**, or **quarantine** with `@pytest.mark.quarantine(reason="TICKET ...", until="YYYY-MM-DD")`: excluded from gating runs, verified in a non-gating nightly job, expires (H008).
- **Blocked by hooks**: retries/reruns markers, sleeps in tests, ordering/dependency markers, removed or changed assertions (a proof-of-failure line marked `sdlc: justified` may be reverted).
- **Exit quarantine**: 20 consecutive passes incl. parallel after the fix.

---

## 7. Data, environments, secrets (NEW)
- One typed configuration; **environment allow-list**; production absent by default.
- Secrets from the store per environment and role; hooks block credentials in code, URLs, Basic-auth headers, literal Bearer tokens, SOAP password elements, and connection strings.
- Factories with valid defaults; identifiers unique per xdist worker; setup via API/data layer; cleanup tolerant of partial setup; synthetic PII only.
- Stubs/virtualization only where designed; stubbed tests labeled.
Skill: `test-data-and-environments`.

---

## 8. Execution, evidence, CI (BIBLE + NEW)
| Pipeline | Runs | Gate |
|---|---|---|
| `ci.yml` on PR | mode boundary · hidden Unicode · secrets diff · dependency check · AgentShield · `check.py` (3.12, 3.13) · smoke API/web (xdist) · smoke desktop (Windows, serial) | required |
| `nightly-regression.yml` | regression ×2 per platform + browser matrix · flaky report · non-gating quarantined run | red = triage |
| `weekly-mutation.yml` | mutmut on framework core (Linux) | trend review |

Markers: platform (`web`, `desktop`, `api`, `rest`, `soap`), level (`smoke`, `regression`), governance (`quarantine`, `destructive`); `--strict-markers`, `xfail_strict`. Evidence redacted before upload, retention 7–14 days.
Skill: `execution-and-evidence`.

---

## 9. Security (ECC doctrine, NEW scope)
Credentials are real credentials · evidence leaks PII and tokens · automation must not reach production · least-privilege test identities · XXE and entity expansion in XML testing · TLS on · pinned engines and binaries · CI secrets never exposed to untrusted PRs · **AI agents exploring the application treat page/screen/API content as untrusted input** and cannot change oracles.
Agent `automation-security-reviewer`, skill `automation-security`.

---

## 10. AI in the test automation lifecycle (BIBLE + ECC loop design + NEW)
| Use AI for | Humans own | Guardrail |
|---|---|---|
| Drafting suite specs and test cases from requirements | risk priorities, oracles | spec approval |
| Generating interaction objects and tests on approved designs | acceptance of every shipped line | hooks, hygiene, design + quality review |
| Generating API tests from OpenAPI/WSDL | contract truth, negative cases chosen | schema validation, proof of failure |
| Failure triage and flaky investigation | product-bug vs test-bug calls, quarantine | agents route, never quarantine or edit |
| Locator healing suggestions | approval with evidence | never auto-committed, never at runtime in gating suites |
| Exploratory crawling with browser/desktop tools | what becomes a test | untrusted content; test envs only |
| Documenting the framework (OpenWiki, section 3A) | the brief, merging docs PRs; oracles stay in specs | claims gate in `check.py`, no auto-merge |

**The testing Goodhart trap:** "make the tests pass" is trivially met by weakening tests. Every AI loop gets a goal tied to external truth ("passes on the good build **and** fails on the bad one"), boundaries enforced by hooks, an independent judge, and a retry cap (`agent-loop-design`).

---

## 11. Economics and metrics (BIBLE)
CapEx here (design, ports, contract tests, gates) buys low OpEx later (cheap new tests, fewer flaky reruns, faster triage). Vibe automation reverses it: fast first tests, then a maintenance tax that can kill the suite.

| Metric | Why |
|---|---|
| Flake rate and quarantine count/age | reliability; trust in red |
| Smoke/regression duration (p50/p95) | feedback speed |
| Time from failure to classified root cause | diagnosability |
| High-risk requirement coverage | protection where it matters |
| Proof-of-failure rate for new tests; mutation score trend (core) | test effectiveness |
| Tests changed per UI change | maintainability (should be ~1 interaction object) |
| Token cost per merged task; reviewer findings per PR | AI economics and gate value |
| Harness-eval pass rate and cost with vs without `openwiki/` | whether the code wiki pays for itself |

Model routing: opus for planning, design review, framework implementation, security; sonnet for test authoring, test-quality review, flaky investigation; haiku for framework test writing, first-pass review, CI triage.

---

## 12. When the agent gets it wrong (BIBLE)
Most failures are harness failures. Use `sdlc-harness-fix`: identify the missing instruction, enforcement, layer rule, oracle, or boundary; fix at the cheapest reliable layer (hook/check > AGENTS.md line > skill); add a Lesson and a test that reproduces it.

---

## 13. Playbooks (BIBLE, tailored)
**Individual engineer**
- [ ] Spec and oracle before automation; proof of failure for every new test.
- [ ] Interaction objects, not locators in tests; waits on conditions.
- [ ] Run new tests ×3 incl. parallel before PR.
- [ ] Keep manual exploratory and debugging skills sharp; AI drafts, you judge.

**QA / test-automation lead**
- [ ] Harness, designs, and layers.toml owned via CODEOWNERS.
- [ ] Set the bar at reliability and effectiveness (flake rate, proof of failure), not test count.
- [ ] Enforce the exploration/engineering branch boundary.
- [ ] Review AI-generated tests for oracle strength; track quarantine age.

**Organization**
- [ ] Treat the TAF as a product: roadmap, owners, versioning, readiness checklist.
- [ ] Invest in environments, test data, Windows desktop runners, and evidence storage before scaling suites.
- [ ] Testability requirements for product teams (test ids, automation ids, API contracts, seedable data).
- [ ] Hybrid human/agent teams with task files as the handoff protocol; humans own oracles and releases.

---

## 14. Keeping it alive
Review quarterly: tool ADRs (engines evolve), flake and duration trends, quarantine age, hygiene rules that produce noise, AgentShield on `.claude/`. Replace tools freely behind ports; keep the creed.

---

## Appendix: kit map
| Path | What | Source |
|---|---|---|
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | static context: stack decisions, layer rule, test conventions, hard rules | BIBLE + NEW |
| `.claude/settings.json` | hooks, permissions (incl. certificate files, production data), env | BIBLE + ECC |
| `.claude/hooks/lib/secrets_guard.py` | credentials incl. URL creds, Basic auth, Bearer tokens, SOAP passwords, DSNs | BIBLE + ECC + NEW |
| `.claude/hooks/lib/test_guard.py` | blocks sleeps in tests and removed or changed assertions | NEW |
| `.claude/hooks/lib/quality_guard.py` | gate config protection; noqa/ignore/skip; retries/flaky; ordering markers | ECC + NEW |
| `.claude/hooks/lib/bypass_guard.py`, `deps_guard.py`, `fact_force.py` | hook bypass, package slopsquatting, investigate-before-edit (+ layer questions) | ECC + NEW |
| `.claude/hooks/{pre_tool,post_tool,stop,scan}.py` | dispatch, trace + ruff, gate loop, CI scans | BIBLE + ECC |
| `.claude/agents/` | taf-planner, design-reviewer, framework-implementer, framework-test-writer, test-author, automation-reviewer, test-quality-reviewer, automation-security-reviewer, flaky-test-investigator, ci-triage | BIBLE + ECC + NEW |
| `.claude/skills/` (19) | taf-spec, sdlc-wiki, system-design-hld, sdlc-adr, code-design-lld (+SOLID, patterns refs), taf-contract-first, sdlc-delegate, automation-review, sdlc-harness-fix, web-automation, desktop-automation, api-rest-automation, api-xml-soap-automation, test-data-and-environments, execution-and-evidence, flaky-test-management, test-quality-and-mutation, automation-security, agent-loop-design | BIBLE + ECC + NEW |
| `scripts/check.py` | all gates | BIBLE + NEW |
| `scripts/architecture_check.py` | layer + library ownership from `layers.toml` | NEW |
| `scripts/hygiene_check.py` | test hygiene H001–H008 | NEW |
| `scripts/flaky_report.py` | flaky detection from repeated JUnit runs (safe XML) | NEW |
| `scripts/verify_deps.py`, `scripts/harness_eval.py` | dependency verification; coding-harness evals | BIBLE |
| `scripts/verify_wiki.py` | OpenWiki claims must match cited code; OKF v0.2 warnings (gate in `check.py`) | BIBLE + NEW |
| `openwiki/` (generated) | agent-maintained, claim-grounded framework wiki (section 3A) | BIBLE + NEW |
| `docs/FEATURE_WALKTHROUGH.md` | one feature from an empty kit to a merged PR: every step, back-and-forth, hook, gate, and enforcement gap | BIBLE + ECC + NEW |
| `docs/specs/` | framework capability and test-suite spec templates | NEW |
| `docs/test-cases/_TEMPLATE.md` | test case with oracle and proof of failure | NEW |
| `docs/design/` | HLD, LLD templates; `_layers.example.toml` | BIBLE + NEW |
| `docs/adr/` | ADR template; decision backlog D-01…D-12 | BIBLE + NEW |
| `docs/tasks/_TEMPLATE.md` | agent task with design and must-NOT list | BIBLE + NEW |
| `docs/checklists/` | automation code review, design review, framework readiness | NEW |
| `.github/workflows/` | ci, nightly-regression, weekly-mutation, openwiki-update (off until `OPENWIKI_ENABLED=true`) | BIBLE + NEW |
| `.pre-commit-config.yaml`, CODEOWNERS, PR template, dependabot | governance | BIBLE + ECC + NEW |
| `evals/harness_cases.jsonl` | does the harness steer agents correctly | BIBLE + NEW |
| `.claude/hooks/tests/`, `scripts/tests/` | self-tests of the harness | NEW |
