"""The swarm's new screens moving (24 fps; loops where it says so), the same way as the Foundry's (ui_anim.py).

    python3 tools/sprites/swarm_anim.py settings|development|defeat|pause|artifacts|moments|battle_end|all
"""
import sys
import copy
import numpy as np
from PIL import Image
import pxfx
import swarm_ui as UI
import swarm_hud as SH
import swarm_menus as M
from ui_anim import out_back, overlay_in, FPS
from paths import out


def settings():
    """The mouse drags the interface's size from ×1 to ×2 — the amber drop slides along its groove (eased, a little
    overshoot), the window in the comb grows the interface with it; then a click on the vsync lantern, its light
    going out."""
    images = []
    seq = [0.0] * 6 + [out_back(t / 10) for t in range(1, 11)] + [1.0] * 6
    for i, v in enumerate(seq):
        sc = M.settings("screen", ret=True, anim={"scale": v, "vsync": True})
        images.append(sc.image(2).crop((400, 160, 1900, 760)))
        print(i, end=" ", flush=True)
    for i in range(10):
        sc = M.settings("screen", ret=True, anim={"scale": 1.0, "vsync": i < 3})
        images.append(sc.image(2).crop((400, 160, 1900, 760)))
    UI.WOBBLE[0] = 0.0
    pxfx.save_gif(images, out("swarm_settings_anim.gif"), FPS, half=True)
    print("\nswarm_settings_anim.gif", len(images))


def development(names=("Матка", "Разум улья", "Пожиратель", "Чума")):
    """Each leader's chamber alive, the growth under the mouse: royal jelly rising in the Queen's cell, psi rings
    spreading in the Mind's bubble, blood running off the Devourer's teeth, spores puffing off the Plague's
    puffball — loops of 24."""
    for name in names:
        images = []
        for i in range(24):
            sc = SH.development(name, frame=i, ret=True)
            images.append(sc.image(2))
            print(i, end=" ", flush=True)
        UI.WOBBLE[0] = 0.0
        fn = f"swarm_development_{SH.LEADER_EN[name]}_anim.gif"
        pxfx.save_gif(images, out(fn), 12, half=True)
        print("\n" + fn, len(images))


def defeat():
    """The dark nest: flakes of wax drifting down, the last larva twitching — a loop of 36."""
    images = []
    for i in range(36):
        sc = M.defeat(ret=True, anim={"frame": i})
        images.append(sc.image(2))
        print(i, end=" ", flush=True)
    UI.WOBBLE[0] = 0.0
    pxfx.save_gif(images, out("swarm_defeat_anim.gif"), 12, half=True)
    print("\nswarm_defeat_anim.gif", len(images))


def pause():
    """Pause over the battle: the plate dropping in."""
    base = SH.battle_hud(ret=True).image(2)
    final = M.pause(ret=True).image(2)
    UI.WOBBLE[0] = 0.0
    pxfx.save_gif(overlay_in(base, final, (660, 160, 1260, 924)), out("swarm_pause_anim.gif"), FPS, half=True)
    print("swarm_pause_anim.gif")


def artifacts():
    """The artifacts in the wing: a glint running round the awoken one's gold rim; then the Chalice fires — its
    cell flares acid and fades."""
    import swarm_artifacts as A
    base = SH.brood("plain", ret=True)
    images = []
    for i in range(36):
        sc = copy.deepcopy(base)
        fire = "chalice" if 18 <= i < 30 else None
        A.rack(sc, fire=fire, phase=(i % 18) / 18.0)
        images.append(sc.image(2).crop((0, 0, 1000, 100)))
    UI.WOBBLE[0] = 0.0
    pxfx.save_gif(images, out("swarm_artifacts_anim.gif"), FPS)
    print("swarm_artifacts_anim.gif", len(images))


