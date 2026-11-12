"""The Foundry's screens, in its own materials (foundry_ui) and the swarm's language of glyphs (fxg, swarm_hud):
the workshop between battles, the golem's card, the leader pick, after the battle, the battle itself.

    python3 tools/sprites/foundry_hud.py            -> every screen into out/
    python3 tools/sprites/foundry_hud.py workshop   -> one (a key of SCREENS)
"""
import sys
import numpy as np
from kit import *
import foundry_ui as FU
from foundry_ui import INK, MUTED, PALE, BRASS, HOT, DARK, RED
import swarm_hud as H
from swarm_ui import letters
import swarm_ui as SU
import icons as IC
from paths import out

S = 2
WW, HH = 960, 540
GOLD = (240, 200, 120)

# ---------------------------------------------------------------- what each module does, in glyphs
MOD_FX = {
    # the Guard
    "tower": ["{дальность} {свой} сзади → {перехват}"],
    "intercept": ["{атака} {свой} {радиус:1} → {перехват:1}"],
    "anchor": ["{начало} → {прикован}", "{клетка:3} → {цель:1}"],
    "plates": ["первые 3 {атака} → {урон:0}"],
    "counter": ["{рана} {радиус:1} {раз} → {атака}"],
    "hot": ["{рана} {радиус:1} → {огонь}"],
    "tracks": ["{размер:−2} → сквозь · {урон} {дроб}"],
    "flail": ["{атака} → {клетка:2}"],
    # the Sage
    "chain": ["{атака} → {молния} {цепь:2}"],
    "ground": ["{каждые:3} → {оглушение:1} {радиус:1}"],
    "overload": ["{каждые:2} → {свой} {радиус:1} {урон:×2}"],
    "fireball": ["{каждые:3} → {огонь} {дальность:5}"],
    "firewall": ["{раз} → {огонь} {клетка:3}"],
    "blades": ["{каждые:2} → {свой} {радиус:1} {атака} {огонь}"],
    # the Forge
    "magnet": ["{всегда} → {притяг} {радиус:3}"],
    "rod": ["{молния} · {дальность} → {цель:1}"],
    "smoke": ["{всегда} → {радиус:1} {дальность:✕}"],
    "whistle": ["{каждые:4} → {страх} {радиус:2}"],
    "maw": ["{каждые:2} → {огонь} {клетка:2}"],
    "greedy": ["{огонь} {дальность} → {урон:0}", "×3 → {огонь} в ответ"],
    # the Gun
    "mortar": ["{каждые:3} → {площадь} {радиус:1}"],
    "long": ["{атака} → {дальность:∞} насквозь"],
    "spider": ["{радиус:1} → отход {клетка:1}"],
    "canister": ["{радиус:1} → {площадь} · {полёт:✕}"],
    "hotshot": ["{атака} → {огонь} {клетка:3}"],
    "bomb": ["{каждые:3} → {через:2} {площадь}"],
    # the Mechanic
    "repair": ["{каждые:2} → {ремонт:4} {радиус:1}"],
    "crane": ["{раз} {поломка} {радиус:1} → {ремонт}"],
    "spares": ["{поломка} {радиус:1} → {модуль} цел"],
    "oiler": ["{свой} {радиус:1} → {инициатива} первым"],
    "welding": ["{ремонт} {радиус:1} · {огонь} {радиус:1}"],
    "oiltank": ["{атака} → масло: {огонь} ×2"],
    # rare
    "torch": ["{начало} → {огонь} {на:∞}", "{атака} → {огонь}"],
    "nozzles": ["{раз} → рывок {клетка:4} · {огонь}"],
    "bounce": ["{атака} → {цепь:3} {огонь}"],
    "whirl": ["{раз} {огонь} {клетка:3} → смерч {на:3}"],
    "grapple": ["{атака} → {притяг} {дальность:2}"],
    "mill": ["{начало} → катится · {урон} {дроб}"],
    "dome": ["{всегда} → {радиус:1} {дальность:✕}"],
    "bombcore": ["{поломка} → {площадь} {радиус:1}"],
    "ram": ["{начало} → разгон · {урон:×2}"],
    "buffer": ["{атака} → отброс · о стену {урон:×2}"],
    "spark": ["{атака} {броня} → {огонь} {радиус:1}"],
    "poker": ["{атака} → отброс в {огонь}"],
    # cores
    "cast": ["{всегда} → {здоровье:+}"],
    "fire": ["{атака} → {огонь}"],
    "volt": ["{атака} → {молния} {цепь}", "{машина} → {оглушение:1}"],
}
MOD_NAME = {}


