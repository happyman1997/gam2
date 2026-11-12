"""A golem assembled from parts: a hull (корпус — the frame: role, size, its back unit, its own rule), legs, two arms,
a head, a core and the hull's own role modules. Legs, arms and heads are common: any of them goes on any hull; the
role modules go only on their hull, and a few of them need a part to ride on (a long barrel needs a cannon).

Every part is the drawing it always was, lifted off the golem it was drawn for: the heads come off their donors at
the neck and are set on the new hull's neck; the arms are the hand items, held as their donor held them; the legs are
leg functions on the hull's own hips.

    python3 tools/sprites/golem_parts.py        -> out/golem_parts.png (every part on one hull, and mixed builds)
"""
import numpy as np
from kit import *
from r3d import Model, Mat, render, rot_z, rot_y, rot_x, I3
from golem6 import M_IRON, M_DIRON, M_STEEL, M_HOLE, spike, STYLE1
import golems_h as GH
import humanoid as HM
import frames as F
from humanoid import arr, unit, lerp, Parts, fist, ram, rivets, block, leg as plain_leg
from clipcheck import cells, STEP

# ---------------------------------------------------------------- hulls
def guard_torso(G, P, S):
    HM.torso(G, P)


GUARD = dict(
    name="Страж", role="танк · 6", k=2.2, paint=F.PAINT["Страж"], canvas=(82, 80, 36, 72),
    hip=HM.HIP, hz=HM.HZ, hipx=(0.4, -0.8), LT=HM.LT, LS=HM.LS, LU=HM.LU, LF=HM.LF, th_leg=1.0, th_arm=1.0,
    sh=arr(HM.SH), torso=guard_torso,
    poses=dict(idle=dict(lean=0.0, t=(0.0, 0.0, 0.0), ank=((2.8, 3.6, HM.HZ + 0.7), (-4.6, 3.6, -HM.HZ - 0.8)))),
)
HULLS = {"Страж": GUARD, **{n: GH.BY_NAME[n] for n in ("Мудрец", "Горн", "Орудие", "Механик")}}


# ---------------------------------------------------------------- arms: what each hand holds
def _maul(G, side, sh, el, w, s, P, A, S):
    """Паровой молот, carried on the shoulder as the Guard carries it."""
    rest = arr(sh) + arr((-0.2, 5.7, 0.4)) * arr((1, 1, s))
    u = HM.grip_on(w, w - el, rest, s)
    hand, _, u = fist(G, "hand_" + side, w, w - el, u, s, P)
    face, hc = HM.maul(G, hand, u, P, (0, 1, 0), reach=13.0)
    return dict(face=face, hc=hc, hand=hand, u=u, w=w, el=el)


def _shield(G, side, sh, el, w, s, P, A, S):
    """Башенный щит on a bracket through the fist."""
    fc, hf, uf = fist(G, "hand_" + side, w, w - el, (0, 1, 0), s, P)
    R = rot_y(0.5 if s < 0 else 0.15)                   # face to the viewer, in either hand
    sc = fc + R @ arr((HM.SHIELD_GAP + 0.75, 0, 0)) + arr((0, 0, 1.2 * s if s > 0 else 0))
    back = HM.shield(G, sc, R, P)
    HM.bracket(G, fc, uf, back, R)
    return dict(sc=sc, R=R, fc=fc, w=w, el=el)


def _fist(G, side, sh, el, w, s, P, A, S):
    """Кулак-поршень: a bare fist on a piston wrist, a striking plate over the knuckles."""
    d = unit(w - el)
    hand, h, u = fist(G, "hand_" + side, w, w - el, arr((0, 1.0, 0)) - d * d[1] + arr((1e-3, 0, 0)), s, P, th=1.15)
    g = G["item_" + side]
    g.cyl(w - d * 3.4, w - d * 0.6, 1.25, M_DIRON, seg=10)                                  # the wrist piston
    g.cyl(w - d * 3.0, w - d * 2.4, 1.5, M_STEEL, seg=10)
    return dict(w=w, d=d, hand=hand)


def _flame(G, side, sh, el, w, s, P, A, S):
    X = A["_X"]
    A2 = dict(A, _X=(lambda p: X(arr(p) * arr((1, 1, s)))))                              # the hose to the near side's back
    return GH.flamethrower(G, side, sh, el, w, s, P, A2, S)


