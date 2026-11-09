"""The Guard's modules on the humanoid Guard, each at levels I–III. A module is an ability, and it shows: the shield
grows into a pavise, an anchor hangs on the boiler, plates are bolted over the chest, seams glow red-hot. Some
rare modules change the body itself: tracks instead of legs, a flail instead of the maul.

At level III a module gets a new facet, not only bigger numbers — and a new look to go with it.

    python3 tools/sprites/guard_modules.py      -> out/guard_modules_check.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_STEEL, M_RUST, M_HOLE, M_HOSE, emissive, spike, tbox, STYLE1
from golem7 import M_PUFF
import humanoid as HM
from humanoid import arr, unit, lerp, rivets, ram, axle, gear, block, fist, basis, Parts, chest_front, chest_side, HIP, SH
from clipcheck import report
from golems_h import sparks as _sparks


def GH_sparks(fx, p):
    _sparks(fx, arr(p), n=5, spread=2.2, seed=3, big=True)

P = Mat(HM.PAINT)
HOT = Mat(EMBER, emissive=hexc("#ff7a28"), glow_r=4, glow_k=0.4)
GLOWPLATE = Mat(ramp("#3a1006", "#7a2a0c", "#b8501a", "#e88a34", "#ffc070"), emissive=hexc("#ff7a28"), glow_r=5, glow_k=0.3)
CHAIN = Mat(ramp("#141418", "#2a2c32", "#4a4e58", "#787e8a", "#aab0bc"))
RUNE = Mat(EMBER, emissive=hexc("#ff8a30"), glow_r=4, glow_k=0.35)


def sat(info):
    """The shield's own frame: x out of its face, y up, z across."""
    C, R = info["sc"], info["R"]
    return lambda x, y=0.0, z=0.0: C + R @ arr((x, y, z))


# ---------------------------------------------------------------- Ростовой щит
def tower_shield(G, info, t):
    """The shield grows: an apron down to the ground; II — side wings; III — a crenellated top, a second slit,
    a prop behind it (it stands on its own)."""
    g, at, R = G["m_shield"], sat(info), info["R"]
    g.box(at(0.1, -14.0), (1.2, 7.0, 11.6), P, R)                                     # the apron
    g.box(at(0.1, -14.0), (1.4, 0.8, 12.2), M_DIRON, R)
    rivets(g, [at(0.8, -12.0, z) for z in (-4.6, 0.0, 4.6)], r=0.35)
    for z in (-4.0, 4.0):
        spike(g, at(0, -17.4, z), at(0.4, -19.2, z), 0.7, M_IRON)
    if t >= 2:                                                                         # side wings, angled forward
        for s in (-1, 1):
            hinge = at(0, 0, s * 6.6)
            Rw = R @ rot_y(-s * 0.5)
            g.box(hinge + Rw @ arr((0, -2.0, s * 2.4)), (1.1, 24.0, 4.6), P, Rw)
            g.box(hinge + Rw @ arr((0.6, -2.0, s * 4.6)), (0.4, 24.0, 0.6), M_DIRON, Rw)
            for y in (-10.0, 0.0, 8.0):
                g.cyl(hinge + R @ arr((-0.2, y - 1.0, 0)), hinge + R @ arr((-0.2, y + 1.0, 0)), 0.7, M_IRON, seg=6)
    if t >= 3:                                                                         # a crenellated top, a prop
        for z in (-4.4, 0.0, 4.4):
            g.box(at(0, 11.9, z), (1.5, 2.4, 2.6), P, R)
        g.box(at(1.1, 3.0), (0.3, 1.0, 6.0), M_HOLE, R)
        g.box(at(1.1, 3.0, -2.4), (0.32, 0.7, 0.7), emissive("fire", 3, 0.3), R)
        prop = at(-0.8, 6.0, -2.0)
        foot = prop + R @ arr((-9.0, 0, 0)) * 1.0
        foot = arr((foot[0], 0.4, foot[2]))
        g.cyl(prop, foot, 0.55, M_DIRON, seg=6)
        g.cyl(foot, foot + (0, 0.5, 0), 1.2, M_IRON, seg=8)
    return [("m_shield", "shield"), ("m_shield", "bracket"), ("m_shield", "hand_f")]


