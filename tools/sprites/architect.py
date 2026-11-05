"""The Architect's army: golems with building modules (mobile and deployed), the mason golem, the leader."""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
import golem7 as G
from golem6 import M_IRON, M_DIRON, M_BRONZE, M_HOLE, STYLE1
from golem7 import tbox, cfg, M_PUFF, M_SPARK
from leaders import human, LINEN, LEATHER, FLAME

WOOD = Mat(ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844"))
STONE = Mat(ramp("#22202a", "#3e3a46", "#5e5a68", "#86828e", "#b2aeb8"))
MORTAR = Mat(ramp("#1a1820", "#2a2830", "#3a3842", "#4a4852", "#5a5862"))
RUNE = Mat(EMBER, emissive=hexc("#ff8a30"), glow_r=5, glow_k=0.35)
PAPER = Mat(ramp("#4a4436", "#7a7258", "#aaa080", "#d8cea8", "#f6eed2"))


def spike(m, a, b, r, mat=M_IRON):
    m.cyl(a, b, r, mat, r1=0.12, seg=5)


def wall_segment(m, x, z0, z1, h, tier, y0=0.0):
    """A wall along z (across the golem's front). Tier I logs, II stone and bronze, III iron, spikes and runes."""
    L = z1 - z0
    zc = (z0 + z1) / 2
    if tier == 1:
        n = int(h // 2.4)
        for i in range(n):
            y = y0 + 1.2 + i * 2.4
            m.cyl((x, y, z0), (x, y, z1), 1.25, WOOD, seg=7)
        for z in (z0 + 1.5, zc, z1 - 1.5):
            m.box((x + 1.4, y0 + h / 2, z), (0.6, h, 0.8), WOOD)
    elif tier == 2:
        rows = int(h // 3)
        for r in range(rows):
            off = 0 if r % 2 == 0 else 2.0
            z = z0 + off
            while z < z1 - 0.5:
                w = min(4.0, z1 - z)
                tbox(m, (x, y0 + 1.5 + r * 3, z + w / 2), (2.6, w - 0.3), (2.4, w - 0.4), 2.8, STONE)
                z += 4.0
        m.box((x + 1.35, y0 + h - 1.0, zc), (0.5, 1.0, L), M_BRONZE)
    else:
        m.box((x, y0 + h / 2, zc), (2.4, h, L), M_IRON)
        for z in np.arange(z0 + 2, z1 - 1, 4.0):
            m.box((x + 1.25, y0 + h / 2, z), (0.4, h - 1, 0.6), M_DIRON)
            m.ell((x + 1.4, y0 + h - 1.5, z), (0.5, 0.5, 0.5), M_BRONZE)
            spike(m, (x + 1.2, y0 + h * 0.55, z + 2), (x + 4.6, y0 + h * 0.55, z + 2), 0.6)
        m.box((x + 1.3, y0 + h * 0.3, zc), (0.3, 0.6, L - 2), RUNE)
        for z in np.arange(z0 + 1, z1, 3.0):
            tbox(m, (x, y0 + h + 0.8, z), (2.4, 1.6), (1.6, 0.8), 1.6, M_IRON)


# ---------------------------------------------------------------- building modules on a golem
def with_module(module, deployed=False, tier=2, pose="idle"):
    c = cfg(legs="tracks", head="visor", core="fire", arms=("piston", "piston"),
            tools=("hammer", "shield") if module not in ("wall", "gate") else ("hammer", "claw"))
    m = G.model(c, 1, "idle")
    hip = G.HIP["tracks"]
    top = hip + 19
    if module == "tower":
        if not deployed:
            m.cyl((-5.5, top - 4, 0), (-5.5, top + 1.5, 0), 4.2, STONE if tier > 1 else WOOD, seg=10)
            for a in np.linspace(0, 2 * np.pi, 7)[:-1]:
                m.box((-5.5 + np.cos(a) * 4.0, top + 2.2, np.sin(a) * 4.0), (1.4, 1.4, 1.4), M_BRONZE)
        else:
            mat = STONE if tier > 1 else WOOD
            tx = -6.5
            m.cyl((tx, top - 6, 0), (tx, top + 22, 0), 5.6, mat, seg=12)
            for y in (top + 4, top + 13):
                m.cyl((tx, y, 0), (tx, y + 0.9, 0), 6.0, M_BRONZE, seg=12)
            m.cyl((tx, top + 22, 0), (tx, top + 23.6, 0), 7.0, mat, seg=12)
            for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
                m.box((tx + np.cos(a) * 6.3, top + 24.8, np.sin(a) * 6.3), (1.9, 2.4, 1.9), mat)
            for y in (top + 8, top + 17):
                m.box((tx + 5.4, y, 0), (0.6, 1.4, 2.0), M_HOLE)
            barrel_end = (tx + 14.0, top + 17.0, 0) if pose == "idle" else (tx + 11.5, top + 17.4, 0)
            m.cyl((tx + 4.0, top + 17.0, 0), barrel_end, 1.4, M_IRON, seg=8)
            if pose == "attack":
                m.ell((tx + 15.5, top + 17.6, 0), (2.6, 2.0, 2.0), FLAME)
            for (x, z) in ((-13, 7), (-13, -7), (13, 7), (13, -7)):
                spike(m, (x * 0.85, 4.0, z), (x * 1.05, -0.6, z * 1.1), 1.0, M_DIRON)
    elif module == "wall":
        if not deployed:
            for i in range(3):
                m.box((-1.0, hip + 6 + i * 3.4, 12.6 + i * 0.3), (12, 3.0, 1.0), M_IRON)
        else:
            wall_segment(m, 12.0, -22.0, 22.0, 15.0, tier)
    elif module == "gate":
        if not deployed:
            m.box((-6.0, top - 2, 0), (1.2, 8, 9), WOOD)
        else:
            for z in (-13.0, 13.0):
                tbox(m, (12.0, 10.0, z), (4.0, 4.0), (3.2, 3.2), 20.0, STONE if tier > 1 else WOOD)
                tbox(m, (12.0, 21.0, z), (4.4, 4.4), (2.0, 2.0), 2.4, M_BRONZE)
            m.box((12.0, 18.6, 0), (3.2, 2.2, 29.0), M_BRONZE)
            for z, ang in ((-12.0, 0.9), (12.0, -0.9)):
                leaf = Model()
                leaf.box((0, 8.0, z * -0.45), (1.2, 15.0, 11.5), WOOD)
                for y in (3.0, 12.5):
                    leaf.box((0.7, y, z * -0.45), (0.3, 1.0, 11.5), M_IRON)
                leaf = leaf.transformed(rot_y(ang * 0.8), (0, 0, 0))
                m.extend(leaf.transformed(I3, (12.0, 0.5, z)))
    elif module == "bell":
        if not deployed:
            m.cyl((-6.0, top - 1, 0), (-6.0, top + 4.0, 0), 1.8, M_BRONZE, r1=3.0, seg=10)
        else:
            for z in (-7.5, 7.5):
                m.box((0.5, top + 12.0, z), (1.8, 26.0, 1.8), WOOD)
            m.box((0.5, top + 25.6, 0), (2.0, 1.8, 17.5), WOOD)
            sw = 0.0 if pose == "idle" else 0.45
            bell = Model()
            bell.cyl((0, -0.8, 0), (0, -7.2, 0), 2.0, M_BRONZE, r1=4.8, seg=12)
            bell.ell((0, -7.4, 0), (1.0, 1.0, 1.0), M_DIRON)
            m.extend(bell.transformed(rot_x(sw) @ rot_z(sw * 0.5), (0.5, top + 25.0, 0)))
            if pose == "attack":
                for r in (9.0, 12.5):
                    for a in np.linspace(-0.8, 0.8, 6):
                        m.ell((0.5 + np.cos(a) * r, top + 18.0, np.sin(a) * r), (0.4, 0.4, 0.4), M_SPARK)
    return m


def mason(pose="idle", tier=2):
    """The mason: a small golem with a trowel that lays a section of wall every 2 turns."""
    c = cfg(legs="springs", head="visor", core="fire", arms=("piston", "piston"), tools=("claw", "claw"))
    m = G.model(c, 1, "idle")
    hip = G.HIP["springs"]
    m.box((-7.2, hip + 12, 0), (3.2, 10, 8), WOOD)                     # hod of bricks on the back
    for i in range(3):
        for z in (-2.2, 2.2):
            m.box((-7.2, hip + 17.6 + i * 1.6, z), (2.8, 1.4, 3.6), STONE if tier > 1 else WOOD)
    hand = np.array((8.0, hip + 4.0, 13.5))
    tip = hand + (np.array((4.0, -2.5, 0)) if pose == "idle" else np.array((5.0, -5.0, 0)))
    m.cyl(hand, hand + (tip - hand) * 0.4, 0.4, WOOD, seg=4)
    m.solid([hand + (tip - hand) * 0.4 + d for d in ((0, 0.4, -1.4), (0, 0.4, 1.4), (0, -0.4, 0))] + [tip],
            [[0, 1, 3], [1, 2, 3], [2, 0, 3], [0, 1, 2]], M_IRON)
    wall_segment(m, 15.0, -6.0, 8.0 if pose == "attack" else 2.0, 7.0, tier)
    return m


# ---------------------------------------------------------------- the leader
def architect(pose="idle"):
    """The Architect on a walking crane, a block hanging from the hook and a scroll of drawings in hand."""
    m = Model()
    for z in (-4.0, 4.0):
        hip = np.array((0.0, 9.5, z))
        knee = np.array((3.5, 5.0, z * 1.1))
        foot = np.array((0.5, 0.6, z * 1.2))
        m.cyl(hip, knee, 1.6, M_IRON, seg=6)
        m.ell(knee, (1.8, 1.8, 1.8), M_BRONZE)
        m.cyl(knee, foot, 1.4, M_IRON, seg=6)
        tbox(m, foot + (1.0, -0.3, 0), (6.0, 3.6), (5.0, 3.0), 1.2, M_IRON)
    tbox(m, (0, 11.0, 0), (11, 9), (12, 10), 3.0, WOOD)
    for x, z in ((-4.5, -3.5), (-4.5, 3.5), (-2.5, 0)):
        m.cyl((x, 12.5, z), (-3.5, 27.0, 0), 0.5, M_IRON, seg=4)       # lattice mast
    m.ell((-3.5, 27.2, 0), (1.2, 1.2, 1.2), M_BRONZE)
    tip = np.array((10.5, 30.0, 0)) if pose == "idle" else np.array((12.5, 25.0, 0))
    m.cyl((-3.5, 27.2, 0), tip, 0.7, M_IRON, seg=5)
    m.cyl((-3.5, 27.2, 0), (-9.0, 24.5, 0), 0.6, M_IRON, seg=5)
    tbox(m, (-9.5, 23.5, 0), (3.2, 3.2), (3.2, 3.2), 3.2, STONE)        # counterweight
    hook = tip + (0, -7.0, 0) if pose == "idle" else tip + (2.5, -6.0, 0)
    m.cyl(tip, hook, 0.18, M_DIRON, seg=4)
    tbox(m, hook + (0, -2.6, 0), (5.0, 5.0), (5.0, 5.0), 5.0, STONE)
    human(m, (2.0, 12.5, -1.5), LINEN, pose)
    bp = np.array((4.2, 21.0, -2.0))                                       # an unrolled blueprint
    m.box(bp, (0.3, 3.4, 4.6), Mat(ramp("#0c1a3a", "#16306a", "#2a52a0", "#4a7ad0", "#8ab4f0")), rot_z(-0.3))
    for dy in (-1.0, 0.0, 1.0):
        m.box(bp + (0.25, dy, 0), (0.1, 0.25, 3.8), Mat(ramp("#6a9ad0", "#8ab4e0", "#b0d0f0", "#d8ecff", "#ffffff"),
                                                         emissive=hexc("#9ad0ff"), glow_r=3, glow_k=0.25), rot_z(-0.3))
    m.cyl((-3.5, 27.2, 0), (-3.5, 33.0, 0), 0.3, M_DIRON, seg=4)            # flag on the mast
    m.box((-5.4, 31.6, 0), (3.6, 2.4, 0.3), Mat(ramp("#2a1a06", "#5a3a0e", "#9a6a1a", "#d8a030", "#f6d070")))
    for i in range(3):                                                     # a half-built pillar on the deck
        tbox(m, (-3.0, 13.5 + i * 2.2, 3.4), (3.0, 3.0), (2.8, 2.8), 2.0, STONE)
    tbox(m, (2.2, 24.6, -1.5), (2.6, 2.6), (1.8, 1.8), 2.2, LEATHER)   # tall hat
    m.box((2.2, 23.5, -1.5), (3.4, 0.4, 3.4), LEATHER)
    if pose == "attack":
        tbox(m, (8.0, 19.0, -1.0), (1.6, 1.0), (1.6, 1.0), 1.0, STONE)
    return m


def render_model(m, k, w=104, h=128, ox=42, oy=104):
    spr = render(m.scaled(k), int(w * k), int(h * k), int(ox * k), int(oy * k), **STYLE1)
    spr.ox, spr.oy = int(ox * k), int(oy * k)
    return spr
