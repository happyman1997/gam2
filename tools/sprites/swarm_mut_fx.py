"""The most visible mutations, animated in the battle's own scale (zoomed, as swarm_effects): the web, the glue, the bolas,
the midge cloud, the cocoon, the psi break (Надлом), the spores, the larvae from a living host.

    python3 tools/sprites/swarm_mut_fx.py      -> out/swarm_mut_fx.gif, out/swarm_mut_fx.png
"""
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
import swarm1 as W
import swarm_effects as E
import swarm_status as ST
import swarm_abilities as SA
import swarm_leaders as SL
from swarm_effects import X, GY, frame, burst, splash, drops, ring, lines, lit, golem, human, arc_pts, trail, dot, speed
from paths import font, out

SILK_C, GLUE, PSI_C, SPORE, GREEN = hexc("#e8e0d0"), hexc("#e8c840"), hexc("#c8a0ff"), hexc("#f09040"), hexc("#9ae030")


@lru_cache(maxsize=None)
def mb(traits=(), pose="idle", key=None, seed=1, soldier=False):
    return W.build(traits, 0.0, pose, soldier, k=E.Z, genes=W.genes_for(seed), rare=key)


@lru_cache(maxsize=None)
def larva(pose="attack", host=None):
    return SL.build("личинка", pose, E.Z, host=host)


@lru_cache(maxsize=None)
def cocoon():
    import swarm_mut as SM
    SM.Z = E.Z
    return SM.cocoon()


def mark(spr, x, y, key):
    return lambda sc: ST.glyph(sc, key, x, ST.top_of(spr, y) - 12)


def web(sc, x, y, r):
    for f in (0.35, 0.7, 1.0):
        if f * 46 <= r + 1:
            ring(sc, x, y, 46 * f, SILK_C, 0.6, ry=12 * f)
    for t in np.linspace(0, 2 * np.pi, 9)[:-1]:
        lines(sc, (x, y), (x + np.cos(t) * min(r, 46), y + np.sin(t) * min(r, 46) * 0.26), SILK_C, 0.6)


