from graphics import (draw_text, draw_rectangle, text_width, draw_image,
    open_file, blit, get_grob_size, get_formula_size, render_formula)
from constants import (FONT_10, FONT_12, FONT_14,
    TABLE_MAX_COLS, TABLE_CELL_PAD, GR_TMP, TRANSPARENCY,
    SCROLLBAR_WIDTH, SCROLLBAR_MIN_THUMB, BLOCKQUOTE_INDENT,
    BLOCKQUOTE_BAR_WIDTH, NESTED_LIST_INDENT)
import theme


class MarkdownViewer:
    """A simple markdown viewer for HP Prime."""

    def __init__(self, gr, height=230):
        self.gr = gr
        self.height = height
        self.document = MarkdownDocument()

    def load_markdown_file(self, filename):
        """Load markdown content from a file."""
        return self.document.load_file(filename)

    def render(self):
        """Render the loaded markdown document."""
        self.document.render(self.gr, height=self.height)

    def scroll_up(self):
        self.document.scroll_up()

    def scroll_down(self):
        self.document.scroll_down()

    def scroll_by(self, delta):
        self.document.scroll_by(delta)

    def scroll_page_up(self):
        self.document.scroll_page_up()

    def scroll_page_down(self):
        self.document.scroll_page_down()

    def scroll_to_top(self):
        self.document.scroll_to_top()

    def scroll_to_bottom(self):
        self.document.scroll_to_bottom()

    def toggle_theme(self):
        """Toggle light/dark theme and re-render."""
        theme.toggle()
        if self.document.renderer:
            self.document.renderer._content_height = 0
        self.document.render(self.gr)

    def search(self, term, case_sensitive=False):
        """Search for term in the document."""
        if not self.document.renderer:
            return False
        r = self.document.renderer
        r._search_case = case_sensitive
        r._search_term = term if case_sensitive else (term.lower() if term else None)
        r._search_positions = []
        r._search_match_idx = 0
        if not term:
            self.document.render(self.gr)
            return False
        # Full render pass to collect match positions
        saved_height = r._content_height
        r._content_height = 0
        self.document.render(self.gr)
        r._content_height = saved_height if saved_height > 0 else r._content_height
        if r._search_positions:
            target = r._search_positions[0] - r.y
            r.scroll_offset = max(0, target)
            m = r._max_scroll()
            if r.scroll_offset > m:
                r.scroll_offset = m
            self.document.render(self.gr)
            return True
        return False

    def search_next(self):
        """Jump to next search match."""
        if not self.document.renderer:
            return
        r = self.document.renderer
        if not r._search_positions:
            return
        r._search_match_idx = (r._search_match_idx + 1) % len(r._search_positions)
        target = r._search_positions[r._search_match_idx] - r.y
        r.scroll_offset = max(0, target)
        m = r._max_scroll()
        if r.scroll_offset > m:
            r.scroll_offset = m
        self.document.render(self.gr)

    def get_search_info(self):
        """Return (current_match_1based, total_matches) or None."""
        if not self.document.renderer:
            return None
        r = self.document.renderer
        if not r._search_term or not r._search_positions:
            return None
        return (r._search_match_idx + 1, len(r._search_positions))

    def clear_search(self):
        """Clear search highlighting."""
        if self.document.renderer:
            self.document.renderer._search_term = None
            self.document.renderer._search_positions = []
            self.document.render(self.gr)

    def get_scroll_position(self):
        """Get current scroll offset for bookmarking."""
        if self.document.renderer:
            return self.document.renderer.scroll_offset
        return 0

    def set_scroll_position(self, pos):
        """Restore a saved scroll offset."""
        if self.document.renderer:
            self.document.renderer.scroll_offset = pos

    def is_scrollbar_tap(self, x, y):
        """Check if a tap at (x,y) is on the scrollbar.
        
        Returns True if the tap is within the scrollbar track area.
        """
        if not self.document.renderer:
            return False
        r = self.document.renderer
        if r._content_height <= r.height:
            return False
        bar_x = r.x + r.width - SCROLLBAR_WIDTH
        bar_y = r.y
        bar_h = r.height
        return x >= bar_x and x <= bar_x + SCROLLBAR_WIDTH and y >= bar_y and y < bar_y + bar_h

    def scroll_to_ratio(self, ratio):
        """Scroll to a position based on a 0.0-1.0 ratio of the document.
        
        Args:
            ratio: 0.0 = top, 1.0 = bottom
        """
        if not self.document.renderer:
            return
        r = self.document.renderer
        max_scroll = r._max_scroll()
        if max_scroll <= 0:
            return
        target_offset = int(max_scroll * max(0.0, min(1.0, ratio)))
        r.scroll_offset = target_offset

    def scrollbar_y_to_ratio(self, y):
        """Convert a Y coordinate in the scrollbar to a scroll ratio.
        
        Args:
            y: Y coordinate of tap/drag
            
        Returns:
            Float 0.0-1.0 representing position in document
        """
        if not self.document.renderer:
            return 0.0
        r = self.document.renderer
        bar_y = r.y
        bar_h = r.height
        if bar_h <= 0:
            return 0.0
        # Clamp to scrollbar bounds
        local_y = max(0, min(bar_h, y - bar_y))
        return local_y / bar_h

    def set_bookmarks(self, positions):
        """Set bookmark positions for scrollbar display."""
        if self.document.renderer:
            self.document.renderer._bookmarks = positions

    def get_content_height(self):
        """Get total content height (for bookmark position context)."""
        if self.document.renderer:
            return self.document.renderer._content_height
        return 0

    def get_headers(self):
        """Extract table of contents from the document.

        Returns list of (level, title, line_index) tuples.
        """
        if not self.document.content:
            return []
        headers = []
        for i, line in enumerate(self.document.content.split('\n')):
            stripped = line.strip()
            if stripped.startswith('#'):
                level = 0
                while level < len(stripped) and stripped[level] == '#':
                    level += 1
                if level > 6:
                    level = 6
                title = stripped[level:].strip()
                if title:
                    headers.append((level, title, i))
        return headers

    def scroll_to_line(self, line_index):
        """Scroll so that the given source line index is visible.

        Uses the cached per-line Y offsets for exact positioning.
        Falls back to a measurement pass if the cache is not yet built.
        """
        if not self.document.renderer or not self.document.content:
            return
        r = self.document.renderer

        # Use cached offsets if available
        if r._line_y_cache and line_index < len(r._line_y_cache):
            r.scroll_offset = max(0, r._line_y_cache[line_index])
            m = r._max_scroll()
            if r.scroll_offset > m:
                r.scroll_offset = m
            self.document.render(self.gr, height=self.height)
            return

        # Cache not built yet — trigger a measurement pass
        saved_scroll = r.scroll_offset
        r.scroll_offset = 0
        r._content_height = 0
        self.document.render(self.gr, height=self.height)

        # Now use the freshly built cache
        if r._line_y_cache and line_index < len(r._line_y_cache):
            r.scroll_offset = max(0, r._line_y_cache[line_index])
        else:
            r.scroll_offset = saved_scroll
        m = r._max_scroll()
        if r.scroll_offset > m:
            r.scroll_offset = m
        self.document.render(self.gr, height=self.height)

    def get_link_at(self, tx, ty):
        """Return the URL of a link at screen coordinates, or None."""
        if not self.document.renderer:
            return None
        for x1, y1, x2, y2, url in self.document.renderer._link_zones:
            if x1 <= tx <= x2 and y1 <= ty <= y2:
                return url
        return None

    def get_progress_percent(self):
        """Return scroll progress as 0–100 integer."""
        if not self.document.renderer:
            return 0
        r = self.document.renderer
        m = r._max_scroll()
        if m <= 0:
            return 100
        return min(100, int(r.scroll_offset * 100 / m))

    def get_document_stats(self):
        """Return (line_count, word_count, read_time_min) for the document."""
        content = self.document.content
        if not content:
            return (0, 0, 0)
        lines = content.split('\n')
        line_count = len(lines)
        word_count = 0
        for line in lines:
            words = line.split()
            word_count += len(words)
        # Average reading speed: ~200 words/min
        read_min = (word_count + 199) // 200
        if read_min < 1 and word_count > 0:
            read_min = 1
        return (line_count, word_count, read_min)


