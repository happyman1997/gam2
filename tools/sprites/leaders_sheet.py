"""Foundry leaders: an overview of all four, plus sheets for the Architect's and the Inventor's armies."""
from PIL import ImageFont
from kit import *
import colossus as CL
import golem7 as G7
import frames as F
import golems_h as GH
import leaders_h as LH
import swarm1 as SW
from noise import value_noise
from paths import font, out

S = 2
GOLD, INK, MUT, BAD = (226, 186, 106), (236, 226, 200), (190, 182, 164), (236, 112, 92)


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
    ("Отец колосса", "размер 7 · титан, армия из одного",
     lambda p: GH.colossus_build(p, 1.95), 80,
     [("Сотрясение", "каждые 3 хода: оглушает мелких врагов вокруг"),
      ("Неудержимый", "постоянно: не сдвинуть, не отбросить, не оглушить"),
      ("Ужас", "постоянно: враги до 3 клеток проверяют страх"),
      ("Второе дыхание", "раз за бой при поломке: встаёт с половиной прочности"),
      ("Один за всех", "поход: 7 ячеек и колоссальные модули, лидерства — на одного помощника"),
      ("Прожорливый", "слабость: ремонт стоит вдвое больше металла", 1)]),
    ("Изобретатель", "размер 3 · аугменты дают армии способности",
     lambda p: GH.build(LH.INVENTOR, p, 3.6), 30,
     [("Шокер", "атака: бьёт током, оглушает механизмы"),
      ("Полевая настройка", "в начале боя: соседний голем получает аугмент на бой"),
      ("Перегрузка", "каждые 3 хода: аугмент соседа срабатывает дважды"),
      ("Резонанс", "постоянно: аугменты рядом срабатывают на ход раньше"),
      ("Мастерская аугментов", "поход: аугменты в мастерской, фреймы на размер меньше"),
      ("На проводах", "слабость: погиб — аугменты армии гаснут", 1)]),
    ("Маньяк", "размер 4 · безумные конструкты",
     lambda p: GH.build(GH.MANIAC, p, 3.0), 38,
     [("Импровизация", "каждые 3 хода: модуль соседа на ход становится другим"),
      ("Это должно работать!", "когда его конструкт ломается: взрыв и град деталей"),
      ("Дикий смех", "постоянно: жуть — враги до 2 клеток проверяют страх"),
      ("Свободная сборка", "поход: модули любой роли в любой фрейм, +2 ячейки"),
      ("Без техники безопасности", "слабость: взрывы задевают и своих", 1)]),
    ("Зодчий", "размер 4 · армия становится крепостью",
     lambda p: GH.build(LH.ZODCHIY, p, 2.9), 40,
     [("Артель", "в начале боя: призывает каменщиков"),
      ("Сигнал к развёртыванию", "на 2-м ходу: големы со строительными модулями разворачиваются"),
      ("Камень к камню", "постоянно: развёрнутых рядом не окружить, они чинятся"),
      ("Смена позиции", "каждые 4 хода: развёрнутый голем переходит на соседнюю клетку"),
      ("Чертёжная мастерская", "поход: строительные модули в мастерской"),
      ("Долгая стройка", "слабость: пока не развернулись, не атакуют", 1)]),
]


ACCENT = ["#ff7a20", "#40d8ff", "#e060e0", "#e2b968"]


