"""The Maniac's constructs on the humanoid golems. "Free assembly": any module goes on any frame, and his crazy
modules go where no module should — saw blades for legs, a catapult for a head, a fist on a spring, a third and
fourth arm, a golem walking on its hands. Every illegal part carries the Maniac's mark: purple and green sparks.

Improvisation: for a turn a module of a neighbouring construct becomes something else — the maul spews flame,
the shield opens into a saw.

    python3 tools/sprites/constructs.py      -> out/constructs_check.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_STEEL, M_RUST, M_HOLE, M_HOSE, emissive, spike, tbox, STYLE1
from golem7 import M_PUFF
import golems_h as GH
import humanoid as HM
from golems_h import (arr, unit, lerp, rivets, sparks, puffs, Parts, ik, place_upper, basis, axle, gear, ram, block,
                      fist, mad_specks, SAW, PATCH_G, PATCH_B, RUST_P, BRASS_P, MAD, MADG, ARC, ENERGY)
from clipcheck import report, cells, STEP

GLOVE = Mat(ramp("#2a0606", "#5a0e0e", "#9a1c1c", "#d0402e", "#f08060"))
ROPE = Mat(ramp("#2a2014", "#4a3a22", "#6e5a38", "#968050", "#bea870"))
WOOD = Mat(ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844"))
FLAME = Mat(FIRE, emissive=hexc("#ff8a30"), glow_r=7, glow_k=0.55)
BUG = Mat(ramp("#120a14", "#2a1430", "#46244e", "#6a3a72", "#94609a"))
ROCKET = [Mat(ramp("#2a0606", "#6a1010", "#b02a1a", "#e8603a", "#ffb090")),
          Mat(ramp("#06142a", "#0e2a6a", "#1a50b0", "#3a8ae8", "#90c8ff")),
          Mat(ramp("#2a2406", "#6a5a10", "#b09a1a", "#e8d03a", "#fff090"))]
STAR = [Mat(ramp("#5a1460", "#9a2aa0", "#d860d0", "#ffc0f4", "#ffffff"), emissive=hexc("#e060e0"), glow_r=8, glow_k=0.6),
        Mat(ramp("#145a20", "#2aa040", "#70e080", "#d0ffd8", "#ffffff"), emissive=hexc("#60f080"), glow_r=8, glow_k=0.6),
        Mat(ramp("#6a4a10", "#b08a1a", "#f0c840", "#fff0a0", "#ffffff"), emissive=hexc("#ffd060"), glow_r=8, glow_k=0.6)]


def mark(g, c, seed=0, n=3, r=1.6):
    """The Maniac's mark on an illegal part: purple and green sparks."""
    mad_specks(g, c, n=n, r=r, seed=seed)


def extent(G, key):
    """The bounding box of a group, from its grid cells."""
    c = np.array(list(cells(G[key]))) * STEP
    return c.min(0), c.max(0)


def frame_parts(S, A):
    G, info = GH.creature_parts(S, A, fx=False)
    return G, info, GH.BASE_ALLOWED + S.get("allow", [])


# ---------------------------------------------------------------- Ноги-пилы: the legs are saw blades
SAW_R = 7.4


def saw_leg(G, key, hipj, knee, ankle, s, P, th=1.0, spin=0.0):
    """A strut from the hip down to the hub of a circular saw that the construct rolls on."""
    g = G[key]
    hipj = arr(hipj)
    c = arr((hipj[0] + 0.6, SAW_R + 0.3, hipj[2] + s * 1.4))
    block(g, hipj, c + (0, 1.0, 0), (2.6, 2.4), (2.0, 2.0), M_DIRON)
    block(g, lerp(hipj, c, 0.15), lerp(hipj, c, 0.75), (1.0, 2.8), (1.0, 2.4), Mat(RUST_P), off=(1.4, 0, 0))
    ax = arr((0, 0, s * 1.0))
    bc = c + ax * 1.9                                                  # the blade, outside the strut
    g.cyl(c, bc + ax * 0.6, 1.0, M_DIRON, seg=8)
    G[key + ".ram"].cyl(bc - ax * 0.25, bc + ax * 0.25, SAW_R, SAW, seg=24)
    for i in range(22):
        a = 2 * np.pi * i / 22 + spin
        G[key + ".ram"].box(bc + arr((np.cos(a), np.sin(a), 0)) * (SAW_R + 0.35), (0.9, 0.55, 0.4), SAW, rot_z(a + 0.5))
    g.ell(bc + ax * 0.4, (1.4, 1.4, 0.3), M_IRON)
    for i in range(4):                                                 # a patched guard over the back of the blade
        a = 1.7 + i * 0.42
        d = arr((np.cos(a), np.sin(a), 0))
        g.box(bc + d * (SAW_R + 1.0) + ax * 0.2, (2.2, 0.5, 1.6), Mat(PATCH_G if i % 2 else PATCH_B), rot_z(a + np.pi / 2))
    mark(g, c + (0, 3.0, 0), seed=int(s + 2))


