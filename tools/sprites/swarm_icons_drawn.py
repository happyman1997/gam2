"""The swarm's icons drawn in code, pixel by pixel, the same way as the module icons (icons_drawn.py) — no image
under them — in the swarm's own ramps (icons.R: chitin, rust, amber, acid, membrane…), the light from the top
left, our dark outline outside. Bugs are side on, facing right, like the swarm's creatures on the field.

    python3 tools/sprites/swarm_icons_drawn.py traits    -> out/swicons_traits.png (a batch, large and in a cell)
    python3 tools/sprites/swarm_icons_drawn.py atlas     -> assets/swarm_icons.png, .json (same cells and keys)
"""
import numpy as np
import icons as IC
from icons_drawn import Pix, grid, flame

NEW = {}


def icon(key):
    def reg(f):
        NEW[key] = f
        return f
    return reg


def ell(cx, cy, rx, ry):
    return grid(lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0)


def legs(p, roots, ramp="chitin", lv=1, spread=1.0, foot=13):
    """Thin jointed legs from the body down to the ground: each root (x, y) goes out to a knee and down."""
    for k, (x, y) in enumerate(roots):
        d = (k - (len(roots) - 1) / 2) * spread
        kx, ky = round(x + d), y + 1
        p.line([(x, y), (kx, ky), (round(kx + d * 0.6), foot)], ramp, lv)


def antennae(p, x, y, ramp="chitin", lv=3, long=4, elbow=True):
    if elbow:
        p.line([(x, y), (x + 1, y - 2), (x + long, y - 3)], ramp, lv)
    else:
        p.line([(x, y), (x + long, y - long)], ramp, lv)


# ---------------------------------------------------------------- the swarm's traits: one bug for each
@icon("ant")
def ant():
    """Муравей: a plain worker ant — round head with its jaws, a narrow thorax, the waist, a big oval gaster."""
    p = Pix()
    legs(p, [(6, 8), (8, 8), (10, 8)], spread=1.6)
    p.fill(ell(4.0, 8.0, 3.2, 2.4), "chitin", inner=(3, 2))        # the gaster
    p.fill(ell(8.5, 7.5, 1.8, 1.2), "chitin", inner=(3, 2))        # the thorax
    p.fill(ell(12.0, 6.5, 1.9, 1.7), "chitin", inner=(3, 2))       # the head
    p.px(13, 6, "rust", 4)                                         # its eye
    p.line([(13, 8), (14, 9)], "rust", 3)                          # its jaws
    antennae(p, 12, 5, long=3)
    return p.done()


@icon("wings")
def wasp():
    """Крылья · оса: a wasp — the striped amber and black abdomen ending in its sting, the narrow waist, two
    clear wings raised over its back."""
    p = Pix()
    legs(p, [(8, 9), (10, 9)], spread=1.4)
    ab = ell(4.5, 9.0, 3.4, 2.4)
    p.fill(ab, "amber", inner=(3, 2))
    for x in (3, 6):
        for y in range(16):
            if ab[y, x] or ab[y, x - 1]:
                p.px(x, y, "chitin", 1)                            # its black bands
    p.px(0, 10, "chitin", 2)                                       # the sting
    p.fill(ell(9.5, 8.5, 1.8, 1.5), "chitin", inner=(3, 2))        # the thorax
    p.fill(ell(12.8, 8.0, 1.6, 1.5), "amber", inner=(3, 2))        # the head
    p.px(13, 7, "chitin", 1)
    for (cx, cy, rx, ry) in ((7.0, 4.5, 3.0, 1.6), (10.0, 3.5, 2.6, 1.4)):
        p.fill(ell(cx, cy, rx, ry), "slate", inner=(4, 3), rim=4, shade=2)   # the wings
    antennae(p, 13, 7, long=2, elbow=False)
    return p.done()


@icon("stinger")
def scorpion():
    """Жало · скорпион: a scorpion side on, low to the ground — its claws reaching forward, its segmented tail
    curling up over its back, the sting at the tip hooked down."""
    p = Pix()
    legs(p, [(6, 11), (8, 11), (10, 11)], ramp="rust", spread=1.2, foot=14)
    p.fill(ell(8.0, 10.5, 4.6, 1.8), "rust", inner=(3, 2))         # the body
    for (cx, cy) in ((3.0, 9.0), (2.0, 7.0), (2.5, 5.0), (4.0, 3.5), (6.0, 3.0)):
        p.fill(ell(cx, cy, 1.2, 1.2), "rust", inner=(3, 2))        # the tail's segments
    p.line([(7, 3), (8, 4), (8, 5)], "crimson", 4)                 # the sting
    p.fill(ell(13.0, 9.0, 1.6, 1.1), "rust", inner=(3, 2))         # the claw
    p.line([(14, 8), (15, 7)], "rust", 3)
    p.line([(14, 10), (15, 10)], "rust", 2)
    return p.done()


@icon("acid")
def acid_bug():
    """Кислотная железа · бочонок: a beetle carrying a swollen gland of acid for a belly — glowing green through the
    skin, a drop falling off it."""
    p = Pix()
    legs(p, [(7, 10), (9, 10), (11, 10)], spread=1.2)
    p.fill(ell(5.5, 7.5, 4.3, 3.6), "acid", inner=(3, 2), rim=4, shade=1)   # the gland
    p.px(4, 5, "lantern", 4)                                       # its shine
    p.fill(ell(11.0, 8.5, 2.0, 1.6), "chitin", inner=(3, 2))       # thorax
    p.fill(ell(13.5, 8.0, 1.5, 1.4), "chitin", inner=(3, 2))       # head
    p.px(14, 7, "acid", 4)
    p.px(5, 12, "acid", 3)                                         # a drop
    p.px(5, 13, "acid", 2)
    antennae(p, 14, 7, long=2, elbow=False)
    return p.done()


@icon("horn")
def horn_beetle():
    """Рог · жук: a rhinoceros beetle — its domed wing cases shining, the long curved horn sweeping up off its
    head."""
    p = Pix()
    legs(p, [(5, 11), (8, 11), (10, 11)], spread=1.2, foot=14)
    p.fill(ell(6.5, 8.5, 5.0, 3.6), "elytra", inner=(3, 2))        # the wing cases
    p.line([(6, 5), (6, 12)], "elytra", 1)                         # their seam
    p.px(4, 6, "elytra", 4)
    p.px(3, 7, "elytra", 4)
    p.fill(ell(12.2, 9.0, 1.8, 1.6), "chitin", inner=(3, 2))       # the head
    p.line([(13, 8), (14, 6), (14, 4), (13, 2)], "chitin", 3)      # the horn
    p.px(14, 5, "chitin", 4)
    return p.done()


@icon("carapace")
def woodlouse():
    """Панцирь · мокрица: a woodlouse — a low dome of overlapping grey plates, a row of little legs under it."""
    p = Pix()
    for x in range(3, 13, 2):
        p.line([(x, 12), (x - 1, 13)], "slate", 1)                 # the little legs
    dome = grid(lambda x, y: ((x - 7.5) / 6.6) ** 2 + ((y - 11.5) / 6.0) ** 2 <= 1 and y <= 11)
    p.fill(dome, "slate", inner=(3, 2))
    for x in (4, 6, 8, 10, 12):                                    # the plates' edges
        for y in range(16):
            if dome[y, x] and not dome[y - 1, x]:
                p.px(x, y, "slate", 4)
            if dome[y, x] and y > 7:
                p.px(x, y, "slate", 1)
    p.px(14, 10, "slate", 2)                                       # its head and feelers
    p.line([(14, 9), (15, 7)], "slate", 3)
    return p.done()


@icon("jumper")
def grasshopper():
    """Прыгучие ноги · кузнечик: a grasshopper — the long body, its huge hind leg folded: the thick thigh running
    back and up to the knee over its tail, the shin folded down under it, ready to spring; feelers forward."""
    p = Pix()
    p.fill(ell(7.5, 9.5, 5.6, 1.8), "olive", inner=(3, 2))         # the body
    p.fill(ell(13.0, 8.5, 1.8, 1.8), "olive", inner=(3, 2))        # the head
    p.px(14, 8, "chitin", 1)
    p.line([(11, 10), (12, 13)], "olive", 1)                       # front legs
    p.line([(9, 10), (9, 13)], "olive", 1)
    p.tube(8.0, 8.5, 2.5, 4.5, 1.3, "olive", levels=(4, 3, 2))    # the hind thigh, back and up
    p.line([(2, 5), (4, 9), (7, 13)], "olive", 2)                  # its shin, folded down under
    p.line([(14, 7), (15, 3)], "olive", 3)                         # feelers, forward
    p.line([(13, 7), (13, 2)], "olive", 3)
    return p.done()


@icon("scythes")
def mantis():
    """Серпы · богомол: a mantis reared up — wings folded along its back, the long neck, the triangle head, the
    two scythe forelegs folded up in front of its chest, spined, their blades bright."""
    p = Pix()
    p.fill(ell(4.5, 11.0, 3.8, 1.7), "mantis", inner=(3, 2))       # the abdomen
    p.fill(ell(4.0, 9.5, 3.2, 0.9), "olive", inner=(3, 2))         # the folded wings
    p.tube(7.0, 10.0, 9.5, 4.0, 0.9, "mantis", levels=(4, 3, 2))   # the neck
    head = grid(lambda x, y: 8 <= x <= 12 and 1 <= y <= 3 and abs(x - 10) <= 3 - (y - 1))
    p.fill(head, "mantis", inner=(3, 2))
    p.px(11, 1, "acid", 4)                                         # its eye
    p.line([(9, 5), (13, 5)], "mantis", 3)                         # the scythe: upper arm forward
    p.line([(13, 5), (12, 9)], "mantis", 2)                        # folded back down
    p.line([(14, 5), (13, 9)], "steel", 4)                         # its blade
    for x, y in ((11, 6), (11, 8)):
        p.px(x, y, "mantis", 4)                                    # spines
    legs(p, [(4, 12), (7, 11)], ramp="mantis", spread=1.4, foot=14)
    return p.done()


