"""Animated attack of the Father of the Colossus: idle -> the mace raised high and cocked behind ->
an overhead blow coming down a little across the body -> contact (lightning into the ground) ->
the mace raised again. The minigun spins up and fires all through the blow.

Poses are numbers (golems_h.COLOSSUS), the in-betweens are interpolated: the hand and the mace turn
on an arc round the shoulder, the stepping foot lifts. Every frame goes through the clipping check.

    python3 tools/sprites/animate_colossus.py      -> out/colossus_attack.gif
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
from r3d import render
from noise import value_noise
import golems_h as GH
import swarm1 as W
from animate import arc_lerp, ease_io, to_screen
from battle import flash, put
from clipcheck import report
from paths import font, out

S = GH.COLOSSUS
IDLE = dict(S["poses"]["idle"], spin=0.0, fx=None)
HIT = dict(S["poses"]["attack"], fx=None)
# the wind-up: the body turned and leaning back, the near arm raised high, the mace cocked behind it
WIND = dict(IDLE, lean=0.07, twist=0.2, t=(-0.6, -0.5, 0.0),
            hand_n=(-1.5, 13.5, 6.5), pole_n=(-0.3, 0.2, 1.0), mace_dir=(-0.75, -0.35, 0.45), ram_n="front",
            hand_f=(10.5, -10.0, -1.0))


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def forearm(A):
    """The direction of the near forearm in pose A, worked out as creature_parts does it."""
    R = GH.rot_z(A["lean"]) @ GH.rot_y(A.get("twist", 0.0))
    X = GH.place_upper(GH.Parts(), R, A["t"], hip=S["hip"], keys=GH.UPPER)
    sh = X(S["sh"])
    el, w = GH.ik(sh, sh + np.asarray(A["hand_n"], float), S["LU"], S["LF"], A["pole_n"])
    return unit(w - el)


def held(ref):
    """How the mace sits in the hand in pose `ref`: the forearm and the haft."""
    d = forearm(ref)
    return d, GH.grip_dir(d, ref["mace_dir"], least=ref.get("grip_least", 72.0))


def grip_of(ref):
    """The hold as (the axis the haft and the forearm turn about, the angle between them)."""
    d, u = held(ref)
    return unit(np.cross(d, u)), np.arccos(np.clip(d @ u, -1, 1))


def hold(A, n, th):
    """Pose A with the haft at angle th to the forearm, in the plane square to n: the hand does not roll."""
    d = forearm(A)
    p = np.cross(n, d)
    p = unit(p - d * (d @ p))
    return dict(A, mace_dir=tuple(np.cos(th) * d + np.sin(th) * p), grip_least=30.0)


def slerp(a, b, s):
    a, b = unit(a), unit(b)
    w = np.arccos(np.clip(a @ b, -1, 1))
    if w < 1e-6:
        return a
    return unit((np.sin((1 - s) * w) * a + np.sin(s * w) * b) / np.sin(w))


def blend(A0, A1, s, way_hand, way_mace):
    """Numbers between two poses: the hand and the mace turn round the shoulder the given ways."""
    L = lambda k: tuple(np.asarray(A0[k], float) + (np.asarray(A1[k], float) - np.asarray(A0[k], float)) * s)
    A = dict(A1 if s >= 0.5 else A0)
    for k in ("lean", "twist"):
        A[k] = A0.get(k, 0.0) + (A1.get(k, 0.0) - A0.get(k, 0.0)) * s
    A["grip_least"] = A0.get("grip_least", 72.0) + (A1.get("grip_least", 72.0) - A0.get("grip_least", 72.0)) * s
    A["t"] = L("t")
    bump = np.sin(np.pi * s)
    ank = []
    for f0, f1 in zip(A0["ank"], A1["ank"]):
        p = np.asarray(f0, float) + (np.asarray(f1, float) - np.asarray(f0, float)) * s
        if np.linalg.norm(np.asarray(f1)[[0, 2]] - np.asarray(f0)[[0, 2]]) > 2.5:
            p[1] += 3.0 * bump                                         # a stepping foot lifts
        ank.append(tuple(p))
    A["ank"] = tuple(ank)
    A["hand_n"] = tuple(arc_lerp(A0["hand_n"], A1["hand_n"], s, "xy", way_hand))
    A["mace_dir"] = tuple(unit(arc_lerp(A0["mace_dir"], A1["mace_dir"], s, "xy", way_mace)))
    for k in ("pole_n", "pole_f"):
        A[k] = tuple(unit(L(k)))
    A["hand_f"] = L("hand_f")
    A["fx"] = None
    return A


def timeline():
    """(numbers, duration ms, ft or None, gun firing) for every frame. The mace is held the same way all
    through (thumb up, as at rest): the wrist only bends, evenly, from cocked back to driving the head down."""
    n_i, th_i = grip_of(IDLE)
    n_c, th_c = grip_of(HIT)
    th_w = np.radians(112.0)                                  # cocked: the head well back behind the hand
    f = [(IDLE, 420, None, False)]
    for s in (1 / 3, 2 / 3):                                  # raising the mace and cocking it behind
        e = ease_io(s)
        A = blend(IDLE, WIND, e, +1, +1)
        f.append((hold(A, slerp(n_i, n_c, e), th_i + (th_w - th_i) * e), 80, None, False))
    f.append((hold(WIND, n_c, th_w), 160, None, True))
    for s in (0.35, 0.65):                                    # the blow comes down over the top
        A = dict(blend(WIND, HIT, s, -1, -1), ram_n="front")
        f.append((hold(A, n_c, th_w + (th_c - th_w) * s), 50, None, True))
    f.append((HIT, 220, 0.0, True))
    f.append((HIT, 140, 1.0, True))
    for s in (0.3, 0.6, 0.85):                                # the mace goes up again
        e = ease_io(s)
        A = blend(HIT, IDLE, e, 0, +1)
        f.append((hold(A, slerp(n_c, n_i, e), th_c + (th_i - th_c) * e), 100, None, False))
    return [(dict(A, spin=0.55 * i), dur, ft, fire) for i, (A, dur, ft, fire) in enumerate(f)]   # the barrels turn


def frame_parts(A, ft, fire, burst):
    G, info = GH.creature_parts(S, A, fx=False)
    if ft is not None:
        GH.col_mace_fx(G["fx"], info, ft)
    if fire:
        GH.col_gun_fx(G["fx"], info, 0.0 if ft is None else ft, burst=burst)
    return G, info


def sprite_of(G, k):
    cw, ch, cx, cy = S["canvas"]
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **GH.STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def main(k=3.5, PW=470, PH=300, SC=2, name="colossus_attack.gif"):
    WW, HH = PW, PH + 40
    bg = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 95) * 0.6 + value_noise(WW, HH, 5, 96) * 0.4
    th = BAYER[bg.yy % 4, bg.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        bg.rgb[lv == i] = hexc(col)
    line = timeline()
    _, hinfo = GH.creature_parts(S, HIT, fx=False)
    hit = S["hit"](hinfo)
    bug = W.build((), 0.02, "idle", True, k=k / 3.5, genes=W.genes_for(7))
    cx, by = int(PW * 0.34), PH - 56
    frames, durs = [], []
    for fi, (A, dur, ft, fire) in enumerate(line):
        G, info = frame_parts(A, ft, fire, burst=fi)
        bad = report(G, GH.BASE_ALLOWED + S.get("allow", []), skip=("fx",))
        if bad:
            print(fi, "clipping:", [(a, b, round(v, 2)) for v, a, b in bad])
        spr = sprite_of(G, k)
        sc = Scene(WW, HH)
        sc.rgb[:] = bg.rgb
        e = ((sc.xx - cx - 8) / (30 * k)) ** 2 + ((sc.yy - by) / (5 * k)) ** 2
        sc.rgb[e <= 1] *= 0.62
        dx, dy = to_screen((hit[0] + 1.0, 0.0, hit[2]), k)       # the target stands where the blow lands
        b, push = bug, 0
        if ft == 0.0:
            b = flash(bug, 0.75)
        elif ft == 1.0:
            b, push = flash(bug, 0.3), int(round(1.6 * k))
        bx, byy = int(cx + dx + push), int(by + dy)
        e = ((sc.xx - bx) / (3.3 * k / 3.5 * 2.2)) ** 2 + ((sc.yy - byy) / (k / 3.5 * 2.2)) ** 2
        sc.rgb[e <= 1] *= 0.62
        put(sc, b, bx, byy, mirror=True)
        sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
        img = sc.image(SC)
        d = ImageDraw.Draw(img)
        fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
        label = "Отец колосса · атака"
        d.text(((PW * SC - d.textlength(label, font=fh)) / 2, (PH + 6) * SC), label, font=fh, fill=(226, 186, 106))
        frames.append(img)
        durs.append(dur)
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames]
    path = out(name)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2, optimize=False)
    print(path, frames[0].size, len(frames), "frames")
    return frames, durs


if __name__ == "__main__":
    main()