# ---------------------------------------------------------------- Перехват
def intercept(G, info, t):
    """A buckler on a swing arm from the near pauldron: it swings out to take a blow meant for a neighbour.
    II — a longer arm, a bigger buckler; III — a hooked rim and a catch chain."""
    g = G["m_icpt"]
    root = arr((-3.6, 41.0, 13.2))
    g.box(root + (0, -0.6, 0), (3.0, 1.2, 3.0), M_DIRON)
    axle(g, root + (0, 0.4, 0), 1.0, 1.2, 1)
    L = 6.0 if t == 1 else 8.0
    elbow = root + arr((-0.6, 2.4, 3.4)) * (L / 6.0)
    c = elbow + arr((3.8, -3.2, 2.0)) * (L / 6.0)
    g.cyl(root, elbow, 0.6, M_IRON, seg=6)
    ram(g, root + (0.6, 0.2, 0.3), elbow + (0.4, -0.6, -0.2), 0.42)
    g.ell(elbow, (0.9, 0.9, 0.9), M_DIRON)
    g.cyl(elbow, c, 0.55, M_IRON, seg=6)
    r = 3.2 if t == 1 else 4.4
    n = unit(arr((0.55, 0.15, 0.82)))
    g.cyl(c - n * 0.5, c + n * 0.3, r, P, seg=16)
    g.cyl(c + n * 0.3, c + n * 0.7, r * 0.45, M_IRON, seg=10)
    g.ell(c + n * 0.8, (0.8, 0.8, 0.8), M_DIRON)
    side = unit(np.cross(n, arr((0, 1.0, 0))))
    up = unit(np.cross(side, n))
    rivets(g, [c + n * 0.35 + (np.cos(a) * side + np.sin(a) * up) * (r - 0.6) for a in np.linspace(0, 2 * np.pi, 9)[:-1]], r=0.3)
    if t >= 3:
        for a in (0.6, 2.2, 3.8, 5.4):                                               # hooks on the rim
            q = c + (np.cos(a) * side + np.sin(a) * up) * r
            spike(g, q, q + (np.cos(a) * side + np.sin(a) * up) * 1.6 + n * 0.8, 0.45, M_IRON)
        for i in range(5):                                                            # the catch chain hanging from it
            g.ell(c - up * (r + 0.8 + i * 1.0), (0.35, 0.55, 0.2 if i % 2 else 0.35), CHAIN)
        g.ell(c - up * (r + 6.2), (0.9, 0.9, 0.9), M_IRON)
    return [("m_icpt", "pauldron_n"), ("m_icpt", "arm_n.ball")]


# ---------------------------------------------------------------- Якорь
def anchor_shape(g, top, L=13.0, r=0.8):
    """A ship's anchor hanging from `top`: ring, stock, shank, curved flukes with spade tips."""
    top = arr(top)
    bot = top - (0, L, 0)
    g.ell(top + (0, 0.8, 0), (0.9, 0.9, 0.35), M_IRON)                               # the ring
    g.cyl(top + (-2.6, -1.4, 0), top + (2.6, -1.4, 0), r * 0.7, M_DIRON, seg=6)      # the stock
    g.cyl(top, bot, r, M_IRON, seg=8)                                                # the shank
    for sx in (-1, 1):
        a = bot
        m = bot + (sx * 2.2, 0.8, 0)
        b = bot + (sx * 3.4, 3.4, 0)
        g.cyl(a, m, r * 0.9, M_IRON, seg=6)
        g.cyl(m, b, r * 0.85, M_IRON, seg=6)
        tbox(g, b + (sx * 0.2, 0.6, 0), (1.8, 0.8), (0.4, 0.4), 2.2, M_DIRON, rot_z(-sx * 0.5))
    return bot


