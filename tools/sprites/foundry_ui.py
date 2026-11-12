"""The Foundry's interface: the swarm's grammar (swarm_ui) in the Foundry's own materials. The background is a
soot-black forge wall with the hearth's glow; panels are forged iron sheets with rivets and brass corners; cells are
iron frames with screwed brass angles; buttons are bars of metal, and what a button does is what metal it is —
hot metal for the action that moves the run on, dark tempered steel for going back, rust for what melts something
down, brass for what is on, dull iron for what can't be pressed. Under the mouse the metal heats up. At the foot of
a screen the controls are a machine's console: the screen's own action a lever beside a cast nameplate, the rest
push-buttons in hex nuts with stamped tags, repairing a valve's handwheel. Letters,
glyphs and tooltips are the swarm's own (swarm_ui.letters, fxg).

    python3 tools/sprites/foundry_ui.py      -> out/foundry_ui_kit.png
"""
import numpy as np
from kit import *
from noise import value_noise
import swarm_ui as SU
from swarm_ui import letters, edges, shrink, chamfer_mask, OUTL

INK = (236, 226, 204)
MUTED = (170, 160, 150)
PALE = (120, 114, 112)
BRASS = (226, 186, 106)
HOT = (255, 176, 84)
DARK = (34, 22, 12)
RED = (236, 110, 90)


# ---------------------------------------------------------------- the wall
def forge(w, h, seed=1):
    """Soot-black brick, the mortar darker, the hearth's glow low on the left, ash in the air."""
    sc = Scene(w, h)
    n = value_noise(w, h, 12, seed) * 0.6 + value_noise(w, h, 4, seed + 1) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, c in enumerate(("#141214", "#181517", "#1c181a", "#201b1d")):
        sc.rgb[lv == i] = hexc(c)
    BH, BW = 12, 30
    Y, X = sc.yy, sc.xx
    row = Y // BH
    off = (row % 2) * (BW // 2)
    mortar = (Y % BH == 0) | ((X + off) % BW == 0)
    sc.rgb[mortar] *= 0.62
    lit = ((Y % BH) == 1) & ~mortar                                  # the top edge of each brick catches the glow
    sc.rgb[lit] = sc.rgb[lit] * 0.85 + hexc("#3a2a24") * 0.15
    soot = value_noise(w, h, 60, seed + 5) > 0.62
    sc.rgb[soot] *= 0.8
    heat = np.clip(1 - np.hypot((X - 0) / (w * 0.9), (Y - h) / (h * 0.9)), 0, 1) ** 2
    sc.rgb[:] = sc.rgb + (hexc("#ff6a1a") * 0.28 * heat[..., None])
    rnd = np.random.RandomState(seed)
    for _ in range(60):                                             # ash and a few embers drifting up
        x, y = rnd.randint(0, w), rnd.randint(0, h)
        if rnd.rand() < 0.2:
            sc.rgb[y, x] = hexc("#ff9a3a")
        else:
            sc.rgb[y, x] = sc.rgb[y, x] * 0.5 + hexc("#6a625e") * 0.5
    sc.rgb[:] = np.clip(sc.rgb, 0, 255)
    return sc


# ---------------------------------------------------------------- bits of metal
def rivet(sc, x, y, col="#9a9aa4"):
    x, y = int(x), int(y)
    if 1 <= x < sc.w - 2 and 1 <= y < sc.h - 2:
        sc.rgb[y - 1:y + 2, x - 1:x + 2] = OUTL
        sc.rgb[y:y + 1, x:x + 1] = hexc(col)
        sc.rgb[y - 1, x] = sc.rgb[y - 1, x] * 0.3 + hexc("#d8d8e0") * 0.7


def screw(sc, x, y):
    """A slotted screw head in a brass angle."""
    x, y = int(x), int(y)
    sc.rgb[y - 2:y + 3, x - 1:x + 2] = hexc("#2a2018")
    sc.rgb[y - 1:y + 2, x - 2:x + 3] = hexc("#2a2018")
    sc.rgb[y - 1:y + 2, x - 1:x + 2] = hexc("#c8a060")
    sc.rgb[y, x - 1:x + 2] = hexc("#4a3418")


def brass_corners(sc, x0, y0, x1, y1, L=7, col="#b8904a"):
    """Brass angle irons screwed on at the corners."""
    c, d = hexc(col), hexc("#5a4020")
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1 - 1, y0, -1, 1), (x0, y1 - 1, 1, -1), (x1 - 1, y1 - 1, -1, -1)):
        for k in range(L):
            for w_ in range(2):
                xx, yy = cx + sx * k, cy + sy * w_
                if 0 <= xx < sc.w and 0 <= yy < sc.h:
                    sc.rgb[yy, xx] = c if w_ == 0 else d
                xx, yy = cx + sx * w_, cy + sy * k
                if 0 <= xx < sc.w and 0 <= yy < sc.h:
                    sc.rgb[yy, xx] = c if w_ == 0 else d
        screw(sc, cx + sx * 3, cy + sy * 3)


