"""Golem with swappable arms, hand tools and legs (style 1). Every module has levels I-III."""
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
import golem6 as G6
from golem6 import M_IRON, M_DIRON, M_BRONZE, M_HOLE, M_SMOKE, emissive, spike, pivot, STYLE1


def tbox(m, c, bot, top, h, mat, R=I3):
    bx, bz, tx, tz = bot[0] / 2, bot[1] / 2, top[0] / 2, top[1] / 2
    v = [(-bx, -h / 2, -bz), (bx, -h / 2, -bz), (bx, -h / 2, bz), (-bx, -h / 2, bz),
         (-tx, h / 2, -tz), (tx, h / 2, -tz), (tx, h / 2, tz), (-tx, h / 2, tz)]
    c = np.array(c, float)
    m.solid([c + R @ np.array(p) for p in v], [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], mat)


def seg_box(m, a, b, wa, wb, mat):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    L = np.linalg.norm(d)
    y = d / L
    x = np.cross(y, [0, 0, 1.0])
    if np.linalg.norm(x) < 1e-6:
        x = np.array([1.0, 0, 0])
    x /= np.linalg.norm(x)
    z = np.cross(x, y)
    tbox(m, (a + b) / 2, (wa, wa), (wb, wb), L, mat, np.stack([x, y, z], 1))


# ---------------------------------------------------------------- legs
def legs_pillars(m, hip, t):
    for z in (-5.8, 5.8):
        tbox(m, (0.5, (hip + 1.4) / 2, z), (7.4, 7.4), (6.0, 6.0), hip - 1.4, M_BRONZE)
        m.box((0.5, hip * 0.55, z), (7.6, 1.2, 7.6), M_DIRON)
        tbox(m, (1.6, 0.7, z), (10.5, 8.5), (9, 7.2), 1.4, M_IRON)
        if t >= 2:
            m.box((4.2, hip * 0.62, z), (1.2, hip * 0.55, 5.5), M_IRON)
        if t >= 3:
            for dz in (-2.2, 0, 2.2):
                spike(m, (6.5, 0.8, z + dz), (9.5, 0.6, z + dz * 1.2), 0.8)
    m.box((0, hip, 0), (10, 3, 15), M_DIRON)


def legs_spider(m, hip, t):
    r = (1.5, 1.9, 2.2)[t - 1]
    for s in (1, -1):
        for f in (1, -1):
            h = np.array((f * 3.5, hip - 1, s * 5))
            kn = np.array((f * 9.5, hip + 3.5, s * 11.5))
            ft = np.array((f * 13, 0.2, s * 14))
            m.ell(h, (2.4, 2.4, 2.4), M_IRON)
            m.cyl(h, kn, r, M_IRON, seg=6)
            m.ell(kn, (r + 0.8, r + 0.8, r + 0.8), M_BRONZE)
            m.cyl(kn, ft, r * 0.9, M_IRON, r1=0.45 if t < 3 else 0.2, seg=6)
            if t >= 2:
                m.cyl(h + (kn - h) * 0.25, h + (kn - h) * 0.7, r + 0.7, M_BRONZE, seg=6)
            if t >= 3:
                spike(m, kn, kn + np.array((0, 3.5, s * 1)), 0.9, M_BRONZE)
    tbox(m, (0, hip - 1, 0), (12, 13), (11, 14), 4, M_DIRON)


LEGS = dict(tracks=lambda m, hip, t: G6.legs_tracks(m, hip, t),
            springs=lambda m, hip, t: G6.legs_springs(m, hip, t),
            pillars=legs_pillars, spider=legs_spider)
HIP = dict(tracks=11, springs=17, pillars=12, spider=15)


# ---------------------------------------------------------------- where the hand goes for each tool
def hand_target(tool, S, side, pose):
    if tool == "hammer":
        d = (10.5, -6, 0) if pose == "idle" else (13.5, -7, 0)
    elif tool == "shield":
        d = (1.5, -7, 1.5 * side)
    elif tool == "claw":
        d = (5.5, -11, 1.5 * side) if pose == "idle" else (3.5, -9, 1.5 * side)
    else:  # cannon: forearm mount
        d = (2, -4, 0) if pose == "idle" else (-1, -4, 0)
    return S + np.array(d, float)


