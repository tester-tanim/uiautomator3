# UIAutomator 3.0

Next-generation Android automation framework focused on precision UI inspection, robust
element identification, and reliable mobile automation — designed as a successor to
[openatx/uiautomator2](https://github.com/openatx/uiautomator2).

See [docs/UIAUTOMATOR3_ARCHITECTURE.md](docs/UIAUTOMATOR3_ARCHITECTURE.md) for the full
design and phase plan, and [docs/UIAUTOMATOR2_ANALYSIS.md](docs/UIAUTOMATOR2_ANALYSIS.md)
for the predecessor-project analysis this design responds to.

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
- A full XPath 1.0 engine (uiautomator3 generates a best-effort structural XPath, not a real XPath evaluator)
- Screen recording (video), a state-based UI model, and a plugin registry are all still unimplemented placeholders in uiautomator3

See [docs/UIAUTOMATOR2_ANALYSIS.md](docs/UIAUTOMATOR2_ANALYSIS.md) and
[docs/UIAUTOMATOR3_ARCHITECTURE.md](docs/UIAUTOMATOR3_ARCHITECTURE.md) for the full detail
behind this comparison.

## Status

Phases 1-12 of the architecture's phase plan are implemented: device connection, gestures,
hierarchy inspection, scored locators, self-healing, OCR/vision fallbacks, a web inspector,
interaction recording + code generation, AI-ready inspection + an MCP server, and short-TTL
caching. See [CHANGELOG.md](CHANGELOG.md) for the full breakdown and known limitations.

## Quick start

```bash
pip install -e .                          # core only
pip install -e ".[ocr,vision,web,mcp]"    # everything
```

```python
import uiautomator3 as u3

d = u3.connect()

d(text="Login").click()
d(resourceId="com.example:id/email").click()
d.send_keys("test@example.com")

# scored, ranked locators for any element
locator = d(text="Login")
print(locator.best_locator(), locator.confidence)

# structured, LLM-free element description for AI agents
print(d.ai.inspect())
```

## CLI

```bash
u3 devices                 # list attached devices
u3 doctor                  # environment diagnostics
u3 dump                    # raw UI hierarchy XML
u3 screenshot -o shot.png
u3 inspect                 # launch the web inspector (requires the `web` extra)
u3 codegen session.json --format python
u3 mcp serve                # start the MCP server (requires the `mcp` extra)
```

## Web inspector

```bash
pip install -e ".[web]"
u3 inspect                                 # backend at http://127.0.0.1:17920

cd inspector-web && npm install && npm run dev   # frontend at http://localhost:5173
```

Live device screenshot, click-to-select element overlay, and generated/scored locators —
see [docs/UIAUTOMATOR3_ARCHITECTURE.md §11](docs/UIAUTOMATOR3_ARCHITECTURE.md).

## Development

```bash
pip install -e ".[ocr,vision,web,mcp]"
pip install pytest pytest-cov ruff mypy

pytest tests/unit -v
ruff check uiautomator3 tests
ruff format uiautomator3 tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions, the mypy/numpy version-pinning
note, and how to submit changes.

## License

[MIT](LICENSE)
