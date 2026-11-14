"""Module icons drawn by hand in code, pixel by pixel — no source image under them. Each icon is 16×16: its parts
laid in as blocks and single pixels, every one with its tone picked from our ramps (icons.R), the light from the
top left; then our dark outline round the whole shape, outside it. The way to replace the icons made from the
Pixel Art Atlas dataset (its sprites are AI-generated, see docs/STEAM.md) — drawn from what each module is,
not traced from the old icon.

    python3 tools/sprites/icons_drawn.py atlas     -> assets/module_icons.png, .json (all 65, same cells and keys)
    python3 tools/sprites/icons_drawn.py contact   -> out/icons_modules.png (every icon, a row for each owner)
    python3 tools/sprites/icons_drawn.py guard     -> out/icons_guard.png (a batch: the icon large and in a cell)
"""
import numpy as np
from kit import hexc
import icons as IC

OUTLINE = hexc("#08060c")
_PAINTS = {}


def ramp_of(name):
    """A ramp by name: ours (icons.R), or a frame's own paint — "paint:Страж"."""
    if name.startswith("paint:"):
        if not _PAINTS:
            _PAINTS.update(IC.paints())
        return _PAINTS[name[6:]]
    return IC.R[name]


def grid(f):
    """A 16×16 mask from a test on (x, y)."""
    return np.array([[bool(f(x, y)) for x in range(16)] for y in range(16)])


class Pix:
    """A 16×16 icon being drawn: colours or nothing; the outline goes on last, round what is there."""

    def __init__(self):
        self.c = np.zeros((16, 16, 3))
        self.a = np.zeros((16, 16), bool)
        self.hole = np.zeros((16, 16), bool)          # drawn as outline colour inside the shape (a bore, a slot)

    def px(self, x, y, ramp, lv):
        if 0 <= x < 16 and 0 <= y < 16:
            self.c[y, x] = ramp_of(ramp)[int(max(0, min(4, lv)))]
            self.a[y, x] = True
            self.hole[y, x] = False

    def fill(self, mask, ramp, inner=(3, 2), rim=4, shade=1, split=0.0):
        """A flat shape, bevelled: the pixels on its top or left edge catch the light (rim), those on its bottom
        or right edge are in shadow (shade), the inside goes from inner[0] at the top left to inner[1] at the bottom
        right (split moves the line between them)."""
        m = np.asarray(mask, bool)
        ys, xs = np.nonzero(m)
        if not len(xs):
            return
        pr = (xs + ys).astype(float)
        lo, hi = pr.min(), pr.max()
        pm = np.pad(m, 1)
        for x, y, t in zip(xs, ys, (pr - lo) / max(1.0, hi - lo)):
            up, lf = pm[y, x + 1], pm[y + 1, x]
            dn, rt = pm[y + 2, x + 1], pm[y + 1, x + 2]
            if not up or not lf:
                lv = rim if (not up and not lf) or (not up and t < 0.75) or (not lf and t < 0.75) else inner[1]
            elif not dn or not rt:
                lv = shade
            else:
                lv = inner[0] if t < 0.5 + split else inner[1]
            self.px(x, y, ramp, lv)

    def disc(self, cx, cy, r, ramp, levels=(4, 3, 2, 1), hole=0.0):
        """A round thing lit from the top left: the tone by how far round it faces the light."""
        for y in range(16):
            for x in range(16):
                d = np.hypot(x - cx, y - cy)
                if d <= r:
                    if d <= hole:
                        self.dark(x, y)
                        continue
                    f = ((x - cx) + (y - cy)) / max(r, 0.5) / 1.414      # -1 facing the light .. 1 away
                    k = int(np.clip((f + 1) / 2 * len(levels), 0, len(levels) - 1))
                    self.px(x, y, ramp, levels[k])

    def tube(self, ax, ay, bx, by, r, ramp, levels=(4, 3, 2, 1), t0=0.0, t1=None):
        """A round bar from a to b: lit along the side that faces the top left."""
        L = np.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        sgn = 1 if (-uy * -1 + ux * -1) < 0 else -1          # which side of the bar faces the light
        t1 = L if t1 is None else t1
        for y in range(16):
            for x in range(16):
                dx, dy = x - ax, y - ay
                t, n = dx * ux + dy * uy, (-dx * uy + dy * ux) * sgn
                if t0 - 0.5 <= t <= t1 + 0.5 and abs(n) <= r:
                    k = int(np.clip((n / r + 1) / 2 * len(levels), 0, len(levels) - 1))
                    self.px(x, y, ramp, levels[k])

    def line(self, pts, ramp, lv):
        out = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for t in range(n + 1):
                out.append((round(x0 + (x1 - x0) * t / n), round(y0 + (y1 - y0) * t / n)))
        for x, y in out:
            self.px(x, y, ramp, lv)
        return out

    def rect(self, x0, y0, x1, y1, ramp, rows):
        """A block x0..x1, y0..y1 (inclusive); rows — the tone of each row top to bottom (the last repeats)."""
        for j, y in enumerate(range(y0, y1 + 1)):
            lv = rows[min(j, len(rows) - 1)]
            for x in range(x0, x1 + 1):
                self.px(x, y, ramp, lv)

    def col(self, x, y0, y1, ramp, rows):
        self.rect(x, y0, x, y1, ramp, rows)

    def dark(self, x, y):
        """A hole into the thing: the outline's colour, inside the shape."""
        self.a[y, x] = True
        self.hole[y, x] = True

    def done(self):
        a = self.a
        p = np.pad(a, 1)
        ring = ~a & (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:])
        out = np.zeros((16, 16, 4), np.uint8)
        out[..., :3] = np.clip(self.c, 0, 255)
        out[self.hole, :3] = OUTLINE
        out[ring, :3] = OUTLINE
        out[..., 3] = (a | ring) * 255
        return out


# ---------------------------------------------------------------- the icons
def long_barrel():
    """Длинный ствол: a long barrel lying level, pointing right — a brass breech collar with two bolts, the tube
    lit along its top, two brass bands, a sight on top, a slotted muzzle brake, the bore dark at its mouth."""
    p = Pix()
    p.rect(3, 6, 11, 8, "steel", [3, 2, 1])                # the tube
    p.rect(3, 6, 11, 6, "steel", [4])
    for x in (6, 9):                                      # brass bands, standing proud of the tube
        p.col(x, 5, 9, "brass", [4, 4, 3, 2, 1])
    p.col(10, 4, 5, "iron", [4, 3])                       # the sight
    p.rect(12, 4, 14, 10, "iron", [4, 3, 3, 3, 3, 2, 1])  # the muzzle brake
    p.col(14, 5, 9, "iron", [2])
    for y in (5, 9):
        p.dark(13, y)                                     # its slots
    p.dark(14, 7)                                         # the bore
    p.rect(1, 4, 2, 10, "brass", [4, 3, 3, 3, 3, 2, 1])   # the breech collar
    p.col(2, 5, 9, "brass", [2])
    for y in (5, 9):
        p.px(1, y, "brass", 4)                            # its bolts
    p.px(1, 6, "brass", 1)
    p.px(1, 10, "brass", 1)
    return p.done()


def mortar():
    """Мортира: a short fat barrel cocked up to the right at 45° on a low iron bed — its muzzle a round dark bore
    in a lit rim, facing us; a brass band round the barrel, a brass trunnion where it sits in the bed."""
    p = Pix()
    p.rect(1, 12, 11, 14, "iron", [4, 2, 1])              # the bed
    p.px(1, 12, "iron", 3)
    for x in (3, 9):
        p.px(x, 13, "brass", 4)
    ax, ay, bx, by = 4.0, 10.5, 10.0, 4.5                 # the barrel's axis, breech to muzzle
    ux, uy = (bx - ax) / np.hypot(bx - ax, by - ay), (by - ay) / np.hypot(bx - ax, by - ay)
    for y in range(16):
        for x in range(16):
            dx, dy = x - ax, y - ay
            t = dx * ux + dy * uy                         # along the axis
            n = -dx * uy + dy * ux                        # across it: < 0 the upper left side, lit
            if -1.0 <= t <= np.hypot(bx - ax, by - ay) and abs(n) <= 2.6:
                lv = 4 if n < -1.6 else 3 if n < -0.4 else 2 if n < 1.0 else 1
                band = 3.4 <= t <= 4.4                    # a brass band round it
                p.px(x, y, "brass" if band else "iron", lv)
    cx, cy = 10.6, 4.4                                    # the muzzle, round, facing up-right toward us
    for y in range(16):
        for x in range(16):
            d = np.hypot(x - cx, y - cy)
            if d <= 3.3:
                p.px(x, y, "iron", 4 if (x - cx) + (y - cy) < -1.5 else 3 if (x - cx) + (y - cy) < 1.5 else 2)
            if d <= 1.7:
                p.dark(x, y)                              # the bore
    p.rect(3, 10, 4, 11, "brass", [4, 2])                 # the trunnion
    return p.done()


def _line(p, pts, ramp, lv):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            out.append((round(x0 + (x1 - x0) * t / n), round(y0 + (y1 - y0) * t / n)))
    return out


def chain_lightning():
    """Цепная молния: a coil of copper turns with a brass ball on top throws an arc; it strikes, jumps on and
    strikes again — a white-hot jagged core, the cold blue glow along it, a star of sparks at each strike."""
    p = Pix()
    p.rect(1, 13, 5, 14, "iron", [3, 1])                  # the base plate
    for y in range(9, 13):                                # the coil: copper turns, lit and shadowed in turn
        p.rect(2, y, 4, y, "copper", [4 if y % 2 else 2])
        p.px(4, y, "copper", 1 if y % 2 == 0 else 3)
    for y, (x0, x1) in {4: (2, 4), 5: (1, 5), 6: (1, 5), 7: (2, 4)}.items():   # the ball on top, round
        for x in range(x0, x1 + 1):
            lv = 4 if (x - 2.5) + (y - 4.5) < -0.5 else 3 if (x - 3) + (y - 5.5) < 1 else 2
            p.px(x, y, "brass", lv)
    p.px(2, 5, "steel", 4)                                # its glint
    p.px(3, 8, "brass", 2)                                # the neck
    core = _line(p, [(6, 5), (8, 4), (7, 2), (10, 1)], "volt", 4)
    core += _line(p, [(10, 1), (12, 5), (11, 7), (13, 10)], "volt", 4)
    for x, y in core:                                     # the glow first, then the core over it
        for dx, dy in ((1, 0), (0, 1)):
            if 0 <= x + dx < 16 and 0 <= y + dy < 16:
                p.px(x + dx, y + dy, "volt", 2)
    for x, y in core:
        p.px(x, y, "volt", 4)
    for cx, cy in ((10, 1), (13, 11)):                    # sparks where it strikes
        p.px(cx, cy, "volt", 4)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if 0 <= cx + dx < 16 and 0 <= cy + dy < 16 and (cx + dx, cy + dy) not in core:
                p.px(cx + dx, cy + dy, "volt", 3)
    return p.done()


