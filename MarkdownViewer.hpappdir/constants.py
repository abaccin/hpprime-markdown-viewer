from micropython import const

GR_AFF = const(0)
GR_DRAW = const(1)
GR_LAYERS = const(2)
GR_GUI = const(3)
GR_PAL = const(4)
GR_TMP = const(5)
GR_ZOOM = const(6)
GR_VARIOUS = const(7)
GR_CURS = const(8)
GR_ICO = const(9)

ICO_WIDTH = const(37)
TRANSPARENCY = const(0xA8A8A7)

# Font sizes for TEXTOUT_P
FONT_DEFAULT = const(0)   # Current font size as set by Home Settings
FONT_10 = const(1)        # Size 10 font
FONT_12 = const(2)        # Size 12 font
FONT_14 = const(3)        # Size 14 font
FONT_16 = const(4)        # Size 16 font
FONT_18 = const(5)        # Size 18 font
FONT_20 = const(6)        # Size 20 font
FONT_22 = const(7)        # Size 22 font

# Color constants
COLOR_BLACK = const(0x000000)
COLOR_WHITE = const(0xf8f8f8)
COLOR_RED = const(0xf80000)
COLOR_GRAY = const(0x808080)
COLOR_NORMAL = const(0x000000)
COLOR_HEADER = const(0x000080)
COLOR_CODE = const(0x006400)
COLOR_BOLD = const(0x000000)
COLOR_ITALIC = const(0x404040)
COLOR_BG = const(0xFFFFFF)
COLOR_TABLE_BORDER = const(0xAAAAAA)
COLOR_TABLE_HEADER_BG = const(0xE8E8E8)
COLOR_TABLE_ALT_BG = const(0xF4F4F4)
COLOR_WARNING = const(0xCC6600)

# Table limits
TABLE_MAX_COLS = const(5)
TABLE_CELL_PAD = const(3)
