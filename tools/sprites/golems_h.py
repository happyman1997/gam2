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

    def build(self, G, P, grate=True, fins=4, gauge=True, chest=True):
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
        if not chest:
            return
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
    lift = 3.3 * S["th_leg"] + 0.3 - 3.6          # the soles rest on the ground whatever the leg's thickness
    for key, hx, ank, s in (("leg_n", S["hipx"][0], A["ank"][0], 1), ("leg_f", S["hipx"][1], A["ank"][1], -1)):
        h = X((hx, S["hip"], S["hz"] * s))
        kn, an = ik(h, arr(ank) + (0, lift, 0), S["LT"], S["LS"], (1.0, 0.25, 0.0))
        leg(G, key, h, kn, an, s, S["paints"][key] if S.get("paints") else P, th=S["th_leg"])
    A = dict(A, _X=X)
    wpn = S["two_hand"](A, X, S) if S.get("two_hand") else None
    for side, s in (("n", 1), ("f", -1)):
        sh = X(S["sh"] * arr((1, 1, s)))
        if wpn is not None:          # both fists close on the weapon: find the wrists that put the grips there
            Gw, a, tf = wpn["grip_" + side], wpn["a"], S.get("th_fist", 1.0)
            W = Gw - a * 0.0
            for _ in range(5):
                el, w = ik(sh, W, S["LU"], S["LF"], A["pole_" + side])
                h, _, _ = H.hand_frame(w - el, a, s)
                W = Gw - h * 2.4 * tf
            el, w = ik(sh, W, S["LU"], S["LF"], A["pole_" + side])
        else:
            el, w = ik(sh, sh + arr(A["hand_" + side]), S["LU"], S["LF"], A["pole_" + side])
        Pa = S["paints"]["arm_" + side] if S.get("paints") else P
        arm(G, "arm_" + side, sh, el, w, s, Pa, ram_side=A.get("ram_" + side, "back"), th=S["th_arm"], cuff=S.get("cuff", True))
        if wpn is not None:
            fist(G, "hand_" + side, w, w - el, wpn["a"], s, P, th=S.get("th_fist", 1.0))
            info[side] = dict(w=w, el=el)
        else:
            info[side] = S["item_" + side](G, side, sh, el, w, s, P, A, S)
        info["sh_" + side] = sh
    if wpn is not None:
        info["wpn"] = S["weapon"](G, wpn, info, A, S, P)
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
    for key in ("wrench_dir", "hammer_dir", "trowel_dir", "ladle_dir", "sword_dir", "mace_dir"):
        if key in I:
            A[key] = (0.9, -0.15, 0.4)
    if "manip_n" in I:
        A["manip_n"] = ((-6.0, 30.0, 5.4), (-2.0, 22.0, 7.0), (2.0, 14.0, 7.4))
        A["manip_f"] = ((-6.0, 30.0, -5.4), (-3.0, 21.0, -7.2), (0.0, 13.0, -7.6))
        A["gear_in_claw"] = False
    return A


def broken_fx(fx, info):
    X = info["X"]
    for i, d in enumerate(((2.0, 30.0, 0.0), (0.5, 34.0, 1.4), (-1.5, 38.5, -0.6))):
        fx.ell(X(d), (2.0 + i * 0.9, 1.6 + i * 0.7, 1.8 + i * 0.8), M_PUFF)


def hit_point(S):
    """Where this golem's attack lands (model coordinates), or None if it does not strike an enemy."""
    _, info = creature_parts(S, S["poses"]["attack"], fx=False)
    return S["hit"](info) if S.get("hit") else None


def check(S, pose, min_vol=0.05):
    from clipcheck import report
    G, _ = creature_parts(S, S["poses"][pose])
    return report(G, BASE_ALLOWED + S.get("allow", []), skip=("fx",), min_vol=min_vol)


def build(S, pose="idle", k=None, yaw=None):
    k = S["k"] if k is None else k
    cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
    w, h = int(cw * k), int(ch * k)
    ox, oy = int(cx * k), int(cy * k)
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
    hit=lambda info: (info["n"]["face"] + info["f"]["face"]) / 2 * arr((1, 0, 1)),
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
    ch.box((mx + 0.4, 24.6, 0), (1.0, 6.2, 7.0), emissive("fire", 14, 0.7))
    for z in np.linspace(-3.0, 3.0, 6):
        ch.box((mx + 1.0, 24.6, z), (0.5, 6.4, 0.5), M_DIRON)
    for y in (22.4, 26.8):
        ch.box((mx + 1.05, y, 0), (0.55, 0.5, 7.4), M_IRON)
    ch.box((mx + 0.6, 28.9, 0), (1.4, 0.9, 9.0), M_IRON)                                   # lintel
    g = arr((np.cos(0.75) * (r + 0.3), 29.6, np.sin(0.75) * (r + 0.3)))
    ch.cyl(g, g + arr((np.cos(0.75), 0, np.sin(0.75))) * 0.6, 1.1, M_STEEL, seg=10)       # gauge
    # fuel tanks either side of the chimney, the chimney itself
    bk = G["back"]
    for z in (4.8, -4.8):
        bk.cyl((-6.8, 21.4, z), (-6.8, 30.0, z), 2.2, FUEL, seg=12)
        bk.ell((-6.8, 30.0, z), (2.2, 1.1, 2.2), FUEL)
        bk.cyl((-6.8, 23.0, z), (-6.8, 23.6, z), 2.45, M_IRON, seg=12)
        bk.cyl((-6.8, 28.0, z), (-6.8, 28.6, z), 2.45, M_IRON, seg=12)
        bk.box((-4.9, 26.0, z), (1.6, 1.2, 1.4), M_DIRON)
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


FUEL = Mat(ramp("#1e1a10", "#3a3420", "#5e5434", "#86784c", "#b0a070"))


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
    for sg in (1, -1):
        j = unit(d * np.cos(a) + side_v * np.sin(a) * sg)
        p1 = hb + j * 4.2
        k = unit(d - side_v * sg * 0.9)
        g.cyl(hb, p1, 0.75, M_DIRON, r1=0.6, seg=6)
        g.cyl(p1, p1 + k * 2.0, 0.6, M_IRON, r1=0.35, seg=6)
    return dict()


