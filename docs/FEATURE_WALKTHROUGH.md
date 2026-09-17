# From zero to a merged feature: a step-by-step walkthrough

This document follows **one feature** from an **empty copy of this kit** to a merged pull request and its
first nightly run. Every step names what you type, what Claude does, which file, agent, skill, hook or gate is
involved, the back-and-forth you should expect, and where each practice comes from.

**Example feature:** "The framework must support the Order API: create an order and read its status over REST."

Everything about the kit's behavior below was checked against the kit's source files. Things that depend on
your environment (applications, tool choices, numbers, dialogue) are **examples** and are marked as such.

---

## Legend

**Where a practice comes from**

| Label | Meaning |
|---|---|
| **AI-SDLC** | From *The New SDLC With Vibe Coding* via the AI-SDLC bible (labelled `BIBLE` inside `BIBLE.md`) |
| **ECC** | Harness hardening adapted from the ECC repository |
| **NEW** | Built specifically for test automation in this kit |

**How strongly a rule is enforced**

| Kind | Meaning | Can Claude get past it? |
|---|---|---|
| **HOOK** | Code in `.claude/hooks/` runs before or after a Claude tool call and can block it (exit code 2) | No, not without a human changing the hook |
| **GATE** | A script (`scripts/check.py` and friends) fails locally, in git hooks, or in CI | Only by fixing the cause; weakening the gate is itself hook-blocked |
| **PROMPT** | An instruction in `AGENTS.md`, an agent file, or a skill | Yes. The model is told, not forced. Review catches misses |
| **HUMAN** | Only a person does it; nothing automated checks it was done | Yes, if the human skips it |
| **CI** | A GitHub Actions job in `.github/workflows/` | Only if branch protection doesn't require the job |

---

## Part 0: What "zero" means

**Exists in the kit**

| Thing | Path |
|---|---|
| Doctrine and runbook | `BIBLE.md` |
| Instructions Claude reads on every turn | `AGENTS.md` (loaded through `CLAUDE.md`) |
| Hook wiring, permissions, harness settings | `.claude/settings.json` |
| Hooks | `.claude/hooks/pre_tool.py`, `post_tool.py`, `stop.py`, `scan.py`, `lib/*.py` |
| 10 agents, 18 skills | `.claude/agents/`, `.claude/skills/` |
| Templates | `docs/specs/`, `docs/test-cases/`, `docs/design/`, `docs/adr/`, `docs/tasks/`, `docs/checklists/` |
| Gate scripts | `scripts/check.py`, `architecture_check.py`, `hygiene_check.py`, `flaky_report.py`, `verify_deps.py`, `harness_eval.py` |
| Git hooks config | `.pre-commit-config.yaml` |
| CI | `.github/workflows/ci.yml`, `nightly-regression.yml`, `weekly-mutation.yml` |

**Does not exist yet**

- `src/` (no framework code) and `tests/` (no automated tests)
- `docs/design/layers.toml`, so the architecture check prints `SKIP` and passes
- Any spec, ADR, HLD, LLD or task: only `_TEMPLATE` files
- Any tool decision: every row in `docs/adr/DECISION_BACKLOG.md` is `Open`; every `Stack` line in `AGENTS.md` is `TODO`
- Any engine library (browser, desktop, HTTP, SOAP client): the only runtime dependency is `defusedxml`
- Real owners in `.github/CODEOWNERS` (placeholders `@your-org/...`)
- GitHub settings: branch protection, the `test` environment, secrets, runners

---

## Part 1: One-time setup (you, no Claude yet)

### 1.1 Install the tools
- **git**
- **Python 3.12+**, callable as `python`. The hooks run `python "$CLAUDE_PROJECT_DIR/.claude/hooks/..."`, so if
  `python` is not on your PATH, no hook runs.
- **uv**, used for every project command.
- **Claude Code**
- **Node.js 22** (optional locally). Only needed to run AgentShield yourself; CI installs it.

### 1.2 Get the kit and install the dev tools
```bash
git clone <your copy of this repo> taf && cd taf
uv sync
```
`uv sync` creates `.venv/` from `uv.lock`: pytest, pytest-xdist, pytest-cov, ruff, mypy, pip-audit, pre-commit,
mutmut, and types-defusedxml.

### 1.3 Prove the gates are green on the empty kit
```bash
uv run python scripts/check.py
```
Expected: every line `[PASS]`, then `All gates passed.`
- `architecture rules` passes because the script prints `SKIP: docs/design/layers.toml not found`.
- `test hygiene` passes because it prints `SKIP: no test paths found yet.`
- `framework self-tests + coverage` runs the kit's own tests (`scripts/tests/`, `.claude/hooks/tests/`).
- `vulnerable dependencies` (pip-audit) needs internet access.

**GATE · AI-SDLC + NEW**

