"""The swarm's mutations: the common pool and each leader's own pool. Every mutation shows on the body (it takes a detail's
place), and each sheet shows what it does in battle (or in the brood, for those that work there).

    python3 tools/sprites/swarm_mut.py            -> out/swarm_mut_*.png (all five pools)
    python3 tools/sprites/swarm_mut.py check      -> out/swarm_mut_check.png (every body, large)
    python3 tools/sprites/swarm_mut.py common     -> one pool (common, matka, razum, devourer, cuckoo)
"""
import sys
import numpy as np
from kit import *
from r3d import Mat, rot_z, rot_y, rot_x
import swarm1 as W
from swarm1 import spike, rings, M_BONE, M_FANG, M_SHEEN, M_EYE, M_DARKEYE, M_WING_NEAR, M_VEIN

# ------------------------------------------------------------------ materials
SILK = Mat(ramp("#2a2622", "#5a544a", "#948c7e", "#c8c0b0", "#f0eadc"))
GLAND = Mat(ramp("#2a1a04", "#6a4a08", "#b08a14", "#e8c840", "#fff2a0"), emissive=hexc("#e0b020"), glow_r=3, glow_k=0.2)
VIVI = Mat(ramp("#1c0e14", "#3e2232", "#6a4458", "#9a7488", "#ccaabb"))
GRUB = Mat(ramp("#241a12", "#54442e", "#8a7656", "#bea98a", "#ece0c4"))
PSI = Mat(ramp("#1e0e36", "#462078", "#7640c0", "#ac80ec", "#e6d2ff"), emissive=hexc("#b070ff"), glow_r=5, glow_k=0.45)
PSI_DIM = Mat(ramp("#1a0e2c", "#341a5a", "#563090", "#8460c0", "#c0a8e8"), emissive=hexc("#8a50e0"), glow_r=3, glow_k=0.2)
MASK = Mat(ramp("#2a2630", "#5a5462", "#948c9a", "#c8c0cc", "#f0eaf2"))
DREAD = Mat(ramp("#2a0618", "#6a0e30", "#b02050", "#f04a80", "#ffb0d0"), emissive=hexc("#ff4080"), glow_r=3, glow_k=0.35)
STICKY = Mat(ramp("#2a1a04", "#6a4a10", "#b0841c", "#e8c050", "#fff0b0"), emissive=hexc("#f0c040"), glow_r=3, glow_k=0.3)
FUZZ = Mat(ramp("#2a1606", "#5e340c", "#9a5c16", "#d2902e", "#f6d08a"))
BEEBAND = Mat(ramp("#1a1404", "#4a3a08", "#8a6c10", "#d0a828", "#f6e080"))
HONEY = Mat(ramp("#2a1402", "#6a3606", "#b0640e", "#e8a028", "#ffe08a"), emissive=hexc("#e09020"), glow_r=5, glow_k=0.3)
BLOOD = Mat(ramp("#1a0204", "#4a060a", "#8e1010", "#d02a1e", "#ff8a6a"), emissive=hexc("#e02a1a"), glow_r=3, glow_k=0.3)
WARN = Mat(ramp("#1a0404", "#4a0a08", "#8a1a10", "#c83a1c", "#f08a50"))
STEEL = Mat(ramp("#1e2228", "#3a404a", "#606874", "#949ca8", "#d0d6de"))
SHIELD = Mat(ramp("#1a1008", "#3e2a14", "#6e4c26", "#a47a44", "#d8b07a"))
FLESH = Mat(ramp("#2a1a1a", "#5a3a3a", "#9a6a66", "#d0a09a", "#f6d6d0"))
HEAL = Mat(ramp("#0e2a10", "#1e5a24", "#3a9a40", "#7ad070", "#d0ffc0"), emissive=hexc("#70e070"), glow_r=3, glow_k=0.3)
ROYAL = Mat(ramp("#2a1a04", "#6a4608", "#b08018", "#e8c040", "#fff4b0"), emissive=hexc("#f0c040"), glow_r=3, glow_k=0.2)
NACRE = Mat(ramp("#2a2830", "#4a4858", "#7a7890", "#b0b0c8", "#e8eaf6"), dither=True)
EGG = Mat(ramp("#1e2a14", "#3a5222", "#5e823a", "#8eb458", "#cce890"), emissive=hexc("#7ab040"), glow_r=3, glow_k=0.18)
SAC = Mat(ramp("#0c040a", "#1e0a16", "#38142a", "#58223e", "#86405a"))
BAND = Mat(ramp("#2a2622", "#5a544c", "#948c80", "#c8c0b2", "#f0eadc"))
SATED = Mat(ramp("#2a1018", "#5a2432", "#9a4a58", "#d08088", "#f6c0c0"))
FAT = Mat(ramp("#2a2014", "#5a4a30", "#9a8458", "#d0bc8a", "#f6ecd0"))
MEAT = Mat(ramp("#2a0606", "#5a1010", "#9a2a24", "#d05a48", "#f6a090"))
TOOTH = Mat(ramp("#1a1410", "#3e3428", "#7a6c58", "#c2b49a", "#f2ead6"))
CRIMSON = Mat(ramp("#14040a", "#3a0a14", "#6a1420", "#a02a2e", "#d65a4a"))
FRENZY_EYE = Mat(ramp("#4a0604", "#9a1008", "#e02a10", "#ff7a3a", "#ffd0a0"), emissive=hexc("#ff4a1a"), glow_r=5, glow_k=0.6)
ESSENCE = Mat(ramp("#3a3a08", "#7a7a14", "#c0c830", "#eef070", "#ffffd0"), emissive=hexc("#e8f070"), glow_r=8, glow_k=0.6)
VEIL = Mat(ramp("#0c0a10", "#1c1824", "#2e2838", "#463e52", "#6a6078"), dither=True)
FUNGUS = Mat(ramp("#2a1e10", "#5a4428", "#9a7a4a", "#d0b07a", "#f6e8c0"))
CAP = Mat(ramp("#3a1606", "#7a3010", "#c05a1a", "#f09040", "#ffd090"), emissive=hexc("#f08030"), glow_r=3, glow_k=0.25)
LEUCO = Mat(ramp("#0e2a0a", "#1e5a14", "#3a9a22", "#78d040", "#d0ff90"), emissive=hexc("#80e040"), glow_r=3, glow_k=0.3)
OIL = Mat(ramp("#08060c", "#16121e", "#262036", "#3e3454", "#6a5a8a"))
MUTA = [Mat(ramp("#2a0e36", "#5a1e78", "#9a40c0", "#d080f0", "#f6d0ff"), emissive=hexc("#c070ff"), glow_r=3, glow_k=0.35),
        Mat(ramp("#3a1406", "#7a2e0c", "#c05a14", "#f09030", "#ffd090"), emissive=hexc("#ff8a20"), glow_r=3, glow_k=0.35),
        Mat(ramp("#0e2a0a", "#1e5a14", "#3a9a22", "#78d040", "#d0ff90"), emissive=hexc("#80e040"), glow_r=3, glow_k=0.35)]
BLOODY = Mat(ramp("#120406", "#34080c", "#5e1014", "#8e1e1e", "#c04a3a"))


# ------------------------------------------------------------------ the pools
# what each mutation does, as the game shows it: lines of terms (fxg.py) with numbers and arrows, as in Conquest
# of Elysium — "{когда} → {что}"; the mouse over a glyph shows what it means. A drawback starts with "минус:".
FX = {
    "spinner": ["{раз} → {паутина} {ход:∞}", "минус: {раз} → {атака:0}", "минус: {огонь} → {паутина:✕}"],
    "exploder": ["{полрана} → {клей:1} {радиус:1}", "{клей} → {машина:✓}", "минус: {полрана} → {гибель}"],
    "bolas": ["{атака} → {притяг}", "{притяг} → {перезарядка}"],
    "beeball": ["{облепили:2+} → {мимо}"],
    "pupa": ["{раз} {полрана} → {кокон}", "{кокон} {ход:2} → {лечение} {полёт} {урон:+}", "{огонь} → {кокон:✕}",
             "минус: {конец} → {гибель}"],
    "midge": ["{гибель} → {облако}", "{облако} → {мимо} · {машина} {сбой}", "минус: {огонь} → {облако:✕}"],
    "honey": ["{всегда} → {лечение} {радиус:1}", "{гибель} → {мёд}"],
    "blister": ["{рана} {радиус:1} → {ожог}", "{ожог} → {машина:✓}"],
    "cutters": ["{атака} → {щит}"],
    "guard": ["{лидер} {радиус:1} → {перехват:1}"],
    "regen": ["{каждые:1} → {реген}", "минус: {огонь} → {реген:✕}"],
    "nest": ["{гибель_своя} {радиус:1} → {яйцо}", "{яйцо} {ход:2} → {личинка}"],
    "nurse": ["{личинка} {радиус:1} → {рабочая}"],
    "vivi": ["{гибель} → {личинка}"],
    "bud": ["{раз} {рана} → {деление}"],
    "dominant": ["{выводок} → {наследие:100%}"],
    "flight": ["{выводок} → {пара} {выбор}"],
    "hybrid": ["{выводок} → {гибрид}", "минус: {бесплоден}"],
    "heir": ["{лидер} {гибель} → {лидер}", "{всегда} → {атака:0}"],
    "psi_gland": ["{атака} → {пси} {мимо}"],
    "psi_reson": ["{помутнение} → {цепь}"],
    "psi_dread": ["{цель} {помутнение}/{страх} → {урон:+}"],
    "psi_whisper": ["{каждые:1} → {страх} {радиус:1}", "{машина} → {сбой}"],
    "strider": ["{раз} → {страх:1–6} {радиус:2}", "{машина} → {инициатива:−2} {ход:1}"],
    "psi_echo": ["{гибель_своя} → {пси} {цепь}"],
    "psi_last": ["{гибель} → {убийца} {помутнение:1}"],
    "psi_leash": ["{захват} {радиус:1} → {ход:∞}", "минус: {захват} → {цель:1} {носитель}"],
    "psi_relay": ["{всегда} → {ретранс}", "минус: {носитель} → {цель:1}"],
    "sated": ["{съедена} → {тело:2}", "минус: {скорость:−1}"],
    "bait": ["{гибель} → {зов}"],
    "fattened": ["{улей} {съедена} → {рост}", "{конец} → {жир:+1}"],
    "frenzy": ["{ест} {радиус:1} → {безумие}"],
    "table": ["{ест} {радиус:1} → {лечение}"],
    "hungry": ["{гибель} {радиус:1} → {тело} → {рост}"],
    "devblood": ["{выводок} → {гигант:+}"],
    "essence": ["{съедена} → {лидер} {форма} {ход:∞}"],
    "parasitoid": ["{пробой} → {заражение}"],
    "bloodeggs": ["{гибель} → {убийца} {заражение}", "{заражение} {ход:2} → {личинка} {рана}"],
    "spores": ["{заражение} {гибель} → {споры}"],
    "call": ["{атака} {заражение} → {притяг}"],
    "bodyguard": ["{атака} {заражение} → {личинка} {охрана}"],
    "gnaw": ["{атака} {заражение} → {урон:−1} {каждые:1}", "{лечение} → {заражение}"],
    "mutagen": ["{заражение} {гибель} → {личинка} {черта}"],
    "unstable": ["{каждые:5} → {черта} {ход:∞}"],
    "royal": ["{заражение} {гигант} {гибель} → {копия}"],
}


