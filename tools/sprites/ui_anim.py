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
    pxfx.save_gif(images, out("foundry_hearth.gif"), meta["fps"])
    print("foundry_hearth.gif", n, "frames")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "console"
    {"console": console, "hearth": hearth}[what]()
