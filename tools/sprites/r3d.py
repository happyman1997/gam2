"""Tiny 3/4-view rasteriser: boxes, cylinders, ellipsoids and limbs -> banded pixel art.

Local model space: +x forward, +y up, +z the creature's near side. The model is turned by YAW
towards the viewer and seen from slightly above (PITCH), orthographic, 1 unit = 1 pixel.
"""
import numpy as np
from PIL import Image, ImageDraw
from kit import Sprite, OUTLINE, shift, hexc, BAYER

YAW = np.radians(38)
PITCH = np.radians(24)
SA, CA = np.sin(PITCH), np.cos(PITCH)
TO_CAM = np.array([0.0, SA, CA])
LIGHT = np.array([-0.35, 0.75, 0.56]); LIGHT /= np.linalg.norm(LIGHT)
AMB, DIF = 0.30, 0.72


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def rot_z(a):
    """Pitch a part in its x-y plane (positive = nose up)."""
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


I3 = np.eye(3)


class Model:
    def __init__(self):
        self.ops = []

    def box(self, c, size, mat, R=I3):
        self.ops.append(("box", np.array(c, float), np.array(size, float), mat, R))

    def cyl(self, p0, p1, r0, mat, r1=None, seg=8):
        self.ops.append(("cyl", np.array(p0, float), np.array(p1, float), r0, r0 if r1 is None else r1, mat, seg))

    def ell(self, c, radii, mat, R=I3):
        self.ops.append(("ell", np.array(c, float), np.array(radii, float), mat, R))

    def limb(self, pts, width, mat, band=2):
        self.ops.append(("limb", [np.array(p, float) for p in pts], width, mat, band))

    def poly(self, pts, mat):
        self.ops.append(("poly", [np.array(p, float) for p in pts], mat))

    def solid(self, verts, faces, mat):
        self.ops.append(("solid", [np.array(v, float) for v in verts], faces, mat))

    def transformed(self, R=I3, t=(0, 0, 0)):
        """Copy of the model rotated by R about the origin and moved by t (for whole-body poses)."""
        m = Model()
        t = np.array(t, float)
        for op in self.ops:
            k = op[0]
            if k == "box":
                m.ops.append(("box", R @ op[1] + t, op[2], op[3], R @ op[4]))
            elif k == "cyl":
                m.ops.append(("cyl", R @ op[1] + t, R @ op[2] + t, op[3], op[4], op[5], op[6]))
            elif k == "ell":
                m.ops.append(("ell", R @ op[1] + t, op[2], op[3], R @ op[4]))
            elif k == "limb":
                m.ops.append(("limb", [R @ p + t for p in op[1]], op[2], op[3], op[4]))
            elif k == "poly":
                m.ops.append(("poly", [R @ p + t for p in op[1]], op[2]))
            elif k == "solid":
                m.ops.append(("solid", [R @ p + t for p in op[1]], op[2], op[3]))
        return m

    def scaled(self, k):
        m = Model()
        for op in self.ops:
            t = op[0]
            if t == "box":
                m.ops.append(("box", op[1] * k, op[2] * k, op[3], op[4]))
            elif t == "cyl":
                m.ops.append(("cyl", op[1] * k, op[2] * k, op[3] * k, op[4] * k, op[5], op[6]))
            elif t == "ell":
                m.ops.append(("ell", op[1] * k, op[2] * k, op[3], op[4]))
            elif t == "limb":
                wd = op[2] if k < 1.4 else max(op[2], int(round(op[2] * k * 0.75)))
                m.ops.append(("limb", [p * k for p in op[1]], wd, op[3], op[4]))
            elif t == "poly":
                m.ops.append(("poly", [p * k for p in op[1]], op[2]))
            elif t == "solid":
                m.ops.append(("solid", [p * k for p in op[1]], op[2], op[3]))
        return m

    def extend(self, other):
        self.ops.extend(other.ops)


class Mat:
    def __init__(self, ramp, emissive=None, glow_r=0, glow_k=0.0, noise=0.0, alt=None, alt_amt=0.0, dither=False):
        self.ramp = ramp
        self.emissive = emissive  # glow colour (array) or None
        self.glow_r, self.glow_k = glow_r, glow_k
        self.noise = noise        # chance a pixel drops / gains one band: worn, rough surfaces
        self.alt, self.alt_amt = alt, alt_amt  # blotches of another ramp: rust, patina, mottling
        self.dither = dither      # half-transparent (wings): keep a checkerboard only
        self.smoke = False        # not drawn: becomes a soft puff in the scene