# (key, name, what it does, the second body to show it on)
POOLS = {
    "common": ("Общий пул мутаций", None, "у любого лидера: полезны против любого врага, минус никогда не бьёт по рою", [
        ("spinner", "Прядильные железы", "паутина на клетке: враг застревает, свои бегают свободно", ("stinger",)),
        ("exploder", "Взрывной муравей", "раненая лопается клеем: соседние враги склеены, и машины тоже", ("wings",)),
        ("bolas", "Болас", "бросает липкий шарик на нити и подтягивает врага к рою", ("jumper",)),
        ("beeball", "Пчелиный шар", "облепившие одного врага давят его мимо брони", ("horn",)),
        ("pupa", "Куколка", "раненая окукливается и выходит крылатой; после боя умирает", ("scythes",)),
        ("midge", "Мошкара", "убитая рассыпается облаком: жалит сквозь броню, стрелки не видят", ("acid",)),
        ("honey", "Медовые соты", "соты с мёдом на спине: свои пьют; погибнув, заливает клетку — враги вязнут", ("carapace",)),
        ("blister", "Нарывник", "кто ранит её вплотную, обжигается: его удар слабее", ("firefly",)),
        ("cutters", "Кусачки", "перекусывают щит: щит не спасает от её укуса", ("horn",)),
        ("guard", "Стража лидера", "рядом с лидером принимает удары по нему на себя", ("carapace",)),
        ("regen", "Живучая", "каждый раунд затягивает раны; пока горит — нет", ("wings",)),
    ]),
    "matka": ("Мутации Матки", "Матка", "ветки: Гнездо и Порода; ключевая — Наследница", [
        ("nest", "Малое гнездо", "погибшая рядом своя роняет яйцо, как у Матки", ("carapace",)),
        ("nurse", "Кормилица", "личинка рядом с ней дорастает до рабочей прямо в бою", ("wings",)),
        ("vivi", "Живородящая", "погибнув, выпускает личинку", ("acid",)),
        ("bud", "Почкование", "впервые раненая делится надвое", ("scythes",)),
        ("dominant", "Доминантная линия", "её главная черта передаётся потомкам всегда", ("horn",)),
        ("flight", "Брачный полёт", "пару ей в выводке выбираешь сам", ("stinger",)),
        ("hybrid", "Гибрид", "потомок другой формы берёт способности обеих; гибрид бесплоден", ("wings", "stinger")),
        ("heir", "Наследница", "ключевая: Матка пала — она новая Матка", ("wings",)),
    ]),
    "razum": ("Мутации Разума улья", "Разум улья", "пси-мутации; ветки: Безумие, Ужас, Крик, Кукловод; ключевая — Ретранслятор", [
        ("psi_gland", "Пси-железа", "укус бьёт пси — мимо брони, копит надлом", ("stinger",)),
        ("psi_reson", "Резонатор", "Помутнение бежит дальше по цепочке резонаторов", ("wings",)),
        ("psi_dread", "Чутьё на страх", "сильнее бьёт сбитых с толку, надломленных, бегущих", ("jumper",)),
        ("psi_whisper", "Жуткий шёпот", "соседние враги каждый раунд проверяют страх", ("scythes",)),
        ("strider", "Стрекот", "раз за бой: враги рядом проверяют страх, машины дребезжат", ("jumper",)),
        ("psi_echo", "Эхо крика", "крик погибшей подхватывают соседи с Эхом", ("acid",)),
        ("psi_last", "Последняя воля", "погибая, на раунд забирает разум убийцы", ("acid",)),
        ("psi_leash", "Пси-поводок", "захваченный рядом с ней остаётся у роя, пока она жива", ("horn",)),
        ("psi_relay", "Ретранслятор", "ключевая: Разум бьёт и захватывает с её места", ("wings",)),
    ]),
    "devourer": ("Мутации Пожирателя", "Пожиратель", "ветки: Корм, Пир, Голод; ключевая — Питательная суть", [
        ("sated", "Сытная", "съеденная, засчитывается ему как два тела", ("wings",)),
        ("bait", "Приманка", "погибнув, зовёт его кровью: он бросается к ней напролом", ("wings",)),
        ("fattened", "Откормленная", "между боями её скармливают ему: он сразу растёт", ("acid",)),
        ("frenzy", "Кормовое безумие", "пока он ест, она рядом бьёт сильнее", ("scythes",)),
        ("table", "За столом", "пока он ест, она рядом ест с ним и лечится", ("horn",)),
        ("hungry", "Голодная", "ест павших и растёт в бою, как маленький Пожиратель", ("acid",)),
        ("devblood", "Кровь Пожирателя", "её потомки чаще рождаются гигантами", ("horn",)),
        ("essence", "Питательная суть", "ключевая: съеденная, отдаёт ему способность формы", ("wings",)),
    ]),
    "cuckoo": ("Мутации Чумы", "Чума", "хаос вокруг заражения; ветки: Заражение, Хозяин, Мутации; ключевая — Королевская кладка", [
        ("parasitoid", "Паразитоид", "её пробивший удар заражает, как Яйцеклад", ("wings",)),
        ("bloodeggs", "Яйца в крови", "убийца получает созревшую кладку: личинки выйдут из живого", ("acid",)),
        ("spores", "Споры", "заражённый, погибая, заражает всех соседей", ("acid",)),
        ("call", "Зов кладки", "заражённый бросает строй и бредёт в рой", ("jumper",)),
        ("bodyguard", "Телохранитель", "хозяин стоит над личинками и бьёт любого, кто подойдёт", ("horn",)),
        ("gnaw", "Прожорливая кладка", "кладка ест хозяина: он слабеет, лечение кормит её", ("wings",)),
        ("mutagen", "Мутагенная кладка", "из хозяев вылупляется что попало", ("wings",)),
        ("unstable", "Нестабильная", "каждые 5 раундов — новая случайная черта", ("wings",)),
        ("royal", "Королевская кладка", "ключевая: из крупного врага — его хитиновая копия", ("stinger",)),
    ]),
}
ALL = {k: (name, what) for pool in POOLS.values() for (k, name, what, _) in pool[3]}


# ------------------------------------------------------------------ helpers on the body
def thorax(a):
    return a["wing"] + np.array((-0.2, -1.7, 0))


def surf(a, n, seed, near=True, top=0.0):
    """Points on the near side of the gaster (for spots, eggs, bulges)."""
    rnd = np.random.RandomState(seed)
    gc, gr = a["gc"], a["gr"]
    out = []
    while len(out) < n:
        x, y = rnd.uniform(-0.8, 0.8), rnd.uniform(-0.5 + top, 0.85)
        r2 = x * x + y * y
        if r2 > 0.9:
            continue
        z = np.sqrt(max(0.0, 1 - r2))
        out.append(gc + np.array((x * gr * 1.25, y * gr, (z if near else -z) * gr * 0.98)))
    return out


def chain(m, pts, r0, r1, mat, seg=5):
    for i, (p, q) in enumerate(zip(pts[:-1], pts[1:])):
        t0, t1 = i / (len(pts) - 1), (i + 1) / (len(pts) - 1)
        m.cyl(p, q, r0 + (r1 - r0) * t0, mat, r1=r0 + (r1 - r0) * t1, seg=seg)