def cloud(sc, x, y, rx, ry, seed, col=hexc("#3a3046"), n=120):
    rnd = np.random.RandomState(seed)
    for _ in range(n):
        a, r = rnd.uniform(0, 2 * np.pi), np.sqrt(rnd.uniform(0, 1))
        dot(sc, x + np.cos(a) * rx * r, y + np.sin(a) * ry * r, col)
    for _ in range(n // 3):
        a, r = rnd.uniform(0, 2 * np.pi), np.sqrt(rnd.uniform(0, 1))
        dot(sc, x + np.cos(a) * rx * r, y + np.sin(a) * ry * r, hexc("#9a92b4"))


# ---------------------------------------------------------------- the sequences
def spinner():
    g = golem("Механик")
    b = lambda p: mb((), p, "spinner", 5)
    w = lambda r: (lambda sc: web(sc, X(1.7), GY + 4, r))
    return [frame([(b("idle"), X(0.5), GY), (g, X(3.0), GY)]),
            frame([(b("attack"), X(0.6), GY), (g, X(2.8), GY)], fx=[w(18), lambda sc: lines(sc, (X(0.2), GY - 10), (X(1.5), GY + 2), SILK_C)],
                  text=[(X(1.6), 22, "плетёт — в этот раунд не бьёт")]),
            frame([(b("idle"), X(0.5), GY), (g, X(2.1), GY)], fx=[w(46)], text=[(X(1.6), 22, "паутина до конца боя")]),
            frame([(b("idle"), X(0.5), GY), (g, X(1.8), GY), (mb((), "attack", None, 6), X(1.2), GY + 10)],
                  fx=[w(46), mark(g, X(1.8), GY, "web")], text=[(X(1.6), 22, "враг застрял; свои бегают свободно")], key=True)]


def exploder():
    g = golem("Механик")
    ga = golem("Механик", "attack")
    b = mb((), "idle", "exploder", 7)
    return [frame([(b, X(1.1), GY), (g, X(2.4), GY)]),
            frame([(lit(b, hexc("#fff4dc"), 0.5), X(1.1), GY), (ga, X(2.4), GY)], fx=[lambda sc: burst(sc, X(1.3), GY - 14, 9)],
                  text=[(X(1.6), 22, "ранена ниже половины")]),
            frame([(g, X(2.4), GY)], fx=[lambda sc: splash(sc, X(1.6), GY + 4, 52, GLUE, 0.8),
                                         lambda sc: drops(sc, X(1.3), GY - 16, hexc("#f0d050"), 16, 34, 2),
                                         lambda sc: burst(sc, X(1.1), GY - 10, 14, GLUE)],
                  text=[(X(1.6), 22, "лопнула липким клеем")], key=True),
            frame([(g, X(2.4), GY)], fx=[lambda sc: ST.ground(sc, "glued", X(2.4), GY, 30), mark(g, X(2.4), GY, "glued")],
                  text=[(X(1.6), 22, "склеен: раунд не ходит и не бьёт")])]


def bolas():
    inv = human("Изобретатель")
    b = lambda p: mb(("ant",), p, "bolas", 8)
    path = arc_pts(X(0.9), GY - 26, X(3.4), GY - 30, 40)
    return [frame([(b("idle"), X(0.5), GY), (inv, X(3.4), GY)]),
            frame([(b("attack"), X(0.6), GY), (inv, X(3.4), GY)], fx=[lambda sc: trail(sc, path[:22], SILK_C),
                                                                      lambda sc: E.blob(sc, *path[22], 3, hexc("#f0c040"))],
                  text=[(X(1.9), 22, "бросает липкий шарик на нити")]),
            frame([(b("attack"), X(0.6), GY), (inv, X(3.4), GY)], fx=[lambda sc: trail(sc, path, SILK_C),
                                                                      lambda sc: E.blob(sc, X(3.4) - 2, GY - 30, 4, hexc("#f0c040"))],
                  text=[(X(1.9), 22, "попала")]),
            frame([(b("idle"), X(0.5), GY), (inv, X(1.5), GY)], fx=[lambda sc: lines(sc, (X(0.9), GY - 26), (X(1.5), GY - 30), SILK_C),
                                                                   lambda sc: speed(sc, X(2.4), GY - 6, 4, 26)],
                  text=[(X(1.9), 22, "подтянула к рою")], key=True),
            frame([(b("attack"), X(0.6), GY), (inv, X(1.5), GY), (mb((), "attack", None, 9), X(1.0), GY + 12),
                   (mb(("stinger",), "attack", None, 10), X(1.1), GY - 12)],
                  fx=[lambda sc: burst(sc, X(1.4), GY - 24, 8)], text=[(X(1.9), 22, "а тут его уже ждут")])]


def midge():
    g, ga = golem("Механик"), golem("Механик", "attack")
    b = mb((), "idle", "midge", 11)
    return [frame([(b, X(1.1), GY), (ga, X(2.3), GY)], fx=[lambda sc: burst(sc, X(1.3), GY - 14, 10)],
                  text=[(X(1.7), 22, "убита")]),
            frame([(g, X(2.3), GY)], fx=[lambda sc: cloud(sc, X(1.1), GY - 16, 22, 14, 1)],
                  text=[(X(1.7), 22, "рассыпалась облаком мошек")]),
            frame([(g, X(2.3), GY)], fx=[lambda sc: cloud(sc, X(1.8), GY - 26, 30, 20, 2)]),
            frame([(ga, X(2.3), GY), (mb((), "idle", None, 12), X(1.2), GY)],
                  fx=[lambda sc: cloud(sc, X(2.3), GY - 36, 34, 30, 3, n=170), lambda sc: lines(sc, (X(2.0), GY - 26), (X(1.6), GY - 52), hexc("#9a92b4"))],
                  text=[(X(1.7), 22, "жалит; удары мимо, стрелки не видят")], key=True)]


def pupa():
    g, ga = golem("Механик"), golem("Механик", "attack")
    b = mb((), "idle", "pupa", 13)
    c = cocoon()
    adult = mb(("ant", "wings"), "attack", None, 13)
    return [frame([(b, X(1.1), GY), (ga, X(2.3), GY)], fx=[lambda sc: burst(sc, X(1.3), GY - 14, 9)],
                  text=[(X(1.7), 22, "ранена ниже половины")]),
            frame([(c, X(1.1), GY), (g, X(2.3), GY)], text=[(X(1.7), 22, "окуклилась")]),
            frame([(c, X(1.1), GY), (ga, X(2.3), GY)], fx=[lambda sc: burst(sc, X(1.25), GY - 10, 8, SILK_C)],
                  text=[(X(1.7), 22, "кокон держит удары")]),
            frame([(lit(c, hexc("#fff4dc"), 0.4), X(1.1), GY), (g, X(2.3), GY)], fx=[lambda sc: burst(sc, X(1.1), GY - 12, 14, hexc("#fff0c0"))]),
            frame([(adult, X(1.4), GY - 26, "air"), (g, X(2.3), GY)], fx=[lambda sc: burst(sc, X(2.0), GY - 50, 9)],
                  text=[(X(1.7), 22, "вышла крылатой и целой")], key=True)]


def nadlom():
    inv = human("Изобретатель")
    b = lambda p, s: mb((), p, "psi_gland", s)
    seq = []
    for n in range(5):
        pose = "attack" if n % 2 else "idle"
        cast = [(b(pose, 14), X(1.2), GY), (b("idle" if n % 2 else "attack", 15), X(1.0), GY + 14)]
        if n < 4:
            fx = [lambda sc, n=n: ST.pips(sc, X(2.2), ST.top_of(inv, GY) - 8, n),
                  lambda sc: sc.glow(X(2.0), GY - 26, 14, PSI_C, 0.5)]
            seq.append(frame(cast + [(inv, X(2.2), GY)], fx=fx, text=[(X(1.7), 22, "укус пси: копится" if n else "пси-железа кусает")]))
        else:
            v = lit(inv, PSI_C, 0.25)
            fx = [lambda sc: ST.glyph(sc, "broken", X(2.2), ST.top_of(inv, GY) - 12),
                  lambda sc: [dot(sc, X(2.2) + np.cos(a) * 12, ST.top_of(inv, GY) - 4 + np.sin(a) * 3, PSI_C, r=1)
                              for a in (0.4, 2.5, 4.6)]]
            seq.append(frame([(b("idle", 14), X(1.2), GY), (b("idle", 15), X(1.0), GY + 14), (v, X(2.2), GY)], fx=fx,
                             text=[(X(1.7), 22, "больше боевого духа — надлом: раунд стоит")], key=True))
    return seq


def spores():
    inv, zod = human("Изобретатель"), human("Зодчий")
    bug_ = mb((), "attack", None, 16)
    dead = human("Изобретатель", "broken")
    host = lambda: (inv, X(2.0), GY)
    return [frame([host(), (zod, X(2.9), GY + 6), (bug_, X(1.1), GY)], fx=[mark(inv, X(2.0), GY, "infected")],
                  text=[(X(1.8), 22, "в нём кладка со спорами")]),
            frame([(lit(inv, hexc("#fff4dc"), 0.5), X(2.0), GY), (zod, X(2.9), GY + 6), (bug_, X(1.2), GY)],
                  fx=[lambda sc: burst(sc, X(1.8), GY - 20, 9)], text=[(X(1.8), 22, "погибает")]),
            frame([(dead, X(2.0), GY + 6), (zod, X(2.9), GY + 6), (bug_, X(1.1), GY)],
                  fx=[lambda sc: cloud(sc, X(2.0), GY - 20, 60, 30, 4, SPORE, 200)], text=[(X(1.8), 22, "лопается спорами")], key=True),
            frame([(dead, X(2.0), GY + 6), (zod, X(2.9), GY + 6), (bug_, X(1.1), GY)],
                  fx=[mark(zod, X(2.9), GY + 6, "infected"), mark(bug_, X(1.1), GY, "infected")],
                  text=[(X(1.8), 22, "заражены все соседи — и свои")])]


def bloodeggs():
    g, ga = golem("Механик"), golem("Механик", "attack")
    b = mb((), "idle", "bloodeggs", 17)
    return [frame([(b, X(1.1), GY), (ga, X(2.3), GY)], fx=[lambda sc: burst(sc, X(1.3), GY - 14, 9)],
                  text=[(X(1.7), 22, "голем раздавил особь")]),
            frame([(lit(b, (26, 18, 16), 0.7), X(1.1), GY + 2), (g, X(2.3), GY)], fx=[mark(g, X(2.3), GY, "infected")],
                  text=[(X(1.7), 22, "яйца перешли в него")]),
            frame([(lit(b, (26, 18, 16), 0.7), X(1.1), GY + 2), (g, X(2.3), GY)], fx=[mark(g, X(2.3), GY, "hatching")],
                  text=[(X(1.7), 22, "кладка зреет")]),
            frame([(g, X(2.3), GY), (larva(), X(1.5), GY + 4), (larva("idle"), X(1.75), GY - 14)],
                  fx=[lambda sc: burst(sc, X(2.1), GY - 30, 12, GREEN), lambda sc: SA.spots(sc, int(X(2.3)), int(GY - 40), [(-4, 0), (3, 8), (0, -10)])],
                  text=[(X(1.7), 22, "личинки вышли — а он ещё жив")], key=True)]


PANELS = [("Прядильные железы", spinner), ("Взрывной муравей", exploder), ("Болас", bolas), ("Мошкара", midge),
          ("Куколка", pupa), ("Надлом", nadlom), ("Споры", spores), ("Яйца в крови", bloodeggs)]


def main():
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 20)
    ft_ = ImageFont.truetype(font("PTSerif-Bold.ttf"), 24)
    ps = []
    for label, fn in PANELS:
        seq = fn()
        ps.append((label, E.render_panel(seq), [f["dur"] + 380 for f in seq], next((i for i, f in enumerate(seq) if f["key"]), 0)))
    n = max(len(p[1]) for p in ps)
    cols, gap, top, lab = 4, 12, 44, 30
    pw, ph = ps[0][1][0].size
    rows = (len(ps) + cols - 1) // cols
    Wd, Hh = cols * (pw + gap) + gap, top + rows * (ph + lab + gap)
    frames, durs = [], []
    for i in range(n + 2):
        img = Image.new("RGB", (Wd, Hh), (24, 18, 30))
        d = ImageDraw.Draw(img)
        d.text((gap, 8), "Рой: мутации в бою", font=ft_, fill=(236, 214, 160))
        for j, (label, imgs, ds, _) in enumerate(ps):
            x, y = gap + (j % cols) * (pw + gap), top + (j // cols) * (ph + lab + gap)
            img.paste(imgs[min(i, len(imgs) - 1)], (x, y))
            d.text((x + 8, y + ph + 4), label, font=fh, fill=(226, 186, 106))
        frames.append(img)
        durs.append(1200 if i >= n else max(p[2][min(i, len(p[2]) - 1)] for p in ps))
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames]
    pal[0].save(out("swarm_mut_fx.gif"), save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2, optimize=False)
    print("swarm_mut_fx.gif", frames[0].size, len(frames), "frames")
    # the key frames, for a still look
    s = 0.62
    kp = [(label, imgs[key].resize((int(pw * s), int(ph * s)), Image.NEAREST)) for label, imgs, _, key in ps]
    kw, kh = kp[0][1].size
    img = Image.new("RGB", (cols * (kw + gap) + gap, 52 + rows * (kh + 26 + gap)), (24, 18, 30))
    d = ImageDraw.Draw(img)
    d.text((gap, 12), "Рой: мутации в бою — ключевые кадры", font=ft_, fill=(236, 214, 160))
    for j, (label, im) in enumerate(kp):
        x, y = gap + (j % cols) * (kw + gap), 52 + (j // cols) * (kh + 26 + gap)
        img.paste(im, (x, y))
        d.text((x + 6, y + kh + 4), label, font=ImageFont.truetype(font("PTSerif-Bold.ttf"), 17), fill=(226, 186, 106))
    img.save(out("swarm_mut_fx.png"))
    print("swarm_mut_fx.png", img.size)


if __name__ == "__main__":
    main()
