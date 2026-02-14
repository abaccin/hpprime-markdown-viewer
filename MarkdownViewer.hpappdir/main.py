from constants import (GR_AFF, FONT_10, FONT_12, FONT_14, DRAG_THRESHOLD,
    MENU_Y, MENU_HEIGHT, VIEWER_HEIGHT)
from hpprime import eval, fillrect
from graphics import draw_text, draw_rectangle, text_width, get_mouse
from keycodes import (KEY_UP, KEY_DOWN, KEY_ENTER, KEY_ON, KEY_PLUS,
    KEY_MINUS, KEY_BACKSPACE, KEY_LOG, KEY_ESC, KEY_F1, KEY_F2, KEY_F6)
from file_ops import list_files
from markdown_viewer import MarkdownViewer
import theme

# Soft-key menu labels
BROWSER_MENU = ["", "", "", "", "", "Theme"]
VIEWER_MENU = ["Find", "Next", "", "", "", "Theme"]


def get_key():
    """Read the current key code, or 0 if none pressed."""
    k = eval('GETKEY()')
    return k if k > 0 else 0


def get_touch_y():
    """Get the Y coordinate of the current touch, or -1 if not touching."""
    try:
        m = get_mouse()
        if not m or type(m) is not list:
            return -1
        first = m[0]
        if type(first) is list:
            if len(first) >= 2 and first[0] >= 0:
                return int(first[1])
        elif type(first) in (int, float):
            if len(m) >= 2 and m[0] >= 0:
                return int(m[1])
    except Exception:
        pass
    return -1


def get_touch():
    """Get (x, y) of the current touch, or (-1, -1) if not touching."""
    try:
        m = get_mouse()
        if not m or type(m) is not list:
            return (-1, -1)
        first = m[0]
        if type(first) is list:
            if len(first) >= 2 and first[0] >= 0:
                return (int(first[0]), int(first[1]))
        elif type(first) in (int, float):
            if len(m) >= 2 and m[0] >= 0:
                return (int(m[0]), int(m[1]))
    except Exception:
        pass
    return (-1, -1)


def get_md_files():
    """Get list of .md files from storage."""
    all_files = list_files()
    md_files = []
    if all_files:
        for f in all_files:
            if str(f).endswith('.md'):
                md_files.append(str(f))
    return md_files


def save_bookmark(filename, scroll_pos):
    """Save last opened file and scroll position."""
    try:
        with open('.bookmark', 'w') as f:
            f.write(filename + '\n' + str(scroll_pos))
    except:
        pass


def load_bookmark():
    """Load last opened file and scroll position."""
    try:
        with open('.bookmark', 'r') as f:
            lines = f.read().strip().split('\n')
            if len(lines) >= 2:
                return lines[0], int(lines[1])
            elif len(lines) == 1:
                return lines[0], 0
    except:
        pass
    return None, 0


def show_search_dialog():
    """Show an on-screen search input bar. Returns text or None on cancel."""
    # Key-to-character map for text entry (HP Prime keys)
    key_chars = {
        14: 'a', 15: 'b', 16: 'c', 17: 'd', 18: 'e',
        20: 'f', 21: 'g', 22: 'h', 23: 'i', 24: 'j',
        25: 'k', 26: 'l', 27: 'm', 28: 'n', 29: 'o',
        31: 'p', 32: 'q', 33: 'r', 34: 's', 35: 't',
        37: 'u', 38: 'v', 39: 'w', 40: 'x', 42: 'y',
        43: 'z', 49: ' ', 48: '.', 45: '-',
    }
    text = ""
    bar_y = MENU_Y - 22
    ok_x1 = 282
    ok_x2 = 316
    ok_y1 = bar_y + 2
    ok_y2 = bar_y + 18
    touch_was_down = False
    tap_x = -1
    tap_y = -1

    def draw_bar():
        c = theme.colors
        # Background
        draw_rectangle(GR_AFF, 0, bar_y, 320, bar_y + 20,
                       c['table_header_bg'], 255, c['table_header_bg'], 255)
        # Top border
        draw_rectangle(GR_AFF, 0, bar_y, 320, bar_y + 1,
                       c['table_border'], 255, c['table_border'], 255)
        # Label
        draw_text(GR_AFF, 4, bar_y + 4, "Find:", FONT_10, c['header'])
        # Input field bg
        draw_rectangle(GR_AFF, 40, bar_y + 2, 278, bar_y + 18,
                       c['bg'], 255, c['bg'], 255)
        # Input field border
        draw_rectangle(GR_AFF, 40, bar_y + 2, 278, bar_y + 3,
                       c['table_border'], 255, c['table_border'], 255)
        draw_rectangle(GR_AFF, 40, bar_y + 17, 278, bar_y + 18,
                       c['table_border'], 255, c['table_border'], 255)
        draw_rectangle(GR_AFF, 40, bar_y + 2, 41, bar_y + 18,
                       c['table_border'], 255, c['table_border'], 255)
        draw_rectangle(GR_AFF, 277, bar_y + 2, 278, bar_y + 18,
                       c['table_border'], 255, c['table_border'], 255)
        # Text + cursor
        display = text
        tw = text_width(display, FONT_10)
        while tw > 225 and len(display) > 0:
            display = display[1:]
            tw = text_width(display, FONT_10)
        draw_text(GR_AFF, 44, bar_y + 4, display, FONT_10,
                  c['normal'], 228)
        # Cursor
        cx = 44 + tw
        if cx < 274:
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

        # Handle touch tap on OK button
        tx, ty = get_touch()
        if tx >= 0 and ty >= 0:
            touch_was_down = True
            tap_x = tx
            tap_y = ty
        elif touch_was_down:
            touch_was_down = False
            # Finger released - check if tap was on OK button
            if ok_x1 <= tap_x <= ok_x2 and ok_y1 <= tap_y <= ok_y2:
                return text if text else None


