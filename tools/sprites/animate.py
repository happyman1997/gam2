"""Animated attacks of the humanoid Guard: idle -> wind-up -> blow -> contact -> recovery -> idle.

Poses are numbers (humanoid.ATTACKS), so in-between frames are interpolated: the hand and the haft
travel on an arc round the shoulder, a stepping foot lifts, the maul head leaves a motion trail
between frames. Every frame goes through the clipping check.

    python3 tools/sprites/animate.py            -> out/guard_attack.gif (the Guard's attack, close up and at battle size)
    python3 tools/sprites/animate.py all        -> out/guard_attacks.gif (all three attack poses side by side)
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
from r3d import render, rot_y, SA, CA, YAW
from golem6 import STYLE1, M_IRON
import humanoid as H
import swarm1 as W
from battle import flash, put
from clipcheck import report
from noise import value_noise
from paths import font, out

_far = H.SH * (1, 1, -1)


def idle_numbers():
    """The idle pose as numbers, so it can be blended with the attacks."""
    A = dict(lean=0.0, twist=0.0, t=(0.0, 0.0, 0.0),
             ankles=((2.8, 3.6, H.HZ + 0.7), (-4.6, 3.6, -H.HZ - 0.8)),
             hand=(H.WX, H.WY, H.WZ), hand_pole=(1.4, -7.6, 2.0), face=(0.0, 1.0, 0.0),
             shield=(5.8, -10.0, -2.0), shield_pole=(0.8, -8.0, -1.6), shield_rot=0.5, fx=None, ram="back",
             carry=1.0)
    A["haft"] = H.carry_haft()
    return A


IDLE = idle_numbers()

# wind-up keyframes: where the blow starts from
WINDUP = {
    "slam": dict(lean=0.08, twist=0.22, t=(-0.4, -0.6, 0.0),
                 ankles=((2.8, 3.6, H.HZ + 0.7), (0.0, 5.0, -H.HZ - 0.9)),
                 hand=(0.6, 12.6, -1.6), hand_pole=(-1.0, 0.0, 0.5), haft=(-0.75, 0.66, 0.0), face=(0.66, 0.75, 0.0),
                 shield=(8.0, -5.5, 1.0), shield_pole=(0.0, -1.0, -0.4), shield_rot=0.25, fx=None, ram="front", carry=0.0),
    "sweep": dict(lean=0.05, twist=0.3, t=(-0.3, -1.0, 0.0),
                  ankles=((2.8, 3.6, H.HZ + 0.9), (-4.6, 3.6, -H.HZ - 0.8)),
                  hand=(0.1, -14.1, 2.6), hand_pole=(0.6, 0.0, 0.6), haft=(-0.987, -0.165, 0.0), face=(0.165, -0.987, 0.0),
                  shield=(7.0, -7.0, 1.0), shield_pole=(0.0, -1.0, -0.4), shield_rot=0.3, fx=None, ram="back", carry=0.0),
    "ram": dict(lean=0.12, twist=-0.15, t=(-0.8, -1.0, 0.0),
                ankles=((2.0, 3.6, H.HZ + 0.9), (-2.5, 4.6, -H.HZ - 0.4)),
                hand=(H.WX, H.WY, H.WZ), hand_pole=(1.4, -7.6, 2.0), haft=IDLE["haft"], face=(0.0, 1.0, 0.0), carry=1.0,
                shield=(5.5, -9.0, -1.0), shield_pole=(0.0, -1.0, -0.6), shield_rot=0.3, fx=None, ram="back"),
}
# the plane the hand and haft swing in, and the way round (-1: forward and down / towards the far side)
SWING = {"slam": ("xy", -1), "sweep": ("xz", -1), "ram": ("xy", 0)}


def _plane(v, plane):
    v = H.arr(v)
    a, b = (0, 1) if plane == "xy" else (0, 2)
    return np.arctan2(v[b], v[a]), np.hypot(v[a], v[b]), a, b


def arc_lerp(v0, v1, s, plane, way):
    """Blend two vectors by turning round the plane's normal the given way (and lerping the rest)."""
    t0, r0, a, b = _plane(v0, plane)
    t1, r1, _, _ = _plane(v1, plane)
    d = t1 - t0
    if way == 0:
        d = (d + np.pi) % (2 * np.pi) - np.pi
    if way < 0 and d > 0:
        d -= 2 * np.pi
    if way > 0 and d < 0:
        d += 2 * np.pi
    t, r = t0 + d * s, r0 + (r1 - r0) * s
    out = H.arr(v0) + (H.arr(v1) - H.arr(v0)) * s
    out[a], out[b] = r * np.cos(t), r * np.sin(t)
    return out


