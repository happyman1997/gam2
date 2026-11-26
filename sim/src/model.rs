//! Units as data: damage and armor types, passives, abilities, unit templates.

use serde::{Deserialize, Serialize};

/// Damage types.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Default, Serialize, Deserialize)]
pub enum Dmg {
    #[default]
    Pierce,
    Slash,
    Blunt,
    Fire,
    Cold,
    Shock,
    Poison,
    Acid,
}

/// Armor types: what the protection is made of.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArmorType {
    None,
    Soft,
    Leather,
    Chain,
    Plate,
    Cast,
    Chitin,
    HeavyChitin,
    Bone,
    Wood,
    Stone,
    Iron,
    Flame,
}

impl ArmorType {
    /// Holds the blow: damage halved.
    pub fn resists(self, d: Dmg) -> bool {
        use ArmorType::*;
        use Dmg::*;
        match self {
            Leather => d == Blunt,
            Chain => d == Slash,
            Plate => matches!(d, Slash | Pierce),
            Cast => d == Pierce,
            Chitin => d == Slash,
            HeavyChitin => matches!(d, Slash | Pierce),
            Bone => d == Pierce,
            Wood => d == Pierce,
            Stone | Iron => matches!(d, Slash | Pierce),
            _ => false,
        }
    }

    /// Breaks under the blow: damage doubled.
    pub fn weak_to(self, d: Dmg) -> bool {
        use ArmorType::*;
        use Dmg::*;
        match self {
            Soft => d == Pierce,
            Leather => d == Slash,
            Chain => d == Pierce,
            Plate | Chitin | HeavyChitin | Bone | Stone => d == Blunt,
            Wood => matches!(d, Fire | Slash),
            Flame => d == Cold,
            _ => false,
        }
    }

    pub fn immune(self, d: Dmg) -> bool {
        self == ArmorType::Flame && d == Dmg::Fire
    }

    /// Metal conducts: +50% from lightning.
    pub fn metal(self) -> bool {
        matches!(self, ArmorType::Chain | ArmorType::Plate | ArmorType::Cast | ArmorType::Iron)
    }

    /// Armor taken off by one acid hit: one, whatever the armor (twice that for cast metal was a hard counter — a
    /// crowd of barrels stripped any golem bare in two rounds).
    pub fn acid_strip(self) -> i32 {
        1
    }
}