def moments():
    """The swarm's numbers: each jumps up out of the target, hangs, drifts up and fades; the heavy «14!» lasts a
    little longer."""
    import battle as BT
    import swarm_status as ST
    import swarm_moments as SM
    import swarm1 as W
    sc0 = SH.battle_hud(ret=True, pops=False)
    gp = BT.LAST["gpos"]
    qx, qy = BT.X0 + 15.6 * BT.CW, BT.Y0 + 8.4 * BT.CH
    qtop = ST.top_of(W.queen(0.0, "attack", k=0.92), qy)
    SM.leader_pop(sc0, "Кладка", "{каждые:3} → {личинка:×2}", "clutch", qx + 10, qtop - 18)
    SM.larvae_drop(sc0, int(qx - 70), int(qy + 6))
    SM.death(sc0, 728, 408, seed=11, traits=("horn",), egg=True)
    sx, sy, ss = gp[("Страж", 5, 6)]
    mx, my, ms = gp[("Мудрец", 5, 0)]
    hx, hy, hs = gp[("Горн", 6, 2)]
    nums = [(sx + 40, ST.top_of(ss, sy) - 6, "14!", "crit", 0, 22), (sx + 60, ST.top_of(ss, sy) + 34, "3", "hit", 4, 16),
            (mx + 60, ST.top_of(ms, my) + 40, "2", "poison", 2, 16), (hx + 30, ST.top_of(hs, hy) - 8, "4", "psi", 6, 16),
            (hx + 70, ST.top_of(hs, hy) + 30, "мимо", "miss", 8, 16), (548, 380, "-6", "hurt", 10, 16),
            (650, 108, "-9", "hurt", 12, 16), (600, 250, "+2", "heal", 14, 16)]
    images = []
    for i in range(36):
        sc = copy.deepcopy(sc0)
        for x, y, t, kind, st, life in nums:
            age = i - st
            if age < 0 or age >= life:
                continue
            pop = out_back(min(1.0, age / 4))
            dy = int(round(-6 * pop - max(0, age - 8) * 0.8))
            before = sc.rgb.copy()
            SM.number(sc, x, int(y + dy + (1 - pop) * 6), t, kind)
            fade = 1.0 if age < life - 5 else (life - age) / 5.0
            sc.rgb[:] = before * (1 - fade) + sc.rgb * fade
        images.append(sc.image(2).crop((300, 60, 1600, 1000)))
        print(i, end=" ", flush=True)
    UI.WOBBLE[0] = 0.0
    pxfx.save_gif(images, out("swarm_battle_numbers.gif"), FPS, half=True)
    print("\nswarm_battle_numbers.gif", len(images))


def battle_end():
    """The battle's end: the field dims and the plate drops across it; then the two wasps beat their wings."""
    import swarm_moments as SM
    base = SH.battle_hud(ret=True, pops=False).image(2)
    final = SM.end(True, 0, ret=True).image(2)
    frames = overlay_in(base, final, (0, 380, 1920, 720))
    for i in range(16):
        frames.append(SM.end(True, i, ret=True).image(2))
        print(i, end=" ", flush=True)
    UI.WOBBLE[0] = 0.0
    pxfx.save_gif(frames, out("swarm_battle_end_anim.gif"), FPS, half=True)
    print("\nswarm_battle_end_anim.gif", len(frames))


