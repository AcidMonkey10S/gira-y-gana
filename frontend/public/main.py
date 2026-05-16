"""
================================================================
  RP2040 HDMI SLOT MACHINE  -  "Junk Food Edition"
                                 CircuitPython / picodvi version
================================================================

Hardware  : RP2040 board with PicoDVI sock (e.g. Adafruit Feather
            RP2040 DVI, Pimoroni Pico DV, Pico + Adafruit DVI sock)
Firmware  : CircuitPython 8.x or newer  (must include the `picodvi`
            built-in module).  Get it from circuitpython.org.
Display   : 320 x 240 @ 60 Hz HDMI / DVI via picodvi.Framebuffer
Input     : One momentary push-button between GP25 and GND.
            (GP15 is used by HDMI clock, so the button cannot live
             there anymore - GP25 is free and easy to wire on most
             RP2040 boards.)

HDMI / DVI pin mapping (matches your wiring):

      clk_dp  GP14    clk_dn  GP15
      red_dp  GP12    red_dn  GP13
      green   GP18            GP19
      blue    GP16            GP17

Game      : 3 reels, single GIRAR button.
            Symbols: BURGER, WINGS, COKE, FRIES
            Every 50th spin -> guaranteed 3-of-a-kind (jackpot).
            All other spins are non-winning.

Install:
  1. Flash a CircuitPython UF2 build that supports `picodvi`
     onto the Pico (drag/drop while holding BOOTSEL).
  2. The board mounts as `CIRCUITPY`.
  3. Copy this file as `code.py` (or `main.py`) to the root of
     the CIRCUITPY drive.
  4. Done. Press the button to play.
================================================================
"""

import gc
import board
import digitalio
import displayio
import framebufferio
import picodvi
import random
import time
import terminalio
from adafruit_display_text import label


# -------------------- display --------------------------------------
# Free as much contiguous heap as possible BEFORE asking picodvi
# for its framebuffer (it needs one big aligned chunk + DMA scratch).
displayio.release_displays()
gc.collect()

# NOTE on memory:
#   320 x 240 @ color_depth=16 => 153,600 byte FB + DMA scratch
#                                 (~165 KB total) -> won't fit on a
#                                 plain RP2040 (264 KB SRAM) once
#                                 CircuitPython + displayio are loaded.
#   320 x 240 @ color_depth=8  =>  76,800 byte FB (~90 KB total) -> fits.
# The palette has <16 colours, so 8-bit indexed is plenty.
fb = picodvi.Framebuffer(
    320, 240,
    clk_dp=board.GP14, clk_dn=board.GP15,
    red_dp=board.GP12, red_dn=board.GP13,
    green_dp=board.GP18, green_dn=board.GP19,
    blue_dp=board.GP16, blue_dn=board.GP17,
    color_depth=8,
)
display = framebufferio.FramebufferDisplay(fb)
W, H = 320, 240


# -------------------- input ----------------------------------------
btn = digitalio.DigitalInOut(board.GP25)
btn.direction = digitalio.Direction.INPUT
btn.pull = digitalio.Pull.UP


# -------------------- game tuning ----------------------------------
WIN_EVERY = 50           # guaranteed 3-of-a-kind every Nth press

