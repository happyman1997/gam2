"""States over units on the battlefield, one set for every effect the swarm puts on its enemies (and a few on itself):
a small pixel glyph over the head, at the battle's own scale, sometimes something at the feet or on the body.
Glyphs stack left to right; the psi pile-up (Надлом) is a row of diamonds above them.

    python3 tools/sprites/swarm_status.py      -> out/swarm_status.png
"""
import numpy as np
from kit import *

OUT = hexc("#140c18")
C = dict(o=OUT, G=hexc("#7ab040"), g=hexc("#cce890"), d=hexc("#2a3a14"), w=hexc("#ece0c4"), k=hexc("#1a120c"),
         P=hexc("#9a60e0"), p=hexc("#e6d2ff"), W=hexc("#fff4dc"), Y=hexc("#e8c040"), y=hexc("#fff0a0"),
         A=hexc("#e09020"), a=hexc("#ffd070"), R=hexc("#d02a1e"), r=hexc("#ff8a6a"), S=hexc("#e8e0d0"),
         B=hexc("#70c8ff"), b=hexc("#e0f6ff"), I=hexc("#6a7280"), i=hexc("#b0b8c4"), V=hexc("#9ae030"))

GLYPHS = {
    "infected": ["...ooo...",
                 "..oGGGo..",
                 ".oGgGGGo.",
                 ".oGGGdGo.",
                 "oGdGGGGGo",
                 "oGGGgGdGo",
                 "oGGdGGGGo",
                 ".oGGGGGo.",
                 "..ooooo.."],
    "hatching": ["..o...o..",
                 ".oGo.oGo.",
                 ".oGGoGGo.",
                 "oGwwwwwGo",
                 "oGwkwwwGo",
                 "oGGwwwGGo",
                 "oGGGGGGGo",
                 ".oGGGGGo.",
                 "..ooooo.."],
    "broken": ["....oo...",
               "...oPPo..",
               "..oPpo...",
               ".oPPPPo..",
               "..ooPpo..",
               "...oPo...",
               "..oPo....",
               ".oPo.....",
               "..o......"],
    "fear": [".oo..oo.",
             "oWWooWWo",
             "oWWooWWo",
             "oWWooWWo",
             "oWWooWWo",
             ".oo..oo.",
             "oWWooWWo",
             ".oo..oo."],
    "glued": ["...oo....",
              "..oYYo...",
              ".oYyYYo..",
              ".oYYYYo..",
              "oYYYYYYo.",
              "oYyYYYYo.",
              ".oYYYYo..",
              "..oooo...",
              "........."],
    "web": ["o...o...o",
            ".oS.S.So.",
            "..oSSSo..",
            "oSSoSoSSo",
            "..oSSSo..",
            ".oS.S.So.",
            "o...o...o"],
    "honey": ["...oo....",
              "..oAAo...",
              ".oAaAAo..",
              "oAAAAAAo.",
              "oAaAAAAo.",
              "oAAAAAAo.",
              ".oAAAAo..",
              "..oooo..."],
    "blister": [".ooo...ooo.",
               "oRrRo..oWo.",
               "oRRRo..oWo.",
               "oRRRo.ooWoo",
               ".ooo..oWWWo",
               ".......oWo.",
               "........o.."],
    "captured": ["..ooooo..",
                 ".oPPPPPo.",
                 "oPPpppPPo",
                 "oPpkkkpPo",
                 "oPPpppPPo",
                 ".oPPPPPo.",
                 "..ooooo.."],
    "stall": ["....ooo",
             "...oBbo",
             "..oBBo.",
             ".oBbBBo",
             "..oBBo.",
             ".oBBo..",
             "oBbo...",
             "ooo...."],
    "confused": ["..oooo...",
                 ".oPPPPo..",
                 "oPooooPo.",
                 "oPoPPoPo.",
                 "oPoPooPo.",
                 "oPooPPo..",
                 ".oPo.oo..",
                 "..oPPPo..",
                 "...ooo..."],
    "shred": ["ooooooo",
              "oIiIoIo",
              "oIIoIIo",
              "oIoIIIo",
              ".oIoIo.",
              "..oIo..",
              "...o..."],
    "poison": ["...o....",
               "..oVo...",
               ".oVVVo..",
               "oVVgVVo.",
               "oVVVVVo.",
               ".oVVVo.o",
               "..ooo.oVo",
               "......oo."],
    "frenzy": [".ooooo..",
               "oRrRRRo.",
               ".oRRRo..",
               "..oRRo..",
               "..oRo...",
               "...oRo..",
               "....o...",
               "........"],
    "heal": ["..ooo..",
             "..oVo..",
             "oooVooo",
             "oVVVVVo",
             "oooVooo",
             "..oVo..",
             "..ooo.."],
}

