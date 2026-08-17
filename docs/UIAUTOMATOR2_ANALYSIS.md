# UIAutomator2 Architecture Analysis

This document analyzes the current `openatx/uiautomator2` codebase (as vendored at
`c:\Users\Tanim\Documents\uiautomator2`) to inform the design of UIAutomator 3.0. All
findings below are based on direct reading of the source, not assumptions from naming.

## 1. Package Structure

Core package `uiautomator2/` (~4,900 LOC across top-level modules):

| File | LOC | Responsibility |
|---|---|---|
| `__init__.py` | 983 | Public API: `_Device`, `_AppMixIn`, `_PluginMixIn`, `Device`, `Session`, `connect()` |
| `core.py` | 336 | Transport: pushes/launches `u2.jar`, HTTP+JSON-RPC over ADB tunnel |
| `base.py` | 195 | `_BaseClient` — device discovery, `shell()`, `settings`, `jsonrpc` proxy |
| `abstract.py` | 85 | ABCs decoupling `xpath.py`/`watcher.py` from concrete `Device` |
| `_selector.py` | 580 | `Selector`/`UiObject` — legacy `UiSelector`-bitmask query API |
| `_proto.py` | 17 | Shared constants (`SCROLL_STEPS`, `HTTP_TIMEOUT`, `Direction`) |
| `_input.py` | 197 | Custom AdbKeyboard IME for reliable Unicode text input |
| `xpath.py` | 772 | lxml-based XPath querying (`XPathEntry`, `XMLElement`, `PageSource`) |
| `settings.py` | 105 | Typed dict-like config (`wait_timeout`, `max_depth`, ...) |
| `swipe.py` | 60 | Directional swipe helper |
| `watcher.py` | 324 | Two parallel background polling/trigger systems |
| `image.py` | 353 | OpenCV/`findit` template matching, SSIM |
| `screenrecord.py` | 141 | Video recording via legacy minicap websocket |
| `exceptions.py` | 64 | Exception hierarchy |
| `utils.py` | 294 | Grab-bag utilities |
| `agent_cli/` | ~2000+ | Host-side CLI+HTTP daemon (`u2cli`), NOT a device-side agent |

Plugins (`xpath`, `watcher`, `image`, `screenrecord`, `swipe_ext`) attach to `Device` via
lazy `cached_property` in `_PluginMixIn`, keeping the core free of heavy optional deps
(cv2, lxml) until used.

## 2. Device-Side Architecture

**No bundled "ATX agent."** The historical Go `atx-agent` + minicap/minitouch +
instrumentation-APK architecture has been archived (`_archived/init.py`, dead code, not
imported) in favor of a single Java server, `u2.jar`.

- `launch_uiautomator()` runs `CLASSPATH=/data/local/tmp/u2.jar app_process / com.wetest.uia2.Main -p {port}` via a persistent `adb shell` stream.
- `u2.jar` and a companion IME APK (`app-uiautomator.apk`) are **bundled in the pip
  package** as build-time assets, not downloaded at connect time — a meaningful
  reliability improvement over the old download-on-first-connect model.
- Transport is **HTTP+JSON-RPC over an ADB TCP tunnel**: `AdbHTTPConnection` overrides
  `.connect()` to use `adbutils.create_connection()` instead of a real socket.
  `_jsonrpc_call` posts to `/jsonrpc/0` and maps device-side error strings to typed
  exceptions.
- Readiness polled via `GET /ping` → `b"pong"`.
- No minicap/minitouch in the live path (screenshots use device-side JPEG encode or
  `adb screencap` fallback).
- `agent_cli/` is unrelated to the device — it's a host-side caching daemon
  (`127.0.0.1:17913`) so repeated `u2cli` shell invocations don't re-establish a
  `Device`/JVM connection each time.

## 3. Python Client Architecture

- `connect()` → `connect_usb()` → resolves an `adbutils.AdbDevice` → constructs `Device`.
- `Device(_Device, _AppMixIn, _PluginMixIn, InputMethodMixIn, _DeprecatedMixIn)`, built on
  `_BaseClient` → `BasicUiautomatorServer` → `AbstractUiautomatorServer` (ABC).
