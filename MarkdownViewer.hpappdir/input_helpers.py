"""Input helper functions for HP Prime touch and keyboard.

Reusable — no app-specific dependencies.
"""

from hpprime import eval
from graphics import get_mouse


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


def get_ticks():
    """Get current tick count in milliseconds."""
    try:
        return int(eval('ticks()'))
    except:
        return 0


def get_menu_tap(tx, ty, menu_y=220, menu_h=20):
    """If (tx, ty) is in a 6-slot menu bar, return slot index 0-5. Else -1."""
    if ty >= menu_y and ty < menu_y + menu_h:
        slot = tx // 53
        if slot > 5:
            slot = 5
        return slot
    return -1
