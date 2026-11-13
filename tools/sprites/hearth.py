"""The smelting hearth, drawn by hand rather than by noise: a firebrick forge of uneven bricks with the fire's light
on its upper courses and an ash door glowing low; an iron plate on top; a heap of coal, every lump its own shape —
white-hot by the crucible, cooling to black with a red edge towards the rim, the hot ones cracked with light;
tongues of flame of different heights and leans in clean bands; a tulip crucible of fired clay sunk in the coals,
red-hot below, its melt crusted with dross, a spout; the pour into a sand mould in a nailed wooden flask.

    python3 tools/sprites/hearth.py      -> out/hearth_check.png (the scene alone, large)
"""
import numpy as np
from kit import *
from swarm_ui import edges, OUTL

HEAT = ["#0c0705", "#24130e", "#4a1a0e", "#8a2a10", "#cc4a14", "#f08a24", "#ffc44a", "#fff2b8"]
FLAME = ("#b8320f", "#ec6c1a", "#ffb22e", "#fff0a8")
BRICK = [("#3a1c14", "#5a2c1e", "#7a3e28", "#9a5434"), ("#34181a", "#522820", "#70382a", "#8e4c36"),
         ("#40221a", "#603426", "#80482e", "#a05e3a")]
CLAY = ("#1c1a1e", "#2c2a30", "#3e3a40", "#56525a", "#76707a")
WOODP = ("#1e1208", "#3e2812", "#62401e", "#8a5e2e", "#b4844a")


def _h(c):
    return hexc(c)


def bricks(sc, x0, x1, y0, y1, seed=3):
    """The forge's front: courses of firebricks of uneven length, mortar between, a chipped corner here and there,
    each brick a little different; the upper courses warmed by the fire, the lower ones in shade."""
    rnd = np.random.RandomState(seed)
    sc.rgb[y0:y1, x0:x1] = _h("#140a08")                                    # mortar
    H_ = 9
    for ci, yy in enumerate(range(y0, y1, H_)):
        xx = x0 - rnd.randint(0, 14)
        warm = 1.0 - (yy - y0) / max(1, (y1 - y0))                          # firelight from above
        while xx < x1:
            L = rnd.randint(16, 27)
            bx0, bx1 = max(x0, xx + 1), min(x1, xx + L)
            by0, by1 = yy + 1, min(y1, yy + H_)
            if bx1 - bx0 >= 3:
                pal = [_h(c) for c in BRICK[rnd.randint(0, 3)]]
                sc.rgb[by0:by1, bx0:bx1] = pal[1]
                sc.rgb[by0, bx0:bx1] = pal[3] if warm > 0.55 else pal[2]    # its lit top edge
                sc.rgb[by1 - 1, bx0:bx1] = pal[0]                           # its shaded bottom
                sc.rgb[by0:by1, bx0] = pal[2]
                for _ in range(rnd.randint(0, 3)):                          # specks of grog
                    sx, sy = rnd.randint(bx0 + 1, max(bx0 + 2, bx1 - 1)), rnd.randint(by0 + 1, max(by0 + 2, by1 - 1))
                    sc.rgb[sy, sx] = pal[0] if rnd.rand() < 0.5 else pal[2]
                if rnd.rand() < 0.25:                                       # a chipped corner
                    sc.rgb[by0, bx1 - 1] = _h("#140a08")
                    sc.rgb[by0 + 1, bx1 - 1] = pal[0]
                if warm > 0.4:                                              # the fire's glow on it
                    k = (warm - 0.4) * 0.5
                    sc.rgb[by0:by1, bx0:bx1] = sc.rgb[by0:by1, bx0:bx1] * (1 - k) + _h("#ff7a2a") * k
            xx += L


