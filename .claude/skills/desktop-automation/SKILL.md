---
name: desktop-automation
description: Design and write desktop application automation (Windows desktop apps such as Win32, WinForms, WPF, UWP, or other desktop technologies selected by ADR): desktop driver adapter behind ports, screen objects, element identification via UI automation properties, window and application lifecycle, synchronization, focus and session constraints, and failure evidence. Use when building the desktop driver layer, screen objects, or desktop test cases.
---

# Desktop automation

## Driver layer (only place the desktop automation library is imported)
- Adapter implements the same ports as web where meaningful (find, act, read, wait, evidence) plus desktop-specific capabilities (launch/attach application, window management, keyboard/mouse fallback). Passes contract tests.
- Choose the automation backend per application technology in an ADR (e.g. UI Automation-based access for modern Windows UI frameworks vs legacy Win32 access), verified in a spike against the real application.
- Application lifecycle: launch with a known clean state (fresh profile/config directory, test database or service stub), attach by process id, close and kill the process tree on teardown. Leftover processes break the next test.

## Screen objects
- One per window/dialog/major panel; methods express user intent; no assertions inside.
- Identify elements by stable automation properties (automation id / control name set by developers), then control type + name within a stable parent. Coordinates and image matching are last resorts with an ADR.
- Request automation ids from developers as a testability requirement.

## Synchronization
- Wait for window existence, element enabled/visible, busy cursor/progress indicators gone, or application state files. Never sleep.
- Modal dialogs and unexpected popups (updates, licensing, crash reporters) handled by a central watchdog in the driver layer that records evidence.

## Execution constraints (design for them)
- Desktop UI tests usually need an **interactive, unlocked desktop session**; CI runners must be configured for it (auto-logon agent, no screen lock, fixed resolution and DPI scaling).
- One UI session cannot safely run two UI tests at once: parallelize across machines/VMs, not with xdist workers on one desktop. Mark such tests and configure CI accordingly.
- Keyboard input and focus are global: never type while another window can steal focus; verify the target window is active before sending keys.
- Locale, DPI, resolution, and theme pinned per environment.

## Evidence
Screenshot of the active window and full screen, element tree dump of the failing window, application logs, and event log entries when available. Redact sensitive screens.

## Data and state
Seed data through services, files, or databases the application reads; reset between tests. Never depend on data left by a previous test.
