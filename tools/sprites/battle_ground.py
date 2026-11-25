"""The battlefield's ground, three of them: an ordinary fight (earth, tufts, pebbles, a few old bones), an elite's
(colder and stonier: slabs, rubble, cracks, the rust of old machines) and a boss's (scorched: ash, cinders smouldering
in the cracks, heaps of bones and chitin at the edges). Dark and low in contrast so the bodies read on it; the small
things on it — stones, bones, shards, scraps — drawn by hand pixel by pixel and scattered, each lit from the top
left. The cells' corners over each side's deployment zone stay marked faintly in its colour.

    python3 tools/sprites/battle_ground.py      -> out/ground_{fight,elite,boss}.png (a look at them)
"""
import os
import random
import numpy as np
from PIL import Image
from kit import hexc, BAYER
from noise import value_noise

CW, CH = 50, 34
FIELD = dict(ww=1920, hh=1080, cols=36, rows=30, zone=15, x0=60, y0=46)

THEMES = {
    # earth in four close tones (the old ground's), moss, the grey-violet of the pebbles
    "fight": dict(earth=("#262030", "#2a2334", "#2e2638", "#32293c"), dirt="#2a1e22", dust="#3a3044",
                  stone=("#5a5268", "#46405a", "#2e2a3a"), moss=("#2c3a3a", "#33443f", "#283432", "#3a4a44"),
                  tufts=2400, pebbles=900, stones=120, slabs=8, bones=26, skulls=3, shards=10, scraps=4, cracks=10,
                  scorch=0, embers=0),
    # colder, greyer stone; the rubble and the rust of the machines broken here before
    "elite": dict(earth=("#22222c", "#262632", "#2a2a36", "#2e2e3a"), dirt="#24202a", dust="#363644",
                  stone=("#646478", "#4c4c60", "#30303e"), moss=("#2a3434", "#30403c", "#263030", "#36443e"),
                  tufts=900, pebbles=1600, stones=300, slabs=40, bones=30, skulls=4, shards=14, scraps=40, cracks=46,
                  scorch=6, embers=0),
    # scorched: ash, cinders in the cracks, the bones and chitin of the beaten heaped at the edges
    "boss": dict(earth=("#221a20", "#261d23", "#2a2026", "#2e2329"), dirt="#2c1c1c", dust="#3a2e32",
                 stone=("#5c4c52", "#463840", "#2c2228"), moss=("#2a2a26", "#30302a", "#262420", "#363428"),
                 tufts=300, pebbles=1200, stones=200, slabs=26, bones=90, skulls=16, shards=60, scraps=24, cracks=60,
                 scorch=14, embers=1),
}

# the small things, by hand: L light (top left), M middle, D dark, o its shadow on the ground; bones B/b with k
# for holes; chitin C/c, its shine s; rust R/r, its bolt hole o
PEBBLES = [["LM", "MD"], [".LM.", "LMMD", ".DD."], ["LL.", "LMD", ".DD"]]
STONES = [["..LLM.", ".LMMMD", "LMMMDD", ".DDDD."],
          [".LLM..", "LMMMD.", "MMMMDD", ".DDDD."],
          ["..LM..", ".LMMD.", "LMMMMD", "MMMMDD", ".DDDD."]]
SLABS = [["..LLLLM...", ".LMMMMMMD.", "LMMMMMMMMD", ".DMMMMMDD.", "..DDDDDD.."],
         [".LLLLM.....", "LMMMMMMLM..", "MMMMMMMMMMD", ".DMMMMMMMDD", "..DDDDDDD.."],
         ["...LLM..", ".LLMMMD.", "LMMMMMMD", "MMMMMMDD", ".DDMMDD.", "...DD..."]]
TUFTS = [["..g..", "g.g.g", ".GgG."], ["g...", ".g.g", ".GG."], [".g.g.", "gGgGg"], ["g.", "Gg"]]
BONES = [["b.....b", ".bBBBb.", "b.....b"], ["b...", ".bB.", "..Bb", "...b"], ["bBBBBb"], [".b", "bB", "B.", "b."]]
SKULLS = [[".BBB.", "BkBkB", ".BBB.", ".b.b."], [".BBb", "BkBB", ".BBb"]]
SHARDS = [["..cC", ".cCs", "cCc."], ["cCC.", ".cCs", "..c."], [".cs", "cCc", "cc."]]
SCRAPS = [["rRRr..", ".rRRRr", "..rr.."], [".r.r.", "rRRRr", ".RoR.", "rRRRr", ".r.r."], ["rRr", "RoR", "rRr"],
          ["rRRRRr", "r....r"]]


def stamp(rgb, grid, x, y, pal, shadow=True):
    """A hand-drawn thing on the ground at (x, y), its shadow a pixel below and right."""
    h, w = len(grid), max(len(r) for r in grid)
    H, W = rgb.shape[:2]
    if shadow:
        for j, row in enumerate(grid):
            for i, ch in enumerate(row):
                if ch != "." and 0 <= y + j + 1 < H and 0 <= x + i + 1 < W:
                    rgb[y + j + 1, x + i + 1] *= 0.72
    for j, row in enumerate(grid):
        for i, ch in enumerate(row):
            if ch == "." or ch not in pal:
                continue
            if 0 <= y + j < H and 0 <= x + i < W:
                rgb[y + j, x + i] = pal[ch]