def hammered(sc, m, seed, k=0.12):
    """Hammer marks: faint dents of light and shade across a sheet."""
    n = value_noise(sc.w, sc.h, 6, seed)
    sc.rgb[m] = sc.rgb[m] * (1 - k + 2 * k * n[m][:, None])


def plate(sc, x0, y0, x1, y1, seed=1, rivets=True):
    """A forged iron sheet: darker toward the bottom, hammered, a bright bevel along the top, rivets round the edge
    and brass angles at the corners."""
    m = chamfer_mask(sc, x0, y0, x1, y1, 4)
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    top_c, bot_c = hexc("#2c2a30"), hexc("#18171c")
    sc.rgb[m] = (top_c * (1 - t) + bot_c * t)[m]
    hammered(sc, m, seed)
    o, top, left = edges(m)
    sc.rgb[o] = OUTL
    i1 = shrink(m)
    o1, top1, left1 = edges(i1)
    sc.rgb[o1] = hexc("#3a3840")
    sc.rgb[top1] = hexc("#6a6870")
    sc.rgb[left1 & ~top1] = hexc("#4a4850")
    if rivets:
        for x in range(x0 + 14, x1 - 10, 18):
            rivet(sc, x, y0 + 4)
            rivet(sc, x, y1 - 5)
        for y in range(y0 + 16, y1 - 12, 18):
            rivet(sc, x0 + 4, y)
            rivet(sc, x1 - 5, y)
    brass_corners(sc, x0 + 1, y0 + 1, x1 - 1, y1 - 1)
    sc.occ[m] = True
    sc.light[m] = 0


CELL = {   # rim, its lit edge, the fill
    "normal": ("#5a5c66", "#8a8c96", "#141318"),
    "hi": ("#b8904a", "#f0c878", "#1c1610"),          # chosen: brass
    "hover": ("#ff8a2a", "#ffd890", "#22140c"),       # under the mouse: the metal heats up
    "new": ("#4a90b0", "#9ad8f0", "#10161a"),         # a new module: cold blue steel
    "broken": ("#a8402e", "#e07a5a", "#1e1012"),      # broken: rust red, a crack
    "rare": ("#8a5ab8", "#c8a0f0", "#16121e"),        # a rare module
    "trophy": ("#9a7a4a", "#d0b080", "#18140e"),      # a trophy off a beaten machine
    "locked": ("#2a2a30", "#3a3a42", "#0e0e12"),
}


def cell(sc, x0, y0, x1, y1, state="normal"):
    """An iron frame round a dark well, brass angles at the corners. The state is its rim's metal, and a shape:
    chosen — a brass tab on the left; under the mouse — red-hot rim, heat in the well and sparks off the edge;
    new — a cold-blue arrow up; broken — a crack across the corner; rare — a gem; a trophy — a gear."""
    rim, hi, fill = CELL[state]
    m = chamfer_mask(sc, x0, y0, x1, y1, 3)
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    base = hexc(fill)
    sc.rgb[m] = (base * (1.2 - 0.35 * t))[m]
    o, top, left = edges(m)
    sc.rgb[o] = OUTL
    r1 = shrink(m)
    o1, top1, left1 = edges(r1)
    sc.rgb[o1] = hexc(rim)
    sc.rgb[(top1 | left1) & o1] = hexc(hi)
    r2 = shrink(r1)
    o2, _, _ = edges(r2)
    sc.rgb[o2] = sc.rgb[o2] * 0.5 + hexc("#000000") * 0.5
    if state in ("hi", "hover", "rare"):
        halo = chamfer_mask(sc, x0 - 2, y0 - 2, x1 + 2, y1 + 2, 4) & ~m
        th = BAYER[sc.yy % 4, sc.xx % 4]
        sc.rgb[halo & (th < 0.6)] = sc.rgb[halo & (th < 0.6)] * 0.4 + hexc(hi) * 0.6
    if state == "hover":                                   # heat soaking in from the red-hot rim
        d = np.minimum(np.minimum(sc.xx - x0, x1 - sc.xx), np.minimum(sc.yy - y0, y1 - sc.yy)).astype(float)
        for k, (dd, col) in enumerate(((4, "#c8501a"), (7, "#7a2a0e"), (11, "#3a1608"))):
            ring = r2 & (d < dd) & (d >= (dd - 3 if k else 0))
            th = BAYER[sc.yy % 4, sc.xx % 4]
            sc.rgb[ring & (th < 0.75 - k * 0.2)] = sc.rgb[ring & (th < 0.75 - k * 0.2)] * 0.45 + hexc(col) * 0.55
        sparks(sc, x1 - 8, y0 + 3, 10, seed=x0 + y0)
        sparks(sc, x0 + 12, y1 - 3, 6, seed=x1 + y1)
    brass_corners(sc, x0 + 2, y0 + 2, x1 - 2, y1 - 2, L=5, col="#9a7a40" if state != "hi" else "#e0b860")
    cy = (y0 + y1) // 2
    if state == "hi":
        SU._px(sc, ["a..", "aa.", "aAa", "aa.", "a.."], x0 - 3, cy - 7, {"a": hi, "A": "#fff4c8"}, z=3)
    elif state == "new":
        SU._px(sc, [".b.", "bBb", ".B.", ".B."], x1 - 16, y0 + 6, {"b": hi, "B": "#e8f8ff"})
    elif state == "broken":
        SU._px(sc, ["r....", ".r...", ".rr..", "...r.", "....r"], x1 - 16, y1 - 16, {"r": "#ff8a6a"})
    elif state == "rare":
        SU._px(sc, ["..p..", ".pWp.", "pWWWp", ".pWp.", "..p.."], x1 - 18, y0 + 6, {"p": hi, "W": "#ffffff"})
    elif state == "trophy":
        SU._px(sc, [".g.g.", "ggggg", ".gWg.", "ggggg", ".g.g."], x1 - 18, y0 + 6, {"g": hi, "W": "#2a2018"})
    sc.occ[m] = True
    sc.light[m] = 0


