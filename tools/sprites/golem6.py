"""Modular golem (style 1) where every module has three visible upgrade levels."""
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3

# mature, worked metals: gunmetal, blackened steel, aged brass — no toy orange
IRON2 = ramp("#101114", "#1f2126", "#33363e", "#4f535e", "#7d828f")
DIRON2 = ramp("#09090b", "#131418", "#1f2127", "#30333b", "#4b4f59")
BRASS2 = ramp("#1a100a", "#352214", "#573a22", "#7e5a34", "#ae8a56")
M_IRON = Mat(IRON2)
M_DIRON = Mat(DIRON2)
M_BRONZE = Mat(BRASS2)
M_STEEL = Mat(ramp("#1a1c22", "#3a3e48", "#6a707e", "#a6acb8", "#e2e6ee"))     # polished rods, rivet heads
M_RUST = Mat(ramp("#1a0a06", "#3a160a", "#5e2810", "#82401c", "#a8622e"))
M_HOSE = Mat(ramp("#08080a", "#121216", "#1c1c22", "#2a2a32", "#3e3e48"))
M_GLASS = Mat(ramp("#1e2a26", "#3a524a", "#6a8a7c", "#a8c8b8", "#e8fff4"))
M_PLATE = Mat(ramp("#3a3630", "#5a554a", "#7e786a", "#a6a090", "#cec8b6"))     # stamped serial plate
M_HOLE = Mat([hexc("#07060a")] * 2 + [hexc("#120f18")] * 3)
SMOKE = ramp("#2a2a33", "#3d3d48", "#5a5a66", "#7c7c88", "#a4a4ae")
M_SMOKE = Mat(SMOKE)
GLOW = {"fire": (FIRE, hexc("#ff7a20")), "volt": (VOLT, hexc("#40d8ff"))}

STYLE1 = dict(amb=0.40, dif=0.60, gradient=False, edges=False, outline_tint=0.22)


def emissive(kind, r, k):
    rp, col = GLOW[kind]
    return Mat(rp, emissive=col, glow_r=r, glow_k=k)


def pivot(m, R, p):
    p = np.array(p, float)
    return m.transformed(R, p - R @ p)


def spike(m, base, tip, r=1.0, mat=M_IRON):
    m.cyl(base, tip, r, mat, r1=0.15, seg=6)


def tbox(m, c, bot, top, h, mat, R=I3):
    bx, bz, tx, tz = bot[0] / 2, bot[1] / 2, top[0] / 2, top[1] / 2
    v = [(-bx, -h / 2, -bz), (bx, -h / 2, -bz), (bx, -h / 2, bz), (-bx, -h / 2, bz),
         (-tx, h / 2, -tz), (tx, h / 2, -tz), (tx, h / 2, tz), (-tx, h / 2, tz)]
    c = np.array(c, float)
    m.solid([c + R @ np.array(p) for p in v], [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], mat)


def hip_of(legs):
    return 11 if legs == "tracks" else 17


# ---------------------------------------------------------------- legs
def legs_tracks(m, hip, t):
    for z in (6.5, -6.5):
        m.box((0, 4.5, z), (26, 9, 6), M_DIRON)
    m.box((0, 9, 0), (14, 5, 8), M_IRON)
    for x in (-8, 0, 8):
        m.cyl((x, 4.5, 9.4), (x, 4.5, 10.4), 3.1, M_BRONZE)
        m.cyl((x, 4.5, 10.3), (x, 4.5, 10.6), 1.0, M_DIRON)
    if t >= 2:   # armoured skirts over the treads
        for s in (1, -1):
            m.box((0, 8.0, 10.2 * s), (25, 3.2, 1.0), M_BRONZE)
            for x in (-10, -5, 0, 5, 10):
                m.ell((x, 8.0, 10.8 * s), (0.6, 0.6, 0.4), M_IRON)
    if t >= 3:   # spiked ram
        m.box((14.2, 4.6, 0), (2.4, 7, 17), M_IRON)
        for z in (-5.5, 0, 5.5):
            spike(m, (15.2, 4.6, z), (19.5, 4.2, z), 1.3)