def _names():
    import frame_modules as FM
    import guard_modules as GM
    for rows in FM.FRAMES.values():
        for key, nm, *_ in rows:
            MOD_NAME[key] = nm
    for key, v in GM.MODULES.items():
        MOD_NAME[key] = v[0]
    for key, nm, *_ in FM.RARE:
        MOD_NAME[key] = nm
    for key, nm, _ in FM.CORES:
        MOD_NAME[key] = nm + " ядро"


_names()


# ---------------------------------------------------------------- shared pieces
def screen(seed):
    """The forge wall, the beam, the tooltips in iron."""
    SU.WOBBLE[0] = 0.0
    H.HOVER.clear()
    H.KIT["cell"] = FU.cell
    return FU.forge(WW, HH, seed)


def title(sc, text, sub=None, epi=None, x=16):
    """The screen's name in pale steel letters, a little heat glowing under them."""
    w = letters(sc, text, x, 6, "title", 24, col=(232, 222, 206), col2=(120, 96, 70), jitter=0)
    for k in range(0, w, 3):                                     # heat along the letters' foot
        sc.rgb[31, x + k] = sc.rgb[31, x + k] * 0.4 + hexc("#ff8a3a") * 0.6
    if epi:
        letters(sc, sub, x + w + 24, 12, "title", 16, col=epi, col2=tuple(int(v * 0.45) for v in epi), jitter=0)
    elif sub:
        letters(sc, sub, x + w + 16, 12, "text", 16, col=MUTED)
    return w


def toolbar(sc, alt=False, on=False):
    """The right end of the beam, the same on every screen: Alt, two sockets kept for buttons to come, «?» (F1)."""
    H.keycap(sc, 790, 14, "Alt", lit=alt)
    for sx in (832, 872):
        FU.socket(sc, sx, 10, sx + 32, 34)
    FU.button(sc, 912, 8, 950, 36, "brass" if on else "steel")
    letters(sc, "?", 931, 14, "title", 16, col=DARK if on else INK, outline=not on, align="center")
    H.keycap(sc, 900, 28, "F1")


def metal(sc, n, x=700):
    """The Foundry's purse, on the beam: ingots and a number."""
    H.glyph(sc, "металл", x, 10, 2)
    letters(sc, str(n), x + 30, 12, "title", 16, col=(214, 220, 236), col2=(90, 96, 120))


def action(sc, x0, y0, x1, y1, text, kind="hot", heated=False, big=False):
    """A button: big ones (the screen's own action) in the title letters, the rest in text."""
    FU.button(sc, x0, y0, x1, y1, kind, heated=heated)
    col = FU.BUTTON[kind][2]
    letters(sc, text, (x0 + x1) / 2, (y0 + y1) / 2 - (9 if big else 8), "title" if big else "text", 16, col=col,
            outline=kind not in ("hot", "brass"), align="center")


def heading(sc, text, x, y):
    return letters(sc, text, x, y, "title", 16, col=GOLD, col2=(130, 90, 40))


def golem_sprite(frame, mods, k):
    import frame_modules as FM
    import guard_modules as GM
    import frames as F
    kk = F.FRAMES[frame][0] * k
    if frame == "Страж":
        return GM.build(list(mods), dict(mods), k=kk)
    return FM.build_multi(frame, dict(mods), k=kk)


def mod_icon(sc, key, x, y, z=1):
    spr = IC.icon(key, z, "module")
    sc.blit(spr, int(x), int(y))
    sc.occ[int(y):int(y) + spr.h, int(x):int(x) + spr.w] |= spr.a
    return spr.w


