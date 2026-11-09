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
def leg(G, key, hipj, knee, ankle, s, P, th=1.0):
    """th: thickness of the leg (1 — the Guard); lengths come from the joints."""
    g, rm = G[key], G[key + ".ram"]
    hipj, knee, ankle = arr(hipj), arr(knee), arr(ankle)
    T = lambda *v: tuple(x * th for x in v)
    axle(g, hipj, 2.6 * th, 3.4 * th, s)
    gear(g, hipj + (0, 0, 1.7 * th * s), 2.3 * th, s, teeth=11)
    Rt = block(g, hipj, knee, T(3.8, 3.8), T(3.4, 3.4), M_DIRON)                                 # thigh beam
    block(g, lerp(hipj, knee, 0.2), lerp(hipj, knee, 0.86), T(1.4, 4.4), T(1.4, 3.9), P, off=T(2.4, 0, 0))   # front plate
    block(g, lerp(hipj, knee, 0.36), lerp(hipj, knee, 0.84), T(4.0, 1.1), T(3.6, 1.1), P, off=T(0.3, 0, 2.3 * s))  # outer plate
    conduit(g, lerp(hipj, knee, 0.42) + (0, 0, 3.3 * th * s), lerp(hipj, knee, 0.8) + (0, 0, 3.3 * th * s), r=0.5 * th)
    axle(g, knee, 2.2 * th, 4.2 * th, s)
    gear(g, knee + (0, 0, 2.1 * th * s), 1.8 * th, s, teeth=9)
    g.ell(knee + Rt @ arr(T(2.5, 0.0, 0)), T(1.5, 2.2, 2.2), P)                                  # knee cap
    rivets(g, [knee + Rt @ arr(T(3.9, 0.0, 0))], r=0.35 * th)
    Rs = block(g, knee, ankle, T(3.2, 3.2), T(3.2, 3.2), M_DIRON, off=T(-0.3, 0, 0))             # shin beam
    block(g, lerp(knee, ankle, 0.1), lerp(knee, ankle, 0.92), T(4.4, 4.8), T(5.0, 5.4), P, off=T(0.7, 0, 0))   # greave
    block(g, lerp(knee, ankle, 0.16), lerp(knee, ankle, 0.82), T(1.1, 1.4), T(1.1, 1.6), M_DIRON, off=T(3.4, 0, 0))  # ridge
    rivets(g, [lerp(knee, ankle, t) + Rs @ arr(T(1.0, 0, 0)) + (0, 0, 2.75 * th * s) for t in (0.3, 0.55, 0.8)], r=0.35 * th)
    # thigh ram: from the back of the thigh across the knee to the back of the shin, on lugs
    bt, bs = -Rt[:, 0], -Rs[:, 0]
    A = lerp(hipj, knee, 0.3) + bt * 3.5 * th
    B = lerp(knee, ankle, 0.28) + bs * 3.4 * th
    g.cyl(A, A - bt * 2.0 * th, 0.6 * th, M_DIRON, seg=6)
    g.cyl(B, B - bs * 2.0 * th, 0.6 * th, M_DIRON, seg=6)
    ram(rm, A, B, 0.85 * th)
    # ankle and an articulated foot: heel, hinge, toe block, toe cap, claws
    axle(g, ankle, 1.6 * th, 3.8 * th, s)
    g.box(ankle + T(-1.5, -2.1, 0), T(4.4, 2.2, 5.0), M_IRON)
    toe = ankle + T(3.4, -2.4, 0)
    g.cyl(ankle + T(1.0, -2.2, -2.6), ankle + T(1.0, -2.2, 2.6), 1.0 * th, M_DIRON, seg=8)
    g.box(toe, T(5.2, 1.8, 5.2), M_IRON)
    tbox(g, toe + T(0.4, 1.15, 0), T(4.0, 5.2), T(3.0, 4.4), 0.5 * th, P)
    for z in (-1.7, 0, 1.7):
        g.box(toe + T(2.95, -0.2, z), T(1.0, 1.3, 1.2), M_DIRON)
    # ankle ram: shin back to the heel
    C = lerp(knee, ankle, 0.48) + bs * 3.3 * th
    D = ankle + T(-4.0, -1.0, 0)
    g.cyl(C, C - bs * 1.9 * th, 0.5 * th, M_DIRON, seg=6)
    ram(rm, C, D, 0.6 * th)


