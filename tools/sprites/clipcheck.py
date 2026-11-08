"""Clipping check for models built from named part groups.

Every primitive is filled with points on a regular grid; for each pair of groups the shared
volume is reported. Pairs that are meant to touch (a hand on a haft, a leg in the pelvis) are
passed as `allowed`; everything else should come out near zero.

    from clipcheck import report
    report(groups, allowed)          # groups: {name: Model}
"""
import numpy as np

STEP = 0.25


def _grid(lo, hi):
    lo = np.floor(np.asarray(lo) / STEP).astype(int)
    hi = np.ceil(np.asarray(hi) / STEP).astype(int)
    ax = [np.arange(a, b + 1) for a, b in zip(lo, hi)]
    g = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
    return g, g * STEP


def _inside(op, p):
    k = op[0]
    if k == "box":
        c, size, R = op[1], op[2], op[4]
        q = (p - c) @ R
        return np.all(np.abs(q) <= size / 2, axis=1)
    if k == "cyl":
        p0, p1, r0, r1 = op[1], op[2], op[3], op[4]
        a = p1 - p0
        L2 = a @ a
        t = ((p - p0) @ a) / L2
        d = p - p0 - np.outer(t, a)
        r = r0 + (r1 - r0) * np.clip(t, 0, 1)
        return (t >= 0) & (t <= 1) & (np.einsum("ij,ij->i", d, d) <= r * r)
    if k == "ell":
        c, rad, R = op[1], op[2], op[4]
        q = ((p - c) @ R) / rad
        return np.einsum("ij,ij->i", q, q) <= 1
    if k == "solid":
        v = np.array(op[1])
        cen = v.mean(0)
        ok = np.ones(len(p), bool)
        for f in op[2]:
            a, b, c = v[f[0]], v[f[1]], v[f[2]]
            n = np.cross(b - a, c - a)
            if np.linalg.norm(n) < 1e-9:
                continue
            if (cen - a) @ n > 0:
                n = -n
            ok &= (p - a) @ n <= 1e-9
        return ok
    if k == "limb":
        pts, w = op[1], op[2] / 2
        ok = np.zeros(len(p), bool)
        for a, b in zip(pts[:-1], pts[1:]):
            ab = b - a
            t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
            d = p - a - np.outer(t, ab)
            ok |= np.einsum("ij,ij->i", d, d) <= w * w
        return ok
    return np.zeros(len(p), bool)


def _bounds(op):
    k = op[0]
    if k == "box":
        e = np.abs(op[4]) @ (op[2] / 2)
        return op[1] - e, op[1] + e
    if k == "cyl":
        r = max(op[3], op[4])
        return np.minimum(op[1], op[2]) - r, np.maximum(op[1], op[2]) + r
    if k == "ell":
        e = np.abs(op[4]) @ op[2]
        return op[1] - e, op[1] + e
    if k == "solid":
        v = np.array(op[1])
        return v.min(0), v.max(0)
    if k == "limb":
        v = np.array(op[1])
        return v.min(0) - op[2], v.max(0) + op[2]
    return None


def cells(model):
    """Set of grid cells inside the model."""
    out = set()
    for op in model.ops:
        if op[0] not in ("box", "cyl", "ell", "solid", "limb"):
            continue
        mat = op[3] if op[0] in ("box", "ell") else (op[5] if op[0] == "cyl" else op[-1])
        if getattr(mat, "smoke", False) or getattr(mat, "emissive", None) is not None and op[0] == "ell" and mat.glow_r >= 10:
            continue                                   # puffs and loose sparks are not solid
        lo, hi = _bounds(op)
        g, p = _grid(lo, hi)
        m = _inside(op, p)
        out.update(map(tuple, g[m]))
    return out


def report(groups, allowed=(), skip=(), min_vol=0.05):
    allowed = {frozenset(a) for a in allowed}
    names = [n for n in groups if n not in skip]
    C = {n: cells(groups[n]) for n in names}
    bad = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if frozenset((a, b)) in allowed:
                continue
            v = len(C[a] & C[b]) * STEP ** 3
            if v >= min_vol:
                bad.append((v, a, b))
    bad.sort(reverse=True)
    return bad