# ------------------------------------------------------------------ on the body
def add(m, mc, a, key, pose):
    y0, gc, gr, w, hc, hs = a["y0"], a["gc"], a["gr"], a["wing"], a["hc"], a["hs"]
    atk = pose == "attack"
    # ---- the common pool
    if key == "spinner":
        t = a["tip"]
        for z in (-0.8, 0.0, 0.8):
            m.cyl(t + (0.8, 0.3, z), t + (-1.8, -0.8, z * 1.6), 0.75, M_BONE, r1=0.25, seg=6)
        end = np.array((t[0] - 6.0, 0.2, 1.4))
        m.cyl(t + (-1.8, -0.8, 0), end, 0.3, SILK, seg=4)
        m.poly([end + (1.0, 0.0, -2.0), end + (-3.0, 0.0, 1.6), end + (1.4, 0.0, 2.8)], SILK)
        for d in ((-1.0, 0.1, -0.6), (0.2, 0.1, 1.2)):
            m.cyl(end + (1.0, 0.0, -2.0), end + np.array(d) * 2, 0.15, Mat(W.chitin(0.0)), seg=3)
    elif key == "exploder":
        m.ell(gc, (gr * 1.25, gr * 1.15, gr * 1.15), GLAND, rot_z(0.2))
        for t in (-0.5, 0.0, 0.5):
            x = gc[0] + t * gr
            r = gr * 1.15 * np.sqrt(max(0.1, 1 - t * t * 0.8))
            m.cyl((x - 0.2, gc[1], 0), (x + 0.2, gc[1], 0), r * 1.02, Mat(W.chitin(0.0)), seg=14)
        m.ell(gc + (gr * 0.3, gr * 0.7, gr * 0.6), (gr * 0.3, gr * 0.2, gr * 0.25), M_SHEEN)
    elif key == "bolas":
        f = a.get("fore") if a.get("fore") is not None else hc + np.array((-2.0, -1.0, 0))
        hold = hc + np.array((1.2 * hs, 2.6 * hs, 1.6))
        m.limb([f + (0, 0, 1.2), f + (0.6, 3.6, 2.0), hold], 1, mc, band=3)
        ball = hold + ((5.0, 1.6, 0.6) if atk else (2.2, -5.0, 0.6))
        m.cyl(hold, ball, 0.32, SILK, seg=4)
        m.ell(ball, (2.0, 2.0, 2.0), STICKY)
        m.ell(ball + (0.5, 0.6, 0.9), (0.45, 0.4, 0.4), M_SHEEN)
        for d in ((-0.7, -1.3, 0.3), (0.6, -1.4, -0.2)):
            m.ell(ball + d, (0.35, 0.5, 0.35), STICKY)
    elif key == "beeball":
        tc = thorax(a)
        m.ell(tc + (0, 0.25, 0), (3.4, 2.6, 2.5), FUZZ, rot_z(0.22))
        for i in range(10):
            ang = 0.2 + i * 0.32
            p = tc + np.array((np.cos(ang) * 3.0, np.sin(ang) * 2.4 + 0.3, 0))
            for z in (1.6, -1.6):
                m.ell(p + (0, 0, z), (0.6, 0.6, 0.6), FUZZ)
        rings(m, gc, rot_z(0.25), gr * 1.3, gr * 0.98, BEEBAND, n=3)
    elif key == "pupa":
        L = gr * 1.3
        for k in range(4):
            pts = []
            for x in np.linspace(-0.95, 0.95, 14):
                ph = x * 3.2 + k * np.pi / 2
                r = gr * np.sqrt(max(0.0, 1 - x * x)) * 1.04 + 0.2
                pts.append(gc + rot_z(0.25) @ np.array((x * L, np.cos(ph) * r, np.sin(ph) * r)))
            m.limb(pts, 1, SILK, band=3)
        m.ell(gc + rot_z(0.25) @ np.array((-gr * 0.55, 0, 0)), (gr * 0.95, gr * 1.08, gr * 1.08), Mat(SILK.ramp, dither=True), rot_z(0.25))
        t = a["tip"]
        for z in (-0.6, 0.6):
            m.cyl(t, t + (-3.0, -2.2 + z, z * 1.5), 0.45, SILK, r1=0.1, seg=4)
    elif key == "midge":
        for i, p in enumerate(surf(a, 16, 3, top=-0.2)):
            m.ell(p, (0.55, 0.45, 0.4), M_SHEEN if i % 3 == 0 else M_DARKEYE)
        rnd = np.random.RandomState(5)
        for i in range(9):
            c = gc + np.array((rnd.uniform(-2, 14), rnd.uniform(gr + 1.5, gr + 9), rnd.uniform(-2, 4)))
            m.ell(c, (0.55, 0.45, 0.45), M_DARKEYE)
            m.ell(c + (-0.3, 0.6, 0.4), (0.5, 0.25, 0.25), M_WING_NEAR)
    elif key == "honey":
        WAX = Mat(ramp("#2a2010", "#6a5420", "#b09040", "#e0c878", "#fff4c8"))
        tops = [(-0.75, 0.0), (-0.25, 0.0), (0.25, 0.0), (-0.5, 0.42), (0.0, 0.42), (-0.5, -0.42), (0.0, -0.42), (0.45, 0.4)]
        for i, (u, v) in enumerate(tops):                      # a slab of comb stuck to the back
            x = gc[0] + u * gr * 1.1
            y = gc[1] + gr * 0.85 - abs(u) * 0.9
            z = v * gr * 1.05
            base = np.array((x, y, z))
            top = base + np.array((-0.3, 2.2 + 0.4 * (i % 2), 0))
            m.cyl(base, top, 1.15, WAX, seg=6)
            if i % 3 != 2:
                m.ell(top + (0, 0.05, 0), (0.9, 0.3, 0.9), HONEY)
            else:
                m.ell(top + (0, 0.05, 0), (0.9, 0.25, 0.9), Mat(W.chitin_shift(WAX, 0.0, light=1.3)))
        m.ell(gc + (gr * 0.2, gr * 0.2, gr * 0.85), (0.5, 0.8, 0.4), HONEY)
        m.ell(gc + (gr * 0.2, -gr * 0.4, gr * 0.85), (0.35, 0.5, 0.3), HONEY)
    elif key == "blister":
        rings(m, gc, rot_z(0.25), gr * 1.3, gr * 0.99, WARN, n=2)
        m.ell(hc, (2.4 * hs, 2.2 * hs, 2.2 * hs), WARN)
        for z in (1.2, -1.2):
            m.ell(hc + (0.9 * hs, 0.5 * hs, z * hs), (0.55, 0.55, 0.55), M_DARKEYE)
        for f in a["feet"]:
            if f[2] > 0:
                p = np.array((f[0] - 0.4, y0 * 0.62, f[2] * 0.72))
                m.ell(p, (0.55, 0.65, 0.55), BLOOD)
                m.ell(p + (0.1, -1.0, 0), (0.3, 0.45, 0.3), BLOOD)
    elif key == "cutters":
        jaw = 0.85 if atk else 0.35
        for z in (1.0, -1.0):
            base = hc + np.array((1.6 * hs, -0.8 * hs, z * 0.7 * hs))
            L = 6.2 * hs
            mid = base + np.array((np.cos(jaw) * L * 0.6, -0.4, np.sign(z) * np.sin(jaw) * L * 0.5))
            tip = mid + np.array((L * 0.5, -0.1, -np.sign(z) * L * 0.34))
            m.cyl(base, mid, 1.35 * hs, STEEL, r1=1.05 * hs, seg=6)
            m.cyl(mid, tip, 1.05 * hs, STEEL, r1=0.15, seg=5)
            for t in (0.3, 0.55, 0.8):
                p = base + (mid - base) * t * 1.6 if t < 0.6 else mid + (tip - mid) * (t - 0.4)
                spike(m, p, p + np.array((0.25, -0.8, -np.sign(z) * 1.4)) * hs, 0.45 * hs, M_FANG)
            m.cyl(mid + (0, 0.6, 0), tip + (0, 0.5, 0), 0.35, M_SHEEN, seg=4)
    elif key == "guard":
        c = hc + np.array((1.3 * hs, 0.5 * hs, 0))
        m.ell(c, (0.8 * hs, 3.6 * hs, 3.6 * hs), SHIELD)
        m.ell(c + (0.4 * hs, 0, 0), (0.55 * hs, 2.8 * hs, 2.8 * hs), Mat(W.chitin_shift(SHIELD, 0.0, light=1.3)))
        for ang in np.linspace(0, 2 * np.pi, 11)[:-1]:
            p = c + np.array((0.55 * hs, np.sin(ang) * 3.2 * hs, np.cos(ang) * 3.2 * hs))
            m.ell(p, (0.35, 0.35, 0.35), M_BONE)
        for (x, y) in a["back"][-2:]:
            m.box((x, y - 0.1, 0), (2.6, 0.9, 3.0), SHIELD, rot_z(0.15))
    elif key == "regen":
        hd = a.get("hind") if a.get("hind") is not None else gc + np.array((gr, -1.0, 0))
        hip = hd + np.array((0.4, 0.4, 1.6))
        m.cyl(hip, hip + (-1.2, -2.0, 1.6), 0.75, FLESH, r1=0.6, seg=6)
        m.ell(hip + (-1.2, -2.0, 1.6), (0.8, 0.8, 0.8), FLESH)
        m.ell(hip + (-1.3, -2.3, 2.1), (0.4, 0.4, 0.4), HEAL)
        for i, p in enumerate(surf(a, 5, 11, top=-0.1)):
            m.ell(p, (1.4, 1.0, 0.45), FLESH)
            m.box(p + (0, 0, 0.4), (1.6, 0.25, 0.2), HEAL, rot_z(0.5 + i))
        m.ell(thorax(a) + (0.6, 0.9, 1.5), (1.0, 0.7, 0.4), FLESH)
    # ---- the Matka's pool
    elif key == "nest":
        for i, (x, y) in enumerate(a["back"][:3]):
            for j, d in enumerate(((0, 0.6, 0.0), (0.9, 0.3, 0.9), (-0.9, 0.3, -0.9), (0.2, 0.4, 1.2))):
                m.ell(np.array((x, y, 0)) + d, (0.8, 1.15, 0.8), EGG, rot_z(0.3 + 0.2 * j))
        m.ell(gc + (0, gr * 0.85, 0), (gr * 0.9, 0.5, gr * 0.7), SILK, rot_z(0.25))
    elif key == "nurse":
        p = hc + np.array((3.4 * hs, -1.6 * hs, 0.4))
        for i in range(6):
            ang = -0.6 + i * 0.55
            q = p + np.array((np.cos(ang) * 1.4, np.sin(ang) * 1.6, 0))
            m.ell(q, (0.95 - 0.06 * i, 0.85 - 0.06 * i, 0.85), GRUB)
        m.ell(p + (1.4, -0.6, 0.3), (0.35, 0.35, 0.35), M_DARKEYE)
        m.ell(thorax(a) + (1.4, -0.5, 0), (1.6, 1.3, 1.5), Mat(W.chitin_shift(mc, 0.0, sat=0.8, light=1.5)))
    elif key == "vivi":
        m.ell(gc, (gr * 1.12, gr * 1.06, gr * 1.06), VIVI, rot_z(0.2))
        for i in range(7):
            ang = 0.6 + i * 0.7
            p = gc + np.array((np.cos(ang) * gr * 0.52, np.sin(ang) * gr * 0.46, gr * 0.84))
            m.ell(p, (gr * 0.3 - 0.04 * i, gr * 0.28 - 0.04 * i, 0.6), GRUB)
        m.ell(gc + np.array((np.cos(0.6) * gr * 0.62, np.sin(0.6) * gr * 0.5, gr * 0.9)), (gr * 0.18, gr * 0.18, 0.5), Mat(W.chitin(0.0)))
    elif key == "bud":
        pale = Mat(W.chitin_shift(mc, 0.0, sat=0.8, light=1.45))
        c = gc + np.array((gr * 0.05, gr * 0.05, gr * 1.05))
        m.ell(gc + np.array((gr * 0.05, 0.0, gr * 0.75)), (gr * 0.5, gr * 0.45, gr * 0.3), VIVI)
        m.ell(c + (0, 0, gr * 0.3), (gr * 0.75, gr * 0.62, gr * 0.6), pale)
        h = c + (gr * 0.7, gr * 0.2, gr * 0.55)
        m.ell(h, (gr * 0.4, gr * 0.36, gr * 0.36), pale)
        for z in (0.16, -0.16):
            m.ell(h + (gr * 0.28, gr * 0.12, z * gr + gr * 0.2), (0.38, 0.38, 0.38), M_EYE)
        for k in range(3):
            m.limb([c + (gr * (0.35 - 0.35 * k), -gr * 0.4, gr * 0.7), c + (gr * (0.5 - 0.35 * k), -gr * 0.95, gr * 1.1)], 1, pale, band=2)
    elif key == "dominant":
        for i, d in enumerate(((-0.6, 1.7), (0.0, 2.0), (0.6, 1.7))):
            b = hc + np.array((d[0] * hs, d[1] * hs, 0))
            spike(m, b, b + np.array((-0.4, 3.4 + 1.2 * (i == 1), 0)) * hs, 0.8 * hs, ROYAL)
        tc = thorax(a)
        for x in (-1.6, 0.0, 1.6):
            spike(m, tc + (x, 1.8, 0), tc + (x - 1.0, 4.6, 0), 0.7, ROYAL)
        rings(m, gc, rot_z(0.25), gr * 1.3, gr * 0.99, ROYAL, n=1)
    elif key == "flight":
        r0 = w
        L = a["length"] / 14
        up = 4.0 if atk else 0.0
        for z in (-0.7, 0.7):
            s = np.sign(z)
            m.poly([r0 + (0.6, 0.4, z), r0 + (-17.5 * L, 1.4 + up, z + 2.2 * s), r0 + (-18.5 * L, 3.0 + up, z + 1.6 * s),
                    r0 + (-5.0 * L, 2.4 + up * 0.5, z + 0.7 * s)], NACRE)
            m.limb([r0 + (0.3, 0.6, z), r0 + (-17.6 * L, 2.4 + up, z + 1.9 * s)], 1, M_VEIN, band=2)
        m.ell(w + (0.2, 0.2, 0), (2.0, 1.2, 1.8), ROYAL)
    elif key == "hybrid":
        other = Mat(W.chitin(0.0, "stinger" if not a.get("has_stinger") else None))
        m.ell(gc + (0, 0.05, 0), (gr * 1.36, gr * 1.04, gr * 1.04), other, rot_z(0.25))
        tc = thorax(a)
        x0 = gc[0] + gr * 1.2
        for ang in np.linspace(-0.2, np.pi + 0.2, 9):
            p = np.array((x0 - 0.2, gc[1] + np.sin(ang) * gr * 0.62, np.cos(ang) * gr * 0.62))
            m.box(p + (0, 0, 0.3), (2.2, 0.5, 0.5), M_BONE, rot_z(0.3))
        m.ell(tc, (2.4, 1.5, 1.5), Mat(W.chitin_shift(other, 0.0, light=1.1)), rot_z(0.22))
    elif key == "heir":
        m.ell(gc + (-gr * 0.2, 0.2, 0), (gr * 1.6, gr * 1.26, gr * 1.26), SAC, rot_z(0.18))
        for t in (-0.55, -0.1, 0.35):
            x = gc[0] - gr * 0.2 + t * gr * 1.4
            r = gr * 1.26 * np.sqrt(max(0.1, 1 - t * t * 0.9)) * 1.01
            m.cyl((x - 0.25, gc[1] + 0.2, 0), (x + 0.25, gc[1] + 0.2, 0), r, BAND, seg=14)
        for i, d in enumerate(((-0.5, 1.8), (0.1, 2.1), (0.7, 1.8))):
            b = hc + np.array((d[0] * hs, d[1] * hs, 0))
            spike(m, b, b + np.array((-0.2, 1.6, 0)) * hs, 0.45 * hs, ROYAL)
    # ---- the Hive Mind's pool
    elif key == "psi_gland":
        for z in (1, -1):
            base = hc + np.array((1.5 * hs, -0.9 * hs, z * 0.6 * hs))
            m.ell(base + np.array((1.6 * hs, -0.5, z * 0.4)), (2.0 * hs, 1.0, 1.0), PSI)
        m.ell(hc + np.array((0.2 * hs, -0.2 * hs, 0)), (2.0 * hs, 1.6 * hs, 2.0 * hs), PSI_DIM)
        m.ell(hc + np.array((-0.2 * hs, 0.4 * hs, 1.7 * hs)), (1.3 * hs, 1.0 * hs, 0.6), PSI)
    elif key == "psi_reson":
        for z in (1, -1):
            a0 = hc + np.array((0.8 * hs, 1.2 * hs, 0.5 * z))
            p1 = a0 + np.array((1.0, 4.4, 1.0 * z))
            p2 = p1 + np.array((4.4, 2.6, 1.8 * z))
            m.limb([a0, p1, p2], 1, mc, band=3 if z > 0 else 1)
            m.ell(p2, (0.8, 0.8, 0.8), PSI)
            m.ell(p1 + (p2 - p1) * 0.5, (0.45, 0.45, 0.45), PSI_DIM)
    elif key == "psi_echo":
        m.ell(w + np.array((0.6, -1.6, 0)), (1.8, 1.5, 1.7), PSI_DIM)
        for r in (1.2, 1.9):
            for t in np.linspace(0, 2 * np.pi, 9)[:-1]:
                m.ell(w + np.array((0.6, -1.6 + np.sin(t) * r * 0.8, np.cos(t) * r * 1.4)), (0.22, 0.22, 0.22), PSI)
    elif key == "psi_leash":
        for z, sw in ((1, 1.0), (-1, -0.6), (0, 0.4)):
            p0 = np.array((w[0] - 1.0, w[1] + 1.0, 0.6 * z))
            pts = [p0 + np.array((-2.0 * i, 1.6 * np.sin(i * 1.1 + sw) + 0.8 * i, z * 0.6 * i)) for i in range(5)]
            m.limb(pts, 1, PSI_DIM, band=2)
            m.ell(pts[-1], (0.4, 0.4, 0.4), PSI)
    elif key == "psi_whisper":
        m.ell(hc + np.array((0.7 * hs, 0.2 * hs, 0)), (1.9 * hs, 1.8 * hs, 2.0 * hs), MASK)
        for (dx, dy, dz) in ((1.5, 0.6, 0.6), (1.5, 0.6, -0.6), (1.2, 1.1, 0.0), (1.7, 0.0, 0.0), (1.0, 0.9, 0.9), (1.0, 0.9, -0.9)):
            m.ell(hc + np.array((dx * hs + 1.0 * hs, dy * hs, dz * hs)), (0.4, 0.4, 0.4), PSI)
    elif key == "psi_dread":
        for z in (1, -1):
            m.ell(hc + np.array((0.9 * hs, 0.5 * hs, 1.2 * z * hs)), (0.7, 0.7, 0.55), DREAD)
            m.ell(hc + np.array((1.4 * hs, -0.3 * hs, 0.7 * z * hs)), (0.5, 0.4, 0.4), Mat(W.chitin_shift(mc, 0.0, light=1.6)))
        for (x, y) in a["back"][:3]:
            spike(m, (x, y - 0.2, 0), (x - 0.6, y + 2.2, 0), 0.35, DREAD)
    elif key == "strider":
        top = gc + np.array((0, gr * 0.92, 0))
        m.ell(top, (gr * 0.9, 0.5, gr * 0.75), Mat(W.chitin_shift(mc, 0.0, light=1.5)), rot_z(0.2))
        for i in range(8):
            p = top + np.array((gr * 0.75 - i * gr * 0.22, 0.45 + 0.04 * i, 0))
            m.box(p, (0.32, 0.9, gr * 1.3), M_BONE, rot_z(0.2))
        for z in (1, -1):
            m.ell(w + (0.6, -0.6, 1.8 * z), (0.8, 0.8, 0.3), M_SHEEN)
    elif key == "psi_last":
        c = gc + np.array((gr * 0.15, gr * 0.15, gr * 0.86))
        m.ell(c, (gr * 0.62, gr * 0.58, 0.6), MASK)
        m.ell(c + (gr * 0.05, -gr * 0.5, 0.1), (gr * 0.36, gr * 0.22, 0.5), MASK)
        for dx in (-0.25, 0.3):
            m.ell(c + np.array((dx * gr, gr * 0.1, 0.45)), (gr * 0.17, gr * 0.19, 0.3), M_DARKEYE)
            m.ell(c + np.array((dx * gr, gr * 0.1, 0.65)), (0.4, 0.4, 0.3), PSI)
        for dx in (-0.15, 0.0, 0.15):
            m.box(c + np.array((dx * gr, -gr * 0.5, 0.55)), (0.25, gr * 0.22, 0.2), M_DARKEYE)
    elif key == "psi_relay":
        b = w + np.array((-0.4, 0.4, 0))
        top = b + np.array((-1.2, 8.0, 0))
        m.cyl(b, top, 0.7, mc, r1=0.45, seg=6)
        for t in (0.45, 0.75):
            p = b + (top - b) * t
            m.ell(p, (1.7 - t, 0.25, 1.7 - t), PSI_DIM)
        m.ell(top + (0, 1.5, 0), (2.0, 1.6, 1.8), PSI_DIM)
        for d in ((0.7, 2.3, 0.7), (-0.6, 2.2, 0.9), (0.2, 2.6, -0.6), (0.9, 1.4, 1.1)):
            m.ell(top + d, (0.7, 0.6, 0.6), PSI)
    # ---- the Devourer's pool
    elif key == "sated":
        m.ell(gc + (0, 0.3, 0), (gr * 1.45, gr * 1.32, gr * 1.32), SATED, rot_z(0.2))
        for x in (-0.7, 0.0, 0.6):
            m.ell(gc + np.array((x * gr, gr * 1.27 - abs(x) * 0.9, 0)), (1.3, 0.35, 2.0), mc, rot_z(0.2 - x * 0.4))
        for i, p in enumerate(surf(a, 5, 21, top=-0.2)):
            m.box(p * np.array((1, 1, 1.0)) + (0, 0, 0.35), (0.25, 1.3, 0.2), Mat(W.chitin_shift(SATED, 0.0, light=1.3)), rot_z(0.4))
    elif key == "bait":
        for x in (-0.6, -0.05, 0.5):
            p = gc + np.array((x * gr, -gr * 0.1, gr * 0.9))
            m.ell(p, (1.4, 1.2, 0.7), BLOOD)
            m.ell(p + (0.1, -1.2, 0.2), (0.55, 0.9, 0.5), BLOOD)
        for x in (gc[0] - 1.0, gc[0] + 1.6):
            for k_ in range(2):
                m.ell((x, max(1.0, gc[1] - gr - 1.2 - k_ * 1.6), gr * 0.5), (0.3, 0.55, 0.3), BLOOD)
        m.ell(thorax(a) + (0, -0.2, 1.4), (1.0, 0.8, 0.5), BLOOD)
    elif key == "fattened":
        for i, x in enumerate((-0.9, -0.3, 0.3)):
            m.ell(gc + np.array((x * gr, -gr * 0.12, 0)), (gr * 0.55, gr * 1.18, gr * 1.22), FAT, rot_z(0.25))
        tc = thorax(a)
        m.ell(tc + (0, -0.4, 0), (2.9, 2.3, 2.4), FAT, rot_z(0.22))
        m.ell(gc + (gr * 0.1, -gr * 0.95, 0), (gr * 1.05, gr * 0.42, gr * 0.9), FAT)
    elif key == "frenzy":
        for z in (1.2, -1.2):
            m.ell(hc + (0.9 * hs, 0.5 * hs, z * hs), (0.95, 0.95, 0.95), FRENZY_EYE)
        mouth = hc + np.array((2.2 * hs, -1.5 * hs, 0.3))
        for k_ in range(4):
            m.ell(mouth + (0.2 * k_, -1.0 * k_, 0), (0.42 - 0.05 * k_, 0.6, 0.42 - 0.05 * k_), BLOOD)
        for (x, y) in a["back"]:
            spike(m, (x, y - 0.4, 0), (x - 1.0, y + 2.8, 0), 0.5, mc)
            m.ell((x - 1.0, y + 2.8, 0), (0.32, 0.32, 0.32), BLOOD)
    elif key == "table":
        p = hc + np.array((3.8 * hs, -1.5 * hs, 0.2))
        p = p + np.array((0.8, -0.4, 0))
        m.ell(p, (2.6, 1.9, 2.0), MEAT, rot_z(0.3))
        m.ell(p + (0.6, 0.8, 1.2), (1.1, 0.7, 0.7), FAT)
        b0, b1 = p + np.array((-2.2, -1.4, 1.4)), p + np.array((2.6, 2.0, -0.8))
        m.cyl(b0, b1, 0.55, M_BONE, seg=5)
        for q in (b0, b1):
            m.ell(q, (0.85, 0.85, 0.85), M_BONE)
    elif key == "hungry":
        m.ell(gc, (gr * 1.36, gr * 1.04, gr * 1.04), Mat(W.chitin_shift(mc, 0.0, sat=0.5, light=0.55)), rot_z(0.25))
        for t in (-0.6, -0.3, 0.0, 0.3, 0.6):
            x = gc[0] + t * gr * 1.2
            r = gr * 1.06 * np.sqrt(max(0.1, 1 - t * t * 0.75))
            m.cyl((x - 0.32, gc[1], 0), (x + 0.32, gc[1], 0), r, M_BONE, seg=12)
        for z in (1.0, -1.0):
            base = hc + np.array((1.5 * hs, -1.2 * hs, z * 0.5 * hs))
            spike(m, base, base + np.array((2.6, -1.6, z * 0.4)) * hs, 0.5 * hs, TOOTH)
    elif key == "devblood":
        for (x, y) in a["back"]:
            m.box((x, y - 0.1, 0), (2.6, 1.0, 3.2), CRIMSON, rot_z(0.18))
            spike(m, (x, y + 0.3, 0), (x - 1.0, y + 2.4, 0), 0.6, TOOTH)
        for z in (1, -1):
            for i in range(3):
                b = hc + np.array(((1.0 + 0.5 * i) * hs, -1.1 * hs, z * (0.9 - 0.25 * i) * hs))
                spike(m, b, b + np.array((0.5, -1.4, 0)) * hs, 0.32 * hs, TOOTH)
        m.ell(hc + (0.1 * hs, 0.9 * hs, 0), (1.9 * hs, 1.0 * hs, 1.9 * hs), CRIMSON)
    elif key == "essence":
        c = gc + np.array((gr * 0.1, -gr * 0.05, gr * 0.5))
        m.ell(c, (gr * 0.95, gr * 0.82, gr * 0.7), SAC)
        m.ell(c + (0, 0, gr * 0.3), (gr * 0.72, gr * 0.62, gr * 0.62), ESSENCE)
        for ang in np.linspace(0, 2 * np.pi, 7)[:-1]:
            m.box(c + np.array((np.cos(ang) * gr * 0.4, np.sin(ang) * gr * 0.35, gr * 0.62)), (gr * 0.5, 0.25, 0.2), SAC, rot_z(ang))
    # ---- the Cuckoo's pool
    elif key == "parasitoid":
        t = a["tip"]
        if atk:
            pts = [t, t + (-2.0, -3.0, 0.4), t + (3.0, -5.0, 0.6), t + (11.0, -4.2, 0.6), t + (16.0, -3.0, 0.6)]
        else:
            pts = [t, t + (-4.0, -1.2, 0.2), t + (-9.0, -1.6, 0.3), t + (-14.0, -0.8, 0.3), t + (-17.0, 0.2, 0.3)]
        chain(m, pts, 0.42, 0.1, M_FANG)
        for z in (0.5, -0.5):
            m.cyl(t, t + ((-3.4, -1.6, z) if not atk else (-1.6, -3.2, z)), 0.38, Mat(W.chitin(0.0)), r1=0.15, seg=4)
        m.ell(t + (0.6, 0.3, 0), (1.3, 1.1, 1.2), EGG)
    elif key == "bloodeggs":
        m.ell(gc + (0, 0.02, 0), (gr * 1.35, gr * 1.03, gr * 1.03), Mat(W.chitin_shift(mc, 0.12, sat=1.6, light=1.25), dither=True), rot_z(0.25))
        for i, p in enumerate(surf(a, 14, 41)):
            m.ell(p, (0.55, 0.42, 0.35), EGG)
        tc = thorax(a)
        for d in ((0.6, 0.6, 1.6), (-0.7, 0.2, 1.7), (0.0, 1.2, 1.4)):
            m.ell(tc + d, (0.45, 0.36, 0.3), EGG)
    elif key == "spores":
        b = w + np.array((-0.6, 0.5, 0))
        pts = [b, b + (-1.6, 3.4, 0.2), b + (-0.6, 6.6, 0.4), b + (0.8, 9.0, 0.3)]
        chain(m, pts, 0.75, 0.45, FUNGUS)
        m.ell(pts[-1] + (0, 0.8, 0), (1.8, 1.1, 1.8), CAP)
        h0 = hc + np.array((-0.3 * hs, 1.6 * hs, 0.3))
        chain(m, [h0, h0 + (0.6, 2.4, 0.2), h0 + (1.6, 4.2, 0.2)], 0.45, 0.3, FUNGUS)
        m.ell(h0 + (1.6, 4.8, 0.2), (1.0, 0.7, 1.0), CAP)
        for p in surf(a, 5, 51, top=-0.3):
            m.ell(p, (0.7, 0.5, 0.35), FUNGUS)
        rnd = np.random.RandomState(9)
        for _ in range(7):
            m.ell(pts[-1] + np.array((rnd.uniform(-3, 3), rnd.uniform(1.5, 5), rnd.uniform(-1, 2))), (0.28, 0.28, 0.28), CAP)
    elif key == "call":
        base = hc + np.array((0.8 * hs, 1.0 * hs, 1.0 * hs))
        sway = 1.0 if atk else 0.0
        pts = [base + np.array((0.7 * i + sway * 0.3 * i, 1.35 * i - 0.06 * i * i, 0.25 * i)) for i in range(7)]
        for i, p in enumerate(pts):
            r = 1.45 - 0.07 * i
            m.ell(p * 1.0 + (0.25 * i, 0.3 * i, 0), (r, r * 0.95, r), LEUCO if i % 2 == 0 else BAND)
        m.ell(pts[-1] + (2.0, 2.4, 0), (0.6, 0.6, 0.6), M_DARKEYE)
        base2 = hc + np.array((0.6 * hs, 1.0 * hs, -1.0 * hs))
        for i in range(4):
            m.ell(base2 + np.array((0.5 * i, 1.0 * i, -0.2 * i)), (0.7, 0.7, 0.7), LEUCO if i % 2 == 0 else BAND)
    elif key == "bodyguard":
        for i, p in enumerate(surf(a, 7, 61, top=0.15)):
            ang = 0.4 + i * 0.5
            m.ell(p + (0, 0, 0.4), (1.15, 0.55, 0.55), SILK, rot_z(ang))
            m.ell(p + (0.3, 0.15, 0.85), (0.35, 0.18, 0.18), BAND, rot_z(ang))
        for (x, y) in a["back"][:3]:
            m.ell((x, y + 0.4, 0), (1.15, 0.55, 0.6), SILK, rot_z(0.6))
    elif key == "gnaw":
        for i, p in enumerate(surf(a, 5, 71, top=-0.2)):
            ang = 0.3 + i * 0.9
            for k_ in range(3):
                q = p + np.array((np.cos(ang) * 0.8 * k_, np.sin(ang) * 0.8 * k_, 0.25))
                m.ell(q, (0.75 - 0.1 * k_, 0.6 - 0.08 * k_, 0.5), GRUB)
        for p in surf(a, 3, 72, top=0.0):
            m.ell(p + (0, 0, 0.3), (0.6, 0.45, 0.3), BLOODY)
        p = surf(a, 1, 73, top=0.3)[0]
        m.ell(p + (0, 0, 0.6), (0.6, 0.55, 0.5), GRUB)
        m.ell(p + (0.35, 0.1, 1.0), (0.25, 0.25, 0.2), M_DARKEYE)
    elif key == "mutagen":
        c = gc + np.array((gr * 0.15, -gr * 0.2, gr * 0.45))
        m.ell(c, (gr * 0.95, gr * 0.78, gr * 0.75), OIL)
        for i, p in enumerate(surf(a, 9, 81, top=-0.4)):
            m.ell(p + (0, 0, 0.3), (0.8 - 0.05 * (i % 3), 0.65, 0.4), MUTA[i % 3])
        m.ell(c + (gr * 0.3, gr * 0.5, gr * 0.55), (gr * 0.28, gr * 0.16, gr * 0.2), M_SHEEN)
    elif key == "unstable":
        new = Mat(W.chitin_shift(mc, 0.3, sat=1.3, light=1.6))
        m.ell(gc + (0, gr * 0.62, gr * 0.15), (gr * 1.05, gr * 0.45, gr * 0.5), new, rot_z(0.25))
        for side in (1, -1):
            for x in (-0.6, -0.1, 0.4):
                b = gc + np.array((x * gr, gr * 0.95, side * gr * 0.35))
                m.poly([b, b + np.array((-1.4, 1.6, side * 1.8)), b + np.array((1.0, 1.9, side * 1.6))], mc)
        for i, p in enumerate(surf(a, 4, 91, top=-0.5)):
            m.ell(p + (0, 0, 0.25), (0.9, 0.7, 0.4), MUTA[(i + 1) % 3])
        f = a.get("fore") if a.get("fore") is not None else hc
        m.limb([f + (0, 0, 1.8), f + (2.4, 2.6, 3.0), f + (4.4, 1.2, 3.4)], 1, new, band=3)
        spike(m, f + (4.4, 1.2, 3.4), f + (5.8, 2.6, 3.4), 0.5, M_FANG)
    elif key == "royal":
        t = a["tip"]
        pts = [t, t + (-2.6, -1.8, 0), t + (-5.0, -2.4, 0), t + (-7.4, -1.6, 0)]
        chain(m, pts, 1.0, 0.6, M_BONE)
        for p in pts[1:3]:
            m.cyl(p + (0.25, 0, 0), p - (0.25, 0, 0), 1.0, ROYAL, seg=10)
        egg = pts[-1] + np.array((-1.6, 0.4, 0))
        m.ell(egg, (2.0, 1.6, 1.6), EGG, rot_z(-0.4))
        m.ell(egg + (0.6, 0.6, 1.0), (0.5, 0.4, 0.4), M_SHEEN)
        for i, d in enumerate(((-0.5, 1.8), (0.1, 2.1), (0.7, 1.8))):
            b = hc + np.array((d[0] * hs, d[1] * hs, 0))
            spike(m, b, b + np.array((-0.2, 1.6, 0)) * hs, 0.45 * hs, ROYAL)
    else:
        raise KeyError(key)


