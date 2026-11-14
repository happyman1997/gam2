"""Icons from the Pixel Art Atlas dataset — now only the swarm's (assets/swarm_icons.png). The Foundry's module icons
are drawn in code instead (icons_drawn.py → assets/module_icons.png); this module still reads that atlas
(icon(), icon_rgba()) and holds the ramps both use (R).

Originally: module icons, 16×16 pixel icons for the Foundry's modules.

They are made from sprites of the CC0 dataset Angais/pixel-art-atlas-1.4m
(https://huggingface.co/datasets/Angais/pixel-art-atlas-1.4m, public domain, CC0 1.0 — its sprites are AI-generated,
by Krea 2 Turbo with a pixel-art LoRA; the Krea 2 licence allows commercial use of its outputs under $1M yearly
revenue, see docs/STEAM.md) and reworked for the game:
recoloured into the Foundry's palettes (iron, brass, copper, fire, the arc's blue, the frames' own paints, the
Maniac's purple for his modules), turned to face right like our creatures, given our outline and a rim light along
the top edge. Only the reworked icons are kept in the repository (assets/module_icons.png); the dataset is not.

    python3 tools/sprites/icons.py <dir with the dataset's tokens.npy, palette.npy>
        -> assets/module_icons.png, .json and assets/swarm_icons.png, .json (the swarm's traits, chimeras, leaders, brood)
    icons.icon("long", 5)  -> a Sprite of the «Длинный ствол» icon, 5× (nearest), centred on (ox, oy)
    icons.icon("acid", 5, "swarm")  -> the swarm's «Кислотная железа»
"""
import json
import os
import colorsys
import numpy as np
from kit import *

HERE = os.path.dirname(os.path.abspath(__file__))
ASSET = os.path.join(HERE, "assets", "module_icons.png")
INDEX = os.path.join(HERE, "assets", "module_icons.json")
SW_ASSET = os.path.join(HERE, "assets", "swarm_icons.png")
SW_INDEX = os.path.join(HERE, "assets", "swarm_icons.json")

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
    # the swarm
    "chitin": ramp("#07050a", "#180e1c", "#30182c", "#523048", "#9a84a2"),
    "rust": ramp("#080404", "#1e0a08", "#3a1410", "#5e2618", "#a8603e"),
    "olive": ramp("#060804", "#151b0c", "#283216", "#424e22", "#808e4a"),
    "mantis": ramp("#0a0c08", "#20281c", "#3a4630", "#5e6c52", "#a4b294"),
    "amber": ramp("#140a04", "#3a2008", "#74420c", "#b4741a", "#e2b048"),
    "elytra": ramp("#0a0408", "#24080e", "#4a1016", "#7e2220", "#c0603a"),
    "slate": ramp("#14141c", "#2a2a36", "#4a4a5a", "#74748a", "#a8a8bc"),
    "acid": ramp("#0a1a04", "#1e3c0a", "#3e7a16", "#7ac83a", "#c8ff8a"),
    "lantern": ramp("#4a4410", "#8a7a18", "#d0b830", "#f4e870", "#fffcd0"),
    "crimson": ramp("#14040a", "#3a0a14", "#6a1420", "#a02a2e", "#d65a4a"),
    "membrane": ramp("#12060e", "#2a0e1c", "#461828", "#6a2838", "#9a4a56"),
    "brain": ramp("#1c0c16", "#3c1a2c", "#66304a", "#98566e", "#cc8c98"),
    "phero": ramp("#1e0e36", "#462078", "#7640c0", "#ac80ec", "#e6d2ff"),
    "egg": ramp("#2a3a20", "#4a6a2e", "#76a040", "#a8d060", "#e0f6a0"),
    "grub": ramp("#241a12", "#54442e", "#8a7656", "#bea98a", "#ece0c4"),
    "skin": ramp("#2a140c", "#5a3020", "#9a5a3c", "#d09070", "#f2c8a8"),
    "fur": ramp("#141010", "#2e2620", "#4e4236", "#766652", "#a8987e"),
    "bone": ramp("#120c0a", "#2e241c", "#6a5a46", "#b4a688", "#ece2c8"),
    "slime": ramp("#06201c", "#0e4a3e", "#1a8270", "#4ac0a8", "#b0f4e4"),
    "worm": ramp("#200810", "#4a1424", "#80283c", "#c05062", "#f0a0a8"),
    "locust": ramp("#0a0802", "#262006", "#56460e", "#9a821e", "#e2ca50"),
    "petal": ramp("#2a1420", "#6a3450", "#b06a8a", "#e0a8c0", "#fbe4ee"),
    "lure": ramp("#401006", "#8a2a0a", "#d0601a", "#f4a040", "#ffe0a0"),
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


