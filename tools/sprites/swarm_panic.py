"""Panic: a crushing blow from the Guard; the creatures next to it check fear; the frightened ones turn round and run
for the edge of the field with the fear sign over them, the crowd scattering; the dense middle holds — «Стая» gives
courage for every neighbour.

    python3 tools/sprites/swarm_panic.py      -> out/swarm_panic.gif, out/swarm_panic.png (key frames)
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
import swarm_effects as E
import swarm_fire as SF
import icons as IC
from paths import font, out

GY = SF.GY
GUARD_X = 446
# the swarm: (traits, soldier, seed, x, y, flees: (dx, dy) per frame or None)
SWARM = [
    ((), True, 1, 362, GY + 2, None),                          # the one the hammer hits
    ((), False, 2, 340, GY - 16, (-1.0, -0.55)), ((), False, 3, 344, GY + 20, (-1.0, 0.5)),
    (("stinger",), False, 4, 318, GY - 2, None), ((), False, 5, 300, GY - 22, (-1.0, -0.8)),
    (("horn",), False, 6, 300, GY + 14, None), ((), False, 7, 276, GY + 2, None), ((), False, 8, 264, GY - 18, None),
    (("acid",), False, 9, 252, GY + 20, None), ((), False, 10, 236, GY + 2, None), ((), False, 11, 214, GY - 14, None),
    ((), False, 12, 200, GY + 16, None), (("scythes",), False, 13, 384, GY - 26, (-1.0, -0.3)),
]


def fear_icon(sc, x, y):
    s = IC.icon("fear", 1, "swarm")
    sc.blit(s, int(x - s.ox), int(y - s.oy))


def dust(sc, x, y, seed):
    rnd = np.random.RandomState(seed)
    for _ in range(5):
        E.dot(sc, x + rnd.uniform(4, 16), y - rnd.uniform(0, 5), hexc("#5a4e46"), 0.7)


def frames():
    guard_idle, guard_hit = E.golem("Страж", "idle"), E.golem("Страж", "attack")
    texts = ["", "сокрушительный удар: соседи цели проверяют страх", "испугавшиеся разворачиваются и бегут к краю",
             "толпа рассыпается, плотная середина держится — Стая", "сбежавшие не дерутся, после победы вернутся"]
    seq = []
    for f in range(5):
        cast, over, under = [], [], []
        for i, (traits, soldier, seed, x, y, flee) in enumerate(SWARM):
            if i == 0:                                          # the crushed one flies back a cell
                if f == 0:
                    cast.append((E.bug(traits, "attack", soldier, seed=seed), x, y))
                elif f == 1:
                    cast.append((E.lit(E.bug(traits, "idle", soldier, seed=seed), (245, 245, 245), 0.7), x - 24, y - 4))
                    over.append(lambda sc, x=x: E.burst(sc, x - 10, GY - 16, 12))
                else:
                    cast.append((E.lit(E.bug(traits, "idle", soldier, seed=seed), (26, 18, 16), 0.7), x - 50, y + 2))
                continue
            if flee and f >= 1:
                if f == 1:                                      # it flinches; the fear sign comes up
                    cast.append((E.bug(traits, "idle", soldier, seed=seed), x, y))
                    over.append(lambda sc, x=x, y=y: fear_icon(sc, x, y - 26))
                    continue
                t = f - 1
                nx, ny = x + flee[0] * 70 * t, y + flee[1] * 30 * t
                if nx < 14:
                    continue                                   # off the field
                cast.append((E.mirror(E.bug(traits, "idle", soldier, seed=seed)), nx, ny))
                over.append(lambda sc, nx=nx, ny=ny: fear_icon(sc, nx, ny - 26))
                under.append(lambda sc, nx=nx, ny=ny, s=seed + f: dust(sc, nx, ny, s))
                continue
            pose = "attack" if (f in (0, 2, 3) and x > 260) else "idle"
            cast.append((E.bug(traits, pose, soldier, seed=seed), x + (6 if f >= 2 and x > 300 else 0), y))
        cast.append((guard_hit if f == 1 else guard_idle, GUARD_X, GY))
        seq.append(dict(cast=cast, fx=dict(over=over, under=under), text=texts[f], dur=900 if f in (1, 4) else 650))
    return seq


def render():
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 20)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 24)
    seq = frames()
    imgs = []
    for fr in seq:
        im = SF.draw(fr["cast"], fr["fx"], seed=27).image(2)
        if fr["text"]:
            d = ImageDraw.Draw(im)
            tw = d.textlength(fr["text"], font=fh)
            d.rectangle((20, 14, 20 + tw + 16, 46), fill=(20, 14, 26))
            d.text((28, 17), fr["text"], font=fh, fill=(244, 226, 180))
        imgs.append(im)
    W_, H_ = imgs[0].size
    frames_ = []
    for im in imgs:
        c = Image.new("RGB", (W_ + 24, H_ + 60), (24, 18, 30))
        ImageDraw.Draw(c).text((12, 12), "Паника: испугавшиеся бегут к краю поля", font=ft, fill=(236, 214, 160))
        c.paste(im, (12, 48))
        frames_.append(c)
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames_]
    pal[0].save(out("swarm_panic.gif"), save_all=True, append_images=pal[1:], duration=[f["dur"] for f in seq], loop=0,
                disposal=2, optimize=False)
    keys = [1, 2, 3]
    s = 0.62
    kw, kh = int(W_ * s), int(H_ * s)
    sheet = Image.new("RGB", (len(keys) * (kw + 10) + 10, kh + 64), (24, 18, 30))
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), "Паника: испугавшиеся бегут к краю поля", font=ft, fill=(236, 214, 160))
    for j, k in enumerate(keys):
        sheet.paste(imgs[k].resize((kw, kh), Image.NEAREST), (10 + j * (kw + 10), 50))
    sheet.save(out("swarm_panic.png"))
    print("swarm_panic.gif", frames_[0].size, len(frames_), "frames; swarm_panic.png", sheet.size)


if __name__ == "__main__":
    render()