# ------------------------------------------------------------------ the cast of the scenes (battle scale, zoomed)
Z = 1.15
F = 1.0                                   # stretches the scenes' offsets on sheets with wider columns
PSI_C, GREEN, RED, AMBER_C, WHITE_C, SILK_C = hexc("#c8a0ff"), hexc("#9ae030"), hexc("#ff5a3a"), hexc("#f0b040"), hexc("#fff4dc"), hexc("#e8e0d0")
_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def bug(traits=(), pose="idle", key=None, seed=1, soldier=False, chimera=None, k=None):
    k = Z if k is None else k
    return cached(("bug", traits, pose, key, seed, soldier, chimera, k),
                  lambda: W.build(traits, 0.0, pose, soldier, k=k, genes=W.genes_for(seed), rare=key, chimera=chimera))


def golem(name="Механик", pose="idle", k=1.0, face_left=True):
    import frames as F
    import swarm_effects as E
    def mk():
        spr = F.build(name, pose, k=F.FRAMES[name][0] * Z * k)
        return E.mirror(spr) if face_left else spr
    return cached(("golem", name, pose, k, face_left, Z), mk)


def man(pose="idle", who="inv", face_left=True):
    import golems_h as GH
    import leaders_h as LH
    import swarm_effects as E
    S_, k = {"inv": (LH.INVENTOR, 0.9), "arch": (LH.ZODCHIY, 1.05), "mason": (GH.MASON, 0.85)}[who]
    def mk():
        spr = GH.build(S_, pose, k * Z)
        return E.mirror(spr) if face_left else spr
    return cached(("man", pose, who, face_left, Z), mk)


