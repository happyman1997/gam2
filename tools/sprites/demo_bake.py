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


def save_sprite(name, spr):
    """A kit Sprite as an RGBA PNG cropped to what it covers; the pivot moved with the crop."""
    ys, xs = np.nonzero(spr.a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    rgba[..., :3] = np.clip(spr.rgb[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    rgba[..., 3] = spr.a[y0:y1, x0:x1] * 255
    os.makedirs(os.path.join(DST, "sprites"), exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(os.path.join(DST, "sprites", name + ".png"))
    MANIFEST["sprites"][name] = dict(file=f"sprites/{name}.png", w=int(x1 - x0), h=int(y1 - y0),
                                     ox=int(spr.ox - x0), oy=int(spr.oy - y0))


def units():
    """The Inventor's golems and himself (idle, attack, broken), the Devourer's ants and grasshoppers in four
    variants each (idle, attack, dead), the Devourer at each growth step (idle, attack, dead)."""
    for name, k in (("Мудрец", BT.GK[4]), ("Орудие", BT.GK[4]), ("Механик", BT.GK[4] * 0.88)):
        for pose in ("idle", "attack", "broken"):
            save_sprite(f"{name}_{pose}", F.build(name, pose, k=k))
    for pose in ("idle", "attack", "broken"):
        save_sprite(f"Изобретатель_{pose}", LH.GH.build(LH.INVENTOR, pose, 1.05))
    for name, traits, soldier in (("Муравей (рабочая)", (), False), ("Муравей (солдат)", (), True),
                                  ("Кузнечик (рабочая)", ("jumper",), False)):
        for v in range(4):
            seed = 700 + v * 13 + len(name)
            hue = (-0.12, -0.04, 0.05, 0.12)[v]
            for pose in ("idle", "attack"):
                save_sprite(f"{name}_{v}_{pose}", W.build(traits, hue, pose, soldier, k=1.0, genes=W.genes_for(seed)))
            save_sprite(f"{name}_{v}_dead", flip_dead(W.build(traits, hue, "idle", soldier, k=1.0, genes=W.genes_for(seed)), 0.3))
    for stage in range(3):
        for pose in ("idle", "attack"):
            save_sprite(f"Пожиратель_{stage}_{pose}", SL.build("Пожиратель", pose, 1.0, stage=stage))
        save_sprite(f"Пожиратель_{stage}_dead", flip_dead(SL.build("Пожиратель", "idle", 1.0, stage=stage), 0.3))


def ground():
    sc = Scene(BT.WW, BT.HH)
    BT.ground(sc)
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


def main():
    os.makedirs(DST, exist_ok=True)
    UI.WOBBLE[0] = 0.0
    ground()
    units()
    fx()
    fonts()
    ui()
    json.dump(MANIFEST, open(os.path.join(DST, "assets.json"), "w"), ensure_ascii=False, indent=1)
    print("sprites", len(MANIFEST["sprites"]), "fx", len(MANIFEST["fx"]), "fonts", len(MANIFEST["fonts"]),
          "ui", len(MANIFEST["ui"]))


if __name__ == "__main__":
    main()
