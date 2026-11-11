"""Psi mutations — only in the Hive Mind's swarm: mutations on psi and fear, each shown on the body.
  psi_gland    Пси-железа       — mandibles glowing violet
  psi_reson    Резонатор        — long antennae with glowing beads at the tips
  psi_echo     Эхо крика        — a glowing resonator sac on the thorax
  psi_leash    Пси-поводок      — glowing filaments trailing from the back
  psi_whisper  Жуткий шёпот     — a pale mask on the head, a cluster of small eyes
  psi_dread    Чутьё на страх   — swollen sensory pits, red-violet eyes

    python3 tools/sprites/swarm_psi.py      -> out/swarm_psi.png
"""
import numpy as np
from kit import *
from r3d import Mat, rot_z
import swarm1 as W
from swarm1 import spike, M_BONE, M_FANG

PSI = Mat(ramp("#1e0e36", "#462078", "#7640c0", "#ac80ec", "#e6d2ff"), emissive=hexc("#b070ff"), glow_r=5, glow_k=0.45)
PSI_DIM = Mat(ramp("#1a0e2c", "#341a5a", "#563090", "#8460c0", "#c0a8e8"), emissive=hexc("#8a50e0"), glow_r=3, glow_k=0.2)
MASK = Mat(ramp("#2a2630", "#5a5462", "#948c9a", "#c8c0cc", "#f0eaf2"))
DREAD = Mat(ramp("#2a0618", "#6a0e30", "#b02050", "#f04a80", "#ffb0d0"), emissive=hexc("#ff4080"), glow_r=3, glow_k=0.35)

PSI_MUT = [("psi_gland", "Пси-железа", "укус +1 пси, мимо брони"),
           ("psi_reson", "Резонатор", "Помутнение рядом с ней перекидывается ещё на клетку"),
           ("psi_echo", "Эхо крика", "погибая, бьёт 1 пси убийцу и всех врагов рядом"),
           ("psi_leash", "Пси-поводок", "захваченный враг рядом остаётся за роем на ход дольше"),
           ("psi_whisper", "Жуткий шёпот", "враги рядом проверяют страх; у машин сбой, −1 к инициативе"),
           ("psi_dread", "Чутьё на страх", "+2 к удару по испуганному, бегущему, сбоящему")]
SECOND = {"psi_gland": ("stinger",), "psi_reson": ("wings",), "psi_echo": ("acid",), "psi_leash": ("horn",),
          "psi_whisper": ("scythes",), "psi_dread": ("jumper",)}


