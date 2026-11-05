"""Foundry sheet: leaders with their ability sets, the clockwork beetle, leaders for later, a broken golem."""
from PIL import ImageFont
from kit import *
import golem7 as G
import leaders as LD
from golem7 import cfg
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 760
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


ABIL = {
    "colossus": ("якорь", [("Вызов", "каждые 3 хода: соседние враги бьют только его"),
                           ("Плечом к плечу", "постоянно: большого голема рядом не окружить"),
                           ("Последний рывок", "раз за бой: поднимает сломанного большого голема"),
                           ("Литьё великанов", "поход: большие корпуса на треть дешевле")]),
    "clock": ("призыватель", [("Заводные жуки", "каждые 2 хода: самоходка бежит к врагу и взрывается"),
                              ("Сцепка", "постоянно: соседние малые големы бьют одну цель"),
                              ("Перевод часов", "на 3-м ходу: големы рядом делают лишний ход"),
                              ("Серийное производство", "поход: малые корпуса дешевле, +2 к пределу")]),
    "brazier": ("поджигатель", [("Огненный бросок", "каждый ход: клетка с врагами горит 2 хода"),
                                ("Тепло очага", "постоянно: големы рядом греются быстрее"),
                                ("Вспышка", "при перегреве голема рядом: взрыв пламени"),
                                ("Хранить огонь", "поход: огненные ядра в предложениях чаще")]),
}
xs = {"colossus": 120, "clock": 440, "brazier": 760}
for key in ABIL:
    cx = xs[key]
    put(LD.build(key, "idle", k=1.5), cx - 10, 230, 40)
    put(LD.build(key, "attack", k=1.5), cx + 120, 230, 40)
put(LD.build_beetle("idle", k=2.4), 110, 520, 14)
put(LD.build_beetle("attack", k=2.4), 190, 520, 14)
put(LD.build("forge", "idle", k=1.2), 360, 520, 34)
put(LD.build("spider", "idle", k=1.2), 500, 520, 34)
gc = cfg(arms=("heavy", "piston"), tools=("hammer", "shield"))
put(G.build(gc, 2, "idle", k=1.5), 690, 700, 40)
put(G.build(gc, 2, "broken", k=1.5), 860, 700, 40)

img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 19)
fbs = ImageFont.truetype(font("PTSerif-Bold.ttf"), 15)
fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 15)
GOLD, INK, MUT = (226, 186, 106), (236, 226, 200), (190, 182, 164)
d.text((24, 16), "Литейщик: лидеры и их способности", font=ft, fill=INK)
d.text((24, 62), "Лидер — юнит размера 4. Способности срабатывают сами по условию. Слева покой, справа атака.", font=fr, fill=MUT)
for key, (role, ab) in ABIL.items():
    cx = (xs[key] + 55) * S
    name = LD.LEADERS[key][1]
    d.text((cx - d.textlength(name, font=fb) / 2, 244 * S), name, font=fb, fill=INK)
    d.text((cx - d.textlength(role, font=fr) / 2, 244 * S + 26), role, font=fr, fill=GOLD)
    y = 244 * S + 56
    x0 = cx - 290
    for nm, txt in ab:
        d.text((x0, y), nm, font=fbs, fill=INK)
        d.text((x0, y + 19), txt, font=fr, fill=MUT)
        y += 44
d.text((24, 430 * S), "Заводной жук", font=fh, fill=GOLD)
d.text((24, 430 * S + 30), "размер 1, его выпускает Часовщик", font=fr, fill=MUT)
d.text((300 * S, 430 * S), "Позже, через метапрогрессию", font=fh, fill=GOLD)
for cx, nm, role in ((360, "Мастер кузни", "ремонтник"), (500, "Изобретатель", "строитель")):
    d.text((cx * S - d.textlength(nm, font=fb) / 2, 532 * S), nm, font=fb, fill=INK)
    d.text((cx * S - d.textlength(role, font=fr) / 2, 532 * S + 26), role, font=fr, fill=MUT)
d.text((24, 600 * S), "Поломка вместо смерти:", font=fh, fill=GOLD)
d.text((24, 600 * S + 32), "ядро гаснет, голем оседает,", font=fr, fill=MUT)
d.text((24, 600 * S + 54), "оторванная деталь лежит рядом", font=fr, fill=MUT)
for cx, t in ((690, "Молотобоец"), (860, "сломан")):
    d.text((cx * S - d.textlength(t, font=fb) / 2, 720 * S), t, font=fb, fill=INK)
img.save(out("foundry_leaders.png"))
print(img.size)