def saw_legs(t="idle"):
    S = dict(GH.SAGE)
    spin = 0.0 if t == "idle" else 0.13
    S["leg_fn"] = lambda G, key, h, k, a, s, P, th=1.0: saw_leg(G, key, h, k, a, s, P, th, spin)
    A = dict(S["poses"]["idle"], fx=None)
    if t != "idle":
        A.update(lean=-0.12, t=(1.0, 0.0, 0.0))
    G, info, allow = frame_parts(S, A)
    if t != "idle":                                    # rolling into them, cutting: sparks off the front of the blades
        for z in (-1, 1):
            p = arr((GH.SAGE["hipx"][0] + 0.6 + SAW_R * 0.85, 1.4, z * (GH.SAGE["hz"] + 3.3)))
            sparks(G["fx"], p, n=7, spread=3.0, seed=5 + z, big=True)
            G["fx"].ell(p + (-3.0, 0.8, 0), (2.4, 1.2, 1.8), M_PUFF)
    return G, allow + [("leg_n", "leg_n.ram"), ("leg_f", "leg_f.ram"), ("leg_n", "pelvis"), ("leg_f", "pelvis"),
                       ("leg_n.ram", "robe"), ("leg_f.ram", "robe"), ("leg_n", "robe"), ("leg_f", "robe")]


# ---------------------------------------------------------------- Голова-катапульта: a catapult for a head
def catapult(g, base, arm_a, cup_scrap=True, fire=False, L=9.0, R=I3):
    """A small torsion catapult: two cheeks, a rope skein, a throwing arm at angle arm_a (from straight up,
    + forward), a cup at its end."""
    base = arr(base)
    P = lambda v: base + R @ arr(v)
    g.box(P((0, 0.4, 0)), (4.0, 0.8, 4.4), M_DIRON, R)
    for z in (-1.7, 1.7):
        g.box(P((0, 2.2, z)), (2.6, 3.4, 0.6), WOOD, R)                               # cheeks
    g.cyl(P((0, 2.6, -2.2)), P((0, 2.6, 2.2)), 0.9, ROPE, seg=8)                      # the skein
    d = R @ arr((np.sin(arm_a), np.cos(arm_a), 0))
    piv = P((0, 2.6, 0))
    tip = piv + d * L
    g.cyl(piv, tip, 0.45, WOOD, seg=6)
    g.cyl(lerp(piv, tip, 0.3), lerp(piv, tip, 0.34), 0.6, M_IRON, seg=6)
    cup = tip + d * 0.6
    g.cyl(cup - d * 0.4, cup + d * 0.5, 1.5, M_IRON, r1=1.9, seg=10)               # the cup
    if cup_scrap:
        g.ell(cup + d * 0.9, (1.2, 0.9, 1.1), M_RUST)
        g.box(cup + d * 1.0 + (0.6, 0.6, 0.2), (1.4, 0.4, 0.6), M_STEEL, rot_z(0.6))
    if fire:
        for i, o in enumerate(((0, 2.4, 0), (0.9, 3.6, 0.6), (-0.8, 3.2, -0.6), (0.2, 4.6, 0))):
            g.ell(cup + d * 1.2 + arr(o), (1.2 - 0.15 * i, 1.8 - 0.2 * i, 1.2 - 0.15 * i), FLAME)
    return dict(piv=piv, tip=tip, cup=cup, d=d)