/// Passives and weaknesses that the battle rules know about.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Trait {
    /// Adjacent enemies must hit this unit first (Страж).
    Zaslon,
    /// Blows ignore half of the target's armor (a module: no frame has it now).
    Probivnoy,
    /// A mage: its weapon is a spell — no far-half loss, no secondary weapon; with an enemy adjacent
    /// the spell goes off one time in four (Мудрец).
    Caster,
    /// Adjacent allied golems recharge their fire and lightning modules a round sooner (Мудрец).
    Pitanie,
    /// Acid shorts the windings: silent for 2 rounds after an acid hit (Мудрец).
    Zamykanie,
    /// Each round sets one adjacent enemy on fire (Горн).
    ZharGorna,
    /// Ranged: aims at the far rows and loses nothing at long range (Орудие).
    Navodka,
    /// Adjacent allied golems mend 1 each round (Механик).
    Naladka,
    /// Does not attack (Механик).
    NoAttack,
    /// Fire deals a quarter (the Foundry class).
    FireResist75,
    /// Morale 99, never afraid (golems).
    Mindless,
    /// Poison does nothing (golems).
    PoisonImmune,
    /// Cannot be moved or knocked back (Отец колосса).
    Unstoppable,
    /// Enemies within `radius` check fear `1–die` against morale every round.
    Fear { die: u32, radius: u32 },
    /// The side's leader: its death matters (the Swarm: «Обезглавленный рой»).
    Leader,
    /// The Swarm: +1 morale for every adjacent ally, up to +4 («Стая»).
    Staya,
    /// The Swarm: a kill heals a quarter of health («Пожирание»).
    Devour,
    /// Ant: +1 to the damage bonus with 3+ adjacent allies («Строй»).
    Stroy,
    /// Wasp: flies over everyone, goes for archers and leaders first.
    Flyer,
    /// Scorpion: a blow that gets through adds `1–die` poison.
    Venom { die: u32 },
    /// Barrel: bursts with acid `1–die` on everyone adjacent when it dies, its own too.
    BurstAcid { die: u32 },
    /// Beetle: the first melee blow of the battle is ×1.5 and knocks back.
    Charge,
    /// Isopod: whoever hits it in melee takes `1–die` piercing.
    Thorns { die: u32 },
    /// Isopod: below half health curls up — +3 armor, no attacks.
    CurlUp,
    /// Grasshopper: in the first round leaps over the line into the enemy's back rows.
    Leap,
    /// Mantis: two blows a round.
    TwinBlades,
    /// Firefly: enemy archers aim at it first.
    Glow,
    /// Hive Mind: every ally has the full «Стая» bonus.
    HiveMind,
    /// Devourer: it eats every enemy that falls beside it (within a cell), whoever killed it; every 2nd meal — ×1.5
    /// health and +2 to the blow, up to twice (with its third stage every meal, thrice); it starves without meals.
    Grows,
    /// Cuckoo: a blow that gets through infects; an infected enemy that dies hatches 2 larvae
    /// (not mechanisms).
    Infects,
    /// Cuckoo: in the first round one allied worker appears in the enemy's rear («Подкидыш»).
    Changeling,
    /// Viviparous (a mutation of the Mother's pool): dying, it lets out a larva of its side — one, the larva without
    /// the trait («Живородящая»).
    Viviparous,
    /// Spitter: no shot between its spits; whoever reaches it gets only a weak bite («слабый укус»).
    Spitter,
    /// Мошкара: every third body that falls (not burnt) crumbles into a midge cloud of its side.
    Midges,
    /// The midge cloud itself: stings through any armor, enemy shooters next to it see nothing to shoot, fire burns it
    /// threefold; it thins out after a few rounds and does not count as an army.
    Cloud,
    /// Паутина: every fourth round, instead of a blow, spins a web on its cells and around them (when an enemy beside it
    /// is out of the web, or it has nothing to strike anyway); an enemy on the web is stuck — it stops walking, spends
    /// two actions tearing free and takes blows half as hard again; fire runs along the web.
    Spinner,
    /// Медовые соты: a wounded body next to its own mends a point a round; a dying one floods its cell and the cells
    /// round it with honey — enemies standing in it strike weaker.
    Honey,
    /// Почкование: wounded for the first time, it splits — a bud with half the health left steps out beside it.
    Buds,
    /// Мимикрия: the swarm takes up the weapon of the last machine it broke below half its health (or saw fall), one at a
    /// time — a Sage's or the
    /// Inventor's: the bite shocks; a Forge's: it sets alight, +1; a Guard's, a Mason's or the Architect's: the shell is
    /// two points harder; a Gun's or the Father's: the bite is blunt; a Mechanic's: it mends two a round; the Maniac's: +2.
    Mimic,
    /// Кукловод: its blows hook a machine (an infected one is hooked too); a hooked machine that falls rises for its side
    /// with a quarter of its health, its modules silent —
    /// larvae work its hull for two rounds, its own weapons turned on its own (then it falls apart, and the larvae come
    /// out).
    Puppeteer,
    /// A fallen machine worked by larvae (Кукловод): no army, it falls apart after two rounds.
    Puppet,
    /// Мираж: as the battle begins, every second body of the swarm gets a ghost twin beside it.
    Mirage,
    /// A ghost of the Hive Mind's mirage: does not strike, melts away at the first blow, no army.
    Ghost,
    /// Третья ступень (the Devourer's own mutation): it grows on every meal, not every second, and thrice, not twice;
    /// at the third stage its every blow tramples all enemies of size 5 or less beside it.
    ThirdStage,
    /// The Devourer at the start of a run (Голод): `left` more enemies for the swarm to kill this run before it is fed;
    /// till then it starves from the 2nd round without a meal and loses a fifth of its health a round (fed: from the
    /// 3rd, a tenth).
    Hungry { left: u32 },
    /// Стрекот: every second round an enemy with four or more of these beside it loses its blow (the chirr shakes it;
    /// machines ring with it too).
    Chirr,
    /// Тесла-сеть (the Inventor): while he stands, lightning runs between his golems — each to its two nearest within
    /// `TESLA_REACH` cells — and every enemy standing on a line between two of them takes 1–`TESLA_DIE` lightning a
    /// round. He falls — the net goes dark.
    Tesla,
    /// Трофеи (the Maniac): an enemy that falls within 3 cells of him — he tears a part off it and bolts it on the golem
    /// nearest to it, for the rest of the battle (at most two a golem): a wasp's wings make it fly, a scorpion's sting
    /// poisons, a beetle's horn charges, a woodlouse's shell pricks, a mantis's scythes strike twice, a grasshopper's legs
    /// leap, a barrel's sack bursts with acid, a firefly's lantern flashes, an ant's jaws +1; a machine gives its first
    /// module, a leader its head on a pike (terror).
    Trophies,
    /// A wall segment of the Architect's (Стена): stands, does not strike, holds a whole cell; no army. The enemy goes
    /// round it, and breaks it only when there is nothing else beside to strike; shooters do not waste shots on it.
    Wall,
    /// Метаморфоз (the Mother): a larva of her side that has lived three rounds pupates and comes out as the form that
    /// has killed the most in this battle — the brood turns into whatever wins.
    Metamorph,
    /// Эпидемия (the Plague): every fourth round she spits spores at the nearest enemy, however far — it is infected;
    /// and while she stands, the infection runs on its own — every round an infected enemy passes it to one of its own
    /// beside it, one time in three.
    Contagion,
    /// Память роя (the Hive Mind, its run's rule): the swarm remembers the kind of enemy (index `k` into `KNOWN`) that
    /// killed the most of it in a battle, and goes for it first for the rest of the run.
    Knows { k: u8 },
    /// Громоотвод (a module of the Foundry's): lightning from the sky goes for it three times as readily and runs off
    /// into the ground, as does a jolt through slime — neither does it any harm.
    Grounded,
    /// Сухой хитин (a doctrine of the swarm's): its fallen leave a dry crust, not slime — lightning does not run
    /// through it, and nothing nests in it.
    DryChitin,
    /// A set of finds of one element (three or more in the army): what it does for the whole side (`Element`).
    Set { e: Element },
    /// Раскалённая броня (a module): whoever strikes it in melee catches fire.
    HotArmor,
    /// Огненные (an elite's): its blows set alight; fire does it a quarter.
    Blazing,
    /// В масле (an elite's): the battle begins with oil under it.
    Oily,
    /// В слизи (an elite's): the battle begins with slime under it.
    Slimy,
    /// Живучие (an elite's): the first blow that would kill it leaves it on 1.
    Stubborn,
    /// A boss: at half its health it goes into its second phase (each leader its own).
    Boss,
    // ---- not numbers but habits (CONCEPT.md, «Повадки вместо цифр»)
    /// Ростовой щит: the allies right behind it (beside it, farther from the shooter) can't be shot at.
    TowerShield,
    /// Длинный ствол: a shot goes through — the enemy right behind the target takes half.
    Pierce,
    /// Искрящий молот: every blow throws a spark — an enemy beside the target catches fire.
    Sparks,
    /// Живой факел: burns the whole battle and takes no harm of it; its blows set alight, it lights the night.
    Torch,
    /// Длинные лапы: the sting reaches the one right behind the target too.
    Reach,
    /// Дальний плевок: the acid splashes the target's neighbours, half each.
    Splash,
    /// Бугристые надкрылья: a blow its shell stops whole glances off into another enemy beside it.
    Ricochet,
    /// Известковый панцирь: curled up, it draws the blows of the enemies beside it (a living shield).
    Bulwark,
    /// Знамя (the leader brings it): when half the army has fallen, the banner rises — whoever stands picks it up — the
    /// rest are mended a quarter and stand fast, once a battle.
    Banner,
    /// Кровавая чаша: its kill mends its own beside it, 2 each.
    Chalice,
    /// Тяжёлая наковальня, Рвущие челюсти: every blow that gets through takes a point of armor off.
    Crush,
    /// Колокол тревоги (on the leader): every fourth round it rings — the enemies within 2 cells of it are stunned.
    Bell,
    /// Гранёные кости: the highest roll of the die strikes double and stuns.
    LoadedDice,
    /// Песочные часы: the first blow that would kill it turns its time back — to the health it had as the round began.
    Hourglass,
    /// Фонарь дальнобоя: its shots set alight, and it sees in the night.
    Flare,
    /// Сброс плит (the Colossus): with every quarter of his health lost a plate falls off onto the enemies beside him.
    ShedPlates,
    /// Цепной шокер (the Inventor): his blow leaps to two enemies beside the target, half each.
    Chain,
    /// Пила-вихрь (the Maniac): his blow cuts every enemy beside him.
    Whirl,
    /// Каменный дождь (the Architect): his walls, falling, crush the enemies beside them.
    Rubble,
    /// Кирпичи навесом (the Architect): his throw lands on the whole cell, the small ones there stunned one time in two.
    Lob,
    /// Живой щит (the Mother): a blow at her is taken by a body of hers beside her.
    Escort,
    /// Воля роя (the Hive Mind): his swarm does not flee.
    Rally,
    /// Пси-отпор (the Hive Mind): whoever strikes him close loses its thought — skips its next blow.
    MindWard,
    /// Отрыжка (the Devourer): a meal digested, he spits its acid over the enemies within 2 cells.
    Belch,
    /// Кислотная кровь (the Devourer): whoever strikes him close is splashed with acid.
    AcidBlood,
    /// Чумная кровь (the Plague): whoever kills a body of hers close is infected.
    PlagueBlood,
    /// Кокон (the Plague): the first blow that would kill her, she pupates: half her health back, two rounds still.
    Cocoon,
    /// Ударная волна (the Colossus): his quake throws back all it strikes (and they bowl over the others).
    Shockwave,
    /// Засада (the Mother): her larvae hatch out of the ground beside the nearest enemy.
    Ambush,
    /// Mends 2 a round (the Devourer who ate Mechanics).
    Regen,
}

