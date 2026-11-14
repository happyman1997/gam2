"""Artifacts in the Foundry's interface. They are always passive and the army's, not a golem's, so they sit on the
beam itself, left of the title: five round brass-rimmed sockets, an artifact in each (an empty one — a dark
well). One that has awoken (its condition met — it grew stronger) has a gold rim and a star. Under the mouse an
artifact opens its tooltip: what it does in glyphs, its awakening (a bar filled with molten metal toward its
condition), and its hidden pair — «?» until the two have met once. In battle, when one fires, its socket flares
and the artifact pops out under the beam, with a line to the golem it touched.

    python3 tools/sprites/artifacts_ui.py   -> out/foundry_artifacts.png, out/foundry_artifact_battle.png
"""
import numpy as np
from kit import hexc
import foundry_ui as FU
import foundry_hud as FH
import icons_drawn as D
from foundry_hud import letters, H, SU, INK, MUTED, PALE, GOLD, S, out

ARTIFACTS = {   # key: (name, kind, lines, awakening (text, have, need), pair)
    "banner": ("Знамя двух ветров", "широкий", ["центр: {атака} +2", "фланги: {броня:+2}"],
               ("{убийство} центром", 7, 10), None),
    "chalice": ("Кровавая чаша", "широкий", ["{убийство} → {свой} {радиус:1} {ремонт:3}"], ("{ремонт} 30", 30, 30), None),
    "anvil": ("Тяжёлая наковальня", "широкий", ["{урон:+50%} · ходит последним"], None, ("bell", True)),
    "bell": ("Колокол тревоги", "широкий", ["{гибель_своя} → {свой} {урон:+1}"], None, ("anvil", True)),
    "hourglass": ("Песочные часы", "редкий", ["2 хода без {атака} → {урон:×2}"], ("бой без потерь", 0, 1), ("?", False)),
}


def art_icon(sc, key, x, y, z=1):
    rgba = np.repeat(np.repeat(D.ART[key](), z, 0), z, 1)
    m = rgba[..., 3] > 0
    sc.rgb[y:y + rgba.shape[0], x:x + rgba.shape[1]][m] = rgba[..., :3][m]


def socket(sc, cx, cy, key=None, state="normal", phase=None):
    """A round socket in the beam: a brass rim (gold and glowing when awoken, red-hot when firing), a dark well,
    the artifact in it."""
    X, Y = sc.xx - cx, sc.yy - cy
    d = np.hypot(X, Y)
    if state in ("awake", "fire"):
        sc.glow(cx, cy, 16, hexc("#ffb040" if state == "fire" else "#f0c878"), 0.5 if state == "fire" else 0.3)
    rim = d <= 11
    sc.rgb[d <= 12] = SU.OUTL
    ramp = {"awake": FU.BRASSR, "fire": ("#7a2208", "#c2500e", "#f08a2a", "#ffd890", "#fff3c0")}.get(state, FU.BRASSR)
    FU._bands(sc, rim, ramp, 0.75 - (X + Y) / 30.0 if state != "normal" else 0.55 - (X + Y) / 34.0)
    sc.rgb[d <= 9] = SU.OUTL
    sc.rgb[d <= 8.4] = hexc("#0c0b0e")
    if key:
        art_icon(sc, key, cx - 8, cy - 8, 1)
    if state == "awake" and phase is not None:                                # a glint running round the gold rim
        a = phase * 2 * np.pi
        gx_, gy_ = int(cx + np.cos(a) * 10), int(cy + np.sin(a) * 10)
        sc.rgb[gy_ - 1:gy_ + 2, gx_ - 1:gx_ + 2] = hexc("#fff4c8")
    if state == "awake":                                                      # the awakened star
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)):
            sc.rgb[cy - 10 + dy, cx + 9 + dx] = hexc("#fff4c8")


def rack(sc, x0=88, cy=21, items=(("banner", "awake"), ("chalice", "normal"), ("anvil", "normal"), ("bell", "normal"),
                                  (None, "normal")), fire=None, phase=None):
    for j, (key, st) in enumerate(items):
        socket(sc, x0 + j * 23, cy, key, "fire" if key and key == fire else st, phase)
    return [(key, x0 + j * 23, cy) for j, (key, _) in enumerate(items)]