def _side(d, s):
    """A donor's hand pose for the near side, mirrored to the far side (s = -1)."""
    out = {}
    for k, v in d.items():
        out[k] = tuple(np.array(v) * (1, 1, s)) if isinstance(v, tuple) and len(v) == 3 and k in ("hand", "pole") else v
    return out


ARMS = {   # key: name, item, the pose its donor holds it in (near side), extra pose keys
    "fist": ("Кулак-поршень", _fist, dict(hand=(4.0, -11.6, 1.6), pole=(-0.5, -0.2, 1.0))),
    "maul": ("Паровой молот", _maul, dict(hand=(HM.WX, HM.WY, HM.WZ), pole=(1.4, -7.6, 2.0))),
    "shield": ("Щит", _shield, dict(hand=(5.8, -10.0, 2.0), pole=(0.8, -8.0, 1.6))),
    "cannon": ("Пушка", GH.cannon, dict(hand=(8.2, -8.6, 3.0), pole=(-1.0, -0.5, 0.6),
                                        far=dict(hand=(8.0, -3.4, 3.6), pole=(-1.0, -0.8, 0.5)))),
    "staff": ("Посох-электрод", GH.sage_staff, dict(hand=(5.0, -8.0, 4.0), pole=(-0.6, -0.6, 1.0),
                                                    staff_dir=(0.05, 1.0, 0.05), hold=0.46)),
    "focus": ("Ладонь-разрядник", GH.sage_focus, dict(hand=(5.0, -12.0, 1.2), pole=(-0.4, -0.2, 1.0))),
    "flame": ("Огнемёт", _flame, dict(hand=(5.0, -12.5, 3.0), pole=(-0.4, -0.2, 1.0))),
    "tongs": ("Клещи", GH.tongs, dict(hand=(3.0, -13.4, 2.8), pole=(-0.3, -0.2, 1.0), open=10.0)),
    "wrench": ("Ключ", GH.big_wrench, dict(hand=(3.4, -11.0, 2.4), pole=(-0.5, -0.2, 1.0), wrench_dir=(0.25, -0.97, 0.0))),
    "can": ("Лейка", GH.oil_can, dict(hand=(4.8, -8.6, 2.4), pole=(-0.6, -0.4, 1.0), can_dir=(0.0, 1.0, 0.0))),
    # rare
    "spark": ("Искрящий молот", lambda *a: _rare_item("spark")(*a), dict(hand=(3.4, -11.0, 2.4), pole=(-0.5, -0.2, 1.0))),
    "poker": ("Кочерга", lambda *a: _rare_item("poker")(*a), dict(hand=(3.0, -13.4, 2.8), pole=(-0.3, -0.2, 1.0))),
    "flail": ("Кистень", lambda *a: _flail(*a), dict(hand=(6.4, -12.6, 2.6), pole=(1.6, -7.4, 1.8))),
}
RARE_PARTS = {"spark", "poker", "flail", "tracks", "mill"}


def _rare_item(key):
    import frame_modules as FM
    return FM.spark_hammer_fn(2) if key == "spark" else FM.poker_fn(2)


def _flail(G, side, sh, el, w, s, P, A, S):
    """Кистень: the Guard's flail, in whichever hand."""
    import guard_modules as GM
    sub = Parts()
    GM.flail(sub, dict(w=arr(w) * arr((1, 1, s)), el=arr(el) * arr((1, 1, s))), 2)
    M = np.diag((1.0, 1.0, float(s)))
    for k_, m in sub.items():
        G[k_.replace("hand_n", "hand_" + side).replace("m_flail", "item_" + side)].extend(m.transformed(M, arr((0, 0, 0))))
    return dict(w=w)


