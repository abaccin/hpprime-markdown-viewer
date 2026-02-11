from hpprime import eval, fillrect

def color_to_rgb(color):
    """Extract R, G, B components from a 24-bit hex color."""
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    return r, g, b


def draw_rectangle(gr, x1, y1, x2, y2, edge_color, edge_alpha,
              fill_color=0x0, fill_alpha=255):
    """Draw a rectangle with edge and fill colors."""
    w = x2 - x1
    h = y2 - y1
    fillrect(gr, x1, y1, w, h, edge_color, fill_color)


def draw_text(gr, x, y, text, fontsize, text_color, width=320, bg_color=None):
    """Draw text at (x, y). If bg_color is None, no background is drawn."""
    r1, g1, b1 = color_to_rgb(text_color)
    cmd = ('TEXTOUT_P("' + str(text) + '",G' + str(gr)
           + "," + str(x) + "," + str(y)
           + "," + str(fontsize)
           + ",RGB(" + str(r1) + "," + str(g1) + "," + str(b1) + ")"
           + "," + str(width))
    if bg_color is not None:
        r2, g2, b2 = color_to_rgb(bg_color)
        cmd += ",RGB(" + str(r2) + "," + str(g2) + "," + str(b2) + ")"
    cmd += ")"
    eval(cmd)


def get_mouse():
    """Get the current mouse/touch state."""
    return eval("mouse")


def text_width(text, fontsize):
    """Get the pixel width of text at the given font size."""
    result = eval('TEXTSIZE("' + str(text) + '",' + str(fontsize) + ')')
    if type(result) is list:
        return result[0]
    return result


def draw_image(gr, x, y, pixel_data, img_width, img_height):
    """Draw a raw RGB image pixel by pixel.

    pixel_data is bytes: R,G,B triplets for each pixel, row by row.
    """
    idx = 0
    for row in range(img_height):
        for col in range(img_width):
            if idx + 2 < len(pixel_data):
                r = pixel_data[idx]
                g = pixel_data[idx + 1]
                b = pixel_data[idx + 2]
                color = (r << 16) | (g << 8) | b
                if color != 0xFFFFFF:  # skip white for transparency
                    fillrect(gr, x + col, y + row, 1, 1, color, color)
                idx += 3
