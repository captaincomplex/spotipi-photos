"""Spotipi Photos — illustrated assembly guide. Original line-art, drawn with reportlab.

Mirrors the approach used for Ident's assembly guide: no photographs and no
third-party artwork — every object on the page is drawn from primitives here,
so the file is ours to ship and ours to change.

All object dimensions are in millimetres, so that object sizes and page layout
are in the same units. A scale factor s=1 draws an object at its natural size.

    python3 assembly_guide_source.py                  # writes alongside this file
    python3 assembly_guide_source.py /path/out.pdf
"""
import math
import os
import sys

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

W, H = A4
INK = (0.10, 0.11, 0.13)
GREY = (0.55, 0.58, 0.62)
LIGHT = (0.88, 0.89, 0.91)
ACC = (0.16, 0.60, 0.86)
RED = (0.80, 0.25, 0.25)
GREEN = (0.20, 0.60, 0.42)
AMBER = (0.85, 0.60, 0.15)
PAPER = (0.98, 0.98, 0.97)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "spotipi_assembly_guide.pdf")
if len(sys.argv) > 1:
    OUT = sys.argv[1]

c = canvas.Canvas(OUT, pagesize=A4)
c.setTitle("Spotipi Photos — Assembly Guide")
c.setAuthor("Spotipi Photos")
c.setSubject("How to assemble your Spotipi Photos LED matrix display")

VERSION_LINE = "Correct as of version 2.4"
TOTAL = 8

L = 20*mm            # left margin
R = W - 20*mm        # right margin


# ---------- primitives ----------
def stroke(col=INK, w=1.6):
    c.setStrokeColorRGB(*col); c.setLineWidth(w)
    c.setLineCap(1); c.setLineJoin(1)


def fill(col):
    c.setFillColorRGB(*col)


def rrect(x, y, w, h, r=4, s=INK, f=None, lw=1.6):
    stroke(s, lw)
    if f:
        fill(f); c.roundRect(x, y, w, h, r, stroke=1, fill=1)
    else:
        c.roundRect(x, y, w, h, r, stroke=1, fill=0)


def label(x, y, t, size=9.5, col=INK, font="Helvetica", align="l"):
    fill(col); c.setFont(font, size)
    if align == "c":
        c.drawCentredString(x, y, t)
    elif align == "r":
        c.drawRightString(x, y, t)
    else:
        c.drawString(x, y, t)


def callout(x, y, n, r=4.2*mm, col=ACC):
    """Filled numbered badge, for pointing at a specific socket."""
    stroke((1, 1, 1), 1.8); fill(col)
    c.circle(x, y, r, stroke=1, fill=1)
    fill((1, 1, 1)); c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(x, y - 3.3, str(n))


def stepnum(x, y, n, r=9, col=INK):
    stroke(col, 1.6); fill((1, 1, 1))
    c.circle(x, y, r, stroke=1, fill=1)
    fill(col); c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x, y - 3.8, str(n))


def arrow(x1, y1, x2, y2, col=ACC, w=1.8, head=5):
    stroke(col, w); c.line(x1, y1, x2, y2)
    a = math.atan2(y2 - y1, x2 - x1)
    fill(col)
    p = c.beginPath(); p.moveTo(x2, y2)
    p.lineTo(x2 - head * math.cos(a - 0.4), y2 - head * math.sin(a - 0.4))
    p.lineTo(x2 - head * math.cos(a + 0.4), y2 - head * math.sin(a + 0.4))
    p.close(); c.drawPath(p, stroke=0, fill=1)


def dashed(x1, y1, x2, y2, col=GREY):
    c.saveState(); stroke(col, 1.0); c.setDash(3, 3)
    c.line(x1, y1, x2, y2); c.restoreState()


def crossout(cx, cy, r=26):
    stroke(RED, 3.0); c.circle(cx, cy, r, stroke=1, fill=0)
    d = r * 0.707; c.line(cx - d, cy + d, cx + d, cy - d)


def tick(cx, cy, s=1.0, col=GREEN):
    stroke(col, 3.0)
    c.line(cx - 7*s, cy, cx - 2*s, cy - 6*s)
    c.line(cx - 2*s, cy - 6*s, cx + 8*s, cy + 7*s)


# ---------- objects (all sized in mm) ----------
def matrix_panel(x, y, s=1.0, dots=12):
    """64x64 LED matrix, front view. Natural size 26mm square on the page."""
    side = 26*mm*s
    rrect(x, y, side, side, 1.5*mm*s, INK, (0.13, 0.13, 0.15), 1.8)
    inset = 2.2*mm*s
    step = (side - 2*inset) / (dots - 1)
    for r in range(dots):
        for i in range(dots):
            v = (i + r) / (2.0 * (dots - 1))
            fill((0.16 + 0.80*v, 0.66 - 0.10*v, 0.86 - 0.62*v))
            c.circle(x + inset + i*step, y + inset + r*step,
                     0.55*mm*s, stroke=0, fill=1)
    return side


def matrix_back(x, y, s=1.0):
    """Back of the panel: two HUB75 sockets and the power header."""
    side = 26*mm*s
    rrect(x, y, side, side, 1.5*mm*s, INK, (0.90, 0.90, 0.88), 1.8)
    rrect(x + 3*mm*s, y + side - 8*mm*s, 8*mm*s, 3.4*mm*s, 0.6*mm*s,
          INK, (1, 1, 1), 1.3)
    label(x + 3*mm*s, y + side - 11.4*mm*s, "INPUT", 6.2*s, INK, "Helvetica-Bold")
    rrect(x + 15*mm*s, y + side - 8*mm*s, 8*mm*s, 3.4*mm*s, 0.6*mm*s,
          GREY, (1, 1, 1), 1.1)
    label(x + 15*mm*s, y + side - 11.4*mm*s, "OUTPUT", 6.2*s, GREY)
    stroke(INK, 1.3)
    for i in range(4):
        c.rect(x + 9*mm*s + i*1.9*mm*s, y + 4*mm*s, 1.2*mm*s, 2.6*mm*s,
               stroke=1, fill=0)
    label(x + 9*mm*s, y + 1.6*mm*s, "POWER", 6.2*s, INK, "Helvetica-Bold")
    return side


