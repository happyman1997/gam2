"""The swarm creature's card for each form, every one in its own frame — as each of the Foundry's golems has its
own card. The card's layout is the same (swarm_hud.big_card); the portrait's well is the form's own place: an ant
in its tunnels in the earth, a wasp in the grey paper of its nest, a scorpion on cracked ground under the night, a
beetle in bark with its galleries, a barrel over an acid pool, a woodlouse under a wet log in moss, a grasshopper in
tall grass, a mantis in leaves with an orchid, a firefly in a dark glade among other lights, a spitter in its web.
The card's edge takes the form's colour, its icon sits on the wing.

The numbers are the simulation's (sim/src/data.rs: swarm()), the abilities and weaknesses the concept's.

    python3 tools/sprites/swarm_form_cards.py   -> out/swarm_card_<form>.png, out/swarm_cards_forms.png
"""
import numpy as np
from PIL import Image
from kit import hexc, BAYER
import swarm_ui as UI
import swarm_hud as SH
from swarm_hud import bug, icon, put, GOLD, INK, RED, S, out
from noise import value_noise

X0, Y0, X1, Y1 = 24, 68, 294, 294          # the portrait's well


def _m(sc, x0, y0, x1, y1):
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    t = np.clip((sc.yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    return m, t


def dith(sc, m, cols, v):
    """Fill a mask with a ramp by a value 0..1, ordered-dithered."""
    lv = np.clip((v * len(cols) + (BAYER[sc.yy % 4, sc.xx % 4] - 0.5) * 0.7).astype(int), 0, len(cols) - 1)
    for i, c in enumerate(cols):
        sc.rgb[m & (lv == i)] = hexc(c)


def h_ant(sc, x0, y0, x1, y1):
    """Earth, its tunnels gnawed through it: dark winding channels with a lighter rim, chambers, grains."""
    m, t = _m(sc, x0, y0, x1, y1)
    n = value_noise(sc.w, sc.h, 9, 3)
    dith(sc, m, ("#1c120c", "#2a1a10", "#3a2414", "#4a3018"), n * 0.8 + 0.1)
    rnd = np.random.RandomState(5)
    rim, core = np.zeros_like(m), np.zeros_like(m)
    for _ in range(5):                                                   # tunnels: their rims, then their dark cores
        x, y = rnd.randint(x0, x1), rnd.randint(y0, y0 + 40)
        a = rnd.uniform(0.6, 2.4)
        for k in range(160):
            a += rnd.uniform(-0.25, 0.25)
            x, y = x + np.cos(a) * 1.6, y + abs(np.sin(a)) * 1.4
            if not (x0 + 4 < x < x1 - 4 and y0 + 4 < y < y1 - 4):
                break
            d = np.hypot(sc.xx - x, sc.yy - y)
            rim |= d <= 5.5
            core |= d <= 3.5
    sc.rgb[rim & m] = hexc("#5a3a1c")
    sc.rgb[core & m] = hexc("#0e0806")
    for (cx, cy, r) in ((80, 250, 16), (230, 150, 13)):                  # chambers
        e = ((sc.xx - cx) / (r * 1.5)) ** 2 + ((sc.yy - cy) / r) ** 2
        sc.rgb[(e <= 1.25) & (e > 1) & m] = hexc("#5a3a1c")
        sc.rgb[(e <= 1) & m] = hexc("#0e0806")
        for k in range(5):
            sc.rgb[cy + r // 2 - 2, cx - 10 + k * 5:cx - 8 + k * 5] = hexc("#e8e0c0")     # eggs in the chamber
    for _ in range(70):
        px_, py_ = rnd.randint(x0, x1), rnd.randint(y0, y1)
        if m[py_, px_] and sc.rgb[py_, px_].sum() > 60:
            sc.rgb[py_, px_] = hexc("#6a4a2a")


def h_wasp(sc, x0, y0, x1, y1):
    """The grey paper of a wasp's nest: wavy layered bands in shades of grey and tan, a few paper cells above."""
    m, t = _m(sc, x0, y0, x1, y1)
    band = ((sc.yy + 6 * np.sin(sc.xx / 13.0) + 3 * np.sin(sc.xx / 5.0 + sc.yy / 9.0)) / 7.0).astype(int) % 5
    pal = [hexc(c) for c in ("#3a3632", "#4a443c", "#5a5248", "#2e2a28", "#6a6052")]
    for i, c in enumerate(pal):
        sc.rgb[m & (band == i)] = c
    for y in range(y0, y1, 7):
        for x in range(x0, x1):
            yy = int(y + 6 * np.sin(x / 13.0) + 3 * np.sin(x / 5.0 + y / 9.0))
            if y0 <= yy < y1 and (x // 2) % 3:
                sc.rgb[yy, x] = sc.rgb[yy, x] * 0.7
    sc.rgb[m] *= (0.55 + 0.45 * t)[m]
    R = 9
    for i in range(int((x1 - x0) / (R * 1.5)) + 1):                      # paper comb across the top
        for j in range(3):
            cx, cy = x0 + i * R * 1.5, y0 + 6 + j * R * 1.73 + (R * 0.86 if i % 2 else 0)
            hx = SH.hexmask(sc, int(cx), int(cy), R)
            sc.rgb[hx & m] = hexc("#1a1816")
            sc.rgb[hx & ~SH.hexmask(sc, int(cx), int(cy), R - 2) & m] = hexc("#7a7062")


def h_scorpion(sc, x0, y0, x1, y1):
    """Night over dry ground: a violet sky with a few stars, the ground cracked into plates, stones."""
    m, t = _m(sc, x0, y0, x1, y1)
    gy = int(y0 + (y1 - y0) * 0.55)
    sky = m & (sc.yy < gy)
    sc.rgb[sky] = (hexc("#0e0a1c") * (1 - t) * 1.0 + hexc("#2a1a30") * t)[sky]
    rnd = np.random.RandomState(7)
    for _ in range(30):
        sx, sy = rnd.randint(x0, x1), rnd.randint(y0, gy - 6)
        sc.rgb[sy, sx] = hexc("#d8d0f0") if rnd.rand() < 0.3 else hexc("#6a6080")
    gnd = m & (sc.yy >= gy)
    tg = np.clip((sc.yy - gy) / max(1, y1 - gy), 0, 1)
    dith(sc, gnd, ("#3a2410", "#5a3a1a", "#7a5226", "#9a6a34"), 0.75 - tg * 0.5)
    for _ in range(9):                                                   # the cracks between the plates
        x, y = rnd.randint(x0, x1), rnd.randint(gy, y1)
        for k in range(40):
            x += rnd.choice((-1, 0, 1, 1)); y += rnd.choice((-1, 0, 1))
            if x0 <= x < x1 and gy <= y < y1:
                sc.rgb[y, x] = hexc("#1e1208")
    for (sx, sy, r) in ((60, 288, 7), (250, 286, 9), (200, 292, 4)):
        e = ((sc.xx - sx) / r) ** 2 + ((sc.yy - sy) / (r * 0.6)) ** 2 <= 1
        sc.rgb[e & m] = hexc("#5e5850")
        sc.rgb[e & m & (sc.yy < sy - r * 0.2)] = hexc("#8a847a")
    sc.rgb[gy, x0:x1] = hexc("#1a1018")


def h_beetle(sc, x0, y0, x1, y1):
    """Under bark: brown wood in long grain, and the galleries a beetle's brood engraves in it — a trunk gallery
    with its side tunnels running out."""
    m, t = _m(sc, x0, y0, x1, y1)
    grain = np.sin(sc.xx / 3.0 + 2.5 * np.sin(sc.yy / 23.0) + value_noise(sc.w, sc.h, 11, 9) * 4)
    dith(sc, m, ("#2a180c", "#3a2412", "#4e321a", "#5e3e22"), 0.5 + 0.3 * grain)
    cx = (x0 + x1) // 2
    for y in range(y0 + 8, y1 - 8):                                      # the trunk gallery
        sc.rgb[y, cx - 3:cx + 4] = hexc("#140a04")
        sc.rgb[y, cx - 4] = hexc("#7a5430")
    for k in range(10):                                                  # the side tunnels, each widening as it went
        y = y0 + 16 + k * 20
        for side in (-1, 1):
            for s in range(0, 100, 1):
                xx = int(cx + side * s)
                yy = int(y + 8 * np.sin(s / 30.0 + k) + s * 0.08)
                w = 1 + s // 40
                if x0 + 2 < xx < x1 - 2 and y0 < yy < y1 - 2:
                    sc.rgb[yy - w:yy + w + 1, xx] = hexc("#180c06")


def h_barrel(sc, x0, y0, x1, y1):
    """Etched stone over an acid pool: grey stone pitted by the acid, the pool glowing green at the foot with
    bubbles on it, its light on the stone."""
    m, t = _m(sc, x0, y0, x1, y1)
    n = value_noise(sc.w, sc.h, 8, 13)
    dith(sc, m, ("#141a14", "#1e2620", "#2a322a", "#3a4236"), n * 0.7 + 0.1)
    rnd = np.random.RandomState(13)
    for _ in range(40):                                                  # pits eaten in the stone
        px_, py_, r = rnd.randint(x0, x1), rnd.randint(y0, y1 - 40), rnd.uniform(1.5, 4)
        d = np.hypot(sc.xx - px_, sc.yy - py_)
        sc.rgb[(d <= r) & m] = hexc("#0a0e0a")
        sc.rgb[(d <= r) & (d > r - 1) & (sc.yy > py_) & m] = hexc("#5a7a3a")
    py = y1 - 34
    pool = m & (sc.yy >= py + 3 * np.sin(sc.xx / 9.0))
    tp = np.clip((sc.yy - py) / 34.0, 0, 1)[..., None]
    sc.rgb[pool] = (hexc("#b8f040") * (1 - tp) + hexc("#3a7a10") * tp)[pool]
    sc.glow((x0 + x1) // 2, py, 120, hexc("#9ae030"), 0.18)
    for k in range(9):
        bx, by, r = rnd.randint(x0 + 6, x1 - 6), rnd.randint(py + 4, y1 - 4), rnd.choice((2, 2, 3))
        d = np.hypot(sc.xx - bx, sc.yy - by)
        sc.rgb[(d <= r) & (d > r - 1) & m] = hexc("#f0ffb0")


def h_isopod(sc, x0, y0, x1, y1):
    """Under a wet log: the log's dark underside above, wet slate below, moss in patches, drops of water."""
    m, t = _m(sc, x0, y0, x1, y1)
    n = value_noise(sc.w, sc.h, 10, 21)
    dith(sc, m, ("#141618", "#1e2226", "#2a3036", "#363e46"), n * 0.6 + 0.2)
    log = m & (sc.yy < y0 + 40 + 6 * np.sin(sc.xx / 17.0))
    dith(sc, log, ("#1a100a", "#2a1a10", "#3a2414"), 0.4 + 0.4 * np.sin(sc.xx / 4.0) * 0.5)
    rnd = np.random.RandomState(21)
    for _ in range(26):                                                  # moss
        mx, my = rnd.randint(x0, x1), rnd.randint(y0 + 40, y1)
        r = rnd.uniform(3, 9)
        e = ((sc.xx - mx) / r) ** 2 + ((sc.yy - my) / (r * 0.5)) ** 2 <= 1
        mm = e & m & ~log
        sc.rgb[mm] = hexc("#2e4a1c")
        sc.rgb[mm & ((sc.xx + sc.yy) % 3 == 0)] = hexc("#4a6a28")
    for _ in range(14):                                                  # drops
        dx_, dy_ = rnd.randint(x0 + 4, x1 - 4), rnd.randint(y0 + 30, y1 - 4)
        sc.rgb[dy_:dy_ + 3, dx_:dx_ + 2] = hexc("#5a7088")
        sc.rgb[dy_, dx_] = hexc("#c8e0f0")


def h_grass(sc, x0, y0, x1, y1):
    """Tall grass against a dusk sky: blades rising from the foot, bending, in layers from dark to lit."""
    m, t = _m(sc, x0, y0, x1, y1)
    sc.rgb[m] = (hexc("#2a2238") * (1 - t) + hexc("#5a4630") * t)[m]
    rnd = np.random.RandomState(17)
    for layer, cols in enumerate((("#1a2410", "#24321a"), ("#2a3a18", "#3e5222"), ("#46602a", "#6a8a34"))):
        for _ in range(26):
            bx = rnd.randint(x0, x1)
            h = rnd.randint(60, 190 - layer * 30)
            bend = rnd.uniform(-0.5, 0.5)
            for k in range(h):
                q = k / h
                x = int(bx + bend * q * q * 40)
                y = y1 - 1 - k
                w = 2 if q < 0.6 else 1
                if x0 <= x < x1 - w and y0 <= y:
                    sc.rgb[y, x:x + w] = hexc(cols[0])
                    sc.rgb[y, x] = hexc(cols[1])


def h_mantis(sc, x0, y0, x1, y1):
    """Among leaves: broad leaves in greens with their veins, and an orchid's pale pink petals by the corner."""
    m, t = _m(sc, x0, y0, x1, y1)
    sc.rgb[m] = (hexc("#0e1a10") * (1 - t) + hexc("#162418") * t)[m]
    rnd = np.random.RandomState(31)
    for k in range(9):                                                   # leaves
        cx, cy = rnd.randint(x0, x1), rnd.randint(y0, y1)
        a = rnd.uniform(0, np.pi)
        L, Wd = rnd.uniform(50, 90), rnd.uniform(14, 24)
        X = (sc.xx - cx) * np.cos(a) + (sc.yy - cy) * np.sin(a)
        Y = -(sc.xx - cx) * np.sin(a) + (sc.yy - cy) * np.cos(a)
        leaf = (np.abs(Y) <= Wd * np.sqrt(np.clip(1 - (X / L) ** 2, 0, 1))) & m
        g = ("#1e3a16", "#2a4e1c", "#3a6624")[k % 3]
        sc.rgb[leaf] = hexc(g)
        sc.rgb[leaf & (Y < -Wd * 0.3)] = hexc(g) * 1.2
        sc.rgb[leaf & (np.abs(Y) < 0.7)] = hexc("#5a8a3a")
        sc.rgb[leaf & (np.abs(Y - X * 0.5 % 12) < 0.5) & (Y > 0)] = hexc(g) * 0.75
    ox, oy = x1 - 46, y0 + 44                                            # the orchid
    for j in range(5):
        a = j * 2 * np.pi / 5 - np.pi / 2
        px_, py_ = ox + np.cos(a) * 16, oy + np.sin(a) * 16
        e = ((sc.xx - px_) / 12) ** 2 + ((sc.yy - py_) / 8) ** 2 <= 1
        sc.rgb[e & m] = hexc("#e8b0d0")
        sc.rgb[e & m & (sc.yy < py_)] = hexc("#f8d8ec")
    d = np.hypot(sc.xx - ox, sc.yy - oy)
    sc.rgb[(d <= 6) & m] = hexc("#c04a8a")
    sc.rgb[(d <= 2) & m] = hexc("#ffe080")


def h_firefly(sc, x0, y0, x1, y1):
    """A dark glade at night: deep blue, grass in silhouette at the foot, other fireflies' lights in the air."""
    m, t = _m(sc, x0, y0, x1, y1)
    sc.rgb[m] = (hexc("#06081a") * (1 - t) + hexc("#0e1a1e") * t)[m]
    rnd = np.random.RandomState(41)
    keep = sc.rgb.copy()
    for _ in range(18):
        fx, fy = rnd.randint(x0 + 8, x1 - 8), rnd.randint(y0 + 8, y1 - 60)
        sc.glow(fx, fy, rnd.randint(6, 12), hexc("#d8f060"), 0.35)
        sc.rgb[fy:fy + 2, fx:fx + 2] = hexc("#f8ffc0")
    sc.rgb[~m] = keep[~m]
    for _ in range(60):
        bx = rnd.randint(x0, x1)
        h = rnd.randint(8, 40)
        bend = rnd.uniform(-0.4, 0.4)
        for k in range(h):
            x = int(bx + bend * (k / h) ** 2 * 14)
            if x0 <= x < x1:
                sc.rgb[y1 - 1 - k, x] = hexc("#020406")


def h_spitter(sc, x0, y0, x1, y1):
    """Its web: dark, the radial threads and the spiral of silk catching a little light, dew on them."""
    m, t = _m(sc, x0, y0, x1, y1)
    sc.rgb[m] = (hexc("#14101c") * (1 - t) + hexc("#0c0a12") * t)[m]
    cx, cy = x0 + 70, y0 + 60
    keep = sc.rgb.copy()
    for a in np.linspace(0, 2 * np.pi, 14, endpoint=False):
        UI.silk(sc, (cx, cy), (cx + np.cos(a) * 320, cy + np.sin(a) * 320), sag=3, col="#a8a0b8", k=0.5)
    for r in range(14, 300, 13):
        pts = [(cx + np.cos(a) * r, cy + np.sin(a) * r) for a in np.linspace(0, 2 * np.pi, 15)]
        for p, q in zip(pts[:-1], pts[1:]):
            UI.silk(sc, p, q, sag=2, col="#8a8498", k=0.4)
    sc.rgb[~m] = keep[~m]


FORM = {   # form: (name, its habitat, the card's edge colour)
    None: ("Муравей", h_ant, "#b0703a"), "wings": ("Оса", h_wasp, "#e0c040"), "stinger": ("Скорпион", h_scorpion, "#d08a3a"),
    "horn": ("Жук", h_beetle, "#8aa040"), "acid": ("Бочонок", h_barrel, "#9ae030"), "carapace": ("Мокрица", h_isopod, "#8a96a8"),
    "jumper": ("Кузнечик", h_grass, "#a8b040"), "scythes": ("Богомол", h_mantis, "#e080b0"),
    "firefly": ("Светлячок", h_firefly, "#e8f070"), "spitter": ("Паук-плевун", h_spitter, "#d8d0c0"),
}
FORM_KEY = {None: "ant", "wings": "wasp", "stinger": "scorpion", "horn": "beetle", "acid": "barrel", "carapace": "isopod",
            "jumper": "grasshopper", "scythes": "mantis", "firefly": "firefly", "spitter": "spitter"}


def dress(sc, form, spec):
    """The card made the form's: its place in the portrait's well, the creature back in it, the edge in its
    colour, its icon on the wing."""
    nm, hab, col = FORM[form]
    hab(sc, X0, Y0, X1, Y1)
    put(sc, spec["sprite"], 159 + spec.get("dx", 0), 268, spec.get("sw", 40))
    SH._rim(sc, col)
    icon(sc, "ant" if form is None else form, 600, 6, 2)


CLASS = [("ant", "класс", "Стая", "", INK), ("biomass", "класс", "Пожирание", "", INK)]
ARMOR = {"хитин": ("carapace", "класс", "Хитин", "", INK), "тяж": ("carapace", "класс", "Тяжёлый хитин", "", INK),
         "мягк": ("acid", "класс", "Мягкое тело", "", INK)}
FX_MORE = {   # the forms' abilities in terms (fxg.py), for the tooltip
    "Закрыть брешь": ["{гибель_своя} {радиус:1} → {свой} на её {клетка}"],
    "Полёт": ["{всегда} → {полёт} {скорость:+1}", "{начало} → {цель} стрелки, {лидер}"],
    "Хрупкая": ["{огонь} → падает", "сбили → падает"],
    "Плевок": ["{атака} {дальность:3} → {кисл} {броня:−1}"],
    "Лопается": ["{гибель} {радиус:1} → {кисл:1–4} всем, своим тоже"],
    "Мягкое тело": ["{всегда} → {кол} ×2"],
    "Разгон": ["{начало} {атака} → {урон:×1,5}, отбрасывает", "{атака} → {дроб}"],
    "Медленный": ["{всегда} → {скорость:1}"],
    "Тяжёлый хитин": ["{всегда} → {руб} ×½ · {кол} ×½ · {дроб} ×2"],
    "Шипы": ["{рана} вплотную → {кол:1–3} в ответ"],
    "Сворачивается": ["{здоровье} < ½ → {броня:+3}, не бьёт"],
    "Слабый удар": ["{урон:−1} · {скорость:1}"],
    "Прыжок": ["{начало} → через строй к дальнему", "приземление {радиус:1} → {оглушение} мелким"],
    "Один в тылу": ["после прыжка → один, окружён"],
    "Серпы": ["{атака} → {руб} ×2 за ход", "{всегда} → {инициатива:+2}"],
    "Одиночка": ["Стая → ✕"],
    "Вспышка": ["{каждые:3} → {радиус:1} враги {мимо}"],
    "Светится": ["{всегда} → стрелки бьют его первым"],
}


def worker(hp, armor="0 {хитин}", speed="3"):
    return [("здоровье", str(hp)), ("броня", armor), ("скорость", speed), ("боевой дух", "6"), ("размер", "1"),
            ("предел роя", "1")]


def soldier(hp, armor="2 {хитин}", speed="2"):
    return [("здоровье", str(hp)), ("броня", armor), ("скорость", speed), ("боевой дух", "9"), ("размер", "2"),
            ("предел роя", "3")]


SPECS = [   # form, seed, caste, how big, stats, attacks, its own abilities, armour class, how many, killed
    (None, 81, "рабочая", 4.6, worker(8), [("ant", "Укус", "1–4 +1", "{кол}", "1", "")],
     [("ant", "форма", "Закрыть брешь", "", GOLD)], "хитин", 19, 14),
    ("wings", 83, "рабочая", 4.2, worker(8, speed="4"), [("wings", "Жало", "1–4 +1", "{кол}", "1", "")],
     [("wings", "форма", "Полёт", "", GOLD), ("fear", "слабость", "Хрупкая", "", RED)], "хитин", 4, 6),
    ("acid", 85, "рабочая", 4.2, worker(11, armor="0 {мягкое}"), [("acid", "Плевок", "1–6 +1", "{кисл}", "3", "{броня:−1}")],
     [("acid", "форма", "Плевок", "", GOLD), ("fear", "слабость", "Лопается", "", RED)], "мягк", 2, 3),
    ("horn", 87, "солдат", 3.0, soldier(12, armor="2 {тяжхитин}", speed="1"),
     [("horn", "Рог", "1–8", "{дроб}", "1", "{начало} → {урон:×1,5}")],
     [("horn", "форма", "Разгон", "", GOLD), ("fear", "слабость", "Медленный", "", RED)], "тяж", 2, 5),
    ("carapace", 89, "солдат", 3.0, soldier(11, armor="3 {тяжхитин}", speed="1"), [("carapace", "Жвалы", "1–8 −1", "{руб}", "1", "")],
     [("carapace", "форма", "Шипы", "", GOLD), ("carapace", "форма", "Сворачивается", "", GOLD),
      ("fear", "слабость", "Слабый удар", "", RED)], "тяж", 1, 1),
    ("jumper", 91, "рабочая", 4.2, worker(8), [("jumper", "Укус", "1–4 +1", "{кол}", "1", "")],
     [("jumper", "форма", "Прыжок", "", GOLD), ("fear", "слабость", "Один в тылу", "", RED)], "хитин", 3, 4),
    ("scythes", 93, "солдат", 3.0, soldier(11), [("scythes", "Серпы", "1–8 ×2", "{руб}", "1", "{инициатива:+2}")],
     [("scythes", "форма", "Серпы", "", GOLD), ("fear", "слабость", "Одиночка", "", RED)], "хитин", 2, 7),
    ("firefly", 95, "рабочая", 4.4, worker(8), [("firefly", "Укус", "1–4", "{кол}", "1", "")],
     [("firefly", "форма", "Вспышка", "", GOLD), ("fear", "слабость", "Светится", "", RED)], "хитин", 3, 2),
]


def card(form, seed, caste, k, stats, attacks, own, armor, n, killed, save=True):
    nm = FORM[form][0]
    traits = () if form is None else (form,)
    abilities = own + ([] if form == "scythes" else [CLASS[0]]) + [CLASS[1], ARMOR[armor]]
    spec = dict(seed=seed, title=nm.upper(), sub=caste, cell="normal",
                sprite=bug(traits, "idle", k, seed, soldier=caste == "солдат"), sw=40,
                facts=[("val", "убито стаей в прошлом бою", str(killed), (150, 220, 120)), ("val", "таких в рое", str(n), INK)],
                stats=stats, attacks=attacks,
                below=("ПОТОМКАМ", [("ant" if form is None else form, nm if form is None else
                                     {"wings": "Крылья", "acid": "Кислотная железа", "horn": "Рог", "carapace": "Панцирь",
                                      "jumper": "Прыгучие ноги", "scythes": "Серпы", "firefly": "Светящееся брюшко"}[form],
                                     "{наследие}", GOLD)]),
                abilities=abilities, hover=None)
    sc = SH.big_card(spec, None, save=False)
    dress(sc, form, spec)
    if not save:
        return sc
    name = f"swarm_card_{FORM_KEY[form]}.png"
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)
    return sc


def scorpion_dressed():
    """The scorpion's card (swarm_hud.cards) in its own frame too."""
    import swarm_hud as H
    keep = H.big_card
    got = {}

    def grab(spec, name, save=True):
        if name == "swarm_card.png":
            sc = keep(spec, name, save=False)
            dress(sc, "stinger", spec)
            img = sc.image(S)
            UI.WOBBLE[0] = 0.0
            img.save(out(name))
            print(name, img.size)
            got["sc"] = sc
            return sc
        return None
    H.big_card = grab
    try:
        H.cards()
    finally:
        H.big_card = keep
    return got.get("sc")


def frames_sheet():
    """The ten forms' wells side by side: each form's place, the creature in it."""
    from kit import Scene
    W_, H_ = 5 * 190 + 10, 2 * 230 + 50
    sc = UI.nest(W_, H_, 9)
    UI.wing(sc, 0, 0, W_, 40)
    SH.letters(sc, "КАРТОЧКИ ОСОБЕЙ: У КАЖДОЙ ФОРМЫ СВОЯ НИША", W_ // 2, 8, "title", 16, col=(240, 196, 110),
               col2=(170, 110, 50), align="center")
    for i, form in enumerate(FORM):
        nm, hab, col = FORM[form]
        x0, y0 = 10 + (i % 5) * 190, 50 + (i // 5) * 230
        UI.cell(sc, x0, y0, x0 + 180, y0 + 200, "normal", col=col)
        hab(sc, x0 + 6, y0 + 6, x0 + 174, y0 + 170)
        traits = () if form is None else (form,)
        put(sc, bug(traits, "idle", 2.6 if form not in ("horn", "carapace", "scythes") else 1.9, 81 + 2 * i,
                    soldier=form in ("horn", "carapace", "scythes")), x0 + 90, y0 + 156, 26)
        SH.letters(sc, nm, x0 + 90, y0 + 176, "text", 16, col=hexc(col), align="center", jitter=1, seed=i)
    img = sc.image(S)
    img.save(out("swarm_cards_forms.png"))
    print("swarm_cards_forms.png", img.size)


if __name__ == "__main__":
    SH.ABIL_FX.update(FX_MORE)
    for args in SPECS:
        card(*args)
    scorpion_dressed()
    frames_sheet()