# ---------------------------------------------------------------- arms and hands
def arm(G, key, sh, elbow, wrist, s, P, ram_side="back", th=1.0, cuff=True):
    """Upper arm with a ram, elbow gear, a heavy gauntlet with a heat conduit. th: thickness."""
    g, rm = G[key], G[key + ".ram"]
    sh, elbow, wrist = arr(sh), arr(elbow), arr(wrist)
    T = lambda *v: tuple(x * th for x in v)
    G[key + ".ball"].ell(sh, T(2.9, 2.9, 2.9), M_DIRON)                                       # shoulder socket
    block(g, sh + unit(elbow - sh) * 2.0 * th, elbow, T(3.4, 3.4), T(3.0, 3.0), M_DIRON)      # from the socket's rim
    block(g, lerp(sh, elbow, 0.32), lerp(sh, elbow, 0.86), T(3.6, 1.1), T(3.0, 1.1), P, off=(0, 0, 2.15 * th * s))
    axle(g, elbow, 2.0 * th, 4.0 * th, s)
    gear(g, elbow + (0, 0, 2.0 * th * s), 1.6 * th, s, teeth=9)
    Rf = block(g, elbow, wrist, T(4.2, 4.2), T(5.4, 5.0), P)                                    # gauntlet
    if cuff:
        block(g, lerp(elbow, wrist, 0.78), wrist, T(6.0, 5.6), T(6.0, 5.6), M_DIRON)            # cuff
    conduit(g, lerp(elbow, wrist, 0.22) + (0, 0, 2.95 * th * s), lerp(elbow, wrist, 0.7) + (0, 0, 2.95 * th * s), r=0.45 * th)
    rivets(g, [lerp(elbow, wrist, t) + Rf @ arr(T(2.35, 0, 0)) for t in (0.3, 0.55)], r=0.35 * th)
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
        A = lerp(sh, elbow, 0.5) + nb * 2.7 * th
        B = elbow + unit(out * 0.6 + nb) * 3.3 * th
        g.cyl(A, A - nb * 1.4 * th, 0.5 * th, M_DIRON, seg=6)
        g.cyl(elbow, B, 0.8 * th, M_IRON, seg=6)
    else:                        # a raised, nearly straight arm: biceps ram under the arm
        nf = -nb - F * (-nb @ F)
        nf[2] = 0.0
        nf = unit(nf)
        A = lerp(sh, elbow, 0.72) - nb * 2.7 * th
        B = lerp(elbow, wrist, 0.62) + nf * 3.3 * th
        g.cyl(A, A + nb * 1.4 * th, 0.5 * th, M_DIRON, seg=6)
        g.cyl(B, B - nf * 1.4 * th, 0.5 * th, M_DIRON, seg=6)
    ram(rm, A, B, 0.75 * th)
    return wrist


def hand_frame(along, grip, s):
    """Axes of a fist holding a haft along `grip`: h — from the wrist to the knuckles (as close to the
    forearm as the grip allows), u — the haft, n — the back of the hand, facing outwards."""
    d, u = unit(along), unit(grip)
    h = unit(d - u * (d @ u))
    n = np.cross(h, u)
    if n[2] * s < 0:
        n = -n
    return h, u, n