def pi_board(x, y, s=1.0):
    """Raspberry Pi 3 Model A+, top view. Natural 27 x 22 mm."""
    bw, bh = 27*mm*s, 22*mm*s
    rrect(x, y, bw, bh, 1*mm*s, INK, (0.93, 0.95, 0.94), 1.6)
    stroke(GREY, 1.0)
    for row in range(2):
        for i in range(20):
            px = x + 2.6*mm*s + i*(bw - 5.6*mm*s)/19
            c.rect(px - 0.35*mm*s, y + bh - (3.2 + row*2.4)*mm*s,
                   0.7*mm*s, 1.9*mm*s, stroke=1, fill=0)
    rrect(x + 9.5*mm*s, y + 8*mm*s, 6*mm*s, 5.2*mm*s, 0.5*mm*s, GREY, None, 1.2)
    stroke(INK, 1.4)
    c.rect(x + bw - 7*mm*s, y + 2*mm*s, 5.2*mm*s, 3.8*mm*s, stroke=1, fill=0)
    c.rect(x + 1.6*mm*s, y + 1.4*mm*s, 3.8*mm*s, 2.1*mm*s, stroke=1, fill=0)
    return bw, bh


def bonnet(x, y, s=1.0):
    """Adafruit RGB Matrix Bonnet: barrel jack, screw terminal, IDC socket."""
    bw, bh = 27*mm*s, 14*mm*s
    rrect(x, y, bw, bh, 0.9*mm*s, INK, (0.20, 0.42, 0.34), 1.6)
    # barrel jack
    rrect(x + 1*mm*s, y + 4.2*mm*s, 4.8*mm*s, 5.2*mm*s, 0.7*mm*s,
          INK, (0.15, 0.15, 0.17), 1.4)
    stroke((1, 1, 1), 1.0)
    c.circle(x + 3.4*mm*s, y + 6.8*mm*s, 1.25*mm*s, stroke=1, fill=0)
    # screw terminal
    rrect(x + 7.2*mm*s, y + 4.5*mm*s, 6.2*mm*s, 4.8*mm*s, 0.5*mm*s,
          INK, (0.35, 0.37, 0.40), 1.3)
    stroke((1, 1, 1), 1.1)
    c.circle(x + 8.9*mm*s, y + 6.9*mm*s, 0.9*mm*s, stroke=1, fill=0)
    c.circle(x + 11.7*mm*s, y + 6.9*mm*s, 0.9*mm*s, stroke=1, fill=0)
    fill((1, 1, 1)); c.setFont("Helvetica-Bold", 6.0*s)
    c.drawCentredString(x + 8.9*mm*s, y + 2.5*mm*s, "+")
    c.drawCentredString(x + 11.7*mm*s, y + 2.5*mm*s, "-")
    # IDC socket
    rrect(x + 15.5*mm*s, y + 3.8*mm*s, 9.6*mm*s, 6.2*mm*s, 0.5*mm*s,
          INK, (0.92, 0.92, 0.90), 1.4)
    stroke(GREY, 0.8)
    for i in range(8):
        c.line(x + 16.6*mm*s + i*1.1*mm*s, y + 4.8*mm*s,
               x + 16.6*mm*s + i*1.1*mm*s, y + 9.0*mm*s)
    stroke(GREY, 1.0)
    for i in range(20):
        px = x + 2.6*mm*s + i*(bw - 5.6*mm*s)/19
        c.rect(px - 0.32*mm*s, y + 0.5*mm*s, 0.64*mm*s, 1.6*mm*s,
               stroke=1, fill=0)
    return bw, bh


def ribbon(x1, y1, x2, y2, s=1.0):
    stroke(GREY, 5.0*s)
    mx = (x1 + x2) / 2
    p = c.beginPath(); p.moveTo(x1, y1); p.curveTo(mx, y1, mx, y2, x2, y2)
    c.drawPath(p, stroke=1, fill=0)
    stroke((1, 1, 1), 1.0)
    p2 = c.beginPath(); p2.moveTo(x1, y1); p2.curveTo(mx, y1, mx, y2, x2, y2)
    c.drawPath(p2, stroke=1, fill=0)


def power_lead(x1, y1, x2, y2, col=RED, w=2.2):
    stroke(col, w)
    mx = (x1 + x2) / 2
    p = c.beginPath(); p.moveTo(x1, y1); p.curveTo(mx, y1, mx, y2, x2, y2)
    c.drawPath(p, stroke=1, fill=0)


def psu_barrel(x, y, s=1.0):
    """Mains brick with a barrel plug on a lead. Natural body 13 x 9 mm."""
    rrect(x, y, 13*mm*s, 9*mm*s, 1*mm*s, INK, (0.95, 0.95, 0.94), 1.5)
    label(x + 6.5*mm*s, y + 3.6*mm*s, "5V 4A", 6.4*s, INK, "Helvetica-Bold", "c")
    stroke(INK, 1.4)
    c.line(x + 4*mm*s, y + 9*mm*s, x + 4*mm*s, y + 11.4*mm*s)
    c.line(x + 9*mm*s, y + 9*mm*s, x + 9*mm*s, y + 11.4*mm*s)
    stroke(INK, 1.5)
    p = c.beginPath(); p.moveTo(x + 13*mm*s, y + 4.4*mm*s)
    p.curveTo(x + 21*mm*s, y + 4.4*mm*s, x + 19*mm*s, y - 4*mm*s,
              x + 27*mm*s, y - 2.6*mm*s)
    c.drawPath(p, stroke=1, fill=0)
    rrect(x + 27*mm*s, y - 4.4*mm*s, 4.4*mm*s, 3.6*mm*s, 0.6*mm*s,
          INK, (0.15, 0.15, 0.17), 1.4)


