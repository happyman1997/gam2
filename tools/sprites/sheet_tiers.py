from PIL import ImageFont
from kit import *
import golem6 as G
from noise import value_noise
from paths import font, out

S = 2
k = 2.0
w, h, ox, oy = G.dims(k)
A = ("tracks", "visor", "fire", "hammer", "shield")
B = ("springs", "sensor", "volt", "cannon", "claw")
cw, ch, top = 200, 250, 40
WW, HH = cw * 4, top + ch * 3
sc = Scene(WW, HH)
n = value_noise(WW, HH, 12, 7) * 0.6 + value_noise(WW, HH, 4, 8) * 0.4
th = BAYER[sc.yy % 4, sc.xx % 4]
lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
    sc.rgb[lv == i] = hexc(c)

def place(spr, cx, base_y):
    e = ((sc.xx - cx) / 40) ** 2 + ((sc.yy - base_y) / 8) ** 2
    sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(base_y - spr.oy))

caps = []
rows = [("Молотобоец", A), ("Пушкарь", B)]
for r, (name, cfg) in enumerate(rows):
    y0 = top + r * ch
    for i in range(3):
        cx = 100 + cw // 2 + i * cw
        place(G.build(cfg, i + 1, k=k), cx, y0 + 168)
    caps.append((r, name))
single = [("молот", dict(legs=1, head=1, core=1, far=3, near=1, armour=1)),
          ("щит", dict(legs=1, head=1, core=1, far=1, near=3, armour=1)),
          ("гусеницы", dict(legs=3, head=1, core=1, far=1, near=1, armour=1)),
          ("ядро и броня", dict(legs=1, head=1, core=3, far=1, near=1, armour=3))]
y0 = top + 2 * ch
for i, (lbl, lvd) in enumerate(single):
    cx = cw // 2 + i * cw
    place(G.build(A, lvd, k=k), cx, y0 + 168)
img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 19)
fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 15)
d.text((24, 18), "Модульный голем: улучшения видны на спрайте", font=ft, fill=(236, 226, 200))

def wrap(text, font, width):
    out, line = [], ""
    for word in text.split(" "):
        t = (line + " " + word).strip()
        if d.textlength(t, font=font) > width and line:
            out.append(line); line = word
        else:
            line = t
    out.append(line)
    return out

notes = {
    "Молотобоец": ["базовые модули",
                   "молот с шипами · рога · щит с шипом и заклёпками · броня на боках · юбки на гусеницах · клетка на ядре",
                   "молот с горящей руной · корона шипов · башенный щит · шипы на плечах · таран · ядро с отдушинами"],
    "Пушкарь": ["базовые модули",
                "длинный ствол с дульным тормозом · вторая антенна · большая линза · клешня в обойме · бронированные колени",
                "спаренные стволы и барабан · боковые линзы · четырёхпалая клешня · когти на ступнях · ядро с отдушинами"],
}
for r, name in caps:
    y = (top + r * ch) * S
    d.text((24, y + 8), name, font=fh, fill=(226, 186, 106))
    for i in range(3):
        cx = (100 + cw // 2 + i * cw) * S
        t = "Уровень " + "I" * (i + 1)
        d.text((cx - d.textlength(t, font=fb) / 2, y + 8), t, font=fb, fill=(236, 226, 200))
        yy = (top + r * ch + 180) * S
        for line in wrap(notes[name][i], fr, cw * S - 40):
            d.text((cx - d.textlength(line, font=fr) / 2, yy), line, font=fr, fill=(196, 188, 170))
            yy += 20
y = (top + 2 * ch) * S
d.text((24, y + 8), "Каждый модуль улучшается отдельно: остальные остаются на уровне I", font=fh, fill=(226, 186, 106))
for i, (lbl, _) in enumerate(single):
    cx = (cw // 2 + i * cw) * S
    t = f"{lbl}: уровень III"
    d.text((cx - d.textlength(t, font=fb) / 2, (top + 2 * ch + 182) * S), t, font=fb, fill=(236, 226, 200))
img.save(out("golem_tiers.png"))
print(img.size)
