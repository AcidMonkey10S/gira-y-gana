"""
================================================================
  RP2040 HDMI SLOT MACHINE  -  "Junk Food Edition"
                                 CircuitPython / picodvi version
                                 *** with full PNG artwork ***
================================================================

Hardware  : RP2040 board with PicoDVI sock (Adafruit Feather RP2040 DVI,
            Pimoroni Pico DV, Pico + Adafruit DVI sock).
Firmware  : CircuitPython 8.x or newer (must include the `picodvi`
            built-in module). https://circuitpython.org/
Display   : 320 x 240 @ 60 Hz HDMI / DVI via picodvi.Framebuffer
Input     : Momentary push-button between GP25 and GND.

HDMI / DVI pin mapping (matches the project wiring):

      clk_dp  GP14    clk_dn  GP15
      red_dp  GP12    red_dn  GP13
      green   GP18            GP19
      blue    GP16            GP17

Game      : 3 reels, single GIRAR button.
            Symbols: BURGER, WINGS, COKE, FRIES (real PNG artwork).
            Every WIN_EVERY-th spin -> guaranteed 3-of-a-kind (jackpot).
            All other spins are non-winning.

----------------------------------------------------------------
FILES YOU MUST COPY TO THE CIRCUITPY DRIVE (root):

   /main.py               <-- this file
   /bg.bmp                <-- 320x240 8-bit indexed BMP (the cabinet art)
   /symbols.bmp           <-- 60x240  8-bit indexed BMP (4 stacked tiles)
   /lib/adafruit_imageload/
   /lib/adafruit_display_text/

The two `lib/` folders come from the Adafruit CircuitPython library
bundle that matches your CircuitPython version:
   https://circuitpython.org/libraries
Just drop the matching folders into /lib/ on the CIRCUITPY drive.

----------------------------------------------------------------
WHY color_depth=8 AND OnDiskBitmap for the background:

   * picodvi.Framebuffer(320, 240, color_depth=16) needs ~165 KB
     contiguous SRAM. The RP2040 only has 264 KB total. After
     CircuitPython + displayio is loaded, there isn't enough
     contiguous heap left, hence the original
     `MemoryError: allocating 165132 bytes`.
     Going to color_depth=8 drops the framebuffer to ~77 KB.

   * Even at color_depth=8, ALSO loading a 320x240 background
     bitmap into RAM (another 76 KB) does not fit. And after
     loading any partial bg, the heap fragments so badly that
     even the small (14 KB) symbols sheet can no longer be
     allocated.
     -> the background is loaded with `displayio.OnDiskBitmap`,
        which streams pixels straight from flash and uses ~0
        bytes of SRAM. That leaves the heap clean for the
        symbols sheet.

   Effective RAM budget:
       framebuffer (320x240x8)  ~77 KB
       symbols sheet (60x240x8) ~14 KB
       bg (OnDiskBitmap)          0 KB
       everything else           ~5 KB
       --------------------------------
                       total   ~96 KB    (out of 264 KB)
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
import adafruit_imageload
from adafruit_display_text import label


# -------------------- display --------------------------------------
# Free as much contiguous heap as possible BEFORE asking picodvi
# for its framebuffer (it needs one big aligned chunk + DMA scratch).
displayio.release_displays()
gc.collect()

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

CELL = 60                # symbol size in px (tile size inside symbols.bmp)
N_SYM = 4
NAMES = ("BURGER", "WINGS", "COKE", "FRIES")  # MUST match the order used
                                              # by build_pico_assets.py

REEL_W = 70
REEL_H = 70
GAP    = 14
TOTAL_W = 3 * REEL_W + 2 * GAP
REEL_TOP = (H - REEL_H) // 2 + 6
REEL_X = [(W - TOTAL_W) // 2 + i * (REEL_W + GAP) for i in range(3)]


# -------------------- pre-load BIG bitmaps -------------------------
# Strategy:
#   * The background is the biggest piece of art (320x240). We load it
#     with displayio.OnDiskBitmap, which streams pixels from flash and
#     uses ~0 bytes of SRAM. That keeps the heap clean.
#   * The symbol sheet (60x240, ~14 KB) is loaded into RAM with
#     adafruit_imageload because the reel TileGrids change tile indices
#     every animation frame -- random access from flash would be slow.
gc.collect()
bg_bmp = displayio.OnDiskBitmap("/bg.bmp")     # 0 RAM, just a file handle
gc.collect()
sheet, sheet_pal = adafruit_imageload.load(
    "/symbols.bmp",
    bitmap=displayio.Bitmap,
    palette=displayio.Palette,
)
gc.collect()


# -------------------- scene ----------------------------------------
root = displayio.Group()
display.root_group = root


# --- 1. background image (full 320x240, streamed from flash) ------
root.append(displayio.TileGrid(bg_bmp, pixel_shader=bg_bmp.pixel_shader))


# --- 2. yellow reel-window borders --------------------------------
def make_frame_bitmap():
    f = displayio.Bitmap(REEL_W, REEL_H, 2)
    # top + bottom (2 px thick)
    for x in range(REEL_W):
        f[x, 0] = 1
        f[x, 1] = 1
        f[x, REEL_H - 1] = 1
        f[x, REEL_H - 2] = 1
    # left + right (2 px thick)
    for y in range(REEL_H):
        f[0, y] = 1
        f[1, y] = 1
        f[REEL_W - 1, y] = 1
        f[REEL_W - 2, y] = 1
    return f

frame_bmp = make_frame_bitmap()
frame_pal = displayio.Palette(2)
frame_pal[0] = 0x000000
frame_pal.make_transparent(0)   # let the background show through
frame_pal[1] = 0xFFC828         # gold border


# --- 3. three reels (use the pre-loaded `sheet`) ------------------
reels = []
for i in range(3):
    g = displayio.Group(x=REEL_X[i], y=REEL_TOP)
    g.append(displayio.TileGrid(frame_bmp, pixel_shader=frame_pal))

    tg = displayio.TileGrid(
        sheet, pixel_shader=sheet_pal,
        tile_width=CELL, tile_height=CELL,
        width=1, height=1,
        x=(REEL_W - CELL) // 2, y=(REEL_H - CELL) // 2,
    )
    tg[0, 0] = i % N_SYM        # initial preview symbol
    g.append(tg)

    root.append(g)
    reels.append(tg)


# --- 4. message line (jackpot text) -------------------------------
msg = label.Label(
    terminalio.FONT, text="", color=0xFFE070, scale=2,
    anchor_point=(0.5, 1.0),
    anchored_position=(W // 2, H - 8),
)
root.append(msg)

gc.collect()


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
    # stop the reels one after the other for a classic feel
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
        for i in range(10):
            msg.color = 0xFF2020 if i % 2 == 0 else 0xFFC828
            time.sleep(0.15)
        msg.color = 0xFFE070
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
