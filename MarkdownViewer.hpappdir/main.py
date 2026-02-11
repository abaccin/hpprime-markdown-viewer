from constants import (GR_AFF, FONT_10, FONT_12, FONT_14,
    COLOR_BLACK, COLOR_WHITE, COLOR_HEADER, COLOR_RED, COLOR_GRAY,
    DRAG_THRESHOLD)
from hpprime import eval, fillrect, keyboard
from graphics import draw_text, draw_rectangle, text_width, get_mouse
from keycodes import KEY_UP, KEY_DOWN, KEY_ENTER, KEY_ON
from file_ops import list_files
from markdown_viewer import MarkdownViewer


def get_key():
    """Read the current key code, or 0 if none pressed."""
    if keyboard():
        return eval('GETKEY()')
    return 0


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


def draw_file_browser(md_files, selected):
    """Draw the file browser screen."""
    fillrect(0, 0, 0, 320, 240, COLOR_WHITE, COLOR_WHITE)
    tw = text_width("Markdown Viewer", FONT_14)
    draw_text(GR_AFF, (320 - tw) // 2, 5, "Markdown Viewer", FONT_14, COLOR_HEADER)
    draw_text(GR_AFF, 10, 25, "Select a Markdown file", FONT_12, COLOR_HEADER)
    draw_rectangle(GR_AFF, 5, 42, 315, 43, COLOR_HEADER, 255, COLOR_HEADER, 255)

    max_visible = 9
    start = 0
    if selected >= max_visible:
        start = selected - max_visible + 1

    for i in range(start, min(start + max_visible, len(md_files))):
        y = 50 + (i - start) * 20
        if i == selected:
            draw_rectangle(GR_AFF, 8, y - 2, 312, y + 16, COLOR_HEADER, 255, COLOR_HEADER, 255)
            draw_text(GR_AFF, 15, y, md_files[i], FONT_12, COLOR_WHITE)
        else:
            draw_text(GR_AFF, 15, y, md_files[i], FONT_12, COLOR_BLACK)

    if len(md_files) == 0:
        draw_text(GR_AFF, 15, 30, "No .md files found", FONT_10, COLOR_RED)

    draw_text(GR_AFF, 10, 225, "Up/Down:Select  Enter/Tap:Open  ON:Exit", FONT_10, COLOR_GRAY)


def file_browser():
    """Show file browser and return selected filename."""
    md_files = get_md_files()
    selected = 0
    max_visible = 9
    touch_down = False
    tap_x = -1
    tap_y = -1

    draw_file_browser(md_files, selected)

    try:
        while True:
            key = get_key()
            if key > 0:
                if key == KEY_UP:
                    if selected > 0:
                        selected -= 1
                        draw_file_browser(md_files, selected)
                elif key == KEY_DOWN:
                    if selected < len(md_files) - 1:
                        selected += 1
                        draw_file_browser(md_files, selected)
                elif key == KEY_ENTER:
                    if len(md_files) > 0:
                        return md_files[selected]

            # Handle touch: tap to select, tap selected to open
            tx, ty = get_touch()
            if tx >= 0 and ty >= 0:
                touch_down = True
                tap_x = tx
                tap_y = ty
            elif touch_down:
                # Finger just released — process tap
                touch_down = False
                if len(md_files) > 0 and tap_y >= 50 and tap_y < 230:
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
                            draw_file_browser(md_files, selected)

    except KeyboardInterrupt:
        return None


def clear_screen():
    """Clear the screen and terminal output on exit."""
    fillrect(0, 0, 0, 320, 240, 0, 0)


# Main function
def main():
    """Main entry point - file browser then markdown viewer."""
    filename = file_browser()
    if filename is None:
        clear_screen()
        return

    viewer = MarkdownViewer(GR_AFF)
    viewer.load_markdown_file(filename)
    viewer.render()

    drag_last_y = -1

    try:
        while True:
            key = get_key()
            if key > 0:
                if key == KEY_UP:
                    viewer.scroll_up()
                    viewer.render()
                elif key == KEY_DOWN:
                    viewer.scroll_down()
                    viewer.render()

            # Handle touch drag scrolling
            touch_y = get_touch_y()
            if touch_y >= 0:
                if drag_last_y >= 0:
                    delta = drag_last_y - touch_y
                    if abs(delta) >= DRAG_THRESHOLD:
                        viewer.scroll_by(delta)
                        viewer.render()
                        drag_last_y = touch_y
                else:
                    drag_last_y = touch_y
            else:
                drag_last_y = -1
    except KeyboardInterrupt:
        pass

    clear_screen()


try:
    main()
except KeyboardInterrupt:
    clear_screen()