def legs_springs(m, hip, t):
    for z in (-5.5, 5.5):
        knee = np.array((4.5, hip - 7, z))
        ankle = np.array((1.5, 3, z))
        m.ell((0, hip, z), (3, 3, 3), M_IRON)
        m.cyl((0, hip, z), knee, 2.6 if t < 3 else 3.0, M_BRONZE)
        m.cyl(knee, ankle, 0.9, M_DIRON)
        rc = 2.5 if t == 1 else 2.9
        for i in range(5):
            t0 = 0.12 + i * 0.18
            a = knee + (ankle - knee) * t0
            b = knee + (ankle - knee) * (t0 + 0.07)
            m.cyl(a, b, rc, M_IRON)
        m.ell(knee, (2.6, 2.6, 2.6), M_IRON)
        m.box((2.8, 1.5, z), (9, 3, 5), M_IRON)
        if t >= 2:
            m.box(knee + (2.4, 0.5, 0), (1.4, 5.2, 4.6), M_BRONZE)
        if t >= 3:
            for dz in (-1.6, 0, 1.6):
                spike(m, (7, 1.2, z + dz), (10, 0.6, z + dz * 1.3), 0.8)


# ---------------------------------------------------------------- torso, armour, core
def torso(m, hip):
    """A wedge: narrow waist, broad armoured chest."""
    tbox(m, (0, hip + 9, 0), (13.5, 15.5), (16, 19), 18, M_BRONZE)
    tbox(m, (7.4, hip + 10.5, 0), (2.4, 11.5), (3.0, 13.5), 12, M_IRON)
    m.box((0, hip + 3, 0), (16, 2.2, 17), M_DIRON)
    m.box((-0.5, hip + 18.6, 0), (12, 3, 15), M_IRON)


def tech(m, hip, t):
    """What makes a golem read as a machine: rivets, seams, pistons, hoses, stacks, a gauge, a serial plate."""
    for x in (-5, -2.5, 0, 2.5, 5):                          # rivet rows on the flank
        m.ell((x, hip + 15.6, 9.25), (0.45, 0.45, 0.3), M_STEEL)
    for x in (-4, -1, 2, 5):
        m.ell((x, hip + 5.0, 8.3), (0.45, 0.45, 0.3), M_STEEL)
    for y in (hip + 6.0, hip + 14.5):                        # rivets on the chest plate
        for z in (-4.5, 4.5):
            m.ell((8.9, y, z), (0.3, 0.45, 0.45), M_STEEL)
    m.box((-1.6, hip + 10.0, 8.95), (0.35, 11.0, 0.2), M_HOLE)          # panel seams
    m.box((1.5, hip + 11.5, 9.05), (8.5, 0.3, 0.2), M_HOLE)
    for x in (-2.5, 2.5):                                    # rust streaks under the rivets
        m.box((x, hip + 13.9, 9.3), (0.35, 2.6, 0.12), M_RUST)
    m.box((-4.8, hip + 9.0, 9.05), (3.2, 1.7, 0.2), M_PLATE)            # stamped serial plate
    for i in range(3):
        m.box((-5.9 + i * 1.1, hip + 9.0, 9.18), (0.5, 0.8, 0.06), M_HOLE)
    g = np.array((8.85, hip + 16.2, -3.6))                   # a pressure gauge on the chest
    m.cyl(g, g + (0.7, 0, 0), 1.45, M_STEEL, seg=10)
    m.ell(g + (0.75, 0, 0), (0.2, 1.1, 1.1), M_GLASS)
    m.box(g + (0.85, 0.3, 0.35), (0.12, 0.9, 0.18), M_HOLE, rot_x(0.6))
    for s in (1, -1):                                        # shoulder pistons
        a = np.array((-6.2, hip + 18.6, 6.3 * s))
        b = np.array((-3.0, hip + 17.4, 8.9 * s))
        m.cyl(a, b, 0.95, M_DIRON, seg=6)
        m.cyl(b, b + np.array((2.2, -0.6, 1.0 * s)), 0.45, M_STEEL, seg=5)
    hose = [np.array(p) for p in ((-6.0, hip + 14.5, 8.6), (-7.8, hip + 10.0, 10.4), (-6.6, hip + 5.2, 9.4), (-3.4, hip + 3.6, 8.8))]
    for p0, p1 in zip(hose[:-1], hose[1:]):                  # a fuel hose looping down the flank
        m.cyl(p0, p1, 0.75, M_HOSE, seg=6)
    for s, h_ in ((1, 9.5), (-1, 7.5)):                      # exhaust stacks on the back
        b0 = np.array((-6.6, hip + 16.5, 3.6 * s))
        top = b0 + np.array((-0.6, h_, 0))
        m.cyl(b0, top, 1.15, M_DIRON, seg=8)
        m.cyl(top, top + (0, 0.9, 0), 1.6, M_IRON, seg=8)
        m.cyl(b0 + (-0.2, h_ * 0.45, 0), b0 + (-0.25, h_ * 0.45 + 0.7, 0), 1.45, M_RUST, seg=8)


