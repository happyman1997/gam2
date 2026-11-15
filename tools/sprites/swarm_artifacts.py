"""Artifacts in the swarm's interface. The same artifacts as the Foundry's — always passive, the army's — but they
sit in the wing as the swarm keeps things: each sealed in a wax cell under a drop of amber, five cells in a row
after the title (an empty one — a dark open cell). One that has awoken has a gold rim, a glint running round it and
a star; one firing in battle flares acid. Under the mouse an artifact opens its tooltip: what it does in glyphs, its
awakening (a groove filling with ichor toward its condition), and its hidden pair — a silk thread to «?» until the
two have met once. In battle, when one fires, its cell pops out under the wing with its line, and a silk thread
runs to the creature it touched.

    python3 tools/sprites/swarm_artifacts.py   -> out/swarm_artifacts.png, out/swarm_artifacts_pair.png,
                                                  out/swarm_artifact_battle.png
"""
import numpy as np
from kit import hexc
import swarm_ui as UI
import swarm_hud as SH
import icons_drawn as D
from swarm_hud import letters, fx_line, cursor, INK, MUTED, GOLD, PALE, S, out

ARTIFACTS = {   # key: (name, kind, lines, awakening (text, have, need), pair) — the swarm's wording
    "banner": ("Знамя двух ветров", "широкий", ["центр: {атака} +2", "фланги: {броня:+2}"],
               ("{убийство} центром", 7, 10), None),
    "chalice": ("Кровавая чаша", "широкий", ["{убийство} → {свой} {радиус:1} {лечение:3}"], ("{лечение} 30", 30, 30), None),
    "anvil": ("Тяжёлая наковальня", "широкий", ["{урон:+50%} · ходит последним"], None, ("bell", True)),
    "bell": ("Колокол тревоги", "широкий", ["{гибель_своя} → {свой} {урон:+1}"], None, ("anvil", True)),
    "hourglass": ("Песочные часы", "редкий", ["2 хода без {атака} → {урон:×2}"], ("бой без потерь", 0, 1), ("?", False)),
}
ICHOR = ("#3a6a10", "#6aa020", "#a8e040", "#e0ff90")


def art_icon(sc, key, x, y, z=1):
    rgba = np.repeat(np.repeat(D.ART[key](), z, 0), z, 1)
    m = rgba[..., 3] > 0
    sc.rgb[y:y + rgba.shape[0], x:x + rgba.shape[1]][m] = rgba[..., :3][m]


def cell(sc, cx, cy, key=None, state="normal", phase=None):
    """A wax cell in the wing, the artifact sealed in it under amber: a wax rim (gold when awoken, acid when
    firing), the amber glowing faintly over the thing inside; an empty one dark and open."""
    hx = lambda r: SH.hexmask(sc, cx, cy, r)
    if state == "awake":
        sc.glow(cx, cy, 16, hexc("#f0c878"), 0.3)
    elif state == "fire":
        sc.glow(cx, cy, 20, hexc("#b0f040"), 0.55)
    sc.rgb[hx(13)] = UI.OUTL
    rim = {"awake": ("#a07018", "#f0c050"), "fire": ("#5a9a18", "#d8ff70")}.get(state, ("#5e3c16", "#a07030"))
    ring = hx(12) & ~hx(9)
    sc.rgb[ring] = hexc(rim[0])
    sc.rgb[ring & ((sc.xx - cx) + (sc.yy - cy) * 1.4 < -4)] = hexc(rim[1])
    sc.rgb[hx(9)] = UI.OUTL
    if key:
        t = np.clip((sc.yy - (cy - 8)) / 16.0, 0, 1)[..., None]
        amber = hexc("#5a3008") * (1 - t) + hexc("#8a5010") * t
        m = hx(8)
        sc.rgb[m] = amber[m]
        art_icon(sc, key, cx - 8, cy - 8, 1)
        sc.rgb[m] = sc.rgb[m] * 0.8 + hexc("#e8a030") * 0.2                # under the amber
        sc.rgb[cy - 6, cx - 4:cx - 1] = hexc("#ffe8a0")                    # the amber's glint
        sc.rgb[cy - 5, cx - 5] = hexc("#ffe8a0")
    else:
        sc.rgb[hx(8)] = hexc("#0c0a0e")
    if state == "awake":
        if phase is not None:                                              # a glint running round the gold rim
            a = phase * 2 * np.pi
            gx, gy = int(cx + np.cos(a) * 10.5), int(cy + np.sin(a) * 10.5)
            sc.rgb[gy - 1:gy + 2, gx - 1:gx + 2] = hexc("#fff4c8")
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)):         # the awakened star
            sc.rgb[cy - 11 + dy, cx + 10 + dx] = hexc("#fff4c8")


def rack(sc, x0=318, cy=22, items=(("banner", "awake"), ("chalice", "normal"), ("anvil", "normal"), ("bell", "normal"),
                                   (None, "normal")), fire=None, phase=None):
    for j, (key, st) in enumerate(items):
        cell(sc, x0 + j * 26, cy, key, "fire" if key and key == fire else st, phase)
    return [(key, x0 + j * 26, cy) for j, (key, _) in enumerate(items)]