def leader(name, pose="idle", k=0.6, stage=0):
    import swarm_leaders as SL
    k = k * Z / 1.15
    return cached(("leader", name, pose, k, stage), lambda: SL.build(name, pose, k, stage=stage))


def larva(pose="idle", host=None, k=None):
    import swarm_leaders as SL
    k = Z if k is None else k
    return cached(("larva", pose, host, k), lambda: SL.build("личинка", pose, k, host=host))


def clutch(stage=0, k=0.55):
    import swarm_abilities as SA
    k = k * Z / 1.15
    return cached(("clutch", stage, k), lambda: SA.render_small(SA.clutch(stage), k))


def devourer_winged(pose="attack", k=None):
    k = 0.62 * Z / 1.15 if k is None else k
    """The Devourer with the wings it took from an eaten wasp (Питательная суть)."""
    import swarm_leaders as SL
    from r3d import render
    def mk():
        m = SL.pozhiratel(pose, 0)
        r0 = np.array((0.4, 10.2, 0))
        for z in (-1.2, 1.2):
            sg = np.sign(z)
            mat = W.M_WING if z < 0 else W.M_WING_NEAR
            m.poly([r0 + (0.6, 0.2, z), r0 + (-17.0, 6.0, z + 9.0 * sg), r0 + (-14.0, 11.0, z + 9.5 * sg),
                    r0 + (-5.0, 7.0, z + 5.0 * sg), r0 + (-0.6, 1.2, z + 0.4 * sg)], mat)
            m.limb([r0 + (0.2, 0.4, z), r0 + (-15.6, 8.4, z + 9.0 * sg)], 1, M_VEIN, band=2)
        s = SL.SCALE[5] * k
        w, h, ox, oy = int(110 * s), int(80 * s), int(70 * s), int(66 * s)
        spr = W.rim_light(render(m.scaled(s), w, h, ox, oy, **W.STYLE1))
        spr.ox, spr.oy = ox, oy
        return SL.trim(spr)
    return cached(("devw", pose, k), mk)


