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
    "через": ["aaaaaaa", ".a...a.", ".ayyya.", "..aya..", "...a...", "..a.a..", ".a.y.a.", ".ayyya.", "aaaaaaa"],
    "на": ["a.......a", "aaaaaaaaa", "ayyyyyyya", "aaaaaaaaa", "a.......a"],
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
    "улей": ["..AAAA..", ".AaaaaA.", "AaaAAaaA", "AaAyyAaA", "AaaAAaaA", ".AaaaaA.", "..AAAA.."],
    "конец": ["IAAAAA.", "IAaAaA.", "IAAAAA.", "IaAaAa.", "I......", "I......", "I......", "II....."],
    "начало": ["A......", "AA.....", "AaA....", "AaaA...", "AaaaA..", "AaaA...", "AaA....", "AA.....", "A......"],
    "машина": ["..I.I..", ".IIiII.", "IIi.iII", ".i...i.", "IIi.iII", ".IIiII.", "..I.I.."],
    "лидер": ["A..A..A", "AA.A.AA", "AAAAAAA", "AaAaAaA", "AAAAAAA"],
    "яйцо": ["..EEE..", ".EEEEE.", "EEEEEEE", "EEEEEeE", "EEEEeeE", ".EeeeE.", "..EEE.."],
    "личинка": ["...LLL...", "..LLLLL..", ".LLk..LL.", ".LL....L.", ".LLL.....", "..LLLL...", "...LLLLL.",
                "....LLL.."],
    "призыв": ["g..V..g", ".g.V.g.", "..LLL..", "VVLkLVV", "..LLL..", ".g.V.g.", "g..V..g"],
    "прикован": ["...I...", "..IiI..", "...I...", ".IIIII.", "...I...", "I..I..I", "II.I.II", ".IIIII."],
    "оглушение": ["y...y..", "yy.yyy.", ".y..y..", "...y...", "..yyy..", "...y..."],
    "перехват": ["A.A.A.", "AAAAA.", "......", "IIIII.", "IiiiI.", ".IiI..", "..I..."],
    "притяг": ["WW...WW", "RR...II", "RR...II", "RR...II", ".RR.II.", "..RRI.."],
    "споры": [".g...V.", "..V.g..", "V..g..V", ".g.V.g.", "..V..g.", "g..V..."],
    "мимо": ["IIIII..W", "Iiii..WW", "Iii..W.I", "Ii.W..iI", ".W...iI.", "W.IiiI..", "..III..."],
    "щит": ["..III..", ".IiiiI.", "IRiiiRI", "IiRiRiI", "IiiRiiI", ".IRiRI.", "..III.."],
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
    "ожог": ["......Wi", ".....Wi.", "....Wi..", "........", "..Wi.A..", ".Wi.ARA.", "Wi...A.."],
    "захват": ["P.P.P..", "P.P.P.P", "PPPPP.P", "PpPPPPP", "PPPPPP.", ".PPPP..", "..pp...", ".p..p..", "..pp..."],
    "здоровье": [".RR.RR.", "RrRRRRR", "RRRRRRR", ".RRRRR.", "..RRR..", "...R..."],
    "броня": ["IIIIIII", "IiiiiiI", "IiWiiiI", "IiiiiiI", ".IiiiI.", "..IiI..", "...I..."],
    "скорость": ["....aa.", "aa..aaa", "...aaaa", "aaaaaaa", "...aaaa", "aa..aaa", "....aa."],
    "дух": ["...y...", "...y...", "yyyyyyy", ".yyyyy.", "..yyy..", ".yy.yy.", "y.....y"],
    "размер": ["......i", "....i.i", "..i.i.i", "i.i.i.i", "iiiiiii"],
    "дальность": [".....a.", ".....aa", "a.a.aaa", ".....aa", ".....a."],
    "инициатива": ["y..y...", "yy.yy..", ".yy.yy.", "..yy.yy", ".yy.yy.", "yy.yy..", "y..y..."],
    "урон": ["R..R..R", ".R.R.R.", "..RrR..", "RRrWrRR", "..RrR..", ".R.R.R.", "R..R..R"],
    "рабочая": ["...k....", "..k.....", ".ii.iii.", "iiiiiiii", ".i.i.i..", "i..i..i."],
    "свой": ["...k....", "..k.....", ".VV.VVV.", "VVVVVVVV", ".V.V.V..", "V..V..V."],
    "потомок": ["..EEE.V.", ".EEEEVVV", "EEEEE.V.", "EEEEEEE.", ".EeeeE..", "..EEE..."],
    "биомасса": ["..RRR..", ".RkRRR.", "RRRRkRR", "RkRRRRR", ".RRRkR.", "..RRR.."],
    "предел": ["...V...", "..VgV..", ".VgVVV.", "VVVVVVV", ".VVVVV.", "..VVV..", "...V..."],
    "хитин": ["..PPP..", ".PpPPP.", "PPPPPPP", "PkkkkkP", "PPPPPPP", ".PPPPP."],
    "тяжхитин": ["..III..", ".IiIII.", "IIIIIII", "IkkkkkI", "IIIIIII", "IkkkkkI", "IIIIIII"],
    "мягкое": ["..rrr..", ".rRrrr.", "rrrrrrr", ".rrrrr."],
    "облепили": ["g.g.g", ".kkk.", "gkkkg", ".kkk.", "g.g.g"],
    "пара": ["a.......a", ".aa.y.aa.", "aAAa.aAAa", ".aa...aa.", "a.a...a.a"],
    "гибрид": ["..VVRR..", ".VVVRRR.", "VVVVRRRR", ".VVVRRR.", "..VVRR.."],
    "наследие": ["...A...", "...A...", ".AAAAA.", "..AAA..", "...A...", "..EEE..", ".EEEEE.", "..EEE.."],
    "цепь": ["bbb......", "b.b......", "bbbbb....", "..b.b....", "..bbbbb..", "....b.b..", "....bbb.."],
    "убийца": ["......R", ".....RR", "....RR.", "...RR..", ".IRR...", "..I....", ".I.I..."],
    "носитель": [".yyyyy.", "..yyy..", "...y...", ".VVVVV.", "VVVVVVV", "V.V.V.V"],
    "ретранс": ["P.....P", ".P...P.", "..PPP..", "...P...", "..PPP..", "..P.P..", ".P...P."],
    "съедена": ["...k.k.", "....k..", ".VVVVRR", "VVgVR..", "VVVVVR.", ".VVVRR.", "V.V.V.."],
    "зов": ["R.R.R..", ".R.R.R.", "..R.R.R", ".R.R.R.", "R.R.R.."],
    "жир": ["...a...", "..aaa..", ".aaaaa.", "aaayaaa", "aaaaaaa", ".aaaaa."],
    "форма": ["..A.A..", "...A...", ".AAAAA.", "AAaAAAA", ".AAAAA.", "A.A.A.A"],
    "охрана": ["IIIIIII", "Ii.E.iI", "IiEEEiI", ".IiEiI.", "..IiI..", "...I..."],
    "площадь": ["A.A.A.A", ".......", "A.aaa.A", "..aRa..", "A.aaa.A", ".......", "A.A.A.A"],
    "рой": ["V.V.V", "VVVVV", ".....", "V.V.V", "VVVVV"],
    "мутация": ["V...R", ".V.R.", "..g..", ".R.V.", "R...V", ".R.V.", "..g..", ".V.R.", "V...R"],
    "одна_цель": ["a..a..a", ".a.a.a.", "..aaa..", "...R..."],
    "голод": ["IIIIIII", "IWIWIWI", "I.....I", "IWIWIWI", "IIIIIII"],
    "тыл": ["II..a..", "II.aa..", "IIaaaaa", "II.aa..", "II..a.."],
    "химера": [".t.t.t.", ".t.t.t.", "tttttt.", "ttttttt", ".ttttt.", "..ttt.."],
    "пёстрая": ["V.R.A", ".b.P.", "A.V.R"],
    "убийство": ["R...R", "RR.RR", ".RRR.", "..R..", ".r.r."],
    "клетка": ["iiiiiii", "i.....i", "i.....i", "i.....i", "i.....i", "iiiiiii"],
    "черта_боя": ["A.....A", ".A...A.", "..A.A..", "...A...", "..A.A..", ".A...A.", "A.....A"],
    "кормление": ["...R...", "..RRR..", "...R...", "AAAAAAA", "AaAaAaA", "AAAAAAA"],
    "цель": ["...R...", ".RRRRR.", ".R...R.", "RR.R.RR", ".R...R.", ".RRRRR.", "...R..."],
    "порода": ["k.......k...", ".k.......k..", "VVV.....VVV.", "VgVV.ii.VgVV", "VVVV....VVVV", "V.V..ii.V.V."],
    "солдат": ["..k.k.....", "WW.k......", ".WIII.III.", "WIIiIIIIII", ".IIIIIIII.", "..I.I.I.I.", ".I..I..I..", "I...I...I."],
    "новая_форма": ["......y..", ".....yWy.", "...k..y..", "..k......", ".AA.AAA..", "AAAAAAAA.", ".A.A.A...",
                    "A..A..A.."],
    "босс": ["W.......W", "WW.....WW", ".WIIIIIW.", ".IIIIIII.", "IIRkIkRII", "IIIIIIIII", ".IkIkIkI.", "..IIIII.."],
    "дикие": ["T...T...T..", ".T...T...T.", ".T...T...T.", "..T...T...T", "..t...t...t"],
    "живой": ["..tt..", "..tt..", ".tttt.", "t.tt.t", "..tt..", ".t..t.", ".t..t."],
    "стена": ["SSSsSSSsS", "sssssssss", "SsSSSsSSS", "sssssssss", "SSSsSSSsS", "sssssssss"],
}

