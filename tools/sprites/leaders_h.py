"""The Foundry's human leaders in the style of the humanoid golems (golems_h): the Inventor and the
Architect. Built from the same kit — bones and IK, parts by groups, the clipping check — with what
golems do not have: human sleeves and hands, faces, hair, goggles.

    python3 tools/sprites/leaders_h.py      -> out/leaders_h.png (a close-up check sheet)
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_STEEL, M_HOLE, M_GLASS, M_HOSE, emissive, spike, tbox, STYLE1
from golem7 import M_PUFF
import golems_h as GH
from golems_h import arr, unit, lerp, rivets, grip_dir, sparks, puffs, ENERGY, ARC, BRASS, COPPER, Parts
from leaders import SKIN, LEATHER, LINEN

COAT = ramp("#0a0e1c", "#161f38", "#243258", "#36487c", "#5468a2")              # the Inventor's blue frock coat
BRASS_P = Mat(ramp("#1c1206", "#3e2a0e", "#6a4a1a", "#9a722c", "#ccA04a".lower()))
GREY_HAIR = Mat(ramp("#3a3a3e", "#5e5e64", "#8a8a90", "#b4b4ba", "#dedee2"))
WOOD = Mat(ramp("#1a0e06", "#34200e", "#553418", "#7a4e26", "#a06c3a"))
LENS = Mat(ramp("#1a3a4a", "#2a6a8a", "#4aa8d0", "#8ad8f0", "#d8f6ff"))                 # goggle glass: bright, but no glow
SPARK = Mat(ramp("#2a6a8a", "#4aa8d0", "#8ad8f0", "#c8f2ff", "#ffffff"), emissive=hexc("#70e0ff"), glow_r=4, glow_k=0.45)                          # small lit things: the bulb, the toroid


def zigzag(m, a, b, n=6, amp=1.0, seed=0, r=0.3, mat=ARC):
    """A jagged discharge from a to b."""
    rnd = np.random.RandomState(seed)
    a, b = arr(a), arr(b)
    pts = [a] + [lerp(a, b, i / n) + arr(rnd.uniform(-1, 1, 3)) * amp * (1 - abs(2 * i / n - 1) * 0.5) for i in range(1, n)] + [b]
    for p, q in zip(pts[:-1], pts[1:]):
        m.cyl(p, q, r, mat, seg=4)
    return pts


# ---------------------------------------------------------------- human parts
def sleeve_arm(cloth, cuff_mat=LINEN):
    """A human arm in a coat sleeve: upper arm, elbow, forearm, a linen cuff at the wrist."""
    def draw(G, key, sh, elbow, wrist, s, P, ram_side="back", th=1.0, cuff=True):
        g = G[key]
        sh, elbow, wrist = arr(sh), arr(elbow), arr(wrist)
        G[key + ".ball"].ell(sh, (1.3, 1.3, 1.3), cloth)
        g.cyl(sh + unit(elbow - sh) * 1.1, elbow, 1.0, cloth, r1=0.9, seg=8)
        g.ell(elbow, (0.95, 0.95, 0.95), cloth)
        g.cyl(elbow, wrist - unit(wrist - elbow) * 0.4, 0.9, cloth, r1=0.85, seg=8)
        g.cyl(wrist - unit(wrist - elbow) * 0.9, wrist, 0.95, cuff_mat, seg=8)                    # the cuff
        return wrist
    return draw


def glove(G, key, wrist, d, up, s):
    """A gloved hand closed round a grip at the wrist; returns the grip point."""
    g = G[key]
    d, up = unit(d), unit(up)
    side = unit(np.cross(d, up)) * s
    c = arr(wrist) + d * 0.9
    g.ell(c, (1.0, 0.85, 0.75), LEATHER)
    g.ell(c + d * 0.6 - up * 0.3 + side * 0.15, (0.55, 0.5, 0.6), LEATHER)                   # fingers
    g.ell(c + up * 0.55 + d * 0.2 + side * 0.4, (0.45, 0.3, 0.35), LEATHER)                  # thumb
    return c


def human_head(G, hc, R=I3, hair="wild", mustache=True, goggles="eyes", cap=None, face=SKIN):
    """A head at hc facing +x: skull, nose, ears, hair, mustache, goggles, an optional cap."""
    hd = G["head"]
    hc = arr(hc)
    P = lambda v: hc + R @ arr(v)
    hd.cyl(P((-0.4, -2.6, 0)), P((-0.2, -1.4, 0)), 0.9, face, seg=8)                         # neck
    hd.ell(hc, (1.85, 2.15, 1.75), face, R)                                                  # skull
    hd.ell(P((1.75, -0.2, 0)), (0.45, 0.55, 0.38), face, R)                                   # nose
    for z in (-1.7, 1.7):
        hd.ell(P((-0.1, -0.1, z)), (0.35, 0.5, 0.25), face, R)                                # ears
    hd.ell(P((1.2, -1.3, 0)), (0.6, 0.35, 1.0), Mat(ramp("#2a1410", "#4a2218", "#6a3424", "#8a4a34", "#aa6650")), R)  # mouth
    if hair == "wild":         # a bald crown, grey tufts bushing out over the ears and at the back
        hd.ell(P((-0.9, 0.3, 0)), (1.3, 1.7, 1.85), GREY_HAIR, R)
        for z in (-1, 1):
            for (x, y, zz, r) in ((-0.2, 0.6, 1.9, 0.75), (-1.0, 1.1, 2.0, 0.85), (-1.6, 0.1, 1.8, 0.8), (-0.6, -0.4, 2.0, 0.6)):
                hd.ell(P((x, y, zz * z)), (r, r * 0.9, r), GREY_HAIR, R)
            spike(hd, P((-0.6, 1.0, 2.0 * z)), P((-1.2, 1.9, 2.9 * z)), 0.45, GREY_HAIR)
    elif hair == "neat":
        hd.ell(P((-0.5, 0.8, 0)), (1.65, 1.5, 1.8), Mat(ramp("#120c08", "#22180e", "#3a2a18", "#5a4428", "#7a603a")), R)
    if mustache:               # a walrus mustache hanging over the mouth
        for z in (-1, 1):
            hd.ell(P((1.75, -0.8, 0.55 * z)), (0.45, 0.4, 0.65), GREY_HAIR, R)
            spike(hd, P((1.65, -0.85, 0.9 * z)), P((1.3, -1.6, 1.45 * z)), 0.38, GREY_HAIR)
    if goggles:                # brass-rimmed goggles; their lenses catch the glow of the arcs
        y = 0.35 if goggles == "eyes" else 1.6
        for z in (-0.75, 0.75):
            hd.cyl(P((1.35, y, z)), P((2.0, y, z)), 0.62, BRASS_P, seg=10)
            hd.ell(P((2.0, y, z)), (0.12, 0.48, 0.48), LENS, R)
        hd.cyl(P((0.0, y, -1.8)), P((0.0, y, 1.8)), 0.25, LEATHER, seg=6)                      # the strap
    if cap:                    # a cap with a short peak
        hd.ell(P((-0.2, 1.4, 0)), (1.95, 1.0, 1.95), cap, R)
        hd.box(P((1.4, 1.1, 0)), (1.6, 0.25, 2.6), cap, R @ rot_z(-0.15))


# ---------------------------------------------------------------- the Inventor
def brass_leg(G, key, hipj, knee, ankle, s, P, th=1.0):
    """A light brass leg in place of a lost one: slim struts, an open knee with a gear and a spring,
    a piston down the back, a clawed foot. Lighter than any golem's leg — it carries a man."""
    from humanoid import block, axle, gear, ram
    g, rm = G[key], G[key + ".ram"]
    hipj, knee, ankle = arr(hipj), arr(knee), arr(ankle)
    axle(g, hipj, 1.5, 2.4, s, mat=M_DIRON)
    Rt = block(g, hipj, knee, (1.5, 1.6), (1.3, 1.4), M_DIRON)                                 # the thigh strut
    block(g, lerp(hipj, knee, 0.12), lerp(hipj, knee, 0.82), (1.0, 2.2), (0.9, 1.9), P, off=(1.0, 0, 0))   # cover
    rivets(g, [lerp(hipj, knee, t) + Rt @ arr((1.55, 0, 0)) for t in (0.3, 0.62)], mat=M_STEEL, r=0.22)
    axle(g, knee, 1.3, 2.6, s, mat=M_DIRON)
    gear(g, knee + (0, 0, 1.3 * s), 1.25, s, teeth=8, mat=P)
    g.ell(knee + Rt @ arr((1.3, 0.0, 0)), (0.9, 1.1, 1.1), P)                                  # knee cap
    Rs = block(g, knee, ankle, (1.3, 1.3), (1.2, 1.2), M_DIRON)                                # the shin strut
    block(g, lerp(knee, ankle, 0.1), lerp(knee, ankle, 0.78), (1.4, 2.2), (1.1, 1.8), P, off=(0.8, 0, 0))   # shin plate
    bt, bs = -Rt[:, 0], -Rs[:, 0]
    A = lerp(hipj, knee, 0.25) + bt * 1.6
    B = lerp(knee, ankle, 0.3) + bs * 1.5
    g.cyl(A, A - bt * 0.9, 0.3, M_DIRON, seg=6)
    g.cyl(B, B - bs * 0.9, 0.3, M_DIRON, seg=6)
    ram(rm, A, B, 0.45)                                                                        # the knee piston
    for i in range(5):                                                                         # a spring down the shin
        t = 0.38 + i * 0.09
        g.cyl(lerp(knee, ankle, t) + bs * 1.2, lerp(knee, ankle, t + 0.04) + bs * 1.2, 0.55, M_STEEL, seg=6)
    axle(g, ankle, 0.9, 2.2, s, mat=M_DIRON)
    g.box(ankle + (-0.9, -1.5, 0), (2.4, 1.4, 2.6), M_DIRON)                                  # heel
    toe = ankle + (1.8, -1.8, 0)
    g.box(toe, (3.2, 1.0, 2.8), P)
    for z in (-0.9, 0.0, 0.9):
        g.box(toe + (1.85, -0.1, z), (0.7, 0.8, 0.6), M_STEEL)                                  # toe claws


