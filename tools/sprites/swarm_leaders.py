"""The Swarm's four leaders, in the swarm's style (dark oily chitin, red eye clusters, bone fangs, ichor), plus the larva
their abilities hatch.

  Матка (size 6)      — the queen: a bloated veined egg-sac of an abdomen, eggs showing through it, stretched dark
                        plates on top, shed wing stubs, a crown of spines on a small armoured head; eggs behind her.
  Разум улья (size 4) — a swollen wrinkled brain-sac on a soft pale grub of a body; feathery antennae and nodes that
                        glow with pheromone violet; a small face with a cluster of eyes under the brain.
  Пожиратель (5→7)    — a low heavy beast that is mostly maw: four jaws with rows of teeth, armour plates, spines;
                        it grows in battle — three stages, more plates and spines, and at the last its cracks glow.
  Кукушка (size 3)    — a parasitoid wasp: slender, a sickle abdomen banded rust, an egg bulb, and an ovipositor longer
                        than its body that it swings forward under itself to strike.
  личинка             — a pale grub with a dark head and jaws: hatched by the Matka's laying and the Cuckoo's eggs.

Geometry is in worker units (a worker is about 15 long); the size sets the scale, as for every swarm creature.

    python3 tools/sprites/swarm_leaders.py          -> out/swarm_leaders.png (the sheet)
    python3 tools/sprites/swarm_leaders.py check    -> out/swarm_leaders_check.png
    python3 tools/sprites/swarm_leaders.py dev      -> out/swarm_development.png (each leader's developments)
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
import swarm1 as W
from swarm1 import (pivot, spike, leg_pairs, antennae, mandibles, rings, chitin, chitin_shift, M_EYE, M_FANG, M_BONE,
                    M_ICHOR, M_SHEEN, M_DARKEYE, M_WING, M_WING_NEAR, M_VEIN, M_EGG, M_MEMBRANE, AMBER, CRIMSON)

SCALE = {1: 1.0, 2: 1.45, 3: 1.9, 4: 2.3, 5: 2.7, 6: 3.1, 7: 3.5}
SIZE = {"Матка": 6, "Разум улья": 4, "Пожиратель": 5, "Кукушка": 3, "личинка": 1}

M_GRUB = Mat(ramp("#241a12", "#54442e", "#8a7656", "#bea98a", "#ece0c4"))
M_GRUB_SEG = Mat(ramp("#1a120c", "#3a2c1e", "#5e4c36", "#8a765a", "#b8a484"))
M_BRAIN = Mat(ramp("#1c0c16", "#3c1a2c", "#66304a", "#98566e", "#cc8c98"))
M_FOLD = Mat(ramp("#120610", "#26101e", "#401c32", "#62304a", "#8e566c"))
M_PHERO = Mat(ramp("#1e0e36", "#462078", "#7640c0", "#ac80ec", "#e6d2ff"), emissive=hexc("#b070ff"), glow_r=6, glow_k=0.5)
M_PHERO_DIM = Mat(ramp("#1a0e2c", "#341a5a", "#563090", "#8460c0", "#c0a8e8"), emissive=hexc("#8a50e0"), glow_r=4, glow_k=0.25)
M_VEIN_R = Mat(ramp("#0e0408", "#260a12", "#44121e", "#681e2a", "#94303c"))
M_EGG_IN = Mat(ramp("#1e2a14", "#3a5222", "#5e823a", "#8eb458", "#cce890"), emissive=hexc("#7ab040"), glow_r=3, glow_k=0.18)
M_TOOTH = Mat(ramp("#1a1410", "#3e3428", "#7a6c58", "#c2b49a", "#f2ead6"))
M_BLOODY = Mat(ramp("#120406", "#34080c", "#5e1014", "#8e1e1e", "#c04a3a"))
M_CRACK = Mat(ramp("#401006", "#8a2a0a", "#d0601a", "#f4a040", "#ffe0a0"), emissive=hexc("#ff7a20"), glow_r=5, glow_k=0.45)
M_SAC = Mat(ramp("#0c040a", "#1e0a16", "#38142a", "#58223e", "#86405a"))          # the queen's stretched membrane
M_WHITE_BAND = Mat(ramp("#2a2622", "#5a544c", "#948c80", "#c8c0b2", "#f0eadc"))

DEVOURER = ["#040202", "#120405", "#260808", "#3e120e", "#723024"]          # black-crimson
QUEEN = ["#07050a", "#1a0c1c", "#341830", "#58304e", "#a084a6"]             # the ant violet-black, deeper
CUCKOO = ["#050404", "#141012", "#28201e", "#423630", "#8a7a6a"]             # sooty black
HIVE = ["#0c0a10", "#221c2a", "#3a3046", "#5a4e68", "#988aa8"]               # pale ash-violet, soft


def mat(base, hue=0.0):
    import colorsys
    out = []
    for c in base:
        r, g, b = (hexc(c) / 255).tolist()
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb((h + hue) % 1.0, l, s)
        out.append(np.array([r * 255, g * 255, b * 255], dtype=np.float32))
    return Mat(out)


def eyes(m, hc, pts, r=0.42):
    for p in pts:
        m.ell(hc + np.array(p), (r, r, r), M_EYE)


def legs(m, mc, hips, knees, feet, width=1, claw=0.9, thick=None):
    """Pairs of legs given for the near side (z > 0); the far side is mirrored. thick: (thigh, shin) radii — solid
    tapered segments with a knob at the knee, for the heavy ones."""
    for side in (1, -1):
        band = 3 if side > 0 else 1
        for h, k, f in zip(hips, knees, feet):
            h, k, f = (np.array((p[0], p[1], p[2] * side)) for p in (h, k, f))
            if thick:
                m.cyl(h, k, thick[0], mc, r1=thick[0] * 0.75, seg=6)
                m.ell(k, (thick[0] * 0.8,) * 3, mc)
                m.cyl(k, f, thick[1], mc, r1=thick[1] * 0.45, seg=6)
                spike(m, k, k + np.array((-1.0, 1.8, 0.5 * side)), thick[0] * 0.35, M_FANG)
                spike(m, f + (0, 0.3, 0), f + np.array((claw, -0.2, 0.3 * side)), thick[1] * 0.4, M_FANG)
                continue
            m.limb([h, k], width, mc, band=band)
            m.limb([k, f], width, mc, band=band - 1 if side > 0 else 1)
            m.limb([k, k + np.array((-0.8, 1.4, 0.4 * side))], 1, M_FANG, band=2)
            m.limb([f, f + np.array((claw, -0.2, 0.3 * side))], 1, M_FANG, band=2)


# ---------------------------------------------------------------- Матка
def matka(pose="idle", hue=0.0):
    m = Model()
    mc = mat(QUEEN, hue)
    plate = Mat(chitin_shift(mc, 0.0, light=0.9))
    # the abdomen: a membrane sac lying on the ground, dark plates stretched apart on top, veins, eggs showing through
    gc, gx, gy, gz = np.array((-14.0, 7.0, 0)), 15.5, 6.6, 6.6
    m.ell(gc, (gx, gy, gz), M_SAC)
    for i in range(7):
        x = 0.2 - i * 4.6
        t = (x - gc[0]) / gx
        k = np.sqrt(max(0.05, 1 - t * t))
        r, rz = gy * k, gz * k
        m.ell((x, gc[1] + r * 0.42, 0), (2.1, r * 0.66, rz * 0.9), plate)              # tergite on top
        m.ell((x, gc[1] - r * 0.62, 0), (1.6, r * 0.4, rz * 0.7), plate)              # sternite underneath
        if 0 < i < 6:
            for z in (1, -1):                                                           # veins over the membrane
                m.limb([np.array((x - 0.6, gc[1] + r * 0.2, z * rz * 0.95)), np.array((x - 2.6, gc[1] - r * 0.25, z * rz * 0.98))],
                       1, M_VEIN_R, band=2)
    rng = np.random.default_rng(3)
    for _ in range(14):                                                                 # eggs showing through the side
        x = rng.uniform(-27.0, -2.0)
        t = (x - gc[0]) / gx
        k = np.sqrt(max(0.05, 1 - t * t))
        a = rng.uniform(-0.7, 0.15)
        p = np.array((x, gc[1] + gy * k * np.sin(a) * 0.9, gz * k * np.cos(a) * 0.93))
        m.ell(p, (1.0, 0.7, 0.55), M_EGG_IN)
    # the ovipositor at the tip, eggs on the ground behind her
    tip = gc + np.array((-gx + 0.6, -1.8, 0))
    m.cyl(tip + (1.0, 0.4, 0), tip + (-2.6, -2.6, 0), 1.6, plate, r1=0.7, seg=7)
    for ex, ey, ez in ((-32.5, 1.0, 1.6), (-34.0, 1.0, -0.6), (-33.0, 2.6, 0.4), (-35.6, 0.9, 1.8), (-34.6, 0.9, -2.6),
                       (-31.6, 0.9, -2.0)):
        m.ell((ex, ey, ez), (1.3, 0.95, 0.95), M_EGG)
    # thorax with shed wing stubs, the waist
    m.ell((2.4, 6.4, 0), (1.2, 1.5, 1.2), mc)
    m.ell((5.6, 7.4, 0), (3.2, 2.6, 2.7), mc, rot_z(0.2))
    m.ell((5.8, 9.4, 0), (2.6, 0.9, 2.3), plate, rot_z(0.2))
    for z in (1, -1):
        r0 = np.array((5.0, 9.6, 1.0 * z))
        m.poly([r0, r0 + (-4.6, 1.4, 1.8 * z), r0 + (-3.8, 2.8, 2.4 * z), r0 + (-2.2, 2.0, 1.4 * z), r0 + (-1.6, 3.0, 1.6 * z),
                r0 + (0.4, 1.2, 0.4 * z)], M_WING_NEAR if z > 0 else M_WING)
    # the head: armoured, a crown of spines, a cluster of eyes, bone mandibles
    up = 0.0 if pose == "idle" else 2.4
    hd = Model()
    hc = np.array((10.0, 8.0, 0))
    hd.ell(hc, (2.5, 2.3, 2.5), mc)
    hd.ell(hc + (-0.4, 1.4, 0), (2.0, 1.0, 2.2), plate)
    for a, L in ((-0.9, 3.2), (-0.45, 3.8), (0.0, 4.2), (0.45, 3.8), (0.9, 3.2)):         # the crown
        base = hc + np.array((-0.8, 1.8, np.sin(a) * 1.8))
        spike(hd, base, base + np.array((-L * 0.55, L * 0.85, np.sin(a) * L * 0.6)), 0.55, M_BONE)
    eyes(hd, hc, [(1.4, 0.8, 1.3), (1.4, 0.8, -1.3), (0.8, 1.5, 1.0), (0.8, 1.5, -1.0), (1.9, 0.1, 1.4), (1.9, 0.1, -1.4)])
    mandibles(hd, M_BONE, hc, 1.25, 0.3 if pose == "idle" else 0.85)
    antennae(hd, mc, hc + (1.0, 1.4, 0), long=1.2)
    if pose == "attack":
        hd.ell(hc + (2.8, -1.8, 0), (0.6, 0.8, 0.6), M_ICHOR)
        hd.ell(hc + (3.0, -3.6, 0), (0.4, 0.6, 0.4), M_ICHOR)
        hd = pivot(hd, rot_z(0.28), (6.6, 8.2, 0)).transformed(I3, (0.6, up * 0.4, 0))
    m.extend(hd)
    legs(m, mc, hips=[(3.6, 6.2, 1.8), (5.6, 6.0, 2.0), (7.4, 6.4, 1.8)],
         knees=[(0.6, 9.6, 6.8), (5.4, 9.8, 7.6), (10.0, 9.4, 6.4)],
         feet=[(-1.4, 0.0, 9.0), (5.6, 0.0, 9.8), (12.6, 0.0, 8.2)], thick=(0.75, 0.55))
    return m


# ---------------------------------------------------------------- Разум улья
def razum(pose="idle", hue=0.0):
    m = Model()
    mc = mat(HIVE, hue)
    soft = Mat(chitin_shift(mc, 0.0, sat=0.6, light=1.25))
    # a soft pale grub of a body, in segments
    for i, (x, r) in enumerate(((-9.0, 2.4), (-6.6, 3.0), (-3.9, 3.4), (-1.0, 3.5))):
        m.ell((x, 4.0 + r * 0.25, 0), (1.7, r, r * 1.05), soft)
        m.ell((x - 0.9, 4.0 + r * 0.25, 0), (0.5, r * 0.92, r * 0.98), M_GRUB_SEG)
    # the brain-sac, swollen over the front, two lobes split by a fissure, folds, veins and glowing nodes
    bc = np.array((1.4, 11.2, 0))
    bx, by, bz = 7.0, 5.9, 6.3
    pulse = 1.0 if pose == "idle" else 1.06
    m.ell(bc, (bx * pulse, by * pulse, bz * pulse), M_BRAIN)
    rng = np.random.default_rng(11)
    for _ in range(80):                                                            # the folds: ridges on the surface
        th, ph = rng.uniform(0, np.pi * 0.62), rng.uniform(0, 2 * np.pi)
        n = np.array((np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)))
        p = bc + n * np.array((bx, by, bz)) * 0.97 * pulse
        if abs(p[2]) < 0.7:
            continue
        t = np.cross(n, (0, 0, 1.0)) if rng.random() < 0.5 else np.cross(n, (1.0, 0, 0))
        t = t / (np.linalg.norm(t) + 1e-9)
        b = np.cross(n, t)
        R = np.stack((t, n, b), axis=1)
        m.ell(p, (rng.uniform(1.2, 2.2), 0.45, 0.5), M_FOLD, R)
    m.box(bc + (0, by * pulse - 0.3, 0), (bx * 1.7, 0.8, 0.7), M_DARKEYE)       # the fissure between the lobes
    for z in (1, -1):
        for a in (-0.5, 0.3, 1.0):
            p0 = bc + np.array((np.cos(a) * bx * 0.7, -by * 0.55, z * bz * 0.78)) * pulse
            m.limb([p0, p0 + np.array((-1.6, 2.6, z * 0.6)), p0 + np.array((-0.6, 4.6, z * 0.4))], 1, M_VEIN_R, band=2)
    nodes = [(-0.6, 0.62, 0.62), (0.45, 0.72, 0.5), (0.1, 0.35, 0.92), (-0.55, 0.2, 0.8), (0.7, 0.15, 0.7)]
    for nx, ny, nz in nodes:
        for z in (1, -1):
            p = bc + np.array((nx * bx, ny * by, z * nz * bz)) * pulse
            m.ell(p, (0.65, 0.65, 0.65), M_PHERO if pose == "attack" or nx > 0 else M_PHERO_DIM)
    # a small face under the front of the brain: eyes, short jaws, feathery antennae glowing at the tips
    hc = np.array((6.6, 6.0, 0))
    m.ell(hc, (1.8, 1.6, 2.0), mc)
    eyes(m, hc, [(1.1, 0.6, 0.9), (1.1, 0.6, -0.9), (1.5, 0.0, 0.6), (1.5, 0.0, -0.6), (0.7, 1.1, 1.2), (0.7, 1.1, -1.2),
                 (1.6, 0.7, 0.0)], r=0.34)
    mandibles(m, M_FANG, hc, 0.8, 0.25 if pose == "idle" else 0.8)
    for z in (1, -1):
        a0 = hc + np.array((0.8, 1.0, 0.5 * z))
        reach = (5.2, 4.6) if pose == "idle" else (7.4, 2.4)
        tip = a0 + np.array((reach[0], reach[1] + 2.4, 2.6 * z))
        mid = a0 + np.array((1.2, 3.4, 1.0 * z))
        m.limb([a0, mid, tip], 1, mc, band=3 if z > 0 else 1)
        for f in (0.2, 0.4, 0.6, 0.8):                                            # the feathery side branches
            p = mid + (tip - mid) * f
            m.limb([p, p + np.array((-0.6, 1.1, 0.5 * z))], 1, mc, band=2)
        m.ell(tip, (0.55, 0.55, 0.55), M_PHERO)
    legs(m, mc, hips=[(-5.0, 3.0, 1.8), (-1.6, 3.2, 2.0), (2.2, 3.6, 1.8)],
         knees=[(-7.4, 5.6, 4.8), (-1.6, 5.8, 5.4), (3.8, 5.6, 4.8)],
         feet=[(-9.2, 0.0, 6.4), (-1.4, 0.0, 7.0), (5.6, 0.0, 6.2)], thick=(0.5, 0.38))
    if pose == "attack":                                        # the psionic blow: rings going out from the brain
        for j, (x, r) in enumerate(((10.5, 2.6), (14.0, 3.6), (17.6, 4.6))):
            for t in np.linspace(0, 2 * np.pi, 14 + 4 * j)[:-1]:
                m.ell((x, 9.0 + np.sin(t) * r, np.cos(t) * r), (0.35, 0.35, 0.35), M_PHERO if j < 2 else M_PHERO_DIM)
    return m


# ---------------------------------------------------------------- Пожиратель
def pozhiratel(pose="idle", stage=0, hue=0.0):
    """stage 0, 1, 2 — sizes 5, 6, 7: more plates and spines as it grows; at the last its cracks glow."""
    m = Model()
    mc = mat(DEVOURER, hue)
    heavy = Mat(chitin_shift(mc, 0.0, light=1.18))
    g = 1.0 + 0.06 * stage
    # a low heavy body: the abdomen in ring plates, a huge humped thorax
    ac = np.array((-7.6, 5.6, 0))
    m.ell(ac, (6.2 * g, 3.8, 4.8), mc, rot_z(0.1))
    for i in range(4 + stage):                                                                # overlapping plates
        x = ac[0] + 4.6 * g - i * (9.6 * g / (3 + stage))
        t = (x - ac[0]) / (6.2 * g)
        k = np.sqrt(max(0.1, 1 - t * t))
        m.ell((x, ac[1] + 3.8 * k * 0.5, 0), (1.5, 3.8 * k * 0.6, 4.8 * k * 0.95), heavy)
        m.ell((x + 0.5, ac[1] + 3.8 * k * 1.02, 0), (0.9, 0.3, 4.8 * k * 0.5), M_SHEEN)
    m.ell((0.6, 6.6, 0), (4.6, 3.9, 4.6), mc)
    m.ell((0.8, 8.9 + 0.2 * stage, 0), (4.6, 2.2, 4.4), heavy, rot_z(-0.1))                  # the pronotum shield
    m.ell((1.4, 10.6 + 0.2 * stage, 0), (2.4, 0.4, 2.6), M_SHEEN, rot_z(-0.1))
    for z in (1, -1):
        m.ell((1.4, 6.8, 4.0 * z), (3.6, 2.6, 1.0), heavy)                                   # side plates
    nsp = (3, 4, 5)[stage]
    for i in range(nsp):                                                                      # spines down the back
        x = 2.0 - i * (11.0 / max(1, nsp - 1))
        y = 10.4 + 0.2 * stage if x > -2.5 else ac[1] + 3.8 * np.sqrt(max(0, 1 - ((x - ac[0]) / (6.2 * g)) ** 2))
        L = 3.0 + 0.9 * stage
        for z in ((0.0,) if stage < 2 else (1.6, -1.6)):
            spike(m, (x, y - 0.6, z), (x - L * 0.55, y + L, z * 1.5), 0.75 + 0.12 * stage, M_FANG)
    if stage == 2:                                                                            # cracks glow with ichor
        for a, b in (((2.8, 11.2, 1.6), (-0.4, 10.6, 3.4)), ((-0.4, 10.6, 3.4), (-2.6, 9.0, 3.2)),
                     ((-5.0, 9.8, 2.0), (-8.6, 9.6, 3.0)), ((-8.6, 9.6, 3.0), (-11.0, 8.0, 2.8))):
            m.limb([np.array(a), np.array(b)], 1, M_CRACK, band=2)
    # the head that is mostly maw: four jaws with rows of teeth, a hood of plate, small red eyes
    jaw = (0.35 if pose == "idle" else 0.95) + 0.05 * stage
    hd = Model()
    hc = np.array((6.2, 6.0, 0))
    hd.ell(hc, (2.8, 3.2, 3.6), mc)
    hd.ell(hc + (-0.2, 2.2, 0), (2.8, 1.3, 3.4), heavy, rot_z(-0.25))
    eyes(hd, hc, [(1.0, 2.0, 1.6), (1.0, 2.0, -1.6), (1.6, 1.5, 2.0), (1.6, 1.5, -2.0)], r=0.38)
    mouth = hc + np.array((2.2, -0.2, 0))
    hd.ell(mouth, (0.9, 1.6 + jaw, 1.6 + jaw), M_BLOODY if stage else M_DARKEYE)          # the gullet
    for k, (dy, dz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):                     # upper, lower, side jaws
        d = np.array((np.cos(jaw), np.sin(jaw) * dy, np.sin(jaw) * dz))
        base = mouth + np.array((0, 1.3 * dy, 1.3 * dz))
        L = 5.0 + 0.6 * stage if dy == 0 else 4.2 + 0.5 * stage
        tip = base + d * L + np.array((0, -0.6 * (dy == 0), 0))
        hd.cyl(base, tip, 1.25, M_BONE, r1=0.3, seg=5)
        hook = tip + np.array((0.6, -0.9 * dy, -0.9 * dz)) * 1.4
        hd.cyl(tip, hook, 0.3, M_FANG, r1=0.05, seg=4)
        for f in (0.3, 0.55, 0.8):                                                      # teeth on the inner edge
            p = base + (tip - base) * f
            spike(hd, p, p - np.array((0, dy, dz)) * 0.9 + np.array((0.3, 0, 0)), 0.22, M_TOOTH)
    if pose == "attack":
        for i in range(3):
            hd.ell(mouth + np.array((0.6, -2.0 - 1.2 * i, 0.4 * (i - 1))), (0.4, 0.7, 0.4), M_ICHOR)
        hd = pivot(hd, rot_z(-0.15), (4.0, 7.0, 0)).transformed(I3, (1.2, -0.4, 0))
    m.extend(hd)
    legs(m, mc, hips=[(-4.0, 4.6, 3.4), (-0.6, 4.8, 3.8), (2.8, 5.0, 3.6)],
         knees=[(-7.8, 7.4, 7.6), (-0.8, 7.8, 8.6), (6.0, 7.2, 7.8)],
         feet=[(-10.0, 0.0, 9.0), (-0.4, 0.0, 10.4), (8.6, 0.0, 9.0)], claw=1.6, thick=(1.25, 0.95))
    return m


# ---------------------------------------------------------------- Кукушка
def kukushka(pose="idle", hue=0.0):
    m = Model()
    mc = mat(CUCKOO, hue)
    band = Mat(chitin_shift(Mat(AMBER), -0.04, sat=0.9, light=0.9))
    # thorax, a long thin waist
    m.ell((2.0, 8.0, 0), (2.6, 2.0, 1.8), mc, rot_z(0.15))
    m.cyl((-0.4, 7.8, 0), (-3.6, 8.6, 0), 0.5, mc, seg=6)
    # a sickle abdomen, flattened sideways, banded; in the attack it curls under the body
    curl = pose == "attack"
    if not curl:
        pts = [(-5.0, 9.0), (-7.6, 9.2), (-10.2, 8.6), (-12.6, 7.4), (-14.4, 5.8)]
    else:
        pts = [(-5.0, 8.4), (-7.0, 6.8), (-7.6, 4.6), (-6.6, 2.8), (-4.6, 1.8)]
    for i, (x, y) in enumerate(pts):
        r = 1.9 - 0.12 * i
        m.ell((x, y, 0), (1.6, r, r * 0.75), band if i % 2 else mc)
    tip = np.array((*pts[-1], 0.0))
    bulb = tip + (np.array((-1.4, -0.6, 0)) if not curl else np.array((1.0, -0.4, 0)))
    m.ell(bulb, (1.6, 1.3, 1.2), M_MEMBRANE)                                                  # the egg bulb
    for d in ((-0.4, 0.3, 0.8), (0.4, -0.2, 0.8), (0.0, 0.5, -0.6)):
        m.ell(bulb + np.array(d), (0.5, 0.4, 0.35), M_EGG_IN)
    # the ovipositor and its two sheaths, longer than the body
    if not curl:
        ov = [bulb + (-0.6, -0.2, 0), bulb + (-6.0, -1.2, 0), bulb + (-11.0, -0.4, 0), bulb + (-14.6, 1.6, 0)]
    else:
        ov = [bulb + (0.6, -0.3, 0), bulb + (7.0, 4.6, 0), bulb + (15.0, 6.2, 0), bulb + (22.0, 2.0, 0)]   # over the heads of its own
    m.limb(ov, 1, M_FANG, band=3)
    for z in (0.5, -0.5):
        m.limb([p + np.array((0, 0.4, z)) for p in ov[:3]], 1, mc, band=2 if z > 0 else 1)
    m.ell(ov[-1], (0.35, 0.35, 0.35), M_ICHOR)
    # the head: small, big dark eyes, long antennae with a white band
    hc = np.array((5.4, 8.8, 0))
    m.ell(hc, (1.5, 1.6, 1.6), mc)
    for z in (1, -1):
        m.ell(hc + (0.5, 0.4, z * 1.0), (0.9, 1.2, 0.6), M_DARKEYE)
    eyes(m, hc, [(0.0, 1.4, 0.5), (0.0, 1.4, -0.5), (0.4, 1.5, 0.0)], r=0.25)
    mandibles(m, Mat(AMBER), hc, 0.65, 0.3 if not curl else 0.75)
    for z in (1, -1):
        a0 = hc + np.array((0.7, 1.2, 0.4 * z))
        p1 = a0 + np.array((1.6, 3.6, 1.2 * z))
        p2 = p1 + np.array((3.0, 2.6, 1.6 * z))
        p3 = p2 + np.array((3.4, -0.6, 1.0 * z))
        m.limb([a0, p1], 1, mc, band=3 if z > 0 else 1)
        m.limb([p1, p2], 1, M_WHITE_BAND, band=3 if z > 0 else 1)
        m.limb([p2, p3], 1, mc, band=3 if z > 0 else 1)
    # wings: narrow and smoky, darker tips
    r0 = np.array((1.6, 9.6, 0))
    up = 0.0 if not curl else 2.4
    for z in (-0.8, 0.8):
        s = np.sign(z)
        mt = M_WING if z < 0 else M_WING_NEAR
        m.poly([r0 + (0.4, 0.2, z), r0 + (-11.0, 2.8 + up, z + 5.0 * s), r0 + (-10.0, 4.6 + up, z + 5.4 * s),
                r0 + (-4.0, 3.2 + up, z + 2.6 * s), r0 + (-0.4, 0.9, z + 0.3 * s)], mt)
        m.poly([r0 + (-9.0, 3.0 + up, z + 4.5 * s), r0 + (-11.0, 2.8 + up, z + 5.0 * s), r0 + (-10.0, 4.6 + up, z + 5.4 * s),
                r0 + (-8.6, 4.4 + up, z + 4.8 * s)], M_DARKEYE)
        m.limb([r0 + (0.2, 0.4, z), r0 + (-10.4, 3.6 + up, z + 5.2 * s)], 1, M_VEIN, band=2)
    legs(m, mc, hips=[(0.0, 7.0, 1.2), (1.8, 6.9, 1.3), (3.2, 7.2, 1.2)],
         knees=[(-4.8, 11.0, 4.4), (1.0, 10.6, 4.8), (5.4, 10.0, 4.0)],
         feet=[(-8.6, 0.0, 6.0), (0.6, 0.0, 6.4), (7.6, 0.0, 5.4)])
    return m


# ---------------------------------------------------------------- личинка
STEEL_L = Mat(ramp("#1e2228", "#3a404a", "#606874", "#949ca8", "#d0d6de"))
SKIN_L = Mat(ramp("#2a140c", "#5a3020", "#9a5a3c", "#d09070", "#f2c8a8"))


def larva(pose="idle", hue=0.0, host=None):
    """A pale grub curled a little, a dark head capsule with jaws, stubby legs. host: the trait it took from the body
    it hatched from — "iron" (a golem: steel bands), "hand" (a man: a little hand), "bones" (the undead: bone spurs)."""
    m = Model()
    if host == "iron":
        for i in (1, 3, 5):
            x = -1.4 - i * 1.7
            y = 2.4 + 0.5 * np.sin(i * 0.5)
            r = 2.1 - abs(i - 2) * 0.2
            m.ell((x, y, 0), (0.55, r * 1.06, r * 1.02), STEEL_L)
    elif host == "hand":
        s0 = np.array((-5.0, 4.2, 1.2))
        m.cyl(s0, s0 + (0.6, 2.6, 1.2), 0.55, SKIN_L, r1=0.45, seg=5)
        h = s0 + (0.9, 3.0, 1.3)
        m.ell(h, (0.7, 0.5, 0.6), SKIN_L)
        for k in range(3):
            m.cyl(h + (0.3, 0.2, -0.4 + 0.4 * k), h + (1.1, 0.7, -0.5 + 0.5 * k), 0.18, SKIN_L, seg=4)
    elif host == "bones":
        for x in (-3.0, -6.4, -9.8):
            spike(m, (x, 3.6, 0), (x - 1.0, 6.0, 0), 0.4, M_BONE)
    for i in range(7):
        x = -1.4 - i * 1.7
        y = 2.4 + 0.5 * np.sin(i * 0.5) + (0.0 if pose == "idle" else 0.4 * i * 0.2)
        r = 2.1 - abs(i - 2) * 0.2
        m.ell((x, y, 0), (1.15, r, r * 0.95), M_GRUB)
        m.ell((x - 0.8, y, 0), (0.25, r * 0.9, r * 0.88), M_GRUB_SEG)
    hc = np.array((0.8, 2.8 + (0.6 if pose == "attack" else 0.0), 0))
    m.ell(hc, (1.3, 1.3, 1.3), Mat(chitin(0.0)))
    eyes(m, hc, [(0.8, 0.5, 0.5), (0.8, 0.5, -0.5)], r=0.25)
    mandibles(m, M_FANG, hc, 0.55, 0.3 if pose == "idle" else 0.9)
    for x in (-1.4, -3.0, -4.6):
        for z in (1, -1):
            m.limb([np.array((x, 1.4, 1.2 * z)), np.array((x + 0.4, 0.0, 1.9 * z))], 1, M_GRUB_SEG, band=2)
    return m


BUILD = {"Матка": matka, "Разум улья": razum, "Пожиратель": pozhiratel, "Кукушка": kukushka, "личинка": larva}


def trim(spr, pad=2):
    """Crop a sprite to what it draws, keeping its origin."""
    ys, xs = np.nonzero(spr.a)
    if not len(xs):
        return spr
    x0, x1 = max(0, xs.min() - pad), min(spr.w, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(spr.h, ys.max() + pad + 1)
    s = Sprite(x1 - x0, y1 - y0)
    s.rgb, s.a = spr.rgb[y0:y1, x0:x1].copy(), spr.a[y0:y1, x0:x1].copy()
    s.emit = [(x - x0, y - y0, r, c, k) for (x, y, r, c, k) in spr.emit]
    s.smokes = [(x - x0, y - y0, r) for (x, y, r) in spr.smokes]
    s.ox, s.oy = spr.ox - x0, spr.oy - y0
    return s


# ---------------------------------------------------------------- development: what each choice adds to the body
DEV = {
    "Матка": [("often", "Кладка чаще", "откладывает каждые 2 хода — яйца светятся сквозь брюшко, кладка больше"),
              ("larva", "+1 личинка", "личинки вылупляются по три и цепляются за неё"),
              ("size", "+1 к размеру", "размер 7 — гнездо на 3 клетки; корона выше")],
    "Разум улья": [("two", "Захват чаще", "вторая пара перистых усов: перезарядка Захвата 4 хода"),
                   ("every", "Пси-удар дальше", "мозг весь светится узлами: бьёт на 4 клетки"),
                   ("strike", "Помутнение шире", "шипы по борозде: волна на 3 клетки")],
    "Пожиратель": [("bigger", "Стартует крупнее", "бой начинает размером 6"),
                   ("every_kill", "Растёт с каждого тела", "раздутое брюхо светится ихором"),
                   ("heal", "Лечится вдвое", "второй желудок-мешок на спине")],
    "Кукушка": [("three", "Личинок 3", "мешочек с тремя крупными яйцами"),
                ("venom", "Заражает и яд скорпионов", "ядовитая железа, яйцеклад сочится ядом"),
                ("two", "Подкидышей двое", "несёт рабочую под брюхом")],
}


def add_dev(m, name, dev, pose, hue=0.0):
    """The development the leader took, on its body (coordinates as in its builder)."""
    if not dev:
        return
    if name == "Матка":
        mc = mat(QUEEN, hue)
        gc, gx, gy, gz = np.array((-14.0, 7.0, 0)), 15.5, 6.6, 6.6
        if dev == "often":
            rng = np.random.default_rng(9)
            for _ in range(16):
                x = rng.uniform(-27.0, -2.0)
                t = (x - gc[0]) / gx
                kk = np.sqrt(max(0.05, 1 - t * t))
                a = rng.uniform(-0.6, 0.3)
                m.ell((x, gc[1] + gy * kk * np.sin(a) * 0.9, gz * kk * np.cos(a) * 0.95), (1.1, 0.8, 0.6), M_EGG_IN)
            for ex, ey, ez in ((-37.0, 1.0, 0.2), (-38.4, 1.0, 2.2), (-36.6, 2.6, 1.2), (-39.0, 1.0, -1.6), (-37.6, 2.6, -0.8),
                               (-40.4, 1.0, 0.6), (-35.2, 1.0, 3.4)):
                m.ell((ex, ey, ez), (1.3, 0.95, 0.95), W.M_EGG)
        elif dev == "larva":
            for (x, y, z, r) in ((-4.0, 0.0, 10.0, 0.5), (4.0, 0.0, 11.0, -0.2), (15.5, 0.0, 6.0, 0.3),
                                 (-12.0, gc[1] + gy * 0.92, 1.2, 0.0)):
                lv = larva("idle").transformed(rot_y(r), (0, 0, 0)).scaled(0.75)
                m.extend(lv.transformed(I3, (x, y, z)))
        elif dev == "size":
            hc = np.array((10.0, 8.0, 0))
            for a, L in ((-0.6, 5.6), (-0.2, 6.6), (0.2, 6.6), (0.6, 5.6)):
                base = hc + np.array((-0.6, 2.0, np.sin(a) * 1.4))
                W.spike(m, base, base + np.array((-L * 0.45, L, np.sin(a) * L * 0.5)), 0.6, M_BONE)
    elif name == "Разум улья":
        mc = mat(HIVE, hue)
        bc, bx, by, bz = np.array((1.4, 11.2, 0)), 7.0, 5.9, 6.3
        if dev == "two":
            for z in (1, -1):
                a0 = bc + np.array((bx * 0.4, by * 0.8, 1.2 * z))
                mid = a0 + np.array((1.6, 3.6, 1.4 * z))
                tip = mid + np.array((4.4, 2.6, 2.4 * z))
                m.limb([a0, mid, tip], 1, mc, band=3 if z > 0 else 1)
                for f in (0.25, 0.5, 0.75):
                    p = mid + (tip - mid) * f
                    m.limb([p, p + np.array((-0.6, 1.2, 0.5 * z))], 1, mc, band=2)
                m.ell(tip, (0.65, 0.65, 0.65), M_PHERO)
        elif dev == "every":
            rng = np.random.default_rng(13)
            for _ in range(18):
                th, ph = rng.uniform(0.1, 1.4), rng.uniform(-0.4, 1.9)
                n = np.array((np.sin(th) * np.cos(ph), np.cos(th), np.sin(th) * np.sin(ph)))
                m.ell(bc + n * np.array((bx, by, bz)) * 1.0, (0.6, 0.6, 0.6), M_PHERO)
        elif dev == "strike":
            for x in np.linspace(-4.5, 5.0, 6):
                p = bc + np.array((x, by * np.sqrt(max(0.0, 1 - (x / bx) ** 2)) - 0.2, 0))
                W.spike(m, p, p + np.array((-1.0, 2.6, 0)), 0.55, M_BONE)
            mandibles(m, M_BONE, np.array((6.6, 6.0, 0)), 1.3, 0.3 if pose == "idle" else 0.85)
    elif name == "Пожиратель":
        ac = np.array((-7.6, 5.6, 0))
        if dev == "every_kill":
            m.ell(ac + (0.4, -1.2, 0.0), (6.6, 3.4, 5.4), M_BLOODY)
            for x in (-12.0, -9.0, -6.0, -3.0):
                m.limb([np.array((x, ac[1] - 3.6, 4.0)), np.array((x + 1.0, ac[1] - 0.4, 5.2))], 1, M_CRACK, band=2)
            m.ell(ac + (1.0, -2.6, 4.6), (2.2, 1.0, 0.6), M_CRACK)
        elif dev == "heal":
            c = np.array((-6.0, 11.2, 0))
            m.ell(c, (4.4, 3.0, 3.4), M_SAC)
            for z in (1, -1):
                m.limb([c + (-3.0, 1.2, 2.6 * z), c + (0.0, 2.6, 3.0 * z), c + (3.0, 1.0, 2.4 * z)], 1, M_VEIN_R, band=2)
            m.ell(c + (1.4, 1.6, 2.0), (1.0, 0.6, 0.8), M_BLOODY)
    elif name == "Кукушка":
        curl = pose == "attack"
        tip = np.array((-14.4, 5.8, 0)) if not curl else np.array((-4.6, 1.8, 0))
        bulb = tip + (np.array((-1.4, -0.6, 0)) if not curl else np.array((1.0, -0.4, 0)))
        if dev == "three":
            m.ell(bulb, (2.8, 2.3, 2.1), M_MEMBRANE)
            for d in ((-1.0, 0.3, 1.5), (0.8, -0.1, 1.6), (0.0, 1.0, 1.3)):
                m.ell(bulb + np.array(d), (1.0, 0.8, 0.7), W.M_EGG)
        elif dev == "venom":
            m.ell(bulb + (0.6, 1.2, 0), (1.4, 1.1, 1.1), W.M_ACID)
            far = np.array((-30.0, 6.8, 0)) if not curl else np.array((11.0, 2.0, 0))
            for f in (0.3, 0.55, 0.8, 1.0):
                p = bulb + (far - bulb) * f
                m.ell(p + (0, -0.6, 0), (0.35, 0.55, 0.35), W.M_ACID)
        elif dev == "two":
            ant = W.body(0.12, (), "idle", False, genes=W.genes_for(5))
            m.extend(ant.transformed(rot_z(0.5), (0.0, 0.0, 0)).scaled(0.85).transformed(I3, (4.6, 2.2, 1.0)))


def build(name, pose="idle", k=1.0, stage=0, hue=0.0, dev=None, host=None):
    """k multiplies the in-game scale, as in swarm1.build. dev: the development taken (see DEV)."""
    if name == "Пожиратель" and dev == "bigger":
        stage = max(stage, 1)
    size = SIZE[name] + (stage if name == "Пожиратель" else 0) + (1 if (name == "Матка" and dev == "size") else 0)
    s = SCALE[size] * k
    if name == "Пожиратель":
        m = pozhiratel(pose, stage, hue)
    elif name == "личинка":
        m = larva(pose, hue, host)
    else:
        m = BUILD[name](pose, hue)
    add_dev(m, name, dev, pose, hue)
    w, h, ox, oy = int(110 * s), int(70 * s), int(70 * s), int(56 * s)
    spr = W.rim_light(render(m.scaled(s), w, h, ox, oy, **W.STYLE1))
    spr.ox, spr.oy = ox, oy
    return trim(spr)


LEADERS = [
    ("Матка", "размер 6 · число и порода", 1.4,
     [("Кладка", "каждые 3 хода: 2 личинки; дожившие уйдут в выводок с чертой, что больше убивала"),
      ("Сердце роя", "постоянно: погибшая рядом своя роняет яйцо — через 2 хода личинка"),
      ("Плодовитость", "поход: в выводке на потомка больше, кормление вдвое дешевле"),
      ("Медлительная", "слабость: скорость 1, держится в тылу", 1)]),
    ("Разум улья", "размер 4 · рой, который думает: урон пси", 1.9,
     [("Пси-удар", "атака: мыслью на 3 клетки, мимо брони"),
      ("Помутнение", "каждые 3 хода: враги рядом путают цели, у машин сбой"),
      ("Предсмертный крик", "постоянно: погибшая особь бьёт убийцу 1 пси"),
      ("Захват разума", "перезарядка 6: раненый враг за рой — мелкий 5 ходов, средний 2"),
      ("Мыслящая порода", "поход: в выводке выпадают пси-мутации — на пси и страх"),
      ("Хрупкий мозг", "слабость: мало здоровья, мягкое тело; гибель обезглавливает рой", 1)]),
    ("Пожиратель", "размер 5–7 · зверь растёт в бою", 1.3,
     [("Рост", "каждые 2 съеденных тела, свои тоже: здоровье ×1,4 и +2 к удару — до размера 7"),
      ("Каннибал", "постоянно: ест погибших своих рядом, как чужих"),
      ("Всё в пасть", "поход: съеденное в бою — биомасса, она идёт в его рост; рой меньше"),
      ("Ненасытный", "слабость: три раунда без еды — съедает живую свою особь рядом", 1)]),
    ("Кукушка", "размер 3 · рой растёт за счёт врага", 2.2,
     [("Длинный яйцеклад", "постоянно: колет на 2 клетки и раньше всех — инициатива +3"),
      ("Яйцеклад", "атака: заражает; живой, погибнув, выпускает 2 личинки, машина — гнездо"),
      ("Дети хозяина", "постоянно: личинки берут черту хозяина и уходят в выводок химерами"),
      ("Подкидыш", "в начале боя: одна рабочая оказывается в тылу врага"),
      ("Чужие черты", "поход: чужие черты чаще и безумнее, у особи их может быть две"),
      ("Хрупкая кладка", "слабость: огонь выжигает кладку — заражённый очищается", 1)]),
]
ACCENT = ["#e0609a", "#b080ff", "#ff6a3a", "#e8a040"]


def sheet():
    """The Swarm's four leaders like the Foundry's sheet: each at rest and attacking (the Devourer at its three
    sizes), what they do, and a row in the true relative scale with the Guard for comparison."""
    from leaders_sheet import canvas, put, fonts, S as SS, GOLD, INK, MUT, BAD
    import frames as F
    from paths import out
    WW, HH, QH = 960, 860, 290
    sc = canvas(WW, HH, 23)
    caps = []
    for i, (name, _, k, _) in enumerate(LEADERS):
        x0, y0 = (i % 2) * 480, 50 + (i // 2) * QH
        sc.glow(x0 + 220, y0 + 150, 190, hexc(ACCENT[i]), 0.26)
        by = y0 + 178
        if name == "Пожиратель":
            for j, (st, p) in enumerate(((0, "idle"), (1, "idle"), (2, "attack"))):
                spr = build(name, p, k, stage=st)
                cx = x0 + 85 + j * 150
                put(sc, spr, cx, by, spr.w * 0.36)
                caps.append((cx, by + 22, ("размер 5", "размер 6", "размер 7 · атака")[j]))
        else:
            for j, p in enumerate(("idle", "attack")):
                spr = build(name, p, k)
                cx = x0 + (175 if name == "Матка" else 130) + j * (228 if name == "Матка" else 210)
                put(sc, spr, cx, by, spr.w * 0.36)
    yb = 50 + 2 * QH + 140
    r = 1.15 / 1.8                                         # the same ratio as on the Foundry's sheet
    row = [(build("Пожиратель", "idle", r, stage=2), "Пожиратель · 7"),
           (build("Матка", "idle", r), "Матка · 6"),
           (F.build("Страж", "idle", k=2.2 * r), "Страж · 6"),
           (build("Пожиратель", "idle", r), "Пожиратель · 5"),
           (build("Разум улья", "idle", r), "Разум улья · 4"),
           (build("Кукушка", "idle", r), "Кукушка · 3"),
           (W.build((), 0.0, "idle", soldier=True, k=r), "солдат · 2"),
           (W.build((), 0.0, "idle", k=r), "рабочая · 1"),
           (build("личинка", "idle", r), "личинка")]
    xs = [75, 200, 315, 410, 500, 585, 665, 740, 815]
    for (spr, _), x in zip(row, xs):
        put(sc, spr, x, yb, max(6, spr.w * 0.4))
    img = sc.image(SS)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    d.text((24, 16), "Рой: четыре лидера", font=ft, fill=INK)
    d.text((24, 60), "Лидер — особь на поле. У всех хитин, Стая и Пожирание; гибель лидера — рой проверяет страх "
                     "(«Обезглавленный рой»). Красным — слабость.", font=fr, fill=MUT)
    for i, (name, sub, _, ab) in enumerate(LEADERS):
        x0, y0 = (i % 2) * 480 * SS, (50 + (i // 2) * QH) * SS
        d.text((x0 + 24, y0 + 6), name, font=fh, fill=tuple(int(c) for c in hexc(ACCENT[i])))
        d.text((x0 + 24 + d.textlength(name, font=fh) + 12, y0 + 12), sub, font=fr, fill=MUT)
        y = y0 + 210 * SS
        for nm, txt, *neg in ab:
            d.text((x0 + 24, y), nm, font=fbs, fill=BAD if neg else INK)
            d.text((x0 + 24 + d.textlength(nm, font=fbs) + 10, y + 1), txt, font=fr, fill=MUT)
            y += 24
    for x, y, t in caps:
        d.text((x * SS - d.textlength(t, font=fr) / 2, y * SS), t, font=fr, fill=MUT)
    d.text((24, (50 + 2 * QH) * SS + 6), "Масштаб: всё в настоящем соотношении размеров, Страж Литейщика для сравнения",
           font=fh, fill=GOLD)
    for (_, label), x in zip(row, xs):
        d.text((x * SS - d.textlength(label, font=fr) / 2, (yb + 8) * SS), label, font=fr, fill=INK)
    img.save(out("swarm_leaders.png"))
    print("swarm_leaders.png", img.size)


def dev_sheet():
    """Each leader as it starts and with each of its three developments."""
    from PIL import ImageFont
    from leaders_sheet import canvas, put, fonts, S as SS, GOLD, INK, MUT
    from paths import out, font
    K = {"Матка": 0.95, "Разум улья": 1.7, "Пожиратель": 1.1, "Кукушка": 1.55}
    RH = {"Матка": 150, "Разум улья": 142, "Пожиратель": 132, "Кукушка": 124}
    WW, Y0, CWD = 960, 60, 240
    HH = Y0 + sum(RH.values()) + 8
    sc = canvas(WW, HH, 47)
    labels, y0 = [], Y0
    for r, (name, devs) in enumerate(DEV.items()):
        by = y0 + RH[name] - 52
        for j, dv in enumerate([None] + [d[0] for d in devs]):
            cx = 120 + j * CWD
            spr = build(name, "idle", K[name], dev=dv)
            put(sc, spr, cx, by, spr.w * 0.34)
            labels.append(("cap", cx, by + 8, ("как начинает", "") if dv is None else next((n, w) for k, n, w in devs if k == dv)))
        labels.append(("head", 24, y0 + 2, (name, ACCENT[[l[0] for l in LEADERS].index(name)])))
        y0 += RH[name]
    img = sc.image(SS)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    small = ImageFont.truetype(font("PTSerif-Regular.ttf"), 14)
    d.text((24, 16), "Рой: развитие лидеров", font=ft, fill=INK)
    d.text((24, 60), "После босса лидер получает развитие — один вариант из предложенных. Каждый виден на спрайте.",
           font=fr, fill=MUT)
    for kind, x, y, v in labels:
        if kind == "head":
            d.text((x * SS, y * SS), v[0], font=fh, fill=tuple(int(c) for c in hexc(v[1])))
            continue
        name, what = v
        d.text((x * SS - d.textlength(name, font=fbs) / 2, y * SS), name, font=fbs, fill=INK if what else MUT)
        words, lines, cur = what.split(" "), [], ""
        for wd in words:
            if d.textlength(cur + " " + wd, font=small) > (CWD - 16) * SS and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for n, ln in enumerate(lines[:2]):
            d.text((x * SS - d.textlength(ln, font=small) / 2, y * SS + 22 + n * 18), ln, font=small, fill=MUT)
    img.save(out("swarm_development.png"))
    print("swarm_development.png", img.size)


if __name__ == "__main__":
    import sys
    from paths import out
    if "dev" in sys.argv[1:]:
        dev_sheet()
        raise SystemExit
    if "check" not in sys.argv[1:]:
        sheet()
        raise SystemExit
    items = [("Матка", 0), ("Разум улья", 0), ("Пожиратель", 0), ("Пожиратель", 1), ("Пожиратель", 2), ("Кукушка", 0),
             ("личинка", 0)]
    K = 1.4
    sprs = [[build(n, p, K, st) for p in ("idle", "attack")] for n, st in items]
    Wd = sum(max(a.w, b.w) + 16 for a, b in sprs)
    Hd = max(a.h for a, _ in sprs) + max(b.h for _, b in sprs) + 24
    sc = Scene(Wd, Hd)
    sc.rgb[:] = hexc("#2c2436")
    x = 8
    for a, b in sprs:
        cw = max(a.w, b.w)
        sc.blit(a, x + (cw - a.w) // 2, max(s.h for s, _ in sprs) - a.h + 4)
        sc.blit(b, x + (cw - b.w) // 2, Hd - b.h - 4)
        x += cw + 16
    sc.image(2).save(out("swarm_leaders_check.png"))
    print(Wd, Hd)