- Init sequence: wait for ADB device → acquire per-`(serial, port)` class-level lock →
  push/start `u2.jar` → register `atexit` cleanup.
- `jsonrpc` property returns a dynamic proxy (`__getattr__` captures method name) — free-form
  RPC dispatch with **no schema/type checking** client-side.
- Built-in transport-level self-healing: `jsonrpc_call` catches connection errors, restarts
  the uiautomator server, and retries once.
- `Session` wraps a `Device` bound to one package/pid; raises `SessionBrokenError` if the
  tracked pid dies (checked via `ps` before each call, not push-based).
- **Fully synchronous** — no async/await anywhere; concurrency only via daemon threads with
  hand-rolled `Event`/`Lock` coordination, reimplemented independently in several places.

## 4. Selector/Locator System

`Selector(dict)` directly encodes the Android `UiSelector` bitmask wire protocol — each
field (`text`, `resourceId`, `instance`, ...) sets a mask bit; **all matching logic runs
device-side** in the Java uiautomator server. There is no client-side scoring, ranking, or
fuzzy matching.

- `UiObject` (returned by `d(text=...)`) has **no ambiguity resolution**: for singular
  operations it implicitly uses the first device-determined match. Explicit indexing
  (`d(text="x")[2]`) exists but nothing automatic.
- `.right()/.left()/.up()/.down()` implement a hand-rolled nearest-neighbor geometric query
  against a *second, independently specified* selector — the only relationship-aware query
  in the codebase, and it's O(n) with a custom distance function, not general
  parent/sibling/ancestor traversal.
- `.parent()` is explicitly `NotImplementedError` (Android's `UiObject` API has no
  `getParent()`).
- `.wait()`/`.wait_gone()` delegate to a **blocking device-side RPC**
  (`waitForExists`/`waitUntilGone`).

## 5. XPath Implementation

Uses **lxml** for real XPath 1.0 + EXSLT regex support (`re:match()`).

- `strict_xpath()` is a useful shorthand-expansion DSL: `"@resid"` → resource-id lookup,
  `"^regex"` → regex OR across text/desc/resource-id, `"%contains%"` → substring match,
  bare string → implicit OR across three attributes. This is a **fixed heuristic**, not a
  ranked/confidence-scored match.
- `PageSource.root` rewrites lxml node tags from `class` attributes (`<node
  class="android.widget.TextView">` → tag `TextView`), enabling `//TextView`-style XPath.
- **No automatic hierarchy caching**: every `.exists`/`.click()`/`.wait()` re-dumps the
  hierarchy unless the caller explicitly passes a cached `source=`.
- `__and__`/`__or__` support set intersection/union of two independently-evaluated XPath
  queries — real but limited compositionality.
- `DeviceXPathSelector.wait()` is a **Python-side polling loop** (`sleep(0.2)`), architecturally
  inconsistent with `_selector.py`'s device-side blocking wait — two selector systems, two
  different wait strategies.
- `fallback(func)` lets `.click()` invoke a user callback on not-found — a manual escape
  hatch, not automatic alternate-selector retry.
- `scroll_to()` has an acknowledged FIXME: no detection of reaching the end of a scrollable
  list, so it can spin for the full `max_swipes` budget unnecessarily.

## 6. Hierarchy Dumping

`dump_hierarchy()` delegates to `jsonrpc.dumpWindowHierarchy(...)`, entirely device-side,
with `@retry(HierarchyEmptyError, tries=3, delay=1)` working around a known device
flakiness (empty `<hierarchy/>` dumps). Returns a raw XML **string** — no typed tree model
at the `Device` level. Normalization into objects only happens downstream in `xpath.py`.

**Critical structural finding:** the selector system (`_selector.py`, RPC-object-based:
`objInfo`, `objInfoOfAllInstances`) and the XPath system (`xpath.py`, parsed-XML-based)
query the hierarchy through **two entirely separate code paths and data
representations**. There is no unified element model.

