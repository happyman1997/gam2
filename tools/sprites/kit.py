"""Tiny pixel-art kit: aliased masks, ramp shading, outlines, part shadows, additive light."""
import numpy as np
from PIL import Image, ImageDraw


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def ramp(*cols):
    return [hexc(c) for c in cols]


OUTLINE = hexc("#0b0a10")

IRON = ramp("#1a1b24", "#2d2f3d", "#474a5b", "#6c7083", "#a2a7b8")
DIRON = ramp("#121219", "#1e1f29", "#2f3140", "#474a5b", "#6c7083")
BRONZE = ramp("#2b1812", "#55301f", "#86532f", "#b78243", "#e4bb6a")
FIRE = ramp("#5a1408", "#a8320e", "#e86a1a", "#ffb43a", "#fff3c0")
VOLT = ramp("#0e2a3a", "#16607a", "#2ab0c8", "#7ae8f0", "#e8fffd")
GLOWG = ramp("#173a12", "#2f7a1e", "#5ec42e", "#a8f05a", "#efffc0")
WING = ramp("#221f33", "#3a3654", "#5a5680", "#8682aa", "#b4b0d4")
BONE = ramp("#3a3028", "#6a5a48", "#a08c70", "#d0c0a0", "#f4ecd8")


def chitin(hue_shift=0.0):
    """Chitin ramp, hue shifted for inherited colouring."""
    import colorsys
    base = ["#120a1a", "#2a1238", "#461e58", "#6a3478", "#9a5aa0"]
    out = []
    for c in base:
        r, g, b = (hexc(c) / 255).tolist()
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        h = (h + hue_shift) % 1.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        out.append(np.array([r * 255, g * 255, b * 255], dtype=np.float32))
    return out


def blank_mask(w, h):
    return Image.new("1", (w, h), 0)


def to_np(m):
    return np.array(m, dtype=bool)


def m_rect(w, h, x0, y0, x1, y1):
    m = blank_mask(w, h)
    ImageDraw.Draw(m).rectangle([x0, y0, x1, y1], fill=1)
    return to_np(m)


def m_rrect(w, h, x0, y0, x1, y1, r=2):
    m = blank_mask(w, h)
    ImageDraw.Draw(m).rounded_rectangle([x0, y0, x1, y1], radius=r, fill=1)
    return to_np(m)


def m_ellipse(w, h, x0, y0, x1, y1):
    m = blank_mask(w, h)
    ImageDraw.Draw(m).ellipse([x0, y0, x1, y1], fill=1)
    return to_np(m)


def m_poly(w, h, pts):
    m = blank_mask(w, h)
    ImageDraw.Draw(m).polygon(pts, fill=1)
    return to_np(m)


def m_line(w, h, pts, width=1):
    m = blank_mask(w, h)
    ImageDraw.Draw(m).line(pts, fill=1, width=width)
    return to_np(m)


def shift(a, dx, dy, fill=False):
    out = np.full_like(a, fill)
    h, w = a.shape
    ys = slice(max(dy, 0), h + min(dy, 0))
    yd = slice(max(-dy, 0), h + min(-dy, 0))
    xs = slice(max(dx, 0), w + min(dx, 0))
    xd = slice(max(-dx, 0), w + min(-dx, 0))
    out[ys, xs] = a[yd, xd]
    return out


def shade_box(mask, base=2):
    """Index map: lit top/left rims, dark bottom/right rims."""
    idx = np.full(mask.shape, base, dtype=np.int8)
    above = shift(mask, 0, 1)   # value of pixel above
    below = shift(mask, 0, -1)
    left = shift(mask, 1, 0)
    right = shift(mask, -1, 0)
    top_e = mask & ~above
    bot_e = mask & ~below
    left_e = mask & ~left
    right_e = mask & ~right
    idx[left_e] = base + 1
    idx[right_e] = base - 1
    idx[bot_e] = base - 1
    below2 = shift(mask, 0, -2)
    idx[mask & below & ~below2 & right_e] = base - 2
    idx[bot_e & right_e] = base - 2
    idx[top_e] = base + 1
    idx[top_e & left_e] = min(base + 2, 4)
    return idx