### 1.4 Install the git hooks
```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

| Hook stage | What runs | Source |
|---|---|---|
| Every `git commit` | ruff check/format, file-hygiene hooks (large files > 500 KB, merge conflicts, toml/yaml/xml/json syntax, private keys, end-of-file, trailing whitespace), staged-secrets scan, hidden-Unicode scan, `hygiene_check.py`, `architecture_check.py` | AI-SDLC + ECC + NEW |
| Every `git push` | full `scripts/check.py` | AI-SDLC + NEW |

**GATE**

### 1.5 (Optional) Stop your personal global rules from loading here
If you keep personal rules in `~/.claude/rules/`, Claude Code loads them in this repo too, and some conflict
with the kit (for example black/isort instead of ruff). Create `.claude/settings.local.json` (gitignored):
```json
{
  "claudeMdExcludes": [
    "C:/Users/<you>/.claude/rules/**",
    "**/Users/<you>/.claude/rules/**"
  ]
}
```
**HUMAN**

### 1.6 GitHub settings (you or a repo admin)

| Setting | Why | Source |
|---|---|---|
| Branch protection on `main` requiring jobs `mode-boundary`, `harness`, `quality (3.12)`, `quality (3.13)`, `smoke-api-web`, `smoke-desktop` | CI only protects `main` if its jobs are required | AI-SDLC |
| Environment named `test` holding test-only secrets | the smoke and nightly jobs declare `environment: test` | NEW |
| Replace `@your-org/...` in `.github/CODEOWNERS` | harness, design, and ADR changes need named reviewers | AI-SDLC + ECC |
| Decide how CI reaches your test environments (GitHub-hosted or self-hosted runners) | a GitHub-hosted runner cannot reach a private network | NEW |

**HUMAN**

---

## Part 2: Opening Claude Code

```bash
git switch -c feat/order-api-design
claude
```

**What loads automatically, in order**

1. `CLAUDE.md` loads, which imports `AGENTS.md`: what the project is, the layer rule, test conventions, hard
   rules, the branch-mode table, and the workflow. **PROMPT · AI-SDLC + NEW**
2. `.claude/settings.json` loads, in a trusted folder:
   - **env:** `SDLC_MAX_FIX_ATTEMPTS=3`, `SDLC_FACT_FORCE=1`, `SDLC_FACT_FORCE_PATHS=src/`, `SDLC_MIN_PACKAGE_AGE_DAYS=30`
   - **permissions allow** (no prompt): `uv run pytest`, `uv run --no-sync` for pytest/ruff/mypy and the check
     scripts, and `git status`, `git diff`, `git log`. Anything else asks you first in the default permission mode.
   - **permissions deny:** reading `.env*`, `secrets/**`, `test-data/production/**`, `*.pfx` and `*.p12`;
     `git push --force`, `git reset --hard`, `git commit --no-verify`; `sudo`, `ssh`, `scp`, `uv publish`, and more.
   - **hooks:** `pre_tool.py` before Bash, PowerShell, Write, Edit and MultiEdit; `post_tool.py` after every tool;
     `stop.py` when Claude tries to finish a turn.

   **HOOK · AI-SDLC + ECC**
3. The names and descriptions of the 18 skills and 10 agents load. Their full text loads only when used.
   **AI-SDLC** (static vs dynamic context)

**Check it yourself:** type `/hooks` to see the three registered hooks and `/agents` to see the ten agents.

**How to make Claude use a specific skill or agent:** Claude picks skills and agents by matching their
descriptions, which usually works. **Naming them in your message is the reliable way**, e.g. "Use the
`taf-spec` skill" or "Use the `taf-planner` agent". This walkthrough always names them.

**Mode:** `AGENTS.md` says `feat/*` means Engineering mode. The **hooks behave the same on every branch**. The
only thing that checks the branch is the CI job `mode-boundary`, which fails a PR from `proto/*` or `spike/*`
into `main`. **PROMPT + CI · AI-SDLC**

**The Stop hook runs after every turn that leaves changes.** When Claude tries to end a turn, `stop.py` runs
`git status --porcelain`.
- If nothing changed, it does nothing.
- If anything changed (even a Markdown file), it runs `uv run --no-sync python scripts/check.py --fast`: ruff,
  mypy, unit/contract self-tests with `-x`, the architecture check, and the hygiene check.
- If that fails, Claude is not allowed to stop and gets the failure output (attempt 1/3, 2/3, 3/3).
- **Exception, the red phase:** if the only changed Python files are test code and
  `check.py --red-phase` (every fast gate except the self-tests) passes, Claude may stop. You see
  "Red phase: framework self-tests are failing, only test files changed…". This does not use up a fix attempt.
- After 3 failed attempts it lets Claude stop with: "Quality gates still failing after 3 automatic fix
  attempts. Human needed…"

**HOOK · AI-SDLC** (feedback loop) + **ECC** (retry cap)

---

## Step 1: First request, when nothing exists yet

**You type**
> I want the framework to support the Order API: create an order and get its status over REST. Use the
> `taf-planner` agent to tell me what has to happen first.

**What happens, in order**

1. The main Claude session starts the `taf-planner` agent (model opus). **ECC** (model routing) + **NEW**
   - Its tools are Read, Grep, Glob, Write and WebFetch; it has no Bash.
   - Its instructions say to write only under `docs/`. **PROMPT**
2. `taf-planner` reads `AGENTS.md` (all Stack lines `TODO`), `docs/adr/DECISION_BACKLOG.md` (all `Open`),
   `docs/specs/` (templates only) and `docs/design/` (templates only, no `layers.toml`). It finds no `src/` or `tests/`.
3. It returns a plan instead of code, because its instructions say to use specs, ADRs and design before
   implementation. **PROMPT · AI-SDLC**

**Example reply from Claude**
> Nothing is built yet. Before any Order API code:
> 1. Framework capability spec: REST API support (`taf-spec`).
> 2. Test-suite spec for the Order API, plus test cases with oracles (`taf-spec`, `docs/test-cases/`).
> 3. ADRs that block REST work: D-03 REST client, D-05 contract/schema validation, D-06 reporting and
>    evidence, D-09 configuration and secrets, D-10 repository and packaging layout. D-07 parallel execution
>    and D-08 test data also affect this feature.
> 4. HLD plus `docs/design/layers.toml` (`system-design-hld`), reviewed by `design-reviewer`.
> 5. LLD for the REST client, Order service object, models, data factory, assertions and fixtures.
> 6. Tasks, then tests first, then implementation.
>
> `BIBLE.md` §0 recommends a walking skeleton with one web, one desktop, one REST and one SOAP path.
> Decisions I need from you:
> (a) walking-skeleton scope;
> (b) where the Order API contract (OpenAPI) is;
> (c) which test environment and host;
> (d) who owns expected behavior (oracles).

**Stop hook:** nothing was written, so `git status --porcelain` is empty and no gates run.

**Back-and-forth**
- **Round 2, you:**
  > (a) First slice is REST Order API only. The HLD must still cover web, desktop and SOAP, but their ADRs come later.
  > (b) I'll add the OpenAPI file at `docs/external/order-api.yaml`.
  > (c) Environment `test`, host `orders.test.example.internal`.
  > (d) I own the oracles.

  Choosing a REST-only first slice **departs from the kit's default** (all four platforms). That is your call,
  and it gets written into the capability spec's "Out of scope" section. **HUMAN · AI-SDLC**
- **Round 3, you** add `docs/external/order-api.yaml` yourself. Claude's WebFetch cannot reach an internal host,
  and nothing in the kit fetches contracts for you. **HUMAN**

---

## Step 2: Framework capability spec

**You type**
> Use the `taf-spec` skill. Write the framework capability spec for REST API support, with the Order API as
> the first consumer.

**What happens, in order**

1. The `taf-spec` skill loads (section A, framework capability spec). **AI-SDLC + NEW**
2. Claude copies `docs/specs/_FRAMEWORK_CAPABILITY_TEMPLATE.md` to `docs/specs/rest-api-support.md` and fills:
   - Status `Draft`
   - Problem and consumers
   - Intended usage: a sketch of test code at interaction level, with no HTTP calls
   - Acceptance criteria `AC-n`
   - Variants in scope
   - Quality attributes table
   - Failure behavior table
   - Design ("HLD required? yes": new platform)
   - Out of scope ("web, desktop, SOAP: later slices")
   - Open questions
3. Claude ends its turn, and the Stop hook fires: a new file exists, so `check.py --fast` runs. No Python
   changed, so it passes and Claude stops. **HOOK**

**Example acceptance criteria (first draft)**
- AC-1: a service object creates an order and returns a typed result exposing status code, headers and parsed body.
- AC-2: a failed API test attaches the request and response to the report, with sensitive fields redacted.
- AC-3: the base URL comes from environment configuration; an unknown environment fails fast.
- AC-4: TLS verification is on.

**Example open questions from Claude**
1. Authentication scheme and where credentials come from?
2. Timeouts (connect, read)?
3. Which fields must be redacted?

**Back-and-forth**
- **Round 2, you:**
  > OAuth2 client credentials. The token endpoint is in environment config. Client id and secret come from
  > CI secret `TAF_ORDERS_CLIENT_SECRET` and your shell locally. Timeouts: connect 10 s, read 30 s. Redact
  > `Authorization`, `Set-Cookie`, `access_token`, `customer.email`, `customer.phone`.
- **Round 3, Claude** updates the spec. Suppose it adds an example config line with a realistic-looking secret
  value. The `pre_tool.py` hook **blocks the Write**. **HOOK · AI-SDLC + ECC + NEW**
  - Guard: `secrets_guard`, pattern "hard-coded credential", which matches a key containing
    password/secret/token/api_key with a quoted value of 8+ characters that isn't a placeholder.
  - Claude sees: `BLOCKED: possible hard-coded credential in this Write call. Test credentials are real credentials: read them from the environment or the secret manager ...`
  - Claude rewrites the line as `client_secret = "${TAF_ORDERS_CLIENT_SECRET}"`. The placeholder form `${...}`
    is allowed, and the write goes through.
  - This guard scans **every file Claude writes**, including Markdown.
- **Round 4, you:** "AC-3 is not binary. What exactly happens?"
  **Claude:** "AC-3: before any request is sent, the framework raises `EnvironmentNotAllowedError` naming the
  requested host and the allowed hosts for the selected environment."
- **Round 5, you:** "Approved." You change `Status: Draft` to `Status: Approved`, or ask Claude to.

**Done when:** the spec status is `Approved` and no open questions remain.
- **HUMAN.** No hook or gate checks the status line.
- `docs/specs/` has **no CODEOWNERS entry** in the kit, so only the PR reviewer protects it.

---

## Step 3: Test-suite spec and test cases

**You type**
> Use the `taf-spec` skill. Write the test-suite spec for the Order API and one test-case file per scenario.

**What happens, in order**

1. `taf-spec` loads (section B, test-suite spec). **NEW**
2. Claude writes `docs/specs/order-api-tests.md` from `_TEST_SUITE_TEMPLATE.md` (example content):

   | Requirement / risk | Impact | Likelihood | Score | Level | Why that level |
   |---|---|---|---|---|---|
   | REQ-ORD-1 create order | 5 | 3 | 15 | api | server behavior; no UI needed |
   | REQ-ORD-3 new order status | 5 | 2 | 10 | api | state is visible through the API |
   | REQ-ORD-7 invalid payload rejected (400) | 4 | 3 | 12 | api | error body is part of the contract |
   | REQ-ORD-9 unauthenticated (401) / wrong role (403) | 5 | 2 | 10 | api | security |
   | REQ-ORD-12 order total rounding | 5 | 3 | 15 | api | calculated server-side |

   It also fills scenarios with oracles, negative paths, data and environments, execution (smoke vs regression),
   traceability, exit criteria and open questions.
3. It writes `docs/test-cases/TC-ORD-001.md` … `TC-ORD-005.md` from `docs/test-cases/_TEMPLATE.md`: preconditions
   and data, steps at API-intent level, **oracle**, a **proof-of-failure** section (filled later), and automation notes.
4. The Stop hook runs `check.py --fast`; it passes.

**Back-and-forth**
- **Round 1, Claude's open questions:**
  1. Can tests delete orders, or is there a cleanup job?
  2. What is the rounding rule for totals?
  3. Is a new order always `PENDING`?
- **Round 2, you:**
  > No DELETE endpoint; the test environment purges orders tagged `source=automation` every night.
  > Round half-up to 2 decimals (REQ-ORD-12). Always `PENDING` (REQ-ORD-3).
- **Round 3, Claude** updates the data section: tag every created order `source=automation`; references unique
  per worker; no teardown delete. It flags the risk that orders pile up during the day. You accept the risk.
- **Round 4, you challenge a weak oracle.** Claude's first draft of TC-ORD-001 said "201 and body not empty".
  > That oracle can't catch a wrong order. Make it concrete.

  **Claude** rewrites it. This is `taf-spec` and `taf-contract-first` guidance ("the oracle is concrete"). **PROMPT · NEW**
  - status 201
  - `Location` header ends with `/orders/{id}`
  - body valid against the OpenAPI schema
  - `status == "PENDING"`
  - `total == 59.97` for the three example lines
  - a follow-up GET returns the same order
  - must NOT happen: a second order for the same idempotency key
- **Round 5, you:** "Approved." Both files are now `Approved`.

**Done when:** the suite spec and test cases are `Approved`. **HUMAN**

---

## Step 4: Tool decisions (ADRs with spikes)

This step shows **D-03 (REST client)** in full; the other blocking decisions follow the same loop.

**You type**
> Use the `sdlc-adr` skill for D-03, the REST client. Compare httpx and requests (example options) with a
> spike against the test environment.

**Numbering:** the skill numbers ADRs as the highest existing `docs/adr/NNNN-*.md` plus one, so the first is
`0001`; `_TEMPLATE.md` and `DECISION_BACKLOG.md` don't count. HLD and LLD files in `docs/design/` are numbered
the same way. **PROMPT · AI-SDLC**

**What happens, in order**

1. **Spike branch.** Claude runs `git switch -c spike/rest-client`. `git switch` is not in the allow list, so
   Claude Code asks you. The skill says spikes go on `spike/*`. **PROMPT · NEW**
2. **Add candidate libraries.** Claude runs `uv add httpx` and `uv add requests`, and you approve each prompt.
   - `pre_tool.py` runs `deps_guard` first.
     - It asks PyPI whether each package exists and was first published at least 30 days ago
       (`SDLC_MIN_PACKAGE_AGE_DAYS`).
     - It **fails closed**: if PyPI can't be reached, the install is blocked.
   - Both packages pass.
   - If Claude had typed a name that doesn't exist, it would see
     `BLOCKED dependency install: <name>: does not exist on PyPI (hallucinated or misspelled?)`.
   - To approve a brand-new internal package, a human adds it to `SDLC_ALLOW_PACKAGES`.

   **HOOK · ECC**
3. **Credentials for the spike.** Claude cannot read `.env` (permission deny). Before starting `claude`, you
   export `TAF_ENV=test` and `TAF_ORDERS_CLIENT_SECRET=...` in your shell; commands Claude runs inherit them.
   **HUMAN · NEW**
4. **Spike code.** Claude writes throwaway scripts on the spike branch, e.g. `spikes/rest_client/`.
   - `fact_force` does **not** fire, because only `.py` files under `SDLC_FACT_FORCE_PATHS` (default `src/`) are gated.
   - `post_tool.py` still runs ruff on every edited `.py` file.
     - It logs a trace line to `.sdlc/traces/<session>.jsonl`, masking known token formats (AWS, GitHub, LLM,
       Google, Slack keys, private keys).
     - If ruff finds something it can't auto-fix, Claude gets the findings back and must fix them before continuing.

   **HOOK · AI-SDLC + ECC**
5. **Measure.** Claude runs the same "create order, then get status" flow many times with each library, in
   parallel with xdist. It records stability, duration, how redaction hooks and timeouts work, and typing
   quality. The numbers come from **your** environment.
6. **Write the ADR.** Claude writes `docs/adr/0001-rest-client.md` from `_TEMPLATE.md` with `Status: Proposed`:
   - context
   - options with measured spike results
   - decision as a trade-off
   - consequences
   - design principles impact: "only the `api_clients` layer imports the HTTP library; enforced by
     `library_owners` in `layers.toml`"
   - rules for future changes

   **AI-SDLC + NEW**

**Back-and-forth**
- **Round 2, you:** "20 runs is too few. Run 50 and add p95 duration." Claude reruns and updates the table.
- **Round 3, you:** "Accepted: httpx." The skill's step 7 has Claude:
  - set the ADR status to `Accepted`. Only your statement makes this change; the skill says a human accepts.
    **PROMPT + HUMAN**
  - change the `AGENTS.md` Stack line to `REST client: httpx (ADR-0001)`
  - set backlog row D-03 to `Decided (ADR-0001)`
  - note that `layers.toml` doesn't exist yet, so the ownership rule goes in during Step 5
- **Round 4, cleanup:** the spike branch is never merged. Claude switches back to `feat/order-api-design` and
  brings over **only** the ADR, `AGENTS.md` and backlog changes. `requests` never reaches the design branch.
  `httpx` is added again on the implementation branch in Step 9.

**The other blocking decisions** run the same loop and produce `docs/adr/0002-…` through `0005-…`:

| Backlog item | Question for this slice |
|---|---|
| D-05 | How responses are validated against the OpenAPI contract |
| D-06 | Where evidence and reports go; retention |
| D-09 | Configuration format, secret source, environment allow-list |
| D-10 | Package layout (e.g. `src/taf/`), and whether the framework is an installable package |

You can **defer** D-07 and D-08: their backlog rows stay `Open`, and the suite spec already covers data for this slice.

**Done when:** every ADR this slice needs is `Accepted`. **HUMAN**

---

## Step 5: HLD and `layers.toml`

**You type**
> Use the `system-design-hld` skill. Write the framework HLD for all four platforms. Only the REST path is
> decided; mark the rest as pending their ADRs.

**What happens, in order**

1. Claude writes `docs/design/0001-framework-hld.md` from `_HLD_TEMPLATE.md`:
   - context and goals
   - measurable quality attributes
   - context diagram
   - layers and responsibilities table
   - ports and adapters (`HttpPort` for REST now; web, desktop and SOAP ports marked pending D-01, D-02, D-04)
   - composition and configuration (environment allow-list)
   - execution model, test data, evidence and reporting, key flows, failure modes, ADR links, risks

   **AI-SDLC + ECC + NEW**
2. Claude copies `docs/design/_layers.example.toml` to **`docs/design/layers.toml`** and adapts it to the
   HLD's layers (e.g. `tests`, `services`, `api_clients`, `ports`, `models`, `assertions`, `data`, `evidence`,
   `config` under `src/taf/`), keeping `httpx = ["api_clients"]`.
3. **From this moment `architecture_check.py` enforces the rules** on every `.py` file outside `.venv/`,
   `.claude/` and `scripts/`, in the Stop hook, pre-commit, pre-push and CI. No framework code exists yet, so it
   reports `0 architecture violation(s)`. **GATE · NEW**

**Back-and-forth**
- **Round 2, you:** "Run the `design-reviewer` agent on the HLD."
  - `design-reviewer` (opus) is independent: its instructions forbid editing what it reviews.
    **PROMPT · AI-SDLC + ECC**
  - It reads `docs/design/`, the ADRs, and `docs/checklists/design-review.md`.

  **Example verdict:** APPROVE WITH CONDITIONS
  - HIGH `docs/design/layers.toml`: `data` may import `services`, but HLD §4 says `data` imports only
    `models` and `config`. Decide which is true and make both files match.
  - MEDIUM `docs/design/0001-framework-hld.md` §11: no failure mode for "token endpoint unavailable".
- **Round 3, you:** "Factories create orders through the Order service, so `data` may import `services`. Add
  the token failure mode." Claude fixes both files.
- **Round 4, you:** "Run `automation-security-reviewer` on the HLD." The HLD template's sign-off list includes it.
  **Example finding:**
  - HIGH §6: the allow-list check must run before the first request, including the token request.

  Claude fixes it.
- **Round 5, you:** tick the sign-off boxes and set `Status: Approved`. **HUMAN**

**Harness configuration after the HLD** (from the `BIBLE.md` §0 checklist)

| Change | Who can make it | Why |
|---|---|---|
| `.claude/settings.json`: `SDLC_FACT_FORCE_PATHS` → `src/taf/` (or keep `src/`) | Claude or you | Not blocked by a hook; CODEOWNERS `/.claude/` reviews it |
| `pyproject.toml` `[tool.mypy] files` → add `src/taf`; if `taf` isn't installed as a package, also `mypy_path` so mypy resolves `taf` | **You only** | `quality_guard` **blocks Claude**: `BLOCKED: this edit changes [tool.mypy] in pyproject.toml ... quality-gate settings need a human-approved PR.` **HOOK · ECC** |
| `pyproject.toml` `[tool.pytest.ini_options] pythonpath = ["src"]`, needed if ADR D-10 keeps `[tool.uv] package = false` | **You only** | Same guard, `[tool.pytest]` section |
| Or: make `taf` an installable package (`[tool.uv] package = true` plus `[build-system]`), if D-10 chose that | Claude or you | Those sections aren't quality-gate sections, so no block |
| `pyproject.toml` `[tool.mutmut]` for framework core | Claude or you | Not a protected section; `weekly-mutation.yml` skips until it exists |
| `.github/CODEOWNERS`: uncomment `/src/<framework>/` and `/tests/` with real teams | You | Ownership is a human decision |
| `AGENTS.md`: fill "TODO (HLD): framework root package, layer names, fixture layout" | Claude or you | Must stay ≤ 150 lines (`check.py` static context budget) **GATE · AI-SDLC** |

---

## Step 6: LLD

**You type**
> Use the `code-design-lld` skill. Write the LLD for the REST client adapter, the Order service object,
> models, the order data factory, order assertions and the fixtures.

**What happens, in order**

Claude writes `docs/design/0002-order-api-lld.md` from `_LLD_TEMPLATE.md` (example content). **ECC + NEW**

| Section | Example content |
|---|---|
| 2. Module map | `src/taf/config/settings.py` (config) · `src/taf/ports/http.py` (ports) · `src/taf/api/clients/http_client.py` (api_clients) · `src/taf/models/order.py` (models) · `src/taf/api/services/order_service.py` (services) · `src/taf/data/order_factory.py` (data) · `src/taf/assertions/order_assertions.py` (assertions) · `tests/conftest.py` fixtures |
| 3. Public interfaces | `HttpPort` Protocol with `send(request) -> HttpResponse`; `OrderService.create(new_order) -> ApiResult[Order]`, `OrderService.get(order_id) -> ApiResult[Order]` |
| 4. Models | frozen dataclasses `NewOrder`, `Order`, `Money`; invariant: total = sum of line totals, rounded half-up to 2 decimals |
| 5. Fixtures | `settings` (session), `http_client` (session; with xdist every worker is its own process, so this is per worker), `order_service` (function), `order_factory` (function; references include worker id and a UUID) |
| 6. Sync, errors, evidence | GET-after-create waits on a condition via a framework `wait_until(condition, timeout)`; 4xx/5xx returned as results, not raised; transport errors raised with request context; redacted request/response attached on failure |
| 8. SOLID check | S: service object knows only order endpoints · O: auth scheme is a strategy · L: every `HttpPort` adapter passes the contract tests · I: `HttpPort` has one method · D: services depend on `HttpPort`, not httpx |
| 9. Simplicity check | `HttpPort` with one real adapter is justified as a **test seam** (fake in unit tests) and a **volatile engine boundary**; no `BaseService` |
| 10. Tests | unit tests with a fake `HttpPort`; `@pytest.mark.contract` tests parametrized over adapters |

**Back-and-forth**
- **Round 1, `design-reviewer`** on Claude's first draft:
  - MEDIUM over-design: `BaseService` with generic CRUD and a single subclass; inline it into `OrderService`.
    ("Simplicity is a design rule" in `AGENTS.md`.)
  - HIGH parallel safety: `http_client` caches an OAuth token and refreshes it; state that session scope means
    per xdist worker process and that no state is shared across workers.

  Claude fixes both.
- **Round 2, you:** "Why does `create` return `ApiResult` instead of raising on 400?"
  **Claude**, quoting the `api-rest-automation` skill: negative tests must assert status and error body, so
  service objects return a result exposing status, headers and body. You accept.
- **Round 3, you:** sign off. `Status: Approved`. **HUMAN**

### Design PR (the kit doesn't prescribe PR size; this walkthrough uses a design-only PR first)

**What's in it:** specs, test cases, ADRs, HLD, `layers.toml`, LLD, and your harness config edits.

1. Claude runs `git add` and `git commit`; Claude Code asks you to approve each.
   - `pre_tool.py` checks the commit command:
     - `bypass_guard` blocks `--no-verify`, `-n`, `SKIP=`, `core.hooksPath` overrides.
     - `secrets_guard` scans the command **and** all pending changes, including untracked files.

     **HOOK · ECC + AI-SDLC**
   - git's pre-commit hooks run (Part 1.4). If `end-of-file-fixer` or `trailing-whitespace` modifies a file,
     the commit stops; Claude stages the fixed files and commits again. **GATE**
2. `git push -u origin feat/order-api-design` (you approve the prompt) triggers the pre-push hook: full
   `check.py`. **GATE**
3. Claude runs `gh pr create` and fills `.github/pull_request_template.md` (kind: design docs; mode:
   engineering; design-reviewer verdict).
4. **CI (`ci.yml`)**
   - `mode-boundary` passes (`feat/*`).
   - `harness`: hidden Unicode, secrets in the branch diff, `verify_deps.py`, AgentShield on `.claude/`.
   - `quality` on Python 3.12 and 3.13 runs full `check.py`.
   - `smoke-api-web` and `smoke-desktop` find no tests (pytest exit 5) and pass with a warning.

   **CI · AI-SDLC + ECC + NEW**
5. **CODEOWNERS** requests test-architects (`docs/design/`, `docs/adr/`) and harness-owners (`AGENTS.md`,
   `.claude/`, `pyproject.toml`). Humans review and merge. **HUMAN**

---

## Step 7: Tasks

```bash
git switch main && git pull && git switch -c feat/order-api
```

**You type**
> Use the `sdlc-delegate` skill. Break the Order API LLD into task files.

**What happens, in order**

Claude writes `docs/tasks/ORD-01.md` … `ORD-05.md` from `docs/tasks/_TEMPLATE.md`. Each has goal, design,
done-when (binary), a **Must NOT** list (no removed assertions, sleeps, retries, skip/xfail, locators, URLs,
credentials in tests, no quality config edits), and files in scope. **AI-SDLC + NEW**

| Task | Goal | Agent | Mode |
|---|---|---|---|
| ORD-01 | configuration, environment allow-list, errors | framework-implementer | conductor (first design of a cross-cutting piece) |
| ORD-02 | `HttpPort`, httpx adapter, OAuth, redaction | framework-implementer | conductor (first design of a port/adapter) |
| ORD-03 | models and `OrderService` | framework-implementer | conductor |
| ORD-04 | order factory, assertions, fixtures | framework-implementer | orchestrator allowed |
| ORD-05 | automate TC-ORD-001 … 005 | test-author | orchestrator allowed |

**Back-and-forth**
- **You:** "ORD-03 and ORD-04 both touch `OrderService`. Make them sequential."
  **Claude** sets `depends_on: ORD-03` on ORD-04; the skill says tasks touching the same interaction object run
  sequentially. **PROMPT · AI-SDLC**

---

## Step 8: Tests first for the framework (red)

**You type**
> Use the `taf-contract-first` skill with the `framework-test-writer` agent for ORD-01 to ORD-04. Stop when
> the tests are red for the right reason and show me the failures.

**What happens, in order**

1. `framework-test-writer` (haiku) writes unit tests (`@pytest.mark.unit`) against the LLD's public interfaces,
   using a fake `HttpPort`. **AI-SDLC** (tests first) + **NEW** (contract tests per adapter)
   - Paths follow the LLD, e.g. `tests/framework/unit/test_order_service.py`.
   - Cases: success, 400/401/403/404 results, timeout, malformed JSON, token refresh, redaction applied,
     environment not allowed.
   - It writes `@pytest.mark.contract` tests once against `HttpPort`, parametrized over adapters.
2. Hooks on each test file:
   - `fact_force` does **not** fire: `tests/` isn't under `SDLC_FACT_FORCE_PATHS`.
   - `test_guard` would block any added `time.sleep(`. **HOOK · NEW**
   - `quality_guard` would block `@pytest.mark.skip`, `skipif`, `xfail` or `pytest.skip(` without an
     `sdlc: justified` reason on the line. **HOOK · ECC**
   - `post_tool.py` runs ruff. **Example:** `PT011 pytest.raises(ValueError) is too broad` can't be auto-fixed,
     so Claude gets it back immediately and adds `match=`. **HOOK · ECC**
3. It runs `uv run --no-sync pytest -m unit tests/framework` (allowed without prompt). Expected red:
   `ModuleNotFoundError: No module named 'taf.api.services.order_service'`. That is the right reason (the module
   the LLD names doesn't exist yet), not a typo in the test.

4. **Claude tries to stop; the Stop hook checks for a red phase.** **HOOK · AI-SDLC + NEW**
   1. `check.py --fast` fails, because the self-tests are red.
   2. `stop.py` lists changed files with `git status --porcelain -uall`. The only changed Python files are
      under `tests/`, so this may be a red phase.
   3. It runs `uv run --no-sync python scripts/check.py --red-phase`: static context budget, module size,
      lint + design rules, types, architecture, hygiene. Everything except the self-tests.
   4. That passes, so Claude may stop, and you see:
      `Red phase: framework self-tests are failing, only test files changed, and every other fast gate passes. ...`
   5. No fix attempt is used up.

**When the red phase is refused (Claude must keep fixing):**

| Situation | Why |
|---|---|
| A file under `src/` also changed | Implementation plus failing tests is not a red phase |
| A test file has a lint, type or hygiene problem | `check.py --red-phase` fails |
| No test file changed | Nothing was written test-first |
| `SDLC_RED_PHASE_CMD=off` is set | You disabled the exception |

**Limits to know**
- The red phase only proves "only tests changed and everything else is clean". It does not prove the
  failures are for the right reason. **Read the failures Claude shows you.** **HUMAN**
- It also applies if an agent **breaks** an existing test while only editing tests. You'll see the red-phase
  message, and pre-push and CI still fail.
- A framework test must never be made skip/xfail to get past red. `framework-test-writer` is told never to
  (**PROMPT**), and `quality_guard` blocks it (**HOOK**).

**Back-and-forth**
- **You**, after reading the failures: "TestTokenRefresh fails with `AttributeError: 'FakeHttpPort' object has no
  attribute 'calls'`. That's a bug in the fake, not a missing feature. Fix the fake."
- **Claude** fixes the fake (a test-code change, so still a red phase) and shows the failures again: only
  `ModuleNotFoundError` for the modules the LLD names.
- **You:** "Good. Implement ORD-01 with `framework-implementer`."

---

## Step 9: Implement the framework (green)

**What happens, in order** (one task at a time, `framework-implementer`, model opus)

1. **Read first:** `AGENTS.md`, the task, the LLD, the spec, the ADRs, `layers.toml`; search for existing
   utilities. **PROMPT · AI-SDLC + ECC**
2. **Add the dependency:** `uv add httpx` (you approve). `deps_guard` checks PyPI. `uv.lock` changes and must be
   committed, because CI runs `uv sync --locked`. **HOOK · ECC**
3. **First write of a framework file:** Claude tries to Write `src/taf/config/settings.py`. `fact_force`
   **denies it once**:
   ```
   Before changing src/taf/config/settings.py, state these facts in your reply, then retry the edit:
   1. Which layer src/taf/config/settings.py belongs to and its single responsibility, in one sentence.
   2. Evidence that no existing module already does this (search for it).
   3. Which module will import it, and which abstractions (ports/Protocols) it depends on.
   4. The LLD or task section it implements (docs/design or docs/tasks), if one exists.
   5. The user's current instruction, quoted verbatim.
   ```
   Claude searches, writes the five answers in its reply, and retries; the retry goes through.
   - For an **existing** file the questions are different: importers, affected public API, data shapes, and a
     design check against `layers.toml`.
   - The hook records each file once per session in `.sdlc/fact_force/<session>.json`.
   - **The hook does not judge the answers.** It forces the investigation to be written where you can read it.

   **HOOK · ECC** (GateGuard) + **NEW** (layer questions)
4. **Lint feedback after every edit:** `post_tool.py` runs `ruff format` and `ruff check --fix`. **HOOK + GATE · ECC + NEW**
   - `PLR2004 Magic value used in comparison` for `status_code == 401` → Claude uses `HTTPStatus.UNAUTHORIZED`.
   - `C901 redact_body is too complex (10 > 8)` → Claude splits the function.
5. **A layer slip, caught at Stop:** Claude writes `import httpx` in `src/taf/api/services/order_service.py` to
   catch `httpx.HTTPStatusError`. Architecture is not checked at write time, so the edit succeeds. When Claude
   tries to stop, `check.py --fast` fails:
   ```
   [FAIL] architecture rules (layers.toml)
   src/taf/api/services/order_service.py:3: layer 'services' imports 'httpx' (owned by ['api_clients'])
   ```
   Claude gets "fix attempt 1/3" and maps httpx errors to framework errors inside the client layer.
   **HOOK (Stop) + GATE · NEW**
6. **Blocked shortcuts**

   | Claude tries to… | What happens | Kind · Source |
   |---|---|---|
   | Add `# type: ignore` to silence mypy on an httpx event hook | Blocked unless the same line carries `sdlc: justified <reason>`; Claude fixes the types | HOOK · ECC |
   | Raise `max-args` from 5 to 6 in `pyproject.toml` for `OrderService.create` | Blocked (`[tool.ruff]` is a quality section); Claude uses the `NewOrder` parameter object | HOOK · ECC |
   | Edit `.pre-commit-config.yaml` | Blocked (protected file) | HOOK · ECC |
   | `git commit --no-verify` | Blocked twice: permission deny and `bypass_guard` | HOOK · ECC |
   | `rm tests/framework/unit/test_order_service.py` | Blocked by `bypass_guard` ("deleting tests") | HOOK · ECC |

7. **Sleeping inside framework code is allowed.** A `wait_until` helper in `src/taf/core/waits.py` that calls
   `time.sleep(poll_interval)` is not blocked:
   - `test_guard` only looks at test code (`tests/`, `test_*.py`, `*_test.py`, `conftest.py`).
   - Hygiene rule H001 only looks inside test functions.
   - Polling belongs in the framework; tests call the helper.
8. **Green:** Claude runs `uv run --no-sync python scripts/check.py --fast` itself (allowed). When it tries to
   stop, the Stop hook passes.

**Back-and-forth: three failures and a human**

- The token-refresh unit test keeps failing. The LLD says "refresh 60 s before expiry"; the spec's AC says
  "refresh after a 401". After the third failed Stop attempt, Claude may stop with the `Human needed` message
  and explains the contradiction.
- **You:** "Refresh 60 s before expiry. Update the spec and LLD."
- **Claude** updates both. `framework-implementer` is told a structural LLD change needs re-review, so you run
  `design-reviewer` on the changed LLD section. **HOOK (damping) + HUMAN · AI-SDLC + ECC**

**Note:** `check.py --fast` does **not** measure coverage. The 80% coverage floor is checked only by the full
`check.py` (pre-push and CI). **GATE**

---

## Step 10: Automate the test cases

**You type**
> Use the `test-author` agent for ORD-05: automate TC-ORD-001 to TC-ORD-005.

**What happens, in order**

1. `test-author` (sonnet) reads each test case (oracle, data, preconditions) and the `api-rest-automation`
   skill. **PROMPT · NEW**
2. It writes tests that use only interaction objects, factories, fixtures and assertion helpers (example):
   ```python
   import pytest

   from taf.assertions.order_assertions import assert_order

   pytestmark = [pytest.mark.api, pytest.mark.rest]


   @pytest.mark.smoke
   def test_create_order_returns_pending_order(order_service, order_factory):
       new_order = order_factory.build(line_count=3)

       result = order_service.create(new_order)

       assert result.status_code == 201
       assert_order(result.body).has_status("PENDING").has_total(new_order.expected_total)
       assert order_service.get(result.body.order_id).body == result.body
   ```
3. **Hooks and gates during authoring**

   | Situation | What happens | Kind · Source |
   |---|---|---|
   | Claude adds `time.sleep(2)` before the GET (eventual consistency) | **Blocked at write:** `BLOCKED: adds a hard sleep in test code (...). Synchronize on a condition with the framework's explicit wait ...`; Claude uses `wait_until` | HOOK · NEW |
   | Claude puts `"https://orders.test.example.internal"` in a test | Not blocked at write. Stop hook → `hygiene_check.py` → `H007 hard-coded URL: read it from environment config`; Claude moves it to config | HOOK (Stop) + GATE · NEW |
   | A test has `api` but no `smoke`/`regression` marker | Stop hook → `H004 test_get_status no level marker (regression\|smoke)`; without it no CI job would ever select the test | GATE · NEW |
   | A test has no platform marker | `H004 ... no platform marker (api\|desktop\|web)` | GATE · NEW |
   | A test with no `assert` / `expect` / `verify…` / `assert_…` call | `H006 ... has no assertion or expect/verify` | GATE · NEW |
   | Claude adds `@pytest.mark.flaky(reruns=2)` | Blocked at write (retry/flaky masking) | HOOK · NEW |
   | Claude adds `@pytest.mark.order(1)` | Blocked at write (test ordering/dependency); H005 in hygiene too | HOOK + GATE · NEW |

4. **Environment:** tests read `TAF_ENV` and the client secret from the shell you started Claude Code in. If
   they're missing, ORD-01's configuration raises a clear error and `test-author` asks you. Claude will not read
   `.env`. **HUMAN · NEW**
5. **Proof of failure:** for each test, `test-author` temporarily changes an expected value on a marked line,
   runs the test, sees it fail, restores the original line, and records this in the test case's "Proof of
   failure" section. **PROMPT · NEW**
   ```python
   assert result.body.status == "CONFIRMED"  # sdlc: justified proof of failure, revert
   ```
   - The marker is required: `test_guard` blocks changing an assertion line without it.
   - Restoring is allowed because the line being replaced carries the marker.
   - If the temporary line is never restored, the test keeps failing (it asserts a wrong value), and the leftover
     marker is visible in the diff.

   **HOOK · NEW**
6. **Stability:** it runs the new tests 3 times with separate `uv run pytest` invocations (no repeat plugin is
   installed), including once with `-n 2`, and reports results. **PROMPT · NEW**
7. It runs `uv run --no-sync python scripts/hygiene_check.py tests/api/orders` and the fast gates.

**Back-and-forth: the application disagrees with the oracle**

- TC-ORD-005 fails against the test environment: expected total `59.97` (REQ-ORD-12, half-up), actual `59.96`.
- **Blocked:** deleting the assertion, or changing `59.97` to `59.96`, is blocked by `test_guard`:
  ``BLOCKED: this edit removes or changes assertions in tests/api/orders/test_totals.py (`assert ... == 59.97`). Making a test pass by checking less, or by changing the expected value to match the application, is not a fix. ...``
  **HOOK · NEW**
- **What the hook can't tell:** whether a new value is justified. An agent *could* add
  `# sdlc: justified <reason>` to push the change through; the reason is then visible in the diff for review.
  `AGENTS.md` and `test-author` say to cite a requirement or ticket. **PROMPT + HUMAN**
- **Blind spot:** only the first line of a multi-line assertion is compared, so a value on a continuation line
  isn't guarded.
- **Claude**, following its instructions:
  > TC-ORD-005 fails: expected 59.97 per REQ-ORD-12 (half-up), actual 59.96, which looks like half-even
  > rounding. Product bug or requirement change?
- **You:** "Product bug, ORD-BUG-77."
- **What happens to the test** (kit default: `ci-triage` routes a product bug as "keep the test failing"):
  - TC-ORD-005 is marked `regression`, so it turns the nightly red until the bug is fixed. That is the test
    doing its job.
  - If your team wants it non-blocking, a **human** approves an expected-failure marker with the reason on the same line:
    ```python
    @pytest.mark.xfail(reason="ORD-BUG-77 rounding", strict=True)  # sdlc: justified product bug ORD-BUG-77
    ```
    - Without `sdlc: justified` on that line, `quality_guard` blocks the edit.
    - `xfail_strict = true` in `pyproject.toml` makes the test fail once the bug is fixed (XPASS), reminding you
      to remove the marker.
- **Not stopped by the Stop hook:** the Stop hook's fast gates run only `unit or contract` tests. A failing
  **API** test does not stop Claude from ending its turn; API tests run in CI and when Claude or you run them.

---

## Step 11: Independent review

**You type**
> Run `automation-reviewer`, `design-reviewer`, `test-quality-reviewer` and `automation-security-reviewer` on
> this branch.

**What happens, in order**

The four agents run, each reading the diff (`git diff main...HEAD`), the spec, test cases, LLD, and their
checklist or skill. Their instructions say Bash is read-only and they never edit or commit. That is **PROMPT**;
their tool list still includes Bash, and your permission prompts still apply. **AI-SDLC** (the builder never
grades itself) + **ECC** (reviewer agents, severity format) + **NEW** (what they check)

**Example findings and how each is resolved**

| Reviewer | Finding | Resolution |
|---|---|---|
| `automation-reviewer` (haiku) | HIGH `tests/conftest.py:31`: `order_factory` is session-scoped and keeps a list of created orders shared by every test in a worker | `framework-implementer` makes it function-scoped, as the LLD says |
| `design-reviewer` (opus) | MEDIUM `src/taf/assertions/order_assertions.py:22`: duplicates money parsing from `models/order.py` | `framework-implementer` reuses `Money` |
| `test-quality-reviewer` (sonnet) | CRITICAL gap: REQ-ORD-9 "wrong role (403)" is high-risk in the suite spec but has no test | **You decide:** add now. Back to Step 3 for `TC-ORD-006`, then Step 10 |
| `automation-security-reviewer` (opus) | HIGH `src/taf/api/clients/http_client.py:88`: redaction covers the `Authorization` header but not `access_token` in the token response body attached as evidence | `framework-implementer` fixes it and adds a redaction unit test |

The first row is a design deviation no hook or gate detects (fixture scope isn't statically checked); only review catches it.

**Loop:** fix → Stop hook gates → re-run the reviewer that raised the finding → until no CRITICAL or HIGH remains.

---

## Step 12: Full gates, commit, PR, CI

1. **Full gates:** Claude runs `uv run python scripts/check.py`. mypy now includes `src/taf` from your Step 5
   edit. **GATE · AI-SDLC + NEW**
   - Back-and-forth: `framework self-tests + coverage` fails at 74% (floor 80).
   - Claude cannot add `# pragma: no cover` (**HOOK · ECC**).
   - `framework-test-writer` adds unit tests for the uncovered branches, and the run goes green.
2. **Commit:** the same hooks as the design PR: `bypass_guard`, `secrets_guard` over all pending changes, git
   pre-commit hooks (now `hygiene_check.py` and `architecture_check.py` have real code to check). **HOOK + GATE**
3. **Push:** the pre-push hook runs full `check.py`. **GATE**
4. **PR:** Claude fills the template:
   - design-reviewer verdict
   - test integrity boxes (no assertions removed, no sleeps or retries, new tests run ≥ 3 times, proof of failure recorded)
   - verification boxes, risk (environments touched: `test`)

   **AI-SDLC + NEW**
5. **CI on the PR** **CI · AI-SDLC + ECC + NEW**
   - `mode-boundary` passes.
   - `harness`: hidden Unicode, secrets in the branch diff, `verify_deps.py` (checks `httpx` age and existence),
     AgentShield (fails on high/critical findings in `.claude/`).
   - `quality` (3.12, 3.13) runs `uv sync --locked` (fails if `uv.lock` isn't committed), then full `check.py`.
   - `smoke-api-web` runs `pytest -m "smoke and (api or web) and not quarantine" -n auto`. **Two things the kit
     does not do for you:**
     - The workflow only sets `TAF_ENV: test`. Add the Order API secret to that job's `env:` from
       `${{ secrets.TAF_ORDERS_CLIENT_SECRET }}`. That's a `.github/` change reviewed by harness-owners.
     - The runner must be able to reach `orders.test.example.internal` (Part 1.6).
   - `smoke-desktop` has no desktop tests (exit 5) and passes with a warning.
6. **Human review:** CODEOWNERS requests owners for `src/taf/`, `tests/`, `.github/`, `pyproject.toml` (the
   `httpx` dependency). A human reviews every line and merges. **HUMAN · AI-SDLC**

---

## Step 13: After merge

### Nightly regression (`nightly-regression.yml`, daily 01:11 UTC)

**What runs:**
- Job `api-web` runs for **both** matrix entries (`primary`, `secondary`). The matrix is meant for browsers,
  so for API-only tests it just runs the same suite twice, **in parallel against the same environment**.
- Each leg runs `-m "regression and (api or web) and not quarantine"` twice, then
  `flaky_report.py run1.xml run2.xml --fail-on-flaky`.
- Job `desktop`: no tests, passes with a warning.
- Job `quarantined`: runs quarantined tests without gating.

**CI · NEW**

**Back-and-forth: a flaky test**
- TC-ORD-002 failed in run 1 and passed in run 2, so `flaky.json` lists it and the job is red.
- **You:** "Use `ci-triage` on last night's run." `ci-triage` (haiku) may use `gh run view <id> --log-failed`.
  **Example result:** cluster "TC-ORD-002 intermittent 409 Conflict", classification **flaky**, next action
  `flaky-test-investigator`. **PROMPT · AI-SDLC + NEW**
- **You:** "Use `flaky-test-investigator` on TC-ORD-002." **PROMPT · NEW**
  - It reruns with `-n 4` and repeated runs.
  - **Example diagnosis:** data collision. Both matrix legs run at the same time with the same xdist worker ids
    (`gw0`, `gw1`, …); a reference built from the worker id plus a timestamp collides.
  - **Fix:** add a UUID to the reference.
  - It never proposes retries, longer sleeps, or loosened assertions.
- **The fix** goes through a small loop of Steps 9 → 12 on `fix/order-reference-uniqueness`.
- **If the fix will take time,** a human approves quarantine:
  ```python
  @pytest.mark.quarantine(reason="QA-1234 409 on parallel create", until="2026-10-15")
  ```
  - `quality_guard` does not block this marker.
  - Hygiene rule H008 fails if `reason` or `until` is missing or the date has passed. **GATE · NEW**
  - Gating runs exclude it (`not quarantine`); the nightly `quarantined` job still runs it.
  - "Leave quarantine after 20 consecutive passes" is a rule in the `flaky-test-management` skill; **nothing
    counts those passes automatically.** **PROMPT + HUMAN**

### Weekly mutation testing (`weekly-mutation.yml`, Sundays 03:23 UTC)
Skipped with a warning until `[tool.mutmut]` exists in `pyproject.toml` (Step 5). After that, its results are an
artifact to review as a trend; the job never fails the build (`mutmut run || true`). **CI · NEW**

### When an agent did something it must never do again
- **Example:** an agent wrote `verify=False` (TLS verification off) in the API client. Only the
  `automation-security-reviewer` caught it in review; no hook or gate checks for it today.
- **You:** "Use the `sdlc-harness-fix` skill: an agent disabled TLS verification in the HTTP client."
- **Claude**, following the skill's table:
  - classifies it as "Knew the rule, broke it again → prose, not enforcement → hook, with a test"
  - proposes a new guard in `.claude/hooks/lib/` (wired into `pre_tool.py`) plus a test in `.claude/hooks/tests/`
  - adds one Lessons line to `AGENTS.md`: `- YYYY-MM-DD: <rule>. (why: <what happened>)`
  - the change goes through a harness PR reviewed by CODEOWNERS `/.claude/`

**AI-SDLC** (harness post-mortems, lessons) + **ECC** (hooks over prose)

### Checking that the harness still steers agents (optional)
`uv run python scripts/harness_eval.py` runs the 4 cases in `evals/harness_cases.jsonl`:
- It needs the `claude` CLI and spends tokens.
- It runs Claude Code headless against the repo.
- It writes `.sdlc/evals/harness_latest.json`.

**AI-SDLC + NEW**

---

## Summary 1: Which rules are hard blocks and which are instructions

| Rule | HOOK | GATE / CI | PROMPT | HUMAN |
|---|---|---|---|---|
| No hard-coded credentials (incl. URL creds, Basic/Bearer headers, SOAP passwords, DSNs) | `secrets_guard` (writes, Bash, commits) | pre-commit staged scan, CI diff scan | `AGENTS.md` | review |
| No sleeps in tests | `test_guard` | H001 | agents | review |
| No removed assertions | `test_guard` | none | agents | review |
| No changed or loosened assertion lines without `sdlc: justified <reason>` | `test_guard` (first line of each assertion) | none | `AGENTS.md`, `test-author` | review judges the reason |
| TLS verification stays on | **none** | none | `api-rest-automation`, security reviewer | review |
| No retries / reruns / ordering markers | `quality_guard` | H005 (ordering) | agents | review |
| No skip/xfail without reason | `quality_guard` | H003 | agents | review |
| No weakening of lint/type/test/coverage config | `quality_guard` | CODEOWNERS | `AGENTS.md` | review |
| No hook bypass, force push, hard reset, deleting tests | `bypass_guard` + permission deny | none | none | none |
| Only real, established packages | `deps_guard` | `verify_deps.py` in CI, `pip-audit` | none | none |
| Investigate before editing framework code | `fact_force` (asks; doesn't judge answers) | none | `framework-implementer` | you read the answers |
| Layer rules and engine ownership | none at write time | `architecture_check.py` (Stop hook, pre-commit, pre-push, CI) | `AGENTS.md` | design review |
| Locators / URLs out of tests | none at write time | H002, H007 | agents | review |
| Automated tests have a platform **and** a level marker; self-tests `unit`/`contract` | none | H004 | agents | review |
| Quarantine has a ticket and expiry | none | H008 | skill | you approve |
| Gates green before Claude stops | Stop hook (max 3 fix attempts; red phase allowed when only tests changed and other gates pass) | none | none | after 3 attempts; read red-phase failures |
| Fixture scope and parallel safety match the LLD | **none** | none | LLD, agents | design and code review |
| Spec / ADR / HLD / LLD approved before code | **none** | none | agents and skills | **you** |
| Proof of failure, 3× stability runs | none | none | `test-author` | PR template checkbox, review |
| Exploration branches never merge to `main` | none | `mode-boundary` | `AGENTS.md` | branch protection |

## Summary 2: Where each step comes from

| Step | AI-SDLC | ECC | NEW |
|---|---|---|---|
| Setup and session start | always-on vs on-demand context, gates in git hooks and CI | hooks, permission denies | TAF-specific hooks and gates |
| 1. First request | plan before code, human decides scope | model routing | decision backlog, walking-skeleton guidance |
| 2. Capability spec | spec-driven development, human approval | secrets guard on docs | capability template (failure behavior, diagnosability) |
| 3. Suite spec and test cases | spec approval | none | risk scoring, pyramid level, concrete oracles, proof-of-failure plan |
| 4. ADRs | explicit decisions, humans accept | package verification | spikes on the real app, library ownership |
| 5. HLD | design before code | independent design reviewer | `layers.toml` + architecture check, TAF layers, security sign-off |
| 6. LLD | none | SOLID / LLD discipline, simplicity rule | fixtures, parallel safety, sync and evidence sections |
| 7. Tasks | conductor vs orchestrator, task files | none | Must NOT list for test integrity |
| 8. Tests first | tests before code, Stop-hook red phase | lint feedback, suppression guard | contract tests per adapter |
| 9. Implementation | Stop-hook feedback loop | fact-force, config protection, bypass guard, retry cap | layer questions, layer violations caught |
| 10. Test automation | none | none | sleep/assertion guard, hygiene H001–H008, proof of failure, stability runs |
| 11. Review | builder never grades itself | reviewer agents, severity format | test-quality and automation-security reviewers |
| 12. PR and CI | human reviews every line, CI gates | AgentShield, hidden Unicode, secrets diff | smoke by platform, desktop on Windows |
| 13. Operate | lessons, harness post-mortems, evals | hooks over prose | nightly ×2 + flaky report, quarantine with expiry, mutation |

## Summary 3: Things only you do

1. Install tools, set up GitHub (branch protection, `test` environment, secrets, runners, CODEOWNERS).
2. Decide scope and answer every open question about expected behavior.
3. Approve specs and test cases, accept ADRs, sign off HLD and LLD.
4. Edit quality-gate sections of `pyproject.toml` (mypy files, pytest pythonpath) when the design requires it.
5. Export environment variables with test credentials before starting Claude Code.
6. Decide "product bug or test bug", and approve any xfail or quarantine.
7. Review and merge every PR.

## Summary 4: Gaps in the kit

Each item was confirmed in the source.

**Fixed after this walkthrough was first written** (each with tests in `.claude/hooks/tests/` or `scripts/tests/`)

| Gap | Fix |
|---|---|
| Changing an expected value inside an assertion wasn't blocked | `test_guard` compares assertion lines (whitespace-insensitive) and blocks removed or changed ones unless the edit carries `sdlc: justified <reason>`; lines already carrying the marker may be reverted (proof of failure) |
| A test with only a platform marker passed every gate but never ran in CI | H004 requires `unit`/`contract`, or a platform (`web`/`desktop`/`api`) **and** a level (`smoke`/`regression`) |
| `Authorization: Bearer <literal token>` wasn't matched | `secrets_guard` pattern "Bearer token"; f-strings, `${VAR}` and `<token>` placeholders don't match |
| The Stop hook blocked the tests-first red phase | `stop.py` allows stopping when only test files changed and `check.py --red-phase` passes; the user is told tests are red |
| ADR numbering counted the template and backlog | `sdlc-adr`, `system-design-hld`, `code-design-lld` define NNNN as highest existing plus one, starting at `0001` |
| `harness_eval.py` docstring referred to the agentic kit | Corrected |

**Still open**

1. **Approvals aren't machine-checked.** Nothing verifies a spec, ADR, HLD or LLD is `Approved` before code is
   written, and `docs/specs/` and `docs/test-cases/` have no CODEOWNERS entry.
2. **Hooks ignore branch mode.** Exploration vs engineering is only enforced when a PR targets `main`.
3. **Nightly legs share one environment.** The `api-web` matrix runs two legs in parallel against the same
   environment, which can create data collisions.
4. **The CI smoke job lacks application secrets.** It sets only `TAF_ENV`; each application's secrets must be
   added to the workflow.
5. **TLS verification isn't checked.** No hook or gate detects `verify=False`; only review does.
6. **The assertion guard has limits.**
   - Only the first line of a multi-line assertion is compared.
   - A `sdlc: justified` marker lets any change through, so reviewers must judge the reason.
   - Renaming a variable used in an assertion also needs the marker.
7. **The red phase can hide a broken test.** It also applies when an agent breaks an existing test while editing
   only tests; pre-push and CI still catch it.
8. **Not yet run for real:** the GitHub workflows (never run on GitHub), mutmut (unsupported on native Windows),
   and the harness evals (need the `claude` CLI).
