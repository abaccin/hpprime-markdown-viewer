"""MarkdownViewer for HP Prime — main entry point."""

from constants import (GR_AFF, DRAG_THRESHOLD, MENU_Y, VIEWER_HEIGHT,
    LONG_PRESS_MS)
from hpprime import fillrect
from keycodes import (KEY_UP, KEY_DOWN, KEY_ESC, KEY_PLUS,
    KEY_MINUS, KEY_BACKSPACE, KEY_LOG, KEY_F1, KEY_F2, KEY_F6)
from markdown_viewer import MarkdownViewer
from input_helpers import get_key, get_touch, get_ticks, get_menu_tap
from ui import (draw_menu, show_input_bar, show_context_menu,
    show_list_manager)
from browser import file_picker
import theme
import bookmarks

VIEWER_MENU = ["Find", "Next", "Marks", "", "", "Theme"]
BROWSER_MENU = ["", "", "", "", "", "Theme"]


def save_last_file(filename, scroll_pos):
    """Save last opened file and scroll position."""
    try:
        with open('.bookmark', 'w') as f:
            f.write(filename + '\n' + str(scroll_pos))
    except:
        pass


def load_last_file():
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


def clear_screen():
    fillrect(0, 0, 0, 320, 240, 0, 0)


def _browser_menu_tap(slot):
    """Handle menu taps in the file browser. Returns True if redraw needed."""
    if slot == 5:
        theme.toggle()
        return True
    return False


def main():
    """Main entry point — file browser then markdown viewer."""
    last_file, last_scroll = load_last_file()

    while True:
        filename = file_picker(
            title="Markdown Viewer",
            subtitle="Select a Markdown file",
            ext='.md',
            menu_labels=BROWSER_MENU,
            on_menu_tap=_browser_menu_tap,
            highlight=last_file,
            menu_y=MENU_Y,
        )
        if filename is None:
            clear_screen()
            return

        viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT)
        viewer.load_markdown_file(filename)

        if filename == last_file and last_scroll > 0:
            viewer.set_scroll_position(last_scroll)

        marks = bookmarks.load(filename)
        viewer.set_bookmarks(marks)

        fillrect(0, 0, 0, 320, MENU_Y,
                 theme.colors['bg'], theme.colors['bg'])
        viewer.render()
        draw_menu(VIEWER_MENU, menu_y=MENU_Y)

        drag_last_y = -1
        touch_down = False
        tap_x = -1
        tap_y = -1
        touch_start_time = 0
        long_press_fired = False
        action = 'back'

        def redraw():
            fillrect(0, 0, 0, 320, MENU_Y,
                     theme.colors['bg'], theme.colors['bg'])
            viewer.render()
            draw_menu(VIEWER_MENU, menu_y=MENU_Y)

        def do_search():
            term = show_input_bar(label="Find:", menu_y=MENU_Y)
            fillrect(0, 0, 0, 320, MENU_Y,
                     theme.colors['bg'], theme.colors['bg'])
            if term:
                viewer.search(term)
            else:
                viewer.render()
            draw_menu(VIEWER_MENU, menu_y=MENU_Y)

        def open_bookmark_mgr():
            nonlocal marks
            labels = ["Position " + str(p) for p in marks]
            while True:
                result = show_list_manager(
                    title="Bookmarks",
                    subtitle=filename,
                    items=labels,
                    empty_lines=["No bookmarks yet.",
                                 "Long-press in the document",
                                 "to add a bookmark."],
                    hint="Enter=Go  Del=Remove  ESC=Close",
                    allow_delete=True,
                    item_icon_color=theme.colors['bookmark_mark'],
                    menu_y=MENU_Y,
                )
                if result is None:
                    break
                elif result.startswith('select:'):
                    idx = int(result[7:])
                    if idx < len(marks):
                        viewer.set_scroll_position(marks[idx])
                        break
                elif result.startswith('delete:'):
                    idx = int(result[7:])
                    if idx < len(marks):
                        marks = bookmarks.remove(filename, marks[idx])
                        viewer.set_bookmarks(marks)
                        labels = ["Position " + str(p) for p in marks]
            redraw()

        try:
            while True:
                key = get_key()
                if key > 0:
                    if key == KEY_ESC:
                        break
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
                        do_search()
                    elif key == KEY_F2:
                        viewer.search_next()
                    elif key == KEY_F6:
                        viewer.toggle_theme()
                        draw_menu(VIEWER_MENU, menu_y=MENU_Y)

                tx, ty = get_touch()
                if tx >= 0 and ty >= 0:
                    if not touch_down:
                        touch_down = True
                        tap_x = tx
                        tap_y = ty
                        drag_last_y = ty
                        touch_start_time = get_ticks()
                        long_press_fired = False
                    else:
                        moved_lp = abs(tx - tap_x) + abs(ty - tap_y)
                        if (not long_press_fired and
                                moved_lp < DRAG_THRESHOLD * 3 and
                                tap_y < MENU_Y):
                            elapsed = get_ticks() - touch_start_time
                            if elapsed >= LONG_PRESS_MS:
                                long_press_fired = True
                                choice = show_context_menu(
                                    tap_x, tap_y, ["Add Bookmark"],
                                    content_bottom=MENU_Y)
                                if choice == 0:
                                    pos = viewer.get_scroll_position()
                                    marks = bookmarks.add(filename, pos)
                                    viewer.set_bookmarks(marks)
                                redraw()
                                touch_down = False
                                drag_last_y = -1
                        else:
                            if ty < MENU_Y and drag_last_y >= 0:
                                delta = drag_last_y - ty
                                if abs(delta) >= DRAG_THRESHOLD:
                                    viewer.scroll_by(delta)
                                    viewer.render()
                                    drag_last_y = ty
                else:
                    if touch_down:
                        touch_down = False
                        if not long_press_fired:
                            moved = abs(tap_y - drag_last_y) if drag_last_y >= 0 else 0
                            if moved < DRAG_THRESHOLD * 2:
                                slot = get_menu_tap(tap_x, tap_y, MENU_Y)
                                if slot == 0:
                                    do_search()
                                elif slot == 1:
                                    viewer.search_next()
                                elif slot == 2:
                                    open_bookmark_mgr()
                                elif slot == 5:
                                    viewer.toggle_theme()
                                    draw_menu(VIEWER_MENU, menu_y=MENU_Y)
                        drag_last_y = -1
        except KeyboardInterrupt:
            action = 'exit'

        last_file = filename
        last_scroll = viewer.get_scroll_position()
        save_last_file(filename, last_scroll)

        if action == 'exit':
            clear_screen()
            return


try:
    main()
except KeyboardInterrupt:
    clear_screen()
