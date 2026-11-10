"""Running torches: the Gorn's flame catches the swarm's front; the burning small creatures panic and run back
through their own, setting alight everyone they brush past; a burning wasp falls and sets its cell burning; the
fireproof golem stands in the blaze. The general fire rules (see the concept, «Огонь») as the swarm meets them.

    python3 tools/sprites/swarm_fire.py      -> out/swarm_fire.gif, out/swarm_fire.png (key frames)
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
import swarm_effects as E
from battle import shadow
from animate_duel import background
from paths import font, out

PW, PH, GY = 520, 214, 176
FIRE = [hexc("#7a1e08"), hexc("#d2480e"), hexc("#f08a20"), hexc("#ffc850"), hexc("#fff4c0")]
CHAR = (26, 18, 16)
GORN_X = 452

# the swarm: (traits, soldier, seed, x, y)
SWARM = [((), False, 1, 356, GY - 10), ((), False, 2, 362, GY + 14), (("stinger",), False, 3, 340, GY + 2),
         ((), False, 4, 300, GY - 18), (("horn",), False, 5, 296, GY + 8), ((), True, 6, 262, GY - 4),
         ((), False, 7, 230, GY + 16), (("acid",), False, 8, 214, GY - 16), ((), False, 9, 176, GY + 4),
         (("scythes",), False, 10, 150, GY - 12), ((), False, 11, 120, GY + 14), (("jumper",), False, 12, 96, GY - 4)]
WASP = (("wings",), False, 13)


def flame(sc, x, y, h, seed, k=1.0):
    """Tongues of fire standing on (x, y), about h tall."""
    rnd = np.random.RandomState(seed)
    for i in range(4):
        dx = rnd.uniform(-h * 0.35, h * 0.35)
        hh = h * rnd.uniform(0.55, 1.0) * k
        cx, cy = x + dx, y - hh * 0.5
        for j, (sx, sy, col) in enumerate(((0.38, 0.55, FIRE[1]), (0.28, 0.42, FIRE[2]), (0.17, 0.3, FIRE[3]), (0.08, 0.16, FIRE[4]))):
            e = ((sc.xx - cx) / max(1.0, hh * sx)) ** 2 + ((sc.yy - (cy + hh * 0.18 * j)) / max(1.0, hh * sy)) ** 2
            sel = e <= 1
            sc.rgb[sel] = col
    sc.glow(x, y - h * 0.4, h * 2.2, FIRE[2], 0.55 * k)


def ground_fire(sc, x, y, w, seed):
    th = BAYER[sc.yy % 4, sc.xx % 4]
    e = ((sc.xx - x) / w) ** 2 + ((sc.yy - y) / (w * 0.28)) ** 2
    sel = (e <= 1) & (th < 0.6)
    sc.rgb[sel] = sc.rgb[sel] * 0.4 + FIRE[0] * 0.6
    rnd = np.random.RandomState(seed)
    for i in range(3):
        flame(sc, x + rnd.uniform(-w * 0.6, w * 0.6), y + rnd.uniform(-2, 2), rnd.uniform(7, 12), seed * 7 + i, 0.8)


def draw(cast, fx, seed=21):
    sc = Scene(PW, PH)
    sc.rgb[:] = background(PW, PH, seed).rgb
    for c in range(0, 12):
        x = int(20 + c * E.CW)
        if 0 <= x < PW:
            sc.rgb[:, x] *= 0.92
    for f in fx.get("under", []):
        f(sc)
    for spr, x, y, *opt in sorted(cast, key=lambda c: (len(c) > 3 and c[3] == "air", c[2])):
        if not (opt and opt[0] == "air"):
            shadow(sc, x, y, max(10, spr.w * 0.6), 5)
        sc.blit(spr, int(round(x - spr.ox)), int(round(y - spr.oy)))
    for f in fx.get("over", []):
        f(sc)
    return sc


def frames():
    """Six moments; for each, who burns, where everyone is, what is on fire."""
    gorn_idle, gorn_fire = E.golem("Горн", "idle"), E.golem("Горн", "attack")
    seq = []
    # where the burning ones run: back through the swarm, a little zigzag
    burning0 = {0, 1, 2}
    runs = {0: [356, 300, 236, 160, 90], 1: [362, 318, 250, 186, 118], 2: [340, 282, 214, 148, 74]}
    catches = {1: set(), 2: {3, 4}, 3: {6, 7}, 4: {9}}                 # who the runners set alight, frame by frame
    wasp_y = [GY - 60, GY - 60, GY - 60, GY - 30, GY - 4, GY - 4]
    lit_set = set()
    texts = ["", "огонь по мелочи", "горящие бегут прочь — сквозь своих", "и поджигают всех, мимо кого бегут",
             "горящая оса падает и поджигает клетку", "Горн огнеупорен и стоит в пожаре"]
    patches = []
    for f in range(6):
        cast, over, under = [], [], []
        if f == 1:
            lit_set |= burning0
        lit_set |= catches.get(f, set())
        for i, (traits, soldier, seed, x, y) in enumerate(SWARM):
            b = E.bug(traits, "idle", soldier, seed=seed)
            if i in burning0 and f >= 2:                                      # the runners, turned round
                x = runs[i][min(f - 1, 4)]
                y = y + (6 if f % 2 else -6) * (i - 1) * 0.5
                spr = E.mirror(E.lit(b, FIRE[2], 0.35))
                if f == 5:
                    spr = E.lit(b, CHAR, 0.75)
                    y += 3
                cast.append((spr, x, y))
                if f < 5:
                    over.append(lambda sc, x=x, y=y, i=i, f=f: flame(sc, x - 2, y - 10, 15, i * 13 + f))
                    under.append(lambda sc, x=x, y=y, i=i, f=f: [E.dot(sc, x + 10 + k * 6, y - 2 - (k % 2) * 3, FIRE[2], r=1)
                                                               for k in range(5)])
                    patches.append((x + 14, y + 2))
                continue
            if i in lit_set and i not in burning0:
                spr = E.mirror(E.lit(b, FIRE[2], 0.35)) if f < 5 else E.lit(b, CHAR, 0.7)
                dx = -18 * (f - min(k for k, v in catches.items() if i in v)) if f < 5 else -40
                cast.append((spr, x + dx, y))
                if f < 5:
                    over.append(lambda sc, x=x + dx, y=y, i=i, f=f: flame(sc, x - 2, y - 10, 13, i * 17 + f))
                continue
            if f == 1 and i in burning0:
                cast.append((E.lit(b, FIRE[2], 0.4), x, y))
                over.append(lambda sc, x=x, y=y, i=i: flame(sc, x, y - 8, 14, i * 5))
                continue
            pose = "attack" if f == 0 and i < 5 else "idle"
            spr = E.bug(traits, pose, soldier, seed=seed)
            if f >= 3 and x < 300 and i % 3 == 0:
                spr = E.mirror(spr)                                           # the swarm shies from the fire
            cast.append((spr, x + (0 if f < 3 else -6), y))
        # the burning wasp
        wx = 250 - 6 * f
        wasp = E.bug(WASP[0], "idle", WASP[1], seed=WASP[2])
        if f >= 2:
            wasp = E.lit(wasp, FIRE[2], 0.35) if f < 5 else E.lit(wasp, CHAR, 0.7)
        cast.append((wasp, wx, wasp_y[f], "air") if f < 4 else (wasp, wx, wasp_y[f]))
        if 2 <= f < 5:
            over.append(lambda sc, wx=wx, f=f: flame(sc, wx, wasp_y[f] - 12, 14, 90 + f))
        if f >= 4:
            under.append(lambda sc, wx=wx: ground_fire(sc, wx, GY, 26, 7))
        for (px, py) in patches[-9:] if f >= 3 else []:
            under.append(lambda sc, px=px, py=py: ground_fire(sc, px, py, 12, int(px)))
        cast.append((gorn_fire if f == 1 else gorn_idle, GORN_X, GY))
        if f == 5:
            under.append(lambda sc: ground_fire(sc, GORN_X - 6, GY + 2, 34, 3))
        seq.append(dict(cast=cast, fx=dict(over=over, under=under), text=texts[f], dur=700 if f in (1, 5) else 520))
    return seq


def render():
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 20)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 24)
    seq = frames()
    imgs = []
    for fr in seq:
        im = draw(fr["cast"], fr["fx"]).image(2)
        if fr["text"]:
            d = ImageDraw.Draw(im)
            tw = d.textlength(fr["text"], font=fh)
            d.rectangle((20, 14, 20 + tw + 16, 46), fill=(20, 14, 26))
            d.text((28, 17), fr["text"], font=fh, fill=(244, 226, 180))
        imgs.append(im)
    W_, H_ = imgs[0].size
    frames_ = []
    for im in imgs:
        canvas_ = Image.new("RGB", (W_ + 24, H_ + 60), (24, 18, 30))
        d = ImageDraw.Draw(canvas_)
        d.text((12, 12), "Бегущие факелы: огонь против роя", font=ft, fill=(236, 214, 160))
        canvas_.paste(im, (12, 48))
        frames_.append(canvas_)
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames_]
    pal[0].save(out("swarm_fire.gif"), save_all=True, append_images=pal[1:], duration=[f["dur"] for f in seq], loop=0,
                disposal=2, optimize=False)
    # the key frames side by side
    keys = [1, 3, 5]
    s = 0.62
    kw, kh = int(W_ * s), int(H_ * s)
    sheet = Image.new("RGB", (len(keys) * (kw + 10) + 10, kh + 64), (24, 18, 30))
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), "Бегущие факелы: огонь против роя", font=ft, fill=(236, 214, 160))
    for j, k in enumerate(keys):
        sheet.paste(imgs[k].resize((kw, kh), Image.NEAREST), (10 + j * (kw + 10), 50))
    sheet.save(out("swarm_fire.png"))
    print("swarm_fire.gif", frames_[0].size, len(frames_), "frames; swarm_fire.png", sheet.size)


if __name__ == "__main__":
    render()
