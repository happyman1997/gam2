"""Modules of the humanoid frames (golems_h) at levels I–III, as the Guard's are in guard_modules.py. A module is an
ability and shows on the golem; it is mounted where the half-turned view can see it — on the near pauldron, the
front of the body, the near arm, over the shoulders, on the ground at its feet. At level III it gets a new facet and
a new look.

    python3 tools/sprites/frame_modules.py Мудрец      -> out/frame_modules_check.png (one frame, every module, I–III)
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_STEEL, M_RUST, M_HOLE, M_HOSE, M_GLASS, M_BRONZE, emissive, spike, tbox, STYLE1
from golem7 import M_PUFF
import golems_h as GH
from golems_h import (arr, unit, lerp, rivets, sparks, puffs, Parts, ik, place_upper, basis, ram, block, axle, gear,
                      COPPER, PORC, ARC, ENERGY, SAW, BRASS_P as BRASS_R, insulator)
from clipcheck import report, cells, STEP
from leaders_h import zigzag, lattice

BRASS = Mat(BRASS_R)
HOT = Mat(EMBER, emissive=hexc("#ff7a28"), glow_r=4, glow_k=0.4)
FLAME = Mat(FIRE, emissive=hexc("#ff8a30"), glow_r=7, glow_k=0.55)
COAL = emissive("fire", 6, 0.6)
GLASS = Mat(ramp("#1a2a30", "#2e4a54", "#4e7a86", "#86b4c0", "#d0f0f8"))
CHAIN = Mat(ramp("#141418", "#2a2c32", "#4a4e58", "#787e8a", "#aab0bc"))
RED = Mat(ramp("#2a0606", "#5a0e0e", "#9a1c1c", "#d0402e", "#f08060"))
BLUE = Mat(ramp("#06142a", "#0e2a6a", "#1a50b0", "#3a8ae8", "#90c8ff"))
STEAM = Mat(ramp("#6a6a70", "#8e8e96", "#b4b4bc", "#d6d6dc", "#f4f4f8"), dither=True)
SMOKE = M_PUFF
ROPE = Mat(ramp("#2a2014", "#4a3a22", "#6e5a38", "#968050", "#bea870"))
OIL = Mat(ramp("#060504", "#14100a", "#261e12", "#3a2e1c", "#54442a"))
STONE = Mat(ramp("#22202a", "#3e3a46", "#5e5a68", "#86828e", "#b2aeb8"))
BOMB = Mat(ramp("#08080a", "#141418", "#22222a", "#34343e", "#4c4c58"))


# ---------------------------------------------------------------- the frame and where things are on it
def golem(frame, A=None, **over):
    S = dict(GH.BY_NAME[frame], **over)
    A = dict(S["poses"]["idle"], fx=None) if A is None else A
    G, info = GH.creature_parts(S, A, fx=False)
    R = rot_z(A["lean"]) @ rot_y(A.get("twist", 0.0))
    X = place_upper(Parts(), R, A["t"], hip=S["hip"], keys=())
    for side, s in (("n", 1), ("f", -1)):
        sh = X(S["sh"] * arr((1, 1, s)))
        el, w = ik(sh, sh + arr(A["hand_" + side]), S["LU"], S["LF"], A["pole_" + side])
        info["el_" + side], info["w_" + side] = el, w
    from augments import leg_joints
    info.update(S=S, A=A, X=X, R=R, legs=leg_joints(S, A))
    return G, info, GH.BASE_ALLOWED + S.get("allow", [])


def box_of(G, key):
    c = np.array(list(cells(G[key]))) * STEP
    return c.min(0), c.max(0)


def top_at(G, x, z, r=1.6, keys=("chest", "back", "pauldron_n", "pauldron_f", "head", "spine", "robe", "hose")):
    ys = [p[1] for k in keys if k in G for p in (np.array(c) * STEP for c in cells(G[k]))
          if (p[0] - x) ** 2 + (p[2] - z) ** 2 <= r * r]
    return max(ys) if ys else None


def front_at(G, y, z, keys=("chest", "pelvis", "spine", "robe"), r=0.8):
    xs = [p[0] for k in keys if k in G for p in (np.array(c) * STEP for c in cells(G[k]))
          if abs(p[1] - y) <= r and abs(p[2] - z) <= r]
    return max(xs) if xs else None


def shoulder_top(G, info, dx=0.0, dz=1.0):
    """A point on top of the near pauldron."""
    sh = info["sh_n"]
    x, z = sh[0] + dx, sh[2] + dz
    y = top_at(G, x, z, keys=("pauldron_n", "arm_n.ball", "chest"))
    return arr((x, (y if y is not None else sh[1] + 4.0) + 0.2, z))


def chain(g, a, b, n=None, r=0.35):
    a, b = arr(a), arr(b)
    n = n or max(2, int(np.linalg.norm(b - a) / 0.9))
    for i in range(n):
        p = lerp(a, b, (i + 0.5) / n)
        g.ell(p, (r, r * 1.4, r) if i % 2 else (r * 1.3, r, r * 0.8), CHAIN)


def canister(g, base, r, h, mat, cap=BRASS, d=(0, 1.0, 0)):
    base, d = arr(base), unit(d)
    g.cyl(base, base + d * h, r, mat, seg=12)
    g.cyl(base + d * h, base + d * (h + 0.4), r * 0.85, cap, seg=12)
    g.cyl(base + d * (h + 0.4), base + d * (h + 1.0), r * 0.35, cap, seg=8)
    g.cyl(base + d * h * 0.3, base + d * (h * 0.3 + 0.3), r + 0.08, cap, seg=12)
    return base + d * (h + 1.0)


# ================================================================ Мудрец
def s_chain(G, info, t):
    """Цепная молния: a copper ring round the staff under its ball, conductor balls hung on it — as many as the
    lightning jumps (2, then 3, at III 4) — with arcs between them at III."""
    g = G["m"]
    st = info["n"]
    c, u = st["tip"] - st["u"] * 2.8, st["u"]
    side = unit(np.cross(u, arr((1.0, 0, 0))))
    fwd = unit(np.cross(side, u))
    R = 3.8
    pts = [c + (np.cos(a) * side + np.sin(a) * fwd) * R for a in np.linspace(0, 2 * np.pi, 15)]
    for p, q in zip(pts[:-1], pts[1:]):
        g.cyl(p, q, 0.36, COPPER, seg=5)
    for a in (0.0, np.pi / 2, np.pi, 3 * np.pi / 2):
        g.cyl(c + (np.cos(a) * side + np.sin(a) * fwd) * 0.7, c + (np.cos(a) * side + np.sin(a) * fwd) * R, 0.2, COPPER, seg=4)
    n = {1: 2, 2: 3, 3: 4}[t]
    balls = []
    for i in range(n):
        a = 2 * np.pi * i / n + 0.4
        p = c + (np.cos(a) * side + np.sin(a) * fwd) * R
        b = p - u * 2.4
        g.cyl(p, b, 0.14, CHAIN, seg=4)
        g.ell(b - u * 0.9, (1.05, 1.05, 1.05), COPPER)
        balls.append(b - u * 0.9)
    if t >= 3:
        for p, q in zip(balls, balls[1:] + balls[:1]):
            zigzag(G["fx"], p, q, n=3, amp=0.4, seed=int(p[1] * 10) % 97, r=0.15)
    return [("m", "item_n")]


def s_ground(G, info, t):
    """Разряд в землю: copper stakes driven into the ground round its feet, a cable from the staff's butt;
    II — four stakes; III — a ring of six on a copper ring (radius 2), sparks playing on it."""
    g = G["m"]
    st = info["n"]
    butt = st["hand"] - st["u"] * 34.0 * 0.46
    n = {1: 2, 2: 4, 3: 6}[t]
    R = 11.5 if t < 3 else 12.5
    tops = []
    for i in range(n):
        a = 2 * np.pi * i / n + (0.35 if t < 3 else 0.62)
        p = arr((np.cos(a) * R + 1.0, 0.0, np.sin(a) * R))
        g.cyl(p - (0, 0.4, 0), p + (0, 4.6, 0), 0.42, COPPER, seg=6)
        insulator(g, p + (0, 4.6, 0), p + (0, 6.4, 0), 0.8, n=2)
        g.ell(p + (0, 6.9, 0), (0.6, 0.6, 0.6), COPPER)
        tops.append(p + (0, 0.5, 0))
    near = min(tops, key=lambda p: np.linalg.norm(p - butt))
    g.cyl(butt + (0, 0.4, 0), near, 0.2, M_HOSE, seg=4)
    if t >= 3:
        for p, q in zip(tops, tops[1:] + tops[:1]):
            g.cyl(p, q, 0.18, COPPER, seg=4)
        for i, p in enumerate(tops[::2]):
            zigzag(G["fx"], p + (0, 6.9, 0), p + arr((0.8, 9.4, 0.6)), n=3, amp=0.3, seed=i, r=0.16)
    return [("m", "item_n")]


def s_overload(G, info, t):
    """Перегрузка: Leyden jars in a rack on the near pauldron — glass, copper foil, a brass terminal ball;
    II — three; III — four, and a jumper cable with a clamp to hand to a neighbour."""
    g = G["m"]
    base = shoulder_top(G, info, dx=-1.4, dz=0.6)
    n = {1: 2, 2: 3, 3: 4}[t]
    g.box(base + (0, 0.2, 0), (2.8, 0.4, 1.7 * n + 0.6), BRASS)
    tops = []
    for i in range(n):
        p = base + arr((0, 0.4, (i - (n - 1) / 2) * 1.7))
        g.cyl(p, p + (0, 3.6, 0), 0.72, GLASS, seg=10)
        g.cyl(p, p + (0, 1.6, 0), 0.76, COPPER, seg=10)
        g.cyl(p + (0, 3.6, 0), p + (0, 4.0, 0), 0.6, BRASS, seg=8)
        g.cyl(p + (0, 4.0, 0), p + (0, 5.1, 0), 0.14, BRASS, seg=4)
        g.ell(p + (0, 5.4, 0), (0.42, 0.42, 0.42), BRASS)
        tops.append(p + (0, 5.4, 0))
    for p, q in zip(tops[:-1], tops[1:]):
        g.cyl(p, q, 0.1, COPPER, seg=4)
    if t >= 3:
        cl = base + arr((4.0, -6.0, 3.0))
        g.cyl(tops[-1], cl, 0.18, RED, seg=4)
        g.box(cl, (1.2, 0.6, 0.5), RED)
        g.box(cl + (0.8, 0, 0), (0.8, 0.25, 0.6), M_STEEL)
        G["fx"].ell(tops[0] + (0, 0.4, 0), (0.4, 0.4, 0.4), GH.ENERGY)
    return [("m", "pauldron_n"), ("m", "arm_n.ball")]


def s_fireball(G, info, t):
    """Огненный шар: a brass censer of coals hung by a chain from the staff; II — larger, flames over it;
    III — three fire motes circling it."""
    g = G["m"]
    st = info["n"]
    hook = st["tip"] - st["u"] * 6.0 + arr((0.0, 0.0, 1.0))
    g.cyl(hook - arr((0, 0, 1.0)), hook + arr((0.6, 0, 0.6)), 0.25, M_IRON, seg=4)
    r = 1.8 if t == 1 else 2.3
    c = hook + arr((2.4, -6.0, 2.2))
    chain(g, hook + (0.6, 0, 0.6), c + (0, r + 0.2, 0))
    g.ell(c, (r, r * 0.85, r), BRASS)
    for a in np.linspace(0, 2 * np.pi, 7)[:-1]:
        g.ell(c + arr((np.cos(a) * r * 0.9, 0.0, np.sin(a) * r * 0.9)), (0.25, 0.3, 0.25), COAL)
    g.cyl(c + (0, r * 0.7, 0), c + (0, r * 0.95, 0), r * 0.6, BRASS, seg=10)
    if t >= 2:
        for i, o in enumerate(((0, 1.4, 0), (0.4, 2.2, 0.2), (-0.3, 2.0, -0.3))):
            G["fx"].ell(c + arr(o) * r / 1.3, (0.6 - 0.1 * i, 0.9 - 0.15 * i, 0.6 - 0.1 * i), FLAME)
    if t >= 3:
        for a in (0.4, 2.5, 4.6):
            G["fx"].ell(c + arr((np.cos(a) * 3.2, 0.6, np.sin(a) * 3.2)), (0.45, 0.55, 0.45), FLAME)
    return [("m", "item_n")]


def s_firewall(G, info, t):
    """Огненная стена: a fuel tank on the back, a pipe down to a rake of burners along the hem of the robe,
    pilot flames at II; III — the rake glows and every burner has its flame."""
    g = G["m"]
    lo, hi = box_of(G, "robe")
    x = hi[0] + 0.9
    n = 3 if t < 3 else 5
    zs = np.linspace(-4.0, 4.0, n)
    g.cyl((x, 8.4, zs[0] - 0.8), (x, 8.4, zs[-1] + 0.8), 0.45, M_DIRON, seg=6)
    for z in zs:
        g.cyl((x, 8.4, z), (x + 1.4, 7.0, z), 0.42, M_IRON, r1=0.62, seg=8)
        if t >= 2:
            G["fx"].ell((x + 1.9, 6.6, z), (0.35, 0.5, 0.35), FLAME if t >= 3 else COAL)
    tank = arr((-6.6, 40.0, 4.8))
    g.cyl(tank, tank + (0, 6.0, 0), 1.3, RED, seg=10)
    g.cyl(tank + (0, 6.0, 0), tank + (0, 6.6, 0), 0.7, BRASS, seg=8)
    via = arr((-7.0, 22.0, 9.0))
    g.cyl(tank, via, 0.24, M_HOSE, seg=4)
    g.cyl(via, (x - 0.6, 8.6, zs[-1] + 0.8), 0.24, M_HOSE, seg=4)
    if t >= 3:
        g.box((x + 0.5, 8.4, 0), (0.25, 0.4, zs[-1] - zs[0] + 1.6), HOT)
    return [("m", "robe"), ("m", "back"), ("m", "leg_n"), ("m", "pelvis")]


def s_blades(G, info, t):
    """Раскалённые клинки: a quiver of red-hot blades on the back, over the near shoulder, ready to hand out;
    II — three; III — four, shimmering."""
    g = G["m"]
    n = {1: 2, 2: 3, 3: 4}[t]
    base = arr((-6.4, 33.0, 5.6))
    g.box(base + (0, 2.0, 0), (2.4, 4.6, 1.4 * n + 0.6), Mat(ramp("#1a0e08", "#2e1a10", "#46281a", "#603a26", "#7e5038")), rot_z(0.35))
    for i in range(n):
        zz = (i - (n - 1) / 2) * 1.3
        a = base + arr((0.6, 4.4, zz))
        d = unit(arr((-0.35, 1.0, 0.05 * zz)))
        g.cyl(a - d * 0.6, a + d * 1.2, 0.35, M_DIRON, seg=6)                        # the hilt
        g.box(a + d * 1.4, (0.6, 0.3, 1.4), BRASS, basis(a, a + d)[0])
        b0, b1 = a + d * 1.6, a + d * 8.6
        g.box(lerp(b0, b1, 0.4), (0.25, 4.8, 0.8), M_STEEL, basis(b0, b1)[0])
        g.box(lerp(b0, b1, 0.82), (0.25, 2.8, 0.8), HOT, basis(b0, b1)[0])
    if t >= 3:
        G["fx"].ell(base + (-2.0, 13.0, 0.0), (2.0, 2.4, 2.0), Mat(ramp("#2a1a14", "#4a2e22", "#6e4632", "#96644a", "#c08a68"), dither=True))
    return [("m", "back"), ("m", "pauldron_n"), ("m", "chest")]


# ================================================================ Горн
def stack_top(G):
    """The top of the Gorn's chimney."""
    lo, hi = box_of(G, "back")
    pts = [np.array(c) * STEP for c in cells(G["back"])]
    top = [p for p in pts if p[1] >= hi[1] - 0.6]
    c = np.mean(top, axis=0)
    return arr((c[0], hi[1], c[2]))


