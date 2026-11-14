"""The swarm's interface kit, in the insects' own materials: a nest of wax cells behind everything, chitin plates for
panels, chamfered comb cells for cards, resin drops for buttons, a wing membrane for the title bar, an abdomen of
segments for the limit bar, antennae on the big panels. Pixel fonts: Press Start 2P for headings (OFL, in fonts/),
GNU Unifont for text (tools/sprites/fonts/unifont-18.0.01.otf, SIL OFL 1.1 — or GPL-2+ with the font exception).

    python3 tools/sprites/swarm_ui.py      -> out/swarm_ui_kit.png (every piece, in every state)
"""
import os
import zlib
import numpy as np
from PIL import ImageFont
from kit import *
from noise import value_noise
from paths import font

OUTL = hexc("#08060c")
INK, MUTED, GOLD, BIO, RED, GREEN, DARK = (236, 224, 196), (170, 156, 180), (240, 190, 90), (160, 230, 110), (240, 122, 96), (150, 220, 120), (40, 22, 8)
VIOLET = (196, 150, 255)
UNIFONT = font("unifont-18.0.01.otf")        # GNU Unifont: SIL OFL 1.1 (or GPL-2+ with the font exception), fonts/

# rims of the comb cells: (rim, rim highlight, fill)
CELL = {
    "normal": ("#4a3e5c", "#7a6c90", "#1a1322"),
    "hi": ("#c88a2a", "#ffd070", "#241a16"),
    "new": ("#4a8a2a", "#9ae060", "#16201a"),
    "eat": ("#a83a2e", "#f07a5a", "#2a1218"),
    "locked": ("#2a2432", "#3a3446", "#100c14"),
    "mut": ("#a8822a", "#e8c050", "#1e1a16"),
    "find": ("#6a4a9a", "#b090e0", "#1a1426"),
    "hover": ("#b8f030", "#f4ffb0", "#161c14"),     # under the mouse: bright acid and bites, whatever the cell is
}
BUTTON = {   # top → bottom of the resin, the shine, the text colour
    "amber": (("#ffe08a", "#f0a838", "#c06a14", "#6a3406"), "#fff8d8", DARK),
    "chitin": (("#7a6c90", "#463a58", "#2a2236", "#140e1c"), "#b8acd0", INK),
    "blood": (("#ff9a7a", "#d0402a", "#8a1810", "#3a0604"), "#ffd0c0", INK),
    "acid": (("#8ac850", "#4e8a24", "#2a5212", "#10220a"), "#c8f0a0", INK),
    "dim": (("#4a4256", "#2e2838", "#201a28", "#120e18"), "#6a6078", (120, 110, 130)),
}


# ---------------------------------------------------------------- fonts
def fnt(kind="text", size=16):
    if kind == "title":
        return ImageFont.truetype(font("PressStart2P-Regular.ttf"), size)
    if os.path.exists(UNIFONT):
        return ImageFont.truetype(UNIFONT, 32 if size >= 26 else 16)
    return ImageFont.truetype(font("PTSerif-Regular.ttf"), size)


def f(b, s):
    """A drop-in for the old (bold, size) helper: big numbers and headings, the rest in the text font."""
    if s >= 26:
        return fnt("text", 32)
    if b and s >= 19:
        return fnt("title", 16)
    return fnt("text", 16)


# ---------------------------------------------------------------- the nest behind everything
def hexline(sc, a, b, col, k=1.0):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
    for t in np.linspace(0, 1, n):
        x, y = int(round(a[0] + (b[0] - a[0]) * t)), int(round(a[1] + (b[1] - a[1]) * t))
        if 0 <= x < sc.w and 0 <= y < sc.h:
            sc.rgb[y, x] = sc.rgb[y, x] * (1 - k) + col * k


def nest(w, h, seed=1):
    """Dark wax comb: faint hexagons, darker tunnels gnawed through, a few old resin drips."""
    sc = Scene(w, h)
    n = value_noise(w, h, 14, seed) * 0.6 + value_noise(w, h, 5, seed + 1) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, c in enumerate(("#18121c", "#1c1520", "#201824", "#241b28")):
        sc.rgb[lv == i] = hexc(c)
    R = 13
    dx, dy = R * 1.5, R * np.sqrt(3)
    col = hexc("#2e2434")
    for i in range(int(w / dx) + 2):
        for j in range(int(h / dy) + 2):
            cx, cy = i * dx, j * dy + (dy / 2 if i % 2 else 0)
            pts = [(cx + R * np.cos(a), cy + R * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 7)]
            for p, q in zip(pts[:-1], pts[1:]):
                hexline(sc, p, q, col, 0.55)
    tun = value_noise(w, h, 40, seed + 7)
    sel = tun > 0.68
    sc.rgb[sel] *= 0.72
    rnd = np.random.RandomState(seed)
    for _ in range(6):
        x, y = rnd.randint(20, w - 20), rnd.randint(40, h - 40)
        for k in range(rnd.randint(6, 16)):
            sc.rgb[y + k, x] = sc.rgb[y + k, x] * 0.5 + hexc("#6a3a10") * 0.5
        sc.rgb[y + k:y + k + 2, x - 1:x + 2] = hexc("#8a5214")
    return sc