def fist(G, key, wrist, along, grip, s, P, th=1.0):
    """A gauntleted hand closed round a haft. The haft runs through the fist from the thumb to the
    little finger; four finger rolls wrap its front, the fingertips tuck in on the inner side, the thumb
    closes over it, a riveted plate guards the back of the hand. Returns the grip point and the axes."""
    g = G[key]
    W = arr(wrist)
    h, u, n = hand_frame(along, grip, s)
    R = np.column_stack([h, u, n])
    T = lambda *v: tuple(x * th for x in v)
    Gp = W + h * 2.4 * th
    g.ell(W + unit(along) * 0.3 * th, T(1.8, 1.8, 1.8), M_DIRON)                              # wrist joint
    g.box(Gp + (-h * 1.7 + n * 0.3) * th, T(1.6, 3.4, 3.0), M_IRON, R)                         # palm
    g.box(Gp + (h * 0.3 + n * 0.35) * th, T(3.0, 3.9, 3.1), M_IRON, R)                         # the closed fist
    for i in range(4):                                                                         # fingers round the haft
        p = Gp + u * (-1.5 + i * 1.0) * th
        g.box(p + (h * 2.0 + n * 0.2) * th, T(1.0, 0.78, 3.4), M_IRON, R)                     # rolls over the front
        g.box(p + (h * 1.2 - n * 1.5) * th, T(1.6, 0.74, 0.7), M_DIRON, R)                    # tips on the inner side
        g.box(p + (h * 1.25 + n * 2.15) * th, T(1.3, 0.8, 0.75), P, R)                        # knuckle plates
        rivets(g, [p + (h * 1.25 + n * 2.55) * th], r=0.22 * th)
    g.box(Gp + (u * 2.4 + h * 0.6 - n * 0.4) * th, T(2.8, 1.0, 1.8), M_IRON, R)               # thumb over the haft
    g.box(Gp + (u * 2.4 + h * 1.95 - n * 0.85) * th, T(1.0, 1.0, 1.0), M_DIRON, R)            # thumb tip
    g.box(Gp + (-h * 0.9 + n * 2.05) * th, T(2.4, 3.7, 0.45), P, R)                            # back-of-hand plate
    rivets(g, [Gp + (-h * 0.9 + n * 2.3 + u * dy) * th for dy in (-1.2, 1.2)], r=0.3 * th)
    return Gp, h, u


def grip_on(W, along, target, s, rounds=3, th=1.0):
    """Grip point and haft direction for a fist at W whose haft points at `target`."""
    u = unit(arr(target) - arr(W))
    for _ in range(rounds):
        h, u2, _ = hand_frame(along, u, s)
        Gp = arr(W) + h * 2.4 * th
        u = unit(arr(target) - Gp)
    return u


# ---------------------------------------------------------------- weapons
def maul(G, hand, u, P, t_fwd, reach):
    """Steam maul: haft with a feed line, head with a hot striking face and a steam ram at the back."""
    g = G["hammer"]
    hand, u = arr(hand), unit(u)
    butt, top = hand - u * BUTT, hand + u * reach
    g.cyl(butt, top, 0.85, M_DIRON, seg=6)
    g.cyl(butt - u * 0.6, butt, 1.15, M_IRON, seg=6)
    for k in (2.95, -2.35):                                         # steel grip bands either side of the fist
        p = hand + u * k
        g.cyl(p, p + u * 0.45 * np.sign(k), 1.05, M_STEEL, seg=6)
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


def bracket(G, grip, u, back_c, R):
    """A handle bar through the far fist and two struts to a hinge on the shield's back."""
    g = G["bracket"]
    grip, u, back_c = arr(grip), unit(u), arr(back_c)
    a0, a1 = grip - u * 2.9, grip + u * 2.9
    g.cyl(a0, a1, 0.7, M_IRON, seg=8)
    for a, y in ((a0, -2.9), (a1, 2.9)):
        g.cyl(a, back_c + R @ arr((0, y, 0)), 0.55, M_DIRON, seg=6)
    g.cyl(back_c + R @ arr((-0.45, -3.7, 0)), back_c + R @ arr((-0.45, 3.7, 0)), 0.7, M_IRON, seg=8)


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


UPPER = ("pelvis", "spine", "chest", "boiler", "stacks", "hose", "head", "pauldron_n", "pauldron_f")
LT, LS = 9.75, 7.25              # thigh and shin
LU, LF = 8.0, 9.0                # upper arm and forearm


def ik(a, target, L1, L2, pole):
    """Two-bone chain from a towards target: the middle joint bends towards `pole`. Returns (joint, end)."""
    a, target = arr(a), arr(target)
    v = target - a
    d = min(np.linalg.norm(v), (L1 + L2) * 0.995)
    v = unit(v)
    x = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    hgt = np.sqrt(max(L1 * L1 - x * x, 0.0))
    p = arr(pole) - v * (arr(pole) @ v)
    return a + v * x + unit(p) * hgt, a + v * d


