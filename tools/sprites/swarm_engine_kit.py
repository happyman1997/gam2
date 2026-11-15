"""The swarm's interface for the engine, like the Foundry's (engine_kit.py): every element as a transparent PNG, drawn
by the same code as the screens (swarm_ui.py, swarm_menus.py, swarm_artifacts.py), lifted off black and white to
keep its halos (pxfx.matte), with a manifest that says how to grow it — 9-slice or 3-slice, which strips repeat —
and where the overlays go (a plate's spiracles and spines, a cell's state marks). The pieces are drawn with straight
edges: the screens' hand wobble (±1.3 px) is left to the engine (or left out).

    python3 tools/sprites/swarm_engine_kit.py   -> assets/ui_kit/swarm/*.png + kit.json, out/swarm_engine_kit.png

Sizes are at the art's own scale (the screen is 960×540); the game draws them ×2 (or ×N), nearest.
"""
import json
import os
import numpy as np
from PIL import Image
from kit import Scene, hexc
import swarm_ui as UI
import swarm_hud as SH
import swarm_menus as M
import swarm_artifacts as A
import swarm_moments as SM
from engine_kit import lift, grow
from paths import out

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "assets", "ui_kit", "swarm")
PIECES = {}
CELL_STATES = ("normal", "hi", "new", "eat", "locked", "mut", "find", "hover")
BUTTON_KINDS = ("acid", "chitin", "blood", "amber", "dim")
BUTTON_H = (22, 30, 42, 56)


def save(name, im, **meta):
    os.makedirs(DST, exist_ok=True)
    im.save(os.path.join(DST, name + ".png"))
    PIECES[name] = dict(file=name + ".png", size=[im.width, im.height], **meta)
    return im


def crop(im, box):
    return Image.fromarray(np.asarray(im)[box[1]:box[3], box[0]:box[2]].copy(), "RGBA")