## 7. Screenshots

`_Device.screenshot()`: primary path is device-side JPEG encode via
`jsonrpc.takeScreenshot(1, 80)` (base64 → PIL); falls back to `adbutils`
`screencap`-based screenshot if the RPC returns `None`, or always for multi-display
(`display_id`). Optional PIL/OpenCV format conversion. `image.py`'s `ImageX` adds template
matching (`findit`/OpenCV `matchTemplate`) and SSIM comparison — real but limited to
template-match vision, no OCR, no ML-based detection.

## 8. Gestures/Input

Fairly complete: `click`/`double_click`/`long_click`, low-level `touch.down/move/up`,
`swipe`/`swipe_points`, `drag`, `press`/`long_press` (key names or keycodes). True
multi-touch exists via `UiObject.gesture()`/`.pinch_in()`/`.pinch_out()`, but scoped to a
selector-relative gesture only.

Text input is unusually elaborate: a custom **AdbKeyboard IME APK** driven via
`am broadcast`, because standard `setText`/clipboard approaches are unreliable for
Unicode/IME-dependent apps. Two-tier fallback: clipboard-paste first, IME broadcast on
failure.

## 9. Waits

Two independent, inconsistent mechanisms (see §5/§4): device-blocking RPC wait
(`_selector.py`) vs. Python polling loop (`xpath.py`). Configuration lives in
`settings.py`'s `Settings` (type-checked assignment, deprecated-key shims,
`operation_delay` pre/post-sleep around click/swipe/drag/press). `retry` decorator usage is
ad hoc per-function, not a general configurable retry policy.

## 10. App Management

Almost entirely raw `adb shell` / `adbutils` calls, **not** the jsonrpc server — this is
deliberate, since app lifecycle control must keep working even if the uiautomator server
itself is down (explicitly noted in a code comment). `app_start` uses `monkey` or
`am start`; `app_stop`/`app_clear`/`app_install` delegate to `adbutils`; `app_uninstall`
shells `pm uninstall`; `app_auto_grant_permissions` regex-parses `dumpsys package` output
(brittle, SDK 23+ only, explicit TODO for older Android).

## 11. Watchers

**Two parallel, competing implementations**: `Watcher` (`d.watcher`) and `WatchContext`
(`d.watch_context()`), each with independently coded thread/lock/`Event` lifecycle and
xpath-matching logic against a dumped hierarchy. `WatchContext` adds chained
`.when(a).when(b)` conditions and built-in popup-dismiss patterns
(Chinese/English "Agree"/"继续使用"/etc.). `Watcher` is the only place hierarchy dumping
is reused across multiple checks within one poll cycle.

## 12. Exception Hierarchy

```
BaseException (custom — shadows the Python builtin within this module, and propagates via `from uiautomator2.exceptions import *`)
├── DeviceError
│   ├── AdbShellError, ConnectError, AdbBroadcastError, InputIMEError
│   ├── HTTPError → HTTPTimeoutError
│   └── UiAutomationError → UiAutomationNotConnectedError, InjectPermissionError,
│         APKSignatureError, LaunchUiAutomationError, AccessibilityServiceAlreadyRegisteredError
└── RPCError
    ├── RPCUnknownError, RPCInvalidError, HierarchyEmptyError, RPCStackOverflowError
    └── NormalError → XPathElementNotFoundError, SessionBrokenError,
          UiObjectNotFoundError, AppNotFoundError
```

## 13. Testing Approach

**Pure unit tests with mocks only — no real-device/integration tests** in this repo.
`test_xpath.py` (164 lines) has solid coverage of XPath shorthand expansion and click/
exists/wait against a static hardcoded hierarchy fixture. `test_agent_cli.py` (976 lines,
the largest test file) covers the host-side CLI daemon extensively.

**Notable gap: zero direct unit tests found for `_selector.py`/`UiObject`** — the
`d(text=...)` API that is arguably the library's primary value proposition — nor for
`watcher.py`, `image.py`, `screenrecord.py`, `swipe.py`.

