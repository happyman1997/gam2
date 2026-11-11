"""Battle on a large field in style 1: Foundry (leader + golems of sizes 4-6, one broken) against the Swarm."""
import random
from PIL import ImageFont
from kit import *
from r3d import rot_x, rot_z, render
import frames as F
import leaders_h as LH
import swarm1 as W
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 540
CW, CH, X0, Y0 = 50, 34, 30, 46
GK = {4: 1.15, 5: 1.6, 6: 2.2}          # golem scale per size
CELLS = {4: 1, 5: 2, 6: 3}


def ground(sc):
    yy, xx = sc.yy, sc.xx
    th = BAYER[yy % 4, xx % 4]
    n1 = value_noise(WW, HH, 20, 1) * 0.5 + value_noise(WW, HH, 6, 2) * 0.5
    cols = [hexc(c) for c in ("#262030", "#2a2334", "#2e2638", "#32293c")]
    lv = np.clip(np.floor(n1 * 4 + (th - 0.5) * 1.2), 0, 3).astype(int)
    for i, c in enumerate(cols):
        sc.rgb[lv == i] = c
    n2 = value_noise(WW, HH, 24, 3) * 0.6 + value_noise(WW, HH, 6, 4) * 0.4
    centre = np.exp(-((xx - 440 - 30 * np.sin(yy / 60.0)) / 110.0) ** 2)
    dirt = (n2 * 0.8 + centre * 0.5 + (th - 0.5) * 0.15) > 0.8
    sc.rgb[dirt] = sc.rgb[dirt] * 0.82 + hexc("#2a1e22") * 0.18
    rnd = random.Random(3)
    for _ in range(2200):
        x, y = rnd.randrange(1, WW - 1), rnd.randrange(3, HH)
        if dirt[y, x]:
            continue
        col = hexc(rnd.choice(("#2c3a3a", "#33443f", "#283432", "#3a4a44")))
        for k in range(rnd.randint(1, 3)):
            sc.rgb[y - k, x + (rnd.choice((-1, 0, 1)) if k else 0)] = col
    for _ in range(4000):
        x, y = rnd.randrange(WW), rnd.randrange(HH)
        sc.rgb[y, x] *= rnd.choice((0.88, 1.12))
    for c in range(19):
        for r in range(15):
            x, y = X0 + c * CW, Y0 + r * CH
            if c in (8, 9, 10) or not (0 <= x < WW and 0 <= y < HH):
                continue
            col = hexc("#c9b27a") if c < 8 else hexc("#9a8ab8")
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                if 0 <= x + dx < WW and 0 <= y + dy < HH:
                    sc.rgb[y + dy, x + dx] = sc.rgb[y + dy, x + dx] * 0.75 + col * 0.25


def shadow(sc, x, y, w, h=5):
    e = ((sc.xx - x) / (w / 2)) ** 2 + ((sc.yy - y) / (h / 2)) ** 2
    sc.rgb[e <= 1] *= 0.62


def footprint(sc, c, r, n):
    x0, y0, x1, y1 = X0 + c * CW, Y0 + r * CH, X0 + (c + n) * CW, Y0 + (r + n) * CH
    edge = np.zeros((HH, WW), bool)
    edge[y0:y1, x0] = edge[y0:y1, x1 - 1] = True
    edge[y0, x0:x1] = edge[y1 - 1, x0:x1] = True
    edge &= ((sc.xx + sc.yy) % 3 != 0)
    sc.rgb[edge] = sc.rgb[edge] * 0.55 + hexc("#c9b27a") * 0.45


def put(sc, spr, fx, fy, mirror=False):
    ox, oy = spr.ox, spr.oy
    if mirror:
        f = spr.flipped()
        f.ox, f.oy = spr.w - 1 - ox, oy
        spr = f
    sc.blit(spr, int(round(fx - spr.ox)), int(round(fy - spr.oy)))


def flash(spr, k=0.65):
    f = Sprite(spr.w, spr.h)
    f.rgb, f.a = spr.rgb * (1 - k) + 245 * k, spr.a.copy()
    f.ox, f.oy = spr.ox, spr.oy
    return f