def cocoon(k=None):
    k = Z if k is None else k
    from r3d import Model, render
    import swarm_leaders as SL
    def mk():
        m = Model()
        m.ell((0, 2.6, 0), (5.2, 2.6, 2.8), SILK, rot_z(0.15))
        for x in (-3.0, -1.0, 1.0, 3.0):
            m.ell((x, 2.6 + x * 0.15, 0), (0.35, 2.75, 2.95), Mat(W.chitin_shift(SILK, 0.0, light=0.8)), rot_z(0.15))
        for a_, b_ in (((4.8, 3.4, 0), (8.0, 8.0, 0.4)), ((-4.8, 2.0, 0), (-7.6, 0.0, 0.6))):
            m.cyl(np.array(a_), np.array(b_), 0.2, SILK, seg=3)
        spr = W.rim_light(render(m.scaled(k * 1.4), int(40 * k), int(30 * k), int(20 * k), int(24 * k), **W.STYLE1))
        spr.ox, spr.oy = int(20 * k), int(24 * k)
        return SL.trim(spr)
    return cached(("cocoon", k), mk)


# ------------------------------------------------------------------ small 2D marks
def E():
    import swarm_effects
    return swarm_effects


def SA():
    import swarm_abilities
    return swarm_abilities


def put(sc, spr, cx, by, sw=8):
    from leaders_sheet import put as lput
    if sw <= 0:
        sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))
    else:
        lput(sc, spr, cx, by, sw)


def dead(spr):
    return E().lit(spr, (26, 18, 16), 0.72)


def pips(sc, x, y, n, of=4):
    import swarm_status as ST
    ST.pips(sc, x, y, n, of)


def arrow_l(sc, x0, x1, y, col=hexc("#e2b968")):
    for x in range(int(x1), int(x0)):
        E().dot(sc, x, y, col)
    for d in range(1, 5):
        E().dot(sc, x1 + d, y - d, col)
        E().dot(sc, x1 + d, y + d, col)


def arrow_r(sc, x0, x1, y, col=hexc("#e2b968")):
    for x in range(int(x0), int(x1)):
        E().dot(sc, x, y, col)
    for d in range(1, 5):
        E().dot(sc, x1 - d, y - d, col)
        E().dot(sc, x1 - d, y + d, col)


def plus(sc, x, y, col=GREEN, r=3):
    for d in range(-r, r + 1):
        E().dot(sc, x + d, y, col)
        E().dot(sc, x, y + d, col)
    sc.glow(x, y, 7, col, 0.3)


def cloud(sc, x, y, rx, ry, n, col, seed=0):
    rnd = np.random.RandomState(seed)
    for _ in range(n):
        a, r = rnd.uniform(0, 2 * np.pi), np.sqrt(rnd.uniform(0, 1))
        E().dot(sc, x + np.cos(a) * rx * r, y + np.sin(a) * ry * r, col)
    sc.glow(x, y, max(rx, ry), col, 0.2)


def daze(sc, x, y, col=PSI_C):
    """Надлом: a violet crack over the head and stars going round."""
    for i, (dx, dy) in enumerate(((-6, 0), (-2, -4), (1, 1), (5, -5), (8, -1))):
        if i:
            px, py = prev
            for t in np.linspace(0, 1, 6):
                E().dot(sc, px + (x + dx - px) * t, py + (y + dy - py) * t, col)
        prev = (x + dx, y + dy)
    for i in range(4):
        a = i * np.pi / 2 + 0.4
        px, py = x + 1 + np.cos(a) * 12, y + 6 + np.sin(a) * 4
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            E().dot(sc, px + dx, py + dy, col)
        sc.glow(px, py, 5, col, 0.3)


def fear(sc, x, y):
    for dx in (-4, 4):
        for dy in range(-6, 0):
            E().dot(sc, x + dx, y + dy, WHITE_C)
        E().dot(sc, x + dx, y + 2, WHITE_C)
    sc.glow(x, y - 2, 9, WHITE_C, 0.25)


