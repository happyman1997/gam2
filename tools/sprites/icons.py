"""Module icons: 16×16 pixel icons for the Foundry's modules.

They are made from sprites of the CC0 dataset Angais/pixel-art-atlas-1.4m
(https://huggingface.co/datasets/Angais/pixel-art-atlas-1.4m, public domain, CC0 1.0) and reworked for the game:
recoloured into the Foundry's palettes (iron, brass, copper, fire, the arc's blue, the frames' own paints, the
Maniac's purple for his modules), turned to face right like our creatures, given our outline and a rim light along
the top edge. Only the reworked icons are kept in the repository (assets/module_icons.png); the dataset is not.

    python3 tools/sprites/icons.py <dir with the dataset's tokens.npy, palette.npy>   -> assets/module_icons.png, .json
    icons.icon("long", 5)  -> a Sprite of the «Длинный ствол» icon, 5× (nearest), centred on (ox, oy)
"""
import json
import os
import colorsys
import numpy as np
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(HERE, "assets", "module_icons.png")
INDEX = os.path.join(HERE, "assets", "module_icons.json")

R = {   # target ramps, dark → light
    "iron": ramp("#141519", "#262930", "#3c414c", "#5c6372", "#8d95a6"),
    "steel": ramp("#1e2228", "#3a404a", "#606874", "#949ca8", "#d0d6de"),
    "brass": ramp("#1c1206", "#3e2a0e", "#6a4a1a", "#9a722c", "#cca04a"),
    "copper": ramp("#2a1006", "#5a240e", "#8a4018", "#b8662a", "#e09a50"),
    "fire": ramp("#5a1408", "#a8320e", "#e86a1a", "#ffb43a", "#fff3c0"),
    "ember": ramp("#3a0e06", "#7a2208", "#c2500e", "#f08a2a", "#ffd890"),
    "volt": ramp("#0e2a3a", "#16607a", "#2ab0c8", "#7ae8f0", "#e8fffd"),
    "wood": ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844"),
    "stone": ramp("#22202a", "#3e3a46", "#5e5a68", "#86828e", "#b2aeb8"),
    "red": ramp("#2a0606", "#5a0e0e", "#9a1c1c", "#d0402e", "#f08060"),
    "blue": ramp("#06142a", "#0e2a6a", "#1a50b0", "#3a8ae8", "#90c8ff"),
    "mad": ramp("#2a0a2a", "#5a1460", "#9a2aa0", "#d860d0", "#ffc0f4"),
    "madg": ramp("#0a2a10", "#145a20", "#2aa040", "#70e080", "#d0ffd8"),
    "ochre": ramp("#1e1404", "#46300a", "#76561a", "#a8822a", "#d6b048"),
}


def paints():
    from frames import PAINT
    return {"Страж": PAINT["Страж"], "Мудрец": PAINT["Мудрец"], "Горн": PAINT["Горн"], "Орудие": PAINT["Орудие"],
            "Механик": PAINT["Механик"]}


BASE = dict(grey="iron", warm="brass", red="red", green="iron", blue="steel", purple="steel", brown="wood")
FIREY = dict(warm="fire", red="fire", brown="ember")
VOLTY = dict(warm="volt", blue="volt", purple="volt", green="volt")

