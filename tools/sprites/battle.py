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


def dead_bug(hue, seed):
    m = W.body(hue, (), "idle").transformed(rot_x(np.pi), (0, 10.0, 0)).transformed(rot_z(0.15))
    spr = render(m.scaled(1.0), 64, 56, 30, 48, **W.STYLE1)
    spr.ox, spr.oy = 30, 48
    return spr


LEADERS = {   # the swarm's leader: (name, size, file, evolutions bred by now: form → its evolutions)
    "Матка": ("матка", 6, "battle.png", {}),
    "Разум улья": ("Разум улья", 4, "battle_razum.png", {None: ("phalanx",), "wings": ("syringe",), "scythes": ("saws",)}),
    "Пожиратель": ("Пожиратель", 7, "battle_pozh.png", {None: ("formic",), "horn": ("forked",), "stinger": ("vise",)}),
    "Кукушка": ("Кукушка", 3, "battle_kuk.png", {"acid": ("scent",), "wings": ("tough",), "firefly": ("hood",)}),
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
    for (c, r, size, frame, pose, dx) in golems:
        n = CELLS[size]
        fx = X0 + (c + n / 2) * CW + dx
        fy = Y0 + (r + n * 0.72) * CH
        spr = F.build(frame, pose, k=GK[size])
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
    count = 0
    plans = (None,) * 4 + W.TRAITS

    def front_at(y):
        xs = [x for (x, y0, y1) in fronts if y0 <= y <= y1]
        return max(xs) if xs else None

    def bug(traits, pose, soldier, x, y, hit=False):
        if any(a <= x <= c and b <= y <= d for a, b, c, d in reserve):
            return
        primary = traits[0] if traits and traits[0] != "giant" else None
        spr = W.build(traits, rnd.uniform(-0.16, 0.16), pose, soldier, k=1.0, genes=W.genes_for(rnd.randrange(10 ** 6)),
                      evo=evo_of.get(primary, ()))
        placed.append((x, y))
        if hit:
            spr = flash(spr, 0.75)
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
    for c in range(7, 16):
        for r in range(14):
            dens = {7: 0.7, 8: 0.85, 9: 0.9, 10: 0.85, 11: 0.7, 12: 0.55, 13: 0.45, 14: 0.3, 15: 0.2}[c]
            if (c >= 13 and 5 <= r <= 9) or rnd.random() > dens:
                continue
            soldiers = rnd.random() < 0.12
            nunits = 2 if soldiers else rnd.choice((2, 3, 3, 4))
            cx, cy = X0 + c * CW + CW / 2, Y0 + r * CH + CH / 2
            spots = []
            for _ in range(nunits):
                for _t in range(30):
                    ox, oy = rnd.uniform(-CW * 0.5, CW * 0.5), rnd.uniform(-CH * 0.45, CH * 0.45)
                    if all(abs(ox - a) > 12 or abs(oy - b) > 7 for a, b in spots):
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
                bug(traits, pose, soldiers and primary is None, fx, fy)
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
    elif leader == "Разум улья":
        qs = SL.build("Разум улья", "idle", 1.0)
        items.append((qy, lambda: (shadow(sc, qx + 4, qy, 60, 10), put(sc, qs, qx, qy, mirror=True))))
    elif leader == "Кукушка":
        qs = SL.build("Кукушка", "idle", 1.0)
        items.append((qy, lambda: (shadow(sc, qx + 4, qy, 50, 8), put(sc, qs, qx, qy, mirror=True))))
        cx_, cy_ = lx - 26, ly + 4                  # the changeling: a worker in the Foundry's rear, at the Architect's back
        ch = W.build((), 0.02, "attack", False, k=1.0, genes=W.genes_for(77))
        items.append((cy_, lambda: (shadow(sc, cx_, cy_ + 2, 22, 5), put(sc, ch, cx_, cy_))))
    count += 1

    for _, f in sorted(items, key=lambda t: t[0]):
        f()
    for (tx, ty) in targets:
        spark(sc, int(tx), int(ty) - 6, True)
    if leader == "Разум улья":                    # psi: a blow from the brain into the Guard, the clouding over its line
        SA.psi_wave(sc, (qx - 10, qy - 34), (gx + 10, gy - 70))
        for r in (40, 62, 84):
            SA.ring(sc, gx - 10, gy + 2, r, r * 0.3, SA.PHERO, 0.45)
        for k_ in range(8):                           # the machines' cores stall: sparks over them
            sc.rgb[int(gy - 96 - (k_ * 7) % 20), int(gx - 20 + (k_ * 11) % 40)] = hexc("#e0e0f0")
    if leader == "Кукушка":                       # the Architect bitten from behind: infected
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


def overview(names=("Разум улья", "Пожиратель", "Кукушка")):
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
