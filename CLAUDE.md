# pdf-toolkit — Claude Coding Rules

These rules merge the project's required common rules and Python rules. They apply to every change in this repository.

---

## Common Rules

### Use Objects for Related Values

When multiple related values must be passed between classes or methods, bundle them into a dedicated object (e.g., DTO/Settings/Config) instead of passing many parameters.

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

### Confirm Dependency Versions

Before adding any new package, confirm the version with the user.

### Error Handling & Logging Strategy

Centralized error handler. Use structured logging (not `print`). Log at appropriate levels with context.

### Input Validation at Boundaries

Validate at API/user/file/external boundaries. Fail fast with clear messages.

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

### Type Hints

All public functions/classes/methods: typed parameters + return types. Avoid `Any` unless at a boundary.

### Centralized Configuration

Single `Settings` module driven by env vars. No `os.getenv` scattered across the codebase.

### Tests

- pytest, no network in unit tests, use `tmp_path` / fixtures.
- Use `MagicMock(spec=ClassName)` — never bare `MagicMock()`.

### Required Batch Files

- `pdf-swap-pages.bat`, `pdf-delete-page.bat` (this project's CLI entry points)
- `tools/run_tests.bat`
- `tools/run_integration_tests.bat`
- `install.bat`, `update.bat`

### Async Patterns

Use `asyncio` only for I/O-bound tasks. Never block the event loop.

### Validation

Use Pydantic at API boundaries (not used in this CLI-only project).

### Structured Logging

Use the `logging` module (configured once, centrally). Never `print()`.

---

## Project-Specific Notes

- This project is a pure CLI — no Jinja2 templates, no localization, no DB, no async.
- All PDF I/O goes through `pypdf`.
- The single error boundary for the CLI layer is `app/cli/_common.run_with_backup`.
- Backup format is locked: `backup/YYYYMMDD-HHMM-<filename>.pdf`.
- **Every new feature must be added to the wizard** (`app/cli/pdft.py` — append a `WizardOption` to `WIZARD_OPTIONS`). The wizard is the global entry point installed by `pdf-install-global`; if a feature isn't in the wizard, users with the global install can't reach it.
