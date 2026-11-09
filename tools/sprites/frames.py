"""The Foundry's five frames: each with its own paint, its own silhouette parts and the modules of its role.
PAINT keeps the old Molot's soot-black for the earlier box-bodied sheets (sheet_tiers)."""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
import golem6 as G6
import golem7 as G
from golem6 import M_IRON, M_DIRON, M_BRONZE, M_HOLE, M_STEEL, M_RUST, M_HOSE, emissive, spike, STYLE1
from golem7 import cfg, M_PUFF

PAINT = {   # every frame keeps its own colour key; all of them worked, scuffed metal
    "Страж": ramp("#0e1218", "#1c2430", "#2e3a4a", "#4a5a6e", "#7a8aa0"),     # blued steel
    "Молот": ramp("#0e0c0c", "#1c1816", "#2e2824", "#4a4038", "#766a5c"),     # soot-black
    "Горн": ramp("#1a0806", "#3a120c", "#5a2014", "#823222", "#b0563a"),      # firebrick
    "Орудие": ramp("#10120a", "#1e2214", "#323820", "#4e5632", "#7a8452"),    # olive drab
    "Механик": ramp("#1a1206", "#3a280c", "#5e4214", "#8a6420", "#c49a3a"),   # workshop ochre
    "Мудрец": ramp("#170c08", "#32190f", "#542c18", "#7e4626", "#ab6c3c"),    # old copper and porcelain
}

FRAMES = {   # cfg, module levels, scale (size 4 → 1.15, 5 → 1.6, 6 → 2.2), role
    "Страж": (cfg(legs="pillars", arms=("heavy", "heavy"), tools=("hammer", "shield")),
             dict(legs=2, head=2, core=2, armour=3, arm_far=2, arm_near=2, tool_far=1, tool_near=3), 2.2, "танк · 6"),
    "Мудрец": (cfg(legs="pillars", head="sensor", core="volt", arms=("piston", "piston"), tools=("claw", "claw")),
              2, 1.6, "маг · 5"),
    "Горн": (cfg(legs="tracks", core="fire", arms=("piston", "piston"), tools=("claw", "claw")),
            2, 1.6, "контроль · 5"),
    "Орудие": (cfg(legs="spider", head="sensor", arms=("piston", "piston"), tools=("cannon", "cannon")),
              dict(legs=2, head=3, core=2, armour=2, arm_far=2, arm_near=2, tool_far=2, tool_near=2), 1.6, "стрелок · 5"),
    "Механик": (cfg(legs="spider", head="sensor", arms=("long", "long"), tools=("claw", "claw")),
               1, 1.15, "поддержка · 4"),
}


def repaint(m, old, new):
    out = Model()
    out.ops = [tuple(new if x is old else x for x in op) for op in m.ops]
    return out