def shade_sphere(mask, lx=-0.35, ly=-0.4, bands=(0.28, 0.62, 0.92, 1.15), top=4):
    ys, xs = np.nonzero(mask)
    idx = np.zeros(mask.shape, dtype=np.int8)
    if len(xs) == 0:
        return idx
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = max((x1 - x0 + 1) / 2, 1), max((y1 - y0 + 1) / 2, 1)
    px, py = cx + lx * rx, cy + ly * ry
    yy, xx = np.mgrid[0:mask.shape[0], 0:mask.shape[1]]
    d = np.sqrt(((xx - px) / rx) ** 2 + ((yy - py) / ry) ** 2)
    lvl = np.full(mask.shape, top - 4, dtype=np.int8)
    for i, b in enumerate(reversed(bands)):
        lvl[d < b] = top - 3 + i
    idx[mask] = np.clip(lvl[mask], 0, 4)
    return idx


class Sprite:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), dtype=np.float32)
        self.a = np.zeros((h, w), dtype=bool)
        self.emit = []  # (x, y, radius, colour, strength)
        self.smokes = []  # (x, y, radius)

    def paint(self, mask, ramp_, idx=None, shading="box", base=2, shadow=True, flat=None):
        """Draw a part. shadow: darken what lies just below/right of the part."""
        if shadow:
            grown = shift(mask, 1, 1) | shift(mask, 0, 1)
            sh = grown & ~mask & self.a
            self.rgb[sh] *= 0.55
        if flat is not None:
            self.rgb[mask] = ramp_[flat]
        else:
            if idx is None:
                idx = shade_box(mask, base) if shading == "box" else shade_sphere(mask)
            idx = np.clip(idx, 0, len(ramp_) - 1)
            for i, c in enumerate(ramp_):
                self.rgb[mask & (idx == i)] = c
        self.a |= mask

    def px(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rgb[y, x] = col
            self.a[y, x] = True

    def outline(self, col=OUTLINE, tint=0.22):
        a = self.a
        n = shift(a, 1, 0) | shift(a, -1, 0) | shift(a, 0, 1) | shift(a, 0, -1)
        ring = n & ~a
        # tinted outline: a little of the neighbour colour
        neigh = np.zeros_like(self.rgb)
        cnt = np.zeros(a.shape, dtype=np.float32)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sa = shift(a, dx, dy)
            sr = np.zeros_like(self.rgb)
            h, w = a.shape
            ys = slice(max(dy, 0), h + min(dy, 0)); yd = slice(max(-dy, 0), h + min(-dy, 0))
            xs = slice(max(dx, 0), w + min(dx, 0)); xd = slice(max(-dx, 0), w + min(-dx, 0))
            sr[ys, xs] = self.rgb[yd, xd]
            neigh += sr * sa[..., None]
            cnt += sa
        neigh /= np.maximum(cnt, 1)[..., None]
        self.rgb[ring] = col * (1 - tint) + neigh[ring] * tint
        self.a |= ring

    def flipped(self):
        s = Sprite(self.w, self.h)
        s.rgb = self.rgb[:, ::-1].copy()
        s.a = self.a[:, ::-1].copy()
        s.emit = [(self.w - 1 - x, y, r, c, k) for (x, y, r, c, k) in self.emit]
        s.smokes = [(self.w - 1 - x, y, r) for (x, y, r) in self.smokes]
        return s

    def image(self, scale=1):
        out = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        out[..., :3] = np.clip(self.rgb, 0, 255).astype(np.uint8)
        out[..., 3] = self.a * 255
        im = Image.fromarray(out, "RGBA")
        if scale != 1:
            im = im.resize((self.w * scale, self.h * scale), Image.NEAREST)
        return im


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


class Scene:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), dtype=np.float32)
        self.light = np.zeros((h, w, 3), dtype=np.float32)
        self.occ = np.zeros((h, w), dtype=bool)
        self.yy, self.xx = np.mgrid[0:h, 0:w]

    def blit(self, spr, x, y, emit=True):
        h, w = spr.h, spr.w
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        if x1 <= x0 or y1 <= y0:
            return
        sa = spr.a[y0 - y:y1 - y, x0 - x:x1 - x]
        sr = spr.rgb[y0 - y:y1 - y, x0 - x:x1 - x]
        reg = self.rgb[y0:y1, x0:x1]
        reg[sa] = sr[sa]
        self.occ[y0:y1, x0:x1] |= sa
        if emit:
            for (ex, ey, r, c, k) in spr.emit:
                self.glow(x + ex, y + ey, r, c, k)
        for (sx, sy, r) in getattr(spr, "smokes", []):
            self.smoke(x + sx, y + sy, r)

    def smoke(self, x, y, r, col=None, k=0.55):
        col = hexc("#55555a") if col is None else col
        d = np.sqrt((self.xx - x) ** 2 + ((self.yy - y) * 1.15) ** 2) / r
        th = BAYER[self.yy % 4, self.xx % 4]
        a = np.clip(1 - d, 0, 1) ** 0.7 * k
        a = np.floor(a * 4 + th * 0.99) / 4          # stepped and dithered: reads as pixel smoke
        sel = a > 0
        self.rgb[sel] = self.rgb[sel] * (1 - a[sel, None]) + col * a[sel, None]

    def glow(self, x, y, r, col, k=1.0):
        d = np.sqrt((self.xx - x) ** 2 + ((self.yy - y) * 1.2) ** 2) / r
        v = np.clip(1 - d, 0, 1) ** 1.5
        self.light += v[..., None] * (col / 255.0)[None, None, :] * k * 120

    def compose(self, step=22.0):
        th = BAYER[self.yy % 4, self.xx % 4][..., None]
        bg = np.floor(self.light / step + th) * step            # dithered on the ground
        fg = np.floor(self.light * 0.5 / step + 0.5) * step     # clean bands on sprites
        L = np.where(self.occ[..., None], fg, bg)
        return np.clip(self.rgb + L, 0, 255)

    def image(self, scale=1):
        im = Image.fromarray(self.compose().astype(np.uint8), "RGB")
        if scale != 1:
            im = im.resize((self.w * scale, self.h * scale), Image.NEAREST)
        return im


