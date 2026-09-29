"""01 vs 10 at every size the logo is actually used."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stylise_candidates as sc

FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
FS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
FW = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def build(name):
    p = sc.PARAMS[name]
    img = ImageOps.exif_transpose(Image.open(os.path.join(sc.SRC, name + ".jpeg"))).convert("RGB")
    img = ImageOps.fit(img, (min(img.size),) * 2, Image.LANCZOS)
    labels, pal = sc.flatten(img, p["k"], p.get("keep_dark"))
    if p.get("flatten"):
        labels, pal = sc.apply_flatten(labels, pal, p["flatten"])
    return labels, pal, p["discs"]

def solid_icon(labels, pal, discs, px):
    """Small app icon: one pixel per cell on the lattice, rounded corners."""
    g = sc.render_grid(labels, pal, discs, None, px)
    im = Image.fromarray(g, "RGB").convert("RGBA")
    m = Image.new("L", (px * 8, px * 8), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, px * 8 - 1, px * 8 - 1], radius=int(px * 8 * .22), fill=255)
    im.putalpha(m.resize((px, px), Image.LANCZOS))
    return im

def panel(labels, pal, discs, n, show=192):
    g = sc.render_grid(labels, pal, discs, None, n)
    im = Image.fromarray(g, "RGB").resize((show, show), Image.NEAREST)
    bez = Image.new("RGB", (show + 16, show + 16), (8, 8, 10)); bez.paste(im, (8, 8))
    return bez

def wordmark(icon):
    W, H = 460, 110
    wm = Image.new("RGB", (W, H), (250, 250, 248)); d = ImageDraw.Draw(wm)
    ic = icon.resize((80, 80), Image.LANCZOS); wm.paste(ic, (15, 15), ic)
    f1 = ImageFont.truetype(FW, 38); f2 = ImageFont.truetype(FR, 38)
    d.text((112, 28), "Spotipi", font=f1, fill=(26, 28, 33))
    w = d.textlength("Spotipi", font=f1)
    d.text((112 + w, 28), " Photos", font=f2, fill=(107, 112, 120))
    return wm

if __name__ == "__main__":
    cands = [("01-orange-sunset-ridges-sea", "01  Orange sunset"), ("10-pink-dusk-mountains", "10  Pink dusk")]
    COLW = 520
    sheet = Image.new("RGB", (40 + 2 * COLW, 1260), (250, 250, 248)); d = ImageDraw.Draw(sheet)
    d.text((20, 14), "Finalists at real sizes", font=ImageFont.truetype(FW, 20), fill=(26, 28, 33))
    for i, (name, title) in enumerate(cands):
        labels, pal, discs = build(name)
        x0 = 20 + i * COLW; y = 56
        d.text((x0, y), title, font=FB, fill=(26, 28, 33)); y += 24
        flat = sc.render_flat512(labels, pal, discs, None).resize((220, 220), Image.LANCZOS)
        sheet.paste(flat, (x0, y))
        dot = sc.render_icon(sc.render_grid(labels, pal, discs, None, 16), 220)
        sheet.paste(dot, (x0 + 250, y), dot)
        d.text((x0, y + 226), "artwork", font=FS, fill=(107, 112, 120))
        d.text((x0 + 250, y + 226), "app icon (16-dot)", font=FS, fill=(107, 112, 120))
        y += 256
        d.text((x0, y), "Small icons -- actual size, then 4x", font=FB, fill=(26, 28, 33)); y += 22
        xx = x0
        for px in (64, 32, 16):
            ic = solid_icon(labels, pal, discs, px)
            sheet.paste(ic, (xx, y + (64 - px)), ic)
            big = ic.resize((px * 4 if px < 64 else 128,) * 2, Image.NEAREST)
            sheet.paste(big, (xx, y + 74), big)
            d.text((xx, y + 74 + big.height + 4), f"{px}px", font=FS, fill=(107, 112, 120))
            xx += max(big.width, 64) + 22
        y += 74 + 128 + 30
        d.text((x0, y), "On the panel", font=FB, fill=(26, 28, 33)); y += 22
        sheet.paste(panel(labels, pal, discs, 64), (x0, y))
        sheet.paste(panel(labels, pal, discs, 32), (x0 + 240, y))
        d.text((x0, y + 212), "64x64", font=FS, fill=(107, 112, 120))
        d.text((x0 + 240, y + 212), "32x32", font=FS, fill=(107, 112, 120))
        y += 236
        sheet.paste(wordmark(solid_icon(labels, pal, discs, 64)), (x0, y))
        d.text((x0, y + 114), "wordmark", font=FS, fill=(107, 112, 120))
    sheet.save(os.path.join(sc.OUT, "finalists-01-vs-10.png")); print("written")
