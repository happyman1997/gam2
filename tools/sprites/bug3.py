"""Swarm creatures in 3/4 view: base body + inherited parts, idle and attack sprites."""
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, I3

M_BONE = Mat(BONE)
M_WING = Mat(WING)
M_GLOW = Mat(GLOWG, emissive=hexc("#7ae040"), glow_r=7, glow_k=0.45)
M_EYE = Mat(GLOWG, emissive=hexc("#9af060"), glow_r=7, glow_k=0.5)
M_VENOM = Mat(GLOWG, emissive=hexc("#8af04a"), glow_r=10, glow_k=0.8)
EGG = ramp("#173a12", "#24561a", "#3c8a26", "#62b83a", "#a8e070")
M_EGG = Mat(EGG, emissive=hexc("#6ad040"), glow_r=0, glow_k=0)

W, H, OX, OY = 72, 62, 32, 56


def pivot(m, R, p):
    p = np.array(p, float)
    return m.transformed(R, p - R @ p)


def legs(m, mc, y0, pose, lift=0.0):
    """Three pairs. In attack the front pair rears up."""
    for side in (1, -1):
        for i, (x, dx) in enumerate(((-3, -3.5), (0.5, 0.5), (4, 4))):
            hip = np.array((x, y0 - 1.5, 3.2 * side))
            knee = np.array((x + dx, y0 + 2.5, 7.5 * side))
            foot = np.array((x + dx * 1.6, lift, 10.5 * side))
            if pose == "attack" and i == 2:
                knee = np.array((x + 5, y0 + 5, 6 * side))
                foot = np.array((x + 9, y0 + 3, 7 * side))
            m.limb([hip, knee, foot], 1, mc, band=3 if side > 0 else 1)


def body(hue=0.0, traits=(), pose="idle"):
    c = chitin(hue)
    mc = Mat(c)
    shell = Mat([c[0] * 0.8, c[0], c[1], c[2], c[3]])
    m = Model()
    y0 = 8.0
    jaw = 0.35 if pose == "idle" else 0.75

    m.ell((-9, y0 + 1, 0), (8, 6.2, 6.2), mc)                       # abdomen
    for (gx, gy, gz) in ((-12, y0 + 6.2, 2.2), (-8, y0 + 6.9, -0.5), (-4.5, y0 + 5.6, 2.8)):
        m.ell((gx, gy, gz), (1.0, 0.8, 1.0), M_GLOW)
    m.ell((0.5, y0, 0), (4.6, 4.2, 4.2), mc)                       # thorax
    m.ell((7, y0 + 1, 0), (4.4, 3.9, 3.9), mc)                     # head
    for z in (2.4, -2.4):
        m.ell((9.6, y0 + 2.4, z), (1.1, 1.1, 1.1), M_EYE)
        # mandibles open wider when biting
        base = np.array((10.5, y0 - 0.5, z * 0.6))
        tip = base + np.array((np.cos(jaw) * 4, -1.2, np.sign(z) * np.sin(jaw) * 4))
        m.cyl(base, tip, 0.9, M_BONE, r1=0.2, seg=5)
        m.limb([(9, y0 + 4, z * 0.6), (11, y0 + 9, z * 1.2), (14.5, y0 + 10.5, z * 1.8)], 1, mc, band=3)

    if "carapace" in traits:
        m.ell((-9, y0 + 2.4, 0), (8.6, 5.6, 6.8), shell)
        m.ell((0.5, y0 + 1.4, 0), (4.9, 3.8, 4.6), shell)
        for x in (-14, -10, -6, -2):
            yb = y0 + 7.6 if x < -3 else y0 + 5.2
            m.cyl((x, yb - 1.2, 0), (x - 1, yb + 2.4, 0), 1.0, M_BONE, r1=0.2, seg=5)
        m.cyl((8.5, y0 + 4, 0), (13, y0 + 10, 0), 1.6, M_BONE, r1=0.3, seg=6)   # horn

    if "stinger" in traits:
        if pose == "idle":
            chain = [(-16, y0 + 2), (-18.5, y0 + 5.5), (-19, y0 + 9.5), (-17, y0 + 13), (-13.5, y0 + 14.5)]
            tip_from, tip_to = (-12.5, y0 + 14.5), (-8.5, y0 + 12)
        else:  # whips over the back towards the target
            chain = [(-16, y0 + 3), (-16, y0 + 8), (-12, y0 + 12.5), (-6, y0 + 15), (0, y0 + 15.5)]
            tip_from, tip_to = (1, y0 + 15.5), (7, y0 + 11)
        for i, (x, y) in enumerate(chain):
            r = 2.3 - i * 0.2
            m.ell((x, y, 0), (r, r, r), mc)
        m.cyl((*tip_from, 0), (*tip_to, 0), 1.3, M_BONE, r1=0.25, seg=6)
        m.ell((tip_to[0], tip_to[1] - 0.5, 0), (0.9, 0.9, 0.9), M_VENOM)
        if pose == "attack":
            m.ell((tip_to[0] + 4, tip_to[1] - 3, 0), (1.1, 1.1, 1.1), M_VENOM)

    if "wings" in traits:
        up = 0 if pose == "idle" else 6
        for z, mat_band in ((-2.5, 1), (2.5, 3)):
            sgn = 1 if z > 0 else -1
            m.poly([(1, y0 + 4, z), (-2, y0 + 4.5, z), (-18, y0 + 7 + up, z + 5 * sgn), (-12, y0 + 9 + up, z + 2.5 * sgn)], M_WING)
            m.limb([(0, y0 + 4.3, z), (-15, y0 + 8 + up, z + 4 * sgn)], 1, M_WING, band=mat_band)

    hover = 7.0 if "wings" in traits else 0.0
    legs(m, mc, y0, pose, lift=hover * 0.6 if hover else 0.0)
    if hover:
        m = m.transformed(I3, (0, hover, 0))
    if pose == "attack":
        lean = -0.18 if "wings" not in traits else -0.35
        m = pivot(m, rot_z(lean), (0, hover + 2, 0))
        m = m.transformed(I3, (3, 0, 0))
    return m


