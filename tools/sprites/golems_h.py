"""The Foundry's golems as humanoid machines (the style worked out on the Guard in humanoid.py).

One body kit — a gearbox pelvis, an open spine with the furnace glowing through, a broad furnace
chest, axles with gear rings, hydraulic rams, heat conduits — and for each golem its own build,
head, back unit, hands, paint, idle pose and attack (the instant of contact, as the attack sprite
is shown when a blow lands). Every pose is checked for clipping.

    python3 tools/sprites/golems_h.py          -> out/foundry_humanoid.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import (M_IRON, M_DIRON, M_STEEL, M_RUST, M_HOSE, M_GLASS, M_PLATE, M_HOLE,
                    emissive, spike, tbox, pivot, STYLE1)
from golem7 import M_PUFF
import humanoid as H
from humanoid import (arr, unit, lerp, basis, block, axle, gear, ram, conduit, rivets, Parts, leg, arm, fist,
                      grip_on, ik, place_upper, smear, SMEAR, LAMP_G)
from frames import PAINT as FRAME_PAINT

UPPER = ("pelvis", "spine", "chest", "back", "head", "pauldron_n", "pauldron_f")
BASE_ALLOWED = [("leg_n", "pelvis"), ("leg_f", "pelvis"), ("leg_n", "leg_n.ram"), ("leg_f", "leg_f.ram"),
                ("spine", "pelvis"), ("spine", "chest"), ("chest", "back"), ("chest", "head"), ("back", "head"),
                ("chest", "pauldron_n"), ("chest", "pauldron_f"), ("pauldron_n", "pauldron_f"),
                ("chest", "arm_n.ball"), ("chest", "arm_f.ball"), ("pauldron_n", "arm_n.ball"), ("pauldron_f", "arm_f.ball"),
                ("arm_n", "arm_n.ball"), ("arm_f", "arm_f.ball"), ("arm_n.ram", "arm_n.ball"), ("arm_f.ram", "arm_f.ball"),
                ("pauldron_n", "arm_n"), ("pauldron_f", "arm_f"), ("arm_n", "arm_n.ram"), ("arm_f", "arm_f.ram"),
                ("arm_n", "hand_n"), ("arm_f", "hand_f"), ("hand_n", "item_n"), ("hand_f", "item_f"),
                ("head", "arm_n.ball"), ("head", "arm_f.ball"), ("back", "pauldron_n"), ("back", "pauldron_f")]


# ---------------------------------------------------------------- the shared body kit
class Core:
    """Pelvis, open spine and a two-layer furnace chest, all from a few numbers."""

    def __init__(self, hip, pel, chest, shell_off=(0.6, 0.4), shrink=(0.94, 0.93), ring_r=3.0):
        self.hip = hip
        self.pel = pel                       # (bottom (x, z), top (x, z))
        self.cx, self.cy, self.bot, self.top, self.h = chest
        self.sx, self.sy = self.cx + shell_off[0], self.cy + shell_off[1]
        self.sbot = (self.bot[0] * shrink[0], self.bot[1] * shrink[1])
        self.stop = (self.top[0] * shrink[0], self.top[1] * shrink[1])
        self.sh_ = self.h * shrink[0]
        self.ring_r = ring_r

    def front(self, y):
        """x of the painted shell's front face at height y."""
        t = np.clip((y - (self.sy - self.sh_ / 2)) / self.sh_, 0, 1)
        return self.sx + (self.sbot[0] + (self.stop[0] - self.sbot[0]) * t) / 2

    def side(self, y):
        """z of the dark frame's flank at height y."""
        t = np.clip((y - (self.cy - self.h / 2)) / self.h, 0, 1)
        return (self.bot[1] + (self.top[1] - self.bot[1]) * t) / 2

    def bottom(self):
        return self.cy - self.h / 2

    def build(self, G, P, grate=True, fins=4, gauge=True):
        hip = self.hip
        pl = G["pelvis"]
        tbox(pl, (-0.2, hip + 1.4, 0), self.pel[0], self.pel[1], 3.2, M_DIRON)
        f = -0.2 + self.pel[1][0] / 2
        tbox(pl, (f + 0.45, hip - 0.5, 0), (1.0, 2.8), (1.2, 3.2), 3.8, P, rot_z(-0.2))
        pl.box((f, hip + 1.4, 0), (0.7, 1.2, 3.4), M_DIRON)
        sp = G["spine"]
        y0, y1 = hip + 3.0, self.bottom() + 0.4
        n = 3
        step = (y1 - y0) / n
        for i in range(n):
            y = y0 + i * step
            sp.cyl((-0.8, y, 0), (-0.8, y + step * 0.72, 0), self.ring_r + 0.15 * i, M_DIRON, seg=12)
            sp.cyl((-0.8, y + step * 0.72, 0), (-0.8, y + step, 0), self.ring_r * 0.82, emissive("fire", 6, 0.35), seg=12)
        zz = self.ring_r + 0.7
        for s in (1, -1):
            ram(sp, (0.8, y0 + 0.3, zz * s), (1.1, y1 + 0.4, zz * s), 0.55)
        fr = -0.2 + self.pel[1][0] / 2 + 0.3
        for z in (-0.9, 0.9):
            sp.cyl((fr, y0 - 0.4, z), (fr + 0.6, y1 + 0.2, z), 0.5, M_HOSE, seg=5)
        ch = G["chest"]
        tbox(ch, (self.cx, self.cy, 0), self.bot, self.top, self.h, M_DIRON)
        tbox(ch, (self.sx, self.sy, 0), self.sbot, self.stop, self.sh_, P)
        ylo, yhi = self.sy - self.sh_ / 2, self.sy + self.sh_ / 2
        for y0_, y1_, w0, w1 in ((yhi - 3.1, yhi - 0.2, self.stop[1] * 0.7, self.stop[1] * 0.9),
                                 (ylo + 0.3, ylo + 1.5, self.sbot[1] * 0.6, self.sbot[1] * 0.7)):
            f0, f1 = self.front(y0_), self.front(y1_)
            tbox(ch, ((f0 + f1) / 2 + 0.3, (y0_ + y1_) / 2, 0), (0.7, w0), (0.7, w1), y1_ - y0_, P,
                 rot_z(-np.arctan2(f1 - f0, y1_ - y0_)))                                    # breastplate bands
        if grate:
            fy = self.sy - 0.8
            fx = self.front(fy)
            ch.box((fx + 0.35, fy, 0), (1.4, 5.2, 6.8), M_DIRON)
            ch.ell((fx + 0.6, fy, 0), (0.7, 2.3, 2.9), emissive("fire", 14, 0.7))
            for z in (-2.4, -1.2, 0.0, 1.2, 2.4):
                ch.box((fx + 1.2, fy, z), (0.45, 5.0, 0.45), M_DIRON)
            ch.box((fx + 1.2, fy + 2.7, 0), (0.7, 0.6, 7.0), M_IRON)
        yr = yhi - 1.4
        rivets(ch, [(self.front(yr) + 0.65, yr, z) for z in np.linspace(-self.stop[1] * 0.3, self.stop[1] * 0.3, 5)], r=0.35)
        if gauge:
            g = arr((self.front(self.sy + 1.8) + 0.65, self.sy + 1.8, self.stop[1] * 0.24))
            ch.cyl(g - (0.3, 0, 0), g + (0.45, 0, 0), 1.2, M_STEEL, seg=10)
            ch.ell(g + (0.5, 0, 0), (0.15, 0.9, 0.9), M_GLASS)
            ch.box((self.front(self.sy + 1.6) + 0.7, self.sy + 1.6, -self.stop[1] * 0.24), (0.3, 1.3, 2.6), M_PLATE)
            for z, lamp in ((-2.4, LAMP_G), (-1.4, emissive("fire", 3, 0.4))):
                ch.ell((self.front(ylo + 0.6) + 0.35, ylo + 0.9, z), (0.35, 0.35, 0.35), lamp)
        for i in range(fins):
            y = self.cy - self.h / 2 + 0.6 + i * 1.2
            for s in (1, -1):
                ch.box((-0.6, y, s * (self.side(y) + 0.45)), (5.0, 0.4, 1.0), M_IRON)


