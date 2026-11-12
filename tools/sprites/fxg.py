"""The effects' own words: one small glyph per term — what triggers, what happens, what state it leaves — so an
effect is written as a row of glyphs with numbers and arrows, as in Conquest of Elysium, and the meaning of each
glyph is shown when the mouse is over it. A line is written with tokens: "{гибель_своя}{радиус:1} → {яйцо}" — a
term in braces, its number after a colon; the damage types of dmg.py are terms too.

    python3 tools/sprites/fxg.py      -> out/fx_glossary.png
"""
import re
import numpy as np
from PIL import Image
from kit import *
import dmg
import swarm_status as ST

OUT = hexc("#140c18")
C = dict(dmg.C)
C.update(S=hexc("#e8dcc0"), s=hexc("#a89878"), E=hexc("#f4ecd0"), e=hexc("#c8b890"), L=hexc("#efe0b8"),
         l=hexc("#b8a070"), D=hexc("#4a4456"), r=hexc("#ff8a6a"), V=hexc("#62b832"), g=hexc("#c8f08a"))

OWN = {
    "всегда": ["..........", ".WW....WW.", "W..W..W..W", "W...WW...W", "W..W..W..W", ".WW....WW."],
    "раз": ["..iiiii..", ".i.....i.", "i...W...i", "i..WW...i", "i...W...i", "i...W...i", "i..WWW..i",
            ".i.....i.", "..iiiii.."],
    "каждые": ["..aaaa...", ".a....a.a", "a......aa", "a.....aaa", "a........", "........a", "aaa.....a",
               "aa......a", "a.a....a.", "...aaaa.."],
    "ход": ["aaaaaaa", ".a...a.", ".ayyya.", "..aya..", "...a...", "..a.a..", ".a.y.a.", ".ayyya.", "aaaaaaa"],
    "атака": ["S.....S", "S.....S", "SS...SS", ".S...S.", ".SS.SS.", "..S.S..", "..S.S..", "...S..."],
    "пробой": ["IIIIIII", "IiiWiiI", "Iii.iiI", "IiW.iiI", ".Ii.iI.", ".IiWiI.", "..I.I..", "...I..."],
    "рана": ["...R...", "...R...", "..RRR..", ".RrRRR.", ".RRRRR.", "RRRRRRR", ".RRRRR.", "..RRR.."],
    "полрана": [".RR.DD.", "RrRRDDD", "RRRRDDD", "RRRRDDD", ".RRRDD.", "..RRD..", "...R..."],
    "гибель": ["..SSSSS..", ".SSSSSSS.", "SSkkSkkSS", "SSkkSkkSS", "SSSSkSSSS", ".SSSSSSS.", "..SkSkS..",
               "..SSSSS.."],
    "гибель_своя": ["..VVVVV..", ".VVgVVVV.", "VVkkVkkVV", "VVkkVkkVV", "VVVVkVVVV", ".VVVVVVV.", "..VkVkV..",
                    "..VVVVV.."],
    "радиус": ["..bbbbb..", ".b.....b.", "b..bbb..b", "b.b...b.b", "b.b.W.b.b", "b.b...b.b", "b..bbb..b",
               ".b.....b.", "..bbbbb.."],
    "выводок": ["...EE....", "..EEEE...", "..EeEE...", ".EE..EE..", "EEEEEEEE.", "EeEEEeEE.", ".EE..EE.."],
    "улей": ["..AAA..", ".A...A.", "A.aaa.A", "A.aAa.A", "A.aaa.A", ".A...A.", "..AAA.."],
    "ест": ["RRRRRRRRR", "RWRWRWRWR", "R.......R", "R.......R", "RWRWRWRWR", "RRRRRRRRR"],
    "конец": ["IAAAAA.", "IAaAaA.", "IAAAAA.", "IaAaAa.", "I......", "I......", "I......", "II....."],
    "начало": ["A......", "AA.....", "AaA....", "AaaA...", "AaaaA..", "AaaA...", "AaA....", "AA.....", "A......"],
    "машина": ["..I.I..", ".IIiII.", "IIi.iII", ".i...i.", "IIi.iII", ".IIiII.", "..I.I.."],
    "лидер": ["A..A..A", "AA.A.AA", "AAAAAAA", "AaAaAaA", "AAAAAAA"],
    "яйцо": ["..EEE..", ".EEEEE.", "EEEEEEE", "EEEEEeE", "EEEEeeE", ".EeeeE.", "..EEE.."],
    "личинка": ["...LLL...", "..LLLLL..", ".LLk..LL.", ".LL....L.", ".LLL.....", "..LLLL...", "...LLLLL.",
                "....LLL.."],
    "призыв": ["..VVV..", ".V.g.V.", "V..g..V", "VgggggV", "V..g..V", ".V.g.V.", "..VVV.."],
    "прикован": ["...I...", "..IiI..", "...I...", ".IIIII.", "...I...", "I..I..I", "II.I.II", ".IIIII."],
    "оглушение": ["y...y..", "yy.yyy.", ".y..y..", "...y...", "..yyy..", "...y..."],
    "перехват": ["IIIIIII", "IiiiiiI", "Ii.R.iI", "IiRRRiI", ".IiRiI.", "..IiI..", "...I..."],
    "притяг": ["..aaaa.", ".a....a", "a.....a", "a......", "a...a..", ".a.aa..", "..aaa.."],
    "споры": [".g...V.", "..V.g..", "V..g..V", ".g.V.g.", "..V..g.", "g..V..."],
    "мимо": ["IIIII..W", "Iiii..WW", "Iii..W.I", "Ii.W..iI", ".W...iI.", "W.IiiI..", "..III..."],
    "щит": ["IIIIIII", "IRiiiRI", "IiRiRiI", "IiiRiiI", ".IRiRI.", "..IRI..", "...I..."],
    "полёт": ["......bb", "....bbWb", "..bbWWb.", "bbWWbb..", "WWbb....", "bb......"],
    "деление": ["VV...VV", "V.V.V.V", "...V...", "...V...", "...V..."],
    "гигант": ["...A...", "..AAA..", ".AAAAA.", "...A...", "...A...", "..AAA.."],
    "бесплоден": ["..EEE.R", ".EEEER.", "EEEERE.", "EEERE..", "EERE...", ".REeE..", "R.EE..."],
    "выбор": ["W......", "WW.....", "WWW....", "WWWW...", "WWWWW..", "WWW....", "W.WW...", "...WW.."],
    "рост": ["...R...", "..RRR..", ".RRRRR.", "RRRRRRR", "..RRR..", "..RRR..", "..RRR.."],
    "тело": ["S.....S", "SS...SS", ".SSSSS.", "SS...SS", "S.....S"],
    "кокон": ["..SS...", ".SsSS..", ".SSsS..", ".SsSS..", ".SSsS..", "..SS...", "...S..."],
    "облако": [".D.D...", "D.D.D.D", ".D.D.D.", "D.D.D..", ".D...D."],
    "черта": [".AAAA.", "A....A", "....A.", "...A..", "...A..", "......", "...A.."],
    "копия": ["PPP....", "PpP.PPP", "PPP.PpP", "....PPP"],
    "реген": [".VV.VV.", "VgVVVVV", "VVVVVVV", ".VVVVV.", "..VVV..", "...V..."],
}