def anchor(G, info, t):
    """A ship's anchor slung at the near hip on a chain; II — claws on the feet that bite into the ground;
    III — hydraulic stays from the hips to pads on the ground: he does not move again."""
    g = G["m_anchor"]
    hook = arr((1.0, 19.6, 9.2))
    g.box(hook + (-0.6, 0.6, -0.8), (3.0, 1.4, 1.2), M_DIRON)                        # a hook on the belt
    for i in range(3):
        g.ell(hook + (0, -0.8 - i * 0.9, 0.6), (0.3, 0.5, 0.45) if i % 2 else (0.45, 0.5, 0.3), CHAIN)
    anchor_shape(g, hook + (0, -3.6, 0.9), L=11.0 if t == 1 else 12.0, r=0.75 if t == 1 else 0.9)
    if t >= 2:
        for (h, k, a, s) in info["legs"]:
            for dz in (-1.6, 0.0, 1.6):
                spike(g, a + (5.4, -2.6, dz), a + (6.8, -4.4, dz * 1.1), 0.7, M_IRON)   # toe claws into the ground
    if t >= 3:
        for s in (-1, 1):
            a = arr((-1.6, 18.6, s * 6.4))
            f = arr((-6.0, 0.6, s * 15.0))
            ram(g, a, f + (0, 2.0, 0), 0.8)
            g.cyl(f, f + (0, 0.7, 0), 2.2, M_DIRON, seg=10)
            for dz in (-1.2, 1.2):
                spike(g, f + (0, 0.2, dz), f + (0, -1.6, dz), 0.5, M_IRON)
        g.box(hook + (0.2, -9.0, 0.9 + 0.9), (0.6, 3.0, 0.2), RUNE)
    return [("m_anchor", "leg_n"), ("m_anchor", "leg_f"), ("m_anchor", "pelvis"), ("m_anchor", "leg_n.ram"),
            ("m_anchor", "leg_f.ram")]


# ---------------------------------------------------------------- Броневые листы
RAW = Mat(ramp("#22262c", "#3e444e", "#646c78", "#949ca8", "#c8ced8"))                # unpainted plate steel


def plates(G, info, t, lost=0):
    """Three raw steel plates bolted on — over the near pauldron, the near forearm, the near thigh: the first three
    blows only knock one off each. II — doubled, riveted round; III — studded with spikes. lost: plates gone."""
    g = G["m_plates"]
    h, k, a, s = info["legs"][0]
    Rt, _ = basis(h, k)
    el, w = info["el"], info["w"]
    Rf, _ = basis(el, w)
    spots = [(arr((-0.2, 42.6, 11.6)), (6.8, 0.8, 5.6), rot_x(0.55) @ rot_z(-0.1)),          # on the pauldron
             (lerp(el, w, 0.5) + Rf @ arr((0, 0, 0)) + arr((0, 0, 3.0)), (3.6, 5.0, 0.7), Rf),  # on the gauntlet
             (lerp(h, k, 0.55) + Rt @ arr((0.6, 0, 0)) + arr((0, 0, 3.4)), (3.6, 5.6, 0.7), Rt)]  # on the thigh
    for i, (c, size, R) in enumerate(spots):
        if i < lost:
            if i == lost - 1:                                  # the one just knocked off flies away, spinning
                fly = c + arr((5.0, 4.0, 6.0))
                G["fx"].box(fly, arr(size) + (0, 0, 0.3), RAW, R @ rot_x(0.9) @ rot_z(0.7))
                GH_sparks(G["fx"], c + arr((0.6, 0.0, 1.2)))
            continue
        sz = arr(size) + (arr((0, 0, 0.4)) if t >= 2 and size[2] < 1 else arr((0, 0.4, 0)) if t >= 2 else 0)
        g.box(c, sz, RAW, R)
        thin = int(np.argmin(sz))
        n_ = R[:, thin]
        e1, e2 = [R[:, j] * (sz[j] / 2 - 0.6) for j in range(3) if j != thin]
        out = n_ * (sz[thin] / 2 + 0.1)
        if out @ arr((0.3, 0.6, 1.0)) < 0:
            out, n_ = -out, -n_
        rivets(g, [c + out + e1 * a1 + e2 * a2 for a1 in (-1, 1) for a2 in (-1, 1)], mat=M_STEEL, r=0.32)
        if t >= 3:
            spike(g, c + out, c + out + n_ * 2.4, 0.6, M_STEEL)
    return [("m_plates", "pauldron_n"), ("m_plates", "arm_n"), ("m_plates", "leg_n"), ("m_plates", "arm_n.ram"),
            ("m_plates", "leg_n.ram"), ("m_plates", "hammer")]


