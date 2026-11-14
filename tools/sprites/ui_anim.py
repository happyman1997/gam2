"""The Foundry's interface moving: clicks on the console's controls (a push-button sinking and springing back with
its tag swinging on the wire, the valve's wheel turning with a hiss of steam, the lever thrown with sparks off its
stop and the nameplate's enamel flaring), the hearth burning (pixelfx fire over our coals, the coals breathing).
Frames at 24 fps; each animation goes out as a GIF to look at and as a sprite sheet with Aseprite-style JSON for
the engine (assets/ui_anim/).

    python3 tools/sprites/ui_anim.py console   -> out/foundry_console_click.gif, assets/ui_anim/*.png|json
    python3 tools/sprites/ui_anim.py hearth    -> out/foundry_hearth.gif (the smelting screen, its hearth alive)
"""
import sys
import numpy as np
from kit import *
import foundry_ui as FU
import foundry_hud as FH
import pxfx
from paths import out

FPS = 24
TOP = 440                   # the console strip is drawn from this row of the screen down


# ---------------------------------------------------------------- easing (Robert Penner's, BSD)
def out_back(t, s=2.2):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def in_out_cubic(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def out_quad(t):
    return 1 - (1 - t) ** 2


# ---------------------------------------------------------------- the clicks, frame by frame
def press_curve(n):
    """A push-button's cap over a click: down fast, held, back up past its rest and settling."""
    keys = [0.0, 0.55, 1.0, 1.0, 0.85, 0.3, -0.35, -0.2, 0.05, 0.0]
    return [keys[i] if i < len(keys) else 0.0 for i in range(n)]


def swing_curve(n, start=2):
    """The tag on its wire after the knock: a swing that dies away."""
    out_ = []
    for i in range(n):
        t = i - start
        out_.append(0 if t < 0 else int(round(2.4 * np.exp(-t / 5.0) * np.sin(t * 0.9))))
    return out_


CONSOLE = [   # (x0, y0, x1, y1, text, kind, big) as on the workshop's console
    (12, 478, 174, 526, "Автосборка", "steel", False),
    (178, 478, 356, 526, "Починить · 2", "hot", False),
    (360, 478, 522, 526, "Переплавка", "rust", False),
    (526, 478, 704, 526, "Пропуск · +4", "steel", False),
    (710, 472, 948, 532, "В БОЙ", "hot", True),
]


def console_timeline():
    """Per frame, each control's state: Автосборка clicked, then the valve turned, then the lever thrown."""
    n = 96
    st = [dict() for _ in range(n)]
    pc, sw = press_curve(14), swing_curve(18)
    for i in range(14):
        st[6 + i]["Автосборка"] = dict(press=pc[i], swing=sw[i])
    for i in range(14, 18):
        st[6 + i]["Автосборка"] = dict(swing=sw[i])
    for i in range(26):                                            # the valve: a quarter turn, eased
        f = min(1.0, i / 12.0)
        st[24 + i]["Починить · 2"] = dict(turn=in_out_cubic(f) * np.pi / 2, swing=swing_curve(26, 3)[i])
    for i in range(n - 54):                                        # the lever: thrown past its stop, back onto it
        f = min(1.0, i / 6.0)
        ang = -0.5 + (0.62 + 0.5) * out_back(f, 2.6)
        glow = 0.32 * np.exp(-max(0, i - 5) / 6.0) if i >= 5 else 0.0
        st[54 + i]["В БОЙ"] = dict(angle=ang, glow=glow)
    return st


def draw_console(sc, frame_state, dy=0):
    FU.sill(sc, 468 - TOP + dy, sc.h)
    for x0, y0, x1, y1, text, kind, big in CONSOLE:
        FH.action(sc, x0, y0 - TOP + dy, x1, y1 - TOP + dy, text, kind, big=big, anim=frame_state.get(text))


def console():
    """The console strip with three clicks in a row, as a GIF; and each control's click alone, as a sheet."""
    st = console_timeline()
    steam, sm = pxfx.load("valve-steam")
    spark, km = pxfx.load("hit-spark")
    images = []
    for i, fs in enumerate(st):
        sc = Scene(960, 540 - TOP)
        sc.rgb[:] = hexc("#1a1820")
        shake = 1 if 55 <= i <= 56 else 0                          # the lever lands: the console jolts
        draw_console(sc, fs, dy=shake)
        j = i - 26                                                 # the steam off the valve's spindle
        if 0 <= j < len(steam):
            pxfx.blend(sc, steam[j], 200, 502 - TOP - 14, sm["pivot"])
        j = i - 59                                                 # sparks off the lever's stop
        if 0 <= j < len(spark):
            lx, py = 728, 532 + 2 - 9 - TOP
            ex, ey = lx + np.sin(0.62) * 48, py - np.cos(0.62) * 48
            pxfx.blend(sc, spark[j], ex, ey + 10, km["pivot"])
        images.append(sc.image(2))
    pxfx.save_gif(images, out("foundry_console_click.gif"), FPS)
    print("foundry_console_click.gif", len(images), "frames")
    # each control's click alone, transparent, for the engine
    for key, x0, x1, n0, n in (("Автосборка", 0, 180, 6, 18), ("Починить · 2", 170, 362, 24, 26), ("В БОЙ", 700, 960, 54, 30)):
        name = {"Автосборка": "button_click", "Починить · 2": "valve_turn", "В БОЙ": "lever_pull"}[key]
        frames_ = []
        for i in range(n0, n0 + n):
            fs = st[i]

            def draw(s, fs=fs, key=key):
                for c in CONSOLE:
                    if c[4] == key:
                        FH.action(s, c[0] - x0, c[1] - TOP, c[2] - x0, c[3] - TOP, c[4], c[5], big=c[6], anim=fs.get(key))
            frames_.append(pxfx.matte(draw, x1 - x0, 540 - TOP))
        pxfx.save_sheet(frames_, name, FPS, loop=False, pivot=(0, 0))
        print("sheet", name, len(frames_))


def hearth():
    """The smelting screen with its hearth alive: pixelfx's forge fire looping over the coals, the coals breathing,
    the glow pulsing; the rest of the screen drawn once."""
    import copy
    import hearth as HT
    import icons as IC
    base = FH.smelt(base_only=True)
    frames, meta = pxfx.load("forge-fire")
    melt = FH.molten(IC.icon("canister", 3, "module"))
    cast = FH.molten(IC.icon("long", 3, "module"), 1.2)
    images = []
    n = len(frames)
    for i in range(n):
        sc = copy.deepcopy(base)
        HT.scene(sc, 316, 60, 644, 454, melt, cast, frame=i, phase=i / n)
        images.append(sc.image(2))
    pxfx.save_gif(images, out("foundry_hearth.gif"), meta["fps"], half=True)
    print("foundry_hearth.gif", n, "frames")


def workshop():
    """The workshop alive, then a part set in: the part on the crane swaying, the mount it goes to pulsing hot, a
    glint running along the spanners, sparks at the slipway, the lever's enamel breathing; then the crane lowers the
    Long Barrel onto the Gun's arm — it lands with a clank and a spray of sparks, its box flares and cools, the drawn
    golem now carries it, the empty hook goes back up."""
    import copy
    spark, km = pxfx.load("hit-spark")
    n_idle, n_drop, n_after = 24, 10, 26
    images = []
    pt = None
    for i in range(n_idle + n_drop + n_after):
        t = i / FPS
        a = dict(sway=2.2 * np.sin(2 * np.pi * t / 1.6), pulse=0.75 + 0.25 * np.sin(2 * np.pi * t / 0.8),
                 plate=0.05 * np.sin(2 * np.pi * t / 1.2), seed=i // 2)
        g = (t % 2.0) / 0.6
        a["glint"] = g if g <= 1 else None
        if n_idle <= i < n_idle + n_drop:                                  # lowering
            a["drop"] = (i - n_idle + 1) / n_drop
            a["sway"] *= 1 - a["drop"]
        elif i >= n_idle + n_drop:                                         # set in, the hook going back up
            j = i - n_idle - n_drop
            a.update(installed="long", retract=min(1.0, j / 12.0), sway=0, flash="long" if j < 4 else None)
        sc = FH.workshop(anim=a, ret=True)
        if i >= n_idle + n_drop:
            j = i - n_idle - n_drop
            if j == 0 or j == 1:                                           # the clank: the screen jolts
                sc.rgb[:] = np.roll(sc.rgb, 1, axis=0)
            if j < len(spark):
                pxfx.blend(sc, spark[j], 518, 362, km["pivot"])
        images.append(sc.image(2))
        print(i, end=" ", flush=True)
    pxfx.save_gif(images, out("foundry_workshop_anim.gif"), FPS, half=True)
    print("\nfoundry_workshop_anim.gif", len(images), "frames")


def tabs():
    """A click on the panel's tabs: ДОБЫЧА open, the mouse on СТОЙКА, it sinks under the click, opens — a glint runs
    across its brass; the repair badge throbs all the while."""
    images = []
    for i in range(40):
        sc = Scene(960, 100)
        sc.rgb[:] = hexc("#1c1a20")
        FU.plate(sc, 708, 52, 948, 100, seed=4)
        cur = "loot" if i < 12 else "rack"
        a = dict(pulse=1.0 * max(0.0, np.sin(2 * np.pi * i / 16.0)))
        if 8 <= i < 12:
            a["press"] = "rack"
        if 12 <= i < 22:
            a["flash"] = (i - 12) / 9.0
        FH.panel_tabs(sc, cur, anim=a)
        if 6 <= i < 12:
            import swarm_hud as H
            H.cursor(sc, 800, 72 + (1 if 8 <= i < 12 else 0))
        images.append(sc.image(2).crop((700 * 2, 50 * 2, 952 * 2, 92 * 2)))
    pxfx.save_gif(images, out("foundry_tabs_click.gif"), FPS)
    print("foundry_tabs_click.gif", len(images))


def steps():
    """The new golem's steps moving on: the heat runs out of ТЕЛО's point into ЯДРО, ЯДРО heats from the left,
    ТЕЛО cools to brass behind it, sparks fly off the new step's point."""
    def bar(cur):
        sc = Scene(960, 96)
        sc.rgb[:] = hexc("#1c1a20")
        FH.steps_bar(sc, cur, y=52 - 40)
        return sc
    A, B = bar(1), bar(2)
    n = len(FH.STEPS)
    w = (960 - 24 + 12 * (n - 1)) // n
    xa0, xa1 = 12 + 1 * (w - 12), 12 + 1 * (w - 12) + w                     # ТЕЛО
    xb0, xb1 = 12 + 2 * (w - 12), 12 + 2 * (w - 12) + w                     # ЯДРО
    images = []
    for i in range(30):
        sc = Scene(960, 96)
        sc.rgb[:] = A.rgb.copy()
        if i >= 6:
            f = min(1.0, (i - 6) / 10.0)
            front = xb0 + (xb1 - xb0) * f
            cool = np.clip(f * 1.2, 0, 1)
            sc.rgb[:, xa0:xa1] = A.rgb[:, xa0:xa1] * (1 - cool) + B.rgb[:, xa0:xa1] * cool
            sc.rgb[:, xb0:int(front)] = B.rgb[:, xb0:int(front)]
            if f < 1:
                col = (sc.yy >= 12) & (sc.yy < 44) & (np.abs(sc.xx - front) < 1.5) & (B.rgb.sum(axis=2) > 120)
                sc.rgb[col] = np.array((255.0, 236.0, 160.0))
        if 16 <= i < 26:
            FU.sparks(sc, xb1 - 10, 28, 10, seed=i)
        images.append(sc.image(2).crop((0, 8 * 2, 960 * 2, 50 * 2)))
    pxfx.save_gif(images, out("foundry_steps.gif"), FPS)
    print("foundry_steps.gif", len(images))


def metal_tick():
    """The purse paying: the ingot hops, 14 slides up and out, 12 slides in from below, a red −2 floats away."""
    import swarm_hud as H
    from swarm_ui import letters
    images = []
    for i in range(30):
        sc = Scene(220, 44)
        FU.wing(sc, 0, 0, 220, 44)
        f = np.clip((i - 6) / 8.0, 0, 1)
        hop = -int(round(3 * np.sin(np.pi * np.clip((i - 5) / 6.0, 0, 1))))
        H.glyph(sc, "металл", 18, 10 + hop, 2)
        bg = sc.rgb.copy()
        if f < 1:
            letters(sc, "14", 48, 12 - int(16 * f), "title", 16, col=(214, 220, 236), col2=(90, 96, 120))
        if f > 0:
            letters(sc, "12", 48, 12 + int(16 * (1 - f)), "title", 16, col=(214, 220, 236), col2=(90, 96, 120))
        win = np.zeros((sc.h, sc.w), bool)                                 # the numbers show only in their slot
        win[9:33, 44:92] = True
        outside = ~win & (sc.xx >= 40) & (sc.xx < 96)
        sc.rgb[outside] = bg[outside]
        if 6 <= i < 26:
            k = (i - 6) / 20.0
            letters(sc, "−2", 98, 12 - int(10 * k), "text", 16, col=(255, 120, 90))
        images.append(sc.image(2))
    pxfx.save_gif(images, out("foundry_metal_tick.gif"), FPS)
    print("foundry_metal_tick.gif", len(images))


def gears_title():
    """The victory's title: its cogs turning in mesh, the small ones the other way and faster; one tooth's turn
    loops seamlessly."""
    images = []
    n = 24
    for i in range(n):
        sc = Scene(960, 44)
        FU.wing(sc, 0, 0, 960, 44)
        FH.title_center(sc, "ПОБЕДА", "gears", turn=(2 * np.pi / 12) * i / n)
        images.append(sc.image(2).crop((560, 0, 1360, 88)))
    pxfx.save_gif(images, out("foundry_gears.gif"), FPS)
    print("foundry_gears.gif", n)


def leaders():
    """Choosing the leader: the chosen one's furnace burning behind him — pixelfx's fire in the arch, sparks at its
    mouth — as a loop."""
    frames, meta = pxfx.load("forge-fire")
    images = []
    for i in range(len(frames)):
        sc = FH.leaders_pick(anim={"frame": i}, ret=True)
        images.append(sc.image(2))
        print(i, end=" ", flush=True)
    pxfx.save_gif(images, out("foundry_leader_fire.gif"), meta["fps"], half=True)
    print("\nfoundry_leader_fire.gif", len(images))


def leader_card():
    """The leader's full card: his furnace burning behind him, two fires in turns, sparks at his feet — the card's
    left plate, the only part of the screen that moves, as a loop."""
    frames, meta = pxfx.load("forge-fire")
    images = []
    for i in range(len(frames)):
        sc = FH.leader_card(frame=i, ret=True)
        images.append(sc.image(2).crop((0, 96, 672, 932)))
        print(i, end=" ", flush=True)
    pxfx.save_gif(images, out("foundry_leader_card.gif"), meta["fps"], half=True)
    print("\nfoundry_leader_card.gif", len(images))


def heat_env(i, a, b, c, d):
    """How hot a thing under the mouse is at frame i: heating a..b, held b..c, cooling c..d (eased)."""
    if i < a or i >= d:
        return 0.0
    if i < b:
        return in_out_cubic((i - a) / max(1, b - a))
    if i < c:
        return 1.0
    return 1.0 - in_out_cubic((i - c) / max(1, d - c))


def hover():
    """The mouse passing over things: a part's box on the drawing, a golem's bay on the army's rack, a card in the
    crate — each rim heats red from the edge in, holds with the sparks flickering, and cools when the mouse moves on."""
    import swarm_hud as H
    from swarm_ui import letters
    import frames as F

    def draw(sc, states, seed):
        sc.rgb[:] = hexc("#1c1a20")
        FH.blueprint_sheet(sc, 10, 10, 200, 110)
        FH.part_box(sc, 28, 38, "canister", "ствол", 1, state=states[0], w=152, h=42) if states[0] != "hover" else None
        if states[0] == "hover":
            FU.cell(sc, 28, 38, 180, 80, "hover", seed=seed)
            letters(sc, "Ствол", 36, 40, "text", 16, col=(150, 200, 230), outline=False)
            FH.mod_icon(sc, "canister", 36, 60)
            letters(sc, "Картечь", 58, 59, "text", 16, col=FH.INK)
            FU.levels(sc, 180 - 26, 44, 1)
        FU.cell(sc, 222, 14, 382, 100, states[1], seed=seed)                 # a bay on the army's rack
        g = FH.golem_sprite("Механик", {"repair": 1, "oiler": 1}, 0.48)
        sc.blit(g, int(222 + 34 - g.ox), int(14 + 78 - g.oy))
        letters(sc, "Механик", 222 + 66, 22, "text", 16, col=FH.INK)
        for j in range(3):
            cx_ = 222 + 68 + j * 12
            sc.rgb[46:56, cx_:cx_ + 9] = (14, 12, 18)
            sc.rgb[47:55, cx_ + 1:cx_ + 8] = FU.hexc("#e0b860") if j < 2 else FU.hexc("#24222a")
        FU.core_port(sc, 222 + 74, 76, "cast")
        FU.cell(sc, 404, 8, 628, 114, states[2], seed=seed)                  # a card in the crate
        FU.cell(sc, 412, 18, 464, 70, "locked")
        FH.mod_icon(sc, "grapple", 422, 28, 2)
        letters(sc, "Крюк-кошка", 474, 22, "text", 16, col=FH.INK)
        letters(sc, "любой", 474, 40, "text", 16, col=FH.PALE)
        H.fx_rows(sc, 412, 84, 210, FH.MOD_FX["grapple"])

    base = Scene(640, 124)
    draw(base, ("normal", "normal", "rare"), 0)
    hot = []
    for sd in range(4):
        sc = Scene(640, 124)
        draw(sc, ("hover", "hover", "hover"), sd * 7)
        hot.append(sc.rgb.copy())
    spans = ((4, 10, 18, 24), (20, 26, 34, 40), (36, 42, 52, 58))
    xs = ((10, 200), (216, 388), (398, 634))
    cur = ((120, 66), (330, 70), (560, 64))
    images = []
    for i in range(64):
        sc = Scene(640, 124)
        sc.rgb[:] = base.rgb
        hb = hot[(i // 3) % 4]
        for (x0, x1), sp in zip(xs, spans):
            h = heat_env(i, *sp)
            if h > 0:
                sc.rgb[:, x0:x1] = base.rgb[:, x0:x1] * (1 - h) + hb[:, x0:x1] * h
        for (x0, x1), sp, (cx_, cy_) in zip(xs, spans, cur):
            if sp[0] <= i < sp[2] + 2:
                H.cursor(sc, cx_, cy_)
        images.append(sc.image(2))
    pxfx.save_gif(images, out("foundry_hover.gif"), FPS)
    print("foundry_hover.gif", len(images))


def speed():
    """The battle's speed buttons: ×2 clicked off, then pause clicked on — each cap sinks, its key lights."""
    import swarm_hud as H
    import swarm_ui as SU
    images = []
    for i in range(40):
        sc = Scene(240, 48)
        FU.wing(sc, 0, 0, 240, 34)
        sc.rgb[34:] = FU.hexc("#1c1a20")
        two_on = i < 12
        pause_on = i >= 30
        pc = press_curve(14)
        p2 = pc[i - 6] if 6 <= i < 20 else 0.0
        pp = pc[i - 24] if 24 <= i < 38 else 0.0
        for cx, t_, on, key, pr in ((40, "II", pause_on, "Пробел", pp), (110, "×2", two_on, "Tab", p2),
                                    (180, "»", False, "End", 0.0)):
            FU.cap_button(sc, cx, 17, 11, t_, "brass" if on else "steel", press=pr)
            kw = SU.text_width(key, "text", 16) + 12
            H.keycap(sc, int(cx - kw / 2), 32, key, lit=pr > 0.5)
        if 3 <= i < 20:
            H.cursor(sc, 116, 22)
        elif 21 <= i < 38:
            H.cursor(sc, 46, 22)
        images.append(sc.image(2))
    pxfx.save_gif(images, out("foundry_speed.gif"), FPS)
    print("foundry_speed.gif", len(images))


def start():
    """A new golem started: steam going up off its chimney and shoulders in turns, sparks at the foot of the stand,
    as a loop."""
    import copy
    base = FH.assembly(4, anim={}, ret=True)
    steam, sm = pxfx.load("valve-steam")
    n = 36
    vents = ((280, 258, 0, 0.9), (280, 258, 18, 0.9), (326, 318, 9, 0.55))   # the chimney twice, a shoulder valve
    images = []
    for i in range(n):
        sc = copy.deepcopy(base)
        for x, y, off, k in vents:
            j = (i + off) % n
            if j < len(steam):
                pxfx.blend(sc, steam[j], x, y, sm["pivot"], k=k)
        FU.sparks(sc, 200, 440, 12, seed=3 + i // 2)
        FU.sparks(sc, 400, 440, 10, seed=40 + i // 2)
        images.append(sc.image(2))
    pxfx.save_gif(images, out("foundry_start.gif"), FPS, half=True)
    print("foundry_start.gif", n)


def aftermath_anim():
    """The victory screen: the repair stamp comes down — big and faint, smaller, lands with a jolt — and the part
    that broke throbs red on the drawing; the cogs in the title turn all the while."""
    images = []
    seq = [None] * 6 + [(2.2, 0.35), (1.6, 0.6), (1.15, 0.85), (1.0, 1.0)] + [(1.0, 1.0)] * 26
    for i, st in enumerate(seq):
        pulse = 0.55 + 0.45 * np.sin(2 * np.pi * i / 18.0)
        sc = FH.aftermath(anim={"stamp": st, "pulse": pulse}, ret=True)
        # the cogs in the title turning: redraw the title bar over the screen's
        FU.wing(sc, 0, 0, 960, 44)
        FH.title_center(sc, "ПОБЕДА", "gears", turn=(2 * np.pi / 12) * i / 24)
        FH.metal(sc, 20, x=18)
        FH.toolbar(sc)
        if i in (9, 10):
            sc.rgb[:] = np.roll(sc.rgb, 1, axis=0)
        images.append(sc.image(2))
        print(i, end=" ", flush=True)
    pxfx.save_gif(images, out("foundry_aftermath_anim.gif"), FPS, half=True)
    print("\nfoundry_aftermath_anim.gif", len(images))


def card_tip():
    """The golem's card: the mouse comes onto the Mortar's box, the box heats, its tooltip slides up into place
    and fades in."""
    import copy
    images = []
    seq = [0.0] * 6 + [0.2, 0.45, 0.7, 0.88, 1.0] + [1.0] * 13
    for i, k in enumerate(seq):
        sc = FH.card(anim={"tip": k}, ret=True)
        images.append(sc.image(2))
        print(i, end=" ", flush=True)
    pxfx.save_gif(images, out("foundry_card_tip.gif"), FPS, half=True)
    print("\nfoundry_card_tip.gif", len(images))


def pop_env(i, start, n=24):
    """A module's pop over its golem at frame i: (k, rise, heat) — it jumps up out of the golem past its place and
    settles, glows red-hot, cools to iron, then drifts up and fades. None when it is not up."""
    t = i - start
    if t < 0 or t >= n:
        return None
    if t < 5:
        e = out_back(t / 5)
        return min(1.0, t / 3), -10 * (1 - e), 1.0
    if t < n - 6:
        return 1.0, 0.0, max(0.0, 1 - (t - 5) / 10)
    f = (t - (n - 6)) / 6
    return 1 - in_out_cubic(f), 6 * out_quad(f), 0.0


def battle_anim():
    """The battle seen by the Foundry: the tug of war on the beam swaying — the iron pushes in after the Canister
    fires, the swarm presses back — sparks at the seam; the modules' icons popping up over their golems in turn."""
    images = []
    N = 48
    for i in range(N):
        share = 0.44 + 0.022 * np.sin(2 * np.pi * i / N) + 0.008 * np.sin(6 * np.pi * i / N)
        pops = []
        for key, nm, who, st in (("canister", "Картечь", ("Орудие", 3, 2), 0), ("intercept", "Перехват", ("Страж", 5, 6), 22)):
            e = pop_env(i, st)
            if e:
                pops.append((key, nm, who) + e)
        sc = FH.battle_view("run", t=i, share=share, pops=pops, ret=True)
        images.append(sc.image(2).crop((0, 0, 1120, 680)))
        print(i, end=" ", flush=True)
    pxfx.save_gif(images, out("foundry_battle_anim.gif"), FPS, half=True)
    print("\nfoundry_battle_anim.gif", len(images))


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "console"
    {"console": console, "hearth": hearth, "workshop": workshop, "tabs": tabs, "steps": steps,
     "metal": metal_tick, "gears": gears_title, "leaders": leaders,
     "hover": hover, "speed": speed, "start": start, "aftermath": aftermath_anim, "card": card_tip, "leadercard": leader_card,
     "battle": battle_anim}[what]()
