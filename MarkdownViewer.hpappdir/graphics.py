from hpprime import eval, fillrect, dimgrob


def draw_rectangle(gr, x1, y1, x2, y2, edge_color, edge_alpha,
              fill_color=0x0, fill_alpha=255):
    """Draw a rectangle with edge and fill colors."""
    fillrect(gr, x1, y1, x2 - x1, y2 - y1, edge_color, fill_color)


def _escape_text(text):
    """Escape special characters for use in PPL eval strings."""
    return str(text).replace('\\', '\\\\').replace('"', '\\"')


def draw_text(gr, x, y, text, fontsize, text_color, width=320, bg_color=None):
    """Draw text at (x, y). If bg_color is None, no background is drawn."""
    safe = _escape_text(text)
    r = (text_color >> 16) & 0xFF
    g = (text_color >> 8) & 0xFF
    b = text_color & 0xFF
    if bg_color is not None:
        r2 = (bg_color >> 16) & 0xFF
        g2 = (bg_color >> 8) & 0xFF
        b2 = bg_color & 0xFF
        eval('TEXTOUT_P("%s",G%d,%d,%d,%d,RGB(%d,%d,%d),%d,RGB(%d,%d,%d))'
             % (safe, gr, x, y, fontsize, r, g, b, width, r2, g2, b2))
    else:
        eval('TEXTOUT_P("%s",G%d,%d,%d,%d,RGB(%d,%d,%d),%d)'
             % (safe, gr, x, y, fontsize, r, g, b, width))


def text_width(text, fontsize):
    """Get the pixel width of text at the given font size."""
    safe = _escape_text(text)
    result = eval('TEXTSIZE("%s",%d)' % (safe, fontsize))
    if type(result) is list:
        return result[0]
    return result


def draw_image(gr, x, y, pixel_data, img_width, img_height,
               tmp_gr=5):
    """Draw a raw RGB image using off-screen buffer with run-length optimization.

    pixel_data is bytes: R,G,B triplets for each pixel, row by row.
    White pixels (0xFFFFFF) are treated as transparent (not drawn).
    Draws to a temp buffer first, then blits to the destination in one call.
    Consecutive same-color pixels in each row are merged into a single fillrect.
    """
    # Create temp grob filled with white (matches background)
    dimgrob(tmp_gr, img_width, img_height, 0xFFFFFF)

    # Draw pixels row by row with horizontal run-length optimization
    idx = 0
    for row in range(img_height):
        run_start = 0
        run_color = -1

        for col in range(img_width):
            if idx + 2 < len(pixel_data):
                r = pixel_data[idx]
                g = pixel_data[idx + 1]
                b = pixel_data[idx + 2]
                color = (r << 16) | (g << 8) | b
                idx += 3
            else:
                color = -1

            # White pixels are transparent — skip them
            if color == 0xFFFFFF:
                color = -1

            if color != run_color:
                # Flush previous run if it's a visible color
                if run_color >= 0:
                    fillrect(tmp_gr, run_start, row,
                             col - run_start, 1, run_color, run_color)
                run_start = col
                run_color = color

        # Flush last run in row
        if run_color >= 0:
            fillrect(tmp_gr, run_start, row,
                     img_width - run_start, 1, run_color, run_color)

    # Blit to destination in one call (no transparency needed, white = background)
    blit(gr, x, y, x + img_width, y + img_height,
         tmp_gr, 0, 0, img_width, img_height)


def open_file(gr, name, app_name=""):
    """Load an image file into a graphics buffer using AFiles.

    gr: target graphics buffer number
    name: filename (e.g. 'icon.png')
    app_name: app name for cross-app file access (optional)
    """
    if app_name == "":
        eval('G%d:=AFiles("%s")' % (gr, name))
    else:
        eval('G%d:=EXPR(REPLACE("%s"," ","_")+".AFiles(""%s"")")' % (gr, app_name, name))


def blit(gr, dx1, dy1, dx2, dy2, src_gr, sx1, sy1, sx2, sy2,
         transp_color=0xA8A8A7, transp_alpha=255):
    """Blit (copy) a region from one graphics buffer to another.

    gr: destination buffer
    dx1,dy1,dx2,dy2: destination rectangle
    src_gr: source buffer
    sx1,sy1,sx2,sy2: source rectangle
    transp_color: color to treat as transparent
    transp_alpha: transparency alpha (255 = fully opaque / no transparency effect)
    """
    if transp_alpha != 255:
        cmd = "BLIT_P(G{0},{1},{2},{3},{4},G{5},{6},{7},{8},{9},{10},{11})".format(
            gr, dx1, dy1, dx2, dy2, src_gr, sx1, sy1, sx2, sy2,
            transp_color, transp_alpha)
    else:
        cmd = "BLIT_P(G{0},{1},{2},{3},{4},G{5},{6},{7},{8},{9})".format(
            gr, dx1, dy1, dx2, dy2, src_gr, sx1, sy1, sx2, sy2)
    eval(cmd)