def g_magnet(G, info, t):
    """Магнит: a red horseshoe magnet with bright poles on the near pauldron, poles forward; II — bigger, copper
    windings; III — a second one turned the other way (Отталкивание), blue sparks between the poles."""
    g = G["m"]
    base = shoulder_top(G, info, dx=-0.8, dz=0.6)
    def horseshoe(c, s, flip=1):
        r = 1.6 * s
        pts = [c + arr((0, r + np.sin(a) * r, np.cos(a) * r * 1.1)) for a in np.linspace(0, np.pi, 8)]
        for p, q in zip(pts[:-1], pts[1:]):
            g.cyl(p, q, 0.6 * s, BLUE, seg=8)
        for z in (-r * 1.1, r * 1.1):
            p = c + arr((0, r, z))
            g.cyl(p, p + arr((2.2 * s * flip, -0.8 * s, 0)), 0.6 * s, BLUE, seg=8)
            g.cyl(p + arr((2.2 * s * flip, -0.8 * s, 0)), p + arr((3.0 * s * flip, -1.1 * s, 0)), 0.62 * s, M_STEEL, seg=8)
            if t >= 2:
                for k in range(3):
                    q = p + arr(((0.5 + k * 0.5) * s * flip, -0.2 * s * k, 0))
                    g.cyl(q, q + arr((0.25 * flip, 0, 0)), 0.72 * s, COPPER, seg=8)
        return c + arr((3.2 * s * flip, r - 1.1 * s, 0))
    s = 1.0 if t == 1 else 1.3
    g.box(base + (0, 0.3, 0), (2.6, 0.6, 2.6), M_DIRON)
    tip = horseshoe(base + arr((0, 0.4, 0)), s)
    if t >= 3:
        tip2 = horseshoe(base + arr((-1.0, 0.4, 0)), s * 0.8, flip=-1)
        for z in (-1.6, 1.6):
            zigzag(G["fx"], tip + arr((0, 0, z)), tip + arr((2.6, 0.6, z)), n=3, amp=0.35, seed=int(z + 5), r=0.14)
    return [("m", "pauldron_n"), ("m", "arm_n.ball"), ("m", "chest")]


def g_rod(G, info, t):
    """Громоотвод: a lightning rod on the top of the stack; II — a three-pronged crown on insulators;
    III — a cable down to a stake in the ground, a spark caught on the crown."""
    g = G["m"]
    top = stack_top(G)
    L = 7.0 if t == 1 else 9.0
    g.cyl(top - (0, 0.5, 0), top + (0, 0.6, 0), 1.4, M_DIRON, seg=10)
    if t >= 2:
        insulator(g, top + (0, 0.6, 0), top + (0, 2.6, 0), 0.9, n=3)
    a = top + (0, 2.6 if t >= 2 else 0.6, 0)
    g.cyl(a, a + (0, L, 0), 0.3, COPPER, seg=6)
    spike(g, a + (0, L, 0), a + (0, L + 1.6, 0), 0.4, COPPER)
    if t >= 2:
        for zz in (-1.2, 1.2):
            g.cyl(a + (0, L - 1.6, 0), a + (0, L - 0.4, zz), 0.18, COPPER, seg=4)
            spike(g, a + (0, L - 0.4, zz), a + (0, L + 0.8, zz * 1.1), 0.22, COPPER)
    if t >= 3:
        st = arr((-12.0, 0.0, 6.0))
        g.cyl(a + (0, 1.0, 0), st + (0, 3.0, 0), 0.16, COPPER, seg=4)
        g.cyl(st, st + (0, 3.0, 0), 0.35, COPPER, seg=6)
        zigzag(G["fx"], a + (0, L + 1.6, 0), a + arr((2.6, L + 6.0, 1.4)), n=4, amp=0.6, seed=4, r=0.2)
    return [("m", "back")]


