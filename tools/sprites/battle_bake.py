"""The battle's own pieces that the tech demo lacked, baked into game/assets next to demo_bake's: the ground of an
ordinary fight, an elite's and a boss's (tools/sprites/battle_ground.py), the state glyphs over
the heads (the concept's set, tools/sprites/swarm_status.py, and the states it had no glyph for: burning, stunned,
the Hive Mind's mark, blinded, hooked by the Puppeteer, the starving Devourer) and the flames on a burning body
(the concept's running torches, tools/sprites/swarm_fire.py).

demo_bake.main calls bake(MANIFEST); run alone it updates the assets already baked:

    python3 tools/sprites/battle_bake.py   -> game/assets/{ground*.png, icons/status.png, fx/burn-body.png, assets.json}
"""
import json
import os
import numpy as np
from PIL import Image
from kit import hexc
import swarm_status as ST

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "..", "..", "game", "assets")

C = dict(ST.C)
C.update(K=hexc("#5a1c10"), F=hexc("#f0a038"))

# the states the concept had no glyph for, in its manner: 7–9 art pixels, a dark outline, two or three tones
NEW = {
    # a tongue of fire: red outside, orange, a pale-yellow heart
    "burn": ["...oo...",
             "..oRo...",
             "..oRRo..",
             ".oRARRo.",
             ".oRAAaRo",
             "oRAayARo",
             "oRAyyARo",
             ".oRAARo.",
             "..oooo.."],
    # a spark of stars over a stunned head
    "stun": ["...o...",
             "..oYo..",
             ".oYyYo.",
             "oYyWyYo",
             ".oYyYo.",
             "..oYo..",
             "...o..."],
    # the Hive Mind's mark: a violet ring with its cross
    "mark": ["...ooo...",
             "..oPPPo..",
             ".oPo.oPo.",
             "oPPopoPPo",
             ".oPo.oPo.",
             "..oPPPo..",
             "...ooo..."],
    # blinded by the midges: a shut eye with its lashes
    "blind": ["..o.o.o..",
              ".oSoSoSo.",
              "oSSSSSSSo",
              ".oSSSSSo.",
              "..ooooo.."],
    # hooked by the Puppeteer: a barbed hook, sickly green
    "hook": ["...oo..",
             "..oGGo.",
             "..oGo..",
             "..oGo..",
             "oo.oGo.",
             "oGooGo.",
             ".oGGGo.",
             "..ooo.."],
    # the starving Devourer: an open maw with its teeth
    "hunger": [".ooooooo.",
               "oRRRRRRRo",
               "oRWRWRWRo",
               "okWkkkWko",
               "oRkWkWkRo",
               "oRRRRRRRo",
               ".ooooooo."],
}
GLYPHS = dict(ST.GLYPHS, **NEW)
# what the engine shows (game/src/playback.rs STATUS_GLYPHS) and its name for the Alt mode
STATUS = {"hunger": "Голод", "burn": "Горит", "stun": "Оглушён", "fear": "Испуг", "mark": "Метка Разума",
          "hook": "Зацеплен", "infected": "Заражён", "poison": "Яд", "blind": "Ослеплён", "glued": "Склеен",
          "web": "В паутине", "stall": "Сбой", "shred": "Броня разъедена"}
# drawn twice the concept's size: on the field a glyph of 9 art pixels reads as a speck behind the numbers
Z = 2
CELL = 12 * Z


def glyph_rgba(key):
    rows = GLYPHS[key]
    h, w = len(rows), max(len(r) for r in rows)   # a few of the concept's rows run a pixel long
    out = np.zeros((h, w, 4), np.uint8)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                out[j, i, :3] = np.clip(C[ch], 0, 255)
                out[j, i, 3] = 255
    return out


def status(manifest):
    """The glyphs in one atlas row, each pixel doubled, in a 24 px cell at its top left; an icon each: `status/<key>`."""
    keys = list(STATUS)
    atlas = np.zeros((CELL, CELL * len(keys), 4), np.uint8)
    manifest.setdefault("icons", {})
    for n, k in enumerate(keys):
        g = glyph_rgba(k).repeat(Z, axis=0).repeat(Z, axis=1)
        h, w = g.shape[:2]
        atlas[:h, n * CELL:n * CELL + w] = g
        manifest["icons"][f"status/{k}"] = dict(atlas="icons/status.png", rect=[n * CELL, 0, w, h], name=STATUS[k])
    os.makedirs(os.path.join(DST, "icons"), exist_ok=True)
    Image.fromarray(atlas, "RGBA").save(os.path.join(DST, "icons", "status.png"))


FIRE = [hexc("#7a1e08"), hexc("#d2480e"), hexc("#f08a20"), hexc("#ffc850"), hexc("#fff4c0")]


