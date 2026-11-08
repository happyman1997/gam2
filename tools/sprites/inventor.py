"""The Inventor (an augmented human) and small golems fitted with augments."""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
import golem7 as G
from golem6 import M_IRON, M_DIRON, M_BRONZE, M_HOLE, STYLE1
from golem7 import tbox, cfg, M_PUFF, M_SPARK
from leaders import SKIN, HAIR, LEATHER, CLOTH_BLUE, GLASS, FLAME

COPPER = Mat(ramp("#2a1408", "#5a2a10", "#9a4a1c", "#d07a3a", "#f4b07a"))
ARC = Mat(VOLT, emissive=hexc("#60e0ff"), glow_r=8, glow_k=0.6)
ARC_BIG = Mat(VOLT, emissive=hexc("#80f0ff"), glow_r=14, glow_k=0.9)
MIRROR = Mat(ramp("#3a4048", "#6a7480", "#a8b4c0", "#dce6ee", "#ffffff"))


def zigzag(m, a, b, n=5, amp=1.0, seed=0, mat=ARC):
    rng = np.random.default_rng(seed)
    a, b = np.array(a, float), np.array(b, float)
    pts = [a]
    for i in range(1, n):
        p = a + (b - a) * i / n + rng.normal(size=3) * amp * np.array((0.3, 1.0, 0.6))
        pts.append(p)
    pts.append(b)
    m.limb(pts, 1, mat, band=4)


def coil(m, base, h, r, mat=COPPER):
    base = np.array(base, float)
    n = int(h / 0.9)
    for i in range(n):
        p = base + np.array((0, i * 0.9, 0))
        m.cyl(p, p + (0, 0.5, 0), r, mat, seg=8)
    m.cyl(base, base + (0, h, 0), r * 0.45, M_DIRON, seg=6)


# ---------------------------------------------------------------- the Inventor
def inventor(pose="idle"):
    """Size 3: mechanical legs and arm, a coil backpack, a shock pistol."""
    m = Model()
    for z in (-1.3, 1.3):                                            # piston legs
        m.cyl((0, 9.0, z), (1.2, 4.6, z), 0.9, M_IRON, seg=6)
        m.ell((1.2, 4.6, z), (1.1, 1.1, 1.1), M_BRONZE)
        m.cyl((1.2, 4.6, z), (0.4, 0.6, z), 0.7, M_IRON, seg=6)
        tbox(m, (1.4, 0.4, z), (3.2, 1.6), (2.6, 1.4), 0.8, M_IRON)
    tbox(m, (0, 12.0, 0), (3.2, 3.0), (3.8, 3.6), 6.0, CLOTH_BLUE)      # coat
    tbox(m, (0, 8.6, 0), (4.2, 3.6), (3.4, 3.2), 2.6, CLOTH_BLUE)
    m.box((1.6, 12.0, 0), (0.3, 5.6, 1.0), M_BRONZE)                   # buttons strip
    h = np.array((0.2, 16.6, 0))
    m.ell(h, (1.5, 1.6, 1.5), SKIN)
    m.ell(h + (-0.5, 0.7, 0), (1.45, 1.1, 1.55), HAIR)
    for z in (-0.6, 0.6):
        m.ell(h + (1.3, 0.2, z), (0.35, 0.55, 0.55), ARC)
    m.box(h + (0.4, 0.2, 0), (2.4, 0.3, 3.0), LEATHER)
    # backpack with a tesla coil
    tbox(m, (-2.8, 12.5, 0), (2.8, 4.2), (2.6, 3.8), 6.0, M_BRONZE)
    coil(m, (-3.0, 15.5, 0), 7.0, 1.3)
    m.cyl((-3.0, 22.6, 0), (-3.0, 23.0, 0), 2.6, COPPER, seg=12)
    m.ell((-3.0, 24.2, 0), (1.6, 1.6, 1.6), ARC_BIG)
    for i, d in enumerate(((3.5, 2.5, 1.5), (-3.0, 3.0, -2.0), (0.5, 4.5, 2.5), (2.0, 1.0, -3.0))):
        zigzag(m, (-3.0, 24.2, 0), np.array((-3.0, 24.2, 0)) + d, n=3, amp=0.7, seed=i)
    # a hovering helper drone
    dr = np.array((5.5, 21.0, 4.0)) if pose == "idle" else np.array((8.0, 19.0, 3.0))
    m.ell(dr, (1.6, 1.0, 1.6), M_BRONZE)
    m.ell(dr + (1.4, -0.1, 0), (0.45, 0.45, 0.45), ARC)
    for dx, dz in ((1.6, 1.6), (-1.6, 1.6), (1.6, -1.6), (-1.6, -1.6)):
        m.cyl(dr, dr + (dx, 0.3, dz), 0.2, M_DIRON, seg=4)
        m.cyl(dr + (dx, 0.5, dz), dr + (dx, 0.6, dz), 1.1, MIRROR, seg=8)
    # mechanical far arm with a claw hand
    S = np.array((0.2, 14.4, -2.2))
    E = S + (1.0, -3.2, -0.6)
    Hn = E + (2.6, -1.0, 0)
    m.cyl(S, E, 0.75, M_IRON, seg=6)
    m.ell(E, (0.9, 0.9, 0.9), M_BRONZE)
    m.cyl(E, Hn, 0.65, M_IRON, seg=6)
    for d in ((1.2, -0.6, 0.4), (1.4, 0.0, 0), (1.2, -0.6, -0.4)):
        m.cyl(Hn, Hn + np.array(d), 0.25, M_IRON, r1=0.08, seg=4)
    # near arm with the shock pistol
    Sn = np.array((0.2, 14.4, 2.2))
    hand = Sn + ((2.6, -1.2, 0.6) if pose == "idle" else (3.6, 0.2, 0.6))
    m.cyl(Sn, hand, 0.6, CLOTH_BLUE, seg=5)
    m.box(hand + (0.9, 0.2, 0), (2.4, 1.0, 0.9), M_BRONZE)
    m.cyl(hand + (2.1, 0.2, 0), hand + (3.4, 0.2, 0), 0.55, COPPER, seg=6)
    if pose == "attack":
        zigzag(m, hand + (3.6, 0.2, 0), hand + (15.0, -2.0, 0), n=7, amp=1.4, seed=5, mat=ARC_BIG)
        m.ell(hand + (3.8, 0.2, 0), (1.2, 1.2, 1.2), ARC_BIG)
    return m


