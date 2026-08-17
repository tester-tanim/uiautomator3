# UIAutomator 3.0

Next-generation Android automation framework focused on precision UI inspection, robust
element identification, and reliable mobile automation — designed as a successor to
[openatx/uiautomator2](https://github.com/openatx/uiautomator2).

See [docs/UIAUTOMATOR3_ARCHITECTURE.md](docs/UIAUTOMATOR3_ARCHITECTURE.md) for the full
design and phase plan, and [docs/UIAUTOMATOR2_ANALYSIS.md](docs/UIAUTOMATOR2_ANALYSIS.md)
for the predecessor-project analysis this design responds to.

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