def flamethrower(G, side, sh, el, w, s, P, A, S):
    """A heavy flamethrower held by its pistol grip: the pipe runs along the forearm above the fist,
    a perforated heat jacket, a flared nozzle with an igniter, an armoured hose back to the fuel tanks."""
    d = unit(w - el)
    up = arr((0, 1.0, 0)) - d * d[1]
    up = unit(up) if np.linalg.norm(up) > 1e-6 else arr((1.0, 0, 0))
    hand, h, u = fist(G, "hand_" + side, w, w - el, up, s, P, th=1.0)
    g = G["item_" + side]
    c = hand + u * 4.4 + d * 1.2                             # the pipe's axis above the fist
    R = np.column_stack([d, u, np.cross(d, u)])
    g.cyl(hand - u * 2.2, c, 0.8, M_IRON, seg=8)                                          # the pistol grip
    g.cyl(c - d * 2.6, c + d * 13.0, 1.0, M_DIRON, seg=10)                                # the pipe
    g.box(c - d * 1.6, (2.2, 2.6, 2.6), M_IRON, R)                                        # valve block
    g.cyl(c - d * 2.6, c - d * 3.2, 1.5, M_IRON, seg=10)
    g.cyl(c + d * 0.6, c + d * 2.8, 1.4, P, seg=10)
    g.cyl(c + d * 6.0, c + d * 11.6, 1.55, M_IRON, seg=10)                                # perforated heat jacket
    for t in np.linspace(6.6, 11.0, 5):
        g.cyl(c + d * t, c + d * (t + 0.25), 1.65, M_HOLE, seg=10)
    g.cyl(c + d * 13.0, c + d * 14.8, 1.05, M_STEEL, r1=1.8, seg=10)                      # flared nozzle
    g.ell(c + d * 14.9, (0.2, 1.4, 1.4), M_HOLE, R)
    g.cyl(c + d * 12.0 - u * 1.5, c + d * 14.2 - u * 1.5, 0.35, M_STEEL, seg=6)            # igniter
    g.box(c + d * 1.0 - u * 1.6, (1.4, 1.4, 0.5), M_STEEL, R)                              # trigger guard
    X = info_X = A["_X"]
    out = arr((0, 0, 2.8))
    pts = [c - d * 3.2, c - d * 5.0 + out + u * 1.5, X((-3.0, 19.0, 11.4)), X((-6.4, 22.4, 8.0)), X((-6.8, 24.0, 6.4))]
    for p0, p1 in zip(pts[:-1], pts[1:]):
        G["hose"].cyl(p0, p1, 0.75, M_HOSE, seg=6)
    nozzle = c + d * 15.0
    if not A.get("fx"):
        G["fx"].ell(nozzle - u * 1.5 + d * 0.3, (0.6, 0.8, 0.6), emissive("fire", 6, 0.8))   # pilot light
    return dict(nozzle=nozzle, a=d, up=u)


def gorn_fx(fx, A, info, S, ft):
    w = info["n"]
    noz, a, up = w["nozzle"], w["a"], w["up"]
    near = ft < 0.5
    rnd = np.random.RandomState(13)
    L = 24.0 * (1.0 if near else 0.8)
    n = 22
    for i in range(n):                      # a long roaring jet: a white-hot core, an orange body, red licks
        t = (i + 1) / n
        p = noz + a * (L * t) + up * (1.5 * t * t) + arr((0, rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4))) * t * 3
        r = 0.9 + 3.6 * t ** 0.8
        fx.ell(p, (r * 1.4, r * 0.85, r), emissive("fire", 24 if i in (2, n - 1) else (10 if i % 4 == 0 else 0), 0.9))
        if t < 0.55:
            fx.ell(p, (r * 0.8, r * 0.45, r * 0.55), Mat(ramp("#fff0a0", "#fff6c0", "#fffad8", "#fffde8", "#ffffff"),
                                                         emissive=hexc("#fff0b0"), glow_r=0, glow_k=0))
        if i % 2 == 0:
            q = p + arr((rnd.uniform(-0.6, 0.6), rnd.uniform(0.6, 1.2), rnd.uniform(-1, 1))) * r
            fx.ell(q, (r * 0.4,) * 3, emissive("fire", 0, 0.7))
    end = noz + a * L + up * 1.5
    puffs(fx, end + arr((0, 3.0, 0)), n=4, r=3.0, spread=4.0, ft=ft, seed=5)
    puffs(fx, noz + a * 6 + up * 3.5, n=2, r=1.8, spread=2.0, ft=ft, seed=6)


GORN = dict(
    name="Горн", role="контроль · 5", k=1.6, paint=FRAME_PAINT["Горн"],
    hip=16.0, hz=5.0, hipx=(0.4, -0.8), LT=7.8, LS=6.4, LU=8.0, LF=8.6, th_leg=1.15, th_arm=1.05,
    sh=arr((-0.4, 28.4, 10.0)), torso=gorn_torso, item_n=flamethrower, item_f=tongs, fx=gorn_fx,
    hit=lambda info: (info["n"]["nozzle"] + info["n"]["a"] * 24.0) * arr((1, 0, 1)),
    allow=[("hand_n", "item_n"), ("arm_f", "item_f"), ("hose", "back"), ("hose", "item_n"), ("hose", "arm_n")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.6, 3.6, 6.0), (-3.6, 3.6, -6.0)), open=10.0,
                  hand_n=(5.0, -12.5, 3.0), pole_n=(-0.4, -0.2, 1.0), hand_f=(3.0, -13.4, -2.8), pole_f=(-0.3, -0.2, -1.0),
                  ram_n="back", ram_f="front"),
        attack=dict(lean=-0.06, t=(0.6, -0.8, 0.0), ank=((4.4, 3.6, 6.2), (-5.0, 3.6, -6.0)), open=30.0,
                    hand_n=(10.0, -7.4, 1.6), pole_n=(-1.0, -0.3, 0.6), hand_f=(-1.0, -11.0, -5.6), pole_f=(-0.5, 0.2, -1.0),
                    ram_n="back", fx=True),
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
    hit=lambda info: (info["n"]["muzzle"] + info["n"]["d"] * (info["n"]["muzzle"][1] / max(0.05, -info["n"]["d"][1]))) * arr((1, 0, 1)),
    allow=[("arm_n", "item_n"), ("arm_f", "item_f")],
    poses=dict(
        idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.8, 3.6, 5.3), (-4.6, 3.6, -5.4)),
                  hand_n=(6.0, -10.5, 1.0), pole_n=(-0.6, -0.2, 0.8), hand_f=(5.5, -10.5, -1.0), pole_f=(-0.6, -0.2, -0.8)),
        attack=dict(lean=0.08, t=(-0.8, -0.4, 0.0), ank=((3.8, 3.6, 5.8), (-5.6, 3.6, -5.8)),
                    hand_n=(10.5, -7.5, 0.6), pole_n=(-1.0, -0.2, 0.6), hand_f=(10.1, -7.5, -0.6), pole_f=(-1.0, -0.2, -0.6),
                    ram_n="front", ram_f="front", fx=True),
    ),
)


# ---------------------------------------------------------------- Механик: a walking workshop
MEH_CORE = Core(17.0, ((5.0, 7.2), (5.6, 8.0)), (0.0, 26.0, (6.2, 6.6), (8.2, 12.6), 7.2), ring_r=2.5)
HAZARD = Mat(ramp("#0c0c0c", "#161616", "#202020", "#2c2c2c", "#3a3a3a"))
LAMP = Mat(ramp("#fff0c0", "#fff4d0", "#fff8e0", "#fffcf0", "#ffffff"), emissive=hexc("#ffe8a0"), glow_r=10, glow_k=0.6)
BEAM = Mat(ramp("#6a5a30", "#8a7840", "#b09a58", "#d8c078", "#f8e8a8"), dither=True)