def armour(m, hip, t):
    if t >= 2:   # bolted flank plates
        for s in (1, -1):
            m.box((0, hip + 9.5, 9.5 * s), (12, 10, 1.2), M_IRON)
            for x in (-4.5, 4.5):
                for y in (hip + 6, hip + 13):
                    m.ell((x, y, 10.2 * s), (0.6, 0.6, 0.4), M_BRONZE)
        for x in (-5, 0, 5):
            m.ell((x + 2, hip + 3, 9.8), (0.7, 0.7, 0.5), M_BRONZE)
    if t >= 3:   # heavy chest frame and spiked shoulders
        m.box((9.3, hip + 16, 0), (1.2, 2.2, 14), M_IRON)
        m.box((9.3, hip + 4.6, 0), (1.2, 2.2, 14), M_IRON)
        for s in (1, -1):
            spike(m, (0.5, hip + 18.5, 10.5 * s), (-0.5, hip + 24, 12.5 * s), 1.3)
            spike(m, (3.5, hip + 18, 10.5 * s), (4.5, hip + 22.5, 12 * s), 1.0)


def core(m, hip, kind, t):
    c = np.array((9.9, hip + 10.5, 0))
    sock = (4.4, 5.0, 5.6)[t - 1]
    m.cyl(c + (-1.1, 0, 0), c + (-0.1, 0, 0), sock, M_DIRON)
    r = ((1.6, 3.1, 3.1), (1.9, 3.8, 3.8), (2.2, 4.5, 4.5))[t - 1]
    m.ell(c, r, emissive(kind, (18, 22, 28)[t - 1], (0.75, 0.85, 0.95)[t - 1]))
    if t >= 2:   # cage over the core
        for z in (-2.2, 0, 2.2):
            m.box(c + (1.6, 0, z), (0.6, 9 if t == 2 else 10.5, 0.7), M_IRON)
    if t >= 3:   # vents on the flank breathing the core's light
        for y in (hip + 6.5, hip + 9, hip + 11.5):
            m.box((-2, y, 10.4), (6, 0.8, 0.4), emissive(kind, 0, 0))


