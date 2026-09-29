#!/usr/bin/env python3
"""
build_logo_assets.py -- the production logo: every file the project ships.

Two logos, both drawn from the owner's own photos in the option-1 style
(stylise_candidates.py does the drawing):

  sunset  -- photo 01, orange sunset; the sun setting behind the ridges.
             The DEFAULT: it is what config/default.png, the app icons,
             the favicon, the wordmark and the PDF guide use.
  dusk    -- photo 10, pink dusk; the whole sun just clear of the ridges.
             Chosen instead from the web control panel ("Logo" card).

For each logo this writes image/logos/<key>/:
    icon-512/256/128.png   16-dot app icon (the matrix look)
    icon-64/32/16.png      solid pixels -- dots turn to mush this small
    icon.svg, favicon.ico, wordmark.png, wordmark-dark.png
    panel-64.png, panel-32.png   what the LEDs show, one pixel per LED
    grid-16.json, grid-20.json   colours for the PDF guide (reportlab only)
and config/logos/<key>-64.png / -32.png for the display daemon.
The default's files are also copied to image/ and config/default*.png, where
README, the guide and older installs expect them.

    python3 build_logo_assets.py
"""
import copy
import json
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stylise_candidates as sc      # noqa: E402
import compare_finalists as cf       # noqa: E402

CONFIG = os.path.abspath(os.path.join(HERE, "..", "config"))
DEFAULT = "sunset"
LOGOS = {
    "sunset": dict(photo="01-orange-sunset-ridges-sea", change=None,
                   title="Orange sunset"),
    "dusk":   dict(photo="10-pink-dusk-mountains", change=dict(cy=.36, behind=False),
                   title="Pink dusk"),
}
INK = (0x1A, 0x1C, 0x21); MUTED = (0x6B, 0x70, 0x78)
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def hexof(c):
    return "#%02x%02x%02x" % tuple(int(v) for v in c)


def icon_svg(grid, size=512):
    n = grid.shape[0]; pad = .085
    inner = size * (1 - 2 * pad); off = size * pad; rad = inner / n * .40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
           f'viewBox="0 0 {size} {size}" role="img" aria-label="Spotipi Photos">',
           '  <title>Spotipi Photos</title>',
           f'  <rect width="{size}" height="{size}" rx="{size * .22:.1f}" fill="{hexof(sc.PANEL)}"/>']
    for r in range(n):
        for c in range(n):
            out.append(f'  <circle cx="{off + (c + .5) / n * inner:.2f}" '
                       f'cy="{off + (r + .5) / n * inner:.2f}" r="{rad:.2f}" '
                       f'fill="{hexof(grid[r, c])}"/>')
    out.append('</svg>')
    return "\n".join(out)


def wordmark(icon_big, path, width=1400, dark=False):
    """Same layout as the original make_logo wordmark, with this logo's icon."""
    h = width // 4
    bg = sc.PANEL if dark else (0xFA, 0xFA, 0xF8)
    fg = (0xF2, 0xF3, 0xF5) if dark else INK
    sub = (0x9A, 0xA0, 0xA8) if dark else MUTED
    img = Image.new("RGB", (width, h), bg)
    icon_px = int(h * .70)
    ic = icon_big.resize((icon_px, icon_px), Image.LANCZOS)
    x = int(h * .22)
    img.paste(ic, (x, (h - icon_px) // 2), ic)
    d = ImageDraw.Draw(img)
    tx = x + icon_px + int(h * .24)
    avail = width - tx - int(h * .22)
    fs = int(h * .36)
    while fs > 8:
        f1 = ImageFont.truetype(FONT_B, fs); f2 = ImageFont.truetype(FONT_R, fs)
        w1 = d.textlength("Spotipi", font=f1); w2 = d.textlength(" Photos", font=f2)
        if w1 + w2 <= avail:
            break
        fs -= 2
    ty = (h - (fs * 1.30 + int(h * .155))) / 2
    d.text((tx, ty), "Spotipi", font=f1, fill=fg)
    d.text((tx + w1, ty), " Photos", font=f2, fill=sub)
    d.text((tx + 2, ty + fs * 1.30), "PHOTOS AND ALBUM ART ON AN LED MATRIX",
           font=ImageFont.truetype(FONT_R, int(h * .105)), fill=sub)
    img.save(path)


def build(key, spec):
    out = os.path.join(HERE, "logos", key)
    os.makedirs(out, exist_ok=True)
    labels, pal, discs = cf.build(spec["photo"])
    discs = copy.deepcopy(discs)
    if spec["change"]:
        discs[0].update(spec["change"])
    grid = lambda n: sc.render_grid(labels, pal, discs, None, n)   # noqa: E731
    g16 = grid(16)
    for px in (512, 256, 128):
        sc.render_icon(g16, px).save(os.path.join(out, f"icon-{px}.png"))
    small = {px: cf.solid_icon(labels, pal, discs, px) for px in (64, 48, 32, 16)}
    for px in (64, 32, 16):
        small[px].save(os.path.join(out, f"icon-{px}.png"))
    small[64].save(os.path.join(out, "favicon.ico"),
                   sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
                   append_images=[small[16], small[32], small[48]])
    open(os.path.join(out, "icon.svg"), "w").write(icon_svg(g16))
    big = sc.render_icon(g16, 1024)
    wordmark(big, os.path.join(out, "wordmark.png"))
    wordmark(big, os.path.join(out, "wordmark-dark.png"), dark=True)
    os.makedirs(os.path.join(CONFIG, "logos"), exist_ok=True)
    for n in (64, 32):
        p = Image.fromarray(grid(n), "RGB")
        p.save(os.path.join(out, f"panel-{n}.png"))
        p.save(os.path.join(CONFIG, "logos", f"{key}-{n}.png"))
    Image.fromarray(grid(64), "RGB").resize((256, 256), Image.NEAREST).save(
        os.path.join(out, "panel-preview.png"))
    for n in (16, 20):
        json.dump([[hexof(c) for c in row] for row in grid(n)],
                  open(os.path.join(out, f"grid-{n}.json"), "w"))
    return out


if __name__ == "__main__":
    for key, spec in LOGOS.items():
        print(key, "->", os.path.relpath(build(key, spec), HERE))
    src = os.path.join(HERE, "logos", DEFAULT)
    for f in ("icon-512.png", "icon-256.png", "icon-128.png", "icon-64.png", "icon-32.png",
              "icon-16.png", "icon.svg", "favicon.ico", "wordmark.png", "wordmark-dark.png"):
        shutil.copy(os.path.join(src, f), os.path.join(HERE, f))
    shutil.copy(os.path.join(src, "panel-preview.png"), os.path.join(HERE, "panel-splash-preview.png"))
    shutil.copy(os.path.join(src, "panel-64.png"), os.path.join(CONFIG, "default.png"))
    shutil.copy(os.path.join(src, "panel-32.png"), os.path.join(CONFIG, "default-32.png"))
    print("default (%s) copied to image/ and config/default*.png" % DEFAULT)