def lump(sc, x, y, r, heat, seed, fire):
    """One lump of coal: an irregular rounded shape; hot ones glow from inside with bright cracks, cool ones are
    black with a red rim on the side that faces the fire."""
    rnd = np.random.RandomState(seed)
    R = int(r + 3)
    y0, y1, x0, x1 = int(y - R), int(y + R + 1), int(x - R), int(x + R + 1)
    if y0 < 0 or x0 < 0 or y1 > sc.h or x1 > sc.w:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    lx, ly = xx - x, yy - y
    a = np.arctan2(ly, lx)
    p1, p2 = rnd.uniform(0, 6.3, 2)
    rr = r * (1 + 0.2 * np.sin(3 * a + p1) + 0.12 * np.sin(5 * a + p2)) * np.where(ly > 0, 0.85, 1.0)
    d = np.hypot(lx, ly)
    m = d <= rr
    if not m.any():
        return
    pal = [_h(c) for c in HEAT]
    inner = np.clip(1 - d / np.maximum(rr, 0.5), 0, 1)
    if heat > 0.35:
        lvl = 2 + heat * 4.2 * (0.55 + 0.45 * inner) - (ly / max(r, 1)) * 0.6
    else:
        lvl = 1 + inner * 0.6 - (lx * 0.3 + ly * 0.7) / max(r, 1) * 0.6
    idx = np.clip(np.round(lvl), 0, 7).astype(int)
    col = np.array(pal)[idx]
    win = sc.rgb[y0:y1, x0:x1]
    win[m] = col[m]
    # the rim towards the fire glows on cool lumps
    fx, fy = fire
    dx, dy = fx - x, fy - y
    dn = np.hypot(dx, dy) + 1e-6
    face = (lx * dx + ly * dy) / (np.maximum(d, 0.5) * dn)
    edge = m & (d > rr - 1.6)
    if heat <= 0.35:
        win[edge & (face > 0.35)] = pal[3] if heat > 0.15 else pal[2]
    # bright cracks across hot lumps
    if heat > 0.5:
        ang = rnd.uniform(0, 3.1)
        c_ = np.abs(lx * np.sin(ang) - ly * np.cos(ang) + rnd.uniform(-1, 1)) < 0.6
        win[m & c_ & (inner > 0.25)] = pal[7] if heat > 0.75 else pal[6]
    # outline: dark below and on the shaded side, none on top of hot ones
    up = np.zeros_like(m); up[1:] = m[:-1]
    dn_ = np.zeros_like(m); dn_[:-1] = m[1:]
    lf = np.zeros_like(m); lf[:, 1:] = m[:, :-1]
    rt = np.zeros_like(m); rt[:, :-1] = m[:, 1:]
    out_ = m & ~(up & dn_ & lf & rt)
    win[out_ & (~dn_ | ~rt)] = pal[0]
    sc.rgb[y0:y1, x0:x1] = win


def flame(sc, bx, by, h, w, lean, seed):
    """A tongue of flame from (bx, by) up: a teardrop bent by its lean, in four clean bands from a pale core to a red
    edge, its tip broken into two or three licks."""
    rnd = np.random.RandomState(seed)
    y0, y1 = int(by - h - 2), int(by + 1)
    x0, x1 = int(bx - w - abs(lean) * h - 4), int(bx + w + abs(lean) * h + 4)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    s = np.clip((by - yy) / h, 0, 1.2)
    xc = bx + lean * h * s ** 2 + np.sin(s * 5.0 + rnd.uniform(0, 6)) * w * 0.18 * s
    hw = np.where(s < 0.18, w * np.sqrt(np.clip(s / 0.18, 0, 1)), w * np.clip((1 - s) / 0.82, 0, 1) ** 0.9)
    q = np.abs(xx - xc) / np.maximum(hw, 0.3)
    m = (q <= 1) & (s <= 1) & (yy <= by)
    lick = (s > 0.7) & (np.sin((xx - xc) * 1.4 + rnd.uniform(0, 6)) > 0.55)       # a broken tip
    m &= ~lick
    band = np.where((q < 0.32) & (s < 0.55), 3, np.where((q < 0.6) & (s < 0.78), 2, np.where(q < 0.86, 1, 0)))
    pal = np.array([_h(c) for c in FLAME])
    win = sc.rgb[y0:y1, x0:x1]
    win[m] = pal[band][m]
    sc.rgb[y0:y1, x0:x1] = win