def pauldron(G, key, c, s, P, r=(4.8, 3.0, 4.0), layers=2, spikes=0):
    pd = G[key]
    c = arr(c)
    pd.ell(c, r, P)
    for i in range(layers):
        tbox(pd, c + (0, -r[1] * (0.73 + 0.4 * i), (0.9 + 0.6 * i) * s), (r[0] * 1.45 - i * 1.0, 3.2), (r[0] * 1.65 - i * 1.0, 3.6),
             1.5, P, rot_x((-0.35 - 0.15 * i) * s))
    pd.ell(c + (0, r[1] * 0.33, 0), (r[0] * 0.8, r[1] * 0.5, r[2] * 0.82), M_DIRON)
    rivets(pd, [c + (x, r[1] * 0.6, r[2] * 0.72 * s) for x in (-r[0] * 0.5, 0.0, r[0] * 0.5)], r=0.35)
    for i in range(spikes):
        x = (i - (spikes - 1) / 2) * 2.6
        spike(pd, c + (x, r[1] * 0.7, r[2] * 0.4 * s), c + (x - 0.8, r[1] + 3.4, (r[2] * 0.4 + 1.2) * s), 1.0, M_IRON)


def scaled(G, key, sz, about, build):
    """Build into a scratch model and scale it about a point into G[key]."""
    if abs(sz - 1.0) < 1e-6:
        return build(G)
    tmp = Parts()
    out = build(tmp)
    about = arr(about)
    for k, m in tmp.items():
        G[k].extend(m.transformed(I3, -about).scaled(sz).transformed(I3, about))
    return out


# ---------------------------------------------------------------- posing
def creature_parts(S, A, P=None, fx=True):
    """Build golem S in pose A (numbers). Returns the parts and where things are."""
    P = Mat(S["paint"]) if P is None else P
    G = Parts()
    S["torso"](G, P, S)
    R = rot_z(A["lean"]) @ rot_y(A.get("twist", 0.0))
    X = place_upper(G, R, A["t"], hip=S["hip"], keys=UPPER)
    info = dict(X=X, R=R)
    for key, hx, ank, s in (("leg_n", S["hipx"][0], A["ank"][0], 1), ("leg_f", S["hipx"][1], A["ank"][1], -1)):
        h = X((hx, S["hip"], S["hz"] * s))
        kn, an = ik(h, ank, S["LT"], S["LS"], (1.0, 0.25, 0.0))
        leg(G, key, h, kn, an, s, P, th=S["th_leg"])
    for side, s in (("n", 1), ("f", -1)):
        sh = X(S["sh"] * arr((1, 1, s)))
        el, w = ik(sh, sh + arr(A["hand_" + side]), S["LU"], S["LF"], A["pole_" + side])
        arm(G, "arm_" + side, sh, el, w, s, P, ram_side=A.get("ram_" + side, "back"), th=S["th_arm"], cuff=S.get("cuff", True))
        info[side] = S["item_" + side](G, side, sh, el, w, s, P, A, S)
        info["sh_" + side] = sh
    if S.get("after"):
        S["after"](G, info, A)
    if fx and A.get("fx") == "broken":
        broken_fx(G["fx"], info)
    elif fx and A.get("fx"):
        S["fx"](G["fx"], A, info, S, A.get("ft", 0.0))
    return G, info


def broken_pose(S):
    """Slumped onto the knees, the body fallen forward, the arms hanging to the ground; smoke, no fire."""
    I = S["poses"]["idle"]
    hz = S["hz"]
    A = dict(I)
    A.update(lean=-0.5, twist=0.12, t=(1.4, -S["hip"] * 0.4, 0.0),
             ank=((-S["LT"] * 0.55, 2.4, hz + 1.0), (-S["LT"] * 0.75, 2.4, -hz - 1.2)),
             hand_n=(5.0, -S["LU"] - S["LF"] + 1.0, 2.6), pole_n=(-0.6, 0.0, 1.0),
             hand_f=(3.6, -S["LU"] - S["LF"] + 1.4, -2.6), pole_f=(-0.6, 0.0, -1.0),
             ram_n="back", ram_f="back", fx="broken", open=40.0, hook=10.0)
    return A


def broken_fx(fx, info):
    X = info["X"]
    for i, d in enumerate(((2.0, 30.0, 0.0), (0.5, 34.0, 1.4), (-1.5, 38.5, -0.6))):
        fx.ell(X(d), (2.0 + i * 0.9, 1.6 + i * 0.7, 1.8 + i * 0.8), M_PUFF)


def check(S, pose, min_vol=0.05):
    from clipcheck import report
    G, _ = creature_parts(S, S["poses"][pose])
    return report(G, BASE_ALLOWED + S.get("allow", []), skip=("fx",), min_vol=min_vol)


def build(S, pose="idle", k=None, yaw=None):
    k = S["k"] if k is None else k
    w, h = int(90 * k), int(84 * k)
    ox, oy = int(38 * k), int(74 * k)
    G, _ = creature_parts(S, S["poses"][pose])
    opts = dict(STYLE1)
    if yaw is not None:
        opts["yaw"] = yaw
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **opts), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def grip_dir(d, u, least=72.0, most=116.0):
    """Turn a held tool's direction u so it sits in the fist at a real grip angle to the forearm d."""
    d, u = unit(d), unit(u)
    ang = np.degrees(np.arccos(np.clip(d @ u, -1, 1)))
    if least <= ang <= most:
        return u
    n = u - d * (d @ u)
    if np.linalg.norm(n) < 1e-6:
        n = arr((0, 1.0, 0)) - d * d[1]
    n = unit(n)
    a = np.radians(least if ang < least else most)
    return d * np.cos(a) + n * np.sin(a)


def puffs(fx, p, n=3, r=2.0, spread=3.5, ft=0.0, seed=0):
    rnd = np.random.RandomState(seed)
    for i in range(n):
        d = arr((rnd.uniform(-1, 1), rnd.uniform(0.3, 1.0), rnd.uniform(-1, 1))) * spread * (1 + 0.8 * ft)
        fx.ell(arr(p) + d, (r * (1 + 0.4 * ft),) * 3 * arr((1.0, 0.65, 0.9)), M_PUFF)


def sparks(fx, p, n=5, spread=2.4, ft=0.0, seed=1, big=True):
    rnd = np.random.RandomState(seed)
    if big and ft < 0.5:
        fx.ell(arr(p), (1.5, 1.5, 1.5), emissive("fire", 20, 0.9))
    for i in range(n):
        d = arr((rnd.uniform(-1, 1), rnd.uniform(0.0, 1.2), rnd.uniform(-1, 1))) * spread * (1 + 1.3 * ft)
        fx.ell(arr(p) + d, ((0.6 - 0.05 * i) / (1 + 0.5 * ft),) * 3, emissive("fire", 5 if i == 0 else 0, 0.8))


# ---------------------------------------------------------------- Молот: a brawler with hammer fists
MOLOT_CORE = Core(17.5, ((6.8, 9.6), (7.4, 10.6)), (0.8, 27.4, (8.6, 9.4), (12.4, 21.0), 8.8), ring_r=3.2)


