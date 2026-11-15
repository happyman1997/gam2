"""The swarm forms up by itself at the start of a battle (CONCEPT.md, «Строй сам»): there is no placing — each
flock takes its row by its role, and the cells fill from the middle of the field to its edges. Here the swarm
streams in from the right, flock after flock in the order of the roles, each settling into its cells: the
woodlouse (a shield) in the middle of the front row, the strikers either side of it (the sturdiest first: the
soldier ants, the beetles, then the scorpions and the ants), the wasps (flank) at the end of the front row, the
barrels (archers) at the back, the Queen (a leader in the rear) last, in the middle of the last row. When all
stand, the flocks' seams light up — the neighbours on them are the brood's pairs.

    python3 tools/sprites/swarm_formation.py   -> out/swarm_formation.gif, out/swarm_formation.png
"""
import copy
import numpy as np
from kit import Scene, hexc
import battle as BT
import frames as F
import swarm1 as W
import swarm_ui as UI
import swarm_hud as SH
import pxfx
from ui_anim import out_back, FPS
from paths import out

FRONT, BACK, MID, ROWS = 11, 18, 7, 15          # the swarm's zone: its front column, its back, the middle row
ORDER = [MID + d for k in range(ROWS) for d in ((-k, k) if k else (0,)) if 0 <= MID + d < ROWS]

FLOCKS = [   # (name, traits, soldier, count, role, per cell, seam colour) — in the order the roles stand
    ("мокрица", ("carapace",), True, 1, "shield", 1, "#8a96a8"),
    ("муравей-солдат", (), True, 2, "strike", 1, "#c08a5a"),
    ("жук", ("horn",), True, 2, "strike", 1, "#8aa040"),
    ("скорпион", ("stinger",), False, 7, "strike", 4, "#d08a3a"),
    ("муравей", (), False, 19, "strike", 4, "#b0703a"),
    ("оса", ("wings",), False, 4, "flank", 4, "#e0c040"),
    ("бочонок", ("acid",), False, 2, "archer", 4, "#9ae030"),
]
SLOTS4 = ((-11, -6), (11, -7), (-10, 8), (12, 7))