def fire(sc, cx, base_y, tongues, seed=0):
    """A fire, not a row of candles: tongues (x offset, height, width, lean) grown together from one base into one
    shape, coloured by how deep inside it a pixel is — a red edge, orange, yellow, a pale heart low down."""
    from swarm_ui import shrink
    rnd = np.random.RandomState(seed)
    X, Y = sc.xx.astype(float), sc.yy.astype(float)
    m = np.zeros((sc.h, sc.w), bool)
    for dx, h, w, lean in tongues:
        bx = cx + dx
        s = np.clip((base_y - Y) / h, -0.3, 1.2)
        xc = bx + lean * h * np.clip(s, 0, 1) ** 2 + np.sin(np.clip(s, 0, 1) * 4.0 + rnd.uniform(0, 6)) * w * 0.2
        hw = np.where(s < 0.0, w * np.sqrt(np.clip(1 + s / 0.3, 0, 1)), w * np.clip(1 - s, 0, 1) ** 0.85)
        m |= (np.abs(X - xc) <= hw) & (s <= 1) & (Y <= base_y + 6)
    d1 = shrink(m)
    d2 = shrink(shrink(d1))
    d3 = shrink(shrink(d2))
    pal = [_h(c) for c in FLAME]
    sc.rgb[m] = pal[0]
    sc.rgb[d1] = pal[1]
    sc.rgb[d2] = pal[2]
    low = Y > base_y - 14
    sc.rgb[d3 & low] = pal[3]
    th = BAYER[sc.yy % 4, sc.xx % 4]
    tips = m & ~d1 & (th < 0.5) & (Y < base_y - 20)                       # the edge breaking up near the tips
    sc.rgb[tips] = sc.rgb[tips] * 0.6 + _h("#5a1408") * 0.4
    return m


def heap(sc, cx, base_y, half, height):
    """The coal's mass under the lumps: a low mound, black at its foot, smouldering red towards the middle."""
    X, Y = sc.xx.astype(float), sc.yy.astype(float)
    u = (X - cx) / half
    crest = base_y - height * np.clip(1 - u * u, 0, 1) ** 1.1
    m = (np.abs(u) <= 1) & (Y >= crest) & (Y < base_y)
    heat = np.clip(1 - np.abs(u) * 1.3, 0, 1) * np.clip((Y - crest) / 10.0, 0, 1)
    pal = np.array([_h(c) for c in ("#0c0705", "#1c0e0a", "#3a1208", "#6a1e0c")])
    th = BAYER[sc.yy % 4, sc.xx % 4]
    sc.rgb[m] = pal[np.clip(np.floor(heat * 3.4 + (th - 0.5) * 0.7), 0, 3).astype(int)][m]
    o, _, _ = edges(m)
    sc.rgb[o & (Y < base_y - 1)] = OUTL
    return crest


