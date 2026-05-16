import { useEffect, useRef, useState, useCallback } from "react";

/* ------------------------------------------------------------------ */
/*  Pixel-art SVG symbols - matches the MicroPython draw_* functions  */
/* ------------------------------------------------------------------ */

const Burger = () => (
  <svg viewBox="0 0 60 60" className="w-full h-full" shapeRendering="crispEdges">
    {/* top bun */}
    <ellipse cx="30" cy="16" rx="24" ry="12" fill="#dcaa64" />
    <rect x="6" y="14" width="48" height="10" fill="#dcaa64" />
    {/* seeds */}
    <rect x="18" y="9"  width="2" height="2" fill="#fff" />
    <rect x="30" y="6"  width="2" height="2" fill="#fff" />
    <rect x="42" y="9"  width="2" height="2" fill="#fff" />
    {/* lettuce */}
    <rect x="4" y="22" width="52" height="6" fill="#3cb446" />
    <rect x="2" y="24" width="56" height="3" fill="#3cb446" />
    {/* cheese */}
    <rect x="4" y="28" width="52" height="5" fill="#fac828" />
    <polygon points="4,33 8,37 12,33" fill="#fac828" />
    <polygon points="48,33 52,37 56,33" fill="#fac828" />
    {/* patty */}
    <rect x="4" y="33" width="52" height="10" fill="#78461e" />
    {/* bottom bun */}
    <rect x="6" y="43" width="48" height="10" fill="#dcaa64" />
    <ellipse cx="30" cy="51" rx="24" ry="6" fill="#dcaa64" />
  </svg>
);

const Wings = () => (
  <svg viewBox="0 0 60 60" className="w-full h-full" shapeRendering="crispEdges">
    {/* drumstick meat */}
    <circle cx="22" cy="22" r="16" fill="#78461e" />
    <circle cx="16" cy="30" r="12" fill="#78461e" />
    <circle cx="22" cy="22" r="11" fill="#e68228" />
    <circle cx="16" cy="30" r="8"  fill="#e68228" />
    {/* crispy specks */}
    <rect x="18" y="18" width="2" height="2" fill="#78461e" />
    <rect x="24" y="24" width="2" height="2" fill="#78461e" />
    <rect x="14" y="28" width="2" height="2" fill="#78461e" />
    {/* bone shaft */}
    <rect x="28" y="30" width="22" height="6" fill="#bebebe" />
    {/* bone knobs */}
    <circle cx="50" cy="28" r="6" fill="#bebebe" />
    <circle cx="50" cy="36" r="6" fill="#bebebe" />
    <circle cx="50" cy="28" r="4" fill="#fff" />
    <circle cx="50" cy="36" r="4" fill="#fff" />
  </svg>
);

const Coke = () => (
  <svg viewBox="0 0 60 60" className="w-full h-full" shapeRendering="crispEdges">
    {/* cap */}
    <rect x="22" y="2"  width="16" height="4"  fill="#fac828" />
    {/* neck */}
    <rect x="24" y="4"  width="12" height="8"  fill="#820a14" />
    {/* shoulders */}
    <rect x="20" y="12" width="20" height="6"  fill="#820a14" />
    {/* body */}
    <rect x="14" y="18" width="32" height="36" fill="#820a14" />
    {/* white label */}
    <rect x="14" y="30" width="32" height="12" fill="#fff" />
    {/* red swoosh */}
    <rect x="17" y="33" width="26" height="3"  fill="#dc1e28" />
    <rect x="17" y="38" width="26" height="2"  fill="#dc1e28" />
    {/* highlight */}
    <rect x="16" y="20" width="2" height="30" fill="#c8323c" opacity="0.7" />
  </svg>
);