def bolt(sc, x, y, col, length=18):
    rp = VOLT if col == "volt" else FIRE
    for i in range(length):
        t = i / length
        c = rp[4] if i < 2 else (rp[3] if t < 0.3 else (rp[2] if t < 0.65 else rp[1]))
        sc.rgb[y, int(x - i)] = c
        sc.occ[y, int(x - i)] = True
    sc.rgb[y - 1:y + 2, x - 1:x + 1] = rp[4]
    sc.glow(x - 2, y, 12, hexc("#40d8ff") if col == "volt" else hexc("#ff9a30"), 0.6)


def spark(sc, x, y, big=False):
    n = 4 if big else 3
    for d in range(-n, n + 1):
        col = hexc("#ffffff") if abs(d) <= 1 else hexc("#ffe0a0")
        sc.rgb[y, x + d] = col
        if abs(d) < n:
            sc.rgb[y + d, x] = col
    sc.occ[y - n:y + n + 1, x - n:x + n + 1] = True
    sc.glow(x, y, 14 if big else 10, hexc("#ffd890"), 0.6)


def glue_arc(sc, a, b, h, col):
    """A strand of sticky venom over the heads of the swarm: a light thread with a dark underside, drops hanging off
    it, a glob at each end."""
    n = int(np.hypot(b[0] - a[0], b[1] - a[1])) + 2
    dark = col * 0.35
    for i, t in enumerate(np.linspace(0, 1, n)):
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t - h * 4 * t * (1 - t)
        xi, yi = int(round(x)), int(round(y))
        sc.rgb[yi + 1, xi] = sc.rgb[yi + 1, xi] * 0.3 + dark * 0.7
        sc.rgb[yi, xi] = col
        sc.occ[yi:yi + 2, xi] = True
        if i % 23 == 11:                            # a drop hanging off the strand
            sc.rgb[yi + 2:yi + 4, xi] = col * 0.85
    for (x, y), r in ((a, 2), (b, 3)):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    sc.rgb[int(y + dy), int(x + dx)] = col if dy < r - 1 else dark
        sc.glow(x, y, 8 + 3 * r, col, 0.35)


def tint(spr, col, k):
    f = Sprite(spr.w, spr.h)
    f.rgb, f.a = spr.rgb * (1 - k) + col * k, spr.a.copy()
    f.ox, f.oy = spr.ox, spr.oy
    return f


def dead_bug(hue, seed):
    m = W.body(hue, (), "idle").transformed(rot_x(np.pi), (0, 10.0, 0)).transformed(rot_z(0.15))
    spr = render(m.scaled(1.0), 64, 56, 30, 48, **W.STYLE1)
    spr.ox, spr.oy = 30, 48
    return spr


POOL = {"Матка": "matka", "Разум улья": "razum", "Пожиратель": "devourer", "Чума": "cuckoo"}   # its mutation pool

LEADERS = {   # the swarm's leader: (name, size, file, evolutions bred by now: form → its evolutions)
    "Матка": ("матка", 6, "battle.png", {}),
    "Разум улья": ("Разум улья", 4, "battle_razum.png", {None: ("phalanx",), "wings": ("syringe",), "scythes": ("saws",)}),
    "Пожиратель": ("Пожиратель", 7, "battle_pozh.png", {None: ("formic",), "horn": ("forked",), "stinger": ("vise",)}),
    "Чума": ("Чума", 3, "battle_kuk.png", {"acid": ("scent",), "wings": ("tough",), "firefly": ("hood",)}),
}