def crucible(sc, cx, top, bot):
    """A tulip crucible of fired clay: a thick lip, the belly swelling a little below it, a rounded foot; grey above,
    red-hot where it sits in the coals; a beak of a spout on the right. Returns the spout's tip."""
    X, Y = sc.xx.astype(float), sc.yy.astype(float)
    hgt = bot - top
    s = (Y - top) / hgt
    sc_ = np.clip(s, 0, 1)
    hw = 30 + 6 * np.sin(np.pi * np.clip(sc_ / 0.7, 0, 1) * 0.9) - 14 * np.clip((sc_ - 0.45) / 0.55, 0, 1) ** 1.6
    foot = np.where(s > 0.86, np.sqrt(np.clip(1 - ((s - 0.86) / 0.14) ** 2, 0, 1)), 1.0)
    body = (s >= 0) & (s <= 1) & (np.abs(X - cx) <= hw * foot)
    clay = [_h(c) for c in CLAY]
    heatp = [_h(c) for c in HEAT]
    u = (X - cx) / np.maximum(hw, 1)                                             # across the body, −1..1
    lit = np.clip(0.55 + 0.45 * np.cos((u + 0.38) * 1.7) - 0.25 * (u > 0.55), 0, 1)   # a cylinder lit from the left
    th = BAYER[sc.yy % 4, sc.xx % 4]
    base = np.clip(np.floor(lit * 4.0 + (th - 0.5) * 0.5 + 0.5), 0, 4).astype(int)
    col = np.array(clay)[base]
    hot = np.clip((s - 0.45) / 0.55, 0, 1)                                       # red-hot towards the foot
    hidx = np.clip(np.round(2 + hot * 3.4 + lit * 0.8), 0, 7).astype(int)
    hcol = np.array(heatp)[hidx]
    mix = (hot > 0.05)[..., None]
    k = np.clip(hot * 1.4, 0, 1)[..., None]
    out = np.where(mix, col * (1 - k) + hcol * k, col)
    sc.rgb[body] = out[body]
    # banded marks of the fire's soot and the glaze running
    for yb in (top + hgt * 0.32, top + hgt * 0.36):
        row = body & (np.abs(Y - yb) < 0.5)
        sc.rgb[row] = sc.rgb[row] * 0.75
    lip = (Y >= top - 5) & (Y < top + 3) & (np.abs(X - cx) <= 35) & (((X - cx) / 35.0) ** 2 + ((Y - (top - 1)) / 5.0) ** 2 <= 1)
    ul = (X - cx) / 35.0
    lt2 = np.clip(np.round(1.2 + np.clip(0.6 + 0.4 * np.cos((ul + 0.4) * 1.7), 0, 1) * 3.0), 0, 4).astype(int)
    sc.rgb[lip] = np.array(clay)[lt2][lip]
    sp = (Y >= top - 6) & (Y < top + 2) & (X >= cx + 30) & (X <= cx + 44) & ((Y - (top - 6)) >= (X - (cx + 30)) * 0.35)
    sc.rgb[sp] = clay[3]
    m = body | lip | sp
    o, _, _ = edges(m)
    sc.rgb[o] = OUTL
    # the melt: a bright ellipse under the lip, dross floating on it
    melt = ((X - cx) / 29.5) ** 2 + ((Y - (top - 1)) / 3.0) ** 2 <= 1
    t = np.clip(1 - np.hypot((X - cx) / 32, (Y - top) / 4), 0, 1)
    midx = np.clip(np.round(5 + t * 2.4), 0, 7).astype(int)
    sc.rgb[melt] = np.array(heatp)[midx][melt]
    rnd = np.random.RandomState(4)
    for _ in range(5):
        dx_, dl = rnd.randint(-24, 24), rnd.randint(2, 5)
        sc.rgb[int(top - 1), int(cx + dx_):int(cx + dx_ + dl)] = heatp[3]
    return (cx + 44, top - 3), m


def flask(sc, x0, x1, y0, y1):
    """A moulding flask: a box of planks with nails at the corners, packed dark sand on top."""
    X, Y = sc.xx, sc.yy
    box = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    wp = [_h(c) for c in WOODP]
    sc.rgb[box] = wp[2]
    for yy in range(y0 + 7, y1, 7):                                              # the planks
        sc.rgb[yy, x0:x1] = wp[0]
        sc.rgb[yy + 1, x0:x1] = wp[3]
    sc.rgb[y0:y1, x0:x0 + 3] = wp[1]
    sc.rgb[y0:y1, x1 - 3:x1] = wp[1]
    for nx in (x0 + 1, x1 - 2):
        for ny in range(y0 + 3, y1, 7):
            sc.rgb[ny, nx] = _h("#8a8890")
    sand = (X >= x0 + 3) & (X < x1 - 3) & (Y >= y0 - 3) & (Y < y0 + 2)
    th = BAYER[sc.yy % 4, sc.xx % 4]
    sc.rgb[sand] = np.where((th < 0.5)[..., None], _h("#3a342e"), _h("#2a2622"))[sand]
    o, _, _ = edges(box | sand)
    sc.rgb[o] = OUTL


IRONP = ("#121116", "#2c2a32", "#4a4852", "#74727e", "#acaab6")


def _seg(X, Y, p0, p1, r):
    (ax, ay), (bx, by) = p0, p1
    dx, dy = bx - ax, by - ay
    L2 = max(1e-6, dx * dx + dy * dy)
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy)) <= r


