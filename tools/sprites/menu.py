"""The game's own screens before a run: the main menu and the choice of class.

  main menu  — the forge at night: a great furnace mouth in the middle with pixelfx's fire in it, a Guard standing
               before it, and on the right the wall broken open — the swarm's green glow and its bugs coming
               through; the game's name goes on an empty cast cartouche at the top (the name isn't chosen yet —
               it says so); the menu is the Foundry's console: the big lever for a new run, push-buttons for the rest;
  class pick — the screen split down the middle: the Foundry's half in forge iron (its leader in a furnace arch,
               a golem by it, «мало, но каждый силён»), the swarm's in its own chitin and wax (the Queen, its
               brood, «масса и селекция»); the chosen half bright and the other dimmed; each its own button.

    python3 tools/sprites/menu.py   -> out/menu_main.png, out/menu_class.png
"""
import numpy as np
from kit import hexc
import foundry_ui as FU
import foundry_hud as FH
import swarm_ui as UI
import swarm_hud as SH
from foundry_hud import letters, H, SU, INK, MUTED, PALE, GOLD, WW, HH, S, out, action, leader_sprite
import frames as F
import pxfx


def furnace(sc, ax, ay, ar, floor, frame=0, hot=True):
    """A furnace mouth: an arch of iron with rivets, its depth dark, pixelfx's fire in it."""
    X, Y = sc.xx, sc.yy
    arch = ((((X - ax) / ar) ** 2 + ((Y - ay) / ar) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar) & (Y > ay) & (Y < floor))
    t = np.clip((Y - (ay - ar)) / (floor - ay + ar), 0, 1)
    fire = hexc("#1e0a06")[None, None, :] * (1 - t[..., None]) + hexc("#7a2410")[None, None, :] * t[..., None]
    sc.rgb[arch] = fire[arch] if hot else hexc("#0e0d10")
    inner = ((((X - ax) / (ar - 4)) ** 2 + ((Y - ay) / (ar - 4)) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar - 4) & (Y > ay) & (Y < floor))
    if hot:
        frames_, meta = pxfx.load("forge-fire")
        before = sc.rgb.copy()
        for dx in (-ar * 0.45, ar * 0.4):
            pxfx.blend(sc, frames_[(frame + (dx > 0) * 9) % len(frames_)], ax + dx, floor, meta["pivot"])
        sc.rgb[~inner] = before[~inner]
    sc.rgb[arch & ~inner] = hexc("#b8904a") if hot else hexc("#4a4850")
    for kk in range(-5, 6):
        a_ = np.pi * (0.5 + kk / 12)
        FU.rivet(sc, ax - np.cos(a_) * (ar + 6), ay - np.sin(a_) * (ar + 6))