# ---------------- muted, less cartoony palette ----------------
STEEL = ramp("#17181c", "#2c2e33", "#46494e", "#6a6d70", "#9b9d9c")
DSTEEL = ramp("#101114", "#1d1e22", "#2d2f34", "#43464b", "#62656a")
BRASS = ramp("#271c10", "#48361f", "#6d5532", "#957a4a", "#c0a674")
VERDI = ramp("#16201b", "#26362d", "#3a5143", "#557060", "#7a9483")
RUST = ramp("#1e110b", "#3a1f12", "#5a311b", "#7a4626", "#9a6038")
EMBER = ramp("#3a0e06", "#7a2208", "#c2500e", "#f08a2a", "#ffd890")
ARC = ramp("#0c2028", "#174654", "#2a7e8e", "#62b8c0", "#c8f0ee")
LEATHER = ramp("#1a120c", "#2e2016", "#463222", "#614834", "#7e644c")
HORN = ramp("#2a241c", "#4a4030", "#6e624a", "#968866", "#bcae8a")
MEMBRANE = ramp("#3a2e22", "#5a4836", "#7e6a50", "#a08c6e", "#c4b490")


def chit2(kind="brown"):
    base = {
        "brown": ["#0c0907", "#1c140f", "#2e2018", "#463224", "#634a36"],
        "rust": ["#110806", "#26110b", "#3d1d12", "#5a2e1d", "#7c442c"],
        "olive": ["#0a0b07", "#181a10", "#272a1a", "#3c3f28", "#56593a"],
        "black": ["#08090c", "#121419", "#1e2128", "#2e323c", "#464b58"],
    }[kind]
    return ramp(*base)


def rim_light(spr, col="#c0b0d0", k=0.65):
    """A thin rim just under the top outline (and weaker on the left): dark bodies stay readable on dark ground."""
    a = spr.a
    above = np.zeros_like(a)
    above[1:] = a[:-1]
    top = a & ~above
    rim = np.zeros_like(a)
    rim[1:] = top[:-1]
    rim &= a & ~top
    left = np.zeros_like(a)
    left[:, 1:] = a[:, :-1]
    edge_l = a & ~left
    side = np.zeros_like(a)
    side[:, 1:] = edge_l[:, :-1]
    side &= a & ~edge_l & ~rim
    c = hexc(col)
    spr.rgb[rim] = spr.rgb[rim] * (1 - k) + c * k
    spr.rgb[side] = spr.rgb[side] * (1 - k * 0.5) + c * k * 0.5
    return spr