def molot_torso(G, P, S):
    C = MOLOT_CORE
    C.build(G, P, grate=True, fins=3)
    # a low, armoured hump on the back with two short stacks raked backwards
    bk = G["back"]
    tbox(bk, (-4.6, 29.6, 0), (4.0, 13.0), (3.0, 11.0), 4.0, P, rot_z(0.35))
    tbox(bk, (-4.2, 29.8, 0), (4.4, 6.0), (3.4, 5.0), 4.6, M_DIRON, rot_z(0.35))
    for z in (3.2, -3.2):
        b0 = arr((-5.2, 30.6, z))
        top = b0 + (-3.0, 5.0, 0.6 * np.sign(z))
        bk.cyl(b0, top, 1.3, M_DIRON, seg=8)
        bk.cyl(top, top + unit(top - b0) * 0.8, 1.8, M_IRON, seg=8)
        bk.cyl(lerp(b0, top, 0.45), lerp(b0, top, 0.55), 1.55, M_RUST, seg=8)
        for i, d in enumerate(((-1.0, 2.2, 0), (-2.4, 4.4, 0.4))):
            bk.ell(top + arr(d), (1.7 + i * 0.8, 1.3 + i * 0.6, 1.5 + i * 0.6), M_PUFF)
    # a small head sunk low and forward between the shoulders: a slit visor, a heavy jaw
    hd = G["head"]
    hc = arr((5.0, 34.4, 0))
    tbox(hd, hc + (-0.6, -2.6, 0), (4.6, 5.0), (4.2, 4.6), 1.4, M_DIRON)                   # collar
    tbox(hd, hc, (4.8, 4.4), (4.2, 3.8), 4.6, P)
    tbox(hd, hc + (1.2, -1.4, 0), (2.6, 3.8), (2.2, 3.4), 2.2, M_IRON)
    hd.box(hc + (2.15, 0.5, 0), (0.5, 0.6, 3.4), emissive("fire", 8, 0.6))
    hd.box(hc + (1.8, 1.3, 0), (1.4, 0.9, 4.4), M_DIRON)
    for i in range(2):
        hd.box(hc + (2.4, -1.9 + i * 0.8, 0), (0.3, 0.25, 2.0), M_HOLE)
    hd.box(hc + (-0.3, 2.4, 0), (3.6, 0.8, 0.8), M_DIRON)
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pauldron(G, key, S["sh"] * arr((1, 1, s)) + (0, 1.5, 0), s, P, r=(5.0, 3.0, 4.2), layers=3)


def hammer_fist(G, side, sh, el, w, s, P, A, S):
    """The forearm ends in a hammer head driven by two rams — a jackhammer fist."""
    g = G["item_" + side]
    d = unit(w - el)
    R, _ = basis(w, w + d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0))
    ex, ez = R[:, 0], R[:, 2]
    hc = w + d * 4.4
    at = lambda x, y, z=0.0: hc + R @ arr((x, y, z))
    G["hand_" + side].ell(w + d * 0.4, (2.6, 2.6, 2.6), M_DIRON)                         # wrist joint
    g.box(hc, (7.6, 6.4, 7.6), M_IRON, R)
    g.box(at(0, -0.4), (8.2, 2.2, 8.2), P, R)
    g.box(at(0, 1.9), (8.2, 0.5, 8.2), emissive("fire", 0, 0), R)                          # a glowing seam
    g.box(at(0, 3.55), (7.2, 0.9, 7.2), M_DIRON, R)
    g.box(at(0, 4.05), (5.6, 0.3, 5.6), emissive("fire", 10, 0.55), R)                     # hot striking face
    for e in (ex, -ex):
        a = w - d * 4.0 + e * 3.6
        b = hc - d * 2.6 + e * 4.2
        ram(G["hand_" + side], a, b, 0.75)
    rivets(g, [at(x, -0.4, 4.15) for x in (-2.6, 0, 2.6)] + [at(x, -0.4, -4.15) for x in (-2.6, 0, 2.6)], r=0.35)
    return dict(hc=hc, face=hc + d * 4.3, d=d)


def molot_fx(fx, A, info, S, ft):
    faces = [info["n"]["face"], info["f"]["face"]]
    mid = (faces[0] + faces[1]) / 2
    g = arr((mid[0], 0.3, mid[2]))
    near = ft < 0.5
    if near:
        for side in ("n", "f"):
            sh, hc = info["sh_" + side], info[side]["hc"]
            v = hc - sh
            if A.get("smear", True):
                smear(fx, sh, np.linalg.norm(v[:2]), np.radians(110), np.arctan2(v[1], v[0]) + 0.3, "xy", 4.5, 4.0)
        fx.ell(g + (0, 0.1, 0), (6.5, 0.25, 6.0), emissive("fire", 0, 0))
        fx.ell(g + (0, 0.2, 0), (3.8, 0.3, 3.4), emissive("fire", 20, 0.85))
    for p in faces:
        sparks(fx, p, n=4, ft=ft, seed=int(p[2] * 10) % 7, big=near)
    puffs(fx, g, n=4, r=2.4, spread=5.0, ft=ft, seed=3)
    for i, d in enumerate(((3.0, 3.2, 2.0), (-2.6, 4.0, -1.5), (4.2, 2.0, -2.6), (-1.0, 5.0, 2.8))):
        fx.box(g + arr(d) * (1.0 + 1.5 * ft), (0.9, 0.8, 0.9), M_IRON, rot_z(0.6 + 1.8 * ft + i))


MOLOT = dict(
    name="Молот", role="разрушитель · 5", k=1.6, paint=FRAME_PAINT["Молот"],
    hip=17.5, hz=4.8, hipx=(0.4, -0.8), LT=8.6, LS=6.8, LU=9.0, LF=10.0, th_leg=1.05, th_arm=1.3,
    sh=arr((0.8, 30.0, 12.2)), torso=molot_torso, item_n=hammer_fist, item_f=hammer_fist, fx=molot_fx,
    allow=[("arm_n", "item_n"), ("arm_f", "item_f")],
    poses=dict(
        idle=dict(lean=-0.12, t=(0.4, -0.6, 0.0), ank=((2.4, 3.6, 5.7), (-3.6, 3.6, -5.7)),
                  hand_n=(8.0, -12.5, 1.0), pole_n=(-0.4, -0.2, 1.0), hand_f=(7.0, -12.5, -1.0), pole_f=(-0.4, -0.2, -1.0)),
        attack=dict(lean=-0.38, t=(1.4, -1.6, 0.0), ank=((4.5, 3.6, 6.0), (-5.5, 3.6, -5.8)),
                    hand_n=(12.5, -14.0, -3.0), pole_n=(0.0, 0.6, 1.0), hand_f=(12.5, -14.0, 3.0), pole_f=(0.0, 0.6, -1.0),
                    ram_n="front", ram_f="front", fx=True),
    ),
)

# ---------------------------------------------------------------- Горн: a stocky furnace with a tall chimney
GORN_CORE = Core(16.0, ((6.2, 8.8), (6.8, 9.6)), (0.0, 25.0, (6.0, 6.0), (7.0, 8.0), 6.0), ring_r=3.0)


