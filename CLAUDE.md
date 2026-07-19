# pdf-toolkit — Claude Coding Rules

These rules merge the project's required common rules and Python rules. They apply to every change in this repository.

Source rules: `D:\GIT\BenjaminKobjolke\claude-code\coding-rules` (`COMMON_RULES.md` + `AI_RULES.md` + `PYTHON_RULES.md`). Re-run `/coding-rules:add-or-update` to resync. Jinja2/localization rules omitted — this project has no web layer.

---

## Code Analysis

After implementing new features or making significant changes, run the code analysis:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\pdf-toolkit'; cmd /c '.\tools\analyze_code.bat'"
```

Results are written to `code_analysis_results/*.csv`. To auto-fix Ruff issues first, run `tools\fix_ruff_issues.bat` (preview with `tools\fix_ruff_issues_dry_run.bat`). Fix any reported issues before committing.

---

## Common Rules

### Use Objects for Related Values

When multiple related values must be passed between classes or methods, bundle them into a dedicated object (e.g., DTO/Settings/Config) instead of passing many parameters.

### No Bag-of-Keys Returns at Module Boundaries

Public manager/service/repository methods that cross a module boundary return a typed object (DTO/value object/model), never a raw string-keyed `dict`. Lists vs single must be obvious from type + name (`get_thing() -> Thing | None` vs `get_things() -> list[Thing]`). Distinguish absent (`None`) from empty (`[]`). Internal private dict juggling inside one method is fine.

### Reuse Existing Models Before Inventing Array Shapes

Before designing a new DTO, grep for an existing domain class that already owns the same data and use it. A `get_xxx_object()` alongside a legacy dict-returning method is an acceptable migration step; delete the dict version once consumers migrate.

### Tests Pin the Shape Before the Refactor

When converting a dict return to a typed object, write a characterization test first against the current API, confirm it passes, then refactor; the same test stays green afterward. TDD applied to refactors.

### Test-Driven Development for Features and Bug Fixes

1. Write tests first
2. Run the tests and confirm they fail
3. Implement the change or fix
4. Run the tests again and confirm they pass

### Integration Tests

Every project must include integration tests in addition to unit tests.

### Test Runner Scripts

- `tools/run_tests.bat` — runs unit tests
- `tools/run_integration_tests.bat` — runs integration tests

### Prefer Type-Safe Values

Use strong, explicit types instead of loosely typed values.

### String Constants

Centralize string constants in a dedicated module/class. Do not scatter raw strings.

### README.md is Mandatory

Project name, description, install, usage, dependencies.

### Don't Repeat Yourself (DRY)

Extract shared logic into helpers or base abstractions. Use constants for repeated values.

### Derive, Don't Duplicate — One Value Owns the Derivation

When one value strictly determines another (true functional dependency), pass only the determinant and derive the rest — never thread both side-by-side through call sites. The richer type owns the relationship via a pure, cheap, exhaustive `match`/getter. Don't force a derivation when the relationship is many-to-many or genuinely independent.

### Keep It Simple (KISS)

Simplest solution that works. YAGNI — no interface with one impl, no factory for one product, no config for a constant. Boring over clever. Deletion over addition.

### Reusable Tooling

Before building project-specific infrastructure scripts (audits, codemods, build helpers, lint checks), check the matching language's `*_setup_files/` folder in the coding-rules repo for an existing equivalent. If you build a new one, prove it on real data, copy it back into `*_setup_files/tools/`, and document it in that language's `*_RULES.md` so the next project picks it up.

### Confirm Dependency Versions

Before adding any new package, confirm the version with the user.

### Error Handling & Logging Strategy

Centralized error handler. Use structured logging (not `print`). Log at appropriate levels with context.

### Centralized Logger — Single Off Switch

Route all logging through one logger class (`AppLogger` / `app_logger.py`). Never call `print`/`logging.getLogger(...)` at call sites. Callers pass a level; the logger decides emission from central config. Built-in output appears in exactly one file — the logger impl. One toggle disables/level-filters/redirects all logging.

### Comments Explain Why, Not What

Comment intent and non-obvious reasoning, not a restatement of code. Document why a workaround exists, a constraint not visible locally. Prefer self-documenting code. Delete stale comments.

### Input Validation at Boundaries

Validate at API/user/file/external boundaries. Fail fast with clear messages.

### No Hardcoded Environment Values

Never hardcode paths, hostnames, IPs, ports, base URLs in code. Read from central config with a committed `.example` template. Distinct from secrets — this is about portability.

### Maximum File Length — 300 Lines

Split files when they exceed 300 lines. Group extractions by domain, not by type.

### Naming Conventions

- Files: `snake_case`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Security Baseline

Never commit secrets. Escape output. Parameterized queries / ORM only. Validate input. Keep deps updated.

### No God Classes

Warning signs: >5 public methods, >4 constructor deps, methods spanning unrelated domains, or "Manager/Handler/Service/Helper" catch-all names. Split by responsibility.

### Self-Describing Classes

When behavior depends on which fields a class has, the class declares those fields through a contract — never hardcode field lists in consuming code.

### Inject Collaborators, Don't Fold Dependencies In

Prefer injected collaborators (constructor injection) over fold-in reuse (mixins/traits/multiple inheritance) — folding merges all the helper's dependencies into the host. Reserve fold-in for stateless, dependency-free helpers. Never instantiate a service inside a method (`new`/direct construction) — it hides the dependency and blocks test substitution. Collapse config-callback swarms (many one-line overridable getters) into one value object handed to the base.

---

## Python Rules (uv)

### Project Setup

- `pyproject.toml` is the single source of truth. Commit `uv.lock`.
- Python pinned `>=3.11,<3.13`.
- Manage deps with `uv add ...`.

### Toolchain (CI must run all)

- `ruff check`
- `ruff format --check`
- `mypy`

### GUI Framework

Desktop GUI uses **PySide6** (Qt for Python). Install the latest — don't pin old. (`app/gui/` is the desktop layer.)

### Database

If a DB is needed, use SQLAlchemy ORM — not raw SQL. (Settings backend is sqlite-based.)

### Type Hints

All public functions/classes/methods: typed parameters + return types. Avoid `Any` unless at a boundary.

### Centralized Configuration

Single `Settings` module driven by env vars. No `os.getenv` scattered across the codebase.

### Tests

- pytest, no network in unit tests, use `tmp_path` / fixtures.
- Use `MagicMock(spec=ClassName)` — never bare `MagicMock()`.

### Required Batch Files

- `pdf-swap-pages.bat`, `pdf-delete-page.bat`, `pdf-insert-page.bat`, `pdf-extract-page.bat` (this project's CLI entry points)
- `tools/run_tests.bat`
- `tools/run_integration_tests.bat`
- `install.bat`, `update.bat`

### Async Patterns

Use `asyncio` only for I/O-bound tasks. Never block the event loop.

### Validation

Use Pydantic at API boundaries (not used in this CLI-only project).

### Structured Logging

Route all logging through `AppLogger` (`app_logger.py`) wrapping `logging`/`structlog`. Feature code calls `AppLogger`, never `logging.getLogger(...)` or `print()`.

### Self-Describing Classes

Implement via Protocol/ABC (`get_searchable_fields()`) for simple cases, or dataclass field metadata for declarative per-field control.

---

## AI Workflow Rules (always apply)

Language-independent; run each step as the named skill, don't reimplement.

### Feature / Change Workflow

After the user approves a plan:

```
plan approved
  → /plan:dry            check approved plan for DRY/consolidation BEFORE code
  → /plan:dry-checked    reload + review the DRY-adjusted plan
  → /convention:check    scan for existing patterns/components to reuse
  ─────────────────────  DRY GATE — must clear to proceed
  → restate Definition-of-Done aloud
  → implement
  → /dry:check           post-implementation DRY audit
  → /verify:after-change run tests + code analysis
```

**DRY gate** (precondition for implementing — restate aloud when you start): `/plan:dry` ran and adjusted the plan; `/plan:dry-checked` confirmed it; `/convention:check` found utilities to reuse. If mid-implementation you'd add a helper/type/pattern the gate would catch, stop and re-clear it.

**Definition of Done** — state in chat before the first edit: Scope (what changes / what doesn't); Reuse (existing fn/component + path); DRY gate cleared; `/dry:check` clean; `/verify:after-change` green.

### Bug-Fix Workflow

Shorter (no plan-DRY phase): `bugs:fix → /verify:after-change`.

---

## Accepted Rule Exceptions

- No root `start.bat` (Python rules require one): `pdft.bat` (CLI wizard) and `FastFileViewer.bat` (GUI) are the entry points instead.

## Project-Specific Notes

- CLI + PySide6 desktop GUI (`app/gui/`). Settings persist in a sqlite backend. No Jinja2, no localization, no web layer.
- All PDF I/O goes through `pypdf`.
- The single error boundary for the CLI layer is `app/cli/_common.run_with_backup`.
- Backup format is locked: `backup/YYYYMMDD-HHMM-<filename>.pdf`.
- **Every new feature must be added to the wizard** (`app/cli/pdft.py` — append a `WizardOption` to `WIZARD_OPTIONS`). The wizard is the global entry point installed by `pdf-install-global`; if a feature isn't in the wizard, users with the global install can't reach it.
