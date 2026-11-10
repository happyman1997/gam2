"""The Swarm leaders' abilities at work, in the true relative scale of a battle (zoomed): the Matka's laying, the Hive
Mind's mark and its one mind, the Devourer growing through its three sizes, the Cuckoo's egg-laying (a human enemy
infected, then larvae crawling out of the body; mechanisms are not infected) and the changeling in the enemy's rear.

    python3 tools/sprites/swarm_abilities.py      -> out/swarm_abilities.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_x, I3
import swarm1 as W
import swarm_leaders as SL
import frames as F
import golems_h as GH
import leaders_h as LH
from leaders_sheet import canvas, put, fonts, S, GOLD, INK, MUT, BAD
from paths import out

Z = 1.4                                     # zoom over the battle scale; everything in a row shares it
PHERO = hexc("#b070ff")
INFECT = hexc("#9ae030")


def flip(spr):
    """An enemy faces the other way."""
    f = spr.flipped()
    f.ox, f.oy = spr.w - 1 - spr.ox, spr.oy
    return f


def render_small(m, k, size=1, box=(60, 40, 30, 32)):
    s = SL.SCALE[size] * k
    w, h, ox, oy = (int(v * s) for v in box)
    spr = W.rim_light(render(m.scaled(s), w, h, ox, oy, **W.STYLE1))
    spr.ox, spr.oy = ox, oy
    return SL.trim(spr)


def clutch(stage=0):
    """Eggs on the ground: 0 — fresh, 1 — cracking with larvae pushing out, 2 — empty broken shells."""
    m = Model()
    rng = np.random.default_rng(5)
    spots = [(0.0, 0.0), (4.2, 2.4), (-3.6, 2.8), (1.6, -3.4), (-2.4, -2.6), (5.2, -1.8)]
    for i, (x, z) in enumerate(spots):
        c = np.array((x, 1.9, z))
        if stage == 0 or (stage == 1 and i > 1):
            m.ell(c, (2.3, 1.9, 1.9), W.M_EGG)
            m.ell(c + (0.7, 0.9, 0.5), (0.55, 0.4, 0.5), SL.M_GRUB)            # a wet glint
            continue
        m.ell(c - (0, 0.8, 0), (2.3, 1.0, 1.9), W.M_EGG)                       # the bottom of the shell
        for a in np.linspace(0, 2 * np.pi, 8)[:-1]:                              # jagged rim
            p = c + np.array((np.cos(a) * 2.0, 0.1, np.sin(a) * 1.6))
            W.spike(m, p, p + np.array((np.cos(a) * 0.5, 1.0 + rng.uniform(0, 0.8), np.sin(a) * 0.3)), 0.45, W.M_EGG)
        if stage == 1:                                                          # a larva heaving itself out
            lv = SL.larva("attack")
            lv = lv.transformed(rot_z(1.1), (0, 0, 0)).scaled(0.8).transformed(I3, c + (0.6, -0.4, 0))
            m.extend(lv)
    for x in (-1.2, 2.6):                                                        # slime under the clutch
        m.ell((x, 0.1, 0.4), (3.6, 0.15, 2.6), SL.M_EGG_IN)
    return m


def thread(sc, a, b, col=PHERO, sag=10.0, k=0.9):
    """A pheromone thread: a sagging dotted line with a faint glow along it."""
    a, b = np.array(a, float), np.array(b, float)
    n = int(np.hypot(*(b - a)) / 1.2) + 2
    for i, t in enumerate(np.linspace(0, 1, n)):
        p = a + (b - a) * t + np.array((0, -sag * 4 * t * (1 - t)))
        x, y = int(round(p[0])), int(round(p[1]))
        if 0 <= x < sc.w and 0 <= y < sc.h and (i % 3 != 2):
            sc.rgb[y, x] = sc.rgb[y, x] * (1 - k) + col * k
        if i % 9 == 0:
            sc.glow(p[0], p[1], 7, col, 0.18)


def ring(sc, cx, cy, rx, ry, col=PHERO, k=0.85):
    for t in np.linspace(0, 2 * np.pi, int(2 * np.pi * max(rx, ry))):
        x, y = int(round(cx + np.cos(t) * rx)), int(round(cy + np.sin(t) * ry))
        if 0 <= x < sc.w and 0 <= y < sc.h:
            sc.rgb[y, x] = sc.rgb[y, x] * (1 - k) + col * k
    sc.glow(cx, cy, rx * 1.3, col, 0.35)


def sigil(sc, cx, cy, r, col=PHERO):
    """The mark: a hovering pheromone glyph — a ring with three spikes pointing in."""
    ring(sc, cx, cy, r, r, col)
    for a in (np.pi / 2, np.pi / 2 + 2 * np.pi / 3, np.pi / 2 + 4 * np.pi / 3):
        for t in np.linspace(0.35, 1.0, 8):
            x, y = int(round(cx + np.cos(a) * r * t)), int(round(cy - np.sin(a) * r * t))
            sc.rgb[y, x] = col
    sc.glow(cx, cy, r * 2.2, col, 0.5)


def splat(sc, cx, cy, r, col=INFECT, k=0.6):
    e = ((sc.xx - cx) / r) ** 2 + ((sc.yy - cy) / (r * 0.35)) ** 2
    th = BAYER[sc.yy % 4, sc.xx % 4]
    sel = (e <= 1) & (th < 0.7)
    sc.rgb[sel] = sc.rgb[sel] * (1 - k) + col * k * 0.6


def spots(sc, cx, cy, pts, col=INFECT):
    for dx, dy in pts:
        for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            sc.rgb[cy + dy + oy, cx + dx + ox] = col
        sc.glow(cx + dx, cy + dy, 5, col, 0.25)


def arrow(sc, x0, x1, y, col=hexc("#e2b968")):
    for x in range(int(x0), int(x1)):
        sc.rgb[y, x] = col
        sc.rgb[y + 1, x] = col * 0.6
    for d in range(1, 6):
        sc.rgb[y - d, int(x1) - d] = col
        sc.rgb[y + d, int(x1) - d] = col


LOWS = []


def put(sc, spr, cx, by, sw):
    """leaders_sheet.put, remembering how far each sprite reaches below its ground line."""
    import leaders_sheet as LS
    LS.put(sc, spr, cx, by, sw)
    LOWS.append((by, by + int(np.nonzero(spr.a.any(axis=1))[0].max()) - spr.oy))


def sheet():
    WW, RH, Y0 = 960, 204, 84
    HH = Y0 + 4 * RH + 10
    sc = canvas(WW, HH, 27)
    caps, heads = [], []
    k = Z

    # ---- Матка: laying
    y0 = Y0
    by = y0 + RH - 44
    heads.append((y0, "Матка", "Кладка — каждые 3 хода", "развитие: кладка чаще, +1 личинка или +1 к размеру", 0))
    put(sc, SL.build("Матка", "idle", k), 190, by, 95)
    eg = render_small(clutch(0), k * 1.9)
    sc.blit(eg, 300 - eg.ox, by - eg.oy)
    caps.append((210, by + 10, "отложила кладку"))
    eg = render_small(clutch(1), k * 1.9)
    put(sc, eg, 455, by, 22)
    caps.append((455, by + 10, "яйца лопаются"))
    put(sc, render_small(clutch(2), k * 1.9), 600, by + 4, 22)
    for dx in (-26, 26):
        put(sc, SL.build("личинка", "attack", k), 600 + dx, by, 10)
    gol = flip(F.build("Орудие", "idle", k=1.6 * k))
    put(sc, gol, 700, by, 34)
    caps.append((620, by + 10, "две личинки со следующего раунда бьются"))

    # ---- Разум улья: one mind and the mark
    y0 += RH
    by = y0 + RH - 44
    heads.append((y0, "Разум улья", "Единый разум и Метка", "развитие: две метки, метка каждый ход или +1 к удару", 1))
    rz = SL.build("Разум улья", "idle", k)
    put(sc, rz, 120, by, 36)
    bugs = [((), False, 230, by - 40), (("wings",), False, 260, by - 4), (("stinger",), True, 205, by + 2),
            (("scythes",), False, 300, by - 30)]
    for traits, sold, x, yb in bugs:
        b = W.build(traits, 0.05, "idle", soldier=sold, k=k)
        put(sc, b, x, yb, 10)
        thread(sc, (120 + 8, by - 52), (x, yb - 10), sag=-12)
    caps.append((200, by + 10, "Стая на всё поле: +4 к духу каждой особи"))
    tg = flip(F.build("Орудие", "idle", k=1.6 * k))
    put(sc, tg, 720, by, 34)
    ring(sc, 720, by + 2, 34, 8)
    top = by - (tg.oy - int(np.nonzero(tg.a.any(axis=1))[0].min()))
    sigil(sc, 716, top - 14, 10)
    for traits, sold, x in ((("horn",), True, 600), ((), False, 640), (("jumper",), False, 572)):
        put(sc, W.build(traits, -0.05, "attack", soldier=sold, k=k), x, by + (0 if sold else -2), 10)
    for x in (600, 640, 572):
        thread(sc, (x + 6, by - 24), (700, by - 70), sag=10, k=0.6)
    caps.append((660, by + 10, "Метка: рой бьёт её первым и на 1 сильнее"))

    # ---- Пожиратель: growing
    y0 += RH
    by = y0 + RH - 44
    heads.append((y0, "Пожиратель", "Рост — каждые 2 съеденных тела, свои тоже", "развитие: стартует крупнее, растёт с каждого тела или лечится вдвое", 2))
    xs = (110, 410, 760)
    import swarm_effects as E
    dead = lambda sd: E.lit(W.build((), 0.0, "idle", False, k=k, genes=W.genes_for(sd)), (40, 22, 22), 0.6)
    put(sc, dead(41), xs[0] + 74, by + 4, 0)                    # its own dead, in its jaws
    put(sc, dead(42), xs[0] + 96, by - 6, 0)
    for j, (st, p) in enumerate(((0, "attack"), (1, "idle"), (2, "attack"))):
        spr = SL.build("Пожиратель", p, k, stage=st)
        put(sc, spr, xs[j], by, spr.w * 0.38)
        caps.append((xs[j], by + 10, ("размер 5: ест погибших своих", "размер 6: здоровье ×1,4, +2 к удару", "размер 7: ещё раз")[j]))
    arrow(sc, 205, 290, by - 40)
    arrow(sc, 525, 610, by - 40)
    caps.append((248, by - 62, "2 тела"))
    caps.append((568, by - 62, "ещё 2"))

    # ---- Кукушка: the egg-layer and the changeling
    y0 += RH
    by = y0 + RH - 44
    heads.append((y0, "Кукушка", "Яйцеклад и Подкидыш", "развитие: личинок 3, заражает и яд скорпионов, или подкидышей двое", 3))
    ku = SL.build("Кукушка", "attack", k)
    put(sc, ku, 95, by, 24)
    inv = flip(GH.build(LH.INVENTOR, "idle", 0.9 * k))
    put(sc, inv, 142, by, 14)
    spots(sc, 140, by - 30, [(0, 0), (-3, 6), (2, 12), (-1, -8)])
    caps.append((130, by + 10, "пробивший удар заражает"))
    dead = flip(GH.build(LH.INVENTOR, "broken", 0.9 * k))
    put(sc, dead, 330, by, 16)
    splat(sc, 330, by + 2, 26)
    for dx in (-30, 30):
        put(sc, flip(SL.build("личинка", "attack", k)) if dx > 0 else SL.build("личинка", "attack", k), 330 + dx, by + 2, 8)
    caps.append((330, by + 10, "погиб — выпускает 2 личинки"))
    gx = 548                                           # a machine is a nest: eggs ripen in the warmth of its furnace
    put(sc, flip(F.build("Орудие", "idle", k=1.6 * k)), gx, by, 30)
    spots(sc, gx - 6, by - 64, [(0, 0), (-8, 6), (6, 10), (-2, 18), (10, -4)])
    put(sc, flip(SL.build("личинка", "attack", k)), gx - 22, by - 58, 0)
    put(sc, SL.build("личинка", "attack", k), gx - 64, by + 2, 8)
    put(sc, flip(SL.build("личинка", "idle", k)), gx + 40, by + 4, 8)
    caps.append((gx - 20, by + 10, "в машине — гнездо: личинки лезут из решёток"))
    for g, x in (("Страж", 700), ("Мудрец", 770)):
        put(sc, flip(F.build(g, "idle", k=F.FRAMES[g][0] * k * 0.8)), x, by, 30)
    splat(sc, 870, by + 2, 16, col=hexc("#6a5038"), k=0.8)
    put(sc, flip(W.build((), 0.0, "attack", k=k)), 868, by, 8)
    caps.append((800, by + 10, "Подкидыш: рабочая в тылу врага"))

    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Рой: способности лидеров на поле", font=ft, fill=INK)
    d.text((24, 60), "В настоящем соотношении размеров (увеличено). Рой идёт слева направо; враги смотрят навстречу.",
           font=fr, fill=MUT)
    for y0, name, ab, dev, i in heads:
        col = tuple(int(c) for c in hexc(SL.ACCENT[i]))
        d.text((24, (y0 + 4) * S), name, font=fh, fill=col)
        x = 24 + d.textlength(name, font=fh) + 12
        d.text((x, (y0 + 4) * S + 4), ab, font=fbs, fill=INK)
        d.text((x + d.textlength(ab, font=fbs) + 14, (y0 + 4) * S + 5), dev, font=fr, fill=MUT)
    for x, y, t in caps:
        if t not in ("2 тела", "ещё 2"):            # captions go under the lowest thing standing on that ground
            y = max([bot for b, bot in LOWS if abs(b - (y - 10)) < 50] + [y - 10]) + 5
        d.text((x * S - d.textlength(t, font=fr) / 2, y * S), t, font=fr, fill=INK)
    img.save(out("swarm_abilities.png"))
    print("swarm_abilities.png", img.size)


if __name__ == "__main__":
    sheet()
