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
    axle(g, hipj, 2.2, 3.0, s)
    gear(g, hipj + (0, 0, 1.5 * s), 2.0, s)
    Rt = block(g, hipj, knee, (3.0, 3.0), (2.8, 2.8), M_DIRON)                                   # thigh beam
    block(g, lerp(hipj, knee, 0.22), lerp(hipj, knee, 0.86), (1.2, 3.4), (1.2, 3.0), P, off=(1.95, 0, 0))   # front plate
    block(g, lerp(hipj, knee, 0.38), lerp(hipj, knee, 0.84), (3.2, 1.0), (2.8, 1.0), P, off=(0.2, 0, 1.85 * s))  # outer plate
    conduit(g, lerp(hipj, knee, 0.42) + (0, 0, 2.75 * s), lerp(hipj, knee, 0.8) + (0, 0, 2.75 * s))
    axle(g, knee, 1.8, 3.4, s)
    gear(g, knee + (0, 0, 1.7 * s), 1.5, s, teeth=8)
    g.ell(knee + Rt @ arr((2.0, 0.0, 0)), (1.2, 1.8, 1.7), P)                                     # knee cap
    rivets(g, [knee + Rt @ arr((3.1, 0.0, 0))])
    Rs = block(g, knee, ankle, (2.6, 2.6), (2.6, 2.6), M_DIRON, off=(-0.3, 0, 0))                 # shin beam
    block(g, lerp(knee, ankle, 0.1), lerp(knee, ankle, 0.92), (3.4, 3.8), (3.8, 4.2), P, off=(0.6, 0, 0))   # greave
    block(g, lerp(knee, ankle, 0.16), lerp(knee, ankle, 0.82), (1.0, 1.2), (1.0, 1.4), M_DIRON, off=(2.75, 0, 0))  # ridge
    rivets(g, [lerp(knee, ankle, t) + Rs @ arr((0.8, 0, 0)) + (0, 0, 2.15 * s) for t in (0.3, 0.55, 0.8)])
    # thigh ram: from the back of the thigh across the knee to the back of the shin, on lugs
    bt, bs = -Rt[:, 0], -Rs[:, 0]
    A = lerp(hipj, knee, 0.3) + bt * 3.0
    B = lerp(knee, ankle, 0.28) + bs * 2.9
    g.cyl(A, A - bt * 1.7, 0.5, M_DIRON, seg=6)
    g.cyl(B, B - bs * 1.8, 0.5, M_DIRON, seg=6)
    ram(rm, A, B, 0.7)
    # ankle and an articulated foot: heel, hinge, toe block, toe cap, claws
    axle(g, ankle, 1.3, 3.2, s)
    g.box(ankle + (-1.3, -2.2, 0), (3.6, 2.0, 4.0), M_IRON)
    toe = ankle + (2.9, -2.5, 0)
    g.cyl(ankle + (0.9, -2.3, -2.1), ankle + (0.9, -2.3, 2.1), 0.9, M_DIRON, seg=8)
    g.box(toe, (4.4, 1.6, 4.2), M_IRON)
    tbox(g, toe + (0.4, 1.05, 0), (3.4, 4.2), (2.6, 3.6), 0.5, P)
    for z in (-1.4, 0, 1.4):
        g.box(toe + (2.5, -0.2, z), (0.9, 1.1, 1.0), M_DIRON)
    # ankle ram: shin back to the heel
    C = lerp(knee, ankle, 0.48) + bs * 2.8
    D = ankle + (-3.4, -1.0, 0)
    g.cyl(C, C - bs * 1.7, 0.45, M_DIRON, seg=6)
    ram(rm, C, D, 0.5)


