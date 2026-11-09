"""The Architect's building modules on the humanoid golems: how a golem carries a module (marching) and what
it turns into when it deploys. A deployed golem does not vanish into the building: it plants itself and
becomes its core — the Guard's shield is the middle of the wall, the Gun stands on top of its tower.

Levels of a building show on the sprite: I — logs and junk, II — stone and bronze, III — iron, spikes,
runes. Every form goes through the clipping check like the golems themselves.

    python3 tools/sprites/buildings.py            -> out/buildings_check.png (every module, both views, all levels)
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_STEEL, M_RUST, M_HOLE, M_BRONZE, emissive, spike, tbox, STYLE1
from golem7 import M_PUFF
import golems_h as GH
import humanoid as HM
from golems_h import arr, unit, lerp, rivets, sparks, puffs, Parts
from clipcheck import report, cells, STEP

LOG = Mat(ramp("#1e1208", "#3a2412", "#5a3a1e", "#7c562e", "#a07844"))
LOG_END = Mat(ramp("#2a1a0c", "#4a3018", "#6e4a26", "#94683a", "#bc8e56"))
ROPE = Mat(ramp("#2a2014", "#4a3a22", "#6e5a38", "#968050", "#bea870"))
STONE = Mat(ramp("#22202a", "#3e3a46", "#5e5a68", "#86828e", "#b2aeb8"))
MORTAR = Mat(ramp("#141218", "#201e26", "#2c2a34", "#383640", "#46444e"))
PLATE = Mat(ramp("#121418", "#22262e", "#363c46", "#525a66", "#7a8290"))
RUNE = Mat(EMBER, emissive=hexc("#ff8a30"), glow_r=4, glow_k=0.35)
TAR = Mat(ramp("#0a0506", "#1e0e0a", "#3a1e10", "#62361a", "#94602c"))
TAR_HOT = Mat(ramp("#3a1206", "#6a2a0c", "#a04a14", "#d07a24", "#f0b050"), emissive=hexc("#e07020"), glow_r=5, glow_k=0.35)
EARTH = Mat(ramp("#120e0c", "#221a16", "#342822", "#4a3a30", "#62503f"), dither=True)


# ---------------------------------------------------------------- what a level is made of
def tier_mats(t):
    """main: the bulk, trim: bands and frames, cap: the top course."""
    if t == 1:
        return dict(main=LOG, trim=ROPE, cap=LOG_END, frame=M_RUST)
    if t == 2:
        return dict(main=STONE, trim=M_BRONZE, cap=STONE, frame=M_BRONZE)
    return dict(main=PLATE, trim=M_DIRON, cap=M_IRON, frame=M_DIRON)


def wall_run(g, x, z0, z1, y0, h, t, depth=2.6, face=1):
    """A straight stretch of wall along z, its face looking +x (face=1). I: logs laid on their side with posts;
    II: courses of offset stone with a bronze coping band; III: riveted iron plates, spikes and a rune line."""
    M = tier_mats(t)
    L = z1 - z0
    zc = (z0 + z1) / 2
    if t == 1:
        n = max(1, int(h // 2.3))
        for i in range(n):
            y = y0 + 1.15 + i * 2.3
            g.cyl((x, y, z0), (x, y, z1), 1.15, LOG, seg=7)
            g.cyl((x, y, z0 - 0.05), (x, y, z0 + 0.15), 1.0, LOG_END, seg=7)
        top = y0 + n * 2.3
        for z in np.linspace(z0 + 1.0, z1 - 1.0, max(2, int(L // 6) + 1)):
            g.cyl((x + face * 1.5, y0, z), (x + face * 1.5, top + 1.0, z), 0.55, LOG_END, seg=6)          # posts
            g.cyl((x + face * 1.5, top - 0.6, z - 0.5), (x + face * 1.5, top - 0.6, z + 0.5), 0.75, ROPE, seg=6)
            spike(g, (x + face * 1.5, top + 1.0, z), (x + face * 1.5, top + 2.4, z), 0.55, LOG_END)
    elif t == 2:
        rows = max(1, int(h // 2.6))
        g.box((x - face * 0.1, y0 + rows * 1.3, zc), (depth - 0.4, rows * 2.6, L - 0.2), MORTAR)
        for r in range(rows):
            off = 0.0 if r % 2 == 0 else 1.6
            z = z0 + off
            while z < z1 - 0.4:
                w = min(3.2, z1 - z)
                if w > 0.6:
                    tbox(g, (x, y0 + 1.3 + r * 2.6, z + w / 2), (depth, w - 0.25), (depth - 0.2, w - 0.35), 2.35, STONE)
                z += 3.2
        top = y0 + rows * 2.6
        g.box((x, top + 0.35, zc), (depth + 0.4, 0.7, L), M_BRONZE)
        for z in np.arange(z0 + 1.2, z1 - 0.6, 3.2):
            g.box((x, top + 1.5, z), (depth, 1.6, 1.4), STONE)                                         # merlons
    else:
        g.box((x, y0 + h / 2, zc), (depth, h, L), PLATE)
        for z in np.arange(z0 + 2.0, z1 - 1.0, 4.0):
            g.box((x + face * (depth / 2 + 0.15), y0 + h / 2, z), (0.3, h - 0.8, 0.6), M_DIRON)
            rivets(g, [(x + face * (depth / 2 + 0.3), y0 + yy, z) for yy in (1.2, h * 0.5, h - 1.2)], r=0.3)
            spike(g, (x + face * depth / 2, y0 + h * 0.62, z + 2.0), (x + face * (depth / 2 + 3.2), y0 + h * 0.62, z + 2.0), 0.55, M_IRON)
        g.box((x + face * (depth / 2 + 0.1), y0 + h * 0.3, zc), (0.25, 0.6, L - 1.6), RUNE)
        for z in np.arange(z0 + 1.0, z1, 2.6):
            tbox(g, (x, y0 + h + 0.7, z), (depth, 1.4), (depth * 0.5, 0.6), 1.4, M_IRON)              # iron teeth


def drum(g, c, R, y0, h, t, n=None):
    """A round tower body. I: a palisade of pointed logs bound with rope; II: offset stone courses;
    III: iron plates on a frame, rivets, spikes and a rune ring."""
    c = arr(c)
    if t == 1:
        n = n or int(2 * np.pi * R / 1.9)
        for i in range(n):
            a = 2 * np.pi * i / n
            p = c + (np.cos(a) * R, 0, np.sin(a) * R)
            hh = h + (0.6 if i % 2 else 0.0)
            g.cyl(p + (0, y0, 0), p + (0, y0 + hh, 0), 0.98, LOG, seg=6)
            spike(g, p + (0, y0 + hh, 0), p + (0, y0 + hh + 1.4, 0), 0.9, LOG_END)
        for y in (y0 + h * 0.3, y0 + h * 0.75):
            g.cyl(c + (0, y, 0), c + (0, y + 0.5, 0), R + 1.0, ROPE, seg=24)
        g.cyl(c + (0, y0, 0), c + (0, y0 + h, 0), R - 0.6, M_DIRON, seg=20)
    elif t == 2:
        g.cyl(c + (0, y0, 0), c + (0, y0 + h, 0), R - 0.4, MORTAR, seg=24)
        rows = int(h // 2.4)
        for r in range(rows):
            m = int(2 * np.pi * R / 3.0)
            for i in range(m):
                a = 2 * np.pi * (i + 0.5 * (r % 2)) / m
                p = c + (np.cos(a) * R, y0 + 1.2 + r * 2.4, np.sin(a) * R)
                tbox(g, p, (1.6, 2.6), (1.5, 2.5), 2.2, STONE, rot_y(-a))
        g.cyl(c + (0, y0 + rows * 2.4, 0), c + (0, y0 + rows * 2.4 + 0.7, 0), R + 0.5, M_BRONZE, seg=24)
    else:
        g.cyl(c + (0, y0, 0), c + (0, y0 + h, 0), R, PLATE, seg=16)
        for i in range(8):
            a = 2 * np.pi * (i + 0.5) / 8
            p = c + (np.cos(a) * (R + 0.15), 0, np.sin(a) * (R + 0.15))
            g.box(p + (0, y0 + h / 2, 0), (0.6, h - 0.6, 0.8), M_DIRON, rot_y(-a))
            spike(g, p + (0, y0 + h * 0.55, 0), p + (np.cos(a) * 3.0, y0 + h * 0.55, np.sin(a) * 3.0), 0.6, M_IRON)
            rivets(g, [p + (np.cos(a) * 0.35, y0 + yy, np.sin(a) * 0.35) for yy in (1.0, h - 1.0)], r=0.3)
        g.cyl(c + (0, y0 + h * 0.3, 0), c + (0, y0 + h * 0.3 + 0.5, 0), R + 0.12, RUNE, seg=16)


def masonry(g, c, sx, sz, h, mat=None, course=2.4):
    """A block of laid stone: courses of two blocks, turned every other course, mortar showing between them."""
    c = arr(c)
    mat = mat or STONE
    g.box(c + (0, h / 2, 0), (sx - 0.3, h, sz - 0.3), MORTAR)
    n = max(1, int(round(h / course)))
    ch = h / n
    for r in range(n):
        y = c[1] + ch * (r + 0.5)
        if r % 2:
            for dz in (-sz / 4, sz / 4):
                tbox(g, (c[0], y, c[2] + dz), (sx, sz / 2 - 0.25), (sx - 0.15, sz / 2 - 0.35), ch - 0.25, mat)
        else:
            for dx in (-sx / 4, sx / 4):
                tbox(g, (c[0] + dx, y, c[2]), (sx / 2 - 0.25, sz), (sx / 2 - 0.35, sz - 0.15), ch - 0.25, mat)


# ---------------------------------------------------------------- the frames
def golem(name, A, fx=True):
    """Parts of a frame in pose A and the clipping pairs it allows."""
    if name == "Страж":
        G, info = HM.pose_parts(A, fx=False)
        if fx and A.get("fx"):
            HM.impact(G["fx"], A, A.get("ft", 0.0), info)
        return G, info, list(HM.ALLOWED)
    S = GH.BY_NAME[name]
    G, info = GH.creature_parts(S, A, fx=fx)
    return G, info, GH.BASE_ALLOWED + S.get("allow", [])


def pose_of(name, pose):
    if name == "Страж":
        if pose == "idle":
            return None
        return dict(HM.ATTACKS[HM.ATTACK if pose == "attack" else pose])
    return dict(GH.BY_NAME[name]["poses"][pose])


def lift(G, h):
    for k in list(G):
        G[k] = G[k].transformed(I3, (0, h, 0))


# ---------------------------------------------------------------- marching: the module packed on the back
def back_line(G, y0, y1, z0, z1, keys=None):
    """The rearmost point of the golem (smallest x) within a height and width band."""
    xs = []
    for k, m in G.items():
        if k == "fx" or (keys and k not in keys):
            continue
        for c in cells(m):
            x, y, z = (np.array(c) * STEP)
            if y0 <= y <= y1 and z0 <= z <= z1:
                xs.append(x)
    return min(xs) if xs else 0.0


def pack(G, kind, t, y0, y1, w, x_back):
    """A carrying frame on the golem's back with the folded module in it. x_back: where the back is."""
    M = tier_mats(t)
    g = G["pack"]
    d = 4.4 if kind != "panels" else 3.2
    x1 = x_back - 0.9                       # the frame's front, just behind the back
    xc = x1 - d / 2
    yc, H = (y0 + y1) / 2, y1 - y0
    for z in (-w / 2, w / 2):               # the frame: two uprights, rails top and bottom, straps forward
        g.cyl((x1 - 0.3, y0 - 1.5, z), (x1 - 0.3, y1 + 0.8, z), 0.4, M_DIRON, seg=5)
        g.cyl((x1 - d, y0 - 1.0, z), (x1 - d, y1, z), 0.35, M_DIRON, seg=5)
        g.cyl((x1 - 0.3, y0 - 1.2, z), (x1 - d, y0 - 1.0, z), 0.35, M_DIRON, seg=5)
    g.cyl((x1 - 0.3, y1 + 0.8, -w / 2), (x1 - 0.3, y1 + 0.8, w / 2), 0.4, M_DIRON, seg=5)
    if kind == "panels":                    # wall leaves folded flat: three standing slabs
        for i in range(3):
            x = x1 - 0.7 - i * 0.95
            if t == 1:
                for j in range(int(w // 1.7)):
                    z = -w / 2 + 0.85 + j * 1.7
                    g.cyl((x, y0, z), (x, y1, z), 0.42, LOG, seg=6)
            elif t == 2:
                g.box((x, yc, 0), (0.8, H, w - 0.6), STONE)
                g.box((x, y1 - 0.4, 0), (0.85, 0.5, w - 0.6), M_BRONZE)
            else:
                g.box((x, yc, 0), (0.8, H, w - 0.6), PLATE)
                rivets(g, [(x - 0.45, yc + yy, z) for yy in (-H / 3, H / 3) for z in (-w / 3, w / 3)], r=0.25)
    elif kind == "blocks":                  # stacked courses for a tower
        for r in range(int(H // 2.2)):
            y = y0 + 1.1 + r * 2.2
            for z in np.arange(-w / 2 + 1.3, w / 2 - 0.5, 2.6):
                if t == 1:
                    g.cyl((xc, y, z - 1.1), (xc, y, z + 1.1), 1.0, LOG, seg=6)
                elif t == 2:
                    g.box((xc, y, z + (0.6 if r % 2 else 0) * 0), (d - 0.8, 2.0, 2.4), STONE)
                else:
                    g.box((xc, y, z), (d - 0.8, 2.0, 2.4), PLATE)
        g.cyl((x1 - d - 0.2, y1 - 1.2, -w / 2), (x1 - d - 0.2, y1 - 1.2, w / 2), 0.25, ROPE if t == 1 else M_DIRON, seg=4)
    return xc


# ---------------------------------------------------------------- Бойницы: the Gun on its tower
TOWER_H, TOWER_R = 20.0, 12.4


def tower(t, pose="idle", deployed=True):
    name = "Орудие"
    if not deployed:
        return golem_pack(name, "blocks", t, "blocks")
    A = pose_of(name, "attack" if pose == "attack" else "idle")
    A["ank"] = ((2.0, 3.6, 4.2), (-3.8, 3.6, -4.2))
    G, info, allow = golem(name, A, fx=(pose == "attack"))
    b = G["bld"]
    y0 = -TOWER_H
    b.cyl((0, y0, 0), (0, y0 + 0.9, 0), TOWER_R + 1.6, M_DIRON if t > 1 else LOG, seg=24)          # footing
    drum(b, (0, 0, 0), TOWER_R, y0 + 0.9, TOWER_H - 1.6, t)
    b.cyl((0, -0.7, 0), (0, 0.0, 0), TOWER_R + 0.3, M_DIRON if t > 1 else LOG_END, seg=24)          # the deck
    for a in np.radians(np.arange(-150, 181, 30)):                                                   # merlons, a gap in front
        if abs(a) < 0.35:
            continue
        p = (np.cos(a) * (TOWER_R - 0.2), 1.6, np.sin(a) * (TOWER_R - 0.2))
        if t == 1:
            spike(b, p - arr((0, 1.6, 0)), p + arr((0, 1.4, 0)), 0.8, LOG_END)
        else:
            tbox(b, p, (1.6, 2.4), (1.4, 2.2), 3.2, STONE if t == 2 else PLATE, rot_y(-a))
    for a in (-0.5, 0.5, -1.4, 1.4):                                                                 # embrasures
        p = arr((np.cos(a) * (TOWER_R + 0.9), y0 + TOWER_H * 0.55, np.sin(a) * (TOWER_R + 0.9)))
        b.box(p, (0.5, 2.6, 0.7), M_HOLE, rot_y(-a))
    lift(G, TOWER_H)
    return G, allow


def guard_wall_pose():
    """The Guard down on one knee behind its shield, the shield planted on its spikes, the maul on the shoulder."""
    A = dict(HM.ATTACKS["ram"])
    A.update(lean=-0.05, twist=0.0, t=(0.0, -6.0, 0.0), ankles=((3.0, 3.6, HM.HZ + 1.0), (-7.0, 3.6, -HM.HZ - 0.6)),
             shield=(10.0, -8.0, 6.0), shield_pole=(0.0, -1.0, -0.5), shield_rot=0.0, fx=None)
    return A


def wall(t, pose="idle", deployed=True):
    name = "Страж"
    if not deployed:
        return golem_pack(name, "panels", t, "panels")
    A = guard_wall_pose()
    G, info, allow = golem(name, A, fx=False)
    sc, R = info["sc"], info["R"]
    b = G["bld"]
    half = 6.6
    x = sc[0] + 0.2
    wall_run(b, x, -28.0, sc[2] - half - 0.1, 0.0, 19.0, t, depth=3.0)
    wall_run(b, x, sc[2] + half + 0.1, 28.0, 0.0, 19.0, t, depth=3.0)
    return G, allow + [("shield", "bld")]


# ---------------------------------------------------------------- more packs
def pack_item(G, kind, t, x_back, y0, top):
    """Folded modules that are not panels or blocks: a cauldron, a mast, a jib, a forge, a press.
    Built on the same carrying frame; what sticks up over the shoulders shows what it is."""
    g = G["pack"]
    M = tier_mats(t)
    xc = x_back - 2.8
    w = 7.0
    for z in (-w / 2, w / 2):
        g.cyl((x_back - 0.7, y0 - 1.5, z), (x_back - 0.7, y0 + 9.0, z), 0.4, M_DIRON, seg=5)
    g.box((xc, y0 - 1.0, 0), (4.6, 0.7, w + 0.6), M_DIRON)                                       # the shelf
    if kind == "cauldron":
        pot = Model()
        pot.cyl((0, 0, 0), (0, 5.4, 0), 2.9, M_DIRON, r1=3.6, seg=14)
        pot.cyl((0, 5.4, 0), (0, 6.2, 0), 3.8, M_IRON, seg=14)
        pot.cyl((0, 2.0, 0), (0, 2.8, 0), 3.4, M_BRONZE if t > 1 else ROPE, seg=14)
        pot.ell((0, 6.4, 0), (3.4, 0.5, 3.4), TAR)
        g.extend(pot.transformed(I3, (xc - 1.0, y0 - 0.6, 0)))
        g.ell((xc - 1.6, y0 + 9.0, 0.4), (1.6, 1.3, 1.4), M_PUFF)
    elif kind == "mast":
        from leaders_h import lattice
        h = top - y0
        lattice(g, (xc, y0 - 0.6, 0), (xc, top, 0), 3.0, M_BRONZE if t == 2 else (LOG if t == 1 else M_DIRON),
                up=(1, 0, 0), r=0.35, tri=False)
        g.ell((xc, top + 1.8, 0), (2.0, 2.0, 2.0), GH.COPPER)
        for i in range(3):
            g.cyl((xc, top - 2.0 - i * 0.9, 0), (xc, top - 1.6 - i * 0.9, 0), 1.3, GH.PORC, seg=10)
    elif kind == "jib":
        from leaders_h import lattice
        lattice(g, (xc, y0 - 0.6, 0), (xc - 1.0, top, 0), 2.4, M_BRONZE if t == 2 else (LOG if t == 1 else M_DIRON),
                up=(1, 0, 0), r=0.32)
        g.cyl((xc - 1.0, top, 0), (xc + 1.4, top - 4.0, 0), 0.12, M_DIRON, seg=4)
        g.cyl((xc + 1.4, top - 4.0, 0), (xc + 1.4, top - 5.4, 0), 0.25, M_STEEL, seg=5)           # the hook
    elif kind == "forge":
        g.box((xc, y0 + 1.6, 0), (3.6, 3.4, 5.4), STONE if t == 2 else (LOG if t == 1 else PLATE))   # the folded hearth
        tbox(g, (xc, y0 + 4.6, 0), (3.0, 4.6), (2.0, 3.2), 2.6, M_IRON)                          # the anvil on top
        g.cyl((xc - 0.8, y0 + 3.0, 2.0), (xc - 0.8, top, 2.0), 0.7, M_DIRON, seg=8)                # the chimney pipe
        g.cyl((xc - 0.8, top, 2.0), (xc - 0.8, top + 0.6, 2.0), 1.1, M_DIRON, seg=8)
    elif kind == "press":
        tbox(g, (xc, y0 + 2.4, 0), (3.6, 6.0), (3.6, 6.0), 4.8, M_IRON if t > 1 else LOG)          # the stamp
        for z in (-2.6, 2.6):
            g.cyl((xc + 0.6, y0, z), (xc + 0.6, top, z), 0.55, M[("frame")], seg=6)                 # the guide posts
            HM.ram(g, (xc - 1.2, y0 + 5.0, z * 0.5), (xc - 1.2, top - 2.0, z * 0.5), 0.5)
        g.cyl((xc + 0.6, top, -3.2), (xc + 0.6, top, 3.2), 0.6, M[("frame")], seg=6)


def golem_pack(name, kind, t, pack_kind="item"):
    """A frame at rest with its module packed on its back."""
    if name == "Страж":
        G = HM.guard_parts("idle")
        allow = list(HM.ALLOWED)
        keys = ("boiler", "stacks", "chest", "head", "pelvis", "spine")
        y0, top = (28.0, 56.0) if kind in ("panels", "blocks") else (36.0, 56.0)
    else:
        S = GH.BY_NAME[name]
        G, info, allow = golem(name, pose_of(name, "idle"))
        keys = ("back", "chest", "pelvis", "head", "spine", "robe", "hose")
        y0 = S["hip"] + 6.0
        top = S["sh"][1] + 16.0
        if kind in ("cauldron", "forge", "press"):
            y0 = S["sh"][1] + (4.0 if kind == "cauldron" else -3.0)
    xb = back_line(G, y0 - 2.0, top + 4.0, -4.0, 4.0, keys=keys)
    if pack_kind in ("panels", "blocks"):
        pack(G, pack_kind, t, y0, top, 12.0 if pack_kind == "panels" else 8.0, xb)
    else:
        pack_item(G, kind, t, xb, y0, top)
    return G, allow + [("pack", k) for k in ("back", "boiler", "stacks", "hose", "manip")]


# ---------------------------------------------------------------- Створки: a gate with the Guard as its keeper
def gate(t, pose="idle", deployed=True):
    if not deployed:
        return golem_pack("Страж", "panels", t, "panels")
    G = HM.guard_parts("idle")
    allow = list(HM.ALLOWED)
    b = G["bld"]
    M = tier_mats(t)
    x, zp, H = 21.0, 16.0, 30.0
    for z in (-zp, zp):                                          # the gate towers
        if t == 1:
            for dx in (-1.6, 0.0, 1.6):
                for dz in (-1.6, 0.0, 1.6):
                    b.cyl((x + dx, 0, z + dz), (x + dx, H - abs(dx) - abs(dz) * 0.5, z + dz), 0.85, LOG, seg=6)
            b.cyl((x, H * 0.55, z), (x, H * 0.55 + 0.6, z), 2.9, ROPE, seg=10)
        elif t == 2:
            for r in range(int(H // 2.5)):
                tbox(b, (x, 1.25 + r * 2.5, z), (5.6, 5.6), (5.4, 5.4), 2.3, STONE)
            tbox(b, (x, H + 0.8, z), (6.4, 6.4), (6.4, 6.4), 1.4, M_BRONZE)
        else:
            tbox(b, (x, H / 2, z), (6.0, 6.0), (5.4, 5.4), H, PLATE)
            for zz in (-2.0, 2.0):
                rivets(b, [(x + 3.0, y, z + zz) for y in (3.0, H / 2, H - 3.0)], r=0.35)
            spike(b, (x, H, z), (x, H + 4.0, z), 1.2, M_IRON)
            b.box((x + 2.9, H * 0.6, z), (0.3, 3.0, 0.8), RUNE)
    b.box((x, H - 3.0, 0), (3.4, 2.4, 2 * zp - 5.0), M["main"] if t > 1 else LOG)            # the lintel
    b.box((x + 1.8, H - 3.0, 0), (0.3, 0.8, 2 * zp - 6.0), M["trim"])
    ang = 1.15 if pose == "attack" else 0.0                      # opened for its own side to pass
    for s_ in (-1, 1):
        hinge = arr((x, 0, s_ * (zp - 3.0)))
        R = rot_y(s_ * ang)
        leaf = Model()
        Wd, Hh = zp - 3.2, H - 4.6
        if t == 1:
            for j in range(int(Wd // 1.3)):
                zz = -s_ * (0.65 + j * 1.3)
                leaf.cyl((0, 0.2, zz), (0, Hh, zz), 0.6, LOG, seg=6)
            for y in (3.0, Hh - 3.0):
                leaf.box((0.7, y, -s_ * Wd / 2), (0.4, 1.0, Wd), ROPE)
        else:
            leaf.box((0, Hh / 2, -s_ * Wd / 2), (1.2, Hh, Wd), LOG if t == 2 else PLATE)
            for y in (3.0, Hh / 2, Hh - 3.0):
                leaf.box((0.7, y, -s_ * Wd / 2), (0.3, 1.2, Wd), M["trim"])
            rivets(leaf, [(0.9, y, -s_ * zz) for y in (3.0, Hh / 2, Hh - 3.0) for zz in (2.0, Wd - 2.0)], r=0.3)
            if t == 3:
                leaf.box((0.75, Hh * 0.75, -s_ * Wd / 2), (0.2, 0.5, Wd - 2.0), RUNE)
        b.extend(leaf.transformed(R, hinge))
    return G, allow


# ---------------------------------------------------------------- Пресс: dug in, the stamp raised in a frame
def press(t, pose="idle", deployed=True):
    if not deployed:
        return golem_pack("Страж", "press", t)
    A = guard_wall_pose()
    G, info, allow = golem("Страж", A, fx=False)
    b = G["bld"]
    M = tier_mats(t)
    for (x, z, r) in ((4.0, 7.0, 5.6), (-6.0, -6.0, 5.6), (-1.0, 0.5, 8.0)):                    # dug in: earth heaped round its legs
        G["earth"].ell((x, 0.6, z), (r, 3.6, r * 0.9), EARTH)
    x0, H, zz = 23.0, 36.0, 6.0
    for z in (-zz, zz):                                                                     # two guide posts on a sill
        if t == 1:
            b.cyl((x0, 0, z), (x0, H, z), 1.2, LOG, seg=7)
        elif t == 2:
            masonry(b, (x0, 0, z), 3.0, 3.0, H, course=3.0)
        else:
            tbox(b, (x0, H / 2, z), (2.4, 2.4), (2.0, 2.0), H, PLATE)
            spike(b, (x0, H, z), (x0, H + 3.0, z), 0.9, M_IRON)
    b.box((x0, 0.4, 0), (6.0, 0.8, 2 * zz + 4.0), M["frame"])
    b.box((x0, H + 0.8, 0), (3.2, 1.8, 2 * zz + 3.0), M["main"] if t > 1 else LOG)
    down = pose == "attack"
    y = 1.6 if down else H - 12.0                                                          # the stamp
    tbox(b, (x0, y + 4.0, 0), (5.0, 2 * zz - 3.0), (5.0, 2 * zz - 3.0), 7.0, M_IRON if t > 1 else STONE)
    b.box((x0, y + 0.3, 0), (5.6, 0.6, 2 * zz - 2.4), M_DIRON)
    if t == 3:
        for dz in (-3.0, 0.0, 3.0):
            spike(b, (x0, y + 0.2, dz), (x0, y - 1.6, dz), 0.6, M_IRON)
        b.box((x0 + 2.55, y + 4.0, 0), (0.2, 0.6, 2 * zz - 5.0), RUNE)
    for z in (-zz + 1.6, zz - 1.6):                                                         # two rams from the head beam
        HM.ram(b, (x0, H - 0.2, z * 0.6), (x0, y + 7.6, z * 0.6), 0.75)
    hose = [info["sh"] + arr((-6.0, 2.0, -2.0)), arr((4.0, H + 4.0, 0.0)), arr((x0 - 1.5, H + 1.6, 0.0))]
    for p0, p1 in zip(hose[:-1], hose[1:]):
        G["hose2"].cyl(p0, p1, 0.6, GH.M_HOSE if hasattr(GH, "M_HOSE") else M_DIRON, seg=6)
    if down:
        G["fx"].ell((x0 + 1.0, 1.4, 0.0), (8.0, 1.6, 9.0), Mat(ramp("#3a3230", "#5a504a", "#7e726a", "#a49890", "#c8beb4"), dither=True))
        sparks(G["fx"], arr((x0 + 3.0, 1.0, 0.0)), n=6, spread=5.0, seed=3, big=False)
    return G, allow + [("earth", "leg_n"), ("earth", "leg_f"), ("earth", "leg_n.ram"), ("earth", "leg_f.ram"),
                       ("earth", "shield"), ("hose2", "boiler"), ("hose2", "stacks"), ("hose2", "bld"), ("hose2", "chest"),
                       ("hose2", "head"), ("hose2", "pauldron_f")]


# ---------------------------------------------------------------- Смоляной котёл: the Gorn heats a cauldron and tips it
def pitch(t, pose="idle", deployed=True):
    if not deployed:
        return golem_pack("Горн", "cauldron", t)
    S = GH.GORN
    A = dict(S["poses"]["idle"])
    A.update(lean=-0.12, t=(0.4, -2.6, 0.0), ank=((3.4, 3.6, 6.4), (-5.2, 3.6, -6.4)),
             hand_n=(6.5, -10.5, 3.0), pole_n=(-0.3, 0.0, 1.0), hand_f=(6.0, -9.6, -3.8), pole_f=(-0.4, -0.2, -1.0), fx=None)
    G, info, allow = golem("Горн", A, fx=False)
    b = G["bld"]
    M = tier_mats(t)
    nz, a = info["n"]["nozzle"], info["n"]["a"]
    mouth = nz + a * 2.6                                         # the firing mouth right where the nozzle points
    hx, hz = mouth[0] + 5.2, mouth[2]
    for i, f in enumerate((0.5, 1.3, 2.1)):                      # the Gorn's flame going into the hearth
        G["fx"].ell(nz + a * f, (0.7 + 0.25 * i, 0.7 + 0.25 * i, 0.7 + 0.25 * i), GH.emissive("fire", 6, 0.7))
    if t == 1:                                                                               # the hearth
        for i in range(5):
            for an in np.linspace(0, 2 * np.pi, 9)[:-1]:
                if i in (2, 3) and np.cos(an) < -0.8:
                    continue                                     # the mouth
                b.ell((hx + np.cos(an) * 4.6, 1.1 + i * 2.1, hz + np.sin(an) * 4.6), (1.4, 1.15, 1.4), STONE)
    else:
        if t == 2:
            masonry(b, (hx, 0, hz), 10.0, 10.0, 10.0)
        else:
            tbox(b, (hx, 5.0, hz), (10.0, 10.0), (9.0, 9.0), 10.0, PLATE)
        b.box((hx, 10.2, hz), (9.4, 0.6, 9.4), M_BRONZE if t == 2 else M_DIRON)
        if t == 3:
            b.box((hx - 4.55, 3.0, hz), (0.2, 0.6, 6.0), RUNE)
    my = mouth[1]
    b.box((hx - 4.4, my, hz), (1.2, 3.4, 3.8), M_HOLE)                                        # the firing mouth
    for dz in (-1.2, 0.0, 1.2):
        b.ell((hx - 3.8, my - 0.4, hz + dz), (0.8, 1.3, 0.8), GH.emissive("fire", 6, 0.6))
    piv = arr((hx, 21.0, hz))
    for z in (-1, 1):                                                                         # the cradle
        b.cyl((hx, 10.4, hz + z * 7.6), piv + (0, 0, z * 7.6), 0.8, M["frame"], seg=6)
        b.cyl(piv + (0, 0, z * 7.6), piv + (0, 0, z * 6.1), 0.6, M_IRON, seg=6)
    tilt = -1.0 if pose == "attack" else 0.0
    R = rot_z(tilt)
    pot = Model()
    pot.cyl((0, -6.0, 0), (0, 0, 0), 3.6, M_DIRON, r1=4.8, seg=16)
    pot.cyl((0, 0, 0), (0, 0.9, 0), 5.1, M_IRON, seg=16)
    pot.cyl((0, -2.2, 0), (0, -1.4, 0), 4.5, M["trim"] if t > 1 else ROPE, seg=16)
    if tilt == 0.0:
        pot.cyl((0, 0.7, 0), (0, 1.0, 0), 4.5, TAR_HOT, seg=16)
    if t == 3:
        for a in np.linspace(0, 2 * np.pi, 7)[:-1]:
            spike(pot, (np.cos(a) * 4.4, -3.0, np.sin(a) * 4.4), (np.cos(a) * 6.4, -3.0, np.sin(a) * 6.4), 0.5, M_IRON)
    b.extend(pot.transformed(R, piv + (0, 2.0, 0)).transformed(I3, -piv).scaled(1.2).transformed(I3, piv))
    fx = G["fx"]
    if pose == "attack":                                                                      # boiling tar poured on the cells ahead
        lip = piv + ((0, 2.0, 0) + R @ arr((5.0, 0.9, 0))) * 1.2
        end = arr((hx + 14.0, 0.5, hz))
        pts = [lip, lip + (3.4, -1.2, 0), lerp(lip, end, 0.6) + (0, -1.5, 0), end]
        for p0, p1, r0 in zip(pts[:-1], pts[1:], (1.9, 1.7, 1.6)):
            fx.cyl(p0, p1, r0, TAR_HOT, r1=r0 - 0.2, seg=8)
        fx.ell(end + (3.0, 0, 0), (8.0, 0.6, 7.0), TAR)
        fx.ell(end + (2.0, 0.4, 0), (4.0, 0.5, 3.6), TAR_HOT)
        puffs(fx, end + (2.0, 3.0, 0), n=3, r=2.4, spread=3.0, seed=4)
    else:
        puffs(fx, piv + (0, 6.0, 0), n=2, r=2.0, spread=2.0, seed=5)
    return G, allow + [("bld", "fx")]


# ---------------------------------------------------------------- Громовая вышка: the Sage at the foot of a lightning tower
def thunder(t, pose="idle", deployed=True):
    if not deployed:
        return golem_pack("Мудрец", "mast", t)
    from leaders_h import lattice, zigzag
    S = GH.SAGE
    A = dict(S["poses"]["idle"])
    A.update(hand_n=(6.0, -9.0, 2.0), staff_dir=(0.0, 1.0, 0.0), hold=0.62, fx=None)
    if pose == "attack":
        A.update(hand_f=(9.0, -4.0, -1.0), pole_f=(-0.6, -0.2, -1.0))
    G, info, allow = golem("Мудрец", A, fx=False)
    b = G["bld"]
    M = tier_mats(t)
    tx, tz, top = -16.0, -6.0, 66.0
    base = arr((tx, 0, tz))
    if t == 1:
        for (dx, dz) in ((-2.4, -2.4), (2.4, -2.4), (2.4, 2.4), (-2.4, 2.4)):
            b.cyl(base + (dx * 1.6, 0, dz * 1.6), base + (dx * 0.3, top - 6, dz * 0.3), 0.75, LOG, seg=6)
        for y in np.arange(6.0, top - 8, 9.0):
            k = 1.6 - (1.3 * y / (top - 6))
            b.cyl(base + (-2.4 * k, y, -2.4 * k), base + (2.4 * k, y, 2.4 * k), 0.4, ROPE, seg=4)
            b.cyl(base + (2.4 * k, y, -2.4 * k), base + (-2.4 * k, y, 2.4 * k), 0.4, ROPE, seg=4)
    else:
        if t == 2:
            masonry(b, base, 9.0, 9.0, 4.4, course=2.2)
        else:
            tbox(b, base + (0, 2.0, 0), (9.0, 9.0), (8.0, 8.0), 4.0, PLATE)
        lattice(b, base + (0, 4.0, 0), base + (0, top - 6, 0), 4.2, M["frame"], up=(1, 0, 0), r=0.45, tri=False)
        if t == 3:
            b.box(base + (4.05, 2.0, 0), (0.2, 0.6, 5.0), RUNE)
            for z in (-1, 1):
                spike(b, base + (0, top - 12, 2.4 * z), base + (0, top - 12, 5.4 * z), 0.6, M_IRON)
    for i in range(4):                                                                       # insulators, coil, toroid, the ball
        y = top - 6 + i * 1.1
        b.cyl(base + (0, y, 0), base + (0, y + 0.6, 0), 1.6 - 0.1 * i, GH.PORC, seg=10)
    b.cyl(base + (0, top - 1.6, 0), base + (0, top - 0.8, 0), 3.6, GH.COPPER, seg=16)
    b.ell(base + (0, top + 2.2, 0), (3.0, 3.0, 3.0), GH.COPPER)
    fx = G["fx"]
    ball = base + (0, top + 2.2, 0)
    for i, d in enumerate(((3.0, 2.0, 2.0), (-2.4, 3.0, -1.6), (0.6, 3.6, -3.0))):
        zigzag(fx, ball, ball + arr(d), n=3, amp=0.5, seed=i, r=0.22, mat=GH.ARC)
    cable = [info["X"]((-4.6, 36.0, -3.0)), base + (3.0, 30.0, 1.0), base + (1.6, 18.0, 1.8)]           # from the horns to the tower
    for p0, p1 in zip(cable[:-1], cable[1:]):
        G["cable"].cyl(p0, p1, 0.35, GH.M_HOSE if hasattr(GH, "M_HOSE") else M_DIRON, seg=5)
    if pose == "attack":                                                                      # the tower strikes the nearest enemy
        tgt = arr((34.0, 1.0, 4.0))
        zigzag(fx, ball, tgt, n=10, amp=3.0, seed=9, r=0.5, mat=GH.ARC)
        fx.ell(ball, (4.0, 4.0, 4.0), GH.ENERGY)
        fx.ell(tgt, (3.0, 1.2, 3.0), GH.ENERGY)
        sparks(fx, tgt, n=6, spread=3.0, seed=10, big=False)
    return G, allow + [("cable", "back"), ("cable", "bld"), ("cable", "chest")]


# ---------------------------------------------------------------- Подъёмная стрела: the Mechanic becomes a crane
def boom(t, pose="idle", deployed=True):
    if not deployed:
        return golem_pack("Механик", "jib", t)
    from leaders_h import lattice
    S = GH.MEH
    A = dict(S["poses"]["idle"])
    A.update(t=(0.0, -2.0, 0.0), ank=((3.0, 3.6, 5.0), (-1.2, 3.6, -5.0)), fx=None)
    G, info, allow = golem("Механик", A, fx=False)
    b = G["bld"]
    M = tier_mats(t)
    X = info["X"]
    for z in (-1, 1):                                                                        # outriggers to both sides, on pads
        a = X((-5.2, 15.0, 2.6 * z))
        f = arr((-9.0, 0.6, 15.0 * z))
        b.cyl(a, f + (0, 3.0, 0), 0.9, M["frame"] if t > 1 else LOG, seg=6)
        HM.ram(b, f + (0, 3.0, 0), f + (0, 1.0, 0), 0.6)
        b.cyl(f, f + (0, 0.7, 0), 2.0, M_DIRON, seg=10)
    root = X((-6.6, 36.0, 0.0))
    mast_top = X((-8.0, 56.0, 0.0))
    up = pose == "attack"
    tip = mast_top + (arr((26.0, 12.0, 0.0)) if up else arr((30.0, -3.0, 0.0)))
    if t == 1:                                                                               # a derrick of poles lashed with rope
        for z in (-1.4, 1.4):
            b.cyl(root + (0, 0, z), mast_top, 0.7, LOG, seg=6)
        b.cyl(mast_top + (-0.4, -1.0, 0), tip, 0.8, LOG, seg=6)
        b.ell(mast_top, (1.1, 1.1, 1.1), ROPE)
    else:
        lattice(b, root, mast_top, 2.4, M["frame"], up=(1, 0, 0), r=0.35, tri=False)
        lattice(b, mast_top + (0.5, -0.8, 0), tip, 2.2, M["frame"], n=8, r=0.32)
        if t == 3:
            b.box(root + (1.3, 3.0, 0), (0.2, 3.0, 0.6), RUNE)
            spike(b, mast_top, mast_top + (-3.0, 2.0, 0), 0.6, M_IRON)
    b.cyl(mast_top + (0, 1.2, 0), tip, 0.12, M_DIRON, seg=4)                                  # the stay
    b.cyl(tip - (0, 0, 0.6), tip + (0, 0, 0.6), 0.9, M_DIRON, seg=10)
    hook = tip + (0, -9.0 if not up else -6.0, 0)
    b.cyl(tip, hook, 0.12, M_DIRON, seg=4)
    b.box(hook + (0, -0.6, 0), (1.0, 1.4, 1.0), M_DIRON)
    b.cyl(hook + (0, -1.3, 0), hook + (0, -2.6, 0), 0.25, M_STEEL, seg=5)
    if up:                                                                                    # lifting a golem: a yoke with two chains
        y = hook + (0, -2.8, 0)
        b.box(y, (1.0, 0.6, 7.0), M_IRON)
        for z in (-3.0, 3.0):
            b.cyl(y + (0, 0, z), y + (0.6, -4.0, z * 1.2), 0.18, M_STEEL, seg=4)
    return G, allow + [("bld", "back"), ("bld", "manip"), ("bld", "pelvis")]


# ---------------------------------------------------------------- Полевая кузня: the Mechanic at a forge
def forge(t, pose="idle", deployed=True):
    if not deployed:
        return golem_pack("Механик", "forge", t)
    S = GH.MEH
    A = dict(S["poses"]["attack" if pose == "attack" else "idle"])
    A.update(fx=None)
    G, info, allow = golem("Механик", A, fx=False)
    b = G["bld"]
    M = tier_mats(t)
    fx_, fz = 6.0, -19.0                                                                      # the hearth beside it, the anvil in front
    if t == 1:
        for i in range(4):
            for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
                b.ell((fx_ + np.cos(a) * 4.4, 1.2 + i * 2.2, fz + np.sin(a) * 4.0), (1.4, 1.2, 1.4), Mat(ramp("#2a1408", "#4a2412", "#6e3a1e", "#94542e", "#b8744a")))
    else:
        if t == 2:
            masonry(b, (fx_, 0, fz), 9.0, 8.0, 8.8)
        else:
            tbox(b, (fx_, 4.4, fz), (9.0, 8.0), (8.4, 7.6), 8.8, PLATE)
        if t == 3:
            b.box((fx_ + 4.25, 2.0, fz), (0.2, 0.6, 5.0), RUNE)
    b.ell((fx_ + 1.0, 9.0, fz), (3.0, 1.0, 2.6), GH.emissive("fire", 6, 0.6))                 # the coals
    tbox(b, (fx_, 13.0, fz), (8.0, 7.4), (3.0, 3.0), 4.6, M["trim"] if t > 1 else M_RUST)       # the hood
    b.cyl((fx_, 15.0, fz), (fx_, 30.0, fz), 1.2, M_DIRON, seg=8)                                # the chimney
    G["fx"].ell((fx_ - 0.6, 32.6, fz + 0.4), (2.2, 1.8, 2.0), M_PUFF)
    bx, bz = 14.0, 1.0                                                                        # the anvil on a block
    b.box((bx, 2.2, bz), (3.6, 4.4, 4.2), LOG if t < 3 else PLATE)
    tbox(b, (bx, 5.6, bz), (3.2, 4.6), (2.2, 3.2), 2.4, M_IRON)
    b.box((bx, 7.2, bz), (2.6, 0.8, 6.4), M_STEEL)
    b.cyl((bx, 7.0, bz + 3.2), (bx, 7.0, bz + 5.0), 0.7, M_STEEL, r1=0.1, seg=6)                 # the horn
    G["bld2"].box((fx_ - 7.0, 1.2, fz), (5.0, 2.4, 3.6), LOG)                                 # bellows
    G["bld2"].box((fx_ - 7.0, 2.7, fz), (4.6, 0.6, 3.2), Mat(ramp("#1a0e08", "#2e1a10", "#46281a", "#603a26", "#7e5038")))
    if pose == "attack":
        sparks(G["fx"], arr((bx, 8.0, bz)), n=8, spread=3.0, seed=12, big=True)
    return G, allow + [("bld", "bld2")]


MODULES = {
    "tower": ("Бойницы", "Орудие", tower),
    "wall": ("Щит-стена", "Страж", wall),
    "gate": ("Створки", "Страж", gate),
    "pitch": ("Смоляной котёл", "Горн", pitch),
    "press": ("Пресс", "Страж", press),
    "thunder": ("Громовая вышка", "Мудрец", thunder),
    "boom": ("Подъёмная стрела", "Механик", boom),
    "forge": ("Полевая кузня", "Механик", forge),
}


def parts(key, deployed=True, t=2, pose="idle"):
    return MODULES[key][2](t, pose, deployed)


def check(key, deployed=True, t=2, pose="idle"):
    G, allow = parts(key, deployed, t, pose)
    return report(G, allow + [("bld", "bld")], skip=("fx",))


def build(key, deployed=True, t=2, pose="idle", k=1.6, canvas=(120, 100, 56, 84)):
    G, _ = parts(key, deployed, t, pose)
    cw, ch, cx, cy = canvas
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    import sys
    from PIL import Image
    from paths import out
    keys = sys.argv[1:] or list(MODULES)
    rows = []
    for key in keys:
        row = []
        for dep, t, pose in ((False, 2, "idle"), (True, 1, "idle"), (True, 2, "idle"), (True, 3, "idle"), (True, 2, "attack")):
            print(key, "deployed" if dep else "marching", t, pose, check(key, dep, t, pose))
            im = build(key, dep, t, pose, k=2.0).image(1)
            bb = im.getbbox()
            row.append(im.crop((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6)))
        rows.append(row)
    W = max(sum(i.width + 16 for i in r) for r in rows)
    H = sum(max(i.height for i in r) + 16 for r in rows)
    sheet = Image.new("RGBA", (W, H), (52, 46, 58, 255))
    y = 0
    for r in rows:
        x, h = 0, max(i.height for i in r)
        for i in r:
            sheet.alpha_composite(i, (x, y + h - i.height))
            x += i.width + 16
        y += h + 16
    sheet.save(out("buildings_check.png"))
