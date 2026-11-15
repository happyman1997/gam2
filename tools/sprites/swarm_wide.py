"""The swarm's screens on a bigger canvas (1280×720 — 2560×1440 at ×2), laid out by the same rule as the
Foundry's (wide.py): what is at an edge stays pinned to it, the plates between grow, nothing is stretched.

  the brood   — the wing the full width (the title and the artifacts pinned left, the purse and «?» right); the
                limit's centipede drawn the full width again (more segments' room, the same count); the groups
                pinned left and top — the room they gain shown as empty comb cells (a fourth column, more rows);
                the biomass column pinned right, its plate grown; the buttons pinned to their ends;
  the battle  — the field keeps its size in cells, in the middle; the ground runs on round it; the wing the full
                width: the swarm's count left, the tug in the middle, the turn and the speed right with their keys;
  the rest    — settings, defeat, a leader's development: plates pinned left and right, the middle one growing,
                its content centred (the development's chamber grows in the leader's own material).

    python3 tools/sprites/swarm_wide.py   -> out/swarm_wide.png, out/swarm_wide_battle.png, out/swarm_wide_screens.png
"""
import numpy as np
from PIL import Image
from kit import Scene, hexc
import swarm_ui as UI
import swarm_hud as SH
from swarm_ui import letters
from paths import out


def paste(sc, src, x0, y0, x1, y1, dx, dy):
    sc.rgb[dy:dy + (y1 - y0), dx:dx + (x1 - x0)] = src[y0:y1, x0:x1]


def load(name):
    return np.asarray(Image.open(out(name)).convert("RGB").resize((960, 540), Image.NEAREST)).astype(np.float32)


def beam(sc, src, W, left=300):
    """The wing the full width: its left end pinned (the title), the middle centred, the right end pinned."""
    dw = W - 960
    UI.wing(sc, 0, 0, W, 44)
    paste(sc, src, 0, 0, left, 41, 0, 0)
    paste(sc, src, left, 0, 776, 41, left + dw // 2, 0)
    paste(sc, src, 776, 0, 960, 41, W - 184, 0)


def brood_layout(W, H):
    import brood as B
    src = SH.brood("plain", ret=True).rgb.copy()
    UI.WOBBLE[0] = 1.3
    dw, dh = W - 960, H - 540
    sc = UI.nest(W, H, 31)
    UI.wing(sc, 0, 0, W, 44)
    paste(sc, src, 0, 0, 660, 41, 0, 0)                                       # the title and the artifacts
    paste(sc, src, 680, 0, 960, 41, W - 280, 0)                               # the purse, Alt, «?»
    # the limit: its plate and its centipede drawn again the full width
    groups = [list(g) for g in B.GROUPS]
    total = sum(B.pts(g) * g[5] for g in groups)
    limit = SH.BROOD_LEADER["Матка"][5]
    UI.plate(sc, 12, 50, W - 12, 94)
    paste(sc, src, 18, 54, 148, 90, 18, 54)
    UI.segbar(sc, 150, 62, W - 22, 16, total, limit, total - limit)
    # the groups pinned left and top; the room they gain — empty comb cells
    paste(sc, src, 0, 96, 706, 436, 0, 96)
    GX0, GY0, GCW, GCH = 12, 100, 224, 78
    cols = (W - 262 - GX0) // (GCW + 8)
    rows = (H - 110 - GY0) // (GCH + 6)
    for r in range(rows):
        for c in range(cols):
            if c < 3 and r < 4:
                continue
            x0, y0 = GX0 + c * (GCW + 8), GY0 + r * (GCH + 6)
            UI.cell(sc, x0, y0, x0 + GCW, y0 + GCH, "locked")
    paste(sc, src, 0, 436, 706, 476, 0, 436 + dh)                             # natural selection, at the foot
    # the biomass column pinned right, its plate grown
    UI.plate(sc, W - 250, 100, W - 12, 474 + dh, antennae=True)
    paste(sc, src, 714, 104, 944, 470, W - 246, 104)
    # the buttons pinned to their ends
    paste(sc, src, 0, 478, 706, 540, 0, H - 62)
    paste(sc, src, 706, 476, 960, 540, W - 254, H - 64)
    UI.WOBBLE[0] = 0.0
    return sc


def sheet():
    """The brood at 960×540 and at 1280×720, side by side."""
    k = 0.5
    lays = [(960, 540, "960 × 540"), (1280, 720, "1280 × 720 · группы закреплены, пустые соты — место для новых")]
    canvas = Image.new("RGB", (int(960 * k) + int(1280 * k) + 48, int(720 * k) + 50), (20, 18, 22))
    x = 16
    for W, H, lab in lays:
        sc = brood_layout(W, H)
        im = Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8)).resize((int(W * k), int(H * k)), Image.BOX)
        canvas.paste(im, (x, 40))
        lsc = Scene(int(W * k), 30)
        lsc.rgb[:] = (20, 18, 22)
        letters(lsc, lab, 0, 4, "text", 16, col=(240, 200, 120))
        canvas.paste(Image.fromarray(np.clip(lsc.rgb, 0, 255).astype(np.uint8)), (x, 6))
        x += int(W * k) + 16
    canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
    canvas.save(out("swarm_wide.png"))
    print("swarm_wide.png", canvas.size)
    big = brood_layout(1280, 720)
    Image.fromarray(np.clip(big.rgb, 0, 255).astype(np.uint8)).resize((2560, 1440), Image.NEAREST).save(out("swarm_wide_brood.png"))
    print("swarm_wide_brood.png")