# term: (name, what it means, where the glyph comes from: "own" — above, ("status", key), ("dmg", key))
TERMS = {
    "всегда": ("Постоянно", "действует всё время", "own"),
    "раз": ("Раз за бой", "срабатывает один раз за бой", "own"),
    "каждые": ("Каждые N ходов", "срабатывает раз в N ходов", "own"),
    "ход": ("Ходы", "сколько ходов: «через N» после стрелки, «на N» после эффекта; ∞ — до конца боя", "own"),
    "атака": ("Атака", "при каждом её ударе", "own"),
    "пробой": ("Пробил броню", "удар прошёл сквозь броню цели", "own"),
    "рана": ("Ранена", "получила урон", "own"),
    "полрана": ("Ранена ниже половины", "здоровья меньше половины", "own"),
    "гибель": ("Гибель", "она погибла", "own"),
    "гибель_своя": ("Гибель своей", "погибла особь роя", "own"),
    "радиус": ("Радиус", "в N клетках от неё", "own"),
    "выводок": ("Выводок", "срабатывает в выводке после боя", "own"),
    "улей": ("Улей", "срабатывает между боями", "own"),
    "ест": ("Пожиратель ест", "Пожиратель ест рядом", "own"),
    "конец": ("Конец боя", "в конце боя", "own"),
    "начало": ("Начало боя", "в первом раунде", "own"),
    "машина": ("Машины", "против машин", "own"),
    "лидер": ("Лидер", "лидер роя рядом", "own"),
    "яйцо": ("Яйцо", "лежит на клетке; через 2 хода из него личинка", "own"),
    "личинка": ("Личинка", "особь размера 1; бьётся со следующего раунда", "own"),
    "призыв": ("Призыв", "появляется рядом с ней", "own"),
    "прикован": ("Прикован", "не перемещается; атаковать может", "own"),
    "оглушение": ("Оглушение", "N раундов не действует", "own"),
    "перехват": ("Перехват", "принимает удар по лидеру на себя; N — ударов за ход", "own"),
    "притяг": ("Притягивание", "тянет цель к рою; крупную — себя к ней", "own"),
    "споры": ("Споры", "заражает всех соседей, своих тоже", "own"),
    "мимо": ("Мимо брони", "броня цели не учитывается", "own"),
    "щит": ("Мимо щита", "щит цели не учитывается", "own"),
    "полёт": ("Полёт", "проходит сквозь своих", "own"),
    "деление": ("Деление", "делится на две особи, у каждой половина здоровья", "own"),
    "гигант": ("Гигант", "размер +1, способность формы сильнее", "own"),
    "бесплоден": ("Бесплоден", "в выводке не встаёт в пары", "own"),
    "выбор": ("Выбор игрока", "решает игрок", "own"),
    "рост": ("Рост", "здоровье ×1,4, удар +2", "own"),
    "тело": ("Тело", "труп, съеденный Пожирателем; N — сколько тел засчитано", "own"),
    "кокон": ("Кокон", "вместо хода; через 2 раунда выходит взрослой: здоровье полное, крылья, удар сильнее", "own"),
    "облако": ("Облако мошки", "ползёт к врагу, жалит мимо брони; стрелки сквозь него не видят", "own"),
    "черта": ("Случайная черта", "деталь, мутация или чужая черта — наугад", "own"),
    "копия": ("Хитиновая копия", "гигант-химера с чертой хозяина", "own"),
    "реген": ("Регенерация", "каждый раунд затягивает раны; горит — не заживает", "own"),
    "клей": ("Клей", "прикован N раундов: не перемещается, атаковать может", ("status", "glued")),
    "паутина": ("Паутина", "кто входит — застревает на 1 раунд; свои проходят", ("status", "web")),
    "мёд": ("Мёд", "враги в клетке вязнут: скорость ниже", ("status", "honey")),
    "броня": ("Броня", "броня цели меняется на N до конца боя; с одной цели не больше −2", ("status", "shred")),
    "ожог": ("Ожог", "его удар слабее до конца боя; не суммируется", ("status", "blister")),
    "страх": ("Страх", "проверка боевого духа на N; провалил — бежит", ("status", "fear")),
    "сбой": ("Сбой", "машина пропускает шаг, способности молчат раунд", ("status", "stall")),
    "помутнение": ("Помутнение", "N раундов бьёт случайную цель, свою тоже", ("status", "confused")),
    "захват": ("Захват", "враг бьётся за рой N ходов", ("status", "captured")),
    "лечение": ("Лечение", "восстанавливает здоровье; N — сколько", ("status", "heal")),
    "заражение": ("Заражение", "в нём кладка: погибнув, выпустит личинок", ("status", "infected")),
    "безумие": ("Кормовое безумие", "следующий удар сильнее", ("status", "frenzy")),
}
for k_, (nm, _rows) in dmg.GLYPHS.items():
    TERMS[k_] = (nm.capitalize(), {"кол": "колющий урон", "руб": "рубящий урон", "дроб": "дробящий урон",
                                   "огонь": "урон огнём; поджигает", "молния": "урон молнией", "холод": "урон холодом",
                                   "яд": "урон ядом каждый раунд; копится; машинам не страшен",
                                   "кисл": "урон кислотой; снимает броню", "пси": "урон мыслью, мимо брони; копит надлом"}[k_],
                 ("dmg", k_))

