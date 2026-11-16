"""The game's sounds, all CC0 (free for commercial use, credit not required, may be shared): Kenney's packs, as
Kenney himself uploaded them to OpenGameArt, and CC0 sound effects by other authors on OpenGameArt — each page's
licence checked to be CC0 before it is listed here (CC-BY, CC-BY-SA, GPL and OGA-BY-only pages are not used).

Downloads the sources into tools/audio/cache, takes the files each sound of the game is made from (cutting a file
of several sounds at its silences, or a stretch out of a long recording), trims the silence before them, brings them
to the loudness the sound should have (A-weighted, the loudest 150 ms; never over −1 dBFS), writes mono OGG Vorbis 44.1 kHz into game/assets/sfx
with sfx.json (the game's sound → its variants) and SOURCES.md (each file: what for, whose, which page, licence).

    python3 tools/audio/sfx_build.py
"""
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
DST = os.path.join(HERE, "..", "..", "game", "assets", "sfx")
OGA = "https://opengameart.org/sites/default/files/"
PAGE = "https://opengameart.org/content/"
SRC = {   # source: (author, page, [archive or file urls])
    "rpg": ("Kenney", PAGE + "50-rpg-sound-effects", [OGA + "RPGsounds_Kenney.zip"]),
    "scifi": ("Kenney", PAGE + "sci-fi-sounds", [OGA + "sci-fi_sounds.zip"]),
    "interface": ("Kenney", PAGE + "interface-sounds", [OGA + "kenney_interfaceSounds.zip"]),
    "creature": ("rubberduck", PAGE + "80-cc0-creature-sfx", [OGA + "80-CC0-creature-SFX_0.zip"]),
    "creature2": ("rubberduck", PAGE + "80-cc0-creture-sfx-2", [OGA + "80-CC0-creature-sfx-2.zip"]),
    "bfh": ("rubberduck", PAGE + "75-cc0-breaking-falling-hit-sfx", [OGA + "sfx_breaking_and_falling.zip"]),
    "crunchybite": ("fvcalderan", PAGE + "crunchy-bite", [OGA + "crunchybite.ogg"]),
    "crunches": ("StarNinjas", PAGE + "7-eating-crunches", [OGA + "crunch_-_tito.zip"]),
    "squish": ("EZduzziteh", PAGE + "squish-sounds-effects",
               [OGA + f for f in ("squish_01_0.mp3", "squish_02.mp3", "squish_03.mp3", "squish_04.mp3", "squish_05.mp3",
                                  "squish_06.mp3", "squishsplat_impact.mp3")]),
    "wetsquish": ("qubodup", PAGE + "8-wet-squish-slurp-impacts", [OGA + "im.mp3"]),
    "breakcrunch": ("qubodup", PAGE + "5-break-crunch-impacts", [OGA + "imp_3.mp3"]),
    "metal": ("BMacZero", PAGE + "metal-impact-sounds", [OGA + f for f in ("clink1_0.wav", "clink2.wav", "clink3.wav",
                                                                          "thud2.wav", "thud3.wav")]),
    "spark": ("BMacZero", PAGE + "electricity-sound-effects-0", [OGA + "spark.wav"]),
    "elec": ("faxcorp", PAGE + "electricity-game-sound-pack",
             [OGA + f for f in ("hit.wav", "crackleelectricityloop.wav", "snaploop.wav", "death_1.wav")]),
    "sfx100v2": ("rubberduck", PAGE + "100-cc0-sfx-2", [OGA + "sfx_100_v2.zip"]),
    "bangs": ("rubberduck", PAGE + "25-cc0-bang-firework-sfx", [OGA + "25-CC0-bang-sfx.zip"]),
    "cannon": ("Thimras", PAGE + "cannon-fire", [OGA + "cannon_fire.ogg"]),
    "gunshots": ("kurt", PAGE + "gunshots", [OGA + "22%20Magnum.wav"]),
    "explosions": ("EZduzziteh", PAGE + "explosions-4", [OGA + "explosion3.ogg"]),
    "fanfare": ("Zane Little Music", PAGE + "hyper-ultra-fanfare", [OGA + "sboe.mp3"]),
    "gameover": ("KLY", PAGE + "kl-peach-game-over-iii", [OGA + "KL%20Peach%20Game%20Over%20III.mp3"]),
    "mechexp": ("Spring Spring", PAGE + "mechanical-explosion", [OGA + "mechanical_explosion.wav"]),
    "steam": ("bart", PAGE + "steam-release-sounds", [OGA + "steam_hisses.zip"]),
    "cicada": ("syncopika", PAGE + "cicada-sounds", [OGA + "082526-cicadasounds.ogg"]),
}


