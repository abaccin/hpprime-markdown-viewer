"""Reusable UI components for HP Prime (320x240).

All functions accept an optional ``colors`` dict for theming.
If not provided, ``theme.colors`` is used as the default palette.

Required color keys per component:

draw_menu:        menu_bg, menu_text, menu_divider
show_input_bar:   table_header_bg, table_border, header, bg, normal
show_context_menu: ctx_bg, ctx_border, ctx_text
show_list_manager: bg, header, italic, normal, table_border,
                   browser_sel, browser_sel_text, bookmark_mark (optional)
"""

from constants import (GR_AFF, FONT_10, FONT_12, FONT_14,
    NOTCH_X, NOTCH_Y, NOTCH_W, NOTCH_H, GR_MENU_SAVE, MENU_HEIGHT)
from hpprime import fillrect, strblit2, dimgrob
from graphics import draw_text, draw_rectangle, text_width
from keycodes import KEY_ENTER, KEY_ESC, KEY_BACKSPACE, KEY_UP, KEY_DOWN
from input_helpers import get_key, get_touch


def _c(colors):
    """Return the given colors dict, or fall back to theme.colors."""
    if colors is not None:
        return colors
    import theme
    return theme.colors


# ---------------------------------------------------------------------------
# Menu bar
# ---------------------------------------------------------------------------

def draw_menu(labels, menu_y=220, menu_h=20, colors=None):
    """Draw a 6-slot soft-key menu bar.

    Args:
        labels: list of up to 6 strings (empty string = blank slot).
        menu_y: top Y coordinate of the menu bar.
        menu_h: height of the menu bar.
        colors: dict with keys menu_bg, menu_text, menu_divider.
    """
    c = _c(colors)
    fillrect(0, 0, menu_y, 320, menu_h, c['menu_bg'], c['menu_bg'])

    slot_w = 53  # 320 / 6 ≈ 53
    for i in range(6):
        x1 = i * slot_w
        x2 = (i + 1) * slot_w if i < 5 else 320

        if i > 0:
            draw_rectangle(GR_AFF, x1, menu_y + 2,
                           x1 + 1, menu_y + menu_h - 2,
                           c['menu_divider'], 255, c['menu_divider'], 255)

        label = labels[i] if i < len(labels) else ""
        if label:
            tw = text_width(label, FONT_10)
            tx = x1 + (x2 - x1 - tw) // 2
            draw_text(GR_AFF, tx, menu_y + 5, label, FONT_10, c['menu_text'])


# ---------------------------------------------------------------------------
# Menu notch (bottom-right trigger tab) & overlay helpers
# ---------------------------------------------------------------------------

def draw_notch(colors=None):
    """Draw a small menu-trigger tab at the bottom-right corner.

    The notch is a small rectangle with a hamburger icon (three lines)
    that hints the user can tap to reveal the menu bar.
    """
    c = _c(colors)
    bg = c['menu_bg']
    fg = c['menu_text']
    fillrect(GR_AFF, NOTCH_X, NOTCH_Y, NOTCH_W, NOTCH_H, bg, bg)
    # Three horizontal lines (hamburger icon)
    for i in range(3):
        ly = NOTCH_Y + 3 + i * 3
        fillrect(GR_AFF, NOTCH_X + 12, ly, 14, 1, fg, fg)


def is_notch_tap(tx, ty):
    """Return True if (tx, ty) is within the notch hit area.

    The hit area is slightly larger than the visual notch for easier tapping.
    """
    return (tx >= NOTCH_X - 4 and tx < NOTCH_X + NOTCH_W + 4
            and ty >= NOTCH_Y - 4 and ty < NOTCH_Y + NOTCH_H + 4)


def save_menu_area(menu_y=220, menu_h=20):
    """Save the screen area where the menu will be drawn to GR_MENU_SAVE.

    Uses strblit2 to copy pixels from the display buffer to an off-screen
    GROB so they can be restored later when the menu is dismissed.
    """
    dimgrob(GR_MENU_SAVE, 320, menu_h, 0)
    strblit2(GR_MENU_SAVE, 0, 0, 320, menu_h,
             GR_AFF, 0, menu_y, 320, menu_h)


def restore_menu_area(menu_y=220, menu_h=20):
    """Restore the saved screen area, hiding the menu overlay.

    Uses strblit2 to copy the previously saved pixels back to the display.
    """
    strblit2(GR_AFF, 0, menu_y, 320, menu_h,
             GR_MENU_SAVE, 0, 0, 320, menu_h)


# ---------------------------------------------------------------------------
# Text input bar
# ---------------------------------------------------------------------------