def psu_usb(x, y, s=1.0):
    rrect(x, y, 11*mm*s, 8*mm*s, 1*mm*s, INK, (0.95, 0.95, 0.94), 1.5)
    label(x + 5.5*mm*s, y + 3.2*mm*s, "5.1V", 6.0*s, INK, "Helvetica-Bold", "c")
    stroke(INK, 1.4)
    c.line(x + 3.4*mm*s, y + 8*mm*s, x + 3.4*mm*s, y + 10.2*mm*s)
    c.line(x + 7.6*mm*s, y + 8*mm*s, x + 7.6*mm*s, y + 10.2*mm*s)
    stroke(INK, 1.5)
    p = c.beginPath(); p.moveTo(x + 11*mm*s, y + 3.6*mm*s)
    p.curveTo(x + 18*mm*s, y + 3.6*mm*s, x + 16*mm*s, y - 3.6*mm*s,
              x + 23*mm*s, y - 2.4*mm*s)
    c.drawPath(p, stroke=1, fill=0)
    c.rect(x + 23*mm*s, y - 3.8*mm*s, 3.2*mm*s, 2.6*mm*s, stroke=1, fill=0)


def pigtail(x, y, s=1.0):
    """Panel power cable: 4-hole plug one end, two spade terminals the other."""
    rrect(x, y, 6*mm*s, 4*mm*s, 0.5*mm*s, INK, (0.92, 0.92, 0.90), 1.4)
    stroke(GREY, 0.9)
    for i in range(4):
        c.line(x + 1.2*mm*s + i*1.2*mm*s, y + 0.8*mm*s,
               x + 1.2*mm*s + i*1.2*mm*s, y + 3.2*mm*s)
    power_lead(x + 6*mm*s, y + 2.8*mm*s, x + 20*mm*s, y + 5.4*mm*s, RED, 2.2*s)
    power_lead(x + 6*mm*s, y + 1.2*mm*s, x + 20*mm*s, y + 0.6*mm*s, INK, 2.2*s)
    stroke(RED, 1.4); fill((1, 0.93, 0.92))
    c.rect(x + 20*mm*s, y + 4.2*mm*s, 3.2*mm*s, 2.4*mm*s, stroke=1, fill=1)
    stroke(INK, 1.4); fill((0.90, 0.90, 0.90))
    c.rect(x + 20*mm*s, y - 0.6*mm*s, 3.2*mm*s, 2.4*mm*s, stroke=1, fill=1)


def sd_card(x, y, s=1.0):
    w_, h_ = 7*mm*s, 9*mm*s
    p = c.beginPath()
    p.moveTo(x, y); p.lineTo(x + w_, y); p.lineTo(x + w_, y + h_)
    p.lineTo(x + 2.2*mm*s, y + h_); p.lineTo(x, y + h_ - 2.6*mm*s); p.close()
    stroke(INK, 1.5); fill((0.95, 0.95, 0.93)); c.drawPath(p, stroke=1, fill=1)
    stroke(GREY, 0.9)
    for i in range(4):
        c.line(x + 1.6*mm*s + i*1.3*mm*s, y + 1*mm*s,
               x + 1.6*mm*s + i*1.3*mm*s, y + 3*mm*s)


def phone(x, y, s=1.0):
    rrect(x, y, 11*mm*s, 20*mm*s, 1.4*mm*s, INK, (1, 1, 1), 1.6)
    rrect(x + 1.1*mm*s, y + 2.2*mm*s, 8.8*mm*s, 15.6*mm*s, 0.5*mm*s,
          LIGHT, None, 0.9)
    stroke(GREY, 1.2)
    c.line(x + 4*mm*s, y + 1.2*mm*s, x + 7*mm*s, y + 1.2*mm*s)


def laptop(x, y, s=1.0):
    rrect(x, y + 3.6*mm*s, 21*mm*s, 13*mm*s, 0.9*mm*s, INK, (1, 1, 1), 1.6)
    rrect(x + 1.4*mm*s, y + 5*mm*s, 18.2*mm*s, 10.2*mm*s, 0.4*mm*s,
          LIGHT, None, 0.9)
    stroke(INK, 1.6)
    p = c.beginPath(); p.moveTo(x - 2.2*mm*s, y); p.lineTo(x + 23.2*mm*s, y)
    p.lineTo(x + 21*mm*s, y + 3.6*mm*s); p.lineTo(x, y + 3.6*mm*s); p.close()
    fill((0.96, 0.96, 0.95)); c.drawPath(p, stroke=1, fill=1)


def clockface(x, y, r=13, mins=3):
    stroke(INK, 1.6); fill((1, 1, 1)); c.circle(x, y, r, stroke=1, fill=1)
    stroke(INK, 1.8); c.line(x, y, x, y + r*0.6)
    a = math.radians(90 - mins*30)
    c.line(x, y, x + r*0.75*math.cos(a), y + r*0.75*math.sin(a))


def bolt(x, y, s=1.0, col=AMBER):
    fill(col)
    p = c.beginPath()
    p.moveTo(x, y + 10*s); p.lineTo(x + 5*s, y + 10*s); p.lineTo(x + 1*s, y + 3*s)
    p.lineTo(x + 6*s, y + 3*s); p.lineTo(x - 1*s, y - 10*s); p.lineTo(x + 1*s, y + 1*s)
    p.lineTo(x - 4*s, y + 1*s); p.close()
    c.drawPath(p, stroke=0, fill=1)


