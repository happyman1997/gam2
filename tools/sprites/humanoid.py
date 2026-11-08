"""Trial: one Foundry golem (the Guard) rebuilt as a humanoid machine.

Human build — feet, knees, hips, a waist, a chest, shoulders, elbows, hands, a head on a neck —
but every part is a mechanism: axles with gear rings, hydraulic rams on mount lugs, glowing heat
conduits, an open spine with the furnace showing through, cooling fins, a boiler with a fan and
a valve wheel, a helm with twin optics, a steam maul, a shield on a hinged bracket.

The model is kept as named part groups so `clipcheck.py` can prove nothing passes through
anything it should not.

    python3 tools/sprites/humanoid.py          -> out/humanoid_trial.png (+ clipping report)
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import (M_IRON, M_DIRON, M_STEEL, M_RUST, M_HOSE, M_GLASS, M_PLATE, M_HOLE,
                    emissive, spike, tbox, pivot, STYLE1)
from golem7 import M_PUFF

PAINT = ramp("#0e1218", "#1c2430", "#2e3a4a", "#4a5a6e", "#7a8aa0")   # the Guard's blued steel
LAMP_G = Mat(ramp("#0a2a10", "#145a20", "#2a9a3a", "#6ae070", "#d0ffd0"), emissive=hexc("#60ff80"), glow_r=3, glow_k=0.35)


def arr(p):
    return np.array(p, float)


def unit(v):
    v = arr(v)
    return v / np.linalg.norm(v)


def lerp(a, b, t):
    return arr(a) + (arr(b) - arr(a)) * t


def basis(a, b, fwd=(1, 0, 0)):
    """Rotation whose local y runs from a to b and local x leans towards `fwd`."""
    ey = unit(arr(b) - arr(a))
    f = arr(fwd)
    ex = f - ey * (f @ ey)
    if np.linalg.norm(ex) < 1e-6:
        ex = arr((0, 0, 1.0)) - ey * ey[2]
    ex /= np.linalg.norm(ex)
    return np.column_stack([ex, ey, np.cross(ex, ey)]), np.linalg.norm(arr(b) - arr(a))


def block(m, a, b, bot, top, mat, fwd=(1, 0, 0), off=(0, 0, 0)):
    """A tapered block along a->b; bot/top are (forward, side) sizes at a and b.
    off = (along local forward, along the bone, along WORLD z)."""
    R, L = basis(a, b, fwd)
    c = (arr(a) + arr(b)) / 2 + R @ arr((off[0], off[1], 0)) + arr((0, 0, off[2]))
    tbox(m, c, bot, top, L, mat, R)
    return R


def axle(m, p, r, w, s, mat=M_DIRON):
    """A joint drum across the body (along z), hub cap on the outer face."""
    p = arr(p)
    m.cyl(p - (0, 0, w / 2), p + (0, 0, w / 2), r, mat, seg=10)
    m.cyl(p + (0, 0, s * (w / 2 - 0.1)), p + (0, 0, s * (w / 2 + 0.3)), r * 0.45, M_STEEL, seg=8)


def gear(m, c, r, s, teeth=10, mat=M_IRON):
    """A toothed ring on the outer face of a joint."""
    c = arr(c)
    m.cyl(c, c + (0, 0, 0.6 * s), r, mat, seg=14)
    for i in range(teeth):
        a = 2 * np.pi * (i + 0.5) / teeth
        m.box(c + (np.cos(a) * (r + 0.2), np.sin(a) * (r + 0.2), 0.3 * s), (0.6, 0.5, 0.6), mat, rot_z(a))
    m.cyl(c + (0, 0, 0.5 * s), c + (0, 0, 0.95 * s), r * 0.42, M_STEEL, seg=8)


def ram(m, a, b, r=0.7):
    """Hydraulic ram: dark sleeve from a, polished rod to b, clevis eyes at both ends."""
    a, b = arr(a), arr(b)
    mid = lerp(a, b, 0.55)
    m.cyl(a, mid, r, M_DIRON, seg=8)
    m.cyl(lerp(a, b, 0.48), mid, r + 0.15, M_IRON, seg=8)
    m.cyl(mid, b, r * 0.5, M_STEEL, seg=6)
    for p in (a, b):
        m.cyl(p - (0, 0, r * 0.7), p + (0, 0, r * 0.7), r * 0.75, M_DIRON, seg=8)


def conduit(m, a, b, r=0.45, windows=(0.35, 0.68)):
    """A heat conduit from the furnace: dark pipe with glowing sight-glass windows."""
    a, b = arr(a), arr(b)
    m.cyl(a, b, r, M_DIRON, seg=6)
    for t in windows:
        m.cyl(lerp(a, b, t - 0.06), lerp(a, b, t + 0.06), r + 0.08, emissive("fire", 4, 0.3), seg=6)
    for t in (0.0, 1.0):
        m.cyl(lerp(a, b, max(0, t - 0.05)), lerp(a, b, min(1, t + 0.05)), r + 0.2, M_STEEL, seg=6)


def rivets(m, pts, mat=M_STEEL, r=0.3):
    for p in pts:
        m.ell(p, (r, r, r), mat)


class Parts(dict):
    def __missing__(self, k):
        self[k] = Model()
        return self[k]

    def model(self):
        m = Model()
        for g in self.values():
            m.extend(g)
        return m


# ---------------------------------------------------------------- legs
def leg(G, key, hipj, knee, ankle, s, P):
    g, rm = G[key], G[key + ".ram"]
    hipj, knee, ankle = arr(hipj), arr(knee), arr(ankle)
    axle(g, hipj, 2.6, 3.4, s)
    gear(g, hipj + (0, 0, 1.7 * s), 2.3, s, teeth=11)
    Rt = block(g, hipj, knee, (3.8, 3.8), (3.4, 3.4), M_DIRON)                                   # thigh beam
    block(g, lerp(hipj, knee, 0.2), lerp(hipj, knee, 0.86), (1.4, 4.4), (1.4, 3.9), P, off=(2.4, 0, 0))     # front plate
    block(g, lerp(hipj, knee, 0.36), lerp(hipj, knee, 0.84), (4.0, 1.1), (3.6, 1.1), P, off=(0.3, 0, 2.3 * s))  # outer plate
    conduit(g, lerp(hipj, knee, 0.42) + (0, 0, 3.3 * s), lerp(hipj, knee, 0.8) + (0, 0, 3.3 * s), r=0.5)
    axle(g, knee, 2.2, 4.2, s)
    gear(g, knee + (0, 0, 2.1 * s), 1.8, s, teeth=9)
    g.ell(knee + Rt @ arr((2.5, 0.0, 0)), (1.5, 2.2, 2.2), P)                                     # knee cap
    rivets(g, [knee + Rt @ arr((3.9, 0.0, 0))], r=0.35)
    Rs = block(g, knee, ankle, (3.2, 3.2), (3.2, 3.2), M_DIRON, off=(-0.3, 0, 0))                 # shin beam
    block(g, lerp(knee, ankle, 0.1), lerp(knee, ankle, 0.92), (4.4, 4.8), (5.0, 5.4), P, off=(0.7, 0, 0))   # greave
    block(g, lerp(knee, ankle, 0.16), lerp(knee, ankle, 0.82), (1.1, 1.4), (1.1, 1.6), M_DIRON, off=(3.4, 0, 0))  # ridge
    rivets(g, [lerp(knee, ankle, t) + Rs @ arr((1.0, 0, 0)) + (0, 0, 2.75 * s) for t in (0.3, 0.55, 0.8)], r=0.35)
    # thigh ram: from the back of the thigh across the knee to the back of the shin, on lugs
    bt, bs = -Rt[:, 0], -Rs[:, 0]
    A = lerp(hipj, knee, 0.3) + bt * 3.5
    B = lerp(knee, ankle, 0.28) + bs * 3.4
    g.cyl(A, A - bt * 2.0, 0.6, M_DIRON, seg=6)
    g.cyl(B, B - bs * 2.0, 0.6, M_DIRON, seg=6)
    ram(rm, A, B, 0.85)
    # ankle and an articulated foot: heel, hinge, toe block, toe cap, claws
    axle(g, ankle, 1.6, 3.8, s)
    g.box(ankle + (-1.5, -2.1, 0), (4.4, 2.2, 5.0), M_IRON)
    toe = ankle + (3.4, -2.4, 0)
    g.cyl(ankle + (1.0, -2.2, -2.6), ankle + (1.0, -2.2, 2.6), 1.0, M_DIRON, seg=8)
    g.box(toe, (5.2, 1.8, 5.2), M_IRON)
    tbox(g, toe + (0.4, 1.15, 0), (4.0, 5.2), (3.0, 4.4), 0.5, P)
    for z in (-1.7, 0, 1.7):
        g.box(toe + (2.95, -0.2, z), (1.0, 1.3, 1.2), M_DIRON)
    # ankle ram: shin back to the heel
    C = lerp(knee, ankle, 0.48) + bs * 3.3
    D = ankle + (-4.0, -1.0, 0)
    g.cyl(C, C - bs * 1.9, 0.5, M_DIRON, seg=6)
    ram(rm, C, D, 0.6)


# ---------------------------------------------------------------- arms and hands
def arm(G, key, sh, elbow, wrist, s, P, ram_side="back"):
    """Upper arm with a ram, elbow gear, a heavy gauntlet with a heat conduit."""
    g, rm = G[key], G[key + ".ram"]
    sh, elbow, wrist = arr(sh), arr(elbow), arr(wrist)
    g.ell(sh, (2.9, 2.9, 2.9), M_DIRON)
    block(g, sh, elbow, (3.4, 3.4), (3.0, 3.0), M_DIRON)
    block(g, lerp(sh, elbow, 0.32), lerp(sh, elbow, 0.86), (3.6, 1.1), (3.0, 1.1), P, off=(0, 0, 2.15 * s))
    axle(g, elbow, 2.0, 4.0, s)
    gear(g, elbow + (0, 0, 2.0 * s), 1.6, s, teeth=9)
    Rf = block(g, elbow, wrist, (4.2, 4.2), (5.4, 5.0), P)                                      # gauntlet
    block(g, lerp(elbow, wrist, 0.78), wrist, (6.0, 5.6), (6.0, 5.6), M_DIRON)                  # cuff
    conduit(g, lerp(elbow, wrist, 0.22) + (0, 0, 2.95 * s), lerp(elbow, wrist, 0.7) + (0, 0, 2.95 * s), r=0.45)
    rivets(g, [lerp(elbow, wrist, t) + Rf @ arr((2.35, 0, 0)) for t in (0.3, 0.55)], r=0.35)
    U, F = unit(sh - elbow), unit(wrist - elbow)
    out = -(U + F)
    out[2] = 0.0                                                     # arms bend in their own plane
    if np.linalg.norm(out) < 0.5:
        out = arr((0, 1.0, 0)) - F * F[1]
        out[2] = 0.0
    out = unit(out)
    nb = out - U * (out @ U)
    nb[2] = 0.0
    nb = unit(nb)                                                    # the back of the upper arm
    if ram_side == "back":       # triceps ram to a lever behind the elbow
        A = lerp(sh, elbow, 0.5) + nb * 2.7
        B = elbow + unit(out * 0.6 + nb) * 3.3
        g.cyl(A, A - nb * 1.4, 0.5, M_DIRON, seg=6)
        g.cyl(elbow, B, 0.8, M_IRON, seg=6)
    else:                        # a raised, nearly straight arm: biceps ram under the arm
        nf = -nb - F * (-nb @ F)
        nf[2] = 0.0
        nf = unit(nf)
        A = lerp(sh, elbow, 0.72) - nb * 2.7
        B = lerp(elbow, wrist, 0.62) + nf * 3.3
        g.cyl(A, A + nb * 1.4, 0.5, M_DIRON, seg=6)
        g.cyl(B, B - nf * 1.4, 0.5, M_DIRON, seg=6)
    ram(rm, A, B, 0.75)
    return wrist


def fist(G, key, wrist, along, grip, P):
    """A gauntleted hand closed around a haft along `grip`: palm, four knuckles, a thumb, a guard."""
    g = G[key]
    w = arr(wrist)
    d, gr = unit(along), unit(grip)
    gr = unit(gr - d * (gr @ d))
    side = np.cross(d, gr)
    R = np.column_stack([d, gr, side])
    c = w + d * 2.0
    g.box(c, (3.8, 4.0, 3.8), M_IRON, R)
    for i in range(4):
        g.box(c + d * 1.3 + gr * (-1.5 + i * 1.0) + side * 1.5, (1.2, 0.85, 1.4), M_DIRON, R)
    g.box(c - side * 1.6 + d * 0.6, (1.5, 1.5, 1.1), M_DIRON, R)
    g.box(c - d * 0.3 + side * 2.05, (3.0, 3.6, 0.5), P, R)                                  # knuckle guard
    return c


# ---------------------------------------------------------------- weapons
def maul(G, hand, u, P, t_fwd, reach):
    """Steam maul: haft with a feed line, head with a hot striking face and a steam ram at the back."""
    g = G["hammer"]
    hand, u = arr(hand), unit(u)
    butt, top = hand - u * 1.6, hand + u * reach
    g.cyl(butt, top, 0.85, M_DIRON, seg=6)
    g.cyl(butt - u * 0.6, butt, 1.15, M_IRON, seg=6)
    for k in (reach - 5.6, reach - 2.8):
        p = hand + u * k
        g.cyl(p, p + u * 0.9, 1.2, M_IRON, seg=6)
    R, _ = basis(top - u, top + u, t_fwd)
    side = R[:, 2]
    g.cyl(hand + u * 3.8 + side * 1.25, top + u * 0.3 + side * 1.25, 0.4, M_HOSE, seg=5)        # feed line
    hc = top + u * 2.8
    at = lambda x, y=0.0, z=0.0: hc + R @ arr((x, y, z))
    g.box(hc, (9.8, 5.6, 5.6), M_IRON, R)
    g.box(hc, (2.4, 6.2, 6.2), P, R)
    g.box(at(5.3), (0.9, 6.0, 6.0), M_DIRON, R)
    g.box(at(5.85), (0.3, 4.8, 4.8), emissive("fire", 10, 0.5), R)                              # hot striking face
    g.cyl(at(-4.9), at(-7.2), 1.9, M_DIRON, seg=10)                                              # steam ram housing
    g.cyl(at(-7.2), at(-7.7), 2.25, M_IRON, seg=10)
    g.cyl(at(-7.7), at(-8.8), 0.8, M_STEEL, seg=6)
    for zz in (2.85, -2.85):
        for x in (-3.3, -2.3, 2.3, 3.3):
            g.box(at(x, 0, zz), (0.4, 3.2, 0.15), M_HOLE, R)                                    # vents
        rivets(g, [at(0, dy, zz * 1.1) for dy in (-1.7, 1.7)], r=0.35)
    return at(6.05), hc


def shield(G, C, R, P):
    """Tower shield: dark frame, two plates with a seam, vision slit, boss, ground spikes, edge hinges."""
    g = G["shield"]
    C = arr(C)
    at = lambda x, y=0.0, z=0.0: C + R @ arr((x, y, z))
    g.box(C, (1.5, 21.5, 13.0), M_DIRON, R)
    g.box(at(0.5, 5.3), (1.1, 10.0, 11.4), P, R)
    g.box(at(0.5, -5.45), (1.1, 9.6, 11.4), P, R)
    g.box(at(1.1, 7.7), (0.3, 1.0, 6.0), M_HOLE, R)                                               # vision slit
    g.box(at(1.1, 7.7, 2.4), (0.32, 0.7, 0.7), emissive("fire", 3, 0.3), R)                       # an optic behind it
    g.box(at(1.1, -1.7), (0.3, 12.5, 1.2), M_DIRON, R)
    g.ell(at(1.3, -1.7), (1.0, 2.1, 2.1), M_IRON, R)
    for y in (-9.6, -1.2, 1.8, 9.4):
        rivets(g, [at(1.15, y, z) for z in (-5.3, 5.3)], r=0.35)
    for z in (-4.0, 4.0):
        spike(g, at(0, -10.75, z), at(0.5, -13.0, z), 0.8, M_IRON)                                # ground spikes
    for y in (-7.0, 0.0, 7.0):
        g.cyl(at(-0.2, y - 1.1, -6.7), at(-0.2, y + 1.1, -6.7), 0.7, M_IRON, seg=6)              # edge hinges
    g.box(at(1.1, -6.8, 3.0), (0.2, 2.8, 0.4), M_RUST, R)
    return at(-0.75)


def bracket(G, fist_c, d, back_c, R):
    """Hinged bracket from the gauntlet to the shield's back."""
    g = G["bracket"]
    f = arr(fist_c) + unit(d) * 1.9
    for y in (-2.8, 2.8):
        a = f + R @ arr((0, y * 0.5, 0))
        b = arr(back_c) + R @ arr((0, y, 0))
        g.cyl(a, b, 0.55, M_DIRON, seg=6)
    g.cyl(arr(back_c) + R @ arr((-0.45, -3.7, 0)), arr(back_c) + R @ arr((-0.45, 3.7, 0)), 0.7, M_IRON, seg=8)


