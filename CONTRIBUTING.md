# Contributing to UIAutomator 3.0

Thanks for your interest in contributing. This document covers how to set up a
development environment, the conventions this codebase follows, and how to submit
changes.

## Development setup

```bash
git clone <repo-url>
cd uiautomator3
pip install -e ".[ocr,vision,web,mcp]"
pip install pytest pytest-cov ruff mypy
```

For the web inspector frontend:

```bash
cd inspector-web
npm install
npm run dev   # dev server at http://localhost:5173
```

## Running checks locally

```bash
pytest tests/unit -v                     # unit tests (no device required)
ruff check uiautomator3 tests            # lint
ruff format uiautomator3 tests           # format
mypy uiautomator3                        # type check (see note below)
```

```bash
cd inspector-web
npx tsc --noEmit                         # frontend type check
npm run build                            # frontend production build
```

**mypy note:** the project targets Python 3.8 compatibility (`python_version = "3.8"` in
`pyproject.toml`). Checking against that target requires a mypy release that still
supports pre-3.10 targets (mypy 2.0+ dropped this — use `mypy<2.0`, e.g. `1.14.1`) and a
`numpy` version whose bundled type stubs don't use syntax newer than the target Python
(numpy 2.x's stubs need Python 3.12+ to parse — use `numpy<2` for the mypy environment
specifically). If you're on a newer interpreter with a newer numpy installed, this may
fail locally with a stub-parsing error unrelated to your changes; CI pins compatible
versions and is the source of truth.

## Code conventions

- **Python 3.8 compatibility is required.** Use `Optional[X]`, `List[X]`, `Dict[X, Y]`
  from `typing` — never `X | None` or built-in generic subscripting (`list[X]`). This is
  enforced by `CLAUDE.md` and by excluding ruff's `FA100` rule (which would otherwise push
  the incompatible syntax).
- **Type hints on public APIs.** Internal helpers can be looser, but anything a user or
  another module calls should be typed.
- **No comments explaining *what* code does** — well-named identifiers should make that
  clear. Comments are for *why*: a non-obvious constraint, a workaround for a specific
  device/library quirk, or a design decision that isn't obvious from the code alone. Many
  existing modules cite the specific architecture-doc section or analysis finding that
  motivated a design choice — follow that pattern when it's genuinely useful context, skip
  it when it isn't.
- **Keep the core light.** `uiautomator3/__init__.py` and anything it imports at module
  load time must not require `cv2`, `numpy`, `pytesseract`, `fastapi`, or `mcp`. Those are
  optional extras (`ocr`, `vision`, `web`, `mcp`) — import them lazily, inside the function
  or `__init__` that actually needs them, following the pattern in
  `ocr/tesseract_provider.py` or `vision/template_provider.py`.
- **One element model.** Every locator strategy should produce/consume `UIElement` from
  `uiautomator3.elements` — don't introduce a second element representation.
- **Score, don't guess.** If you're adding a new locator strategy, it needs a uniqueness/
  stability score like the existing ones in `locator/generator.py`, not silent
  first-match-wins behavior.

See `docs/UIAUTOMATOR3_ARCHITECTURE.md` for the full module-responsibility breakdown and
`docs/UIAUTOMATOR2_ANALYSIS.md` for the predecessor-project analysis this design responds
to — most non-obvious design choices in the codebase trace back to a specific finding in
one of these two documents.

## Testing

- Unit tests (`tests/unit/`) must not require a physical device or emulator — mock
  `adbutils`/`Device` the way existing tests do (see `tests/unit/test_device.py` for the
  standard pattern).
- If you're fixing a bug that only showed up against real hardware, add a regression test
  that would have caught it with a mock, even though you found it live — that's how most
  of this project's own bugs were caught during development (see `CHANGELOG.md` and commit
  history for examples).
- New locator strategies, providers (OCR/vision), or codegen formats need both correctness
  tests and — where relevant — a defensive test for malformed/untrusted input (see
  `tests/unit/test_codegen_python.py`'s security-regression tests for the shape this
  should take).

## Submitting changes

1. Fork and branch from `master`.
2. Make your change, following the conventions above.
3. Run the full local check suite (pytest, ruff check, ruff format, and the frontend build
   if you touched `inspector-web/`).
4. Write a commit message that explains *why*, not just *what* — see the existing commit
   history for the expected tone and level of detail.
5. Open a PR. CI (`.github/workflows/ci.yml`) will run the same checks; please make sure
   they're green before requesting review.

## Reporting security issues

If you find a security vulnerability, please do not open a public issue. See the fix in
commit `101d45e` for the kind of issue this project treats as security-relevant (code
injection into generated automation scripts, unauthenticated access to device control
surfaces, etc.) — if in doubt, treat it as sensitive and report privately first.