# key: (name, what it means, who it falls on)
STATES = [
    ("infected", "Заражён", "в нём кладка: погибнув, выпустит личинок", "Кукушка"),
    ("hatching", "Кладка зреет", "личинки вот-вот выйдут — из живого (Яйца в крови)", "Кукушка"),
    ("nadlom", "Надлом", "ромбы — накопленный пси; полный ряд — раунд не действует", "Разум улья"),
    ("confused", "Помутнение", "раунд путает цели; машина сбоит", "Разум улья"),
    ("captured", "Захвачен", "бьётся за рой; кольцо гаснет, когда время выходит", "Разум улья"),
    ("fear", "Испуг", "бежит к краю поля", "страх"),
    ("stall", "Сбой", "у машины: шаг пропущен, способности молчат", "машины"),
    ("glued", "Склеен", "раунд не ходит и не бьёт", "Взрывной муравей"),
    ("web", "В паутине", "застрял на раунд", "Прядильные железы"),
    ("honey", "В мёде", "вязнет", "Медовая бочка"),
    ("blister", "Ожог", "его удар слабее до конца боя", "Нарывник"),
    ("shred", "Броня разъедена", "минус броня до конца боя", "скорпион, кислота"),
    ("poison", "Яд", "копится и выходит каждый раунд", "жало"),
    ("frenzy", "Кормовое безумие", "своя особь бьёт сильнее, пока Пожиратель ест", "свои"),
    ("heal", "Лечится", "мёд, стол Пожирателя, Живучая", "свои"),
]
GROUND = {"glued", "web", "honey"}


def glyph(sc, key, cx, top, z=1):
    rows = GLYPHS[key]
    h, w = len(rows), len(rows[0])
    x0, y0 = int(round(cx - w * z / 2)), int(round(top))
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            ys, xs = y0 + j * z, x0 + i * z
            if 0 <= ys and ys + z <= sc.h and 0 <= xs and xs + z <= sc.w:
                sc.rgb[ys:ys + z, xs:xs + z] = C[ch]
    return w * z, h * z


def pips(sc, cx, y, n, of=4, z=1):
    """The psi pile: a row of diamonds, n of them lit."""
    for i in range(of):
        x = cx + (i - (of - 1) / 2) * 6 * z
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                d = abs(dx) + abs(dy)
                if d > 2:
                    continue
                col = OUT if d == 2 else (C["P"] if i < n else hexc("#3a2a52"))
                if d == 0 and i < n:
                    col = C["p"]
                xs, ys = int(x + dx * z), int(y + dy * z)
                sc.rgb[ys:ys + z, xs:xs + z] = col
        if i < n:
            sc.glow(x, y, 5 * z, C["P"], 0.25)


def top_of(spr, by):
    rows = np.nonzero(spr.a.any(axis=1))[0]
    return by - spr.oy + rows.min()


