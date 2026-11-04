"""Mock-up of the swarm's between-battles screen: brood, queen, evolution of a form, natural selection."""
from PIL import ImageFont
from kit import *
import swarm1 as W
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 540
INK, MUTED, GOLD, BIO = (236, 226, 204), (176, 166, 150), (226, 186, 106), (150, 230, 110)


def frame(sc, x0, y0, x1, y1, hi=False, col=None):
    sc.rgb[y0:y1, x0:x1] = hexc("#16121e")
    rim = hexc(col) if col else (hexc("#e2b968") if hi else hexc("#6c7083"))
    dark = rim * 0.5
    sc.rgb[y0, x0:x1] = rim; sc.rgb[y1 - 1, x0:x1] = dark
    sc.rgb[y0:y1, x0] = rim; sc.rgb[y0:y1, x1 - 1] = dark
    for (cx, cy) in ((x0, y0), (x1 - 3, y0), (x0, y1 - 3), (x1 - 3, y1 - 3)):
        sc.rgb[cy:cy + 3, cx:cx + 3] = hexc("#7a5aa0")
    sc.occ[y0:y1, x0:x1] = True
    sc.light[y0:y1, x0:x1] = 0


def put(sc, spr, cx, by, sw=0):
    if sw:
        e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(2.5, sw * 0.2)) ** 2
        sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


OFFSPRING = [(("horn", "wings"), 0.01, "Жук с крыльями", "оса × жук", "рог, крылья · размер 1"),
             (("wings", "carapace", "giant"), -0.02, "Огромная оса", "оса × мокрица", "крылья, панцирь · гигантизм"),
             (("acid", "scythes"), 0.05, "Бочонок с серпами", "бочонок × богомол", "кислота, серпы · размер 1")]
EVOLVE = [(("wings",), -0.08, "Осы × 12", "жало пробивает броню", 15),
          (("horn",), 0.12, "Жуки × 5", "рог отбрасывает на 2 клетки", 12),
          ((), 0.0, "Муравьи × 31", "+1 к скорости", 10)]
SELECTION = [("жало", 23), ("рог", 11), ("кислота", 7), ("серпы", 4)]


def build():
    sc = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 31) * 0.6 + value_noise(WW, HH, 5, 32) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, c in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        sc.rgb[lv == i] = hexc(c)
    sc.glow(150, 330, 200, hexc("#7ae040"), 0.25)       # the nest glows faintly
    frame(sc, 0, 0, WW, 30)
    # queen in her nest
    frame(sc, 10, 40, 300, 430)
    e = ((sc.xx - 150) / 132) ** 2 + ((sc.yy - 300) / 30) ** 2
    sc.rgb[(e <= 1)] = sc.rgb[(e <= 1)] * 0.6 + hexc("#3a2a40") * 0.4
    put(sc, W.queen(0.0, "idle", k=0.82), 190, 300)
    for (ex, ey) in ((50, 316), (62, 322), (44, 326), (250, 318), (262, 312)):
        egg = W.Model()
        egg.ell((0, 1.2, 0), (1.6, 1.2, 1.2), W.M_EGG)
        spr = W.render(egg.scaled(2.2), 16, 12, 8, 10, **W.STYLE1)
        sc.blit(spr, ex - 8, ey - 10)
    sc.rgb[352:360, 30:280] = hexc("#2a2232")
    sc.rgb[352:360, 30:30 + int(250 * 64 / 80)] = hexc("#6ac040")
    frame(sc, 30, 380, 280, 418, hi=False, col="#6ac040")
    # offspring cards
    for i, (t, hue, *_rest) in enumerate(OFFSPRING):
        x0 = 312 + i * 112
        frame(sc, x0, 40, x0 + 104, 300, hi=(i == 0))
        sc.rgb[52:150, x0 + 8:x0 + 96] = hexc("#1e1828")
        put(sc, W.build(t, hue, "idle", k=1.6 if "giant" not in t else 1.15), x0 + 52, 138)
    frame(sc, 312, 312, 640, 346, col="#6ac040")
    # evolution of a form
    frame(sc, 652, 40, 950, 250)
    for i, (t, hue, *_r) in enumerate(EVOLVE):
        y = 76 + i * 58
        frame(sc, 662, y, 940, y + 50, hi=(i == 0))
        put(sc, W.build(t, hue, "idle", k=1.05), 692, y + 42)
    # natural selection
    frame(sc, 652, 262, 950, 430)
    for i, (name, kills) in enumerate(SELECTION):
        y = 300 + i * 30
        sc.rgb[y + 8:y + 16, 760:930] = hexc("#2a2232")
        sc.rgb[y + 8:y + 16, 760:760 + int(170 * kills / 23)] = hexc("#b04a3a") if i == 0 else hexc("#7a5a8a")
    # bottom
    frame(sc, 0, 444, WW, HH)
    for (x0, x1, hi) in ((16, 216, False), (230, 470, False), (784, 944, True)):
        frame(sc, x0, 476, x1, 516, hi)
    return sc