class MarkdownRenderer:
    """Lightweight markdown renderer for HP Prime display (320x240)."""

    # Base64 lookup table (class-level constant, built once)
    _B64 = {}
    _b64c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    for _i in range(64):
        _B64[_b64c[_i]] = _i
    del _b64c, _i

    def __init__(self, gr, x=5, y=5, width=310, height=230):
        self.gr = gr
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.current_y = y
        self.line_height = 12
        self.scroll_offset = 0
        self._table_buffer = []
        self._in_code_fence = False
        self._code_lang = ''
        self._content_height = 0
        self._blockquote_depth = 0
        self._search_term = None
        self._search_case = False
        self._search_positions = []
        self._search_match_idx = 0
        self._bookmarks = []
        self._link_zones = []  # [(x1, y1, x2, y2, url)] for tap detection
        self._line_y_cache = []     # abs Y offset per source line
        self._line_fence_cache = [] # code-fence state per source line
        self._in_math_fence = False
        self._math_buffer = []
        self._formula_cache = {}    # expr -> (width, height)

    def _in_view(self, y, h=12):
        """Check if a line at y with height h is within the visible area."""
        return y >= self.y and y + h <= self.y + self.height

    def _find_first_visible(self):
        """Binary search for the first source line that could be visible.

        Returns the index into _line_y_cache of the first line whose
        absolute Y is within a margin above the current scroll offset.
        """
        target = self.scroll_offset - 50
        if target <= 0:
            return 0
        cache = self._line_y_cache
        lo = 0
        hi = len(cache) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cache[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def clear(self):
        """Clear the rendering area."""
        bg = theme.colors['bg']
        draw_rectangle(self.gr, self.x, self.y,
                  self.x + self.width, self.y + self.height,
                  bg, 255, bg, 255)
        self.current_y = self.y

    def render(self, markdown_text):
        """Render markdown text to the graphics buffer.

        First render (content_height==0) does a full measurement pass,
        building a per-line Y-offset cache.  Subsequent renders use
        the cache to skip lines above the viewport (partial render).
        """
        self.clear()
        self.current_y = self.y - self.scroll_offset
        self._table_buffer = []
        self._in_code_fence = False
        self._in_math_fence = False
        self._math_buffer = []
        self._blockquote_depth = 0
        self._link_zones = []

        lines = markdown_text.split('\n')
        n = len(lines)
        is_measuring = self._content_height == 0

        # Only rebuild search positions during measurement pass
        if self._search_term and is_measuring:
            self._search_positions = []

        if is_measuring:
            # --- Full measurement pass: build cache ---
            cache_y = []
            cache_f = []
            for line in lines:
                cache_y.append(
                    self.current_y + self.scroll_offset - self.y)
                # Fence state: 0=none, 1=code, 2=math
                if self._in_math_fence:
                    cache_f.append(2)
                elif self._in_code_fence:
                    cache_f.append(1)
                else:
                    cache_f.append(0)
                self._render_line(line)
            if self._table_buffer:
                self._flush_table()
            self._content_height = (
                self.current_y + self.scroll_offset - self.y)
            self._line_y_cache = cache_y
            self._line_fence_cache = cache_f
        elif self._line_y_cache and len(self._line_y_cache) == n:
            # --- Cached partial render: skip above viewport ---
            start_idx = self._find_first_visible()
            # Back up into any table block that straddles the edge
            while (start_idx > 0
                    and lines[start_idx - 1].strip().startswith('|')):
                start_idx -= 1
            # Back up into any math fence block that straddles the edge
            if (start_idx < n
                    and self._line_fence_cache[start_idx] == 2):
                while (start_idx > 0
                        and self._line_fence_cache[start_idx] == 2):
                    start_idx -= 1
            # Restore rendering state from cache
            if start_idx > 0:
                state = self._line_fence_cache[start_idx]
                self._in_code_fence = (state == 1)
                self._in_math_fence = (state == 2)
                self.current_y = (
                    self.y + self._line_y_cache[start_idx]
                    - self.scroll_offset)
            for i in range(start_idx, n):
                if self.current_y > self.y + self.height:
                    break
                self._render_line(lines[i])
            if self._table_buffer:
                self._flush_table()
        else:
            # --- Fallback: no cache, content_height known ---
            for line in lines:
                if self.current_y > self.y + self.height:
                    break
                self._render_line(line)
            if self._table_buffer:
                self._flush_table()

        self._draw_scrollbar()

    def _render_line(self, line):
        """Render a single line of markdown."""
        line = line.rstrip()

        # Handle code/math fences
        if line.strip().startswith('```'):
            if self._in_math_fence:
                self._in_math_fence = False
                self._flush_math()
                return
            elif self._in_code_fence:
                self._in_code_fence = False
                return
            else:
                tag = line.strip()[3:].strip().lower()
                if tag in ('math', 'formula', 'cas'):
                    self._in_math_fence = True
                    self._math_buffer = []
                    return
                else:
                    self._in_code_fence = True
                    self._code_lang = tag
                    return

        if self._in_math_fence:
            self._math_buffer.append(line)
            return

        if self._in_code_fence:
            self._render_code_line(line)
            return

        # Check if we're collecting table rows
        if self._table_buffer:
            if line.startswith('|'):
                self._buffer_table_line(line)
                return
            else:
                self._flush_table()

        stripped = line.strip()

        if not stripped:
            self.current_y += self.line_height // 2
            return

        if line.startswith('|'):
            self._buffer_table_line(line)
        elif stripped.startswith('!['):
            self._render_image(stripped)
        elif line.startswith('#'):
            self._render_header(line)
        elif stripped == '---' or stripped == '***' or stripped == '___':
            self._render_hr()
        elif stripped.startswith('>'):
            self._render_blockquote(stripped)
        else:
            # Detect indentation for nested lists
            indent = 0
            temp = line
            while temp.startswith(' '):
                indent += 1
                temp = temp[1:]
            level = indent // 2
            sl = temp

            # Task list
            if (sl.startswith('- [ ] ') or
                    sl.startswith('- [x] ') or
                    sl.startswith('- [X] ')):
                checked = sl[3] in ('x', 'X')
                self._render_task_list_item(sl[6:], checked, level)
            # Unordered list
            elif sl.startswith('- ') or sl.startswith('* '):
                self._render_list_item(sl[2:], indent_level=level)
            # Ordered list
            elif self._is_ordered_list(sl):
                dot = sl.index('.')
                num = sl[:dot]
                text = sl[dot + 1:].lstrip()
                if text:
                    self._render_list_item(text, bullet=num + '.', indent_level=level)
            else:
                self._render_paragraph(line)

    # Keywords per language for syntax highlighting
    _KW = {
        'python': {'False','None','True','and','as','assert','async',
            'await','break','class','continue','def','del','elif',
            'else','except','finally','for','from','global','if',
            'import','in','is','lambda','not','or','pass','raise',
            'return','try','while','with','yield'},
        'c': {'auto','break','case','char','const','continue',
            'default','do','double','else','enum','extern','float',
            'for','goto','if','int','long','register','return',
            'short','signed','sizeof','static','struct','switch',
            'typedef','union','unsigned','void','volatile','while',
            'include','define','ifdef','ifndef','endif','pragma'},
        'ppl': {'BEGIN','END','IF','THEN','ELSE','FOR','FROM','TO',
            'STEP','DO','WHILE','REPEAT','UNTIL','RETURN','LOCAL',
            'EXPORT','CASE','DEFAULT','IFERR','KILL','PRINT',
            'FREEZE','MSGBOX','INPUT','CHOOSE','TEXTOUT_P',
            'RECT_P','LINE_P','ARC_P','BLIT_P','DRAWMENU',
            'GROBW_P','GROBH_P','DIMGROB_P','RGB','GETKEY',
            'MOUSE','WAIT','SIZE','DIM','MAKELIST','CONCAT'},
    }
    _KW['cpp'] = _KW['c']
    _KW['h'] = _KW['c']
    _KW['py'] = _KW['python']

    _BUILTINS = {
        'python': {'abs','all','any','bin','bool','bytes','chr',
            'dict','dir','enumerate','eval','filter','float',
            'format','getattr','hasattr','hex','id','input','int',
            'isinstance','iter','len','list','map','max','min',
            'next','object','oct','open','ord','pow','print',
            'range','repr','reversed','round','set','setattr',
            'slice','sorted','str','sum','super','tuple','type',
            'vars','zip','self'},
    }
    _BUILTINS['py'] = _BUILTINS['python']

    def _tokenize_code(self, line, lang):
        """Tokenize a code line into (text, color_key) segments."""
        c = theme.colors
        code_c = c['code']
        kw_c = c.get('syn_keyword', code_c)
        str_c = c.get('syn_string', code_c)
        cmt_c = c.get('syn_comment', code_c)
        num_c = c.get('syn_number', code_c)
        bi_c = c.get('syn_builtin', code_c)
        dec_c = c.get('syn_decorator', code_c)
        kw_set = self._KW.get(lang)
        bi_set = self._BUILTINS.get(lang)
        tokens = []
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            # Comments: # (python/ppl) or // (c/cpp)
            if ch == '#' and lang in ('python', 'py', 'ppl'):
                # But skip #include, #define etc in PPL context
                if lang == 'ppl' or (i == 0 or line[i-1] == ' '):
                    tokens.append((line[i:], cmt_c))
                    break
            if ch == '/' and i + 1 < n and line[i+1] == '/' and lang in ('c', 'cpp', 'h', 'ppl'):
                tokens.append((line[i:], cmt_c))
                break
            # Strings
            if ch in ('"', "'"):
                q = ch
                j = i + 1
                while j < n:
                    if line[j] == '\\':
                        j += 2
                        continue
                    if line[j] == q:
                        j += 1
                        break
                    j += 1
                tokens.append((line[i:j], str_c))
                i = j
                continue
            # Decorator
            if ch == '@' and lang in ('python', 'py') and (i == 0 or line[i-1] == ' '):
                j = i + 1
                while j < n and (line[j].isalpha() or line[j] == '_' or line[j] == '.'):
                    j += 1
                tokens.append((line[i:j], dec_c))
                i = j
                continue
            # Numbers
            if ch.isdigit() or (ch == '.' and i + 1 < n and line[i+1].isdigit()):
                j = i + 1
                while j < n and (line[j].isdigit() or line[j] in '.xXabcdefABCDEF_'):
                    j += 1
                tokens.append((line[i:j], num_c))
                i = j
                continue
            # Identifiers / keywords
            if ch.isalpha() or ch == '_':
                j = i + 1
                while j < n and (line[j].isalpha() or line[j].isdigit() or line[j] == '_'):
                    j += 1
                word = line[i:j]
                if kw_set and word in kw_set:
                    tokens.append((word, kw_c))
                elif bi_set and word in bi_set:
                    tokens.append((word, bi_c))
                else:
                    tokens.append((word, code_c))
                i = j
                continue
            # Other characters (operators, whitespace, etc.)
            j = i + 1
            while j < n and not (line[j].isalpha() or line[j] == '_' or
                    line[j].isdigit() or line[j] in '#@"\'/' or
                    (line[j] == '.' and j + 1 < n and line[j+1].isdigit())):
                j += 1
            tokens.append((line[i:j], code_c))
            i = j
        return tokens

    def _render_code_line(self, line):
        """Render a line inside a code fence with syntax highlighting."""
        if self._in_view(self.current_y, self.line_height):
            code_bg = theme.colors['code_bg']
            draw_rectangle(self.gr, self.x, self.current_y,
                           self.x + self.width, self.current_y + self.line_height,
                           code_bg, 255, code_bg, 255)
            if line:
                lang = self._code_lang
                if lang and lang in self._KW:
                    tokens = self._tokenize_code(line, lang)
                    cx = self.x + 4
                    for text, color in tokens:
                        tw = text_width(text, FONT_10)
                        if cx + tw > self.x + self.width:
                            break
                        draw_text(self.gr, cx, self.current_y,
                                  text, FONT_10, color,
                                  self.width, bg_color=code_bg)
                        cx += tw
                else:
                    draw_text(self.gr, self.x + 4, self.current_y,
                              line, FONT_10, theme.colors['code'],
                              self.width - 4, bg_color=code_bg)
        self.current_y += self.line_height

    def _flush_math(self):
        """Render collected math fence lines as pretty-printed formulas."""
        for line in self._math_buffer:
            expr = line.strip()
            if expr:
                self._render_formula(expr)
        self._math_buffer = []

    def _render_formula(self, expr):
        """Render a CAS expression as a formatted formula."""
        # Get cached dimensions or measure
        if expr in self._formula_cache:
            size = self._formula_cache[expr]
        else:
            size = get_formula_size(expr)
            if size is None:
                fw = min(text_width(expr, FONT_10) + 20,
                         self.width - 20)
                size = (fw, 14)
            self._formula_cache[expr] = size

        fw, fh = size
        pad = 6
        total_w = fw + pad * 2 + 2
        total_h = fh + pad * 2 + 2

        # Clamp width to available area
        if total_w > self.width:
            total_w = self.width

        # Center horizontally
        fx = self.x + (self.width - total_w) // 2

        c = theme.colors
        if self._in_view(self.current_y, total_h):
            render_formula(self.gr, fx, self.current_y,
                           expr, fw, fh,
                           c.get('formula_border', c['table_border']),
                           c['normal'])

        self.current_y += total_h + 4

    def _is_ordered_list(self, line):
        """Check if line starts with a number followed by '. '."""
        dot = line.find('.')
        if dot > 0 and dot < len(line) - 1 and line[dot + 1] == ' ':
            return line[:dot].isdigit()
        return False

    def _render_hr(self):
        """Render a horizontal rule."""
        self.current_y += 4
        if self._in_view(self.current_y, 1):
            draw_rectangle(self.gr, self.x, self.current_y,
                      self.x + self.width, self.current_y + 1,
                      theme.colors['normal'], 255,
                      theme.colors['normal'], 255)
        self.current_y += 6

    def _render_header(self, line):
        """Render a header line (# Header)."""
        level = 0
        while level < len(line) and line[level] == '#':
            level += 1
        if level > 6:
            level = 6

        text = line[level:].strip()

        if level == 1:
            fontsize = FONT_14
            self.current_y += 3
        elif level == 2:
            fontsize = FONT_12
            self.current_y += 2
        else:
            fontsize = FONT_10

        if self._in_view(self.current_y, self.line_height + fontsize * 4):
            draw_text(self.gr, self.x, self.current_y,
                      text, fontsize, theme.colors['header'], self.width)
        self.current_y += self.line_height + fontsize * 4
        self.current_y += 3

    def _render_blockquote(self, line):
        """Render a blockquote line (> text), supports nesting."""
        depth = 0
        temp = line
        while temp.startswith('>'):
            depth += 1
            temp = temp[1:]
            if temp.startswith(' '):
                temp = temp[1:]

        text_x = self.x + depth * BLOCKQUOTE_INDENT
        self._blockquote_depth = depth
        self._render_wrapped(temp.strip(), text_x)
        self._blockquote_depth = 0

    def _render_task_list_item(self, text, checked, indent_level=0):
        """Render a task list item with checkbox."""
        indent = indent_level * NESTED_LIST_INDENT
        box_x = self.x + 10 + indent
        box_y = self.current_y + 2
        box_size = 8
        text_x = box_x + box_size + 5

        if self._in_view(self.current_y):
            # Draw checkbox border
            draw_rectangle(self.gr, box_x, box_y,
                           box_x + box_size, box_y + box_size,
                           theme.colors['normal'], 255,
                           theme.colors['bg'], 255)
            if checked:
                # Draw filled check indicator
                draw_rectangle(self.gr, box_x + 2, box_y + 2,
                               box_x + box_size - 2, box_y + box_size - 2,
                               theme.colors['task_done'], 255,
                               theme.colors['task_done'], 255)

        self._render_wrapped(text, text_x)

    def _render_list_item(self, text, bullet='\u2022', indent_level=0):
        """Render a list item with bullet or number prefix."""
        indent = indent_level * NESTED_LIST_INDENT
        bullet_x = self.x + 10 + indent
        text_x = self.x + 25 + indent

        if self._in_view(self.current_y):
            draw_text(self.gr, bullet_x, self.current_y,
                      bullet, FONT_10, theme.colors['normal'],
                      self.x + self.width - bullet_x)
        self._render_wrapped(text, text_x)

    def _is_table_separator(self, cells):
        """Check if cells form a separator row like |---|---|."""
        for c in cells:
            stripped = c.replace('-', '').replace(':', '').replace(' ', '')
            if stripped != '':
                return False
        return True

    def _buffer_table_line(self, line):
        """Buffer a table row for later rendering."""
        parts = line.split('|')
        if parts and parts[0].strip() == '':
            parts = parts[1:]
        if parts and parts[-1].strip() == '':
            parts = parts[:-1]
        cells = [c.strip() for c in parts]
        if self._is_table_separator(cells):
            return
        self._table_buffer.append(cells)

    def _flush_table(self):
        """Render a buffered table."""
        rows = self._table_buffer
        self._table_buffer = []
        if not rows:
            return

        num_cols = max(len(r) for r in rows)

        if num_cols > TABLE_MAX_COLS:
            self._render_table_warning(num_cols)
            return

        col_widths = [0] * num_cols
        for row in rows:
            for i in range(len(row)):
                if i < num_cols:
                    w = text_width(row[i], FONT_10)
                    if w > col_widths[i]:
                        col_widths[i] = w

        pad = TABLE_CELL_PAD
        total_w = sum(w + pad * 2 for w in col_widths) + num_cols + 1

        if total_w > self.width:
            avail = self.width - (num_cols + 1)
            per_col = avail // num_cols - pad * 2
            if per_col < 10:
                self._render_table_warning(num_cols)
                return
            col_widths = [per_col] * num_cols
            total_w = self.width

        row_h = self.line_height + 2
        c = theme.colors
        th_bg = c['table_header_bg']
        alt_bg = c['table_alt_bg']
        bg = c['bg']
        t_border = c['table_border']
        c_bold = c['bold']
        c_normal = c['normal']

        for ri in range(len(rows)):
            row = rows[ri]
            is_header = (ri == 0)

            if is_header:
                row_bg = th_bg
            elif ri % 2 == 0:
                row_bg = alt_bg
            else:
                row_bg = bg

            if self._in_view(self.current_y, row_h):
                cx = self.x
                for ci in range(num_cols):
                    cell_w = col_widths[ci] + pad * 2
                    cell_text = row[ci] if ci < len(row) else ''

                    draw_rectangle(self.gr, cx, self.current_y,
                                   cx + cell_w, self.current_y + row_h,
                                   t_border, 255, row_bg, 255)

                    txt_color = c_bold if is_header else c_normal
                    draw_text(self.gr, cx + pad, self.current_y + 1,
                              cell_text, FONT_10, txt_color,
                              col_widths[ci])
                    if is_header:
                        draw_text(self.gr, cx + pad + 1, self.current_y + 1,
                                  cell_text, FONT_10, c_bold,
                                  col_widths[ci])
                    cx += cell_w

            self.current_y += row_h

        self.current_y += 4

    def _render_table_warning(self, num_cols):
        """Show a warning when a table is too wide to render."""
        msg = '[Table too wide (' + str(num_cols) + ' cols)]'
        if self._in_view(self.current_y):
            draw_text(self.gr, self.x, self.current_y,
                      msg, FONT_10, theme.colors['warning'], self.width)
        self.current_y += self.line_height

    def _render_paragraph(self, line):
        """Render a paragraph with inline formatting."""
        self._render_wrapped(line, self.x)

    def _draw_line_decorations(self):
        """Draw blockquote decorations for the current line."""
        if self._blockquote_depth > 0 and self._in_view(self.current_y, self.line_height):
            bq_bg = theme.colors['blockquote_bg']
            bq_bar = theme.colors['blockquote_bar']
            draw_rectangle(self.gr, self.x, self.current_y,
                           self.x + self.width, self.current_y + self.line_height,
                           bq_bg, 255, bq_bg, 255)
            for d in range(self._blockquote_depth):
                bx = self.x + d * BLOCKQUOTE_INDENT + 3
                draw_rectangle(self.gr, bx, self.current_y,
                               bx + BLOCKQUOTE_BAR_WIDTH,
                               self.current_y + self.line_height,
                               bq_bar, 255, bq_bar, 255)

    def _render_wrapped(self, text, start_x):
        """Render text with word wrapping and inline formatting."""
        segments = self._parse_inline(text)
        current_x = start_x
        max_x = self.x + self.width - SCROLLBAR_WIDTH - 1

        self._draw_line_decorations()

        # Cache frequently accessed theme colors
        c = theme.colors
        color_map = {
            'normal': c['normal'],
            'bold': c['bold'],
            'italic': c['italic'],
            'code': c['code'],
            'link': c['link'],
            'strikethrough': c['strikethrough'],
        }
        search_hl = c['search_hl']
        search_term = self._search_term

        for seg in segments:
            seg_type = seg[0]
            seg_text = seg[1]
            seg_url = seg[2] if len(seg) > 2 else None
            color = color_map.get(seg_type, color_map['normal'])

            words = seg_text.split(' ')
            for wi in range(len(words)):
                word = words[wi]
                if wi > 0:
                    sp_w = text_width(' ', FONT_10)
                    if current_x + sp_w > max_x and current_x > start_x:
                        self.current_y += self.line_height
                        current_x = start_x
                        self._draw_line_decorations()
                    else:
                        current_x += sp_w

                if not word:
                    continue

                word = str(word)
                w = text_width(word, FONT_10)
                if current_x + w > max_x and current_x > start_x:
                    self.current_y += self.line_height
                    current_x = start_x
                    self._draw_line_decorations()

                if self._in_view(self.current_y):
                    clip_w = max_x - current_x

                    # Search highlighting
                    hw = word if self._search_case else word.lower()
                    if search_term and search_term in hw:
                        draw_rectangle(self.gr, current_x, self.current_y,
                                       current_x + w,
                                       self.current_y + self.line_height,
                                       search_hl, 255, search_hl, 255)
                        abs_y = self.current_y + self.scroll_offset
                        if abs_y not in self._search_positions:
                            self._search_positions.append(abs_y)

                    draw_text(self.gr, current_x, self.current_y,
                              word, FONT_10, color, clip_w)
                    if seg_type == 'bold':
                        draw_text(self.gr, current_x + 1, self.current_y,
                                  word, FONT_10, color, clip_w)

                    # Strikethrough line
                    if seg_type == 'strikethrough':
                        mid_y = self.current_y + self.line_height // 2
                        draw_rectangle(self.gr, current_x, mid_y,
                                       current_x + w, mid_y + 1,
                                       color, 255, color, 255)

                    # Record link zones for tap detection
                    if seg_type == 'link' and seg_url:
                        self._link_zones.append((
                            current_x, self.current_y,
                            current_x + w,
                            self.current_y + self.line_height,
                            seg_url))

                elif search_term and search_term in word.lower():
                    # Record position even for off-screen matches
                    abs_y = self.current_y + self.scroll_offset
                    if abs_y not in self._search_positions:
                        self._search_positions.append(abs_y)

                current_x += w

        self.current_y += self.line_height

    def _parse_inline(self, text):
        """Parse inline markdown formatting.

        Returns list of tuples: (type, text) or (type, text, url) for links.
        Type is one of: 'normal', 'bold', 'italic', 'code', 'strikethrough', 'link'.
        """
        segments = []
        i = 0
        buf = []  # Use list + join instead of string concatenation

        while i < len(text):
            # ~~strikethrough~~
            if i < len(text) - 1 and text[i:i + 2] == '~~':
                if buf:
                    segments.append(('normal', ''.join(buf)))
                    buf = []
                end = text.find('~~', i + 2)
                if end != -1:
                    segments.append(('strikethrough', text[i + 2:end]))
                    i = end + 2
                    continue

            # [link text](url)
            if text[i] == '[':
                bracket_end = text.find(']', i + 1)
                if (bracket_end != -1 and bracket_end + 1 < len(text)
                        and text[bracket_end + 1] == '('):
                    paren_end = text.find(')', bracket_end + 2)
                    if paren_end != -1:
                        if buf:
                            segments.append(('normal', ''.join(buf)))
                            buf = []
                        link_text = text[i + 1:bracket_end]
                        link_url = text[bracket_end + 2:paren_end]
                        segments.append(('link', link_text, link_url))
                        i = paren_end + 1
                        continue

            # **bold**
            if i < len(text) - 1 and text[i:i + 2] == '**':
                if buf:
                    segments.append(('normal', ''.join(buf)))
                    buf = []
                end = text.find('**', i + 2)
                if end != -1:
                    segments.append(('bold', text[i + 2:end]))
                    i = end + 2
                    continue

            # *italic*
            elif text[i] == '*':
                if buf:
                    segments.append(('normal', ''.join(buf)))
                    buf = []
                end = text.find('*', i + 1)
                if end != -1:
                    segments.append(('italic', text[i + 1:end]))
                    i = end + 1
                    continue

            # `code`
            elif text[i] == '`':
                if buf:
                    segments.append(('normal', ''.join(buf)))
                    buf = []
                end = text.find('`', i + 1)
                if end != -1:
                    segments.append(('code', text[i + 1:end]))
                    i = end + 1
                    continue

            buf.append(text[i])
            i += 1

        if buf:
            segments.append(('normal', ''.join(buf)))

        return segments if segments else [('normal', text)]

    def _render_image(self, line):
        """Render an image from ![alt](source)."""
        bracket_end = line.find(']')
        if bracket_end == -1:
            self._render_paragraph(line)
            return
        paren_start = line.find('(', bracket_end)
        paren_end = line.rfind(')')
        if paren_start == -1 or paren_end == -1:
            self._render_paragraph(line)
            return

        url = line[paren_start + 1:paren_end]

        if 'base64,' in url:
            self._render_base64_image(url)
        else:
            self._render_file_image(url)

    def _render_file_image(self, filename):
        """Render an image loaded from a file via AFiles."""
        try:
            open_file(GR_TMP, filename)
            size = get_grob_size(GR_TMP)
            if not size:
                return
            img_w, img_h = size

            display_w = img_w
            display_h = img_h
            if display_w > self.width:
                display_h = int(img_h * self.width / img_w)
                display_w = self.width

            img_x = self.x + (self.width - display_w) // 2
            if self._in_view(self.current_y, display_h):
                blit(self.gr, img_x, self.current_y,
                     img_x + display_w, self.current_y + display_h,
                     GR_TMP, 0, 0, img_w, img_h,
                     TRANSPARENCY)
            self.current_y += display_h + 4
        except:
            pass

    def _render_base64_image(self, url):
        """Render an image from base64-encoded raw pixel data."""
        b64_data = url[url.index('base64,') + 7:]
        raw = self._base64_decode(b64_data)
        if len(raw) < 5:
            return

        img_w = (raw[0] << 8) | raw[1]
        img_h = (raw[2] << 8) | raw[3]
        pixel_data = raw[4:]

        if img_w <= 0 or img_h <= 0:
            return
        if len(pixel_data) < img_w * img_h * 3:
            return

        img_x = self.x + (self.width - img_w) // 2
        if self._in_view(self.current_y, img_h):
            draw_image(self.gr, img_x, self.current_y,
                       pixel_data, img_w, img_h)
        self.current_y += img_h + 4

    def _base64_decode(self, data):
        """Decode base64 string to bytes."""
        table = MarkdownRenderer._B64
        data = data.replace('\n', '').replace('\r', '').replace(' ', '').rstrip('=')
        result = []
        buf = 0
        bits = 0
        for c in data:
            if c in table:
                buf = (buf << 6) | table[c]
                bits += 6
                if bits >= 8:
                    bits -= 8
                    result.append((buf >> bits) & 0xFF)
        return bytes(result)

    def _draw_scrollbar(self):
        """Draw a scrollbar on the right edge."""
        if self._content_height <= self.height:
            return

        bar_x = self.x + self.width - SCROLLBAR_WIDTH
        bar_y = self.y
        bar_h = self.height

        # Track
        draw_rectangle(self.gr, bar_x, bar_y,
                       bar_x + SCROLLBAR_WIDTH, bar_y + bar_h,
                       theme.colors['scrollbar'], 255,
                       theme.colors['scrollbar'], 255)

        # Thumb
        visible_ratio = self.height / self._content_height
        thumb_h = max(SCROLLBAR_MIN_THUMB, int(bar_h * visible_ratio))
        max_s = self._max_scroll()
        if max_s > 0:
            thumb_y = bar_y + int((bar_h - thumb_h) * self.scroll_offset / max_s)
        else:
            thumb_y = bar_y

        draw_rectangle(self.gr, bar_x, thumb_y,
                       bar_x + SCROLLBAR_WIDTH, thumb_y + thumb_h,
                       theme.colors['scrollbar_thumb'], 255,
                       theme.colors['scrollbar_thumb'], 255)

        # Bookmark marks (red indicators)
        if self._bookmarks and self._content_height > 0:
            for bpos in self._bookmarks:
                if bpos <= self._content_height:
                    mark_y = bar_y + int(bar_h * bpos / self._content_height)
                    if mark_y < bar_y:
                        mark_y = bar_y
                    if mark_y > bar_y + bar_h - 2:
                        mark_y = bar_y + bar_h - 2
                    draw_rectangle(self.gr, bar_x - 1, mark_y,
                                   bar_x + SCROLLBAR_WIDTH + 1, mark_y + 2,
                                   theme.colors['bookmark_mark'], 255,
                                   theme.colors['bookmark_mark'], 255)

        # Search match marks (yellow indicators)
        if self._search_positions and self._content_height > 0:
            hl_c = theme.colors['search_hl']
            for spos in self._search_positions:
                mark_y = bar_y + int(bar_h * spos / self._content_height)
                if mark_y < bar_y:
                    mark_y = bar_y
                if mark_y > bar_y + bar_h - 2:
                    mark_y = bar_y + bar_h - 2
                draw_rectangle(self.gr, bar_x, mark_y,
                               bar_x + SCROLLBAR_WIDTH, mark_y + 2,
                               hl_c, 255, hl_c, 255)

    def _max_scroll(self):
        """Get the maximum scroll offset."""
        max_off = self._content_height - self.height
        return max_off if max_off > 0 else 0

    def scroll_up(self, amount=20):
        self.scroll_offset -= amount
        if self.scroll_offset < 0:
            self.scroll_offset = 0

    def scroll_down(self, amount=20):
        self.scroll_offset += amount
        m = self._max_scroll()
        if self.scroll_offset > m:
            self.scroll_offset = m

    def scroll_by(self, delta):
        self.scroll_offset += delta
        if self.scroll_offset < 0:
            self.scroll_offset = 0
        m = self._max_scroll()
        if self.scroll_offset > m:
            self.scroll_offset = m

    def scroll_page_up(self):
        self.scroll_offset -= self.height
        if self.scroll_offset < 0:
            self.scroll_offset = 0

    def scroll_page_down(self):
        self.scroll_offset += self.height
        m = self._max_scroll()
        if self.scroll_offset > m:
            self.scroll_offset = m

    def scroll_to_top(self):
        self.scroll_offset = 0

    def scroll_to_bottom(self):
        self.scroll_offset = self._max_scroll()


class MarkdownDocument:
    """Loads and manages markdown document content."""

    def __init__(self):
        self.content = ""
        self.renderer = None

    def load_file(self, filename):
        """Load markdown from a text file."""
        try:
            with open(filename, 'r') as f:
                self.content = f.read()
            return True
        except:
            self.content = "# Error\n\nCould not load file: " + filename
            return False

    def render(self, gr, x=5, y=5, width=310, height=230):
        """Render the document to a graphics buffer."""
        if not self.renderer:
            self.renderer = MarkdownRenderer(gr, x, y, width, height)
        self.renderer.render(self.content)

    def scroll_up(self):
        if self.renderer:
            self.renderer.scroll_up()
            self.renderer.render(self.content)

    def scroll_down(self):
        if self.renderer:
            self.renderer.scroll_down()
            self.renderer.render(self.content)

    def scroll_by(self, delta):
        if self.renderer:
            self.renderer.scroll_by(delta)
            self.renderer.render(self.content)

    def scroll_page_up(self):
        if self.renderer:
            self.renderer.scroll_page_up()
            self.renderer.render(self.content)

    def scroll_page_down(self):
        if self.renderer:
            self.renderer.scroll_page_down()
            self.renderer.render(self.content)

    def scroll_to_top(self):
        if self.renderer:
            self.renderer.scroll_to_top()
            self.renderer.render(self.content)

    def scroll_to_bottom(self):
        if self.renderer:
            self.renderer.scroll_to_bottom()
            self.renderer.render(self.content)
