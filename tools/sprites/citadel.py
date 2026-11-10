"""Цитадель — the Architect's late development: a big golem that deploys into a fortress where other golems stand.

Marching, it is a walking keep: a body of laid stone (I — a timber frame, III — iron plate) with battlements, arrow
slits and a shut gate in its breast; a watchtower for a head with a lit slit and a banner; round turrets for
shoulders, the arms hanging from them with fists like rams; legs like pillars; and folded on its back, the curtain
walls it carries. Deployed, it sits down on its footing, the shoulder turrets run down to the ground and flank the
keep, the watchtower rises, the arms plant themselves in front as buttresses, the walls unfold to both sides with
towers at their ends — and golems stand on its roof and towers. Levels I–III as for every building: logs, stone, iron.

    python3 tools/sprites/citadel.py           -> out/citadel.png (the sheet)
    python3 tools/sprites/citadel.py check     -> out/citadel_check.png and the clipping report
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_y, I3
from golem6 import M_IRON, M_DIRON, M_HOLE, M_RUST, emissive, spike, tbox, STYLE1
import golems_h as GH
import buildings as BD
from golems_h import arr, unit, rivets, ik, Parts, arm
from clipcheck import report

W, D = 46.0, 50.0                       # the keep: x — front to back, z — side to side
TR, TZ = 7.5, 30.5                      # the shoulder turrets: radius, offset to the side
P_CIT = {1: ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844"),      # its arms take the level's material:
         2: ramp("#1c1a20", "#34303a", "#4e4a56", "#6e6a76", "#96929e"),      # timber, stone, iron plate
         3: ramp("#121418", "#22262e", "#363c46", "#525a66", "#7a8290")}
BANNER = Mat(ramp("#2a1a06", "#5a3a0e", "#9a6a1a", "#d8a030", "#f6d070"))
EYE = emissive("fire", 6, 0.6)
K = 1.6                                 # its battle scale: the same as the golems standing on it
STONE_D = Mat(ramp("#1e1c24", "#36323e", "#524e5c", "#76727e", "#9e9aa6"))


def roof(g, c, R, h, t):
    M = BD.tier_mats(t)
    g.cyl(c, c + (0, h, 0), R, M["frame"] if t > 1 else BD.LOG_END, r1=0.35, seg=12)


def keep(G, y0, H, t, gate=True):
    """The block of the keep: masonry (I — logs on a frame, III — riveted plate), slits, the gate, battlements.
    Returns the height of its roof."""
    g = G["chest"]
    M = BD.tier_mats(t)
    if t == 1:
        g.box((0, y0 + H / 2, 0), (W - 1.0, H, D - 1.0), M_RUST)
        n = int(H // 2.3)
        for i in range(n):                                                        # logs laid on their side
            y = y0 + 1.15 + i * 2.3
            g.cyl((W / 2 - 0.6, y, -D / 2), (W / 2 - 0.6, y, D / 2), 1.15, BD.LOG, seg=7)
            g.cyl((-W / 2, y, D / 2 - 0.6), (W / 2, y, D / 2 - 0.6), 1.15, BD.LOG, seg=7)
        for x, z in ((W / 2, D / 2), (W / 2, -D / 2), (-W / 2, D / 2), (0.0, D / 2), (W / 2, 0.0)):
            g.cyl((x, y0, z), (x, y0 + H + 0.6, z), 1.3, BD.LOG_END, seg=7)            # corner posts
        for y in (y0 + H * 0.3, y0 + H * 0.72):
            g.box((W / 2 + 0.6, y, 0), (0.5, 0.9, D), BD.ROPE)
            g.box((0, y, D / 2 + 0.6), (W, 0.9, 0.5), BD.ROPE)
    elif t == 2:
        face_stones(g, y0, H)
    else:
        g.box((0, y0 + H / 2, 0), (W, H, D), BD.PLATE)
        for z in np.arange(-D / 2 + 3.0, D / 2 - 1.0, 6.0):
            g.box((W / 2 + 0.15, y0 + H / 2, z), (0.3, H - 1.0, 0.7), M_DIRON)
            rivets(g, [(W / 2 + 0.35, y0 + yy, z) for yy in (2.5, H / 2, H - 2.5)], r=0.35)
        for x in np.arange(-W / 2 + 3.0, W / 2 - 1.0, 6.0):
            g.box((x, y0 + H / 2, D / 2 + 0.15), (0.7, H - 1.0, 0.3), M_DIRON)
            rivets(g, [(x, y0 + yy, D / 2 + 0.35) for yy in (2.5, H / 2, H - 2.5)], r=0.35)
        g.box((W / 2 + 0.2, y0 + H * 0.62, 0), (0.25, 0.6, D - 2.0), BD.RUNE)
        g.box((0, y0 + H * 0.62, D / 2 + 0.2), (W - 2.0, 0.6, 0.25), BD.RUNE)
    top = y0 + H
    g.box((0, top + 0.4, 0), (W + 1.0, 0.8, D + 1.0), M["trim"])
    cap = BD.STONE if t == 2 else M["cap"]
    for x in np.arange(-W / 2 + 1.2, W / 2, 3.6):                                   # battlements
        for z in (-D / 2 + 0.7, D / 2 - 0.7):
            g.box((x, top + 1.9, z), (2.0, 2.2, 1.4), cap)
    for z in np.arange(-D / 2 + 4.8, D / 2 - 2.0, 3.6):
        for x in (-W / 2 + 0.7, W / 2 - 0.7):
            g.box((x, top + 1.9, z), (1.4, 2.2, 2.0), cap)
    for y in (y0 + H * 0.52, y0 + H * 0.82):                                        # arrow slits
        for z in (-15.0, -5.0, 5.0, 15.0):
            g.box((W / 2 + 0.6, y, z), (0.3, 4.0, 1.0), M_HOLE)
        for x in (-14.0, -4.0, 6.0, 15.0):
            g.box((x, y, D / 2 + 0.6), (1.0, 4.0, 0.3), M_HOLE)
    if gate:                                                    # the gate in its breast: an arch and a portcullis
        gh = min(15.0, H * 0.36)
        g.box((W / 2 + 0.55, y0 + gh / 2 + 0.2, 0), (0.3, gh, 11.0), M_HOLE)
        g.cyl((W / 2 + 0.55, y0 + gh + 0.3, -5.5), (W / 2 + 0.55, y0 + gh + 0.3, 5.5), 1.4, M["frame"], seg=6)
        for z in (-4.2, -2.1, 0.0, 2.1, 4.2):
            g.cyl((W / 2 + 0.9, y0 + 0.4, z), (W / 2 + 0.9, y0 + gh, z), 0.4, M_IRON, seg=4)
        for y in (y0 + gh * 0.3, y0 + gh * 0.6, y0 + gh * 0.88):
            g.cyl((W / 2 + 0.9, y, -5.0), (W / 2 + 0.9, y, 5.0), 0.4, M_IRON, seg=4)
    return top


def face_stones(g, y0, H, course=2.9, L=4.8):
    """Laid stone on the faces we see (+x the front, +z the side): offset courses of blocks, every few a darker one,
    mortar showing between them."""
    g.box((0, y0 + H / 2, 0), (W - 0.6, H, D - 0.6), BD.MORTAR)
    n = max(1, int(round(H / course)))
    ch = H / n
    rng = np.random.default_rng(7)
    for r in range(n):
        y = y0 + ch * (r + 0.5)
        for along, span in (("z", D), ("x", W)):
            a = -span / 2 - (L / 2 if r % 2 else 0.0)
            while a < span / 2 - 0.3:
                a0, a1 = max(a, -span / 2), min(a + L, span / 2)
                if a1 - a0 > 0.8:
                    m = STONE_D if rng.random() < 0.22 else BD.STONE
                    c = (a0 + a1) / 2
                    if along == "z":
                        tbox(g, (W / 2 - 0.7, y, c), (1.4, a1 - a0 - 0.3), (1.2, a1 - a0 - 0.45), ch - 0.32, m)
                    else:
                        tbox(g, (c, y, D / 2 - 0.7), (a1 - a0 - 0.3, 1.4), (a1 - a0 - 0.45, 1.2), ch - 0.32, m)
                a += L


def column(g, c, R, y0, h, t):
    """A pillar of the leg: I — a bundle of logs with rope bands, II — stone drums, III — iron plate with spikes."""
    c = arr(c)
    if t == 1:
        n = int(2 * np.pi * R / 2.0)
        for i in range(n):
            a = 2 * np.pi * i / n
            p = c + (np.cos(a) * (R - 0.9), 0, np.sin(a) * (R - 0.9))
            g.cyl(p + (0, y0, 0), p + (0, y0 + h, 0), 1.05, BD.LOG, seg=6)
        g.cyl(c + (0, y0, 0), c + (0, y0 + h, 0), R - 1.2, M_DIRON, seg=12)
        for y in (y0 + h * 0.25, y0 + h * 0.75):
            g.cyl(c + (0, y, 0), c + (0, y + 0.8, 0), R + 0.25, BD.ROPE, seg=16)
    else:
        BD.drum(g, c, R, y0, h, t)


def rot_to(d):
    """The rotation taking +y to the direction d."""
    d, y = unit(d), arr((0.0, 1.0, 0.0))
    v, c = np.cross(y, d), float(y @ d)
    if np.linalg.norm(v) < 1e-9:
        return I3 if c > 0 else np.diag([1.0, -1.0, -1.0])
    V = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return I3 + V + V @ V / (1 + c)


def column_between(g, A, B, R, t):
    """A pillar from A to B at any slant: built upright, then turned into place."""
    A, B = arr(A), arr(B)
    tmp = Model()
    column(tmp, (0, 0, 0), R, 0.0, float(np.linalg.norm(B - A)), t)
    g.ops.extend(tmp.transformed(rot_to(B - A), A).ops)


def pillar_leg(t):
    """A leg like a tower's pillar: an iron foot-plinth with toes, a shin and a thigh of the level's material,
    an iron knee ring with a cap, a hip joint."""
    def fn(G, key, h, kn, an, s, P, th=1.0):
        g = G[key]
        h = arr(h)
        x0, z0 = h[0], h[2]
        if h[1] < HIP - 6.0:            # kneeling: the thigh down to a knee on the ground, the shin lying back
            kn, ft = arr((x0 + 9.0, 6.2, z0)), arr((x0 - 9.0, 6.2, z0))
            column_between(g, h, kn, 5.0, t)
            column_between(g, kn, ft, 5.6, t)
            g.ell(kn, (6.4, 6.4, 6.4), M_DIRON)
            g.ell(kn + (5.6, 0.6, 0), (2.2, 3.0, 3.4), P)
            g.box(ft + (-2.3, -0.2, 0), (4.6, 12.0, 12.0), M_IRON)                  # the foot upright, toes down
            for dz in (-3.6, 0.0, 3.6):
                g.box((ft[0] - 5.6, 1.6, z0 + dz), (3.2, 3.0, 3.0), M_DIRON)
            g.ell(h, (5.6, 4.6, 5.6), M_DIRON)
            return
        tbox(g, (x0 + 1.4, 2.3, z0), (15.0, 13.0), (12.0, 11.0), 4.6, M_IRON)
        for dz in (-3.6, 0.0, 3.6):
            g.box((x0 + 9.4, 1.6, z0 + dz), (3.2, 3.0, 3.0), M_DIRON)
        column(g, (x0, 0, z0), 5.6, 4.6, 13.6, t)
        g.cyl((x0, 18.2, z0), (x0, 21.2, z0), 6.6, M_DIRON, seg=16)
        g.ell((x0 + 6.0, 19.7, z0), (2.2, 3.0, 3.4), P)
        rivets(g, [(x0 + 8.1, 19.7, z0)], r=0.5)
        column(g, (x0, 0, z0), 5.0, 21.2, h[1] - 23.0, t)
        g.ell(h, (5.6, 4.6, 5.6), M_DIRON)
    return fn


def turret(g, c, y0, h, t):
    """A shoulder turret: a round tower body with a ring of crenels and a pointed roof."""
    BD.drum(g, c, TR, y0, h, t)
    M = BD.tier_mats(t)
    top = arr(c) + (0, y0 + h, 0)
    g.cyl(top, top + (0, 0.7, 0), TR + 0.6, M["trim"], seg=16)
    roof(g, top + (0, 0.7, 0), TR + 1.4, 9.0, t)


def watchtower(g, c, y0, h, t):
    """The head: a round tower with a lit slit looking forward, a roof and a banner."""
    c = arr(c)
    BD.drum(g, c, 7.0, y0, h, t)
    g.box(c + (7.1, y0 + h - 4.0, 0), (0.4, 1.4, 6.0), EYE)
    M = BD.tier_mats(t)
    g.cyl(c + (0, y0 + h, 0), c + (0, y0 + h + 0.8, 0), 7.8, M["trim"], seg=20)
    roof(g, c + (0, y0 + h + 0.8, 0), 8.6, 9.0, t)
    top = c + (0, y0 + h + 9.8, 0)
    g.cyl(top - (0, 0.5, 0), top + (0, 9.0, 0), 0.4, M_DIRON, seg=4)
    g.box(top + (-3.2, 7.0, 0), (6.2, 3.8, 0.3), BANNER)


# ---------------------------------------------------------------- marching: the walking keep
HIP = 36.0
KH = 44.0


def cit_torso(G, P, S):
    t = S["tier"]
    y0 = HIP + 1.0
    tbox(G["pelvis"], (0, HIP - 4.0, 0), (W - 12.0, D - 12.0), (W - 8.0, D - 8.0), 5.6, M_DIRON)  # the plinth on its hips
    top = keep(G, y0, KH, t)
    for s in (1, -1):
        turret(G["pauldron_" + ("n" if s > 0 else "f")], (0.0, 0, s * TZ), y0 + 14.0, KH - 11.0, t)
    watchtower(G["head"], (5.0, 0, 0), top, 12.0, t)
    # the curtain walls it carries, folded up on its back, on hinges
    b = G["back"]
    th = S.get("open", 0.0)
    if th:                  # unfolding: each half swings out on a hinge at its outer corner, like a door
        for s in (1, -1):
            tmp = Model()
            L = D / 2 - 1.8
            BD.wall_run(tmp, -1.7, min(0.0, -s * L), max(0.0, -s * L), y0 + 6.0, KH + 9.0, t, depth=3.4, face=-1)
            hinge = arr((-W / 2 - 0.9, 0.0, s * (D / 2 - 1.0)))
            b.ops.extend(tmp.transformed(rot_y(-s * th), hinge).ops)
            b.cyl(hinge + (0, y0 + 5.0, 0), hinge + (0, y0 + KH + 15.5, 0), 1.0, M_DIRON, seg=8)
        return
    for z0, z1 in ((-D / 2 + 1.0, -0.8), (0.8, D / 2 - 1.0)):
        BD.wall_run(b, -W / 2 - 2.6, z0, z1, y0 + 6.0, KH + 9.0, t, depth=3.4, face=-1)
    for y in (y0 + 10.0, y0 + KH - 3.0):
        b.cyl((-W / 2 - 0.9, y, -D / 2 + 2.0), (-W / 2 - 0.9, y, D / 2 - 2.0), 0.9, M_DIRON, seg=6)


def cit_fist(G, side, sh, el, w, s, P, A, S):
    """A fist like a ram: a heavy round of iron with knuckle blocks; spikes at III."""
    d = unit(w - el)
    g = G["hand_" + side]
    c = w + d * 4.2
    g.ell(c, (7.0, 6.6, 6.6), M_DIRON)
    for k in range(4):
        g.box(c + d * 4.6 + arr((0, 0, (k - 1.5) * 3.0)), (3.4, 2.8, 2.6), M_IRON)
    if S.get("tier", 2) == 3:
        for k in range(4):
            q = c + d * 5.8 + arr((0, 0, (k - 1.5) * 3.0))
            spike(g, q, q + d * 3.6, 0.9, M_IRON)
    return dict(w=w, el=el)


CITADEL = dict(
    name="Цитадель", role="развитие Зодчего", k=K, paint=P_CIT[2],
    hip=HIP, hz=13.0, hipx=(0.8, -0.8), LT=18.5, LS=18.5, LU=17.0, LF=17.0, th_leg=3.2, th_arm=2.8, cuff=True,
    sh=arr((0.0, HIP + 15.0, TZ)), torso=cit_torso, item_n=cit_fist, item_f=cit_fist, fx=lambda *a: None,
    allow=[("hand_n", "arm_n"), ("hand_f", "arm_f"), ("chest", "leg_n"), ("chest", "leg_f"), ("back", "pelvis"),
           ("pauldron_n", "arm_n"), ("pauldron_f", "arm_f"), ("chest", "pelvis"), ("head", "chest")],
    poses=dict(idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((0.8, 3.6, 13.0), (-0.8, 3.6, -13.0)),
                         hand_n=(5.0, -31.0, 4.0), pole_n=(-0.6, 0.0, 1.0),
                         hand_f=(3.0, -31.0, -4.0), pole_f=(-0.6, 0.0, -1.0)),
               unfold=dict(lean=0.0, t=(0.0, -14.0, 0.0), ank=((0.8, 3.6, 13.0), (-0.8, 3.6, -13.0)),
                           hand_n=(17.0, -26.0, 4.0), pole_n=(-0.6, 0.4, 1.0),
                           hand_f=(17.0, -26.0, -4.0), pole_f=(-0.6, 0.4, -1.0))),
)


def marching(t=2):
    S = dict(CITADEL, tier=t, leg_fn=pillar_leg(t), paint=P_CIT[t])
    G, _ = GH.creature_parts(S, S["poses"]["idle"], fx=False)
    return G, GH.BASE_ALLOWED + S["allow"]


def unfolding(t=2):
    """Halfway: it kneels, the fists go down to the ground in front, the walls on its back swing open."""
    S = dict(CITADEL, tier=t, leg_fn=pillar_leg(t), paint=P_CIT[t], open=1.05)
    G, _ = GH.creature_parts(S, S["poses"]["unfold"], fx=False)
    return G, GH.BASE_ALLOWED + S["allow"] + [("back", "pauldron_n"), ("back", "pauldron_f"), ("back", "chest")]


# ---------------------------------------------------------------- deployed: the fortress, golems on it
DH = 44.0                   # the keep sits lower: its legs folded under the footing
WALL_X, WALL_H, WALL_D = -12.0, 32.0, 8.0
END_Z, END_R, END_H = 80.0, 13.0, 40.0
BATTLE = {"Страж": 2.2, "Мудрец": 1.6, "Горн": 1.6, "Орудие": 1.6, "Механик": 1.15}
GARRISON = (("Орудие", (6.0, None, 2.0)), ("Мудрец", (WALL_X, END_H, END_Z)))


def garrison(G, allow, frame, at, name=None):
    """A golem in its own idle pose standing at `at` (its parts copied in under a prefix)."""
    S = GH.BY_NAME[frame]
    Gg, _ = GH.creature_parts(S, S["poses"]["idle"], fx=False)
    pre = (name or frame) + ":"
    f = BATTLE[frame] / K                       # its own battle scale, against the Citadel's
    for k, m in Gg.items():
        if k != "fx":
            G[pre + k] = m.scaled(f).transformed(I3, at)
    allow += [(pre + a, pre + b) for a, b in GH.BASE_ALLOWED + S.get("allow", [])]
    return pre


def deployed(t=2, men=True):
    G = Parts()
    P = Mat(P_CIT[t])
    M = BD.tier_mats(t)
    base = BD.STONE if t == 2 else (BD.LOG if t == 1 else BD.PLATE)
    tbox(G["pelvis"], (0, 3.0, 0), (W + 10.0, D + 10.0), (W + 6.0, D + 6.0), 6.0, base)    # the footing it sits on
    for z in (-13.0, 13.0):                                                                 # its knees, folded under
        G["pelvis"].ell((W / 2 + 4.6, 4.2, z), (5.4, 4.0, 5.0), M_DIRON)
    top = keep(G, 6.0, DH, t)
    for s in (1, -1):                                       # the shoulder turrets run down to the ground
        turret(G["pauldron_" + ("n" if s > 0 else "f")], (0.0, 0, s * TZ), 0.0, DH + 10.0, t)
    watchtower(G["head"], (-11.0, 0, 0), top, 20.0, t)                         # the head rises higher
    allow = [("head", "chest"), ("chest", "pelvis"), ("pauldron_n", "chest"), ("pauldron_f", "chest"),
             ("pauldron_n", "pelvis"), ("pauldron_f", "pelvis")]
    for side, s in (("n", 1), ("f", -1)):                   # the arms planted in front as buttresses
        sh = arr((5.0, 34.0, s * (TZ + 5.0)))
        fist_at = arr((25.0, 7.0, s * (TZ + 8.0)))
        el, w = ik(sh, fist_at, 17.0, 17.0, (0.0, 1.0, s * 0.6))
        arm(G, "arm_" + side, sh, el, w, s, P, th=2.8)
        cit_fist(G, side, sh, el, w, s, P, {}, dict(tier=t))
        allow += [("arm_" + side, "hand_" + side), ("arm_" + side + ".ball", "pauldron_" + side),
                  ("arm_" + side, "pauldron_" + side), ("arm_" + side + ".ball", "chest"), ("arm_" + side, "arm_" + side + ".ball"),
                  ("arm_" + side, "arm_" + side + ".ram"), ("arm_" + side + ".ram", "arm_" + side + ".ball")]
    b = G["walls"]                                          # the curtain walls unfolded, towers at their ends
    for s in (1, -1):
        z0, z1 = sorted((s * (TZ + TR - 0.5), s * (END_Z - END_R + 0.5)))
        BD.wall_run(b, WALL_X, z0, z1, 0.0, WALL_H, t, depth=WALL_D)
        c = arr((WALL_X, 0, s * END_Z))
        BD.drum(b, c, END_R, 0.0, END_H, t)
        b.cyl(c + (0, END_H, 0), c + (0, END_H + 0.8, 0), END_R + 0.6, M["trim"], seg=24)
        for a in np.linspace(0, 2 * np.pi, 17)[:-1]:
            b.box(c + arr((np.cos(a) * (END_R - 0.2), END_H + 2.0, np.sin(a) * (END_R - 0.2))), (2.0, 2.4, 2.0),
                  BD.STONE if t == 2 else M["cap"])
    allow += [("walls", "pauldron_n"), ("walls", "pauldron_f")]
    if men:
        for frame, (x, y, z) in GARRISON:
            pre = garrison(G, allow, frame, (x, (top + 0.9) if y is None else y + 0.9, z))
            on = "chest" if y is None else "walls"
            allow += [(pre + k, on) for k in ("leg_n", "leg_f", "leg_n.ram", "leg_f.ram")]
    return G, allow


def render_parts(G, k=K, canvas=(330, 260, 165, 200)):
    cw, ch, cx, cy = canvas
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def build(form="marching", t=2, k=K, men=True):
    G, _ = {"marching": lambda: marching(t), "unfolding": lambda: unfolding(t), "deployed": lambda: deployed(t, men)}[form]()
    return render_parts(G, k)


def check(G, allow):
    return report(G, allow, skip=("fx",))


def sheet():
    """Level II: marching, unfolding, deployed with a garrison; below, levels I and III marching and deployed."""
    from leaders_sheet import canvas, put, fonts, S as SS, GOLD, INK, MUT
    from paths import out
    WW = 960
    rows = [(2, ("marching", "unfolding", "deployed"), ("в походе", "садится, стены расходятся",
                                                       "развёрнута: Орудие на крыше донжона, Мудрец на угловой башне")),
            (1, ("marching", "deployed"), ("I · в походе", "I · развёрнута")),
            (3, ("marching", "deployed"), ("III · в походе", "III · развёрнута"))]
    sprites = {}
    for t, forms, _ in rows:
        for f in forms:
            spr = build(f, t)
            a = spr.image(1).getbbox()
            sprites[(t, f)] = (spr, a[0] - spr.ox, a[2] - spr.ox, spr.oy - a[1], a[3] - spr.oy)  # left, right; up, down
    Y0 = 70
    H1 = max(sprites[(2, f)][3] for f in rows[0][1]) + 12
    H2 = max(sprites[(t, f)][3] for t in (1, 3) for f in ("marching", "deployed")) + 12
    labels = []

    lows = [sprites[k][4] for k in sprites]
    HH = Y0 + H1 + max(lows) + 6 + 56 + H2 + max(lows) + 6 + 30
    sc = canvas(WW, int(HH), 61)

    def lay(items, x0, x1, by):
        widths = [sprites[k][2] - sprites[k][1] for k in items]
        gap = (x1 - x0 - sum(widths)) / (len(items) + 1)
        x = x0 + gap
        for k, w in zip(items, widths):
            spr, l, r, h, lo = sprites[k]
            cx = x - l
            put(sc, spr, cx, by, (r - l) * 0.42)
            yield k, x + w / 2
            x += w + gap

    low = lambda ks: max(sprites[k][4] for k in ks) + 6           # how far the row reaches below its ground line
    by1 = Y0 + H1
    ks1 = [(2, f) for f in rows[0][1]]
    for (k, xc), cap in zip(lay(ks1, 0, WW, by1), rows[0][2]):
        labels.append((xc, by1 + low(ks1), cap))
    by2 = by1 + low(ks1) + 56 + H2
    ks2 = [(t, f) for t, forms, _ in rows[1:] for f in forms]
    for half, (t, forms, caps) in enumerate(rows[1:]):
        for (k, xc), cap in zip(lay([(t, f) for f in forms], half * WW / 2, (half + 1) * WW / 2, by2), caps):
            labels.append((xc, by2 + low(ks2), cap))
    img = sc.image(SS)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Цитадель: крепость, которая ходит", font=ft, fill=INK)
    d.text((24, 60), "Развитие Зодчего. В походе — голем-донжон: башня-голова, башни-плечи, ноги-столпы, стены сложены "
                     "за спиной. На месте садится,", font=fr, fill=MUT)
    d.text((24, 84), "плечевые башни уходят в землю, руки становятся контрфорсами, стены расходятся к угловым башням — "
                     "и на ней стоят големы. Масштаб настоящий.", font=fr, fill=MUT)
    for x, y, cap in labels:
        d.text((x * SS - d.textlength(cap, font=fr) / 2, y * SS), cap, font=fr, fill=INK)
    d.text((24, (by1 + low(ks1) + 26) * SS), "Уровни: I — брёвна и верёвка, III — клёпаное железо, шипы и руны", font=fh, fill=GOLD)
    img.save(out("citadel.png"))
    print("citadel.png", img.size)


if __name__ == "__main__":
    import sys
    if "check" not in sys.argv[1:]:
        sheet()
        raise SystemExit
    from PIL import Image
    from paths import out
    ims = []
    for name, (G, allow) in (("marching", marching(2)), ("unfolding", unfolding(2)), ("II", deployed(2))):
        print(name, check(G, allow)[:8])
        im = render_parts(G).image(1)
        bb = im.getbbox()
        ims.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
    Wd = sum(i.width + 12 for i in ims)
    Hd = max(i.height for i in ims)
    sheet = Image.new("RGBA", (Wd, Hd), (52, 46, 58, 255))
    x = 0
    for i in ims:
        sheet.alpha_composite(i, (x, Hd - i.height))
        x += i.width + 12
    sheet.save(out("citadel_check.png"))