# ---------------------------------------------------------------- the workshop: one of three, on the golem, to battle
ARMY = [   # (frame, cells, modules {key: level}, core, state)
    ("Страж", 5, {"tower": 2, "intercept": 1, "plates": 1}, "cast", "normal"),
    ("Мудрец", 4, {"chain": 1, "fireball": 1, "overload": 2}, "volt", "broken"),
    ("Орудие", 4, {"mortar": 1, "canister": 1}, "cast", "hi"),
    ("Механик", 3, {"repair": 1, "oiler": 1}, "cast", "normal"),
]
OFFERS = [   # (key, kind, cell state, what it is, for whom, lines)
    ("long", "новый модуль", "new", "Длинный ствол", "Орудие", MOD_FX["long"]),
    ("repair", "улучшение", "hi", "Ремонт II", "Механик", ["{ремонт:4} ⇒ {ремонт:6}"]),
    ("grapple", "редкий", "rare", "Крюк-кошка", "любой", MOD_FX["grapple"]),
]


def workshop(variant=None):
    """The workshop: the golems on their stands, each with its cells of modules and its core; three offers on the
    right — one of three; the chosen one is already shown in the golem's free cell, a chain to it from the card."""
    sc = screen(11)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, "МАСТЕРСКАЯ")
    metal(sc, 14)
    toolbar(sc)
    # the golems
    FU.plate(sc, 12, 52, 690, 462, seed=3)
    cw = 168
    slot_spots = {}
    for i, (frame, ncell, mods, core, state) in enumerate(ARMY):
        x0 = 20 + i * cw
        cx = x0 + cw / 2 - 4
        FU.cell(sc, x0, 60, x0 + cw - 8, 452, state)
        letters(sc, frame, cx, 70, "text", 16, col=GOLD if state == "hi" else INK, align="center")
        show = dict(mods)
        if state == "hi":
            show["long"] = 1                                            # the preview: the chosen module in place
        spr = golem_sprite(frame, show, 1.08)
        # the stand: an anvil-dark block, the core's lamp in front
        sy = 296
        sc.rgb[sy:sy + 14, int(cx - 52):int(cx + 52)] = hexc("#24222a")
        sc.rgb[sy, int(cx - 52):int(cx + 52)] = hexc("#5a5860")
        sc.rgb[sy + 13, int(cx - 52):int(cx + 52)] = SU.OUTL
        core_col = {"cast": "#c8c8d0", "fire": "#ff8a2a", "volt": "#8ad8ff"}[core]
        cc = (int(cx), sy + 7)
        d = np.hypot(sc.xx - cc[0], sc.yy - cc[1])
        sc.rgb[d < 5] = SU.OUTL
        sc.rgb[d < 4] = hexc(core_col)
        if state == "broken":                                          # broken: dark, slumped, the core out
            sc.rgb[d < 4] = hexc("#3a3a40")
            from swarm_effects import lit
            spr = lit(spr, (70, 70, 80), 0.45)
        put = int(cx - spr.ox), int(sy - spr.oy)
        sc.blit(spr, *put)
        if state == "broken":
            FU.steam(sc, cx + 14, sy - 70, 10, seed=i)
            H.glyph(sc, "поломка", int(cx - 10), 92, 2)
        # its cells: icon, level notches; the empty ones dark
        sw_ = 30
        row_x = cx - (ncell * (sw_ + 2)) / 2
        keys = list(mods) + (["long"] if state == "hi" else [])
        for j in range(ncell):
            sx = int(row_x + j * (sw_ + 2))
            sy2 = 320
            if j < len(keys):
                k_ = keys[j]
                new = state == "hi" and k_ == "long"
                FU.cell(sc, sx, sy2, sx + sw_, sy2 + sw_, "new" if new else "normal")
                mod_icon(sc, k_, sx + 7, sy2 + 7)
                H.HOVER.append(("@" + k_, sx + 7, sy2 + 7, 16, 16))
                FU.levels(sc, sx + 6, sy2 + sw_ + 3, show.get(k_, 1))
                slot_spots[(frame, k_)] = (sx, sy2)
            else:
                FU.socket(sc, sx + 2, sy2 + 2, sx + sw_ - 2, sy2 + sw_ - 2)
        # under the cells: its body and what keeps it whole
        hp_full = {"Страж": 10, "Мудрец": 10, "Орудие": 10, "Механик": 10}[frame]
        hp_now = {"Страж": 7, "Мудрец": 0, "Орудие": 10, "Механик": 9}[frame]
        H.glyph(sc, "здоровье", int(x0 + 14), 374, 2)
        SU.meter(sc, x0 + 40, 380, x0 + 140, 7, hp_full, hp_now, "#c04a3a")
        if state == "broken":
            H.fx_line(sc, x0 + 14, 404, "{ремонт} {металл:2}")
        H.glyph(sc, "ядро", int(x0 + 14), 424, 2)
        letters(sc, MOD_NAME[core].split()[0].lower(), x0 + 40, 424, "text", 16, col=MUTED)
    # the offers: one of three
    FU.plate(sc, 700, 52, 948, 462, seed=4)
    heading(sc, "НАГРАДА", 714, 64)
    H.fx_line(sc, 714, 86, "{выбор:1 из 3}", dim=True)
    for j, (key, kind, st, nm, who, lines) in enumerate(OFFERS):
        y0 = 114 + j * 114
        hov = variant is None and j == 2
        FU.cell(sc, 710, y0, 938, y0 + 106, "hover" if hov else st)
        FU.cell(sc, 718, y0 + 10, 770, y0 + 62, "locked")
        mod_icon(sc, key, 728, y0 + 20, 2)
        letters(sc, nm, 780, y0 + 10, "text", 16, col=GOLD if st == "hi" else INK)
        letters(sc, kind, 780, y0 + 28, "text", 16, col={"new": (140, 200, 230), "hi": BRASS, "rare": (200, 150, 240)}[st])
        letters(sc, who, 780, y0 + 46, "text", 16, col=PALE)
        H.fx_rows(sc, 722, y0 + 74, 210, lines)
        if j == 0:
            a = (710, y0 + 40)
    # a brass chain from the chosen card to the free cell it will take
    bx, by = slot_spots[("Орудие", "long")]
    tgt = (bx + 15, by - 2)
    n = 40
    for k in range(n + 1):
        t = k / n
        x = a[0] + (tgt[0] - a[0]) * t
        y = a[1] + (tgt[1] - a[1]) * t + np.sin(t * np.pi) * 40
        xi, yi = int(x), int(y)
        if k % 2 == 0:                                                   # a link face-on
            sc.rgb[yi - 2:yi + 3, xi - 3:xi + 4] = SU.OUTL
            sc.rgb[yi - 1:yi + 2, xi - 2:xi + 3] = hexc("#e0b860")
            sc.rgb[yi, xi - 1:xi + 2] = hexc("#5a4020")
        else:                                                            # edge-on
            sc.rgb[yi - 1:yi + 2, xi - 2:xi + 3] = SU.OUTL
            sc.rgb[yi, xi - 1:xi + 2] = hexc("#f8d890")
    # leaving
    action(sc, 12, 478, 210, 526, "Автосборка", "steel")
    action(sc, 220, 478, 450, 526, "Починить всё · 2", "hot")
    action(sc, 460, 478, 690, 526, "Пропустить · +4", "steel")
    action(sc, 700, 472, 948, 532, "В БОЙ", "hot", big=True)
    # the living: a chain from the beam between the plates, sparks off the anvil
    FU.chain(sc, 695, 44, 104)
    sc.rgb[104:110, 691:700] = SU.OUTL
    sc.rgb[105:109, 692:699] = hexc("#8a8890")
    FU.sparks(sc, 20, 470, 12, seed=5)
    name = "foundry_workshop.png"
    if variant == "tip":
        H.point_at(sc, "@long", 0, w=280)
        name = "foundry_tip.png"
    elif variant is None:
        H.cursor(sc, 900, 360)
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


