"""The swarm's own settings, pause and defeat — the same screens as the Foundry's (foundry_hud), in the nest's wax
and chitin instead of iron and brass.

  settings — sections on wax cells left (each its own little bug-drawn icon: a compound eye for the screen, a
             chirping cricket for sound, a comb cell for the game, a chitin-grown key for keys), the rows right.
             The controls are the swarm's: a groove gnawed in the wax with comb cells for its notches and a drop
             of amber for the slider (a level fills the groove with glowing ichor), a firefly's lantern in a
             chitin socket for on and off, a pair of mandibles round a wax window for a list. On ЭКРАН the
             interface's size in whole steps, the ones this screen can't take gnawed through, and a window in
             the comb showing how much of the screen the interface takes.
  pause    — over the battle: a plate with antennae, the run's place in a line, the acid button to carry on,
             the rest on chitin; giving up is blood.
  defeat   — the nest gone dark: the leader on its back in a broken comb, its last larvae, wax flakes drifting
             down; the run summed up and how little was missing; what the run opened and what is next.

    python3 tools/sprites/swarm_menus.py   -> out/swarm_settings*.png, out/swarm_pause.png, out/swarm_defeat.png
"""
import numpy as np
from kit import hexc, BAYER, Sprite
import swarm_ui as UI
import swarm_hud as SH
from swarm_hud import letters, heading, title, help_button, fx_line, fx_rows, glyph, icon, put, keycap, act_button, \
    cursor, INK, MUTED, GOLD, DARK
from swarm_hud import PALE
from paths import out
from noise import value_noise

WW, HH, S = SH.WW, SH.HH, SH.S
WAX = ("#3a2410", "#5e3c16", "#8a5a1e", "#b8822e")
ICHOR = ("#3a6a10", "#6aa020", "#a8e040", "#e0ff90")


# ---------------------------------------------------------------- the swarm's controls
def ui_icon(sc, key, x, y, z=2):
    import swarm_icons_drawn as D
    rgba = np.repeat(np.repeat(D.UI[key](), z, 0), z, 1)
    m = rgba[..., 3] > 0
    sc.rgb[y:y + rgba.shape[0], x:x + rgba.shape[1]][m] = rgba[..., :3][m]


def button(sc, x0, y0, x1, y1, text, kind="chitin", big=False):
    """A swarm button with its word: acid moves on, chitin goes back or aside, blood loses something."""
    if kind == "acid":
        return act_button(sc, x0, y0, x1, y1, text, key=None)
    UI.button(sc, x0, y0, x1, y1, kind)
    col = {"blood": (255, 200, 180), "chitin": INK, "dim": PALE}.get(kind, INK)
    letters(sc, text, (x0 + x1) / 2, (y0 + y1) / 2 - 9, "title" if big else "text", 16, col=col, align="center")


def bead(sc, bx, y):
    """The slider: a drop of amber with a gnat caught in it, lit on its top left."""
    X, Y = sc.xx - bx, sc.yy - y
    drop = (X / 7.0) ** 2 + (((Y + 1) / 9.0) ** 2) * (1 + 0.25 * (Y < 0)) <= 1
    sh = np.roll(np.roll(drop, 2, 0), 2, 1) & ~drop
    sc.rgb[sh] *= 0.45
    sc.rgb[np.roll(drop, 1, 0) | np.roll(drop, -1, 0) | np.roll(drop, 1, 1) | np.roll(drop, -1, 1)] = UI.OUTL
    t = np.clip(0.5 - X / 14.0 - Y / 18.0, 0, 1)
    lv = np.clip((t * 4 + (BAYER[sc.yy % 4, sc.xx % 4] - 0.5) * 0.5).astype(int), 0, 3)
    for i, c in enumerate(("#8a4a0c", "#c07018", "#e8a030", "#ffd070")):
        sc.rgb[drop & (lv == i)] = hexc(c)
    sc.rgb[y:y + 2, bx - 1:bx + 2] = hexc("#2a1606")                   # the gnat in it
    sc.rgb[y - 1, bx - 2] = hexc("#2a1606")
    sc.rgb[y - 1, bx + 2] = hexc("#2a1606")
    sc.rgb[y - 5:y - 3, bx - 3] = hexc("#fff0c0")