# ---------------------------------------------------------------- arms and hands
def arm(G, key, sh, elbow, wrist, s, P, ram_side="back"):
    """Upper arm with a triceps ram on a lever, elbow gear, a gauntlet with a heat conduit."""
    g, rm = G[key], G[key + ".ram"]
    sh, elbow, wrist = arr(sh), arr(elbow), arr(wrist)
    g.ell(sh, (2.4, 2.4, 2.4), M_DIRON)
    block(g, sh, elbow, (2.6, 2.6), (2.4, 2.4), M_DIRON)
    block(g, lerp(sh, elbow, 0.32), lerp(sh, elbow, 0.86), (2.8, 1.0), (2.4, 1.0), P, off=(0, 0, 1.7 * s))
    axle(g, elbow, 1.6, 3.2, s)
    gear(g, elbow + (0, 0, 1.6 * s), 1.3, s, teeth=8)
    Rf = block(g, elbow, wrist, (3.2, 3.2), (4.0, 3.8), P)                                      # gauntlet
    block(g, lerp(elbow, wrist, 0.78), wrist, (4.5, 4.3), (4.5, 4.3), M_DIRON)                  # cuff
    conduit(g, lerp(elbow, wrist, 0.22) + (0, 0, 2.3 * s), lerp(elbow, wrist, 0.7) + (0, 0, 2.3 * s), r=0.4)
    rivets(g, [lerp(elbow, wrist, t) + Rf @ arr((1.75, 0, 0)) for t in (0.3, 0.55)])
    # triceps: a ram along the back of the upper arm to a lever on the outside of the elbow
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
        A = lerp(sh, elbow, 0.4) + nb * 2.2
        B = elbow + unit(out * 0.6 + nb) * 2.7
        g.cyl(A, A - nb * 1.2, 0.45, M_DIRON, seg=6)
        g.cyl(elbow, B, 0.65, M_IRON, seg=6)
    else:                        # a raised, nearly straight arm: biceps ram under the arm
        nf = -nb - F * (-nb @ F)
        nf[2] = 0.0
        nf = unit(nf)
        A = lerp(sh, elbow, 0.45) - nb * 2.2
        B = lerp(elbow, wrist, 0.45) + nf * 2.5
        g.cyl(A, A + nb * 1.2, 0.45, M_DIRON, seg=6)
        g.cyl(B, B - nf * 1.3, 0.45, M_DIRON, seg=6)
    ram(rm, A, B, 0.6)
    return wrist


def fist(G, key, wrist, along, grip, P):
    """A gauntleted hand closed around a haft along `grip`: palm, four knuckles, a thumb, a guard."""
    g = G[key]
    w = arr(wrist)
    d, gr = unit(along), unit(grip)
    gr = unit(gr - d * (gr @ d))
    side = np.cross(d, gr)
    R = np.column_stack([d, gr, side])
    c = w + d * 1.6
    g.box(c, (3.0, 3.2, 3.0), M_IRON, R)
    for i in range(4):
        g.box(c + d * 1.0 + gr * (-1.2 + i * 0.8) + side * 1.2, (1.0, 0.7, 1.1), M_DIRON, R)
    g.box(c - side * 1.25 + d * 0.5, (1.2, 1.2, 0.9), M_DIRON, R)
    g.box(c - d * 0.2 + side * 1.6, (2.4, 2.8, 0.4), P, R)                                   # knuckle guard
    return c