# ---------------------------------------------------------------- the golem's card, as big as the screen
ABIL = {   # the frame's and the class's own, in glyphs
    "Наводка": ["{дальность} → 2–3 ряд", "{дальность} → {урон} без потерь"],
    "Огнеупорность": ["{огонь} ×¼ · гаснет за ход"],
    "Литой металл": ["{кол} ×½ · {дроб} ×1 · {кисл} ×2"],
    "Бесстрашие": ["{страх:✕} · {яд:✕}"],
    "Проводник": ["{молния} ×1,5"],
}


def card(frame="Орудие", hover="Мортира"):
    """A golem's card, as in Conquest of Elysium: the golem large on its stand with what it costs and what drives it;
    its body and its blow in a column; its modules in their cells, level by level; on the right what it can and can't,
    the one under the mouse opened in a tooltip."""
    sc = screen(13)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, frame.upper(), "стрелок · голем")
    toolbar(sc)
    FU.plate(sc, 6, 50, WW - 6, HH - 6, seed=7)
    mods = {"mortar": 1, "canister": 1, "long": 1}
    # left: the golem
    FU.cell(sc, 18, 62, 300, 300, "hi")
    spr = golem_sprite(frame, mods, 1.7)
    sc.rgb[276:286, 70:250] = hexc("#24222a")
    sc.rgb[276, 70:250] = hexc("#5a5860")
    sc.blit(spr, int(160 - spr.ox), int(278 - spr.oy))
    y = 314
    for key, lab, val in (("лидер", "лидерство", "5"), ("ядро", "ядро", "литое"), ("убийство", "в прошлом бою", "3")):
        H.glyph(sc, key, 24, y, 2)
        letters(sc, lab, 58, y + 2, "text", 16, col=MUTED)
        letters(sc, val, 290, y + 2, "text", 16, col=INK, align="right")
        y += 30
    action(sc, 22, HH - 54, 296, HH - 16, "Закрыть", "steel")
    # middle: body, blow, modules
    x0, x1 = 316, 616
    heading(sc, "ТЕЛО", x0, 62)
    y = 88
    for key, val in (("здоровье", "55"), ("броня", "2 {литой}"), ("скорость", "1"), ("размер", "5"), ("инициатива", "4")):
        a_ = H.glyph(sc, key, x0, y - 4, 2)
        w, _ = H.fx_line(sc, 0, 0, val, draw=False)
        H.dots(sc, x0 + a_ + 8, x1 - w - 6, y + 10)
        H.fx_line(sc, x1 - w, y - 2, val)
        y += 24
    y += 8
    heading(sc, "ВОЗМОЖНОСТИ", x0, y)
    y += 26
    cols = (x0 + 20, x0 + 112, x0 + 192, x0 + 252)
    for cx, lab in zip(cols, ("атака", "урон", None, "дальность")):
        if lab:
            H.glyph(sc, lab, cx, y - 6, 2)
    y += 14
    sc.rgb[y, x0:x1] = sc.rgb[y, x0:x1] * 0.5 + hexc("#5a5860") * 0.5
    mod_icon(sc, "long", x0, y + 5)
    letters(sc, "Ствол", cols[0], y + 6, "text", 16, col=GOLD)
    letters(sc, "1–10 +3", cols[1], y + 6, "text", 16, col=INK)
    H.fx_line(sc, cols[2], y + 6, "{дроб}")
    letters(sc, "3", cols[3], y + 6, "text", 16, col=INK)
    y += 30
    H.fx_line(sc, x0 + 20, y, ABIL["Наводка"][1], dim=True)
    y += 34
    heading(sc, "МОДУЛИ", x0, y)
    y += 28
    for j, (k_, lv) in enumerate(list(mods.items()) + [(None, 0)]):
        sx = x0 + j * 62
        if k_:
            FU.cell(sc, sx, y, sx + 54, y + 54, "new" if k_ == "long" else "normal")
            mod_icon(sc, k_, sx + 11, y + 11, 2)
            FU.levels(sc, sx + 18, y + 58, lv)
        else:
            FU.socket(sc, sx + 4, y + 4, sx + 50, y + 50)
    # right: what it can and can't
    rx0, rx1 = 632, WW - 18
    heading(sc, "СПОСОБНОСТИ", rx0, 62)
    rows = [("glyph", "цель", "Наводка", "фрейм", GOLD),
            ("mod", "mortar", "Мортира", "модуль · I", INK),
            ("mod", "canister", "Картечь", "модуль · I", INK),
            ("mod", "long", "Длинный ствол", "модуль · I · новый", (140, 200, 230)),
            ("glyph", "огонь", "Огнеупорность", "класс", (214, 196, 150)),
            ("glyph", "литой", "Литой металл", "класс", (214, 196, 150)),
            ("glyph", "дух", "Бесстрашие", "класс", (214, 196, 150)),
            ("glyph", "молния", "Проводник", "слабость", RED)]
    y = 88
    for kind, key, nm, lab, col in rows:
        if nm == hover:
            FU.cell(sc, rx0 - 6, y - 4, rx1, y + 38, "hi")
            hy = y
        if kind == "mod":
            mod_icon(sc, key, rx0, y, 2)
        else:
            H.glyph(sc, key, rx0 + 2, y + 2, 2)
        letters(sc, nm, rx0 + 42, y + 1, "text", 16, col=col)
        letters(sc, lab, rx0 + 42, y + 18, "text", 16, col=MUTED)
        y += 44
    # the one under the mouse
    key = {"Мортира": "mortar", "Картечь": "canister", "Длинный ствол": "long"}.get(hover)
    lines = MOD_FX[key] if key else ABIL[hover]
    th = H.fx_rows(sc, 0, 0, rx1 - rx0 - 24, lines, draw=False) + 40
    ty = min(hy + 46, HH - 16 - th)
    FU.cell(sc, rx0 + 10, ty, rx1, ty + th, "normal")
    letters(sc, hover, rx0 + 22, ty + 8, "text", 16, col=GOLD)
    H.fx_rows(sc, rx0 + 22, ty + 32, rx1 - rx0 - 34, lines)
    H.cursor(sc, rx0 + 150, hy + 12)
    img = sc.image(S)
    img.save(out("foundry_card.png"))
    print("foundry_card.png", img.size)