def brass_arm(G, key, sh, elbow, wrist, s, P, ram_side="back", th=1.0, cuff=True):
    """The mechanical arm: a shoulder drum strapped on over the coat, slim struts, a piston across the elbow."""
    from humanoid import block, axle, ram
    g, rm = G[key], G[key + ".ram"]
    sh, elbow, wrist = arr(sh), arr(elbow), arr(wrist)
    G[key + ".ball"].ell(sh, (1.5, 1.5, 1.5), P)
    Ru = block(g, sh + unit(elbow - sh) * 1.2, elbow, (1.2, 1.2), (1.1, 1.1), M_DIRON)
    block(g, lerp(sh, elbow, 0.3), lerp(sh, elbow, 0.85), (1.6, 1.0), (1.4, 0.9), P, off=(0.3, 0, 0.5 * s))
    axle(g, elbow, 1.0, 2.0, s, mat=M_DIRON)
    Rf = block(g, elbow, wrist, (1.1, 1.1), (1.0, 1.0), M_DIRON)
    block(g, lerp(elbow, wrist, 0.15), lerp(elbow, wrist, 0.8), (1.5, 1.6), (1.3, 1.4), P, off=(0.2, 0, 0))
    b = -Ru[:, 0] if ram_side == "back" else Ru[:, 0]
    ram(rm, lerp(sh, elbow, 0.35) + b * 1.0, lerp(elbow, wrist, 0.35) + b * 0.9, 0.32)
    return wrist