def plates_layout(name, cols, W, H, split=600, foot_wing=True, leader=None, rim=None):
    """Any swarm screen of plates side by side: the wing the full width, the plates pinned to their edges, the one
    marked «grow» taking the extra width (its content centred), every plate taking the extra height (content at
    its top); the foot the full width, its left buttons pinned left and its right ones right. A «chamber» grows
    in the leader's own material instead of a plate."""
    src = load(name)
    UI.WOBBLE[0] = 1.3
    dw, dh = W - 960, H - 540
    sc = UI.nest(W, H, 13)
    beam(sc, src, W)
    for x0, y0, x1, y1, mode in cols:
        nx0 = x0 + (dw if mode == "pin_r" else 0)
        nx1 = x1 + (dw if mode in ("pin_r", "grow", "chamber") else 0)
        # what the plate (or the chamber) is by itself, to lift only what was drawn on it
        bare = Scene(960, 540)
        if mode == "chamber":
            SH.FILL[leader](bare, x0, y0, x1, y1)
            bare.rgb[y0:y1, x0:x1] *= 0.42
            SH.FILL[leader](sc, nx0, y0, nx1, y1 + dh)
            sc.rgb[y0:y1 + dh, nx0:nx1] *= 0.42
            ix0, iy0, ix1, iy1 = x0, y0 + 2, x1 - 9, y1
        else:
            UI.plate(bare, x0, y0, x1, y1)
            UI.plate(sc, nx0, y0, nx1, y1 + dh)
            ix0, iy0, ix1, iy1 = x0 + 5, y0 + 5, x1 - 5, y1 - 5
        ox = nx0 + (dw // 2 if mode in ("grow", "chamber") else 0) + (ix0 - x0)
        sink = dh // 2 if mode == "chamber" else 0                       # a growing plate: headings stay in line
        if mode == "chamber" and leader == "Матка":                       # her cells hang from the ceiling: pinned up
            sink = 0
        oy = sink + iy0
        if mode == "chamber":                                             # what joins the growths runs the full width
            if leader == "Матка":
                cm = (sc.xx >= nx0) & (sc.xx < nx1) & (sc.yy >= 46) & (sc.yy < 62)
                sc.rgb[cm] = hexc("#5a3608")
                UI.comb(sc, cm, nx0, 44, hexc("#a0701e"), 0.9, R=7)
                sc.rgb[61:63, nx0:nx1] = UI.OUTL
            elif leader == "Пожиратель":
                SH.thick(sc, [(nx0, 292 + sink), (nx1 - 8, 292 + sink)], 7, hexc("#7a1a14"), hexc("#b03a2a"))
                for x in range(nx0 + 8, nx1 - 8, 18):
                    sc.rgb[288 + sink:297 + sink, x] = hexc("#4a0c0a")
        part, base_ = src[iy0:iy1, ix0:ix1], bare.rgb[iy0:iy1, ix0:ix1]
        m = np.abs(part - base_).max(axis=-1) > 10
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
        dst = sc.rgb[oy:oy + part.shape[0], ox:ox + part.shape[1]]
        dst[m] = part[m]
    sy = 466 + dh
    if foot_wing:
        UI.wing(sc, 0, sy + 2, W, H)
    paste(sc, src, 0, 468, split, 540, 0, sy + 2)
    paste(sc, src, split, 466, 960, 540, W - (960 - split), sy)
    if rim:                                                               # a leader's screen: its edge, the full size
        rim_at(sc, rim, W, H, 46)
    UI.WOBBLE[0] = 0.0
    return sc


def rim_at(sc, col, W, H, y0):
    """The leader's (or the form's) coloured edge round a screen of any size (swarm_hud._rim)."""
    c = hexc(col)
    for k in (0, 1):
        sc.rgb[y0 + k, 6:W - 6] = c * (0.9 - 0.3 * k)
        sc.rgb[H - 7 - k, 6:W - 6] = c * (0.9 - 0.3 * k)
        sc.rgb[y0:H - 6, 6 + k] = c * (0.9 - 0.3 * k)
        sc.rgb[y0:H - 6, W - 7 - k] = c * (0.9 - 0.3 * k)


def card_layout(name, W, H, rim=None, left=440):
    """A full card (swarm_hud.big_card) on a bigger canvas: one plate the whole size; the portrait and its facts
    pinned left and top, «Закрыть» to the bottom left; the numbers and attacks in the middle; the abilities
    pinned right — only what was drawn on the plate is lifted onto the bigger one."""
    src = load(name)
    UI.WOBBLE[0] = 1.3
    dw, dh = W - 960, H - 540
    sc = UI.nest(W, H, 13)
    beam(sc, src, W, left)
    bare = Scene(960, 540)
    UI.plate(bare, 6, 50, 954, 534)
    UI.plate(sc, 6, 50, W - 6, H - 6)

    def lift(x0, y0, x1, y1, dx, dy):
        part, base_ = src[y0:y1, x0:x1], bare.rgb[y0:y1, x0:x1]
        m = np.abs(part - base_).max(axis=-1) > 10
        m = m | np.roll(m, 1, 0) | np.roll(m, -1, 0) | np.roll(m, 1, 1) | np.roll(m, -1, 1)
        dst = sc.rgb[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        dst[m] = part[m]
    lift(10, 54, 310, 470, 0, 0)                                          # the portrait and its facts
    lift(10, 470, 310, 530, 0, dh)                                        # «Закрыть»
    lift(310, 54, 624, 530, dw // 2, 0)                                   # the numbers, the attacks
    lift(624, 54, 950, 530, dw, 0)                                        # the abilities
    if rim:
        rim_at(sc, rim, W, H, 50)
    UI.WOBBLE[0] = 0.0
    return sc


def screens_sheet2():
    """The rest at 1280×720: the hive (the Devourer's), the evolution (the Plague's), the leader's choice, a card."""
    import swarm_form_cards as FC
    k = 0.5
    cw, ch = int(1280 * k), int(720 * k)
    canvas = Image.new("RGB", (cw * 2 + 48, ch * 2 + 48), (20, 18, 22))
    camp = [(12, 52, 286, 446, "pin_l"), (296, 52, 652, 446, "grow"), (662, 52, 948, 446, "pin_r")]
    evo = [(12, 52, 300, 446, "pin_l"), (310, 52, 948, 446, "grow")]
    lays = [plates_layout("swarm_camp_pozh.png", camp, 1280, 720, 600, False, None, SH.LEADER_COL["Пожиратель"]),
            plates_layout("swarm_evolution_kuk.png", evo, 1280, 720, 600, False, None, SH.LEADER_COL["Чума"]),
            SH.leaders_pick(1280, 720, ret=True),
            card_layout("swarm_card_wasp.png", 1280, 720, FC.FORM["wings"][2])]
    for i, sc in enumerate(lays):
        im = Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8)).resize((cw, ch), Image.BOX)
        canvas.paste(im, (16 + (i % 2) * (cw + 16), 16 + (i // 2) * (ch + 16)))
    canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
    canvas.save(out("swarm_wide_screens2.png"))
    print("swarm_wide_screens2.png", canvas.size)
    big = card_layout("swarm_card_leader.png", 1280, 720, SH.LEADER_COL["Матка"])
    Image.fromarray(np.clip(big.rgb, 0, 255).astype(np.uint8)).resize((2560, 1440), Image.NEAREST).save(out("swarm_wide_card.png"))
    print("swarm_wide_card.png")


SCREENS = [   # file, its plates (x0, y0, x1, y1, how it grows), where the foot splits, a foot wing, the leader
    ("swarm_settings.png", [(12, 52, 196, 462, "pin_l"), (206, 52, 948, 462, "grow")], 600, True, None),
    ("swarm_defeat.png", [(12, 52, 330, 462, "pin_l"), (340, 52, 626, 462, "grow"), (634, 52, 948, 462, "pin_r")], 600,
     True, None),
    ("swarm_development_matka.png", [(12, 52, 300, 446, "pin_l"), (304, 46, 956, 456, "chamber")], 600, False, "Матка"),
    ("swarm_development_pozh.png", [(12, 52, 300, 446, "pin_l"), (304, 46, 956, 456, "chamber")], 600, False,
     "Пожиратель"),
]


def screens_sheet():
    """Four more screens at 1280×720, two by two."""
    k = 0.5
    cw, ch = int(1280 * k), int(720 * k)
    canvas = Image.new("RGB", (cw * 2 + 48, ch * 2 + 48), (20, 18, 22))
    for i, (name, cols, split, foot, lead) in enumerate(SCREENS):
        sc = plates_layout(name, cols, 1280, 720, split, foot, lead)
        im = Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8)).resize((cw, ch), Image.BOX)
        canvas.paste(im, (16 + (i % 2) * (cw + 16), 16 + (i // 2) * (ch + 16)))
    canvas = canvas.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
    canvas.save(out("swarm_wide_screens.png"))
    print("swarm_wide_screens.png", canvas.size)


def battle_layout(W, H):
    """The battle on a bigger canvas: the field keeps its size in cells, in the middle; the ground runs on round it
    (fading into it at the seam); the wing the full width — the swarm's count pinned left, the tug and the
    Foundry's count in the middle, the turn and the speed pinned right with their keys."""
    import battle as BT
    src = load("swarm_battle_hud.png")
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
    a[0:22, 690:960] = 0                                                       # the keys under the speed go with it
    big.rgb[fy0:fy0 + 506, mx:mx + 960] = big.rgb[fy0:fy0 + 506, mx:mx + 960] * (1 - a) + field * a
    UI.wing(big, 0, 0, W, 34)
    paste(big, src, 0, 0, 140, 33, 0, 0)                                      # the swarm's count
    paste(big, src, 140, 0, 690, 33, W // 2 - 275, 0)                         # the tug, the Foundry's count
    paste(big, src, 690, 0, 960, 56, W - 270, 0)                              # the turn, the speed, their keys
    return big


def battle_sheet():
    lays = [(960, 540, "960 × 540"), (1280, 720, "1280 × 720 · поле тем же размером, по центру")]
    k = 0.5
    canvas = Image.new("RGB", (int(960 * k) + int(1280 * k) + 48, int(720 * k) + 50), (20, 18, 22))
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
    canvas.save(out("swarm_wide_battle.png"))
    print("swarm_wide_battle.png", canvas.size)


if __name__ == "__main__":
    sheet()
    battle_sheet()
    screens_sheet()
    screens_sheet2()
