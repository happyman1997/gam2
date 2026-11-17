"""Golems drawn by hand in code, pixel by pixel, at their size on the field — no 3D render under them. The way the
module icons are drawn (icons_drawn.py), on a canvas the size of a body: each part laid in as a shape with its tone
picked from our ramps, the light from the top left (a lit rim on the top and left edges, shade on the bottom and
right), round things shaded by how far they face the light; a few pixels placed one by one where a shape needs them;
then our dark outline round the whole figure, outside it.

A sample first, to compare with the render: the Sage.

    python3 tools/sprites/golems_drawn.py sample   -> out/golem_drawn_sample.png (the render and the drawing side by side)
"""
import numpy as np
from kit import hexc, ramp
import icons as IC

OUTLINE = hexc("#0c0a10")
RAMPS = dict(IC.R)
RAMPS["porcelain"] = ramp("#3a3640", "#6e6874", "#a8a2a8", "#d8d2ca", "#f6f2e8")   # old porcelain, warm in the light
RAMPS["copper_dark"] = ramp("#1e0e08", "#44200e", "#6c3a1c", "#985e34", "#c08454")   # copper gone brown with age
RAMPS["verdigris"] = ramp("#14282a", "#24463e", "#3e6e5a", "#5e9878", "#8cc4a0")      # the green of old copper


class Canvas:
    """A body being drawn: colours or nothing; the outline goes on last, round what is there."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.c = np.zeros((h, w, 3))
        self.a = np.zeros((h, w), bool)
        self.hole = np.zeros((h, w), bool)
        self.yy, self.xx = np.mgrid[0:h, 0:w]

    def px(self, x, y, rmp, lv):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.c[y, x] = RAMPS[rmp][int(max(0, min(4, lv)))]
            self.a[y, x] = True
            self.hole[y, x] = False

    def fill(self, mask, rmp, inner=(3, 2), rim=4, shade=1, split=0.0):
        """A shape, bevelled: its top and left edge catch the light, its bottom and right edge are in shade, the
        inside goes from inner[0] at the top left to inner[1] at the bottom right."""
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
                lv = rim if (not up and not lf) or t < 0.75 else inner[1]
            elif not dn or not rt:
                lv = shade
            else:
                lv = inner[0] if t < 0.5 + split else inner[1]
            self.px(x, y, rmp, lv)

    def box(self, x0, y0, x1, y1, rmp, **kw):
        self.fill((self.xx >= x0) & (self.xx <= x1) & (self.yy >= y0) & (self.yy <= y1), rmp, **kw)

    def oval(self, cx, cy, rx, ry, rmp, **kw):
        self.fill(((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2 <= 1.0, rmp, **kw)

    def poly(self, pts, rmp, **kw):
        """A filled polygon (even-odd), bevelled like fill."""
        x, y = self.xx + 0.5, self.yy + 0.5
        inside = np.zeros_like(self.a)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            cross = ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-9) + x0)
            inside ^= cross
        self.fill(inside, rmp, **kw)

    def sphere(self, pts, rmp, cx, cy, rx, ry):
        """A rounded mass inside a polygon: the tone by how far round it faces the top left (light on the upper
        left, a broad shade on the lower right), the outermost pixels on the shaded side darkest."""
        x, y = self.xx + 0.5, self.yy + 0.5
        inside = np.zeros_like(self.a)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            inside ^= ((y0 > y) != (y1 > y)) & (x < (x1 - x0) * (y - y0) / (y1 - y0 + 1e-9) + x0)
        pm = np.pad(inside, 1)
        for yy, xx in zip(*np.nonzero(inside)):
            nx, ny = (xx - cx) / rx, (yy - cy) / ry
            f = (nx * 0.7 + ny * 0.8) / 1.06 + 0.25 * (nx * nx + ny * ny)
            lv = 4 if f < -0.5 else 3 if f < -0.02 else 2 if f < 0.32 else 1      # clear steps, not a ramp
            if not pm[yy + 2, xx + 1] or not pm[yy + 1, xx + 2]:
                lv = min(lv, 1)                                       # the shaded edge
            elif (not pm[yy, xx + 1] or not pm[yy + 1, xx]) and f < 0.1:
                lv = 4                                                # the lit rim
            self.px(xx, yy, rmp, lv)

    def disc(self, cx, cy, r, rmp, levels=(4, 3, 2, 1)):
        """A round thing lit from the top left: the tone by how far round it faces the light."""
        d = np.hypot(self.xx - cx, self.yy - cy)
        for y, x in zip(*np.nonzero(d <= r)):
            f = ((x - cx) + (y - cy)) / max(r, 0.5) / 1.414
            k = int(np.clip((f + 1) / 2 * len(levels), 0, len(levels) - 1))
            self.px(x, y, rmp, levels[k])

    def tube(self, ax, ay, bx, by, r, rmp, levels=(4, 3, 2, 1)):
        """A round bar from a to b, lit along the side that faces the top left."""
        L = max(np.hypot(bx - ax, by - ay), 0.01)
        ux, uy = (bx - ax) / L, (by - ay) / L
        sgn = 1 if (uy - ux) < 0 else -1
        dx, dy = self.xx - ax, self.yy - ay
        t, n = dx * ux + dy * uy, (-dx * uy + dy * ux) * sgn
        for y, x in zip(*np.nonzero((t >= -0.5) & (t <= L + 0.5) & (np.abs(n) <= r))):
            k = int(np.clip((n[y, x] / r + 1) / 2 * len(levels), 0, len(levels) - 1))
            self.px(x, y, rmp, levels[k])

    def line(self, pts, rmp, lv):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(abs(x1 - x0), abs(y1 - y0), 1)
            for t in range(n + 1):
                self.px(x0 + (x1 - x0) * t / n, y0 + (y1 - y0) * t / n, rmp, lv)

    def dark(self, x, y):
        """A gap into the body: the outline's colour inside the shape (a seam, a slot)."""
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = True
            self.hole[y, x] = True

    def done(self):
        """RGBA: the body, its seams, and the dark outline round it (outside, four-way)."""
        a = self.a
        p = np.pad(a, 1)
        ring = ~a & (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:])
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., :3] = np.clip(self.c, 0, 255)
        out[self.hole, :3] = OUTLINE
        out[ring, :3] = OUTLINE
        out[..., 3] = (a | ring) * 255
        return out


