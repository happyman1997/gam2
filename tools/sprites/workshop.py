"""Mock-up of the between-battles workshop: pick 1 of 3 modules, drop it on a golem, done. The golems wear the
modules listed under them; the cards show the module icons (icons.py)."""
from PIL import ImageFont
from kit import *
import frames as F
import icons as IC
import guard_modules as GM
import frame_modules as FM
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 540
INK = (236, 226, 204)
MUTED = (176, 166, 150)
GOLD = (226, 186, 106)


def frame(sc, x0, y0, x1, y1, hi=False):
    sc.rgb[y0:y1, x0:x1] = hexc("#16121e")
    rim = hexc("#e2b968") if hi else hexc("#6c7083")
    dark = hexc("#8a6a30") if hi else hexc("#2d2f3d")
    sc.rgb[y0, x0:x1] = rim; sc.rgb[y1 - 1, x0:x1] = dark
    sc.rgb[y0:y1, x0] = rim; sc.rgb[y0:y1, x1 - 1] = dark
    sc.rgb[y0 + 1, x0 + 1:x1 - 1] = hexc("#474a5b"); sc.rgb[y0 + 1:y1 - 1, x0 + 1] = hexc("#474a5b")
    for (cx, cy) in ((x0, y0), (x1 - 3, y0), (x0, y1 - 3), (x1 - 3, y1 - 3)):
        sc.rgb[cy:cy + 3, cx:cx + 3] = hexc("#b78243")
    sc.occ[y0:y1, x0:x1] = True
    sc.light[y0:y1, x0:x1] = 0