# ---------------------------------------------------------------- legs
def heavy_leg(G, key, hipj, knee, ankle, s, P, th=1.0):
    """Опоры: thick legs, a riveted thigh guard, a spiked knee shield, a broad outrigger sole with claws front and
    back — it stands where it is put."""
    plain_leg(G, key, hipj, knee, ankle, s, P, th=th)
    g = G[key]
    hj, kn, an = arr(hipj), arr(knee), arr(ankle)
    block(g, lerp(hj, kn, 0.15), lerp(hj, kn, 0.75), (1.3 * th, 5.6 * th), (1.3 * th, 5.0 * th), P, off=(3.0 * th, 0, 0))
    rivets(g, [lerp(hj, kn, t) + arr((3.8 * th, 0, z)) for t in (0.3, 0.6) for z in (-1.6 * th, 1.6 * th)], r=0.35)
    g.ell(kn + (2.6 * th, 0.4, 0), (1.5 * th, 3.0 * th, 3.0 * th), M_IRON)                 # the knee shield
    spike(g, kn + (3.6 * th, 0.4, 0), kn + (5.8 * th, 0.8, 0), 0.6 * th, M_STEEL)
    g.box((an[0] + 1.0 * th, 0.55, an[2]), (11.0 * th, 1.1, 7.6 * th), M_DIRON)            # the outrigger sole
    g.box((an[0] + 1.0 * th, 1.2, an[2]), (8.0 * th, 0.4, 6.4 * th), P)
    for dz in (-2.6, 0.0, 2.6):
        spike(g, (an[0] + 6.2 * th, 0.8, an[2] + dz * th), (an[0] + 8.6 * th, 0.15, an[2] + dz * 1.3 * th), 0.6 * th, M_STEEL)
    for dz in (-1.8, 1.8):
        spike(g, (an[0] - 4.2 * th, 0.8, an[2] + dz * th), (an[0] - 6.2 * th, 0.15, an[2] + dz * 1.2 * th), 0.5 * th, M_STEEL)


def no_leg(G, key, hipj, knee, ankle, s, P, th=1.0):
    pass


def _legs(key):
    import frame_modules as FM
    return {"walk": (None, 1.0), "heavy": (heavy_leg, 1.35), "spider": (FM.spider_leg_fn(2, armour=True), 1.0),
            "tracks": (no_leg, 1.0), "mill": (FM.millstone_leg(2), 1.0)}[key]


LEGS = {"walk": "Шагающие", "heavy": "Опоры", "spider": "Паучьи лапы", "tracks": "Гусеницы", "mill": "Жернова"}


# ---------------------------------------------------------------- heads: lifted off their donors at the neck
HEADS = {"helm": ("Шлем", "Страж"), "hood": ("Капюшон с линзой", "Мудрец"), "stoker": ("Шлем кочегара", "Горн"),
         "range": ("Дальномер", "Орудие"), "lamp": ("Фонарь", "Механик")}
_NECK = {}


def neck(m):
    """The bottom of a head model: the middle of its lowest cells."""
    c = np.array(list(cells(m))) * STEP
    lo = c[:, 1].min()
    b = c[c[:, 1] < lo + 1.2]
    return arr((b[:, 0].mean(), lo, b[:, 2].mean()))


def head_model(key, P):
    donor = HULLS[HEADS[key][1]]
    G = Parts()
    donor["torso"](G, P, donor)
    return G["head"]


def hull_neck(name):
    if name not in _NECK:
        S = HULLS[name]
        G = Parts()
        S["torso"](G, Mat(S["paint"]), S)
        _NECK[name] = neck(G["head"])
    return _NECK[name]


# ---------------------------------------------------------------- the stock build of each hull
STOCK = {
    "Страж": dict(legs="walk", arm_n="maul", arm_f="shield", head="helm"),
    "Мудрец": dict(legs="walk", arm_n="staff", arm_f="focus", head="hood"),
    "Горн": dict(legs="walk", arm_n="flame", arm_f="tongs", head="stoker"),
    "Орудие": dict(legs="walk", arm_n="cannon", arm_f="cannon", head="range"),
    "Механик": dict(legs="walk", arm_n="wrench", arm_f="can", head="lamp"),
}
NEEDS = {"chain": "staff", "fireball": "staff", "ground": "staff", "long": "cannon", "canister": "cannon",
         "hotshot": "cannon", "buffer": "cannon", "bounce": "cannon", "tower": "shield", "counter": "shield"}
