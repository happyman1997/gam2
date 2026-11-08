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
M_EYE = Mat(ramp("#3a0604", "#7a0c08", "#c41e10", "#ff5a2a", "#ffc0a0"), emissive=hexc("#ff3a1a"), glow_r=3, glow_k=0.35)
M_FANG = Mat(ramp("#120c0a", "#2e241c", "#6a5a46", "#b4a688", "#ece2c8"))
M_ICHOR = Mat(ramp("#1a2a06", "#3a5a0e", "#6a9a1a", "#a8d040", "#e8ff9a"), emissive=hexc("#9ae030"), glow_r=4, glow_k=0.4)
M_SHEEN = Mat(ramp("#2a2236", "#4a3e5e", "#6e6488", "#9a92b4", "#cfc8e6"))
M_DARKEYE = Mat(ramp("#08060a", "#141018", "#221c2a", "#3a3046", "#8a7aa0"))
M_WING = Mat(ramp("#1a1620", "#2c2634", "#463e4e", "#6a6070", "#9a90a0"), dither=True)
M_WING_NEAR = Mat(ramp("#221c28", "#3a3242", "#5a5064", "#86798c", "#b8aabc"))
M_VEIN = Mat(ramp("#1c1830", "#2c2848", "#403c64", "#56527e", "#6e6a98"))
M_ACID = Mat(GLOWG, emissive=hexc("#8af04a"), glow_r=9, glow_k=0.55)
M_ACID_BELLY = Mat(ramp("#0a1204", "#18280a", "#2e4a12", "#527422", "#90ae40"), emissive=hexc("#6a9a20"), glow_r=10, glow_k=0.22)
M_ACID_SPIT = Mat(GLOWG, emissive=hexc("#a8ff60"), glow_r=12, glow_k=0.8)
M_LANTERN = Mat(ramp("#4a4410", "#8a7a18", "#d0b830", "#f4e870", "#fffcd0"), emissive=hexc("#f0e060"), glow_r=15, glow_k=0.75)
M_EGG = Mat(ramp("#2a3a20", "#4a6a2e", "#76a040", "#a8d060", "#e0f6a0"), emissive=hexc("#80d040"), glow_r=0, glow_k=0)
M_MEMBRANE = Mat(ramp("#12060e", "#2a0e1c", "#461828", "#6a2838", "#9a4a56"))   # swollen veined flesh
AMBER = ramp("#140a04", "#3a2008", "#74420c", "#b4741a", "#e2b048")      # dirty warning yellow
ELYTRA = ramp("#0a0408", "#24080e", "#4a1016", "#7e2220", "#c0603a")     # dried blood
CRIMSON = ramp("#14040a", "#3a0a14", "#6a1420", "#a02a2e", "#d65a4a")


# every form keeps its own colour key so the forms read apart at a glance; all stay dark and oily
FORM_CHITIN = {
    None: ["#07050a", "#180e1c", "#30182c", "#523048", "#9a84a2"],        # ant: violet-black
    "stinger": ["#080404", "#1e0a08", "#3a1410", "#5e2618", "#a8603e"],   # scorpion: rust-black
    "jumper": ["#060804", "#151b0c", "#283216", "#424e22", "#808e4a"],    # grasshopper: rotten olive
    "scythes": ["#0a0c08", "#20281c", "#3a4630", "#5e6c52", "#a4b294"],   # mantis: pale sickly green
    "firefly": ["#080604", "#1c120a", "#322010", "#50361a", "#927040"],   # firefly: dark amber
}


def chitin(hue_shift=0.0, form=None):
    """Dark oily chitin with a cold sheen on top; the form sets the colour key, hue shifts it for inheritance."""
    import colorsys
    base = FORM_CHITIN.get(form, FORM_CHITIN[None])
    out = []
    for c in base:
        r, g, b = (hexc(c) / 255).tolist()
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb((h + hue_shift) % 1.0, l, s * 0.85)
        out.append(np.array([r * 255, g * 255, b * 255], dtype=np.float32))
    return out

TRAITS = ("wings", "stinger", "acid", "horn", "carapace", "jumper", "scythes", "firefly")
CHIMERAS = ("iron", "boil", "hand", "face", "bones", "quills", "snout", "slime", "worm")
CHIMERA_NAMES = dict(iron="Железный панцирь", boil="Кипящая кровь", hand="Человеческая рука", face="Человеческое лицо",
                     bones="Чужие кости", quills="Иглы", snout="Волчий нюх", slime="Слизистая кожа", worm="Червь внутри")

