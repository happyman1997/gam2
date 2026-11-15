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
from kit import hexc as _hexc
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


LEADER_MOMENT = {   # the leader's ability firing, as the swarm sees it: (name, line, icon, the tug)
    "Разум улья": ("Захват разума", "{каждые:6} → {захват} {цель} {полрана}", "m_psi_leash", 0.62),
    "Пожиратель": ("Рост", "{тело:2} → {рост}", "pozh", 0.58),
    "Чума": ("Заражение", "{пробой} → {заражение}", "m_parasitoid", 0.56),
}


def leader_moments(name, ret=False):
    """The battle with each of the other leaders, the swarm's HUD over it: the leader's health and crown, its
    ability popping up in its wax cell, and what the ability does on the field — the Mind seizes a Mechanic
    (violet, its time in pips, a thread of thought to it from across the field), the Devourer grows a step (a
    red flare, the growth's stones, his health jumping), the Plague's eggs ripen in a Forge's firebox and a grub
    crawls out of the grate."""
    import battle as BT
    import swarm_leaders as SL
    import swarm_abilities as SA
    sc, count, ng = BT.build(name)
    UI.WOBBLE[0] = 1.0
    SH.HOVER.clear()
    gp = BT.LAST["gpos"]
    lx, ly, lspr = BT.LAST["lead"]
    if name == "Пожиратель":
        gx, gy = BT.X0 + 6.5 * BT.CW + 16, BT.Y0 + (6 + 3 * 0.72) * BT.CH
        qx, qy = gx + 150, gy + 14
        qspr = SL.build("Пожиратель", "attack", 1.0, stage=2)
    else:
        qx, qy = BT.X0 + 15.6 * BT.CW, BT.Y0 + 8.4 * BT.CH
        qspr = SL.build(name, "idle", 1.0)
    qtop = ST.top_of(qspr, qy)
    ab, line, key, share = LEADER_MOMENT[name]
    # both leaders' health over them, the crown by it
    lit = {"Разум улья": 6, "Пожиратель": 9, "Чума": 5}[name]
    UI.meter(sc, qx - 46, qtop - 12, qx + 46, 7, 10, lit, "#c04a3a")
    glyph(sc, "лидер", qx - 64, qtop - 14, 2)
    ltop = ST.top_of(lspr, ly)
    UI.meter(sc, lx - 40, ltop - 12, lx + 40, 7, 10, 6, "#d08a3a")
    glyph(sc, "лидер", lx - 58, ltop - 14, 2)
    sx, sy, sspr = gp[("Страж", 5, 6)]
    if name == "Разум улья":
        mx, my, mspr = gp[("Механик", 4, 12)]                             # seized
        ST.on_body(sc, mspr, mx, my, "captured", seed=2)
        mtop = ST.top_of(mspr, my)
        sc.glow(mx, my - 20, 34, hexc("#b070ff"), 0.35)
        for r in (22, 34):
            SA.ring(sc, mx, my + 2, r, r * 0.3, SA.PHERO, 0.6)
        ST.glyph(sc, "captured", mx - 8, mtop - 12)
        ST.pips(sc, mx + 10, mtop - 8, 2, of=2)
        SA.thread(sc, (qx - 14, qtop + 6), (mx + 6, mtop + 4), sag=-60, k=0.85)
        leader_pop(sc, ab, line, key, qx - 40, qtop - 22)
        number(sc, sx + 40, ST.top_of(sspr, sy) - 6, "5", "psi")
        number(sc, mx + 40, mtop + 6, "мимо", "miss")
    elif name == "Пожиратель":
        sc.glow(qx + 20, qy - 30, 90, hexc("#ff4a30"), 0.3)               # the growth: a red flare
        for k_ in range(2):                                              # its two steps a battle, both taken now
            UI.gem(sc, qx - 18 + k_ * 16, qtop - 26, 6, 6, "eat")
        for k_ in range(2):                                              # bodies toward the next: none yet
            UI.gem(sc, qx + 22 + k_ * 10, qtop - 26, 3.5, 4.5, "dim")
        leader_pop(sc, ab, line, key, qx + 40, qtop - 40)
        number(sc, qx + 120, qtop + 10, "+16", "heal")
        number(sc, sx + 10, ST.top_of(sspr, sy) - 30, "16!", "crit")
        number(sc, 640, 140, "-7", "hurt")
    else:
        hx, hy, hspr = gp[("Механик", 3, 9)]                             # the eggs ripening in its firebox
        ST.on_body(sc, hspr, hx, hy, "infected", seed=3)
        htop = ST.top_of(hspr, hy)
        ST.glyph(sc, "infected", hx - 8, htop - 12)
        for k_ in range(3):                                              # turns to the next grub: the last one now
            UI.gem(sc, hx + 8 + k_ * 9, htop - 7, 3.5, 4.5, "ok")
        SA.splat(sc, hx - 30, hy + 8, 9, col=hexc("#5a4030"), k=0.6)
        lv = SL.build("личинка", "attack", 1.6)
        BT.shadow(sc, hx - 36, hy + 8, 16, 4)
        BT.put(sc, lv, hx - 36, hy + 8, mirror=True)                     # out of the grate, crawling off
        for k_ in range(5):                                              # its slime trail back to the grate
            sc.rgb[int(hy + 8), int(hx - 24 + k_ * 4):int(hx - 22 + k_ * 4)] = hexc("#8aa040")
        sc.glow(hx - 2, hy - 18, 16, hexc("#9ae030"), 0.4)
        leader_pop(sc, ab, line, key, qx - 40, qtop - 22)
        number(sc, sx + 40, ST.top_of(sspr, sy) - 6, "3", "hit")
        number(sc, lx + 30, ltop - 30, "2", "poison")
    SH.battle_wing(sc, count, ng, False, share=share, turn=6)
    if ret:
        return sc
    fn = f"swarm_battle_moments_{SH.LEADER_EN[name]}.png"
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(fn))
    print(fn, img.size)


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
    for n_ in ("Разум улья", "Пожиратель", "Чума"):
        leader_moments(n_)
    moments()
    end(True)
    end(False)