POOL = {   # the hulls' role modules (the Gun's spider legs became legs; the Buffer took their place)
    "Страж": ["tower", "intercept", "anchor", "plates", "counter", "hot"],
    "Мудрец": ["chain", "ground", "overload", "fireball", "firewall", "blades"],
    "Горн": ["magnet", "rod", "smoke", "whistle", "maw", "greedy"],
    "Орудие": ["mortar", "long", "buffer", "canister", "hotshot", "bomb"],
    "Механик": ["repair", "crane", "spares", "oiler", "welding", "oiltank"],
}


def spec(hull, legs=None, arm_n=None, arm_f=None, head=None):
    """The golems_h spec of a hull wearing these parts (the stock ones where not given)."""
    st = STOCK[hull]
    legs, arm_n, arm_f, head = legs or st["legs"], arm_n or st["arm_n"], arm_f or st["arm_f"], head or st["head"]
    S0 = HULLS[hull]
    S = dict(S0)
    lf, th = _legs(legs)
    if lf is not None:
        S["leg_fn"] = lf
    S["th_leg"] = S0["th_leg"] * th
    idle = dict(S0["poses"]["idle"])
    for side, s, key in (("n", 1, arm_n), ("f", -1, arm_f)):
        _, fn, pose = ARMS[key]
        S["item_" + side] = fn
        p = dict(pose)
        far = p.pop("far", None)
        if side == "f" and far:                        # held differently in the other hand (the guns: hip and shoulder)
            p.update(far)
        idle["hand_" + side] = tuple(np.array(p.pop("hand")) * (1, 1, s))
        idle["pole_" + side] = tuple(np.array(p.pop("pole")) * (1, 1, s))
        idle.update(p)
    if legs == "spider":                               # on spider legs the hands are carried up, out of the legs' way
        for side in ("n", "f"):
            h = np.array(idle["hand_" + side])
            idle["hand_" + side] = (h[0] + 2.0, max(h[1], -8.0), h[2])
    S.pop("two_hand", None)
    S.pop("after", None) if hull != "Механик" else None
    S["poses"] = dict(idle=idle)
    S["_parts"] = dict(hull=hull, legs=legs, arm_n=arm_n, arm_f=arm_f, head=head)
    return S


def assemble(hull, legs=None, arm_n=None, arm_f=None, head=None, core=None, mods=None, P=None):
    """The golem's model parts and where things are on it, as frame_modules.golem gives them, for the modules."""
    from augments import leg_joints
    import frame_modules as FM
    import guard_modules as GM
    S = spec(hull, legs, arm_n, arm_f, head)
    pr = S["_parts"]
    P = Mat(S["paint"]) if P is None else P
    A = dict(S["poses"]["idle"], fx=None)
    G, info = GH.creature_parts(S, A, P=P, fx=False)
    # the head: the hull's own off, the chosen one on at the hull's neck
    if pr["head"] != STOCK[hull]["head"]:
        hm = head_model(pr["head"], P)
        d = hull_neck(hull) - neck(hm)
        G["head"] = Parts()["head"]
        G["head"].extend(hm.transformed(I3, d))
    if pr["legs"] == "tracks":
        GM.tracks(G, None, 2)
    R = rot_z(A["lean"]) @ rot_y(A.get("twist", 0.0))
    X = GH.place_upper(Parts(), R, A["t"], hip=S["hip"], keys=())
    for side in ("n", "f"):
        sh = info["sh_" + side]
        el, w = GH.ik(sh, sh + arr(A["hand_" + side]), S["LU"], S["LF"], A["pole_" + side])
        info["el_" + side], info["w_" + side] = el, w
    info.update(S=S, A=A, X=X, R=R, legs=leg_joints(S, A), parts=pr)
    # what the Guard's modules look for: the near arm, the far arm, the shield in whichever hand holds it
    info.update(el=info["el_n"], w=info["w_n"], elf=info["el_f"], wf=info["w_f"], sh=info["sh_n"], fs=info["sh_f"])
    for side in ("n", "f"):
        if isinstance(info.get(side), dict) and "sc" in info[side]:
            info.update(sc=info[side]["sc"], R=info[side]["R"], fc=info[side]["fc"])
    for key, lv in (mods or {}).items():
        need = NEEDS.get(key)
        if need and need not in (pr["arm_n"], pr["arm_f"]):
            continue                                   # nothing for it to ride on
        rare = next((r for r in FM.RARE if r[0] == key), None)
        if rare:                                       # a rare module, any hull
            rare[4](G, info, lv)
        elif hull == "Страж":
            GM.MODULES[key][2](G, dict(info, R=info.get("R")), lv)
        else:
            FM.module(hull, key)[3](G, info, lv)
    if core:
        FM.core_fn(core)(G, info, 2)
    return G, info


