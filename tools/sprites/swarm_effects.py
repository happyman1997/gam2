"""The swarm's form abilities going off in battle, in the battle's own scale (zoomed): Строй, Полёт, Жало, Плевок and
bursting, Разгон, Шипы and curling up, Прыжок, Серпы, Вспышка, Пожирание — and what gigantism blows each of them up
into. The swarm comes from the left, its enemies (the Foundry: golems, and its human leaders for what only works on
the living) face it from the right.

    python3 tools/sprites/swarm_effects.py      -> out/swarm_forms.gif, out/swarm_giants.gif, out/swarm_effects.png
"""
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
from r3d import Model, Mat, render, rot_z, rot_x, rot_y, I3
import swarm1 as W
import swarm_leaders as SL
import frames as F
import golems_h as GH
import leaders_h as LH
from battle import shadow, flash
from animate_duel import background
from paths import font, out

Z = 1.3                                   # zoom over the battle scale, the same for everyone
PW, PH, GY = 380, 200, 168                # a panel and its ground line
CW = 50 * Z                               # a battle cell, zoomed
ACID = hexc("#a8ff60")
POISON = hexc("#9ae030")
GOLD = hexc("#f0c860")
WHITE = hexc("#fff4dc")
STAR = hexc("#ffe080")


# ---------------------------------------------------------------- the cast
@lru_cache(maxsize=None)
def bug(traits=(), pose="idle", soldier=False, giant=False, hue=0.0, seed=7):
    t = tuple(traits) + (("giant",) if giant else ())
    return W.build(t, hue, pose, soldier, k=Z, genes=W.genes_for(seed))


def mirror(spr):
    f = spr.flipped()
    f.ox, f.oy = spr.w - 1 - spr.ox, spr.oy
    return f


@lru_cache(maxsize=None)
def golem(name, pose="idle"):
    return mirror(F.build(name, pose, k=F.FRAMES[name][0] * Z))


@lru_cache(maxsize=None)
def human(name="Изобретатель", pose="idle"):
    S = {"Изобретатель": (LH.INVENTOR, 0.9), "Зодчий": (LH.ZODCHIY, 1.05)}[name]
    return mirror(GH.build(S[0], pose, S[1] * Z))


@lru_cache(maxsize=None)
def mason(pose="idle"):
    return mirror(GH.build(GH.MASON, pose, 0.85 * Z))


@lru_cache(maxsize=None)
def ball(giant=False, roll=0.0):
    """A curled-up isopod: its plates closed into a ball."""
    m = Model()
    mc = Mat(W.chitin(0.0, "carapace"))
    plate = Mat(W.chitin_shift(mc, -0.18, sat=0.55, light=1.35))
    R = 4.6
    for i in range(9):
        a = roll + i * 2 * np.pi / 9
        c = np.array((np.cos(a) * R * 0.55, R + np.sin(a) * R * 0.55, 0))
        m.ell(c, (1.9, 1.9, 4.4), plate, rot_z(a))
        W.spike(m, c + np.array((np.cos(a), np.sin(a), 0)) * 1.6, c + np.array((np.cos(a), np.sin(a), 0)) * 4.0, 0.6, plate)
    m.ell((0, R, 0), (R * 0.75, R * 0.75, 3.8), mc)
    s = SL.SCALE[3 if giant else 1] * Z
    w, h, ox, oy = int(40 * s), int(36 * s), int(20 * s), int(30 * s)
    spr = W.rim_light(render(m.scaled(s), w, h, ox, oy, **W.STYLE1))
    spr.ox, spr.oy = ox, oy
    return SL.trim(spr)


def lit(spr, col, k):
    f = Sprite(spr.w, spr.h)
    f.rgb, f.a = spr.rgb * (1 - k) + np.array(col, float) * k, spr.a.copy()
    f.ox, f.oy = spr.ox, spr.oy
    return f


# ---------------------------------------------------------------- 2D effects on the panel
def dot(sc, x, y, col, k=1.0, r=0):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            xx, yy = int(round(x)) + dx, int(round(y)) + dy
            if 0 <= xx < sc.w and 0 <= yy < sc.h:
                sc.rgb[yy, xx] = sc.rgb[yy, xx] * (1 - k) + col * k


