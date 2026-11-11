"""The swarm's screens, done by hand rather than by a template: text drawn into the picture itself (big, in pixel
letters, the headings dripping and bristling, the swarm's own script under them), live creatures sitting on the
interface, silk and cobwebs, resin running off the plates, old engravings showing through.

    python3 tools/sprites/swarm_hud.py            -> out/brood.png, out/swarm_camp.png, out/swarm_evolution_screen.png,
                                                     out/swarm_deploy.png, out/brood_finds.png, out/brood_pools.png,
                                                     out/swarm_flocks.png, out/swarm_battle_hud.png, out/swarm_aftermath.png,
                                                     out/swarm_leader_pick.png, out/swarm_development_screen.png
    python3 tools/sprites/swarm_hud.py brood      -> one screen (a key of SCREENS: brood, camp, evolution, deploy, finds,
                                                     pools, flocks, battle, aftermath, leader, development)
"""
import sys
from functools import lru_cache
import numpy as np
from kit import *
import swarm1 as W
import swarm_ui as UI
from swarm_ui import letters, scribble, INK, MUTED, GOLD, BIO, RED, GREEN, DARK, VIOLET
import icons as IC
from paths import out

S = 2
WW, HH = 960, 540
PALE = (120, 108, 132)


@lru_cache(maxsize=None)
def bug(traits=(), pose="idle", k=0.55, seed=1, soldier=False, hue=0.0, rare=None, evo=()):
    return W.build(traits, hue, pose, soldier, k=k, genes=W.genes_for(seed), rare=rare, evo=evo)


@lru_cache(maxsize=None)
def leader(name, pose="idle", k=1.0):
    import swarm_leaders as SL
    return SL.build(name, pose, k)


@lru_cache(maxsize=None)
def larva(pose="idle", k=0.6):
    import swarm_leaders as SL
    return SL.build("личинка", pose, k)


@lru_cache(maxsize=None)
def clutch(k=0.7):
    import swarm_abilities as SA
    return SA.render_small(SA.clutch(0), k)


def icon(sc, key, x, y, z=1):
    spr = IC.icon(key, z, "swarm")
    sc.blit(spr, int(x), int(y))
    sc.occ[int(y):int(y) + spr.h, int(x):int(x) + spr.w] |= spr.a
    return spr.w


def put(sc, spr, cx, by, sw=10):
    if sw:
        e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(2.5, sw * 0.2)) ** 2
        sc.rgb[e <= 1] *= 0.6
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


def title(sc, text, sub, x=16, seed=0):
    """The screen's name in dripping, bristling letters, a line under it in the swarm's script."""
    w = letters(sc, text, x, 6, "title", 24, col=(236, 216, 170), col2=(150, 96, 60), jitter=1, drips=6, hairs=9, seed=seed)
    letters(sc, sub, x + w + 16, 6, "text", 16, col=(196, 182, 206), jitter=1, seed=seed + 1)
    scribble(sc, x + w + 16, 27, UI.text_width(sub) + 4, seed=seed + 2)
    return w


def frame_screen(seed):
    UI.WOBBLE[0] = 1.3
    sc = UI.nest(WW, HH, seed)
    return sc


