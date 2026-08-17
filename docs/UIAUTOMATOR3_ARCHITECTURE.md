# UIAutomator 3.0 — Proposed Architecture

This document proposes the architecture for UIAutomator 3.0, informed by
[UIAUTOMATOR2_ANALYSIS.md](UIAUTOMATOR2_ANALYSIS.md). It covers module responsibilities,
data flow, and the pipelines for UI inspection, locator generation, self-healing, OCR,
vision, the inspector, MCP, and plugins. This is a design document; implementation proceeds
phase by phase per the project spec, starting with Phase 1 only.

## 1. Guiding Principles (carried from analysis)

- **One element model.** Every locator strategy (resource-id, text, XPath, OCR, vision)
  produces and consumes the same `UIElement`, built once per hierarchy snapshot. v2's split
  between `UiObject` and `XMLElement` is not repeated.
- **Score everything.** Every generated locator carries uniqueness/stability/confidence
  scores. Nothing is "first match wins" silently.
- **Core stays light.** OCR, vision, and AI are optional plugins, imported lazily. The core
  automation engine (connect, tap, swipe, hierarchy dump, basic selectors) has no cv2/lxml/ML
  dependency requirement.
- **Bundle, don't download.** Following v2's proven fix, the device-side agent ships inside
  the Python package as a build asset, not fetched at runtime.
- **One transport abstraction, swappable backends.** The wire protocol (HTTP/JSON-RPC today)
  must not leak into the public API, so it can evolve without breaking user code.
- **Fail with structure, not stack traces.** Typed exceptions and ambiguity reports
  (candidates + recommendation + reason) are first-class, not afterthoughts.

## 2. Top-Level Module Responsibilities

```
uiautomator3/
├── client/        Public-facing Device/Session/connect() API — the thing users import
├── device/         Device abstraction, capabilities, health monitor
├── adb/            ADB device discovery/connection (wraps adbutils)
├── transport/       Transport abstraction: HTTP / WebSocket / ADB / Local backends
├── server/          Client-side management of the on-device agent process lifecycle
├── hierarchy/       Hierarchy collection + XML parsing + normalization into UIElement trees
├── elements/         UIElement dataclass, ElementTree, relationship graph
├── selectors/         Selector DSL (the `d(text=..., resourceId=...)` surface)
├── locator/          Locator object, generation, scoring, ranking, stability analysis
├── matching/         Hybrid element matching engine + confidence scoring
├── healing/           Self-healing fallback chains + healing reports
├── inspector/          Inspector backend: collectors, analyzers, exporters (server-side of web UI)
├── vision/            Optional computer-vision element detection
├── ocr/               Optional OCR provider abstraction + coordinate mapping
├── gestures/           Tap/swipe/drag/multi-touch gesture engine
├── waits/              Unified wait/retry engine (single implementation, not two)
├── apps/               App lifecycle management (install/start/stop/current/...)
├── screenshots/         Screenshot capture + format conversion
├── recording/           Interaction recorder + action timeline
├── diagnostics/         Logging, failure artifact collection, doctor checks
├── codegen/             Code generation (Python/pytest/POM/JSON/YAML) from recordings
├── ai/                  AI-ready structured inspection + action API
├── mcp/                 MCP server exposing tools to AI agents
├── cli/                 `u3` command-line entry point
├── plugins/             Plugin registration system
└── utils/               Small shared helpers (no business logic)
```

Each module exposes a narrow public interface; cross-module dependencies flow inward
toward `elements/` and `hierarchy/`, which have no dependency on `inspector/`, `ocr/`,
`vision/`, `ai/`, or `mcp/`. This is the enforcement mechanism for keeping the core light —
if `hierarchy/` ever needs to `import cv2`, that's a design violation.

## 3. Data Flow — UI Inspection Pipeline

```
                         ┌─────────────────────┐
                         │   Android Device     │
                         └──────────┬───────────┘
                                    │ transport (HTTP/JSON-RPC over ADB tunnel)
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │                    Inspector                        │
        │                                                       │
        │  HierarchyCollector ──┐                               │
        │  AccessibilityCollector├─► ElementNormalizer ─► UIElement tree
        │  WindowCollector ─────┤        (elements/)             │
        │  ScreenshotCollector ─┘                                │
        │                                                        │
        │  (lazy, only if requested/cached-miss)                 │
        │  OCRCollector ──────────► RelationshipAnalyzer          │
        │  VisionAnalyzer ────────►      │                        │
        │  BoundsAnalyzer ────────►      ▼                        │
        │                          ElementMatcher                 │
        │                                │                        │
        │                                ▼                        │
        │                        SelectorGenerator                │
        │                                │                        │
        │                                ▼                        │
        │                        ConfidenceEngine                 │
        │                                │                        │
        │                                ▼                        │
        │                       InspectionExporter                │
        └───────────────────────────────────────────────────┘
```

Each `*Collector` produces raw, source-specific data. `ElementNormalizer` is the single
place where all sources merge into `UIElement` instances — this directly replaces v2's two
separate representations (RPC objects vs. parsed XML) with one.