def gorn_torso(G, P, S):
    C = GORN_CORE
    C.build(G, P, grate=False, fins=0, gauge=False)
    ch = G["chest"]
    y0, y1, r = 19.2, 31.6, 8.2
    ch.cyl((0, y0, 0), (0, y1, 0), r, M_DIRON, seg=16)                                     # the furnace barrel
    for yb in (19.6, 25.6, 31.0):
        ch.cyl((0, yb, 0), (0, yb + 1.0, 0), r + 0.35, P, seg=16)                           # painted hoops
    for yb, h in ((21.0, 4.2), (26.9, 3.7)):
        for a in np.linspace(0.5, 2 * np.pi - 0.5, 9):
            if abs(np.cos(a)) > 0.8 and np.cos(a) > 0:
                continue
            ch.box((np.cos(a) * (r + 0.15), yb + h / 2, np.sin(a) * (r + 0.15)), (0.4, h, 2.6), P, rot_y(-a))
    ch.ell((0, y1, 0), (r, 2.6, r), P)                                                      # domed top
    rivets(ch, [(np.cos(a) * (r + 0.4), y1 - 0.2, np.sin(a) * (r + 0.4)) for a in np.linspace(0, 2 * np.pi, 13)[:-1]], r=0.35)
    # the mouth: a big grate in the belly, glowing through
    mx = r - 0.2
    ch.box((mx, 24.6, 0), (1.6, 7.4, 8.2), M_DIRON)
    ch.box((mx + 0.4, 24.6, 0), (1.0, 6.2, 7.0), emissive("fire", 20, 0.85))
    for z in np.linspace(-3.0, 3.0, 6):
        ch.box((mx + 1.0, 24.6, z), (0.5, 6.4, 0.5), M_DIRON)
    for y in (22.4, 26.8):
        ch.box((mx + 1.05, y, 0), (0.55, 0.5, 7.4), M_IRON)
    ch.box((mx + 0.6, 28.9, 0), (1.4, 0.9, 9.0), M_IRON)                                   # lintel
    g = arr((np.cos(0.75) * (r + 0.3), 29.6, np.sin(0.75) * (r + 0.3)))
    ch.cyl(g, g + arr((np.cos(0.75), 0, np.sin(0.75))) * 0.6, 1.1, M_STEEL, seg=10)       # gauge
    # the chimney and a bellows on the back
    bk = G["back"]
    c0, c1 = arr((-5.4, 30.4, 0)), arr((-7.2, 51.0, 0))
    bk.cyl(c0, c1, 2.5, M_DIRON, r1=2.1, seg=12)
    for f in (0.25, 0.55, 0.85):
        p = lerp(c0, c1, f)
        bk.cyl(p, p + (0, 0.8, 0), 2.75 - 0.3 * f, M_RUST if f != 0.55 else P, seg=12)
    bk.cyl(c1, c1 + (0, 1.2, 0), 3.0, M_IRON, seg=12)
    bk.box(lerp(c0, c1, 0.4) + (1.6, 0, 0), (2.2, 1.2, 1.2), M_IRON)                      # stay to the dome
    for i, d in enumerate(((0.0, 3.0, 0.0), (-1.6, 6.2, 0.8), (-3.6, 9.6, -0.6))):
        bk.ell(c1 + arr(d), (2.1 + i * 0.9, 1.7 + i * 0.7, 1.9 + i * 0.8), M_PUFF)
    # a stoker's head: round helm, two goggles, a breathing grille
    hd = G["head"]
    hc = arr((3.2, 35.6, 0))
    hd.cyl((1.8, 32.4, 0), hc + (-0.4, -1.4, 0), 1.6, M_DIRON, seg=8)
    hd.ell(hc, (2.9, 2.7, 2.9), P)
    hd.ell(hc + (-0.3, 0.9, 0), (2.6, 1.6, 2.7), M_DIRON)
    for z in (-1.15, 1.15):
        p = hc + arr((2.0, 0.2, z))
        hd.cyl(p, p + (1.0, 0, 0), 0.85, M_STEEL, seg=10)
        hd.ell(p + (1.05, 0, 0), (0.2, 0.65, 0.65), emissive("fire", 6, 0.6))
    for i in range(3):
        hd.box(hc + arr((2.45, -1.2 - i * 0.5, 0)), (0.4, 0.22, 1.8), M_HOLE)
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pauldron(G, key, S["sh"] * arr((1, 1, s)) + (0, 1.2, 0), s, P, r=(4.0, 2.6, 3.6), layers=2)


def tongs(G, side, sh, el, w, s, P, A, S):
    """Forge tongs for a hand: a hinge block and two hooked jaws."""
    g = G["item_" + side]
    d = unit(w - el)
    side_v = unit(np.cross(d, arr((0, 0, 1.0)))) if abs(d[2]) < 0.9 else arr((0, 1.0, 0))
    G["hand_" + side].ell(w + d * 0.3, (1.9, 1.9, 1.9), M_DIRON)
    hb = w + d * 1.9
    R = np.column_stack([d, side_v, np.cross(d, side_v)])
    g.box(hb, (2.6, 3.0, 3.0), M_IRON, R)
    g.cyl(hb - np.cross(d, side_v) * 1.8, hb + np.cross(d, side_v) * 1.8, 0.7, M_STEEL, seg=8)
    a = np.radians(A.get("open", 12.0))
    tips = []
    for sg in (1, -1):
        j = unit(d * np.cos(a) + side_v * np.sin(a) * sg)
        p1 = hb + j * 4.2
        k = unit(d - side_v * sg * 0.9)
        p2 = p1 + k * 2.0
        g.cyl(hb, p1, 0.75, M_DIRON, r1=0.6, seg=6)
        g.cyl(p1, p2, 0.6, M_IRON, r1=0.35, seg=6)
        tips.append(p2)
    return dict(tip=(tips[0] + tips[1]) / 2, d=d)


def gorn_fx(fx, A, info, S, ft):
    X = info["X"]
    mouth = X((8.9, 24.6, 0.0))
    target = arr((23.0, 2.5, 0.0))
    near = ft < 0.5
    n = 16
    rnd = np.random.RandomState(11)
    for i in range(n):                      # the jet widens away from the mouth, licking flames off it
        t = (i + 1) / n
        p = lerp(mouth, target, t) + arr((0, 1.2 * np.sin(np.pi * t), 0))
        r = 1.5 + 3.0 * t
        kind = emissive("fire", 22 if i in (0, n - 1) else (8 if i % 3 == 0 else 0), 0.9)
        fx.ell(p, (r * 1.3, r * 0.75, r * 0.95), kind)
        if i % 2 == 1:
            q = p + arr((rnd.uniform(-1, 1), rnd.uniform(0.4, 1.0), rnd.uniform(-1, 1))) * r * 0.8
            fx.ell(q, (r * 0.45,) * 3, emissive("fire", 0, 0.6))
    puffs(fx, target + arr((2.0, 2.0, 0)), n=4, r=2.6, spread=4.0, ft=ft, seed=5)
    c1 = X((-7.2, 52.0, 0))
    for i, d in enumerate(((0.0, 4.0, 0.0), (-2.0, 8.0, 1.0), (-4.5, 12.0, -1.0))):
        fx.ell(c1 + arr(d), (2.6 + i * 1.2, 2.0 + i * 0.9, 2.4 + i * 1.0), M_PUFF)


GORN = dict(
    name="Горн", role="контроль · 5", k=1.6, paint=FRAME_PAINT["Горн"],
    hip=16.0, hz=5.0, hipx=(0.4, -0.8), LT=7.8, LS=6.4, LU=8.0, LF=8.6, th_leg=1.15, th_arm=1.05,
    sh=arr((-0.4, 28.4, 10.0)), torso=gorn_torso, item_n=tongs, item_f=tongs, fx=gorn_fx,
    allow=[("arm_n", "item_n"), ("arm_f", "item_f")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.6, 3.6, 6.0), (-3.6, 3.6, -6.0)), open=10.0,
                  hand_n=(3.6, -13.4, 2.8), pole_n=(-0.3, -0.2, 1.0), hand_f=(3.0, -13.4, -2.8), pole_f=(-0.3, -0.2, -1.0),
                  ram_n="front", ram_f="front"),
        attack=dict(lean=0.1, t=(-0.6, -0.6, 0.0), ank=((3.5, 3.6, 6.4), (-4.5, 3.6, -6.2)), open=34.0,
                    hand_n=(-1.5, -10.0, 6.0), pole_n=(-0.5, 0.2, 1.0), hand_f=(-1.5, -10.0, -6.0), pole_f=(-0.5, 0.2, -1.0),
                    fx=True),
    ),
)


