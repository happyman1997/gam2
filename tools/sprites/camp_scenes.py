"""The pictures on the camp's two cards, one pair a class, drawn from the game's own bodies and effects instead of a
lone icon: the Foundry's Ремонт (the Mechanic welding a broken Guard back together, sparks flying) and Закалка (a
golem glowing from the quench, steam rolling off it by the anvil); the swarm's Кладка (the Mother over a clutch of
eggs, larvae wriggling out) and Отбор (one bred bug in the middle, lit, the plain ones round it dim).

battle_bake.bake calls bake(manifest, dst): ui/camp_{rest,up}_{0,1}.png, 260×128, transparent.

    python3 tools/sprites/camp_scenes.py      -> out/camp_scenes.png (the four on the cards' colours, ×2)
"""
import os
import numpy as np
from PIL import Image
from kit import hexc

W, H = 260, 128


class Pic:
    """A transparent picture being put together: bodies laid by their ground point, effects by their pivot, light."""

    def __init__(self):
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), np.float32)

    def put(self, spr, x, y, flip=False, tint=None, k=1.0):
        """A kit Sprite with its ground point at (x, y); tint=(colour, amount) heats or dims it."""
        rgb, a = spr.rgb, spr.a.astype(np.float32)
        ox = spr.ox
        if flip:
            rgb, a, ox = rgb[:, ::-1], a[:, ::-1], spr.w - 1 - spr.ox
        x0, y0 = int(round(x - ox)), int(round(y - spr.oy))
        self._lay(rgb, a * k, x0, y0, tint)

    def fx(self, frame, x, y, pivot, k=1.0):
        """A pixelfx frame (float RGBA, alpha 0..1) with its pivot at (x, y)."""
        self._lay(frame[..., :3], frame[..., 3] * k, int(round(x - pivot[0])), int(round(y - pivot[1])), None)

    def _lay(self, rgb, a, x0, y0, tint):
        h, w = a.shape
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
        if xb <= xa or yb <= ya:
            return
        src = rgb[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
        if tint is not None:
            col, amt = tint
            src = src * (1 - amt) + np.asarray(col, np.float32) * amt
        al = a[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
        reg = self.rgb[ya:yb, xa:xb]
        self.rgb[ya:yb, xa:xb] = reg * (1 - al) + src * al
        self.a[ya:yb, xa:xb] = np.maximum(self.a[ya:yb, xa:xb], al[..., 0])

    def glow(self, cx, cy, r, col, k):
        """Light round a point: on what is there it brightens, on the empty card it is a soft halo of its own."""
        yy, xx = np.mgrid[0:H, 0:W]
        g = np.clip(1 - np.hypot(xx - cx, yy - cy) / r, 0, 1) ** 2 * k
        col = np.asarray(col, np.float32)
        self.rgb = self.rgb + col * g[..., None] * (self.a[..., None] > 0)
        halo = g * (self.a == 0)
        lvl = np.floor(halo * 4) / 4                           # in steps, not a smooth airbrush
        sel = lvl > 0
        self.rgb[sel] = col * 0.55
        self.a[sel] = np.maximum(self.a[sel], lvl[sel] * 0.6)

    def shadow(self, cx, cy, rx, ry):
        yy, xx = np.mgrid[0:H, 0:W]
        sel = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
        self.rgb[sel] *= np.where(self.a[sel] > 0, 0.6, 1.0)[..., None]
        empty = sel & (self.a == 0)
        self.rgb[empty] = (12, 8, 14)
        self.a[empty] = 0.45

    def image(self):
        out = np.zeros((H, W, 4), np.uint8)
        out[..., :3] = np.clip(self.rgb, 0, 255)
        out[..., 3] = np.clip(self.a * 255, 0, 255)
        return Image.fromarray(out, "RGBA")


def heat(spr):
    """A golem fresh from the quench: its upper, lit side glowing orange-hot, cooling to its own iron below."""
    import copy
    s = copy.deepcopy(spr)
    rows = np.nonzero(s.a.any(axis=1))[0]
    top, bot = rows.min(), rows.max()
    for y in range(top, bot + 1):
        t = max(0.0, 1 - (y - top) / max(1, (bot - top) * 0.7))
        lit = s.a[y] & (s.rgb[y].sum(axis=1) > 260)                     # only the lit faces glow
        s.rgb[y][lit] = s.rgb[y][lit] * (1 - 0.4 * t) + np.array((255, 150, 60)) * 0.4 * t
    return s


def egg(pic, x, y):
    for dy in range(-3, 4):
        for dx in range(-2, 3):
            if (dx / 2.4) ** 2 + (dy / 3.4) ** 2 <= 1 and 0 <= y + dy < H and 0 <= x + dx < W:
                c = hexc("#fff4dc") if dx < 0 and dy < -1 else hexc("#e8dcb4") if dx + dy < 3 else hexc("#b8a882")
                pic.rgb[y + dy, x + dx] = c
                pic.a[y + dy, x + dx] = 1
    for dy in range(-4, 5):                                    # its dark rim
        for dx in range(-3, 4):
            if 0 <= y + dy < H and 0 <= x + dx < W and pic.a[y + dy, x + dx] == 0 and (dx / 3.2) ** 2 + (dy / 4.2) ** 2 <= 1:
                pic.rgb[y + dy, x + dx] = (26, 20, 16)
                pic.a[y + dy, x + dx] = 1


def scenes():
    import demo_bake as DB
    import frames as F
    import swarm_leaders as SL
    import swarm1 as SW
    import pxfx
    out = {}
    # the Foundry's Ремонт: the Mechanic at a broken Guard, the weld throwing sparks
    p = Pic()
    p.shadow(170, 120, 54, 8)
    p.shadow(84, 120, 30, 6)
    guard = DB.foundry_build("Страж", "broken", 1.5)
    p.put(guard, 170, 120, flip=True)
    p.put(DB.foundry_build("Механик", "attack", 1.7), 84, 120)
    sp, meta = pxfx.load("hit-spark")
    p.fx(sp[2], 140, 96, meta["pivot"])
    p.glow(140, 92, 30, (255, 200, 110), 0.5)
    out["camp_rest_0"] = p
    # Закалка: a golem hot from the quench by the anvil, steam rolling off it
    p = Pic()
    p.shadow(150, 118, 42, 7)
    p.put(heat(DB.foundry_build("Страж", "idle", 1.25)), 150, 118)
    st, meta = pxfx.load("valve-steam")
    for x, f in ((122, 10), (170, 16), (146, 22)):
        p.fx(st[f % len(st)], x, 70, meta["pivot"], k=0.8)
    anvil = Image.open(os.path.join(os.path.dirname(__file__), "..", "..", "game", "assets", "ui", "anvil.png")).convert("RGBA")
    av = np.asarray(anvil).astype(np.float32)
    p._lay(av[..., :3], av[..., 3] / 255.0, 30, 118 - av.shape[0], None)
    p.glow(150, 70, 60, (255, 120, 40), 0.35)
    out["camp_up_0"] = p
    # the swarm's Кладка: the Mother over her clutch, larvae wriggling out of it
    p = Pic()
    p.shadow(176, 116, 56, 8)
    mother = SL.build("Матка", "idle", 0.66)
    p.put(mother, 252 - (mother.w - mother.ox), 116, flip=True)
    p.glow(66, 106, 40, (150, 230, 70), 0.25)
    for x, y in ((52, 104), (62, 110), (70, 103), (80, 111), (46, 112), (90, 105), (58, 98), (72, 114)):
        egg(p, x, y)
    for x, y, fl in ((104, 118, False), (30, 120, True), (116, 110, False)):
        p.put(SL.build("личинка", "walk0", 1.5), x, y, flip=fl)
    out["camp_rest_1"] = p
    # Отбор: one bred bug in the middle, lit; the plain ones round it, dim
    p = Pic()
    for x, y, tr, g in ((52, 114, (), 31), (210, 114, (), 37), (90, 104, ("stinger",), 41), (172, 104, ("horn",), 43)):
        p.put(SW.build(tr, 0.0, "idle", False, k=1.6, genes=SW.genes_for(g)), x, y, flip=x > 130, tint=((20, 16, 24), 0.45))
    p.shadow(131, 118, 34, 6)
    p.put(SW.build(("wings",), 0.0, "attack", True, k=2.4, genes=SW.genes_for(7)), 131, 118)
    p.glow(131, 92, 52, (160, 240, 80), 0.4)
    out["camp_up_1"] = p
    return out


def bake(manifest, dst):
    os.makedirs(os.path.join(dst, "ui"), exist_ok=True)
    for name, pic in scenes().items():
        pic.image().save(os.path.join(dst, "ui", name + ".png"))
        manifest.setdefault("ui", {})[name] = dict(file=f"ui/{name}.png", size=[W, H])


if __name__ == "__main__":
    from paths import out
    sc = scenes()
    sheet = Image.new("RGBA", (W * 2 + 30, H * 2 + 30), (40, 30, 46, 255))
    for i, (name, pic) in enumerate(sc.items()):
        bg = Image.new("RGBA", (W, H), ((54, 40, 30, 255) if name.endswith("0") else (34, 40, 30, 255)))
        bg.alpha_composite(pic.image())
        sheet.paste(bg, (10 + (i % 2) * (W + 10), 10 + (i // 2) * (H + 10)))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out("camp_scenes.png"))
    print(out("camp_scenes.png"))
