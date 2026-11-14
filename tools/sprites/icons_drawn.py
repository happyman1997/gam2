"""Module icons drawn by hand in code, pixel by pixel — no source image under them. Each icon is 16×16: its parts
laid in as blocks and single pixels, every one with its tone picked from our ramps (icons.R), the light from the
top left; then our dark outline round the whole shape, outside it. The way to replace the icons made from the
Pixel Art Atlas dataset (its sprites are AI-generated, see docs/STEAM.md) — drawn from what each module is,
not traced from the old icon.

    python3 tools/sprites/icons_drawn.py   -> out/icons_redraw.png (the old icon and the new one, large and in a cell)
"""
import numpy as np
from kit import hexc
import icons as IC

OUTLINE = hexc("#08060c")


class Pix:
    """A 16×16 icon being drawn: colours or nothing; the outline goes on last, round what is there."""

    def __init__(self):
        self.c = np.zeros((16, 16, 3))
        self.a = np.zeros((16, 16), bool)
        self.hole = np.zeros((16, 16), bool)          # drawn as outline colour inside the shape (a bore, a slot)

    def px(self, x, y, ramp, lv):
        if 0 <= x < 16 and 0 <= y < 16:
            self.c[y, x] = IC.R[ramp][lv]
            self.a[y, x] = True
            self.hole[y, x] = False

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
NAMES = {"long": "Длинный ствол", "mortar": "Мортира", "chain": "Цепная молния", "plates": "Броневые листы"}


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
    keys = list(NEW)
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


if __name__ == "__main__":
    sheet()
