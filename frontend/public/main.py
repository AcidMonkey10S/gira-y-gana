"""
================================================================
  RP2040 HDMI SLOT MACHINE  -  "Junk Food Edition"
                                 CircuitPython / picodvi version
                                 *** 3 x 3 grid + on-screen GIRAR ***
================================================================

Hardware  : RP2040 board with PicoDVI sock.
Firmware  : CircuitPython 8.x or newer (must include the `picodvi`
            built-in module). https://circuitpython.org/
Display   : 320 x 240 @ 60 Hz HDMI / DVI via picodvi.Framebuffer
Input     : Momentary push-button between GP25 and GND.

HDMI / DVI pin mapping (matches the project wiring):

      clk_dp  GP14    clk_dn  GP15
      red_dp  GP12    red_dn  GP13
      green   GP18            GP19
      blue    GP16            GP17

Layout    : background image (full 320x240, streamed from flash),
            three reel columns each showing 3 stacked symbols
            (= 9 visible cells), and a big red GIRAR button at the
            bottom that highlights while the wheels are spinning.
            Payline = the middle row.

Game      : every WIN_EVERY-th press is a guaranteed jackpot
            (3-of-a-kind on the middle / payline row). All other
            spins are non-winning.

----------------------------------------------------------------
FILES YOU MUST COPY TO THE CIRCUITPY DRIVE (root):

   /main.py               <-- this file
   /bg.bmp                <-- 320x240 8-bit indexed BMP (the cabinet art)
   /symbols.bmp           <-- 54x216  8-bit indexed BMP (4 stacked tiles)
   /lib/adafruit_imageload/
   /lib/adafruit_display_text/

The two `lib/` folders come from the Adafruit CircuitPython library
bundle that matches your CircuitPython version:
   https://circuitpython.org/libraries

----------------------------------------------------------------
WHY color_depth=8 AND OnDiskBitmap for the background:

  * picodvi.Framebuffer(320, 240, color_depth=16) needs ~165 KB
    contiguous SRAM. RP2040 only has 264 KB total -> can't fit.
    color_depth=8 drops the FB to ~77 KB.
  * Keeping a 320x240 background bitmap ALSO in SRAM does not fit
    next to the FB. We use displayio.OnDiskBitmap for the bg, which
    streams pixels straight from flash (~0 bytes RAM cost).
  * Symbols sheet (54x216 @ 8-bit = ~12 KB) is loaded into SRAM
    because the reel TileGrids change tile indices every animation
    frame -- random access from flash would be too slow.

  RAM budget:
       framebuffer (320x240x8)  ~77 KB
       symbols sheet (54x216)   ~12 KB
       bg (OnDiskBitmap)          0 KB
       everything else           ~5 KB
       --------------------------------
                       total   ~94 KB    (out of 264 KB)
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

CELL = 48                # symbol tile size in symbols.bmp
N_SYM = 4
NAMES = ("BURGER", "WINGS", "COKE", "FRIES")  # MUST match build_pico_assets.py

# 3 x 3 reel grid -- placed UNDER the bg title and ABOVE the GIRAR button
BORDER = 2
COL_GAP = 12
REEL_COL_W = CELL + 2 * BORDER         # 52
REEL_COL_H = 3 * CELL + 2 * BORDER     # 148
TOTAL_W    = 3 * REEL_COL_W + 2 * COL_GAP   # 180

REEL_X_START = (W - TOTAL_W) // 2      # 70
REEL_Y_TOP   = 42                       # clears the bg title at the top
REEL_X = [REEL_X_START + i * (REEL_COL_W + COL_GAP) for i in range(3)]

# big "GIRAR" button at the bottom
BTN_W, BTN_H = 110, 34
BTN_X = (W - BTN_W) // 2
BTN_Y = REEL_Y_TOP + REEL_COL_H + 8     # 198


# -------------------- pre-load BIG bitmaps -------------------------
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


# --- 2. reel-column frame (one shared bitmap, 3 instances) --------
def make_col_frame_bmp():
    f = displayio.Bitmap(REEL_COL_W, REEL_COL_H, 2)
    # top + bottom (BORDER px thick)
    for x in range(REEL_COL_W):
        for t in range(BORDER):
            f[x, t] = 1
            f[x, REEL_COL_H - 1 - t] = 1
    # left + right (BORDER px thick)
    for y in range(REEL_COL_H):
        for t in range(BORDER):
            f[t, y] = 1
            f[REEL_COL_W - 1 - t, y] = 1
    # thin payline marks (between row 1 and row 2 = middle row)
    pay_y = BORDER + CELL          # bottom of top cell / top of middle cell
    for x in range(REEL_COL_W):
        f[x, pay_y] = 1
        f[x, pay_y + CELL - 1] = 1
    return f

col_frame_bmp = make_col_frame_bmp()
col_frame_pal = displayio.Palette(2)
col_frame_pal[0] = 0x000000
col_frame_pal.make_transparent(0)      # let the bg show through inside
col_frame_pal[1] = 0xFFC828            # gold border + payline


# --- 3. three reel columns, each a 1x3 TileGrid -------------------
reel_grids = []
reel_state = []                         # [top, mid, bot] symbol index per reel
for i in range(3):
    g = displayio.Group(x=REEL_X[i], y=REEL_Y_TOP)
    g.append(displayio.TileGrid(col_frame_bmp, pixel_shader=col_frame_pal))

    tg = displayio.TileGrid(
        sheet, pixel_shader=sheet_pal,
        tile_width=CELL, tile_height=CELL,
        width=1, height=3,
        x=BORDER, y=BORDER,
    )
    init = [random.randint(0, N_SYM - 1) for _ in range(3)]
    tg[0, 0] = init[0]
    tg[0, 1] = init[1]
    tg[0, 2] = init[2]

    g.append(tg)
    root.append(g)
    reel_grids.append(tg)
    reel_state.append(init)


# --- 4. GIRAR button --------------------------------------------------
def make_btn_bmp(border_thick=2):
    b = displayio.Bitmap(BTN_W, BTN_H, 3)   # 0=transparent, 1=fill, 2=border
    for y in range(BTN_H):
        for x in range(BTN_W):
            on_border = (
                x < border_thick or x >= BTN_W - border_thick
                or y < border_thick or y >= BTN_H - border_thick
            )
            b[x, y] = 2 if on_border else 1
    return b

btn_bmp = make_btn_bmp()
btn_pal = displayio.Palette(3)
btn_pal[0] = 0x000000
btn_pal.make_transparent(0)
btn_pal[1] = 0xC81428                   # red fill (idle)
btn_pal[2] = 0xFFC828                   # gold border

btn_tg = displayio.TileGrid(btn_bmp, pixel_shader=btn_pal, x=BTN_X, y=BTN_Y)
root.append(btn_tg)

btn_label = label.Label(
    terminalio.FONT, text="GIRAR", color=0xFFFFFF, scale=2,
    anchor_point=(0.5, 0.5),
    anchored_position=(W // 2, BTN_Y + BTN_H // 2),
)
root.append(btn_label)


# --- 5. jackpot message (overlays the GIRAR button when winning) --
# Appended AFTER the button so it draws on top. Empty by default;
# set msg.text on a jackpot to flash a celebration over the button.
msg = label.Label(
    terminalio.FONT, text="", color=0xFFE070, scale=2,
    anchor_point=(0.5, 0.5),
    anchored_position=(W // 2, BTN_Y + BTN_H // 2),
)
root.append(msg)

gc.collect()


# -------------------- helpers -------------------------------------
def set_button_state(spinning):
    """Recolour the GIRAR button to give visual feedback."""
    if spinning:
        btn_pal[1] = 0x6E0814           # darker red while spinning
        btn_label.color = 0xFFC828
    else:
        btn_pal[1] = 0xC81428           # idle red
        btn_label.color = 0xFFFFFF


def update_reel(r, syms):
    """Push the 3 symbol indices into reel `r`'s TileGrid + cache."""
    reel_state[r] = syms
    tg = reel_grids[r]
    tg[0, 0] = syms[0]
    tg[0, 1] = syms[1]
    tg[0, 2] = syms[2]