const Fries = () => (
  <svg viewBox="0 0 60 60" className="w-full h-full" shapeRendering="crispEdges">
    {/* fries sticking out of carton */}
    <rect x="16" y="6"  width="5" height="22" fill="#fac828" />
    <rect x="22" y="2"  width="5" height="26" fill="#fbd24a" />
    <rect x="28" y="6"  width="5" height="22" fill="#fac828" />
    <rect x="34" y="3"  width="5" height="25" fill="#fbd24a" />
    <rect x="40" y="8"  width="5" height="20" fill="#fac828" />
    {/* darker fry tips */}
    <rect x="16" y="6"  width="5" height="3"  fill="#d9a418" />
    <rect x="22" y="2"  width="5" height="3"  fill="#d9a418" />
    <rect x="28" y="6"  width="5" height="3"  fill="#d9a418" />
    <rect x="34" y="3"  width="5" height="3"  fill="#d9a418" />
    <rect x="40" y="8"  width="5" height="3"  fill="#d9a418" />
    {/* carton top lip */}
    <rect x="10" y="26" width="42" height="4" fill="#c81428" />
    {/* carton body (red) with white vertical stripes */}
    <rect x="12" y="30" width="38" height="24" fill="#dc1e28" />
    <rect x="16" y="30" width="3"  height="24" fill="#fff" />
    <rect x="25" y="30" width="3"  height="24" fill="#fff" />
    <rect x="34" y="30" width="3"  height="24" fill="#fff" />
    <rect x="43" y="30" width="3"  height="24" fill="#fff" />
    {/* carton bottom shadow */}
    <rect x="12" y="50" width="38" height="4"  fill="#aa1020" />
  </svg>
);

/* ------------------------------------------------------------------ */
/*  Symbol images - all rendered onto the SAME red/gold badge so they  */
/*  feel like they belong on the same slot-machine cabinet.            */
/* ------------------------------------------------------------------ */

const SymbolImg = ({ src, alt }) => (
  <img
    src={src}
    alt={alt}
    draggable={false}
    style={{ width: "100%", height: "100%", objectFit: "contain" }}
  />
);

const SYMBOLS = [
  { key: "burger", label: "BURGER", el: <SymbolImg src="/symbols/burger.png" alt="burger" />, payout: 50  },
  { key: "wings",  label: "WINGS",  el: <SymbolImg src="/symbols/wings.png"  alt="wings"  />, payout: 30  },
  { key: "coke",   label: "COKE",   el: <SymbolImg src="/symbols/coke.png"   alt="coke"   />, payout: 100 },
  { key: "fries",  label: "FRIES",  el: <SymbolImg src="/symbols/fries.png"  alt="fries"  />, payout: 40  },
];

// ---------------------------------------------------------------------
//  GAME TUNING (mirrors main.py on the RP2040)
//  WIN_EVERY = guaranteed 3-of-a-kind on every Nth spin.
//  All other spins are non-winning (re-rolled if a natural triple
//  comes up by chance).
// ---------------------------------------------------------------------
const WIN_EVERY = 50;

function pickFinals(spinIndex) {
  const n = SYMBOLS.length;
  if (spinIndex > 0 && spinIndex % WIN_EVERY === 0) {
    const s = Math.floor(Math.random() * n);
    return [s, s, s];
  }
  // losing/pair spin - re-roll any accidental triple so wins only
  // happen exactly on the scheduled spins.
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const roll = [
      Math.floor(Math.random() * n),
      Math.floor(Math.random() * n),
      Math.floor(Math.random() * n),
    ];
    if (!(roll[0] === roll[1] && roll[1] === roll[2])) return roll;
  }
}

/* ------------------------------------------------------------------ */
/*  Reel component                                                    */
/* ------------------------------------------------------------------ */

const CELL_H = 150; // px height of one symbol on screen