# ---------------------------------------------------------------- Орудие: a gunner, cannons for forearms
ORUDIE_CORE = Core(20.5, ((6.0, 8.6), (6.6, 9.4)), (0.0, 30.6, (7.6, 8.0), (10.0, 16.0), 8.8), ring_r=2.9)


def orudie_torso(G, P, S):
    C = ORUDIE_CORE
    C.build(G, P, grate=True, fins=4)
    # an ammunition drum across the back, a belt feeding the near cannon
    bk = G["back"]
    dc = arr((-6.6, 31.0, 0))
    bk.cyl(dc + (0, 0, -4.8), dc + (0, 0, 4.8), 4.4, M_IRON, seg=16)
    for z in (-3.6, 0.0, 3.6):
        bk.cyl(dc + (0, 0, z - 0.4), dc + (0, 0, z + 0.4), 4.75, P, seg=16)
    for z in (-4.9, 4.9):
        bk.cyl(dc + (0, 0, z), dc + (0, 0, z + 0.3 * np.sign(z)), 2.0, M_DIRON, seg=10)
    rivets(bk, [dc + arr((np.cos(a) * 4.8, np.sin(a) * 4.8, z)) for a in np.linspace(0.3, 2.8, 4) for z in (-1.8, 1.8)], r=0.32)
    # the head: a compact helm under a long stereo range-finder bar
    hd = G["head"]
    tbox(hd, (0.4, 35.4, 0), (7.0, 8.4), (5.0, 5.8), 1.8, M_DIRON)
    hd.cyl((0.6, 35.4, 0), (1.4, 37.6, 0), 1.5, M_DIRON, seg=8)
    hc = arr((2.0, 39.6, 0))
    tbox(hd, hc, (4.6, 4.0), (4.0, 3.4), 4.2, P)
    hd.box(hc + (2.15, 0.2, 0), (0.5, 0.6, 3.0), emissive("fire", 6, 0.5))
    tbox(hd, hc + (1.0, -1.4, 0), (2.4, 3.2), (2.0, 2.8), 2.0, M_IRON)
    bar_y = hc[1] + 2.8
    hd.box((hc[0], bar_y - 0.6, 0), (1.8, 1.2, 2.0), M_DIRON)
    hd.cyl((hc[0], bar_y, -7.0), (hc[0], bar_y, 7.0), 0.95, M_DIRON, seg=10)
    for z in (-7.0, 7.0):
        hd.cyl((hc[0] - 1.2, bar_y, z), (hc[0] + 1.6, bar_y, z), 1.25, M_IRON, seg=10)
        hd.ell((hc[0] + 1.65, bar_y, z), (0.2, 0.9, 0.9), M_GLASS)
    for z in (-3.5, 3.5):
        hd.cyl((hc[0], bar_y, z - 0.3), (hc[0], bar_y, z + 0.3), 1.15, P, seg=10)
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pauldron(G, key, S["sh"] * arr((1, 1, s)) + (0, 1.2, 0), s, P, r=(4.2, 2.8, 3.6), layers=2)


def cannon(G, side, sh, el, w, s, P, A, S):
    """The forearm ends in a breech and a long barrel with bands, a sight and a muzzle brake."""
    g = G["item_" + side]
    d = unit(w - el)
    up = arr((0, 1.0, 0)) - d * d[1]
    up = unit(up) if np.linalg.norm(up) > 1e-6 else arr((1.0, 0, 0))
    R = np.column_stack([d, up, np.cross(d, up)])
    g.box(w + d * 1.4, (3.4, 4.6, 4.6), M_DIRON, R)                                        # breech
    g.box(w + d * 1.4 + up * 2.6, (2.0, 0.8, 2.0), P, R)
    m0, m1 = w + d * 2.8, w + d * 15.0
    g.cyl(m0, m1, 2.0, M_IRON, seg=12)
    for f in (0.12, 0.4, 0.68):
        p = lerp(m0, m1, f)
        g.cyl(p, p + d * 0.7, 2.4, M_STEEL if f != 0.4 else P, seg=12)
    g.cyl(m0, lerp(m0, m1, 0.3), 2.25, P, seg=12)                                        # painted jacket
    g.box(lerp(m0, m1, 0.35) + up * 2.4, (2.4, 1.0, 0.7), M_DIRON, R)                      # sight
    g.box(m1 + d * 1.1, (2.4, 4.6, 4.6), M_DIRON, R)                                       # muzzle brake
    for v in (up, -up):
        g.box(m1 + d * 1.1 + v * 2.35, (1.3, 0.2, 3.2), M_HOLE, R)
    g.ell(m1 + d * 2.35, (0.2, 1.3, 1.3), M_HOLE, R)
    return dict(muzzle=m1 + d * 2.5, breech=w + d * 1.4 + up * 2.0, d=d, up=up)


def orudie_fx(fx, A, info, S, ft):
    near = ft < 0.5
    for side in ("n", "f"):
        it = info[side]
        mz, d, up = it["muzzle"], it["d"], it["up"]
        if near:
            fx.ell(mz + d * 1.6, (2.6, 2.0, 2.0), emissive("fire", 22, 0.95))                   # muzzle flash
            for a in (0.0, 1.2, -1.2):
                tip = mz + d * 3.6 + up * a
                fx.cyl(mz + d * 0.6, tip, 1.2, emissive("fire", 0, 0), r1=0.2, seg=6)
            for i in range(3):                                                             # tracer streaks
                p = mz + d * (9.0 + i * 4.5) + up * (0.3 * i)
                fx.cyl(p, p + d * 3.0, 0.35, emissive("fire", 4, 0.6), seg=5)
        puffs(fx, mz + d * (2.5 + 2.5 * ft), n=3, r=1.8, spread=2.2, ft=ft, seed=7 if side == "n" else 9)
        bc = it["breech"]                                                                  # a spent case flying back
        cs = bc + up * (2.0 + 2.0 * ft) - d * (1.5 + 2.5 * ft)
        fx.cyl(cs, cs + unit(up - d) * 1.4, 0.45, Mat(ramp("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f0d88a")), seg=6)


ORUDIE = dict(
    name="Орудие", role="стрелок · 5", k=1.6, paint=FRAME_PAINT["Орудие"],
    hip=20.5, hz=4.6, hipx=(0.4, -0.8), LT=9.75, LS=7.25, LU=8.0, LF=8.0, th_leg=1.0, th_arm=1.05,
    sh=arr((-0.6, 34.0, 9.2)), torso=orudie_torso, item_n=cannon, item_f=cannon, fx=orudie_fx,
    allow=[("arm_n", "item_n"), ("arm_f", "item_f")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.8, 3.6, 5.3), (-4.6, 3.6, -5.4)),
                  hand_n=(6.0, -10.5, 1.0), pole_n=(-0.6, -0.2, 0.8), hand_f=(5.5, -10.5, -1.0), pole_f=(-0.6, -0.2, -0.8)),
        attack=dict(lean=0.08, t=(-0.8, -0.4, 0.0), ank=((3.8, 3.6, 5.8), (-5.6, 3.6, -5.8)),
                    hand_n=(11.0, -3.0, 0.6), pole_n=(-0.3, -1.0, 0.6), hand_f=(10.6, -3.0, -0.6), pole_f=(-0.3, -1.0, -0.6),
                    ram_n="front", ram_f="front", fx=True),
    ),
)


# ---------------------------------------------------------------- Механик: a lean worker under a crane jib
MEH_CORE = Core(18.0, ((5.0, 7.0), (5.6, 7.8)), (0.0, 27.4, (6.0, 6.4), (8.0, 12.4), 7.2), ring_r=2.5)