def place_upper(G, R, t, hip=None, keys=None):
    """Lean, twist and lower the whole upper body about the hips; returns the same map for points."""
    piv, t = arr((0, HIP if hip is None else hip, 0)), arr(t)
    for k in (UPPER if keys is None else keys):
        if k in G:
            G[k] = pivot(G[k], R, piv).transformed(I3, t)
    return lambda p: R @ (arr(p) - piv) + piv + t


# Attack poses — the frame shown at the moment a blow lands (Conquest of Elysium swaps idle for attack
# on every hit), so each is the instant of contact, not a stance. The Guard's attack is "slam";
# "sweep" and "ram" are kept as a reserve for other frames and for module attacks.
# hand/shield: wrist targets relative to the shoulder; poles: where the elbow points;
# haft: direction from the fist to the maul head; face: where the striking face looks.
ATTACKS = {
    "slam": dict(name="удар сверху", lean=-0.3, twist=-0.15, t=(1.2, -2.0, 0.0),
                 ankles=((-5.0, 3.6, HZ + 1.0), (6.5, 3.6, -HZ - 0.8)),
                 hand=(8.4, -10.8, -1.3), hand_pole=(0.3, 1.0, 0.8), haft=(0.95, -0.312, 0), face=(-0.312, -0.95, 0),
                 shield=(-5.0, -12.5, -3.0), shield_pole=(0.3, -1.0, -0.6), shield_rot=-2.6, fx="slam", ram="front"),
    "sweep": dict(name="размах понизу", lean=-0.2, twist=-0.32, t=(0.8, -2.4, 0.0),
                  ankles=((2.5, 3.6, HZ + 2.6), (-4.5, 3.6, -HZ - 1.6)),
                  hand=(6.44, -14.04, -6.17), hand_pole=(0.3, 1.0, 0.8), haft=(0.97, -0.214, -0.096), face=(0.004, 0.0, -1.0),
                  shield=(-5.0, -12.5, -3.0), shield_pole=(0.3, -1.0, -0.6), shield_rot=-2.6, fx="sweep", ram="front"),
    "ram": dict(name="удар щитом", lean=-0.22, twist=0.35, t=(1.6, -1.8, 0.0),
                ankles=((-2.0, 3.6, HZ + 1.0), (7.5, 3.6, -HZ - 0.6)),
                hand=(6.4, 0.8, 2.4), hand_pole=(1.4, -7.6, 2.0), haft=None, face=(0.0, 1.0, 0.0), carry=1.0,
                shield=(10.5, -2.0, 3.0), shield_pole=(0.0, -1.0, -0.5), shield_rot=0.0, fx="ram", ram="back"),
    # the same overhead blow against taller enemies (see golems_h bands): the maul out in front, its face
    # coming down into a body about the Guard's own height; held high, driven into the belly of a giant
    "level": dict(name="удар вровень", lean=-0.361, twist=-0.295, t=(1.182, -2.693, 0.0), ankles=((-4.671, 3.6, 5.176), (2.628, 3.6, -5.632)), hand=(10.443, -12.202, 2.505), hand_pole=(0.199, 0.945, 0.258), haft=(0.763, 0.571, -0.303), face=(0.64, -0.734, 0.229), shield=(-5.0, -12.5, -3.0), shield_pole=(0.3, -1.0, -0.6), shield_rot=-2.6, fx="slam", ram="front", ground=False),
    "high": dict(name="удар снизу вверх", lean=-0.375, twist=-0.045, t=(0.67, -0.941, 0.0), ankles=((-1.425, 3.6, 5.111), (5.954, 3.6, -5.487)), hand=(11.415, 3.951, 1.379), hand_pole=(0.654, 0.708, 0.268), haft=(0.339, 0.746, 0.573), face=(0.797, 0.096, -0.597), shield=(-5.0, -12.5, -3.0), shield_pole=(0.3, -1.0, -0.6), shield_rot=-2.6, fx="slam", ram="front", ground=False),
}
BANDS = dict(low="slam", level="level", high="high")
SMEAR = Mat(ramp("#2a2e38", "#4a505e", "#6e7686", "#98a0b2", "#c8ced8"), dither=True)


