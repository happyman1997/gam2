"""pixelfx effects in our scenes. pixelfx (https://github.com/patch-gg/pixelfx, MIT) draws pixel art effects in code
and renders them to sprite sheets with Aseprite-style JSON. Our own effects live in tools/fx/<category>/<name>.js and
are written to pixelfx's contract; this builds them (and any stock pixelfx effect) into tools/sprites/assets/fx/,
so the game and these scripts need only the sheets, never pixelfx itself.

    python3 tools/sprites/pxfx.py build foundry/forge-fire foundry/valve-steam impacts/hit-spark
        (needs a pixelfx checkout: $PIXELFX, or ../../../pixelfx next to the repo; and Node)

    frames, meta = pxfx.load("forge-fire")     # RGBA float frames (alpha 0..1), meta.pixelfx (fps, loop, pivot)
    pxfx.blend(sc, frames[i], x, y)            # alpha over the scene, x, y = where the effect's pivot goes
"""
import json
import os
import shutil
import subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "fx")
OUT = os.path.join(HERE, "assets", "fx")
PIXELFX = os.environ.get("PIXELFX", os.path.abspath(os.path.join(HERE, "..", "..", "..", "pixelfx")))
_CACHE = {}


def build(ids, opts=None):
    """Copy our effects into the pixelfx checkout, render each id to a sheet, keep the sheet and its JSON."""
    for cat in os.listdir(SRC):
        dst = os.path.join(PIXELFX, "src", "fx", cat)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(os.path.join(SRC, cat), dst)
    os.makedirs(OUT, exist_ok=True)
    for fid in ids:
        cmd = ["node", "tools/render.mjs", fid, "--sheet"]
        if opts and fid in opts:
            cmd += ["--opts", json.dumps(opts[fid])]
        subprocess.run(cmd, cwd=PIXELFX, check=True, stdout=subprocess.DEVNULL)
        name = fid.split("/")[-1]
        for ext in ("png", "json"):
            shutil.copy(os.path.join(PIXELFX, "records", fid, f"{name}.{ext}"), os.path.join(OUT, f"{name}.{ext}"))
        print("built", fid)


def load(name):
    """The frames of a built sheet as float RGBA arrays, and its meta (the pixelfx block: fps, loop, pivot...)."""
    if name in _CACHE:
        return _CACHE[name]
    from PIL import Image
    js = json.load(open(os.path.join(OUT, f"{name}.json")))
    im = np.asarray(Image.open(os.path.join(OUT, f"{name}.png")).convert("RGBA")).astype(np.float32)
    frames = []
    for f in js["frames"]:
        r = f["frame"]
        fr = im[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"]].copy()
        fr[..., 3] /= 255.0
        frames.append(fr)
    meta = js["meta"]["pixelfx"]
    _CACHE[name] = (frames, meta)
    return frames, meta


def blend(sc, fr, x, y, pivot=(0, 0), k=1.0):
    """Lay an RGBA frame over the scene with its pivot at (x, y)."""
    h, w = fr.shape[:2]
    x0, y0 = int(round(x - pivot[0])), int(round(y - pivot[1]))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(sc.w, x0 + w), min(sc.h, y0 + h)
    if xb <= xa or yb <= ya:
        return
    f = fr[ya - y0:yb - y0, xa - x0:xb - x0]
    a = f[..., 3:4] * k
    reg = sc.rgb[ya:yb, xa:xb]
    sc.rgb[ya:yb, xa:xb] = reg * (1 - a) + f[..., :3] * a


def save_gif(images, path, fps=24, durations=None):
    """Frames (PIL RGB images) to a GIF on one shared palette, so nothing flickers between frames."""
    from PIL import Image
    n = len(images)
    probe = Image.new("RGB", (images[0].width, images[0].height * min(n, 6)))
    for i, k in enumerate(np.linspace(0, n - 1, min(n, 6)).astype(int)):
        probe.paste(images[k], (0, i * images[0].height))
    pal = probe.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    frames = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in images]
    durs = durations or [int(round(1000 / fps))] * n
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=1, optimize=False)


def save_sheet(images, name, fps=24, loop=False, pivot=(0, 0), out_dir=None, columns=8):
    """RGBA frames (PIL) to a sprite sheet and Aseprite-style JSON, the same layout pixelfx writes, for the engine."""
    from PIL import Image
    out_dir = out_dir or os.path.join(HERE, "assets", "ui_anim")
    os.makedirs(out_dir, exist_ok=True)
    w, h = images[0].size
    cols = min(columns, len(images))
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * w, rows * h), (0, 0, 0, 0))
    frames = []
    for i, im in enumerate(images):
        x, y = (i % cols) * w, (i // cols) * h
        sheet.paste(im, (x, y))
        frames.append({"filename": f"{name} {i}", "frame": {"x": x, "y": y, "w": w, "h": h}, "rotated": False,
                       "trimmed": False, "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
                       "sourceSize": {"w": w, "h": h}, "duration": int(round(1000 / fps))})
    sheet.save(os.path.join(out_dir, f"{name}.png"))
    meta = {"app": "gam2 tools/sprites", "version": "1", "image": f"{name}.png", "format": "RGBA8888",
            "size": {"w": sheet.width, "h": sheet.height}, "scale": "1",
            "frameTags": [{"name": name, "from": 0, "to": len(images) - 1, "direction": "forward"}],
            "pixelfx": {"id": name, "fps": fps, "loop": loop, "frames": len(images), "frameSize": [w, h],
                        "pivot": list(pivot), "columns": cols}}
    json.dump({"frames": frames, "meta": meta}, open(os.path.join(out_dir, f"{name}.json"), "w"), indent=1)


def matte(draw, w, h):
    """Draw something twice, on black and on white, and recover its colour and alpha: the controls as transparent
    sprites for the engine, with their soft halos kept."""
    from kit import Scene
    from PIL import Image
    a, b = Scene(w, h), Scene(w, h)
    a.rgb[:] = 0.0
    b.rgb[:] = 255.0
    draw(a)
    draw(b)
    A, B = np.clip(a.rgb, 0, 255), np.clip(b.rgb, 0, 255)
    alpha = np.clip(1.0 - (B - A).mean(axis=2) / 255.0, 0, 1)
    col = np.where(alpha[..., None] > 1e-3, A / np.maximum(alpha[..., None], 1e-3), 0)
    rgba = np.dstack((np.clip(col, 0, 255), alpha * 255)).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["build"]:
        build(sys.argv[2:])