# ------------------------------------------------------------------ what each one does, in battle (x — the middle of the column)
def scene(sc, key, x, by):
    """Draws the scene; returns the caption and text marks [(x, y, text)]."""
    e, sa = E(), SA()
    T = []
    if key == "spinner":
        for r in (8, 16, 24):
            e.ring(sc, x + 26 * F, by, r * 1.6, SILK_C, 0.55, ry=r * 0.45)
        for t in np.linspace(0, np.pi, 7):
            e.lines(sc, (x + 26 * F, by), (x + 26 * F + np.cos(t) * 40, by + np.sin(t) * 12 - 4), SILK_C, 0.55)
        put(sc, golem(), x + 30 * F, by, 0)
        for k_ in range(4):
            e.lines(sc, (x + 16 * F + k_ * 6, by - 2 * F), (x + 20 * F + k_ * 5, by - 26 * F), SILK_C, 0.7)
        put(sc, bug((), key="spinner", seed=5), x - 38 * F, by)
        return "враг застрял в паутине", T
    if key == "exploder":
        put(sc, golem(), x + 24 * F, by, 0)
        e.splash(sc, x + 6 * F, by + 2 * F, 40, hexc("#e8c840"), 0.75)
        e.drops(sc, x - 6 * F, by - 10 * F, hexc("#f0d050"), 12, 22, 1)
        return "лопнула: враг склеен", T
    if key == "bolas":
        put(sc, bug(("ant",), "attack", key="bolas", seed=6), x - 42 * F, by)
        put(sc, man(), x + 40 * F, by)
        sa.thread(sc, (x - 22 * F, by - 18 * F), (x + 30 * F, by - 26 * F), hexc("#e8e0d0"), sag=-4)
        e.blob(sc, x + 32 * F, by - 26 * F, 4, hexc("#f0c040"))
        e.speed(sc, x + 66 * F, by - 4 * F, 3, 14, hexc("#c8bca8"))
        arrow_l(sc, x + 30 * F, x + 4 * F, by + 6 * F)
        return "подтянула врага к рою", T
    if key == "beeball":
        put(sc, golem(), x + 16 * F, by, 0)
        sc.glow(x + 16 * F, by - 22 * F, 40, hexc("#ff9a30"), 0.55)
        e.ring(sc, x + 16 * F, by - 20 * F, 28, hexc("#ffb050"), 0.6, ry=22)
        put(sc, bug((), "attack", key="beeball", seed=7), x - 22 * F, by + 2 * F)
        put(sc, bug((), "attack", key="beeball", seed=8), x - 10 * F, by - 30 * F)
        put(sc, e.mirror(bug((), "attack", key="beeball", seed=9)), x + 58 * F, by + 2 * F)
        return "облепили — давят мимо брони", T
    if key == "pupa":
        put(sc, cocoon(), x - 22 * F, by, 10)
        put(sc, golem("Механик", "attack"), x + 40 * F, by, 0)
        e.burst(sc, x - 10 * F, by - 10 * F, 6)
        put(sc, e.lit(bug(("ant", "wings"), "attack", seed=10), (240, 220, 160), 0.2), x - 30 * F, by - 30 * F)
        e.lines(sc, (x - 22 * F, by - 8 * F), (x - 28 * F, by - 26 * F), SILK_C, 0.6)
        return "кокон — выходит крылатой", T
    if key == "midge":
        put(sc, dead(bug((), key="midge", seed=11)), x - 40 * F, by)
        put(sc, golem("Механик", "attack"), x + 30 * F, by, 0)
        cloud(sc, x + 20 * F, by - 26 * F, 34, 22, 140, hexc("#3a3046"), 3)
        cloud(sc, x + 20 * F, by - 26 * F, 30, 18, 60, hexc("#9a92b4"), 4)
        return "жалит сквозь броню; стрелки не видят", T
    if key == "honey":
        e.splash(sc, x + 26 * F, by + 2 * F, 34, hexc("#e8a028"), 0.8)
        put(sc, golem(), x + 30 * F, by, 0)
        e.drops(sc, x + 26 * F, by - 2 * F, hexc("#ffd070"), 8, 14, 2)
        put(sc, bug((), key="honey", seed=12), x - 38 * F, by)
        put(sc, bug((), "attack", seed=13), x - 12 * F, by + 4 * F)
        plus(sc, x - 8 * F, by - 26 * F)
        return "свои пьют, враг вяз в мёде", T
    if key == "blister":
        put(sc, bug((), key="blister", seed=14), x - 26 * F, by)
        put(sc, man("attack"), x + 32 * F, by)
        e.drops(sc, x + 6 * F, by - 20 * F, RED, 10, 12, 3)
        sc.glow(x + 14 * F, by - 26 * F, 14, RED, 0.6)
        T.append((x + 34 * F, by - 58 * F, "слабее"))
        return "обжёгся — бьёт слабее", T
    if key == "cutters":
        put(sc, golem("Страж", k=0.6), x + 34 * F, by, 0)
        put(sc, bug((), "attack", key="cutters", seed=15), x - 30 * F, by)
        e.burst(sc, x - 2 * F, by - 20 * F, 8)
        for d in ((-4, -30), (2, -36), (-8, -14), (6, -26), (0, -10)):
            e.dot(sc, x + d[0] * F, by + d[1] * F, hexc("#8a7a66"), r=1)
        for k_ in range(6):                                    # the bitten-out notch in the shield
            e.dot(sc, x + (4 + k_) * F, by - (18 + (k_ % 2) * 3) * F, hexc("#140c18"), r=1)
        return "перекусила щит", T
    if key == "guard":
        put(sc, leader("Разум улья", k=0.62), x - 52 * F, by, 10)
        put(sc, bug((), key="guard", seed=16), x - 6 * F, by)
        put(sc, man("attack"), x + 44 * F, by)
        e.slash(sc, x + 12 * F, by - 22 * F, 14, 1.0, 2.6, WHITE_C)
        e.lines(sc, (x + 22 * F, by - 30 * F), (x - 40 * F, by - 34 * F), hexc("#ff8a60"), 0.5)
        return "удар по лидеру — на неё", T
    if key == "regen":
        put(sc, bug((), key="regen", seed=17), x - 10 * F, by)
        for (dx, dy) in ((-18, -30), (2, -40), (16, -26), (-30, -16)):
            plus(sc, x + dx, by + dy)
        put(sc, man(), x + 50 * F, by)
        return "раны затягиваются", T
    # ---- Матка
    if key == "nest":
        put(sc, dead(bug((), key="nest", seed=18)), x - 34 * F, by)
        put(sc, clutch(0, 1.7), x + 10 * F, by, 14)
        put(sc, leader("Матка", k=0.36), x + 58 * F, by, 10)
        return "погибла — яйцо, как у Матки", T
    if key == "nurse":
        put(sc, bug((), key="nurse", seed=19), x - 44 * F, by)
        put(sc, larva(k=Z * 1.4), x - 2 * F, by)
        arrow_r(sc, x + 16 * F, x + 32 * F, by - 10 * F)
        put(sc, e.lit(bug((), seed=20), (240, 220, 160), 0.15), x + 50 * F, by)
        return "личинка дорастает до рабочей", T
    if key == "vivi":
        put(sc, dead(bug(("acid",), key="vivi", seed=6)), x - 14 * F, by + 2 * F, 10)
        put(sc, larva("attack"), x + 30 * F, by, 6)
        return "погибла — личинка", T
    if key == "bud":
        put(sc, golem("Механик", "attack"), x + 40 * F, by, 0)
        for dx, dy, sd in ((-14, -8, 8), (-22, 10, 9)):
            put(sc, bug(("scythes",), "attack", seed=sd), x + dx, by + dy)
        e.burst(sc, x - 18 * F, by - 2 * F, 8, hexc("#c8a0e0"))
        return "ранена — стала двумя", T
    if key == "dominant":
        put(sc, e.lit(bug(("ant", "horn"), key="dominant", seed=21), (255, 220, 120), 0.12), x - 40 * F, by)
        for dx, sd in ((18, 22), (48, 23)):
            put(sc, bug(("ant", "horn"), seed=sd, k=0.9), x + dx, by)
            sa.thread(sc, (x - 30 * F, by - 30 * F), (x + dx, by - 24 * F), hexc("#f0c040"), sag=8)
        return "её черта — у всех потомков", T
    if key == "flight":
        put(sc, bug(("ant",), "attack", key="flight", seed=24), x - 34 * F, by - 18 * F)
        put(sc, e.mirror(bug(("ant", "horn"), "attack", key="flight", seed=25)), x + 34 * F, by - 22 * F)
        sa.thread(sc, (x - 24 * F, by - 46 * F), (x + 24 * F, by - 50 * F), hexc("#f0c040"), sag=10)
        e.stars(sc, x, by - 64 * F, 8, 4)
        return "пару ей выбираешь сам", T
    if key == "hybrid":
        put(sc, bug(("wings",), seed=26, k=0.85), x - 56 * F, by - 26 * F)
        put(sc, bug(("stinger",), seed=27, k=0.85), x - 50 * F, by + 2 * F)
        arrow_r(sc, x - 26 * F, x - 6 * F, by - 12 * F)
        put(sc, bug(("wings", "stinger"), key="hybrid", seed=28), x + 34 * F, by)
        ex, ey = x + 52 * F, by - 22 * F
        e.blob(sc, ex, ey, 4, hexc("#a8d060"), glow=0.2)
        for d in range(-6, 7):
            e.dot(sc, ex + d, ey + d * 0.8, RED)
            e.dot(sc, ex + d, ey - d * 0.8, RED)
        return "оса с жалом скорпиона; бесплоден", T
    if key == "heir":
        put(sc, dead(leader("Матка", k=0.4)), x - 34 * F, by, 10)
        put(sc, bug(("ant",), key="heir", seed=29), x + 38 * F, by)
        sc.glow(x + 38 * F, by - 24 * F, 30, hexc("#f0c040"), 0.45)
        e.ring(sc, x + 42 * F, by - 40 * F, 8, hexc("#f0c040"), 0.8, ry=3)
        return "Матка пала — новая Матка", T
    # ---- Разум улья
    if key == "psi_gland":
        put(sc, bug((), "attack", key="psi_gland", seed=30), x - 26 * F, by)
        put(sc, man(), x + 34 * F, by)
        sc.glow(x + 24 * F, by - 26 * F, 18, PSI_C, 0.6)
        pips(sc, x + 34 * F, by - 62 * F, 3)
        return "укус пси — копит надлом", T
    if key == "psi_reson":
        for i, dx in enumerate((-56, -30)):
            put(sc, bug((), key="psi_reson", seed=31 + i), x + dx, by)
        put(sc, golem(), x + 34 * F, by, 0)
        for i, (cx_, r_) in enumerate(((x - 48 * F, 10), (x - 20 * F, 14), (x + 30 * F, 22))):
            sa.ring(sc, cx_, by - 30 * F - i * 2, r_, r_ * 0.45, PSI_C, 0.75)
        sa.thread(sc, (x - 48 * F, by - 30 * F), (x + 26 * F, by - 36 * F), PSI_C, sag=6)
        return "волна бежит по цепочке", T
    if key == "psi_dread":
        put(sc, man(), x + 34 * F, by)
        daze(sc, x + 34 * F, by - 60 * F)
        put(sc, bug(("jumper",), "attack", key="psi_dread", seed=33), x - 24 * F, by)
        e.burst(sc, x + 18 * F, by - 24 * F, 10, hexc("#ff80b0"))
        return "бьёт надломленного сильнее", T
    if key == "psi_whisper":
        put(sc, bug((), key="psi_whisper", seed=34), x - 30 * F, by)
        put(sc, man(), x + 34 * F, by)
        for r_ in (8, 14, 20):
            sa.ring(sc, x - 4 * F, by - 26 * F, r_ * 0.5, r_, PSI_C, 0.4)
        fear(sc, x + 34 * F, by - 60 * F)
        return "соседи проверяют страх", T
    if key == "strider":
        put(sc, bug(("jumper",), "attack", key="strider", seed=7), x - 34 * F, by)
        for r_ in (10, 18, 26):
            sa.ring(sc, x - 20 * F, by - 18 * F, r_, r_ * 0.8, hexc("#e0d8a0"), 0.5)
        put(sc, golem(), x + 34 * F, by, 0)
        for dy in (-50, -34, -18):
            for k_ in range(3):
                e.dot(sc, x + 50 * F + k_ * 3, by + dy + (k_ % 2) * 2, hexc("#e0d8a0"))
        return "страх; машины дребезжат", T
    if key == "psi_echo":
        put(sc, dead(bug(("acid",), key="psi_echo", seed=35)), x - 30 * F, by + 2 * F, 10)
        put(sc, man(), x + 22 * F, by)
        put(sc, man(who="mason"), x + 58 * F, by + 2 * F)
        for (tx, ty) in ((x + 20 * F, by - 40 * F), (x + 56 * F, by - 30 * F)):
            sa.zigzag2d(sc, (x - 26 * F, by - 20 * F), (tx, ty), PSI_C)
        return "крик бьёт всех рядом", T
    if key == "psi_last":
        put(sc, dead(bug(("acid",), key="psi_last", seed=36)), x - 50 * F, by + 2 * F, 10)
        put(sc, man("attack", face_left=False), x - 2 * F, by)
        put(sc, golem(), x + 50 * F, by, 0)
        sa.zigzag2d(sc, (x - 44 * F, by - 20 * F), (x - 2 * F, by - 54 * F), PSI_C)
        e.slash(sc, x + 26 * F, by - 26 * F, 12, -1.0, 1.2, WHITE_C)
        return "убийца бьёт своих", T
    if key == "psi_leash":
        put(sc, bug(("ant", "horn"), key="psi_leash", seed=37), x - 34 * F, by)
        put(sc, e.lit(man(who="mason", face_left=False), (200, 160, 255), 0.25), x + 30 * F, by)
        sa.thread(sc, (x - 44 * F, by - 22 * F), (x + 28 * F, by - 40 * F), PSI_C, sag=-12)
        e.ring(sc, x + 30 * F, by - 50 * F, 8, PSI_C, 0.8, ry=3)
        return "захваченный держится, пока она жива", T
    if key == "psi_relay":
        put(sc, leader("Разум улья", k=0.42), x - 58 * F, by, 10)
        put(sc, bug((), key="psi_relay", seed=38), x - 6 * F, by)
        sa.thread(sc, (x - 50 * F, by - 44 * F), (x - 12 * F, by - 44 * F), PSI_C, sag=6)
        sa.psi_wave(sc, (x - 4 * F, by - 44 * F), (x + 44 * F, by - 30 * F))
        put(sc, man(), x + 50 * F, by)
        return "Разум бьёт с её места", T
    # ---- Пожиратель
    if key == "sated":
        put(sc, leader("Пожиратель", "attack", k=0.55), x + 26 * F, by, 14)
        put(sc, dead(bug((), key="sated", seed=40)), x - 44 * F, by)
        T.append((x - 44 * F, by - 30 * F, "×2"))
        return "съел — как двоих", T
    if key == "bait":
        e.splash(sc, x + 50 * F, by + 2 * F, 18, RED, 0.8)
        put(sc, dead(bug(("wings",), key="bait", seed=41)), x + 50 * F, by, 0)
        put(sc, leader("Пожиратель", "attack", k=0.5), x - 16 * F, by, 14)
        e.speed(sc, x - 36 * F, by - 14 * F, 4, 18)
        sa.thread(sc, (x + 48 * F, by - 14 * F), (x + 20 * F, by - 30 * F), RED, sag=-8)
        return "бросается к ней напролом", T
    if key == "fattened":
        put(sc, bug((), key="fattened", seed=42), x - 44 * F, by)
        arrow_r(sc, x - 20 * F, x, by - 14 * F)
        put(sc, e.lit(leader("Пожиратель", k=0.5, stage=1), (255, 220, 140), 0.1), x + 40 * F, by, 14)
        return "в Улье на корм — он растёт", T
    if key == "frenzy":
        put(sc, leader("Пожиратель", "attack", k=0.5), x + 34 * F, by, 14)
        for dx, dy, sd in ((-40, 0, 43), (-20, 8, 44)):
            put(sc, e.lit(bug(("scythes",), "attack", key="frenzy", seed=sd), (255, 60, 40), 0.18), x + dx, by + dy)
        sc.glow(x - 30 * F, by - 20 * F, 30, RED, 0.4)
        return "пока он ест — бьют сильнее", T
    if key == "table":
        put(sc, leader("Пожиратель", "attack", k=0.5), x + 34 * F, by, 14)
        for dx, dy, sd in ((-44, 0, 45), (-22, 8, 46)):
            put(sc, bug((), key="table", seed=sd), x + dx, by + dy)
        for (dx, dy) in ((-44, -30), (-22, -24)):
            plus(sc, x + dx, by + dy)
        return "едят с ним и лечатся", T
    if key == "hungry":
        put(sc, dead(man(who="mason")), x + 30 * F, by + 2 * F, 10)
        put(sc, e.lit(bug(("acid",), "attack", key="hungry", seed=47, k=Z * 1.25), (255, 200, 160), 0.08), x - 16 * F, by)
        return "ест павших и растёт", T
    if key == "devblood":
        put(sc, bug((), key="devblood", seed=48), x - 44 * F, by)
        arrow_r(sc, x - 22 * F, x - 4 * F, by - 14 * F)
        put(sc, bug(("ant", "giant"), key="devblood", seed=49), x + 38 * F, by, 12)
        return "её потомки — гиганты", T
    if key == "essence":
        put(sc, dead(bug(("wings",), key="essence", seed=50)), x - 48 * F, by)
        put(sc, devourer_winged(), x + 30 * F, by, 14)
        sa.thread(sc, (x - 44 * F, by - 20 * F), (x + 6 * F, by - 40 * F), hexc("#e8f070"), sag=10)
        e.blob(sc, x - 20 * F, by - 36 * F, 3, hexc("#e8f070"))
        return "съел осу — у него крылья", T
    # ---- Чума
    if key == "parasitoid":
        put(sc, bug(("ant",), "attack", key="parasitoid", seed=51), x - 30 * F, by)
        put(sc, man(), x + 38 * F, by)
        sa.spots(sc, int(x + 34 * F), int(by - 30 * F), [(-4, 0), (3, 6), (0, -8), (5, -2)])
        return "укол — враг заражён", T
    if key == "bloodeggs":
        put(sc, golem("Страж", k=0.62), x + 26 * F, by, 0)
        sa.spots(sc, int(x + 26 * F), int(by - 40 * F), [(-6, 0), (4, 8), (-2, -10), (6, -4), (0, 14)])
        put(sc, larva("attack", host="iron", k=Z * 0.9), x - 22 * F, by, 6)
        put(sc, larva("attack", host="iron", k=Z * 0.9), x - 4 * F, by - 26 * F, 0)
        e.burst(sc, x + 8 * F, by - 30 * F, 6, GREEN)
        return "личинки вышли из живого", T
    if key == "spores":
        put(sc, dead(man(who="mason")), x + 6 * F, by + 2 * F, 10)
        cloud(sc, x + 6 * F, by - 24 * F, 46, 20, 120, hexc("#f09040"), 5)
        put(sc, bug((), seed=52), x - 46 * F, by)
        put(sc, man(), x + 52 * F, by)
        sa.spots(sc, int(x - 46 * F), int(by - 14 * F), [(-3, 0), (3, 3)])
        sa.spots(sc, int(x + 50 * F), int(by - 30 * F), [(-3, 0), (3, 5), (0, -6)])
        return "заражены все соседи", T
    if key == "call":
        put(sc, bug((), seed=53), x - 54 * F, by)
        put(sc, bug(("ant",), key="call", seed=54), x - 32 * F, by + 4 * F)
        for dx, k_ in ((60, 0.75), (44, 0.5)):
            put(sc, e.lit(man(), (40, 30, 60), k_), x + dx, by, 0)
        put(sc, man(), x + 20 * F, by)
        sc.glow(x + 20 * F, by - 50 * F, 12, GREEN, 0.6)
        arrow_l(sc, x + 6 * F, x - 14 * F, by + 6 * F)
        return "заражённый бредёт в рой", T
    if key == "bodyguard":
        put(sc, larva(), x + 2 * F, by + 2 * F, 6)
        put(sc, larva("attack"), x + 18 * F, by + 6 * F, 6)
        put(sc, e.lit(man("attack"), (150, 230, 90), 0.15), x + 46 * F, by)
        put(sc, bug((), "attack", seed=55), x - 40 * F, by)
        e.slash(sc, x - 24 * F, by - 12 * F, 10, 0.6, 2.4, WHITE_C)
        return "стоит над кладкой, бьёт любого", T
    if key == "gnaw":
        put(sc, e.lit(golem(), (120, 200, 80), 0.18), x + 18 * F, by, 0)
        sa.spots(sc, int(x + 18 * F), int(by - 30 * F), [(-6, 0), (4, 6), (0, -8), (6, -2), (-3, 9)])
        plus(sc, x + 52 * F, by - 52 * F, hexc("#70e0ff"))
        arrow_l(sc, x + 46 * F, x + 32 * F, by - 40 * F, hexc("#70e0ff"))
        put(sc, bug(("ant",), key="gnaw", seed=56), x - 44 * F, by)
        T.append((x + 18 * F, by - 72 * F, "слабее"))
        return "кладка ест хозяина; починка — ей", T
    if key == "mutagen":
        put(sc, clutch(2, 0.5), x, by + 4 * F, 10)
        put(sc, larva("attack", host="hand"), x - 44 * F, by, 6)
        put(sc, larva("attack", k=Z * 1.7), x + 4 * F, by, 10)
        put(sc, dead(larva(k=Z * 0.75)), x + 50 * F, by, 4)
        return "вылупилось что попало", T
    if key == "unstable":
        put(sc, bug((), key="spinner", seed=57), x - 40 * F, by)
        arrow_r(sc, x - 12 * F, x + 8 * F, by - 14 * F)
        put(sc, bug((), key="honey", seed=57), x + 40 * F, by)
        T += [(x - 40 * F, by - 58 * F, "раунд 5"), (x + 40 * F, by - 58 * F, "раунд 10")]
        return "каждые 5 раундов — новая черта", T
    if key == "royal":
        put(sc, dead(golem("Страж", k=0.55)), x + 40 * F, by, 0)
        put(sc, e.lit(bug(("horn", "giant"), "attack", chimera="iron", seed=58), (150, 230, 90), 0.12), x - 18 * F, by, 12)
        sc.glow(x - 18 * F, by - 24 * F, 34, GREEN, 0.35)
        return "из Стража — хитиновый Страж", T
    raise KeyError(key)