def smear(m, c, r, a0, a1, plane, width, depth, n=8):
    """A dithered motion trail along an arc of radius r about c: plane 'xy' (an overhead swing) or 'xz' (a sweep)."""
    c = arr(c)
    pt = (lambda a: c + r * arr((np.cos(a), np.sin(a), 0))) if plane == "xy" else \
         (lambda a: c + r * arr((np.cos(a), 0, np.sin(a))))
    for i in range(n):
        t0, t1 = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
        p0, p1 = pt(t0), pt(t1)
        tv = unit(p1 - p0)
        ax = arr((0, 0, 1.0)) if plane == "xy" else arr((0, 1.0, 0))
        R = np.column_stack([tv, ax, np.cross(tv, ax)]) if plane == "xz" else np.column_stack([tv, np.cross(ax, tv), ax])
        k = 0.25 + 0.75 * (i + 1) / n
        size = (np.linalg.norm(p1 - p0) * 1.1, depth * k, width * k) if plane == "xz" else (np.linalg.norm(p1 - p0) * 1.1, width * k, depth * k)
        m.box((p0 + p1) / 2, size, SMEAR, R)


ATTACK = "slam"                  # what pose="attack" means


def pose_parts(A, P=None, fx=True):
    """Build the Guard from a pose given as numbers (see ATTACKS). Returns the parts and where things are."""
    P = Mat(PAINT) if P is None else P
    G = Parts()
    torso(G, P)
    far = SH * (1, 1, -1)
    X = place_upper(G, rot_z(A["lean"]) @ rot_y(A["twist"]), A["t"])
    for key, hip, ank, s in (("leg_n", (0.4, HIP, HZ), A["ankles"][0], 1), ("leg_f", (-0.8, HIP, -HZ), A["ankles"][1], -1)):
        h = X(hip)
        kn, an = ik(h, ank, LT, LS, (1.0, 0.25, 0.0))
        leg(G, key, h, kn, an, s, P)
    sh, fs = X(SH), X(far)
    c = float(A.get("carry", 0.0))                       # carried (1): the arm and maul turn with the body
    Rb = rot_z(A["lean"]) @ rot_y(A["twist"])
    body = lambda v: arr(v) * (1 - c) + (Rb @ arr(v)) * c
    el, w = ik(sh, sh + body(A["hand"]), LU, LF, body(A["hand_pole"]))
    arm(G, "arm_n", sh, el, w, 1, P, ram_side=A.get("ram", "back"))
    hand, _, u = fist(G, "hand_n", w, w - el, unit(body(A["haft"])), 1, P)
    face, hc = maul(G, hand, u, P, body(A["face"]), reach=13.0)
    elf, wf = ik(fs, fs + arr(A["shield"]), LU, LF, A["shield_pole"])
    arm(G, "arm_f", fs, elf, wf, -1, P)
    fc, hf, uf = fist(G, "hand_f", wf, wf - elf, (0, 1, 0), -1, P)
    R = rot_y(A["shield_rot"])
    sc = fc + R @ arr((SHIELD_GAP + 0.75, 0, 0))
    back = shield(G, sc, R, P)
    bracket(G, fc, uf, back, R)
    tf = unit(body(A["face"]) - u * (body(A["face"]) @ u))
    info = dict(sh=sh, hc=hc, face=face, tf=tf, u=u, sc=sc, R=R, fs=fs)
    if fx:
        impact(G["fx"], A, A.get("ft", 0.0), info)
    return G, info