CELL = 60                # symbol size in px
REEL_W = 70
REEL_H = 70
GAP    = 14
TOTAL_W = 3 * REEL_W + 2 * GAP
REEL_TOP = (H - REEL_H) // 2 + 6
REEL_X = [(W - TOTAL_W) // 2 + i * (REEL_W + GAP) for i in range(3)]


# -------------------- pixel drawing helpers ------------------------
def fill_rect(bmp, x, y, w, h, c):
    for j in range(h):
        yy = y + j
        if 0 <= yy < bmp.height:
            for i in range(w):
                xx = x + i
                if 0 <= xx < bmp.width:
                    bmp[xx, yy] = c

def fill_circle(bmp, cx, cy, r, c):
    r2 = r * r
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            if i * i + j * j <= r2:
                xx, yy = cx + i, cy + j
                if 0 <= xx < bmp.width and 0 <= yy < bmp.height:
                    bmp[xx, yy] = c


# -------------------- shared symbol bitmap -------------------------
# One big bitmap holding all 4 symbols stacked vertically. A TileGrid
# with tile_height=CELL then just picks which tile (= which symbol)
# to display per reel - this is the displayio-idiomatic way and avoids
# allocating a fresh bitmap every frame.
N_SYM = 4
sheet = displayio.Bitmap(CELL, CELL * N_SYM, 16)
pal = displayio.Palette(16)
# shared palette across all symbols
pal[0]  = 0x000000   # background (black)
pal[1]  = 0xDCAA64   # bun tan
pal[2]  = 0xFFFFFF   # white (seeds, bone tip, stripes)
pal[3]  = 0x3CB446   # lettuce green
pal[4]  = 0xFAC828   # cheese / fries yellow
pal[5]  = 0x78461E   # patty / meat brown
pal[6]  = 0xE68228   # crispy orange
pal[7]  = 0xBEBEBE   # bone grey
pal[8]  = 0x820A14   # coke dark red
pal[9]  = 0xDC1E28   # coke red swoosh
pal[10] = 0xFBD24A   # lighter fries
pal[11] = 0xD9A418   # fry tips
pal[12] = 0xFFC828   # gold (used by flash)

NAMES = ("BURGER", "WINGS", "COKE", "FRIES")

def draw_burger(yoff):
    fill_rect(sheet, 6,  yoff + 8,  48, 14, 1)
    fill_circle(sheet, 30, yoff + 12, 22, 1)
    for sx, sy in ((18, 10), (30, 6), (42, 10)):
        sheet[sx, yoff + sy] = 2
        sheet[sx + 1, yoff + sy] = 2
        sheet[sx, yoff + sy + 1] = 2
    fill_rect(sheet, 4, yoff + 22, 52, 6, 3)
    fill_rect(sheet, 4, yoff + 28, 52, 5, 4)
    fill_rect(sheet, 4, yoff + 33, 52, 10, 5)
    fill_rect(sheet, 6, yoff + 43, 48, 10, 1)

def draw_wings(yoff):
    fill_circle(sheet, 22, yoff + 22, 16, 5)
    fill_circle(sheet, 16, yoff + 30, 12, 5)
    fill_circle(sheet, 22, yoff + 22, 11, 6)
    fill_rect(sheet, 28, yoff + 30, 22, 6, 7)
    fill_circle(sheet, 50, yoff + 28, 6, 7)
    fill_circle(sheet, 50, yoff + 36, 6, 7)
    fill_circle(sheet, 50, yoff + 28, 4, 2)
    fill_circle(sheet, 50, yoff + 36, 4, 2)

def draw_coke(yoff):
    fill_rect(sheet, 24, yoff + 4,  12, 8,  8)
    fill_rect(sheet, 20, yoff + 12, 20, 6,  8)
    fill_rect(sheet, 14, yoff + 18, 32, 36, 8)
    fill_rect(sheet, 22, yoff + 2,  16, 4,  4)
    fill_rect(sheet, 14, yoff + 30, 32, 12, 2)
    fill_rect(sheet, 17, yoff + 33, 26, 3,  9)
    fill_rect(sheet, 17, yoff + 38, 26, 2,  9)

def draw_fries(yoff):
    fill_rect(sheet, 16, yoff + 6,  5, 22, 4)
    fill_rect(sheet, 22, yoff + 2,  5, 26, 10)
    fill_rect(sheet, 28, yoff + 6,  5, 22, 4)
    fill_rect(sheet, 34, yoff + 3,  5, 25, 10)
    fill_rect(sheet, 40, yoff + 8,  5, 20, 4)
    for x in (16, 22, 28, 34, 40):
        fill_rect(sheet, x, yoff + 2 if x in (22, 34) else yoff + (6 if x in (16,28) else 8), 5, 3, 11)
    fill_rect(sheet, 10, yoff + 26, 42, 4, 8)    # carton top lip
    fill_rect(sheet, 12, yoff + 30, 38, 24, 9)   # carton body red
    fill_rect(sheet, 16, yoff + 30, 3, 24, 2)    # white stripes
    fill_rect(sheet, 25, yoff + 30, 3, 24, 2)
    fill_rect(sheet, 34, yoff + 30, 3, 24, 2)
    fill_rect(sheet, 43, yoff + 30, 3, 24, 2)

# bake the four symbols into the sheet
draw_burger(0 * CELL)
draw_wings (1 * CELL)
draw_coke  (2 * CELL)
draw_fries (3 * CELL)


# -------------------- scene ----------------------------------------
root = displayio.Group()
display.root_group = root

# solid dark background
bg_bmp = displayio.Bitmap(W, H, 1)
bg_pal = displayio.Palette(1)
bg_pal[0] = 0x140014
root.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_pal))

