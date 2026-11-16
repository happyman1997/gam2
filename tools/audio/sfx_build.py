"""The game's sounds, all CC0 (free for commercial use, credit not required, may be shared): Kenney's packs, as
Kenney himself uploaded them to OpenGameArt, and CC0 sound effects by other authors on OpenGameArt — each page's
licence checked to be CC0 before it is listed here (CC-BY, CC-BY-SA, GPL and OGA-BY-only pages are not used).

Downloads the sources into tools/audio/cache, takes the files each sound of the game is made from (cutting a file
of several sounds at its silences, or a stretch out of a long recording), trims the silence before them, brings them
to one loudness (peak at −1 dBFS, then the sound's own gain), writes mono OGG Vorbis 44.1 kHz into game/assets/sfx
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
    "digital": ("Kenney", PAGE + "63-digital-sound-effects-lasers-phasers-space-etc", [OGA + "Digital_SFX_Set.zip"]),
    "jingles": ("Kenney", PAGE + "85-short-music-jingles", [OGA + "jingleSounds_Kenney.zip"]),
    "creature": ("rubberduck", PAGE + "80-cc0-creature-sfx", [OGA + "80-CC0-creature-SFX_0.zip"]),
    "creature2": ("rubberduck", PAGE + "80-cc0-creture-sfx-2", [OGA + "80-CC0-creature-sfx-2.zip"]),
    "bfh": ("rubberduck", PAGE + "75-cc0-breaking-falling-hit-sfx", [OGA + "sfx_breaking_and_falling.zip"]),
    "insect": ("fvcalderan", PAGE + "insect-sounds", [OGA + "insect.zip"]),
    "crunchybite": ("fvcalderan", PAGE + "crunchy-bite", [OGA + "crunchybite.ogg"]),
    "crunches": ("StarNinjas", PAGE + "7-eating-crunches", [OGA + "crunch_-_tito.zip"]),
    "squish": ("EZduzziteh", PAGE + "squish-sounds-effects",
               [OGA + f for f in ("squish_01_0.mp3", "squish_02.mp3", "squish_03.mp3", "squish_04.mp3", "squish_05.mp3",
                                  "squish_06.mp3", "squishsplat_impact.mp3")]),
    "wetsquish": ("qubodup", PAGE + "8-wet-squish-slurp-impacts", [OGA + "im.mp3"]),
    "breakcrunch": ("qubodup", PAGE + "5-break-crunch-impacts", [OGA + "imp_3.mp3"]),
    "metal": ("BMacZero", PAGE + "metal-impact-sounds", [OGA + f for f in ("clink1_0.wav", "clink2.wav", "clink3.wav")]),
    "spark": ("BMacZero", PAGE + "electricity-sound-effects-0", [OGA + "spark.wav"]),
    "chunky": ("Joth", PAGE + "chunky-explosion", [OGA + "Chunky%20Explosion.mp3"]),
    "mechexp": ("Spring Spring", PAGE + "mechanical-explosion", [OGA + "mechanical_explosion.wav"]),
    "steam": ("bart", PAGE + "steam-release-sounds", [OGA + "steam_hisses.zip"]),
    "metalsteps": ("Thimras", PAGE + "metal-footsteps-on-concrete", [OGA + "metal_steps.ogg"]),
    "cicada": ("syncopika", PAGE + "cicada-sounds", [OGA + "082526-cicadasounds.ogg"]),
}


def k(src, files):
    return [(src, f) for f in files]


SOUNDS = {   # the game's sound: (what it is for, [(source, file[, {"split": n} | {"cut": (start, length)}])], gain dB)
    "bite": ("укус особи: хитиновые жвалы", k("crunchybite", ["crunchybite.ogg"]) +
             k("crunches", [f"crunch.{i}.ogg" for i in (1, 2, 3, 5)]) + k("creature", ["eat_01.ogg", "eat_03.ogg"]), -10),
    "hit_metal": ("укус приходится по голему: звон металла", k("metal", ["clink1_0.wav", "clink2.wav", "clink3.wav"]) +
                  k("bfh", [f"bfh1_metal_hit_0{i}.ogg" for i in (1, 2, 4)]) + k("scifi", ["Audio/impactMetal_000.ogg"]), -12),
    "hit_flesh": ("голем бьёт особь: хруст", [("breakcrunch", "imp_3.mp3", {"split": i}) for i in range(5)] +
                  k("rpg", ["OGG/chop.ogg"]), -8),
    "zap": ("разряд Мудреца и Изобретателя", k("spark", ["spark.wav"]) + k("digital", ["zap1.mp3", "zap2.mp3"]), -9),
    "blast": ("залп Мортиры", k("chunky", ["Chunky Explosion.mp3"]) +
              k("scifi", ["Audio/lowFrequency_explosion_000.ogg", "Audio/lowFrequency_explosion_001.ogg"]), -4),
    "squish": ("гибель особи: мокрый шлепок", k("squish", ["squish_01_0.mp3", "squish_02.mp3", "squish_03.mp3",
                                                         "squish_04.mp3", "squish_05.mp3", "squish_06.mp3"]) +
               [("wetsquish", "im.mp3", {"split": i}) for i in range(5)], -9),
    "bug_cry": ("писк гибнущей особи, стрекот роя", k("insect", [f"insect{i}.ogg" for i in range(6)]) +
                k("creature", ["bug_01.ogg", "bug_02.ogg", "bug_03.ogg", "bug_04.ogg"]) +
                k("creature2", ["bug_05.ogg", "bug_07.ogg", "bug_08.ogg", "bug_10.ogg"]), -16),
    "break": ("голем сломан: механический взрыв, падает железо", k("mechexp", ["mechanical_explosion.wav"]) +
              k("bfh", [f"bfh1_metal_falling_0{i}.ogg" for i in (1, 2, 5)]), -6),
    "heal": ("ремонт Механика: пар", k("steam", [f"steam hisses - Marker #{i}.wav" for i in (1, 2, 3)]), -16),
    "miss": ("промах: свист", k("rpg", [f"OGG/drawKnife{i}.ogg" for i in (1, 2, 3)]), -12),
    "step": ("тяжёлый шаг голема", [("metalsteps", "metal_steps.ogg", {"split": i}) for i in range(1, 7)], -14),
    "swarm_bed": ("стрекот роя фоном, пока рой жив (петля)", [("cicada", "082526-cicadasounds.ogg", {"cut": (2.0, 6.0)})], -24),
    "click": ("кнопка", k("interface", [f"Audio/click_00{i}.ogg" for i in (1, 2, 3)]), -8),
    "toggle": ("переключатель: пауза, скорость", k("interface", [f"Audio/switch_00{i}.ogg" for i in (1, 2, 3)]), -8),
    "win": ("победа", k("jingles", ["OGG/jingles_NES/jingles_NES12.ogg"]), -6),
    "lose": ("поражение", k("jingles", ["OGG/jingles_NES/jingles_NES11.ogg"]), -6),
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
    af = "silenceremove=start_periods=1:start_threshold=-50dB" if "cut" not in opt else "afade=t=in:d=0.3,afade=t=out:st=5.6:d=0.4"
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + cut + ["-i", src, "-ac", "1", "-ar", "44100", "-af", af, tmp], check=True)
    g = -1.0 - peak_db(tmp) + gain
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
            src, rel = item[0], item[1]
            opt = item[2] if len(item) > 2 else {}
            out = f"{name}_{i}.ogg"
            convert(find(src, rel), os.path.join(DST, out), gain, opt)
            outs.append(f"sfx/{out}")
            author, page, _u = SRC[src]
            authors.setdefault(author, set()).add(page)
            part = f" (кусок {opt['split'] + 1})" if "split" in opt else (f" ({opt['cut'][0]}–{opt['cut'][0] + opt['cut'][1]} с)" if "cut" in opt else "")
            rows.append(f"| `{out}` | {what} | {author}: `{rel}`{part} | [{page.split('/')[-1]}]({page}) |")
        manifest[name] = outs
    json.dump(manifest, open(os.path.join(DST, "sfx.json"), "w"), ensure_ascii=False, indent=1)
    shutil.copy(find("scifi", "License.txt"), os.path.join(DST, "LICENSE-Kenney.txt"))
    with open(os.path.join(DST, "SOURCES.md"), "w") as f:
        f.write("# Откуда звуки\n\nВсе звуки — под CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/): можно в "
                "коммерческих проектах, указывать автора не обязательно, можно распространять. Источник — OpenGameArt; "
                "лицензия каждой страницы проверена (CC0), страницы с CC-BY, CC-BY-SA, GPL не используются. Наборы Kenney "
                "выложил сам Kenney (пользователь `kenney`). Обработка: моно 44,1 кГц, тишина в начале срезана, пик −1 dBFS "
                "плюс поправка громкости звука, OGG Vorbis (`tools/audio/sfx_build.py`).\n\n## Авторы\n\n")
        for a, pages in sorted(authors.items()):
            f.write(f"- {a} — " + ", ".join(f"[{p.split('/')[-1]}]({p})" for p in sorted(pages)) + "\n")
        f.write("\n## Файлы\n\n| Файл | Для чего | Откуда | Страница |\n|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print(len(rows), "files ->", DST)


if __name__ == "__main__":
    main()