def _parse_func_args(s):
    """Split comma-separated args respecting parentheses."""
    args = []
    depth = 0
    start = 0
    for i in range(len(s)):
        c = s[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif c == ',' and depth == 0:
            args.append(s[start:i].strip())
            start = i + 1
    args.append(s[start:].strip())
    return args


def _math_subs(s):
    """Apply Unicode math symbol substitutions."""
    s = s.replace('infinity', '\u221e')
    s = s.replace('inf', '\u221e')
    s = s.replace('pi', '\u03c0')
    s = s.replace('sqrt(', '\u221a(')
    s = s.replace('^2', '\u00b2')
    s = s.replace('^3', '\u00b3')
    s = s.replace('*', '\u00b7')
    return s


def _try_func(s):
    """Try to transform known CAS function patterns."""
    sl = s.lower()

    if sl.startswith('integrate(') and s.endswith(')'):
        args = _parse_func_args(s[10:-1])
        if len(args) >= 2:
            f = _math_subs(args[0])
            v = args[1]
            if len(args) == 4:
                a = _math_subs(args[2])
                b = _math_subs(args[3])
                return '\u222b[%s,%s] %s d%s' % (a, b, f, v)
            return '\u222b %s d%s' % (f, v)

    if sl.startswith('sum(') and s.endswith(')'):
        args = _parse_func_args(s[4:-1])
        if len(args) >= 4:
            f = _math_subs(args[0])
            v = args[1]
            a = _math_subs(args[2])
            b = _math_subs(args[3])
            return '\u03a3(%s=%s..%s) %s' % (v, a, b, f)
        if len(args) >= 1:
            return '\u03a3 ' + _math_subs(args[0])

    if sl.startswith('diff(') and s.endswith(')'):
        args = _parse_func_args(s[5:-1])
        if len(args) >= 2:
            f = _math_subs(args[0])
            v = args[1]
            return 'd/d%s(%s)' % (v, f)

    if sl.startswith('limit(') and s.endswith(')'):
        args = _parse_func_args(s[6:-1])
        if len(args) >= 3:
            f = _math_subs(args[0])
            v = args[1]
            a = _math_subs(args[2])
            return 'lim(%s\u2192%s) %s' % (v, a, f)

    return None


def format_math(expr):
    """Transform a CAS expression into readable math text."""
    s = expr.strip()
    result = _try_func(s)
    if result is not None:
        return result
    return _math_subs(s)


FORMULA_FONT = 2  # FONT_12


def get_formula_size(expr):
    """Get pixel dimensions for a formatted formula."""
    display = format_math(expr)
    safe = _escape_text(display)
    try:
        result = eval('TEXTSIZE("%s",%d)' % (safe, FORMULA_FONT))
        if type(result) is list and len(result) >= 2:
            return (int(result[0]), int(result[1]))
    except:
        pass
    return None


def _rgb_str(color):
    """Convert 0xRRGGBB integer to 'RGB(r,g,b)' PPL string."""
    return "RGB(%d,%d,%d)" % (
        (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF)


def render_formula(gr, dest_x, dest_y, expr, expr_w, expr_h,
                   border_color, text_color):
    """Render a formula as formatted text in a bordered box."""
    display = format_math(expr)
    safe = _escape_text(display)
    pad = 6
    gw = expr_w + pad * 2
    gh = expr_h + pad * 2
    bc = _rgb_str(border_color)
    tc = _rgb_str(text_color)

    x1 = dest_x
    y1 = dest_y
    x2 = x1 + gw + 1
    y2 = y1 + gh + 1

    # Draw bordered white box
    eval("RECT_P(G%d,%d,%d,%d,%d,%s,RGB(255,255,255))" %
         (gr, x1, y1, x2, y2, bc))

    # Draw formatted text
    eval('TEXTOUT_P("%s",G%d,%d,%d,%d,%s,%d)' %
         (safe, gr, x1 + pad, y1 + pad, FORMULA_FONT, tc, gw))


def get_grob_size(gr):
    """Get the width and height of a graphics buffer.

    Returns (width, height) or None on failure.
    """
    try:
        w = int(eval('GROBW_P(G%d)' % gr) or 0)
        h = int(eval('GROBH_P(G%d)' % gr) or 0)
        if w > 0 and h > 0:
            return (w, h)
    except:
        pass
    return None