def k(src, files, **opt):
    return [(src, f, opt) for f in files]


# the game's sound: (what it is for, [(source, file, options)], loudness dB(A) — how loud it feels: the loudest 150 ms,
# A-weighted; every variant brought to it, so they do not jump about). Options: "split": n — the n-th piece of a file of
# several sounds; "cut": (start, length) — a stretch of a long file; "rate": tone (0.8 = lower and slower, heavier);
# "lowpass": Hz above which the shrill top is cut; "len": seconds kept, the end faded out; "layers": sounds mixed with
# it ({src, rel, db against it, len, af — their own filters}); "punch": squeezed and driven, so a blow sounds fat
def L(src, rel, db, ln, af):
    return dict(src=src, rel=rel, db=db, len=ln, af=af)


CRACK = L("bangs", "shot_02.ogg", -4, 0.15, "highpass=f=1500")              # the snap at the very start of a discharge
THUNDER = L("sfx100v2", "sfx100v2_thunder_01.ogg", -4, 0.8, "lowpass=f=500,bass=g=4:f=80")   # the clap under it
BOOM = L("cannon", "cannon_fire.ogg", -2, 0.9, "lowpass=f=400")              # the barrel's low boom under a shot
SNAP = L("bangs", "bang_05.ogg", -6, 0.25, "highpass=f=800")                 # the first hard edge of a blast
SUB = L("scifi", "Audio/lowFrequency_explosion_000.ogg", -4, 1.2, "lowpass=f=200")   # the ground shaking under it
PUNCH = "acompressor=threshold=-20dB:ratio=5:attack=1:release=90:makeup=8dB,bass=g=3:f=90,asoftclip=type=tanh"

