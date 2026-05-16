"""Render a static 320x240 preview that mimics what the Pico will show.
Saves to frontend/public/circuitpython/preview.png so you can eyeball
the layout without flashing the board."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART  = os.path.join(ROOT, "frontend", "public")
OUT  = os.path.join(ART, "circuitpython", "preview.png")

W, H = 320, 240
CELL = 48
BORDER = 2
COL_GAP = 12
REEL_COL_W = CELL + 2 * BORDER
REEL_COL_H = 3 * CELL + 2 * BORDER
TOTAL_W = 3 * REEL_COL_W + 2 * COL_GAP
REEL_X_START = (W - TOTAL_W) // 2
REEL_Y_TOP = 42
BTN_W, BTN_H = 110, 34
BTN_X = (W - BTN_W) // 2
BTN_Y = REEL_Y_TOP + REEL_COL_H + 8

# load bg.bmp (the Pico will show exactly this)
bg = Image.open(os.path.join(ART, "circuitpython", "bg.bmp")).convert("RGB")
canvas = bg.copy().resize((W, H))
draw = ImageDraw.Draw(canvas, "RGBA")

# load symbols.bmp tiles
sheet = Image.open(os.path.join(ART, "circuitpython", "symbols.bmp")).convert("RGB")
tiles = [sheet.crop((0, i * CELL, CELL, (i + 1) * CELL)) for i in range(4)]

# draw 3x3 reels with gold borders (transparent inside)
for c in range(3):
    x0 = REEL_X_START + c * (REEL_COL_W + COL_GAP)
    y0 = REEL_Y_TOP
    # paste a sample symbol per cell
    for r in range(3):
        sym = (c + r) % 4
        canvas.paste(tiles[sym],
                     (x0 + BORDER, y0 + BORDER + r * CELL))
    # gold border around the column
    draw.rectangle([x0, y0, x0 + REEL_COL_W - 1, y0 + REEL_COL_H - 1],
                   outline=(255, 200, 40), width=BORDER)
    # payline marks (top + bottom of middle cell)
    pay_y_top = y0 + BORDER + CELL
    pay_y_bot = pay_y_top + CELL - 1
    draw.line([x0, pay_y_top, x0 + REEL_COL_W - 1, pay_y_top], fill=(255, 200, 40), width=1)
    draw.line([x0, pay_y_bot, x0 + REEL_COL_W - 1, pay_y_bot], fill=(255, 200, 40), width=1)

# GIRAR button
draw.rectangle([BTN_X, BTN_Y, BTN_X + BTN_W - 1, BTN_Y + BTN_H - 1],
               fill=(200, 20, 40), outline=(255, 200, 40), width=2)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
except Exception:
    font = ImageFont.load_default()
text = "GIRAR"
bbox = draw.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text((BTN_X + (BTN_W - tw) // 2 - bbox[0],
           BTN_Y + (BTN_H - th) // 2 - bbox[1]),
          text, fill=(255, 255, 255), font=font)

canvas.save(OUT)
print("preview ->", OUT)
