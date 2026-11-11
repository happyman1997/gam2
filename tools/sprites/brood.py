"""Mock-up of the swarm's between-battles screen: everything hatches, the swarm overflows its limit and the player
eats the extra (new or old, one by one or a whole group) for biomass; biomass spending. Also the brood's finds."""
from PIL import Image, ImageFont
from kit import *
import swarm1 as W
from noise import value_noise
from paths import font, out
import icons as IC
import swarm_ui as UI

S = 2
WW, HH = 960, 540
INK, MUTED, GOLD, BIO = (236, 226, 204), (176, 166, 150), (226, 186, 106), (150, 230, 110)
BADGE = {"гигант": (196, 150, 236), "новая форма": (226, 186, 106), "химера": (236, 120, 96)}


def frame(sc, x0, y0, x1, y1, hi=False, col=None):
    sc.rgb[y0:y1, x0:x1] = hexc("#16121e")
    rim = hexc(col) if col else (hexc("#e2b968") if hi else hexc("#6c7083"))
    dark = rim * 0.5
    sc.rgb[y0, x0:x1] = rim
    sc.rgb[y1 - 1, x0:x1] = dark
    sc.rgb[y0:y1, x0] = rim
    sc.rgb[y0:y1, x1 - 1] = dark
    for (cx, cy) in ((x0, y0), (x1 - 3, y0), (x0, y1 - 3), (x1 - 3, y1 - 3)):
        sc.rgb[cy:cy + 3, cx:cx + 3] = hexc("#7a5aa0")
    sc.occ[y0:y1, x0:x1] = True
    sc.light[y0:y1, x0:x1] = 0


def put(sc, spr, cx, by, sw=0):
    if sw:
        e = ((sc.xx - cx) / sw) ** 2 + ((sc.yy - by) / max(2.5, sw * 0.2)) ** 2
        sc.rgb[e <= 1] *= 0.62
    sc.blit(spr, int(cx - spr.ox), int(by - spr.oy))


LIMIT = 45                       # the swarm's limit in points
# the swarm after hatching, in groups: (traits, soldier, chimera, hue, name, count, new, badge, eat)
GROUPS = [
    ((), False, None, 0.05, "муравей", 19, 0, None, 5),
    ((), True, None, 0.03, "муравей-солдат", 2, 0, None, 0),
    (("wings",), False, None, -0.05, "оса", 3, 0, None, 0),
    (("stinger",), False, None, -0.08, "скорпион", 5, 2, None, 0),
    (("stinger",), True, None, -0.1, "скорпион-солдат", 2, 1, None, 0),
    (("ant", "stinger"), False, None, 0.04, "муравей с гнездом", 1, 1, None, 0),
    (("horn",), True, None, 0.12, "жук-солдат", 2, 1, None, 0),
    (("horn", "wings"), False, None, 0.1, "жук-прядильщик", 1, 1, None, 0),
    (("wings", "stinger"), False, None, -0.04, "оса-скорпион", 1, 1, None, 0),
    (("carapace",), True, None, 0.0, "мокрица-солдат", 1, 0, None, 0),
    (("acid",), False, "hand", 0.0, "бочонок с рукой", 1, 1, "химера", 0),
    (("scythes",), False, None, 0.06, "богомол", 1, 1, "новая форма", 0),
]
SELECTION = (("жало", 23, "stinger"), ("рог", 11, "horn"), ("кислота", 7, "acid"), ("серпы", 4, "scythes"))
KID_ICON = {"химера": "hand", "новая форма": "scythes"}
# mutations in the groups: (key, mark); a leader's own pool is marked in the leader's colour, the common pool in silver
MUTS = {5: ("nest", "мутация Матки"), 7: ("spinner", "общая мутация"), 8: ("hybrid", "гибрид · бесплоден")}
POOL_COL = {"Матка": (240, 200, 90), "Разум улья": (196, 150, 255), "Пожиратель": (236, 96, 80), "Кукушка": (150, 220, 90),
            "общая": (206, 206, 222), "бесплоден": (240, 140, 140)}