def catapult_head(t="idle", frame="Орудие"):
    S = GH.BY_NAME[frame]
    A = dict(S["poses"]["idle"], fx=None)
    G, info, allow = frame_parts(S, A)
    lo, hi = extent(G, "head")
    del G["head"]
    neck = arr(((lo[0] + hi[0]) / 2, lo[1] + 0.6, (lo[2] + hi[2]) / 2))
    a = -0.55 if t == "idle" else 1.1                  # cocked up and back; flung forward
    c = catapult(G["head"], neck, a, cup_scrap=(t == "idle"), L=13.0)
    mark(G["head"], neck + (1.4, 2.4, 2.4), seed=7)
    if t != "idle":                                    # a lump of scrap on its way over the front rank
        for i, o in enumerate(((10.0, 6.0, 0.0), (12.5, 4.6, 1.4), (11.6, 7.4, -1.2))):
            p = c["cup"] + arr(o)
            G["fx"].box(p, (1.6 - 0.3 * i, 1.0, 1.2), M_RUST if i == 0 else M_STEEL, rot_z(0.7 * i) @ rot_x(0.4 * i))
    return G, allow + [("head", "chest"), ("head", "back"), ("head", "manip"), ("head", "pauldron_n"), ("head", "pauldron_f")]


# ---------------------------------------------------------------- Кулак на пружине: a fist on a spring
def spring_fist(G, side, sh, el, w, s, P, A, S):
    g = G["item_" + side]
    d = unit(w - el)
    G["hand_" + side].ell(w + d * 0.4, (1.8, 1.8, 1.8), M_DIRON)
    ext = 2.8 if not A.get("punch") else 15.0
    a, b = w + d * 1.2, w + d * (1.2 + ext)
    n = 6 if not A.get("punch") else 11
    for i in range(n):
        p = lerp(a, b, (i + 0.5) / n)
        g.cyl(p - d * 0.2, p + d * 0.2, 1.5, GH.SAW, seg=10)
    g.cyl(a, b, 0.4, M_DIRON, seg=6)
    R, _ = basis(b, b + d)
    gc = b + d * 2.2                                                  # a big boxing glove riveted to an iron plate
    g.box(b + d * 0.3, (0.8, 3.6, 3.6), M_IRON, R)
    g.ell(gc, (2.6, 2.4, 2.4), GLOVE, R)
    g.ell(gc + R @ arr((0.4, 1.4, 1.6)), (1.0, 0.9, 1.0), GLOVE, R)
    g.cyl(b + d * 0.6, b + d * 1.4, 1.6, Mat(ramp("#2a2420", "#4a423a", "#6e645a", "#968a7e", "#c0b4a6")), seg=10)
    mark(g, w + d * 1.5 + (0, 2.0, 0), seed=11)
    return dict(glove=gc, d=d)


def fist_construct(t="idle"):
    S = dict(GH.MEH, item_n=spring_fist)
    A = dict(S["poses"]["idle"], fx=None)
    if t != "idle":
        A.update(hand_n=(9.6, -5.0, 0.4), pole_n=(-0.6, -0.6, 0.8), lean=-0.1, punch=True)
    G, info, allow = frame_parts(S, A)
    if t != "idle":                                    # the blow lands a cell ahead and throws the enemy back
        gc, d = info["n"]["glove"], info["n"]["d"]
        G["fx"].ell(gc + d * 2.6, (0.8, 3.0, 3.0), ENERGY, basis(gc, gc + d)[0])
        sparks(G["fx"], gc + d * 2.8, n=6, spread=3.0, seed=12, big=True)
        for i in range(3):
            G["fx"].ell(gc + d * (3.4 + i) + arr((0, (i - 1) * 2.0, 0)), (1.6, 0.6, 0.6), M_PUFF)
    return G, allow + [("hand_n", "item_n"), ("arm_n", "item_n")]


