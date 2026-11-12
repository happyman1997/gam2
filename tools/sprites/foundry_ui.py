"""The Foundry's interface: the swarm's grammar (swarm_ui) in the Foundry's own materials. The background is a
soot-black forge wall with the hearth's glow; panels are forged iron sheets with rivets and brass corners; cells are
iron frames with screwed brass angles; buttons are bars of metal, and what a button does is what metal it is —
hot metal for the action that moves the run on, dark tempered steel for going back, rust for what melts something
down, brass for what is on, dull iron for what can't be pressed. Under the mouse the metal heats up. Letters,
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
    button(sc, 26, 120, 196, 158, "hot", heated=True)
    x = 26
    for st in ("normal", "hi", "hover", "new", "broken", "rare", "trophy"):
        cell(sc, x, 180, x + 120, 240, st)
        x += 130
    levels(sc, 230, 136, 2)
    socket(sc, 300, 126, 332, 150)
    chain(sc, 360, 116, 170)
    sparks(sc, 420, 140, 12)
    img = sc.image(2)
    img.save(out("foundry_ui_kit.png"))
    print("foundry_ui_kit.png", img.size)


if __name__ == "__main__":
    kit_sheet()