# ---------------------------------------------------------------- choosing the leader
PICK = [   # (name, epithet, sprite, scale on the card, the army it starts with, its own rule)
    ("Отец колосса", "армия из одного", "colossus", 1.55, ["Механик"], "{каждые:3} → {оглушение:1} {радиус:1}"),
    ("Изобретатель", "мастер аугментов", "inventor", 2.6, ["Мудрец", "Орудие", "Механик"],
     "{начало} → {свой} {радиус:1} {модуль:+1}"),
    ("Маньяк", "безумный сборщик", "maniac", 2.2, ["Мудрец", "Орудие"], "{каждые:3} → {свой} {модуль} наугад"),
    ("Зодчий", "строитель крепостей", "zodchiy", 2.15, ["Страж", "Механик"], "{начало} → каменщик ×2"),
]


def leader_sprite(kind, k, pose="idle"):
    import golems_h as GH
    import leaders_h as LH
    if kind == "colossus":
        return GH.colossus_build(pose, k)
    return GH.build({"inventor": LH.INVENTOR, "maniac": GH.MANIAC, "zodchiy": LH.ZODCHIY}[kind], pose, k)


def leaders_pick():
    """Four leaders, each behind a furnace door: the chosen one's door is open and hot. Under each: the golems it
    starts with, and its own rule; the rest behind «Полное описание»."""
    import frames as F
    sc = screen(17)
    FU.wing(sc, 0, 0, WW, 44)
    w = title(sc, "ЛИДЕР")
    letters(sc, "КТО ПОВЕДЁТ КУЗНЮ", 16 + w + 30, 8, "title", 24, col=(255, 170, 80), col2=(120, 40, 10))
    toolbar(sc)
    for i, (nm, epi, kind, k, army, rule) in enumerate(PICK):
        x0, sel = 14 + i * 236, i == 0
        x1 = x0 + 226
        FU.plate(sc, x0, 54, x1, 456, seed=20 + i)
        # the furnace mouth: an arch, its fire bright on the chosen one
        X, Y = sc.xx, sc.yy
        ax, ay, ar = (x0 + x1) / 2, 200, 86
        arch = ((((X - ax) / ar) ** 2 + ((Y - ay) / ar) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar) & (Y > ay) & (Y < 300))
        t = np.clip((Y - 114) / 186, 0, 1)
        if sel:
            fire = hexc("#3a1606")[None, None, :] * (1 - t[..., None]) + hexc("#ff7a1a")[None, None, :] * t[..., None]
        else:
            fire = hexc("#141216")[None, None, :] * (1 - t[..., None]) + hexc("#4a2010")[None, None, :] * t[..., None]
        sc.rgb[arch] = fire[arch]
        rim = arch & ~((((X - ax) / (ar - 3)) ** 2 + ((Y - ay) / (ar - 3)) ** 2 <= 1) & (Y <= ay) | ((np.abs(X - ax) <= ar - 3) & (Y > ay) & (Y < 300)))
        sc.rgb[rim] = hexc("#b8904a") if sel else hexc("#4a4850")
        for kk in range(-4, 5):                                       # the voussoirs: rivets round the arch
            a_ = np.pi * (0.5 + kk / 10)
            FU.rivet(sc, ax - np.cos(a_) * (ar + 4), ay - np.sin(a_) * (ar + 4))
        spr = leader_sprite(kind, k)
        sc.blit(spr, int(ax - spr.ox), int(296 - spr.oy))
        if sel:
            FU.sparks(sc, ax - 60, 296, 10, seed=3)
            FU.sparks(sc, ax + 64, 290, 8, seed=4)
        # the brass nameplate
        FU.cell(sc, x0 + 10, 62, x1 - 10, 104, "hi" if sel else "normal")
        letters(sc, nm.upper(), ax, 68, "title", 16, col=(255, 210, 140) if sel else INK, align="center")
        letters(sc, epi, ax, 86, "text", 16, col=BRASS if sel else MUTED, align="center")
        # what it starts with: its golems small, and its rule
        gx = ax - (len(army) - 1) * 28
        for j, fr in enumerate(army):
            g = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.58)
            sc.blit(g, int(gx + j * 56 - g.ox), int(380 - g.oy))
        wl, _ = H.fx_line(sc, 0, 0, rule, draw=False)
        H.fx_line(sc, int(ax - wl / 2), 396, rule)
        sc.rgb[300:302, x0 + 16:x1 - 16] = hexc("#5a5860")
    action(sc, 12, 474, 300, 526, "Назад", "steel")
    action(sc, 326, 474, 634, 526, "Полное описание", "steel")
    action(sc, 660, 470, 948, 530, "В ПОХОД", "hot", big=True)
    img = sc.image(S)
    img.save(out("foundry_leader_pick.png"))
    print("foundry_leader_pick.png", img.size)


