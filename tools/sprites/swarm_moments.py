"""The battle's moments, in the swarm's own look: what the field shows besides the creatures and the golems.

  the leader's ability — a wax cell with the crown glyph pops over the leader with its name and line (the Queen's
                         «Кладка»: larvae dropping out under her, still wet);
  a creature dying     — it rolls onto its back, legs curled, a splash of ichor round it; by the Queen's
                         «Сердце роя» an egg is left glowing in the splash;
  damage numbers       — written by the swarm like its titles, dripping: the swarm's blows acid-green, a heavy one
                         bigger and pale with «!» and spatter, the swarm's own wounds amber ichor, poison green with
                         a bubble, psi violet, a miss grey, healing pale green;
  the battle's end     — the field dimmed, a plate with antennae across it: ПОБЕДА in dripping acid between two
                         wasps beating their wings, or ПОРАЖЕНИЕ grey between two dead.

    python3 tools/sprites/swarm_moments.py   -> out/swarm_battle_moments.png, out/swarm_battle_end.png,
                                                out/swarm_battle_end_defeat.png
"""
import numpy as np
from kit import hexc
import swarm_ui as UI
import swarm_hud as SH
from swarm_hud import letters, fx_line, glyph, icon, INK, MUTED, GOLD, S, out, WW, HH
import swarm_status as ST

NUM = {   # kind: (colour, edge, size)
    "hit": ((214, 250, 110), (50, 96, 20), 16), "crit": ((246, 255, 206), (96, 150, 24), 24),
    "hurt": ((240, 160, 70), (100, 40, 10), 16), "poison": ((150, 230, 60), (30, 70, 10), 16),
    "psi": ((206, 160, 255), (70, 30, 120), 16), "miss": ((170, 166, 160), (50, 48, 52), 16),
    "heal": ((196, 250, 160), (40, 110, 40), 16)}


def number(sc, x, y, text, kind="hit"):
    """A number written by the swarm: dripping, bristling letters."""
    col, col2, px = NUM[kind]
    if kind == "crit":
        sc.glow(x, y + 12, 20, hexc("#b0f040"), 0.4)
        rnd = np.random.RandomState(int(x))
        for _ in range(9):                                                   # spatter round it
            a, r = rnd.uniform(0, 2 * np.pi), rnd.uniform(22, 34)
            sx, sy = int(x + np.cos(a) * r * 1.3), int(y + 12 + np.sin(a) * r * 0.7)
            sc.rgb[sy:sy + 2, sx:sx + 2] = np.array(col2) * 1.4
    if kind == "poison":
        bx = x + UI.text_width(text, "title", px) // 2 + 6
        d = np.hypot(sc.xx - bx, sc.yy - (y + 4))
        sc.rgb[(d <= 4) & (d > 2.6)] = np.array(col)
        sc.rgb[int(y + 2), int(bx - 1)] = (240, 255, 210)
    letters(sc, text, x, y, "title", px, col=col, col2=col2, align="center", jitter=1, drips=3 if kind != "miss" else 0,
            seed=int(x) % 17)


