# PDF Render Quality (sharp pages, any zoom)

The GUI renders each page at the screen's **true pixel density** and re-renders
when zoom changes, so text stays crisp on HiDPI displays and when zoomed in —
without ever moving placed text fields, images, or search highlights.

## The problem it fixes

A page used to be rasterised **once** at a fixed `render.DEFAULT_ZOOM = 1.5`,
and all zoom was a `QGraphicsView` *transform* on top of that one bitmap. On a
scaled Windows display (125–150%) Qt then upscaled the 1.5x pixmap to physical
pixels — blurry on open, before any zoom. Zooming in compounded it (bitmap
interpolation, not vector re-rasterisation).

## How it works

```
                 quality = view scale  ×  screen DPR        (physical px per scene unit)
                          │
 zoom change ─▶ ZoomController._notify ─▶ RenderQualityController.request(scale)
                          │  (debounce 120ms, skip if <15% change, cap at MAX_QUALITY)
                          ▼
            render.render_page(source, index, quality)
                          │  fitz matrix = DEFAULT_ZOOM × quality   → more PHYSICAL pixels
                          │  image.setDevicePixelRatio(quality)     → LOGICAL size unchanged
                          ▼
            pixmap_item.setPixmap(...)   scene rect / overlay coords untouched
```

**Key invariant — overlay coordinates never move.** Text fields, images and
highlights are stored in *render-time scene pixels* = `PDF points × DEFAULT_ZOOM`
(see `app/pdf/text_spec.py`, `image_spec.py`). The scene rect is the page
pixmap's `boundingRect()`. So the pixmap's **logical (device-independent) size
must stay `points × DEFAULT_ZOOM`** no matter how sharp it renders.

The trick: render more **physical** pixels but call `QImage.setDevicePixelRatio(quality)`.
`QGraphicsPixmapItem.boundingRect()` divides by device-pixel-ratio, so scene
rect, overlay positions and highlights are identical — only pixel density rises.
`quality == 1.0` reproduces the old output exactly.

### Quality = on-screen density (DPI-match)

`quality = view_scale × screen_dpr` is the number of physical screen pixels each
scene unit occupies, so the page is rasterised **1:1** with the pixels it covers.

- Fit-to-window on a 1.0x screen → low quality (page shown small, no wasted px).
- 150% Windows scaling → `screen_dpr = 1.5` → renders 1.5× denser → sharp.
- Zoom in → `view_scale` rises → re-render denser instead of upscaling the bitmap.

Guards (in `app/gui/render_quality.py`):

| Constant | Purpose |
|----------|---------|
| `_RERENDER_RATIO = 0.15` | Skip re-render if quality changed < 15% (avoid churn). |
| `MAX_QUALITY = 8.0` | Cap pixmap blow-up at extreme zoom (smooth-transform hint covers beyond). |
| `_DEBOUNCE_MS = 120` | Single-shot timer coalesces a zoom burst into one re-render. |

## Files

| File | Role |
|------|------|
| `app/gui/render.py` | `render_page(source, index, quality=1.0)` — renders at `DEFAULT_ZOOM × quality` px, tags `setDevicePixelRatio(quality)`. |
| `app/gui/render_quality.py` | `target_quality()`, `needs_rerender()`, `RenderQualityController` (debounce timer + re-render). |
| `app/gui/zoom_controller.py` | `on_scale_changed` hook fired from `_apply` / `_fit_to_viewport` (covers every zoom path). |
| `app/gui/page_view.py` | Wires the controller; `_show()` calls `render_now()`; sets `SmoothPixmapTransform` + `Antialiasing` render hints. |
| `app/gui/main.py` | `setHighDpiScaleFactorRoundingPolicy(PassThrough)` so fractional Windows scaling reports its true ratio (set before `QApplication`). |

## Tests

| Test | Pins |
|------|------|
| `tests/unit/test_gui_render.py` | `quality` tags device-pixel-ratio, scales physical px, keeps logical size. |
| `tests/unit/test_render_quality.py` | `target_quality` = scale×dpr (clamped); `needs_rerender` threshold. |
| `tests/integration/test_zoom_rerender.py` | Re-render at higher quality keeps scene rect + overlay `pos()`; zoom-in schedules a re-render. |

## Tuning

- Sharper deeper into zoom-in: raise `MAX_QUALITY` (more memory/CPU per page).
- Fewer re-renders on small zoom steps: raise `_RERENDER_RATIO`.
- Snappier vs. fewer renders during fast zoom: lower / raise `_DEBOUNCE_MS`.
