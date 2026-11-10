"""The Foundry's five frames: each with its own paint, its battle scale and its role; build() draws them
(humanoid.py for the Guard, golems_h.py for the rest); the sheet foundry_frames.png."""
import numpy as np
from kit import *

PAINT = {   # every frame keeps its own colour key; all of them worked, scuffed metal
    "Страж": ramp("#0e1218", "#1c2430", "#2e3a4a", "#4a5a6e", "#7a8aa0"),     # blued steel
    "Горн": ramp("#1a0806", "#3a120c", "#5a2014", "#823222", "#b0563a"),      # firebrick
    "Орудие": ramp("#10120a", "#1e2214", "#323820", "#4e5632", "#7a8452"),    # olive drab
    "Механик": ramp("#1a1206", "#3a280c", "#5e4214", "#8a6420", "#c49a3a"),   # workshop ochre
    "Мудрец": ramp("#170c08", "#32190f", "#542c18", "#7e4626", "#ab6c3c"),    # old copper and porcelain
}

FRAMES = {   # scale on the battlefield (size 4 → 1.15, 5 → 1.6, 6 → 2.2), role
    "Страж": (2.2, "танк · 6"),
    "Мудрец": (1.6, "маг · 5"),
    "Горн": (1.6, "контроль · 5"),
    "Орудие": (1.6, "стрелок · 5"),
    "Механик": (1.15, "поддержка · 4"),
}


def build(name, pose="idle", k=None):
    """The frame's sprite: the humanoid machines of humanoid.py (the Guard) and golems_h.py (the rest)."""
    import humanoid as HM
    import golems_h as GH
    k = FRAMES[name][0] if k is None else k
    if name == "Страж":
        return HM.build(pose, k)
    return GH.build(GH.BY_NAME[name], pose, k)


def hit(name):
    """Model-space point where the frame's attack lands, or None (the Mechanic repairs, it does not hit)."""
    import humanoid as HM
    import golems_h as GH
    if name == "Страж":
        return HM.hit_point()
    if name == "Орудие":                 # shells go down-range: the target stands a few cells ahead
        _, info = GH.creature_parts(GH.ORUDIE, GH.ORUDIE["poses"]["attack"], fx=False)
        mz, d = info["n"]["muzzle"], info["n"]["d"]
        h = np.array((d[0], 0.0, d[2] * 0.3))
        return np.array((mz[0], 0.0, mz[2])) + h / np.linalg.norm(h) * 55.0
    return GH.hit_point(GH.BY_NAME[name])


def to_screen(p, k):
    """Model point -> pixel offset from a sprite's ground origin, as r3d projects it."""
    from r3d import rot_y, SA, CA, YAW
    q = rot_y(YAW) @ np.array(p, float)
    return q[0] * k, (q[2] * SA - q[1] * CA) * k


if __name__ == "__main__":
    from PIL import ImageFont
    from noise import value_noise
    from paths import font, out
    S = 2
    WW, HH = 960, 540
    sc = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 81) * 0.6 + value_noise(WW, HH, 5, 82) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        sc.rgb[lv == i] = hexc(col)
    names = list(FRAMES)
    for i, name in enumerate(names):
        cx = 88 + i * 192
        for j, pose in enumerate(("idle", "attack")):
            spr = build(name, pose, k=FRAMES[name][0] * 1.15)
            by = 250 + j * 250
            e = ((sc.xx - cx) / (36 * FRAMES[name][0])) ** 2 + ((sc.yy - by) / 7) ** 2
            sc.rgb[e <= 1] *= 0.62
            sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 22)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 16)
    d.text((24, 12), "Литейщик: пять фреймов — свой цвет и свой силуэт у каждой роли", font=ft, fill=(236, 226, 200))
    d.text((24, 52), "Человекоподобные машины. Сверху покой, снизу атака — момент удара. В настоящем соотношении размеров.",
           font=fr, fill=(190, 182, 164))
    for i, name in enumerate(names):
        cx = (88 + i * 192) * S
        d.text((cx - d.textlength(name, font=fh) / 2, 272 * S), name, font=fh, fill=(226, 186, 106))
        sub = FRAMES[name][1]
        d.text((cx - d.textlength(sub, font=fr) / 2, 272 * S + 28), sub, font=fr, fill=(190, 182, 164))
    img.save(out("foundry_frames.png"))
    print(img.size)