M_IRONV = Mat(IRON)
M_HOT = Mat(ramp("#3a0806", "#7a160c", "#c03a14", "#f07a2a", "#ffd080"), emissive=hexc("#ff6a20"), glow_r=7, glow_k=0.55)
M_STEAM = Mat(ramp("#3a3a44", "#55555f", "#74747e", "#9a9aa4", "#c4c4cc"))
M_STEAM.smoke = True
M_SKIN = Mat(ramp("#3a2216", "#6a4028", "#a06a44", "#cc9a6a", "#ecc8a0"))
M_FUR = Mat(ramp("#1a1410", "#352a20", "#544434", "#76624e", "#9c866e"))
M_SLIME = Mat(ramp("#0c2a2a", "#145a50", "#2a9a80", "#6ad8b8", "#d0fff0"), emissive=hexc("#60e0c0"), glow_r=4, glow_k=0.25)
M_SLIME_FILM = Mat(ramp("#0e2a2c", "#1a4a48", "#2a6e66", "#4aa894", "#9ae0cc"), dither=True)
M_WORM = Mat(ramp("#3a1418", "#6a2a30", "#a04a50", "#d07a78", "#f4b0a8"))
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
            # a spine at the knee and a hooked claw at the foot
            m.limb([knee, knee + np.array((-0.9, 1.6, 0.5 * side))], 1, M_FANG, band=2)
            m.limb([foot, foot + np.array((0.9, -0.2, 0.3 * side))], 1, M_FANG, band=2)


def antennae(m, mc, a0, back=False, long=1.0):
    long *= 1.3
    for z in (0.5, -0.5):
        p0 = a0 + np.array((0, 0, z))
        if back:
            pts = [p0, p0 + (-1.0, 3.0 * long, z * 1.2), p0 + (-7.0 * long, 5.5 * long, z * 3.0)]
        else:
            pts = [p0, p0 + (0.2, 3.0 * long, z * 0.6), p0 + (3.2 * long, 3.6 * long, z * 2.4)]
        m.limb(pts, 1, mc, band=3 if z > 0 else 1)


