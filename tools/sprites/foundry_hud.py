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


# ---------------------------------------------------------------- building a golem: the slipway and the steps
ARMY = [   # (frame, cells, modules {key: level}, core, state)
    ("Страж", 5, {"tower": 2, "intercept": 1, "plates": 1}, "cast", "normal"),
    ("Мудрец", 4, {"chain": 1, "fireball": 1, "overload": 2}, "volt", "broken"),
    ("Орудие", 4, {"mortar": 1, "canister": 1}, "cast", "hi"),
    ("Механик", 3, {"repair": 1, "oiler": 1}, "cast", "normal"),
]
OFFERS = [   # (key, kind, cell state, its name, for whom, lines)
    ("long", "новый модуль", "new", "Длинный ствол", "Орудие", MOD_FX["long"]),
    ("repair", "улучшение", "hi", "Ремонт II", "Механик", ["{ремонт:4} ⇒ {ремонт:6}"]),
    ("grapple", "редкий", "rare", "Крюк-кошка", "любой", MOD_FX["grapple"]),
]
# where each part sits on the frame, as an offset from the golem's foot at the slipway's scale 2.56 (frame scale 1.6):
# a callout runs from that point to the part's box
MOUNT = {
    "Орудие": {"mortar": ("спина", (-13, -104)), "canister": ("рука", (6, -44)), "long": ("ствол", (40, -22)),
               "free": ("плечо", (-24, -80)), "core": ("грудь · ядро", (10, -66))},
}
BLUE = hexc("#9ad8ff")


def blueprint_sheet(sc, x0, y0, x1, y1, stamp=None, top=False):
    """The drawing pinned behind the slipway: blue paper, a fine grid and a bolder one, a frame round it, tacks in
    the corners, a title block in the corner."""
    sc.rgb[y0:y1, x0:x1] = hexc("#14243a")
    for x in range(x0, x1, 8):
        sc.rgb[y0:y1, x] = sc.rgb[y0:y1, x] * 0.8 + hexc("#24405e") * 0.2
    for y in range(y0, y1, 8):
        sc.rgb[y, x0:x1] = sc.rgb[y, x0:x1] * 0.8 + hexc("#24405e") * 0.2
    for x in range(x0, x1, 40):
        sc.rgb[y0:y1, x] = sc.rgb[y0:y1, x] * 0.6 + hexc("#3a6a94") * 0.4
    for y in range(y0, y1, 40):
        sc.rgb[y, x0:x1] = sc.rgb[y, x0:x1] * 0.6 + hexc("#3a6a94") * 0.4
    for k in (3, 4):
        sc.rgb[y0 + k, x0 + k:x1 - k] = BLUE * 0.6
        sc.rgb[y1 - 1 - k, x0 + k:x1 - k] = BLUE * 0.6
        sc.rgb[y0 + k:y1 - k, x0 + k] = BLUE * 0.6
        sc.rgb[y0 + k:y1 - k, x1 - 1 - k] = BLUE * 0.6
    for (tx, ty) in ((x0 + 9, y0 + 9), (x1 - 10, y0 + 9), (x0 + 9, y1 - 10), (x1 - 10, y1 - 10)):
        sc.rgb[ty - 2:ty + 3, tx - 2:tx + 3] = SU.OUTL
        sc.rgb[ty - 1:ty + 2, tx - 1:tx + 2] = hexc("#c84a3a")
    if stamp:
        bx0, by0 = x1 - 190, (y0 + 20 if top else y1 - 46)
        by1 = by0 + 41
        sc.rgb[by0:by1, bx0:x1 - 5] = sc.rgb[by0:by1, bx0:x1 - 5] * 0.6 + hexc("#0c1828") * 0.4
        sc.rgb[by0, bx0:x1 - 5] = BLUE * 0.6
        sc.rgb[by1, bx0:x1 - 5] = BLUE * 0.6
        sc.rgb[by0:by1, bx0] = BLUE * 0.6
        for j, ln in enumerate(stamp):
            letters(sc, ln, bx0 + 8, by0 + 5 + j * 18, "text", 16, col=(170, 220, 250), outline=False)
    sc.occ[y0:y1, x0:x1] = True
    sc.light[y0:y1, x0:x1] = 0