def sage():
    """Мудрец, the Foundry's mage: a heavy copper boiler gone brown and green with age on iron legs, a stack of
    porcelain insulators rising from its back with a cable to the staff, a helmet thrust forward with a glowing
    slit, the staff with its charged ball in the far hand. Faces right; the ground point at (20, 56)."""
    g = Canvas(44, 60)
    C = "copper_dark"
    # the staff, behind the body: an iron pole with brass rings, the ball in brass claws
    g.line([(6, 9), (6, 55)], "iron", 3)
    g.line([(7, 9), (7, 55)], "iron", 1)
    for y in (21, 33, 45):
        g.line([(5, y), (8, y)], "brass", 3)
        g.px(8, y, "brass", 1)
    for (x, y, lv) in ((4, 8, 3), (9, 8, 2), (3, 6, 3), (10, 6, 1), (4, 3, 2), (9, 3, 1)):
        g.px(x, y, "brass", lv)
    g.disc(6.5, 5.0, 3.1, "volt", levels=(4, 4, 3, 2))
    g.px(5, 4, "volt", 4)
    # the far leg, in the body's shadow
    g.poly([(13, 35), (19, 35), (18, 44), (13, 44)], "iron", inner=(1, 1), rim=2, shade=0)
    g.disc(15.5, 45, 2.2, C, levels=(2, 1, 1, 0))
    g.poly([(12, 47), (18, 47), (17, 53), (12, 53)], "iron", inner=(1, 1), rim=2, shade=0)
    g.poly([(10, 53), (18, 53), (19, 56), (10, 56)], "iron", inner=(1, 0), rim=1, shade=0)
    # the far arm, down to the staff
    g.tube(12, 18, 9, 26, 1.8, C, levels=(2, 2, 1, 0))
    g.disc(7.5, 27.5, 2.3, "iron", levels=(3, 2, 1, 1))
    # the insulator stack on an iron pipe, a cable from its top to the staff's ball
    g.line([(16, 15), (16, 4)], "iron", 1)
    for y in (13, 10, 7):
        g.oval(16, y, 2.8, 1.5, "porcelain", inner=(3, 2), rim=4, shade=1)
        g.line([(14, y + 1), (18, y + 1)], "porcelain", 0)
    g.box(15, 2, 17, 4, "iron", inner=(2, 2), rim=3, shade=1)
    g.line([(14, 3), (12, 2), (10, 3)], "iron", 1)                          # the cable, sagging to the claws
    # the hips: an iron belt, two hanging plates
    g.box(13, 31, 28, 34, "iron", inner=(2, 1), rim=3, shade=0)
    g.poly([(14, 34), (20, 34), (19, 38), (15, 38)], C, inner=(2, 1), rim=3, shade=0)
    g.poly([(21, 34), (27, 34), (26, 38), (22, 38)], C, inner=(3, 2), rim=4, shade=1)
    # the boiler: a barrel, round in the light, heavy in the shade
    body = [(11, 18), (15, 14), (27, 14), (32, 18), (33, 25), (30, 31), (13, 31), (10, 25)]
    g.sphere(body, C, 22, 21, 11.5, 9.5)
    for (x, y) in ((15, 17), (16, 17), (17, 16), (15, 18)):                   # the sheen on the boiler's shoulder
        g.px(x, y, "copper", 4)
    g.line([(23, 15), (24, 31)], C, 0)                                        # the seam of the front plate
    for y in range(17, 31, 3):
        g.px(25, y, C, 4)                                                      # its rivets
    for x in range(12, 32, 3):                                                 # the riveted band round the belly
        if g.a[28, x]:
            g.px(x, 28, C, 4 if x < 22 else 3)
    for x in range(11, 33):
        if g.a[29, x] and not g.hole[29, x]:
            g.px(x, 29, C, 1)
    for (x, y) in ((14, 30), (15, 30), (17, 30), (28, 27), (29, 26), (29, 27), (12, 24), (13, 26)):
        g.px(x, y, "verdigris", 2 if (x + y) % 2 else 3)                    # the green of old copper, low down
    # the core: a glowing window in an iron ring on the front plate
    g.disc(26, 24, 3.3, "iron", levels=(2, 1, 1, 0))
    g.disc(26, 24, 2.1, "volt", levels=(4, 4, 3, 2))
    g.px(25, 23, "volt", 4)
    for (x, y) in ((24, 27), (25, 28), (27, 28)):                             # its light on the plate below
        g.px(x, y, C, 4)
    # the helmet, thrust forward: a brow, the glowing slit, a grille for a jaw
    g.box(25, 12, 29, 15, "iron", inner=(1, 1), rim=2, shade=0)               # the neck
    g.poly([(25, 5), (31, 5), (33, 8), (32, 12), (25, 12)], C, inner=(3, 2), rim=4, shade=1)
    g.line([(26, 5), (31, 5)], C, 4)
    g.line([(27, 8), (32, 8)], "volt", 3)
    g.px(31, 8, "volt", 4)
    g.px(32, 8, "volt", 4)
    for x in (28, 30):
        g.dark(x, 10)
    # the near leg: an iron thigh, a copper knee with a piston behind it, a shin guard, a heavy boot
    g.poly([(22, 35), (28, 35), (28, 43), (23, 43)], "iron", inner=(3, 2), rim=4, shade=1)
    g.tube(21, 39, 22, 49, 0.8, "steel", levels=(3, 2))                     # the knee piston
    g.disc(26, 44.5, 2.6, C, levels=(4, 3, 2, 1))
    g.poly([(23, 47), (29, 47), (28, 53), (23, 53)], C, inner=(3, 2), rim=4, shade=1)
    g.line([(24, 49), (27, 49)], C, 1)
    g.poly([(22, 53), (31, 53), (33, 56), (22, 56)], "iron", inner=(3, 2), rim=4, shade=1)
    for x in (25, 28, 31):
        g.dark(x, 56)
    # the near arm: a big pauldron, an iron arm, a copper gauntlet
    g.tube(31, 22, 33, 29, 1.9, "iron", levels=(4, 3, 2, 1))
    for (x, y) in ((28, 20), (29, 21), (30, 21), (27, 19)):                  # the pauldron's shadow on the body
        if g.a[y, x]:
            g.px(x, y, C, 1)
    g.disc(31, 17, 4.2, C, levels=(4, 4, 3, 2, 1))
    g.px(30, 15, C, 4)
    g.px(33, 15, "verdigris", 3)
    g.poly([(31, 29), (36, 29), (37, 34), (31, 35)], C, inner=(3, 2), rim=4, shade=1)
    g.line([(32, 33), (36, 33)], C, 1)
    g.px(36, 31, "verdigris", 2)
    return g.done(), (20, 56)


