"""
Convert the project PNGs into Pico-friendly 8-bit indexed BMP files
for use with CircuitPython + picodvi + adafruit_imageload.

Inputs (project art):
  frontend/public/bg.png                       (1408x768 RGBA)
  frontend/public/symbols/pico60/{symbol}.png  (60x60 RGBA)

Outputs (drop next to main.py on CIRCUITPY drive):
  frontend/public/circuitpython/bg.bmp         (320x240, 8-bit indexed, ~77 KB)
                                               -- main.py reads this through
                                                  displayio.OnDiskBitmap so it
                                                  uses ~0 bytes of RAM (pixels
                                                  stream from flash on demand).
                                                  That's how we afford a full
                                                  320x240 background on the
                                                  RP2040 alongside picodvi.
  frontend/public/circuitpython/symbols.bmp    (54x216, 8-bit indexed, ~12 KB)

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


def to_indexed_bmp(rgb_img, out_path, colors=256, dither=True):
    """Quantize to <= `colors` palette and save as 8-bit indexed BMP."""
    p = rgb_img.quantize(
        colors=colors,
        method=Image.MEDIANCUT,
        dither=Image.FLOYDSTEINBERG if dither else Image.NONE,
    )
    # PIL writes 8-bit indexed BMPs when mode == 'P'
    p.save(out_path, format="BMP")
    return p


# ---------- background ----------
bg = Image.open(os.path.join(SRC, "bg.png"))
bg = flatten(bg, bg_color=(10, 0, 20))
# Center-crop+resize to 320x240. Full screen resolution is fine here
# because main.py loads bg.bmp via displayio.OnDiskBitmap, which streams
# pixels straight from flash (~0 bytes of SRAM cost).
bg_fit = ImageOps.fit(bg, (320, 240), method=Image.LANCZOS,
                      centering=(0.5, 0.5))
to_indexed_bmp(bg_fit, os.path.join(OUT, "bg.bmp"), colors=256)
print("wrote bg.bmp", os.path.getsize(os.path.join(OUT, "bg.bmp")), "bytes")

# ---------- symbol sheet (60x240, 4 stacked symbols) ----------
order = ["burger", "wings", "coke", "fries"]   # MUST match NAMES in main.py
CELL_SIZE = 48   # tile size in symbols.bmp -- MUST match CELL in main.py

# Use the HI-RES 240x240 source art (frontend/public/symbols/*.png) and
# downsample to CELL_SIZE with LANCZOS for a clean, smooth result. The
# 60x60 versions in symbols/pico60/ were already pre-pixelated, so going
# back to the 240x240 originals gives much sharper symbols on the Pico.
sheet = Image.new("RGB", (CELL_SIZE, CELL_SIZE * len(order)), (0, 0, 0))
for i, name in enumerate(order):
    p_hi = os.path.join(SRC, "symbols", f"{name}.png")          # 240x240
    p_lo = os.path.join(SRC, "symbols", "pico60", f"{name}.png")  # 60x60
    src_path = p_hi if os.path.exists(p_hi) else p_lo
    s = flatten(Image.open(src_path), bg_color=(0, 0, 0))
    if s.size != (CELL_SIZE, CELL_SIZE):
        s = s.resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)
    sheet.paste(s, (0, i * CELL_SIZE))
# 128 colours + NO DITHERING -> clean, flat-shaded cartoon symbols
# (dithering scatters grainy noise pixels which look terrible on a 48px tile).
to_indexed_bmp(sheet, os.path.join(OUT, "symbols.bmp"),
               colors=128, dither=False)
print("wrote symbols.bmp", os.path.getsize(os.path.join(OUT, "symbols.bmp")), "bytes")

print("done ->", OUT)
