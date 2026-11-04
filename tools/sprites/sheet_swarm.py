"""Swarm design sheet: body forms, a crowd at game scale, inheritance, castes and bred lines."""
import random
from PIL import ImageFont
from kit import *
import swarm1 as W
from noise import value_noise
from paths import font, out

S = 2
WW = 960
HEAD = 34
rows_h = [120, 150, 110, 110, 140]
HH = 40 + sum(h + HEAD for h in rows_h)
sc = Scene(WW, HH)
n = value_noise(WW, HH, 12, 7) * 0.6 + value_noise(WW, HH, 4, 8) * 0.4
th = BAYER[sc.yy % 4, sc.xx % 4]
lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
    sc.rgb[lv == i] = hexc(c)
labels, titles, arrows, crosses = [], [], [], []


def put(spr, cx, by, sw):
    e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(2.5, sw * 0.2)) ** 2
    sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


y = 40
# 1. forms
titles.append((y, "Главная черта задаёт форму тела"))
by = y + HEAD + rows_h[0] - 26
forms = [()] + [(t,) for t in W.TRAITS]
cw = WW / len(forms)
for i, t in enumerate(forms):
    cx = int(cw / 2 + i * cw)
    put(W.build(t, 0.0, "idle", False, k=1.8), cx, by, 16)
    labels.append((cx, by + 6, "Муравей" if not t else W.PLANS[t[0]], "без черт" if not t else W.NAMES[t[0]].lower()))
y += HEAD + rows_h[0]

# 2. crowd at the real in-game size
titles.append((y, "Толпа в настоящем игровом размере — каждая особь своя"))
rnd = random.Random(12)
units = []
for _ in range(46):
    roll = rnd.random()
    primary = None if roll < 0.3 else rnd.choice(W.TRAITS)
    extra = [t for t in W.TRAITS if t != primary and rnd.random() < 0.12]
    traits = ((primary,) if primary else ()) + tuple(extra[:2])
    soldier = primary is None and rnd.random() < 0.3
    if rnd.random() < 0.1:
        traits += ("giant",)
    hue = rnd.uniform(-0.16, 0.16)
    genes = W.genes_for(rnd.randrange(10 ** 6))
    x = rnd.uniform(30, WW - 30)
    yy = rnd.uniform(y + HEAD + 40, y + HEAD + rows_h[1] - 8)
    units.append((yy, x, traits, hue, soldier, genes))
for (yy, x, traits, hue, soldier, genes) in sorted(units):
    spr = W.build(traits, hue, "idle" if rnd.random() < 0.7 else "attack", soldier, k=1.0, genes=genes)
    sp2 = spr.flipped()
    sp2.ox, sp2.oy = spr.w - 1 - spr.ox, spr.oy
    put(sp2, x, yy, 8)
y += HEAD + rows_h[1]

# 3. inheritance with different body forms
titles.append((y, "Наследование: форма тела от одного родителя, детали от другого, окрас смешан"))
by = y + HEAD + rows_h[2] - 30
A, B = (("wings", "acid"), -0.10), (("horn", "carapace"), 0.12)
put(W.build(A[0], A[1], "idle", k=1.8), 80, by, 16)
labels.append((80, by + 6, "Оса", "крылья, кислота"))
crosses.append((165, by - 16))
put(W.build(B[0], B[1], "idle", k=1.8), 250, by, 16)
labels.append((250, by + 6, "Жук", "рог, панцирь"))
arrows.append((320, by - 16, 380, by - 16))
kids = [(("horn", "wings"), "Жук", "рог, крылья"),
        (("wings", "carapace"), "Оса", "крылья, панцирь"),
        (("carapace", "acid", "scythes"), "Мокрица", "панцирь, кислота + серпы"),
        (("acid", "horn", "giant"), "Бочонок", "кислота, рог + гигантизм")]
for i, (t, nm, txt) in enumerate(kids):
    cx = 450 + i * 140
    put(W.build(t, (A[1] + B[1]) / 2 + (-0.03, 0.02, 0.04, -0.01)[i], "idle", k=1.8), cx, by, 18)
    labels.append((cx, by + 6, nm, txt))
y += HEAD + rows_h[2]

# 4. castes at true relative scale
titles.append((y, "Касты — в настоящем соотношении размеров"))
by = y + HEAD + rows_h[3] - 30
put(W.build((), 0.0, "idle", False, k=1.5), 120, by, 14)
labels.append((120, by + 6, "Рабочая", "размер 1"))
put(W.build((), 0.0, "idle", True, k=1.5), 270, by, 20)
labels.append((270, by + 6, "Солдат", "размер 2"))
put(W.queen(0.0, "idle", k=0.6), 600, by, 90)
labels.append((560, by + 6, "Матка", "размер 6"))
y += HEAD + rows_h[3]

# 5. bred lines
titles.append((y, "Породы к концу похода — то, что вывел игрок"))
by = y + HEAD + rows_h[4] - 30
bred = [(("wings", "acid", "stinger", "giant"), -0.06, "Кислотный шершень"),
        (("horn", "wings", "carapace", "giant"), 0.10, "Летучий таран"),
        (("scythes", "firefly", "carapace"), 0.02, "Светящийся богомол"),
        (("stinger", "jumper", "giant"), -0.14, "Прыгучий скорпион")]
for i, (t, hue, name) in enumerate(bred):
    cx = 120 + i * 240
    put(W.build(t, hue, "idle", k=1.8), cx, by, 26)
    labels.append((cx, by + 6, name, f"размер {W.size_of(t)}"))

img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 21)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 17)
fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 15)
d.text((24, 16), "Рой: формы тела, черты, наследование", font=ft, fill=(236, 226, 200))
for (ty, t) in titles:
    d.text((24, ty * S + 10), t, font=fh, fill=(226, 186, 106))
for (cx, ly, a, b) in labels:
    d.text((cx * S - d.textlength(a, font=fb) / 2, ly * S), a, font=fb, fill=(236, 226, 200))
    if b:
        d.text((cx * S - d.textlength(b, font=fr) / 2, ly * S + 22), b, font=fr, fill=(186, 178, 160))
for (x0, y0, x1, y1) in arrows:
    d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=(226, 186, 106), width=4)
    d.polygon([(x1 * S + 14, y1 * S), (x1 * S - 4, y1 * S - 10), (x1 * S - 4, y1 * S + 10)], fill=(226, 186, 106))
for (cx, cy) in crosses:
    d.text((cx * S - d.textlength("×", font=ft) / 2, cy * S - 22), "×", font=ft, fill=(226, 186, 106))
img.save(out("swarm_design.png"))
print(img.size)
