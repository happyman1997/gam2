"""The Foundry's interface for the engine: every element as a transparent PNG, drawn by the same code as the screens
(foundry_ui.py) and lifted off black and white to keep its soft halos (pxfx.matte), with a manifest that says how
to grow it to any size — 9-slice or 3-slice, which strips repeat, and the period they repeat at, so the rivets,
the dithering and the hammer marks never tear at a seam. Next to them: the controls in each of their states, the
nameplates at the widths the screens use, the glyphs of the effect lines in one atlas, and pointers to what is
already in assets/ (module icons, animation sheets, pixelfx effects) and to the fonts.

    python3 tools/sprites/engine_kit.py   -> assets/ui_kit/foundry/*.png + kit.json, out/foundry_engine_kit.png

Sizes are at the art's own scale (the screen is 960×540); the game draws them ×2 (or ×N), nearest.
"""
import json
import os
import numpy as np
from PIL import Image
from kit import Scene, hexc
import foundry_ui as FU
import swarm_hud as H
import pxfx
from paths import out

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "assets", "ui_kit", "foundry")
PIECES = {}


def save(name, im, **meta):
    os.makedirs(DST, exist_ok=True)
    im.save(os.path.join(DST, name + ".png"))
    PIECES[name] = dict(file=name + ".png", size=[im.width, im.height], **meta)
    return im


def lift(draw, w, h):
    """Draw it on black and on white; colour and alpha back (pxfx.matte)."""
    return pxfx.matte(draw, w, h)


# ---------------------------------------------------------------- growing a piece: 9-slice with repeats
def grow(im, W, H, sl, tx, ty):
    """The piece at a new size: corners as they are; the edges and the middle repeat their strips (tx — the source
    columns that repeat along the top and bottom, ty — the rows that repeat down the sides), cut at the far end.
    sl = (left, top, right, bottom). A 3-slice is the same with top = bottom = 0 and ty the whole height."""
    src = np.asarray(im)
    L, T, R, B = sl
    h0, w0 = src.shape[:2]
    out_ = np.zeros((H, W, 4), np.uint8)

    def cols(n):                                   # source columns for the middle of a row n wide
        seg = np.arange(tx[0], tx[1])
        return np.resize(seg, n)

    def rows(n):
        seg = np.arange(ty[0], ty[1])
        return np.resize(seg, n)

    xs = np.concatenate([np.arange(L), cols(W - L - R), np.arange(w0 - R, w0)])
    ys = np.concatenate([np.arange(T), rows(H - T - B), np.arange(h0 - B, h0)])
    out_[:] = src[ys][:, xs]
    return Image.fromarray(out_, "RGBA")


