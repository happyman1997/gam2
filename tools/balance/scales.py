"""Scales by size from Dominions 5 (Illwinter, the studio behind Conquest of Elysium).

Downloads the community unit table (dom5inspector, BaseU.csv) into tools/balance/cache once,
and prints medians by size, translated into our size scale. The data itself is not stored in git.

    .venv/bin/python -I tools/balance/scales.py
"""
import csv
import os
import sys
import urllib.request

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
URL = "https://raw.githubusercontent.com/larzm42/dom5inspector/gh-pages/gamedata/BaseU.csv"

# our size -> Dominions size (our human is 3, theirs is 2; our size 2 sits between their 1 and 2)
OURS = {1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0, 5: 4.0, 6: 5.0, 7: 6.0}
HUMAN_HP = 12          # our human (size 3) — the anchor of the scale
HUMAN_DMG = 4.5        # average blow of our human: 1–6 +1


def load():
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "BaseU.csv")
    if not os.path.exists(path):
        urllib.request.urlretrieve(URL, path)
    return list(csv.DictReader(open(path, encoding="utf-8", errors="ignore"), delimiter="\t"))


def num(r, k):
    try:
        return float(r.get(k) or 0)
    except ValueError:
        return 0.0


def by_size(rows):
    seen, groups = set(), {}
    for r in rows:
        key = (r["name"], r["hp"], r["size"])
        if key in seen or num(r, "hp") <= 0:
            continue
        seen.add(key)
        groups.setdefault(int(num(r, "size")), []).append(r)
    stats = {}
    for s, v in groups.items():
        col = lambda k: np.array([num(r, k) for r in v])
        hp = col("hp")
        stats[s] = dict(n=len(v), hp=np.median(hp), hp10=np.percentile(hp, 10), hp90=np.percentile(hp, 90),
                        prot=np.median(col("prot")), str=np.median(col("str")), mor=np.median(col("mor")))
    return stats


def interp(stats, s, key):
    lo, hi = int(np.floor(s)), int(np.ceil(s))
    if lo == hi:
        return stats[lo][key]
    t = s - lo
    return float(np.exp(np.log(stats[lo][key]) * (1 - t) + np.log(stats[hi][key]) * t))


def main():
    stats = by_size(load())
    print("Dominions 5, медианы по размеру")
    print("| Размер | Юнитов | Здоровье | 10–90% | Броня | Сила | Боевой дух |")
    print("|---|---|---|---|---|---|---|")
    for s in sorted(stats):
        d = stats[s]
        print(f"| {s} | {d['n']} | {d['hp']:.0f} | {d['hp10']:.0f}–{d['hp90']:.0f} | {d['prot']:.0f} | {d['str']:.0f} | {d['mor']:.0f} |")
    base_hp, base_str = stats[2]["hp"], stats[2]["str"]
    print("\nНаша шкала (человек размера 3: здоровье 12, удар в среднем 4,5)")
    print("| Размер | Здоровье, обычное | Здоровье, элита (90%) | Средний удар |")
    print("|---|---|---|---|")
    for ours, theirs in OURS.items():
        hp = HUMAN_HP * interp(stats, theirs, "hp") / base_hp
        hp90 = HUMAN_HP * interp(stats, theirs, "hp90") / base_hp
        dmg = HUMAN_DMG * interp(stats, theirs, "str") / base_str
        print(f"| {ours} | {hp:.0f} | {hp90:.0f} | {dmg:.1f} |")


if __name__ == "__main__":
    sys.exit(main())