def blob(sc, x, y, r, col, k=0.95, glow=0.5):
    e = ((sc.xx - x) / r) ** 2 + ((sc.yy - y) / (r * 0.85)) ** 2
    sel = e <= 1
    sc.rgb[sel] = sc.rgb[sel] * (1 - k) + col * k
    hi = ((sc.xx - x + r * 0.35) / (r * 0.4)) ** 2 + ((sc.yy - y + r * 0.35) / (r * 0.35)) ** 2 <= 1
    sc.rgb[hi & sel] = np.minimum(255, col * 1.25 + 30)
    sc.glow(x, y, r * 3, col, glow)


def splash(sc, x, y, rx, col, k=0.7):
    e = ((sc.xx - x) / rx) ** 2 + ((sc.yy - y) / (rx * 0.3)) ** 2
    th = BAYER[sc.yy % 4, sc.xx % 4]
    sel = (e <= 1) & (th < 0.75)
    sc.rgb[sel] = sc.rgb[sel] * (1 - k) + col * k
    sc.glow(x, y - 4, rx * 1.4, col, 0.45)


def drops(sc, x, y, col, n=7, R=14, seed=0, up=0):
    rnd = np.random.RandomState(seed)
    for _ in range(n):
        a = rnd.uniform(-np.pi, 0)
        rr = rnd.uniform(0.4, 1.0) * R
        dot(sc, x + np.cos(a) * rr, y + np.sin(a) * rr * 0.8 - up, col, r=1)


def bubbles(sc, x, y, col=POISON, n=5, seed=0, h=26):
    rnd = np.random.RandomState(seed)
    for i in range(n):
        bx, by = x + rnd.uniform(-9, 9), y - rnd.uniform(0, h)
        for t in np.linspace(0, 2 * np.pi, 10):
            dot(sc, bx + np.cos(t) * 2, by + np.sin(t) * 2, col)
        sc.glow(bx, by, 6, col, 0.2)


def burst(sc, x, y, r, col=WHITE, k=0.9):
    """A hit: a white star of short rays and a glow."""
    for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
        for t in np.linspace(0.3, 1.0, int(r)):
            dot(sc, x + np.cos(a) * r * t, y + np.sin(a) * r * t * 0.8, col, k)
    sc.glow(x, y, r * 2.4, col, 0.6)


def stars(sc, x, y, r=10, n=4, phase=0.0):
    for i in range(n):
        a = phase + i * 2 * np.pi / n
        px, py = x + np.cos(a) * r, y + np.sin(a) * r * 0.35
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            dot(sc, px + dx, py + dy, STAR)
        sc.glow(px, py, 5, STAR, 0.3)


def ring(sc, x, y, rx, col, k=0.8, ry=None):
    ry = rx * 0.32 if ry is None else ry
    for t in np.linspace(0, 2 * np.pi, int(7 * rx)):
        dot(sc, x + np.cos(t) * rx, y + np.sin(t) * ry, col, k)
    sc.glow(x, y, rx, col, 0.3)


def trail(sc, pts, col, every=2, k=0.8):
    for i, (x, y) in enumerate(pts):
        if i % every == 0:
            dot(sc, x, y, col, k)


def arc_pts(x0, y0, x1, y1, h, n=40):
    t = np.linspace(0, 1, n)
    return list(zip(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t - h * 4 * t * (1 - t)))


def speed(sc, x, y, n=4, L=22, col=hexc("#c8bca8")):
    for i in range(n):
        yy = y - 6 - i * 5
        for xx in range(int(x - L - i * 3), int(x - i * 3)):
            if xx % 3:
                dot(sc, xx, yy, col, 0.7)


def slash(sc, x, y, r, a0, a1, col=WHITE, w=2):
    for t in np.linspace(a0, a1, int(abs(a1 - a0) * r)):
        for d in range(w):
            dot(sc, x + np.cos(t) * (r - d), y - np.sin(t) * (r - d) * 0.9, col)
    sc.glow(x + np.cos((a0 + a1) / 2) * r, y - np.sin((a0 + a1) / 2) * r, r, col, 0.4)


def lines(sc, a, b, col=GOLD, k=0.8):
    n = int(np.hypot(b[0] - a[0], b[1] - a[1]))
    for i in range(n):
        if i % 3 != 2:
            dot(sc, a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n, col, k)