def main_menu(frame=0, ret=False):
    sc = FH.screen(101)
    sc.glow(400, 330, 260, hexc("#ff7a2a"), 0.28)
    furnace(sc, 400, 250, 140, 410, frame)
    # the wall broken open on the right, the swarm's glow through it
    X, Y = sc.xx, sc.yy
    hole = ((X - 800) / 120.0) ** 2 + ((Y - 300) / 150.0) ** 2 + 0.25 * np.sin(Y / 9.0) * np.cos(X / 7.0) <= 1
    sc.rgb[hole] = sc.rgb[hole] * 0.2 + hexc("#1a2a10") * 0.8
    sc.glow(800, 300, 140, hexc("#7ac83a"), 0.3)
    rim = hole & ~(np.roll(hole, 3, 0) & np.roll(hole, -3, 0) & np.roll(hole, 3, 1) & np.roll(hole, -3, 1))
    sc.rgb[rim] = hexc("#3a3436")
    for j, (bx, by, tr, kk) in enumerate(((800, 250, ("wings",), 1.4), (850, 330, (), 1.3), (770, 320, ("horn",), 1.6),
                                         (830, 400, ("stinger",), 1.7), (740, 420, ("acid",), 1.8), (690, 380, (), 1.9),
                                         (880, 430, ("scythes",), 1.5), (660, 300, ("stinger",), 1.6))):
        SH.put(sc, SH.bug(tr, "attack" if j % 3 == 0 else "idle", kk, 300 + j), bx, by, 10)   # coming through
    g = F.build("Страж", "idle", k=F.FRAMES["Страж"][0] * 1.5)                # a Guard standing before the fire
    sc.blit(g, int(560 - g.ox), int(420 - g.oy))
    sc.rgb[410:416, 220:620] = hexc("#24222a")
    # the cartouche for the game's name — empty until it has one
    FU.nameplate(sc, 250, 26, 710, 86, "", hot=False)
    letters(sc, "название игры", 480, 48, "text", 16, col=(150, 130, 100), align="center")
    # the console: the menu
    FU.sill(sc, 440)
    action(sc, 24, 448, 340, 520, "НОВЫЙ ПОХОД", "hot", big=True)
    for j, (t, kind) in enumerate((("Продолжить · бой 5", "steel"), ("Настройки", "steel"), ("Об игре", "steel"),
                                   ("Выход", "dull"))):
        x0 = 360 + (j % 2) * 290
        y0 = 452 + (j // 2) * 40
        action(sc, x0, y0, x0 + 270, y0 + 34, t, kind)
    letters(sc, "версия 0.1", WW - 12, HH - 22, "text", 16, col=PALE, align="right")
    if ret:
        return sc
    img = sc.image(S)
    img.save(out("menu_main.png"))
    print("menu_main.png", img.size)


def class_pick(chosen="foundry", ret=False):
    sc = FH.screen(103)
    nest = UI.nest(WW, HH, 7)
    right = sc.xx >= WW // 2
    sc.rgb[right] = nest.rgb[right]
    # the seam: a jagged tear between iron and wax
    for y in range(HH):
        x = WW // 2 + int(4 * np.sin(y / 11.0) + 3 * np.sin(y / 3.7))
        sc.rgb[y, x - 1:x + 2] = SU.OUTL
    FU.wing(sc, 0, 0, WW // 2, 44)
    UI.wing(sc, WW // 2, 0, WW, 44)
    tw = SU.text_width("КЛАСС", "title", 24)
    letters(sc, "КЛАСС", WW // 2 - tw // 2, 8, "title", 24, col=(232, 222, 206), col2=(120, 96, 70))
    # the Foundry's half
    FU.plate(sc, 16, 56, 462, 420, seed=31)
    furnace(sc, 239, 190, 96, 300, 0)
    spr = leader_sprite("colossus", 1.9)
    sc.blit(spr, int(239 - spr.ox), int(296 - spr.oy))
    for fr, x in (("Механик", 120), ("Орудие", 362)):
        g = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.62)
        sc.blit(g, int(x - g.ox), int(300 - g.oy))
    FU.cell(sc, 30, 312, 448, 410, "hi" if chosen == "foundry" else "normal")
    letters(sc, "ЛИТЕЙЩИК", 44, 320, "title", 16, col=(255, 210, 140), col2=(130, 90, 40))
    letters(sc, "мало, но каждый силён", 44, 344, "text", 16, col=INK)
    letters(sc, "големы из деталей · модули · ремонт", 44, 364, "text", 16, col=MUTED)
    letters(sc, "4 лидера", 44, 384, "text", 16, col=MUTED)
    # the swarm's half
    UI.plate(sc, 498, 56, 944, 420, antennae=True)
    q = SH.leader("Матка", "idle", 1.15)
    SH.put(sc, q, 760, 296, 30)
    for j, (tr, x, y) in enumerate(((("stinger",), 560, 300), (("wings",), 610, 280), ((), 900, 296),
                                    (("horn",), 870, 270), (("acid",), 590, 250))):
        SH.put(sc, SH.bug(tr, "idle", 0.8, 50 + j), x, y, 8)
    UI.cell(sc, 512, 312, 930, 410, "hi" if chosen == "swarm" else "normal")
    letters(sc, "РОЙ", 526, 320, "title", 16, col=(176, 244, 70), col2=(70, 150, 50), jitter=1, hairs=3)
    letters(sc, "масса и селекция", 526, 344, "text", 16, col=INK)
    letters(sc, "сотни особей · мутации · порода", 526, 364, "text", 16, col=MUTED)
    letters(sc, "4 лидера", 526, 384, "text", 16, col=MUTED)
    if chosen == "foundry":                                                   # the other half sinks back
        sc.rgb[right & (sc.yy > 44)] *= 0.55
    else:
        sc.rgb[~right & (sc.yy > 44)] *= 0.55
    FU.sill(sc, 440, None)
    UI.wing(sc, WW // 2, 440, WW, HH)
    action(sc, 24, 456, 300, 516, "ЛИТЕЙЩИК", "hot", big=True, heated=chosen == "foundry")
    SH.act_button(sc, 660, 456, 936, 516, "РОЙ", key=None, dim=chosen != "swarm")
    action(sc, 330, 470, 460, 506, "Назад", "steel")
    if ret:
        return sc
    img = sc.image(S)
    img.save(out("menu_class.png"))
    print("menu_class.png", img.size)


if __name__ == "__main__":
    main_menu()
    class_pick()