BUTTON = {   # the bar's ramp top → bottom, its bevel, the text colour
    "hot": (("#fff0a0", "#ffb040", "#e0601a", "#7a2408"), "#fffbe0", DARK),       # the action: hot metal
    "steel": (("#6a6e7c", "#44465a", "#2a2a3a", "#16161e"), "#b0b8d0", INK),     # going back: tempered steel
    "rust": (("#c8704a", "#9a3e24", "#5e1e12", "#2a0c08"), "#f0b090", INK),      # what melts down: rust
    "brass": (("#ffe8a0", "#e0b050", "#a87420", "#4a3008"), "#fff8d8", DARK),    # on, open: brass
    "dull": (("#4a4848", "#363434", "#262424", "#141212"), "#6a6866", PALE),     # can't be pressed: dull iron
}


def button(sc, x0, y0, x1, y1, kind="steel", heated=False):
    """A bar of metal in a dark iron bezel, a bolt head at each end; hot metal glows round itself. Heated — the mouse
    over it: the bar reddens toward the ends and throws sparks."""
    ramp_, bevel, _ = BUTTON[kind]
    X, Y = sc.xx, sc.yy
    h = y1 - y0
    outer = chamfer_mask(sc, x0, y0, x1, y1, 5)
    body = chamfer_mask(sc, x0 + 3, y0 + 3, x1 - 3, y1 - 3, 4)
    sc.rgb[outer] = hexc("#1a181c")
    o, top, left = edges(outer)
    sc.rgb[o] = OUTL
    sc.rgb[top & ~o] = hexc("#5a5860")
    pal = np.array([hexc(c) for c in ramp_])
    tt = np.clip((Y - y0 - 3) / max(1, h - 6), 0, 1)
    idx = np.clip(np.floor(tt * 3.6 + BAYER[Y % 4, X % 4] * 0.6), 0, 3).astype(int)
    sc.rgb[body] = pal[idx][body]
    if kind == "steel":                                      # temper colours drifting along tempered steel
        hue = (X - x0) / max(1, x1 - x0)
        tint = np.stack([110 + 50 * np.sin(hue * 5.0), 90 + 40 * np.sin(hue * 5.0 + 2.0), 140 + 50 * np.sin(hue * 5.0 + 4.0)], -1)
        band = body & (Y < y0 + h * 0.5)
        sc.rgb[band] = sc.rgb[band] * 0.78 + tint[band] * 0.22
    if kind == "rust":                                       # pitting
        pit = body & (value_noise(sc.w, sc.h, 3, x0 + y0) > 0.66)
        sc.rgb[pit] *= 0.7
    bo, btop, _ = edges(body)
    sc.rgb[btop] = sc.rgb[btop] * 0.3 + hexc(bevel) * 0.7
    bb = bo & ~btop & (Y > (y0 + y1) / 2)
    sc.rgb[bb] = sc.rgb[bb] * 0.55
    if heated:
        d = np.minimum(X - x0, x1 - X) / max(1, (x1 - x0) * 0.5)
        hot = body & (d < 0.35)
        sc.rgb[hot] = sc.rgb[hot] * 0.6 + hexc("#ff5a1a") * 0.4
        sparks(sc, x1 - 8, y0 + 4, 9, seed=x0)
        sparks(sc, x0 + 10, y1 - 4, 6, seed=x1)
    for bx in (x0 + 8, x1 - 9):                               # bolt heads
        cy = (y0 + y1) // 2
        sc.rgb[cy - 3:cy + 4, bx - 2:bx + 3] = OUTL
        sc.rgb[cy - 2:cy + 3, bx - 3:bx + 4] = OUTL
        sc.rgb[cy - 2:cy + 3, bx - 2:bx + 3] = hexc("#8a8890")
        sc.rgb[cy - 2, bx - 1:bx + 2] = hexc("#d0d0d8")
        sc.rgb[cy, bx - 1:bx + 2] = hexc("#3a3840")
    if kind == "hot":                                      # hot metal lights the iron round it
        halo = chamfer_mask(sc, x0 - 3, y0 - 3, x1 + 3, y1 + 3, 6) & ~outer
        th = BAYER[sc.yy % 4, sc.xx % 4]
        sc.rgb[halo & (th < 0.5)] = sc.rgb[halo & (th < 0.5)] * 0.5 + hexc("#ff8a2a") * 0.5
    sc.occ[outer] = True
    sc.light[outer] = 0