# ---------------------------------------------------------------- Контрудар
def counter(G, info, t, fired=False):
    """A big spring-loaded spike on a piston in the boss of the shield answers the first blow; II — a recoil
    spring on the shield arm and a second spike; III — spikes all round the rim."""
    g, at, R = G["m_counter"], sat(info), info["R"]
    out = R @ arr((1.0, 0, 0))
    for y in ((-1.7,) if t == 1 else (-1.7, 6.0)):
        base = at(1.4, y)
        g.cyl(base, base + out * 2.2, 2.0, M_DIRON, seg=10)
        g.cyl(base + out * 2.2, base + out * 2.6, 2.3, M_IRON, seg=10)
        L = 1.0 if not fired else 7.5
        g.cyl(base + out * 2.6, base + out * (2.6 + L), 0.7, M_STEEL, seg=6)
        spike(g, base + out * (2.6 + L), base + out * (6.6 + L), 1.5, M_STEEL)
        if fired:
            G["fx"].ell(base + out * (6.8 + L), (1.8, 1.8, 1.8), emissive("fire", 8, 0.6))
    if t >= 2:
        a, b = info["elf"], info["wf"]
        d = unit(b - a)
        for i in range(6):
            p = lerp(a, b, 0.25 + i * 0.09)
            g.cyl(p - d * 0.15, p + d * 0.15, 3.1, CHAIN, seg=10)
    if t >= 3:
        for y in (-9.0, 0.0, 9.0):
            for z in (-6.8, 6.8):
                spike(g, at(0.2, y, z), at(1.8, y, z * 1.25), 0.7, M_IRON)
    return [("m_counter", "shield"), ("m_counter", "arm_f"), ("m_counter", "bracket"), ("m_counter", "hand_f")]


# ---------------------------------------------------------------- Раскалённая броня
def hot_armour(G, info, t):
    """The furnace heat let into the armour: glowing seams down the near arm and leg; II — on the pauldron and the
    breast too, heat shimmer; III — the plates themselves red-hot, flames licking the shoulders."""
    g = G["m_hot"]
    h, k, a, s = info["legs"][0]
    Rt, _ = basis(h, k)
    el, w = info["el"], info["w"]
    Rf, _ = basis(el, w)
    g.box(lerp(el, w, 0.5) + arr((0, 0, 2.85)), (0.5, 4.6, 0.3), HOT, Rf)                          # gauntlet seam
    g.box(lerp(h, k, 0.55) + Rt @ arr((0.4, 0, 0)) + arr((0, 0, 3.05)), (3.0, 0.5, 0.3), HOT, Rt)  # thigh seam
    g.box(lerp(h, k, 0.35) + Rt @ arr((0.4, 0, 0)) + arr((0, 0, 3.05)), (3.0, 0.5, 0.3), HOT, Rt)
    if t >= 2:
        for y in (28.4, 32.4):
            x = chest_front(y) + 0.25
            g.box((x, y, 1.6), (0.3, 0.5, chest_side(y) * 0.9), HOT, rot_z(-0.12))
        g.box(arr((-0.4, 41.8, 13.3)), (5.6, 0.5, 0.35), HOT, rot_x(0.55))
        for i, p in enumerate(((5.0, 47.0, 4.0), (-1.0, 49.0, -2.0))):
            G["fx"].ell(arr(p), (1.8, 2.6, 1.8), Mat(ramp("#2a1a14", "#4a2e22", "#6e4632", "#96644a", "#c08a68"), dither=True))
    if t >= 3:
        g.box(lerp(el, w, 0.55) + arr((0, 0, 2.75)), (2.6, 3.4, 0.25), GLOWPLATE, Rf)
        g.box(lerp(h, k, 0.5) + Rt @ arr((0.4, 0, 0)) + arr((0, 0, 2.95)), (3.0, 4.0, 0.25), GLOWPLATE, Rt)
        for i, o in enumerate(((0.0, 0.0), (2.0, 0.8), (-2.0, 0.6))):
            G["fx"].ell(arr((o[0], 43.0 + o[1] + i * 0.4, 12.0)), (0.9, 1.7 - 0.2 * i, 0.9), Mat(FIRE, emissive=hexc("#ff8a30"), glow_r=6, glow_k=0.5))
    return [("m_hot", "chest"), ("m_hot", "pauldron_n"), ("m_hot", "arm_n"), ("m_hot", "leg_n")]