def nadlom(sc, x, y1, y2):
    """The extra column on the Hive Mind's sheet: what psi does when it has piled up."""
    put(sc, man(), x, y1, 10)
    daze(sc, x, y1 - 54)
    pips(sc, x + 34, y1 - 30, 4)
    g = E().lit(golem(), (30, 28, 40), 0.5)
    put(sc, g, x, y2, 0)
    sc.smoke(x + 4, y2 - 40, 8)


# ------------------------------------------------------------------ the sheets
FILES = {"common": "swarm_mut_common.png", "matka": "swarm_mut_matka.png", "razum": "swarm_mut_razum.png",
         "devourer": "swarm_mut_devourer.png", "cuckoo": "swarm_mut_cuckoo.png"}


def sheet(pid):
    from PIL import ImageFont
    from leaders_sheet import canvas, fonts, S, GOLD, INK, MUT
    from paths import out, font
    import swarm_leaders as SL
    title, lead, sub, items = POOLS[pid]
    items = list(items) + ([("nadlom", "Надлом", "пси копится; больше боевого духа — раунд не действует", None)]
                           if pid == "razum" else [])
    n = len(items)
    per = n if n <= 6 else (n + 1) // 2
    rows = [items[:per], items[per:]] if n > per else [items]
    WW, BAND = 960, 334
    HEAD = 100 if lead else 76
    CWD = min(200, (WW - 40) // per)
    global Z, F
    F = 1.25 if CWD >= 200 else 1.0
    Z = 1.15 * F
    HH = HEAD + BAND * len(rows) + 6
    sc = canvas(WW, HH, 60 + len(pid))
    if lead:
        spr = SL.build(lead, "idle", 1.0)
        k = min(1.0, 92 / spr.h, 150 / spr.w)
        put(sc, SL.build(lead, "idle", k), WW - 90, HEAD - 6, 24)
    marks = []
    for r, row in enumerate(rows):
        top = HEAD + r * BAND
        Y1, Y2, Y3 = top + 62, top + 190, top + 300
        X0 = (WW - CWD * len(row)) / 2 + CWD / 2
        for j, (key, name, what, sec) in enumerate(row):
            cx = X0 + j * CWD
            if key == "nadlom":
                nadlom(sc, cx, Y1, Y2)
                marks.append((cx, Y1, Y2, Y3, name, what, "у голема гаснет искра в ядре", []))
                continue
            put(sc, W.build((), 0.03, "idle", False, k=2.6 * F, genes=W.genes_for(80 + j + r * 7), rare=key), cx, Y1, int(18 * F))
            put(sc, W.build(sec, 0.0, "idle", False, k=2.0 * F, genes=W.genes_for(90 + j + r * 7), rare=key), cx, Y2, int(16 * F))
            cap, T = scene(sc, key, cx, Y3)
            marks.append((cx, Y1, Y2, Y3, name, what, cap, T))
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    small = ImageFont.truetype(font("PTSerif-Regular.ttf"), 14)
    tiny = ImageFont.truetype(font("PTSerif-Bold.ttf"), 13)
    d.text((24, 16), title, font=ft, fill=INK)
    d.text((24, 60), sub[0].upper() + sub[1:], font=fr, fill=MUT)
    d.text((24, 88), "Занимают место детали, наследуются, видны на теле. Ниже тела — что мутация делает в бою.", font=fr, fill=MUT)

    def wrap(t, f, wmax):
        words, lines, cur = t.split(" "), [], ""
        for wd in words:
            if d.textlength(cur + " " + wd, font=f) > wmax and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        return lines + [cur]

    for (cx, Y1, Y2, Y3, name, what, cap, T) in marks:
        X = cx * S
        d.text((X - d.textlength(name, font=fbs) / 2, (Y1 + 10) * S), name, font=fbs, fill=GOLD)
        for n_, ln in enumerate(wrap(what, small, (CWD - 12) * S)[:3]):
            d.text((X - d.textlength(ln, font=small) / 2, (Y1 + 10) * S + 24 + n_ * 18), ln, font=small, fill=MUT)
        for n_, ln in enumerate(wrap(cap, small, (CWD - 8) * S)[:2]):
            d.text((X - d.textlength(ln, font=small) / 2, (Y3 + 14) * S + n_ * 18), ln, font=small, fill=INK)
        for (tx, ty, tt) in T:
            d.text((tx * S - d.textlength(tt, font=tiny) / 2, ty * S), tt, font=tiny, fill=(250, 226, 160))
    img.save(out(FILES[pid]))
    Z, F = 1.15, 1.0
    print(FILES[pid], img.size)


# ------------------------------------------------------------------ a large check of every body
def check(only=None):
    from leaders_sheet import canvas, put, fonts, S, GOLD
    from paths import out
    keys = only or [k for pool in POOLS.values() for (k, *_r) in pool[3]]
    cols, CW_, RH = 9, 110, 120
    rows = (len(keys) + cols - 1) // cols
    sc = canvas(cols * CW_ + 20, rows * RH * 2 + 20, 5)
    for i, key in enumerate(keys):
        cx, by = 60 + (i % cols) * CW_, 90 + (i // cols) * RH * 2
        put(sc, W.build((), 0.03, "idle", False, k=2.4, genes=W.genes_for(30 + i), rare=key), cx, by, 16)
        sec = next(s for pool in POOLS.values() for (k, _n, _w, s) in pool[3] if k == key)
        put(sc, W.build(sec, 0.0, "attack", False, k=1.8, genes=W.genes_for(50 + i), rare=key), cx, by + RH, 16)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    ft, fh, fb, fbs, fr = fonts()
    for i, key in enumerate(keys):
        cx, by = 60 + (i % cols) * CW_, 90 + (i // cols) * RH * 2
        d.text((cx * S - d.textlength(ALL[key][0], font=fr) / 2, (by + 8) * S), ALL[key][0], font=fr, fill=GOLD)
    img.save(out("swarm_mut_check.png"))
    print("swarm_mut_check.png", img.size)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg == "check":
        check(sys.argv[2].split(",") if len(sys.argv) > 2 else None)
    elif arg == "all":
        for pid in POOLS:
            sheet(pid)
    else:
        sheet(arg)