def g_smoke(G, info, t):
    """Дымовая труба: more stacks beside the chimney, each smoking; II — two; III — three and a pall of smoke."""
    g = G["m"]
    top = stack_top(G)
    n = t
    for i in range(n):
        p = top + arr((1.2 - i * 0.6, -14.0, 3.2 + i * 2.2))
        h = 9.0 - i * 2.0
        g.cyl(p, p + (0, h, 0), 0.95, M_DIRON, seg=10)
        g.cyl(p + (0, h, 0), p + (0, h + 0.6, 0), 1.25, M_IRON, seg=10)
        g.cyl(p + (0, 2.0, 0), p + (0, 2.4, 0), 1.1, M_RUST, seg=10)
        G["fx"].ell(p + (0, h + 2.2, 0), (1.8, 1.4, 1.6), SMOKE)
    if t >= 3:
        for i, d in enumerate(((3.0, 46.0, 9.0), (-2.0, 50.0, 10.0), (6.0, 42.0, 12.0))):
            G["fx"].ell(arr(d), (3.0 + i, 2.0 + 0.5 * i, 2.6 + i), SMOKE)
    return [("m", "back"), ("m", "pauldron_n"), ("m", "chest")]


def g_whistle(G, info, t):
    """Паровой свисток: a brass steam whistle on the near pauldron with a steam pipe; II — two; III — an organ
    of three that blows, plumes of steam."""
    g = G["m"]
    base = shoulder_top(G, info, dx=-1.0, dz=0.4)
    n = {1: 1, 2: 2, 3: 3}[t]
    g.box(base + (0, 0.3, 0), (2.4, 0.6, 1.6 * n + 0.6), M_DIRON)
    for i in range(n):
        p = base + arr((0, 0.6, (i - (n - 1) / 2) * 1.6))
        h = 4.6 + i * 1.4
        g.cyl(p, p + (0, h, 0), 0.8, BRASS, seg=10)
        g.box(p + (0.55, h * 0.6, 0), (0.3, 0.5, 0.9), M_HOLE)
        g.cyl(p + (0, h, 0), p + (0, h + 0.5, 0), 0.75, BRASS, seg=10)
        if t >= 3:
            G["fx"].ell(p + (0, h + 2.0, 0), (1.0, 1.8, 1.0), STEAM)
    g.cyl(base + (-1.2, 0.3, 0), base + (-4.0, -3.0, -2.0), 0.3, M_HOSE, seg=4)
    return [("m", "pauldron_n"), ("m", "arm_n.ball"), ("m", "chest"), ("m", "back")]


def g_maw(G, info, t):
    """Пасть топки: the firebox in the chest opened into a toothed maw; II — bigger jaws; III — a tongue of fire."""
    g = G["m"]
    y, z = 26.0, 2.0
    x = front_at(G, y, z)
    x = (x if x is not None else 8.0) + 0.2
    w, h = (3.6, 2.2) if t == 1 else (4.6, 2.8)
    g.box((x, y, z), (0.4, h, w), COAL)
    for sgn in (1, -1):
        g.box((x + 0.2, y + sgn * (h / 2 + 0.3), z), (0.9, 0.7, w + 0.8), M_DIRON)
        n = 4 if t == 1 else 5
        for i in range(n):
            zz = z - w / 2 + 0.5 + i * (w - 1.0) / (n - 1)
            spike(g, (x + 0.5, y + sgn * (h / 2 + 0.1), zz), (x + 0.6, y + sgn * (h / 2 - 0.9), zz), 0.32, M_STEEL)
    if t >= 3:
        for i, o in enumerate(((1.4, 0.0, 0.0), (2.8, 0.6, 0.2), (4.0, 1.2, -0.2))):
            G["fx"].ell(arr((x, y, z)) + arr(o), (1.0 - 0.15 * i, 0.8 - 0.1 * i, 1.2 - 0.2 * i), FLAME)
    return [("m", "chest")]


def g_greedy(G, info, t):
    """Жадная топка: a funnel on the near pauldron that swallows fire; II — wider, with a grille; III — a
    swallowed fireball glowing in it."""
    g = G["m"]
    base = shoulder_top(G, info, dx=-1.2, dz=0.4)
    d = unit(arr((0.45, 1.0, 0.2)))
    r = 1.8 if t == 1 else 2.6
    g.cyl(base, base + d * 2.0, 0.9, M_DIRON, seg=10)
    g.cyl(base + d * 2.0, base + d * 5.0, 1.0, M_IRON, r1=r, seg=14)
    g.cyl(base + d * 5.0, base + d * 5.3, r + 0.2, BRASS, seg=14)
    g.cyl(base + d * 4.6, base + d * 5.1, r - 0.3, COAL, seg=12)
    if t >= 2:
        side = unit(np.cross(d, arr((0, 0, 1.0))))
        for k in (-0.8, 0.0, 0.8):
            g.cyl(base + d * 5.25 + side * k * r - arr((0, 0, r * 0.8)), base + d * 5.25 + side * k * r + arr((0, 0, r * 0.8)), 0.12, M_STEEL, seg=4)
    if t >= 3:
        G["fx"].ell(base + d * 6.0, (1.2, 1.2, 1.2), FLAME)
        G["fx"].ell(base + d * 6.0, (0.6, 0.6, 0.6), COAL)
    return [("m", "pauldron_n"), ("m", "arm_n.ball"), ("m", "chest")]