def ground(sc, key, x, by, w=26):
    rnd = np.random.RandomState(len(key))
    if key == "glued":
        for _ in range(9):
            px, py = x + rnd.uniform(-w * 0.6, w * 0.6), by + rnd.uniform(-2, 3)
            for dx in range(-2, 3):
                for dy in range(-1, 2):
                    sc.rgb[int(py + dy), int(px + dx)] = C["Y"] if (dx + dy) % 3 else C["y"]
        sc.glow(x, by, w, C["Y"], 0.3)
    elif key == "web":
        for r in (0.35, 0.7, 1.0):
            for t in np.linspace(0, 2 * np.pi, int(40 * r) + 8):
                sc.rgb[int(by + np.sin(t) * w * 0.3 * r), int(x + np.cos(t) * w * r)] = C["S"] * 0.85
        for t in np.linspace(0, np.pi * 2, 9)[:-1]:
            for f in np.linspace(0, 1, 18):
                sc.rgb[int(by + np.sin(t) * w * 0.3 * f), int(x + np.cos(t) * w * f)] = C["S"] * 0.85
    elif key == "honey":
        e = ((sc.xx - x) / (w * 1.05)) ** 2 + ((sc.yy - by - 1) / (w * 0.28)) ** 2
        th = BAYER[sc.yy % 4, sc.xx % 4]
        sel = (e <= 1) & (th < 0.8)
        sc.rgb[sel] = sc.rgb[sel] * 0.25 + C["A"] * 0.75
        sc.glow(x, by, w, C["A"], 0.3)


def on_body(sc, spr, x, by, key, seed=0):
    """Marks on the body itself: infection spots, a violet tint for the captured, a dim core for a stalled machine."""
    rnd = np.random.RandomState(seed)
    ys, xs = np.nonzero(spr.a)
    X0, Y0 = int(x - spr.ox), int(by - spr.oy)
    if key in ("infected", "hatching"):
        sel = rnd.choice(len(ys), size=min(9, len(ys)), replace=False)
        for s_ in sel:
            sc.rgb[Y0 + ys[s_], X0 + xs[s_]] = C["V"]
            sc.glow(X0 + xs[s_], Y0 + ys[s_], 3, C["V"], 0.2)
    if key == "captured":
        sc.rgb[Y0 + ys, X0 + xs] = sc.rgb[Y0 + ys, X0 + xs] * 0.7 + C["P"] * 0.3
    if key == "stall":
        sc.rgb[Y0 + ys, X0 + xs] = sc.rgb[Y0 + ys, X0 + xs] * 0.72
    if key == "frenzy":
        sc.rgb[Y0 + ys, X0 + xs] = sc.rgb[Y0 + ys, X0 + xs] * 0.8 + C["R"] * 0.2


def unit(sc, spr, x, by, states=(), psi=None, seed=0, shadow=True):
    """A unit with its states: ground marks, the body, marks on the body, glyphs over the head, the psi row."""
    for k_ in states:
        if k_ in GROUND:
            ground(sc, k_, x, by, w=max(14, spr.w * 0.36))
    if shadow:
        e = ((sc.xx - x) / max(6, spr.w * 0.3)) ** 2 + ((sc.yy - by) / 3.5) ** 2
        sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(x - spr.ox), int(by - spr.oy))
    for k_ in states:
        on_body(sc, spr, x, by, k_, seed)
    top = top_of(spr, by)
    gl = [k_ for k_ in states if k_ in GLYPHS and k_ != "nadlom"]
    if psi is not None and psi >= 4:
        gl = ["broken"] + gl
    widths = [len(GLYPHS[k_][0]) + 2 for k_ in gl]
    cx = x - sum(widths) / 2
    gy = top - 12
    for k_, w_ in zip(gl, widths):
        glyph(sc, k_, cx + w_ / 2, gy)
        cx += w_
    if "captured" in states:
        for t in np.linspace(0, 2 * np.pi, 40):
            sc.rgb[int(top - 2 + np.sin(t) * 2), int(x + np.cos(t) * 8)] = C["P"]
        sc.glow(x, top - 2, 10, C["P"], 0.3)
    if psi is not None and psi < 4:
        pips(sc, x, (gy - 5) if gl else (top - 6), psi)
    if psi is not None and psi >= 4:
        for i in range(3):
            a_ = i * 2.1 + 0.4
            px, py = x + np.cos(a_) * 11, top - 4 + np.sin(a_) * 3
            sc.rgb[int(py), int(px)] = C["p"]
            sc.glow(px, py, 4, C["P"], 0.3)


