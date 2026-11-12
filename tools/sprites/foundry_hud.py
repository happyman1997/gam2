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


def golem_sprite(frame, mods, k, body=None, core=None):
    """The golem assembled from its parts (golem_parts): hull, legs, arms, head, its modules; k — over its battle scale."""
    import golem_parts as GP
    import frames as F
    return GP.build(frame, k=F.FRAMES[frame][0] * k, mods=dict(mods), core=core, **(body or {}))


# what each body part does, in glyphs
PART_FX = {
    # legs
    "walk": ["{скорость:1}"],
    "heavy": ["{броня:+1} · {притяг:✕}", "ходит последним"],
    "spider": ["{размер:−2} → через", "{радиус:1} → отход {клетка:1}"],
    "tracks": ["{размер:−2} → сквозь · {урон} {дроб}"],
    "mill": ["{начало} → катится · {урон} {дроб}"],
    # arms
    "fist": ["{атака} {дроб} вплотную · слабый"],
    "maul": ["{атака} {дроб} вплотную · тяжёлый"],
    "shield": ["{атака} спереди → {урон:½}"],
    "cannon": ["{атака} {дроб} {дальность:3}"],
    "staff": ["{атака} {молния} {дальность:4}"],
    "focus": ["{молния} · заклинания → {дальность:+1}"],
    "flame": ["{атака} {огонь} {клетка:2}"],
    "tongs": ["{атака} → {захват}"],
    "wrench": ["{свой} {радиус:1} → {ремонт:2}"],
    "can": ["{инициатива} первым"],
    "spark": ["{атака} {броня} → {огонь} {радиус:1}"],
    "poker": ["{атака} → отброс в {огонь}"],
    "flail": ["{атака} → {клетка:2}"],
    # heads
    "helm": ["{броня:+1}"],
    "hood": ["заклинания → {дальность:+1}"],
    "stoker": ["{огонь:✕}"],
    "range": ["{дальность:+1}"],
    "lamp": ["{свой} {радиус:1} → {мимо:✕}"],
}
SLOTS = (("head", "голова"), ("arm_n", "правая рука"), ("arm_f", "левая рука"), ("legs", "ноги"))


def part_name(slot, key):
    import golem_parts as GP
    return {"legs": GP.LEGS, "head": {k: v[0] for k, v in GP.HEADS.items()}}.get(
        slot, {k: v[0] for k, v in GP.ARMS.items()})[key]


def part_icon(sc, slot, key, x, y, px=16, hull=None):
    """A body part's icon: the part itself, drawn alone (in the paint of the hull it is on, if given)."""
    import golem_parts as GP
    kind = "legs" if slot == "legs" else ("head" if slot == "head" else "arm")
    spr = GP.part_sprite(kind, key, px, hull=hull)
    sc.blit(spr, int(x), int(y))
    sc.occ[int(y):int(y) + spr.h, int(x):int(x) + spr.w] |= spr.a
    return spr.w


def body_points(frame, body):
    """Where each body part is on the golem: offsets from its foot at frame scale 1.6 (as the module mounts)."""
    import golem_parts as GP
    import frames as F
    S = GP.spec(frame, **body)
    pr = S["_parts"]
    _, info = GP.assemble(frame, **body)
    k = F.FRAMES[frame][0] * 1.6
    out = {}
    nk = GP.hull_neck(frame)
    out["head"] = F.to_screen(nk + np.array((1.2, 3.4, 0.0)), k)
    out["arm_n"] = F.to_screen(info["w_n"], k)
    out["arm_f"] = F.to_screen(info["w_f"], k)
    if pr["legs"] in ("tracks", "mill"):
        out["legs"] = F.to_screen(np.array((0.0, 5.0, 6.6)), k)
    else:
        out["legs"] = F.to_screen(info["legs"][0][1], k)
    return out, pr


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
BODY = {"Орудие": {"legs": "heavy"}}       # the army's golems that do not wear their stock parts
OFFERS = [   # (key, kind, cell state, its name, for whom, lines); a body part's key is (slot, part)
    ("long", "новый модуль", "new", "Длинный ствол", "Орудие", MOD_FX["long"]),
    (("head", "lamp"), "деталь тела", "hi", "Фонарь", "голова · любой", PART_FX["lamp"]),
    ("grapple", "редкий", "rare", "Крюк-кошка", "любой", MOD_FX["grapple"]),
]
# where each part sits on the frame: measured, not guessed — the frame is rendered with the module and without it,
# and the middle of what changed is the mount (offsets from the golem's foot, at frame scale 1.6); kept in
# assets/module_mounts.json, remade with «python3 foundry_hud.py mounts»
MOUNTS_FILE = None


def _mounts_path():
    import os
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "module_mounts.json")