# ---------------------------------------------------------------- arm types
def draw_arm(m, S, Hn, kind, t, side, tool):
    """Draws shoulder -> elbow(s) -> wrist and returns the wrist and the forearm direction."""
    if kind == "long":
        Hn = S + (Hn - S) * 1.55 + np.array((2.5, 1.5, 0))
        E1 = S + (Hn - S) * 0.33 + np.array((-1.8, -1.0, 0))
        E2 = S + (Hn - S) * 0.68 + np.array((0.8, -2.2, 0))
        m.ell(S, (3.2, 3.2, 3.2), M_IRON)
        r = (1.8, 2.0, 2.2)[t - 1]
        for a, b in ((S, E1), (E1, E2), (E2, Hn)):
            m.cyl(a, b, r, M_IRON, seg=6)
        for e in (E1, E2):
            m.ell(e, (r + 0.9, r + 0.9, r + 0.9), M_BRONZE)
        if t >= 2:
            m.cyl(S + (E1 - S) * 0.2, S + (E1 - S) * 0.8, r + 0.6, M_BRONZE, seg=6)
        if t >= 3:
            spike(m, E2, E2 + np.array((-1, 3.5, 0)), 0.8, M_BRONZE)
        m.ell(S + (0, 1.5, 0), (3.8, 3.0, 3.6), M_BRONZE)
        return Hn, Hn - E2
    E = (S + Hn) / 2 + np.array((-1.5, -2.5, 0))
    if kind == "piston":
        m.box(S, (5, 5, 5), M_DIRON)
        r = (2.4, 2.7, 2.9)[t - 1]
        m.cyl(S, E, r, M_IRON)
        m.cyl(S + (1.6, -1.2, 0), E + (1.6, 1.2, 0), 0.8, Mat(ramp("#2a2c30", "#4a4e54", "#70767c", "#a0a6aa", "#d0d4d6")), seg=6)
        m.cyl(E + (0, 0, -2.8), E + (0, 0, 2.8), r + 0.3, M_DIRON, seg=8)
        m.cyl(E, Hn, r, M_IRON)
        if t >= 2:
            m.cyl(E + (Hn - E) * 0.35, E + (Hn - E) * 0.8, r + 0.6, M_BRONZE)
        if t >= 3:
            m.cyl(S + (-1.6, -1.2, 0), E + (-1.6, 1.2, 0), 0.8, M_IRON, seg=6)
        m.ell(S + (0, 2, 0), (4.6, 3.8, 4.2), M_BRONZE)
    else:  # heavy
        w = (6.8, 7.4, 7.9)[t - 1]
        tbox(m, S + (0, 1.6, side * 0.8), (10.5, 10.5), (8, 7.5), 8.5, M_BRONZE, rot_x(-0.18 * side))
        seg_box(m, S, E, w, w - 0.6, M_BRONZE)
        m.ell(E, (w * 0.5, w * 0.5, w * 0.5), M_IRON)
        seg_box(m, E, Hn, w - 0.4, w + 0.6, M_BRONZE)
        m.cyl(Hn + (E - Hn) * 0.12, Hn + (E - Hn) * 0.25, w * 0.62, M_DIRON)
        if t >= 2:
            m.box(S + (0, 4.6, side * 0.5), (7, 1.0, 6.2), M_IRON, rot_x(-0.18 * side))
        if t >= 3:
            spike(m, S + (0, 5, side * 1), S + (-1, 9.5, side * 2.5), 1.3)
    return Hn, Hn - E


# ---------------------------------------------------------------- tools
def tool_hammer(m, Hn, fdir, pose, core_k, t):
    shaft = np.array((3, 13 + t, 0)) if pose == "idle" else np.array((13 + t, -10, 0))
    sd = shaft / np.linalg.norm(shaft)
    top = Hn + shaft
    m.cyl(Hn - sd * 3, top, 1.1 + 0.2 * (t - 1), M_DIRON)
    R = rot_z(np.arctan2(sd[1], sd[0]) - np.pi / 2)
    hs = ((13, 7, 7), (15, 8, 8), (16.5, 9, 9))[t - 1]
    m.box(top, hs, M_IRON, R)
    m.box(top, (2.6, hs[1] + 0.6, hs[2] + 0.6), M_BRONZE if t < 3 else emissive(core_k, 9, 0.5), R)
    if t >= 2:
        for sgn in (1, -1):
            for dy, dz in ((0, 0), (2.2, 2.2), (-2.2, -2.2), (2.2, -2.2), (-2.2, 2.2))[: 1 if t == 2 else 5]:
                spike(m, top + R @ np.array((sgn * hs[0] / 2, dy, dz)),
                      top + R @ np.array((sgn * (hs[0] / 2 + (3 if t == 2 else 2.4)), dy, dz)), 1.1 if t == 2 else 0.9)
    m.ell(Hn, (2.7, 2.7, 2.7), M_BRONZE)