SOUNDS = {
    "bite": ("укус особи: хитиновые жвалы", k("crunchybite", ["crunchybite.ogg"]) +
             k("crunches", [f"crunch.{i}.ogg" for i in (1, 2, 3, 5)]) + k("creature", ["eat_01.ogg"]), -30),
    "hit_metal": ("укус приходится по голему: звон металла", k("metal", ["clink1_0.wav", "clink2.wav", "clink3.wav"], lowpass=5000) +
                  k("bfh", [f"bfh1_metal_hit_0{i}.ogg" for i in (2, 4)], lowpass=5000) +
                  k("scifi", ["Audio/impactMetal_000.ogg"], lowpass=5000), -31),
    "hit_flesh": ("голем бьёт особь: хруст", [("breakcrunch", "imp_3.mp3", {"split": i}) for i in range(5)] +
                  k("rpg", ["OGG/chop.ogg"]), -27),
    # a discharge: a snap, the crackle of a real spark, the low clap of thunder; squeezed and driven so it bites
    "zap": ("разряд Мудреца и Изобретателя: щелчок, треск искры, раскат", [
        ("elec", "hit.wav", {"len": 0.7, "layers": [CRACK, THUNDER], "punch": True}),
        ("elec", "crackleelectricityloop.wav", {"cut": (0.0, 0.4), "layers": [CRACK, THUNDER], "punch": True}),
        ("elec", "snaploop.wav", {"cut": (0.6, 0.45), "layers": [CRACK, THUNDER], "punch": True}),
        ("elec", "death_1.wav", {"len": 0.6, "layers": [CRACK, THUNDER], "punch": True}),
        ("spark", "spark.wav", {"layers": [CRACK, THUNDER], "punch": True})], -25),
    # the Mortar fires: a crack of the charge and the barrel's boom; the shell lands: a blast with a hard edge and
    # the ground shaking under it
    "shot": ("выстрел Мортиры: хлопок заряда и низкий бас ствола",
             k("bangs", ["cannon_01.ogg", "cannon_04.ogg", "cannon_05.ogg"], len=0.9, layers=[BOOM], punch=True) +
             k("gunshots", ["22 Magnum.wav"], len=0.8, layers=[BOOM], punch=True), -25),
    "blast": ("разрыв снаряда Мортиры", k("scifi", [f"Audio/explosionCrunch_00{i}.ogg" for i in (0, 1, 3)],
                                        len=1.4, layers=[SNAP, SUB], punch=True) +
              k("explosions", ["explosion3.ogg"], len=1.4, layers=[SNAP, SUB], punch=True), -22),
    "squish": ("гибель особи: мокрый шлепок", k("squish", ["squish_01_0.mp3", "squish_02.mp3", "squish_03.mp3",
                                                         "squish_04.mp3", "squish_06.mp3"]) +
               [("wetsquish", "im.mp3", {"split": i}) for i in range(5)], -27),
    "death_rattle": ("хрип гибнущей особи: низкий, без писка", k("creature", ["hurt_04.ogg", "hurt_05.ogg", "grunt_02.ogg"]) +
                     k("creature2", ["grunt_06.ogg", "grunt_08.ogg", "monster_09.ogg", "monster_12.ogg"]) +
                     [("creature2", "die_03.ogg", {"lowpass": 3500})], -31),
    "break": ("голем сломан: механический взрыв, падает железо", k("mechexp", ["mechanical_explosion.wav"]) +
              k("bfh", [f"bfh1_metal_falling_0{i}.ogg" for i in (1, 2)], lowpass=5000), -23),
    "heal": ("ремонт Механика: глухой выдох пара", k("steam", [f"steam hisses - Marker #{i}.wav" for i in (1, 2, 3)],
                                                    rate=0.8, lowpass=1600, len=1.0), -27),
    "miss": ("промах: свист", k("rpg", [f"OGG/drawKnife{i}.ogg" for i in (1, 2, 3)], lowpass=4000), -32),
    "step": ("тяжёлый шаг голема: глухой удар металла", k("metal", ["thud2.wav", "thud3.wav"], rate=0.8, lowpass=1800, len=0.35) +
             k("bfh", ["bfh1_hit_02.ogg", "bfh1_hit_07.ogg"], lowpass=2000, len=0.35) +
             k("rpg", ["OGG/footstep02.ogg", "OGG/footstep04.ogg"], rate=0.65, lowpass=1500, len=0.35), -32),
    "swarm_bed": ("стрекот роя фоном, пока рой жив (петля)", [("cicada", "082526-cicadasounds.ogg", {"cut": (2.0, 6.0)})], -47),
    "click": ("кнопка", k("interface", [f"Audio/click_00{i}.ogg" for i in (1, 2, 3)]), -36),
    "toggle": ("переключатель: пауза, скорость", k("interface", [f"Audio/switch_00{i}.ogg" for i in (2, 3, 4)], lowpass=4000), -33),
    "win": ("победа: напористая минорная фанфара", k("fanfare", ["sboe.mp3"]), -20),
    "lose": ("поражение: короткая нисходящая тема", k("gameover", ["KL Peach Game Over III.mp3"]), -21),
}


