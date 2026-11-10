"""Modules going off in battle, on the battlefield's own grid (cells of 50 × 34 pixels): the Sage's spells, the
Gorn's breath and magnet, the Gun's mortar, canister and bombs, the Mechanic's oil, the Guard's anchor, rare
modules. The golem wears the module; the effect is built in the golem's own 3D space, on world points worked out
from screen cells, and drawn with the golem; the enemies are the swarm's sprites standing in their cells.

    python3 tools/sprites/effects.py              -> out/effects_<frame>.gif for every frame, out/effects.png (key frames)
    python3 tools/sprites/effects.py Мудрец       -> just one
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from kit import *
from r3d import Model, Mat, render, rot_y, rot_z, rot_x, YAW, SA, CA
import golems_h as GH
import frame_modules as FM
import guard_modules as GM
import humanoid as HM
import swarm1 as W
from golems_h import arr, unit, lerp, sparks, puffs, ENERGY, ARC, M_PUFF, STYLE1
from frame_modules import FLAME, HOT, COAL, STEAM, OIL
from leaders_h import zigzag
from battle import put, shadow, flash
from animate_duel import background, halo
from paths import font, out

CW, CH = 50, 34                     # a battlefield cell on screen
K = {"Мудрец": 1.6, "Горн": 1.6, "Орудие": 1.6, "Механик": 1.15, "Страж": 2.2}
SMOKE = Mat(ramp("#2a2830", "#46444e", "#6a6874", "#908e9a", "#b8b6c2"), dither=True)
DUST = Mat(ramp("#3a3230", "#5a504a", "#7e726a", "#a49890", "#c8beb4"), dither=True)
STUN = Mat(ramp("#2a6a8a", "#4aa8d0", "#8ad8f0", "#c8f2ff", "#ffffff"), emissive=hexc("#70e0ff"), glow_r=5, glow_k=0.5)
MAGNET = Mat(ramp("#0e2a6a", "#1a50b0", "#3a8ae8", "#90c8ff", "#e0f0ff"), emissive=hexc("#5aa0ff"), glow_r=4, glow_k=0.4)


class Field:
    """Screen cells ↔ world points, at the golem's scale k; the golem stands in cell (0, 0)."""

    def __init__(self, k):
        self.k = k
        self.Rinv = rot_y(YAW).T

    def w(self, dc, dr, h=0.0):
        """The world point over the centre of cell (dc, dr), h units up."""
        q = arr((dc * CW / self.k, 0.0, dr * CH / (self.k * SA)))
        return self.Rinv @ q + arr((0, h, 0))


def soldier(seed=7):
    return W.build((), 0.02, "idle", True, k=1.0, genes=W.genes_for(seed))


def tint(spr, col, k):
    f = Sprite(spr.w, spr.h)
    f.rgb, f.a = spr.rgb * (1 - k) + np.array(hexc(col), float) * k, spr.a.copy()
    f.ox, f.oy = spr.ox, spr.oy
    return f


# ---------------------------------------------------------------- the golem wearing its module
def frame_golem(frame, levels, pose="idle", A=None):
    S = GH.BY_NAME[frame]
    A = dict(S["poses"][pose], fx=None) if A is None else A
    G, info, _ = FM.golem(frame, A=A)
    for key, t in levels.items():
        FM.module(frame, key)[3](G, info, t)
    return G, info


# ---------------------------------------------------------------- effect helpers (world space)
def bolt(fx, a, b, seed, r=0.35, amp=1.2, n=8):
    zigzag(fx, a, b, n=n, amp=amp, seed=seed, r=r, mat=ARC)
    fx.ell(b, (1.6, 1.6, 1.6), ENERGY)


def flames(fx, c, size=1.0, n=4, seed=0):
    rnd = np.random.RandomState(seed)
    for i in range(n):
        o = arr((rnd.uniform(-4.0, 4.0), 0.0, rnd.uniform(-4.0, 4.0))) * size
        h = rnd.uniform(3.6, 6.4) * size
        fx.ell(c + o + arr((0, h * 0.6, 0)), (2.0 * size, h * 0.7, 2.0 * size), FLAME)
        fx.ell(c + o + arr((0.4, h * 1.3, 0)), (1.0 * size, h * 0.4, 1.0 * size), FLAME)


def blast(fx, c, R, seed=0):
    """An explosion: a fireball, a ring of fire on the ground, dust and flying bits."""
    fx.ell(c + arr((0, R * 0.5, 0)), (R * 0.75, R * 0.6, R * 0.75), FLAME)
    fx.ell(c + arr((0, R * 0.45, 0)), (R * 0.4, R * 0.35, R * 0.4), COAL)
    fx.ell(c + arr((0, 0.3, 0)), (R * 1.25, 0.4, R * 1.25), Mat(EMBER, emissive=hexc("#ff7a28"), glow_r=5, glow_k=0.4))
    puffs(fx, c + arr((0, R * 0.9, 0)), n=3, r=R * 0.35, spread=R * 0.6, seed=seed)
    sparks(fx, c + arr((0, R * 0.5, 0)), n=8, spread=R * 0.6, seed=seed + 1, big=True)


