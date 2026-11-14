"""The battle's moments, in the Foundry's iron: what the field shows besides the golems and the swarm.

  the leader's ability — a brass box with the crown glyph pops over the leader with its name and line (the
                         Architect's «Кладка»: a run of wall laid on the cell before him, the stones still settling);
  a golem breaking     — the Forge goes down mid-fight: sparks and a puff of smoke off it, its core gone dark, a part
                         torn off lying by its feet, the breakdown mark by its side;
  damage numbers       — struck into the air like hot iron: orange with a dark red edge, a heavy blow bigger and
                         white-hot with «!», damage to a golem red, a miss grey;
  the battle's end     — the field dimmed, a cast plate across it: ПОБЕДА between turning cogs, or ПОРАЖЕНИЕ cold.

    python3 tools/sprites/battle_moments.py   -> out/foundry_battle_moments.png, out/foundry_battle_end.png,
                                                 out/foundry_battle_end_defeat.png
"""
import numpy as np
from kit import hexc
import foundry_ui as FU
import foundry_hud as FH
from foundry_hud import letters, H, SU, INK, MUTED, GOLD, WW, HH, S, out
import swarm_status as ST


def number(sc, x, y, text, kind="hit"):
    """A damage number struck in hot iron."""
    col, col2, px = {"hit": ((255, 176, 80), (120, 30, 10), 16), "crit": ((255, 246, 210), (190, 60, 20), 24),
                     "hurt": ((255, 110, 90), (90, 10, 10), 16), "miss": ((170, 166, 160), (50, 48, 52), 16),
                     "heal": ((150, 240, 130), (40, 110, 40), 16)}[kind]
    if kind == "crit":
        sc.glow(x, y + 12, 18, hexc("#ff8a2a"), 0.4)
    letters(sc, text, x, y, "title", px, col=col, col2=col2, align="center")