def mandibles(m, mat, hc, hs, jaw):
    """Big hooked fangs with teeth on the inner edge."""
    for z in (1.0, -1.0):
        base = hc + (1.5 * hs, -0.9 * hs, z * 0.6 * hs)
        L = 3.2 * hs
        mid = base + np.array((np.cos(jaw) * L * 0.6, -0.6, np.sign(z) * np.sin(jaw) * L * 0.55))
        tip = mid + np.array((L * 0.45, -0.2, -np.sign(z) * L * 0.28))
        m.cyl(base, mid, 0.75 * hs, M_FANG, r1=0.5 * hs, seg=5)
        m.cyl(mid, tip, 0.5 * hs, M_FANG, r1=0.08, seg=4)
        for t in (0.35, 0.7):
            p = base + (mid - base) * t
            spike(m, p, p + np.array((0.3, -0.5, -np.sign(z) * 0.8)) * hs, 0.25 * hs, M_FANG)


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
    for z in (0.7, -0.7):                                    # propodeal spines, as real ants have
        spike(m, (-1.4, y0 + 1.6, z), (-3.4, y0 + 4.6, z * 1.6), 0.55, mc)
    tipp = gc + (-5.2 * gs, -1.4, 0)
    spike(m, tipp + (0.8, 0.4, 0), tipp + (-2.6, -1.6, 0), 1.0, M_FANG)
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
    m.ell(gc, (6.8 * gs, 2.5 * gs, 2.5 * gs), stripe, R)
    rings(m, gc, R, 6.8 * gs, 2.5 * gs, mc, n=4)
    hc = np.array((4.5, y0 + 1.6, 0))
    m.ell(hc, (2.0 * hs, 2.1 * hs, 2.3 * hs), mc)
    for z in (1.4, -1.4):
        m.ell(hc + (0.5, 0.6, z * hs), (1.1, 1.4, 0.8), M_DARKEYE)
    mandibles(m, Mat(AMBER), hc, hs * 0.8, 0.3 if pose == "idle" else 0.7)
    antennae(m, mc, hc + (0.6, 1.6 * hs, 0), long=1.2)
    tip = gc + R @ np.array((-6.8 * gs, 0, 0))
    m.cyl(tip + R @ np.array((0.8, 0, 0)), tip + R @ np.array((-3.4, -0.4, 0)), 0.9, M_FANG, r1=0.08, seg=5)
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
        b = a + (4.0, 1.0, np.sign(z) * 1.8)
        m.cyl(a, b, 0.8, mc, seg=5)
        m.ell(b + (1.6, 0.3, 0), (2.4, 1.4, 1.3), M_BONE)
        spike(m, b + (3.0, 0.9, 0), b + (5.6, 1.0, -np.sign(z) * 0.6), 0.6, M_FANG)
        spike(m, b + (3.0, -0.1, 0), b + (5.0, -0.6, -np.sign(z) * 0.4), 0.45, M_FANG)
    pts = [(-5.5, y0 + 1.8), (-8.4, y0 + 4.4), (-10.0, y0 + 8.0), (-9.4, y0 + 11.6), (-6.8, y0 + 13.8), (-3.6, y0 + 14.4)]
    tm = Model()
    for i, (x, y) in enumerate(pts):
        r = 2.0 - i * 0.16
        tm.ell((x, y, 0), (r, r, r), tail)
    bulb = np.array((-2.0, y0 + 13.6, 0))
    tm.ell(bulb, (1.9, 1.5, 1.5), Mat(CRIMSON))
    hook = bulb + np.array((2.2, -1.0, 0))
    tm.cyl(bulb + (0.8, -0.2, 0), hook, 0.9, M_FANG, r1=0.5, seg=5)
    tm.cyl(hook, hook + np.array((0.8, -2.6, 0)), 0.5, M_FANG, r1=0.06, seg=4)
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
    for z in (1.4, -1.4):                                            # pointed tips of the wing cases
        spike(m, (-9.0 * gs, y0 + 2.4, z), (-12.6 * gs, y0 + 0.6, z * 1.2), 1.0, ely)
    hc = np.array((5.4, y0 + 1.2, 0))
    m.ell(hc, (1.6 * hs, 1.5 * hs, 1.9 * hs), mc)
    for z in (1.2, -1.2):
        m.ell(hc + (0.7, 0.4, z * hs), (0.4, 0.4, 0.4), M_EYE)
    # rhinoceros horn, curving back, plus a short horn on the pronotum
    hr = Model()
    hr.cyl(hc + (0.8, 0.8, 0), hc + (4.2, 5.4, 0), 1.7 * hs, M_BONE, r1=1.0 * hs, seg=6)
    hr.cyl(hc + (4.2, 5.4, 0), hc + (3.2, 9.4, 0), 1.0 * hs, M_BONE, r1=0.15, seg=6)
    hr.cyl((3.4, y0 + 4.2, 0), (7.0, y0 + 7.0, 0), 1.0, M_BONE, r1=0.15, seg=5)
    for z in (1.6, -1.6):
        spike(hr, (2.6, y0 + 3.6, z), (3.6, y0 + 6.2, z * 1.5), 0.6, M_BONE)
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
    plate = Mat(chitin_shift(mc, -0.18, sat=0.55, light=1.35))   # slate plates, a shade lighter
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
        spike(m, (-12.6, y0 + 0.6, z), (-17.0, y0 + 0.4, z * 1.8), 0.6, plate)
    for (x, y) in back:     # a serrated back
        spike(m, (x, y - 0.3, 0), (x - 1.4, y + 1.8, 0), 0.7, plate)
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
    antennae(m, mc, hc + (0.6, 2.4 * hs, 0), back=True, long=1.8)
    leg_pairs(m, mc, y0, ((0.4, 0.8), (2.2, 2.4)), 1.0, 0.85, 0, pose)
    for side in (1, -1):    # the huge hind legs are the body plan here
        hip = np.array((-1.6, y0 - 0.4, 1.6 * side))
        if pose == "idle":
            knee, foot = np.array((-7.6, y0 + 11.0, 3.0 * side)), np.array((-11.6, 0.2, 3.8 * side))
        else:
            knee, foot = np.array((-7.5, y0 - 1.0, 2.8 * side)), np.array((-12.5, y0 - 5.5, 3.4 * side))
        m.cyl(hip, knee, 2.3, mc, r1=1.1, seg=6)
        m.ell(knee, (1.1, 1.1, 1.1), M_BONE)
        spike(m, knee, knee + np.array((-1.0, 2.4, 0)), 0.6, M_FANG)
        m.cyl(knee, foot, 0.6, mc, r1=0.4, seg=5)
        for f in (0.3, 0.55, 0.8):                     # spines along the shin
            p = knee + (foot - knee) * f
            spike(m, p, p + np.array((-1.0, 0.5, 0.3 * side)), 0.22, M_FANG)
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
    neck_top = np.array((3.4, y0 + 10.8, 0))
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
            elbow, tip = base + (3.2, 2.6, 0.6 * side), base + (4.4, -5.6, 0.8 * side)
        else:
            elbow, tip = base + (4.2, 3.6, 0.6 * side), base + (11.0, 0.8, 0.8 * side)
        m.cyl(base, elbow, 1.0, jade, seg=5)
        m.cyl(elbow, tip, 1.3, M_BONE, r1=0.12, seg=4)
        for f in (0.25, 0.45, 0.65, 0.82):
            p = elbow + (tip - elbow) * f
            spike(m, p, p + np.array((-1.0, 0.4, 0)), 0.3, M_FANG)
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
    antennae(m, mc, hc + (0.6, 0.8, 0), long=2.0)
    m.ell(shield + (1.6, 0.4, 0), (2.4, 1.0, 3.0), mc, rot_z(-0.3))      # a hood over the head
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