# ---------------------------------------------------------------- Рука-рука-рука: more arms
def extra_arm(G, key, sh, hand, pole, P, tool, th=0.72):
    """One more arm bolted on a plate at the shoulder, with a hammer or a claw."""
    LU, LF = 6.6, 7.2
    el, w = ik(sh, sh + arr(hand), LU, LF, pole)
    G[key + ".plate"].box(sh + (-0.6, 0, 0), (3.6, 3.6, 1.2), Mat(PATCH_B))
    HM.arm(G, key, sh, el, w, 1, P, ram_side="back", th=th, cuff=False)
    d = unit(w - el)
    g = G[key + ".tool"]
    if tool == "hammer":                               # a sledge in the fist
        hand_, h, u = fist(G, key + ".hand", w, w - el, arr((0, 1.0, 0)) - d * d[1] + arr((0.3, 0, 0)), 1, P, th=0.7)
        top = hand_ + u * 8.0
        g.cyl(hand_ - u * 1.8, top, 0.5, WOOD, seg=6)
        Rh, _ = basis(top - u, top + u, d)
        g.box(top + u * 1.2, (5.6, 3.0, 3.0), M_IRON, Rh)
        g.box(top + u * 1.2 + Rh @ arr((2.9, 0, 0)), (0.4, 2.6, 2.6), M_STEEL, Rh)
        return dict(head=top + u * 1.2, face=top + u * 1.2 + Rh @ arr((3.2, 0, 0)))
    side = unit(np.cross(d, arr((0, 0, 1.0))))
    G[key + ".hand"].ell(w + d * 0.4, (1.4, 1.4, 1.4), M_DIRON)
    for sg in (1, -1):                                 # a scrap claw
        k = w + d * 1.0 + side * 1.0 * sg
        g.cyl(w + d * 0.6, k + d * 2.0, 0.45, M_RUST, seg=5)
        g.cyl(k + d * 2.0, k + d * 3.4 - side * 0.9 * sg, 0.38, M_STEEL, seg=5)
    return dict(tip=w + d * 3.6)


def triple_arm(t="idle", frame="Орудие"):
    S = GH.BY_NAME[frame]
    A = dict(S["poses"]["idle"], fx=None)
    G, info, allow = frame_parts(S, A)
    X = info["X"]
    P = Mat(S["paint"])
    s1, s2 = X(S["sh"] + arr((-2.2, 6.2, -0.6))), X(S["sh"] * arr((1, 1, -1)) + arr((-2.6, 5.4, 1.2)))
    if t == "idle":
        h1 = extra_arm(G, "arm_x1", s1, (3.0, 11.0, 2.6), (-0.6, 0.0, 1.0), P, "hammer")
    else:                                               # the hammer's turn: brought down in front
        h1 = extra_arm(G, "arm_x1", s1, (11.0, -2.0, 1.6), (-0.4, 1.0, 0.6), P, "hammer")
        sparks(G["fx"], h1["face"], n=6, spread=2.4, seed=21, big=True)
        G["fx"].ell(h1["face"], (1.6, 1.6, 1.6), emissive("fire", 8, 0.6))
    extra_arm(G, "arm_x2", s2, (8.0, 6.0, -3.0), (-0.6, 0.4, -1.0), P, "claw")
    for s_ in (s1, s2):
        mark(G["back"], s_ + (-1.6, 1.4, 1.2), seed=int(s_[1]))
    extra = []
    for k in ("arm_x1", "arm_x2"):
        extra += [(k, k + ".plate"), (k, k + ".ball"), (k, "back"), (k, k + ".ram"), (k + ".ram", k + ".ball"), (k + ".plate", k + ".ball"),
                  (k + ".plate", "pauldron_n"), (k + ".plate", "chest"), (k + ".plate", "back"), (k + ".ball", "pauldron_n"),
                  (k + ".ball", "chest"), (k + ".ball", "back"), (k, k + ".hand"), (k + ".hand", k + ".tool"), (k, k + ".tool"),
                  (k + ".plate", "hose"), (k + ".ball", "hose"), (k + ".plate", "pauldron_f"), (k + ".ball", "pauldron_f")]
    return G, allow + extra


