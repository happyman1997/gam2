"""The interface on other screens: the art's canvas is 960×540 at ×2 (1920×1080); on 2560×1440 at ×2 it is
1280×720, on a 16:10 screen 960×600 (and the scale chosen in the settings moves it too). The screens are not
stretched: they are laid out again by one rule — what is at an edge stays pinned to that edge, the panels in
between grow (they are 9-slices), and the drawing in the middle gets a bigger sheet with the golem centred on it.

Here the workshop is laid out that way from its 960×540 render, region by region:

  the beam      — drawn the full width; the purse pinned left, the title and its spanners centred, Alt/«?» pinned right;
  the rack      — pinned left and top: more height is room for more golems;
  the panel     — pinned right and top, its plate grown to the new height;
  the drawing   — its plate and its blueprint sheet grown, the slipway centred on the sheet (shifted by whole cells of
                  the grid, so the grid's lines run on);
  the console   — drawn the full width; the push-buttons pinned left, the big lever pinned right.

    python3 tools/sprites/wide.py    -> out/foundry_wide.png (the three side by side, and the rule drawn over)
"""
import numpy as np
from PIL import Image
from kit import Scene, hexc
import foundry_ui as FU
import foundry_hud as FH
from swarm_ui import letters
from paths import out


def base():
    """The 960×540 workshop at the art's own scale (from its ×2 render)."""
    im = Image.open(out("foundry_workshop.png")).convert("RGB")
    return np.asarray(im.resize((960, 540), Image.NEAREST)).astype(np.float32)


def paste(sc, src, x0, y0, x1, y1, dx, dy):
    """Copy src[y0:y1, x0:x1] into the scene at (dx, dy)."""
    sc.rgb[dy:dy + (y1 - y0), dx:dx + (x1 - x0)] = src[y0:y1, x0:x1]