def deploy():
    """Each flock's cells: shields and strikers in the front row from its middle out (spilling into the second),
    the flank at the front row's ends, top and bottom by turns, the archers at the back, the rear leader in the
    last row's middle."""
    taken, cells = set(), {}
    flank_side = 0
    for name, traits, soldier, n, role, per, _ in FLOCKS:
        need = -(-n // per)
        got = []
        if role in ("shield", "strike"):
            for col in range(FRONT, BACK):
                for r in ORDER:
                    if len(got) < need and (col, r) not in taken and not (col == FRONT and r in (0, ROWS - 1)):
                        got.append((col, r))
                if len(got) >= need:
                    break
        elif role == "flank":
            for k in range(need):
                r = 0 if flank_side % 2 == 0 else ROWS - 1
                flank_side += 1
                got.append((FRONT, r) if (FRONT, r) not in taken else (FRONT + 1, r))
        elif role == "archer":
            for r in ORDER:
                if len(got) < need and (BACK - 4, r) not in taken:     # the back rows, before the leader's
                    got.append((BACK - 4, r))
        taken |= set(got)
        cells[name] = got
    return cells


def cell_xy(c, r):
    return BT.X0 + (c + 0.5) * BT.CW, BT.Y0 + (r + 0.75) * BT.CH


def background():
    sc = Scene(BT.WW, BT.HH)
    BT.ground(sc)
    for (c, r, size, frame) in ((5, 6, 6, "Страж"), (5, 0, 5, "Мудрец"), (6, 11, 5, "Горн"), (3, 3, 5, "Орудие"),
                                (3, 9, 4, "Механик")):
        n = BT.CELLS[size]
        fx, fy = BT.X0 + (c + n / 2) * BT.CW, BT.Y0 + (r + n * 0.72) * BT.CH
        BT.footprint(sc, c, r, n)
        BT.shadow(sc, fx + 2, fy, 22 * n + 14, 6 + 3 * n)
        BT.put(sc, F.build(frame, "idle", k=BT.GK[size]), fx, fy)
    return sc


def frames_():
    cells = deploy()
    rnd = np.random.RandomState(4)
    movers = []                                   # (sprites idle/attack, target, start, t0, duration)
    t0 = 0
    for j, (name, traits, soldier, n, role, per, _) in enumerate(FLOCKS):
        for i in range(n):
            c, r = cells[name][i // per]
            cx, cy = cell_xy(c, r)
            dx, dy = (0, 0) if per == 1 else SLOTS4[i % per]
            seed = 900 + j * 40 + i
            sprs = (W.build(traits, rnd.uniform(-0.12, 0.12), "idle", soldier, k=1.0, genes=W.genes_for(seed)),
                    W.build(traits, rnd.uniform(-0.12, 0.12), "attack", soldier, k=1.0, genes=W.genes_for(seed)))
            start = (BT.WW + 30 + rnd.uniform(0, 80), cy + dy + rnd.uniform(-30, 30))
            movers.append((sprs, (cx + dx, cy + dy), start, t0 + rnd.randint(0, 5), 16 + rnd.randint(0, 6)))
        t0 += 4
    q = W.queen(0.0, "idle", k=0.92)                                     # the Queen: a leader in the rear, last
    qx, qy = cell_xy(BACK - 1.7, MID + 0.9)                              # her three cells in the last rows' middle
    movers.append(((q, q), (qx, qy), (BT.WW + 120, qy), t0 + 2, 26))
    end = max(m[3] + m[4] for m in movers)
    base = background()
    out_frames = []
    for f in range(end + 22):
        sc = copy.deepcopy(base)
        drawn = []
        for sprs, (tx, ty), (sx, sy), st, dur in movers:
            if f < st:
                continue
            u = min(1.0, (f - st) / dur)
            e = 1 - (1 - u) ** 3
            x, y = sx + (tx - sx) * e, sy + (ty - sy) * e
            walking = u < 1.0
            drawn.append((y, x, sprs[(f // 3) % 2] if walking else sprs[0], sprs[0] is q))
        for y, x, spr, big in sorted(drawn, key=lambda t: t[0]):
            BT.shadow(sc, x + (20 if big else 0), y, 150 if big else 14, 20 if big else 3)
            BT.put(sc, spr, x, y, mirror=True)
        if f >= end:                                                     # the seams between the flocks light up
            k = min(1.0, (f - end) / 8)
            seams(sc, cells, k)
        out_frames.append(sc)
    return out_frames


def seams(sc, cells, k):
    """Each flock's cells outlined in its colour, dotted — where two meet, the neighbours are the brood's pairs."""
    for name, *_r, col in FLOCKS:
        m = np.zeros((BT.HH, BT.WW), bool)
        for (c, r) in cells[name]:
            x0, y0 = BT.X0 + c * BT.CW, BT.Y0 + r * BT.CH
            m[y0 + 2:y0 + BT.CH - 2, x0 + 2:x0 + BT.CW - 2] = True
        o, _, _ = UI.edges(m)
        o &= ((sc.xx + sc.yy) % 3 != 0)
        sc.rgb[o] = sc.rgb[o] * (1 - 0.8 * k) + hexc(col) * 0.8 * k


def main():
    frs = frames_()
    images = [f.image(2) for f in frs]
    pxfx.save_gif(images, out("swarm_formation.gif"), FPS, half=True)
    print("swarm_formation.gif", len(images))
    last = frs[-1]
    SH.letters(last, "строй сам: стаи встают по ролям", 940, 512, "text", 16, col=(214, 196, 150), align="right")
    img = last.image(2)
    img.save(out("swarm_formation.png"))
    print("swarm_formation.png", img.size)


if __name__ == "__main__":
    main()
