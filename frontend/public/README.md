# RP2040 HDMI Slot Machine — CircuitPython / picodvi

A 3-reel "junk food" slot machine that runs on an **RP2040** with a
**PicoDVI** HDMI/DVI output, written in **CircuitPython** using the
built-in `picodvi` module.

Symbols: **Burger, Wings, Coke, Fries**.
Input: **one** push-button.
Win logic: every **50th** press is a guaranteed 3-of-a-kind.

---

## 1. Hardware

| Part | Notes |
|---|---|
| RP2040 board with PicoDVI | e.g. Adafruit Feather RP2040 DVI, or Pico + Adafruit DVI sock |
| HDMI / DVI cable + monitor or TV | Any HDMI display |
| Momentary push-button | Normally-open tactile button |
| 2 × Dupont jumper wires | For the button |

### Wiring

The `picodvi.Framebuffer` uses GP12 through GP19 for the HDMI signal,
so the button can **not** sit on GP15 anymore. It's now on **GP25**
(change the constant in `main.py` if you prefer another free pin).

| Signal       | Pico pin | Connect to                |
|--------------|----------|----------------------------|
| HDMI clk_dp  | GP14     | DVI sock                  |
| HDMI clk_dn  | GP15     | DVI sock                  |
| HDMI red_dp  | GP12     | DVI sock                  |
| HDMI red_dn  | GP13     | DVI sock                  |
| HDMI green   | GP18 / GP19 | DVI sock              |
| HDMI blue    | GP16 / GP17 | DVI sock              |
| **GIRAR button** | **GP25** | one side of the button |
| GND          | GND      | other side of the button  |

```
   Pico                                  Button (push-to-close)
  ┌──────────┐                          ┌────────┐
  │  GP25    ├──────────────────────────┤        │
  │          │                          │ GIRAR  │
  │  GND     ├──────────────────────────┤        │
  └──────────┘                          └────────┘
```

The internal pull-up is enabled in code, so the button only needs to
short GP25 to GND when pressed.

---

## 2. Firmware

You need **CircuitPython 8.x or newer** with the `picodvi` built-in
module compiled in (Adafruit ship this in their official builds for
the Feather RP2040 DVI, the Pico DVI base, and similar).

1. Hold **BOOTSEL** on the Pico, plug it in via USB.
2. The `RPI-RP2` drive appears.
3. Download the matching CircuitPython UF2 from
   <https://circuitpython.org/board/adafruit_feather_rp2040_dvi/>
   (or whichever board you have) and drag it onto `RPI-RP2`.
4. After reboot the board mounts as **CIRCUITPY**.

You also need the `adafruit_display_text` library. The simplest way:
1. Download the latest "Library Bundle" from
   <https://circuitpython.org/libraries>
2. Copy `adafruit_display_text/` from the bundle into the `lib/`
   folder of the `CIRCUITPY` drive.

---

## 3. Install the game

1. Click ⬇ **DOWNLOAD main.py** below the simulator (or copy
   `/app/frontend/public/main.py`).
2. Save it onto the **CIRCUITPY** drive as `code.py` (CircuitPython's
   auto-run entry point) — or as `main.py` if you've configured it.
3. The board reboots automatically. The slot machine appears on the
   HDMI screen.

That's it.

---

## 4. How to play

- Press **GIRAR** (the button on GP25) to spin the three reels.
- They stop one after the other, classic slot-machine style.
- **Every 50th press is a guaranteed 3-of-a-kind.** When it lands the
  "GIRA Y GANA" headline flashes red/gold and the winning symbol's
  name is announced (`JACKPOT! BURGER`, etc.).
- Pairs do **not** count as wins — only 3 matching symbols.

---

## 5. Customisation tips

- **Different button pin?** Change `board.GP25` in `main.py`.
- **Change win frequency?** Edit `WIN_EVERY = 50`.
- **Different colours?** Edit the `pal[i] = 0xRRGGBB` lines near the
  shared palette block.
- **Use photo PNGs** like in the simulator? The pixel-art symbols are
  drawn at boot time; replacing them with PNGs would require the
  `adafruit_imageload` library and converting each PNG to a 60×60
  indexed BMP. Ping me if you want a version that does that.

Enjoy! 🍔🍗🥤🍟
