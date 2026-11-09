"""The Maniac: his crazy constructs at rest and at work, the Maniac himself, Improvisation (a module of a neighbouring
construct turns into something else for a turn)."""
from kit import *
import golems_h as GH
import constructs as CN
from leaders_sheet import canvas, put, fonts, S, GOLD, INK, MUT
from paths import out

WW, HH = 960, 800
K = 1.9
sc = canvas(WW, HH, 13)
cells_ = list(CN.CONSTRUCTS) + ["maniac"]
CW, RH, Y0 = 240, 235, 50
caps = []
for i, key in enumerate(cells_):
    x0, y0 = (i % 4) * CW, Y0 + (i // 4) * RH
    by = y0 + 165
    if key == "maniac":
        sprs = [GH.build(GH.MANIAC, "idle", K * 0.82), GH.build(GH.MANIAC, "attack", K * 0.82)]
    else:
        sprs = [CN.build(key, "idle", k=K), CN.build(key, "go", k=K)]
    lows = []
    for j, spr in enumerate(sprs):
        put(sc, spr, x0 + 62 + j * 116, by, 26)
        lows.append(int(np.nonzero(spr.a.any(axis=1))[0].max()) - spr.oy)
    caps.append((x0, by + max(8, max(lows) + 4), key))
yi = Y0 + 2 * RH + 225                                         # Improvisation: before -> after
pairs = [("hammer", 90, 300), ("shield", 560, 770)]
for which, xa, xb in pairs:
    put(sc, CN.build_improvised(which, False, k=2.0), xa, yi, 40)
    put(sc, CN.build_improvised(which, True, k=2.0), xb, yi, 40)

img = sc.image(S)
d = ImageDraw.Draw(img)
ft, fh, fb, fbs, fr = fonts()
d.text((24, 16), "Маньяк: безумные конструкты и Импровизация", font=ft, fill=INK)
d.text((24, 60), "Свободная сборка: любой модуль на любой фрейм, а безумные модули — туда, где модулей не бывает. "
                 "Каждая «незаконная» деталь —", font=fr, fill=MUT)
d.text((24, 84), "своя способность; на ней знак Маньяка — фиолетово-зелёные искры. Слева покой, справа в деле.",
       font=fr, fill=MUT)
for x0, y, key in caps:
    if key == "maniac":
        name, frame, txt = "Маньяк", "лидер", "безумец в кабине-клетке: пила и бур"
    else:
        name, frame, txt, _ = CN.CONSTRUCTS[key]
    cx = (x0 + CW / 2) * S
    d.text((cx - d.textlength(name, font=fbs) / 2, y * S), name, font=fbs, fill=INK)
    d.text((cx - d.textlength(frame, font=fr) / 2, y * S + 22), frame, font=fr, fill=GOLD)
    d.text((cx - d.textlength(txt, font=fr) / 2, y * S + 42), txt, font=fr, fill=MUT)
d.text((24, (yi - 150) * S), "Импровизация: на один ход модуль соседнего конструкта становится другим", font=fh, fill=GOLD)
d.text((24, (yi - 150) * S + 32), "Знак — фиолетово-зелёные искры вокруг модуля и значок нового эффекта над ним.",
       font=fr, fill=MUT)
for (which, xa, xb), (a, b) in zip(pairs, (("молот", "молот изрыгает пламя в обе стороны"),
                                           ("щит", "щит раскрылся в пилу: режет соседей"))):
    yy = (yi + 10) * S
    d.text((xa * S - d.textlength(a, font=fb) / 2, yy), a, font=fb, fill=INK)
    d.text((xb * S - d.textlength(b, font=fr) / 2, yy + 4), b, font=fr, fill=INK)
    ya, x1, x2 = (yi - 50) * S, (xa + 80) * S, (xb - 90) * S
    d.line([(x1, ya), (x2, ya)], fill=(220, 110, 220), width=4)
    d.polygon([(x2 + 14, ya), (x2 - 4, ya - 10), (x2 - 4, ya + 10)], fill=(220, 110, 220))
img.save(out("maniac.png"))
print(img.size)