/// What a find is made of, its element: three finds of one element in an army make a set (`Trait::Set`) — the
/// Foundry's fire, lightning, iron and impact, the swarm's nest, venom, wing and shell.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Element {
    Fire,
    Volt,
    Iron,
    Impact,
    Nest,
    Venom,
    Wing,
    Shell,
}

impl Element {
    pub const ALL: [Element; 8] = [Element::Fire, Element::Volt, Element::Iron, Element::Impact, Element::Nest, Element::Venom, Element::Wing, Element::Shell];

    pub fn key(self) -> &'static str {
        match self {
            Element::Fire => "fire",
            Element::Volt => "volt",
            Element::Iron => "iron",
            Element::Impact => "impact",
            Element::Nest => "nest",
            Element::Venom => "venom",
            Element::Wing => "wing",
            Element::Shell => "shell",
        }
    }

    pub fn bit(self) -> u16 {
        1 << (self as u16)
    }
}

/// What an elite enemy is besides its numbers (a road with an elite brings one): armored, blazing, standing in oil or
/// in slime, hard to kill, unstoppable.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum Affix {
    #[default]
    None,
    Armored,
    Blazing,
    Oily,
    Slimy,
    Stubborn,
    Unstoppable,
}

impl Affix {
    pub const ALL: [Affix; 6] = [Affix::Armored, Affix::Blazing, Affix::Oily, Affix::Slimy, Affix::Stubborn, Affix::Unstoppable];