def _ironpaint(sc, m, pal=IRONP, glow=None):
    """Paint a forged shape: a mid tone, its top and left edges caught by the light, its bottom and right in shade,
    an outline; glow — a mask of where it is still hot."""
    from swarm_ui import shrink
    p = [_h(c) for c in pal]
    sc.rgb[m] = p[2]
    up = np.zeros_like(m); up[1:] = m[:-1]
    dn = np.zeros_like(m); dn[:-1] = m[1:]
    lf = np.zeros_like(m); lf[:, 1:] = m[:, :-1]
    rt = np.zeros_like(m); rt[:, :-1] = m[:, 1:]
    inner = shrink(m)
    sc.rgb[m & ~inner & (~up | ~lf)] = p[4]
    sc.rgb[m & ~inner & ~dn & up & lf] = p[1]
    sc.rgb[m & ~inner & ~rt & up & lf & dn] = p[1]
    warm = m & ~inner & ~dn                                                   # the fire's light from below
    sc.rgb[warm] = sc.rgb[warm] * 0.45 + _h("#d8803a") * 0.55
    if glow is not None:
        g = m & glow
        sc.rgb[g] = sc.rgb[g] * 0.3 + _h("#e05a1a") * 0.7
    o, _, _ = edges(m)
    sc.rgb[o] = OUTL


def s_hook(X, Y, x, y):
    """An S-hook hanging from the rail at (x, y): two small open loops."""
    a = (np.abs(np.hypot(X - x, Y - (y + 3)) - 2.6) <= 0.8) & ~((X > x) & (Y > y + 3))
    b = (np.abs(np.hypot(X - x, Y - (y + 8)) - 2.6) <= 0.8) & ~((X < x) & (Y < y + 8))
    return a | b


