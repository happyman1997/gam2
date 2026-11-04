"""Foundry leaders (style 1): a small human riding a walking machine. Leaders are units on the field."""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_BRONZE, M_HOLE, STYLE1
from golem7 import tbox, M_PUFF, M_SPARK

SKIN = Mat(ramp("#3a2216", "#6a4028", "#a06a44", "#cc9a6a", "#ecc8a0"))
LEATHER = Mat(ramp("#1e120a", "#3a2414", "#5a3a20", "#7c5430", "#a07444"))
CLOTH_RED = Mat(ramp("#1e0808", "#400e10", "#6a1a1a", "#942a24", "#c04434"))
CLOTH_BLUE = Mat(ramp("#0c1020", "#18203a", "#263458", "#3a4c7a", "#5a6c9e"))
HAIR = Mat(ramp("#120c08", "#22180e", "#3a2a18", "#5a4428", "#7a603a"))
LINEN = Mat(ramp("#3a3428", "#6a604c", "#9a8e72", "#c8bc9a", "#ece2c4"))
GLASS = Mat(ramp("#0c2a34", "#145060", "#2a8ca0", "#6ad0de", "#d0f8ff"), emissive=hexc("#60d8f0"), glow_r=4, glow_k=0.3)
FORGE = Mat(EMBER, emissive=hexc("#ff7a20"), glow_r=20, glow_k=0.8)
FLAME = Mat(ramp("#7a2008", "#c0400e", "#f07a1a", "#ffc040", "#fff4b0"), emissive=hexc("#ff9030"), glow_r=26, glow_k=0.95)


def human(m, base, cloth, pose="idle", hammer=False, tool=None, robe=False, beard=False, goggles=False, apron=False):
    """A small figure about 11 units tall standing at `base`, facing +x."""
    b = np.array(base, float)
    if robe:
        tbox(m, b + (0, 3.2, 0), (4.6, 4.6), (2.6, 2.8), 6.4, cloth)
    else:
        for z in (-0.8, 0.8):
            m.box(b + (0, 1.6, z), (1.2, 3.2, 1.1), LEATHER)
        tbox(m, b + (0, 4.4, 0), (2.6, 2.4), (3.0, 3.0), 3.2, cloth)
    tbox(m, b + (0, 7.2, 0), (2.8, 2.6), (3.4, 3.4), 3.2, cloth)
    if apron:
        tbox(m, b + (1.55, 4.8, 0), (0.5, 2.6), (0.5, 2.2), 6.0, LEATHER)
    h = b + (0.2, 10.0, 0)
    m.ell(h, (1.3, 1.4, 1.3), SKIN)
    m.ell(h + (-0.4, 0.6, 0), (1.25, 1.0, 1.35), HAIR if not robe else cloth)
    if robe:
        m.ell(h + (-0.3, 0.4, 0), (1.6, 1.7, 1.6), cloth)        # hood
        m.ell(h + (0.45, 0.0, 0), (1.0, 1.1, 1.1), SKIN)
    if beard:
        m.ell(h + (0.6, -1.0, 0), (0.9, 1.1, 1.0), HAIR)
    if goggles:
        for z in (-0.5, 0.5):
            m.ell(h + (1.15, 0.2, z), (0.25, 0.4, 0.4), GLASS)
    sh = b + (0, 8.4, 0)
    # near arm
    if hammer:
        up_ = pose == "idle"
        hand = sh + ((1.6, 2.6, 1.8) if up_ else (3.0, -1.0, 1.8))
        m.cyl(sh + (0, 0, 1.6), hand, 0.55, cloth, seg=5)
        top = hand + ((1.0, 4.2, 0) if up_ else (4.2, -0.8, 0))
        m.cyl(hand, top, 0.3, LEATHER, seg=4)
        m.box(top, (2.4, 1.4, 1.4), M_IRON, rot_z(np.arctan2(top[1] - hand[1], top[0] - hand[0]) - np.pi / 2))
    else:
        m.cyl(sh + (0, 0, 1.6), sh + (1.6, -2.4, 1.9), 0.55, cloth, seg=5)
    m.cyl(sh + (0, 0, -1.6), sh + (1.8, -2.2, -1.9), 0.55, cloth, seg=5)
    if tool == "staff":
        m.cyl(b + (1.8, 0, -2.0), b + (2.4, 14.5, -2.2), 0.35, LEATHER, seg=4)
        m.ell(b + (2.5, 15.6, -2.2), (1.0, 1.5, 1.0), FLAME)
    if tool == "wrench":
        m.cyl(sh + (1.6, -2.4, 1.9), sh + (3.2, -0.6, 2.0), 0.35, M_IRON, seg=4)
        m.box(sh + (3.4, -0.4, 2.0), (0.9, 1.4, 0.7), M_IRON)