`OCRCollector`/`VisionAnalyzer` are **lazy**: they only run when a hierarchy-based match
fails or is explicitly requested, per the performance targets (hierarchy collection <
300ms; OCR/vision must not run on every refresh).

## 4. UIElement Model (`elements/`)

A typed dataclass (not a raw dict), matching the shape specified in the project brief:

```python
@dataclass(frozen=True)
class Bounds:
    left: int
    top: int
    right: int
    bottom: int

@dataclass
class UIElement:
    id: str
    text: Optional[str]
    content_description: Optional[str]
    resource_id: Optional[str]
    class_name: Optional[str]
    package_name: Optional[str]
    bounds: Bounds
    clickable: bool
    enabled: bool
    visible: bool
    focused: bool
    selected: bool
    checked: bool
    scrollable: bool
    parent_id: Optional[str]
    children: List[str]
    depth: int
    role: Optional[str] = None          # semantic classification, §8
    ocr_text: Optional[str] = None       # populated lazily
    visual_confidence: Optional[float] = None
    source: FrozenSet[str] = frozenset() # which collectors contributed
```

`ElementTree` wraps a list of `UIElement` plus indices (`by_id`, `by_resource_id`,
`children_of`, `siblings_of`) so relationship queries (§6) are O(1)/O(depth) instead of
v2's O(n) linear scans.

Python version note: this project targets **Python 3.8 compatibility** (per repository
convention). Use `Optional[X]`/`List[X]`/`FrozenSet[X]` from `typing`, never `X | None` or
built-in generic subscripting (`list[X]`), throughout the codebase.

## 5. Locator Generation & Scoring Pipeline (`locator/`)

```
UIElement + ElementTree
        │
        ▼
 candidate generation (one per strategy: resource_id, text, content_desc,
 class+text, xpath, relative_xpath, ocr, visual, coordinate)
        │
        ▼
 for each candidate:
   uniqueness   = 1 / (count of elements in current tree matching this locator)
   stability    = f(depends_on_index, depends_on_dynamic_attrs, resource_id_naming_pattern)
   specificity  = f(number of constraining attributes)
        │
        ▼
 composite score = weighted(uniqueness, stability, specificity)
        │
        ▼
 rank descending → LocatorSet { best, alternatives[], scores{} }
```

This is a deterministic, rule-based scoring engine (not ML) for v1 — matching the
project's Phase 5 scope. Default priority order (resource-id → accessibility/desc → unique
text → class+attrs → relative hierarchy → XPath → OCR → visual → coordinate) is the
starting weight vector, but actual ranking is re-sorted per-element based on computed
scores, not hardcoded — so a non-unique resource-id legitimately loses to unique text.

`locator.analyze_locator(locator_string)` (Phase 5/7) reuses this same scoring path against
a supplied locator rather than a generated candidate, producing the stability report shown
in the project brief.

## 6. Relationship & Spatial Engine

Built directly on `ElementTree` indices — no re-parsing per query:

- **Hierarchical**: parent, child, ancestor, descendant, sibling, preceding/following
  sibling — graph traversal over `parent_id`/`children`.
- **Spatial**: above/below/left_of/right_of/near/inside/contains/overlaps/aligned_with/
  same_row/same_column — pure geometry over `Bounds`, no device round-trip needed once a
  hierarchy snapshot is loaded.

This generalizes v2's `.right()/.left()/.up()/.down()` (which required a second live
selector query per call) into geometry computed once against the already-collected tree.

## 7. Self-Healing Architecture (`healing/`)

```
locator.click()
     │
     ▼
 primary strategy fails (ElementNotFoundError)
     │
     ▼
 HealingChain: [resource_id, accessibility_id, text, class+text,
                 relative_hierarchy, ocr, visual]
     │  (skip strategies already tried; try next in order)
     ▼
 candidate found? ──no──► raise with full HealingReport attached
     │ yes
     ▼
 confidence >= settings.self_healing_min_confidence (default 0.85)?
     │ yes
     ▼
 execute action, attach HealingReport { original, recovered_via, confidence }
```

Healing is **opt-in via `d.settings["self_healing"] = True`** (default False) — v2 has no
equivalent, and this is new surface area that must not silently change behavior for
existing-style literal selectors unless explicitly enabled.

## 8. Semantic Role Classification

A small rule table (`elements/roles.py`) maps `(class_name, clickable, checkable, text
presence, children)` → role (`button`, `input`, `text`, `checkbox`, ...), consulted by the
`ElementNormalizer`. Explicitly rule-based, not classifier-based, for v1 — matches
"Do not depend exclusively on class names" (checks clickable/checkable/editable state
too) while staying deterministic and fast (<100ms budget).

## 9. OCR Architecture (`ocr/`)

```python
class OCRProvider(Protocol):
    def detect_text(self, image: Image) -> List[OCRTextRegion]: ...
```

