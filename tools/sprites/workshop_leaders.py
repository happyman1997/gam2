"""The workshop as each leader runs it — the same slipway, rack and panel, but what the leader's rule changes is on
the drawing:

  Изобретатель — small hulls (a size down: a cell fewer, cheaper in leadership, so more golems), and on every one
                 an augment cell on the wrist — cold blue, an arc at its mount; the panel offers augments;
  Маньяк       — a module off another hull set where it doesn't belong (the Gun's Mortar on the Sage's back): its box
                 purple, mad sparks at the mount; the panel shows the quirk it rolled, useful or dangerous;
  Зодчий       — a building golem's card with both its forms side by side, marching and deployed, and the levels;
  Отец колосса — the Colossus on the slipway: its body fixed, its seven cells, the colossal module on its shoulder.

    python3 tools/sprites/workshop_leaders.py [inventor|maniac|zodchiy|colossus]
"""
import sys
import numpy as np
from kit import hexc
import foundry_ui as FU
import foundry_hud as FH
from foundry_hud import (screen, title_center, toolbar, heading, action, letters, mod_icon, metal, leader_sprite,
                         slipway, part_box, callout, slot_label, H, SU, INK, MUTED, PALE, GOLD, RED, BRASS, WW, S, out)
import frames as F

FH.MOD_NAME.update({"col_battery": "Плечевая батарея", "col_reactor": "Реактор с трубами", "col_rail": "Рельсотрон",
                    "col_scoop": "Ковш-дробилка", "a_coil": "Грозовая катушка", "a_mirror": "Отражатель",
                    "a_spring": "Пружинный рывок", "c_saw": "Ноги-пилы", "c_catapult": "Голова-катапульта"})


def bay_rack(sc, x0, y0, x1, rows):
    """The army's rack: (frame, cells filled / of, an augment?, chosen, small, scale) — the golem small, its cells,
    a blue augment cell if it has one."""
    y = y0
    for frame, filled, of, aug, sel, small, k in rows:
        FU.cell(sc, x0, y, x1, y + 86, "hi" if sel else "normal")
        g = F.build(frame, "idle", k=F.FRAMES[frame][0] * k)
        sc.blit(g, int(x0 + 34 - g.ox), int(y + 78 - g.oy))
        letters(sc, frame, x0 + 66, y + 6, "text", 16, col=GOLD if sel else INK)
        if small:
            letters(sc, "малый", x0 + 66, y + 24, "text", 16, col=MUTED)
        for j in range(of):
            cx_ = x0 + 68 + j * 12
            sc.rgb[y + 46:y + 56, cx_:cx_ + 9] = SU.OUTL
            sc.rgb[y + 47:y + 55, cx_ + 1:cx_ + 8] = hexc("#e0b860") if j < filled else hexc("#24222a")
        if aug:
            cx_ = x0 + 68 + of * 12 + 4
            sc.rgb[y + 46:y + 56, cx_:cx_ + 9] = SU.OUTL
            sc.rgb[y + 47:y + 55, cx_ + 1:cx_ + 8] = hexc("#7ae8f0")
        FU.core_port(sc, x0 + 74, y + 70, "cast")
        y += 92
    FU.cell(sc, x0, y, x1, y + 44, "locked")
    letters(sc, "+ новый голем", (x0 + x1) / 2, y + 14, "text", 16, col=PALE, align="center")


def frame_screen(seed):
    sc = screen(seed)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "МАСТЕРСКАЯ")
    metal(sc, 14, x=18)
    toolbar(sc)
    return sc


def console(sc):
    FU.sill(sc, 468)
    action(sc, 12, 478, 174, 526, "Автосборка", "steel")
    action(sc, 178, 478, 356, 526, "Починить · 2", "hot")
    action(sc, 360, 478, 522, 526, "Переплавка", "rust")
    action(sc, 526, 478, 704, 526, "Пропуск · +4", "steel")
    action(sc, 710, 472, 948, 532, "В БОЙ", "hot", big=True)


def save(sc, name):
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