class Raster:
    def __init__(self, w, h, ox, oy, yaw=YAW):
        self.w, self.h, self.ox, self.oy = w, h, ox, oy
        self.Ry = rot_y(yaw)
        self.z = np.full((h, w), -1e9)
        self.mat = np.full((h, w), -1, dtype=np.int32)
        self.idx = np.zeros((h, w), dtype=np.int8)
        self.thin = np.zeros((h, w), dtype=bool)
        self.mats = []
        self.emits = []
        self.smokes = []
        self.amb, self.dif, self.gradient = AMB, DIF, True
        self.yy, self.xx = np.mgrid[0:h, 0:w]

    # world -> screen
    def proj(self, p_local):
        p = self.Ry @ p_local
        sx = p[0] + self.ox
        sy = p[2] * SA - p[1] * CA + self.oy
        d = p[1] * SA + p[2] * CA
        return sx, sy, d

    def mat_id(self, m):
        for i, mm in enumerate(self.mats):
            if mm is m:
                return i
        self.mats.append(m)
        return len(self.mats) - 1

    def band(self, n_world, m):
        if m.emissive is not None:
            b = max(0.0, float(n_world @ TO_CAM))
            return int(np.clip(2 + b * 2.99, 2, 4))
        b = self.amb + self.dif * max(0.0, float(n_world @ LIGHT))
        return int(np.clip(b * 4.999, 1, 4))

    def write(self, mask, depth, m, idx, thin=False):
        upd = mask & (depth > self.z + 0.01)
        self.thin[upd] = thin
        self.z[upd] = depth[upd] if np.ndim(depth) else depth
        self.mat[upd] = self.mat_id(m)
        if np.ndim(idx):
            self.idx[upd] = idx[upd]
        else:
            self.idx[upd] = idx

    def face(self, pts_local, n_local_world, m):
        n = n_local_world / (np.linalg.norm(n_local_world) + 1e-9)
        if n @ TO_CAM <= 0.0:
            return
        P = [self.proj(p) for p in pts_local]
        img = Image.new("1", (self.w, self.h), 0)
        ImageDraw.Draw(img).polygon([(x, y) for x, y, _ in P], fill=1)
        mask = np.array(img, dtype=bool)
        if not mask.any():
            return
        # depth plane through the first three projected vertices
        (x0, y0, d0), (x1, y1, d1), (x2, y2, d2) = P[0], P[1], P[2]
        A = np.array([[x0, y0, 1], [x1, y1, 1], [x2, y2, 1]])
        try:
            a, b, c = np.linalg.solve(A, [d0, d1, d2])
            depth = a * self.xx + b * self.yy + c
        except np.linalg.LinAlgError:
            depth = np.full(mask.shape, np.mean([d0, d1, d2]))
        if m.emissive is None and self.gradient:
            # vertical falloff across the face, dithered: lit at the top, darker at the bottom
            b0 = self.amb + self.dif * max(0.0, float(n @ LIGHT))
            ys = np.nonzero(mask)[0]
            y_top, y_bot = ys.min(), ys.max()
            span = max(y_bot - y_top, 1)
            g = (self.yy - y_top) / span
            k = 0.12 if span > 6 else 0.05
            b = b0 + k * (0.5 - g)
            th = BAYER[self.yy % 4, self.xx % 4]
            idx = np.clip(np.floor(b * 4.999 + (th - 0.5) * 0.4), 1, 4).astype(np.int8)
            self.write(mask, depth, m, idx)
        else:
            self.write(mask, depth, m, self.band(n, m))

    def do_box(self, c, size, m, R):
        hx, hy, hz = size / 2
        Q = self.Ry @ R
        axes = [np.array(v, float) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
        hs = (hx, hy, hz)
        for ai in range(3):
            for sgn in (1, -1):
                n = axes[ai] * sgn
                u = axes[(ai + 1) % 3] * hs[(ai + 1) % 3]
                v = axes[(ai + 2) % 3] * hs[(ai + 2) % 3]
                ctr = n * hs[ai]
                quad = [ctr + u + v, ctr - u + v, ctr - u - v, ctr + u - v]
                self.face([c + R @ q for q in quad], Q @ n, m)

    def do_cyl(self, p0, p1, r0, r1, m, seg):
        ax = p1 - p0
        L = np.linalg.norm(ax)
        if L < 1e-6:
            return
        ax = ax / L
        t = np.array([0, 1.0, 0]) if abs(ax[1]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(ax, t); u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        angs = [2 * np.pi * i / seg + np.pi / seg for i in range(seg)]
        ring0 = [p0 + r0 * (np.cos(a) * u + np.sin(a) * v) for a in angs]
        ring1 = [p1 + r1 * (np.cos(a) * u + np.sin(a) * v) for a in angs]
        for i in range(seg):
            j = (i + 1) % seg
            am = (angs[i] + angs[j]) / 2 + (np.pi if j == 0 else 0)
            n = np.cos(am) * u + np.sin(am) * v + ax * (r0 - r1) / L
            self.face([ring0[i], ring0[j], ring1[j], ring1[i]], self.Ry @ n, m)
        self.face(ring0[::-1], self.Ry @ (-ax), m)
        self.face(ring1, self.Ry @ ax, m)

    def do_ell(self, c, radii, m, R):
        Q = self.Ry @ R
        cw = self.Ry @ c
        S = np.diag(radii)
        M = np.diag(1 / radii) @ Q.T
        rmax = radii.max()
        sx_c, sy_c, _ = self.proj(c)
        x0, x1 = int(max(sx_c - rmax - 2, 0)), int(min(sx_c + rmax + 2, self.w))
        y0, y1 = int(max(sy_c - rmax - 2, 0)), int(min(sy_c + rmax + 2, self.h))
        if x1 <= x0 or y1 <= y0:
            return
        xs = self.xx[y0:y1, x0:x1] - self.ox + 0.0
        ys = self.yy[y0:y1, x0:x1] - self.oy + 0.0
        A = np.stack([xs, -ys * CA, ys * SA], -1) - cw
        B = np.array([0, SA, CA])
        u = A @ M.T
        w = M @ B
        aa = w @ w
        bb = 2 * (u @ w)
        cc = (u * u).sum(-1) - 1
        disc = bb * bb - 4 * aa * cc
        hit = disc >= 0
        t = (-bb + np.sqrt(np.maximum(disc, 0))) / (2 * aa)
        q = u + t[..., None] * w
        n = q @ (Q @ np.diag(1 / radii)).T
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        if m.emissive is not None:
            b = np.clip(n @ TO_CAM, 0, 1)
            idx = np.clip(2 + b * 2.99, 2, 4).astype(np.int8)
        else:
            b = self.amb + self.dif * np.clip(n @ LIGHT, 0, 1)
            idx = np.clip(b * 4.999, 1, 4).astype(np.int8)
        mask = np.zeros((self.h, self.w), dtype=bool)
        depth = np.full((self.h, self.w), -1e9)
        idxf = np.zeros((self.h, self.w), dtype=np.int8)
        mask[y0:y1, x0:x1] = hit
        depth[y0:y1, x0:x1] = np.where(hit, t, -1e9)
        idxf[y0:y1, x0:x1] = idx
        self.write(mask, depth, m, idxf)

    def do_limb(self, pts, width, m, band):
        for a, b in zip(pts[:-1], pts[1:]):
            xa, ya, da = self.proj(a)
            xb, yb, db = self.proj(b)
            img = Image.new("1", (self.w, self.h), 0)
            ImageDraw.Draw(img).line([(xa, ya), (xb, yb)], fill=1, width=width)
            mask = np.array(img, dtype=bool)
            self.write(mask, np.full(mask.shape, (da + db) / 2 + 0.5), m, band, thin=width <= 1)

    def do_poly(self, pts, m):
        n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
        nw = self.Ry @ n
        if nw @ TO_CAM < 0:
            nw = -nw
            pts = pts[::-1]
        self.face(pts, nw, m)

    def do_solid(self, verts, faces, m):
        cen = np.mean(verts, axis=0)
        for f in faces:
            pts = [verts[i] for i in f]
            n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.linalg.norm(n) < 1e-9:
                continue
            if n @ (np.mean(pts, axis=0) - cen) < 0:
                n = -n
                pts = pts[::-1]
            self.face(pts, self.Ry @ n, m)

    def render(self, model):
        for op in model.ops:
            k = op[0]
            if k == "ell" and getattr(op[3], "smoke", False):
                sx, sy, _ = self.proj(op[1])
                self.smokes.append((sx, sy, float(op[2].max()) * 1.6))
                continue
            if k == "solid":
                self.do_solid(op[1], op[2], op[3])
                continue
            if k == "box":
                self.do_box(op[1], op[2], op[3], op[4])
            elif k == "cyl":
                self.do_cyl(*op[1:])
            elif k == "ell":
                self.do_ell(op[1], op[2], op[3], op[4])
            elif k == "limb":
                self.do_limb(op[1], op[2], op[3], op[4])
            elif k == "poly":
                self.do_poly(op[1], op[2])
            m = op[3] if k in ("box", "ell") else (op[5] if k == "cyl" else (op[3] if k == "limb" else op[2]))
            if m.emissive is not None and m.glow_r:
                p = op[1] if k in ("box", "ell") else (op[2] if k == "cyl" else op[1][-1])
                sx, sy, _ = self.proj(p)
                self.emits.append((sx, sy, m.glow_r, m.emissive, m.glow_k))

    def sprite(self, edge=2.2, outline_tint=0.5, seed=0):
        s = Sprite(self.w, self.h)
        a = self.mat >= 0
        idx = self.idx.copy()
        rng = np.random.default_rng(seed)
        white = rng.random((self.h, self.w))
        # low-frequency blotches for rust / patina
        lo = rng.random((self.h // 4 + 2, self.w // 4 + 2))
        lo = np.kron(lo, np.ones((4, 4)))[:self.h, :self.w]
        lo = (lo + np.roll(lo, 2, 0) + np.roll(lo, 2, 1) + np.roll(np.roll(lo, 2, 0), 2, 1)) / 4
        altsel = np.zeros_like(a)
        holes = np.zeros_like(a)
        for i, m in enumerate(self.mats):
            sel = self.mat == i
            if m.noise:
                up = sel & (white < m.noise / 2)
                dn = sel & (white > 1 - m.noise / 2)
                idx[up] = np.minimum(idx[up] + 1, 4)
                idx[dn] = np.maximum(idx[dn] - 1, 1)
            if m.alt is not None and m.alt_amt:
                altsel |= sel & (lo > 1 - m.alt_amt)
            if m.dither:
                holes |= sel & ((self.xx + self.yy) % 2 == 1)
        z = np.where(a, self.z, -1e9)
        emis = np.zeros_like(a)
        for i, m in enumerate(self.mats):
            if m.emissive is not None or m.dither:
                emis |= self.mat == i
        if getattr(self, "edges", True):
            # crisp lit rims on the upper/left edges of every part: what makes it read as metal
            up_z = shift(z, 0, 1, fill=-1e9)
            lf_z = shift(z, 1, 0, fill=-1e9)
            rim = a & ~emis & ~self.thin & ((up_z < z - edge) | (lf_z < z - edge * 2))
            idx[rim] = np.minimum(idx[rim] + 1, 4)
        if getattr(self, "grime", 0) > 0:
            wy = -(self.yy - self.oy) * CA + z * SA          # world height of each pixel
            top = np.percentile(wy[a], 95) if a.any() else 1
            g = np.clip(1 - wy / (top * self.grime), 0, 1)
            th = BAYER[self.yy % 4, self.xx % 4]
            dirty = a & ~emis & (g > th * 1.15)
            idx[dirty] = np.maximum(idx[dirty] - 1, 0)
        # occlusion lines: a pixel just behind a nearer part gets darker
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nz = shift(z, dx, dy, fill=-1e9)
            na = shift(a, dx, dy)
            behind = a & na & (nz > z + edge)
            idx[behind] = np.maximum(idx[behind] - 2, 0)
        for i, m in enumerate(self.mats):
            sel = self.mat == i
            rp = m.ramp
            for k, col in enumerate(rp):
                s.rgb[sel & (idx == k)] = col
            if m.alt is not None:
                for k, col in enumerate(m.alt):
                    s.rgb[sel & altsel & (idx == k)] = col
        s.a = a
        s.emit = [(x, y, r, c, k) for (x, y, r, c, k) in self.emits]
        s.smokes = list(self.smokes)
        soft = np.zeros_like(a)
        for i, m in enumerate(self.mats):
            if m.dither:
                soft |= self.mat == i
        s.a = a & ~self.thin & ~soft  # thin limbs and soft stuff get no outline of their own
        s.outline(tint=outline_tint)
        s.a |= a
        s.a &= ~holes
        return s


def render(model, w, h, ox, oy, yaw=YAW, outline_tint=0.5, seed=0, edges=True, grime=0.0,
           amb=None, dif=None, gradient=True):
    r = Raster(w, h, ox, oy, yaw)
    r.edges, r.grime, r.gradient = edges, grime, gradient
    if amb is not None:
        r.amb = amb
    if dif is not None:
        r.dif = dif
    r.render(model)
    return r.sprite(outline_tint=outline_tint, seed=seed)
