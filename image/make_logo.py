#!/usr/bin/env python3
"""
make_logo.py -- generates the whole Spotipi Photos identity from one geometry.

Two renderings of the same composition, for two different jobs:

  * The ICON is a dot grid inside a rounded square. The dots are the point:
    they say "this is a matrix display" to someone looking at a favicon or a
    README. Used for docs, the website and app icons.

  * The PANEL SPLASH is the same composition drawn as solid shapes at native
    64x64 (and 32x32). No simulated dots here -- on the real hardware the LEDs
    ARE the dots, so drawing more would just fight the display.

The composition is a sun over two ridgelines: a photograph, and a record. The
sun has a hole in the middle.

    python3 make_logo.py

Writes SVG and PNG into this folder, and the panel splashes into ../config/.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.abspath(os.path.join(HERE, "..", "config"))
# Superseded as the live logo by build_logo_assets.py (the owner's photos 01 and 10).
# Kept for the concept sheets; writes only into concepts/option1-generic/.
OUT = os.path.join(HERE, "concepts", "option1-generic")

# ---------------------------------------------------------------- palette ---
PANEL   = (0x14, 0x16, 0x1A)     # the unlit panel
SKY     = (0x25, 0x29, 0x31)     # dim "off" dots, so the grid reads as a grid
SUN     = (0xF5, 0xA5, 0x24)     # amber
RIDGE_F = (0x2E, 0x8F, 0xC8)     # far ridge, blue
RIDGE_N = (0x17, 0xA3, 0x98)     # near ridge, teal
INK     = (0x1A, 0x1C, 0x21)
MUTED   = (0x6B, 0x70, 0x78)

def hexof(c):
    return "#%02x%02x%02x" % c

# ------------------------------------------------------------- composition ---
# Everything below works in a unit square (0..1, y down) so the icon grid and
# the pixel splash can share one definition and stay in step.

SUN_CX, SUN_CY, SUN_R = 0.63, 0.34, 0.175

# The sun is also an LP. The hole is STYLISED, not to scale: a true LP hole
# (0.286" in an 11 7/8" disc, RIAA) is 2.4% of the diameter and vanishes at
# LED resolution. 11% keeps it clearly a record without turning it into a
# doughnut, and on a 64x64 panel it lands on a neat 3-LED "plus".
HOLE_FRAC = 0.11            # hole diameter / disc diameter
HOLE_R = SUN_R * HOLE_FRAC

# Optional record label, for the "label" variant. Real LP labels are roughly
# a third of the disc; the colour is chosen to stand apart from the amber sun,
# the blue/teal ridges and the dark sky.
LABEL_FRAC = 0.36           # label diameter / disc diameter
LABEL_R = SUN_R * LABEL_FRAC
LABEL = (0xE0, 0x3E, 0x6E)  # raspberry: warm enough to sit with amber, never mistaken for it

USE_LABEL = False           # the live logo; flip for the label variant


def ridge_far(x):
    """Far ridgeline: height (unit y, down) of the skyline at x."""
    return 0.66 - 0.20 * math.exp(-((x - 0.34) ** 2) / 0.045)


def ridge_near(x):
    return 0.80 - 0.17 * math.exp(-((x - 0.70) ** 2) / 0.055)


def lattice_sun(c, r, n, label=None):
    """Is grid cell (c, r) of an n x n raster the hole, the label, the sun, or none?

    The centre is snapped onto a cell so the disc is symmetric in both axes --
    round at every size. (Unsnapped, the 16-dot icon came out 6 wide by 5 tall.)

    The hole is always at least one cell: at small sizes the stylised 11%
    would round away to nothing, and a record needs its hole.
    """
    if label is None:
        label = USE_LABEL
    c0 = round(SUN_CX * n - 0.5)
    r0 = round(SUN_CY * n - 0.5)
    d = math.hypot(c - c0, r - r0)
    hole_r = max(0.5, HOLE_R * n) + 1e-9
    if d <= hole_r:
        return "hole"
    if label:
        # the label must show as at least a ring of cells around the hole
        label_r = max(hole_r + 1.0, LABEL_R * n) + 1e-9
        if d <= label_r:
            return "label"
    if d <= SUN_R * n:
        return "sun"
    return None


def colour_at_cell(c, r, n, label=None):
    """Colour of cell (c, r) on an n x n raster: ridges by their curves, sun on the lattice."""
    u, v = (c + 0.5) / n, (r + 0.5) / n
    if v >= ridge_near(u):
        return RIDGE_N
    if v >= ridge_far(u):
        return RIDGE_F
    kind = lattice_sun(c, r, n, label)
    if kind == "sun":
        return SUN
    if kind == "label":
        return LABEL
    return None                                # sky, or the hole


# -------------------------------------------------------------- icon (dots) ---
GRID = 16          # dots across
PAD = 0.085        # inset from the rounded square's edge, in unit terms

def icon_cells():
    """Yield (col, row, cx, cy, colour) for every dot in the icon grid."""
    for r in range(GRID):
        for c in range(GRID):
            yield c, r, (c + 0.5) / GRID, (r + 0.5) / GRID, colour_at_cell(c, r, GRID)

DOT_MIN = 128       # below this the dot grid turns to mush; use solid shapes

def draw_icon_png(size, path, bg=PANEL, dots=None):
    """Rounded-square app icon.

    Responsive by design: at 128px and up the dot grid is legible and says
    "matrix display" at a glance. Below that the dots collapse into noise, so
    small sizes get the same composition drawn solid -- which is also exactly
    what the real panel shows.
    """
    if dots is None:
        dots = size >= DOT_MIN
    ss = 4                                    # supersample for clean circles
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = int(S * 0.22)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=radius, fill=bg + (255,))

    if dots:
        inner = S * (1 - 2 * PAD)
        off = S * PAD
        dot_r = (inner / GRID) * 0.40
        for c, r, u, v, col in icon_cells():
            cx = off + u * inner
            cy = off + v * inner
            col = col or SKY
            d.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
                      fill=col + (255,))
    else:
        # Solid version, drawn on the pixel lattice -- the same rule the panel
        # uses, so a 64px icon is exactly what the 64x64 panel shows.
        art = Image.new("RGBA", (size, size), PANEL + (255,))
        ap = art.load()
        for r_ in range(size):
            for c_ in range(size):
                col = colour_at_cell(c_, r_, size)
                if col:
                    ap[c_, r_] = col + (255,)
        art = art.resize((S, S), Image.NEAREST)
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1],
                                               radius=radius, fill=255)
        img.paste(art, (0, 0), mask)

    img = img.resize((size, size), Image.LANCZOS)
    img.save(path)
    return path

def icon_svg(size=512, transparent=False):
    inner = size * (1 - 2 * PAD)
    off = size * PAD
    dot_r = (inner / GRID) * 0.40
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" role="img" aria-label="Spotipi Photos">',
        '  <title>Spotipi Photos</title>',
    ]
    if not transparent:
        out.append(f'  <rect width="{size}" height="{size}" rx="{size*0.22:.1f}" '
                   f'fill="{hexof(PANEL)}"/>')
    out.append('  <g>')
    for c, r, u, v, col in icon_cells():
        cx = off + u * inner
        cy = off + v * inner
        out.append(f'    <circle cx="{cx:.2f}" cy="{cy:.2f}" r="{dot_r:.2f}" '
                   f'fill="{hexof(col or SKY)}"/>')
    out.append('  </g>')
    out.append('</svg>')
    return "\n".join(out)

# ------------------------------------------------------- panel splash (px) ---
def draw_panel(size, path, preview_scale=1):
    """Native-resolution splash for the matrix: one pixel per LED, no smoothing.

    Anti-aliasing a 64-pixel image and hoping the panel shows it faithfully is
    how the sun ended up 23 LEDs wide and 22 tall. Each LED is decided here,
    on the lattice, so what this writes is exactly what lights up.
    """
    img = Image.new("RGB", (size, size), PANEL)
    px = img.load()
    for r in range(size):
        for c in range(size):
            col = colour_at_cell(c, r, size)
            if col:
                px[c, r] = col
    if preview_scale > 1:
        img = img.resize((size * preview_scale, size * preview_scale), Image.NEAREST)
    img.save(path)
    return path

# ------------------------------------------------------------- wordmark ------
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def draw_wordmark(path, width=1400, dark=False):
    h = width // 4
    bg = PANEL if dark else (0xFA, 0xFA, 0xF8)
    fg = (0xF2, 0xF3, 0xF5) if dark else INK
    sub = (0x9A, 0xA0, 0xA8) if dark else MUTED
    img = Image.new("RGB", (width, h), bg)

    icon_px = int(h * 0.70)
    tmp = "/tmp/_wm_icon.png"
    draw_icon_png(icon_px * 4, tmp, dots=True)   # render big, paste small: keeps dots crisp
    ic = Image.open(tmp).convert("RGBA").resize((icon_px, icon_px), Image.LANCZOS)
    x = int(h * 0.22)
    img.paste(ic, (x, (h - icon_px) // 2), ic)

    d = ImageDraw.Draw(img)
    tx = x + icon_px + int(h * 0.24)
    right_margin = int(h * 0.22)
    avail = width - tx - right_margin

    # shrink the type until "Spotipi Photos" fits inside the right margin
    fs = int(h * 0.36)
    while fs > 8:
        f1 = ImageFont.truetype(FONT_B, fs)
        f2 = ImageFont.truetype(FONT_R, fs)
        w1 = d.textlength("Spotipi", font=f1)
        w2 = d.textlength(" Photos", font=f2)
        if w1 + w2 <= avail:
            break
        fs -= 2

    block_h = fs * 1.30 + int(h * 0.155)
    ty = (h - block_h) / 2
    d.text((tx, ty), "Spotipi", font=f1, fill=fg)
    d.text((tx + w1, ty), " Photos", font=f2, fill=sub)
    d.text((tx + 2, ty + fs * 1.30), "PHOTOS AND ALBUM ART ON AN LED MATRIX",
           font=ImageFont.truetype(FONT_R, int(h * 0.105)), fill=sub)
    img.save(path)
    return path

# ------------------------------------------------------------------- main ----
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    made = []
    open(os.path.join(OUT, "icon.svg"), "w").write(icon_svg(512))
    made.append("image/icon.svg")

    for px in (512, 256, 128, 64, 32, 16):
        draw_icon_png(px, os.path.join(OUT, f"icon-{px}.png"))
        made.append(f"image/icon-{px}.png"
                    + ("  (dot grid)" if px >= DOT_MIN else "  (solid)"))

    ico = os.path.join(OUT, "favicon.ico")
    Image.open(os.path.join(OUT, "icon-256.png")).save(
        ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    made.append("image/favicon.ico")

    draw_wordmark(os.path.join(OUT, "wordmark.png"), dark=False)
    draw_wordmark(os.path.join(OUT, "wordmark-dark.png"), dark=True)
    made += ["image/wordmark.png", "image/wordmark-dark.png"]

    # the splash the panel actually shows
    draw_panel(64, os.path.join(OUT, "default.png"))
    draw_panel(32, os.path.join(OUT, "default-32.png"))
    draw_panel(64, os.path.join(OUT, "panel-splash-preview.png"), preview_scale=4)
    made += ["concepts/option1-generic/default.png", "concepts/option1-generic/default-32.png",
             "concepts/option1-generic/panel-splash-preview.png"]

    print("Written:")
    for m in made:
        print("  " + m)