def meh_torso(G, P, S):
    C = MEH_CORE
    C.build(G, P, grate=True, fins=3)
    bk = G["back"]
    # a tool chest on the back: drawers, handles, hazard stripes, an oil tank under it
    tbox(bk, (-5.4, 27.6, 0), (5.2, 11.6), (5.0, 12.4), 9.4, P)
    tbox(bk, (-5.4, 32.6, 0), (5.4, 12.8), (5.4, 12.8), 0.8, M_DIRON)
    for y in (24.6, 27.4, 30.2):
        bk.box((-5.4, y, 6.3), (4.4, 0.25, 0.2), M_HOLE)
        bk.box((-5.4, y + 1.2, 6.45), (1.6, 0.4, 0.3), M_STEEL)
    for i in range(5):                                                 # black stripes on the yellow
        bk.box((-7.95, 24.4 + i * 1.9, 0), (0.15, 0.9, 11.0), HAZARD, rot_x(0.5))
    bk.cyl((-5.4, 21.2, -4.6), (-5.4, 21.2, 4.6), 1.7, M_RUST, seg=10)
    for z in (3.0, -3.0):                                              # manipulator mounts on the chest's lid
        bk.cyl((-5.4, 33.0, z), (-5.4, 34.2, z), 1.5, M_DIRON, seg=10)
    # the head is a work lamp in a cage
    hd = G["head"]
    tbox(hd, (0.4, 30.2, 0), (6.0, 7.2), (4.4, 5.0), 1.6, M_DIRON)
    hd.cyl((0.6, 30.2, 0), (1.2, 32.2, 0), 1.3, M_DIRON, seg=8)
    hc = arr((1.8, 34.0, 0))
    hd.cyl(hc + (-1.8, 0, 0), hc + (1.8, 0, 0), 2.4, P, seg=14)
    hd.cyl(hc + (1.6, 0, 0), hc + (2.2, 0, 0), 2.7, M_DIRON, seg=14)
    hd.ell(hc + (2.25, 0, 0), (0.3, 1.9, 1.9), LAMP)
    for zz in (-1.1, 0.0, 1.1):
        hd.box(hc + (2.7, 0, zz), (0.3, 4.4, 0.25), M_IRON)
    hd.box(hc + (2.7, 0, 0), (0.3, 0.25, 4.4), M_IRON)
    tbox(hd, hc + (0.3, 2.6, 0), (4.4, 5.4), (3.2, 4.0), 0.8, M_DIRON)                       # hood
    hd.cyl(hc + (-1.0, 2.8, -1.2), hc + (-1.4, 5.6, -1.4), 0.2, M_STEEL, seg=4)               # whip aerial
    hd.ell(hc + (-1.4, 5.8, -1.4), (0.3, 0.3, 0.3), emissive("fire", 3, 0.5))
    for s, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        pauldron(G, key, S["sh"] * arr((1, 1, s)) + (0, 1.0, 0), s, P, r=(3.4, 2.2, 3.0), layers=1)


def manipulator(g, base, j1, j2, tip, tool, P, A):
    """A jointed tool arm: three segments on gear joints, a ram on the first."""
    for a, b, r in ((base, j1, 0.75), (j1, j2, 0.65), (j2, tip, 0.55)):
        g.cyl(a, b, r, M_IRON, seg=8)
        g.cyl(lerp(a, b, 0.4), lerp(a, b, 0.6), r + 0.2, P, seg=8)
    for j in (base, j1, j2):
        g.ell(j, (1.05, 1.05, 1.05), M_DIRON)
    ram(g, lerp(base, j1, 0.15) + arr((0.8, 0.2, 0)), lerp(j1, j2, 0.3) + arr((0, 0.8, 0)), 0.4)
    d = unit(tip - j2)
    if tool == "torch":
        g.cyl(tip, tip + d * 1.6, 0.7, M_STEEL, r1=0.3, seg=6)
        return tip + d * 1.8
    side = unit(np.cross(d, arr((0, 0, 1.0)))) if abs(d[2]) < 0.9 else arr((1.0, 0, 0))
    for sg in (1, -1):                                                 # a two-fingered claw
        k = tip + side * 0.9 * sg
        g.cyl(tip, k + d * 1.6, 0.4, M_STEEL, seg=5)
        g.cyl(k + d * 1.6, k + d * 2.6 - side * 0.6 * sg, 0.32, M_STEEL, seg=5)
    return tip + d * 2.4


def meh_after(G, info, A):
    X = info["X"]
    g = G["manip"]
    tips = {}
    for side, z, tool in (("n", 3.0, "torch"), ("f", -3.0, "claw")):
        base = X((-5.4, 34.6, z))
        j1, j2, tip = (arr(p) for p in A["manip_" + side])
        tips[side] = manipulator(g, base, j1, j2, tip, tool, Mat(FRAME_PAINT["Механик"]), A)
    info["tips"] = tips
    if A.get("gear_in_claw"):
        c = tips["f"]
        G["manip"].cyl(c + (0, 0, -0.4), c + (0, 0, 0.4), 1.5, M_STEEL, seg=10)
        for i in range(8):
            a = 2 * np.pi * i / 8
            G["manip"].box(c + (np.cos(a) * 1.7, np.sin(a) * 1.7, 0), (0.6, 0.5, 0.8), M_STEEL, rot_z(a))


def big_wrench(G, side, sh, el, w, s, P, A, S):
    u = grip_dir(w - el, arr(A.get("wrench_dir", (0.3, -0.95, 0.0))))
    hand, h, u = fist(G, "hand_" + side, w, w - el, u, s, P, th=0.85)
    g = G["item_" + side]
    g.cyl(hand - u * 2.2, hand + u * 8.4, 0.75, M_IRON, seg=6)
    head = hand + u * 9.6
    v = unit(np.cross(u, arr((0, 0, 1.0)))) if abs(u[2]) < 0.9 else arr((1.0, 0, 0))
    R = np.column_stack([u, v, np.cross(u, v)])
    g.box(head, (2.4, 4.6, 1.6), M_STEEL, R)
    for sg in (1, -1):
        g.box(head + u * 1.8 + v * 1.5 * sg, (1.8, 1.4, 1.6), M_STEEL, R)
    g.cyl(head - u * 0.6 + v * 0.0, head - u * 0.6 + R[:, 2] * 0.9, 0.7, M_IRON, seg=8)
    return dict(head=head + u * 2.4)


def oil_can(G, side, sh, el, w, s, P, A, S):
    u = grip_dir(w - el, arr(A.get("can_dir", (0.0, 1.0, 0.0))))
    hand, h, u = fist(G, "hand_" + side, w, w - el, u, s, P, th=0.85)
    g = G["item_" + side]
    body = hand + h * 2.6
    g.cyl(body - u * 1.6, body + u * 1.4, 1.6, Mat(ramp("#1a1c10", "#34381e", "#545c30", "#7a8448", "#a6b06a")), seg=10)
    g.cyl(body + u * 1.4, body + u * 2.2, 1.6, M_STEEL, r1=0.6, seg=10)
    sp = unit(u + h * 0.9)
    g.cyl(body + u * 2.0, body + u * 2.0 + sp * 5.0, 0.32, M_STEEL, r1=0.18, seg=6)          # long spout
    g.cyl(hand - u * 1.4, hand + u * 1.4, 0.4, M_IRON, seg=6)
    return dict(spout=body + u * 2.0 + sp * 5.2, sp=sp)


def meh_fx(fx, A, info, S, ft):
    near = ft < 0.5
    t = info["tips"]["n"]
    work = arr(A["work"])
    if near:
        fx.ell(work, (1.6, 1.6, 1.6), emissive("volt", 22, 0.95))                           # the weld's flash
        fx.cyl(t, work, 0.45, emissive("volt", 0, 0), r1=0.2, seg=6)
    rnd = np.random.RandomState(4)
    for i in range(14):                                  # a shower of welding sparks, falling
        d = arr((rnd.uniform(-0.6, 1.6), rnd.uniform(-1.6, 1.0), rnd.uniform(-1.2, 1.2))) * (2.6 + 1.8 * ft)
        fx.cyl(work + d, work + d * 1.4 + arr((0, -0.6, 0)), 0.25, emissive("fire", 2 if i < 3 else 0, 0.6), seg=4)
    puffs(fx, work + arr((-0.5, 2.4, 0)), n=2, r=1.4, spread=1.8, ft=ft, seed=6)
    lamp = info["X"]((4.4, 34.0, 0))                      # the lamp lights the work
    for i in range(4):
        f = (i + 0.5) / 4
        fx.ell(lerp(lamp, work, f), (0.6 + 1.2 * f,) * 3, BEAM)
    sp = info["f"]["spout"]                              # oil dripping from the can
    for i in range(3):
        fx.ell(sp + arr((0.2 * i, -1.0 - 1.2 * i, 0)), (0.3, 0.45, 0.3), Mat(ramp("#0a0a06", "#1c1a0e", "#34301a", "#5a542c", "#8a8044")))


