"""Autoplay and palette control for animated GIFs.

The viewer opens images (including ``.gif``) through fitz, which keeps only the
first frame. This controller layers Qt's native :class:`QMovie` decoder on top:
while an animated GIF is open it drives the page pixmap frame-by-frame and tells
the view to suspend the fitz re-render that would otherwise overwrite each frame.

Mirrors :class:`~app.gui.reload_controller.ReloadController`'s
``on_document_opened`` / ``on_document_closed`` lifecycle so the two read
identically at the call sites in :class:`~app.gui.main_window.MainWindow`.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QMovie

from app.gui.page_view import PageView
from app.pdf.file_format import FileFormat


class GifController:
    """Plays an animated GIF into the page view; no-op for any other document."""

    def __init__(self, page_view: PageView) -> None:
        self._page_view = page_view
        self._movie: QMovie | None = None

    def on_document_opened(self, source: Path, fmt: FileFormat | None) -> None:
        """Autoplay ``source`` if it is an animated GIF; otherwise stay idle.

        The view has already cleared its render suspension in ``load``; here we
        only re-arm it when there is actually a movie to drive.
        """
        self._drop_movie()
        if fmt is not FileFormat.GIF:
            return
        movie = QMovie(str(source))
        # A static / single-frame GIF has nothing to animate (frameCount may also
        # report 0 when the handler can't seek — treat that as static, not a crash).
        if movie.frameCount() <= 1:
            return
        movie.frameChanged.connect(self._on_frame)
        self._movie = movie
        self._page_view.set_animating(True)
        movie.start()

    def on_document_closed(self) -> None:
        """Stop and drop the movie (the view clears suspension itself on reset)."""
        self._drop_movie()

    def toggle(self) -> None:
        """Pause a running movie, resume a paused one, restart a finished one."""
        movie = self._movie
        if movie is None:
            return
        if movie.state() == QMovie.MovieState.Running:
            movie.setPaused(True)
        elif movie.state() == QMovie.MovieState.Paused:
            movie.setPaused(False)
        else:  # NotRunning: a non-looping GIF that reached its last frame
            movie.start()

    def is_animated(self) -> bool:
        """True while an animated GIF is loaded (gates the palette command)."""
        return self._movie is not None

    def is_playing(self) -> bool:
        """True while the movie is actively running (drives the toggle's title)."""
        return self._movie is not None and self._movie.state() == QMovie.MovieState.Running

    def _on_frame(self, _index: int) -> None:
        if self._movie is not None:
            self._page_view.show_animation_frame(self._movie.currentPixmap())

    def _drop_movie(self) -> None:
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