def show_input_bar(label="Find:", menu_y=220, colors=None):
    """Show a one-line text input bar above the menu.

    Returns entered text, or None on cancel (ESC).
    The caller is responsible for redrawing underneath after return.

    Args:
        label: text shown to the left of the input field.
        menu_y: Y position of the menu bar (bar is drawn just above).
        colors: dict with keys table_header_bg, table_border, header,
                bg, normal.
    """
    key_chars = {
        14: 'a', 15: 'b', 16: 'c', 17: 'd', 18: 'e',
        20: 'f', 21: 'g', 22: 'h', 23: 'i', 24: 'j',
        25: 'k', 26: 'l', 27: 'm', 28: 'n', 29: 'o',
        31: 'p', 32: 'q', 33: 'r', 34: 's', 35: 't',
        37: 'u', 38: 'v', 39: 'w', 40: 'x', 42: 'y',
        43: 'z', 49: ' ', 48: '.', 45: '-',
    }
    c = _c(colors)
    text = ""
    bar_y = menu_y - 22
    lbl_w = text_width(label, FONT_10) + 8
    field_x1 = lbl_w
    field_x2 = 278
    ok_x1 = 282
    ok_x2 = 316
    ok_y1 = bar_y + 2
    ok_y2 = bar_y + 18
    max_text_w = field_x2 - field_x1 - 8
    touch_was_down = False
    tap_x = -1
    tap_y = -1

    def draw_bar():
        # Background
        draw_rectangle(GR_AFF, 0, bar_y, 320, bar_y + 20,
                       c['table_header_bg'], 255, c['table_header_bg'], 255)
        # Top border
        draw_rectangle(GR_AFF, 0, bar_y, 320, bar_y + 1,
                       c['table_border'], 255, c['table_border'], 255)
        # Label
        draw_text(GR_AFF, 4, bar_y + 4, label, FONT_10, c['header'])
        # Input field
        draw_rectangle(GR_AFF, field_x1, bar_y + 2, field_x2, bar_y + 18,
                       c['bg'], 255, c['bg'], 255)
        # Field border
        draw_rectangle(GR_AFF, field_x1, bar_y + 2, field_x2, bar_y + 3,
                       c['table_border'], 255, c['table_border'], 255)
        draw_rectangle(GR_AFF, field_x1, bar_y + 17, field_x2, bar_y + 18,
                       c['table_border'], 255, c['table_border'], 255)
        draw_rectangle(GR_AFF, field_x1, bar_y + 2, field_x1 + 1, bar_y + 18,
                       c['table_border'], 255, c['table_border'], 255)
        draw_rectangle(GR_AFF, field_x2 - 1, bar_y + 2, field_x2, bar_y + 18,
                       c['table_border'], 255, c['table_border'], 255)
        # Text + cursor
        display = text
        tw = text_width(display, FONT_10)
        while tw > max_text_w and len(display) > 0:
            display = display[1:]
            tw = text_width(display, FONT_10)
        draw_text(GR_AFF, field_x1 + 4, bar_y + 4, display, FONT_10,
                  c['normal'], max_text_w)
        cx = field_x1 + 4 + tw
        if cx < field_x2 - 4:
            draw_rectangle(GR_AFF, cx, bar_y + 4, cx + 1, bar_y + 16,
                           c['normal'], 255, c['normal'], 255)
        # OK button
        draw_rectangle(GR_AFF, ok_x1, ok_y1, ok_x2, ok_y2,
                       c['header'], 255, c['header'], 255)
        okw = text_width("OK", FONT_10)
        draw_text(GR_AFF, ok_x1 + (ok_x2 - ok_x1 - okw) // 2,
                  bar_y + 4, "OK", FONT_10, 0xFFFFFF)

    draw_bar()

    while True:
        k = get_key()
        if k > 0:
            if k == KEY_ENTER:
                return text if text else None
            elif k == KEY_ESC:
                return None
            elif k == KEY_BACKSPACE:
                if text:
                    text = text[:-1]
                    draw_bar()
            elif k in key_chars:
                text += key_chars[k]
                draw_bar()

        tx, ty = get_touch()
        if tx >= 0 and ty >= 0:
            touch_was_down = True
            tap_x = tx
            tap_y = ty
        elif touch_was_down:
            touch_was_down = False
            if ok_x1 <= tap_x <= ok_x2 and ok_y1 <= tap_y <= ok_y2:
                return text if text else None


# ---------------------------------------------------------------------------
# Context menu (popup)
# ---------------------------------------------------------------------------