def overview():
    WW, HH = 960, 960
    sc = canvas(WW, HH, 21)
    QH = 330
    for i, (_, _, fn, sw, _) in enumerate(LEADERS):
        x0, y0 = (i % 2) * 480, 50 + (i // 2) * QH
        sc.glow(x0 + 200, y0 + 150, 190, hexc(ACCENT[i]), 0.28)
        put(sc, fn("idle"), x0 + 120, y0 + 220, sw)
        put(sc, fn("attack"), x0 + 330, y0 + 220, sw)
    # true relative scale
    yb = 50 + 2 * QH + 210
    r = 1.15 / 1.8
    row = [(GH.colossus_build("idle", 3.5 * r), "Отец колосса · 7", 70),
           (F.build("Страж", "idle", k=2.2 * r), "Страж · 6", 36),
           (F.build("Мудрец", "idle", k=1.6 * r), "Мудрец · 5", 24),
           (GH.build(LH.ZODCHIY, "idle", 1.05 * r), "Зодчий · 4", 16),
           (GH.build(LH.INVENTOR, "idle", 0.9 * r), "Изобретатель · 3", 10),
           (SW.build((), 0.0, "idle", k=r), "рабочая роя · 1", 6)]
    xs = [140, 340, 490, 610, 720, 810]
    for (spr, _, sw), x in zip(row, xs):
        put(sc, spr, x, yb, sw)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Литейщик: четыре лидера", font=ft, fill=INK)
    d.text((24, 60), "Лидер — юнит на поле. Способности срабатывают сами по условию. Гибель лидера бой не заканчивает. Все огнеупорны; красным — слабость.",
           font=fr, fill=MUT)
    for i, (name, sub, _, _, ab) in enumerate(LEADERS):
        x0, y0 = (i % 2) * 480 * S, (50 + (i // 2) * QH) * S
        d.text((x0 + 24, y0 + 6), name, font=fh, fill=hexc(ACCENT[i]).astype(int).tolist() and tuple(int(c) for c in hexc(ACCENT[i])))
        d.text((x0 + 24 + d.textlength(name, font=fh) + 12, y0 + 12), sub, font=fr, fill=MUT)
        y = y0 + 230 * S
        for nm, txt, *neg in ab:
            d.text((x0 + 24, y), nm, font=fbs, fill=BAD if neg else INK)
            d.text((x0 + 24 + d.textlength(nm, font=fbs) + 10, y + 1), txt, font=fr, fill=MUT)
            y += 24
    d.text((24, (50 + 2 * QH) * S + 6), "Масштаб: всё в настоящем соотношении размеров", font=fh, fill=GOLD)
    for (_, label, _), x in zip(row, xs):
        d.text((x * S - d.textlength(label, font=fr) / 2, (yb + 8) * S), label, font=fr, fill=INK)
    img.save(out("foundry_leaders.png"))


def architect_sheet():
    """The building modules: each frame marching with its module packed on the back, deployed (the golem
    plants itself and becomes the core of the building), and at work; below, the levels and the mason."""
    import buildings as BD
    WW, HH = 960, 1110
    sc = canvas(WW, HH, 31)
    K = {"Страж": 2.2, "Орудие": 1.6, "Горн": 1.6, "Мудрец": 1.6, "Механик": 1.15}       # the frames' battle scale
    f = 1.0
    mods = [("tower", "башня: каждый ход стреляет во 2–3 ряд", "стреляет", dict()),
            ("wall", "стена на 3 клетки: мелкие не пройдут", "уровень III", dict(t=3, pose="idle")),
            ("gate", "ворота: свои проходят, враги нет", "открыты", dict()),
            ("pitch", "каждые 3 хода льёт кипящую смолу", "льёт смолу", dict()),
            ("press", "вкапывается: первый враг рядом расплющен", "давит", dict()),
            ("thunder", "каждые 2 хода бьёт молнией в радиусе 4", "бьёт молнией", dict()),
            ("boom", "раз в 3 хода переставляет соседнего голема", "переставляет", dict()),
            ("forge", "раз в 2 хода чинит голема рядом", "чинит", dict())]
    rows_h, Y0 = (222, 222, 205, 160), 96                     # the Mechanic (size 4) needs less height
    labels = []
    for i, (key, desc, act, alt) in enumerate(mods):
        name, frame, _ = BD.MODULES[key]
        k = K[frame] * f
        x0, y0 = (i % 2) * 480, Y0 + sum(rows_h[:i // 2])
        by = y0 + rows_h[i // 2] - 38
        sw = 16 * k
        third = dict(t=alt.get("t", 2), pose=alt.get("pose", "attack"))
        lows = []
        for j, (dep, t, pose, cap) in enumerate(((False, 2, "idle", "в походе"), (True, 2, "idle", "развёрнут"),
                                                 (True, third["t"], third["pose"], act))):
            cx = x0 + 85 + j * 150
            spr = BD.build(key, dep, t, pose, k=k)
            put(sc, spr, cx, by, sw)
            lows.append(int(np.nonzero(spr.a.any(axis=1))[0].max()) - spr.oy)   # how far it reaches below the ground line
        for j, cap in enumerate(("в походе", "развёрнут", act)):
            labels.append((x0 + 85 + j * 150, by + max(9, max(lows) + 4), cap))
        labels.append((x0, y0, (name, frame, desc)))
    yb = Y0 + sum(rows_h) + 150                                       # the levels and the mason
    for j, t in enumerate((1, 2, 3)):
        put(sc, BD.build("tower", True, t, "idle", k=1.25), 90 + j * 150, yb, 26)
    put(sc, GH.build(GH.MASON, "idle", k=1.7), 690, yb, 18)
    put(sc, GH.build(GH.MASON, "attack", k=1.7), 830, yb, 18)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Зодчий: големы разворачиваются в укрепления", font=ft, fill=INK)
    d.text((24, 60), "Строительный модуль едет сложенным за спиной. Развернувшись, голем врастает в постройку и становится её "
                     "сердцевиной: щит — середина стены, Орудие стоит на своей башне.", font=fr, fill=MUT)
    d.text((24, 84), "Развёртывание — способность по условию (например, на 2-м ходу). Масштаб фреймов настоящий.", font=fr, fill=MUT)
    for x, y, cap in labels:
        if isinstance(cap, tuple):
            name, frame, desc = cap
            d.text(((x + 24) * S, (y + 6) * S), name, font=fbs, fill=GOLD)
            w = d.textlength(name, font=fbs)
            d.text(((x + 24) * S + w + 10, (y + 6) * S + 1), f"{frame} · {desc}", font=fr, fill=MUT)
        else:
            d.text((x * S - d.textlength(cap, font=fr) / 2, y * S), cap, font=fr, fill=INK)
    d.text((24, (yb - 128) * S), "Уровни построек видны на спрайте", font=fh, fill=GOLD)
    for j, t in enumerate(("I · брёвна и хлам", "II · камень и бронза", "III · железо, шипы, руны")):
        cx = (90 + j * 150) * S
        d.text((cx - d.textlength(t, font=fr) / 2, (yb + 9) * S), t, font=fr, fill=INK)
    d.text((620 * S, (yb - 128) * S), "Каменщик — призыв Зодчего", font=fh, fill=GOLD)
    d.text((620 * S, (yb - 128) * S + 30), "каждые 2 хода выкладывает отрезок стены", font=fr, fill=MUT)
    img.save(out("architect.png"))


def inventor_sheet():
    """Augments: each on a small frame at rest and going off; below, the Inventor's starting army to scale."""
    import augments as AU
    WW, HH = 960, 500
    sc = canvas(WW, HH, 41)
    small = 0.82                                                  # frames cast a size smaller
    K = {"Мудрец": 1.6, "Горн": 1.6, "Орудие": 1.6, "Механик": 1.15}
    augs = [("coil", "Орудие"), ("mirror", "Механик"), ("spring", "Горн")]
    by = 236
    caps = []
    for i, (key, frame) in enumerate(augs):
        cx = 90 + i * 320
        k = 2.0                                                   # the same size for all three: the augment is what matters
        for j, pose in enumerate(("idle", "active")):
            put(sc, AU.build(frame, key, pose, k=k), cx + j * 130, by, 16 * k)
        caps.append((cx + 65, key, frame))
    yb = HH - 40
    army = [(LH.INVENTOR, None, None, 0.9, "Изобретатель"),
            ("Мудрец", "coil", "Мудрец", K["Мудрец"] * small, "малый Мудрец · катушка"),
            ("Орудие", "coil", "Орудие", K["Орудие"] * small, "малое Орудие · катушка"),
            ("Механик", "mirror", "Механик", K["Механик"] * small, "малый Механик · отражатель")]
    xs = [150, 330, 520, 720]
    f = 1.5
    for (who, key, frame, k, _), x in zip(army, xs):
        spr = GH.build(who, "idle", k * f) if key is None else AU.build(frame, key, "idle", k=k * f)
        put(sc, spr, x, yb, 14 * k * f)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Изобретатель: аугмент добавляет голему способность, а не цифры", font=ft, fill=INK)
    d.text((24, 60), "Аугмент встаёт на любой фрейм — место находится по силуэту голема. Латунный корпус и синяя лампа: "
                     "аугменты держатся на Изобретателе,", font=fr, fill=MUT)
    d.text((24, 84), "погибнет он — лампы погаснут (слабость «На проводах»). Слева покой, справа срабатывание.",
           font=fr, fill=MUT)
    for cx, key, frame in caps:
        name, txt, _ = AU.AUGS[key]
        d.text((cx * S - d.textlength(name, font=fb) / 2, (by + 14) * S), name, font=fb, fill=INK)
        d.text((cx * S - d.textlength(txt, font=fr) / 2, (by + 14) * S + 26), txt, font=fr, fill=MUT)
        sub = f"на малом фрейме: {frame}"
        d.text((cx * S - d.textlength(sub, font=fr) / 2, (by + 14) * S + 48), sub, font=fr, fill=MUT)
    d.text((24, (by + 64) * S), "Стартовая армия: малые фреймы с аугментами, в настоящем масштабе", font=fh, fill=GOLD)
    for (_, _, _, _, label), x in zip(army, xs):
        d.text((x * S - d.textlength(label, font=fr) / 2, (yb + 8) * S), label, font=fr, fill=INK)
    img.save(out("inventor.png"))


if __name__ == "__main__":
    overview()
    architect_sheet()
    inventor_sheet()
    print("ok")