## 14. Known Weaknesses / Technical Debt

- **Dead code path**: `screenrecord.py` references `self._d.address`, an attribute that
  does not exist anywhere on `Device`/`_BaseClient` — this method would raise
  `AttributeError` on first real use. Leftover from the atx-agent/minicap era.
- **Duplicate watcher systems** (`Watcher` vs `WatchContext`) — overlapping responsibility,
  separately maintained thread lifecycles.
- **Two incompatible selector/query subsystems** (`_selector.py` vs `xpath.py`) with no
  shared element abstraction, different `.info` shapes, different wait strategies.
- **Stale CLI/docs referencing atx-agent** even though the connect path no longer uses it
  (`__main__.py` help text and `cmd_purge` still target atx-agent/minicap/minitouch).
- **`_archived/` directory** (~1,200 LOC) is the pre-rewrite download-on-connect
  implementation, kept for reference but adding repo surface area.
- Explicit `FIXME` (incomplete scroll-to-bottom detection) and `TODO`s (no Android ≤5.1
  support, an acknowledged API smell around `wait_timeout`) left in place.
- **Unbounded global state**: a class-level lock dict (`BasicUiautomatorServer._locks`)
  keyed by `(serial, port)` never evicts entries; `utils.cache_return` has no
  expiry policy (usage sites not exhaustively verified).
- **`exceptions.BaseException` shadows the Python builtin**, propagated via `import *`.
- **Fully synchronous, no structured concurrency** — daemon threads with hand-rolled
  `Event`/`Lock` coordination reimplemented independently per feature (watchers,
  screenrecord, ADB stream reading).
- **No typed/structured data models** anywhere — hierarchy nodes, selector info, and RPC
  results are raw `dict`/`str`/lxml elements, not dataclasses or a UIElement model.
- **No OCR support** — `image.py` is template-matching (OpenCV/`findit`) and SSIM only.
- **No self-healing or confidence-ranked selectors** — matching is strictly literal,
  first-match-wins for singular operations. The only automatic recovery is
  transport-level (restart uiautomator server and retry once on connection error), not
  selector-level.
- **No bundled web/GUI inspector** — the inspector (`uiautodev`) is a fully separate,
  optional PyPI package by the same author, not part of this repo.
- **Relationship/sibling queries are minimal**: only geometric nearest-neighbor
  (`.right()/.left()/.up()/.down()`) against an independently specified second selector;
  no general ancestor/descendant/sibling traversal; `.parent()` unimplemented.

## 15. Opportunities for UIAutomator 3.0

Directly motivated by the findings above:

1. **Unify the element model.** Replace the `UiObject` vs `XMLElement` split with a single
   normalized `UIElement` built from one hierarchy dump, shared by every locator strategy.
2. **Add confidence/stability scoring to locators** — nothing in v2 ranks or scores
   selector quality; this is the single biggest capability gap relative to the UIAutomator
   3.0 vision.
3. **Add real self-healing** — v2's only automatic recovery is transport-level; there is no
   alternate-selector fallback chain when a locator legitimately stops matching.
4. **Consolidate watchers into one implementation** with one thread/lifecycle model.
5. **Introduce a typed data model** (dataclasses) for elements, device info, and app info
   instead of raw dicts/strings, while keeping the core dependency-light.
6. **Keep the "bundle the agent in the package" lesson** — v2's move from
   download-on-connect to bundled `u2.jar` was a real reliability win; UIAutomator 3.0's
   device-side agent should follow the same principle.
7. **Keep OCR/vision optional** — v2 already demonstrates the value of lazy `cached_property`
   plugin attachment to keep heavy deps (cv2, lxml) out of the core import path; extend
   this pattern to OCR/vision/AI modules.
8. **Preserve the useful parts**: `strict_xpath()`'s shorthand DSL, the AdbKeyboard IME
   text-input fallback chain, and bundling the device-side binary in the wheel are all
   worth carrying forward conceptually into the new architecture.
