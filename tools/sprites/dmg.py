"""Damage-type icons: one small pixel glyph per type, put into the text wherever a type is named, instead of the word.
In a string a type is written as a token — "{кол}", "{руб}", "{дроб}", "{огонь}", "{молния}", "{холод}", "{яд}",
"{кисл}", "{пси}" — and the text renderers (swarm_ui.rich for the hand-made screens, rich_pil for the sheets) draw
the glyph in its place. The glyphs are drawn in colour only; the dark outline is added around them.

    python3 tools/sprites/dmg.py      -> out/dmg_types.png
"""
import re
import numpy as np
from PIL import Image
from kit import *

OUT = hexc("#140c18")
C = dict(W=hexc("#fff8e8"), i=hexc("#c8d0dc"), I=hexc("#7a8494"), T=hexc("#8a5a30"), t=hexc("#c89058"),
         R=hexc("#d0301e"), A=hexc("#f08a20"), a=hexc("#ffc850"), y=hexc("#fff4a0"),
         b=hexc("#8ad8ff"), B=hexc("#3a8ae0"), V=hexc("#62b832"), g=hexc("#c8f08a"), k=hexc("#1a2a10"),
         J=hexc("#c0e030"), j=hexc("#f4ffa8"), P=hexc("#9a60e0"), p=hexc("#e6d2ff"), K=hexc("#2a1440"))

GLYPHS = {   # key: (name, rows)
    "кол": ("колющий", ["........i....",
                        "........Wi...",
                        "I.......WWi..",
                        "II.....tWWWi.",
                        ".ITTTTTTWWWWi",
                        "II.....tWWWi.",
                        "I.......WWi..",
                        "........Wi...",
                        "........i...."]),
    "руб": ("рубящий", ["..........Wi",
                        ".........WWi",
                        "........WWi.",
                        ".......WWi..",
                        "......WWi...",
                        ".....WWi....",
                        "....WWi.....",
                        ".A.WWi......",
                        "..AAi.......",
                        "..tAA.......",
                        ".t..A.......",
                        "t..........."]),
    "дроб": ("дробящий", [".iWWiiiiI..",
                          "iWWiiiiiII.",
                          "iWiiiiiiIII",
                          "iiiiiiiIIII",
                          ".IIIIIIIII.",
                          "....tT.....",
                          "....tT.....",
                          "....tT.....",
                          "....tT.....",
                          "....tT.....",
                          "....TT....."]),
    "огонь": ("огонь", [".....R.....",
                        "....RR.....",
                        "....RAR..R.",
                        "...RAAR..R.",
                        "..RAAaR.RR.",
                        ".RAAaaARAR.",
                        ".RAaaaAAAR.",
                        "RAaayaaAAR.",
                        "RAayyyaAAR.",
                        "RAayyyaaAR.",
                        ".RAaaaaAR..",
                        "..RRRRRR..."]),
    "молния": ("молния", ["....bbbbb",
                          "...bWWWb.",
                          "...bWWb..",
                          "..bWWb...",
                          "..bWWbbbb",
                          ".bWWWWWWb",
                          ".bbbbWWb.",
                          "....bWb..",
                          "...bWb...",
                          "..bWb....",
                          "..bb.....",
                          ".b......."]),
    "холод": ("холод", ["b....b....b",
                        ".b...b...b.",
                        "..b..W..b..",
                        "...bWbWb...",
                        "....bWb....",
                        "bbWWWWWWWbb",
                        "....bWb....",
                        "...bWbWb...",
                        "..b..W..b..",
                        ".b...b...b.",
                        "b....b....b"]),
    "яд": ("яд", ["....g....",
                  "....V....",
                  "...VVV...",
                  "..VgVVV..",
                  ".VgVVVVV.",
                  ".VVVVVVV.",
                  "VVkkVkkVV",
                  "VVkkVkkVV",
                  "VVVVVVVVV",
                  ".VVkVkVV.",
                  "..VVVVV..",
                  "...VVV..."]),
    "кисл": ("кислота", ["..j.....j..",
                         "......j....",
                         "....J......",
                         "...JjJ.....",
                         "..JjJJJ....",
                         "..JJJJJ....",
                         "...JJJ.....",
                         "........j..",
                         ".j..j......",
                         "VJVJVJVJVJ.",
                         "JVjVJVJjVJV",
                         ".VJVJVJVJV."]),
    "пси": ("пси", ["...PPPPP...",
                    ".PPpppppPP.",
                    "PppPPPPPppP",
                    "PpPPKKKPPpP",
                    "PpPKKpKKPpP",
                    "PpPPKKKPPpP",
                    "PppPPPPPppP",
                    ".PPpppppPP.",
                    "...PPPPP..."]),
}
TOKEN = re.compile(r"\{(\w+)\}")
H = 9            # glyph box height, before the outline