# ---------------------------------------------------------------- Изобретатель: small hulls, an augment cell each
def anim_spot(sc, kind, frame):
    """What moves at a leader's own mount: an arc crawling off the augment, mad sparks circling the alien module."""
    import leader_cards as LC
    pt = FH._STATE.get("pts", {}).get("a_coil" if kind == "inventor" else "mortar")
    if pt is None:
        return
    x, y = int(pt[0]), int(pt[1])
    rnd = np.random.RandomState(200 + frame)
    if kind == "inventor":
        sc.glow(x, y, 12, hexc("#2ab0c8"), 0.3 + 0.3 * (frame % 6 < 3))
        if frame % 6 != 5:
            ang = rnd.uniform(-2.6, -0.6)
            LC.jag(sc, LC.arc_pts(x, y, int(x + np.cos(ang) * 22), int(y + np.sin(ang) * 22), 4, rnd, 5))
    else:
        sc.glow(x, y, 12, hexc("#d860d0"), 0.35 + 0.25 * np.sin(frame * 2 * np.pi / 12))
        for k in range(6):
            a = frame * 0.5 + k * np.pi / 3
            r = 8 + 3 * np.sin(frame * 0.7 + k)
            sc.rgb[int(y + np.sin(a) * r), int(x + np.cos(a) * r)] = hexc("#70e080") if k % 2 else hexc("#ffc0f4")


def inventor(frame=None):
    sc = frame_screen(21)
    bay_rack(sc, 10, 52, 168, [("Мудрец", 1, 3, True, True, True, 0.42), ("Орудие", 1, 3, True, False, True, 0.4),
                               ("Механик", 1, 2, True, False, True, 0.4)])
    FU.plate(sc, 176, 52, 700, 462, seed=3)
    hot = slipway(sc, "Мудрец", {"overload": 1}, "cast", 3, (186, 62, 690, 408), role="маг · малый · размер 4",
                  crane=False, scale=0.82, extra=[("аугмент", "arm_n", "a_coil", "augment_hot")])
    H.fx_line(sc, 190, 418, "малый корпус: {модуль:−1} · {лидер} −1")
    for j in range(3):
        cx_ = 690 - (4 - j) * 30
        FU.cell(sc, cx_, 412, cx_ + 24, 436, "hi" if j < 1 else "locked")
    FU.cell(sc, 666, 412, 690, 436, "new")
    letters(sc, "ячейки", 690 - 4 * 30, 440, "text", 16, col=MUTED)
    FU.plate(sc, 708, 52, 948, 462, seed=4)
    for j, (text, on) in enumerate((("ДОБЫЧА", False), ("АУГМЕНТЫ", True), ("РЕМОНТ", False))):
        x0 = 714 + j * 78
        FU.tab(sc, x0, 58, x0 + 74 + (8 if on else 0), 84, text, active=on)
    sc.rgb[84, 710:946] = hexc("#8a6a34")
    letters(sc, "аугмент · запястье", 720, 92, "text", 16, col=(150, 210, 240))
    for j, (k_, nm, line, st) in enumerate((("a_coil", "Грозовая катушка", "{каждые:2} → {молния} {радиус:1}", "hi"),
                                            ("a_mirror", "Отражатель", "первый {атака} → назад", "normal"),
                                            ("a_spring", "Пружинный рывок", "{начало} → прыжок к врагу", "normal"))):
        y0 = 116 + j * 86
        FU.cell(sc, 716, y0, 940, y0 + 78, st)
        FU.cell(sc, 724, y0 + 8, 766, y0 + 50, "locked")
        mod_icon(sc, k_, 729, y0 + 13, 2)
        letters(sc, nm, 776, y0 + 8, "text", 16, col=GOLD if st == "hi" else INK)
        letters(sc, "стоит" if st == "hi" else "на стойке", 776, y0 + 28, "text", 16, col=MUTED)
        H.fx_line(sc, 724, y0 + 54, line)
    H.fx_line(sc, 720, 380, "аугмент — не цифры,", dim=True)
    letters(sc, "а новая способность", 720, 400, "text", 16, col=PALE)
    console(sc)
    if hot:
        H.cursor(sc, hot[1], hot[2])
    if frame is not None:
        anim_spot(sc, "inventor", frame)
        return sc
    save(sc, "foundry_workshop_inventor.png")