def brood_eat():
    """The swarm's own correction, its main gesture (as dragging a module is the Foundry's): the mouse comes to the
    wasps' group, a left click — the last wasp's scale goes amber and is bitten, crumbs fly, the limit's
    centipede marks one more scale, the purse ticks up with a «+1»; a while later a right click gives it back."""
    import swarm_ui as U
    s0 = SH.brood("plain", ret=True, anim={"hover": 2, "bio": 34})
    s1 = SH.brood("plain", ret=True, anim={"hover": 2, "bio": 35, "eat": {2: 1}})
    x0, y0 = 12 + 2 * 232, 100                                           # the wasps' cell
    gx, gy = x0 + 88 + 2 * 14, y0 + 62                                   # its last scale
    hx, hy = x0 + 150, y0 + 40                                           # where the mouse rests
    start = (330, 330)
    images = []

    def frame(base, cur, press=False, gem=None, crumbs=0.0, pop=None):
        sc = copy.deepcopy(base)
        if gem:
            U.gem(sc, gx, gy, 5.5, 7.0, "eat", bite=gem == "bite")
        if crumbs:
            rnd = np.random.RandomState(3)
            for k in range(7):
                a = rnd.uniform(-2.6, -0.5)
                r = 4 + crumbs * rnd.uniform(10, 18)
                px_, py_ = int(gx + 3 + np.cos(a) * r), int(gy - 4 + np.sin(a) * r + crumbs * crumbs * 8)
                sc.rgb[py_:py_ + 2, px_:px_ + 2] = (255, 230, 150) if k % 2 else (200, 140, 40)
        if pop is not None:                                              # «+1» / «−1» rising off the purse
            t, txt = pop
            SH.letters(sc, txt, 770, int(30 - t * 10), "title", 16, col=(200, 250, 130), col2=(70, 150, 50))
        SH.cursor(sc, int(cur[0]) + (1 if press else 0), int(cur[1]) + (1 if press else 0))
        return sc.image(2)

    for i in range(12):                                                  # the mouse comes over
        t = out_back(i / 11) if i < 11 else 1.0
        images.append(frame(s0, (start[0] + (hx - start[0]) * t, start[1] + (hy - start[1]) * t)))
    images.append(frame(s0, (hx, hy), press=True))
    images.append(frame(s0, (hx, hy), press=True, gem="amber"))
    images.append(frame(s0, (hx, hy), gem="amber"))
    for i in range(6):                                                   # bitten: crumbs fly, the purse ticks up
        images.append(frame(s1, (hx, hy), crumbs=(i + 1) / 6, pop=(i / 10, "+1")))
    for i in range(6, 12):
        images.append(frame(s1, (hx, hy), pop=(i / 10, "+1") if i < 10 else None))
    images += [images[-1]] * 6
    images.append(frame(s1, (hx, hy), press=True))                      # a right click: it is given back
    for i in range(6):
        images.append(frame(s0, (hx, hy), pop=(i / 10, "−1")))
    images += [frame(s0, (hx, hy))] * 8
    U.WOBBLE[0] = 0.0
    crop = [im.crop((0, 0, 1640, 400)) for im in images]
    pxfx.save_gif(crop, out("swarm_brood_eat.gif"), FPS, half=True)
    print("swarm_brood_eat.gif", len(crop))