def brandmark(x, y, size, dots=True, grid=16):
    """The Spotipi Photos mark: the owner's orange-sunset photo, drawn as LEDs.

    Colours come from image/logos/sunset/grid-<n>.json, written by
    image/build_logo_assets.py, so the guide still builds with nothing but
    reportlab. `dots` draws the matrix look; False draws square pixels, which
    is what the panel itself shows.
    """
    import json as _json
    gp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                      "image", "logos", "sunset", f"grid-{grid}.json")
    cells = _json.load(open(gp))
    n = len(cells)

    def rgb(h):
        return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))

    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, size, size, size * 0.22)
    c.clipPath(p, stroke=0, fill=0)
    fill((0.078, 0.086, 0.102)); c.rect(x, y, size, size, stroke=0, fill=1)
    if dots:
        pad = 0.085
        inner = size * (1 - 2 * pad); off = size * pad; dr = (inner / n) * 0.40
        for row in range(n):
            for col in range(n):
                fill(rgb(cells[row][col]))
                # y is flipped: the grid runs top-down, reportlab bottom-up
                c.circle(x + off + (col + 0.5) / n * inner,
                         y + size - (off + (row + 0.5) / n * inner), dr, stroke=0, fill=1)
    else:
        step = size / n
        for row in range(n):
            for col in range(n):
                fill(rgb(cells[row][col]))
                # a hair of overlap so no seams show between squares
                c.rect(x + col * step, y + size - (row + 1) * step,
                       step + 0.05, step + 0.05, stroke=0, fill=1)
    c.restoreState()


# ---------- page furniture ----------
def page_header(title, n, total=TOTAL):
    brandmark(L, H - 16.5*mm, 5.5*mm, dots=False)
    fill(INK); c.setFont("Helvetica-Bold", 8.5)
    c.drawString(L + 7.5*mm, H - 15*mm, "SPOTIPI PHOTOS")
    fill(GREY); c.setFont("Helvetica", 8.5)
    c.drawRightString(R, H - 15*mm, f"{n} / {total}")
    stroke(LIGHT, 1.0); c.line(L, H - 18*mm, R, H - 18*mm)
    if title:
        fill(INK); c.setFont("Helvetica-Bold", 15)
        c.drawString(L, H - 30*mm, title)


def footer(note=""):
    stroke(LIGHT, 1.0); c.line(L, 18*mm, R, 18*mm)
    fill(GREY); c.setFont("Helvetica", 7.5)
    c.drawString(L, 13*mm, note or "Full instructions: SPOTIPI_BEGINNERS_GUIDE.md")
    c.drawRightString(R, 13*mm, VERSION_LINE)


# ============================== PAGE 1 — COVER ==============================
fill(PAPER); c.rect(0, 0, W, H, stroke=0, fill=1)

brandmark(L, H - 62*mm, 26*mm, dots=True)
fill(INK); c.setFont("Helvetica-Bold", 34)
c.drawString(L + 32*mm, H - 46*mm, "SPOTIPI")
fill(GREY); c.setFont("Helvetica", 12.5)
c.drawString(L + 32*mm, H - 55*mm, "Photos — assembly guide")
stroke(ACC, 2.5); c.line(L + 32*mm, H - 60*mm, L + 72*mm, H - 60*mm)

# hero: the mark itself, at panel scale, on a stand
side = 62*mm
hx = (W - side) / 2
hy = H/2 - 40*mm
brandmark(hx, hy, side, dots=True, grid=20)
cxm = hx + side/2
stroke(INK, 1.8)
c.line(cxm, hy, cxm, hy - 12*mm)
c.line(cxm - 17*mm, hy - 12*mm, cxm + 17*mm, hy - 12*mm)

fill(GREY); c.setFont("Helvetica", 10)
c.drawString(L, 56*mm, "Your photos, and your album art, on 4,096 LEDs.")
c.drawString(L, 50*mm, "No soldering required. One power supply. No special tools.")
c.drawString(L, 44*mm, "About an hour to build, then a longer wait while software installs.")
c.drawString(L, 38*mm, "Works from a Windows PC or a Mac.")
fill(RED); c.setFont("Helvetica-Bold", 10)
c.drawString(L, 29*mm, "Read pages 2 and 3 before you plug anything in.")
footer()
c.showPage()

# ============================== PAGE 2 — PARTS ==============================
page_header("What's in front of you", 2)
label(L, H - 38*mm,
      "Lay everything out and check it off. Nothing here is supplied by us — you bought it yourself.",
      9.5, GREY)

ART = L + 6*mm
TXT = L + 52*mm


def part_row(top, title, lines, qty, draw, title_col=INK):
    label(TXT, top, title, 10.5, title_col, "Helvetica-Bold")
    y = top - 7*mm
    for ln in lines:
        label(TXT, y, ln, 9, GREY)
        y -= 5.6*mm
    label(TXT, y - 1.5*mm, qty, 9.5, INK, "Helvetica-Bold")
    draw()


row = H - 54*mm
part_row(row, "64x64 LED matrix panel, 3mm pitch",
         ["192 x 192 mm, and heavier than it looks (235 g).",
          "Comes with its ribbon cable AND its power cable.",
          "32x32 and 64x32 panels also work — see the guide."],
         "x 1",
         lambda: matrix_panel(ART, row - 20*mm, 0.95, dots=10))

row -= 38*mm
part_row(row, "Adafruit RGB Matrix Bonnet",
         ["Arrives fully assembled — no soldering.",
          "Not the HAT + RTC: that costs more and adds a clock",
          "this project never uses."],
         "x 1",
         lambda: bonnet(ART - 2*mm, row - 13*mm, 1.05))

row -= 38*mm
part_row(row, "Raspberry Pi 3 Model A+",
         ["The 40 pins are already fitted.",
          "Not a Pi Zero 2 W (out of stock, and marginal here),",
          "and not a Pi 5."],
         "x 1",
         lambda: pi_board(ART, row - 20*mm, 1.05))

row -= 40*mm
part_row(row, "ONE 5V 4A power supply",
         ["2.1mm barrel plug, centre positive.",
          "It powers the panel AND the Pi — the bonnet feeds",
          "the Pi through an onboard diode. See page 3."],
         "x 1",
         lambda: psu_barrel(ART, row - 14*mm, 0.95))

row -= 38*mm
part_row(row, "microSD card",
         ["16-32GB. You'll also need a way to plug it",
          "into your computer."],
         "x 1",
         lambda: sd_card(ART + 4*mm, row - 14*mm, 1.15))

rrect(L, 26*mm, R - L, 24*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, 42*mm, "Tools needed", 10, INK, "Helvetica-Bold")
label(L + 6*mm, 35*mm,
      "A small flat screwdriver, for two screw terminals. That is all for the standard build.", 9, GREY)
