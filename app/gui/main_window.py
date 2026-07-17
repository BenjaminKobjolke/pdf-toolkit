"""The main viewer window: a thin coordinator wiring controls to core ops."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow

from app.gui import (
    confirm_dialog,
    file_browser_model,
    file_dialogs,
    overlay_selection,
    strings,
)
from app.gui.main_window_accessors import CollaboratorAccessors
from app.gui.window_builder import assemble
from app.pdf.file_format import FileFormat

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent

    from app.config.key_bindings import KeyMap
    from app.config.settings import Settings
    from app.gui.operations import OpResult


class MainWindow(CollaboratorAccessors, QMainWindow):
    """Viewer window; delegates page rendering and op execution to collaborators.

    The collaborators are constructed and assigned by
    :func:`app.gui.window_builder.assemble`; they are declared (with their
    read-only accessors) on :class:`CollaboratorAccessors`.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._source: Path | None = None
        assemble(self, settings)

    def open_pdf(self, path: Path | None = None) -> None:
        """Open ``path`` (or prompt for one) into a working copy and show page 1."""
        if not self._save.confirm_unsaved():
            return
        if path is None:
            chosen = file_dialogs.prompt_open_file(
                self,
                strings.DIALOG_OPEN_TITLE,
                self._open_filter.current_filter(),
                self._source.parent if self._source else None,
            )
            if chosen is None:
                return
            path = chosen
        # Boundary: reject a format the viewer can't render (e.g. a path passed on
        # the command line) instead of handing it to fitz and failing obscurely.
        doc_format = FileFormat.of(path)
        if doc_format is None:
            confirm_dialog.show_message(
                self,
                strings.DIALOG_ERROR_TITLE,
                strings.MSG_UNSUPPORTED_FORMAT_FMT.format(name=path.name),
                confirm_dialog.Severity.WARNING,
            )
            return
        # Capture the outgoing document's view state before switching away.
        self._doc_memories.capture(self._source)
        self._source = path
        working = self._working_doc.open(path)
        # Asset paths resolve against the original PDF's directory, not the temp
        # working copy; set this before rendering so the first restore can load
        # image pixmaps.
        self._controller.set_base_dir(path.parent)
        self._images.set_base_dir(path.parent)
        # Load saved content before rendering so the first page_changed restores
        # it onto the page (it shows whether or not edit mode is on). The sidecar
        # is keyed to the working copy, seeded from the original on open.
        self._load_text_fields(working)
        self._page_view.load(working)
        # Restore the remembered zoom/page for this document (independent dimensions).
        self._doc_memories.apply_for(path)
        self._bar.update_for(has_doc=True, is_pdf=doc_format is FileFormat.PDF)
        self._mode_bar.set_dirty(False)
        self._recent.add(path)
        self.setWindowTitle(strings.WINDOW_TITLE_OPEN_FMT.format(path=path))

    def open_from_history(self) -> None:
        self._document_actions.open_from_history()

    def open_folder_from_history(self) -> None:
        self._document_actions.open_folder_from_history()

    def open_next_file(self) -> None:
        """Open the alphabetically next openable file in the document's directory."""
        self._open_sibling(1)

    def open_previous_file(self) -> None:
        """Open the alphabetically previous openable file in the document's directory."""
        self._open_sibling(-1)

    def _open_sibling(self, step: int) -> None:
        if self._source is None:
            return
        target = file_browser_model.sibling_file(
            self._source, self._open_filter.current_filter(), step
        )
        if target is None:
            self._mode_bar.set_hint(strings.HINT_NO_SIBLING_FILE)
            return
        self.open_pdf(target)

    def close_document(self) -> None:
        """Offer to save pending changes, then return to the empty viewer state."""
        if not self._save.confirm_unsaved():
            return
        self._doc_memories.capture(self._source)
        self._working_doc.close()
        self._page_view.reset()
        self._bar.update_for(has_doc=False, is_pdf=False)
        self._mode_bar.clear_page_label()
        self._mode_bar.clear_zoom_label()
        self._mode_bar.set_dirty(False)
        if self._edit_bar.is_edit_mode():
            self._edit_bar.toggle_edit_mode()
        self._source = None
        self.setWindowTitle(strings.WINDOW_TITLE)

    def exit_app(self) -> None:
        self.close()

    def save_changes(self) -> None:
        """Write the working copy's changes back to the original file (with a backup)."""
        self._save.save()

    def open_command_palette(self) -> None:
        self._palette_actions.open_commands()

    def show_keyboard_shortcuts(self) -> None:
        self._palette_actions.show_shortcuts()

    def show_release_notes(self) -> None:
        """Open the release-notes browser (newest first, Older/Newer navigation)."""
        from app.gui.release_notes_dialog import ReleaseNotesDialog
        from app.release.notes_loader import load_release_notes

        ReleaseNotesDialog(load_release_notes(), self).exec()

    def configure_shortcuts(self) -> None:
        """Open the searchable command list for binding/clearing shortcuts."""
        self._keybinding_actions.open_config()

    def current_keymap(self) -> KeyMap:
        """Return the effective keymap (used by the palette to show chords)."""
        return self._keymap

    def apply_keymap(self, keymap: KeyMap) -> None:
        """Adopt ``keymap`` as effective and rebuild the live shortcuts."""
        self._keymap = keymap
        self._shortcut_installer.reinstall(keymap)

    def toggle_edit_mode(self) -> None:
        self._edit_bar.toggle_edit_mode()

    def exit_edit_mode(self) -> None:
        """Leave edit mode if active (used when entering the mutually-exclusive select mode)."""
        if self._edit_bar.is_edit_mode():
            self._edit_bar.toggle_edit_mode()

    def toggle_select_mode(self) -> None:
        """Enter/leave vim-style text select mode."""
        self._select.toggle()

    def open_link_hints(self) -> None:
        """Enter vim-style open-link mode (type a letter to open a link)."""
        self._link_hints.open()

    def copy_link_hints(self) -> None:
        """Enter vim-style copy-link mode (type a letter to copy a link)."""
        self._link_hints.copy()

    def add_text_field(self) -> None:
        """Add a text field, entering edit mode first if needed (palette/button)."""
        self._overlay_actions.add_text_field()

    def add_image(self) -> None:
        """Add an image, entering edit mode first if needed (palette/button)."""
        self._overlay_actions.add_image()

    def add_rect(self) -> None:
        """Add a rectangle, entering edit mode first if needed (palette/button)."""
        self._overlay_actions.add_rect()

    def select_next_editable(self) -> None:
        """Select the next editable element on the page (enters edit mode first)."""
        self._overlay_actions.ensure_edit_mode()
        overlay_selection.select_adjacent_editable(self._page_view, forward=True)

    def select_previous_editable(self) -> None:
        """Select the previous editable element on the page (enters edit mode first)."""
        self._overlay_actions.ensure_edit_mode()
        overlay_selection.select_adjacent_editable(self._page_view, forward=False)

    def open_remembered_settings(self) -> None:
        """Show the remembered-settings picker to reset stored preferences."""
        self._remembered.open()

    def remember_document_zoom(self) -> None:
        """Open the per-document zoom remember/auto/forget menu."""
        self._doc_zoom.open_menu()

    def remember_document_page(self) -> None:
        """Open the per-document page remember/auto/forget menu."""
        self._doc_page.open_menu()

    def export_text(self) -> None:
        """Flatten placed overlay: overwrite the original or write a new file."""
        self._export.export()

    def delete_saved_text_fields(self) -> None:
        self._document_actions.delete_saved_text_fields()

    def rename_file(self) -> None:
        self._document_actions.rename_file()

    def toggle_menu_bar(self) -> None:
        """Show/hide the top menu bar (remembered across sessions)."""
        self._chrome.toggle_menu()

    def toggle_toolbar(self) -> None:
        """Show/hide the button toolbars (remembered across sessions)."""
        self._chrome.toggle_toolbar()

    def toggle_statusbar(self) -> None:
        """Show/hide the mode footer bar (remembered across sessions)."""
        self._chrome.toggle_statusbar()

    def toggle_fullscreen(self) -> None:
        """Flip fullscreen for the current session (not remembered across runs)."""
        if self.isFullScreen():
            self._geometry.exit_fullscreen()
        else:
            self._geometry.enter_fullscreen()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Confirm unsaved changes, then persist UI + window state before closing."""
        if not self._save.confirm_unsaved():
            event.ignore()
            return
        self._doc_memories.capture(self._source)
        self._working_doc.close()
        self._chrome.save()
        self._geometry.save()
        self._backend.close()
        super().closeEvent(event)

    def _original_dir(self) -> Path | None:
        original = self._working_doc.original()
        return original.parent if original is not None else None

    def _load_text_fields(self, path: Path) -> None:
        try:
            self._controller.on_document_loaded(path)
        except ValueError as err:
            confirm_dialog.show_message(
                self,
                strings.DIALOG_ERROR_TITLE,
                strings.MSG_SIDECAR_LOAD_FAILED_FMT.format(error=err),
                confirm_dialog.Severity.WARNING,
            )

    def _report(self, result: OpResult) -> None:
        if result.ok:
            confirm_dialog.show_message(self, strings.DIALOG_SUCCESS_TITLE, result.message)
        else:
            confirm_dialog.show_message(
                self, strings.DIALOG_ERROR_TITLE, result.message, confirm_dialog.Severity.ERROR
            )