def add_chimera(m, mc, a, kind, pose):
    """Foreign traits grown from eaten enemies — only living parts."""
    hc, hs, gc, gr, y0 = a["hc"], a["hs"], a["gc"], a["gr"], a["y0"]
    if kind == "iron":                       # iron veins in the chitin, like the scaly-foot snail
        for t in (-0.55, 0.0, 0.55):
            x = gc[0] + t * gr * 1.2
            r = gr * np.sqrt(max(0.15, 1 - t * t * 0.7)) * 1.03
            m.cyl((x - 0.6, gc[1], 0), (x + 0.6, gc[1], 0), r, M_IRONV, seg=12)
        for (x, y) in a["back"][-2:]:
            m.box((x, y - 0.2, 0), (2.2, 0.8, 2.6), M_IRONV)
    elif kind == "boil":                     # boiling blood, like the bombardier beetle
        for d in ((0.6, 0.3, 0.8), (-1.4, -0.4, 0.7), (0.2, -1.0, 0.75)):
            m.ell(gc + np.array((d[0] * gr * 0.5, d[1] * gr * 0.5, d[2] * gr)), (gr * 0.35, gr * 0.22, 0.4), M_HOT)
        for i, d in enumerate(((-0.5, 1.3, 0), (0.6, 2.4, 0.4), (-1.2, 3.4, -0.3))):
            m.ell(gc + np.array((d[0] * gr, gr + d[1], d[2])), (1.1 + 0.3 * i, 0.9 + 0.25 * i, 1.0 + 0.3 * i), M_STEAM)
    elif kind == "hand":                     # a human arm grows out of the belly
        s0 = gc + np.array((gr * 0.3, gr * 0.1, gr * 0.75))
        up = 0.0 if pose == "idle" else 2.5
        elbow = s0 + np.array((-1.0, 4.2 + up, 2.2))
        hand = elbow + np.array((4.2, 1.6 + up, 0.6))
        m.cyl(s0, elbow, 1.3, M_SKIN, r1=1.05, seg=6)
        m.ell(elbow, (1.1, 1.1, 1.1), M_SKIN)
        m.cyl(elbow, hand, 1.0, M_SKIN, r1=0.85, seg=6)
        m.ell(hand, (1.4, 1.0, 1.2), M_SKIN)
        for k in range(4):
            m.cyl(hand + (0.7, 0.2, -0.75 + 0.5 * k), hand + (2.3, 0.9, -0.9 + 0.6 * k), 0.32, M_SKIN, seg=4)
        m.cyl(hand + (0.0, 0.6, 1.0), hand + (0.8, 1.6, 1.7), 0.34, M_SKIN, seg=4)
    elif kind == "face":                     # a human face on the belly
        fc = gc + np.array((0.0, 0.3, gr * 0.78))
        m.ell(fc, (gr * 0.72, gr * 0.85, 1.4), M_SKIN)
        for dx in (-0.42, 0.42):
            m.ell(fc + np.array((dx * gr * 0.8, gr * 0.25, 1.0)), (0.75, 0.5, 0.4), M_DARKEYE)
            m.box(fc + np.array((dx * gr * 0.8, gr * 0.5, 1.1)), (1.5, 0.35, 0.3), M_DARKEYE)
        m.ell(fc + np.array((0, -gr * 0.02, 1.3)), (0.45, 0.6, 0.4), M_SKIN)
        m.ell(fc + np.array((0, -gr * 0.42, 1.0)), (gr * 0.32, 0.32, 0.35), M_DARKEYE)
    elif kind == "bones":                    # foreign bones stick out of the chitin
        for t in (-0.6, -0.2, 0.2):
            x = gc[0] + t * gr
            for z in (1, -1):
                m.cyl((x, gc[1] + gr * 0.5, z * gr * 0.5), (x - 0.6, gc[1] - gr * 0.2, z * gr * 1.15), 0.45, M_BONE, r1=0.3, seg=5)
        for (x, y) in a["back"]:
            spike(m, (x, y - 0.4, 0), (x - 1.6, y + 3.6, 0), 0.7)
    elif kind == "quills":                   # a back bristling with quills
        pts = a["back"] + [(gc[0] + gr * dx, gc[1] + gr * 0.8) for dx in (-0.6, -0.1, 0.4)]
        for i, (x, y) in enumerate(pts):
            for z in (-0.8, 0.0, 0.8):
                L = 5.5 + (i % 3)
                m.cyl((x, y - 0.3, z), (x - L * 0.75, y + L * 0.65, z * 1.6), 0.32, M_BONE, r1=0.06, seg=4)
    elif kind == "snout":                    # a wolf's muzzle and ears
        tip = hc + np.array((3.6 * hs, -0.5 * hs, 0))
        m.cyl(hc + (0.8 * hs, 0, 0), tip, 1.3 * hs, M_FUR, r1=0.75 * hs, seg=8)
        m.ell(tip + (0.2, 0.15, 0), (0.55 * hs, 0.45 * hs, 0.5 * hs), M_DARKEYE)
        for z in (0.9, -0.9):
            m.cyl(hc + (-0.4 * hs, 1.4 * hs, z * hs), hc + (-0.9 * hs, 3.0 * hs, z * hs * 1.1), 0.7 * hs, M_FUR, r1=0.1, seg=4)
    elif kind == "slime":                    # wet glistening skin, dripping
        m.ell(gc + np.array((0, gr * 0.05, 0)), (gr * 1.36, gr * 1.04, gr * 1.04), M_SLIME_FILM, rot_z(0.25))
        for d in ((0.3, 0.7, 0.75), (-0.6, 0.5, 0.85), (0.0, -0.2, 0.95), (0.7, -0.1, 0.8)):
            m.ell(gc + np.array((d[0] * gr, d[1] * gr * 0.6, d[2] * gr)), (1.0, 0.7, 0.5), M_SLIME)
        for x in (gc[0] - gr * 0.4, gc[0] + gr * 0.3, a["hc"][0] - 3.0):
            m.ell((x, max(1.2, y0 - 3.4), 0.8), (0.7, 1.6, 0.7), M_SLIME)
        m.ell(hc + (0.4 * hs, 1.2 * hs, 0.8), (0.9, 0.6, 0.6), M_SLIME)
    elif kind == "worm":                     # a worm squirms out of the belly
        base = gc + np.array((0.3 * gr, gr * 0.7, 0.3 * gr))
        wig = 0.0 if pose == "idle" else 0.8
        for i in range(7):
            p = base + np.array((1.0 * i, 1.3 * i - 0.14 * i * i, np.sin(i * 1.2 + wig) * 1.1))
            m.ell(p, (1.25 - 0.07 * i, 1.1 - 0.06 * i, 1.1 - 0.06 * i), M_WORM)
        m.ell(base + np.array((7.0, 2.9, np.sin(8.4 + wig) * 1.1)), (0.45, 0.4, 0.4), M_DARKEYE)


