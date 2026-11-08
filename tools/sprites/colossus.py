"""Father of the Colossus: a titan of its own build, far bigger than any golem."""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_BRONZE, M_HOLE, STYLE1, emissive
from golem7 import tbox, M_PUFF, M_SPARK
from leaders import CLOTH_RED

FURNACE = Mat(EMBER, emissive=hexc("#ff7a20"), glow_r=34, glow_k=0.9)
SLIT = Mat(EMBER, emissive=hexc("#ffb040"), glow_r=10, glow_k=0.6)
RUNEB = Mat(EMBER, emissive=hexc("#ff8a30"), glow_r=8, glow_k=0.45)


def spike(m, a, b, r, mat=M_BRONZE):
    m.cyl(a, b, r, mat, r1=0.15, seg=6)


def colossus(pose="idle"):
    m = Model()
    # legs: columns with knee plates and huge feet
    for z in (-8.5, 8.5):
        tbox(m, (0, 17.5, z), (9.0, 9.0), (10.0, 10.0), 11.0, M_BRONZE)
        m.box((0.5, 16.0, z), (10.4, 1.6, 10.4), M_DIRON)
        tbox(m, (5.2, 12.5, z), (1.6, 7.0), (1.8, 8.0), 6.0, M_IRON)       # knee plate
        tbox(m, (0.5, 7.0, z), (11.0, 10.0), (9.4, 9.0), 10.0, M_BRONZE)
        tbox(m, (2.5, 1.5, z), (17.0, 12.0), (14.0, 10.0), 3.0, M_IRON)
        for dz in (-3.5, 0, 3.5):
            spike(m, (10.5, 1.4, z + dz), (13.5, 0.8, z + dz * 1.1), 0.9, M_IRON)
    up = Model()
    tbox(up, (0, 25.0, 0), (18, 22), (20, 25), 5.0, M_IRON)               # pelvis
    for i, z in enumerate(np.linspace(-10, 10, 5)):
        tbox(up, (9.8, 20.5, z), (1.0, 4.0), (1.0, 4.6), 7.0, M_DIRON)    # skirt plates
    tbox(up, (0, 38.5, 0), (20, 24), (26, 36), 23.0, M_BRONZE)            # torso, broad at the top
    up.box((11.6, 39.0, 0), (1.2, 13.0, 15.0), M_HOLE)                    # chest furnace
    up.box((12.7, 39.0, 0), (0.6, 11.5, 13.5), FURNACE)
    for z in np.linspace(-6, 6, 5):
        up.box((13.5, 39.0, z), (0.9, 14.0, 1.1), M_DIRON)
    for y in (32.0, 46.0):
        up.box((13.5, y, 0), (0.9, 1.2, 16.0), M_DIRON)
    up.box((11.6, 30.0, 0), (1.0, 1.2, 22.0), RUNEB)                      # rune band
    # pauldrons with spikes
    for z in (-18.0, 18.0):
        s = np.sign(z)
        for i, (dy, w) in enumerate(((0.0, 13.0), (-3.0, 12.0), (-5.6, 10.5))):
            tbox(up, (0.5, 50.5 + dy, z + s * i * 0.8), (w, 11.0), (w - 3, 8.0), 3.0, M_IRON if i else M_BRONZE,
                 rot_x(-0.3 * s))
        for dx in (-4.0, 0.0, 4.0):
            spike(up, (dx, 52.5, z), (dx - 0.5, 60.0, z + s * 2.5), 1.3)
    # head: a great helm sunk between the shoulders, crown of spikes, glowing slit
    up.cyl((4.0, 49.0, 0), (4.0, 58.0, 0), 5.0, M_IRON, seg=12)
    up.box((9.0, 54.0, 0), (0.8, 1.3, 7.0), SLIT)
    up.box((9.0, 51.5, 0), (0.8, 4.0, 1.2), SLIT)
    for a in np.linspace(-1.0, 1.0, 5):
        spike(up, (4.0 + np.cos(a) * 4.2, 58.0, np.sin(a) * 4.2), (4.5 + np.cos(a) * 5.4, 64.0 - abs(a) * 1.5, np.sin(a) * 5.4), 0.9)
    # back: reactor drum, twin stacks, a banner
    up.cyl((-13.5, 30.0, 0), (-13.5, 47.0, 0), 6.2, M_DIRON, seg=12)
    for y in (33.0, 38.0, 43.0):
        up.cyl((-13.5, y, 0), (-13.5, y + 1.0, 0), 6.5, RUNEB, seg=12)
    for z in (-7.0, 7.0):
        up.cyl((-12.0, 44.0, z), (-14.5, 70.0, z), 2.2, M_DIRON, seg=8)
        up.cyl((-14.5, 70.0, z), (-14.6, 71.6, z), 3.0, M_DIRON, seg=8)
        for i, d in enumerate(((-15.5, 74.0, z), (-18.0, 78.5, z * 0.8), (-22.0, 82.0, z * 0.6))):
            up.ell(np.array(d), (2.6 + i * 0.9, 2.3 + i * 0.8, 2.6 + i * 0.9), M_PUFF)
    up.cyl((-9.0, 46.0, 0), (-9.5, 80.0, 0), 0.6, M_DIRON, seg=5)
    up.box((-12.5, 74.0, 0), (6.0, 11.0, 0.6), CLOTH_RED)
    up.box((-12.5, 74.5, 0.4), (2.4, 3.0, 0.3), M_BRONZE)
    up.box((-12.5, 79.8, 0), (7.0, 0.8, 0.8), M_BRONZE)
    # near arm: a giant tower shield
    Sn = np.array((0.5, 47.0, 19.0))
    En = Sn + (3.0, -11.0, 2.5)
    up.cyl(Sn, En, 4.4, M_IRON, seg=8)
    up.ell(En, (4.6, 4.6, 4.6), M_BRONZE)
    R = rot_y(-0.5)
    c = En + np.array((5.0, -5.0 + (2.0 if pose == "attack" else 0), 5.0))
    up.box(c, (16.0, 26.0, 1.6), M_BRONZE, R)
    up.box(c + R @ np.array((0, 0, 0.9)), (13.5, 23.5, 1.4), M_IRON, R)
    up.box(c + R @ np.array((0, 3, 1.7)), (2.2, 15.0, 0.5), M_BRONZE, R)
    up.box(c + R @ np.array((0, 6, 1.7)), (10.0, 2.2, 0.5), M_BRONZE, R)
    up.ell(c + R @ np.array((0, 6, 2.0)), (1.8, 1.8, 1.0), FURNACE, R)
    for sx in (-5.5, 5.5):
        for sy in (-9.5, 0.0, 9.5):
            up.ell(c + R @ np.array((sx, sy, 1.9)), (0.9, 0.9, 0.6), M_BRONZE, R)
    # far arm: the anvil hammer
    Sf = np.array((0.5, 47.0, -19.0))
    if pose == "idle":
        Ef, Hf, shaft = Sf + (4.0, -11.0, -1.5), Sf + (12.0, -10.0, -1.5), np.array((3.0, 26.0, 0))
    else:
        Ef, Hf, shaft = Sf + (10.0, -3.0, -1.5), Sf + (20.0, -10.0, -1.5), np.array((22.0, -14.0, 0))
    up.cyl(Sf, Ef, 4.4, M_IRON, seg=8)
    up.ell(Ef, (4.6, 4.6, 4.6), M_BRONZE)
    up.cyl(Ef, Hf, 4.0, M_IRON, seg=8)
    up.ell(Hf, (3.6, 3.6, 3.6), M_BRONZE)
    sd = shaft / np.linalg.norm(shaft)
    top = Hf + shaft
    up.cyl(Hf - sd * 5, top, 1.6, M_DIRON, seg=6)
    Rh = rot_z(np.arctan2(sd[1], sd[0]) - np.pi / 2)
    tbox(up, top, (24.0, 12.0), (18.0, 10.0), 11.0, M_IRON, Rh)
    up.box(top, (4.0, 11.6, 12.6), RUNEB, Rh)
    if pose == "attack":
        lean = rot_z(-0.14)
        up = up.transformed(lean, np.array((0, 24.0, 0)) - lean @ np.array((0, 24.0, 0)))
        ground = np.array((44.0, 1.0, -20.0))
        for a in np.linspace(0, 2 * np.pi, 14)[:-1]:
            up.ell(ground + (np.cos(a) * 9.0, 0.5, np.sin(a) * 9.0), (0.6, 0.6, 0.6), M_SPARK)
        for d in ((-4, 2, 3), (4, 3, -3), (0, 4, 0)):
            up.ell(ground + d, (4.0, 3.0, 4.0), M_PUFF)
    m.extend(up)
    return m


def build(pose="idle", k=1.0):
    w, h, ox, oy = int(150 * k), int(140 * k), int(60 * k), int(112 * k)
    spr = rim_light(render(colossus(pose).scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


if __name__ == "__main__":
    from paths import out
    a, b = build("idle", 1.3), build("attack", 1.3)
    sc = Scene(a.w * 2, a.h)
    sc.rgb[:] = hexc("#2c2436")
    sc.blit(a, 0, 0)
    sc.blit(b, a.w, 0)
    sc.image(2).save(out("test_colossus.png"))
