"""Modules and their levels on the humanoid frames: the Guard (its six modules and the rare ones that change its
body, each at levels I–III; what they do in battle; two builds put together), then the Sage, the Gorn, the Gun and
the Mechanic — six modules each at levels I–III.

    python3 tools/sprites/modules_sheet.py      -> out/guard_modules.png, out/<frame>_modules.png
"""
from kit import *
import guard_modules as GM
from leaders_sheet import canvas, put, fonts, S, GOLD, INK, MUT
from paths import out
import frame_modules as FMOD

FILES = {"Мудрец": "sage_modules.png", "Горн": "gorn_modules.png", "Орудие": "orudie_modules.png", "Механик": "meh_modules.png"}
LEADS = {"Мудрец": "его модули — заклинания: молния и огонь",
         "Горн": "печь на ногах: магнит, громоотвод, дым, свисток, пасть топки",
         "Орудие": "стрелок: мортира, длинный ствол, паучьи лапы, картечь, калёное ядро, бомбы",
         "Механик": "поддержка: ремонт, кран, запчасти, маслёнка, сварка, масляный бак"}


def frame_sheet(frame, K, sp=150):
    mods = FMOD.FRAMES[frame]
    WW, HH = 960, 92 + 3 * 175 + 24
    sc = canvas(WW, HH, 53)
    labels = []
    for i, (key, name, desc, _, _) in enumerate(mods):
        x0, y0 = (i % 2) * 480, 92 + (i // 2) * 175
        by = y0 + 150
        for j, t in enumerate((1, 2, 3)):
            cx = x0 + 95 + j * sp
            put(sc, FMOD.build(frame, key, t, k=K), cx, by, 30)
            labels.append(("lv", cx, by + 8, ("I", "II", "III")[j]))
        labels.append(("mod", x0, y0, (name, desc)))
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), f"{frame}: модули и их уровни на спрайте", font=ft, fill=INK)
    d.text((24, 60), f"{LEADS[frame]}. Модуль виден на големе и растёт с уровнем; на III уровне у него новая грань — "
                     "и новый вид.", font=fr, fill=MUT)
    for kind, x, y, v in labels:
        if kind == "mod":
            name, txt = v
            d.text(((x + 24) * S, (y + 8) * S), name, font=fbs, fill=GOLD)
            d.text(((x + 24) * S + d.textlength(name, font=fbs) + 10, (y + 8) * S + 1), txt, font=fr, fill=MUT)
        else:
            d.text((x * S - d.textlength(v, font=fb) / 2, y * S), v, font=fb, fill=INK)
    img.save(out(FILES[frame]))
    print(FILES[frame], img.size)



