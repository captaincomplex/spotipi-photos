#!/usr/bin/env python3
"""
concepts_music.py -- the LP-sun logo, pushed towards music.

Two rows, compared side by side on the design canvas:

  Row A, Spotify green (no Spotify circle or waves -- but note Spotify's
  developer branding rules list Spotify Green itself as a brand element an
  app's logo "should not include"):
    A1  green label on the record          (photo 01)
    A2  green hills                        (photo 01)
    A3  green sun over a black night sky   (photo 01)
  Row B, music cues that are not Spotify's:
    B1  record grooves in the sun          (photo 01)
    B2  hills made of equaliser bars       (photo 01)
    B3  a tonearm resting on the sun       (photo 10, whole sun)

Same lattice rules as stylise_candidates.py: the disc centre snaps to a cell,
radius k+0.5 cells, the hole at least one cell. Everything is decided per
cell, so the 16-dot icon, the 64/32 panels and the artwork (a 256-cell
lattice, smoothed) all come from one function.

    python3 concepts_music.py
"""
import copy
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stylise_candidates as sc      # noqa: E402
import compare_finalists as cf       # noqa: E402

OUT = os.path.join(HERE, "concepts", "option1-music")
SPOTIFY_GREEN = (0x1D, 0xB9, 0x54)


def lum(c):
    return sc.lum(c)


# ------------------------------------------------------------ recolours ----
def green_hills(pal, sky):
    pal = pal.copy()
    ridge = sorted((i for i in range(len(pal)) if i not in sky), key=lambda i: -lum(pal[i]))
    for i, col in zip(ridge, [SPOTIFY_GREEN, (18, 122, 56), (10, 78, 36), (6, 50, 24)]):
        pal[i] = col
    return pal


def night(pal, sky):
    pal = pal.copy()
    skies = sorted(sky, key=lambda i: lum(pal[i]))
    for i, col in zip(skies, [(0x19, 0x14, 0x14), (0x1F, 0x1A, 0x1A), (0x26, 0x20, 0x20),
                              (0x2D, 0x26, 0x26), (0x33, 0x2C, 0x2C)]):
        pal[i] = col
    ridge = sorted((i for i in range(len(pal)) if i not in sky), key=lambda i: -lum(pal[i]))
    for i, col in zip(ridge, [(0x4A, 0x4A, 0x4E), (0x30, 0x30, 0x34), (0x22, 0x22, 0x26)]):
        pal[i] = col
    return pal


# ------------------------------------------------------------ disc effects -
def green_label(dist, rc, n, col):
    return SPOTIFY_GREEN if dist <= max(1.5 if n <= 16 else 0, 0.36 * rc) + 1e-9 else col


def grooves(dist, rc, n, col):
    if n >= 128:
        rings = (0.45, 0.62, 0.80)
    elif n >= 48:
        rings = (0.50, 0.78)
    elif n >= 24:
        rings = (0.62,)
    else:
        return col
    w = max(0.5, 0.03 * rc)
    if any(abs(dist - f * rc) < w for f in rings):
        return tuple(int(v * 0.80) for v in col)
    return col


# ------------------------------------------------------------ post effects -
def eq_bars(grid, labs, sky, n, disc):
    """Hills rebuilt as equaliser bars: each bar rises to the highest point of
    the ridge across its width; gaps show the sky (and the sun) behind."""
    horizon = []
    for c in range(n):
        rows = [r for r in range(n) if labs[r, c] not in sky]
        horizon.append(rows[0] if rows else n)
    base = n - max(1, round(0.12 * n))
    nb = 5 if n <= 16 else (8 if n <= 32 else 12)
    period = n / nb
    # An equaliser, not a fence: heights follow the ridge, then a fixed
    # up-and-down pattern exaggerates them.
    pattern = (0.70, 1.05, 0.85, 1.25, 0.95, 0.65, 1.15, 0.90, 1.10, 0.75, 1.20, 0.85)
    bar_of, top_of = {}, {}
    for b in range(nb):
        x0 = round(b * period + period * 0.2)
        x1 = min(n, max(x0 + 1, round(b * period + period * 0.8)))
        ridge_top = min(horizon[x0:x1])
        h = max(2, round((base - ridge_top) * pattern[b % len(pattern)]))
        for c in range(x0, x1):
            bar_of[c] = (x0, x1)
            top_of[c] = max(1, base - h)
    ridge_cols = [grid[r, c].copy() for c in range(n) for r in range(n) if labs[r, c] not in sky]
    darkest = min(ridge_cols, key=lum) if ridge_cols else np.array(sc.PANEL)
    src = grid.copy()
    for c in range(n):
        h = horizon[c]
        sky_col = src[max(0, h - 1), c]
        if c in bar_of:
            x0, x1 = bar_of[c]
            top = top_of[c]
            for r in range(min(top, h), base):          # sky/sun behind a short bar
                if r < top:
                    grid[r, c] = disc(r, c) or sky_col
            below = [src[r, cc] for cc in range(x0, x1) for r in range(horizon[cc], n)
                     if labs[r, cc] not in sky]
            bar_col = max(below, key=lum) if below else darkest
            for r in range(top, base):
                grid[r, c] = bar_col
        else:
            for r in range(h, base):
                grid[r, c] = disc(r, c) or sky_col
        for r in range(base, n):
            grid[r, c] = darkest