def layout(W, H):
    src = base()
    sc = FU.forge(W, H, 11)
    # the beam
    FU.wing(sc, 0, 0, W, 44)
    paste(sc, src, 0, 0, 120, 41, 0, 0)                                       # the purse
    paste(sc, src, 286, 0, 676, 41, W // 2 - 195, 0)                          # the title and its spanners
    paste(sc, src, 776, 0, 960, 41, W - 184, 0)                               # Alt, sockets, «?»
    # the console along the foot
    sy = H - 72
    FU.sill(sc, sy)
    paste(sc, src, 0, 472, 706, 540, 0, sy + 4)                               # push-buttons, pinned left
    paste(sc, src, 706, 468, 960, 540, W - 254, sy)                           # the lever, pinned right
    by1 = sy - 6
    # the rack, pinned left and top
    paste(sc, src, 6, 48, 172, 466, 6, 48)
    # the panel, pinned right: its plate grown, the old content laid in at the top
    px0 = W - 252
    FU.plate(sc, px0, 52, W - 12, by1, seed=4)
    paste(sc, src, 712, 56, 944, 458, px0 + 4, 56)
    # the drawing: plate and sheet grown, the slipway centred on whole cells of the grid
    cx0, cx1 = 176, px0 - 8
    FU.plate(sc, cx0, 52, cx1, by1, seed=3)
    sx0, sy0, sx1, sy1 = cx0 + 10, 62, cx1 - 10, by1 - 58
    FH.blueprint_sheet(sc, sx0, sy0, sx1, sy1)
    ow, oh = 690 - 186, 408 - 62
    dx = int(round(((sx1 - sx0) - ow) / 2 / 40)) * 40
    dy = int(round(((sy1 - sy0) - oh) / 2 / 40)) * 40
    paste(sc, src, 196, 70, 680, 400, sx0 + 10 + dx, sy0 + 8 + dy)
    paste(sc, src, 186, 410, 690, 446, sx0, sy1 + 6)                         # the frame's rule and its cells
    return sc


def regions(sc, W, H):
    """The rule over a layout, in tinted bands: pinned to an edge (blue), grows (gold)."""
    sy = H - 72
    zones = [((0, 0, 120, 44), "pin"), ((W - 184, 0, W, 44), "pin"), ((W // 2 - 195, 0, W // 2 + 195, 44), "pin"),
             ((120, 0, W // 2 - 195, 44), "grow"), ((W // 2 + 195, 0, W - 184, 44), "grow"),
             ((6, 48, 172, sy - 6), "pin"), ((W - 252, 52, W - 12, sy - 6), "pin"),
             ((176, 52, W - 260, sy - 6), "grow"), ((0, sy, 706, H), "pin"), ((W - 254, sy, W, H), "pin"),
             ((706, sy, W - 254, H), "grow")]
    for (x0, y0, x1, y1), kind in zones:
        if x1 <= x0:
            continue
        col = hexc("#4a90b0") if kind == "pin" else hexc("#e0b860")
        m = (sc.xx >= x0) & (sc.xx < x1) & (sc.yy >= y0) & (sc.yy < y1)
        sc.rgb[m] = sc.rgb[m] * 0.55 + col * 0.45
        for x in range(x0, x1):
            sc.rgb[y0, x] = col
            sc.rgb[y1 - 1, x] = col
        sc.rgb[y0:y1, x0] = col
        sc.rgb[y0:y1, x1 - 1] = col


def sheet():
    """The workshop at 960×540, 1280×720 and 960×600; under them the 1280×720 one with the rule drawn over."""
    lays = [(960, 540, "960 × 540 · 1920×1080 ×2"), (1280, 720, "1280 × 720 · 2560×1440 ×2"),
            (960, 600, "960 × 600 · 1920×1200 ×2")]
    scs = [(layout(W, H), W, H, lab) for W, H, lab in lays]
    rule = layout(1280, 720)
    regions(rule, 1280, 720)
    k = 0.5
    tw = sum(int(W * k) for _, W, _, _ in scs) + 16 * 4
    th = 40 + int(720 * k) + 40 + int(720 * k) + 50
    canvas = Image.new("RGB", (tw, th), (20, 18, 22))
    x = 16
    for sc, W, H, lab in scs:
        im = Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8)).resize((int(W * k), int(H * k)), Image.BOX)
        canvas.paste(im, (x, 40))
        lsc = Scene(int(W * k), 30)
        lsc.rgb[:] = (20, 18, 22)
        letters(lsc, lab, 0, 4, "text", 16, col=(240, 200, 120))
        canvas.paste(Image.fromarray(np.clip(lsc.rgb, 0, 255).astype(np.uint8)), (x, 6))
        x += int(W * k) + 16
    im = Image.fromarray(np.clip(rule.rgb, 0, 255).astype(np.uint8)).resize((int(1280 * k), int(720 * k)), Image.BOX)
    y2 = 40 + int(720 * k) + 40
    canvas.paste(im, (16, y2))
    lsc = Scene(tw - 16 - int(1280 * k) - 32, 120)
    lsc.rgb[:] = (20, 18, 22)
    letters(lsc, "синее — прижато к краю", 0, 0, "text", 16, col=(154, 216, 240))
    letters(lsc, "жёлтое — растёт", 0, 22, "text", 16, col=(240, 200, 120))
    letters(lsc, "чертёж — лист больше,", 0, 54, "text", 16, col=(200, 192, 180))
    letters(lsc, "голем по центру", 0, 74, "text", 16, col=(200, 192, 180))
    canvas.paste(Image.fromarray(np.clip(lsc.rgb, 0, 255).astype(np.uint8)), (16 + int(1280 * k) + 32, y2 + 10))
    canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
    canvas.save(out("foundry_wide.png"))
    print("foundry_wide.png", canvas.size)


def battle_layout(W, H):
    """The battle on a bigger canvas: the field keeps its size in cells — it is not stretched — and stands in the
    middle; round it the same ground runs on without the cells' marks (fading into it at the seam). The beam runs
    the full width: the Foundry's count pinned left, the tug of war in the middle, the turn and the speed pinned
    right with their keys."""
    import battle as BT
    src = np.asarray(Image.open(out("foundry_battle.png")).convert("RGB").resize((960, 540), Image.NEAREST)).astype(np.float32)
    mx, my = (W - 960) // 2, (H - 540) // 2
    if mx == 0 and my == 0:
        big = Scene(W, H)
        big.rgb[:] = src
        return big
    keep = (BT.WW, BT.HH, BT.X0, BT.Y0)
    BT.WW, BT.HH, BT.X0, BT.Y0 = W, H, BT.X0 + mx, BT.Y0 + my + 400       # cell marks pushed off the canvas
    big = Scene(W, H)
    BT.ground(big)
    BT.WW, BT.HH, BT.X0, BT.Y0 = keep
    field = src[34:540]
    fy0 = my + 34
    yy, xx = np.mgrid[0:506, 0:960]
    e = np.minimum(np.minimum(xx, 959 - xx), np.minimum(yy, 505 - yy)).astype(np.float32)
    a = np.clip(e / 24.0, 0, 1)[..., None]
    a[0:28, 640:960] = 0                                                       # the keys under the speed caps go with them
    big.rgb[fy0:fy0 + 506, mx:mx + 960] = big.rgb[fy0:fy0 + 506, mx:mx + 960] * (1 - a) + field * a
    FU.wing(big, 0, 0, W, 34)
    paste(big, src, 0, 0, 146, 33, 0, 0)                                      # the Foundry's count
    paste(big, src, 146, 0, 600, 33, W // 2 - 227, 0)                         # the tug and the swarm's count
    paste(big, src, 650, 0, 960, 60, W - 310, 0)                              # the turn, the speed, their keys
    return big


def battle_sheet():
    lays = [(960, 540, "960 × 540"), (1280, 720, "1280 × 720 · поле тем же размером, по центру")]
    k = 0.5
    tw = int(960 * k) + int(1280 * k) + 48
    th = int(720 * k) + 50
    canvas = Image.new("RGB", (tw, th), (20, 18, 22))
    x = 16
    for W, H, lab in lays:
        sc = battle_layout(W, H)
        im = Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8)).resize((int(W * k), int(H * k)), Image.BOX)
        canvas.paste(im, (x, 40))
        lsc = Scene(int(W * k), 30)
        lsc.rgb[:] = (20, 18, 22)
        letters(lsc, lab, 0, 4, "text", 16, col=(240, 200, 120))
        canvas.paste(Image.fromarray(np.clip(lsc.rgb, 0, 255).astype(np.uint8)), (x, 6))
        x += int(W * k) + 16
    canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
    canvas.save(out("foundry_wide_battle.png"))
    print("foundry_wide_battle.png", canvas.size)


if __name__ == "__main__":
    sheet()
    battle_sheet()