def build(leader="Матка"):
    import swarm_leaders as SL
    import swarm_abilities as SA
    sc = Scene(WW, HH)
    ground(sc)
    items = []
    rnd = random.Random(8)
    evo_of = LEADERS[leader][3]
    placed = []                                     # where the bugs stand (for the Hive Mind's threads)
    reserve = []                                    # boxes kept clear of bugs (the Devourer at the front)

    # ---------------- foundry
    golems = [  # (col, row, size, frame, pose, dx)
        (5, 6, 6, "Страж", "attack", 16),
        (5, 0, 5, "Мудрец", "attack", 24),
        (6, 11, 5, "Горн", "attack", 0),
        (6, 2, 5, "Горн", "broken", 6),
        (3, 2, 5, "Орудие", "attack", 0),
        (3, 9, 4, "Механик", "attack", 0),
        (4, 12, 4, "Механик", "idle", 0),
    ]
    fronts, targets = [], []
    gpos = {}                                       # (frame, col, row) -> (x, y, sprite): for the states over them
    for (c, r, size, frame, pose, dx) in golems:
        n = CELLS[size]
        fx = X0 + (c + n / 2) * CW + dx
        fy = Y0 + (r + n * 0.72) * CH
        spr = F.build(frame, pose, k=GK[size])
        gpos[(frame, c, r)] = (fx, fy, spr)
        def f(spr=spr, fx=fx, fy=fy, size=size, c=c, r=r, n=n):
            footprint(sc, c, r, n)
            shadow(sc, fx + 2, fy, 22 * n + 14, 6 + 3 * n)
            put(sc, spr, fx, fy)
        items.append((fy, f))
        cols = np.nonzero(spr.a[: spr.oy + 2].max(axis=0))[0]          # the sprite's front edge
        front = fx + cols.max() - spr.ox
        if front > 380:                                                # golems in the front line hold the swarm back
            fronts.append((front, fy - 6 * n - 8, fy + 8))
        h = F.hit(frame) if pose == "attack" else None
        if h is not None:
            hx, hy = F.to_screen(h, GK[size])
            targets.append([fx + hx, fy + hy, frame == "Орудие"])
    lx, ly = X0 + 2.5 * CW, Y0 + 6.8 * CH
    lead = LH.GH.build(LH.ZODCHIY, "idle", 1.05)
    items.append((ly, lambda: (shadow(sc, lx + 2, ly, 34, 7), put(sc, lead, lx, ly))))
    gx, gy = X0 + 6.5 * CW + 16, Y0 + (6 + 3 * 0.72) * CH            # the Guard
    if leader == "Пожиратель":                     # grown to size 7, at the front, its jaws in the Guard
        px, py = gx + 150, gy + 14
        reserve.append((px - 40, py - 60, px + 120, py + 34))
        dv = SL.build("Пожиратель", "attack", 1.0, stage=2)
        items.append((py, lambda: (shadow(sc, px + 30, py, 130, 16), put(sc, dv, px, py, mirror=True))))

    # ---------------- swarm: pressed against the golems, the ones being hit stand where the blows land
    import swarm_mut as MU
    import swarm_status as ST
    count = 0
    plans = (None,) * 4 + W.TRAITS
    pool = [k for k, *_ in MU.POOLS["common"][3]] + [k for k, *_ in MU.POOLS[POOL[leader]][3]]
    marks = []                                      # (state, x, top) glyphs to draw over the crowd afterwards
    spiders = [(548, 486, "attack"), (566, 452, "attack"), (590, 506, "idle")]   # spitters, 2–3 cells behind the front
    for (x, y, _) in spiders:
        reserve.append((x - 22, y - 22, x + 22, y + 8))

    def front_at(y):
        xs = [x for (x, y0, y1) in fronts if y0 <= y <= y1]
        return max(xs) if xs else None

    def bug(traits, pose, soldier, x, y, hit=False, rare=None, chimera=None, state=None):
        if any(a <= x <= c and b <= y <= d for a, b, c, d in reserve):
            return
        primary = traits[0] if traits and traits[0] != "giant" else None
        spr = W.build(traits, rnd.uniform(-0.16, 0.16), pose, soldier, k=1.0, genes=W.genes_for(rnd.randrange(10 ** 6)),
                      evo=evo_of.get(primary, ()), rare=rare, chimera=chimera)
        placed.append((x, y))
        if hit:
            spr = flash(spr, 0.75)
        if state == "frenzy":                       # the Devourer's feeding frenzy: a red flush and the glyph
            spr = tint(spr, hexc("#e04030"), 0.22)
        if state:
            marks.append((state, x, ST.top_of(spr, y) - 11))
        def f(spr=spr, fx=x, fy=y):
            shadow(sc, fx - 1, fy, 14, 3)
            put(sc, spr, fx, fy, mirror=True)
        items.append((y, f))

    shots = []
    for t in targets:                       # a gunner's shells fly over its neighbours into the swarm's front rank
        if t[2]:
            fr = front_at(t[1])
            mz = (t[0] - 52, t[1] - 20)
            t[0] = (fr if fr is not None else 420) + 10
            shots.append((mz, (t[0], t[1] - 6)))
    targets = [(t[0], t[1]) for t in targets]
    for (tx, ty) in targets:
        for ox, oy in ((0, 0), (12, -6), (10, 7)):
            bug((rnd.choice(plans),) if rnd.random() < 0.5 else (), "attack", False, tx + ox, ty + oy, hit=(ox == 0))
            count += 1
    tight = leader == "Матка"                      # Матка's tight flocks: up to 6 small ones in a cell, the swarm narrower
    if tight:
        DENS = {7: 0.85, 8: 0.95, 9: 0.95, 10: 0.9, 11: 0.8, 12: 0.55, 13: 0.2, 14: 0.08, 15: 0.0}
    else:
        DENS = {7: 0.7, 8: 0.85, 9: 0.9, 10: 0.85, 11: 0.7, 12: 0.55, 13: 0.45, 14: 0.3, 15: 0.2}
    for c in range(7, 16):
        for r in range(14):
            cx, cy = X0 + c * CW + CW / 2, Y0 + r * CH + CH / 2
            dens = DENS[c]
            pack = leader == "Пожиратель" and abs(cx - (gx + 190)) < 170 and abs(cy - (gy + 10)) < 120
            if pack:                                # the Devourer's pack: the flocks rushed where he rushed
                dens = min(1.0, dens + 0.35)
            if (c >= 13 and 5 <= r <= 9) or rnd.random() > dens:
                continue
            soldiers = rnd.random() < 0.12
            nunits = 2 if soldiers else rnd.choice((4, 5, 5, 6) if tight else (2, 3, 3, 4))
            nunits += 1 if pack else 0
            gapx, gapy = (9, 5) if tight else (12, 7)
            spots = []
            for _ in range(nunits):
                for _t in range(30):
                    ox, oy = rnd.uniform(-CW * 0.5, CW * 0.5), rnd.uniform(-CH * 0.45, CH * 0.45)
                    if all(abs(ox - a) > gapx or abs(oy - b) > gapy for a, b in spots):
                        break
                spots.append((ox, oy))
                fx, fy = cx + ox, cy + oy
                fr = front_at(fy)
                if fr is not None and fx < fr + 4:
                    fx = fr + 4 + rnd.uniform(0, 14)
                elif fr is None and c == 7:
                    continue                     # no golem in this row: the swarm's front stays where it was
                if any(abs(fx - tx) < 16 and abs(fy - ty) < 10 for (tx, ty) in targets):
                    continue
                primary = rnd.choice(plans)
                extra = tuple(t for t in W.TRAITS if t != primary and rnd.random() < 0.1)[:1]
                traits = ((primary,) if primary else ()) + extra
                if rnd.random() < 0.06:
                    traits += ("giant",)
                near_front = fr is not None and fx < fr + 30
                pose = "attack" if (near_front or c <= 8) and rnd.random() < 0.7 else "idle"
                rare = rnd.choice(pool) if "giant" not in traits and rnd.random() < 0.07 else None
                chim = rnd.choice(W.CHIMERAS) if leader == "Чума" and rnd.random() < 0.07 else None
                state = None
                if pack and np.hypot(fx - (gx + 150), fy - gy) < 80 and rnd.random() < 0.12:
                    state = "frenzy"                # Кормовое безумие: those beside him while he eats
                bug(traits, pose, soldiers and primary is None, fx, fy, rare=rare, chimera=chim, state=state)
                count += 1
    for (x, y, pose) in spiders:                    # the spitters stand back and spit glue over the heads of their own
        spr = W.build(("spitter",), rnd.uniform(-0.1, 0.1), pose, False, k=1.0, genes=W.genes_for(500 + int(x)))
        items.append((y, lambda spr=spr, x=x, y=y: (shadow(sc, x - 1, y, 16, 3), put(sc, spr, x, y, mirror=True))))
        count += 1
    for i in range(10):
        y = rnd.uniform(70, 510)
        fr = front_at(y)
        x = (fr if fr is not None else 432) + rnd.uniform(0, 20)
        spr = dead_bug(rnd.uniform(-0.15, 0.15), i)
        items.append((y - 3, lambda spr=spr, x=x, y=y: put(sc, spr, x, y, mirror=True)))
    qx, qy = X0 + 15.6 * CW, Y0 + 8.4 * CH
    if leader == "Матка":
        qs = W.queen(0.0, "attack", k=0.92)
        items.append((qy, lambda: (shadow(sc, qx + 30, qy, 170, 22), put(sc, qs, qx, qy, mirror=True))))
        # Кладка: a clutch at her side hatching, two larvae already out; the Heiress keeps close and does not fight
        cl = SA.render_small(SA.clutch(1), 1.0)
        cxl, cyl = qx - 74, qy + 16
        items.append((cyl, lambda: put(sc, cl, cxl, cyl)))
        marks.append(("hatching", cxl, ST.top_of(cl, cyl) - 11))
        for i, (dx_, dy_) in enumerate(((-34, 6), (-22, 22))):
            lv = SL.build("личинка", "attack", 1.0)
            items.append((cyl + dy_, lambda lv=lv, x=cxl + dx_, y=cyl + dy_: (shadow(sc, x, y, 12, 3), put(sc, lv, x, y, mirror=True))))
        hr = W.build(("wings",), 0.0, "idle", False, k=1.0, genes=W.genes_for(31), rare="heir")
        hx, hy = qx - 40, qy - 30
        items.append((hy, lambda: (shadow(sc, hx, hy, 14, 3), put(sc, hr, hx, hy, mirror=True))))
    elif leader == "Разум улья":
        qs = SL.build("Разум улья", "idle", 1.0)
        items.append((qy, lambda: (shadow(sc, qx + 4, qy, 60, 10), put(sc, qs, qx, qy, mirror=True))))
    elif leader == "Чума":
        qs = SL.build("Чума", "idle", 1.0)
        items.append((qy, lambda: (shadow(sc, qx + 4, qy, 50, 8), put(sc, qs, qx, qy, mirror=True))))
        cx_, cy_ = lx - 26, ly + 4                  # the changeling: a worker in the Foundry's rear, at the Architect's back
        ch = W.build((), 0.02, "attack", False, k=1.0, genes=W.genes_for(77))
        items.append((cy_, lambda: (shadow(sc, cx_, cy_ + 2, 22, 5), put(sc, ch, cx_, cy_))))
    count += 1

    if leader == "Пожиратель":                     # the pack leaves him the bodies: the dead heaped at his jaws
        for i, (dx_, dy_) in enumerate(((-34, 18), (-20, 30), (-46, 34), (-8, 40))):
            spr = dead_bug(rnd.uniform(-0.15, 0.15), 20 + i)
            items.append((py + dy_ - 3, lambda spr=spr, x=px + dx_, y=py + dy_: put(sc, spr, x, y, mirror=True)))

    for _, f in sorted(items, key=lambda t: t[0]):
        f()
    for (tx, ty) in targets:
        spark(sc, int(tx), int(ty) - 6, True)
    # the spitters' glue: arcs over the swarm's heads into the Forge at the bottom, which is glued to its cell
    import swarm_effects as E
    glue = hexc("#e8dcb0")
    hx_, hy_, hspr = gpos[("Горн", 6, 11)]
    for (x, y, pose), (tx, ty) in zip(spiders, ((hx_ + 18, hy_ - 30), (hx_ + 10, hy_ - 44))):
        if pose != "attack":
            continue
        glue_arc(sc, (x - 11, y - 7), (tx, ty), 30, glue)
    ST.ground(sc, "glued", hx_ + 2, hy_, 34)
    ST.glyph(sc, "glued", hx_, ST.top_of(hspr, hy_) - 12)
    # acid and stings eat the Guard's armour
    sx_, sy_, sspr = gpos[("Страж", 5, 6)]
    ST.glyph(sc, "shred", sx_ + 8, ST.top_of(sspr, sy_) - 12)
    for state, x, top in marks:
        ST.glyph(sc, state, x, top)
    if leader == "Чума":                       # the Architect bitten from behind: infected
        ST.on_body(sc, lead, lx, ly, "infected", seed=4)
        ST.glyph(sc, "infected", lx, ST.top_of(lead, ly) - 12)
    if leader == "Разум улья":                    # one thought per flock: the whole flock's threads meet on one golem
        mx_, my_, mspr = gpos[("Мудрец", 5, 0)]
        aim = (mx_ + 6, my_ - 40)
        near = [(x, y) for (x, y) in placed if aim[0] + 60 < x < aim[0] + 190 and aim[1] - 30 < y < aim[1] + 90]
        for (x, y) in near[:9]:
            SA.thread(sc, (x - 4, y - 12), aim, sag=-8, k=0.6)
        SA.sigil(sc, aim[0], aim[1], 6)
        kx_, ky_, kspr = gpos[("Механик", 3, 9)]  # the clouding: a mindless machine stalls
        ST.on_body(sc, kspr, kx_, ky_, "stall")
        ST.glyph(sc, "stall", kx_, ST.top_of(kspr, ky_) - 12)
    if leader == "Разум улья":                    # psi: a blow from the brain into the Guard, the clouding over its line
        SA.psi_wave(sc, (qx - 10, qy - 34), (gx + 10, gy - 70))
        g_ = F.build("Страж", "attack", k=GK[6])  # the psi piling up over the Guard
        ST.pips(sc, gx, ST.top_of(g_, gy) - 18, 3)
        for r in (40, 62, 84):
            SA.ring(sc, gx - 10, gy + 2, r, r * 0.3, SA.PHERO, 0.45)
        for k_ in range(8):                           # the machines' cores stall: sparks over them
            sc.rgb[int(gy - 96 - (k_ * 7) % 20), int(gx - 20 + (k_ * 11) % 40)] = hexc("#e0e0f0")
    if leader == "Чума":                       # the Architect bitten from behind: infected
        SA.spots(sc, int(lx) + 2, int(ly) - 30, [(0, 0), (-3, 7), (2, 13)])
        SA.splat(sc, lx - 26, ly + 6, 14, col=hexc("#5a4030"), k=0.7)
    for (a, b) in shots:                    # tracers along the shells' path
        for f in (0.35, 0.7):
            x = a[0] + (b[0] - a[0]) * f
            y = a[1] + (b[1] - a[1]) * f
            bolt(sc, int(x), int(y), "fire", 14)
    return sc, count, len(golems)