def forge_walker(pose="idle"):
    """The Forgemaster: a smith on a walking forge, mending golems nearby."""
    m = Model()
    for x in (-4.5, 4.5):
        for z in (-4.0, 4.0):
            tbox(m, (x, 3.0, z), (3.6, 3.6), (3.0, 3.0), 6.0, M_BRONZE)
            m.box((x + 0.8, 0.5, z), (5.0, 1.0, 4.0), M_IRON)
    tbox(m, (0, 10.5, 0), (15, 12), (13, 10.5), 9, M_DIRON)
    m.box((0, 15.4, 0), (15.5, 1.0, 12.5), M_BRONZE)
    m.box((7.1, 10.0, 0), (1.4, 5.0, 6.0), M_HOLE)                 # forge mouth
    m.box((7.5, 9.8, 0), (0.6, 4.0, 5.0), FORGE)
    for z in (-1.6, 0, 1.6):
        m.box((7.9, 10.0, z), (0.5, 5.4, 0.5), M_DIRON)
    m.cyl((-4.5, 15.5, -2.5), (-5.0, 27, -2.5), 1.6, M_DIRON, seg=8)
    m.cyl((-5.0, 27, -2.5), (-5.0, 28.2, -2.5), 2.2, M_DIRON, seg=8)
    for i, d in enumerate(((-5.5, 30.5, -2.5), (-7.5, 34, -2), (-10.5, 37, -2.5))):
        m.ell(d, (2.4 + i * 0.6, 2.2, 2.2), M_PUFF)
    for d in ((-4.0, 31, -1.5), (-6.0, 33, -3.0)):
        m.ell(d, (0.45, 0.45, 0.45), M_SPARK)
    tbox(m, (5.0, 17.2, 2.5), (4.0, 2.2), (5.0, 2.6), 2.4, M_DIRON)  # anvil
    human(m, (0.5, 16.0, -1.0), LINEN, pose, hammer=True, beard=True, apron=True)
    if pose == "attack":
        for d in ((6.0, 19.5, 2.5), (7.0, 20.5, 3.4), (5.0, 21.0, 1.6)):
            m.ell(d, (0.5, 0.5, 0.5), M_SPARK)
    return m