def build(hull, k=None, pose="idle", **parts):
    """The sprite of a hull wearing these parts; k — its scale (the hull's battle scale by default)."""
    k = F.FRAMES[hull][0] if k is None else k
    G, _ = assemble(hull, **parts)
    cw, ch, cx, cy = HULLS[hull].get("canvas", (90, 84, 38, 74))
    cw, ch, cx, cy = cw + 40, ch + 16, cx + 14, cy + 6
    w, h, ox, oy = int(cw * k), int(ch * k), int(cx * k), int(cy * k)
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = ox, oy
    return spr


# ---------------------------------------------------------------- a part on its own, for its icon
PART_KEYS = {"head": ("head",), "legs": ("leg_n", "leg_n.ram", "leg_f", "leg_f.ram", "m_tracks"),
             "arm": ("arm_n", "arm_n.ram", "arm_n.ball", "hand_n", "item_n", "hammer", "shield", "bracket", "hose")}
DONOR = {"legs": "Орудие", "head": None, "arm": None}
_ICON = {}


def part_sprite(kind, key, px=16, hull=None):
    """The part alone, drawn as it is on a golem and fitted into a px×px square, outlined; kind — head, legs, arm."""
    ck = (kind, key, px, hull)
    if ck in _ICON:
        return _ICON[ck]
    if kind == "head":
        hull = hull or HEADS[key][1]
        G, _ = assemble(hull, head=key)
    elif kind == "legs":
        hull = hull or "Орудие"
        G, _ = assemble(hull, legs=key)
    else:
        hull = hull or "Орудие"
        G, _ = assemble(hull, arm_n=key, arm_f="fist")
    sub = Parts()
    for k_ in PART_KEYS[kind]:
        if k_ in G:
            sub[k_] = G[k_]
    if kind == "arm" and key == "flame":
        sub.pop("hose", None)
    m = sub.model()
    big = render(m.scaled(2.0), 300, 300, 150, 200, **STYLE1)
    ys, xs = np.nonzero(big.a)
    w0, h0 = (xs.max() - xs.min() + 1) / 2.0, (ys.max() - ys.min() + 1) / 2.0
    k = (px - 3) / max(w0, h0)
    cxm, cym = ((xs.max() + xs.min()) / 2 - 150) / 2.0, ((ys.max() + ys.min()) / 2 - 200) / 2.0
    spr = render(m.scaled(k), px, px, int(round(px / 2 - cxm * k)), int(round(px / 2 - cym * k)), **STYLE1)
    spr = rim_light(spr, col="#b8bcc6", k=0.55)
    spr.ox, spr.oy = 0, 0
    _ICON[ck] = spr
    return spr


