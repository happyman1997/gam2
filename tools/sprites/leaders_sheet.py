"""Foundry leaders: an overview of all four, plus sheets for the Architect's and the Inventor's armies."""
from PIL import ImageFont
from kit import *
import architect as AR
import inventor as IV
import maniac as MN
from noise import value_noise
from paths import font, out

S = 2
GOLD, INK, MUT = (226, 186, 106), (236, 226, 200), (190, 182, 164)


def canvas(w, h, seed):
    sc = Scene(w, h)
    n = value_noise(w, h, 12, seed) * 0.6 + value_noise(w, h, 4, seed + 1) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, c in enumerate(("#2a2232", "#2e2536", "#32283c", "#362b40")):
        sc.rgb[lv == i] = hexc(c)
    return sc


def put(sc, spr, cx, by, sw):
    e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(3, sw * 0.18)) ** 2
    sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


def fonts():
    f = lambda b, s: ImageFont.truetype(font("PTSerif-Bold.ttf" if b else "PTSerif-Regular.ttf"), s)
    return f(1, 28), f(1, 22), f(1, 18), f(1, 15), f(0, 15)


LEADERS = [
    ("Отец колосса", "размер 6 · армия из одного",
     lambda p: IV.render_model(IV.colossus(p), 2.0, w=110, h=130, ox=46, oy=104), 70,
     [("Сотрясение", "каждые 3 хода: оглушает мелких врагов вокруг"),
      ("Неудержимый", "постоянно: не сдвинуть, не отбросить, не оглушить"),
      ("Второе дыхание", "раз за бой при поломке: встаёт с половиной прочности"),
      ("Один за всех", "поход: 7 ячеек и колоссальные модули, лидерства — на одного помощника")]),
    ("Изобретатель", "размер 3 · аугменты дают армии способности",
     lambda p: IV.render_model(IV.inventor(p), 3.0, w=50, h=56, ox=22, oy=46), 30,
     [("Шокер", "атака: бьёт током, оглушает механизмы"),
      ("Полевая настройка", "в начале боя: соседний голем получает аугмент на бой"),
      ("Перегрузка", "каждые 3 хода: аугмент соседа срабатывает дважды"),
      ("Мастерская аугментов", "поход: аугменты в мастерской, малые корпуса дешевле")]),
    ("Маньяк", "размер 4 · безумные конструкты",
     lambda p: MN.render_model(MN.maniac(p), 2.6, w=60, h=70, ox=28, oy=60), 34,
     [("Импровизация", "каждые 3 хода: модуль соседа на ход становится другим"),
      ("Это должно работать!", "когда его конструкт ломается: взрыв и град деталей"),
      ("Дикий смех", "постоянно: у врагов рядом падает боевой дух"),
      ("Свободная сборка", "поход: модули в любые ячейки, +2 к вместимости")]),
    ("Зодчий", "размер 4 · армия становится крепостью",
     lambda p: AR.render_model(AR.architect(p), 2.1, w=60, h=80, ox=28, oy=66), 34,
     [("Сигнал к развёртыванию", "на 2-м ходу: големы со строительными модулями разворачиваются"),
      ("Камень к камню", "постоянно: развёрнутых рядом не окружить, они чинятся"),
      ("Смена позиции", "каждые 4 хода: развёрнутый голем переходит на соседнюю клетку"),
      ("Чертёжная мастерская", "поход: строительные модули и каменщики в мастерской")]),
]


