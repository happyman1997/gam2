"""The Foundry's other three leaders in full — each card in its own materials, so a leader is known by its card
before a word is read. The same things are on all of them (the leader large, its passport, its weapons, who
comes with it, its abilities with when they fire, its rule for the run, how it grows), but:

  Изобретатель — a laboratory: the leader under a glass bell jar with arcs crawling inside it, its passport on
                 blueprint paper with its small golems drawn in blue lines, its augments on patent slips sealed
                 with red wax, tesla coils by the title;
  Маньяк       — a lair on a scrapheap: patchwork plates daubed purple and green, the leader behind the crooked
                 bars of its cage, hazard tape, its abilities on notes nailed up askew, its mad modules in a
                 heap, the title shaking between two circular saws;
  Зодчий       — a building site: a wall of dressed stone, the leader on scaffolding in a stone arch, its passport
                 cut into a stone tablet, its abilities on blocks of the wall (the weakness cracked), its building
                 modules on a drawing, trowels by the title.

    python3 tools/sprites/leader_cards.py [inventor|maniac|zodchiy]   -> out/foundry_card_<leader>.png
"""
import sys
import numpy as np
from kit import hexc
import foundry_ui as FU
import foundry_hud as FH
from foundry_hud import (screen, title_center, toolbar, heading, action, letters, mod_icon, leader_sprite, H, SU,
                         INK, MUTED, PALE, GOLD, RED, BRASS, WW, HH, S, out)
import frames as F

PAPER = ((236, 226, 200), (200, 186, 152), (150, 132, 100))      # light, mid, edge
INK_DARK = (44, 32, 22)
BLUE_INK = (170, 220, 250)


def army_sprite(frame, f=0.62):
    key = ("army", frame, round(f, 3))
    if key not in FH._LEADERS:
        if frame == "Каменщик":
            import golems_h as GH
            FH._LEADERS[key] = GH.build(GH.MASON, "idle", 0.9)
        else:
            FH._LEADERS[key] = F.build(frame, "idle", k=F.FRAMES[frame][0] * f)
    return FH._LEADERS[key]


def jag(sc, pts, core="#e8fffd", glow="#2ab0c8"):
    """A jagged arc of lightning through the points, a cold glow beside its white core."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for t in np.linspace(0, 1, n):
            x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
            if 0 < x < sc.w - 1 and 0 < y < sc.h - 1:
                sc.rgb[y, x + 1] = hexc(glow)
                sc.rgb[y + 1, x] = hexc(glow)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for t in np.linspace(0, 1, n):
            x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
            if 0 <= x < sc.w and 0 <= y < sc.h:
                sc.rgb[y, x] = hexc(core)


def stat_rows(sc, x0, x1, y, rows, lab_col=MUTED, dot_col=None, step=21):
    """The body's numbers: a glyph, its word, dots, the value at the right."""
    for g, lab, val in rows:
        a_ = H.glyph(sc, g, x0, y - 4, 2)
        letters(sc, lab, x0 + a_ + 8, y - 2, "text", 16, col=lab_col)
        w, _ = H.fx_line(sc, 0, 0, val, draw=False)
        lw = SU.text_width(lab, "text", 16)
        for x in range(x0 + a_ + 14 + lw, x1 - w - 6, 4):
            sc.rgb[y + 10, x] = hexc(dot_col) if dot_col else sc.rgb[y + 10, x] * 0.4 + np.array(lab_col) * 0.6
        H.fx_line(sc, x1 - w, y - 2, val)
        y += step
    return y


def bottom(sc):
    FU.sill(sc, 468)
    action(sc, 12, 478, 220, 526, "Назад", "steel")
    action(sc, 640, 472, 948, 532, "ВЫБРАТЬ", "hot", big=True)


# ---------------------------------------------------------------- Изобретатель: the laboratory
def tesla(sc, x, base):
    """A small tesla coil standing on the beam: a base plate, the copper winding in bands, a brass ball on top."""
    sc.rgb[base - 3:base, x - 8:x + 9] = hexc("#3a3842")
    sc.rgb[base - 3, x - 8:x + 9] = hexc("#6a6870")
    for y in range(base - 24, base - 3):
        sc.rgb[y, x - 4:x + 5] = hexc("#e09a50") if y % 2 else hexc("#8a4018")
        sc.rgb[y, x - 4] = hexc("#5a240e")
    d = np.hypot(sc.xx - x, sc.yy - (base - 29))
    sc.rgb[d <= 5.5] = SU.OUTL
    sc.rgb[d <= 4.5] = hexc("#a0782c")
    sc.rgb[(d <= 3) & (sc.xx < x) & (sc.yy < base - 29)] = hexc("#f4dc96")
    o, _, _ = SU.edges((np.abs(sc.xx - x) <= 4) & (sc.yy >= base - 24) & (sc.yy < base - 3))
    sc.rgb[o] = SU.OUTL


