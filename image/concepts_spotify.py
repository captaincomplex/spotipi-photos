#!/usr/bin/env python3
"""
concepts_spotify.py -- the sunset logo in Spotify's colours, with the three
curved waves from Spotify's icon.

Concept round only. Spotify's developer branding rules say an app's logo
should not include Spotify Green, the circle or the waves; the owner has
chosen to explore it anyway (free, open-source project).

  S1  Spotify sun setting   -- green sun with black waves, setting behind
                               the ridges of photo 01; orange sunset kept
  S2  Spotify sun, night    -- the same sun whole, over photo 01's ridges,
                               the sky turned to a dark green-glow sunset
  S3  Record eclipse        -- a black record for a sun, its waves cut out
                               to show a Spotify-green sunset behind it
  S4  Wave hills            -- the waves become the hills; a green LP sun
                               setting behind them

Everything is decided per cell on the lattice, as in stylise_candidates.py
(disc centre snapped to a cell, radius k+0.5, waves at least one cell thick
with at least one cell between them), so the 16-dot icon, the 32/64 panels
and the artwork (a 256-cell lattice, smoothed) come from one function.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stylise_candidates as sc      # noqa: E402
import compare_finalists as cf       # noqa: E402

OUT = os.path.join(HERE, "concepts", "option1-spotify")
GREEN = (0x1D, 0xB9, 0x54)           # Spotify Green
GREEN_HI = (0x1E, 0xD7, 0x60)
BLACK = (0x12, 0x12, 0x12)
PHOTO = "01-orange-sunset-ridges-sea"


# ------------------------------------------------------------ geometry -----
def disc_geom(cx, cy, r, n):
    c0 = round(cx * n - 0.5); r0 = round(cy * n - 0.5)
    R = max(1.5, round(r * n - 0.5) + 0.5)
    return c0, r0, R


def arc_hit(dx, dy, half_w, drop, thick):
    """Cell on an arc of a circle: chord 2*half_w wide, ends `drop` below the
    crown, `thick` cells thick. A ring test (not a curve y=f(x)) gives the
    clean stepped arc pixel art uses, with no breaks at any size."""
    if abs(dx) > half_w + 0.5:
        return False
    rad = (half_w ** 2 + drop ** 2) / (2 * drop)
    return abs(math.hypot(dx, dy - rad) - rad) <= thick / 2 + 1e-9


def on_wave(dx, dy, R, n):
    """True if cell offset (dx, dy) from the disc centre lies on one of the
    three waves: top longest and thickest, each curving down at the ends."""
    gap = max(0.30 * R, 2.0)
    for off, wid, th in ((-gap, .64, .15), (0.0, .53, .12), (gap, .42, .10)):
        w = wid * R
        if arc_hit(dx, dy - off, w, max(1.0, 0.20 * R), max(1.0, th * R)):
            return True
    return False


def bands(v, stops):
    """Flat-colour sky: stops = [(v_from, colour), ...] top to bottom."""
    col = stops[0][1]
    for v0, c in stops:
        if v >= v0:
            col = c
    return col


# ------------------------------------------------------------ scenes -------
LABELS, PAL0, DISCS = cf.build(PHOTO)
SKY = sc.open_sky(PAL0, DISCS[0]["thr"])
RIDGE = sorted((i for i in range(len(PAL0)) if i not in SKY), key=lambda i: -sc.lum(PAL0[i]))
SKY_BY_ROW = sorted(SKY, key=lambda i: np.argwhere(LABELS == i)[:, 0].mean())


def photo_scene(sky_map, ridge_cols):
    pal = PAL0.copy()
    for i, col in zip(RIDGE, ridge_cols):
        pal[i] = col
    if sky_map:
        for i, col in zip(SKY_BY_ROW, sky_map):
            pal[i] = col
    return pal


def render(concept, n):
    grid = np.zeros((n, n, 3), np.uint8)
    kind = concept["kind"]
    if kind in ("S1", "S2", "S3"):
        pal = concept["pal"]
        cx, cy, r = concept["sun"]
        c0, r0, R = disc_geom(cx, cy, r, n)
        for row in range(n):
            for col in range(n):
                lab = sc.cell_label(LABELS, col, row, n)
                base = tuple(pal[lab])
                if kind == "S3" and lab in SKY:
                    base = bands((row + .5) / n, concept["sky"])
                out = base
                dx, dy = col - c0, row - r0
                inside = math.hypot(dx, dy) <= R + 1e-9
                visible = lab in SKY or not concept["behind"]
                if inside and visible:
                    if kind == "S3":            # black record, waves cut through to the sky
                        out = base if on_wave(dx, dy, R, n) else BLACK
                    else:                       # Spotify-green sun, black waves
                        out = BLACK if on_wave(dx, dy, R, n) else GREEN
                grid[row, col] = out
        return grid
    # S4: synthetic -- dark sky with a green glow, LP sun, three wave hills
    cx, cy, r = .50, .50, .22
    c0, r0, R = disc_geom(cx, cy, r, n)
    hole = max(0.5, r * sc.HOLE_FRAC * n)
    sky = [(0, (0x10, 0x10, 0x10)), (.22, (0x0F, 0x1C, 0x14)), (.36, (0x10, 0x2C, 0x1B)),
           (.47, (0x12, 0x40, 0x24))]
    hills = [(.60, .95, .10, GREEN), (.72, .80, .08, (0x17, 0x8F, 0x44)),
             (.84, .66, .07, (0x11, 0x63, 0x31))]
    for row in range(n):
        for col in range(n):
            u, v = (col + .5) / n, (row + .5) / n
            out = bands(v, sky)
            ground = .56 + .10 * (u - .5) ** 2
            dx, dy = col - c0, row - r0
            d = math.hypot(dx, dy)
            if v < ground and d <= R + 1e-9:
                out = sc.PANEL if d <= hole + 1e-9 else GREEN
            if v >= ground:
                out = BLACK
                for y0, wid, th, hc in hills:
                    if arc_hit(col + .5 - n / 2, row + .5 - y0 * n, wid / 2 * n,
                               max(1.0, .10 * n), max(1.0, th * .5 * n)):
                        out = hc
            grid[row, col] = out
    return grid


CONCEPTS = [
    dict(key="S1-spotify-sun-setting", kind="S1", behind=True, sun=(.50, .50, .25),
         pal=photo_scene(None, [(0x20, 0x20, 0x20), (0x0E, 0x0E, 0x0E)]),
         title="Spotify sun setting",
         note="A Spotify-green sun with its waves, setting behind your ridges; the orange sunset kept."),
    dict(key="S2-spotify-sun-night", kind="S2", behind=False, sun=(.50, .30, .26),
         pal=photo_scene([(0x10, 0x10, 0x10), (0x0E, 0x22, 0x16), (0x10, 0x3A, 0x20),
                          (0x13, 0x55, 0x2B), (0x16, 0x70, 0x36)],
                         [(0x1C, 0x1C, 0x1C), (0x0A, 0x0A, 0x0A)]),
         title="Spotify sun over a green dusk",
         note="The whole sun up, over your ridges; the sky turned to a dark, green-glow sunset."),
    dict(key="S3-record-eclipse", kind="S3", behind=True, sun=(.50, .47, .25),
         pal=photo_scene(None, [(0x0B, 0x3D, 0x1F), (0x07, 0x26, 0x13)]),
         sky=[(0, (0x0D, 0x4F, 0x28)), (.18, (0x12, 0x73, 0x37)), (.32, (0x17, 0x96, 0x47)),
              (.44, GREEN), (.52, GREEN_HI)],
         title="Record eclipse",
         note="A black record as the sun, its waves cut out to show a Spotify-green sunset."),
    dict(key="S4-wave-hills", kind="S4",
         title="Wave hills",
         note="The three waves become the hills; a green LP sun setting behind them."),
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for cpt in CONCEPTS:
        art = Image.fromarray(render(cpt, 256), "RGB").resize((512, 512), Image.LANCZOS)
        g16, g32, g64 = render(cpt, 16), render(cpt, 32), render(cpt, 64)
        dot = sc.render_icon(g16, 512)
        p64 = Image.fromarray(g64, "RGB").resize((512, 512), Image.NEAREST)
        p32 = Image.fromarray(g32, "RGB").resize((512, 512), Image.NEAREST)
        k = cpt["key"]
        art.save(os.path.join(OUT, f"{k}-artwork.png"))
        dot.save(os.path.join(OUT, f"{k}-icon16dot.png"))
        p64.save(os.path.join(OUT, f"{k}-panel64.png"))
        p32.save(os.path.join(OUT, f"{k}-panel32.png"))
        rows.append((k, art, dot, p64, p32))
    T, G = 200, 14
    sheet = Image.new("RGB", (4 * (T + G) + 230, len(rows) * (T + G) + 20), (250, 250, 248))
    dr = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    for j, (k, *ims) in enumerate(rows):
        y = 10 + j * (T + G)
        dr.text((10, y + T // 2), k, font=f, fill=(26, 28, 33))
        for i, im in enumerate(ims):
            im = im.resize((T, T), Image.LANCZOS if i < 2 else Image.NEAREST)
            sheet.paste(im, (220 + i * (T + G), y), im if im.mode == "RGBA" else None)
    sheet.save(os.path.join(OUT, "sheet.png"))
    print("ok")