# ---------------------------------------------------------------- augments on small golems
def augmented(aug, pose="idle"):
    c = cfg(legs="springs", head="visor", core="volt", arms=("piston", "piston"), tools=("hammer", "claw"))
    m = G.model(c, 1, "idle" if aug != "spring" else ("idle" if pose == "idle" else "attack"))
    hip = G.HIP["springs"]
    if aug == "coil":            # lightning coil: strikes a neighbouring enemy every 2 turns
        base = np.array((-0.5, hip + 18.5, 8.0))
        m.box(base + (0, -0.6, 0), (3.6, 1.2, 3.6), M_BRONZE)
        coil(m, base, 8.0, 1.6)
        m.ell(base + (0, 8.8, 0), (2.0, 2.0, 2.0), ARC)
        if pose == "attack":
            zigzag(m, base + (0, 8.8, 0), base + (24, -10, 2), n=8, amp=1.6, seed=3, mat=ARC_BIG)
        else:
            zigzag(m, base + (0, 8.8, 0), base + (2.5, 11.0, 1.0), n=3, amp=0.5, seed=1)
            zigzag(m, base + (0, 8.8, 0), base + (-2.0, 10.5, 1.5), n=3, amp=0.5, seed=2)
    elif aug == "mirror":        # reflector: the first blow of the battle is returned to the attacker
        R = rot_y(0.55)
        c0 = np.array((10.4, hip + 10.5, 1.5))
        disc = Model()
        disc.cyl((-0.4, 0, 0), (0.3, 0, 0), 5.2, M_BRONZE, seg=14)
        disc.cyl((0.3, 0, 0), (0.6, 0, 0), 4.4, MIRROR, seg=14)
        m.extend(disc.transformed(R, c0))
        if pose == "attack":
            for i in range(6):
                a = i / 6 * 2 * np.pi
                m.cyl(c0 + (1.5, 0, 0), c0 + (8.0, np.cos(a) * 4.0, np.sin(a) * 4.0), 0.3, ARC, r1=0.05, seg=4)
    elif aug == "spring":        # spring dash: leaps at the nearest enemy at the start of battle
        for z in (-8.5, 8.5):
            for i in range(4):
                y = hip - 8 + i * 1.8
                m.box((-3.5 - i * 0.6, y, z), (9.0 - i * 1.6, 0.8, 2.6), M_BRONZE if i % 2 else M_IRON, rot_z(0.45))
            m.cyl((-1.0, hip - 3.0, z), (-1.0, hip - 3.0, z + 0.8 * np.sign(z)), 1.4, M_DIRON, seg=8)
        if pose == "attack":
            m = m.transformed(rot_z(-0.35), (4.0, 7.0, 0))
            for d in ((-8, 2, 0), (-11, 3, 2), (-10, 0, -2)):
                m.ell(np.array(d, float), (1.4, 1.2, 1.2), M_PUFF)
    return m


def render_model(m, k, w=104, h=120, ox=42, oy=96):
    spr = rim_light(render(m.scaled(k), int(w * k), int(h * k), int(ox * k), int(oy * k), **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = int(ox * k), int(oy * k)
    return spr
