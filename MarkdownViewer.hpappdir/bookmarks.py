"""Multi-bookmark storage for MarkdownViewer.

File format (.bookmarks):
    file:filename.md
    123
    456
    file:other.md
    789

Each 'file:' line starts a section, followed by scroll positions.
"""


def _load_all():
    """Load all bookmarks from .bookmarks file. Returns dict {filename: [positions]}."""
    data = {}
    try:
        with open('.bookmarks', 'r') as f:
            text = f.read().strip()
        if not text:
            return data
        current = None
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('file:'):
                current = line[5:]
                if current not in data:
                    data[current] = []
            elif current and line:
                try:
                    data[current].append(int(line))
                except:
                    pass
    except:
        pass
    return data


def _save_all(data):
    """Save all bookmarks to .bookmarks file."""
    try:
        with open('.bookmarks', 'w') as f:
            for fname in data:
                if data[fname]:
                    f.write('file:' + fname + '\n')
                    for pos in data[fname]:
                        f.write(str(pos) + '\n')
    except:
        pass


def load(filename):
    """Load bookmarks for a specific file. Returns sorted list of positions."""
    data = _load_all()
    positions = data.get(filename, [])
    positions.sort()
    return positions


def add(filename, pos):
    """Add a bookmark at scroll position. Returns updated list."""
    data = _load_all()
    if filename not in data:
        data[filename] = []
    if pos not in data[filename]:
        data[filename].append(pos)
        data[filename].sort()
    _save_all(data)
    return data[filename]


def remove(filename, pos):
    """Remove a bookmark. Returns updated list."""
    data = _load_all()
    if filename in data and pos in data[filename]:
        data[filename].remove(pos)
        if not data[filename]:
            del data[filename]
    _save_all(data)
    return data.get(filename, [])