# ---------------------------------------------------------------- a frame: who stands where, what goes off
def X(c):
    """The x of the centre of cell c (0 — the swarm's front cell)."""
    return 92 + c * CW


def frame(cast, fx=(), text=(), dur=260, key=False):
    return dict(cast=cast, fx=fx, text=text, dur=dur, key=key)


def draw(fr, seed=11):
    sc = Scene(PW, PH)
    sc.rgb[:] = background(PW, PH, seed).rgb
    for c in range(-2, 7):
        x = int(X(c) - CW / 2)
        if 0 <= x < PW:
            sc.rgb[:, x] *= 0.9
    for y in (GY - 22, GY + 18):
        sc.rgb[int(y), :] *= 0.9
    for spr, x, y, *opt in sorted(fr["cast"], key=lambda c: (len(c) > 3, c[2])):     # flyers over everyone
        if not (opt and opt[0] == "air"):
            shadow(sc, x, y if not opt else GY, max(10, spr.w * 0.6), 5)
        sc.blit(spr, int(round(x - spr.ox)), int(round(y - spr.oy)))
    for f in fr["fx"]:
        f(sc)
    return sc


def cast_line(*items):
    return list(items)


# ---------------------------------------------------------------- the forms
def ant_stroy(giant=False):
    t = golem("Орудие")
    if not giant:
        mates = [(bug(seed=2), X(0.4), GY - 16), (bug(seed=3), X(0.5), GY + 14), (bug(seed=4), X(-0.3), GY)]
        hero = lambda p: (bug(pose=p, seed=5), X(1.2) + (6 if p == "attack" else 0), GY)
        base = [(t, X(3), GY)] + mates
        links = lambda sc: [lines(sc, (x, y - 8), (X(1.2), GY - 8)) for _, x, y in mates]
        return [frame(base + [hero("idle")]),
                frame(base + [hero("idle")], fx=[links], text=[(X(1.2), GY - 40, "трое рядом: +1")]),
                frame(base + [hero("attack")], fx=[links, lambda sc: burst(sc, X(3) - 30, GY - 30, 10)],
                      text=[(X(1.2), GY - 40, "+1 к удару")], key=True),
                frame(base + [hero("idle")])]
    g = lambda p: (bug(pose=p, soldier=True, giant=True, seed=9), X(0.6), GY)
    ants = [(X(1.6), GY - 18), (X(1.7), GY + 14), (X(-0.6), GY - 16), (X(-0.5), GY + 16), (X(2.3), GY)]
    base = [(t, X(3.4), GY)]
    aura = lambda sc: ring(sc, X(0.6), GY, CW * 2.1, GOLD, 0.6)
    return [frame(base + [g("idle")] + [(bug(seed=20 + i), x, y) for i, (x, y) in enumerate(ants)]),
            frame(base + [g("idle")] + [(bug(seed=20 + i), x, y) for i, (x, y) in enumerate(ants)], fx=[aura],
                  text=[(X(0.6), GY - 56, "Строй на радиус 2")]),
            frame(base + [g("idle")] + [(bug(pose="attack", seed=20 + i), x + 5, y) for i, (x, y) in enumerate(ants)],
                  fx=[aura, lambda sc: burst(sc, X(3.4) - 32, GY - 30, 10)], text=[(X(0.6), GY - 56, "+1 всем своим")],
                  key=True)]


