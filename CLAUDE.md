# Version
2

# Coding Rules (Pointer)

This project's rules live in two files in the project root:

- `CODING_RULES.md` — code quality and conventions. BINDING for all code work in
  this repository, always.
- `IMPLEMENTATION_FLOW.md` — the end-to-end flow to follow when planning and
  implementing a change (checks, gates, Definition of Done).

MANDATORY: Before writing or editing ANY code, you MUST Read BOTH files in full
**in the current session**. Do not rely on memory of a previous session, a
summary, or partial reads.

If you are about to make a code change and have not read both files in this
session: STOP, read them, then continue.

An external tool may orchestrate the implementation itself. When a skill or run
states that the implementation is orchestrated, ignore `IMPLEMENTATION_FLOW.md`
entirely — the orchestrator runs those steps as its own phases. `CODING_RULES.md`
stays binding either way.

Do not inline rules back into this file and do not use `@import` for either file —
they are intentionally referenced, not imported.

# pdf-toolkit

## Code Analysis

After implementing new features or making significant changes, run the code analysis:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\pdf-toolkit'; cmd /c '.\tools\analyze_code.bat'"
```

Results are written to `code_analysis_results/*.csv`. To auto-fix Ruff issues first, run `tools\fix_ruff_issues.bat` (preview with `tools\fix_ruff_issues_dry_run.bat`). Fix any reported issues before committing.

## Accepted Rule Exceptions

- No root `start.bat` (Python rules require one): `pdft.bat` (CLI wizard) and `FastFileViewer.bat` (GUI) are the entry points instead.

## Project-Specific Notes

- CLI + PySide6 desktop GUI (`app/gui/`). Settings persist in a raw `sqlite3` key-value store by choice, not SQLAlchemy. No Jinja2, no localization, no web layer.
- Required CLI entry batch files: `pdf-swap-pages.bat`, `pdf-delete-page.bat`, `pdf-insert-page.bat`, `pdf-extract-page.bat`; other entry/setup files include `pdft.bat`, `FastFileViewer.bat`, `install.bat`, and `update.bat`.
- All PDF I/O goes through `pypdf`.
- Heavy libraries not needed to display a document (`pypdf`, `img2pdf`, `markdown`, `send2trash`, `asyncio`) stay imported inside the functions that use them; `app/gui/main.py` must not import `MainWindow` at module level. `tests/integration/test_startup_imports.py` guards both rules.
- The single error boundary for the CLI layer is `app/cli/_common.run_with_backup`.
- Backup format is locked: `backup/YYYYMMDD-HHMM-<filename>.pdf`.
- **Every new feature must be added to the wizard** (`app/cli/pdft.py` — append a `WizardOption` to `WIZARD_OPTIONS`). The wizard is the global entry point installed by `pdf-install-global`; if a feature isn't in the wizard, users with the global install can't reach it.
- This project's code directory is `app/` (graphify graph scope).