def leader_pop(sc, name, line, cx, top):
    """The leader's ability firing, over the leader: a brass box with the crown, the name, its line."""
    w = 196
    x0, y0 = int(cx - w // 2), int(top - 58)
    sc.glow(cx, y0 + 20, 34, hexc("#f0c878"), 0.4)
    FU.cell(sc, x0, y0, x0 + w, y0 + 46, "hi")
    H.glyph(sc, "лидер", x0 + 8, y0 + 8, 2)
    letters(sc, name, x0 + 36, y0 + 4, "text", 16, col=GOLD)
    H.fx_line(sc, x0 + 36, y0 + 22, line)


def wall_run(sc, x0, y_base, n=3):
    """A short run of fresh wall: dressed stones in two courses, dust still rising off them."""
    for c in range(n):
        for r in range(2):
            bx0 = x0 + c * 16 + (8 if r else 0)
            by0 = y_base - 10 - r * 10
            m = (sc.xx >= bx0) & (sc.xx < bx0 + 15) & (sc.yy >= by0) & (sc.yy < by0 + 9)
            t = np.clip((sc.yy - by0) / 9.0, 0, 1)[..., None]
            sc.rgb[m] = (hexc("#a89e88") * (1 - t) + hexc("#6e6656") * t)[m]
            o, top, _ = SU.edges(m)
            sc.rgb[top] = hexc("#d0c6ae")
            sc.rgb[o & ~top] = SU.OUTL
    rnd = np.random.RandomState(3)
    for _ in range(14):
        px_, py_ = int(x0 + rnd.uniform(0, n * 16 + 8)), int(y_base - 24 - rnd.uniform(0, 14))
        sc.rgb[py_, px_] = sc.rgb[py_, px_] * 0.4 + hexc("#c8beaa") * 0.6


def breaking(sc, gx, gy, gspr):
    """The Forge breaking mid-fight: a burst of sparks, a puff of smoke, its core dark, a torn-off part by it."""
    gx, gy = int(gx), int(gy)
    top = int(ST.top_of(gspr, gy))
    cx, cy = gx + 4, (top + gy) // 2
    for k in range(18):                                                      # sparks thrown off
        a = k * 2 * np.pi / 18 + 0.3
        r = 10 + (k % 4) * 6
        x, y = int(cx + np.cos(a) * r), int(cy + np.sin(a) * r * 0.7)
        sc.rgb[y, x] = hexc("#ffd890") if k % 3 else hexc("#ff8a2a")
        sc.rgb[y + 1, x] = hexc("#c2500e")
    for (dx, dy, r) in ((-8, -26, 7), (4, -34, 9), (14, -24, 6)):            # smoke
        d = np.hypot(sc.xx - (cx + dx), sc.yy - (top + dy + 10))
        m = d <= r
        sc.rgb[m] = sc.rgb[m] * 0.45 + hexc("#4a4850") * 0.55
    d = np.hypot(sc.xx - cx, sc.yy - cy)                                     # the core gone dark
    sc.rgb[(d <= 5) & (d > 3)] = hexc("#2a2830")
    sc.rgb[d <= 3] = hexc("#121114")
    FH.mod_icon(sc, "maw", gx + 26, gy - 10, 1)                              # the part torn off, on the ground
    sc.rgb[gy + 6:gy + 8, gx + 24:gx + 44] = sc.rgb[gy + 6:gy + 8, gx + 24:gx + 44] * 0.5
    FH.mark_broken(sc, gx - 58, gy - 46)


def moments():
    sc = FH.battle_view("run", ret=True, pops=[])
    fd = FH._FIELD
    gp = fd["gpos"]
    lx, ly, lspr = fd["lead"]
    ltop = ST.top_of(lspr, ly)
    wall_run(sc, int(lx + 30), int(ly + 4))
    leader_pop(sc, "Кладка", "{каждые:2} → стена I", lx, ltop - 4)
    breaking(sc, *gp[("Горн", 6, 2)])
    sx, sy, sspr = gp[("Страж", 5, 6)]                                        # numbers over the blows
    number(sc, sx + 70, ST.top_of(sspr, sy) + 4, "18!", "crit")
    number(sc, sx + 96, ST.top_of(sspr, sy) + 40, "6")
    ox, oy, ospr = gp[("Орудие", 3, 2)]
    number(sc, ox + 250, ST.top_of(ospr, oy) + 30, "9")
    number(sc, ox + 280, ST.top_of(ospr, oy) + 56, "мимо", "miss")
    mx, my, mspr = gp[("Мудрец", 5, 0)]
    number(sc, mx + 140, ST.top_of(mspr, my) + 52, "7")
    hx, hy, hspr = gp[("Горн", 6, 11)]
    number(sc, hx - 6, ST.top_of(hspr, hy) - 28, "-4", "hurt")
    kx, ky, kspr = gp[("Механик", 3, 9)]
    number(sc, kx, ST.top_of(kspr, ky) - 26, "+4", "heal")
    img = sc.image(S)
    img.save(out("foundry_battle_moments.png"))
    print("foundry_battle_moments.png", img.size)


def end(win=True, turn=0.0):
    sc = FH.battle_view("run", ret=True, pops=[])
    sc.rgb[34:] = sc.rgb[34:] * (0.5 if win else 0.35)
    if not win:
        FH.cold(sc, sc.yy >= 34, 0.6)
    cy = HH // 2 - 10
    sc.rgb[cy - 60:cy + 60, :] = sc.rgb[cy - 60:cy + 60, :] * 0.6
    FU.nameplate(sc, WW // 2 - 170, cy - 34, WW // 2 + 170, cy + 30, "", hot=win)
    text = "ПОБЕДА" if win else "ПОРАЖЕНИЕ"
    tw = SU.text_width(text, "title", 24)
    letters(sc, text, WW // 2 - tw // 2, cy - 12, "title", 24,
            col=(255, 222, 150) if win else (176, 178, 186), col2=(150, 100, 40) if win else (56, 58, 68))
    if win:
        FU.gears(sc, WW // 2 - 170 - 92, WW // 2 - 178, cy, flip=False, seed=0.0, turn=turn)
        FU.gears(sc, WW // 2 + 178, WW // 2 + 170 + 92, cy, flip=True, seed=0.3, turn=turn)
        sub = "рой рассеян · 41 врагов · {металл:+6}"
    else:
        sub = "Матка устояла · ей оставалось 18"
    w, _ = H.fx_line(sc, 0, 0, sub, draw=False)
    H.fx_line(sc, WW // 2 - w // 2, cy + 42, sub)
    letters(sc, "щелчок — дальше", WW // 2, cy + 68, "text", 16, col=MUTED, align="center")
    name = "foundry_battle_end.png" if win else "foundry_battle_end_defeat.png"
    img = sc.image(S)
    img.save(out(name))
    print(name, img.size)


if __name__ == "__main__":
    moments()
    end(True)
    end(False)