def crack(rgb, rnd, x, y, n, col, hot=None, ang=None):
    """A crack: a line that keeps its way with a little jitter, a pixel at a time, a branch now and then; darker than
    the ground, its near side catching a lighter pixel; cinders glowing in it now and then."""
    H, W = rgb.shape[:2]
    ang = rnd.uniform(0, 2 * np.pi) if ang is None else ang
    for k in range(n):
        ang += rnd.uniform(-0.22, 0.22)
        x += np.cos(ang)
        y += np.sin(ang) * 0.7
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= yi < H - 1 and 0 <= xi < W):
            break
        rgb[yi, xi] = hot if (hot is not None and rnd.random() < 0.2) else col
        rgb[yi + 1, xi] = rgb[yi + 1, xi] * 1.12
        if rnd.random() < 0.035 and n - k > 10:
            crack(rgb, rnd, x, y, (n - k) // 2, col, hot, ang + rnd.choice((-1, 1)) * rnd.uniform(0.5, 0.9))


def ground(theme="fight", ww=1920, hh=1080, cols=36, rows=30, zone=15, x0=60, y0=46):
    T = THEMES[theme]
    rnd = random.Random({"fight": 3, "elite": 5, "boss": 7}[theme])
    yy, xx = np.mgrid[0:hh, 0:ww]
    th = BAYER[yy % 4, xx % 4]
    # earth: four tones in big soft patches, dithered where they meet
    n1 = value_noise(ww, hh, 40, 1) * 0.55 + value_noise(ww, hh, 12, 2) * 0.3 + value_noise(ww, hh, 4, 9) * 0.15
    lv = np.clip(np.floor(n1 * 4 + (th - 0.5) * 1.1), 0, 3).astype(int)
    rgb = np.zeros((hh, ww, 3))
    for i, c in enumerate(T["earth"]):
        rgb[lv == i] = hexc(c)
    # the trodden strip down the no man's land, and dry dust in the low places
    n2 = value_noise(ww, hh, 30, 3) * 0.6 + value_noise(ww, hh, 8, 4) * 0.4
    mid = x0 + cols * CW / 2
    centre = np.exp(-((xx - mid - 34 * np.sin(yy / 70.0)) / 140.0) ** 2)
    dirt = (n2 * 0.8 + centre * 0.55 + (th - 0.5) * 0.15) > 0.82
    rgb[dirt] = rgb[dirt] * 0.8 + hexc(T["dirt"]) * 0.2
    n3 = value_noise(ww, hh, 60, 11)
    dust = (n3 + (th - 0.5) * 0.12) > 0.74
    rgb[dust] = rgb[dust] * 0.7 + hexc(T["dust"]) * 0.3
    # rises and hollows: the land's own lie, a slow light and dark across the field in a few steps
    lie = value_noise(ww, hh, 220, 31) * 0.7 + value_noise(ww, hh, 90, 32) * 0.3
    rgb *= (0.9 + 0.04 * np.floor(lie * 5 + (th - 0.5) * 0.8).clip(0, 4))[..., None]
    # clods: the earth's grain — a short lighter dash, the dark of its underside below it
    for _ in range(int(16000 * ww * hh / (1920 * 1080))):
        x, y, n = rnd.randrange(ww - 5), rnd.randrange(hh - 2), rnd.randint(2, 4)
        rgb[y, x:x + n] *= 1.1
        rgb[y + 1, x + 1:x + n + 1] *= 0.88
    # scorch: burnt ground with a ragged rim, a ring of pale ash round it
    rough = value_noise(ww, hh, 9, 21)
    for _ in range(T["scorch"]):
        cx, cy, r = rnd.uniform(0, ww), rnd.uniform(0, hh), rnd.uniform(26, 80)
        x_0, x_1, y_0, y_1 = int(max(0, cx - r * 1.5)), int(min(ww, cx + r * 1.5)), int(max(0, cy - r)), int(min(hh, cy + r))
        sub = (slice(y_0, y_1), slice(x_0, x_1))
        e = np.sqrt(((xx[sub] - cx) / r) ** 2 + ((yy[sub] - cy) / (r * 0.55)) ** 2) + (rough[sub] - 0.5) * 0.7
        rgb[sub][(e < 1.08) & (e >= 0.92) & (th[sub] < 0.5)] *= 1.18
        rgb[sub][e < 0.92] *= 0.82
        rgb[sub][e < 0.5] *= 0.9
    # cracks; in the boss's ground cinders smoulder in them
    for _ in range(T["cracks"]):
        crack(rgb, rnd, rnd.uniform(0, ww), rnd.uniform(0, hh), rnd.randint(14, 60), hexc("#16101a"),
              hexc("#a8401a") if T["embers"] else None)
    L, M, D = (hexc(c) for c in T["stone"])
    stone = dict(L=L, M=M, D=D)
    bone = dict(B=hexc("#a49a8c"), b=hexc("#6e665e"), k=hexc("#1a1418"))
    chit = dict(C=hexc("#4a3046"), c=hexc("#2e1e2c"), s=hexc("#8a6a8a"))
    rust = dict(R=hexc("#7a4a2c"), r=hexc("#4a2c1e"), o=hexc("#1c1416"))
    moss = [hexc(c) for c in T["moss"]]

    def anywhere(edge=0.0):
        """A place on the field; with edge > 0 mostly near its border (the heaps of the beaten)."""
        if edge and rnd.random() < edge:
            side = rnd.choice("lrtb")
            x = rnd.uniform(0, 140) if side == "l" else rnd.uniform(ww - 140, ww) if side == "r" else rnd.uniform(0, ww)
            y = rnd.uniform(0, 90) if side == "t" else rnd.uniform(hh - 90, hh) if side == "b" else rnd.uniform(0, hh)
            return int(x), int(y)
        return rnd.randrange(ww), rnd.randrange(hh)

    def clustered(n, spread, per=(5, 14), edge=0.0):
        """n places in clumps: a few heaps, thick in the middle, thinning out; a fifth of them on their own."""
        out = []
        while len(out) < n:
            if rnd.random() < 0.2:
                out.append(anywhere(edge))
                continue
            cx, cy = anywhere(edge)
            for _ in range(rnd.randint(*per)):
                r = spread * rnd.random() ** 1.6
                a = rnd.uniform(0, 2 * np.pi)
                out.append((int(cx + np.cos(a) * r), int(cy + np.sin(a) * r * 0.6)))
        return out[:n]

    for x, y in clustered(T["tufts"], 60, (8, 24)):
        if not (0 <= x < ww and 0 <= y < hh) or dirt[y, x]:
            continue
        g = rnd.choice(TUFTS)
        stamp(rgb, g, x, y, dict(g=rnd.choice(moss), G=rnd.choice(moss) * 0.85), shadow=False)
    for x, y in clustered(T["pebbles"], 46, (6, 18)):
        stamp(rgb, rnd.choice(PEBBLES), x, y, {k: v * rnd.uniform(0.85, 1.0) for k, v in stone.items()})
    for x, y in clustered(T["stones"], 40, (3, 8)):
        stamp(rgb, rnd.choice(STONES), x, y, {k: v * rnd.uniform(0.85, 1.0) for k, v in stone.items()})
    for _ in range(T["slabs"]):
        x, y = anywhere(0.5)
        stamp(rgb, rnd.choice(SLABS), x, y, {k: v * rnd.uniform(0.8, 0.95) for k, v in stone.items()})
    edge = 0.7 if theme == "boss" else 0.3
    for _ in range(T["scraps"]):
        x, y = anywhere(edge)
        stamp(rgb, rnd.choice(SCRAPS), x, y, rust)
    for _ in range(T["shards"]):
        x, y = anywhere(edge)
        stamp(rgb, rnd.choice(SHARDS), x, y, chit)
    for _ in range(T["bones"]):
        x, y = anywhere(edge)
        stamp(rgb, rnd.choice(BONES), x, y, {k: v * rnd.uniform(0.8, 1.0) for k, v in bone.items()})
    for _ in range(T["skulls"]):
        x, y = anywhere(edge)
        stamp(rgb, rnd.choice(SKULLS), x, y, bone)
    # specks
    for _ in range(int(9000 * ww * hh / (1920 * 1080))):
        x, y = rnd.randrange(ww), rnd.randrange(hh)
        rgb[y, x] *= rnd.choice((0.86, 1.14))
    # the edges sink into the dark, so the field reads as a place and the eye stays in the middle
    vx = np.minimum(xx, ww - 1 - xx) / 160.0
    vy = np.minimum(yy, hh - 1 - yy) / 110.0
    v = np.clip(np.minimum(vx, vy), 0, 1)
    shade = 0.72 + 0.28 * np.floor(v * 4 + (th - 0.5) * 0.9).clip(0, 4) / 4
    rgb *= shade[..., None]
    # the cells' corners over each side's deployment zone
    for c in range(cols + 1):
        for r in range(rows + 1):
            x, y = x0 + c * CW, y0 + r * CH
            left, right = c <= zone, c >= cols - zone
            if not (left or right) or not (0 <= x < ww and 0 <= y < hh):
                continue
            col = hexc("#c9b27a") if left else hexc("#9a8ab8")
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                if 0 <= x + dx < ww and 0 <= y + dy < hh:
                    rgb[y + dy, x + dx] = rgb[y + dy, x + dx] * 0.75 + col * 0.25
    return np.clip(rgb, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    from paths import out
    for t in THEMES:
        Image.fromarray(ground(t), "RGB").save(out(f"ground_{t}.png"))
        print(out(f"ground_{t}.png"))