def rgba(key):
    """The glyph with its outline as an RGBA array (1 px = 1 px)."""
    rows = GLYPHS[key][1]
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


def width(key, z=1):
    return rgba(key).shape[1] * z


def draw(sc, key, x, y, z=1):
    """Into a Scene: top-left at (x, y)."""
    a = rgba(key)
    for j in range(a.shape[0]):
        for i in range(a.shape[1]):
            if a[j, i, 3]:
                ys, xs = int(y) + j * z, int(x) + i * z
                if 0 <= ys and ys + z <= sc.h and 0 <= xs and xs + z <= sc.w:
                    sc.rgb[ys:ys + z, xs:xs + z] = a[j, i, :3]
                    sc.occ[ys:ys + z, xs:xs + z] = True
    return a.shape[1] * z


def pil(key, z):
    a = rgba(key)
    return Image.fromarray(a, "RGBA").resize((a.shape[1] * z, a.shape[0] * z), Image.NEAREST)


def parts(text):
    """The text split into words and glyphs: [("t", "текст"), ("g", "кол"), ...]."""
    out, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out.append(("t", text[pos:m.start()]))
        out.append(("g", m.group(1)))
        pos = m.end()
    if pos < len(text):
        out.append(("t", text[pos:]))
    return out


def plain(text):
    """The text with each glyph spelled out (for places that can only take words)."""
    return TOKEN.sub(lambda m: GLYPHS[m.group(1)][0], text)


# ---------------------------------------------------------------- PIL text with glyphs (the sheets)
def zoom(fnt):
    return max(1, round(fnt.size / 14))


def width_pil(d, text, fnt):
    z = zoom(fnt)
    return sum(d.textlength(s, font=fnt) if k == "t" else width(s, z) + 2 * z for k, s in parts(text))


def rich_pil(img, d, x, y, text, fnt, fill, anchor="left"):
    """Draws text with glyphs at (x, y) — the text's top; anchor 'left' or 'center'. Returns the width."""
    z = zoom(fnt)
    w = width_pil(d, text, fnt)
    if anchor == "center":
        x -= w / 2
    for k, s in parts(text):
        if k == "t":
            d.text((x, y), s, font=fnt, fill=fill)
            x += d.textlength(s, font=fnt)
        else:
            g = pil(s, z)
            img.paste(g, (int(x + z), int(y + fnt.size * 0.5 - g.height / 2 + z)), g)
            x += g.width + 2 * z
    return w


def wrap_pil(d, text, fnt, maxw):
    words, lines, cur = text.split(" "), [], ""
    for wd in words:
        if width_pil(d, (cur + " " + wd).strip(), fnt) > maxw and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    return lines + [cur]


def sheet():
    from PIL import ImageDraw, ImageFont
    from paths import font, out
    keys = list(GLYPHS)
    S_ = 6
    img = Image.new("RGB", (len(keys) * 120 + 20, 150), (24, 18, 30))
    d = ImageDraw.Draw(img)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 18)
    for i, k in enumerate(keys):
        g = pil(k, S_)
        x = 20 + i * 120 + (100 - g.width) // 2
        img.paste(g, (x, 20 + (66 - g.height) // 2), g)
        name = GLYPHS[k][0]
        d.text((20 + i * 120 + 50 - d.textlength(name, font=fr) / 2, 100), name, font=fr, fill=(236, 224, 196))
    img.save(out("dmg_types.png"))
    print("dmg_types.png", img.size)


if __name__ == "__main__":
    sheet()