def drawn(spr, col="#9ad8ff", fill="#1e3a5a"):
    """A frame as a drawing on the blueprint: the outline and the inner edges in light lines, the body filled
    with the paper's darker blue — not built yet."""
    import numpy as np
    s = spr.__class__(spr.w, spr.h)
    s.a = spr.a.copy()
    lum = spr.rgb.mean(axis=2)
    s.rgb[:] = hexc(fill)
    a = spr.a
    edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    gy = np.abs(np.roll(lum, 1, 0) - lum) + np.abs(np.roll(lum, 1, 1) - lum)
    inner = a & (gy > 34)
    s.rgb[inner] = hexc(col) * 0.55 + hexc(fill) * 0.45
    s.rgb[edge] = hexc(col)
    s.ox, s.oy = spr.ox, spr.oy
    return s


def callout(sc, p, q, col=BLUE, dash=False):
    """A leader line from a point on the golem to a part's box: a dot at the point, a dogleg to the box."""
    (px, py), (qx, qy) = p, q
    mx = qx
    pts = [(px, py), (mx, py), (qx, qy)] if abs(qy - py) > 2 else [(px, py), (qx, qy)]
    pts = [(px, py), (px + (qx - px) * 0.5, py), (px + (qx - px) * 0.5, qy), (qx, qy)]
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(bx - ax), abs(by - ay))) + 1
        for i in range(n):
            if dash and (i // 3) % 2:
                continue
            x = int(round(ax + (bx - ax) * i / max(1, n - 1)))
            y = int(round(ay + (by - ay) * i / max(1, n - 1)))
            sc.rgb[y, x] = col
    sc.rgb[int(py) - 2:int(py) + 3, int(px) - 2:int(px) + 3] = SU.OUTL
    sc.rgb[int(py) - 1:int(py) + 2, int(px) - 1:int(px) + 2] = col


def part_box(sc, x, y, key, label, lv=1, state="normal", w=118):
    """A part's box at the end of a callout: the mount's name, the module's icon, its name, its level."""
    FU.cell(sc, x, y, x + w, y + 46, state)
    letters(sc, label.upper(), x + 8, y + 5, "title", 8, col=(150, 200, 230), outline=False)
    if key:
        mod_icon(sc, key, x + 8, y + 18)
        H.HOVER.append(("@" + key, x + 8, y + 18, 16, 16))
        letters(sc, MOD_NAME[key], x + 30, y + 18, "text", 16, col=INK if state != "new" else (170, 220, 250))
        FU.levels(sc, x + w - 26, y + 6, lv)
    else:
        letters(sc, "свободно", x + 30, y + 18, "text", 16, col=PALE)
    return x + w, y + 23


def crane_hook(sc, x, y_top, y_hook, key):
    """The gantry's trolley, its chain down, the hook, and the part hanging from it."""
    sc.rgb[y_top:y_top + 8, x - 16:x + 17] = hexc("#3a3840")
    sc.rgb[y_top, x - 16:x + 17] = hexc("#6a6870")
    sc.rgb[y_top + 7, x - 16:x + 17] = SU.OUTL
    FU.rivet(sc, x - 10, y_top + 4)
    FU.rivet(sc, x + 10, y_top + 4)
    FU.chain(sc, x, y_top + 8, y_hook)
    for k in range(6):                                                # the hook
        sc.rgb[y_hook + k, x - 1:x + 2] = hexc("#8a8890")
    sc.rgb[y_hook + 5:y_hook + 8, x - 4:x + 2] = hexc("#8a8890")
    sc.rgb[y_hook + 3:y_hook + 6, x - 5] = hexc("#8a8890")
    spr = IC.icon(key, 3, "module")
    sc.blit(spr, int(x - spr.w / 2), int(y_hook + 8))
    sc.occ[int(y_hook + 8):int(y_hook + 8) + spr.h, int(x - spr.w / 2):int(x - spr.w / 2) + spr.w] |= spr.a
    return int(y_hook + 8 + spr.h)


def rack(sc, x0, y0, x1, sel="Орудие"):
    """The army on its rack, one bay each: the golem small, its cells filled or not; and a bay for a new one."""
    import frames as F
    y = y0
    for frame, ncell, mods, core, state in ARMY:
        st = "hi" if frame == sel else ("broken" if state == "broken" else "normal")
        FU.cell(sc, x0, y, x1, y + 86, st)
        g = F.build(frame, "broken" if state == "broken" else "idle", k=F.FRAMES[frame][0] * 0.48)
        if state == "broken":
            from swarm_effects import lit
            g = lit(g, (70, 70, 80), 0.45)
        sc.blit(g, int(x0 + 34 - g.ox), int(y + 78 - g.oy))
        letters(sc, frame, x0 + 66, y + 8, "text", 16, col=GOLD if st == "hi" else INK)
        for j in range(ncell):                                      # its cells: lit if a module is in
            cx_ = x0 + 68 + j * 12
            filled = j < len(mods)
            sc.rgb[y + 32:y + 42, cx_:cx_ + 9] = SU.OUTL
            sc.rgb[y + 33:y + 41, cx_ + 1:cx_ + 8] = hexc("#e0b860") if filled else hexc("#24222a")
        if state == "broken":
            H.fx_line(sc, x0 + 66, y + 52, "{поломка}")
        else:
            H.glyph(sc, "ядро", x0 + 66, y + 54, 1)
            letters(sc, MOD_NAME[core].split()[0].lower(), x0 + 84, y + 52, "text", 16, col=MUTED)
        y += 92
    FU.cell(sc, x0, y, x1, y + 44, "locked")
    letters(sc, "+ новый голем", (x0 + x1) / 2, y + 14, "text", 16, col=PALE, align="center")
    return y + 44


def workshop(variant=None):
    """The slipway: the golem on the workbench before its drawing, a callout from every mount to its part — the
    back, the arm, the barrel, the shoulder, the chest with the core; the chosen part hangs from the crane over its
    free mount. On the left the army on its rack; on the right the crate with what the battle brought, one of three."""
    import frames as F
    sc = screen(11)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, "МАСТЕРСКАЯ")
    metal(sc, 14)
    toolbar(sc)
    rack(sc, 10, 52, 168)
    # the slipway: the drawing, the gantry, the golem on its stand
    FU.plate(sc, 176, 52, 700, 462, seed=3)
    blueprint_sheet(sc, 186, 62, 690, 408, stamp=["КАРКАС: ОРУДИЕ", "стрелок · размер 5"], top=True)
    sc.rgb[70:78, 190:686] = hexc("#2a2830")                         # the gantry beam
    sc.rgb[70, 190:686] = hexc("#5a5860")
    sc.rgb[77, 190:686] = SU.OUTL
    for x in range(196, 686, 14):
        FU.rivet(sc, x, 74)
    frame, ncell, mods, core, _ = ARMY[2]
    K = 2.15                                                        # the slipway's frame scale, over the field's
    spr = golem_sprite(frame, mods, K)
    fx_, fy_ = 432, 388
    sc.rgb[fy_ + 2:fy_ + 14, fx_ - 80:fx_ + 80] = hexc("#24222a")    # the stand
    sc.rgb[fy_ + 2, fx_ - 80:fx_ + 80] = hexc("#6a6870")
    sc.rgb[fy_ + 13, fx_ - 80:fx_ + 80] = SU.OUTL
    sc.blit(spr, int(fx_ - spr.ox), int(fy_ - spr.oy))
    sk = K / 1.6                                                     # the mounts were measured at 1.6
    mp = {k: (fx_ + dx * sk, fy_ + dy * sk) for k, (lab, (dx, dy)) in MOUNT[frame].items()}
    labs = {k: lab for k, (lab, _) in MOUNT[frame].items()}
    # the boxes round the golem, a callout to each mount: the back, a free shoulder, the chest and its core on the
    # left; the arm and the barrel — where the new part goes — on the right
    for k_, by in (("mortar", 98), ("free", 182), ("core", 266)):
        if k_ == "core":
            FU.cell(sc, 198, by, 316, by + 46, "normal")
            letters(sc, "ГРУДЬ · ЯДРО", 206, by + 5, "title", 8, col=(150, 200, 230), outline=False)
            H.glyph(sc, "ядро", 206, by + 19, 2)
            letters(sc, "литое", 230, by + 18, "text", 16, col=INK)
            ex, ey = 316, by + 23
        else:
            ex, ey = part_box(sc, 198, by, None if k_ == "free" else k_, labs[k_], mods.get(k_, 1))
        callout(sc, mp[k_], (ex, ey), dash=k_ == "free")
    part_box(sc, 540, 222, "canister", labs["canister"], mods["canister"], w=140)
    callout(sc, mp["canister"], (540, 245))
    # the barrel's mount: the chosen part goes here — the box under the mouse, hot; the part on the crane above
    FU.cell(sc, 540, 300, 680, 346, "hover" if variant is None else "new")
    letters(sc, labs["long"].upper(), 548, 305, "title", 8, col=(150, 200, 230), outline=False)
    letters(sc, "Длинный ствол", 568, 318, "text", 16, col=(255, 210, 150))
    mod_icon(sc, "long", 548, 318)
    callout(sc, mp["long"], (540, 323), col=hexc("#ffb060"))
    hx = int(mp["long"][0])
    bottom = crane_hook(sc, hx, 70, 108, "long")
    sc.glow(mp["long"][0], mp["long"][1], 10, hexc("#ffb060"), 0.6)
    for k in range(bottom + 4, int(mp["long"][1]) - 8, 4):           # where it goes
        sc.rgb[k:k + 2, hx] = hexc("#ffb060")
    # under the drawing: the frame's own and the cells' count
    H.fx_line(sc, 190, 418, "Наводка: {дальность} → {урон} без потерь")
    for j in range(ncell):
        cx_ = 560 + j * 30
        FU.cell(sc, cx_, 412, cx_ + 24, 436, "hi" if j < len(mods) else ("new" if j == len(mods) else "locked"))
    letters(sc, "ячейки", 560, 440, "text", 16, col=MUTED)
    # the crate: what the battle brought
    FU.plate(sc, 708, 52, 948, 462, seed=4)
    heading(sc, "ДЕТАЛИ", 720, 64)
    H.fx_line(sc, 720, 86, "{выбор:1 из 3}", dim=True)
    for j, (key, kind, st, nm, who, lines) in enumerate(OFFERS):
        y0 = 112 + j * 114
        hov = False
        FU.cell(sc, 716, y0, 940, y0 + 106, "hi" if j == 0 else st)
        if j == 0:                                                 # it is on the hook: an empty nest in the straw
            FU.socket(sc, 724, y0 + 10, 776, y0 + 62)
            letters(sc, "на", 750, y0 + 20, "text", 16, col=BRASS, align="center")
            letters(sc, "крюке", 750, y0 + 38, "text", 16, col=BRASS, align="center")
        else:
            FU.cell(sc, 724, y0 + 10, 776, y0 + 62, "locked")
            mod_icon(sc, key, 734, y0 + 20, 2)
        sc.rgb[y0 + 12:y0 + 30, 786:930] = hexc("#d8c8a0")                      # the paper tag
        sc.rgb[y0 + 12, 786:930] = hexc("#f0e4c4")
        sc.rgb[y0 + 29, 786:930] = hexc("#8a7a5a")
        sc.rgb[y0 + 20:y0 + 22, 778:786] = hexc("#b8a880")                     # its string
        letters(sc, kind, 792, y0 + 13, "text", 16,
                col={"new": (40, 90, 130), "hi": (120, 80, 20), "rare": (100, 50, 150)}[st], outline=False, shadow=False)
        letters(sc, nm, 786, y0 + 36, "text", 16, col=GOLD if j == 0 else INK)
        letters(sc, who, 786, y0 + 54, "text", 16, col=PALE)
        H.fx_rows(sc, 724, y0 + 76, 210, lines)
    # leaving
    action(sc, 12, 478, 210, 526, "Автосборка", "steel")
    action(sc, 220, 478, 450, 526, "Починить всё · 2", "hot")
    action(sc, 460, 478, 690, 526, "Пропустить · +4", "steel")
    action(sc, 700, 472, 948, 532, "В БОЙ", "hot", big=True)
    FU.sparks(sc, 186, 400, 10, seed=5)
    name = "foundry_workshop.png"
    if variant is None:
        H.cursor(sc, 640, 330)
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


