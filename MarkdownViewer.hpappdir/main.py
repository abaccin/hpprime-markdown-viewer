"""MarkdownViewer for HP Prime — main entry point."""

import gc
import ppl_guard
from constants import (GR_AFF, DRAG_THRESHOLD, MENU_Y, VIEWER_HEIGHT_FULL,
    LONG_PRESS_MS, FONT_10)
from hpprime import fillrect
from keycodes import (KEY_UP, KEY_DOWN, KEY_ESC, KEY_PLUS,
    KEY_MINUS, KEY_BACKSPACE, KEY_LOG, KEY_F1, KEY_F2,
    KEY_F3, KEY_F4, KEY_F5, KEY_F6, KEY_LEFT, KEY_RIGHT)
from markdown_viewer import MarkdownViewer
from input_helpers import get_key, get_key_fast, get_touch, get_ticks, get_menu_tap, mouse_clear
from ui import (draw_menu, draw_notch, is_notch_tap,
    save_menu_area, restore_menu_area,
    show_search_input, show_context_menu, show_list_manager,
    show_stats_dialog, show_goto_dialog, show_shortcuts_overlay,
    show_about_dialog)
from graphics import draw_text, text_width
from browser import file_picker
import theme
import bookmarks
import file_prefs

VIEWER_MENU = ["Find", "Next", "Marks", "TOC", "More", "Theme"]
BROWSER_MENU = ["Recent", "", "", "About", "Help", "Theme"]


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
    elif slot == 3:  # About
        show_about_dialog(MENU_Y)
        return True
    elif slot == 4:  # Help
        return 'open:' + _find_help_file()
    elif slot == 5:  # Theme
        theme.toggle()
        return True
    return False