# ---------------------------------------------------------------- weapons
def maul(G, hand, u, P, t_fwd, reach):
    """Steam maul: haft with a feed line, head with a hot striking face and a steam ram at the back."""
    g = G["hammer"]
    hand, u = arr(hand), unit(u)
    butt, top = hand - u * 1.3, hand + u * reach
    g.cyl(butt, top, 0.7, M_DIRON, seg=6)
    g.cyl(butt - u * 0.5, butt, 0.95, M_IRON, seg=6)
    for k in (reach - 5.0, reach - 2.4):
        p = hand + u * k
        g.cyl(p, p + u * 0.8, 1.0, M_IRON, seg=6)
    R, _ = basis(top - u, top + u, t_fwd)
    side = R[:, 2]
    g.cyl(hand + u * 3.2 + side * 1.0, top + u * 0.3 + side * 1.0, 0.35, M_HOSE, seg=5)        # feed line
    hc = top + u * 2.4
    at = lambda x, y=0.0, z=0.0: hc + R @ arr((x, y, z))
    g.box(hc, (8.4, 4.6, 4.6), M_IRON, R)
    g.box(hc, (2.0, 5.2, 5.2), P, R)
    g.box(at(4.5), (0.8, 5.0, 5.0), M_DIRON, R)
    g.box(at(5.0), (0.3, 4.0, 4.0), emissive("fire", 9, 0.5), R)                                # hot striking face
    g.cyl(at(-4.2), at(-6.2), 1.6, M_DIRON, seg=10)                                              # steam ram housing
    g.cyl(at(-6.2), at(-6.6), 1.9, M_IRON, seg=10)
    g.cyl(at(-6.6), at(-7.6), 0.7, M_STEEL, seg=6)
    for zz in (2.35, -2.35):
        for x in (-2.8, -1.9, 1.9, 2.8):
            g.box(at(x, 0, zz), (0.35, 2.6, 0.15), M_HOLE, R)                                  # vents
        rivets(g, [at(0, dy, zz * 1.13) for dy in (-1.4, 1.4)])
    return at(5.2), hc


def shield(G, C, R, P):
    """Tower shield: dark frame, two plates with a seam, vision slit, boss, ground spikes, edge hinges."""
    g = G["shield"]
    C = arr(C)
    at = lambda x, y=0.0, z=0.0: C + R @ arr((x, y, z))
    g.box(C, (1.3, 19.0, 11.0), M_DIRON, R)
    g.box(at(0.45, 4.7), (1.0, 8.8, 9.6), P, R)
    g.box(at(0.45, -4.85), (1.0, 8.4, 9.6), P, R)
    g.box(at(1.0, 6.8), (0.3, 0.9, 5.0), M_HOLE, R)                                               # vision slit
    g.box(at(1.0, 6.8, 2.0), (0.32, 0.6, 0.6), emissive("fire", 3, 0.3), R)                       # an optic behind it
    g.box(at(1.0, -1.5), (0.3, 11.0, 1.0), M_DIRON, R)
    g.ell(at(1.2, -1.5), (0.9, 1.8, 1.8), M_IRON, R)
    for y in (-8.4, -1.0, 1.6, 8.2):
        rivets(g, [at(1.05, y, z) for z in (-4.4, 4.4)])
    for z in (-3.4, 3.4):
        spike(g, at(0, -9.5, z), at(0.4, -11.4, z), 0.7, M_IRON)                                  # ground spikes
    for y in (-6.0, 0.0, 6.0):
        g.cyl(at(-0.2, y - 1.0, -5.7), at(-0.2, y + 1.0, -5.7), 0.6, M_IRON, seg=6)              # edge hinges
    g.box(at(1.0, -6.0, 2.6), (0.2, 2.4, 0.35), M_RUST, R)
    return at(-0.65)


def bracket(G, fist_c, d, back_c, R):
    """Hinged bracket from the gauntlet to the shield's back."""
    g = G["bracket"]
    f = arr(fist_c) + unit(d) * 1.5
    for y in (-2.4, 2.4):
        a = f + R @ arr((0, y * 0.5, 0))
        b = arr(back_c) + R @ arr((0, y, 0))
        g.cyl(a, b, 0.45, M_DIRON, seg=6)
    g.cyl(arr(back_c) + R @ arr((-0.4, -3.2, 0)), arr(back_c) + R @ arr((-0.4, 3.2, 0)), 0.6, M_IRON, seg=8)


# ---------------------------------------------------------------- body
HIP = 21.0
SH = arr((-0.4, 34.6, 8.2))                 # near shoulder; the far one mirrors in z
CY = 31.0


def chest_front(y):
    """x of the painted chest layer's front face at height y."""
    return 0.6 + 3.3 + 1.2 * (y - 27.7) / 7.4


def chest_side(y):
    """z of the dark chest frame's flank at height y."""
    return 3.5 + 3.8 * (y - 26.8) / 8.4