def inventor_torso(G, P, S):
    ch, bk, pl = G["chest"], G["back"], G["pelvis"]
    hip = S["hip"]
    # the waist: a leather belt over the gearbox that carries the brass legs
    tbox(pl, (0, hip + 0.6, 0), (3.2, 5.2), (3.2, 5.0), 2.8, M_DIRON)
    pl.box((0.1, hip + 1.9, 0), (3.6, 1.0, 5.4), LEATHER)
    pl.box((2.0, hip + 1.9, 0), (0.3, 1.0, 1.2), BRASS_P)                                    # buckle
    for z in (-2.2, 2.4):
        pl.box((0.6, hip + 1.2, z), (1.6, 1.6, 1.0), LEATHER)                                # pouches
    # the coat: a waistcoat front, the frock coat over it, a high collar, brass buttons
    tbox(ch, (0, 21.8, 0), (3.2, 4.8), (4.0, 7.0), 7.8, P)
    tbox(ch, (1.55, 21.6, 0), (0.6, 2.6), (0.6, 3.0), 6.8, Mat(ramp("#1a1006", "#3a240e", "#5e3c18", "#866024", "#b08a3a")))
    rivets(ch, [(1.95, y, 0) for y in (19.4, 21.0, 22.6, 24.2)], mat=BRASS_P, r=0.28)
    for z in (-1, 1):
        ch.ell((0, 25.0, 3.0 * z), (1.9, 1.4, 1.2), P)                                       # shoulders
        tbox(ch, (1.6, 23.2, 1.4 * z), (0.4, 1.4), (0.4, 0.7), 4.2, P, rot_x(-0.2 * z))       # lapels
    tbox(ch, (-0.5, 26.2, 0), (3.2, 4.6), (2.6, 3.6), 1.8, P)                                 # high collar
    ch.box((1.2, 25.9, 0), (0.6, 1.2, 1.2), LINEN)                                            # cravat
    # tails of the frock coat behind the legs
    rb = G["robe"]
    for z in (-1, 1):
        tbox(rb, (-2.8, 14.6, 1.3 * z), (0.5, 2.4), (0.5, 2.0), 7.0, P, rot_z(0.18))
    # the backpack: a brass frame, straps, and a Tesla coil standing over the head
    tbox(bk, (-3.3, 22.0, 0), (2.4, 4.4), (2.2, 4.0), 6.4, BRASS_P)
    bk.box((-4.6, 22.0, 0), (0.4, 5.6, 3.0), M_DIRON)
    for z in (-1.6, 1.6):
        bk.box((-1.9, 24.4, z), (2.0, 0.6, 0.7), LEATHER, rot_z(-0.6))                        # straps
    bk.cyl((-3.4, 25.2, 0), (-3.4, 26.4, 0), 1.5, M_DIRON, seg=10)
    for i in range(9):                                                                         # the coil
        y = 26.6 + i * 0.85
        bk.cyl((-3.4, y, 0), (-3.4, y + 0.5, 0), 1.1, COPPER, seg=10)
    bk.cyl((-3.4, 26.4, 0), (-3.4, 34.4, 0), 0.5, M_DIRON, seg=6)
    bk.ell((-3.4, 34.8, 0), (2.4, 0.8, 2.4), BRASS_P)                                         # the toroid
    bk.ell((-3.4, 35.4, 0), (0.5, 0.5, 0.5), SPARK)
    for i, d in enumerate(((2.6, 1.6, 1.8), (-2.4, 2.0, -1.4), (0.4, 2.6, -2.6))):
        zigzag(bk, (-3.4, 35.4, 0), arr((-3.4, 35.4, 0)) + arr(d), n=3, amp=0.35, seed=i, r=0.18)
    human_head(G, (0.9, 29.4, 0), hair="wild", mustache=True, goggles="eyes")