# ---------------------------------------------------------------- Вверх ногами: walking on its hands
def wheel_hand(G, side, sh, el, w, s, P, A, S):
    """The forearm ends in a wheel (the construct stands on it, upside down)."""
    g = G["item_" + side]
    d = unit(w - el)
    G["hand_" + side].ell(w + d * 0.4, (1.8, 1.8, 1.8), M_DIRON)
    c = w + d * 3.6
    ax = arr((0, 0, s * 1.0))
    g.cyl(w + d * 0.8, c, 0.8, M_DIRON, seg=6)
    g.cyl(c - ax * 1.6, c + ax * 1.6, 3.4, M_HOSE, seg=16)                              # a cart tyre
    g.cyl(c - ax * 1.7, c + ax * 1.7, 1.6, Mat(RUST_P), seg=10)
    for i in range(6):
        a = 2 * np.pi * i / 6
        g.box(c + arr((np.cos(a), np.sin(a), 0)) * 2.3 + ax * 1.65, (2.2, 0.4, 0.2), M_IRON, rot_z(a))
    return dict(c=c, r=3.4)


def upside_down(t="idle"):
    S = dict(GH.SAGE, item_n=wheel_hand, item_f=wheel_hand)
    A = dict(S["poses"]["idle"], fx=None)
    A.update(hand_n=(0.6, 15.0, 1.6), pole_n=(-1.0, 0.0, 0.3), hand_f=(0.6, 15.0, -1.6), pole_f=(-1.0, 0.0, -0.3))
    if t == "idle":                                     # the feet up in the air with hammers on them
        A["ank"] = ((2.0, 2.0, 5.0), (-3.0, 2.6, -5.0))
    else:
        A["ank"] = ((9.0, 6.0, 5.0), (-5.0, 1.0, -5.0))
    G, info, allow = frame_parts(S, A)
    from augments import leg_joints
    for h, kn, an, s in leg_joints(S, A):               # sledge heads on the soles (below them, before the flip)
        g = G["hammer_" + ("n" if s > 0 else "f")]
        d = unit(an - kn)
        g.cyl(an + d * 1.0, an + d * 6.0, 0.55, WOOD, seg=6)
        Rh, _ = basis(an + d * 6.0, an + d * 7.0, arr((1.0, 0, 0)))
        g.box(an + d * 7.2, (3.2, 2.6, 5.0), M_IRON, Rh)
        mark(g, an + d * 3.0 + arr((0, 0, s * 1.6)), seed=30 + s)
    wy = max(info["n"]["c"][1], info["f"]["c"][1]) + 3.4
    for k in list(G):                                   # turned over: the wheels on the ground, the hammers up
        G[k] = G[k].transformed(rot_x(np.pi), (0, wy, 0))
    if t != "idle":
        top = max(np.array(list(cells(G["hammer_n"]))) * STEP, key=lambda p: p[1]) if cells(G["hammer_n"]) else arr((0, 0, 0))
        sparks(G["fx"], arr(top) + (2.0, 0.0, 0.0), n=5, spread=2.0, seed=31, big=False)
    return G, allow + [("hammer_n", "leg_n"), ("hammer_f", "leg_f"), ("hand_n", "item_n"), ("hand_f", "item_f")]


# ---------------------------------------------------------------- Пылающая катапульта: a burning enemy thrown back
def burning_catapult(t="idle", frame="Горн"):
    S = GH.BY_NAME[frame]
    A = dict(S["poses"]["idle"], fx=None)
    G, info, allow = frame_parts(S, A)
    lo, hi = extent(G, "back")
    base = arr((lo[0] + 2.0, hi[1] + 0.2, 0.0))
    a = -0.75 if t == "idle" else 0.7
    g = G["cat"]
    tbox(g, base + (0.6, -0.6, 0), (6.0, 6.0), (5.0, 5.0), 1.6, Mat(PATCH_G))
    c = catapult(g, base + (0.4, 0.0, 0.0), a, cup_scrap=False, fire=(t == "idle"), L=16.0)
    mark(g, base + (2.0, 3.0, 3.0), seed=40)
    bug = Model()                                       # a swarm soldier, caught and set alight
    bug.ell((0, 0, 0), (2.8, 1.6, 1.9), BUG)
    bug.ell((2.8, 0.4, 0), (1.4, 1.2, 1.2), BUG)
    for z in (-1, 1):
        for x in (-1.4, 0.0, 1.4):
            bug.cyl((x, -0.5, z * 1.3), (x + 0.8, -2.4, z * 3.0), 0.28, BUG, seg=4)
        bug.cyl((3.8, 0.8, z * 0.5), (5.4, 1.8, z * 1.2), 0.2, BUG, seg=4)
    if t == "idle":
        g.extend(bug.transformed(rot_z(0.4), c["cup"] + c["d"] * 1.4))
    else:                                               # flung back into its own rank, burning
        p = c["cup"] + arr((14.0, 8.0, 0.0))
        G["fx"].extend(bug.transformed(rot_z(-0.8), p))
        for i, o in enumerate(((0, 2.2, 0), (-1.6, 3.2, 0.8), (1.2, 2.8, -0.8), (-3.0, 1.4, 0), (-4.4, 2.6, 0.4))):
            G["fx"].ell(p + arr(o), (1.5 - 0.15 * i, 2.2 - 0.25 * i, 1.5 - 0.15 * i), FLAME)
    return G, allow + [("cat", "back"), ("cat", "chest"), ("cat", "head")]