def armour_plates():
    """Броневые листы: the lames of a cuirass — three curved iron plates lapped like shingles, each narrower than
    the one above, their ends lifted; a ridge down the middle, a lit top edge, a shadow under the plate above,
    brass rivets at the ends."""
    p = Pix()
    lames = [(1, 14, 3), (2, 13, 7), (4, 11, 11)]         # (x from, x to, top row)
    for x0, x1, y0 in reversed(lames):                    # the lower ones first: each upper plate laps over
        for x in range(x0, x1 + 1):
            e = min(x - x0, x1 - x)
            lift = 2 if e == 0 else 1 if e < 3 else 0      # the ends curve up
            top = y0 - lift
            tones = [4, 3, 2, 1]
            for k, lv in enumerate(tones):
                p.px(x, top + k, "iron", lv)
            if x in (7, 8):                               # the ridge down the middle catches the light
                p.px(x, top + 1, "iron", 4)
                p.px(x, top + 2, "iron", 3 if x == 7 else 2)
        for x in (x0 + 1, x1 - 1):
            p.px(x, y0, "brass", 4)                       # rivets
            p.px(x, y0 + 1, "brass", 2)
    return p.done()


NEW = {"long": long_barrel, "mortar": mortar, "chain": chain_lightning, "plates": armour_plates}


def icon(key):
    def reg(f):
        NEW[key] = f
        return f
    return reg


# ---------------------------------------------------------------- the Guard
@icon("tower")
def tower_shield():
    """Ростовой щит: a tall shield, the Guard's blue-grey paint inside a steel rim, a viewing slit near the top,
    a brass boss in the middle, brass rivets at the rim's corners."""
    p = Pix()
    m = grid(lambda x, y: 4 <= x <= 11 and 1 <= y <= 14 and not ((x in (4, 11)) and y in (1, 14)))
    p.fill(m, "steel", inner=(3, 3), rim=4, shade=1)
    inner = grid(lambda x, y: 5 <= x <= 10 and 2 <= y <= 13)
    p.fill(inner, "paint:Страж", inner=(3, 2), rim=4, shade=1)
    for x in range(6, 10):
        p.dark(x, 3)                                      # the viewing slit
    p.disc(7.5, 8.0, 1.6, "brass")                        # the boss
    for x, y in ((4, 2), (11, 2), (4, 13), (11, 13)):
        p.px(x, y, "brass", 4)
    return p.done()


@icon("intercept")
def intercept():
    """Перехват: a pointed shield thrust out into the path of a bolt meant for someone else — the bolt, flying in
    from the right, strikes its face and sparks fly."""
    p = Pix()
    m = grid(lambda x, y: 1 <= x <= 9 and 2 <= y <= 13 and (y <= 9 or abs(x - 5) <= 13 - y))
    p.fill(m, "brass", inner=(3, 2), rim=4, shade=1)
    inner = grid(lambda x, y: 2 <= x <= 8 and 3 <= y <= 12 and (y <= 9 or abs(x - 5) <= 12 - y))
    p.fill(inner, "paint:Страж", inner=(3, 2), rim=4, shade=1)
    p.col(5, 4, 10, "steel", [4, 3, 3, 3, 2, 2, 2])       # a steel bar down the middle
    p.line([(11, 6), (14, 6)], "wood", 3)                 # the bolt, its shaft
    p.line([(11, 7), (14, 7)], "wood", 2)
    p.px(15, 5, "red", 3)                                 # its fletching
    p.px(15, 8, "red", 2)
    p.px(10, 6, "steel", 4)                               # its head, on the shield's face
    p.px(10, 7, "steel", 3)
    for x, y, lv in ((11, 4, 4), (12, 9, 3), (10, 3, 3), (11, 10, 2)):
        p.px(x, y, "fire", lv)                            # sparks off the strike
    return p.done()


@icon("anchor")
def anchor():
    """Якорь: an iron anchor — a ring at the top with its chain running off, the stock across, the shank, the
    arms curving up to barbed flukes."""
    p = Pix()
    pts = set()
    for x, y in ((6, 1), (7, 1), (8, 1), (6, 2), (8, 2), (6, 3), (7, 3), (8, 3)):
        pts.add((x, y))                                   # the ring
    for x in range(4, 12):
        pts.add((x, 4))                                   # the stock
    for y in range(4, 13):
        pts.add((7, y)); pts.add((8, y))                  # the shank
    arm = [(6, 13), (5, 13), (4, 12), (3, 11), (3, 10), (9, 13), (10, 13), (11, 12), (12, 11), (12, 10)]
    pts.update(arm)
    pts.update([(7, 13), (8, 13), (7, 14), (8, 14)])      # the crown
    pts.update([(2, 9), (3, 9), (2, 10), (13, 9), (12, 9), (13, 10)])   # the flukes
    m = np.zeros((16, 16), bool)
    for x, y in pts:
        m[y, x] = True
    p.fill(m, "iron", inner=(3, 2), rim=4, shade=1)
    p.dark(7, 2)                                          # the ring's eye
    for x, y, lv in ((10, 1, 3), (11, 2, 2), (12, 2, 3), (13, 3, 2), (14, 4, 3), (14, 5, 2)):
        p.px(x, y, "steel", lv)                           # the chain, link by link
    p.px(9, 1, "steel", 3)
    return p.done()


@icon("counter")
def counter():
    """Контрудар: an armoured fist driven back at whoever struck — a steel gauntlet, its knuckles rounded at the
    front, the fingers folded under them, the thumb across; the Guard's paint on the cuff; a flash where it lands."""
    p = Pix()
    cuff = grid(lambda x, y: 1 <= x <= 4 and 6 <= y <= 11)
    p.fill(cuff, "paint:Страж", inner=(3, 2))
    p.col(4, 6, 11, "steel", [3, 3, 2, 2, 2, 1])          # the cuff's steel edge
    fist = grid(lambda x, y: 5 <= x <= 12 and 4 <= y <= 12 and not (x == 12 and y in (4, 12))
                and not (x == 5 and y == 4))
    p.fill(fist, "steel", inner=(3, 2))
    for x in (11, 12):                                    # the knuckles, a lit ridge at the front
        p.col(x, 5, 11, "steel", [4, 3, 4, 3, 4, 3, 2] if x == 11 else [3, 2, 3, 2, 3, 2, 1])
    for y in (6, 8, 10):
        for x in range(8, 11):
            p.px(x, y, "steel", 1)                        # the folded fingers
    p.rect(5, 10, 9, 11, "steel", [4, 3])                 # the thumb, across the fingers
    p.px(5, 12, "steel", 2)
    for x, y, lv in ((14, 8, 4), (14, 6, 3), (14, 10, 3), (15, 8, 2)):
        p.px(x, y, "fire", lv)                            # where it lands
    return p.done()


@icon("hot")
def hot_armour():
    """Раскалённая броня: a breastplate glowing red-hot — its rim brightest, the ridge down the middle white-hot,
    heat curling up off the shoulders."""
    p = Pix()
    rows = {4: [(3, 5), (10, 12)], 5: [(2, 13)], 6: [(2, 13)], 7: [(4, 11)], 8: [(4, 11)], 9: [(4, 11)],
            10: [(4, 11)], 11: [(4, 11)], 12: [(5, 10)], 13: [(6, 9)]}
    m = np.zeros((16, 16), bool)
    for y, spans in rows.items():
        for x0, x1 in spans:
            m[y, x0:x1 + 1] = True
    p.fill(m, "iron", inner=(3, 2), rim=4, shade=1)
    pm = np.pad(m, 1)
    core = m & pm[:-2, 1:-1] & pm[2:, 1:-1] & pm[1:-1, :-2] & pm[1:-1, 2:]
    p.fill(core, "ember", inner=(3, 2), rim=4, shade=2)   # glowing through from inside the iron
    for x, y in ((3, 5), (12, 5), (5, 12), (10, 12)):
        p.px(x, y, "brass", 4)                            # rivets
    for y in range(5, 13):
        p.px(7, y, "fire", 4)                             # the ridge, white-hot
        p.px(8, y, "fire", 3)
    for x, y, lv in ((6, 1, 3), (7, 0, 2), (9, 1, 3), (8, 2, 2)):
        p.px(x, y, "fire", lv)                            # heat rising off the neck
    return p.done()


# ---------------------------------------------------------------- the Sage
def flame(p, x0, base, h, w=3, lv=(4, 3, 2, 1)):
    """A tongue of fire standing on base, h high, w wide at the foot — white-hot inside, red at the edges, its
    tip leaning a little right."""
    for k in range(h):
        y = base - k
        half = max(0, round((w / 2) * (1 - k / h) ** 0.7))
        lean = round(k * 0.25)
        for x in range(x0 - half + lean, x0 + half + lean + 1):
            d = abs(x - (x0 + lean)) / max(half, 1)
            t = 0.6 * d + 0.5 * k / h
            p.px(x, y, "fire", lv[min(len(lv) - 1, int(t * len(lv)))])


@icon("ground")
def ground_strike():
    """Разряд в землю: a bolt driven straight down into the ground — the earth cracks, sparks run out along it to
    both sides (everyone near is stunned)."""
    p = Pix()
    p.rect(1, 12, 14, 14, "stone", [3, 2, 1])             # the ground
    core = p.line([(8, 0), (6, 3), (9, 6), (7, 9), (8, 11)], "volt", 4)
    for x, y in core:
        if (x + 1, y) not in core:
            p.px(x + 1, y, "volt", 2)
    p.rect(6, 11, 9, 12, "volt", [4, 3])                  # where it strikes
    for x, y, lv in ((4, 12, 3), (3, 13, 2), (11, 12, 3), (12, 13, 2), (2, 12, 2), (13, 11, 2)):
        p.px(x, y, "volt", lv)                            # the charge running out through the ground
    for x, y in ((5, 13), (10, 13)):
        p.dark(x, y)                                      # cracks
    for x, y in ((3, 10), (12, 9)):
        p.px(x, y, "volt", 4)                             # sparks thrown up
    return p.done()


@icon("overload")
def overload():
    """Перегрузка: a pressure gauge driven past its limit — the needle hard over in the red, the glass cracked,
    sparks jumping off the rim (the golems near it strike twice as hard)."""
    p = Pix()
    p.disc(7.5, 8.5, 6.2, "steel", levels=(4, 3, 3, 2, 1))     # the rim
    p.disc(7.5, 8.5, 4.9, "bone", levels=(4, 4, 4, 3))         # the face
    for x, y in ((4, 6), (5, 5), (7, 4), (9, 5), (3, 8)):
        p.px(x, y, "iron", 2)                                 # the scale's ticks
    for x, y in ((10, 5), (11, 6), (11, 7), (12, 8), (10, 6)):
        p.px(x, y, "red", 3)                                  # the red zone
    p.line([(7, 9), (9, 7), (11, 6)], "red", 1)               # the needle, hard over
    p.px(7, 9, "brass", 4)                                    # its hub
    p.px(4, 11, "iron", 1)                                    # the crack across the glass
    p.px(5, 10, "iron", 1)
    p.px(5, 12, "iron", 1)
    for x, y, lv in ((14, 2, 4), (13, 1, 3), (15, 3, 2), (1, 2, 4), (2, 1, 3)):
        p.px(x, y, "volt", lv)                                # sparks off it
    return p.done()


@icon("fireball")
def fireball():
    """Огненный шар: a ball of fire flying right, white-hot at its heart, its flames streaming back behind it."""
    p = Pix()
    for k, (x, y) in enumerate(((2, 4), (3, 6), (1, 8), (3, 10), (5, 12))):
        p.line([(x, y), (8, 8)], "fire", 1 if k % 2 else 2)   # the tail, streaming back
    p.disc(9.5, 8.0, 4.6, "fire", levels=(4, 4, 3, 2, 1))
    p.disc(10.2, 7.4, 2.0, "fire", levels=(4,))
    p.px(10, 6, "lantern", 4)                             # the white heart
    return p.done()