def impact(fx, A, ft, info):
    """Effects of the blow landing. ft = 0 at the instant of contact, 1 a moment later (flash gone,
    sparks flown further, dust spread)."""
    sh, hc, face, tf, u, sc, R = (info[k] for k in ("sh", "hc", "face", "tf", "u", "sc", "R"))
    near = ft < 0.5
    spread, grow = 1.0 + 1.2 * ft, 1.0 + 0.5 * ft
    if A["fx"] in ("slam", "sweep"):
        for i, d in enumerate((9.6, 11.2, 13.2)):                          # the steam ram fires: a jet out of the back
            fx.ell(hc - tf * (d + 2.0 * ft), (1.3 + 0.6 * i,) * 3 * np.array(grow), M_PUFF)
        for i, d in enumerate(((1.2, 0.0, 0.0), (2.4, 1.8, 1.4), (2.0, -1.6, -1.2), (3.6, 0.6, -0.4), (1.6, 2.6, -2.0))):
            if i == 0 and not near:
                continue
            fx.ell(face + tf * d[0] * spread + arr((0, d[1], d[2])) * (0.6 if i else 0) * spread, ((0.75 - 0.08 * i) / grow,) * 3,
                   emissive("fire", 16 if i == 0 else 4, 0.85))
    if A["fx"] == "slam" and not A.get("ground", True):      # into a body: a flash, armour chips, no dust
        if near:
            fx.ell(face + tf * 0.6, (1.4, 2.2, 2.2), emissive("fire", 22, 0.9))
        for i, d in enumerate(((1.6, 2.0, 1.4), (1.2, -2.2, -1.2), (2.4, 0.6, -2.0))):
            fx.box(face + tf * d[0] * spread + arr((0, d[1], d[2])) * spread - (0, 1.5 * ft, 0), (0.8, 0.7, 0.8), M_IRON,
                   rot_z(0.7 + i + 2.0 * ft))
    elif A["fx"] == "slam":       # grit and dust where the blow lands
        if near:
            fx.ell(face + tf * 0.6, (1.4, 2.2, 2.2), emissive("fire", 22, 0.9))                 # the flash of contact
        g = arr((face[0], 0.3, face[2]))
        for i, d in enumerate(((-3.0, 1.4, 2.4), (3.2, 1.6, 2.0), (0.5, 2.0, -2.6))):
            fx.ell(g + arr(d) * spread, (2.0 + 0.3 * i, 1.3, 1.7) * np.array(grow), M_PUFF)
        for d in ((2.6, 3.4, 1.6), (-2.2, 4.2, -1.0), (3.8, 2.0, -1.8)):
            fx.box(g + arr(d) * (1.0 + 1.6 * ft), (0.8, 0.7, 0.8), M_IRON, rot_z(0.7 + 2.0 * ft))
    elif A["fx"] == "sweep":      # dust kicked up behind the low blow
        if near:
            fx.ell(face + tf * 0.6, (1.4, 2.2, 2.2), emissive("fire", 20, 0.9))                 # the flash of contact
        for i, d in enumerate(((-2.0, -2.4, 3.0), (-5.0, -2.6, 5.0), (-8.5, -2.8, 7.0))):
            fx.ell(arr((hc[0], 0.0, hc[2])) + arr((d[0], 1.2, d[2])) * np.array((1, 1, spread)), (2.0 + 0.4 * i, 1.2, 1.8) * np.array(grow), M_PUFF)
    elif A["fx"] == "ram":        # the shield's face strikes: a flash, sparks, dust
        front = sc + R @ arr((1.6, 0, 0))
        if near:
            fx.ell(front + R @ arr((0.9, 1.5, 0)), (1.4, 3.0, 3.0), emissive("fire", 20, 0.85))
        for i, d in enumerate(((2.6, 5.0, 2.6), (3.4, 0.5, -3.2), (2.2, -4.0, 3.4), (4.4, 2.6, 0.0), (3.0, -1.5, -4.8))):
            fx.ell(front + R @ (arr(d) * spread), ((0.6 - 0.06 * i) / grow,) * 3, emissive("fire", 5 if i == 0 else 0, 0.7))
        f = arr(A["ankles"][1]) + arr((2.0, -2.4, 0))
        for i, d in enumerate(((1.5, 1.2, 1.5), (3.2, 1.6, -1.0), (-0.5, 1.0, -2.5), (-3.0, 1.0, 1.0))):
            fx.ell(f + arr(d) * spread, (1.8 + i * 0.3, 1.2, 1.6) * np.array(grow), M_PUFF)