def leader_pop(sc, name, line, key, cx, top):
    """The leader's ability firing, over it: a wax cell with the crown and the ability's icon, its name, its
    line."""
    w = 216
    x0, y0 = int(cx - w // 2), int(top - 62)
    sc.glow(cx, y0 + 22, 38, hexc("#f0c060"), 0.4)
    UI.cell(sc, x0, y0, x0 + w, y0 + 48, "hi")
    glyph(sc, "лидер", x0 + 8, y0 + 4, 2)
    icon(sc, key, x0 + 8, y0 + 20, 1)
    letters(sc, name, x0 + 36, y0 + 4, "text", 16, col=GOLD, jitter=1, seed=4)
    fx_line(sc, x0 + 36, y0 + 24, line)


def larvae_drop(sc, cx, by, n=2):
    """New larvae under the Queen, still wet, a glisten on them."""
    for j in range(n):
        lv = SH.larva("idle", 0.75)
        x, y = cx - 30 + j * 26, by + 4 + (j % 2) * 3
        sc.blit(lv, int(x - lv.ox), int(y - lv.oy), emit=False)
        sc.rgb[int(y - 6), int(x - 3):int(x)] = hexc("#f4ffe0")


def death(sc, x, by, seed=1, traits=(), egg=False):
    """A creature dying: on its back, legs curled, a splash of ichor round it; by the Queen's Heart of the swarm
    an egg left glowing in the splash."""
    from swarm_menus import flip_dead
    rnd = np.random.RandomState(seed)
    for _ in range(14):                                                      # the splash
        a, r = rnd.uniform(0, 2 * np.pi), rnd.uniform(4, 20)
        sx, sy = int(x + np.cos(a) * r * 1.4), int(by + np.sin(a) * r * 0.45)
        s_ = rnd.randint(1, 4)
        sc.rgb[sy:sy + s_, sx:sx + s_ + 1] = hexc("#8aa020") * rnd.uniform(0.7, 1.1)
    body = flip_dead(SH.bug(traits, "idle", 0.9, seed), 0.3)
    bottom = np.nonzero(body.a.any(axis=1))[0].max()
    sc.blit(body, int(x - body.ox), int(by - bottom), emit=False)
    if egg:
        ex, ey = x + 22, by - 4
        sc.glow(ex, ey, 10, hexc("#e8f070"), 0.5)
        e = ((sc.xx - ex) / 4.0) ** 2 + ((sc.yy - ey) / 5.5) ** 2
        sc.rgb[e <= 1.3] = UI.OUTL
        sc.rgb[e <= 1] = hexc("#e8f0b0")
        sc.rgb[(e <= 1) & (sc.xx > ex) & (sc.yy > ey)] = hexc("#b8c870")
        sc.rgb[int(ey - 3), int(ex - 2)] = hexc("#ffffff")


def moments():
    import battle as BT
    sc = SH.battle_hud(ret=True, pops=False)
    gp = BT.LAST["gpos"]
    qx, qy = BT.X0 + 15.6 * BT.CW, BT.Y0 + 8.4 * BT.CH
    import swarm1 as W
    qtop = ST.top_of(W.queen(0.0, "attack", k=0.92), qy)
    leader_pop(sc, "Кладка", "{каждые:3} → {личинка:×2}", "clutch", qx + 10, qtop - 18)
    larvae_drop(sc, int(qx - 70), int(qy + 6))
    death(sc, 728, 408, seed=11, traits=("horn",), egg=True)
    death(sc, 796, 128, seed=12, traits=("wings",))
    sx, sy, sspr = gp[("Страж", 5, 6)]                                       # the swarm's blows on the golems
    number(sc, sx + 40, ST.top_of(sspr, sy) - 6, "14!", "crit")
    number(sc, sx + 60, ST.top_of(sspr, sy) + 34, "3", "hit")
    mx, my, mspr = gp[("Мудрец", 5, 0)]
    number(sc, mx + 60, ST.top_of(mspr, my) + 40, "2", "poison")
    hx, hy, hspr = gp[("Горн", 6, 2)]
    number(sc, hx + 30, ST.top_of(hspr, hy) - 8, "4", "psi")
    number(sc, hx + 70, ST.top_of(hspr, hy) + 30, "мимо", "miss")
    number(sc, 548, 380, "-6", "hurt")                                       # and the golems' on the swarm
    number(sc, 650, 108, "-9", "hurt")
    number(sc, 600, 250, "+2", "heal")
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_battle_moments.png"))
    print("swarm_battle_moments.png", img.size)


def end(win=True, frame=0, ret=False):
    """The battle's end: the field dimmed, a plate across it — ПОБЕДА between two wasps beating their wings, or
    ПОРАЖЕНИЕ grey between two dead."""
    from swarm_menus import flip_dead, dark_nest
    sc = SH.battle_hud(ret=True, pops=False)
    sc.rgb[34:] = sc.rgb[34:] * (0.5 if win else 0.35)
    if not win:
        dark_nest(sc, sc.yy >= 34, 0.6)
    cy = HH // 2 - 10
    sc.rgb[cy - 64:cy + 64, :] = sc.rgb[cy - 64:cy + 64, :] * 0.6
    x0, x1 = WW // 2 - 180, WW // 2 + 180
    UI.plate(sc, x0, cy - 38, x1, cy + 32, antennae=True)
    if not win:
        sc.rgb[cy - 38:cy + 33, x0:x1 + 1] = sc.rgb[cy - 38:cy + 33, x0:x1 + 1] * 0.7
    text = "ПОБЕДА" if win else "ПОРАЖЕНИЕ"
    tw = UI.text_width(text, "title", 24)
    if win:
        letters(sc, text, WW // 2 - tw // 2, cy - 16, "title", 24, col=(176, 244, 70), col2=(70, 150, 50), jitter=1,
                drips=3, hairs=4, seed=9)
        for side in (-1, 1):                                                 # two wasps beating their wings
            pose = "attack" if (frame // 2) % 2 else "idle"
            b = SH.bug(("wings", "stinger"), pose, 1.6, 31 + (side > 0))
            if side > 0:                                                     # both face the plate
                f = b.flipped()
                f.ox, f.oy = b.w - 1 - b.ox, b.oy
                b = f
            bx = WW // 2 + side * 222
            SH.put(sc, b, bx, cy + 26 + (1 if (frame // 2) % 2 else 0), 16)
        sub = "Литейщик разбит · 7 големов · {биомасса:+9}"
    else:
        letters(sc, text, WW // 2 - tw // 2, cy - 16, "title", 24, col=(176, 178, 186), col2=(56, 58, 68), jitter=1,
                seed=9)
        for side in (-1, 1):
            b = flip_dead(SH.bug((), "idle", 1.2, 41 + (side > 0)))
            bottom = np.nonzero(b.a.any(axis=1))[0].max()
            sc.blit(b, int(WW // 2 + side * 232 - b.ox), int(cy + 26 - bottom), emit=False)
        sub = "Зодчий устоял · ему оставалось 22"
    w, _ = fx_line(sc, 0, 0, sub, draw=False)
    fx_line(sc, WW // 2 - w // 2, cy + 44, sub)
    letters(sc, "щелчок — дальше", WW // 2, cy + 70, "text", 16, col=MUTED, align="center")
    if ret:
        return sc
    name = "swarm_battle_end.png" if win else "swarm_battle_end_defeat.png"
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)


if __name__ == "__main__":
    moments()
    end(True)
    end(False)