    pub fn key(self) -> &'static str {
        match self {
            Affix::None => "none",
            Affix::Armored => "armored",
            Affix::Blazing => "blazing",
            Affix::Oily => "oily",
            Affix::Slimy => "slimy",
            Affix::Stubborn => "stubborn",
            Affix::Unstoppable => "unstoppable",
        }
    }

    /// Puts it on a body of the enemy.
    pub fn apply(self, t: &mut Template) {
        let mut add = |x: Trait| {
            if !t.traits.contains(&x) {
                t.traits.push(x);
            }
        };
        match self {
            Affix::None => {}
            Affix::Armored => t.armor += 2,
            Affix::Blazing => {
                add(Trait::Blazing);
                add(Trait::FireResist75);
            }
            Affix::Oily => add(Trait::Oily),
            Affix::Slimy => add(Trait::Slimy),
            Affix::Stubborn => add(Trait::Stubborn),
            Affix::Unstoppable => add(Trait::Unstoppable),
        }
    }
}

/// The enemies the Hive Mind can remember (Память роя), by units.ron key: `Trait::Knows { k }` is an index here.
pub const KNOWN: [&str; 10] = ["strazh", "mudrets", "gorn", "orudie", "mekhanik", "kamenshchik", "otets_kolossa", "izobretatel", "manyak", "zodchiy"];