@icon("firewall")
def firewall():
    """Огненная стена: a row of flames rising off a line of burning coals — three tongues, the middle one tallest."""
    p = Pix()
    for x0, h in ((3, 8), (8, 11), (12, 7)):
        flame(p, x0, 11, h, w=4)
    p.rect(1, 12, 14, 13, "ember", [3, 1])                # the coals
    for x in (2, 5, 9, 13):
        p.px(x, 12, "fire", 4)
    return p.done()


@icon("blades")
def hot_blades():
    """Раскалённые клинки: two swords crossed, their blades glowing red from the forge with white-hot edges, brass
    guards, dark grips, brass pommels."""
    p = Pix()
    for flip in (1, 0):                                       # the second sword crosses over the first
        def P(x, y):
            return (15 - x, y) if flip else (x, y)
        p.line([P(10, 9), P(3, 2)], "ember", 1)               # the blade: its shadowed side
        p.line([P(9, 9), P(2, 2)], "ember", 3)
        p.line([P(9, 8), P(3, 2)], "fire", 4)                 # its edge, catching the light
        p.px(*P(2, 1), "fire", 4)
        p.line([P(9, 11), P(11, 9)], "brass", 3)              # the guard
        p.px(*P(9, 11), "brass", 4)
        p.line([P(11, 11), P(12, 12)], "wood", 2)             # the grip
        p.px(*P(13, 13), "brass", 4)                          # the pommel
    return p.done()


# ---------------------------------------------------------------- the Forge
@icon("magnet")
def magnet():
    """Магнит: a horseshoe magnet standing open end up, in the Forge's red, its poles bright steel; the field
    arching between them, an iron nut flying in."""
    p = Pix()
    m = grid(lambda x, y: (4 <= y <= 10 and (2 <= x <= 4 or 11 <= x <= 13))
             or (11 <= y <= 14 and abs(x - 7.5) + max(0, y - 11) * 1.2 <= 6.2 and not (y <= 12 and 5 <= x <= 10)))
    p.fill(m, "paint:Горн", inner=(3, 2), rim=4, shade=1)
    p.rect(2, 4, 4, 5, "steel", [4, 2])                       # the poles
    p.rect(11, 4, 13, 5, "steel", [4, 2])
    for x, y, lv in ((5, 3, 2), (6, 2, 3), (9, 2, 3), (10, 3, 2)):
        p.px(x, y, "volt", lv)                                # the field arching over the gap
    p.rect(7, 0, 8, 1, "steel", [4, 2])                       # a nut, pulled in
    return p.done()


@icon("rod")
def lightning_rod():
    """Громоотвод: an iron spike standing on two white insulators and a copper foot — lightning out of the sky
    strikes its point and a ring of sparks flares round it."""
    p = Pix()
    p.rect(4, 13, 11, 14, "copper", [4, 1])                   # the foot
    p.rect(5, 11, 10, 12, "bone", [4, 2])                     # the insulators
    p.rect(6, 9, 9, 10, "bone", [4, 2])
    p.col(7, 3, 8, "steel", [4])                              # the spike
    p.col(8, 3, 8, "steel", [2])
    p.px(7, 2, "steel", 4)
    core = p.line([(15, 4), (12, 3), (13, 1), (8, 1)], "volt", 4)     # the bolt
    for x, y in core:
        if (x, y + 1) not in core and y + 1 < 16:
            p.px(x, y + 1, "volt", 2)
    for x, y in ((6, 1), (7, 0), (8, 0), (6, 3)):
        p.px(x, y, "volt", 3)                                 # sparks round the point
    return p.done()


@icon("smoke")
def smokestack():
    """Дымовая труба: a brick stack in the Forge's red with an iron lip, black smoke rolling out of it in puffs
    that grow as they rise (no one sees far through it)."""
    p = Pix()
    stack = grid(lambda x, y: 5 <= x <= 9 and 7 <= y <= 14)
    p.fill(stack, "paint:Горн", inner=(3, 2))
    for y in (9, 11, 13):                                     # the courses of brick
        for x in range(5, 10):
            p.px(x, y, "paint:Горн", 1)
        p.px(7 if y % 4 == 1 else 6, y + 1 if y < 14 else y, "paint:Горн", 1)
    p.rect(4, 6, 10, 7, "iron", [4, 2])                       # the lip
    p.disc(7.5, 3.6, 1.6, "stone", levels=(4, 3, 2))          # the smoke
    p.disc(10.5, 2.4, 2.1, "stone", levels=(4, 3, 2, 1))
    p.disc(13.6, 2.0, 1.9, "stone", levels=(3, 2, 1))
    return p.done()


@icon("whistle")
def steam_whistle():
    """Паровой свисток: a brass bell whistle standing on its pipe, side on — the domed bell, the dark ring of its
    slot, the pull-cord lever with its red knob — and a white plume of steam shooting straight up out of the slot,
    widening as it rises, with the sound in arcs either side."""
    p = Pix()
    p.rect(6, 13, 9, 14, "copper", [3, 1])                    # the pipe's flange
    p.col(7, 11, 12, "copper", [4, 3])                        # the pipe
    p.col(8, 11, 12, "copper", [2, 1])
    bell = grid(lambda x, y: (6 <= x <= 9 and 7 <= y <= 10) or (y == 6 and 7 <= x <= 8))
    p.fill(bell, "brass", inner=(3, 2))
    for x in range(6, 10):
        p.px(x, 9, "iron", 0)                                 # the slot
    p.line([(10, 8), (12, 10)], "iron", 3)                    # the lever
    p.px(13, 11, "red", 3)
    for y, half in ((5, 1), (4, 1), (3, 2), (2, 2), (1, 3), (0, 3)):   # the plume, widening upward
        for x in range(8 - half, 8 + half):
            p.px(x, y, "steel", 4 if abs(x - 7.5) < half - 0.5 else 3)
    for x, ys in ((3, (4, 5, 6)), (12, (4, 5, 6)), (1, (3, 7)), (14, (3, 7))):
        for y in ys:
            p.px(x, y, "steel", 2)                            # its scream
    return p.done()


@icon("maw")
def furnace_maw():
    """Пасть топки: a furnace door flung open like a jaw — iron teeth along the frame, fire roaring inside and
    licking out."""
    p = Pix()
    frame = grid(lambda x, y: 1 <= x <= 13 and 3 <= y <= 14)
    p.fill(frame, "paint:Горн", inner=(3, 2))
    mouth = grid(lambda x, y: 3 <= x <= 11 and 5 <= y <= 12)
    p.fill(mouth, "ember", inner=(4, 3), rim=2, shade=1)
    for x in (3, 5, 7, 9, 11):
        p.px(x, 5, "steel", 3)                            # teeth above
        p.px(x + (1 if x < 11 else 0), 12, "steel", 2)    # and below
    flame(p, 7, 11, 5, w=4)
    p.rect(11, 0, 14, 2, "iron", [4, 2, 1])               # the door, swung up
    p.col(14, 0, 4, "iron", [2])
    p.px(14, 8, "fire", 3)                                # fire licking out
    p.px(15, 7, "fire", 2)
    return p.done()


@icon("greedy")
def greedy_furnace():
    """Жадная топка: a furnace with a wide hopper on top, the fire thrown at it pouring down into the hopper from
    both sides — it eats the fire (fire from afar does it no harm)."""
    p = Pix()
    body = grid(lambda x, y: 3 <= x <= 12 and 8 <= y <= 14)
    p.fill(body, "paint:Горн", inner=(3, 2))
    p.rect(6, 10, 9, 12, "ember", [4, 3, 2])                  # the door, glowing
    p.px(7, 11, "iron", 1)
    p.px(8, 11, "iron", 1)
    hop = grid(lambda x, y: 3 <= y <= 7 and abs(x - 7.5) <= 6.5 - (y - 3))
    p.fill(hop, "iron", inner=(3, 2))
    for x in range(4, 12):
        p.dark(x, 4)                                          # its open mouth
    p.px(7, 4, "fire", 4)
    p.px(8, 4, "fire", 3)
    for pts, sh in (([(0, 0), (2, 1), (4, 3)], 1), ([(15, 0), (13, 1), (11, 3)], -1)):
        for x, y in p.line([(a + sh, b) for a, b in pts], "fire", 2):
            pass
        p.line(pts, "fire", 4)                                # fire pouring in
    return p.done()


# ---------------------------------------------------------------- the Gun
@icon("spider")
def spider_legs():
    """Паучьи лапы: a squat body in the Gun's olive on four jointed iron legs, two each side, knees high, feet
    planted wide — it steps back out of reach."""
    p = Pix()
    for side in (-1, 1):
        for k, (kx, ky, fx) in enumerate(((3.5, 2, 0.5), (5.5, 4, 2.5))):
            x0, x1 = 7.5 + side * 2, 7.5 + side * kx
            p.line([(round(x0), 7 + k), (round(x1), ky + 1)], "iron", 3)          # thigh up to the knee
            p.line([(round(x1), ky + 1), (round(7.5 + side * (kx + fx + 2)), 13 + (k == 0))], "iron", 2)
            p.px(round(x1), ky + 1, "brass", 4)                                   # the knee joint
    body = grid(lambda x, y: ((x - 7.5) / 3.6) ** 2 + ((y - 8.5) / 2.6) ** 2 <= 1)
    p.fill(body, "paint:Орудие", inner=(3, 2))
    p.px(9, 8, "red", 4)                                       # its eye
    return p.done()


@icon("canister")
def canister():
    """Картечь: a tin of shot bursting out of the muzzle — the tin's torn lip on the left, the balls fanning out
    to the right, bigger and nearer at the front."""
    p = Pix()
    tin = grid(lambda x, y: 1 <= x <= 5 and 4 <= y <= 11)
    p.fill(tin, "steel", inner=(3, 2))
    for y in (4, 7, 11):
        p.px(6, y, "steel", 3)                                 # the torn lip
    for (cx, cy, r) in ((8.5, 7.5, 1.2), (11, 4.5, 1.3), (11.5, 10.5, 1.3), (14, 7.5, 1.3), (13.5, 2.0, 0.9),
                        (14.0, 13.0, 0.9), (9.5, 12.5, 0.8), (9.5, 2.5, 0.8)):
        p.disc(cx, cy, r, "iron", levels=(4, 3, 2))
    for x, y in ((7, 5), (7, 10)):
        p.px(x, y, "fire", 3)                                  # the flash
    return p.done()


@icon("hotshot")
def hot_shot():
    """Калёное ядро: a solid shot heated red in the furnace, held in iron tongs — its crust dark in patches,
    glowing through them; heat shimmering up off it."""
    p = Pix()
    p.disc(8.0, 8.5, 4.6, "ember", levels=(4, 4, 3, 2, 1))
    for x, y in ((6, 7), (9, 10), (10, 7)):
        p.px(x, y, "ember", 1)                                 # crust
    p.px(6, 6, "fire", 4)                                      # where it's hottest
    for side in (-1, 1):                                       # the tongs' jaws gripping it
        x = 8 + side * 5
        p.col(x, 6, 11, "iron", [4, 3, 3, 2, 2, 1])
        p.line([(x, 11), (8 + side * 2, 14)], "iron", 2)
    for x, y in ((6, 2), (8, 1), (10, 2), (7, 3)):
        p.px(x, y, "fire", 2)                                  # heat rising
    return p.done()


