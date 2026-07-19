"""The main viewer window: a thin coordinator wiring controls to core ops."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow

from app.gui import confirm_dialog, overlay_selection, strings
from app.gui.main_window_accessors import CollaboratorAccessors
from app.gui.window_builder import assemble

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
        self._lifecycle.open_pdf(path)

    def open_from_history(self) -> None:
        self._document_actions.open_from_history()

    def open_folder_from_history(self) -> None:
        self._document_actions.open_folder_from_history()

    def open_next_file(self) -> None:
        """Open the alphabetically next openable file in the document's directory."""
        self._lifecycle.open_sibling(1)

    def open_previous_file(self) -> None:
        """Open the alphabetically previous openable file in the document's directory."""
        self._lifecycle.open_sibling(-1)

    def open_directory(self) -> None:
        """Browse to a folder and open its first openable file."""
        self._lifecycle.open_directory()

    def close_document(self) -> None:
        """Offer to save pending changes, then return to the empty viewer state."""
        self._lifecycle.close_document()

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
        if self._lifecycle.shutdown():
            super().closeEvent(event)
        else:
            event.ignore()

    def _original_dir(self) -> Path | None:
        original = self._working_doc.original()
        return original.parent if original is not None else None

    def _set_source(self, path: Path | None) -> None:
        self._source = path

    def _report(self, result: OpResult) -> None:
        if result.ok:
            confirm_dialog.show_message(self, strings.DIALOG_SUCCESS_TITLE, result.message)
        else:
            confirm_dialog.show_message(
                self, strings.DIALOG_ERROR_TITLE, result.message, confirm_dialog.Severity.ERROR
            )