def shock_pistol(G, side, sh, el, w, s, P, A, S):
    """A gloved hand with the shocker: a brass body, a glass bulb glowing on top, a copper coil barrel."""
    d = unit(w - el)
    up = arr((0, 1.0, 0)) - d * d[1]
    up = unit(up) if np.linalg.norm(up) > 1e-6 else arr((1.0, 0, 0))
    c = glove(G, "hand_" + side, w, d, up, s)
    g = G["item_" + side]
    R = np.column_stack([d, up, np.cross(d, up)])
    g.cyl(c - up * 1.2, c + up * 0.4, 0.42, WOOD, seg=6)                                   # the grip
    body = c + up * 0.9 + d * 0.8
    g.box(body, (2.6, 1.2, 0.9), BRASS_P, R)
    g.ell(body + up * 0.9, (0.55, 0.55, 0.55), SPARK)                                       # the bulb
    g.cyl(body + d * 1.2, body + d * 3.2, 0.42, COPPER, seg=6)
    for t in (1.6, 2.2, 2.8):
        g.cyl(body + d * t, body + d * (t + 0.25), 0.62, COPPER, seg=8)
    muzzle = body + d * 3.4
    for o in (up, -up):
        g.cyl(muzzle, muzzle + d * 0.8 + o * 0.35, 0.16, M_STEEL, seg=4)                     # two prongs
    m = muzzle + d * 0.8
    reach = 11.0 / max(0.3, np.hypot(d[0], d[2]))               # the arc jumps about 11 units ahead
    if d[1] < -0.2:
        reach = (m[1] - 0.3) / -d[1]                             # aimed down: it strikes the ground
    return dict(muzzle=m, d=d, up=up, target=m + d * reach)


def claw_hand(G, side, sh, el, w, s, P, A, S):
    """The mechanical arm ends in a three-fingered claw."""
    d = unit(w - el)
    g = G["item_" + side]
    G["hand_" + side].ell(arr(w) + d * 0.3, (0.9, 0.9, 0.9), M_DIRON)
    up = arr((0, 1.0, 0)) - d * d[1]
    up = unit(up) if np.linalg.norm(up) > 1e-6 else arr((1.0, 0, 0))
    sideways = unit(np.cross(d, up))
    base = arr(w) + d * 0.9
    g.box(base, (1.4, 1.4, 1.4), BRASS_P, np.column_stack([d, up, sideways]))
    for o in (up, -up * 0.5 + sideways * 0.85, -up * 0.5 - sideways * 0.85):
        k = base + d * 0.6 + o * 0.6
        tip = k + d * 1.6 + o * 0.3
        g.cyl(k, tip, 0.28, M_STEEL, seg=4)
        g.cyl(tip, tip + d * 0.8 - o * 0.6, 0.22, M_STEEL, r1=0.06, seg=4)
    return dict(w=w)


def inventor_fx(fx, A, info, S, ft):
    """Шокер: an arc from the prongs to the target."""
    gun = info["n"]
    near = ft < 0.5
    if near:
        fx.ell(gun["muzzle"], (1.1, 1.1, 1.1), ENERGY)
        zigzag(fx, gun["muzzle"], gun["target"], n=7, amp=1.0, seed=5, r=0.3)
        fx.ell(gun["target"], (1.8, 1.8, 1.8), ENERGY)
        if A.get("ground", True):
            fx.ell(arr((gun["target"][0], 0.2, gun["target"][2])), (3.0, 0.2, 2.6),
                   Mat(ramp("#0e1a22", "#18303c", "#245060", "#3a7a8e", "#6ab8c8"), dither=True))
    sparks(fx, gun["target"], n=5, spread=2.0, ft=ft, seed=6, big=False)


