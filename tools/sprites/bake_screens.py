"""Bakes the screens' art for the game (game/assets/bg, game/assets/ui): the backgrounds the mockups are drawn on,
taken from the very functions that drew the mockups, with every word and every button left out — the engine draws
the text (it will be translated) and the buttons (they move under the mouse). What is baked:

  bg/forge, bg/hive            the Foundry's soot-black brick and the swarm's dark wax comb, plain
  bg/menu_0..7                 the main menu: the furnace burning (eight frames of the fire), the Guard, the wall broken
                               open with the swarm coming through; the cartouche for the name and the console's sill
  bg/class_0..7                the class pick, both halves lit; the engine dims the one not under the mouse
  bg/leaders_f, bg/leaders_s   the leader pick of each class, every card unchosen; the chosen card's crop on top:
                               ui/pick_f{i}_{frame} (its furnace open and burning, six frames), ui/pick_s{i}
  ui/gear_{r}_{k}              brass gears turning (eight phases), ui/lantern_{on,off}, ui/anvil

    python3 tools/sprites/bake_screens.py      (demo_bake.py runs it too)
"""
import contextlib
import json
import os
import sys
import numpy as np
from PIL import Image
from kit import Scene, hexc
import pxfx

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "..", "..", "game", "assets")
MANIFEST = {"bg": {}, "ui": {}}


@contextlib.contextmanager
def no_text():
    """Every word and button the mockup functions draw, left out for the time: letters still measure (layouts use
    their widths), glyph lines measure without drawing, buttons and the toolbar draw nothing."""
    import swarm_ui as SU
    import swarm_hud as SH
    import foundry_hud as FH
    orig_letters, orig_fx = SU.letters, SH.fx_line

    def letters(sc, text, *a, **k):
        kind = a[2] if len(a) > 2 else k.get("kind", "text")
        px = a[3] if len(a) > 3 else k.get("px", 16)
        return SU.text_width(text, kind, px)

    def fx_line(sc, x, y, line, *a, **k):
        k["draw"] = False
        return orig_fx(sc, x, y, line, *a, **k)

    noop = lambda *a, **k: None
    saved = []
    for mod in list(sys.modules.values()):
        for name, new, old in (("letters", letters, orig_letters), ("fx_line", fx_line, orig_fx)):
            if getattr(mod, name, None) is old:
                saved.append((mod, name, old))
                setattr(mod, name, new)
    for mod, name in ((FH, "action"), (FH, "toolbar"), (SH, "act_button"), (SH, "help_button"), (SH, "keycap")):
        saved.append((mod, name, getattr(mod, name)))
        setattr(mod, name, noop)
    import menu
    for name in ("action",):
        saved.append((menu, name, getattr(menu, name)))
        setattr(menu, name, noop)
    try:
        yield
    finally:
        for mod, name, old in saved:
            setattr(mod, name, old)


def rgb_of(sc):
    return Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8), "RGB")


def save_bg(name, sc, crop=None):
    os.makedirs(os.path.join(DST, "bg"), exist_ok=True)
    im = rgb_of(sc)
    if crop:
        im = im.crop(crop)
    im.save(os.path.join(DST, "bg", name + ".png"), optimize=True)
    MANIFEST["bg"][name] = dict(file=f"bg/{name}.png", size=[im.width, im.height])


def save_ui(name, im, **meta):
    os.makedirs(os.path.join(DST, "ui"), exist_ok=True)
    im.save(os.path.join(DST, "ui", name + ".png"), optimize=True)
    MANIFEST["ui"][name] = dict(file=f"ui/{name}.png", size=[im.width, im.height], **meta)


def plain():
    import foundry_hud as FH
    import swarm_ui as UI
    save_bg("forge", FH.screen(5))
    UI.WOBBLE[0] = 0.0
    save_bg("hive", UI.nest(960, 540, 9))


def menu_frames():
    import menu
    with no_text():
        for f in range(8):
            save_bg(f"menu_{f}", menu.main_menu(frame=f * 2, ret=True))


