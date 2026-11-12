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
from swarm_mut import FX
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


EPITHET = {"Матка": ("мать роя", (240, 200, 90)), "Разум улья": ("мысль роя", (196, 150, 255)),
           "Пожиратель": ("голод роя", (236, 96, 80)), "Чума": ("чума роя", (150, 220, 90))}


def epithet(sc, text, x, y, col, seed=0, px=16, curls=True):
    """A leader's by-name, written by the swarm itself: pixel letters in the leader's colour, dripping and
    bristling, a curl of silk at each end."""
    c2 = tuple(int(v * 0.42) for v in col)
    w = letters(sc, text, x, y, "title", px, col=col, col2=c2, jitter=1, drips=4, hairs=5, seed=seed)
    if curls:
        hx = "#%02x%02x%02x" % tuple(int(v * 0.8) for v in col)
        UI.silk(sc, (x - 24, y + px // 2 + 2), (x - 6, y + px // 2), sag=-6, col=hx)
        UI.silk(sc, (x + w + 6, y + px // 2), (x + w + 24, y + px // 2 + 2), sag=-6, col=hx)
        for cx in (x - 25, x + w + 24):
            sc.rgb[int(y + px // 2 + 1):int(y + px // 2 + 4), int(cx):int(cx) + 2] = hexc(hx)
    return w


def title(sc, text, sub=None, x=16, seed=0, epi=None):
    """The screen's name in dripping, bristling letters; for a leader, its by-name written in its colour beside it."""
    w = letters(sc, text, x, 6, "title", 24, col=(236, 216, 170), col2=(150, 96, 60), jitter=1, drips=6, hairs=9, seed=seed)
    if epi:
        epithet(sc, sub, x + w + 44, 10, epi, seed=seed + 1)
    elif sub:
        letters(sc, sub, x + w + 16, 10, "text", 16, col=(196, 182, 206), jitter=1, seed=seed + 1)
    return w


def frame_screen(seed):
    UI.WOBBLE[0] = 1.3
    HOVER.clear()
    sc = UI.nest(WW, HH, seed)
    return sc


HOVER = []        # every glyph and icon on the screen the mouse can point at: (key, x, y, w, h); «@key» — a trait's icon
ALT = [False]     # Alt held: each line of terms is read out in small words under itself


def glyph(sc, key, x, y, z=2):
    """A term's glyph on its own, outside a line — it has its tooltip all the same."""
    import fxg
    a_ = fxg.rgba(key)
    fxg.draw(sc, key, x, y, z)
    HOVER.append((key, int(x), int(y), a_.shape[1] * z, a_.shape[0] * z))
    return a_.shape[1] * z


def help_button(sc, on=False, alt=False):
    """«?» at the right of the wing: the glossary of glyphs, on every screen; beside it the Alt key while held."""
    UI.button(sc, 912, 8, 950, 36, "amber" if on else "chitin")
    letters(sc, "?", 931, 14, "title", 16, col=DARK if on else INK, outline=not on, align="center")
    if alt:
        keycap(sc, 860, 12, "Alt", lit=True)


def act_button(sc, x0, y0, x1, y1, text):
    """The swarm's own action — what moves the run on: acid. Leaving and going back are chitin, what destroys is
    blood, what is on or chosen is amber, what can't be pressed is dim; under the mouse any button is eaten through."""
    UI.button(sc, x0, y0, x1, y1, "acid")
    letters(sc, text, (x0 + x1) / 2, (y0 + y1) / 2 - 9, "title", 16, col=ACID2, col2=(110, 170, 40), align="center",
            jitter=1, hairs=4)


def keycap(sc, x, y, t, lit=False):
    """A key of the keyboard, drawn small."""
    w = UI.text_width(t, "title", 8) + 14
    face, rim = (hexc("#f0c060"), hexc("#7a4a10")) if lit else (hexc("#4a4056"), hexc("#1a1420"))
    sc.rgb[y:y + 20, x:x + w] = rim
    sc.rgb[y + 1:y + 16, x + 1:x + w - 1] = face
    sc.rgb[y + 1, x + 2:x + w - 2] = np.minimum(face + 40, 255)
    sc.occ[y:y + 20, x:x + w] = True
    letters(sc, t, x + w / 2, y + 5, "title", 8, col=DARK if lit else INK, outline=False, align="center")
    return w


# ---------------------------------------------------------------- the brood: everything hatched, eat the extra
def brood(variant=None):
    import brood as B
    sc = frame_screen(31)
    UI.engrave(sc, leader("Матка", "idle", 2.2), 640, 560, k=0.8)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 40, 920, 44, "#b06818", n=7, seed=3)
    title(sc, "ВЫВОДОК", seed=5)
    # biomass, top right
    icon(sc, "biomass", 712, 6, 2)
    letters(sc, "34", 752, 12, "title", 16, col=(170, 240, 120), col2=(70, 150, 50), jitter=1)
    fx_line(sc, 798, 12, "{съедена:5} → +5")
    help_button(sc)
    # the limit: an abdomen of segments
    total, eaten = B.totals()
    UI.plate(sc, 12, 50, 948, 96)
    fx_line(sc, 24, 54, "{предел}")
    letters(sc, f"{total}/{B.LIMIT}", 50, 56, "title", 16, col=(255, 140, 110), col2=(170, 50, 40), jitter=1)
    fx_line(sc, 24, 76, f"{{съедена:{eaten}}} из {total - B.LIMIT}", dim=True)
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
        glyph(sc, "предел", x0 + 106 + cw, y0 + 31, 1)
        letters(sc, str(B.pts(B.GROUPS[k_]) * count), x0 + 118 + cw, y0 + 34, "title", 8, col=PALE, outline=False)
        if eat:
            fx_line(sc, x0 + 100, y0 + 50, f"{{съедена:{eat}}} → +{eat * B.pts(B.GROUPS[k_])}")
        elif new:
            fx_line(sc, x0 + 100, y0 + 50, f"{{потомок:+{new}}}")
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
    fx_line(sc, 24, 412, "{убийство} → {потомок}")
    for i, (name, kills, key) in enumerate(B.SELECTION):
        x = 150 + i * 200
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
    for x0, x1, t, kind, col in ((12, 236, "Автоотбор", "chitin", INK), (246, 470, "Съесть новых", "blood", INK),
                                 (714, 948, f"В бой · съешь ещё {total - B.LIMIT - eaten}", "dim", PALE)):
        UI.button(sc, x0, 496, x1, 532, kind)
        letters(sc, t, (x0 + x1) / 2, 505, "text", 16, col=col, align="center")
    w_, _ = fx_line(sc, 0, 0, "{съедена} → {биомасса}", draw=False)
    fx_line(sc, 592 - w_ // 2, 505, "{съедена} → {биомасса}", dim=True)
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
    name = "brood.png"
    if variant == "tip":                         # the mouse over «съедена» in the ants' cell
        point_at(sc, "съедена", 2)
        name = "swarm_tip_glyph.png"
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)


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
    title(sc, "УЛЕЙ", seed=21)
    help_button(sc)
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
    fx_line(sc, 310, 84, "{выбор:1 из 3}", dim=True)
    offers = [("horn", "Рог", "деталь", ["{начало} → {урон:+2} {дроб}"], (236, 224, 196)),
              ("m_spinner", "Прядильные железы", "общая мутация", FX["spinner"][:2], (206, 206, 222)),
              ("m_nest", "Малое гнездо", "мутация Матки", FX["nest"], (240, 200, 90))]
    X, Y = sc.xx, sc.yy
    for k_, (key, name, kind, what, kcol) in enumerate(offers):
        y0 = 110 + k_ * 108
        UI.cell(sc, 306, y0, 642, y0 + 100, "hi" if k_ == 0 else ("hover" if k_ == 1 else "normal"))
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
        fx_rows(sc, 386, y0 + 46, 244, what[:1], dim=bool(k_))
    # what it becomes
    UI.plate(sc, 662, 52, 948, 446, antennae=True)
    UI.engrave(sc, bug((), "idle", 4.2, 70, soldier=True), 820, 330, col="#2a2234", k=0.9)
    heading(sc, "КАКИМ СТАНЕТ", 676, 64, seed=3)
    put(sc, W.build((), 0.03, "idle", True, k=2.3, genes=W.genes_for(70)), 728, 236, 26)
    put(sc, W.build(("ant", "horn"), 0.03, "idle", True, k=2.3, genes=W.genes_for(70)), 876, 236, 26)
    letters(sc, "сейчас", 728, 246, "text", 16, col=MUTED, align="center")
    letters(sc, "с рогом", 876, 246, "text", 16, col=GOLD, align="center")
    UI.silk(sc, (762, 190), (834, 190), sag=-6, col="#e8c050")
    fx_rows(sc, 676, 290, 262, offers[0][3] + ["{@horn} {наследие}"], lh=30)
    # leave / mutate
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Отказаться", 156, 486, "title", 16, col=INK, align="center")
    act_button(sc, 690, 466, 948, 524, "МУТИРОВАТЬ")

    cursor(sc, 560, 240)                         # the mouse over the second offer: its rim goes acid
    # the living
    UI.creature(sc, bug(("stinger",), "idle", 1.0, 71), 230, 54)
    UI.silk(sc, (600, 44), (600, 62), sag=0)
    UI.creature(sc, larva("idle", 0.8), 604, 76, shadow=False)
    UI.creature(sc, bug(("wings",), "idle", 1.0, 72), 930, 470)
    UI.creature(sc, clutch(0.9), 640, 448)
    UI.cobweb(sc, 2, 448, 28, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_camp.png"))
    print("swarm_camp.png", img.size)


# ---------------------------------------------------------------- the evolution of a form
def evolution(variant=None):
    import swarm_screens as SS
    import swarm_evo as EV
    sc = frame_screen(71)
    ALT[0] = variant == "alt"
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=8)
    title(sc, "ЭВОЛЮЦИЯ", seed=23)
    help_button(sc, alt=ALT[0])
    icon(sc, "biomass", 776 if ALT[0] else 830, 8, 2)
    letters(sc, "39", 816 if ALT[0] else 870, 10, "title", 16, col=(170, 240, 120), col2=(70, 150, 50), jitter=1)
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
    fx_line(sc, 326, 84, "{биомасса} 15 · 25 · 40", dim=True)
    nxt = SS.COSTS[len(taken)]
    for j, (key, ename, what, look) in enumerate(EV.EVO[form]):
        x0 = 322 + j * 208
        is_taken = key in taken
        UI.cell(sc, x0, 108, x0 + 200, 438, "hi" if j == 1 else ("new" if is_taken else "normal"))
        icon(sc, "evo_" + key, x0 + 12, 118, 2)
        letters(sc, ename, x0 + 50, 120, "text", 16, col=GOLD if j == 1 else INK, jitter=1, seed=j)
        if is_taken:
            letters(sc, "взята", x0 + 50, 138, "text", 16, col=GREEN)
        else:
            fx_line(sc, x0 + 50, 136, f"{{биомасса:{nxt}}}")
        fx_rows(sc, x0 + 12, 170, 180, EV.EVO_FX[key], lh=28)
        put(sc, W.build((form,), -0.08, "idle", False, k=3.2, genes=W.genes_for(3), evo=(key,)), x0 + 104, 350, 28)
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Назад", 156, 486, "title", 16, col=INK, align="center")
    act_button(sc, 660, 466, 948, 524, f"ВЗЯТЬ · {nxt}")
    UI.creature(sc, bug((), "idle", 1.0, 73), 200, 54)
    UI.creature(sc, bug(("horn",), "idle", 0.9, 74), 600, 448)
    UI.silk(sc, (700, 44), (700, 62), sag=0)
    UI.creature(sc, bug(("ant",), "attack", 0.85, 75, rare="spinner"), 706, 76, shadow=False)
    UI.cobweb(sc, 958, 448, 30, quad=(-1, 1))
    name = "swarm_alt_words.png" if ALT[0] else "swarm_evolution_screen.png"
    ALT[0] = False
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)


# ---------------------------------------------------------------- deployment by flocks
def deploy():
    import swarm_screens as SS
    import frames as F
    sc = frame_screen(75)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=5, seed=9)
    title(sc, "РАССТАНОВКА", seed=25)
    letters(sc, "Литейщик: 4 голема", 884, 12, "text", 16, col=(214, 196, 150), align="right")
    help_button(sc)
    UI.plate(sc, 660, 50, 948, 122)
    icon(sc, "matka", 670, 58, 2)
    letters(sc, "ТЕСНЫЕ СТАИ", 708, 57, "title", 8, col=GOLD, outline=False)
    fx_rows(sc, 708, 70, 230, ABIL_FX["Тесные стаи"], lh=24)
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
    fx_line(sc, GX0 + 6 * CW_ + 10, GY0 + 4 * CH_ + 10, "← {пара} → {потомок}")
    UI.plate(sc, 4, HH - 92, WW - 4, HH - 2)
    for k_, (traits, soldier, name, n, cells, col, placed) in enumerate([fl for fl in SS.FLOCKS if not fl[6]]):
        x0 = 12 + k_ * 150
        UI.cell(sc, x0, HH - 84, x0 + 142, HH - 10, "normal", col=col)
        put(sc, W.build(traits, 0.0, "idle", soldier, k=1.1, genes=W.genes_for(90 + k_)), x0 + 34, HH - 22, 10)
        for j, ln in enumerate(wrap(name.replace("-", "- "), 76)):
            letters(sc, ln.replace("- ", "-"), x0 + 62, HH - 80 + j * 16, "text", 16, col=INK, jitter=1, seed=k_ + j)
        letters(sc, f"×{n}", x0 + 62, HH - 42, "title", 8, col=GOLD, outline=False)
        letters(sc, "в запасе", x0 + 62, HH - 28, "title", 8, col=PALE, outline=False)
    for k_, t in enumerate(("в линию", "в кулак", "разделить", "как в прошлый")):
        x0, y0 = 318 + (k_ % 2) * 172, HH - 86 + (k_ // 2) * 40
        UI.button(sc, x0, y0, x0 + 164, y0 + 34, "chitin")
        letters(sc, t, x0 + 82, y0 + 9, "text", 16, col=INK, align="center")
    act_button(sc, 690, HH - 80, 948, HH - 20, "В БОЙ")
    UI.creature(sc, bug((), "idle", 0.9, 76), 420, HH - 92)
    UI.creature(sc, bug(("wings",), "idle", 0.9, 77), 930, HH - 94)
    UI.cobweb(sc, 958, 46, 40, quad=(-1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_deploy.png"))
    print("swarm_deploy.png", img.size)


# ---------------------------------------------------------------- the brood's finds, and what the leaders' pools add
FINDS_FX = [   # when each find comes, and what it gives (fxg.py)
    ("{конец} {порода:×2}", ["{потомок:×3} {порода}", "{мутация:✕}"]),
    ("{рабочая} {убийство:№1}", ["{кокон} → {солдат}"]),
    ("{дикие}", ["{новая_форма:×3}"]),
    ("{босс}", ["{потомок} → {гигант}"]),
    ("{добыча} {живой}", ["{потомок:1–2} → {химера}"]),
]


def finds():
    import brood as B
    from swarm_abilities import render_small
    WW_, HH_ = 960, 300
    UI.WOBBLE[0] = 1.3
    sc = UI.nest(WW_, HH_, 33)
    UI.wing(sc, 0, 0, WW_, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=5, seed=12)
    title(sc, "НАХОДКИ", seed=27)
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
    for i, (x0, (name, _, _), (when, what)) in enumerate(zip(xs, B.FINDS, FINDS_FX)):
        cx = x0 + CW_ / 2
        icon(sc, icons_[i], x0 + 10, 60)
        for j, ln in enumerate(wrap(name, CW_ - 40)):
            letters(sc, ln, x0 + 30, 61 + j * 17, "text", 16, col=GOLD, jitter=1, seed=i + j)
        for j, ln in enumerate([when] + what):
            w_, _ = fx_line(sc, 0, 0, ln, draw=False)
            fx_line(sc, int(cx - w_ / 2), (96 if j == 0 else by + 16 + (j - 1) * 28), ln, dim=(j == 0))
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
    title(sc, "МУТАЦИИ ЛИДЕРОВ", seed=29)
    PW_ = 232
    xs = [12 + i * (PW_ + 2) for i in range(4)]
    for x0 in xs:
        UI.cell(sc, x0, 52, x0 + PW_, 352, "find")
    heads = [("Брачный полёт", FX["flight"][0], "m_flight"), ("Гибрид", FX["hybrid"][0], "m_hybrid"),
             ("Откормленная", FX["fattened"][0], "m_fattened"), ("Чья мутация", None, "m_nest")]
    for x0, (h, sub, key) in zip(xs, heads):
        icon(sc, key, x0 + 12, 60, 2)
        letters(sc, h, x0 + 50, 62, "text", 16, col=GOLD, jitter=1, seed=len(h))
        if sub:
            fx_line(sc, x0 + 50, 80, sub.replace("{выводок} → ", ""))
    # mating flight
    x0 = xs[0]
    put(sc, W.build(("ant",), 0.05, "attack", False, k=1.9, genes=W.genes_for(61), rare="flight"), x0 + 60, 178, 14)
    for j, (tr, sol, sd, nm) in enumerate(((("horn",), True, 62, "жук"), (("stinger",), False, 63, "скорпион"), (("wings",), False, 64, "оса"))):
        cy = 110 + j * 62
        UI.cell(sc, x0 + 128, cy, x0 + 222, cy + 56, "hi" if j == 1 else "normal")
        put(sc, W.build(tr, 0.0, "idle", sol, k=1.0 if sol else 1.3, genes=W.genes_for(sd)), x0 + 160, cy + 48, 8)
        letters(sc, nm, x0 + 175, cy + 3, "text", 16, col=GOLD if j == 1 else MUTED, align="center")
    UI.silk(sc, (x0 + 76, 134), (x0 + 132, 196), sag=8, col="#f0c040")
    act_button(sc, x0 + 14, 300, x0 + PW_ - 14, 338, "СПАРИТЬ")
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
    w_, _ = fx_line(sc, 0, 0, FX["hybrid"][1], draw=False)
    fx_line(sc, int(x0 + PW_ / 2 - w_ / 2), 290, FX["hybrid"][1])
    # fattened
    x0 = xs[2]
    put(sc, W.build((), 0.05, "idle", False, k=1.9, genes=W.genes_for(68), rare="fattened"), x0 + 56, 168, 14)
    UI.meter(sc, x0 + 20, 186, x0 + 96, 8, 5, 3, "#e8c070")
    fx_line(sc, x0 + 20, 198, "{жир:3}")
    SA.arrow(sc, x0 + 104, x0 + 128, 140)
    put(sc, SL.build("Пожиратель", "idle", 0.42, stage=1), x0 + 180, 170, 18)
    fx_line(sc, x0 + 16, 240, FX["fattened"][1])
    UI.button(sc, x0 + 14, 300, x0 + PW_ - 14, 338, "blood")
    letters(sc, "СКОРМИТЬ", x0 + PW_ / 2, 312, "title", 16, col=INK, align="center")
    # whose mutation
    x0 = xs[3]
    rows = [("m_nest", "Матки", B.POOL_COL["Матка"]), ("m_psi_gland", "Разума", B.POOL_COL["Разум улья"]),
            ("m_sated", "Пожирателя", B.POOL_COL["Пожиратель"]), ("m_spores", "Чумы", B.POOL_COL["Чума"]),
            ("m_spinner", "общая", B.POOL_COL["общая"]), ("m_hybrid", "бесплоден", B.POOL_COL["бесплоден"])]
    for k_, (key, t, col) in enumerate(rows):
        y = 108 + k_ * 36
        icon(sc, key, x0 + 18, y, 2)
        letters(sc, t, x0 + 60, y + 8, "text", 16, col=col, jitter=1, seed=k_)
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
    title(sc, "СТАИ", seed=31)
    PW_ = 232
    xs = [12 + i * (PW_ + 4) for i in range(4)]
    for x0 in xs:
        UI.cell(sc, x0, 52, x0 + PW_, 322, "find")
    heads = [("Матка", "Тесные стаи", ABIL_FX["Тесные стаи"][0], ABIL_FX["Тесные стаи"][1]),
             ("Разум улья", "Одна мысль", ABIL_FX["Одна мысль на стаю"][0], "минус: лишний {урон} → ✕"),
             ("Пожиратель", "Свора", "{рой} {тело} → {лидер}", ABIL_FX["Свора"][2]),
             ("Чума", "Пёстрые стаи", ABIL_FX["Пёстрые стаи"][0], "минус: {скорость} у каждой своя")]
    for x0, (who, name, sub, minus) in zip(xs, heads):
        letters(sc, who, x0 + 12, 60, "title", 8, col=PALE, outline=False)
        letters(sc, name, x0 + 12, 72, "text", 16, col=GOLD, jitter=1, seed=len(name))
        fx_line(sc, x0 + 12, 94, sub)
        w_, _ = fx_line(sc, 0, 0, minus, draw=False)
        fx_line(sc, int(x0 + PW_ / 2 - w_ / 2), 290, minus)
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
    # Разум: the whole flock into one target, the other enemy left alone
    x0 = xs[1]
    t1, t2 = E.golem("Механик"), E.human("Изобретатель")
    put(sc, t1, x0 + 186, 214, 0)
    put(sc, t2, x0 + 196, 276, 0)
    for j, (dx, dy) in enumerate(((40, 160), (30, 196), (56, 232), (80, 182), (70, 262))):
        put(sc, bug(("scythes",), "attack", ZD, 110 + j), x0 + dx, dy, 0)
        UI.silk(sc, (x0 + dx + 10, dy - 10), (x0 + 166, 190), sag=-4, col="#c8a0ff")
    E.burst(sc, x0 + 170, 190, 9, hexc("#c8a0ff"))
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
    # Чума: one flock of all kinds, pairs inside it
    x0 = xs[3]
    cellbox(x0 + 24, 140, 184, 130, "#9ae060")
    kinds = [((), 130), (("wings",), 131), (("stinger",), 132), (("horn",), 133), (("acid",), 134), (("spitter",), 135)]
    pos = [(60, 176), (120, 170), (176, 182), (66, 230), (128, 236), (182, 250)]
    for (tr, sd), (dx, dy) in zip(kinds, pos):
        put(sc, bug(tr, "idle", ZD, sd), x0 + dx, dy, 0)
    UI.silk(sc, (x0 + 66, 214), (x0 + 128, 222), sag=8, col="#f0c040")
    UI.silk(sc, (x0 + 120, 156), (x0 + 176, 166), sag=8, col="#f0c040")
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
            cx0, cy0, cx1 = 572, 296, 826
            rows_ = ["{каждые:2} → {яд} {клей:1} {дальность:3}", "{перезарядка:1}", "минус: {атака} → {урон:−}"]
            cy1 = fx_rows(sc, cx0 + 10, cy0 + 44, cx1 - cx0 - 20, rows_, draw=False) + 10
            UI.cell(sc, cx0, cy0, cx1, cy1, "hi")
            icon(sc, "spitter", cx0 + 8, cy0 + 6, 2)
            letters(sc, "Паук-плевун", cx0 + 44, cy0 + 10, "text", 16, col=GOLD, jitter=1, seed=7)
            letters(sc, "рабочая", cx0 + 44, cy0 + 26, "title", 8, col=PALE, outline=False)
            fx_rows(sc, cx0 + 10, cy0 + 44, cx1 - cx0 - 20, rows_)
            cursor(sc, sx_ - 2, sy_ - 14)
            name = "swarm_battle_pause.png"
        img = sc.image(S)
        UI.WOBBLE[0] = 0.0
        img.save(out(name))
        print(name, img.size)


# ---------------------------------------------------------------- after the battle: the battle changes the breed
def aftermath(variant=None):
    import brood as B
    import swarm_effects as E
    sc = frame_screen(37)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=17)
    title(sc, "ПОБЕДА", seed=33)
    help_button(sc)
    # losses
    UI.plate(sc, 12, 52, 300, 446, antennae=True)
    heading(sc, "ПОТЕРИ", 26, 64, seed=6)
    for j in range(9):
        put(sc, E.lit(bug(((), ("stinger",), ("wings",))[j % 3], "idle", 1.25, 160 + j), (26, 18, 16), 0.7), 56 + (j % 3) * 76 + (j // 3) * 14, 132 + (j // 3) * 34, 9)
    fx_line(sc, 26, 262, "{гибель_своя}")
    letters(sc, "23", 64, 254, "title", 24, col=(255, 140, 110), col2=(170, 50, 40), jitter=1, drips=3)
    fx_line(sc, 26, 322, "{добыча}")
    letters(sc, "14", 64, 314, "title", 24, col=(170, 240, 120), col2=(70, 150, 50), jitter=1)
    fx_line(sc, 120, 322, "→ {биомасса:+14}")
    # what the battle gave: the leader's own gift
    UI.plate(sc, 310, 52, 652, 446, antennae=True)
    UI.engrave(sc, leader("Матка", "idle", 1.6), 560, 470, col="#2a2234", k=0.9)
    heading(sc, "ДАР МАТКИ", 324, 64, seed=7)
    fx_line(sc, 324, 92, "{конец} {личинка:×3} → {выводок}")
    for j, dx in enumerate((380, 440, 500)):
        put(sc, larva("idle", 1.5), dx, 196, 12)
    icon(sc, "stinger", 560, 168, 2)
    fx_line(sc, 324, 226, "{черта_боя} → {@stinger} жало")
    UI.cell(sc, 320, 268, 642, 340, "mut")
    letters(sc, "Сердце роя", 334, 278, "text", 16, col=GOLD, jitter=1)
    fx_line(sc, 334, 302, "{яйцо:5} → {личинка:5} → {выводок}")
    put(sc, clutch(1.0), 580, 330, 0)
    UI.cell(sc, 320, 352, 642, 436, "normal")
    fx_line(sc, 334, 360, "{убийство} → {потомок}", dim=True)
    for i, (name, kills, key) in enumerate(B.SELECTION):
        x, y = 334 + i * 76, 384
        icon(sc, key, x, y)
        letters(sc, str(kills), x + 20, y + 4, "title", 8, col=PALE, outline=False)
        UI.meter(sc, x, y + 24, x + 64, 6, 8, round(8 * kills / 23), "#c04a3a" if i == 0 else "#8a6aa8")
    # pairs at the seams of the flocks, and the find
    UI.plate(sc, 662, 52, 948, 446, antennae=True)
    heading(sc, "ПАРЫ", 676, 64, seed=8)
    fx_line(sc, 676, 92, "{пара:3} → {потомок}")
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
    fx_rows(sc, 684, 366, 250, ["{рабочая} {убийство:№1}", "{кокон} → {солдат}"], lh=26)
    put(sc, bug(("ant", "stinger"), "idle", 1.1, 77, soldier=True), 900, 426, 10)
    act_button(sc, 690, 466, 948, 524, "В ВЫВОДОК")
    UI.creature(sc, bug((), "idle", 1.0, 170), 250, 54)
    UI.cobweb(sc, 2, 448, 30, quad=(1, 1))
    name = "swarm_aftermath.png"
    if variant == "tip":                         # the mouse over the stinger: the trait itself
        point_at(sc, "@stinger", 0, w=300)
        name = "swarm_tip_trait.png"
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)


# ---------------------------------------------------------------- choosing the leader at the start of the run
ACID, ACID2 = (176, 244, 70), (236, 255, 140)


def dilate(m, d=1):
    out = m.copy()
    for _ in range(d):
        out = out | np.roll(out, 1, 0) | np.roll(out, -1, 0) | np.roll(out, 1, 1) | np.roll(out, -1, 1)
    return out


def neon(sc, m, col, width=5, k=0.55):
    """A glowing rim around a shape: a hard line of light, then a fading haze outside it."""
    col = np.array(col, float)
    prev = m
    for d in range(1, width + 1):
        ring = dilate(prev, 1) & ~prev
        a = k * (1 - (d - 1) / width) ** 1.6
        sc.rgb[ring] = sc.rgb[ring] * (1 - a) + col * a
        prev = prev | ring
    o, _, _ = UI.edges(m)
    sc.rgb[o] = np.minimum(255, col * 1.1 + 20)


def ellipse(sc, cx, cy, rx, ry, p=2.0):
    return (np.abs(sc.xx - cx) / rx) ** p + (np.abs(sc.yy - cy) / ry) ** p <= 1


def thick(sc, pts, w, col, hi=None):
    """A thick jointed line through points: a dark outline, a body, a lit top edge."""
    for (a_, b_) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(b_[0] - a_[0]), abs(b_[1] - a_[1]))) + 1
        for t in np.linspace(0, 1, n):
            x, y = int(a_[0] + (b_[0] - a_[0]) * t), int(a_[1] + (b_[1] - a_[1]) * t)
            sc.rgb[y - w:y + w + 1, x - w:x + w + 1] = UI.OUTL
    for (a_, b_) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(b_[0] - a_[0]), abs(b_[1] - a_[1]))) + 1
        for t in np.linspace(0, 1, n):
            x, y = int(a_[0] + (b_[0] - a_[0]) * t), int(a_[1] + (b_[1] - a_[1]) * t)
            sc.rgb[y - w + 1:y + w, x - w + 1:x + w] = col
            if hi is not None:
                sc.rgb[y - w + 1, x] = hi
    sc.occ[...] |= False


def bug_card(sc, cx, y0, name, sel, seed):
    """A leader's card shaped as a beetle: a head with compound eyes, sickle mandibles and elbowed antennae; the
    pronotum bearing the name and the by-name, spined at the shoulders; the elytra holding the leader, a seam down
    the middle, rows of pits, parting at the tips over a glowing wing; six jointed legs; acid dripping off the tips.
    The chosen one burns acid-bright; the others smoulder."""
    import swarm_leaders as SL
    ep, ecol = EPITHET[name]
    glow = ACID if sel else tuple(int(v * 0.5) for v in ACID)
    G = np.array(glow, float)
    rnd = np.random.RandomState(seed)
    X, Y = sc.xx, sc.yy
    dy = Y - y0
    if sel:
        sc.glow(cx, y0 + 200, 185, hexc("#9ae030"), 0.32)
    # six legs from under the elytra: femur up and out, tibia down with spikes, a hooked tarsus
    for side in (-1, 1):
        for j, ly in enumerate((y0 + 116, y0 + 168, y0 + 220)):
            p0 = (cx + side * 80, ly)
            p1 = (cx + side * 100, ly - 14 + j * 5)
            p2 = (cx + side * 110, ly + 24 + j * 5)
            p3 = (cx + side * 114, ly + 36 + j * 5)
            thick(sc, [p0, p1], 2, hexc("#3a2c46"), G * 0.8)
            thick(sc, [p1, p2, p3], 1, hexc("#4a3a58"), G * 0.8)
            sc.rgb[int(p1[1]) - 1:int(p1[1]) + 2, int(p1[0]) - 1:int(p1[0]) + 2] = G
            for t in (0.35, 0.7):
                x, y = int(p1[0] + (p2[0] - p1[0]) * t), int(p1[1] + (p2[1] - p1[1]) * t)
                sc.rgb[y - 4:y, x + side * 2] = UI.OUTL
                sc.rgb[y - 3:y, x + side * 2] = hexc("#8a7a9a")
    # elbowed antennae with glowing clubs
    for side in (-1, 1):
        base, elbow, tipp = (cx + side * 12, y0 + 6), (cx + side * 22, y0 - 10), (cx + side * 48, y0 - 6)
        thick(sc, [base, elbow, tipp], 1, hexc("#4a3a58"), G * 0.7)
        sc.rgb[int(tipp[1]) - 2:int(tipp[1]) + 3, int(tipp[0]) - 2:int(tipp[0]) + 3] = np.array(ACID2 if sel else glow, float)
        sc.glow(tipp[0], tipp[1], 9, G, 0.5)
    # the body outline, row by row
    hw = np.zeros(Y.shape, float)
    r_head = (dy >= 0) & (dy < 36)
    hw[r_head] = 34 * np.sqrt(np.clip(1 - ((dy[r_head] - 18) / 19) ** 2, 0, 1))
    r_pro = (dy >= 34) & (dy < 88)
    hw_pro = np.where(dy < 70, 78 + 10 * np.sin(np.pi / 2 * np.clip((dy - 34) / 36, 0, 1)), 88 - 4 * (dy - 70) / 18)
    hw[r_pro] = hw_pro[r_pro]
    r_ely = (dy >= 90) & (dy < 384)
    hw_ely = np.where(dy < 300, 86, 86 * np.sqrt(np.clip(1 - ((dy - 300) / 84) ** 2, 0, 1)) ** 0.9)
    hw[r_ely] = hw_ely[r_ely]
    body = (np.abs(X - cx) <= hw) & (hw > 0)
    pron = body & r_pro
    ely = body & r_ely
    parted = ely & (dy > 318) & (np.abs(X - cx) < (dy - 318) * 0.42)   # the elytra part at the tips
    ely = ely & ~parted
    for side in (-1, 1):                                       # shoulder spines on the pronotum
        for k_ in range(12):
            yy, xx = y0 + 62 - k_ * 0.5, cx + side * (87 + k_)
            body[int(yy) - max(0, 2 - k_ // 4):int(yy) + 1, int(xx)] = True
    neon(sc, body, glow, 6 if sel else 4, 0.6 if sel else 0.4)
    t = np.clip(dy / 384, 0, 1)[..., None]
    fill = hexc("#30223a") * (1 - t) + hexc("#0c0810") * t
    sc.rgb[body] = fill[body]
    # the wing glowing in the parting
    sc.rgb[parted] = sc.rgb[parted] * 0.3 + G * 0.55
    for k_ in range(3):
        vein = parted & (np.abs((X - cx) - (dy - 318) * (k_ - 1) * 0.2) < 0.6)
        sc.rgb[vein] = np.array(ACID2, float)
    # elytra: a faint comb, rows of pits, a seam with the scutellum at its top, a sheen down each side
    UI.comb(sc, ely, cx - 86, y0 + 90, G, 0.1, R=7)
    for col_ in (-64, -44, -24, 24, 44, 64):
        for yy in range(int(y0 + 100), int(y0 + 330), 7):
            if ely[yy, int(cx + col_)]:
                sc.rgb[yy, int(cx + col_)] = sc.rgb[yy, int(cx + col_)] * 0.45
    seam = ely & (np.abs(X - cx) < 1)
    sc.rgb[seam] = UI.OUTL
    scut = (dy >= 88) & (dy < 108) & (np.abs(X - cx) <= (108 - dy) * 0.55)
    sc.rgb[scut] = hexc("#46345a")
    for side in (-1, 1):
        d_ = np.abs(X - (cx + side * 60))
        sh = ely & (d_ < 9) & (dy > 96) & (dy < 320)
        a_ = (0.16 * (1 - d_ / 9))[..., None]
        sc.rgb[sh] = (sc.rgb * (1 - a_) + hexc("#6a9a7e") * a_)[sh]
    groove = body & (dy >= 86) & (dy < 90)                     # the joint between pronotum and elytra
    sc.rgb[groove] = UI.OUTL
    psheen = pron & (((X - cx) / 60) ** 2 + ((Y - (y0 + 44)) / 7) ** 2 <= 1)
    sc.rgb[psheen] = sc.rgb[psheen] * 0.7 + hexc("#5a7a66") * 0.3
    # compound eyes, sickle mandibles
    for side in (-1, 1):
        eye = ellipse(sc, cx + side * 27, y0 + 18, 8, 12) & ~ellipse(sc, cx + side * 17, y0 + 20, 5, 9)
        sc.rgb[eye] = np.array(ecol, float) * (0.85 if sel else 0.5)
        fac = eye & (((X + Y) % 3 == 0) | ((X - Y) % 3 == 0))
        sc.rgb[fac] = sc.rgb[fac] * 0.6
        hi = ellipse(sc, cx + side * 29, y0 + 11, 2, 3)
        sc.rgb[hi & eye] = hexc("#ffffff") * 0.85
        sc.glow(cx + side * 27, y0 + 18, 14, np.array(ecol, float), 0.3 if sel else 0.15)
        eo, _, _ = UI.edges(eye)
        sc.rgb[eo] = UI.OUTL
    for side in (-1, 1):
        pts = [(cx + side * (20 - 26 * tt), y0 + 28 + 12 * np.sin(tt * 2.2)) for tt in np.linspace(0, 1, 9)]
        thick(sc, pts[:6], 2, hexc("#bda97a"), hexc("#fff4d0"))
        thick(sc, pts[5:], 1, hexc("#e8dcb0"), hexc("#ffffff"))
    # the name and the by-name on the pronotum
    letters(sc, name.upper(), cx, y0 + 40, "title", 16, col=ACID2 if sel else INK, col2=(90, 150, 40) if sel else None,
            jitter=1, hairs=4, seed=seed, align="center")
    w = UI.text_width(ep, "title", 16)
    epithet(sc, ep, cx - w / 2, y0 + 62, ecol, seed=seed + 3, px=16, curls=False)
    # the leader on the elytra
    spr = SL.build(name, "idle", 1.0)
    kk = min(2.2, 158 / spr.w, 176 / spr.h)
    lead = SL.build(name, "idle", kk)
    if not sel:
        import swarm_effects as E
        lead = E.lit(lead, (20, 30, 16), 0.25)
    put(sc, lead, cx + 4, y0 + 262, 44)
    # acid off the tips
    for side in (-1, 1):
        x = cx + side * 9
        for i in range(6):
            sc.rgb[int(y0 + 380 + i), int(x)] = np.array(ACID2 if sel else glow, float)
        drop = ellipse(sc, x, y0 + 389, 2.2, 3)
        sc.rgb[drop] = np.array(ACID2, float)
        sc.glow(x, y0 + 388, 9, hexc("#b8f040"), 0.5 if sel else 0.25)
    pud = ellipse(sc, cx, y0 + 398, 24 + rnd.randint(0, 6), 3)
    sc.rgb[pud] = sc.rgb[pud] * 0.4 + G * 0.6
    sc.glow(cx, y0 + 398, 26, hexc("#9ae030"), 0.3 if sel else 0.15)


def leaders_pick():
    sc = frame_screen(41)
    X, Y = sc.xx, sc.yy
    fog = np.clip((Y - 300) / 240, 0, 1)[..., None] * 0.22    # acid haze rising from the floor
    sc.rgb[:] = sc.rgb * (1 - fog) + np.array((60, 110, 20), float) * fog
    rnd = np.random.RandomState(7)
    for _ in range(40):                                          # bubbles
        bx, by, br = rnd.randint(10, 950), rnd.randint(300, 470), rnd.choice((1, 1, 2, 3))
        ring = (np.abs(np.hypot(X - bx, Y - by) - br) < 0.7)
        sc.rgb[ring] = sc.rgb[ring] * 0.4 + np.array(ACID, float) * 0.6
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#7ab020", n=8, seed=18)
    w = letters(sc, "ЛИДЕР", 16, 6, "title", 24, col=(236, 216, 170), col2=(150, 96, 60), jitter=1, drips=6, hairs=9, seed=35)
    epithet(sc, "КТО СОЖРЕТ ИХ ВСЕХ", 16 + w + 44, 10, ACID, seed=36, px=24)
    help_button(sc)
    names = ["Матка", "Разум улья", "Пожиратель", "Чума"]
    for i, name in enumerate(names):
        bug_card(sc, 132 + i * 232, 60, name, i == 0, seed=40 + i)
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Назад", 156, 486, "title", 16, col=INK, align="center")
    UI.button(sc, 326, 470, 634, 520, "chitin")
    letters(sc, "ПОЛНОЕ ОПИСАНИЕ", 480, 486, "title", 16, col=ACID2, align="center")
    UI.button(sc, 660, 466, 948, 524, "acid")
    letters(sc, "В ПОХОД", 804, 486, "title", 16, col=ACID2, col2=(110, 170, 40), align="center", jitter=1, hairs=4)
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
    title(sc, "РАЗВИТИЕ", seed=37)
    help_button(sc)
    UI.plate(sc, 12, 52, 300, 446, antennae=True)
    heading(sc, "СЕЙЧАС", 26, 64, seed=9)
    icon(sc, "razum", 26, 90, 2)
    letters(sc, "Разум улья", 64, 94, "text", 16, col=INK, jitter=1, seed=4)
    put(sc, SL.build("Разум улья", "idle", 2.1), 156, 276, 34)
    fx_rows(sc, 26, 300, 260, ["{пси} {дальность:3}", "{захват} {каждые:6}", "{помутнение} {радиус:2}",
                               "минус: {мягкое}"], lh=28)
    for j, (key, name, look) in enumerate(SL.DEV["Разум улья"]):
        x0 = 312 + j * 214
        UI.cell(sc, x0, 52, x0 + 206, 446, "hi" if j == 1 else "normal")
        put(sc, SL.build("Разум улья", "idle", 1.9, dev=key), x0 + 103, 272, 30)
        letters(sc, name, x0 + 14, 300, "text", 16, col=GOLD if j == 1 else INK, jitter=1, seed=j)
        fx_line(sc, x0 + 14, 330, DEV_FX["Разум улья"][key])
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Позже", 156, 486, "title", 16, col=INK, align="center")
    act_button(sc, 690, 466, 948, 524, "ПРОРАСТИ")
    UI.creature(sc, bug((), "idle", 1.0, 190), 540, 54)
    UI.cobweb(sc, 2, 448, 30, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_development_screen.png"))
    print("swarm_development_screen.png", img.size)


# ---------------------------------------------------------------- the creature's card: who it is, what it can, where it came from
SILVER = (200, 206, 220)


FXZ = 2                                       # glyphs in effect lines: twice their pixel size, as big as the letters


def fx_line(sc, x, y, line, dim=False, draw=True, z=None):
    """One line of terms (fxg.py): each term its glyph, its number after it in gold, arrows and words between.
    A line starting «минус:» is a drawback, in red. Returns the width and where each glyph went."""
    import fxg
    z = FXZ if z is None else z
    neg = line.startswith("минус:")
    tcol = (236, 150, 130) if neg else (MUTED if dim else INK)
    cx, spots = x, []
    if neg:
        if draw:
            letters(sc, "минус:", cx, y, "text", 16, col=RED)
        cx += UI.text_width("минус: ")
        line = line[len("минус:"):].strip()
    for part in fxg.parts(line):
        if part[0] == "t":
            if draw and part[1].strip():
                letters(sc, part[1], cx, y, "text", 16, col=tcol)
            cx += UI.text_width(part[1])
        elif part[1].startswith("@"):                          # a trait's or ability's own icon, «{@stinger}»
            spr = IC.icon(part[1][1:], 1, "swarm")
            if draw:
                icon(sc, part[1][1:], cx + 1, int(y + 9 - spr.h / 2))
                HOVER.append((part[1], int(cx + 1), int(y + 9 - spr.h / 2), spr.w, spr.h))
            cx += spr.w + 4
            val = part[2]
            if val:
                if draw:
                    letters(sc, val, cx - 1, y, "text", 16, col=(255, 214, 110))
                cx += UI.text_width(val) + 2
        else:
            _, key, val = part
            a_ = fxg.rgba(key)
            gh, gw = a_.shape[0] * z, a_.shape[1] * z
            gy = int(y + 9 - gh / 2)
            if draw:
                fxg.draw(sc, key, cx + 1, gy, z)
                HOVER.append((key, int(cx + 1), gy, gw, gh))
            spots.append((key, cx + 1, gy, gw, gh))
            cx += gw + 4
            if val:
                if draw:
                    letters(sc, val, cx - 1, y, "text", 16, col=(255, 214, 110) if not neg else RED)
                cx += UI.text_width(val) + 2
    return cx - x, spots


def fx_rows(sc, x, y, w, rows, lh=26, dim=False, draw=True):
    """A column of effect lines. Returns the y under the last. With Alt held each line is read out under itself."""
    for line in rows:
        fx_line(sc, x, y, line, dim=dim, draw=draw)
        y += lh
        if ALT[0]:
            y = alt_words(sc, x, y - 4, w, line, draw) + 6
    return y


def alt_words(sc, x, y, w, line, draw=True):
    """The Alt view: a line of terms in small words, wrapped to the width. Returns the y under it."""
    import fxg
    text = fxg.words(line, names=lambda k: TRAIT_TIP.get(k, (k,))[0].lower())
    parts_, cur = [], ""
    for wd in text.split(" "):
        if UI.text_width((cur + " " + wd).strip(), "text", 16) > w and cur:
            parts_.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    for j, ln in enumerate(parts_ + [cur]):
        if draw:
            letters(sc, ln, x, y + j * 17, "text", 16, col=(200, 178, 118))
    return y + 17 * (len(parts_) + 1)


def gloss_tip(sc, key, x, y, w=250, draw=True):
    """What a glyph means, under the mouse: the glyph large, its name, one line of meaning. A trait's icon
    («@stinger») shows the trait: its name, what it is and what it does, in terms."""
    import fxg
    if key.startswith("@"):
        nm, kind, rows = TRAIT_TIP[key[1:]]
        h = fx_rows(sc, 0, 0, w - 24, rows, draw=False) + 46
        if draw:
            UI.cell(sc, x, y, x + w, y + h, "normal")
            icon(sc, key[1:], x + 10, y + 8, 2)
            letters(sc, nm, x + 48, y + 8, "text", 16, col=GOLD)
            letters(sc, kind, x + 48, y + 26, "title", 8, col=PALE, outline=False)
            fx_rows(sc, x + 12, y + 46, w - 24, rows)
        return h
    nm, what, _ = fxg.TERMS[key]
    lines = wrap(what, w - 24)
    h = 46 + len(lines) * 16
    if draw:
        UI.cell(sc, x, y, x + w, y + h, "normal")
        fxg.draw(sc, key, x + 12, y + 10, 2)
        letters(sc, nm, x + 44, y + 12, "text", 16, col=GOLD)
        for j, ln in enumerate(lines):
            UI.rich(sc, ln, x + 12, y + 36 + j * 16, "text", 16, col=INK)
    return h


def point_at(sc, key, nth=0, w=260):
    """The mouse over a glyph already on the screen: the cursor on it, its tooltip under it (over it, near the bottom)."""
    spots = [sp for sp in HOVER if sp[0] == key]
    k_, gx, gy, gw, gh = spots[nth]
    h = gloss_tip(sc, key, 0, 0, w, draw=False)
    tx = int(min(max(8, gx + gw // 2 - 24), WW - 8 - w))
    ty = gy + gh + 10 if gy + gh + 10 + h < HH - 8 else gy - h - 10
    gloss_tip(sc, key, tx, ty, w)
    cursor(sc, gx + gw // 2, gy + gh // 2)


TRAIT_TIP = {   # a trait's icon in a line points at the trait itself: name, what it is, what it does
    "stinger": ("Жало", "деталь формы", ["{пробой} → {яд:1–4} {броня:−1}", "{машина} → {яд:✕}"]),
    "horn": ("Рог", "деталь", ["{начало} → {урон:+2} {дроб}"]),
    "wings": ("Крылья", "деталь формы", ["{всегда} → {полёт}"]),
}


ABIL_FX = {   # the abilities on the cards, in terms (fxg.py)
    "Кладка": ["{каждые:3} → {призыв} {личинка:×2}", "{конец} {личинка} → {выводок} {черта_боя}"],
    "Сердце роя": ["{гибель_своя} {радиус:2} → {яйцо}", "{яйцо} {через:2} → {личинка}"],
    "Плодовитость": ["{выводок} → {потомок:+1}", "{улей} → {кормление:×½}"],
    "Тесные стаи": ["{клетка} → {рабочая:×6}", "минус: {площадь} → {клетка}"],
    "Медлительная": ["{всегда} → {скорость:1}", "{гибель} → {рой} {страх:1–9}"],
    "Помутнение": ["{каждые:3} → {помутнение:1} {радиус:2}", "{машина} → {сбой}"],
    "Предсмертный крик": ["{гибель_своя} → {убийца} {пси:1} {мимо}", "{машина} → {пси:1} / {гибель_своя:2}"],
    "Захват разума": ["{каждые:6} → {захват} {цель} {полрана}", "{размер:1–3} → {на:5}", "{размер:4–5} → {на:2}",
                      "{размер:6–7} → {оглушение:1}"],
    "Мыслящая порода": ["{выводок} → {мутация} {пси}"],
    "Одна мысль на стаю": ["{всегда} → {одна_цель}"],
    "Хрупкий мозг": ["{всегда} → {мягкое}", "{гибель} → {рой} {страх:1–9}"],
    "Рост": ["{тело:2} → {рост}", "{рост:×2} → {размер:7}"],
    "Каннибал": ["{гибель_своя} {радиус:1} → {тело} {лечение}"],
    "Всё в пасть": ["{конец} → {биомасса:+1} / {тело}", "минус: {рой:−}"],
    "Свора": ["{рой} → {лидер}", "{тело} → {лидер}", "минус: {тело} → {лечение:✕}"],
    "Ненасытный": ["{голод:3} → {тело} {свой}", "{голод:3} {свой:0} → {здоровье:−10%} {каждые:1}"],
    "Заражение": ["{пробой} → {заражение}", "{заражение} {гибель} → {личинка:×2}",
                  "{машина} {заражение} → {личинка} {каждые:3}"],
    "Длинный яйцеклад": ["{всегда} → {дальность:2} {инициатива:+3}"],
    "Подкидыш": ["{начало} → {рабочая} {тыл}"],
    "Дети хозяина": ["{заражение} {личинка} → {химера}", "{конец} {личинка} → {выводок}"],
    "Чужие черты": ["{выводок} → {химера:×2}"],
    "Пёстрые стаи": ["{всегда} → {пёстрая}", "{выводок} → {пара} {пёстрая}"],
    "Хрупкая кладка": ["{огонь} → {заражение:✕}"],
    "Жало": ["{пробой} → {яд:1–4} {броня:−1}", "{машина} → {яд:✕}"],
    "Крылья": ["{всегда} → {полёт}"],
    "Клешни-тиски": ["{атака} → {дроб} {прикован}"],
    "Хитин": ["{всегда} → {руб} ×½ · {дроб} ×2"],
    "Стая": ["{всегда} → {дух:+1} / {свой} {радиус:1} · ≤ +4"],
    "Пожирание": ["{убийство} → {тело} {лечение:25%}", "{конец} → {биомасса}"],
    "Медленнее других": ["{всегда} → {скорость:2}"],
}


DEV_FX = {   # a leader's growth, as what it changes (fxg.py)
    "Матка": {"often": "{личинка:×2} {каждые:3} → {каждые:2}", "larva": "{каждые:3} {личинка:×2} → {личинка:×3}",
              "size": "{размер:6} → {размер:7}"},
    "Разум улья": {"two": "{захват} {каждые:6} → {каждые:4}", "every": "{пси} {дальность:3} → {дальность:4}",
                   "strike": "{помутнение} {радиус:2} → {радиус:3}"},
    "Пожиратель": {"bigger": "{начало} {размер:5} → {размер:6}", "every_kill": "{рост} {тело:2} → {тело:1}",
                   "heal": "{лечение} → {лечение:×2}"},
    "Чума": {"three": "{заражение} {личинка:×2} → {личинка:×3}", "venom": "{яд} → {заражение}",
             "two": "{тыл} {рабочая:×1} → {рабочая:×2}"},
}


def dev_choice(name):
    import swarm_leaders as SL
    return ("fx", "на выбор", [DEV_FX[name][k] for k, _, _ in SL.DEV[name]])


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


def hexmask(sc, cx, cy, r):
    X, Y = np.abs(sc.xx - cx), np.abs(sc.yy - cy)
    return (X <= r * 0.866) & (Y <= r - X * 0.577)


def comb_cell(sc, cx, cy, r, state, key=None):
    """One cell of a leader's comb. lived — such a one is in the swarm now; open — it has woken this run;
    sealed — it has not woken yet (a wax cap, nothing to see); hover — the one under the mouse."""
    m, inner = hexmask(sc, cx, cy, r), hexmask(sc, cx, cy, r - 3)
    rim = {"lived": "#7ac040", "open": "#c88a2a", "hover": "#ffd070", "sealed": "#4a3e5c",
           "key": "#f0c050", "keysealed": "#8a6a2a", "sealedhover": "#b8f040"}[state]
    if state == "sealedhover":                                 # under the mouse it lights up, but stays shut
        sc.glow(cx, cy, r * 1.7, hexc("#9ae030"), 0.35)
    sc.rgb[m] = hexc(rim)
    if state in ("sealed", "keysealed", "sealedhover"):    # a wax cap: domed, a little lighter on top
        t = np.clip((sc.yy - (cy - r)) / (2 * r), 0, 1)[..., None]
        cap = hexc("#4a3c34") * (1 - t) + hexc("#241a1c") * t
        sc.rgb[inner] = cap[inner]
        dome = hexmask(sc, cx - r * 0.18, cy - r * 0.28, r * 0.32)
        sc.rgb[dome & inner] = sc.rgb[dome & inner] * 0.6 + hexc("#8a7458") * 0.4
    else:
        sc.rgb[inner] = hexc("#1c1420")
        if state == "hover":
            sc.glow(cx, cy, r * 1.6, hexc("#ffd070"), 0.35)
    o, _, _ = UI.edges(m)
    sc.rgb[o] = UI.OUTL
    sc.occ[m] = True
    sc.light[m] = 0
    if key and state not in ("sealed", "keysealed", "sealedhover"):
        icon(sc, key, cx - 16, cy - 16, 2)


def crown(sc, cx, top):
    """A small crown over the royal cell: the key mutation."""
    rows = ["o..o..o..o", "oAoAooAoAo", "oAAAAAAAAo", "oaAaAAaAao", "oAAAAAAAAo", "oooooooooo"]
    col = dict(o=UI.OUTL, A=hexc("#e8a838"), a=hexc("#fff0a0"))
    z = 2
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                yy, xx = int(top) + j * z, int(cx) - 5 * z + i * z
                sc.rgb[yy:yy + z, xx:xx + z] = col[ch]
    sc.glow(cx, top + 6, 16, hexc("#f0c050"), 0.35)


def pict_flight(sc, x0, y, x1):
    """Брачный полёт, without words: she, a thread, three of the survivors — the player's cursor on one of them."""
    me = bug(("wings",), "idle", 1.3, 41, rare="flight")
    put(sc, me, x0 + 34, y + 40, 10)
    cands = [(("horn",), 42), (("stinger",), 43), (("wings",), 44)]
    xs = [x0 + 150 + i * 52 for i in range(3)]
    sc.glow(xs[1], y + 32, 26, hexc("#ffd070"), 0.35)
    for t in np.linspace(0, 2 * np.pi, 80):                # the chosen one, ringed
        sc.rgb[int(y + 42 + np.sin(t) * 5), int(xs[1] + np.cos(t) * 20)] = hexc("#ffd070")
    UI.silk(sc, (x0 + 56, y + 22), (xs[1] - 14, y + 22), sag=-10, col="#f0c040")
    for i, ((tr, sd), cx) in enumerate(zip(cands, xs)):
        put(sc, bug(tr, "idle", 1.0, sd), cx, y + 40, 8)
    letters(sc, "?", xs[0], y - 4, "title", 8, col=PALE, outline=False, align="center")
    letters(sc, "?", xs[2], y - 4, "title", 8, col=PALE, outline=False, align="center")
    cursor(sc, int(xs[1]) + 2, int(y) + 22)


PICT = {"Брачный полёт": (pict_flight, FX["flight"])}


def leader_comb(sc, x0, y, rows, key, hover):
    """The leader's mutations as a comb: a row of cells per branch, the key one a big royal cell at the end."""
    r, step = 21, 21 * 1.732
    off = max(UI.text_width(br) for br, _ in rows) + 16 + r
    pos, right = {}, 0
    for j, (branch, cells) in enumerate(rows):
        cy = y + j * r * 1.5
        UI.rich(sc, branch, x0, cy - 8, "text", 16, col=MUTED)
        for i, (k_, st, nm, desc) in enumerate(cells):
            cx = x0 + off + i * step + (step / 2 if j % 2 else 0)
            if nm == hover:
                st = "sealedhover" if st == "sealed" else "hover"
            comb_cell(sc, cx, cy, r, st, k_)
            pos[nm] = (cx, cy, nm, desc, st)
            right = max(right, cx + r)
    k_, st, nm, desc = key
    kx, ky = right + 40, y + r * 1.5 * (len(rows) - 1) / 2
    sc.glow(kx, ky, 40, hexc("#f0c050"), 0.25)
    comb_cell(sc, kx, ky, 30, st, k_)
    crown(sc, kx, ky - 30 - 13)
    pos[nm] = (kx, ky, nm, desc, st)
    return pos, y + r * 1.5 * (len(rows) - 1) + 34


def big_card(spec, name, save=True):
    """A creature's card as big as the screen, as in Conquest of Elysium: the creature large on the left with where
    it came from; the numbers in a column; every attack in a column of its own — damage, type, reach, what it does
    besides; on the right what it can and what it can't, each with its icon."""
    sc = frame_screen(spec["seed"])
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=spec["seed"])
    title(sc, spec["title"], spec["sub"], seed=spec["seed"] + 1, epi=spec.get("epi"))
    help_button(sc)
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
        elif kind == "fx":
            lab, rows = row
            letters(sc, lab, 22, y, "title", 8, col=PALE, outline=False)
            y = fx_rows(sc, 22, y + 12, 270, rows, lh=26) + 8
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
    import fxg
    STAT = {"здоровье": "здоровье", "броня": "броня", "скорость": "скорость", "боевой дух": "дух", "размер": "размер",
            "предел роя": "предел"}
    for lab, val in spec["stats"]:
        k_ = STAT[lab]
        a_ = fxg.rgba(k_)
        glyph(sc, k_, x0, y + 9 - a_.shape[0], 2)
        w, _ = fx_line(sc, 0, 0, val, draw=False)
        dots(sc, x0 + a_.shape[1] * 2 + 8, x1 - w - 6, y + 12)
        fx_line(sc, x1 - w, y, val)
        y += 22
    y += 12
    heading(sc, "ВОЗМОЖНОСТИ", x0, y, seed=4)
    y += 26
    cols = (x0 + 20, x0 + 112, x0 + 172, x0 + 252)
    for cx, lab in zip(cols, ("атака", "урон", None, "дальность")):
        if lab:
            glyph(sc, lab, cx, y - 6, 2)
    y += 12
    for key, nm, dmg, typ, reach, note in spec["attacks"]:
        sc.rgb[y, x0:x1] = sc.rgb[y, x0:x1] * 0.5 + hexc("#4a3e5c") * 0.5
        icon(sc, key, x0, y + 5, 1)
        for cx, val, col in zip(cols, (nm, dmg, typ, reach), (GOLD, INK, INK, INK)):
            fx_line(sc, cx, y + 6, val) if "{" in val else UI.rich(sc, val, cx, y + 6, "text", 16, col=col)
        y += 28
        if note:
            fx_line(sc, x0 + 20, y + 2, note, dim=True)
            y += 26
        y += 4
    # under the attacks: the leader's comb of mutations; what woke shows its icon, what didn't is sealed
    if spec.get("comb"):
        rows, key, hover = spec["comb"]
        y += 10
        heading(sc, "МУТАЦИИ", x0, y, seed=6)
        pos, yb = leader_comb(sc, x0, y + 60, rows, key, hover)
    if spec.get("comb") and hover and pos[hover][4] == "sealedhover":     # sealed: it lights, nothing opens
        cursor(sc, int(pos[hover][0]) + 4, int(pos[hover][1]) + 2)
    elif spec.get("comb") and hover:
        cx, cy, nm, desc, _ = pos[hover]
        draw_pict, line = PICT[nm]
        ty0 = int(yb + 4)
        h_ = fx_rows(sc, x0 + 12, 0, x1 - x0 - 24, line, draw=False)
        UI.cell(sc, x0, ty0, x1, ty0 + 90 + h_, "normal")
        letters(sc, nm, x0 + 12, ty0 + 8, "text", 16, col=GOLD)
        draw_pict(sc, x0 + 12, ty0 + 36, x1 - 12)
        fx_rows(sc, x0 + 12, ty0 + 82, x1 - x0 - 24, line)
        cursor(sc, int(cx) + 4, int(cy) + 2)
    # under the attacks: what it hands down — icons in a column
    if spec.get("below"):
        head, rows = spec["below"]
        y += 10
        heading(sc, head, x0, y, seed=6)
        y += 26
        for key, nm, note, col in rows:
            icon(sc, key, x0, y, 1)
            letters(sc, nm, x0 + 20, y + 1, "text", 16, col=col)
            if note:
                w_, _ = fx_line(sc, 0, 0, note, draw=False)
                fx_line(sc, x1 - w_, y + 1, note, dim=True)
            y += 18
    # right: what it can and what it can't — a column of names; the text shows when the mouse is over one
    x0, x1 = 632, WW - 18
    heading(sc, spec.get("right", "СПОСОБНОСТИ"), x0, 62, seed=5)
    y = 90
    hov = spec.get("hover", len(spec["abilities"]) - 1)        # None: the mouse is elsewhere
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
    if hov is not None:
        key, lab, nm, desc, col = spec["abilities"][hov]
        rows = ABIL_FX.get(nm, desc)
        tx0, ty0 = x0 + 10, hy + 46
        h_ = fx_rows(sc, tx0 + 12, 0, x1 - tx0 - 24, rows, draw=False)
        UI.cell(sc, tx0, ty0, x1, ty0 + 34 + h_, "normal")
        letters(sc, nm, tx0 + 12, ty0 + 8, "text", 16, col=col)
        fx_rows(sc, tx0 + 12, ty0 + 28, x1 - tx0 - 24, rows)
        cursor(sc, int(hx) - 30, int(hy) + 10)
    if not save:
        return sc
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)


def matka_spec(hover="Брачный полёт"):
    spec = dict(
        seed=57, title="МАТКА", sub=EPITHET["Матка"][0], epi=EPITHET["Матка"][1], cell="mut",
        sprite=leader("Матка", "idle", 1.45), dx=14, sw=56,
        facts=[("val", "развитие", "ещё не выбрано", MUTED),
               dev_choice("Матка")],
        stats=[("здоровье", "80"), ("броня", "2 {хитин}"), ("скорость", "1"), ("размер", "6")],
        attacks=[("matka", "Жвалы", "1–6 +2", "{руб}", "1", "")],
        hover=None,
        comb=([("Гнездо", [("m_nest", "lived", "Малое гнездо", ""), ("m_nurse", "open", "Кормилица", ""),
                            ("m_vivi", "sealed", "Живородящая", ""), ("m_bud", "sealed", "Почкование", "")]),
               ("Порода", [("m_dominant", "sealed", "Доминантная линия", ""),
                           ("m_flight", "open", "Брачный полёт", "Пару ей в выводке выбираешь сам из всех выживших, а не из соседей по бою."),
                           ("m_hybrid", "sealed", "Гибрид", "")])],
              ("m_heir", "keysealed", "Наследница", ""), "Брачный полёт"),
        abilities=[("clutch", "каждые 3 хода", "Кладка", "Каждые 3 хода рядом с Маткой вылупляются 2 личинки. В бой они вступают со следующего хода. Личинки, которые доживут до конца боя, попадут в выводок с чертой, убившей в этом бою больше всего врагов.", GOLD),
                   ("larva", "постоянно", "Сердце роя", "Если особь роя погибает в 2 клетках от Матки, на её месте остаётся яйцо. Через 2 хода из него вылупляется личинка.", GOLD),
                   ("feed", "правило похода", "Плодовитость", "В выводке на одного потомка больше. Кормление лидера стоит в два раза дешевле.", (214, 196, 150)),
                   ("matka", "стаи роя", "Тесные стаи", "В одной клетке помещается до 6 мелких особей вместо 4. Удары по площади и растаптывание задевают их всех.", (214, 196, 150)),
                   ("fear", "слабость", "Медлительная", "Скорость 1. Если Матка погибнет, каждая особь роя проходит проверку страха 1–9.", RED)])
    spec["comb"] = spec["comb"][:2] + (hover,)
    return spec


def cards():
    big_card(dict(
        seed=53, title="СКОРПИОН", sub="рабочая · «Летучее жало» · в рое 7",
        sprite=bug(("stinger", "wings"), "idle", 4.2, 61, rare="blister", evo=("vise",)), dx=-6,
        facts=[("parents", [("stinger", "скорпион"), ("wings", "оса")]),
               ("val", "убито стаей в прошлом бою", "9", GREEN),
               ("val", "таких в рое", "7", INK)],
        stats=[("здоровье", "8"), ("броня", "0 {хитин}"), ("скорость", "2"), ("боевой дух", "6"),
               ("размер", "1"), ("предел роя", "1")],
        attacks=[("stinger", "Жало", "1–4 +1", "{кол}", "1", "{пробой} → {яд:1–4} {броня:−1}"),
                 ("evo_vise", "Клешни", "—", "{дроб}", "1", "{атака} → {прикован}")],
        below=("ПОТОМКАМ", [("stinger", "Жало", "{наследие}", GOLD), ("wings", "Крылья", "{наследие}", GOLD),
                            ("m_blister", "Нарывник", "{мутация}", SILVER)]),
        abilities=[("stinger", "форма", "Жало", "Если удар жалом пробивает броню, цель получает 1–4 {яд} и теряет 1 броню до конца боя. {яд} накапливается. С одной цели снимается не больше 2 брони. Машинам {яд} не страшен, но броню жало снимает и с них.", GOLD),
                   ("wings", "деталь", "Крылья", "Может проходить через клетки, занятые своими.", GOLD),
                   ("m_blister", "мутация · общая", "Нарывник", FX["blister"], SILVER),
                   ("evo_vise", "эволюция формы", "Клешни-тиски", "Клешни бьют {дроб}. Враг, в которого они попали, не может уйти со своей клетки.", (150, 220, 120)),
                   ("fear", "слабость", "Медленнее других", "Скорость 2, у других рабочих 3.", RED),
                   ("ant", "класс", "Стая", "Боевой дух +1 за каждую свою особь в соседних клетках, но не больше +4.", INK),
                   ("biomass", "класс", "Пожирание", "Убив врага, съедает труп и восстанавливает четверть здоровья. После боя съеденное идёт в биомассу.", INK),
                   ("carapace", "класс", "Хитин", "Урон {руб} по ней в два раза меньше, {дроб} в два раза больше.", INK)]),
        "swarm_card.png")
    big_card(matka_spec(), "swarm_card_leader.png")
    PSI, MEAT, KUK, RULE = VIOLET, (236, 120, 96), (150, 220, 90), (214, 196, 150)
    big_card(dict(
        seed=61, title="РАЗУМ УЛЬЯ", sub=EPITHET["Разум улья"][0], epi=EPITHET["Разум улья"][1], cell="find",
        sprite=leader("Разум улья", "idle", 2.6), dx=4, sw=46,
        facts=[("val", "развитие", "ещё не выбрано", MUTED),
               dev_choice("Разум улья")],
        stats=[("здоровье", "22"), ("броня", "0 {мягкое}"), ("скорость", "1"), ("размер", "4")],
        attacks=[("razum", "Пси-удар", "1–6", "{пси}", "3", "{мимо}")],
        hover=None,
        comb=([("Основа", [("m_psi_gland", "lived", "Пси-железа", "")]),
               ("Безумие", [("m_psi_reson", "open", "Резонатор", ""), ("m_psi_dread", "sealed", "Чутьё на страх", "")]),
               ("Ужас", [("m_psi_whisper", "sealed", "Жуткий шёпот", ""), ("m_strider", "sealed", "Стрекот", "")]),
               ("Крик", [("m_psi_echo", "sealed", "Эхо крика", ""), ("m_psi_last", "sealed", "Последняя воля", "")]),
               ("Кукловод", [("m_psi_leash", "sealed", "Пси-поводок", "")])],
              ("m_psi_relay", "keysealed", "Ретранслятор", ""), "Жуткий шёпот"),
        abilities=[("m_psi_reson", "каждые 3 хода", "Помутнение", "Враги в 2 клетках от самой плотной их группы на ход путают цели и бьют своих. У машин сбой: шаг пропущен, способности молчат.", PSI),
                   ("m_psi_echo", "постоянно", "Предсмертный крик", "Когда особь роя погибает, её убийца получает 1 {пси} мимо брони. Машина — 1 {пси} за каждые две смерти.", PSI),
                   ("m_psi_leash", "раз в 6 ходов", "Захват разума", "Враг ниже половины здоровья переходит к рою: размер 1–3 на 5 ходов, 4–5 на 2 хода. Размер 6–7 только оглушает на ход.", PSI),
                   ("m_psi_gland", "правило похода", "Мыслящая порода", "В выводке выпадают мутации на {пси} и страх, чаще у потомков тех, кто стоял рядом с Разумом.", RULE),
                   ("razum", "стаи роя", "Одна мысль на стаю", "Вся стая бьёт ту цель, на которую напала первая её особь.", RULE),
                   ("fear", "слабость", "Хрупкий мозг", "Мягкое тело. Если Разум погибнет, каждая особь роя проходит проверку страха 1–9.", RED)]),
        "swarm_card_razum.png")
    big_card(dict(
        seed=65, title="ПОЖИРАТЕЛЬ", sub=EPITHET["Пожиратель"][0], epi=EPITHET["Пожиратель"][1], cell="eat",
        sprite=leader("Пожиратель", "idle", 2.1), dx=8, sw=56,
        facts=[("val", "развитие", "ещё не выбрано", MUTED),
               dev_choice("Пожиратель")],
        stats=[("здоровье", "41"), ("броня", "2 {тяжхитин}"), ("скорость", "2"), ("размер", "5–7")],
        attacks=[("pozh", "Пасть", "1–8 +2", "{руб}", "1", "")],
        hover=None,
        comb=([("Корм", [("m_sated", "lived", "Сытная", ""), ("m_bait", "sealed", "Приманка", ""),
                         ("m_fattened", "sealed", "Откормленная", "")]),
               ("Пир", [("m_frenzy", "open", "Кормовое безумие", ""), ("m_table", "sealed", "За столом", "")]),
               ("Голод", [("m_hungry", "sealed", "Голодная", ""), ("m_devblood", "sealed", "Кровь Пожирателя", "")])],
              ("m_essence", "keysealed", "Питательная суть", ""), None),
        abilities=[("pozh", "каждые 2 тела", "Рост", "За каждые 2 съеденных тела, своих или чужих: здоровье ×1,4 и +2 к удару. До двух раз за бой, до размера 7.", MEAT),
                   ("m_table", "постоянно", "Каннибал", "Ест погибших своих рядом так же, как чужих: лечится и растёт.", MEAT),
                   ("biomass", "правило похода", "Всё в пасть", "Каждое съеденное им в бою тело — +1 биомасса после боя. Её можно отдать на его рост. Рой меньше.", RULE),
                   ("m_frenzy", "стаи роя", "Свора", "Стаи бросаются туда же, куда он, и оставляют ему тела убитых. Сами особи пожиранием не лечатся.", RULE),
                   ("m_hungry", "слабость", "Ненасытный", "Три хода без еды: хватает самую мелкую свою особь рядом и съедает. Если рядом никого, теряет десятую часть здоровья за ход.", RED)]),
        "swarm_card_pozh.png")
    big_card(dict(
        seed=69, title="ЧУМА", sub=EPITHET["Чума"][0], epi=EPITHET["Чума"][1], cell="new",
        sprite=leader("Чума", "idle", 2.4), dx=6, sw=44,
        facts=[("val", "развитие", "ещё не выбрано", MUTED),
               dev_choice("Чума")],
        stats=[("здоровье", "12"), ("броня", "1 {хитин}"), ("скорость", "2"), ("размер", "3")],
        attacks=[("kuk", "Яйцеклад", "1–6", "{кол}", "2", "{инициатива:+3} · {пробой} → {заражение}")],
        hover=None,
        comb=([("Заражение", [("m_parasitoid", "lived", "Паразитоид", ""), ("m_bloodeggs", "sealed", "Яйца в крови", ""),
                              ("m_spores", "open", "Споры", "")]),
               ("Хозяин", [("m_call", "sealed", "Зов кладки", ""), ("m_bodyguard", "sealed", "Телохранитель", ""),
                           ("m_gnaw", "sealed", "Прожорливая кладка", "")]),
               ("Мутации", [("m_mutagen", "sealed", "Мутагенная кладка", ""), ("m_unstable", "open", "Нестабильная", "")])],
              ("m_royal", "keysealed", "Королевская кладка", ""), None),
        abilities=[("m_parasitoid", "атака", "Заражение", "Пробил броню — цель заражена. Живой, погибнув, выпускает 2 личинки. В машине кладка зреет в топке: каждые 3 хода личинка, сломанная выпускает ещё 2.", KUK),
                   ("kuk", "постоянно", "Длинный яйцеклад", "Колет на 2 клетки, инициатива +3: бьёт раньше всех.", KUK),
                   ("ant", "в начале боя", "Подкидыш", "Одна рабочая начинает бой в тылу врага.", KUK),
                   ("hand", "постоянно", "Дети хозяина", "Личинка из заражённого берёт черту хозяина: у человека руку, у голема железный панцирь, у нежити чужие кости. Дожившие до конца боя уходят в выводок химерами.", KUK),
                   ("m_mutagen", "правило похода", "Чужие черты", "Чужие черты выпадают чаще и сильнее, у особи их может быть две.", RULE),
                   ("m_call", "стаи роя", "Пёстрые стаи", "В одну стаю можно ставить разные виды. Пары в выводке складываются и внутри стаи.", RULE),
                   ("fear", "слабость", "Хрупкая кладка", "{огонь} выжигает кладку: заражённый, получив {огонь}, даже свой, очищается.", RED)]),
        "swarm_card_kuk.png")


# ---------------------------------------------------------------- a mutation's own card: clicked on any card, opens over it
MUT_CARD = {   # key: (name, whose · branch, state, carriers, the line, body traits for the carrier)
    "nest": ("Малое гнездо", "мутация Матки · Гнездо", "в рое", 3, None, ("carapace",)),
}


def mutation_card(key="nest"):
    """A mutation opened from a card: over the dimmed card, a plate with the mutation large — who carries it, the
    moment it works in battle as a picture, one line of what it does, what it hands down."""
    import swarm_mut as M
    name, whose, state, n, line, tr = MUT_CARD[key]
    rows = FX[key]
    sc = big_card(matka_spec(hover=None), None, save=False)
    sc.rgb *= 0.38                                              # the card underneath, dimmed
    x0, y0, x1, y1 = 176, 64, 784, 476
    UI.plate(sc, x0, y0, x1, y1, antennae=True)
    neon(sc, UI.chamfer_mask(sc, x0, y0, x1, y1, 9), (232, 192, 80), 4, 0.35)
    # the header: the icon large, the name, whose it is, how many carry it now
    sc.glow(x0 + 46, y0 + 44, 34, hexc("#f0c050"), 0.35)
    icon(sc, "m_" + key, x0 + 22, y0 + 20, 3)
    letters(sc, name.upper(), x0 + 86, y0 + 18, "title", 24, col=(236, 216, 170), col2=(150, 96, 60), jitter=1,
            drips=4, hairs=6, seed=11)
    letters(sc, whose, x0 + 88, y0 + 50, "text", 16, col=(240, 200, 90))
    chip = f"{state}: {n}"
    w = UI.text_width(chip)
    UI.cell(sc, x1 - w - 46, y0 + 20, x1 - 16, y0 + 50, "new")
    letters(sc, chip, x1 - 31, y0 + 27, "text", 16, col=GREEN, align="right")
    # the carrier, large, in a comb cell
    UI.cell(sc, x0 + 18, y0 + 84, x0 + 196, y0 + 300, "new")
    M.Z, M.F = 2.7, 2.5
    put(sc, M.bug(tr, "idle", key=key, seed=5, k=4.2), x0 + 108, y0 + 262, 36)
    # the moment it works, as a picture
    UI.cell(sc, x0 + 206, y0 + 84, x1 - 18, y0 + 300, "normal")
    gx0, gx1 = x0 + 214, x1 - 26
    floor = (sc.yy > y0 + 250) & (sc.yy < y0 + 292) & (sc.xx > gx0) & (sc.xx < gx1)
    sc.rgb[floor] = sc.rgb[floor] * 0.75 + hexc("#2a2018") * 0.25
    M.scene(sc, key, (gx0 + gx1) / 2 - 10, y0 + 266)
    # its effects, as standard lines, and what it hands down
    spots = []
    for j, ln in enumerate(rows):
        spots += fx_line(sc, x0 + 22, y0 + 314 + j * 26, ln)[1]
    fx_line(sc, x0 + 22, y0 + 318 + len(rows) * 26, "{выводок} → потомкам", dim=True)
    # the mouse over a glyph: what it means
    egg = next(sp for sp in spots if sp[0] == "яйцо")
    sc.glow(egg[1] + egg[3] / 2, egg[2] + egg[4] / 2, 10, hexc("#ffd070"), 0.5)
    gloss_tip(sc, "яйцо", int(egg[1] + egg[3] + 26), y0 + 296, 252)
    cursor(sc, int(egg[1] + egg[3] / 2), int(egg[2] + egg[4] / 2))

    UI.button(sc, x1 - 220, y1 - 54, x1 - 20, y1 - 16, "chitin")
    letters(sc, "Закрыть", x1 - 120, y1 - 44, "title", 16, col=INK, align="center")
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_mutation_card.png"))
    print("swarm_mutation_card.png", img.size)


# ---------------------------------------------------------------- a button under the mouse: the swarm takes a bite
def button_gif():
    """The hover on a clickable button, the swarm's way: holes eat into it — bites out of the edges, then through
    the gem — as if something unseen were feeding on it; the mouse leaves and it is whole again."""
    from PIL import Image
    Wd, Hd = 480, 120
    bg = UI.nest(Wd, Hd, 12)
    x0, y0, x1, y1 = 110, 40, 370, 86
    cy = (y0 + y1) / 2

    def hole(sc, parts):
        """A bite-shaped hole: a few overlapping circles; the background shows through, the cut edge lit."""
        m = np.zeros(sc.yy.shape, bool)
        for (bx, by, r) in parts:
            m |= np.hypot(sc.xx - bx, sc.yy - by) <= r + 1
        inside = (sc.xx >= x0 - 2) & (sc.xx <= x1 + 2) & (sc.yy >= y0 - 2) & (sc.yy <= y1 + 2)
        m &= inside
        sc.rgb[m] = bg.rgb[m] * 0.8
        ring = dilate(m, 1) & ~m & inside
        sc.rgb[ring] = UI.OUTL
        lit = dilate(m, 2) & ~dilate(m, 1) & inside
        sc.rgb[lit] = np.minimum(255, sc.rgb[lit] * 1.3 + 25)

    H = [  # each hole: its circles, one more per step as the bite widens
        [(x0 + 22, y0 - 1, 4), (x0 + 28, y0 + 1, 4), (x0 + 34, y0 - 1, 3)],
        [(x1 - 30, y1 + 1, 4), (x1 - 24, y1 - 1, 5), (x1 - 17, y1 + 1, 3)],
        [(x0 + 8, cy + 2, 4), (x0 + 12, cy - 4, 3), (x0 + 16, cy + 6, 3)],
        [(x1 - 46, y0 + 9, 3), (x1 - 41, y0 + 12, 3), (x1 - 44, y0 + 16, 2)],
        [(x0 + 48, y1 - 7, 3), (x0 + 52, y1 - 3, 3)],
        [(x1 - 9, cy - 5, 4), (x1 - 12, cy + 2, 3)],
    ]
    steps = [(1, 1), (2, 2), (3, 2), (4, 3), (6, 3)]           # (holes open, circles in each)
    seq = [(False, 0, 0, 0.0, 420)] + [(True, nh, nc, 0.15 + 0.06 * i, 60) for i, (nh, nc) in enumerate(steps)] + \
          [(True, 6, 3, 0.4, 700), (False, 0, 0, 0.0, 300)]
    frames, durs = [], []
    for mouse, nh, nc, gl, dur in seq:
        sc = Scene(Wd, Hd)
        sc.rgb[:] = bg.rgb
        UI.WOBBLE[0] = 0.0
        if gl:
            sc.glow((x0 + x1) / 2, cy, 150, hexc("#9ae030"), gl)
        UI.button(sc, x0, y0, x1, y1, "acid")
        letters(sc, "В ПОХОД", (x0 + x1) / 2, y0 + 15, "title", 16, col=ACID2, col2=(110, 170, 40), align="center", jitter=1)
        for parts in H[:nh]:
            hole(sc, parts[:nc])
        if mouse:
            cursor(sc, int((x0 + x1) / 2) + 40, int(cy) + 4)
        frames.append(sc.image(S).convert("P", palette=Image.ADAPTIVE, colors=255))
        durs.append(dur)
    frames[0].save(out("swarm_button_hover.gif"), save_all=True, append_images=frames[1:], duration=durs, loop=0,
                   disposal=2)
    strip = Image.new("RGB", (Wd * S, Hd * S * 3))
    for i, fi in enumerate((0, 3, 6)):
        strip.paste(frames[fi].convert("RGB"), (0, i * Hd * S))
    strip.save(out("swarm_button_hover.png"))
    print("swarm_button_hover.gif", frames[0].size, len(frames))


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
    title(sc, "ЛИДЕРЫ НА ПОЛЕ", seed=43)
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
    caption(3, "Пожиратель голоден", "три хода без еды — красные камни; хватает свою, самую мелкую")

    # 5 — Чума: the eggs ripen in a machine's warm firebox; a grub crawls out every 3 turns
    px, py = P(4)
    k_spr = SL.build("Чума", "attack", 1.0)
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
    caption(4, "Чума", "в машине зреет кладка: камни до следующей личинки")

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


# ---------------------------------------------------------------- the glossary: every glyph, behind «?» on any screen
def uses(key, limit=4, width=280):
    """Where a term is met: lines of abilities, mutations and evolutions that have it — (whose, line)."""
    import swarm_mut as SM
    import swarm_evo as EV
    names = {k: nm for v in SM.POOLS.values() for k, nm, *_ in v[3]}
    evo = {k: nm for rows in EV.EVO.values() for k, nm, *_ in rows}
    src = ([(nm, rows) for nm, rows in ABIL_FX.items()] + [(names.get(k, k), rows) for k, rows in SM.FX.items()]
           + [(evo.get(k, k), rows) for k, rows in EV.EVO_FX.items()])
    out_, seen = [], set()
    for who, rows in src:
        for ln in rows:
            if ("{" + key + "}" in ln or "{" + key + ":" in ln) and who not in seen:
                w_, _ = fx_line(None, 0, 0, ln, draw=False)
                if w_ <= width:
                    out_.append((who, ln))
                    seen.add(who)
                    break
        if len(out_) >= limit:
            break
    return out_


def glossary_screen(chapter="Когда", term="гибель_своя"):
    """«?»: the glyphs by chapter — when, time, what it does, states, fate, brood, enemies, damage; the chosen one
    large with its meaning and the lines it is met in."""
    import fxg
    sc = frame_screen(91)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=6, seed=21)
    title(sc, "ЗНАЧКИ", seed=41)
    help_button(sc, on=True)
    # chapters
    UI.plate(sc, 12, 52, 196, 446, antennae=True)
    for i, (ch, keys) in enumerate(fxg.GROUPS):
        y0 = 60 + i * 47
        on = ch == chapter
        UI.cell(sc, 20, y0, 188, y0 + 41, "hi" if on else "normal")
        a_ = fxg.rgba(keys[0])
        fxg.draw(sc, keys[0], 30 + (22 - a_.shape[1] * 2) // 2, y0 + 20 - a_.shape[0], 2)
        letters(sc, ch, 62, y0 + 8, "text", 16, col=GOLD if on else INK, jitter=1, seed=i)
        letters(sc, str(len(keys)), 62, y0 + 26, "title", 8, col=PALE, outline=False)
    # the chapter's glyphs, two columns
    keys = dict(fxg.GROUPS)[chapter]
    UI.plate(sc, 206, 52, 630, 446, antennae=True)
    heading(sc, chapter.upper(), 220, 62, seed=7)
    half = (len(keys) + 1) // 2
    for j, k_ in enumerate(keys):
        x0, y0 = 216 + (j // half) * 206, 90 + (j % half) * 34
        if k_ == term:
            UI.cell(sc, x0 - 4, y0 - 4, x0 + 202, y0 + 30, "hi")
        a_ = fxg.rgba(k_)
        glyph(sc, k_, x0 + (26 - a_.shape[1] * 2) // 2, y0 + 13 - a_.shape[0], 2)
        letters(sc, fxg.TERMS[k_][0], x0 + 34, y0 + 5, "text", 16, col=GOLD if k_ == term else INK)
    # the chosen one
    nm, what, _ = fxg.TERMS[term]
    UI.plate(sc, 640, 52, 948, 446, antennae=True)
    a_ = fxg.rgba(term)
    fxg.draw(sc, term, 654, 66, 4)
    heading(sc, nm.upper(), 664 + a_.shape[1] * 4, 66 + a_.shape[0] * 2 - 10, seed=8)
    y = 76 + a_.shape[0] * 4
    for ln in wrap(what, 276):
        UI.rich(sc, ln, 654, y, "text", 16, col=INK)
        y += 18
    y += 14
    letters(sc, "ВСТРЕЧАЕТСЯ", 654, y, "title", 8, col=PALE, outline=False)
    y += 16
    for who, ln in uses(term, 4, 276):
        letters(sc, who, 654, y, "text", 16, col=GOLD, jitter=1, seed=len(who))
        fx_line(sc, 654, y + 22, ln)
        y += 56
    # leave; Alt
    UI.button(sc, 12, 470, 300, 520, "chitin")
    letters(sc, "Закрыть", 156, 486, "title", 16, col=INK, align="center")
    kw = keycap(sc, 400, 484, "Alt")
    letters(sc, "— подписи под значками", 408 + kw, 485, "text", 16, col=MUTED)
    UI.creature(sc, bug(("wings",), "idle", 0.9, 93), 900, 52)
    UI.cobweb(sc, 2, 448, 28, quad=(1, 1))
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_glossary_screen.png"))
    print("swarm_glossary_screen.png", img.size)


def roles():
    """The rule of the swarm's interface, on one sheet: what a button's colour says, what a cell's rim says."""
    WW_, HH_ = 960, 300
    UI.WOBBLE[0] = 1.3
    HOVER.clear()
    sc = UI.nest(WW_, HH_, 95)
    UI.wing(sc, 0, 0, WW_, 44)
    UI.drips(sc, 60, 900, 44, "#b06818", n=5, seed=23)
    title(sc, "КНОПКИ И ЯЧЕЙКИ", seed=43)
    UI.plate(sc, 12, 52, 948, 292, antennae=False)
    heading(sc, "КНОПКИ", 26, 62, seed=2)
    btns = [("acid", "В БОЙ", "действие роя"), ("chitin", "Назад", "переход"), ("blood", "Съесть", "уничтожить"),
            ("amber", "×2", "включено"), ("dim", "В бой", "недоступно")]
    for i, (kind, t, what) in enumerate(btns):
        x0 = 26 + i * 184
        if kind == "acid":
            act_button(sc, x0, 88, x0 + 172, 130, t)
        else:
            UI.button(sc, x0, 88, x0 + 172, 130, kind)
            letters(sc, t, x0 + 86, 101, "text", 16, col=DARK if kind == "amber" else (PALE if kind == "dim" else INK),
                    outline=kind != "amber", align="center")
        letters(sc, what, x0 + 86, 138, "text", 16, col=MUTED, align="center")
    heading(sc, "ЯЧЕЙКИ", 26, 170, seed=3)
    cells = [("normal", "обычная"), ("hi", "выбрана"), ("hover", "под мышью"), ("new", "новые"), ("eat", "к съедению"),
             ("mut", "мутация"), ("find", "находка")]
    for i, (st, what) in enumerate(cells):
        x0 = 26 + i * 131
        UI.cell(sc, x0, 196, x0 + 121, 250, st)
        letters(sc, what, x0 + 60, 256, "text", 16, col=MUTED, align="center")
    cursor(sc, 26 + 2 * 131 + 70, 222)
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_ui_roles.png"))
    print("swarm_ui_roles.png", img.size)


def hints():
    """The mouse over a glyph, over a trait's icon; the Alt view."""
    brood("tip")
    aftermath("tip")
    evolution("alt")


SCREENS = {"brood": brood, "camp": camp, "evolution": evolution, "deploy": deploy, "finds": finds, "pools": pools,
           "flocks": flocks, "battle": battle_hud, "aftermath": aftermath, "leader": leaders_pick, "development": development,
           "card": cards, "field": leaders_field, "mutation": mutation_card, "hover": button_gif,
           "glossary": glossary_screen, "hints": hints, "roles": roles}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in SCREENS.items():
        if arg in ("all", k):
            fn()