@icon("bomb")
def bomb():
    """Бомба с фитилём: a round black iron bomb with a brass fuse cap, the fuse curling out of it and burning, a
    spark spitting at its end."""
    p = Pix()
    p.disc(7.0, 9.5, 5.0, "iron", levels=(3, 2, 2, 1, 1))
    p.px(5, 7, "steel", 4)                                     # its shine
    p.px(4, 8, "steel", 3)
    p.rect(9, 3, 11, 5, "brass", [4, 3, 2])                    # the fuse cap
    p.line([(11, 2), (12, 1), (13, 1)], "wood", 3)             # the fuse
    for x, y, lv in ((14, 0, 4), (15, 1, 3), (14, 2, 2), (13, 0, 3)):
        p.px(x, y, "fire", lv)                                 # burning
    return p.done()


# ---------------------------------------------------------------- the Mechanic
@icon("repair")
def repair():
    """Ремонт: a big open-ended spanner across a hex nut, the Mechanic's yellow on its grip."""
    p = Pix()
    p.tube(3.0, 13.0, 9.5, 6.5, 1.1, "steel", levels=(4, 3, 2))
    p.tube(3.0, 13.0, 6.0, 10.0, 1.3, "paint:Механик", levels=(4, 3, 2, 1))   # the grip
    head = grid(lambda x, y: ((x - 11.2) ** 2 + (y - 4.6) ** 2 <= 11.5) and not (abs(x - 12.6) + abs(y - 3.2) <= 1.6
                                                                               or (x >= 12 and y <= 3)))
    p.fill(head, "steel", inner=(3, 2))
    p.px(3, 13, "iron", 2)
    for x, y in ((12, 2), (13, 3), (14, 3), (13, 1)):
        if 0 <= x < 16:
            p.a[y, x] = False
            p.hole[y, x] = False
    p.disc(3.0, 4.0, 1.8, "brass", levels=(4, 3, 2), hole=0.6)   # a nut
    return p.done()


@icon("crane")
def crane():
    """Кран: a little derrick in the Mechanic's yellow — the mast, the jib reaching out, the pulley, a chain down
    to a hook."""
    p = Pix()
    p.rect(1, 13, 8, 14, "iron", [3, 1])                       # its foot
    p.col(3, 2, 12, "paint:Механик", [4, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2])     # the mast
    p.col(4, 2, 12, "paint:Механик", [2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1])
    p.line([(4, 2), (13, 2)], "paint:Механик", 4)              # the jib
    p.line([(4, 3), (13, 3)], "paint:Механик", 2)
    p.line([(5, 4), (8, 3)], "iron", 2)                        # a strut
    p.px(13, 4, "brass", 4)                                    # the pulley
    for y in range(5, 10):
        p.px(13, y, "steel", 3 if y % 2 else 2)                # the chain
    p.line([(12, 10), (13, 11), (14, 10)], "steel", 4)         # the hook
    p.px(14, 9, "steel", 3)
    return p.done()


@icon("spares")
def spares():
    """Запасные части: a wooden crate of spares, lid off — a cog and the head of a bolt sticking up out of it."""
    p = Pix()
    crate = grid(lambda x, y: 2 <= x <= 13 and 8 <= y <= 14)
    p.fill(crate, "wood", inner=(3, 2))
    for y in (10, 12):
        for x in range(3, 13):
            p.px(x, y, "wood", 1)                              # the boards
    p.col(7, 9, 13, "wood", [4])
    for x in (3, 12):
        p.px(x, 9, "steel", 4)                                 # nails
    for k in range(8):                                         # the cog
        a = k * np.pi / 4
        p.px(round(5.5 + np.cos(a) * 3.0), round(5.5 + np.sin(a) * 3.0), "steel", 3)
    p.disc(5.5, 5.5, 2.2, "steel", levels=(4, 3, 2), hole=0.7)
    p.rect(10, 2, 12, 3, "iron", [4, 2])                       # a bolt's head
    p.col(11, 4, 7, "iron", [3, 2, 3, 2])
    return p.done()


@icon("oiler")
def oiler():
    """Маслёнка: an oil can — its round body, the long thin spout reaching up and out, the thumb pump on top, a
    drop of oil falling off the tip (the golems near it act first)."""
    p = Pix()
    body = grid(lambda x, y: ((x - 5.5) / 4.6) ** 2 + ((y - 10.5) / 3.6) ** 2 <= 1)
    p.fill(body, "paint:Механик", inner=(3, 2))
    p.rect(4, 6, 7, 6, "brass", [3])                           # the neck
    p.col(5, 4, 5, "steel", [4, 3])                            # the thumb pump
    p.px(6, 4, "steel", 2)
    p.line([(8, 7), (13, 2)], "steel", 3)                      # the spout
    p.line([(9, 7), (13, 3)], "steel", 2)
    p.px(14, 4, "iron", 1)                                     # the drop of oil
    p.px(14, 5, "iron", 2)
    return p.done()


@icon("welding")
def welding():
    """Сварка: a welding torch — its brass handle and valve, the steel neck bent down, a white-blue flame at the
    nozzle and a shower of sparks off the seam below."""
    p = Pix()
    p.tube(1.5, 4.5, 7.5, 4.5, 1.4, "brass", levels=(4, 3, 2))   # the handle
    p.px(3, 2, "red", 3)                                       # the valve
    p.px(3, 3, "red", 2)
    p.line([(8, 4), (10, 5), (11, 7)], "steel", 3)             # the neck
    p.px(11, 8, "iron", 2)                                     # the nozzle
    p.px(11, 9, "volt", 4)                                     # the flame
    p.px(11, 10, "volt", 3)
    p.px(12, 10, "steel", 4)
    p.rect(5, 12, 15, 13, "iron", [3, 1])                      # the seam
    for x, y, lv in ((9, 11, 4), (13, 11, 4), (8, 10, 3), (14, 9, 3), (12, 12, 4), (7, 11, 2)):
        p.px(x, y, "fire", lv)                                 # sparks
    return p.done()


@icon("oiltank")
def oiltank():
    """Масляный бак: a riveted drum of oil, the Mechanic's yellow bands round it, a spigot at the foot dripping
    black oil; a flame on the drip (oil burns twice as hot)."""
    p = Pix()
    drum = grid(lambda x, y: 3 <= x <= 11 and 2 <= y <= 13 and not (x in (3, 11) and y in (2, 13)))
    p.fill(drum, "iron", inner=(3, 2))
    for y in (4, 11):
        p.rect(3, y, 11, y, "paint:Механик", [4 if y == 4 else 3])   # the bands
    for x, y in ((7, 5), (7, 6), (6, 7), (7, 7), (8, 7), (6, 8), (7, 8), (8, 8), (7, 9)):
        p.px(x, y, "iron", 0)                                  # the oil drop sign
    p.px(6, 7, "steel", 2)
    p.rect(12, 11, 13, 11, "brass", [3])                       # the spigot
    p.px(13, 12, "iron", 1)
    p.px(13, 13, "fire", 4)                                    # the flame on the drip
    p.px(14, 13, "fire", 3)
    p.px(13, 14, "fire", 2)
    return p.done()


# ---------------------------------------------------------------- rare modules, for any frame
@icon("torch")
def living_torch():
    """Живой факел: a torch made of a golem's own arm — an iron bracket, a pitch-soaked head blazing up tall (it
    burns from the start to the end)."""
    p = Pix()
    p.tube(5.0, 14.0, 8.0, 8.0, 1.0, "wood", levels=(4, 3, 2))   # the haft
    p.rect(6, 6, 10, 8, "iron", [4, 3, 2])                     # the iron cup
    p.px(6, 7, "brass", 4)
    flame(p, 8, 5, 6, w=5)
    flame(p, 7, 3, 3, w=2)
    p.px(10, 1, "fire", 3)
    p.px(5, 3, "fire", 2)
    return p.done()