def bell_jar(sc, x0, y0, x1, y1):
    """A glass bell jar: the dome and the straight sides, glass tinting what's inside cold, a hard bright streak
    down its left, its rim catching the light, a brass knob on top."""
    cx = (x0 + x1) / 2
    rx = (x1 - x0) / 2
    top = y0 + 60
    X, Y = sc.xx, sc.yy
    m = (((X - cx) / rx) ** 2 + ((Y - top) / 60.0) ** 2 <= 1) & (Y <= top) | ((np.abs(X - cx) <= rx) & (Y > top) & (Y < y1))
    sc.rgb[m] = sc.rgb[m] * 0.82 + hexc("#1a4a58") * 0.18
    o, _, _ = SU.edges(m)
    sc.rgb[o] = sc.rgb[o] * 0.3 + hexc("#9ad8f0") * 0.7
    streak = m & (np.abs(X - (x0 + 22) + (Y - top) * 0.0) <= 1.5) & (Y > top - 30) & (Y < y1 - 40)
    sc.rgb[streak] = sc.rgb[streak] * 0.45 + hexc("#e8fffd") * 0.55
    streak2 = m & (np.abs(X - (x0 + 30)) <= 0.5) & (Y > top) & (Y < y1 - 90)
    sc.rgb[streak2] = sc.rgb[streak2] * 0.6 + hexc("#e8fffd") * 0.4
    d = np.hypot(X - cx, Y - (y0 - 4))
    sc.rgb[d <= 6] = SU.OUTL
    sc.rgb[d <= 5] = hexc("#a0782c")
    sc.rgb[(d <= 3) & (X < cx) & (Y < y0 - 4)] = hexc("#f4dc96")


def patent_slip(sc, x0, y0, x1, y1, key, name, line, seed=0):
    """A patent slip: cream paper with a ruled edge, the augment's icon, its name in ink, its line, a red wax
    seal pressed at the right."""
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    sc.rgb[m] = (np.array(PAPER[0]) * (1 - t * 0.25))[m]
    sh = np.roll(np.roll(m, 3, 0), 2, 1) & ~m
    sc.rgb[sh] *= 0.45
    sc.rgb[y0 + 3, x0 + 3:x1 - 3] = PAPER[2]
    sc.rgb[y1 - 4, x0 + 3:x1 - 3] = PAPER[2]
    o, _, _ = SU.edges(m)
    sc.rgb[o] = PAPER[2]
    FU.cell(sc, x0 + 6, y0 + 8, x0 + 44, y0 + 46, "locked")
    mod_icon(sc, key, x0 + 9, y0 + 11, 2)
    letters(sc, name, x0 + 52, y0 + 8, "text", 16, col=INK_DARK, outline=False, shadow=False)
    H.fx_line(sc, x0 + 52, y0 + 28, line)
    cx, cy = x1 - 18, y0 + 18
    d = np.hypot(sc.xx - cx, sc.yy - cy)
    wax = d <= 9 + (np.sin(np.arctan2(sc.yy - cy, sc.xx - cx) * 7 + seed) * 1.2)
    sc.rgb[wax] = hexc("#9a1c1c")
    sc.rgb[wax & (d <= 6)] = hexc("#c0402e")
    sc.rgb[wax & (d <= 6) & (d >= 4.8)] = hexc("#6a0e0e")
    sc.rgb[(d <= 2) & wax] = hexc("#f08060")


def arc_pts(x0, y0, x1, y1, n, rnd, amp=6):
    """A jagged path from one point to another: n kinks thrown off the straight line at random."""
    pts = [(x0, y0)]
    for k in range(1, n):
        t = k / n
        pts.append((int(x0 + (x1 - x0) * t + rnd.uniform(-amp, amp) * 0.4), int(y0 + (y1 - y0) * t + rnd.uniform(-amp, amp))))
    return pts + [(x1, y1)]


