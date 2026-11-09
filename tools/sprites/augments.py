"""The Inventor's augments on the humanoid golems. An augment gives a golem an ability, not numbers: a lightning
coil on the shoulder, a mirror buckler on the forearm, coil springs on the shins. Every augment sits in a brass
housing with a blue lamp — it runs off the Inventor ("На проводах": if he falls, the lamps go out).

Where an augment goes is found from the golem's own shape (the top of the shoulder, the outside of the forearm,
the shins), so any frame takes any augment. Each one is checked for clipping like the golems.

    python3 tools/sprites/augments.py      -> out/augments_check.png
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_STEEL, M_HOLE, STYLE1
from golem7 import M_PUFF
import golems_h as GH
from golems_h import arr, unit, lerp, rivets, sparks, puffs, Parts, ik, place_upper, COPPER, PORC, ARC, ENERGY
from clipcheck import report, cells, STEP
from leaders_h import BRASS_P, SPARK, LENS, zigzag

MIRROR = Mat(ramp("#18202a", "#2e3c4c", "#4e6276", "#7e94aa", "#c4d4e2"))                  # polished: dark, a cold sheen
LAMP = Mat(ramp("#1a3a5a", "#2a6a9a", "#4aa8e0", "#9ad8ff", "#e8f8ff"), emissive=hexc("#60c8ff"), glow_r=3, glow_k=0.4)
SPRING = Mat(ramp("#2a1a08", "#5a3c14", "#8e6624", "#c49a40", "#f0d27a"))                  # brass springs: the Inventor's work
BODY = ("chest", "back", "pauldron_n", "pauldron_f", "head", "spine", "pelvis", "robe", "hose")


def lamp(g, p, d):
    """The blue indicator lamp in a brass collar."""
    p, d = arr(p), unit(d)
    g.cyl(p - d * 0.2, p + d * 0.35, 0.55, BRASS_P, seg=8)
    g.ell(p + d * 0.45, (0.38, 0.38, 0.38), LAMP)


def top_at(G, x, z, r=2.0, keys=BODY):
    """The highest point of the body over a small patch (x, z)."""
    ys = []
    for k in keys:
        if k not in G:
            continue
        for c in cells(G[k]):
            p = np.array(c) * STEP
            if (p[0] - x) ** 2 + (p[2] - z) ** 2 <= r * r:
                ys.append(p[1])
    return max(ys) if ys else None


def leg_joints(S, A):
    """Hip, knee and ankle of both legs, worked out as creature_parts does it."""
    R = rot_z(A["lean"]) @ rot_y(A.get("twist", 0.0))
    X = place_upper(Parts(), R, A["t"], hip=S["hip"], keys=())
    lift = 3.3 * S["th_leg"] + 0.3 - 3.6
    out = []
    for hx, ank, s in ((S["hipx"][0], A["ank"][0], 1), (S["hipx"][1], A["ank"][1], -1)):
        h = X((hx, S["hip"], S["hz"] * s))
        kn, an = ik(h, arr(ank) + (0, lift, 0), S["LT"], S["LS"], (1.0, 0.25, 0.0))
        out.append((h, kn, an, s))
    return out


# ---------------------------------------------------------------- Грозовая катушка
COIL_SPOTS = ((-1.2, 0.0, -0.8, 1.35), (-3.0, 0.0, -2.0, 1.35), (-3.6, 0.0, -4.6, 1.35), (-4.8, 0.0, -7.8, 1.1),
              (-4.8, 0.0, -7.8, 0.9))   # on the shoulder; further back; on the middle of the back, smaller


def coil(G, S, A, info, active, spot=0):
    """A Tesla coil standing on the near shoulder (or further back, where there is room): a brass base,
    porcelain, the copper winding, a toroid with a spark on it."""
    g = Model()
    sh = info["sh_n"]
    c = sh + arr(COIL_SPOTS[spot][:3])
    y = top_at(G, c[0], c[2])
    y = (y if y is not None else sh[1] + 3.0) + 0.3
    base = arr((0.0, 0.0, 0.0))
    g.cyl(base - (0, 0.6, 0), base + (0, 0.5, 0), 1.9, BRASS_P, seg=12)
    lamp(g, base + (1.6, 0.0, 0.9), (1.0, 0.2, 0.6))
    for i in range(2):
        g.cyl(base + (0, 0.5 + i * 0.9, 0), base + (0, 1.0 + i * 0.9, 0), 1.25, PORC, seg=10)
    g.cyl(base + (0, 2.0, 0), base + (0, 8.2, 0), 0.55, M_DIRON, seg=6)
    for i in range(7):
        g.cyl(base + (0, 2.2 + i * 0.8, 0), base + (0, 2.6 + i * 0.8, 0), 1.0, COPPER, seg=10)
    top = base + (0, 8.6, 0)
    g.ell(top, (2.3, 0.7, 2.3), BRASS_P)
    K = COIL_SPOTS[spot][3]
    G["aug"].extend(g.scaled(K).transformed(I3, (c[0], y, c[2])))
    ball = arr((c[0], y, c[2])) + (top + (0, 0.9, 0)) * K
    G["aug"].ell(ball, (0.7, 0.7, 0.7), SPARK)
    fx = G["fx"]
    if active:                                   # a neighbouring enemy struck
        tgt = arr((sh[0] + 22.0, 9.0, sh[2] - 2.0))
        zigzag(fx, ball, tgt, n=9, amp=1.6, seed=3, r=0.35)
        fx.ell(ball, (1.6, 1.6, 1.6), ENERGY)
        fx.ell(tgt, (1.8, 1.8, 1.8), ENERGY)
        sparks(fx, tgt, n=5, spread=2.4, seed=4, big=False)
    else:
        for i, d in enumerate(((2.2, 1.4, 1.0), (-1.8, 1.8, -1.2))):
            zigzag(fx, ball, ball + arr(d), n=3, amp=0.35, seed=i, r=0.16)
    return [("aug", k) for k in ("pauldron_n", "chest", "back", "arm_n.ball")]


# ---------------------------------------------------------------- Отражатель
def mirror(G, S, A, info, active):
    """A round mirror buckler on the outside of the near forearm, turned towards the enemy."""
    g = G["aug"]
    n_ = info["n"]
    el, w = info["el_n"], info["w_n"]
    d = unit(w - el)
    out = unit(arr((0.55, 0.0, 0.85)) - d * (d @ arr((0.55, 0.0, 0.85))))
    c = lerp(el, w, 0.45) + out * (S["th_arm"] * 2.6 + 1.2)
    side = unit(np.cross(out, d))
    R = np.column_stack([out, d, side])          # the disc's face looks along `out`
    g.cyl(c - out * 1.6, c - out * 0.3, 0.6, M_DIRON, seg=6)                              # the mount on the forearm
    g.cyl(c - out * 0.5, c + out * 0.3, 4.2, BRASS_P, seg=16)                             # the rim
    g.ell(c + out * 0.3, (0.9, 3.6, 3.6), MIRROR, R)                                       # the polished dome
    g.ell(c + out * 0.95 + d * 1.2 - side * 1.0, (0.2, 0.7, 0.5), Mat(ramp("#a8c0d4", "#d2e2ee", "#f2f8fc", "#ffffff", "#ffffff")), R)
    rivets(g, [c + out * 0.35 + (np.cos(a) * d + np.sin(a) * side) * 3.9 for a in np.linspace(0, 2 * np.pi, 9)[:-1]],
           mat=BRASS_P, r=0.3)
    lamp(g, c - out * 0.2 + d * 4.3, d)
    fx = G["fx"]
    if active:                                   # the blow comes back at the attacker: a flash and rays thrown forward
        fx.ell(c + out * 1.0, (0.6, 4.0, 4.0), ENERGY, R)
        for i, a in enumerate(np.linspace(0, 2 * np.pi, 9)[:-1]):
            q = c + out * 0.8 + (np.cos(a) * d + np.sin(a) * side) * 2.0
            fx.cyl(q, q + out * 6.0 + arr((5.0, 0, 0)) + (np.cos(a) * d + np.sin(a) * side) * 2.4, 0.3, ARC, r1=0.06, seg=4)
        zigzag(fx, c + out * 0.8, c + arr((20.0, 3.0, 6.0)), n=7, amp=1.0, seed=7, r=0.3)
    return [("aug", "arm_n"), ("aug", "arm_n.ram")]


# ---------------------------------------------------------------- Пружинный рывок
def springs(G, S, A, info, active):
    """Coil springs down the outside of both shins, from a lug under the knee to a heel plate; a dash: the golem
    thrown forward off its springs, dust where it stood."""
    g = G["aug"]
    th = S["th_leg"]
    for h, kn, an, s in leg_joints(S, A):
        o = arr((0, 0, s * 3.9 * th))
        a, b = kn + o - (0, 1.0, 0), an + o + (0, 0.6, 0)
        g.cyl(a - (0, 0, s * 1.2 * th), a + (0, 0, s * 0.3), 0.7, BRASS_P, seg=8)            # the lug under the knee
        g.box(b + (-0.6, -0.4, s * -0.2), (3.2, 0.7, 1.6), BRASS_P)                            # the heel plate
        n = 9 if not active else 7
        L = b - a
        for i in range(n):
            p = a + L * (i + 0.5) / n
            g.cyl(p - unit(L) * 0.24, p + unit(L) * 0.24, 1.6, SPRING, seg=10)
        g.cyl(a, b, 0.3, M_DIRON, seg=5)
        lamp(g, a + (0.9, -0.2, s * 0.4), (1.0, 0.0, s * 0.5))
    return [("aug", "leg_n"), ("aug", "leg_f"), ("aug", "leg_n.ram"), ("aug", "leg_f.ram")]


AUGS = {
    "coil": ("Грозовая катушка", "если рядом враг — каждые 2 хода бьёт его молнией", coil),
    "mirror": ("Отражатель", "первый удар в бою отражается в атакующего", mirror),
    "spring": ("Пружинный рывок", "в начале боя прыгает к ближайшему врагу", springs),
}


def parts(frame, aug, pose="idle"):
    """A frame with an augment. pose: idle, or "active" — the augment going off."""
    S = GH.BY_NAME[frame]
    active = pose == "active"
    A = dict(S["poses"]["idle"], fx=None)
    if active and aug == "spring":               # the legs thrust back, the body thrown forward
        A.update(lean=-0.25, ank=(arr(A["ank"][0]) + (-4.0, 0, 0), arr(A["ank"][1]) + (-6.0, 0, 0)))
    G, info = GH.creature_parts(S, A, fx=False)
    for side in ("n", "f"):                      # the arm joints, for mounting
        R = rot_z(A["lean"]) @ rot_y(A.get("twist", 0.0))
        X = place_upper(Parts(), R, A["t"], hip=S["hip"], keys=())
        sh = X(S["sh"] * arr((1, 1, 1 if side == "n" else -1)))
        el, w = ik(sh, sh + arr(A["hand_" + side]), S["LU"], S["LF"], A["pole_" + side])
        info["el_" + side], info["w_" + side] = el, w
    base_allow = GH.BASE_ALLOWED + S.get("allow", [])
    if aug == "coil":                            # the first spot on the shoulder that is free
        for spot in range(len(COIL_SPOTS)):
            G2, info2 = GH.creature_parts(S, A, fx=False)
            info2.update({k: info[k] for k in ("el_n", "w_n", "el_f", "w_f")})
            extra = coil(G2, S, A, info2, active, spot)
            if not report(G2, base_allow + extra, skip=("fx",)):
                break
        G = G2
        allow = base_allow + extra
    else:
        allow = base_allow + AUGS[aug][2](G, S, A, info, active)
    if active and aug == "spring":
        for k in list(G):
            G[k] = G[k].transformed(rot_z(-0.12), (5.0, 6.0, 0.0))
        for i, d in enumerate(((-4.0, 1.6, 7.0), (-9.0, 2.4, 3.0), (-6.0, 1.4, -3.0), (-11.0, 3.2, 0.0))):
            G["fx"].ell(arr(d), (3.6 + 0.6 * i, 2.2 + 0.4 * i, 3.2 + 0.5 * i), M_PUFF)
    return G, allow


def check(frame, aug, pose="idle"):
    G, allow = parts(frame, aug, pose)
    return report(G, allow, skip=("fx",))


def build(frame, aug, pose="idle", k=1.3):
    S = GH.BY_NAME[frame]
    G, _ = parts(frame, aug, pose)
    cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
    cw, ch = cw + 24, ch + 12
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int((cy + 12) * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    import sys
    from PIL import Image
    from paths import out
    frames = ["Мудрец", "Горн", "Орудие", "Механик"]
    rows = []
    for aug in (sys.argv[1:] or list(AUGS)):
        row = []
        for fr in frames:
            for pose in ("idle", "active"):
                bad = check(fr, aug, pose)
                if bad:
                    print(aug, fr, pose, bad)
                im = build(fr, aug, pose, k=2.0).image(1)
                bb = im.getbbox()
                row.append(im.crop((bb[0] - 4, bb[1] - 4, bb[2] + 4, bb[3] + 4)))
        rows.append(row)
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
    sheet.save(out("augments_check.png"))
    print("ok")