def meh_torso(G, P, S):
    C = MEH_CORE
    C.build(G, P, grate=True, fins=3)
    bk = G["back"]
    # a gas tank for the torch and the crane: mast, jib with a truss, counterweight, pulley
    bk.cyl((-4.6, 23.0, 2.8), (-4.6, 30.0, 2.8), 1.5, M_RUST, seg=10)
    bk.ell((-4.6, 30.0, 2.8), (1.5, 0.8, 1.5), M_RUST)
    base, mast = arr((-4.4, 27.0, -2.2)), arr((-4.8, 44.0, -2.2))
    bk.box(base, (2.8, 3.0, 2.6), M_DIRON)
    bk.cyl(base, mast, 1.0, M_IRON, seg=8)
    tip = arr((13.0, 45.6, -2.2))
    back_end = arr((-9.5, 44.2, -2.2))
    bk.cyl(back_end, tip, 0.8, M_IRON, seg=8)
    for f in (0.2, 0.4, 0.6, 0.8):
        p = lerp(mast, tip, f)
        bk.cyl(p, lerp(mast + (0, -4.5, 0), tip, max(0.0, f - 0.18)), 0.35, M_STEEL, seg=5)
    bk.cyl(mast + (0, -4.5, 0), tip - (0, 0.6, 0), 0.4, M_IRON, seg=5)
    tbox(bk, back_end + (0, -1.2, 0), (3.6, 3.4), (3.6, 3.4), 3.4, M_DIRON)                # counterweight
    bk.cyl(tip + (0, 0, -0.8), tip + (0, 0, 0.8), 1.0, M_STEEL, seg=10)                    # pulley
    # a welder's mask: one big dark lens with an amber spark of an eye
    hd = G["head"]
    tbox(hd, (0.4, 31.4, 0), (6.0, 7.0), (4.4, 4.8), 1.6, M_DIRON)
    hd.cyl((0.6, 31.4, 0), (1.4, 33.4, 0), 1.3, M_DIRON, seg=8)
    hc = arr((2.0, 35.6, 0))
    tbox(hd, hc, (4.4, 3.8), (3.8, 3.2), 4.4, P)
    hd.cyl(hc + (1.9, 0.3, 0), hc + (2.6, 0.3, 0), 1.35, M_DIRON, seg=12)
    hd.ell(hc + (2.65, 0.3, 0), (0.18, 1.05, 1.05), Mat(ramp("#081008", "#10200e", "#1c3418", "#2e5426", "#4e7a40")))
    hd.ell(hc + (2.75, 0.5, 0.3), (0.1, 0.25, 0.25), emissive("fire", 4, 0.6))
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pauldron(G, key, S["sh"] * arr((1, 1, s)) + (0, 1.0, 0), s, P, r=(3.4, 2.2, 3.0), layers=1)


def meh_hook(G, info, A):
    """The crane's cable and hook, hanging where the pose says."""
    X = info["X"]
    tip = X((13.0, 45.0, -2.2))
    hk = arr((tip[0], A.get("hook", 24.0), tip[2]))
    g = G["back"]
    g.cyl(tip, hk, 0.25, M_HOSE, seg=4)
    g.cyl(hk, hk + (1.0, -2.2, 0), 0.65, M_STEEL, seg=6)
    g.cyl(hk + (1.0, -2.2, 0), hk + (-0.8, -3.6, 0), 0.55, M_STEEL, seg=6)


def torch(G, side, sh, el, w, s, P, A, S):
    d = unit(w - el)
    u = grip_dir(d, arr(A.get("torch_dir", (0.6, -0.8, 0.0))))
    hand, h, u = fist(G, "hand_" + side, w, w - el, u, s, P, th=0.85)
    g = G["item_" + side]
    g.cyl(hand - u * 2.2, hand + u * 2.8, 0.75, M_STEEL, seg=8)                            # torch body
    g.cyl(hand + u * 2.8, hand + u * 4.6, 0.5, M_IRON, r1=0.3, seg=6)                     # nozzle
    g.cyl(hand - u * 2.2, hand - u * 2.9, 0.9, M_IRON, seg=8)
    return dict(nozzle=hand + u * 4.8, u=u)


def wrench(G, side, sh, el, w, s, P, A, S):
    u = grip_dir(w - el, arr(A.get("wrench_dir", (0.3, -0.95, 0.0))))
    hand, h, u = fist(G, "hand_" + side, w, w - el, u, s, P, th=0.85)
    g = G["item_" + side]
    g.cyl(hand - u * 2.2, hand + u * 6.4, 0.6, M_IRON, seg=6)
    head = hand + u * 7.4
    R = np.column_stack([u, unit(np.cross(u, arr((0, 0, 1.0)))) if abs(u[2]) < 0.9 else arr((1, 0, 0)),
                         np.cross(u, unit(np.cross(u, arr((0, 0, 1.0))))) if abs(u[2]) < 0.9 else arr((0, 1, 0))])
    g.box(head, (2.0, 3.6, 1.2), M_STEEL, R)
    g.box(head + u * 1.4 + R[:, 1] * 1.1, (1.4, 1.0, 1.2), M_STEEL, R)
    g.box(head + u * 1.4 - R[:, 1] * 1.1, (1.4, 1.0, 1.2), M_STEEL, R)
    return dict(head=head)


def meh_fx(fx, A, info, S, ft):
    noz, u = info["n"]["nozzle"], info["n"]["u"]
    near = ft < 0.5
    blue = emissive("volt", 14, 0.9)
    if near:
        fx.cyl(noz, noz + u * 2.4, 0.55, blue, r1=0.15, seg=6)
        fx.ell(noz + u * 2.6, (1.1, 1.1, 1.1), emissive("volt", 18, 0.95))
    hot = noz + u * 2.8
    rnd = np.random.RandomState(4)
    for i in range(7):                                   # a shower of welding sparks
        d = arr((rnd.uniform(-1.0, 1.4), rnd.uniform(-0.6, 1.0), rnd.uniform(-1, 1))) * (2.2 + 1.6 * ft)
        fx.cyl(hot + d, hot + d * 1.35, 0.22, emissive("fire", 0, 0), seg=4)
    puffs(fx, hot + arr((0.5, 1.8, 0)), n=2, r=1.5, spread=2.0, ft=ft, seed=6)


def meh_item_n(G, side, sh, el, w, s, P, A, S):
    out = torch(G, side, sh, el, w, s, P, A, S)
    return out


MEH = dict(
    name="Механик", role="поддержка · 4", k=1.15, paint=FRAME_PAINT["Механик"],
    hip=18.0, hz=3.6, hipx=(0.3, -0.6), LT=8.6, LS=6.9, LU=7.4, LF=7.8, th_leg=0.82, th_arm=0.85,
    sh=arr((-0.6, 30.6, 7.6)), torso=meh_torso, item_n=meh_item_n, item_f=wrench, fx=meh_fx, after=meh_hook,
    allow=[("hand_n", "item_n"), ("hand_f", "item_f")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.2, 3.6, 4.2), (-3.6, 3.6, -4.2)), hook=26.0,
                  hand_n=(4.6, -10.5, 2.6), pole_n=(-0.5, -0.2, 1.0), torch_dir=(0.75, -0.66, 0.0),
                  hand_f=(2.6, -12.0, -2.8), pole_f=(-0.4, -0.2, -1.0), wrench_dir=(0.35, -0.94, -0.1)),
        attack=dict(lean=-0.24, t=(0.6, -1.0, 0.0), ank=((4.0, 3.6, 4.4), (-4.4, 3.6, -4.4)), hook=18.0,
                    hand_n=(10.0, -8.0, -1.0), pole_n=(-0.2, -0.5, 1.0), torch_dir=(0.66, -0.75, 0.0),
                    hand_f=(-2.0, -11.0, -3.0), pole_f=(-0.3, -0.2, -1.0), wrench_dir=(-0.2, -0.98, 0.0),
                    fx=True),
    ),
)

