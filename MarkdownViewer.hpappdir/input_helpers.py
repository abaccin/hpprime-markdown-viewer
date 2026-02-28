"""Input helper functions for HP Prime touch and keyboard.

Dynatris-style: keyboard() bitmask with edge detection and DAS key repeat.
Uses hpprime.keyboard() instead of eval('GETKEY()') for key detection.
Uses eval('wait') for idle throttling (power-efficient for a reader app).
"""

from hpprime import eval as heval, ticks as _ticks, keyboard as _keyboard
from cas import get_key as _cas_get_key

# --- Keyboard state (Dynatris / TinyTurtle pattern) ---
_prev_kb = 0
_repeat_key = -1       # bit index of key currently auto-repeating
_repeat_ticks = 0      # ticks when the key was first held
_DAS_DELAY = 350       # ms before first repeat fires
_DAS_RATE = 70         # ms between successive repeats

# Key bit indices that auto-repeat when held (scroll keys for reader):
# Up=2, Down=12, Plus=50, Minus=45
_REPEAT_KEYS = {2, 12, 50, 45}


def _lowest_bit(mask):
    """Return bit index of the lowest set bit, or -1."""
    i = 0
    while mask:
        if mask & 1:
            return i
        mask >>= 1
        i += 1
    return -1


def get_key():
    """Read key using keyboard() bitmask — edge detect + DAS repeat.

    Returns GETKEY-compatible keycode (bit position) or 0 if no key.
    Throttled with eval('wait(1/20)') to save power during idle.
    """
    global _prev_kb, _repeat_key, _repeat_ticks

    heval('wait(1/20)')

    kb = _keyboard()
    new_pressed = kb & ~_prev_kb  # rising edges only
    _prev_kb = kb

    # Drain GETKEY buffer so stale keys don't pile up (TML/TinyTurtle pattern)
    if new_pressed:
        _cas_get_key()

    now = _ticks()

    # New key press — return it and start DAS timer
    if new_pressed:
        bit = _lowest_bit(new_pressed)
        # Track repeat for scroll keys
        if bit in _REPEAT_KEYS:
            _repeat_key = bit
            _repeat_ticks = now
        else:
            _repeat_key = -1
        return bit

    # No new press — check DAS auto-repeat for held scroll keys
    if _repeat_key >= 0 and kb & (1 << _repeat_key):
        elapsed = now - _repeat_ticks
        if elapsed >= _DAS_DELAY:
            # Fire a repeat and reset timer for rate interval
            _repeat_ticks = now - (_DAS_DELAY - _DAS_RATE)
            return _repeat_key
    else:
        _repeat_key = -1

    return 0


def get_key_fast():
    """Read key with shorter wait — for active scrolling/drag."""
    global _prev_kb, _repeat_key, _repeat_ticks

    heval('wait(1/50)')

    kb = _keyboard()
    new_pressed = kb & ~_prev_kb
    _prev_kb = kb

    if new_pressed:
        _cas_get_key()

    now = _ticks()

    if new_pressed:
        bit = _lowest_bit(new_pressed)
        if bit in _REPEAT_KEYS:
            _repeat_key = bit
            _repeat_ticks = now
        else:
            _repeat_key = -1
        return bit

    if _repeat_key >= 0 and kb & (1 << _repeat_key):
        elapsed = now - _repeat_ticks
        if elapsed >= _DAS_DELAY:
            _repeat_ticks = now - (_DAS_DELAY - _DAS_RATE)
            return _repeat_key
    else:
        _repeat_key = -1

    return 0


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


def mouse_clear():
    """Drain all pending touch events to prevent ghost taps / bounce."""
    while heval('mouse(1)') >= 0:
        pass


def get_ticks():
    """Get current tick count in milliseconds."""
    return _ticks()


def get_menu_tap(tx, ty, menu_y=220, menu_h=20):
    """If (tx, ty) is in a 6-slot menu bar, return slot index 0-5. Else -1."""
    if ty >= menu_y and ty < menu_y + menu_h:
        slot = tx // 53
        if slot > 5:
            slot = 5
        return slot
    return -1