def show_context_menu(x, y, items, content_bottom=220, colors=None):
    """Show a popup context menu near (x, y).

    Args:
        x, y: touch coordinates where the menu should appear.
        items: list of label strings.
        content_bottom: lower bound of the content area (popup won't overlap).
        colors: dict with keys ctx_bg, ctx_border, ctx_text.

    Returns:
        Index of selected item (0-based), or -1 on cancel.
    """
    c = _c(colors)
    padding = 6
    item_h = 18
    max_w = 0
    for item in items:
        w = text_width(item, FONT_10)
        if w > max_w:
            max_w = w
    popup_w = max_w + padding * 2 + 4
    popup_h = len(items) * item_h + padding * 2
    # Keep on screen
    px = x - popup_w // 2
    py = y - popup_h - 5
    if px < 2:
        px = 2
    if px + popup_w > 318:
        px = 318 - popup_w
    if py < 2:
        py = y + 5
    if py + popup_h > content_bottom - 2:
        py = content_bottom - 2 - popup_h
    # Border + background
    draw_rectangle(GR_AFF, px - 1, py - 1, px + popup_w + 1, py + popup_h + 1,
                   c['ctx_border'], 255, c['ctx_border'], 255)
    draw_rectangle(GR_AFF, px, py, px + popup_w, py + popup_h,
                   c['ctx_bg'], 255, c['ctx_bg'], 255)
    for i, item in enumerate(items):
        iy = py + padding + i * item_h
        draw_text(GR_AFF, px + padding, iy + 2, item, FONT_10, c['ctx_text'])

    # Wait for current touch to end
    while True:
        tx, ty = get_touch()
        if tx < 0:
            break
    # Wait for new tap
    touch_down = False
    tap_x = -1
    tap_y = -1
    while True:
        k = get_key()
        if k == KEY_ESC:
            return -1
        tx, ty = get_touch()
        if tx >= 0 and ty >= 0:
            touch_down = True
            tap_x = tx
            tap_y = ty
        elif touch_down:
            touch_down = False
            if px <= tap_x <= px + popup_w and py <= tap_y <= py + popup_h:
                idx = (tap_y - py - padding) // item_h
                if 0 <= idx < len(items):
                    return idx
            return -1


# ---------------------------------------------------------------------------
# List manager (generic scrollable list with optional delete)
# ---------------------------------------------------------------------------