# ---------------------------------------------------------------- shapes
def comb(sc, m, x0, y0, col, k, R=7):
    """Faint wax comb inside a shape."""
    dx, dy = R * 1.5, R * np.sqrt(3)
    ys, xs = np.nonzero(m)
    if not len(xs):
        return
    for i in range(int((xs.max() - x0) / dx) + 2):
        for j in range(int((ys.max() - y0) / dy) + 2):
            cx, cy = x0 + i * dx, y0 + j * dy + (dy / 2 if i % 2 else 0)
            pts = [(cx + R * np.cos(a), cy + R * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 7)]
            for p, q in zip(pts[:-1], pts[1:]):
                n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) + 1
                for t in np.linspace(0, 1, n):
                    x, y = int(round(p[0] + (q[0] - p[0]) * t)), int(round(p[1] + (q[1] - p[1]) * t))
                    if 0 <= x < sc.w and 0 <= y < sc.h and m[y, x]:
                        sc.rgb[y, x] = sc.rgb[y, x] * (1 - k) + col * k



WOBBLE = [0.0]          # how far edges wander, in pixels (0 — straight); set by the screens that want a hand-drawn look


def chamfer_mask(sc, x0, y0, x1, y1, c):
    X, Y = sc.xx, sc.yy
    if WOBBLE[0]:
        rnd = np.random.RandomState(int(x0 * 7 + y0 * 13 + x1) % 100000)
        kx, ky = np.arange(0, sc.w + 12, 12), np.arange(0, sc.h + 12, 12)
        oy = np.interp(np.arange(sc.w), kx, rnd.uniform(-1, 1, len(kx)))
        ox = np.interp(np.arange(sc.h), ky, rnd.uniform(-1, 1, len(ky)))
        X = X + np.round(ox * WOBBLE[0])[:, None].astype(int)
        Y = Y + np.round(oy * WOBBLE[0])[None, :].astype(int)
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    m &= (X - x0) + (Y - y0) >= c
    m &= (x1 - 1 - X) + (Y - y0) >= c
    m &= (X - x0) + (y1 - 1 - Y) >= c
    m &= (x1 - 1 - X) + (y1 - 1 - Y) >= c
    return m


def edges(m):
    up = np.zeros_like(m); up[1:] = m[:-1]
    dn = np.zeros_like(m); dn[:-1] = m[1:]
    lf = np.zeros_like(m); lf[:, 1:] = m[:, :-1]
    rt = np.zeros_like(m); rt[:, :-1] = m[:, 1:]
    outer = m & ~(up & dn & lf & rt)
    top = m & ~up
    left = m & ~lf
    return outer, top, left


def shrink(m):
    o, _, _ = edges(m)
    return m & ~o


def plate(sc, x0, y0, x1, y1, tone="panel", antennae=False):
    """A chitin plate: segmented like a tergite, an oily sheen along the top, spiracles down the sides."""
    m = chamfer_mask(sc, x0, y0, x1, y1, 9)
    top_c, bot_c = (hexc("#211828"), hexc("#140e1a")) if tone == "panel" else (hexc("#2a2034"), hexc("#18121e"))
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    sc.rgb[m] = (top_c * (1 - t) + bot_c * t)[m]
    for y in range(y0 + 14, y1 - 6, 16):                      # the segments
        row = m[y] & m[min(y + 1, sc.h - 1)]
        sc.rgb[y, row] = sc.rgb[y, row] * 0.7
        sc.rgb[y + 1, row] = sc.rgb[y + 1, row] * 0.85 + hexc("#3a3048") * 0.15
    o, top, left = edges(m)
    inner = shrink(m)
    o2, top2, left2 = edges(inner)
    sc.rgb[o] = OUTL
    sc.rgb[top2] = hexc("#5a4e6a")
    sc.rgb[left2 & ~top2] = hexc("#3e3450")
    bot2 = o2 & ~top2 & ~left2
    sc.rgb[bot2] = hexc("#0e0a12")
    # the sheen: a soft lighter streak under the top edge
    sh = m & (sc.yy >= y0 + 2) & (sc.yy < y0 + 4) & (sc.xx > x0 + 10) & (sc.xx < x0 + (x1 - x0) * 0.6)
    sc.rgb[sh] = sc.rgb[sh] * 0.6 + hexc("#7a6c90") * 0.4
    for y in range(y0 + 22, y1 - 14, 34):                     # spiracles
        for x in (x0 + 3, x1 - 4):
            sc.rgb[y - 1:y + 2, x - 1:x + 2] = hexc("#3a3048")
            sc.rgb[y, x] = OUTL
    for x in range(x0 + 30, x1 - 24, 48):                     # the top rim in overlapping scutes
        sc.rgb[y0 + 1:y0 + 4, x] = OUTL
        sc.rgb[y0 + 2, x + 1:x + 6] = hexc("#7a6c90")
    sc.occ[m] = True
    sc.light[m] = 0
    if y1 - y0 > 60:
        for y in range(y0 + 30, y1 - 24, 46):                 # short bone spines off the sides
            for x, sd in ((x0, -1), (x1 - 1, 1)):
                for k in range(4):
                    yy, xx = y - k // 2, x + sd * k
                    if 0 <= xx < sc.w:
                        sc.rgb[yy, xx] = hexc("#8a7a66") if k < 3 else hexc("#c8b898")
    if antennae:
        antenna(sc, x0 + 16, y0, -1)
        antenna(sc, x1 - 16, y0, 1)
        for x, sd in ((x0 + 6, 1), (x1 - 7, -1)):              # mandible hooks at the bottom corners
            for k in range(7):
                yy, xx = y1 - 1 + (k if k < 4 else 6 - k), x + sd * k
                if 0 <= yy < sc.h:
                    sc.rgb[yy, xx] = hexc("#5a4e6a")
                    sc.rgb[min(yy + 1, sc.h - 1), xx] = OUTL