# ================================================================ Орудие
def o_mortar(G, info, t):
    """Мортира: a stubby mortar on trunnions on the back, its mouth up and forward; II — bigger, banded;
    III — a pair of them."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    base = arr(((lo[0] + hi[0]) / 2 - 0.6, hi[1] + 0.2, 0.0))
    g.box(base + (0, 0.5, 0), (4.4, 1.0, 6.0), M_DIRON)
    r = 2.2 if t == 1 else 2.6
    zs = (0.0,) if t < 3 else (-2.9, 2.9)
    d = unit(arr((0.35, 1.0, 0.0)))
    for z in zs:
        c = base + arr((0, 3.2, z))
        g.cyl(c - arr((0, 0, r + 0.6)), c + arr((0, 0, r + 0.6)), 0.6, M_IRON, seg=6)  # trunnion
        g.cyl(c - d * 2.0, c + d * 5.0, r, M_IRON, r1=r * 0.92, seg=12)
        g.cyl(c + d * 5.0, c + d * 5.7, r + 0.4, M_DIRON, seg=12)
        g.ell(c + d * 5.75, (r * 0.75, 0.1, r * 0.75), M_HOLE, basis(c, c + d)[0] @ rot_z(np.pi / 2))
        if t >= 2:
            for k in (0.4, 2.2):
                g.cyl(c + d * k, c + d * (k + 0.45), r + 0.2, BRASS, seg=12)
    return [("m", "back"), ("m", "head")]


def o_long(G, info, t):
    """Длинный ствол: the near gun lengthened by an extension past its muzzle brake; II — longer, a second brake;
    III — longer still, a sighting scope on top."""
    g = G["m"]
    c = info["n"]
    m, d, up = c["muzzle"], c["d"], c["up"]
    L = {1: 6.0, 2: 9.0, 3: 12.0}[t]
    R = basis(m, m + d, up)[0] if False else None
    g.cyl(m - d * 0.4, m + d * L, 0.95, M_DIRON, seg=10)
    g.cyl(m - d * 0.4, m + d * 0.6, 1.35, M_IRON, seg=10)
    for k in np.arange(1.6, L - 0.5, 2.4):
        g.cyl(m + d * k, m + d * (k + 0.3), 1.1, M_IRON, seg=10)
    if t >= 2:
        g.cyl(m + d * L, m + d * (L + 1.4), 1.5, M_DIRON, seg=10)
        g.ell(m + d * (L + 1.45), (0.15, 0.8, 0.8), M_HOLE, np.column_stack([d, up, np.cross(d, up)]))
    if t >= 3:
        s0 = c["breech"] + up * 1.6
        g.cyl(s0, s0 + d * 6.0, 0.45, BRASS, seg=8)
        g.cyl(s0 + d * 6.0, s0 + d * 6.4, 0.6, GLASS, seg=8)
        for k in (1.0, 5.0):
            g.cyl(s0 + d * k, s0 + d * k - up * 1.4, 0.2, M_DIRON, seg=4)
    return [("m", "item_n")]


def spider_leg_fn(n_legs, armour=False):
    """Паучьи лапы: jointed legs out from the hips, spread wide, the body carried between them; armour (II) —
    painted plates on them; three a side at III, with claws."""
    def fn(G, key, hipj, knee, ankle, s, P, th=1.0):
        g = G[key]
        hipj = arr(hipj)
        axle(g, hipj, 2.0, 2.4, s)
        specs = [(7.0, 10.0), (-7.0, -9.0)] if n_legs == 2 else [(7.0, 10.5), (0.0, 0.5), (-7.0, -9.5)]
        for kx, fx_ in specs:
            kn = hipj + arr((kx * 0.7, 2.0, s * 7.5))
            ft = arr((hipj[0] + fx_, 0.4, s * (abs(hipj[2]) + 12.0 + (2.0 if abs(kx) < 1 else 0.0))))
            g.cyl(hipj, kn, 0.95, M_DIRON, seg=8)
            g.ell(kn, (1.25, 1.25, 1.25), M_IRON)
            g.cyl(kn, ft + (0, 1.4, 0), 0.8, M_DIRON, r1=0.45, seg=8)
            spike(g, ft + (0, 1.4, 0), ft, 0.45, M_STEEL)
            if armour:
                block(g, lerp(hipj, kn, 0.25), lerp(hipj, kn, 0.9), (1.8, 1.2), (1.6, 1.1), P, off=(0, 0, 0))
                block(g, lerp(kn, ft, 0.1), lerp(kn, ft, 0.55), (1.6, 1.0), (1.2, 0.8), P, off=(0, 0, 0))
            if n_legs >= 3:
                for dz in (-0.6, 0.6):
                    spike(g, ft + (0, 1.0, dz), ft + (0.9, 0.0, dz * 1.6), 0.25, M_STEEL)
    return fn


def o_spider(G, info, t):
    return []


def o_canister(G, info, t):
    """Картечь: a flared blunderbuss mouth on the near gun; II — a bandolier of canister rounds over the near
    pauldron; III — the far gun flared as well."""
    g = G["m"]
    for side in (("n",) if t < 3 else ("n", "f")):
        c = info[side]
        m, d = c["muzzle"], c["d"]
        g.cyl(m - d * 0.6, m + d * 2.6, 1.3, M_IRON, r1=2.7, seg=14)
        g.cyl(m + d * 2.6, m + d * 2.9, 2.85, BRASS, seg=14)
        g.ell(m + d * 2.95, (0.1, 2.3, 2.3), M_HOLE, np.column_stack([d, c["up"], np.cross(d, c["up"])]))
    if t >= 2:
        a = shoulder_top(G, info, dx=1.8, dz=0.0)
        b = arr((5.4, 26.0, -3.0))
        for i in range(6):
            p = lerp(a, b, (i + 0.5) / 6)
            g.cyl(p - arr((0, 0.7, 0)), p + arr((0, 0.7, 0)), 0.55, RED, seg=8)
            g.cyl(p + arr((0, 0.7, 0)), p + arr((0, 0.9, 0)), 0.55, BRASS, seg=8)
        g.cyl(a, b, 0.25, Mat(ramp("#1a0e08", "#2e1a10", "#46281a", "#603a26", "#7e5038")), seg=4)
    return [("m", "item_n"), ("m", "item_f"), ("m", "pauldron_n"), ("m", "chest"), ("m", "arm_n.ball")]


def o_hotshot(G, info, t):
    """Калёное ядро: a brazier on the back where the shot is heated — glowing coals, a red-hot ball; II — three
    balls; III — the near gun's bands glowing too."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    c = arr(((lo[0] + hi[0]) / 2 - 0.4, hi[1] + 0.4, 0.0))
    tbox(g, c + (0, 1.4, 0), (4.0, 5.0), (5.0, 6.4), 2.8, M_IRON)
    g.box(c + (0, 2.85, 0), (4.6, 0.3, 6.0), COAL)
    for x in (-1.6, 0.0, 1.6):
        g.box(c + (x, 2.95, 0), (0.25, 0.25, 6.2), M_DIRON)
    n = 1 if t == 1 else 3
    for i in range(n):
        g.ell(c + arr((0.4 * (i - 1), 3.9, (i - (n - 1) / 2) * 1.8)), (0.9, 0.9, 0.9), HOT)
    G["fx"].ell(c + (0, 6.0, 0), (1.6, 1.2, 1.6), Mat(ramp("#2a1a14", "#4a2e22", "#6e4632", "#96644a", "#c08a68"), dither=True))
    if t >= 3:
        cc = info["n"]
        for k in (-4.0, -7.0, -10.0):
            p = cc["muzzle"] + cc["d"] * k
            g.cyl(p, p + cc["d"] * 0.5, 1.25, HOT, seg=10)
    return [("m", "back"), ("m", "head"), ("m", "item_n")]


def o_bomb(G, info, t):
    """Бомба с фитилём: black bombs with brass bands and fuses hung from a strap at the outside of the near hip;
    II — two; III — three, a fuse lit."""
    g = G["m"]
    S = info["S"]
    y = S["hip"] - 1.0
    strap = arr((-0.6, y + 1.6, S["hz"] + 5.6))
    g.box(strap, (5.0, 0.8, 0.6), Mat(ramp("#1a0e08", "#2e1a10", "#46281a", "#603a26", "#7e5038")))
    for i in range(t):
        c = strap + arr((-1.6 + i * 1.8, -3.0 - (i % 2) * 0.8, 1.2))
        g.cyl(strap + arr((-1.6 + i * 1.8, 0, 0.3)), c + (0, 1.6, 0), 0.14, ROPE, seg=3)
        g.ell(c, (1.6, 1.6, 1.6), BOMB)
        g.cyl(c - (0, 0.15, 0), c + (0, 0.15, 0), 1.65, BRASS, seg=12)
        g.cyl(c + (0.6, 1.2, 0.6), c + (1.0, 1.7, 1.0), 0.4, M_IRON, seg=6)
        g.cyl(c + (1.0, 1.7, 1.0), c + (1.6, 2.6, 1.3), 0.14, ROPE, seg=3)
        if t >= 3 and i == t - 1:
            sparks(G["fx"], c + (1.7, 2.8, 1.4), n=5, spread=1.0, seed=2, big=False)
    return [("m", "pelvis"), ("m", "leg_n"), ("m", "leg_n.ram")]


# ================================================================ Механик
def m_repair(G, info, t):
    """Ремонт: a riveting gun in a holster at the belt; II — a stack of patch plates on the near pauldron;
    III — a bandolier of rivet cartridges across the chest."""
    g = G["m"]
    S = info["S"]
    y = S["hip"] - 0.4
    x = (front_at(G, y + 1.0, 0.0, keys=("pelvis",)) or 4.0) + 1.0
    g.box(arr((x, y - 0.6, 0.8)), (2.0, 4.0, 2.0), RED)
    g.box(arr((x + 0.3, y + 1.8, 0.8)), (3.4, 1.8, 1.6), M_STEEL)
    g.box(arr((x - 0.6, y + 0.6, 0.8)), (1.0, 2.0, 1.0), M_STEEL)
    g.cyl(arr((x + 2.0, y + 1.8, 0.8)), arr((x + 4.4, y + 1.8, 0.8)), 0.5, M_STEEL, seg=6)
    g.cyl(arr((x - 0.6, y + 1.6, 0.8)), arr((x - 1.4, y + 0.4, 0.8)), 0.25, M_HOSE, seg=4)
    if t >= 2:
        base = shoulder_top(G, info, dx=-0.6, dz=0.4)
        for i in range(3):
            g.box(base + arr((0, 0.35 + i * 0.6, 0)), (3.8 - i * 0.4, 0.45, 3.0 - i * 0.3),
                  Mat(ramp("#22262c", "#3e444e", "#646c78", "#949ca8", "#c8ced8")), rot_y(0.3 * i))
    if t >= 3:
        a, b = shoulder_top(G, info, dx=1.6, dz=-0.6), arr((4.8, 21.0, -4.0))
        for i in range(7):
            p = lerp(a, b, (i + 0.5) / 7)
            g.cyl(p - arr((0, 0.5, 0)), p + arr((0, 0.5, 0)), 0.42, BRASS, seg=6)
        g.cyl(a, b, 0.22, Mat(ramp("#1a0e08", "#2e1a10", "#46281a", "#603a26", "#7e5038")), seg=4)
    return [("m", "pelvis"), ("m", "pauldron_n"), ("m", "chest"), ("m", "arm_n.ball"), ("m", "spine")]