# -------------------- game ----------------------------------------
def pick_finals(spin_idx):
    """Return [s0, s1, s2] for the MIDDLE (payline) row.
    Every WIN_EVERY-th call is a forced 3-of-a-kind."""
    if spin_idx > 0 and spin_idx % WIN_EVERY == 0:
        s = random.randint(0, N_SYM - 1)
        return [s, s, s]
    while True:
        r = [random.randint(0, N_SYM - 1) for _ in range(3)]
        if not (r[0] == r[1] == r[2]):
            return r


def play_spin(spin_idx):
    finals_mid = pick_finals(spin_idx)

    set_button_state(spinning=True)
    msg.text = ""

    locked = [False, False, False]
    # stop the reels one after the other for a classic feel
    stop_at = [time.monotonic() + d for d in (0.7, 1.1, 1.5)]

    while not all(locked):
        now = time.monotonic()
        for r in range(3):
            if locked[r]:
                continue
            if now >= stop_at[r]:
                # final symbols: middle row = winning symbol;
                # top/bot are random non-matches for visual variety
                mid = finals_mid[r]
                top = (mid + random.randint(1, N_SYM - 1)) % N_SYM
                bot = (mid + random.randint(1, N_SYM - 1)) % N_SYM
                update_reel(r, [top, mid, bot])
                locked[r] = True
            else:
                # animate: shift reel up by 1, drop a new symbol at bottom
                cur = reel_state[r]
                update_reel(r, [cur[1], cur[2], random.randint(0, N_SYM - 1)])
        time.sleep(0.06)

    set_button_state(spinning=False)

    # jackpot? (3-of-a-kind on the middle / payline row)
    if finals_mid[0] == finals_mid[1] == finals_mid[2]:
        btn_label.text = ""           # hide GIRAR so msg can take over the button
        msg.text = "JACKPOT! " + NAMES[finals_mid[0]]
        for i in range(10):
            msg.color = 0xFF2020 if i % 2 == 0 else 0xFFC828
            btn_pal[1] = 0xFFC828 if i % 2 == 0 else 0xC81428    # button flashes too
            time.sleep(0.15)
        msg.color = 0xFFE070
        time.sleep(0.6)
        msg.text = ""
        btn_label.text = "GIRAR"
        btn_pal[1] = 0xC81428
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