def build():
    sc = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 21) * 0.6 + value_noise(WW, HH, 5, 22) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, c in enumerate(("#241e2c", "#282130", "#2c2434", "#302738")):
        sc.rgb[lv == i] = hexc(c)
    # stone floor seams
    for y in range(60, 430, 46):
        sc.rgb[y, 10:600] *= 0.75
    for y0 in range(60, 430, 46):
        off = 0 if (y0 // 46) % 2 else 34
        for x in range(10 + off, 600, 68):
            sc.rgb[y0:y0 + 46, x] *= 0.8
    sc.glow(30, 420, 220, hexc("#ff7a20"), 0.35)       # the forge off to the left

    frame(sc, 0, 0, WW, 30)
    # golems on pedestals
    golems = [   # (frame, display scale, module chips, the modules it wears)
        ("Страж", 1.0, ["Ростовой щит II · Перехват I", "Броневые листы I", "литое ядро"],
         {"tower": 2, "intercept": 1, "plates": 1}),
        ("Мудрец", 1.15, ["Цепная молния I · Огненный шар I", "Перегрузка II", "грозовое ядро"],
         {"chain": 1, "fireball": 1, "overload": 2}),
        ("Орудие", 1.15, ["Мортира I · Картечь I", "свободная ячейка", "литое ядро"],
         {"mortar": 1, "canister": 1, "long": 1}),            # the preview: Длинный ствол already in place
        ("Механик", 1.3, ["Ремонт I · Маслёнка I", "свободная ячейка", "литое ядро"],
         {"repair": 1, "oiler": 1}),
    ]
    xs = [86, 228, 370, 514]
    base = 318
    for i, (name, kk, _, mods) in enumerate(golems):
        x = xs[i]
        hi = i == 2
        e = ((sc.xx - x) / 62) ** 2 + ((sc.yy - base) / 15) ** 2
        ring = (e <= 1) & (e > 0.8)
        sc.rgb[e <= 1] *= 0.7
        sc.rgb[ring] = sc.rgb[ring] * 0.4 + (hexc("#e2b968") if hi else hexc("#5a5a6a")) * 0.6
        k = F.FRAMES[name][0] * kk
        if name == "Страж":
            spr = GM.build(list(mods), mods, k=k)
        else:
            spr = FM.build_multi(name, mods, k=k)
        sc.blit(spr, int(x - spr.ox), int(base - spr.oy))
    # reward cards
    frame(sc, 616, 40, 950, 74)
    cards = [(IC.icon("long", 5), True), (IC.icon("repair", 5), False), (IC.icon("grapple", 5), False)]
    ys = [84, 196, 308]
    for (ic, hi), y in zip(cards, ys):
        frame(sc, 616, y, 950, y + 102, hi)
        sc.rgb[y + 8:y + 94, 626:712] = hexc("#1e1828")
        sc.blit(ic, 669 - ic.ox, y + 51 - ic.oy)
    # bottom bar
    frame(sc, 0, 440, WW, HH)
    for (x0, x1, hi) in ((16, 196, False), (210, 450, False), (464, 704, False), (784, 944, True)):
        frame(sc, x0, 470, x1, 512, hi)
    return sc, golems, xs, base, ys


def overlay(img, golems, xs, base, ys):
    d = ImageDraw.Draw(img)
    f = lambda b, s: ImageFont.truetype(font("PTSerif-Bold.ttf" if b else "PTSerif-Regular.ttf"), s)
    d.text((20, 12), "Мастерская · после боя 4 из 12", font=f(1, 24), fill=INK)
    t = "Металл: 14"
    d.text((WW * S - 24 - d.textlength(t, font=f(1, 22)), 14), t, font=f(1, 22), fill=GOLD)
    for i, (name, _, chips, _m) in enumerate(golems):
        cx = xs[i] * S
        d.text((cx - d.textlength(name, font=f(1, 20)) / 2, (base + 22) * S), name, font=f(1, 20), fill=INK)
        for j, line in enumerate(chips):
            d.text((cx - d.textlength(line, font=f(0, 15)) / 2, (base + 22) * S + 30 + j * 20), line, font=f(0, 15), fill=MUTED)
    # preview tag over the target golem
    tag = "предпросмотр: Длинный ствол встал в свободную ячейку"
    tx = xs[2] * S
    w = d.textlength(tag, font=f(0, 15))
    ty = (base - 128) * S
    d.rectangle([tx - w / 2 - 10, ty, tx + w / 2 + 10, ty + 28], fill=(26, 20, 16), outline=(226, 186, 106))
    d.text((tx - w / 2, ty + 3), tag, font=f(0, 15), fill=(240, 220, 170))
    d.text((640 * S, 48 * S), "Награда: выбери 1 из 3", font=f(1, 24), fill=INK)
    cards = [("НОВЫЙ МОДУЛЬ", "Длинный ствол", ["бьёт самого дальнего врага насквозь", "для Орудия"]),
             ("УЛУЧШЕНИЕ", "Ремонт: уровень II", ["чинит на 6 вместо 4", "Ремонт уже стоит у Механика"]),
             ("РЕДКИЙ", "Крюк-кошка", ["цепляет врага из второго ряда", "и подтягивает к себе · любой фрейм"])]
    tagcol = {"НОВЫЙ МОДУЛЬ": (140, 200, 230), "УЛУЧШЕНИЕ": (226, 186, 106), "РЕДКИЙ": (210, 130, 230)}
    for (tg, name, lines), y in zip(cards, ys):
        x = 724 * S
        d.text((x, (y + 8) * S), tg, font=f(1, 14), fill=tagcol[tg])
        d.text((x, (y + 8) * S + 20), name, font=f(1, 22), fill=INK)
        for j, ln in enumerate(lines):
            d.text((x, (y + 8) * S + 54 + j * 21), ln, font=f(0, 16), fill=MUTED)
    # drag line from the chosen card to the golem
    x0, y0 = 616 * S, (ys[0] + 51) * S
    x1, y1 = xs[2] * S + 70, (base - 60) * S
    steps = 40
    for i in range(0, steps, 2):
        a, b = i / steps, (i + 1) / steps
        d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=(226, 186, 106), width=3)
    d.ellipse([x1 - 6, y1 - 6, x1 + 6, y1 + 6], fill=(226, 186, 106))
    btn = [(16, 196, "Автосборка"), (210, 450, "Починить всё · 3 металла"), (464, 704, "Пропустить · +4 металла"), (784, 944, "В бой")]
    for x0_, x1_, t in btn:
        w = d.textlength(t, font=f(1, 20))
        d.text(((x0_ + x1_) * S / 2 - w / 2, 480 * S), t, font=f(1, 20), fill=INK if t != "В бой" else (250, 226, 160))
    d.text((20, 448 * S), "Перетащи модуль на голема: спрайт и характеристики меняются сразу. Повтор модуля сам поднимает его уровень.",
           font=f(0, 16), fill=MUTED)


if __name__ == "__main__":
    sc, golems, xs, base, ys = build()
    img = sc.image(S)
    overlay(img, golems, xs, base, ys)
    img.save(out("workshop.png"))
    print(img.size)
