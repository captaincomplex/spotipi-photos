#!/usr/bin/env python3
"""
logo_concepts.py -- five candidate marks for Spotipi Photos, side by side.

The brief: it should be readable as EITHER a photograph OR an album cover,
because the product is both. Each concept is defined once, in a unit square,
and rendered two ways:

    ICON   - a dot grid on a rounded panel. Says "matrix display" at a glance.
    PANEL  - solid shapes at 64x64. What the hardware would actually show,
             where the LEDs supply the dots themselves.

Concept 5 is a template rather than a fixed design: it takes one of your own
photographs and reduces it to the panel's resolution. Pass one in with --photo.

    python3 logo_concepts.py
    python3 logo_concepts.py --photo ~/Pictures/mine.jpg
"""
import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "concepts")

PANEL_BG = (0x14, 0x16, 0x1A)
SKY_OFF  = (0x25, 0x29, 0x31)
AMBER    = (0xF5, 0xA5, 0x24)
BLUE     = (0x2E, 0x8F, 0xC8)
TEAL     = (0x17, 0xA3, 0x98)
ROSE     = (0xE0, 0x5C, 0x6B)
CREAM    = (0xF2, 0xE4, 0xC8)
INK      = (0x1A, 0x1C, 0x21)
MUTED    = (0x6B, 0x70, 0x78)


# ============================ the five compositions ============================
# Each is colour_at(u, v) -> RGB or None, in a unit square with y running down.

def c1_sun_ridges(u, v, n=64):
    """1. SUN & RIDGES - a landscape photo whose sun is an LP.
    Delegates to make_logo.py so the concept and the real logo can't drift."""
    import make_logo as ml
    c = min(int(u * n), n - 1)
    r = min(int(v * n), n - 1)
    return ml.colour_at_cell(c, r, n)


def c2_aperture(u, v):
    """2. APERTURE / RECORD - a vinyl disc whose centre label is a six-bladed
    camera aperture, open onto a tiny sunset. Record from across the room,
    camera up close."""
    dx, dy = u - 0.5, v - 0.5
    d = math.hypot(dx, dy)
    if d > 0.45:
        return None
    if d > 0.26:                                     # the vinyl, with grooves
        return (0x55, 0x5C, 0x6A) if int(d * 60) % 2 else (0x33, 0x38, 0x42)
    # the label is a hexagon: an aperture six blades wide
    ang = math.atan2(dy, dx)
    sector = math.pi / 3
    a = (ang + math.pi / 6) % sector - sector / 2
    hex_r = 0.20 * math.cos(math.pi / 6) / math.cos(a)
    if d > hex_r:
        return AMBER                                 # the blades
    # inside the aperture: sky over sea, like a photo seen through a lens
    if dy < 0.02:
        return ROSE if dy > -0.06 else (0xF2, 0x8F, 0x5A)
    return BLUE


def c3_skyline(u, v):
    """3. SKYLINE / EQUALISER - bars rising from the bottom under a low sun.
    A city at dusk, or a graphic equaliser mid-song. The strongest dual read."""
    bars = [0.50, 0.30, 0.62, 0.40, 0.24]
    n = len(bars)
    i = min(int(u * n), n - 1)
    x_in = (u * n) % 1.0
    in_bar = 0.12 < x_in < 0.88 and v >= bars[i]
    if in_bar:
        f = (v - bars[i]) / max(1e-6, 1 - bars[i])
        if f < 0.16: return AMBER
        if f < 0.45: return ROSE
        return BLUE
    if math.hypot(u - 0.5, v - 0.30) <= 0.17:       # the sun, behind the city
        return (0x7A, 0x4A, 0x2E)
    return None


def c4_sleeve(u, v):
    """4. SLEEVE & DISC - a record sleeve with the disc sliding out, the sleeve
    face carrying a photographic gradient. The most literal 'album cover'."""
    d = math.hypot(u - 0.70, v - 0.50)                # the disc, right of centre
    disc = d <= 0.30
    if disc and u > 0.56:
        if d <= 0.042: return None                    # centre hole
        if d <= 0.10:  return AMBER                   # label
        if d >= 0.275: return (0x8A, 0x90, 0x9C)      # the rim catches the light
        return (0x4A, 0x50, 0x5C) if int(d * 46) % 2 else (0x30, 0x35, 0x3E)
    if 0.10 <= u <= 0.62 and 0.14 <= v <= 0.86:       # the sleeve
        t = (u - 0.10) / 0.52
        g = (v - 0.14) / 0.72
        return (int(46 + 190 * t), int(150 - 40 * g + 40 * t), int(200 - 90 * t))
    return None


