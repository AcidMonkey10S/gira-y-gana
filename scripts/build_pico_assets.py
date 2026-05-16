"""
Convert the project PNGs into Pico-friendly 8-bit indexed BMP files
for use with CircuitPython + picodvi + adafruit_imageload.

Inputs (project art):
  frontend/public/bg.png                       (1408x768 RGBA)
  frontend/public/symbols/pico60/{symbol}.png  (60x60 RGBA)

Outputs (drop next to main.py on CIRCUITPY drive):
  frontend/public/circuitpython/bg.bmp         (320x240, 8-bit indexed, ~77 KB)
  frontend/public/circuitpython/symbols.bmp    (60x240,  8-bit indexed, ~14 KB)

The symbols are stacked vertically into ONE sheet so a single
displayio.TileGrid can pick which 60x60 tile to draw per reel - this
is the same idiom the existing main.py already uses, just with real art.
"""
import os
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "frontend", "public")
OUT = os.path.join(SRC, "circuitpython")
os.makedirs(OUT, exist_ok=True)


def flatten(img, bg_color=(0, 0, 0)):
    """Composite an RGBA image onto a solid background -> RGB."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    out = Image.new("RGB", img.size, bg_color)
    out.paste(img, (0, 0), img)
    return out


def to_indexed_bmp(rgb_img, out_path, colors=256):
    """Quantize to <= `colors` palette and save as 8-bit indexed BMP."""
    p = rgb_img.quantize(colors=colors, method=Image.MEDIANCUT,
                         dither=Image.FLOYDSTEINBERG)
    # PIL writes 8-bit indexed BMPs when mode == 'P'
    p.save(out_path, format="BMP")
    return p


# ---------- background ----------
bg = Image.open(os.path.join(SRC, "bg.png"))
bg = flatten(bg, bg_color=(10, 0, 20))
# Center-crop+resize so we keep the central GIRA Y GANA + starburst
bg_fit = ImageOps.fit(bg, (320, 240), method=Image.LANCZOS,
                      centering=(0.5, 0.5))
to_indexed_bmp(bg_fit, os.path.join(OUT, "bg.bmp"), colors=256)
print("wrote bg.bmp", os.path.getsize(os.path.join(OUT, "bg.bmp")), "bytes")

# ---------- symbol sheet (60x240, 4 stacked symbols) ----------
order = ["burger", "wings", "coke", "fries"]   # MUST match NAMES in main.py
sheet = Image.new("RGB", (60, 240), (0, 0, 0))
for i, name in enumerate(order):
    p = os.path.join(SRC, "symbols", "pico60", f"{name}.png")
    s = flatten(Image.open(p), bg_color=(0, 0, 0))
    if s.size != (60, 60):
        s = s.resize((60, 60), Image.LANCZOS)
    sheet.paste(s, (0, i * 60))
# 64 colours is plenty for 4 stylised cartoon symbols and keeps the BMP small
to_indexed_bmp(sheet, os.path.join(OUT, "symbols.bmp"), colors=64)
print("wrote symbols.bmp", os.path.getsize(os.path.join(OUT, "symbols.bmp")), "bytes")

print("done ->", OUT)
