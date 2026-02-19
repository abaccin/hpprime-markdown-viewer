"""MarkdownViewer for HP Prime — main entry point."""

from constants import (GR_AFF, DRAG_THRESHOLD, MENU_Y, VIEWER_HEIGHT_FULL,
    LONG_PRESS_MS, FONT_10)
from hpprime import fillrect
from keycodes import (KEY_UP, KEY_DOWN, KEY_ESC, KEY_PLUS,
    KEY_MINUS, KEY_BACKSPACE, KEY_LOG, KEY_F1, KEY_F2,
    KEY_F3, KEY_F4, KEY_F5, KEY_F6)
from markdown_viewer import MarkdownViewer
from input_helpers import get_key, get_key_fast, get_touch, get_ticks, get_menu_tap, mouse_clear
from ui import (draw_menu, draw_notch, is_notch_tap,
    save_menu_area, restore_menu_area,
    show_search_input, show_context_menu, show_list_manager,
    show_stats_dialog)
from graphics import draw_text, text_width
from browser import file_picker
import theme
import bookmarks
import file_prefs

VIEWER_MENU = ["Find", "Next", "Marks", "TOC", "Info", "Theme"]
BROWSER_MENU = ["Recent", "", "", "", "", "Theme"]


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


def _browser_menu_tap(slot, selected_file):
    """Handle menu taps in the file browser.

    Returns:
        True      — redraw the browser screen.
        'reload'  — rebuild file list and redraw.
        'open:f'  — open file f directly.
        False     — no action.
    """
    if slot == 0:  # Recent
        recent = file_prefs.get_recent()
        if not recent:
            return True
        result = show_list_manager(
            title="Recent Files",
            subtitle="Last opened",
            items=recent,
            empty_lines=["No recent files."],
            hint="Enter=Open  ESC=Close",
            allow_delete=False,
            menu_y=MENU_Y,
        )
        if result is not None and result.startswith('select:'):
            idx = int(result[7:])
            if idx < len(recent):
                return 'open:' + recent[idx]
        return True
    elif slot == 5:  # Theme
        theme.toggle()
        return True
    return False


_search_pill_x = 320  # left edge of the search status pill


def _draw_search_status(viewer):
    """Draw 'X of Y' search match counter at bottom-right."""
    global _search_pill_x
    info = viewer.get_search_info()
    c = theme.colors
    _search_pill_x = 320
    sy = 227
    if info:
        cur, total = info
        label = str(cur) + ' of ' + str(total) + ' matches'
        tw = text_width(label, FONT_10)
        sw = tw + 8
        _search_pill_x = 320 - sw
        fillrect(GR_AFF, _search_pill_x, sy, sw, 13, c['menu_bg'], c['menu_bg'])
        draw_text(GR_AFF, _search_pill_x + 4, sy + 2, label, FONT_10, c['menu_text'])


def _draw_progress(viewer):
    """Draw a small progress pill at the bottom-left, styled like the notch."""
    pct = viewer.get_progress_percent()
    label = str(pct) + '%'
    tw = text_width(label, FONT_10)
    pw = tw + 8
    px = 0
    py = 227
    c = theme.colors
    fillrect(GR_AFF, px, py, pw, 13, c['menu_bg'], c['menu_bg'])
    draw_text(GR_AFF, px + 4, py + 2, label, FONT_10, c['menu_text'])
    _draw_search_status(viewer)
    # Thin reading progress bar at the very top of the screen
    bar_w = int(320 * pct / 100) if pct < 100 else 320
    bar_c = c.get('progress_bar', c['header'])
    bg = c['bg']
    if bar_w > 0:
        fillrect(GR_AFF, 0, 0, bar_w, 2, bar_c, bar_c)
    if bar_w < 320:
        fillrect(GR_AFF, bar_w, 0, 320 - bar_w, 2, bg, bg)