def draw_menu(labels):
    """Draw a soft-key menu bar at the bottom of the screen."""
    c = theme.colors
    menu_bg = c['menu_bg']
    menu_text = c['menu_text']
    menu_div = c['menu_divider']

    fillrect(0, 0, MENU_Y, 320, MENU_HEIGHT, menu_bg, menu_bg)

    slot_w = 53  # 320 / 6 ~= 53
    for i in range(6):
        x1 = i * slot_w
        x2 = (i + 1) * slot_w if i < 5 else 320

        if i > 0:
            draw_rectangle(GR_AFF, x1, MENU_Y + 2,
                           x1 + 1, MENU_Y + MENU_HEIGHT - 2,
                           menu_div, 255, menu_div, 255)

        label = labels[i] if i < len(labels) else ""
        if label:
            tw = text_width(label, FONT_10)
            tx = x1 + (x2 - x1 - tw) // 2
            draw_text(GR_AFF, tx, MENU_Y + 5, label, FONT_10, menu_text)


def get_menu_tap(tx, ty):
    """If (tx, ty) is in the menu bar, return slot index 0-5. Else -1."""
    if ty >= MENU_Y and ty < MENU_Y + MENU_HEIGHT:
        slot = tx // 53
        if slot > 5:
            slot = 5
        return slot
    return -1


def draw_file_browser(md_files, selected, last_file=None):
    """Draw the file browser screen."""
    c = theme.colors
    fillrect(0, 0, 0, 320, MENU_Y, c['browser_bg'], c['browser_bg'])

    tw = text_width("Markdown Viewer", FONT_14)
    draw_text(GR_AFF, (320 - tw) // 2, 5, "Markdown Viewer", FONT_14,
              c['browser_subtitle'])
    draw_text(GR_AFF, 10, 25, "Select a Markdown file", FONT_12,
              c['browser_subtitle'])

    bdr_bottom = MENU_Y - 3
    draw_rectangle(GR_AFF, 5, 42, 315, 43, c['browser_border'], 255,
                   c['browser_border'], 255)
    draw_rectangle(GR_AFF, 5, 43, 6, bdr_bottom, c['browser_border'], 255,
                   c['browser_border'], 255)
    draw_rectangle(GR_AFF, 314, 43, 315, bdr_bottom, c['browser_border'], 255,
                   c['browser_border'], 255)

    max_visible = 8
    start = 0
    if selected >= max_visible:
        start = selected - max_visible + 1

    for i in range(start, min(start + max_visible, len(md_files))):
        y = 50 + (i - start) * 20
        if i == selected:
            draw_rectangle(GR_AFF, 8, y - 2, 312, y + 16,
                           c['browser_sel'], 255, c['browser_sel'], 255)
            draw_text(GR_AFF, 15, y, md_files[i], FONT_12,
                      c['browser_sel_text'])
        else:
            label = md_files[i]
            if last_file and md_files[i] == last_file:
                label = '\u25B6 ' + label
            draw_text(GR_AFF, 15, y, label, FONT_12, c['browser_text'])

    if len(md_files) == 0:
        draw_text(GR_AFF, 15, 60, "No .md files found", FONT_10,
                  c['browser_error'])

    draw_rectangle(GR_AFF, 5, bdr_bottom, 315, bdr_bottom + 1,
                   c['browser_border'], 255, c['browser_border'], 255)
    draw_menu(BROWSER_MENU)