# ---------------------------------------------------------------- heads
def head_visor(m, hip, kind, t):
    y = hip + 24
    m.box((2.5, y, 0), (9, 8, 9), M_IRON)
    m.box((1.5, y + 5, 0), (7, 2, 2.6), M_BRONZE)
    m.box((7.2, y + 0.5, 0), (0.8, 1.4, 6.5), emissive(kind, 8 + 3 * (t - 1), 0.5))
    m.box((4.6, y + 3.2, 0), (5.6, 1.4, 9.6), M_DIRON)             # a heavy brow over the slit
    for s in (1, -1):                                               # breathing vents on the jaw
        for i in range(3):
            m.box((6.9, y - 2.4 + i * 0.9, 2.6 * s), (0.4, 0.4, 2.2), M_HOLE)
    if t >= 2:   # armoured cheek plates and a cable to the back
        for s in (1, -1):
            m.box((4.5, y - 1.5, 4.9 * s), (5.5, 4.5, 0.9), M_BRONZE)
        m.cyl((-2.0, y + 1.0, -2.5), (-4.5, y - 3.5, -3.0), 0.6, M_HOSE, seg=5)
    if t >= 3:   # a low crest of short blades
        for x in (-1, 1.5, 4):
            spike(m, (x, y + 3.8, 0), (x - 1.2, y + 6.4, 0), 0.8, M_IRON)


def head_sensor(m, hip, kind, t):
    y = hip + 24
    m.ell((2, y, 0), (5, 4.6, 5), M_IRON)
    lr = (1.8, 2.3, 2.6)[t - 1]
    m.cyl((4, y, 0), (8.6, y, 0), lr + 0.6, M_DIRON)
    eye = emissive(kind, 9 + 2 * t, 0.55)
    m.ell((8.7, y, 0), (0.7, lr, lr), eye)
    m.limb([(-1, y + 4, -2), (-3, y + 10, -3)], 1, M_DIRON, band=3)
    m.ell((-3, y + 10.5, -3), (0.8, 0.8, 0.8), eye)
    if t >= 2:
        m.limb([(-1, y + 4, 2), (-2, y + 12, 3)], 1, M_DIRON, band=3)
        m.ell((-2, y + 12.5, 3), (0.8, 0.8, 0.8), eye)
    if t >= 3:   # extra side lenses and a hood
        for s in (1, -1):
            m.cyl((4, y + 2.6, 3 * s), (6.6, y + 2.6, 3.3 * s), 1.2, M_DIRON)
            m.ell((6.7, y + 2.6, 3.3 * s), (0.5, 1.0, 1.0), eye)
        m.box((4.5, y + 4.6, 0), (6, 1.0, 9), M_BRONZE)


# ---------------------------------------------------------------- arms
def shoulder(m, hip, z):
    m.ell((0.5, hip + 16, z), (4.6, 3.8, 4.2), M_BRONZE)


def far_hammer(m, hip, pose, kind, t):
    z = -12.5
    S = np.array((0.5, hip + 14, z))
    if pose == "idle":
        E, Hn, shaft = np.array((4, hip + 7, z)), np.array((11, hip + 8, z)), np.array((3, 13 + t, 0))
    else:
        E, Hn, shaft = np.array((7, hip + 11, z)), np.array((14, hip + 7, z)), np.array((13 + t, -10, 0))
    m.cyl(S, E, 2.4, M_IRON)
    m.cyl(E, Hn, 2.4, M_IRON)
    sd = shaft / np.linalg.norm(shaft)
    top = Hn + shaft
    m.cyl(Hn - sd * 3, top, 1.1 + 0.2 * (t - 1), M_DIRON)
    R = rot_z(np.arctan2(sd[1], sd[0]) - np.pi / 2)
    hs = ((13, 7, 7), (15, 8, 8), (16.5, 9, 9))[t - 1]
    m.box(top, hs, M_IRON, R)
    band = M_BRONZE if t < 3 else emissive(kind, 9, 0.5)
    m.box(top, (2.6, hs[1] + 0.6, hs[2] + 0.6), band, R)
    if t >= 2:   # spiked striking faces
        for sgn in (1, -1):
            for dy, dz in ((0, 0), (2.2, 2.2), (-2.2, -2.2), (2.2, -2.2), (-2.2, 2.2))[: 1 if t == 2 else 5]:
                b = top + R @ np.array((sgn * hs[0] / 2, dy, dz))
                tip = top + R @ np.array((sgn * (hs[0] / 2 + (3 if t == 2 else 2.4)), dy, dz))
                spike(m, b, tip, 1.1 if t == 2 else 0.9)
    if t >= 3:
        for k in (0.35, 0.65):
            m.cyl(Hn + (top - Hn) * k, Hn + (top - Hn) * (k + 0.05), 1.8, M_BRONZE)
    m.ell(Hn, (2.7, 2.7, 2.7), M_BRONZE)
    shoulder(m, hip, -10.5)