def wasp_flight(giant=False):
    if not giant:
        front, back = golem("Страж"), golem("Орудие")
        path = arc_pts(X(0), GY - 10, X(2.9), GY - 44, 70)
        base = [(front, X(1.7), GY + 4), (back, X(3.8), GY - 8)]
        out_ = []
        for j, i in enumerate((0, 12, 24, 39)):
            x, y = path[i]
            pose = "attack" if j == 3 else "idle"
            fx = [lambda sc, i=i: trail(sc, path[:i], hexc("#c8c0d8"))]
            if j == 3:
                fx.append(lambda sc: burst(sc, X(3.8) - 34, GY - 52, 10))
            out_.append(frame(base + [(bug(("wings",), pose, seed=6), x, y + 14, "air")], fx=fx, key=j == 3,
                              text=[(X(2.2), 24, "над строем — к стрелку")] if j == 3 else []))
        return out_
    inv = human("Изобретатель")
    gw = lambda p: bug(("wings",), p, soldier=True, giant=True, seed=8)
    base = [(golem("Страж"), X(3.35), GY + 6)]
    return [frame(base + [(inv, X(2.3), GY), (gw("idle"), X(0.4), GY - 10, "air")]),
            frame(base + [(inv, X(2.3), GY), (gw("attack"), X(1.6), GY - 26, "air")], fx=[lambda sc: burst(sc, X(2.3), GY - 40, 8)]),
            frame(base + [(inv, X(1.5), GY - 50, "air"), (gw("idle"), X(1.2), GY - 30, "air")],
                  text=[(X(1.4), 22, "хватает мелкого и уносит")], key=True),
            frame(base + [(inv, X(0.2), GY - 70, "air"), (gw("idle"), X(-0.1), GY - 50, "air")])]


def scorpion_sting(giant=False):
    a, b = human("Изобретатель"), human("Зодчий")
    if not giant:
        s = lambda p: bug(("stinger",), p, soldier=True, seed=4)
        base = [(a, X(2.4), GY)]
        return [frame(base + [(s("idle"), X(1.0), GY)]),
                frame(base + [(s("attack"), X(1.3), GY)], fx=[lambda sc: burst(sc, X(2.4) - 4, GY - 26, 8)], key=True,
                      text=[(X(2.0), 30, "пробил — яд 1–6")]),
                frame(base + [(s("idle"), X(1.0), GY)], fx=[lambda sc: bubbles(sc, X(2.4), GY - 20, seed=1)],
                      text=[(X(2.0), 30, "яд копится")]),
                frame(base + [(s("attack"), X(1.3), GY)], fx=[lambda sc: bubbles(sc, X(2.4), GY - 20, n=10, seed=2)])]
    s = lambda p: bug(("stinger",), p, soldier=True, giant=True, seed=4)
    base = [(a, X(2.5), GY - 10), (b, X(2.9), GY + 14)]
    return [frame(base + [(s("idle"), X(0.8), GY)]),
            frame(base + [(s("attack"), X(1.2), GY)], key=True, text=[(X(2.0), 24, "жало бьёт цель и соседа")],
                  fx=[lambda sc: burst(sc, X(2.5) - 4, GY - 36, 8), lambda sc: burst(sc, X(2.9) - 4, GY - 14, 8)]),
            frame(base + [(s("idle"), X(0.8), GY)], fx=[lambda sc: bubbles(sc, X(2.5), GY - 30, seed=3),
                                                         lambda sc: bubbles(sc, X(2.9), GY - 6, seed=4)])]


def barrel_spit(giant=False):
    if not giant:
        t = golem("Орудие")
        b = lambda p: bug(("acid",), p, seed=3)
        path = arc_pts(X(0) + 16, GY - 16, X(3) - 18, GY - 40, 30)
        mate = (bug(seed=31), X(0.2), GY + 18)
        base = [(t, X(3.2), GY), mate]
        f = [frame(base + [(b("idle"), X(0), GY)])]
        for j, i in enumerate((8, 18, 29)):
            fx = [lambda sc, i=i: trail(sc, path[:i], ACID, 3), lambda sc, i=i: blob(sc, *path[i], 3, ACID)]
            if j == 2:
                fx += [lambda sc: splash(sc, X(3.2) - 10, GY - 30, 14, ACID), lambda sc: drops(sc, X(3.2) - 10, GY - 34, ACID)]
            f.append(frame(base + [(b("attack" if j == 0 else "idle"), X(0), GY)], fx=fx, key=j == 2,
                           text=[(X(2.4), 26, "плевок на 3 клетки: −броня")] if j == 2 else []))
        hit = lit(b("idle"), WHITE, 0.6)
        f.append(frame([(t, X(3.2), GY), (lit(mate[0], ACID, 0.4), mate[1], mate[2]), (hit, X(0), GY)],
                       fx=[lambda sc: splash(sc, X(0), GY, 46, ACID), lambda sc: drops(sc, X(0), GY - 10, ACID, 14, 30, 2)],
                       text=[(X(1.0), 26, "гибнет — лопается на всех соседей")], dur=420))
        return f
    t1, t2 = golem("Орудие"), golem("Мудрец")
    b = lambda p: bug(("acid",), p, soldier=True, giant=True, seed=3)
    path = arc_pts(X(0) + 26, GY - 30, X(3.2), GY - 30, 46)
    base = [(t1, X(3.0), GY - 14), (t2, X(3.6), GY + 16)]
    f = [frame(base + [(b("idle"), X(0), GY)])]
    for j, i in enumerate((12, 29)):
        f.append(frame(base + [(b("attack"), X(0), GY)], fx=[lambda sc, i=i: trail(sc, path[:i], ACID, 3),
                                                              lambda sc, i=i: blob(sc, *path[i], 5, ACID)]))
    f.append(frame(base + [(b("idle"), X(0), GY)], key=True, text=[(X(2.2), 24, "по клетке и всем соседним")],
                   fx=[lambda sc: splash(sc, X(3.3), GY, 70, ACID), lambda sc: drops(sc, X(3.0), GY - 50, ACID, 12, 24, 3),
                       lambda sc: drops(sc, X(3.6), GY - 24, ACID, 12, 24, 4)]))
    return f


