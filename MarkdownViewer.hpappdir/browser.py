"""Reusable file picker for HP Prime (320x240).

Displays a scrollable list of files, lets the user select one by
keyboard or touch, and returns the chosen filename.

The caller can customize the title, subtitle, file extension filter,
menu labels, menu-tap handler, and color palette.
"""

from constants import (GR_AFF, FONT_10, FONT_12, FONT_14)
from hpprime import fillrect
from graphics import draw_text, draw_rectangle, text_width
from keycodes import KEY_UP, KEY_DOWN, KEY_ENTER, KEY_ESC
from file_ops import list_files
from input_helpers import get_key, get_touch, get_menu_tap
from ui import draw_menu


def _get_colors(colors):
    if colors is not None:
        return colors
    import theme
    return theme.colors


def get_files(ext=None):
    """List files from storage, optionally filtered by extension.

    Args:
        ext: file extension including dot (e.g. '.md'). None = all files.
    """
    all_files = list_files()
    result = []
    if all_files:
        for f in all_files:
            s = str(f)
            if ext is None or s.endswith(ext):
                result.append(s)
    return result


def file_picker(title="Files", subtitle="Select a file", ext=None,
                menu_labels=None, on_menu_tap=None, highlight=None,
                menu_y=220, colors=None):
    """Show a file-picker screen and return the selected filename.

    Args:
        title:       heading text centred at top.
        subtitle:    smaller text below the heading.
        ext:         file extension filter (e.g. '.md'). None = all files.
        menu_labels: list of up to 6 menu-bar labels (default: all blank).
        on_menu_tap: callback(slot) called when a menu slot is tapped.
                     Should return True if the screen needs redrawing.
        highlight:   filename to mark with a triangle in the list.
        menu_y:      Y coordinate of the menu bar.
        colors:      color dict (see ui.py for required keys). Falls back
                     to theme.colors.

    Returns:
        Selected filename (str), or None if cancelled (ESC / ON).
    """
    files = get_files(ext)
    selected = 0

    if highlight and highlight in files:
        selected = files.index(highlight)

    if menu_labels is None:
        menu_labels = ["", "", "", "", "", ""]

    max_visible = 8
    touch_down = False
    tap_x = -1
    tap_y = -1

    def draw_screen():
        c = _get_colors(colors)
        fillrect(0, 0, 0, 320, menu_y, c['browser_bg'], c['browser_bg'])

        tw = text_width(title, FONT_14)
        draw_text(GR_AFF, (320 - tw) // 2, 5, title, FONT_14,
                  c['browser_subtitle'])
        draw_text(GR_AFF, 10, 25, subtitle, FONT_12,
                  c['browser_subtitle'])

        bdr_bottom = menu_y - 3
        draw_rectangle(GR_AFF, 5, 42, 315, 43,
                       c['browser_border'], 255, c['browser_border'], 255)
        draw_rectangle(GR_AFF, 5, 43, 6, bdr_bottom,
                       c['browser_border'], 255, c['browser_border'], 255)
        draw_rectangle(GR_AFF, 314, 43, 315, bdr_bottom,
                       c['browser_border'], 255, c['browser_border'], 255)

        start = 0
        if selected >= max_visible:
            start = selected - max_visible + 1

        for i in range(start, min(start + max_visible, len(files))):
            y = 50 + (i - start) * 20
            if i == selected:
                draw_rectangle(GR_AFF, 8, y - 2, 312, y + 16,
                               c['browser_sel'], 255, c['browser_sel'], 255)
                draw_text(GR_AFF, 15, y, files[i], FONT_12,
                          c['browser_sel_text'])
            else:
                label = files[i]
                if highlight and files[i] == highlight:
                    label = '\u25B6 ' + label
                draw_text(GR_AFF, 15, y, label, FONT_12, c['browser_text'])

        if len(files) == 0:
            draw_text(GR_AFF, 15, 60, "No files found", FONT_10,
                      c['browser_error'])

        draw_rectangle(GR_AFF, 5, bdr_bottom, 315, bdr_bottom + 1,
                       c['browser_border'], 255, c['browser_border'], 255)
        draw_menu(menu_labels, menu_y=menu_y, colors=c)

    draw_screen()

    try:
        while True:
            key = get_key()
            if key > 0:
                if key == KEY_UP:
                    if selected > 0:
                        selected -= 1
                        draw_screen()
                elif key == KEY_DOWN:
                    if selected < len(files) - 1:
                        selected += 1
                        draw_screen()
                elif key == KEY_ENTER:
                    if len(files) > 0:
                        return files[selected]
                elif key == KEY_ESC:
                    return None

            tx, ty = get_touch()
            if tx >= 0 and ty >= 0:
                touch_down = True
                tap_x = tx
                tap_y = ty
            elif touch_down:
                touch_down = False
                slot = get_menu_tap(tap_x, tap_y, menu_y)
                if slot >= 0 and on_menu_tap:
                    if on_menu_tap(slot):
                        draw_screen()
                elif len(files) > 0 and tap_y >= 50 and tap_y < menu_y:
                    start = 0
                    if selected >= max_visible:
                        start = selected - max_visible + 1
                    row = (tap_y - 50) // 20
                    tapped = start + row
                    if tapped < len(files):
                        if tapped == selected:
                            return files[selected]
                        else:
                            selected = tapped
                            draw_screen()

    except KeyboardInterrupt:
        return None
