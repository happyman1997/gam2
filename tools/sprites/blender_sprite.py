"""Golem sprites through Blender: the same model the game's renderer draws (r3d — boxes, cylinders, ellipsoids,
limbs, polygons), rebuilt in Blender and rendered at the sprite's own size with no smoothing. Blender gives three
plain pictures — which part and material each pixel is, which way its surface faces, how near it is; the sprite is
then put together here: each material's own ramp, the light in hard steps (no gradients, no dither), a dark line
where a part passes in front of another, our outline round the figure. The way Dead Cells made pixel characters
from 3D models.

    python3 tools/sprites/blender_sprite.py sample   -> out/golem_blender_sample.png (the old render beside it)

Needs Blender (`blender` on the PATH, run in the background).
"""
import json
import os
import subprocess
import tempfile
import numpy as np
from PIL import Image
from r3d import rot_y, YAW, SA, CA
from kit import OUTLINE

HERE = os.path.dirname(os.path.abspath(__file__))
# model space → view space: turned to the viewer by YAW, tipped by PITCH; x right, y up the screen, z towards the eye
P = np.array([[1, 0, 0], [0, CA, -SA], [0, SA, CA]])
V = P @ rot_y(YAW)
import r3d
LIGHT = rot_y(YAW) @ r3d.LIGHT          # the game renderer's light, in the turned model's frame
LIGHT = P @ LIGHT                       # and tipped like the view

BLENDER_SCRIPT = r'''
import bpy, bmesh, json, sys, math
from mathutils import Matrix, Vector
args = sys.argv[sys.argv.index("--") + 1:]
data = json.load(open(args[0]))
out = args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 1
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 0
sc.cycles.filter_width = 0.01
sc.render.film_transparent = True
sc.render.resolution_x, sc.render.resolution_y = data["w"], data["h"]
sc.render.resolution_percentage = 100
try:
    sc.view_settings.view_transform = "Raw"
except TypeError:
    sc.view_settings.view_transform = "Standard"
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_depth = "8"
sc.render.image_settings.color_mode = "RGBA"
cam = bpy.data.cameras.new("cam")
cam.type = "ORTHO"
cam.sensor_fit = "HORIZONTAL"
cam.ortho_scale = data["w"]
co = bpy.data.objects.new("cam", cam)
co.location = (data["w"] / 2 - data["ox"], -(data["h"] / 2 - data["oy"]), 500.0)
sc.collection.objects.link(co)
sc.camera = co

def add(name, bm, smooth):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    return ob

objs = []
for i, op in enumerate(data["ops"]):
    bm = bmesh.new()
    k = op["k"]
    if k == "ell":
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
        R = Matrix([op["R"][0] + [0], op["R"][1] + [0], op["R"][2] + [0], [0, 0, 0, 1]])
        M = Matrix.Translation(op["c"]) @ R @ Matrix.Diagonal(op["r"] + [1])
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        smooth = True
    elif k == "box":
        bmesh.ops.create_cube(bm, size=1.0)
        R = Matrix([op["R"][0] + [0], op["R"][1] + [0], op["R"][2] + [0], [0, 0, 0, 1]])
        M = Matrix.Translation(op["c"]) @ R @ Matrix.Diagonal(op["s"] + [1])
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        smooth = False
    elif k == "cyl":
        a, b = Vector(op["a"]), Vector(op["b"])
        L = (b - a).length
        if L < 1e-6:
            continue
        bmesh.ops.create_cone(bm, cap_ends=True, segments=max(12, op["seg"]), radius1=op["r0"], radius2=op["r1"], depth=L)
        q = Vector((0, 0, 1)).rotation_difference((b - a).normalized())
        M = Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
        smooth = True
    elif k in ("poly", "solid"):
        vs = [bm.verts.new(v) for v in op["v"]]
        for f in op["f"]:
            try:
                bm.faces.new([vs[j] for j in f])
            except ValueError:
                pass
        smooth = False
    else:
        continue
    ob = add("p%d" % i, bm, smooth)
    ob["mid"], ob["oid"] = op["m"], i + 1
    objs.append(ob)

def emission(name, build):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(e.outputs[0], o.inputs[0])
    build(nt, e)
    return mat

def normal_pass(nt, e):
    g = nt.nodes.new("ShaderNodeNewGeometry")
    flip = nt.nodes.new("ShaderNodeVectorMath"); flip.operation = "SCALE"
    s = nt.nodes.new("ShaderNodeMath"); s.operation = "MULTIPLY_ADD"
    nt.links.new(g.outputs["Backfacing"], s.inputs[0]); s.inputs[1].default_value = -2.0; s.inputs[2].default_value = 1.0
    nt.links.new(g.outputs["Normal"], flip.inputs[0]); nt.links.new(s.outputs[0], flip.inputs["Scale"])
    m = nt.nodes.new("ShaderNodeVectorMath"); m.operation = "MULTIPLY_ADD"
    nt.links.new(flip.outputs[0], m.inputs[0]); m.inputs[1].default_value = (0.5, 0.5, 0.5); m.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(m.outputs[0], e.inputs["Color"])

def depth_pass(nt, e):
    g = nt.nodes.new("ShaderNodeNewGeometry")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(g.outputs["Position"], sp.inputs[0])
    m = nt.nodes.new("ShaderNodeMath"); m.operation = "MULTIPLY_ADD"
    nt.links.new(sp.outputs["Z"], m.inputs[0]); m.inputs[1].default_value = 1 / 100.0; m.inputs[2].default_value = 0.5
    c = nt.nodes.new("ShaderNodeCombineXYZ")
    for j in range(3):
        nt.links.new(m.outputs[0], c.inputs[j])
    nt.links.new(c.outputs[0], e.inputs["Color"])

def render(path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

for ob in objs:                                            # 1: which material and which part
    mid, oid = ob["mid"], ob["oid"]
    col = ((mid + 1) / 255.0, (oid // 255) / 255.0, (oid % 255) / 255.0, 1.0)
    mat = emission("id%d" % oid, lambda nt, e, col=col: e.inputs["Color"].__setattr__("default_value", col))
    ob.data.materials.clear(); ob.data.materials.append(mat)
render(out + "/id.png")
nm = emission("normal", normal_pass)
for ob in objs:
    ob.data.materials.clear(); ob.data.materials.append(nm)
render(out + "/normal.png")
dm = emission("depth", depth_pass)
for ob in objs:
    ob.data.materials.clear(); ob.data.materials.append(dm)
render(out + "/depth.png")
'''