def flame_frame(t, w=14, h=20, seed=3):
    """Three tongues of fire standing on the bottom middle: each thick in its lower third and drawn up to a point that
    sways, coloured by how far a pixel is from its middle line and how high it is (a white-gold heart low down, gold,
    orange, red at the rim and the tip); their heights and sway follow the phase t (0..1), so the loop closes. Now and
    then a lick tears off the tallest tip."""
    out = np.zeros((h, w, 4), np.uint8)
    heat = np.full((h, w), -1.0)
    rnd = np.random.RandomState(seed)
    base = h - 1
    for i, (off, tall) in enumerate(((-0.24, 0.62), (0.0, 0.95), (0.24, 0.7))):
        ph = rnd.uniform(0, 1)
        hh = (h - 3) * tall * (0.82 + 0.18 * np.sin(2 * np.pi * (2 * t + ph)))
        cx = w / 2 + off * w
        hw0 = w * (0.2 if i == 1 else 0.16)
        for y in range(h):
            u = (base - y) / max(1.0, hh)
            if u < 0 or u > 1:
                continue
            sway = 1.6 * u ** 1.5 * np.sin(2 * np.pi * (t + ph) + u * 2.0)
            xc = cx + sway
            hw = hw0 * (np.sin(np.pi * min(1.0, u * 0.9 + 0.12)) ** 0.8) * (1 - u) ** 0.35
            for x in range(w):
                d = abs(x + 0.5 - xc) / max(0.6, hw)
                if d <= 1:
                    hv = (1 - d) * (1 - u) * 1.4
                    heat[y, x] = max(heat[y, x], hv)
        # a lick torn off the tall one, rising
        if i == 1:
            k = (t * 2) % 1
            ly = int(round(base - hh - 1 - k * 4))
            lx = int(round(cx + 1.6 * np.sin(2 * np.pi * (t + ph) + 2.0)))
            if 0 <= ly < h and 0 <= lx < w and k < 0.7:
                heat[ly, lx] = max(heat[ly, lx], 0.05)
    steps = ((0.85, FIRE[4]), (0.6, FIRE[3]), (0.35, FIRE[2]), (0.12, FIRE[1]), (0.0, FIRE[0]))
    for th, col in reversed(steps):
        sel = heat >= th
        out[sel, :3] = np.clip(col, 0, 255)
        out[sel, 3] = 255
    return out


def flames(manifest, n=8):
    frames = [flame_frame(k / n) for k in range(n)]
    h, w = frames[0].shape[:2]
    sheet = np.concatenate(frames, axis=1)
    os.makedirs(os.path.join(DST, "fx"), exist_ok=True)
    Image.fromarray(sheet, "RGBA").save(os.path.join(DST, "fx", "burn-body.png"))
    manifest.setdefault("fx", {})["burn-body"] = dict(file="fx/burn-body.png", w=w, h=h, frames=n, pivot=[w // 2, h - 1], fps=12.0)


def grounds():
    """The battlefield's ground for an ordinary fight, an elite's and a boss's (tools/sprites/battle_ground.py)."""
    import battle_ground as BG
    for theme, name in (("fight", "ground"), ("elite", "ground_elite"), ("boss", "ground_boss")):
        Image.fromarray(BG.ground(theme, **BG.FIELD), "RGB").save(os.path.join(DST, name + ".png"))


# the modules' effects (pixelfx, built by pxfx.py into tools/sprites/assets/fx): (name, every n-th frame, cut after)
MODULE_FX = (("fireball", 2, None), ("fire-breath", 2, 24), ("ground-slam", 3, 66), ("muzzle-shotgun", 2, 50),
             ("acid-splash", 3, 75), ("mana-burst", 2, None))


def module_fx(manifest):
    """The effects of what goes off in battle, as demo_bake's sheets: the Sage's fireball in flight, the Forge's
    flame, the Colossus's quake, the Gun's grapeshot, the spitter's gob bursting, the firefly's flash."""
    import pxfx
    os.makedirs(os.path.join(DST, "fx"), exist_ok=True)
    for name, step, cut in MODULE_FX:
        frames_, meta = pxfx.load(name)
        frames_ = frames_[:cut:step] if cut else frames_[::step]
        h, w = frames_[0].shape[:2]
        sheet = np.zeros((h, w * len(frames_), 4), np.uint8)
        for i, f in enumerate(frames_):
            sheet[:, i * w:(i + 1) * w, :3] = np.clip(f[..., :3], 0, 255).astype(np.uint8)
            sheet[:, i * w:(i + 1) * w, 3] = np.clip(f[..., 3] * 255, 0, 255).astype(np.uint8)
        Image.fromarray(sheet, "RGBA").save(os.path.join(DST, "fx", name + ".png"))
        manifest.setdefault("fx", {})[name] = dict(file=f"fx/{name}.png", w=w, h=h, frames=len(frames_), pivot=meta["pivot"],
                                                   fps=meta["fps"] / step)


def bake(manifest):
    grounds()
    status(manifest)
    flames(manifest)
    module_fx(manifest)


if __name__ == "__main__":
    path = os.path.join(DST, "assets.json")
    m = json.load(open(path))
    bake(m)
    json.dump(m, open(path, "w"), ensure_ascii=False, indent=1)
    print("status", sum(1 for k in m["icons"] if k.startswith("status/")), "fx", len(m["fx"]))
