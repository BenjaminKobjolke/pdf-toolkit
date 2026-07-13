"""Vim-style link hint mode for the page view (open or copy).

A peer of select mode: on activation every http(s) link on the current page
(geometry from :func:`app.pdf.links.page_links`) gets a letter label; typing the
label runs a terminal action on that URL — :meth:`open` opens it in the default
browser, :meth:`copy` copies it to the clipboard — and leaves the mode. ``Esc``
cancels.

Modal key capture reuses the single page-view key interceptor, restored to
select mode on exit (``SelectController.handle_key`` is inert while select mode
is inactive, so restoring to it is always safe).
"""

from __future__ import annotations

import string
import webbrowser
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from app.gui import link_strings
from app.gui.link_hint_style import LinkHintStyle
from app.gui.link_hints import LinkHints
from app.gui.mode_status_bar import ModeStatusBar
from app.gui.page_view import PageView
from app.gui.select_controller import SelectController
from app.pdf.links import page_links

_ALPHABET = string.ascii_lowercase


def hint_labels(count: int) -> list[str]:
    """Return ``count`` unique lowercase labels, all the same length.

    1–26 → single letters; 27+ → two-char combos (``aa``, ``ab``, …). Equal
    length keeps prefix matching unambiguous while keystrokes are buffered.
    """
    if count <= 0:
        return []
    if count <= len(_ALPHABET):
        return list(_ALPHABET[:count])
    combos = [a + b for a in _ALPHABET for b in _ALPHABET]
    return combos[:count]


class LinkHintController:
    """Owns open-link mode state and dispatches its keys for a :class:`PageView`."""

    def __init__(
        self,
        page_view: PageView,
        mode_bar: ModeStatusBar,
        select: SelectController,
        style: LinkHintStyle,
        exit_edit_mode: Callable[[], None],
    ) -> None:
        self._page_view = page_view
        self._mode_bar = mode_bar
        self._select = select
        self._exit_edit_mode = exit_edit_mode
        self._hints = LinkHints(page_view.graphics_scene(), style)
        self._active = False
        self._labels: dict[str, str] = {}  # label -> uri
        self._buffer = ""
        self._on_pick: Callable[[str], None] = _open_in_browser

    def is_active(self) -> bool:
        return self._active

    def open(self) -> None:
        """Enter hint mode where the chosen link opens in the default browser."""
        self._activate(_open_in_browser, link_strings.MODE_OPEN_LINK)

    def copy(self) -> None:
        """Enter hint mode where the chosen link is copied to the clipboard."""
        self._activate(_copy_to_clipboard, link_strings.MODE_COPY_LINK)

    def _activate(self, on_pick: Callable[[str], None], hint: str) -> None:
        """Enter hint mode for the current page, or show a hint if it has no links."""
        source = self._page_view.source()
        if source is None:
            return
        self._exit_edit_mode()
        self._select.set_active(False)  # modes are mutually exclusive
        links = page_links(source, self._page_view.current_page_index())
        if not links:
            self._mode_bar.set_hint(link_strings.NO_LINKS)
            return
        labels = hint_labels(len(links))
        self._labels = {label: link.uri for label, link in zip(labels, links, strict=True)}
        self._hints.set(list(zip(links, labels, strict=True)))
        self._buffer = ""
        self._on_pick = on_pick
        self._active = True
        self._page_view.set_key_interceptor(self.handle_key)
        self._mode_bar.set_hint(hint)

    def handle_key(self, event: QKeyEvent) -> bool:
        """Handle a key while active. Returns True when consumed (modal)."""
        if not self._active:
            return False
        if Qt.Key(event.key()) == Qt.Key.Key_Escape:
            self._exit()
            return True
        text = event.text()
        if not text or not text.isalpha():
            return True  # swallow non-letter keys so navigation stays disabled
        self._buffer += text.lower()
        uri = self._labels.get(self._buffer)
        if uri is not None:
            self._on_pick(uri)
            self._exit()
        elif not any(label.startswith(self._buffer) for label in self._labels):
            self._buffer = ""  # dead end — start over
        return True

    def _exit(self) -> None:
        self._active = False
        self._buffer = ""
        self._labels = {}
        self._hints.clear()
        self._page_view.set_key_interceptor(self._select.handle_key)
        self._mode_bar.set_edit_mode(False)


def _open_in_browser(uri: str) -> None:
    """Open ``uri`` in the default browser."""
    webbrowser.open(uri)


def _copy_to_clipboard(uri: str) -> None:
    """Put ``uri`` on the system clipboard (as select-mode yank does)."""
    QApplication.clipboard().setText(uri)
