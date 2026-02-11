from constants import (GR_AFF, FONT_10, FONT_12, FONT_14,
    COLOR_BLACK, COLOR_WHITE, COLOR_HEADER, COLOR_RED, COLOR_GRAY)
from hpprime import eval, fillrect, keyboard
from graphics import draw_text, draw_rectangle, text_width
from keycodes import KEY_UP, KEY_DOWN, KEY_ENTER, KEY_ON
from file_ops import list_files
from markdown_viewer import MarkdownViewer


def get_key():
    """Read the current key code, or 0 if none pressed."""
    if keyboard():
        return eval('GETKEY()')
    return 0


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

    draw_text(GR_AFF, 10, 225, "Up/Down:Select  Enter:Open  ON:Exit", FONT_10, COLOR_GRAY)


def file_browser():
    """Show file browser and return selected filename."""
    md_files = get_md_files()
    selected = 0

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
    except KeyboardInterrupt:
        pass

    clear_screen()


try:
    main()
except KeyboardInterrupt:
    clear_screen()