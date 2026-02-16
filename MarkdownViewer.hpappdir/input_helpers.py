"""Input helper functions for HP Prime touch and keyboard.

Reusable — no app-specific dependencies.
"""

from hpprime import eval as heval


def get_key():
    """Read the current key code, or 0 if none pressed."""
    heval('wait(0.05)')
    k = heval('GETKEY()')
    return k if k > 0 else 0


def get_touch_y():
    """Get the Y coordinate of the current touch, or -1 if not touching."""
    m = heval("mouse")
    if m:
        f = m[0]
        if type(f) is list:
            if len(f) >= 2 and f[0] >= 0:
                return int(f[1])
        elif type(f) in (int, float) and len(m) >= 2 and m[0] >= 0:
            return int(m[1])
    return -1


def get_touch():
    """Get (x, y) of the current touch, or (-1, -1) if not touching."""
    m = heval("mouse")
    if m:
        f = m[0]
        if type(f) is list:
            if len(f) >= 2 and f[0] >= 0:
                return (int(f[0]), int(f[1]))
        elif type(f) in (int, float) and len(m) >= 2 and m[0] >= 0:
            return (int(m[0]), int(m[1]))
    return (-1, -1)


def get_ticks():
    """Get current tick count in milliseconds."""
    return int(heval('ticks()'))


def get_menu_tap(tx, ty, menu_y=220, menu_h=20):
    """If (tx, ty) is in a 6-slot menu bar, return slot index 0-5. Else -1."""
    if ty >= menu_y and ty < menu_y + menu_h:
        slot = tx // 53
        if slot > 5:
            slot = 5
        return slot
    return -1