def main():
    """Main entry point — file browser then markdown viewer."""
    theme.init()
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

        file_prefs.add_recent(filename)

        # Navigation back-stack: list of (filename, scroll_pos)
        nav_stack = []
        viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT_FULL)
        viewer.load_markdown_file(filename)

        if filename == last_file and last_scroll > 0:
            viewer.set_scroll_position(last_scroll)

        marks = bookmarks.load(filename)
        viewer.set_bookmarks(marks)

        drag_last_y = -1
        touch_down = False
        tap_x = -1
        tap_y = -1
        touch_start_time = 0
        long_press_fired = False
        menu_visible = False
        action = 'back'
        scrollbar_dragging = False

        def _draw_overlay():
            """Draw notch + progress bar (called after every scroll/render)."""
            draw_notch()
            _draw_progress(viewer)

        def redraw():
            fillrect(0, 0, 0, 320, 240,
                     theme.colors['bg'], theme.colors['bg'])
            viewer.render()
            _draw_overlay()

        fillrect(0, 0, 0, 320, 240,
                 theme.colors['bg'], theme.colors['bg'])
        viewer.render()
        _draw_overlay()

        def hide_menu():
            nonlocal menu_visible
            if menu_visible:
                restore_menu_area(MENU_Y)
                draw_notch()
                menu_visible = False

        def show_menu():
            nonlocal menu_visible
            save_menu_area(MENU_Y)
            draw_menu(VIEWER_MENU, menu_y=MENU_Y)
            menu_visible = True

        search_case = False

        def do_search():
            nonlocal menu_visible, search_case
            menu_visible = False
            term, search_case = show_search_input(
                case_sensitive=search_case, menu_y=MENU_Y)
            mouse_clear()
            fillrect(0, 0, 0, 320, 240,
                     theme.colors['bg'], theme.colors['bg'])
            if term:
                viewer.search(term, case_sensitive=search_case)
            else:
                viewer.clear_search()
            _draw_overlay()

        def open_bookmark_mgr():
            nonlocal marks, menu_visible
            menu_visible = False
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
            mouse_clear()
            redraw()

        def open_toc():
            nonlocal menu_visible
            menu_visible = False
            headers = viewer.get_headers()
            if not headers:
                redraw()
                return
            labels = []
            for level, title, _ in headers:
                prefix = '  ' * (level - 1)
                labels.append(prefix + title)
            result = show_list_manager(
                title="Table of Contents",
                subtitle=filename,
                items=labels,
                empty_lines=["No headers found."],
                hint="Enter=Jump  ESC=Close",
                allow_delete=False,
                menu_y=MENU_Y,
            )
            if result is not None and result.startswith('select:'):
                idx = int(result[7:])
                if idx < len(headers):
                    _, _, line_idx = headers[idx]
                    viewer.scroll_to_line(line_idx)
                    _draw_overlay()
                    return
            redraw()

        def open_stats():
            nonlocal menu_visible
            menu_visible = False
            lines, words, mins = viewer.get_document_stats()
            show_stats_dialog(filename, lines, words, mins, MENU_Y)
            redraw()

        def navigate_link(url):
            """Open a .md link, pushing current file onto the back-stack."""
            nonlocal filename, marks, viewer
            if not url.endswith('.md'):
                return False
            nav_stack.append((filename, viewer.get_scroll_position()))
            filename = url
            viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT_FULL)
            viewer.load_markdown_file(filename)
            marks = bookmarks.load(filename)
            viewer.set_bookmarks(marks)
            redraw()
            return True

        def navigate_back():
            """Pop the back-stack, returning to the previous file."""
            nonlocal filename, marks, viewer
            if not nav_stack:
                return False
            prev_file, prev_scroll = nav_stack.pop()
            filename = prev_file
            viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT_FULL)
            viewer.load_markdown_file(filename)
            viewer.set_scroll_position(prev_scroll)
            marks = bookmarks.load(filename)
            viewer.set_bookmarks(marks)
            redraw()
            return True

        try:
            while True:
                key = get_key()
                if key > 0:
                    if menu_visible:
                        hide_menu()
                    if key == KEY_ESC:
                        if not navigate_back():
                            break
                        continue
                    elif key == KEY_UP:
                        viewer.scroll_up()
                        _draw_overlay()
                    elif key == KEY_DOWN:
                        viewer.scroll_down()
                        _draw_overlay()
                    elif key == KEY_PLUS:
                        viewer.scroll_page_down()
                        _draw_overlay()
                    elif key == KEY_MINUS:
                        viewer.scroll_page_up()
                        _draw_overlay()
                    elif key == KEY_BACKSPACE:
                        viewer.scroll_to_top()
                        _draw_overlay()
                    elif key == KEY_LOG:
                        viewer.scroll_to_bottom()
                        _draw_overlay()
                    elif key == KEY_F1:
                        do_search()
                    elif key == KEY_F2:
                        viewer.search_next()
                        _draw_overlay()
                    elif key == KEY_F3:
                        open_toc()
                    elif key == KEY_F4:
                        open_toc()
                    elif key == KEY_F5:
                        open_stats()
                    elif key == KEY_F6:
                        theme.toggle()
                        redraw()

                tx, ty = get_touch()
                if tx >= 0 and ty >= 0:
                    if not touch_down:
                        touch_down = True
                        tap_x = tx
                        tap_y = ty
                        drag_last_y = ty
                        touch_start_time = get_ticks()
                        long_press_fired = False
                        # Check if starting a scrollbar drag
                        if not menu_visible and viewer.is_scrollbar_tap(tx, ty):
                            scrollbar_dragging = True
                            ratio = viewer.scrollbar_y_to_ratio(ty)
                            viewer.scroll_to_ratio(ratio)
                            viewer.render()
                            _draw_overlay()
                    else:
                        # Continue scrollbar drag
                        if scrollbar_dragging:
                            ratio = viewer.scrollbar_y_to_ratio(ty)
                            viewer.scroll_to_ratio(ratio)
                            viewer.render()
                            _draw_overlay()
                        else:
                            moved_lp = abs(tx - tap_x) + abs(ty - tap_y)
                            if (not long_press_fired and
                                    not menu_visible and
                                    moved_lp < DRAG_THRESHOLD * 3 and
                                    tap_y < MENU_Y):
                                elapsed = get_ticks() - touch_start_time
                                if elapsed >= LONG_PRESS_MS:
                                    long_press_fired = True
                                    choice = show_context_menu(
                                        tap_x, tap_y, ["Add Bookmark"],
                                        content_bottom=240)
                                    if choice == 0:
                                        pos = viewer.get_scroll_position()
                                        marks = bookmarks.add(filename, pos)
                                        viewer.set_bookmarks(marks)
                                    redraw()
                                    touch_down = False
                                    drag_last_y = -1
                            else:
                                if not menu_visible and ty < MENU_Y and drag_last_y >= 0:
                                    delta = drag_last_y - ty
                                    if abs(delta) >= DRAG_THRESHOLD:
                                        viewer.scroll_by_fast(delta)
                                        _draw_overlay()
                                        drag_last_y = ty
                else:
                    if touch_down:
                        touch_down = False
                        scrollbar_dragging = False
                        if not long_press_fired:
                            moved = abs(tap_y - drag_last_y) if drag_last_y >= 0 else 0
                            if moved < DRAG_THRESHOLD * 2:
                                if menu_visible:
                                    slot = get_menu_tap(tap_x, tap_y, MENU_Y)
                                    if slot >= 0:
                                        if slot == 0:
                                            do_search()
                                        elif slot == 1:
                                            viewer.search_next()
                                            hide_menu()
                                            _draw_progress(viewer)
                                        elif slot == 2:
                                            open_bookmark_mgr()
                                        elif slot == 3:
                                            open_toc()
                                        elif slot == 4:
                                            open_stats()
                                        elif slot == 5:
                                            theme.toggle()
                                            menu_visible = False
                                            redraw()
                                    else:
                                        hide_menu()
                                elif is_notch_tap(tap_x, tap_y):
                                    show_menu()
                                elif (tap_y >= 227 and tap_y <= 240
                                      and tap_x >= _search_pill_x
                                      and _search_pill_x < 320):
                                    viewer.search_next()
                                    _draw_overlay()
                                else:
                                    # Check for link tap
                                    url = viewer.get_link_at(tap_x, tap_y)
                                    if url:
                                        navigate_link(url)
                        drag_last_y = -1
        except KeyboardInterrupt:
            action = 'exit'

        last_file = filename
        last_scroll = viewer.get_scroll_position()
        save_last_file(filename, last_scroll)
        file_prefs.set_progress(filename, viewer.get_progress_percent())

        if action == 'exit':
            clear_screen()
            return


try:
    main()
except KeyboardInterrupt:
    clear_screen()