# ---------------------------------------------------------------- the brood: everything hatched, eat the extra
def brood():
    import brood as B
    sc = frame_screen(31)
    UI.engrave(sc, leader("Матка", "idle", 2.2), 640, 560, k=0.8)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 40, 920, 44, "#b06818", n=7, seed=3)
    title(sc, "ВЫВОДОК", "вылупились все. лишних — в пасть.", seed=5)
    # biomass, top right
    icon(sc, "biomass", 742, 8, 2)
    letters(sc, "34", 782, 8, "title", 16, col=(170, 240, 120), col2=(70, 150, 50), jitter=1)
    letters(sc, "биомасса", 822, 6, "text", 16, col=BIO)
    letters(sc, "+5 за съеденных", 822, 22, "text", 16, col=(120, 180, 96))
    # the limit: an abdomen of segments
    total, eaten = B.totals()
    UI.plate(sc, 12, 50, 948, 96)
    letters(sc, "улей тесен:", 24, 58, "text", 16, col=INK)
    letters(sc, f"{total}/{B.LIMIT}", 24, 74, "title", 16, col=(255, 140, 110), col2=(170, 50, 40), jitter=1)
    letters(sc, f"лишних {total - B.LIMIT}, к съедению {eaten}", 132, 74, "text", 16, col=MUTED)
    bx0, bx1 = 322, 938
    sb0, sw = UI.segbar(sc, bx0, 62, bx1, 16, total, B.LIMIT, eaten)
    letters(sc, "предел", sb0 + B.LIMIT * sw, 84, "title", 8, col=(240, 230, 200), align="center")
    UI.drips(sc, 300, 900, 96, "#7a9a30", n=3, seed=7, Lmax=9)
    # the groups: comb cells
    GX0, GY0, GCW, GCH = 12, 104, 232, 96
    for k_, (traits, soldier, chim, hue, name, count, new, badge, eat) in enumerate(B.GROUPS):
        x0, y0 = GX0 + (k_ % 4) * (GCW + 2), GY0 + (k_ // 4) * (GCH + 3)
        UI.cell(sc, x0, y0, x0 + GCW, y0 + GCH, "eat" if eat else ("new" if new else "normal"))
        mut = B.MUTS.get(k_, (None,))[0]
        spr = W.build(traits, hue, "idle", soldier, k=1.25 if soldier else 1.6, chimera=chim, genes=W.genes_for(k_ * 7 + 3), rare=mut)
        if count > 1:
            spr2 = W.build(traits, hue + 0.03, "idle", soldier, k=1.0 if soldier else 1.3, chimera=chim, genes=W.genes_for(k_ * 7 + 4), rare=mut)
            put(sc, spr2, x0 + 30, y0 + GCH - 26, 0)
        put(sc, spr, x0 + 50, y0 + GCH - 10, 12)
        letters(sc, name, x0 + 12, y0 + 6, "text", 16, col=INK, jitter=1, seed=k_)
        cw = letters(sc, f"×{count}", x0 + 100, y0 + 28, "title", 16, col=(236, 220, 190), col2=(160, 130, 100))
        letters(sc, f"{B.pts(B.GROUPS[k_]) * count} оч", x0 + 104 + cw, y0 + 34, "title", 8, col=PALE, outline=False)
        if eat:
            letters(sc, f"съесть {eat}: +{eat * B.pts(B.GROUPS[k_])}", x0 + 100, y0 + 52, "text", 16, col=RED)
        elif new:
            letters(sc, f"новых {new}", x0 + 100, y0 + 52, "text", 16, col=GREEN)
        mark = None
        if k_ in B.MUTS:
            key, m = B.MUTS[k_]
            mark = ("m_" + key, {"мутация Матки": "Матки", "общая мутация": "общая", "гибрид · бесплоден": "бесплоден"}[m],
                    B.MARK_COL[m])
        elif badge:
            mark = (B.KID_ICON[badge], badge, B.BADGE[badge])
        if mark:
            icon(sc, mark[0], x0 + 98, y0 + 70)
            letters(sc, mark[1], x0 + 118, y0 + 71, "text", 16, col=mark[2])
        UI.button(sc, x0 + 204, y0 + 28, x0 + 228, y0 + 50, "blood")
        UI.button(sc, x0 + 204, y0 + 56, x0 + 228, y0 + 78, "chitin")
        letters(sc, "−", x0 + 216, y0 + 31, "text", 16, col=INK, align="center")
        letters(sc, "+", x0 + 216, y0 + 59, "text", 16, col=INK, align="center")
    # natural selection
    UI.plate(sc, 12, 402, 948, 440)
    icon(sc, "selection", 22, 412)
    letters(sc, "кто убивал — тот плодится:", 42, 413, "text", 16, col=INK)
    for i, (name, kills, key) in enumerate(B.SELECTION):
        x = 268 + i * 170
        icon(sc, key, x, 412)
        letters(sc, name, x + 20, 413, "text", 16, col=INK if i else (255, 170, 130))
        UI.meter(sc, x + 84, 418, x + 144, 7, 10, round(10 * kills / 23), "#c04a3a" if i == 0 else "#8a6aa8")
        letters(sc, str(kills), x + 150, 416, "title", 8, col=PALE, outline=False)
    # spending and leaving
    spend = [(12, 236, "Кормить · 10", "feed"), (246, 470, "Эволюция · 15", "evolve"),
             (480, 704, "Ещё кладка · 10", "clutch"), (714, 948, "Перебросить · 5", "reroll")]
    for x0, x1, t, key in spend:
        UI.button(sc, x0, 450, x1, 486, "acid")
        tw = UI.text_width(t)
        icon(sc, key, (x0 + x1) / 2 - tw / 2 - 22, 459)
        letters(sc, t, (x0 + x1) / 2 + 10, 459, "text", 16, col=INK, align="center")
    for x0, x1, t, kind, col in ((12, 236, "Автоотбор", "chitin", INK), (246, 470, "Съесть новых", "chitin", INK),
                                 (714, 948, f"В бой · съешь ещё {total - B.LIMIT - eaten}", "dim", PALE)):
        UI.button(sc, x0, 496, x1, 532, kind)
        letters(sc, t, (x0 + x1) / 2, 505, "text", 16, col=col, align="center")
    letters(sc, "съеденное — биомасса", 592, 498, "text", 16, col=MUTED, align="center")
    scribble(sc, 512, 518, 160, seed=11)
    # the living: an ant walking the limit plate, one let down on silk, eggs in a corner, a wasp resting on «В бой»
    UI.creature(sc, bug((), "idle", 1.0, 41), 272, 52)
    UI.silk(sc, (560, 44), (560, 50), sag=0)
    UI.creature(sc, bug(("ant",), "attack", 0.85, 42, rare="spinner"), 566, 64, shadow=False)
    UI.creature(sc, clutch(0.95), 474, 446)
    UI.creature(sc, larva("idle", 0.85), 40, 498)
    UI.creature(sc, bug(("wings",), "idle", 0.95, 43), 934, 506)
    UI.creature(sc, bug(("horn",), "idle", 0.8, 44), 742, 444)
    UI.cobweb(sc, 958, 444, 34, quad=(-1, 1))
    UI.cobweb(sc, 2, 444, 26, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("brood.png"))
    print("brood.png", img.size)


def wrap(text, width, kind="text", px=16):
    words, lines, cur = text.split(" "), [], ""
    for wd in words:
        if UI.text_width((cur + " " + wd).strip(), kind, px) > width and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    return lines + [cur]


def heading(sc, text, x, y, col=(240, 196, 110), seed=0):
    w = letters(sc, text, x, y, "title", 16, col=col, col2=(170, 110, 50), jitter=1, drips=3, hairs=3, seed=seed)
    return w


# ---------------------------------------------------------------- the camp: the swarm picks a mutation itself
def camp():
    import swarm_screens as SS
    sc = frame_screen(73)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=5)
    title(sc, "ЛАГЕРЬ", "рой линяет. что-то в нём проросло", seed=21)
    # who
    UI.plate(sc, 12, 52, 286, 446, antennae=True)
    heading(sc, "КТО", 26, 64, seed=1)
    for i, (traits, soldier, name, n) in enumerate(SS.CAMP_WHO):
        y0 = 90 + i * 58
        UI.cell(sc, 20, y0, 278, y0 + 52, "hi" if i == 0 else "normal")
        put(sc, W.build(traits, 0.03, "idle", soldier, k=1.1 if soldier else 1.4, genes=W.genes_for(70 + i)), 62, y0 + 46, 12)
        letters(sc, name, 110, y0 + 9, "text", 16, col=GOLD if i == 0 else INK, jitter=1, seed=i)
        letters(sc, f"×{n}", 112, y0 + 30, "title", 8, col=PALE, outline=False)
    # what fell out: three random offers, one of them or nothing
    UI.plate(sc, 296, 52, 652, 446, antennae=True)
    heading(sc, "ЧТО ВЫПАЛО", 310, 64, seed=2)
    letters(sc, "три случайных: бери одно или ничего", 310, 86, "text", 16, col=MUTED)
    offers = [("horn", "Рог", "деталь", "первый удар боя сильнее и дробящий", (236, 224, 196)),
              ("m_spinner", "Прядильные железы", "общая мутация", "паутина на клетке: враг застревает, свои бегают", (206, 206, 222)),
              ("m_nest", "Малое гнездо", "мутация Матки", "погибшая рядом своя роняет яйцо, как у Матки", (240, 200, 90))]
    X, Y = sc.xx, sc.yy
    for k_, (key, name, kind, what, kcol) in enumerate(offers):
        y0 = 110 + k_ * 108
        UI.cell(sc, 306, y0, 642, y0 + 100, "hi" if k_ == 0 else ("mut" if key.startswith("m_") else "normal"))
        ex, ey = 346, y0 + 50                                   # each offer hatched from its own egg
        egg = ((X - ex) / 26) ** 2 + ((Y - ey) / 34) ** 2 <= 1
        sc.rgb[egg] = hexc("#2e3a22")
        sc.rgb[egg & (Y < ey - 6)] = hexc("#46582e")
        sc.rgb[egg & (((X - ex + 8) / 6) ** 2 + ((Y - ey + 18) / 8) ** 2 <= 1)] = hexc("#7a9a48")
        eo, _, _ = UI.edges(egg)
        sc.rgb[eo] = UI.OUTL
        for t in range(9):                                     # the crack it came out of
            cx_, cy_ = ex - 16 + t * 4, ey - 26 + (3 if t % 2 else -1)
            sc.rgb[int(cy_):int(cy_) + 2, int(cx_):int(cx_) + 2] = UI.OUTL
        sc.occ[egg] = True
        sc.light[egg] = 0
        icon(sc, key, ex - 16, ey - 12, 2)
        letters(sc, name, 386, y0 + 10, "text", 16, col=GOLD if k_ == 0 else INK, jitter=1, seed=k_)
        letters(sc, kind, 386, y0 + 28, "title", 8, col=kcol, outline=False)
        for n_, ln in enumerate(wrap(what, 244)):
            letters(sc, ln, 386, y0 + 46 + n_ * 17, "text", 16, col=MUTED if k_ else INK)
    scribble(sc, 316, 434, 200, seed=36)
    # what it becomes
    UI.plate(sc, 662, 52, 948, 446, antennae=True)
    UI.engrave(sc, bug((), "idle", 4.2, 70, soldier=True), 820, 330, col="#2a2234", k=0.9)
    heading(sc, "КАКИМ СТАНЕТ", 676, 64, seed=3)
    put(sc, W.build((), 0.03, "idle", True, k=1.9, genes=W.genes_for(70)), 730, 214, 22)
    put(sc, W.build(("ant", "horn"), 0.03, "idle", True, k=1.9, genes=W.genes_for(70)), 872, 214, 22)
    letters(sc, "сейчас", 730, 222, "text", 16, col=MUTED, align="center")
    letters(sc, "с рогом", 872, 222, "text", 16, col=GOLD, align="center")
    UI.silk(sc, (760, 180), (836, 180), sag=-6, col="#e8c050")
    text = ("Муравей-солдат получает Рог: первый удар боя сильнее и дробящий — против литого металла. "
            "Рог наследуется: в кладках этой линии появятся рога.")
    for n_, ln in enumerate(wrap(text, 262)):
        letters(sc, ln, 676, 254 + n_ * 18, "text", 16, col=INK)
    scribble(sc, 676, 380, 250, seed=31)
    scribble(sc, 676, 392, 180, seed=32)
    # leave / mutate
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Отказаться", 156, 486, "title", 16, col=INK, align="center")
    UI.button(sc, 690, 466, 948, 524, "amber")
    letters(sc, "МУТИРОВАТЬ", 819, 486, "title", 16, col=DARK, col2=(90, 40, 10), outline=False, align="center", jitter=1)
    letters(sc, "выпадает из встреченного", 495, 470, "text", 16, col=MUTED, align="center")
    letters(sc, "в походе; лагерь — подарок", 495, 488, "text", 16, col=MUTED, align="center")
    scribble(sc, 420, 512, 150, seed=33)
    # the living
    UI.creature(sc, bug(("stinger",), "idle", 1.0, 71), 230, 54)
    UI.silk(sc, (474, 44), (474, 84), sag=0)
    UI.creature(sc, larva("idle", 0.8), 478, 98, shadow=False)
    UI.creature(sc, bug(("wings",), "idle", 1.0, 72), 930, 470)
    UI.creature(sc, clutch(0.9), 640, 448)
    UI.cobweb(sc, 2, 448, 28, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_camp.png"))
    print("swarm_camp.png", img.size)


# ---------------------------------------------------------------- the evolution of a form
def evolution():
    import swarm_screens as SS
    import swarm_evo as EV
    sc = frame_screen(71)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=8)
    title(sc, "ЭВОЛЮЦИЯ", "вся форма меняется разом, и нерождённые тоже", seed=23)
    icon(sc, "biomass", 830, 8, 2)
    letters(sc, "39", 870, 10, "title", 16, col=(170, 240, 120), col2=(70, 150, 50), jitter=1)
    UI.plate(sc, 12, 52, 300, 446, antennae=True)
    heading(sc, "ФОРМЫ В РОЕ", 26, 64, seed=4)
    for i, (form, name, n, taken) in enumerate(SS.FORMS_IN_SWARM):
        y0 = 90 + i * 58
        UI.cell(sc, 20, y0, 292, y0 + 52, "hi" if i == SS.CHOSEN else "normal")
        put(sc, W.build(() if form is None else (form,), 0.0, "idle", False, k=1.35, genes=W.genes_for(60 + i), evo=taken), 62, y0 + 46, 12)
        letters(sc, name, 108, y0 + 8, "text", 16, col=GOLD if i == SS.CHOSEN else INK, jitter=1, seed=i)
        letters(sc, f"×{n}  {len(taken)}/3", 110, y0 + 30, "title", 8, col=PALE, outline=False)
        for k_, key in enumerate(taken):
            icon(sc, "evo_" + key, 250 + k_ * 18, y0 + 18)
    form, name, n, taken = SS.FORMS_IN_SWARM[SS.CHOSEN]
    UI.plate(sc, 310, 52, 948, 446, antennae=True)
    UI.engrave(sc, bug((form,), "idle", 5.0, 3), 640, 470, col="#2a2234", k=0.9)
    heading(sc, f"{name.upper()} · {n} ТЕЛ", 326, 64, seed=5)
    letters(sc, "каждая следующая дороже: 15, 25, 40", 326, 86, "text", 16, col=MUTED)
    nxt = SS.COSTS[len(taken)]
    for j, (key, ename, what, look) in enumerate(EV.EVO[form]):
        x0 = 322 + j * 208
        is_taken = key in taken
        UI.cell(sc, x0, 108, x0 + 200, 438, "hi" if j == 1 else ("new" if is_taken else "normal"))
        icon(sc, "evo_" + key, x0 + 12, 118, 2)
        letters(sc, ename, x0 + 50, 120, "text", 16, col=GOLD if j == 1 else INK, jitter=1, seed=j)
        letters(sc, "взята" if is_taken else f"{nxt} биомассы", x0 + 50, 138, "text", 16, col=GREEN if is_taken else BIO)
        for k_, ln in enumerate(wrap(what, 180)):
            letters(sc, ln, x0 + 12, 166 + k_ * 17, "text", 16, col=INK)
        put(sc, W.build((form,), -0.08, "idle", False, k=2.4, genes=W.genes_for(3), evo=(key,)), x0 + 104, 340, 22)
        for k_, ln in enumerate(wrap("на теле: " + look, 180)):
            letters(sc, ln, x0 + 12, 360 + k_ * 17, "text", 16, col=MUTED)
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Назад", 156, 486, "title", 16, col=INK, align="center")
    UI.button(sc, 660, 466, 948, 524, "amber")
    letters(sc, f"ВЗЯТЬ · {nxt}", 804, 486, "title", 16, col=DARK, col2=(90, 40, 10), outline=False, align="center", jitter=1)
    letters(sc, "Разум улья: эволюция", 480, 470, "text", 16, col=MUTED, align="center")
    letters(sc, "дешевле на 1 биомассу", 480, 488, "text", 16, col=MUTED, align="center")
    scribble(sc, 400, 512, 160, seed=34)
    UI.creature(sc, bug((), "idle", 1.0, 73), 200, 54)
    UI.creature(sc, bug(("horn",), "idle", 0.9, 74), 600, 448)
    UI.silk(sc, (700, 44), (700, 62), sag=0)
    UI.creature(sc, bug(("ant",), "attack", 0.85, 75, rare="spinner"), 706, 76, shadow=False)
    UI.cobweb(sc, 958, 448, 30, quad=(-1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_evolution_screen.png"))
    print("swarm_evolution_screen.png", img.size)


# ---------------------------------------------------------------- deployment by flocks
def deploy():
    import swarm_screens as SS
    import frames as F
    sc = frame_screen(75)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=5, seed=9)
    title(sc, "РАССТАНОВКА", "стаи ложатся на поле; выходит вся армия", seed=25)
    letters(sc, "Литейщик: 4 голема", 944, 8, "text", 16, col=(214, 196, 150), align="right")
    UI.plate(sc, 600, 50, 948, 92)
    icon(sc, "matka", 610, 56, 2)
    letters(sc, "СТАИ МАТКИ: ТЕСНЫЕ", 648, 57, "title", 8, col=GOLD, outline=False)
    letters(sc, "в клетке до 6 мелких, а не 4", 648, 70, "text", 16, col=INK)
    CW_, CH_, GX0, GY0 = SS.CW_, SS.CH_, SS.GX0, SS.GY0 + 4
    cols, rows = 21, 12
    for c in range(cols):
        for r in range(rows):
            x, y = GX0 + c * CW_, GY0 + r * CH_
            if 9 <= c < 13:
                continue
            col = hexc("#9a8ab8") if c < 9 else hexc("#c9b27a")
            for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
                sc.rgb[y + dy, x + dx] = sc.rgb[y + dy, x + dx] * 0.55 + col * 0.45
    rnd = np.random.default_rng(3)
    items = []
    for k_, (traits, soldier, name, n, cells, col, placed) in enumerate(SS.FLOCKS):
        if not placed:
            continue
        m = np.zeros((HH, WW), bool)
        for (c, r) in cells:
            m[GY0 + r * CH_ + 2:GY0 + (r + 1) * CH_ - 2, GX0 + c * CW_ + 2:GX0 + (c + 1) * CW_ - 2] = True
        edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        sc.rgb[m] = sc.rgb[m] * 0.8 + hexc(col) * 0.2
        sc.rgb[edge & ((sc.xx + sc.yy) % 3 != 0)] = hexc(col)
        per = max(1, int(np.ceil(n / max(1, len(cells)))))
        placed_n = 0
        for (c, r) in cells:
            for j in range(per):
                if placed_n >= n:
                    break
                if per > 4:                                         # a tight cell: three abreast
                    x = GX0 + c * CW_ + 8 + (j % 3) * 12 + (j // 3) * 5 + rnd.uniform(-2, 2)
                    y = GY0 + r * CH_ + 13 + (j // 3) * 11 + rnd.uniform(-1, 1)
                else:
                    x = GX0 + c * CW_ + 10 + (j % 2) * 18 + rnd.uniform(-3, 3)
                    y = GY0 + r * CH_ + 14 + (j // 2) * 10 + rnd.uniform(-2, 2)
                items.append((y, W.build(traits, rnd.uniform(-0.1, 0.1), "idle", soldier, k=SS.ZD, genes=W.genes_for(k_ * 50 + placed_n)), x))
                placed_n += 1
    for (y, spr, x) in sorted(items, key=lambda t: t[0]):
        sc.blit(spr, int(x - spr.ox), int(y - spr.oy))
    q = W.queen(0.0, "idle", k=SS.ZD)
    sc.blit(q, int(GX0 + 1.6 * CW_ - q.ox), int(GY0 + 6.6 * CH_ - q.oy))
    for name_, c, r in (("Страж", 14.5, 6.2), ("Орудие", 15.0, 2.6), ("Горн", 15.2, 9.8), ("Механик", 17.4, 6.0)):
        g = F.build(name_, "idle", k=F.FRAMES[name_][0] * SS.ZD)
        f_ = g.flipped()
        f_.ox, f_.oy = g.w - 1 - g.ox, g.oy
        sc.blit(f_, int(GX0 + c * CW_ - f_.ox), int(GY0 + r * CH_ - f_.oy))
    UI.silk(sc, (GX0 + 4 * CW_ + 30, GY0 + 4 * CH_ + 15), (GX0 + 5 * CW_ + 8, GY0 + 4 * CH_ + 15), sag=4, col="#7ae040")
    for k_, (traits, soldier, name, n, cells, col, placed) in enumerate(SS.FLOCKS):
        if not placed:
            continue
        c = min(cells, key=lambda t: (t[1], t[0]))
        letters(sc, f"{name} ×{n}", GX0 + c[0] * CW_, GY0 + c[1] * CH_ - 18, "text", 16, col=tuple(int(v) for v in hexc(col)),
                jitter=1, seed=k_)
    letters(sc, "← пара: кладка", GX0 + 6 * CW_ + 10, GY0 + 4 * CH_ + 10, "text", 16, col=(130, 230, 90))
    UI.plate(sc, 4, HH - 92, WW - 4, HH - 2)
    for k_, (traits, soldier, name, n, cells, col, placed) in enumerate([fl for fl in SS.FLOCKS if not fl[6]]):
        x0 = 12 + k_ * 150
        UI.cell(sc, x0, HH - 84, x0 + 142, HH - 10, "normal", col=col)
        put(sc, W.build(traits, 0.0, "idle", soldier, k=1.1, genes=W.genes_for(90 + k_)), x0 + 34, HH - 22, 10)
        for j, ln in enumerate(wrap(name.replace("-", "- "), 76)):
            letters(sc, ln.replace("- ", "-"), x0 + 62, HH - 80 + j * 16, "text", 16, col=INK, jitter=1, seed=k_ + j)
        letters(sc, f"×{n}", x0 + 62, HH - 42, "title", 8, col=GOLD, outline=False)
        letters(sc, "не стоит", x0 + 62, HH - 28, "title", 8, col=PALE, outline=False)
    for k_, t in enumerate(("в линию", "в кулак", "разделить", "как в прошлый")):
        x0 = 316 + k_ * 158
        UI.button(sc, x0, HH - 66, x0 + 150, HH - 26, "chitin")
        letters(sc, t, x0 + 75, HH - 54, "text", 16, col=INK, align="center")
    UI.creature(sc, bug((), "idle", 0.9, 76), 420, HH - 92)
    UI.creature(sc, bug(("wings",), "idle", 0.9, 77), 930, HH - 94)
    UI.cobweb(sc, 958, 46, 40, quad=(-1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_deploy.png"))
    print("swarm_deploy.png", img.size)


# ---------------------------------------------------------------- the brood's finds, and what the leaders' pools add
def finds():
    import brood as B
    from swarm_abilities import render_small
    WW_, HH_ = 960, 300
    UI.WOBBLE[0] = 1.3
    sc = UI.nest(WW_, HH_, 33)
    UI.wing(sc, 0, 0, WW_, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=5, seed=12)
    title(sc, "НАХОДКИ", "иногда вместо кладки — подарок боя", seed=27)
    CW_ = 184
    xs = [12 + i * (CW_ + 4) for i in range(5)]
    for x0 in xs:
        UI.cell(sc, x0, 52, x0 + CW_, 292, "find")
    by = 196
    x0 = xs[0]
    for j, dx in enumerate((46, 92, 140)):
        put(sc, W.build(("stinger",), -0.08 + 0.01 * j, "idle", False, k=1.9, genes=W.genes_for(3)), x0 + dx, by - (16 if j == 1 else 0), 16)
    x0 = xs[1]
    put(sc, W.build(("ant", "horn"), 0.05, "idle", False, k=1.8, genes=W.genes_for(8)), x0 + 32, by, 12)
    put(sc, render_small(B.cocoon_model().scaled(1.5), 2.2), x0 + 90, by, 20)
    put(sc, W.build(("ant", "horn"), 0.05, "idle", True, k=1.8, genes=W.genes_for(8)), x0 + 148, by, 18)
    x0 = xs[2]
    for j, (dx, dy) in enumerate(((50, 0), (96, -18), (138, 2))):
        put(sc, W.build(("firefly",), 0.08 * (j - 1), "idle", False, k=1.9, genes=W.genes_for(40 + j)), x0 + dx, by + dy, 14)
    x0 = xs[3]
    put(sc, render_small(B.giant_egg_model(), 2.4, size=2), x0 + 92, by, 40)
    x0 = xs[4]
    put(sc, W.build(("acid",), 0.0, "idle", False, k=1.9, chimera="hand", genes=W.genes_for(50)), x0 + 54, by, 16)
    put(sc, W.build(("ant",), 0.05, "idle", False, k=1.9, chimera="face", genes=W.genes_for(51)), x0 + 134, by, 14)
    icons_ = ["evolve", "larva", "ant", "clutch", "hand"]
    for i, (x0, (name, when, what)) in enumerate(zip(xs, B.FINDS)):
        cx = x0 + CW_ / 2
        icon(sc, icons_[i], x0 + 10, 60)
        for j, ln in enumerate(wrap(name, CW_ - 40)):
            letters(sc, ln, x0 + 30, 61 + j * 17, "text", 16, col=GOLD, jitter=1, seed=i + j)
        for j, ln in enumerate(wrap(when, CW_ - 16)):
            letters(sc, ln, cx, 96 + j * 16, "text", 16, col=MUTED, align="center")
        for j, ln in enumerate(wrap(what, CW_ - 16)):
            letters(sc, ln, cx, by + 12 + j * 17, "text", 16, col=INK, align="center")
    UI.creature(sc, bug((), "idle", 0.9, 81), 300, 54)
    UI.cobweb(sc, 958, 46, 30, quad=(-1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("brood_finds.png"))
    print("brood_finds.png", img.size)


def pools():
    import brood as B
    import swarm_leaders as SL
    import swarm_abilities as SA
    import swarm_effects as E
    WW_, HH_ = 960, 360
    UI.WOBBLE[0] = 1.3
    sc = UI.nest(WW_, HH_, 35)
    UI.wing(sc, 0, 0, WW_, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=5, seed=14)
    title(sc, "ПУЛЫ", "что лидеры приносят в выводок", seed=29)
    PW_ = 232
    xs = [12 + i * (PW_ + 2) for i in range(4)]
    for x0 in xs:
        UI.cell(sc, x0, 52, x0 + PW_, 352, "find")
    heads = [("Брачный полёт", "пару выбираешь сам", "m_flight"), ("Гибрид", "бесплоден", "m_hybrid"),
             ("Откормленная", "у Пожирателя", "m_fattened"), ("Чей пул", "тот и цвет", "m_nest")]
    for x0, (h, sub, key) in zip(xs, heads):
        icon(sc, key, x0 + 12, 60, 2)
        letters(sc, h, x0 + 50, 62, "text", 16, col=GOLD, jitter=1, seed=len(h))
        letters(sc, sub, x0 + 50, 80, "text", 16, col=MUTED)
    # mating flight
    x0 = xs[0]
    put(sc, W.build(("ant",), 0.05, "attack", False, k=1.9, genes=W.genes_for(61), rare="flight"), x0 + 60, 178, 14)
    for j, (tr, sol, sd, nm) in enumerate(((("horn",), True, 62, "жук"), (("stinger",), False, 63, "скорпион"), (("wings",), False, 64, "оса"))):
        cy = 110 + j * 62
        UI.cell(sc, x0 + 128, cy, x0 + 222, cy + 56, "hi" if j == 1 else "normal")
        put(sc, W.build(tr, 0.0, "idle", sol, k=1.0 if sol else 1.3, genes=W.genes_for(sd)), x0 + 160, cy + 48, 8)
        letters(sc, nm, x0 + 175, cy + 3, "text", 16, col=GOLD if j == 1 else MUTED, align="center")
    UI.silk(sc, (x0 + 76, 134), (x0 + 132, 196), sag=8, col="#f0c040")
    for j, ln in enumerate(("с кем —", "решаешь ты,", "не стык стай")):
        letters(sc, ln, x0 + 12, 216 + j * 17, "text", 16, col=INK)
    UI.button(sc, x0 + 14, 300, x0 + PW_ - 14, 338, "amber")
    letters(sc, "СПАРИТЬ", x0 + PW_ / 2, 312, "title", 16, col=DARK, col2=(90, 40, 10), outline=False, align="center")
    # hybrid
    x0 = xs[1]
    put(sc, W.build(("wings",), 0.0, "idle", False, k=1.3, genes=W.genes_for(65)), x0 + 60, 140, 8)
    put(sc, W.build(("stinger",), -0.08, "idle", False, k=1.3, genes=W.genes_for(66)), x0 + 170, 140, 10)
    UI.silk(sc, (x0 + 70, 128), (x0 + 160, 128), sag=6, col="#c0c0d0")
    letters(sc, "оса × скорпион", x0 + PW_ / 2, 150, "text", 16, col=MUTED, align="center")
    put(sc, W.build(("wings", "stinger"), -0.04, "idle", False, k=2.1, genes=W.genes_for(67), rare="hybrid"), x0 + 100, 252, 16)
    ex, ey = x0 + 190, 224
    E.blob(sc, ex, ey, 5, hexc("#a8d060"), glow=0.1)
    for dd in range(-8, 9):
        E.dot(sc, ex + dd, ey + dd * 0.9, hexc("#e04a3a"))
        E.dot(sc, ex + dd, ey - dd * 0.9, hexc("#e04a3a"))
    for j, ln in enumerate(("тело осы, жало скорпиона;", "в пары не встаёт —", "каждого выводят заново")):
        letters(sc, ln, x0 + PW_ / 2, 270 + j * 17, "text", 16, col=INK, align="center")
    # fattened
    x0 = xs[2]
    put(sc, W.build((), 0.05, "idle", False, k=1.9, genes=W.genes_for(68), rare="fattened"), x0 + 56, 168, 14)
    UI.meter(sc, x0 + 20, 186, x0 + 96, 8, 5, 3, "#e8c070")
    letters(sc, "жир: 3 боя", x0 + 20, 198, "text", 16, col=(232, 192, 112))
    SA.arrow(sc, x0 + 104, x0 + 128, 140)
    put(sc, SL.build("Пожиратель", "idle", 0.42, stage=1), x0 + 180, 170, 18)
    for j, ln in enumerate(("дольше держишь —", "больше он вырастет;", "пока жива — плодится")):
        letters(sc, ln, x0 + 16, 224 + j * 17, "text", 16, col=INK)
    UI.button(sc, x0 + 14, 300, x0 + PW_ - 14, 338, "blood")
    letters(sc, "СКОРМИТЬ", x0 + PW_ / 2, 312, "title", 16, col=INK, align="center")
    # whose pool
    x0 = xs[3]
    rows = [("m_nest", "Матки", B.POOL_COL["Матка"]), ("m_psi_gland", "Разума", B.POOL_COL["Разум улья"]),
            ("m_sated", "Пожирателя", B.POOL_COL["Пожиратель"]), ("m_spores", "Кукушки", B.POOL_COL["Кукушка"]),
            ("m_spinner", "общая", B.POOL_COL["общая"]), ("m_hybrid", "бесплоден", B.POOL_COL["бесплоден"])]
    for k_, (key, t, col) in enumerate(rows):
        y = 108 + k_ * 36
        icon(sc, key, x0 + 18, y, 2)
        letters(sc, t, x0 + 60, y + 8, "text", 16, col=col, jitter=1, seed=k_)
    scribble(sc, x0 + 18, 334, 190, seed=41)
    UI.creature(sc, bug(("wings",), "idle", 0.9, 82), 700, 54)
    UI.cobweb(sc, 2, 46, 30, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("brood_pools.png"))
    print("brood_pools.png", img.size)


# ---------------------------------------------------------------- how each leader changes the flocks
def flocks():
    import swarm_effects as E
    WW_, HH_ = 960, 330
    UI.WOBBLE[0] = 1.3
    sc = UI.nest(WW_, HH_, 37)
    UI.wing(sc, 0, 0, WW_, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=5, seed=16)
    title(sc, "СТАИ", "у каждого лидера рой стоит по-своему", seed=31)
    PW_ = 232
    xs = [12 + i * (PW_ + 4) for i in range(4)]
    for x0 in xs:
        UI.cell(sc, x0, 52, x0 + PW_, 322, "find")
    heads = [("Матка", "Тесные стаи", "в клетке 6, а не 4"), ("Разум улья", "Одна мысль", "вся стая — в одну цель"),
             ("Пожиратель", "Свора", "за вожаком, тела — ему"), ("Кукушка", "Пёстрые стаи", "разные виды вперемешку")]
    for x0, (who, name, sub) in zip(xs, heads):
        letters(sc, who, x0 + 12, 60, "title", 8, col=PALE, outline=False)
        letters(sc, name, x0 + 12, 72, "text", 16, col=GOLD, jitter=1, seed=len(name))
        letters(sc, sub, x0 + 12, 90, "text", 16, col=MUTED)
    ZD = 0.75

    def cellbox(x, y, w, h, col):
        for xx in range(int(x), int(x + w)):
            for yy in (int(y), int(y + h - 1)):
                if (xx + yy) % 3:
                    sc.rgb[yy, xx] = hexc(col)
        for yy in range(int(y), int(y + h)):
            for xx in (int(x), int(x + w - 1)):
                if (xx + yy) % 3:
                    sc.rgb[yy, xx] = hexc(col)

    # Матка: four in a cell, and six
    x0 = xs[0]
    for k_, (cx, n, lab) in enumerate(((x0 + 60, 4, "обычно"), (x0 + 166, 6, "у Матки"))):
        cellbox(cx - 44, 150, 88, 70, "#c9b27a")
        for j in range(n):
            put(sc, bug((), "idle", ZD, 100 + j), cx - 26 + (j % 2) * 30 + (j // 2 % 2) * 6, 172 + (j // 2) * 18, 0)
        letters(sc, str(n), cx, 226, "title", 16, col=GOLD if k_ else INK, align="center")
        letters(sc, lab, cx, 248, "text", 16, col=MUTED, align="center")
    letters(sc, "площадь бьёт больше тел", x0 + PW_ / 2, 292, "text", 16, col=RED, align="center")
    # Разум: the whole flock into one target, the other enemy left alone
    x0 = xs[1]
    t1, t2 = E.golem("Механик"), E.human("Изобретатель")
    put(sc, t1, x0 + 186, 214, 0)
    put(sc, t2, x0 + 196, 276, 0)
    for j, (dx, dy) in enumerate(((40, 160), (30, 196), (56, 232), (80, 182), (70, 262))):
        put(sc, bug(("scythes",), "attack", ZD, 110 + j), x0 + dx, dy, 0)
        UI.silk(sc, (x0 + dx + 10, dy - 10), (x0 + 166, 190), sag=-4, col="#c8a0ff")
    E.burst(sc, x0 + 170, 190, 9, hexc("#c8a0ff"))
    letters(sc, "лишний урон пропадает", x0 + PW_ / 2, 292, "text", 16, col=RED, align="center")
    # Пожиратель: the pack runs where he ran; the bodies are left for him
    x0 = xs[2]
    put(sc, leader("Пожиратель", "attack", 0.6), x0 + 150, 214, 16)
    E.speed(sc, x0 + 96, 204, 4, 22)
    for j, (dx, dy) in enumerate(((60, 182), (44, 222), (84, 246), (28, 264))):
        put(sc, bug((), "attack", ZD, 120 + j), x0 + dx, dy, 0)
    for dx, dy in ((150, 266), (204, 250)):                   # the bodies, left lying for him
        E.splash(sc, x0 + dx, dy, 18, hexc("#7a1a14"), 0.7)
        put(sc, E.lit(bug((), "idle", ZD, 150 + dx), (40, 16, 14), 0.6), x0 + dx, dy - 1, 0)
        sc.glow(x0 + dx, dy - 6, 14, hexc("#d02a1e"), 0.4)
    letters(sc, "ему", x0 + 204, 226, "title", 8, col=(255, 140, 110), outline=False, align="center")
    letters(sc, "сами не лечатся", x0 + PW_ / 2, 292, "text", 16, col=RED, align="center")
    # Кукушка: one flock of all kinds, pairs inside it
    x0 = xs[3]
    cellbox(x0 + 24, 140, 184, 130, "#9ae060")
    kinds = [((), 130), (("wings",), 131), (("stinger",), 132), (("horn",), 133), (("acid",), 134), (("spitter",), 135)]
    pos = [(60, 176), (120, 170), (176, 182), (66, 230), (128, 236), (182, 250)]
    for (tr, sd), (dx, dy) in zip(kinds, pos):
        put(sc, bug(tr, "idle", ZD, sd), x0 + dx, dy, 0)
    UI.silk(sc, (x0 + 66, 214), (x0 + 128, 222), sag=8, col="#f0c040")
    UI.silk(sc, (x0 + 120, 156), (x0 + 176, 166), sag=8, col="#f0c040")
    letters(sc, "быстрые обгоняют", x0 + PW_ / 2, 292, "text", 16, col=RED, align="center")
    UI.creature(sc, bug((), "idle", 0.9, 140), 470, 54)
    UI.cobweb(sc, 958, 46, 30, quad=(-1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_flocks.png"))
    print("swarm_flocks.png", img.size)


# ---------------------------------------------------------------- the battle itself, with the swarm's interface over it
def battle_hud():
    import battle as BT
    sc, count, ng = BT.build("Матка")
    UI.WOBBLE[0] = 1.0
    # top: a thin wing with the turn, the swarm and the enemy, the speed
    UI.wing(sc, 0, 0, WW, 34)
    letters(sc, "ХОД 5", 400, 4, "title", 24, col=(236, 216, 170), col2=(150, 96, 60), jitter=1, drips=4, hairs=5, align="center")
    letters(sc, f"рой {count - 1}", 16, 5, "title", 16, col=(170, 240, 120), col2=(70, 150, 50))
    letters(sc, "съедено 14", 16, 22, "text", 16, col=MUTED)
    letters(sc, f"Литейщик · {ng} големов", 700, 6, "text", 16, col=(214, 196, 150), align="right")
    for k_, t in enumerate(("II", "×1", "×2", "×4")):
        x0 = 716 + k_ * 58
        UI.button(sc, x0, 6, x0 + 52, 28, "amber" if t == "×2" else "chitin")
        letters(sc, t, x0 + 26, 9, "text", 16, col=DARK if t == "×2" else INK, outline=t != "×2", align="center")
    # bottom left: the leader — health, abilities, their cooldowns; the leader itself sits on the plate's edge
    UI.plate(sc, 4, 448, 324, 536, antennae=True)
    put(sc, leader("Матка", "idle", 0.74), 62, 530, 30)
    letters(sc, "МАТКА", 124, 456, "title", 16, col=GOLD, jitter=1, seed=3)
    UI.meter(sc, 124, 478, 316, 10, 16, 13, "#c04a3a")
    abil = [("clutch", "1"), ("larva", ""), ("feed", "")]
    for k_, (key, cd) in enumerate(abil):
        x0 = 124 + k_ * 66
        UI.cell(sc, x0, 494, x0 + 60, 532, "hi" if k_ == 0 else "normal")
        icon(sc, key, x0 + 4, 497, 2)
        if cd:
            letters(sc, cd, x0 + 50, 512, "title", 8, col=(255, 200, 120), align="center")
    # bottom: the flocks — kind, alive of all, a state if any
    import swarm_status as ST
    UI.plate(sc, 330, 448, 956, 536)
    others = [(("stinger",), "скорпионы", 31, 36, "poison"), (("horn",), "жуки", 12, 12, None),
              (("acid",), "бочонки", 18, 24, None), (("wings",), "осы", 27, 33, "fear"), (("spitter",), "пауки", 3, 3, None)]
    ants = count - 1 - sum(o[2] for o in others)                 # the strip adds up to the swarm counted on the field
    flocks_ = [((), "муравьи", ants, ants + 27, None)] + others
    for k_, (tr, name, alive, tot, st) in enumerate(flocks_):
        x0 = 338 + k_ * 102
        UI.cell(sc, x0, 456, x0 + 96, 530, "new" if alive == tot else "normal")
        letters(sc, name, x0 + 8, 459, "text", 16, col=INK, jitter=1, seed=k_)
        icon(sc, tr[0] if tr else "ant", x0 + 6, 476, 2)
        letters(sc, f"{alive}", x0 + 44, 482, "title", 8, col=GOLD if alive == tot else (255, 150, 120), outline=False)
        letters(sc, f"из {tot}", x0 + 44, 495, "title", 8, col=PALE, outline=False)
        UI.meter(sc, x0 + 8, 514, x0 + 88, 7, min(tot, 10), round(min(tot, 10) * alive / tot), "#8a6aa8")
        if st:
            ST.glyph(sc, st, x0 + 87, 462)
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_battle_hud.png"))
    print("swarm_battle_hud.png", img.size)


# ---------------------------------------------------------------- after the battle: the battle changes the breed
def aftermath():
    import brood as B
    import swarm_effects as E
    sc = frame_screen(37)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=17)
    title(sc, "ПОБЕДА", "бой меняет породу", seed=33)
    # losses
    UI.plate(sc, 12, 52, 300, 446, antennae=True)
    heading(sc, "ПОТЕРИ", 26, 64, seed=6)
    for j in range(9):
        put(sc, E.lit(bug(((), ("stinger",), ("wings",))[j % 3], "idle", 1.25, 160 + j), (26, 18, 16), 0.7), 56 + (j % 3) * 76 + (j // 3) * 14, 132 + (j // 3) * 34, 9)
    letters(sc, "погибло", 26, 240, "text", 16, col=MUTED)
    letters(sc, "23", 26, 258, "title", 24, col=(255, 140, 110), col2=(170, 50, 40), jitter=1, drips=3)
    letters(sc, "съедено врагов", 26, 300, "text", 16, col=MUTED)
    letters(sc, "14", 26, 318, "title", 24, col=(170, 240, 120), col2=(70, 150, 50), jitter=1)
    icon(sc, "biomass", 90, 316, 2)
    letters(sc, "+14 биомассы", 130, 326, "text", 16, col=BIO)
    scribble(sc, 26, 380, 250, seed=51)
    letters(sc, "погибшие не вернутся", 26, 400, "text", 16, col=PALE)
    # what the battle gave: the leader's own gift
    UI.plate(sc, 310, 52, 652, 446, antennae=True)
    UI.engrave(sc, leader("Матка", "idle", 1.6), 560, 470, col="#2a2234", k=0.9)
    heading(sc, "ДАР МАТКИ", 324, 64, seed=7)
    letters(sc, "личинки, дожившие до конца боя,", 324, 88, "text", 16, col=MUTED)
    letters(sc, "уходят в выводок", 324, 106, "text", 16, col=MUTED)
    for j, dx in enumerate((380, 440, 500)):
        put(sc, larva("idle", 1.5), dx, 196, 12)
    icon(sc, "stinger", 560, 168, 2)
    for j, ln in enumerate(("рождаются с жалом —", "оно убивало больше всех")):
        letters(sc, ln, 324, 220 + j * 18, "text", 16, col=INK)
    UI.cell(sc, 320, 268, 642, 340, "mut")
    letters(sc, "Сердце роя: 5 яиц у Матки", 334, 278, "text", 16, col=GOLD)
    letters(sc, "вылупились — бились — живы", 334, 296, "text", 16, col=INK)
    put(sc, clutch(1.0), 580, 330, 0)
    UI.cell(sc, 320, 352, 642, 436, "normal")
    letters(sc, "по чертам: кто убивал", 334, 362, "text", 16, col=MUTED)
    for i, (name, kills, key) in enumerate(B.SELECTION):
        x, y = 334 + i * 76, 384
        icon(sc, key, x, y)
        letters(sc, str(kills), x + 20, y + 4, "title", 8, col=PALE, outline=False)
        UI.meter(sc, x, y + 24, x + 64, 6, 8, round(8 * kills / 23), "#c04a3a" if i == 0 else "#8a6aa8")
    # pairs at the seams of the flocks, and the find
    UI.plate(sc, 662, 52, 948, 446, antennae=True)
    heading(sc, "ПАРЫ", 676, 64, seed=8)
    letters(sc, "стыки стай: 3 пары", 676, 88, "text", 16, col=MUTED)
    pairs = [(((), ("stinger",)), 170), ((("horn",), ("wings",)), 230), ((("acid",), ()), 290)]
    for (a_, b_), y in pairs:
        put(sc, bug(a_, "idle", 1.2, y), 712, y, 10)
        put(sc, bug(b_, "idle", 1.2, y + 1), 800, y, 10)
        UI.silk(sc, (724, y - 16), (790, y - 16), sag=8, col="#f0c040")
        letters(sc, "→", 846, y - 22, "text", 16, col=MUTED)
        put(sc, clutch(1.6), 896, y, 8)
    UI.cell(sc, 670, 316, 940, 436, "find")
    letters(sc, "находка", 684, 326, "title", 8, col=PALE, outline=False)
    letters(sc, "Взросление", 684, 340, "text", 16, col=GOLD, jitter=1)
    for j, ln in enumerate(("рабочая убила больше", "всех — выйдет солдатом")):
        letters(sc, ln, 684, 360 + j * 18, "text", 16, col=INK)
    put(sc, bug(("ant", "stinger"), "idle", 1.1, 77, soldier=True), 900, 426, 10)
    UI.button(sc, 690, 466, 948, 524, "amber")
    letters(sc, "В ВЫВОДОК", 819, 486, "title", 16, col=DARK, col2=(90, 40, 10), outline=False, align="center", jitter=1)
    letters(sc, "выжившие отдыхают, пары кладут яйца", 480, 480, "text", 16, col=MUTED, align="center")
    scribble(sc, 380, 500, 200, seed=52)
    UI.creature(sc, bug((), "idle", 1.0, 170), 250, 54)
    UI.cobweb(sc, 2, 448, 30, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_aftermath.png"))
    print("swarm_aftermath.png", img.size)


# ---------------------------------------------------------------- choosing the leader at the start of the run
def leaders_pick():
    import swarm_leaders as SL
    sc = frame_screen(41)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=18)
    title(sc, "ЛИДЕР", "кто поведёт рой в этот поход", seed=35)
    # start armies as in the concept (workers; soldiers), the flock rule, the key mutation of the leader's pool
    data = [("Матка", "matka", "число и порода", "тесные стаи", "Наследница",
             [((), 12), (("wings",), 3), (("stinger",), 3)], [((), 2), (("horn",), 1), (("carapace",), 1)]),
            ("Разум улья", "razum", "пси мимо брони, захват", "одна мысль на стаю", "Ретранслятор",
             [((), 9), (("firefly",), 3)], [((), 3), (("scythes",), 2), (("stinger",), 1)]),
            ("Пожиратель", "pozh", "зверь растёт в бою", "свора", "Питательная суть",
             [((), 15), (("jumper",), 3)], [((), 2)]),
            ("Кукушка", "kuk", "рой растёт за счёт врага", "пёстрые стаи", "Королевская кладка",
             [((), 15), (("stinger",), 3), (("acid",), 3)], [((), 3)])]
    PW_ = 232
    for k_, (name, ik, what, rule, key, army, soldiers) in enumerate(data):
        x0 = 12 + k_ * (PW_ + 4)
        UI.cell(sc, x0, 52, x0 + PW_, 452, "hi" if k_ == 0 else "normal")
        spr = SL.build(name, "idle", 1.0)
        kk = min(1.75, 172 / spr.w, 116 / spr.h)
        put(sc, SL.build(name, "idle", kk), x0 + PW_ / 2 + 6, 180, 30)
        icon(sc, ik, x0 + 12, 202, 2)
        letters(sc, name, x0 + 50, 206, "text", 16, col=GOLD if k_ == 0 else INK, jitter=1, seed=k_)
        letters(sc, what, x0 + 12, 236, "text", 16, col=INK)
        letters(sc, "стаи:", x0 + 12, 264, "title", 8, col=PALE, outline=False)
        letters(sc, rule, x0 + 54, 260, "text", 16, col=GOLD)
        for r, (lab, row, sold, by) in enumerate((("рабочие:", army, False, 330), ("солдаты:", soldiers, True, 394))):
            letters(sc, lab, x0 + 12, by - 46, "title", 8, col=PALE, outline=False)
            for j, (tr, n) in enumerate(row):
                b_ = bug(tr, "idle", 1.0, 180 + j + k_ * 5 + r * 20, soldier=sold)
                cx = x0 + 32 + j * 72
                put(sc, b_, cx, by, 8)
                right = np.nonzero(b_.a.any(axis=0))[0].max()
                letters(sc, f"×{n}", cx - b_.ox + right + 3, by - 6, "title", 8, col=INK)
        letters(sc, "ключ:", x0 + 12, 422, "title", 8, col=PALE, outline=False)
        letters(sc, key, x0 + 54, 418, "text", 16, col=(196, 160, 236))
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Назад", 156, 486, "title", 16, col=INK, align="center")
    UI.button(sc, 690, 466, 948, 524, "amber")
    letters(sc, "В ПОХОД", 819, 486, "title", 16, col=DARK, col2=(90, 40, 10), outline=False, align="center", jitter=1)
    letters(sc, "у каждого лидера свой пул мутаций", 495, 480, "text", 16, col=MUTED, align="center")
    scribble(sc, 400, 500, 190, seed=53)
    UI.cobweb(sc, 958, 46, 34, quad=(-1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_leader_pick.png"))
    print("swarm_leader_pick.png", img.size)


# ---------------------------------------------------------------- the leader grows: choose its development
def development():
    import swarm_leaders as SL
    sc = frame_screen(47)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=19)
    title(sc, "РАЗВИТИЕ", "Разум улья созрел: во что ему прорасти", seed=37)
    UI.plate(sc, 12, 52, 300, 446, antennae=True)
    heading(sc, "СЕЙЧАС", 26, 64, seed=9)
    icon(sc, "razum", 26, 90, 2)
    letters(sc, "Разум улья", 64, 94, "text", 16, col=INK, jitter=1, seed=4)
    put(sc, SL.build("Разум улья", "idle", 2.1), 156, 276, 34)
    for j, ln in enumerate(("Пси-удар на 3 клетки", "Захват раз в 6 ходов", "Помутнение на 2 клетки")):
        letters(sc, ln, 26, 300 + j * 20, "text", 16, col=INK)
    scribble(sc, 26, 370, 240, seed=61)
    letters(sc, "слабость: хрупкий мозг", 26, 400, "text", 16, col=(200, 120, 110))
    for j, (key, name, look) in enumerate(SL.DEV["Разум улья"]):
        x0 = 312 + j * 214
        UI.cell(sc, x0, 52, x0 + 206, 446, "hi" if j == 1 else "normal")
        put(sc, SL.build("Разум улья", "idle", 1.9, dev=key), x0 + 103, 232, 30)
        letters(sc, name, x0 + 14, 252, "text", 16, col=GOLD if j == 1 else INK, jitter=1, seed=j)
        for k_, ln in enumerate(wrap(look, 180)):
            letters(sc, ln, x0 + 14, 278 + k_ * 17, "text", 16, col=MUTED)
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Позже", 156, 486, "title", 16, col=INK, align="center")
    UI.button(sc, 690, 466, 948, 524, "amber")
    letters(sc, "ПРОРАСТИ", 819, 486, "title", 16, col=DARK, col2=(90, 40, 10), outline=False, align="center", jitter=1)
    letters(sc, "развитие — навсегда, на весь поход", 495, 480, "text", 16, col=MUTED, align="center")
    scribble(sc, 400, 500, 190, seed=62)
    UI.creature(sc, bug((), "idle", 1.0, 190), 540, 54)
    UI.cobweb(sc, 2, 448, 30, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_development_screen.png"))
    print("swarm_development_screen.png", img.size)


SCREENS = {"brood": brood, "camp": camp, "evolution": evolution, "deploy": deploy, "finds": finds, "pools": pools,
           "flocks": flocks, "battle": battle_hud, "aftermath": aftermath, "leader": leaders_pick, "development": development}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in SCREENS.items():
        if arg in ("all", k):
            fn()