const Reel = ({ spinning, finalIdx, delay, onLanded }) => {
  const N = SYMBOLS.length;
  // continuous row index (float). middle slot always shows SYMBOLS[row mod N].
  const rowRef = useRef(finalIdx);
  const [, setTick] = useState(0); // force re-render on each anim frame
  const rafRef = useRef();

  // Run the spin animation when `spinning` flips to true
  useEffect(() => {
    if (!spinning) return;
    let cancelled = false;
    const duration = 1200 + delay;
    const startRow = rowRef.current;
    // travel at least 20 rows, then keep going until landing on a row that
    // is congruent to finalIdx modulo N (so the middle slot shows finalIdx)
    let travel = 20;
    const wantMod = ((finalIdx % N) + N) % N;
    while ((((Math.round(startRow) + travel) % N) + N) % N !== wantMod) {
      travel++;
    }
    const endRow = Math.round(startRow) + travel;
    const startTime = performance.now();
    const step = (now) => {
      if (cancelled) return;
      const p = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      rowRef.current = startRow + (endRow - startRow) * eased;
      setTick((t) => t + 1);
      if (p < 1) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        rowRef.current = endRow;
        setTick((t) => t + 1);
        onLanded && onLanded();
      }
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      cancelled = true;
      cancelAnimationFrame(rafRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [spinning]);

  // When not spinning and finalIdx is set externally, snap to it
  useEffect(() => {
    if (!spinning) {
      rowRef.current = finalIdx;
      setTick((t) => t + 1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [finalIdx]);

  // Render a small window of symbols around the current cursor row,
  // positioned so the symbol at integer index `row` sits in the middle slot.
  const row = rowRef.current;
  const baseRow = Math.floor(row);
  const cells = [];
  for (let k = baseRow - 2; k <= baseRow + 3; k++) {
    const symIdx = ((k % N) + N) % N;
    const top = (k - row) * CELL_H + CELL_H; // middle slot is at y = CELL_H
    cells.push({ k, symIdx, top });
  }

  return (
    <div
      data-testid={`reel-${delay}`}
      className="relative overflow-hidden rounded-md border-2 border-yellow-400 bg-black"
      style={{
        height: `${CELL_H * 3}px`,
        width: `${CELL_H}px`,
        boxShadow:
          "inset 0 0 24px rgba(0,0,0,0.9), 0 0 18px rgba(255, 215, 0, 0.35)",
      }}
    >
      {/* darkening overlays at top and bottom for "viewport" feel */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-1/3 bg-gradient-to-b from-black/80 to-transparent z-10" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/80 to-transparent z-10" />
      {/* center highlight band */}
      <div className="pointer-events-none absolute inset-x-0 top-1/3 h-1/3 border-y-2 border-yellow-300/70 z-20" />

      {cells.map(({ k, symIdx, top }) => (
        <div
          key={k}
          style={{
            position: "absolute",
            top: `${top}px`,
            left: 0,
            width: CELL_H,
            height: CELL_H,
            willChange: "transform",
          }}
          className="flex items-center justify-center p-2"
        >
          <div style={{ width: CELL_H - 16, height: CELL_H - 16 }}>
            {SYMBOLS[symIdx].el}
          </div>
        </div>
      ))}
    </div>
  );
};

/* ------------------------------------------------------------------ */
/*  Sound (WebAudio beep, mirrors the buzzer code on hardware)        */
/* ------------------------------------------------------------------ */

const useBeeper = () => {
  const ctxRef = useRef(null);
  const getCtx = () => {
    if (!ctxRef.current) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) ctxRef.current = new AC();
    }
    return ctxRef.current;
  };
  return useCallback((freq, ms) => {
    const ctx = getCtx();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "square";
    osc.frequency.value = freq;
    gain.gain.value = 0.05;
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + ms / 1000);
  }, []);
};

/* ------------------------------------------------------------------ */
/*  Main slot machine                                                 */
/* ------------------------------------------------------------------ */

export default function SlotMachine() {
  const [finals, setFinals] = useState([0, 1, 2]); // initial preview
  const [spinning, setSpinning] = useState(false);
  const [message, setMessage] = useState("");
  const [flash, setFlash] = useState(false);
  const landedRef = useRef(0);
  const spinCountRef = useRef(0);
  const beep = useBeeper();

  const evaluate = useCallback((picks) => {
    const [a, b, c] = picks;
    // only 3-of-a-kind counts as a win; pairs are ignored.
    if (a === b && b === c) {
      return { win: true, text: `JACKPOT! ${SYMBOLS[a].label}` };
    }
    return { win: false, text: "" };
  }, []);

  const spin = useCallback(() => {
    if (spinning) return;
    spinCountRef.current += 1;
    const picks = pickFinals(spinCountRef.current);
    setFinals(picks);
    setMessage("");
    setFlash(false);
    setSpinning(true);
    landedRef.current = 0;
    beep(440, 60);
  }, [spinning, beep]);

  const onReelLanded = useCallback(() => {
    landedRef.current += 1;
    beep(660 + landedRef.current * 110, 60);
    if (landedRef.current === 3) {
      setSpinning(false);
      const res = evaluate(finals);
      if (res.win) {
        setMessage(res.text);
        setFlash(true);
        // play a small win arpeggio
        [880, 1040, 1240, 1480].forEach((f, i) =>
          setTimeout(() => beep(f, 90), i * 110)
        );
        setTimeout(() => setFlash(false), 1800);
      }
    }
  }, [evaluate, finals, beep]);

  // keyboard: SPACE = spin
  useEffect(() => {
    const onKey = (e) => {
      if (e.code === "Space") {
        e.preventDefault();
        spin();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [spin]);

  return (
    <div
      className="slot-page min-h-screen w-full flex items-center justify-center px-4 py-6 select-none"
      style={{
        backgroundImage: "url(/bg.png)",
        backgroundSize: "contain",
        backgroundPosition: "center center",
        backgroundRepeat: "no-repeat",
        backgroundAttachment: "fixed",
        backgroundColor: "#2a1109",
      }}
    >
      <div className="w-full max-w-5xl flex flex-col items-center gap-6">
        {/* spacer that pushes the reels down so they sit BELOW the
            "GIRA Y GANA" headline that lives in the background image */}
        <div className="reels-spacer" />

        {/* reels row - free-floating, no cabinet */}
        <div
          data-testid="reels-row"
          className={`flex items-center justify-center gap-3 sm:gap-6 ${flash ? "reels-flash" : ""}`}
        >
          <Reel
            spinning={spinning}
            finalIdx={finals[0]}
            delay={0}
            onLanded={onReelLanded}
          />
          <Reel
            spinning={spinning}
            finalIdx={finals[1]}
            delay={250}
            onLanded={onReelLanded}
          />
          <Reel
            spinning={spinning}
            finalIdx={finals[2]}
            delay={500}
            onLanded={onReelLanded}
          />
        </div>

        {/* message bar - only visible when there is a win to celebrate */}
        {message && (
          <div className="flex items-center justify-center">
            <span
              data-testid="message-display"
              className={`font-pixel text-lg sm:text-2xl px-4 py-2 rounded ${flash ? "text-black bg-yellow-300" : "text-yellow-100 bg-black/55"}`}
            >
              {message}
            </span>
          </div>
        )}

        {/* single big GIRAR button, centered */}
        <div className="w-full flex items-center justify-center">
          <button
            data-testid="spin-button"
            onClick={spin}
            disabled={spinning}
            className={`relative font-pixel tracking-widest text-2xl sm:text-3xl text-black px-16 py-6 rounded-full transition-transform active:translate-y-1 ${
              spinning
                ? "bg-zinc-500 cursor-not-allowed"
                : "bg-gradient-to-b from-red-400 to-red-600 hover:from-red-300 shadow-[0_10px_0_#7a0008,0_0_40px_rgba(255,60,80,0.6)]"
            }`}
          >
            {spinning ? "GIRANDO" : "GIRAR"}
          </button>
        </div>
      </div>
    </div>
  );
}