def tooltip(sc, key, x0, y0, w=300):
    """An artifact under the mouse: large, its name and kind, its lines, its awakening, its pair."""
    nm, kind, lines, wake, pair = ARTIFACTS[key]
    h = 64 + 26 * len(lines) + (60 if wake else 0) + (48 if pair else 0)
    FU.cell(sc, x0, y0, x0 + w, y0 + h, "hi")
    FU.cell(sc, x0 + 10, y0 + 10, x0 + 52, y0 + 52, "locked")
    art_icon(sc, key, x0 + 15, y0 + 15, 2)
    letters(sc, nm, x0 + 62, y0 + 12, "text", 16, col=GOLD)
    letters(sc, f"артефакт · {kind} · всегда", x0 + 62, y0 + 32, "text", 16, col=MUTED)
    y = y0 + 62
    for ln in lines:
        H.fx_line(sc, x0 + 12, y, ln)
        y += 26
    if wake:
        text, have, need = wake
        done = have >= need
        letters(sc, "пробудился" if done else "пробуждение", x0 + 12, y + 2, "text", 16, col=GOLD if done else MUTED)
        H.fx_line(sc, x0 + 130, y, text)
        bx0, bx1 = x0 + 12, x0 + w - 60
        sc.rgb[y + 26:y + 34, bx0:bx1] = hexc("#08070a")
        f = int(bx0 + (bx1 - bx0) * min(1, have / need))
        if f > bx0:
            t = np.clip((sc.yy[y + 26:y + 34, bx0:f] - (y + 26)) / 8.0, 0, 1)[..., None]
            sc.rgb[y + 26:y + 34, bx0:f] = hexc("#ffd890") * (1 - t) + hexc("#c2500e") * t
        letters(sc, f"{have}/{need}", x0 + w - 12, y + 22, "text", 16, col=INK, align="right")
        y += 46
    if pair:
        other, known = pair
        for k in range(3):                                                    # a chain link: the pair
            sc.rgb[y + 6:y + 12, x0 + 14 + k * 6:x0 + 18 + k * 6] = hexc("#a0782c" if known else "#4a4850")
        if known:
            letters(sc, f"пара: {ARTIFACTS[other][0]}", x0 + 40, y, "text", 16, col=GOLD)
            letters(sc, "вместе: гибель своего → его удар ×2", x0 + 12, y + 20, "text", 16, col=INK)
        else:
            letters(sc, "у него есть пара: ???", x0 + 40, y, "text", 16, col=PALE)
            letters(sc, "откроется, когда встретятся", x0 + 12, y + 20, "text", 16, col=MUTED)
    return x0, y0, x0 + w, y0 + h


def workshop_view():
    """The workshop with its artifacts on the beam and one under the mouse."""
    sc = FH.workshop(ret=True)
    pos = rack(sc)
    key, cx, cy = pos[0]
    tooltip(sc, "banner", 74, 44)
    H.cursor(sc, cx + 2, cy + 4)
    img = sc.image(S)
    img.save(out("foundry_artifacts.png"))
    print("foundry_artifacts.png", img.size)
    sc = FH.workshop(ret=True)
    rack(sc)
    tooltip(sc, "anvil", 120, 44)
    H.cursor(sc, pos[2][1] + 2, cy + 4)
    img = sc.image(S)
    img.save(out("foundry_artifacts_pair.png"))
    print("foundry_artifacts_pair.png", img.size)


def battle_view():
    """In battle: the Blood Chalice fires — a kill by the Guard heals its neighbours: the artifact pops out under
    the beam in a red-hot socket with its line, a thin line runs to the Guard, green numbers over the healed."""
    import battle as BT
    import swarm_status as ST
    sc = FH.battle_view("run", ret=True)
    gp = FH._FIELD["gpos"]
    x, y = 30, 40
    socket(sc, x + 14, y + 16, "chalice", "fire")
    FU.cell(sc, x + 32, y, x + 300, y + 44, "hi")
    letters(sc, "Кровавая чаша", x + 42, y + 3, "text", 16, col=GOLD)
    H.fx_line(sc, x + 42, y + 21, "{убийство} → {ремонт:3} рядом")
    gx, gy, gspr = gp[("Страж", 5, 6)]
    top = ST.top_of(gspr, gy)
    for k in range(0, 60):                                                    # the line to the golem it touched
        t = k / 59
        px_, py_ = int(x + 14 + (gx - x - 14) * t), int(y + 32 + (top - 10 - y - 32) * t)
        if k % 3 != 2:
            sc.rgb[py_, px_] = hexc("#f0c878")
    for who in (("Механик", 3, 9), ("Горн", 6, 11)):
        if who in gp:
            hx, hy, hspr = gp[who]
            letters(sc, "+3", hx, ST.top_of(hspr, hy) - 26, "title", 16, col=(150, 240, 130), col2=(40, 110, 40),
                    align="center")
    img = sc.image(S)
    img.save(out("foundry_artifact_battle.png"))
    print("foundry_artifact_battle.png", img.size)


if __name__ == "__main__":
    workshop_view()
    battle_view()
