"""01 and 10: sun setting behind the hills vs the whole sun up in the sky.

For each finalist, three placements of the same LP-sun:
  set   -- current: sitting on the ridges, lower part hidden
  low   -- whole disc just clear of the ridges
  high  -- whole disc well up in the sky
Horizon heights were measured from the flattened artwork (first non-sky
row per column), so 'low' leaves a small band of sky under the disc.

Writes finalists-fullsun.png plus one set of assets per variant into
concepts/option1-fullsun/ (artwork, 16-dot icon, 64/32 panels, 32px icon).
"""
import os, sys, copy
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stylise_candidates as sc
import compare_finalists as cf

OUT = os.path.join(sc.HERE, "concepts", "option1-fullsun")
VARIANTS = {
    "01-orange-sunset-ridges-sea": [
        ("set",  None),
        ("low",  dict(cy=.37, behind=False)),
        ("high", dict(cy=.27, behind=False)),
    ],
    "10-pink-dusk-mountains": [
        ("set",  None),
        ("low",  dict(cy=.36, behind=False)),
        ("high", dict(cy=.26, behind=False)),
    ],
}

def variant(discs, change):
    d = copy.deepcopy(discs)
    if change:
        d[0].update(change)
    return d

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    FB = ImageFont.truetype(cf.FW, 14); FS = ImageFont.truetype(cf.FR, 11)
    T = 200; G = 18
    cols = ["artwork", "app icon (16-dot)", "64x64 panel", "32x32 panel", "32px icon (4x)"]
    rows = [(n, v, c) for n, vs in VARIANTS.items() for v, c in vs]
    sheet = Image.new("RGB", (G + len(cols) * (T + G) + 60, 70 + len(rows) * (T + 40)), (250, 250, 248))
    d = ImageDraw.Draw(sheet)
    d.text((G, 14), "Sun setting vs sun in full", font=ImageFont.truetype(cf.FW, 20), fill=(26, 28, 33))
    for i, c in enumerate(cols):
        d.text((G + 60 + i * (T + G), 44), c, font=FB, fill=(26, 28, 33))
    cache = {}
    for j, (name, vname, change) in enumerate(rows):
        if name not in cache:
            cache[name] = cf.build(name)
        labels, pal, discs = cache[name]
        ds = variant(discs, change)
        tag = f"{name[:2]}-{vname}"
        flat = sc.render_flat512(labels, pal, ds, None)
        dot = sc.render_icon(sc.render_grid(labels, pal, ds, None, 16), 512)
        p64 = Image.fromarray(sc.render_grid(labels, pal, ds, None, 64), "RGB")
        p32 = Image.fromarray(sc.render_grid(labels, pal, ds, None, 32), "RGB")
        i32 = cf.solid_icon(labels, pal, ds, 32)
        flat.save(os.path.join(OUT, f"{tag}-artwork.png"))
        dot.save(os.path.join(OUT, f"{tag}-icon16dot.png"))
        p64.resize((512, 512), Image.NEAREST).save(os.path.join(OUT, f"{tag}-panel64.png"))
        p32.resize((512, 512), Image.NEAREST).save(os.path.join(OUT, f"{tag}-panel32.png"))
        i32.save(os.path.join(OUT, f"{tag}-icon32.png"))
        y = 70 + j * (T + 40)
        d.text((G, y + T // 2 - 8), tag, font=FB, fill=(26, 28, 33))
        x = G + 60
        for im in (flat.resize((T, T), Image.LANCZOS), dot.resize((T, T), Image.LANCZOS),
                   p64.resize((T, T), Image.NEAREST), p32.resize((T, T), Image.NEAREST),
                   i32.resize((128, 128), Image.NEAREST)):
            if im.mode == "RGBA":
                sheet.paste(im, (x, y), im)
            else:
                sheet.paste(im, (x, y))
            x += T + G
    sheet.save(os.path.join(sc.OUT, "finalists-fullsun.png")); print("ok")