BROKEN = dict(lean=-0.5, twist=0.12, t=(1.4, -8.0, 0.0), ankles=((-5.4, 2.4, HZ + 1.0), (-7.3, 2.4, -HZ - 1.2)),
              hand=(5.0, -16.0, 2.6), hand_pole=(-0.6, 0.0, 1.0), haft=(0.6, -0.2, 0.75), face=(0.0, 1.0, 0.0),
              shield=(3.0, -15.6, -4.5), shield_pole=(0.3, 0.0, -1.0), shield_rot=1.0, fx=None, ram="back")


IDLE_LEGS = (((0.4, HIP, HZ), (3.6, 10.8, HZ + 0.5), (2.8, 3.6, HZ + 0.7), 1),
             ((-0.8, HIP, -HZ), (-1.0, 10.8, -HZ - 0.6), (-4.6, 3.6, -HZ - 0.8), -1))


def guard_idle(P=None, legs=True, weapon=True, near_arm=None):
    """The Guard at rest, and where its parts are (for modules mounted on it). legs/weapon=False leave the legs or
    the maul out, for modules that replace them; near_arm=(elbow, wrist) offsets from the shoulder pose that arm."""
    P = Mat(PAINT) if P is None else P
    G = Parts()
    torso(G, P)
    far = SH * (1, 1, -1)
    info = dict(sh=arr(SH), fs=arr(far), legs=[tuple(arr(v) for v in l[:3]) + (l[3],) for l in IDLE_LEGS])
    if legs:
        for (key, (h, k, a, s)) in zip(("leg_n", "leg_f"), IDLE_LEGS):
            leg(G, key, h, k, a, s, P)
    # the maul carried on the shoulder: the haft rests on top of the pauldron, head behind
    el = SH + (1.4, -7.6, 2.0) if near_arm is None else SH + arr(near_arm[0])
    w = arm(G, "arm_n", SH, el, SH + ((WX, WY, WZ) if near_arm is None else arr(near_arm[1])), 1, P)
    rest = arr((-0.8, RY, 10.4))
    u = grip_on(w, w - el, rest, 1)
    if weapon:
        hand, _, u = fist(G, "hand_n", w, w - el, u, 1, P)
        face, hc = maul(G, hand, u, P, (0, 1, 0), reach=13.0)
        info.update(face=face, hc=hc)
    else:
        hand = w
    info.update(hand=hand, u=u, el=el, w=w)
    elf = far + (0.8, -8.0, -1.6)
    w = arm(G, "arm_f", far, elf, far + (5.8, -10.0, -2.0), -1, P)
    fc, hf, uf = fist(G, "hand_f", w, w - elf, (0, 1, 0), -1, P)
    R = rot_y(0.5)
    sc = fc + R @ arr((SHIELD_GAP + 0.75, 0, 0))
    back = shield(G, sc, R, P)
    bracket(G, fc, uf, back, R)
    info.update(sc=sc, R=R, fc=fc, elf=elf, wf=w)
    return G, info


def guard_parts(pose="idle", P=None):
    P = Mat(PAINT) if P is None else P
    if pose == "idle":
        return guard_idle(P)[0]
    G = Parts()
    if pose == "broken":
        G, info = pose_parts(BROKEN, P, fx=False)
        X = lambda p: rot_z(BROKEN["lean"]) @ rot_y(BROKEN["twist"]) @ (arr(p) - (0, HIP, 0)) + (0, HIP, 0) + arr(BROKEN["t"])
        for i, d in enumerate(((2.0, 33.0, 0.0), (0.5, 37.0, 1.4), (-1.5, 41.5, -0.6))):
            G["fx"].ell(X(d), (2.2 + i * 1.0, 1.8 + i * 0.8, 2.0 + i * 0.9), M_PUFF)
        return G
    G, _ = pose_parts(ATTACKS[ATTACK if pose == "attack" else pose], P)
    return G


WX, WY, WZ, RY = 6.4, 0.8, 2.4, 39.9      # idle: wrist of the carrying arm, height where the haft rests on the pauldron
SHIELD_GAP = 4.6                 # from the grip to the shield's back face
BUTT = 3.2                       # haft beyond the fist on the little-finger side