# the swarm's icons: its traits (the form each gives as the first trait), the chimeras' foreign traits, its leaders and
# the brood screen's actions; recoloured into the swarm's oily chitin, acid, ichor and pheromone colours
CH = dict(grey="chitin", brown="chitin", red="chitin", warm="amber", green="chitin", blue="chitin", purple="chitin")
SWARM_ICONS = {
    "ant": (834220, "Муравей · без черт", "черта", dict(CH)),
    "wings": (1211376, "Крылья · оса", "черта", dict(CH, warm="amber", grey="slate", blue="slate")),
    "stinger": (685804, "Жало · скорпион", "черта", dict(grey="rust", brown="rust", red="crimson", warm="bone")),
    "acid": (1289263, "Кислотная железа · бочонок", "черта", dict(green="acid", grey="chitin", blue="acid")),
    "horn": (1059264, "Рог · жук", "черта", dict(grey="elytra", brown="elytra", red="elytra", warm="bone", blue="elytra")),
    "carapace": (1367859, "Панцирь · мокрица", "черта", dict(grey="slate", brown="slate", warm="slate", red="slate")),
    "jumper": (841013, "Прыгучие ноги · кузнечик", "черта", dict(green="olive", grey="olive", brown="olive", warm="olive")),
    "scythes": (845234, "Серпы · богомол", "черта", dict(green="mantis", grey="bone", brown="mantis", warm="bone")),
    "firefly": (1140464, "Светлячок · светляк", "черта", dict(green="lantern", grey="chitin", warm="lantern", brown="amber")),
    "spitter": (476648, "Клейкие железы · паук-плевун", "черта", dict(brown="bone", warm="amber", red="crimson", grey="chitin")),
    "iron": (644922, "Железный панцирь", "химера", dict(warm="iron", brown="iron", red="iron", grey="grub", green="grub")),
    "boil": (731424, "Кипящая кровь", "химера", dict(red="fire", warm="fire", grey="steel", brown="ember")),
    "hand": (622418, "Человеческая рука", "химера", dict(warm="skin", brown="skin", red="skin", grey="skin")),
    "face": (816676, "Человеческое лицо", "химера", dict(warm="skin", brown="skin", red="crimson", grey="chitin", green="skin")),
    "bones": (1282939, "Чужие кости", "химера", dict(grey="bone", warm="bone", brown="bone")),
    "quills": (1351734, "Иглы", "химера", dict(brown="bone", grey="bone", warm="bone", red="chitin")),
    "snout": (724249, "Волчий нюх", "химера", dict(grey="fur", brown="fur", warm="fur", red="crimson")),
    "slime": (1218735, "Слизистая кожа", "химера", dict(green="slime", grey="slime", blue="slime", warm="slime")),
    "worm": (1396528, "Червь внутри", "химера", dict(red="worm", warm="worm", brown="worm", grey="worm", purple="worm")),
    "matka": (708853, "Матка", "лидер", dict(warm="amber", brown="amber", red="crimson", blue="egg", grey="bone")),
    "razum": (597655, "Разум улья", "лидер", dict(red="brain", warm="phero", grey="brain", purple="phero", blue="phero")),
    "pozh": (1366933, "Пожиратель", "лидер", dict(red="crimson", grey="bone", warm="bone", brown="crimson")),
    "kuk": (357997, "Чума", "лидер", dict(green="amber", blue="amber", grey="chitin", purple="chitin", warm="amber")),
    "feed": (936138, "Кормление лидера", "выводок", dict(red="crimson", brown="crimson", warm="bone", grey="bone")),
    "evolve": (189565, "Эволюция формы", "выводок", dict(green="acid", brown="chitin", warm="amber", grey="chitin")),
    "clutch": (1268191, "Вторая кладка", "выводок", dict(brown="chitin", warm="amber", grey="egg", green="egg")),
    "reroll": (1576, "Переброс кладок", "выводок", dict(grey="bone", red="crimson", warm="amber")),
    "biomass": (1310924, "Биомасса", "выводок", dict(red="crimson", brown="crimson", warm="membrane", grey="bone")),
    "larva": (617184, "Личинка", "выводок", dict(brown="grub", warm="grub", red="grub", grey="grub")),
    "selection": (1364435, "Естественный отбор", "выводок", dict(grey="bone", brown="chitin", warm="bone")),
    "fear": (929257, "Страх", "бой", dict(warm="bone", blue="phero", red="crimson", grey="chitin")),
    # evolutions of the forms
    "evo_formic": (1399573, "Муравьиная кислота", "эволюция", dict(blue="acid", grey="chitin", warm="acid")),
    "evo_phalanx": (1146545, "Сомкнутый строй", "эволюция", dict(grey="slate", warm="bone", red="crimson")),
    "evo_bridge": (931195, "Живой мост", "эволюция", dict(grey="bone", brown="chitin", warm="bone")),
    "evo_syringe": (719074, "Жало-шприц", "эволюция", dict(red="crimson", grey="bone", blue="bone", warm="amber")),
    "evo_tough": (1235642, "Жёсткие крылья", "эволюция", dict(grey="amber", warm="amber", brown="chitin")),
    "evo_dive": (1034603, "Пикирование", "эволюция", dict(brown="chitin", grey="bone", warm="amber")),
    "evo_vise": (797141, "Клешни-тиски", "эволюция", dict(red="bone", warm="bone", brown="rust", grey="rust")),
    "evo_neuro": (867496, "Нейротоксин", "эволюция", dict(red="phero", purple="phero", grey="steel", blue="phero", brown="chitin")),
    "evo_longlegs": (1155620, "Длинные лапы", "эволюция", dict(red="rust", warm="rust", brown="rust", grey="bone")),
    "evo_farspit": (785063, "Дальний плевок", "эволюция", dict(grey="chitin", blue="acid", warm="acid", red="acid")),
    "evo_scent": (426832, "Свой запах", "эволюция", dict(warm="amber", grey="chitin", red="crimson")),
    "evo_pool": (737509, "Едкая лужа", "эволюция", dict(green="acid", grey="acid", blue="acid")),
    "evo_forked": (1251315, "Двойной рог", "эволюция", dict(brown="bone", grey="bone", warm="bone")),
    "evo_bosses": (1082063, "Бугристые надкрылья", "эволюция", dict(grey="elytra", brown="elytra", warm="bone", red="elytra")),
    "evo_flyer": (634178, "Летучий жук", "эволюция", dict(blue="amber", grey="elytra", green="amber", purple="elytra")),
    "evo_longspines": (1004377, "Длинные шипы", "эволюция", dict(grey="bone", blue="bone", warm="bone")),
    "evo_lime": (533399, "Известковый панцирь", "эволюция", dict(grey="stone", brown="stone", purple="stone")),
    "evo_flanges": (127633, "Щитовые края", "эволюция", dict(grey="slate", warm="bone", red="slate", blue="slate")),
    "evo_locust": (631602, "Стадная фаза", "эволюция", dict(green="locust", grey="locust", brown="locust", warm="locust")),
    "evo_shins": (1067322, "Шипастые голени", "эволюция", dict(grey="olive", brown="olive", warm="bone")),
    "evo_farjump": (893935, "Дальний прыжок", "эволюция", dict(grey="bone", warm="bone", brown="olive", red="olive")),
    "evo_saws": (1275309, "Серпы-пилы", "эволюция", dict(grey="bone", brown="mantis", warm="bone")),
    "evo_orchid": (248731, "Цветочная мимикрия", "эволюция", dict(red="petal", warm="petal", purple="petal", green="mantis", brown="mantis")),
    "evo_eyespots": (816490, "Глазчатые крылья", "эволюция", dict(green="mantis", blue="phero", warm="amber", brown="chitin", grey="chitin")),
    "evo_bright": (392718, "Яркий фонарь", "эволюция", dict(warm="lantern", red="lantern", grey="chitin", brown="amber")),
    "evo_hood": (1076579, "Капюшон", "эволюция", dict(brown="chitin", warm="lantern", grey="chitin", red="chitin")),
    "evo_lure": (434562, "Ложный сигнал", "эволюция", dict(warm="lure", red="lure", grey="chitin", blue="lantern")),
    "evo_net": (1366120, "Ловчая сеть", "эволюция", dict(grey="bone", brown="chitin", warm="bone", red="amber")),
    "evo_recoil": (299380, "Отскок на нити", "эволюция", dict(grey="bone", brown="amber", red="amber", blue="bone", warm="bone")),
    "evo_pull": (1281104, "Стащить со стены", "эволюция", dict(red="amber", warm="amber", grey="bone", brown="chitin")),
    # mutations: the common pool and each leader's pool (keys as in swarm_mut, with "m_")
    "m_spinner": (420375, "Прядильные железы", "общий пул", dict(grey="bone", blue="bone", purple="bone")),
    "m_exploder": (1320474, "Взрывной муравей", "общий пул", dict(red="amber", warm="lantern", grey="chitin", brown="chitin")),
    "m_bolas": (1089911, "Болас", "общий пул", dict(grey="bone", brown="amber", warm="lantern", red="amber", blue="bone")),
    "m_beeball": (687208, "Пчелиный шар", "общий пул", dict(warm="amber", brown="chitin", grey="bone", blue="bone")),
    "m_pupa": (581358, "Куколка", "общий пул", dict(grey="bone", warm="bone", brown="bone", green="bone")),
    "m_midge": (1063365, "Мошкара", "общий пул", dict(grey="slate", brown="chitin", red="crimson", blue="slate")),
    "m_honey": (1027171, "Медовые соты", "общий пул", dict(warm="amber", brown="chitin", red="amber", grey="bone")),
    "m_blister": (731424, "Нарывник", "общий пул", dict(red="crimson", warm="fire", grey="chitin")),
    "m_cutters": (742632, "Кусачки", "общий пул", dict(grey="steel", red="crimson", warm="bone", brown="chitin", blue="steel")),
    "m_guard": (1336617, "Стража лидера", "общий пул", dict(grey="elytra", brown="elytra", warm="bone", blue="slate", purple="slate")),
    "m_regen": (608641, "Живучая", "общий пул", dict(red="skin", warm="skin", brown="skin", grey="bone", green="acid")),
    "m_nest": (426120, "Малое гнездо", "Матка", dict(brown="chitin", warm="amber", grey="egg", blue="egg", green="egg")),
    "m_nurse": (1114675, "Кормилица", "Матка", dict(red="grub", warm="grub", brown="grub", grey="grub", purple="grub")),
    "m_vivi": (569154, "Живородящая", "Матка", dict(grey="grub", warm="grub", red="crimson", brown="grub")),
    "m_bud": (59838, "Почкование", "Матка", dict(green="egg", grey="bone", brown="chitin", warm="bone", blue="egg")),
    "m_dominant": (1321919, "Доминантная линия", "Матка", dict(warm="amber", brown="amber", red="crimson", blue="phero", grey="bone")),
    "m_flight": (823556, "Брачный полёт", "Матка", dict(green="bone", warm="amber", red="amber", brown="chitin", grey="bone")),
    "m_hybrid": (697886, "Гибрид", "Матка", dict(red="crimson", blue="acid", purple="acid", warm="amber", grey="bone")),
    "m_heir": (934737, "Наследница", "Матка", dict(warm="amber", brown="amber", red="crimson", blue="egg", purple="membrane", grey="bone")),
    "m_psi_gland": (1386217, "Пси-железа", "Разум улья", dict(grey="phero", warm="phero", brown="chitin", red="phero")),
    "m_psi_reson": (577641, "Резонатор", "Разум улья", dict(blue="phero", purple="phero", grey="chitin", warm="phero")),
    "m_psi_dread": (731518, "Чутьё на страх", "Разум улья", dict(red="crimson", grey="bone", purple="phero", brown="chitin", warm="crimson")),
    "m_psi_whisper": (90008, "Жуткий шёпот", "Разум улья", dict(purple="phero", grey="bone", red="phero", brown="chitin", warm="bone")),
    "m_strider": (658377, "Стрекот", "Разум улья", dict(warm="amber", brown="chitin", red="amber", grey="bone")),
    "m_psi_echo": (938397, "Эхо крика", "Разум улья", dict(warm="phero", brown="brain", red="brain", grey="phero")),
    "m_psi_last": (1389787, "Последняя воля", "Разум улья", dict(grey="bone", red="phero", purple="phero", blue="phero", brown="chitin")),
    "m_psi_leash": (804313, "Пси-поводок", "Разум улья", dict(brown="phero", warm="phero", grey="phero", red="phero")),
    "m_psi_relay": (824543, "Ретранслятор", "Разум улья", dict(warm="phero", blue="phero", grey="chitin", red="brain", brown="chitin")),
    "m_sated": (109728, "Сытная", "Пожиратель", dict(red="membrane", brown="membrane", warm="skin", grey="bone")),
    "m_bait": (869845, "Приманка", "Пожиратель", dict(red="crimson", grey="chitin", blue="chitin", warm="crimson")),
    "m_fattened": (380143, "Откормленная", "Пожиратель", dict(red="skin", purple="skin", warm="skin", grey="bone", brown="chitin")),
    "m_frenzy": (896038, "Кормовое безумие", "Пожиратель", dict(grey="crimson", warm="crimson", brown="chitin", red="crimson")),
    "m_table": (1274202, "За столом", "Пожиратель", dict(red="membrane", brown="membrane", warm="skin", grey="bone")),
    "m_hungry": (1238985, "Голодная", "Пожиратель", dict(grey="bone", warm="bone", brown="bone")),
    "m_devblood": (890211, "Кровь Пожирателя", "Пожиратель", dict(red="crimson", brown="crimson", grey="chitin", warm="crimson")),
    "m_essence": (717747, "Питательная суть", "Пожиратель", dict(warm="lantern", grey="lantern", brown="amber", blue="lantern")),
    "m_parasitoid": (862234, "Паразитоид", "Чума", dict(blue="egg", grey="bone", red="crimson", brown="chitin", warm="amber")),
    "m_bloodeggs": (763338, "Яйца в крови", "Чума", dict(green="egg", grey="egg", red="crimson", purple="crimson", brown="chitin")),
    "m_spores": (1036721, "Споры", "Чума", dict(warm="amber", brown="amber", grey="bone", red="amber")),
    "m_call": (1200904, "Зов кладки", "Чума", dict(green="acid", grey="bone", brown="chitin", warm="acid")),
    "m_bodyguard": (874853, "Телохранитель", "Чума", dict(warm="amber", brown="chitin", grey="bone", blue="bone")),
    "m_gnaw": (1348304, "Прожорливая кладка", "Чума", dict(brown="grub", red="grub", warm="grub", grey="grub")),
    "m_mutagen": (1336294, "Мутагенная кладка", "Чума", dict(green="acid", brown="chitin", grey="phero", warm="amber", red="crimson")),
    "m_unstable": (467654, "Нестабильная", "Чума", dict(red="crimson", warm="amber", blue="phero", purple="phero", grey="bone")),
    "m_royal": (160836, "Королевская кладка", "Чума", dict(warm="amber", brown="amber", red="crimson", grey="egg", green="egg")),
}
SETS = {"module": (ICONS, ASSET, INDEX), "swarm": (SWARM_ICONS, SW_ASSET, SW_INDEX)}

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