def shoulder_of(A):
    R = H.rot_z(A["lean"]) @ H.rot_y(A["twist"])
    piv = H.arr((0, H.HIP, 0))
    return R @ (H.SH - piv) + piv + H.arr(A["t"])


def fix_grip(A, least=70.0, most=118.0):
    """Keep the haft between `least` and `most` degrees off the forearm (a real grip), turning it in
    their common plane. Works in the same space pose_parts does, carried or not."""
    c = float(A.get("carry", 0.0))
    M = np.eye(3) * (1 - c) + (H.rot_z(A["lean"]) @ H.rot_y(A["twist"])) * c
    sh = shoulder_of(A)
    el, w = H.ik(sh, sh + M @ H.arr(A["hand"]), H.LU, H.LF, M @ H.arr(A["hand_pole"]))
    d, u = H.unit(w - el), H.unit(M @ H.arr(A["haft"]))
    ang = np.degrees(np.arccos(np.clip(d @ u, -1, 1)))
    if least <= ang <= most:
        return A
    n = u - d * (d @ u)
    if np.linalg.norm(n) < 1e-6:
        n = H.arr((0, 1.0, 0)) - d * d[1]
    n = H.unit(n)
    a = np.radians(least if ang < least else most)
    A = dict(A)
    A["haft"] = tuple(H.unit(np.linalg.solve(M, d * np.cos(a) + n * np.sin(a))))
    return A


def blend(A0, A1, s, plane, way, lift=0.0):
    L = lambda k: tuple(H.arr(A0[k]) + (H.arr(A1[k]) - H.arr(A0[k])) * s)
    A = dict(A1 if s >= 0.5 else A0)
    bump = np.sin(np.pi * s)
    for k in ("lean", "twist", "shield_rot"):
        A[k] = A0[k] + (A1[k] - A0[k]) * s
    A["carry"] = A0.get("carry", 0.0) + (A1.get("carry", 0.0) - A0.get("carry", 0.0)) * s
    A["t"] = L("t")
    sh = H.arr(L("shield"))
    if abs(A1["shield_rot"] - A0["shield_rot"]) > 1.0:          # a shield turning round swings wide of the body
        sh += H.arr((0.0, 2.0, -6.0)) * bump
    A["shield"] = tuple(sh)
    A["hand_pole"] = tuple(H.unit(L("hand_pole")))
    A["shield_pole"] = tuple(H.unit(H.arr(L("shield_pole")) + H.arr((0, 0, -1.0)) * bump))
    ank = []
    for f0, f1 in zip(A0["ankles"], A1["ankles"]):
        p = H.arr(f0) + (H.arr(f1) - H.arr(f0)) * s
        if np.linalg.norm(H.arr(f1)[[0, 2]] - H.arr(f0)[[0, 2]]) > 2.5:
            p[1] += 2.2 * bump                                         # a stepping foot lifts
        ank.append(tuple(p))
    A["ankles"] = tuple(ank)
    A["hand"] = tuple(arc_lerp(A0["hand"], A1["hand"], s, plane, way) + H.arr((0.0, lift, lift * 0.8)) * bump)
    A["haft"] = tuple(H.unit(arc_lerp(A0["haft"], A1["haft"], s, plane, way)))
    A["face"] = tuple(H.unit(L("face")))
    A["fx"] = None
    return fix_grip(A)