def show_list_manager(title, subtitle, items, empty_lines=None,
                      hint="", allow_delete=False, item_icon_color=None,
                      menu_y=220, colors=None):
    """Show a full-screen scrollable list manager.

    Args:
        title: heading centred at top.
        subtitle: smaller text below heading.
        items: list of label strings to display.
        empty_lines: list of strings to show when items is empty.
        hint: text at bottom (e.g. key instructions).
        allow_delete: if True, shows a Del button on the selected row.
        item_icon_color: if set, draw a small colored square before each
                         unselected item (e.g. bookmark color).
        menu_y: Y position of external menu bar (content stops here).
        colors: dict with keys bg, header, italic, normal, table_border,
                browser_sel, browser_sel_text.

    Returns:
        'select:N'  — user chose item at index N.
        'delete:N'  — user asked to delete item at index N.
        None        — user cancelled (ESC).
    """
    c = _c(colors)
    selected = 0
    page_size = 7

    def draw_mgr():
        fillrect(0, 0, 0, 320, menu_y, c['bg'], c['bg'])
        tw = text_width(title, FONT_14)
        draw_text(GR_AFF, (320 - tw) // 2, 5, title, FONT_14, c['header'])
        draw_text(GR_AFF, 10, 25, subtitle, FONT_10, c['italic'])
        draw_rectangle(GR_AFF, 5, 40, 315, 41,
                       c['table_border'], 255, c['table_border'], 255)
        if not items:
            if empty_lines:
                for j, line in enumerate(empty_lines):
                    draw_text(GR_AFF, 15, 60 + j * 15, line, FONT_10,
                              c['italic'] if j == 0 else c['normal'])
        else:
            start = 0
            if selected >= page_size:
                start = selected - page_size + 1
            for i in range(start, min(start + page_size, len(items))):
                iy = 48 + (i - start) * 22
                label = items[i]
                del_right = 280 if allow_delete else 312
                if i == selected:
                    draw_rectangle(GR_AFF, 8, iy, del_right, iy + 18,
                                   c['browser_sel'], 255,
                                   c['browser_sel'], 255)
                    draw_text(GR_AFF, 15, iy + 2, label, FONT_10,
                              c['browser_sel_text'])
                    if allow_delete:
                        draw_rectangle(GR_AFF, 282, iy, 312, iy + 18,
                                       0xCC0000, 255, 0xCC0000, 255)
                        dw = text_width("Del", FONT_10)
                        draw_text(GR_AFF, 282 + (30 - dw) // 2, iy + 2,
                                  "Del", FONT_10, 0xFFFFFF)
                else:
                    icon_offset = 0
                    if item_icon_color is not None:
                        draw_rectangle(GR_AFF, 10, iy + 5, 14, iy + 13,
                                       item_icon_color, 255,
                                       item_icon_color, 255)
                        icon_offset = 10
                    draw_text(GR_AFF, 10 + icon_offset, iy + 2, label,
                              FONT_10, c['normal'])
        if hint:
            draw_rectangle(GR_AFF, 5, menu_y - 20, 315, menu_y - 19,
                           c['table_border'], 255, c['table_border'], 255)
            draw_text(GR_AFF, 10, menu_y - 16, hint, FONT_10, c['italic'])

    draw_mgr()
    touch_down = False
    tap_x = -1
    tap_y = -1

    while True:
        k = get_key()
        if k > 0:
            if k == KEY_ESC:
                return None
            elif k == KEY_ENTER:
                if items:
                    return 'select:' + str(selected)
            elif k == KEY_BACKSPACE and allow_delete:
                if items:
                    return 'delete:' + str(selected)
            elif k == KEY_UP:
                if selected > 0:
                    selected -= 1
                    draw_mgr()
            elif k == KEY_DOWN:
                if items and selected < len(items) - 1:
                    selected += 1
                    draw_mgr()

        tx, ty = get_touch()
        if tx >= 0 and ty >= 0:
            touch_down = True
            tap_x = tx
            tap_y = ty
        elif touch_down:
            touch_down = False
            if items and tap_y >= 48 and tap_y < 48 + page_size * 22:
                start = 0
                if selected >= page_size:
                    start = selected - page_size + 1
                row = (tap_y - 48) // 22
                idx = start + row
                if idx < len(items):
                    if allow_delete and tap_x >= 282 and idx == selected:
                        return 'delete:' + str(idx)
                    elif idx == selected:
                        return 'select:' + str(idx)
                    else:
                        selected = idx
                        draw_mgr()


# ---------------------------------------------------------------------------
# Document stats dialog
# ---------------------------------------------------------------------------

def show_stats_dialog(filename, line_count, word_count, read_min,
                      menu_y=220, colors=None):
    """Show a modal dialog with document statistics.

    Args:
        filename:   document filename.
        line_count: number of lines in the document.
        word_count: number of words.
        read_min:   estimated reading time in minutes.
        menu_y:     Y position of menu bar (dialog appears above).
        colors:     color dict.

    Blocks until the user presses ESC / Enter or taps outside the dialog.
    """
    c = _c(colors)
    # Dialog dimensions
    dw = 220
    dh = 110
    dx = (320 - dw) // 2
    dy = (menu_y - dh) // 2
    if dy < 10:
        dy = 10

    # Border + background
    draw_rectangle(GR_AFF, dx - 1, dy - 1, dx + dw + 1, dy + dh + 1,
                   c['ctx_border'], 255, c['ctx_border'], 255)
    draw_rectangle(GR_AFF, dx, dy, dx + dw, dy + dh,
                   c['ctx_bg'], 255, c['ctx_bg'], 255)

    # Title
    title = "Document Info"
    tw = text_width(title, FONT_14)
    draw_text(GR_AFF, dx + (dw - tw) // 2, dy + 6, title, FONT_14,
              c['ctx_text'])

    # Separator
    draw_rectangle(GR_AFF, dx + 10, dy + 26, dx + dw - 10, dy + 27,
                   c['ctx_border'], 255, c['ctx_border'], 255)

    # Stats
    col1_x = dx + 15
    col2_x = dx + 120
    row_y = dy + 34
    row_h = 16
    labels = ["File:", "Lines:", "Words:", "Read time:"]
    values = [
        filename if len(filename) <= 16 else filename[:14] + '..',
        str(line_count),
        str(word_count),
        str(read_min) + " min" if read_min > 0 else "< 1 min",
    ]
    for i in range(len(labels)):
        y = row_y + i * row_h
        draw_text(GR_AFF, col1_x, y, labels[i], FONT_10, c['ctx_text'])
        draw_text(GR_AFF, col2_x, y, values[i], FONT_10, c['ctx_text'])

    # Hint
    hint = "Press ESC or Enter to close"
    hw = text_width(hint, FONT_10)
    draw_text(GR_AFF, dx + (dw - hw) // 2, dy + dh - 16, hint, FONT_10,
              c['ctx_border'])

    # Wait for dismiss
    while True:
        tx, ty = get_touch()
        if tx < 0:
            break
    touch_down = False
    while True:
        k = get_key()
        if k == KEY_ESC or k == KEY_ENTER:
            return
        tx, ty = get_touch()
        if tx >= 0 and ty >= 0:
            touch_down = True
        elif touch_down:
            return