# ---------------------------------------------------------------- plates, cells, wings
def plates():
    """The chitin plate: a 9-slice whose strips are clean segments (one every 16 px) and one scute of the top rim
    (every 48 px); the spiracles down the sides and the bone spines are overlays, so they keep their spacing at any
    height. The antennae and the mandible hooks of a plate «with antennae» are overlays too."""
    im = lift(lambda sc: UI.plate(sc, 0, 0, 256, 256), 256, 256)
    save("plate", im, slice=[12, 12, 12, 12], tile_x=[78, 126], tile_y=[94, 110], mode="9-slice",
         note="the sheen under the top edge runs the whole width here (on the screens — its left 60%)")
    sp = lift(lambda sc: (sc.rgb.__setitem__((slice(0, 3), slice(0, 3)), hexc("#3a3048")),
                          sc.rgb.__setitem__((1, 1), UI.OUTL)), 3, 3)
    save("plate_spiracle", sp, place="x = 2 and x = w − 5; y = 21 + 34·k while y < h − 14")
    spine = lift(lambda sc: [sc.rgb.__setitem__((1 - k // 2, 3 - k), hexc("#8a7a66") if k < 3 else hexc("#c8b898"))
                             for k in range(4)], 4, 2)
    save("plate_spine_left", spine, place="off the left edge, its tip outward: x = −3, y = 29 + 46·k (plates taller than 60)")
    save("plate_spine_right", spine.transpose(Image.FLIP_LEFT_RIGHT), place="x = w − 1, y = 29 + 46·k")
    ant = lift(lambda sc: UI.antenna(sc, 28, 14, -1), 32, 16)
    save("plate_antenna_left", ant, anchor="its root at (28, 14) on the plate's top edge, 16 px in from the left")
    save("plate_antenna_right", ant.transpose(Image.FLIP_LEFT_RIGHT), anchor="root at (3, 14), 16 px in from the right")


def cells():
    """A comb cell in each state, at two chamfers (8 for a cell under 56 px tall, 12 for a taller one); 4 px of pad
    for the halo; the state's mark (the chosen one's tab, new's arrow, the eaten one's teeth, the helix, the gem) is
    an overlay. The bites of the one under the mouse sit in the corner slices."""
    keep = UI.state_mark
    UI.state_mark = lambda *a, **k: None
    try:
        for c, h, T, B in ((8, 50, 18, 28), (12, 78, 20, 40)):
            for st in CELL_STATES:
                im = lift(lambda sc, st=st, h=h: UI.cell(sc, 4, 4, 100, 4 + h, st), 104, h + 8)
                save(f"cell_{st}_{c}", im, slice=[40, T, 40, B], tile_x=[48, 56], tile_y=[T, T + 4], mode="9-slice", pad=4,
                     use=f"chamfer {c}: " + ("cells under 56 px tall" if c == 8 else "cells 56 px tall and over"))
    finally:
        UI.state_mark = keep
    for st, (w, h) in (("hi", (12, 18)), ("new", (10, 10)), ("eat", (40, 7)), ("mut", (10, 10)), ("find", (14, 14))):
        rim, hi_, _ = UI.CELL[st]

        def draw(sc, st=st):
            UI.state_mark(sc, 60, 4, 100, 40, st, rim, hi_)
        full = lift(draw, 104, 44)
        a = np.asarray(full)[..., 3]
        ys, xs = np.nonzero(a)
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        place = {"hi": "its tip on the cell's left edge, middle", "new": "top right: x = w − 14, y = 5",
                 "eat": "bottom right: x = w − 60, y = h − 9", "mut": "top right: x = w − 14, y = 6",
                 "find": "top right: x = w − 18, y = 5"}[st]
        save(f"cell_mark_{st}", crop(full, box), place=place)


def wings():
    """The wing over the screen (44 px), the battle's thinner one (34) and the foot (72): their veins don't repeat,
    so each is drawn whole at the width of the canvases the game uses."""
    for W in (960, 1280):
        for nm, h in (("wing", 44), ("wing_battle", 34), ("foot", 72)):
            save(f"{nm}_{W}", lift(lambda sc, W=W, h=h: UI.wing(sc, 0, 0, W, h), W, h),
                 use=f"drawn whole across a {W}-wide canvas")


def buttons():
    """The buttons, each kind at the heights the screens use: 3-slices — the tips with their mandibles and studs
    whole, the middle repeating a 6 px strip of the keel; the word is the engine's."""
    text = {"acid": dict(colour="#ecff8c", edge="#6eaa28", kind="title", hairs=4),
            "chitin": dict(colour="#ecdcc4", kind="text"), "blood": dict(colour="#ffc8b4", kind="text"),
            "amber": dict(colour="#281608", kind="text", outline=False), "dim": dict(colour="#786c84", kind="title", outline=False)}
    for kind in BUTTON_KINDS:
        for h in BUTTON_H:
            Wb = 200
            im = lift(lambda sc, kind=kind, h=h: UI.button(sc, 14, 4, 14 + Wb, 4 + h, kind), Wb + 28, h + 8)
            e = int(h * 1.3) + 16
            save(f"button_{kind}_{h}", im, slice=[e, 0, e, 0], tile_x=[110, 116], tile_y=[0, h + 8], mode="3-slice", pad=[14, 4],
                 text=dict(align="center", px=16, y=h // 2 - 5, **text[kind]),
                 note="chitin's iridescence drifts along the whole width on the screens; here its middle repeats")


# ---------------------------------------------------------------- the settings' controls, the brood's scales
def controls():
    """The groove gnawed in the wax (3-slice), its comb-cell notch and the amber drop; the ichor of a level; the
    firefly's lantern on and off; the pair of mandibles round a list's window; the settings' four icons."""
    def gr(sc):
        M.groove(sc, 4, 196, 8, 2, 1)
    im = lift(gr, 200, 16)
    a = np.asarray(im).copy()
    a[:, 86:114] = a[:, 60:88]                                             # no notch or drop in the middle strip
    save("groove", Image.fromarray(a, "RGBA"), slice=[8, 0, 8, 0], tile_x=[60, 84], tile_y=[0, 16], mode="3-slice",
         note="the drop rides at y = 8 (its middle); notches at y = 8, labels 12 px under")
    save("groove_notch", lift(lambda sc: (sc.rgb.__setitem__(SH.hexmask(sc, 7, 7, 6), hexc(M.WAX[2])),
                                          sc.rgb.__setitem__(SH.hexmask(sc, 7, 7, 4), hexc("#0e0a10"))), 14, 14), pivot=[7, 7])
    save("groove_drop", lift(lambda sc: M.bead(sc, 10, 12), 20, 24), pivot=[10, 12])

    def ichor(sc):
        t = np.clip(sc.yy / 6.0, 0, 1)[..., None]
        sc.rgb[:] = hexc(M.ICHOR[3]) * (1 - t) + hexc(M.ICHOR[1]) * t
    save("groove_ichor", lift(ichor, 4, 7), slice=[0, 0, 0, 0], tile_x=[0, 4], tile_y=[0, 7], mode="3-slice",
         anchor="inside the groove (y 5..11), from its left end to the drop; a pale bubble every 13 px")
    for on in (True, False):
        save(f"lantern_{'on' if on else 'off'}", lift(lambda sc, on=on: M.lantern(sc, 22, 22, on), 44, 44), pivot=[22, 22])
    full = lift(lambda sc: M.mandibles(sc, 2, 202, 16, ""), 204, 32)
    save("mandible_left", crop(full, (0, 0, 22, 32)), anchor="left of the window, the list's middle at y = 16")
    save("mandible_right", crop(full, (182, 0, 204, 32)), anchor="right of the window")
    import swarm_icons_drawn as D
    keys = list(D.UI)
    atlas = np.zeros((16, 16 * len(keys), 4), np.uint8)
    for j, k in enumerate(keys):
        atlas[:, j * 16:(j + 1) * 16] = D.UI[k]()
    Image.fromarray(atlas, "RGBA").save(os.path.join(DST, "settings_icons.png"))
    PIECES["settings_icons"] = dict(file="settings_icons.png", size=[16 * len(keys), 16], cells=keys, cell=16, z=2)


def scales():
    """The brood's limit as a centipede: a scale in each of its states (the engine sets its width from the count:
    a = max(3, w·0.62), b = h/2 + 2), the head, the tail, the bone pin at the limit; and a meter's dim scale."""
    for kind, bite, crack in (("ok", False, False), ("over", False, True), ("eat", True, False), ("dim", False, False),
                              ("violet", False, False)):
        nm = {"ok": "scale_ok", "over": "scale_over", "eat": "scale_eat", "dim": "scale_dim", "violet": "scale_violet"}[kind]
        save(nm, lift(lambda sc, kind=kind, bite=bite, crack=crack: UI.gem(sc, 8, 11, 6.2, 10, kind, bite=bite, crack=crack),
                      17, 23), pivot=[8, 11], note="drawn at a = 6.2, b = 10 (16 px tall bar); the engine redraws it at other sizes")
    full = lift(lambda sc: UI.segbar(sc, 2, 12, 160, 16, 8, 6, 1), 170, 44)
    save("centipede_head", crop(full, (0, 0, 20, 44)), anchor="the bar's left end at x = 2, its top at y = 12")
    save("centipede_tail", crop(full, (150, 0, 170, 44)), anchor="the bar's right end at x = 160")
    save("limit_pin", crop(full, (int(2 + 16 + 6 * (160 - 10 - 18) / 8) - 3, 0, int(2 + 16 + 6 * (160 - 10 - 18) / 8) + 3, 44)),
         anchor="at the limit, over the scales")


# ---------------------------------------------------------------- the run's pieces
def run_pieces():
    """The artifact cells in their states (the artifacts' icons — the Foundry's atlas, they are the same things),
    the leader's ability box, the battle's end plate, the damage numbers' style (a spec: the engine writes them)."""
    for st in ("empty", "normal", "awake", "fire"):
        def draw(sc, st=st):
            A.cell(sc, 16, 16, None if st == "empty" else "banner", "normal" if st == "empty" else st)
        im = lift(draw, 32, 32)
        if st != "empty":                                                  # the cell without its artifact: the engine puts it in
            keep = A.art_icon
            A.art_icon = lambda *a, **k: None
            im = lift(draw, 32, 32)
            A.art_icon = keep
        save(f"artifact_cell_{st}", im, pivot=[16, 16],
             note="the artifact's icon at (8, 8), ×1, under the amber (×0.8 + #e8a030 ×0.2)" if st != "empty" else "an empty open cell")
    PIECES["artifacts"] = dict(file="../foundry/artifacts.png", note="the same atlas as the Foundry's")
    save("crown", lift(lambda sc: SH.glyph(sc, "лидер", 0, 0, 2), 26, 20),
         note="the leader's ability box: cell_hi_8 grown to 216×48, the crown at (8, 4), the ability's icon at (8, 20), "
              "name at (36, 4), line at (36, 24)")
    for kind, win in (("win", True), ("lose", False)):
        def draw(sc, win=win):
            UI.plate(sc, 30, 20, 390, 90, antennae=True)
            if not win:
                sc.rgb[20:91, 30:391] *= 0.7
        save(f"end_plate_{kind}", lift(draw, 420, 100), text=dict(align="center", kind="title", px=24, y=38),
             note="across the dimmed field; two wasps beating their wings either side (win), two dead (lose)")
    PIECES["damage_numbers"] = dict(kind="spec", font="title", drips=3, jitter=1,
                                    rise="out_back over 4 frames, then 0.8 px/frame up, fade the last 5",
                                    styles={k: dict(px=v[2], colour="#%02x%02x%02x" % v[0], edge="#%02x%02x%02x" % v[1])
                                            for k, v in SM.NUM.items()})


def manifest():
    rel = lambda *p: os.path.join(*p)
    kit = dict(
        name="Рой", scale="art px (960×540 screen); draw ×2 nearest",
        pieces=PIECES,
        slicing=("9-slice: corners as they are, edges and middle repeat tile_x / tile_y of the source, cut at the far "
                 "end; 3-slice: the same along x only. pad — transparent margin kept for halos."),
        glyphs=dict(file="../foundry/glyphs.json", note="the effect lines' glyphs are the same for both classes", z=2),
        icons=dict(swarm=rel("..", "..", "swarm_icons.png"), index=rel("..", "..", "swarm_icons.json"), cell=16),
        fonts=dict(
            title=dict(file="tools/sprites/fonts/PressStart2P-Regular.ttf", px=[16, 24], license="OFL 1.1 (в репо)",
                       swarm="jitter 1 px, drips and bristles (swarm_ui.letters)"),
            text=dict(file="tools/sprites/fonts/unifont-18.0.01.otf", px=[16],
                      license="SIL OFL 1.1 (или GPL-2+ с исключением для шрифтов); OFL-Unifont.txt, LICENSE-Unifont.txt")),
        colours=dict(ink="#ecdcc4", muted="#aa9cb4", gold="#f0be5a", pale="#786c84", acid="#b0f446", outline="#100c10",
                     wax=list(M.WAX), ichor=list(M.ICHOR)),
        background=dict(nest="swarm_ui.nest: dark wax comb, R = 13 hexagons, tunnels; drawn per screen, not sliced"),
    )
    json.dump(kit, open(os.path.join(DST, "kit.json"), "w"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- the proof
def preview():
    """Everything on one sheet, and the test: each sliced piece grown to a new size beside the same element drawn
    at that size by swarm_ui."""
    from swarm_ui import letters
    sc = UI.nest(960, 540, 5)
    UI.wing(sc, 0, 0, 960, 44)
    letters(sc, "НАБОР ДЛЯ ДВИЖКА · РОЙ", 480, 8, "title", 24, col=(176, 244, 70), col2=(70, 150, 50), align="center")
    canvas = Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    def put(im, x, y):
        canvas.alpha_composite(im, (int(x), int(y)))

    def label(t, x, y):
        s2 = Scene(len(t) * 9 + 8, 18)
        s2.rgb[:] = 0
        letters(s2, t, 2, 1, "text", 16, col=(170, 156, 180), outline=False, shadow=False)
        a = np.clip(s2.rgb, 0, 255).astype(np.uint8)
        al = (a.max(axis=2) > 20).astype(np.uint8) * 255
        canvas.alpha_composite(Image.fromarray(np.dstack((a, al)), "RGBA"), (int(x), int(y)))

    def src(name):
        return Image.open(os.path.join(DST, PIECES[name]["file"])).convert("RGBA")

    def g(name, W, H):
        p = PIECES[name]
        return grow(src(name), W, H, p["slice"], p["tile_x"], p["tile_y"])

    label("плита: сборка", 12, 52)
    pl = g("plate", 200, 140)
    put(pl, 12, 70)
    for k in range(4):                                                       # its overlays
        put(src("plate_spiracle"), 12 + 2, 70 + 21 + 34 * k) if 21 + 34 * k < 126 else None
        put(src("plate_spiracle"), 12 + 195, 70 + 21 + 34 * k) if 21 + 34 * k < 126 else None
    label("нарисовано", 224, 52)
    put(lift(lambda s: UI.plate(s, 0, 0, 200, 140), 200, 140), 224, 70)
    label("ячейки: сборка 118×52", 440, 52)
    for i, st in enumerate(CELL_STATES):
        put(g(f"cell_{st}_8", 126, 60), 436 + (i % 4) * 128, 66 + (i // 4) * 60)
    put(src("cell_mark_hi"), 436 + 128 + 4 - 3, 66 + 30 - 7)
    put(src("cell_mark_new"), 436 + 256 + 118 - 14 + 4, 66 + 9)
    put(src("cell_mark_eat"), 436 + 384 + 118 - 60 + 4, 66 + 52 - 9 + 4)
    label("нарисовано", 440, 188)
    for i, st in enumerate(("hover", "hi")):
        put(lift(lambda s, st=st: UI.cell(s, 4, 4, 122, 56, st), 126, 60), 436 + i * 128, 204)
    y = 278
    label("кнопки: сборка 180 px и нарисовано", 12, y - 18)
    for i, kind in enumerate(BUTTON_KINDS):
        put(g(f"button_{kind}_30", 208, 38), 12 + (i % 3) * 214, y + (i // 3) * 42)
    put(lift(lambda s: UI.button(s, 14, 4, 194, 34, "acid"), 208, 38), 12 + 2 * 214, y + 42)
    y = 380
    label("паз, капля, фонарик, жвалы, шкала", 12, y - 18)
    gp = PIECES["groove"]
    put(grow(src("groove"), 260, 16, gp["slice"], gp["tile_x"], gp["tile_y"]), 12, y)
    put(src("groove_notch"), 12 + 4, y + 1)
    put(src("groove_notch"), 12 + 250, y + 1)
    put(src("groove_drop"), 12 + 120, y - 4)
    put(src("lantern_on"), 290, y - 14)
    put(src("lantern_off"), 334, y - 14)
    put(src("mandible_left"), 390, y - 8)
    put(src("mandible_right"), 560, y - 8)
    put(lift(lambda s: UI.cell(s, 0, 0, 160, 28, "normal"), 160, 28), 410, y - 6)
    for i, nm in enumerate(("scale_ok", "scale_over", "scale_eat", "scale_dim", "scale_violet")):
        put(src(nm), 620 + i * 18, y - 4)
    put(src("centipede_head"), 720, y - 16)
    put(src("centipede_tail"), 744, y - 16)
    y = 444
    label("ячейки артефактов, корона, плита конца боя", 12, y - 18)
    for i, st in enumerate(("empty", "normal", "awake", "fire")):
        put(src(f"artifact_cell_{st}"), 12 + i * 36, y)
    put(src("crown"), 160, y + 6)
    put(src("end_plate_win").resize((210, 50), Image.NEAREST), 200, y - 6)
    put(src("end_plate_lose").resize((210, 50), Image.NEAREST), 420, y - 6)
    put(Image.open(os.path.join(DST, "settings_icons.png")).convert("RGBA").resize((128, 32), Image.NEAREST), 650, y)
    canvas = canvas.convert("RGB").resize((1920, 1080), Image.NEAREST)
    canvas.save(out("swarm_engine_kit.png"))
    print("swarm_engine_kit.png", canvas.size)


if __name__ == "__main__":
    UI.WOBBLE[0] = 0.0
    plates()
    cells()
    wings()
    buttons()
    controls()
    scales()
    run_pieces()
    manifest()
    preview()
    print(len(PIECES), "pieces ->", DST)