def tool_rack(sc, x0, x1, y_rail, seed=0):
    """The forge's back wall: an iron rail on two brackets, and hanging from it on S-hooks the smith's own tools,
    each its own length — long tongs, a ladle with a crust of metal set in it, a skimmer, a poker still warm at
    its end, a hand hammer."""
    X, Y = sc.xx.astype(float), sc.yy.astype(float)
    rail = (X >= x0) & (X < x1) & (Y >= y_rail) & (Y < y_rail + 4)
    br = np.zeros_like(rail)
    for bx in (x0 + 10, x1 - 12):                                             # the brackets into the wall
        br |= (X >= bx - 2) & (X <= bx + 2) & (Y >= y_rail + 3) & (Y < y_rail + 16) & ((Y - y_rail - 3) <= (X - bx + 2) * 6)
        br |= _seg(X, Y, (bx, y_rail + 2), (bx - 8, y_rail + 14), 1.4)
    _ironpaint(sc, rail | br)
    for bx in (x0 + 4, x0 + 18, x1 - 6, x1 - 20):
        sc.rgb[int(y_rail + 1), int(bx)] = _h("#a8a6b0")
    # the tools, by hand: where each hangs, how long it is
    W = x1 - x0
    hx = [x0 + W * f for f in (0.13, 0.3, 0.62, 0.78, 0.92)]
    hooks = np.zeros_like(rail)
    for x in hx:
        hooks |= s_hook(X, Y, x, y_rail + 3)
    _ironpaint(sc, hooks)
    yh = y_rail + 14                                                          # where the tools hang from
    # 1. long tongs: two reins from a ring, a rivet, two short jaws
    x = hx[0]
    ring = np.abs(np.hypot(X - x, Y - (yh + 2)) - 2.5) <= 1.0
    reins = _seg(X, Y, (x - 1, yh + 4), (x - 4, yh + 70), 1.7) | _seg(X, Y, (x + 1, yh + 4), (x + 4, yh + 70), 1.7)
    piv = np.hypot(X - x, Y - (yh + 72)) <= 3.2
    jaws = _seg(X, Y, (x - 2, yh + 72), (x - 6, yh + 84), 1.8) | _seg(X, Y, (x + 2, yh + 72), (x + 5, yh + 85), 1.8)
    jaws |= _seg(X, Y, (x - 6, yh + 84), (x - 3, yh + 89), 1.6) | _seg(X, Y, (x + 5, yh + 85), (x + 2, yh + 89), 1.6)
    _ironpaint(sc, ring | reins | piv | jaws)
    # 2. a ladle: a long handle, a round bowl with a crust of set metal inside
    x = hx[1]
    handle = _seg(X, Y, (x, yh), (x + 2, yh + 58), 1.8) | (np.abs(np.hypot(X - x, Y - (yh + 1)) - 2.6) <= 1.0)
    bowl = ((((X - (x + 2)) / 9.0) ** 2 + ((Y - (yh + 62)) / 7.5) ** 2) <= 1) & (Y >= yh + 58)
    rim = _seg(X, Y, (x - 8, yh + 58), (x + 12, yh + 58), 1.5)
    _ironpaint(sc, handle | bowl | rim)
    crust = ((((X - (x + 2)) / 6.5) ** 2 + ((Y - (yh + 60)) / 2.2) ** 2) <= 1)
    sc.rgb[crust & bowl] = _h("#7a4a2a")
    sc.rgb[crust & bowl & (Y < yh + 60)] = _h("#a8683a")
    # 3. a skimmer: a flat perforated disc on a thin handle
    x = hx[2]
    handle = _seg(X, Y, (x, yh), (x - 1, yh + 52), 1.6) | (np.abs(np.hypot(X - x, Y - (yh + 1)) - 2.4) <= 1.0)
    disc = (((X - (x - 1)) / 8.0) ** 2 + ((Y - (yh + 60)) / 8.5) ** 2) <= 1
    _ironpaint(sc, handle | disc)
    for hx_, hy_ in ((-4, -4), (0, -5), (3, -2), (-3, 1), (1, 2), (-1, 5), (4, 3)):
        sc.rgb[int(yh + 60 + hy_), int(x - 1 + hx_)] = _h("#0a090c")
    # 4. a poker: a rod with a bent hook, its end still dull red
    x = hx[3]
    rod = _seg(X, Y, (x, yh), (x + 1, yh + 80), 1.8) | _seg(X, Y, (x + 1, yh + 80), (x - 6, yh + 87), 1.8)
    rod |= np.abs(np.hypot(X - x, Y - (yh + 1)) - 2.6) <= 1.0
    _ironpaint(sc, rod, glow=(Y > yh + 72))
    # 5. a hand hammer, head down
    x = hx[4]
    wood = _seg(X, Y, (x, yh + 2), (x, yh + 40), 2.2)
    loop = np.abs(np.hypot(X - x, Y - (yh + 1)) - 2.6) <= 1.0
    head = (np.abs(X - (x + 1)) <= 9) & (Y >= yh + 40) & (Y < yh + 49)
    head &= ~((X > x + 6) & (Y < yh + 42))                                  # the peen's slope
    _ironpaint(sc, loop | head)
    wp = [_h(c) for c in WOODP]
    sc.rgb[wood] = wp[2]
    sc.rgb[wood & (X < x)] = wp[3]
    o, _, _ = edges(wood)
    sc.rgb[o] = OUTL


def smoke(sc, x, y_bot, y_top, seed=0):
    """Smoke going up from the fire: separate puffs, small and dense low down, larger and fainter as they rise,
    leaning a little; each with its own light top and shaded underside."""
    X, Y = sc.xx.astype(float), sc.yy.astype(float)
    rnd = np.random.RandomState(seed)
    th = BAYER[sc.yy % 4, sc.xx % 4]
    n = 6
    for i in range(n):
        t = i / (n - 1)
        cy = y_bot - (y_bot - y_top) * t
        cx = x + 14 * np.sin(t * 2.2 + 0.4) + rnd.uniform(-2, 2)
        r = 9 + 14 * t
        k = 0.42 - 0.3 * t                                                   # fainter as it rises
        m = np.zeros((sc.h, sc.w), bool)
        for j in range(4):
            ox, oy = rnd.uniform(-r * 0.7, r * 0.7), rnd.uniform(-r * 0.35, r * 0.35)
            m |= np.hypot(X - (cx + ox), Y - (cy + oy)) <= r * rnd.uniform(0.45, 0.7)
        edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        body = m & ~edge
        sc.rgb[body] = sc.rgb[body] * (1 - k) + _h("#5a5662") * k
        lit = m & ~np.roll(m, 2, 0)                                          # the tops of the billows catch light
        sc.rgb[lit] = sc.rgb[lit] * (1 - k) + _h("#8a8692") * k
        thin = edge & (th < 0.5)                                             # a ragged, thinning edge
        sc.rgb[thin] = sc.rgb[thin] * (1 - k * 0.6) + _h("#5a5662") * (k * 0.6)