STEPS = ["КАРКАС", "ЯДРО", "МОДУЛИ", "ПУСК"]


def steps_bar(sc, cur, y=52):
    """The four steps of a new golem across the top: done in brass, the current one hot, the next ones dull."""
    x = 12
    for i, st in enumerate(STEPS):
        kind = "brass" if i < cur else ("hot" if i == cur else "dull")
        FU.button(sc, x, y, x + 214, y + 34, kind)
        letters(sc, f"{i + 1}. {st}", x + 107, y + 10, "text", 16, col=FU.BUTTON[kind][2], outline=kind == "dull",
                align="center")
        if i < len(STEPS) - 1:
            letters(sc, "»", x + 226, y + 9, "text", 16, col=MUTED, align="center")
        x += 238


def assembly(step=0):
    """A new golem, built from nothing: 1 — the frame (one of two, as drawings on blueprint paper: role, size, cells,
    its own rule, price); 2 — the core (three, glowing in their cradles, one goes into the chest); 3 — the modules,
    on the slipway (workshop()); 4 — the start: steam, sparks, and its passport — what it was built of."""
    import frames as F
    import golems_h as GH
    sc = screen(23 + step)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, "НОВЫЙ ГОЛЕМ")
    metal(sc, 22)
    toolbar(sc)
    steps_bar(sc, step)
    if step == 0:
        frames = [("Страж", "танк", 6, 5, "заслон: {радиус:1} → {цель:1}", 10, 6),
                  ("Горн", "контроль", 5, 4, "{каждые:1} → {огонь} {радиус:1}", 8, 5)]
        for i, (fr, role, size, cells, rule, price, lead) in enumerate(frames):
            x0 = 12 + i * 472
            x1 = x0 + 464
            sel = i == 1
            FU.cell(sc, x0, 96, x1, 462, "hi" if sel else "normal")
            blueprint_sheet(sc, x0 + 10, 106, x1 - 10, 330, stamp=[f"КАРКАС: {fr.upper()}", f"{role} · размер {size}"])
            g = drawn(F.build(fr, "idle", k=F.FRAMES[fr][0] * 1.25))
            sc.blit(g, int((x0 + x1) / 2 - 40 - g.ox), int(318 - g.oy))
            # its height as a dimension line
            top = 318 - int(g.oy) + int(np.nonzero(g.a.any(axis=1))[0][0])
            dx = x0 + 40
            sc.rgb[top:318, dx] = BLUE
            sc.rgb[top, dx - 4:dx + 5] = BLUE
            sc.rgb[317, dx - 4:dx + 5] = BLUE
            letters(sc, str(size), dx + 6, (top + 318) // 2 - 8, "text", 16, col=(170, 220, 250), outline=False)
            letters(sc, fr, x0 + 18, 340, "title", 16, col=GOLD if sel else INK)
            for j in range(cells):                                   # its empty cells, waiting
                FU.socket(sc, x0 + 18 + j * 34, 366, x0 + 46 + j * 34, 394)
            letters(sc, "ячеек " + str(cells), x0 + 30 + cells * 34, 372, "text", 16, col=MUTED)
            H.fx_line(sc, x0 + 18, 404, rule)
            H.fx_line(sc, x0 + 18, 432, f"{{металл:{price}}} · {{лидер:{lead}}}")
        action(sc, 12, 478, 300, 526, "Назад", "steel")
        action(sc, 660, 472, 948, 532, "ДАЛЕЕ: ЯДРО", "hot", big=True)
        name = "foundry_new_frame.png"
    elif step == 1:
        FU.plate(sc, 12, 96, 948, 462, seed=9)
        blueprint_sheet(sc, 22, 106, 420, 452, stamp=["КАРКАС: ГОРН", "ядро — в грудь"], top=True)
        g = F.build("Горн", "idle", k=F.FRAMES["Горн"][0] * 2.0)
        gx, gy = 200, 440
        sc.blit(g, int(gx - g.ox), int(gy - g.oy))
        rows_ = np.nonzero(g.a.any(axis=1))[0]
        cols_ = np.nonzero(g.a.any(axis=0))[0]
        top_, bot_ = gy - g.oy + rows_[0], gy - g.oy + rows_[-1]
        cx = int(gx - g.ox + (cols_[0] + cols_[-1]) / 2)
        cy = int(top_ + (bot_ - top_) * 0.52)                           # the chest, where the core goes
        cores = [("cast", "литое", "#c8c8d0", MOD_FX["cast"]), ("fire", "огненное", "#ff8a2a", MOD_FX["fire"]),
                 ("volt", "грозовое", "#8ad8ff", MOD_FX["volt"])]
        for j, (k_, nm, col, lines) in enumerate(cores):
            y0 = 112 + j * 114
            sel = k_ == "fire"
            FU.cell(sc, 436, y0, 940, y0 + 106, "hi" if sel else "normal")
            ox, oy = 490, y0 + 52                                     # the core in its cradle
            d = np.hypot(sc.xx - ox, sc.yy - oy)
            sc.rgb[(d < 26) & (d >= 22)] = hexc("#5a5860")
            sc.rgb[d < 22] = hexc("#14121a")
            sc.rgb[d < 16] = hexc(col) * 0.5
            sc.rgb[d < 11] = hexc(col)
            sc.rgb[d < 5] = hexc("#ffffff") * 0.6 + hexc(col) * 0.4
            sc.glow(ox, oy, 26, hexc(col), 0.5 if sel else 0.25)
            letters(sc, nm + " ядро", 530, y0 + 14, "text", 16, col=GOLD if sel else INK)
            H.fx_rows(sc, 530, y0 + 40, 400, lines)
            if sel:
                callout(sc, (cx, cy), (466, oy), col=hexc("#ff8a2a"))
        action(sc, 12, 478, 300, 526, "Назад", "steel")
        action(sc, 660, 472, 948, 532, "ДАЛЕЕ: МОДУЛИ", "hot", big=True)
        name = "foundry_new_core.png"
    else:
        FU.plate(sc, 12, 96, 948, 462, seed=10)
        g = F.build("Горн", "idle", k=F.FRAMES["Горн"][0] * 2.3)
        sc.rgb[440:452, 190:410] = hexc("#24222a")                   # the stand
        sc.rgb[440, 190:410] = hexc("#6a6870")
        sc.blit(g, int(300 - g.ox), int(442 - g.oy))
        FU.steam(sc, 270, 200, 18, seed=1)
        FU.steam(sc, 340, 190, 14, seed=2)
        FU.sparks(sc, 200, 440, 14, seed=3)
        FU.sparks(sc, 400, 440, 12, seed=4)
        letters(sc, "ГОРН ГОТОВ", 300, 116, "title", 24, col=(255, 200, 120), col2=(140, 60, 10), align="center")
        # its passport: what it was built of, step by step
        FU.cell(sc, 540, 116, 936, 450, "hi")
        heading(sc, "ПАСПОРТ", 556, 128)
        y = 160
        for lab, val in (("каркас", "Горн · контроль · размер 5"), ("ядро", "огненное"), ("ячейки", "4")):
            letters(sc, lab, 556, y, "text", 16, col=MUTED)
            letters(sc, val, 650, y, "text", 16, col=INK)
            y += 26
        H.fx_line(sc, 556, y + 4, "Жар горна: {каждые:1} → {огонь} {радиус:1}")
        y += 44
        letters(sc, "модули", 556, y, "text", 16, col=MUTED)
        for j, (k_, nm) in enumerate((("magnet", "Магнит"), ("maw", "Пасть топки"), (None, ""), (None, ""))):
            yy = y + 22 + j * 38
            if k_:
                FU.cell(sc, 556, yy, 590, yy + 34, "normal")
                mod_icon(sc, k_, 565, yy + 9)
                letters(sc, nm, 600, yy + 9, "text", 16, col=INK)
                FU.levels(sc, 880, yy + 14, 1)
            else:
                FU.socket(sc, 558, yy + 2, 588, yy + 32)
                letters(sc, "свободно", 600, yy + 9, "text", 16, col=PALE)
        action(sc, 12, 478, 300, 526, "Назад", "steel")
        action(sc, 660, 472, 948, 532, "В МАСТЕРСКУЮ", "hot", big=True)
        name = "foundry_new_start.png"
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


def new_golem():
    for st in (0, 1, 3):
        assembly(st)


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


SCREENS = {"workshop": workshop, "new": new_golem, "card": card, "leader": leaders_pick, "aftermath": aftermath, "battle": battle}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for k, fn in SCREENS.items():
        if arg in ("all", k):
            fn()