# headline
title = label.Label(
    terminalio.FONT, text="GIRA  Y  GANA",
    color=0xFFC828, scale=2,
    anchor_point=(0.5, 0.0),
    anchored_position=(W // 2, 6),
)
root.append(title)

# 3 reels - each is a small group with a yellow border + a TileGrid
# pointing to ONE tile (60x60) inside the shared sheet.
reels = []
for i in range(3):
    g = displayio.Group(x=REEL_X[i], y=REEL_TOP)

    # border bitmap (just 4 edges)
    frame_bmp = displayio.Bitmap(REEL_W, REEL_H, 2)
    frame_pal = displayio.Palette(2)
    frame_pal[0] = 0x000000
    frame_pal[1] = 0xFFC828
    fill_rect(frame_bmp, 0, 0, REEL_W, 2, 1)
    fill_rect(frame_bmp, 0, REEL_H - 2, REEL_W, 2, 1)
    fill_rect(frame_bmp, 0, 0, 2, REEL_H, 1)
    fill_rect(frame_bmp, REEL_W - 2, 0, 2, REEL_H, 1)
    g.append(displayio.TileGrid(frame_bmp, pixel_shader=frame_pal))

    # the symbol tile - a 1x1 grid that selects which 60x60 slice of
    # `sheet` to draw at the centre of the reel
    tg = displayio.TileGrid(
        sheet, pixel_shader=pal,
        tile_width=CELL, tile_height=CELL,
        width=1, height=1,
        x=(REEL_W - CELL) // 2, y=(REEL_H - CELL) // 2,
    )
    tg[0, 0] = i % N_SYM     # initial preview symbol
    g.append(tg)

    root.append(g)
    reels.append(tg)

# message line (hidden when empty)
msg = label.Label(
    terminalio.FONT, text="", color=0xFFE070, scale=2,
    anchor_point=(0.5, 1.0),
    anchored_position=(W // 2, H - 8),
)
root.append(msg)


# -------------------- game ----------------------------------------
def pick_finals(spin_idx):
    """Return [s0, s1, s2]; every WIN_EVERY-th call is a forced triple."""
    if spin_idx > 0 and spin_idx % WIN_EVERY == 0:
        s = random.randint(0, N_SYM - 1)
        return [s, s, s]
    while True:
        r = [random.randint(0, N_SYM - 1) for _ in range(3)]
        if not (r[0] == r[1] == r[2]):
            return r


def play_spin(spin_idx):
    finals = pick_finals(spin_idx)

    locked = [False, False, False]
    # stop the reels one after the other, classic feel
    stop_at = [time.monotonic() + d for d in (0.7, 1.1, 1.5)]

    while not all(locked):
        now = time.monotonic()
        for r in range(3):
            if locked[r]:
                continue
            if now >= stop_at[r]:
                reels[r][0, 0] = finals[r]
                locked[r] = True
            else:
                reels[r][0, 0] = random.randint(0, N_SYM - 1)
        time.sleep(0.06)

    # 3-of-a-kind?
    if finals[0] == finals[1] == finals[2]:
        msg.text = "JACKPOT! " + NAMES[finals[0]]
        # flash the headline for ~1.5 s
        for i in range(10):
            title.color = 0xFF2020 if i % 2 == 0 else 0xFFC828
            time.sleep(0.15)
        title.color = 0xFFC828
        time.sleep(0.6)
        msg.text = ""
    # losing spin: stay silent


# -------------------- main loop -----------------------------------
spin_index = 0
while True:
    # wait for press (button is active-LOW, internal pull-up)
    while btn.value:
        time.sleep(0.02)
    time.sleep(0.04)            # debounce

    spin_index += 1
    play_spin(spin_index)

    # wait for release before accepting another press
    while not btn.value:
        time.sleep(0.02)
    time.sleep(0.10)
