"""Guard for PPL eval calls — ensures dot decimal separator mode.

HP Prime's Home Settings include a Digit Grouping / Decimal Mark option
(HSeparator) that controls whether dot or comma is used as the decimal
separator and whether commas or semicolons separate function arguments.

When comma-decimal mode is active, PPL function calls that use commas
as argument separators (e.g. TEXTSIZE("hi",2)) or dots in decimal
numbers (e.g. wait(0.05)) will silently fail or produce wrong results.

This module saves system settings at startup and forces safe defaults.
Settings are restored on exit via cleanup().

Inspired by Dynatris AppContext pattern:
- Save/restore HSeparator (decimal mode)
- Save/restore TDim (display auto-dim timeout)
- Flush keyboard buffer on exit
- Free temporary GROBs on exit

Usage — call once at startup, restore once at exit:
    import ppl_guard
    ppl_guard.init()      # force safe settings
    ...                   # all PPL eval calls are now safe
    ppl_guard.cleanup()   # restore original settings on exit

Reference: https://www.hpmuseum.org/forum/thread-23501.html
"""

from hpprime import eval as heval, dimgrob

_saved_separator = None
_saved_tdim = None


def init():
    """Save system settings and force safe defaults.

    Call this ONCE at app startup, before any PPL eval calls
    that use decimal numbers or multi-argument PPL functions.
    """
    global _saved_separator, _saved_tdim
    try:
        _saved_separator = int(heval('HSeparator'))
    except:
        _saved_separator = 0
    # Save display dim timeout
    try:
        _saved_tdim = int(heval('TDim'))
    except:
        _saved_tdim = None
    # Force dot decimal separator (option 0 = 123,456.789)
    # HSeparator:=0 uses only integers, so it works safely
    # regardless of the current decimal separator setting.
    try:
        heval('HSeparator:=0')
    except:
        pass
    # Extend display dim timeout to prevent auto-dim during reading
    try:
        heval('TDim:=9E4')
    except:
        pass


def cleanup():
    """Restore original system settings.

    Call this on app exit to leave the calculator in its
    original state.
    """
    global _saved_separator, _saved_tdim
    # Free temporary GROBs (G1-G9) to release memory
    for g in range(1, 10):
        try:
            dimgrob(g, 0, 0, 0)
        except:
            pass
    # Flush keyboard buffer
    try:
        heval('ISKEYDOWN(-1)')
    except:
        pass
    # Restore display dim timeout
    if _saved_tdim is not None:
        try:
            heval('TDim:=%d' % _saved_tdim)
        except:
            pass
    # Reset auto-off timer
    try:
        heval('TOff:=TOff')
    except:
        pass
    # Restore decimal separator
    if _saved_separator is not None:
        try:
            heval('HSeparator:=%d' % _saved_separator)
        except:
            pass