# ---------------------------------------------------------------- the console: the screen's controls are a machine's
def sill(sc, y0, y1=None):
    """The console along the foot of the screen: an iron beam, hammered, a brass strip along its top and a row of
    rivets along its foot; the controls are set into it."""
    y1 = sc.h if y1 is None else y1
    m = (sc.yy >= y0) & (sc.yy < y1)
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    sc.rgb[m] = (hexc("#1f1d22") * (1 - t) + hexc("#121115") * t)[m]
    hammered(sc, m, 47, k=0.16)
    sc.rgb[y0] = OUTL
    sc.rgb[y0 + 1] = hexc("#c8a060")
    sc.rgb[y0 + 2] = hexc("#8a6a34")
    sc.rgb[y0 + 3] = OUTL
    for x in range(12, sc.w, 26):
        rivet(sc, x, y1 - 5)
    sc.occ[m] = True
    sc.light[m] = 0


def _ramp_fill(sc, m, ramp_, t):
    """Fill mask m from a 5-colour ramp by t in 0..1 (dark → light), with the 4×4 dither."""
    pal = np.array([hexc(c) for c in ramp_])
    th = BAYER[sc.yy % 4, sc.xx % 4]
    idx = np.clip(np.floor(t * 4.0 + (th - 0.5) * 0.9), 0, 4).astype(int)
    sc.rgb[m] = pal[idx][m]


CAP = {   # the push-button's cap, dark → light
    "steel": ("#14161c", "#262a32", "#3e4450", "#626c7c", "#a0aabc"),
    "brass": ("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f4dc96"),
    "rust": ("#2a0806", "#5a140c", "#8e2a16", "#c44a28", "#f08a5a"),
    "hot": ("#5a1408", "#a8320e", "#e86a1a", "#ffb43a", "#fff3c0"),
    "dull": ("#18181a", "#222224", "#2e2e30", "#3c3c3e", "#4e4e50"),
}


def pushbutton(sc, cx, cy, r=14, kind="steel", pressed=False):
    """A mushroom push-button in a hex-nut bezel: the nut's facets lit from the top left, a dark well, the domed cap
    with a hard highlight; pressed (the mouse on it) — the cap sinks a pixel and the nut warms."""
    X, Y = sc.xx - cx, sc.yy - cy
    d = np.hypot(X, Y)
    ang = np.arctan2(Y, X)
    R = r + 6
    hexr = R * np.cos(np.pi / 6) / np.cos(np.mod(ang, np.pi / 3) - np.pi / 6)
    nut = d <= hexr
    facet = np.floor(np.mod(ang + np.pi / 6, 2 * np.pi) / (np.pi / 3))
    nrm = facet * np.pi / 3                                    # the facet's outward direction
    lit = 0.5 + 0.5 * np.cos(nrm - (-2.35))                    # light from the top left
    base = hexc("#262428")[None, None, :] * (1 - lit[..., None]) + hexc("#8a8892")[None, None, :] * lit[..., None]
    if pressed:
        base = base * 0.75 + hexc("#ff7a2a") * 0.25
    sc.rgb[nut] = base[nut]
    o, _, _ = edges(nut)
    sc.rgb[o] = OUTL
    well = d <= r + 2
    sc.rgb[well] = hexc("#0a090c")
    dy = 1 if pressed else -1
    dc = np.hypot(X, Y - dy)
    cap = dc <= r
    lt = np.clip(0.55 - (X * 0.6 + (Y - dy) * 0.8) / (2.2 * r) - (dc / r) ** 4 * 0.35, 0, 1)
    _ramp_fill(sc, cap, CAP[kind], lt)
    rim = cap & (dc > r - 1.6)
    sc.rgb[rim] = sc.rgb[rim] * 0.6
    hl = np.hypot(X + r * 0.38, Y - dy + r * 0.42) <= max(1.2, r * 0.2)
    sc.rgb[hl & cap] = hexc(CAP[kind][4]) * 0.5 + hexc("#ffffff") * 0.5
    co, _, _ = edges(cap)
    sc.rgb[co & (Y - dy > 0)] = OUTL
    sc.occ[nut] = True
    sc.light[nut] = 0
    if kind == "hot":                                          # hot metal lights the iron round it
        halo = (d > hexr) & (d <= hexr + 3)
        th = BAYER[sc.yy % 4, sc.xx % 4]
        sc.rgb[halo & (th < 0.45)] = sc.rgb[halo & (th < 0.45)] * 0.5 + hexc("#ff8a2a") * 0.5


TAG = {   # the tag's ink, its metal, its lit edge
    "steel": ("#14161c", "#9aa0ac", "#d4d8e0"), "brass": ("#2a1806", "#c09a50", "#f0d490"),
    "rust": ("#1e0a06", "#a8705a", "#d8a088"), "hot": ("#2a1806", "#c09a50", "#f0d490"),
    "dull": ("#1a1a1c", "#56565c", "#6e6e74")}


