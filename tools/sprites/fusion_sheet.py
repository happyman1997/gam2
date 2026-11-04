"""Fusion: four size-1 swarm creatures in one cell grow into a single size-3 creature mid-battle."""
from PIL import ImageFont
from kit import *
import swarm1 as W
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 300
sc = Scene(WW, HH)
n = value_noise(WW, HH, 12, 5) * 0.6 + value_noise(WW, HH, 4, 6) * 0.4
th = BAYER[sc.yy % 4, sc.xx % 4]
lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
    sc.rgb[lv == i] = hexc(c)

members = [(("horn",), 0.10), (("acid",), -0.06), (("scythes",), 0.02), (("stinger",), -0.15)]


def put(spr, cx, by, sw):
    e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(2.5, sw * 0.2)) ** 2
    sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


# the cell with four of them
x0, y0, x1, y1 = 40, 120, 300, 250
edge = np.zeros((HH, WW), bool)
edge[y0:y1, x0] = edge[y0:y1, x1 - 1] = True
edge[y0, x0:x1] = edge[y1 - 1, x0:x1] = True
edge &= ((sc.xx + sc.yy) % 3 != 0)
sc.rgb[edge] = sc.rgb[edge] * 0.5 + hexc("#c9b27a") * 0.5
spots = [(100, 170), (220, 165), (110, 232), (230, 228)]
for (t, hue), (cx, by) in sorted(zip(members, spots), key=lambda u: u[1][1]):
    put(W.build(t, hue, "idle", k=1.7), cx, by, 16)
# the fused creature, idle and attacking
put(W.fusion(members, "idle", k=1.7), 570, 240, 62)
put(W.fusion(members, "attack", k=1.7), 830, 240, 62)

img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 19)
fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 16)
G = (226, 186, 106)
d.text((24, 16), "Сросток: четверо в одной клетке срастаются посреди боя", font=ft, fill=(236, 226, 200))
d.text((24, 62), "Срастание случается, когда в клетке четыре особи размера 1 и рядом враг крупнее их. Части тела берутся от каждой.",
       font=fr, fill=(196, 188, 170))
d.text((x0 * S, (y1 + 10) * S), "4 особи размера 1: рог, кислота, серпы, жало", font=fb, fill=(236, 226, 200))
d.line([(320 * S, 190 * S), (400 * S, 190 * S)], fill=G, width=4)
d.polygon([(414 * S, 190 * S), (396 * S, 180 * S), (396 * S, 200 * S)], fill=G)
for cx, a, b in ((570, "Сросток", "размер 3 · все их черты"), (830, "Сросток в атаке", "хвост бьёт, кислота летит")):
    d.text((cx * S - d.textlength(a, font=fb) / 2, (y1 + 10) * S), a, font=fb, fill=(236, 226, 200))
    d.text((cx * S - d.textlength(b, font=fr) / 2, (y1 + 10) * S + 26), b, font=fr, fill=(186, 178, 160))
img.save(out("swarm_fusion.png"))
print(img.size)
