from micropython import const

GR_AFF = const(0)
GR_TMP = const(5)
TRANSPARENCY = const(0xA8A8A7)

# Font sizes for TEXTOUT_P
FONT_10 = const(1)        # Size 10 font
FONT_12 = const(2)        # Size 12 font
FONT_14 = const(3)        # Size 14 font

# Table limits
TABLE_MAX_COLS = const(5)
TABLE_CELL_PAD = const(3)

# Scrollbar
SCROLLBAR_WIDTH = const(4)
SCROLLBAR_MIN_THUMB = const(15)

# Blockquote
BLOCKQUOTE_INDENT = const(15)
BLOCKQUOTE_BAR_WIDTH = const(3)

# Nested lists
NESTED_LIST_INDENT = const(15)

# Menu bar
MENU_Y = const(220)
MENU_HEIGHT = const(20)
VIEWER_HEIGHT = const(212)
VIEWER_HEIGHT_FULL = const(232)

# Notch (bottom-right menu trigger)
NOTCH_X = const(282)
NOTCH_Y = const(227)
NOTCH_W = const(38)
NOTCH_H = const(13)
GR_MENU_SAVE = const(7)

# Touch/drag scrolling
DRAG_THRESHOLD = const(3)

# Long press (milliseconds)
LONG_PRESS_MS = const(600)
