"""The swarm's interface kit, in the insects' own materials: a nest of wax cells behind everything, chitin plates for
panels, chamfered comb cells for cards, resin drops for buttons, a wing membrane for the title bar, an abdomen of
segments for the limit bar, antennae on the big panels. Pixel fonts: Press Start 2P for headings (OFL, in fonts/),
GNU Unifont for text (taken from the system package fonts-unifont; PT Serif if it is missing).

    python3 tools/sprites/swarm_ui.py      -> out/swarm_ui_kit.png (every piece, in every state)
"""
import os
import numpy as np
from PIL import ImageFont
from kit import *
from noise import value_noise
from paths import font

OUTL = hexc("#08060c")
INK, MUTED, GOLD, BIO, RED, GREEN, DARK = (236, 224, 196), (170, 156, 180), (240, 190, 90), (160, 230, 110), (240, 122, 96), (150, 220, 120), (40, 22, 8)
VIOLET = (196, 150, 255)
UNIFONT = "/usr/share/fonts/opentype/unifont/unifont.otf"

# rims of the comb cells: (rim, rim highlight, fill)
CELL = {
    "normal": ("#4a3e5c", "#7a6c90", "#1a1322"),
    "hi": ("#c88a2a", "#ffd070", "#241a16"),
    "new": ("#4a8a2a", "#9ae060", "#16201a"),
    "eat": ("#a83a2e", "#f07a5a", "#2a1218"),
    "locked": ("#2a2432", "#3a3446", "#100c14"),
    "mut": ("#a8822a", "#e8c050", "#1e1a16"),
    "find": ("#6a4a9a", "#b090e0", "#1a1426"),
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
    if state in ("hi", "mut", "find") or col is not None and state == "hi":
        halo = chamfer_mask(sc, x0 - 2, y0 - 2, x1 + 2, y1 + 2, c + 1) & ~m
        th = BAYER[sc.yy % 4, sc.xx % 4]
        sc.rgb[halo & (th < 0.6)] = sc.rgb[halo & (th < 0.6)] * 0.4 + hexc(hi) * 0.6


def button(sc, x0, y0, x1, y1, kind="amber"):
    """A resin drop pressed into a long hexagon: pointed ends, lit from the top, bubbles caught inside, a shine streak."""
    ramp_, shine, _ = BUTTON[kind]
    h = y1 - y0
    cy = (y0 + y1) / 2
    X, Y = sc.xx, sc.yy
    pt = h * 0.5
    m = (Y >= y0) & (Y < y1) & (X >= x0) & (X < x1)
    m &= (X - x0) >= np.abs(Y - cy + 0.5) * (pt / (h / 2)) * 0.9
    m &= (x1 - 1 - X) >= np.abs(Y - cy + 0.5) * (pt / (h / 2)) * 0.9
    t = np.clip((Y - y0) / max(1, h), 0, 1)
    pal = np.array([hexc(c) for c in ramp_])
    idx = np.clip(np.floor(t * 3.6 + BAYER[Y % 4, X % 4] * 0.6), 0, 3).astype(int)
    sc.rgb[m] = pal[idx][m]
    o, top, left = edges(m)
    sc.rgb[o] = OUTL
    inner = shrink(m)
    o1, top1, _ = edges(inner)
    sc.rgb[top1] = sc.rgb[top1] * 0.4 + hexc(shine) * 0.6
    streak = m & (Y >= y0 + 3) & (Y < y0 + 5) & (X > x0 + pt + 4) & (X < x0 + pt + (x1 - x0) * 0.35)
    sc.rgb[streak] = sc.rgb[streak] * 0.3 + hexc(shine) * 0.7
    if kind == "amber":
        rnd = np.random.RandomState(int(x0 + y0))
        for _ in range(int((x1 - x0) / 14)):
            bx, by = rnd.uniform(x0 + pt + 4, x1 - pt - 4), rnd.uniform(y0 + h * 0.45, y1 - 4)
            r_ = rnd.choice((1, 1, 2))
            bub = ((X - bx) ** 2 + (Y - by) ** 2 <= r_ * r_) & m
            sc.rgb[bub] = sc.rgb[bub] * 0.5 + hexc(shine) * 0.5
    sc.occ[m] = True
    sc.light[m] = 0


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


def segbar(sc, x0, y0, x1, h, total, limit, marked):
    """The limit as an abdomen: one segment per point; within the limit acid-green, over it blood-red,
    the ones marked to be eaten hatched amber; a bone tick at the limit."""
    n = total
    w = (x1 - x0) / n
    for i in range(n):
        a, b = x0 + i * w + 1, x0 + (i + 1) * w - 1
        col = hexc("#6ab030") if i < limit else hexc("#b0382a")
        hl = hexc("#b0f070") if i < limit else hexc("#ff7a5a")
        mm = (sc.xx >= a) & (sc.xx < b) & (sc.yy >= y0) & (sc.yy < y0 + h)
        mm &= ((sc.xx - (a + b) / 2) / ((b - a) / 2 + 0.5)) ** 2 + ((sc.yy - y0 - h / 2) / (h / 2 + 0.6)) ** 2 <= 1.15
        sc.rgb[mm] = col
        sc.rgb[mm & (sc.yy < y0 + 3)] = hl
        if i >= n - marked:
            hat = mm & ((sc.xx + sc.yy) % 4 < 2)
            sc.rgb[hat] = hexc("#e8b84a")
        o, _, _ = edges(mm)
        sc.rgb[o] = OUTL
    lx = int(x0 + limit * w)
    sc.rgb[y0 - 5:y0 + h + 5, lx - 1:lx + 1] = hexc("#f0e6c8")
    sc.rgb[y0 - 7:y0 - 5, lx - 3:lx + 3] = hexc("#f0e6c8")


def meter(sc, x0, y0, x1, h, n, filled, col="#b04a3a"):
    """A short row of segments: how many of n are filled (kills by trait and the like)."""
    w = (x1 - x0) / n
    for i in range(n):
        a, b = x0 + i * w + 1, x0 + (i + 1) * w - 1
        mm = (sc.xx >= a) & (sc.xx < b) & (sc.yy >= y0) & (sc.yy < y0 + h)
        sc.rgb[mm] = hexc(col) if i < filled else hexc("#2a2232")
        if i < filled:
            sc.rgb[mm & (sc.yy < y0 + 2)] = hexc(col) * 1.4
        o, _, _ = edges(mm)
        sc.rgb[o] = OUTL


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


def letters(sc, text, x, y, kind="text", px=16, col=INK, col2=None, outline=True, shadow=True, jitter=0, drips=0,
            hairs=0, align="left", seed=0):
    """Text drawn into the scene itself, on its pixel grid: dark outline, a shadow, a light top on each stroke,
    the letters dancing off the baseline (jitter), ichor running down (drips), bristles on top (hairs)."""
    from PIL import Image, ImageDraw
    f_ = _font(kind, px)
    rnd = np.random.RandomState((abs(hash(text)) + seed) % 2 ** 31)
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
