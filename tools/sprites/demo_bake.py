"""Bakes what the tech demo draws into game/assets: the field's ground, every unit of the demo's battle (the
Inventor's start against the Devourer's) in each pose it takes, with its pivot (the point on the ground it stands
on), the effects, bitmap fonts with Cyrillic, and the battle HUD's pieces. The game is a Rust program and does not
run this code; what it shows comes from here (docs/TECH.md: sprites baked for the demo, the builders ported later).

    python3 tools/sprites/demo_bake.py   -> game/assets/{ground.png, sprites/, fx/, fonts/, ui/, assets.json}
"""
import json
import os
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import Scene, hexc
import battle as BT
import frames as F
import leaders_h as LH
import swarm1 as W
import swarm_leaders as SL
import swarm_ui as UI
import swarm_hud as SH
import pxfx
from swarm_menus import flip_dead

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "..", "..", "game", "assets")
MANIFEST = {"sprites": {}, "fx": {}, "fonts": {}, "ui": {}}


def save_sprite(name, spr, emit=None):
    """A kit Sprite as an RGBA PNG cropped to what it covers; the pivot moved with the crop; `emit` — where a bolt
    leaves it, in px from the ground point (the same after the crop)."""
    ys, xs = np.nonzero(spr.a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    rgba[..., :3] = np.clip(spr.rgb[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    rgba[..., 3] = spr.a[y0:y1, x0:x1] * 255
    os.makedirs(os.path.dirname(os.path.join(DST, "sprites", name + ".png")), exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(os.path.join(DST, "sprites", name + ".png"))
    MANIFEST["sprites"][name] = dict(file=f"sprites/{name}.png", w=int(x1 - x0), h=int(y1 - y0),
                                     ox=int(spr.ox - x0), oy=int(spr.oy - y0))
    if emit is not None:
        MANIFEST["sprites"][name]["emit"] = [int(round(emit[0])), int(round(emit[1]))]


# The Foundry's bodies on the field: (name, size) as the simulation has them (a «smaller» frame is a size less) and
# the scale each is drawn at — the frames by size (the demo's small Sage, Gun and Mechanic as before), the leaders and
# the Mason at their own.
GOLEM_K = {3: BT.GK[4] * 0.88, 4: BT.GK[4], 5: BT.GK[5], 6: BT.GK[6]}
FOUNDRY = [("Страж", 6), ("Страж", 5), ("Мудрец", 5), ("Мудрец", 4), ("Горн", 5), ("Горн", 4), ("Орудие", 5),
           ("Орудие", 4), ("Механик", 4), ("Механик", 3), ("Каменщик", 2), ("Отец колосса", 7), ("Изобретатель", 3),
           ("Маньяк", 4), ("Зодчий", 4)]
OWN_K = {"Каменщик": 0.85, "Отец колосса": 3.2, "Изобретатель": 1.05, "Маньяк": 1.3, "Зодчий": 1.05}
# the swarm's forms: the trait that makes each (swarm1.PLANS), the ant has none
FORMS = [("Муравей", ())] + [(nm, (tr,)) for tr, nm in W.PLANS.items()]
SWARM_LEADERS = ["Матка", "Разум улья", "Чума"]


def foundry_spec(name):
    """The builder's description of a body (golems_h for the frames and the Maniac and the Colossus, leaders_h for the
    Inventor and the Architect); None for the Guard (humanoid.py, no walk)."""
    if name == "Изобретатель":
        return LH.INVENTOR
    if name == "Зодчий":
        return LH.ZODCHIY
    return LH.GH.BY_NAME.get(name)


def foundry_build(name, pose, k):
    S = foundry_spec(name)
    if name == "Страж":
        return F.build(name, pose, k=k)
    return LH.GH.build(S, pose, k)


def units():
    """Every body a battle can show: the Foundry's frames, the Mason and the leaders (idle, attack — the casters'
    with the point their bolt leaves from — broken, four frames of a walk), each form of the swarm as worker and
    soldier in four variants (idle, attack, dead, two frames of a walk), the swarm's leaders (the Devourer at each
    growth step) and the larva."""
    for name, size in FOUNDRY:
        k = OWN_K.get(name, GOLEM_K.get(size))
        S = foundry_spec(name)
        key = f"{name}_{size}"
        for pose in ("idle", "attack", "broken"):
            if pose == "attack" and S is not None and "cast" in S["poses"]:
                # a caster: the game draws the bolt from the ball of the staff / the prongs to the target (emit)
                _, info = LH.GH.creature_parts(S, S["poses"]["cast"], fx=False)
                tip = info["n"].get("tip", info["n"].get("muzzle"))
                save_sprite(f"{key}_{pose}", foundry_build(name, "cast", k), emit=F.to_screen(tip, k))
                continue
            save_sprite(f"{key}_{pose}", foundry_build(name, pose, k))
        if S is not None:                                    # the Guard (humanoid.py) has no walk: it glides
            for i in range(4):
                S["poses"][f"walk{i}"] = LH.GH.walk_pose(S, i)
                save_sprite(f"{key}_walk{i}", foundry_build(name, f"walk{i}", k))
    for name, traits in FORMS:
        for caste, soldier in (("рабочая", False), ("солдат", True)):
            full = f"{name} ({caste})"
            for v in range(4):
                seed = 700 + v * 13 + len(full)
                hue = (-0.12, -0.04, 0.05, 0.12)[v]
                for pose in ("idle", "attack", "walk0", "walk1"):          # walk: the two tripods of legs in turn
                    save_sprite(f"{full}_{v}_{pose}", W.build(traits, hue, pose, soldier, k=1.0, genes=W.genes_for(seed)))
                save_sprite(f"{full}_{v}_dead", flip_dead(W.build(traits, hue, "idle", soldier, k=1.0, genes=W.genes_for(seed)), 0.3))
    for stage in range(3):
        for pose in ("idle", "attack", "walk0", "walk1"):
            save_sprite(f"Пожиратель_{stage}_{pose}", SL.build("Пожиратель", pose, 1.0, stage=stage))
        save_sprite(f"Пожиратель_{stage}_dead", flip_dead(SL.build("Пожиратель", "idle", 1.0, stage=stage), 0.3))
    for name in SWARM_LEADERS + ["личинка"]:
        key = "Личинка" if name == "личинка" else name
        for pose in ("idle", "attack", "walk0", "walk1"):
            save_sprite(f"{key}_{pose}", SL.build(name, pose, 1.0))
        save_sprite(f"{key}_dead", flip_dead(SL.build(name, "idle", 1.0), 0.3))


# the game's battlefield (sim/src/battle.rs W, H, ZONE; game/src/playback.rs X0, Y0): 1920x1080 art pixels
FIELD = dict(ww=1920, hh=1080, cols=36, rows=30, zone=15, x0=60, y0=46)


def ground():
    sc = Scene(FIELD["ww"], FIELD["hh"])
    BT.ground(sc, **FIELD)
    Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8), "RGB").save(os.path.join(DST, "ground.png"))


def fx():
    """The effects as sheets: frames of one size side by side, the pivot, the frame rate; the long explosion
    thinned to every third frame and cut where its smoke has gone."""
    os.makedirs(os.path.join(DST, "fx"), exist_ok=True)
    for name, step, cut in (("hit-spark", 1, None), ("zap-hit", 1, None), ("small-explosion", 3, 120), ("heal", 2, None)):
        frames_, meta = pxfx.load(name)
        frames_ = frames_[:cut:step] if cut else frames_[::step]
        h, w = frames_[0].shape[:2]
        sheet = np.zeros((h, w * len(frames_), 4), np.uint8)
        for i, f in enumerate(frames_):
            sheet[:, i * w:(i + 1) * w, :3] = np.clip(f[..., :3], 0, 255).astype(np.uint8)
            sheet[:, i * w:(i + 1) * w, 3] = np.clip(f[..., 3] * 255, 0, 255).astype(np.uint8)
        Image.fromarray(sheet, "RGBA").save(os.path.join(DST, "fx", name + ".png"))
        MANIFEST["fx"][name] = dict(file=f"fx/{name}.png", w=w, h=h, frames=len(frames_), pivot=meta["pivot"],
                                    fps=meta["fps"] / step)


CHARS = ("".join(chr(c) for c in range(32, 127)) + "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
         "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" + "×—–«»·…−½№→⇒✕")


def fonts():
    """Bitmap fonts: each glyph rendered at its size, one bit (the fonts are pixel fonts), in one atlas row by
    row; per glyph where it is, its width and its advance. Drawn with its top at the given y, like the art's."""
    os.makedirs(os.path.join(DST, "fonts"), exist_ok=True)
    for key, file, px in (("text16", "unifont-18.0.01.otf", 16), ("title16", "PressStart2P-Regular.ttf", 16),
                          ("title24", "PressStart2P-Regular.ttf", 24)):
        ft = ImageFont.truetype(os.path.join(HERE, "fonts", file), px)
        lh = px + px // 2
        cells, glyphs = [], {}
        for ch in CHARS:
            adv = int(round(ft.getlength(ch)))
            if adv <= 0:
                continue
            im = Image.new("L", (adv + px, lh), 0)
            ImageDraw.Draw(im).text((0, 0), ch, font=ft, fill=255)
            a = (np.asarray(im) > 110).astype(np.uint8) * 255
            cells.append((ch, a, adv))
        cols = 32
        cw = max(a.shape[1] for _, a, _ in cells)
        rows = (len(cells) + cols - 1) // cols
        atlas = np.zeros((rows * lh, cols * cw), np.uint8)
        for i, (ch, a, adv) in enumerate(cells):
            x, y = (i % cols) * cw, (i // cols) * lh
            atlas[y:y + lh, x:x + a.shape[1]] = a
            glyphs[ch] = [x, y, int(a.shape[1]), adv]
        Image.fromarray(atlas, "L").save(os.path.join(DST, "fonts", key + ".png"))
        MANIFEST["fonts"][key] = dict(file=f"fonts/{key}.png", line=lh, glyphs=glyphs)


def ui():
    """The battle HUD's pieces: the swarm's thin wing, its buttons (3-slices from the engine kit), the tug of war
    all swarm and all Foundry (the game cuts them at the share), the crown, a meter's scales, the end plates."""
    os.makedirs(os.path.join(DST, "ui"), exist_ok=True)
    kit = os.path.join(HERE, "assets", "ui_kit", "swarm")
    kj = json.load(open(os.path.join(kit, "kit.json")))["pieces"]
    for name in ("wing_battle_960", "wing_battle_1280", "button_chitin_22", "button_amber_22", "crown", "scale_over",
                 "scale_eat", "scale_dim", "scale_ok", "end_plate_win", "end_plate_lose", "lantern_on", "lantern_off"):
        shutil.copy(os.path.join(kit, kj[name]["file"]), os.path.join(DST, "ui", name + ".png"))
        MANIFEST["ui"][name] = dict(kj[name], file=f"ui/{name}.png")
    for share, nm in ((1.0, "tug_swarm"), (0.0, "tug_foundry")):
        sc = Scene(392, 15)                                  # room either side for the seam's sparks
        sc.rgb[:] = 0
        SH.tug(sc, 8, 0, 384, 15, share)
        m = UI.chamfer_mask(sc, 8, 0, 384, 15, 4)
        rgba = np.dstack((np.clip(sc.rgb, 0, 255).astype(np.uint8), m.astype(np.uint8) * 255))[:, 8:384]
        Image.fromarray(rgba, "RGBA").save(os.path.join(DST, "ui", nm + ".png"))
        MANIFEST["ui"][nm] = dict(file=f"ui/{nm}.png", size=[376, 15])


def kits():
    """Both engine kits whole (tools/sprites/assets/ui_kit/{foundry,swarm}: plates, cells, buttons, tags, levers,
    sills, wings…) under ui/foundry/… and ui/swarm/…, each with its slicing; the icon atlases (the Foundry's modules,
    the swarm's traits and mutations, the Foundry's glyphs) under icons/, with where each icon is."""
    for kit in ("foundry", "swarm"):
        src = os.path.join(HERE, "assets", "ui_kit", kit)
        kj = json.load(open(os.path.join(src, "kit.json")))["pieces"]
        os.makedirs(os.path.join(DST, "ui", kit), exist_ok=True)
        for name, meta in kj.items():
            if not isinstance(meta, dict) or "file" not in meta or not meta["file"].endswith(".png"):
                continue
            f = os.path.join(src, meta["file"])
            if not os.path.isfile(f):
                continue
            shutil.copy(f, os.path.join(DST, "ui", kit, name + ".png"))
            MANIFEST["ui"][f"{kit}/{name}"] = dict({k: v for k, v in meta.items() if k in ("size", "slice", "tile_x", "tile_y", "mode", "pad")},
                                                   file=f"ui/{kit}/{name}.png")
    os.makedirs(os.path.join(DST, "icons"), exist_ok=True)
    MANIFEST["icons"] = {}
    for key, png, idx in (("module", "module_icons.png", "module_icons.json"), ("swarm", "swarm_icons.png", "swarm_icons.json")):
        shutil.copy(os.path.join(HERE, "assets", png), os.path.join(DST, "icons", png))
        j = json.load(open(os.path.join(HERE, "assets", idx)))
        cell = j.get("cell", 16)
        for name, v in j["icons"].items():
            cx, cy = v["cell"]
            MANIFEST["icons"][f"{key}/{name}"] = dict(atlas=f"icons/{png}", rect=[cx * cell, cy * cell, cell, cell], name=v.get("name", ""))
    g = json.load(open(os.path.join(HERE, "assets", "ui_kit", "foundry", "glyphs.json")))
    shutil.copy(os.path.join(HERE, "assets", "ui_kit", "foundry", g["image"]), os.path.join(DST, "icons", "glyphs.png"))
    for name, v in g["glyphs"].items():
        MANIFEST["icons"][f"glyph/{name}"] = dict(atlas="icons/glyphs.png", rect=[v["x"], v["y"], v["w"], v["h"]], name=v.get("name", ""))


def portraits():
    """Each body larger, for the cards of the screens between battles (a reward, the trader's goods, the army, the
    camp): about a hundred pixels tall for a golem, the swarm's forms as worker and soldier, its leaders."""
    import foundry_hud as FH
    for name, k in (("Страж", 2.3), ("Мудрец", 2.1), ("Горн", 2.1), ("Орудие", 2.0), ("Механик", 2.4)):
        save_sprite(f"portrait/{name}", F.build(name, "idle", k=k))
    save_sprite("portrait/Каменщик", LH.GH.build(LH.GH.BY_NAME["Каменщик"], "idle", 2.4))
    for name, kind, k in (("Отец колосса", "colossus", 1.5), ("Изобретатель", "inventor", 2.6), ("Маньяк", "maniac", 2.2),
                          ("Зодчий", "zodchiy", 2.1)):
        save_sprite(f"portrait/{name}", FH.leader_sprite(kind, k))
    for name, traits in FORMS:
        for caste, soldier, k in (("рабочая", False, 4.2), ("солдат", True, 3.2)):
            save_sprite(f"portrait/{name} ({caste})", W.build(traits, 0.0, "idle", soldier, k=k, genes=W.genes_for(31 + len(name))))
    for name in ["Матка", "Разум улья", "Пожиратель", "Чума"]:
        spr = SL.build(name, "idle", 1.0)
        kk = min(2.2, 180 / spr.w, 110 / spr.h)
        save_sprite(f"portrait/{name}", SL.build(name, "idle", kk))


def main():
    os.makedirs(DST, exist_ok=True)
    UI.WOBBLE[0] = 0.0
    ground()
    units()
    portraits()
    fx()
    fonts()
    ui()
    kits()
    import bake_screens
    bake_screens.DST = DST
    bake_screens.main(write_manifest=False)
    MANIFEST["bg"] = bake_screens.MANIFEST["bg"]
    MANIFEST["ui"].update(bake_screens.MANIFEST["ui"])
    json.dump(MANIFEST, open(os.path.join(DST, "assets.json"), "w"), ensure_ascii=False, indent=1)
    print("sprites", len(MANIFEST["sprites"]), "fx", len(MANIFEST["fx"]), "fonts", len(MANIFEST["fonts"]),
          "ui", len(MANIFEST["ui"]), "icons", len(MANIFEST["icons"]), "bg", len(MANIFEST["bg"]))


if __name__ == "__main__":
    main()