ease_io = lambda s: 0.5 - 0.5 * np.cos(np.pi * s)
ease_in = lambda s: s * s


LIFT = {   # on the way back the maul is raised before it goes onto the shoulder again
    "slam": dict(hand=(8.0, -4.0, 1.0), haft=(0.1, 1.0, 0.0), face=(1.0, 0.0, 0.0)),
    "sweep": dict(hand=(8.0, -4.0, 1.0), haft=(0.1, 1.0, 0.0), face=(1.0, 0.0, 0.0)),
    "ram": dict(hand=(3.0, -5.0, 3.0), haft=(-0.3, 0.95, 0.0), face=(1.0, 0.3, 0.0)),
}


def timeline(kind):
    """(numbers, duration ms, ft or None, trail (s0, s1) or None, segment) for every frame."""
    I, Wd, X = IDLE, WINDUP[kind], dict(H.ATTACKS[kind], smear=False)
    plane, way = SWING[kind]
    Lf = dict(I, carry=0.0, **LIFT[kind])
    up = {"slam": 2.0, "sweep": 6.0, "ram": 0.0}[kind]
    f = [(I, 420, None, None, None)]
    for s in (1 / 3, 2 / 3):
        f.append((blend(I, Wd, ease_io(s), "xy", 0, lift=up), 70, None, None, None))
    f.append((fix_grip(Wd), 150, None, None, None))
    seg = (Wd, X, plane, way)
    prev = 0.0
    for s in (0.45, 0.8):
        f.append((blend(Wd, X, ease_in(s), plane, way), 45, None, (prev, ease_in(s)), seg))
        prev = ease_in(s)
    f.append((dict(X, ft=0.0), 210, 0.0, (prev, 1.0), seg))
    f.append((dict(X, ft=1.0), 130, 1.0, None, None))
    if kind == "ram":       # the maul never left the shoulder: straight back to rest
        for s in (0.35, 0.7):
            f.append((blend(X, I, ease_io(s), "xy", 0), 95, None, None, None))
        f.append((blend(X, I, ease_io(0.9), "xy", 0), 95, None, None, None))
    else:
        f.append((blend(X, Lf, ease_io(0.5), "xy", 0), 90, None, None, None))
        f.append((fix_grip(Lf), 100, None, None, None))
        f.append((blend(Lf, I, ease_io(0.5), "xy", 0, lift=3.0), 90, None, None, None))
    return f


def trail(G, seg, s0, s1, kind):
    """Dithered boxes along the path the maul head (or the shield, for the ram) took since the last frame."""
    Wd, X, plane, way = seg
    key = "sc" if kind == "ram" else "hc"
    pts = []
    for s in np.linspace(s0, s1, 6):
        A = blend(Wd, X, s, plane, way) if s < 1 else X
        _, info = H.pose_parts(A, fx=False)
        pts.append(info[key])
    fx = G["fx"]
    for i, (p0, p1) in enumerate(zip(pts[:-1], pts[1:])):
        L = np.linalg.norm(p1 - p0)
        if L < 0.5:
            continue
        tv = H.unit(p1 - p0)
        side = H.unit(np.cross(tv, (0, 0, 1.0))) if abs(tv[2]) < 0.9 else H.arr((0, 1.0, 0))
        R = np.column_stack([tv, side, np.cross(tv, side)])
        k = 0.35 + 0.65 * (i + 1) / (len(pts) - 1)
        size = (L * 1.1, (9.0 if kind == "ram" else 4.6) * k, (5.0 if kind == "ram" else 4.6) * k)
        fx.box((p0 + p1) / 2, size, H.SMEAR, R)