def measure_mounts():
    import json
    import frame_modules as FM
    import guard_modules as GM
    res = {}
    for frame in ("Страж", "Мудрец", "Горн", "Орудие", "Механик"):
        keys = list(GM.MODULES) if frame == "Страж" else [k for k, *_ in FM.FRAMES[frame]]
        b = golem_sprite(frame, {}, 1.6)
        body = np.nonzero(b.a)
        res[frame] = {"_body": [int(body[1].min() - b.ox), int(body[1].max() - b.ox), int(body[0].min() - b.oy), 0]}
        for k in keys:
            try:
                a = golem_sprite(frame, {k: 1}, 1.6)
            except Exception as e:
                print("skip", frame, k, e)
                continue
            dx, dy = a.ox - b.ox, a.oy - b.oy
            pts = []
            ys, xs = np.nonzero(a.a)
            for y, x in zip(ys, xs):
                yb, xb = y - dy, x - dx
                if 0 <= yb < b.h and 0 <= xb < b.w and b.a[yb, xb] and np.abs(a.rgb[y, x] - b.rgb[yb, xb]).sum() < 30:
                    continue
                pts.append((x - a.ox, y - a.oy))
            if pts:
                p_ = np.array(pts)
                res[frame][k] = [int(np.median(p_[:, 0])), int(np.median(p_[:, 1]))]
        print(frame, res[frame])
    json.dump(res, open(_mounts_path(), "w"), ensure_ascii=False, indent=1)


def mounts():
    import json
    global MOUNTS_FILE
    if MOUNTS_FILE is None:
        MOUNTS_FILE = json.load(open(_mounts_path()))
    return MOUNTS_FILE


MOUNT_NAME = {   # where on the golem each module is mounted, by name
    "tower": "щит", "intercept": "плечо", "anchor": "ноги", "plates": "грудь", "counter": "щит", "hot": "броня",
    "tracks": "ноги", "flail": "рука",
    "chain": "плечо", "ground": "ноги", "overload": "спина", "fireball": "запястье", "firewall": "плечи", "blades": "плечо",
    "magnet": "грудь", "rod": "труба", "smoke": "труба", "whistle": "плечо", "maw": "топка", "greedy": "топка",
    "mortar": "спина", "long": "ствол", "spider": "ноги", "canister": "ствол", "hotshot": "спина", "bomb": "пояс",
    "repair": "запястье", "crane": "спина", "spares": "пояс", "oiler": "плечо", "welding": "спина", "oiltank": "спина",
}


def region(frame, p):
    """A mount's name, from where it sits on the body: head, shoulder, back, chest, arm, legs."""
    x0, x1, top, _ = mounts()[frame]["_body"]
    hgt = -top
    ry = -p[1] / hgt
    rx = p[0] / max(1, (x1 - x0) / 2)
    if ry > 0.86:
        return "голова"
    if ry > 0.62:
        return "спина" if rx < -0.2 else "плечо"
    if ry > 0.3:
        return "рука" if rx > 0.2 else ("спина" if rx < -0.3 else "грудь")
    return "ноги"


def free_spots(frame, used):
    """Where an empty cell is drawn: the body's regions nobody uses yet."""
    x0, x1, top, _ = mounts()[frame]["_body"]
    hgt = -top
    cand = [("плечо", (x0 * 0.35, -hgt * 0.74)), ("ноги", (0, -hgt * 0.16)), ("спина", (x0 * 0.6, -hgt * 0.5)),
            ("голова", (0, -hgt * 0.9)), ("рука", (x1 * 0.6, -hgt * 0.45))]
    taken = {region(frame, p) for p in used}
    return [c for c in cand if c[0] not in taken] + cand
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


def callout(sc, p, q, col=BLUE, dash=False, lane=None):
    """A leader line from a point on the golem to a part's box: a dot at the point, a dogleg to the box; the
    vertical run at its own lane, so the lines of one side don't lie on each other."""
    (px, py), (qx, qy) = p, q
    lx = px + (qx - px) * 0.5 if lane is None else lane
    pts = [(px, py), (lx, py), (lx, qy), (qx, qy)]
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


def part_box(sc, x, y, key, label, lv=1, state="normal", w=118, h=46):
    """A module's box at the end of a callout: the mount's name, the module's icon, its name, its level."""
    FU.cell(sc, x, y, x + w, y + h, state)
    letters(sc, label.upper(), x + 8, y + 4, "title", 8, col=(150, 200, 230), outline=False)
    if key:
        mod_icon(sc, key, x + 8, y + 18)
        H.HOVER.append(("@" + key, x + 8, y + 18, 16, 16))
        letters(sc, MOD_NAME[key], x + 30, y + 17, "text", 16, col=INK if state != "new" else (170, 220, 250))
        FU.levels(sc, x + w - 26, y + 6, lv)
    else:
        letters(sc, "свободно", x + 30, y + 17, "text", 16, col=PALE)
    return x + w, y + h // 2