# ---------------------------------------------------------------- Гусеницы (rare): tracks instead of legs
def tracks(G, info, t):
    g = G["m_tracks"]
    for s in (-1, 1):
        z = s * 6.6
        L, Hh = 22.0, 7.6
        c = arr((0.0, Hh / 2 + 0.2, z))
        g.box(c, (L - 4.0, Hh - 1.0, 4.2), M_DIRON)                                 # the frame
        for x in np.linspace(-L / 2 + 2.4, L / 2 - 2.4, 5):                         # road wheels
            g.cyl((x, 2.2, z - s * 2.3), (x, 2.2, z + s * 2.3), 1.9, M_IRON, seg=10)
        for x in (-L / 2 + 1.4, L / 2 - 1.4):                                        # sprocket and idler
            g.cyl((x, Hh / 2 + 0.6, z - s * 2.4), (x, Hh / 2 + 0.6, z + s * 2.4), 2.8, M_IRON, seg=12)
            g.cyl((x, Hh / 2 + 0.6, z + s * 2.4), (x, Hh / 2 + 0.6, z + s * 2.7), 1.2, M_STEEL, seg=8)
        for i in range(14):                                                          # the belt: shoes along the top and bottom
            x = -L / 2 + 1.0 + i * (L - 2.0) / 13
            g.box((x, Hh + 0.6, z), (1.3, 0.5, 4.8), CHAIN)
            g.box((x, 0.25, z), (1.3, 0.5, 4.8), CHAIN)
        if t >= 2:                                                                   # skirts
            g.box((0.0, Hh - 1.0, z + s * 2.75), (L - 3.0, 3.6, 0.4), P)
            rivets(g, [(x, Hh - 1.0, z + s * 3.0) for x in np.linspace(-L / 2 + 3, L / 2 - 3, 5)], r=0.32)
    col = arr((0.0, 8.4, 0.0))                                                       # a column up to the hips
    g.box(col + (0, 0.4, 0), (8.0, 1.2, 10.4), M_IRON)
    g.cyl(col + (0, 1.0, 0), col + (0, 10.2, 0), 3.4, M_DIRON, seg=14)
    for s in (-1, 1):
        ram(g, col + (2.4, 1.2, s * 2.6), arr((2.0, 18.4, s * 3.0)), 0.6)
    if t >= 3:                                                                       # a ram plough with spikes
        g.box((13.0, 3.0, 0.0), (1.4, 5.2, 17.6), M_IRON, rot_z(-0.35))
        for z in np.linspace(-7.0, 7.0, 5):
            spike(g, (13.6, 3.4, z), (16.4, 2.8, z), 0.7, M_STEEL)
        for s in (-1, 1):
            g.cyl((10.0, 3.0, s * 6.6), (12.6, 3.0, s * 6.6), 0.7, M_DIRON, seg=6)
    return [("m_tracks", "pelvis")]


# ---------------------------------------------------------------- Кистень (rare): a flail instead of the maul
def flail(G, info, t):
    g = G["m_flail"]
    w, el = info["w"], info["el"]
    hand, _, u = fist(G, "hand_n", w, w - el, unit(arr((0.75, 0.62, 0.22))), 1, P)
    top = hand + u * 8.0
    g.cyl(hand - u * 2.6, top, 0.8, M_DIRON, seg=6)
    g.cyl(hand - u * 3.2, hand - u * 2.6, 1.1, M_IRON, seg=6)
    g.cyl(top - u * 1.0, top + u * 0.4, 1.1, M_IRON, seg=6)
    heads = [(arr((0.6, 0.0, 1.2)), 2.2 if t == 1 else 2.8)]
    if t >= 3:
        heads.append((arr((2.6, 2.0, -1.6)), 2.4))
    for k, (off, r) in enumerate(heads):
        a = top + u * 0.4
        b = top + off + arr((0, -6.0, 0))
        n = 7
        for i in range(n):                                                           # chain links
            p = lerp(a, b, (i + 0.5) / n)
            g.ell(p, (0.35, 0.5, 0.35) if i % 2 else (0.5, 0.35, 0.5), CHAIN)
        c = b - arr((0, r, 0))
        g.ell(c, (r, r, r), Mat(ramp("#22262c", "#3e444e", "#646c78", "#949ca8", "#c8ced8")))
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (0.7, 0.7, 0), (-0.7, -0.7, 0),
                  (0, 0.7, 0.7), (0.7, 0, -0.7))[: 6 + 2 * (t - 1)]:
            d = unit(arr(d))
            spike(g, c + d * r * 0.8, c + d * (r + 1.6), 0.55, M_STEEL)
        if t >= 3 and k == 0:
            g.box(c + (r * 0.9, 0, 0), (0.2, 0.5, 1.4), RUNE)
    return [("m_flail", "hand_n"), ("m_flail", "arm_n")]


