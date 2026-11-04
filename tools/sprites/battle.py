"""Battle on a large field in style 1: Foundry (leader + golems of sizes 4-6, one broken) against the Swarm."""
import random
from PIL import ImageFont
from kit import *
from r3d import rot_x, rot_z, render
import golem7 as G
import leaders as LD
import swarm1 as W
from golem7 import cfg
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


def build():
    sc = Scene(WW, HH)
    ground(sc)
    items = []
    rnd = random.Random(8)

    # ---------------- foundry
    golems = [  # (col, row, size, cfg, level, pose, dx)
        (5, 6, 6, cfg(legs="pillars", arms=("heavy", "heavy"), tools=("hammer", "shield")), 3, "attack", 16),
        (6, 0, 5, cfg(arms=("heavy", "piston"), tools=("hammer", "shield")), 2, "attack", 14),
        (6, 11, 5, cfg(legs="spider", arms=("long", "long"), tools=("hammer", "claw")), 2, "idle", 0),
        (6, 2, 5, cfg(arms=("piston", "heavy"), tools=("claw", "shield")), 1, "broken", 6),
        (3, 2, 5, cfg(head="sensor", core="volt", tools=("cannon", "shield")), 2, "attack", 0),
        (3, 9, 4, cfg(legs="springs", head="sensor", core="volt", tools=("cannon", "claw")), 1, "attack", 0),
        (4, 12, 4, cfg(legs="springs", tools=("hammer", "shield")), 1, "idle", 0),
    ]
    for (c, r, size, gcfg, lv, pose, dx) in golems:
        n = CELLS[size]
        fx = X0 + (c + n / 2) * CW + dx
        fy = Y0 + (r + n * 0.72) * CH
        spr = G.build(gcfg, lv, pose, k=GK[size])
        def f(spr=spr, fx=fx, fy=fy, size=size, c=c, r=r, n=n):
            footprint(sc, c, r, n)
            shadow(sc, fx + 2, fy, 22 * n + 14, 6 + 3 * n)
            put(sc, spr, fx, fy)
        items.append((fy, f))
    lx, ly = X0 + 2.5 * CW, Y0 + 6.8 * CH
    lead = LD.build("forge", "idle", k=1.0)
    items.append((ly, lambda: (shadow(sc, lx + 2, ly, 34, 7), put(sc, lead, lx, ly))))

    # ---------------- swarm
    count = 0
    plans = (None,) * 4 + W.TRAITS
    for c in range(8, 16):
        for r in range(14):
            dens = {8: 0.8, 9: 0.9, 10: 0.85, 11: 0.7, 12: 0.55, 13: 0.45, 14: 0.3, 15: 0.2}[c]
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
                primary = rnd.choice(plans)
                extra = tuple(t for t in W.TRAITS if t != primary and rnd.random() < 0.1)[:1]
                traits = ((primary,) if primary else ()) + extra
                if rnd.random() < 0.06:
                    traits += ("giant",)
                pose = "attack" if (c <= 9 and rnd.random() < 0.6) else "idle"
                hue = rnd.uniform(-0.16, 0.16)
                spr = W.build(traits, hue, pose, soldiers and primary is None, k=1.0, genes=W.genes_for(rnd.randrange(10 ** 6)))
                if c == 8 and rnd.random() < 0.15:
                    spr = flash(spr)
                fx, fy = cx + ox, cy + oy
                def f(spr=spr, fx=fx, fy=fy):
                    shadow(sc, fx - 1, fy, 14, 3)
                    put(sc, spr, fx, fy, mirror=True)
                items.append((fy, f))
                count += 1
    for i in range(10):
        x, y = rnd.uniform(395, 480), rnd.uniform(70, 510)
        spr = dead_bug(rnd.uniform(-0.15, 0.15), i)
        items.append((y - 3, lambda spr=spr, x=x, y=y: put(sc, spr, x, y, mirror=True)))
    qx, qy = X0 + 15.6 * CW, Y0 + 8.4 * CH
    qs = W.queen(0.0, "attack", k=0.92)
    items.append((qy, lambda: (shadow(sc, qx + 30, qy, 170, 22), put(sc, qs, qx, qy, mirror=True))))
    count += 1

    for _, f in sorted(items, key=lambda t: t[0]):
        f()
    for (x, y, col) in ((260, 128, "volt"), (300, 374, "volt"), (232, 140, "volt")):
        bolt(sc, x, y, col)
    for (x, y, big) in ((452, 296, True), (432, 66, True), (470, 274, False), (425, 86, False)):
        spark(sc, x, y, big)
    return sc, count, len(golems)


def overlay(img, count, ng):
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
    fs = ImageFont.truetype(font("PTSerif-Regular.ttf"), 17)
    t = "Ход 5"
    w = d.textlength(t, font=ft)
    d.rectangle([WW - w / 2 - 22, 10, WW + w / 2 + 22, 46], fill=(18, 16, 22), outline=(110, 100, 130))
    d.text((WW - w / 2, 15), t, font=ft, fill=(230, 222, 206))
    d.text((24, HH * S - 34), f"Литейщик · лидер и {ng} големов · размеры 4–6 (1, 2×2, 3×3 клетки) · один сломан",
           font=fs, fill=(214, 196, 150))
    t2 = f"Рой · {count - 1} особей размера 1–2 и матка (6)"
    d.text((WW * S - 24 - d.textlength(t2, font=fs), HH * S - 34), t2, font=fs, fill=(196, 186, 214))


if __name__ == "__main__":
    sc, count, ng = build()
    img = sc.image(S)
    overlay(img, count, ng)
    img.save(out("battle.png"))
    print(img.size, count)