def file_browser(last_file=None):
    """Show file browser and return selected filename."""
    md_files = get_md_files()
    selected = 0

    # Pre-select last opened file
    if last_file and last_file in md_files:
        selected = md_files.index(last_file)

    max_visible = 8
    touch_down = False
    tap_x = -1
    tap_y = -1

    draw_file_browser(md_files, selected, last_file)

    try:
        while True:
            key = get_key()
            if key > 0:
                if key == KEY_UP:
                    if selected > 0:
                        selected -= 1
                        draw_file_browser(md_files, selected, last_file)
                elif key == KEY_DOWN:
                    if selected < len(md_files) - 1:
                        selected += 1
                        draw_file_browser(md_files, selected, last_file)
                elif key == KEY_ENTER:
                    if len(md_files) > 0:
                        return md_files[selected]
                elif key == KEY_F6:
                    theme.toggle()
                    draw_file_browser(md_files, selected, last_file)

            # Handle touch: tap to select, tap selected to open, tap menu
            tx, ty = get_touch()
            if tx >= 0 and ty >= 0:
                touch_down = True
                tap_x = tx
                tap_y = ty
            elif touch_down:
                touch_down = False
                # Check menu tap first
                slot = get_menu_tap(tap_x, tap_y)
                if slot == 5:  # Theme
                    theme.toggle()
                    draw_file_browser(md_files, selected, last_file)
                elif len(md_files) > 0 and tap_y >= 50 and tap_y < MENU_Y:
                    start = 0
                    if selected >= max_visible:
                        start = selected - max_visible + 1
                    row = (tap_y - 50) // 20
                    tapped = start + row
                    if tapped < len(md_files):
                        if tapped == selected:
                            return md_files[selected]
                        else:
                            selected = tapped
                            draw_file_browser(md_files, selected, last_file)

    except KeyboardInterrupt:
        return None


def clear_screen():
    """Clear the screen on exit."""
    fillrect(0, 0, 0, 320, 240, 0, 0)


# Main function
def main():
    """Main entry point - file browser then markdown viewer with back navigation."""
    last_file, last_scroll = load_bookmark()

    while True:
        filename = file_browser(last_file)
        if filename is None:
            clear_screen()
            return

        viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT)
        viewer.load_markdown_file(filename)

        # Restore scroll position if reopening same file
        if filename == last_file and last_scroll > 0:
            viewer.set_scroll_position(last_scroll)

        # Clear screen and draw viewer + menu
        fillrect(0, 0, 0, 320, MENU_Y,
                 theme.colors['bg'], theme.colors['bg'])
        viewer.render()
        draw_menu(VIEWER_MENU)

        drag_last_y = -1
        touch_down = False
        tap_x = -1
        tap_y = -1
        action = 'back'

        try:
            while True:
                key = get_key()
                if key > 0:
                    if key == KEY_ESC:
                        break  # Back to file browser
                    elif key == KEY_UP:
                        viewer.scroll_up()
                    elif key == KEY_DOWN:
                        viewer.scroll_down()
                    elif key == KEY_PLUS:
                        viewer.scroll_page_down()
                    elif key == KEY_MINUS:
                        viewer.scroll_page_up()
                    elif key == KEY_BACKSPACE:
                        viewer.scroll_to_top()
                    elif key == KEY_LOG:
                        viewer.scroll_to_bottom()
                    elif key == KEY_F1:
                        term = show_search_dialog()
                        # Redraw after dialog overlay
                        fillrect(0, 0, 0, 320, MENU_Y,
                                 theme.colors['bg'], theme.colors['bg'])
                        if term:
                            viewer.search(term)
                        else:
                            viewer.render()
                        draw_menu(VIEWER_MENU)
                    elif key == KEY_F2:
                        viewer.search_next()
                    elif key == KEY_F6:
                        viewer.toggle_theme()
                        draw_menu(VIEWER_MENU)

                # Handle touch: drag scrolling + menu taps
                tx, ty = get_touch()
                if tx >= 0 and ty >= 0:
                    if not touch_down:
                        touch_down = True
                        tap_x = tx
                        tap_y = ty
                        drag_last_y = ty
                    else:
                        # Dragging in content area
                        if ty < MENU_Y and drag_last_y >= 0:
                            delta = drag_last_y - ty
                            if abs(delta) >= DRAG_THRESHOLD:
                                viewer.scroll_by(delta)
                                viewer.render()
                                drag_last_y = ty
                else:
                    if touch_down:
                        touch_down = False
                        # Check if it was a tap (not a drag)
                        moved = abs(tap_y - drag_last_y) if drag_last_y >= 0 else 0
                        if moved < DRAG_THRESHOLD * 2:
                            slot = get_menu_tap(tap_x, tap_y)
                            if slot == 0:  # Find
                                term = show_search_dialog()
                                fillrect(0, 0, 0, 320, MENU_Y,
                                         theme.colors['bg'],
                                         theme.colors['bg'])
                                if term:
                                    viewer.search(term)
                                else:
                                    viewer.render()
                                draw_menu(VIEWER_MENU)
                            elif slot == 1:  # Next
                                viewer.search_next()
                            elif slot == 5:  # Theme
                                viewer.toggle_theme()
                                draw_menu(VIEWER_MENU)
                        drag_last_y = -1
        except KeyboardInterrupt:
            action = 'exit'

        # Save bookmark
        last_file = filename
        last_scroll = viewer.get_scroll_position()
        save_bookmark(filename, last_scroll)

        if action == 'exit':
            clear_screen()
            return
        # action == 'back': loop continues to file browser


try:
    main()
except KeyboardInterrupt:
    clear_screen()