def m_crane(G, info, t):
    """Кран: a small jib crane standing up from the tool chest, its hook out over the head; II — a longer jib;
    III — a winch drum and a counterweight."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    base = arr(((lo[0] + hi[0]) / 2, hi[1] - 0.2, 0.0))
    top = base + arr((0, 13.0, 0))
    lattice(g, base, top, 1.6, BRASS, up=(1, 0, 0), r=0.28, tri=False)
    L = 11.0 if t == 1 else 15.0
    tip = top + arr((L, 1.0, 0.0))
    lattice(g, top + (0.4, -0.8, 0), tip, 1.4, BRASS, n=6, r=0.24)
    g.cyl(top + (0, 1.6, 0), tip, 0.1, M_DIRON, seg=4)
    g.cyl(top, top + (0, 1.6, 0), 0.3, M_DIRON, seg=4)
    hook = tip + arr((0, -5.0, 0))
    g.cyl(tip, hook, 0.1, M_DIRON, seg=4)
    g.box(hook - (0, 0.5, 0), (0.8, 1.1, 0.8), M_DIRON)
    g.cyl(hook - (0, 1.0, 0), hook - (0, 2.0, 0), 0.2, M_STEEL, seg=4)
    if t >= 3:
        g.cyl(top + (-1.2, -4.0, -1.4), top + (-1.2, -4.0, 1.4), 1.0, M_DIRON, seg=10)
        g.box(top + arr((-4.0, -0.6, 0)), (2.4, 2.4, 2.4), STONE)
        g.cyl(top + (-0.8, -0.4, 0), top + (-3.0, -0.4, 0), 0.3, BRASS, seg=4)
    return [("m", "back"), ("m", "manip")]


def m_spares(G, info, t):
    """Запасные части: a crate of parts on the belt with a gear in it; II — a bigger crate, a piston sticking out;
    III — and a sack of cogs at the hip."""
    g = G["m"]
    S = info["S"]
    y = S["hip"] - 1.0
    x = (front_at(G, y + 1.0, 0.0, keys=("pelvis",)) or 4.0) + 1.9
    w = 3.0 if t == 1 else 3.8
    g.box(arr((x, y - 0.6, 0.2)), (w * 0.8, w * 0.8, w), Mat(ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844")))
    g.box(arr((x, y - 0.6, 0.2)), (w * 0.8 + 0.1, 0.4, w + 0.1), M_DIRON)
    c = arr((x + 0.2, y + w * 0.4 + 0.2, 0.6))
    g.cyl(c - arr((0, 0, 0.3)), c + arr((0, 0, 0.3)), 1.0, M_STEEL, seg=10)
    for i in range(8):
        a = 2 * np.pi * i / 8
        g.box(c + arr((np.cos(a), np.sin(a), 0)) * 1.15, (0.45, 0.4, 0.6), M_STEEL, rot_z(a))
    if t >= 2:
        HM_ram = ram
        HM_ram(g, arr((x - 0.4, y + w * 0.3, -0.8)), arr((x + 1.8, y + w * 0.3 + 2.4, -1.2)), 0.45)
    if t >= 3:
        sk = arr((x - 1.2, y - 3.6, 3.6))
        g.ell(sk, (1.6, 1.9, 1.5), Mat(ramp("#2a2014", "#4a3a22", "#6e5a38", "#968050", "#bea870")))
        g.cyl(sk + (0, 1.8, 0), arr((x - 1.0, y + 0.6, 2.6)), 0.15, M_HOSE, seg=3)
        for i, o in enumerate(((0.6, 1.6, 0.8), (-0.4, 1.9, 0.2))):
            g.cyl(sk + arr(o) - arr((0, 0, 0.2)), sk + arr(o) + arr((0, 0, 0.2)), 0.55, M_STEEL, seg=8)
    return [("m", "pelvis"), ("m", "leg_n"), ("m", "leg_f")]


def m_oiler(G, info, t):
    """Маслёнка: a big oil can on the near pauldron, its long spout forward; II — a tank on the back feeding it;
    III — a second spout, oil dripping."""
    g = G["m"]
    base = shoulder_top(G, info, dx=-0.4, dz=1.6)
    c = base + arr((0, 2.0, 0))
    TIN = Mat(ramp("#1e2228", "#3a404a", "#606874", "#949ca8", "#d0d6de"))
    g.cyl(base, base + (0, 4.2, 0), 1.8, TIN, r1=1.2, seg=12)
    g.cyl(base + (0, 4.2, 0), base + (0, 4.7, 0), 0.6, TIN, seg=8)
    g.cyl(base + (0, 1.2, 0), base + (0, 1.5, 0), 1.75, RED, seg=12)
    sp = unit(arr((1.0, 0.45, 0.25)))
    tips = []
    for k, o in enumerate(((0, 0, 0),) if t < 3 else ((0, 0, -0.5), (0, 0, 0.6))):
        a = c + arr((1.2, 0.0, 0)) + arr(o)
        tip = a + sp * 6.5
        g.cyl(a, tip, 0.4, M_STEEL, r1=0.16, seg=6)
        tips.append(tip)
    if t >= 2:
        lo, hi = box_of(G, "back")
        tank = arr((lo[0] - 1.2, 24.0, 4.4))
        g.cyl(tank, tank + (0, 6.0, 0), 1.4, OIL, seg=10)
        g.cyl(tank + (0, 6.0, 0), tank + (0, 6.5, 0), 0.8, BRASS, seg=8)
        g.cyl(tank + (0, 6.5, 0), base + (-0.8, 0.8, 0), 0.24, M_HOSE, seg=4)
    if t >= 3:
        for i, tip in enumerate(tips):
            G["fx"].ell(tip + arr((0.2, -1.4 - i * 0.6, 0)), (0.25, 0.4, 0.25), OIL)
    return [("m", "pauldron_n"), ("m", "arm_n.ball"), ("m", "back"), ("m", "manip"), ("m", "chest")]


def m_welding(G, info, t):
    """Сварка: a gas bottle strapped behind the tool chest, standing over the shoulder; II — two bottles (red and
    blue) with hoses to the torch; III — a dark welding visor down over the lamp, sparks at the torch."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    x = lo[0] - 1.6
    bottles = [(RED, 2.8)] + ([(BLUE, -1.2)] if t >= 2 else [])
    for mat, z in bottles:
        b = arr((x, 18.0, z))
        canister(g, b, 1.5, 20.0, mat, cap=M_STEEL)
        g.cyl(b + (0, 6.0, 0), b + (0, 6.6, 0), 1.6, M_DIRON, seg=10)
    if t >= 2:
        tip = info.get("tips", {}).get("n", arr((5.0, 40.0, 9.0)))
        for mat, z in bottles:
            g.cyl(arr((x, 39.0, z)), tip + arr((-1.5, -0.6, 0)), 0.2, M_HOSE, seg=4)
    if t >= 3:
        lo_h, hi_h = box_of(G, "head")
        g.box(arr((hi_h[0] + 0.4, (lo_h[1] + hi_h[1]) / 2 + 0.6, 0)), (0.4, 4.0, 5.0), Mat(ramp("#060a08", "#0e1a14", "#1a2e24", "#2e4a3c", "#4e7a64")))
        g.box(arr((hi_h[0] + 0.2, hi_h[1] - 0.8, 0)), (1.0, 0.5, 5.2), M_DIRON)
        tip = info.get("tips", {}).get("n", arr((5.0, 40.0, 9.0)))
        sparks(G["fx"], tip + arr((0.8, 0, 0)), n=8, spread=2.6, seed=6, big=True)
        G["fx"].ell(tip + arr((0.6, 0, 0)), (1.0, 1.0, 1.0), ENERGY)
    return [("m", "back"), ("m", "manip"), ("m", "head")]