def menace(m, mc, a, pose):
    """What makes every bug frightening: clustered red eyes, bristles, an oily glint, dripping ichor."""
    hc, hs, gc, gr = a["hc"], a["hs"], a["gc"], a["gr"]
    for dx, dy, z in ((-0.2, 1.0, 1.25),):
        m.ell(hc + np.array((dx * hs, dy * hs, z * hs)), (0.32, 0.32, 0.32), M_EYE)
    for (x, y) in a["back"][:4]:
        m.limb([np.array((x, y - 0.2, 0.4)), np.array((x - 0.8, y + 1.8, 0.9))], 1, mc, band=1)
    m.ell(gc + np.array((gr * 0.25, gr * 0.78, gr * 0.3)), (gr * 0.32, gr * 0.07, gr * 0.16), M_SHEEN, rot_z(0.3))
    if pose == "attack":
        mouth = hc + np.array((2.2 * hs, -1.4 * hs, 0))
        m.ell(mouth, (0.45, 0.6, 0.45), M_ICHOR)
        m.ell(mouth + (0.2, -1.6, 0), (0.3, 0.45, 0.3), M_ICHOR)


def body(hue=0.0, traits=(), pose="idle", soldier=False, genes=None, chimera=None):
    """traits[0] decides the body plan; "ant" as the first trait keeps the ant body for detail traits."""
    traits = tuple(t for t in traits if t != "giant")
    g = genes or genes_for(int(abs(hue) * 1000) + 7 * len(traits))
    m = Model()
    primary = traits[0] if traits and traits[0] != "ant" else None
    mc = Mat(chitin(hue, primary))
    traits = tuple(t for t in traits if t != "ant")
    a = PLAN_FN[primary](m, mc, g, pose, soldier)
    menace(m, mc, a, pose)
    add_parts(m, mc, a, traits, pose)
    if chimera:
        add_chimera(m, mc, a, chimera, pose)
    hover = 6.0 if ("wings" in traits) else 0.0
    if primary == "wings":
        hover = 5.0
    if pose == "idle" and not hover:
        m = pivot(m, rot_z(-0.07), (0, 4.0, 0))
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