def tool_shield(m, Hn, fdir, pose, core_k, t, side=1):
    R = rot_y(-0.45 * side)
    c = Hn + np.array((3 + (0 if pose == "idle" else -2.5), 1.5 + (1.5 if t == 3 else 0), 2 * side))
    rim = ((13.5, 16.5), (13.5, 16.5), (15.5, 21))[t - 1]
    out = np.array((0, 0, side))
    m.box(c, (rim[0], rim[1], 1.2), M_BRONZE, R)
    m.box(c + R @ (out * 0.7), (rim[0] - 2, rim[1] - 2, 1.4), M_IRON, R)
    m.ell(c + R @ (out * 1.5), (2.4, 2.4, 1.6), M_BRONZE, R)
    if t >= 2:
        for sx_ in (-1, 1):
            for sy_ in (-1, 1):
                m.ell(c + R @ np.array((sx_ * (rim[0] / 2 - 2), sy_ * (rim[1] / 2 - 2), 1.5 * side)), (0.8, 0.8, 0.6), M_BRONZE, R)
        spike(m, c + R @ (out * 2.6), c + R @ (out * (6.5 if t == 2 else 8)), 1.3 if t == 2 else 1.6)
    if t >= 3:
        m.box(c + R @ (out * 1.5), (1.4, rim[1] - 5, 0.4), M_BRONZE, R)
        m.box(c + R @ np.array((0, 3, 1.5 * side)), (rim[0] - 5, 1.4, 0.4), M_BRONZE, R)


def tool_claw(m, Hn, fdir, pose, core_k, t, side=1):
    k = (1.0, 1.4, 1.7)[t - 1]
    fingers = [(3, -2.2, 1.2), (3.6, -0.6, 0), (3, -2.2, -1.2)]
    if t >= 3:
        fingers.append((2.4, -3.2, 0))
    m.box(Hn, (3.4, 3.4, 3.4), M_IRON)
    for d in fingers:
        m.cyl(Hn, Hn + np.array(d) * k, 0.9 + 0.15 * (t - 1), M_IRON, r1=0.25, seg=5)


def tool_cannon(m, Hn, fdir, pose, core_k, t, side=1):
    R = rot_z(0 if pose == "idle" else 0.08)
    base = Hn + np.array((0, 1.5, 0))
    L = (22, 26, 26)[t - 1]
    barrels = [0.0] if t < 3 else [2.4, -2.4]
    rb = 3.0 if t < 3 else 2.4
    for dy in barrels:
        at = lambda x, dy=dy: base + np.array((0, dy, 0)) + R @ np.array((x, 0, 0))
        m.cyl(at(-2), at(L), rb, M_IRON)
        for x in ((7, 15) if t == 1 else (6, 12, 18)):
            m.cyl(at(x), at(x + 1.8), rb + 0.6, M_BRONZE)
        if t == 1:
            m.cyl(at(L - 1.5), at(L + 1), rb + 0.7, M_DIRON)
        else:
            m.box(at(L + 0.5), (3.2, rb * 2 + 2.2, rb * 2 + 2.2), M_DIRON, R)
            for vy in (-1.2, 1.2):
                m.box(at(L + 0.5) + np.array((0, vy * rb, 0)), (1.2, 0.7, rb * 2 + 2.6), M_HOLE, R)
        m.ell(at(L + (1.1 if t == 1 else 2.15)), (0.3, rb * 0.62, rb * 0.62), M_HOLE, R)
    if t >= 3:
        for x in (4, 14):
            m.box(base + R @ np.array((x, 0, 0)), (2.2, 10, 6.6), M_BRONZE, R)
    if pose == "attack":
        fl = emissive(core_k, 20, 0.9)
        for dy in barrels:
            m.ell(base + np.array((0, dy, 0)) + R @ np.array((L + 4, 0, 0)), (4.5, 3.6, 3.6), fl)
        m.ell(base + R @ np.array((L - 3, 5, 1)), (3.2, 2.6, 2.6), M_SMOKE)


TOOLS = dict(hammer=tool_hammer, shield=tool_shield, claw=tool_claw, cannon=tool_cannon)


M_PUFF = Mat(ramp("#26262a", "#36363a", "#4a4a50", "#606066", "#7c7c82"))
M_PUFF.smoke = True
M_SPARK = Mat(ramp("#5a3a10", "#a06a18", "#e0a030", "#ffd870", "#fff6d0"), emissive=hexc("#ffc060"), glow_r=5, glow_k=0.45)
M_DEADCORE = Mat(ramp("#1e0c06", "#3a140a", "#5a200e", "#7a3214", "#9a4a20"), emissive=hexc("#a03810"), glow_r=7, glow_k=0.2)


