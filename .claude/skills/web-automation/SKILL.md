---
name: web-automation
description: Design and write web UI automation in the framework: web driver adapter behind ports, page and component objects, locator strategy, synchronization, browser/context isolation, network control, cross-browser runs, and failure evidence. Use when building the web driver layer, page objects, or web test cases, whatever engine the ADR selected.
---

# Web automation

## Driver layer (only place the browser engine is imported)
- One adapter per engine implementing the ports from the HLD (navigate, find, act, read, wait, evidence). Passes the shared contract tests.
- Session lifecycle per test (fresh browser context/profile per test by default); per-worker browser processes when isolation cost is too high, never shared across workers.
- Headless in CI; browser, version, viewport, locale, and timezone from configuration.
- Evidence on failure: screenshot, DOM snapshot or engine trace, console errors, network log. Redacted and attached to the test report.

## Page and component objects
- Model user intent: `checkout.pay_with(card)`, not `click("#btn-3")`. Return new objects or plain state; no assertions inside.
- Components for reusable widgets (date picker, data grid, header) composed into pages; no deep inheritance.
- Locators live here, in one place per concept.

## Locator strategy (most to least stable)
1. Dedicated test attributes agreed with developers (e.g. `data-testid`): request them; they are a testability requirement.
2. Accessible role + accessible name / label (also validates accessibility).
3. Stable ids and names.
4. CSS scoped to a stable container.
5. XPath only for structures nothing else can express; never absolute paths or index chains.
Text-based locators are fine for user-visible labels that are part of the requirement; not for text that changes with data or locale.

## Synchronization
- Wait on conditions: element visible/enabled/detached, URL changed, specific network response completed, spinner gone. Use the engine's auto-waiting where it exists, and centralize custom waits in the driver layer.
- Timeouts named and configurable per environment; failure messages say what was awaited and what was observed.
- Never `sleep`. Never poll the DOM in tests.

## State and data
- Set up state through APIs or data factories, not by clicking through the UI; authenticate via stored session state or API login where the ADR allows.
- Network interception/stubbing only for scenarios that need controlled backend behavior (errors, slow responses), and label those tests so they aren't mistaken for end-to-end coverage.

## Cross-browser and parallel
- Browser matrix defined by risk (primary browser on every PR; others nightly).
- Tests independent and parallel-safe: unique users/data per worker; no shared downloads folder.

## Beyond functional (optional, decided by ADR)
Accessibility scans on key pages; visual comparison for stable, high-value screens only, with reviewed baselines.