def m_oiltank(G, info, t):
    """Масляный бак: a barrel of oil slung on the back, out over the near side, with a hand pump; II — bigger;
    III — a hose to a spray lance, oil spattering."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    r = 2.0 if t == 1 else 2.5
    c = arr((-6.4, 25.0, hi[2] + r + 0.6))
    g.cyl(c - arr((0, 3.4, 0)), c + arr((0, 3.4, 0)), r, OIL, seg=14)
    for k in (-2.6, 0.0, 2.6):
        g.cyl(c + arr((0, k, 0)), c + arr((0, k + 0.35, 0)), r + 0.1, M_DIRON, seg=14)
    g.cyl(c + arr((0, 1.0, 0)), c + arr((0, 1.8, 0)), r + 0.05, RED, seg=14)
    g.cyl(c + arr((0, 3.4, 0)), c + arr((0, 5.4, 0)), 0.3, M_STEEL, seg=6)
    g.cyl(c + arr((-1.2, 5.4, 0)), c + arr((1.2, 5.4, 0)), 0.3, M_IRON, seg=6)
    if t >= 3:                                         # a spray lance over the near shoulder, spattering oil ahead
        a = c + arr((0.6, 3.0, 0.6))
        via = arr((-2.0, 35.0, a[2] + 1.6))
        lance = arr((4.0, 34.0, a[2] + 2.0))
        g.cyl(a, via, 0.24, M_HOSE, seg=4)
        g.cyl(via, lance, 0.3, BRASS, seg=6)
        g.cyl(lance, lance + arr((0.6, 0, 0)), 0.5, BRASS, r1=0.3, seg=6)
        for i in range(4):
            G["fx"].ell(lance + arr((1.6 + i * 1.2, -0.4 - i * 0.7, 0.2 * i)), (0.4, 0.35, 0.35), OIL)
    return [("m", "back"), ("m", "manip"), ("m", "item_f"), ("m", "hand_f"), ("m", "arm_f"), ("m", "arm_n.ram")]


FRAMES = {
    "Мудрец": [("chain", "Цепная молния", "разряд перескакивает на 2 врагов, III — на 4", s_chain, {}),
               ("ground", "Разряд в землю", "каждые 3 хода оглушает врагов вокруг, III — радиус 2", s_ground, {}),
               ("overload", "Перегрузка", "раз в 2 хода сосед бьёт вдвое сильнее", s_overload, {}),
               ("fireball", "Огненный шар", "каждые 3 хода: шар на 5 клеток, поджигает", s_fireball, {}),
               ("firewall", "Огненная стена", "раз за бой: стена огня на 3 клетки", s_firewall, {}),
               ("blades", "Раскалённые клинки", "раз в 2 хода сосед поджигает всех, кого бьёт", s_blades, {})],
    "Горн": [("magnet", "Магнит", "стягивает врагов в радиусе 3, III — Отталкивание", g_magnet, {}),
             ("rod", "Громоотвод", "вражеские молнии и снаряды летят в него", g_rod, {}),
             ("smoke", "Дымовая труба", "соседние клетки в дыму: стрелки промахиваются", g_smoke, {}),
             ("whistle", "Паровой свисток", "каждые 4 хода пугает врагов в радиусе 2", g_whistle, {}),
             ("maw", "Пасть топки", "каждые 2 хода выдыхает огонь на 2 клетки", g_maw, {}),
             ("greedy", "Жадная топка", "глотает огненные снаряды, третий — выплёвывает", g_greedy, {})],
    "Орудие": [("mortar", "Мортира", "каждые 3 хода навесной залп по клетке и соседним", o_mortar, {}),
               ("long", "Длинный ствол", "бьёт самого дальнего врага насквозь", o_long, {}),
               ("spider", "Паучьи лапы", "переступает через мелких, отходит от вплотную", o_spider, {"spider": True}),
               ("canister", "Картечь", "в упор стреляет конусом, сбивает летунов", o_canister, {}),
               ("hotshot", "Калёное ядро", "ядро катится дальше, оставляя горящую дорожку", o_hotshot, {}),
               ("bomb", "Бомба с фитилём", "каждые 3 хода бомба: шипит 2 раунда и взрывается", o_bomb, {})],
    "Механик": [("repair", "Ремонт", "каждые 2 хода чинит самого повреждённого рядом", m_repair, {}),
                ("crane", "Кран", "раз за бой поднимает сломанного соседа", m_crane, {}),
                ("spares", "Запасные части", "сломался сосед — его модуль не теряет уровень", m_spares, {}),
                ("oiler", "Маслёнка", "сосед ходит первым в раунде", m_oiler, {}),
                ("welding", "Сварка", "чинит соседа, искры обжигают врагов рядом", m_welding, {}),
                ("oiltank", "Масляный бак", "обливает врага маслом: огонь жжёт вдвое", m_oiltank, {})],
}



# ================================================================ rare modules (any frame) and cores
def r_torch(G, info, t):
    """Живой факел: the golem sets itself alight — flames on its shoulders and head; II — on its arms and thighs;
    III — wrapped in fire, glowing."""
    fx = G["fx"]
    pts = []
    for key in ("pauldron_n", "pauldron_f", "head"):
        lo, hi = box_of(G, key)
        pts.append(arr(((lo[0] + hi[0]) / 2, hi[1], (lo[2] + hi[2]) / 2)))
    if t >= 2:
        for side in ("n", "f"):
            pts.append(lerp(info["el_" + side], info["w_" + side], 0.5) + arr((0, 1.6, 0)))
        for (h, k, a, s_) in info["legs"]:
            pts.append(lerp(h, k, 0.5) + arr((0.8, 1.0, s_ * 1.6)))
    if t >= 3:
        lo, hi = box_of(G, "chest")
        pts += [arr((hi[0], (lo[1] + hi[1]) / 2, z)) for z in (-3.0, 3.0)]
        pts += [arr((lo[0] - 1.0, hi[1] - 2.0, z)) for z in (-3.0, 3.0)]
    for i, p in enumerate(pts):
        sz = 1.0 + 0.35 * t
        fx.ell(p + arr((0, sz * 0.9, 0)), (sz * 0.8, sz * 1.5, sz * 0.8), FLAME)
        fx.ell(p + arr((0.3, sz * 2.2, 0.2)), (sz * 0.45, sz * 0.9, sz * 0.45), FLAME)
    return []


def r_nozzles(G, info, t):
    """Сопла: rocket nozzles on the outside of the back pointing down; II — three, with fins; III — they fire."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    zs = (hi[2] + 5.2,) if t < 2 else (hi[2] + 5.2, hi[2] + 8.6)
    g.box(arr((lo[0] + 3.4, 33.0, hi[2] + 2.0)), (3.0, 2.0, 4.0), M_DIRON)                    # the bracket off the back
    for z in zs:
        top = arr((lo[0] + 3.4, 34.0, z))
        g.cyl(top, top - (0, 6.0, 0), 1.5, M_DIRON, seg=10)
        g.cyl(top - (0, 6.0, 0), top - (0, 8.4, 0), 1.2, M_IRON, r1=2.0, seg=10)
        g.cyl(top - (0, 8.3, 0), top - (0, 8.5, 0), 1.5, M_HOLE, seg=10)
        g.cyl(top + (0, 0, -2.2), top + (0, 0, 0), 0.8, M_IRON, seg=6)
        g.cyl(top + (0, 0.4, 0), top + (0, 1.4, 0), 0.8, M_IRON, r1=0.2, seg=8)
        if t >= 2:
            for d in ((1, 0, 0), (-1, 0, 0)):
                g.box(top - (0, 4.4, 0) + arr(d) * 1.4, (1.2, 2.4, 0.25), M_IRON)
        if t >= 3:
            for i in range(5):
                G["fx"].ell(top - arr((0.4 * i, 9.4 + i * 1.8, 0)), (1.6 - 0.2 * i, 1.6, 1.6 - 0.2 * i), FLAME)
    return [("m", "back"), ("m", "robe"), ("m", "arm_n"), ("m", "arm_f"), ("m", "pauldron_n"), ("m", "pauldron_f")]


def r_bounce(G, info, t):
    """Скачущее ядро: ribbed red-hot balls with spring bands in a rack on the back, over the shoulders; II — two;
    III — three, and a spring cup on the near gun to bounce them off."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    base = arr((lo[0] + 3.0, hi[1] + 2.4, hi[2] + 5.6))           # a rack out over the near shoulder, clear of the head
    n = t
    g.box(base + (0, 0.4, 0), (2.6 * n + 0.6, 0.8, 3.4), M_DIRON)
    g.cyl(arr((lo[0] + 3.0, hi[1] - 1.0, hi[2] - 0.5)), base + (0, 0.2, -1.4), 0.6, M_DIRON, seg=6)
    for i in range(n):
        c = base + arr(((i - (n - 1) / 2) * 2.6, 2.4, 0))
        g.ell(c, (1.3, 1.3, 1.3), HOT)
        g.cyl(c - arr((0, 0.22, 0)), c + arr((0, 0.22, 0)), 1.42, M_DIRON, seg=10)
        g.cyl(c - arr((0.22, 0, 0)), c + arr((0.22, 0, 0)), 1.42, M_DIRON, seg=10)
        g.box(c - arr((0, 1.6, 0)), (0.6, 0.6, 0.6), M_IRON)
    if t >= 3:
        c = info["n"]
        m, d = c["muzzle"], c["d"]
        for k in range(5):
            p = m + d * (0.6 + k * 0.5)
            g.cyl(p, p + d * 0.25, 1.9, M_STEEL, seg=10)
    return [("m", "back"), ("m", "head"), ("m", "item_n"), ("m", "pauldron_n"), ("m", "arm_n.ball")]


def r_whirl(G, info, t):
    """Огненный смерч: a ducted fan on the back over the near shoulder; II — bigger, more blades;
    III — a spiral of fire coming off it."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    c = arr((lo[0] + 1.6, 40.0, hi[2] + 1.2))
    r = 3.0 if t == 1 else 4.0
    ax = unit(arr((0.0, 0.3, 1.0)))
    g.cyl(c - ax * 0.8, c + ax * 0.8, r + 0.4, M_IRON, seg=16)
    g.cyl(c - ax * 0.85, c + ax * 0.85, r - 0.1, M_HOLE, seg=16)
    sd = unit(np.cross(ax, arr((1.0, 0, 0))))
    fw = unit(np.cross(sd, ax))
    nb = 4 if t == 1 else 6
    for i in range(nb):
        a = 2 * np.pi * i / nb
        dd = np.cos(a) * sd + np.sin(a) * fw
        g.box(c + dd * r * 0.5 + ax * 0.9, (0.4, 0.3, 0.3) + abs(dd) * r * 0.9, M_STEEL)
    g.ell(c + ax * 1.0, (0.8, 0.8, 0.8), BRASS)
    g.cyl(c - ax * 0.8, arr((lo[0] + 1.0, 33.0, hi[2] - 1.0)), 0.6, M_DIRON, seg=6)
    if t >= 3:
        for i in range(10):
            a = i * 0.9
            p = c + ax * (1.6 + i * 0.6) + (np.cos(a) * sd + np.sin(a) * fw) * (1.0 + i * 0.25)
            G["fx"].ell(p, (0.6, 0.6, 0.6), FLAME)
    return [("m", "back"), ("m", "pauldron_n"), ("m", "arm_n.ball")]


def r_grapple(G, info, t):
    """Крюк-кошка: a launcher tube on the near pauldron pointing forward, a four-pronged hook in its mouth;
    II — a chain drum behind it; III — bigger, barbed."""
    g = G["m"]
    base = shoulder_top(G, info, dx=-0.6, dz=1.0)
    d = unit(arr((1.0, 0.15, 0.1)))
    a, b = base + arr((-2.4, 1.4, 0)), base + arr((-2.4, 1.4, 0)) + d * 7.0
    g.box(base + (0, 0.4, 0), (2.4, 0.8, 2.0), M_DIRON)
    g.cyl(a, b, 1.0, M_DIRON, seg=10)
    for k in (1.0, 3.5, 6.0):
        g.cyl(a + d * k, a + d * (k + 0.5), 1.12, RED, seg=10)
    g.cyl(b, b + d * 0.5, 1.25, M_IRON, seg=10)
    hk = b + d * 1.4
    s_ = 1.3 if t < 3 else 1.8
    g.cyl(b + d * 0.4, hk, 0.4, M_STEEL, seg=6)
    up = arr((0, 1.0, 0))
    side = unit(np.cross(d, up))
    for v in (side, -side, up, -up):
        p = hk + v * 0.2
        q = p + d * 1.2 * s_ + v * 1.2 * s_
        g.cyl(p, q, 0.32, M_STEEL, seg=4)
        g.cyl(q, q - d * 0.8 * s_ + v * 0.3, 0.26, M_STEEL, seg=4)
        if t >= 3:
            spike(g, q, q + v * 0.8, 0.2, M_STEEL)
    if t >= 2:
        c = a - d * 1.6
        g.cyl(c - side * 1.2, c + side * 1.2, 1.5, M_IRON, seg=10)
        for k in range(3):
            g.cyl(c - side * 0.9 + side * k * 0.8, c - side * 0.6 + side * k * 0.8, 1.7, CHAIN, seg=10)
    return [("m", "pauldron_n"), ("m", "arm_n.ball"), ("m", "manip"), ("m", "head"), ("m", "chest")]


