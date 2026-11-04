from PIL import ImageFont
from kit import *
import golem7 as G
from golem7 import cfg
from noise import value_noise
from paths import font, out

S = 2
k = 1.9
cw, ch, top = 205, 232, 44
rows = [
    ("Руки — каждая меняется отдельно", "в дальней руке молот, в ближней клешня", [
        ("поршневые", cfg(arms=("piston", "piston"), tools=("hammer", "claw"))),
        ("тяжёлые", cfg(arms=("heavy", "heavy"), tools=("hammer", "claw"))),
        ("длинные", cfg(arms=("long", "long"), tools=("hammer", "claw"))),
        ("тяжёлая + длинная", cfg(arms=("heavy", "long"), tools=("hammer", "claw")))]),
    ("Ноги", None, [
        ("гусеницы", cfg(legs="tracks")),
        ("пружины", cfg(legs="springs")),
        ("тумбы", cfg(legs="pillars")),
        ("паучьи", cfg(legs="spider"))]),
    ("Что в руках", "любой инструмент в любой руке", [
        ("молот и щит", cfg(arms=("heavy", "heavy"), tools=("hammer", "shield"))),
        ("пушка и клешня", cfg(arms=("heavy", "heavy"), tools=("cannon", "claw"))),
        ("две пушки", cfg(arms=("piston", "piston"), tools=("cannon", "cannon"))),
        ("два молота", cfg(arms=("piston", "piston"), tools=("hammer", "hammer")))]),
    ("Всё вместе, уровень III", None, [
        ("Таран", cfg(legs="pillars", head="visor", core="fire", arms=("heavy", "heavy"), tools=("hammer", "shield"))),
        ("Паук-стрелок", cfg(legs="spider", head="sensor", core="volt", arms=("long", "long"), tools=("cannon", "claw"))),
        ("Батарея", cfg(legs="tracks", head="sensor", core="fire", arms=("piston", "piston"), tools=("cannon", "cannon"))),
        ("Прыгун", cfg(legs="springs", head="visor", core="volt", arms=("long", "heavy"), tools=("hammer", "claw")))]),
]
WW, HH = cw * 4, top + ch * len(rows)
sc = Scene(WW, HH)
n = value_noise(WW, HH, 12, 7) * 0.6 + value_noise(WW, HH, 4, 8) * 0.4
th = BAYER[sc.yy % 4, sc.xx % 4]
lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
    sc.rgb[lv == i] = hexc(c)
for r, (title, sub, items) in enumerate(rows):
    y0 = top + r * ch
    level = 3 if r == 3 else 2
    for i, (lbl, c) in enumerate(items):
        cx, by = cw // 2 + i * cw - 6, y0 + 178
        e = ((sc.xx - cx) / 40) ** 2 + ((sc.yy - by) / 8) ** 2
        sc.rgb[e <= 1] *= 0.62
        spr = G.build(c, level, k=k)
        sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
fs = ImageFont.truetype(font("PTSerif-Regular.ttf"), 17)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 19)
d.text((24, 18), "Модульный голем: руки, инструменты и ноги меняются", font=ft, fill=(236, 226, 200))
for r, (title, sub, items) in enumerate(rows):
    y = (top + r * ch) * S
    d.text((24, y + 8), title, font=fh, fill=(226, 186, 106))
    if sub:
        d.text((24 + d.textlength(title, font=fh) + 16, y + 13), sub, font=fs, fill=(186, 178, 160))
    for i, (lbl, _) in enumerate(items):
        cx = (cw // 2 + i * cw - 6) * S
        d.text((cx - d.textlength(lbl, font=fb) / 2, (top + r * ch + 192) * S), lbl, font=fb, fill=(236, 226, 200))
img.save(out("golem_limbs.png"))
print(img.size)
