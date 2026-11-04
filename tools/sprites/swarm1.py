"""Swarm creatures in style 1: an ant-like body plan where every inherited trait is a visible part.

Castes: worker (size 1), soldier (size 2), queen (size 6). Traits stack on any body.
Colour (hue) is inherited: a child takes the average of its parents plus a little drift.
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3

STYLE1 = dict(amb=0.40, dif=0.60, gradient=False, edges=False, outline_tint=0.22)

M_BONE = Mat(BONE)
M_EYE = Mat(GLOWG, emissive=hexc("#9af060"), glow_r=5, glow_k=0.4)
M_WING = Mat(ramp("#2e2a48", "#4c4874", "#76729e", "#a6a2cc", "#d4d0ee"), dither=True)
M_WING_NEAR = Mat(ramp("#3a3658", "#5c5888", "#8a86b8", "#b8b4de", "#e2def8"))
M_VEIN = Mat(ramp("#1c1830", "#2c2848", "#403c64", "#56527e", "#6e6a98"))
M_ACID = Mat(GLOWG, emissive=hexc("#8af04a"), glow_r=9, glow_k=0.55)
M_ACID_SPIT = Mat(GLOWG, emissive=hexc("#a8ff60"), glow_r=12, glow_k=0.8)
M_FIREFLY = Mat(ramp("#4a4410", "#8a7a18", "#d0b830", "#f4e870", "#fffcd0"), emissive=hexc("#f0e060"), glow_r=14, glow_k=0.7)
M_EGG = Mat(ramp("#2a3a20", "#4a6a2e", "#76a040", "#a8d060", "#e0f6a0"), emissive=hexc("#80d040"), glow_r=0, glow_k=0)
M_MEMBRANE = Mat(ramp("#2a1e34", "#45304f", "#664a6e", "#8a6a90", "#b08eb4"))

TRAITS = ("wings", "stinger", "acid", "horn", "carapace", "jumper", "scythes", "firefly")
NAMES = dict(wings="Крылья", stinger="Жало", acid="Кислотная железа", horn="Рог", carapace="Панцирь",
             jumper="Прыгучие ноги", scythes="Серпы", firefly="Светлячок", giant="Гигантизм")


def pivot(m, R, p):
    p = np.array(p, float)
    return m.transformed(R, p - R @ p)


def spike(m, a, b, r, mat=M_BONE):
    m.cyl(a, b, r, mat, r1=0.12, seg=5)


def legs(m, mc, y0, pose, traits, lift=0.0, spread=1.0):
    for side in (1, -1):
        band = 3 if side > 0 else 1
        for i, (x, dx) in enumerate(((-1.6, -3.2), (0.4, 0.3), (2.4, 3.4))):
            if i == 0 and "jumper" in traits:
                continue            # replaced by jumping legs
            if i == 2 and "scythes" in traits:
                continue            # replaced by scythes
            hip = np.array((x, y0 - 1.2, 1.4 * side))
            knee = np.array((x + dx * 0.8, y0 + 1.8, 3.6 * side * spread))
            foot = np.array((x + dx * 1.4, lift, 5.4 * side * spread))
            if pose == "attack" and i == 2:
                knee = np.array((x + 3.5, y0 + 4.2, 3.6 * side))
                foot = np.array((x + 6.5, y0 + 2.2, 4.4 * side))
            m.limb([hip, knee], 1, mc, band=band)
            m.limb([knee, foot], 1, mc, band=band - 1 if side > 0 else 1)
        if "jumper" in traits:      # big grasshopper femur, thin tibia
            hip = np.array((-1.4, y0 - 1.0, 1.5 * side))
            if pose == "idle":
                knee = np.array((-5.8, y0 + 6.2, 3.2 * side))
                foot = np.array((-9.0, lift, 4.2 * side))
            else:                   # extended: the leap
                knee = np.array((-5.5, y0 - 1.0, 2.8 * side))
                foot = np.array((-9.5, y0 - 4.5, 3.4 * side))
            m.cyl(hip, knee, 1.9, mc, r1=1.0, seg=6)
            m.ell(knee, (1.1, 1.1, 1.1), M_BONE)
            m.cyl(knee, foot, 0.55, mc, r1=0.4, seg=5)
            spike(m, knee + (foot - knee) * 0.4, knee + (foot - knee) * 0.4 + np.array((-1.2, 0.6, 0)), 0.3)
        if "scythes" in traits:     # mantis forelegs with bone blades
            base = np.array((2.4, y0 + 0.2, 1.2 * side))
            if pose == "idle":
                elbow = np.array((4.4, y0 + 6.6, 1.8 * side))
                tip = np.array((7.4, y0 + 2.2, 2.0 * side))
            else:
                elbow = np.array((5.4, y0 + 5.6, 1.8 * side))
                tip = np.array((10.0, y0 + 2.6, 2.1 * side))
            m.cyl(base, elbow, 1.1, M_BONE, seg=6)
            m.cyl(elbow, tip + (tip - elbow) * 0.35, 1.6, M_BONE, r1=0.15, seg=4)
            for f in (0.3, 0.55):
                spike(m, elbow + (tip - elbow) * f, elbow + (tip - elbow) * f + np.array((-0.8, -0.9, 0)), 0.3)


def body(hue=0.0, traits=(), pose="idle", soldier=False):
    c = chitin(hue)
    mc = Mat(c)
    shell = Mat([c[0] * 0.8, c[0], c[1], c[2], c[3]])
    m = Model()
    y0 = 6.5
    jaw = 0.25 if pose == "idle" else 0.7

    # gaster
    if "stinger" in traits and pose == "attack":
        g = Model()
        g.ell((-6.5, y0, 0), (4.6, 3.4, 3.4), mc, rot_z(0.5))
        g.cyl((-10.0, y0 - 2.8, 0), (-13.4, y0 - 5.4, 0), 1.25, M_BONE, r1=0.15, seg=6)
        if "acid" in traits:
            g.ell((-7.5, y0 - 2.4, 0), (2.4, 1.8, 2.4), M_ACID)
        g = pivot(g, rot_z(1.9), (-2.6, y0, 0))
        m.extend(g)
        m.ell((5.5, y0 - 4.2, 0), (0.7, 0.7, 0.7), M_ACID)
    else:
        m.ell((-6.8, y0 + 0.4, 0), (5.2, 3.9, 3.9), mc, rot_z(0.25))
        if "stinger" in traits:
            m.cyl((-11.4, y0 - 0.6, 0), (-17.0, y0 - 3.6, 0), 1.7, M_BONE, r1=0.15, seg=6)
            spike(m, (-13.2, y0 - 1.6, 0), (-13.0, y0 - 3.4, 0), 0.4)
        if "acid" in traits:     # glowing gland under the gaster, a drip below it
            m.ell((-7.0, y0 - 2.0, 1.2), (3.3, 2.5, 3.0), M_ACID)
            m.ell((-6.4, y0 - 4.8, 1.8), (0.7, 0.9, 0.7), M_ACID)
    if "firefly" in traits:
        m.ell((-10.4, y0 + 0.9, 0), (1.7, 1.6, 1.6), M_FIREFLY)
    m.ell((-2.4, y0 + 0.2, 0), (0.9, 1.3, 0.9), mc)                     # petiole
    m.ell((0.6, y0 + 0.9, 0), (3.0, 2.1, 2.0), mc, rot_z(0.22))        # thorax

    hs = 1.45 if soldier else 1.0
    hc = np.array((4.3 + (hs - 1) * 1.6, y0 + 1.6, 0))
    m.ell(hc, (2.3 * hs, 2.1 * hs, 2.1 * hs), mc)
    for z in (1.2, -1.2):
        m.ell(hc + (0.9 * hs, 0.5 * hs, z * hs), (0.55, 0.55, 0.55), M_EYE)
        base = hc + (1.6 * hs, -0.9 * hs, z * 0.5 * hs)
        L = 2.3 * hs
        tip = base + np.array((np.cos(jaw) * L, -0.5, np.sign(z) * np.sin(jaw) * L * 0.8))
        m.cyl(base, tip, 0.55 * hs, M_BONE if soldier else mc, r1=0.12, seg=4)
        a0 = hc + (0.8 * hs, 1.3 * hs, z * 0.4)
        m.limb([a0, a0 + (0.2, 3.0, z * 0.5), a0 + (3.2, 3.6, z * 1.4)], 1, mc, band=3 if z > 0 else 1)
    if soldier:
        m.box(hc + (0, 1.5 * hs, 0), (3.2, 0.8, 2.6), M_BONE, rot_z(-0.2))
    if "horn" in traits:
        m.cyl(hc + (0.6 * hs, 1.2 * hs, 0), hc + (3.6 * hs, 5.6 * hs, 0), 2.0 * hs, M_BONE, r1=1.1 * hs, seg=6)
        spike(m, hc + (3.6 * hs, 5.6 * hs, 0), hc + (7.0 * hs, 8.6 * hs, 0), 1.1 * hs)
        spike(m, hc + (-0.6 * hs, 1.6 * hs, 0), hc + (-0.4 * hs, 3.8 * hs, 0), 0.7 * hs)
    if pose == "attack" and "acid" in traits and "stinger" not in traits:
        m.ell(hc + (4.5, -0.6, 0), (1.3, 1.1, 1.1), M_ACID_SPIT)
        m.ell(hc + (7.0, -1.2, 0), (0.6, 0.6, 0.6), M_ACID_SPIT)

    if "carapace" in traits:
        m.ell((-6.8, y0 + 1.6, 0), (5.5, 3.2, 4.2), shell, rot_z(0.25))
        m.ell((0.6, y0 + 1.6, 0), (2.9, 1.3, 1.9), shell, rot_z(0.22))
        for x in (-9.0, -6.6, -4.2, -0.4, 1.8):
            top = y0 + (4.0 if x < -2 else 3.0) - (0.6 if x < -8 else 0)
            spike(m, (x, top - 0.6, 0), (x - 0.9, top + 3.2, 0), 0.9)

    if "wings" in traits:
        up = 0 if pose == "idle" else 3.5
        for z in (-0.9, 0.9):
            s = np.sign(z)
            mat = M_WING if z < 0 else M_WING_NEAR
            m.poly([(1.4, y0 + 2.8, z), (-14.5, y0 + 5.5 + up, z + 7.5 * s), (-13.0, y0 + 9.0 + up, z + 8.0 * s),
                    (-5.5, y0 + 8.0 + up, z + 4.5 * s), (0.2, y0 + 3.6, z + 0.4 * s)], mat)
            m.limb([(1.0, y0 + 3.0, z), (-13.6, y0 + 7.0 + up, z + 7.6 * s)], 1, M_VEIN, band=2)
            m.limb([(0.4, y0 + 3.3, z), (-8.0, y0 + 7.6 + up, z + 5.4 * s)], 1, M_VEIN, band=2)

    hover = 6.0 if "wings" in traits else 0.0
    legs(m, mc, y0, pose, traits, lift=hover * 0.7 if hover else 0.0, spread=1.25 if soldier else 1.0)
    if hover:
        m = m.transformed(I3, (0, hover, 0))
    if pose == "attack":
        if "jumper" in traits and "wings" not in traits:
            m = pivot(m, rot_z(0.18), (0, 0, 0)).transformed(I3, (3, 5, 0))
        else:
            lean = -0.16 if "wings" not in traits else -0.35
            if "horn" in traits:
                lean = -0.3
            m = pivot(m, rot_z(lean), (0, hover + 1.5, 0))
            m = m.transformed(I3, (2.5, 0, 0))
    return m


def size_of(traits, soldier=False):
    return (2 if soldier else 1) + (1 if "giant" in traits else 0)


def scale_for(size):
    return {1: 1.0, 2: 1.45, 3: 1.9, 4: 2.3}[size]


def build(traits=(), hue=0.0, pose="idle", soldier=False, k=1.0):
    """k multiplies the in-game scale (use >1 for close-up sheets)."""
    s = scale_for(size_of(traits, soldier)) * k
    w, h, ox, oy = int(60 * s), int(46 * s), int(26 * s), int(40 * s)
    spr = render(body(hue, tuple(t for t in traits if t != "giant"), pose, soldier).scaled(s), w, h, ox, oy, **STYLE1)
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
    K = 2.4
    items = [((), False), (("wings",), False), (("stinger",), False), (("acid",), False),
             (("horn",), False), (("carapace",), False), (("jumper",), False), (("scythes",), False), (("firefly",), False)]
    w, h = 150, 120
    sc = Scene(w * len(items), h * 2)
    sc.rgb[:] = hexc("#2c2436")
    for i, (t, sold) in enumerate(items):
        for j, pose in enumerate(("idle", "attack")):
            spr = build(t, 0.0, pose, sold, k=K)
            sc.blit(spr, int(i * w + w / 2 - spr.ox), int(j * h + h - 12 - spr.oy))
    sc.image(2).save(out("test_swarm1.png"))