def millstone_leg(t):
    """Колёса-жернова: the legs are millstones on axles; II — iron-banded; III — spiked."""
    def fn(G, key, hipj, knee, ankle, s, P, th=1.0):
        g = G[key]
        hipj = arr(hipj)
        R = 7.0
        c = arr((hipj[0] + 0.4, R + 0.3, hipj[2] + s * 1.6))
        block(g, hipj, c + (0, 1.0, 0), (2.6, 2.4), (2.2, 2.2), M_DIRON)
        ax = arr((0, 0, s * 1.0))
        bc = c + ax * 2.6
        g.cyl(c, bc + ax * 1.4, 1.0, M_DIRON, seg=8)
        G[key + ".ram"].cyl(bc - ax * 1.2, bc + ax * 1.2, R, STONE, seg=20)
        for a in np.linspace(0, np.pi, 4)[:-1]:                                     # dressing grooves
            dd = arr((np.cos(a), np.sin(a), 0))
            G[key + ".ram"].box(bc + ax * 1.22, (2 * R * 0.9, 0.3, 0.1), M_DIRON, rot_z(a))
        g.cyl(bc + ax * 1.2, bc + ax * 1.6, 1.4, M_IRON, seg=10)
        if t >= 2:
            G[key + ".ram"].cyl(bc - ax * 1.25, bc + ax * 1.25, R + 0.25, M_DIRON, seg=20)
            G[key + ".ram"].cyl(bc - ax * 1.3, bc + ax * 1.3, R - 0.4, STONE, seg=20)
        if t >= 3:
            for i in range(10):
                a = 2 * np.pi * i / 10
                p = bc + arr((np.cos(a), np.sin(a), 0)) * (R + 0.2)
                spike(G[key + ".ram"], p, p + arr((np.cos(a), np.sin(a), 0)) * 1.6, 0.45, M_STEEL)
    return fn


def r_mill(G, info, t):
    return [("leg_n", "leg_n.ram"), ("leg_f", "leg_f.ram"), ("leg_n", "pelvis"), ("leg_f", "pelvis"), ("leg_f.ram", "item_f")]


def r_dome(G, info, t):
    """Щит-купол: a dome of plates on a mast from the back, held over its head; II — bigger, riveted;
    III — spiked rim and a rune."""
    g = G["m"]
    lo, hi = box_of(G, "back")
    lo_h, hi_h = box_of(G, "head")
    top = max(hi[1], hi_h[1]) + 4.0
    mast = arr((lo[0] + 1.0, hi[1] - 6.0, 0.0))
    c = arr(((lo_h[0] + hi_h[0]) / 2 - 1.0, top, 0.0))
    g.cyl(mast, c - (0, 1.0, 0), 0.5, M_DIRON, seg=6)
    r = 7.0 if t == 1 else 9.0
    n = 10
    for i in range(n):
        a0, a1 = 2 * np.pi * i / n, 2 * np.pi * (i + 1) / n
        p0 = c + arr((np.cos(a0) * r, -1.6, np.sin(a0) * r))
        p1 = c + arr((np.cos(a1) * r, -1.6, np.sin(a1) * r))
        g.solid([c + (0, 1.6, 0), p0, p1, c + (0, 1.2, 0)], [[0, 1, 2], [1, 2, 3], [0, 1, 3], [0, 2, 3]],
                Mat(info["S"]["paint"]) if i % 2 else M_IRON)
    g.ell(c + (0, 1.7, 0), (0.9, 0.6, 0.9), BRASS)
    if t >= 2:
        for i in range(n):
            a = 2 * np.pi * (i + 0.5) / n
            g.ell(c + arr((np.cos(a) * r * 0.7, -0.5, np.sin(a) * r * 0.7)), (0.3, 0.3, 0.3), M_STEEL)
    if t >= 3:
        for i in range(n):
            a = 2 * np.pi * i / n
            p = c + arr((np.cos(a) * r, -1.6, np.sin(a) * r))
            spike(g, p, p + arr((np.cos(a) * 1.6, -0.6, np.sin(a) * 1.6)), 0.35, M_STEEL)
        g.box(c + arr((r * 0.55, -0.2, 0)), (0.2, 0.5, 2.0), HOT)
    return [("m", "back"), ("m", "head"), ("m", "item_n")]


def r_bomb_core(G, info, t):
    """Котёл-бомба (ядро): the core turned into a pressure bomb — a big gauge on the breast, needle in the red;
    II — a hissing safety valve, hazard stripes; III — bulging red-hot plates."""
    g = G["m"]
    y, z = 27.0, 3.4
    x = (front_at(G, y, z) or 8.0) + 0.3
    c = arr((x, y, z))
    g.cyl(c, c + (0.6, 0, 0), 2.2, BRASS, seg=16)
    g.cyl(c + (0.6, 0, 0), c + (0.75, 0, 0), 1.85, Mat(ramp("#c8c0a8", "#dcd4bc", "#ece6d2", "#f8f4e8", "#ffffff")), seg=16)
    g.box(c + (0.8, 0.5, 0.5), (0.1, 0.25, 0.25), RED)
    g.box(c + (0.82, 0.6, 0.7), (0.1, 1.6, 0.18), M_DIRON, rot_x(-0.9))
    if t >= 2:
        v = c + arr((-1.0, 4.0, -1.0))
        g.cyl(v, v + (0, 1.6, 0), 0.5, BRASS, seg=8)
        g.cyl(v + (0, 1.6, 0), v + (0, 2.0, 0), 0.9, BRASS, seg=8)
        G["fx"].ell(v + (0, 3.4, 0), (1.0, 1.6, 1.0), STEAM)
        for k in range(4):
            g.box(c + arr((0.2, -3.2, -2.4 + k * 1.6)), (0.3, 1.0, 0.8), RED if k % 2 else Mat(ramp("#2a2406", "#6a5a10", "#b09a1a", "#e8d03a", "#fff090")), rot_x(0.6))
    if t >= 3:
        for dz in (-3.4, 3.4):
            g.ell(c + arr((-0.4, -1.0, dz - 3.4 + 3.4)), (0.9, 2.2, 1.4), HOT)
    return [("m", "chest"), ("m", "hose")]


def r_ram(G, info, t):
    """Таранный нос: an iron wedge on the breast; II — bigger, riveted; III — «Клин»: blades out to the sides."""
    g = G["m"]
    y = 25.0
    x = (front_at(G, y, 0.0) or 6.0) - 0.4
    L = 4.0 if t == 1 else 5.6
    base = [arr((x, y + 3.0, -3.0)), arr((x, y + 3.0, 3.0)), arr((x, y - 3.0, 3.0)), arr((x, y - 3.0, -3.0))]
    tip = arr((x + L, y, 0.0))
    g.solid(base + [tip], [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], M_IRON)
    g.box(arr((x - 0.2, y, 0)), (0.6, 6.6, 6.6), M_DIRON)
    if t >= 2:
        rivets(g, [arr((x + 0.4, y + yy, zz)) for yy in (-2.4, 2.4) for zz in (-2.4, 2.4)], r=0.35)
    if t >= 3:
        for sz in (-1, 1):
            g.solid([arr((x + 1.0, y + 1.0, sz * 2.6)), arr((x + 1.0, y - 1.0, sz * 2.6)), arr((x + 2.4, y, sz * 7.0)),
                     arr((x + 3.0, y, sz * 2.0))], [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], M_STEEL)
    return [("m", "chest"), ("m", "spine"), ("m", "pelvis"), ("m", "item_n"), ("m", "item_f")]


def r_buffer(G, info, t):
    """Отбойник: a pneumatic pusher on the near gun: a flat pad on a piston; II — a bigger pad on a spring;
    III — the pad studded with spikes."""
    g = G["m"]
    c = info["n"]
    m, d, up = c["muzzle"], c["d"], c["up"]
    side = unit(np.cross(d, up))
    base = c["breech"] + up * 0.8 + side * 1.8
    L = 9.0
    ram(g, base, base + d * L, 0.6)
    pad = base + d * (L + 0.6)
    R = np.column_stack([d, up, side])
    s_ = 1.0 if t == 1 else 1.4
    g.box(pad, (0.8, 3.2 * s_, 3.2 * s_), M_IRON, R)
    if t >= 2:
        for k in range(5):
            p = base + d * (2.0 + k * 0.6)
            g.cyl(p, p + d * 0.2, 1.1, CHAIN, seg=10)
    if t >= 3:
        for a in (-1, 0, 1):
            for b in (-1, 1):
                q = pad + up * a * 1.3 * s_ + side * b * 1.1 * s_
                spike(g, q + d * 0.3, q + d * 1.8, 0.4, M_STEEL)
    return [("m", "item_n"), ("m", "arm_n")]