def torso(G, P):
    # pelvis: a gearbox with a centre plate
    pl = G["pelvis"]
    tbox(pl, (-0.2, HIP + 1.4, 0), (5.4, 7.4), (6.0, 8.4), 3.2, M_DIRON)
    tbox(pl, (3.15, HIP - 0.4, 0), (0.9, 2.4), (1.1, 2.8), 3.4, P, rot_z(-0.2))
    pl.box((2.7, HIP + 1.4, 0), (0.6, 1.0, 3.0), M_DIRON)
    # waist: an open spine — rings with the furnace showing between them, rams and cables
    sp = G["spine"]
    for i, y in enumerate((24.0, 25.2, 26.4)):
        sp.cyl((-0.8, y, 0), (-0.8, y + 0.9, 0), 2.5 + 0.15 * i, M_DIRON, seg=10)
        sp.cyl((-0.8, y + 0.9, 0), (-0.8, y + 1.2, 0), 2.0, emissive("fire", 6, 0.35), seg=10)
    for zz in (3.0, -3.0):
        ram(sp, (0.6, 23.6, zz), (0.9, 27.6, zz), 0.5)
    for z in (-0.8, 0.8):
        sp.cyl((2.5, 23.6, z), (3.1, 27.4, z), 0.45, M_HOSE, seg=5)
    # chest: a V-shaped furnace — dark frame, painted shell, breastplate, grate, gauges, fins
    ch = G["chest"]
    tbox(ch, (0.0, CY, 0), (7.0, 7.0), (9.6, 14.6), 8.4, M_DIRON)
    tbox(ch, (0.6, CY + 0.4, 0), (6.6, 6.4), (9.0, 13.8), 7.4, P)
    for y0, y1, w0, w1 in ((32.0, 34.9, 9.6, 12.4), (28.0, 29.0, 4.0, 4.6)):
        f0, f1 = chest_front(y0), chest_front(y1)
        tbox(ch, ((f0 + f1) / 2 + 0.25, (y0 + y1) / 2, 0), (0.6, w0), (0.6, w1), y1 - y0, P,
             rot_z(-np.arctan2(f1 - f0, y1 - y0)))                                              # breastplate bands
    fy = CY - 0.6
    fx = chest_front(fy)
    ch.box((fx + 0.3, fy, 0), (1.2, 4.4, 5.6), M_DIRON)                                         # furnace mouth
    ch.ell((fx + 0.5, fy, 0), (0.6, 1.9, 2.4), emissive("fire", 13, 0.7))
    for z in (-1.8, -0.6, 0.6, 1.8):
        ch.box((fx + 1.05, fy, z), (0.4, 4.2, 0.4), M_DIRON)
    ch.box((fx + 1.05, fy + 2.3, 0), (0.6, 0.5, 5.8), M_IRON)
    for y in (33.6,):
        rivets(ch, [(chest_front(y) + 0.55, y, z) for z in (-4.6, -2.3, 0, 2.3, 4.6)])
    g = arr((chest_front(32.6) + 0.55, 32.6, 3.4))                                             # pressure gauge
    ch.cyl(g - (0.3, 0, 0), g + (0.4, 0, 0), 1.0, M_STEEL, seg=10)
    ch.ell(g + (0.45, 0, 0), (0.15, 0.75, 0.75), M_GLASS)
    ch.box((chest_front(32.4) + 0.6, 32.4, -3.4), (0.3, 1.1, 2.2), M_PLATE)                    # serial plate
    for z, lamp in ((-2.0, LAMP_G), (-1.2, emissive("fire", 3, 0.4))):
        ch.ell((chest_front(26.9) + 0.3, 27.6, z), (0.3, 0.3, 0.3), lamp)                         # indicator lamps
    for y in (28.0, 29.2, 30.4, 31.6):                                                          # cooling fins on the flanks
        for s in (1, -1):
            ch.box((-0.6, y, s * (chest_side(y) + 0.42)), (4.2, 0.35, 0.9), M_IRON)
    # back: a boiler with rust bands, a fan housing, a valve wheel on the near end cap
    bo = G["boiler"]
    bo.cyl((-5.2, 30.5, -4.4), (-5.2, 30.5, 4.4), 3.0, M_IRON, seg=14)
    for z in (-3.0, 2.4):
        bo.cyl((-5.2, 30.5, z), (-5.2, 30.5, z + 0.6), 3.25, M_RUST, seg=14)
    bo.cyl((-7.9, 29.8, 0), (-9.0, 29.8, 0), 2.0, M_DIRON, seg=12)
    for a in (0.0, np.pi / 3, 2 * np.pi / 3):
        bo.box((-9.05, 29.8, 0), (0.2, 3.6, 0.35), M_STEEL, rot_x(a))
    bo.ell((-9.1, 29.8, 0), (0.25, 0.6, 0.6), M_IRON)
    wc = arr((-5.2, 30.5, 4.4))
    bo.cyl(wc, wc + (0, 0, 0.9), 0.35, M_STEEL, seg=6)
    for i in range(8):
        a0, a1 = 2 * np.pi * i / 8, 2 * np.pi * (i + 1) / 8
        p0 = wc + (np.cos(a0) * 1.5, np.sin(a0) * 1.5, 0.9)
        p1 = wc + (np.cos(a1) * 1.5, np.sin(a1) * 1.5, 0.9)
        bo.cyl(p0, p1, 0.25, M_RUST if i % 2 else M_IRON, seg=5)
    for a in (0.0, np.pi / 2):
        bo.box(wc + (0, 0, 0.9), (3.0, 0.3, 0.3), M_IRON, rot_z(a))
    st = G["stacks"]
    for z, h in ((2.2, 8.0), (-2.2, 6.4)):
        b0 = arr((-6.0, 32.6, z))
        top = b0 + (-0.8, h, 0)
        st.cyl(b0, top, 1.0, M_DIRON, seg=8)
        st.cyl(top, top + (0, 0.7, 0), 1.4, M_IRON, seg=8)
        st.cyl(lerp(b0, top, 0.5), lerp(b0, top, 0.5) + (0, 0.5, 0), 1.25, M_RUST, seg=8)
        for i, d in enumerate(((0.0, 2.4, 0), (-1.2, 4.8, 0.4))):
            st.ell(top + arr(d), (1.5 + i * 0.8, 1.2 + i * 0.6, 1.3 + i * 0.6), M_PUFF)
    ho = G["hose"]
    pts = [arr(p) for p in ((-5.0, 32.4, 4.0), (-6.0, 34.6, 7.2), (-2.6, 35.0, 8.8))]
    for p0, p1 in zip(pts[:-1], pts[1:]):
        ho.cyl(p0, p1, 0.55, M_HOSE, seg=6)
    # neck and helm: gorget, a neck of rings, cables, a helm with twin optics and ear vents
    hd = G["head"]
    tbox(hd, (0.4, 35.6, 0), (6.6, 8.0), (4.6, 5.4), 1.6, M_DIRON)
    hd.cyl((0.6, 35.6, 0), (1.6, 38.6, 0), 1.3, M_DIRON, seg=8)
    for i in range(3):
        hd.cyl((0.8 + 0.3 * i, 36.3 + i * 0.8, 0), (0.8 + 0.3 * i, 36.7 + i * 0.8, 0), 1.6, M_STEEL, seg=8)
    for z in (-1.0, 1.0):
        hd.cyl((-0.4, 38.5, z), (-2.2, 35.6, z * 1.6), 0.4, M_HOSE, seg=5)
    hc = arr((2.0, 41.0, 0))
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
    # pauldrons
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pd = G[key]
        c = SH * (1, 1, s) + (0, 1.0, 0)
        pd.ell(c, (3.8, 2.4, 3.2), P)
        tbox(pd, c + (0, -1.8, 0.7 * s), (5.6, 2.6), (6.4, 3.0), 1.4, P, rot_x(-0.35 * s))
        pd.ell(c + (0, 0.8, 0), (3.0, 1.2, 2.6), M_DIRON)
        rivets(pd, [c + (x, 1.4, 2.3 * s) for x in (-1.8, 0.0, 1.8)])
        pd.box(c + (0.4, -0.6, 3.1 * s), (2.2, 1.2, 0.2), M_PLATE)