# ---------------------------------------------------------------- Салют: a rocket battery that goes off when it breaks
def salute(t="idle", frame="Горн"):
    S = GH.BY_NAME[frame]
    A = dict(GH.broken_pose(S) if t != "idle" else S["poses"]["idle"])
    A["fx"] = None
    G, info, allow = frame_parts(S, A)
    X = info["X"]
    g = G["rack"]
    base = X(S["sh"] * arr((1, 1, 0)) + arr((-7.2, 3.6, 4.6)))      # on the back, beside the stack
    Rr = (rot_z(A["lean"]) @ rot_y(A.get("twist", 0.0))) @ rot_z(0.25)
    g.box(base, (3.0, 1.0, 5.6), Mat(PATCH_B), Rr)
    for i, (dz, dx) in enumerate(((-1.8, 0.0), (0.0, 0.4), (1.8, 0.0), (-0.9, -1.2), (0.9, -1.2))):
        p0 = base + Rr @ arr((dx, 0.6, dz))
        d = Rr @ unit(arr((0.25, 1.0, dz * 0.12)))
        if t == "idle":                                  # rockets in their tubes, fuses out
            g.cyl(p0, p0 + d * 8.0, 0.8, ROCKET[i % 3], seg=6)
            g.cyl(p0 + d * 8.0, p0 + d * 10.0, 0.8, ROCKET[i % 3], r1=0.05, seg=6)
            g.cyl(p0 - d * 0.2, p0 + d * 0.8, 1.0, M_DIRON, seg=6)
            g.cyl(p0 - d * 0.6, p0 - d * 1.6, 0.1, ROPE, seg=3)
        else:
            g.cyl(p0, p0 + d * 1.6, 0.6, M_DIRON, seg=6)  # empty tubes
    mark(g, base + (0, 2.0, 0), seed=50)
    if t != "idle":                                      # fireworks over five cells
        for i, c in enumerate(((14.0, 40.0, 10.0), (26.0, 30.0, -6.0), (4.0, 50.0, -12.0), (34.0, 44.0, 6.0), (20.0, 56.0, 0.0))):
            c = arr(c)
            m = STAR[i % 3]
            G["fx"].ell(c, (1.2, 1.2, 1.2), m)
            for j in range(8):
                a = 2 * np.pi * j / 8 + i
                G["fx"].cyl(c, c + arr((np.cos(a), np.sin(a), 0.4 * np.cos(a * 2))) * 4.2, 0.25, m, r1=0.05, seg=4)
        GH.broken_fx(G["fx"], info)
    return G, allow + [("rack", "back"), ("rack", "chest"), ("rack", "hose"), ("rack", "manip")]


