"""File preferences: favorites, recent files, and sort mode.

Manages pinned/favorite files, recently opened file history,
and sort direction state for the file browser.

Persistence:
    .favorites  — one pinned filename per line
    .recent     — one recent filename per line (most recent first)
"""

MAX_RECENT = 10

_favorites = None
_sort_col = 'fav'
_sort_asc = True
_recent = None


def _load_favorites_file():
    try:
        with open('.favorites', 'r') as f:
            text = f.read().strip()
        if not text:
            return []
        return [l.strip() for l in text.split('\n') if l.strip()]
    except:
        return []


def _save_favorites_file(favs):
    try:
        with open('.favorites', 'w') as f:
            for name in favs:
                f.write(name + '\n')
    except:
        pass


def get_favorites():
    """Get the list of favorite/pinned filenames."""
    global _favorites
    if _favorites is None:
        _favorites = _load_favorites_file()
    return _favorites


def toggle_favorite(filename):
    """Toggle pin status. Returns (updated_list, is_now_pinned)."""
    global _favorites
    favs = list(get_favorites())
    if filename in favs:
        favs.remove(filename)
        is_pinned = False
    else:
        favs.append(filename)
        is_pinned = True
    _favorites = favs
    _save_favorites_file(favs)
    return favs, is_pinned


def get_sort():
    """Return (column, ascending). Column is 'name', 'size', or 'fav'."""
    return _sort_col, _sort_asc


def cycle_sort(col):
    """Cycle sort on the given column. Returns (column, ascending).

    If already sorting by this column, toggles direction.
    Otherwise switches to this column ascending.
    """
    global _sort_col, _sort_asc
    if _sort_col == col:
        _sort_asc = not _sort_asc
    else:
        _sort_col = col
        _sort_asc = True
    return _sort_col, _sort_asc


def _load_recent_file():
    try:
        with open('.recent', 'r') as f:
            text = f.read().strip()
        if not text:
            return []
        items = [l.strip() for l in text.split('\n') if l.strip()]
        return items[:MAX_RECENT]
    except:
        return []


def _save_recent_file(recent):
    try:
        with open('.recent', 'w') as f:
            for name in recent[:MAX_RECENT]:
                f.write(name + '\n')
    except:
        pass


def get_recent():
    """Get the list of recently opened filenames (most recent first)."""
    global _recent
    if _recent is None:
        _recent = _load_recent_file()
    return _recent


def add_recent(filename):
    """Add a file to the recent list. Returns updated list."""
    global _recent
    recent = list(get_recent())
    if filename in recent:
        recent.remove(filename)
    recent.insert(0, filename)
    recent = recent[:MAX_RECENT]
    _recent = recent
    _save_recent_file(recent)
    return recent
