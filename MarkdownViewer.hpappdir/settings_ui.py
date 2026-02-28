"""Settings dialog — lazy-loaded to reduce startup memory on G1."""

from constants import GR_AFF, FONT_10, FONT_14
from graphics import draw_text, draw_rectangle, text_width
from hpprime import fillrect
from keycodes import KEY_ENTER, KEY_ESC
from input_helpers import get_key, get_touch, mouse_clear
import theme


def show_settings_dialog(menu_y=220, colors=None):
    """Show a settings/info dialog with version, build, and platform.

    Blocks until the user presses ESC / Enter or taps outside.

    Returns False (no settings changed yet — placeholder for future toggles).
    """
    from constants import APP_VERSION, BUILD_NUMBER
    import gc

    c = colors if colors is not None else theme.colors
    dw = 240
    dh = 120
    dx = (320 - dw) // 2
    dy = (menu_y - dh) // 2
    if dy < 5:
        dy = 5

    # Border + background
    draw_rectangle(GR_AFF, dx - 1, dy - 1, dx + dw + 1, dy + dh + 1,
                   c['ctx_border'], 255, c['ctx_border'], 255)
    draw_rectangle(GR_AFF, dx, dy, dx + dw, dy + dh,
                   c['ctx_bg'], 255, c['ctx_bg'], 255)

    # Title
    title = "Settings"
    tw = text_width(title, FONT_14)
    draw_text(GR_AFF, dx + (dw - tw) // 2, dy + 6, title, FONT_14,
              c.get('header', c['ctx_text']))

    # Separator
    draw_rectangle(GR_AFF, dx + 10, dy + 26, dx + dw - 10, dy + 27,
                   c['ctx_border'], 255, c['ctx_border'], 255)

    # Info rows
    col1 = dx + 15
    col2 = dx + 110
    row_y = dy + 34
    rh = 18

    draw_text(GR_AFF, col1, row_y, "Version:", FONT_10, c['ctx_text'])
    draw_text(GR_AFF, col2, row_y, APP_VERSION, FONT_10, c['ctx_text'])
    row_y += rh

    draw_text(GR_AFF, col1, row_y, "Build:", FONT_10, c['ctx_text'])
    draw_text(GR_AFF, col2, row_y, str(BUILD_NUMBER), FONT_10, c['ctx_text'])
    row_y += rh

    try:
        import sys
        plat = sys.platform
    except:
        plat = "unknown"
    draw_text(GR_AFF, col1, row_y, "Platform:", FONT_10, c['ctx_text'])
    draw_text(GR_AFF, col2, row_y, str(plat), FONT_10, c['ctx_text'])
    row_y += rh

    mem_label = str(gc.mem_free()) + " bytes free"
    draw_text(GR_AFF, col1, row_y, "Memory:", FONT_10, c['ctx_text'])
    draw_text(GR_AFF, col2, row_y, mem_label, FONT_10, c['ctx_text'])

    # Hint
    hint = "ESC or Enter to close"
    hw = text_width(hint, FONT_10)
    draw_text(GR_AFF, dx + (dw - hw) // 2, dy + dh - 14, hint, FONT_10,
              c.get('browser_hint', c['ctx_border']))

    mouse_clear()
    touch_down = False
    while True:
        k = get_key()
        if k == KEY_ESC or k == KEY_ENTER:
            return False
        tx, ty = get_touch()
        if tx >= 0 and ty >= 0:
            touch_down = True
        elif touch_down:
            return False