def spark_hammer_fn(t):
    """Искрящий молот: in place of the wrench, a sledge with a flint striking face; II — heavier; III — the face
    glowing, sparks."""
    def fn(G, side, sh, el, w, s, P, A, S):
        u = GH.grip_dir(w - el, arr((0.3, -0.95, 0.0)))
        hand, h, u = GH.fist(G, "hand_" + side, w, w - el, u, s, P, th=0.85)
        g = G["item_" + side]
        g.cyl(hand - u * 2.0, hand + u * 8.0, 0.65, Mat(ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844")), seg=6)
        head = hand + u * 9.2
        v = unit(np.cross(u, arr((0, 0, 1.0)))) if abs(u[2]) < 0.9 else arr((1.0, 0, 0))
        R = np.column_stack([u, v, np.cross(u, v)])
        k = 1.0 if t == 1 else 1.3
        g.box(head, (2.4 * k, 5.0 * k, 2.4 * k), M_IRON, R)
        for sg in (1, -1):
            g.box(head + v * sg * 2.7 * k, (2.0 * k, 0.6, 2.0 * k), STONE if t < 3 else HOT, R)
        if t >= 3:
            sparks(G["fx"], head + v * 3.4 * k, n=7, spread=2.4, seed=9, big=True)
        return dict(head=head)
    return fn


def r_spark(G, info, t):
    return [("hand_n", "item_n")]


def poker_fn(t):
    """Кочерга: in place of the tongs, a long iron poker with a hooked tip; II — longer, the tip glowing;
    III — a flame on the hook."""
    def fn(G, side, sh, el, w, s, P, A, S):
        d = unit(w - el)
        G["hand_" + side].ell(w + d * 0.3, (1.9, 1.9, 1.9), M_DIRON)
        g = G["item_" + side]
        L = 12.0 if t == 1 else 15.0
        a, b = w + d * 1.2, w + d * L
        g.cyl(w + d * 0.6, w + d * 2.0, 0.9, M_IRON, seg=8)
        g.cyl(a, b, 0.5, M_IRON, seg=6)
        hk = unit(d + arr((0, 1.0, 0)) * 0.9)
        tip = b + hk * 2.2
        g.cyl(b, tip, 0.45, HOT if t >= 2 else M_IRON, seg=6)
        g.cyl(b - d * 2.0, b, 0.55, HOT if t >= 2 else M_DIRON, seg=6)
        if t >= 3:
            for i, o in enumerate(((0, 1.2, 0), (0.3, 2.2, 0.2))):
                G["fx"].ell(tip + arr(o), (0.6 - 0.15 * i, 1.0 - 0.2 * i, 0.6 - 0.15 * i), FLAME)
        return dict(tip=tip)
    return fn


def r_poker(G, info, t):
    return []


def core_fn(kind):
    """Ядро: a porthole on the breast showing what burns inside — Литое: a solid cast iron cap bolted on;
    Огненное: an orange window with a grate; Грозовое: a blue window with arcs."""
    def fn(G, info, t):
        g = G["m"]
        y, z = 31.6, 2.6
        x = (front_at(G, y, z) or 6.0) + 0.2
        c = arr((x, y, z))
        g.cyl(c - (0.2, 0, 0), c + (0.7, 0, 0), 3.2, M_DIRON, seg=16)
        rivets(g, [c + arr((0.75, np.sin(a) * 2.8, np.cos(a) * 2.8)) for a in np.linspace(0, 2 * np.pi, 9)[:-1]], r=0.32)
        if kind == "cast":
            g.ell(c + (0.8, 0, 0), (0.8, 2.4, 2.4), Mat(ramp("#22262c", "#3e444e", "#646c78", "#949ca8", "#c8ced8")))
            g.box(c + (1.5, 0, 0), (0.3, 0.6, 2.6), M_DIRON)
        elif kind == "fire":
            g.cyl(c + (0.6, 0, 0), c + (0.8, 0, 0), 2.5, COAL, seg=16)
            for zz in (-1.2, 0.0, 1.2):
                g.box(c + (0.9, 0, zz), (0.2, 4.6, 0.3), M_DIRON)
            G["fx"].ell(c + (1.4, 2.4, 0), (0.6, 1.0, 0.6), FLAME)
        else:
            g.cyl(c + (0.6, 0, 0), c + (0.8, 0, 0), 2.5, GH.ENERGY, seg=16)
            for i, dd in enumerate(((0.6, 2.4, 1.6), (0.4, -1.8, 2.6), (0.8, 2.0, -2.2))):
                zigzag(G["fx"], c + (0.9, 0, 0), c + arr(dd) + (1.0, 0, 0), n=3, amp=0.4, seed=i, r=0.14)
        return [("m", "chest"), ("m", "item_n"), ("m", "item_f"), ("m", "arm_n"), ("m", "head")]
    return fn


RARE = [("torch", "Живой факел", "горит весь бой: всё, чего касается, загорается", "Орудие", r_torch, {}),
        ("nozzles", "Сопла", "раз за бой огненный рывок на 4 клетки", "Мудрец", r_nozzles, {}),
        ("bounce", "Скачущее ядро", "отскакивает от врага к врагу 3 раза, поджигает", "Орудие", r_bounce, {}),
        ("whirl", "Огненный смерч", "горящие клетки сливаются в бродящий смерч", "Горн", r_whirl, {}),
        ("grapple", "Крюк-кошка", "цепляет врага из второго ряда и тянет к себе", "Механик", r_grapple, {}),
        ("mill", "Колёса-жернова", "катится по прямой и давит всё на пути", "Горн", r_mill, {"mill": True}),
        ("dome", "Щит-купол", "накрывает соседние клетки от стрел", "Мудрец", r_dome, {}),
        ("bombcore", "Котёл-бомба", "ядро: при поломке взрывается и отбрасывает всех", "Горн", r_bomb_core, {}),
        ("ram", "Таранный нос", "разгон по прямой, первый удар двойной; III — Клин", "Механик", r_ram, {}),
        ("buffer", "Отбойник", "отбрасывает врага; о стену — урон двойной", "Орудие", r_buffer, {}),
        ("spark", "Искрящий молот", "по броне высекает искры, соседние клетки горят", "Механик", r_spark, {"item_n": "spark"}),
        ("poker", "Кочерга", "отбрасывает врага в горящую клетку", "Горн", r_poker, {"item_f": "poker"})]
CORES = [("cast", "Литое", "без стихии, но голем прочнее"), ("fire", "Огненное", "удары поджигают цель"),
         ("volt", "Грозовое", "цепная молния, оглушает механизмы")]


def rare_parts(key, t=1):
    _, name, desc, frame, fn, over = next(r for r in RARE if r[0] == key)
    so = {}
    if over.get("mill"):
        so["leg_fn"] = millstone_leg(t)
    if over.get("item_n") == "spark":
        so["item_n"] = spark_hammer_fn(t)
    if over.get("item_f") == "poker":
        so["item_f"] = poker_fn(t)
    G, info, allow = golem(frame, **so)
    return G, allow + fn(G, info, t), frame


def core_parts(kind, frame="Орудие"):
    G, info, allow = golem(frame)
    return G, allow + core_fn(kind)(G, info, 2), frame


def render_parts(G, frame, k):
    S = GH.BY_NAME[frame]
    cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
    cw, ch, cy = cw + 20, ch + 16, cy + 6
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def module(frame, key):
    return next(m for m in FRAMES[frame] if m[0] == key)


def parts(frame, key, t=1):
    _, _, _, fn, over = module(frame, key)
    so = dict(over.get("S", {}))
    A = None
    if over.get("spider"):                            # on spider legs the guns are carried up, out of the legs' way
        so["leg_fn"] = spider_leg_fn(2 if t < 3 else 3, armour=t >= 2)
        Sx = GH.BY_NAME[frame]
        L = Sx["poses"]["attack_level"]
        A = dict(Sx["poses"]["idle"], fx=None, **{k: L[k] for k in ("hand_n", "hand_f", "pole_n", "pole_f", "ram_n", "ram_f")})
    G, info, allow = golem(frame, A=A, **so)
    allow = allow + fn(G, info, t)
    return G, allow


def check(frame, key, t=1):
    G, allow = parts(frame, key, t)
    return report(G, allow, skip=("fx",))


def build(frame, key, t=1, k=1.6):
    S = GH.BY_NAME[frame]
    G, _ = parts(frame, key, t)
    cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
    cw, ch, cy = cw + 20, ch + 16, cy + 6
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def check_rare():
    from PIL import Image
    from paths import out
    rows = []
    for key in [r[0] for r in RARE]:
        row = []
        for t in (1, 2, 3):
            G, allow, frame = rare_parts(key, t)
            bad = report(G, allow, skip=("fx",))
            if bad:
                print(key, t, bad)
            im = render_parts(G, frame, 2.0).image(1)
            bb = im.getbbox()
            row.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
        rows.append(row)
    row = []
    for kind, _, _ in CORES:
        G, allow, frame = core_parts(kind)
        bad = report(G, allow, skip=("fx",))
        if bad:
            print(kind, bad)
        im = render_parts(G, frame, 2.0).image(1)
        bb = im.getbbox()
        row.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
    rows.append(row)
    lines = [rows[i:i + 2] for i in range(0, len(rows), 2)]
    W = max(sum(sum(i.width + 10 for i in r) + 30 for r in ln) for ln in lines)
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
    sheet.save(out("rare_check.png"))


if __name__ == "__main__":
    import sys
    from PIL import Image
    from paths import out
    if sys.argv[1:] == ["rare"]:
        check_rare()
        sys.exit()
    frame = sys.argv[1] if len(sys.argv) > 1 else "Мудрец"
    keys = sys.argv[2:] or [m[0] for m in FRAMES[frame]]
    rows = []
    for key in keys:
        row = []
        for t in (1, 2, 3):
            bad = check(frame, key, t)
            if bad:
                print(frame, key, t, bad)
            im = build(frame, key, t, k=3.0).image(1)
            bb = im.getbbox()
            row.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
        rows.append(row)
    lines = [rows[i:i + 2] for i in range(0, len(rows), 2)]
    W = max(sum(sum(i.width + 10 for i in r) + 30 for r in ln) for ln in lines)
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
    sheet.save(out("frame_modules_check.png"))
    print("ok")