def beetle_charge(giant=False):
    if not giant:
        g = golem("Страж")
        b = lambda p: bug(("horn",), p, soldier=True, seed=5)
        return [frame([(g, X(2.6), GY), (b("idle"), X(-0.4), GY)]),
                frame([(g, X(2.6), GY), (b("idle"), X(0.8), GY)], fx=[lambda sc: speed(sc, X(0.8) - 20, GY)]),
                frame([(g, X(2.6), GY), (b("attack"), X(1.6), GY)], fx=[lambda sc: speed(sc, X(1.6) - 20, GY),
                                                                         lambda sc: burst(sc, X(2.6) - 46, GY - 18, 12)],
                      text=[(X(1.8), 26, "первый удар ×1,5, дробящий")], key=True),
                frame([(lit(g, WHITE, 0.15), X(3.1), GY), (b("idle"), X(1.6), GY)], text=[(X(1.8), 26, "и отбрасывает")])]
    b = lambda p: bug(("horn",), p, soldier=True, giant=True, seed=5)
    inv, mas = human("Изобретатель"), mason()
    down = human("Изобретатель", "broken")
    return [frame([(inv, X(1.9), GY), (mas, X(3.0), GY), (b("idle"), X(-0.2), GY)]),
            frame([(inv, X(1.9), GY), (mas, X(3.0), GY), (b("attack"), X(1.4), GY)],
                  fx=[lambda sc: speed(sc, X(1.4) - 30, GY, 5, 30), lambda sc: burst(sc, X(1.9), GY - 20, 10)]),
            frame([(down, X(1.6), GY + 10), (lit(mason("broken"), WHITE, 0.3), X(3.2), GY), (b("attack"), X(2.6), GY)],
                  fx=[lambda sc: speed(sc, X(2.6) - 30, GY, 5, 40), lambda sc: burst(sc, X(3.1), GY - 24, 10)],
                  text=[(X(2.0), 24, "насквозь, давит всех на пути")], key=True),
            frame([(down, X(1.6), GY + 10), (mason("broken"), X(3.2), GY + 6), (b("idle"), X(4.2), GY)])]