def fetch():
    for name, (_a, _p, urls) in SRC.items():
        d = os.path.join(CACHE, name)
        if os.path.isdir(d):
            continue
        os.makedirs(d)
        for u in urls:
            f = os.path.join(d, urllib.parse.unquote(u.split("/")[-1]))
            urllib.request.urlretrieve(u, f)
            if f.endswith(".zip"):
                with zipfile.ZipFile(f) as zf:
                    zf.extractall(d)
        print("fetched", name)


def find(src, rel):
    """The file in the unpacked source (archives keep their own top folders)."""
    for dirpath, _dirs, files in os.walk(os.path.join(CACHE, src)):
        if os.path.basename(rel) in files:
            cand = os.path.join(dirpath, os.path.basename(rel))
            if cand.replace("\\", "/").endswith(rel):
                return cand
    raise FileNotFoundError(f"{src}: {rel}")


def peak_db(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", out)
    return float(m.group(1)) if m else 0.0


def loudness(path):
    """How loud a sound feels: dB(A) of its loudest 150 ms (A-weighted, so a deep boom is not taken for a loud one)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-ac", "1", "-ar", "44100", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    f = np.fft.rfftfreq(len(x), 1 / 44100) + 1e-9
    f2 = f ** 2
    a = (12194 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194 ** 2))
    y = np.fft.irfft(np.fft.rfft(x) * a, len(x))
    w = min(len(y), int(0.15 * 44100))
    return 10 * np.log10(np.convolve(y ** 2, np.ones(w) / w, "valid").max() + 1e-12)


def segments(path):
    """A file of several sounds, cut at its silences: [(start, end)]."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "silencedetect=noise=-40dB:d=0.12", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [0.0] + [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout.strip())
    return [(a, b) for a, b in zip(ends, starts + [dur]) if b - a > 0.05]


def convert(src, dst, gain, opt):
    tmp = dst + ".tmp.wav"
    cut = []
    if "split" in opt:
        a, b = segments(src)[opt["split"]]
        cut = ["-ss", f"{max(0.0, a - 0.01):.3f}", "-to", f"{b + 0.05:.3f}"]
    elif "cut" in opt:
        cut = ["-ss", str(opt["cut"][0]), "-t", str(opt["cut"][1])]
    if "cut" in opt:                                    # a stretch of a long file: faded in and out so it does not click
        n = opt["cut"][1]
        fi, fo = (0.3, 0.4) if n > 2 else (0.005, n * 0.35)
        af = f"afade=t=in:d={fi},afade=t=out:st={n - fo:.3f}:d={fo:.3f}"
    else:
        af = "silenceremove=start_periods=1:start_threshold=-50dB"
    if "rate" in opt:                                   # lower (or higher) and slower, as a heavier body would sound
        af += f",asetrate={int(44100 * opt['rate'])},aresample=44100"
    if "lowpass" in opt:                                # the shrill top cut off
        af += f",lowpass=f={opt['lowpass']}"
    if "len" in opt:                                    # only the blow itself, the tail faded out
        af += f",atrim=0:{opt['len']},afade=t=out:st={opt['len'] * 0.5:.3f}:d={opt['len'] * 0.5:.3f}"
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + cut + ["-i", src, "-ac", "1", "-ar", "44100", "-af", af, tmp], check=True)
    if opt.get("layers"):
        ins, chain = ["-i", tmp], [f"[0]volume={-1.0 - peak_db(tmp):.2f}dB[m]"]
        made = []
        for j, ly in enumerate(opt["layers"]):
            f = f"{dst}.layer{j}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", find(ly["src"], ly["rel"]), "-ac", "1", "-ar", "44100", "-af",
                            f"silenceremove=start_periods=1:start_threshold=-50dB,{ly['af']},atrim=0:{ly['len']},"
                            f"afade=t=out:st={ly['len'] * 0.4:.3f}:d={ly['len'] * 0.6:.3f}", f], check=True)
            ins += ["-i", f]
            chain.append(f"[{j + 1}]volume={-1.0 - peak_db(f) + ly['db']:.2f}dB[l{j}]")
            made.append(f)
        n = len(made) + 1
        chain.append("[m]" + "".join(f"[l{j}]" for j in range(len(made))) + f"amix=inputs={n}:normalize=0:duration=longest")
        both = dst + ".both.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(chain), both], check=True)
        os.replace(both, tmp)
        for f in made:
            os.remove(f)
    if opt.get("punch"):                                # squeezed and driven: the blow sounds fat, not thin
        fat = dst + ".fat.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={-6.0 - peak_db(tmp):.2f}dB,{PUNCH}", fat],
                       check=True)
        os.replace(fat, tmp)
    g = min(gain - loudness(tmp), -1.0 - peak_db(tmp))   # as loud as the sound should feel, never over −1 dBFS
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={g:.2f}dB", "-c:a", "libvorbis", "-q:a", "4", dst],
                   check=True)
    os.remove(tmp)


