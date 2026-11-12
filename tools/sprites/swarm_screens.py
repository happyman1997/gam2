"""Mock-ups of the swarm's other screens, in the brood screen's style:
  evolution  — «Эволюция формы»: the forms in the swarm, the chosen form's three evolutions as cards
  camp       — the camp: the swarm chooses a mutation itself — who gets it, which trait, what it will look like

    python3 tools/sprites/swarm_screens.py      -> out/swarm_evolution_screen.png, out/swarm_camp.png
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
import swarm1 as W
import swarm_evo as EV
import frames as F
from brood import put, icon, INK, MUTED, GOLD, BIO, S, WW, HH
import swarm_ui as UI
from noise import value_noise
from paths import font, out

RED = (240, 120, 96)
GREEN = (150, 220, 120)
f = UI.f


def ground(seed):
    sc = UI.nest(WW, HH, seed)
    UI.wing(sc, 0, 0, WW, 30)
    return sc


def wrap(d, text, font_, width):
    words, lines, cur = text.split(" "), [], ""
    for wd in words:
        if d.textlength(cur + " " + wd, font=font_) > width and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    lines.append(cur)
    return lines


# ---------------------------------------------------------------- evolution
FORMS_IN_SWARM = [(None, "муравей", 19, ("formic",)), ("wings", "оса", 4, ()), ("stinger", "скорпион", 7, ("vise",)),
                  ("horn", "жук", 3, ()), ("acid", "бочонок", 2, ()), ("scythes", "богомол", 1, ())]
CHOSEN = 2
COSTS = (15, 25, 40)


def evolution_screen():
    sc = ground(71)
    UI.plate(sc, 12, 40, 300, 446, antennae=True)
    for i, (form, name, n, taken) in enumerate(FORMS_IN_SWARM):
        y0 = 74 + i * 60
        UI.cell(sc, 20, y0, 292, y0 + 54, "hi" if i == CHOSEN else "normal")
        put(sc, W.build(() if form is None else (form,), 0.0, "idle", False, k=1.4, genes=W.genes_for(60 + i), evo=taken), 60,
            y0 + 46, 12)
    UI.plate(sc, 310, 40, 948, 446, antennae=True)
    form, name, n, taken = FORMS_IN_SWARM[CHOSEN]
    for j, (key, ename, what, look) in enumerate(EV.EVO[form]):
        x0 = 322 + j * 208
        is_taken = key in taken
        UI.cell(sc, x0, 92, x0 + 200, 436, "hi" if j == 1 else ("new" if is_taken else "normal"))
        put(sc, W.build((form,), -0.08, "idle", False, k=2.5, genes=W.genes_for(3), evo=(key,)), x0 + 104, 300, 22)
    UI.button(sc, 12, 474, 300, 520, "chitin")
    UI.button(sc, 714, 474, 948, 520, "amber")
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    d.text((20, 18), "Эволюция формы · все особи формы получают её сразу, и будущие тоже", font=f(1, 24), fill=INK)
    t = "Биомасса 39"
    tx = WW * S - 24 - d.textlength(t, font=f(1, 21))
    d.text((tx, 15), t, font=f(1, 21), fill=BIO)
    icon(img, "biomass", tx - 40, 10, 34)
    d.text((40, 50 * S), "Формы в рое", font=f(1, 19), fill=GOLD)
    for i, (form_, name_, n_, taken_) in enumerate(FORMS_IN_SWARM):
        y0 = (74 + i * 60) * S
        d.text((110 * S, y0 + 10), name_, font=f(1, 17), fill=INK)
        d.text((110 * S, y0 + 38), f"×{n_} · эволюций {len(taken_)} из 3", font=f(0, 14), fill=MUTED)
        for k, key in enumerate(taken_):
            icon(img, "evo_" + key, (250 + k * 20) * S, y0 + 14, 32)
    d.text((330 * S, 50 * S), f"{name.capitalize()} · {n} особей", font=f(1, 22), fill=GOLD)
    d.text((330 * S, 50 * S + 34), "каждая следующая эволюция этой формы дороже: 15, потом 25, потом 40", font=f(0, 15), fill=MUTED)
    nxt = COSTS[len(taken)]
    for j, (key, ename, what, look) in enumerate(EV.EVO[form]):
        x0 = (322 + j * 208) * S
        is_taken = key in taken
        icon(img, "evo_" + key, x0 + 16, 104 * S, 48)
        d.text((x0 + 76, 106 * S), ename, font=f(1, 17), fill=INK)
        d.text((x0 + 76, 106 * S + 26), "взята" if is_taken else f"{nxt} биомассы", font=f(1, 15), fill=GREEN if is_taken else BIO)
        for k, ln in enumerate(wrap(d, what, f(0, 15), 184 * S)):
            d.text((x0 + 16, 144 * S + k * 22), ln, font=f(0, 15), fill=INK)
        d.text((x0 + 16, 320 * S), "на спрайте: " + look, font=f(0, 14), fill=MUTED)
    d.text(((12 + 300) * S / 2 - d.textlength("Назад к выводку", font=f(1, 19)) / 2, 490 * S), "Назад к выводку", font=f(1, 19), fill=INK)
    t = f"Взять «{EV.EVO[form][1][1]}» · {nxt}"
    d.text(((714 + 948) * S / 2 - d.textlength(t, font=f(1, 19)) / 2, 490 * S), t, font=f(1, 19), fill=UI.DARK)
    t = "Разум улья: эволюция дешевле на 1 биомассу"
    d.text(((300 + 714) * S / 2 - d.textlength(t, font=f(0, 15)) / 2, 490 * S), t, font=f(0, 15), fill=MUTED)
    img.save(out("swarm_evolution_screen.png"))
    print("swarm_evolution_screen.png", img.size)


# ---------------------------------------------------------------- camp
CAMP_WHO = [((), True, "муравей-солдат", 2), ((), False, "муравей", 19), (("stinger",), False, "скорпион", 7),
            (("horn",), True, "жук-солдат", 2), (("wings",), False, "оса", 4), (("acid",), False, "бочонок", 2)]
DETAILS = [("wings", "Крылья", "Перепархивает: проходит над своими"), ("stinger", "Жало", "Жальце: +1–2 яда"),
           ("acid", "Кислотная железа", "раз за бой плевок, −1 брони"), ("horn", "Рог", "первый удар +2, дробящий"),
           ("carapace", "Панцирь", "шипы на спине: 1 колющего в ответ"), ("jumper", "Прыгучие ноги", "+2 к скорости в первый ход"),
           ("scythes", "Серпы", "инициатива +2"), ("firefly", "Светлячок", "раз за бой вспышка")]
MUTS_MET = [("spinner", "Прядильные железы"), ("nest", "Малое гнездо")]
PICK = 3                                     # «Рог»


def camp_screen():
    sc = ground(73)
    UI.plate(sc, 12, 40, 286, 446, antennae=True)
    for i, (traits, soldier, name, n) in enumerate(CAMP_WHO):
        y0 = 74 + i * 60
        UI.cell(sc, 20, y0, 278, y0 + 54, "hi" if i == 0 else "normal")
        put(sc, W.build(traits, 0.03, "idle", soldier, k=1.15 if soldier else 1.4, genes=W.genes_for(70 + i)), 58, y0 + 46, 12)
    UI.plate(sc, 296, 40, 652, 446, antennae=True)
    keys = [d[0] for d in DETAILS] + ["m_" + r[0] for r in MUTS_MET] + ["giant", "chimera"]
    for k, key in enumerate(keys):
        x0, y0 = 306 + (k % 4) * 86, 92 + (k // 4) * 100
        locked = key in ("giant", "chimera")
        UI.cell(sc, x0, y0, x0 + 80, y0 + 92, "locked" if locked else ("hi" if k == PICK else ("mut" if key.startswith("m_") else "normal")))
    UI.plate(sc, 662, 40, 948, 446, antennae=True)
    before = W.build((), 0.03, "idle", True, k=2.0, genes=W.genes_for(70))
    after = W.build(("ant", "horn"), 0.03, "idle", True, k=2.0, genes=W.genes_for(70))
    put(sc, before, 730, 236, 22)
    put(sc, after, 870, 236, 22)
    UI.button(sc, 12, 474, 300, 520, "chitin")
    UI.button(sc, 714, 474, 948, 520, "amber")
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    d.text((20, 18), "Лагерь · рой сам выбирает мутацию для одной особи", font=f(1, 24), fill=INK)
    d.text((32 * S, 50 * S), "Кто", font=f(1, 19), fill=GOLD)
    for i, (traits, soldier, name, n) in enumerate(CAMP_WHO):
        y0 = (74 + i * 60) * S
        d.text((104 * S, y0 + 12), name, font=f(1, 17), fill=INK)
        d.text((104 * S, y0 + 40), f"×{n}", font=f(0, 15), fill=MUTED)
    d.text((310 * S, 50 * S), "Какая черта", font=f(1, 19), fill=GOLD)
    d.text((310 * S, 50 * S + 32), "деталь любой черты или мутация — общая или Матки, — уже встреченная", font=f(0, 14), fill=MUTED)
    names = {d_[0]: d_[1] for d_ in DETAILS}
    names.update({"m_" + r[0]: r[1] for r in MUTS_MET})
    names.update(giant="гигантизм", chimera="чужая черта")
    for k, key in enumerate(keys):
        x0, y0 = (306 + (k % 4) * 86) * S, (92 + (k // 4) * 100) * S
        locked = key in ("giant", "chimera")
        if not locked:
            icon(img, key if not key.startswith("m_") else key, x0 + 48, y0 + 16, 64)
        nm = names[key]
        lines = wrap(d, nm, f(1, 14), 76 * S)
        for n_, ln in enumerate(lines):
            d.text((x0 + 80 * S / 2 - d.textlength(ln, font=f(1, 14)) / 2, y0 + 112 + n_ * 18), ln, font=f(1, 14),
                   fill=(110, 100, 120) if locked else (INK if not key.startswith("m_") else GOLD))
        if locked:
            d.text((x0 + 80 * S / 2 - d.textlength("только", font=f(0, 13)) / 2, y0 + 40), "только", font=f(0, 13), fill=(110, 100, 120))
            d.text((x0 + 80 * S / 2 - d.textlength("в выводке", font=f(0, 13)) / 2, y0 + 60), "в выводке", font=f(0, 13), fill=(110, 100, 120))
    d.text((680 * S, 50 * S), "Будет", font=f(1, 19), fill=GOLD)
    d.text((800 * S - 10, 200 * S), "→", font=f(1, 30), fill=INK) if False else None
    d.text((730 * S - d.textlength("сейчас", font=f(0, 15)) / 2, 246 * S), "сейчас", font=f(0, 15), fill=MUTED)
    d.text((870 * S - d.textlength("с рогом", font=f(0, 15)) / 2, 246 * S), "с рогом", font=f(0, 15), fill=MUTED)
    for k, ln in enumerate(wrap(d, "Муравей-солдат получает деталь «Рог»: первый удар боя +2 и дробящий — "
                                   "против литого металла. Деталь наследуется: в кладках этой линии появятся рога.",
                                   f(0, 16), 260 * S)):
        d.text((680 * S, 280 * S + k * 24), ln, font=f(0, 16), fill=INK)
    d.text(((12 + 300) * S / 2 - d.textlength("Уйти из Улья", font=f(1, 19)) / 2, 490 * S), "Уйти из Улья", font=f(1, 19), fill=INK)
    t = "Мутировать"
    d.text(((714 + 948) * S / 2 - d.textlength(t, font=f(1, 19)) / 2, 490 * S), t, font=f(1, 19), fill=UI.DARK)
    t = "Гигант — сюрприз выводка, чужие черты — от съеденных."
    d.text(((300 + 714) * S / 2 - d.textlength(t, font=f(0, 15)) / 2, 490 * S), t, font=f(0, 15), fill=MUTED)
    img.save(out("swarm_camp.png"))
    print("swarm_camp.png", img.size)


if __name__ == "__main__":
    # the screens themselves are drawn by swarm_hud (hand-made, text in the picture); this module keeps their data
    import swarm_hud
    for k in ("evolution", "camp"):
        swarm_hud.SCREENS[k]()
