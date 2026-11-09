"""Attacks by the height of the target. Where a blow lands depends on how tall the enemy is next to the
attacker (the ratio of their heights on the battlefield):

    low   — the enemy is less than half as tall: the blow comes down to the ground;
    level — from half as tall to 1.6 times taller: the blow lands in the body, at about the attacker's chest;
    high  — 1.6 times taller and more: the blow goes up, into the belly of a giant.

Each band is its own contact pose (golems_h: S["bands"], humanoid: BANDS) with its own wind-up; the
in-betweens are interpolated and checked for clipping. Shown as duels in the battle scale: the target is
placed by its silhouette so its front is where the blow lands; it lights up there and is knocked back
(the Father of the Colossus is not: he is unstoppable).

    python3 tools/sprites/animate_duel.py            -> out/bands_<creature>.gif for every attacker, out/attack_bands.png
    python3 tools/sprites/animate_duel.py Молот      -> just one
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
from r3d import render
from noise import value_noise
import golems_h as GH
import humanoid as HM
import animate as AN
import animate_colossus as AC
import swarm1 as W
from animate import ease_io, to_screen, arc_lerp
from battle import put
from clipcheck import report
from paths import font, out

unit = AC.unit

# ---------------------------------------------------------------- targets, in the battle scale
TARGETS = {
    "soldier": dict(name="солдат роя", spr=lambda: W.build((), 0.02, "idle", True, k=1.0, genes=W.genes_for(7)), push=3),
    "queen": dict(name="матка", spr=lambda: W.queen(0.0, "idle", k=1.0), push=2),
    "guard": dict(name="Страж", spr=lambda: HM.build("idle", 2.2), push=4),
    "colossus": dict(name="титан", spr=lambda: GH.colossus_build("idle", 3.5), push=0, body=lambda: body_only(GH.COLOSSUS, 3.5)),
}


def body_only(S, k):
    """The creature without its arms and what they hold: where a blow can land on the body itself."""
    G, _ = GH.creature_parts(S, S["poses"]["idle"], fx=False)
    for key in list(G):
        if key.startswith(("arm_", "hand_", "item_")) or key == "fx":
            del G[key]
    cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
    spr = render(G.model().scaled(k), int(cw * k), int(ch * k), int(cx * k), int(cy * k), **GH.STYLE1)
    spr.ox, spr.oy = int(cx * k), int(cy * k)
    return spr
BAND_NAME = dict(low="сверху вниз", level="вровень", high="снизу вверх")


# ---------------------------------------------------------------- golems_h creatures: numbers between poses
DIRS = ("mace_dir", "hammer_dir", "face", "trowel_dir")


def gblend(A0, A1, s, way, arcs):
    """Numbers between two poses: the hands in `arcs` and the held tools turn round the shoulder `way`."""
    A = AC.blend(A0, A1, s, way, way, arcs=arcs)
    for k in DIRS:
        if k in A0 and k in A1:
            A[k] = tuple(unit(arc_lerp(A0[k], A1[k], s, "xy", way)))
    for k in ("open", "spin"):
        if k in A0 and k in A1:
            A[k] = A0[k] + (A1[k] - A0[k]) * s
    return A


def clean(S, A, ft=None):
    """A frame that clips gets the other side for its arm rams, or its hands moved a little outwards."""
    if ft is not None:
        return A
    S["poses"]["_t"] = dict(A, fx=None)
    if not GH.check(S, "_t"):
        return A
    tries = [dict(A, ram_n=rn, ram_f=rf) for rn in ("back", "front") for rf in ("back", "front")]
    for out_ in (1.0, 2.0, 3.0, 4.0):
        for B in list(tries[:4]):
            C = dict(B)
            for k in ("n", "f"):
                h = np.array(C["hand_" + k], float)
                h[2] += out_ if k == "n" else -out_
                C["hand_" + k] = tuple(h)
            tries.append(C)
    for B in tries:
        S["poses"]["_t"] = dict(B, fx=None)
        if not GH.check(S, "_t"):
            return B
    return A


def strike_line(S, wind, X, way, arcs):
    """Idle, the wind-up, the blow, contact, a moment later, back to idle."""
    I = dict(S["poses"]["idle"], fx=None)
    f = [(I, 420, None)]
    for s in (1 / 3, 2 / 3):
        f.append((gblend(I, wind, ease_io(s), 0, arcs), 80, None))
    f.append((wind, 160, None))
    for s in (0.35, 0.65):
        f.append((gblend(wind, X, s, way, arcs), 50, None))
    f.append((X, 220, 0.0))
    f.append((X, 140, 1.0))
    for s in (0.3, 0.6, 0.85):
        f.append((gblend(X, I, ease_io(s), 0, arcs), 100, None))
    return [(clean(S, A, ft), dur, ft) for A, dur, ft in f]


def shot_line(S, X, arcs=("n", "f")):
    """A gunner: raise the weapon to the target, hold, fire, the recoil, back to idle."""
    I = dict(S["poses"]["idle"], fx=None)
    aim = dict(X, fx=None)
    kick = dict(X, t=tuple(np.asarray(X["t"], float) - (0.8, 0.0, 0.0)), lean=X["lean"] + 0.05)
    f = [(I, 420, None)]
    for s in (1 / 3, 2 / 3):
        f.append((gblend(I, aim, ease_io(s), 0, arcs), 80, None))
    f.append((aim, 160, None))
    f.append((aim, 50, None))
    f.append((aim, 50, None))
    f.append((X, 220, 0.0))
    f.append((kick, 140, 1.0))
    for s in (0.3, 0.6, 0.85):
        f.append((gblend(kick, I, ease_io(s), 0, arcs), 100, None))
    return [(clean(S, A, ft), dur, ft) for A, dur, ft in f]


def golem_frame(S):
    def frame(A, ft, i):
        G, info = GH.creature_parts(S, A, fx=False)
        if ft is not None:
            S["fx"](G["fx"], dict(A, fx=True), info, S, ft)
        return G, info
    return frame


def golem_sprite(S):
    def sprite(G, k):
        cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
        w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
        spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **GH.STYLE1), col="#b8bcc6", k=0.55)
        spr.ox, spr.oy = ox, oy
        return spr
    return sprite


def golem_check(S):
    return lambda G: report(G, GH.BASE_ALLOWED + S.get("allow", []), skip=("fx",))


# ---------------------------------------------------------------- the wind-ups
MO, MS, MN = GH.MOLOT, GH.MASON, GH.MANIAC
MO_I, MS_I, MN_I = MO["poses"]["idle"], MS["poses"]["idle"], MN["poses"]["idle"]
WIND = dict(
    molot_low=dict(MO_I, lean=0.12, twist=0.0, t=(-0.6, -0.6, 0.0), hand_n=(1.5, 13.0, 3.5), hand_f=(0.5, 13.0, -3.5),
                   pole_n=(-0.2, 0.3, 1.0), pole_f=(-0.2, 0.3, -1.0), ram_n="front", ram_f="front"),
    molot_level=dict(MO_I, lean=0.06, twist=0.15, t=(-0.6, -0.6, 0.0), hand_n=(-5.0, -6.0, 5.0), hand_f=(-4.0, -8.0, -6.0),
                     pole_n=(-0.6, 0.6, 1.0), pole_f=(-0.6, 0.6, -1.0), ram_n="back", ram_f="back"),
    molot_high=dict(MO_I, lean=-0.2, twist=0.05, t=(0.0, -2.6, 0.0), hand_n=(-2.0, -14.5, 4.0), hand_f=(-3.0, -14.5, -4.0),
                    pole_n=(-0.6, 0.2, 1.0), pole_f=(-0.6, 0.2, -1.0), ram_n="back", ram_f="back"),
    mason=dict(MS_I, lean=0.08, twist=0.18, t=(-0.4, -0.5, 0.0), hand_n=(-1.5, 10.0, 2.5), pole_n=(-0.6, 0.0, 1.0),
               hammer_dir=(-0.8, 0.3, 0.1), face=(0.2, 1.0, 0.0), hand_f=(3.0, -10.4, -3.4), ram_n="front"),
    maniac_over=dict(MN_I, lean=0.08, twist=0.18, t=(-0.4, -0.5, 0.0), hand_n=(1.0, 11.0, 3.0), pole_n=(-0.6, 0.0, 1.0),
                     hand_f=(5.0, -9.0, -2.0), ram_n="front", spin=0.6),
    maniac_under=dict(MN_I, lean=-0.12, twist=0.15, t=(-0.4, -1.4, 0.0), hand_n=(-4.0, -11.0, 3.5), pole_n=(-0.6, 0.3, 1.0),
                      hand_f=(5.0, -9.0, -2.0), ram_n="back", spin=0.6),
)


def melee(S, band, wind, way, arcs):
    X = dict(S["poses"][S["bands"][band]], fx=True)
    return lambda: strike_line(S, dict(WIND[wind], fx=None), X, way, arcs)


def gunner(S, band, arcs=("n", "f")):
    X = dict(S["poses"][S["bands"][band]], fx=True)
    return lambda: shot_line(S, X, arcs)


# ---------------------------------------------------------------- the Guard and the Father of the Colossus
def guard_line(kind):
    def line():
        return [(A, dur, ft) for A, dur, ft, tr, seg in AN.timeline(kind)]
    return line


def guard_frame(A, ft, i):
    G, info = HM.pose_parts(A, fx=False)
    if ft is not None:
        HM.impact(G["fx"], A, ft, info)
    return G, info


def colossus_line(band):
    X = dict(GH.COLOSSUS["poses"][GH.COLOSSUS["bands"][band]], fx=None)
    return lambda: [(clean(GH.COLOSSUS, A, ft) if i else A, dur, ft) for i, (A, dur, ft, fire) in enumerate(AC.timeline(X))]


def colossus_frame(A, ft, i):
    return AC.frame_parts(A, ft, 3 <= i <= 7, i)


ATTACKERS = {
    "Страж": dict(file="guard", frame=guard_frame, sprite=AN.sprite_of, strike=lambda info: info["face"],
                  check=lambda G: report(G, HM.ALLOWED, skip=("sparks", "fx")),
                  panels=[("low", "soldier", guard_line("slam")), ("level", "queen", guard_line("level")),
                          ("high", "colossus", guard_line("high"))]),
    "Молот": dict(file="molot", S=MO, panels=[("low", "soldier", melee(MO, "low", "molot_low", -1, ("n", "f"))),
                                              ("level", "queen", melee(MO, "level", "molot_level", 0, ("n", "f"))),
                                              ("high", "colossus", melee(MO, "high", "molot_high", +1, ("n", "f")))]),
    "Горн": dict(file="gorn", S=GH.GORN, panels=[("low", "soldier", gunner(GH.GORN, "low", ("n",))),
                                                 ("level", "queen", gunner(GH.GORN, "level", ("n",))),
                                                 ("high", "colossus", gunner(GH.GORN, "high", ("n",)))]),
    "Орудие": dict(file="orudie", S=GH.ORUDIE, panels=[("low", "soldier", gunner(GH.ORUDIE, "low")),
                                                       ("level", "queen", gunner(GH.ORUDIE, "level")),
                                                       ("high", "colossus", gunner(GH.ORUDIE, "high"))]),
    "Маньяк": dict(file="maniac", S=MN, panels=[("low", "soldier", melee(MN, "low", "maniac_over", -1, ("n",))),
                                                ("level", "queen", melee(MN, "level", "maniac_over", -1, ("n",))),
                                                ("high", "colossus", melee(MN, "high", "maniac_under", +1, ("n",)))]),
    "Каменщик": dict(file="mason", S=MS, panels=[("level", "soldier", melee(MS, "level", "mason", -1, ("n",))),
                                                 ("high", "queen", melee(MS, "high", "mason", -1, ("n",)))]),
    "Отец колосса": dict(file="colossus", S=GH.COLOSSUS, frame=colossus_frame,
                         panels=[("low", "soldier", colossus_line("low")), ("level", "guard", colossus_line("level"))]),
}
SCALE = {"Страж": 2.2, "Молот": 1.6, "Горн": 1.6, "Орудие": 1.6, "Маньяк": 1.3, "Каменщик": 0.85, "Отец колосса": 3.5}


# ---------------------------------------------------------------- the duel scene
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
    H, Wd = sc.rgb.shape[:2]
    m = np.zeros((H, Wd), bool)
    ys, xs = np.nonzero(spr.a)
    ys, xs = ys + y0, xs + x0
    ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < Wd)
    m[ys[ok], xs[ok]] = True
    d = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                d |= np.roll(np.roll(m, dy, 0), dx, 1)
    ring = d & ~m & sc.occ
    sc.rgb[ring] *= k


def background(Wd, H, seed=95):
    bg = Scene(Wd, H)
    n = value_noise(Wd, H, 14, seed) * 0.6 + value_noise(Wd, H, 5, seed + 1) * 0.4
    th = BAYER[bg.yy % 4, bg.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        bg.rgb[lv == i] = hexc(col)
    return bg


def shadow(sc, x, y, rx, ry):
    e = ((sc.xx - x) / rx) ** 2 + ((sc.yy - y) / ry) ** 2
    sc.rgb[e <= 1] *= 0.62


def front_at(spr, row):
    """The frontmost column of the sprite (facing right) on a row, looking a few rows up and down if empty."""
    for d in range(0, 40):
        for r in (row - d, row + d):
            if 0 <= r < spr.h and spr.a[r].any():
                return int(np.nonzero(spr.a[r])[0].max())
    return int(np.nonzero(spr.a.any(axis=0))[0].max())


def panel(who, band, tname, line, BW=1000, BH=560):
    """Frames of one duel on a wide canvas, then cropped to what is drawn."""
    A_ = ATTACKERS[who]
    k = SCALE[who]
    S = A_.get("S")
    frame = A_.get("frame") or golem_frame(S)
    sprite = A_.get("sprite") or golem_sprite(S)
    check = A_.get("check") or golem_check(S)
    strike = A_.get("strike") or S["strike"]
    seq = line()
    i_hit = next(i for i, (A, dur, ft) in enumerate(seq) if ft == 0.0)
    _, hinfo = frame(seq[i_hit][0], None, 0)
    c = strike(hinfo)
    T = TARGETS[tname]
    tgt = T["spr"]()
    cx, by = int(BW * 0.3), BH - 70
    hx, hy = to_screen(c, k)
    gy = by + to_screen((c[0], 0.0, c[2]), k)[1]               # the target stands under the point of contact
    fx_, fy_ = cx + hx, by + hy
    body = T["body"]() if "body" in T else tgt                  # the front of its body, not of its weapons
    cf = front_at(body, int(round(fy_ - gy + tgt.oy)))
    bite = 2
    tx, ty = fx_ - bite - tgt.ox + cf, gy
    lx, ly = tgt.ox - (fx_ - tx), fy_ - ty + tgt.oy             # the struck spot in the target's own pixels
    bg = background(BW, BH)
    scenes, durs = [], []
    for i, (A, dur, ft) in enumerate(seq):
        G, info = frame(A, ft, i)
        bad = check(G)
        if bad:
            print(who, band, i, "clipping:", [(a, b, round(v, 2)) for v, a, b in bad])
        spr = sprite(G, k)
        sc = Scene(BW, BH)
        sc.rgb[:] = bg.rgb
        t, push = tgt, 0
        if ft is not None:
            t = struck(tgt, lx, ly, 6 + 2.2 * np.sqrt(tgt.w), 0.75 if ft == 0.0 else 0.3)
            push = T["push"] if ft == 1.0 else 0
        shadow(sc, tx + push - 0.1 * tgt.w, ty, 0.36 * tgt.w, 0.06 * tgt.w + 3)
        shadow(sc, cx + 4 * k, by, 24 * k, 4.5 * k)
        put(sc, t, tx + push, ty, mirror=True)
        halo(sc, spr, int(cx - spr.ox), int(by - spr.oy))
        sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
        scenes.append(sc)
        durs.append(dur)
    occ = np.zeros((BH, BW), bool)
    for sc in scenes:
        occ |= sc.occ
    ys, xs = np.nonzero(occ)
    x0, x1 = max(0, xs.min() - 14), min(BW, xs.max() + 15)
    y0, y1 = max(0, ys.min() - 12), min(BH, max(ys.max(), by + 6) + 10)
    label = f"{BAND_NAME[band]}: {T['name']}"
    return [sc.image(1).crop((x0, y0, x1, y1)) for sc in scenes], durs, label, i_hit


def attacker_gif(who, SC=2):
    A_ = ATTACKERS[who]
    panels = [panel(who, band, tname, line) for band, tname, line in A_["panels"]]
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
    ft_ = ImageFont.truetype(font("PTSerif-Bold.ttf"), 26)
    gap, top, foot = 16, 48, 40
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    slot = [max(p[0][0].width * SC, int(probe.textlength(p[2], font=fh)) + 16) for p in panels]   # room for the label
    Wd = sum(slot) + gap * (len(panels) + 1)
    Hh = max(p[0][0].height for p in panels) * SC + top + foot
    n = len(panels[0][0])
    imgs = []
    for i in range(n):
        img = Image.new("RGB", (Wd, Hh), (24, 18, 30))
        d = ImageDraw.Draw(img)
        d.text((gap, 8), f"{who}: атака по росту цели", font=ft_, fill=(236, 214, 160))
        x = gap
        for (frames, durs, label, i_hit), sw in zip(panels, slot):
            im = frames[i].resize((frames[i].width * SC, frames[i].height * SC), Image.NEAREST)
            img.paste(im, (x + (sw - im.width) // 2, Hh - foot - im.height))
            d.text((x + (sw - d.textlength(label, font=fh)) / 2, Hh - foot + 6), label, font=fh, fill=(226, 186, 106))
            x += sw + gap
        imgs.append(img)
    durs = panels[0][1]
    import os, json
    os.makedirs(out("bands"), exist_ok=True)                  # the contact frames, for the sheet
    for (band, _, _), (frames, _, label, i_hit) in zip(A_["panels"], panels):
        frames[i_hit].save(out(f"bands/{A_['file']}_{band}.png"))
        json.dump(label, open(out(f"bands/{A_['file']}_{band}.json"), "w"), ensure_ascii=False)
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in imgs]
    path = out(f"bands_{A_['file']}.gif")
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2, optimize=False)
    print(path, imgs[0].size, n, "frames")
    return panels


def sheet():
    """The contact frames of every attacker and band on one sheet (from out/bands, written with the gifs)."""
    import json
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 15)
    fn = ImageFont.truetype(font("PTSerif-Bold.ttf"), 18)
    cols = ("low", "level", "high")
    rows = []
    for who, A_ in ATTACKERS.items():
        bands = [b for b, _, _ in A_["panels"]]
        rows.append((who, {b: (Image.open(out(f"bands/{A_['file']}_{b}.png")).convert("RGB"),
                               json.load(open(out(f"bands/{A_['file']}_{b}.json")))) for b in bands}))
    colw = [max((r[1][c][0].width for r in rows if c in r[1]), default=0) for c in cols]
    left, gap, lab = 130, 14, 24
    Wd = left + sum(colw) + gap * 4
    hs = [max(im.height for im, _ in r[1].values()) + lab + gap for r in rows]
    img = Image.new("RGB", (Wd, sum(hs) + 50), (24, 18, 30))
    d = ImageDraw.Draw(img)
    d.text((gap, 12), "Атака по росту цели: кадры удара", font=fn, fill=(236, 214, 160))
    y = 50
    for (who, ims), h in zip(rows, hs):
        d.text((gap, y + 6), who, font=fn, fill=(236, 214, 160))
        for j, c in enumerate(cols):
            if c not in ims:
                continue
            im, label = ims[c]
            xj = left + sum(colw[:j]) + gap * j
            img.paste(im, (xj, y + h - lab - gap - im.height))
            d.text((xj, y + h - lab - gap + 4), label, font=fh, fill=(226, 186, 106))
        y += h
    path = out("attack_bands.png")
    img.save(path)
    print(path, img.size)


if __name__ == "__main__":
    if sys.argv[1:] == ["sheet"]:
        sheet()
    else:
        for who in sys.argv[1:] or list(ATTACKERS):
            attacker_gif(who)
        if not sys.argv[1:]:
            sheet()
