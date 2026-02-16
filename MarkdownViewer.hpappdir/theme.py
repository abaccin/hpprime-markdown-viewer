"""Theme support for MarkdownViewer - light and dark color palettes."""

LIGHT = {
    'bg': 0xFFFFFF,
    'normal': 0x000000,
    'header': 0x000080,
    'code': 0x006400,
    'bold': 0x000000,
    'italic': 0x404040,
    'link': 0x0000CC,
    'code_bg': 0xE8E8E8,
    'table_border': 0xAAAAAA,
    'table_header_bg': 0xE8E8E8,
    'table_alt_bg': 0xF4F4F4,
    'warning': 0xCC6600,
    'blockquote_bar': 0x808080,
    'blockquote_bg': 0xF0F0F0,
    'scrollbar': 0xDDDDDD,
    'scrollbar_thumb': 0x888888,
    'search_hl': 0xFFFF00,
    'task_done': 0x008000,
    'strikethrough': 0x808080,
    'browser_bg': 0xF8F8F8,
    'browser_sel': 0x000080,
    'browser_text': 0x000000,
    'browser_sel_text': 0xF8F8F8,
    'browser_subtitle': 0x000080,
    'browser_border': 0x000080,
    'browser_hint': 0x808080,
    'browser_error': 0xF80000,
    'menu_bg': 0x000080,
    'menu_text': 0xFFFFFF,
    'menu_divider': 0x4040A0,
    'bookmark_mark': 0xF80000,
    'ctx_bg': 0xF0F0F0,
    'ctx_border': 0x808080,
    'ctx_text': 0x000000,
    'ctx_sel': 0x000080,
    'ctx_sel_text': 0xFFFFFF,
    'fav_star': 0xCCA000,
    'progress_bar': 0x4040C0,
}

DARK = {
    'bg': 0x1E1E1E,
    'normal': 0xD4D4D4,
    'header': 0x569CD6,
    'code': 0x6A9955,
    'bold': 0xD4D4D4,
    'italic': 0x9CDCFE,
    'link': 0x4EC9B0,
    'code_bg': 0x2D2D2D,
    'table_border': 0x404040,
    'table_header_bg': 0x333333,
    'table_alt_bg': 0x252525,
    'warning': 0xCE9178,
    'blockquote_bar': 0x569CD6,
    'blockquote_bg': 0x252525,
    'scrollbar': 0x333333,
    'scrollbar_thumb': 0x666666,
    'search_hl': 0x613214,
    'task_done': 0x6A9955,
    'strikethrough': 0x808080,
    'browser_bg': 0x1E1E1E,
    'browser_sel': 0x264F78,
    'browser_text': 0xD4D4D4,
    'browser_sel_text': 0xFFFFFF,
    'browser_subtitle': 0x569CD6,
    'browser_border': 0x404040,
    'browser_hint': 0x808080,
    'browser_error': 0xF44747,
    'menu_bg': 0x333333,
    'menu_text': 0xD4D4D4,
    'menu_divider': 0x555555,
    'bookmark_mark': 0xF80000,
    'ctx_bg': 0x2D2D2D,
    'ctx_border': 0x555555,
    'ctx_text': 0xD4D4D4,
    'ctx_sel': 0x264F78,
    'ctx_sel_text': 0xFFFFFF,
    'fav_star': 0xFFD700,
    'progress_bar': 0x569CD6,
}

# Current active theme colors (mutable dict)
colors = dict(LIGHT)
_is_dark = False


def toggle():
    """Toggle between light and dark themes."""
    global _is_dark
    _is_dark = not _is_dark
    if _is_dark:
        colors.update(DARK)
    else:
        colors.update(LIGHT)


def is_dark():
    """Return True if dark theme is active."""
    return _is_dark
