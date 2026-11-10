"""Mock-up of the swarm's between-battles screen: three clutches, one is chosen; biomass spending."""
from PIL import Image, ImageFont
from kit import *
import swarm1 as W
from noise import value_noise
from paths import font, out
import icons as IC

S = 2
WW, HH = 960, 540
INK, MUTED, GOLD, BIO = (236, 226, 204), (176, 166, 150), (226, 186, 106), (150, 230, 110)
BADGE = {"гигант": (196, 150, 236), "новая форма": (226, 186, 106), "химера": (236, 120, 96)}


def frame(sc, x0, y0, x1, y1, hi=False, col=None):
    sc.rgb[y0:y1, x0:x1] = hexc("#16121e")
    rim = hexc(col) if col else (hexc("#e2b968") if hi else hexc("#6c7083"))
    dark = rim * 0.5
    sc.rgb[y0, x0:x1] = rim
    sc.rgb[y1 - 1, x0:x1] = dark
    sc.rgb[y0:y1, x0] = rim
    sc.rgb[y0:y1, x1 - 1] = dark
    for (cx, cy) in ((x0, y0), (x1 - 3, y0), (x0, y1 - 3), (x1 - 3, y1 - 3)):
        sc.rgb[cy:cy + 3, cx:cx + 3] = hexc("#7a5aa0")
    sc.occ[y0:y1, x0:x1] = True
    sc.light[y0:y1, x0:x1] = 0


def put(sc, spr, cx, by, sw=0):
    if sw:
        e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(2.5, sw * 0.2)) ** 2
        sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


# one offspring: (traits, soldier, chimera, hue, label, badge)
CLUTCHES = [
    dict(name="Линия жала", parents=((("stinger",), True, None, -0.1), (("ant",), False, None, 0.05)),
         parents_txt="скорпион-солдат × муравей", hint="отбор: жало +",
         kids=[(("stinger",), False, None, -0.08, "скорпион", None), (("stinger",), False, None, -0.03, "скорпион", None),
               (("stinger",), True, None, -0.1, "скорпион-солдат", None), (("ant", "stinger"), False, None, 0.04, "муравей с жалом", None)]),
    dict(name="Линия рога", parents=((("horn",), False, None, 0.12), (("wings",), False, None, -0.05)),
         parents_txt="жук × оса", hint="отбор: рог +",
         kids=[(("horn", "wings"), False, None, 0.1, "жук с крыльями", None), (("horn",), True, None, 0.12, "жук-солдат", None),
               (("wings", "horn"), False, None, -0.04, "оса с рогом", None), (("horn", "giant"), False, None, 0.14, "жук", "гигант")]),
    dict(name="Линия химер", parents=((("acid",), False, None, 0.02), (("ant",), True, "hand", -0.02)),
         parents_txt="бочонок × муравей с рукой", hint="съели людей: чужие черты",
         kids=[(("acid",), False, None, 0.03, "бочонок", None), (("acid",), False, "hand", 0.0, "бочонок с рукой", "химера"),
               (("ant",), True, "hand", -0.03, "муравей с рукой", "химера"), (("scythes",), False, None, 0.06, "богомол", "новая форма")]),
]
SELECTION = (("жало", 23, "stinger"), ("рог", 11, "horn"), ("кислота", 7, "acid"), ("серпы", 4, "scythes"))
HINT_ICON = ["stinger", "horn", "hand"]
KID_ICON = {"химера": "hand", "новая форма": "scythes"}


def icon(img, key, x, y, px):
    """Paste a swarm icon (16×16, nearest) of px pixels with its top-left at (x, y)."""
    im = Image.fromarray(IC.icon_rgba(key, "swarm"), "RGBA").resize((px, px), Image.NEAREST)
    img.paste(im, (int(x), int(y)), im)


def points(kid):
    traits, soldier = kid[0], kid[1]
    return (3 if soldier else 1) * (2 if "giant" in traits else 1)


def build():
    sc = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 31) * 0.6 + value_noise(WW, HH, 5, 32) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, c in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        sc.rgb[lv == i] = hexc(c)
    frame(sc, 0, 0, WW, 30)
    for i, cl in enumerate(CLUTCHES):
        x0 = 12 + i * 314
        frame(sc, x0, 40, x0 + 302, 384, hi=(i == 0))
        sc.glow(x0 + 151, 260, 120, hexc("#7ae040"), 0.10)
        for (traits, soldier, chim, hue), px in zip(cl["parents"], (x0 + 92, x0 + 210)):
            put(sc, W.build(traits, hue, "idle", soldier, k=1.15, chimera=chim), px, 128, 14)
        for j, (traits, soldier, chim, hue, _, _) in enumerate(cl["kids"]):
            cx = x0 + (82 if j % 2 == 0 else 222)
            by = 236 if j < 2 else 330
            sw = 16 if not soldier and "giant" not in traits else 22
            put(sc, W.build(traits, hue, "idle", soldier, k=1.5, chimera=chim, genes=W.genes_for(i * 10 + j)), cx, by, sw)
    frame(sc, 12, 394, 948, 432)
    for i, (_, kills, _) in enumerate(SELECTION):
        x = 250 + i * 176
        sc.rgb[410:418, x + 70:x + 160] = hexc("#2a2232")
        sc.rgb[410:418, x + 70:x + 70 + int(90 * kills / 23)] = hexc("#b04a3a") if i == 0 else hexc("#7a5a8a")
    frame(sc, 0, 442, WW, HH)
    for (x0, x1) in ((12, 236), (246, 470), (480, 704), (714, 948)):
        frame(sc, x0, 452, x1, 488, col="#6ac040")
    for (x0, x1, hi) in ((12, 236, False), (246, 470, False), (714, 948, True)):
        frame(sc, x0, 496, x1, 532, hi)
    return sc


