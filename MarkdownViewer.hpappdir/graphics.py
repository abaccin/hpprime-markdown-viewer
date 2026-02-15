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