def model(cfg, lv=1, pose="idle"):
    """cfg keys: legs, head, core, arms (far, near), tools (far, near). lv: int or dict per slot.
    pose: idle, attack or broken (slumped, core nearly out, the far arm torn off and lying in front)."""
    L = lv if isinstance(lv, dict) else {k: lv for k in ("legs", "head", "core", "armour", "arm_far", "arm_near", "tool_far", "tool_near")}
    broken = pose == "broken"
    p = "idle" if broken else pose
    hip = HIP[cfg["legs"]]
    lower = Model()
    LEGS[cfg["legs"]](lower, hip, L["legs"])
    up = Model()
    debris = Model()
    G6.torso(up, hip)
    G6.armour(up, hip, L["armour"])
    if broken:
        c = np.array((9.9, hip + 10.5, 0))
        up.cyl(c + (-1.1, 0, 0), c + (-0.1, 0, 0), 4.4, M_DIRON)
        up.ell(c, (1.4, 2.8, 2.8), M_DEADCORE)
        up.box(c + (0.9, 0.4, 0), (0.5, 6.0, 0.6), M_HOLE, rot_x(0.5))
    else:
        G6.core(up, hip, cfg["core"], L["core"])
    G6.HEADS[cfg["head"]](up, hip, cfg["core"], L["head"])
    S_far = None
    for slot, side, z in (("far", -1, -12.5), ("near", 1, 12.0)):
        S = np.array((0.5, hip + 14, z))
        tool = cfg["tools"][slot]
        target = debris if (broken and slot == "far") else up
        if broken and slot == "far":
            S_far = S
        Hn = hand_target(tool, S, side, p)
        Hn, fdir = draw_arm(target, S, Hn, cfg["arms"][slot], L["arm_" + slot], side, tool)
        fn = TOOLS[tool]
        if tool == "hammer":
            fn(target, Hn, fdir, p, cfg["core"], L["tool_" + slot])
        else:
            fn(target, Hn, fdir, p, cfg["core"], L["tool_" + slot], side)
    if pose == "attack":
        lean = -0.16 if "hammer" in cfg["tools"].values() else 0.07
        up = pivot(up, rot_z(lean), (0, hip, 0))
    if broken:
        for d in ((0.6, 3.4, 2.8), (2.2, 5.0, 3.6), (-0.8, 6.2, 3.0), (1.4, 7.4, 2.2)):
            up.ell(S_far + d, (0.7, 0.7, 0.7), M_SPARK)
        for i, d in enumerate(((1, 14, 0), (-1.5, 19, 1), (-4.5, 24, 0), (-8, 28, 0.5))):
            up.ell(np.array((0, hip + 10, 0)) + d, (3.2 + i * 0.8, 3.0, 3.0), M_PUFF)
        up = pivot(up, rot_z(-0.36), (0, hip, 0)).transformed(I3, (0, -2.5, 0))
        debris = debris.transformed(I3, -S_far)
        debris = debris.transformed(rot_y(0.5) @ rot_x(-np.pi / 2), (16.0, 2.6, 6.0))
    m = Model()
    m.extend(lower)
    m.extend(up)
    m.extend(debris)
    return m


def dims(k):
    return int(104 * k), int(104 * k), int(round(40 * k)), int(round(82 * k))


def build(cfg, lv=1, pose="idle", k=2.0, **kw):
    w, h, ox, oy = dims(k)
    opts = dict(STYLE1)
    opts.update(kw)
    spr = render(model(cfg, lv, pose).scaled(k), w, h, ox, oy, **opts)
    spr.ox, spr.oy = ox, oy
    return spr


def cfg(legs="tracks", head="visor", core="fire", arms=("piston", "piston"), tools=("hammer", "shield")):
    return dict(legs=legs, head=head, core=core, arms=dict(far=arms[0], near=arms[1]), tools=dict(far=tools[0], near=tools[1]))


if __name__ == "__main__":
    from paths import out
    tests = [cfg(arms=("piston", "piston")), cfg(arms=("heavy", "heavy")), cfg(arms=("long", "long")),
             cfg(legs="pillars"), cfg(legs="spider"), cfg(legs="springs", tools=("cannon", "claw"))]
    w, h, _, _ = dims(2.0)
    sc = Scene(3 * w, 2 * h)
    sc.rgb[:] = hexc("#2c2436")
    for i, c in enumerate(tests):
        sc.blit(build(c, 2), (i % 3) * w, (i // 3) * h)
    sc.image(2).save(out("test_g7.png"))
