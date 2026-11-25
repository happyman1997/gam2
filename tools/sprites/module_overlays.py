"""The modules on the golems in battle. A golem's battle sprite is one picture a frame and pose; a module put on it in
the workshop shows over it as a layer of its own: the frame drawn with the module and without, in the same pose and
scale, and what changed between them — the module where it is seen, the body where the module covers it, nothing
where the body hides the module. Every module the run can put on a frame (finds.ron) that its builder draws
(frame_modules.py: the Sage, the Gun, the Mechanic in any pose; guard_modules.py: the Guard at rest), at each level.

battle_bake.bake calls bake(manifest): sprites/mod/<frame>_<size>_<module>_<level>_<pose>.png, each with its ground
point like the bodies' (the game lays it over the body's sprite of that pose).

    python3 tools/sprites/module_overlays.py      -> out/module_overlays.png (each frame with each module, idle, III)
"""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "..", "..", "game", "assets")

# the run's module keys (finds.ron) by frame, and the art's: the same keys
FOUNDRY_MODS = {"Мудрец": ("overload", "fireball"), "Орудие": ("mortar", "canister", "long"), "Механик": ("repair",),
                "Страж": ("intercept", "plates", "tower", "counter")}


def poses_of(name, S):
    """The poses the battle shows a frame in, as demo_bake bakes them: the caster's attack is its cast."""
    if S is None:
        return [("idle", None)]                                  # the Guard: its modules are built on it at rest
    out = [("idle", S["poses"]["idle"]), ("attack", S["poses"]["cast" if "cast" in S["poses"] else "attack"]),
           ("broken", S["poses"]["broken"])]
    import golems_h as GH
    for i in range(4):
        out.append((f"walk{i}", GH.walk_pose(S, i)))
    return out


def render_pair(name, key, t, A, k):
    """The frame in pose A with the module and without, rendered alike: (with, without) kit Sprites."""
    if name == "Страж":
        import guard_modules as GM
        import humanoid as HM
        from r3d import render
        from golem6 import STYLE1
        from golems_h import rim_light
        G, _ = GM.parts(key, t)
        G0, _ = HM.guard_idle(GM.P, **GM.MODULES[key][3])
        w, h, ox, oy = int(96 * k), int(86 * k), int(40 * k), int(76 * k)
        out = []
        for g in (G, G0):
            spr = rim_light(render(g.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
            spr.ox, spr.oy = ox, oy
            out.append(spr)
        return out
    import frame_modules as FM
    _, _, _, fn, over = FM.module(name, key)
    so = dict(over.get("S", {}))
    G, info, _ = FM.golem(name, A=dict(A, fx=None), **so)
    fn(G, info, t)
    G0, _, _ = FM.golem(name, A=dict(A, fx=None), **so)
    return FM.render_parts(G, name, k), FM.render_parts(G0, name, k)


def overlay(with_, without):
    """What the module changed: its pixels, cropped, and where the ground point falls in them; None if nothing."""
    a1, a0 = with_.a.astype(bool), without.a.astype(bool)
    diff = a1 & (~a0 | (np.abs(with_.rgb - without.rgb).sum(axis=2) > 8))
    if not diff.any():
        return None
    ys, xs = np.nonzero(diff)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    rgba[..., :3] = np.clip(with_.rgb[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    rgba[..., 3] = diff[y0:y1, x0:x1] * 255
    return rgba, int(with_.ox - x0), int(with_.oy - y0)


def bake(manifest, only=None):
    import demo_bake as DB
    sprites = manifest.setdefault("sprites", {})
    os.makedirs(os.path.join(DST, "sprites", "mod"), exist_ok=True)
    n = 0
    for name, size in DB.FOUNDRY:
        if name not in FOUNDRY_MODS or (only and name not in only):
            continue
        k = DB.OWN_K.get(name, DB.GOLEM_K.get(size))
        S = DB.foundry_spec(name)
        for pose, A in poses_of(name, S):
            for key in FOUNDRY_MODS[name]:
                for t in (1, 2, 3):
                    got = overlay(*render_pair(name, key, t, A, k))
                    if got is None:
                        continue
                    rgba, ox, oy = got
                    nm = f"mod/{name}_{size}_{key}_{t}_{pose}"
                    Image.fromarray(rgba, "RGBA").save(os.path.join(DST, "sprites", nm + ".png"))
                    sprites[nm] = dict(file=f"sprites/{nm}.png", w=rgba.shape[1], h=rgba.shape[0], ox=ox, oy=oy)
                    n += 1
    return n


if __name__ == "__main__":
    import sys
    import json
    from paths import out
    import demo_bake as DB
    # a look: each frame at rest with each of its modules at level III, the module layer over the battle sprite
    tiles = []
    seen = set()
    for name, size in DB.FOUNDRY:
        if name not in FOUNDRY_MODS or name in seen:
            continue
        seen.add(name)
        k = DB.OWN_K.get(name, DB.GOLEM_K.get(size)) * 2
        S = DB.foundry_spec(name)
        A = S["poses"]["idle"] if S is not None else None
        for key in FOUNDRY_MODS[name]:
            w, wo = render_pair(name, key, 3, A, k)
            o = overlay(w, wo)
            body = DB.foundry_build(name, "idle", k)
            im = np.zeros((body.h, body.w, 4), np.uint8)
            im[..., :3] = np.clip(body.rgb, 0, 255)
            im[..., 3] = body.a * 255
            base = Image.fromarray(im, "RGBA")
            if o:
                lay = Image.fromarray(o[0], "RGBA")
                base.alpha_composite(lay, (int(body.ox - o[1]), int(body.oy - o[2])))
            tiles.append(base.crop(base.getbbox()))
    W = sum(t.width + 8 for t in tiles) + 8
    H = max(t.height for t in tiles) + 16
    sheet = Image.new("RGBA", (W, H), (52, 46, 58, 255))
    x = 8
    for t in tiles:
        sheet.alpha_composite(t, (x, H - 8 - t.height))
        x += t.width + 8
    sheet.save(out("module_overlays.png"))
    print(out("module_overlays.png"))
