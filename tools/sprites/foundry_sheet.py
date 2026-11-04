"""Foundry sheet: the three leaders (idle and attack) and what a broken golem looks like."""
from PIL import ImageFont
from kit import *
import golem7 as G
import leaders as LD
from golem7 import cfg
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 580
sc = Scene(WW, HH)
n = value_noise(WW, HH, 12, 9) * 0.6 + value_noise(WW, HH, 4, 10) * 0.4
th = BAYER[sc.yy % 4, sc.xx % 4]
lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
    sc.rgb[lv == i] = hexc(c)


def put(spr, cx, by, sw):
    e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(3, sw * 0.18)) ** 2
    sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


labels = []
keys = list(LD.LEADERS)
for i, key in enumerate(keys):
    cx = 110 + i * 320
    put(LD.build(key, "idle", k=1.5), cx, 236, 40)
    put(LD.build(key, "attack", k=1.5), cx + 140, 236, 40)
    labels.append((cx + 70, 248, LD.LEADERS[key][1]))
golems = [(cfg(arms=("heavy", "piston"), tools=("hammer", "shield")), "Молотобоец"),
          (cfg(legs="springs", head="sensor", core="volt", arms=("piston", "piston"), tools=("cannon", "claw")), "Пушкарь")]
for i, (c, name) in enumerate(golems):
    cx = 140 + i * 420
    put(G.build(c, 2, "idle", k=1.7), cx, 500, 46)
    put(G.build(c, 2, "broken", k=1.7), cx + 190, 500, 46)
img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 19)
fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 16)
GOLD, INK, MUT = (226, 186, 106), (236, 226, 200), (190, 182, 164)
d.text((24, 16), "Литейщик: лидеры и поломка", font=ft, fill=INK)
d.text((24, 66), "Лидеры — на поле боя, размер 4. Слева покой, справа атака.", font=fh, fill=GOLD)
notes = ["чинит соседних големов в бою", "4 предложения в мастерской вместо 3", "големы рядом греются быстрее"]
for (cx, ly, name), note in zip(labels, notes):
    d.text((cx * S - d.textlength(name, font=fb) / 2, ly * S), name, font=fb, fill=INK)
    d.text((cx * S - d.textlength(note, font=fr) / 2, ly * S + 26), note, font=fr, fill=MUT)
d.text((24, 300 * S), "Поломка вместо смерти: ядро гаснет, голем оседает, оторванная деталь лежит рядом.", font=fh, fill=GOLD)
for i, (_, name) in enumerate(golems):
    cx = 140 + i * 420
    for dx, t in ((0, name), (190, name + " — сломан")):
        d.text(((cx + dx) * S - d.textlength(t, font=fb) / 2, 534 * S), t, font=fb, fill=INK)
img.save(out("foundry_leaders.png"))
print(img.size)