def guard_parts(pose="idle", P=None):
    P = Mat(PAINT) if P is None else P
    atk = pose == "attack"
    G = Parts()
    leg(G, "leg_n", (0.4, HIP, 3.6), (3.4, 11.6, 4.0), (2.6, 3.3, 4.2), 1, P)
    leg(G, "leg_f", (-0.8, HIP, -3.6), (-1.2, 11.6, -4.2), (-4.4, 3.3, -4.4), -1, P)
    torso(G, P)
    far = SH * (1, 1, -1)
    if not atk:
        # the maul carried on the shoulder: the haft rests on top of the pauldron, head behind
        el = SH + (1.2, -7.2, 1.8)
        w = arm(G, "arm_n", SH, el, SH + (5.4, 0.0, 1.4), 1, P)
        rest = arr((-0.6, 39.55, 8.6))
        hand = fist(G, "hand_n", w, w - el, rest - w, P)
        maul(G, hand, rest - hand, P, (0, 1, 0), reach=12.0)
        elf = far + (0.6, -7.6, -1.4)
        w = arm(G, "arm_f", far, elf, far + (5.0, -9.6, -1.8), -1, P)
        fc = fist(G, "hand_f", w, w - elf, (0, 1, 0), P)
        R = rot_y(0.5)
        back = shield(G, fc + R @ arr((1.5 + 1.8 + 0.65, 0, 0)), R, P)
        bracket(G, fc, w - elf, back, R)
    else:
        el = SH + (4.8, -0.4, 1.4)
        w = arm(G, "arm_n", SH, el, SH + (10.4, 0.2, 1.0), 1, P, ram_side="front")
        u = unit(arr((0.56, -0.83, 0)))
        hand = fist(G, "hand_n", w, w - el, u, P)
        face, _ = maul(G, hand, u, P, (0.83, 0.56, 0), reach=13.0)
        sp = G["sparks"]
        for i, dd in enumerate(((1.0, 0.0, 0.0), (2.4, 1.4, 0.8), (2.0, -1.2, -0.9), (3.4, 0.4, 0.2))):
            sp.ell(face + unit(arr((0.83, 0.56, 0))) * dd[0] + arr((0, dd[1], dd[2])), (0.9 - 0.15 * i,) * 3,
                   emissive("fire", 10 if i == 0 else 0, 0.8))
        elf = far + (1.6, -7.4, -1.4)
        w = arm(G, "arm_f", far, elf, far + (6.4, -8.6, -1.8), -1, P)
        fc = fist(G, "hand_f", w, w - elf, (0, 1, 0), P)
        R = rot_y(0.3)
        back = shield(G, fc + R @ arr((1.5 + 1.8 + 0.65, 0, 0)), R, P)
        bracket(G, fc, w - elf, back, R)
        for k in list(G):
            if not k.startswith("leg_"):
                G[k] = pivot(G[k], rot_z(-0.14), (0, HIP, 0))
    return G


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
    w, h = int(64 * k), int(62 * k)
    ox, oy = int(28 * k), int(56 * k)
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
    d.text((24, 12), "Проба 2: Страж — человекоподобная машина, технологичнее, без пересечений", font=ft, fill=(236, 226, 200))
    d.text((24, 52), "Крупно — покой и атака. Внизу — в размере боя: старый Страж, новый, и рой для масштаба.",
           font=fr, fill=(190, 182, 164))
    for x, t in ((110, "было"), (300, "стало · покой"), (470, "стало · атака"), (670, "рабочая и солдат роя")):
        d.text((x * S - d.textlength(t, font=fr) / 2, (by + 10) * S), t, font=fr, fill=(226, 186, 106))
    img.save(out("humanoid_trial.png"))
    print(img.size)