def shade(im, top=1.18, bottom=0.82):
    """The plate's top-to-bottom shading, as the engine lays it over a flat plate (a vertical multiply)."""
    a = np.asarray(im).astype(np.float32)
    k = np.linspace(top, bottom, a.shape[0])[:, None, None]
    a[..., :3] = np.clip(a[..., :3] * k, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- the pieces
def plate():
    """The iron sheet: rivets every 18 px round the edge — the strips repeat a whole rivet period."""
    im = lift(lambda sc: FU.plate(sc, 0, 0, 128, 128, seed=1, shade=False), 128, 128)
    save("plate", im, slice=[23, 25, 15, 13], tile_x=[23, 41], tile_y=[25, 43], mode="9-slice",
         period=18, snap="w = 38 + 18·n, h = 38 + 18·n (a rivet never cut in half)",
         shade=dict(top=1.18, bottom=0.82, note="vertical multiply over the whole plate"))


CELL_STATES = ("normal", "hi", "hover", "new", "broken", "rare", "trophy", "locked")


def cells():
    """A cell in each state: 4 px of margin round it for the halo and the sparks; the strips repeat 4 px (the
    dither's period), taken from the middle of the sides — clear of the sparks at the corners and of the chosen
    one's tab at the left middle; the marks at the top right (new, rare, trophy) inside the corner."""
    for st in CELL_STATES:
        im = lift(lambda sc, st=st: FU.cell(sc, 4, 4, 100, 100, st, seed=1), 104, 104)
        if st == "hi":                     # the tab at the left middle: an overlay (the strips are taken clear of it)
            tab = np.asarray(im)[44:61, 0:14].copy()
            save("cell_hi_tab", Image.fromarray(tab, "RGBA"),
                 anchor="the cell's left edge at x = 4, its middle at y = 8 (the piece's pad included)")
        top = 22 if st in ("new", "rare", "trophy") else 16              # the mark at the top right stays whole
        save(f"cell_{st}", im, slice=[16, top, 24, 20], tile_x=[48, 52], tile_y=[64, 68], mode="9-slice", pad=4)


def tags():
    """The stamped tags of the console: the point and its hole on the left, a 3-slice; the text is the engine's
    (dark, struck, 16 px), from x = 27."""
    for kind in ("steel", "brass", "rust", "dull"):
        im = lift(lambda sc, kind=kind: FU.tag(sc, 0, 0, 120, 26, "", kind), 120, 26)
        save(f"tag_{kind}", im, slice=[20, 0, 4, 0], tile_x=[20, 24], tile_y=[0, 26], mode="3-slice",
             text=dict(x=27, kind="text", px=16))


def beams():
    """The beam over the screen (44 px) and the console's sill under it (72 px): 3-slices along the rivets."""
    im = lift(lambda sc: FU.wing(sc, 0, 0, 109, 44), 109, 44)
    save("wing", im, slice=[21, 0, 0, 0], tile_x=[21, 43], tile_y=[0, 44], mode="3-slice", period=22)
    im = lift(lambda sc: FU.sill(sc, 0, 72), 129, 72)
    save("sill", im, slice=[25, 0, 0, 0], tile_x=[25, 51], tile_y=[0, 72], mode="3-slice", period=26)


def tabs_keys():
    """The panel's tabs (open — brass, shut — iron) and a keyboard key (lit while held), 3-slices; the red badge
    an overlay at the tab's top right; the socket kept for a button to come."""
    for on in (True, False):
        im = lift(lambda sc, on=on: FU.tab(sc, 0, 0, 74, 26, "", active=on), 74, 26)
        save("tab_open" if on else "tab_shut", im, slice=[6, 0, 6, 0], tile_x=[6, 10], tile_y=[0, 26], mode="3-slice",
             text=dict(align="center", kind="text", px=16))
    im = lift(lambda sc: FU.tab(sc, 0, 0, 74, 26, "", active=False, badge=" "), 74, 26)
    a = np.asarray(im)[0:12, 60:74]
    save("tab_badge", Image.fromarray(a.copy(), "RGBA"), anchor="the tab's top right, x = w − 14")
    for lit in (False, True):
        im = lift(lambda sc, lit=lit: H.keycap(sc, 0, 0, "", lit=lit), 14, 20)
        save("key_lit" if lit else "key", im, slice=[4, 0, 4, 0], tile_x=[4, 10], tile_y=[0, 20], mode="3-slice",
             text=dict(align="center", kind="title", px=8))
    save("socket", lift(lambda sc: FU.socket(sc, 0, 0, 32, 24), 32, 24))


NAMEPLATE_W = (160, 192, 224, 256, 288)


def nameplates():
    """The cast nameplate of the screen's own action: its top is one arch from end to end, so it can't be sliced —
    it comes at the widths the screens use; the letters are the engine's (title, 16 px, centred)."""
    for w in NAMEPLATE_W:
        for kind, kw in (("hot", dict(hot=True)), ("hot_lit", dict(hot=True, glow=0.12)), ("black", dict(hot=False))):
            im = lift(lambda sc, w=w, kw=kw: FU.nameplate(sc, 0, 0, w, 42, "", **kw), w, 42)
            save(f"nameplate_{kind}_{w}", im, text=dict(align="center", kind="title", px=16, y=14))


def controls():
    """The controls, each in its states, as sprites (no slicing): push-buttons at rest and pressed, the valve
    still and turning, the lever back and thrown, the small round caps."""
    for kind in ("steel", "brass", "rust", "dull", "hot"):
        for pr, nm in ((0.0, "rest"), (1.0, "down")):
            im = lift(lambda sc, kind=kind, pr=pr: FU.pushbutton(sc, 20, 20, 13, kind=kind, press=pr), 40, 40)
            save(f"button_{kind}_{nm}", im, pivot=[20, 20])
    for t_, nm in ((None, "rest"), (0.5, "turning")):
        im = lift(lambda sc, t_=t_: FU.valve(sc, 22, 22, 15, turning=t_ is not None, turn=t_), 44, 44)
        save(f"valve_{nm}", im, pivot=[22, 22])
    for pulled, nm in ((False, "rest"), (True, "thrown")):
        im = lift(lambda sc, pulled=pulled: FU.lever(sc, 22, 8, 58, pulled=pulled), 48, 64)
        save(f"lever_{nm}", im, pivot=[22, 58])
    for kind in ("steel", "brass"):
        for pr, nm in ((0.0, "rest"), (1.0, "down")):
            im = lift(lambda sc, kind=kind, pr=pr: FU.pushbutton(sc, 15, 15, 11, kind=kind, press=pr), 30, 30)
            save(f"cap_{kind}_{nm}", im, pivot=[15, 15], text=dict(align="center", kind="text", px=16))


def glyphs():
    """Every glyph of the effect lines and the damage types in one atlas, 2 px apart, with its name and meaning."""
    import fxg
    import dmg
    items = [(k, fxg.rgba(k), fxg.TERMS[k][0], fxg.TERMS[k][1]) for k in fxg.TERMS]
    items += [("dmg:" + k, dmg.rgba(k), k, "тип урона") for k in dmg.GLYPHS]
    cols, x, y, rowh, pos = 16, 0, 0, 0, {}
    W = 16 * 18
    for i, (k, a, nm, what) in enumerate(items):
        h, w = a.shape[:2]
        if x + w > W:
            x, y, rowh = 0, y + rowh + 2, 0
        pos[k] = dict(x=x, y=y, w=w, h=h, name=nm, meaning=what)
        x += w + 2
        rowh = max(rowh, h)
    atlas = np.zeros((y + rowh, W, 4), np.uint8)
    for k, a, *_ in items:
        p = pos[k]
        atlas[p["y"]:p["y"] + p["h"], p["x"]:p["x"] + p["w"]] = a
    os.makedirs(DST, exist_ok=True)
    Image.fromarray(atlas, "RGBA").save(os.path.join(DST, "glyphs.png"))
    json.dump(dict(image="glyphs.png", glyphs=pos), open(os.path.join(DST, "glyphs.json"), "w"), ensure_ascii=False,
              indent=1)
    return len(items)


def manifest(n_glyphs):
    rel = lambda *p: os.path.join(*p)
    anims = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, "assets", "ui_anim")) if f.endswith(".json"))
    fx = sorted(f[:-5] for f in os.listdir(os.path.join(HERE, "assets", "fx")) if f.endswith(".json"))
    kit = dict(
        name="Литейщик", scale="art px (960×540 screen); draw ×2 nearest",
        pieces=PIECES,
        slicing=("9-slice: corners as they are, edges and middle repeat tile_x / tile_y of the source, cut at the far "
                 "end; 3-slice: the same along x only. pad — transparent margin kept for halos and sparks."),
        glyphs=dict(file="glyphs.json", count=n_glyphs, z=2),
        icons=dict(modules=rel("..", "..", "module_icons.png"), index=rel("..", "..", "module_icons.json"), cell=16),
        animations={a: rel("..", "..", "ui_anim", a + ".json") for a in anims},
        effects={f: rel("..", "..", "fx", f + ".json") for f in fx},
        fonts=dict(
            title=dict(file="tools/sprites/fonts/PressStart2P-Regular.ttf", px=[8, 16, 24], license="OFL 1.1 (в репо)"),
            text=dict(file="GNU Unifont (unifont.otf), 16 px",
                      license="SIL OFL 1.1 (двойная с GPL-2+ и исключением для шрифтов, с версии 13.0.04)",
                      note="не в репозитории: шрифт системный — до выпуска взять релиз с unifoundry.com с текстом OFL")),
        colours=dict(ink="#e6dccc", muted="#8a8478", gold="#f0c878", red="#e05a3a", blue="#9ad8ff",
                     outline="#100c10"),
    )
    json.dump(kit, open(os.path.join(DST, "kit.json"), "w"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- the proof: grown pieces next to drawn ones
def preview():
    """Everything on one sheet; and the test — each sliced piece grown to a new size, beside the same element drawn
    at that size by foundry_ui."""
    sc = FU.forge(960, 540, 5)
    FU.wing(sc, 0, 0, 960, 44)
    from swarm_ui import letters
    letters(sc, "НАБОР ДЛЯ ДВИЖКА", 480, 8, "title", 24, col=(232, 222, 206), col2=(120, 96, 70), align="center")
    canvas = Image.fromarray(np.clip(sc.rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    def put(im, x, y):
        canvas.alpha_composite(im, (int(x), int(y)))

    def label(t, x, y):
        s2 = Scene(len(t) * 9 + 8, 18)
        s2.rgb[:] = 0
        letters(s2, t, 2, 1, "text", 16, col=(150, 142, 128), outline=False, shadow=False)
        a = np.clip(s2.rgb, 0, 255).astype(np.uint8)
        al = (a.max(axis=2) > 20).astype(np.uint8) * 255
        canvas.alpha_composite(Image.fromarray(np.dstack((a, al)), "RGBA"), (int(x), int(y)))

    def src(name):
        return Image.open(os.path.join(DST, PIECES[name]["file"])).convert("RGBA")

    # row 1: the plate grown (left) and drawn (right), shaded alike
    p = PIECES["plate"]
    W_, H_ = 38 + 18 * 9, 38 + 18 * 5
    label("сборка 9-slice", 12, 52)
    put(shade(grow(src("plate"), W_, H_, p["slice"], p["tile_x"], p["tile_y"])), 12, 70)
    label("нарисовано", 224, 52)
    put(shade(lift(lambda s: FU.plate(s, 0, 0, W_, H_, seed=1, shade=False), W_, H_)), 224, 70)
    # cells grown to 150×52, each state; and drawn at the same size under the first two
    label("ячейки: сборка", 440, 52)
    for i, st in enumerate(CELL_STATES):
        c = PIECES[f"cell_{st}"]
        g = grow(src(f"cell_{st}"), 126, 52, c["slice"], c["tile_x"], c["tile_y"])
        put(g, 436 + (i % 4) * 128, 68 + (i // 4) * 54)
    put(src("cell_hi_tab"), 436 + 128, 68 + 52 // 2 - 8)
    label("нарисовано", 440, 178)
    for i, st in enumerate(("hover", "broken")):
        put(lift(lambda s, st=st: FU.cell(s, 4, 4, 122, 48, st, seed=1), 126, 52), 436 + i * 128, 196)
    # tags grown to 150, the beam and the sill grown, the tabs and keys
    y = 262
    label("бирки, вкладки, клавиши", 12, y - 18)
    for i, kind in enumerate(("steel", "brass", "rust", "dull")):
        t_ = PIECES[f"tag_{kind}"]
        put(grow(src(f"tag_{kind}"), 150, 26, t_["slice"], t_["tile_x"], t_["tile_y"]), 12 + i * 160, y)
    for i, nm in enumerate(("tab_open", "tab_shut")):
        t_ = PIECES[nm]
        put(grow(src(nm), 100, 26, t_["slice"], t_["tile_x"], t_["tile_y"]), 660 + i * 106, y)
    put(src("tab_badge"), 660 + 106 + 100 - 14, y)
    for i, nm in enumerate(("key", "key_lit")):
        t_ = PIECES[nm]
        put(grow(src(nm), 44, 20, t_["slice"], t_["tile_x"], t_["tile_y"]), 880 + i * 0, y + 30 * i)
    put(src("socket"), 12, y + 34)
    w_ = PIECES["wing"]
    put(grow(src("wing"), 400, 44, w_["slice"], w_["tile_x"], w_["tile_y"]), 60, y + 34)
    s_ = PIECES["sill"]
    put(grow(src("sill"), 400, 72, s_["slice"], s_["tile_x"], s_["tile_y"]), 470, y + 34)
    # the controls and the nameplates
    y = 392
    label("органы управления", 12, y - 18)
    x = 12
    for kind in ("steel", "brass", "rust", "dull", "hot"):
        for nm in ("rest", "down"):
            put(src(f"button_{kind}_{nm}"), x, y)
            x += 36
    for nm in ("valve_rest", "valve_turning"):
        put(src(nm), x, y - 2)
        x += 44
    for nm in ("lever_rest", "lever_thrown"):
        put(src(nm), x, y - 20)
        x += 46
    for kind in ("steel", "brass"):
        for nm in ("rest", "down"):
            put(src(f"cap_{kind}_{nm}"), x, y + 4)
            x += 30
    label("таблички (ширины 160…288)", 12, 444)
    x = 12
    for kind, w in (("hot", 160), ("hot_lit", 192), ("black", 224)):
        put(src(f"nameplate_{kind}_{w}"), x, 464)
        x += w + 12
    gl = Image.open(os.path.join(DST, "glyphs.png")).convert("RGBA")
    label("значки", 640, 444)
    put(gl, 640, 464)
    canvas = canvas.convert("RGB").resize((1920, 1080), Image.NEAREST)
    canvas.save(out("foundry_engine_kit.png"))
    print("foundry_engine_kit.png", canvas.size)


if __name__ == "__main__":
    plate()
    cells()
    tags()
    beams()
    tabs_keys()
    nameplates()
    controls()
    n = glyphs()
    manifest(n)
    print(len(PIECES), "pieces,", n, "glyphs ->", DST)
    preview()