def near_shield(m, hip, pose, kind, t):
    z = 11.5
    dx = 0 if pose == "idle" else -2.5
    S = np.array((0.5, hip + 14, z))
    E = np.array((2 + dx, hip + 7, 13))
    m.cyl(S, E, 2.4, M_IRON)
    R = rot_y(-0.45)
    c = np.array((5 + dx, hip + 8.5 + (1.5 if t == 3 else 0), 15))
    rim = ((13.5, 16.5), (13.5, 16.5), (15.5, 21))[t - 1]
    m.box(c, (rim[0], rim[1], 1.2), M_BRONZE, R)
    m.box(c + R @ np.array((0, 0, 0.7)), (rim[0] - 2, rim[1] - 2, 1.4), M_IRON, R)
    m.ell(c + R @ np.array((0, 0, 1.5)), (2.4, 2.4, 1.6), M_BRONZE, R)
    if t >= 2:
        for sx_ in (-1, 1):
            for sy_ in (-1, 1):
                m.ell(c + R @ np.array((sx_ * (rim[0] / 2 - 2), sy_ * (rim[1] / 2 - 2), 1.5)), (0.8, 0.8, 0.6), M_BRONZE, R)
        spike(m, c + R @ np.array((0, 0, 2.6)), c + R @ np.array((0, 0, 6.5 if t == 2 else 8)), 1.3 if t == 2 else 1.6)
    if t >= 3:   # cross emblem
        m.box(c + R @ np.array((0, 0, 1.5)), (1.4, rim[1] - 5, 0.4), M_BRONZE, R)
        m.box(c + R @ np.array((0, 3, 1.5)), (rim[0] - 5, 1.4, 0.4), M_BRONZE, R)
    shoulder(m, hip, 10.5)


def far_cannon(m, hip, pose, kind, t):
    z = -12.5
    back = 0 if pose == "idle" else -3
    R = rot_z(0 if pose == "idle" else 0.08)
    base = np.array((1 + back, hip + 12, z))
    L = (22, 26, 26)[t - 1]
    barrels = [0.0] if t < 3 else [2.4, -2.4]
    rb = 3.0 if t < 3 else 2.4
    for dy in barrels:
        at = lambda x, dy=dy: base + np.array((0, dy, 0)) + R @ np.array((x, 0, 0))
        m.cyl(at(0), at(L), rb, M_IRON)
        bands = (7, 15) if t == 1 else (6, 12, 18)
        for x in bands:
            m.cyl(at(x), at(x + 1.8), rb + 0.6, M_BRONZE)
        if t == 1:
            m.cyl(at(L - 1.5), at(L + 1), rb + 0.7, M_DIRON)
        else:   # muzzle brake with vents
            m.box(at(L + 0.5), (3.2, rb * 2 + 2.2, rb * 2 + 2.2), M_DIRON, R)
            for vy in (-1.2, 1.2):
                m.box(at(L + 0.5) + np.array((0, vy * rb, 0)), (1.2, 0.7, rb * 2 + 2.6), M_HOLE, R)
        m.ell(at(L + (1.1 if t == 1 else 2.15)), (0.3, rb * 0.62, rb * 0.62), M_HOLE, R)
    if t >= 3:   # clamps joining the twin barrels, ammunition drum
        for x in (4, 14):
            m.box(base + R @ np.array((x, 0, 0)), (2.2, 10, 6.6), M_BRONZE, R)
        m.cyl(base + (-1, 3, -3.8), base + (-1, 3, -7.8), 4.2, M_BRONZE, seg=10)
    if pose == "attack":
        fl = emissive(kind, 20, 0.9)
        for dy in barrels:
            tip = base + np.array((0, dy, 0)) + R @ np.array((L + 4, 0, 0))
            m.ell(tip, (4.5, 3.6, 3.6), fl)
        m.ell(base + R @ np.array((L - 3, 5, 1)), (3.2, 2.6, 2.6), M_SMOKE)
    shoulder(m, hip, -10.5)