def rare_sheet():
    """The rare modules, each on a frame it suits, at levels I–III; below, the three cores."""
    KF = {"Мудрец": 2.3, "Горн": 2.2, "Орудие": 2.0, "Механик": 2.7}
    RH = 175
    WW, HH = 960, 92 + 6 * RH + 230
    sc = canvas(WW, HH, 57)
    labels = []
    for i, (key, name, desc, frame, _, _) in enumerate(FMOD.RARE):
        x0, y0 = (i % 2) * 480, 92 + (i // 2) * RH
        by = y0 + 150
        for j, t in enumerate((1, 2, 3)):
            G, _, fr = FMOD.rare_parts(key, t)
            cx = x0 + 95 + j * 150
            put(sc, FMOD.render_parts(G, fr, KF[fr]), cx, by, 30)
            labels.append(("lv", cx, by + 8, ("I", "II", "III")[j]))
        labels.append(("mod", x0, y0, (name, f"{frame} · {desc}")))
    yc = 92 + 6 * RH + 190
    for j, (kind, name, desc) in enumerate(FMOD.CORES):
        G, _, fr = FMOD.core_parts(kind)
        cx = 160 + j * 320
        put(sc, FMOD.render_parts(G, fr, 2.2), cx, yc, 30)
        labels.append(("core", cx, yc + 8, (name, desc)))
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr_ = fonts()
    d.text((24, 16), "Редкие модули и ядра", font=ft, fill=INK)
    d.text((24, 60), "Редкий модуль встаёт на любой фрейм; здесь каждый на том, кому он больше к лицу. Колёса-жернова "
                     "меняют ноги, Искрящий молот и Кочерга — то, что в руке.", font=fr_, fill=MUT)
    for kind, x, y, v in labels:
        if kind == "mod":
            name, txt = v
            d.text(((x + 24) * S, (y + 8) * S), name, font=fbs, fill=GOLD)
            d.text(((x + 24) * S + d.textlength(name, font=fbs) + 10, (y + 8) * S + 1), txt, font=fr_, fill=MUT)
        elif kind == "lv":
            d.text((x * S - d.textlength(v, font=fb) / 2, y * S), v, font=fb, fill=INK)
        else:
            name, txt = v
            d.text((x * S - d.textlength(name, font=fbs) / 2, y * S), name, font=fbs, fill=INK)
            d.text((x * S - d.textlength(txt, font=fr_) / 2, y * S + 24), txt, font=fr_, fill=MUT)
    d.text((24, (yc - 160) * S), "Ядро — стихия обычных ударов: окно в груди", font=fh, fill=GOLD)
    img.save(out("rare_modules.png"))
    print("rare_modules.png", img.size)


def guard_sheet():

    K = 2.1
    WW, HH = 960, 1200
    sc = canvas(WW, HH, 51)
    keys = list(GM.MODULES)
    RH, Y0 = 212, 92
    labels = []
    for i, key in enumerate(keys):
        x0, y0 = (i % 2) * 480, Y0 + (i // 2) * RH
        by = y0 + 184
        for j, t in enumerate((1, 2, 3)):
            cx = x0 + 95 + j * 150
            put(sc, GM.build(key, t, k=K), cx, by, 34)
            labels.append(("lv", cx, by + 8, ("I", "II", "III")[j]))
        labels.append(("mod", x0, y0, key))
    yb = Y0 + 4 * RH + 190                                         # in battle, and two builds
    battle = [(("plates",), 2, dict(lost=1), "лист сбит: осталось два"),
              (("plates",), 2, dict(lost=2), "сбит второй"),
              (("counter",), 2, dict(fired=True), "контрудар: шип выстрелил")]
    builds = [(("tower", "anchor", "plates"), {"tower": 3, "anchor": 2, "plates": 2}, "«Стена»: Ростовой щит III, Якорь II, Листы II"),
              (("counter", "hot", "flail"), {"counter": 3, "hot": 2, "flail": 1}, "«Наковальня»: Контрудар III, Раскалённая броня II, Кистень")]
    for j, (ks, t, kw, cap) in enumerate(battle):
        cx = 85 + j * 145
        put(sc, GM.build(list(ks), t, k=K, **kw), cx, yb, 34)
        labels.append(("cap", cx, yb + 8, cap))
    for j, (ks, t, cap) in enumerate(builds):
        cx = 590 + j * 230
        put(sc, GM.build(list(ks), t, k=K), cx, yb, 34)
        labels.append(("cap", cx, yb + 8, cap))

    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Страж: модули и их уровни на спрайте", font=ft, fill=INK)
    d.text((24, 60), "Модуль — способность, он стоит в ячейке и виден на големе. На III уровне он получает новую грань — "
                     "и новый вид. Редкие модули меняют само тело:", font=fr, fill=MUT)
    d.text((24, 84), "Гусеницы вместо ног, Кистень вместо молота. Модули складываются в сборку: каждый улучшается отдельно.",
           font=fr, fill=MUT)
    for kind, x, y, v in labels:
        if kind == "mod":
            name, txt = GM.MODULES[v][0], GM.MODULES[v][1]
            d.text(((x + 24) * S, (y + 8) * S), name, font=fbs, fill=GOLD)
            d.text(((x + 24) * S + d.textlength(name, font=fbs) + 10, (y + 8) * S + 1), txt, font=fr, fill=MUT)
        elif kind == "lv":
            d.text((x * S - d.textlength(v, font=fb) / 2, y * S), v, font=fb, fill=INK)
        else:
            words, lines, cur = v.split(" "), [], ""
            for wd in words:                                       # wrap long captions
                if d.textlength(cur + " " + wd, font=fr) > 200 * S and cur:
                    lines.append(cur)
                    cur = wd
                else:
                    cur = (cur + " " + wd).strip()
            lines.append(cur)
            for n, ln in enumerate(lines):
                d.text((x * S - d.textlength(ln, font=fr) / 2, y * S + n * 20), ln, font=fr, fill=INK)
    d.text((24, (yb - 170) * S), "В бою", font=fh, fill=GOLD)
    d.text((500 * S, (yb - 170) * S), "Сборки", font=fh, fill=GOLD)
    img.save(out("guard_modules.png"))
    print(img.size)


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["Страж", "Мудрец", "Горн", "Орудие", "Механик", "редкие"]
    K = {"Мудрец": 2.3, "Горн": 2.2, "Орудие": 2.0, "Механик": 2.7}
    for fr in which:
        if fr == "Страж":
            guard_sheet()
        elif fr == "редкие":
            rare_sheet()
        else:
            frame_sheet(fr, K[fr])