/// What the sky and the earth do over a battle (a road on the map can bring it): nothing, a thunderstorm — lightning
/// from the sky, drawn to iron; an earthquake — the ground splits across the field; the night — shooters see only
/// what burns or glows past three cells.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum Weather {
    #[default]
    Clear,
    Storm,
    Quake,
    Night,
}

impl Weather {
    pub fn key(self) -> &'static str {
        match self {
            Weather::Clear => "clear",
            Weather::Storm => "storm",
            Weather::Quake => "quake",
            Weather::Night => "night",
        }
    }
}

/// Abilities with a condition.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Ability {
    /// Every `every` rounds, instead of the normal attack: area blow on a cell and its neighbours (Мортира).
    Volley { every: u32, die: u32, bonus: i32, dmg: Dmg },
    /// Every `every` rounds: mend the most damaged adjacent golem (Ремонт).
    Repair { every: u32, amount: i32 },
    /// Every `every` rounds, instead of the normal attack: one bolt within `range`
    /// (Грозовая катушка: range 1; Голова-катапульта: range 3).
    Bolt { every: u32, die: u32, bonus: i32, dmg: Dmg, range: u32 },
    /// The melee blow also hits a second adjacent enemy (Кистень).
    Flail,
    /// The first `n` damaging blows of the battle are absorbed (Броневые листы).
    Plates(u32),
    /// Ranged unit with an enemy adjacent fires at up to 3 adjacent enemies at full power (Картечь).
    PointBlank,
    /// Once per round takes a blow meant for an adjacent allied golem (Перехват).
    Intercept,
    /// Every `every` rounds, instead of attacking: adjacent enemies miss next round (Светляк).
    Flash { every: u32 },
    /// Every `every` rounds, instead of attacking: sticky poison on an enemy within its range — glued to its
    /// cell next round (it can hit, it can't walk; machines too) and `1–die` poison (not machines) (Паук-плевун).
    Spit { every: u32, die: u32 },
    /// Every `every` rounds: `n` larvae (workers) hatch next to it; they act from the next round (Матка).
    Brood { every: u32, n: u32 },
    /// Every `every` rounds: marks the most dangerous enemy; allies who reach it hit it first, +1 (Разум улья).
    Mark { every: u32 },
    /// Every `every` rounds, instead of the spell: an adjacent allied golem hits twice as hard this round (Перегрузка).
    Overload { every: u32 },
    /// Every `every` rounds, instead of the spell: a fireball within `range` — the cell and its neighbours,
    /// fire, sets them burning (Огненный шар).
    Fireball { every: u32, die: u32, bonus: i32, range: u32 },
    /// Every `every` rounds, instead of attacking: a blunt blow on every enemy within `radius`; the small ones (size
    /// 1–2) that take damage are stunned for their next attack (Сотрясение, Отец колосса).
    Quake { every: u32, die: u32, bonus: i32, radius: u32 },
    /// As the battle begins: the modules of allied golems within two cells a level stronger — a round sooner, a die
    /// bigger (Аугменты, Изобретатель).
    Augment,
    /// Every `every` rounds (besides attacking): an allied golem within two cells gets a module at random until the
    /// battle ends (Маньяк).
    Tinker { every: u32 },
    /// Бросок титана (Отец колосса): every `every` rounds, instead of his blow, he grabs the biggest enemy beside him (up
    /// to size 5) and hurls it into the thickest of its own within `range` cells: it takes 3–12 blunt, everyone of its
    /// side round where it lands 1–6, the small ones stunned.
    Hurl { every: u32, range: u32 },
    /// Чертёж (Зодчий): as the battle begins `n` wall segments rise in front of his army — two by two with a gap of two
    /// between, corridors for the enemy; while a wall stands his army waits behind them (Гарнизон) and steps out only
    /// to an enemy within 3 cells (up to round 10).
    Blueprint { n: u32 },
    /// Кладка стены (Каменщик): every `every` rounds, instead of his blow, lays a wall segment beside him on the enemy's
    /// side (at most 3 a battle), once an enemy is within 8 cells — under its nose too.
    Lay { every: u32 },
    /// Подмена (Разум улья): every `every` rounds (besides his blow) he swaps places in the minds of two: the enemy's
    /// shooter or leader safest behind its line and a body of his own in the thick of the swarm — the shooter wakes up
    /// among the swarm, dazed (it skips its next blow), the body stands at the enemy's back.
    Swap { every: u32 },
    /// Глотает целиком (Пожиратель): every `every` rounds, instead of his bite, he swallows an enemy beside him smaller
    /// than himself, whole. Inside it is digested — 1–6 a round, +2 for each stage of his growth, past its armor — and it
    /// strikes him from within, past his. Digested, it is his meal; he falls — it bursts out of him, dazed.
    Swallow { every: u32 },
    /// Пандемия (Чума, her run's rule): as the battle begins, `n` bodies of the enemy are infected already.
    Pandemic { n: u32 },
}

