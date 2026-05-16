# Pico flash bundle — Junk Food Edition

Drop the contents of this folder onto the **`CIRCUITPY`** drive that
appears when your RP2040 board boots into CircuitPython.

```
CIRCUITPY/
├── main.py                 <-- from this folder
├── bg.bmp                  <-- from this folder (320x240 indexed BMP)
├── symbols.bmp             <-- from this folder (60x240  indexed BMP)
└── lib/
    ├── adafruit_imageload/         <-- from the Adafruit library bundle
    └── adafruit_display_text/      <-- from the Adafruit library bundle
```

## 1. CircuitPython firmware

You need a CircuitPython UF2 build for your specific board that
includes the **`picodvi`** module (CircuitPython 8.x or newer).
Get it from <https://circuitpython.org/downloads> — search for your
RP2040 board and pick the latest stable build.

Flash by holding **BOOTSEL**, plugging in USB, and dragging the
UF2 to the `RPI-RP2` drive.

## 2. Required libraries

Download the matching **CircuitPython library bundle** from
<https://circuitpython.org/libraries> and copy these two folders into
`CIRCUITPY/lib/`:

* `adafruit_imageload/`
* `adafruit_display_text/`

## 3. Hardware

Pin map (matches `main.py`):

| Signal      | Pin   |
|-------------|-------|
| HDMI clk_dp | GP14  |
| HDMI clk_dn | GP15  |
| HDMI red_dp | GP12  |
| HDMI red_dn | GP13  |
| HDMI green  | GP18 / GP19 |
| HDMI blue   | GP16 / GP17 |
| GIRAR button | **GP25** to **GND** (internal pull-up) |

## 4. Regenerating the assets

If you tweak `bg.png` or any symbol PNG, regenerate the BMPs:

```bash
python3 scripts/build_pico_assets.py
```

This rewrites `bg.bmp` and `symbols.bmp` in this folder.

## 5. Memory note (the original error)

The original `main.py` allocated a `picodvi.Framebuffer` with
`color_depth=16`, which needs ~165 KB contiguous SRAM. A plain RP2040
only has 264 KB total and after CircuitPython + displayio there is
not enough contiguous heap left, hence:

```
MemoryError: memory allocation failed, allocating 165132 bytes
```

This build uses `color_depth=8` (~77 KB framebuffer, ~90 KB total) and
calls `gc.collect()` immediately before the allocation. The palette
contains far fewer than 256 colours so 8-bit indexed is plenty.
