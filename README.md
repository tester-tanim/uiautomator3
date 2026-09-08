<div align="center">

# UIAutomator 3.0

**Next-generation Android automation framework** focused on precision UI inspection,
robust element identification, and reliable mobile automation.

Designed as a successor to [openatx/uiautomator2](https://github.com/openatx/uiautomator2).

[![CI](https://github.com/tester-tanim/uiautomator3/actions/workflows/ci.yml/badge.svg)](https://github.com/tester-tanim/uiautomator3/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Quick start](#quick-start) •
[Web inspector](#web-inspector) •
[vs. uiautomator2](#uiautomator3-vs-uiautomator2) •
[Docs](docs/UIAUTOMATOR3_ARCHITECTURE.md) •
[Contributing](CONTRIBUTING.md)

</div>

---

## What is this?

uiautomator3 drives Android devices over plain `adb` — no bundled device-side agent —
and builds every locator strategy (text, resource-id, OCR, computer vision) on one
scored, self-healing element model instead of ad hoc per-strategy code.

```python
import uiautomator3 as u3

d = u3.connect()

d(text="Login").click()
d(resourceId="com.example:id/email").click()
d.send_keys("test@example.com")

# Full XPath 1.0 requires the optional lxml dependency.
# pip install -e ".[xpath]"
d.xpath("//TextView[contains(@text, 'Login')]").click()

# scored, ranked locators for any element
locator = d(text="Login")
print(locator.best_locator(), locator.confidence)

# structured, LLM-free element description for AI agents
print(d.ai.inspect())
```

## Highlights

| | |
|---|---|
| 🎯 **Scored locators** | Every candidate selector gets a uniqueness/stability/specificity score — ambiguous matches raise `ElementAmbiguousError` instead of silently guessing |
| 🩹 **Self-healing** | Opt-in: remembers a resolved element's attributes and re-locates it when the original locator stops matching |
| 🔍 **OCR + vision fallback** | `d.ocr(text)` and `d.visual(template)` locate elements no accessibility tree can see — both optional, lazily imported |
| 🧭 **XPath 1.0** | `d.xpath(expression)` evaluates full XPath 1.0 against the normalized hierarchy — install the optional `xpath` extra |
| 🖥️ **Built-in web inspector** | React/TS + FastAPI/WebSocket UI with a live device preview, click-to-select overlay, and copyable generated locators |
| 🎬 **Record → codegen** | Turn a recorded interaction session into Python, pytest, Page Object Model, JSON, YAML, or Robot Framework |
| 🤖 **AI-ready** | `d.ai.inspect()/find()/click()/type()` plus an MCP server so agents can drive the device directly |
| ⚡ **Cached reads** | Hierarchy/screenshot reads are cached for a short TTL and auto-invalidated after any action |

## Table of contents

- [Quick start](#quick-start)
- [CLI](#cli)
- [Web inspector](#web-inspector)
- [uiautomator3 vs. uiautomator2](#uiautomator3-vs-uiautomator2)
- [Status](#status)
- [Development](#development)
- [License](#license)

## Quick start

```bash
pip install -e .                          # core only
pip install -e ".[ocr,vision,web,mcp,xpath]" # optional features
```

```python
import uiautomator3 as u3

d = u3.connect()

d(text="Login").click()
d(resourceId="com.example:id/email").click()
d.send_keys("test@example.com")

login = d.xpath("//TextView[contains(@text, 'Login')]")
login.click()

locator = d(text="Login")
print(locator.best_locator(), locator.confidence)

print(d.ai.inspect())
```

## CLI

```bash
u3 devices                  # list attached devices
u3 doctor                   # environment diagnostics
u3 dump                     # raw UI hierarchy XML
u3 screenshot -o shot.png
u3 inspect                  # launch the web inspector (requires the `web` extra)
u3 codegen session.json --format python
u3 mcp serve                 # start the MCP server (requires the `mcp` extra)
```

## Web inspector

```bash
pip install -e ".[web]"
u3 inspect                                       # backend at http://127.0.0.1:17920

cd inspector-web && npm install && npm run dev   # frontend at http://localhost:5173
```

Live device screenshot, click-to-select element overlay, a collapsible full hierarchy
tree (with one-click tree copy), and generated/scored locators per element — see
[docs/UIAUTOMATOR3_ARCHITECTURE.md §11](docs/UIAUTOMATOR3_ARCHITECTURE.md).

## uiautomator3 vs. uiautomator2

### Architecture

| | uiautomator2 | uiautomator3 |
|---|---|---|
| **Device-side agent** | `u2.jar` pushed to device, JSON-RPC over an ADB tunnel | No bundled agent — plain `adb shell` (`uiautomator dump`, `input`, `screencap`) |
| **Element model** | Two incompatible representations: `UiObject` (RPC objects) and `XMLElement` (parsed XML) — different `.info` shapes, different wait strategies | One `UIElement`/`ElementTree` model that every locator strategy (text, resource-id, OCR, vision) builds on |
| **Selector matching** | Device-side, literal only — first match wins, no scoring | Client-side, every candidate gets a uniqueness/stability/specificity score; ambiguous matches raise `ElementAmbiguousError` instead of guessing |
| **Self-healing** | None — only a transport-level "restart the server and retry once" | Opt-in: remembers a resolved element's attributes and searches for a replacement locator when the original stops matching |

### Capabilities uiautomator3 adds

- Locator scoring/stability analysis (`d.analyze_locator()`, `d(...).confidence`)
- OCR and computer-vision fallback locators (`d.ocr(text)`, `d.visual(template)`) — both optional, lazily imported
- A web inspector (React/TS + FastAPI/WebSocket) built into the project — uiautomator2's inspector (`uiautodev`) is a separate, unrelated package
- Interaction recording → code generation (Python/pytest/Page Object Model/JSON/YAML/Robot Framework) from a recorded session
- AI-ready structured inspection (`d.ai.inspect()/find()/click()/type()`) and an MCP server so AI agents can drive the device directly
- Caching — hierarchy/screenshot reads are cached for a short TTL and auto-invalidated after any action, versus uiautomator2 re-dumping every call

### What uiautomator2 still does that uiautomator3 doesn't yet

- Fast device-side JPEG screenshot encoding (uiautomator3 currently uses `adb screencap`, which is slower)
- Screen recording (video), a state-based UI model, and a plugin registry are all still unimplemented placeholders in uiautomator3

See [docs/UIAUTOMATOR2_ANALYSIS.md](docs/UIAUTOMATOR2_ANALYSIS.md) and
[docs/UIAUTOMATOR3_ARCHITECTURE.md](docs/UIAUTOMATOR3_ARCHITECTURE.md) for the full detail
behind this comparison.

## Status

Phases 1-12 of the architecture's phase plan are implemented: device connection, gestures,
hierarchy inspection, scored locators, self-healing, OCR/vision fallbacks, a web inspector,
interaction recording + code generation, AI-ready inspection + an MCP server, and short-TTL
caching. See [CHANGELOG.md](CHANGELOG.md) for the full breakdown and known limitations.

## Development

```bash
pip install -e ".[ocr,vision,web,mcp]"
pip install pytest pytest-cov ruff mypy

pytest tests/unit -v
ruff check uiautomator3 tests
ruff format uiautomator3 tests
```

CI runs the unit test suite across Python 3.8–3.12, `ruff` lint/format checks, `mypy`,
`u3 doctor` against a deviceless runner, and an `inspector-web` typecheck + build — see
[.github/workflows/ci.yml](.github/workflows/ci.yml).

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions, the mypy/numpy version-pinning
note, and how to submit changes.

## License

[MIT](LICENSE)