def rim_light(spr, col="#c0b0d0", k=0.65):
    """A thin cold rim just under the top outline: dark bodies stay readable on dark ground."""
    a = spr.a
    above = np.zeros_like(a)
    above[1:] = a[:-1]
    top = a & ~above                       # the top outline pixels
    rim = np.zeros_like(a)
    rim[1:] = top[:-1]
    rim &= a & ~top
    left = np.zeros_like(a)
    left[:, 1:] = a[:, :-1]
    side = np.zeros_like(a)
    side[:, 1:] = (a & ~left)[:, :-1]
    side &= a & ~(a & ~left) & ~rim
    c = hexc(col)
    spr.rgb[rim] = spr.rgb[rim] * (1 - k) + c * k
    spr.rgb[side] = spr.rgb[side] * (1 - k * 0.5) + c * k * 0.5
    return spr


def build(traits=(), hue=0.0, pose="idle", soldier=False, k=1.0, genes=None, chimera=None):
    """k multiplies the in-game scale (use >1 for close-up sheets)."""
    s = scale_for(size_of(traits, soldier)) * k
    w, h, ox, oy = int(64 * s), int(60 * s), int(30 * s), int(52 * s)
    spr = rim_light(render(body(hue, traits, pose, soldier, genes, chimera).scaled(s), w, h, ox, oy, **STYLE1))
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
        m.ell(hc + (0.6, 1.5, z * 0.8), (0.45, 0.45, 0.45), M_EYE)
        m.ell(hc + (1.6, 0.0, z * 1.1), (0.4, 0.4, 0.4), M_EYE)
        base = hc + (2.1, -1.0, z * 0.5)
        mid = base + np.array((np.cos(jaw) * 2.6, -0.8, np.sign(z) * np.sin(jaw) * 2.2))
        tip = mid + np.array((1.6, -0.3, -np.sign(z) * 1.2))
        m.cyl(base, mid, 0.85, M_FANG, r1=0.55, seg=5)
        m.cyl(mid, tip, 0.55, M_FANG, r1=0.08, seg=4)
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
    spr = rim_light(render(m.scaled(s), w, h, ox, oy, **STYLE1))
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