# ---------------------------------------------------------------- body
HIP = 20.0
HZ = 4.4                                    # half the hip spread
SH = arr((-0.6, 34.2, 10.0))                # near shoulder; the far one mirrors in z
CY = 30.6


def chest_front(y):
    """x of the painted chest layer's front face at height y."""
    return 0.7 + 3.9 + 1.4 * (y - 26.9) / 8.2


def chest_side(y):
    """z of the dark chest frame's flank at height y."""
    return 4.3 + 5.1 * (y - 26.0) / 9.2


def torso(G, P):
    # pelvis: a gearbox with a centre plate
    pl = G["pelvis"]
    tbox(pl, (-0.2, HIP + 1.4, 0), (6.4, 9.0), (7.0, 10.0), 3.2, M_DIRON)
    tbox(pl, (3.75, HIP - 0.5, 0), (1.0, 2.8), (1.2, 3.2), 3.8, P, rot_z(-0.2))
    pl.box((3.3, HIP + 1.4, 0), (0.7, 1.2, 3.4), M_DIRON)
    # waist: an open spine — rings with the furnace showing between them, rams and cables
    sp = G["spine"]
    for i, y in enumerate((23.0, 24.1, 25.2)):
        sp.cyl((-0.8, y, 0), (-0.8, y + 0.8, 0), 3.0 + 0.15 * i, M_DIRON, seg=12)
        sp.cyl((-0.8, y + 0.8, 0), (-0.8, y + 1.1, 0), 2.5, emissive("fire", 6, 0.35), seg=12)
    for zz in (3.7, -3.7):
        ram(sp, (0.8, 23.3, zz), (1.1, 26.8, zz), 0.55)
    for z in (-0.9, 0.9):
        sp.cyl((3.2, 22.6, z), (3.8, 26.4, z), 0.5, M_HOSE, seg=5)
    # chest: a broad furnace — dark frame, painted shell, breastplate, grate, gauges, fins
    ch = G["chest"]
    tbox(ch, (0.0, CY, 0), (8.2, 8.6), (11.2, 18.8), 9.2, M_DIRON)
    tbox(ch, (0.7, 31.0, 0), (7.8, 8.0), (10.6, 18.0), 8.2, P)
    for y0, y1, w0, w1 in ((31.8, 34.9, 12.4, 16.0), (27.2, 28.4, 5.0, 5.8)):
        f0, f1 = chest_front(y0), chest_front(y1)
        tbox(ch, ((f0 + f1) / 2 + 0.3, (y0 + y1) / 2, 0), (0.7, w0), (0.7, w1), y1 - y0, P,
             rot_z(-np.arctan2(f1 - f0, y1 - y0)))                                              # breastplate bands
    fy = 30.0
    fx = chest_front(fy)
    ch.box((fx + 0.35, fy, 0), (1.4, 5.2, 6.8), M_DIRON)                                        # furnace mouth
    ch.ell((fx + 0.6, fy, 0), (0.7, 2.3, 2.9), emissive("fire", 14, 0.7))
    for z in (-2.4, -1.2, 0.0, 1.2, 2.4):
        ch.box((fx + 1.2, fy, z), (0.45, 5.0, 0.45), M_DIRON)
    ch.box((fx + 1.2, fy + 2.7, 0), (0.7, 0.6, 7.0), M_IRON)
    rivets(ch, [(chest_front(33.8) + 0.65, 33.8, z) for z in (-5.6, -2.8, 0, 2.8, 5.6)], r=0.35)
    g = arr((chest_front(32.4) + 0.65, 32.4, 4.4))                                             # pressure gauge
    ch.cyl(g - (0.3, 0, 0), g + (0.45, 0, 0), 1.2, M_STEEL, seg=10)
    ch.ell(g + (0.5, 0, 0), (0.15, 0.9, 0.9), M_GLASS)
    ch.box((chest_front(32.2) + 0.7, 32.2, -4.4), (0.3, 1.3, 2.6), M_PLATE)                    # serial plate
    for z, lamp in ((-2.4, LAMP_G), (-1.4, emissive("fire", 3, 0.4))):
        ch.ell((chest_front(27.0) + 0.35, 27.8, z), (0.35, 0.35, 0.35), lamp)                     # indicator lamps
    for y in (27.0, 28.2, 29.4, 30.6):                                                          # cooling fins on the flanks
        for s in (1, -1):
            ch.box((-0.6, y, s * (chest_side(y) + 0.45)), (5.0, 0.4, 1.0), M_IRON)
    # back: a boiler with rust bands, a fan housing, a valve wheel on the near end cap
    bo = G["boiler"]
    bo.cyl((-6.2, 30.0, -5.4), (-6.2, 30.0, 5.4), 3.6, M_IRON, seg=14)
    for z in (-3.8, 3.0):
        bo.cyl((-6.2, 30.0, z), (-6.2, 30.0, z + 0.7), 3.85, M_RUST, seg=14)
    bo.cyl((-9.6, 29.4, 0), (-10.9, 29.4, 0), 2.4, M_DIRON, seg=12)
    for a in (0.0, np.pi / 3, 2 * np.pi / 3):
        bo.box((-10.95, 29.4, 0), (0.2, 4.4, 0.4), M_STEEL, rot_x(a))
    bo.ell((-11.0, 29.4, 0), (0.25, 0.7, 0.7), M_IRON)
    wc = arr((-6.2, 30.0, 5.4))
    bo.cyl(wc, wc + (0, 0, 1.0), 0.4, M_STEEL, seg=6)
    for i in range(8):
        a0, a1 = 2 * np.pi * i / 8, 2 * np.pi * (i + 1) / 8
        p0 = wc + (np.cos(a0) * 1.8, np.sin(a0) * 1.8, 1.0)
        p1 = wc + (np.cos(a1) * 1.8, np.sin(a1) * 1.8, 1.0)
        bo.cyl(p0, p1, 0.3, M_RUST if i % 2 else M_IRON, seg=5)
    for a in (0.0, np.pi / 2):
        bo.box(wc + (0, 0, 1.0), (3.6, 0.35, 0.35), M_IRON, rot_z(a))
    st = G["stacks"]
    for z, h in ((2.6, 9.0), (-2.6, 7.4)):
        b0 = arr((-7.0, 32.6, z))
        top = b0 + (-0.9, h, 0)
        st.cyl(b0, top, 1.2, M_DIRON, seg=8)
        st.cyl(top, top + (0, 0.8, 0), 1.7, M_IRON, seg=8)
        st.cyl(lerp(b0, top, 0.5), lerp(b0, top, 0.5) + (0, 0.6, 0), 1.5, M_RUST, seg=8)
        for i, d in enumerate(((0.0, 2.6, 0), (-1.3, 5.2, 0.4))):
            st.ell(top + arr(d), (1.7 + i * 0.9, 1.4 + i * 0.7, 1.5 + i * 0.7), M_PUFF)
    ho = G["hose"]
    pts = [arr(p) for p in ((-6.0, 32.6, 4.8), (-7.8, 34.6, 9.4), (-3.6, 34.9, 10.8))]
    for p0, p1 in zip(pts[:-1], pts[1:]):
        ho.cyl(p0, p1, 0.6, M_HOSE, seg=6)
    # neck and helm: a short neck between the shoulders, a helm with twin optics
    hd = G["head"]
    tbox(hd, (0.4, 35.4, 0), (8.0, 9.6), (5.6, 6.6), 1.8, M_DIRON)                              # gorget
    hd.cyl((0.6, 35.4, 0), (1.6, 37.8, 0), 1.6, M_DIRON, seg=8)
    for i in range(2):
        hd.cyl((0.9 + 0.35 * i, 36.2 + i * 0.8, 0), (0.9 + 0.35 * i, 36.6 + i * 0.8, 0), 1.9, M_STEEL, seg=8)
    for z in (-1.1, 1.1):
        hd.cyl((-0.4, 37.6, z), (-2.4, 35.2, z * 1.7), 0.45, M_HOSE, seg=5)
    hc = arr((2.2, 40.0, 0))
    tbox(hd, hc, (4.8, 4.2), (4.0, 3.6), 5.2, P)
    tbox(hd, hc + (0.2, 2.9, 0), (4.0, 3.6), (2.6, 2.0), 1.0, P)
    hd.box(hc + (0.0, 3.6, 0), (4.4, 0.8, 0.7), M_DIRON)                                        # low crest
    tbox(hd, hc + (1.1, -1.5, 0), (2.6, 3.4), (2.0, 3.0), 2.4, M_IRON)                          # jaw
    for i in range(2):
        hd.box(hc + (2.35, -2.2 + i * 0.8, 0), (0.3, 0.25, 1.8), M_HOLE)
    hd.box(hc + (2.05, 1.6, 0), (1.0, 0.8, 4.0), M_DIRON)                                       # brow
    for z, r in ((0.95, 0.95), (-1.0, 0.65)):                                                   # twin optics
        p = hc + arr((2.0, 0.6, z))
        hd.cyl(p, p + (1.5, 0, 0), r, M_DIRON, seg=10)
        hd.cyl(p + (1.3, 0, 0), p + (1.6, 0, 0), r + 0.2, M_STEEL, seg=10)
        hd.ell(p + (1.65, 0, 0), (0.2, r * 0.75, r * 0.75), emissive("fire", 6, 0.6))
    for s in (1, -1):                                                                           # slotted side plates
        p = hc + arr((-0.2, -0.2, 2.15 * s))
        hd.box(p, (2.6, 2.6, 0.5), M_IRON)
        for dy in (-0.7, 0.0, 0.7):
            hd.box(p + (0, dy, 0.27 * s), (1.9, 0.22, 0.1), M_HOLE)
    hd.cyl(hc + (-1.4, 1.2, -0.8), hc + (-2.0, 4.6, -0.8), 0.35, M_IRON, seg=6)                 # whistle pipe
    hd.cyl(hc + (-2.0, 4.6, -0.8), hc + (-2.05, 5.1, -0.8), 0.55, M_STEEL, seg=6)
    rivets(hd, [hc + (0.2, 0.0, 2.05), hc + (0.2, 0.0, -2.05), hc + (-1.0, 0.6, 2.0)])
    # pauldrons: big layered plates over the shoulder sockets
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pd = G[key]
        c = SH * (1, 1, s) + (0, 1.2, 0)
        pd.ell(c, (4.8, 3.0, 4.0), P)
        tbox(pd, c + (0, -2.2, 0.9 * s), (7.0, 3.2), (8.0, 3.6), 1.6, P, rot_x(-0.35 * s))
        tbox(pd, c + (0, -3.4, 1.5 * s), (6.0, 3.0), (6.8, 3.2), 1.2, P, rot_x(-0.5 * s))
        pd.ell(c + (0, 1.0, 0), (3.8, 1.5, 3.3), M_DIRON)
        rivets(pd, [c + (x, 1.8, 2.9 * s) for x in (-2.4, 0.0, 2.4)], r=0.35)
        pd.box(c + (0.5, -0.7, 3.9 * s), (2.6, 1.4, 0.2), M_PLATE)