def sample():
    """The render as it is now and the drawing, on the field's ground, at 1× and enlarged."""
    from PIL import Image
    from paths import out
    import os
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "game", "assets")
    old = Image.open(os.path.join(root, "sprites", "Мудрец_idle.png")).convert("RGBA")
    ground = Image.open(os.path.join(root, "ground.png")).convert("RGBA")
    rgba, (ox, oy) = sage()
    new = Image.fromarray(rgba, "RGBA")
    W, H = 120, 80
    tile = ground.crop((300, 300, 300 + W, 300 + H))
    row = Image.new("RGBA", (W * 2, H))
    for i, (im, px, py) in enumerate(((old, 15, 50), (new, ox, oy))):
        t = tile.copy()
        t.alpha_composite(im, (60 - px, 70 - py))
        row.paste(t, (i * W, 0))
    big = row.resize((row.width * 6, row.height * 6), Image.NEAREST)
    small = row.resize((row.width * 2, row.height * 2), Image.NEAREST)
    sheet = Image.new("RGBA", (big.width, big.height + small.height + 8), (20, 16, 24, 255))
    sheet.paste(big, (0, 0))
    sheet.paste(small, (0, big.height + 8))
    sheet.save(out("golem_drawn_sample.png"))
    return out("golem_drawn_sample.png")


if __name__ == "__main__":
    import sys
    if (sys.argv[1:] or ["sample"])[0] == "sample":
        print(sample())