def isopod_thorns(giant=False):
    if not giant:
        g = lambda p: golem("Страж", p)
        iso = bug(("carapace",), soldier=True, seed=6)
        return [frame([(g("idle"), X(2.2), GY), (iso, X(0.9), GY)]),
                frame([(g("attack"), X(2.0), GY), (lit(iso, WHITE, 0.5), X(0.9), GY)], key=True,
                      fx=[lambda sc: [dot(sc, X(1.3) + i * 7, GY - 14 - i * 5, WHITE, r=1) for i in range(5)],
                          lambda sc: burst(sc, X(1.9), GY - 40, 8, hexc("#ff7060"))],
                      text=[(X(1.4), 24, "ударил вплотную — шипы в ответ")]),
                frame([(g("idle"), X(2.2), GY), (ball(), X(0.9), GY)], text=[(X(1.4), 24, "ранена — свернулась: +3 брони")]),
                frame([(g("attack"), X(2.0), GY), (ball(), X(0.9), GY)], fx=[lambda sc: burst(sc, X(1.1), GY - 14, 7, hexc("#b8b8c8"))])]
    inv, mas = human("Изобретатель"), mason()
    out_ = [frame([(inv, X(1.6), GY), (mas, X(2.8), GY), (ball(True, 0.0), X(0.0), GY)])]
    for j, (x, r) in enumerate(((1.0, 0.7), (2.0, 1.4), (3.2, 2.1))):
        cast = [(ball(True, r), X(x), GY)]
        cast.append((human("Изобретатель", "broken") if x > 1.5 else inv, X(1.6), GY + (10 if x > 1.5 else 0)))
        cast.append((mason("broken") if x > 2.7 else mas, X(2.8), GY + (6 if x > 2.7 else 0)))
        out_.append(frame(cast, fx=[lambda sc, x=x: speed(sc, X(x) - 30, GY - 6, 4, 24)], key=j == 1,
                          text=[(X(1.8), 24, "катится шаром, давит мелочь")] if j == 1 else []))
    return out_


def hopper_leap(giant=False):
    if not giant:
        front, back = golem("Страж"), golem("Орудие")
        h = lambda p: bug(("jumper",), p, seed=7)
        path = arc_pts(X(0), GY, X(3.0), GY - 10, 90)
        base = [(front, X(1.7), GY + 6), (back, X(3.9), GY - 6)]
        out_ = [frame(base + [(h("idle"), X(0), GY)])]
        for j, i in enumerate((12, 26, 39)):
            x, y = path[i]
            out_.append(frame(base + [(h("attack"), x, y, "air")], fx=[lambda sc, i=i: trail(sc, path[:i], hexc("#c8d0a0"))],
                              key=j == 2, text=[(X(2.4), 22, "в первом раунде — через строй к дальнему")] if j == 2 else []))
        out_.append(frame(base + [(h("attack"), X(3.0), GY - 10)], fx=[lambda sc: burst(sc, X(3.9) - 26, GY - 40, 9)],
                          text=[(X(2.4), 22, "после прыжка один и окружён")]))
        return out_
    h = lambda p: bug(("jumper",), p, soldier=True, giant=True, seed=7)
    inv, mas = human("Изобретатель"), mason()
    path = arc_pts(X(-0.2), GY, X(2.6), GY, 100)
    base = [(golem("Страж"), X(1.2), GY + 8), (inv, X(3.3), GY - 14), (mas, X(3.4), GY + 18)]
    out_ = [frame(base + [(h("idle"), X(-0.2), GY)])]
    for i in (14, 28):
        out_.append(frame(base + [(h("attack"), *path[i], "air")], fx=[lambda sc, i=i: trail(sc, path[:i], hexc("#c8d0a0"))]))
    out_.append(frame(base + [(h("idle"), X(2.6), GY)], key=True, text=[(X(2.2), 22, "приземление оглушает мелких")],
                      fx=[lambda sc: ring(sc, X(2.6), GY, 60, hexc("#e8d8a0")), lambda sc: stars(sc, X(3.3), GY - 70, 8),
                          lambda sc: stars(sc, X(3.4), GY - 40, 8, phase=0.6)]))
    return out_


def mantis_blades(giant=False):
    if not giant:
        g = golem("Страж")
        m = lambda p: bug(("scythes",), p, soldier=True, seed=8)
        return [frame([(g, X(2.3), GY), (m("idle"), X(1.0), GY)]),
                frame([(g, X(2.3), GY), (m("attack"), X(1.1), GY)], fx=[lambda sc: slash(sc, X(2.0), GY - 40, 26, 2.2, 0.6)],
                      text=[(X(1.6), 24, "первый удар")]),
                frame([(g, X(2.3), GY), (m("attack"), X(1.1), GY)], key=True, text=[(X(1.6), 24, "и второй в том же раунде")],
                      fx=[lambda sc: slash(sc, X(2.0), GY - 40, 26, 2.2, 0.6, hexc("#a0a0a8"), 1),
                          lambda sc: slash(sc, X(2.0), GY - 24, 26, -0.6, 0.9)]),
                frame([(g, X(2.3), GY), (m("idle"), X(1.0), GY)])]
    m = lambda p: bug(("scythes",), p, soldier=True, giant=True, seed=8)
    inv, z = human("Изобретатель"), human("Зодчий")
    base = [(inv, X(2.2), GY - 12), (z, X(2.5), GY + 14)]
    return [frame(base + [(m("idle"), X(0.8), GY)]),
            frame(base + [(m("attack"), X(1.0), GY)], key=True, text=[(X(1.8), 22, "серпы бьют всю клетку")],
                  fx=[lambda sc: slash(sc, X(1.9), GY - 26, 48, 2.0, -0.4, WHITE, 3)]),
            frame([(lit(inv, WHITE, 0.4), X(2.2), GY - 12), (lit(z, WHITE, 0.4), X(2.5), GY + 14), (m("idle"), X(0.8), GY)])]