TOKEN = re.compile(r"\{([^}:]+)(?::([^}]*))?\}")


def rgba(key):
    """The glyph with its outline, as an RGBA array."""
    src = TERMS[key][2]
    if src == ("dmg", key) or (isinstance(src, tuple) and src[0] == "dmg"):
        return dmg.rgba(src[1])
    if isinstance(src, tuple) and src[0] == "status":
        rows = ST.GLYPHS[src[1]]
        h, w = len(rows), max(len(r) for r in rows)
        a = np.zeros((h, w, 4), np.uint8)
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    a[j, i, :3] = OUT if ch == "o" else ST.C[ch]
                    a[j, i, 3] = 255
        return a
    rows = OWN[key]
    h, w = len(rows), max(len(r) for r in rows)
    a = np.zeros((h + 2, w + 2, 4), np.uint8)
    m = np.zeros((h + 2, w + 2), bool)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                a[j + 1, i + 1, :3] = C[ch]
                a[j + 1, i + 1, 3] = 255
                m[j + 1, i + 1] = True
    ring = np.zeros_like(m)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ring |= np.roll(np.roll(m, dy, 0), dx, 1)
    ring &= ~m
    a[ring, :3] = OUT
    a[ring, 3] = 255
    return a


def draw(sc, key, x, y, z=1):
    a = rgba(key)
    for j in range(a.shape[0]):
        for i in range(a.shape[1]):
            if a[j, i, 3]:
                ys, xs = int(y) + j * z, int(x) + i * z
                if 0 <= ys and ys + z <= sc.h and 0 <= xs and xs + z <= sc.w:
                    sc.rgb[ys:ys + z, xs:xs + z] = a[j, i, :3]
                    sc.occ[ys:ys + z, xs:xs + z] = True
    return a.shape[1] * z


