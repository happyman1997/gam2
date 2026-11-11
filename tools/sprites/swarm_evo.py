"""Evolution of the swarm's forms: three evolutions for each of the ten forms. One is bought at a time in the brood,
for biomass, and acts on every creature whose body is that form — those alive and those still to hatch. Each shows on
the sprite, so a bred line reads on the field: acid-glowing ant gasters, a wasp's long syringe of a sting, a
scorpion's vice claws, a barrel's warning bands, a beetle's second horn, an isopod's lime crust, the locust's
yellow-and-black, a mantis's orchid petals, a firefly's hood.

    python3 tools/sprites/swarm_evo.py      -> out/swarm_evolution.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, rot_z, rot_x, rot_y, I3
import swarm1 as W
from swarm1 import spike, rings, M_BONE, M_FANG, M_SHEEN, M_ACID, M_ICHOR, M_LANTERN, M_DARKEYE, M_WING, M_EYE, AMBER, ELYTRA

PLATE_E = Mat(ramp("#08070c", "#1a1622", "#302a3c", "#544c66", "#9a90b4"))            # a darker helmet of plates
WING_T = Mat(ramp("#120a04", "#2a1808", "#4e3010", "#80521c", "#b47e34"), dither=True)   # stiff amber wings
WING_TN = Mat(ramp("#160c04", "#321c0a", "#5a3a14", "#8e6024", "#c4903e"))
NEURO = Mat(ramp("#1e0a30", "#46186a", "#7a30b0", "#b070e8", "#e8c8ff"), emissive=hexc("#a060f0"), glow_r=5, glow_k=0.45)
WARN = Mat(ramp("#140c02", "#3a2806", "#76560c", "#c09a1a", "#f0d050"))
LIME = Mat(ramp("#2a2a2c", "#4a4a4c", "#747270", "#a4a09a", "#d4d0c6"), dither=True)
LOCUST = ["#0a0802", "#262006", "#56460e", "#9a821e", "#e2ca50"]
PETAL = Mat(ramp("#2a1420", "#6a3450", "#b06a8a", "#e0a8c0", "#fbe4ee"))
SPOT_RING = Mat(ramp("#060406", "#100a10", "#1c141c", "#2a202a", "#3a2e3a"))
SPOT_IRIS = Mat(ramp("#3a2a06", "#7a5a0e", "#c09a1a", "#f0d050", "#fff4b0"), emissive=hexc("#e0c040"), glow_r=2, glow_k=0.2)
LURE = Mat(ramp("#401006", "#8a2a0a", "#d0601a", "#f4a040", "#ffe0a0"), emissive=hexc("#ff8a30"), glow_r=6, glow_k=0.5)
BRIGHT = Mat(ramp("#5a5214", "#a0901c", "#e2cc3a", "#faf088", "#ffffe0"), emissive=hexc("#fff080"), glow_r=22, glow_k=0.95)

# form (its main trait; None — the ant) → three evolutions: key, name, what it does, how it looks
EVO = {
    None: [("formic", "Муравьиная кислота", "пробивший укус снимает 1 броню, литому металлу 2", "брюшко светится кислотой"),
           ("phalanx", "Сомкнутый строй", "вставший в брешь: +1 к броне до конца боя", "щитки на голове и груди"),
           ("bridge", "Живой мост", "трое своих рядом — стена и постройка его не держат", "крючья на лапах")],
    "wings": [("syringe", "Жало-шприц", "жало не замечает 2 брони", "длинное жало"),
              ("tough", "Жёсткие крылья", "подожжённая или сбитая не падает, огонь вдвое слабее", "тёмные янтарные крылья"),
              ("dive", "Пикирование", "первый удар после перелёта строя двойной", "лапы-крючья с шипами")],
    "stinger": [("vise", "Клешни-тиски", "держит соседнего врага, клешни бьют дробящим", "огромные клешни"),
                ("neuro", "Нейротоксин", "пробивший удар: −1 к скорости и −2 к инициативе", "мешок жала светится"),
                ("longlegs", "Длинные лапы", "больше не медлительный", "высокие лапы")],
    "acid": [("farspit", "Дальний плевок", "плевок на 4 клетки, через головы своих", "хоботок-сопло"),
             ("scent", "Свой запах", "лопаясь, не задевает своих", "предупреждающие полосы"),
             ("pool", "Едкая лужа", "плевок оставляет лужу на 2 раунда: −1 брони за раунд", "поры и пузыри на брюшке")],
    "horn": [("forked", "Двойной рог", "Разгон каждые 3 хода, а не один раз", "второй рог со спины"),
             ("bosses", "Бугристые надкрылья", "+2 брони против стрел и снарядов", "бугры на надкрыльях"),
             ("flyer", "Летучий жук", "разгоняется с подлёта, перелетая своих", "раскрытые крылья")],
    "carapace": [("longspines", "Длинные шипы", "шипы ранят 1–4, свернувшись, колет всех соседей", "шипы вдвое длиннее"),
                 ("lime", "Известковый панцирь", "свернувшись, +5 брони и дробящий не ломает", "каменная корка"),
                 ("flanges", "Щитовые края", "соседние свои получают +1 к броне", "широкие боковые пластины")],
    "jumper": [("locust", "Стадная фаза", "прыгают стаей и приземляются рядом друг с другом", "окраска саранчи"),
               ("shins", "Шипастые голени", "приземление бьёт цель шипами, колющий 1–6", "шипы на голенях"),
               ("farjump", "Дальний прыжок", "прыжок через всё поле, к лидеру или стрелку", "ноги длиннее")],
    "scythes": [("saws", "Серпы-пилы", "третий удар за раунд по цели ниже половины здоровья", "зубья-пилы"),
                ("orchid", "Цветочная мимикрия", "пока не ударил, стрелки и удары по площади его не видят", "лепестки"),
                ("eyespots", "Глазчатые крылья", "в первом раунде соседние враги проверяют страх 1–6", "крылья с глазками")],
    "spitter": [("net", "Ловчая сеть", "плевок клеит и соседнего врага", "зигзаги шёлка на брюшке"),
                ("recoil", "Отскок на нити", "дошли вплотную — отпрыгивает на нити на 2 клетки назад", "нить петлёй со спины"),
                ("pull", "Стащить со стены", "приклеенный стрелок на стене или башне падает вниз", "крючья на передних лапах")],
    "firefly": [("bright", "Яркий фонарь", "вспышка каждые 2 хода", "фонарь крупнее"),
                ("hood", "Капюшон", "гасит фонарь: стрелки больше не целятся в него первым", "капюшон над фонарём"),
                ("lure", "Ложный сигнал", "раз в 3 хода враг до 2 клеток шагает к нему", "двухцветный фонарь")],
}
FORM_NAME = {None: "Муравей", "wings": "Оса", "stinger": "Скорпион", "acid": "Бочонок", "horn": "Жук", "carapace": "Мокрица",
             "jumper": "Кузнечик", "scythes": "Богомол", "firefly": "Светляк", "spitter": "Паук-плевун"}


def before(g, mc, primary, evo, hue):
    """What changes before the body is laid out: proportions and colour."""
    g = dict(g)
    if "longlegs" in evo:
        g["leg"] = g["leg"] * 1.4
    if "farjump" in evo:
        g["hind"] = 1.35
    if "locust" in evo and primary == "jumper":
        import colorsys
        out = []
        for c in LOCUST:
            r, gg, b = (hexc(c) / 255).tolist()
            h, l, s = colorsys.rgb_to_hls(r, gg, b)
            r, gg, b = colorsys.hls_to_rgb((h + hue) % 1.0, l, s)
            out.append(np.array([r * 255, gg * 255, b * 255], dtype=np.float32))
        mc = Mat(out)
    return g, mc


def wings(a, evo):
    if "tough" in evo:
        a["wing_far"], a["wing_near"] = WING_T, WING_TN


def add(m, mc, a, primary, evo, pose, g):
    y0, hc, hs, gc, gr = a["y0"], a["hc"], a["hs"], a["gc"], a["gr"]
    if "formic" in evo:
        t = a["tip"]
        m.ell(gc + (-gr * 0.55, -gr * 0.05, 0), (gr * 0.75, gr * 0.85, gr * 0.85), M_ACID)       # the acid gland shows through
        m.ell(t + (0.9, 0.5, 0), (1.6, 1.3, 1.3), M_ACID)
        m.ell(t + (0.4, -1.4, 0), (0.55, 0.9, 0.55), M_ACID)
        m.ell(t + (0.2, -3.2, 0), (0.4, 0.6, 0.4), M_ACID)
    if "phalanx" in evo:
        for c, r, R in ((hc + (-0.1, 1.4 * hs, 0), (2.5 * hs, 1.1, 2.4 * hs), I3), ((0.6, y0 + 2.8, 0), (3.4, 1.1, 2.6), rot_z(0.22)),
                        ((-6.8, y0 + 0.4 + gr * 0.92, 0), (gr * 1.0, 0.9, gr * 0.85), rot_z(0.25))):
            c = np.array(c)
            m.ell(c, r, PLATE_E, R)
            m.ell(c + (0.3, r[1] * 0.75, 0), (r[0] * 0.55, 0.3, r[2] * 0.5), M_SHEEN, R)
            for z in (1, -1):
                spike(m, c + (0, 0, z * r[2] * 0.9), c + (-0.8, 0.9, z * (r[2] + 1.2)), 0.35, M_BONE)
    if "bridge" in evo:
        for f in a["feet"]:
            s = np.sign(f[2]) or 1
            m.cyl(f + (0.3, 0.1, 0), f + (2.0, 0.8, 0.5 * s), 0.42, M_BONE, r1=0.3, seg=5)
            m.cyl(f + (2.0, 0.8, 0.5 * s), f + (2.4, 2.4, 0.7 * s), 0.3, M_BONE, r1=0.06, seg=4)
    if "syringe" in evo:
        t = a["tip"]
        d = (t - gc) / (np.linalg.norm(t - gc) + 1e-9)
        m.cyl(t - d * 0.5, t + d * 7.0, 0.7, M_BONE, r1=0.06, seg=5)
        m.ell(t + d * 2.4 + (0, 0.5, 0), (1.0, 0.25, 0.4), M_SHEEN)
        m.ell(t + d * 7.4, (0.35, 0.35, 0.35), M_ICHOR)
    if "dive" in evo and a.get("fore") is not None:
        f0 = a["fore"]
        for side in (1, -1):
            base = f0 + (0, 0, 1.0 * side)
            elbow = base + (1.4, -2.2, 1.3 * side)
            tip = elbow + (2.6, 1.8, 0.4 * side)
            elbow = base + (1.8, -3.0, 1.6 * side)
            tip = elbow + (3.4, 2.4, 0.4 * side)
            m.cyl(base, elbow, 0.75, mc, seg=5)
            m.cyl(elbow, tip, 0.7, Mat(AMBER), r1=0.3, seg=5)
            m.cyl(tip, tip + (0.8, -2.0, 0), 0.4, M_BONE, r1=0.05, seg=4)
            for f in (0.3, 0.6, 0.9):
                p = elbow + (tip - elbow) * f
                spike(m, p, p + (0.4, 1.4, 0.2 * side), 0.3, M_BONE)
    if "vise" in evo:
        for c in a.get("claws", []):
            s = np.sign(c[2])
            m.ell(c + (0.6, 0.3, 0), (3.4, 2.1, 2.0), M_BONE)
            spike(m, c + (3.0, 1.4, 0), c + (6.6, 1.4, -s * 0.8), 0.9, M_FANG)
            spike(m, c + (3.0, -0.5, 0), c + (6.2, -1.0, -s * 0.6), 0.7, M_FANG)
            for k in range(3):
                spike(m, c + (4.0 + k, 0.9, -s * 0.2), c + (4.2 + k, 0.0, -s * 0.4), 0.18, M_FANG)
    if "neuro" in evo and a.get("bulb") is not None:
        b = a["bulb"]
        m.ell(b, (2.2, 1.8, 1.8), NEURO)
        m.ell(b + (1.6, -1.6, 0), (0.4, 0.6, 0.4), NEURO)
    if "farspit" in evo:
        m.cyl(hc + (1.0 * hs, -0.7 * hs, 0), hc + (4.8 * hs, -1.6 * hs, 0), 0.75 * hs, mc, r1=0.45 * hs, seg=6)
        m.ell(hc + (5.0 * hs, -1.65 * hs, 0), (0.5, 0.7 * hs, 0.7 * hs), M_ACID)
    if "scent" in evo:
        rings(m, gc, I3, gr * 1.1, gr, WARN, n=3)
    if "pool" in evo:
        rng = np.random.default_rng(4)
        for _ in range(9):
            th, ph = rng.uniform(0.2, 1.3), rng.uniform(-0.3, 1.6)
            n = np.array((np.sin(th) * np.cos(ph) * 0.9, np.cos(th), np.sin(th) * np.sin(ph)))
            m.ell(gc + n * gr * 1.02, (0.55, 0.55, 0.55), M_ACID)
        for i, (dx, dy) in enumerate(((0.2, 1.4), (-0.4, 2.6), (0.5, 3.6))):
            m.ell(gc + (dx * gr, gr + dy, 0.3), (0.5 + 0.15 * i, 0.5 + 0.15 * i, 0.5), M_ACID)
    if "forked" in evo:
        hr = Model()
        hr.cyl((1.6, y0 + 4.4, 0), (4.6, y0 + 9.6, 0), 1.4, M_BONE, r1=1.0, seg=6)
        hr.cyl((4.6, y0 + 9.6, 0), (8.6, y0 + 10.6, 0), 1.0, M_BONE, r1=0.6, seg=6)
        hr.cyl((8.6, y0 + 10.6, 0), (10.4, y0 + 8.4, 0), 0.6, M_BONE, r1=0.08, seg=5)
        for z in (1, -1):
            spike(hr, (6.4, y0 + 10.2, 0), (6.8, y0 + 8.6, 0.8 * z), 0.35, M_BONE)
        m.extend(hr)
    if "bosses" in evo:
        lite = Mat(W.chitin_shift(Mat(ELYTRA), 0.0, light=1.3))
        gs = gr / 3.9
        for x in np.arange(-9.0, 0.6, 2.2):
            for z in (-2.8, -0.9, 0.9, 2.8):
                q = 1 - ((x + 4.0) / (6.6 * gs)) ** 2 - (z / (4.9 * gs)) ** 2
                if q > 0.05:
                    m.ell((x, y0 + 2.0 + 3.9 * gs * np.sqrt(q), z), (1.0, 0.75, 1.0), lite)
    if "flyer" in evo:
        r0 = np.array((-1.0, y0 + 4.2, 0))
        up = 0.0 if pose == "idle" else 2.0
        for z in (-1.2, 1.2):
            s = np.sign(z)
            m.poly([r0 + (0.4, 0, z), r0 + (-10.0, 3.6 + up, z + 7.4 * s), r0 + (-8.0, 6.4 + up, z + 8.0 * s),
                    r0 + (-2.6, 4.2 + up, z + 3.2 * s)], WING_T if z < 0 else WING_TN)
            m.limb([r0 + (0.2, 0.3, z), r0 + (-9.0, 4.6 + up, z + 7.6 * s)], 1, Mat(ELYTRA), band=2)
    if primary == "carapace" and evo:
        gs = gr / 2.8
        for i in range(7):
            x = 3.2 - i * 2.2
            k = 1.0 - abs(i - 2.2) * 0.08
            top = y0 + 1.2 + 2.8 * k * gs
            if "longspines" in evo:
                spike(m, (x, top - 0.4, 0), (x - 2.6, top + 4.6, 0), 0.8, M_BONE)
                for z in (1, -1):
                    spike(m, (x, y0 + 1.6, z * 3.4 * k * gs), (x - 1.2, y0 + 3.6, z * (4.4 * k * gs + 2.6)), 0.5, M_BONE)
            if "lime" in evo and i % 2 == 0:
                for z in (-2.2, 0.0, 2.2):
                    m.ell((x + 0.3, top - 0.3 - abs(z) * 0.3, z), (1.5, 0.75, 1.3), LIME)
            if "flanges" in evo:
                for z in (1, -1):
                    m.ell((x, y0 + 1.0, z * (4.4 * k * gs + 1.2)), (1.7, 0.6, 2.6), Mat(W.chitin_shift(mc, -0.18, sat=0.5, light=1.6)),
                          rot_x(-0.3 * z))
    if "shins" in evo:
        for knee, foot, side in a.get("hind_legs", []):
            for f in (0.2, 0.42, 0.64, 0.86):
                p = knee + (foot - knee) * f
                spike(m, p, p + np.array((-1.6, 1.4, 0.5 * side)), 0.42, M_BONE)
    if "saws" in evo:
        for elbow, tip, side in a.get("scythes", []):
            for f in np.linspace(0.18, 0.92, 7):
                p = elbow + (tip - elbow) * f
                d = (tip - elbow) / np.linalg.norm(tip - elbow)
                inner = np.array((-d[1], d[0], 0)) * (1 if d[1] < 0 else -1)
                spike(m, p, p + inner * 1.9 + d * 0.5, 0.45, M_BONE)
    if "orchid" in evo:
        for elbow, tip, side in a.get("scythes", []):
            m.ell(elbow + (-0.6, -0.4, 0.8 * side), (1.8, 1.0, 0.5), PETAL, rot_z(0.6))
        for i, x in enumerate((-3.0, -6.0, -9.0)):
            for z in (1, -1):
                m.ell((x, y0 + 1.6, z * 2.6), (1.6, 1.1, 0.5), PETAL, rot_x(0.5 * z) @ rot_z(-0.3))
        for p in a["feet"][:2]:
            m.ell(p + (0, 2.6, 0), (1.2, 0.8, 0.4), PETAL)
    if "eyespots" in evo:
        r0 = np.array((-1.6, y0 + 2.6, 0))
        lift = 1.0 if pose == "idle" else 1.4
        for z in (-1, 1):
            s = z
            pts = [r0 + (0, 0, 0.8 * s), r0 + (-5.0, 7.6 * lift, 2.6 * s), r0 + (-9.0, 5.2 * lift, 3.8 * s),
                   r0 + (-8.0, 0.8, 3.0 * s)]
            m.poly(pts, Mat(W.chitin_shift(mc, 0.33, sat=0.7)))
            c = (pts[1] + pts[2] + pts[3]) / 3 + (0, 0, 0.35 * s)
            m.ell(c, (1.5, 1.5, 0.3), SPOT_RING)
            m.ell(c + (0, 0, 0.12 * s), (0.9, 0.9, 0.3), SPOT_IRIS)
            m.ell(c + (0.1, 0.1, 0.22 * s), (0.4, 0.4, 0.3), M_DARKEYE)
    if primary == "spitter" and evo:
        SILK = Mat(ramp("#2a2622", "#5a544a", "#948c7e", "#c8c0b0", "#f0eadc"))
        if "net" in evo:                                       # zigzag silk bands over the abdomen
            for k in range(7):
                x = gc[0] - gr * 0.9 + k * gr * 0.3
                y = gc[1] + gr * 0.95 + (0.5 if k % 2 else -0.3)
                m.ell((x, y, 0), (0.55, 0.3, gr * 0.7), SILK)
        if "recoil" in evo:                                    # a dragline looping up from the spinnerets
            t = a["tip"]
            pts = [t + (-1.0 * k, 1.6 * k - 0.1 * k * k, 0.3 * k) for k in range(8)]
            pts += [pts[-1] + (1.2 * k, 0.6 * k, 0.2) for k in range(1, 5)]
            for p, q in zip(pts[:-1], pts[1:]):
                m.cyl(p, q, 0.22, SILK, seg=3)
        if "pull" in evo:                                      # hooks on the front feet
            for f in a["feet"]:
                if f[0] > 3.0:
                    s = np.sign(f[2]) or 1
                    m.cyl(f, f + (1.6, 1.4, 0.3 * s), 0.45, M_BONE, r1=0.3, seg=5)
                    m.cyl(f + (1.6, 1.4, 0.3 * s), f + (2.6, 0.6, 0.3 * s), 0.3, M_BONE, r1=0.06, seg=4)
    if primary == "firefly" and evo:
        lan = a["tip"]
        if "bright" in evo:
            m.ell(lan + (-0.6, 0.1, 0), (3.5, 2.9, 3.4), BRIGHT)
        if "lure" in evo:
            for dx in (-1.8, 0.0, 1.6):
                m.ell(lan + (dx, 0, 0), (0.75, 2.6, 3.1), LURE)
        if "hood" in evo:
            m.ell(lan + (0.6, 1.4, 0), (3.2, 1.5, 3.2), mc)
            m.ell(lan + (-1.8, 0.6, 0), (1.2, 1.6, 3.0), mc)


def sheet():
    """Every form: as bred, each of its three evolutions, and all three together."""
    from PIL import ImageFont
    from leaders_sheet import canvas, put, fonts, S, GOLD, INK, MUT
    from paths import out, font
    K = 2.6
    forms = [None, "wings", "stinger", "acid", "horn", "carapace", "jumper", "scythes", "firefly", "spitter"]
    RH, Y0, X0, CWD = 104, 92, 120, 168
    WW, HH = 960, Y0 + len(forms) * RH + 12
    sc = canvas(WW, HH, 41)
    labels = []
    for r, f in enumerate(forms):
        by = Y0 + r * RH + 62
        traits = () if f is None else (f,)
        keys = [k for k, *_ in EVO[f]]
        variants = [()] + [(k,) for k in keys] + [tuple(keys)]
        for j, ev in enumerate(variants):
            cx = X0 + 30 + j * CWD if j < 4 else X0 + 30 + 3 * CWD + 132
            spr = W.build(traits, 0.0, "idle", False, k=K, genes=W.genes_for(11 + r), evo=ev)
            put(sc, spr, cx, by, 16)
            if 0 < j < 4:
                _, name, what, _ = EVO[f][j - 1]
                labels.append(("evo", cx, by + 6, name, what))
            elif j == 4:
                labels.append(("all", cx, by + 6, "все три", ""))
        labels.append(("form", 16, by - 40, FORM_NAME[f], ""))
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    small = ImageFont.truetype(font("PTSerif-Regular.ttf"), 13)
    d.text((24, 16), "Рой: эволюция форм", font=ft, fill=INK)
    d.text((24, 60), "У каждой формы три эволюции. Их берут по одной в выводке за биомассу, в любом порядке; эволюция "
                     "действует на всех особей этой формы, нынешних и будущих,", font=fr, fill=MUT)
    d.text((24, 84), "и видна на спрайте. Слева — форма как есть, справа — со всеми тремя.", font=fr, fill=MUT)
    for kind, x, y, name, what in labels:
        if kind == "form":
            d.text((x * S, y * S), name, font=fh, fill=GOLD)
            continue
        d.text((x * S - d.textlength(name, font=fbs) / 2, y * S), name, font=fbs, fill=INK)
        if what:
            words, lines, cur = what.split(" "), [], ""
            for wd in words:
                if d.textlength(cur + " " + wd, font=small) > (CWD - 12) * S and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = (cur + " " + wd).strip()
            lines.append(cur)
            for n, ln in enumerate(lines[:2]):
                d.text((x * S - d.textlength(ln, font=small) / 2, y * S + 22 + n * 17), ln, font=small, fill=MUT)
    img.save(out("swarm_evolution.png"))
    print("swarm_evolution.png", img.size)


if __name__ == "__main__":
    sheet()
