"""Swarm combination sheets: every body form with every detail trait, castes and giants, foreign traits."""
from PIL import ImageFont
from kit import *
import swarm1 as W
from noise import value_noise
from paths import font, out

S = 2
INK, MUT, GOLD, DIM = (236, 226, 204), (176, 166, 150), (226, 186, 106), (110, 100, 120)
FORMS = (("ant", "Муравей"),) + tuple((t, W.PLANS[t]) for t in W.TRAITS)
DETAILS = ((None, "без детали"),) + tuple((t, W.NAMES[t]) for t in W.TRAITS)


def canvas(w, h, seed):
    sc = Scene(w, h)
    n = value_noise(w, h, 14, seed) * 0.6 + value_noise(w, h, 5, seed + 1) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, c in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        sc.rgb[lv == i] = hexc(c)
    return sc


def put(sc, spr, cx, by, sw=0):
    if sw:
        e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(2.5, sw * 0.2)) ** 2
        sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


def fonts():
    f = lambda b, s: ImageFont.truetype(font("PTSerif-Bold.ttf" if b else "PTSerif-Regular.ttf"), s)
    return f(1, 30), f(1, 20), f(1, 16), f(0, 15), f(0, 13)


def centered(d, x, y, text, fnt, fill):
    d.text((x - d.textlength(text, font=fnt) / 2, y), text, font=fnt, fill=fill)