def extras(name, m, hip, pose):
    """The parts that make each frame's silhouette its own."""
    if name == "Страж":       # a tall armoured back plate: the widest, tallest outline
        G6.tbox(m, (-7.0, hip + 21.0, 0), (3.0, 17.0), (2.4, 12.0), 12.0, M_IRON)
        for z in (-4.0, 0.0, 4.0):
            m.ell((-5.6, hip + 26.0, z), (0.4, 0.5, 0.5), M_STEEL)
    elif name == "Горн":      # a furnace: a tall chimney with smoke and a glowing fire-box grate
        c0 = np.array((-6.5, hip + 15.0, 0))
        top = c0 + np.array((-1.0, 21.0, 0))
        m.cyl(c0, top, 2.6, M_DIRON, r1=2.2, seg=10)
        m.cyl(top, top + (0, 1.4, 0), 3.2, M_IRON, seg=10)
        for f in (0.3, 0.62):
            p = c0 + (top - c0) * f
            m.cyl(p, p + (0, 0.8, 0), 2.9, M_RUST, seg=10)
        for i, d in enumerate(((0.0, 3.0, 0.0), (-1.5, 6.0, 0.8), (-3.5, 9.5, -0.6))):
            m.ell(top + np.array(d), (2.0 + i * 0.9, 1.6 + i * 0.7, 1.8 + i * 0.8), M_PUFF)
        fire = emissive("fire", 16, 0.7)
        m.box((9.4, hip + 6.0, 0), (0.8, 4.2, 9.5), fire)
        for z in (-3.6, -1.2, 1.2, 3.6):
            m.box((9.9, hip + 6.0, z), (0.6, 4.8, 0.7), M_DIRON)
        if pose == "attack":
            for i in range(4):
                m.ell((12.5 + i * 3.2, hip + 6.0 - i * 0.6, 0), (2.2 + i * 0.6, 1.6 + i * 0.4, 1.6 + i * 0.5), emissive("fire", 14, 0.8))
    elif name == "Орудие":    # an ammunition drum on the back and a range-finder
        d = np.array((-8.0, hip + 12.0, 0))
        m.cyl(d + (0, 0, -4.5), d + (0, 0, 4.5), 4.4, M_DIRON, seg=14)
        for z in (-3.0, 0.0, 3.0):
            m.cyl(d + (0, 0, z - 0.4), d + (0, 0, z + 0.4), 4.8, M_BRONZE, seg=14)
        m.cyl((-3.0, hip + 12.0, 3.0), (-3.0, hip + 8.0, 9.0), 0.8, M_HOSE, seg=6)
        rf = np.array((0.0, hip + 27.0, -3.0))
        m.cyl(rf, rf + (5.0, 0.4, 0), 0.8, M_DIRON, seg=6)
        m.ell(rf + (5.2, 0.4, 0), (0.4, 0.8, 0.8), emissive("fire", 6, 0.5))
    elif name == "Механик":   # a crane jib with a hook, a toolbox on the hip
        base = np.array((-5.0, hip + 18.0, -4.0))
        mast = np.array((-4.0, hip + 36.0, -4.0))
        tip = np.array((14.0, hip + 37.5, -4.0))
        m.cyl(base, mast, 1.5, M_IRON, seg=6)
        m.cyl(mast + (-5.0, 0, 0), tip, 1.2, M_IRON, seg=6)
        for f in (0.25, 0.5, 0.75):                              # truss braces
            p = mast + (tip - mast) * f
            m.cyl(p, mast + (0, -6.0, 0) + (tip - mast) * (f - 0.2), 0.45, M_STEEL, seg=4)
        G6.tbox(m, mast + (-7.5, -1.0, 0), (3.6, 3.6), (3.6, 3.6), 3.2, M_DIRON)       # counterweight
        hook_y = hip + (16.0 if pose == "idle" else 11.0)
        hk = np.array((tip[0], hook_y, tip[2]))
        m.cyl(tip, hk, 0.3, M_HOSE, seg=4)
        m.cyl(hk, hk + (0.9, -2.2, 0), 0.75, M_STEEL, seg=5)
        m.cyl(hk + (0.9, -2.2, 0), hk + (-0.9, -3.6, 0), 0.65, M_STEEL, seg=5)
        G6.tbox(m, (1.0, hip + 4.5, 9.8), (6.0, 3.0), (6.0, 3.0), 3.4, M_RUST)
        m.cyl((-1.0, hip + 6.6, 9.8), (3.0, hip + 6.6, 9.8), 0.3, M_STEEL, seg=4)
        if pose == "attack":       # a welding torch flaring
            m.ell((13.0, hip + 4.0, 6.0), (1.4, 1.4, 1.4), emissive("volt", 12, 0.9))


def model(name, pose="idle"):
    c, lv, _, _ = FRAMES[name]
    hip = G.HIP[c["legs"]]
    m = G.model(c, lv, pose)
    if pose != "broken":
        extras(name, m, hip, pose)
    return repaint(m, M_BRONZE, Mat(PAINT[name]))


def build(name, pose="idle", k=None):
    """The frame's sprite. The frames are humanoid machines now (humanoid.py, golems_h.py);
    build_boxy keeps the earlier box-bodied golems for reference."""
    import humanoid as HM
    import golems_h as GH
    k = FRAMES[name][2] if k is None else k
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


def build_boxy(name, pose="idle", k=None):
    k = FRAMES[name][2] if k is None else k
    w, h, ox, oy = G.dims(k)
    h = int(h * 1.25)
    oy = oy + (h - G.dims(k)[1])
    spr = rim_light(render(model(name, pose).scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


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
            spr = build(name, pose, k=FRAMES[name][2] * 1.15)
            by = 250 + j * 250
            e = ((sc.xx - cx) / (36 * FRAMES[name][2])) ** 2 + ((sc.yy - by) / 7) ** 2
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
        sub = FRAMES[name][3]
        d.text((cx - d.textlength(sub, font=fr) / 2, 272 * S + 28), sub, font=fr, fill=(190, 182, 164))
    img.save(out("foundry_frames.png"))
    print(img.size)