def tag(sc, x0, y0, x1, y1, text, kind="steel", wire_to=None):
    """A stamped tag on the console beside its control: pointed at the control, a hole at the point with a wire to
    it, the letters struck into the metal (dark, with the light catching the lower edge of each stroke)."""
    X, Y = sc.xx, sc.yy
    yc = (y0 + y1) / 2
    p = (y1 - y0) / 2
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    m &= (X - x0) >= np.abs(Y - yc) * 0.9                       # the point toward the control
    m &= (x1 - 1 - X) + (Y - y0) >= 3
    m &= (x1 - 1 - X) + (y1 - 1 - Y) >= 3
    dark, mid, light = (hexc(c) for c in TAG[kind])
    t = np.clip((Y - y0) / max(1, y1 - y0), 0, 1)
    th = BAYER[sc.yy % 4, sc.xx % 4]
    fill = np.where(((t + (th - 0.5) * 0.25) < 0.45)[..., None], mid[None, None, :] * 1.06, mid[None, None, :] * 0.86)
    sc.rgb[m] = fill[m]
    hammered(sc, m, x0 + y0, k=0.10)
    o, top, _ = edges(m)
    sc.rgb[top] = light
    sc.rgb[o & ~top] = OUTL
    bot = o & (Y > yc)
    sc.rgb[bot] = OUTL
    hx, hy = int(x0 + p * 0.95), int(yc)                         # the hole and its wire
    sc.rgb[hy - 2:hy + 3, hx - 2:hx + 3] = OUTL
    sc.rgb[hy - 1:hy + 2, hx - 1:hx + 2] = hexc("#0a090c")
    if wire_to is not None:
        wx = int(wire_to)
        for x in range(min(wx, hx), max(wx, hx)):
            sc.rgb[hy + (1 if (x // 3) % 2 else 0), x] = hexc("#8a8890")
    tx = x0 + p * 1.6 + 6
    tw = SU.text_width(text, "text", 16)
    ink = tuple(int(v) for v in dark)
    letters(sc, text, tx + 1, yc - 8 + 1, "text", 16, col=tuple(int(v) for v in light), outline=False, shadow=False)
    letters(sc, text, tx, yc - 8, "text", 16, col=ink, outline=False, shadow=False)
    sc.occ[m] = True
    sc.light[m] = 0
    return tw


def nameplate(sc, x0, y0, x1, y1, text, hot=True, heated=False):
    """A cast plate like a locomotive's: an arched top, a raised brass rim, raised brass letters on enamel — black
    enamel, or glowing ember-red when it is the step that moves the run on."""
    X, Y = sc.xx, sc.yy
    w = x1 - x0
    xc = (x0 + x1) / 2
    u = (X - xc) / (w / 2)
    top = y0 + 7 * u ** 2                                          # the arched top
    m = (X >= x0) & (X < x1) & (Y >= top) & (Y < y1)
    cr = 6                                                         # cast corners, cut in as quarter circles
    for cx_, cy_ in ((x0, y0 + 7), (x1 - 1, y0 + 7), (x0, y1 - 1), (x1 - 1, y1 - 1)):
        m &= np.hypot(X - cx_, Y - cy_) > cr
    inner = shrink(shrink(shrink(m)))
    rim = m & ~inner
    lt = np.clip(0.6 - (X - xc) / w * 0.5 - (Y - (y0 + y1) / 2) / (y1 - y0) * 0.9, 0, 1)
    _ramp_fill(sc, rim, ("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f4dc96"), lt)
    o, _, _ = edges(m)
    sc.rgb[o] = OUTL
    io, itop, _ = edges(inner)
    t = np.clip((Y - y0) / max(1, y1 - y0), 0, 1)
    if hot:
        enamel = ("#2a0604", "#4a0e08", "#7a1c0c", "#b0361a", "#e86a2a")
        tt = 0.72 - t * 0.55 + (0.12 if heated else 0.0)
    else:
        enamel = ("#0a090c", "#121016", "#1a1820", "#24222a", "#302e38")
        tt = 0.6 - t * 0.4
    _ramp_fill(sc, inner, enamel, np.clip(tt, 0, 1))
    sc.rgb[itop] = sc.rgb[itop] * 0.4                              # the enamel sits below the rim
    for bx in (x0 + 9, x1 - 10):                                   # bolts through the rim's ends
        by = (y0 + y1) // 2 + 2
        sc.rgb[by - 2:by + 3, bx - 2:bx + 3] = OUTL
        sc.rgb[by - 1:by + 2, bx - 1:bx + 2] = hexc("#d0a848")
        sc.rgb[by - 1, bx - 1] = hexc("#f4dc96")
    letters(sc, text, xc, (y0 + y1) / 2 - 7, "title", 16, col=(255, 222, 150), col2=(150, 100, 40), align="center")
    if heated:
        sparks(sc, x1 - 14, y0 + 6, 9, seed=x0)
        sparks(sc, x0 + 18, y1 - 4, 6, seed=x1)
    sc.occ[m] = True
    sc.light[m] = 0


def lever(sc, x, y0, y1, pulled=False, hot=True):
    """A throttle lever (рубильник): a toothed iron quadrant on a base block, a thick arm from a pivot at its foot,
    a red ball for a handle; pulled (the mouse on it) — thrown forward, sparks at the pivot."""
    X, Y = sc.xx, sc.yy
    px, py = x, y1 - 9
    R = (y1 - y0) * 0.42
    dd = np.hypot(X - px, Y - py)
    quad = (dd <= R) & (Y <= py)
    teeth = (dd > R) & (dd <= R + 2) & (Y <= py - 1) & (np.mod(np.arctan2(X - px, py - Y) * 9 / np.pi, 2) < 1)
    q = quad | teeth
    _ramp_fill(sc, q, ("#141316", "#1e1c22", "#2a2830", "#3c3a44", "#5a5862"),
               np.clip(0.62 - (X - px) / (3 * R) + (Y - py) / (2.5 * R), 0, 1))
    o, _, _ = edges(q)
    sc.rgb[o] = OUTL
    slot = (dd >= R * 0.55) & (dd <= R * 0.72) & (Y <= py - 2) & (np.abs(X - px) <= (py - Y) * 1.6)
    sc.rgb[slot] = hexc("#060508")
    base = (np.abs(X - px) <= R + 3) & (Y > py) & (Y <= y1)
    _ramp_fill(sc, base, ("#141316", "#1e1c22", "#2a2830", "#3c3a44", "#5a5862"), np.clip(0.7 - (Y - py) / 10.0, 0, 1))
    bo, btop, _ = edges(base)
    sc.rgb[bo] = OUTL
    sc.rgb[btop & ~bo] = hexc("#6a6870")
    for bx in (px - R + 1, px + R - 1):
        rivet(sc, int(bx), int(py + 4))
    a = 0.62 if pulled else -0.5
    L = (y1 - y0) - 14
    ex, ey = px + np.sin(a) * L, py - np.cos(a) * L
    ux, uy = np.sin(a), -np.cos(a)
    along = (X - px) * ux + (Y - py) * uy
    across = np.abs(-(X - px) * uy + (Y - py) * ux)
    arm = (along >= -2) & (along <= L) & (across <= 2.2)
    _ramp_fill(sc, arm, ("#2a2c34", "#50545e", "#868a94", "#bcc0c8", "#eef0f4"),
               np.clip(0.75 - ((X - px) * uy - (Y - py) * ux) / 5.0 * 0.0 - across / 4.0, 0, 1))
    ao, _, _ = edges(arm)
    sc.rgb[ao] = OUTL
    d = np.hypot(X - ex, Y - ey)                                   # the handle
    ball = d <= 5.5
    _ramp_fill(sc, ball, CAP["rust"], np.clip(0.62 - ((X - ex) + (Y - ey)) / 10.0, 0, 1))
    bo2, _, _ = edges(ball)
    sc.rgb[bo2] = OUTL
    sc.rgb[int(ey) - 2:int(ey), int(ex) - 2:int(ex)] = hexc("#ffd0b0")
    pv = np.hypot(X - px, Y - py) <= 3.2                           # the pivot
    _ramp_fill(sc, pv, ("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f4dc96"), np.clip(0.6 - ((X - px) + (Y - py)) / 6, 0, 1))
    sc.rgb[int(py), int(px)] = OUTL
    if pulled:
        sparks(sc, px + 5, py - 3, 8, seed=int(px))
    sc.occ[q | ball | base | arm] = True
    sc.light[q | base] = 0


def step_plate(sc, x0, y0, x1, y1, text, kind="dull", first=False):
    """A step of a sequence: a cast plate shaped as an arrow — its tail notched to take the previous one's point — so
    the steps read as one chain. Done — brass; the current one — hot enamel in a brass rim; the next ones — dull iron."""
    X, Y = sc.xx, sc.yy
    yc = (y0 + y1) / 2
    h2 = (y1 - y0) / 2
    pt = h2 * 0.8
    m = (Y >= y0) & (Y < y1) & (X >= x0) & (X < x1)
    m &= (x1 - 1 - X) >= np.abs(Y - yc) * (pt / h2)                     # the point
    if not first:
        m &= (X - x0) >= pt - np.abs(Y - yc) * (pt / h2)                # the notch
    inner = shrink(shrink(m))
    rim = m & ~inner
    t = np.clip((Y - y0) / max(1, y1 - y0), 0, 1)
    if kind == "hot":
        _ramp_fill(sc, rim, ("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f4dc96"), np.clip(0.75 - t * 0.6, 0, 1))
        _ramp_fill(sc, inner, ("#2a0604", "#4a0e08", "#7a1c0c", "#b0361a", "#e86a2a"), np.clip(0.75 - t * 0.6, 0, 1))
        col = (255, 222, 150)
    elif kind == "brass":
        _ramp_fill(sc, m, ("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f4dc96"), np.clip(0.85 - t * 0.6, 0, 1))
        col = (52, 32, 10)
    else:
        _ramp_fill(sc, m, ("#141316", "#1c1a20", "#26242a", "#323038", "#46444c"), np.clip(0.8 - t * 0.6, 0, 1))
        col = (120, 114, 112)
    o, top, _ = edges(m)
    sc.rgb[o] = OUTL
    sc.rgb[top & ~o] = sc.rgb[top & ~o] * 0.6 + hexc("#ffffff") * 0.15
    tx = (x0 + x1) / 2 + pt * 0.3
    if kind == "brass":                                                 # struck into the brass: dark letters
        col = (30, 18, 4)
    letters(sc, text, tx, yc - 8, "text", 16, col=col, outline=kind == "hot", shadow=kind == "hot", align="center")
    sc.occ[m] = True
    sc.light[m] = 0


def tab(sc, x0, y0, x1, y1, text, active=False, badge=None):
    """A tab on top of a panel: a cast plate with its top corners cut away; the active one brass and open into the
    panel below, the rest dull iron. badge — a red number riveted to its corner (what needs doing there)."""
    X, Y = sc.xx, sc.yy
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    m &= (X - x0) + (Y - y0) * 0.0 >= np.maximum(0, 5 - (Y - y0))       # the cut top corners
    m &= (x1 - 1 - X) >= np.maximum(0, 5 - (Y - y0))
    t = np.clip((Y - y0) / max(1, y1 - y0), 0, 1)
    if active:
        _ramp_fill(sc, m, ("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f4dc96"), np.clip(0.85 - t * 0.5, 0, 1))
        col = (30, 18, 4)
    else:
        _ramp_fill(sc, m, ("#141316", "#1c1a20", "#26242a", "#323038", "#46444c"), np.clip(0.7 - t * 0.5, 0, 1))
        col = (150, 142, 136)
    o, top, _ = edges(m)
    sc.rgb[o & ~((Y == y1 - 1) & active)] = OUTL
    letters(sc, text, (x0 + x1) / 2, (y0 + y1) / 2 - 8, "text", 16, col=col, outline=False, shadow=not active,
            align="center")
    if badge:
        bx, by = x1 - 6, y0 + 3
        d = np.hypot(X - bx, Y - by)
        sc.rgb[d <= 6] = OUTL
        sc.rgb[d <= 5] = hexc("#c8402a")
        sc.rgb[d <= 2] = hexc("#e8603a")
        letters(sc, str(badge), bx, by - 8, "text", 16, col=(255, 236, 220), outline=False, shadow=False, align="center")
    sc.occ[m] = True
    sc.light[m] = 0


def cap_button(sc, cx, cy, r, text, kind="steel", pressed=False):
    """A small round push-button with its sign stamped on the cap (the battle's speed: pause, ×2, to the end)."""
    pushbutton(sc, cx, cy, r, kind=kind, pressed=pressed)
    dark = kind in ("brass", "hot")
    letters(sc, text, cx, cy - 8 + (1 if pressed else -1), "text", 16, col=(40, 26, 10) if dark else (226, 220, 210),
            outline=not dark, shadow=False, align="center")


def valve(sc, cx, cy, r=16, turning=False):
    """A valve's handwheel, red-painted iron: a flange behind it with bolts, a rim, four spokes, a brass nut on the
    hub; turning (the mouse on it) — the spokes a little round, a puff of steam."""
    X, Y = sc.xx - cx, sc.yy - cy
    d = np.hypot(X, Y)
    fl = d <= r + 4
    sc.rgb[fl] = hexc("#1a181c")
    fo, _, _ = edges(fl)
    sc.rgb[fo] = OUTL
    for a in np.linspace(0, 2 * np.pi, 7)[:-1] + 0.3:
        bx, by = int(round(cx + np.cos(a) * (r + 2))), int(round(cy + np.sin(a) * (r + 2)))
        sc.rgb[by, bx] = hexc("#8a8890")
    rim = (d <= r) & (d >= r - 3.5)
    lt = np.clip(0.55 - (X * 0.6 + Y * 0.8) / (2.0 * r), 0, 1)
    _ramp_fill(sc, rim, CAP["rust"], lt)
    a0 = 0.35 if turning else 0.0
    for k in range(4):
        a = a0 + k * np.pi / 2 + np.pi / 4
        dx, dy = np.cos(a), np.sin(a)
        along = X * dx + Y * dy
        across = np.abs(-X * dy + Y * dx)
        sp = (along > 2) & (along < r - 2) & (across <= 1.3)
        _ramp_fill(sc, sp, CAP["rust"], np.clip(lt - 0.1, 0, 1))
    hub = d <= 4
    _ramp_fill(sc, hub, ("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f4dc96"), np.clip(0.6 - (X + Y) / 8.0, 0, 1))
    ro, _, _ = edges((d <= r) & ~((d < r - 3.5) & ~hub & ~np.zeros_like(hub)))
    sc.rgb[edges(d <= r)[0]] = OUTL
    sc.rgb[edges((d < r - 3.5))[0] & ~(d <= 4)] = sc.rgb[edges((d < r - 3.5))[0] & ~(d <= 4)] * 0.6
    sc.rgb[cy, cx] = OUTL
    if turning:
        steam(sc, cx + r - 2, cy - r, 8, seed=cx)
    sc.occ[fl] = True


def wing(sc, x0, y0, x1, y1):
    """The title bar: an iron beam, hammered, a row of rivets along its foot and a brass strip under it."""
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    sc.rgb[m] = (hexc("#232126") * (1 - t) + hexc("#151418") * t)[m]
    hammered(sc, m, 31, k=0.16)
    for x in range(x0 + 10, x1, 22):
        rivet(sc, x, y1 - 7)
    sc.rgb[y1 - 3, x0:x1] = hexc("#8a6a34")
    sc.rgb[y1 - 2, x0:x1] = hexc("#c8a060")
    sc.rgb[y1 - 1, x0:x1] = OUTL
    sc.occ[m] = True
    sc.light[m] = 0


def socket(sc, x0, y0, x1, y1):
    """An empty socket in the beam, kept for a button to come: a recess with two screws."""
    sc.rgb[y0:y1, x0:x1] = sc.rgb[y0:y1, x0:x1] * 0.3 + hexc("#08070a") * 0.7
    sc.rgb[y0, x0:x1] = OUTL
    sc.rgb[y1 - 1, x0:x1] = hexc("#4a4850")
    sc.rgb[y0:y1, x0] = OUTL
    sc.rgb[y0:y1, x1 - 1] = hexc("#3a3840")
    screw(sc, x0 + 4, y0 + 4)
    screw(sc, x1 - 5, y1 - 5)


def sparks(sc, x, y, n=8, seed=0):
    """A spray of sparks flying off hot metal."""
    rnd = np.random.RandomState(int(seed) % 100000)
    for _ in range(n):
        a = rnd.uniform(-2.6, -0.4)
        L = rnd.uniform(3, 9)
        for k in range(int(L)):
            xx, yy = int(x + np.cos(a) * k), int(y + np.sin(a) * k + k * k * 0.04)
            if 0 <= xx < sc.w and 0 <= yy < sc.h:
                sc.rgb[yy, xx] = hexc("#fff0a0") if k > L - 2 else hexc("#ff9a3a")


def steam(sc, x, y, r=10, seed=0):
    """A puff of steam rising off the metal."""
    rnd = np.random.RandomState(seed)
    for _ in range(5):
        cx, cy, rr = x + rnd.uniform(-r, r) * 0.6, y - rnd.uniform(0, r), rnd.uniform(r * 0.3, r * 0.6)
        d = np.hypot(sc.xx - cx, sc.yy - cy)
        m = d < rr
        sc.rgb[m] = sc.rgb[m] * 0.75 + hexc("#b8b4b0") * 0.25


def chain(sc, x, y0, y1, col="#6a6870"):
    """A hanging chain: links alternating face-on and edge-on."""
    for k, y in enumerate(range(int(y0), int(y1), 5)):
        if k % 2 == 0:
            sc.rgb[y:y + 5, x - 2] = OUTL
            sc.rgb[y:y + 5, x + 2] = OUTL
            sc.rgb[y, x - 1:x + 2] = OUTL
            sc.rgb[y + 4, x - 1:x + 2] = OUTL
            sc.rgb[y + 1:y + 4, x - 1] = hexc(col)
            sc.rgb[y + 1:y + 4, x + 1] = hexc(col)
        else:
            sc.rgb[y:y + 5, x - 1:x + 2] = OUTL
            sc.rgb[y + 1:y + 4, x] = hexc("#9a98a0")


def levels(sc, x, y, lv, n=3):
    """A module's level I–III as notches in a brass bar: lit ones glow."""
    for k in range(n):
        xx = x + k * 6
        sc.rgb[y:y + 6, xx:xx + 4] = OUTL
        sc.rgb[y + 1:y + 5, xx + 1:xx + 3] = hexc("#ffc860") if k < lv else hexc("#3a3430")


def kit_sheet():
    from paths import out
    sc = forge(960, 300, 3)
    wing(sc, 0, 0, 960, 44)
    letters(sc, "НАБОР ЛИТЕЙЩИКА", 16, 8, "title", 24, col=(232, 220, 200), col2=(120, 90, 60))
    plate(sc, 12, 54, 948, 292)
    x = 26
    for kind in ("hot", "steel", "rust", "brass", "dull"):
        button(sc, x, 70, x + 170, 108, kind)
        x += 182
    sill(sc, 112, 170)
    lever(sc, 40, 116, 166)
    nameplate(sc, 60, 120, 230, 162, "В БОЙ")
    lever(sc, 252, 116, 166, pulled=True)
    nameplate(sc, 272, 120, 442, 162, "В БОЙ", heated=True)
    pushbutton(sc, 476, 141, 13, "steel")
    tag(sc, 496, 128, 610, 154, "Автосборка", "steel", wire_to=490)
    pushbutton(sc, 640, 141, 13, "steel", pressed=True)
    tag(sc, 660, 128, 760, 154, "Назад", "steel", wire_to=654)
    valve(sc, 790, 141, 15)
    tag(sc, 812, 128, 940, 154, "Починить · 2", "brass", wire_to=806)
    x = 26
    for st in ("normal", "hi", "hover", "new", "broken", "rare", "trophy"):
        cell(sc, x, 180, x + 120, 240, st)
        x += 130
    levels(sc, 830, 250, 2)
    socket(sc, 860, 246, 884, 270)
    chain(sc, 900, 246, 284)
    img = sc.image(2)
    img.save(out("foundry_ui_kit.png"))
    print("foundry_ui_kit.png", img.size)


if __name__ == "__main__":
    kit_sheet()