def export(model, w, h, ox, oy):
    """The model's parts in view space, as the Blender script reads them; and its materials."""
    mats, ops = [], []

    def mid(m):
        for i, x in enumerate(mats):
            if x is m:
                return i
        mats.append(m)
        return len(mats) - 1

    for op in model.ops:
        k = op[0]
        m_ = op[3] if k in ("box", "ell", "limb", "solid") else (op[5] if k == "cyl" else op[2])
        big = (k == "ell" and op[2].max() > 1.6) or (k == "cyl" and max(op[3], op[4]) > 1.6) or (k == "box" and op[2].max() > 3)
        if m_.emissive is not None and big:
            continue                    # the furnace's insides: the old renderer kept them under the shell; small glows stay
        if k == "ell":
            if getattr(op[3], "smoke", False):
                continue
            ops.append(dict(k="ell", c=(V @ op[1]).tolist(), r=op[2].tolist(), R=(V @ op[4]).tolist(), m=mid(op[3])))
        elif k == "box":
            ops.append(dict(k="box", c=(V @ op[1]).tolist(), s=op[2].tolist(), R=(V @ op[4]).tolist(), m=mid(op[3])))
        elif k == "cyl":
            ops.append(dict(k="cyl", a=(V @ op[1]).tolist(), b=(V @ op[2]).tolist(), r0=float(op[3]), r1=float(op[4]),
                            seg=int(op[6]), m=mid(op[5])))
        elif k == "limb":
            r = max(0.55, op[2] * 0.5)
            for a, b in zip(op[1][:-1], op[1][1:]):
                ops.append(dict(k="cyl", a=(V @ a).tolist(), b=(V @ b).tolist(), r0=r, r1=r, seg=8, m=mid(op[3]),
                                band=int(op[4])))
        elif k == "poly":
            ops.append(dict(k="poly", v=[(V @ p).tolist() for p in op[1]], f=[list(range(len(op[1])))], m=mid(op[2])))
        elif k == "solid":
            ops.append(dict(k="solid", v=[(V @ p).tolist() for p in op[1]], f=[list(f) for f in op[2]], m=mid(op[3])))
    return dict(w=w, h=h, ox=ox, oy=oy, ops=ops), mats


def passes(model, w, h, ox, oy, k=1):
    """Blender's three pictures of the model at k times the sprite's size: (material, part), surface normal,
    nearness; and each part's fixed tone, if it has one (a limb)."""
    data, mats = export(model.scaled(k), w * k, h * k, ox * k, oy * k)
    bands = {i + 1: op.get("band") for i, op in enumerate(data["ops"])}
    with tempfile.TemporaryDirectory() as tmp:
        jp, sp = os.path.join(tmp, "model.json"), os.path.join(tmp, "make.py")
        json.dump(data, open(jp, "w"))
        open(sp, "w").write(BLENDER_SCRIPT)
        subprocess.run(["blender", "-b", "--factory-startup", "-noaudio", "--python", sp, "--", jp, tmp],
                       check=True, capture_output=True)
        load = lambda n: np.array(Image.open(os.path.join(tmp, n)).convert("RGBA"), dtype=np.float64) / 255.0
        idp, nrm, dep = load("id.png"), load("normal.png"), load("depth.png")
    m = np.rint(idp[..., 0] * 255).astype(int) - 1
    alpha = (idp[..., 3] > 0.5) & (m >= 0) & (m < len(mats))     # a pixel that reads as no material is left empty
    part = np.rint(idp[..., 1] * 255).astype(int) * 255 + np.rint(idp[..., 2] * 255).astype(int)
    n = nrm[..., :3] * 2 - 1
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    z = (dep[..., 0] - 0.5) * 100.0
    return alpha, m, part, n, z, mats, bands


