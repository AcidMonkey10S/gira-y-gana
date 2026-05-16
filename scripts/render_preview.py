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
COL_GAP = 14
REEL_COL_W = CELL + 2 * BORDER
REEL_COL_H = 3 * CELL + 2 * BORDER
TOTAL_W = 3 * REEL_COL_W + 2 * COL_GAP
REEL_X_START = (W - TOTAL_W) // 2
REEL_Y_TOP = 44
BTN_W, BTN_H = 140, 40
BTN_X = (W - BTN_W) // 2
BTN_Y = REEL_Y_TOP + REEL_COL_H + 6

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

# GIRAR button (rounded pill)
BTN_R = 16
draw.rounded_rectangle([BTN_X, BTN_Y, BTN_X + BTN_W - 1, BTN_Y + BTN_H - 1],
                       radius=BTN_R, fill=(200, 20, 40),
                       outline=(255, 200, 40), width=2)

# Gold payline arrows (shaft + arrowhead) pointing at the middle row
ARROW_W, ARROW_H = 28, 14
ARROW_HEAD_W = 12
ARROW_SHAFT_T = 4
arrow_y_center = REEL_Y_TOP + BORDER + CELL + CELL // 2
arrow_y_top = arrow_y_center - ARROW_H // 2
last_reel_end = REEL_X_START + 3 * REEL_COL_W + 2 * COL_GAP
GOLD = (255, 200, 40)
shaft_y0 = arrow_y_top + (ARROW_H - ARROW_SHAFT_T) // 2

# left arrow: ===> (shaft on left, triangle head on right)
lx = REEL_X_START - ARROW_W - 4
draw.rectangle([lx, shaft_y0,
                lx + (ARROW_W - ARROW_HEAD_W) - 1, shaft_y0 + ARROW_SHAFT_T - 1],
               fill=GOLD)
draw.polygon(
    [(lx + (ARROW_W - ARROW_HEAD_W), arrow_y_top),
     (lx + (ARROW_W - ARROW_HEAD_W), arrow_y_top + ARROW_H - 1),
     (lx + ARROW_W - 1, arrow_y_top + ARROW_H // 2)],
    fill=GOLD)

# right arrow: <=== (triangle head on left, shaft on right)
rx = last_reel_end + 4
draw.polygon(
    [(rx + ARROW_HEAD_W - 1, arrow_y_top),
     (rx + ARROW_HEAD_W - 1, arrow_y_top + ARROW_H - 1),
     (rx, arrow_y_top + ARROW_H // 2)],
    fill=GOLD)
draw.rectangle([rx + ARROW_HEAD_W, shaft_y0,
                rx + ARROW_W - 1, shaft_y0 + ARROW_SHAFT_T - 1],
               fill=GOLD)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
except Exception:
    font = ImageFont.load_default()
text = "GIRAR"
bbox = draw.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text((BTN_X + (BTN_W - tw) // 2 - bbox[0],
           BTN_Y + (BTN_H - th) // 2 - bbox[1]),
          text, fill=(0, 0, 0), font=font)

canvas.save(OUT)
print("preview ->", OUT)