def firefly_flash(giant=False):
    f = lambda p: bug(("firefly",), p, soldier=giant, giant=giant, seed=9)
    if not giant:
        g1, g2 = golem("Страж"), golem("Мудрец")
        base = [(g1, X(1.8), GY - 12), (g2, X(1.9), GY + 18)]
        return [frame(base + [(f("idle"), X(0.6), GY)]),
                frame([(lit(g1, WHITE, 0.25), X(1.8), GY - 12), (lit(g2, WHITE, 0.25), X(1.9), GY + 18), (f("attack"), X(0.6), GY)],
                      fx=[lambda sc: sc.glow(X(0.6) - 20, GY - 14, 90, hexc("#fff0a0"), 1.0)], key=True,
                      text=[(X(1.4), 22, "вспышка: соседи раунд промахиваются")]),
                frame(base + [(f("idle"), X(0.6), GY)], fx=[lambda sc: stars(sc, X(1.8), GY - 150, 10),
                                                             lambda sc: stars(sc, X(1.9), GY - 110, 10, phase=0.5)],
                      text=[(X(1.4), 22, "промах")])]
    gs = [(golem("Страж"), X(1.7), GY - 14), (golem("Мудрец"), X(2.6), GY + 16), (golem("Орудие"), X(3.4), GY - 10)]
    return [frame(gs + [(f("idle"), X(0.2), GY)]),
            frame([(lit(s, WHITE, 0.25), x, y) for s, x, y in gs] + [(f("attack"), X(0.2), GY)], key=True,
                  fx=[lambda sc: sc.glow(X(0.2) - 20, GY - 18, 190, hexc("#fff0a0"), 1.1)], text=[(X(2.0), 22, "ослепляет в радиусе 2")]),
            frame(gs + [(f("idle"), X(0.2), GY)], fx=[lambda sc: [stars(sc, x, y - 150 if s is gs[0][0] else y - 110, 10, phase=i)
                                                                   for i, (s, x, y) in enumerate(gs)]])]


def devour(giant=False):
    a = lambda p: bug((), p, soldier=True, seed=10)
    inv = human("Изобретатель")
    dead = human("Изобретатель", "broken")
    return [frame([(inv, X(2.0), GY), (a("idle"), X(0.9), GY)]),
            frame([(lit(inv, WHITE, 0.5), X(2.0), GY), (a("attack"), X(1.1), GY)], fx=[lambda sc: burst(sc, X(2.0) - 6, GY - 22, 9)]),
            frame([(dead, X(2.0), GY + 6), (a("attack"), X(1.3), GY)], key=True, text=[(X(1.6), 24, "убил — съедает тело")],
                  fx=[lambda sc: splash(sc, X(2.0), GY + 6, 22, hexc("#7a1a14"), 0.6)]),
            frame([(dead, X(2.0), GY + 6), (a("attack"), X(1.3), GY)], text=[(X(1.6), 24, "+¼ здоровья, после боя — биомасса")],
                  fx=[lambda sc: splash(sc, X(2.0), GY + 6, 22, hexc("#7a1a14"), 0.6),
                      lambda sc: [dot(sc, X(1.1) + dx, GY - 34 - dy, POISON, r=1) for dx, dy in ((0, 0), (8, 10), (-6, 16), (4, 24))]])]