label(L + 6*mm, 29.5*mm,
      "A soldering iron is optional, for the one-wire quality mod described on page 8.", 9, GREY)
footer()
c.showPage()

# ============================== PAGE 3 — BEFORE YOU START ==============================
page_header("Before you start", 3)

# --- the power story, in one box ---
bx, byy, bh = L, H - 116*mm, 78*mm
rrect(bx, byy, R - L, bh, 4, ACC, (0.96, 0.98, 1.0), 1.4)
label(bx + 6*mm, byy + bh - 10*mm, "One power supply runs the whole thing",
      12, ACC, "Helvetica-Bold")
for i, t in enumerate([
        "The 5V 4A supply plugs into the BONNET, and the bonnet feeds the Pi through a diode on the",
        "board. Adafruit put it plainly: \"just plug in the 5V wall adapter into the bonnet and it will",
        "automagically power up the Pi too\". You do not need a second supply for the Pi."]):
    label(bx + 6*mm, byy + bh - 19*mm - i*6.5*mm, t, 9.5, INK)

psu_barrel(bx + 12*mm, byy + 22*mm, 0.95)
arrow(bx + 56*mm, byy + 26*mm, bx + 72*mm, byy + 26*mm, ACC, 2.2, 6)
bonnet(bx + 78*mm, byy + 19*mm, 1.15)
arrow(bx + 116*mm, byy + 26*mm, bx + 130*mm, byy + 26*mm, ACC, 2.2, 6)
label(bx + 134*mm, byy + 30*mm, "panel", 9.5, INK, "Helvetica-Bold")
label(bx + 134*mm, byy + 23*mm, "and Pi", 9.5, INK, "Helvetica-Bold")
label(bx + 6*mm, byy + 10*mm,
      "Add a second, micro-USB supply for the Pi ONLY if you run a 64x64 panel at brightness 90-100 and see",
      8.6, GREY)
label(bx + 6*mm, byy + 5*mm,
      "the Pi's undervoltage warning. Most builds never do, and a 32x32 never will.", 8.6, GREY)

# --- polarity: the correct wiring, shown once ---
py, ph = H - 186*mm, 62*mm
rrect(L, py, R - L, ph, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, py + ph - 10*mm, "Two wires into the bonnet's screw terminal",
      11, INK, "Helvetica-Bold")

tx0 = L + 10*mm
stroke(RED, 3.0); c.line(tx0, py + 34*mm, tx0 + 26*mm, py + 34*mm)
stroke(INK, 3.0); c.line(tx0, py + 24*mm, tx0 + 26*mm, py + 24*mm)
label(tx0 + 31*mm, py + 32*mm, "RED", 11, RED, "Helvetica-Bold")
label(tx0 + 31*mm, py + 22*mm, "BLACK", 11, INK, "Helvetica-Bold")
label(tx0 + 55*mm, py + 32*mm, "goes to", 9.5, GREY)
label(tx0 + 55*mm, py + 22*mm, "goes to", 9.5, GREY)
fill(INK); c.setFont("Helvetica-Bold", 15)
c.drawString(tx0 + 78*mm, py + 31*mm, "+")
c.drawString(tx0 + 78*mm, py + 21*mm, "-")
label(tx0 + 88*mm, py + 32*mm, "marked on the bonnet", 9.5, INK)
label(tx0 + 88*mm, py + 22*mm, "marked on the bonnet", 9.5, INK)

label(L + 6*mm, py + 12*mm,
      "Loosen the screw, insert the wire, tighten, then tug gently — neither should pull out.", 9, GREY)
label(L + 6*mm, py + 6*mm,
      "Check both before the supply goes anywhere near a mains socket.", 9, INK, "Helvetica-Bold")

# --- two things to sort out before the parts arrive ---
ry = 68*mm
rrect(L, ry, R - L, 44*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, ry + 35*mm, "Two things to sort out while you wait for the parts",
      10, INK, "Helvetica-Bold")
fill(ACC); c.circle(L + 9*mm, ry + 26.2*mm, 1.4*mm, stroke=0, fill=1)
label(L + 14*mm, ry + 25*mm, "A free Spotify developer app.", 9, INK, "Helvetica-Bold")
label(L + 61*mm, ry + 25*mm,
      "Five minutes at developer.spotify.com/dashboard. It gives you", 9, GREY)
label(L + 14*mm, ry + 19*mm,
      "three values the Pi needs later. No Premium required. The guide walks through it.", 9, GREY)
fill(ACC); c.circle(L + 9*mm, ry + 10.2*mm, 1.4*mm, stroke=0, fill=1)
label(L + 14*mm, ry + 9*mm, "How photos will reach it.", 9, INK, "Helvetica-Bold")
label(L + 56*mm, ry + 9*mm,
      "Automatically from Apple Photos needs a Mac.", 9, GREY)
label(L + 14*mm, ry + 3*mm,
      "From a Windows PC, a supplied script crops and copies them across whenever you want a change.", 9, GREY)