impl Ability {
    /// Two of one kind put together (a leader grown twice the same way): the better of each number, so the second
    /// growth adds to the first rather than taking its place.
    pub fn stronger(self, other: Ability) -> Ability {
        use Ability::*;
        match (self, other) {
            (Brood { every: a, n: x }, Brood { every: b, n: y }) => Brood { every: a.min(b), n: x.max(y) },
            (Mark { every: a }, Mark { every: b }) => Mark { every: a.min(b) },
            (Tinker { every: a }, Tinker { every: b }) => Tinker { every: a.min(b) },
            (Quake { every: a, die: d, bonus: x, radius: r }, Quake { every: b, die: e, bonus: y, radius: q }) => {
                Quake { every: a.min(b), die: d.max(e), bonus: x.max(y), radius: r.max(q) }
            }
            (Hurl { every: a, range: r }, Hurl { every: b, range: q }) => Hurl { every: a.min(b), range: r.max(q) },
            (Blueprint { n: a }, Blueprint { n: b }) => Blueprint { n: a.max(b) },
            (Swap { every: a }, Swap { every: b }) => Swap { every: a.min(b) },
            (Swallow { every: a }, Swallow { every: b }) => Swallow { every: a.min(b) },
            (Pandemic { n: a }, Pandemic { n: b }) => Pandemic { n: a.max(b) },
            (_, o) => o,
        }
    }

    /// A module a level stronger: a round sooner and a die bigger (more mended, one more plate); the same when it has
    /// no numbers to raise.
    pub fn level_up(self) -> Ability {
        use Ability::*;
        let sooner = |e: u32| e.saturating_sub(1).max(1);
        match self {
            Volley { every, die, bonus, dmg } => Volley { every: sooner(every), die: die + 2, bonus, dmg },
            Bolt { every, die, bonus, dmg, range } => Bolt { every: sooner(every), die: die + 2, bonus, dmg, range },
            Repair { every, amount } => Repair { every: sooner(every), amount: amount + 2 },
            Overload { every } => Overload { every: sooner(every) },
            Fireball { every, die, bonus, range } => Fireball { every: sooner(every), die: die + 2, bonus, range },
            Plates(n) => Plates(n + 1),
            other => other,
        }
    }

    /// Whether a level makes it stronger (else a level gives the body a harder blow instead).
    pub fn levels(&self) -> bool {
        self.level_up() != *self
    }