BRASS_RAMP = ramp("#1c1206", "#3e2a0e", "#6a4a1a", "#9a722c", "#cca04a")
INVENTOR = dict(
    name="Изобретатель", role="лидер · 3", k=1.6, paint=COAT, canvas=(64, 60, 26, 50),
    paints=dict(leg_n=Mat(BRASS_RAMP), leg_f=Mat(BRASS_RAMP), arm_n=Mat(COAT), arm_f=Mat(BRASS_RAMP)),
    hip=15.0, hz=2.3, hipx=(0.2, -0.4), LT=7.0, LS=6.6, LU=5.0, LF=5.0, th_leg=0.6, th_arm=0.45, cuff=False,
    leg_fn=brass_leg,
    sh=arr((0.0, 25.0, 4.3)), torso=inventor_torso, item_n=shock_pistol, item_f=claw_hand, fx=inventor_fx,
    arm_fn=dict(n=sleeve_arm(Mat(COAT)), f=brass_arm),
    hit=lambda info: info["n"]["target"] * arr((1, 0, 1)),
    strike=lambda info: info["n"]["target"],
    allow=[("hand_n", "item_n"), ("arm_f", "item_f"), ("hand_f", "item_f"), ("robe", "pelvis"), ("robe", "chest"),
           ("chest", "pelvis"), ("arm_n", "hand_n")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((1.6, 3.6, 2.8), (-2.2, 3.6, -2.8)),
                  hand_n=(3.4, -6.4, 1.0), pole_n=(-0.6, -0.3, 1.0), hand_f=(2.4, -7.6, -1.2), pole_f=(-0.6, -0.2, -1.0)),
        attack=dict(lean=-0.08, twist=-0.15, t=(0.4, -0.4, 0.0), ank=((3.0, 3.6, 2.8), (-2.6, 3.6, -2.8)),
                    hand_n=(8.6, -2.6, -0.4), pole_n=(-0.3, -1.0, 0.6), hand_f=(-1.6, -7.0, -1.8), pole_f=(-0.6, 0.0, -1.0),
                    fx=True, ground=False),
        attack_low=dict(lean=-0.18, twist=-0.15, t=(0.6, -0.8, 0.0), ank=((3.2, 3.6, 2.8), (-2.6, 3.6, -2.8)),
                        hand_n=(5.0, -8.4, -0.4), pole_n=(-0.3, -1.0, 0.6), hand_f=(-1.2, -7.0, -1.8), pole_f=(-0.6, 0.0, -1.0),
                        fx=True, ground=True),
        attack_high=dict(lean=0.06, twist=-0.15, t=(0.2, -0.2, 0.0), ank=((3.0, 3.6, 2.8), (-2.6, 3.6, -2.8)),
                         hand_n=(9.2, 3.4, -0.4), pole_n=(-0.3, -1.0, 0.6), hand_f=(-1.6, -7.0, -1.8), pole_f=(-0.6, 0.0, -1.0),
                         fx=True, ground=False),
    ),
    bands=dict(low="attack_low", level="attack", high="attack_high"),
)
INVENTOR["poses"]["broken"] = dict(GH.broken_pose(INVENTOR), lean=-0.3, hand_n=(3.4, -8.6, 2.2), hand_f=(2.2, -8.8, -2.2))



# ---------------------------------------------------------------- the Architect on his walking crane
CRANE = ramp("#1e1404", "#46300a", "#76561a", "#a8822a", "#d6b048")             # crane ochre
GREEN_COAT = Mat(ramp("#0a120c", "#16241a", "#22382a", "#34503c", "#4e7056"))
BEARD = Mat(ramp("#120a06", "#24140a", "#3a2412", "#55381e", "#704e2c"))
STONE = Mat(ramp("#22202a", "#3e3a46", "#5e5a68", "#86828e", "#b2aeb8"))
BRICK = Mat(ramp("#260c08", "#4a1a10", "#76301c", "#a04a2c", "#c86c44"))
BLUEPRINT = Mat(ramp("#0c1a3a", "#16306a", "#2a52a0", "#4a7ad0", "#8ab4f0"))
CAP = Mat(ramp("#0c0c10", "#1a1a22", "#2a2a36", "#3e3e4e", "#585868"))
DUST = Mat(ramp("#3a3230", "#5a504a", "#7e726a", "#a49890", "#c8beb4"), dither=True)
ZOD_SCALE = 0.84                     # the man in the cabin, to the scale of the crane (the Inventor's sim scale over the crane's)


def lattice(g, a, b, w, mat, n=None, up=(0, 1, 0), r=0.32, tri=True):
    """A lattice girder from a to b: chords and zigzag braces. w: width; tri: a triangular section."""
    a, b = arr(a), arr(b)
    d = unit(b - a)
    u = arr(up) - d * (d @ arr(up))
    u = unit(u) if np.linalg.norm(u) > 1e-6 else arr((1.0, 0, 0))
    z = unit(np.cross(d, u))
    L = np.linalg.norm(b - a)
    n = n or max(2, int(L / (w * 1.1)))
    cs = [u * w * 0.5, -u * w * 0.4 + z * w * 0.5, -u * w * 0.4 - z * w * 0.5] if tri else \
         [u * w * 0.5 + z * w * 0.5, u * w * 0.5 - z * w * 0.5, -u * w * 0.5 - z * w * 0.5, -u * w * 0.5 + z * w * 0.5]
    for c in cs:
        g.cyl(a + c, b + c, r, mat, seg=5)
    for i in range(n):
        p0, p1 = a + d * L * i / n, a + d * L * (i + 1) / n
        for j in range(len(cs)):
            c0, c1 = cs[j], cs[(j + 1) % len(cs)]
            if i % 2:
                c0, c1 = c1, c0
            g.cyl(p0 + c0, p1 + c1, r * 0.7, M_DIRON, seg=4)