def tooltip(sc, key, x0, y0, w=310):
    """An artifact under the mouse: large, its name and kind, its lines, its awakening, its pair."""
    nm, kind, lines, wake, pair = ARTIFACTS[key]
    h = 64 + 26 * len(lines) + (60 if wake else 0) + (48 if pair else 0)
    UI.cell(sc, x0, y0, x0 + w, y0 + h, "hi")
    UI.cell(sc, x0 + 10, y0 + 10, x0 + 52, y0 + 52, "normal")
    art_icon(sc, key, x0 + 15, y0 + 15, 2)
    letters(sc, nm, x0 + 62, y0 + 12, "text", 16, col=GOLD, jitter=1, seed=3)
    letters(sc, f"артефакт · {kind} · всегда", x0 + 62, y0 + 32, "text", 16, col=MUTED)
    y = y0 + 62
    for ln in lines:
        fx_line(sc, x0 + 12, y, ln)
        y += 26
    if wake:
        text, have, need = wake
        done = have >= need
        letters(sc, "пробудился" if done else "пробуждение", x0 + 12, y + 2, "text", 16, col=GOLD if done else MUTED)
        fx_line(sc, x0 + 130, y, text)
        bx0, bx1 = x0 + 12, x0 + w - 60                                    # a groove filling with ichor
        sc.rgb[y + 25:y + 35, bx0 - 1:bx1 + 1] = hexc("#5e3c16")
        sc.rgb[y + 26:y + 34, bx0:bx1] = hexc("#0e0a10")
        f = int(bx0 + (bx1 - bx0) * min(1, have / need))
        if f > bx0:
            t = np.clip((sc.yy[y + 26:y + 34, bx0:f] - (y + 26)) / 8.0, 0, 1)[..., None]
            sc.rgb[y + 26:y + 34, bx0:f] = hexc(ICHOR[3]) * (1 - t) + hexc(ICHOR[1]) * t
            for k in range(bx0 + 6, f - 4, 14):
                sc.rgb[y + 28, k] = hexc("#f4ffd0")
        letters(sc, f"{have}/{need}", x0 + w - 12, y + 22, "text", 16, col=INK, align="right")
        y += 46
    if pair:
        other, known = pair
        UI.silk(sc, (x0 + 12, y + 9), (x0 + 34, y + 9), sag=3, col="#e8e0c8" if known else "#6a6470", k=0.9)
        for xx in (x0 + 12, x0 + 34):
            sc.rgb[y + 7:y + 12, xx - 2:xx + 3] = hexc("#e8e0c8" if known else "#6a6470")
        if known:
            letters(sc, f"пара: {ARTIFACTS[other][0]}", x0 + 42, y, "text", 16, col=GOLD)
            letters(sc, "вместе: гибель своего → его удар ×2", x0 + 12, y + 20, "text", 16, col=INK)
        else:
            letters(sc, "у него есть пара: ???", x0 + 42, y, "text", 16, col=PALE)
            letters(sc, "откроется, когда встретятся", x0 + 12, y + 20, "text", 16, col=MUTED)
    return x0, y0, x0 + w, y0 + h


def brood_view():
    """The brood with its artifacts in the wing and one under the mouse."""
    sc = SH.brood("plain", ret=True)
    pos = rack(sc)
    _, cx, cy = pos[0]
    tooltip(sc, "banner", 300, 44)
    cursor(sc, cx + 2, cy + 4)
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_artifacts.png"))
    print("swarm_artifacts.png", img.size)
    sc = SH.brood("plain", ret=True)
    rack(sc)
    tooltip(sc, "anvil", 352, 44)
    cursor(sc, pos[2][1] + 2, cy + 4)
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_artifacts_pair.png"))
    print("swarm_artifacts_pair.png", img.size)


def battle_view():
    """In battle: the Blood Chalice fires — a kill by a horned ant heals the ones around it: the cell pops out
    under the wing flaring acid with its line, a silk thread runs to the ant, pale green numbers over the healed."""
    import swarm_moments as M
    sc = SH.battle_hud(ret=True)
    x, y = 30, 44
    cell(sc, x + 14, y + 18, "chalice", "fire")
    UI.cell(sc, x + 32, y, x + 312, y + 44, "hi")
    letters(sc, "Кровавая чаша", x + 42, y + 3, "text", 16, col=GOLD, jitter=1, seed=2)
    fx_line(sc, x + 42, y + 21, "{убийство} → {лечение:3} рядом")
    tx, ty = 486, 300                                                    # the ant that killed
    sc.glow(tx, ty - 10, 16, hexc("#b0f040"), 0.4)
    UI.silk(sc, (x + 14, y + 34), (tx, ty - 22), sag=30, col="#d8ffa0", k=0.85)
    for (hx, hy) in ((446, 280), (530, 300), (476, 352)):
        M.number(sc, hx, hy - 30, "+3", "heal")
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_artifact_battle.png"))
    print("swarm_artifact_battle.png", img.size)


if __name__ == "__main__":
    brood_view()
    battle_view()