    /// How many rounds between its uses, for those used every so often.
    pub fn every(&self) -> Option<u32> {
        match *self {
            Ability::Volley { every, .. }
            | Ability::Repair { every, .. }
            | Ability::Bolt { every, .. }
            | Ability::Flash { every }
            | Ability::Spit { every, .. }
            | Ability::Brood { every, .. }
            | Ability::Mark { every }
            | Ability::Overload { every }
            | Ability::Fireball { every, .. }
            | Ability::Quake { every, .. }
            | Ability::Tinker { every }
            | Ability::Hurl { every, .. }
            | Ability::Lay { every }
            | Ability::Swap { every }
            | Ability::Swallow { every } => Some(every),
            _ => None,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Template {
    pub name: std::borrow::Cow<'static, str>,
    pub size: u32,
    pub hp: i32,
    pub die: u32,
    pub bonus: i32,
    pub dmg: Dmg,
    pub init: u32,
    pub armor: i32,
    pub morale: u32,
    pub speed: u32,
    pub range: u32,
    pub armor_type: ArmorType,
    pub golem: bool,
    pub traits: Vec<Trait>,
    pub abilities: Vec<Ability>,
    /// The modules put on it (finds.ron keys) with their levels I–III: only for the picture (its modules shown on it
    /// in battle); what they give is already in the numbers, traits and abilities above.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub mods: Vec<(String, u8)>,
}

impl Template {
    pub fn has(&self, t: Trait) -> bool {
        self.traits.contains(&t)
    }

    /// Whether it counts as its side's army: a midge cloud, a ghost of a mirage, a puppet machine and a wall do not (a side of
    /// them alone has lost; they are not counted as fallen).
    pub fn is_army(&self) -> bool {
        !self.has(Trait::Cloud) && !self.has(Trait::Ghost) && !self.has(Trait::Puppet) && !self.has(Trait::Wall)
    }

    pub fn fear(&self) -> Option<(u32, u32)> {
        self.traits.iter().find_map(|t| match t {
            Trait::Fear { die, radius } => Some((*die, *radius)),
            _ => None,
        })
    }

    pub fn has_ability(&self, pred: impl Fn(&Ability) -> bool) -> bool {
        self.abilities.iter().any(pred)
    }

    pub fn with(mut self, a: Ability) -> Self {
        self.abilities.push(a);
        self
    }

    pub fn with_trait(mut self, t: Trait) -> Self {
        self.traits.push(t);
        self
    }

    /// The Inventor's frames: one size smaller (a leadership point cheaper), −1 to the damage bonus.
    pub fn smaller(mut self) -> Self {
        self.size -= 1;
        self.bonus -= 1;
        self
    }

    pub fn morale_eff(&self) -> u32 {
        if self.has(Trait::Mindless) {
            99
        } else {
            self.morale
        }
    }
}

/// Damage that gets through: vulnerability, stun, armor (halved by Пробивной), resistance,
/// elemental resistance, metal conducting lightning. The order of docs/CONCEPT.md.
pub fn mitigate(raw: i32, dmg: Dmg, t: &Template, armor_now: i32, stunned: bool, probivnoy: bool) -> i32 {
    let at = t.armor_type;
    if at.immune(dmg) || (dmg == Dmg::Poison && t.has(Trait::PoisonImmune)) {
        return 0;
    }
    let mut d = raw;
    if at.weak_to(dmg) {
        d *= 2;
    }
    if stunned {
        d += 1;
    }
    if dmg == Dmg::Fire && t.has(Trait::Cloud) {
        d *= 3;
    }
    if dmg != Dmg::Fire && dmg != Dmg::Poison {
        let mut arm = armor_now.max(0);
        if probivnoy {
            arm /= 2;
        }
        d -= arm;
    }
    if d <= 0 {
        return 0;
    }
    if at.resists(dmg) {
        d /= 2;
    }
    if dmg == Dmg::Fire && t.has(Trait::FireResist75) {
        d = (d / 4).max(1);
    }
    if dmg == Dmg::Shock && at.metal() {
        d = d * 3 / 2;
    }
    d.max(0)
}
