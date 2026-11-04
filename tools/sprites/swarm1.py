"""Swarm creatures in style 1.

The first (dominant) trait decides the body plan, so silhouettes differ a lot:
  ()        ant          wings    wasp          stinger  scorpion       acid     honeypot
  horn      beetle       carapace isopod        jumper   grasshopper    scythes  mantis
  firefly   firefly
Further traits add parts to whatever body there is. Colour (hue) and proportions are inherited.
Castes: worker (size 1), soldier (size 2), queen (size 6). Mutation "giant" adds +1 size.
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3

STYLE1 = dict(amb=0.40, dif=0.60, gradient=False, edges=False, outline_tint=0.22)

M_BONE = Mat(BONE)
M_EYE = Mat(GLOWG, emissive=hexc("#9af060"), glow_r=5, glow_k=0.4)
M_DARKEYE = Mat(ramp("#08060a", "#141018", "#221c2a", "#3a3046", "#8a7aa0"))
M_WING = Mat(ramp("#2e2a48", "#4c4874", "#76729e", "#a6a2cc", "#d4d0ee"), dither=True)
M_WING_NEAR = Mat(ramp("#3a3658", "#5c5888", "#8a86b8", "#b8b4de", "#e2def8"))
M_VEIN = Mat(ramp("#1c1830", "#2c2848", "#403c64", "#56527e", "#6e6a98"))
M_ACID = Mat(GLOWG, emissive=hexc("#8af04a"), glow_r=9, glow_k=0.55)
M_ACID_BELLY = Mat(ramp("#1e3a14", "#2e6a20", "#4aa030", "#86d050", "#cff59a"), emissive=hexc("#7ae040"), glow_r=16, glow_k=0.45)
M_ACID_SPIT = Mat(GLOWG, emissive=hexc("#a8ff60"), glow_r=12, glow_k=0.8)
M_LANTERN = Mat(ramp("#4a4410", "#8a7a18", "#d0b830", "#f4e870", "#fffcd0"), emissive=hexc("#f0e060"), glow_r=15, glow_k=0.75)
M_EGG = Mat(ramp("#2a3a20", "#4a6a2e", "#76a040", "#a8d060", "#e0f6a0"), emissive=hexc("#80d040"), glow_r=0, glow_k=0)
M_MEMBRANE = Mat(ramp("#2a1e34", "#45304f", "#664a6e", "#8a6a90", "#b08eb4"))
AMBER = ramp("#2a1606", "#5a3008", "#9a5c10", "#d8962a", "#f6d070")
ELYTRA = ramp("#1e0c1a", "#4a1430", "#7a2a3a", "#b4543e", "#e8a060")
CRIMSON = ramp("#1e060c", "#480e1a", "#7a1c28", "#b0343a", "#e06a5a")

TRAITS = ("wings", "stinger", "acid", "horn", "carapace", "jumper", "scythes", "firefly")
NAMES = dict(wings="Крылья", stinger="Жало", acid="Кислотная железа", horn="Рог", carapace="Панцирь",
             jumper="Прыгучие ноги", scythes="Серпы", firefly="Светлячок", giant="Гигантизм")
PLANS = dict(wings="Оса", stinger="Скорпион", acid="Бочонок", horn="Жук", carapace="Мокрица",
             jumper="Кузнечик", scythes="Богомол", firefly="Светляк")


def pivot(m, R, p):
    p = np.array(p, float)
    return m.transformed(R, p - R @ p)


def spike(m, a, b, r, mat=M_BONE):
    m.cyl(a, b, r, mat, r1=0.12, seg=5)


def genes_for(seed):
    """Inherited proportions: gaster, head, legs. Kept within a range that still reads well."""
    rng = np.random.default_rng(seed)
    return dict(gs=rng.uniform(0.85, 1.2), hsz=rng.uniform(0.88, 1.18), leg=rng.uniform(0.85, 1.2))


def leg_pairs(m, mc, y0, xs, spread, length, lift, pose, skip=(), fore_lift=False):
    for side in (1, -1):
        band = 3 if side > 0 else 1
        for i, (x, dx) in enumerate(xs):
            if i in skip:
                continue
            hip = np.array((x, y0 - 1.0, 1.3 * side))
            knee = np.array((x + dx * 0.8, y0 + 1.6 * length, 3.4 * side * spread))
            foot = np.array((x + dx * 1.4, lift, 5.2 * side * spread))
            if pose == "attack" and fore_lift and i == len(xs) - 1:
                knee = np.array((x + 3.5, y0 + 4.0, 3.4 * side))
                foot = np.array((x + 6.0, y0 + 2.2, 4.2 * side))
            m.limb([hip, knee], 1, mc, band=band)
            m.limb([knee, foot], 1, mc, band=band - 1 if side > 0 else 1)


def antennae(m, mc, a0, back=False, long=1.0):
    for z in (0.5, -0.5):
        p0 = a0 + np.array((0, 0, z))
        if back:
            pts = [p0, p0 + (-1.0, 3.0 * long, z * 1.2), p0 + (-7.0 * long, 5.5 * long, z * 3.0)]
        else:
            pts = [p0, p0 + (0.2, 3.0 * long, z * 0.6), p0 + (3.2 * long, 3.6 * long, z * 2.4)]
        m.limb(pts, 1, mc, band=3 if z > 0 else 1)


def mandibles(m, mat, hc, hs, jaw):
    for z in (1.0, -1.0):
        base = hc + (1.6 * hs, -0.9 * hs, z * 0.5 * hs)
        L = 2.3 * hs
        tip = base + np.array((np.cos(jaw) * L, -0.5, np.sign(z) * np.sin(jaw) * L * 0.8))
        m.cyl(base, tip, 0.55 * hs, mat, r1=0.12, seg=4)


def rings(m, center, R, length, radius, mat, n=3):
    """Thin bands around an ellipsoid (semi-axis `length` along local x, `radius` across): stripes."""
    for i in range(n):
        t = (i + 1) / (n + 1) * 2 - 1           # -1..1 along the axis
        x = t * length * 0.8
        rr = radius * np.sqrt(max(0.0, 1 - (x / length) ** 2)) + 0.35
        c = np.array(center) + R @ np.array((x, 0, 0))
        m.ell(c, (0.6, rr, rr), mat, R)


# ------------------------------------------------------------------ body plans
def plan_ant(m, mc, g, pose, soldier):
    y0 = 6.5 * g["leg"]
    gs, hs = g["gs"], g["hsz"] * (1.45 if soldier else 1.0)
    jaw = 0.25 if pose == "idle" else 0.7
    gc = np.array((-6.8, y0 + 0.4, 0))
    m.ell(gc, (5.2 * gs, 3.9 * gs, 3.9 * gs), mc, rot_z(0.25))
    m.ell((-2.4, y0 + 0.2, 0), (0.9, 1.3, 0.9), mc)
    m.ell((0.6, y0 + 0.9, 0), (3.0, 2.1, 2.0), mc, rot_z(0.22))
    hc = np.array((4.3 + (hs - 1) * 1.6, y0 + 1.6, 0))
    m.ell(hc, (2.3 * hs, 2.1 * hs, 2.1 * hs), mc)
    for z in (1.2, -1.2):
        m.ell(hc + (0.9 * hs, 0.5 * hs, z * hs), (0.55, 0.55, 0.55), M_EYE)
    mandibles(m, M_BONE if soldier else mc, hc, hs, jaw)
    antennae(m, mc, hc + (0.8 * hs, 1.3 * hs, 0))
    if soldier:
        m.box(hc + (0, 1.5 * hs, 0), (3.2, 0.8, 2.6), M_BONE, rot_z(-0.2))
    leg_pairs(m, mc, y0, ((-1.6, -3.2), (0.4, 0.3), (2.4, 3.4)), 1.25 if soldier else 1.0, g["leg"], 0, pose, fore_lift=True)
    return dict(y0=y0, hc=hc, hs=hs, tip=gc + (-5.2 * gs, -1.4, 0), gc=gc, gr=3.9 * gs,
                back=[(-9.0, y0 + 3.9 * gs), (-6.6, y0 + 4.3 * gs), (-4.2, y0 + 3.8 * gs), (-0.4, y0 + 3), (1.8, y0 + 2.8)],
                wing=np.array((0.8, y0 + 2.6, 0)), hind=np.array((-1.4, y0 - 1.0, 0)), fore=np.array((2.4, y0 + 0.2, 0)),
                length=14)


def plan_wasp(m, mc, g, pose, soldier):
    y0 = 7.0
    gs, hs = g["gs"], g["hsz"]
    stripe = Mat(AMBER)
    m.ell((0.8, y0 + 1.2, 0), (3.0, 2.3, 2.1), mc, rot_z(0.2))
    m.cyl((-2.0, y0 + 0.6, 0), (-4.4, y0 - 0.4, 0), 0.55, mc, seg=6)
    R = rot_z(0.42 if pose == "idle" else 0.9)
    gc = np.array((-9.0, y0 - 1.6, 0))
    m.ell(gc, (5.8 * gs, 2.6 * gs, 2.6 * gs), stripe, R)
    rings(m, gc, R, 5.8 * gs, 2.6 * gs, mc, n=4)
    hc = np.array((4.5, y0 + 1.6, 0))
    m.ell(hc, (2.0 * hs, 2.1 * hs, 2.3 * hs), mc)
    for z in (1.4, -1.4):
        m.ell(hc + (0.5, 0.6, z * hs), (1.1, 1.4, 0.8), M_DARKEYE)
    mandibles(m, Mat(AMBER), hc, hs * 0.8, 0.3 if pose == "idle" else 0.7)
    antennae(m, mc, hc + (0.6, 1.6 * hs, 0), long=1.2)
    tip = gc + R @ np.array((-5.8 * gs, 0, 0))
    leg_pairs(m, mc, y0, ((-1.2, -2.0), (0.6, 0.2), (2.2, 2.6)), 0.9, 0.9, y0 - 4.5, pose)
    return dict(y0=y0, hc=hc, hs=hs, tip=tip, gc=gc, gr=2.6 * gs, back=[(-6, y0 + 1.5), (-2, y0 + 3.2), (1, y0 + 3.4)],
                wing=np.array((0.8, y0 + 2.9, 0)), hind=np.array((-1.2, y0 - 0.8, 0)), fore=np.array((2.2, y0 + 0.4, 0)),
                length=16, hover=0.0, built_wings=True)


def plan_scorpion(m, mc, g, pose, soldier):
    y0 = 4.6 * g["leg"]
    hs = g["hsz"]
    tail = Mat(chitin_shift(mc, 0.06))
    m.ell((-1.5, y0 + 0.6, 0), (4.6, 2.2, 3.0), mc)                 # flat body
    hc = np.array((3.8, y0 + 0.8, 0))
    m.ell(hc, (2.2 * hs, 1.6 * hs, 2.4 * hs), mc)
    for z in (0.8, -0.8):
        m.ell(hc + (1.4, 0.8, z), (0.45, 0.45, 0.45), M_EYE)
    # pincers
    for z in (2.0, -2.0):
        a = hc + (0.5, -0.2, z)
        b = a + (3.4, 0.6, np.sign(z) * 1.6)
        m.cyl(a, b, 0.7, mc, seg=5)
        m.ell(b + (1.2, 0.2, 0), (1.6, 1.0, 1.0), M_BONE)
        spike(m, b + (2.2, 0.4, 0), b + (3.6, 0.2, -np.sign(z) * 0.6), 0.35)
    pts = [(-5.5, y0 + 1.6), (-8.0, y0 + 3.8), (-9.4, y0 + 6.8), (-8.8, y0 + 9.8), (-6.6, y0 + 11.6), (-4.0, y0 + 12.0)]
    tm = Model()
    for i, (x, y) in enumerate(pts):
        r = 2.0 - i * 0.16
        tm.ell((x, y, 0), (r, r, r), tail)
    bulb = np.array((-2.6, y0 + 11.4, 0))
    tm.ell(bulb, (1.6, 1.3, 1.3), Mat(CRIMSON))
    tm.cyl(bulb + (0.8, -0.4, 0), bulb + (3.0, -2.6, 0), 0.8, M_BONE, r1=0.12, seg=5)
    if pose == "attack":
        tm = pivot(tm, rot_z(-0.75), (-5.0, y0 + 1.4, 0))
    m.extend(tm)
    leg_pairs(m, mc, y0, ((-3.2, -3.0), (-1.4, -0.8), (0.4, 1.0), (1.8, 2.6)), 1.15, g["leg"] * 0.8, 0, pose)
    return dict(y0=y0, hc=hc, hs=hs, tip=np.array((-6, y0, 0)), gc=np.array((-2, y0, 0)), gr=2.2,
                back=[(-3.5, y0 + 2.6), (-1.5, y0 + 2.8), (0.5, y0 + 2.6)], wing=np.array((-0.5, y0 + 2.6, 0)),
                hind=np.array((-3.2, y0 - 0.6, 0)), fore=np.array((1.8, y0 + 0.2, 0)), length=14, has_stinger=True)


def plan_honeypot(m, mc, g, pose, soldier):
    y0 = 5.0
    gs, hs = g["gs"], g["hsz"]
    gc = np.array((-7.4, y0 + 3.0, 0))
    m.ell(gc, (6.4 * gs, 5.8 * gs, 5.8 * gs), M_ACID_BELLY)
    for x in (-10.5, -7.4, -4.4):     # dark plates stretched over the belly
        m.ell((x, y0 + 3.0 + 4.8 * gs, 0), (0.9, 1.5, 3.4 * gs), mc)
    m.ell((-1.0, y0 + 0.6, 0), (0.8, 1.1, 0.8), mc)
    m.ell((1.2, y0 + 0.9, 0), (2.2, 1.6, 1.6), mc, rot_z(0.22))
    hc = np.array((4.2, y0 + 1.5, 0))
    m.ell(hc, (1.8 * hs, 1.7 * hs, 1.7 * hs), mc)
    for z in (1.0, -1.0):
        m.ell(hc + (0.8, 0.4, z * hs), (0.45, 0.45, 0.45), M_EYE)
    mandibles(m, mc, hc, hs * 0.85, 0.25 if pose == "idle" else 0.8)
    antennae(m, mc, hc + (0.6, 1.1 * hs, 0), long=0.9)
    leg_pairs(m, mc, y0, ((-0.4, -2.2), (1.0, 0.3), (2.4, 2.4)), 1.1, 0.8, 0, pose)
    return dict(y0=y0, hc=hc, hs=hs * 0.85, tip=gc + (-6.4 * gs, -1.0, 0), gc=gc, gr=5.8 * gs,
                back=[(-10, y0 + 8.4), (-7, y0 + 9.0), (-4, y0 + 8.2)], wing=np.array((1.2, y0 + 2.4, 0)),
                hind=np.array((-0.4, y0 - 0.8, 0)), fore=np.array((2.4, y0 + 0.2, 0)), length=15, has_acid=True)


def plan_beetle(m, mc, g, pose, soldier):
    y0 = 3.9 * g["leg"]
    gs, hs = g["gs"], g["hsz"]
    ely = Mat(ELYTRA)
    m.ell((-4.0, y0 + 2.0, 0), (6.6 * gs, 3.9 * gs, 4.9 * gs), ely)
    m.box((-4.0, y0 + 2.0 + 3.85 * gs, 0), (11.5 * gs, 0.5, 0.45), Mat(ramp("#0c0408", "#1a0810", "#2a0e18", "#3a1420", "#4a1a28")))
    m.ell((2.6, y0 + 2.0, 0), (2.6, 2.6, 3.8), mc)                  # pronotum
    hc = np.array((5.4, y0 + 1.2, 0))
    m.ell(hc, (1.6 * hs, 1.5 * hs, 1.9 * hs), mc)
    for z in (1.2, -1.2):
        m.ell(hc + (0.7, 0.4, z * hs), (0.4, 0.4, 0.4), M_EYE)
    # rhinoceros horn, curving back, plus a short horn on the pronotum
    hr = Model()
    hr.cyl(hc + (0.8, 0.8, 0), hc + (3.4, 4.4, 0), 1.6 * hs, M_BONE, r1=1.0 * hs, seg=6)
    hr.cyl(hc + (3.4, 4.4, 0), hc + (3.0, 7.6, 0), 1.0 * hs, M_BONE, r1=0.2, seg=6)
    hr.cyl((3.4, y0 + 4.2, 0), (6.0, y0 + 6.0, 0), 1.0, M_BONE, r1=0.15, seg=5)
    if pose == "attack":
        hr = pivot(hr, rot_z(-0.55), hc)
    m.extend(hr)
    leg_pairs(m, mc, y0, ((-2.6, -2.2), (0.0, 0.2), (2.4, 2.4)), 1.35, 0.5, 0, pose)
    return dict(y0=y0, hc=hc, hs=hs, tip=np.array((-10.6 * gs, y0 + 1.0, 0)), gc=np.array((-4, y0 + 1, 0)), gr=3.9 * gs,
                back=[(-8, y0 + 5.0 * gs), (-5, y0 + 5.8 * gs), (-2, y0 + 5.6 * gs), (1.5, y0 + 4.4)],
                wing=np.array((-2.0, y0 + 5.5, 0)), hind=np.array((-2.6, y0 - 0.8, 0)), fore=np.array((2.4, y0 + 0.2, 0)),
                length=15, has_horn=True)


def plan_isopod(m, mc, g, pose, soldier):
    y0 = 3.6
    gs, hs = g["gs"], g["hsz"]
    plate = Mat(chitin_shift(mc, -0.18, sat=0.55))
    back = []
    for i in range(7):
        x = 3.2 - i * 2.2
        k = 1.0 - abs(i - 2.2) * 0.08
        m.ell((x, y0 + 1.2, 0), (1.7, 2.8 * k * gs, 4.4 * k * gs), plate)
        back.append((x, y0 + 1.2 + 2.8 * k * gs))
    m.ell((-12.0, y0 + 0.8, 0), (1.4, 1.6, 2.6), plate)
    hc = np.array((5.4, y0 + 0.6, 0))
    m.ell(hc, (1.4 * hs, 1.3 * hs, 2.4 * hs), mc)
    for z in (1.4, -1.4):
        m.ell(hc + (0.6, 0.5, z * hs), (0.4, 0.4, 0.4), M_EYE)
    antennae(m, mc, hc + (0.8, 0.6, 0), long=1.3)
    for z in (1.4, -1.4):   # tail prongs
        spike(m, (-12.6, y0 + 0.6, z), (-15.0, y0 + 0.2, z * 1.6), 0.45, plate)
    xs = tuple((3.0 - i * 2.2, 0.4) for i in range(6))
    leg_pairs(m, mc, y0, xs, 1.4, 0.55, 0, pose)
    return dict(y0=y0, hc=hc, hs=hs, tip=np.array((-12.6, y0 + 0.8, 0)), gc=np.array((-4, y0, 0)), gr=2.8 * gs,
                back=back[::2], wing=np.array((0.0, y0 + 3.8, 0)), hind=np.array((-6.0, y0 - 0.4, 0)),
                fore=np.array((3.0, y0, 0)), length=17, has_carapace=True)


def plan_grasshopper(m, mc, g, pose, soldier):
    y0 = 6.0 * g["leg"]
    gs, hs = g["gs"], g["hsz"]
    stripe = Mat(chitin_shift(mc, 0.0, light=1.35))
    gc = np.array((-6.6, y0 + 0.6, 0))
    m.ell(gc, (6.4 * gs, 2.2 * gs, 2.0 * gs), mc, rot_z(0.08))
    rings(m, gc, rot_z(0.08), 6.4 * gs, 2.2 * gs, stripe, n=4)
    m.ell((0.6, y0 + 1.4, 0), (3.2, 2.4, 2.1), mc)
    m.box((0.8, y0 + 3.4, 0), (5.2, 1.0, 3.6), stripe, rot_z(0.06))     # saddle
    m.ell((-4.5, y0 + 2.6, 0), (6.0, 0.8, 1.6), stripe, rot_z(0.05))   # folded wings
    hc = np.array((4.6, y0 + 2.2, 0))
    m.ell(hc, (1.9 * hs, 2.7 * hs, 1.9 * hs), mc)
    for z in (1.2, -1.2):
        m.ell(hc + (0.6, 1.2, z * hs), (0.7, 0.9, 0.5), M_EYE)
    mandibles(m, mc, hc + (0, -1.2, 0), hs * 0.7, 0.3)
    antennae(m, mc, hc + (0.6, 2.4 * hs, 0), back=True, long=1.3)
    leg_pairs(m, mc, y0, ((0.4, 0.8), (2.2, 2.4)), 1.0, 0.85, 0, pose)
    for side in (1, -1):    # the huge hind legs are the body plan here
        hip = np.array((-1.6, y0 - 0.4, 1.6 * side))
        if pose == "idle":
            knee, foot = np.array((-7.0, y0 + 8.0, 3.0 * side)), np.array((-10.4, 0.2, 3.8 * side))
        else:
            knee, foot = np.array((-7.5, y0 - 1.0, 2.8 * side)), np.array((-12.5, y0 - 5.5, 3.4 * side))
        m.cyl(hip, knee, 2.3, mc, r1=1.1, seg=6)
        m.ell(knee, (1.1, 1.1, 1.1), M_BONE)
        m.cyl(knee, foot, 0.6, mc, r1=0.4, seg=5)
    return dict(y0=y0, hc=hc, hs=hs, tip=gc + (-6.4 * gs, 0, 0), gc=gc, gr=2.2 * gs,
                back=[(-8, y0 + 3.4), (-4, y0 + 3.6), (0, y0 + 4.2)], wing=np.array((0.8, y0 + 3.8, 0)),
                hind=None, fore=np.array((2.2, y0 + 0.4, 0)), length=17, has_jumper=True)


def plan_mantis(m, mc, g, pose, soldier):
    y0 = 7.0 * g["leg"]
    gs, hs = g["gs"], g["hsz"]
    jade = Mat(chitin_shift(mc, 0.33, sat=0.7))
    gc = np.array((-6.4, y0 + 0.4, 0))
    m.ell(gc, (5.8 * gs, 2.3 * gs, 2.3 * gs), mc, rot_z(-0.08))
    m.ell((-5.4, y0 + 2.2, 0), (5.2 * gs, 0.9, 2.2), jade, rot_z(-0.05))   # leaf-like folded wings
    m.ell((-0.4, y0 + 0.8, 0), (2.0, 1.6, 1.5), mc)
    neck_top = np.array((3.2, y0 + 9.0, 0))
    m.cyl((-0.2, y0 + 1.2, 0), neck_top, 1.25, mc, r1=1.0, seg=6)
    hc = neck_top + (1.0, 1.6, 0)
    m.solid([hc + (1.2 * hs, -1.8 * hs, 0), hc + (-0.8, 0.9 * hs, 2.4 * hs), hc + (-0.8, 0.9 * hs, -2.4 * hs),
             hc + (-1.0, -0.6, 0)], [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], mc)
    for z in (2.2, -2.2):
        m.ell(hc + (-0.4, 0.9 * hs, z * hs), (0.7, 0.7, 0.7), M_EYE)
    antennae(m, mc, hc + (0.2, 1.0, 0), long=1.1)
    for side in (1, -1):    # raptorial forelegs
        base = neck_top + (-1.0, -2.6, 1.0 * side)
        if pose == "idle":
            elbow, tip = base + (2.4, 1.2, 0.6 * side), base + (3.2, -4.0, 0.8 * side)
        else:
            elbow, tip = base + (3.4, 2.4, 0.6 * side), base + (8.5, 0.6, 0.8 * side)
        m.cyl(base, elbow, 0.85, jade, seg=5)
        m.cyl(elbow, tip, 1.0, M_BONE, r1=0.15, seg=4)
        for f in (0.35, 0.6):
            spike(m, elbow + (tip - elbow) * f, elbow + (tip - elbow) * f + np.array((-0.7, 0.3, 0)), 0.25)
    leg_pairs(m, mc, y0, ((-2.6, -3.6), (-0.6, 1.8)), 1.2, 1.25, 0, pose)
    return dict(y0=y0, hc=hc, hs=hs, tip=gc + (-5.8 * gs, -0.4, 0), gc=gc, gr=2.3 * gs,
                back=[(-9, y0 + 3.0), (-6, y0 + 3.2), (-3, y0 + 3.0)], wing=np.array((-0.4, y0 + 2.4, 0)),
                hind=np.array((-2.6, y0 - 0.6, 0)), fore=None, length=16, has_scythes=True)


def plan_firefly(m, mc, g, pose, soldier):
    y0 = 5.6 * g["leg"]
    gs, hs = g["gs"], g["hsz"]
    soft = Mat(chitin_shift(mc, -0.04, light=0.85))
    m.ell((-4.4, y0 + 1.0, 0), (6.0 * gs, 2.2, 3.0), mc)
    open_ = 0.12 if pose == "idle" else 0.55
    for z in (1.0, -1.0):
        m.ell((-3.6, y0 + 2.6, 1.7 * z), (5.6 * gs, 1.4, 2.0), soft, rot_y(-0.08 * z) @ rot_x(open_ * z))
    lan = np.array((-10.2 * gs, y0 + 1.0, 0))
    m.ell(lan, (2.6 if pose == "idle" else 3.2, 2.2, 2.7), M_LANTERN)
    shield = np.array((2.8, y0 + 2.2, 0))
    m.ell(shield, (2.8, 1.5, 3.6), mc)
    for z in (1.4, -1.4):
        m.ell(shield + (0.2, 1.2, z), (1.0, 0.4, 0.9), Mat(ramp("#3a1e14", "#7a3a24", "#c06a40", "#e8a070", "#fad0a8")))
    hc = np.array((4.6, y0 + 1.0, 0))
    m.ell(hc, (1.4 * hs, 1.3 * hs, 1.6 * hs), mc)
    for z in (1.0, -1.0):
        m.ell(hc + (0.6, 0.3, z * hs), (0.55, 0.55, 0.55), M_DARKEYE)
    antennae(m, mc, hc + (0.6, 0.8, 0), long=1.5)
    leg_pairs(m, mc, y0, ((-2.4, -2.4), (-0.2, 0.2), (2.0, 2.4)), 1.15, g["leg"] * 0.85, 0, pose)
    return dict(y0=y0, hc=hc, hs=hs, tip=lan, gc=np.array((-4, y0, 0)), gr=2.2,
                back=[(-7, y0 + 4.0), (-4, y0 + 4.4), (-1, y0 + 4.0)], wing=np.array((-1.0, y0 + 3.6, 0)),
                hind=np.array((-2.4, y0 - 0.8, 0)), fore=np.array((2.0, y0 + 0.2, 0)), length=16, has_firefly=True)


PLAN_FN = {None: plan_ant, "wings": plan_wasp, "stinger": plan_scorpion, "acid": plan_honeypot, "horn": plan_beetle,
           "carapace": plan_isopod, "jumper": plan_grasshopper, "scythes": plan_mantis, "firefly": plan_firefly}


def chitin_shift(mat, dh, sat=1.0, light=1.0):
    import colorsys
    out = []
    for c in mat.ramp:
        r, g, b = (np.clip(c, 0, 255) / 255).tolist()
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb((h + dh) % 1, min(l * light, 0.95), min(s * sat, 1))
        out.append(np.array([r * 255, g * 255, b * 255], dtype=np.float32))
    return out


# ------------------------------------------------------------------ extra traits on any body
def add_parts(m, mc, a, traits, pose):
    y0, hc, hs = a["y0"], a["hc"], a["hs"]
    if "wings" in traits:
        up = 0 if pose == "idle" else 3.5
        L = a["length"] / 14
        r0 = a["wing"]
        for z in (-0.9, 0.9):
            s = np.sign(z)
            mat = M_WING if z < 0 else M_WING_NEAR
            m.poly([r0 + (0.6, 0.2, z), r0 + (-15.5 * L, 2.9 + up, z + 7.5 * s), r0 + (-14.0 * L, 6.4 + up, z + 8.0 * s),
                    r0 + (-6.5 * L, 5.4 + up, z + 4.5 * s), r0 + (-0.6, 1.0, z + 0.4 * s)], mat)
            m.limb([r0 + (0.2, 0.4, z), r0 + (-14.6 * L, 4.4 + up, z + 7.6 * s)], 1, M_VEIN, band=2)
    if "stinger" in traits and not a.get("has_stinger"):
        t = a["tip"]
        m.cyl(t + (0.8, 0.4, 0), t + (-3.6, -2.4, 0), 1.4, M_BONE, r1=0.15, seg=6)
    if "acid" in traits and not a.get("has_acid"):
        gc = a["gc"]
        m.ell(gc + (-0.2, -a["gr"] * 0.55, 1.2), (3.0, 2.2, 2.8), M_ACID)
        if pose == "attack":
            m.ell(hc + (4.5, -0.6, 0), (1.3, 1.1, 1.1), M_ACID_SPIT)
            m.ell(hc + (7.0, -1.2, 0), (0.6, 0.6, 0.6), M_ACID_SPIT)
    if "horn" in traits and not a.get("has_horn"):
        m.cyl(hc + (0.6 * hs, 1.0 * hs, 0), hc + (3.0 * hs, 4.6 * hs, 0), 1.6 * hs, M_BONE, r1=0.9 * hs, seg=6)
        spike(m, hc + (3.0 * hs, 4.6 * hs, 0), hc + (5.6 * hs, 7.2 * hs, 0), 0.9 * hs)
    if "carapace" in traits and not a.get("has_carapace"):
        for (x, y) in a["back"]:
            spike(m, (x, y - 0.6, 0), (x - 0.9, y + 3.0, 0), 0.9)
    if "jumper" in traits and not a.get("has_jumper") and a.get("hind") is not None:
        h0 = a["hind"]
        for side in (1, -1):
            hip = h0 + (0, 0, 1.5 * side)
            knee = hip + ((-4.4, 7.2, 1.6 * side) if pose == "idle" else (-4.2, 0.0, 1.4 * side))
            foot = knee + ((-3.2, -knee[1] + 0.2, 0.8 * side) if pose == "idle" else (-4.0, -4.0, 0.6 * side))
            m.cyl(hip, knee, 1.9, mc, r1=1.0, seg=6)
            m.ell(knee, (1.1, 1.1, 1.1), M_BONE)
            m.cyl(knee, foot, 0.55, mc, r1=0.4, seg=5)
    if "scythes" in traits and not a.get("has_scythes") and a.get("fore") is not None:
        f0 = a["fore"]
        for side in (1, -1):
            base = f0 + (0, 0, 1.2 * side)
            elbow = base + ((2.0, 6.4, 0.6 * side) if pose == "idle" else (3.0, 5.6, 0.6 * side))
            tip = base + ((5.0, 2.0, 0.8 * side) if pose == "idle" else (9.6, 2.6, 0.9 * side))
            m.cyl(base, elbow, 1.1, M_BONE, seg=6)
            m.cyl(elbow, tip + (tip - elbow) * 0.35, 1.6, M_BONE, r1=0.15, seg=4)
    if "firefly" in traits and not a.get("has_firefly"):
        m.ell(a["tip"] + (0.6, 0.6, 0), (1.9, 1.7, 1.8), M_LANTERN)


def body(hue=0.0, traits=(), pose="idle", soldier=False, genes=None):
    traits = tuple(t for t in traits if t != "giant")
    g = genes or genes_for(int(abs(hue) * 1000) + 7 * len(traits))
    mc = Mat(chitin(hue))
    m = Model()
    primary = traits[0] if traits and not soldier else None
    a = PLAN_FN[primary](m, mc, g, pose, soldier)
    add_parts(m, mc, a, traits, pose)
    hover = 6.0 if ("wings" in traits) else 0.0
    if primary == "wings":
        hover = 5.0
    if hover:
        m = m.transformed(I3, (0, hover, 0))
    if pose == "attack":
        if primary == "jumper" or ("jumper" in traits and primary is None):
            m = pivot(m, rot_z(0.18), (0, 0, 0)).transformed(I3, (3, 5, 0))
        elif primary in ("stinger", "scythes", "firefly", "acid"):
            m = m.transformed(I3, (2.0, 0, 0))
        else:
            lean = -0.35 if "wings" in traits else (-0.3 if "horn" in traits else -0.16)
            m = pivot(m, rot_z(lean), (0, hover + 1.5, 0)).transformed(I3, (2.5, 0, 0))
    return m


def size_of(traits, soldier=False):
    return (2 if soldier else 1) + (1 if "giant" in traits else 0)


def scale_for(size):
    return {1: 1.0, 2: 1.45, 3: 1.9, 4: 2.3}[size]


def build(traits=(), hue=0.0, pose="idle", soldier=False, k=1.0, genes=None):
    """k multiplies the in-game scale (use >1 for close-up sheets)."""
    s = scale_for(size_of(traits, soldier)) * k
    w, h, ox, oy = int(64 * s), int(56 * s), int(30 * s), int(48 * s)
    spr = render(body(hue, traits, pose, soldier, genes).scaled(s), w, h, ox, oy, **STYLE1)
    spr.ox, spr.oy = ox, oy
    return spr


def queen(hue=0.0, pose="idle", k=1.0):
    c = chitin(hue)
    mc = Mat(c)
    m = Model()
    for (cx, r) in ((-6, 7.5), (-13, 10), (-21, 10.5), (-29, 9), (-35.5, 6)):
        m.ell((cx, 11, 0), (4.2, r, r * 0.95), M_MEMBRANE)
        m.ell((cx + 0.6, 11 + r * 0.32, 0), (3.2, r * 0.72, r * 0.82), mc)
    m.ell((-39, 9, 0), (2.4, 3.2, 3.2), mc)
    for ex, ey, ez in ((-42, 4, 1.5), (-43.5, 6, -1), (-41.5, 2.5, -2.5), (-44, 3, 2)):
        m.ell((ex, ey, ez), (1.5, 1.1, 1.1), M_EGG)
    m.ell((-1.5, 9, 0), (1.3, 1.8, 1.3), mc)
    m.ell((2.5, 10, 0), (4, 2.8, 2.6), mc, rot_z(0.2))
    up = 0 if pose == "idle" else 2.5
    hc = np.array((7.6, 11.8 + up, 0))
    m.ell(hc, (2.6, 2.3, 2.3), mc)
    jaw = 0.25 if pose == "idle" else 0.8
    for z in (1.4, -1.4):
        m.ell(hc + (1.2, 0.7, z), (0.7, 0.7, 0.7), M_EYE)
        base = hc + (2.1, -1.0, z * 0.5)
        tip = base + np.array((np.cos(jaw) * 2.8, -0.6, np.sign(z) * np.sin(jaw) * 2.4))
        m.cyl(base, tip, 0.6, M_BONE, r1=0.12, seg=4)
        a0 = hc + (1.0, 1.6, z * 0.4)
        m.limb([a0, a0 + (0.2, 3.6, z * 0.5), a0 + (3.8, 4.4, z * 1.4)], 1, mc, band=3 if z > 0 else 1)
    if pose == "attack":
        m.ell(hc + (6.5, -1.5, 0), (1.8, 1.5, 1.5), M_ACID_SPIT)
        m.ell(hc + (9.5, -2.5, 0), (0.9, 0.9, 0.9), M_ACID_SPIT)
    for side in (1, -1):
        for x, dx in ((0.5, -3), (2.5, 0.5), (4.5, 3.5)):
            hip = np.array((x, 8.4, 1.8 * side))
            knee = np.array((x + dx, 11.5, 6 * side))
            foot = np.array((x + dx * 1.6, 0, 8.5 * side))
            m.limb([hip, knee, foot], 1, mc, band=3 if side > 0 else 1)
    s = 2.6 * k
    w, h, ox, oy = int(88 * s), int(56 * s), int(48 * s), int(50 * s)
    spr = render(m.scaled(s), w, h, ox, oy, **STYLE1)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    from paths import out
    K = 2.2
    items = [()] + [(t,) for t in TRAITS]
    w, h = 140, 120
    sc = Scene(w * len(items), h * 2)
    sc.rgb[:] = hexc("#2c2436")
    for i, t in enumerate(items):
        for j, pose in enumerate(("idle", "attack")):
            spr = build(t, 0.0, pose, False, k=K)
            sc.blit(spr, int(i * w + w / 2 - spr.ox), int(j * h + h - 14 - spr.oy))
    sc.image(2).save(out("test_swarm1.png"))

