"""Maps this app's own shortcut-config wording (``app/gui/strings.py``) onto the
shared ``command_palette`` library's :class:`~command_palette.ShortcutEditorLabels`,
so moving the editor into the library kept every user-facing string identical.
"""

from __future__ import annotations

from command_palette import ShortcutEditorLabels

from app.gui import strings

APP_SHORTCUT_LABELS = ShortcutEditorLabels(
    title=strings.CONFIGURE_SHORTCUTS_TITLE,
    placeholder=strings.CONFIGURE_SHORTCUTS_PLACEHOLDER,
    capture_title=strings.CAPTURE_TITLE,
    capture_prompt_fmt=strings.CAPTURE_PROMPT_FMT,
    capture_detected_fmt=strings.CAPTURE_DETECTED_FMT,
    capture_waiting=strings.CAPTURE_WAITING,
    confirm_reassign_title=strings.CONFIRM_REASSIGN_TITLE,
    confirm_reassign_fmt=strings.CONFIRM_REASSIGN_FMT,
    confirm_add_or_replace_title=strings.CONFIRM_ADD_OR_REPLACE_TITLE,
    confirm_add_or_replace_fmt=strings.CONFIRM_ADD_OR_REPLACE_FMT,
    confirm_clear_title=strings.CONFIRM_CLEAR_SHORTCUT_TITLE,
    confirm_clear_fmt=strings.CONFIRM_CLEAR_SHORTCUT_FMT,
    delete_title_fmt=strings.DELETE_SHORTCUT_TITLE_FMT,
    delete_placeholder=strings.DELETE_SHORTCUT_PLACEHOLDER,
    delete_all_label=strings.DELETE_ALL_SHORTCUTS,
    msg_set_fmt=strings.MSG_SHORTCUT_SET_FMT,
    msg_stolen_fmt=strings.MSG_SHORTCUT_STOLEN_FMT,
    msg_cleared_fmt=strings.MSG_SHORTCUT_CLEARED_FMT,
    msg_chord_removed_fmt=strings.MSG_SHORTCUT_CHORD_REMOVED_FMT,
    msg_none_to_clear_fmt=strings.MSG_SHORTCUT_NONE_TO_CLEAR_FMT,
    btn_append=strings.BTN_APPEND,
    btn_replace=strings.BTN_REPLACE,
    btn_cancel=strings.BTN_CANCEL,
    btn_yes=strings.BTN_YES,
    btn_no=strings.BTN_NO,
)
