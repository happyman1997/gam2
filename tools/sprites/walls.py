"""The Architect's walls on the field (Чертёж, Кладка стены): a block of masonry that holds one cell — a front of stones
laid in courses, a lit top with three merlons, a timber beam bolted across with bronze, chips, a crack, moss at the
foot — four of them laid differently (the game picks one by the wall's number), and the heap of stones a broken one
leaves. Drawn stone by stone: each its own width and tone, lit from the top left, mortar dark between.

battle_bake.bake calls bake(manifest): sprites/Стена_<0..3>_idle.png and Стена_<0..3>_dead.png with their ground
points, like the swarm's bodies (render.rs draws a wall by that name).

    python3 tools/sprites/walls.py      -> game/assets/sprites/Стена_*.png, assets.json; out/walls.png (a look, ×4)
"""
import json
import os
import numpy as np
from PIL import Image
from kit import hexc

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "..", "..", "game", "assets")

OUT = hexc("#1c161e")
MORTAR = hexc("#2d2632")
# the stones: dark to lit, a cold grey with a little warmth in it
STONE = [hexc("#433b49"), hexc("#5b5262"), hexc("#756c7c"), hexc("#938a97"), hexc("#b4abb4")]
TOP = [hexc("#7d7482"), hexc("#a39aa5"), hexc("#c7bec4")]
WOOD = [hexc("#3a2416"), hexc("#5e3a22"), hexc("#7f5330")]
BRONZE = [hexc("#6a4418"), hexc("#b07a2a"), hexc("#e8b860")]
MOSS = [hexc("#2e4a1e"), hexc("#4c6e26")]
DIRT = hexc("#2a2018")

W, H = 46, 44          # the sprite
FRONT = 26             # the front face's height under the top
TOPH = 8               # the top face's depth
MER = 7                # the merlons' height over the top