def sheet():
    """Every part on the same hull, and mixed builds: the legs, the heads, the arms; then golems from several hulls."""
    from PIL import ImageFont
    from noise import value_noise
    from paths import font, out
    S_ = 2
    WW, HH = 960, 1060
    sc = Scene(WW, HH)
    n = value_noise(WW, HH, 14, 81) * 0.6 + value_noise(WW, HH, 5, 82) * 0.4
    th = BAYER[sc.yy % 4, sc.xx % 4]
    lv = np.clip(np.floor(n * 4 + (th - 0.5)), 0, 3).astype(int)
    for i, col in enumerate(("#221a28", "#261e2c", "#2a2130", "#2e2434")):
        sc.rgb[lv == i] = hexc(col)
    labels = []

    def row(y, items, kfac, step, x0=70, icons=None):
        for i, (hull, kw, lab) in enumerate(items):
            spr = build(hull, k=F.FRAMES[hull][0] * kfac, **kw)
            cx = x0 + i * step
            e = ((sc.xx - cx) / 40) ** 2 + ((sc.yy - y) / 6) ** 2
            sc.rgb[e <= 1] *= 0.62
            sc.blit(spr, int(cx - spr.ox), int(y - spr.oy))
            if icons:                                                   # the part alone, in its frame, beside it
                ic = part_sprite(icons[i][0], icons[i][1], 32)
                ix, iy = cx - step // 2 + 4, y - 120
                sc.rgb[iy - 2:iy + 34, ix - 2:ix + 34] = hexc("#14121a")
                sc.rgb[iy - 2, ix - 2:ix + 34] = hexc("#5a5860")
                sc.blit(ic, ix, iy)
            labels.append((cx, y + 6, lab))
    big = 1.25
    row(214, [("Орудие", dict(legs=k_), LEGS[k_] + (" · редкие" if k_ in RARE_PARTS else "")) for k_ in LEGS], big, 190,
        x0=110, icons=[("legs", k_) for k_ in LEGS])
    row(424, [("Орудие", dict(head=k_), HEADS[k_][0]) for k_ in HEADS], big, 190, x0=110,
        icons=[("head", k_) for k_ in HEADS])
    arms = list(ARMS)
    a1, a2 = arms[:7], arms[7:]
    alab = lambda k_: ARMS[k_][0] + (" · редкая" if k_ in RARE_PARTS else "")
    row(634, [("Орудие", dict(arm_n=k_, arm_f="fist"), alab(k_)) for k_ in a1], 1.1, 134, x0=74,
        icons=[("arm", k_) for k_ in a1])
    row(824, [("Орудие", dict(arm_n=k_, arm_f="fist"), alab(k_)) for k_ in a2], 1.1, 134, x0=74,
        icons=[("arm", k_) for k_ in a2])
    mixed = [("Страж", dict(legs="tracks", arm_n="cannon", arm_f="cannon", head="range"), "Страж · гусеницы, две пушки"),
             ("Мудрец", dict(legs="heavy", arm_n="maul", arm_f="shield", head="helm"), "Мудрец · опоры, молот, щит"),
             ("Горн", dict(legs="spider", arm_n="flame", arm_f="flame", head="stoker"), "Горн · лапы, два огнемёта"),
             ("Орудие", dict(legs="mill", arm_n="flail", arm_f="tongs", head="lamp"), "Орудие · жернова, кистень"),
             ("Механик", dict(legs="heavy", arm_n="staff", arm_f="wrench", head="hood"), "Механик · посох, ключ")]
    row(1014, mixed, 1.0, 190, x0=110)
    img = sc.image(S_)
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(font("PTSerif-Bold.ttf"), 28)
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 20)
    fr = ImageFont.truetype(font("PTSerif-Regular.ttf"), 15)
    d.text((24, 12), "Голем из деталей: корпус, ноги, руки, голова", font=ft, fill=(236, 226, 200))
    d.text((24, 50), "Ноги, руки и головы общие — встают на любой корпус. Корпус задаёт роль, размер, свою пассивку и ячейки модулей.",
           font=fr, fill=(190, 182, 164))
    for y, t in ((44, "НОГИ"), (254, "ГОЛОВЫ"), (464, "РУКИ · в правой руке"), (850, "СБОРКИ · разные корпуса")):
        d.text((24, y * S_), t, font=fh, fill=(226, 186, 106))
    for cx, y, lab in labels:
        for j, ln in enumerate(lab.split(" · ")):
            d.text((cx * S_ - d.textlength(ln, font=fr) / 2, y * S_ + j * 18), ln, font=fr,
                   fill=(214, 206, 186) if j == 0 else (170, 160, 140))
    img.save(out("golem_parts.png"))
    print("golem_parts.png", img.size)


if __name__ == "__main__":
    import sys
    from paths import out
    if len(sys.argv) == 1:
        sheet()
        sys.exit()
    hull = sys.argv[1]
    sc = Scene(960, 300)
    sc.rgb[:] = hexc("#1c1a22")
    x = 60
    for kw in (dict(), dict(legs="heavy"), dict(legs="spider"), dict(legs="tracks"), dict(head="hood"),
               dict(head="lamp"), dict(arm_n="maul", arm_f="shield"), dict(arm_n="staff", arm_f="tongs")):
        spr = build(hull, k=1.6, **kw)
        sc.blit(spr, int(x - spr.ox), int(260 - spr.oy))
        x += 112
    sc.image(2).save(out("golem_parts_check.png"))
    print("golem_parts_check.png")