def tonearm(grid, labs, sky, n, disc, d):
    """A tonearm from a pivot top-right to a headshell on the sun."""
    P = (0.90 * n, 0.09 * n)
    S = ((d["cx"] + 0.52 * d["r"]) * n, (d["cy"] - 0.48 * d["r"]) * n)
    t = max(1.0, 0.016 * n)
    for r in range(n):
        for c in range(n):
            x, y = c + 0.5, r + 0.5
            vx, vy = S[0] - P[0], S[1] - P[1]
            u = max(0, min(1, ((x - P[0]) * vx + (y - P[1]) * vy) / (vx * vx + vy * vy)))
            dseg = math.hypot(x - (P[0] + u * vx), y - (P[1] + u * vy))
            if math.hypot(x - P[0], y - P[1]) <= max(1.0, 0.04 * n):
                grid[r, c] = (150, 150, 160)
            elif math.hypot(x - S[0], y - S[1]) <= max(0.8, 0.028 * n):
                grid[r, c] = (245, 245, 248)
            elif dseg <= t / 2 + 0.2:
                grid[r, c] = (220, 220, 228)


# ------------------------------------------------------------ renderer -----
CONCEPTS = [
    dict(key="A1-green-label", photo="01-orange-sunset-ridges-sea", row="A",
         title="Green label", note="The record gets a Spotify-green label.",
         disc_fx=green_label),
    dict(key="A2-green-hills", photo="01-orange-sunset-ridges-sea", row="A",
         title="Green hills", note="The ridges in Spotify green, the sunset kept.",
         recolour=green_hills),
    dict(key="A3-green-night", photo="01-orange-sunset-ridges-sea", row="A",
         title="Green sun, night sky", note="A Spotify-green sun setting over dark hills.",
         recolour=night, disc_colour=SPOTIFY_GREEN),
    dict(key="B1-grooves", photo="01-orange-sunset-ridges-sea", row="B",
         title="Record grooves", note="Groove rings in the sun, so it reads as an LP.",
         disc_fx=grooves),
    dict(key="B2-eq-hills", photo="01-orange-sunset-ridges-sea", row="B",
         title="Equaliser hills", note="The ridges rebuilt as equaliser bars.",
         post="eq"),
    dict(key="B3-tonearm", photo="10-pink-dusk-mountains", row="B",
         change=dict(cy=.36, behind=False),
         title="Tonearm", note="A tonearm resting on the whole sun.",
         post="arm"),
]


def load(spec):
    labels, pal0, discs = cf.build(spec["photo"])
    d = copy.deepcopy(discs[0])
    if spec.get("change"):
        d.update(spec["change"])
    if spec.get("disc_colour"):
        d["colour"] = spec["disc_colour"]
    sky = sc.open_sky(pal0, d.get("thr", 100))
    pal = spec["recolour"](pal0, sky) if spec.get("recolour") else pal0
    return labels, pal, d, sky


def render(spec, n):
    labels, pal, d, sky = spec["_data"]
    c0 = round(d["cx"] * n - 0.5); r0 = round(d["cy"] * n - 0.5)
    rc = max(1.5, round(d["r"] * n - 0.5) + 0.5)
    hole = max(0.5, d["r"] * sc.HOLE_FRAC * n)
    fx = spec.get("disc_fx")

    def disc(r, c):
        dist = math.hypot(c - c0, r - r0)
        if dist > rc + 1e-9:
            return None
        if dist <= hole + 1e-9:
            return sc.PANEL
        col = tuple(d["colour"])
        return fx(dist, rc, n, col) if fx else col

    grid = np.zeros((n, n, 3), np.uint8)
    labs = np.zeros((n, n), int)
    for r in range(n):
        for c in range(n):
            lab = sc.cell_label(labels, c, r, n)
            labs[r, c] = lab
            col = pal[lab]
            dc = disc(r, c)
            if dc is not None and (not d["behind"] or lab in sky):
                col = dc
            grid[r, c] = col
    if spec.get("post") == "eq":
        eq_bars(grid, labs, sky, n, disc)
    elif spec.get("post") == "arm":
        tonearm(grid, labs, sky, n, disc, d)
    return grid


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for spec in CONCEPTS:
        spec["_data"] = load(spec)
        art = Image.fromarray(render(spec, 256), "RGB").resize((512, 512), Image.LANCZOS)
        g16, g32, g64 = render(spec, 16), render(spec, 32), render(spec, 64)
        dot = sc.render_icon(g16, 512)
        p64 = Image.fromarray(g64, "RGB").resize((512, 512), Image.NEAREST)
        p32 = Image.fromarray(g32, "RGB").resize((512, 512), Image.NEAREST)
        k = spec["key"]
        art.save(os.path.join(OUT, f"{k}-artwork.png"))
        dot.save(os.path.join(OUT, f"{k}-icon16dot.png"))
        p64.save(os.path.join(OUT, f"{k}-panel64.png"))
        p32.save(os.path.join(OUT, f"{k}-panel32.png"))
        rows.append((k, art, dot, p64, p32))
        print("done", k)
    T, G = 180, 14
    sheet = Image.new("RGB", (4 * (T + G) + 200, len(rows) * (T + G) + 20), (250, 250, 248))
    dr = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    for j, (k, *ims) in enumerate(rows):
        y = 10 + j * (T + G)
        dr.text((10, y + T // 2), k, font=f, fill=(26, 28, 33))
        for i, im in enumerate(ims):
            im = im.resize((T, T), Image.LANCZOS if i < 2 else Image.NEAREST)
            sheet.paste(im, (190 + i * (T + G), y), im if im.mode == "RGBA" else None)
    sheet.save(os.path.join(OUT, "sheet.png"))
    print("sheet written")