def crane_hook(sc, x, y_top, y_hook, key, part=None):
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
    if part:                                                          # a body part: its own drawing on the hook
        import golem_parts as GP
        slot, pk = part
        spr = GP.part_sprite("legs" if slot == "legs" else ("head" if slot == "head" else "arm"), pk, 40)
    else:
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
        if state == "broken":
            g = F.build(frame, "broken", k=F.FRAMES[frame][0] * 0.48)
        else:
            g = golem_sprite(frame, mods, 0.48, body=BODY.get(frame))
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


ROLE = {"Страж": "танк · размер 6", "Мудрец": "маг · размер 5", "Горн": "контроль · размер 5",
        "Орудие": "стрелок · размер 5", "Механик": "поддержка · размер 4"}
SCALE = {"Страж": 1.55, "Механик": 2.5}          # how large each frame stands on a full-height drawing


def slipway(sc, frame, mods, core, ncell, rect, new_key=None, variant=None, role=None, broken=False,
            damaged=(), hover=None, crane=True, lw=150, rw=152, body=None, body_hot=None, body_new=None,
            body_only=False):
    """The drawing with the golem before it: the gantry beam, the hull's plate top left, the golem on its stand.
    On the left its body — a callout from the head, the right arm, the left arm and the legs to each part's box; on
    the right what is inside — the chest with its core and every module cell (measured mounts), empty cells dashed.
    Each line runs in its own lane. new_key — a module on the crane; body_new — (slot, key), a body part on the
    crane; body_hot — the body slot being chosen; damaged — modules that broke (red); hover — the box under the mouse.
    Returns where the hot part is (or the hovered box), for the cursor."""
    x0, y0, x1, y1 = rect
    body = dict(body or {})
    if body_new:
        body[body_new[0]] = body_new[1]
    blueprint_sheet(sc, x0, y0, x1, y1)
    sc.rgb[y0 + 8:y0 + 16, x0 + 4:x1 - 4] = hexc("#2a2830")         # the gantry beam
    sc.rgb[y0 + 8, x0 + 4:x1 - 4] = hexc("#5a5860")
    sc.rgb[y0 + 15, x0 + 4:x1 - 4] = SU.OUTL
    for x in range(x0 + 10, x1 - 4, 14):
        FU.rivet(sc, x, y0 + 12)
    K = SCALE.get(frame, 2.15) * (y1 - y0) / 346
    spr = golem_sprite(frame, {} if body_only else dict(mods), K, body=body)
    fx_ = x0 + 12 + lw + int((x1 - x0 - 24 - lw - rw) / 2)
    fy_ = y1 - 18
    sc.rgb[fy_ + 2:fy_ + 14, fx_ - 80:fx_ + 80] = hexc("#24222a")    # the stand
    sc.rgb[fy_ + 2, fx_ - 80:fx_ + 80] = hexc("#6a6870")
    sc.rgb[fy_ + 13, fx_ - 80:fx_ + 80] = SU.OUTL
    if broken:
        from swarm_effects import lit
        spr = lit(spr, (70, 70, 80), 0.45)
    sc.blit(spr, int(fx_ - spr.ox), int(fy_ - spr.oy))
    sk = K / 1.6
    M = mounts()[frame]
    at = lambda p: (fx_ + p[0] * sk, fy_ + p[1] * sk)
    BP, pr = body_points(frame, body)
    # the body: fixed order, top to bottom
    left = [(lab, at(BP[slot]), pr[slot], slot) for slot, lab in SLOTS]
    # inside: the core, the modules, the free cells
    right = []
    if not body_only:
        for k_, lv in mods.items():
            p = M.get(k_, [0, -60])
            right.append((MOUNT_NAME.get(k_, region(frame, p)), at(p), k_, lv, "broken" if k_ in damaged else "normal"))
        frees = free_spots(frame, [M.get(k_, [0, -60]) for k_ in mods])
        for j in range(ncell - len(mods)):
            lab, p = frees[j]
            if j == 0 and new_key:                                   # the free cell the part on the crane will take
                p = M.get(new_key, p)
                right.append((MOUNT_NAME.get(new_key, "ячейка"), at(p), new_key, 1, "incoming"))
            else:
                right.append(("ячейка", at(p), None, 0, "free"))
        right.sort(key=lambda t: t[1][1])
        top = M["_body"][2]
        if core:
            right.insert(0, ("грудь · ядро", at(((M["_body"][0] + M["_body"][1]) / 2 * 0.3, top * 0.55)), core, 0, "core"))
    FU.cell(sc, x0 + 8, y0 + 22, x0 + 214, y0 + 62, "normal")       # the hull's own plate on the drawing
    letters(sc, f"КОРПУС: {frame.upper()}", x0 + 18, y0 + 28, "title", 8, col=(150, 200, 230), outline=False)
    letters(sc, role or ROLE[frame], x0 + 18, y0 + 42, "text", 16, col=(170, 220, 250), outline=False)
    hot = None
    RED_ = hexc("#ff6a4a")
    HOTC = hexc("#ffb060")
    BH = 42
    # the body column
    n = len(left)
    for j, (lab, pt, key, slot) in enumerate(left):
        by = int(y0 + 72 + j * (y1 - y0 - 72 - 6 - BH) / (n - 1))
        bx, bw = x0 + 12, lw
        ex = bx + bw
        lane = ex + 10 + j * 7
        incoming = body_new and body_new[0] == slot
        st = "hover" if (incoming and variant is None) or slot == body_hot else ("new" if incoming else "normal")
        FU.cell(sc, bx, by, bx + bw, by + BH, st)
        letters(sc, lab.upper(), bx + 8, by + 4, "title", 8, col=(150, 200, 230), outline=False)
        part_icon(sc, slot, key, bx + 6, by + 18, hull=frame)
        letters(sc, part_name(slot, key), bx + 26, by + 18, "text", 16,
                col=(255, 210, 150) if incoming else INK)
        H.HOVER.append(("@" + key, bx + 6, by + 18, 16, 16))
        callout(sc, pt, (ex, by + BH // 2), col=HOTC if incoming or slot == body_hot else BLUE, lane=lane)
        if incoming or slot == body_hot:
            hot = (pt, bx + bw - 26, by + 28, bx, by, "l")
    # the inside column
    n = len(right)
    for j, (lab, pt, key, lv, st) in enumerate(right):
        by = int(y0 + 22 + j * (y1 - y0 - 22 - 6 - BH) / (n - 1)) if n > 1 else int(y0 + (y1 - y0) / 2)
        bw = rw
        bx = x1 - 10 - rw
        ex = bx
        lane = ex - 10 - j * 7
        if st == "core":
            FU.cell(sc, bx, by, bx + bw, by + BH, "normal")
            letters(sc, "ГРУДЬ · ЯДРО", bx + 8, by + 4, "title", 8, col=(150, 200, 230), outline=False)
            H.glyph(sc, "ядро", bx + 8, by + 18, 2)
            letters(sc, MOD_NAME[key].split()[0].lower(), bx + 32, by + 17, "text", 16, col=INK)
            callout(sc, pt, (ex, by + BH // 2), lane=lane)
        elif st == "incoming":
            FU.cell(sc, bx, by, bx + bw, by + BH, "hover" if variant is None else "new")
            letters(sc, lab.upper(), bx + 8, by + 4, "title", 8, col=(150, 200, 230), outline=False)
            mod_icon(sc, key, bx + 8, by + 18)
            letters(sc, MOD_NAME[key], bx + 28, by + 17, "text", 16, col=(255, 210, 150))
            callout(sc, pt, (ex, by + BH // 2), col=HOTC, lane=lane)
            hot = (pt, bx + bw - 30, by + 28)
        elif st == "broken":
            part_box(sc, bx, by, key, lab, lv, state="broken", w=bw, h=BH)
            callout(sc, pt, (ex, by + BH // 2), col=RED_, lane=lane)
            sc.glow(pt[0], pt[1], 8, RED_, 0.5)
        else:
            part_box(sc, bx, by, key, lab, lv, state="hover" if key and key == hover else "normal", w=bw, h=BH)
            callout(sc, pt, (ex, by + BH // 2), col=hexc("#ffe0a0") if key and key == hover else BLUE,
                    dash=st == "free", lane=lane)
            if key and key == hover:
                hot = (pt, bx + bw - 30, by + 28, bx, by, "r")
    if hot and crane and (new_key or body_new):                       # the crane: the part over its mount
        pt = hot[0]
        hx = min(int(pt[0]), x1 - 10 - rw - 30)                       # never over the boxes of the right column
        if body_new:
            bottom = crane_hook(sc, hx, y0 + 8, y0 + 30, None, part=body_new)
        else:
            bottom = crane_hook(sc, hx, y0 + 8, y0 + 38, new_key)
        sc.glow(pt[0], pt[1], 10, HOTC, 0.6)
        for k in range(bottom + 4, int(pt[1]) - 8, 4):
            sc.rgb[k:k + 2, hx] = HOTC
    return hot


def workshop(variant=None, frame="Орудие", new_key="long", name=None):
    """The slipway: the golem on the workbench before its drawing, a callout from every mount to its part — measured
    on the sprite, named by where it sits (back, shoulder, arm, chest, legs); empty cells dashed; the chest with its
    core. The chosen part hangs from the crane over the mount it takes. On the left the army on its rack; on the right
    the crate with what the battle brought, one of three."""
    import frames as F
    sc = screen(11)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, "МАСТЕРСКАЯ")
    metal(sc, 14)
    toolbar(sc)
    rack(sc, 10, 52, 168, sel=frame)
    _, ncell, mods, core, state = next(g for g in ARMY if g[0] == frame)
    role = ROLE[frame]
    FU.plate(sc, 176, 52, 700, 462, seed=3)
    hot = slipway(sc, frame, mods, core, ncell, (186, 62, 690, 408), new_key=new_key, variant=variant,
                  role=role, broken=state == "broken", body=BODY.get(frame))
    # under the drawing: the frame's own and its cells
    passive = {"Страж": "Заслон: {радиус:1} → {цель:1}", "Мудрец": "Питание: {свой} {радиус:1} → {через:−1}",
               "Горн": "Жар горна: {каждые:1} → {огонь} {радиус:1}", "Орудие": "Наводка: {дальность} → {урон} без потерь",
               "Механик": "Наладка: {каждые:1} → {свой} {радиус:1} {ремонт:1}"}[frame]
    H.fx_line(sc, 190, 418, passive)
    for j in range(ncell):
        cx_ = 690 - (ncell - j) * 30
        FU.cell(sc, cx_, 412, cx_ + 24, 436, "hi" if j < len(mods) else ("new" if (j == len(mods) and new_key) else "locked"))
    letters(sc, "ячейки", 690 - ncell * 30, 440, "text", 16, col=MUTED)
    # the crate: what the battle brought
    FU.plate(sc, 708, 52, 948, 462, seed=4)
    heading(sc, "ДЕТАЛИ", 720, 64)
    H.fx_line(sc, 720, 86, "{выбор:1 из 3}", dim=True)
    for j, (key, kind, st, nm, who, lines) in enumerate(OFFERS):
        y0 = 112 + j * 114
        on_hook = key == new_key
        FU.cell(sc, 716, y0, 940, y0 + 106, "hi" if on_hook else st)
        if on_hook:
            FU.socket(sc, 724, y0 + 10, 776, y0 + 62)
            letters(sc, "на", 750, y0 + 20, "text", 16, col=BRASS, align="center")
            letters(sc, "крюке", 750, y0 + 38, "text", 16, col=BRASS, align="center")
        else:
            FU.cell(sc, 724, y0 + 10, 776, y0 + 62, "locked")
            if isinstance(key, tuple):
                part_icon(sc, key[0], key[1], 734, y0 + 20, 32)
            else:
                mod_icon(sc, key, 734, y0 + 20, 2)
        sc.rgb[y0 + 12:y0 + 30, 786:930] = hexc("#d8c8a0")                      # the paper tag
        sc.rgb[y0 + 12, 786:930] = hexc("#f0e4c4")
        sc.rgb[y0 + 29, 786:930] = hexc("#8a7a5a")
        sc.rgb[y0 + 20:y0 + 22, 778:786] = hexc("#b8a880")
        letters(sc, kind, 792, y0 + 13, "text", 16,
                col={"new": (40, 90, 130), "hi": (120, 80, 20), "rare": (100, 50, 150)}[st], outline=False, shadow=False)
        letters(sc, nm, 786, y0 + 36, "text", 16, col=GOLD if on_hook else INK)
        letters(sc, who, 786, y0 + 54, "text", 16, col=PALE)
        H.fx_rows(sc, 724, y0 + 76, 210, lines)
    action(sc, 12, 478, 210, 526, "Автосборка", "steel")
    action(sc, 220, 478, 450, 526, "Починить всё · 2", "hot")
    action(sc, 460, 478, 690, 526, "Пропустить · +4", "steel")
    action(sc, 700, 472, 948, 532, "В БОЙ", "hot", big=True)
    FU.sparks(sc, 186, 400, 10, seed=5)
    if variant is None and hot:
        H.cursor(sc, hot[1], hot[2])
    name = name or "foundry_workshop.png"
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


def slipways():
    """The slipway for each frame of the army, to see the mounts measured right; and a sheet of the four."""
    from PIL import Image
    files = []
    for fr in ("Страж", "Мудрец", "Механик"):
        n = f"foundry_slipway_{fr}.png"
        workshop("plain", fr, None, n)
        files.append(n)
    files.append("foundry_workshop.png")
    sheet = Image.new("RGB", (2 * 1048, 2 * 712), (20, 18, 22))
    for i, n in enumerate(files):
        im = Image.open(out(n)).crop((352, 104, 1400, 816))
        sheet.paste(im, ((i % 2) * 1048, (i // 2) * 712))
    sheet = sheet.resize((1048, 712))
    sheet.save(out("foundry_slipways.png"))
    print("foundry_slipways.png", sheet.size)


STEPS = ["КОРПУС", "ТЕЛО", "ЯДРО", "МОДУЛИ", "ПУСК"]
NEW_BODY = {"legs": "heavy", "arm_f": "shield"}       # the new Furnace in the example: shield and outriggers


def steps_bar(sc, cur, y=52):
    """The five steps of a new golem across the top: done in brass, the current one hot, the next ones dull."""
    x = 12
    w = 168
    for i, st in enumerate(STEPS):
        kind = "brass" if i < cur else ("hot" if i == cur else "dull")
        FU.button(sc, x, y, x + w, y + 34, kind)
        letters(sc, f"{i + 1}. {st}", x + w // 2, y + 10, "text", 16, col=FU.BUTTON[kind][2], outline=kind == "dull",
                align="center")
        if i < len(STEPS) - 1:
            letters(sc, "»", x + w + 10, y + 9, "text", 16, col=MUTED, align="center")
        x += w + 23


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
            blueprint_sheet(sc, x0 + 10, 106, x1 - 10, 330, stamp=[f"КОРПУС: {fr.upper()}", f"{role} · размер {size}"])
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
        action(sc, 660, 472, 948, 532, "ДАЛЕЕ: ТЕЛО", "hot", big=True)
        name = "foundry_new_frame.png"
    elif step == 1:
        # the body: the hull on the slipway with its stock parts; a slot chosen on the left, the rack of parts on the right
        FU.plate(sc, 12, 96, 566, 462, seed=12)
        hot = slipway(sc, "Горн", {}, None, 4, (22, 106, 556, 452), body=NEW_BODY, body_hot="arm_f", body_only=True,
                      crane=False, rw=20, role="контроль · размер 5")
        FU.plate(sc, 574, 96, 948, 462, seed=13)
        heading(sc, "СТОЙКА", 588, 108)
        letters(sc, "левая рука", 940, 116, "text", 16, col=GOLD, align="right")
        rows = [("tongs", "штатная", "normal"), ("shield", "на стойке · 1", "hi"), ("cannon", "на стойке · 1", "normal"),
                ("fist", "запасная", "normal")]
        for j, (k_, tag, st) in enumerate(rows):
            y0 = 138 + j * 72
            FU.cell(sc, 584, y0, 940, y0 + 66, st)
            FU.cell(sc, 592, y0 + 7, 644, y0 + 59, "locked")
            part_icon(sc, "arm_f", k_, 602, y0 + 17, 32, hull="Горн")
            letters(sc, part_name("arm_f", k_), 656, y0 + 7, "text", 16, col=GOLD if st == "hi" else INK)
            letters(sc, tag, 932, y0 + 7, "text", 16, col=BRASS if "стойке" in tag else PALE, align="right")
            H.fx_rows(sc, 656, y0 + 33, 270, PART_FX[k_])
        H.fx_line(sc, 588, 430, "{лкм} гнездо слева → деталь справа", dim=True)
        if hot:
            H.cursor(sc, 900, 138 + 72 + 40)
        action(sc, 12, 478, 300, 526, "Назад", "steel")
        action(sc, 660, 472, 948, 532, "ДАЛЕЕ: ЯДРО", "hot", big=True)
        name = "foundry_new_body.png"
    elif step == 2:
        FU.plate(sc, 12, 96, 948, 462, seed=9)
        blueprint_sheet(sc, 22, 106, 420, 452, stamp=["КОРПУС: ГОРН", "ядро — в грудь"], top=True)
        g = golem_sprite("Горн", {}, 2.0, body=NEW_BODY)
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
        g = golem_sprite("Горн", {"magnet": 1, "maw": 1}, 2.3, body=NEW_BODY, core="fire")
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
        y = 158
        for lab, val in (("корпус", "Горн · контроль · размер 5"), ("ядро", "огненное")):
            letters(sc, lab, 556, y, "text", 16, col=MUTED)
            letters(sc, val, 650, y, "text", 16, col=INK)
            y += 24
        H.fx_line(sc, 556, y + 2, "Жар горна: {каждые:1} → {огонь} {радиус:1}")
        y += 34
        letters(sc, "тело", 556, y, "text", 16, col=MUTED)
        body = dict({"legs": "walk", "arm_n": "flame", "arm_f": "tongs", "head": "stoker"}, **NEW_BODY)
        for j, (slot, _) in enumerate(SLOTS):
            cx_ = 650 + (j % 2) * 140
            cy_ = y + (j // 2) * 24
            part_icon(sc, slot, body[slot], cx_, cy_, hull="Горн")
            letters(sc, part_name(slot, body[slot]), cx_ + 20, cy_, "text", 16, col=INK)
        y += 52
        letters(sc, "модули", 556, y, "text", 16, col=MUTED)
        for j, (k_, nm) in enumerate((("magnet", "Магнит"), ("maw", "Пасть топки"), (None, ""), (None, ""))):
            yy = y + 20 + j * 30
            if k_:
                FU.cell(sc, 556, yy, 584, yy + 28, "normal")
                mod_icon(sc, k_, 562, yy + 6)
                letters(sc, nm, 596, yy + 6, "text", 16, col=INK)
                FU.levels(sc, 880, yy + 11, 1)
            else:
                FU.socket(sc, 558, yy + 2, 582, yy + 26)
                letters(sc, "свободно", 596, yy + 6, "text", 16, col=PALE)
        action(sc, 12, 478, 300, 526, "Назад", "steel")
        action(sc, 660, 472, 948, 532, "В МАСТЕРСКУЮ", "hot", big=True)
        name = "foundry_new_start.png"
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


def new_golem():
    for st in (0, 1, 2, 4):
        assembly(st)


# ---------------------------------------------------------------- the golem's card, as big as the screen
ABIL = {   # the frame's and the class's own, in glyphs
    "Наводка": ["{дальность} → 2–3 ряд", "{дальность} → {урон} без потерь"],
    "Огнеупорность": ["{огонь} ×¼ · гаснет за ход"],
    "Литой металл": ["{кол} ×½ · {дроб} ×1 · {кисл} ×2"],
    "Бесстрашие": ["{страх:✕} · {яд:✕}"],
    "Проводник": ["{молния} ×1,5"],
}


def card(frame="Орудие", hover="mortar"):
    """A golem's card, in the slipway's language: on the left its drawing, a callout from every mount to its module
    (the one under the mouse opened in a tooltip), the chest with its core, its own rule and its cells under it; on
    the right its passport — leadership, core, last battle; body; blow; what its class can and can't."""
    sc = screen(13)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, frame.upper(), "стрелок · голем")
    toolbar(sc)
    mods = {"mortar": 1, "canister": 1, "long": 1}
    ncell, core = 4, "cast"
    # left: the drawing
    FU.plate(sc, 6, 50, 590, 532, seed=7)
    hot = slipway(sc, frame, mods, core, ncell, (16, 60, 580, 452), hover=hover, crane=False, body=BODY.get(frame))
    H.fx_line(sc, 20, 466, "Наводка: {дальность} → {урон} без потерь")
    for j in range(ncell):
        cx_ = 580 - (ncell - j) * 30
        FU.cell(sc, cx_, 460, cx_ + 24, 484, "hi" if j < len(mods) else "locked")
    letters(sc, "ячейки", 580 - ncell * 30, 490, "text", 16, col=MUTED)
    # right: the passport
    x0, x1 = 612, WW - 18
    FU.plate(sc, 598, 50, WW - 6, 466, seed=8)
    heading(sc, "ПАСПОРТ", x0, 62)
    H.fx_line(sc, x0, 90, "{лидер:5} · {ядро} литое · {убийство:3} в прошлом бою")
    y = 124
    heading(sc, "ТЕЛО", x0, y)
    y += 28
    for key, val in (("здоровье", "55"), ("броня", "2 {литой}"), ("скорость", "1"), ("размер", "5"), ("инициатива", "4")):
        a_ = H.glyph(sc, key, x0, y - 4, 2)
        w, _ = H.fx_line(sc, 0, 0, val, draw=False)
        H.dots(sc, x0 + a_ + 8, x1 - w - 6, y + 10)
        H.fx_line(sc, x1 - w, y - 2, val)
        y += 18
    y += 4
    heading(sc, "ВОЗМОЖНОСТИ", x0, y)
    y += 28
    cols = (x0 + 20, x0 + 116, x0 + 200, x0 + 262)
    for cx, lab in zip(cols, ("атака", "урон", None, "дальность")):
        if lab:
            H.glyph(sc, lab, cx, y - 6, 2)
    y += 14
    sc.rgb[y, x0:x1] = sc.rgb[y, x0:x1] * 0.5 + hexc("#5a5860") * 0.5
    for slot in ("arm_n", "arm_f"):                                  # a row per arm: what each hand strikes with
        part_icon(sc, slot, "cannon", x0, y + 5, hull=frame)
        letters(sc, part_name(slot, "cannon"), cols[0], y + 6, "text", 16, col=GOLD)
        letters(sc, "1–10 +3", cols[1], y + 6, "text", 16, col=INK)
        H.fx_line(sc, cols[2], y + 6, "{дроб}")
        letters(sc, "3", cols[3], y + 6, "text", 16, col=INK)
        y += 22
    y += 6
    heading(sc, "СПОСОБНОСТИ", x0, y)
    y += 26
    for key, nm, lab, col in (("огонь", "Огнеупорность", "класс", (214, 196, 150)),
                              ("литой", "Литой металл", "класс", (214, 196, 150)),
                              ("дух", "Бесстрашие", "класс", (214, 196, 150)),
                              ("молния", "Проводник", "слабость", RED)):
        H.glyph(sc, key, x0 + 2, y - 3, 2)
        letters(sc, nm, x0 + 30, y, "text", 16, col=col)
        letters(sc, lab, x1, y, "text", 16, col=MUTED, align="right")
        y += 24
    action(sc, 598, 478, WW - 6, 528, "Закрыть", "steel")
    # the module under the mouse: its tooltip under its box
    if hot:
        pt, cx, cy, bx, by, side = hot
        lines = MOD_FX[hover]
        tw = 300
        th = H.fx_rows(sc, 0, 0, tw - 24, lines, draw=False) + 40
        tx = bx if side == "l" else bx + 152 - tw
        FU.cell(sc, tx, by + 52, tx + tw, by + 52 + th, "normal")
        letters(sc, MOD_NAME[hover], tx + 12, by + 60, "text", 16, col=GOLD)
        FU.levels(sc, tx + tw - 30, by + 62, mods[hover])
        H.fx_rows(sc, tx + 12, by + 84, tw - 24, lines)
        H.cursor(sc, cx, cy)
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
def damage_drawing(sc, frame, mods, key, x, y, K):
    """The golem as a drawing on the blueprint, the part that broke picked out in red — its own pixels, found as
    what changes when the frame is drawn without it. Returns the part's mount, for the callout."""
    full = golem_sprite(frame, mods, K)
    bare = golem_sprite(frame, {k: v for k, v in mods.items() if k != key}, K)
    d = drawn(full)
    dx, dy = full.ox - bare.ox, full.oy - bare.oy
    ys, xs = np.nonzero(full.a)
    red = hexc("#ff6a4a")
    for yy, xx in zip(ys, xs):
        yb, xb = int(yy - dy), int(xx - dx)
        if 0 <= yb < bare.h and 0 <= xb < bare.w and bare.a[yb, xb] and np.abs(full.rgb[yy, xx] - bare.rgb[yb, xb]).sum() < 30:
            continue
        d.rgb[yy, xx] = red if d.rgb[yy, xx].sum() > hexc("#1e3a5a").sum() + 30 else red * 0.45 + hexc("#1e3a5a") * 0.55
    sc.rgb[y + 2:y + 6, x - 60:x + 60] = BLUE * 0.6                 # the ground line of the drawing
    sc.blit(d, int(x - d.ox), int(y - d.oy))
    p = mounts()[frame][key]
    sk = K / 1.6
    pt = (x + p[0] * sk, y + p[1] * sk)
    sc.glow(pt[0], pt[1], 12, red, 0.5)
    return pt


def stamp(sc, x, y, text, col="#e0503a"):
    """A rubber stamp on the drawing: red letters in a double red frame, a little worn."""
    w = SU.text_width(text, "title", 8) + 16
    c = hexc(col)
    for k in (0, 2):
        sc.rgb[y + k, x + k:x + w - k] = c
        sc.rgb[y + 21 - k, x + k:x + w - k] = c
        sc.rgb[y + k:y + 22 - k, x + k] = c
        sc.rgb[y + k:y + 22 - k, x + w - 1 - k] = c
    letters(sc, text, x + 8, y + 7, "title", 8, col=tuple(int(v) for v in c), outline=False, shadow=False)
    rng = np.random.default_rng(len(text))
    for _ in range(18):                                               # worn spots
        sx, sy = x + rng.integers(0, w), y + rng.integers(0, 22)
        sc.rgb[sy, sx] = hexc("#14243a")


def aftermath():
    """Victory: what broke and what it cost, what the battle paid, who did what."""
    import frames as F
    from swarm_effects import lit
    sc = screen(19)
    FU.wing(sc, 0, 0, WW, 44)
    title(sc, "ПОБЕДА")
    metal(sc, 20)
    toolbar(sc)
    # broken: the damage report — the golem as a drawing, the part that broke in red, a red callout to it
    FU.plate(sc, 12, 52, 330, 462, seed=31)
    heading(sc, "ПОЛОМКИ", 26, 64)
    blueprint_sheet(sc, 22, 90, 320, 304)
    FU.cell(sc, 30, 98, 178, 134, "normal")
    letters(sc, "КОРПУС: МУДРЕЦ", 38, 103, "title", 8, col=(150, 200, 230), outline=False)
    letters(sc, ROLE["Мудрец"], 38, 116, "text", 16, col=(170, 220, 250), outline=False)
    pt = damage_drawing(sc, "Мудрец", {"chain": 1, "fireball": 1, "overload": 2}, "overload", 236, 292, 2.4)
    stamp(sc, 32, 268, "В РЕМОНТ")
    lane = 160
    callout(sc, pt, (lane, 314), col=hexc("#ff6a4a"), lane=lane)
    FU.cell(sc, 22, 314, 320, 378, "broken")
    letters(sc, "СПИНА", 32, 319, "title", 8, col=(230, 150, 130), outline=False)
    mod_icon(sc, "overload", 32, 334, 2)
    letters(sc, "Перегрузка", 74, 332, "text", 16, col=INK)
    H.fx_line(sc, 74, 352, "{модуль:II} ⇒ {модуль:I}")
    H.fx_line(sc, 26, 394, "{ремонт} → {металл:2}")
    H.fx_line(sc, 26, 424, "не починил → пропускает бой", dim=True)
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


SCREENS = {"workshop": workshop, "slipways": slipways, "new": new_golem, "card": card, "leader": leaders_pick, "aftermath": aftermath, "battle": battle}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "mounts":
        measure_mounts()
        sys.exit()
    for k, fn in SCREENS.items():
        if arg in ("all", k):
            fn()