def parts(line):
    """A line split into text and terms: [("t", "→ "), ("g", "яйцо", None), ("g", "ход", "2"), ...]."""
    out, pos = [], 0
    for m in TOKEN.finditer(line):
        if m.start() > pos:
            out.append(("t", line[pos:m.start()]))
        out.append(("g", m.group(1), m.group(2)))
        pos = m.end()
    if pos < len(line):
        out.append(("t", line[pos:]))
    return out


def pil(key, z):
    a = rgba(key)
    return Image.fromarray(a, "RGBA").resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST)


def sheet():
    """The glossary: every term's glyph, its name and what it means."""
    from PIL import ImageDraw, ImageFont
    from paths import font, out
    keys = list(TERMS)
    cols, cw, rh = 3, 640, 58
    rows_n = (len(keys) + cols - 1) // cols
    img = Image.new("RGB", (cols * cw + 20, rows_n * rh + 80), (24, 18, 30))
    d = ImageDraw.Draw(img)
    fb = ImageFont.truetype(font("PTSerif-Bold.ttf"), 19)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 16)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 26)
    d.text((20, 14), "Значки эффектов: что срабатывает, что происходит, что остаётся", font=ft, fill=(236, 214, 160))
    for n, k_ in enumerate(keys):
        x, y = 20 + (n // rows_n) * cw, 64 + (n % rows_n) * rh
        g = pil(k_, 4)
        img.paste(g, (x + (48 - g.width) // 2, y + (48 - g.height) // 2), g)
        nm, what, _ = TERMS[k_]
        d.text((x + 62, y + 2), nm, font=fb, fill=(240, 200, 110))
        d.text((x + 62, y + 26), what, font=fr, fill=(214, 204, 220))
    img.save(out("fx_glossary.png"))
    print("fx_glossary.png", img.size)


if __name__ == "__main__":
    sheet()
