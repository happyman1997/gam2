"""Trial: one Foundry golem (the Guard) rebuilt as a humanoid machine.

Human build — feet, knees, hips, a waist, a chest, shoulders, elbows, hands, a head on a neck —
but every part is a mechanism: joints are axles, the waist is an open spine of rings and rods,
pistons drive knees and elbows, the chest is a furnace with a grate, a boiler rides on the back.

    python3 tools/sprites/humanoid.py      -> out/humanoid_trial.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import (M_IRON, M_DIRON, M_STEEL, M_RUST, M_HOSE, M_GLASS, M_PLATE, M_HOLE, M_SMOKE,
                    emissive, spike, tbox, pivot, STYLE1)
from golem7 import M_PUFF

PAINT = ramp("#0e1218", "#1c2430", "#2e3a4a", "#4a5a6e", "#7a8aa0")   # the Guard's blued steel


def basis(a, b, fwd=(1, 0, 0)):
    """Rotation whose local y runs from a to b and local x leans towards `fwd`."""
    ey = np.array(b, float) - np.array(a, float)
    L = np.linalg.norm(ey)
    ey /= L
    f = np.array(fwd, float)
    ex = f - ey * (f @ ey)
    if np.linalg.norm(ex) < 1e-6:
        ex = np.array((0, 0, 1.0)) - ey * ey[2]
    ex /= np.linalg.norm(ex)
    return np.column_stack([ex, ey, np.cross(ex, ey)]), L


def block(m, a, b, bot, top, mat, fwd=(1, 0, 0), off=(0, 0, 0), grow=0.0):
    """A tapered block along a->b; bot/top are (forward, side) sizes at a and b; off shifts it in its own frame."""
    R, L = basis(a, b, fwd)
    c = (np.array(a, float) + np.array(b, float)) / 2 + R @ np.array(off, float)
    tbox(m, c, bot, top, L + grow, mat, R)
    return R


def axle(m, p, r, w, mat=M_DIRON, cap=M_STEEL):
    """A joint: a short drum across the body (along z) with a bright hub on the near face."""
    p = np.array(p, float)
    m.cyl(p - (0, 0, w / 2), p + (0, 0, w / 2), r, mat, seg=10)
    m.cyl(p + (0, 0, w / 2 - 0.1), p + (0, 0, w / 2 + 0.35), r * 0.45, cap, seg=8)


def piston(m, a, b, r=0.75):
    """Cylinder body from a, polished rod to b."""
    a, b = np.array(a, float), np.array(b, float)
    mid = a + (b - a) * 0.55
    m.cyl(a, mid, r, M_DIRON, seg=6)
    m.cyl(mid, b, r * 0.5, M_STEEL, seg=5)
    m.ell(b, (r * 0.6, r * 0.6, r * 0.6), M_DIRON)


def rivets(m, pts, mat=M_STEEL, r=0.32):
    for p in pts:
        m.ell(p, (r, r, r), mat)


# ---------------------------------------------------------------- legs
def leg(m, P, hipj, knee, ankle, near):
    s = 1 if near else -1
    hipj, knee, ankle = (np.array(p, float) for p in (hipj, knee, ankle))
    axle(m, hipj, 2.3, 3.0)
    # thigh: a dark frame with a painted plate on the front and outside
    block(m, hipj, knee, (3.6, 3.4), (4.4, 4.0), M_DIRON)
    block(m, hipj + (0, -0.6, 0), knee + (0, 1.4, 0), (2.4, 4.2), (3.4, 4.8), P, off=(1.2, 0, 0.3 * s))
    # knee: an axle, a cap and a piston behind it
    axle(m, knee, 1.8, 3.6)
    m.ell(knee + (1.9, 0.2, 0), (1.3, 1.9, 1.9), P)
    rivets(m, [knee + (3.1, 0.3, 0)])
    piston(m, hipj + (-2.2, -2.5, 0.0), knee + (-2.3, -3.2, 0.0), 0.8)
    # shin: a heavy greave, wider at the ankle
    block(m, knee, ankle, (4.0, 3.8), (4.8, 4.4), P, off=(0.3, 0, 0))
    block(m, knee + (0, -1.5, 0), ankle + (0, 1.8, 0), (1.2, 2.2), (1.2, 2.6), M_DIRON, off=(2.8, 0, 0))   # shin ridge
    rivets(m, [knee + (2.3, -3.0, 2.1 * s), knee + (2.5, -6.0, 2.3 * s)])
    # ankle and foot: a toe plate, a heel spur
    axle(m, ankle, 1.3, 3.2)
    f = ankle + (1.6, -2.0, 0)
    m.box(f, (7.6, 2.0, 4.4), M_IRON)
    tbox(m, f + (2.6, 0.7, 0), (3.0, 4.6), (2.0, 4.0), 1.2, P)
    m.box(f + (-3.8, -0.2, 0), (1.4, 1.6, 2.6), M_DIRON)
    for z in (-1.4, 0, 1.4):                                   # three toes
        m.box(f + (4.2, -0.3, z), (1.2, 1.4, 1.1), M_DIRON)


# ---------------------------------------------------------------- arms and hands
def arm(m, P, sh, elbow, wrist, near):
    sh, elbow, wrist = (np.array(p, float) for p in (sh, elbow, wrist))
    s = 1 if near else -1
    m.ell(sh, (2.4, 2.4, 2.4), M_DIRON)                       # shoulder ball socket
    block(m, sh, elbow, (2.6, 2.6), (2.4, 2.4), M_DIRON)       # upper arm frame
    block(m, sh + (0, -1.0, 0), elbow + (0, 1.0, 0), (3.2, 1.0), (2.8, 1.0), P, off=(0, 0, 1.6 * s))  # outer plate
    piston(m, sh + (1.4, -1.0, 0.4 * s), elbow + (1.6, -0.6, 0.6 * s), 0.6)                         # biceps ram
    axle(m, elbow, 1.6, 3.4)
    # forearm: a heavy gauntlet, wider at the wrist
    block(m, elbow, wrist, (3.4, 3.2), (4.4, 4.0), P)
    R, _ = basis(elbow, wrist)
    for t in (0.35, 0.7):
        rivets(m, [elbow + (wrist - elbow) * t + R @ np.array((0, 0, 2.2 * s))])
    block(m, elbow + (wrist - elbow) * 0.75, wrist, (4.8, 4.4), (4.8, 4.4), M_DIRON)                # cuff band
    return wrist


def fist(m, wrist, along, grip_axis, P):
    """A gauntleted hand closed around a haft: palm block, four finger segments, a thumb."""
    w = np.array(wrist, float)
    d = np.array(along, float) / np.linalg.norm(along)
    g = np.array(grip_axis, float) / np.linalg.norm(grip_axis)
    c = w + d * 1.6
    R, _ = basis(w, w + d)
    m.box(c, (3.0, 3.0, 3.0), M_IRON, R)
    side = np.cross(d, g)
    for i in range(4):
        p = c + d * 1.2 + g * (-1.35 + i * 0.9)
        m.box(p + side * 0.9, (1.0, 0.85, 1.4), M_DIRON, R)
    m.box(c + side * -1.2 + d * 0.6, (1.0, 1.6, 1.0), M_DIRON, R)
    m.box(c + side * 1.6 - d * 0.4, (2.6, 0.5, 2.6), P, R)       # knuckle guard
    return c


# ---------------------------------------------------------------- weapons
def hammer(m, hand, toward, P, t_fwd, reach=17.0):
    """A long-hafted maul: the haft runs from the fist towards `toward`, the head at that end."""
    hand, toward = np.array(hand, float), np.array(toward, float)
    u = toward / np.linalg.norm(toward)
    butt = hand - u * 4.5
    top = hand + u * reach
    m.cyl(butt, top, 0.7, M_DIRON, seg=6)
    for k in (-3.0, reach - 6.0, reach - 3.0):                   # grip wrap and collars
        p = hand + u * k
        m.cyl(p, p + u * 0.8, 1.0, M_STEEL if k < 0 else M_IRON, seg=6)
    m.ell(butt, (0.95, 0.95, 0.95), M_IRON)
    R, _ = basis(top - u, top + u, t_fwd)
    hc = top + u * 2.4
    m.box(hc, (9.5, 4.8, 4.8), M_IRON, R)
    m.box(hc, (1.8, 5.4, 5.4), P, R)
    m.box(hc + R @ np.array((4.9, 0, 0)), (0.6, 4.0, 4.0), emissive("fire", 9, 0.5), R)   # hot striking face
    m.box(hc + R @ np.array((-4.9, 0, 0)), (0.8, 4.2, 4.2), M_DIRON, R)
    for dy in (-1.5, 1.5):
        rivets(m, [hc + R @ np.array((0, dy, 2.75)), hc + R @ np.array((0, dy, -2.75))])
    return hc + R @ np.array((5.4, 0, 0)), hc + u * 2.4


def tower_shield(m, c, R, P):
    """A tall riveted shield with a sight slot; boss and rim in dark iron."""
    c = np.array(c, float)
    m.box(c, (1.3, 19.0, 11.0), M_DIRON, R)
    m.box(c + R @ np.array((0.45, 0, 0)), (1.0, 17.6, 9.6), P, R)
    m.box(c + R @ np.array((1.0, 5.6, 0)), (0.3, 0.9, 5.4), M_HOLE, R)           # sight slot
    m.box(c + R @ np.array((1.0, -1.2, 0)), (0.3, 10.5, 1.1), M_DIRON, R)        # spine
    m.ell(c + R @ np.array((1.15, -1.2, 0)), (0.9, 1.9, 1.9), M_IRON, R)          # boss
    for y in (-8.2, -2.8, 2.8, 7.8):
        for z in (-4.4, 4.4):
            rivets(m, [c + R @ np.array((1.05, y, z))])
    m.box(c + R @ np.array((1.0, -6.0, 2.6)), (0.2, 2.4, 0.35), M_RUST, R)        # a rust streak


# ---------------------------------------------------------------- body
HIP, KNEE, ANKLE = 21.0, 11.6, 3.3
SH = np.array((-0.4, 34.6, 8.2))           # near shoulder; the far one mirrors in z


def guard(pose="idle", P=None, rest="shoulder"):
    P = Mat(PAINT) if P is None else P
    atk = pose == "attack"
    m = Model()
    # legs: a long stride, the near leg forward, a clear gap between them
    leg(m, P, (0.4, HIP, 3.6), (3.4, KNEE, 4.0), (2.6, ANKLE, 4.2), near=True)
    leg(m, P, (-0.8, HIP, -3.6), (-1.2, KNEE, -4.2), (-4.4, ANKLE, -4.4), near=False)

    up = Model()
    # pelvis: a dark gearbox with small tassets
    tbox(up, (-0.2, HIP + 1.4, 0), (5.4, 7.4), (6.0, 8.4), 3.2, M_DIRON)
    up.cyl((-0.2, HIP + 1.0, 4.3), (-0.2, HIP + 1.0, 4.9), 1.6, M_STEEL, seg=10)    # gear hub on the near hip
    for s in (1, -1):
        tbox(up, (2.0, HIP - 0.2, 3.7 * s), (0.9, 3.6), (1.3, 4.0), 3.2, P, rot_z(-0.3))
    tbox(up, (2.9, HIP + 0.4, 0), (0.9, 2.6), (1.2, 3.0), 2.8, P, rot_z(-0.2))
    # waist: an open spine — stacked rings, rods and cables, much narrower than the chest
    for i, y in enumerate((HIP + 3.0, HIP + 4.3, HIP + 5.6)):
        up.cyl((-0.8, y, 0), (-0.8, y + 0.9, 0), 2.5 + 0.15 * i, M_DIRON, seg=10)
        up.cyl((-0.8, y + 0.9, 0), (-0.8, y + 1.3, 0), 2.0, emissive("fire", 6, 0.35), seg=10)   # the furnace shows through
    for s in (1, -1):
        piston(up, (0.6, HIP + 2.4, 2.4 * s), (1.0, HIP + 7.0, 2.8 * s), 0.55)        # abdominal rams
    for z in (-0.8, 0.8):
        up.cyl((1.6, HIP + 2.4, z), (2.4, HIP + 7.2, z), 0.5, M_HOSE, seg=5)        # belly cables
    # chest: a V-shaped furnace — narrow at the waist, broad at the shoulders
    cy = 31.0
    tbox(up, (0.0, cy, 0), (7.0, 7.0), (9.6, 14.6), 8.4, M_DIRON)
    tbox(up, (0.6, cy + 0.4, 0), (6.6, 6.4), (9.0, 13.8), 7.4, P)
    tbox(up, (3.9, cy + 0.6, 0), (0.9, 5.4), (1.2, 10.4), 6.4, P, rot_z(-0.16))      # breastplate
    up.box((4.4, cy - 0.6, 0), (1.2, 4.6, 5.6), M_DIRON)                               # furnace mouth
    up.ell((4.6, cy - 0.6, 0), (0.7, 2.0, 2.5), emissive("fire", 22, 0.9))
    for z in (-1.8, -0.6, 0.6, 1.8):
        up.box((5.15, cy - 0.6, z), (0.4, 4.4, 0.4), M_DIRON)                          # grate bars
    rivets(up, [(4.9, cy + 3.3, z) for z in (-4.0, -2.0, 0, 2.0, 4.0)] + [(4.0, cy - 3.3, z) for z in (-2.4, 2.4)])
    up.box((4.6, cy + 2.0, -3.4), (0.3, 1.1, 2.2), M_PLATE)                           # serial plate
    g = np.array((4.5, cy + 1.6, 3.6))                                                 # pressure gauge
    up.cyl(g, g + (0.6, 0, 0), 1.1, M_STEEL, seg=10)
    up.ell(g + (0.65, 0, 0), (0.2, 0.8, 0.8), M_GLASS)
    up.box((2.2, cy, 6.3), (0.3, 5.0, 0.15), M_HOLE)                                  # flank seam
    up.box((0.4, cy + 2.2, 6.7), (0.35, 2.2, 0.12), M_RUST)
    # back: a boiler, two stacks, a hose to the near arm
    up.cyl((-5.2, cy - 0.5, -4.4), (-5.2, cy - 0.5, 4.4), 3.0, M_IRON, seg=12)
    for z in (-2.8, 2.8):
        up.cyl((-5.2, cy - 0.5, z), (-5.2, cy - 0.5, z + 0.6), 3.3, M_RUST, seg=12)
    for z, h in ((2.2, 8.0), (-2.2, 6.4)):
        b0 = np.array((-6.0, cy + 1.6, z))
        top = b0 + (-0.8, h, 0)
        up.cyl(b0, top, 1.0, M_DIRON, seg=8)
        up.cyl(top, top + (0, 0.7, 0), 1.4, M_IRON, seg=8)
        for i, d in enumerate(((0.0, 2.4, 0), (-1.2, 4.8, 0.6))):
            up.ell(top + np.array(d), (1.5 + i * 0.8, 1.2 + i * 0.6, 1.4 + i * 0.7), M_PUFF)
    hose = [np.array(p) for p in ((-4.6, cy + 1.0, 4.6), (-3.6, cy - 3.0, 8.4), (-1.6, cy - 5.6, 9.8))]
    for p0, p1 in zip(hose[:-1], hose[1:]):
        up.cyl(p0, p1, 0.55, M_HOSE, seg=6)
    # neck with cables, a helm that stands clear of the shoulders
    tbox(up, (0.4, 35.6, 0), (6.6, 8.0), (4.6, 5.4), 1.6, M_DIRON)                    # gorget
    up.cyl((0.6, 35.6, 0), (1.6, 38.6, 0), 1.3, M_DIRON, seg=8)
    for i in range(3):
        up.cyl((0.8 + 0.3 * i, 36.2 + i * 0.8, 0), (0.8 + 0.3 * i, 36.6 + i * 0.8, 0), 1.6, M_STEEL, seg=8)
    for z in (-1.0, 1.0):
        up.cyl((-0.6, 38.4, z), (-2.4, 35.2, z * 1.8), 0.4, M_HOSE, seg=5)
    hc = np.array((2.0, 41.0, 0))
    tbox(up, hc, (4.8, 4.2), (4.0, 3.6), 5.2, P)                                       # helm
    tbox(up, hc + (0.2, 2.9, 0), (4.0, 3.6), (2.6, 2.0), 1.0, P)                       # rounded crown
    tbox(up, hc + (1.1, -1.4, 0), (2.6, 3.4), (2.0, 3.0), 2.6, M_IRON)                 # jaw
    for i in range(3):
        up.box(hc + (2.15, -2.2 + i * 0.65, 0), (0.3, 0.3, 2.4), M_HOLE)               # breathing slots
    up.box(hc + (2.35, 0.6, 0), (0.5, 0.6, 3.2), emissive("fire", 7, 0.55))           # visor slit
    up.box(hc + (1.9, 1.4, 0), (1.4, 0.7, 4.3), M_DIRON)                               # brow
    up.box(hc + (0.0, 3.6, 0), (4.6, 0.8, 0.8), M_DIRON)                               # low crest
    rivets(up, [hc + (0.2, 0.0, 2.05), hc + (0.2, 0.0, -2.05)])
    # shoulders: layered pauldrons over ball sockets
    for s in (1, -1):
        c = SH * (1, 1, s) + (0, 1.0, 0)
        up.ell(c, (3.8, 2.4, 3.2), P)
        tbox(up, c + (0, -1.8, 0.7 * s), (5.6, 2.6), (6.4, 3.0), 1.4, P, rot_x(-0.35 * s))
        up.ell(c + (0, 0.8, 0), (3.0, 1.2, 2.6), M_DIRON)
        rivets(up, [c + (x, 1.4, 2.3 * s) for x in (-1.8, 0.0, 1.8)])
    up.box(SH + (0.4, 0.4, 3.1), (2.2, 1.2, 0.2), M_PLATE)                             # a number on the near pauldron

    # arms hang clear of the body: hammer in the near (right) hand, shield on the far (left) arm
    far = SH * (1, 1, -1)
    if not atk and rest == "shoulder":     # the maul carried on the shoulder, head behind
        w = arm(up, P, SH, SH + (1.2, -7.2, 1.8), SH + (5.6, -4.4, 1.4), near=True)
        hand = fist(up, w, (0.8, 0.6, 0.0), (-0.75, 0.66, 0.0), P)
        hammer(up, hand, (-0.75, 0.66, 0.0), P, (0, 1, 0), reach=13.0)
        w = arm(up, P, far, far + (0.8, -7.6, -1.6), far + (5.0, -9.6, -2.0), near=False)
        fist(up, w, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), P)
        tower_shield(up, (7.6, 23.2, -10.4), rot_y(0.5), P)
    elif not atk:
        w = arm(up, P, SH, SH + (0.2, -7.4, 1.2), SH + (4.2, -12.6, 0.6), near=True)
        hand = fist(up, w, (0.7, -1.0, -0.1), (0.3, 0.0, 1.0), P)
        dn = np.array((0.30, -1.0, -0.08))
        reach = (hand[1] - 4.8 * 0.95) / 0.95 - 1.9
        hammer(up, hand, dn, P, (1, 0, 0), reach=reach)                                # resting head-down on the ground
        w = arm(up, P, far, far + (0.8, -7.6, -1.6), far + (5.0, -9.6, -2.0), near=False)
        fist(up, w, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), P)
        tower_shield(up, (7.6, 23.2, -10.4), rot_y(0.5), P)
    else:
        w = arm(up, P, SH, SH + (4.0, 0.6, 1.0), SH + (9.0, -3.4, 1.0), near=True)
        hand = fist(up, w, (1.0, -0.5, 0.0), (0.0, 0.0, 1.0), P)
        face, _ = hammer(up, hand, (1.0, -0.62, 0.0), P, (0, 1, 0), reach=14.0)
        w = arm(up, P, far, far + (1.6, -7.6, -1.6), far + (6.0, -8.6, -2.0), near=False)
        fist(up, w, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), P)
        tower_shield(up, (9.0, 24.4, -10.2), rot_y(0.3), P)
        for i, d in enumerate(((1.2, 0.0, 0.0), (2.6, 1.6, 0.8), (2.2, -1.4, -0.9), (3.6, 0.4, 0.2))):
            up.ell(face + np.array(d), (0.9 - 0.15 * i,) * 3, emissive("fire", 10 if i == 0 else 0, 0.8))   # sparks off the face
        up = pivot(up, rot_z(-0.14), (0, HIP, 0))
    m.extend(up)
    return m


def build(pose="idle", k=2.2, P=None, rest="shoulder"):
    w, h = int(64 * k), int(60 * k)
    ox, oy = int(26 * k), int(54 * k)
    spr = rim_light(render(guard(pose, P, rest).scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    from PIL import ImageFont
    from noise import value_noise
    from paths import font, out
    import frames as F
    import swarm1 as W
    S = 2
    WW, HH = 960, 560
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

    put(build("idle", 5.0), 190, 300, 90)
    put(build("attack", 5.0), 560, 300, 90)
    by = 520
    put(F.build("Страж", "idle"), 110, by, 52)
    put(build("idle"), 300, by, 46)
    put(build("attack"), 470, by, 46)
    put(W.build((), 0.0, "idle", False, k=1.0), 640, by, 8)
    put(W.build((), 0.05, "idle", True, k=1.0), 700, by, 12)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 17)
    d.text((24, 12), "Проба: Страж человекоподобный, но машина", font=ft, fill=(236, 226, 200))
    d.text((24, 52), "Крупно — покой и атака. Внизу — в размере боя: старый Страж, новый, и рой для масштаба.",
           font=fr, fill=(190, 182, 164))
    for x, t in ((110, "было"), (300, "стало · покой"), (470, "стало · атака"), (670, "рабочая и солдат роя")):
        d.text((x * S - d.textlength(t, font=fr) / 2, (by + 10) * S), t, font=fr, fill=(226, 186, 106))
    img.save(out("humanoid_trial.png"))
    print(img.size)
