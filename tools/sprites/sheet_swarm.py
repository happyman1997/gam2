"""Swarm design sheet: castes, traits (idle and attack), inheritance, a bred line at the end of a run."""
from PIL import ImageFont
from kit import *
import swarm1 as W
from noise import value_noise
from paths import font, out

S = 2
WW = 960
rows_h = [150, 118, 118, 150, 150]
head = 34
HH = 40 + sum(h + head for h in rows_h)
sc = Scene(WW, HH)
n = value_noise(WW, HH, 12, 7) * 0.6 + value_noise(WW, HH, 4, 8) * 0.4
th = BAYER[sc.yy % 4, sc.xx % 4]
lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
    sc.rgb[lv == i] = hexc(c)

labels, titles, arrows, crosses = [], [], [], []


def put(spr, cx, by, shadow_w):
    e = ((sc.xx - cx) / shadow_w) ** 2 + ((sc.yy - by) / max(3, shadow_w * 0.18)) ** 2
    sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


y = 40
# 1. castes at true relative scale
titles.append((y, "Касты — в настоящем соотношении размеров"))
by = y + head + rows_h[0] - 30
K0 = 1.5
put(W.build((), 0.0, "idle", False, k=K0), 120, by, 14)
labels.append((120, by + 8, "Рабочая", "размер 1"))
put(W.build((), 0.0, "idle", True, k=K0), 270, by, 20)
labels.append((270, by + 8, "Солдат", "размер 2"))
put(W.queen(0.0, "idle", k=K0 / 2.6 * 2.6 * 0.62), 600, by, 90)
labels.append((560, by + 8, "Матка", "размер 6"))
y += head + rows_h[0]

# 2-3. traits, idle and attack
K = 2.0
traits = ["wings", "stinger", "acid", "horn", "carapace", "jumper", "scythes", "firefly"]
cw = WW // len(traits)
for r, pose in enumerate(("idle", "attack")):
    titles.append((y, "Черты — каждая видна на теле" if pose == "idle" else "Атака — отдельный спрайт для каждой черты"))
    by = y + head + rows_h[1 + r] - 22
    for i, t in enumerate(traits):
        cx = cw // 2 + i * cw
        put(W.build((t,), 0.0, pose, False, k=K), cx, by, 16)
        if pose == "idle":
            labels.append((cx, by + 6, W.NAMES[t], None))
    y += head + rows_h[1 + r]

# 4. inheritance
titles.append((y, "Наследование: по черте от каждого родителя, окрас смешивается, иногда мутация"))
by = y + head + rows_h[3] - 30
A, B = (("wings", "acid"), -0.10), (("horn", "carapace"), 0.12)
put(W.build(A[0], A[1], "idle", False, k=K), 80, by, 16)
labels.append((80, by + 6, "Родитель", "крылья, кислота"))
put(W.build(B[0], B[1], "idle", False, k=K), 230, by, 16)
labels.append((230, by + 6, "Родитель", "рог, панцирь"))
kids = [(("wings", "horn"), "крылья, рог"),
        (("acid", "carapace", "scythes"), "кислота, панцирь + серпы"),
        (("wings", "carapace", "giant"), "крылья, панцирь + гигантизм")]
for i, (t, txt) in enumerate(kids):
    cx = 450 + i * 180
    hue = (A[1] + B[1]) / 2 + (-0.03, 0.02, 0.04)[i]
    put(W.build(t, hue, "idle", False, k=K), cx, by, 18 if "giant" not in t else 26)
    labels.append((cx, by + 6, "Потомок", txt))
arrows.append((300, by - 18, 372, by - 18))
crosses.append((155, by - 18))
y += head + rows_h[3]

# 5. a bred line at the end of a run
titles.append((y, "Порода к концу похода — то, что вывел игрок"))
by = y + head + rows_h[4] - 30
bred = [(("wings", "acid", "stinger", "giant"), -0.06, "Кислотный шершень"),
        (("horn", "carapace", "jumper", "giant"), 0.10, "Рогатый таран"),
        (("scythes", "carapace", "firefly"), 0.02, "Светящийся богомол"),
        (("wings", "scythes", "firefly", "giant"), -0.14, "Ночной жнец")]
for i, (t, hue, name) in enumerate(bred):
    cx = 120 + i * 240
    put(W.build(t, hue, "idle", False, k=K), cx, by, 26)
    sz = W.size_of(t)
    labels.append((cx, by + 6, name, f"размер {sz}"))

img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 21)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 17)
fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 15)
d.text((24, 16), "Рой: касты, черты, наследование", font=ft, fill=(236, 226, 200))
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
    t = "×"
    d.text((cx * S - d.textlength(t, font=ft) / 2, cy * S - 22), t, font=ft, fill=(226, 186, 106))
img.save(out("swarm_design.png"))
print(img.size)