def sprite(model, w, h, ox, oy, steps=(0.7, 0.36, 0.02), k=3):
    """The sprite from Blender's pictures, rendered k times larger: every pixel's material and tone step worked out
    there, then each k×k block takes the one most of it shows (small parts merge into clean patches instead of
    speckle); a line where a part is in front of another; the outline round the whole."""
    alpha, m, part, n, z, mats, bands = passes(model, w, h, ox, oy, k)
    ndl = n @ LIGHT
    lv = np.clip(((r3d.AMB + r3d.DIF * np.clip(ndl, 0, 1)) * 4.999).astype(int), 1, 4)   # the game renderer's steps
    for oid, band in bands.items():                       # limbs: their own fixed tone
        if band is not None:
            lv[part == oid] = int(np.clip(band + 1, 1, 4))
    emis = np.array([mm.emissive is not None for mm in mats] + [False])
    lv = np.where(alpha & emis[np.clip(m, 0, len(mats))], np.where(n[..., 2] > 0.55, 4, 3), lv)
    key = np.where(alpha, (m + 1) * 8 + lv, 0)              # material and step together
    H, W = h, w
    out_key = np.zeros((H, W), int)
    out_part = np.zeros((H, W), int)
    out_z = np.full((H, W), -1e9)
    for y in range(H):
        for x in range(W):
            blk = key[y * k:(y + 1) * k, x * k:(x + 1) * k].ravel()
            cov = blk[blk > 0]
            if len(cov) * 2 < len(blk):                      # less than half covered: empty
                continue
            vals, cnt = np.unique(cov, return_counts=True)
            out_key[y, x] = vals[cnt.argmax()]
            bp = part[y * k:(y + 1) * k, x * k:(x + 1) * k].ravel()[blk > 0]
            pv, pc = np.unique(bp, return_counts=True)
            out_part[y, x] = pv[pc.argmax()]
            out_z[y, x] = z[y * k:(y + 1) * k, x * k:(x + 1) * k].ravel()[blk > 0].mean()
    a = out_key > 0
    mm_i, lv_i = out_key // 8 - 1, out_key % 8
    rgb = np.zeros((H, W, 3))
    for y, x in zip(*np.nonzero(a)):
        rgb[y, x] = mats[mm_i[y, x]].ramp[lv_i[y, x]]
    # a part behind another along its edge: the far side darkens (an inner line in its own colour)
    for y, x in zip(*np.nonzero(a)):
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and a[yy, xx] and out_part[yy, xx] != out_part[y, x] \
                    and out_z[y, x] < out_z[yy, xx] - 1.2 * k:
                mm = mats[mm_i[y, x]]
                if mm.emissive is None:
                    rgb[y, x] = mm.ramp[max(0, lv_i[y, x] - 2)]
                break
    p = np.pad(a, 1)
    ring = ~a & (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:])
    res = np.zeros((H, W, 4), np.uint8)
    res[..., :3] = np.clip(rgb, 0, 255)
    res[ring, :3] = OUTLINE
    res[..., 3] = (a | ring) * 255
    return res


def sample():
    import golems_h as GH
    import battle as BT
    from paths import out
    S = GH.BY_NAME["Мудрец"]
    k = BT.GK[4]
    cw, ch, cx, cy = S.get("canvas", (90, 84, 38, 74))
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    G, _ = GH.creature_parts(S, S["poses"]["idle"])
    rgba = sprite(G.model().scaled(k), w, h, ox, oy)
    ys, xs = np.nonzero(rgba[..., 3])
    new = Image.fromarray(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA")
    nox, noy = ox - xs.min(), oy - ys.min()
    root = os.path.join(HERE, "..", "..", "game", "assets")
    old = Image.open(os.path.join(root, "sprites", "Мудрец_idle.png")).convert("RGBA")
    ground = Image.open(os.path.join(root, "ground.png")).convert("RGBA")
    W, H = 120, 80
    tile = ground.crop((300, 300, 300 + W, 300 + H))
    row = Image.new("RGBA", (W * 2, H))
    for i, (im, px, py) in enumerate(((old, 15, 50), (new, nox, noy))):
        t = tile.copy()
        t.alpha_composite(im, (60 - px, 70 - py))
        row.paste(t, (i * W, 0))
    big = row.resize((row.width * 6, row.height * 6), Image.NEAREST)
    small = row.resize((row.width * 2, row.height * 2), Image.NEAREST)
    sheet = Image.new("RGBA", (big.width, big.height + small.height + 8), (20, 16, 24, 255))
    sheet.paste(big, (0, 0))
    sheet.paste(small, (0, big.height + 8))
    sheet.save(out("golem_blender_sample.png"))
    new.save(out("golem_blender_sage.png"))
    return out("golem_blender_sample.png")


if __name__ == "__main__":
    import sys
    if (sys.argv[1:] or ["sample"])[0] == "sample":
        print(sample())