def _find_help_file():
    """Find the best help file based on system language."""
    try:
        from hpprime import eval as heval
        lang = None
        try:
            lang = heval('Language')
        except:
            return 'help.md'
        if lang is None:
            return 'help.md'
        codes = []
        if type(lang) is int:
            m = {2: 'es', 3: 'fr', 4: 'de', 5: 'it', 6: 'pt'}
            if lang in m:
                codes.append(m[lang])
        elif type(lang) is str:
            lang_l = lang[:4].lower()
            for prefix, code in [('espa', 'es'), ('fran', 'fr'),
                                  ('deut', 'de'), ('ital', 'it')]:
                if prefix in lang_l:
                    codes.append(code)
                    break
        for code in codes:
            name = 'help_' + code + '.md'
            try:
                with open(name, 'r') as f:
                    f.read(1)
                return name
            except:
                pass
    except:
        pass
    return 'help.md'


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
    ppl_guard.init()
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
            return

        file_prefs.add_recent(filename)

        # Free browser memory before loading document
        gc.collect()

        # Navigation stacks: back and forward
        nav_stack = []
        fwd_stack = []
        split_mode = False
        viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT_FULL)
        viewer.load_markdown_file(filename)

        # Restore per-file scroll position
        saved_scroll = file_prefs.get_scroll_pos(filename)
        if saved_scroll > 0:
            viewer.set_scroll_position(saved_scroll)
        elif filename == last_file and last_scroll > 0:
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
            del fwd_stack[:]  # New direction clears forward history
            filename = url
            viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT_FULL)
            viewer.load_markdown_file(filename)
            saved_s = file_prefs.get_scroll_pos(filename)
            if saved_s > 0:
                viewer.set_scroll_position(saved_s)
            marks = bookmarks.load(filename)
            viewer.set_bookmarks(marks)
            redraw()
            return True

        def navigate_back():
            """Pop the back-stack, returning to the previous file."""
            nonlocal filename, marks, viewer
            if not nav_stack:
                return False
            fwd_stack.append((filename, viewer.get_scroll_position()))
            prev_file, prev_scroll = nav_stack.pop()
            filename = prev_file
            viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT_FULL)
            viewer.load_markdown_file(filename)
            viewer.set_scroll_position(prev_scroll)
            marks = bookmarks.load(filename)
            viewer.set_bookmarks(marks)
            redraw()
            return True

        def navigate_forward():
            """Pop the forward-stack, going to the next file."""
            nonlocal filename, marks, viewer
            if not fwd_stack:
                return False
            nav_stack.append((filename, viewer.get_scroll_position()))
            next_file, next_scroll = fwd_stack.pop()
            filename = next_file
            viewer = MarkdownViewer(GR_AFF, height=VIEWER_HEIGHT_FULL)
            viewer.load_markdown_file(filename)
            viewer.set_scroll_position(next_scroll)
            marks = bookmarks.load(filename)
            viewer.set_bookmarks(marks)
            redraw()
            return True

        def _draw_split_toc():
            """Draw the mini-TOC pane in split view mode."""
            c = theme.colors
            fillrect(0, 0, 0, 320, 82, c['bg'], c['bg'])
            from graphics import draw_rectangle as _dr
            _dr(GR_AFF, 0, 80, 320, 82,
                c['table_border'], 255, c['table_border'], 255)
            headers = viewer.get_headers()
            if not headers:
                draw_text(GR_AFF, 10, 5, "No headers",
                          FONT_10, c.get('italic', c['normal']))
                return
            cur = viewer.get_current_header_idx()
            max_show = 5
            start = max(0, cur - max_show // 2)
            sel_bg = c.get('browser_sel', 0x000080)
            sel_t = c.get('browser_sel_text', 0xFFFFFF)
            for i in range(start, min(start + max_show, len(headers))):
                y = 4 + (i - start) * 15
                level, title, _ = headers[i]
                prefix = '  ' * (level - 1)
                if i == cur:
                    fillrect(0, 5, y, 310, 14, sel_bg, sel_bg)
                    draw_text(GR_AFF, 10, y + 1, prefix + title,
                              FONT_10, sel_t, 300)
                else:
                    draw_text(GR_AFF, 10, y + 1, prefix + title,
                              FONT_10, c['normal'], 300)

        def toggle_split():
            nonlocal split_mode
            split_mode = not split_mode
            if split_mode:
                viewer.set_split_viewport(85, VIEWER_HEIGHT_FULL - 80)
            else:
                viewer.set_split_viewport(5, VIEWER_HEIGHT_FULL)
            redraw()
            if split_mode:
                _draw_split_toc()

        def open_more_menu():
            """Show the More submenu with settings and navigation."""
            nonlocal menu_visible
            menu_visible = False
            wrap_label = "Wrap: ON" if viewer.is_word_wrap() else "Wrap: OFF"
            font_label = "Font: " + viewer.get_font_label() + "px"
            split_label = "Split: ON" if split_mode else "Split: OFF"
            choices = [font_label, wrap_label, split_label,
                       "Go to %", "Shortcuts", "Doc Info"]
            if fwd_stack:
                choices.append("Forward \u25B6")
            choice = show_context_menu(160, 100, choices,
                                       content_bottom=220)
            if choice == 0:  # Font
                viewer.cycle_font()
                redraw()
            elif choice == 1:  # Wrap
                viewer.toggle_word_wrap()
                redraw()
            elif choice == 2:  # Split
                toggle_split()
            elif choice == 3:  # Go to %
                pct = show_goto_dialog()
                if pct is not None:
                    viewer.scroll_to_ratio(pct / 100.0)
                    viewer.render()
                redraw()
            elif choice == 4:  # Shortcuts
                show_shortcuts_overlay()
                redraw()
            elif choice == 5:  # Doc Info
                open_stats()
            elif choice == 6 and fwd_stack:
                navigate_forward()
            else:
                redraw()

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
                        open_more_menu()
                    elif key == KEY_F6:
                        theme.toggle()
                        redraw()
                    elif key == KEY_LEFT:
                        if not navigate_back():
                            break
                        continue
                    elif key == KEY_RIGHT:
                        navigate_forward()

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
                                    ctx_items = ["Add Bookmark",
                                                 "Copy Line"]
                                    # Add tag assignment
                                    cur_tag = file_prefs.get_tag(filename)
                                    tag_label = "Tag: " + file_prefs.TAG_NAMES[cur_tag]
                                    ctx_items.append(tag_label)
                                    choice = show_context_menu(
                                        tap_x, tap_y, ctx_items,
                                        content_bottom=240)
                                    if choice == 0:
                                        pos = viewer.get_scroll_position()
                                        marks = bookmarks.add(filename, pos)
                                        viewer.set_bookmarks(marks)
                                    elif choice == 1:
                                        line_text = viewer.get_line_text_at_y(tap_y)
                                        if line_text:
                                            safe = line_text.replace('\\', '\\\\').replace('"', '\\"')
                                            from hpprime import eval as _he
                                            _he('AVars("Clipboard"):="' + safe + '"')
                                    elif choice == 2:
                                        # Cycle tag
                                        new_tag = (cur_tag + 1) % len(file_prefs.TAG_NAMES)
                                        file_prefs.set_tag(filename, new_tag)
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
                                            open_more_menu()
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
                                    # Check for header collapse tap
                                    if viewer.toggle_collapse_at(tap_x, tap_y):
                                        _draw_overlay()
                                    else:
                                        # Check for link tap
                                        url = viewer.get_link_at(tap_x, tap_y)
                                        if url:
                                            navigate_link(url)
                                    # Split view TOC tap
                                    if split_mode and tap_y < 82:
                                        headers = viewer.get_headers()
                                        if headers:
                                            cur = viewer.get_current_header_idx()
                                            max_show = 5
                                            start = max(0, cur - max_show // 2)
                                            row = (tap_y - 4) // 15
                                            idx = start + row
                                            if 0 <= idx < len(headers):
                                                _, _, li = headers[idx]
                                                viewer.scroll_to_line(li)
                                                _draw_overlay()
                                                _draw_split_toc()
                        drag_last_y = -1
        except KeyboardInterrupt:
            action = 'exit'

        last_file = filename
        last_scroll = viewer.get_scroll_position()
        save_last_file(filename, last_scroll)
        file_prefs.set_scroll_pos(filename, last_scroll)
        file_prefs.set_progress(filename, viewer.get_progress_percent())

        if action == 'exit':
            return


try:
    main()
except KeyboardInterrupt:
    pass
finally:
    clear_screen()
    ppl_guard.cleanup()