MARK_COL = {"мутация Матки": POOL_COL["Матка"], "общая мутация": POOL_COL["общая"], "гибрид · бесплоден": POOL_COL["бесплоден"]}
GX0, GY0, GCW, GCH, GCOLS = 12, 92, 232, 100, 4
BX0, BX1 = 300, 930


def pts(g):
    return 3 if g[1] else 1


def totals():
    total = sum(pts(g) * g[5] for g in GROUPS)
    eaten = sum(pts(g) * g[8] for g in GROUPS)
    return total, eaten


def icon(img, key, x, y, px):
    """Paste a swarm icon (16×16, nearest) of px pixels with its top-left at (x, y)."""
    im = Image.fromarray(IC.icon_rgba(key, "swarm"), "RGBA").resize((px, px), Image.NEAREST)
    img.paste(im, (int(x), int(y)), im)


def build():
    sc = UI.nest(WW, HH, 31)
    UI.wing(sc, 0, 0, WW, 30)
    # the limit as an abdomen: one segment per point; the ones over the limit red, the marked hatched
    UI.plate(sc, 12, 38, 948, 84)
    total, eaten = totals()
    UI.segbar(sc, BX0, 62, BX1, 12, total, LIMIT, eaten)
    # the groups
    for k, (traits, soldier, chim, hue, name, count, new, badge, eat) in enumerate(GROUPS):
        x0 = GX0 + (k % GCOLS) * (GCW + 2)
        y0 = GY0 + (k // GCOLS) * (GCH + 4)
        UI.cell(sc, x0, y0, x0 + GCW, y0 + GCH, "eat" if eat else ("new" if new else "normal"))
        mut = MUTS.get(k, (None,))[0]
        spr = W.build(traits, hue, "idle", soldier, k=1.3 if soldier else 1.7, chimera=chim, genes=W.genes_for(k * 7 + 3), rare=mut)
        put(sc, spr, x0 + 52, y0 + GCH - 22, 14 if not soldier else 18)
        if count > 1:                                  # a second one behind: it is a group
            spr2 = W.build(traits, hue + 0.03, "idle", soldier, k=1.05 if soldier else 1.35, chimera=chim, genes=W.genes_for(k * 7 + 4), rare=mut)
            put(sc, spr2, x0 + 30, y0 + GCH - 40, 0)
            sc.blit(spr, int(x0 + 52 - spr.ox), int(y0 + GCH - 22 - spr.oy))
        for bx, kind in ((x0 + GCW - 56, "blood"), (x0 + GCW - 30, "chitin")):    # − and + buttons
            UI.button(sc, bx, y0 + GCH - 30, bx + 24, y0 + GCH - 8, kind)
    UI.plate(sc, 12, 402, 948, 442)
    for i, (_, kills, _) in enumerate(SELECTION):           # kills by trait: little abdomens too
        x = 250 + i * 176
        UI.meter(sc, x + 70, 418, x + 160, 8, 12, round(12 * kills / 23), "#c04a3a" if i == 0 else "#8a6aa8")
    for (x0, x1) in ((12, 236), (246, 470), (480, 704), (714, 948)):
        UI.button(sc, x0, 452, x1, 490, "acid")
    for (x0, x1, kind) in ((12, 236, "chitin"), (246, 470, "chitin"), (714, 948, "dim")):
        UI.button(sc, x0, 498, x1, 534, kind)
    return sc


def overlay(img):
    d = ImageDraw.Draw(img)
    f = UI.f
    total, eaten = totals()
    over = total - LIMIT
    d.text((20, 18), "Выводок · после боя 5 из 14 · вылупились все — съешь лишних", font=f(1, 24), fill=INK)
    t = f"Биомасса 34  +{eaten} за съеденных"
    tx = WW * S - 24 - d.textlength(t, font=f(1, 21))
    d.text((tx, 15), t, font=f(1, 21), fill=BIO)
    icon(img, "biomass", tx - 40, 10, 34)
    d.text((28, 44 * S), f"Предел роя: {total} / {LIMIT} очков", font=f(1, 20), fill=(240, 140, 110))
    d.text((28, 60 * S + 4), f"лишних {over} · отмечено к съедению {eaten} · осталось {over - eaten}", font=f(0, 16), fill=MUTED)
    d.text(((BX0 + LIMIT * (BX1 - BX0) / total) * S - 24, 44 * S), "предел", font=f(0, 15), fill=INK)
    for k, (traits, soldier, chim, hue, name, count, new, badge, eat) in enumerate(GROUPS):
        x0 = (GX0 + (k % GCOLS) * (GCW + 2)) * S
        y0 = (GY0 + (k // GCOLS) * (GCH + 4)) * S
        d.text((x0 + 200, y0 + 14), name, font=f(1, 17), fill=INK)
        d.text((x0 + 200, y0 + 42), f"×{count}", font=f(1, 26), fill=INK)
        d.text((x0 + 262, y0 + 52), f"{pts(GROUPS[k]) * count} оч.", font=f(0, 15), fill=MUTED)
        y = y0 + 88
        if new:
            d.text((x0 + 200, y), f"новых {new}", font=f(1, 15), fill=(150, 220, 120))
            y += 22
        if badge:
            icon(img, KID_ICON[badge], x0 + 198, y - 4, 26)
            d.text((x0 + 228, y), badge, font=f(1, 15), fill=BADGE[badge])
            y += 22
        if k in MUTS:
            key, mark = MUTS[k]
            icon(img, "m_" + key, x0 + 198, y - 4, 26)
            d.text((x0 + 228, y), mark, font=f(1, 15), fill=MARK_COL[mark])
            y += 22
        if eat:
            d.text((x0 + 200, y), f"съесть {eat}: +{eat * pts(GROUPS[k])} биомассы", font=f(1, 15), fill=(240, 120, 96))
        bx = x0 + (GCW - 56) * S
        by = y0 + (GCH - 30) * S
        d.text((bx + 20, by + 12), "−", font=f(0, 16), fill=INK)
        d.text((bx + 26 * S + 20, by + 12), "+", font=f(0, 16), fill=INK)
    icon(img, "selection", 34, 405 * S, 34)
    d.text((74, 412 * S), "Естественный отбор — убийства по чертам:", font=f(1, 16), fill=INK)
    for i, (name, kills, key) in enumerate(SELECTION):
        x = (250 + i * 176) * S
        icon(img, key, x + 18, 405 * S, 34)
        d.text((x + 58, 411 * S), name, font=f(0, 16), fill=INK)
        d.text((x + 330, 411 * S), str(kills), font=f(1, 14), fill=MUTED)
    spend = [(12, 236, "Кормление · 10: кладка +1", "feed"), (246, 470, "Эволюция формы · 15", "evolve"),
             (480, 704, "Ещё кладка · 10", "clutch"), (714, 948, "Перебросить · 5", "reroll")]
    for x0, x1, t, key in spend:
        tw = d.textlength(t, font=f(1, 17))
        d.text(((x0 + x1) * S / 2 - tw / 2 + 20, 464 * S), t, font=f(1, 17), fill=UI.INK)
        icon(img, key, (x0 + x1) * S / 2 - tw / 2 - 26, 455 * S, 40)
    for x0, x1, t, col in ((12, 236, "Автоотбор", INK), (246, 470, "Съесть всех новых", INK),
                           (714, 948, f"В бой — съешь ещё {over - eaten}", (130, 120, 140))):
        d.text(((x0 + x1) * S / 2 - d.textlength(t, font=f(0, 16)) / 2, 509 * S), t, font=f(0, 16), fill=col)
    t = "Съеденное очко предела — биомасса."
    d.text(((480 + 704) * S / 2 - d.textlength(t, font=f(0, 15)) / 2, 508 * S), t, font=f(0, 15), fill=MUTED)


# ---------------------------------------------------------------- finds: the brood's other offers
FINDS = [
    ("Чистая линия", "выжили двое одной формы", "3 потомка той же формы, без мутаций: порода закрепляется"),
    ("Кокон", "рабочая убила больше всех", "окукливается и выходит солдатом с теми же чертами"),
    ("Приблудная стая", "бой со зверями или роем", "3 дикие особи формы, которой у вас нет"),
    ("Яйцо гиганта", "бой с боссом", "из яйца выйдет гигант формы одного из родителей"),
    ("Химерная кладка", "рой съел живых врагов", "у одного-двух потомков чужая черта"),
]


def cocoon_model():
    """A pupa in silk: a spindle wound with threads, the dark head-end of the creature showing."""
    from r3d import Model, Mat, rot_z
    import swarm_leaders as SL
    silk = Mat(ramp("#2a2622", "#5a544a", "#948c7e", "#c8c0b0", "#f0eadc"))
    m = Model()
    R = rot_z(0.35)
    c = np.array((0.0, 5.0, 0.0))
    m.ell(c, (6.0, 2.8, 2.8), silk, R)
    for t in np.linspace(-0.75, 0.75, 6):
        p = c + R @ np.array((t * 6.0, 0, 0))
        r = 2.85 * np.sqrt(1 - t * t)
        m.ell(p, (0.35, r, r), SL.M_GRUB_SEG, R)
    m.ell(c + R @ np.array((5.6, 0, 0)), (1.2, 1.4, 1.4), Mat(W.chitin(0.0)))
    for a, b in (((-4.0, 3.2, 1.5), (-6.2, 0.0, 2.6)), ((-2.0, 2.6, -1.6), (-3.4, 0.0, -2.8)), ((3.0, 6.2, 0.0), (4.6, 12.0, 0.0))):
        m.limb([np.array(a), np.array(b)], 1, silk, band=2)
    return m


def giant_egg_model():
    from r3d import Model, Mat
    import swarm_leaders as SL
    m = Model()
    c = np.array((0.0, 5.6, 0.0))
    m.ell(c, (4.6, 5.6, 4.6), SL.M_EGG_IN)
    m.ell(c + (1.4, 2.2, 1.6), (1.0, 1.4, 0.6), SL.M_GRUB)
    for a in np.linspace(0, 2 * np.pi, 7)[:-1]:
        p0 = c + np.array((np.cos(a) * 3.6, -3.0, np.sin(a) * 3.6))
        p1 = c + np.array((np.cos(a + 0.4) * 4.4, 1.6, np.sin(a + 0.4) * 4.4))
        p2 = c + np.array((np.cos(a + 0.2) * 3.0, 4.6, np.sin(a + 0.2) * 3.0))
        m.limb([p0, p1, p2], 1, SL.M_VEIN_R, band=2)
    for x, z in ((-6.0, 2.0), (5.6, 2.6), (-4.6, -2.4)):
        m.ell((x, 1.15, z), (1.35, 1.15, 1.15), W.M_EGG)
    m.ell((0, 0.1, 0.4), (8.0, 0.15, 5.0), SL.M_EGG_IN)
    return m


def finds():
    from swarm_abilities import render_small
    WW_, HH_ = 960, 272
    sc = UI.nest(WW_, HH_, 33)
    UI.wing(sc, 0, 0, WW_, 30)
    CW_ = 184
    xs = [12 + i * (CW_ + 4) for i in range(5)]
    for i, x0 in enumerate(xs):
        UI.cell(sc, x0, 44, x0 + CW_, 262, "find")
        sc.glow(x0 + CW_ / 2, 150, 90, hexc("#7ae040"), 0.10)
    by = 176
    # Чистая линия: three scorpions alike
    x0 = xs[0]
    for j, dx in enumerate((46, 92, 140)):
        put(sc, W.build(("stinger",), -0.08 + 0.01 * j, "idle", False, k=1.9, genes=W.genes_for(3)), x0 + dx, by - (16 if j == 1 else 0), 16)
    # Кокон: a worker, its cocoon, the soldier it becomes
    x0 = xs[1]
    put(sc, W.build(("ant", "horn"), 0.05, "idle", False, k=1.8, genes=W.genes_for(8)), x0 + 32, by, 12)
    put(sc, render_small(cocoon_model().scaled(1.5), 2.2), x0 + 90, by, 20)
    put(sc, W.build(("ant", "horn"), 0.05, "idle", True, k=1.8, genes=W.genes_for(8)), x0 + 148, by, 18)
    # Приблудная стая: three wild fireflies
    x0 = xs[2]
    for j, (dx, dy) in enumerate(((50, 0), (96, -18), (138, 2))):
        put(sc, W.build(("firefly",), 0.08 * (j - 1), "idle", False, k=1.9, genes=W.genes_for(40 + j)), x0 + dx, by + dy, 14)
    # Яйцо гиганта
    x0 = xs[3]
    put(sc, render_small(giant_egg_model(), 2.4, size=2), x0 + 92, by, 40)
    # Химерная кладка
    x0 = xs[4]
    put(sc, W.build(("acid",), 0.0, "idle", False, k=1.9, chimera="hand", genes=W.genes_for(50)), x0 + 54, by, 16)
    put(sc, W.build(("ant",), 0.05, "idle", False, k=1.9, chimera="face", genes=W.genes_for(51)), x0 + 134, by, 14)
    img = sc.image(S)
    d = ImageDraw.Draw(img)
    f = UI.f
    d.text((20, 18), "Выводок: находки вместо одной из кладок", font=f(1, 24), fill=INK)
    t = "обычно две кладки и одна находка; какая — зависит от прошедшего боя"
    d.text((WW_ * S - 24 - d.textlength(t, font=f(0, 17)), 18), t, font=f(0, 17), fill=MUTED)
    icons_ = ["evolve", "larva", "ant", "clutch", "hand"]
    for i, (x0, (name, when, what)) in enumerate(zip(xs, FINDS)):
        cx = (x0 + CW_ / 2) * S
        nw = d.textlength(name, font=f(1, 19))
        d.text((cx - nw / 2 + 18, 56 * S), name, font=f(1, 19), fill=GOLD)
        icon(img, icons_[i], cx - nw / 2 - 22, 56 * S - 4, 34)
        d.text((cx - d.textlength(when, font=f(0, 14)) / 2, 76 * S), when, font=f(0, 14), fill=MUTED)
        words, lines, cur = what.split(" "), [], ""
        for wd in words:
            if d.textlength(cur + " " + wd, font=f(0, 15)) > (CW_ - 16) * S and cur:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        lines.append(cur)
        for k, ln in enumerate(lines):
            d.text((cx - d.textlength(ln, font=f(0, 15)) / 2, (by + 26) * S + k * 22), ln, font=f(0, 15), fill=INK)
    img.save(out("brood_finds.png"))
    print("brood_finds.png", img.size)


# ---------------------------------------------------------------- what the leaders' pools add to the brood
def pools():
    import swarm_leaders as SL
    import swarm_status as ST
    WW_, HH_ = 960, 330
    sc = UI.nest(WW_, HH_, 35)
    UI.wing(sc, 0, 0, WW_, 30)
    PW_ = 232
    xs = [12 + i * (PW_ + 2) for i in range(4)]
    for x0 in xs:
        UI.cell(sc, x0, 40, x0 + PW_, 320, "find")
    # Брачный полёт: she, and the survivors to choose her pair from
    x0 = xs[0]
    she = W.build(("ant",), 0.05, "attack", False, k=1.9, genes=W.genes_for(61), rare="flight")
    put(sc, she, x0 + 60, 150, 14)
    cands = [(("horn",), True, 62), (("stinger",), False, 63), (("wings",), False, 64)]
    for j, (tr, sol, sd) in enumerate(cands):
        cy = 92 + j * 62
        UI.cell(sc, x0 + 128, cy, x0 + 222, cy + 56, "hi" if j == 1 else "normal")
        put(sc, W.build(tr, 0.0, "idle", sol, k=1.0 if sol else 1.35, genes=W.genes_for(sd)), x0 + 160, cy + 46, 8)
    import swarm_abilities as SA
    SA.thread(sc, (x0 + 76, 112), (x0 + 132, 178), hexc("#f0c040"), sag=8)
    UI.button(sc, x0 + 16, 276, x0 + PW_ - 16, 308, "amber")
    # Гибрид: two parents of two forms; the hybrid, which will never pair
    x0 = xs[1]
    put(sc, W.build(("wings",), 0.0, "idle", False, k=1.3, genes=W.genes_for(65)), x0 + 60, 112, 8)
    put(sc, W.build(("stinger",), -0.08, "idle", False, k=1.3, genes=W.genes_for(66)), x0 + 170, 112, 10)
    SA.thread(sc, (x0 + 70, 100), (x0 + 160, 100), hexc("#c0c0d0"), sag=6)
    hyb = W.build(("wings", "stinger"), -0.04, "idle", False, k=2.1, genes=W.genes_for(67), rare="hybrid")
    put(sc, hyb, x0 + 110, 236, 16)
    ex, ey = x0 + 190, 214
    sc.rgb[ey - 6:ey + 7, ex - 5:ex + 6] = hexc("#2a3a14")
    E = __import__("swarm_effects")
    E.blob(sc, ex, ey, 5, hexc("#a8d060"), glow=0.1)
    for dd in range(-8, 9):
        E.dot(sc, ex + dd, ey + dd * 0.9, hexc("#e04a3a"))
        E.dot(sc, ex + dd, ey - dd * 0.9, hexc("#e04a3a"))
    # Откормленная: fat grows battle by battle; fed to the Devourer between battles, he grows at once
    x0 = xs[2]
    fat = W.build((), 0.05, "idle", False, k=1.9, genes=W.genes_for(68), rare="fattened")
    put(sc, fat, x0 + 56, 150, 14)
    for i in range(5):                                # fat: battles survived
        cx_ = x0 + 26 + i * 14
        sc.rgb[176:184, cx_ - 5:cx_ + 5] = hexc("#e8c070") if i < 3 else hexc("#3a3040")
        sc.rgb[176, cx_ - 5:cx_ + 5] = hexc("#140c18")
        sc.rgb[183, cx_ - 5:cx_ + 5] = hexc("#140c18")
    SA.arrow(sc, x0 + 104, x0 + 128, 140)
    put(sc, SL.build("Пожиратель", "idle", 0.42, stage=1), x0 + 180, 160, 18)
    UI.button(sc, x0 + 16, 276, x0 + PW_ - 16, 308, "blood")
    # the marks: whose pool a mutation is from
    x0 = xs[3]
    return sc, xs, PW_


def pools_overlay(img, xs, PW_):
    d = ImageDraw.Draw(img)
    f = UI.f
    d.text((20, 18), "Выводок: что добавляют пулы лидеров", font=f(1, 24), fill=INK)
    heads = [("Брачный полёт", "пару ей выбираешь сам", "m_flight"),
             ("Гибрид", "бесплоден: в пары не встаёт", "m_hybrid"),
             ("Откормленная", "только у Пожирателя", "m_fattened"),
             ("Отметки мутаций", "чей пул — тот и цвет", "m_nest")]
    for (x0, (h, sub, key)) in zip(xs, heads):
        cx = (x0 + PW_ / 2) * S
        w = d.textlength(h, font=f(1, 19))
        icon(img, key, cx - w / 2 - 22, 50 * S - 4, 34)
        d.text((cx - w / 2 + 18, 50 * S), h, font=f(1, 19), fill=GOLD)
        d.text((cx - d.textlength(sub, font=f(0, 15)) / 2, 70 * S), sub, font=f(0, 15), fill=MUTED)
    x = xs[0] * S
    for j, t in enumerate(("жук-солдат", "скорпион", "оса")):
        d.text(((xs[0] + 175) * S - d.textlength(t, font=f(0, 13)) / 2, (92 + j * 62 + 4) * S), t, font=f(0, 13),
               fill=GOLD if j == 1 else MUTED)
    d.text((x + 30, 214 * S), "она", font=f(0, 15), fill=INK)
    d.text((x + 30, 230 * S), "с кем — решаешь ты,", font=f(0, 15), fill=INK)
    d.text((x + 30, 230 * S + 22), "не стык стай", font=f(0, 15), fill=INK)
    t = "Спарить со скорпионом"
    d.text(((xs[0] + PW_ / 2) * S - d.textlength(t, font=f(1, 16)) / 2, 286 * S), t, font=f(1, 16), fill=UI.DARK)
    x = xs[1] * S
    for k, t in enumerate(("оса × скорпион", "тело осы, жало скорпиона —", "способности обеих форм;",
                           "в пары не встаёт, каждого", "выводят заново")):
        if k == 0:
            d.text(((xs[1] + PW_ / 2) * S - d.textlength(t, font=f(0, 14)) / 2, 122 * S), t, font=f(0, 14), fill=MUTED)
        else:
            d.text(((xs[1] + PW_ / 2) * S - d.textlength(t, font=f(0, 14)) / 2, (246 + (k - 1) * 9.5) * S), t,
                   font=f(0, 14), fill=INK)
    x = xs[2] * S
    d.text((x + 26, 190 * S), "жир: пережила 3 боя", font=f(0, 15), fill=(232, 192, 112))
    for k, t in enumerate(("чем дольше держишь —", "тем больше он вырастет;", "пока жива — производитель")):
        d.text((x + 26, 212 * S + k * 20), t, font=f(0, 15), fill=INK)
    t = "Скормить Пожирателю"
    d.text(((xs[2] + PW_ / 2) * S - d.textlength(t, font=f(1, 16)) / 2, 286 * S), t, font=f(1, 16), fill=INK)
    x = xs[3] * S
    rows = [("m_nest", "мутация Матки", POOL_COL["Матка"]), ("m_psi_gland", "пси-мутация Разума", POOL_COL["Разум улья"]),
            ("m_sated", "мутация Пожирателя", POOL_COL["Пожиратель"]), ("m_spores", "мутация Кукушки", POOL_COL["Кукушка"]),
            ("m_spinner", "общая мутация", POOL_COL["общая"]), ("m_hybrid", "гибрид · бесплоден", POOL_COL["бесплоден"])]
    for k, (key, t, col) in enumerate(rows):
        y = (100 + k * 34) * S
        icon(img, key, x + 24, y - 6, 40)
        d.text((x + 76, y + 4), t, font=f(1, 16), fill=col)
    t = "отметка у группы в выводке и на карточке особи"
    d.text(((xs[3] + PW_ / 2) * S - d.textlength(t, font=f(0, 13)) / 2, 306 * S), t, font=f(0, 13), fill=MUTED)


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["finds"]:
        finds()
        raise SystemExit
    if sys.argv[1:] == ["pools"]:
        sc, xs, PW_ = pools()
        img = sc.image(S)
        pools_overlay(img, xs, PW_)
        img.save(out("brood_pools.png"))
        print("brood_pools.png", img.size)
        raise SystemExit
    sc = build()
    img = sc.image(S)
    overlay(img)
    img.save(out("brood.png"))
    print(img.size)
