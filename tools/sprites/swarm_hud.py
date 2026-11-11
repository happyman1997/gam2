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
        if UI.rich_width((cur + " " + wd).strip(), kind, px) > width and cur:
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
    offers = [("horn", "Рог", "деталь", "первый удар боя сильнее и {дроб}", (236, 224, 196)),
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
            UI.rich(sc, ln, 386, y0 + 46 + n_ * 17, "text", 16, col=MUTED if k_ else INK)
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
    text = ("Муравей-солдат получает Рог: первый удар боя сильнее и {дроб}, против литого металла. "
            "Рог наследуется: в кладках этой линии появятся рога.")
    for n_, ln in enumerate(wrap(text, 262)):
        UI.rich(sc, ln, 676, 254 + n_ * 18, "text", 16, col=INK)
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
            UI.rich(sc, ln, x0 + 12, 166 + k_ * 17, "text", 16, col=INK)
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
def tug(sc, x0, y0, x1, y1, share):
    """Who is winning, at a glance: the swarm's acid-green comb pushing from the left, the Foundry's hot iron from the
    right, a jagged seam throwing sparks where they meet."""
    m = UI.chamfer_mask(sc, x0, y0, x1, y1, 4)
    rim, _, _ = UI.edges(m)
    X, Y = sc.xx, sc.yy
    t = np.clip((Y - y0) / max(1, y1 - y0), 0, 1)[..., None]
    mid = x0 + (x1 - x0) * share
    seam = mid + np.where((Y // 2) % 2 == 0, 2, -2)
    left, right = m & (X < seam), m & (X >= seam)
    sw = hexc("#b4f47a") * (1 - t) + hexc("#2a6224") * t
    fo = hexc("#f09a50") * (1 - t) + hexc("#5a2416") * t
    sc.rgb[left] = sw[left]
    sc.rgb[right] = fo[right]
    UI.comb(sc, left, x0, y0, hexc("#1e4a1a"), 0.55, R=4)
    for x in range(int(mid) + 8, x1 - 4, 12):              # rivets in the iron
        yc = (y0 + y1) // 2
        sc.rgb[yc - 1:yc + 1, x:x + 2] = hexc("#ffd0a0")
        sc.rgb[yc + 1, x:x + 2] = hexc("#3a160e")
    edge = m & (np.abs(X - seam) < 1)
    sc.rgb[edge] = hexc("#fff4c8")
    sc.rgb[rim] = hexc("#0a060e")
    sc.glow(mid, (y0 + y1) / 2, 14, hexc("#ffd890"), 0.6)
    for dx, dy in ((-3, -6), (4, -7), (6, 5), (-5, 6)):     # sparks off the seam
        sc.rgb[int((y0 + y1) / 2 + dy), int(mid + dx)] = hexc("#ffe8a0")


def cursor(sc, x, y):
    """The mouse arrow, pixel by pixel."""
    rows = ["o.........", "oo........", "o#o.......", "o##o......", "o###o.....", "o####o....", "o#####o...",
            "o######o..", "o###oooo..", "o#o#o.....", "oo.o#o....", "o..o#o....", ".....oo..."]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                sc.rgb[y + j, x + i] = hexc("#0a060e") if ch == "o" else hexc("#f4ecd8")


def battle_hud():
    """The battle runs itself: the interface is one thin wing — the sides' tug of war, the speed. Everything else is
    on the field: the leader's health over the leader, an ability's icon popping up when it fires, states over the
    units. On pause, pointing at anyone opens their card."""
    import copy
    import battle as BT
    import swarm_status as ST
    sc0, count, ng = BT.build("Матка")
    qx, qy = BT.X0 + 15.6 * BT.CW, BT.Y0 + 8.4 * BT.CH
    qtop = ST.top_of(W.queen(0.0, "attack", k=0.92), qy)
    for paused in (False, True):
        sc = copy.deepcopy(sc0)
        UI.WOBBLE[0] = 1.0
        # on the field: the leader's health over the leader, and Кладка popping up as it fires
        UI.meter(sc, qx - 46, qtop - 12, qx + 46, 7, 10, 8, "#c04a3a")
        px_, py_ = qx - 104, qtop - 34
        sc.glow(px_ + 16, py_ + 16, 22, hexc("#f0c060"), 0.45)
        icon(sc, "clutch", px_, py_, 2)
        letters(sc, "Кладка", px_ + 16, py_ + 34, "text", 16, col=GOLD, align="center", jitter=1, seed=5)
        # the wing: the swarm against the Foundry, the speed, the turn small by it
        UI.wing(sc, 0, 0, WW, 34)
        letters(sc, f"рой {count - 1}", 16, 8, "title", 16, col=(170, 240, 120), col2=(70, 150, 50))
        tug(sc, 144, 10, 520, 25, 0.6)
        letters(sc, f"Литейщик: {ng - 1} из {ng}", 530, 9, "text", 16, col=(214, 196, 150))
        letters(sc, "ход 5", 728, 13, "title", 8, col=MUTED, outline=False, align="right")
        for x0, x1, t, on in ((736, 784, "II", paused), (790, 838, "×2", not paused), (844, 952, "в конец »", False)):
            UI.button(sc, x0, 6, x1, 28, "amber" if on else "chitin")
            letters(sc, t, (x0 + x1) / 2, 9, "text", 16, col=DARK if on else INK, outline=not on, align="center")
        name = "swarm_battle_hud.png"
        if paused:                                  # on pause: point at a spitter and read its card
            sx_, sy_ = 566, 452
            cx0, cy0, cx1, cy1 = 586, 302, 800, 452
            UI.cell(sc, cx0, cy0, cx1, cy1, "hi")
            icon(sc, "spitter", cx0 + 8, cy0 + 6, 2)
            letters(sc, "Паук-плевун", cx0 + 44, cy0 + 10, "text", 16, col=GOLD, jitter=1, seed=7)
            letters(sc, "рабочая", cx0 + 44, cy0 + 26, "title", 8, col=PALE, outline=False)
            for j, (ln, col) in enumerate((("Плюёт раз в 2 хода", INK), ("на 3 клетки, урон {яд}.", INK),
                                           ("Цель прилипает к клетке", INK), ("на раунд, но бьёт.", INK),
                                           ("Плюнет снова через ход", GREEN), ("Вблизи кусается слабо", RED))):
                UI.rich(sc, ln, cx0 + 10, cy0 + 44 + j * 16, "text", 16, col=col)
            cursor(sc, sx_ - 2, sy_ - 14)
            name = "swarm_battle_pause.png"
        img = sc.image(S)
        UI.WOBBLE[0] = 0.0
        img.save(out(name))
        print(name, img.size)


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


# ---------------------------------------------------------------- the creature's card: who it is, what it can, where it came from
SILVER = (200, 206, 220)


def section(sc, x, y, w, key, label, title, text, col=GOLD, seed=0):
    """One block of a card: an icon, a small label, the name, and what it does, wrapped."""
    if key:
        icon(sc, key, x, y, 1)
    letters(sc, label, x + 20, y, "title", 8, col=PALE, outline=False)
    letters(sc, title, x + 20, y + 9, "text", 16, col=col, jitter=1, seed=seed)
    yy = y + 27
    for ln in wrap(text, w - 4):
        UI.rich(sc, ln, x, yy, "text", 16, col=INK)
        yy += 15
    return yy + 6


def stats(sc, x, y, rows):
    """The numbers, two to a row: a small label over the value."""
    for i, (lab, val) in enumerate(rows):
        cx, cy = x + (i % 2) * 140, y + (i // 2) * 28
        letters(sc, lab, cx, cy, "title", 8, col=PALE, outline=False)
        letters(sc, val, cx, cy + 9, "text", 16, col=INK)
    return y + ((len(rows) + 1) // 2) * 28 + 4


def dots(sc, x0, x1, y):
    """A dotted leader line between a label and its value, as in an old ledger."""
    for x in range(int(x0), int(x1), 4):
        sc.rgb[y, x] = sc.rgb[y, x] * 0.4 + np.array(PALE, float) * 0.6


def big_card(spec, name):
    """A creature's card as big as the screen, as in Conquest of Elysium: the creature large on the left with where
    it came from; the numbers in a column; every attack in a column of its own — damage, type, reach, what it does
    besides; on the right what it can and what it can't, each with its icon."""
    sc = frame_screen(spec["seed"])
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=spec["seed"])
    title(sc, spec["title"], spec["sub"], seed=spec["seed"] + 1)
    UI.plate(sc, 6, 50, WW - 6, HH - 6, antennae=False)
    # left: the creature large, where it came from
    UI.cell(sc, 18, 62, 300, 300, spec.get("cell", "hi"))
    spr = spec["sprite"]
    put(sc, spr, 159 + spec.get("dx", 0), 268, spec.get("sw", 40))
    y = 312
    for kind, *row in spec["facts"]:
        if kind == "parents":
            letters(sc, "родители", 22, y, "title", 8, col=PALE, outline=False)
            x = 22
            for j, (key, nm) in enumerate(row[0]):
                if j:
                    letters(sc, "×", x + 2, y + 12, "text", 16, col=MUTED)
                    x += 16
                icon(sc, key, x, y + 10, 1)
                letters(sc, nm, x + 18, y + 12, "text", 16, col=INK)
                x += 18 + UI.text_width(nm, "text", 16) + 4
            y += 34
        else:
            lab, vals, col = row
            letters(sc, lab, 22, y, "title", 8, col=PALE, outline=False)
            for j, val in enumerate([vals] if isinstance(vals, str) else vals):
                letters(sc, val, 22, y + 10 + j * 16, "text", 16, col=col)
            y += 32 + 16 * (0 if isinstance(vals, str) else len(vals) - 1)
    UI.button(sc, 22, HH - 52, 296, HH - 16, "chitin")
    letters(sc, "Закрыть", 159, HH - 42, "title", 16, col=INK, align="center")
    # middle: the numbers, then the attacks — each its own row
    x0, x1 = 316, 616
    heading(sc, "СУДЬБА", x0, 62, seed=3)
    y = 86
    for lab, val in spec["stats"]:
        letters(sc, lab, x0, y, "text", 16, col=MUTED)
        w = UI.text_width(val, "text", 16)
        dots(sc, x0 + UI.text_width(lab, "text", 16) + 6, x1 - w - 6, y + 12)
        letters(sc, val, x1, y, "text", 16, col=INK, align="right")
        y += 19
    y += 12
    heading(sc, "ВОЗМОЖНОСТИ", x0, y, seed=4)
    y += 26
    cols = (x0 + 20, x0 + 112, x0 + 172, x0 + 252)
    for cx, lab in zip(cols, ("удар", "урон", "тип", "дальн.")):
        letters(sc, lab, cx, y, "title", 8, col=PALE, outline=False)
    y += 12
    for key, nm, dmg, typ, reach, note in spec["attacks"]:
        sc.rgb[y, x0:x1] = sc.rgb[y, x0:x1] * 0.5 + hexc("#4a3e5c") * 0.5
        icon(sc, key, x0, y + 5, 1)
        for cx, val, col in zip(cols, (nm, dmg, typ, reach), (GOLD, INK, INK, INK)):
            UI.rich(sc, val, cx, y + 5, "text", 16, col=col)
        y += 22
        for ln in (wrap(note, x1 - x0 - 24) if note else []):
            UI.rich(sc, ln, x0 + 20, y, "text", 16, col=MUTED)
            y += 15
        y += 4
    # under the attacks: what it hands down, or the leader's pool — icons in a column
    if spec.get("below"):
        head, rows = spec["below"]
        y += 10
        heading(sc, head, x0, y, seed=6)
        y += 26
        for key, nm, note, col in rows:
            icon(sc, key, x0, y, 1)
            letters(sc, nm, x0 + 20, y + 1, "text", 16, col=col)
            if note:
                letters(sc, note, x1, y + 1, "text", 16, col=MUTED, align="right")
            y += 18
    # right: what it can and what it can't — a column of names; the text shows when the mouse is over one
    x0, x1 = 632, WW - 18
    heading(sc, spec.get("right", "СПОСОБНОСТИ"), x0, 62, seed=5)
    y = 90
    hov = spec.get("hover", len(spec["abilities"]) - 1)
    for i, (key, lab, nm, desc, col) in enumerate(spec["abilities"]):
        if i == hov:
            UI.cell(sc, x0 - 6, y - 4, x1, y + 38, "hi")
        icon(sc, key, x0, y, 2)
        letters(sc, nm, x0 + 42, y + 2, "text", 16, col=col, jitter=1, seed=len(nm))
        letters(sc, lab, x0 + 42, y + 21, "title", 8, col=PALE, outline=False)
        if i == hov:
            hy, hx = y, x0 + 42 + UI.text_width(nm, "text", 16)
        y += 44
    # the hovered one: its text in a tooltip under the cursor
    key, lab, nm, desc, col = spec["abilities"][hov]
    lines = wrap(desc, x1 - x0 - 40)
    tx0, ty0 = x0 + 10, hy + 46
    UI.cell(sc, tx0, ty0, x1, ty0 + 30 + len(lines) * 16, "normal")
    letters(sc, nm, tx0 + 12, ty0 + 8, "text", 16, col=col)
    for j, ln in enumerate(lines):
        UI.rich(sc, ln, tx0 + 12, ty0 + 26 + j * 16, "text", 16, col=INK)
    cursor(sc, int(hx) - 30, int(hy) + 10)
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)


def cards():
    big_card(dict(
        seed=53, title="СКОРПИОН", sub="рабочая · «Летучее жало» · в рое 7",
        sprite=bug(("stinger", "wings"), "idle", 4.2, 61, rare="blister", evo=("vise",)), dx=-6,
        facts=[("parents", [("stinger", "скорпион"), ("wings", "оса")]),
               ("val", "убито стаей в прошлом бою", "9", GREEN),
               ("val", "таких в рое", "7", INK)],
        stats=[("здоровье", "8"), ("броня", "0 · хитин"), ("скорость", "2"), ("боевой дух", "6"),
               ("размер", "1"), ("предел роя", "1 очко")],
        attacks=[("stinger", "Жало", "1–4 +1", "{кол}", "1", "если пробивает броню: {яд} 1–4 и −1 к броне"),
                 ("evo_vise", "Клешни", "—", "{дроб}", "1", "цель не может уйти со своей клетки")],
        below=("ПОТОМКАМ", [("stinger", "Жало", "черта", GOLD), ("wings", "Крылья", "черта", GOLD),
                            ("m_blister", "Нарывник", "мутация", SILVER)]),
        abilities=[("stinger", "форма", "Жало", "Если удар жалом пробивает броню, цель получает 1–4 {яд} и теряет 1 броню до конца боя. {яд} накапливается. С одной цели снимается не больше 2 брони. Машинам {яд} не страшен, но броню жало снимает и с них.", GOLD),
                   ("wings", "деталь", "Крылья", "Может проходить через клетки, занятые своими.", GOLD),
                   ("m_blister", "мутация · общий пул", "Нарывник", "Враг, который ранит её в ближнем бою, до конца боя бьёт слабее. На одного врага срабатывает один раз. Действует и на машины.", SILVER),
                   ("evo_vise", "эволюция формы", "Клешни-тиски", "Клешни бьют {дроб}. Враг, в которого они попали, не может уйти со своей клетки.", (150, 220, 120)),
                   ("fear", "слабость", "Медленнее других", "Скорость 2, у других рабочих 3.", RED),
                   ("ant", "класс", "Стая", "Боевой дух +1 за каждую свою особь в соседних клетках, но не больше +4.", INK),
                   ("biomass", "класс", "Пожирание", "Убив врага, съедает труп и восстанавливает четверть здоровья. После боя съеденное идёт в биомассу.", INK),
                   ("carapace", "класс", "Хитин", "Урон {руб} по ней в два раза меньше, {дроб} в два раза больше.", INK)]),
        "swarm_card.png")
    big_card(dict(
        seed=57, title="МАТКА", sub="лидер роя · число и порода", cell="mut",
        sprite=leader("Матка", "idle", 1.45), dx=14, sw=56,
        facts=[("val", "развитие", "ещё не выбрано", MUTED),
               ("val", "на выбор", ["кладка чаще", "+1 личинка", "или +1 к размеру"], INK)],
        stats=[("здоровье", "80"), ("броня", "2 · хитин"), ("скорость", "1"), ("размер", "6")],
        attacks=[("matka", "Жвалы", "1–6 +2", "{руб}", "1", "")],
        below=("ПУЛ МУТАЦИЙ", [("m_nest", "Малое гнездо", "Гнездо", GOLD), ("m_nurse", "Кормилица", "Гнездо", GOLD),
                               ("m_vivi", "Живородящая", "Гнездо", GOLD), ("m_bud", "Почкование", "Гнездо", GOLD),
                               ("m_dominant", "Доминантная линия", "Порода", GOLD), ("m_flight", "Брачный полёт", "Порода", GOLD),
                               ("m_hybrid", "Гибрид", "Порода", GOLD), ("m_heir", "Наследница", "ключ", (196, 160, 236))]),
        abilities=[("clutch", "каждые 3 хода", "Кладка", "Каждые 3 хода рядом с Маткой вылупляются 2 личинки. В бой они вступают со следующего раунда. Личинки, которые доживут до конца боя, попадут в выводок с чертой, убившей в этом бою больше всего врагов.", GOLD),
                   ("larva", "постоянно", "Сердце роя", "Если особь роя погибает в 2 клетках от Матки, на её месте остаётся яйцо. Через 2 хода из него вылупляется личинка.", GOLD),
                   ("feed", "правило похода", "Плодовитость", "В выводке на одного потомка больше. Кормление лидера стоит в два раза дешевле.", (214, 196, 150)),
                   ("matka", "стаи роя", "Тесные стаи", "В одной клетке помещается до 6 мелких особей вместо 4. Удары по площади и растаптывание задевают их всех.", (214, 196, 150)),
                   ("fear", "слабость", "Медлительная", "Скорость 1. Если Матка погибнет, каждая особь роя проходит проверку страха 1–9.", RED)]),
        "swarm_card_leader.png")


# ---------------------------------------------------------------- the leaders on the field: all the battle shows of them
def pop(sc, key, x, y, label, col=GOLD, seed=0):
    """An ability firing: its icon pops up with a glow, the name under it."""
    sc.glow(x, y + 14, 24, np.array(col, float), 0.5)
    icon(sc, key, x - 16, y, 2)
    letters(sc, label, x, y + 34, "text", 16, col=col, align="center", jitter=1, seed=seed)


def hp(sc, spr, x, by, lit, n=10, w=84):
    top = W_top(spr, by)
    UI.meter(sc, x - w / 2, top - 12, x + w / 2, 7, n, lit, "#c04a3a")
    return top - 12


def W_top(spr, by):
    rows = np.nonzero(spr.a.any(axis=1))[0]
    return by - spr.oy + rows.min()


def flip_v(spr):
    """A body on its back: the sprite turned upside down, darkened."""
    f = Sprite(spr.w, spr.h)
    f.rgb, f.a = spr.rgb[::-1] * 0.55, spr.a[::-1].copy()
    f.ox, f.oy = spr.ox, spr.h - 1 - spr.oy + 6
    return f


def leaders_field():
    import battle as BT
    import frames as F
    import swarm_leaders as SL
    import swarm_status as ST
    import swarm_abilities as SA
    sc = Scene(WW, HH)
    BT.ground(sc)
    UI.WOBBLE[0] = 1.0
    UI.wing(sc, 0, 0, WW, 44)
    title(sc, "ЛИДЕРЫ НА ПОЛЕ", "всё, что бой показывает о лидере", seed=43)
    PWd, PHd = 316, 242
    rnd = np.random.RandomState(5)

    def P(i):
        return 4 + (i % 3) * (PWd + 2), 48 + (i // 3) * (PHd + 2)

    def caption(i, name, sub):
        px, py = P(i)
        letters(sc, name, px + 10, py + 6, "text", 16, col=GOLD, jitter=1, seed=i)
        for j, ln in enumerate(wrap(sub, PWd - 20)):
            letters(sc, ln, px + 10, py + 24 + j * 15, "text", 16, col=MUTED)

    def mob(i, xs, traits=((), ("stinger",), ("wings",)), states=()):
        px, py = P(i)
        for j, (dx, dy) in enumerate(xs):
            spr = bug(traits[j % len(traits)], "attack", 1.0, 300 + i * 10 + j)
            x, y = px + dx, py + dy
            BT.shadow(sc, x, y, 14, 3)
            BT.put(sc, spr, x, y, mirror=True)
            if j < len(states) and states[j]:
                ST.glyph(sc, states[j], x, W_top(spr, y) - 11)

    def golem(i, name, dx, dy, pose="attack"):
        px, py = P(i)
        g = F.build(name, pose, k=BT.GK[4 if name == "Механик" else 5])
        BT.shadow(sc, px + dx + 2, py + dy, 40, 7)
        BT.put(sc, g, px + dx, py + dy)
        return g, px + dx, py + dy

    # 1 — Матка: health over her, «Кладка» pops up, the clutch hatching beside her
    px, py = P(0)
    q = W.queen(0.0, "attack", k=0.92)
    qx, qy = px + 236, py + 200
    BT.shadow(sc, qx + 30, qy, 150, 20)
    BT.put(sc, q, qx, qy, mirror=True)
    hp(sc, q, qx + 20, qy, 8)
    cl = SA.render_small(SA.clutch(1), 1.0)
    put(sc, cl, px + 140, py + 214, 0)
    ST.glyph(sc, "hatching", px + 140, W_top(cl, py + 214) - 11)
    for dx, dy in ((110, 206), (96, 222)):
        BT.put(sc, SL.build("личинка", "attack", 1.0), px + dx, py + dy, mirror=True)
    mob(0, ((30, 200), (52, 226), (24, 228)))
    pop(sc, "clutch", px + 150, py + 112, "Кладка", seed=1)
    caption(0, "Матка", "здоровье над ней; «Кладка» всплывает, кладка рядом вылупляется")

    # 2 — Разум улья: «Помутнение» — rings over the golems; the psi piling up over one
    px, py = P(1)
    r_ = SL.build("Разум улья", "idle", 1.0)
    rx, ry = px + 262, py + 196
    BT.shadow(sc, rx + 4, ry, 56, 9)
    BT.put(sc, r_, rx, ry, mirror=True)
    hp(sc, r_, rx, ry, 6, n=6, w=54)
    g, gx_, gy_ = golem(1, "Механик", 70, 214)
    for rr in (26, 40, 54):
        SA.ring(sc, gx_ + 6, gy_ + 2, rr, rr * 0.3, SA.PHERO, 0.45)
    ST.on_body(sc, g, gx_, gy_, "stall")
    ST.glyph(sc, "stall", gx_, W_top(g, gy_) - 12)
    ST.pips(sc, gx_, W_top(g, gy_) - 18, 3)
    SA.psi_wave(sc, (rx - 18, ry - 30), (gx_ + 14, gy_ - 34))
    mob(1, ((150, 214), (172, 226)))
    pop(sc, "m_psi_reson", px + 168, py + 100, "Помутнение", col=VIOLET, seed=2)
    caption(1, "Разум улья", "«Помутнение» — кольца над врагом; над врагом копится пси, машина сбоит")

    # 3 — Пожиратель, fed: the growth steps and the bodies left to the next one
    px, py = P(2)
    d = SL.build("Пожиратель", "attack", 0.9, stage=1)
    dx_, dy_ = px + 210, py + 212
    BT.shadow(sc, dx_ + 20, dy_, 110, 14)
    BT.put(sc, d, dx_, dy_, mirror=True)
    t_ = hp(sc, d, dx_ + 10, dy_, 9)
    for k_ in range(2):                                   # growth: two steps a battle, one taken
        UI.gem(sc, dx_ - 18 + k_ * 16, t_ - 10, 6, 6, "eat" if k_ == 0 else "dim")
    for k_ in range(2):                                   # bodies eaten toward the next step
        UI.gem(sc, dx_ + 22 + k_ * 10, t_ - 10, 3.5, 4.5, "ok" if k_ == 0 else "dim")
    BT.put(sc, BT.dead_bug(0.05, 3), dx_ - 70, dy_ + 4, mirror=True)
    mob(2, ((40, 214), (58, 230), (30, 232), (70, 198)), states=(None, "frenzy", None, "frenzy"))
    pop(sc, "pozh", px + 120, py + 98, "Рост", col=(240, 130, 100), seed=3)
    caption(2, "Пожиратель сыт", "ступени роста — крупные камни; тела до следующей — мелкие")

    # 4 — Пожиратель, hungry: three rounds without food — he takes one of his own
    px, py = P(3)
    d = SL.build("Пожиратель", "attack", 0.9, stage=0)
    dx_, dy_ = px + 210, py + 212
    BT.shadow(sc, dx_ + 20, dy_, 100, 13)
    BT.put(sc, d, dx_, dy_, mirror=True)
    t_ = hp(sc, d, dx_ + 10, dy_, 5)
    for k_ in range(3):                                   # rounds without food: all three gone
        UI.gem(sc, dx_ - 10 + k_ * 12, t_ - 10, 4, 5, "over")
    v = bug((), "idle", 1.0, 77)
    BT.put(sc, BT.flash(v, 0.35), dx_ - 52, dy_ - 6, mirror=True)
    ST.glyph(sc, "captured", dx_ - 52, W_top(v, dy_ - 6) - 11)
    mob(3, ((60, 214), (40, 230), (84, 232)), states=("fear", None, "fear"))
    pop(sc, "feed", px + 110, py + 96, "Ненасытный", col=RED, seed=4)
    caption(3, "Пожиратель голоден", "три раунда без еды — красные камни; хватает свою, самую мелкую")

    # 5 — Кукушка: the eggs ripen in a machine's warm firebox; a grub crawls out every 3 turns
    px, py = P(4)
    k_spr = SL.build("Кукушка", "attack", 1.0)
    kx, ky = px + 250, py + 206
    BT.shadow(sc, kx + 4, ky, 50, 8)
    BT.put(sc, k_spr, kx, ky, mirror=True)
    hp(sc, k_spr, kx, ky, 7, n=6, w=54)
    g, gx_, gy_ = golem(4, "Механик", 84, 214, pose="idle")
    ST.on_body(sc, g, gx_, gy_, "infected", seed=3)
    ST.glyph(sc, "infected", gx_ - 8, W_top(g, gy_) - 12)
    for k_ in range(3):                                   # turns to the next grub: two of three gone
        UI.gem(sc, gx_ + 6 + k_ * 9, W_top(g, gy_) - 7, 3.5, 4.5, "ok" if k_ < 2 else "dim")
    BT.put(sc, SL.build("личинка", "attack", 0.9), gx_ + 30, gy_ + 8)       # a grub already out of the grate
    mob(4, ((160, 222),))
    pop(sc, "kuk", px + 190, py + 98, "Яйцеклад", col=GREEN, seed=5)
    caption(4, "Кукушка", "в машине зреет кладка: камни до следующей личинки")

    # 6 — the leader is dead: the swarm beheaded, everyone tests fear
    px, py = P(5)
    dead = flip_v(SL.build("Разум улья", "idle", 1.0))
    SA.splat(sc, px + 240, py + 192, 26, col=hexc("#5a3a6a"), k=0.6)
    BT.put(sc, dead, px + 240, py + 190)
    mob(5, ((70, 200), (100, 214), (60, 230), (130, 228), (150, 204), (40, 214)),
        states=("fear", "fear", None, "fear", None, "fear"))
    letters(sc, "РОЙ ОБЕЗГЛАВЛЕН", px + PWd / 2, py + 100, "title", 8, col=RED, align="center", jitter=1, seed=9)
    caption(5, "Лидер погиб", "рой обезглавлен: все проверяют страх, у кого сдали нервы — бегут")

    for i in range(6):                                    # thin dark seams between the panels
        px, py = P(i)
        sc.rgb[py:py + PHd, px + PWd:px + PWd + 2] = hexc("#0c0810")
        sc.rgb[py + PHd:py + PHd + 2, px:px + PWd + 2] = hexc("#0c0810")
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_leader_field.png"))
    print("swarm_leader_field.png", img.size)


SCREENS = {"brood": brood, "camp": camp, "evolution": evolution, "deploy": deploy, "finds": finds, "pools": pools,
           "flocks": flocks, "battle": battle_hud, "aftermath": aftermath, "leader": leaders_pick, "development": development,
           "card": cards, "field": leaders_field}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in SCREENS.items():
        if arg in ("all", k):
            fn()
