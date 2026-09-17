# SOLID for a Python test automation framework

## S: Single Responsibility
One reason to change per unit.
- A page/screen/service object changes when *that screen or API* changes, not when a test's expectations change. Keep assertions and test data decisions out of it.
- A driver adapter changes when its engine changes. Keep application knowledge out of it.
- A test changes when the *requirement* changes.
**Smell:** `LoginPage` also creates users, checks audit logs, and parses emails. Split into page object, data factory, and verification helper.
**Don't force it:** a 5-method page object for a 5-control screen is fine.

## O: Open/Closed
Add platforms, browsers, auth schemes, and report sinks by adding code.
```python
DRIVERS: dict[str, Callable[[Settings], BrowserPort]] = {
    "engine_a": build_engine_a,
    "engine_b": build_engine_b,
}
```
**Smell:** `if browser == "chrome": ... elif browser == "firefox": ...` repeated across helpers.
**Don't force it:** one engine and no second in sight is a plain function.

## L: Liskov Substitution
Every adapter behind a port honors the same contract: same timeouts semantics, same exceptions on not-found, same evidence behavior.
**Proof, not hope:** `@pytest.mark.contract` tests written once against the port and parametrized over all adapters.
**Smell:** tests contain `if platform == "desktop": skip this assertion`.

## I: Interface Segregation
Small capability Protocols instead of one `Driver` with 60 methods:
```python
class Clickable(Protocol):
    def click(self, target: Target) -> None: ...


class Readable(Protocol):
    def text_of(self, target: Target) -> str: ...
```
A REST service object does not depend on a browser port; a desktop screen object does not need navigation by URL.
**Smell:** fakes for unit tests must implement dozens of unused methods.

## D: Dependency Inversion
Tests depend on interaction objects; interaction objects depend on ports; adapters implement ports; fixtures (the composition point) wire them from configuration.
```python
def test_invoice_total(invoice_screen: InvoiceScreen, invoice_factory: InvoiceFactory) -> None: ...
```
**Enforced by:** `layers.toml` `may_import` + `library_owners`, checked by `scripts/architecture_check.py`.
**Don't force it:** don't wrap `pathlib`, `json`, or `datetime` behind interfaces.

## Also
- **KISS/YAGNI**: build the capability the next approved spec needs, not a "universal framework".
- **DRY with judgment**: one locator or request builder per concept; tolerate similar-looking tests that verify different behaviors.
- **Law of Demeter**: `app.invoices.open(42).total()` beats `driver.find(...).find(...).text`.
- **Fail fast, fail clearly**: every wait and assertion names what it expected and what it saw.