def overlay(img):
    d = ImageDraw.Draw(img)
    f = lambda b, s: ImageFont.truetype(font("PTSerif-Bold.ttf" if b else "PTSerif-Regular.ttf"), s)
    d.text((20, 12), "Выводок · после боя 4 из 12", font=f(1, 24), fill=INK)
    t = "Биомасса: 37  (+14 за съеденных врагов)"
    d.text((WW * S - 24 - d.textlength(t, font=f(1, 21)), 15), t, font=f(1, 21), fill=BIO)
    d.text((40, 54 * S), "Матка", font=f(1, 22), fill=INK)
    d.text((40, 54 * S + 32), "лидер роя, размер 6", font=f(0, 15), fill=MUTED)
    d.text((60, 334 * S), "Предел численности: 64 / 80", font=f(0, 16), fill=INK)
    t = "Скормить · 10 биомассы даёт +8 к пределу"
    d.text((155 * S - d.textlength(t, font=f(1, 16)) / 2, 390 * S), t, font=f(1, 16), fill=BIO)
    for i, (_, _, name, parents, traits) in enumerate(OFFSPRING):
        cx = (312 + i * 112 + 52) * S
        tag = "ВЫВЕСТИ" if i == 0 else "яйцо"
        d.text((cx - d.textlength(tag, font=f(1, 14)) / 2, 160 * S), tag, font=f(1, 14), fill=GOLD if i == 0 else MUTED)
        for j, (txt, fnt, col) in enumerate(((name, f(1, 17), INK), (parents, f(0, 14), MUTED))):
            words, line, lines = txt.split(" "), "", []
            for w in words:
                tt = (line + " " + w).strip()
                if d.textlength(tt, font=fnt) > 96 * S and line:
                    lines.append(line); line = w
                else:
                    line = tt
            lines.append(line)
            for k, ln in enumerate(lines):
                d.text((cx - d.textlength(ln, font=fnt) / 2, (182 + j * 34) * S + k * 22), ln, font=fnt, fill=col)
        for k, part in enumerate(traits.split(" · ")):
            d.text((cx - d.textlength(part, font=f(0, 14)) / 2, 254 * S + k * 20), part, font=f(0, 14), fill=(200, 190, 170))
    t = "Ещё одно яйцо · 8 биомассы"
    d.text((476 * S - d.textlength(t, font=f(1, 17)) / 2, 321 * S), t, font=f(1, 17), fill=BIO)
    d.text((316 * S, 360 * S), "Потомство — от соседей, переживших бой.", font=f(0, 16), fill=MUTED)
    d.text((316 * S, 360 * S + 24), "Выбери одно, остальных съест матка.", font=f(0, 16), fill=MUTED)
    d.text((664 * S, 52 * S), "Эволюция формы — для всех сразу", font=f(1, 19), fill=INK)
    for i, (_, _, name, what, cost) in enumerate(EVOLVE):
        y = (76 + i * 58) * S
        d.text((720 * S, y + 12), name, font=f(1, 17), fill=INK)
        d.text((720 * S, y + 38), what, font=f(0, 15), fill=MUTED)
        t = f"{cost}"
        d.text((928 * S - d.textlength(t, font=f(1, 18)), y + 24), t, font=f(1, 18), fill=BIO)
    d.text((664 * S, 274 * S), "Естественный отбор", font=f(1, 19), fill=INK)
    d.text((664 * S, 274 * S + 28), "черты, что чаще убивают, чаще наследуются", font=f(0, 14), fill=MUTED)
    for i, (name, kills) in enumerate(SELECTION):
        y = (300 + i * 30) * S
        d.text((668 * S, y + 6), name, font=f(0, 16), fill=INK)
        t = str(kills)
        d.text((934 * S - d.textlength(t, font=f(1, 14)), y - 14), t, font=f(1, 14), fill=MUTED)
    btn = [(16, 216, "Автовыбор"), (230, 470, "Пропустить · +6 биомассы"), (784, 944, "В бой")]
    for x0_, x1_, t in btn:
        w = d.textlength(t, font=f(1, 20))
        d.text(((x0_ + x1_) * S / 2 - w / 2, 486 * S), t, font=f(1, 20), fill=INK if t != "В бой" else (250, 226, 160))
    d.text((20, 452 * S), "Пожирание: каждый съеденный в бою враг даёт биомассу. Обычно на выводок уходит 15–30 секунд.",
           font=f(0, 16), fill=MUTED)


if __name__ == "__main__":
    sc = build()
    img = sc.image(S)
    overlay(img)
    img.save(out("brood.png"))
    print(img.size)