def scene(sc, x0, y0, x1, y1, melt_icon, cast_icon, glow=True):
    """The whole hearth in the box x0..x1, y0..y1 (the forge on the floor at y1)."""
    cx = (x0 + x1) // 2 - 34
    fy = y1 - 18                                                                 # the floor
    e = ((sc.xx - cx) / 120.0) ** 2 + ((sc.yy - fy) / 6.0) ** 2 <= 1            # the shadow on the floor
    sc.rgb[e] *= 0.55
    # the forge
    fx0, fx1, ftop = cx - 100, cx + 100, fy - 74
    bricks(sc, fx0, fx1, ftop, fy)
    X, Y = sc.xx.astype(float), sc.yy.astype(float)
    arch = (np.abs(X - cx) <= 22) & (Y < fy) & ((Y >= fy - 12) | (((X - cx) / 22.0) ** 2 + ((Y - (fy - 12)) / 14.0) ** 2 <= 1))
    door = (np.abs(X - cx) <= 17) & (Y < fy) & ((Y >= fy - 12) | (((X - cx) / 17.0) ** 2 + ((Y - (fy - 12)) / 10.0) ** 2 <= 1))
    ring = arch & ~door                                                          # the arch's bricks
    ang = np.arctan2(Y - (fy - 12), X - cx)
    vous = ring & (np.mod(ang * 7 / np.pi, 1) < 0.12)
    sc.rgb[ring] = _h("#7a3e28")
    sc.rgb[ring & (Y < fy - 12)] = _h("#9a5434")
    sc.rgb[vous] = _h("#140a08")
    tt = np.clip((Y - (fy - 22)) / 22.0, 0, 1)                                   # ash glowing low behind the door
    pal = np.array([_h(c) for c in ("#0c0605", "#2a0e08", "#5a1a0c", "#8a2a10")])
    th = BAYER[sc.yy % 4, sc.xx % 4]
    sc.rgb[door] = pal[np.clip(np.floor(tt * 3.2 + (th - 0.5) * 0.6), 0, 3).astype(int)][door]
    rnd = np.random.RandomState(7)
    for _ in range(10):
        ax, ay = int(cx + rnd.randint(-14, 15)), int(fy - rnd.randint(1, 5))
        sc.rgb[ay, ax] = _h(HEAT[rnd.randint(4, 7)])
    for m_ in (arch, door):
        o, _, _ = edges(m_)
        sc.rgb[o] = OUTL
    fo, _, _ = edges((sc.xx >= fx0) & (sc.xx < fx1) & (sc.yy >= ftop) & (sc.yy < fy))
    sc.rgb[fo] = OUTL
    # the iron plate on top
    plate = (sc.xx >= fx0 - 4) & (sc.xx < fx1 + 4) & (sc.yy >= ftop - 6) & (sc.yy < ftop + 1)
    sc.rgb[plate] = _h("#2a282e")
    sc.rgb[ftop - 6, fx0 - 4:fx1 + 4] = _h("#c87a3a")                             # its edge, lit by the fire
    sc.rgb[ftop - 5, fx0 - 4:fx1 + 4] = _h("#6a4a3a")
    for rx in range(fx0 + 2, fx1, 16):
        sc.rgb[ftop - 3, rx] = _h("#8a8890")
    po, _, _ = edges(plate)
    sc.rgb[po] = OUTL
    # the hood over it all
    top, bot = ftop - 96, ftop - 4
    smoke(sc, cx - 14, top - 58, y0 + 34, seed=2)
    tool_rack(sc, x0 + 14, x1 - 14, y0 + 22, seed=1)
    # the heap of coal, the crucible sunk in it, the fire round it
    firept = (cx, ftop - 22)
    fire(sc, cx, ftop - 26, ((-46, 46, 13, -0.35), (-24, 30, 11, -0.2), (24, 34, 11, 0.25), (48, 50, 13, 0.4),
                             (-70, 24, 9, -0.25), (70, 22, 9, 0.3), (0, 20, 14, 0.0)), seed=3)
    heap(sc, cx, ftop - 4, 98, 40)
    rnd = np.random.RandomState(11)
    lumps = []
    for i in range(70):
        u = rnd.uniform(-1, 1) * (0.5 + 0.5 * rnd.rand())
        hx = cx + u * 92
        crest = ftop - 4 - 40 * np.clip(1 - u * u, 0, 1) ** 1.1
        ly_ = rnd.uniform(crest + 2, ftop - 6)
        r = rnd.uniform(4.5, 8.0) * (1.0 - 0.3 * abs(u))
        dist = np.hypot((hx - firept[0]) / 60.0, (ly_ - firept[1]) / 30.0)
        heat = np.clip(1.25 - dist * 1.15 + rnd.uniform(-0.2, 0.15), 0, 1)
        lumps.append((ly_, hx, r, heat, i))
    lumps.sort()
    for ly_, hx, r, heat, i in lumps:
        if ly_ < top + 40 and abs(hx - cx) < 40:
            lump(sc, hx, ly_, r, heat, i, firept)
    spout, cm = crucible(sc, cx, top, bot)
    heap(sc, cx, ftop - 4, 70, 30) if False else None
    for ly_, hx, r, heat, i in lumps:
        if not (ly_ < top + 40 and abs(hx - cx) < 40):
            lump(sc, hx, ly_, r, heat, i, firept)
    fire(sc, cx, ftop - 10, ((-30, 20, 8, -0.4), (6, 14, 7, 0.1), (34, 22, 8, 0.45)), seed=5)
    if glow:
        sc.glow(cx, ftop - 24, 120, _h("#ff7a2a"), 0.3)
    # the module going into the melt
    if melt_icon is not None:
        sc.blit(melt_icon, int(cx - melt_icon.w / 2 - 6), int(top - melt_icon.h + 10))
        sink = cm & (sc.yy >= top - 3) & (sc.yy < top + 1) & (np.abs(sc.xx - cx) < 28)
        sc.rgb[sink] = _h(HEAT[6])
    # the flask on the right and the pour into it, a solid thread thinning as it falls
    kx0, kx1 = x1 - 96, x1 - 14
    ky0 = fy - 30
    flask(sc, kx0, kx1, ky0, fy)
    if cast_icon is not None:
        sc.blit(cast_icon, int((kx0 + kx1) / 2 - cast_icon.w / 2), int(ky0 - cast_icon.h + 14))
    sx, sy = spout
    ex, ey = (kx0 + kx1) / 2 - 2, ky0 - 12
    heatp = [_h(c) for c in HEAT]
    prev = None
    for i in range(240):
        t = i / 239
        px_ = sx + (ex - sx) * t
        py_ = sy + (ey - sy) * t ** 1.9 - 10 * np.sin(np.pi * t) * (1 - t)
        w_ = 2 if t < 0.35 else 1
        sc.rgb[int(py_) - 1:int(py_) + w_, int(px_) - 1:int(px_) + w_] = heatp[4]
        sc.rgb[int(py_), int(px_)] = heatp[7] if t < 0.6 else heatp[6]
    for dx_, dy_ in ((-5, -3), (4, -5), (7, -2), (-2, -6), (-7, -1)):            # the splash
        sc.rgb[int(ey + dy_), int(ex + dx_)] = heatp[6]
    if glow:
        sc.glow(ex, ey + 8, 30, _h("#ff8a2a"), 0.3)


if __name__ == "__main__":
    import icons as IC
    from paths import out
    import foundry_hud as FH
    sc = Scene(340, 400)
    sc.rgb[:] = hexc("#16141a")
    scene(sc, 6, 6, 334, 394, FH.molten(IC.icon("canister", 3, "module")), FH.molten(IC.icon("long", 3, "module"), 1.2))
    sc.image(3).save(out("hearth_check.png"))
    print("hearth_check.png")
