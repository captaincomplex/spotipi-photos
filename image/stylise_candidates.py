#!/usr/bin/env python3
"""
stylise_candidates.py -- redraw photos in the option-1 house style.

Option 1 is flat colour: a few solid layers (sky, hills, sea) and a round
sun that doubles as an LP, with a stylised centre hole. This takes a real
photograph and does the same to it:

  1. crop to a square around the subject;
  2. blur away texture (waves, grain, cloud detail) so only the big shapes remain;
  3. reduce to a handful of flat colours (k-means), then clean up speckle;
  4. add the LP disc -- behind the landscape where it is a sun or moon,
     in front where it is an engine;
  5. render it three ways, exactly as make_logo.py does for the plain mark:
       flat-512  -- the smooth artwork
       panel64   -- one pixel per LED, disc snapped to the grid
       icon      -- the 16-dot app icon

Where a disc is added that is not in the photo, the PARAMS entry says so.

    python3 stylise_candidates.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "logo-candidates"))
OUT = os.path.join(HERE, "concepts", "option1-from-photos")

PANEL = (0x14, 0x16, 0x1A)
SKY_OFF = (0x25, 0x29, 0x31)
HOLE_FRAC = 0.11            # same stylised LP hole as the live logo
WORK = 256                  # working resolution for the flat artwork

# crop: (left, top, size) as fractions of the SHORT side, from the image's top-left;
#       None = centre crop.
# discs: cx, cy, r in the cropped square (0..1, y down); colour; behind = sits
#        behind the landscape (sun/moon) rather than on top (engine).
# flatten: polygons (unit coords) repainted with one flat colour -- used to
#          remove the easyJet wordmark.
PARAMS = {
    "01-orange-sunset-ridges-sea": dict(k=6, discs=[
        dict(cx=.47, cy=.52, r=.15, colour=(255, 200, 90), behind=True, thr=115)]),
    "02-a320-nose-on-stand": dict(k=7, discs=[
        dict(cx=.205, cy=.565, r=.07, colour=(232, 104, 42), behind=False),
        dict(cx=.795, cy=.565, r=.07, colour=(232, 104, 42), behind=False)],
        note="the two engines are the records"),
    "03-aircraft-silhouette-amber": dict(k=5, keep_dark=70, discs=[
        dict(cx=.50, cy=.56, r=.17, colour=(255, 214, 120), behind=True, thr=90)],
        note="sun added behind the aircraft"),
    "04-tail-at-dusk": dict(k=7, discs=[
        dict(cx=.36, cy=.66, r=.12, colour=(255, 200, 80), behind=True, thr=60)],
        flatten=[dict(poly=[(.60, .36), (.74, .33), (1.0, .70), (1.0, .98), (.80, .98)],
                      colour=(206, 86, 28))],
        note="sun placed on the horizon glow; wordmark painted out"),
    "05-nose-and-engine": dict(k=7, discs=[
        dict(cx=.86, cy=.73, r=.12, colour=(232, 104, 42), behind=False)],
        note="the engine is the record"),
    "06-sunrise-from-flight-deck": dict(k=6, discs=[
        dict(cx=.36, cy=.42, r=.08, colour=(255, 120, 60), behind=True, thr=60)],
        note="the real sun, enlarged"),
    "07-aurora": dict(k=6, discs=[
        dict(cx=.80, cy=.20, r=.09, colour=(236, 232, 214), behind=False)],
        note="moon added -- there isn't one in the photo"),
    "08-tail-blue-sky": dict(k=6, discs=[
        dict(cx=.74, cy=.27, r=.13, colour=(245, 165, 36), behind=True, thr=60)],
        flatten=[dict(poly=[(0, 0), (.30, 0), (.13, .56), (0, .62)],
                      colour=(222, 88, 30))],
        note="sun added; wordmark painted out"),
    "09-golden-glow-single-peak": dict(k=6, discs=[
        dict(cx=.52, cy=.62, r=.16, colour=(255, 222, 140), behind=True, thr=80)],
        note="the glow made into a sun, setting behind the peak"),
    "10-pink-dusk-mountains": dict(k=6, discs=[
        dict(cx=.62, cy=.49, r=.14, colour=(255, 186, 120), behind=True, thr=140)],
        note="sun added, setting behind the ridges"),
}


# ------------------------------------------------------------ flatten ------
def kmeans(pixels, k, iters=12, seed=1):
    rng = np.random.default_rng(seed)
    centres = pixels[rng.choice(len(pixels), k, replace=False)].astype(float)
    for _ in range(iters):
        d = ((pixels[:, None, :] - centres[None, :, :]) ** 2).sum(-1)
        lab = d.argmin(1)
        for j in range(k):
            m = pixels[lab == j]
            if len(m):
                centres[j] = m.mean(0)
    return centres


def flatten(img, k, keep_dark=None):
    """Photo -> a few flat colour regions, index map + palette, at WORK x WORK.

    keep_dark: a luminance threshold. Pixels darker than it in the ORIGINAL are
    forced into the darkest colour afterwards, thickened by one pixel -- so a
    small silhouette (an aircraft against the sky) survives the blur that is
    there to remove texture.
    """
    im = img.resize((WORK, WORK), Image.LANCZOS)
    dark = None
    if keep_dark is not None:
        g = np.asarray(im.convert("L"))
        dm = Image.fromarray(((g < keep_dark) * 255).astype(np.uint8))
        dark = np.asarray(dm.filter(ImageFilter.MaxFilter(3))) > 0
    im = ImageEnhance.Color(im).enhance(1.25)            # a touch more punch for LEDs
    soft = im.filter(ImageFilter.GaussianBlur(3))         # lose waves and grain
    arr = np.asarray(soft).reshape(-1, 3).astype(float)
    sample = arr[:: max(1, len(arr) // 6000)]
    pal = kmeans(sample, k)
    lab = ((arr[:, None, :] - pal[None]) ** 2).sum(-1).argmin(1).reshape(WORK, WORK)
    # clean speckle: majority filter on the label map
    li = Image.fromarray(lab.astype(np.uint8))
    for _ in range(3):
        li = li.filter(ImageFilter.ModeFilter(7))
    labels = np.asarray(li).copy()
    if dark is not None:
        darkest = int(np.argmin([0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in pal]))
        labels[dark] = darkest
    return labels, np.clip(pal, 0, 255).astype(np.uint8)


def paint(labels, pal):
    return Image.fromarray(pal[labels], "RGB")


# ------------------------------------------------------------ geometry -----
def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def open_sky(pal, thr):
    """Colour regions a 'behind' disc may show through: anything lighter than
    the photo's foreground. Hills, ground and silhouettes are the dark regions,
    so a setting sun is cut off by them -- and only by them. (First attempt used
    'colours in the top strip of the frame', which wrongly hid the sun behind
    the lower bands of a graded sky.)"""
    return {i for i, c in enumerate(pal) if lum(c) >= thr}


def apply_flatten(labels, pal, polys):
    """Paint polygons flat (wordmark removal). Returns new labels + palette."""
    pal = list(map(tuple, pal))
    labels = labels.copy()
    for f in polys:
        pal.append(tuple(f["colour"]))
        idx = len(pal) - 1
        mask = Image.new("L", (WORK, WORK), 0)
        ImageDraw.Draw(mask).polygon([(x * WORK, y * WORK) for x, y in f["poly"]], fill=255)
        labels[np.asarray(mask) > 0] = idx
    return labels, np.array(pal, dtype=np.uint8)


def lattice_disc_kind(c, r, n, d):
    """Same rule as make_logo.lattice_sun: centre snapped to a cell, hole >= 1 cell."""
    c0 = round(d["cx"] * n - 0.5); r0 = round(d["cy"] * n - 0.5)
    dist = math.hypot(c - c0, r - r0)
    if dist <= max(0.5, d["r"] * HOLE_FRAC * n) + 1e-9:
        return "hole"
    # radius snapped to k + 0.5 cells: the classic pixel-circle size. A radius
    # just under a whole number (8.96, say) gives a flat 9-cell top row.
    rc = max(1.5, round(d["r"] * n - 0.5) + 0.5)
    if dist <= rc + 1e-9:
        return "disc"
    return None


# ------------------------------------------------------------ renders ------
def cell_label(labels, c, r, n):
    """Majority colour region inside one output cell -- keeps colours flat."""
    s = WORK / n
    blk = labels[int(r * s):int((r + 1) * s), int(c * s):int((c + 1) * s)].ravel()
    return np.bincount(blk).argmax()


def render_grid(labels, pal, discs, sky, n):
    """n x n raster, one entry per LED/dot, with lattice discs."""
    grid = np.zeros((n, n, 3), np.uint8)
    for r in range(n):
        for c in range(n):
            lab = cell_label(labels, c, r, n)
            col = pal[lab]
            for d in discs:
                kind = lattice_disc_kind(c, r, n, d)
                if kind is None:
                    continue
                if d["behind"] and lab not in open_sky(pal, d.get("thr", 100)):
                    continue                          # hidden by the landscape
                col = PANEL if kind == "hole" else d["colour"]
            grid[r, c] = col
    return grid


def render_flat512(labels, pal, discs, sky, size=512):
    base = paint(labels, pal).resize((size, size), Image.NEAREST)
    base = base.filter(ImageFilter.ModeFilter(5))
    ss = 4
    for d in discs:
        layer = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
        dr = ImageDraw.Draw(layer)
        cx, cy, R = d["cx"] * size * ss, d["cy"] * size * ss, d["r"] * size * ss
        h = R * HOLE_FRAC
        dr.ellipse([cx - R, cy - R, cx + R, cy + R], fill=tuple(d["colour"]) + (255,))
        dr.ellipse([cx - h, cy - h, cx + h, cy + h], fill=PANEL + (255,))
        layer = layer.resize((size, size), Image.LANCZOS)
        if d["behind"]:
            m = np.isin(np.asarray(Image.fromarray(labels.astype(np.uint8))
                                   .resize((size, size), Image.NEAREST)),
                        list(open_sky(pal, d.get("thr", 100))))
            a = np.asarray(layer).copy()
            a[..., 3] = (a[..., 3] * m).astype(np.uint8)
            layer = Image.fromarray(a, "RGBA")
        base.paste(layer, (0, 0), layer)
    return base


def render_icon(grid, size=256):
    n = grid.shape[0]
    ss = 4; S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * .22), fill=PANEL + (255,))
    pad = .085; inner = S * (1 - 2 * pad); off = S * pad; rad = inner / n * .40
    for r in range(n):
        for c in range(n):
            cx, cy = off + (c + .5) / n * inner, off + (r + .5) / n * inner
            d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad],
                      fill=tuple(int(v) for v in grid[r, c]) + (255,))
    return img.resize((size, size), Image.LANCZOS)


# --------------------------------------------------------------- main ------
def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    for name, p in PARAMS.items():
        src = os.path.join(SRC, name + ".jpeg")
        img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        img = ImageOps.fit(img, (min(img.size),) * 2, Image.LANCZOS)
        labels, pal = flatten(img, p["k"], p.get("keep_dark"))
        sky = None
        if p.get("flatten"):
            labels, pal = apply_flatten(labels, pal, p["flatten"])
        discs = p["discs"]
        flat = render_flat512(labels, pal, discs, sky)
        g64 = render_grid(labels, pal, discs, sky, 64)
        g16 = render_grid(labels, pal, discs, sky, 16)
        panel = Image.fromarray(g64, "RGB")
        flat.save(os.path.join(OUT, f"{name}-flat512.png"))
        panel.save(os.path.join(OUT, f"{name}-panel64.png"))
        render_icon(g16).save(os.path.join(OUT, f"{name}-icon.png"))
        results.append((name, img, flat, panel, render_icon(g16), p.get("note", "")))
    return results


if __name__ == "__main__":
    res = main()
    # comparison sheet: photo | flat | panel | icon, one row per candidate
    from PIL import ImageFont
    T, G = 170, 14
    W = 4 * T + 5 * G + 250; H = len(res) * (T + G) + 70
    sheet = Image.new("RGB", (W, H), (250, 250, 248)); d = ImageDraw.Draw(sheet)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    fs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    for i, h in enumerate(["Your photo", "Option-1 style", "64x64 panel", "App icon"]):
        d.text((G + i * (T + G), 20), h, font=fb, fill=(26, 28, 33))
    for j, (name, img, flat, panel, icon, note) in enumerate(res):
        y = 44 + j * (T + G)
        sheet.paste(img.resize((T, T), Image.LANCZOS), (G, y))
        sheet.paste(flat.resize((T, T), Image.LANCZOS), (G + (T + G), y))
        sheet.paste(panel.resize((T, T), Image.NEAREST), (G + 2 * (T + G), y))
        sheet.paste(icon.resize((T, T), Image.LANCZOS), (G + 3 * (T + G), y), icon.resize((T, T), Image.LANCZOS))
        x = G + 4 * (T + G)
        d.text((x, y + 8), name, font=fb, fill=(26, 28, 33))
        d.text((x, y + 28), note, font=fs, fill=(107, 112, 120))
    sheet.save(os.path.join(OUT, "comparison.png"))
    print("done:", len(res), "candidates ->", OUT)
