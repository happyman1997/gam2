"""The demo's sounds, from Kenney's packs (CC0 — free for commercial use, credit not required, may be shared), as
Kenney himself uploaded them to OpenGameArt. Downloads the packs into tools/audio/cache, takes the files each
sound of the game is made from, trims the silence before them, brings them to one loudness (peak at −1 dBFS),
writes mono OGG Vorbis 44.1 kHz into game/assets/sfx with sfx.json (the game's sound → its variants) and
SOURCES.md (where each file came from).

    python3 tools/audio/kenney_sfx.py
"""
import json
import os
import re
import shutil
import subprocess
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
DST = os.path.join(HERE, "..", "..", "game", "assets", "sfx")
PACKS = {   # name: (zip on OpenGameArt, its page)
    "rpg": ("https://opengameart.org/sites/default/files/RPGsounds_Kenney.zip", "https://opengameart.org/content/50-rpg-sound-effects"),
    "scifi": ("https://opengameart.org/sites/default/files/sci-fi_sounds.zip", "https://opengameart.org/content/sci-fi-sounds"),
    "interface": ("https://opengameart.org/sites/default/files/kenney_interfaceSounds.zip", "https://opengameart.org/content/interface-sounds"),
    "digital": ("https://opengameart.org/sites/default/files/Digital_SFX_Set.zip", "https://opengameart.org/content/63-digital-sound-effects-lasers-phasers-space-etc"),
    "jingles": ("https://opengameart.org/sites/default/files/jingleSounds_Kenney.zip", "https://opengameart.org/content/85-short-music-jingles"),
}
SOUNDS = {   # the game's sound: (what it is for, [(pack, file in the pack)], gain in dB on top of the normalising)
    "hit_metal": ("рой кусает голема: хитин по металлу", [("scifi", f"Audio/impactMetal_00{i}.ogg") for i in range(5)], -9),
    "hit_flesh": ("голем бьёт особь: хруст и удар", [("rpg", "OGG/chop.ogg"), ("rpg", "OGG/knifeSlice.ogg"),
                                                    ("rpg", "OGG/knifeSlice2.ogg")], -8),
    "zap": ("разряд Мудреца и Изобретателя", [("digital", "zap1.mp3"), ("digital", "zap2.mp3"),
                                             ("scifi", "Audio/laserSmall_000.ogg")], -9),
    "blast": ("залп Мортиры", [("scifi", "Audio/lowFrequency_explosion_000.ogg"),
                               ("scifi", "Audio/lowFrequency_explosion_001.ogg")], -4),
    "squish": ("гибель особи: мокрый шлепок", [("scifi", "Audio/slime_000.ogg"), ("scifi", "Audio/slime_001.ogg")], -10),
    "break": ("голем сломан: хруст металла", [("scifi", f"Audio/explosionCrunch_00{i}.ogg") for i in range(3)], -5),
    "heal": ("ремонт Механика", [("digital", "powerUp2.mp3"), ("digital", "powerUp3.mp3")], -14),
    "miss": ("промах: свист", [("rpg", f"OGG/drawKnife{i}.ogg") for i in (1, 2, 3)], -12),
    "step": ("шаг голема", [("rpg", f"OGG/footstep0{i}.ogg") for i in range(5)], -16),
    "click": ("кнопка", [("interface", f"Audio/click_00{i}.ogg") for i in (1, 2, 3)], -8),
    "toggle": ("переключатель: пауза, скорость", [("interface", f"Audio/switch_00{i}.ogg") for i in (1, 2, 3)], -8),
    "win": ("победа", [("jingles", "OGG/jingles_NES/jingles_NES12.ogg")], -6),
    "lose": ("поражение", [("jingles", "OGG/jingles_NES/jingles_NES11.ogg")], -6),
}


def fetch():
    os.makedirs(CACHE, exist_ok=True)
    for name, (url, _page) in PACKS.items():
        d = os.path.join(CACHE, name)
        if os.path.isdir(d):
            continue
        z = os.path.join(CACHE, name + ".zip")
        urllib.request.urlretrieve(url, z)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(d)
        print("fetched", name)


def find(pack, rel):
    """The file in the unpacked pack (packs keep their own top folder)."""
    root = os.path.join(CACHE, pack)
    for dirpath, _dirs, files in os.walk(root):
        cand = os.path.join(dirpath, os.path.basename(rel))
        if os.path.basename(rel) in files and cand.replace("\\", "/").endswith(rel):
            return cand
    raise FileNotFoundError(f"{pack}: {rel}")


def peak_db(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"max_volume: (-?[\d.]+) dB", out)
    return float(m.group(1)) if m else 0.0


def convert(src, dst, gain):
    tmp = dst + ".tmp.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "44100",
                    "-af", "silenceremove=start_periods=1:start_threshold=-50dB", tmp], check=True)
    g = -1.0 - peak_db(tmp) + gain
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={g:.2f}dB", "-c:a", "libvorbis",
                    "-q:a", "4", dst], check=True)
    os.remove(tmp)


def main():
    fetch()
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    os.makedirs(DST)
    manifest, rows = {}, []
    for name, (what, files, gain) in SOUNDS.items():
        outs = []
        for i, (pack, rel) in enumerate(files):
            out = f"{name}_{i}.ogg"
            convert(find(pack, rel), os.path.join(DST, out), gain)
            outs.append(f"sfx/{out}")
            rows.append(f"| `{out}` | {what} | Kenney, {pack}: `{rel}` | [{PACKS[pack][1].split('/')[-1]}]({PACKS[pack][1]}) |")
        manifest[name] = outs
    json.dump(manifest, open(os.path.join(DST, "sfx.json"), "w"), ensure_ascii=False, indent=1)
    lic = find("scifi", "License.txt")
    shutil.copy(lic, os.path.join(DST, "LICENSE-Kenney.txt"))
    with open(os.path.join(DST, "SOURCES.md"), "w") as f:
        f.write("# Откуда звуки\n\nВсе — Kenney (www.kenney.nl), лицензия CC0 1.0: можно в коммерческих проектах, указывать "
                "автора не обязательно, можно распространять. Наборы скачаны с OpenGameArt, куда их выложил сам Kenney "
                "(пользователь `kenney`). Обработка: моно 44,1 кГц, тишина в начале срезана, пик −1 dBFS плюс поправка "
                "громкости звука, OGG Vorbis (`tools/audio/kenney_sfx.py`).\n\n| Файл | Для чего | Откуда | Страница набора |\n|---|---|---|---|\n")
        f.write("\n".join(rows) + "\n")
    print(len(rows), "files ->", DST)


if __name__ == "__main__":
    main()