def add(m, mc, a, key, pose):
    hc, hs, w, gc, gr = a["hc"], a["hs"], a["wing"], a["gc"], a["gr"]
    if key == "psi_gland":
        for z in (1, -1):
            base = hc + np.array((1.5 * hs, -0.9 * hs, z * 0.6 * hs))
            m.ell(base + np.array((1.4 * hs, -0.5, z * 0.4)), (1.4 * hs, 0.75, 0.75), PSI)
        m.ell(hc + np.array((0.2 * hs, -0.2 * hs, 0)), (1.3 * hs, 1.0 * hs, 1.3 * hs), PSI_DIM)
    elif key == "psi_reson":
        for z in (1, -1):
            a0 = hc + np.array((0.8 * hs, 1.2 * hs, 0.5 * z))
            p1 = a0 + np.array((1.0, 4.4, 1.0 * z))
            p2 = p1 + np.array((4.4, 2.6, 1.8 * z))
            m.limb([a0, p1, p2], 1, mc, band=3 if z > 0 else 1)
            m.ell(p2, (0.8, 0.8, 0.8), PSI)
            m.ell(p1 + (p2 - p1) * 0.5, (0.45, 0.45, 0.45), PSI_DIM)
    elif key == "psi_echo":
        m.ell(w + np.array((0.6, -1.6, 0)), (1.8, 1.5, 1.7), PSI_DIM)
        for r in (1.2, 1.9):
            for t in np.linspace(0, 2 * np.pi, 9)[:-1]:
                m.ell(w + np.array((0.6, -1.6 + np.sin(t) * r * 0.8, np.cos(t) * r * 1.4)), (0.22, 0.22, 0.22), PSI)
    elif key == "psi_leash":
        for z, sw in ((1, 1.0), (-1, -0.6), (0, 0.4)):
            p0 = np.array((w[0] - 1.0, w[1] + 1.0, 0.6 * z))
            pts = [p0 + np.array((-2.0 * i, 1.6 * np.sin(i * 1.1 + sw) + 0.8 * i, z * 0.6 * i)) for i in range(5)]
            m.limb(pts, 1, PSI_DIM, band=2)
            m.ell(pts[-1], (0.4, 0.4, 0.4), PSI)
    elif key == "psi_whisper":
        m.ell(hc + np.array((0.7 * hs, 0.2 * hs, 0)), (1.9 * hs, 1.8 * hs, 2.0 * hs), MASK)
        for (dx, dy, dz) in ((1.5, 0.6, 0.6), (1.5, 0.6, -0.6), (1.2, 1.1, 0.0), (1.7, 0.0, 0.0), (1.0, 0.9, 0.9), (1.0, 0.9, -0.9)):
            m.ell(hc + np.array((dx * hs + 1.0 * hs, dy * hs, dz * hs)), (0.4, 0.4, 0.4), PSI)
    elif key == "psi_dread":
        for z in (1, -1):
            m.ell(hc + np.array((0.9 * hs, 0.5 * hs, 1.2 * z * hs)), (0.7, 0.7, 0.55), DREAD)
            m.ell(hc + np.array((1.4 * hs, -0.3 * hs, 0.7 * z * hs)), (0.5, 0.4, 0.4), Mat(W.chitin_shift(mc, 0.0, light=1.6)))
        for (x, y) in a["back"][:3]:
            spike(m, (x, y - 0.2, 0), (x - 0.6, y + 2.2, 0), 0.35, DREAD)


def sheet():
    from PIL import ImageFont
    from leaders_sheet import canvas, put, fonts, S, GOLD, INK, MUT
    from paths import out, font
    import swarm_leaders as SL
    WW, X0, CWD = 960, 80, 160
    Y1, Y2 = 160, 300
    HH = Y2 + 40
    sc = canvas(WW, HH, 63)
    sc.glow(900, 96, 90, hexc("#b070ff"), 0.25)
    put(sc, SL.build("Разум улья", "idle", 1.2), 896, 104, 20)
    for j, (key, name, what) in enumerate(PSI_MUT):
        cx = X0 + j * CWD
        put(sc, W.build((), 0.03, "idle", False, k=2.6, genes=W.genes_for(80 + j), rare=key), cx, Y1, 18)
        put(sc, W.build(SECOND[key], 0.0, "idle", False, k=2.0, genes=W.genes_for(90 + j), rare=key), cx, Y2, 18)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    small = ImageFont.truetype(font("PTSerif-Regular.ttf"), 14)
    d.text((24, 16), "Разум улья: пси-мутации", font=ft, fill=INK)
    d.text((24, 60), "Выпадают только в рое Разума улья, чаще у тех, кто стоял рядом с ним. Пси и страх; против машин — "
                          "сбой ядра.", font=fr, fill=MUT)
    for j, (key, name, what) in enumerate(PSI_MUT):
        cx = (X0 + j * CWD) * S
        d.text((cx - d.textlength(name, font=fbs) / 2, (Y1 + 12) * S), name, font=fbs, fill=GOLD)
        words, lines, cur = what.split(" "), [], ""
        for wd in words:
            if d.textlength(cur + " " + wd, font=small) > (CWD - 10) * S and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for n, ln in enumerate(lines[:3]):
            d.text((cx - d.textlength(ln, font=small) / 2, (Y1 + 12) * S + 24 + n * 18), ln, font=small, fill=MUT)
    img.save(out("swarm_psi.png"))
    print("swarm_psi.png", img.size)


if __name__ == "__main__":
    sheet()