def small_human(G, key, feet, sc, R=I3):
    """The Architect: a man in a green frock coat and a peaked cap, a dark beard, the blueprints under one
    arm and the other pointing ahead. Drawn at the Inventor's size, then scaled by sc about his feet."""
    def build(T):
        g = T[key]
        tbox(g, (0, 21.6, 0), (3.0, 4.6), (3.8, 6.8), 7.6, GREEN_COAT)                        # the coat
        tbox(g, (0, 16.6, 0), (3.4, 5.0), (3.0, 4.6), 3.0, GREEN_COAT)
        g.box((0.0, 17.9, 0), (3.5, 0.8, 5.0), LEATHER)                                       # belt
        rivets(g, [(1.75, y, 0) for y in (19.6, 21.4, 23.2)], mat=BRASS_P, r=0.26)
        for z in (-1, 1):
            g.ell((0, 25.0, 3.0 * z), (1.7, 1.3, 1.3), GREEN_COAT)                             # shoulders
            g.cyl((0.2, 15.0, 1.3 * z), (0.4, 8.0, 1.4 * z), 1.1, Mat(ramp("#141010", "#242020", "#363030", "#4a4242", "#605858")), seg=8)
        tbox(g, (-0.4, 26.0, 0), (2.8, 4.0), (2.4, 3.2), 1.4, GREEN_COAT)                      # collar
        g.box((1.1, 25.8, 0), (0.6, 1.0, 1.1), LINEN)
        # the near arm points ahead, the far arm holds the rolled-up drawings against the chest
        sh = arr((0.2, 25.0, 3.6))
        el = sh + (2.6, -3.0, 0.6)
        wr = el + (4.2, 1.0, -0.4)
        g.cyl(sh, el, 0.95, GREEN_COAT, seg=8)
        g.cyl(el, wr, 0.85, GREEN_COAT, seg=8)
        g.ell(wr + (0.6, 0.1, 0), (0.75, 0.6, 0.6), SKIN)
        g.cyl(wr + (0.9, 0.2, 0), wr + (2.2, 0.4, 0), 0.25, SKIN, seg=4)                      # the pointing finger
        sf = arr((0.2, 25.0, -3.6))
        ef = sf + (1.2, -4.4, 0.4)
        wf = ef + (2.4, 2.2, 1.6)
        g.cyl(sf, ef, 0.95, GREEN_COAT, seg=8)
        g.cyl(ef, wf, 0.85, GREEN_COAT, seg=8)
        g.ell(wf + (0.3, 0.2, 0.3), (0.65, 0.6, 0.6), SKIN)
        g.cyl(wf + (0.2, -1.6, 1.2), wf + (0.6, 3.6, -1.6), 0.7, BLUEPRINT, seg=8)              # the roll of drawings
        hd = Parts()
        human_head(hd, (0.9, 29.4, 0), hair="neat", mustache=False, goggles=None, cap=CAP)
        for k_, m in hd.items():
            g.extend(m)
        for z in (-1, 1):                                                                     # beard and spectacles
            g.ell((2.0, 28.6, 0.7 * z), (0.45, 0.45, 0.45), Mat(ramp("#1a1a1a", "#3a3a3a", "#8a8a8a", "#cfcfcf", "#ffffff")))
        g.ell((1.6, 27.8, 0), (0.9, 1.2, 1.5), BEARD)
        g.ell((2.1, 27.3, 0), (0.6, 0.8, 0.9), BEARD)
    T = Parts()
    build(T)
    feet = arr(feet)
    for k_, m in T.items():
        G[k_].extend(m.transformed(R, (0, 0, 0)).scaled(sc).transformed(I3, feet))


def zod_torso(G, P, S):
    pl, ch, bk = G["pelvis"], G["chest"], G["back"]
    hip = S["hip"]
    # the hips: a gearbox carrying the legs and a slewing ring on top
    tbox(pl, (0, hip + 0.4, 0), (5.6, 6.4), (6.0, 7.0), 3.6, M_DIRON)
    pl.cyl((0, hip + 2.2, 0), (0, hip + 3.0, 0), 4.6, M_IRON, seg=16)
    # the deck: a plank floor on an iron frame, a waist-high plate in front, railings at the sides
    y = hip + 3.0
    tbox(ch, (0.6, y + 0.7, 0), (15.0, 11.4), (15.0, 11.4), 1.4, M_IRON)
    for z in np.arange(-4.6, 5.0, 1.55):
        ch.box((0.6, y + 1.5, z), (14.4, 0.3, 1.35), WOOD)
    tbox(ch, (7.6, y + 4.4, 0), (1.0, 11.6), (0.8, 11.0), 6.8, P, rot_z(-0.08))                 # the front plate
    rivets(ch, [(8.2, y + 1.8 + 1.9 * i, z) for i in range(3) for z in (-4.6, 4.6)], r=0.3)
    stripes = Mat(ramp("#0c0c0c", "#1a1a1a", "#2a2a2a", "#3a3a3a", "#4a4a4a"))
    for z in (-3.0, 0.0, 3.0):
        ch.box((8.2, y + 7.0, z), (0.25, 0.9, 1.4), stripes, rot_x(0.6))                       # hazard marks
    for z in (-1, 1):
        for x in (7.0, 0.6, -5.4):
            ch.cyl((x, y + 1.4, 5.4 * z), (x, y + 7.8, 5.4 * z), 0.35, M_DIRON, seg=5)        # posts
        ch.cyl((7.0, y + 7.8, 5.4 * z), (-5.4, y + 7.8, 5.4 * z), 0.35, P, seg=5)             # hand rail
        ch.cyl((7.0, y + 4.6, 5.4 * z), (-5.4, y + 4.6, 5.4 * z), 0.25, M_DIRON, seg=4)
    # the winch house behind the man: a rope drum, a small boiler and its stack
    ch.box((-2.6, y + 3.4, -2.6), (3.2, 3.6, 4.4), M_DIRON)
    ch.cyl((-2.6, y + 5.8, -4.2), (-2.6, y + 5.8, -0.8), 1.4, WOOD, seg=12)                   # rope drum
    for z in np.arange(-3.9, -1.0, 0.55):
        ch.cyl((-2.6, y + 5.8, z), (-2.6, y + 5.8, z + 0.3), 1.6, M_HOSE, seg=12)
    ch.cyl((-3.2, y + 1.4, 2.6), (-3.2, y + 7.6, 2.6), 1.8, M_IRON, seg=12)                   # boiler
    ch.cyl((-3.2, y + 7.6, 2.6), (-3.2, y + 8.2, 2.6), 1.95, BRASS_P, seg=12)
    ch.ell((-1.5, y + 3.2, 2.6), (0.3, 0.7, 0.7), emissive("fire", 4, 0.4))                   # firebox glow
    # the mast: a square lattice tower up from the back of the deck; the jib turns on its head
    top = arr(S["sh"]) * arr((1, 1, 0))
    base = arr((top[0], y + 1.4, 0))
    lattice(bk, base, top - (0, 1.4, 0), 3.0, P, up=(1, 0, 0), r=0.4, tri=False)
    bk.box(top - (0, 1.4, 0), (3.6, 0.8, 3.6), M_DIRON)
    # the A-frame over the head of the mast with the luffing pulley; the counter-jib and its stone weight
    ap = top + (-1.2, 6.0, 0)
    for z in (-1.4, 1.4):
        bk.cyl(top + (0.8, 0.6, z), ap, 0.35, P, seg=5)
        bk.cyl(top + (-2.4, 0.6, z), ap, 0.35, P, seg=5)
    bk.cyl(ap - (0, 0, 0.8), ap + (0, 0, 0.8), 0.7, M_DIRON, seg=10)
    cj = top + (-9.0, -0.6, 0)
    lattice(bk, top + (-1.4, 0.2, 0), cj, 2.2, P, up=(0, 1, 0), r=0.32)
    bk.cyl(ap, cj + (0, 0.8, 0), 0.14, M_DIRON, seg=4)                                         # the stay
    for i in range(2):
        tbox(bk, cj + (0.4, -2.0 - i * 2.5, 0), (3.6, 3.6), (3.6, 3.6), 2.4, STONE)           # counterweights
    bk.box(cj + (0.4, -3.25, 1.85), (3.0, 0.4, 0.2), M_DIRON)
    # the Architect at the front of the deck
    small_human(G, "head", (3.0, y + 1.6, 0.4), ZOD_SCALE)
    S["_ap"] = ap