# ---------------------------------------------------------------- Маньяк: a module off another hull, and its quirk
def maniac(frame=None):
    sc = frame_screen(23)
    bay_rack(sc, 10, 52, 168, [("Мудрец", 3, 6, False, True, False, 0.46), ("Орудие", 2, 6, False, False, False, 0.44)])
    FU.plate(sc, 176, 52, 700, 462, seed=3)
    M = FH.mounts()["Мудрец"]
    back = M.get("overload", [-10, -70])
    slipway(sc, "Мудрец", {"fireball": 1}, "cast", 2, (186, 62, 690, 408), role="маг · свободная сборка",
            crane=False, extra=[("чужой", back, "mortar", "illegal"), ("безумный", "legs", "c_saw", "normal")])
    H.fx_line(sc, 190, 418, "свободная сборка: любой модуль · {модуль:+2}")
    for j in range(6):
        cx_ = 690 - (6 - j) * 30
        FU.cell(sc, cx_, 412, cx_ + 24, 436, "rare" if j == 1 else ("hi" if j < 3 else "locked"))
    FU.plate(sc, 708, 52, 948, 462, seed=4)
    heading(sc, "ПРИЧУДА", 722, 62)
    FU.cell(sc, 716, 90, 940, 170, "rare")
    FU.cell(sc, 724, 98, 766, 140, "locked")
    mod_icon(sc, "mortar", 729, 103, 2)
    letters(sc, "Мортира", 776, 98, "text", 16, col=(220, 150, 255))
    letters(sc, "не на своём: Мудрец", 776, 118, "text", 16, col=MUTED)
    H.fx_line(sc, 724, 146, "{каждые:3} → {площадь} {радиус:1}")
    letters(sc, "выпала при установке:", 722, 184, "text", 16, col=MUTED)
    FU.cell(sc, 716, 206, 940, 284, "broken")
    letters(sc, "Отдача", 728, 214, "text", 16, col=(220, 150, 255))
    letters(sc, "опасная", 928, 214, "text", 16, col=(210, 130, 220), align="right")
    H.fx_line(sc, 728, 238, "залп → {оглушение:1} себе")
    letters(sc, "могла быть:", 722, 296, "text", 16, col=MUTED)
    FU.cell(sc, 716, 318, 940, 382, "normal")
    letters(sc, "Самонаводка", 728, 324, "text", 16, col=(110, 220, 130))
    letters(sc, "полезная", 928, 324, "text", 16, col=(110, 220, 130), align="right")
    H.fx_line(sc, 728, 348, "залп → по самой толпе")
    letters(sc, "полезных — 1 из 2", 722, 390, "text", 16, col=INK)
    sc.rgb[412:420, 722:934] = hexc("#08070a")
    sc.rgb[412:420, 722:828] = hexc("#2aa040")
    sc.rgb[412:420, 828:934] = hexc("#9a2aa0")
    letters(sc, "развитие: к зелёному", 722, 426, "text", 16, col=PALE)
    console(sc)
    if frame is not None:
        anim_spot(sc, "maniac", frame)
        return sc
    save(sc, "foundry_workshop_maniac.png")