MEH = dict(
    name="Механик", role="поддержка · 4", k=1.15, paint=FRAME_PAINT["Механик"],
    hip=17.0, hz=3.8, hipx=(0.3, -0.6), LT=8.0, LS=6.6, LU=7.2, LF=7.8, th_leg=0.85, th_arm=0.85,
    sh=arr((-0.6, 29.4, 7.8)), torso=meh_torso, item_n=big_wrench, item_f=oil_can, fx=meh_fx, after=meh_after,
    allow=[("hand_n", "item_n"), ("hand_f", "item_f"), ("back", "manip")],
    poses=dict(
        idle=dict(lean=-0.04, t=(0.0, 0.0, 0.0), ank=((2.2, 3.6, 4.4), (-3.6, 3.6, -4.4)),
                  hand_n=(3.4, -11.0, 2.4), pole_n=(-0.5, -0.2, 1.0), wrench_dir=(0.25, -0.97, 0.0),
                  hand_f=(4.8, -8.6, -2.4), pole_f=(-0.6, -0.4, -1.0), can_dir=(0.0, 1.0, 0.0),
                  manip_n=((-4.0, 40.5, 6.0), (1.6, 43.0, 9.0), (5.4, 39.0, 9.4)),
                  manip_f=((-4.0, 40.5, -6.0), (1.6, 43.0, -9.0), (5.4, 39.0, -9.4))),
        attack=dict(lean=-0.28, t=(0.8, -1.4, 0.0), ank=((4.0, 3.6, 4.6), (-4.4, 3.6, -4.6)),
                    hand_n=(9.0, -4.0, 1.8), pole_n=(-0.6, -1.0, 0.8), wrench_dir=(0.55, 0.55, -0.6),
                    hand_f=(7.6, -5.0, -2.2), pole_f=(-0.6, -0.6, -1.0), can_dir=(0.5, 0.85, 0.0),
                    manip_n=((-2.0, 42.0, 6.0), (6.0, 40.0, 9.5), (12.2, 29.0, 4.0)),
                    manip_f=((-2.0, 42.0, -6.0), (6.0, 40.0, -9.5), (12.8, 29.6, -3.0)),
                    gear_in_claw=True, work=(14.8, 26.6, 0.4), fx=True),
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
    sparks(fx, face, n=4, spread=1.8, ft=ft, seed=2, big=near)
    g = arr((face[0], 0.3, face[2]))
    puffs(fx, g, n=3, r=1.6, spread=2.6, ft=ft, seed=8)
    for i, d in enumerate(((1.8, 2.0, 1.0), (-1.4, 2.6, -0.8), (2.4, 1.2, -1.6))):
        fx.box(g + arr(d) * (1.0 + 1.5 * ft), (0.8, 0.7, 0.8), STONE, rot_z(0.6 + i + 1.6 * ft))


MASON = dict(
    name="Каменщик", role="призыв Зодчего · 2", k=0.85, paint=ramp("#1c1914", "#3a352c", "#5e584a", "#8a826c", "#b4aa90"),
    hip=15.0, hz=3.8, hipx=(0.4, -0.6), LT=7.2, LS=5.8, LU=6.8, LF=7.2, th_leg=0.95, th_arm=1.0,
    sh=arr((-0.6, 26.4, 8.0)), torso=mason_torso, item_n=mason_hammer, item_f=trowel, fx=mason_fx,
    hit=lambda info: info["n"]["face"] * arr((1, 0, 1)),
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


# ---------------------------------------------------------------- Отец колосса: a war machine
GUNMETAL = ramp("#101216", "#20242a", "#363c44", "#545c66", "#808993")
WARN = Mat(ramp("#1a0404", "#3e0a08", "#6a1410", "#9a2016", "#c83420"))
OPTIC = Mat(ramp("#5a0a06", "#a01a10", "#e0402a", "#ff8060", "#ffd0c0"), emissive=hexc("#ff3a24"), glow_r=8, glow_k=0.8)
ENERGY = Mat(ramp("#2a6a8a", "#4aa8d0", "#8ad8f0", "#c8f2ff", "#ffffff"), emissive=hexc("#70e0ff"), glow_r=12, glow_k=0.75)
ARC = Mat(ramp("#4aa8d0", "#8ad8f0", "#c8f2ff", "#eafaff", "#ffffff"), emissive=hexc("#90ecff"), glow_r=6, glow_k=0.5)
COPPER = Mat(ramp("#2a1006", "#5a240e", "#8a4018", "#b8662a", "#e09a50"))
BRASS = Mat(ramp("#3a2410", "#6a4818", "#a0782c", "#d0a848", "#f0d88a"))
COL_CORE = Core(20.0, ((8.6, 13.0), (9.4, 14.4)), (0.6, 31.6, (10.4, 14.0), (14.6, 30.0), 10.4), ring_r=3.2)
COL_SH = arr((0.4, 36.0, 17.0))


def stripes(m, c, R, w, h, n, d=0.3):
    """Red-and-black hazard stripes on a plate (in the plate's own axes: x out, y up, z across)."""
    for i in range(n):
        z = (i - (n - 1) / 2) * w / n
        m.box(arr(c) + R @ arr((d, 0, z)), (0.3, h, w / n * 0.5), WARN, R @ rot_x(0.5))


def col_torso(G, P, S):
    C = COL_CORE
    C.build(G, P, grate=True, fins=4, gauge=False)
    ch = G["chest"]
    top = C.cy + C.h / 2
    # armoured collar: the head sits low inside it, between the shoulders
    tbox(ch, (1.6, top + 0.6, 0), (10.0, 16.0), (8.0, 12.0), 2.0, M_DIRON)
    for s_ in (1, -1):
        tbox(ch, (1.4, top + 1.6, 6.6 * s_), (7.0, 2.6), (5.0, 2.0), 3.2, P, rot_x(0.35 * s_))
    for s_ in (1, -1):                                                   # red warning plates on the breast
        y = C.sy + 2.6
        stripes(ch, (C.front(y) + 0.1, y, 7.0 * s_), I3, 5.0, 3.4, 4)
    for s_ in (1, -1):
        ch.ell((C.front(C.sy - 3.4) + 0.4, C.sy - 3.4, 4.6 * s_), (0.4, 0.5, 0.5), OPTIC)
    # the back: a generator between two exhaust stacks and a capacitor tower that feeds the mace
    bk = G["back"]
    bc = arr((-8.6, top + 1.0, 0))
    tbox(bk, bc + (0, -4.0, 0), (7.0, 20.0), (6.4, 18.0), 9.0, M_DIRON)
    bk.cyl(bc + (0, 2.4, -7.2), bc + (0, 2.4, 3.6), 3.6, P, seg=14)                          # generator drum
    for z in (-6.0, -3.4, -0.8, 1.8):
        bk.cyl(bc + (0, 2.4, z), bc + (0, 2.4, z + 0.6), 3.9, M_DIRON, seg=14)
    stripes(bk, bc + (-3.6, 2.4, -1.8), rot_y(np.pi), 8.0, 2.8, 5)
    for z, h_ in ((-9.8, 9.0), (-12.6, 7.0)):                                                # exhaust stacks
        b0 = bc + (-1.0, -2.0, z)
        b1 = b0 + (-1.4, h_, 0)
        bk.cyl(b0, b1, 1.4, M_DIRON, seg=10)
        bk.cyl(b1 - (0, 1.2, 0), b1, 1.8, M_IRON, seg=10)
        bk.cyl(b1 - (0, 1.0, 0), b1 + (0, 0.1, 0), 1.0, M_HOLE, seg=8)
        for i, d in enumerate(((-0.4, 2.4, 0.0), (-1.8, 5.2, -0.6))):
            bk.ell(b1 + arr(d), (1.6 + i * 0.8, 1.3 + i * 0.6, 1.5 + i * 0.7), M_PUFF)
    t0 = bc + (-1.2, 5.4, -2.4)                                                              # coil mast with a beacon
    bk.cyl(t0 - (0, 7.0, 0), t0 + (0, 6.0, 0), 1.3, M_DIRON, seg=10)
    for i in range(4):
        y = t0[1] + i * 1.5
        bk.cyl((t0[0], y, t0[2]), (t0[0], y + 0.6, t0[2]), 2.0 - 0.15 * i, COPPER, seg=12)
    bk.cyl(t0 + (0, 6.0, 0), t0 + (0, 6.6, 0), 1.6, M_DIRON, seg=10)
    bk.ell(t0 + (0, 7.3, 0), (1.1, 1.1, 1.1), OPTIC)                                          # red beacon
    for z in (-1.0, 1.0):                                                                    # antenna mast
        bk.cyl(bc + (-2.6, 5.0, z * 1.6 - 9.0), bc + (-3.8, 14.0, z * 2.0 - 9.0), 0.2, M_STEEL, seg=4)
    # the head: a low armoured hunter's head, a slit visor with three red eyes, a grilled jaw
    hd = G["head"]
    hc = arr((5.6, top + 4.6, 0))
    hd.cyl(hc - (2.8, 2.6, 0), hc - (1.2, 0.6, 0), 2.2, M_DIRON, seg=8)                     # neck
    tbox(hd, hc, (6.8, 6.8), (5.4, 5.6), 5.0, P)                                             # skull
    tbox(hd, hc + (0.8, 3.1, 0), (5.4, 5.6), (3.0, 3.4), 1.4, P)                             # crown plate
    hd.box(hc + (-0.2, 3.4, 0), (5.6, 0.6, 0.9), WARN)                                      # red stripe over the head
    tbox(hd, hc + (3.0, -0.2, 0), (1.2, 6.4), (2.2, 6.0), 4.0, M_DIRON, rot_z(-0.25))        # sloped face plate
    hd.box(hc + (3.9, 0.9, 0), (0.8, 1.3, 5.6), M_HOLE, rot_z(-0.25))                        # visor slit
    hd.ell(hc + (4.3, 0.9, 0), (0.6, 0.75, 0.95), OPTIC)                                     # three eyes
    for z in (-1.9, 1.9):
        hd.ell(hc + (4.25, 0.95, z), (0.5, 0.55, 0.6), OPTIC)
    tbox(hd, hc + (3.0, -2.9, 0), (2.4, 4.0), (2.8, 5.2), 1.8, M_IRON)                       # jaw
    for z in (-1.5, -0.5, 0.5, 1.5):
        hd.box(hc + (4.3, -2.9, z), (0.4, 1.6, 0.35), M_HOLE)                                # grille
    for s_ in (1, -1):                                                                       # cheek guards
        tbox(hd, hc + (0.8, -0.6, 3.5 * s_), (5.6, 0.9), (4.4, 0.7), 4.4, M_DIRON, rot_x(-0.12 * s_))
        hd.box(hc + (-2.8, 1.0, 2.0 * s_), (0.9, 1.8, 0.9), M_STEEL)                         # sensor stubs
    # massive angular pauldrons with red warning edges
    for s_, key in ((1, "pauldron_n"), (-1, "pauldron_f")):
        c = COL_SH * arr((1, 1, s_)) + (0, 2.4, 0)
        pd = G[key]
        tbox(pd, c + (0, 0.6, 0.0), (10.4, 8.0), (7.4, 5.2), 3.4, P, rot_x(-0.22 * s_))
        tbox(pd, c + (0, -1.8, 2.4 * s_), (11.0, 3.4), (10.4, 3.8), 3.0, P, rot_x(-0.62 * s_))
        pd.box(c + (0, 2.35, 0.0), (7.8, 0.3, 5.4), M_DIRON, rot_x(-0.22 * s_))
        pd.box(c + (0, -2.4, 4.0 * s_), (11.0, 0.9, 0.6), WARN, rot_x(-0.62 * s_))
        rivets(pd, [c + (x, -0.6, 3.6 * s_) for x in (-3.6, 0.0, 3.6)], r=0.4)
        for x in (-2.6, 0.8):                                                                 # spikes
            spike(pd, c + (x, 2.0, 0.6 * s_), c + (x - 1.4, 4.8, 1.4 * s_), 0.8, M_IRON)


def shock_mace(G, side, sh, el, w, s, P, A, S):
    """An electric mace: a long haft with a copper coil, a flanged head on an insulated collar, arcs."""
    u = grip_dir(w - el, arr(A.get("mace_dir", (0.0, 1.0, 0.0))))
    hand, h, u = fist(G, "hand_" + side, w, w - el, u, s, P, th=1.5)
    g = G["item_" + side]
    e1 = unit(np.cross(u, arr((0, 0, 1.0)))) if abs(u[2]) < 0.95 else arr((1.0, 0, 0))
    e2 = np.cross(u, e1)
    g.cyl(hand - u * 4.6, hand + u * 14.0, 0.9, M_DIRON, seg=8)                             # haft
    g.cyl(hand - u * 5.6, hand - u * 4.2, 1.3, M_IRON, seg=8)                                # pommel
    for t in (3.6, 4.6, 5.6, 6.6, 7.6):                                                      # copper coil
        g.cyl(hand + u * t, hand + u * (t + 0.5), 1.3, COPPER, seg=10)
    g.cyl(hand + u * 9.2, hand + u * 11.4, 1.2, M_HOLE, seg=10)                              # insulator
    for t in (9.4, 10.4):
        g.cyl(hand + u * t, hand + u * (t + 0.4), 1.6, M_DIRON, seg=10)
    c = hand + u * 17.0
    g.cyl(c - u * 3.8, c + u * 3.4, 2.4, M_IRON, seg=12)                                    # head core
    g.cyl(c - u * 0.6, c + u * 0.6, 2.8, ENERGY, seg=12)                                    # glowing band
    g.cyl(c - u * 4.4, c - u * 3.6, 2.9, M_DIRON, seg=12)
    for i in range(6):                                                                       # flanges
        a = i * np.pi / 3 + 0.3
        r = e1 * np.cos(a) + e2 * np.sin(a)
        Rf = np.column_stack([r, u, np.cross(r, u)])
        tbox(g, c + r * 3.0, (3.2, 0.8), (1.6, 0.6), 6.8, M_IRON, Rf)
        g.box(c + r * 4.7, (0.6, 5.0, 0.65), M_STEEL, Rf)                                    # honed edge
    spike(g, c + u * 3.4, c + u * 7.4, 1.4, M_IRON)                                          # top spike
    rnd = np.random.RandomState(17)
    for i in range(6):                                                                       # arcs between the flanges
        a = rnd.uniform(0, 2 * np.pi)
        r = e1 * np.cos(a) + e2 * np.sin(a)
        p = c + r * 4.4 + u * rnd.uniform(-2.4, 2.4)
        q = p + r * 1.3 + u * rnd.uniform(-1.0, 1.0)
        g.cyl(p, q, 0.18, ARC, seg=4)
        g.cyl(q, q + r * 1.0 + e1 * rnd.uniform(-0.8, 0.8), 0.15, ARC, seg=4)
    return dict(head=c, u=u, tip=c + u * 7.4, hand=hand)


def minigun(G, side, sh, el, w, s, P, A, S):
    """A rotary minigun on a pistol grip: six barrels in clamps, a drive motor, a box of belted rounds."""
    d = unit(w - el)
    up = arr((0, 1.0, 0)) - d * d[1]
    up = unit(up) if np.linalg.norm(up) > 1e-6 else arr((1.0, 0, 0))
    hand, h, u = fist(G, "hand_" + side, w, w - el, up, s, P, th=1.5)
    g = G["item_" + side]
    e = unit(np.cross(d, u))
    R = np.column_stack([d, u, e])
    c = hand + u * 6.6 + d * 4.4                                                             # axis of the gun above the fist
    g.cyl(hand - u * 3.2, c - u * 1.6, 1.1, M_IRON, seg=8)                                   # pistol grip
    g.box(c - d * 0.2, (8.0, 5.2, 5.0), P, R)                                                # receiver
    g.box(c - d * 0.2 + u * 2.7, (7.0, 0.4, 4.0), WARN, R)
    g.cyl(c - d * 6.6, c - d * 4.2, 2.4, M_DIRON, seg=12)                                    # drive motor
    for t in (-6.2, -5.2):
        g.cyl(c + d * t, c + d * (t + 0.35), 2.7, M_IRON, seg=12)
    g.cyl(c + d * 3.8, c + d * 5.2, 2.6, M_IRON, seg=12)                                     # front bearing
    for i in range(6):                                                                       # the barrel cluster
        a = i * np.pi / 3 + A.get("spin", 0.0)
        o = (u * np.cos(a) + e * np.sin(a)) * 1.25
        g.cyl(c + d * 5.0 + o, c + d * 20.0 + o, 0.42, M_STEEL if i % 2 else M_DIRON, seg=6)
    for t in (11.0, 18.6):                                                                   # clamps
        g.cyl(c + d * t, c + d * (t + 0.8), 2.0, M_DIRON, seg=12)
    g.cyl(c + d * 19.4, c + d * 20.2, 0.6, M_HOLE, seg=8)
    g.cyl(c + u * 3.6 - d * 2.6, c + u * 3.6 + d * 2.0, 0.45, M_IRON, seg=6)                 # carry handle
    for t in (-2.6, 2.0):
        g.cyl(c + u * 2.6 + d * t, c + u * 3.6 + d * t, 0.4, M_IRON, seg=6)
    bx = c + d * 6.6 - u * 5.2                                                               # ammunition box under the barrels
    g.box(bx, (6.0, 4.6, 3.8), M_IRON, R)
    g.box(bx + u * 0.4, (6.2, 0.8, 4.0), WARN, R)
    for i in range(6):                                                                       # the belt up into the receiver
        p = lerp(bx + u * 2.3 - d * 1.6, c - u * 2.5 + d * 1.8, i / 5)
        g.box(p + e * 0.0, (0.9, 0.5, 1.4), BRASS, R)
    return dict(muzzle=c + d * 20.6, d=d, up=u, c=c, e=e)


def col_fx(fx, A, info, S, ft):
    mc = info["n"]
    head, u = mc["head"], mc["u"]
    near = ft < 0.5
    g = arr((head[0], 0.25, head[2]))
    if near:                                                   # the mace lands: a burst of lightning
        fx.ell(head - u * 0.5, (3.0, 3.0, 3.0), ENERGY)
        rnd = np.random.RandomState(41)
        for i in range(9):
            a = rnd.uniform(0, 2 * np.pi)
            p = head + arr((np.cos(a), rnd.uniform(-0.6, 1.0), np.sin(a))) * rnd.uniform(4.0, 8.0)
            p[1] = max(p[1], 0.3)
            q = lerp(head, p, 0.5) + arr((rnd.uniform(-1.4, 1.4), rnd.uniform(-1.0, 1.0), rnd.uniform(-1.4, 1.4)))
            fx.cyl(head, q, 0.26, ARC, seg=4)
            fx.cyl(q, p, 0.2, ARC, seg=4)
        fx.ell(g + (0, 0.1, 0), (7.0, 0.2, 6.0), Mat(ramp("#0e1a22", "#18303c", "#245060", "#3a7a8e", "#6ab8c8"), dither=True))
    sparks(fx, head, n=6, spread=3.4, ft=ft, seed=5, big=False)
    puffs(fx, g, n=4, r=2.6, spread=4.6, ft=ft, seed=3)
    mg = info["f"]                                             # and the minigun pours fire
    mz, d, up, e = mg["muzzle"], mg["d"], mg["up"], mg["e"]
    if near:
        fx.ell(mz + d * 1.8, (2.8, 2.2, 2.2), emissive("fire", 20, 0.9))
        for a in range(5):
            r = up * np.cos(a * 1.26) + e * np.sin(a * 1.26)
            fx.cyl(mz + d * 0.6, mz + d * 3.2 + r * 2.0, 0.9, emissive("fire", 0, 0), r1=0.15, seg=6)
        for i in range(6):                                                    # a stream of tracers
            p = mz + d * (6.0 + i * 4.2) + up * (0.6 if i % 2 else -0.6)
            fx.cyl(p, p + d * 2.4, 0.32, emissive("fire", 3, 0.6), seg=5)
    rnd = np.random.RandomState(13)
    for i in range(5):                                                        # spent cases tumbling out
        p = mg["c"] + e * (2.6 + i * 0.9) - up * (1.0 + i * 1.6) + d * rnd.uniform(-1.0, 1.0)
        fx.box(p, (0.8, 0.45, 0.45), BRASS, rot_z(rnd.uniform(0, 3)))
    puffs(fx, mz + d * 2.6 + up * 1.2, n=3, r=1.8, spread=2.4, ft=ft, seed=9)


COLOSSUS = dict(
    name="Отец колосса", role="лидер-титан · 7", k=3.2, paint=GUNMETAL, canvas=(110, 110, 48, 88),
    hip=20.0, hz=7.4, hipx=(0.4, -0.8), LT=10.0, LS=7.8, LU=10.4, LF=11.0, th_leg=1.4, th_arm=1.55,
    sh=COL_SH, torso=col_torso, item_n=shock_mace, item_f=minigun, fx=col_fx,
    hit=lambda info: info["n"]["head"] * arr((1, 0, 1)),
    allow=[("hand_n", "item_n"), ("hand_f", "item_f")],
    broken=dict(hand_f=(3.6, -19.4, -4.0)),       # the far arm hangs clear of the pauldron
    poses=dict(
        idle=dict(lean=-0.06, t=(0.0, 0.0, 0.0), ank=((3.6, 3.6, 9.4), (-5.0, 3.6, -9.4)),
                  hand_n=(9.0, -4.0, 9.0), pole_n=(-1.0, -0.1, 0.5), mace_dir=(-0.2, 1.0, 0.3), ram_n="back",
                  hand_f=(10.0, -11.0, -1.0), pole_f=(-0.8, -0.4, -0.6), ram_f="back"),
        attack=dict(lean=-0.2, twist=-0.12, t=(1.4, -1.8, 0.0), ank=((5.5, 3.6, 9.6), (-6.5, 3.6, -9.4)),
                    hand_n=(15.0, -9.0, -2.0), pole_n=(0.0, -1.0, 0.8), mace_dir=(0.6, -0.8, 0.0), ram_n="front",
                    hand_f=(11.0, -8.0, -1.0), pole_f=(-0.8, -0.4, -0.6), ram_f="back", spin=0.5, fx=True),
    ),
)


def colossus_check(pose):
    return check(COLOSSUS, pose)


def colossus_build(pose="idle", k=3.2):
    return build(COLOSSUS, pose, k)


# ---------------------------------------------------------------- Маньяк: a madman in a scrap-built exosuit
from leaders import human, HAIR, SKIN, LEATHER, CLOTH_RED
from maniac import MAD, MADG
RUST_P = ramp("#1e0c06", "#3e1a0c", "#62301a", "#8a4c2a", "#b47448")
PATCH_G = ramp("#0e160c", "#1e2e18", "#324a26", "#4e6a38", "#7a9456")
PATCH_B = ramp("#0e1218", "#1e2630", "#323e4a", "#4e5e6e", "#7a8a9a")
BRASS_P = ramp("#1a1006", "#3a2410", "#5e4018", "#8a6428", "#bc9244")
SAW = Mat(ramp("#2a2c34", "#50545e", "#868a94", "#bcc0c8", "#eef0f4"))
MAN_CORE = Core(17.0, ((5.6, 7.8), (6.2, 8.6)), (0.0, 26.0, (6.4, 7.0), (8.4, 13.6), 7.4), ring_r=2.6)


def mad_specks(m, c, n=6, r=4.0, seed=0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        d = rng.normal(size=3)
        d /= np.linalg.norm(d)
        m.ell(arr(c) + d * r * rng.uniform(0.7, 1.2), (0.45, 0.45, 0.45), MAD if i % 2 else MADG)


def man_torso(G, P, S):
    C = MAN_CORE
    C.build(G, P, grate=False, fins=0, gauge=False, chest=False)
    ch = G["chest"]
    y0, y1 = C.cy - C.h / 2, C.cy + C.h / 2
    # an open cockpit cage: a floor, a seat back, bent bars, a waist-high front plate patched together
    tbox(ch, (0.0, y0 + 0.6, 0), (7.0, 8.0), (7.4, 9.0), 1.2, M_DIRON)
    ch.box((-3.2, C.cy + 0.4, 0), (1.2, 7.4, 7.0), M_IRON)                                   # seat back
    for (x, z) in ((3.4, 5.6), (3.4, -5.6), (-3.6, 6.2), (-3.6, -6.2)):
        ch.cyl((x, y0 + 0.8, z), (x * 0.9, y1 + 0.8, z * 1.15), 0.6, M_DIRON, seg=6)
    ch.cyl((3.2, y1 + 0.8, -6.6), (3.2, y1 + 0.8, 6.6), 0.6, M_DIRON, seg=6)
    ch.cyl((-3.4, y1 + 0.8, -7.2), (-3.4, y1 + 0.8, 7.2), 0.6, M_DIRON, seg=6)
    tbox(ch, (3.9, y0 + 2.6, 0), (0.9, 9.0), (0.9, 10.0), 3.4, Mat(PATCH_B), rot_z(-0.1))     # front plate
    ch.box((4.3, y0 + 2.4, -2.6), (0.3, 1.6, 2.6), Mat(BRASS_P))                             # a brass patch
    rivets(ch, [(4.45, y0 + 1.6 + 1.2 * i, z) for i in range(2) for z in (-3.6, 3.6)], r=0.3)
    for z, mat in ((6.4, Mat(PATCH_G)), (-6.4, P)):                                           # odd side plates
        ch.box((0.0, y0 + 3.0, z), (6.0, 4.0, 0.6), mat)
    for i, z in enumerate((-1.6, 0.6)):                                                       # dials on the dash
        g = arr((3.6, y0 + 4.9, z))
        ch.cyl(g, g + (0.5, 0.3, 0), 0.7, M_STEEL, seg=8)
        ch.ell(g + (0.55, 0.32, 0), (0.15, 0.55, 0.55), MAD if i else MADG)
    # the madman himself, goggled, wild-haired, mouth open, hands on the levers
    hd = G["head"]
    pilot = Model()
    human(pilot, (0, 0, 0), CLOTH_RED, "idle", goggles=True, apron=True)
    hd.extend(pilot.scaled(1.8).transformed(I3, (-0.8, y0 + 0.4, 0)))
    hc = arr((-0.44, y0 + 0.4 + 10.0 * 1.8, 0))
    for d in ((-0.8, 1.4, 1.2), (-1.2, 1.6, -1.0), (-1.8, 0.9, 0.2), (-0.2, 2.0, 0.0)):        # hair standing on end
        spike(hd, hc + arr(d) * 0.6, hc + arr(d) * 1.9, 0.5, HAIR)
    hd.box(hc + (2.25, -0.8, 0), (0.25, 0.8, 1.0), M_HOLE)                                    # the open mouth
    for z in (-1.4, 1.4):
        hd.cyl((3.4, y0 + 3.8, z), (2.0, y0 + 6.6, z * 1.2), 0.25, M_STEEL, seg=4)            # levers
        hd.ell((2.0, y0 + 6.8, z * 1.2), (0.45, 0.45, 0.45), Mat(BRASS_P))
    # on the back: a Tesla coil spitting sparks and a bent smokestack
    bk = G["back"]
    cb = arr((-5.4, y1 - 1.6, 2.4))
    bk.cyl(cb, cb + (0, 9.0, 0), 1.3, M_DIRON, seg=10)
    for i in range(7):
        bk.cyl(cb + (0, 1.0 + i * 1.1, 0), cb + (0, 1.5 + i * 1.1, 0), 1.75, Mat(BRASS_P), seg=10)
    bk.ell(cb + (0, 10.4, 0), (2.0, 2.0, 2.0), M_STEEL)
    mad_specks(bk, cb + (0, 10.4, 0), n=6, r=3.0, seed=2)
    s0 = arr((-5.2, y1 - 2.0, -3.0))
    s1 = s0 + (-0.8, 5.0, -0.6)
    s2 = s1 + (-3.2, 3.4, -1.2)
    bk.cyl(s0, s1, 1.1, M_IRON, seg=8)
    bk.cyl(s1, s2, 1.0, M_RUST, seg=8)
    bk.cyl(s2, s2 + unit(s2 - s1) * 0.8, 1.5, M_DIRON, seg=8)
    for i, d in enumerate(((-1.4, 1.6, 0.0), (-3.2, 3.6, 0.6))):
        bk.ell(s2 + arr(d), (1.5 + i * 0.8, 1.2 + i * 0.6, 1.4 + i * 0.7), M_PUFF)
    bk.box((-6.2, C.cy - 1.0, 0), (3.0, 6.0, 8.6), Mat(RUST_P))                               # the generator box
    pauldron(G, "pauldron_n", S["sh"] + (0, 1.2, 0), 1, Mat(PATCH_G), r=(4.0, 2.6, 3.4), layers=2)
    pauldron(G, "pauldron_f", S["sh"] * arr((1, 1, -1)) + (0, 1.0, 0), -1, Mat(RUST_P), r=(3.2, 2.2, 2.8), layers=1, spikes=2)


def buzzsaw(G, side, sh, el, w, s, P, A, S):
    """The forearm ends in a circular saw: an axle, a guard over its upper half, a toothed blade."""
    g = G["item_" + side]
    d = unit(w - el)
    G["hand_" + side].ell(w + d * 0.3, (1.9, 1.9, 1.9), M_DIRON)
    hub = w + d * 3.6
    ax = arr((0, 0, 1.0))
    g.box(w + d * 1.6, (2.6, 2.6, 2.6), Mat(BRASS_P), np.column_stack([d, unit(np.cross(ax, d)), ax]))   # motor
    g.cyl(hub - ax * 1.6, hub + ax * 1.6, 0.8, M_DIRON, seg=8)
    g.cyl(hub - ax * 0.25, hub + ax * 0.25, 4.6, SAW, seg=20)                                # the blade
    for i in range(16):                                                                     # teeth
        a = 2 * np.pi * i / 16 + A.get("spin", 0.0)
        g.box(hub + arr((np.cos(a), np.sin(a), 0)) * 4.9, (0.8, 0.5, 0.4), SAW, rot_z(a + 0.5))
    g.ell(hub + ax * 0.35, (1.0, 1.0, 0.2), M_IRON)
    up = unit(-d + arr((0, 1.0, 0)))
    for i in range(5):                                                                      # a guard over the top
        a = -1.2 + i * 0.55
        dir_ = unit(up * np.cos(a) + unit(np.cross(ax, up)) * np.sin(a))
        g.box(hub + dir_ * 5.3 + ax * 0.9, (1.8, 0.4, 0.4), Mat(PATCH_B), np.column_stack([unit(np.cross(ax, dir_)), dir_, ax]))
    return dict(hub=hub, edge=hub + unit(arr((1.0, -1.0, 0))) * 4.8)


def drill(G, side, sh, el, w, s, P, A, S):
    g = G["item_" + side]
    d = unit(w - el)
    G["hand_" + side].ell(w + d * 0.3, (1.8, 1.8, 1.8), M_DIRON)
    R, _ = basis(w, w + d)
    g.box(w + d * 2.0, (3.2, 3.6, 3.2), Mat(PATCH_G), R)                                    # motor housing
    g.cyl(w + d * 3.8, w + d * 4.6, 1.8, M_STEEL, seg=10)
    tip = w + d * 11.0
    g.cyl(w + d * 4.6, tip, 1.5, M_STEEL, r1=0.15, seg=10)                                 # the bit
    for t in np.linspace(5.2, 9.8, 6):                                                      # spiral flutes
        g.cyl(w + d * t, w + d * (t + 0.35), 1.65 - (t - 4.6) * 0.21, M_DIRON, seg=10)
    return dict(tip=tip)


def man_fx(fx, A, info, S, ft):
    hub = info["n"]["hub"]
    contact = hub + arr((3.6, -3.4, 0.0))
    near = ft < 0.5
    if near:
        fx.ell(contact, (1.4, 1.4, 1.4), emissive("fire", 18, 0.9))
    rnd = np.random.RandomState(9)
    for i in range(12):                                   # sparks flung off the blade
        dd = unit(arr((rnd.uniform(-0.2, 1.0), rnd.uniform(0.0, 1.2), rnd.uniform(-1, 1))))
        p = contact + dd * rnd.uniform(1.0, 4.0) * (1 + ft)
        fx.cyl(p, p + dd * 1.6, 0.2, emissive("fire", 0, 0), seg=4)
    mad_specks(fx, contact, n=6, r=3.4 + 2 * ft, seed=4)
    mad_specks(fx, info["X"]((-5.4, 40.0, 2.4)), n=8, r=4.4, seed=6)                       # the coil goes wild
    puffs(fx, contact + arr((0, 1.5, 0)), n=2, r=1.6, spread=2.0, ft=ft, seed=7)


MANIAC = dict(
    name="Маньяк", role="лидер · 4", k=1.3, paint=RUST_P,
    paints=dict(leg_n=Mat(RUST_P), leg_f=Mat(PATCH_G), arm_n=Mat(PATCH_B), arm_f=Mat(RUST_P)),
    hip=17.0, hz=4.0, hipx=(0.4, -0.6), LT=8.4, LS=6.8, LU=7.4, LF=7.8, th_leg=0.95, th_arm=0.95,
    sh=arr((-0.4, 30.0, 7.8)), torso=man_torso, item_n=buzzsaw, item_f=drill, fx=man_fx,
    hit=lambda info: (info["n"]["hub"] + arr((4.0, -4.0, 0.0))) * arr((1, 0, 1)),
    allow=[("arm_n", "item_n"), ("arm_f", "item_f"), ("hand_n", "item_n"), ("hand_f", "item_f")],
    poses=dict(
        idle=dict(lean=-0.08, t=(0.0, 0.0, 0.0), ank=((2.6, 3.6, 4.8), (-3.4, 3.6, -4.8)),
                  hand_n=(7.0, -6.0, 2.6), pole_n=(-0.6, -0.6, 1.0),
                  hand_f=(7.4, -9.0, -2.0), pole_f=(-0.6, -0.4, -1.0)),
        attack=dict(lean=-0.3, twist=-0.15, t=(1.0, -1.4, 0.0), ank=((5.0, 3.6, 5.0), (-4.6, 3.6, -4.8)),
                    hand_n=(12.0, -9.0, 0.6), pole_n=(-0.4, -0.8, 1.0), spin=0.2,
                    hand_f=(9.0, -4.0, -2.6), pole_f=(-0.6, -0.6, -1.0), fx=True),
    ),
)


ROSTER = [MOLOT, GORN, ORUDIE, MEH, MASON, COLOSSUS, MANIAC]
for _S in ROSTER:
    _S["poses"]["broken"] = dict(broken_pose(_S), **_S.get("broken", {}))
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
    # a close-up sheet of every Foundry creature: idle above, attack below
    S2 = 2
    cols = [("Страж", "танк · 6", lambda p: H.build(p, 2.5)),
            ("Молот", "разрушитель · 5", lambda p: build(MOLOT, p, 2.9)),
            ("Горн", "контроль · 5", lambda p: build(GORN, p, 2.7)),
            ("Орудие", "стрелок · 5", lambda p: build(ORUDIE, p, 2.6)),
            ("Механик", "поддержка · 4", lambda p: build(MEH, p, 2.7)),
            ("Каменщик", "призыв Зодчего · 2", lambda p: build(MASON, p, 3.4)),
            ("Отец колосса", "лидер-титан · 7", lambda p: build(COLOSSUS, p, 2.3)),
            ("Маньяк", "лидер · 4", lambda p: build(MANIAC, p, 3.0))]
    CW, WW, HH = 172, 172 * 8, 640
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
            by = 282 + j * 300
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
        d.text((cx - d.textlength(name, font=fh) / 2, 298 * S2), name, font=fh, fill=(226, 186, 106))
        d.text((cx - d.textlength(role, font=fr) / 2, 298 * S2 + 28), role, font=fr, fill=(190, 182, 164))
    img.save(out("foundry_humanoid.png"))
    print(img.size)