# ---------------------------------------------------------------- after the battle
def aftermath():
    """Victory: what broke and what it cost, what the battle paid, who did what."""
    import frames as F
    from swarm_effects import lit
    sc = screen(19)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, "ПОБЕДА")
    metal(sc, 20)
    toolbar(sc)
    # broken
    FU.plate(sc, 12, 52, 330, 462, seed=31)
    heading(sc, "ПОЛОМКИ", 26, 64)
    g = lit(F.build("Мудрец", "broken", k=1.6 * 1.35), (70, 70, 80), 0.45)
    sc.blit(g, int(170 - g.ox), int(262 - g.oy))
    FU.steam(sc, 196, 150, 14, seed=2)
    H.glyph(sc, "поломка", 26, 92, 2)
    letters(sc, "Мудрец", 60, 94, "text", 16, col=INK)
    FU.cell(sc, 22, 276, 320, 340, "broken")
    mod_icon(sc, "overload", 32, 290, 2)
    letters(sc, "Перегрузка", 74, 286, "text", 16, col=INK)
    H.fx_line(sc, 74, 308, "{модуль:II} ⇒ {модуль:I}")
    H.fx_line(sc, 26, 360, "{ремонт} → {металл:2}")
    H.fx_line(sc, 26, 392, "не починил → пропускает бой", dim=True)
    # the battle's pay
    FU.plate(sc, 340, 52, 640, 462, seed=32)
    heading(sc, "ДОБЫЧА", 354, 64)
    H.glyph(sc, "металл", 354, 100, 2)
    letters(sc, "+6", 392, 96, "title", 24, col=(214, 220, 236), col2=(90, 96, 120))
    letters(sc, "награда за бой", 470, 102, "text", 16, col=MUTED)
    H.glyph(sc, "гибель", 354, 156, 2)
    letters(sc, "41", 392, 150, "title", 24, col=(255, 140, 110), col2=(170, 50, 40))
    letters(sc, "врагов", 470, 156, "text", 16, col=MUTED)
    FU.cell(sc, 350, 192, 630, 258, "trophy")
    letters(sc, "трофей: нет — враг живой", 364, 202, "text", 16, col=MUTED)
    H.fx_line(sc, 364, 226, "{машина} → {модуль} · {металл}", dim=True)
    heading(sc, "КТО ЧТО", 354, 272)
    for j, (fr, kills, dmg_) in enumerate((("Страж", 6, 31), ("Мудрец", 12, 40), ("Орудие", 17, 12), ("Механик", 0, 3))):
        y = 298 + j * 40
        g = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.42)
        sc.blit(g, int(374 - g.ox), int(y + 34 - g.oy))
        letters(sc, fr, 400, y + 4, "text", 16, col=INK)
        H.fx_line(sc, 500, y + 2, f"{{убийство:{kills}}}")
        H.fx_line(sc, 566, y + 2, f"{{рана:{dmg_}}}")
    # what next
    FU.plate(sc, 650, 52, 948, 462, seed=33)
    heading(sc, "ДАЛЬШЕ", 664, 64)
    H.fx_line(sc, 664, 96, "{выбор:1 из 3} → {модуль}")
    H.fx_line(sc, 664, 128, "{металл} → {ремонт} · голем · переплавка", dim=True)
    lead = leader_sprite("zodchiy", 1.9)
    sc.blit(lead, int(800 - lead.ox), int(420 - lead.oy))
    FU.sparks(sc, 740, 420, 10, seed=8)
    action(sc, 650, 470, 948, 530, "В МАСТЕРСКУЮ", "hot", big=True)
    img = sc.image(S)
    img.save(out("foundry_aftermath.png"))
    print("foundry_aftermath.png", img.size)