def overlay(img, count, ng, leader="Матка"):
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
    fs = ImageFont.truetype(font("PTSerif-Regular.ttf"), 17)
    t = "Ход 5"
    w = d.textlength(t, font=ft)
    d.rectangle([WW - w / 2 - 22, 10, WW + w / 2 + 22, 46], fill=(18, 16, 22), outline=(110, 100, 130))
    d.text((WW - w / 2, 15), t, font=ft, fill=(230, 222, 206))
    d.text((24, HH * S - 34), f"Литейщик · лидер и {ng} големов · размеры 4–6 (1, 2×2, 3×3 клетки) · один сломан",
           font=fs, fill=(214, 196, 150))
    name, size = LEADERS[leader][0], LEADERS[leader][1]
    t2 = f"Рой · {count - 1} особей размера 1–2 и {name} ({size})"
    d.text((WW * S - 24 - d.textlength(t2, font=fs), HH * S - 34), t2, font=fs, fill=(196, 186, 214))


def overview(names=("Разум улья", "Пожиратель", "Чума")):
    """The other swarm leaders' battles side by side, half size."""
    from PIL import Image
    ims = [Image.open(out(LEADERS[n][2])).convert("RGB").resize((WW, HH), Image.LANCZOS) for n in names]
    grid = Image.new("RGB", (WW * 2 + 12, HH * 2 + 12), (24, 18, 30))
    grid.paste(Image.open(out("battle.png")).convert("RGB").resize((WW, HH), Image.LANCZOS), (0, 0))
    for i, im in enumerate(ims, 1):
        grid.paste(im, ((i % 2) * (WW + 12), (i // 2) * (HH + 12)))
    grid.save(out("swarm_battles.png"))
    print("swarm_battles.png", grid.size)


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or ["Матка"]
    if names == ["all"]:
        names = list(LEADERS)
    for leader in names:
        sc, count, ng = build(leader)
        img = sc.image(S)
        overlay(img, count, ng, leader)
        img.save(out(LEADERS[leader][2]))
        print(LEADERS[leader][2], img.size, count)
    if len(names) == len(LEADERS):
        overview()