@icon("firefly")
def firefly():
    """Светлячок · светляк: a firefly in flight — dark wing cases spread, its tail a lantern of cold yellow light
    glowing out round it."""
    p = Pix()
    p.fill(ell(4.5, 9.5, 3.4, 2.4), "lantern", inner=(4, 3), rim=4, shade=2)   # the lantern
    for x, y in ((0, 9), (1, 12), (1, 6), (4, 13)):
        p.px(x, y, "lantern", 3)                                   # its glow
    p.fill(ell(9.5, 8.5, 2.6, 1.8), "chitin", inner=(3, 2))        # the body
    p.fill(ell(13.0, 8.0, 1.5, 1.4), "chitin", inner=(3, 2))       # the head
    p.px(14, 7, "rust", 4)
    p.fill(ell(8.0, 5.0, 3.0, 1.4), "elytra", inner=(3, 2))        # wing cases, lifted
    p.fill(ell(10.5, 4.0, 2.6, 1.2), "slate", inner=(4, 3), rim=4, shade=2)   # the wing under them
    antennae(p, 13, 7, long=2, elbow=False)
    return p.done()


@icon("spitter")
def spitter():
    """Клейкие железы · паук-плевун: a spider, its round abdomen, eight arched legs, spitting a gob of glue off its
    jaws."""
    p = Pix()
    for k, (x, y) in enumerate(((6, 9), (7, 9), (8, 9), (9, 9))):
        d = k - 1.5
        p.line([(x, y), (round(x + d * 2.4), 5 + abs(round(d))), (round(x + d * 3.6), 13)], "chitin", 1 + k % 2)
    p.fill(ell(4.0, 8.5, 3.4, 3.0), "chitin", inner=(3, 2))        # the abdomen
    p.px(3, 7, "crimson", 4)                                       # its mark
    p.px(4, 8, "crimson", 3)
    p.fill(ell(9.0, 9.0, 2.0, 1.6), "chitin", inner=(3, 2))        # the head
    for x in (9, 10):
        p.px(x, 8, "crimson", 4)                                   # eyes
    p.disc(13.5, 7.0, 1.6, "bone", levels=(4, 3, 2))               # the glue
    p.px(12, 8, "bone", 3)
    return p.done()


# ---------------------------------------------------------------- chimeras: what the swarm took from others
@icon("iron")
def iron_shell():
    """Железный панцирь: a beetle's back grown over with a plate of riveted iron, torn off something it ate."""
    p = Pix()
    legs(p, [(5, 11), (8, 11), (10, 11)], spread=1.2, foot=14)
    p.fill(ell(7.0, 8.5, 5.4, 3.6), "chitin", inner=(3, 2))
    plate = grid(lambda x, y: 3 <= x <= 10 and 5 <= y <= 9 and not (x in (3, 10) and y == 5))
    p.fill(plate, "iron", inner=(3, 2))
    for x, y in ((4, 6), (9, 6), (4, 8), (9, 8)):
        p.px(x, y, "brass", 4)                                     # rivets
    p.fill(ell(12.8, 9.0, 1.7, 1.5), "chitin", inner=(3, 2))
    p.px(13, 8, "rust", 4)
    return p.done()


@icon("boil")
def boiling_blood():
    """Кипящая кровь: a big drop of blood seething — bubbles breaking on it, steam curling off the top."""
    p = Pix()
    drop = grid(lambda x, y: ((x - 7.5) / 4.6) ** 2 + ((y - 10.0) / 4.4) ** 2 <= 1 or (y < 10 and abs(x - 7.5) <= (y - 3) * 0.7))
    p.fill(drop, "crimson", inner=(3, 2))
    for cx, cy, r in ((6.0, 9.0, 1.0), (9.0, 11.5, 0.8), (8.5, 7.5, 0.7)):
        p.disc(cx, cy, r, "worm", levels=(4, 3))                   # bubbles
    p.px(5, 8, "petal", 4)
    for x, y, lv in ((6, 1, 3), (9, 0, 2), (10, 2, 3)):
        p.px(x, y, "slate", lv)                                    # steam
    return p.done()


@icon("hand")
def human_hand():
    """Человеческая рука: a human hand, pale, its four fingers spread apart and the thumb out, grown out of a
    joint of chitin at the wrist."""
    p = Pix()
    p.rect(5, 13, 9, 14, "chitin", [3, 1])                         # the chitin it grows out of
    palm = grid(lambda x, y: 4 <= x <= 10 and 8 <= y <= 12 and not (x in (4, 10) and y == 12))
    p.fill(palm, "skin", inner=(3, 2))
    for x, top in ((4, 4), (6, 2), (8, 2), (10, 3)):
        p.col(x, top, 7, "skin", [4, 3, 3, 3, 3, 2])               # fingers, one pixel apart
    p.line([(11, 10), (13, 8), (14, 7)], "skin", 3)                # the thumb
    return p.done()


@icon("face")
def human_face():
    """Человеческое лицо: a pale human face, eyes shut, set into the front of a bug's head."""
    p = Pix()
    p.fill(ell(7.5, 8.0, 6.4, 6.0), "chitin", inner=(3, 2))        # the bug's head round it
    p.fill(ell(7.5, 8.5, 4.2, 4.8), "skin", inner=(3, 2))          # the face
    for x in (5, 6, 9, 10):
        p.px(x, 7, "skin", 1)                                      # shut eyes
    p.px(7, 9, "skin", 2)                                          # the nose
    p.px(8, 10, "skin", 2)
    p.rect(6, 11, 9, 11, "crimson", [2])                           # the mouth
    for x, y in ((3, 2), (12, 2)):
        p.line([(x + (1 if x < 7 else -1), 4), (x, y), (x - (1 if x < 7 else -1), 0)], "chitin", 3)   # feelers
    return p.done()


@icon("bones")
def strange_bones():
    """Чужие кости: two bones of something else, crossed, grown into the chitin."""
    p = Pix()
    for a, b in (((3, 13), (12, 3)), ((3, 3), (12, 13))):
        p.line([a, b], "bone", 3)
        p.line([(a[0] + 1, a[1]), (b[0] + 1, b[1])], "bone", 2)
        for (x, y) in (a, b):
            p.disc(x + 0.5, y, 1.4, "bone", levels=(4, 3, 2))      # the knobs at the ends
    return p.done()


@icon("quills")
def quills():
    """Иглы: a hedgehog's quills bristling out of a hump of chitin — long, banded pale and dark."""
    p = Pix()
    p.fill(ell(7.5, 12.0, 6.0, 2.6), "chitin", inner=(3, 2))
    for x0, x1, y1 in ((3, 1, 3), (5, 4, 1), (7, 7, 0), (9, 10, 1), (11, 13, 2), (13, 15, 5)):
        p.line([(x0, 10), (x1, y1)], "bone", 3)
        p.px(x1, y1, "bone", 4)
    return p.done()


@icon("snout")
def wolf_snout():
    """Волчий нюх: a wolf's grey head side on — ear up, the long muzzle out to the right, the black wet nose,
    a yellow eye — sniffing the air."""
    p = Pix()
    head = grid(lambda x, y: ((x - 5.5) / 4.2) ** 2 + ((y - 8.5) / 4.0) ** 2 <= 1
                or (6 <= x <= 13 and 8 <= y <= 11 and y >= 8 + (x - 6) * 0.15))
    p.fill(head, "fur", inner=(3, 2))
    ear = grid(lambda x, y: 3 <= y <= 5 and abs(x - 4.5) <= (y - 2) * 0.7)
    p.fill(ear, "fur", inner=(3, 2))
    p.rect(13, 8, 14, 9, "chitin", [1])                            # the nose
    p.px(13, 8, "slate", 4)
    p.px(7, 7, "amber", 4)                                         # the eye
    p.rect(9, 11, 12, 11, "fur", [1])                              # the mouth line
    for x, y in ((15, 6), (15, 11)):
        p.px(x, y, "fur", 2)                                       # sniffing
    return p.done()


@icon("slime")
def slime_skin():
    """Слизистая кожа: a slick of slime, glistening, running in drops off a bug's back."""
    p = Pix()
    p.fill(ell(7.5, 7.5, 6.0, 3.6), "slime", inner=(3, 2))
    for x, y in ((4, 11), (8, 12), (11, 11)):
        p.col(x, y, y + 1, "slime", [3, 2])                        # drops running off
    p.px(5, 5, "lantern", 4)                                       # its glisten
    p.px(6, 5, "slime", 4)
    p.px(9, 6, "slime", 4)
    return p.done()


@icon("worm")
def worm_inside():
    """Червь внутри: a pale worm curling out of a split in the chitin, its ringed body, its round mouth."""
    p = Pix()
    p.fill(ell(7.5, 12.0, 6.0, 2.6), "chitin", inner=(3, 2))
    p.dark(7, 11)
    p.dark(8, 11)
    for k, (x, y) in enumerate(((7, 10), (6, 8), (6, 6), (8, 4), (10, 4), (11, 6))):
        p.disc(x + 0.5, y + 0.5, 1.4, "worm", levels=(4, 3, 2))
        if k % 2:
            p.px(x, y + 1, "worm", 1)                              # its rings
    p.dark(12, 7)                                                  # its mouth
    return p.done()


# ---------------------------------------------------------------- the swarm's leaders
@icon("matka")
def queen():
    """Матка: the queen — a vast bloated egg-sac of an abdomen, pale and veined, a small armoured head with a
    crown of horns."""
    p = Pix()
    p.fill(ell(6.0, 9.5, 5.6, 4.4), "grub", inner=(3, 2))          # the egg-sac
    for x, y in ((3, 8), (5, 11), (8, 9)):
        p.px(x, y, "crimson", 3)                                   # veins
    p.fill(ell(12.0, 8.0, 2.4, 2.0), "chitin", inner=(3, 2))       # the head
    for x, y in ((11, 5), (12, 4), (13, 5), (14, 6)):
        p.px(x, y, "amber", 4)                                     # the crown of horns
    p.px(13, 8, "acid", 4)
    p.px(4, 14, "egg", 3)                                          # an egg laid
    return p.done()