# ---------------------------------------------------------------- Каменщик: a small mason golem with a hod of stones
STONE = Mat(ramp("#2a2622", "#4a443c", "#6e665a", "#958b7a", "#bcb29e"), noise=0.12)
MASON_CORE = Core(15.0, ((5.4, 7.6), (6.0, 8.4)), (0.0, 23.4, (6.6, 7.0), (8.6, 13.0), 7.2), ring_r=2.6)


def mason_torso(G, P, S):
    C = MASON_CORE
    C.build(G, P, grate=True, fins=2, gauge=False)
    bk = G["back"]
    # a hod on the back: an iron frame with dressed stones in it
    for z in (-3.6, 3.6):
        bk.cyl((-4.6, 19.6, z), (-5.6, 31.0, z), 0.5, M_DIRON, seg=6)
        bk.cyl((-9.4, 20.6, z), (-10.0, 30.4, z), 0.5, M_DIRON, seg=6)
    for y in (20.4, 25.4):
        bk.box((-7.3, y, 0), (5.4, 0.6, 7.8), M_IRON)
    for (x, y, z, sx, sy, sz) in ((-7.2, 22.4, -1.6, 4.0, 3.4, 3.6), (-7.0, 22.4, 2.0, 3.6, 3.4, 3.0),
                                  (-7.4, 27.4, 0.4, 4.2, 3.4, 4.6), (-6.9, 30.2, -1.0, 3.2, 2.4, 3.0)):
        bk.box((x, y, z), (sx, sy, sz), STONE)
    hd = G["head"]
    tbox(hd, (0.4, 27.6, 0), (6.0, 7.4), (4.4, 5.2), 1.4, M_DIRON)
    hc = arr((2.0, 30.6, 0))
    tbox(hd, hc, (4.8, 4.4), (4.2, 3.8), 4.0, P)
    for z in (-0.95, 0.95):
        hd.box(hc + arr((2.2, 0.4, z)), (0.4, 0.5, 1.1), emissive("fire", 5, 0.55))
    hd.box(hc + arr((1.9, 1.3, 0)), (1.2, 0.8, 4.4), M_DIRON)
    hd.box(hc + arr((-0.2, 2.3, 0)), (3.6, 0.7, 0.7), M_DIRON)
    tbox(hd, hc + arr((1.0, -1.3, 0)), (2.6, 3.6), (2.2, 3.2), 2.0, M_IRON)
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pauldron(G, key, S["sh"] * arr((1, 1, s)) + (0, 1.0, 0), s, P, r=(3.6, 2.4, 3.2), layers=1)


def mason_hammer(G, side, sh, el, w, s, P, A, S):
    """A stone-mason's hammer: a flat face and a pick, a short iron-bound haft."""
    u = grip_dir(w - el, arr(A.get("hammer_dir", (0.3, -0.95, 0.0))))
    hand, h, u = fist(G, "hand_" + side, w, w - el, u, s, P, th=0.95)
    g = G["item_" + side]
    top = hand + u * 7.0
    g.cyl(hand - u * 2.4, top, 0.6, M_DIRON, seg=6)
    for k in (-2.6, 2.9):
        g.cyl(hand + u * k, hand + u * (k + 0.4 * np.sign(k)), 0.85, M_STEEL, seg=6)
    f = unit(arr(A.get("face", (1.0, 0.0, 0.0))))
    f = unit(f - u * (f @ u))
    R = np.column_stack([f, u, np.cross(f, u)])
    hc = top + u * 1.4
    g.box(hc, (4.4, 2.6, 2.6), M_IRON, R)
    g.box(hc + f * 2.5, (0.7, 2.8, 2.8), M_STEEL, R)                                        # the flat face
    g.cyl(hc - f * 2.2, hc - f * 4.6, 1.1, M_IRON, r1=0.2, seg=6)                           # the pick
    return dict(face=hc + f * 2.9, hc=hc, f=f)


def trowel(G, side, sh, el, w, s, P, A, S):
    u = grip_dir(w - el, arr(A.get("trowel_dir", (0.2, -0.98, 0.0))))
    hand, h, u = fist(G, "hand_" + side, w, w - el, u, s, P, th=0.95)
    g = G["item_" + side]
    g.cyl(hand - u * 2.2, hand + u * 3.0, 0.5, M_RUST, seg=6)
    n = unit(np.cross(u, arr((0, 0, 1.0)))) if abs(u[2]) < 0.9 else arr((1.0, 0, 0))
    R = np.column_stack([n, u, np.cross(n, u)])
    tbox(g, hand + u * 5.4, (3.0, 0.3), (0.4, 0.3), 4.2, M_STEEL, R)
    return dict()


def mason_fx(fx, A, info, S, ft):
    it = info["n"]
    near = ft < 0.5
    face = it["face"]
    if near and A.get("smear", True):
        sh = info["sh_n"]
        v = it["hc"] - sh
        smear(fx, sh, np.linalg.norm(v[:2]), np.radians(110), np.arctan2(v[1], v[0]) + 0.3, "xy", 2.6, 2.4)
    sparks(fx, face, n=4, spread=1.8, ft=ft, seed=2, big=near)
    g = arr((face[0], 0.3, face[2]))
    puffs(fx, g, n=3, r=1.6, spread=2.6, ft=ft, seed=8)
    for i, d in enumerate(((1.8, 2.0, 1.0), (-1.4, 2.6, -0.8), (2.4, 1.2, -1.6))):
        fx.box(g + arr(d) * (1.0 + 1.5 * ft), (0.8, 0.7, 0.8), STONE, rot_z(0.6 + i + 1.6 * ft))


MASON = dict(
    name="Каменщик", role="призыв Зодчего · 2", k=0.85, paint=ramp("#1c1914", "#3a352c", "#5e584a", "#8a826c", "#b4aa90"),
    hip=15.0, hz=3.8, hipx=(0.4, -0.6), LT=7.2, LS=5.8, LU=6.8, LF=7.2, th_leg=0.95, th_arm=1.0,
    sh=arr((-0.6, 26.4, 8.0)), torso=mason_torso, item_n=mason_hammer, item_f=trowel, fx=mason_fx,
    allow=[("arm_n", "item_n"), ("arm_f", "item_f")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.2, 3.6, 4.4), (-3.4, 3.6, -4.4)),
                  hand_n=(4.4, -9.6, 2.0), pole_n=(-0.5, -0.2, 1.0), hammer_dir=(0.85, 0.5, 0.0), face=(0.5, -0.85, 0.0),
                  hand_f=(3.0, -10.4, -2.2), pole_f=(-0.4, -0.2, -1.0), trowel_dir=(0.6, -0.8, -0.1)),
        attack=dict(lean=-0.3, t=(0.8, -1.4, 0.0), ank=((-2.6, 3.6, 4.4), (4.6, 3.6, -4.4)),
                    hand_n=(9.0, -9.6, -0.8), pole_n=(0.0, 0.3, 1.0), hammer_dir=(0.95, -0.3, 0.0), face=(-0.3, -0.95, 0.0),
                    hand_f=(-4.0, -9.0, -2.6), pole_f=(0.3, -1.0, -0.6), trowel_dir=(-0.3, -0.95, -0.1),
                    ram_n="front", fx=True),
    ),
)


# ---------------------------------------------------------------- Отец колосса: the titan, built on the Guard
BRONZE = ramp("#1a1008", "#3a2610", "#644420", "#946a34", "#c49a58")
CLOTH = Mat(ramp("#1a0606", "#3a0c0c", "#621616", "#8c2420", "#b43a2c"))
GOLD = Mat(ramp("#2a1a06", "#5a3c10", "#8e6420", "#c49038", "#f0c866"))