SCALE = 1.3


def build(traits=(), hue=0.0, pose="idle"):
    return render(body(hue, traits, pose).scaled(SCALE), W, H, OX, OY)


QW, QH, QOX, QOY = 104, 80, 60, 74


def queen(hue=0.0, pose="idle"):
    c = chitin(hue)
    mc = Mat(c)
    m = Model()
    segs = [((-36, 16, 0), (7, 9, 9)), ((-28, 17, 0), (10, 13.5, 12.5)),
            ((-17, 17.5, 0), (12, 15.5, 14.5)), ((-6, 15.5, 0), (10, 13, 12.5))]
    for cc, rr in segs:
        m.ell(cc, rr, mc)
    rnd = np.random.default_rng(5)
    for (cc, rr) in segs[1:]:
        for _ in range(7):
            th, ph = rnd.uniform(0.15, 1.35), rnd.uniform(-0.55, 0.75)
            d = np.array((np.cos(ph) * np.sin(th) * 0.55, np.sin(ph), np.cos(ph) * np.cos(th)))
            p = np.array(cc) + d * np.array(rr) * 0.97
            m.ell(p, (1.9, 1.6, 1.9), M_EGG)
    m.ell((-14, 12, 12), (0.1, 0.1, 0.1), Mat(EGG, emissive=hexc("#6ad040"), glow_r=24, glow_k=0.35))
    head_up = 0 if pose == "idle" else 5
    m.ell((5, 12, 0), (7.5, 6.5, 6.5), mc)                       # thorax
    hc = np.array((14, 15 + head_up, 0))
    m.ell(hc, (5.5, 5, 5), mc)
    for z in (2.8, -2.8):
        m.ell(hc + (3.2, 1.5, z), (1.3, 1.3, 1.3), M_EYE)
        m.limb([hc + (-1, 3.5, z * 0.5), hc + (-4, 9, z), hc + (-10, 12.5, z * 1.3), hc + (-15, 11.5, z * 1.5)], 2, Mat(BONE), band=3 if z > 0 else 2)
        jaw = 0.4 if pose == "idle" else 0.9
        base = hc + (4.5, -2.5, z * 0.5)
        m.cyl(base, base + (np.cos(jaw) * 4.5, -1.5, np.sign(z) * np.sin(jaw) * 4.5), 1.1, M_BONE, r1=0.25, seg=5)
    if pose == "attack":     # spits a glob of acid
        m.ell(hc + (10, -2, 0), (2.6, 2.2, 2.2), M_VENOM)
        m.ell(hc + (14.5, -3.5, 0), (1.3, 1.3, 1.3), M_VENOM)
    for side in (1, -1):
        for x in (1, 5, 9):
            m.limb([(x, 7, 4 * side), (x + 2, 10, 8.5 * side), (x + 3, 0, 10.5 * side)], 1, mc, band=3 if side > 0 else 1)
    return render(m, QW, QH, QOX, QOY)


if __name__ == "__main__":
    from paths import out
    sets = [((), 0.0), (("wings",), -0.08), (("stinger",), 0.06), (("carapace",), -0.16)]
    sc = Scene(4 * W, 2 * H)
    sc.rgb[:] = hexc("#14121c")
    for i, (tr, hue) in enumerate(sets):
        sc.blit(build(tr, hue, "idle"), i * W, 0)
        sc.blit(build(tr, hue, "attack"), i * W, H)
    sc.image(4).save(out("test_bugs34.png"))
    sq = Scene(2 * QW, QH); sq.rgb[:] = hexc("#14121c")
    sq.blit(queen(0.02, "idle"), 0, 0); sq.blit(queen(0.02, "attack"), QW, 0)
    sq.image(4).save(out("test_queen34.png"))