def near_claw(m, hip, pose, kind, t):
    z = 11.5
    S = np.array((0.5, hip + 14, z))
    E, Hn = (np.array((2, hip + 6, 13)), np.array((6, hip + 3, 13.5))) if pose == "idle" else \
            (np.array((1, hip + 7, 13)), np.array((4, hip + 5, 13.5)))
    m.cyl(S, E, 2.3, M_IRON)
    m.cyl(E, Hn, 2.1, M_IRON)
    k = (1.0, 1.4, 1.7)[t - 1]
    fingers = ((3, -2.2, 1.2), (3.6, -0.6, 0), (3, -2.2, -1.2))
    if t >= 3:
        fingers = fingers + ((2.4, -3.2, 0),)
    for d in fingers:
        m.cyl(Hn, Hn + np.array(d) * k, 0.9 + 0.15 * (t - 1), M_IRON, r1=0.25, seg=5)
    if t >= 2:
        m.cyl(E + (Hn - E) * 0.3, E + (Hn - E) * 0.75, 2.7, M_BRONZE)
    shoulder(m, hip, 10.5)


LEGS = dict(tracks=legs_tracks, springs=legs_springs)
HEADS = dict(visor=head_visor, sensor=head_sensor)
FAR = dict(hammer=far_hammer, cannon=far_cannon)
NEAR = dict(shield=near_shield, claw=near_claw)


def model(cfg, lv, pose="idle"):
    """cfg: (legs, head, core, far, near); lv: one level for all, or a dict per slot."""
    legs, head, core_, far, near = cfg
    L = lv if isinstance(lv, dict) else {k: lv for k in ("legs", "head", "core", "far", "near", "armour")}
    hip = hip_of(legs)
    lower = Model()
    LEGS[legs](lower, hip, L["legs"])
    up = Model()
    FAR[far](up, hip, pose, core_, L["far"])
    torso(up, hip)
    armour(up, hip, L["armour"])
    core(up, hip, core_, L["core"])
    HEADS[head](up, hip, core_, L["head"])
    NEAR[near](up, hip, pose, core_, L["near"])
    if pose == "attack":
        up = pivot(up, rot_z(-0.16 if far == "hammer" else 0.07), (0, hip, 0))
        if far == "hammer":
            up = up.transformed(I3, (2.5, 0, 0))
    m = Model()
    m.extend(lower)
    m.extend(up)
    return m


def dims(k):
    return int(96 * k), int(90 * k), int(round(36 * k)), int(round(80 * k))


def build(cfg, lv=1, pose="idle", k=2.0, **kw):
    w, h, ox, oy = dims(k)
    opts = dict(STYLE1)
    opts.update(kw)
    spr = render(model(cfg, lv, pose).scaled(k), w, h, ox, oy, **opts)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    from paths import out
    A = ("tracks", "visor", "fire", "hammer", "shield")
    B = ("springs", "sensor", "volt", "cannon", "claw")
    w, h, _, _ = dims(2.0)
    sc = Scene(3 * w, 2 * h)
    sc.rgb[:] = hexc("#2c2436")
    for i in range(3):
        sc.blit(build(A, i + 1), i * w, 0)
        sc.blit(build(B, i + 1), i * w, h)
    sc.image(2).save(out("test_tiers.png"))