def main():
    fetch()
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    manifest, rows, authors = {}, [], {}
    for name, (what, files, gain) in SOUNDS.items():
        outs = []
        for i, item in enumerate(files):
            src, rel, opt = item[0], item[1], (item[2] if len(item) > 2 else {})
            out = f"{name}_{i}.ogg"
            convert(find(src, rel), os.path.join(DST, out), gain, opt)
            outs.append(f"sfx/{out}")
            author, page, _u = SRC[src]
            authors.setdefault(author, set()).add(page)
            part = f" (кусок {opt['split'] + 1})" if "split" in opt else (f" ({opt['cut'][0]}–{opt['cut'][0] + opt['cut'][1]} с)" if "cut" in opt else "")
            if "rate" in opt:
                part += f", тон ×{opt['rate']}"
            if "lowpass" in opt:
                part += f", срез выше {opt['lowpass']} Гц"
            if "len" in opt:
                part += f", первые {opt['len']} с"
            for ly in opt.get("layers", []):
                la, lp, _lu = SRC[ly["src"]]
                authors.setdefault(la, set()).add(lp)
                part += f"; с ним {la}: `{ly['rel']}` (первые {ly['len']} с, {ly['af'].split('=')[0]})"
            if opt.get("punch"):
                part += "; сжато для плотности"
            rows.append(f"| `{out}` | {what} | {author}: `{rel}`{part} | [{page.split('/')[-1]}]({page}) |")
        manifest[name] = outs
    json.dump(manifest, open(os.path.join(DST, "sfx.json"), "w"), ensure_ascii=False, indent=1)
    shutil.copy(find("scifi", "License.txt"), os.path.join(DST, "LICENSE-Kenney.txt"))
    with open(os.path.join(DST, "SOURCES.md"), "w") as f:
        f.write("# Откуда звуки\n\nВсе звуки — под CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/): можно в "
                "коммерческих проектах, указывать автора не обязательно, можно распространять. Источник — OpenGameArt; "
                "лицензия каждой страницы проверена (CC0), страницы с CC-BY, CC-BY-SA, GPL не используются. Наборы Kenney "
                "выложил сам Kenney (пользователь `kenney`). Обработка: моно 44,1 кГц, тишина в начале срезана, где указано — "
                "тон ниже, срез высоких, укорочено, подмешаны другие звуки, сжато для плотности, громкость выровнена по слышимой (A-взвешенной) громкости, пик не выше −1 dBFS, OGG Vorbis (`tools/audio/sfx_build.py`).\n\n## Авторы\n\n")
        for a, pages in sorted(authors.items()):
            f.write(f"- {a} — " + ", ".join(f"[{p.split('/')[-1]}]({p})" for p in sorted(pages)) + "\n")
        f.write("\n## Файлы\n\n| Файл | Для чего | Откуда | Страница |\n|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print(len(rows), "files ->", DST)


if __name__ == "__main__":
    main()