# ------------------------------------------------------------------ the sheet
def sheet():
    from PIL import ImageFont
    from leaders_sheet import canvas, fonts, S, GOLD, INK, MUT
    from paths import out, font
    import swarm_mut as SM
    SM.Z = 1.3
    hum = SM.man()
    gol = SM.golem()
    bug = SM.bug((), "attack", seed=3)
    WW, CW_, RH = 960, 192, 150
    cols = 5
    rows_ = (len(STATES) + cols - 1) // cols
    top0 = 78
    HH = top0 + rows_ * RH + 190
    sc = canvas(WW, HH, 77)
    for n, (key, name, what, who) in enumerate(STATES):
        cx, by = 16 + CW_ / 2 + (n % cols) * CW_, top0 + (n // cols) * RH + 96
        if key == "nadlom":
            glyph(sc, "broken", cx - 64, by - 78, z=3)
            pips(sc, cx - 64, by - 36, 3, z=2)
        else:
            glyph(sc, key, cx - 64, by - 78, z=4)
        if key in ("frenzy", "heal"):
            unit(sc, bug, cx + 24, by, (key,))
        elif key in ("stall", "shred"):
            unit(sc, gol, cx + 24, by, (key,), seed=n)
        elif key == "nadlom":
            unit(sc, hum, cx + 6, by, (), psi=2)
            unit(sc, hum, cx + 48, by, (), psi=4)
        else:
            unit(sc, hum, cx + 24, by, (key,), seed=n)
    # stacking: several states at once, and the psi row filling up
    yb = top0 + rows_ * RH + 120
    unit(sc, gol, 150, yb, ("infected", "shred", "stall"), seed=2)
    unit(sc, hum, 320, yb, ("glued", "fear", "poison"), psi=3, seed=4)
    unit(sc, hum, 470, yb, ("captured",), seed=5)
    for i in range(5):
        unit(sc, hum, 600 + i * 66, yb, (), psi=i, seed=6)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    small = ImageFont.truetype(font("PTSerif-Regular.ttf"), 14)
    d.text((24, 16), "Рой: состояния на поле", font=ft, fill=INK)
    d.text((24, 60), "Значок над головой в масштабе поля, кое-где ещё след у ног или на теле. Значки встают в ряд; "
                     "ромбы пси — над ними.", font=fr, fill=MUT)
    for n, (key, name, what, who) in enumerate(STATES):
        cx, by = 16 + CW_ / 2 + (n % cols) * CW_, top0 + (n // cols) * RH + 96
        d.text(((cx - CW_ / 2 + 8) * S, (by + 8) * S), name, font=fbs, fill=GOLD)
        d.text(((cx - CW_ / 2 + 8) * S + d.textlength(name, font=fbs) + 10, (by + 8) * S + 2), who, font=small, fill=MUT)
        words, lines, cur = what.split(" "), [], ""
        for wd in words:
            if d.textlength(cur + " " + wd, font=small) > (CW_ - 16) * S and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for k_, ln in enumerate(lines[:2]):
            d.text(((cx - CW_ / 2 + 8) * S, (by + 8) * S + 24 + k_ * 18), ln, font=small, fill=INK)
    d.text((24, (yb - 96) * S), "Сразу несколько: значки в ряд, ромбы пси над ними; ряд ромбов заполняется — и надлом",
           font=fh, fill=GOLD)
    caps = [(150, "заражён, броня, сбой"), (320, "склеен, испуг, яд, пси 3"), (470, "захвачен")] + \
           [(600 + i * 66, f"пси {i}" if i < 4 else "надлом") for i in range(5)]
    for x, c in caps:
        d.text((x * S - d.textlength(c, font=small) / 2, (yb + 10) * S), c, font=small, fill=INK)
    img.save(out("swarm_status.png"))
    print("swarm_status.png", img.size)


if __name__ == "__main__":
    sheet()
