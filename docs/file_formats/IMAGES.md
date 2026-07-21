# Images (`.png` `.jpg` `.jpeg` `.gif` `.bmp` `.tif` `.tiff` `.webp`)

Images open as a single-page document rendered by fitz directly. No text
layer, so search/select/link commands are greyed out. Page dimensions in
**File information** are native pixels.

For `.psd` — which also counts as an image format but has its own render path
and preview-only rules — see [PSD.md](PSD.md).

## Editing (rotate / flip)

**Rotate** (90° left/right, 180°) and **flip** (horizontal/vertical) transform
the pixels themselves (an image has no rotation flag) — `rotate_image` /
`flip_image` in `app/pdf/image_transform.py`, format-preserving, atomic write.
Like PDF page edits, changes apply to the working copy and are deferred until
**Save changes to original file** (`Ctrl+S`), which backs up the original
first. Caveats:

- **JPEG** is re-encoded on save (quality 95) — repeated transforms compound
  the loss.
- Any **EXIF orientation** tag is baked into the pixels; other EXIF metadata
  is dropped.
- **Multi-frame TIFF**: only the first frame is kept.
- **Save As** copies the bytes verbatim — the extension you type does not
  convert the format.

## Animated GIF

An animated `.gif` **autoplays** on open (Qt's movie engine draws frames onto
the page; zoom/fit/scroll behave normally). **GIF: play / pause** in the
palette stops/resumes — shown only while an animated GIF is open. Editing
operations still act on the first frame only, so stop playback and treat it
as a still before transforming.

## Transparency

**Image: transparency background…** (palette) chooses what shows behind
transparent pixels: white (default), black, greenscreen green/blue, or a
checkered pattern. Persisted; also affects **Copy page as image**. Animated
GIF playback frames are not affected.

## Merging

*Merge folder…* accepts only `.png`/`.jpg`/`.jpeg` (the `img2pdf` conversion
set) → `merged.pdf` — deliberately narrower than what the viewer displays.