def overview():
    WW, HH = 960, 640
    sc = canvas(WW, HH, 21)
    for i, (_, _, fn, sw, _) in enumerate(LEADERS):
        x0, y0 = (i % 2) * 480, 50 + (i // 2) * 295
        put(sc, fn("idle"), x0 + 110, y0 + 180, sw)
        put(sc, fn("attack"), x0 + 300, y0 + 180, sw)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Литейщик: четыре лидера", font=ft, fill=INK)
    d.text((24, 60), "Лидер — юнит на поле. Способности срабатывают сами по условию. Гибель лидера бой не заканчивает.",
           font=fr, fill=MUT)
    for i, (name, sub, _, _, ab) in enumerate(LEADERS):
        x0, y0 = (i % 2) * 480 * S, (50 + (i // 2) * 295) * S
        d.text((x0 + 24, y0 + 6), name, font=fh, fill=GOLD)
        d.text((x0 + 24 + d.textlength(name, font=fh) + 12, y0 + 12), sub, font=fr, fill=MUT)
        y = y0 + 190 * S
        for nm, txt in ab:
            d.text((x0 + 24, y), nm, font=fbs, fill=INK)
            d.text((x0 + 24 + d.textlength(nm, font=fbs) + 10, y + 1), txt, font=fr, fill=MUT)
            y += 24
    img.save(out("foundry_leaders.png"))


def architect_sheet():
    WW, HH = 960, 520
    sc = canvas(WW, HH, 31)
    mods = [("tower", "Бойницы: башня", "каждый ход стреляет во 2–3 ряд"),
            ("wall", "Щит-стена: стена", "мелкие враги не проходят"),
            ("gate", "Створки: ворота", "свои проходят, враги нет"),
            ("bell", "Колокол: звонница", "каждые 3 хода: у врагов падает дух")]
    k = 1.5
    for i, (key, _, _) in enumerate(mods):
        cx = 60 + i * 230
        put(sc, AR.render_model(AR.with_module(key, False), k), cx, 200, 26)
        put(sc, AR.render_model(AR.with_module(key, True), k), cx + 110, 200, 30)
    for i, t in enumerate((1, 2, 3)):
        m = AR.Model()
        AR.wall_segment(m, 0.0, -14.0, 14.0, 13.0, t)
        spr = AR.render_model(m, 1.9, w=60, h=40, ox=30, oy=30)
        put(sc, spr, 120 + i * 170, 420, 30)
    put(sc, AR.render_model(AR.mason("idle"), 1.5), 690, 440, 22)
    put(sc, AR.render_model(AR.mason("attack"), 1.5), 840, 440, 22)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Зодчий: големы разворачиваются в укрепления", font=ft, fill=INK)
    d.text((24, 60), "Слева ходовой вид, справа развёрнутый. Развёртывание — способность по условию (например, на 2-м ходу).",
           font=fr, fill=MUT)
    for i, (_, name, txt) in enumerate(mods):
        cx = (60 + i * 230 + 55) * S
        d.text((cx - d.textlength(name, font=fbs) / 2, 212 * S), name, font=fbs, fill=INK)
        d.text((cx - d.textlength(txt, font=fr) / 2, 212 * S + 22), txt, font=fr, fill=MUT)
    d.text((24, 280 * S), "Уровни построек видны на спрайте", font=fh, fill=GOLD)
    for i, t in enumerate(("I · брёвна и хлам", "II · камень и бронза", "III · железо, шипы, руны")):
        cx = (120 + i * 170) * S
        d.text((cx - d.textlength(t, font=fr) / 2, 432 * S), t, font=fr, fill=INK)
    d.text((620 * S, 280 * S), "Каменщик", font=fh, fill=GOLD)
    d.text((620 * S, 280 * S + 30), "каждые 2 хода выкладывает отрезок стены", font=fr, fill=MUT)
    img.save(out("architect.png"))


def inventor_sheet():
    WW, HH = 960, 300
    sc = canvas(WW, HH, 41)
    augs = [("coil", "Грозовая катушка", "если рядом враг — каждые 2 хода бьёт его молнией"),
            ("mirror", "Отражатель", "первый удар в бою отражается в атакующего"),
            ("spring", "Пружинный рывок", "в начале боя прыгает к ближайшему врагу")]
    for i, (key, _, _) in enumerate(augs):
        cx = 90 + i * 320
        put(sc, IV.render_model(IV.augmented(key, "idle"), 1.6), cx, 210, 26)
        put(sc, IV.render_model(IV.augmented(key, "attack"), 1.6), cx + 140, 210, 26)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Изобретатель: аугмент добавляет голему способность, а не цифры", font=ft, fill=INK)
    d.text((24, 60), "Малые големы с аугментами. Слева покой, справа срабатывание.", font=fr, fill=MUT)
    for i, (_, name, txt) in enumerate(augs):
        cx = (90 + i * 320 + 70) * S
        d.text((cx - d.textlength(name, font=fb) / 2, 226 * S), name, font=fb, fill=INK)
        d.text((cx - d.textlength(txt, font=fr) / 2, 226 * S + 26), txt, font=fr, fill=MUT)
    img.save(out("inventor.png"))


if __name__ == "__main__":
    overview()
    architect_sheet()
    inventor_sheet()
    print("ok")