# key: (dataset row, name, whose, recolouring)
ICONS = {
    # Страж
    "tower": (1336617, "Ростовой щит", "Страж", dict(grey="paint", brown="paint", red="paint", warm="brass")),
    "intercept": (1280921, "Перехват", "Страж", dict(grey="paint", warm="brass", red="ember")),
    "anchor": (840513, "Якорь", "Страж", dict(grey="paint", brown="wood")),
    "plates": (373358, "Броневые листы", "Страж", dict(grey="steel")),
    "counter": (1069589, "Контрудар", "Страж", dict(grey="paint", red="ember", warm="ember")),
    "hot": (180692, "Раскалённая броня", "Страж", dict(grey="iron", **FIREY)),
    # Мудрец
    "chain": (1280220, "Цепная молния", "Мудрец", dict(VOLTY, grey="steel")),
    "ground": (560255, "Разряд в землю", "Мудрец", dict(VOLTY, grey="copper")),
    "overload": (1324122, "Перегрузка", "Мудрец", dict(VOLTY, grey="copper", brown="copper", red="copper")),
    "fireball": (1408611, "Огненный шар", "Мудрец", dict(FIREY, grey="ember")),
    "firewall": (768204, "Огненная стена", "Мудрец", dict(FIREY, grey="iron")),
    "blades": (311098, "Раскалённые клинки", "Мудрец", dict(FIREY, grey="steel", blue="ember")),
    # Горн
    "magnet": (1369490, "Магнит", "Горн", dict(red="blue", grey="steel", warm="steel")),
    "rod": (430869, "Громоотвод", "Горн", dict(grey="copper", warm="copper", blue="volt", purple="volt", brown="iron")),
    "smoke": (98669, "Дымовая труба", "Горн", dict(grey="iron", red="paint", brown="paint", warm="paint")),
    "whistle": (163425, "Паровой свисток", "Горн", dict(warm="brass", brown="brass", grey="iron")),
    "maw": (675320, "Пасть топки", "Горн", dict(grey="iron", warm="fire", red="fire", brown="paint")),
    "greedy": (1317737, "Жадная топка", "Горн", dict(warm="fire", red="fire", grey="iron", blue="iron")),
    # Орудие
    "mortar": (203268, "Мортира", "Орудие", dict(grey="paint", brown="wood", warm="brass")),
    "long": (290083, "Длинный ствол", "Орудие", dict(grey="iron", warm="brass", brown="paint", green="paint")),
    "spider": (1313313, "Паучьи лапы", "Орудие", dict(grey="iron", green="ember", red="ember", purple="iron")),
    "canister": (1052381, "Картечь", "Орудие", dict(grey="iron", warm="brass", brown="wood")),
    "hotshot": (968115, "Калёное ядро", "Орудие", dict(grey="ember", warm="ember", brown="ember", red="fire")),
    "bomb": (379903, "Бомба с фитилём", "Орудие", dict(grey="iron", warm="fire", red="fire", brown="wood")),
    # Механик
    "repair": (1384031, "Ремонт", "Механик", dict(grey="steel", red="red", warm="brass")),
    "crane": (1189998, "Кран", "Механик", dict(grey="iron", warm="ochre", brown="ochre")),
    "spares": (1007341, "Запасные части", "Механик", dict(warm="brass", brown="brass", grey="steel")),
    "oiler": (388968, "Маслёнка", "Механик", dict(grey="steel", red="red", blue="steel")),
    "welding": (222617, "Сварка", "Механик", dict(grey="iron", red="red", warm="fire", blue="volt")),
    "oiltank": (432090, "Масляный бак", "Механик", dict(grey="iron", red="red", brown="iron")),
    # редкие
    "torch": (1269828, "Живой факел", "любой", dict(FIREY, brown="wood", grey="iron")),
    "nozzles": (544628, "Сопла", "любой", dict(grey="iron", warm="fire", red="fire", blue="steel")),
    "bounce": (34696, "Скачущее ядро", "любой", dict(grey="ember", warm="ember", brown="ember", red="fire")),
    "whirl": (1366504, "Огненный смерч", "любой", dict(FIREY, grey="ember")),
    "grapple": (1281104, "Крюк-кошка", "любой", dict(grey="steel", red="red", warm="brass", brown="wood")),
    "mill": (1060144, "Колёса-жернова", "любой", dict(grey="stone", brown="iron", warm="iron")),
    "dome": (695849, "Щит-купол", "любой", dict(grey="iron", brown="iron", red="brass", warm="brass")),
    "bombcore": (954892, "Котёл-бомба", "любой", dict(warm="brass", brown="brass", grey="steel", red="red")),
    "ram": (889163, "Таранный нос", "любой", dict(grey="iron", brown="wood", red="ember", green="iron")),
    "buffer": (377417, "Отбойник", "любой", dict(grey="steel", warm="brass", red="red", green="brass")),
    "spark": (760966, "Искрящий молот", "любой", dict(grey="iron", brown="wood", warm="ember")),
    "poker": (890934, "Кочерга", "любой", dict(grey="iron", **FIREY)),
    "tracks": (847591, "Гусеницы", "любой", dict(grey="iron", green="iron", brown="iron", warm="brass")),
    "flail": (1210211, "Кистень", "любой", dict(grey="iron", brown="wood", warm="brass")),
    # ядра
    "cast": (1279983, "Литое ядро", "ядро", dict(grey="steel", blue="steel")),
    "fire": (434937, "Огненное ядро", "ядро", dict(FIREY, grey="fire")),
    "volt": (320464, "Грозовое ядро", "ядро", dict(VOLTY, grey="volt")),
    # строительные модули Зодчего
    "w_tower": (317666, "Бойницы", "Зодчий", dict(grey="stone", red="red", warm="brass", brown="wood")),
    "w_wall": (1400503, "Щит-стена", "Зодчий", dict(red="stone", warm="stone", brown="stone", grey="stone")),
    "w_gate": (544292, "Створки", "Зодчий", dict(brown="wood", grey="iron", warm="brass", green="stone")),
    "w_pitch": (1295401, "Смоляной котёл", "Зодчий", dict(grey="iron", warm="fire", red="fire", brown="wood")),
    "w_press": (717768, "Пресс", "Зодчий", dict(brown="wood", grey="iron", warm="brass")),
    "w_thunder": (1178205, "Громовая вышка", "Зодчий", dict(VOLTY, grey="iron", brown="copper", red="copper")),
    "w_boom": (836849, "Подъёмная стрела", "Зодчий", dict(warm="ochre", grey="iron", red="ochre", brown="iron")),
    "w_forge": (990016, "Полевая кузня", "Зодчий", dict(grey="iron", red="fire", warm="fire")),
    # безумные модули Маньяка
    "c_saw": (1383557, "Ноги-пилы", "Маньяк", dict(grey="steel", red="mad", warm="mad", green="madg")),
    "c_catapult": (1323877, "Голова-катапульта", "Маньяк", dict(brown="wood", grey="iron", red="mad", green="madg")),
    "c_fist": (1375967, "Кулак на пружине", "Маньяк", dict(red="mad", warm="mad", grey="steel", green="madg")),
    "c_triple": (505863, "Рука-рука-рука", "Маньяк", dict(grey="iron", red="mad", warm="mad", blue="madg")),
    "c_upside": (967709, "Вверх ногами", "Маньяк", dict(grey="iron", red="mad", warm="mad", brown="iron")),
    "c_burning": (1193578, "Пылающая катапульта", "Маньяк", dict(grey="iron", **FIREY, green="madg")),
    "c_salute": (503143, "Салют", "Маньяк", dict(red="mad", warm="madg", grey="steel", blue="mad")),
    # аугменты Изобретателя
    "a_coil": (482268, "Грозовая катушка", "Изобретатель", dict(VOLTY, grey="iron", brown="copper", red="copper")),
    "a_mirror": (1273695, "Отражатель", "Изобретатель", dict(warm="brass", brown="brass", grey="steel", blue="volt")),
    "a_spring": (1099958, "Пружинный рывок", "Изобретатель", dict(grey="brass", blue="brass", warm="brass")),
}


