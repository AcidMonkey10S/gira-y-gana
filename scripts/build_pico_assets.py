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
import numpy as np
from scipy import ndimage
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


def remove_bg_flood(img, brightness_thresh=170, neutral_tol=25):
    """Strip the white / light-grey background from a symbol image.

    Many of the source PNGs and JPGs that LOOK transparent actually have
    a checkerboard pattern (alternating ~255 and ~200 grey) baked into
    the RGB data, plus alpha=255 everywhere. Plain near-white thresholding
    misses the grey squares.

    Strategy:
      1. classify every pixel as "background-coloured" if it is bright
         AND neutral (R, G, B within `neutral_tol` of each other).
      2. flood-fill from the four image edges through connected bg pixels.
      3. only pixels CONNECTED to the edge become alpha=0 -- so interior
         white highlights (sesame seeds, fry creases) stay opaque.
    """
    rgba = img.convert("RGBA")
    arr  = np.array(rgba)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    is_bg = (
        (r >= brightness_thresh) &
        (g >= brightness_thresh) &
        (b >= brightness_thresh) &
        (np.maximum.reduce([r, g, b]) - np.minimum.reduce([r, g, b])
         <= neutral_tol)
    )
    labeled, _ = ndimage.label(is_bg)
    edges = np.concatenate([
        labeled[0, :], labeled[-1, :], labeled[:, 0], labeled[:, -1]
    ])
    edge_labels = set(int(v) for v in edges if v != 0)
    if edge_labels:
        final_bg = np.isin(labeled, list(edge_labels))
        arr[:, :, 3] = np.where(final_bg, 0, arr[:, :, 3])
    return Image.fromarray(arr, "RGBA")


def load_symbol(path):
    """Open a symbol file and ALWAYS run edge-flood background removal.
    Don't trust the file's alpha channel -- many "transparent" PNGs
    are actually opaque with a baked-in checkerboard."""
    return remove_bg_flood(Image.open(path))


def auto_crop(rgba, padding=6):
    """Crop tight around the visible (non-transparent) art, square pad."""
    bbox = rgba.getbbox()
    if bbox is None:
        return rgba
    rgba = rgba.crop(bbox)
    w, h = rgba.size
    side = max(w, h) + 2 * padding
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(rgba, ((side - w) // 2, (side - h) // 2), rgba)
    return canvas


def to_indexed_bmp(rgb_img, out_path, colors=256, dither=True):
    """Quantize to <= `colors` palette and save as 8-bit indexed BMP."""
    p = rgb_img.quantize(
        colors=colors,
        method=Image.MEDIANCUT,
        dither=Image.FLOYDSTEINBERG if dither else Image.NONE,
    )
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

# Build the symbol sheet:
#  * load each symbol from frontend/public/symbols/{name}.{png,jpg}
#  * for JPG (no alpha) treat near-white as transparent
#  * auto-crop tight around the artwork + small padding so the icon
#    fills the cell instead of floating in dead space
#  * downsample to CELL_SIZE with LANCZOS for a smooth result
sheet = Image.new("RGB", (CELL_SIZE, CELL_SIZE * len(order)), (0, 0, 0))

def find_source(name):
    """Look for {name}.png then {name}.jpg, fall back to pico60/{name}.png."""
    for ext in ("png", "jpg", "jpeg"):
        p = os.path.join(SRC, "symbols", f"{name}.{ext}")
        if os.path.exists(p):
            return p
    return os.path.join(SRC, "symbols", "pico60", f"{name}.png")

for i, name in enumerate(order):
    src_path = find_source(name)
    rgba = load_symbol(src_path)
    rgba = auto_crop(rgba, padding=6)
    rgba = rgba.resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)
    s = flatten(rgba, bg_color=(0, 0, 0))
    sheet.paste(s, (0, i * CELL_SIZE))
# 128 colours + NO DITHERING -> clean, flat-shaded cartoon symbols
# (dithering scatters grainy noise pixels which look terrible on a 48px tile).
to_indexed_bmp(sheet, os.path.join(OUT, "symbols.bmp"),
               colors=128, dither=False)
print("wrote symbols.bmp", os.path.getsize(os.path.join(OUT, "symbols.bmp")), "bytes")

print("done ->", OUT)