def class_frames():
    """menu.class_pick without its cells, words, buttons and the dimming: both halves lit."""
    import menu
    import foundry_hud as FH
    import foundry_ui as FU
    import swarm_ui as UI
    import swarm_hud as SH
    import frames as F
    from foundry_hud import SU, WW, HH, leader_sprite
    with no_text():
        for f in range(8):
            sc = FH.screen(103)
            nest = UI.nest(WW, HH, 7)
            right = sc.xx >= WW // 2
            sc.rgb[right] = nest.rgb[right]
            for y in range(HH):
                x = WW // 2 + int(4 * np.sin(y / 11.0) + 3 * np.sin(y / 3.7))
                sc.rgb[y, x - 1:x + 2] = SU.OUTL
            FU.wing(sc, 0, 0, WW // 2, 44)
            UI.wing(sc, WW // 2, 0, WW, 44)
            FU.plate(sc, 16, 56, 462, 420, seed=31)
            menu.furnace(sc, 239, 190, 96, 300, f * 2)
            spr = leader_sprite("colossus", 1.9)
            sc.blit(spr, int(239 - spr.ox), int(296 - spr.oy))
            for fr, x in (("Механик", 120), ("Орудие", 362)):
                g = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.62)
                sc.blit(g, int(x - g.ox), int(300 - g.oy))
            UI.plate(sc, 498, 56, 944, 420, antennae=True)
            q = SH.leader("Матка", "idle", 1.15)
            SH.put(sc, q, 760, 296, 30)
            for j, (tr, x, y) in enumerate(((("stinger",), 560, 300), (("wings",), 610, 280), ((), 900, 296),
                                            (("horn",), 870, 270), (("acid",), 590, 250))):
                SH.put(sc, SH.bug(tr, "attack" if (j + f) % 4 == 0 else "idle", 0.8, 50 + j), x, y, 8)
            FU.sill(sc, 440, None)
            UI.wing(sc, WW // 2, 440, WW, HH)
            save_bg(f"class_{f}", sc)


def foundry_leaders():
    """The Foundry's leader pick: all four doors shut (the background), then each card with its door open and the
    fire burning, cut out frame by frame."""
    import foundry_hud as FH
    import foundry_ui as FU
    import swarm_ui as UI
    orig_cell = FU.cell
    with no_text():
        for chosen in (-1, 0, 1, 2, 3):
            for f in (range(6) if chosen >= 0 else [0]):
                sc = leaders_pick_f(chosen, f * 2)
                if chosen < 0:
                    save_bg("leaders_f", sc)
                else:
                    x0 = 14 + chosen * 236
                    im = rgb_of(sc).crop((x0, 54, x0 + 227, 457))
                    save_ui(f"pick_f{chosen}_{f}", im, at=[x0, 54])


def leaders_pick_f(chosen, frame):
    """foundry_hud.leaders_pick with the chosen card given (the mockup always chose the first)."""
    import foundry_hud as FH
    import foundry_ui as FU
    import frames as F
    from foundry_hud import WW
    sc = FH.screen(17)
    FU.wing(sc, 0, 0, WW, 44)
    for i, (nm, epi, kind, k, army, rule) in enumerate(FH.PICK):
        x0, sel = 14 + i * 236, i == chosen
        x1 = x0 + 226
        FU.plate(sc, x0, 54, x1, 456, seed=20 + i)
        X, Y = sc.xx, sc.yy
        ax, ay, ar = (x0 + x1) / 2, 200, 86
        arch = ((((X - ax) / ar) ** 2 + ((Y - ay) / ar) ** 2 <= 1) & (Y <= ay)) | ((np.abs(X - ax) <= ar) & (Y > ay) & (Y < 300))
        t = np.clip((Y - 114) / 186, 0, 1)
        if sel:
            fire = hexc("#1e0a06")[None, None, :] * (1 - t[..., None]) + hexc("#7a2410")[None, None, :] * t[..., None]
        else:
            fire = hexc("#141216")[None, None, :] * (1 - t[..., None]) + hexc("#4a2010")[None, None, :] * t[..., None]
        sc.rgb[arch] = fire[arch]
        rim = arch & ~((((X - ax) / (ar - 3)) ** 2 + ((Y - ay) / (ar - 3)) ** 2 <= 1) & (Y <= ay) | ((np.abs(X - ax) <= ar - 3) & (Y > ay) & (Y < 300)))
        sc.rgb[rim] = hexc("#b8904a") if sel else hexc("#4a4850")
        if sel:
            frames_, meta = pxfx.load("forge-fire")
            before = sc.rgb.copy()
            inside = arch & ~rim
            pxfx.blend(sc, frames_[frame % len(frames_)], ax, 300, meta["pivot"])
            sc.rgb[~inside] = before[~inside]
        for kk in range(-4, 5):
            a_ = np.pi * (0.5 + kk / 10)
            FU.rivet(sc, ax - np.cos(a_) * (ar + 4), ay - np.sin(a_) * (ar + 4))
        spr = FH.leader_sprite(kind, k)
        sc.blit(spr, int(ax - spr.ox), int(296 - spr.oy))
        if sel:
            FU.sparks(sc, ax - 60, 296, 10, seed=3 + frame // 3)
            FU.sparks(sc, ax + 64, 290, 8, seed=4 + frame // 3)
        FU.cell(sc, x0 + 10, 62, x1 - 10, 104, "hi" if sel else "normal")
        gx = ax - (len(army) - 1) * 28
        for j, fr in enumerate(army):
            g = F.build(fr, "idle", k=F.FRAMES[fr][0] * 0.58)
            sc.blit(g, int(gx + j * 56 - g.ox), int(380 - g.oy))
        sc.rgb[300:302, x0 + 16:x1 - 16] = hexc("#5a5860")
    FU.sill(sc, 464)
    return sc


def swarm_leaders():
    """The swarm's leader pick: the four beetle-cards unchosen (the background), each chosen cut out."""
    import swarm_hud as SH
    import swarm_ui as UI
    names = ["Матка", "Разум улья", "Пожиратель", "Чума"]
    with no_text():
        for chosen in (-1, 0, 1, 2, 3):
            sc = SH.frame_screen(41)
            X, Y = sc.xx, sc.yy
            fog = np.clip((Y - 300) / 240, 0, 1)[..., None] * 0.22
            sc.rgb[:] = sc.rgb * (1 - fog) + np.array((60, 110, 20), float) * fog
            rnd = np.random.RandomState(7)
            for _ in range(40):
                bx, by, br = rnd.randint(10, 950), rnd.randint(300, 470), rnd.choice((1, 1, 2, 3))
                ring = (np.abs(np.hypot(X - bx, Y - by) - br) < 0.7)
                sc.rgb[ring] = sc.rgb[ring] * 0.4 + np.array(SH.ACID, float) * 0.6
            UI.wing(sc, 0, 0, 960, 44)
            UI.drips(sc, 60, 900, 44, "#7ab020", n=8, seed=18)
            for i, name in enumerate(names):
                SH.bug_card(sc, int(480 + (i - 1.5) * 232), 60, name, i == chosen, seed=40 + i)
            UI.cobweb(sc, 958, 46, 34, quad=(-1, 1))
            if chosen < 0:
                save_bg("leaders_s", sc)
            else:
                cx = int(480 + (chosen - 1.5) * 232)
                im = rgb_of(sc).crop((cx - 116, 44, cx + 116, 470))
                save_ui(f"pick_s{chosen}", im, at=[cx - 116, 44])
    UI.WOBBLE[0] = 0.0


def props():
    """Small things on transparent ground: brass gears turning, a lantern lit and dark, an anvil."""
    import foundry_ui as FU
    for r, teeth in ((10, 8), (16, 12)):
        for k in range(8):
            ph = k / 8 * (2 * np.pi / teeth)
            def draw(sc, r=r, teeth=teeth, ph=ph):
                FU.gear(sc, r + 3, r + 3, r, teeth=teeth, phase=ph)
            save_ui(f"gear_{r}_{k}", pxfx.matte(draw, 2 * r + 6, 2 * r + 6))
    for lit, nm in ((1.0, "on"), (0.0, "off")):
        def draw(sc, lit=lit):
            FU.lantern(sc, 16, 0, 22, size=1.0, lit=lit, seed=3)
        save_ui(f"lantern_{nm}", pxfx.matte(draw, 32, 48))

    def anvil(sc):
        FU.anvil(sc, 36, 30)
    save_ui("anvil", pxfx.matte(anvil, 72, 34))


def nameplates():
    """The cast nameplates of the screens' main actions, at the sizes the screens use: ember-red enamel at rest and
    glowing under the mouse, black enamel when it can't be pressed (foundry_ui.nameplate, no letters)."""
    import foundry_ui as FU
    with no_text():
        for w, h in ((272, 64), (244, 52), (200, 44)):
            for nm, hot, glow in (("rest", True, 0.0), ("lit", True, 0.16), ("off", False, None)):
                def draw(sc, hot=hot, glow=glow):
                    FU.nameplate(sc, 2, 2, w + 2, h + 2, "", hot=hot, glow=glow)
                save_ui(f"plate_{nm}_{w}x{h}", pxfx.matte(draw, w + 4, h + 4), pad=2)


def main(write_manifest=True):
    plain()
    menu_frames()
    class_frames()
    foundry_leaders()
    swarm_leaders()
    props()
    nameplates()
    if write_manifest:
        json.dump(MANIFEST, open(os.path.join(DST, "screens.json"), "w"), ensure_ascii=False, indent=1)
    print("bg", len(MANIFEST["bg"]), "ui", len(MANIFEST["ui"]))


if __name__ == "__main__":
    main()