# --- brightness ---
rrect(L, 30*mm, R - L, 32*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
bolt(L + 10*mm, 46*mm, 1.0)
label(L + 20*mm, 51*mm, "It is brighter than you are expecting", 10, INK, "Helvetica-Bold")
label(L + 20*mm, 43.5*mm,
      "At full brightness this lights a whole room. Don't judge it on the first switch-on —", 9, GREY)
label(L + 20*mm, 37.5*mm,
      "you set brightness, a night dimmer and an off-schedule from your phone later.", 9, GREY)
footer()
c.showPage()

# ============================== PAGE 4 — STEP 1: CARD ==============================
page_header("", 4)
stepnum(L + 4*mm, H - 32*mm, 1, 10)
label(L + 14*mm, H - 35.5*mm, "Prepare the memory card", 15, INK, "Helvetica-Bold")
label(L + 14*mm, H - 43*mm, "On your own computer — Windows or Mac. Nothing is plugged in yet.", 9.5, GREY)

laptop(L + 22*mm, H - 82*mm, 1.9)
sd_card(L + 116*mm, H - 80*mm, 1.5)
arrow(L + 110*mm, H - 74*mm, L + 90*mm, H - 74*mm, ACC, 2.0, 6)
label(L + 14*mm, H - 95*mm,
      "Install Raspberry Pi Imager from raspberrypi.com/software, choose Raspberry Pi 3,", 9.5, INK)
label(L + 14*mm, H - 102*mm, "and pick Raspberry Pi OS Lite (64-bit).", 9.5, INK)

by = H - 186*mm
rrect(L, by, R - L, 74*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, by + 65*mm, "In Imager, click Edit Settings and fill in all of this:", 10, INK, "Helvetica-Bold")
items = [("Hostname", "spotipi"),
         ("Username", "pi  (and a password you write down)"),
         ("Wi-Fi", "your network name and password, country GB"),
         ("Time zone", "Europe/London — the night dimmer and off-schedule use it"),
         ("Services tab", "tick Enable SSH, password authentication")]
yy = by + 54*mm
for k, v in items:
    fill(ACC); c.circle(L + 9*mm, yy + 1.2*mm, 1.4*mm, stroke=0, fill=1)
    label(L + 14*mm, yy, k, 9.5, INK, "Helvetica-Bold")
    label(L + 48*mm, yy, v, 9.5, GREY)
    yy -= 9*mm
label(L + 6*mm, by + 7*mm,
      "Then Save, Write, and wait. This erases the card — check you picked the card, not your computer's disk.",
      8.6, GREY)

rrect(L, 30*mm, R - L, 34*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, 53*mm, "Why there is no keyboard or monitor in this guide", 10, INK, "Helvetica-Bold")
label(L + 6*mm, 45.5*mm,
      "Those five settings are what let the Pi join your Wi-Fi and accept instructions on first boot.", 9, GREY)
label(L + 6*mm, 39.5*mm,
      "Get them right and you will never plug a screen into it. Get the Wi-Fi wrong and it is the one", 9, GREY)
label(L + 6*mm, 33.5*mm,
      "mistake that means starting this page again.", 9, GREY)
footer()
c.showPage()

# ============================== PAGE 5 — STEP 2: BONNET ONTO PI ==============================
page_header("", 5)
stepnum(L + 4*mm, H - 32*mm, 2, 10)
label(L + 14*mm, H - 35.5*mm, "Push the bonnet onto the Pi", 15, INK, "Helvetica-Bold")
label(L + 14*mm, H - 43*mm, "Everything unplugged. Line the pins up, press straight down.", 9.5, GREY)

dx, dy = L + 30*mm, H - 78*mm
bonnet(dx, dy, 1.5)
pi_board(dx, dy - 40*mm, 1.5)
for off in (8*mm, 18*mm, 28*mm, 36*mm):
    dashed(dx + off, dy - 1*mm, dx + off, dy - 18*mm)
arrow(dx + 62*mm, dy + 7*mm, dx + 44*mm, dy + 7*mm, ACC, 2.0, 5)
label(dx + 65*mm, dy + 8*mm, "all 40 pins", 8.5, ACC, "Helvetica-Bold")
label(dx + 65*mm, dy + 2*mm, "engaged", 8.5, GREY)
label(dx + 65*mm, dy - 26*mm, "Pi underneath,", 8.5, GREY)
label(dx + 65*mm, dy - 32*mm, "bonnet on top", 8.5, GREY)

by = H - 196*mm
rrect(L, by, 82*mm, 54*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
tick(L + 11*mm, by + 43*mm, 1.2)
label(L + 19*mm, by + 41*mm, "Right", 10, GREEN, "Helvetica-Bold")
label(L + 6*mm, by + 31*mm, "Every pin in a socket. Boards", 9, GREY)
label(L + 6*mm, by + 24.5*mm, "parallel, no gap at one end.", 9, GREY)
label(L + 6*mm, by + 18*mm, "Pressed home evenly, both hands.", 9, GREY)
label(L + 6*mm, by + 8*mm, "It only fits one way round.", 9, INK, "Helvetica-Bold")

qx = L + 90*mm
rrect(qx, by, 82*mm, 54*mm, 4, LIGHT, (1.0, 0.98, 0.97), 1.2)
crossout(qx + 11*mm, by + 42*mm, 6*mm)
label(qx + 21*mm, by + 41*mm, "Wrong", 10, RED, "Helvetica-Bold")
label(qx + 6*mm, by + 31*mm, "Offset by one row, or a pin", 9, GREY)
label(qx + 6*mm, by + 24.5*mm, "hanging over the end.", 9, GREY)
label(qx + 6*mm, by + 14.5*mm, "Don't force it. Lift it off, line it", 9, GREY)
label(qx + 6*mm, by + 8*mm, "up again, and try once more.", 9, GREY)

ny = 34*mm
rrect(L, ny, R - L, 52*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, ny + 43*mm, "Think about where it will live, now rather than later", 10, INK, "Helvetica-Bold")
label(L + 6*mm, ny + 35*mm,
      "The ribbon cable in the next step is only about 16 cm long, so the Pi has to sit close behind or", 9, GREY)
label(L + 6*mm, ny + 29*mm,
      "beside the panel — you cannot tuck it away on a shelf below.", 9, GREY)
label(L + 6*mm, ny + 19*mm,
      "The panel is 192 x 192 x 14 mm and 235 g, with M3 threaded holes on the back. It is too deep for a", 9, GREY)
label(L + 6*mm, ny + 13*mm,
      "standard picture frame and too heavy for a picture pin. A deep box frame, or M3 standoffs onto a", 9, GREY)
label(L + 6*mm, ny + 7*mm,
      "backing board, are the two arrangements that work.", 9, GREY)
footer()
c.showPage()

# ============================== PAGE 6 — STEP 3: RIBBON + POWER ==============================
page_header("", 6)
stepnum(L + 4*mm, H - 32*mm, 3, 10)
label(L + 14*mm, H - 35.5*mm, "Connect the panel", 15, INK, "Helvetica-Bold")
label(L + 14*mm, H - 43*mm,
      "Two cables, both supplied with the panel. Nothing plugged into the mains yet.", 9.5, GREY)

# ---- back of the panel, left ----
px, pyy, pscale = L + 2*mm, 186*mm, 1.95
pside = matrix_back(px, pyy, pscale)
label(px, pyy - 6*mm, "BACK of the panel", 9, INK, "Helvetica-Bold")

s_ = pscale
in_x = px + 3*mm*s_ + 4*mm*s_
in_y = pyy + pside - 8*mm*s_ + 1.7*mm*s_
pw_x = px + 9*mm*s_ + 3.8*mm*s_
pw_y = pyy + 4*mm*s_ + 1.3*mm*s_

# ---- bonnet on the Pi, right ----
bx2, by2, bs = L + 116*mm, 204*mm, 1.7
bonnet(bx2, by2, bs)
label(bx2, by2 - 6*mm, "Bonnet, already on the Pi", 9, INK, "Helvetica-Bold")

idc_x = bx2 + 15.5*mm*bs + 4.8*mm*bs
idc_y = by2 + 3.8*mm*bs + 3.1*mm*bs
trm_x = bx2 + 7.2*mm*bs + 3.1*mm*bs
trm_y = by2 + 4.5*mm*bs + 2.4*mm*bs
jck_x = bx2 + 1*mm*bs + 2.4*mm*bs
jck_y = by2 + 4.2*mm*bs + 2.6*mm*bs

ribbon(in_x + 9*mm, in_y, idc_x - 7*mm, idc_y + 4*mm, 1.0)
power_lead(pw_x + 7*mm, pw_y + 1*mm, trm_x - 4*mm, trm_y - 4*mm, RED, 2.4)
power_lead(pw_x + 7*mm, pw_y - 2*mm, trm_x - 4*mm, trm_y - 7*mm, INK, 2.4)

callout(in_x, in_y, 1)
callout(idc_x, idc_y, 2)
callout(pw_x, pw_y, 3)
callout(trm_x, trm_y, 4)
callout(jck_x, jck_y, 5)

# ---- the key ----
ky, kh = 110*mm, 62*mm
rrect(L, ky, R - L, kh, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
rows_ = [
    (1, "Panel INPUT socket", "The grey ribbon goes here — not the socket beside it marked OUTPUT."),
    (2, "Bonnet ribbon socket", "The other end of the same ribbon. Keyed: it only fits one way round."),
    (3, "Panel POWER pins", "The four-hole plug on the power cable pushes on here."),
    (4, "Bonnet screw terminal", "The other end: RED wire to +, BLACK wire to -. Tighten, then tug."),
    (5, "Bonnet barrel jack", "The 5V 4A supply. Connect it last, and not at the wall yet."),
]
yy = ky + kh - 12*mm
for n, what, detail in rows_:
    callout(L + 9*mm, yy + 1*mm, n, 3.4*mm)
    label(L + 16*mm, yy - 1*mm, what, 9.5, INK, "Helvetica-Bold")
    label(L + 58*mm, yy - 1*mm, detail, 9, GREY)
    yy -= 9.6*mm

# ---- note below the key ----
label(L + 2*mm, 100*mm,
      "If the sockets aren't clearly marked, the arrows on the board point AWAY from INPUT. Choosing wrong damages",
      8.6, GREY)
label(L + 2*mm, 94.5*mm,
      "nothing — the panel simply stays dark — so if it does, swap to the other socket and try again.", 8.6, GREY)

# ---- the cable itself, so it's recognisable in the box ----
pigtail(L + 12*mm, 58*mm, 1.7)
label(L + 68*mm, 66*mm,
      "The power cable that came with the panel: a four-hole", 9, GREY)
label(L + 68*mm, 60*mm,
      "plug at one end, two wires at the other.", 9, GREY)
label(L + 68*mm, 52*mm, "Red is +.   Black is -.", 10, INK, "Helvetica-Bold")

rrect(L, 26*mm, R - L, 18*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, 36*mm, "Before you go on", 9.5, INK, "Helvetica-Bold")
label(L + 6*mm, 29.5*mm,
      "Check the ribbon is square at both ends and neither wire pulls out. A half-seated ribbon looks like a software fault.",
      8.6, GREY)
footer()
c.showPage()

# ============================== PAGE 7 — STEP 4: POWER UP ==============================
page_header("", 7)
stepnum(L + 4*mm, H - 32*mm, 4, 10)
label(L + 14*mm, H - 35.5*mm, "Card in, then switch on", 15, INK, "Helvetica-Bold")
label(L + 14*mm, H - 43*mm, "One supply, one switch. Nothing to sequence.", 9.5, GREY)

sy = H - 78*mm
sd_card(L + 10*mm, sy, 1.6)
label(L + 4*mm, sy - 9*mm, "microSD into the Pi", 9, INK, "Helvetica-Bold")
label(L + 4*mm, sy - 15*mm, "card slot on the underside", 8.6, GREY)

arrow(L + 34*mm, sy + 7*mm, L + 54*mm, sy + 7*mm, ACC, 2.2, 6)

psu_barrel(L + 60*mm, sy, 0.95)
label(L + 60*mm, sy - 9*mm, "Switch on at the wall", 9, INK, "Helvetica-Bold")
label(L + 60*mm, sy - 15*mm, "panel and Pi both come up together", 8.6, GREY)

wy2 = 160*mm
rrect(L, wy2, R - L, 34*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
clockface(L + 16*mm, wy2 + 17*mm, 12, 3)
label(L + 32*mm, wy2 + 22*mm, "Wait 2-3 minutes for the first boot.", 10, INK, "Helvetica-Bold")
label(L + 32*mm, wy2 + 14*mm,
      "The panel will show nothing useful yet — the software isn't on it. That comes next, and", 9, GREY)
label(L + 32*mm, wy2 + 8*mm,
      "it happens over the network from your computer.", 9, GREY)

gy = 92*mm
rrect(L, gy, 82*mm, 62*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
tick(L + 11*mm, gy + 51*mm, 1.2)
label(L + 19*mm, gy + 49*mm, "Normal", 10, GREEN, "Helvetica-Bold")
label(L + 6*mm, gy + 39*mm, "The panel flickers, shows random", 9, GREY)
label(L + 6*mm, gy + 32.5*mm, "colour noise, or stays dark.", 9, GREY)
label(L + 6*mm, gy + 22*mm, "A green light on the Pi,", 9, GREY)
label(L + 6*mm, gy + 15.5*mm, "flickering irregularly.", 9, GREY)
label(L + 6*mm, gy + 6*mm, "Nothing is broken.", 9, INK, "Helvetica-Bold")

qx = L + 90*mm
rrect(qx, gy, 82*mm, 62*mm, 4, LIGHT, (1.0, 0.98, 0.97), 1.2)
crossout(qx + 11*mm, gy + 50*mm, 6*mm)
label(qx + 21*mm, gy + 49*mm, "Stop", 10, RED, "Helvetica-Bold")
label(qx + 6*mm, gy + 39*mm, "Anything hot to the touch.", 9, GREY)
label(qx + 6*mm, gy + 32.5*mm, "Any smell of burning.", 9, GREY)
label(qx + 6*mm, gy + 22*mm, "Pull the plug and re-check the", 9, GREY)
label(qx + 6*mm, gy + 15.5*mm, "red-to-plus, black-to-minus", 9, GREY)
label(qx + 6*mm, gy + 9*mm, "wiring on page 3.", 9, GREY)

ty = 30*mm
rrect(L, ty, R - L, 52*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, ty + 43*mm, "The panel stays dark until the software is installed",
      10, INK, "Helvetica-Bold")
label(L + 6*mm, ty + 35*mm,
      "There is nothing on the card yet but the operating system, so an unlit panel now tells you nothing", 9, GREY)
label(L + 6*mm, ty + 29*mm,
      "either way. Don't start rewiring.", 9, GREY)
label(L + 6*mm, ty + 19*mm,
      "What IS worth checking is that the Pi joined your Wi-Fi. On your computer open PowerShell (Windows)", 9, GREY)
label(L + 6*mm, ty + 13*mm,
      "or Terminal (Mac) and run  ping spotipi.local  — replies mean page 4 was right and page 8 can begin.", 9, GREY)
label(L + 6*mm, ty + 6*mm,
      "No replies is almost always the Wi-Fi name or password. Re-flash the card and try again.", 9, GREY)
footer()
c.showPage()

# ============================== PAGE 8 — STEP 5: SOFTWARE ==============================
page_header("", 8)
stepnum(L + 4*mm, H - 32*mm, 5, 10)
label(L + 14*mm, H - 35.5*mm, "The rest happens on screen", 15, INK, "Helvetica-Bold")
label(L + 14*mm, H - 43*mm,
      "The hardware is finished. The software takes about two hours, most of it waiting.", 9.5, GREY)

laptop(L + 12*mm, H - 74*mm, 1.5)
arrow(L + 56*mm, H - 66*mm, L + 76*mm, H - 66*mm, ACC, 2.0, 6)
matrix_panel(L + 84*mm, H - 80*mm, 0.8, dots=10)
label(L + 12*mm, H - 88*mm,
      "From a Windows PC or a Mac, over your own network. You never plug a keyboard or monitor into the Pi.",
      9, GREY)

by = H - 168*mm
rrect(L, by, R - L, 74*mm, 4, LIGHT, (0.99, 0.99, 0.98), 1.2)
label(L + 6*mm, by + 65*mm, "What's left, in order — all of it in the beginner's guide:",
      10, INK, "Helvetica-Bold")
steps = [
    ("Spotify", "create a free developer app — Client ID, Secret and Redirect URI"),
    ("Connect", "ssh pi@spotipi.local  from PowerShell or Terminal"),
    ("Panel driver", "Adafruit's installer, then a 10-20 minute compile"),
    ("Token", "bash generate-token.sh  — the one-off Spotify login"),
    ("Install", "sudo bash install_pi.sh  — sets up both background services"),
    ("Photos", "an Apple Photos album on a Mac, or prepare_photos.py on any PC"),
]
yy = by + 55*mm
for k, v in steps:
    fill(ACC); c.circle(L + 9*mm, yy + 1.2*mm, 1.4*mm, stroke=0, fill=1)
    label(L + 14*mm, yy, k, 9.5, INK, "Helvetica-Bold")
    label(L + 44*mm, yy, v, 9, GREY)
    yy -= 9*mm

# the optional upgrade
uy = 66*mm
rrect(L, uy, R - L, 30*mm, 4, AMBER, (1.0, 0.99, 0.95), 1.3)
bolt(L + 10*mm, uy + 15*mm, 1.0)
label(L + 20*mm, uy + 21*mm, "Optional, and worth it: the one-wire quality mod",
      10, INK, "Helvetica-Bold")
label(L + 20*mm, uy + 13.5*mm,
      "Solder one wire between GPIO 4 and GPIO 18 on the bonnet and the panel goes visibly steadier.", 9, GREY)
label(L + 20*mm, uy + 7.5*mm,
      "Five minutes, one joint, reversible. The guide explains why, and how to switch it on afterwards.", 9, GREY)

phone(L + 10*mm, 24*mm, 1.55)
label(L + 38*mm, 52*mm, "Then it is all a web page", 11, INK, "Helvetica-Bold")
label(L + 38*mm, 44.5*mm, "http://spotipi.local  from your phone, on the same Wi-Fi.", 9.5, INK)
label(L + 38*mm, 37*mm,
      "Brightness, slideshow speed, a night dimmer, an off-schedule, and a live view of", 9, GREY)
label(L + 38*mm, 31*mm,
      "what is on the panel right now. Read SPOTIPI_BEGINNERS_GUIDE.md next.", 9, GREY)
footer()
c.showPage()

c.save()
print("wrote", OUT)