def jib(G, key, sh, elbow, wrist, s, P, ram_side="back", th=1.0, cuff=True):
    """The near "arm" is the crane: the jib from the head of the mast to its tip, the hoist rope from the tip
    to the hook."""
    if s < 0:
        return wrist
    g = G[key]
    sh, elbow, wrist = arr(sh), arr(elbow), arr(wrist)
    G[key + ".ball"].cyl(sh - (0, 0, 1.6), sh + (0, 0, 1.6), 1.2, M_DIRON, seg=10)            # the jib's hinge
    lattice(g, sh + unit(elbow - sh) * 1.0, elbow, 2.4, P, n=6, r=0.36)
    g.cyl(elbow - (0, 0, 0.6), elbow + (0, 0, 0.6), 0.9, M_DIRON, seg=10)                       # the sheave
    g.cyl(elbow - (0, 0, 0.7), elbow + (0, 0, 0.7), 0.35, M_STEEL, seg=6)
    g.cyl(elbow, wrist, 0.13, M_DIRON, seg=4)                                                  # the hoist rope
    return wrist


def hook_sling(G, side, sh, el, w, s, P, A, S):
    if s < 0:
        return dict()
    g = G["item_" + side]
    d = unit(w - el)
    g.box(w + d * 0.6, (1.1, 1.6, 1.1), M_DIRON, np.column_stack([unit(np.cross(d, (0, 0, 1))), d, (0, 0, 1)]))
    hk = w + d * 1.9
    g.cyl(w + d * 1.2, hk, 0.25, M_STEEL, seg=5)
    g.cyl(hk, hk + d * 0.4 + unit(np.cross((0, 0, 1), d)) * 0.7, 0.22, M_STEEL, seg=4)          # the hook's curl
    if not A.get("thrown"):        # a sling of bricks hanging from the hook
        c = hk + d * 2.2
        for z in (-0.9, 0.9):
            g.cyl(hk, c + (0, 0.6, z * 1.6), 0.1, LEATHER, seg=3)
        for i, (x, yy, z) in enumerate(((-0.7, 0, -0.9), (0.7, 0, -0.9), (-0.7, 0, 0.9), (0.7, 0, 0.9), (0.0, 1.0, 0.0))):
            g.box(c + (x, yy, z), (1.3, 0.9, 1.7), BRICK)
    fwd = arr((d[0], 0.0, d[2]))
    fwd = unit(fwd) if np.linalg.norm(fwd) > 0.2 else arr((1.0, 0, 0))
    tgt = hk + fwd * 52.0                                     # lobbed about two cells ahead, landing at the height aimed at
    tgt[1] = A.get("aim_y", 26.0)
    return dict(w=w, el=el, hook=hk, d=d, target=tgt)


def zod_after(G, info, A):
    ap = info["X"](ZODCHIY["_ap"])
    G["arm_n"].cyl(ap, info["n"]["el"], 0.13, M_DIRON, seg=4)                 # the luffing rope