def ring(fx, c, R, mat, n=18, r=0.3, h=0.4):
    pts = [c + arr((np.cos(a) * R, h, np.sin(a) * R * 0.95)) for a in np.linspace(0, 2 * np.pi, n + 1)]
    for p, q in zip(pts[:-1], pts[1:]):
        fx.cyl(p, q, r, mat, seg=4)


# ---------------------------------------------------------------- the effects: each a list of frames
# a frame: dict(G=(parts, info) builder, fx=fn(fx, info, F), enemies=[(dc, dr, state)], allies=[...], dur)
def e_chain():
    """Цепная молния: from the staff into the first enemy, then on to two more."""
    L = {"chain": 1}
    es = [(3, 0), (4, -1), (4.4, 0.9)]
    def fr(step, dur):
        def fx(f, info, F):
            tip = info["n"]["tip"]
            pts = [tip] + [F.w(dc, dr, 9.0) for dc, dr in es]
            for i in range(min(step, 3)):
                bolt(f, pts[i], pts[i + 1], seed=10 + i, amp=1.4 if i == 0 else 1.0)
            for i in range(min(step, 3) - 1):
                sparks(f, pts[i + 1], n=4, spread=2.0, seed=20 + i, big=False)
        st = ["hit" if i == step - 1 else ("stun" if i < step - 1 else "") for i in range(3)]
        return dict(G=lambda: frame_golem("Мудрец", L, "attack"), fx=fx, enemies=[(dc, dr, s) for (dc, dr), s in zip(es, st)], dur=dur)
    return [dict(G=lambda: frame_golem("Мудрец", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=380),
            fr(1, 140), fr(2, 120), dict(fr(3, 160), key=True), fr(4, 260)]


def e_fireball():
    """Огненный шар: the ball flies five cells, bursts on a cell and its neighbours and sets them alight."""
    L = {"fireball": 2}
    tgt = (4, 0)
    es = [(4, 0), (4, -1), (5, 0), (3.8, 1)]
    def fly(s, dur):
        def fx(f, info, F):
            a, b = info["n"]["tip"], F.w(*tgt, 6.0)
            p = lerp(a, b, s) + arr((0, 10.0 * np.sin(np.pi * s), 0))
            f.ell(p, (3.4, 3.4, 3.4), FLAME)
            f.ell(p, (1.7, 1.7, 1.7), COAL)
        return dict(G=lambda: frame_golem("Мудрец", L, "attack"), fx=fx, enemies=[(dc, dr, "") for dc, dr in es], dur=dur)
    def boom(fx_, f, info, F):
        blast(f, F.w(*tgt), 16.0, seed=3)
        for dc, dr in ((4, -1), (5, 0), (3, 0), (4, 1)):
            flames(f, F.w(dc, dr), size=1.6, n=4, seed=dc * 7 + dr)
    def burn(f, info, F):
        for dc, dr in es:
            flames(f, F.w(dc, dr), size=1.2, n=4, seed=int(dc * 11 + dr * 3))
    return [dict(G=lambda: frame_golem("Мудрец", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=360),
            fly(0.15, 90), fly(0.5, 90), fly(0.85, 90),
            dict(G=lambda: frame_golem("Мудрец", L, "attack"), fx=lambda f, i, F: boom(None, f, i, F),
                 enemies=[(dc, dr, "hit") for dc, dr in es], dur=200, key=True),
            dict(G=lambda: frame_golem("Мудрец", L), fx=burn, enemies=[(dc, dr, "burn") for dc, dr in es], dur=320)]


def e_firewall():
    """Огненная стена: a wall of fire three cells long rises in front of the line and burns for three rounds."""
    L = {"firewall": 2}
    es = [(3, -1), (3.2, 0.2), (3, 1), (2, 0)]
    def wall(h, dur, st):
        def fx(f, info, F):
            rnd = np.random.RandomState(int(h))
            for dr in (-1, 0, 1):
                for j in range(6):
                    c = F.w(2 + rnd.uniform(-0.25, 0.25), dr + (j - 2.5) * 0.17)
                    hh = h * rnd.uniform(0.75, 1.15)
                    f.ell(c + arr((0, hh * 0.55, 0)), (5.0, hh * 0.6, 4.0), FLAME)
                    f.ell(c + arr((0.6, hh * 1.2, 0)), (2.4, hh * 0.4, 2.0), FLAME)
                f.ell(F.w(2, dr, 0.3), (9.0, 0.4, 7.0), Mat(EMBER, emissive=hexc("#ff7a28"), glow_r=5, glow_k=0.4))
            if h > 6:
                puffs(f, F.w(2, 0, h + 4), n=2, r=2.0, spread=4.0, seed=4)
        return dict(G=lambda: frame_golem("Мудрец", L, "attack"), fx=fx, enemies=[(dc, dr, s) for (dc, dr), s in zip(es, st)], dur=dur)
    return [dict(G=lambda: frame_golem("Мудрец", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=360),
            wall(3.0, 110, ["", "", "", "hit"]), wall(6.0, 110, ["", "", "", "burn"]), dict(wall(9.0, 300, ["", "", "", "burn"]), key=True)]


def e_ground():
    """Разряд в землю: lightning runs out along the ground from the stakes and stuns everyone round it."""
    L = {"ground": 2}
    es = [(1, 0), (1, -1), (0.2, 1), (-0.8, -0.9)]
    def fx_(f, info, F):
        for i, (dc, dr) in enumerate(es):
            bolt(f, F.w(0, 0, 0.6), F.w(dc, dr, 4.0), seed=40 + i, r=0.3, amp=1.0, n=6)
        ring(f, F.w(0, 0), 22.0, STUN, r=0.45)
        ring(f, F.w(0, 0), 12.0, STUN, r=0.35)
    def after(f, info, F):
        for i, (dc, dr) in enumerate(es):
            sparks(f, F.w(dc, dr, 7.0), n=3, spread=1.6, seed=50 + i, big=False)
    return [dict(G=lambda: frame_golem("Мудрец", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=380),
            dict(G=lambda: frame_golem("Мудрец", L), fx=fx_, enemies=[(dc, dr, "hit") for dc, dr in es], dur=180, key=True),
            dict(G=lambda: frame_golem("Мудрец", L), fx=after, enemies=[(dc, dr, "stun") for dc, dr in es], dur=320)]


def e_overload():
    """Перегрузка: an arc from the jars on the shoulder into a neighbouring golem — it hits twice as hard."""
    L = {"overload": 2}
    ally = (1, -1)
    def fx_(f, info, F, strong):
        jar = FM.shoulder_top(*info["_Gs"], dx=-1.4, dz=0.6) + arr((0, 5.0, 0))
        bolt(f, jar, F.w(*ally, 26.0), seed=60, r=0.35, amp=1.2)
        if strong:
            f.ell(F.w(*ally, 26.0), (3.0, 3.0, 3.0), ENERGY)
    return [dict(G=lambda: frame_golem("Мудрец", L), fx=None, allies=[(*ally, "")], dur=380),
            dict(G=lambda: frame_golem("Мудрец", L), fx=lambda f, i, F: fx_(f, i, F, False), allies=[(*ally, "volt")], dur=160),
            dict(G=lambda: frame_golem("Мудрец", L), fx=lambda f, i, F: fx_(f, i, F, True), allies=[(*ally, "volt2")], dur=320, key=True)]


def e_maw():
    """Пасть топки: the Gorn breathes fire from its chest two cells ahead."""
    L = {"maw": 3}
    es = [(1, 0), (2, 0), (2, -0.8), (1.8, 0.9)]
    def breath(reach, dur, st):
        def fx(f, info, F):
            a = F.w(0, 0, 26.0) + arr((8.0, 0, 2.0))
            for i in range(9):
                s = (i + 1) / 9 * reach
                c = lerp(a, F.w(2.2, 0, 8.0), s)
                f.ell(c, (2.4 + 8.0 * s, 2.0 + 5.0 * s, 2.4 + 8.0 * s), FLAME)
                if i % 3 == 1:
                    f.ell(c, (1.2 + 3.0 * s, 1.0 + 2.0 * s, 1.2 + 3.0 * s), COAL)
        return dict(G=lambda: frame_golem("Горн", L, "attack"), fx=fx, enemies=[(dc, dr, s) for (dc, dr), s in zip(es, st)], dur=dur)
    return [dict(G=lambda: frame_golem("Горн", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=380),
            breath(0.5, 110, ["hit", "", "", ""]), dict(breath(1.0, 200, ["burn", "hit", "hit", "hit"]), key=True),
            dict(G=lambda: frame_golem("Горн", L), fx=None, enemies=[(dc, dr, "burn") for dc, dr in es], dur=320)]


def e_magnet():
    """Магнит: blue waves from the magnet pull the enemies within three cells to it."""
    L = {"magnet": 2}
    start = [(3, 0), (3, -1), (2.6, 1)]
    end = [(1.1, 0), (1.2, -0.9), (1.0, 0.8)]
    def fr(s, dur, waves):
        def fx(f, info, F):
            c = FM.shoulder_top(*info["_Gs"], dx=-0.8, dz=0.6) + arr((2.0, 2.0, 0))
            sx = F.Rinv @ arr((1.0, 0, 0))                         # across the screen, towards the enemies
            for i in range(waves):
                R = 12.0 + i * 16.0
                pts = [c + sx * np.cos(a) * R + arr((0, np.sin(a) * R * 0.75, 0)) for a in np.linspace(-1.0, 1.0, 13)]
                for p, q in zip(pts[:-1], pts[1:]):
                    f.cyl(p, q, 0.8, MAGNET, seg=4)
        es = [(a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s, "pull" if 0 < s < 1 else "") for a, b in zip(start, end)]
        return dict(G=lambda: frame_golem("Горн", L), fx=fx, enemies=es, dur=dur)
    return [fr(0.0, 380, 0), fr(0.33, 110, 1), dict(fr(0.66, 110, 2), key=True), fr(1.0, 300, 3)]


def e_whistle():
    """Паровой свисток: a shriek of steam — rings run out over the ground, the enemies within two cells cower."""
    L = {"whistle": 3}
    es = [(1, 0), (2, -1), (1.8, 1)]
    def fr(n, dur, st):
        def fx(f, info, F):
            base = FM.shoulder_top(*info["_Gs"], dx=-1.0, dz=0.4)
            for i in range(3):
                f.ell(base + arr(((i - 1) * 0.6, 10.0 + i * 2.0, (i - 1) * 2.0)), (2.8, 5.0, 2.8), STEAM)
            for i in range(n):
                ring(f, F.w(0, 0), 14.0 + i * 12.0, Mat(ramp("#8e8e96", "#b4b4bc", "#d6d6dc", "#f4f4f8", "#ffffff")), r=0.3)
        return dict(G=lambda: frame_golem("Горн", L), fx=fx, enemies=[(dc, dr, s) for (dc, dr), s in zip(es, st)], dur=dur)
    return [dict(G=lambda: frame_golem("Горн", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=380),
            fr(1, 120, ["fear", "", ""]), dict(fr(2, 300, ["fear", "fear", "fear"]), key=True)]


def e_smoke():
    """Дымовая труба: the stacks fill the cells round it with smoke; shooters miss into it."""
    L = {"smoke": 3}
    cells = [(1, 0), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (-1, -1), (-1, 1)]
    def fr(n, dur):
        def fx(f, info, F):
            for i, (dc, dr) in enumerate(cells[:n]):
                c = F.w(dc, dr, 8.0)
                f.ell(c, (13.0, 8.0, 11.0), SMOKE)
                f.ell(c + arr((3.0, 8.0, 1.6)), (9.0, 6.0, 8.0), SMOKE)
        return dict(G=lambda: frame_golem("Горн", L), fx=fx, enemies=[(3, 0, "")], dur=dur)
    return [fr(0, 380), fr(3, 120), fr(6, 120), dict(fr(8, 320), key=True)]


def e_mortar():
    """Мортира: the shell goes up from the back, comes down on a cell and its neighbours; the recoil rocks it."""
    L = {"mortar": 2}
    tgt = (4, 0)
    es = [(4, 0), (4, -1), (3.6, 1), (4.8, 0.4)]
    def fly(s, dur):
        def fx(f, info, F):
            lo, hi = FM.box_of(info["_Gs"][0], "back")
            a = arr(((lo[0] + hi[0]) / 2, hi[1] + 9.0, 0))
            b = F.w(*tgt, 2.0)
            p = lerp(a, b, s) + arr((0, 40.0 * np.sin(np.pi * s), 0))
            f.ell(p, (1.3, 1.3, 1.3), Mat(ramp("#08080a", "#141418", "#22222a", "#34343e", "#4c4c58")))
            if s < 0.3:
                puffs(f, a, n=3, r=2.0, spread=2.6, seed=7)
                f.ell(a, (1.8, 1.8, 1.8), FLAME)
        return dict(G=lambda: frame_golem("Орудие", L), fx=fx, enemies=[(dc, dr, "") for dc, dr in es], dur=dur)
    def boom(f, info, F):
        blast(f, F.w(*tgt), 16.0, seed=9)
        for dc, dr in ((4, -1), (3, 0), (5, 0), (4, 1)):
            f.ell(F.w(dc, dr, 3.0), (8.0, 4.0, 7.0), DUST)
    return [dict(G=lambda: frame_golem("Орудие", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=360),
            fly(0.1, 110), fly(0.45, 100), fly(0.85, 100),
            dict(G=lambda: frame_golem("Орудие", L), fx=boom, enemies=[(dc, dr, "hit") for dc, dr in es], dur=320, key=True)]


def e_canister():
    """Картечь: an enemy right against it — a cone of shot point blank, into everyone in front."""
    L = {"canister": 2}
    es = [(1, 0), (1, -0.9), (1, 0.9)]
    def fx_(f, info, F):
        c = info["n"]
        m, d = c["muzzle"] + c["d"] * 2.8, c["d"]
        f.ell(m, (2.4, 2.4, 2.4), FLAME)
        rnd = np.random.RandomState(5)
        for i in range(22):
            q = F.w(1, rnd.uniform(-1.2, 1.2), rnd.uniform(4.0, 16.0)) + arr((rnd.uniform(-3, 3), 0, rnd.uniform(-3, 3)))
            p = lerp(m, q, rnd.uniform(0.55, 0.95))
            f.cyl(p, p + unit(q - m) * 1.2, 0.2, Mat(ramp("#3a3a3a", "#6a6a6a", "#a8a8a8", "#dcdcdc", "#ffffff")), seg=3)
        puffs(f, m + d * 2.0, n=2, r=2.0, spread=2.0, seed=6)
    L_A = GH.ORUDIE["poses"]["attack_level"]
    return [dict(G=lambda: frame_golem("Орудие", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=380),
            dict(G=lambda: frame_golem("Орудие", L, "attack_level"), fx=fx_, enemies=[(dc, dr, "hit") for dc, dr in es], dur=200, key=True),
            dict(G=lambda: frame_golem("Орудие", L, "attack_level"), fx=None, enemies=[(dc + 0.3, dr, "") for dc, dr in es], dur=300)]


def e_long():
    """Длинный ствол: the shot goes through the whole line to the farthest enemy."""
    L = {"long": 3}
    es = [(2, 0), (3, 0), (4.2, 0), (5.4, 0)]
    def fx_(f, info, F):
        c = info["n"]
        m = c["muzzle"] + c["d"] * 12.0
        end = F.w(5.8, 0, 12.0)
        f.cyl(m, end, 0.35, Mat(ramp("#7a5a20", "#c09040", "#f0c060", "#fff0b0", "#ffffff"), emissive=hexc("#ffd080"), glow_r=4, glow_k=0.4), seg=5)
        f.ell(m, (2.0, 2.0, 2.0), FLAME)
        for i, (dc, dr) in enumerate(es):
            sparks(f, F.w(dc, dr, 10.0), n=4, spread=1.6, seed=70 + i, big=False)
    return [dict(G=lambda: frame_golem("Орудие", L), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=380),
            dict(G=lambda: frame_golem("Орудие", L, "attack_level"), fx=fx_, enemies=[(dc, dr, "hit") for dc, dr in es], dur=220, key=True),
            dict(G=lambda: frame_golem("Орудие", L, "attack_level"), fx=None, enemies=[(dc, dr, "") for dc, dr in es[:-1]], dur=300)]


def e_bomb():
    """Бомба с фитилём: a bomb lies on a cell, its fuse hissing for two rounds, then it goes off."""
    L = {"bomb": 3}
    cell = (2, 0)
    es = [(2.6, -0.6), (2.4, 0.8), (3, 0)]
    def lying(n, dur):
        def fx(f, info, F):
            c = F.w(*cell, 1.6)
            f.ell(c, (1.8, 1.8, 1.8), Mat(ramp("#08080a", "#141418", "#22222a", "#34343e", "#4c4c58")))
            f.cyl(c + arr((0, 1.6, 0)), c + arr((0.6, 2.2 + n * 0.6, 0.2)), 0.16, FM.ROPE, seg=3)
            sparks(f, c + arr((0.7, 2.4 + n * 0.6, 0.2)), n=4, spread=1.0, seed=n, big=False)
        return dict(G=lambda: frame_golem("Орудие", L), fx=fx, enemies=[(dc, dr, "") for dc, dr in es], dur=dur)
    return [lying(2, 300), lying(1, 300), lying(0, 200),
            dict(G=lambda: frame_golem("Орудие", L), fx=lambda f, i, F: blast(f, F.w(*cell), 17.0, seed=11),
                 enemies=[(dc, dr, "hit") for dc, dr in es], dur=200, key=True),
            dict(G=lambda: frame_golem("Орудие", L), fx=lambda f, i, F: [flames(f, F.w(dc, dr), 1.2, 4, seed=int(dc * 9 + dr)) for dc, dr in es],
                 enemies=[(dc, dr, "burn") for dc, dr in es], dur=320)]


def e_oiltank():
    """Масляный бак: a spray of oil over the nearest enemy — fire will burn it twice as hard."""
    L = {"oiltank": 3}
    es = [(2, 0)]
    def fx_(f, info, F, s):
        a = arr((4.0, 34.0, 14.0))
        b = F.w(2, 0, 8.0)
        for i in range(8):
            t = (i + 1) / 8 * s
            f.ell(lerp(a, b, t) + arr((0, 4.0 * np.sin(np.pi * t), 0)), (1.6, 1.3, 1.3), OIL)
        if s >= 1:
            f.ell(F.w(2, 0, 0.3), (12.0, 0.4, 9.0), OIL)
            for i in range(5):
                f.ell(F.w(2, 0, 12.0 - i * 2.4) + arr((1.6 * (i % 2), 0, 0.8)), (1.0, 1.4, 1.0), OIL)
    return [dict(G=lambda: frame_golem("Механик", L), fx=None, enemies=[(2, 0, "")], dur=380),
            dict(G=lambda: frame_golem("Механик", L), fx=lambda f, i, F: fx_(f, i, F, 0.6), enemies=[(2, 0, "")], dur=120),
            dict(G=lambda: frame_golem("Механик", L), fx=lambda f, i, F: fx_(f, i, F, 1.0), enemies=[(2, 0, "oil")], dur=320, key=True)]


def e_anchor():
    """Якорь: the Guard drives its claws into the ground: cracks run out, the front of three cells is held."""
    def G_(t):
        return lambda: (GM.parts(["anchor"], 3)[0], dict(_guard=True))
    es = [(2, -1), (2.2, 0), (2, 1)]
    def fx_(f, info, F, n):
        for dr in (-1, 0, 1):
            c = F.w(1, dr, 0.3)
            for i in range(n):
                a = 0.8 * i + dr
                f.cyl(c, c + arr((np.cos(a) * 6.0, 0, np.sin(a) * 6.0)), 0.3, Mat(ramp("#060408", "#0e0a10", "#18121c", "#221a26", "#2c2230")), seg=3)
            f.ell(c + arr((0, 1.0, 0)), (5.0, 1.4, 4.0), DUST)
    return [dict(G=G_(3), fx=None, enemies=[(dc, dr, "") for dc, dr in es], dur=380),
            dict(G=G_(3), fx=lambda f, i, F: fx_(f, i, F, 2), enemies=[(dc, dr, "") for dc, dr in es], dur=150),
            dict(G=G_(3), fx=lambda f, i, F: fx_(f, i, F, 4), enemies=[(dc + 0.25, dr, "blocked") for dc, dr in es], dur=320, key=True)]


def e_whirl():
    """Огненный смерч: three burning cells become a whirlwind of fire that wanders towards the enemy."""
    L = {}
    es = [(3, 0), (3.6, -1), (4, 0.8)]
    def fr(pos, h, dur, st):
        def fx(f, info, F):
            c = F.w(*pos)
            for i in range(18):
                a = i * 0.8
                r = 2.5 + i * 0.6
                f.ell(c + arr((np.cos(a) * r, i * h / 18, np.sin(a) * r)), (2.6, 2.0, 2.6), FLAME)
            f.ell(c + arr((0, 0.3, 0)), (9.0, 0.4, 7.0), Mat(EMBER, emissive=hexc("#ff7a28"), glow_r=5, glow_k=0.4))
        return dict(G=lambda: frame_golem("Горн", {}), fx=fx, enemies=[(dc, dr, s) for (dc, dr), s in zip(es, st)], dur=dur,
                    rare=("whirl", 3))
    return [fr((2, 0), 12.0, 300, ["", "", ""]), fr((2.5, 0), 22.0, 200, ["", "", ""]), dict(fr((3, 0), 30.0, 200, ["burn", "hit", ""]), key=True),
            fr((3.5, -0.4), 30.0, 300, ["burn", "burn", "hit"])]


def e_bounce():
    """Скачущее ядро: the red-hot ball bounces from enemy to enemy three times and sets each alight."""
    es = [(2, 0), (3, -1), (4, 0.6)]
    def fr(n, dur):
        def fx(f, info, F):
            pts = [info["n"]["muzzle"]] + [F.w(dc, dr, 8.0) for dc, dr in es]
            for i in range(n):
                a, b = pts[i], pts[i + 1]
                for j in range(6):
                    t = (j + 0.5) / 6
                    f.ell(lerp(a, b, t) + arr((0, 8.0 * np.sin(np.pi * t), 0)), (0.8, 0.8, 0.8), Mat(EMBER, emissive=hexc("#ff7a28"), glow_r=3, glow_k=0.3))
            if n:
                f.ell(pts[n], (2.6, 2.6, 2.6), HOT)
            for i in range(1, n):
                flames(f, F.w(*es[i - 1]), 0.7, 2, seed=i)
        st = ["burn" if i < n - 1 else ("hit" if i == n - 1 else "") for i in range(3)]
        return dict(G=lambda: frame_golem("Орудие", {}, "attack_level"), fx=fx, enemies=[(dc, dr, s) for (dc, dr), s in zip(es, st)],
                    dur=dur, rare=("bounce", 2))
    return [fr(0, 300), fr(1, 140), fr(2, 140), dict(fr(3, 300), key=True)]


def e_grapple():
    """Крюк-кошка: the hook catches an enemy in the second row and pulls it up to the golem."""
    def fr(pos, out_, dur, st):
        def fx(f, info, F):
            a = FM.shoulder_top(*info["_Gs"], dx=-0.6, dz=1.0) + arr((5.0, 1.6, 0))
            if out_:
                b = F.w(*pos, 9.0)
                n = int(np.linalg.norm(b - a) / 1.0)
                for i in range(n):
                    f.ell(lerp(a, b, (i + 0.5) / n), (0.6, 0.6, 0.6) if i % 2 else (0.8, 0.5, 0.5), FM.CHAIN)
                hk = Mat(ramp("#1e2228", "#3a404a", "#606874", "#949ca8", "#d0d6de"))
                d = unit(b - a)
                for v in (arr((0, 1.0, 0)), arr((0, -1.0, 0)), arr((0, 0, 1.0))):
                    f.cyl(b, b + d * 1.6 + v * 1.8, 0.45, hk, seg=4)
        return dict(G=lambda: frame_golem("Механик", {}), fx=fx, enemies=[(pos[0], pos[1], st)], dur=dur, rare=("grapple", 2))
    return [fr((3, 0), False, 300, ""), fr((3, 0), True, 160, "hit"), dict(fr((2, 0), True, 120, "pull"), key=True), fr((1.1, 0), True, 300, "")]


keys = {}
EFFECTS = {
    "Мудрец": [("Цепная молния", e_chain), ("Огненный шар", e_fireball), ("Огненная стена", e_firewall),
               ("Разряд в землю", e_ground), ("Перегрузка", e_overload)],
    "Горн": [("Пасть топки", e_maw), ("Магнит", e_magnet), ("Паровой свисток", e_whistle), ("Дымовая труба", e_smoke)],
    "Орудие": [("Мортира", e_mortar), ("Картечь", e_canister), ("Длинный ствол", e_long), ("Бомба с фитилём", e_bomb)],
    "Механик": [("Масляный бак", e_oiltank)],
    "Страж": [("Якорь", e_anchor)],
    "редкие": [("Огненный смерч", e_whirl), ("Скачущее ядро", e_bounce), ("Крюк-кошка", e_grapple)],
}
OWNER = {"Огненный смерч": "Горн", "Скачущее ядро": "Орудие", "Крюк-кошка": "Механик"}


# ---------------------------------------------------------------- drawing
def render_frame(spec, frame, PW=420, PH=230, gx=110, gy=170, seed=95):
    k = K[frame]
    F = Field(k)
    built = spec["G"]()
    G, info = built if isinstance(built, tuple) else (built, {})
    if "_guard" not in info:
        info["_Gs"] = (G, info)
        if spec.get("rare"):
            key, t = spec["rare"]
            next(r for r in FM.RARE if r[0] == key)[4](G, info, t)
    if spec.get("fx"):
        spec["fx"](G["fx"], info, F)
    w, h, ox, oy = PW, PH, gx, gy
    spr = rim_light(render(G.model().scaled(k), w, h, ox, oy, **STYLE1), col="#b8bcc6", k=0.55)
    sc = Scene(PW, PH)
    sc.rgb[:] = background(PW, PH, seed).rgb
    for c in range(-2, 8):                                   # the grid, faintly
        x = gx + int((c - 0.5) * CW)
        if 0 <= x < PW:
            sc.rgb[:, x] *= 0.9
    for r in range(-3, 3):
        y = gy + int((r + 0.5) * CH)
        if 0 <= y < PH:
            sc.rgb[y, :] *= 0.9
    shadow(sc, gx + 4, gy, 46 * k / 1.6, 9)
    bug = soldier()
    items = []
    for dc, dr, st in spec.get("enemies", []):
        x, y = gx + dc * CW, gy + dr * CH
        b = bug
        if st == "hit":
            b = flash(bug, 0.7)
        elif st == "burn":
            b = tint(bug, "#ff8a30", 0.35)
        elif st == "stun":
            b = tint(bug, "#70e0ff", 0.4)
        elif st == "oil":
            b = tint(bug, "#0a0806", 0.55)
        elif st == "fear":
            b, x = tint(bug, "#d8d0f0", 0.25), x + 6
        elif st == "pull":
            b = tint(bug, "#5aa0ff", 0.3)
        items.append((y, lambda b=b, x=x, y=y: (shadow(sc, x - 2, y, 30, 6), put(sc, b, int(x), int(y), mirror=True))))
    for dc, dr, st in spec.get("allies", []):
        x, y = gx + dc * CW, gy + dr * CH
        a = HM.build("idle", 2.2)
        if st == "volt":
            a = tint(a, "#70e0ff", 0.25)
        elif st == "volt2":
            a = tint(a, "#70e0ff", 0.4)
        items.append((y, lambda a=a, x=x, y=y: (shadow(sc, x + 4, y, 60, 9), put(sc, a, int(x), int(y)))))
    for y, draw in sorted(items, key=lambda t: t[0]):
        if y <= gy:
            draw()
    halo(sc, spr, 0, 0)
    sc.blit(spr, 0, 0)
    for y, draw in sorted(items, key=lambda t: t[0]):
        if y > gy:
            draw()
    return sc


def effect_gif(frame, SC=2):
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 20)
    ft_ = ImageFont.truetype(font("PTSerif-Bold.ttf"), 24)
    panels = []
    for name, fn in EFFECTS[frame]:
        seq = fn()
        who = OWNER.get(name, frame)
        imgs = [render_frame(s, who).image(1) for s in seq]
        panels.append((name, imgs, [s["dur"] for s in seq]))
        keys[name] = next((i for i, s in enumerate(seq) if s.get("key")), len(seq) * 2 // 3)
    n = max(len(p[1]) for p in panels)
    PW, PH = panels[0][1][0].size
    cols = min(len(panels), 3)
    rows = (len(panels) + cols - 1) // cols
    gap, top, lab = 12, 44, 30
    Wd = cols * (PW * SC + gap) + gap
    Hh = top + rows * (PH * SC + lab + gap)
    frames, durs = [], []
    for i in range(n):
        img = Image.new("RGB", (Wd, Hh), (24, 18, 30))
        d = ImageDraw.Draw(img)
        title = "Редкие модули в бою" if frame == "редкие" else f"{frame}: модули в бою"
        d.text((gap, 8), title, font=ft_, fill=(236, 214, 160))
        for j, (name, imgs, ds) in enumerate(panels):
            im = imgs[min(i, len(imgs) - 1)].resize((PW * SC, PH * SC), Image.NEAREST)
            x, y = gap + (j % cols) * (PW * SC + gap), top + (j // cols) * (PH * SC + lab + gap)
            img.paste(im, (x, y))
            d.text((x + 8, y + PH * SC + 4), name, font=fh, fill=(226, 186, 106))
        frames.append(img)
        durs.append(max(p[2][min(i, len(p[2]) - 1)] for p in panels))
    pal = [f.convert("P", palette=Image.Palette.ADAPTIVE, colors=255) for f in frames]
    files = {"Мудрец": "sage", "Горн": "gorn", "Орудие": "orudie", "Механик": "meh", "Страж": "guard", "редкие": "rare"}
    path = out(f"effects_{files[frame]}.gif")
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=durs, loop=0, disposal=2, optimize=False)
    print(path, frames[0].size, n, "frames")
    return [(name, imgs) for name, imgs, _ in panels]


def key_sheet(all_panels, SC=2):
    """One key frame of every effect: the moment it goes off."""
    fh = ImageFont.truetype(font("PTSerif-Bold.ttf"), 18)
    ft_ = ImageFont.truetype(font("PTSerif-Bold.ttf"), 26)
    items = []
    for frame, panels in all_panels:
        for name, imgs in panels:
            key = imgs[keys.get(name, len(imgs) * 2 // 3)]
            items.append((f"{name} · {OWNER.get(name, frame)}", key))
    PW, PH = items[0][1].size
    cols = 4
    rows = (len(items) + cols - 1) // cols
    s = 0.75
    pw, ph = int(PW * SC * s), int(PH * SC * s)
    gap, top, lab = 10, 52, 28
    img = Image.new("RGB", (cols * (pw + gap) + gap, top + rows * (ph + lab + gap)), (24, 18, 30))
    d = ImageDraw.Draw(img)
    d.text((gap, 12), "Модули в бою: момент срабатывания", font=ft_, fill=(236, 214, 160))
    for j, (label, im) in enumerate(items):
        x, y = gap + (j % cols) * (pw + gap), top + (j // cols) * (ph + lab + gap)
        img.paste(im.resize((pw, ph), Image.NEAREST), (x, y))
        d.text((x + 6, y + ph + 4), label, font=fh, fill=(226, 186, 106))
    path = out("effects.png")
    img.save(path)
    print(path, img.size)


if __name__ == "__main__":
    which = sys.argv[1:] or list(EFFECTS)
    allp = []
    for fr in which:
        allp.append((fr, effect_gif(fr)))
    if not sys.argv[1:]:
        key_sheet(allp)