# term: (name, what it means, where the glyph comes from: "own" — above, ("status", key), ("dmg", key))
TERMS = {
    "всегда": ("Постоянно", "действует всё время", "own"),
    "раз": ("Раз за бой", "срабатывает один раз за бой", "own"),
    "каждые": ("Каждые N ходов", "срабатывает раз в N ходов", "own"),
    "через": ("Через N ходов", "срабатывает через N ходов", "own"),
    "на": ("На N ходов", "длится N ходов; ∞ — до конца боя", "own"),
    "атака": ("Атака", "при каждом её ударе", "own"),
    "пробой": ("Пробил броню", "удар прошёл сквозь броню цели", "own"),
    "рана": ("Ранена", "получила урон", "own"),
    "полрана": ("Ранена ниже половины", "здоровья меньше половины", "own"),
    "гибель": ("Гибель", "она погибла", "own"),
    "гибель_своя": ("Гибель своей", "погибла особь роя", "own"),
    "радиус": ("Радиус", "в N клетках от неё", "own"),
    "выводок": ("Выводок", "срабатывает в выводке после боя", "own"),
    "улей": ("Улей", "срабатывает между боями", "own"),
    "конец": ("Конец боя", "в конце боя", "own"),
    "начало": ("Начало боя", "в первый ход", "own"),
    "машина": ("Машины", "против машин", "own"),
    "лидер": ("Лидер", "лидер роя рядом", "own"),
    "яйцо": ("Яйцо", "лежит на клетке; через 2 хода из него личинка", "own"),
    "личинка": ("Личинка", "особь размера 1; бьётся со следующего хода", "own"),
    "призыв": ("Призыв", "появляется рядом с ней", "own"),
    "прикован": ("Прикован", "не перемещается; атаковать может", "own"),
    "оглушение": ("Оглушение", "N ходов не действует", "own"),
    "перехват": ("Перехват", "принимает удар по лидеру на себя; N — ударов за ход", "own"),
    "притяг": ("Притягивание", "тянет цель к рою; крупную — себя к ней", "own"),
    "споры": ("Споры", "заражает всех соседей, своих тоже", "own"),
    "мимо": ("Мимо брони", "броня цели не учитывается; N — сколько брони", "own"),
    "щит": ("Мимо щита", "щит цели не учитывается", "own"),
    "полёт": ("Полёт", "проходит сквозь своих", "own"),
    "деление": ("Деление", "делится на две особи, у каждой половина здоровья", "own"),
    "гигант": ("Гигант", "размер +1, способность формы сильнее", "own"),
    "бесплоден": ("Бесплоден", "в выводке не встаёт в пары", "own"),
    "выбор": ("Выбор игрока", "решает игрок", "own"),
    "рост": ("Рост", "здоровье ×1,4, удар +2", "own"),
    "тело": ("Тело", "съеденный труп врага; N — сколько тел", "own"),
    "кокон": ("Кокон", "вместо хода; выходит взрослой", "own"),
    "облако": ("Облако мошки", "ползёт к врагу, жалит мимо брони; стрелки сквозь него не видят", "own"),
    "черта": ("Случайная черта", "деталь, мутация или чужая черта — наугад", "own"),
    "копия": ("Хитиновая копия", "гигант-химера с чертой хозяина", "own"),
    "реген": ("Регенерация", "каждый ход затягивает раны; горит — не заживает", "own"),
    "здоровье": ("Здоровье", "сколько урона выдержит", "own"),
    "броня": ("Броня", "вычитается из урона; −N — броня цели ниже до конца боя", "own"),
    "скорость": ("Скорость", "клеток за ход", "own"),
    "дух": ("Боевой дух", "чем выше, тем реже бежит", "own"),
    "размер": ("Размер", "1 — мелкая, 7 — титан; сколько клеток занимает", "own"),
    "дальность": ("Дальность", "на сколько клеток бьёт", "own"),
    "инициатива": ("Инициатива", "кто бьёт раньше", "own"),
    "урон": ("Урон", "сила удара; со знаком — изменение", "own"),
    "рабочая": ("Рабочая", "особь размера 1", "own"),
    "свой": ("Свой", "особь роя", "own"),
    "потомок": ("Потомок", "новая особь из выводка", "own"),
    "биомасса": ("Биомасса", "валюта роя", "own"),
    "предел": ("Предел роя", "сколько очков вмещает рой; у особи — сколько она занимает", "own"),
    "хитин": ("Хитин", "{руб} ×½, {дроб} ×2", "own"),
    "тяжхитин": ("Тяжёлый хитин", "{руб} ×½, {кол} ×½, {дроб} ×2", "own"),
    "мягкое": ("Мягкое тело", "{кол} ×2", "own"),
    "облепили": ("Облепили", "2 и больше своих бьют одну цель", "own"),
    "пара": ("Пара", "родители потомка в выводке", "own"),
    "гибрид": ("Гибрид", "потомок: тело одной формы, способности обеих", "own"),
    "наследие": ("Наследие", "главная черта — потомкам; N — с каким шансом", "own"),
    "цепь": ("Цепь", "передаётся дальше: от особи к особи с той же мутацией", "own"),
    "убийца": ("Убийца", "тот, кто её убил", "own"),
    "носитель": ("Носитель", "особь с этой мутацией", "own"),
    "ретранс": ("Ретранслятор", "Разум бьёт, мутит и захватывает с клетки носителя", "own"),
    "съедена": ("Съедена", "своя особь съедена: Пожирателем в бою или в выводке", "own"),
    "зов": ("Зов крови", "Пожиратель идёт к её трупу и съедает", "own"),
    "жир": ("Жир", "сколько вырастет Пожиратель, съев её", "own"),
    "форма": ("Способность формы", "жало, крылья, плевок…", "own"),
    "охрана": ("Охрана", "стоит над личинками, бьёт всех рядом", "own"),
    "площадь": ("Удар по площади", "бьёт всех в клетке", "own"),
    "рой": ("Рой", "все особи роя", "own"),
    "мутация": ("Мутация", "черта, которой не было у родителей", "own"),
    "одна_цель": ("Одна цель", "вся стая бьёт цель первой напавшей особи", "own"),
    "голод": ("Голод", "ходов без еды", "own"),
    "тыл": ("Тыл врага", "клетка за строем врага", "own"),
    "химера": ("Чужая черта", "от хозяина: рука, панцирь, кости…", "own"),
    "пёстрая": ("Пёстрая стая", "в одной стае разные виды", "own"),
    "убийство": ("Убила", "она убила врага", "own"),
    "клетка": ("Клетка", "одна клетка поля", "own"),
    "черта_боя": ("Черта боя", "черта, что в этом бою убила больше всех", "own"),
    "кормление": ("Кормление лидера", "цена в биомассе", "own"),
    "цель": ("Цель", "кого бьют; N — очередь", "own"),
    "порода": ("Одна форма", "особи одной формы", "own"),
    "солдат": ("Солдат", "крупная особь формы; 3 очка предела", "own"),
    "новая_форма": ("Новая форма", "формы, которой в рое ещё нет", "own"),
    "босс": ("Босс", "главный враг края", "own"),
    "дикие": ("Дикие", "звери или чужой рой", "own"),
    "живой": ("Живой враг", "не машина: человек, зверь, рой", "own"),
    "стена": ("Стена", "стены и постройки врага", "own"),
    "клей": ("Клей", "прикован N ходов: не перемещается, атаковать может", ("status", "glued")),
    "паутина": ("Паутина", "кто входит — застревает на 1 ход; свои проходят", ("status", "web")),
    "мёд": ("Мёд", "враги в клетке вязнут: скорость ниже", ("status", "honey")),
    "ожог": ("Ожог", "его удар слабее до конца боя; не суммируется", "own"),
    "страх": ("Страх", "проверка боевого духа на N; провалил — бежит", ("status", "fear")),
    "сбой": ("Сбой", "машина пропускает шаг, способности молчат ход", ("status", "stall")),
    "помутнение": ("Помутнение", "N ходов бьёт случайную цель, свою тоже", ("status", "confused")),
    "захват": ("Захват", "враг бьётся за рой N ходов", "own"),
    "лечение": ("Лечение", "восстанавливает здоровье; N — сколько", ("status", "heal")),
    "заражение": ("Заражение", "в нём кладка: погибнув, выпустит личинок", ("status", "infected")),
    "безумие": ("Кормовое безумие", "следующий удар сильнее", ("status", "frenzy")),
}
for k_, (nm, _rows) in dmg.GLYPHS.items():
    TERMS[k_] = (nm.capitalize(), {"кол": "колющий урон", "руб": "рубящий урон", "дроб": "дробящий урон",
                                   "огонь": "урон огнём; поджигает", "молния": "урон молнией", "холод": "урон холодом",
                                   "яд": "урон ядом каждый ход; копится; машинам не страшен",
                                   "кисл": "урон кислотой; снимает броню", "пси": "урон мыслью, мимо брони; копит надлом"}[k_],
                 ("dmg", k_))