def inventor(ret=False, frame=None):
    sc = screen(71)
    rnd = np.random.RandomState(5 if frame is None else 100 + frame)
    sc.rgb[:] = sc.rgb * 0.8 + hexc("#10202a") * 0.2
    FU.wing(sc, 0, 0, WW, 44)
    tw = SU.text_width("ИЗОБРЕТАТЕЛЬ", "title", 24)
    x = WW // 2 - tw // 2
    letters(sc, "ИЗОБРЕТАТЕЛЬ", x, 6, "title", 24, col=(232, 222, 206), col2=(120, 96, 70))
    for side, bx in ((-1, x - 30), (1, x + tw + 30)):                         # tesla coils, arcing to each other
        tesla(sc, bx, 42)
        tesla(sc, bx + side * 54, 42)
        if frame is None:
            jag(sc, [(bx, 12), (bx + side * 14, 7), (bx + side * 26, 14), (bx + side * 40, 8), (bx + side * 54, 12)])
        elif frame % 6 != 5:                                                  # the arc flickers, now and then out
            jag(sc, arc_pts(bx, 12, bx + side * 54, 12, 5, rnd, 6))
    toolbar(sc)
    # the bell jar, the leader inside it, arcs crawling between the electrodes
    FU.plate(sc, 12, 52, 330, 462, seed=72)
    sc.rgb[60:394, 20:322] = sc.rgb[60:394, 20:322] * 0.55
    for ex in (60, 282):                                                      # electrodes up from the base
        sc.rgb[300:394, ex - 2:ex + 3] = hexc("#5e5c66")
        sc.rgb[300:394, ex - 2] = hexc("#8e8c96")
        d = np.hypot(sc.xx - ex, sc.yy - 296)
        sc.rgb[d <= 6] = SU.OUTL
        sc.rgb[d <= 5] = hexc("#a0782c")
    spr = leader_sprite("inventor", 5.2)
    sc.blit(spr, int(171 - spr.ox), int(392 - spr.oy))
    if frame is None:
        jag(sc, [(64, 292), (84, 270), (96, 284), (118, 262)])
        jag(sc, [(278, 292), (262, 276), (250, 290), (226, 270)])
    else:                                                                     # the arcs crawl toward the leader
        reach = 30 + (frame % 12) * 4
        jag(sc, arc_pts(64, 292, 64 + reach, 292 - reach * 0.6, 4, rnd, 8))
        jag(sc, arc_pts(278, 292, 278 - reach, 292 - reach * 0.6, 4, rnd, 8))
        if frame % 12 >= 9:                                                   # and meet in a flash over him
            sc.glow(171, 250, 40, hexc("#9ad8f0"), 0.35)
    bell_jar(sc, 28, 74, 314, 394)
    base = (sc.xx >= 20) & (sc.xx < 322) & (sc.yy >= 394) & (sc.yy < 412)
    FU._bands(sc, base, FU.BRASSR, 0.75 - (sc.yy - 394) / 30.0)
    o, _, _ = SU.edges(base)
    sc.rgb[o] = SU.OUTL
    for dx in (40, 302):                                                      # two dials on the base
        d = np.hypot(sc.xx - dx, sc.yy - 403)
        sc.rgb[d <= 6] = SU.OUTL
        sc.rgb[d <= 5] = hexc("#ece2c8")
        sc.rgb[(np.abs(sc.xx - dx - (sc.yy - 403) * -0.6) < 0.7) & (d <= 4) & (sc.yy <= 403)] = hexc("#9a1c1c")
    FU.cell(sc, 24, 418, 318, 456, "hi")
    letters(sc, "ИЗОБРЕТАТЕЛЬ", 171, 422, "text", 16, col=(255, 210, 140), align="center")
    letters(sc, "мастер аугментов", 171, 438, "text", 16, col=BRASS, align="center")
    # the passport, on blueprint paper
    FU.plate(sc, 338, 52, 626, 462, seed=73)
    FH.blueprint_sheet(sc, 344, 58, 620, 456)
    letters(sc, "ПАСПОРТ", 358, 70, "title", 16, col=BLUE_INK, col2=(40, 80, 120))
    H.fx_line(sc, 358, 96, "{лидер} лидерство 10")
    y = stat_rows(sc, 358, 604, 128, (("здоровье", "здоровье", "20"), ("броня", "броня", "1"),
                                      ("скорость", "скорость", "2"), ("размер", "размер", "3"),
                                      ("инициатива", "инициатива", "7")), lab_col=BLUE_INK, dot_col="#3a6a94")
    letters(sc, "Шокер", 358, y + 4, "text", 16, col=(255, 255, 255))
    H.fx_line(sc, 420, y + 4, "1–6 {молния} · оглушает машины")
    y += 34
    letters(sc, "С НИМ — МАЛЫЕ ФРЕЙМЫ", 358, y, "text", 16, col=BLUE_INK)
    y += 22
    for j, (fr, aug, mod) in enumerate((("Мудрец", "a_coil", "overload"), ("Орудие", "a_coil", "mortar"),
                                        ("Механик", "a_mirror", "repair"))):
        gx = 380 + j * 82
        g = FH.drawn(army_sprite(fr, 0.5))
        sc.blit(g, int(gx - g.ox), int(y + 56 - g.oy))
        mod_icon(sc, aug, gx + 14, y + 6, 1)
        mod_icon(sc, mod, gx + 14, y + 26, 1)
    y += 70
    sc.rgb[y, 352:612] = hexc("#3a6a94")
    letters(sc, "ПРАВИЛО ПОХОДА", 358, y + 8, "text", 16, col=GOLD)
    letters(sc, "фреймы на размер меньше:", 358, y + 26, "text", 16, col=BLUE_INK, outline=False)
    letters(sc, "големов больше, у каждого", 358, y + 44, "text", 16, col=BLUE_INK, outline=False)
    letters(sc, "ячейка аугмента", 358, y + 62, "text", 16, col=BLUE_INK, outline=False)
    # augments on patent slips; then the abilities
    FU.plate(sc, 634, 52, 948, 462, seed=74)
    heading(sc, "АУГМЕНТЫ", 648, 62)
    for j, (key, nm, line) in enumerate((("a_coil", "Грозовая катушка", "{каждые:2} → {молния} {радиус:1}"),
                                         ("a_mirror", "Отражатель", "первый {атака} → назад"),
                                         ("a_spring", "Пружинный рывок", "{начало} → прыжок к врагу"))):
        patent_slip(sc, 644, 86 + j * 58, 938, 138 + j * 58, key, nm, line, seed=j)
    heading(sc, "СПОСОБНОСТИ", 648, 260)
    for j, (nm, when, line, col) in enumerate((("Полевая настройка", "начало боя", "{свой} {радиус:1} → аугмент", INK),
                                              ("Перегрузка", "каждые 3", "{свой} {радиус:1} → аугмент ×2", INK),
                                              ("Резонанс", "всегда", "{радиус:2} → на ход раньше", INK),
                                              ("На проводах", "слабость", "{гибель} → аугменты гаснут", RED))):
        y0 = 284 + j * 44
        FU.cell(sc, 642, y0, 940, y0 + 42, "broken" if col == RED else "normal")
        letters(sc, nm, 650, y0 + 3, "text", 16, col=col)
        letters(sc, when, 932, y0 + 3, "text", 16, col=MUTED, align="right")
        H.fx_line(sc, 650, y0 + 22, line)
    bottom(sc)
    letters(sc, "развитие: новый аугмент или +1 на голема", 236, 495, "text", 16, col=MUTED)
    return finish(sc, "inventor", ret or frame is not None)