MODULES = {
    "tower": ("Ростовой щит", "снаряды по своим за спиной попадают в щит", tower_shield, {}),
    "intercept": ("Перехват", "когда бьют соседа, принимает удар на себя", intercept, {}),
    "anchor": ("Якорь", "врастает в землю, держит фронт в 3 клетки", anchor, {}),
    "plates": ("Броневые листы", "первые 3 удара сбивают по листу", plates, {}),
    "counter": ("Контрудар", "на первый удар вплотную отвечает своим", counter, {}),
    "hot": ("Раскалённая броня", "кто бьёт вплотную, загорается", hot_armour, {}),
    "tracks": ("Гусеницы", "редкий: давит мелких на пути", tracks, dict(legs=False)),
    "flail": ("Кистень", "редкий: бьёт сразу 2 клетки", flail, dict(weapon=False, near_arm=((1.6, -7.4, 1.8), (6.4, -12.6, 2.6)))),
}


def parts(keys, t=1, **kw):
    """The Guard at rest with the given modules (a key or a list of keys), all at level t (or a dict key -> level)."""
    keys = [keys] if isinstance(keys, str) else list(keys)
    lv = t if isinstance(t, dict) else {k: t for k in keys}
    opts = {}
    for k in keys:
        opts.update(MODULES[k][3])
    G, info = HM.guard_idle(P, **opts)
    allow = list(HM.ALLOWED)
    for k in keys:
        extra = {}
        if k == "plates" and "lost" in kw:
            extra["lost"] = kw["lost"]
        if k == "counter" and "fired" in kw:
            extra["fired"] = kw["fired"]
        allow += MODULES[k][2](G, info, lv[k], **extra)
    return G, allow


def check(keys, t=1, **kw):
    G, allow = parts(keys, t, **kw)
    return report(G, allow + [(a, b) for a in G for b in G if a.startswith("m_") and b.startswith("m_")], skip=("fx", "sparks"))


def build(keys, t=1, k=2.2, **kw):
    G, _ = parts(keys, t, **kw)
    w, h = int(96 * k), int(86 * k)
    ox, oy = int(40 * k), int(76 * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    import sys
    from PIL import Image
    from paths import out
    rows = []
    for key in (sys.argv[1:] or list(MODULES)):
        row = []
        for t in (1, 2, 3):
            bad = check(key, t)
            if bad:
                print(key, t, bad)
            im = build(key, t, k=2.0).image(1)
            bb = im.getbbox()
            row.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
        rows.append(row)
    per = 2
    flat = [r for r in rows]
    W = max(sum(i.width + 10 for i in r) for r in flat) * per + 30
    lines = [flat[i:i + per] for i in range(0, len(flat), per)]
    H = sum(max(max(i.height for i in r) for r in ln) + 12 for ln in lines)
    sheet = Image.new("RGBA", (W, H), (52, 46, 58, 255))
    y = 0
    for ln in lines:
        x, h = 0, max(max(i.height for i in r) for r in ln)
        for r in ln:
            for i in r:
                sheet.alpha_composite(i, (x, y + h - i.height))
                x += i.width + 10
            x += 30
        y += h + 12
    sheet.save(out("guard_modules_check.png"))
    print("ok")