# ---------------------------------------------------------------- Зодчий: a building golem's two forms
def zodchiy():
    import buildings as BD
    sc = screen(25)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "СТРАЖ")
    letters(sc, "щит · строитель", 16, 13, "text", 16, col=MUTED)
    toolbar(sc)
    FU.plate(sc, 6, 50, 590, 476, seed=7)
    for j, (text, dep) in enumerate((("ХОДОВОЙ", False), ("РАЗВЁРНУТЫЙ", True))):
        x0 = 20 + j * 286
        FU.tab(sc, x0, 60, x0 + 140, 86, text, active=dep)
        FH.blueprint_sheet(sc, x0, 86, x0 + 276, 372)
        spr = BD.build("wall", dep, 2, k=2.7)
        ys, xs = np.nonzero(spr.a)
        sc.blit(spr, int(x0 + 138 - (xs.min() + xs.max()) / 2), int(356 - ys.max()))
        FU.cell(sc, x0 + 8, 94, x0 + 200, 132, "normal")
        slot_label(sc, "ходит, бьёт" if not dep else "стена на 3 клетки", x0 + 16, 96)
        letters(sc, "Щит-стена · II", x0 + 16, 112, "text", 16, col=(170, 220, 250), outline=False)
    letters(sc, "→", 296, 220, "title", 24, col=(255, 170, 80), col2=(120, 40, 10), align="center")
    letters(sc, "уровни постройки", 20, 384, "text", 16, col=MUTED)
    for t in (1, 2, 3):
        spr = BD.build("wall", True, t, k=1.0)
        ys, xs = np.nonzero(spr.a)
        x0 = 20 + (t - 1) * 190
        FU.cell(sc, x0, 404, x0 + 180, 466, "hi" if t == 2 else "normal")
        sc.blit(spr, int(x0 + 46 - (xs.min() + xs.max()) / 2), int(462 - ys.max()))
        letters(sc, ("I", "II", "III")[t - 1], x0 + 170, 410, "text", 16, col=GOLD if t == 2 else INK, align="right")
        letters(sc, ("брёвна", "камень", "железо")[t - 1], x0 + 170, 440, "text", 16, col=MUTED, align="right")
    x0, x1 = 612, WW - 18
    FU.plate(sc, 598, 50, WW - 6, 476, seed=8)
    heading(sc, "ДВА ВИДА", x0, 62)
    rows = [("ходовой", "{скорость:1} · {атака} молотом"), ("развернуться", "{на:2} ход · сигнал Зодчего"),
            ("развёрнутый", "неподвижен · без {атака}"), ("стена", "{клетка:3} · мелкие не проходят"),
            ("", "крупные проламывают"), ("свернуться", "раз в 4 хода · смена позиции")]
    y = 92
    for lab, line in rows:
        if lab:
            letters(sc, lab, x0, y, "text", 16, col=MUTED)
            y += 20
        H.fx_line(sc, x0 + 8, y, line)
        y += 30
    heading(sc, "БРОНЯ ПОСТРОЙКИ", x0, y + 4)
    H.fx_line(sc, x0, y + 32, "I — дерево: горит, рубится")
    H.fx_line(sc, x0, y + 56, "II — камень · III — железо")
    FU.sill(sc, 476)
    action(sc, 12, 484, 220, 532, "Назад", "steel")
    save(sc, "foundry_card_build.png")


