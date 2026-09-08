# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.0.0/); this project has not yet made a
tagged release, so everything to date is grouped under Unreleased.

## [Unreleased] - 0.1.0

Initial implementation, built phase by phase per `docs/UIAUTOMATOR3_ARCHITECTURE.md`.

### Added

- **Core** (`client`, `device`, `adb`, `transport`): `u3.connect()`/`u3.devices()`, ADB-backed
  transport, gestures (tap/long-press/swipe/drag/key press), app lifecycle management
  (install/uninstall/start/stop/current), screenshot capture, `u3 doctor` diagnostics.
- **UI inspection** (`hierarchy`, `elements`): `uiautomator dump`-based hierarchy collection,
  a single normalized `UIElement`/`ElementTree` model shared by every locator strategy,
  semantic role classification, and relationship/spatial queries (parent/child/sibling,
  above/below/left_of/right_of/etc.).
- **Selectors & locators** (`selectors`, `locator`): `d(text=..., resourceId=...)` query
  engine, the fluent `Locator` object (click/wait/assertions, auto-targeting the nearest
  clickable ancestor for real tap accuracy), rule-based locator candidate generation and
  scoring (uniqueness/stability/specificity), and `d.analyze_locator()` stability reports.
- **XPath** (`selectors.xpath`): optional full XPath 1.0 evaluation through `lxml`, exposed
  as `find_all_xpath(tree, expression)` and the lazy `d.xpath(expression)` locator, with
  Android attribute names and class-name shorthand such as `//TextView`.
- **Self-healing** (`healing`): opt-in (`d.settings["self_healing"] = True`) automatic
  locator recovery from a remembered element snapshot when a literal selector stops
  matching.
- **OCR & vision** (`ocr`, `vision`): `d.ocr(text)` (Tesseract-backed) and
  `d.visual(template)`/`d.find_visual()` (from-scratch multi-scale OpenCV template
  matching), both lazily imported and fully optional.
- **Web inspector** (`inspector`, `inspector-web/`): FastAPI + WebSocket backend over the
  same inspection pipeline used from Python; React/TypeScript/Vite frontend with a
  three-panel layout (device tree, live preview with click-to-select overlay, element
  details + generated locators).
- **Recording & code generation** (`recording`, `codegen`): `d.start_recording()`/
  `stop_recording()` captures gesture/selector actions; generators emit Python, pytest,
  Page Object Model, JSON, YAML, Robot Framework, or a raw action script.
- **AI & MCP** (`ai`, `mcp`): `d.ai.inspect()`/`find()`/`click()`/`type()` expose
  role/label/locator/confidence per element via deterministic token-overlap matching (no
  LLM call); an opt-in MCP server (`u3 mcp serve`) wraps the same APIs as tools for AI
  agents, with `run_script` (raw shell) gated behind an explicit `--allow-shell` flag.
- **Performance** (`utils`): short-TTL caching of hierarchy dumps and screenshots
  (`d.settings["hierarchy_cache_ttl"]`/`["screenshot_cache_ttl"]`), invalidated
  automatically after any gesture or selector action.
- **CLI** (`cli`): `u3 devices|doctor|version|dump|screenshot|inspect|codegen|mcp serve`.
- CI: GitHub Actions running the test suite across Python 3.8-3.12, ruff lint/format,
  mypy, and the inspector frontend build.

### Security

- Fixed a code-injection vulnerability in `codegen/python_generator.py` where a
  hand-crafted or tampered recording JSON file could inject arbitrary Python into
  generated automation scripts via an unvalidated `selector_criteria` dict key. Keys are
  now required to be valid Python identifiers; the Robot Framework and raw-script
  generators received analogous newline-injection hardening.

### Known limitations

- No device-side agent yet - hierarchy/gesture/screenshot operations go through
  `uiautomator dump` and plain `adb shell input`/`screencap` rather than a bundled
  JSON-RPC service; this means no fast device-side JPEG screenshot encoding.
- `matching/`, `plugins/`, `server/`, and `waits/` are placeholder packages: their
  intended scope already exists elsewhere (matching in `locator/`, provider-pattern
  plugin points in `ocr/`/`vision/`, waits in `selectors/locator_object.py`) but no
  standalone module has been built yet.
- No screen recording (video), diagnostics failure-artifact bundling, or state-based UI
  model yet.
