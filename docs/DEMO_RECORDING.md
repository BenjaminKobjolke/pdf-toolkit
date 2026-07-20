# Demo Recording

FastFileViewer is wired for the `automated-application-screenshots` tool: scripted,
recordable demos that produce the gifs and stills for the fast-file-viewer landing
page. Landing-page side (distribute mapping, site tooling):
`D:\wamp64\www\app-landing-page\docs\sites\fast-file-viewer\assets.md`.

## Record everything

```
tools\create_media\create_demos.bat
```

Runs `screenshot-tool --config fastfileviewer.json --demo all` — 4 demos × en,de into
`tools\create_media\output\demos\<name>\<lang>\` (gif, mp4, stills). **Keep hands off
keyboard/mouse while the demo window is recording.** The landing repo's
`tools\sites\fast-file-viewer\update_media.bat` calls this and copies the results into
the site assets.

## Dry run one demo (no recording)

```
uv run python -m app.cli.gui --automation-demo 1 --automation-demo-texts tools/create_media/texts/en.json
```

The texts file is **required**: without it `{placeholder}` file names stay literal, the
open fails, and the app hangs on an error dialog instead of exiting.

## The pieces

| File | Role |
|---|---|
| `demo/scripts.py` | `DEMOS` map — the demo content (steps). ids 1/3 = photo browsing (wide/square), 2/4 = md dark mode + pdf search. |
| `demo/steps.py` | App-specific `OpenFile` step (resolves against `demo/assets/`) + `localize_viewer_script`. Generic steps come from the connector. |
| `demo/player.py` | `ViewerDemoPlayer` — connector `KeyEventDemoPlayer` subclass; handles `OpenFile`, discards pending edits on finish. |
| `demo/bootstrap.py` | `prepare_demo_database` — wiped temp SQLite DB per run, seeded from the config's `app_settings` (`"<store>/<field>": value`). |
| `demo/assets/` | Sample documents: `sample_{en,de}.md`, `sample_{en,de}.pdf` (regenerate: `make_samples.py`), `photos/{landscape,portrait}/`. |
| `tools/create_media/fastfileviewer.json` | Tool config: launch command, per-demo window size / `app_settings` / crop / languages. |
| `tools/create_media/texts/{en,de}.json` | Localized placeholders: `sample_md`, `sample_pdf`, `search_term`. |
| `app/gui/main.py` | Demo hook (`_run_demo`): temp DB, single-instance bypass, scrollbars off, `setFixedSize` after `show()`, player start. |

## Demo mode vs normal run

- Settings come from a **wiped temp DB** (`%TEMP%\fastfileviewer-demo-settings\`) — the
  user's real settings are untouched, every run starts deterministic.
- **Single-instance forwarding and the instance server are bypassed** — a recording must
  never land in (or collide with) a real running viewer.
- The window is `setFixedSize`d **after** `show()` (first show pass discards a pre-show
  resize; the mode status bar appearing on document open must not grow the window).
  Config heights are title-bar-compensated: capture includes the ~24 logical px title
  bar, so wide demos use 520×269 (→ 16:9 capture) and square 460×436 (→ 1:1).
- Demos never save; `ViewerDemoPlayer._finish` discards pending edits so quitting can't
  pop the unsaved-changes dialog.
- The demo never mutates committed assets: `open_pdf` works on a temp working copy.

## Writing/editing demos

- Steps and pacing: connector docs
  (`automated-application-screenshots-python-connector\docs\WRITING_DEMOS.md`).
- Palette filter texts must **uniquely** match one command title (token substring match,
  e.g. `"rotate right"` → "Rotate page 90° right") — Return runs the top row.
- Shape/size/font/theme belong in `fastfileviewer.json` (`app_settings` seeds the temp
  DB); typed content and beats belong in `demo/scripts.py`; a content variant needs its
  own demo id.
