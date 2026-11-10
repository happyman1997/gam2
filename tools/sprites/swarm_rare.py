"""The swarm's rare traits: rare mutations that change behaviour, not numbers. Each shows on the body:
  alarm     Тревога            — red alarm glands on the thorax, bristling red-tipped spines
  spinner   Прядильные железы  — spinnerets at the tip of the abdomen, a silk thread
  exploder  Взрывной муравей   — a bloated yellow abdomen full of glands
  vivi      Живородящая        — a sac of an abdomen with a larva curled inside
  strider   Стрекот            — a ribbed file on the back to stridulate with
  bud       Почкование         — a bud on its side: a small second creature with eyes, growing
and what each does in battle, at battle scale (zoomed).

    python3 tools/sprites/swarm_rare.py      -> out/swarm_rare.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, rot_z, rot_x, I3
import swarm1 as W
from swarm1 import spike, M_BONE, M_FANG, M_SHEEN
from golem6 import M_IRON, M_DIRON, emissive

ALARM = Mat(ramp("#2a0606", "#6a0e0e", "#b02018", "#f04a30", "#ffb0a0"), emissive=hexc("#ff4020"), glow_r=4, glow_k=0.4)
SILK = Mat(ramp("#2a2622", "#5a544a", "#948c7e", "#c8c0b0", "#f0eadc"))
GLAND = Mat(ramp("#2a1a04", "#6a4a08", "#b08a14", "#e8c840", "#fff2a0"), emissive=hexc("#e0b020"), glow_r=3, glow_k=0.2)
VIVI = Mat(ramp("#1c0e14", "#3e2232", "#6a4458", "#9a7488", "#ccaabb"))
GRUB = Mat(ramp("#241a12", "#54442e", "#8a7656", "#bea98a", "#ece0c4"))
CORE = emissive("fire", 5, 0.45)
STEEL = Mat(ramp("#1e2228", "#3a404a", "#606874", "#949ca8", "#d0d6de"))
STEEL_D = Mat(ramp("#121418", "#22262e", "#363c46", "#525a66", "#7a8290"))

RARE = [("alarm", "Тревога", "гибель поднимает тревогу: свои в 2 клетках +2 к удару и +1 к скорости"),
        ("spinner", "Прядильные железы", "паутина на клетке: враг застревает, свои бегают свободно"),
        ("exploder", "Взрывной муравей", "раненая лопается липким ядом: соседние враги склеены"),
        ("vivi", "Живородящая", "погибнув, выпускает личинку"),
        ("strider", "Стрекот", "враги проверяют страх, у машин дребезжат детали: −2 к инициативе"),
        ("bud", "Почкование", "впервые раненая делится надвое, у каждой половина здоровья")]
SECOND = {"alarm": ("horn",), "spinner": ("stinger",), "exploder": ("wings",), "vivi": ("acid",), "strider": ("jumper",),
          "bud": ("scythes",)}


def add(m, mc, a, rare, pose):
    y0, gc, gr, w = a["y0"], a["gc"], a["gr"], a["wing"]
    if rare == "alarm":
        for z in (1, -1):
            m.ell(w + (0.2, -1.2, 1.9 * z), (1.0, 0.75, 0.55), ALARM)
        for (x, y) in a["back"]:
            spike(m, (x, y - 0.4, 0), (x - 1.2, y + 3.2, 0), 0.6, M_BONE)
            m.ell((x - 1.2, y + 3.2, 0), (0.35, 0.35, 0.35), ALARM)
    elif rare == "spinner":
        t = a["tip"]
        for z in (-0.8, 0.0, 0.8):
            m.cyl(t + (0.8, 0.3, z), t + (-1.8, -0.8, z * 1.6), 0.75, M_BONE, r1=0.25, seg=6)
        end = np.array((t[0] - 6.0, 0.2, 1.4))
        m.cyl(t + (-1.8, -0.8, 0), end, 0.3, SILK, seg=4)
        m.poly([end + (1.0, 0.0, -2.0), end + (-3.0, 0.0, 1.6), end + (1.4, 0.0, 2.8)], SILK)        # a scrap of web
        for d in ((-1.0, 0.1, -0.6), (0.2, 0.1, 1.2)):
            m.cyl(end + (1.0, 0.0, -2.0), end + np.array(d) * 2, 0.15, Mat(W.chitin(0.0)), seg=3)
    elif rare == "exploder":
        m.ell(gc, (gr * 1.25, gr * 1.15, gr * 1.15), GLAND, rot_z(0.2))
        for t in (-0.5, 0.0, 0.5):
            x = gc[0] + t * gr
            r = gr * 1.15 * np.sqrt(max(0.1, 1 - t * t * 0.8))
            m.cyl((x - 0.2, gc[1], 0), (x + 0.2, gc[1], 0), r * 1.02, Mat(W.chitin(0.0)), seg=14)
        m.ell(gc + (gr * 0.3, gr * 0.7, gr * 0.6), (gr * 0.3, gr * 0.2, gr * 0.25), M_SHEEN)
    elif rare == "vivi":
        m.ell(gc, (gr * 1.12, gr * 1.06, gr * 1.06), VIVI, rot_z(0.2))
        for i in range(7):                                  # a larva curled up, pressing against the side
            ang = 0.6 + i * 0.7
            p = gc + np.array((np.cos(ang) * gr * 0.52, np.sin(ang) * gr * 0.46, gr * 0.84))
            m.ell(p, (gr * 0.3 - 0.04 * i, gr * 0.28 - 0.04 * i, 0.6), GRUB)
        m.ell(gc + np.array((np.cos(0.6) * gr * 0.62, np.sin(0.6) * gr * 0.5, gr * 0.9)), (gr * 0.18, gr * 0.18, 0.5),
              Mat(W.chitin(0.0)))
    elif rare == "strider":
        top = gc + np.array((0, gr * 0.92, 0))
        m.ell(top, (gr * 0.9, 0.5, gr * 0.75), Mat(W.chitin_shift(mc, 0.0, light=1.5)), rot_z(0.2))
        for i in range(8):
            p = top + np.array((gr * 0.75 - i * gr * 0.22, 0.45 + 0.04 * i, 0))
            m.box(p, (0.32, 0.9, gr * 1.3), M_BONE, rot_z(0.2))
        for z in (1, -1):
            m.ell(w + (0.6, -0.6, 1.8 * z), (0.8, 0.8, 0.3), M_SHEEN)          # the drum-skins (tympana)
    elif rare == "bud":
        pale = Mat(W.chitin_shift(mc, 0.0, sat=0.8, light=1.45))
        c = gc + np.array((gr * 0.05, gr * 0.05, gr * 1.05))           # the bud on the near side of the abdomen
        m.ell(gc + np.array((gr * 0.05, 0.0, gr * 0.75)), (gr * 0.5, gr * 0.45, gr * 0.3), VIVI)
        m.ell(c + (0, 0, gr * 0.3), (gr * 0.75, gr * 0.62, gr * 0.6), pale)
        h = c + (gr * 0.7, gr * 0.2, gr * 0.55)
        m.ell(h, (gr * 0.4, gr * 0.36, gr * 0.36), pale)
        for z in (0.16, -0.16):
            m.ell(h + (gr * 0.28, gr * 0.12, z * gr + gr * 0.2), (0.38, 0.38, 0.38), W.M_EYE)
        for k in range(3):
            m.limb([c + (gr * (0.35 - 0.35 * k), -gr * 0.4, gr * 0.7), c + (gr * (0.5 - 0.35 * k), -gr * 0.95, gr * 1.1)], 1, pale,
                   band=2)


def sheet():
    from PIL import ImageFont
    from leaders_sheet import canvas, put, fonts, S, GOLD, INK, MUT
    from paths import out, font
    import swarm_effects as E
    import swarm_abilities as SA
    WW, X0, CWD = 960, 80, 160
    Y1, Y2, Y3 = 132, 262, 410
    HH = Y3 + 64
    sc = canvas(WW, HH, 59)
    for j, (key, name, what) in enumerate(RARE):
        cx = X0 + j * CWD
        put(sc, W.build((), 0.03, "idle", False, k=2.6, genes=W.genes_for(30 + j), rare=key), cx, Y1, 18)
        put(sc, W.build(SECOND[key], 0.0, "idle", False, k=2.0, genes=W.genes_for(40 + j), rare=key), cx, Y2, 18)
    # in battle, zoomed: the Mechanic as the enemy
    Z = 1.15
    meh = lambda p="idle": E.mirror(F_build("Механик", p, 1.15 * Z))
    by = Y3
    # alarm: one dead, the others red with rage, rushing
    x = X0
    put(sc, E.lit(W.build((), 0.0, "idle", False, k=Z, genes=W.genes_for(3), rare="alarm"), (26, 18, 16), 0.7), x - 34, by + 4, 8)
    for dx, dy in ((-6, -10), (8, 6), (-20, 8)):
        put(sc, E.lit(W.build((), 0.0, "attack", False, k=Z, genes=W.genes_for(40 + dx), rare="alarm"), (240, 60, 40), 0.25), x + dx, by + dy, 8)
    E.speed(sc, x - 24, by - 6, 3, 14, hexc("#f06040"))
    # spinner: a web on the Mechanic's cell
    x = X0 + CWD
    for r in (8, 16, 24):
        E.ring(sc, x + 24, by, r * 1.6, hexc("#e8e0d0"), 0.55, ry=r * 0.45)
    for t in np.linspace(0, np.pi, 7):
        E.lines(sc, (x + 24, by), (x + 24 + np.cos(t) * 40, by + np.sin(t) * 12 - 4), hexc("#e8e0d0"), 0.55)
    put(sc, meh(), x + 30, by, 0)
    for k in range(4):
        E.lines(sc, (x + 14 + k * 6, by - 2), (x + 18 + k * 5, by - 26), hexc("#f0eadc"), 0.7)
    put(sc, W.build((), 0.0, "idle", False, k=Z, genes=W.genes_for(5), rare="spinner"), x - 36, by, 8)
    # exploder: the glue splash, the Mechanic's feet stuck
    x = X0 + 2 * CWD
    put(sc, meh(), x + 22, by, 0)
    E.splash(sc, x + 4, by + 2, 40, hexc("#e8c840"), 0.75)
    E.drops(sc, x - 8, by - 10, hexc("#f0d050"), 12, 22, 1)
    for dx in (-30, -22):
        E.dot(sc, x + dx, by - 4, hexc("#3a2a10"), r=1)
    # vivi: a dead body, a larva crawling out
    x = X0 + 3 * CWD
    put(sc, E.lit(W.build(("acid",), 0.0, "idle", False, k=Z, genes=W.genes_for(6), rare="vivi"), (26, 18, 16), 0.7), x - 10, by + 2, 10)
    import swarm_leaders as SL
    put(sc, SL.build("личинка", "attack", Z), x + 26, by, 6)
    # strider: sound rings; the Mechanic's parts rattle
    x = X0 + 4 * CWD
    put(sc, W.build(("jumper",), 0.0, "attack", False, k=Z, genes=W.genes_for(7), rare="strider"), x - 34, by, 8)
    for r in (10, 18, 26):
        SA.ring(sc, x - 20, by - 18, r, r * 0.8, hexc("#e0d8a0"), 0.5)
    put(sc, meh(), x + 34, by, 0)
    for dy in (-50, -34, -18):
        for k in range(3):
            E.dot(sc, x + 50 + k * 3, by + dy + (k % 2) * 2, hexc("#e0d8a0"))
    # bud: wounded, it splits in two
    x = X0 + 5 * CWD
    put(sc, meh("attack"), x + 36, by, 0)
    for dx, dy, sd in ((-14, -8, 8), (-20, 10, 9)):
        put(sc, W.build(("scythes",), 0.0, "attack", False, k=Z, genes=W.genes_for(sd)), x + dx, by + dy, 8)
    E.burst(sc, x - 18, by - 2, 8, hexc("#c8a0e0"))
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    small = ImageFont.truetype(font("PTSerif-Regular.ttf"), 14)
    d.text((24, 16), "Рой: редкие черты", font=ft, fill=INK)
    d.text((24, 60), "Редкие мутации меняют поведение, а не цифры. Занимают место детали, наследуются, видны на спрайте; "
                     "минус никогда не бьёт по остальному рою.", font=fr, fill=MUT)
    for j, (key, name, what) in enumerate(RARE):
        cx = (X0 + j * CWD) * S
        d.text((cx - d.textlength(name, font=fbs) / 2, (Y1 + 10) * S), name, font=fbs, fill=GOLD)
        words, lines, cur = what.split(" "), [], ""
        for wd in words:
            if d.textlength(cur + " " + wd, font=small) > (CWD - 10) * S and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for n, ln in enumerate(lines[:3]):
            d.text((cx - d.textlength(ln, font=small) / 2, (Y1 + 10) * S + 24 + n * 18), ln, font=small, fill=MUT)
    d.text((24, (Y2 + 30) * S), "В бою", font=fh, fill=GOLD)
    caps = ["свои рвутся к убийце", "враг застрял в паутине", "лопнула: враг склеен", "личинка из тела",
            "дребезг: −2 к инициативе", "ранена — стала двумя"]
    for j, c in enumerate(caps):
        cx = (X0 + j * CWD) * S
        d.text((cx - d.textlength(c, font=small) / 2, (Y3 + 18) * S), c, font=small, fill=INK)
    img.save(out("swarm_rare.png"))
    print("swarm_rare.png", img.size)


def F_build(name, pose, k):
    import frames as F
    return F.build(name, pose, k=k)


if __name__ == "__main__":
    sheet()