def build_atlas(src, which="module"):
    from PIL import Image
    table, asset, index_path = SETS[which]
    tokens = np.load(os.path.join(src, "tokens.npy"), mmap_mode="r", allow_pickle=False)
    palette = np.load(os.path.join(src, "palette.npy"), allow_pickle=False)
    keys = list(table)
    cols = 10
    rows = (len(keys) + cols - 1) // cols
    atlas = np.zeros((rows * 16, cols * 16, 4), np.uint8)
    index = {}
    for n, key in enumerate(keys):
        row, name, owner, spec = table[key]
        p = np.asarray(tokens[row]).reshape(16, 16)
        rgba = np.dstack((palette[p], (p != 0).astype("uint8") * 255)).astype(np.uint8)
        y, x = (n // cols) * 16, (n % cols) * 16
        atlas[y:y + 16, x:x + 16] = rework(rgba, spec, owner)
        index[key] = dict(cell=[n % cols, n // cols], name=name, owner=owner, source_row=row)
    os.makedirs(os.path.dirname(asset), exist_ok=True)
    Image.fromarray(atlas, "RGBA").save(asset)
    json.dump(dict(source="Angais/pixel-art-atlas-1.4m (CC0 1.0), reworked", icons=index), open(index_path, "w"),
              ensure_ascii=False, indent=1)
    return atlas


_cache = {}


def icon_rgba(key, which="module"):
    from PIL import Image
    if which not in _cache:
        _, asset, index_path = SETS[which]
        _cache[which] = (np.array(Image.open(asset).convert("RGBA")), json.load(open(index_path))["icons"])
    atlas, index = _cache[which]
    cx, cy = index[key]["cell"]
    return atlas[cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16]


def icon(key, z=5, which="module"):
    """The icon as a Sprite, z× nearest, its centre at (ox, oy)."""
    rgba = np.repeat(np.repeat(icon_rgba(key, which), z, 0), z, 1)
    s = Sprite(16 * z, 16 * z)
    s.rgb = rgba[..., :3].astype(np.float32)
    s.a = rgba[..., 3] > 0
    s.ox, s.oy = 8 * z, 8 * z
    return s


def sheet(path, z=4, which="module"):
    """All the icons with their names, for a look."""
    from PIL import Image, ImageDraw, ImageFont
    from paths import font
    table = SETS[which][0]
    keys = list(table)
    cols = 8
    cw, ch = 16 * z + 150, 16 * z + 16
    rows = (len(keys) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw + 20, rows * ch + 20), (40, 34, 46))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(font("PTSerif-Regular.ttf"), 14)
    for n, key in enumerate(keys):
        x, y = 10 + (n % cols) * cw, 10 + (n // cols) * ch
        im = Image.fromarray(np.repeat(np.repeat(icon_rgba(key, which), z, 0), z, 1), "RGBA")
        img.paste(im, (x, y), im)
        d.text((x + 16 * z + 6, y + 16 * z / 2 - 8), table[key][1], font=f, fill=(230, 220, 196))
    img.save(path)


if __name__ == "__main__":
    import sys
    from paths import out
    if len(sys.argv) > 1:
        build_atlas(sys.argv[1], "module")
        build_atlas(sys.argv[1], "swarm")
    sheet(out("module_icons_sheet.png"))
    sheet(out("swarm_icons_sheet.png"), which="swarm")
    print(ASSET, SW_ASSET)