def group(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    if s < 0.22 or v < 0.12:
        return "grey"
    if 15 <= h < 50 and v < 0.55 and s < 0.8:
        return "brown"
    if h < 15 or h >= 330:
        return "red"
    if h < 65:
        return "warm"
    if h < 170:
        return "green"
    if h < 260:
        return "blue"
    return "purple"


def rework(rgba, spec, owner):
    """The dataset sprite → our icon: mirrored, recoloured by colour groups into our ramps, our outline, a rim light."""
    rgba = rgba[:, ::-1].copy()
    a = rgba[..., 3] > 0
    rgb = rgba[..., :3].astype(float)
    lum = rgb @ np.array((0.299, 0.587, 0.114))
    groups = np.full(a.shape, "", dtype=object)
    for y, x in zip(*np.nonzero(a)):
        groups[y, x] = group(*rgba[y, x, :3])
    out = np.zeros((16, 16, 3), float)
    pt = paints()
    for gname in set(groups[a]):
        m = (groups == gname) & a
        target = dict(BASE, **spec).get(gname, "iron")
        rp = pt[owner] if target == "paint" else R[target]
        l = lum[m]
        lo, hi = np.percentile(l, 4), np.percentile(l, 96)
        t = np.clip((l - lo) / max(hi - lo, 1e-6), 0, 1)
        lift = 1.3 if target == "paint" else 0.9                   # the darkest goes to the outline anyway
        idx = np.clip(np.round(t * (4.0 - lift) + lift), 0, 4).astype(int)
        out[m] = np.array(rp)[idx]
    # our outline: everything on the edge of the shape, or darkest, becomes the outline colour
    pad = np.pad(a, 1)
    edge = a & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    dark = edge & (lum < 60)                                         # the source's own outline, where it was dark
    out[edge] = OUTLINE
    # rim light: the first painted pixel under the top outline gets lighter
    for x in range(16):
        ys = [y for y in range(16) if a[y, x] and not (edge | dark)[y, x]]
        if ys:
            y = ys[0]
            out[y, x] = out[y, x] * 0.55 + hexc("#d8d0e4") * 0.45
    res = np.zeros((16, 16, 4), np.uint8)
    res[..., :3] = np.clip(out, 0, 255).astype(np.uint8)
    res[..., 3] = a * 255
    return res


def build_atlas(src):
    from PIL import Image
    tokens = np.load(os.path.join(src, "tokens.npy"), mmap_mode="r", allow_pickle=False)
    palette = np.load(os.path.join(src, "palette.npy"), allow_pickle=False)
    keys = list(ICONS)
    cols = 10
    rows = (len(keys) + cols - 1) // cols
    atlas = np.zeros((rows * 16, cols * 16, 4), np.uint8)
    index = {}
    for n, key in enumerate(keys):
        row, name, owner, spec = ICONS[key]
        p = np.asarray(tokens[row]).reshape(16, 16)
        rgba = np.dstack((palette[p], (p != 0).astype("uint8") * 255)).astype(np.uint8)
        y, x = (n // cols) * 16, (n % cols) * 16
        atlas[y:y + 16, x:x + 16] = rework(rgba, spec, owner)
        index[key] = dict(cell=[n % cols, n // cols], name=name, owner=owner, source_row=row)
    os.makedirs(os.path.dirname(ASSET), exist_ok=True)
    Image.fromarray(atlas, "RGBA").save(ASSET)
    json.dump(dict(source="Angais/pixel-art-atlas-1.4m (CC0 1.0), reworked", icons=index), open(INDEX, "w"),
              ensure_ascii=False, indent=1)
    return atlas


_cache = {}


def icon_rgba(key):
    from PIL import Image
    if "atlas" not in _cache:
        _cache["atlas"] = np.array(Image.open(ASSET).convert("RGBA"))
        _cache["index"] = json.load(open(INDEX))["icons"]
    cx, cy = _cache["index"][key]["cell"]
    return _cache["atlas"][cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16]


def icon(key, z=5):
    """The icon as a Sprite, z× nearest, its centre at (ox, oy)."""
    rgba = np.repeat(np.repeat(icon_rgba(key), z, 0), z, 1)
    s = Sprite(16 * z, 16 * z)
    s.rgb = rgba[..., :3].astype(np.float32)
    s.a = rgba[..., 3] > 0
    s.ox, s.oy = 8 * z, 8 * z
    return s


def sheet(path, z=4):
    """All the icons with their names, for a look."""
    from PIL import Image, ImageDraw, ImageFont
    from paths import font
    keys = list(ICONS)
    cols = 8
    cw, ch = 16 * z + 150, 16 * z + 16
    rows = (len(keys) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw + 20, rows * ch + 20), (40, 34, 46))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font("PTSerif-Regular.ttf"), 14)
    for n, key in enumerate(keys):
        x, y = 10 + (n % cols) * cw, 10 + (n // cols) * ch
        im = Image.fromarray(np.repeat(np.repeat(icon_rgba(key), z, 0), z, 1), "RGBA")
        img.paste(im, (x, y), im)
        d.text((x + 16 * z + 6, y + 16 * z / 2 - 8), ICONS[key][1], font=f, fill=(230, 220, 196))
    img.save(path)


if __name__ == "__main__":
    import sys
    from paths import out
    if len(sys.argv) > 1:
        build_atlas(sys.argv[1])
    sheet(out("module_icons_sheet.png"))
    print(ASSET, out("module_icons_sheet.png"))