@icon("razum")
def hive_mind():
    """Разум улья: a swollen brain, its folds pulsing, rings of psi spreading out from it."""
    p = Pix()
    p.fill(ell(7.5, 8.0, 5.4, 4.2), "brain", inner=(3, 2))
    for y in (6, 8, 10):
        for x in range(4, 12):
            if (x + y) % 3 == 0:
                p.px(x, y, "brain", 1)                             # its folds
    p.line([(7, 4), (7, 12)], "brain", 1)
    for x, y in ((1, 4), (0, 8), (1, 12), (14, 4), (15, 8), (14, 12)):
        p.px(x, y, "phero", 4)                                     # psi rings
    return p.done()


@icon("pozh")
def devourer():
    """Пожиратель: a maw seen head-on — rings of hooked teeth closing in, a red throat at the middle."""
    p = Pix()
    p.disc(7.5, 7.5, 6.6, "chitin", levels=(3, 3, 2, 1))
    p.disc(7.5, 7.5, 4.2, "crimson", levels=(2, 2, 1))
    p.disc(7.5, 7.5, 1.6, "chitin", levels=(0,))
    for a in np.linspace(0, 2 * np.pi, 10, endpoint=False):
        p.px(round(7.5 + np.cos(a) * 4.6), round(7.5 + np.sin(a) * 4.6), "bone", 4)        # teeth
        p.px(round(7.5 + np.cos(a + 0.3) * 3.2), round(7.5 + np.sin(a + 0.3) * 3.2), "bone", 3)
    return p.done()


@icon("kuk")
def plague():
    """Чума: a host's egg gone wrong — a sickly green egg with a parasite curled dark inside it, spores drifting
    off it."""
    p = Pix()
    p.fill(ell(7.0, 9.0, 4.4, 5.4), "egg", inner=(3, 2))
    p.disc(7.0, 9.5, 2.2, "chitin", levels=(2, 1))                 # the thing inside
    p.px(8, 9, "crimson", 4)                                       # its eye
    for x, y, lv in ((12, 3, 3), (14, 6, 2), (13, 1, 2), (2, 2, 3)):
        p.px(x, y, "egg", lv)                                      # spores
    return p.done()


# ---------------------------------------------------------------- the brood's actions
@icon("feed")
def feed():
    """Кормление лидера: a hunk of raw meat on the bone — what the brood feeds its leader."""
    p = Pix()
    p.line([(2, 13), (5, 10)], "bone", 3)
    p.disc(1.8, 13.5, 1.2, "bone", levels=(4, 3))
    p.fill(ell(9.0, 6.5, 5.0, 4.6), "crimson", inner=(3, 2))
    p.px(7, 4, "petal", 4)                                         # fat
    p.px(8, 4, "petal", 3)
    p.px(11, 8, "crimson", 1)
    return p.done()


@icon("evolve")
def evolve():
    """Эволюция формы: a bug, and three chevrons of light rising over it — the whole breed grows into its next
    form."""
    p = Pix()
    legs(p, [(6, 12), (9, 12)], spread=1.3, foot=14)
    p.fill(ell(7.5, 11.0, 4.6, 2.4), "chitin", inner=(3, 2))
    p.fill(ell(12.2, 10.5, 1.6, 1.4), "chitin", inner=(3, 2))
    p.px(13, 10, "acid", 4)
    for k, y in enumerate((5, 1)):                                  # two chevrons rising over it
        for d in range(0, 4):
            p.px(7 - d, y + d, "acid", 4 - k)
            p.px(8 + d, y + d, "acid", 4 - k)
    return p.done()


@icon("clutch")
def clutch():
    """Вторая кладка: a cluster of eggs, glistening, stuck together in a heap."""
    p = Pix()
    for cx, cy in ((4.5, 11.0), (8.0, 11.5), (11.5, 11.0), (6.0, 7.5), (9.8, 7.5), (8.0, 4.0)):
        p.fill(ell(cx, cy, 2.2, 2.4), "egg", inner=(3, 2))
        p.px(round(cx - 1), round(cy - 1), "lantern", 3)
    return p.done()


@icon("reroll")
def reroll():
    """Переброс кладок: a clutch of eggs inside a circling arrow — thrown again."""
    p = Pix()
    for a in np.linspace(0.35, 2 * np.pi - 0.35, 30):
        p.px(round(7.5 + np.cos(a) * 6.3), round(7.5 + np.sin(a) * 6.3), "amber", 4 if np.sin(a) < 0 else 3)
    for x, y in ((13, 6), (14, 7), (12, 7), (13, 8)):
        p.px(x, y, "amber", 4)                                     # the arrowhead
    for cx, cy in ((6.0, 9.0), (9.0, 9.0), (7.5, 6.0)):
        p.fill(ell(cx, cy, 1.8, 2.0), "egg", inner=(3, 2))
    return p.done()


@icon("biomass")
def biomass():
    """Биомасса: a heap of living green-grey flesh, lumpy, veined, a bubble rising in it."""
    p = Pix()
    for cx, cy, r in ((5.0, 10.0, 3.6), (10.0, 10.5, 3.4), (7.5, 6.5, 3.2)):
        p.fill(ell(cx, cy, r, r * 0.9), "slime", inner=(3, 2))
    for x, y in ((4, 9), (9, 11), (7, 7)):
        p.px(x, y, "crimson", 3)                                   # veins
    p.px(6, 5, "slime", 4)
    return p.done()


@icon("larva")
def larva():
    """Личинка: a fat pale grub, curled, its body in rings, a dark little head."""
    p = Pix()
    for k, (x, y) in enumerate(((3, 10), (5, 12), (8, 12), (11, 11), (12, 8), (11, 5))):
        p.fill(ell(x, y, 2.2, 2.2), "grub", inner=(3, 2))
    p.fill(ell(9.0, 4.0, 1.6, 1.5), "rust", inner=(3, 2))          # its head
    for x, y in ((5, 11), (8, 11), (11, 10)):
        p.px(x, y, "grub", 1)                                      # rings
    return p.done()


@icon("selection")
def selection():
    """Естественный отбор: a big bug standing on a small dead one — the dead one curled pale on its back under
    it, the winner whole and dark, an eye bright."""
    p = Pix()
    p.fill(ell(7.5, 12.5, 5.0, 2.0), "bone", inner=(2, 2), rim=3, shade=1)   # the dead one, a pale husk
    for x in (4, 7, 10):
        p.px(x, 10, "bone", 3)                                # its legs curled up
    legs(p, [(6, 8), (9, 8), (12, 8)], spread=0.9, foot=11)
    p.fill(ell(8.0, 5.5, 4.4, 2.6), "chitin", inner=(3, 2))   # the winner, standing on it
    p.fill(ell(13.0, 4.5, 1.8, 1.7), "chitin", inner=(3, 2))
    p.px(14, 4, "acid", 4)
    p.line([(14, 3), (15, 1)], "chitin", 3)
    return p.done()


@icon("fear")
def fear():
    """Страх: a bug's eye wide open in terror, sweat flying off it."""
    p = Pix()
    p.fill(ell(7.5, 8.5, 6.0, 4.6), "bone", inner=(4, 3))
    p.disc(7.5, 8.5, 2.0, "chitin", levels=(1,))                   # the pupil, shrunk to a point
    p.px(7, 8, "slate", 4)
    for x, y in ((1, 2), (3, 1), (13, 1), (14, 3)):
        p.px(x, y, "blue", 4)                                      # sweat
    return p.done()


# ---------------------------------------------------------------- evolutions: each trait's forms grown further
def small_ant(p, x, y, ramp="chitin", legs_=True):
    """A small ant at (x, y) (its waist), facing right: gaster, thorax, head, feelers."""
    if legs_:
        p.line([(x, y + 1), (x - 1, y + 3)], ramp, 1)
        p.line([(x + 2, y + 1), (x + 3, y + 3)], ramp, 1)
    p.fill(ell(x - 2.0, y, 2.0, 1.5), ramp, inner=(3, 2))
    p.fill(ell(x + 1.0, y - 0.3, 1.0, 0.8), ramp, inner=(3, 2))
    p.fill(ell(x + 3.0, y - 1.0, 1.2, 1.1), ramp, inner=(3, 2))
    p.px(x + 4, y - 3, ramp, 3)


@icon("evo_formic")
def formic_acid():
    """Муравьиная кислота: an ant curling its gaster forward under itself and spraying acid out of the tip."""
    p = Pix()
    small_ant(p, 9, 9)
    for x, y, lv in ((5, 6, 4), (4, 4, 3), (2, 3, 4), (3, 1, 2), (1, 5, 3), (0, 2, 2)):
        p.px(x, y, "acid", lv)                                     # the spray
    return p.done()


@icon("evo_phalanx")
def phalanx():
    """Сомкнутый строй: three ants shoulder to shoulder in a tight rank, the front one darkest."""
    p = Pix()
    for k, (x, y) in enumerate(((7, 4), (9, 8), (11, 12))):
        small_ant(p, x, y, "chitin" if k == 2 else "slate")
    return p.done()


@icon("evo_bridge")
def living_bridge():
    """Живой мост: ants hooked jaw to gaster across a gap between two ledges, the swarm walking over them."""
    p = Pix()
    p.rect(0, 10, 2, 15, "stone", [4, 3, 2, 2, 1, 1])              # the ledges
    p.rect(13, 10, 15, 15, "stone", [3, 2, 2, 1, 1, 1])
    for k, (x, y) in enumerate(((3, 10), (6, 11), (9, 11), (12, 10))):
        p.fill(ell(x, y, 1.8, 1.2), "chitin", inner=(3, 2))        # the bridge of bodies
        p.line([(x, y + 1), (x + (1 if k % 2 else -1), y + 3)], "chitin", 1)
    small_ant(p, 8, 7, "rust", legs_=False)                        # one crossing over
    return p.done()


