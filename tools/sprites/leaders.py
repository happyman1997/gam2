"""Shared pieces for leaders: materials and a small human figure. The leaders live in their own files:
inventor.py (Inventor, Father of the Colossus), maniac.py (Maniac), architect.py (Architect)."""
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
