"""Window-chrome/settings and edit-mode command groups.

Split out of :mod:`app.gui.commands` (which is at the file-length cap) and folded
into the registry by ``build_commands`` via a local import; the cycle is avoided
because ``commands`` imports this module only inside the function body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.gui import commands as c
from app.gui import (
    default_app_strings,
    link_strings,
    select_strings,
    settings_strings,
    strings,
    thumbnail_strings,
)
from app.gui.commands import HAS_TEXT, PDF_ONLY, VIEWABLE, Command, Predicate
from app.os_integration import file_association
from app.pdf.file_format import IMAGE_FORMATS, TEXT_FORMATS, FileFormat

if TYPE_CHECKING:
    from app.gui.main_window import MainWindow


def view_commands(window: MainWindow) -> list[Command]:
    """Window chrome plus command-palette and outline appearance settings."""
    palette = window.palette_controller
    outline = window.outline_controller
    text_view = window.text_view_controller
    open_filter = window.open_filter_controller
    link = window.link_hint_settings
    zoom = window.zoom_settings_controller
    return [
        Command(c.COMMAND_PALETTE, strings.CMD_COMMAND_PALETTE, window.open_command_palette),
        Command(c.CONFIGURE_SHORTCUTS, strings.CMD_CONFIGURE_SHORTCUTS, window.configure_shortcuts),
        Command(
            c.FILE_TYPE_ASSOCIATIONS,
            default_app_strings.CMD_FILE_TYPE_ASSOCIATIONS,
            window.default_app_actions.configure_file_associations,
            file_association.is_supported,
        ),
        Command(c.TOGGLE_MENU, strings.CMD_TOGGLE_MENU, window.toggle_menu_bar),
        Command(c.TOGGLE_TOOLBAR, strings.CMD_TOGGLE_TOOLBAR, window.toggle_toolbar),
        Command(c.TOGGLE_STATUSBAR, strings.CMD_TOGGLE_STATUSBAR, window.toggle_statusbar),
        Command(c.TOGGLE_FULLSCREEN, strings.CMD_TOGGLE_FULLSCREEN, window.toggle_fullscreen),
        Command(
            c.THUMBNAILS_VIEW,
            thumbnail_strings.CMD_THUMBNAILS_VIEW,
            window.thumbnails_controller.toggle,
            window.has_document,
            VIEWABLE,
        ),
        Command(
            c.GIF_TOGGLE,
            strings.CMD_GIF_TOGGLE,
            window.toggle_gif_playback,
            window.is_animated_gif,
            frozenset({FileFormat.GIF}),
        ),
        Command(c.PALETTE_WIDTH, strings.CMD_PALETTE_WIDTH, palette.set_width),
        Command(c.PALETTE_HEIGHT, strings.CMD_PALETTE_HEIGHT, palette.set_height),
        Command(c.PALETTE_FONT, strings.CMD_PALETTE_FONT, palette.set_font_size),
        Command(c.PALETTE_OPACITY, strings.CMD_PALETTE_OPACITY, palette.set_opacity),
        Command(c.PALETTE_BORDERLESS, strings.CMD_PALETTE_BORDERLESS, palette.toggle_borderless),
        Command(c.DIALOG_SIZE, strings.CMD_DIALOG_SIZE, palette.set_dialog_size),
        Command(c.OUTLINE_WIDTH, strings.CMD_OUTLINE_WIDTH, outline.set_width),
        Command(c.OUTLINE_STYLE, strings.CMD_OUTLINE_STYLE, outline.set_style),
        Command(c.OUTLINE_COLOR, strings.CMD_OUTLINE_COLOR, outline.set_color),
        Command(
            c.TEXT_DARK_MODE,
            strings.CMD_TEXT_DARK_MODE,
            text_view.toggle_dark_mode,
            formats=TEXT_FORMATS,
        ),
        Command(
            c.TEXT_FONT_SIZE,
            strings.CMD_TEXT_FONT_SIZE,
            text_view.set_font_size,
            formats=TEXT_FORMATS,
        ),
        Command(
            c.IMAGE_BACKGROUND,
            settings_strings.CMD_IMAGE_BACKGROUND,
            window.image_background_controller.set_background,
            formats=IMAGE_FORMATS,
        ),
        Command(
            c.OPEN_FILTER_ALL_FILES,
            strings.CMD_OPEN_FILTER_ALL_FILES,
            open_filter.toggle_all_files,
        ),
        Command(
            c.OPEN_FILTER_EXTENSIONS,
            strings.CMD_OPEN_FILTER_EXTENSIONS,
            open_filter.edit_extensions,
        ),
        Command(
            c.REUSE_WINDOW,
            strings.CMD_REUSE_WINDOW,
            window.instance_controller.toggle_reuse_window,
        ),
        Command(
            c.FOCUS_ON_FORWARD,
            strings.CMD_FOCUS_ON_FORWARD,
            window.instance_controller.toggle_focus_on_forward,
        ),
        Command(c.LINK_FONT, link_strings.CMD_LINK_FONT, link.set_font_size),
        Command(c.LINK_TEXT_COLOR, link_strings.CMD_LINK_TEXT_COLOR, link.set_text_color),
        Command(c.LINK_BG_COLOR, link_strings.CMD_LINK_BG_COLOR, link.set_background_color),
        Command(c.LINK_BOX_COLOR, link_strings.CMD_LINK_BOX_COLOR, link.set_box_color),
        Command(c.ZOOM_SET_DEFAULT, strings.CMD_SET_DEFAULT_ZOOM, zoom.set_default_zoom),
        Command(c.DOC_ZOOM_REMEMBER, strings.CMD_REMEMBER_DOC_ZOOM, window.remember_document_zoom),
        Command(c.DOC_PAGE_REMEMBER, strings.CMD_REMEMBER_DOC_PAGE, window.remember_document_page),
        Command(
            c.REMEMBERED_SETTINGS,
            strings.CMD_REMEMBERED_SETTINGS,
            window.open_remembered_settings,
        ),
    ]


def edit_commands(window: MainWindow, has_doc: Predicate) -> list[Command]:
    controller = window.controller
    return [
        Command(c.EDIT_MODE, strings.CMD_EDIT_MODE, window.toggle_edit_mode, has_doc, PDF_ONLY),
        Command(
            c.SELECT_MODE,
            select_strings.CMD_SELECT_MODE,
            window.toggle_select_mode,
            has_doc,
            HAS_TEXT,
        ),
        Command(c.OPEN_LINK, link_strings.CMD_OPEN_LINK, window.open_link_hints, has_doc, HAS_TEXT),
        Command(c.COPY_LINK, link_strings.CMD_COPY_LINK, window.copy_link_hints, has_doc, HAS_TEXT),
        Command(
            c.SELECT_NEXT, strings.CMD_SELECT_NEXT, window.select_next_editable, has_doc, PDF_ONLY
        ),
        Command(
            c.SELECT_PREV,
            strings.CMD_SELECT_PREV,
            window.select_previous_editable,
            has_doc,
            PDF_ONLY,
        ),
        Command(c.ADD_FIELD, strings.CMD_ADD_FIELD, window.add_text_field, has_doc, PDF_ONLY),
        Command(c.ADD_IMAGE, strings.CMD_ADD_IMAGE, window.add_image, has_doc, PDF_ONLY),
        Command(
            c.DELETE_FIELD, strings.CMD_DELETE_FIELD, controller.delete_selected, has_doc, PDF_ONLY
        ),
        Command(c.EXPORT_TEXT, strings.CMD_EXPORT_TEXT, window.export_text, has_doc, PDF_ONLY),
        Command(
            c.DELETE_SAVED_FIELDS,
            strings.CMD_DELETE_SAVED_FIELDS,
            window.delete_saved_text_fields,
            has_doc,
            PDF_ONLY,
        ),
    ]
