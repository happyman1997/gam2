"""A screenshot of a real simulated battle: reads the state the `snapshot` tool prints and draws it.

    cargo run --release --bin snapshot -- zodchiy 3 3 > tools/sprites/out/shot.json
    python3 tools/sprites/sim_shot.py tools/sprites/out/shot.json
"""
import json
import random
import sys
from PIL import ImageFont
from kit import *
import golem7 as G
import frames as F
import golems_h as GH
import colossus as CL
import leaders_h as LH
import maniac as MN
import swarm1 as W
from golem7 import cfg
from battle import shadow, put, flash, spark, dead_bug
from noise import value_noise
from paths import font, out

S = 2
WW, HH = 960, 540
FW, FH = 18, 14                     # field size in cells (sim/src/battle.rs)
CW, CH, X0, Y0 = 50, 34, 30, 50
ZONE = 6

def footprint_n(size):
    return 1 if size <= 4 else {5: 2, 6: 3}.get(size, 4)


def ground(sc):
    yy, xx = sc.yy, sc.xx
    th = BAYER[yy % 4, xx % 4]
    n1 = value_noise(WW, HH, 20, 11) * 0.5 + value_noise(WW, HH, 6, 12) * 0.5
    lv = np.clip(np.floor(n1 * 4 + (th - 0.5) * 1.2), 0, 3).astype(int)
    for i, c in enumerate(("#262030", "#2a2334", "#2e2638", "#32293c")):
        sc.rgb[lv == i] = hexc(c)
    n2 = value_noise(WW, HH, 24, 13) * 0.6 + value_noise(WW, HH, 6, 14) * 0.4
    centre = np.exp(-((xx - 480 - 30 * np.sin(yy / 60.0)) / 120.0) ** 2)
    dirt = (n2 * 0.8 + centre * 0.5 + (th - 0.5) * 0.15) > 0.8
    sc.rgb[dirt] = sc.rgb[dirt] * 0.82 + hexc("#2a1e22") * 0.18
    rnd = random.Random(5)
    for _ in range(2200):
        x, y = rnd.randrange(1, WW - 1), rnd.randrange(3, HH)
        if dirt[y, x]:
            continue
        col = hexc(rnd.choice(("#2c3a3a", "#33443f", "#283432", "#3a4a44")))
        for k in range(rnd.randint(1, 3)):
            sc.rgb[y - k, x + (rnd.choice((-1, 0, 1)) if k else 0)] = col
    for c in range(FW + 1):
        for r in range(FH + 1):
            x, y = X0 + c * CW, Y0 + r * CH
            if not (0 <= x < WW and 0 <= y < HH):
                continue
            col = hexc("#c9b27a") if c <= ZONE else (hexc("#9a8ab8") if c >= FW - ZONE else hexc("#6a6070"))
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                if 0 <= x + dx < WW and 0 <= y + dy < HH:
                    sc.rgb[y + dy, x + dx] = sc.rgb[y + dy, x + dx] * 0.75 + col * 0.25


def hp_bar(sc, x, y, w, frac):
    x0, y0 = int(x - w / 2), int(y)
    sc.rgb[y0:y0 + 3, x0 - 1:x0 + w + 1] = hexc("#0c0a10")
    fill = int(round(w * max(0.0, min(1.0, frac))))
    col = hexc("#8fd06a") if frac > 0.5 else (hexc("#e0b040") if frac > 0.25 else hexc("#e05a40"))
    sc.rgb[y0 + 1:y0 + 2, x0:x0 + fill] = col
    sc.occ[y0:y0 + 3, x0 - 1:x0 + w + 1] = True


def unit_sprite(u, pose):
    name = u["name"]
    if name in F.FRAMES:
        return F.build(name, pose)
    if name == "Каменщик":
        return GH.build(GH.MASON, pose, k=0.85)
    if name == "Зодчий":
        return GH.build(LH.ZODCHIY, pose, 1.05)
    if name == "Отец колосса":
        return GH.colossus_build("idle" if pose == "broken" else pose, 3.5)
    if name == "Изобретатель":
        return GH.build(LH.INVENTOR, pose, 0.9)
    if name == "Маньяк":
        return GH.build(GH.MANIAC, pose, 1.3)
    soldier = name == "Солдат"
    rnd = random.Random(u["id"] * 7919)
    return W.build((), rnd.uniform(-0.14, 0.14), "attack" if pose == "attack" else "idle", soldier, k=1.0,
                   genes=W.genes_for(rnd.randrange(10 ** 6)))


SLOTS = {1: [(-0.24, -0.2), (0.24, -0.2), (-0.24, 0.24), (0.24, 0.24)], 2: [(-0.22, -0.05), (0.24, 0.12)]}