TOKEN = re.compile(r"\{([^}:]+)(?::([^}]*))?\}")

# the glossary's chapters, for the in-game reference; whatever is not named here falls into «Что делает»
GROUPS = [
    ("Когда", ["всегда", "раз", "начало", "конец", "атака", "пробой", "рана", "полрана", "гибель", "гибель_своя",
               "убийство", "радиус", "клетка", "площадь", "облепили", "лидер", "голод", "выводок", "улей"]),
    ("Время", ["каждые", "через", "на"]),
    ("Что делает", []),
    ("Состояния", ["клей", "паутина", "мёд", "ожог", "страх", "сбой", "помутнение", "захват", "оглушение", "прикован",
                   "лечение", "заражение", "безумие", "реген"]),
    ("Судьба", ["здоровье", "броня", "хитин", "тяжхитин", "мягкое", "скорость", "дух", "размер", "дальность",
                "инициатива", "урон", "предел"]),
    ("Выводок", ["потомок", "пара", "наследие", "мутация", "гибрид", "бесплоден", "химера", "пёстрая", "черта_боя",
                 "порода", "солдат", "новая_форма", "рабочая", "свой", "рой", "биомасса", "кормление", "съедена",
                 "тело", "выбор"]),
    ("Враги", ["машина", "живой", "дикие", "босс", "стена", "тыл", "цель", "убийца"]),
    ("Урон", list(dmg.GLYPHS)),
]
_named = {k for _, ks in GROUPS for k in ks}
GROUPS[2][1].extend(k for k in TERMS if k not in _named)