FORMS = [("Муравей · Строй", ant_stroy), ("Оса · Полёт", wasp_flight), ("Скорпион · Жало", scorpion_sting),
         ("Бочонок · Плевок и лопается", barrel_spit), ("Жук · Разгон", beetle_charge),
         ("Мокрица · Шипы, сворачивается", isopod_thorns), ("Кузнечик · Прыжок", hopper_leap),
         ("Богомол · Серпы", mantis_blades), ("Светляк · Вспышка", firefly_flash), ("Пожирание · все формы", devour)]


# ---------------------------------------------------------------- the GIFs
def panels(giant):
    res = []
    for name, fn in FORMS:
        if giant and fn is devour:
            continue
        seq = fn(giant)
        res.append((("Гигант: " if giant else "") + name, seq))
    return res


def render_panel(seq):
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 18)
    imgs = []
    for fr in seq:
        im = draw(fr).image(2)
        d = ImageDraw.Draw(im)
        for x, y, t in fr["text"]:
            tw = d.textlength(t, font=fh)
            x2 = min(max(4, x * 2 - tw / 2), PW * 2 - tw - 4)
            d.rectangle((x2 - 5, y * 2 - 3, x2 + tw + 5, y * 2 + 23), fill=(20, 14, 26))
            d.text((x2, y * 2), t, font=fh, fill=(240, 226, 190))
        imgs.append(im)
    return imgs


def gif(giant, name):
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 20)
    ft_ = ImageFont.truetype(font("PTSerif-Bold.ttf"), 24)
    ps = [(label, render_panel(seq), [f["dur"] for f in seq], next((i for i, f in enumerate(seq) if f["key"]), 0))
          for label, seq in panels(giant)]
    n = max(len(p[1]) for p in ps)
    cols, gap, top, lab = 3, 12, 44, 30
    pw, ph = ps[0][1][0].size
    rows = (len(ps) + cols - 1) // cols
    Wd, Hh = cols * (pw + gap) + gap, top + rows * (ph + lab + gap)
    frames, durs = [], []
    for i in range(n + 2):
        img = Image.new("RGB", (Wd, Hh), (24, 18, 30))
        d = ImageDraw.Draw(img)
        d.text((gap, 8), "Гигантизм раздувает способность формы" if giant else "Рой: способности форм в бою", font=ft_,
               fill=(236, 214, 160))
        for j, (label, imgs, ds, _) in enumerate(ps):
            x, y = gap + (j % cols) * (pw + gap), top + (j // cols) * (ph + lab + gap)
            img.paste(imgs[min(i, len(imgs) - 1)], (x, y))
            d.text((x + 8, y + ph + 4), label, font=fh, fill=(226, 186, 106))
        frames.append(img)
        durs.append(700 if i >= n - 1 else max(p[2][min(i, len(p[2]) - 1)] for p in ps) + 160)
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames]
    pal[0].save(out(name), save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2, optimize=False)
    print(name, frames[0].size, len(frames), "frames")
    return [(label, imgs[key]) for label, imgs, _, key in ps]


def key_sheet(items):
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 17)
    ft_ = ImageFont.truetype(font("PTSerif-Bold.ttf"), 26)
    pw, ph = items[0][1].size
    s = 0.62
    pw, ph = int(pw * s), int(ph * s)
    cols, gap, top, lab = 4, 10, 52, 26
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGB", (cols * (pw + gap) + gap, top + rows * (ph + lab + gap)), (24, 18, 30))
    d = ImageDraw.Draw(img)
    d.text((gap, 12), "Рой в бою: момент срабатывания способности формы и её гигантской версии", font=ft_, fill=(236, 214, 160))
    for j, (label, im) in enumerate(items):
        x, y = gap + (j % cols) * (pw + gap), top + (j // cols) * (ph + lab + gap)
        img.paste(im.resize((pw, ph), Image.NEAREST), (x, y))
        d.text((x + 6, y + ph + 4), label, font=fh, fill=(226, 186, 106))
    img.save(out("swarm_effects.png"))
    print("swarm_effects.png", img.size)


if __name__ == "__main__":
    a = gif(False, "swarm_forms.gif")
    b = gif(True, "swarm_giants.gif")
    items = []
    for (la, ia) in a:
        items.append((la, ia))
        gb = next((x for x in b if x[0] == "Гигант: " + la), None)
        if gb:
            items.append(gb)
    key_sheet(items)
