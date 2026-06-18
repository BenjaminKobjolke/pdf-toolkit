# Remembered Settings

pdf-toolkit remembers your preferences across sessions. Everything is stored in a
single local database behind a pluggable backend, so the storage engine can be
swapped without touching the rest of the app.

## Where settings live

- **Default backend:** SQLite, one file at `~/.pdf-toolkit/pdf-toolkit.db`.
- **Override:** set `PDF_TOOLKIT_DATABASE_URL` (e.g.
  `sqlite:///C:/path/to/pdf-toolkit.db`). The URL scheme selects the engine.
- **Swapping engines:** the database is reached through a `StorageBackend`
  interface (`app/storage/backend.py`). Adding MySQL/Postgres means writing one
  new backend class plus a branch in `app/storage/factory.py` and adding its
  driver dependency — **no store code changes**.

The database has two tables:

| Table | Holds |
|-------|-------|
| `settings` | one versioned JSON object per global preference (keyed by name) |
| `document_memory` | per-document rows, keyed by `(namespace, document path)` |

> Migrating from older versions: previous builds used one JSON file per setting
> under `~/.pdf-toolkit/` (`zoom.json`, `window.json`, …). Those files are no
> longer read; remembered values start fresh on the database. The old files are
> left on disk and can be deleted.

## Global settings

These apply everywhere. Each can be cleared from the **Remembered settings…**
command in the palette (pick one to reset, or "clear all").

| Setting | What it remembers |
|---------|-------------------|
| Recent documents list | recently opened PDFs |
| Window chrome preferences | menu / toolbar / status-bar visibility |
| Command-palette appearance | palette size, font, opacity, frameless |
| Command palette usage history | recently run commands (floated to top) |
| Last overlay placement choice | last text/image placement mode |
| Window position and size | where the viewer reopens |
| Image add: copy-vs-reference choice | last image-add choice |
| Field outline appearance | selection outline width / style / colour |
| Default zoom | fit-to-window vs. a fixed percentage on open |
| Keyboard shortcuts | custom chord bindings |

## Per-document settings

These remember a value **per PDF**, keyed by the document's absolute path. Zoom
and page are fully **independent** — separate remember, separate auto-remember,
and separate clearing. They are never captured or cleared together.

| Setting | Command | What it remembers |
|---------|---------|-------------------|
| Remembered document zoom | **Zoom: remember for documents…** | the zoom each PDF was last viewed at |
| Remembered document page | **Page: remember for documents…** | the page each PDF was last on (0-based index) |

Each command opens a small menu with four actions:

- **Remember … for this document** — store the current value for the open PDF.
- **Auto-remember … for all documents (On/Off)** — when on, the value is captured
  automatically for every document.
- **Forget … for this document** — drop the value for the open PDF.
- **Forget … for all documents** — drop the value for every PDF (the auto-remember
  toggle is kept).

### When auto-remember captures

With auto-remember on, the value is captured at **document boundaries** — when you
open another document, close the document, or quit the app — so there is at most
one write per document per dimension. On open, a remembered value is restored;
remembered page indices that fall outside the document's range are clamped.

### Clearing

Per-document memory can be cleared in two places:

- From each Remember menu (this document / all documents), as above.
- From the **Remembered settings…** command, which lists "Remembered document
  zoom" and "Remembered document page" alongside the global settings and fully
  resets the chosen one (values **and** its auto-remember toggle).