def _hod(n):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return "ход"
    return "хода" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else "ходов"


def word(key, val):
    """A term said in words: its name, the number after it («каждые 3 хода», «на 2 хода», «на ∞» — до конца боя)."""
    nm = TERMS[key][0]
    if " N " in nm:
        if val and val.strip().isdigit():
            return nm.replace(" N ходов", " " + val + " " + _hod(val)).lower()
        if key == "на" and val == "∞":
            return "до конца боя"
        return nm.replace(" N ходов", "").lower() + (" " + val if val else "")
    return nm.lower() + (" " + val if val else "")


def words(line, names=None):
    """A line of terms read out in words, the terms in a row parted by «·» — for the Alt view. «{@key}» icons are
    named by names(key)."""
    out, last = [], None
    for part in parts(line):
        if part[0] == "t":
            t = part[1].strip()
            if t:
                out.append(t)
                last = "t"
            continue
        key, val = part[1], part[2]
        w = (names(key[1:]) if names else key[1:]) + (" " + val if val else "") if key.startswith("@") else word(key, val)
        if last == "g":
            out.append("·")
        out.append(w)
        last = "g"
    return " ".join(out)


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
    cols, cw, rh = 3, 660, 52
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
        dmg.rich_pil(img, d, x + 62, y + 26, what, fr, (214, 204, 220))
    img.save(out("fx_glossary.png"))
    print("fx_glossary.png", img.size)


if __name__ == "__main__":
    sheet()
