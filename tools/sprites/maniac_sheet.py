"""The Maniac: crazy modules, their attacks, Improvisation (a module turns into something else for a turn)."""
from PIL import ImageFont
from kit import *
import maniac as MN
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 820
sc = Scene(WW, HH)
n = value_noise(WW, HH, 12, 13) * 0.6 + value_noise(WW, HH, 4, 14) * 0.4
th = BAYER[sc.yy % 4, sc.xx % 4]
lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
    sc.rgb[lv == i] = hexc(c)


def put(spr, cx, by, sw):
    e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(3, sw * 0.18)) ** 2
    sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


K = 1.9
MODS = [("saw", "Ноги-пилы", "постоянно: катится и режет всех на пути"),
        ("catapult", "Голова-катапульта", "каждые 2 хода: лом через строй во 2-й ряд"),
        ("spring", "Кулак на пружине", "каждые 3 хода: удар через клетку, отбрасывает"),
        ("triple", "Рука-рука-рука", "каждый ход: молот, клешня и пушка по очереди"),
        ("wheels", "Вверх ногами", "ходит на руках-колёсах, ноги машут молотами")]
cw = WW // len(MODS)
for i, (key, _, _) in enumerate(MODS):
    put(MN.render_model(MN.construct(key, "idle"), K), cw // 2 + i * cw - 6, 230, 30)
for i, key in enumerate(("saw", "catapult", "spring")):
    put(MN.render_model(MN.construct(key, "attack"), K), 110 + i * 190, 450, 30)
put(MN.render_model(MN.maniac("idle"), K * 1.55, w=60, h=70, ox=28, oy=60), 720, 450, 34)
put(MN.render_model(MN.maniac("attack"), K * 1.55, w=60, h=70, ox=28, oy=60), 860, 450, 34)
pairs = [("hammer", 90, 250), ("shield", 520, 680)]
for which, x0, x1 in pairs:
    put(MN.render_model(MN.improvised(which, False), K), x0, 730, 30)
    put(MN.render_model(MN.improvised(which, True), K), x1, 730, 30)

img = sc.image(S)
d = ImageDraw.Draw(img)
ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 18)
fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 15)
GOLD, INK, MUT = (226, 186, 106), (236, 226, 200), (190, 182, 164)
d.text((24, 16), "Маньяк: безумные модули и Импровизация", font=ft, fill=INK)
d.text((24, 66), "Безумные модули — детали не на своих местах. Каждая — своя способность.", font=fh, fill=GOLD)
for i, (_, name, txt) in enumerate(MODS):
    cx = (cw // 2 + i * cw - 6) * S
    d.text((cx - d.textlength(name, font=fb) / 2, 244 * S), name, font=fb, fill=INK)
    d.text((cx - d.textlength(txt, font=fr) / 2, 244 * S + 26), txt, font=fr, fill=MUT)
d.text((24, 300 * S), "Атака — отдельный спрайт", font=fh, fill=GOLD)
d.text((640 * S, 300 * S), "Маньяк — лидер", font=fh, fill=GOLD)
d.text((640 * S, 300 * S + 32), "на ходуле из хлама: пружина, колесо, деревяшка", font=fr, fill=MUT)
for cx, t in ((720, "покой"), (860, "атака")):
    d.text((cx * S - d.textlength(t, font=fr) / 2, 460 * S), t, font=fr, fill=MUT)
d.text((24, 520 * S), "Импровизация: на один ход модуль соседнего конструкта становится другим", font=fh, fill=GOLD)
d.text((24, 520 * S + 32), "Знак Импровизации — фиолетово-зелёные искры вокруг модуля и значок нового эффекта над ним.",
       font=fr, fill=MUT)
for (which, x0, x1), (a, b) in zip(pairs, (("молот", "огненный молот: бьёт пламенем в обе стороны"),
                                           ("щит", "щит раскрылся в пилу: режет соседей"))):
    yy = 742 * S
    d.text((x0 * S - d.textlength(a, font=fb) / 2, yy), a, font=fb, fill=INK)
    d.text((x1 * S - d.textlength(b, font=fr) / 2, yy + 4), b, font=fr, fill=INK)
    xa, xb, ya = (x0 + 55) * S, (x1 - 60) * S, 690 * S
    d.line([(xa, ya), (xb, ya)], fill=(220, 110, 220), width=4)
    d.polygon([(xb + 14, ya), (xb - 4, ya - 10), (xb - 4, ya + 10)], fill=(220, 110, 220))
img.save(out("maniac.png"))
print(img.size)
