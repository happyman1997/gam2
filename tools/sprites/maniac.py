"""The Maniac's constructs: modules in places they do not belong, and what Improvisation does to a module."""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
import golem6 as G6
import golem7 as G
from golem6 import M_IRON, M_DIRON, M_BRONZE, M_HOLE, STYLE1
from golem7 import tbox, M_PUFF, M_SPARK
from leaders import human, FLAME, LEATHER, HAIR, CLOTH_RED, SKIN

MAD = Mat(ramp("#2a0a2a", "#5a1460", "#9a2aa0", "#d860d0", "#ffc0f4"), emissive=hexc("#e060e0"), glow_r=6, glow_k=0.45)
MADG = Mat(ramp("#0a2a10", "#145a20", "#2aa040", "#70e080", "#d0ffd8"), emissive=hexc("#60f080"), glow_r=6, glow_k=0.45)
GLOVE = Mat(ramp("#2a0606", "#5a0e0e", "#9a1c1c", "#d0402e", "#f08060"))
WOOD = Mat(ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844"))


def madness(m, c, n=6, r=4.0, seed=0):
    """Flickering magenta/green specks: the mark of Improvisation."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        m.ell(np.array(c) + d * r * rng.uniform(0.7, 1.2), (0.45, 0.45, 0.45), MAD if i % 2 else MADG)


def base(m, hip, head=True, kind="fire"):
    G6.torso(m, hip)
    G6.core(m, hip, kind, 1)
    if head:
        G6.head_visor(m, hip, kind, 1)


# ---------------------------------------------------------------- crazy modules
def saw_legs(m, pose="idle"):
    """Spinning saw blades instead of legs: it rolls and cuts whatever it runs into."""
    hip = 17
    BLADE = Mat(ramp("#2a2c34", "#50545e", "#868a94", "#bcc0c8", "#eef0f4"))
    for z in (-6.5, 6.5):
        c = np.array((0.5, 9.0, z))
        m.cyl(c + (0, 0, -0.6), c + (0, 0, 0.6), 8.4, BLADE, seg=18)
        m.cyl(c + (0, 0, 0.55), c + (0, 0, 0.7), 5.0, M_DIRON, seg=14)
        for i in range(18):
            a = i / 18 * 2 * np.pi + (0.17 if pose == "attack" else 0)
            p = c + np.array((np.cos(a) * 8.8, np.sin(a) * 8.8, 0))
            m.box(p, (2.0, 1.6, 1.0), BLADE, rot_z(a + 0.7))
        m.cyl(c + (0, 0, -0.9), c + (0, 0, 0.9), 1.8, M_BRONZE, seg=8)
        m.box(c + (0, 4.5, 0), (2.0, 9.0, 1.4), M_DIRON)
        if pose == "attack":
            for d in ((9.2, 1.0, 1.5), (9.8, 3.0, 0.5), (8.5, -1.0, 1.8), (9.5, -3.0, 1.0)):
                m.ell(c + d, (0.5, 0.5, 0.5), M_SPARK)
    m.box((0.5, hip - 0.5, 0), (6, 3, 13), M_DIRON)
    return hip


def catapult_head(m, hip, pose="idle"):
    """A throwing arm where the head should be: lobs scrap over the front line."""
    top = hip + 19
    for z in (-3.0, 3.0):
        m.box((-0.5, top + 3.5, z), (1.8, 7.0, 1.4), WOOD)
    m.cyl((-0.5, top + 6.5, -3.6), (-0.5, top + 6.5, 3.6), 0.9, M_IRON, seg=6)
    ang = 2.25 if pose == "idle" else 0.55
    piv = np.array((-0.5, top + 6.5, 0))
    tip = piv + np.array((np.cos(ang) * 15, np.sin(ang) * 15, 0))
    m.cyl(piv - (tip - piv) * 0.15, tip, 1.3, WOOD, seg=6)
    m.cyl(tip + (0, 0.2, 0), tip + (0, 2.0, 0), 2.6, M_IRON, r1=3.4, seg=10)
    if pose == "idle":
        m.ell(tip + (0, 3.2, 0), (2.5, 2.5, 2.5), M_DIRON)
        m.box(tip + (0.8, 4.6, 0.6), (1.4, 1.4, 1.4), M_BRONZE, rot_z(0.6))
    else:
        for i, d in enumerate(((10, 10, 0), (14, 9, 0), (18, 7, 0))):
            m.ell(piv + d, ((2.5, 2.5, 2.5) if i == 2 else (0.5, 0.5, 0.5)), M_DIRON if i == 2 else M_SPARK)


def spring_fist(m, hip, pose="idle"):
    """A boxing glove on a coil spring instead of a head."""
    base_ = np.array((1.0, hip + 19.5, 0))
    d = np.array((0.5, 1.0, 0)) if pose == "idle" else np.array((1.0, 0.25, 0))
    d = d / np.linalg.norm(d)
    L = 12.0 if pose == "idle" else 22.0
    n = 11
    for i in range(n):
        p = base_ + d * (L * i / n)
        m.cyl(p, p + d * 0.7, 2.4, M_IRON if i % 2 else M_BRONZE, seg=8)
    m.cyl(base_, base_ + d * L, 0.6, M_DIRON, seg=5)
    f = base_ + d * (L + 3.4)
    m.ell(f, (4.2, 3.8, 3.8), GLOVE)
    m.ell(f + (-2.4, -1.2, 1.6), (2.0, 2.2, 2.0), GLOVE)
    m.box(f - d * 4.2, (1.4, 4.2, 4.4), M_BRONZE)


def triple_arm(m, hip, pose="idle"):
    """One shoulder, three forearms: hammer, claw and cannon at once."""
    S = np.array((0.5, hip + 14, -12.5))
    E = S + np.array((3.5, -6.5, -0.5))
    m.cyl(S, E, 2.6, M_IRON, seg=8)
    m.ell(E, (2.8, 2.8, 2.8), M_BRONZE)
    G6.shoulder(m, hip, -10.5)
    swing = 0 if pose == "idle" else 1
    hands = {"hammer": E + np.array((5.0, 4.0 - 6 * swing, 0)), "claw": E + np.array((6.0, -2.0, 2.0)),
             "cannon": E + np.array((4.0, -6.0, -2.0))}
    for k, hnd in hands.items():
        m.cyl(E, hnd, 1.6, M_IRON, seg=6)
    G.tool_hammer(m, hands["hammer"], None, pose, "fire", 1)
    G.tool_claw(m, hands["claw"], None, pose, "fire", 1, -1)
    G.tool_cannon(m, hands["cannon"] + np.array((0, -1.5, 0)), None, "idle", "volt", 1, -1)


def hand_wheels(m, pose="idle"):
    """Walks on its hands: wheels instead of fists, the legs stuck up in the air holding hammers."""
    hip = 13
    G6.torso(m, hip)
    G6.core(m, hip, "fire", 1)
    for z in (-11.5, 11.5):
        S = np.array((0.5, hip + 14, z))
        m.cyl(S, (2.0, 6.0, z), 2.4, M_IRON, seg=6)
        m.cyl((2.0, 6.0, z - 1.4 * np.sign(z)), (2.0, 6.0, z + 1.4 * np.sign(z)), 6.0, M_DIRON, seg=14)
        m.cyl((2.0, 6.0, z + 1.45 * np.sign(z)), (2.0, 6.0, z + 1.6 * np.sign(z)), 2.4, M_BRONZE, seg=8)
        G6.shoulder(m, hip, 10.5 * np.sign(z))
    for z in (-4.5, 4.5):    # legs up in the air
        h0 = np.array((-1.0, hip + 18, z))
        kn = h0 + np.array((-2.0, 6.0, 0.5 * np.sign(z)))
        ft = kn + np.array((3.0, 5.0, 0))
        m.cyl(h0, kn, 2.4, M_BRONZE, seg=6)
        m.cyl(kn, ft, 2.0, M_BRONZE, seg=6)
        G.tool_hammer(m, ft, None, "idle" if pose == "idle" else "attack", "fire", 1)
    G6.head_visor(m, hip - 1.0, "fire", 1)


# ---------------------------------------------------------------- whole constructs
def construct(kind, pose="idle"):
    m = Model()
    if kind == "saw":
        hip = saw_legs(m, pose)
        base(m, hip)
        S = np.array((0.5, hip + 14, 12.0))
        Hn = G.hand_target("claw", S, 1, "idle")
        Hn, fd = G.draw_arm(m, S, Hn, "piston", 1, 1, "claw")
        G.tool_claw(m, Hn, fd, "idle", "fire", 1, 1)
        G6.shoulder(m, hip, -10.5)
    elif kind == "catapult":
        hip = G.HIP["tracks"]
        G.LEGS["tracks"](m, hip, 1)
        base(m, hip, head=False)
        catapult_head(m, hip, pose)
        for z, side in ((-12.5, -1), (12.0, 1)):
            S = np.array((0.5, hip + 14, z))
            Hn = G.hand_target("shield", S, side, "idle")
            Hn, fd = G.draw_arm(m, S, Hn, "heavy", 1, side, "shield")
        G.tool_shield(m, Hn, fd, "idle", "fire", 1, 1)
    elif kind == "spring":
        hip = G.HIP["springs"]
        G.LEGS["springs"](m, hip, 1)
        base(m, hip, head=False)
        spring_fist(m, hip, pose)
        for z, side in ((-12.5, -1), (12.0, 1)):
            S = np.array((0.5, hip + 14, z))
            Hn = G.hand_target("claw", S, side, "idle")
            Hn, fd = G.draw_arm(m, S, Hn, "piston", 1, side, "claw")
            G.tool_claw(m, Hn, fd, "idle", "fire", 1, side)
    elif kind == "triple":
        hip = G.HIP["pillars"]
        G.LEGS["pillars"](m, hip, 1)
        base(m, hip)
        triple_arm(m, hip, pose)
        S = np.array((0.5, hip + 14, 12.0))
        Hn = G.hand_target("shield", S, 1, "idle")
        Hn, fd = G.draw_arm(m, S, Hn, "piston", 1, 1, "shield")
        G.tool_shield(m, Hn, fd, "idle", "fire", 1, 1)
    elif kind == "wheels":
        hand_wheels(m, pose)
    return m


# ---------------------------------------------------------------- Improvisation: a module changes for a turn
def improvised(which, after=False):
    """A plain hammer-and-shield golem; after Improvisation one module turns into something else for a turn."""
    m = Model()
    hip = G.HIP["tracks"]
    G.LEGS["tracks"](m, hip, 1)
    base(m, hip)
    far_S, near_S = np.array((0.5, hip + 14, -12.5)), np.array((0.5, hip + 14, 12.0))
    Hf = G.hand_target("hammer", far_S, -1, "idle")
    Hf, fdf = G.draw_arm(m, far_S, Hf, "piston", 1, -1, "hammer")
    Hn = G.hand_target("shield", near_S, 1, "idle")
    Hn, fdn = G.draw_arm(m, near_S, Hn, "piston", 1, 1, "shield")
    if which == "hammer":
        G.tool_hammer(m, Hf, fdf, "idle", "fire", 1)
        G.tool_shield(m, Hn, fdn, "idle", "fire", 1, 1)
        top = Hf + np.array((3, 14, 0))
        if after:   # the hammer spews fire from both faces
            for sgn in (1, -1):
                for i, (dx, r) in enumerate(((5.0, 2.0), (8.0, 2.6), (11.0, 2.0))):
                    m.ell(top + np.array((sgn * (6.5 + dx), 0.5 * i, 0)), (r, r * 0.8, r * 0.8), FLAME)
            madness(m, top, n=7, r=5.0, seed=1)
    else:
        G.tool_hammer(m, Hf, fdf, "idle", "fire", 1)
        R = rot_y(-0.45)
        c = Hn + np.array((3, 1.5, 2))
        if not after:
            G.tool_shield(m, Hn, fdn, "idle", "fire", 1, 1)
        else:      # the shield unfolds into a spinning blade-wheel
            m.cyl(c + R @ np.array((0, 0, -0.6)), c + R @ np.array((0, 0, 0.6)), 7.5, M_IRON, seg=14)
            for i in range(10):
                a = i / 10 * 2 * np.pi
                p = c + R @ np.array((np.cos(a) * 7.5, np.sin(a) * 7.5, 0))
                q = c + R @ np.array((np.cos(a + 0.35) * 11.5, np.sin(a + 0.35) * 11.5, 0))
                m.cyl(p, q, 1.0, M_IRON, r1=0.1, seg=4)
            m.ell(c + R @ np.array((0, 0, 1.0)), (2.4, 2.4, 1.4), MAD, R)
            madness(m, c, n=7, r=8.0, seed=2)
    return m


# ---------------------------------------------------------------- the Maniac himself
def maniac(pose="idle"):
    """A wild-haired madman on a tall rickety walker: a bird leg, a spring leg and a wheel."""
    m = Model()
    tbox(m, (0, 15.0, 0), (13, 11), (14, 12), 5.0, WOOD)
    m.box((0, 17.8, 0), (14.5, 0.8, 12.5), M_DIRON)
    # a backward-bending bird leg
    m.cyl((-3.0, 13.0, -4.0), (-6.5, 8.0, -4.5), 1.3, M_IRON, seg=6)
    m.ell((-6.5, 8.0, -4.5), (1.5, 1.5, 1.5), M_BRONZE)
    m.cyl((-6.5, 8.0, -4.5), (-3.5, 0.8, -4.5), 1.0, M_IRON, seg=6)
    for d in ((3.0, 0, 0.8), (3.0, 0, -0.8), (-2.0, 0, 0)):
        spike_(m, (-3.5, 0.8, -4.5), (-3.5 + d[0], 0.2, -4.5 + d[2]), 0.45)
    # a spring leg
    for i in range(6):
        p = np.array((4.0, 12.5 - i * 1.9, -4.0))
        m.cyl(p, p + (0, 0.8, 0), 1.7, M_IRON if i % 2 else M_BRONZE, seg=8)
    m.box((4.0, 0.8, -4.0), (4.0, 1.6, 3.6), M_IRON)
    # a big wheel
    m.cyl((0.5, 5.6, 4.6), (0.5, 5.6, 6.2), 5.6, M_DIRON, seg=16)
    for a_ in np.linspace(0, np.pi, 4)[:-1]:
        m.box((0.5, 5.6, 6.3), (10.8, 0.6, 0.3), M_BRONZE, rot_z(a_))
    m.cyl((0.5, 12.8, 4.4), (0.5, 5.6, 5.0), 0.7, M_IRON, seg=5)
    # crooked chimney spitting mad colours, a big gear, junk
    m.cyl((-5.5, 17.8, 3.5), (-6.4, 25.0, 3.0), 1.0, M_DIRON, seg=6)
    m.cyl((-6.4, 25.0, 3.0), (-3.6, 28.0, 3.6), 1.0, M_DIRON, seg=6)
    for i, d in enumerate(((-2.4, 30.0, 3.8), (-0.8, 32.5, 3.4), (1.2, 34.5, 3.8))):
        m.ell(d, (1.0 + i * 0.3, 1.0 + i * 0.3, 1.0 + i * 0.3), MAD if i % 2 == 0 else MADG)
    m.cyl((-6.8, 20.0, -2.0), (-7.8, 20.0, -2.0), 4.2, M_BRONZE, seg=14)
    for a_ in np.linspace(0, 2 * np.pi, 13)[:-1]:
        m.box((-7.3, 20.0 + np.sin(a_) * 4.6, -2.0 + np.cos(a_) * 4.6), (1.0, 1.2, 1.2), M_BRONZE)
    m.box((-3.5, 19.6, -3.2), (2.6, 2.6, 2.6), WOOD)
    m.cyl((5.5, 17.8, -4.5), (6.5, 24.0, -4.5), 0.35, M_DIRON, seg=4)
    m.ell((6.6, 23.2, -4.5), (0.9, 1.2, 0.9), MADG)                          # hanging lamp
    human(m, (1.5, 18.0, 0.0), CLOTH_RED, pose, goggles=True)
    # giant wrench
    hand = np.array((3.1, 24.4, 1.8)) if pose == "idle" else np.array((4.5, 25.0, 1.8))
    top = hand + ((1.2, 6.0, 0.3) if pose == "idle" else (6.5, 1.5, 0.3))
    m.cyl(hand, top, 0.45, M_IRON, seg=5)
    m.box(top, (3.0, 1.2, 1.0), M_IRON, rot_z(np.arctan2(top[1] - hand[1], top[0] - hand[0])))
    h = np.array((1.7, 28.0, 0.0))
    for d in ((-0.6, 1.6, 0.0), (-1.4, 1.2, 1.0), (-1.4, 1.2, -1.0), (0.2, 1.7, 0.9), (0.2, 1.7, -0.9),
              (-1.8, 0.3, 0), (-0.8, 1.9, 0.5), (-0.8, 1.9, -0.5)):
        m.cyl(h + (0, 0.6, 0), h + np.array(d) * 2.2, 0.5, HAIR, r1=0.1, seg=4)
    if pose == "attack":
        for d in ((7.0, 30.0, 1.0), (8.5, 28.0, -1.0), (6.0, 32.0, 0.0), (9.0, 26.0, 1.5)):
            m.ell(d, (0.6, 0.6, 0.6), MAD if d[0] > 7 else MADG)
        m.cyl((5.0, 29.0, 1.5), (10.5, 25.0, 2.5), 0.3, MAD, seg=4)
    return m


def spike_(m, a, b, r):
    m.cyl(a, b, r, M_IRON, r1=0.1, seg=4)


def render_model(m, k, w=104, h=110, ox=42, oy=88):
    spr = render(m.scaled(k), int(w * k), int(h * k), int(ox * k), int(oy * k), **STYLE1)
    spr.ox, spr.oy = int(ox * k), int(oy * k)
    return spr


M_BONE = Mat(BONE)