ALLOWED = [("leg_n", "pelvis"), ("leg_f", "pelvis"), ("leg_n", "leg_n.ram"), ("leg_f", "leg_f.ram"),
           ("spine", "pelvis"), ("spine", "chest"), ("chest", "boiler"), ("chest", "head"),
           ("chest", "pauldron_n"), ("chest", "pauldron_f"),
           ("chest", "arm_n.ball"), ("chest", "arm_f.ball"), ("pauldron_n", "arm_n.ball"), ("pauldron_f", "arm_f.ball"),
           ("arm_n", "arm_n.ball"), ("arm_f", "arm_f.ball"), ("arm_n.ram", "arm_n.ball"), ("arm_f.ram", "arm_f.ball"),
           ("hose", "arm_n.ball"), ("head", "arm_n.ball"), ("head", "arm_f.ball"),
           ("boiler", "stacks"), ("boiler", "hose"), ("hose", "pauldron_n"), ("hose", "arm_n"),
           ("pauldron_n", "arm_n"), ("pauldron_f", "arm_f"), ("arm_n", "arm_n.ram"), ("arm_f", "arm_f.ram"),
           ("arm_n", "hand_n"), ("arm_f", "hand_f"), ("hand_n", "hammer"), ("hand_f", "bracket"),
           ("bracket", "shield"), ("pauldron_n", "pauldron_f"), ("arm_f", "bracket")]


def carry_haft():
    """Haft direction of the maul resting on the shoulder (idle), for poses that keep carrying it."""
    el, w = ik(SH, SH + arr((WX, WY, WZ)), LU, LF, (1.4, -7.6, 2.0))
    return tuple(grip_on(w, w - el, arr((-0.8, RY, 10.4)), 1))


ATTACKS["ram"]["haft"] = carry_haft()


def hit_point():
    """Where the Guard's attack lands (model coordinates, on the ground)."""
    _, info = pose_parts(ATTACKS[ATTACK], fx=False)
    return info["face"] * arr((1, 0, 1))


def guard(pose="idle", P=None):
    return guard_parts(pose, P).model()


def build(pose="idle", k=2.2, P=None, yaw=None):
    w, h = int(82 * k), int(80 * k)
    ox, oy = int(36 * k), int(72 * k)
    opts = dict(STYLE1)
    if yaw is not None:
        opts["yaw"] = yaw
    spr = rim_light(render(guard(pose, P).scaled(k), w, h, ox, oy, **opts), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def check(pose):
    from clipcheck import report
    return report(guard_parts(pose), ALLOWED, skip=("sparks", "fx"))


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
    WW, HH = 960, 640
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

    put(build("idle", 4.6), 220, 380, 92)
    put(build("attack", 4.6), 640, 380, 92)
    by = 590
    put(F.build("Страж", "idle"), 100, by, 52)
    put(build("idle"), 300, by, 46)
    put(build("attack"), 520, by, 46)
    put(W.build((), 0.0, "idle", False, k=1.0), 740, by, 8)
    put(W.build((), 0.05, "idle", True, k=1.0), 800, by, 12)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 21)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 17)
    d.text((24, 12), "Страж — человекоподобная машина: покой и атака", font=ft, fill=(236, 226, 200))
    d.text((24, 52), "Атака — момент удара: молот с плеча по дуге в цель перед собой. Внизу — в размере боя, "
                     "рядом прежний Страж и рой.", font=fr, fill=(190, 182, 164))
    for x, t in ((220, "покой"), (640, "атака · удар сверху")):
        d.text((x * S - d.textlength(t, font=fh) / 2, 410 * S), t, font=fh, fill=(226, 186, 106))
    for x, t in ((100, "было"), (300, "покой"), (520, "атака"), (770, "рабочая и солдат роя")):
        d.text((x * S - d.textlength(t, font=fr) / 2, (by + 12) * S), t, font=fr, fill=(190, 182, 164))
    img.save(out("guard_humanoid.png"))
    print(img.size)
