from graphics import draw_text, draw_rectangle, text_width, draw_image
from constants import (FONT_10, FONT_12, FONT_14,
    COLOR_NORMAL, COLOR_HEADER, COLOR_CODE, COLOR_BOLD, COLOR_ITALIC, COLOR_BG)


class MarkdownViewer:
    """A simple markdown viewer for HP Prime."""

    def __init__(self, gr):
        self.gr = gr
        self.document = MarkdownDocument()

    def load_markdown_file(self, filename):
        """Load markdown content from a file."""
        return self.document.load_file(filename)

    def render(self):
        """Render the loaded markdown document."""
        self.document.render(self.gr)

    def scroll_up(self):
        """Scroll the document up."""
        self.document.scroll_up()

    def scroll_down(self):
        """Scroll the document down."""
        self.document.scroll_down()


class MarkdownRenderer:
    """Lightweight markdown renderer for HP Prime display (320x240)."""

    def __init__(self, gr, x=5, y=5, width=310, height=230):
        self.gr = gr
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.current_y = y
        self.line_height = 12
        self.scroll_offset = 0

    def _in_view(self, y, h=12):
        """Check if a line at y with height h is fully within the visible area."""
        return y >= self.y and y + h <= self.y + self.height

    def clear(self):
        """Clear the rendering area."""
        draw_rectangle(self.gr, self.x, self.y,
                  self.x + self.width, self.y + self.height,
                  COLOR_BG, 255, COLOR_BG, 255)
        self.current_y = self.y

    def render(self, markdown_text):
        """Render markdown text to the graphics buffer."""
        self.clear()
        self.current_y = self.y - self.scroll_offset
        lines = markdown_text.split('\n')

        for line in lines:
            if self.current_y > self.y + self.height:
                break
            self._render_line(line)

    def _render_line(self, line):
        """Render a single line of markdown."""
        line = line.rstrip()

        if not line:
            self.current_y += self.line_height // 2
            return

        if line.startswith('!['):
            self._render_image(line)
        elif line.startswith('#'):
            self._render_header(line)
        elif line == '---' or line == '***' or line == '___':
            self._render_hr()
        elif line.startswith('- ') or line.startswith('* '):
            self._render_list_item(line[2:])
        elif self._is_ordered_list(line):
            dot = line.index('.')
            num = line[:dot]
            text = line[dot + 1:].lstrip()
            if text:
                self._render_list_item(text, bullet=num + '.')
        elif line.startswith('```'):
            return
        else:
            self._render_paragraph(line)

    def _is_ordered_list(self, line):
        """Check if line starts with a number followed by '. '."""
        dot = line.find('.')
        if dot > 0 and dot < len(line) - 1 and line[dot + 1] == ' ':
            return line[:dot].isdigit()
        return False

    def _render_hr(self):
        """Render a horizontal rule (--- or *** or ___)."""
        self.current_y += 4
        if self._in_view(self.current_y, 1):
            draw_rectangle(self.gr, self.x, self.current_y,
                      self.x + self.width, self.current_y + 1,
                      COLOR_NORMAL, 255, COLOR_NORMAL, 255)
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
                      text, fontsize, COLOR_HEADER, self.width)
        self.current_y += self.line_height + fontsize * 4
        self.current_y += 3

    def _render_list_item(self, text, bullet='\u2022'):
        """Render a list item with bullet or number prefix."""
        bullet_x = self.x + 10
        text_x = self.x + 25

        if self._in_view(self.current_y):
            draw_text(self.gr, bullet_x, self.current_y,
                      bullet, FONT_10, COLOR_NORMAL,
                      self.x + self.width - bullet_x)
        self._render_wrapped(text, text_x)

    def _render_paragraph(self, line):
        """Render a paragraph with inline formatting."""
        self._render_wrapped(line, self.x)

    def _render_wrapped(self, text, start_x):
        """Render text with word wrapping and inline formatting."""
        segments = self._parse_inline(text)
        current_x = start_x
        max_x = self.x + self.width

        for seg_type, seg_text in segments:
            color = COLOR_NORMAL
            if seg_type == 'bold':
                color = COLOR_BOLD
            elif seg_type == 'italic':
                color = COLOR_ITALIC
            elif seg_type == 'code':
                color = COLOR_CODE

            words = seg_text.split(' ')
            for wi in range(len(words)):
                word = words[wi]
                if wi > 0:
                    sp_w = text_width(' ', FONT_10)
                    if current_x + sp_w > max_x and current_x > start_x:
                        self.current_y += self.line_height
                        current_x = start_x
                    else:
                        current_x += sp_w

                if not word:
                    continue

                w = text_width(word, FONT_10)
                if current_x + w > max_x and current_x > start_x:
                    self.current_y += self.line_height
                    current_x = start_x

                if self._in_view(self.current_y):
                    clip_w = max_x - current_x
                    draw_text(self.gr, current_x, self.current_y,
                              word, FONT_10, color, clip_w)
                    if seg_type == 'bold':
                        draw_text(self.gr, current_x + 1, self.current_y,
                                  word, FONT_10, color, clip_w)
                current_x += w

        self.current_y += self.line_height

    def _parse_inline(self, text):
        """Parse inline markdown formatting.

        Returns list of (type, text) tuples where type is one of:
        'normal', 'bold', 'italic', 'code'.
        """
        segments = []
        i = 0
        current_text = ""

        while i < len(text):
            # Check for **bold**
            if i < len(text) - 1 and text[i:i + 2] == '**':
                if current_text:
                    segments.append(('normal', current_text))
                    current_text = ""
                end = text.find('**', i + 2)
                if end != -1:
                    segments.append(('bold', text[i + 2:end]))
                    i = end + 2
                    continue

            # Check for *italic*
            elif text[i] == '*':
                if current_text:
                    segments.append(('normal', current_text))
                    current_text = ""
                end = text.find('*', i + 1)
                if end != -1:
                    segments.append(('italic', text[i + 1:end]))
                    i = end + 1
                    continue

            # Check for `code`
            elif text[i] == '`':
                if current_text:
                    segments.append(('normal', current_text))
                    current_text = ""
                end = text.find('`', i + 1)
                if end != -1:
                    segments.append(('code', text[i + 1:end]))
                    i = end + 1
                    continue

            current_text += text[i]
            i += 1

        if current_text:
            segments.append(('normal', current_text))

        return segments if segments else [('normal', text)]

    def _render_image(self, line):
        """Render an image from ![alt](data:image/...;base64,...)."""
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
        if 'base64,' not in url:
            self._render_paragraph(line)
            return

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
        table = {}
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        for i in range(64):
            table[chars[i]] = i
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

    def scroll_up(self, amount=20):
        """Scroll content up."""
        self.scroll_offset -= amount
        if self.scroll_offset < 0:
            self.scroll_offset = 0

    def scroll_down(self, amount=20):
        """Scroll content down."""
        self.scroll_offset += amount


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
        """Scroll the document up and re-render."""
        if self.renderer:
            self.renderer.scroll_up()
            self.renderer.render(self.content)

    def scroll_down(self):
        """Scroll the document down and re-render."""
        if self.renderer:
            self.renderer.scroll_down()
            self.renderer.render(self.content) 