def overlay(img):
    d = ImageDraw.Draw(img)
    f = lambda b, s: ImageFont.truetype(font("PTSerif-Bold.ttf" if b else "PTSerif-Regular.ttf"), s)
    d.text((20, 12), "Выводок · после боя 5 из 14 · выбери одну кладку", font=f(1, 24), fill=INK)
    t = "Биомасса 34   ·   Предел роя 41 / 45 очков"
    tx = WW * S - 24 - d.textlength(t, font=f(1, 21))
    d.text((tx, 15), t, font=f(1, 21), fill=BIO)
    icon(img, "biomass", tx - 40, 10, 34)
    for i, cl in enumerate(CLUTCHES):
        x0 = 12 + i * 314
        cx = (x0 + 151) * S
        d.text(((x0 + 12) * S, 48 * S), cl["name"], font=f(1, 22), fill=GOLD if i == 0 else INK)
        pts = sum(points(k) for k in cl["kids"])
        t = f"{len(cl['kids'])} особи · +{pts} очков"
        d.text(((x0 + 290) * S - d.textlength(t, font=f(0, 16)), 52 * S), t, font=f(0, 16), fill=MUTED)
        d.text((cx - d.textlength("×", font=f(1, 26)) / 2, 100 * S), "×", font=f(1, 26), fill=MUTED)
        t = "родители: " + cl["parents_txt"]
        d.text((cx - d.textlength(t, font=f(0, 15)) / 2, 138 * S), t, font=f(0, 15), fill=MUTED)
        for j, (_, _, _, _, label, badge) in enumerate(cl["kids"]):
            kx = (x0 + (82 if j % 2 == 0 else 222)) * S
            ky = (242 if j < 2 else 336) * S
            d.text((kx - d.textlength(label, font=f(0, 14)) / 2, ky), label, font=f(0, 14), fill=INK)
            if badge:
                bw = d.textlength(badge, font=f(1, 14))
                dx = 14 if badge in KID_ICON else 0
                d.text((kx - bw / 2 + dx, ky + 22), badge, font=f(1, 14), fill=BADGE[badge])
                if dx:
                    icon(img, KID_ICON[badge], kx - bw / 2 - 16, ky + 19, 26)
        hw = d.textlength(cl["hint"], font=f(1, 15))
        d.text((cx - hw / 2 + 16, 160 * S), cl["hint"], font=f(1, 15), fill=(150, 220, 120))
        icon(img, HINT_ICON[i], cx - hw / 2 - 18, 160 * S - 6, 30)
    icon(img, "selection", 34, 397 * S, 34)
    d.text((74, 404 * S), "Естественный отбор — убийства по чертам:", font=f(1, 16), fill=INK)
    for i, (name, kills, key) in enumerate(SELECTION):
        x = (250 + i * 176) * S
        icon(img, key, x + 18, 397 * S, 34)
        d.text((x + 58, 403 * S), name, font=f(0, 16), fill=INK)
        d.text((x + 330, 403 * S), str(kills), font=f(1, 14), fill=MUTED)
    spend = [(12, 236, "Кормление · 10: кладка +1", "feed"), (246, 470, "Эволюция формы · 15", "evolve"),
             (480, 704, "Вторая кладка · 10", "clutch"), (714, 948, "Перебросить · 5", "reroll")]
    for x0, x1, t, key in spend:
        tw = d.textlength(t, font=f(1, 17))
        d.text(((x0 + x1) * S / 2 - tw / 2 + 20, 461 * S), t, font=f(1, 17), fill=BIO)
        icon(img, key, (x0 + x1) * S / 2 - tw / 2 - 26, 455 * S, 40)
    for x0, x1, t in ((12, 236, "Автовыбор"), (246, 470, "Пропустить · +10 биомассы"), (714, 948, "В бой")):
        d.text(((x0 + x1) * S / 2 - d.textlength(t, font=f(1, 19)) / 2, 505 * S), t, font=f(1, 19),
               fill=(250, 226, 160) if t == "В бой" else INK)
    t = "Потомки сверх предела съедаются и дают биомассу."
    d.text(((480 + 704) * S / 2 - d.textlength(t, font=f(0, 15)) / 2, 506 * S), t, font=f(0, 15), fill=MUTED)


if __name__ == "__main__":
    sc = build()
    img = sc.image(S)
    overlay(img)
    img.save(out("brood.png"))
    print(img.size)