def guard_parts(pose="idle", P=None):
    P = Mat(PAINT) if P is None else P
    atk = pose == "attack"
    G = Parts()
    leg(G, "leg_n", (0.4, HIP, HZ), (3.6, 10.8, HZ + 0.5), (2.8, 3.6, HZ + 0.7), 1, P)
    leg(G, "leg_f", (-0.8, HIP, -HZ), (-1.0, 10.8, -HZ - 0.6), (-4.6, 3.6, -HZ - 0.8), -1, P)
    torso(G, P)
    far = SH * (1, 1, -1)
    if not atk:
        # the maul carried on the shoulder: the haft rests on top of the pauldron, head behind
        el = SH + (1.4, -7.6, 2.0)
        w = arm(G, "arm_n", SH, el, SH + (WX, WY, 1.6), 1, P)
        rest = arr((-0.8, RY, 10.4))
        hand = fist(G, "hand_n", w, w - el, rest - w, P)
        maul(G, hand, rest - hand, P, (0, 1, 0), reach=13.0)
        elf = far + (0.8, -8.0, -1.6)
        w = arm(G, "arm_f", far, elf, far + (5.8, -10.0, -2.0), -1, P)
        fc = fist(G, "hand_f", w, w - elf, (0, 1, 0), P)
        R = rot_y(0.5)
        back = shield(G, fc + R @ arr((1.9 + 2.0 + 0.75, 0, 0)), R, P)
        bracket(G, fc, w - elf, back, R)
    else:
        el = SH + (5.4, -0.4, 1.6)
        w = arm(G, "arm_n", SH, el, SH + (11.8, 0.2, 1.2), 1, P, ram_side="front")
        u = unit(arr(UA))
        hand = fist(G, "hand_n", w, w - el, u, P)
        tf = unit(arr((-UA[1], UA[0], 0)))
        face, _ = maul(G, hand, u, P, tf, reach=13.0)
        sp = G["sparks"]
        for i, dd in enumerate(((1.0, 0.0, 0.0), (2.6, 1.6, 0.9), (2.2, -1.4, -1.0), (3.8, 0.5, 0.2))):
            sp.ell(face + tf * dd[0] + arr((0, dd[1], dd[2])), (1.0 - 0.15 * i,) * 3,
                   emissive("fire", 11 if i == 0 else 0, 0.8))
        elf = far + (1.8, -7.8, -1.6)
        w = arm(G, "arm_f", far, elf, far + (7.2, -9.0, -2.0), -1, P)
        fc = fist(G, "hand_f", w, w - elf, (0, 1, 0), P)
        R = rot_y(0.3)
        back = shield(G, fc + R @ arr((1.9 + 2.0 + 0.75, 0, 0)), R, P)
        bracket(G, fc, w - elf, back, R)
        for k in list(G):
            if not k.startswith("leg_"):
                G[k] = pivot(G[k], rot_z(-0.14), (0, HIP, 0))
    return G