def c5_photo(u, v, src=None):
    """5. YOUR PHOTOGRAPH - one of your own pictures, reduced to the panel's
    resolution. Not a drawing at all: the mark IS the product's output."""
    if src is None:
        # A clearly-synthetic stand-in, so nobody mistakes this for a real photo.
        sky = 0.58
        if v < sky:
            k = v / sky
            return (int(240 - 120 * k), int(160 + 30 * k), int(90 + 120 * k))
        h = 0.58 + 0.16 * math.exp(-((u - 0.38) ** 2) / 0.03)
        if v >= h: return (int(30 + 40 * v), int(70 + 30 * v), int(90 - 20 * v))
        return (int(250 - 40 * u), int(200 - 30 * u), int(120))
    w, hgt = src.size
    return src.getpixel((min(int(u * w), w - 1), min(int(v * hgt), hgt - 1)))


CONCEPTS = [
    ("1", "Sun & ridges", "A landscape whose sun is a record label", c1_sun_ridges),
    ("2", "Aperture / record", "A record whose label is a camera iris", c2_aperture),
    ("3", "Skyline / equaliser", "A city at dusk, or a level meter", c3_skyline),
    ("4", "Sleeve & disc", "The most literal album cover", c4_sleeve),
    ("5", "Your photograph", "Your own picture at panel resolution", c5_photo),
]


# ================================== renderers =================================
def render_icon(fn, size=256, grid=16):
    ss = 4
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(S * 0.22)
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=r, fill=PANEL_BG + (255,))
    pad = 0.085
    inner = S * (1 - 2 * pad)
    off = S * pad
    dot = (inner / grid) * 0.40
    for row in range(grid):
        for col in range(grid):
            u = (col + 0.5) / grid
            v = (row + 0.5) / grid
            c = (fn(u, v, grid) if fn is c1_sun_ridges else fn(u, v)) or SKY_OFF
            c = tuple(int(x) for x in c)
            cx, cy = off + u * inner, off + v * inner
            d.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=c + (255,))
    return img.resize((size, size), Image.LANCZOS)


def render_panel(fn, size=64, scale=1):
    """Native panel resolution: one pixel per LED, then blown up for viewing."""
    img = Image.new("RGB", (size, size), PANEL_BG)
    px = img.load()
    for y in range(size):
        for x in range(size):
            uu, vv = (x + 0.5) / size, (y + 0.5) / size
            c = fn(uu, vv, size) if fn is c1_sun_ridges else fn(uu, vv)
            if c:
                px[x, y] = tuple(int(v) for v in c)
    if scale > 1:
        img = img.resize((size * scale, size * scale), Image.NEAREST)
    return img


def contact_sheet(photo=None):
    ICON, PANEL, GAP, PAD = 190, 190, 34, 40
    head = 84
    W = PAD * 2 + len(CONCEPTS) * ICON + (len(CONCEPTS) - 1) * GAP
    H = head + ICON + 30 + PANEL + 70
    sheet = Image.new("RGB", (W, H), (250, 250, 248))
    d = ImageDraw.Draw(sheet)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 21)
    fn_ = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    fl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)

    d.text((PAD, 26), "Spotipi Photos — five directions", font=fb, fill=INK)
    d.text((PAD, 55), "Top: app icon.  Bottom: exactly what the 64x64 panel would show.",
           font=fl, fill=MUTED)

    def wrap(text, width):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fl) <= width:
                cur = t
            else:
                lines.append(cur); cur = w
        return lines + [cur] if cur else lines

    x = PAD
    for num, name, blurb, fn in CONCEPTS:
        f = (lambda u, v, _f=fn: _f(u, v, photo)) if num == "5" else fn
        icon = render_icon(f, ICON)
        sheet.paste(icon, (x, head), icon)                       # respect the rounded corners
        sheet.paste(render_panel(f, 64, PANEL // 64), (x, head + ICON + 30))
        yy = head + ICON + 30 + PANEL + 12
        d.text((x, yy), f"{num}.  {name}", font=fn_, fill=INK)
        yy += 19
        for line in wrap(blurb, ICON):
            d.text((x, yy), line, font=fl, fill=MUTED)
            yy += 15
        x += ICON + GAP
    return sheet


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", help="An image to drive concept 5.")
    a = ap.parse_args()

    src = None
    if a.photo:
        from PIL import ImageOps
        with Image.open(os.path.expanduser(a.photo)) as im:
            src = ImageOps.fit(ImageOps.exif_transpose(im).convert("RGB"),
                               (64, 64), Image.Resampling.LANCZOS)

    os.makedirs(OUT, exist_ok=True)
    for num, name, _, fn in CONCEPTS:
        f = (lambda u, v, _f=fn: _f(u, v, src)) if num == "5" else fn
        slug = name.lower().replace(" / ", "-").replace(" & ", "-").replace(" ", "-")
        render_icon(f, 512).save(os.path.join(OUT, f"{num}-{slug}-icon.png"))
        render_panel(f, 64).save(os.path.join(OUT, f"{num}-{slug}-panel64.png"))
    contact_sheet(src).save(os.path.join(OUT, "concepts.png"))
    print("Written to image/concepts/ —")
    for f in sorted(os.listdir(OUT)):
        print("  " + f)