def spider_workshop(pose="idle"):
    """The Inventor: an engineer on a spider-legged workshop with a crane arm."""
    m = Model()
    for s in (1, -1):
        for f in (-1, 0, 1):
            h = np.array((f * 4.5, 9.0, s * 4.5))
            kn = np.array((f * 8.5, 13.0, s * 9.5))
            ft = np.array((f * 11.0, 0.2, s * 12.0))
            m.cyl(h, kn, 1.3, M_IRON, seg=6)
            m.ell(kn, (1.6, 1.6, 1.6), M_BRONZE)
            m.cyl(kn, ft, 1.0, M_IRON, r1=0.3, seg=6)
    tbox(m, (0, 9.5, 0), (14, 11), (16, 12), 3.0, M_BRONZE)
    for x in (-7.5, 7.5):
        m.box((x, 12.0, 0), (0.4, 2.0, 11.5), M_DIRON)
    m.box((-4.5, 12.6, 3.0), (3.0, 3.0, 3.0), LEATHER)
    m.box((-4.0, 12.2, -2.8), (2.4, 2.4, 2.4), M_IRON)
    m.cyl((-5.5, 12.0, -1.0), (-5.0, 22.0, -1.0), 0.9, M_DIRON, seg=6)   # crane
    tip = np.array((7.0, 22.0, -1.0)) if pose == "idle" else np.array((11.0, 17.0, -1.0))
    m.cyl((-5.0, 22.0, -1.0), tip, 0.8, M_DIRON, seg=6)
    m.ell((-5.0, 22.0, -1.0), (1.2, 1.2, 1.2), M_BRONZE)
    m.cyl(tip, tip + (0, -4.5, 0), 0.25, M_DIRON, seg=4)
    for d in ((1.4, -2.0, 0.8), (1.8, -0.6, 0), (1.4, -2.0, -0.8)):
        m.cyl(tip + (0, -4.5, 0), tip + (0, -4.5, 0) + np.array(d), 0.4, M_IRON, r1=0.12, seg=4)
    for z in (-2.2, 2.2):
        m.ell((-1.0, 15.8, z), (1.4, 1.4, 1.4), M_BRONZE)     # gear hubs
    human(m, (2.5, 11.0, 0.5), CLOTH_BLUE, pose, goggles=True, tool="wrench")
    return m


def brazier_walker(pose="idle"):
    """The Flamekeeper: a hooded keeper of the core-fire in front of a walking brazier."""
    m = Model()
    for a in (0.0, 2.1, 4.2):
        ft = np.array((np.cos(a) * 8.5, 0.2, np.sin(a) * 8.5))
        kn = np.array((np.cos(a) * 7.0, 9.0, np.sin(a) * 7.0))
        m.cyl((0, 13.0, 0), kn, 1.2, M_BRONZE, seg=6)
        m.cyl(kn, ft, 1.0, M_IRON, r1=0.35, seg=6)
    m.cyl((0, 13.0, 0), (0, 19.0, 0), 4.0, M_IRON, r1=7.0, seg=10)      # the bowl
    m.cyl((0, 18.6, 0), (0, 19.4, 0), 7.4, M_BRONZE, seg=10)
    big = 1.0 if pose == "idle" else 1.35
    for (x, y, z, r) in ((0, 21.5, 0, 3.6), (-1.5, 25.0, 0.8, 2.6), (1.2, 27.5, -0.6, 1.8), (-0.5, 30.0, 0.2, 1.1)):
        m.ell((x, y + (big - 1) * 3, z), (r * big, r * 1.3 * big, r * big), FLAME)
    for d in ((2.5, 31, 1.0), (-2.0, 33, -1.0), (0.5, 35, 0.5)):
        m.ell(d, (0.45, 0.45, 0.45), M_SPARK)
    human(m, (9.0, 0.0, 2.5), CLOTH_RED, pose, robe=True, tool="staff")
    return m


LEADERS = {"forge": (forge_walker, "Мастер кузни"), "spider": (spider_workshop, "Изобретатель"),
           "brazier": (brazier_walker, "Хранительница пламени")}


def build(key, pose="idle", k=1.0):
    fn, _ = LEADERS[key]
    s = 1.55 * k        # leaders are size 4
    w, h, ox, oy = int(52 * s), int(56 * s), int(24 * s), int(46 * s)
    spr = render(fn(pose).scaled(s), w, h, ox, oy, **STYLE1)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    from paths import out
    sprs = [build(k_, p, k=1.4) for k_ in LEADERS for p in ("idle", "attack")]
    w, h = sprs[0].w, sprs[0].h
    sc = Scene(w * 6, h)
    sc.rgb[:] = hexc("#2c2436")
    for i, s_ in enumerate(sprs):
        sc.blit(s_, i * w, 0)
    sc.image(2).save(out("test_leaders.png"))