WX, WY, RY = 6.8, 0.4, 40.1      # idle: wrist of the carrying arm, height where the haft rests on the pauldron
UA = (0.56, -0.83, 0.0)          # attack: direction of the haft


ALLOWED = [("leg_n", "pelvis"), ("leg_f", "pelvis"), ("leg_n", "leg_n.ram"), ("leg_f", "leg_f.ram"),
           ("spine", "pelvis"), ("spine", "chest"), ("chest", "boiler"), ("chest", "head"),
           ("chest", "pauldron_n"), ("chest", "pauldron_f"), ("chest", "arm_n"), ("chest", "arm_f"),
           ("boiler", "stacks"), ("boiler", "hose"), ("hose", "pauldron_n"), ("hose", "arm_n"),
           ("pauldron_n", "arm_n"), ("pauldron_f", "arm_f"), ("arm_n", "arm_n.ram"), ("arm_f", "arm_f.ram"),
           ("arm_n", "hand_n"), ("arm_f", "hand_f"), ("hand_n", "hammer"), ("hand_f", "bracket"),
           ("bracket", "shield"), ("pauldron_n", "pauldron_f")]


def guard(pose="idle", P=None):
    return guard_parts(pose, P).model()


def build(pose="idle", k=2.2, P=None, yaw=None):
    w, h = int(70 * k), int(64 * k)
    ox, oy = int(30 * k), int(58 * k)
    opts = dict(STYLE1)
    if yaw is not None:
        opts["yaw"] = yaw
    spr = rim_light(render(guard(pose, P).scaled(k), w, h, ox, oy, **opts), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def check(pose):
    from clipcheck import report
    return report(guard_parts(pose), ALLOWED, skip=("sparks",))


if __name__ == "__main__":
    from PIL import ImageFont
    from noise import value_noise
    from paths import font, out
    import frames as F
    import swarm1 as W
    for pose in ("idle", "attack"):
        bad = check(pose)
        print(pose, "clipping:", "none" if not bad else ", ".join(f"{a}×{b} {v:.2f}" for v, a, b in bad))
    S = 2
    WW, HH = 960, 580
    sc = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 91) * 0.6 + value_noise(WW, HH, 5, 92) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        sc.rgb[lv == i] = hexc(col)

    def put(spr, cx, by, sw):
        e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(3, sw * 0.18)) ** 2
        sc.rgb[e <= 1] *= 0.62
        sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))

    put(build("idle", 5.0), 200, 318, 90)
    put(build("attack", 5.0), 600, 318, 90)
    by = 540
    put(F.build("Страж", "idle"), 110, by, 52)
    put(build("idle"), 300, by, 46)
    put(build("attack"), 470, by, 46)
    put(W.build((), 0.0, "idle", False, k=1.0), 640, by, 8)
    put(W.build((), 0.05, "idle", True, k=1.0), 700, by, 12)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 17)
    d.text((24, 12), "Проба 3: Страж массивнее — шире плечи и грудь, толще руки и ноги", font=ft, fill=(236, 226, 200))
    d.text((24, 52), "Крупно — покой и атака. Внизу — в размере боя: старый Страж, новый, и рой для масштаба.",
           font=fr, fill=(190, 182, 164))
    for x, t in ((110, "было"), (300, "стало · покой"), (470, "стало · атака"), (670, "рабочая и солдат роя")):
        d.text((x * S - d.textlength(t, font=fr) / 2, (by + 10) * S), t, font=fr, fill=(226, 186, 106))
    img.save(out("humanoid_trial.png"))
    print(img.size)