# ---------------------------------------------------------------- Маньяк: the lair on the scrapheap
def hazard(sc, x0, y0, x1, y1):
    """Hazard tape: yellow and black stripes on the slant."""
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    band = ((sc.xx + sc.yy) // 6) % 2 == 0
    sc.rgb[m & band] = hexc("#e2ca50")
    sc.rgb[m & ~band] = hexc("#1a1612")
    sc.rgb[y0, x0:x1] = SU.OUTL
    sc.rgb[y1 - 1, x0:x1] = SU.OUTL


def sawblade(sc, cx, cy, r, phase=0.0):
    """A circular saw blade: steel, its teeth raked round, a brass nut at the hub."""
    X, Y = sc.xx - cx, sc.yy - cy
    d = np.hypot(X, Y)
    a = np.arctan2(Y, X) + phase
    tooth = (a * 12 / (2 * np.pi)) % 1.0
    m = d <= r - 2 + 3 * (1 - tooth)
    sh = np.roll(np.roll(m, 3, 0), 2, 1) & ~m
    sc.rgb[sh] *= 0.45
    FU._bands(sc, m, FU.STEEL, 0.7 - (X + Y) / (4 * r))
    sc.rgb[(np.abs(d - r * 0.55) < 0.6) & m] = hexc("#5e5c66")
    sc.rgb[d <= 4] = SU.OUTL
    sc.rgb[d <= 3] = hexc("#a0782c")
    o, _, _ = SU.edges(m)
    sc.rgb[o] = SU.OUTL


def daub(sc, m, col, k=0.45):
    sc.rgb[m] = sc.rgb[m] * (1 - k) + hexc(col) * k


def note(sc, x0, y0, x1, y1, name, when, line, ink=INK_DARK, seed=0):
    """A note nailed up askew: grubby paper, a nail through its top, the name scrawled, when, its line."""
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    m &= ~((sc.xx - x0 + sc.yy - y0) < 4)                                      # a torn corner
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    sc.rgb[m] = (np.array((214, 200, 160)) * (1 - t * 0.3))[m]
    sh = np.roll(np.roll(m, 3, 0), 2, 1) & ~m
    sc.rgb[sh] *= 0.45
    o, _, _ = SU.edges(m)
    sc.rgb[o] = (110, 96, 70)
    nx = (x0 + x1) // 2 + (seed % 3 - 1) * 20
    sc.rgb[y0 + 2:y0 + 6, nx - 1:nx + 2] = SU.OUTL                             # the nail
    sc.rgb[y0 + 3, nx] = hexc("#8e8c96")
    letters(sc, name, x0 + 10, y0 + 8, "text", 16, col=ink, outline=False, shadow=False, jitter=1, seed=seed)
    letters(sc, when, x1 - 8, y0 + 8, "text", 16, col=(110, 96, 70), outline=False, shadow=False, align="right")
    H.fx_line(sc, x0 + 10, y0 + 30, line)


def maniac(ret=False, frame=None):
    sc = screen(77)
    ph = 0.0 if frame is None else frame * 2 * np.pi / 12 / 8
    FU.wing(sc, 0, 0, WW, 44)
    tw = SU.text_width("МАНЬЯК", "title", 24)
    x = WW // 2 - tw // 2
    letters(sc, "МАНЬЯК", x, 4, "title", 24, col=(220, 150, 255), col2=(60, 140, 70), jitter=2,
            seed=5 if frame is None else 5 + frame // 3)                      # the letters jump, every few frames
    sawblade(sc, x - 40, 22, 17, 0.2 + ph)                                    # the saws spin, in opposite ways
    sawblade(sc, x + tw + 40, 22, 17, 0.9 - ph)
    sawblade(sc, x - 82, 26, 11, 0.5 - ph * 1.5)
    sawblade(sc, x + tw + 82, 26, 11, 0.1 + ph * 1.5)
    toolbar(sc)
    hazard(sc, 0, 44, WW, 50)
    # the cage, patchwork plates, the leader behind the bars
    for (a, b, c, d_, seed, paint) in ((12, 56, 180, 300, 81, "#7a2a8a"), (150, 70, 332, 260, 82, None),
                                       (20, 270, 324, 462, 83, "#2a7a3a")):
        FU.plate(sc, a, b, c, d_, seed=seed)
        if paint:
            m = (sc.xx >= a + 8) & (sc.xx < c - 8) & (sc.yy >= b + 8) & (sc.yy < d_ - 8)
            daub(sc, m & ((sc.xx * 3 + sc.yy * 5) % 37 < 26), paint, 0.35)
    sc.rgb[70:380, 30:314] = sc.rgb[70:380, 30:314] * 0.5
    spr = leader_sprite("maniac", 3.8)
    sc.blit(spr, int(170 - spr.ox), int(376 - spr.oy))
    for bx in range(36, 314, 26):                                             # the cage's bars, not quite straight
        lean = (bx % 3) - 1
        for y in range(72, 380):
            xx = bx + int(lean * (y - 72) / 160)
            sc.rgb[y, xx:xx + 3] = hexc("#3a3842")
            sc.rgb[y, xx] = hexc("#6a6870")
            sc.rgb[y, xx + 3] = SU.OUTL
    for yy in (70, 376):
        sc.rgb[yy:yy + 6, 30:316] = hexc("#24222a")
        sc.rgb[yy, 30:316] = hexc("#5e5c66")
        sc.rgb[yy + 6, 30:316] = SU.OUTL
    hazard(sc, 30, 382, 316, 390)
    FU.cell(sc, 24, 396, 220, 432, "rare")
    letters(sc, "МАНЬЯК", 34, 400, "text", 16, col=(220, 150, 255), jitter=1, seed=2)
    letters(sc, "безумный сборщик", 34, 416, "text", 16, col=(150, 220, 150))
    for j, k in enumerate(("c_saw", "c_catapult", "c_fist", "c_triple", "c_upside", "c_burning", "c_salute")):
        mod_icon(sc, k, 228 + (j % 3) * 30 + (j // 3) * 8, 396 + (j // 3) * 20 - (j % 2) * 4, 1)   # the heap
    # the passport, patchwork
    FU.plate(sc, 340, 56, 624, 462, seed=84)
    m = (sc.xx >= 348) & (sc.xx < 616) & (sc.yy >= 200) & (sc.yy < 300)
    daub(sc, m & ((sc.xx + sc.yy * 2) % 29 < 20), "#2a7a3a", 0.25)
    letters(sc, "ПАСПОРТ", 354, 66, "title", 16, col=(220, 150, 255), col2=(60, 30, 80), jitter=1, seed=3)
    H.fx_line(sc, 354, 94, "{лидер} лидерство 10")
    y = stat_rows(sc, 354, 610, 124, (("здоровье", "здоровье", "30"), ("броня", "броня", "1"),
                                      ("скорость", "скорость", "2"), ("размер", "размер", "4"),
                                      ("инициатива", "инициатива", "5")))
    for nm, line in (("Пила", "1–8 +2 {руб}"), ("Бур", "1–4 {кол} · бронебойный")):
        letters(sc, nm, 354, y + 4, "text", 16, col=(220, 150, 255))
        H.fx_line(sc, 410, y + 4, line)
        y += 24
    y += 8
    hazard(sc, 348, y, 616, y + 6)
    y += 14
    letters(sc, "С НИМ", 354, y, "text", 16, col=(150, 220, 150))
    for j, (fr, mods) in enumerate((("Мудрец", ("fireball", "c_saw")), ("Орудие", ("c_catapult", "canister")))):
        gx = 384 + j * 120
        g = army_sprite(fr, 0.55)
        sc.blit(g, int(gx - g.ox), int(y + 74 - g.oy))
        for m_, key in enumerate(mods):
            FU.cell(sc, gx + 26, y + 22 + m_ * 26, gx + 50, y + 46 + m_ * 26, "rare" if key.startswith("c_") else "normal")
            mod_icon(sc, key, gx + 30, y + 26 + m_ * 26, 1)
    y += 84
    letters(sc, "правило: любой модуль", 354, y, "text", 16, col=GOLD, jitter=1, seed=4)
    letters(sc, "в любой фрейм, +2 ячейки", 354, y + 18, "text", 16, col=GOLD, jitter=1, seed=6)
    # abilities on nailed notes, askew
    FU.plate(sc, 632, 56, 948, 462, seed=85)
    for j, (nm, when, line, ink) in enumerate((
            ("Импровизация", "каждые 3", "{свой} {радиус:1} → модуль иной", INK_DARK),
            ("Это должно работать!", "поломка", "взрыв {площадь} → {кол}", INK_DARK),
            ("Дикий смех", "всегда", "{радиус:2} → {страх:1–8}", INK_DARK),
            ("Без техники безопасности", "", "взрывы → {свой} тоже", (150, 30, 30)))):
        off = (j % 2) * 10 - 4
        note(sc, 642 + off, 66 + j * 74, 934 + off, 132 + j * 74, nm, when, line, ink, seed=j)
    hazard(sc, 0, 460, WW, 466)
    bottom(sc)
    letters(sc, "развитие: безумный модуль · полезные причуды", 236, 495, "text", 16, col=MUTED)
    return finish(sc, "maniac", ret or frame is not None)


# ---------------------------------------------------------------- Зодчий: the building site
def ashlar(sc, x0, y0, x1, y1, seed=0, tone=1.0):
    """A wall of dressed stone: blocks laid in courses, each shaded a little its own way, mortar between."""
    rnd = np.random.RandomState(seed)
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    sc.rgb[m] = hexc("#2a2620")
    for r, y in enumerate(range(y0, y1, 22)):
        off = 0 if r % 2 == 0 else -24
        for x in range(x0 + off, x1, 48):
            bx0, bx1, by0, by1 = max(x0, x + 1), min(x1, x + 47), y + 1, min(y1, y + 21)
            if bx1 <= bx0:
                continue
            k = rnd.uniform(0.8, 1.15) * tone
            b = (sc.xx >= bx0) & (sc.xx < bx1) & (sc.yy >= by0) & (sc.yy < by1)
            t = np.clip((sc.yy - by0) / 20.0, 0, 1)[..., None]
            sc.rgb[b] = ((hexc("#8a8070") * (1 - t) + hexc("#5e5648") * t) * k)[b]
            sc.rgb[by0, bx0:bx1] = hexc("#b2a890") * k
            sc.rgb[by0:by1, bx0] = sc.rgb[by0:by1, bx0] * 0.9 + hexc("#b2a890") * 0.1 * k
            for _ in range(3):
                px, py = rnd.randint(bx0, bx1), rnd.randint(by0, by1)
                sc.rgb[py, px] = sc.rgb[py, px] * 0.7


def chisel(sc, text, x, y, kind="text", px=16, align="left", deep=(22, 18, 12), lit=(226, 218, 196)):
    """Letters cut into stone: the cut dark, its lower lip catching the light."""
    letters(sc, text, x + 1, y + 1, kind, px, col=lit, outline=False, shadow=False, align=align)
    letters(sc, text, x, y, kind, px, col=deep, outline=False, shadow=False, align=align)


def tablet(sc, x0, y0, x1, y1, crack=False):
    """A stone tablet / a block of the wall: bevelled, a little rough."""
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    sh = np.roll(np.roll(m, 4, 0), 3, 1) & ~m
    sc.rgb[sh] *= 0.4
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    sc.rgb[m] = (hexc("#9a9282") * (1 - t) + hexc("#6e6656") * t)[m]
    rnd = np.random.RandomState(x0 + y0)
    for _ in range((x1 - x0) * (y1 - y0) // 40):
        px, py = rnd.randint(x0, x1), rnd.randint(y0, y1)
        sc.rgb[py, px] = sc.rgb[py, px] * rnd.uniform(0.82, 1.08)
    o, top, left = SU.edges(m)
    sc.rgb[top | left] = hexc("#c8beaa")
    sc.rgb[o & ~(top | left)] = hexc("#3a342a")
    if crack:
        x, y = x1 - 30, y0 + 2
        for k in range(14):
            sc.rgb[y + k, x + (k // 3) - (k % 2)] = hexc("#2a2620")


def trowel(sc, x0, x1, yc, flip=False):
    """A mason's trowel lying on the beam: the turned wooden handle, the bent shank, the steel blade's point
    toward the title."""
    Xs, Y = sc.xx.astype(float), sc.yy.astype(float)
    X = (x0 + x1 - 1) - Xs if flip else Xs
    hl = (x1 - x0) * 0.42
    handle = (X >= x0) & (X < x0 + hl) & (np.abs(Y - yc) <= 4 - (X - x0) / hl * 1.2)
    shank = (X >= x0 + hl) & (X < x0 + hl + 10) & (np.abs(Y - (yc - (X - x0 - hl) * 0.6)) <= 1.2)
    bx0 = x0 + hl + 8
    blade = (X >= bx0) & (X < x1) & (np.abs(Y - (yc - 6)) <= (x1 - X) / (x1 - bx0) * 9) & (Y <= yc - 6 + 2)
    blade |= (X >= bx0) & (X < x1) & (Y > yc - 6) & (Y <= yc - 6 + (x1 - X) / (x1 - bx0) * 3)
    m = handle | shank | blade
    FU._shadow(sc, m)
    FU._bands(sc, handle, FU.WOOD, 0.6 - (Y - yc) / 10.0)
    pal = FU._bands(sc, shank | blade, FU.STEEL, 0.78 - (Y - (yc - 12)) / 24.0)
    FU._finish(sc, m, pal, flip)


def scaffold(sc, x0, x1, y_floor, levels):
    """Wooden scaffolding: poles up, planks across at each level, braces."""
    for x in (x0, x1):
        sc.rgb[levels[-1] - 20:y_floor, x - 2:x + 2] = hexc("#5a3a1e")
        sc.rgb[levels[-1] - 20:y_floor, x - 2] = hexc("#8a5e2e")
    for y in levels:
        sc.rgb[y:y + 5, x0 - 8:x1 + 9] = hexc("#7c562e")
        sc.rgb[y, x0 - 8:x1 + 9] = hexc("#a07844")
        sc.rgb[y + 5, x0 - 8:x1 + 9] = SU.OUTL
    for k in range(len(levels) - 1):
        ya, yb = levels[k], levels[k + 1]
        for t in np.linspace(0, 1, 60):
            sc.rgb[int(yb + (ya - yb) * t), int(x0 + (x1 - x0) * t)] = hexc("#5a3a1e")


def zodchiy(ret=False, frame=None):
    sc = screen(83)
    ashlar(sc, 0, 44, WW, HH, seed=3, tone=0.62)
    FU.wing(sc, 0, 0, WW, 44)
    tw = SU.text_width("ЗОДЧИЙ", "title", 24)
    x = WW // 2 - tw // 2
    letters(sc, "ЗОДЧИЙ", x, 6, "title", 24, col=(232, 222, 206), col2=(120, 96, 70))
    trowel(sc, x - 150, x - 16, 26, flip=False)
    trowel(sc, x + tw + 16, x + tw + 150, 26, flip=True)
    toolbar(sc)
    # the arch, the scaffolding in it, the leader on its planks
    X, Y = sc.xx, sc.yy
    ax, ay, ar = 171, 170, 128
    opening = ((((X - ax) / ar) ** 2 + ((Y - ay) / ar) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar) & (Y > ay) & (Y < 390))
    ring = ((((X - ax) / (ar + 14)) ** 2 + ((Y - ay) / (ar + 14)) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar + 14) & (Y > ay) & (Y < 390))
    ring &= ~opening
    sc.rgb[ring] = hexc("#8a8070")
    for kk in range(-8, 9):                                                   # the voussoirs' joints
        a_ = np.pi * (0.5 + kk / 18)
        for rr in np.linspace(ar, ar + 14, 15):
            px, py = int(ax - np.cos(a_) * rr), int(ay - np.sin(a_) * rr)
            sc.rgb[py, px] = hexc("#3a342a")
    o, _, _ = SU.edges(ring)
    sc.rgb[o] = SU.OUTL
    sc.rgb[opening] = sc.rgb[opening] * 0.3 + hexc("#1c2230") * 0.7
    for k, (sx, sy) in enumerate(((90, 120), (240, 100), (200, 150), (120, 80), (150, 60), (260, 170), (70, 180))):
        tw = 1.0 if frame is None else 0.5 + 0.5 * np.sin(frame * 2 * np.pi / 24 * (1 + k % 3) + k * 2.1)
        sc.rgb[sy, sx] = sc.rgb[sy, sx] * (1 - tw) + hexc("#d8d0e4") * tw   # stars through the arch, twinkling
    scaffold(sc, 66, 276, 390, [372, 300, 230])
    spr = leader_sprite("zodchiy", 3.1)
    sc.blit(spr, int(171 - spr.ox), int(371 - spr.oy))
    if frame is not None:                                                     # mortar dust sifting off the planks
        rnd_ = np.random.RandomState(7)
        for k in range(10):
            x_ = int(rnd_.uniform(70, 272))
            y_ = int(234 + (rnd_.uniform(0, 140) + frame * 3) % 150)
            sc.rgb[y_, x_] = sc.rgb[y_, x_] * 0.4 + hexc("#c8beaa") * 0.6
    tablet(sc, 20, 396, 322, 434)
    chisel(sc, "ЗОДЧИЙ", 171, 400, "text", 16, align="center")
    chisel(sc, "строитель крепостей", 171, 416, "text", 16, align="center")
    for j, k in enumerate(("w_tower", "w_wall", "w_gate", "w_pitch", "w_press", "w_thunder", "w_boom", "w_forge")):
        mod_icon(sc, k, 24 + j * 37, 440, 1)
    # the passport, cut into a stone tablet
    tablet(sc, 340, 56, 624, 462)
    chisel(sc, "ПАСПОРТ", 354, 66, "title", 16)
    H.fx_line(sc, 354, 94, "{лидер} лидерство 10")
    y = stat_rows(sc, 354, 610, 124, (("здоровье", "здоровье", "25"), ("броня", "броня", "1"),
                                      ("скорость", "скорость", "1"), ("размер", "размер", "4"),
                                      ("инициатива", "инициатива", "5")), lab_col=(40, 34, 26), dot_col="#4a4234")
    chisel(sc, "Кирпичи", 354, y + 4)
    H.fx_line(sc, 432, y + 4, "1–4 +1 {дроб} · дальность 2")
    y += 34
    chisel(sc, "С НИМ", 354, y)
    for j, (fr, mods) in enumerate((("Страж", ("w_wall", "intercept")), ("Механик", ("repair",)),
                                    ("Каменщик", ()), ("Каменщик", ()))):
        gx = 380 + j * 64
        g = army_sprite(fr, 0.48)
        sc.blit(g, int(gx - g.ox), int(y + 78 - g.oy))
        for m_, key in enumerate(mods):
            mod_icon(sc, key, gx - 10 + m_ * 18, y + 84, 1)
    y += 112
    chisel(sc, "правило: строительные", 354, y)
    chisel(sc, "модули в мастерской", 354, y + 18)
    # abilities on blocks of the wall
    for j, (nm, when, line, crack) in enumerate((
            ("Артель", "начало", "каменщик ×2 · +1 за босса", False),
            ("Сигнал к развёртыванию", "ход 2", "все разворачиваются", False),
            ("Камень к камню", "всегда", "развёрнутые {ремонт:1}", False),
            ("Смена позиции", "каждые 4", "свернуться · шаг · развернуться", False),
            ("Долгая стройка", "слабость", "не развернулся → без {атака}", True))):
        y0 = 56 + j * 81
        tablet(sc, 634 + (j % 2) * 8, y0, 948 - ((j + 1) % 2) * 8, y0 + 75, crack=crack)
        chisel(sc, nm, 648 + (j % 2) * 8, y0 + 8, deep=(120, 26, 20) if crack else (22, 18, 12))
        chisel(sc, when, 934 - ((j + 1) % 2) * 8, y0 + 8, align="right", deep=(60, 52, 40))
        H.fx_line(sc, 648 + (j % 2) * 8, y0 + 34, line)
    bottom(sc)
    letters(sc, "развитие: раньше · +1 способность · Цитадель", 236, 495, "text", 16, col=MUTED)
    return finish(sc, "zodchiy", ret or frame is not None)


def finish(sc, name, ret):
    if ret:
        return sc
    img = sc.image(S)
    fn = f"foundry_card_{name}.png"
    img.save(out(fn))
    print(fn, img.size)


if __name__ == "__main__":
    which = sys.argv[1:] or ["inventor", "maniac", "zodchiy"]
    for w in which:
        {"inventor": inventor, "maniac": maniac, "zodchiy": zodchiy}[w]()