# ---------------------------------------------------------------- Отец колосса: the Colossus on the slipway
def colossus():
    sc = frame_screen(27)
    FU.cell(sc, 10, 52, 168, 190, "hi")
    g = leader_sprite("colossus", 0.95)
    sc.blit(g, int(60 - g.ox), int(180 - g.oy))
    letters(sc, "Колосс", 100, 58, "text", 16, col=GOLD)
    letters(sc, "лидер", 100, 76, "text", 16, col=MUTED)
    for j in range(7):
        sc.rgb[100 + (j // 4) * 14:110 + (j // 4) * 14, 102 + (j % 4) * 14:111 + (j % 4) * 14] = SU.OUTL
        sc.rgb[101 + (j // 4) * 14:109 + (j // 4) * 14, 103 + (j % 4) * 14:110 + (j % 4) * 14] = \
            hexc("#e0b860") if j < 4 else hexc("#24222a")
    bay_rack(sc, 10, 196, 168, [("Механик", 1, 3, False, False, False, 0.48)])
    FU.plate(sc, 176, 52, 700, 462, seed=3)
    x0, y0, x1, y1 = 186, 62, 690, 408
    FH.blueprint_sheet(sc, x0, y0, x1, y1)
    FU.cell(sc, x0 + 8, y0 + 8, x0 + 214, y0 + 48, "normal")
    slot_label(sc, "корпус: Колосс", x0 + 18, y0 + 9)
    letters(sc, "титан · размер 7", x0 + 18, y0 + 27, "text", 16, col=(170, 220, 250), outline=False)
    spr = leader_sprite("colossus", 2.9)
    ys, xs = np.nonzero(spr.a)
    cx = (x0 + x1) // 2 + 6
    gx, gy = int(cx - (xs.min() + xs.max()) / 2), int(y1 - 14 - ys.max())
    sc.rgb[y1 - 14:y1 - 6, cx - 90:cx + 90] = hexc("#24222a")
    sc.blit(spr, gx, gy)
    bx0, by0, bw_, bh_ = gx + xs.min(), gy + ys.min(), xs.max() - xs.min(), ys.max() - ys.min()
    P = lambda fx, fy: (bx0 + bw_ * fx, by0 + bh_ * fy)
    FH.shoulder_battery(sc, int(bx0 + bw_ * 0.16), int(by0 - 4), 0.5)              # the battery on its shoulder
    left = [("голова", P(0.52, 0.14), "колосс", "не снимается"), ("правая рука", P(0.84, 0.46), "Электробулава", ""),
            ("левая рука", P(0.14, 0.5), "Миниган", ""), ("ноги", P(0.5, 0.9), "колосс", "не снимается")]
    for j, (lab, pt, nm, sub) in enumerate(left):
        by = y0 + 60 + j * 84
        FU.cell(sc, x0 + 10, by, x0 + 150, by + 42, "locked")
        slot_label(sc, lab, x0 + 18, by + 2)
        letters(sc, nm, x0 + 18, by + 21, "text", 16, col=INK)
        callout(sc, pt, (x0 + 150, by + 21), lane=x0 + 160 + j * 7)
    right = [("плечо", P(0.28, 0.04), "col_battery", "trophy"), ("грудь", P(0.5, 0.32), "plates", "normal"),
             ("рука", P(0.82, 0.62), "flail", "normal"), ("спина", P(0.62, 0.2), "magnet", "normal"),
             ("ячейка", P(0.4, 0.55), None, "normal"), ("ячейка", P(0.6, 0.6), None, "normal"),
             ("ячейка", P(0.45, 0.75), None, "normal")]
    for j, (lab, pt, key, st) in enumerate(right):
        by = y0 + 8 + j * 48
        bx = x1 - 10 - 152
        part_box(sc, bx, by, key, lab, 1, state=st, w=152, h=42)
        callout(sc, pt, (bx, by + 21), col=hexc("#e0b860") if st == "trophy" else FH.BLUE, dash=key is None,
                lane=bx - 10 - j * 6)
    H.fx_line(sc, 190, 418, "Один за всех: {модуль} любого корпуса")
    for j in range(7):
        cx_ = 690 - (7 - j) * 30
        FU.cell(sc, cx_, 412, cx_ + 24, 436, "hi" if j < 4 else "locked")
    FU.plate(sc, 708, 52, 948, 462, seed=4)
    heading(sc, "КОЛОССАЛЬНЫЕ", 722, 62)
    for j, (k_, nm, line, st) in enumerate((("col_battery", "Плечевая батарея", "{каждые:3} → ×6 {огонь}", "trophy"),
                                            ("col_reactor", "Реактор с трубами", "каждый 3-й: ход ×2", "locked"),
                                            ("col_rail", "Рельсотрон", "{каждые:4} → луч {кол}", "locked"),
                                            ("col_scoop", "Ковш-дробилка", "{каждые:2} → {дроб} ×3", "locked"))):
        y0_ = 92 + j * 84
        FU.cell(sc, 716, y0_, 940, y0_ + 76, st)
        FU.cell(sc, 724, y0_ + 8, 766, y0_ + 50, "locked")
        mod_icon(sc, k_, 729, y0_ + 13, 2)
        letters(sc, nm, 776, y0_ + 8, "text", 16, col=GOLD if st == "trophy" else PALE)
        letters(sc, "стоит" if st == "trophy" else "развитием", 776, y0_ + 28, "text", 16, col=MUTED)
        H.fx_line(sc, 724, y0_ + 52, line, dim=st != "trophy")
    console(sc)
    save(sc, "foundry_workshop_colossus.png")


if __name__ == "__main__":
    for w in sys.argv[1:] or ["inventor", "maniac", "zodchiy", "colossus"]:
        {"inventor": inventor, "maniac": maniac, "zodchiy": zodchiy, "colossus": colossus}[w]()