def _well_life(sc, name, i):
    """What moves in a leader card's well, frame i of a loop of 24: honey running and eggs breathing for the
    Queen, rings of psi spreading and pulses running out along the threads for the Mind, blood dripping and a
    heartbeat for the Devourer, spores rising for the Plague."""
    import swarm_abilities as SA
    from kit import hexc
    x0, y0, x1, y1 = 24, 68, 294, 294
    t = i / 24.0
    keep = sc.rgb.copy()
    if name == "Матка":
        for (dx, off) in ((60, 0.0), (200, 0.5)):                       # honey running down the comb
            y = int(y0 + 4 + ((t + off) % 1.0) * (y1 - y0 - 30))
            x = x0 + dx
            sc.rgb[y - 6:y, x] = sc.rgb[y - 6:y, x] * 0.5 + hexc("#c08020") * 0.5
            sc.rgb[y:y + 3, x - 1:x + 2] = hexc("#e8b040")
            sc.rgb[y, x - 1] = hexc("#fff0b0")
        br = 0.5 + 0.5 * np.sin(2 * np.pi * t)
        for (ex, ey) in ((50, 286), (62, 282), (74, 288), (240, 286), (254, 282), (266, 288), (56, 274), (258, 274)):
            sc.glow(ex, ey, 9, hexc("#e8ffa0"), 0.08 + 0.18 * br)
    elif name == "Разум улья":
        cx, cy = (x0 + x1) // 2, int(y0 + (y1 - y0) * 0.58)
        for off in (0.0, 1 / 3, 2 / 3):                                  # rings spreading out
            q = (t + off) % 1.0
            r = 20 + 130 * q
            SA.ring(sc, cx, cy, r, r * 0.55, SA.PHERO, 0.7 * (1 - q))
        for j, a in enumerate(np.linspace(0, 2 * np.pi, 7, endpoint=False)):   # a pulse along each thread
            q = (t + j / 7.0) % 1.0
            ex, ey = cx + np.cos(a) * 130, cy + np.sin(a) * 90
            px_, py_ = int(cx + (ex - cx) * q), int(cy + (ey - cy) * q - 10 * 4 * q * (1 - q) * -1)
            sc.glow(px_, py_, 6, hexc("#d0a0ff"), 0.5)
            sc.rgb[py_ - 1:py_ + 1, px_ - 1:px_ + 1] = hexc("#f4e8ff")
    elif name == "Пожиратель":
        beat = max(0.0, np.sin(2 * np.pi * 2 * t)) ** 3                  # two beats a loop
        sc.glow(159, 200, 130, hexc("#ff3020"), 0.06 + 0.14 * beat)
        for (dx, off) in ((50, 0.0), (150, 0.35), (230, 0.7)):           # blood dripping from the top
            q = (t + off) % 1.0
            x = x0 + dx
            L = int(4 + 10 * min(1.0, q * 3))
            sc.rgb[y0:y0 + L, x:x + 2] = hexc("#8a1a14")
            if q > 0.33:
                y = int(y0 + L + (q - 0.33) / 0.67 * (y1 - y0 - L - 20))
                sc.rgb[y:y + 3, x:x + 2] = hexc("#b0241a")
                sc.rgb[y, x] = hexc("#e05a4a")
    else:
        rnd = np.random.RandomState(9)
        sc.glow(150, 250, 70, hexc("#88b040"), 0.1 + 0.06 * np.sin(2 * np.pi * t))
        for k in range(30):                                              # spores rising
            sx, off = rnd.randint(x0 + 6, x1 - 6), rnd.rand()
            q = (t + off) % 1.0
            y = int(y1 - 8 - q * (y1 - y0 - 16))
            x = int(sx + 4 * np.sin(q * 2 * np.pi + k))
            sc.rgb[y:y + 2, x:x + 2] = hexc("#d8ff80") if k % 3 else hexc("#a8d060")
    m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
    sc.rgb[~m] = keep[~m]


def leader_cards():
    """The four leader cards alive: each one's well moving — loops of 24."""
    import swarm_hud as H
    keep = H.big_card
    got = []

    def grab(spec, name, save=True):
        if spec.get("title") in H.CARD_DRESS:
            got.append((spec, name))
        return None
    H.big_card = grab
    try:
        H.cards()
    finally:
        H.big_card = keep
    for spec, name in got:
        lead = {"МАТКА": "Матка", "РАЗУМ УЛЬЯ": "Разум улья", "ПОЖИРАТЕЛЬ": "Пожиратель", "ЧУМА": "Чума"}[spec["title"]]
        base = keep(spec, name, save=False)
        images = []
        for i in range(24):
            sc = copy.deepcopy(base)
            SH.FILL[lead](sc, 24, 68, 294, 294)
            _well_life(sc, lead, i)
            SH.put(sc, spec["sprite"], 159 + spec.get("dx", 0), 268, spec.get("sw", 40))
            images.append(sc.image(2).crop((0, 0, 760, 640)))
            print(i, end=" ", flush=True)
        UI.WOBBLE[0] = 0.0
        fn = f"swarm_card_{SH.LEADER_EN[lead]}_anim.gif"
        pxfx.save_gif(images, out(fn), 12)
        print("\n" + fn, len(images))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    fns = {"settings": settings, "development": development, "defeat": defeat, "pause": pause, "artifacts": artifacts,
           "moments": moments, "battle_end": battle_end, "brood_eat": brood_eat,
           "leader_cards": leader_cards}
    for k, fn in fns.items():
        if what in ("all", k):
            fn()