def colossus_numbers(pose):
    if pose == "idle":
        A = dict(lean=0.0, twist=0.0, t=(0.0, 0.0, 0.0), ankles=((2.8, 3.6, H.HZ + 0.7), (-4.6, 3.6, -H.HZ - 0.8)),
                 hand=(H.WX, H.WY, H.WZ), hand_pole=(1.4, -7.6, 2.0), face=(0.0, 1.0, 0.0), haft=H.carry_haft(),
                 shield=(5.8, -10.0, -2.0), shield_pole=(0.8, -8.0, -1.6), shield_rot=0.5, fx=None, ram="back", carry=1.0)
        return A
    return dict(H.ATTACKS["slam"])


def colossus_parts(pose="idle", fx=True):
    A = colossus_numbers(pose)
    P = Mat(BRONZE)
    G, info = H.pose_parts(A, P, fx=fx)
    R = rot_z(A["lean"]) @ rot_y(A["twist"])
    piv, t = arr((0, H.HIP, 0)), arr(A["t"])
    X = lambda p: R @ (arr(p) - piv) + piv + t
    E = Parts()
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):          # spiked pauldrons
        c = H.SH * arr((1, 1, s)) + (0, 1.2, 0)
        for i, x in enumerate((-2.6, 0.0, 2.6)):
            spike(E[key], c + (x, 2.0, 3.0 * s), c + (x - 1.0, 6.4 - abs(x) * 0.6, (4.8 + 0.4 * i) * s), 1.0, M_IRON)
    hc = arr((2.2, 40.0, 0))                                         # a crown of short blades on the helm
    for i, z in enumerate((-1.6, -0.55, 0.55, 1.6)):
        spike(E["head"], hc + (0.6, 3.8, z), hc + (1.0, 6.4 - 0.5 * abs(z), z * 1.2), 0.55, GOLD)
    E["head"].cyl(hc + (0.2, 3.9, -2.0), hc + (0.2, 3.9, 2.0), 0.6, GOLD, seg=8)
    pole0, pole1 = arr((-9.4, 30.0, -6.2)), arr((-10.4, 64.0, -6.2))  # the banner on its pole
    E["back"].cyl(pole0, pole1, 0.6, M_DIRON, seg=8)
    E["back"].cyl(pole1 + (0.6, -1.0, 0), pole1 + (-9.0, -1.0, 0), 0.45, M_IRON, seg=6)
    E["back"].ell(pole1 + (0, 0.6, 0), (0.9, 1.2, 0.9), GOLD)
    E["back"].box((-6.9, 31.4, -5.6), (3.2, 1.6, 1.4), M_DIRON)                          # the pole's socket
    tl = pole1 + (-0.6, -1.4, 0)
    E["back"].poly([tl, tl + (-8.2, 0, 0), tl + (-8.4, -14.0, 0), tl + (-4.2, -11.0, 0), tl + (-0.2, -14.6, 0)], CLOTH)
    E["back"].poly([tl + (-2.6, -3.2, 0.12), tl + (-5.6, -3.2, 0.12), tl + (-5.6, -6.4, 0.12), tl + (-2.6, -6.4, 0.12)], GOLD)
    for k, m in E.items():
        G[k].extend(pivot(m, R, piv).transformed(I3, t))
    # the maul's head becomes a hammer-anvil: a horn off its back end and a broad face plate
    face, hc2, tf = info["face"], info["hc"], info["tf"]
    G["hammer"].cyl(hc2 - tf * 4.6, hc2 - tf * 10.4, 2.6, M_IRON, r1=0.4, seg=10)
    G["hammer"].box(hc2 + tf * 0.2, (1.0, 1.0, 1.0), GOLD)
    if fx and pose != "idle":                                           # Сотрясение: a wide shock ring
        g = arr((face[0], 0.25, face[2]))
        G["fx"].ell(g, (13.0, 0.2, 11.0), emissive("fire", 0, 0))
        G["fx"].ell(g + (0, 0.05, 0), (9.0, 0.22, 7.6), Mat(ramp("#3a3020", "#6a5a3c", "#9a8a64", "#c8b88e", "#efe2bc"), dither=True))
    return G, info


def colossus_check(pose):
    from clipcheck import report
    G, _ = colossus_parts(pose)
    return report(G, H.ALLOWED + [("boiler", "back"), ("stacks", "back")], skip=("fx", "sparks"))


def colossus_build(pose="idle", k=3.5):
    w, h = int(90 * k), int(92 * k)
    ox, oy = int(40 * k), int(82 * k)
    G, _ = colossus_parts(pose)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


ROSTER = [MOLOT, GORN, ORUDIE, MEH, MASON]
for _S in ROSTER:
    _S["poses"]["broken"] = broken_pose(_S)
BY_NAME = {S["name"]: S for S in ROSTER}




if __name__ == "__main__":
    import sys
    from PIL import ImageFont
    from noise import value_noise
    from paths import font, out
    for S in ROSTER:
        for pose in ("idle", "attack", "broken"):
            bad = check(S, pose)
            print(S["name"], pose, "clipping:", "none" if not bad else [(a, b, round(v, 2)) for v, a, b in bad])
    for pose in ("idle", "attack"):
        bad = colossus_check(pose)
        print("Отец колосса", pose, "clipping:", "none" if not bad else [(a, b, round(v, 2)) for v, a, b in bad])
    # a close-up sheet of every Foundry creature: idle above, attack below
    S2 = 2
    cols = [("Страж", "танк · 6", lambda p: H.build(p, 2.5)),
            ("Молот", "разрушитель · 5", lambda p: build(MOLOT, p, 2.9)),
            ("Горн", "контроль · 5", lambda p: build(GORN, p, 2.7)),
            ("Орудие", "стрелок · 5", lambda p: build(ORUDIE, p, 2.6)),
            ("Механик", "поддержка · 4", lambda p: build(MEH, p, 2.7)),
            ("Каменщик", "призыв Зодчего · 2", lambda p: build(MASON, p, 3.4)),
            ("Отец колосса", "лидер-титан · 7", lambda p: colossus_build(p, 2.1))]
    CW, WW, HH = 172, 172 * 7, 600
    sc = Scene(WW, HH)
    nz = value_noise(WW, HH, 14, 71) * 0.6 + value_noise(WW, HH, 5, 72) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(nz * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        sc.rgb[lv == i] = hexc(col)
    for i, (_, _, fn) in enumerate(cols):
        cx = i * CW + CW // 2 - 14
        for j, pose in enumerate(("idle", "attack")):
            spr = fn(pose)
            by = 262 + j * 290
            e = ((sc.xx - cx) / 52) ** 2 + ((sc.yy - by) / 9) ** 2
            sc.rgb[e <= 1] *= 0.62
            sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
    img = sc.image(S2)
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 21)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 16)
    d.text((24, 12), "Литейщик: все существа — человекоподобные машины", font=ft, fill=(236, 226, 200))
    d.text((24, 52), "Крупно, не в масштабе боя. Сверху покой, снизу атака — момент удара. Все позы без пересечений.",
           font=fr, fill=(190, 182, 164))
    for i, (name, role, _) in enumerate(cols):
        cx = (i * CW + CW // 2) * S2
        d.text((cx - d.textlength(name, font=fh) / 2, 278 * S2), name, font=fh, fill=(226, 186, 106))
        d.text((cx - d.textlength(role, font=fr) / 2, 278 * S2 + 28), role, font=fr, fill=(190, 182, 164))
    img.save(out("foundry_humanoid.png"))
    print(img.size)
