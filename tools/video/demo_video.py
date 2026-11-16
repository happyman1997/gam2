"""The demo's video: battles one after another at 1920×1080, 60 fps, the camera on the clash (the game draws the frames,
`game --video`), and a soundtrack mixed from the same sounds the game plays, at the same moments.

    python3 tools/video/demo_video.py                         # battles 184 and 142 -> docs/images/demo_battle.mp4
    python3 tools/video/demo_video.py --seeds 7 12 --crf 16 --out /tmp/x.mp4

Needs ffmpeg and numpy; builds the game first (cargo, release).
"""
import argparse
import json
import os
import random
import subprocess
import tempfile

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SFX = os.path.join(ROOT, "game", "assets", "sfx")
GAME = os.path.join(ROOT, "target", "release", "game")
SR = 44100


def load(path, cache={}):
    if path not in cache:
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        cache[path] = np.frombuffer(raw, np.float32)
    return cache[path]


def mix(doc, seed=5):
    """The soundtrack as the game would play it: the swarm's chirring while it lives; the cues of a tick at most four
    and one of a kind, a random variant each, a little higher or lower, panned by the place on the field."""
    man = json.load(open(os.path.join(SFX, "sfx.json")))
    out = np.zeros((int(SR * (doc["seconds"] + 2.0)), 2), np.float32)
    bed = load(os.path.join(SFX, "swarm_bed_0.ogg"))
    for a, b in doc["bed"]:
        s0, s1 = int(a * SR), int(b * SR)
        n = s1 - s0
        loop = np.tile(bed, n // len(bed) + 1)[:n]
        env = np.minimum(1.0, np.minimum(np.arange(n) / (0.5 * SR), (n - np.arange(n)) / (0.6 * SR)))
        out[s0:s1] += (loop * env * 0.7)[:, None]
    rnd = random.Random(seed)
    ticks = {}
    for c in doc["cues"]:
        lst = ticks.setdefault((c["battle"], c["frame"]), [])
        if c["name"] not in [x["name"] for x in lst] and len(lst) < 4:
            lst.append(c)
    for lst in ticks.values():
        for c in lst:
            x = load(os.path.join(SFX, os.path.basename(rnd.choice(man[c["name"]]))))
            rate = 0.94 + 0.12 * rnd.random()
            y = np.interp(np.arange(0, len(x) - 1, rate), np.arange(len(x)), x) * 10 ** (c["gain"] / 20)
            pan = max(-1.0, min(1.0, c["x"] / 960 * 2 - 1)) * 0.6
            s0 = int(c["t"] * SR)
            n = min(len(y), len(out) - s0)
            if n > 0:
                out[s0:s0 + n, 0] += y[:n] * np.sqrt((1 - pan) / 2) * 1.41
                out[s0:s0 + n, 1] += y[:n] * np.sqrt((1 + pan) / 2) * 1.41
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[184, 142])
    ap.add_argument("--crf", type=int, default=23)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "images", "demo_battle.mp4"))
    args = ap.parse_args()
    subprocess.run(["cargo", "build", "--release", "-p", "game"], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory() as tmp:
        sound, silent, raw, wav = (os.path.join(tmp, n) for n in ("sound.json", "v.mp4", "mix.f32", "mix.wav"))
        game = subprocess.Popen([GAME, "--video", sound] + [str(s) for s in args.seeds], stdout=subprocess.PIPE)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "60",
                        "-i", "-", "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-crf", str(args.crf),
                        "-pix_fmt", "yuv420p", silent], stdin=game.stdout, check=True)
        if game.wait() != 0:
            raise SystemExit("game --video failed")
        mix(json.load(open(sound))).tofile(raw)
        # a limiter, not a gain down: a pile of blows at one moment must not make the whole battle quiet
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", raw,
                        "-af", "alimiter=limit=0.89:attack=3:release=60:level=false", wav], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.out], check=True)
    print(args.out, round(os.path.getsize(args.out) / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