`OCRCollector` calls the configured provider only when triggered (hierarchy match failed,
or `d.ocr(...)` used explicitly), maps returned pixel regions onto the current
`ElementTree` bounds (nearest-bounds-containment), and emits synthetic `UIElement`s with
`source={"ocr"}` when no hierarchy element occupies that region (e.g. canvas-rendered
text). Providers (`TesseractProvider`, `MLKitProvider`, ...) live behind extras
(`pip install uiautomator3[ocr]`) — never imported by core modules.

## 10. Vision Architecture (`vision/`)

Same provider-pattern shape as OCR: a `VisionProvider` protocol, a default OpenCV
template-matching implementation (directly reusing the proven approach from v2's
`image.py`, since it already works well and has no new-dependency cost beyond what v2
already required), and room for a pluggable ML-based detector later. Template library
lookup and matching happen lazily, never on a plain hierarchy refresh.

## 11. Inspector Architecture (Web UI)

```
Browser (React + TS + Vite)
   │  WebSocket (live tree/screenshot stream) + REST (on-demand actions)
   ▼
FastAPI backend (inspector/server.py)
   │  in-process calls
   ▼
uiautomator3.client.Device
   │  transport/
   ▼
Android Device
```

The backend does not reimplement inspection logic — it's a thin FastAPI layer over the same
`Inspector` pipeline (§3) used by the Python API, so `d.inspect()` from a script and the web
inspector return structurally identical data. This avoids v2's situation where the
inspector (`uiautodev`) is an entirely separate project that could drift from the library.

WebSocket pushes incremental tree/screenshot updates; REST handles one-shot actions
(click-to-select, export, codegen). Frontend renders the overlay/tree/locator-panel layout
specified in the project brief (§33–36).

## 12. MCP Architecture (`mcp/`)

A thin tool-registration layer over the same `Device`/`Inspector`/`ai` APIs — MCP tools are
literally 1:1 wrappers (`find_element` → `device.find(...)`, `inspect_screen` →
`inspector.inspect()`), so there is no parallel logic to maintain. Tools return the
structured JSON shape from §63 of the project brief (role/label/locator/confidence), never
raw screenshots alone. Runs as an opt-in server (`u3 mcp serve`), not started implicitly by
importing the library.

## 13. Plugin Architecture (`plugins/`)

```python
u3.plugins.register(kind="ocr_provider", name="tesseract", factory=TesseractProvider)
```

A single registry (`plugins/registry.py`) keyed by plugin kind
(`ocr_provider`/`vision_provider`/`locator_strategy`/`ai_provider`/`device_provider`/
`codegen_target`/`reporter`), consulted by the relevant module at the point it needs an
implementation (e.g. `ocr/` looks up `ocr_provider` plugins). This generalizes v2's
`_PluginMixIn` lazy-`cached_property` pattern into something third parties can extend
without editing core files.

## 14. Transport Abstraction

```python
class Transport(Protocol):
    def request(self, method: str, params: dict, timeout: float) -> Any: ...
    def connect(self) -> None: ...
    def close(self) -> None: ...
```

`HTTPTransport` (today's HTTP/JSON-RPC-over-ADB-tunnel, directly reusing v2's proven
approach), `WebSocketTransport` (for future push-based hierarchy/event streaming),
`ADBTransport` (raw shell, used by `apps/` per v2's lesson that app-lifecycle control must
work independent of the agent server), and `LocalTransport` (for emulator/testing without a
real device) all implement this. `client/` and `device/` depend only on the `Transport`
protocol, never on a concrete backend — this is what lets the wire protocol evolve without
a public API break, addressing a gap v2 doesn't need (it only ever had one transport) but
which the project brief explicitly requires.

## 15. Device-Side Agent

Following the single strongest lesson from the v2 analysis (§2, §15.6): the agent ships
**inside the pip wheel** as a build asset and is pushed via `adb push` + MD5-checked
skip-if-unchanged, never downloaded from the network at connect time. Internally modularized
(hierarchy / accessibility / input / window manager / screenshot / app control /
diagnostics) but that internal structure is an implementation detail behind the Transport
protocol — the Python side never depends on the agent's internal module boundaries, only on
its RPC surface.

## 16. What Phase 1 Actually Delivers

Per the project brief, Phase 1 is architecture only — no UI automation yet. Concretely:

- Repository structure (§65 of the brief, mirrored under `uiautomator3/`)
- `pyproject.toml`, package skeleton with the module layout from §2 above (empty/minimal
  modules, not stubs pretending to be complete)
- `exceptions.py` with the typed hierarchy from the brief (§56), avoiding v2's
  `BaseException`-shadowing mistake
- `config`/logging scaffolding
- `adb/` wrapping device discovery (via `adbutils`, matching v2's proven choice)
- `transport/` with the `Transport` protocol and a first `ADBTransport` implementation
  sufficient for `u3.devices()` and `u3.doctor()` to work against real hardware
- `u3.connect()` returning a `Device` object with no automation methods yet beyond what's
  needed to prove the transport works (e.g. a ping/health check)

Explicitly **not** in Phase 1: hierarchy dumping, selectors, gestures, screenshots — those
are Phase 2/3 per the brief's own phase boundaries. No placeholder implementations of later
phases will be created ahead of schedule.