@icon("evo_syringe")
def syringe_sting():
    """Жало-шприц: a wasp's striped abdomen ending in a long hollow needle, a drop of venom at its tip."""
    p = Pix()
    ab = ell(9.0, 7.0, 4.6, 3.2)
    p.fill(ab, "amber", inner=(3, 2))
    for x in (8, 11):
        for y in range(16):
            if ab[y, x]:
                p.px(x, y, "chitin", 1)
    p.line([(4, 9), (1, 12)], "steel", 4)                          # the needle
    p.px(0, 13, "acid", 4)                                         # the drop
    p.px(0, 14, "acid", 3)
    p.fill(ell(14.0, 6.0, 1.4, 1.6), "chitin", inner=(3, 2))
    return p.done()


@icon("evo_tough")
def tough_wings():
    """Жёсткие крылья: a wasp's wings grown hard — thick amber plates ribbed with dark veins, like armour."""
    p = Pix()
    for (cx, cy, rx, ry) in ((6.0, 6.0, 5.0, 2.4), (9.0, 4.0, 4.4, 2.0)):
        p.fill(ell(cx, cy, rx, ry), "amber", inner=(3, 2))
    for pts in ([(2, 6), (10, 5)], [(5, 4), (12, 3)], [(4, 8), (9, 7)]):
        p.line(pts, "chitin", 1)                                   # veins
    p.fill(ell(10.0, 11.0, 3.6, 2.0), "chitin", inner=(3, 2))      # the body under them
    p.px(13, 10, "amber", 4)
    return p.done()


@icon("evo_dive")
def dive():
    """Пикирование: a wasp stooping down out of the sky, sting first, speed lines streaming behind it."""
    p = Pix()
    for k in range(3):
        p.line([(1 + k * 3, 0), (4 + k * 3, 4)], "slate", 2)       # speed lines
    p.tube(7.0, 6.0, 12.0, 12.0, 2.0, "amber", levels=(4, 3, 2))
    p.line([(9, 9), (10, 8)], "chitin", 1)
    p.line([(10, 11), (11, 10)], "chitin", 1)
    p.px(13, 13, "chitin", 2)                                      # the sting
    p.px(14, 14, "steel", 4)
    p.fill(ell(6.0, 5.0, 1.6, 1.6), "chitin", inner=(3, 2))
    p.fill(ell(10.0, 4.5, 2.4, 1.2), "slate", inner=(4, 3), rim=4, shade=2)   # a wing
    return p.done()


@icon("evo_vise")
def vise_claws():
    """Клешни-тиски: a scorpion's claw grown huge and heavy, its two fingers clamped shut on something."""
    p = Pix()
    p.tube(1.0, 12.0, 6.0, 9.0, 1.2, "rust", levels=(4, 3, 2))    # the arm
    hand = ell(9.0, 8.0, 3.6, 3.0)
    p.fill(hand, "rust", inner=(3, 2))
    p.line([(11, 6), (14, 4), (15, 6)], "rust", 4)                 # the upper finger
    p.line([(11, 10), (14, 11), (15, 9)], "rust", 2)               # the lower
    p.rect(13, 7, 14, 8, "bone", [3, 2])                           # what it crushes
    return p.done()


@icon("evo_neuro")
def neurotoxin():
    """Нейротоксин: a scorpion's tail tip, the sting dripping a violet venom that numbs."""
    p = Pix()
    for (cx, cy) in ((2.0, 13.0), (3.5, 10.5), (5.5, 8.0), (8.0, 6.0), (10.5, 5.5)):
        p.fill(ell(cx, cy, 1.6, 1.4), "rust", inner=(3, 2))
    p.fill(ell(12.5, 6.5, 1.8, 1.6), "crimson", inner=(3, 2))      # the bulb
    p.line([(13, 8), (12, 10)], "crimson", 4)                      # the sting
    p.px(12, 11, "phero", 4)                                       # the venom
    p.px(12, 12, "phero", 3)
    p.px(11, 14, "phero", 2)
    return p.done()


@icon("evo_longlegs")
def long_legs():
    """Длинные лапы: a scorpion carried high on long stilt legs splayed wide — its segmented tail curled up over
    its back to the hooked sting, its claws reaching forward; a strip of ground far below."""
    p = Pix()
    p.rect(0, 15, 15, 15, "fur", [1])                         # the ground
    for x0, x1 in ((6, 1), (7, 4), (9, 11), (10, 14)):        # the legs: up to a knee, then far down and out
        kx = x0 + (-1 if x1 < x0 else 1)
        p.line([(x0, 8), (kx, 6), (x1, 14)], "rust", 2)
    p.fill(ell(8.0, 8.0, 3.6, 1.5), "rust", inner=(3, 2))     # the body
    for (cx, cy) in ((4.5, 7.0), (3.2, 5.0), (3.4, 3.0), (5.0, 1.6)):
        p.fill(ell(cx, cy, 1.1, 1.0), "rust", inner=(3, 2))   # the tail's segments, curling over
    p.line([(6, 1), (7, 2), (7, 3)], "crimson", 4)            # the sting
    p.fill(ell(12.6, 7.0, 1.4, 1.0), "rust", inner=(3, 2))    # the claw
    p.px(14, 6, "rust", 4)
    p.px(14, 8, "rust", 3)
    return p.done()


@icon("evo_farspit")
def far_spit():
    """Дальний плевок: the acid bug arching a long shot of acid far to the right."""
    p = Pix()
    p.fill(ell(3.5, 11.0, 3.0, 2.4), "acid", inner=(3, 2))
    p.fill(ell(6.8, 11.5, 1.4, 1.2), "chitin", inner=(3, 2))
    for x, y in ((8, 9), (9, 7), (10, 6), (11, 6), (12, 7), (13, 9)):
        p.px(x, y, "acid", 3)                                      # the arc
    p.disc(14.0, 11.0, 1.4, "acid", levels=(4, 3))                 # the shot, landing
    return p.done()


