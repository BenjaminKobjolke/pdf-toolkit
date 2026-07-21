---
description: Scaffold a new command-palette feature end-to-end (id, command, handler, thumbnail-view routing, settings, wizard, tests, docs)
---

# Add a command-palette feature

Add a new feature to the GUI viewer's command palette, following the project's
established pattern so every step (visibility, thumbnail-view routing, persisted
settings, the wizard mandate, tests, docs) is covered.

Feature to add: **$ARGUMENTS**

If `$ARGUMENTS` is empty or ambiguous (which file/page it acts on, whether it
persists a setting, PDF-only vs all formats), ask before writing any code.

## Step 1 — Read the surface docs

Read these first so you match the existing behavior, not invent new patterns:

- `docs/COMMAND_PALETTE.md` — the palette, command list, gating, keyboard chords.
- `docs/REMEMBERED_SETTINGS.md` — persisted-settings surface (only if the feature
  remembers anything).
- `docs/THUMBNAIL_VIEW.md` — how commands behave while the thumbnails grid shows
  (**required** — every new command has to make a decision here, see Step 4).
- `docs/CONFIGURE_SHORTCUTS.md` — only if the feature needs a keyboard chord.
- `docs/edit_mode/EDIT_MODE.md` — only if it's an edit-mode / field / image command.
- `CLAUDE.md` — the wizard mandate and the coding rules that gate this change.

## Step 2 — Restate and scope

State the Definition of Done in chat before the first edit (CLAUDE.md requires
it): what changes, what doesn't, which existing fn/component you reuse and its
path, and whether a persisted setting is involved.

## Step 3 — Follow the project workflow (TDD + DRY gate)

CLAUDE.md's Feature Workflow applies. Do not reimplement it here — invoke the
skills: `/plan:dry` → `/plan:dry-checked` → `/convention:check` (DRY gate), then
write the failing test first, implement, then `/dry:check` and
`/verify:after-change`. For a pure bug-shaped change use `bugs:fix` instead.

## Step 4 — The concrete checklist

The registry is split across group modules because `app/gui/commands.py` is at
its 300-line cap — add the `Command` entry to a **group module**, not `commands.py`.

1. **Id constant** — `app/gui/commands.py`: add `MY_CMD = "my_cmd"`
   (`UPPER_SNAKE_CASE`, value is the stable command id).
2. **Title string** — `app/gui/strings.py` or the relevant `*_strings.py`
   (`file_strings.py`, `settings_strings.py`, `select_strings.py`, …): add
   `CMD_MY = "My command…"`. Never inline a raw title.
3. **Command entry** — add to the right group module:
   `app/gui/doc_commands.py` (file/nav/page ops), `app/gui/view_commands.py`
   (view/palette/settings), or `app/gui/overlay_commands.py` (edit-mode/field/image):
   ```python
   Command(c.MY_CMD, strings.CMD_MY, window.my_handler, <predicate>, <formats>)
   ```
   - Predicates: `has_doc` / `doc_in_view` (see Step 4a). Omit for always-shown.
   - Format sets (`commands.py:22`): `PDF_ONLY`, `HAS_TEXT`, `VIEWABLE`,
     `TRANSFORMABLE`, or `None` (format-agnostic).
   - Use `title_fn=` for a live title (e.g. pixel sizes); see `copy_image_titles`.
4. **Handler** — `app/gui/main_window.py`: add `my_handler`, delegating to a
   controller/actions object (don't put real logic on `MainWindow`). See
   `open_command_palette` → `_palette_actions.open_commands()` for the shape.
5. **Persisted setting (only if it remembers something):**
   - Copy the `app/config/palette_settings.py` pattern: a frozen dataclass +
     `SettingsRecordStore` subclass with `LABEL` and `VERSION`.
   - Add a controller like `app/gui/palette_controller.py` (load once in
     `__init__`, save on edit).
   - Wire it in `app/gui/window_builder.py`, and register the store in
     `remembered_stores(...)` (`app/gui/window_builder_memory.py`) so
     **Remembered settings…** lists it for reset (the label comes from `LABEL`).
6. **Wizard (CLAUDE.md mandate)** — `app/cli/pdft.py`: if the feature is a
   standalone document op, add a `_handle_*(settings) -> int` (pattern:
   `_handle_swap`) and append a `WizardOption("Label", _handle_x)` to
   `WIZARD_OPTIONS`. GUI-only features reached through "Open GUI viewer" need no
   separate option — state which case applies.
7. **Tests:**
   - Store round-trip unit test if a setting was added (pattern:
     `tests/unit/test_palette_settings.py`, real `SqliteBackend(tmp_path/…)`).
   - Integration palette test (`tests/integration/test_command_palette.py`):
     build the registry, `commands.find(registry, c.MY_CMD).is_enabled()` for the
     gate, and drive the command via the `_FakeDialog` monkeypatch on
     `app.gui.palette_actions.FilterListDialog` + the `silence_dialogs` fixture.
     Use `MagicMock(spec=ClassName)` — never bare `MagicMock()`.
8. **Docs** — add a row to `docs/COMMAND_PALETTE.md`; update
   `docs/REMEMBERED_SETTINGS.md` if a setting was added, and
   `docs/THUMBNAIL_VIEW.md` if the command's grid behavior is notable.

### Step 4a — Thumbnail-view decision (required for every command)

While the thumbnails grid shows, each command is either **retargeted to the
selected thumbnail** or **hidden**. This is decided by the predicate — decide
deliberately:

- **`has_doc`** — stays in the palette while the grid shows and **acts on the
  selected thumbnail**. The handler MUST resolve its target through
  `app/gui/effective_target.py` — `effective_source(window)` /
  `effective_page_index(window)` — **not** `window._source` directly. Reading
  `window._source` would make the command operate on the still-open document
  while the grid displays a different file (a real bug). `window.file_actions.*`
  are the reference implementations.
- **`doc_in_view`** — needs the loaded working copy on screen, so it **hides**
  while the grid covers the page. No thumbnail-target work needed.

Format gating already follows the selection: `Command.formats` is checked against
`window.current_format()`, which returns the grid selection's format while the
grid shows (`app/gui/main_window_accessors.py`). So format-based visibility is
free once the predicate is right.

## Step 5 — Verify

Run `/verify:after-change` (tests + `tools/analyze_code.bat`). Fix any reported
issue before finishing. Confirm the new command appears in the palette, is gated
correctly, and behaves as intended in the thumbnails grid per Step 4a.