def frame_parts(A, ft, tr, seg, kind):
    G, info = H.pose_parts(A, fx=False)
    if ft is not None:
        H.impact(G["fx"], A, ft, info)
    if tr is not None:
        trail(G, seg, tr[0], tr[1], kind)
    return G, info


def sprite_of(G, k):
    w, h = int(82 * k), int(80 * k)
    ox, oy = int(36 * k), int(72 * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def to_screen(p, k):
    """Model point -> pixel offset from the sprite's ground origin (as r3d projects it)."""
    q = rot_y(YAW) @ H.arr(p)
    return q[0] * k, (q[2] * SA - q[1] * CA) * k


KINDS = (("slam", "А · удар сверху"), ("sweep", "Б · размах понизу"), ("ram", "В · удар щитом"))


def main(panels, name, S=2, PH=300):
    """panels: (kind, scale, label, width) side by side, all on one timeline."""
    WW, HH = sum(p[3] for p in panels), PH + 40
    bg = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 95) * 0.6 + value_noise(WW, HH, 5, 96) * 0.4
    th = BAYER[bg.yy % 4, bg.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        bg.rgb[lv == i] = hexc(col)
    lines = {kind: timeline(kind) for kind, _, _, _ in panels}
    nfr = len(lines[panels[0][0]])
    frames, durs = [], []
    for fi in range(nfr):
        sc = Scene(WW, HH)
        sc.rgb[:] = bg.rgb
        x0 = 0
        for kind, k, _, pw in panels:
            A, dur, ft, tr, seg = lines[kind][fi]
            G, info = frame_parts(A, ft, tr, seg, kind)
            bad = report(G, H.ALLOWED, skip=("fx", "sparks"))
            if bad:
                print(kind, fi, "clipping:", [(a, b, round(v, 2)) for v, a, b in bad])
            spr = sprite_of(G, k)
            cx, by = x0 + int(pw * 0.36), PH - 52
            e = ((sc.xx - cx - 6) / (23 * k)) ** 2 + ((sc.yy - by) / (4 * k)) ** 2
            sc.rgb[e <= 1] *= 0.62
            X = H.ATTACKS[kind]                        # the target stands where the blow lands
            _, xinfo = H.pose_parts(X, fx=False)
            hit = xinfo["face"] if kind == "slam" else (xinfo["hc"] if kind == "sweep" else
                                                          xinfo["sc"] + xinfo["R"] @ H.arr((3.2, 0, 0)))
            dx, dy = to_screen((hit[0] + (1.5 if kind != "ram" else 2.0), 0.0, hit[2]), k)
            bug = W.build((), 0.02, "idle", True, k=k / 2.2, genes=W.genes_for(7))
            b, push = bug, 0
            if ft == 0.0:
                b = flash(bug, 0.75)
            elif ft == 1.0:
                b, push = flash(bug, 0.3), int(round(1.6 * k))
            bx, byy = int(cx + dx + push), int(by + dy)
            e = ((sc.xx - bx) / (3.3 * k)) ** 2 + ((sc.yy - byy) / k) ** 2
            sc.rgb[e <= 1] *= 0.62
            put(sc, b, bx, byy, mirror=True)
            sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
            x0 += pw
        img = sc.image(S)
        d = ImageDraw.Draw(img)
        fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
        x0 = 0
        for _, _, label, pw in panels:
            x = (x0 + pw // 2) * S
            d.text((x - d.textlength(label, font=fh) / 2, (PH + 6) * S), label, font=fh, fill=(226, 186, 106))
            x0 += pw
        frames.append(img)
        durs.append(lines[panels[0][0]][fi][1])
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames]
    path = out(name)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2, optimize=False)
    print(path, frames[0].size, len(frames), "frames")
    return frames, durs


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["all"]:
        main([(kind, 3.0, label, 330) for kind, label in KINDS], "guard_attacks.gif")
    else:
        main([("slam", 3.6, "Страж · атака", 400), ("slam", 2.2, "в размере боя", 240)], "guard_attack.gif", PH=320)
