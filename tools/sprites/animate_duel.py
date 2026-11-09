"""Attacks by the size of the target. Where a blow lands depends on how much bigger or smaller the enemy is
than the attacker (the difference of sizes, the threshold is 2 — as for trampling):

    low   — the enemy is smaller by 2 and more: the blow comes down to the ground (the attack every frame has);
    level — about the same size (-1..+1): the blow lands in the body, at chest height;
    high  — the enemy is bigger by 2 and more: the blow goes up, into its belly.

Each band is its own contact pose (golems_h: S["bands"]); the wind-up is shared, the in-betweens are
interpolated. Shown here as duels in the battle scale, the target standing where the blow lands:

    python3 tools/sprites/animate_duel.py      -> out/attack_bands.gif
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
from r3d import render
from noise import value_noise
import golems_h as GH
import humanoid as HM
import animate_colossus as AC
from animate import ease_io, to_screen
from battle import put
from clipcheck import report
from paths import font, out

# ---------------------------------------------------------------- Молот: the wind-up of the upward blow
MOLOT = GH.MOLOT
M_IDLE = dict(MOLOT["poses"]["idle"], fx=None)
M_WIND = dict(M_IDLE, lean=-0.2, twist=0.05, t=(0.0, -2.6, 0.0), hand_n=(-2.0, -14.5, 4.0), hand_f=(-3.0, -14.5, -4.0),
              pole_n=(-0.6, 0.2, 1.0), pole_f=(-0.6, 0.2, -1.0), ram_n="back", ram_f="back")
BOTH = ("n", "f")


def clean(S, A, ft=None):
    """An in-between that clips gets the other side for its arm rams, or its hands moved a little outwards."""
    if ft is not None:
        return A
    S["poses"]["_t"] = dict(A, fx=None)
    if not GH.check(S, "_t"):
        return A
    sides = [k for k in ("n", "f") if "hand_" + k in A]
    tries = []
    for rn in ("back", "front"):
        for rf in ("back", "front"):
            tries.append(dict(A, ram_n=rn, ram_f=rf))
    for out_ in (1.0, 2.0, 3.0):
        for B in list(tries[:4]):
            C = dict(B)
            for k in sides:
                h = np.array(C["hand_" + k], float)
                h[2] += out_ if k == "n" else -out_
                C["hand_" + k] = tuple(h)
            tries.append(C)
    for B in tries:
        S["poses"]["_t"] = dict(B, fx=None)
        if not GH.check(S, "_t"):
            return B
    return A


def molot_timeline(hit):
    """Crouch with the fists down by the hips, then both fists swing forward and up into the enemy."""
    f = [(M_IDLE, 420, None)]
    for s in (1 / 3, 2 / 3):
        f.append((AC.blend(M_IDLE, M_WIND, ease_io(s), 0, 0, arcs=BOTH), 80, None))
    f.append((M_WIND, 160, None))
    for s in (0.35, 0.65):
        f.append((AC.blend(M_WIND, hit, s, +1, 0, arcs=BOTH), 50, None))
    f.append((hit, 220, 0.0))
    f.append((hit, 140, 1.0))
    for s in (0.3, 0.6, 0.85):
        f.append((AC.blend(hit, M_IDLE, ease_io(s), 0, 0, arcs=BOTH), 100, None))
    return [(clean(MOLOT, A, ft), dur, ft) for A, dur, ft in f]


def molot_frame(A, ft, i):
    G, info = GH.creature_parts(MOLOT, A, fx=False)
    if ft is not None:
        GH.molot_fx(G["fx"], A, info, MOLOT, ft)
    return G, info


def colossus_timeline(hit):
    return [(clean(GH.COLOSSUS, A, ft) if i else A, dur, ft) for i, (A, dur, ft, fire) in enumerate(AC.timeline(hit))]


def colossus_frame(A, ft, i):
    fire = 3 <= i <= 7
    return AC.frame_parts(A, ft, fire, i)


# ---------------------------------------------------------------- the duel scene
def sprite_of(S, G, k):
    cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **GH.STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


def struck(spr, x, y, r, k=0.7):
    """The target lit up where the blow lands (x, y: pixels in the sprite)."""
    f = Sprite(spr.w, spr.h)
    yy, xx = np.mgrid[0:spr.h, 0:spr.w]
    w = np.clip(1.0 - np.hypot(xx - x, yy - y) / r, 0, 1)[..., None] * k
    f.rgb, f.a = spr.rgb * (1 - w) + 245 * w, spr.a.copy()
    f.ox, f.oy = spr.ox, spr.oy
    return f


def halo(sc, spr, x0, y0, r=2, k=0.45):
    """A dark ring round the sprite where it overlaps what is already drawn: one creature stays readable in
    front of another as dark as itself."""
    H, W = sc.rgb.shape[:2]
    m = np.zeros((H, W), bool)
    ys, xs = np.nonzero(spr.a)
    ys, xs = ys + y0, xs + x0
    ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
    m[ys[ok], xs[ok]] = True
    d = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                d |= np.roll(np.roll(m, dy, 0), dx, 1)
    ring = d & ~m & sc.occ
    sc.rgb[ring] *= k


def background(W, H):
    bg = Scene(W, H)
    n = value_noise(W, H, 14, 95) * 0.6 + value_noise(W, H, 5, 96) * 0.4
    th = BAYER[bg.yy % 4, bg.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        bg.rgb[lv == i] = hexc(col)
    return bg


def shadow(sc, x, y, rx, ry):
    e = ((sc.xx - x) / rx) ** 2 + ((sc.yy - y) / ry) ** 2
    sc.rgb[e <= 1] *= 0.62


DUELS = [
    dict(label="Отец колосса (7) бьёт Стража (6) · вровень",
         S=GH.COLOSSUS, k=3.5, hit="attack_level", line=colossus_timeline, frame=colossus_frame,
         target=lambda: HM.build("idle", 2.2), kt=2.2, point=lambda y: (HM.chest_front(y) - 0.4, y, 0.0), push=4,
         W=430, cx=0.36),
    dict(label="Молот (5) бьёт Отца колосса (7) · снизу вверх",
         S=MOLOT, k=1.6, hit="attack_high", line=molot_timeline, frame=molot_frame,
         target=lambda: GH.colossus_build("idle", 3.5), kt=3.5, point=lambda y: (4.0, y, 10.0), push=0,
         W=430, cx=0.3),
]


def panel(D, PH):
    """Frames of one duel: (list of Scenes, durations)."""
    S, k, kt = D["S"], D["k"], D["kt"]
    hit = dict(S["poses"][D["hit"]], fx=True)
    line = D["line"](hit)
    _, hinfo = D["frame"](hit, None, 0)
    c = S["strike"](hinfo)                                     # where the blow lands (attacker's model)
    pt = D["point"](c[1] * k / kt)                             # ... and the same spot on the target
    tgt = D["target"]()
    W, H = D["W"], PH + 40
    bg = background(W, H)
    cx, by = int(W * D["cx"]), PH - 40
    hx, hy = to_screen(c, k)
    sx, sy = to_screen(pt, kt)
    tx, ty = cx + hx + sx, by + hy - sy                        # the target is drawn mirrored, facing the attacker
    fx_, fy_ = cx + hx, by + hy
    frames, durs = [], []
    for i, (A, dur, ft) in enumerate(line):
        G, info = D["frame"](A, ft, i)
        bad = report(G, GH.BASE_ALLOWED + S.get("allow", []), skip=("fx",))
        if bad:
            print(D["label"], i, "clipping:", [(a, b, round(v, 2)) for v, a, b in bad])
        spr = sprite_of(S, G, k)
        sc = Scene(W, H)
        sc.rgb[:] = bg.rgb
        t, push = tgt, 0
        if ft is not None:
            # the struck spot, in the mirrored target sprite's own pixels
            lx = tgt.w - 1 - (tgt.w - 1 - tgt.ox + (fx_ - tx))
            t = struck(tgt, lx, fy_ - ty + tgt.oy, 8 * kt, 0.75 if ft == 0.0 else 0.3)
            push = D["push"] if ft == 1.0 else 0
        shadow(sc, tx + push - 4 * kt, ty, 24 * kt, 4.5 * kt)
        shadow(sc, cx + 4 * k, by, 24 * k, 4.5 * k)
        put(sc, t, tx + push, ty, mirror=True)
        halo(sc, spr, int(cx - spr.ox), int(by - spr.oy))
        sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
        frames.append(sc)
        durs.append(dur)
    return frames, durs


def main(PH=330, SC=2, name="attack_bands.gif"):
    panels = [panel(D, PH) for D in DUELS]
    n = len(panels[0][0])
    W = max(D["W"] for D in DUELS)
    H = PH + 40
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
    imgs = []
    for i in range(n):
        img = Image.new("RGB", (W * SC, H * SC * len(panels)))
        for j, (D, (frames, _)) in enumerate(zip(DUELS, panels)):
            im = frames[i].image(SC)
            img.paste(im, (0, j * H * SC))
            d = ImageDraw.Draw(img)
            d.text(((W * SC - d.textlength(D["label"], font=fh)) / 2, (j * H + PH + 4) * SC), D["label"], font=fh,
                   fill=(226, 186, 106))
        imgs.append(img)
    durs = panels[0][1]
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in imgs]
    path = out(name)
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2, optimize=False)
    print(path, imgs[0].size, len(imgs), "frames")
    return imgs, durs


if __name__ == "__main__":
    main()
