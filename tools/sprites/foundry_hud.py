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


def title_center(sc, text, tool="wrench", glint=None, turn=0.0):
    """A screen's name in the middle of the beam, a big tool either side of it turned to it: spanners for the
    workshop, smith's hammers for a new golem, tongs with a hot bar for smelting, brass cogs for a victory."""
    tw = SU.text_width(text, "title", 24)
    x = WW // 2 - tw // 2
    letters(sc, text, x, 6, "title", 24, col=(232, 222, 206), col2=(120, 96, 70), jitter=0)
    for k in range(0, tw, 3):
        sc.rgb[31, x + k] = sc.rgb[31, x + k] * 0.4 + hexc("#ff8a3a") * 0.6
    L = int(min(156, 286 - tw // 2, WW // 2 - tw // 2 - 14 - 128))
    if tool == "wrench":
        ml = FU.wrench(sc, x - 14 - L, x - 14, 21, flip=False, size="24", seed=1)
        mr = FU.wrench(sc, x + tw + 14, x + tw + 14 + L, 21, flip=True, size="19", seed=2)
        if glint is not None and 0 <= glint <= 1:                      # a glint running out along both spanners
            for m_, gx in ((ml, x - 14 - glint * L), (mr, x + tw + 14 + glint * L)):
                band = m_ & (np.abs(sc.xx - gx + (sc.yy - 21) * 0.6) < 1.6)
                sc.rgb[band] = sc.rgb[band] * 0.3 + np.array((255.0, 250.0, 236.0)) * 0.7
    elif tool == "lantern":                                            # the camp: lanterns hung either side
        for side, base_x in ((-1, x - 30), (1, x + tw + 30)):
            FU.lantern(sc, base_x, 0, 24, size=1.15, lit=1.0 if glint is None else glint)
            FU.lantern(sc, base_x + side * 64, 0, 20, size=0.85, lit=0.85 if glint is None else glint * 0.9)
    elif tool == "hammer":
        L = min(L, 112)
        FU.hammer(sc, x - 12 - L, x - 12, 21, flip=False, seed=1)
        FU.hammer(sc, x + tw + 12, x + tw + 12 + L, 21, flip=True, seed=2)
    elif tool == "calipers":
        L = min(L, 140)
        FU.calipers(sc, x - 16 - L, x - 16, 19, flip=False, seed=1)
        FU.calipers(sc, x + tw + 16, x + tw + 16 + L, 19, flip=True, seed=2)
    elif tool == "anvils":
        FU.anvil(sc, x - 44, 40, flip=False)
        FU.anvil(sc, x + tw + 44, 40, flip=True)
    elif tool == "tongs":
        L = min(L, 132)
        FU.tongs(sc, x - 24 - L, x - 24, 21, flip=False, seed=1)
        FU.tongs(sc, x + tw + 24, x + tw + 24 + L, 21, flip=True, seed=2)
    else:
        FU.gears(sc, x - 12 - 80, x - 12, 21, flip=False, seed=0.0, turn=turn)
        FU.gears(sc, x + tw + 12, x + tw + 12 + 80, 21, flip=True, seed=0.3, turn=turn)


def toolbar(sc, alt=False, on=False):
    """The right end of the beam, the same on every screen: Alt, two sockets kept for buttons to come, «?» (F1)."""
    H.keycap(sc, 790, 14, "Alt", lit=alt)
    for sx in (832, 872):
        FU.socket(sc, sx, 10, sx + 32, 34)
    FU.cap_button(sc, 930, 19, 11, "?", "brass" if on else "steel")
    H.keycap(sc, 912, 30, "F1")


def metal(sc, n, x=700):
    """The Foundry's purse, on the beam: ingots and a number."""
    H.glyph(sc, "металл", x, 10, 2)
    letters(sc, str(n), x + 30, 12, "title", 16, col=(214, 220, 236), col2=(90, 96, 120))


def action(sc, x0, y0, x1, y1, text, kind="hot", heated=False, big=False, anim=None):
    """A control on the console at the foot of the screen. The screen's own action (big): a throttle lever beside a
    cast nameplate. The rest: a push-button in a hex nut with its stamped tag on a wire; repairing: a valve's
    handwheel. heated — the mouse on it: the lever thrown, the button pressed, the wheel turning. anim — a frame of
    a click: press (0..1, below 0 springing back), angle (the lever), turn (the wheel), swing (the tag), glow (the
    nameplate's enamel)."""
    a = anim or {}
    yc = (y0 + y1) // 2
    if big:
        FU.lever(sc, x0 + 18, y0 - 4, y1 + 2, pulled=heated, angle=a.get("angle"))
        FU.nameplate(sc, x0 + 44, y0 + 3, x1, y1 - 3, text, hot=kind == "hot", heated=heated, glow=a.get("glow"))
        return
    r = 13
    bx = x0 + r + 9
    if text.startswith("Починить"):
        FU.valve(sc, bx, yc, r + 2, turning=heated, turn=a.get("turn"))
        tk = "brass"
    else:
        cap = {"rust": "rust", "dull": "dull", "brass": "brass"}.get(kind, "steel")
        FU.pushbutton(sc, bx, yc, r, kind=cap, pressed=heated, press=a.get("press"))
        tk = {"rust": "rust", "dull": "dull", "brass": "brass"}.get(kind, "steel")
    tx0 = bx + r + 12
    tw = SU.text_width(text, "text", 16)
    FU.tag(sc, tx0, yc - 13, min(x1, int(tx0 + 13 * 1.6 + 6 + tw + 9)), yc + 13, text, tk, wire_to=bx + r + 6,
           dy=a.get("swing", 0))


def heading(sc, text, x, y):
    return letters(sc, text, x, y, "title", 16, col=GOLD, col2=(130, 90, 40))


_GOLEMS = {}


def golem_sprite(frame, mods, k, body=None, core=None):
    """The golem assembled from its parts (golem_parts): hull, legs, arms, head, its modules; k — over its battle
    scale. Kept once drawn, so the frames of an animation don't draw it again."""
    import golem_parts as GP
    import frames as F
    key = (frame, tuple(sorted(dict(mods).items())), round(k, 4), tuple(sorted((body or {}).items())), core)
    if key not in _GOLEMS:
        _GOLEMS[key] = GP.build(frame, k=F.FRAMES[frame][0] * k, mods=dict(mods), core=core, **(body or {}))
    return _GOLEMS[key]


# what each body part does, in glyphs
PART_FX = {
    # legs
    "walk": ["{скорость:1}"],
    "heavy": ["{броня:+1} · {притяг:✕}", "ходит последним"],
    "spider": ["{размер:−2} → через", "{радиус:1} → отход {клетка:1}"],
    "tracks": ["{размер:−2} → сквозь · {урон} {дроб}"],
    "mill": ["{начало} → катится · {урон} {дроб}"],
    # arms
    "fist": ["{атака} {дроб} · слабый"],
    "maul": ["{атака} {дроб} · тяжёлый"],
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


def slot_label(sc, text, x, y, col=(150, 200, 230)):
    """A box's label (the mount, the slot) — 16 px like all text that means something, first letter up."""
    t = text[:1].upper() + text[1:]
    letters(sc, t, x, y, "text", 16, col=col, outline=False)


def part_box(sc, x, y, key, label, lv=1, state="normal", w=118, h=46):
    """A module's box at the end of a callout: the mount's name, the module's icon, its name, its level."""
    FU.cell(sc, x, y, x + w, y + h, state)
    slot_label(sc, label, x + 8, y + 2)
    if key:
        mod_icon(sc, key, x + 8, y + 22)
        H.HOVER.append(("@" + key, x + 8, y + 22, 16, 16))
        letters(sc, MOD_NAME[key], x + 30, y + 21, "text", 16, col=INK if state != "new" else (170, 220, 250))
        FU.levels(sc, x + w - 26, y + 6, lv)
    else:
        letters(sc, "свободно", x + 30, y + 21, "text", 16, col=PALE)
    return x + w, y + h // 2


def crane_hook(sc, x, y_top, y_hook, key, part=None, sway=0, carry=True):
    """The gantry's trolley, its chain down, the hook, and the part hanging from it; sway — how far the hook has
    swung aside (the chain slants to it); carry=False — the hook going back up empty."""
    sc.rgb[y_top:y_top + 8, x - 16:x + 17] = hexc("#3a3840")
    sc.rgb[y_top, x - 16:x + 17] = hexc("#6a6870")
    sc.rgb[y_top + 7, x - 16:x + 17] = SU.OUTL
    FU.rivet(sc, x - 10, y_top + 4)
    FU.rivet(sc, x + 10, y_top + 4)
    y_hook = int(y_hook)
    if abs(sway) < 0.5:
        FU.chain(sc, x, y_top + 8, y_hook)
    else:                                                             # link by link along the slant
        for k_, yy in enumerate(range(y_top + 8, y_hook, 5)):
            xx = int(round(x + sway * (yy - y_top - 8) / max(1, y_hook - y_top - 8)))
            FU.chain(sc, xx, yy, yy + 5) if k_ % 2 == 0 else FU.chain(sc, xx, yy - 5, yy + 5)
    x = int(round(x + sway))
    for k in range(6):                                                # the hook
        sc.rgb[y_hook + k, x - 1:x + 2] = hexc("#8a8890")
    sc.rgb[y_hook + 5:y_hook + 8, x - 4:x + 2] = hexc("#8a8890")
    sc.rgb[y_hook + 3:y_hook + 6, x - 5] = hexc("#8a8890")
    if not carry:
        return y_hook + 8
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
            FU.core_port(sc, x0 + 74, y + 62, core)                     # its core, by colour, no word
            H.HOVER.append(("ядро", x0 + 66, y + 54, 16, 16))
        y += 92
    FU.cell(sc, x0, y, x1, y + 44, "locked")
    letters(sc, "+ новый голем", (x0 + x1) / 2, y + 14, "text", 16, col=PALE, align="center")
    return y + 44


ROLE = {"Страж": "танк · размер 6", "Мудрец": "маг · размер 5", "Горн": "контроль · размер 5",
        "Орудие": "стрелок · размер 5", "Механик": "поддержка · размер 4"}
SCALE = {"Страж": 1.55, "Механик": 2.5}          # how large each frame stands on a full-height drawing


def slipway(sc, frame, mods, core, ncell, rect, new_key=None, variant=None, role=None, broken=False,
            damaged=(), hover=None, crane=True, lw=150, rw=152, body=None, body_hot=None, body_new=None,
            body_only=False, anim=None, scale=1.0, extra=()):
    """The drawing with the golem before it: the gantry beam, the hull's plate top left, the golem on its stand.
    On the left its body — a callout from the head, the right arm, the left arm and the legs to each part's box; on
    the right what is inside — the chest with its core and every module cell (measured mounts), empty cells dashed.
    Each line runs in its own lane. new_key — a module on the crane; body_new — (slot, key), a body part on the
    crane; body_hot — the body slot being chosen; damaged — modules that broke (red); hover — the box under the mouse.
    Returns where the hot part is (or the hovered box), for the cursor."""
    x0, y0, x1, y1 = rect
    a_ = anim or {}
    inst = a_.get("installed")                                        # a module just set in by the crane
    if inst:
        mods = dict(mods)
        mods[inst] = 1
        new_key = None
    body = dict(body or {})
    if body_new:
        body[body_new[0]] = body_new[1]
    blueprint_sheet(sc, x0, y0, x1, y1)
    sc.rgb[y0 + 8:y0 + 16, x0 + 4:x1 - 4] = hexc("#2a2830")         # the gantry beam
    sc.rgb[y0 + 8, x0 + 4:x1 - 4] = hexc("#5a5860")
    sc.rgb[y0 + 15, x0 + 4:x1 - 4] = SU.OUTL
    for x in range(x0 + 10, x1 - 4, 14):
        FU.rivet(sc, x, y0 + 12)
    K = SCALE.get(frame, 2.15) * (y1 - y0) / 346 * scale
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
        for lab_, where, key_, st_ in extra:                          # an augment's cell, a module off another hull
            p_ = BP[where] if isinstance(where, str) else where
            right.append((lab_, at(p_), key_, 1, st_))
        right.sort(key=lambda t: t[1][1])
        top = M["_body"][2]
        if core:
            right.insert(0, ("грудь · ядро", at(((M["_body"][0] + M["_body"][1]) / 2 * 0.3, top * 0.55)), core, 0, "core"))
    FU.cell(sc, x0 + 8, y0 + 22, x0 + 214, y0 + 62, "normal")       # the hull's own plate on the drawing
    slot_label(sc, f"корпус: {frame}", x0 + 18, y0 + 23)
    letters(sc, role or ROLE[frame], x0 + 18, y0 + 41, "text", 16, col=(170, 220, 250), outline=False)
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
        slot_label(sc, lab, bx + 8, by + 2)
        part_icon(sc, slot, key, bx + 6, by + 22, hull=frame)
        letters(sc, part_name(slot, key), bx + 26, by + 21, "text", 16,
                col=(255, 210, 150) if incoming else INK)
        H.HOVER.append(("@" + key, bx + 6, by + 22, 16, 16))
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
            slot_label(sc, "грудь · ядро", bx + 8, by + 2)
            FU.core_port(sc, bx + 16, by + 30, key)
            H.HOVER.append(("ядро", bx + 8, by + 22, 16, 16))
            letters(sc, MOD_NAME[key], bx + 30, by + 21, "text", 16, col=INK)
            callout(sc, pt, (ex, by + BH // 2), lane=lane)
        elif st == "incoming" and variant == "drag":                  # dragged: the free cell waits for it, lit
            FU.cell(sc, bx, by, bx + bw, by + BH, "new")
            slot_label(sc, lab, bx + 8, by + 2)
            letters(sc, "сюда", bx + bw // 2, by + 21, "text", 16, col=(170, 220, 250), align="center")
            callout(sc, pt, (ex, by + BH // 2), col=hexc("#9ad8ff"), lane=lane, dash=True)
            sc.glow(pt[0], pt[1], 9, hexc("#9ad8ff"), 0.6)
            hot = (pt, bx + bw - 30, by + 28, bx, by, "r")
        elif st == "incoming":
            FU.cell(sc, bx, by, bx + bw, by + BH, "hover" if variant is None else "new")
            slot_label(sc, lab, bx + 8, by + 2)
            mod_icon(sc, key, bx + 8, by + 22)
            letters(sc, MOD_NAME[key], bx + 28, by + 21, "text", 16, col=(255, 210, 150))
            callout(sc, pt, (ex, by + BH // 2), col=HOTC, lane=lane)
            hot = (pt, bx + bw - 30, by + 28, bx, by, "r")
        elif st in ("augment", "augment_hot"):                       # the Inventor's: cold blue, an arc at the mount
            part_box(sc, bx, by, key, lab, lv, state="hover" if st == "augment_hot" else "new", w=bw, h=BH)
            callout(sc, pt, (ex, by + BH // 2), col=hexc("#9ad8f0"), lane=lane)
            sc.glow(pt[0], pt[1], 8, hexc("#2ab0c8"), 0.6)
            if st == "augment_hot":
                hot = (pt, bx + bw - 30, by + 28, bx, by, "r")
        elif st == "illegal":                                         # the Maniac's: a module where it doesn't belong
            part_box(sc, bx, by, key, lab, lv, state="rare", w=bw, h=BH)
            callout(sc, pt, (ex, by + BH // 2), col=hexc("#d860d0"), lane=lane)
            sc.glow(pt[0], pt[1], 9, hexc("#d860d0"), 0.6)
            for k_, (dx_, dy_) in enumerate(((-4, -3), (3, -5), (5, 2), (-3, 4))):
                sc.rgb[int(pt[1]) + dy_, int(pt[0]) + dx_] = hexc("#70e080") if k_ % 2 else hexc("#ffc0f4")
        elif st == "broken":
            part_box(sc, bx, by, key, lab, lv, state="broken", w=bw, h=BH)
            callout(sc, pt, (ex, by + BH // 2), col=RED_, lane=lane)
            sc.glow(pt[0], pt[1], 8, RED_, 0.5)
        else:
            part_box(sc, bx, by, key, lab, lv, state="hover" if key and (key == hover or key == a_.get("flash")) else "normal",
                     w=bw, h=BH)
            callout(sc, pt, (ex, by + BH // 2), col=hexc("#ffe0a0") if key and key == hover else BLUE,
                    dash=st == "free", lane=lane)
            if key and key == hover:
                hot = (pt, bx + bw - 30, by + 28, bx, by, "r")
    sway, pulse, drop = a_.get("sway", 0), a_.get("pulse", 1.0), a_.get("drop")
    if hot and crane and (new_key or body_new):                       # the crane: the part over its mount
        pt = hot[0]
        hx = min(int(pt[0]), x1 - 10 - rw - 30)                       # never over the boxes of the right column
        y_rest = y0 + (30 if body_new else 38)
        y_hook = y_rest
        if drop is not None:                                          # lowering it onto the mount
            y_low = int(pt[1]) - 56
            y_hook = int(y_rest + (y_low - y_rest) * drop * drop)
        if body_new:
            bottom = crane_hook(sc, hx, y0 + 8, y_hook, None, part=body_new, sway=sway)
        else:
            bottom = crane_hook(sc, hx, y0 + 8, y_hook, new_key, sway=sway)
        sc.glow(pt[0], pt[1], 10, HOTC, 0.6 * pulse)
        for k in range(bottom + 4, int(pt[1]) - 8, 4):
            sc.rgb[k:k + 2, hx] = HOTC
    if inst:                                                          # the hook going back up, empty
        p_ = at(M.get(inst, [0, -60]))
        hx = min(int(p_[0]), x1 - 10 - rw - 30)
        up = a_.get("retract", 1.0)
        y_low, y_rest = int(p_[1]) - 56, y0 + 38
        crane_hook(sc, hx, y0 + 8, int(y_low + (y_rest - y_low) * (1 - (1 - up) ** 2)), None, sway=sway, carry=False)
    return hot


RACK = {   # the parts rack: spare parts lying on it, by slot kind
    "arm": [("shield", 1), ("tongs", 1)], "legs": [("spider", 1)], "head": [("lamp", 1)],
}


def panel_tabs(sc, cur, broken=1, anim=None):
    """The right panel's tabs: what the battle brought, the parts rack, the repairs. anim: press (which tab is
    held down), flash (a glint across the open one, 0..1), pulse (the repair badge's throb)."""
    a_ = anim or {}
    for j, (key, text) in enumerate((("loot", "ДОБЫЧА"), ("rack", "СТОЙКА"), ("repair", "РЕМОНТ"))):
        x0 = 714 + j * 78
        FU.tab(sc, x0, 58, x0 + 74, 84, text, active=key == cur, badge=broken if key == "repair" and broken else None,
               dy=1 if a_.get("press") == key else 0, flash=a_.get("flash") if key == cur else None,
               pulse=a_.get("pulse", 0.0))
    sc.rgb[84, 710:946] = hexc("#8a6a34")


def loot_panel(sc, new_key, drag=False):
    H.fx_line(sc, 720, 90, "{выбор:1 из 3}", dim=True)
    for j, (key, kind, st, nm, who, lines) in enumerate(OFFERS):
        y0 = 114 + j * 114
        on_hook = key == new_key
        FU.cell(sc, 716, y0, 940, y0 + 106, "hi" if on_hook else st)
        if on_hook:
            FU.socket(sc, 724, y0 + 10, 776, y0 + 62)
            letters(sc, "в" if drag else "на", 750, y0 + 20, "text", 16, col=BRASS, align="center")
            letters(sc, "руке" if drag else "крюке", 750, y0 + 38, "text", 16, col=BRASS, align="center")
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


def rack_panel(sc, frame, slot, chosen, cur):
    """What can go into the chosen body slot: spare parts on the rack, a part off another golem (swapped), the spare
    one; the part now in it goes to the rack."""
    kind = "legs" if slot == "legs" else ("head" if slot == "head" else "arm")
    lab = dict(SLOTS)[slot]
    letters(sc, f"{frame.lower()} · {lab}", 720, 90, "text", 16, col=GOLD)
    rows = [(k_, f"на стойке ×{n}", "rack") for k_, n in RACK[kind]]
    rows += [("wrench", "с Механика", "swap")] if kind == "arm" else []
    rows += [({"arm": "fist", "legs": "walk", "head": "helm"}[kind], "запасная", "spare")]
    rows = rows[:4]
    for j, (k_, tag, src) in enumerate(rows):
        y0 = 110 + j * 74
        st = "hi" if k_ == chosen else "normal"
        FU.cell(sc, 716, y0, 940, y0 + 70, st)
        FU.cell(sc, 722, y0 + 9, 774, y0 + 61, "locked")
        if k_ == chosen:
            letters(sc, "на", 748, y0 + 17, "text", 16, col=BRASS, align="center")
            letters(sc, "крюке", 748, y0 + 35, "text", 16, col=BRASS, align="center")
        else:
            part_icon(sc, slot, k_, 732, y0 + 19, 32, hull=frame)
        letters(sc, part_name(slot, k_), 784, y0 + 4, "text", 16, col=GOLD if st == "hi" else INK)
        letters(sc, tag, 784, y0 + 22, "text", 16, col=BRASS if src == "rack" else (PALE if src == "spare" else MUTED))
        H.fx_rows(sc, 784, y0 + 44, 150, PART_FX[k_])
    y = 110 + len(rows) * 74 + 2
    part_icon(sc, slot, cur, 720, y + 2)
    H.fx_line(sc, 740, y, f"{part_name(slot, cur)} → на стойку", dim=True)
    letters(sc, "переставлять — бесплатно", 720, y + 22, "text", 16, col=PALE)


def repair_panel(sc):
    """What broke on the chosen golem, what it costs to mend, what happens if it is not mended; the whole army."""
    H.glyph(sc, "поломка", 720, 92, 2)
    letters(sc, "Мудрец сломан", 748, 92, "text", 16, col=RED)
    FU.cell(sc, 716, 118, 940, 176, "broken")
    mod_icon(sc, "overload", 726, 132, 2)
    letters(sc, "Перегрузка", 766, 124, "text", 16, col=INK)
    H.fx_line(sc, 766, 146, "{модуль:II} ⇒ {модуль:I}")
    letters(sc, "уровень потерян насовсем", 720, 182, "text", 16, col=MUTED)
    H.fx_line(sc, 720, 206, "{ремонт} → в строй · {металл:2}")
    H.fx_line(sc, 720, 232, "не чинить → пропускает бой", dim=True)
    H.fx_line(sc, 720, 258, "Запасные части → {модуль} цел", dim=True)
    sc.rgb[288, 716:940] = hexc("#5a5860")
    letters(sc, "армия", 720, 294, "text", 16, col=MUTED)
    for j, (fr, ok) in enumerate((("Страж", True), ("Мудрец", False), ("Орудие", True), ("Механик", True))):
        y = 318 + j * 25
        H.glyph(sc, "ремонт" if ok else "поломка", 720, y, 1)
        letters(sc, fr, 744, y - 2, "text", 16, col=INK if ok else RED)
        letters(sc, "в строю" if ok else "{металл:2}".replace("{металл:2}", "2"), 932, y - 2, "text", 16,
                col=PALE if ok else BRASS, align="right")
    H.fx_line(sc, 720, 428, "{металл:14} → {металл:12}")


def workshop(variant=None, frame="Орудие", new_key="long", name=None, panel="loot", body_new=None, anim=None,
             ret=False):
    """The slipway: the golem on the workbench before its drawing, its body on the left, what is inside on the right;
    the chosen part hangs from the crane over the mount it takes. On the left the army on its rack; on the right the
    panel with its tabs: what the battle brought (one of three), the parts rack (a body slot chosen — what can go in
    it), the repairs (a broken golem chosen — what broke and what it costs)."""
    import frames as F
    a_ = anim or {}
    sc = screen(11)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "МАСТЕРСКАЯ", glint=a_.get("glint"))
    metal(sc, 14, x=18)
    toolbar(sc)
    rack(sc, 10, 52, 168, sel=frame)
    _, ncell, mods, core, state = next(g for g in ARMY if g[0] == frame)
    role = ROLE[frame]
    FU.plate(sc, 176, 52, 700, 462, seed=3)
    body = BODY.get(frame)
    if panel == "rack":
        hot = slipway(sc, frame, mods, core, ncell, (186, 62, 690, 408), new_key=None, variant=variant, role=role,
                      body=body, body_new=body_new, body_hot=body_new[0] if body_new else None)
    elif panel == "repair":
        hot = slipway(sc, frame, mods, core, ncell, (186, 62, 690, 408), new_key=None, variant="plain", role=role,
                      broken=True, damaged=("overload",), body=body, crane=False)
        FU.steam(sc, 430, 150, 14, seed=4)
    else:
        hot = slipway(sc, frame, mods, core, ncell, (186, 62, 690, 408), new_key=new_key, variant=variant,
                      role=role, broken=state == "broken", body=body, anim=a_, crane=variant != "drag")
    # under the drawing: the frame's own and its cells
    passive = {"Страж": "Заслон: {радиус:1} → {цель:1}", "Мудрец": "Питание: {свой} {радиус:1} → {через:−1}",
               "Горн": "Жар горна: {каждые:1} → {огонь} {радиус:1}", "Орудие": "Наводка: {дальность} → {урон} без потерь",
               "Механик": "Наладка: {каждые:1} → {свой} {радиус:1} {ремонт:1}"}[frame]
    H.fx_line(sc, 190, 418, passive)
    for j in range(ncell):
        cx_ = 690 - (ncell - j) * 30
        FU.cell(sc, cx_, 412, cx_ + 24, 436, "hi" if j < len(mods) else
                ("new" if (j == len(mods) and new_key and panel == "loot") else "locked"))
    letters(sc, "ячейки", 690 - ncell * 30, 440, "text", 16, col=MUTED)
    # the panel on the right, with its tabs
    FU.plate(sc, 708, 52, 948, 462, seed=4)
    panel_tabs(sc, panel)
    if panel == "rack":
        rack_panel(sc, frame, body_new[0], body_new[1], GP_part(frame, body_new[0]))
    elif panel == "repair":
        repair_panel(sc)
    else:
        loot_panel(sc, new_key, drag=variant == "drag")
    FU.sill(sc, 468)
    action(sc, 12, 478, 174, 526, "Автосборка", "steel")
    action(sc, 178, 478, 356, 526, "Починить · 2", "hot", heated=panel == "repair")
    action(sc, 360, 478, 522, 526, "Переплавка", "rust")
    action(sc, 526, 478, 704, 526, "Пропуск · +4", "steel")
    action(sc, 710, 472, 948, 532, "В БОЙ", "hot", big=True, anim={"glow": a_["plate"]} if "plate" in a_ else None)
    FU.sparks(sc, 186, 400, 10, seed=5 + a_.get("seed", 0))
    if ret:
        return sc
    if panel == "repair":
        H.cursor(sc, 201, 506)
    elif variant == "drag":
        drag_over(sc, new_key, hot, frame, a_.get("at", (446, 300)), a_.get("glow", 1.0))
    elif variant is None and hot:
        H.cursor(sc, hot[1], hot[2])
    if variant == "drag":
        name = name or "foundry_drag.png"
    name = name or {"loot": "foundry_workshop.png", "rack": "foundry_workshop_rack.png",
                    "repair": "foundry_workshop_repair.png"}[panel]
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


def drag_over(sc, key, hot, frame, at, glow=1.0):
    """A module carried with the mouse: the bays it can't go to (other hulls) go dark under a red cross, its tag
    says why; the cell it can take is lit cold blue, a dotted line runs to it from the module; the module itself
    rides the cursor, lifted, its shadow under it."""
    for i, (fr, *_r) in enumerate(ARMY):                              # the rack: only its own hull takes it
        if fr == frame:
            continue
        y = 52 + i * 92
        sc.rgb[y + 2:y + 84, 12:166] *= 0.42
        for d in range(-2, 3):                                        # the cross, thick, rust red
            for t in np.linspace(0, 1, 120):
                x_, y_ = int(30 + t * 56), int(y + 20 + t * 52)
                sc.rgb[y_ + d, x_ - 1:x_ + 2] = hexc("#c84a3a")
                sc.rgb[int(y + 72 - t * 52) + d, x_ - 1:x_ + 2] = hexc("#c84a3a")
        FU.tag(sc, 20, y + 58, 164, y + 80, "другой корпус", "rust")
    if hot is not None and len(hot) > 4:                              # the cell that takes it: a dotted line to it
        tx, ty = hot[3], hot[4] + 21
        sc.glow(tx + 75, ty, 46, hexc("#9ad8ff"), 0.5 * glow)
        x0, y0 = at[0] + 40, at[1] + 20
        n = int(np.hypot(tx - x0, ty - y0) / 6)
        for k in range(n):
            if k % 2 == 0:
                x_ = int(x0 + (tx - x0) * k / n)
                y_ = int(y0 + (ty - y0) * k / n)
                sc.rgb[y_ - 1:y_ + 2, x_ - 1:x_ + 2] = SU.OUTL
                sc.rgb[y_:y_ + 2, x_:x_ + 2] = hexc("#cfeeff")
    cx, cy = at                                                       # the module in hand
    sh = (sc.xx >= cx + 6) & (sc.xx < cx + 50) & (sc.yy >= cy + 8) & (sc.yy < cy + 52)
    sc.rgb[sh] *= 0.5
    sc.glow(cx + 22, cy + 22, 30, hexc("#ffb060"), 0.3)
    FU.cell(sc, cx, cy, cx + 44, cy + 44, "hover")
    mod_icon(sc, key, cx + 6, cy + 6, 2)
    H.cursor(sc, cx + 26, cy + 28)


def states():
    """The Foundry's controls and cells in every state, on one sheet: a control at rest, under the mouse, pressed,
    and shut (its metal dull, why — under it); the cells' rims; the panels when there is nothing in them."""
    sc = screen(97)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "СОСТОЯНИЯ", "wrench")
    FU.plate(sc, 12, 52, 948, 266, seed=81)
    heading(sc, "КНОПКИ", 26, 62)
    cols = ("обычная", "под мышью", "нажата", "недоступна")
    for i, c in enumerate(cols):
        letters(sc, c, 124 + i * 232, 86, "text", 16, col=MUTED, align="center")
    for i in range(4):
        x0 = 24 + i * 232
        heated, an = i == 1, ({"press": 1.0} if i == 2 else None)
        before = sc.rgb.copy()
        action(sc, x0, 106, x0 + 200, 138, "Автосборка", "dull" if i == 3 else "steel", heated=heated, anim=an)
        action(sc, x0, 146, x0 + 200, 178, "Починить · 2", "hot", heated=heated, anim={"turn": 0.5} if i == 2 else None)
        action(sc, x0, 190, x0 + 214, 236, "В БОЙ", "hot" if i < 3 else "dull", big=True, heated=i in (1, 2),
               anim={"angle": 1.0, "glow": 1.0} if i == 2 else None)
        if i == 3:                                                    # shut: the metal of the controls dulled, and why
            new_ = np.abs(sc.rgb - before).max(axis=2) > 1
            new_[:142, :] = False
            sc.rgb[new_] *= 0.55
            H.fx_line(sc, x0 + 6, 240, "не хватает {металл:2}")
    FU.plate(sc, 12, 272, 948, 372, seed=82)
    heading(sc, "ЯЧЕЙКИ", 26, 282)
    cells = [("normal", "обычная"), ("hi", "выбрана"), ("hover", "под мышью"), ("new", "новое"), ("broken", "сломано"),
             ("rare", "редкое"), ("trophy", "трофей"), ("locked", "закрыто"), ("locked", "пусто")]
    for i, (st, what) in enumerate(cells):
        x0 = 24 + i * 102
        FU.cell(sc, x0, 306, x0 + 94, 344, st)
        if what == "пусто":
            for k in range(x0 + 10, x0 + 84, 6):                      # an empty place: a dashed outline in it
                sc.rgb[316, k:k + 3] = hexc("#4a4a52")
                sc.rgb[334, k:k + 3] = hexc("#4a4a52")
        letters(sc, what, x0 + 47, 348, "text", 16, col=MUTED, align="center")
    FU.plate(sc, 12, 378, 948, 532, seed=83)
    heading(sc, "ПУСТО", 26, 388)
    empties = [("ДОБЫЧА", "добычи нет — враг ушёл", "или пропуск → {металл:+4}"),
               ("СТОЙКА", "стойка пуста", "детали — из добычи и трофеев"),
               ("РЕМОНТ", "всё цело", "{ремонт} не нужен")]
    for i, (tab_, ln1, ln2) in enumerate(empties):
        x0 = 24 + i * 308
        FU.tab(sc, x0, 414, x0 + 90, 440, tab_, active=True)
        FU.cell(sc, x0, 440, x0 + 296, 522, "locked")
        for k in range(x0 + 10, x0 + 286, 6):
            sc.rgb[450, k:k + 3] = hexc("#3a3a42")
            sc.rgb[512, k:k + 3] = hexc("#3a3a42")
        letters(sc, ln1, x0 + 148, 458, "text", 16, col=PALE, align="center")
        w_, _ = H.fx_line(sc, 0, 0, ln2, draw=False)
        H.fx_line(sc, int(x0 + 148 - w_ / 2), 482, ln2, dim=True)
    img = sc.image(S)
    img.save(out("foundry_states.png"))
    print("foundry_states.png", img.size)


def GP_part(frame, slot):
    """The part in this slot of this golem now."""
    import golem_parts as GP
    return dict(GP.STOCK[frame], **BODY.get(frame, {}))[slot]


def workshop_rack():
    workshop(frame="Орудие", panel="rack", body_new=("arm_f", "shield"))


def workshop_repair():
    workshop(frame="Мудрец", panel="repair")


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
    n = len(STEPS)
    w = (WW - 24 + 12 * (n - 1)) // n
    for i, st in enumerate(STEPS):
        x = 12 + i * (w - 12)
        kind = "brass" if i < cur else ("hot" if i == cur else "dull")
        FU.step_plate(sc, x, y, x + w, y + 32, f"{i + 1}. {st}", kind, first=i == 0)


def assembly(step=0, anim=None, ret=False):
    """A new golem, built from nothing: 1 — the frame (one of two, as drawings on blueprint paper: role, size, cells,
    its own rule, price); 2 — the core (three, glowing in their cradles, one goes into the chest); 3 — the modules,
    on the slipway (workshop()); 4 — the start: steam, sparks, and its passport — what it was built of."""
    import frames as F
    import golems_h as GH
    sc = screen(23 + step)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "НОВЫЙ ГОЛЕМ", "hammer")
    metal(sc, 22, x=18)
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
        FU.sill(sc, 468)
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
        FU.sill(sc, 468)
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
        FU.sill(sc, 468)
        action(sc, 12, 478, 300, 526, "Назад", "steel")
        action(sc, 660, 472, 948, 532, "ДАЛЕЕ: МОДУЛИ", "hot", big=True)
        name = "foundry_new_core.png"
    else:
        FU.plate(sc, 12, 96, 948, 462, seed=10)
        g = golem_sprite("Горн", {"magnet": 1, "maw": 1}, 2.3, body=NEW_BODY, core="fire")
        sc.rgb[440:452, 190:410] = hexc("#24222a")                   # the stand
        sc.rgb[440, 190:410] = hexc("#6a6870")
        sc.blit(g, int(300 - g.ox), int(442 - g.oy))
        if anim is None:                                              # (moving: ui_anim lays steam and sparks on)
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
        FU.sill(sc, 468)
        action(sc, 12, 478, 300, 526, "Назад", "steel")
        action(sc, 660, 472, 948, 532, "В МАСТЕРСКУЮ", "hot", big=True)
        name = "foundry_new_start.png"
    if ret:
        return sc
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


def new_golem():
    for st in (0, 1, 2, 4):
        assembly(st)


# ---------------------------------------------------------------- the camp: the whole army taken apart and put together again
CAMP_FIND = [   # (key or (slot, part), kind, state, name, for whom, lines)
    (("arm_n", "flail"), "редкая рука", "rare", "Кистень", "рука · любой", PART_FX["flail"]),
    ("fire", "ядро", "hi", "Огненное ядро", "любой", MOD_FX["fire"]),
    ("rest", "отдых", "normal", "Отдых у горна", "вся армия", ["{ремонт} всех · {металл:0}"]),
]


def camp(drag=0.55, ret=False):
    """Привал у горна: the army on its stands in a row, each golem with its body parts, its module cells and its
    core under it — here anything comes off and goes on anywhere, free; a core is being carried from the Sage to the
    Gun (the Gun's core socket glows to take it, the others dim); the bench with what lies spare; one of three things
    found at the camp."""
    import golem_parts as GP
    sc = screen(37)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "ПРИВАЛ", "lantern")
    metal(sc, 14, x=18)
    toolbar(sc)
    # the army on its stands
    FU.plate(sc, 12, 52, 948, 300, seed=51)
    heading(sc, "АРМИЯ", 26, 64)
    letters(sc, "всё снимается и ставится — бесплатно", 934, 70, "text", 16, col=MUTED, align="right")
    targets = {}
    for i, (fr, ncell, mods, core, state) in enumerate(ARMY):
        cx = 128 + i * 232
        body = dict(GP.STOCK[fr], **BODY.get(fr, {}))
        FU.cell(sc, cx - 108, 90, cx + 108, 292, "broken" if state == "broken" else "normal")
        sc.rgb[202:208, cx - 60:cx + 60] = hexc("#24222a")                       # its stand
        sc.rgb[202, cx - 60:cx + 60] = hexc("#5a5860")
        g = golem_sprite(fr, mods, {"Страж": 0.9, "Механик": 1.45}.get(fr, 1.15), body=BODY.get(fr))
        if state == "broken":
            from swarm_effects import lit
            g = lit(g, (70, 70, 80), 0.45)
        sc.blit(g, int(cx - g.ox), int(203 - g.oy))
        letters(sc, fr, cx - 100, 96, "text", 16, col=RED if state == "broken" else INK)
        # its body parts, its modules, its core — each in its own socket
        for j, (slot, _) in enumerate(SLOTS):
            sx = cx - 100 + j * 26
            FU.socket(sc, sx, 212, sx + 22, 234)
            part_icon(sc, slot, body[slot], sx + 3, 215, hull=fr)
        for j in range(ncell):
            sx = cx - 100 + j * 26
            ks = list(mods)
            st = "hi" if j < len(ks) else "locked"
            FU.cell(sc, sx, 240, sx + 22, 262, st)
            if j < len(ks):
                mod_icon(sc, ks[j], sx + 3, 243)
        # the core's socket
        px, py = cx + 82, 252
        targets[fr] = (px, py)
        d = np.hypot(sc.xx - px, sc.yy - py)
        sc.rgb[d <= 11] = SU.OUTL
        sc.rgb[(d <= 10) & (d > 8)] = hexc("#4a4850")
        sc.rgb[d <= 8] = hexc("#0c0b0e")
        if fr != "Мудрец" or drag is None:
            FU.core_port(sc, px, py, core, r=7)
        letters(sc, "ядро", px, 266, "text", 16, col=MUTED, align="center")
    # carrying the Sage's storm core to the Gun: where it can go glows, where it can't is dimmed
    if drag is not None:
        (sx, sy), (tx, ty) = targets["Мудрец"], targets["Орудие"]
        hx, hy = sx + (tx - sx) * drag, sy + (ty - sy) * drag - 34 * np.sin(np.pi * drag)
        for fr, (px, py) in targets.items():
            if fr == "Орудие":
                ring = np.abs(np.hypot(sc.xx - px, sc.yy - py) - 13) <= 1.3
                sc.rgb[ring] = hexc("#8ad8ff")
                sc.glow(px, py, 18, hexc("#8ad8ff"), 0.5)
            elif fr != "Мудрец":
                d = np.hypot(sc.xx - px, sc.yy - py) <= 11
                sc.rgb[d] = sc.rgb[d] * 0.45
        for k in range(40):                                                    # its path, dotted
            t_ = k / 40 * drag
            qx, qy = sx + (tx - sx) * t_, sy + (ty - sy) * t_ - 60 * np.sin(np.pi * t_)
            if k % 2 == 0:
                sc.rgb[int(qy):int(qy) + 2, int(qx):int(qx) + 2] = hexc("#8ad8ff")
        hy = sy + (ty - sy) * drag - 60 * np.sin(np.pi * drag)
        ring = np.abs(np.hypot(sc.xx - sx, sc.yy - sy) - 9) <= 0.8              # where it was taken from
        sc.rgb[ring & ((sc.xx + sc.yy) % 3 == 0)] = hexc("#8ad8ff")
        sc.glow(hx, hy, 26, hexc("#8ad8ff"), 0.55)
        FU.core_port(sc, int(hx), int(hy), "volt", r=11)
        H.cursor(sc, int(hx + 4), int(hy + 4))
    # the bench: what lies spare
    FU.plate(sc, 12, 306, 470, 462, seed=52)
    heading(sc, "ВЕРСТАК", 26, 318)
    sc.rgb[352:446, 22:460] = hexc("#3a2614")                                     # the bench top, planks
    for yy in range(352, 446, 12):
        sc.rgb[yy, 22:460] = hexc("#24160a")
        sc.rgb[yy + 1, 22:460] = hexc("#5a3e22")
    o_, _, _ = SU.edges((sc.xx >= 22) & (sc.xx < 460) & (sc.yy >= 352) & (sc.yy < 446))
    sc.rgb[o_] = SU.OUTL
    spare = [("arm", "shield"), ("arm", "tongs"), ("head", "lamp"), ("legs", "spider"), ("mod", "canister")]
    for j, (kind, k_) in enumerate(spare):
        bx = 36 + j * 84
        FU.cell(sc, bx, 362, bx + 70, 436, "normal")
        if kind == "mod":
            mod_icon(sc, k_, bx + 19, 372, 2)
            nm = MOD_NAME[k_]
        else:
            slot = {"arm": "arm_n", "head": "head", "legs": "legs"}[kind]
            part_icon(sc, slot, k_, bx + 19, 372, 32)
            nm = part_name(slot, k_)
        letters(sc, nm.split()[0] if len(nm) > 9 else nm, bx + 35, 412, "text", 16, col=INK, align="center")
    # found at the camp: one of three
    FU.plate(sc, 478, 306, 948, 462, seed=53)
    heading(sc, "ЧТО НАШЛОСЬ", 492, 318)
    H.fx_line(sc, 934 - 92, 320, "{выбор:1 из 3}", dim=True)
    for j, (key, kind, st, nm, who, lines) in enumerate(CAMP_FIND):
        x0 = 488 + j * 152
        FU.cell(sc, x0, 344, x0 + 146, 456, "hi" if j == 1 else st)
        if isinstance(key, tuple):
            part_icon(sc, key[0], key[1], x0 + 8, 352, 32)
        elif key == "rest":
            H.glyph(sc, "ремонт", x0 + 12, 358, 3)
        else:
            FU.core_port(sc, x0 + 24, 368, key, r=12)
        letters(sc, kind, x0 + 50, 352, "text", 16, col={"rare": (190, 150, 240), "hi": BRASS, "normal": MUTED}[st])
        letters(sc, nm, x0 + 8, 392, "text", 16, col=GOLD if j == 1 else INK)
        letters(sc, who, x0 + 8, 410, "text", 16, col=PALE)
        H.fx_rows(sc, x0 + 8, 430, 132, lines)
    FU.sill(sc, 468)
    action(sc, 12, 478, 200, 526, "Как было", "steel")
    action(sc, 210, 478, 420, 526, "Разобрать всё", "steel")
    action(sc, 680, 472, 948, 532, "В ПУТЬ", "hot", big=True)
    if ret:
        return sc
    img = sc.image(S)
    img.save(out("foundry_camp.png"))
    print("foundry_camp.png", img.size)


# ---------------------------------------------------------------- melting down
def molten(spr, k=1.0):
    """A sprite gone red-hot: its shading mapped onto the melt's ramp."""
    out = spr.__class__(spr.w, spr.h)
    out.a = spr.a.copy()
    lum = spr.rgb.mean(axis=2) / 255.0
    pal = np.array([hexc(c) for c in ("#5a1408", "#a8320e", "#e86a1a", "#ffb43a", "#fff3c0")])
    idx = np.clip((lum * 4.6 * k + 0.6).astype(int), 0, 4)
    out.rgb = pal[idx].astype(np.float32)
    out.ox, out.oy = getattr(spr, "ox", 0), getattr(spr, "oy", 0)
    return out


def crucible_scene(sc, x0, y0, x1, y1, melt_key, cast_key):
    """The hearth (hearth.py): a firebrick forge under its hood, a heap of coal with the crucible sunk in it, the
    module going down into the melt, the pour into the sand mould where the other module is being cast."""
    import hearth
    hearth.scene(sc, x0, y0, x1, y1, molten(IC.icon(melt_key, 3, "module")), molten(IC.icon(cast_key, 3, "module"), 1.2))


_VN = {}


def value_noise_cached(sc):
    from noise import value_noise
    key = (sc.w, sc.h)
    if key not in _VN:
        _VN[key] = value_noise(sc.w, sc.h, 3, 77)
    return _VN[key]


def smelt(base_only=False):
    """Переплавка: a module goes into the crucible and its melt gives a level to another module of the same hull; a
    spare part melts down to metal. Left — what goes in; in the middle the crucible over the hearth pouring into the
    mould; right — what takes the level."""
    sc = screen(29)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "ПЕРЕПЛАВКА", "tongs")
    metal(sc, 14, x=18)
    toolbar(sc)
    FU.plate(sc, 12, 52, 300, 462, seed=41)
    heading(sc, "В ТИГЕЛЬ", 26, 64)
    rows = [("mod", "canister", "Картечь", "Орудие · I", "hi"), ("mod", "chain", "Цепная молния", "Мудрец · I", "normal"),
            ("mod", "repair", "Ремонт", "Механик · I", "normal"), ("part", "tongs", "Клещи", "стойка → {металл:+2}", "normal")]
    for j, (kind, k_, nm, sub, st) in enumerate(rows):
        y0 = 94 + j * 70
        FU.cell(sc, 20, y0, 292, y0 + 62, st)
        FU.cell(sc, 26, y0 + 6, 76, y0 + 56, "locked")
        if kind == "mod":
            mod_icon(sc, k_, 35, y0 + 15, 2)
        else:
            part_icon(sc, "arm_f", k_, 35, y0 + 15, 32)
        letters(sc, nm, 86, y0 + 8, "text", 16, col=GOLD if st == "hi" else INK)
        H.fx_line(sc, 86, y0 + 32, sub, dim=st != "hi")
    H.fx_line(sc, 24, 380, "{модуль} → {модуль:+1}", dim=True)
    letters(sc, "тот же корпус", 24, 404, "text", 16, col=PALE)
    H.fx_line(sc, 24, 428, "деталь → {металл:+2}", dim=True)
    # the crucible
    FU.plate(sc, 308, 52, 652, 462, seed=43)
    sc.rgb[60:454, 316:644] = sc.rgb[60:454, 316:644] * 0.55
    if not base_only:
        crucible_scene(sc, 316, 60, 644, 454, "canister", "long")
    # into the mould
    FU.plate(sc, 660, 52, 948, 462, seed=42)
    heading(sc, "В ЛИТЬЁ", 674, 64)
    rows = [("long", "Длинный ствол", "Орудие", 1, "hi"), ("mortar", "Мортира", "Орудие", 1, "normal"),
            ("intercept", "Перехват", "Страж · другой корпус", 1, "locked")]
    for j, (k_, nm, who, lv, st) in enumerate(rows):
        y0 = 94 + j * 70
        FU.cell(sc, 668, y0, 940, y0 + 62, st)
        FU.cell(sc, 674, y0 + 6, 724, y0 + 56, "locked")
        mod_icon(sc, k_, 683, y0 + 15, 2)
        letters(sc, nm, 734, y0 + 8, "text", 16, col=GOLD if st == "hi" else (INK if st == "normal" else PALE))
        letters(sc, who, 734, y0 + 32, "text", 16, col=MUTED if st != "locked" else PALE)
        if st != "locked":
            H.fx_line(sc, 820, y0 + 30, "{модуль:I} ⇒ {модуль:II}" if st == "hi" else "{модуль:I}", dim=st != "hi")
    H.fx_line(sc, 674, 316, "{металл:3} · за раз", dim=True)
    H.fx_line(sc, 674, 344, "{металл:14} → {металл:11}")
    FU.sill(sc, 468)
    action(sc, 12, 478, 300, 526, "Назад", "steel")
    action(sc, 620, 472, 948, 532, "ПЕРЕПЛАВИТЬ · 3", "hot", big=True)
    H.cursor(sc, 200, 120)
    if base_only:
        return sc
    img = sc.image(S)
    img.save(out("foundry_smelt.png"))
    print("foundry_smelt.png", img.size)


# ---------------------------------------------------------------- the golem's card, as big as the screen
ABIL = {   # the frame's and the class's own, in glyphs
    "Наводка": ["{дальность} → 2–3 ряд", "{дальность} → {урон} без потерь"],
    "Огнеупорность": ["{огонь} ×¼ · гаснет за ход"],
    "Литой металл": ["{кол} ×½ · {дроб} ×1 · {кисл} ×2"],
    "Бесстрашие": ["{страх:✕} · {яд:✕}"],
    "Проводник": ["{молния} ×1,5"],
}


FRAME_EN = {"Страж": "guard", "Мудрец": "sage", "Горн": "forge", "Орудие": "gun", "Механик": "mechanic"}
CARD = {   # frame: (role on the beam, modules, cells, core, the box under the mouse, its own rule, leadership,
           #         body rows, arm rows (slot, part, damage, kind, range), class extras)
    "Орудие": ("стрелок · голем", {"mortar": 1, "canister": 1, "long": 1}, 4, "cast", "mortar",
               "Наводка: {дальность} → {урон} без потерь", 5,
               (("здоровье", "55"), ("броня", "2"), ("скорость", "1"), ("размер", "5"), ("инициатива", "4")),
               (("arm_n", "cannon", "1–10 +3", "{дроб}", "3"), ("arm_f", "cannon", "1–10 +3", "{дроб}", "3")), ()),
    "Страж": ("танк · голем", {"tower": 2, "intercept": 1, "plates": 1}, 5, "cast", "intercept",
              "Заслон: {радиус:1} → {цель:1}", 7,
              (("здоровье", "100"), ("броня", "4"), ("скорость", "1"), ("размер", "6"), ("инициатива", "3")),
              (("arm_n", "maul", "1–6 +3", "{дроб}", "1"), ("arm_f", "shield", "—", "", "")), ()),
    "Мудрец": ("маг · голем", {"chain": 1, "fireball": 1, "overload": 2}, 4, "volt", "chain",
               "Питание: {свой} {радиус:1} → {через:−1}", 5,
               (("здоровье", "40"), ("броня", "2"), ("скорость", "1"), ("размер", "5"), ("инициатива", "5")),
               (("arm_n", "staff", "1–8 +1", "{молния}", "4"), ("arm_f", "focus", "—", "", "")), ()),
    "Горн": ("контроль · голем", {"magnet": 1, "maw": 1}, 4, "fire", "maw",
             "Жар горна: {каждые:1} → {огонь} {радиус:1}", 5,
             (("здоровье", "50"), ("броня", "2"), ("скорость", "1"), ("размер", "5"), ("инициатива", "3")),
             (("arm_n", "flame", "1–6", "{огонь}", "2"), ("arm_f", "tongs", "—", "", "")), ()),
    "Механик": ("поддержка · голем", {"repair": 1, "oiler": 1}, 3, "cast", "repair",
                "Наладка: {каждые:1} → {свой} {радиус:1} {ремонт:1}", 3,
                (("здоровье", "35"), ("броня", "2"), ("скорость", "2"), ("размер", "4"), ("инициатива", "3")),
                (("arm_n", "wrench", "—", "", ""), ("arm_f", "can", "—", "", "")), ()),
}


def card(frame="Орудие", hover="mortar", anim=None, ret=False):
    """A golem's card, in the slipway's language: on the left its drawing, a callout from every mount to its module
    (the one under the mouse opened in a tooltip), the chest with its core, its own rule and its cells under it; on
    the right its passport — leadership, core, last battle; body; blow; what its class can and can't."""
    sc = screen(13)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, frame.upper(), "wrench")
    role_, mods, ncell, core, hover0, rule, lead, body_rows, arm_rows, _x = CARD[frame]
    hover = hover if frame == "Орудие" else hover0
    letters(sc, role_, 16, 13, "text", 16, col=MUTED)
    toolbar(sc)
    # left: the drawing
    FU.plate(sc, 6, 50, 590, 476, seed=7)
    hot = slipway(sc, frame, mods, core, ncell, (16, 60, 580, 432), hover=hover, crane=False, body=BODY.get(frame))
    H.fx_line(sc, 20, 444, rule)
    for j in range(ncell):
        cx_ = 580 - (ncell - j) * 30
        FU.cell(sc, cx_, 440, cx_ + 24, 464, "hi" if j < len(mods) else "locked")
    letters(sc, "ячейки", 580 - ncell * 30 - 8, 444, "text", 16, col=MUTED, align="right")
    # right: the passport
    x0, x1 = 612, WW - 18
    FU.plate(sc, 598, 50, WW - 6, 476, seed=8)
    heading(sc, "ПАСПОРТ", x0, 62)
    H.fx_line(sc, x0, 90, f"{{лидер:{lead}}} · {{ядро}} {MOD_NAME[core].split()[0].lower()} · {{убийство:3}} в прошлом бою")
    y = 124
    heading(sc, "ТЕЛО", x0, y)
    y += 28
    for key, val in body_rows:
        a_ = H.glyph(sc, key, x0, y - 4, 2)
        w, _ = H.fx_line(sc, 0, 0, val, draw=False)
        H.dots(sc, x0 + a_ + 8, x1 - w - 6, y + 10)
        H.fx_line(sc, x1 - w, y - 2, val)
        y += 18
    y += 4
    heading(sc, "ВОЗМОЖНОСТИ", x0, y)
    y += 28
    cols = (x0 + 20, x0 + 138, x0 + 210, x0 + 266)
    for cx, lab in zip(cols, ("атака", "урон", None, "дальность")):
        if lab:
            H.glyph(sc, lab, cx, y - 6, 2)
    y += 14
    sc.rgb[y, x0:x1] = sc.rgb[y, x0:x1] * 0.5 + hexc("#5a5860") * 0.5
    for slot, part, dmg, kind_, rng in arm_rows:                     # a row per arm: what each hand strikes with
        part_icon(sc, slot, part, x0, y + 5, hull=frame)
        letters(sc, part_name(slot, part), cols[0], y + 6, "text", 16, col=GOLD)
        letters(sc, dmg, cols[1], y + 6, "text", 16, col=INK if dmg != "—" else PALE)
        if kind_:
            H.fx_line(sc, cols[2], y + 6, kind_)
        letters(sc, rng, cols[3], y + 6, "text", 16, col=INK)
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
    FU.sill(sc, 482)
    action(sc, 760, 488, WW - 10, 532, "Закрыть", "steel")
    # the module under the mouse: its tooltip under its box
    a_ = anim or {}
    if hot:
        pt, cx, cy, bx, by, side = hot
        lines = MOD_FX[hover]
        tw = 300
        th = H.fx_rows(sc, 0, 0, tw - 24, lines, draw=False) + 40
        tx = bx if side == "l" else bx + 152 - tw
        if by + 52 + th > 470:                                         # no room under the box: open it above
            by = by - 52 - th - 4
        k = a_.get("tip", 1.0)                                         # the tooltip coming in: up from below, fading in
        if k > 0:
            before = sc.rgb.copy()
            dy = int(round((1 - k) * 8))
            FU.cell(sc, tx, by + 52 + dy, tx + tw, by + 52 + th + dy, "normal")
            letters(sc, MOD_NAME[hover], tx + 12, by + 60 + dy, "text", 16, col=GOLD)
            FU.levels(sc, tx + tw - 30, by + 62 + dy, mods[hover])
            H.fx_rows(sc, tx + 12, by + 84 + dy, tw - 24, lines)
            if k < 1:
                sc.rgb[:] = before * (1 - k) + sc.rgb * k
        H.cursor(sc, cx, cy)
    if ret:
        return sc
    img = sc.image(S)
    name = "foundry_card.png" if frame == "Орудие" else f"foundry_card_{FRAME_EN[frame]}.png"
    img.save(out(name))
    print(name, img.size)


# ---------------------------------------------------------------- choosing the leader
PICK = [   # (name, epithet, sprite, scale on the card, the army it starts with, its own rule)
    ("Отец колосса", "армия из одного", "colossus", 1.55, ["Механик"], "{каждые:3} → {оглушение:1} {радиус:1}"),
    ("Изобретатель", "мастер аугментов", "inventor", 2.6, ["Мудрец", "Орудие", "Механик"],
     "{начало} → {свой} {радиус:1} {модуль:+1}"),
    ("Маньяк", "безумный сборщик", "maniac", 2.2, ["Мудрец", "Орудие"], "{каждые:3} → {свой} {модуль} наугад"),
    ("Зодчий", "строитель крепостей", "zodchiy", 2.15, ["Страж", "Механик"], "{начало} → каменщик ×2"),
]


_LEADERS = {}


def leader_sprite(kind, k, pose="idle"):
    import golems_h as GH
    import leaders_h as LH
    key = (kind, round(k, 4), pose)
    if key not in _LEADERS:
        if kind == "colossus":
            _LEADERS[key] = GH.colossus_build(pose, k)
        else:
            _LEADERS[key] = GH.build({"inventor": LH.INVENTOR, "maniac": GH.MANIAC, "zodchiy": LH.ZODCHIY}[kind], pose, k)
    return _LEADERS[key]


def leaders_pick(anim=None, ret=False):
    """Four leaders, each behind a furnace door: the chosen one's door is open and hot. Under each: the golems it
    starts with, and its own rule; the rest behind «Полное описание»."""
    import frames as F
    sc = screen(17)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "ЛИДЕР", "hammer")
    letters(sc, "кто поведёт кузню", 16, 13, "text", 16, col=(255, 170, 80))
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
        if sel:                                                       # the furnace's depth, dark; the fire lights it
            fire = hexc("#1e0a06")[None, None, :] * (1 - t[..., None]) + hexc("#7a2410")[None, None, :] * t[..., None]
        else:
            fire = hexc("#141216")[None, None, :] * (1 - t[..., None]) + hexc("#4a2010")[None, None, :] * t[..., None]
        sc.rgb[arch] = fire[arch]
        rim = arch & ~((((X - ax) / (ar - 3)) ** 2 + ((Y - ay) / (ar - 3)) ** 2 <= 1) & (Y <= ay) | ((np.abs(X - ax) <= ar - 3) & (Y > ay) & (Y < 300)))
        sc.rgb[rim] = hexc("#b8904a") if sel else hexc("#4a4850")
        if sel:                                                       # the furnace burning: pixelfx's fire, in the arch
            import pxfx
            frames, meta = pxfx.load("forge-fire")
            before = sc.rgb.copy()
            inside = arch & ~rim
            pxfx.blend(sc, frames[(anim or {}).get("frame", 0) % len(frames)], ax, 300, meta["pivot"])
            sc.rgb[~inside] = before[~inside]
        for kk in range(-4, 5):                                       # the voussoirs: rivets round the arch
            a_ = np.pi * (0.5 + kk / 10)
            FU.rivet(sc, ax - np.cos(a_) * (ar + 4), ay - np.sin(a_) * (ar + 4))
        spr = leader_sprite(kind, k)
        sc.blit(spr, int(ax - spr.ox), int(296 - spr.oy))
        if sel:
            fs = (anim or {}).get("frame", 0) // 3
            FU.sparks(sc, ax - 60, 296, 10, seed=3 + fs)
            FU.sparks(sc, ax + 64, 290, 8, seed=4 + fs)
        # the brass nameplate
        FU.cell(sc, x0 + 10, 62, x1 - 10, 104, "hi" if sel else "normal")
        letters(sc, nm.upper(), ax, 68, "title", 16, col=(255, 210, 140) if sel else INK, align="center")
        letters(sc, epi, ax, 86, "text", 16, col=BRASS if sel else MUTED, align="center")
        # what it starts with: its golems small, and its rule
        gx = ax - (len(army) - 1) * 28
        for j, fr in enumerate(army):
            ck = ("army", fr)
            if ck not in _LEADERS:
                _LEADERS[ck] = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.58)
            g = _LEADERS[ck]
            sc.blit(g, int(gx + j * 56 - g.ox), int(380 - g.oy))
        wl, _ = H.fx_line(sc, 0, 0, rule, draw=False)
        H.fx_line(sc, int(ax - wl / 2), 396, rule)
        sc.rgb[300:302, x0 + 16:x1 - 16] = hexc("#5a5860")
    FU.sill(sc, 464)
    action(sc, 12, 474, 300, 526, "Назад", "steel")
    action(sc, 326, 474, 634, 526, "Полное описание", "steel")
    action(sc, 660, 470, 948, 530, "В ПОХОД", "hot", big=True)
    if ret:
        return sc
    img = sc.image(S)
    img.save(out("foundry_leader_pick.png"))
    print("foundry_leader_pick.png", img.size)


# ---------------------------------------------------------------- a leader in full, from «Полное описание»
LEADER_FULL = {
    "colossus": dict(
        name="ОТЕЦ КОЛОССА", epi="армия из одного", k=3.0, lead="3 весь поход", cells=7,
        mods=("plates", "flail", "magnet"),
        body=(("здоровье", "здоровье", "160"), ("броня", "броня", "3"), ("скорость", "скорость", "1"),
              ("размер", "размер", "7 · 4×4"), ("инициатива", "инициатива", "1")),
        weapons=(("Электробулава", "1–8 +2 {дроб}", "размах", "1"), ("Миниган", "3 × 1–4 {кол}", None, "4")),
        abil=(("Сотрясение", "каждые 3 хода", "{каждые:3} → {дроб} {радиус:1} · {оглушение:1}", INK),
              ("Неудержимый", "постоянно", "{притяг:✕} · {оглушение:✕}", INK),
              ("Ужас", "постоянно", "{радиус:3} → {страх:1–9}", INK),
              ("Второе дыхание", "раз за бой", "{поломка} → встаёт с ½", INK),
              ("Прожорливый", "слабость", "{ремонт} → {металл:×2}", RED),
              ("Один за всех", "правило похода", "7 ячеек · модули любого корпуса", GOLD)),
        army=(("Механик", ("repair",)),), grow=("после босса, 1 из 2:", "+1 ячейка · колоссальный модуль")),
}


def leader_card(kind="colossus", frame=0, ret=False, alt=False):
    """A Foundry leader in full: the leader large in its open furnace (pixelfx's fire), its nameplate, its own cells
    with the modules it starts with; its passport — leadership, body, weapons, who comes with it; its abilities, each
    a line of glyphs with when it fires; how it grows."""
    import pxfx
    import frames as F
    L = LEADER_FULL[kind]
    sc = screen(39)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, L["name"], "hammer")
    toolbar(sc, alt=alt)
    # the furnace and the leader in it
    FU.plate(sc, 12, 52, 330, 462, seed=61)
    X, Y = sc.xx, sc.yy
    ax, ay, ar, fl = 171, 186, 116, 348
    arch = ((((X - ax) / ar) ** 2 + ((Y - ay) / ar) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar) & (Y > ay) & (Y < fl))
    t = np.clip((Y - ay + ar) / (fl - ay + ar), 0, 1)
    fire = hexc("#1e0a06")[None, None, :] * (1 - t[..., None]) + hexc("#7a2410")[None, None, :] * t[..., None]
    sc.rgb[arch] = fire[arch]
    inner = ((((X - ax) / (ar - 3)) ** 2 + ((Y - ay) / (ar - 3)) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar - 3) & (Y > ay) & (Y < fl))
    frames_, meta = pxfx.load("forge-fire")
    before = sc.rgb.copy()
    for dx in (-62, 58):
        pxfx.blend(sc, frames_[(frame + (dx > 0) * 7) % len(frames_)], ax + dx, fl, meta["pivot"])
    sc.rgb[~inner] = before[~inner]
    sc.rgb[arch & ~inner] = hexc("#b8904a")
    for kk in range(-4, 5):                                           # the voussoirs: rivets round the arch
        a_ = np.pi * (0.5 + kk / 10)
        FU.rivet(sc, ax - np.cos(a_) * (ar + 5), ay - np.sin(a_) * (ar + 5))
    spr = leader_sprite(kind, L["k"])
    sc.blit(spr, int(ax - spr.ox), int(fl - 4 - spr.oy))
    sc.rgb[fl:fl + 3, ax - ar - 6:ax + ar + 7] = hexc("#5a5860")
    FU.sparks(sc, ax - 80, fl - 6, 10, seed=3 + frame // 3)
    FU.sparks(sc, ax + 84, fl - 10, 8, seed=4 + frame // 3)
    FU.cell(sc, 24, 358, 318, 398, "hi")
    letters(sc, L["name"], ax, 363, "title", 16, col=(255, 210, 140), align="center")
    letters(sc, L["epi"], ax, 380, "text", 16, col=BRASS, align="center")
    # its own cells: 7, three of them filled
    n = L["cells"]
    cw = (294 - (n - 1) * 4) / n
    for c in range(n):
        cx0 = int(round(24 + c * (cw + 4)))
        has = c < len(L["mods"])
        FU.cell(sc, cx0, 410, int(round(cx0 + cw)), 452, "normal" if has else "locked")
        if has:
            mod_icon(sc, L["mods"][c], cx0 + cw / 2 - 16, 415, 2)
    # the passport
    x0, x1 = 352, 612
    FU.plate(sc, 338, 52, 626, 462, seed=62)
    heading(sc, "ПАСПОРТ", x0, 62)
    H.fx_line(sc, x0, 90, "{лидер} лидерство " + L["lead"])
    y = 118
    heading(sc, "ТЕЛО", x0, y)
    y += 30
    for g, lab, val in L["body"]:
        a_ = H.glyph(sc, g, x0, y - 4, 2)
        letters(sc, lab, x0 + a_ + 8, y - 2, "text", 16, col=MUTED)
        lw = len(lab) * 8
        w, _ = H.fx_line(sc, 0, 0, val, draw=False)
        H.dots(sc, x0 + a_ + 14 + lw, x1 - w - 6, y + 10)
        H.fx_line(sc, x1 - w, y - 2, val)
        y += 21
    y += 6
    heading(sc, "ОРУЖИЕ", x0, y)
    y += 28
    for nm, dmg, extra, rng in L["weapons"]:
        letters(sc, nm, x0, y, "text", 16, col=GOLD)
        w, _ = H.fx_line(sc, 0, 0, "{дальность:" + rng + "}", draw=False)
        H.fx_line(sc, x1 - w, y, "{дальность:" + rng + "}")
        if alt:                                                        # Alt: the damage's kind said after its glyph
            import fxg
            dw, _ = H.fx_line(sc, x0 + 12, y + 19, dmg)
            ww = letters(sc, fxg.words(dmg).split(" ")[-1], x0 + 18 + dw, y + 21, "text", 16, col=(200, 178, 118))
            if extra:
                letters(sc, "· " + extra, x0 + 26 + dw + ww, y + 21, "text", 16, col=INK)
        else:
            H.fx_line(sc, x0 + 12, y + 19, dmg + ("" if not extra else " · " + extra))
        y += 42
    heading(sc, "С НИМ", x0, y)
    y += 26
    for j, (fr, mods) in enumerate(L["army"]):
        ck = ("army_big", fr)
        if ck not in _LEADERS:
            _LEADERS[ck] = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.95)
        g = _LEADERS[ck]
        sc.blit(g, int(x0 + 22 - g.ox), int(y + 64 - g.oy))
        letters(sc, fr, x0 + 52, y + 8, "text", 16, col=INK)
        for m_, key in enumerate(mods):
            FU.cell(sc, x0 + 52 + m_ * 40, y + 28, x0 + 88 + m_ * 40, y + 62, "normal")
            mod_icon(sc, key, x0 + 54 + m_ * 40, y + 29, 2)
    # the abilities
    rx0, rx1 = 646, WW - 26
    FU.plate(sc, 634, 52, 948, 462, seed=63)
    heading(sc, "СПОСОБНОСТИ", rx0, 62)
    y = 90 if not alt else 84
    for nm, when, line, col in L["abil"]:
        hh = 47
        if alt:                                                        # Alt held: the line said in words under it
            hh = H.alt_words(sc, rx0 + 6, y + 40, rx1 - rx0 - 8, line, draw=False) - y + 2 if "{" in line else 44
        FU.cell(sc, rx0 - 4, y, rx1 + 4, y + hh, "broken" if col == RED else ("hi" if col == GOLD else "normal"))
        letters(sc, nm, rx0 + 6, y + 4, "text", 16, col=col)
        letters(sc, when, rx1 - 4, y + 4, "text", 16, col=MUTED, align="right")
        if alt and "{" in line:
            H.fx_line(sc, rx0 + 6, y + 22, line)
            H.alt_words(sc, rx0 + 6, y + 40, rx1 - rx0 - 8, line)
        else:
            H.fx_line(sc, rx0 + 6, y + (24 if hh == 47 else 22), line)
        y += hh + 4
    if not alt:
        y += 2
        letters(sc, "развитие " + L["grow"][0], rx0, y, "text", 16, col=MUTED)
        letters(sc, L["grow"][1], rx0, y + 18, "text", 16, col=INK)
    FU.sill(sc, 468)
    action(sc, 12, 478, 220, 526, "Назад", "steel")
    action(sc, 640, 472, 948, 532, "ВЫБРАТЬ", "hot", big=True)
    if ret:
        return sc
    name = "foundry_alt.png" if alt else "foundry_leader_card.png"
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


# ---------------------------------------------------------------- after the battle
def damage_drawing(sc, frame, mods, key, x, y, K, pulse=1.0):
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
    sc.glow(pt[0], pt[1], 12, red, 0.5 * pulse)
    return pt


def stamp_falling(sc, x, y, text, scale=1.0, alpha=1.0):
    """The stamp coming down: drawn as it will land, then shown larger and fainter about its own centre — it falls
    onto the paper and lands at scale 1, full strength."""
    from PIL import Image
    tmp = sc.rgb.copy()
    stamp(sc, x, y, text)
    diff = np.abs(sc.rgb - tmp).sum(axis=2) > 1
    ys, xs = np.nonzero(diff)
    if not len(xs):
        return
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    patch = sc.rgb[y0:y1, x0:x1].copy()
    pm = diff[y0:y1, x0:x1]
    sc.rgb[:] = tmp
    if scale != 1.0:
        h, w = patch.shape[:2]
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        patch = np.asarray(Image.fromarray(patch.astype(np.uint8)).resize((nw, nh), Image.NEAREST)).astype(np.float32)
        pm = np.asarray(Image.fromarray(pm.astype(np.uint8) * 255).resize((nw, nh), Image.NEAREST)) > 127
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    px0, py0 = int(cx - patch.shape[1] / 2), int(cy - patch.shape[0] / 2)
    ya, yb = max(0, py0), min(sc.h, py0 + patch.shape[0])
    xa, xb = max(0, px0), min(sc.w, px0 + patch.shape[1])
    sub = pm[ya - py0:yb - py0, xa - px0:xb - px0]
    reg = sc.rgb[ya:yb, xa:xb]
    reg[sub] = reg[sub] * (1 - alpha) + patch[ya - py0:yb - py0, xa - px0:xb - px0][sub] * alpha


def stamp(sc, x, y, text, col="#e0503a"):
    """A rubber stamp on the drawing: red letters in a double red frame, a little worn."""
    w = SU.text_width(text, "text", 16) + 16
    c = hexc(col)
    for k in (0, 2):
        sc.rgb[y + k, x + k:x + w - k] = c
        sc.rgb[y + 23 - k, x + k:x + w - k] = c
        sc.rgb[y + k:y + 24 - k, x + k] = c
        sc.rgb[y + k:y + 24 - k, x + w - 1 - k] = c
    letters(sc, text, x + 8, y + 4, "text", 16, col=tuple(int(v) for v in c), outline=False, shadow=False)
    rng = np.random.default_rng(len(text))
    for _ in range(18):                                               # worn spots
        sx, sy = x + rng.integers(0, w), y + rng.integers(0, 22)
        sc.rgb[sy, sx] = hexc("#14243a")


def num_disc(sc, cx, cy, n, on=True):
    """A step's number on a work order: a brass disc struck with the digit, like a tool check."""
    X, Y = sc.xx - cx, sc.yy - cy
    d = np.hypot(X, Y)
    m = d <= 12.5
    t = np.clip((Y + 12) / 24, 0, 1)[..., None]
    a_, b_ = (hexc("#f0c878"), hexc("#8a6024")) if on else (hexc("#a8aab4"), hexc("#4a4a52"))
    sc.rgb[m] = (a_ * (1 - t) + b_ * t)[m]
    sc.rgb[m & (d > 11.2)] = SU.OUTL
    sc.occ[m] = True
    letters(sc, str(n), cx + 1, cy - 8, "title", 16, col=(52, 32, 12) if on else (30, 30, 36), outline=False,
            shadow=False, align="center")


def aftermath(anim=None, ret=False, variant=None):
    """Victory: what broke and what it cost, what the battle paid (a trophy, if the enemy was a machine), who did
    what; and what's next, as a work order — repair, the find, the workshop — with the purse after it."""
    import frames as F
    from swarm_effects import lit
    sc = screen(19)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "ПОБЕДА", "gears")
    metal(sc, 20, x=18)
    toolbar(sc)
    # broken: the damage report — the golem as a drawing, the part that broke in red, a red callout to it
    FU.plate(sc, 12, 52, 330, 462, seed=31)
    heading(sc, "ПОЛОМКИ", 26, 64)
    blueprint_sheet(sc, 22, 90, 320, 304)
    FU.cell(sc, 30, 98, 178, 134, "normal")
    slot_label(sc, "корпус: Мудрец", 38, 99)
    letters(sc, ROLE["Мудрец"], 38, 116, "text", 16, col=(170, 220, 250), outline=False)
    a_ = anim or {}
    pt = damage_drawing(sc, "Мудрец", {"chain": 1, "fireball": 1, "overload": 2}, "overload", 236, 292, 2.4,
                        pulse=a_.get("pulse", 1.0))
    if "stamp" not in a_:
        stamp(sc, 32, 268, "В РЕМОНТ")
    elif a_["stamp"] is not None:
        stamp_falling(sc, 32, 268, "В РЕМОНТ", *a_["stamp"])
    lane = 160
    callout(sc, pt, (lane, 314), col=hexc("#ff6a4a"), lane=lane)
    FU.cell(sc, 22, 314, 320, 378, "broken")
    slot_label(sc, "спина", 32, 316, col=(230, 150, 130))
    mod_icon(sc, "overload", 32, 338, 2)
    letters(sc, "Перегрузка", 74, 334, "text", 16, col=INK)
    H.fx_line(sc, 74, 354, "{модуль:II} ⇒ {модуль:I}")
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
    if variant == "trophy":                                          # a machine beaten: its part, ours to keep or melt
        sc.glow(386, 225, 26, hexc("#e0b860"), 0.35)
        FU.cell(sc, 358, 200, 410, 250, "normal")
        mod_icon(sc, "dome", 368, 209, 2)
        letters(sc, "Щит-купол", 420, 200, "text", 16, col=GOLD)
        letters(sc, "трофей", 604, 200, "text", 16, col=MUTED, align="right")
        H.fx_line(sc, 420, 226, "в ящик · или {металл:+5}")
    else:
        letters(sc, "трофей: нет — враг живой", 364, 202, "text", 16, col=MUTED)
        H.fx_line(sc, 364, 226, "{машина} → {модуль} · {металл}", dim=True)
    heading(sc, "КТО ЧТО", 354, 272)
    for j, (fr, kills, dmg_) in enumerate((("Страж", 6, 31), ("Мудрец", 12, 40), ("Орудие", 17, 12), ("Механик", 0, 3))):
        y = 298 + j * 40
        ck = ("who", fr)
        if ck not in _LEADERS:
            _LEADERS[ck] = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.42)
        g = _LEADERS[ck]
        sc.blit(g, int(374 - g.ox), int(y + 34 - g.oy))
        letters(sc, fr, 400, y + 4, "text", 16, col=INK)
        H.fx_line(sc, 500, y + 2, f"{{убийство:{kills}}}")
        H.fx_line(sc, 566, y + 2, f"{{рана:{dmg_}}}")
    # what next
    FU.plate(sc, 650, 52, 948, 462, seed=33)
    heading(sc, "ДАЛЬШЕ", 664, 64)
    letters(sc, "наряд в мастерскую", 934, 68, "text", 16, col=MUTED, align="right")
    # the work order: its steps in the order the workshop takes them
    y = 94
    FU.cell(sc, 660, y, 940, y + 92, "broken")                        # 1 — the repair
    num_disc(sc, 678, y + 16, 1)
    letters(sc, "РЕМОНТ", 696, y + 9, "title", 16, col=(240, 160, 130), col2=(110, 40, 30))
    FU.cell(sc, 670, y + 34, 716, y + 80, "locked")
    mod_icon(sc, "overload", 677, y + 41, 2)
    letters(sc, "Мудрец · Перегрузка", 726, y + 36, "text", 16, col=INK)
    H.fx_line(sc, 726, y + 58, "{модуль:II} ⇒ {модуль:I} · {металл:2}")
    y += 100
    FU.cell(sc, 660, y, 940, y + 104, "new")                          # 2 — the find: three crates, shut
    num_disc(sc, 678, y + 16, 2)
    letters(sc, "НАХОДКА", 696, y + 9, "title", 16, col=(170, 220, 250), col2=(30, 70, 110))
    H.fx_line(sc, 830, y + 8, "{выбор:1 из 3}")
    for j in range(3):
        bx = 674 + j * 88
        FU.cell(sc, bx, y + 36, bx + 78, y + 94, "locked")
        for k in range(y + 46, y + 92, 8):                            # the crate's boards
            sc.rgb[k, bx + 6:bx + 72] = sc.rgb[k, bx + 6:bx + 72] * 0.7 + hexc("#4a3a24") * 0.3
        letters(sc, "?", bx + 39, y + 50, "title", 24, col=(150, 200, 230), col2=(30, 70, 110), align="center")
    y += 112
    FU.cell(sc, 660, y, 940, y + 84, "normal")                        # 3 — the workshop: what else can be done
    num_disc(sc, 678, y + 16, 3, on=False)
    letters(sc, "МАСТЕРСКАЯ", 696, y + 9, "title", 16, col=INK, col2=(60, 60, 70))
    letters(sc, "голем · деталь · переплавка", 672, y + 36, "text", 16, col=MUTED)
    H.fx_line(sc, 672, y + 56, "или пропуск → {металл:+4}", dim=True)
    y += 92
    H.fx_line(sc, 664, y + 4, "{металл:20} → после ремонта {металл:18}")
    FU.sill(sc, 468)
    action(sc, 650, 474, 948, 530, "В МАСТЕРСКУЮ", "hot", big=True)
    if ret:
        return sc
    name = "foundry_aftermath_trophy.png" if variant == "trophy" else "foundry_aftermath.png"
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


# ---------------------------------------------------------------- the battle, seen from the Foundry
# ---------------------------------------------------------------- «?»: the glossary, as the Foundry's own journal
GLOSS = ["Когда", "Время", "Что делает", "Состояния", "Тело", "Мастерская", "Враги", "Урон"]   # no brood for golems


def foundry_uses(key, limit=4, width=270):
    """Where a term is met in the Foundry: its modules' lines, its parts', its leader's abilities —
    (icon or None, whose, line)."""
    import golem_parts as GP
    src = [(("mod", k), IC.ICONS[k][1], rows) for k, rows in MOD_FX.items() if k in IC.ICONS]
    names = {**{k: v[0] for k, v in GP.ARMS.items()}, **GP.LEGS, **{k: v[0] for k, v in GP.HEADS.items()}}
    src += [(None, names.get(k, k), rows) for k, rows in PART_FX.items()]
    for L in LEADER_FULL.values():
        src += [(None, nm, [ln]) for nm, _, ln, _ in L["abil"]]
    out_, seen = [], set()
    for ic, who, rows in src:
        for ln in rows:
            if ("{" + key + "}" in ln or "{" + key + ":" in ln) and who not in seen:
                w_, _ = H.fx_line(None, 0, 0, ln, draw=False)
                if w_ <= width:
                    out_.append((ic, who, ln))
                    seen.add(who)
                    break
        if len(out_) >= limit:
            break
    return out_


def glossary(chapter="Когда", term="атака"):
    """«?» in the Foundry: the glyphs by chapter on iron plates; the chosen one large on a sheet of blueprint, its
    meaning, and where the Foundry meets it — modules with their icons, parts, the leader's abilities."""
    import fxg
    sc = screen(91)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "СПРАВОЧНИК", "wrench")
    toolbar(sc, on=True)
    groups = dict(fxg.GROUPS)
    FU.plate(sc, 12, 52, 196, 462, seed=71)                            # the chapters
    for i, ch in enumerate(GLOSS):
        keys = groups[ch]
        y0 = 60 + i * 49
        on = ch == chapter
        FU.cell(sc, 20, y0, 188, y0 + 43, "hi" if on else "normal")
        a_ = fxg.rgba(keys[0])
        fxg.draw(sc, keys[0], 30 + (22 - a_.shape[1] * 2) // 2, y0 + 22 - a_.shape[0], 2)
        cw_ = letters(sc, ch, 60, y0 + 13, "text", 16, col=GOLD if on else INK)
        letters(sc, str(len(keys)), 68 + cw_, y0 + 13, "text", 16, col=MUTED)
    keys = groups[chapter]                                             # the chapter's glyphs, two columns
    FU.plate(sc, 206, 52, 624, 462, seed=72)
    heading(sc, chapter.upper(), 220, 62)
    half = (len(keys) + 1) // 2
    for j, k_ in enumerate(keys):
        x0, y0 = 218 + (j // half) * 202, 92 + (j % half) * 36
        if k_ == term:
            FU.cell(sc, x0 - 6, y0 - 6, x0 + 196, y0 + 30, "hi")
        a_ = fxg.rgba(k_)
        H.glyph(sc, k_, x0 + (26 - a_.shape[1] * 2) // 2, y0 + 12 - a_.shape[0], 2)
        letters(sc, fxg.TERMS[k_][0], x0 + 34, y0 + 4, "text", 16, col=GOLD if k_ == term else INK)
    nm, what, _ = fxg.TERMS[term]                                      # the chosen one, on the drawing
    FU.plate(sc, 634, 52, 948, 462, seed=73)
    blueprint_sheet(sc, 644, 62, 938, 162, stamp=None)
    a_ = fxg.rgba(term)
    gx, gy = 680 - a_.shape[1] * 2, 112 - a_.shape[0] * 2
    sc.rgb[gy - 8, gx:gx + a_.shape[1] * 4] = hexc("#9ad8ff")      # a dimension line over it, as on a drawing
    sc.rgb[gy - 11:gy - 5, gx] = hexc("#9ad8ff")
    sc.rgb[gy - 11:gy - 5, gx + a_.shape[1] * 4 - 1] = hexc("#9ad8ff")
    fxg.draw(sc, term, gx, gy, 4)
    letters(sc, nm.upper(), 724, 92, "title", 16, col=(170, 220, 250), col2=(40, 80, 120))
    letters(sc, "лист " + str(GLOSS.index(chapter) + 1) + "." + str(keys.index(term) + 1), 724, 116, "text", 16,
            col=(110, 160, 200), outline=False)
    y = 174
    for ln in H.wrap(what[:1].upper() + what[1:], 280):
        SU.rich(sc, ln, 648, y, "text", 16, col=INK)
        y += 18
    y += 12
    letters(sc, "встречается", 648, y, "text", 16, col=MUTED)
    y += 22
    for ic, who, ln in foundry_uses(term, 4, 280):
        if ic:
            mod_icon(sc, ic[1], 648, y - 1, 1)
        letters(sc, who, 648 + (22 if ic else 0), y, "text", 16, col=GOLD)
        H.fx_line(sc, 656, y + 20, ln)
        y += 50
    FU.sill(sc, 468)
    action(sc, 12, 478, 240, 526, "Закрыть", "steel")
    kw = H.keycap(sc, 420, 492, "Alt")
    letters(sc, "— подписи под значками", 428 + kw, 493, "text", 16, col=MUTED)
    img = sc.image(S)
    img.save(out("foundry_glossary.png"))
    print("foundry_glossary.png", img.size)


def confirm(sc, title_, rows, yes, items=()):
    """Asking first, only where something is gone for good (a module into the crucible, the leader's growth, the
    finds left behind): the screen dims, an iron plate says what goes — its icons, lines of glyphs — and two
    controls: the lever with the cast plate that does it (Enter), the push-button back (Esc)."""
    sc.rgb[:] = sc.rgb * 0.38
    w = 480
    x0 = WW // 2 - w // 2
    hh = H.fx_rows(sc, 0, 0, w - 48, rows, draw=False)
    ih = 64 if items else 0
    y0 = HH // 2 - (78 + ih + hh + 68) // 2 - 10
    y1 = y0 + 78 + ih + hh + 68
    FU.plate(sc, x0, y0, x0 + w, y1, seed=77)
    FU.wing(sc, x0 + 4, y0 + 4, x0 + w - 4, y0 + 44)
    tw = SU.text_width(title_, "title", 16)
    letters(sc, title_, WW // 2 - tw // 2, y0 + 16, "title", 16, col=GOLD, col2=(130, 90, 40))
    y = y0 + 60
    for j, (key, lvl, st) in enumerate(items):                       # what goes in, an arrow, what it gives
        ix = WW // 2 - len(items) * 40 + 19 + j * 80
        if j:
            letters(sc, "→", ix - 24, y + 12, "title", 16, col=(255, 170, 80), col2=(120, 40, 10), align="center")
        FU.cell(sc, ix, y, ix + 42, y + 42, st)
        mod_icon(sc, key, ix + 5, y + 5, 2)
        if lvl:
            letters(sc, lvl, ix + 21, y + 43, "text", 16, col=BRASS, outline=False, align="center")
    y += ih
    H.fx_rows(sc, x0 + 24, y + 6, w - 48, rows)
    by = y1 - 66
    action(sc, x0 + 16, by + 8, x0 + 170, by + 56, "Назад", "steel")
    action(sc, x0 + 186, by + 2, x0 + w - 16, by + 62, yes, "hot", big=True)
    return sc


def confirm_smelt():
    """The crucible's question: the Canister into the melt for the Long barrel's second level."""
    sc = smelt(base_only=True)
    H.HOVER.clear()
    confirm(sc, "В ТИГЕЛЬ НАВСЕГДА?", ["{модуль} Картечь I → тигель · не вернуть",
                                         "Длинный ствол {модуль:I} ⇒ {модуль:II}", "{металл:14} → {металл:11}"],
            "ПЕРЕПЛАВИТЬ", items=(("canister", "I", "broken"), ("long", "I → II", "hi")))
    H.cursor(sc, 640, 360)
    img = sc.image(S)
    img.save(out("foundry_confirm.png"))
    print("foundry_confirm.png", img.size)


# ---------------------------------------------------------------- settings: the screen, the interface's size, sound, keys
SETTINGS = [("screen", "ЭКРАН"), ("sound", "ЗВУК"), ("game", "ИГРА"), ("keys", "КЛАВИШИ")]


def ui_icon(sc, key, x, y, z=2):
    import icons_drawn as D
    rgba = np.repeat(np.repeat(D.UI[key](), z, 0), z, 1)
    m = rgba[..., 3] > 0
    sc.rgb[y:y + rgba.shape[0], x:x + rgba.shape[1]][m] = rgba[..., :3][m]


def scale_preview(sc, x0, y0, w, h, frac, chosen=False, label=""):
    """A little monitor showing how much of the screen the interface takes at a scale: the workshop shrunk to
    frac of the screen's width, the forge wall round it where the canvas grew."""
    from PIL import Image
    FU.cell(sc, x0 - 6, y0 - 6, x0 + w + 6, y0 + h + 6, "hi" if chosen else "normal")
    wall = FU.forge(w, h, 3)
    sc.rgb[y0:y0 + h, x0:x0 + w] = wall.rgb * 0.8
    shot = Image.open(out("foundry_workshop.png")).convert("RGB")
    tw, th = int(round(w * frac)), int(round(h * frac))
    small = np.asarray(shot.resize((tw, th), Image.BOX)).astype(float)
    ox, oy = x0 + (w - tw) // 2, y0 + (h - th) // 2
    sc.rgb[oy:oy + th, ox:ox + tw] = small
    if label:
        letters(sc, label, x0 + w // 2, y0 + h + 10, "text", 16, col=GOLD if chosen else MUTED, align="center")


def settings(section="screen", ret=False, anim=None):
    """Settings, in the forge's metal: the sections on iron cells on the left, the chosen one's rows on the right —
    each a label and its control: a brass block in a notched groove for a choice, the same groove filled with
    molten metal for a level, a tumbler with its lamp for on and off, arrows round an enamel window for a list.
    On ЭКРАН the interface's size: whole steps of the scale, the ones this screen can't take crossed out, and
    two little monitors showing how much of the screen the interface takes."""
    sc = screen(57)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "НАСТРОЙКИ", "calipers")
    toolbar(sc)
    FU.plate(sc, 12, 52, 196, 462, seed=91)
    for i, (key, nm) in enumerate(SETTINGS):
        y0 = 62 + i * 52
        on = key == section
        FU.cell(sc, 20, y0, 188, y0 + 44, "hi" if on else "normal")
        ui_icon(sc, key, 30, y0 + 6, 2)
        letters(sc, nm, 70, y0 + 14, "text", 16, col=GOLD if on else INK)
    FU.plate(sc, 206, 52, 948, 462, seed=92)
    heading(sc, dict(SETTINGS)[section], 222, 62)
    lab = lambda t, y, sub=None: (letters(sc, t, 224, y - 8, "text", 16, col=INK),
                                  sub and letters(sc, sub, 224, y + 10, "text", 16, col=MUTED))
    if section == "screen":
        lab("Режим окна", 104)
        FU.notch_slider(sc, 430, 690, 104, 3, 2, ["окно", "без рамки", "весь экран"])
        lab("Разрешение", 158)
        FU.chooser(sc, 430, 690, 158, "2560 × 1440")
        sc.rgb[184, 222:934] = sc.rgb[184, 222:934] * 0.5 + hexc("#8a6a34") * 0.5
        letters(sc, "Масштаб интерфейса", 224, 196, "text", 16, col=GOLD)
        letters(sc, "крупнее или мельче —", 224, 216, "text", 16, col=MUTED)
        letters(sc, "целыми шагами,", 224, 234, "text", 16, col=MUTED)
        letters(sc, "пиксели ровные", 224, 252, "text", 16, col=MUTED)
        a_ = anim or {}
        sv = a_.get("scale", 1.0)                                       # the block's place: 0 = ×1, 1 = ×2
        FU.notch_slider(sc, 430, 690, 214, 4, sv, ["×1", "×2", "×3", "×4"], off=(2, 3))
        letters(sc, "мельче", 430, 254, "text", 16, col=MUTED)
        letters(sc, "крупнее", 690, 254, "text", 16, col=MUTED, align="right")
        H.fx_line(sc, 430, 280, "на этом экране: ×1 или ×2")
        letters(sc, "×3 и ×4 не помещаются", 430, 300, "text", 16, col=PALE)
        scale_preview(sc, 730, 200, 176, 99, 0.375 + 0.375 * sv, True, "")
        letters(sc, "×2: холст 1280 × 720" if sv >= 0.5 else "×1: холст 2560 × 1440", 818, 312, "text", 16,
                col=GOLD, align="center")
        sc.rgb[332, 222:934] = sc.rgb[332, 222:934] * 0.5 + hexc("#8a6a34") * 0.5
        lab("Вертикальная синхронизация", 356)
        on = a_.get("vsync", True)
        FU.toggle(sc, 470, 356, on)
        letters(sc, "вкл" if on else "выкл", 496, 348, "text", 16, col=INK if on else MUTED)
        lab("Частота кадров", 412)
        FU.notch_slider(sc, 430, 690, 404, 4, 3, ["60", "120", "144", "без предела"])
    elif section == "sound":
        for j, (nm, v) in enumerate((("Общая громкость", 8), ("Музыка", 6), ("Звуки боя", 9), ("Интерфейс", 7))):
            y = 110 + j * 56
            lab(nm, y)
            FU.notch_slider(sc, 430, 820, y, 11, v, melt=True)
            letters(sc, str(v * 10), 900, y - 8, "text", 16, col=GOLD, align="right")
        lab("Звук в фоне", 352, "когда окно не в фокусе")
        FU.toggle(sc, 470, 352, False)
        letters(sc, "выкл", 496, 344, "text", 16, col=MUTED)
    elif section == "game":
        lab("Скорость боя", 104, "с какой начинается бой")
        FU.notch_slider(sc, 430, 690, 104, 3, 1, ["×1", "×2", "×4"])
        lab("Подсказки", 170, "задержка")
        FU.notch_slider(sc, 430, 690, 170, 3, 1, ["сразу", "0,3 с", "0,6 с"])
        lab("Подписи значков", 236)
        FU.notch_slider(sc, 430, 690, 236, 3, 0, ["держать Alt", "Alt включает", "всегда"])
        lab("Язык", 300)
        FU.chooser(sc, 430, 690, 300, "Русский")
        lab("Тряска экрана", 352)
        FU.toggle(sc, 470, 352, True)
        letters(sc, "вкл", 496, 344, "text", 16, col=INK)
        lab("Вспышки ударов", 400)
        FU.toggle(sc, 470, 400, True)
        letters(sc, "вкл", 496, 392, "text", 16, col=INK)
    else:
        rows = [("Пауза", "Пробел"), ("Скорость боя", "Tab"), ("Бой — в конец", "End"), ("Подписи значков", "Alt"),
                ("Справочник", "F1"), ("Главное действие", "Enter"), ("Назад, закрыть", "Esc")]
        for j, (nm, key) in enumerate(rows):
            y = 100 + j * 44
            hot = j == 3
            FU.cell(sc, 216, y - 18, 938, y + 18, "hover" if hot else "normal")
            letters(sc, nm, 230, y - 8, "text", 16, col=GOLD if hot else INK)
            if hot:
                letters(sc, "нажмите клавишу…", 700, y - 8, "text", 16, col=(255, 200, 140), align="right")
            else:
                H.keycap(sc, 560, y - 10, key)
        letters(sc, "клавиша, занятая другим, подсвечивается красным", 222, 440, "text", 16, col=MUTED)
    FU.sill(sc, 468)
    action(sc, 12, 478, 200, 526, "Назад", "steel")
    action(sc, 210, 478, 420, 526, "По умолчанию", "rust")
    action(sc, 640, 472, 948, 532, "ПРИМЕНИТЬ", "hot", big=True)
    if ret:
        return sc
    name = "foundry_settings.png" if section == "screen" else f"foundry_settings_{section}.png"
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


def pause(ret=False):
    """Pause, over the battle: the field dimmed, an iron plate in the middle — the run's place in a line, then
    the big plate to carry on and the rest on push-buttons: settings, the glossary, give up the run, out to the
    menu, quit."""
    sc = battle_view("run", ret=True)
    sc.rgb[:] = sc.rgb * 0.36
    x0, y0, x1, y1 = 330, 96, 630, 444
    FU.plate(sc, x0, y0, x1, y1, seed=95)
    FU.wing(sc, x0 + 4, y0 + 4, x1 - 4, y0 + 44)
    tw = SU.text_width("ПАУЗА", "title", 24)
    letters(sc, "ПАУЗА", (x0 + x1) // 2 - tw // 2, y0 + 12, "title", 24, col=(232, 222, 206), col2=(120, 96, 70))
    H.fx_line(sc, x0 + 24, y0 + 58, "бой 5 из 15 · ход 5 · {металл:14}")
    action(sc, x0 + 16, y0 + 86, x1 - 16, y0 + 144, "ПРОДОЛЖИТЬ", "hot", big=True)
    for j, (t, kind) in enumerate((("Настройки", "steel"), ("Справочник · F1", "steel"), ("Сдаться", "rust"),
                                   ("Выйти в меню", "steel"), ("Выйти из игры", "dull"))):
        yy = y0 + 160 + j * 36
        action(sc, x0 + 24, yy, x1 - 24, yy + 30, t, kind)
    letters(sc, "Esc — продолжить", (x0 + x1) // 2, y1 - 22, "text", 16, col=MUTED, align="center")
    if ret:
        return sc
    img = sc.image(S)
    img.save(out("foundry_pause.png"))
    print("foundry_pause.png", img.size)


# ---------------------------------------------------------------- the leader grows: the assembly dock
def shoulder_battery(sc, x0, y0, k=1.0):
    """A colossal module, the shoulder battery: a riveted iron box of six rocket tubes, their red warheads in
    the mouths, brass bands, the mounting bracket under it."""
    w, h = int(74 * k), int(46 * k)
    box = (sc.xx >= x0) & (sc.xx < x0 + w) & (sc.yy >= y0) & (sc.yy < y0 + h)
    sh = np.roll(np.roll(box, 4, 0), 3, 1) & ~box
    sc.rgb[sh] *= 0.45
    FU._bands(sc, box, FU.IRON, 0.72 - (sc.yy - y0) / 70.0 - (sc.xx - x0) / 300.0)
    for bx in (x0 + int(22 * k), x0 + int(48 * k)):
        sc.rgb[y0:y0 + h, bx:bx + 3] = hexc("#a0782c")                       # brass bands
        sc.rgb[y0:y0 + h, bx] = hexc("#d0a848")
    for r in range(2):
        for c in range(3):
            cx, cy = x0 + int((12 + c * 25) * k), y0 + int((13 + r * 20) * k)
            d = np.hypot(sc.xx - cx, sc.yy - cy)
            sc.rgb[d <= 8 * k] = hexc("#5e5c66")
            sc.rgb[d <= 6.5 * k] = hexc("#08070a")
            sc.rgb[d <= 3.2 * k] = hexc("#c0402e")                            # the warhead in the mouth
            sc.rgb[(d <= 1.6 * k) & (sc.yy < cy)] = hexc("#f08060")
            sc.rgb[(np.abs(d - 7.4 * k) < 0.6) & (sc.yy < cy) & (sc.xx < cx)] = hexc("#8e8c96")
    br = (sc.xx >= x0 + int(24 * k)) & (sc.xx < x0 + int(50 * k)) & (sc.yy >= y0 + h) & (sc.yy < y0 + h + int(10 * k))
    FU._bands(sc, br, FU.IRON, 0.5 - (sc.yy - (y0 + h)) / 20.0)
    for x, y in ((x0 + 4, y0 + 4), (x0 + w - 5, y0 + 4), (x0 + 4, y0 + h - 5), (x0 + w - 5, y0 + h - 5)):
        FU.rivet(sc, x, y)
    o, top, _ = SU.edges(box | br)
    sc.rgb[top] = hexc("#8e8c96")
    sc.rgb[o] = SU.OUTL
    return (x0 + 6, y0), (x0 + w - 7, y0)


def development(kind="colossus", hot="cell", ret=False, anim=None):
    """The leader grows, after a boss — not a menu but the assembly dock: the leader stands on its plinth between
    two riveted columns under a girder that runs over the whole dock. Left, the riveting bench: a plate of its hull
    with its cells in a row and the new one red-hot, being riveted in, sparks off the rivet gun. Right, a crane
    trolley on the girder lowering a colossal module on chains. Under each, its own lever: pull one."""
    import frames as F
    sc = screen(63)
    FU.wing(sc, 0, 0, WW, 44)
    title_center(sc, "РАЗВИТИЕ", "anvils")
    toolbar(sc)
    FU.i_beam(sc, 0, 50, WW, 66)                                              # the girder over the dock
    for x in (318, 626):
        FU.i_beam(sc, x, 66, x + 16, 452, vertical=True)                      # the columns
    for x0, x1 in ((334, 380), (580, 626)):                                   # braces
        for k in range(40):
            t = k / 39
            xx = int(x0 + (x1 - x0) * t) if x0 == 334 else int(x1 - (x1 - x0) * t)
            sc.rgb[66 + int(t * 46):68 + int(t * 46), xx] = hexc("#3a3842")
    # the leader on its plinth, the dock's glow on it from below
    sc.glow(480, 430, 120, hexc("#ff8a3a"), 0.18)
    sc.rgb[440:452, 360:600] = hexc("#24222a")
    sc.rgb[440, 360:600] = hexc("#6a6870")
    sc.rgb[451, 360:600] = SU.OUTL
    for x in range(368, 600, 16):
        FU.rivet(sc, x, 446)
    name, kk, nopt = DEV_LEADER[kind]
    spr = leader_sprite(kind, kk)
    sc.blit(spr, int(480 - spr.ox), int(440 - spr.oy))
    FU.cell(sc, 380, 74, 580, 112, "hi")
    letters(sc, name, 480, 80, "text", 16, col=GOLD, align="center")
    letters(sc, f"после босса — 1 из {nopt}", 480, 96, "text", 16, col=MUTED, align="center")
    if kind != "colossus":
        DEV_SCENE[kind](sc, hot)
        if ret:
            return sc
        img = sc.image(S)
        img.save(out(f"foundry_development_{kind}.png"))
        print(f"foundry_development_{kind}.png", img.size)
        return
    # left: the riveting bench — the hull's cells, the new one being riveted in
    hot_l, hot_r = hot == "cell", hot == "module"
    sc.rgb[338:350, 20:300] = hexc("#2a2830")                                 # the bench top
    sc.rgb[338, 20:300] = hexc("#6a6870")
    for x in (34, 286):
        sc.rgb[350:420, x - 4:x + 4] = hexc("#1c1a20")                        # its legs
    FU.plate(sc, 26, 230, 296, 336, seed=71)
    letters(sc, "КОРПУС КОЛОССА", 40, 240, "title", 16, col=(150, 200, 230), col2=(40, 80, 120))
    mods = ("plates", "flail", "magnet", None, None, None, None, "new")
    for c, key in enumerate(mods):
        cx0 = 38 + c * 31
        st = "new" if key == "new" else ("normal" if key else "locked")
        FU.cell(sc, cx0, 270, cx0 + 27, 297, "hover" if key == "new" and hot_l else st)
        if key and key != "new":
            mod_icon(sc, key, cx0 + 6, 275, 1)
    letters(sc, "7 → 8", 162, 306, "text", 16, col=(170, 220, 250), align="center")
    fr_ = (anim or {}).get("frame", 0)
    if fr_ % 8 < 5:                                                          # the rivet gun at work, in bursts
        FU.sparks(sc, 262, 276, 12, seed=7 + fr_)
        sc.glow(262, 283, 10, hexc("#ffb060"), 0.5)
    sc.rgb[214:226, 250:288] = hexc("#5e5c66")                               # the rivet gun, hung over it
    sc.rgb[214, 250:288] = hexc("#8e8c96")
    sc.rgb[226:262, 266:272] = hexc("#3a3842")
    sc.rgb[262:268, 264:274] = hexc("#c8a060")
    sc.rgb[66:214, 268:270] = hexc("#24222a")                                # its hose up to the girder
    FU.cell(sc, 24, 120, 300, 212, "hi" if hot_l else "normal")
    letters(sc, "+1 ЯЧЕЙКА", 40, 130, "title", 16, col=(255, 210, 140) if hot_l else GOLD, col2=(130, 90, 40))
    H.fx_line(sc, 40, 156, "{модуль:+1} место на Колоссе")
    letters(sc, "клепают в корпус", 40, 180, "text", 16, col=MUTED)
    # right: the crane lowering a colossal module
    sc.rgb[66:80, 770:820] = hexc("#3a3842")                                 # the trolley on the girder
    sc.rgb[66, 770:820] = hexc("#6a6870")
    FU.rivet(sc, 778, 72)
    FU.rivet(sc, 812, 72)
    sway = int(round(2.4 * np.sin(fr_ * 2 * np.pi / 24)))                   # the battery swinging on its chains
    (ax, ay), (bx, by) = shoulder_battery(sc, 742 + sway, 262, 1.45)
    for (cx, cy) in ((ax, ay), (bx, by)):
        FU.chain(sc, cx, 80, cy)
    letters(sc, "плечевая батарея", 795, 360, "text", 16, col=INK, align="center")
    FU.cell(sc, 660, 120, 936, 230, "hi" if hot_r else "normal")
    letters(sc, "КОЛОССАЛЬНЫЙ", 676, 130, "title", 16, col=(255, 210, 140) if hot_r else GOLD, col2=(130, 90, 40))
    letters(sc, "МОДУЛЬ", 676, 152, "title", 16, col=(255, 210, 140) if hot_r else GOLD, col2=(130, 90, 40))
    H.fx_line(sc, 676, 178, "{каждые:3} → ×6 {огонь} {площадь}")
    letters(sc, "шесть ракет · только Колосс", 676, 202, "text", 16, col=MUTED)
    FU.sill(sc, 468)
    action(sc, 20, 472, 310, 532, "+1 ЯЧЕЙКА", "hot", big=True, heated=hot_l)
    action(sc, 650, 472, 940, 532, "МОДУЛЬ", "hot", big=True, heated=hot_r)
    letters(sc, "выбор навсегда", 480, 492, "text", 16, col=MUTED, align="center")
    if ret:
        return sc
    img = sc.image(S)
    img.save(out("foundry_development.png"))
    print("foundry_development.png", img.size)


DEV_LEADER = {"colossus": ("ОТЕЦ КОЛОССА", 3.5, 2), "inventor": ("ИЗОБРЕТАТЕЛЬ", 5.0, 2),
              "maniac": ("МАНЬЯК", 3.6, 2), "zodchiy": ("ЗОДЧИЙ", 2.6, 3)}


def option_card(sc, x0, y0, x1, y1, title_lines, line, sub, hot):
    """What a choice in the dock gives: its name in brass letters, its line, a word on how it's done."""
    FU.cell(sc, x0, y0, x1, y1, "hi" if hot else "normal")
    col = (255, 210, 140) if hot else GOLD
    y = y0 + 10
    for t in title_lines:
        letters(sc, t, x0 + 16, y, "title", 16, col=col, col2=(130, 90, 40))
        y += 22
    H.fx_line(sc, x0 + 16, y + 4, line)
    letters(sc, sub, x0 + 16, y + 28, "text", 16, col=MUTED)


def bench(sc, x0, x1, y=338):
    sc.rgb[y:y + 12, x0:x1] = hexc("#2a2830")
    sc.rgb[y, x0:x1] = hexc("#6a6870")
    for x in (x0 + 14, x1 - 14):
        sc.rgb[y + 12:y + 82, x - 4:x + 4] = hexc("#1c1a20")


def trolley(sc, x):
    sc.rgb[66:80, x - 25:x + 25] = hexc("#3a3842")
    sc.rgb[66, x - 25:x + 25] = hexc("#6a6870")
    FU.rivet(sc, x - 17, 72)
    FU.rivet(sc, x + 17, 72)


def dev_inventor(sc, hot):
    """The Inventor grows: left, a test bench with a new augment under a canvas sheet and its drawing pinned up
    beside the three it has; right, a small golem hung on a lift while a drill bores a second augment socket in
    its shoulder."""
    import frames as F
    hl, hr = hot in ("cell", "type"), hot in ("module", "more")
    option_card(sc, 24, 120, 300, 230, ["НОВЫЙ ВИД", "АУГМЕНТОВ"], "{модуль} новый — в мастерской", "испытательный стенд", hl)
    blueprint_sheet(sc, 40, 240, 284, 300)
    for j, k_ in enumerate(("a_coil", "a_mirror", "a_spring")):
        mod_icon(sc, k_, 56 + j * 46, 254, 2)
    FU.cell(sc, 194, 250, 236, 292, "new")
    letters(sc, "?", 215, 258, "title", 24, col=(170, 220, 250), col2=(30, 70, 110), align="center")
    bench(sc, 20, 300)
    cloth = (sc.xx >= 70) & (sc.xx < 250) & (sc.yy >= 290 + np.abs(sc.xx - 160) * 0.35) & (sc.yy < 338)
    FU._bands(sc, cloth, ("#3a3020", "#6a5a3c", "#a08a5e", "#c8b48a", "#ece2c8"), 0.85 - (sc.yy - 290) / 70.0)
    for fx in (110, 150, 195):                                                # the canvas's folds
        for yy in range(305, 337):
            if cloth[yy, fx + (yy - 305) // 6]:
                sc.rgb[yy, fx + (yy - 305) // 6] = hexc("#6a5a3c")
    o, _, _ = SU.edges(cloth)
    sc.rgb[o] = SU.OUTL
    sc.glow(160, 320, 40, hexc("#9ad8ff"), 0.2)                              # something glowing under it
    trolley(sc, 795)
    for cx in (765, 825):
        FU.chain(sc, cx, 80, 300)
    sc.rgb[300:308, 750:842] = hexc("#3a3842")                               # the lift's platform
    sc.rgb[300, 750:842] = hexc("#6a6870")
    g = F.build("Мудрец", "idle", k=F.FRAMES["Мудрец"][0] * 1.15)
    sc.blit(g, int(795 - g.ox), int(300 - g.oy))
    FU.cell(sc, 696, 236, 724, 264, "normal")                                # its augment sockets, by it
    mod_icon(sc, "a_coil", 702, 242, 1)
    FU.cell(sc, 696, 270, 724, 298, "hover" if hr else "new")
    sc.rgb[282:286, 652:690] = hexc("#5e5c66")                               # the drill boring the new one
    sc.rgb[283:285, 690:696] = hexc("#b0b4bc")
    sc.rgb[278:290, 636:652] = hexc("#a0782c")
    FU.sparks(sc, 700, 284, 8, seed=11)
    option_card(sc, 660, 120, 936, 222, ["+1 АУГМЕНТ"], "{свой} аугментов: 1 → 2", "на каждого голема", hr)
    FU.sill(sc, 468)
    action(sc, 20, 472, 310, 532, "НОВЫЙ ВИД", "hot", big=True, heated=hl)
    action(sc, 650, 472, 940, 532, "+1 АУГМЕНТ", "hot", big=True, heated=hr)
    letters(sc, "выбор навсегда", 480, 492, "text", 16, col=MUTED, align="center")


def dev_maniac(sc, hot):
    """The Maniac grows: left, a crane's electromagnet hauling a crate taped in hazard stripes out of a heap of
    scrap — a new mad module; right, the dial of his quirks, purple for the dangerous, green for the useful, a
    spanner on its adjusting screw opening the green wider."""
    hl, hr = hot in ("cell", "module_new"), hot in ("module", "quirks")
    option_card(sc, 24, 120, 300, 222, ["БЕЗУМНЫЙ МОДУЛЬ"], "{модуль} новый безумный", "из лома", hl)
    rnd = np.random.RandomState(9)
    for _ in range(26):                                                       # the scrapheap
        x0, y0 = int(rnd.uniform(30, 280)), int(rnd.uniform(380, 444))
        w, h = int(rnd.uniform(10, 30)), int(rnd.uniform(6, 14))
        m = (sc.xx >= x0) & (sc.xx < x0 + w) & (sc.yy >= y0) & (sc.yy < y0 + h) & (sc.yy >= 380 + np.abs(sc.xx - 155) * 0.35)
        FU._bands(sc, m, FU.IRON if rnd.rand() < 0.7 else FU.BRASSR, rnd.uniform(0.3, 0.8) - (sc.yy - y0) / 40.0)
        o, _, _ = SU.edges(m)
        sc.rgb[o] = SU.OUTL
    for j, k_ in enumerate(("c_saw", "c_fist", "c_salute")):
        mod_icon(sc, k_, 70 + j * 70, 404 + (j % 2) * 10, 1)
    trolley(sc, 160)
    sc.rgb[80:240, 159:161] = hexc("#24222a")                                # the magnet's cable
    mag = (np.abs(sc.xx - 160) <= 30) & (sc.yy >= 240) & (sc.yy < 254)
    FU._bands(sc, mag, FU.STEEL, 0.7 - (sc.yy - 240) / 20.0)
    sc.rgb[252:254, 130:191] = hexc("#c04a3a")
    o, _, _ = SU.edges(mag)
    sc.rgb[o] = SU.OUTL
    crate = (np.abs(sc.xx - 160) <= 34) & (sc.yy >= 256) & (sc.yy < 318)
    FU._bands(sc, crate, FU.WOOD, 0.7 - (sc.yy - 256) / 80.0)
    o, _, _ = SU.edges(crate)
    sc.rgb[o] = SU.OUTL
    band = crate & (sc.yy >= 280) & (sc.yy < 290)
    stripes = ((sc.xx + sc.yy) // 5) % 2 == 0
    sc.rgb[band & stripes] = hexc("#e2ca50")
    sc.rgb[band & ~stripes] = hexc("#1a1612")
    sc.glow(160, 300, 30, hexc("#d860d0"), 0.3)
    letters(sc, "?", 160, 293, "title", 16, col=(220, 150, 255), col2=(60, 20, 80), align="center")
    option_card(sc, 660, 120, 936, 222, ["ПРИЧУДЫ"], "чаще полезные, реже опасные", "подкрутить шкалу", hr)
    cx, cy, r = 798, 320, 52
    d = np.hypot(sc.xx - cx, sc.yy - cy)
    a = np.arctan2(sc.yy - cy, sc.xx - cx)
    sc.rgb[d <= r + 5] = SU.OUTL
    FU._bands(sc, (d <= r + 4) & (d > r), FU.BRASSR, 0.7 - (sc.yy - cy) / (2 * r))
    face = d <= r
    sc.rgb[face] = hexc("#ece2c8")
    useful = face & (d > 18) & (a > -np.pi * 0.85) & (a < -np.pi * 0.15)
    danger = face & (d > 18) & (a >= -np.pi * 0.15) & (a < 0.15 * np.pi)
    sc.rgb[useful] = hexc("#2aa040")
    sc.rgb[danger] = hexc("#9a2aa0")
    sc.rgb[face & (d > 18) & (a > -np.pi * 0.85) & (a < -np.pi * 0.78)] = hexc("#70e080")   # the green just widened
    for t in np.linspace(0, 1, 40):                                            # the needle in the green
        x, y = int(cx + np.cos(-np.pi * 0.6) * r * 0.85 * t), int(cy + np.sin(-np.pi * 0.6) * r * 0.85 * t)
        sc.rgb[y, x] = hexc("#1a1612")
    sc.rgb[d <= 4] = hexc("#a0782c")
    letters(sc, "полезно", cx - 30, cy + r + 10, "text", 16, col=(110, 220, 130), align="center")
    letters(sc, "опасно", cx + 34, cy + r + 10, "text", 16, col=(210, 130, 220), align="center")
    FU.wrench(sc, 850, 930, 380, flip=True, size="19", seed=3)                 # the spanner on its screw
    FU.sill(sc, 468)
    action(sc, 20, 472, 310, 532, "БЕЗУМНЫЙ", "hot", big=True, heated=hl)
    action(sc, 650, 472, 940, 532, "ПРИЧУДЫ", "hot", big=True, heated=hr)
    letters(sc, "выбор навсегда", 480, 492, "text", 16, col=MUTED, align="center")


def dev_zodchiy(sc, hot):
    """The Architect grows, one of three: left, a big clock whose hand is being wound back a turn — deploying a
    turn sooner; right, a tower with scaffolding up its side and a new ballista being set on top — one more ability
    when deployed; over the leader, hung from the girder, the blueprint of the Citadel."""
    import citadel as CT
    hl, hm, hr = hot == "early", hot == "citadel", hot == "ability"
    option_card(sc, 24, 120, 300, 222, ["РАНЬШЕ"], "развёртывание на ход раньше", "перевести часы", hl)
    cx, cy, r = 160, 318, 52
    d = np.hypot(sc.xx - cx, sc.yy - cy)
    sc.rgb[d <= r + 5] = SU.OUTL
    FU._bands(sc, (d <= r + 4) & (d > r), FU.BRASSR, 0.7 - (sc.yy - cy) / (2 * r))
    sc.rgb[d <= r] = hexc("#ece2c8")
    for k in range(12):
        a = k * np.pi / 6
        x, y = int(cx + np.cos(a) * (r - 6)), int(cy + np.sin(a) * (r - 6))
        sc.rgb[y - 1:y + 2, x - 1:x + 2] = hexc("#3a342a")
    for t in np.linspace(0, 1, 40):
        x, y = int(cx + np.cos(-np.pi * 0.5 - 0.52) * r * 0.75 * t), int(cy + np.sin(-np.pi * 0.5 - 0.52) * r * 0.75 * t)
        sc.rgb[y, x] = hexc("#1a1612")
    for a in np.linspace(-np.pi * 0.42, -np.pi * 0.6, 10):                   # the arrow winding it back
        x, y = int(cx + np.cos(a) * (r + 12)), int(cy + np.sin(a) * (r + 12))
        sc.rgb[y - 1:y + 2, x - 1:x + 2] = hexc("#c04a3a")
    letters(sc, "ход 2 → 1", cx, cy + r + 14, "text", 16, col=INK, align="center")
    sc.rgb[d <= 4] = hexc("#a0782c")
    option_card(sc, 660, 120, 936, 222, ["+1 СПОСОБНОСТЬ"], "развёрнутым — ещё одна", "надстройка", hr)
    tw_ = (np.abs(sc.xx - 798) <= 34) & (sc.yy >= 290) & (sc.yy < 440)
    sc.rgb[tw_] = hexc("#8a8070")
    for yy in range(296, 440, 12):
        sc.rgb[yy, 764:833] = hexc("#5e5648")
    for xx in (766, 778, 790, 802, 814, 826):
        if (xx // 12) % 2 == 0:
            sc.rgb[278:290, xx:xx + 8] = hexc("#8a8070")
    o, _, _ = SU.edges(tw_)
    sc.rgb[o] = SU.OUTL
    for xx in (756, 840):                                                     # its scaffolding
        sc.rgb[260:440, xx - 1:xx + 2] = hexc("#7c562e")
    for yy in (330, 390):
        sc.rgb[yy:yy + 3, 752:846] = hexc("#a07844")
    bal = (sc.xx >= 780) & (sc.xx < 818) & (sc.yy >= 262) & (sc.yy < 276)
    FU._bands(sc, bal, FU.WOOD, 0.7 - (sc.yy - 262) / 20.0)                   # the new ballista on top
    sc.rgb[268:270, 760:840] = hexc("#5e5c66")
    sc.glow(799, 270, 30, hexc("#9ad8ff"), 0.35)
    # the Citadel's blueprint, hung over the leader
    FU.chain(sc, 380, 80, 122)
    FU.chain(sc, 580, 80, 122)
    blueprint_sheet(sc, 352, 122, 608, 250, stamp=None)
    spr = CT.build("deployed", 2, k=0.62)
    ys, xs = np.nonzero(spr.a)
    kk = 0.62 * min(1.0, 96.0 / max(1, ys.max() - ys.min()), 236.0 / max(1, xs.max() - xs.min()))
    spr = drawn(CT.build("deployed", 2, k=kk))                               # fitted to the sheet
    ys, xs = np.nonzero(spr.a)
    sc.blit(spr, int(480 - (xs.min() + xs.max()) / 2), int(244 - ys.max()))
    FU.cell(sc, 404, 126, 556, 148, "hi" if hm else "normal")
    letters(sc, "ЦИТАДЕЛЬ", 480, 129, "title", 16, col=(255, 210, 140) if hm else (170, 220, 250), col2=(40, 80, 120),
            align="center")
    FU.sill(sc, 468)
    action(sc, 12, 472, 302, 532, "РАНЬШЕ", "hot", big=True, heated=hl)
    action(sc, 334, 472, 626, 532, "ЦИТАДЕЛЬ", "hot", big=True, heated=hm)
    action(sc, 658, 472, 948, 532, "СПОСОБНОСТЬ", "hot", big=True, heated=hr)


DEV_SCENE = {"inventor": dev_inventor, "maniac": dev_maniac, "zodchiy": dev_zodchiy}


# ---------------------------------------------------------------- defeat: the forge gone cold
def cold(sc, m, k=0.55):
    """The colour drained out to cold grey-blue where the heat has gone."""
    g = sc.rgb[m].mean(axis=1, keepdims=True)
    sc.rgb[m] = sc.rgb[m] * (1 - k) + (g * np.array((0.86, 0.92, 1.06))) * k


def defeat(ret=False, anim=None):
    """Defeat, and the run summed up. The forge has gone cold: the title in grey without its heat, the spanners
    by it dark and cracked, ash drifting down. Left, the furnace out — a last few embers — and the army a heap of
    scrap before it. In the middle what the run came to, and how little was missing: the enemy leader's health
    that was left. Right, what the run opened, and what is next to open."""
    import frames as F
    from swarm_effects import lit
    sc = screen(97)
    FU.wing(sc, 0, 0, WW, 44)
    tw = SU.text_width("ПОРАЖЕНИЕ", "title", 24)
    x = WW // 2 - tw // 2
    letters(sc, "ПОРАЖЕНИЕ", x, 6, "title", 24, col=(176, 178, 186), col2=(56, 58, 68))
    L = 140
    ml = FU.wrench(sc, x - 14 - L, x - 14, 21, flip=False, size="24", seed=1)
    mr = FU.wrench(sc, x + tw + 14, x + tw + 14 + L, 21, flip=True, size="19", seed=2)
    for m_, cx in ((ml, x - 14 - L // 2), (mr, x + tw + 14 + L // 2)):
        sc.rgb[m_] *= 0.42                                                  # gone dark
        for k in range(9):                                                  # and cracked across
            yy, xx = 15 + k, int(cx + (k % 3) - 1)
            if m_[yy, xx]:
                sc.rgb[yy, xx] = SU.OUTL
    cold(sc, (sc.yy < 44), 0.6)
    toolbar(sc)
    # left: the furnace out, the army a heap of scrap before it
    FU.plate(sc, 12, 52, 330, 462, seed=98)
    heading(sc, "ЧТО ОСТАЛОСЬ", 26, 62)
    X, Y = sc.xx, sc.yy
    ax, ay, ar = 171, 150, 74
    arch = ((((X - ax) / ar) ** 2 + ((Y - ay) / ar) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar) & (Y > ay) & (Y < 260))
    sc.rgb[arch] = hexc("#0e0d10")
    rim = arch & ~(np.roll(arch, 4, 0) & np.roll(arch, -4, 0) & np.roll(arch, 4, 1) & np.roll(arch, -4, 1))
    sc.rgb[rim] = hexc("#3a3842")
    for kk in range(-4, 5):                                                 # the voussoirs' rivets, cold
        a_ = np.pi * (0.5 + kk / 10)
        FU.rivet(sc, ax - np.cos(a_) * (ar + 5), ay - np.sin(a_) * (ar + 5))
    ash = arch & (Y >= 238) & (np.abs(X - ax) <= 60 - (Y - 238) * 0.0) & (Y >= 238 + np.abs(X - ax) * 0.18)
    sc.rgb[ash] = hexc("#4a4850")                                           # a bank of ash in the grate
    sc.rgb[ash & ((X + Y) % 5 == 0)] = hexc("#6a6870")
    rnd = np.random.RandomState(4)
    for _ in range(9):                                                      # the last embers in it
        ex, ey = int(ax + rnd.uniform(-44, 44)), int(rnd.uniform(244, 256))
        sc.glow(ex, ey, 6, hexc("#c2500e"), 0.25)
        sc.rgb[ey, ex] = hexc("#7a2208") if rnd.rand() < 0.6 else hexc("#e86a1a")
    for k in range(5):                                                      # a thread of smoke from it, thinning
        sx_, sy_ = int(ax + np.sin(k * 1.3) * 6), 120 - k * 9
        sc.rgb[sy_:sy_ + 4, sx_:sx_ + 2] = sc.rgb[sy_:sy_ + 4, sx_:sx_ + 2] * 0.6 + hexc("#5e5c66") * 0.4
    for (fr, dx, dy, kk) in (("Страж", -78, 0, 0.92), ("Мудрец", 70, -4, 0.85), ("Орудие", -10, 18, 0.88),
                             ("Механик", 104, 22, 0.9)):
        g = lit(F.build(fr, "broken", k=F.FRAMES[fr][0] * kk), (60, 64, 76), 0.5)
        sc.blit(g, int(ax + dx - g.ox), int(378 + dy - g.oy))
    sc.rgb[404:410, 24:318] = hexc("#24222a")
    cold(sc, (X >= 20) & (X < 322) & (Y >= 84) & (Y < 410), 0.55)
    fr_ = (anim or {}).get("frame", 0)
    rnd2 = np.random.RandomState(4)
    for e in range(9):                                                      # the embers keep their last red
        ex, ey = int(ax + rnd2.uniform(-44, 44)), int(rnd2.uniform(244, 256))
        br = 0.5 + 0.5 * np.sin(fr_ * 2 * np.pi / 36 * (1 + e % 3) + e * 1.7)   # each breathing at its own pace
        sc.glow(ex, ey, 5, hexc("#c2500e"), 0.12 + 0.3 * br)
        sc.rgb[ey, ex] = hexc("#ff8a2a") if br > 0.6 else (hexc("#a8320e") if br > 0.25 else hexc("#5a1408"))
    H.fx_line(sc, 26, 420, "{гибель} лидер · бой 8 из 15")
    letters(sc, "армия ушла в лом", 26, 440, "text", 16, col=MUTED)
    # the middle: what the run came to
    FU.plate(sc, 340, 52, 626, 462, seed=99)
    heading(sc, "ИТОГ ПОХОДА", 354, 62)
    rows = (("бой", "дошёл до боя", "8 из 15"), ("лидер", "боссов побеждено", "1"),
            ("убийство", "врагов убито", "412"), ("металл", "металла добыто", "86"),
            ("модуль", "модулей поставлено", "11"))
    y = 96
    for g, lab, val in rows:
        a_ = H.glyph(sc, g if g != "бой" else "атака", 354, y - 4, 2)
        letters(sc, lab, 354 + a_ + 8, y - 2, "text", 16, col=MUTED)
        w = SU.text_width(val, "text", 16)
        for xx in range(354 + a_ + 14 + SU.text_width(lab, "text", 16), 610 - w - 6, 4):
            sc.rgb[y + 10, xx] = sc.rgb[y + 10, xx] * 0.4 + np.array(MUTED) * 0.6
        letters(sc, val, 610, y - 2, "text", 16, col=INK, align="right")
        y += 24
    FU.cell(sc, 350, y + 4, 616, y + 70, "hi")                              # the best golem
    gs = golem_sprite("Орудие", {"mortar": 1, "canister": 1}, 0.62, body=BODY.get("Орудие"))
    sc.blit(gs, int(386 - gs.ox), int(y + 66 - gs.oy))
    letters(sc, "лучший — Орудие", 420, y + 12, "text", 16, col=GOLD)
    H.fx_line(sc, 420, y + 36, "{убийство:64} · Мортира II")
    y += 84
    heading(sc, "НЕ ХВАТИЛО", 354, y)
    y += 28
    H.glyph(sc, "лидер", 354, y - 2, 2)
    letters(sc, "Матка", 380, y, "text", 16, col=(240, 140, 120))
    SU.meter(sc, 440, y + 4, 610, 7, 10, 2, "#c04a3a")
    letters(sc, "у неё оставалось 18 здоровья —", 354, y + 26, "text", 16, col=INK)
    letters(sc, "один залп Мортиры", 354, y + 44, "text", 16, col=INK)
    # the right: what the run opened, and what is next
    FU.plate(sc, 634, 52, 948, 462, seed=100)
    heading(sc, "ОТКРЫТО", 648, 62)
    for j, (key, nm, sub) in enumerate((("nozzles", "Сопла", "редкий модуль · в мастерской"),
                                        ("dome", "Щит-купол", "редкий модуль · в мастерской"))):
        y0 = 90 + j * 66
        FU.cell(sc, 642, y0, 940, y0 + 58, "new")
        FU.cell(sc, 650, y0 + 8, 692, y0 + 50, "locked")
        mod_icon(sc, key, 655, y0 + 13, 2)
        letters(sc, nm, 704, y0 + 10, "text", 16, col=GOLD)
        letters(sc, sub, 704, y0 + 30, "text", 16, col=MUTED)
    heading(sc, "ДАЛЬШЕ ОТКРОЕТСЯ", 648, 236)
    for j, (nm, cond, have, need) in enumerate((("Маньяк", "победить 2-го босса", 1, 2),
                                                ("Зодчий", "дойти до 12-го боя", 8, 12),
                                                ("Сложность II", "пройти поход", 0, 1))):
        y0 = 264 + j * 62
        FU.cell(sc, 642, y0, 940, y0 + 54, "locked")
        letters(sc, nm, 654, y0 + 6, "text", 16, col=INK)
        letters(sc, f"{have} из {need}", 928, y0 + 6, "text", 16, col=MUTED, align="right")
        letters(sc, cond, 654, y0 + 28, "text", 16, col=MUTED)
        bx0, bx1 = 820, 928
        sc.rgb[y0 + 34:y0 + 40, bx0:bx1] = hexc("#08070a")
        fill = int(bx0 + (bx1 - bx0) * have / need)
        if fill > bx0:
            sc.rgb[y0 + 34:y0 + 40, bx0:fill] = hexc("#c2500e")
            sc.rgb[y0 + 34, bx0:fill] = hexc("#ffb040")
    for k in range(60):                                                     # ash drifting down over it all
        ax0, ay0 = rnd.randint(0, WW), rnd.randint(44, 466)
        ay_ = 44 + (ay0 - 44 + fr_ * (1 + k % 2)) % 422                     # falling, a loop of 36 frames
        ax_ = int(ax0 + 2 * np.sin((ay_ + k * 13) / 30.0)) % WW
        sc.rgb[ay_, ax_] = sc.rgb[ay_, ax_] * 0.4 + hexc("#8e8c96") * 0.6
    FU.sill(sc, 468)
    action(sc, 12, 478, 220, 526, "В меню", "steel")
    action(sc, 640, 472, 948, 532, "НОВЫЙ ПОХОД", "hot", big=True)
    if ret:
        return sc
    img = sc.image(S)
    img.save(out("foundry_defeat.png"))
    print("foundry_defeat.png", img.size)


def module_pop(sc, key, name, cx, top, k=1.0, rise=0.0, heat=1.0):
    """A module firing, over its golem: its icon in a red-hot box, rising, its name under it; k fades the lot in
    and out, heat cools the box's rim from red back to iron."""
    before = sc.rgb.copy() if k < 1 else None
    y = int(round(top - 48 - rise))
    if y < 42:                                       # no room over its head (the field's top row): by its side
        y, cx = int(round(42 - rise * 0.3)), cx - 58
    x0 = int(round(cx - 19))
    sc.glow(cx, y + 19, 30, hexc("#ff8a2a"), 0.5 * heat)
    FU.cell(sc, x0, y, x0 + 38, y + 38, "hover" if heat > 0.5 else "normal", seed=3)
    mod_icon(sc, key, x0 + 3, y + 3, 2)
    letters(sc, name, cx, y + 42, "text", 16, col=GOLD, align="center")
    if before is not None:
        sc.rgb[:] = before * (1 - k) + sc.rgb * k


def mark_broken(sc, cx, cy):
    """The Foundry's own state on the field: a golem broken in the fight — the breakdown glyph in a rust-red box
    with its crack, by the golem's side; it waits there for the repair after the battle."""
    x0, y0 = int(cx - 13), int(cy - 13)
    sc.glow(cx, cy, 18, hexc("#e04a2a"), 0.35)
    FU.cell(sc, x0, y0, x0 + 26, y0 + 26, "broken")
    H.glyph(sc, "поломка", x0 + 4, y0 + 4, 2)


def golem_tip(sc, gx, gy, name, sub, mods, rows, side="left", w=300):
    """On pause, the golem under the mouse opens its card by it: name, frame and leadership, its modules as icons
    with their levels, then its lines of glyphs (body, blow, what's wrong with it)."""
    x0 = int(gx - 40 - w) if side == "left" else int(gx + 40)
    y0 = int(gy - 150)
    yb = H.fx_rows(sc, x0 + 12, y0 + 96, w - 24, rows, draw=False) + 8
    FU.cell(sc, x0, y0, x0 + w, yb, "hi")
    letters(sc, name, x0 + 12, y0 + 9, "text", 16, col=GOLD)
    letters(sc, sub, x0 + w - 12, y0 + 9, "text", 16, col=MUTED, align="right")
    for m_, (key, lvl, st) in enumerate(mods):
        mx = x0 + 12 + m_ * 46
        FU.cell(sc, mx, y0 + 32, mx + 40, y0 + 72, st)
        mod_icon(sc, key, mx + 4, y0 + 36, 2)
        letters(sc, lvl, mx + 20, y0 + 72, "text", 16, col=BRASS if st != "broken" else RED, outline=False,
                align="center")
    H.fx_rows(sc, x0 + 12, y0 + 96, w - 24, rows)
    return x0, y0, x0 + w, yb


_FIELD = {}


def battle_field():
    """The battle under the HUD — built once (it is the slow part) and copied for every view and frame."""
    import battle as BT
    if "sc" not in _FIELD:
        sc, count, ng = BT.build("Матка")
        _FIELD.update(sc=sc, count=count, ng=ng, gpos=BT.LAST["gpos"], lead=BT.LAST["lead"])
    return _FIELD


def battle_wing(sc, share, paused=False, t=0, ng=7, count=285):
    """The iron beam: the Foundry's count, the tug of war (hot iron pushing from the left, the swarm's green from the
    right, sparks where they meet), the swarm's count, the turn, the speed caps with their keys."""
    FU.wing(sc, 0, 0, WW, 34)
    letters(sc, f"Литейщик {ng - 1}/{ng}", 14, 9, "text", 16, col=(240, 200, 150))
    x0, x1, y0, y1 = 150, 520, 10, 25
    mid = x0 + (x1 - x0) * share
    X, Y = sc.xx, sc.yy
    m = (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)
    tt = np.clip((Y - y0) / (y1 - y0), 0, 1)[..., None]
    left, right = m & (X < mid), m & (X >= mid)
    sc.rgb[left] = (hexc("#ffb050") * (1 - tt) + hexc("#7a2a0a") * tt)[left]
    sc.rgb[right] = (hexc("#b4f47a") * (1 - tt) + hexc("#2a6224") * tt)[right]
    heat = left & (X > mid - 26)                                       # the iron's edge hottest where it pushes
    a_ = np.clip(1 - (mid - X) / 26, 0, 1)[..., None] * 0.6
    sc.rgb[heat] = (sc.rgb * (1 - a_) + hexc("#fff0c0") * a_)[heat]
    for x in range(x0 + 8, int(mid) - 6, 12):
        FU.rivet(sc, x, (y0 + y1) // 2)
    o, _, _ = SU.edges(m)
    sc.rgb[o] = SU.OUTL
    FU.sparks(sc, mid, (y0 + y1) / 2, 8, seed=2 + t // 2)
    letters(sc, f"рой {count - 1}", 530, 9, "text", 16, col=(170, 240, 120))
    letters(sc, "ход 5", 728, 9, "text", 16, col=MUTED, align="right")
    for cx, t_, on, key in ((770, "II", paused, "Пробел"), (840, "×2", not paused, "Tab"), (910, "»", False, "End")):
        FU.cap_button(sc, cx, 17, 11, t_, "brass" if on else "steel")
        kw = SU.text_width(key, "text", 16) + 12
        H.keycap(sc, int(cx - kw / 2), 36, key)


def battle_view(mode="run", t=0, share=0.42, pops=None, ret=False):
    """The battle with the Foundry's interface over it. On the field: both leaders' health over them, a module's
    icon popping up over its golem when it fires, states over the golems (the swarm's glue and acid, and the
    Foundry's own — a broken module). On pause, pointing at a golem opens its card; at a bug, the enemy's."""
    import copy
    import battle as BT
    import swarm_status as ST
    import swarm1 as W
    fd = battle_field()
    sc = copy.deepcopy(fd["sc"])
    H.HOVER.clear()
    H.KIT["cell"] = FU.cell
    gp = fd["gpos"]
    qx, qy = BT.X0 + 15.6 * BT.CW, BT.Y0 + 8.4 * BT.CH
    if "qtop" not in _FIELD:
        _FIELD["qtop"] = ST.top_of(W.queen(0.0, "attack", k=0.92), qy)
    qtop = _FIELD["qtop"]
    lx, ly, lspr = fd["lead"]
    ltop = ST.top_of(lspr, ly)
    SU.meter(sc, lx - 40, ltop - 12, lx + 40, 7, 10, 7, "#d08a3a")
    H.glyph(sc, "лидер", lx - 58, ltop - 14, 2)
    SU.meter(sc, qx - 46, qtop - 12, qx + 46, 7, 10, 8, "#c04a3a")
    H.glyph(sc, "лидер", qx - 64, qtop - 14, 2)
    bx, by, bspr = gp[("Горн", 6, 2)]                                  # the Forge whose module broke
    mark_broken(sc, bx - 58, by - 46)
    if pops is None:
        pops = [("canister", "Картечь", ("Орудие", 3, 2), 1.0, 0.0, 1.0),
                ("intercept", "Перехват", ("Страж", 5, 6), 1.0, 0.0, 1.0)]
    for key, nm, who, k, rise, heat in pops:
        x, y, spr = gp[who]
        module_pop(sc, key, nm, x, ST.top_of(spr, y), k, rise, heat)
    battle_wing(sc, share, mode != "run", t, fd["ng"], fd["count"])
    name = "foundry_battle.png"
    if mode == "pause":                                                # the Guard: its card by it
        gx, gy, gspr = gp[("Страж", 5, 6)]
        golem_tip(sc, gx + 40, gy - 10, "Страж", "голем · 6", (("tower", "II", "normal"), ("intercept", "I", "normal"),
                  ("plates", "I", "normal")),
                  ["{здоровье:71/100} {броня:4 −1} {скорость:1}", "{урон:1–6 +3} {дроб} {дальность:1}",
                   "{атака} {свой} {радиус:1} → {перехват:1}", "разъедена: {броня:−1} до конца боя"], side="right", w=280)
        H.cursor(sc, int(gx) + 4, int(gy) - 60)
        name = "foundry_battle_pause.png"
    elif mode == "enemy":                                              # a spitter: the enemy's card, in our iron
        sx_, sy_ = 566, 452
        x0, y0, w = 590, 300, 270
        rows_ = ["{каждые:2} → {яд} {клей:1} {дальность:3}", "{через:1}", "минус: {атака} → {урон:−}"]
        yb = H.fx_rows(sc, x0 + 12, y0 + 46, w - 24, rows_, draw=False) + 8
        FU.cell(sc, x0, y0, x0 + w, yb, "broken")
        H.icon(sc, "spitter", x0 + 8, y0 + 6, 2)
        letters(sc, "Паук-плевун", x0 + 46, y0 + 9, "text", 16, col=(190, 240, 130))
        letters(sc, "рой · рабочая", x0 + 46, y0 + 25, "text", 16, col=MUTED)
        H.fx_rows(sc, x0 + 12, y0 + 46, w - 24, rows_)
        H.cursor(sc, sx_ - 2, sy_ - 14)
        name = "foundry_battle_enemy.png"
    if ret:
        return sc
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


def battle():
    for mode in ("run", "pause", "enemy"):
        battle_view(mode)


SCREENS = {"workshop": workshop, "camp": camp, "leadercard": leader_card, "rack": workshop_rack, "repair": workshop_repair, "smelt": smelt, "slipways": slipways, "new": new_golem, "card": card, "leader": leaders_pick, "aftermath": aftermath, "battle": battle, "glossary": glossary,
           "confirm": confirm_smelt, "alt": lambda: leader_card(alt=True),
           "drag": lambda: workshop("drag"), "trophy": lambda: aftermath(variant="trophy"),
           "states": states, "settings": lambda: [settings(k) for k, _ in SETTINGS], "pause": pause,
           "development": lambda: [development(k, h) for k, h in (("colossus", "cell"), ("inventor", "type"),
                                                                  ("maniac", "quirks"), ("zodchiy", "citadel"))],
           "defeat": defeat}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "mounts":
        measure_mounts()
        sys.exit()
    for k, fn in SCREENS.items():
        if arg in ("all", k):
            fn()
