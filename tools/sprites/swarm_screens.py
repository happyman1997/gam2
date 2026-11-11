"""Mock-ups of the swarm's other screens, in the brood screen's style:
  evolution  — «Эволюция формы»: the forms in the swarm, the chosen form's three evolutions as cards
  camp       — the camp: the swarm chooses a mutation itself — who gets it, which trait, what it will look like
  deploy     — deployment by flocks: the swarm stands in flocks of one kind, the player puts a flock on the cells
               and shapes it; the creatures settle inside by themselves

    python3 tools/sprites/swarm_screens.py      -> out/swarm_evolution_screen.png, out/swarm_camp.png, out/swarm_deploy.png
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
           ("carapace", "Панцирь", "шипы на спине: 1 колющего в ответ"), ("jumper", "Прыгучие ноги", "+2 к скорости в первом раунде"),
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
    d.text(((12 + 300) * S / 2 - d.textlength("Уйти из лагеря", font=f(1, 19)) / 2, 490 * S), "Уйти из лагеря", font=f(1, 19), fill=INK)
    t = "Мутировать"
    d.text(((714 + 948) * S / 2 - d.textlength(t, font=f(1, 19)) / 2, 490 * S), t, font=f(1, 19), fill=UI.DARK)
    t = "Гигант — сюрприз выводка, чужие черты — от съеденных."
    d.text(((300 + 714) * S / 2 - d.textlength(t, font=f(0, 15)) / 2, 490 * S), t, font=f(0, 15), fill=MUTED)
    img.save(out("swarm_camp.png"))
    print("swarm_camp.png", img.size)


# ---------------------------------------------------------------- deployment by flocks
CW_, CH_, GX0, GY0 = 40, 30, 20, 70           # deployment grid: the swarm's zone on the left, the enemy on the right
ZD = 0.62                                     # everyone at the same zoom: the true relative sizes
FLOCKS = [  # (traits, soldier, name, count, cells (col, row) it covers, colour, placed)
    ((), False, "муравьи", 19, [(c, r) for c in (6, 7) for r in range(2, 9)] + [(5, 4), (5, 5)], "#c9b27a", True),
    (("stinger",), False, "скорпионы", 7, [(4, 3), (4, 4), (4, 5), (4, 6)], "#d0603e", True),
    (("horn",), True, "жуки-солдаты", 2, [(7, 9), (7, 10)], "#c07040", True),
    (("acid",), False, "бочонки", 2, [(3, 4), (3, 5)], "#8ae04a", True),
    (("wings",), False, "осы", 4, [(5, 0), (6, 0), (6, 1)], "#e0b040", True),
    (("scythes",), False, "богомол", 1, [], "#9ab098", False),
    ((), True, "муравьи-солдаты", 2, [], "#c9b27a", False),
]


def deploy_screen():
    sc = ground(75)
    cols, rows = 21, 12
    for c in range(cols):                                       # the grid; the swarm's zone is the left 9 columns
        for r in range(rows):
            x, y = GX0 + c * CW_, GY0 + r * CH_
            col = hexc("#9a8ab8") if c < 9 else hexc("#c9b27a")
            if 9 <= c < 13:
                continue
            for dx, dy in ((0, 0), (1, 0), (0, 1)):
                sc.rgb[y + dy, x + dx] = sc.rgb[y + dy, x + dx] * 0.6 + col * 0.4
    zone = np.zeros((HH, WW), bool)
    zone[GY0:GY0 + rows * CH_, GX0:GX0 + 9 * CW_] = True
    sc.rgb[zone] = sc.rgb[zone] * 0.9 + hexc("#4a3a6a") * 0.1
    rnd = np.random.default_rng(3)
    items = []
    for k, (traits, soldier, name, n, cells, col, placed) in enumerate(FLOCKS):
        if not placed:
            continue
        m = np.zeros((HH, WW), bool)
        for (c, r) in cells:
            m[GY0 + r * CH_ + 2:GY0 + (r + 1) * CH_ - 2, GX0 + c * CW_ + 2:GX0 + (c + 1) * CW_ - 2] = True
        edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        sc.rgb[m] = sc.rgb[m] * 0.82 + hexc(col) * 0.18
        sc.rgb[edge & ((sc.xx + sc.yy) % 3 != 0)] = hexc(col)
        per = max(1, int(np.ceil(n / max(1, len(cells)))))
        placed_n = 0
        for (c, r) in cells:                                   # the creatures settle inside by themselves
            for j in range(per):
                if placed_n >= n:
                    break
                x = GX0 + c * CW_ + 10 + (j % 2) * 18 + rnd.uniform(-3, 3)
                y = GY0 + r * CH_ + 14 + (j // 2) * 10 + rnd.uniform(-2, 2)
                items.append((y, W.build(traits, rnd.uniform(-0.1, 0.1), "idle", soldier, k=ZD, genes=W.genes_for(k * 50 + placed_n)), x))
                placed_n += 1
    for (y, spr, x) in sorted(items, key=lambda t: t[0]):
        sc.blit(spr, int(x - spr.ox), int(y - spr.oy))
    q = W.queen(0.0, "idle", k=ZD)
    sc.blit(q, int(GX0 + 1.6 * CW_ - q.ox), int(GY0 + 6.6 * CH_ - q.oy))
    for name_, c, r, size in (("Страж", 14.5, 6.2, 6), ("Орудие", 15.0, 2.6, 5), ("Горн", 15.2, 9.8, 5), ("Механик", 17.4, 6.0, 4)):
        g = F.build(name_, "idle", k=F.FRAMES[name_][0] * ZD)
        g = g.flipped() if False else g
        f_ = g.flipped()
        f_.ox, f_.oy = g.w - 1 - g.ox, g.oy
        sc.blit(f_, int(GX0 + c * CW_ - f_.ox), int(GY0 + r * CH_ - f_.oy))
    # a pairing hint: two neighbouring flocks of different kinds — the brood's pairs
    for x in range(GX0 + 4 * CW_ + 30, GX0 + 5 * CW_ + 8, 3):
        sc.rgb[GY0 + 4 * CH_ + 15, x] = hexc("#7ae040")
    UI.plate(sc, 4, HH - 86, WW - 4, HH - 2)
    for k, (traits, soldier, name, n, cells, col, placed) in enumerate([fl for fl in FLOCKS if not fl[6]]):
        x0 = 12 + k * 150
        UI.cell(sc, x0, HH - 78, x0 + 142, HH - 10, "normal", col=col)
        put(sc, W.build(traits, 0.0, "idle", soldier, k=1.1, genes=W.genes_for(90 + k)), x0 + 34, HH - 24, 10)
    for k, t in enumerate(("Вытянуть в линию", "Собрать в кулак", "Разделить стаю", "Как в прошлом бою")):
        x0 = 316 + k * 158
        UI.button(sc, x0, HH - 62, x0 + 150, HH - 28, "chitin")
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    d.text((20, 18), "Расстановка · рой ставится стаями · на поле выходит вся армия", font=f(1, 24), fill=INK)
    t = "Литейщик: 4 голема"
    d.text((WW * S - 24 - d.textlength(t, font=f(0, 16)), 22), t, font=f(0, 16), fill=(214, 196, 150))
    for k, (traits, soldier, name, n, cells, col, placed) in enumerate(FLOCKS):
        if not placed:
            continue
        c = min(cells, key=lambda t: (t[1], t[0]))
        x, y = (GX0 + c[0] * CW_) * S, (GY0 + c[1] * CH_) * S - 26
        lab = f"{name} ×{n}"
        d.rectangle((x - 2, y - 2, x + d.textlength(lab, font=f(1, 15)) + 6, y + 22), fill=(20, 14, 26))
        d.text((x + 2, y), lab, font=f(1, 15), fill=tuple(int(v) for v in hexc(col)))
    d.text(((GX0 + 4 * CW_ + 30) * S, (GY0 + 4 * CH_ + 15) * S + 6), "пара: кладка", font=f(0, 13), fill=GREEN)
    for k, (traits, soldier, name, n, cells, col, placed) in enumerate([fl for fl in FLOCKS if not fl[6]]):
        x0 = (12 + k * 150) * S
        d.text((x0 + 120, (HH - 70) * S), name, font=f(1, 15), fill=INK)
        d.text((x0 + 120, (HH - 70) * S + 24), f"×{n} · не поставлена", font=f(0, 13), fill=MUTED)
    for k, t in enumerate(("Вытянуть в линию", "Собрать в кулак", "Разделить стаю", "Как в прошлом бою")):
        x0 = 316 + k * 158
        d.text(((x0 + 75) * S - d.textlength(t, font=f(0, 15)) / 2, (HH - 50) * S), t, font=f(0, 15), fill=INK)
    img.save(out("swarm_deploy.png"))
    print("swarm_deploy.png", img.size)


if __name__ == "__main__":
    evolution_screen()
    camp_screen()
    deploy_screen()