# ---------------------------------------------------------------- Импровизация on the Guard
def improvised(which, after=False):
    A = dict(HM.ATTACKS["level" if which == "hammer" else "ram"], fx=None)
    G, info = HM.pose_parts(A, fx=False)
    allow = list(HM.ALLOWED)
    fx = G["fx"]
    if which == "hammer" and after:                     # the maul spews flame both ways
        hc, tf = info["hc"], info["tf"]
        for sgn in (1, -1):
            for i in range(5):
                p = hc + tf * sgn * (5.5 + i * 2.2) + arr((0, 0.6 * i, 0))
                fx.ell(p, (1.6 + 0.4 * i, 1.4 + 0.3 * i, 1.6 + 0.4 * i), FLAME)
        mad_specks(fx, hc, n=8, r=6.0, seed=60)
        icon = hc + arr((0, 9.0, 0))
        fx.ell(icon, (1.4, 1.8, 1.4), FLAME)
    elif which == "shield" and after:                   # the shield opens into a saw
        sc, R = info["sc"], info["R"]
        del G["shield"]
        g = G["shield"]
        ax = R @ arr((1.0, 0, 0))
        g.cyl(sc - ax * 0.4, sc + ax * 0.4, 8.6, SAW, seg=28)
        for i in range(26):
            a = 2 * np.pi * i / 26
            d = R @ arr((0, np.cos(a), np.sin(a)))
            g.box(sc + d * 9.0, (0.4, 1.0, 1.0), SAW, R @ rot_x(a + 0.6))
        g.cyl(sc - ax * 0.6, sc + ax * 1.6, 1.6, M_DIRON, seg=10)
        mad_specks(fx, sc, n=8, r=9.0, seed=61)
        icon = sc + arr((0, 13.0, 0))
        g2 = Model()
        g2.cyl((0, 0, -0.2), (0, 0, 0.2), 1.8, SAW, seg=12)
        fx.extend(g2.transformed(rot_y(0.6), icon))
    if after:
        fx.ell(icon, (2.6, 2.6, 0.3), Mat(ramp("#2a0a2a", "#5a1460", "#9a2aa0", "#d860d0", "#ffc0f4")), rot_y(0.6))
    return G, allow


CONSTRUCTS = {
    "saw": ("Ноги-пилы", "Мудрец", "постоянно: катится и режет всех на пути", saw_legs),
    "catapult": ("Голова-катапульта", "Орудие", "каждые 2 хода: лом через строй во 2-й ряд", catapult_head),
    "fist": ("Кулак на пружине", "Механик", "каждые 3 хода: удар через клетку, отбрасывает", fist_construct),
    "triple": ("Рука-рука-рука", "Орудие", "каждый ход: молот, клешня и пушка по очереди", triple_arm),
    "upside": ("Вверх ногами", "Мудрец", "ходит на руках-колёсах, ноги машут молотами", upside_down),
    "burning": ("Пылающая катапульта", "Горн", "каждые 3 хода: швыряет горящего врага в его же строй", burning_catapult),
    "salute": ("Салют", "Горн", "при поломке: фейерверк по 5 клеткам", salute),
}


def parts(key, t="idle"):
    return CONSTRUCTS[key][3](t)


def check(key, t="idle"):
    G, allow = parts(key, t)
    return report(G, allow, skip=("fx",))


def render_parts(G, k, canvas=(110, 100, 46, 84)):
    cw, ch, cx, cy = canvas
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def build(key, t="idle", k=1.3):
    G, _ = parts(key, t)
    return render_parts(G, k)


def build_improvised(which, after, k=1.3):
    G, _ = improvised(which, after)
    return render_parts(G, k, canvas=(110, 100, 46, 84))


if __name__ == "__main__":
    import sys
    from PIL import Image
    from paths import out
    ims = []
    for key in (sys.argv[1:] or list(CONSTRUCTS)):
        for t in ("idle", "go"):
            bad = check(key, t)
            if bad:
                print(key, t, bad)
            im = build(key, t, k=2.0).image(1)
            bb = im.getbbox()
            ims.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
    if not sys.argv[1:]:
        for which in ("hammer", "shield"):
            for after in (False, True):
                G, allow = improvised(which, after)
                bad = report(G, allow, skip=("fx", "sparks"))
                if bad:
                    print("improvised", which, after, bad)
                im = build_improvised(which, after, k=1.6).image(1)
                bb = im.getbbox()
                ims.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
    per = 6
    rows = [ims[i:i + per] for i in range(0, len(ims), per)]
    W = max(sum(i.width + 10 for i in r) for r in rows)
    H = sum(max(i.height for i in r) + 12 for r in rows)
    sheet = Image.new("RGBA", (W, H), (52, 46, 58, 255))
    y = 0
    for r in rows:
        x, h = 0, max(i.height for i in r)
        for i in r:
            sheet.alpha_composite(i, (x, y + h - i.height))
            x += i.width + 10
        y += h + 12
    sheet.save(out("constructs_check.png"))
    print("ok")