# ---------------------------------------------------------------- every form × every detail
def combos():
    WW, X0, CW, RH, Y0 = 960, 104, 85, 84, 96
    HH = Y0 + RH * len(FORMS) + 20
    sc = canvas(WW, HH, 51)
    for r, (form, _) in enumerate(FORMS):
        hue = -0.14 + r * 0.035 if form != "spitter" else 0.0
        for c, (det, _) in enumerate(DETAILS):
            cx, by = X0 + c * CW + CW // 2, Y0 + (r + 1) * RH - 14
            if det == form:
                continue
            traits = (form,) + ((det,) if det else ())
            spr = W.build(traits, hue, "idle", False, k=1.55, genes=W.genes_for(r * 31 + c))
            put(sc, spr, cx, by, 13)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fr, fs = fonts()
    n = len(FORMS) * len(DETAILS) - (len(FORMS) - 1)
    d.text((24, 14), f"Рой: каждая форма с каждой деталью — {n} сочетаний рабочей касты", font=ft, fill=INK)
    d.text((24, 62), "Строки — главная черта (форма тела), столбцы — вторая черта (деталь). Окрас и пропорции наследуются, "
                     "поэтому и внутри клетки особи разные.", font=fr, fill=MUT)
    for c, (_, name) in enumerate(DETAILS):
        centered(d, (X0 + c * CW + CW // 2) * S, (Y0 - 18) * S, name, fs, GOLD)
    for r, (form, name) in enumerate(FORMS):
        d.text((14, (Y0 + r * RH + RH // 2 - 8) * S), name, font=fb, fill=INK)
        for c, (det, _) in enumerate(DETAILS):
            if det == form:
                centered(d, (X0 + c * CW + CW // 2) * S, (Y0 + r * RH + RH // 2 - 8) * S, "—", fb, DIM)
    img.save(out("swarm_combos.png"))


# ---------------------------------------------------------------- castes and giants
def castes():
    WW, BW, BH, Y0 = 960, 320, 168, 84
    HH = Y0 + BH * ((len(FORMS) + 2) // 3) + 20
    sc = canvas(WW, HH, 61)
    cols = ((False, (), "рабочая · 1"), (True, (), "солдат · 2"), (False, ("giant",), "гигант · 2"), (True, ("giant",), "гигант-солдат · 3"))
    xs = (46, 112, 188, 268)
    for i, (form, _) in enumerate(FORMS):
        x0, y0 = (i % 3) * BW, Y0 + (i // 3) * BH
        hue = -0.12 + i * 0.03
        for (soldier, extra, _), dx in zip(cols, xs):
            spr = W.build((form,) + extra, hue, "idle", soldier, k=1.25, genes=W.genes_for(i * 7 + 3))
            put(sc, spr, x0 + dx, y0 + 132, 16 if not extra else 24)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fr, fs = fonts()
    d.text((24, 14), "Рой: касты и гигантизм в настоящем соотношении размеров", font=ft, fill=INK)
    d.text((24, 62), "Каста меняет размер и голову (у солдата — жвалы), гигантизм — ещё +1 к размеру и раздутую "
                     "способность формы.", font=fr, fill=MUT)
    for i, (_, name) in enumerate(FORMS):
        x0, y0 = (i % 3) * BW, Y0 + (i // 3) * BH
        d.text(((x0 + 16) * S, (y0 + 8) * S), name, font=fh, fill=GOLD)
        for (_, _, label), dx in zip(cols, xs):
            centered(d, (x0 + dx) * S, (y0 + 140) * S, label, fs, MUT)
    img.save(out("swarm_castes.png"))


# ---------------------------------------------------------------- foreign traits
CHIMERA_TEXT = dict(iron=("литой металл", "молния +50%"), boil=("кипяток, огня не боится", "вода и холод ×2"),
                    hand=("хватка", "хватает и своих"), face=("жуть 1–6", "пугает своих"),
                    bones=("встаёт раз за бой", "дробящий ×2"), quills=("иглы на 3 клетки", "3 залпа за бой"),
                    snout=("по раненым +2", "бросает строй"), slime=("не горит, кислота ½", "сохнет на камне"),
                    worm=("червь кусает убийцу", "ест носителя"))
EXAMPLES = (("jumper", "face", "Кузнечик с лицом"), ("carapace", "iron", "Мокрица в железе"), ("stinger", "hand", "Скорпион с рукой"),
            ("acid", "worm", "Бочонок с червём"), ("scythes", "quills", "Богомол в иглах"), ("firefly", "boil", "Светляк с кипятком"))


def chimeras():
    WW, HH, CW = 960, 470, 106
    sc = canvas(WW, HH, 71)
    for i, c in enumerate(W.CHIMERAS):
        put(sc, W.build(("ant",), 0.02 * i - 0.08, "idle", True, k=2.0, chimera=c), 8 + i * CW + CW // 2, 168, 22)
    for i, (form, c, _) in enumerate(EXAMPLES):
        put(sc, W.build((form,), -0.1 + 0.04 * i, "attack", True, k=1.8, chimera=c), 80 + i * 160, 410, 24)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fr, fs = fonts()
    d.text((24, 14), "Чужие черты — химеры: живые части съеденных врагов", font=ft, fill=INK)
    d.text((24, 62), "Только биология. У каждой черты польза и причуда; на особи — не больше одной, наследуется.",
           font=fr, fill=MUT)
    for i, c in enumerate(W.CHIMERAS):
        cx = (8 + i * CW + CW // 2) * S
        good, bad = CHIMERA_TEXT[c]
        name = W.CHIMERA_NAMES[c]
        words = name.split(" ", 1)
        centered(d, cx, 180 * S, words[0], fs, GOLD)
        if len(words) > 1:
            centered(d, cx, 180 * S + 17, words[1], fs, GOLD)
        centered(d, cx, 180 * S + 40, good, fs, (150, 220, 120))
        centered(d, cx, 180 * S + 58, bad, fs, (236, 120, 96))
    d.text((24, 262 * S), "На других формах — в атаке", font=fh, fill=GOLD)
    for i, (_, _, label) in enumerate(EXAMPLES):
        centered(d, (80 + i * 160) * S, 424 * S, label, fb, INK)
    img.save(out("swarm_chimeras.png"))


if __name__ == "__main__":
    combos()
    castes()
    chimeras()
    print("ok")