def build(state):
    sc = Scene(WW, HH)
    ground(sc)
    units = state["units"]
    attackers = {a for a, _, _ in state["hits"]}
    dmg_to = {}
    for a, t, d in state["hits"]:
        dmg_to[t] = dmg_to.get(t, 0) + d
    items, labels = [], []

    # small units share cells: give each its own spot inside the cell
    cellmates = {}
    for u in units:
        if footprint_n(u["size"]) == 1 and u["size"] <= 2 and (u["alive"] and u["on_field"] or not u["alive"]):
            cellmates.setdefault((u["side"], u["x"], u["y"]), []).append(u["id"])

    for u in units:
        if u["alive"] and not u["on_field"]:
            continue                                   # fled the field
        n = footprint_n(u["size"])
        if n == 1 and u["size"] <= 2:
            mates = cellmates[(u["side"], u["x"], u["y"])]
            k = mates.index(u["id"])
            slots = SLOTS[1] if u["size"] == 1 else SLOTS[2]
            ox, oy = slots[k % len(slots)]
            fx = X0 + (u["x"] + 0.5 + ox) * CW
            fy = Y0 + (u["y"] + 0.62 + oy) * CH
        else:
            fx = X0 + (u["x"] + n / 2) * CW
            fy = Y0 + (u["y"] + n * 0.72) * CH
        mirror = u["side"] == 1 and not u["fleeing"]
        if u["side"] == 0 and u["fleeing"]:
            mirror = True
        if not u["alive"]:
            if u["side"] == 1:
                spr = dead_bug(0.0, u["id"])
                items.append((fy - 4, lambda spr=spr, fx=fx, fy=fy: put(sc, spr, fx, fy, mirror=True)))
            else:
                spr = unit_sprite(u, "broken")
                items.append((fy, lambda spr=spr, fx=fx, fy=fy: (shadow(sc, fx, fy, 22 * n + 14, 6 + 3 * n), put(sc, spr, fx, fy))))
            if u["id"] in dmg_to:
                labels.append((fx, fy - 30, dmg_to[u["id"]], True))
            continue
        pose = "attack" if u["id"] in attackers else "idle"
        spr = unit_sprite(u, pose)
        if n > 1:        # a big unit stands at the front of its square, so its blows reach the cell beyond
            cols = np.nonzero(spr.a[: spr.oy + 2].max(axis=0))[0]
            facing = -1 if mirror else 1
            reach = (cols.max() - spr.ox) if facing > 0 else (spr.ox - cols.min())
            fx += facing * max(0.0, n * CW / 2 - reach - 4)
        hit = dmg_to.get(u["id"], 0)
        if hit > 0:
            spr = flash(spr, 0.45)
        big = n > 1 or u["size"] >= 3

        def draw(u=u, spr=spr, fx=fx, fy=fy, n=n, mirror=mirror, big=big, hit=hit):
            if big:
                shadow(sc, fx + 2, fy, 22 * n + 14, 6 + 3 * n)
            else:
                shadow(sc, fx - 1, fy, 14, 3)
            put(sc, spr, fx, fy, mirror=mirror)
            rows = np.nonzero(spr.a.max(axis=1) > 0)[0]
            top = fy - spr.oy + (rows[0] if len(rows) else 0)
            if big:
                hp_bar(sc, fx, max(2, top - 7), 16 + 8 * n, u["hp"] / u["max"])
            if hit > 0:
                spark(sc, int(fx + (-6 if u["side"] == 1 else 6)), int(fy - (fy - top) * 0.55), big=hit >= 10)
            if u["id"] in dmg_to:
                if big:
                    labels.append((fx + 8 + 4 * n + 14, top - 2, hit, False))
                else:
                    labels.append((fx, top - 2, hit, False))
        items.append((fy, draw))

    for _, f in sorted(items, key=lambda t: t[0]):
        f()
    return sc, labels


def overlay(img, state, labels):
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 26)
    fn = ImageFont.truetype(font("PTSerif-Bold.ttf"), 20)
    fs = ImageFont.truetype(font("PTSerif-Regular.ttf"), 17)
    for x, y, dmg, killed in labels:
        t = str(dmg)
        tx, ty = x * S - d.textlength(t, font=fn) / 2, y * S - 22
        col = (240, 96, 72) if killed else ((150, 146, 156) if dmg == 0 else ((255, 224, 140) if dmg >= 10 else (240, 232, 214)))
        d.text((tx + 2, ty + 2), t, font=fn, fill=(12, 8, 10))
        d.text((tx, ty), t, font=fn, fill=col)
    t = f"Раунд {state['round']}"
    w = d.textlength(t, font=ft)
    d.rectangle([WW - w / 2 - 22, 12, WW + w / 2 + 22, 54], fill=(18, 16, 22), outline=(110, 100, 130))
    d.text((WW - w / 2, 17), t, font=ft, fill=(230, 222, 206))
    units = state["units"]
    a = [u for u in units if u["side"] == 0]
    b = [u for u in units if u["side"] == 1]
    on = lambda xs: sum(1 for u in xs if u["alive"] and u["on_field"])
    run = lambda xs: sum(1 for u in xs if u["alive"] and u["on_field"] and u["fleeing"])
    dead = lambda xs: sum(1 for u in xs if not u["alive"])
    gone = lambda xs: sum(1 for u in xs if u["alive"] and not u["on_field"])
    names = []
    for u in a:
        if u["name"] not in names:
            names.append(u["name"])
    left = "Литейщик: " + ", ".join(names).lower().replace("зодчий", "Зодчий") + f" · сломано {dead(a)}"
    right = f"Рой: на поле {on(b)}, из них бегут {run(b)} · погибло {dead(b)} · ушло с поля {gone(b)}"
    d.text((24, HH * S - 36), left, font=fs, fill=(214, 196, 150))
    d.text((WW * S - 24 - d.textlength(right, font=fs), HH * S - 36), right, font=fs, fill=(196, 186, 214))
    cap = f"{state['title']} · кадр из симуляции, зерно {state['seed']}"
    d.text((24, 20), cap, font=fs, fill=(170, 160, 150))


if __name__ == "__main__":
    state = json.load(open(sys.argv[1], encoding="utf-8"))
    sc, labels = build(state)
    img = sc.image(S)
    overlay(img, state, labels)
    path = out(sys.argv[2] if len(sys.argv) > 2 else "sim_shot.png")
    img.save(path)
    print(path, img.size)