def antenna(sc, x, y, side):
    """A thin antenna curling off a panel's top corner, a knob at its tip."""
    pts = []
    for t in np.linspace(0, 1, 60):
        pts.append((x + side * (6 * t + 20 * t * t), y - 2 - 10 * t + 5 * t * t * t))
    for i, (px, py) in enumerate(pts):
        if 0 <= int(py) < sc.h:
            sc.rgb[int(py), int(px)] = hexc("#6a5e7e") if (i // 6) % 2 else hexc("#4a3e5c")
            sc.rgb[int(py) + 1, int(px)] = OUTL
    px, py = pts[-1]
    sc.rgb[int(py) - 1:int(py) + 2, int(px) - 1:int(px) + 2] = hexc("#8a7ca0")


def cell(sc, x0, y0, x1, y1, state="normal", col=None):
    """A comb cell: a chamfered card with a wax rim; the state colours the rim (and the fill when marked to be eaten)."""
    rim, hi, fill = CELL[state]
    if col is not None:
        rim, hi = col, col
    c = max(8, min(14, int((y1 - y0) * 0.16)))
    m = chamfer_mask(sc, x0, y0, x1, y1, c)
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    base = hexc(fill)
    sc.rgb[m] = (base * (1.15 - 0.3 * t))[m]
    # a soft membrane glow low in the cell
    e = ((sc.xx - (x0 + x1) / 2) / ((x1 - x0) * 0.55)) ** 2 + ((sc.yy - y1 + 10) / ((y1 - y0) * 0.5)) ** 2
    glo = m & (e < 1)
    sc.rgb[glo] = sc.rgb[glo] * 0.88 + hexc("#3a2c48") * 0.12
    comb(sc, m, x0, y0, hexc(rim), 0.07)
    o, top, left = edges(m)
    sc.rgb[o] = OUTL
    r1 = shrink(m)
    o1, top1, left1 = edges(r1)
    sc.rgb[o1] = hexc(rim)
    sc.rgb[(top1 | left1) & o1] = hexc(hi)
    r2 = shrink(r1)
    o2, _, _ = edges(r2)
    sc.rgb[o2] = sc.rgb[o2] * 0.6 + hexc(rim) * 0.2
    # comb notches at the chamfers
    for (cx, cy, dx, dy) in ((x0 + c, y0 + 2, -1, 1), (x1 - c - 1, y0 + 2, 1, 1)):
        for k in range(3):
            if 0 <= cy + k < sc.h:
                sc.rgb[cy + k, cx + dx * k] = hexc(hi)
    sc.occ[m] = True
    sc.light[m] = 0
    if state in ("hi", "mut", "find", "hover") or col is not None and state == "hi":
        halo = chamfer_mask(sc, x0 - 2, y0 - 2, x1 + 2, y1 + 2, c + 1) & ~m
        th = BAYER[sc.yy % 4, sc.xx % 4]
        sc.rgb[halo & (th < 0.6)] = sc.rgb[halo & (th < 0.6)] * 0.4 + hexc(hi) * 0.6
    if state == "hover":                              # bitten: the swarm is already eating the edge, as on a button
        w_ = x1 - x0
        for bx, by, br in ((x0 + w_ * 0.23, y0, 4), (x0 + w_ * 0.31, y0 + 1, 2.5), (x1 - w_ * 0.28, y1 - 1, 4),
                           (x1, y0 + (y1 - y0) * 0.55, 3)):
            d = np.hypot(sc.xx - bx, sc.yy - by)
            sc.rgb[d <= br] = hexc("#0a060e")
            ring = (d > br) & (d <= br + 1.2) & (m | halo)
            sc.rgb[ring] = hexc(rim)
    state_mark(sc, x0, y0, x1, y1, state, rim, hi)


def _px(sc, rows, x, y, pal, z=2):
    """A small mark drawn from rows of letters at z× size, with a dark outline round it."""
    pts = [(i, j, ch) for j, row in enumerate(rows) for i, ch in enumerate(row) if ch != "."]
    for i, j, _ in pts:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xx, yy = int(x + i * z + dx), int(y + j * z + dy)
            sc.rgb[max(0, yy):max(0, yy + z), max(0, xx):max(0, xx + z)] = OUTL
    for i, j, ch in pts:
        xx, yy = int(x + i * z), int(y + j * z)
        sc.rgb[max(0, yy):max(0, yy + z), max(0, xx):max(0, xx + z)] = hexc(pal[ch])
        sc.occ[max(0, yy):max(0, yy + z), max(0, xx):max(0, xx + z)] = True


def state_mark(sc, x0, y0, x1, y1, state, rim, hi):
    """Each state of a cell has a shape as well as a colour, so it reads without telling green from red:
    chosen — a tab pointing in from the left; new — an arrow up; to be eaten — teeth along the bottom;
    a mutation — a twist of a helix; a find — a gem; under the mouse — the bites (in cell())."""
    cy = (y0 + y1) // 2
    if state == "hi":
        _px(sc, ["a..", "aa.", "aAa", "aa.", "a.."], x0 - 3, cy - 7, {"a": hi, "A": "#fff0b0"}, z=3)
    elif state == "new":
        _px(sc, [".g.", "gGg", ".G.", ".G."], x1 - 14, y0 + 5, {"g": hi, "G": "#f0ffd0"})
    elif state == "eat":
        for k in range(4):
            _px(sc, ["www", ".w."], x1 - 60 + k * 9, y1 - 9, {"w": "#f4ecd8"})
    elif state == "mut":
        _px(sc, ["a.b", ".a.", "b.a"], x1 - 14, y0 + 6, {"a": hi, "b": "#c04a3a"})
    elif state == "find":
        _px(sc, ["..p..", ".pWp.", "pWWWp", ".pWp.", "..p.."], x1 - 18, y0 + 5, {"p": hi, "W": "#ffffff"})


def _ramp_fill(sc, m, x0, y0, h, ramp_, X, Y):
    t = np.clip((Y - y0) / max(1, h), 0, 1)
    pal = np.array([hexc(c) for c in ramp_])
    idx = np.clip(np.floor(t * 3.6 + BAYER[Y % 4, X % 4] * 0.6), 0, 3).astype(int)
    sc.rgb[m] = pal[idx][m]


def button(sc, x0, y0, x1, y1, kind="amber"):
    """A gem set in chitin: a long hexagon of resin (or shell) in a dark inlay rim, a keel of light along it,
    spiracle studs at the ends, mandible hooks curling off both tips. Amber holds a gnat caught in it; chitin
    shimmers like a beetle's back."""
    ramp_, shine, _ = BUTTON[kind]
    X, Y = sc.xx, sc.yy
    h = y1 - y0
    cy = (y0 + y1 - 1) / 2
    small = h < 28

    def hexm(a, b, c, d, k=0.9):
        mm = (Y >= b) & (Y < d) & (X >= a) & (X < c)
        half = max(1, (d - b) / 2)
        mm &= (X - a) >= np.abs(Y - (b + d - 1) / 2) * k
        mm &= (c - 1 - X) >= np.abs(Y - (b + d - 1) / 2) * k
        return mm
    outer = hexm(x0, y0, x1, y1)
    rim = outer & ~hexm(x0 + 2, y0 + 2, x1 - 2, y1 - 2)
    body = hexm(x0 + 2, y0 + 2, x1 - 2, y1 - 2)
    # the inlay rim: dark chitin with a light top edge
    sc.rgb[rim] = hexc("#1a1222")
    o, top, left = edges(outer)
    sc.rgb[o] = OUTL
    rt = rim & ~o & (Y < cy)
    sc.rgb[rt] = sc.rgb[rt] * 0.5 + hexc("#6a5e7e") * 0.5
    # the gem
    _ramp_fill(sc, body, x0, y0 + 2, h - 4, ramp_, X, Y)
    if kind == "chitin":                                     # a beetle's iridescence drifting along it
        hue = (X - x0) / max(1, x1 - x0)
        iri = np.stack([90 + 60 * np.sin(hue * 6.0), 70 + 70 * np.sin(hue * 6.0 + 2.1), 120 + 60 * np.sin(hue * 6.0 + 4.2)], -1)
        band = body & (Y < cy)
        sc.rgb[band] = sc.rgb[band] * 0.7 + iri[band] * 0.3
    bo, btop, bleft = edges(body)
    sc.rgb[btop] = sc.rgb[btop] * 0.35 + hexc(shine) * 0.65
    bb = bo & ~btop & (Y > cy)
    sc.rgb[bb] = sc.rgb[bb] * 0.55
    keel = body & (Y == int(y0 + 2 + (h - 4) * 0.32)) & (X > x0 + h * 0.6) & (X < x1 - h * 0.6) & ((X // 3) % 2 == 0)
    sc.rgb[keel] = sc.rgb[keel] * 0.45 + hexc(shine) * 0.55
    if kind == "amber" and not small:                         # bubbles, and a gnat caught in the resin
        rnd = np.random.RandomState(int(x0 + y0))
        for _ in range(int((x1 - x0) / 12)):
            bx, by = rnd.uniform(x0 + h * 0.7, x1 - h * 0.7), rnd.uniform(y0 + h * 0.45, y1 - 4)
            r_ = rnd.choice((1, 1, 2))
            bub = ((X - bx) ** 2 + (Y - by) ** 2 <= r_ * r_) & body
            sc.rgb[bub] = sc.rgb[bub] * 0.45 + hexc(shine) * 0.55
        gx, gy = int(x1 - h * 1.15), int(cy + 1)
        gnat = [(0, 0), (1, 0), (2, 0), (-1, 0), (1, -1), (3, -1), (-1, 1), (1, 1), (3, 1), (-2, -1), (-3, -2), (-2, 1), (0, -2), (2, -2)]
        for dx, dy in gnat:
            sc.rgb[gy + dy, gx + dx] = sc.rgb[gy + dy, gx + dx] * 0.25 + hexc("#3a1a04") * 0.75
        sc.rgb[gy - 3, gx - 1:gx + 2] = sc.rgb[gy - 3, gx - 1:gx + 2] * 0.6 + hexc("#fff0c0") * 0.4    # its wings catch the light
    if not small:
        for x_, sd in ((x0 + h * 0.62, 1), (x1 - 1 - h * 0.62, -1)):     # spiracle studs at the ends
            xi, yi = int(x_), int(cy)
            sc.rgb[yi - 2:yi + 3, xi - 1:xi + 2] = OUTL
            sc.rgb[yi - 1:yi + 2, xi - 2:xi + 3] = OUTL
            sc.rgb[yi - 1:yi + 2, xi - 1:xi + 2] = hexc("#5a4e6a")
            sc.rgb[yi, xi] = hexc(shine)
        gk = {"amber": "eat", "chitin": "violet", "blood": "over", "acid": "ok", "dim": "dim"}[kind]
        for (tx, sd) in ((x0, -1), (x1 - 1, 1)):                          # a gem at each tip, bone mandibles around it
            gx_ = tx + sd * 5
            for up in (-1, 1):
                pts = []
                for k in range(13):                              # a pincer closing round the gem
                    t = k / 12
                    pts.append((tx + sd * (1 + 10 * t), cy + up * (h * 0.3 * (1 - t * t) + 1.2 + h * 0.1 * np.sin(np.pi * t))))
                for n_, (px, py) in enumerate(pts):
                    px, py = int(round(px)), int(round(py))
                    if 0 <= px < sc.w and 0 <= py < sc.h:
                        sc.rgb[py, px] = hexc("#d8c8a8") if n_ < 10 else hexc("#f4ecd8")
                        if 0 <= py + up < sc.h:
                            sc.rgb[py + up, px] = OUTL
                        if 0 <= py - up < sc.h and n_ < 7:
                            sc.rgb[py - up, px] = hexc("#8a7a66")
            gem(sc, tx + sd * 6, cy, 3.4, h * 0.16 + 1, gk)
    sc.occ[outer] = True
    sc.light[outer] = 0
    if kind == "amber":
        sc.glow((x0 + x1) / 2, cy, (x1 - x0) * 0.42, hexc("#ffa030"), 0.18)


def wing(sc, x0, y0, x1, y1):
    """The title bar: a dark wing membrane with branching veins, a chitin rim beneath."""
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    sc.rgb[m] = hexc("#140f1a")
    th = BAYER[sc.yy % 4, sc.xx % 4]
    shim = m & (th < 0.2) & (value_noise(sc.w, sc.h, 30, 9) > 0.55)
    sc.rgb[shim] = hexc("#1e1828")
    rnd = np.random.RandomState(4)
    vein = hexc("#3a3050")
    for k in range(9):                                         # long veins from the left, forking
        yb = y0 + 4 + k * (y1 - y0 - 8) / 8
        pts = [(x0, yb)]
        x, y = x0, yb
        while x < x1:
            x += rnd.uniform(30, 70)
            y = np.clip(y + rnd.uniform(-5, 5), y0 + 2, y1 - 3)
            pts.append((min(x, x1 - 1), y))
        for p, q in zip(pts[:-1], pts[1:]):
            hexline(sc, p, q, vein, 0.8)
            if rnd.rand() < 0.35:
                hexline(sc, q, (q[0] + rnd.uniform(10, 24), np.clip(q[1] + rnd.choice((-1, 1)) * rnd.uniform(4, 9), y0 + 1, y1 - 2)), vein, 0.6)
    sc.rgb[y1 - 3, x0:x1] = hexc("#3a3048")
    sc.rgb[y1 - 2, x0:x1] = hexc("#5a4e6a")
    sc.rgb[y1 - 1, x0:x1] = OUTL
    for x in range(x0 + 6, x1, 16):
        sc.rgb[y1 - 3:y1 - 1, x] = OUTL
    sc.occ[m] = True
    sc.light[m] = 0


GEM = {   # facets: top-left (lit), top-right, bottom-left, bottom-right (shade), the glint
    "ok": ("#b8f070", "#7ac040", "#4e8a24", "#2a5212", "#f0ffd0"),
    "over": ("#ff9a7a", "#d84a30", "#9a2418", "#4a0a06", "#ffe0d0"),
    "eat": ("#ffe08a", "#e8a838", "#b06a14", "#5a3006", "#fff8d8"),
    "dim": ("#5a4e6a", "#463a58", "#2e2638", "#1a1422", "#8a7ca0"),
    "violet": ("#d8b0ff", "#a070e0", "#6a40a8", "#3a2060", "#f4e8ff"),
}


def gem(sc, cx, cy, a, b, kind="ok", bite=False, crack=False):
    """One rhombus scale cut like a gem: four facets, a glint, a dark outline; bitten or cracked if asked."""
    X, Y = sc.xx, sc.yy
    m = (np.abs(X - cx) / a + np.abs(Y - cy) / b) <= 1.0
    if bite:                                               # a bite taken out of the top right
        m &= ((X - (cx + a * 0.55)) ** 2 + (Y - (cy - b * 0.55)) ** 2) > (a * 0.55) ** 2
    tl, tr, bl, br, gl = (hexc(c) for c in GEM[kind])
    sc.rgb[m & (X < cx) & (Y < cy)] = tl
    sc.rgb[m & (X >= cx) & (Y < cy)] = tr
    sc.rgb[m & (X < cx) & (Y >= cy)] = bl
    sc.rgb[m & (X >= cx) & (Y >= cy)] = br
    inner = (np.abs(X - cx) / (a * 0.45) + np.abs(Y - cy) / (b * 0.45)) <= 1.0
    sc.rgb[m & inner] = sc.rgb[m & inner] * 0.6 + tl * 0.4
    o, top, left = edges(m)
    sc.rgb[o] = OUTL
    gx, gy = int(cx - a * 0.35), int(cy - b * 0.35)
    if m[gy, gx]:
        sc.rgb[gy, gx] = gl
    if bite:
        bo = o & (((X - (cx + a * 0.55)) ** 2 + (Y - (cy - b * 0.55)) ** 2) <= (a * 0.55 + 1.2) ** 2)
        sc.rgb[bo & ((X + Y) % 2 == 0)] = hexc("#fff0c0")          # tooth marks along the bite
    if crack:
        for k in range(int(b * 1.4)):
            yy = int(cy - b * 0.7 + k)
            xx = int(cx + (1 if (k // 2) % 2 else -1) * 0.8)
            if m[yy, xx]:
                sc.rgb[yy, xx] = OUTL
    sc.occ[m] = True
    sc.light[m] = 0
    return m


def segbar(sc, x0, y0, x1, h, total, limit, marked, creature=True):
    """The limit as a centipede: one gem-cut scale per point, legs under them, a head with mandibles and antennae
    on the left, the tail's cerci on the right. Within the limit the scales glow acid-green, over it they are
    cracked and red, the ones marked to be eaten amber with a bite out of them; a bone pin stands at the limit."""
    hd, tl = (16, 10) if creature else (0, 0)
    bx0, bx1 = x0 + hd, x1 - tl
    n = total
    w = (bx1 - bx0) / n
    cy = y0 + h / 2
    a, b = max(3.0, w * 0.62), h / 2 + 2
    # the spine under the scales
    sc.rgb[int(cy):int(cy) + 2, int(bx0):int(bx1)] = hexc("#1a1222")
    for i in range(n):                                     # legs
        lx = int(bx0 + (i + 0.5) * w)
        sd = -1 if i % 2 else 1
        for k in range(4):
            yy, xx = int(cy + b - 1 + k), lx + sd * (k // 2)
            if 0 <= yy < sc.h:
                sc.rgb[yy, xx] = hexc("#4a3e5c") if k < 3 else hexc("#7a6c90")
    for i in range(n):
        cx = bx0 + (i + 0.5) * w
        if i >= n - marked:
            gem(sc, cx, cy, a, b, "eat", bite=True)
        elif i >= limit:
            gem(sc, cx, cy, a, b, "over", crack=True)
        else:
            gem(sc, cx, cy, a, b, "ok")
    if creature:                                           # the head: a dark helmet, a red eye, mandibles, antennae
        hx, hy = x0 + 9, cy
        X, Y = sc.xx, sc.yy
        head = ((X - hx) / 8.0) ** 2 + ((Y - hy) / (b + 1)) ** 2 <= 1
        sc.rgb[head] = hexc("#2e2438")
        sc.rgb[head & (Y < hy - 1)] = hexc("#4a3e5c")
        o, _, _ = edges(head)
        sc.rgb[o] = OUTL
        sc.rgb[int(hy) - 2:int(hy), int(hx) - 4:int(hx) - 2] = hexc("#ff4a2a")
        for up in (-1, 1):                                 # mandibles
            for k in range(6):
                xx, yy = int(hx - 7 - k), int(hy + up * (2 + (k * k) // 6))
                sc.rgb[yy, xx] = hexc("#c8b898") if k < 5 else hexc("#f0e6c8")
        for k in range(14):                                # antennae sweeping back over the body
            xx, yy = int(hx - 3 + k * 1.6), int(hy - b - 1 - 6 * np.sin(k / 14 * np.pi))
            if 0 <= yy < sc.h:
                sc.rgb[yy, xx] = hexc("#6a5e7e")
        tx = int(bx1 + 1)                                  # the tail's cerci
        for up in (-1, 1):
            for k in range(8):
                xx, yy = tx + k, int(cy + up * (k * 0.6))
                sc.rgb[yy, xx] = hexc("#6a5e7e") if k < 6 else hexc("#a898c0")
    lx = int(bx0 + limit * w)                               # the bone pin at the limit
    sc.rgb[int(y0 - 7):int(y0 + h + 7), lx - 1:lx + 1] = hexc("#e8dcc0")
    sc.rgb[int(y0 - 7):int(y0 + h + 7), lx + 1] = OUTL
    sc.rgb[int(y0 - 10):int(y0 - 6), lx - 2:lx + 2] = hexc("#f4ecd8")
    sc.rgb[int(y0 - 10), lx - 2:lx + 2] = OUTL
    return bx0, w


def meter(sc, x0, y0, x1, h, n, filled, col="#b04a3a"):
    """A short row of gem scales: how many of n are lit (kills by trait and the like)."""
    w = (x1 - x0) / n
    kind = "over" if col in ("#c04a3a", "#b04a3a") else ("eat" if col in ("#d08a3a",) else "violet")
    for i in range(n):
        gem(sc, x0 + (i + 0.5) * w, y0 + h / 2, max(2.5, w * 0.6), h / 2 + 1.5, kind if i < filled else "dim")


def round_button(sc, cx, cy, r, kind="chitin"):
    button(sc, cx - r, cy - r, cx + r, cy + r, kind)


# ---------------------------------------------------------------- soul: lettering, the swarm's script, drips, webs, crawlers
FONT_FILE = {"title": "PressStart2P-Regular.ttf"}


def _font(kind, px):
    if kind == "title":
        return ImageFont.truetype(font(FONT_FILE["title"]), px)
    if os.path.exists(UNIFONT):
        return ImageFont.truetype(UNIFONT, px)
    return ImageFont.truetype(font("PTSerif-Bold.ttf"), px)


def text_width(text, kind="text", px=16):
    return int(_font(kind, px).getlength(text))


def rich_width(text, kind="text", px=16):
    """The width of a text with damage-type glyphs in it ("{дроб}" and the like, see dmg.py)."""
    import dmg
    return sum(text_width(s, kind, px) if k == "t" else dmg.width(s) + 2 for k, s in dmg.parts(text))


def rich(sc, text, x, y, kind="text", px=16, col=INK, align="left", **kw):
    """letters(), with each damage type drawn as its glyph instead of the word."""
    import dmg
    w = rich_width(text, kind, px)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    for k, s in dmg.parts(text):
        if k == "t":
            letters(sc, s, x, y, kind, px, col=col, **kw)
            x += text_width(s, kind, px)
        else:
            gh = dmg.rgba(s).shape[0]
            dmg.draw(sc, s, x + 1, y + px / 2 - gh / 2 + 1)
            x += dmg.width(s) + 2
    return w


def letters(sc, text, x, y, kind="text", px=16, col=INK, col2=None, outline=True, shadow=True, jitter=0, drips=0,
            hairs=0, align="left", seed=0):
    """Text drawn into the scene itself, on its pixel grid: dark outline, a shadow, a light top on each stroke,
    the letters dancing off the baseline (jitter), ichor running down (drips), bristles on top (hairs)."""
    from PIL import Image, ImageDraw
    f_ = _font(kind, px)
    rnd = np.random.RandomState((zlib.crc32(text.encode("utf-8")) + seed) % 2 ** 31)   # the same every run
    W_ = int(f_.getlength(text)) + 8
    H_ = px + 8 + jitter * 2 + drips + 4
    im = Image.new("L", (W_, H_), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    cx = 3
    for ch in text:
        dy = rnd.randint(-jitter, jitter + 1) if jitter else 0
        d.text((cx, 2 + jitter + dy), ch, font=f_, fill=255)
        cx += f_.getlength(ch)
    m = np.array(im) > 127
    ys, xs = np.nonzero(m)
    if not len(xs):
        return 0
    if align == "center":
        x = x - (xs.max() + 1) / 2
    elif align == "right":
        x = x - (xs.max() + 1)
    X0, Y0 = int(round(x)) - 3, int(round(y)) - 2 - jitter
    h, w = m.shape
    big = np.zeros((sc.h, sc.w), bool)
    ya, yb, xa, xb = max(0, Y0), min(sc.h, Y0 + h), max(0, X0), min(sc.w, X0 + w)
    if yb <= ya or xb <= xa:
        return 0
    big[ya:yb, xa:xb] = m[ya - Y0:yb - Y0, xa - X0:xb - X0]
    if drips:                                    # runs of ichor from the bottoms of some strokes
        bottom = big & ~np.roll(big, -1, 0)
        by_, bx_ = np.nonzero(bottom)
        for k in rnd.choice(len(bx_), size=min(len(bx_), max(1, len(text) // 3)), replace=False):
            L = rnd.randint(2, drips + 1)
            yy, xx = by_[k], bx_[k]
            big[yy:min(sc.h, yy + L), xx] = True
            if yy + L + 1 < sc.h and xx + 1 < sc.w:
                big[yy + L - 1:yy + L + 1, xx:xx + 2] = True
    if hairs:
        topm = big & ~np.roll(big, 1, 0)
        ty, tx = np.nonzero(topm)
        for k in rnd.choice(len(tx), size=min(len(tx), hairs), replace=False):
            L = rnd.randint(2, 4)
            sd = rnd.choice((-1, 1))
            for j in range(1, L + 1):
                yy, xx = ty[k] - j, tx[k] + (sd if j > 1 else 0)
                if 0 <= yy and 0 <= xx < sc.w:
                    big[yy, xx] = True
    if shadow:
        sh = np.roll(np.roll(big, 1, 0), 1, 1) & ~big
        sc.rgb[sh] = sc.rgb[sh] * 0.35
    if outline:
        dil = big | np.roll(big, 1, 0) | np.roll(big, -1, 0) | np.roll(big, 1, 1) | np.roll(big, -1, 1)
        sc.rgb[dil & ~big] = OUTL
        sc.occ[dil] = True
        sc.light[dil] = 0
    c1 = np.array(col, float)
    c2 = np.array(col2 if col2 is not None else tuple(v * 0.62 for v in col), float)
    ty0, ty1 = ys.min() + Y0, ys.max() + Y0
    t = np.clip((sc.yy - ty0) / max(1, ty1 - ty0), 0, 1)[..., None]
    fill = c1 * (1 - t) + c2 * t
    sc.rgb[big] = fill[big]
    top = big & ~np.roll(big, 1, 0)
    sc.rgb[top] = np.minimum(255, sc.rgb[top] * 1.25 + 18)
    return int(xs.max() + 1)


SCRIPT = ["x.x/.x.", ".x./x.x", "xx./.xx", "x.x/xxx", ".x./xxx", "x../.xx", "xxx/x.x", "x.x/.x.", "..x/xx.", "xx./x.."]


def scribble(sc, x, y, w, col=hexc("#6a4a9a"), seed=0, k=0.85):
    """The swarm's own script: a row of little leg-and-body glyphs, like a translation nobody asked for."""
    rnd = np.random.RandomState(seed)
    cx = x
    while cx < x + w - 6:
        g = SCRIPT[rnd.randint(len(SCRIPT))].split("/")
        tall = rnd.rand() < 0.25
        for j, row in enumerate(g):
            for i, ch in enumerate(row):
                if ch == "x":
                    yy, xx = int(y + j * 2 - (2 if tall and j == 0 else 0)), int(cx + i * 1.5)
                    sc.rgb[yy:yy + 2, xx:xx + 1] = sc.rgb[yy:yy + 2, xx:xx + 1] * (1 - k) + col * k
        if rnd.rand() < 0.3:                                   # a leg dropping below the line
            sc.rgb[int(y + 4):int(y + 7), int(cx + 2)] = sc.rgb[int(y + 4):int(y + 7), int(cx + 2)] * (1 - k) + col * k
        cx += 6 + rnd.randint(0, 2) + (4 if rnd.rand() < 0.15 else 0)


def drips(sc, x0, x1, y, col="#c07018", n=4, seed=0, Lmax=14):
    """Resin (or ichor) running off the bottom edge of something."""
    rnd = np.random.RandomState(seed)
    c = hexc(col)
    for _ in range(n):
        x = int(rnd.uniform(x0 + 6, x1 - 6))
        L = rnd.randint(3, Lmax)
        for k in range(L):
            w = 2 if k < L * 0.6 else 1
            sc.rgb[y + k, x:x + w] = c * (1.0 - 0.25 * k / L)
            sc.rgb[y + k, x + w] = OUTL
        sc.rgb[y + L - 1:y + L + 2, x - 1:x + 2] = c * 1.15
        sc.rgb[y + L - 1, x - 1] = np.minimum(255, c * 1.6)
        sc.occ[y:y + L + 2, x - 1:x + 3] = True


def silk(sc, a, b, sag=8, col="#d8d0c0", k=0.75):
    c = hexc(col)
    n = int(np.hypot(b[0] - a[0], b[1] - a[1])) + 2
    for i, t in enumerate(np.linspace(0, 1, n)):
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t + sag * 4 * t * (1 - t)
        if 0 <= int(y) < sc.h and 0 <= int(x) < sc.w and i % 5 != 4:
            sc.rgb[int(y), int(x)] = sc.rgb[int(y), int(x)] * (1 - k) + c * k


def cobweb(sc, x, y, r, quad=(1, 1), col="#b8b0a8"):
    """A cobweb filling a corner: spokes, and threads strung between them."""
    c = hexc(col)
    angs = np.linspace(0, np.pi / 2, 6)
    sx, sy = quad
    for a in angs:
        hexline(sc, (x, y), (x + sx * np.cos(a) * r, y + sy * np.sin(a) * r), c, 0.55)
    for f_ in (0.3, 0.5, 0.72, 0.95):
        pts = [(x + sx * np.cos(a) * r * f_, y + sy * np.sin(a) * r * f_) for a in angs]
        for p, q in zip(pts[:-1], pts[1:]):
            mid = ((p[0] + q[0]) / 2 - sx * 2 * f_, (p[1] + q[1]) / 2 - sy * 2 * f_)
            hexline(sc, p, mid, c, 0.45)
            hexline(sc, mid, q, c, 0.45)


def engrave(sc, spr, x, by, col="#2c2238", k=0.9, flip=False):
    """A sprite as an old engraving behind the interface: its outline and sparse hatching, in one dull colour."""
    a = spr.a[:, ::-1] if flip else spr.a
    ox = spr.w - 1 - spr.ox if flip else spr.ox
    up = np.zeros_like(a); up[1:] = a[:-1]
    dn = np.zeros_like(a); dn[:-1] = a[1:]
    lf = np.zeros_like(a); lf[:, 1:] = a[:, :-1]
    rt = np.zeros_like(a); rt[:, :-1] = a[:, 1:]
    edge = a & ~(up & dn & lf & rt)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    lum = (spr.rgb[:, ::-1] if flip else spr.rgb).mean(axis=2)
    hatch = a & ~edge & ((xx + yy) % 4 == 0) & (lum < 70)
    X0, Y0 = int(x - ox), int(by - spr.oy)
    c = hexc(col)
    for msk in (edge, hatch):
        ys, xs = np.nonzero(msk)
        ys, xs = ys + Y0, xs + X0
        ok = (ys >= 0) & (ys < sc.h) & (xs >= 0) & (xs < sc.w)
        ys, xs = ys[ok], xs[ok]
        sc.rgb[ys, xs] = sc.rgb[ys, xs] * (1 - k) + c * k


def creature(sc, spr, x, by, shadow=True):
    """A live one sitting on the interface."""
    if shadow:
        e = ((sc.xx - x) / max(4, spr.w * 0.3)) ** 2 + ((sc.yy - by) / 2.5) ** 2
        sc.rgb[e <= 1] *= 0.6
    sc.blit(spr, int(x - spr.ox), int(by - spr.oy))
    ys, xs = np.nonzero(spr.a)
    sc.occ[ys + int(by - spr.oy), xs + int(x - spr.ox)] = True


# ---------------------------------------------------------------- a look at the kit
def kit_sheet():
    from paths import out
    from PIL import ImageDraw
    S = 2
    sc = nest(960, 420, 3)
    wing(sc, 0, 0, 960, 30)
    plate(sc, 12, 44, 470, 400, antennae=True)
    for i, st in enumerate(("normal", "hi", "new", "eat", "locked", "mut", "find")):
        x0 = 490 + (i % 4) * 116
        y0 = 56 + (i // 4) * 110
        cell(sc, x0, y0, x0 + 108, y0 + 96, st)
    for i, k in enumerate(BUTTON):
        button(sc, 30 + (i % 2) * 220, 70 + (i // 2) * 52, 30 + (i % 2) * 220 + 200, 70 + (i // 2) * 52 + 34, k)
    round_button(sc, 60, 250, 11, "blood")
    round_button(sc, 90, 250, 11, "chitin")
    segbar(sc, 40, 300, 440, 12, 53, 45, 5)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    d.text((20, 18), "РОЙ · НАБОР ИНТЕРФЕЙСА", font=fnt("title", 16), fill=INK)
    for i, k in enumerate(BUTTON):
        x, y = (30 + (i % 2) * 220 + 100) * S, (70 + (i // 2) * 52 + 9) * S
        t = {"amber": "Мутировать", "chitin": "Автоотбор", "blood": "Съесть", "acid": "Эволюция · 15", "dim": "В бой"}[k]
        d.text((x - d.textlength(t, font=fnt()) / 2, y), t, font=fnt(), fill=BUTTON[k][2])
    for i, st in enumerate(("normal", "hi", "new", "eat", "locked", "mut", "find")):
        x0 = 490 + (i % 4) * 116
        y0 = 56 + (i // 4) * 110
        d.text(((x0 + 10) * S, (y0 + 70) * S), st, font=fnt(), fill=INK)
    d.text((40 * S, 280 * S), "Предел роя: 53 / 45", font=fnt(), fill=RED)
    img.save(out("swarm_ui_kit.png"))
    print("swarm_ui_kit.png", img.size)


if __name__ == "__main__":
    kit_sheet()