def zod_fx(fx, A, info, S, ft):
    """A brick bursting on the target: chips, a dusty puff; a second brick still in the air."""
    c = info["n"]["target"]
    d = info["n"]["d"]
    if ft < 0.5:                   # one more brick just leaving the sling
        fx.box(info["n"]["hook"] + d * 3.4, (1.3, 0.9, 1.7), BRICK, rot_z(0.7) @ rot_x(0.4))
        for i, o in enumerate(((0, 0, 0), (-1.2, 0.8, 0.9), (0.6, -0.9, -1.0))):
            fx.box(c + arr(o), (1.3, 0.9, 1.7), BRICK, rot_z(0.5 * i) @ rot_x(0.3 * i))
        fx.ell(c, (2.6, 2.0, 2.2), DUST)
    else:
        fx.ell(c + (0.6, 0.6, 0), (3.6, 2.8, 3.0), DUST)
    sparks(fx, c, n=6, spread=3.0, ft=ft, seed=11, big=False)
    if A.get("ground", True):
        fx.ell(arr((c[0], 0.3, c[2])), (4.0, 0.3, 3.4), DUST)


ZODCHIY = dict(
    name="Зодчий", role="лидер · 4", k=1.05, paint=CRANE, canvas=(96, 72, 34, 62),
    hip=13.0, hz=4.2, hipx=(0.0, 0.0), LT=7.6, LS=7.4, LU=15.0, LF=7.0, th_leg=0.7, th_arm=1.0, cuff=False,
    sh=arr((-4.4, 47.0, 0.0)), torso=zod_torso, item_n=hook_sling, item_f=hook_sling, fx=zod_fx, after=zod_after,
    arm_fn=dict(n=jib, f=jib),
    hit=lambda info: info["n"]["target"] * arr((1, 0, 1)),
    strike=lambda info: info["n"]["target"],
    allow=[("arm_n", "back"), ("arm_n.ball", "back"), ("arm_n", "item_n"), ("chest", "head"), ("chest", "back"),
           ("pelvis", "chest")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.2, 3.6, 5.0), (-2.4, 3.6, -5.0)),
                  hand_n=(17.0, -6.0, 0.0), pole_n=(0.0, 1.0, 0.0), hand_f=(0.0, -5.0, 0.0), pole_f=(1.0, 0.0, 0.0)),
        # the jib swung down and forward, the rope flung out over its tip: the sling has let go
        attack=dict(lean=-0.06, t=(0.4, -0.4, 0.0), ank=((3.4, 3.6, 5.0), (-2.6, 3.6, -5.0)),
                    hand_n=(20.4, 3.2, 0.0), pole_n=(0.0, -1.0, 0.0), hand_f=(0.0, -5.0, 0.0), pole_f=(1.0, 0.0, 0.0),
                    thrown=True, aim_y=28.0, fx=True, ground=False),
        attack_low=dict(lean=-0.1, t=(0.6, -0.6, 0.0), ank=((3.4, 3.6, 5.0), (-2.6, 3.6, -5.0)),
                        hand_n=(21.4, 0.2, 0.0), pole_n=(0.0, -1.0, 0.0), hand_f=(0.0, -5.0, 0.0), pole_f=(1.0, 0.0, 0.0),
                        thrown=True, aim_y=0.4, fx=True, ground=True),
        attack_high=dict(lean=-0.02, t=(0.2, -0.2, 0.0), ank=((3.4, 3.6, 5.0), (-2.6, 3.6, -5.0)),
                         hand_n=(17.6, 9.0, 0.0), pole_n=(0.0, -1.0, 0.0), hand_f=(0.0, -5.0, 0.0), pole_f=(1.0, 0.0, 0.0),
                         thrown=True, aim_y=52.0, fx=True, ground=False),
    ),
    bands=dict(low="attack_low", level="attack", high="attack_high"),
)
ZODCHIY["poses"]["broken"] = dict(GH.broken_pose(ZODCHIY), hand_n=(12.0, -15.0, 0.0), pole_n=(0.4, 1.0, 0.0),
                                  hand_f=(0.0, -5.0, 0.0), pole_f=(1.0, 0.0, 0.0))

if __name__ == "__main__":
    from PIL import Image
    from paths import out
    ims = []
    for S, poses in ((INVENTOR, ("idle", "attack_low", "attack", "attack_high", "broken")), (ZODCHIY, ("idle", "attack_low", "attack", "attack_high", "broken"))):
        for p in poses:
            print(S["name"], p, GH.check(S, p))
            im = GH.build(S, p, 5.0).image(2)
            bb = im.getbbox()
            im = im.crop((bb[0] - 8, bb[1] - 8, bb[2] + 8, bb[3] + 8))
            c = Image.new("RGBA", im.size, (52, 50, 56, 255))
            c.alpha_composite(im)
            ims.append(c)
    W = sum(i.width for i in ims) + 20 * len(ims)
    H = max(i.height for i in ims)
    sheet = Image.new("RGBA", (W, H), (52, 50, 56, 255))
    x = 0
    for i in ims:
        sheet.paste(i, (x, H - i.height))
        x += i.width + 20
    sheet.save(out("leaders_h.png"))