# ---------------------------------------------------------------- the battle, seen from the Foundry
def battle():
    """The same battle as the swarm's, the interface the Foundry's: an iron beam with the tug of war (hot iron from
    the left, the swarm's green from the right), the speed, the keys; both leaders' health over them."""
    import copy
    import battle as BT
    import swarm_status as ST
    import swarm1 as W
    sc, count, ng = BT.build("Матка")
    H.HOVER.clear()
    H.KIT["cell"] = FU.cell
    qx, qy = BT.X0 + 15.6 * BT.CW, BT.Y0 + 8.4 * BT.CH
    qtop = ST.top_of(W.queen(0.0, "attack", k=0.92), qy)
    lx, ly = BT.X0 + 2.5 * BT.CW, BT.Y0 + 6.8 * BT.CH
    ltop = ST.top_of(BT.LH.GH.build(BT.LH.ZODCHIY, "idle", 1.05), ly)
    SU.meter(sc, lx - 40, ltop - 12, lx + 40, 7, 10, 7, "#d08a3a")
    H.glyph(sc, "лидер", lx - 58, ltop - 14, 2)
    SU.meter(sc, qx - 46, qtop - 12, qx + 46, 7, 10, 8, "#c04a3a")
    H.glyph(sc, "лидер", qx - 64, qtop - 14, 2)
    FU.wing(sc, 0, 0, WW, 34)
    letters(sc, f"Литейщик {ng - 1}/{ng}", 14, 9, "text", 16, col=(240, 200, 150))
    x0, x1, y0, y1 = 150, 520, 10, 25                       # the tug: hot iron from the left, the swarm from the right
    share = 0.42
    mid = x0 + (x1 - x0) * share
    X, Y = sc.xx, sc.yy
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    t = np.clip((Y - y0) / (y1 - y0), 0, 1)[..., None]
    left = m & (X < mid)
    right = m & (X >= mid)
    sc.rgb[left] = (hexc("#ffb050") * (1 - t) + hexc("#7a2a0a") * t)[left]
    sc.rgb[right] = (hexc("#b4f47a") * (1 - t) + hexc("#2a6224") * t)[right]
    for x in range(x0 + 8, int(mid) - 4, 12):
        FU.rivet(sc, x, (y0 + y1) // 2)
    o, _, _ = SU.edges(m)
    sc.rgb[o] = SU.OUTL
    FU.sparks(sc, mid, (y0 + y1) / 2, 8, seed=2)
    letters(sc, f"рой {count - 1}", 530, 9, "text", 16, col=(170, 240, 120))
    letters(sc, "ход 5", 728, 13, "title", 8, col=MUTED, outline=False, align="right")
    for bx0, bx1, t_, on, key in ((736, 784, "II", False, "Пробел"), (790, 838, "×2", True, "Tab"),
                                  (844, 952, "в конец »", False, "End")):
        FU.button(sc, bx0, 5, bx1, 29, "brass" if on else "steel")
        letters(sc, t_, (bx0 + bx1) / 2, 9, "text", 16, col=DARK if on else INK, outline=not on, align="center")
        kw = SU.text_width(key, "title", 8) + 14
        H.keycap(sc, int((bx0 + bx1) / 2 - kw / 2), 32, key)
    img = sc.image(S)
    img.save(out("foundry_battle.png"))
    print("foundry_battle.png", img.size)


SCREENS = {"workshop": workshop, "card": card, "leader": leaders_pick, "aftermath": aftermath, "battle": battle}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in SCREENS.items():
        if arg in ("all", k):
            fn()