def groove(sc, x0, x1, y, n, value, labels=None, off=(), ichor=False):
    """A groove gnawed in the wax, comb cells for its notches, the amber drop at value (a notch, or between for a
    level); ichor — the groove behind the drop filled with glowing ichor (a level: the volume). Labels under the
    notches: the chosen gold, the ones that can't be chosen pale and gnawed through."""
    n_ = value_noise(sc.w, sc.h, 3, 41)
    ch = (sc.xx >= x0) & (sc.xx <= x1) & (np.abs(sc.yy - y) <= 3 + (n_ > 0.6))
    sc.rgb[(sc.xx >= x0 - 2) & (sc.xx <= x1 + 2) & (np.abs(sc.yy - y) <= 6)] = hexc(WAX[1])
    sc.rgb[(sc.xx >= x0 - 2) & (sc.xx <= x1 + 2) & (sc.yy == y - 6)] = hexc(WAX[3])
    sc.rgb[(sc.xx >= x0 - 2) & (sc.xx <= x1 + 2) & (sc.yy == y + 6)] = hexc(WAX[0])
    sc.rgb[ch] = hexc("#0e0a10")
    xs = [x0 + (x1 - x0) * k / max(1, n - 1) for k in range(n)]
    bx = int(x0 + (x1 - x0) * value / max(1, n - 1))
    if ichor and bx > x0:
        m = ch & (sc.xx <= bx)
        t = np.clip((sc.yy - (y - 4)) / 8.0, 0, 1)[..., None]
        sc.rgb[m] = (hexc(ICHOR[3]) * (1 - t) + hexc(ICHOR[1]) * t)[m]
        sc.glow((x0 + bx) // 2, y, max(8, (bx - x0) // 2), hexc(ICHOR[2]), 0.12)
        for k in range(x0 + 5, bx - 4, 13):                             # bubbles in it
            sc.rgb[y - 1, k] = hexc("#f4ffd0")
    for k, x in enumerate(xs):
        if ichor and n > 6:
            continue
        hexm = SH.hexmask(sc, int(x), y, 6)
        sc.rgb[hexm] = hexc(WAX[2])
        sc.rgb[SH.hexmask(sc, int(x), y, 4)] = hexc("#0e0a10") if not (ichor and x <= bx) else hexc(ICHOR[2])
    bead(sc, bx, y)
    if labels:
        for k, (x, t) in enumerate(zip(xs, labels)):
            chosen = abs(k - value) < 0.01
            col = GOLD if chosen else (PALE if k in off else MUTED)
            letters(sc, t, int(x), y + 12, "text", 16, col=col, align="center")
            if k in off:                                                 # gnawed through
                w = UI.text_width(t, "text", 16)
                for xx in range(int(x - w / 2 - 2), int(x + w / 2 + 3)):
                    yy = y + 21 + int(2 * np.sin(xx * 0.9))
                    sc.rgb[yy:yy + 2, xx] = hexc("#1a1418")


def lantern(sc, x, y, on):
    """On and off: a firefly's lantern in a chitin socket — lit acid-yellow when on, a dull grey husk when off."""
    X, Y = sc.xx - x, sc.yy - y
    d = np.hypot(X, Y * 1.1)
    if on:
        sc.glow(x, y, 20, hexc("#e8f070"), 0.35)
    sc.rgb[d <= 12] = UI.OUTL
    sc.rgb[d <= 11] = hexc("#3a2a3a")
    sc.rgb[(d <= 11) & (X + Y < -6)] = hexc("#5a465a")
    seg = d <= 7.5
    sc.rgb[seg] = UI.OUTL
    body = d <= 6.5
    if on:
        t = np.clip(0.6 - (X + Y) / 14.0, 0, 1)[..., None]
        sc.rgb[body] = (hexc("#a8b020") * (1 - t) + hexc("#f8ffa0") * t)[body]
    else:
        sc.rgb[body] = hexc("#4a4838")
        sc.rgb[body & (X + Y < -4)] = hexc("#6a6650")
    for k in (-3, 0, 3):                                                 # its segments
        sc.rgb[(np.abs(Y - k) < 0.6) & body] *= 0.7


def mandibles(sc, x0, x1, y, text):
    """One of a list: a pair of mandibles either side of a dark wax window, the value in it."""
    UI.cell(sc, x0 + 22, y - 14, x1 - 22, y + 14, "normal")
    letters(sc, text, (x0 + x1) // 2, y - 8, "text", 16, col=GOLD, align="center")
    for side in (-1, 1):
        cx = x0 + 10 if side < 0 else x1 - 10
        for k in range(12):                                              # a curved jaw, its tip pointing out
            a = k / 11.0
            px_ = int(cx + side * (6 * a - 4))
            py_ = int(y - 9 + 18 * a)
            w = 3 if 0.2 < a < 0.8 else 2
            sc.rgb[py_ - 1:py_ + 2, px_ - w:px_ + w + 1] = UI.OUTL
        for k in range(12):
            a = k / 11.0
            px_ = int(cx + side * (6 * a - 4) + side * np.sin(a * np.pi) * 3)
            py_ = int(y - 9 + 18 * a)
            sc.rgb[py_, px_ - 1:px_ + 2] = hexc("#8a5a3a")
            sc.rgb[py_, px_ - side] = hexc("#c8946a")
        sc.rgb[y - 1:y + 2, cx + side * 4:cx + side * 4 + 3 * side:side or 1] = hexc("#e8c08a")


def scale_window(sc, x0, y0, w, h, frac, chosen=False):
    """A window in the comb showing how much of the screen the interface takes at a scale: a swarm screen shrunk
    to frac of the width, the nest round it where the canvas grew."""
    from PIL import Image
    UI.cell(sc, x0 - 6, y0 - 6, x0 + w + 6, y0 + h + 6, "hi" if chosen else "normal")
    nest = UI.nest(w, h, 3)
    sc.rgb[y0:y0 + h, x0:x0 + w] = nest.rgb * 0.8
    try:
        shot = Image.open(out("swarm_camp.png")).convert("RGB")
    except FileNotFoundError:
        return
    tw, th = int(round(w * frac)), int(round(h * frac))
    small = np.asarray(shot.resize((tw, th), Image.BOX)).astype(float)
    ox, oy = x0 + (w - tw) // 2, y0 + (h - th) // 2
    sc.rgb[oy:oy + th, ox:ox + tw] = small


SETTINGS = [("screen", "ЭКРАН"), ("sound", "ЗВУК"), ("game", "ИГРА"), ("keys", "КЛАВИШИ")]


def settings(section="screen", ret=False, anim=None):
    sc = SH.frame_screen(57)
    UI.wing(sc, 0, 0, WW, 44)
    UI.drips(sc, 200, 760, 44, "#b06818", n=5, seed=23)
    title(sc, "НАСТРОЙКИ", seed=41)
    help_button(sc)
    UI.plate(sc, 12, 52, 196, 462, antennae=True)
    for i, (key, nm) in enumerate(SETTINGS):
        y0 = 62 + i * 52
        on = key == section
        UI.cell(sc, 20, y0, 188, y0 + 44, "hi" if on else "normal")
        ui_icon(sc, key, 30, y0 + 6, 2)
        letters(sc, nm, 70, y0 + 14, "text", 16, col=GOLD if on else INK, jitter=1, seed=i)
    UI.plate(sc, 206, 52, 948, 462)
    heading(sc, dict(SETTINGS)[section], 222, 62, seed=7)
    lab = lambda t, y, sub=None: (letters(sc, t, 224, y - 8, "text", 16, col=INK),
                                  sub and letters(sc, sub, 224, y + 10, "text", 16, col=MUTED))
    rule = lambda y: UI.silk(sc, (222, y), (934, y), sag=3, col="#8a6a34", k=0.6)
    a_ = anim or {}
    if section == "screen":
        lab("Режим окна", 104)
        groove(sc, 430, 690, 104, 3, 2, ["окно", "без рамки", "весь экран"])
        lab("Разрешение", 158)
        mandibles(sc, 430, 690, 158, "2560 × 1440")
        rule(186)
        letters(sc, "Масштаб интерфейса", 224, 196, "text", 16, col=GOLD)
        letters(sc, "крупнее или мельче —", 224, 216, "text", 16, col=MUTED)
        letters(sc, "целыми шагами,", 224, 234, "text", 16, col=MUTED)
        letters(sc, "пиксели ровные", 224, 252, "text", 16, col=MUTED)
        sv = a_.get("scale", 1.0)
        groove(sc, 430, 690, 214, 4, sv, ["×1", "×2", "×3", "×4"], off=(2, 3))
        letters(sc, "мельче", 430, 254, "text", 16, col=MUTED)
        letters(sc, "крупнее", 690, 254, "text", 16, col=MUTED, align="right")
        fx_line(sc, 430, 280, "на этом экране: ×1 или ×2")
        letters(sc, "×3 и ×4 не помещаются", 430, 300, "text", 16, col=PALE)
        scale_window(sc, 730, 200, 176, 99, 0.375 + 0.375 * sv, True)
        letters(sc, "×2: холст 1280 × 720" if sv >= 0.5 else "×1: холст 2560 × 1440", 818, 312, "text", 16,
                col=GOLD, align="center")
        rule(334)
        lab("Вертикальная синхронизация", 356)
        on = a_.get("vsync", True)
        lantern(sc, 470, 356, on)
        letters(sc, "вкл" if on else "выкл", 496, 348, "text", 16, col=INK if on else MUTED)
        lab("Частота кадров", 412)
        groove(sc, 430, 690, 404, 4, 3, ["60", "120", "144", "без предела"])
    elif section == "sound":
        for j, (nm, v) in enumerate((("Общая громкость", 8), ("Музыка", 6), ("Звуки боя", 9), ("Интерфейс", 7))):
            y = 110 + j * 56
            lab(nm, y)
            groove(sc, 430, 820, y, 11, v, ichor=True)
            letters(sc, str(v * 10), 900, y - 8, "text", 16, col=GOLD, align="right")
        lab("Звук в фоне", 352, "когда окно не в фокусе")
        lantern(sc, 470, 352, False)
        letters(sc, "выкл", 496, 344, "text", 16, col=MUTED)
    elif section == "game":
        lab("Скорость боя", 104, "с какой начинается бой")
        groove(sc, 430, 690, 104, 3, 1, ["×1", "×2", "×4"])
        lab("Подсказки", 170, "задержка")
        groove(sc, 430, 690, 170, 3, 1, ["сразу", "0,3 с", "0,6 с"])
        lab("Подписи значков", 236)
        groove(sc, 430, 690, 236, 3, 0, ["держать Alt", "Alt включает", "всегда"])
        lab("Язык", 300)
        mandibles(sc, 430, 690, 300, "Русский")
        lab("Тряска экрана", 352)
        lantern(sc, 470, 352, True)
        letters(sc, "вкл", 496, 344, "text", 16, col=INK)
        lab("Вспышки ударов", 400)
        lantern(sc, 470, 400, True)
        letters(sc, "вкл", 496, 392, "text", 16, col=INK)
    else:
        rows = [("Пауза", "Пробел"), ("Скорость боя", "Tab"), ("Бой — в конец", "End"), ("Подписи значков", "Alt"),
                ("Справочник", "F1"), ("Главное действие", "Enter"), ("Назад, закрыть", "Esc")]
        for j, (nm, key) in enumerate(rows):
            y = 100 + j * 44
            hot = j == 3
            UI.cell(sc, 216, y - 18, 938, y + 18, "hover" if hot else "normal")
            letters(sc, nm, 230, y - 8, "text", 16, col=GOLD if hot else INK)
            if hot:
                letters(sc, "нажмите клавишу…", 700, y - 8, "text", 16, col=(200, 250, 120), align="right")
            else:
                keycap(sc, 560, y - 10, key)
        letters(sc, "клавиша, занятая другим, подсвечивается красным", 222, 440, "text", 16, col=MUTED)
    UI.wing(sc, 0, 468, WW, HH)
    button(sc, 12, 478, 200, 526, "Назад", "chitin")
    button(sc, 210, 478, 420, 526, "По умолчанию", "chitin")
    act_button(sc, 640, 472, 948, 532, "ПРИМЕНИТЬ")
    UI.cobweb(sc, 196, 52, 26, quad=(1, 1))
    if ret:
        return sc
    name = "swarm_settings.png" if section == "screen" else f"swarm_settings_{section}.png"
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out(name))
    print(name, img.size)


def pause(ret=False):
    """Pause, over the battle: the field dimmed, a plate with antennae in the middle — the run's place in a line,
    the acid button to carry on, the rest on chitin; giving up is blood."""
    sc = SH.battle_hud(ret=True)
    sc.rgb[:] = sc.rgb * 0.36
    x0, y0, x1, y1 = 330, 80, 630, 462
    UI.plate(sc, x0, y0, x1, y1, antennae=True)
    UI.wing(sc, x0 + 4, y0 + 4, x1 - 4, y0 + 44)
    tw = UI.text_width("ПАУЗА", "title", 24)
    letters(sc, "ПАУЗА", (x0 + x1) // 2 - tw // 2, y0 + 12, "title", 24, col=(176, 244, 70), col2=(70, 150, 50),
            jitter=1, hairs=3, seed=3)
    UI.drips(sc, x0 + 20, x1 - 20, y0 + 44, "#b06818", n=4, seed=29)
    fx_line(sc, x0 + 24, y0 + 62, "бой 5 из 15 · ход 5 · {биомасса:14}")
    act_button(sc, x0 + 16, y0 + 90, x1 - 16, y0 + 146, "ПРОДОЛЖИТЬ", key=None)
    for j, (t, kind) in enumerate((("Настройки", "chitin"), ("Справочник · F1", "chitin"), ("Сдаться", "blood"),
                                   ("Выйти в меню", "chitin"), ("Выйти из игры", "chitin"))):
        yy = y0 + 162 + j * 36
        button(sc, x0 + 24, yy, x1 - 24, yy + 30, t, kind)
    letters(sc, "Esc — продолжить", (x0 + x1) // 2, y1 - 22, "text", 16, col=MUTED, align="center")
    if ret:
        return sc
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_pause.png"))
    print("swarm_pause.png", img.size)


def flip_dead(spr, k=0.5):
    """A body on its back, its colour gone grey."""
    f = Sprite(spr.w, spr.h)
    grey = spr.rgb.mean(axis=2, keepdims=True)
    f.rgb = (spr.rgb * (1 - k) + grey * k)[::-1] * 0.6
    f.a = spr.a[::-1].copy()
    f.ox, f.oy = spr.ox, spr.h - 1 - spr.oy + 4
    return f


def dark_nest(sc, m, k):
    """The nest gone dark over a region: colour drained toward a cold grey, dimmed."""
    grey = sc.rgb.mean(axis=2, keepdims=True) * np.array([0.92, 0.94, 1.0])
    sc.rgb[m] = (sc.rgb * (1 - k) + grey * k)[m] * (1 - 0.25 * k)


def defeat(name="Матка", ret=False, anim=None):
    """Defeat, and the run summed up. The nest has gone dark: the title grey without its acid, flakes of wax
    drifting down. Left, the leader on its back in a broken comb, its dead brood round it, a last larva still
    twitching. In the middle what the run came to, and how little was missing. Right, what the run opened, and
    what is next."""
    import swarm_leaders as SL
    fr_ = (anim or {}).get("frame", 0)
    sc = SH.frame_screen(97)
    UI.wing(sc, 0, 0, WW, 44)
    tw = UI.text_width("ПОРАЖЕНИЕ", "title", 24)
    x = WW // 2 - tw // 2
    letters(sc, "ПОРАЖЕНИЕ", x, 6, "title", 24, col=(176, 178, 186), col2=(56, 58, 68), jitter=1, drips=2, seed=11)
    help_button(sc)
    dark_nest(sc, sc.yy < 44, 0.5)
    # left: the leader on its back in a broken comb
    UI.plate(sc, 12, 52, 330, 462)
    heading(sc, "ЧТО ОСТАЛОСЬ", 26, 62, seed=5)
    SH.FILL[name](sc, 22, 88, 320, 404)
    X, Y = sc.xx, sc.yy
    rnd = np.random.RandomState(4)
    for _ in range(9):                                                   # cells broken out of the comb
        hx, hy, r = rnd.randint(36, 306), rnd.randint(100, 330), rnd.randint(9, 15)
        n_ = value_noise(sc.w, sc.h, 3, hx)
        hole = SH.hexmask(sc, hx, hy, r) | (SH.hexmask(sc, hx, hy, r + 2) & (n_ > 0.7))
        rim = SH.hexmask(sc, hx, hy, r + 3) & ~hole
        sc.rgb[rim & (n_ > 0.35)] = hexc("#a07028")
        sc.rgb[hole] = hexc("#0a080c")
        sc.rgb[hole & (sc.yy > hy + r * 0.5)] = hexc("#140e10")
    k_ = {"Матка": 0.95, "Разум улья": 1.9, "Пожиратель": 1.6, "Чума": 1.8}[name]
    body = flip_dead(SL.build(name, "idle", k_))
    bottom = np.nonzero(body.a.any(axis=1))[0].max()
    sc.blit(body, int(171 - body.ox), int(390 - bottom), emit=False)
    sc.rgb[396:404, 22:320] = hexc("#1a1418")
    dark_nest(sc, (X >= 22) & (X < 320) & (Y >= 88) & (Y < 404), 0.6)
    for j, (dx, tr) in enumerate(((-118, ()), (-78, ("wings",)), (92, ("stinger",)), (128, ()), (-36, ("horn",)))):
        b = flip_dead(SH.bug(tr, "idle", 1.35, 400 + j), 0.3)               # its dead brood on the floor round it
        bottom = np.nonzero(b.a.any(axis=1))[0].max()
        bx, by = int(171 + dx - b.ox), int(395 - bottom)
        rim = np.zeros((b.h + 2, b.w + 2), bool)                          # a cold pale rim, so they read in the dark
        for oy, ox in ((0, 1), (2, 1), (1, 0), (1, 2)):
            rim[oy:oy + b.h, ox:ox + b.w] |= b.a
        rim[1:-1, 1:-1] &= ~b.a
        ys, xs = np.nonzero(rim)
        ok = (by + ys - 1 >= 0) & (by + ys - 1 < sc.h) & (bx + xs - 1 >= 0) & (bx + xs - 1 < sc.w)
        sc.rgb[by + ys[ok] - 1, bx + xs[ok] - 1] = hexc("#5a5866")
        sc.blit(b, bx, by, emit=False)
    lv = SH.larva("idle", 0.7)                                           # the last larva, still twitching
    lx, ly = 250 + (1 if (fr_ // 3) % 4 == 0 else 0), 392
    sc.blit(lv, int(lx - lv.ox), int(ly - lv.oy - (1 if (fr_ // 3) % 4 == 1 else 0)), emit=False)
    fx_line(sc, 26, 420, "{гибель} лидер · бой 8 из 15")
    letters(sc, "рой рассыпался", 26, 440, "text", 16, col=MUTED)
    # the middle: what the run came to
    UI.plate(sc, 340, 52, 626, 462)
    heading(sc, "ИТОГ ПОХОДА", 354, 62, seed=6)
    rows = (("атака", "дошёл до боя", "8 из 15"), ("лидер", "боссов побеждено", "1"),
            ("убийство", "врагов убито", "538"), ("биомасса", "биомассы набрано", "112"),
            ("выводок", "особей выведено", "1 240"))
    y = 96
    for g, lab, val in rows:
        a_ = glyph(sc, g, 354, y - 4, 2)
        letters(sc, lab, 354 + a_ + 8, y - 2, "text", 16, col=MUTED)
        w = UI.text_width(val, "text", 16)
        for xx in range(354 + a_ + 14 + UI.text_width(lab, "text", 16), 610 - w - 6, 4):
            sc.rgb[y + 10, xx] = sc.rgb[y + 10, xx] * 0.4 + np.array(MUTED) * 0.6
        letters(sc, val, 610, y - 2, "text", 16, col=INK, align="right")
        y += 24
    UI.cell(sc, 350, y + 4, 616, y + 70, "hi")                           # the best of the breed
    put(sc, SH.bug(("wings", "stinger"), "idle", 0.9, 77), 390, y + 62, 14)
    letters(sc, "лучшая — оса с жалом", 432, y + 12, "text", 16, col=GOLD, jitter=1, seed=2)
    fx_line(sc, 432, y + 36, "{убийство:71} · 4 поколения")
    y += 84
    heading(sc, "НЕ ХВАТИЛО", 354, y, seed=8)
    y += 28
    glyph(sc, "лидер", 354, y - 2, 2)
    letters(sc, "Зодчий", 380, y, "text", 16, col=(240, 180, 120))
    UI.meter(sc, 450, y + 4, 610, 7, 10, 2, "#d08a3a")
    letters(sc, "у него оставалось 22 прочности —", 354, y + 26, "text", 16, col=INK)
    letters(sc, "одна стая ос", 354, y + 44, "text", 16, col=INK)
    # the right: what the run opened, and what is next
    UI.plate(sc, 634, 52, 948, 462)
    heading(sc, "ОТКРЫТО", 648, 62, seed=9)
    for j, (key, nm, sub) in enumerate((("m_honey", "Медовые соты", "мутация · в общем пуле"),
                                        ("m_pupa", "Куколка", "мутация · в общем пуле"))):
        y0 = 90 + j * 66
        UI.cell(sc, 642, y0, 940, y0 + 58, "new")
        UI.cell(sc, 650, y0 + 8, 692, y0 + 50, "normal")
        icon(sc, key, 655, y0 + 13, 2)
        letters(sc, nm, 704, y0 + 10, "text", 16, col=GOLD)
        letters(sc, sub, 704, y0 + 30, "text", 16, col=MUTED)
    heading(sc, "ДАЛЬШЕ ОТКРОЕТСЯ", 648, 236, seed=10)
    for j, (nm, cond, have, need) in enumerate((("Пожиратель", "победить 2-го босса", 1, 2),
                                                ("Чума", "дойти до 12-го боя", 8, 12),
                                                ("Сложность II", "пройти поход", 0, 1))):
        y0 = 264 + j * 62
        UI.cell(sc, 642, y0, 940, y0 + 54, "normal")
        letters(sc, nm, 654, y0 + 6, "text", 16, col=INK)
        letters(sc, f"{have} из {need}", 928, y0 + 6, "text", 16, col=MUTED, align="right")
        letters(sc, cond, 654, y0 + 28, "text", 16, col=MUTED)
        bx0, bx1 = 820, 928
        sc.rgb[y0 + 34:y0 + 40, bx0:bx1] = hexc("#08070a")
        fill = int(bx0 + (bx1 - bx0) * have / need)
        if fill > bx0:
            sc.rgb[y0 + 34:y0 + 40, bx0:fill] = hexc(ICHOR[1])
            sc.rgb[y0 + 34, bx0:fill] = hexc(ICHOR[3])
    rnd = np.random.RandomState(8)
    for k in range(50):                                                  # flakes of wax drifting down, a loop of 36
        ax0, ay0 = rnd.randint(0, WW), rnd.randint(44, 466)
        ay_ = 44 + (ay0 - 44 + fr_ * (1 + k % 2)) % 422
        ax_ = int(ax0 + 3 * np.sin((ay_ + k * 13) / 26.0)) % (WW - 2)
        c = hexc("#8a6a3a") if k % 3 else hexc("#a8a4ac")
        sc.rgb[ay_, ax_:ax_ + 2] = sc.rgb[ay_, ax_:ax_ + 2] * 0.4 + c * 0.6
    UI.wing(sc, 0, 468, WW, HH)
    button(sc, 12, 478, 220, 526, "В меню", "chitin")
    act_button(sc, 640, 472, 948, 532, "НОВЫЙ ПОХОД")
    if ret:
        return sc
    img = sc.image(S)
    UI.WOBBLE[0] = 0.0
    img.save(out("swarm_defeat.png"))
    print("swarm_defeat.png", img.size)


if __name__ == "__main__":
    import sys
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    if arg in ("all", "settings"):
        for sec, _ in SETTINGS:
            settings(sec)
    if arg in ("all", "pause"):
        pause()
    if arg in ("all", "defeat"):
        defeat()