@icon("evo_scent")
def own_scent():
    """Свой запах: the acid bug giving off a smell its own kind knows — wavy lines rising off it."""
    p = Pix()
    legs(p, [(6, 12), (9, 12)], spread=1.2, foot=14)
    p.fill(ell(6.0, 11.0, 4.0, 2.4), "acid", inner=(3, 2))
    p.fill(ell(11.5, 11.5, 1.6, 1.4), "chitin", inner=(3, 2))
    for x0 in (3, 7, 11):
        for k in range(5):
            p.px(x0 + (k % 2), 7 - k, "egg", 4 - k // 2)           # the scent, rising
    return p.done()


@icon("evo_pool")
def acid_pool():
    """Едкая лужа: a puddle of acid on the ground, eating into it, bubbling, a drop falling in."""
    p = Pix()
    p.fill(ell(7.5, 11.5, 7.0, 2.8), "acid", inner=(3, 2))
    for cx, cy in ((5.0, 11.0), (10.0, 12.0)):
        p.disc(cx, cy, 0.9, "lantern", levels=(4, 3))              # bubbles
    p.px(8, 5, "acid", 4)                                          # a drop falling
    p.px(8, 6, "acid", 3)
    for x in (2, 13):
        p.px(x, 8, "slate", 2)                                     # fumes
    return p.done()


def beetle(p, ramp="elytra", x=6.5, y=9.0):
    legs(p, [(int(x) - 1, int(y) + 2), (int(x) + 2, int(y) + 2), (int(x) + 4, int(y) + 2)], spread=1.2, foot=14)
    p.fill(ell(x, y, 5.0, 3.4), ramp, inner=(3, 2))
    p.line([(int(x), int(y) - 3), (int(x), int(y) + 3)], ramp, 1)
    p.fill(ell(x + 5.7, y + 0.5, 1.7, 1.5), "chitin", inner=(3, 2))


@icon("evo_forked")
def forked_horn():
    """Двойной рог: a beetle's horn grown into a fork — two prongs, a gap between them to catch and lever."""
    p = Pix()
    beetle(p)
    p.line([(13, 8), (13, 5), (12, 3)], "chitin", 3)
    p.line([(13, 5), (15, 3)], "chitin", 3)
    p.px(12, 2, "chitin", 4)
    p.px(15, 2, "chitin", 4)
    return p.done()


@icon("evo_bosses")
def knobbed_elytra():
    """Бугристые надкрылья: a beetle's wing cases grown over with hard knobs."""
    p = Pix()
    beetle(p)
    for x, y in ((3, 7), (5, 6), (8, 6), (4, 9), (8, 9), (6, 11), (10, 8)):
        p.px(x, y, "elytra", 4)
        p.px(x + 1, y + 1, "elytra", 1)
    return p.done()


@icon("evo_flyer")
def flyer():
    """Летучий жук: a beetle in flight — wing cases flung up, the clear wings beating out under them."""
    p = Pix()
    p.fill(ell(7.0, 10.0, 4.0, 2.4), "chitin", inner=(3, 2))
    p.fill(ell(11.5, 10.0, 1.6, 1.4), "chitin", inner=(3, 2))
    p.fill(ell(4.5, 5.0, 3.6, 1.6), "elytra", inner=(3, 2))        # wing cases, up
    p.fill(ell(9.5, 4.0, 4.0, 1.6), "slate", inner=(4, 3), rim=4, shade=2)   # the wings
    p.line([(4, 12), (3, 14)], "chitin", 1)
    p.line([(9, 12), (10, 14)], "chitin", 1)
    return p.done()


def woodlouse_dome(p, ramp="slate"):
    for x in range(3, 13, 2):
        p.line([(x, 12), (x - 1, 13)], ramp, 1)
    dome = grid(lambda x, y: ((x - 7.5) / 6.6) ** 2 + ((y - 11.5) / 6.0) ** 2 <= 1 and y <= 11)
    p.fill(dome, ramp, inner=(3, 2))
    for x in (4, 6, 8, 10, 12):
        for y in range(8, 12):
            if dome[y, x]:
                p.px(x, y, ramp, 1)
    return dome


@icon("evo_longspines")
def long_spines():
    """Длинные шипы: a woodlouse's back grown long spines, swept back."""
    p = Pix()
    woodlouse_dome(p)
    for x, y in ((4, 6), (7, 5), (10, 5), (12, 7)):
        p.line([(x, y), (x - 2, y - 4)], "bone", 3)
        p.px(x - 2, y - 4, "bone", 4)
    return p.done()


@icon("evo_lime")
def lime_shell():
    """Известковый панцирь: a woodlouse whose plates have turned to chalky white stone, cracked."""
    p = Pix()
    woodlouse_dome(p, "bone")
    p.px(6, 7, "stone", 1)
    p.px(7, 8, "stone", 1)
    p.px(10, 9, "stone", 1)
    return p.done()


@icon("evo_flanges")
def flanges():
    """Щитовые края: a woodlouse's plates grown out into broad flat flanges at its sides — a shield."""
    p = Pix()
    p.rect(0, 11, 15, 12, "slate", [3, 1])                         # the flanges
    woodlouse_dome(p)
    p.px(0, 11, "slate", 4)
    p.px(15, 11, "slate", 2)
    return p.done()


@icon("evo_locust")
def locust_phase():
    """Стадная фаза: grasshoppers turned locusts — yellow and black, three of them swarming together."""
    p = Pix()
    for (x, y) in ((4, 4), (11, 7), (5, 12)):
        p.fill(ell(x, y, 3.4, 1.4), "locust", inner=(3, 2))
        p.fill(ell(x + 3.4, y - 0.5, 1.2, 1.2), "locust", inner=(3, 2))
        p.line([(x - 2, y - 1), (x, y - 3)], "locust", 2)          # the hind leg
        p.px(x + 4, y - 1, "chitin", 1)
    return p.done()


@icon("evo_shins")
def spiked_shins():
    """Шипастые голени: a grasshopper's hind leg — the thick thigh, and the shin set with a row of spines."""
    p = Pix()
    p.tube(2.0, 12.0, 9.0, 4.0, 1.6, "olive", levels=(4, 3, 2))   # the thigh
    p.line([(9, 4), (14, 13)], "olive", 3)                         # the shin
    for k in range(4):
        x, y = 10 + k, 6 + k * 2
        p.px(x + 1, y, "bone", 4)                                  # spines
    return p.done()


@icon("evo_farjump")
def far_jump():
    """Дальний прыжок: a grasshopper in mid-leap, the long dotted arc of its jump behind it."""
    p = Pix()
    for x, y in ((0, 14), (1, 11), (2, 8), (3, 6), (5, 4)):
        p.px(x, y, "olive", 2)                                     # the arc
    p.fill(ell(10.0, 4.0, 3.6, 1.4), "olive", inner=(3, 2))
    p.fill(ell(13.6, 3.6, 1.3, 1.3), "olive", inner=(3, 2))
    p.line([(8, 5), (6, 8), (8, 10)], "olive", 3)                  # the leg, flung out
    p.px(14, 3, "chitin", 1)
    return p.done()


@icon("evo_saws")
def saw_scythes():
    """Серпы-пилы: a mantis's scythe foreleg, its blade cut into saw teeth."""
    p = Pix()
    p.tube(2.0, 12.0, 8.0, 5.0, 1.2, "mantis", levels=(4, 3, 2))
    p.line([(8, 5), (13, 3), (14, 6)], "mantis", 3)
    for k in range(5):
        x = 9 + k
        p.px(x, 5 + (k % 2), "steel", 4 if k % 2 else 3)           # saw teeth
    return p.done()


@icon("evo_orchid")
def orchid():
    """Цветочная мимикрия: a mantis grown into a flower — petals of pink and white where its legs were."""
    p = Pix()
    for cx, cy in ((4.5, 5.0), (10.5, 5.0), (4.5, 11.0), (10.5, 11.0)):
        p.fill(ell(cx, cy, 2.8, 2.4), "petal", inner=(4, 3))       # petals
    p.fill(ell(7.5, 8.0, 2.4, 3.0), "petal", inner=(3, 2))
    p.px(7, 6, "acid", 4)                                          # its eye, looking out
    p.px(8, 6, "acid", 3)
    return p.done()


@icon("evo_eyespots")
def eyespots():
    """Глазчатые крылья: wings spread wide, each with a great false eye on it to frighten."""
    p = Pix()
    for cx in (4.0, 11.0):
        p.fill(ell(cx, 7.5, 3.6, 5.0), "mantis", inner=(3, 2))
        p.disc(cx, 7.0, 1.9, "amber", levels=(4, 3))
        p.disc(cx, 7.0, 0.9, "chitin", levels=(1,))
    p.col(7, 3, 13, "chitin", [2])
    p.col(8, 3, 13, "chitin", [1])
    return p.done()


@icon("evo_bright")
def bright_lantern():
    """Яркий фонарь: a firefly whose lantern blazes — a big ball of cold light and rays out of it."""
    p = Pix()
    p.fill(ell(5.5, 9.0, 4.2, 3.4), "lantern", inner=(4, 4), rim=4, shade=3)
    for x, y in ((0, 9), (1, 4), (5, 3), (1, 14), (5, 15)):
        p.px(x, y, "lantern", 3)                                   # rays
    p.fill(ell(11.0, 9.0, 2.2, 1.6), "chitin", inner=(3, 2))
    p.fill(ell(13.8, 8.6, 1.3, 1.2), "chitin", inner=(3, 2))
    return p.done()


@icon("evo_hood")
def hood():
    """Капюшон: a firefly whose shell has grown a hood over its head, its light hidden under it until it shows."""
    p = Pix()
    p.fill(ell(4.5, 10.0, 3.0, 2.2), "lantern", inner=(3, 2))
    p.fill(ell(9.5, 9.5, 2.6, 1.8), "chitin", inner=(3, 2))
    hood = grid(lambda x, y: ((x - 12.0) / 3.2) ** 2 + ((y - 8.0) / 3.0) ** 2 <= 1 and y <= 9)
    p.fill(hood, "elytra", inner=(3, 2))
    p.px(13, 10, "lantern", 4)                                     # the light under the hood
    return p.done()


@icon("evo_lure")
def false_lure():
    """Ложный сигнал: a glowing bait dangling on a stalk — a false light that draws the enemy in."""
    p = Pix()
    p.line([(3, 14), (4, 9), (7, 4), (11, 3), (12, 5)], "chitin", 3)
    p.disc(12.5, 8.0, 2.2, "lure", levels=(4, 4, 3, 2))
    for x, y in ((9, 8), (15, 8), (12, 11)):
        p.px(x, y, "lure", 3)                                      # its glow
    return p.done()


@icon("evo_net")
def catch_net():
    """Ловчая сеть: a net of silk thrown wide — rings and spokes, sticky drops on the threads."""
    p = Pix()
    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        p.line([(7, 7), (round(7 + np.cos(a) * 7), round(7 + np.sin(a) * 7))], "bone", 3)
    for rr in (3.0, 5.5):
        for a in np.linspace(0, 2 * np.pi, 28, endpoint=False):
            p.px(round(7 + np.cos(a) * rr), round(7 + np.sin(a) * rr), "bone", 2)
    for x, y in ((4, 4), (10, 9), (9, 3)):
        p.px(x, y, "bone", 4)                                      # sticky drops
    return p.done()


@icon("evo_recoil")
def recoil():
    """Отскок на нити: a spider snapping back up on its thread, an arrow up beside it."""
    p = Pix()
    p.col(8, 0, 7, "bone", [3])                                    # the thread
    for k, (x, y) in enumerate(((6, 10), (7, 10), (9, 10), (10, 10))):
        d = k - 1.5
        p.line([(x, y), (round(x + d * 2), 8), (round(x + d * 3), 13)], "chitin", 1 + k % 2)
    p.fill(ell(8.0, 10.0, 2.6, 2.4), "chitin", inner=(3, 2))
    p.px(7, 9, "crimson", 4)
    for x, y in ((3, 2), (2, 3), (4, 3), (3, 4), (3, 5)):
        p.px(x, y, "amber", 4)                                     # up
    return p.done()


@icon("evo_pull")
def pull_down():
    """Стащить со стены: a thread shot out and caught on someone up on a wall, pulled taut to drag them down."""
    p = Pix()
    p.rect(12, 0, 15, 15, "stone", [4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 1, 1])   # the wall
    p.fill(ell(10.0, 4.0, 1.8, 1.4), "fur", inner=(3, 2))          # someone on it
    p.line([(3, 12), (9, 5)], "bone", 4)                           # the thread, taut
    p.fill(ell(3.0, 12.5, 2.4, 2.0), "chitin", inner=(3, 2))       # the spider pulling
    p.px(4, 11, "crimson", 4)
    return p.done()


# ---------------------------------------------------------------- mutations
def egg(p, cx, cy, ramp="egg", rx=2.6, ry=3.2):
    p.fill(ell(cx, cy, rx, ry), ramp, inner=(3, 2))
    p.px(round(cx - rx * 0.4), round(cy - ry * 0.5), "lantern" if ramp == "egg" else ramp, 4)


def crown(p, x, y, ramp="amber"):
    p.rect(x, y + 2, x + 4, y + 2, ramp, [3])
    for k in (0, 2, 4):
        p.col(x + k, y, y + 1, ramp, [4, 3])


def bug(p, x, y, ramp="chitin", s=1.0, eye="acid"):
    """A plain little bug, side on, facing right, its middle at (x, y)."""
    p.line([(round(x - 1), round(y + 1.5 * s)), (round(x - 2), round(y + 3 * s))], ramp, 1)
    p.line([(round(x + 1), round(y + 1.5 * s)), (round(x + 2), round(y + 3 * s))], ramp, 1)
    p.fill(ell(x - 0.5, y, 3.0 * s, 1.9 * s), ramp, inner=(3, 2))
    p.fill(ell(x + 3.0 * s, y - 0.3, 1.4 * s, 1.3 * s), ramp, inner=(3, 2))
    p.px(round(x + 3.4 * s), round(y - 0.6), eye, 4)


# the common pool
@icon("m_spinner")
def spinner():
    """Прядильные железы: a spider's abdomen, the spinnerets at its tip drawing out a thread wound on a spool."""
    p = Pix()
    p.fill(ell(10.0, 6.0, 4.6, 4.0), "chitin", inner=(3, 2))
    p.px(9, 4, "crimson", 4)
    p.line([(6, 9), (4, 12)], "bone", 4)                           # the thread
    p.rect(1, 11, 5, 14, "bone", [4, 3, 3, 2])                     # the spool of silk
    p.col(3, 11, 14, "bone", [2])
    return p.done()


@icon("m_exploder")
def exploder():
    """Взрывной муравей: an ant whose gaster has swollen tight and glows — about to burst."""
    p = Pix()
    p.fill(ell(5.0, 8.5, 4.4, 4.0), "fire", inner=(3, 2), rim=4, shade=1)
    p.px(4, 6, "lantern", 4)
    for x, y in ((5, 9), (6, 7), (3, 10)):
        p.px(x, y, "ember", 2)                                     # the skin straining
    p.fill(ell(10.5, 9.0, 1.4, 1.0), "chitin", inner=(3, 2))
    p.fill(ell(13.0, 8.0, 1.4, 1.3), "chitin", inner=(3, 2))
    p.line([(10, 10), (10, 13)], "chitin", 1)
    p.line([(12, 9), (13, 12)], "chitin", 1)
    for x, y in ((1, 2), (5, 1), (9, 3)):
        p.px(x, y, "fire", 4)                                      # sparks
    return p.done()


@icon("m_bolas")
def bolas():
    """Болас: two round weights on a cord, whirling."""
    p = Pix()
    p.line([(4, 11), (7, 7), (11, 4)], "bone", 3)
    p.disc(3.5, 11.5, 2.4, "chitin", levels=(4, 3, 2, 1))
    p.disc(11.5, 3.5, 2.4, "chitin", levels=(4, 3, 2, 1))
    for x, y in ((1, 6), (6, 14), (14, 9), (9, 0)):
        p.px(x, y, "slate", 2)                                     # whirling
    return p.done()


@icon("m_beeball")
def beeball():
    """Пчелиный шар: a ball of bees clinging together, smothering what's inside with their heat."""
    p = Pix()
    for k in range(14):
        a, r = k * 2.4, 1.0 + (k % 5) * 1.1
        cx, cy = 7.5 + np.cos(a) * r, 8.0 + np.sin(a) * r
        p.fill(ell(cx, cy, 1.6, 1.1), "amber", inner=(3, 2))
        p.px(round(cx), round(cy), "chitin", 1)
    for x, y in ((2, 2), (13, 3)):
        p.px(x, y, "fire", 3)                                      # the heat
    return p.done()


@icon("m_pupa")
def pupa():
    """Куколка: a pupa hanging from a thread, its case ringed, the form of the bug inside showing through."""
    p = Pix()
    p.col(8, 0, 2, "bone", [3])
    p.fill(ell(7.5, 8.0, 3.4, 5.6), "grub", inner=(3, 2))
    for y in (5, 8, 11):
        for x in range(5, 11):
            p.px(x, y, "grub", 1)
    p.px(6, 4, "chitin", 2)                                        # the shape inside
    p.px(7, 6, "chitin", 2)
    return p.done()


@icon("m_midge")
def midges():
    """Мошкара: a cloud of tiny biting midges, dark specks with clear wings, thickest at the middle."""
    p = Pix()
    for x, y in ((7, 7), (5, 5), (9, 4), (10, 8), (6, 10), (3, 8), (12, 5), (8, 12), (2, 3), (13, 11), (4, 13),
                 (11, 2), (14, 7), (1, 10)):
        p.px(x, y, "chitin", 2)
        p.px(x + (1 if (x + y) % 2 else -1), y - 1, "slate", 4)
    return p.done()


@icon("m_honey")
def honeycomb():
    """Медовые соты: a slab of comb, its cells full of honey, a drop running off."""
    p = Pix()
    for row in range(3):
        for col in range(3):
            cx = 3.0 + col * 4.4 + (row % 2) * 2.2
            cy = 3.5 + row * 4.0
            p.fill(ell(cx, cy, 2.1, 1.9), "amber", inner=(4, 3), rim=4, shade=2)
            p.px(round(cx), round(cy), "amber", 1)
    p.px(8, 14, "amber", 3)
    return p.done()


@icon("m_blister")
def blister():
    """Нарывник: a blister beetle — a red swollen blister on its back, ready to burst and burn."""
    p = Pix()
    bug(p, 7, 10, "chitin", s=1.4)
    p.disc(6.0, 6.0, 2.6, "crimson", levels=(4, 4, 3, 2))
    p.px(5, 5, "petal", 4)
    return p.done()


@icon("m_cutters")
def cutters():
    """Кусачки: a pair of great curved mandibles, serrated on the inside, closing like pincers."""
    p = Pix()
    p.fill(ell(3.0, 8.0, 3.0, 3.8), "chitin", inner=(3, 2))
    for side in (-1, 1):
        pts = [(5, 8 + side * 3), (7, 8 + side * 5), (10, 8 + side * 5), (12, 8 + side * 4), (13, 8 + side * 2),
               (12, 8 + side * 1)]
        p.line(pts, "rust", 4 if side < 0 else 2)
        p.line([(x, y - side) for x, y in pts[1:4]], "rust", 3 if side < 0 else 1)
        p.px(9, 8 + side * 3, "bone", 4)                           # serrations
        p.px(11, 8 + side * 2, "bone", 3)
    return p.done()


@icon("m_guard")
def leader_guard():
    """Стража лидера: a big-headed soldier with jaws like shears, a small gold crown over it — the leader's own."""
    p = Pix()
    bug(p, 6, 10, "rust", s=1.5)
    crown(p, 7, 1)
    return p.done()


@icon("m_regen")
def regen():
    """Живучая: a severed leg growing back — a green bud pushing out of the stump."""
    p = Pix()
    p.fill(ell(5.0, 8.0, 4.4, 3.4), "chitin", inner=(3, 2))
    p.line([(9, 9), (11, 11)], "chitin", 2)                        # the stump
    p.line([(11, 11), (13, 13)], "egg", 4)                         # the new leg budding
    p.px(14, 14, "egg", 3)
    for x, y in ((12, 4), (14, 6), (13, 2)):
        p.px(x, y, "egg", 3)                                       # the life in it
    return p.done()


# the Queen's
@icon("m_nest")
def small_nest():
    """Малое гнездо: a little mound of chewed earth, its dark entrance, an egg in the mouth of it."""
    p = Pix()
    mound = grid(lambda x, y: ((x - 7.5) / 7.0) ** 2 + ((y - 14.0) / 9.0) ** 2 <= 1 and y <= 14)
    p.fill(mound, "fur", inner=(3, 2))
    for x, y in ((6, 10), (7, 10), (8, 10), (6, 11), (7, 11), (8, 11), (7, 9)):
        p.dark(x, y)
    egg(p, 7.5, 12.5, rx=1.2, ry=1.4)
    return p.done()


@icon("m_nurse")
def nurse():
    """Кормилица: a worker carrying a grub in its jaws to feed it."""
    p = Pix()
    bug(p, 5, 9, "chitin", s=1.2)
    p.fill(ell(12.5, 11.0, 2.6, 1.6), "grub", inner=(3, 2))
    return p.done()


@icon("m_vivi")
def viviparous():
    """Живородящая: a mother whose young come out alive — two small ones crawling out from under her."""
    p = Pix()
    bug(p, 8, 6, "chitin", s=1.4)
    bug(p, 4, 12, "grub", s=0.7)
    bug(p, 10, 13, "grub", s=0.7)
    return p.done()


@icon("m_bud")
def budding():
    """Почкование: a bug with a smaller copy budding off its side, still joined."""
    p = Pix()
    bug(p, 6, 7, "chitin", s=1.3)
    p.fill(ell(10.5, 12.0, 2.4, 1.6), "egg", inner=(3, 2))
    p.fill(ell(13.2, 11.8, 1.0, 1.0), "egg", inner=(3, 2))
    p.line([(8, 9), (9, 11)], "egg", 3)                            # still joined
    return p.done()


@icon("m_dominant")
def dominant():
    """Доминантная линия: a bug wearing a gold crown — its line will win out in the brood."""
    p = Pix()
    bug(p, 6, 10, "chitin", s=1.4)
    crown(p, 8, 3)
    for x in (2, 4):
        p.px(x, 2, "amber", 3)
    return p.done()


@icon("m_flight")
def nuptial_flight():
    """Брачный полёт: two winged ants flying up together."""
    p = Pix()
    for (x, y) in ((5, 10), (10, 5)):
        bug(p, x, y, "chitin", s=0.9)
        p.fill(ell(x - 1.0, y - 2.6, 2.4, 1.1), "slate", inner=(4, 3), rim=4, shade=2)
    return p.done()


@icon("m_hybrid")
def hybrid():
    """Гибрид: a bug split down the middle — one half one breed's colour, the other half another's."""
    p = Pix()
    bug(p, 7, 9, "chitin", s=1.5)
    for y in range(16):
        for x in range(8, 16):
            if p.a[y, x] and not p.hole[y, x] and p.c[y, x].sum() > 30:
                p.c[y, x] = IC.R["amber"][2 if p.c[y, x].sum() < 200 else 3]
    return p.done()


@icon("m_heir")
def heir():
    """Наследница: a young queen, small, her abdomen just starting to swell, a little crown."""
    p = Pix()
    p.fill(ell(5.5, 10.0, 3.6, 2.8), "grub", inner=(3, 2))
    p.fill(ell(10.5, 9.5, 1.8, 1.4), "chitin", inner=(3, 2))
    crown(p, 9, 4)
    return p.done()


# the Hive Mind's
def psi_rings(p, cx, cy, rs=(3.5, 5.5), ramp="phero"):
    for k, r in enumerate(rs):
        for a in np.linspace(0, 2 * np.pi, int(r * 6), endpoint=False):
            if (int(a * 3) % 2) == 0:
                p.px(round(cx + np.cos(a) * r), round(cy + np.sin(a) * r), ramp, 4 - k)


@icon("m_psi_gland")
def psi_gland():
    """Пси-железа: a violet gland pulsing in the dark, its glow ringing out."""
    p = Pix()
    psi_rings(p, 7.5, 7.5, (5.6,))
    p.fill(ell(7.5, 7.5, 3.4, 3.0), "phero", inner=(3, 2))
    p.px(6, 6, "lantern", 4)
    return p.done()


@icon("m_psi_reson")
def resonator():
    """Резонатор: a tuning fork of chitin humming, rings spreading from its tines."""
    p = Pix()
    p.col(7, 9, 14, "chitin", [3, 2])
    p.col(5, 2, 8, "chitin", [4, 3, 3, 3, 3, 2, 2])
    p.col(10, 2, 8, "chitin", [3, 2, 2, 2, 2, 2, 1])
    p.rect(5, 8, 10, 9, "chitin", [3, 2])
    for x, y in ((3, 3), (2, 5), (12, 3), (13, 5)):
        p.px(x, y, "phero", 4)
    return p.done()


@icon("m_psi_dread")
def sense_fear():
    """Чутьё на страх: an eye in a violet haze, picking up the fear of those around."""
    p = Pix()
    psi_rings(p, 7.5, 7.5, (6.2,))
    p.fill(ell(7.5, 7.5, 4.6, 2.8), "bone", inner=(4, 3))
    p.disc(7.5, 7.5, 1.8, "phero", levels=(3, 2))
    p.px(7, 7, "chitin", 1)
    return p.done()


@icon("m_psi_whisper")
def whisper():
    """Жуткий шёпот: a bug's jaws parted, violet whispers curling out of them."""
    p = Pix()
    p.fill(ell(4.5, 8.0, 4.0, 4.0), "chitin", inner=(3, 2))
    p.line([(8, 6), (9, 7)], "rust", 3)
    p.line([(8, 10), (9, 9)], "rust", 2)
    for k, y in enumerate((5, 8, 11)):
        for x in range(10, 15):
            p.px(x, y + (x % 2), "phero", 4 - k % 2)
    return p.done()


@icon("m_strider")
def stridulation():
    """Стрекот: a cricket rasping its wings together, the sound shaking out of it."""
    p = Pix()
    bug(p, 7, 10, "olive", s=1.3)
    p.fill(ell(6.0, 7.5, 3.6, 1.2), "olive", inner=(4, 3))
    for x, y in ((2, 3), (4, 2), (6, 3), (10, 2), (12, 3), (14, 2)):
        p.px(x, y, "phero", 3)
    return p.done()


@icon("m_psi_echo")
def echo():
    """Эхо крика: a scream going out and coming back — arcs of psi doubled."""
    p = Pix()
    p.fill(ell(3.0, 8.0, 2.4, 2.4), "brain", inner=(3, 2))
    for r in (4.0, 6.5, 9.0):
        for a in np.linspace(-0.9, 0.9, int(r * 3)):
            p.px(round(3.0 + np.cos(a) * r), round(8.0 + np.sin(a) * r), "phero", 4 if r < 5 else 3)
    return p.done()


@icon("m_psi_last")
def last_will():
    """Последняя воля: a dead bug on its back, and its will rising off it in a violet wisp."""
    p = Pix()
    p.fill(ell(7.5, 13.0, 4.0, 1.6), "chitin", inner=(2, 1), rim=2)
    for x in (5, 7, 9):
        p.line([(x, 12), (x, 10)], "chitin", 2)
    for k, (x, y) in enumerate(((8, 8), (9, 6), (8, 4), (9, 2), (8, 0))):
        p.px(x, y, "phero", 4 - k // 2)
        p.px(x - 1, y + 1, "phero", 2)
    return p.done()


@icon("m_psi_leash")
def psi_leash():
    """Пси-поводок: a violet tether from the hive's brain to the head of someone it holds."""
    p = Pix()
    p.fill(ell(3.0, 4.0, 2.6, 2.2), "brain", inner=(3, 2))
    p.line([(5, 5), (8, 8), (10, 9)], "phero", 4)
    p.fill(ell(12.0, 11.0, 3.0, 3.0), "fur", inner=(3, 2))         # someone's head
    p.px(11, 10, "phero", 4)                                       # its eye taken
    return p.done()


@icon("m_psi_relay")
def relay():
    """Ретранслятор: a tall stalk of chitin with a bulb on top, passing the hive's will on in rings."""
    p = Pix()
    p.col(7, 6, 14, "chitin", [3, 3, 2, 2, 2, 2, 1, 1, 1])
    p.rect(5, 14, 9, 14, "chitin", [2])
    p.fill(ell(7.5, 4.0, 2.0, 2.0), "phero", inner=(3, 2))
    psi_rings(p, 7.5, 4.0, (3.6, 6.0))
    return p.done()


# the Devourer's
@icon("m_sated")
def sated():
    """Сытная: a bug with a belly round and full, content."""
    p = Pix()
    p.fill(ell(6.0, 8.5, 5.0, 4.6), "crimson", inner=(3, 2))
    p.px(4, 6, "petal", 4)
    bug(p, 12, 9, "chitin", s=0.7)
    return p.done()


@icon("m_bait")
def bait():
    """Приманка: a lump of meat on a hook hung on a thread."""
    p = Pix()
    p.col(8, 0, 4, "bone", [3])
    p.line([(8, 5), (9, 8), (7, 9), (6, 8)], "steel", 4)           # the hook
    p.fill(ell(8.0, 11.5, 3.6, 2.8), "crimson", inner=(3, 2))
    p.px(7, 10, "petal", 4)
    return p.done()


@icon("m_fattened")
def fattened():
    """Откормленная: a bug fattened up to bursting, its legs too short for it."""
    p = Pix()
    p.fill(ell(7.5, 8.0, 6.4, 5.4), "grub", inner=(3, 2))
    for x, y in ((5, 6), (9, 9)):
        p.px(x, y, "grub", 1)
    p.fill(ell(13.5, 6.0, 1.4, 1.3), "chitin", inner=(3, 2))
    for x in (4, 7, 10):
        p.px(x, 14, "chitin", 1)
    return p.done()


@icon("m_frenzy")
def frenzy():
    """Кормовое безумие: a bug's head gone red with feeding — eyes blazing, jaws wide and dripping."""
    p = Pix()
    p.fill(ell(6.0, 8.0, 5.0, 4.4), "crimson", inner=(3, 2))
    for x in (5, 8):
        p.px(x, 6, "fire", 4)                                      # blazing eyes
    p.line([(10, 6), (14, 4)], "bone", 3)                          # jaws wide
    p.line([(10, 10), (14, 12)], "bone", 2)
    p.px(12, 13, "crimson", 4)                                     # dripping
    return p.done()


@icon("m_table")
def at_table():
    """За столом: a shallow bowl heaped with gnawed bones — the Devourer's table, shared with its pack."""
    p = Pix()
    bowl = grid(lambda x, y: ((x - 7.5) / 7.0) ** 2 + ((y - 9.0) / 5.0) ** 2 <= 1 and y >= 9)
    p.fill(bowl, "fur", inner=(3, 2))
    p.rect(0, 9, 15, 9, "fur", [4])
    for a, b in (((3, 8), (9, 4)), ((6, 8), (12, 3))):
        p.line([a, b], "bone", 3)
        p.px(b[0], b[1], "bone", 4)
    return p.done()


@icon("m_hungry")
def hungry():
    """Голодная: a lean bug, its sides sunk to the ribs, its jaws open."""
    p = Pix()
    p.fill(ell(6.5, 8.0, 5.0, 1.8), "chitin", inner=(3, 2))
    for x in (4, 6, 8):
        p.px(x, 8, "chitin", 1)                                    # ribs
    p.fill(ell(12.5, 7.5, 1.6, 1.4), "chitin", inner=(3, 2))
    p.line([(14, 6), (15, 5)], "rust", 3)
    p.line([(14, 9), (15, 10)], "rust", 2)
    legs(p, [(5, 9), (8, 9)], spread=1.0, foot=13)
    return p.done()


@icon("m_devblood")
def devourer_blood():
    """Кровь Пожирателя: a drop of the Devourer's black-red blood, a ring of tiny teeth in it."""
    p = Pix()
    drop = grid(lambda x, y: ((x - 7.5) / 4.6) ** 2 + ((y - 10.0) / 4.4) ** 2 <= 1 or (y < 10 and abs(x - 7.5) <= (y - 3) * 0.7))
    p.fill(drop, "crimson", inner=(2, 1), rim=3)
    for a in np.linspace(0, 2 * np.pi, 7, endpoint=False):
        p.px(round(7.5 + np.cos(a) * 2.4), round(10.5 + np.sin(a) * 2.4), "bone", 4)
    return p.done()


@icon("m_essence")
def essence():
    """Питательная суть: a glowing bead of nourishment, green-gold, drawn out of the eaten."""
    p = Pix()
    p.fill(ell(7.5, 8.0, 4.4, 4.4), "egg", inner=(4, 3), rim=4, shade=2)
    p.px(6, 6, "lantern", 4)
    for x, y in ((1, 3), (14, 4), (2, 13), (13, 13)):
        p.px(x, y, "egg", 3)
    return p.done()


# the Plague's
@icon("m_parasitoid")
def parasitoid():
    """Паразитоид: a slender wasp driving its long egg-laying spike into a host's back."""
    p = Pix()
    p.fill(ell(8.0, 12.0, 6.0, 2.6), "fur", inner=(3, 2))          # the host
    p.fill(ell(10.0, 4.0, 3.4, 1.4), "chitin", inner=(3, 2))       # the wasp
    p.fill(ell(13.5, 3.5, 1.2, 1.2), "chitin", inner=(3, 2))
    p.fill(ell(9.0, 2.0, 2.4, 0.9), "slate", inner=(4, 3), rim=4, shade=2)
    p.line([(7, 5), (5, 10)], "egg", 4)                            # the spike, into the host
    return p.done()


@icon("m_bloodeggs")
def blood_eggs():
    """Яйца в крови: eggs floating in a drop of blood."""
    p = Pix()
    drop = grid(lambda x, y: ((x - 7.5) / 5.6) ** 2 + ((y - 9.5) / 5.0) ** 2 <= 1 or (y < 9 and abs(x - 7.5) <= (y - 1) * 0.8))
    p.fill(drop, "crimson", inner=(3, 2))
    for cx, cy in ((5.5, 10.0), (9.5, 11.0), (7.5, 7.0)):
        egg(p, cx, cy, rx=1.2, ry=1.4)
    return p.done()


@icon("m_spores")
def spores():
    """Споры: a fungus cap bursting, a cloud of spores puffing out of it."""
    p = Pix()
    p.rect(6, 10, 9, 14, "grub", [4, 3, 3, 2, 2])                  # the stalk
    cap = grid(lambda x, y: ((x - 7.5) / 6.4) ** 2 + ((y - 9.0) / 4.0) ** 2 <= 1 and y <= 9)
    p.fill(cap, "egg", inner=(3, 2))
    for x, y in ((4, 7), (9, 6), (11, 8)):
        p.px(x, y, "egg", 1)                                       # spots
    for x, y in ((2, 2), (6, 1), (10, 2), (13, 3), (8, 3)):
        p.px(x, y, "egg", 4 if x % 2 else 3)                       # spores
    return p.done()


@icon("m_call")
def clutch_call():
    """Зов кладки: an egg calling — rings going out from it to bring the brood."""
    p = Pix()
    for r in (5.0, 7.0):
        for a in np.linspace(0, 2 * np.pi, int(r * 5), endpoint=False):
            if int(a * 4) % 2 == 0:
                p.px(round(7.5 + np.cos(a) * r), round(8.0 + np.sin(a) * r), "egg", 4 if r < 6 else 3)
    egg(p, 7.5, 8.0)
    return p.done()


@icon("m_bodyguard")
def bodyguard():
    """Телохранитель: a soldier crouched over an egg, its shell for a shield."""
    p = Pix()
    egg(p, 4.0, 11.0, rx=2.2, ry=2.6)
    p.fill(ell(9.5, 7.5, 4.6, 3.6), "chitin", inner=(3, 2))        # the shield-shell over it
    p.fill(ell(13.5, 9.5, 1.4, 1.4), "chitin", inner=(3, 2))
    p.px(14, 9, "acid", 4)
    legs(p, [(8, 10), (11, 10)], spread=0.8, foot=14)
    return p.done()


@icon("m_gnaw")
def gnawing_clutch():
    """Прожорливая кладка: an egg split open along a jagged line of teeth, hungry from before it hatches."""
    p = Pix()
    egg(p, 7.5, 8.0, rx=5.0, ry=6.0)
    for x in range(3, 13):
        p.dark(x, 8)
        if x % 2:
            p.px(x, 7, "bone", 4)
        else:
            p.px(x, 9, "bone", 3)
    return p.done()


@icon("m_mutagen")
def mutagen_clutch():
    """Мутагенная кладка: an egg glowing sick green, a spiral of change inside it."""
    p = Pix()
    p.fill(ell(7.5, 8.0, 4.6, 5.8), "acid", inner=(3, 2), rim=4, shade=1)
    for k in range(10):
        a, r = k * 0.9, 0.5 + k * 0.32
        p.px(round(7.5 + np.cos(a) * r), round(8.0 + np.sin(a) * r * 1.2), "lantern", 4)
    return p.done()


@icon("m_unstable")
def unstable():
    """Нестабильная: an egg cracking, something leaking out of the crack."""
    p = Pix()
    egg(p, 7.5, 8.0, rx=4.6, ry=5.8)
    for x, y in ((6, 3), (7, 5), (6, 7), (8, 8), (7, 10)):
        p.dark(x, y)                                               # the crack
    p.px(8, 12, "acid", 4)
    p.px(8, 13, "acid", 3)
    p.px(9, 14, "acid", 2)
    return p.done()


@icon("m_royal")
def royal_clutch():
    """Королевская кладка: a golden egg under a crown — a queen will come out of it."""
    p = Pix()
    p.fill(ell(7.5, 9.5, 4.4, 5.0), "amber", inner=(4, 3), rim=4, shade=2)
    p.px(6, 7, "lantern", 4)
    crown(p, 5, 1)
    return p.done()


NAMES = {k: v[1] for k, v in IC.SETS["swarm"][0].items()}
BATCHES = {"traits": ["ant", "wings", "stinger", "acid", "horn", "carapace", "jumper", "scythes", "firefly",
                      "spitter"],
           "chimeras": ["iron", "boil", "hand", "face", "bones", "quills", "snout", "slime", "worm", "matka", "razum",
                        "pozh", "kuk", "feed", "evolve", "clutch", "reroll", "biomass", "larva", "selection", "fear",
                        "jumper", "scythes"],
           "evo": ["evo_formic", "evo_phalanx", "evo_bridge", "evo_syringe", "evo_tough", "evo_dive", "evo_vise",
                   "evo_neuro", "evo_longlegs", "evo_farspit", "evo_scent", "evo_pool", "evo_forked", "evo_bosses",
                   "evo_flyer", "evo_longspines", "evo_lime", "evo_flanges", "evo_locust", "evo_shins",
                   "evo_farjump", "evo_saws", "evo_orchid", "evo_eyespots", "evo_bright", "evo_hood", "evo_lure",
                   "evo_net", "evo_recoil", "evo_pull", "evolve", "selection"],
           "mut": [k for k in IC.SETS["swarm"][0] if k.startswith("m_")]}


def review(keys, fname):
    """A batch, new icons only: large (×6) with the name, and in a comb cell (×2)."""
    import swarm_ui as UI
    from swarm_ui import letters
    from paths import out
    per = 6
    rows = (len(keys) + per - 1) // per
    W, H = 960, 8 + rows * 170
    sc = UI.nest(W, H, 9)
    for i, k in enumerate(keys):
        x0, y0 = 10 + (i % per) * 158, 8 + (i // per) * 170
        letters(sc, NAMES[k].split(" · ")[0], x0 + 74, y0, "text", 16, col=(240, 190, 90), align="center")
        rgba = NEW[k]()
        big = np.repeat(np.repeat(rgba, 6, 0), 6, 1)
        m = big[..., 3] > 0
        sc.rgb[y0 + 20:y0 + 116, x0 + 26:x0 + 122][m] = big[..., :3][m]
        UI.cell(sc, x0 + 50, y0 + 120, x0 + 98, y0 + 166, "normal")
        sm = np.repeat(np.repeat(rgba, 2, 0), 2, 1)
        m = sm[..., 3] > 0
        sc.rgb[y0 + 127:y0 + 159, x0 + 58:x0 + 90][m] = sm[..., :3][m]
    img = sc.image(2)
    img.save(out(fname))
    print(fname, img.size)


def atlas():
    """The swarm's icon atlas from the drawn icons — the same cells and keys as before (assets/swarm_icons.png,
    .json), so every swarm screen gets the new icons."""
    import json
    from PIL import Image
    idx_path, png_path = IC.SW_INDEX, IC.SW_ASSET
    old = json.load(open(idx_path))["icons"]
    W = 1 + max(v["cell"][0] for v in old.values())
    H = 1 + max(v["cell"][1] for v in old.values())
    sheet = np.zeros((H * 16, W * 16, 4), np.uint8)
    index = {}
    for k, v in old.items():
        cx, cy = v["cell"]
        sheet[cy * 16:(cy + 1) * 16, cx * 16:(cx + 1) * 16] = NEW[k]()
        index[k] = {kk: vv for kk, vv in v.items() if kk != "source_row"}
    Image.fromarray(sheet, "RGBA").save(png_path)
    json.dump(dict(source="drawn in code, pixel by pixel: tools/sprites/swarm_icons_drawn.py", icons=index),
              open(idx_path, "w"), ensure_ascii=False, indent=1)
    print("swarm_icons.png", len(index), "icons")


def contact():
    """All the swarm's icons on one sheet by kind, ×3."""
    import swarm_ui as UI
    from swarm_ui import letters
    from paths import out
    kinds = {}
    for k, v in IC.SETS["swarm"][0].items():
        kinds.setdefault(v[2], []).append(k)
    rows = []
    for kind, keys in kinds.items():
        for i in range(0, len(keys), 14):
            rows.append((kind if i == 0 else "", keys[i:i + 14]))
    W, H = 960, 12 + len(rows) * 56
    sc = UI.nest(W, H, 11)
    for r, (kind, keys) in enumerate(rows):
        y = 8 + r * 56
        letters(sc, kind, 14, y + 16, "text", 16, col=(240, 190, 90))
        for j, k in enumerate(keys):
            big = np.repeat(np.repeat(NEW[k](), 3, 0), 3, 1)
            m = big[..., 3] > 0
            bx = 150 + j * 56
            sc.rgb[y + 2:y + 50, bx:bx + 48][m] = big[..., :3][m]
    img = sc.image(2)
    img.save(out("swarm_icons_drawn.png"))
    print("swarm_icons_drawn.png", img.size)


if __name__ == "__main__":
    import sys
    what = sys.argv[1] if len(sys.argv) > 1 else "traits"
    if what == "atlas":
        atlas()
    elif what == "contact":
        contact()
    else:
        review(BATCHES[what], f"swicons_{what}.png")