def wall(k):
    """Block `k` of wall (0–3, each laid its own way: 0 plain, 1 a merlon broken off, 2 an arrow slit and two merlons,
    3 an iron cramp instead of the beam): an RGBA array H×W and its ground point (bottom middle)."""
    seed = k * 13 + 5
    rnd = np.random.RandomState(seed)
    img = np.zeros((H, W, 4), np.float32)

    def put(x, y, c, a=1.0):
        if 0 <= x < W and 0 <= y < H:
            img[y, x, :3] = c
            img[y, x, 3] = a

    x0, x1 = 3, W - 3                   # the front's sides
    fy1 = H - 2                         # its foot
    fy0 = fy1 - FRONT                   # its top edge (where the top face meets it)
    ty0 = fy0 - TOPH                    # the top face's far edge
    # the top face: lit, flagstones in two rows, a little narrower at the back (it goes away from us)
    for y in range(ty0, fy0):
        inset = (fy0 - y) // 4
        for x in range(x0 + inset, x1 - inset):
            put(x, y, TOP[1])
    for y in (ty0, ty0 + TOPH // 2):
        for x in range(x0, x1):
            if img[y, x, 3] > 0:
                put(x, y, TOP[0])
    xx = x0 + rnd.randint(3, 8)
    while xx < x1 - 2:
        for y in range(ty0 + 1, fy0):
            if img[y, xx, 3] > 0:
                put(xx, y, TOP[0])
        xx += rnd.randint(7, 12)
    for x in range(x0 + 1, x1 - 1):        # the lit lip along the front edge
        put(x, fy0 - 1, TOP[2])
    # the merlons: three blocks standing on the top, each a little front and a lit cap
    slots = [x0 + 2, (x0 + x1) // 2 - 4, x1 - 10] if k != 2 else [x0 + 4, x1 - 13]
    for n, sx in enumerate(slots):
        w = 8 + rnd.randint(0, 2) + (2 if k == 2 else 0)
        my1 = ty0 + 3
        mer = MER - 4 if (k == 1 and n == 1) else MER      # knocked off by a stone: a stump with a jagged top
        if mer < MER:
            for x in range(sx, sx + w):
                jag = (x * 5 + seed) % 3
                for y in range(my1 - mer - jag, my1):
                    put(x, y, STONE[2] if y > my1 - mer - jag else TOP[1])
                put(x, my1 - mer - jag - 1, OUT)
            for y in range(my1 - mer - 2, my1 + 1):
                put(sx - 1, y, OUT)
                put(sx + w, y, OUT)
            continue
        for y in range(my1 - MER, my1):
            for x in range(sx, sx + w):
                put(x, y, STONE[2] if y > my1 - MER + 2 else TOP[1])
        for x in range(sx, sx + w):
            put(x, my1 - MER, TOP[2])
            put(x, my1, STONE[0])
        for y in range(my1 - MER, my1 + 1):
            put(sx - 1, y, OUT)
            put(sx + w, y, OUT)
            put(sx + w - 1, y, STONE[1] if y > my1 - MER else TOP[0])
        for x in range(sx - 1, sx + w + 1):
            put(x, my1 - MER - 1, OUT)
    # the front: courses of stones, each its own width and tone, staggered
    y = fy0
    course = 0
    while y < fy1:
        h = 5 if course % 2 == 0 else 4
        h = min(h, fy1 - y)
        x = x0 - (rnd.randint(0, 5) if course % 2 else 0)
        while x < x1:
            w = rnd.randint(6, 12)
            tone = 2 + rnd.choice([-1, 0, 0, 0, 1])
            if course >= 4:
                tone = max(1, tone - 1)       # the lower courses in the dark of the ground
            for yy in range(y, y + h):
                for xx in range(max(x, x0), min(x + w, x1)):
                    c = STONE[tone]
                    if yy == y:
                        c = STONE[min(tone + 1, 4)]           # its top edge catches the light
                    elif yy == y + h - 1 or xx == min(x + w, x1) - 1:
                        c = STONE[max(tone - 1, 0)]           # its bottom and right edge in shadow
                    put(xx, yy, c)
                put(min(x + w, x1) - 1 + 1, yy, MORTAR)
            # a chip off a corner now and then
            if rnd.rand() < 0.25:
                put(max(x, x0), y, MORTAR)
            x += w + 1
        for xx in range(x0, x1):
            put(xx, y + h, MORTAR)
        y += h + 1
        course += 1
    # a crack running down from a seam
    cx = rnd.randint(x0 + 6, x1 - 6)
    cy = fy0 + rnd.randint(1, 5)
    for _ in range(rnd.randint(5, 9)):
        put(cx, cy, OUT)
        cy += 1
        cx += rnd.choice([-1, 0, 0, 1])
        if cy >= fy1:
            break
    # an arrow slit in the middle of the front: dark, its sill lit
    if k == 2:
        sx = (x0 + x1) // 2
        for y in range(fy0 + 3, fy0 + 13):
            put(sx, y, OUT)
            put(sx + 1, y, OUT)
        put(sx - 1, fy0 + 13, STONE[4])
        put(sx, fy0 + 13, STONE[4])
        put(sx + 1, fy0 + 13, STONE[4])
        put(sx + 2, fy0 + 13, STONE[4])
    # an iron cramp holding two stones together where the beam would be
    if k == 3:
        cy = fy0 + 10
        for x in range(x0 + 8, x0 + 18):
            put(x, cy, hexc("#2a2a34"))
            put(x, cy - 1, hexc("#6e6e7c"))
        for y in range(cy - 3, cy + 2):
            put(x0 + 8, y, hexc("#4a4a56"))
            put(x0 + 17, y, hexc("#4a4a56"))
    # the timber beam bolted across (the Architect builds with what is at hand), bronze bolts at its ends
    by = fy0 + 8 + rnd.randint(0, 4)
    for x in (range(x0 - 1, x1 + 1) if k != 3 else []):
        put(x, by - 1, OUT)
        put(x, by, WOOD[2] if (x * 7 + seed) % 9 else WOOD[1])
        put(x, by + 1, WOOD[1])
        put(x, by + 2, WOOD[0])
        put(x, by + 3, OUT)
    for bx in ((x0 + 2, x1 - 4) if k != 3 else ()):
        put(bx, by + 1, BRONZE[1])
        put(bx + 1, by + 1, BRONZE[0])
        put(bx, by, BRONZE[2])
    # moss and dirt at the foot
    for x in range(x0, x1):
        if rnd.rand() < 0.35:
            put(x, fy1 - 1, MOSS[rnd.randint(0, 2)])
            if rnd.rand() < 0.4:
                put(x, fy1 - 2, MOSS[0])
    for x in range(x0 - 1, x1 + 1):
        put(x, fy1, DIRT)
    # the outline: one dark pixel round everything that is not empty
    a = img[..., 3] > 0
    grown = a.copy()
    grown[1:] |= a[:-1]
    grown[:-1] |= a[1:]
    grown[:, 1:] |= a[:, :-1]
    grown[:, :-1] |= a[:, 1:]
    edge = grown & ~a
    img[edge, :3] = OUT
    img[edge, 3] = 1.0
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(img[..., :3], 0, 255)
    out[..., 3] = (img[..., 3] > 0) * 255
    return out, (W // 2, fy1)


def rubble(seed):
    """A broken wall: a low heap of its stones and a splinter of the beam, dust round the foot."""
    rnd = np.random.RandomState(seed + 100)
    w, h = W, 18
    img = np.zeros((h, w, 4), np.uint8)
    foot = h - 2
    stones = []
    for _ in range(14):
        sw, sh = rnd.randint(4, 9), rnd.randint(3, 6)
        sx = rnd.randint(3, w - sw - 3)
        # the heap is higher in the middle
        mid = 1 - abs(sx + sw / 2 - w / 2) / (w / 2)
        sy = foot - sh - int(rnd.rand() * 7 * mid)
        stones.append((sy, sx, sw, sh, 1 + rnd.randint(0, 3)))
    stones.sort()
    for sy, sx, sw, sh, tone in stones:
        for y in range(sy, sy + sh):
            for x in range(sx, sx + sw):
                c = STONE[tone]
                if y == sy:
                    c = STONE[min(tone + 1, 4)]
                elif y == sy + sh - 1 or x == sx + sw - 1:
                    c = STONE[max(tone - 1, 0)]
                img[y, x, :3] = c
                img[y, x, 3] = 255
        for x in range(sx - 1, sx + sw + 1):
            for y in (sy - 1, sy + sh):
                if 0 <= y < h and 0 <= x < w and img[y, x, 3] == 0:
                    img[y, x, :3] = OUT
                    img[y, x, 3] = 255
    # the splinter of the beam lying across
    y = foot - 4
    for x in range(8, 8 + rnd.randint(10, 16)):
        img[y, x, :3] = WOOD[1]
        img[y + 1, x, :3] = WOOD[0]
        img[y - 1, x, :3] = OUT
        img[y + 2, x, :3] = OUT
        img[y - 1:y + 3, x, 3] = 255
    for x in range(2, w - 2):
        if img[foot, x, 3] == 0 and rnd.rand() < 0.6:
            img[foot, x, :3] = DIRT
            img[foot, x, 3] = 255
    return img, (w // 2, foot)


def bake(manifest, dst=DST):
    sprites = manifest.setdefault("sprites", {})
    os.makedirs(os.path.join(dst, "sprites"), exist_ok=True)
    for k in range(4):
        for pose, (img, (ox, oy)) in (("idle", wall(k)), ("dead", rubble(k * 13 + 5))):
            name = f"Стена_{k}_{pose}"
            Image.fromarray(img, "RGBA").save(os.path.join(dst, "sprites", name + ".png"))
            sprites[name] = dict(file=f"sprites/{name}.png", w=img.shape[1], h=img.shape[0], ox=ox, oy=oy)


if __name__ == "__main__":
    from paths import out
    path = os.path.join(DST, "assets.json")
    m = json.load(open(path))
    bake(m)
    json.dump(m, open(path, "w"), ensure_ascii=False, indent=1)
    # a look: the four over the field's ground, a column of them as the blueprint stands them, and the rubble
    ground = Image.open(os.path.join(DST, "ground.png")).convert("RGBA").crop((600, 400, 860, 580))
    sheet = ground.copy()
    for k in range(4):
        img, (ox, oy) = wall(k)
        sheet.alpha_composite(Image.fromarray(img, "RGBA"), (10 + k * 50, 10))
        r, (rx, ry) = rubble(k * 13 + 5)
        sheet.alpha_composite(Image.fromarray(r, "RGBA"), (10 + k * 50, 70))
    for j in range(3):
        img, (ox, oy) = wall(j)
        sheet.alpha_composite(Image.fromarray(img, "RGBA"), (212, 20 + j * 34))
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(out("walls.png"))
    print(out("walls.png"))