@icon("nozzles")
def nozzles():
    """Сопла: two bell nozzles side by side pointing back, fire blasting out of them — it lunges four cells."""
    p = Pix()
    for y0 in (2, 8):
        bell = grid(lambda x, y, y0=y0: 7 <= x <= 13 and abs(y - (y0 + 2.5)) <= 1 + (13 - x) * 0.35)
        p.fill(bell, "copper", inner=(3, 2))
        p.col(13, y0 + 1, y0 + 4, "iron", [3, 2, 2, 1])
        for k, (x, w) in enumerate(((6, 2), (4, 2), (2, 1), (1, 0))):
            for dy in range(-w, w + 1):
                p.px(x, y0 + 2 + dy + (k % 2) * 0, "fire", 4 - min(3, abs(dy) + k // 2))
        p.px(5, y0 + 2, "lantern", 4)
    return p.done()


@icon("bounce")
def bouncing_shot():
    """Скачущее ядро: a cannonball skipping along — a dotted arc of its bounces behind it, a puff of dust and
    flame where it last struck."""
    p = Pix()
    for x, y in ((1, 12), (2, 10), (3, 9), (5, 9), (6, 10), (7, 12)):
        p.px(x, y, "steel", 2)                                 # the arc of the last bounce
    p.rect(5, 13, 9, 13, "stone", [3])                         # dust where it struck
    p.px(6, 12, "fire", 3)
    p.px(8, 12, "fire", 2)
    p.disc(11.0, 6.0, 3.6, "iron", levels=(4, 3, 2, 1, 1))
    p.px(10, 4, "steel", 4)
    for x, y in ((8, 9), (9, 10)):
        p.px(x, y, "steel", 3)                                 # rising again
    return p.done()


@icon("whirl")
def fire_whirl():
    """Огненный смерч: a funnel of fire twisting up off the ground, wide at the top, its bands spiralling round."""
    p = Pix()
    for y in range(1, 14):
        half = 1 + (13 - y) * 0.45
        cx = 7.5 + np.sin(y * 0.7) * 1.2
        for x in range(16):
            if abs(x - cx) <= half:
                band = int((x - cx + y * 0.9) // 2) % 2
                lv = 4 if abs(x - cx) < half * 0.35 else (3 if band else 2)
                p.px(x, y, "fire", lv)
    p.rect(4, 14, 11, 14, "ember", [2])
    return p.done()


@icon("grapple")
def grappling_hook():
    """Крюк-кошка: an iron grapnel hanging from its rope — a ring at the top, a straight shank, three sharp
    prongs curving up at the foot, their points bright."""
    p = Pix()
    p.line([(0, 0), (2, 1), (3, 0), (5, 1), (7, 1)], "wood", 3)       # the rope
    p.disc(7.5, 2.5, 1.5, "steel", levels=(4, 3, 2), hole=0.5)        # the ring
    p.col(7, 4, 11, "steel", [4])                              # the shank
    p.col(8, 4, 11, "steel", [2])
    for side in (-1, 1):
        pts = [(7.5 + side * 1.5, 12), (7.5 + side * 3.5, 12), (7.5 + side * 4.5, 11), (7.5 + side * 5.0, 9)]
        p.line([(round(x), y) for x, y in pts], "steel", 3 if side < 0 else 2)
        p.px(round(7.5 + side * 5.0), 8, "steel", 4)           # its point
    p.rect(7, 12, 8, 13, "steel", [3, 2])                      # the front prong, toward us
    p.px(7, 14, "steel", 4)
    return p.done()


@icon("mill")
def millstone_wheels():
    """Колёса-жернова: a pair of round grindstones on one iron axle, seen a little from the front — each a disc
    with a bright rim, a ring groove and a square iron hub; the axle between them; grit spraying off the back."""
    p = Pix()
    p.rect(4, 7, 11, 8, "iron", [3, 1])                       # the axle
    for cx, lv in ((4.5, (4, 3, 3, 2, 1)), (11.0, (3, 3, 2, 2, 1))):
        p.disc(cx, 8.0, 4.2, "stone", levels=lv)
        for a in np.linspace(0, 2 * np.pi, 18, endpoint=False):
            p.px(round(cx + np.cos(a) * 2.6), round(8.0 + np.sin(a) * 2.6), "stone", 1)   # the ring groove
        p.rect(round(cx) - 1, 7, round(cx), 8, "iron", [3, 1])                           # the hub
    for x, y in ((0, 12), (1, 14), (2, 13)):
        p.px(x, y, "stone", 3)                                # grit
    return p.done()


@icon("dome")
def dome_shield():
    """Щит-купол: a dome of cold blue force over a brass emitter, its rim brightest — nothing shoots through it
    from afar."""
    p = Pix()
    p.rect(3, 12, 12, 14, "brass", [4, 3, 1])                  # the emitter
    p.rect(6, 11, 9, 11, "steel", [4])
    for y in range(16):
        for x in range(16):
            d = np.hypot((x - 7.5) / 7.0, (y - 12.0) / 10.5)
            if d <= 1.0 and y <= 11:
                lv = 4 if d > 0.86 else (2 if (x + y) % 3 else 3)
                p.px(x, y, "volt", lv)
    p.px(4, 5, "steel", 4)                                     # a glint on the dome
    return p.done()


@icon("bombcore")
def boiler_bomb():
    """Котёл-бомба: an upright riveted boiler swollen past bearing — its gauge in the red, the safety valve
    screaming steam, a seam split and glowing (break it and it blows)."""
    p = Pix()
    body = grid(lambda x, y: (4 <= x <= 11 and 5 <= y <= 14) or (y == 4 and 5 <= x <= 10) or (y == 3 and 6 <= x <= 9))
    p.fill(body, "copper", inner=(3, 2))
    for y in (7, 11):
        for x in range(4, 12):
            p.px(x, y, "copper", 1)                             # the seams
        for x in (5, 8, 11):
            p.px(x, y, "brass", 4)                             # rivets
    p.disc(7.5, 9.0, 1.4, "bone", levels=(4, 3))               # the gauge
    p.px(8, 9, "red", 2)
    p.px(8, 8, "red", 2)
    p.rect(7, 1, 8, 2, "brass", [4, 2])                        # the safety valve
    for x, y, lv in ((5, 0, 4), (4, 1, 3), (10, 0, 4), (11, 1, 3)):
        p.px(x, y, "steel", lv)                                # steam off it
    for x, y in ((10, 12), (11, 13), (10, 13)):
        p.px(x, y, "fire", 4)                                  # a split seam, glowing
    return p.done()


@icon("ram")
def ram_nose():
    """Таранный нос: a battering ram's iron head shaped like a ram's — the horns curled back, the brow blunt —
    on a wooden beam, aimed to the right."""
    p = Pix()
    p.rect(0, 7, 6, 9, "wood", [4, 3, 2])                      # the beam
    p.col(6, 6, 10, "iron", [3, 3, 2, 2, 1])                   # the collar
    head = grid(lambda x, y: 7 <= x <= 13 and 5 <= y <= 11 and (x <= 11 or abs(y - 8) <= 13 - x))
    p.fill(head, "iron", inner=(3, 2))
    for x, y in ((9, 3), (10, 2), (11, 2), (12, 3), (12, 4), (11, 5)):
        p.px(x, y, "brass", 4 if y <= 3 else 3)                # the horn, curled back
    p.px(11, 7, "red", 4)                                      # the eye
    return p.done()


@icon("buffer")
def buffer():
    """Отбойник: a railway buffer — a round steel plate on a sprung plunger out of its housing, struck flat-on,
    the target thrown back."""
    p = Pix()
    p.rect(1, 5, 5, 11, "iron", [4, 3, 3, 3, 2, 2, 1])        # the housing
    p.rect(6, 7, 8, 9, "steel", [4, 3, 2])                    # the plunger
    for x in (6, 8):
        p.px(x, 6, "steel", 2)                                 # the spring
        p.px(x, 10, "steel", 2)
    p.disc(10.5, 8.0, 0.1, "steel", levels=(4,))
    p.rect(9, 3, 11, 13, "steel", [4, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1])   # the plate
    p.col(9, 4, 12, "steel", [4])
    for x, y in ((13, 6), (14, 8), (13, 10)):
        p.px(x, y, "steel", 2)                                 # the knock
    return p.done()


@icon("spark")
def sparking_hammer():
    """Искрящий молот: a smith's hammer bringing its head down on armour, sparks fountaining off the blow."""
    p = Pix()
    p.tube(2.0, 13.0, 8.0, 6.0, 1.0, "wood", levels=(4, 3, 2))   # the haft
    head = grid(lambda x, y: (5 <= x <= 12 and 2 <= y <= 6) and not (x == 12 and y in (2, 6)))
    p.fill(head, "iron", inner=(3, 2))
    p.col(12, 3, 5, "steel", [4, 3, 2])                        # the striking face
    for x, y, lv in ((14, 2, 4), (14, 5, 3), (13, 8, 4), (15, 7, 3), (11, 9, 2), (15, 4, 4)):
        p.px(x, y, "fire", lv)                                 # sparks
    return p.done()


@icon("poker")
def poker():
    """Кочерга: a long iron poker, its hooked tip glowing red from the fire (it throws the target into the
    flames)."""
    p = Pix()
    p.tube(2.0, 13.0, 11.5, 3.5, 0.8, "iron", levels=(4, 3, 2))
    p.line([(2, 13), (1, 12), (2, 11), (3, 12)], "brass", 3)   # the ring of its handle
    p.line([(10, 4), (11, 3), (12, 2), (13, 2), (14, 3)], "ember", 3)
    p.px(14, 4, "fire", 4)                                     # the hook, red-hot
    p.px(13, 3, "fire", 4)
    p.px(12, 3, "ember", 2)
    return p.done()


@icon("tracks")
def tracks():
    """Гусеницы: a caterpillar track run round its wheels, side on — the links of the belt, the road wheels
    inside, the drive sprocket at the front."""
    p = Pix()
    belt = grid(lambda x, y: 1 <= x <= 14 and 5 <= y <= 12 and not ((x in (1, 14)) and y in (5, 12)))
    p.fill(belt, "iron", inner=(2, 2), rim=3, shade=1)
    inside = grid(lambda x, y: 2 <= x <= 13 and 6 <= y <= 11)
    p.fill(inside, "iron", inner=(1, 1), rim=1, shade=1)
    for x in range(2, 14, 2):
        p.px(x, 5, "steel", 3)                                 # the links
        p.px(x + 1, 12, "steel", 2)
    for cx in (4.5, 8.0, 11.5):
        p.disc(cx, 8.5, 1.8, "steel", levels=(4, 3, 2), hole=0.5)   # the road wheels
    return p.done()


@icon("flail")
def flail():
    """Кистень: a wooden handle, a short chain, a spiked iron ball swinging out on it (it strikes two cells)."""
    p = Pix()
    p.tube(1.5, 14.0, 4.5, 10.0, 1.0, "wood", levels=(4, 3, 2))
    p.px(5, 9, "iron", 3)                                      # the ring
    for x, y, lv in ((6, 8, 3), (7, 7, 2), (8, 6, 3), (9, 6, 2)):
        p.px(x, y, "steel", lv)                                # the chain
    p.disc(11.5, 5.0, 2.8, "iron", levels=(4, 3, 2, 1))
    for x, y in ((11, 1), (15, 5), (11, 9), (14, 2), (14, 8)):
        p.px(x, y, "steel", 4)                                 # spikes
    return p.done()


# ---------------------------------------------------------------- cores: a sphere in its brass cage
def core(fillfn):
    p = Pix()
    fillfn(p)
    for k in range(-1, 2):                                     # the cage: a brass hoop and its straps
        p.px(7 + k, 1, "brass", 4)
        p.px(7 + k, 14, "brass", 2)
    for y in range(3, 13):
        p.px(1, y, "brass", 3)
        p.px(14, y, "brass", 2)
    for x, y in ((2, 2), (3, 1), (12, 1), (13, 2), (2, 13), (3, 14), (12, 14), (13, 13)):
        p.px(x, y, "brass", 3)
    p.col(7, 2, 13, "brass", [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2])
    return p.done()


@icon("cast")
def cast_core():
    """Литое ядро: a ball of dark cast iron in the brass cage — plain, heavy, it adds to the golem's health."""
    return core(lambda p: p.disc(7.5, 7.5, 5.6, "iron", levels=(4, 3, 3, 2, 2, 1)))


@icon("fire")
def fire_core():
    """Огненное ядро: a ball of fire held in the brass cage, white at the heart."""
    def f(p):
        p.disc(7.5, 7.5, 5.6, "fire", levels=(4, 3, 3, 2, 1))
        p.disc(6.5, 6.5, 2.0, "lantern", levels=(4, 3))
    return core(f)


@icon("volt")
def volt_core():
    """Грозовое ядро: a ball of the arc's blue in the brass cage, lightning crawling over it."""
    def f(p):
        p.disc(7.5, 7.5, 5.6, "volt", levels=(3, 3, 2, 2, 1))
        p.line([(3, 5), (5, 7), (4, 9), (7, 11)], "volt", 4)
        p.line([(9, 3), (11, 6), (10, 8), (12, 10)], "volt", 4)
    return core(f)


# ---------------------------------------------------------------- the Architect's building forms
@icon("w_tower")
def loophole_tower():
    """Бойницы: a tall narrow stone tower, crenellated, its courses of stone; one long arrow slit down its face and
    a short one high up, a bowman's eye-line."""
    p = Pix()
    body = grid(lambda x, y: (4 <= x <= 11 and 4 <= y <= 14) or (y in (2, 3) and x in (4, 5, 7, 8, 10, 11)))
    p.fill(body, "stone", inner=(3, 2))
    for y in (6, 9, 12):                                       # courses of stone
        for x in range(5, 11):
            p.px(x, y, "stone", 2)
        p.px(6 if y % 2 else 9, y + 1, "stone", 2)
    for y in range(7, 12):
        p.dark(7, y)                                           # the long slit
    p.dark(7, 4)                                               # the short one
    p.dark(8, 4)
    p.rect(3, 14, 12, 14, "stone", [2])                        # its footing
    return p.done()


@icon("w_wall")
def shield_wall():
    """Щит-стена: a wall of tall shields locked edge to edge, spearpoints over the top."""
    p = Pix()
    for k, x0 in enumerate((1, 6, 11)):
        sh = grid(lambda x, y, x0=x0: x0 <= x <= x0 + 4 and 4 <= y <= 13 and not (y == 13 and x in (x0, x0 + 4)))
        p.fill(sh, "wood", inner=(3, 2))
        p.col(x0 + 2, 5, 12, "iron", [3])                      # a band down each
        p.px(x0 + 2, 8, "brass", 4)                            # its boss
    for x in (3, 8, 13):
        p.col(x, 1, 3, "steel", [4, 3, 2])                     # spearpoints over the top
    return p.done()


@icon("w_gate")
def gate_leaves():
    """Створки: a pair of heavy gate leaves under a stone arch, planked, banded with iron, one leaf swinging
    open."""
    p = Pix()
    arch = grid(lambda x, y: 1 <= x <= 14 and 2 <= y <= 14 and not (3 <= x <= 12 and y >= 5 - (abs(x - 7.5) > 3)))
    p.fill(arch, "stone", inner=(3, 2))
    left = grid(lambda x, y: 3 <= x <= 7 and 5 <= y <= 14)
    p.fill(left, "wood", inner=(3, 2))
    right = grid(lambda x, y: 9 <= x <= 12 and 6 <= y <= 14 and y >= 6 + (x - 9) // 2)
    p.fill(right, "wood", inner=(2, 1))
    for y in (7, 12):
        p.rect(3, y, 7, y, "iron", [2])                        # iron bands
        p.rect(9, y + 1, 12, y + 1, "iron", [1])
    p.px(6, 9, "brass", 4)                                     # the ring
    return p.done()


@icon("w_pitch")
def pitch_cauldron():
    """Смоляной котёл: a black cauldron of boiling pitch on a fire, bubbles bursting on top, tipped on its pivot
    to pour."""
    p = Pix()
    flame(p, 5, 14, 3, w=3)
    flame(p, 10, 14, 3, w=3)
    body = grid(lambda x, y: ((x - 7.5) / 6.0) ** 2 + ((y - 6.0) / 6.0) ** 2 <= 1 and y >= 6)
    p.fill(body, "iron", inner=(2, 1), rim=3, shade=1)
    p.rect(1, 5, 14, 6, "iron", [4, 2])                        # the rim
    p.rect(3, 4, 12, 4, "iron", [0])                           # the pitch
    for x, y in ((5, 3), (9, 2), (11, 3)):
        p.px(x, y, "iron", 1)                                  # bubbles
    p.px(9, 3, "iron", 2)
    p.px(0, 7, "brass", 4)                                     # the pivot
    p.px(15, 7, "brass", 3)
    return p.done()


@icon("w_press")
def screw_press():
    """Пресс: a screw press — the heavy frame, the screw down its middle, the bar through its head to turn it,
    the platen crushing down."""
    p = Pix()
    fr = grid(lambda x, y: ((2 <= x <= 3 or 12 <= x <= 13) and 2 <= y <= 14) or (1 <= y <= 2 and 2 <= x <= 13)
              or (13 <= y <= 14 and 1 <= x <= 14))
    p.fill(fr, "wood", inner=(3, 2))
    for y in range(3, 9):
        p.px(7, y, "steel", 4 if y % 2 else 2)                 # the screw
        p.px(8, y, "steel", 3 if y % 2 else 1)
    p.rect(4, 3, 11, 3, "iron", [3])                           # the bar to turn it
    p.rect(4, 9, 11, 10, "iron", [4, 2])                       # the platen
    p.rect(5, 11, 10, 12, "stone", [2, 1])                     # what it crushes
    return p.done()


@icon("w_thunder")
def thunder_tower():
    """Громовая вышка: a lattice mast of iron with a copper ball on top, lightning cracking off it to both sides."""
    p = Pix()
    for y in range(5, 15):
        w = 1 + (y - 5) * 0.4
        for x in (round(7.5 - w), round(7.5 + w)):
            p.px(x, y, "iron", 3 if x < 8 else 2)              # the legs
        if y % 3 == 0:
            p.line([(round(7.5 - w), y), (round(7.5 + w), y)], "iron", 2)   # the cross-ties
    p.disc(7.5, 3.0, 2.2, "copper", levels=(4, 3, 2, 1))
    p.line([(4, 3), (2, 2), (3, 5), (0, 6)], "volt", 4)        # lightning
    p.line([(11, 3), (13, 2), (12, 5), (15, 6)], "volt", 4)
    return p.done()


@icon("w_boom")
def lifting_boom():
    """Подъёмная стрела: a timber boom on a pivot, a counterweight at its short end, a rope over its long end
    hoisting a stone block."""
    p = Pix()
    p.rect(5, 12, 9, 14, "stone", [3, 2, 1])                   # the base
    p.line([(1, 11), (14, 2)], "wood", 3)                      # the boom
    p.line([(1, 12), (14, 3)], "wood", 2)
    p.disc(7.0, 8.0, 1.2, "brass", levels=(4, 2))              # the pivot
    p.rect(0, 11, 2, 13, "iron", [3, 2, 1])                    # the counterweight
    p.col(14, 4, 8, "wood", [4])                               # the rope
    p.rect(12, 9, 15, 11, "stone", [4, 3, 2])                  # the block
    return p.done()


@icon("w_forge")
def field_forge():
    """Полевая кузня: an anvil on a stump, a hammer striking it, sparks off a glowing bar."""
    p = Pix()
    p.rect(5, 11, 10, 14, "wood", [4, 3, 2, 1])                # the stump
    anv = grid(lambda x, y: (2 <= x <= 13 and y == 7) or (4 <= x <= 12 and y == 8) or (6 <= x <= 10 and 9 <= y <= 10)
               or (1 <= x <= 3 and y == 8 and x != 3) or (x == 1 and y == 7))
    p.fill(anv, "iron", inner=(3, 2))
    p.rect(5, 6, 11, 6, "ember", [3])                          # the glowing bar on it
    p.px(7, 6, "fire", 4)
    p.tube(13.0, 1.0, 9.5, 4.5, 0.8, "wood", levels=(4, 3, 2))   # the hammer's haft
    p.rect(7, 3, 10, 4, "iron", [4, 2])                        # its head
    for x, y in ((4, 4), (5, 3), (12, 5), (13, 6)):
        p.px(x, y, "fire", 4 if x in (4, 13) else 3)           # sparks
    return p.done()


# ---------------------------------------------------------------- the Maniac's mad constructs: his purple and green
@icon("c_saw")
def saw_legs():
    """Ноги-пилы: two circular saw blades for feet, spinning, teeth bright, on struts painted the Maniac's purple."""
    p = Pix()
    for cx in (4.5, 11.5):
        p.disc(cx, 10.5, 3.6, "steel", levels=(4, 3, 3, 2))
        for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            p.px(round(cx + np.cos(a) * 4.2), round(10.5 + np.sin(a) * 4.2), "steel", 4)   # teeth
        p.disc(cx, 10.5, 1.0, "mad", levels=(4, 2))            # the hub
    p.line([(4, 7), (7, 3)], "iron", 3)                        # the struts
    p.line([(11, 7), (8, 3)], "iron", 2)
    p.rect(5, 1, 10, 3, "mad", [4, 3, 2])                      # the hip, the Maniac's purple
    return p.done()


def catapult(p, payload):
    """A mangonel side on: a wheeled timber bed, an A-frame with its crossbar, the long arm flung back against it
    from the axle at the bed's end, the cup at its tip — payload draws what is in the cup."""
    p.rect(1, 11, 13, 12, "wood", [3, 2])                      # the bed
    for cx in (3.0, 11.0):
        p.disc(cx, 13.0, 1.6, "wood", levels=(4, 2, 1), hole=0.4)   # wheels
    p.line([(7, 11), (8, 6)], "wood", 2)                       # the A-frame
    p.line([(10, 11), (9, 6)], "wood", 1)
    p.rect(7, 6, 10, 6, "madg", [3])                           # the crossbar, the Maniac's green
    p.line([(3, 10), (11, 4)], "wood", 4)                      # the arm
    p.line([(3, 11), (11, 5)], "wood", 2)
    p.disc(3.0, 10.5, 1.0, "mad", levels=(4, 2))               # the axle
    p.rect(11, 3, 13, 4, "iron", [3, 2])                       # the cup
    payload(p)


@icon("c_catapult")
def head_catapult():
    """Голова-катапульта: a mangonel loaded with a golem's own head — round, iron, its eye glowing — ready to throw."""
    p = Pix()
    def head(p):
        p.disc(12.5, 1.6, 1.9, "iron", levels=(4, 3, 2))
        p.px(13, 1, "red", 4)                                  # its eye
    catapult(p, head)
    return p.done()


@icon("c_fist")
def spring_fist():
    """Кулак на пружине: a boxing-glove fist on a long coiled spring, shooting out of a purple box."""
    p = Pix()
    box = grid(lambda x, y: 0 <= x <= 3 and 5 <= y <= 11)
    p.fill(box, "mad", inner=(3, 2))
    for x in range(4, 10):
        p.px(x, 6 + (x % 2) * 4, "steel", 4)                   # the spring's coils
        p.px(x, 7 + (x % 2) * 2, "steel", 2)
        p.px(x, 8, "steel", 3 if x % 2 else 1)
    glove = grid(lambda x, y: ((x - 12.0) / 3.2) ** 2 + ((y - 8.0) / 3.8) ** 2 <= 1)
    p.fill(glove, "red", inner=(3, 2))
    p.rect(10, 11, 11, 12, "red", [2, 1])                      # the thumb
    p.px(11, 6, "red", 4)
    return p.done()


@icon("c_triple")
def three_arms():
    """Рука-рука-рука: three iron arms out of one purple shoulder — one reaching up, one straight out, one down —
    each bent at a purple elbow, each with its three-fingered grip."""
    p = Pix()
    p.disc(3.0, 8.0, 2.6, "mad", levels=(4, 3, 2, 1))          # the shoulder
    for (elx, ely, hx, hy) in ((6, 3, 11, 1), (8, 8, 12, 7), (6, 13, 11, 14)):
        p.line([(4, 8), (elx, ely)], "iron", 3)                # upper arm
        p.px(elx, ely, "mad", 4)                               # elbow
        p.line([(elx, ely), (hx - 1, hy)], "iron", 2)          # forearm
        p.px(hx, hy, "steel", 4)                               # the grip's fingers
        p.px(hx + 1, hy - 1 if hy > 0 else hy, "steel", 3)
        p.px(hx + 1, hy + 1 if hy < 15 else hy, "steel", 3)
    return p.done()


@icon("c_upside")
def upside_down():
    """Вверх ногами: a little golem standing on its head — legs kicking up, arms planted, a green eye glowing the
    wrong way up; two arrows going round it."""
    p = Pix()
    p.rect(5, 1, 6, 4, "iron", [3])                            # its legs, up
    p.rect(9, 1, 10, 4, "iron", [2])
    body = grid(lambda x, y: 4 <= x <= 11 and 5 <= y <= 10)
    p.fill(body, "mad", inner=(3, 2))
    p.rect(5, 11, 10, 13, "iron", [3, 2, 1])                   # its head, on the ground
    p.px(8, 12, "madg", 4)                                     # its eye
    p.line([(3, 11), (3, 13)], "iron", 3)                      # arms, planted
    p.line([(12, 11), (12, 13)], "iron", 2)
    p.line([(1, 5), (1, 2), (3, 0)], "madg", 4)                # arrows going round
    p.line([(14, 9), (14, 12), (12, 14)], "madg", 4)
    return p.done()


@icon("c_burning")
def burning_catapult():
    """Пылающая катапульта: a mangonel with a ball of burning pitch in its cup, flames streaming off it."""
    p = Pix()
    def fire(p):
        p.disc(12.5, 1.8, 1.9, "fire", levels=(4, 3, 2))
        for x, y, lv in ((10, 1, 3), (9, 2, 2), (11, 0, 2), (14, 0, 3)):
            p.px(x, y, "fire", lv)
    catapult(p, fire)
    return p.done()


@icon("c_salute")
def salute():
    """Салют: a firework rocket's burst — a star of sparks in the Maniac's purple and green round a white heart,
    the rocket's trail rising to it."""
    p = Pix()
    p.line([(3, 15), (5, 12), (7, 9)], "fire", 2)              # the trail
    cx, cy = 9, 6
    for k, a in enumerate(np.linspace(0, 2 * np.pi, 8, endpoint=False)):
        ramp = "mad" if k % 2 else "madg"
        for rr, lv in ((2, 4), (3.5, 3), (5, 2)):
            p.px(round(cx + np.cos(a) * rr), round(cy + np.sin(a) * rr), ramp, lv)
    p.px(cx, cy, "lantern", 4)
    return p.done()


# ---------------------------------------------------------------- the Inventor's augments
@icon("a_coil")
def storm_coil():
    """Грозовая катушка: a copper coil laid along a forearm's iron bracer, a brass ball at each end, lightning
    arcing between the balls over it."""
    p = Pix()
    br = grid(lambda x, y: 2 <= x <= 13 and 10 <= y <= 13)
    p.fill(br, "iron", inner=(3, 2))
    for x in (3, 12):
        p.px(x, 11, "brass", 4)                                # buckles
    for x in range(4, 12):
        p.col(x, 7, 9, "copper", [4, 3, 1] if x % 2 else [3, 2, 1])   # the coil's turns
    for cx in (3.0, 12.5):
        p.disc(cx, 6.5, 1.4, "brass", levels=(4, 3, 2))        # the terminals
    p.line([(4, 5), (6, 3), (8, 4), (10, 2), (11, 5)], "volt", 4)   # the arc between them
    for x, y in ((6, 4), (8, 5), (10, 3)):
        p.px(x, y, "volt", 2)
    return p.done()


@icon("a_mirror")
def reflector():
    """Отражатель: a round polished mirror on a bracket, a bolt of light striking it and bouncing back off."""
    p = Pix()
    p.rect(1, 7, 3, 9, "iron", [3, 2, 1])                      # the bracket
    p.disc(6.5, 8.0, 4.4, "brass", levels=(4, 3, 2))           # the rim
    p.disc(6.5, 8.0, 3.2, "steel", levels=(4, 4, 3, 2))        # the glass
    p.px(5, 6, "lantern", 4)
    p.line([(15, 2), (10, 6)], "volt", 4)                      # coming in
    p.line([(10, 8), (15, 13)], "volt", 3)                     # going back out
    p.px(11, 7, "lantern", 4)
    return p.done()


@icon("a_spring")
def spring_dash():
    """Пружинный рывок: a heavy coiled spring let go — the coils stretched out to the right, speed lines behind."""
    p = Pix()
    for k in range(5):
        x0 = 3 + k * 2
        p.line([(x0, 4), (x0 + 2, 12)], "steel", 4 if k % 2 == 0 else 3)
        p.line([(x0 + 1, 4), (x0 + 3, 12)], "steel", 2)
    p.rect(1, 3, 3, 13, "iron", [4, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1])   # the base it pushes off
    p.rect(13, 3, 14, 13, "brass", [4, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1])   # the plate it drives
    return p.done()


# ---------------------------------------------------------------- the Colossus's own colossal modules
@icon("col_battery")
def col_battery():
    """Плечевая батарея: a riveted box of six rocket tubes, red warheads in their mouths, a brass band."""
    p = Pix()
    p.fill(grid(lambda x, y: 1 <= x <= 14 and 3 <= y <= 12), "iron", inner=(3, 2))
    p.col(7, 3, 12, "brass", [4, 3, 3, 3, 3, 3, 3, 3, 2, 2])
    for cx in (3, 5, 10, 12):
        for cy in (5, 9):
            if (cx in (5, 10)):
                continue
    for cx, cy in ((3, 5), (5, 5), (10, 5), (12, 5), (3, 9), (5, 9), (10, 9), (12, 9)):
        p.dark(cx, cy)
    for cx, cy in ((3, 6), (5, 6), (10, 6), (12, 6), (3, 10), (5, 10), (10, 10), (12, 10)):
        p.px(cx, cy, "red", 4)
    p.rect(5, 13, 10, 14, "iron", [2, 1])                    # the bracket
    return p.done()


@icon("col_reactor")
def col_reactor():
    """Реактор с трубами: a round reactor glowing through its grille, two exhaust pipes standing up from it,
    heat shimmering off their mouths."""
    p = Pix()
    p.disc(7.5, 10.0, 4.8, "iron", levels=(4, 3, 2, 2, 1))
    p.disc(7.5, 10.0, 2.8, "fire", levels=(4, 4, 3, 2))
    for x in (6, 8):
        p.col(x, 8, 12, "iron", [1])                         # the grille
    for x0 in (3, 11):
        p.rect(x0, 1, x0 + 1, 6, "steel", [4, 3, 3, 3, 2, 2])  # the pipes
        p.px(x0, 0, "fire", 3)
        p.px(x0 + 1, 0, "fire", 2)
    return p.done()


@icon("col_rail")
def col_rail():
    """Рельсотрон: two long copper rails side by side with blue coils between them, a bolt of light along them."""
    p = Pix()
    p.line([(1, 10), (13, 3)], "copper", 4)                  # the rails
    p.line([(2, 12), (14, 5)], "copper", 2)
    for k in range(3):
        x, y = 4 + k * 3, 10 - k * 2
        p.rect(x, y, x + 1, y + 1, "volt", [3, 2])          # coils
    p.line([(3, 11), (15, 4)], "volt", 4)                    # the bolt
    p.px(15, 3, "lantern", 4)
    p.rect(0, 11, 2, 14, "iron", [3, 2, 1])                  # the breech
    return p.done()


@icon("col_scoop")
def col_scoop():
    """Ковш-дробилка: a toothed iron bucket on a hydraulic arm, crushing a lump of rock in its jaws."""
    p = Pix()
    p.line([(1, 14), (5, 8)], "iron", 3)                     # the arm
    p.rect(2, 11, 3, 12, "brass", [4, 3])                    # the piston's collar
    bucket = grid(lambda x, y: 5 <= x <= 13 and 4 <= y <= 11 and (x - 5) + (11 - y) >= 2)
    p.fill(bucket, "iron", inner=(3, 2))
    for x in (6, 8, 10, 12):
        p.px(x, 3, "steel", 4)                               # teeth
    p.rect(8, 6, 11, 8, "stone", [3, 2, 1])                  # the rock in its jaws
    p.px(14, 9, "stone", 3)
    p.px(15, 11, "stone", 2)
    return p.done()


# ---------------------------------------------------------------- artifacts: always passive, the army's
ART = {}


def art(key):
    def reg(f):
        ART[key] = f
        return f
    return reg


@art("banner")
def banner():
    """Знамя двух ветров: a pole with a swallow-tailed banner, half red half blue, streaming."""
    p = Pix()
    p.col(3, 1, 14, "wood", [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 1])
    p.px(3, 0, "brass", 4)
    for y in range(2, 10):
        x1 = 13 - (abs(y - 6) if y >= 6 else 0)
        for x in range(4, x1 + 1):
            p.px(x, y, "red" if y < 6 else "blue", 3 if x < 9 else 2)
    p.px(13, 7, "blue", 1)
    return p.done()


@art("boots")
def boots():
    """Сапоги преследователя: a tall leather boot with a brass spur and wind lines behind it."""
    p = Pix()
    p.fill(grid(lambda x, y: (5 <= x <= 9 and 2 <= y <= 11) or (5 <= x <= 13 and 10 <= y <= 13)), "wood", inner=(3, 2))
    p.rect(5, 13, 13, 13, "wood", [1])
    p.rect(5, 2, 9, 3, "wood", [4, 3])
    p.px(4, 12, "brass", 4)
    p.px(3, 12, "brass", 3)
    for y in (5, 8, 11):
        p.line([(0, y), (2, y)], "steel", 2)
    return p.done()


@art("chalice")
def chalice():
    """Кровавая чаша: a golden goblet brimming red, a drop running down its bowl."""
    p = Pix()
    bowl = grid(lambda x, y: 3 <= y <= 7 and abs(x - 7.5) <= 5 - (y - 3) * 0.6)
    p.fill(bowl, "brass", inner=(3, 2))
    p.rect(3, 2, 12, 2, "crimson", [3])
    p.px(5, 4, "crimson", 4)
    p.px(5, 5, "crimson", 3)
    p.col(7, 8, 11, "brass", [3, 2, 2, 2])
    p.col(8, 8, 11, "brass", [2, 1, 1, 1])
    p.rect(4, 12, 11, 13, "brass", [4, 2])
    return p.done()


@art("anvil")
def heavy_anvil():
    """Тяжёлая наковальня: a squat black anvil, its horn to the left, a dent in its face."""
    p = Pix()
    p.fill(grid(lambda x, y: (y in (4, 5) and 1 <= x <= 14 and (x >= 4 or y == 5)) or (6 <= y <= 8 and 5 <= x <= 11)
                or (9 <= y <= 12 and 3 <= x <= 13)), "iron", inner=(3, 2))
    p.rect(4, 4, 14, 4, "steel", [4])
    p.px(9, 4, "iron", 1)
    p.rect(2, 13, 14, 13, "iron", [1])
    return p.done()


@art("bell")
def alarm_bell():
    """Колокол тревоги: a bronze bell swinging, its clapper out, the ringing in arcs."""
    p = Pix()
    bell = grid(lambda x, y: 3 <= y <= 11 and abs(x - 7.5) <= 2 + (y - 3) * 0.5)
    p.fill(bell, "copper", inner=(3, 2))
    p.rect(3, 11, 12, 12, "copper", [4, 2])
    p.rect(7, 1, 8, 2, "iron", [3, 2])
    p.px(9, 13, "iron", 3)
    for x, y in ((1, 5), (0, 7), (14, 5), (15, 7), (1, 9), (14, 9)):
        p.px(x, y, "brass", 3)
    return p.done()


@art("dice")
def cut_dice():
    """Гранёные кости: two dice of polished bone, their pips sharp."""
    p = Pix()
    p.fill(grid(lambda x, y: 1 <= x <= 7 and 6 <= y <= 12), "bone", inner=(4, 3))
    p.fill(grid(lambda x, y: 8 <= x <= 14 and 2 <= y <= 8), "bone", inner=(4, 3))
    for x, y in ((3, 8), (5, 10), (4, 9), (10, 4), (12, 6), (10, 6), (12, 4)):
        p.px(x, y, "chitin", 1)
    return p.done()


@art("hourglass")
def hourglass():
    """Песочные часы: a brass-framed hourglass, the sand half run through."""
    p = Pix()
    p.rect(3, 1, 12, 2, "brass", [4, 2])
    p.rect(3, 13, 12, 14, "brass", [4, 2])
    glass = grid(lambda x, y: 3 <= y <= 12 and abs(x - 7.5) <= 0.6 + abs(y - 7.5) * 0.8)
    p.fill(glass, "steel", inner=(4, 3), rim=4, shade=2)
    for y in range(9, 13):
        for x in range(16):
            if glass[y, x] and abs(x - 7.5) <= (y - 8) * 0.8:
                p.px(x, y, "amber", 3)
    p.px(7, 8, "amber", 4)
    for y in range(4, 6):
        for x in range(16):
            if glass[y, x]:
                p.px(x, y, "amber", 2)
    return p.done()


@art("fog_lantern")
def fog_lantern():
    """Туманный фонарь: a lantern glowing pale through a curl of fog."""
    p = Pix()
    p.rect(6, 1, 9, 2, "iron", [3, 2])
    p.fill(grid(lambda x, y: 4 <= x <= 11 and 3 <= y <= 11), "iron", inner=(2, 2), rim=3)
    p.rect(5, 4, 10, 10, "lantern", [4, 4, 3, 3, 3, 2, 2])
    p.rect(4, 12, 11, 12, "iron", [2])
    for x, y in ((0, 9), (1, 8), (2, 9), (13, 6), (14, 5), (15, 6), (1, 13), (14, 12)):
        p.px(x, y, "slate", 3)
    return p.done()


# ---------------------------------------------------------------- small icons for the interface itself (settings)
UI = {}


def ui(key):
    def reg(f):
        UI[key] = f
        return f
    return reg


@ui("screen")
def ui_screen():
    """A monitor: an iron frame, a dark glass with a glint, a foot."""
    p = Pix()
    p.fill(grid(lambda x, y: 1 <= x <= 14 and 2 <= y <= 11), "iron", inner=(3, 2))
    p.rect(3, 4, 12, 9, "volt", [2, 1, 1, 1, 1, 0])
    p.px(4, 5, "volt", 4)
    p.px(5, 5, "volt", 3)
    p.rect(6, 12, 9, 13, "iron", [3, 2])
    p.rect(4, 14, 11, 14, "iron", [2])
    return p.done()


@ui("sound")
def ui_sound():
    """A brass horn speaker, its sound in arcs."""
    p = Pix()
    p.rect(2, 6, 4, 10, "iron", [3, 3, 2, 2, 1])
    horn = grid(lambda x, y: 5 <= x <= 9 and abs(y - 8) <= 2 + (x - 5) * 0.9)
    p.fill(horn, "brass", inner=(3, 2))
    for x, ys in ((11, (6, 7, 8, 9, 10)), (13, (4, 5, 8, 11, 12))):
        for y in ys:
            p.px(x, y, "steel", 3 if x == 11 else 2)
    return p.done()


@ui("game")
def ui_game():
    """A cog with a brass hub."""
    p = Pix()
    for k in range(8):
        a = k * np.pi / 4
        p.rect(round(7 + np.cos(a) * 5.5), round(7 + np.sin(a) * 5.5), round(8 + np.cos(a) * 5.5), round(8 + np.sin(a) * 5.5), "steel", [3])
    p.disc(7.5, 7.5, 5.0, "steel", levels=(4, 3, 3, 2), hole=0.0)
    p.disc(7.5, 7.5, 2.0, "brass", levels=(4, 3), hole=0.8)
    return p.done()


@ui("keys")
def ui_keys():
    """A key of the keyboard, its letter worn."""
    p = Pix()
    p.fill(grid(lambda x, y: 1 <= x <= 14 and 3 <= y <= 13), "iron", inner=(2, 2), rim=3, shade=1)
    p.fill(grid(lambda x, y: 3 <= x <= 12 and 4 <= y <= 10), "slate", inner=(3, 3), rim=4, shade=2)
    p.line([(6, 6), (6, 9), (9, 9)], "iron", 1)
    return p.done()


NAMES = {**{k: IC.ICONS[k][1] for k in IC.ICONS}, "col_battery": "Плечевая батарея", "col_reactor": "Реактор с трубами",
         "col_rail": "Рельсотрон", "col_scoop": "Ковш-дробилка"}


def review(keys, fname, title):
    """A batch: each icon old and new, large (×5) and in a workshop cell (×2)."""
    import foundry_ui as FU
    from swarm_ui import letters
    from paths import out
    per = 3
    rows = (len(keys) + per - 1) // per
    W, H = 960, 60 + rows * 196
    sc = FU.forge(W, H, 9)
    FU.wing(sc, 0, 0, W, 44)
    letters(sc, title, W // 2, 8, "title", 24, col=(232, 222, 206), col2=(120, 96, 70), align="center")
    FU.plate(sc, 8, 50, W - 8, H - 6, seed=5)
    for i, k in enumerate(keys):
        x0, y0 = 22 + (i % per) * 312, 58 + (i // per) * 196
        letters(sc, NAMES[k], x0 + 140, y0, "text", 16, col=(240, 200, 120), align="center")
        for j, rgba in enumerate((IC.icon_rgba(k), NEW[k]())):
            bx = x0 + j * 150
            big = np.repeat(np.repeat(rgba, 6, 0), 6, 1)
            m = big[..., 3] > 0
            sc.rgb[y0 + 22:y0 + 118, bx + 20:bx + 116][m] = big[..., :3][m]
            FU.cell(sc, bx + 44, y0 + 128, bx + 92, y0 + 176, "normal")
            sm = np.repeat(np.repeat(rgba, 2, 0), 2, 1)
            m = sm[..., 3] > 0
            sc.rgb[y0 + 136:y0 + 168, bx + 52:bx + 84][m] = sm[..., :3][m]
    img = sc.image(2)
    img.save(out(fname))
    print(fname, img.size)


def sheet():
    """Old and new side by side: large (×6), at the size they are drawn in the workshop (×2 in a cell), and at
    their own size."""
    from PIL import Image
    import foundry_ui as FU
    from swarm_ui import letters
    from paths import out
    W, H = 960, 330
    sc = FU.forge(W, H, 7)
    FU.wing(sc, 0, 0, W, 44)
    letters(sc, "ИКОНКИ: СТАРЫЕ И НОВЫЕ", W // 2, 8, "title", 24, col=(232, 222, 206), col2=(120, 96, 70),
            align="center")
    FU.plate(sc, 12, 52, W - 12, H - 10, seed=5)
    keys = ["long", "mortar", "chain", "plates"]        # the first four, against the dataset's icons they replaced
    for i, k in enumerate(keys):
        x0 = 30 + i * 230
        letters(sc, NAMES[k], x0 + 100, 62, "text", 16, col=(240, 200, 120), align="center")
        for j, (lab, rgba) in enumerate((("было", IC.icon_rgba(k)), ("стало", NEW[k]()))):
            bx = x0 + j * 104
            letters(sc, lab, bx + 48, 86, "text", 16, col=(150, 142, 128), align="center")
            big = np.repeat(np.repeat(rgba, 6, 0), 6, 1)
            m = big[..., 3] > 0
            sc.rgb[108:204, bx:bx + 96][m] = big[..., :3][m]
            FU.cell(sc, bx + 24, 216, bx + 72, 264, "normal")
            sm = np.repeat(np.repeat(rgba, 2, 0), 2, 1)
            m = sm[..., 3] > 0
            sc.rgb[224:256, bx + 32:bx + 64][m] = sm[..., :3][m]
            m = rgba[..., 3] > 0
            sc.rgb[276:292, bx + 40:bx + 56][m] = rgba[..., :3][m]
    img = sc.image(2)
    img.save(out("icons_redraw.png"))
    print("icons_redraw.png", img.size)


EXTRA_NAMES = {"col_battery": "Плечевая батарея", "col_reactor": "Реактор с трубами", "col_rail": "Рельсотрон",
               "col_scoop": "Ковш-дробилка"}


def atlas():
    """The module icons' atlas for the game and the screens, from the drawn icons: the same cells and keys as
    before (assets/module_icons.png, .json), so everything that draws an icon by its key gets the new one."""
    import json, os
    from PIL import Image
    idx_path, png_path = IC.INDEX, IC.ASSET
    old = json.load(open(idx_path))["icons"]
    W = 1 + max(v["cell"][0] for v in old.values())
    H = 1 + max(v["cell"][1] for v in old.values())
    sheet = np.zeros((H * 16, W * 16, 4), np.uint8)
    index = {}
    for k, v in old.items():
        cx, cy = v["cell"]
        sheet[cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16] = NEW[k]()
        index[k] = dict(cell=[cx, cy], name=v["name"], owner=v["owner"])
    used = {tuple(v["cell"]) for v in index.values()}
    free = [(x, y) for y in range(H) for x in range(W) if (x, y) not in used]
    for k in NEW:                                           # icons drawn since: into the free cells
        if k in index:
            continue
        if not free:
            sheet = np.concatenate([sheet, np.zeros((16, W * 16, 4), np.uint8)])
            free = [(x, H) for x in range(W)]
            H += 1
        cx, cy = free.pop(0)
        sheet[cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16] = NEW[k]()
        index[k] = dict(cell=[cx, cy], name=EXTRA_NAMES.get(k, k), owner="Колосс" if k.startswith("col_") else "")
    Image.fromarray(sheet, "RGBA").save(png_path)
    json.dump(dict(source="drawn in code, pixel by pixel: tools/sprites/icons_drawn.py", icons=index),
              open(idx_path, "w"), ensure_ascii=False, indent=1)
    IC._cache.pop("module", None)
    print("module_icons.png", len(index), "icons")


def contact():
    """All the module icons on one sheet, a row for each owner, ×3 — for a look."""
    import foundry_ui as FU
    from swarm_ui import letters
    from paths import out
    owners = {}
    for k, v in IC.ICONS.items():
        owners.setdefault(v[2], []).append(k)
    W, H = 960, 62 + len(owners) * 58
    sc = FU.forge(W, H, 11)
    FU.wing(sc, 0, 0, W, 44)
    letters(sc, "ИКОНКИ МОДУЛЕЙ", W // 2, 8, "title", 24, col=(232, 222, 206), col2=(120, 96, 70), align="center")
    FU.plate(sc, 8, 50, W - 8, H - 6, seed=5)
    for r, (o, keys) in enumerate(owners.items()):
        y = 58 + r * 58
        letters(sc, o, 22, y + 16, "text", 16, col=(240, 200, 120))
        for j, k in enumerate(keys):
            big = np.repeat(np.repeat(NEW[k](), 3, 0), 3, 1)
            m = big[..., 3] > 0
            bx = 140 + j * 56
            sc.rgb[y + 2:y + 50, bx:bx + 48][m] = big[..., :3][m]
    img = sc.image(2)
    img.save(out("icons_modules.png"))
    print("icons_modules.png", img.size)


BATCHES = {"guard": ["tower", "intercept", "anchor", "plates", "counter", "hot"],
           "sage": ["chain", "ground", "overload", "fireball", "firewall", "blades"],
           "forge": ["magnet", "rod", "smoke", "whistle", "maw", "greedy"],
           "gun": ["mortar", "long", "spider", "canister", "hotshot", "bomb"],
           "mechanic": ["repair", "crane", "spares", "oiler", "welding", "oiltank"],
           "rare1": ["torch", "nozzles", "bounce", "whirl", "grapple", "mill"],
           "rare2": ["dome", "bombcore", "ram", "buffer", "spark", "poker"],
           "rare3": ["tracks", "flail", "cast", "fire", "volt", "mill"],
           "architect": ["w_tower", "w_wall", "w_gate", "w_pitch", "w_press", "w_thunder"],
           "maniac": ["w_boom", "w_forge", "c_saw", "c_catapult", "c_fist", "c_triple"],
           "colossal": ["col_battery", "col_reactor", "col_rail", "col_scoop", "plates", "flail"],
           "inventor": ["c_upside", "c_burning", "c_salute", "a_coil", "a_mirror", "a_spring"]}

if __name__ == "__main__":
    import sys
    what = sys.argv[1] if len(sys.argv) > 1 else "sheet"
    if what == "sheet":
        sheet()
    elif what == "atlas":
        atlas()
    elif what == "contact":
        contact()
    else:
        review(BATCHES[what], f"icons_{what}.png", "ИКОНКИ: " + what.upper())
