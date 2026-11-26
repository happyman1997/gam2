//! A run (поход): the class and leader chosen, fifteen battles, a boss every fifth; before each step a choice of two
//! or three roads — a battle (the enemy's whole army in view, its reward), an elite, the trader, an event, a camp.
//! Between battles: the spoils (currency, a find — one of three recruits, an artifact from an elite or a boss).
//!
//! Who the enemy is stays an open question of the concept; for now each class fights the other (the only armies
//! the game can draw). The enemy is fitted to the player's army: candidates of growing strength are played out a
//! few dozen times and the strongest one still beaten often enough is taken — the share falls from about 85 % at
//! the start to about 65 % by the end, 60 % for an elite, 50 % for a boss. These numbers are a frame to play in,
//! not balance.
//!
//! Losses stay: a golem killed in battle is broken (it sits battles out until repaired — at a camp or the trader);
//! a creature of the swarm killed is gone (the swarm grows back at the hive). A leader always comes back.
//! A battle lost ends the run.

use crate::battle::Battle;
use crate::data::{self, Caste, Form};
use crate::model::{Ability, Template, Trait};
use crate::rng::Rng;
use serde::{Deserialize, Serialize};

pub const FIGHTS: u32 = 15;
/// The «form» a mutation of the whole swarm is kept under (`Run::breeds`).
pub const SWARM: &str = "*";
pub const BOSS_EVERY: u32 = 5;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Class {
    Foundry,
    Swarm,
}

impl Class {
    pub fn other(self) -> Class {
        match self {
            Class::Foundry => Class::Swarm,
            Class::Swarm => Class::Foundry,
        }
    }
    /// The start armies of the four leaders (armies.ron).
    pub fn leaders(self) -> [&'static str; 4] {
        match self {
            Class::Foundry => ["start_otets", "start_izobretatel", "start_manyak", "start_zodchiy"],
            Class::Swarm => ["start_matka", "start_razum", "start_pozhiratel", "start_kukushka"],
        }
    }
}

/// An artifact: always passive, it changes the player's army as the battle begins. Each has its icon in the kit's
/// artifact atlas (its key).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Artifact {
    /// Знамя: +3 morale — they hold under fear.
    Znamya,
    /// Сапоги скорохода: +1 speed to everyone.
    Sapogi,
    /// Кровавая чаша: a fifth more health.
    Chasha,
    /// Тяжёлая наковальня: +3 to every blow, but everyone strikes last.
    Nakovalnya,
    /// Колокол тревоги: +2 initiative — they strike first.
    Kolokol,
    /// Гранёные кости: the spread 2 narrower, +2 to every blow — an army you can count on.
    Grani,
    /// Песочные часы: +1 armour to everyone.
    Chasy,
    /// Фонарь: shooters reach one cell further.
    Fonar,
}

impl Artifact {
    pub const ALL: [Artifact; 8] = [
        Artifact::Znamya,
        Artifact::Sapogi,
        Artifact::Chasha,
        Artifact::Nakovalnya,
        Artifact::Kolokol,
        Artifact::Grani,
        Artifact::Chasy,
        Artifact::Fonar,
    ];

    /// The icon's name in the artifact atlas, and the key of its words in the game.
    pub fn key(self) -> &'static str {
        match self {
            Artifact::Znamya => "banner",
            Artifact::Sapogi => "boots",
            Artifact::Chasha => "chalice",
            Artifact::Nakovalnya => "anvil",
            Artifact::Kolokol => "bell",
            Artifact::Grani => "dice",
            Artifact::Chasy => "hourglass",
            Artifact::Fonar => "fog_lantern",
        }
    }

    pub fn apply(self, t: &mut Template) {
        match self {
            Artifact::Znamya => t.morale += 3,
            Artifact::Sapogi => t.speed += 1,
            Artifact::Chasha => t.hp += (t.hp + 4) / 5,
            Artifact::Nakovalnya => {
                t.bonus += 3;
                t.init = 0;
            }
            Artifact::Kolokol => t.init += 2,
            Artifact::Grani => {
                t.die = t.die.saturating_sub(2).max(1);
                t.bonus += 2;
            }
            Artifact::Chasy => t.armor += 1,
            Artifact::Fonar => {
                if t.range > 1 {
                    t.range += 1
                }
            }
        }
    }
}

/// How much of the deployment zone an army may fill, in quarter-cells (a cell takes four small ones, two soldiers;
/// a golem its footprint's cells): three quarters of it, the rest is the room the formation needs.
pub const ROOM: i32 = crate::battle::ZONE * crate::battle::H * 4 * 3 / 4;

/// Battles a step of the enemy's fitting is measured by (fewer and an enemy of one strength comes out anywhere
/// from two thirds to half again of it).
const FIT_TRIES: u32 = 40;

/// How many steps an enemy's ladder has: enough to fill its zone with the smallest of them.
const LADDER: usize = (ROOM / 3) as usize;

pub fn room_cost(t: &Template) -> i32 {
    let f = crate::battle::footprint(t.size);
    match t.size {
        1 => 1,
        2 => 2,
        _ => f * f * 4,
    }
}

/// One of the player's army.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Member {
    pub id: u32,
    pub t: Template,
    /// A golem broken in battle: it sits battles out until repaired.
    pub broken: bool,
    /// The modules put on it in the run (finds.ron keys), in its cells.
    #[serde(default)]
    pub mods: Vec<String>,
    /// The level of each module (I–III), by its place in `mods`; missing — I.
    #[serde(default)]
    pub levels: Vec<u8>,
}

/// The highest level of a module.
pub const MAX_LEVEL: u8 = 3;
/// Metal a melting costs (CONCEPT.md, «Переплавка»).
pub const MELT: i32 = 3;
/// Biomass a form's first evolution costs, and how much more each next one.
pub const EVO_PRICE: i32 = 8;
pub const EVO_STEP: i32 = 4;

impl Member {
    /// The level of its `j`-th module (1–3).
    pub fn level(&self, j: usize) -> u8 {
        self.levels.get(j).copied().unwrap_or(1).clamp(1, MAX_LEVEL)
    }

    fn set_level(&mut self, j: usize, lv: u8) {
        while self.levels.len() < self.mods.len() {
            self.levels.push(1);
        }
        self.levels[j] = lv.clamp(1, MAX_LEVEL);
    }

    fn put(&mut self, key: String, lv: u8) {
        self.levels.truncate(self.mods.len());
        while self.levels.len() < self.mods.len() {
            self.levels.push(1);
        }
        self.mods.push(key);
        self.levels.push(lv);
    }

    /// Its `j`-th module taken off: the key and its level.
    fn take_off(&mut self, j: usize) -> (String, u8) {
        let lv = self.level(j);
        if j < self.levels.len() {
            self.levels.remove(j);
        }
        (self.mods.remove(j), lv)
    }
}

/// What a find is: bodies to take in, a module for a golem, a mutation for a breed.
#[derive(Clone, Debug, Default, PartialEq, Serialize, Deserialize)]
pub enum Find {
    #[default]
    Units,
    Module(String),
    Mutation(String),
}

/// Where a module or a mutation goes: a golem of the army (its index), a breed (its form's name).
#[derive(Clone, Debug, PartialEq)]
pub enum Target {
    Member(usize),
    Form(String),
}

/// A body's breed: its form's name without the caste («Оса (рабочая)» → «Оса»).
pub fn form_of(t: &Template) -> &str {
    t.name.split(" (").next().unwrap_or(&t.name)
}


/// Something to take into the army: a golem, a flock of the swarm. `key` names it for the game (the portrait, the
/// name): a unit's key in units.ron, or «form.caste» of the swarm.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Offer {
    pub key: String,
    pub units: Vec<Template>,
    pub price: i32,
    #[serde(default)]
    pub find: Find,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Kind {
    Fight,
    Elite,
    Boss,
    Merchant,
    Event,
    Camp,
}

impl Kind {
    pub fn is_battle(self) -> bool {
        matches!(self, Kind::Fight | Kind::Elite | Kind::Boss)
    }
}

/// A road at the fork.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Node {
    pub kind: Kind,
    /// The enemy's army (a battle), the army it is grown from (its leader's start army, or «golems» / «swarm»).
    pub enemy: Vec<Template>,
    pub enemy_key: String,
    /// The currency the battle pays.
    pub reward: i32,
    /// Which event (an Event road).
    pub event: usize,
    /// How hard the battle is: 1 — the usual, 2 — dangerous (pays more, a rarer find), 3 — a boss.
    #[serde(default)]
    pub danger: u8,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum Reward {
    Money(i32),
    /// The Foundry: every broken golem mended, at this price (2 metal a golem).
    Repair(i32),
    /// The swarm: the brood — new bodies of the forms that fell, hatched from the survivors.
    Brood(Vec<Template>),
    /// One of these into the army, or none (a little currency for passing).
    Find(Vec<Offer>),
    Artifact(Artifact),
    /// After a boss: one of these for the leader, for good (keys of growth.ron).
    Growth(Vec<String>),
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Stats {
    pub won: u32,
    pub kills: u32,
    pub earned: i32,
    pub lost: u32,
}

/// The trader's stall: recruits, artifacts, one service (repairs for the Foundry, a clutch of workers for the swarm).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Shop {
    pub offers: Vec<(Offer, bool)>,
    pub artifacts: Vec<(Artifact, i32, bool)>,
    pub service: i32,
    pub service_used: bool,
}

/// What an event offers: each option's effect (the game words them).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum Effect {
    Money(i32),
    /// Pay currency for an artifact.
    BuyArtifact(i32),
    /// Give a random fighter (not the leader) for an artifact.
    TradeUnit,
    /// A random golem broken / random creatures lost, for currency.
    Hurt(i32),
    /// Recruits join: a golem (Foundry) or a clutch of workers (swarm).
    Join,
    /// One fighter joins: a golem (Foundry) or a soldier of some form (swarm).
    Recruit,
    /// All fighters +health.
    Feast,
    Leave,
}

/// The events: (key — the game's words for it, the class it is for or None for both, its options).
pub const EVENTS: [(&str, Option<Class>, [Effect; 3]); 6] = [
    ("forge", Some(Class::Foundry), [Effect::Money(12), Effect::Feast, Effect::Leave]),
    ("rockfall", Some(Class::Foundry), [Effect::Hurt(15), Effect::Money(-4), Effect::Leave]),
    ("nest", Some(Class::Swarm), [Effect::Hurt(14), Effect::Join, Effect::Leave]),
    ("carcass", Some(Class::Swarm), [Effect::Money(8), Effect::Feast, Effect::Leave]),
    ("shadow", None, [Effect::TradeUnit, Effect::BuyArtifact(15), Effect::Leave]),
    ("deserter", None, [Effect::Recruit, Effect::Money(6), Effect::Leave]),
];

/// What a battle did to the player's army: who of `fighters()` was killed, how many of the enemy fell.
pub struct BattleResult {
    pub won: bool,
    pub dead: Vec<usize>,
    pub kills: u32,
    /// How many of the player's army each kind of enemy (`model::KNOWN` index) killed (Память роя).
    pub foe_kills: Vec<(u8, u32)>,
    /// The kinds of enemy (`model::KNOWN` indexes) the player's Devourer ate (Ты — то, что ты ешь).
    pub eaten: Vec<u8>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Run {
    pub class: Class,
    pub leader: usize,
    pub seed: u64,
    rng: Rng,
    /// Battles won.
    pub fight: u32,
    pub money: i32,
    pub army: Vec<Member>,
    next_id: u32,
    /// The leader's member id: it always comes back from a battle and is never given away.
    pub leader_id: u32,
    pub artifacts: Vec<Artifact>,
    /// The swarm's mutations: (form, mutation key). A found mutation goes onto the whole swarm — form `SWARM`, every
    /// body of every form and every brood after; an evolution (bought) onto its own form. (A save from before has
    /// found ones on a form: they stay there.)
    #[serde(default)]
    pub breeds: Vec<(String, String)>,
    /// How the leader has grown after the bosses (keys of growth.ron).
    #[serde(default)]
    pub growth: Vec<String>,
    /// Память роя (the Hive Mind): the kinds of enemy the swarm remembers, `model::KNOWN` indexes, oldest first.
    #[serde(default)]
    pub memory: Vec<u8>,
    /// Ты — то, что ты ешь (the Devourer): how many of each kind of enemy (`model::KNOWN` index) it has eaten this run.
    #[serde(default)]
    pub diet: Vec<u32>,
    /// The roads to choose from now.
    pub path: Vec<Node>,
    /// A stop (trader, event, camp) was taken since the last battle: the next fork is battles only.
    pub stopped: bool,
    pub stats: Stats,
    /// Some(true) — the last boss beaten; Some(false) — a battle lost.
    pub over: Option<bool>,
}

impl Run {
    pub fn new(class: Class, leader: usize, seed: u64) -> Run {
        let army = data::army(class.leaders()[leader]);
        let mut run = Run {
            class,
            leader,
            seed,
            rng: Rng::new(seed),
            fight: 0,
            money: match class {
                Class::Foundry => 20,
                Class::Swarm => 10,
            },
            army: vec![],
            next_id: 0,
            leader_id: 0,
            breeds: vec![],
            growth: vec![],
            memory: vec![],
            diet: vec![],
            artifacts: vec![],
            path: vec![],
            stopped: false,
            stats: Stats::default(),
            over: None,
        };
        // the leader: the one with the trait, else the biggest (the Father of the Colossus has no trait yet)
        let lead = army
            .iter()
            .position(|t| t.has(Trait::Leader))
            .or_else(|| (0..army.len()).max_by_key(|&i| army[i].size))
            .unwrap_or(0);
        for (i, t) in army.into_iter().enumerate() {
            if i == lead {
                run.leader_id = run.next_id;
            }
            run.add(t);
        }
        run.fork();
        run
    }

    fn add(&mut self, t: Template) {
        self.army.push(Member { id: self.next_id, t, broken: false, mods: vec![], levels: vec![] });
        self.next_id += 1;
    }

    fn roll(&mut self, n: usize) -> usize {
        (self.rng.next_u64() % n.max(1) as u64) as usize
    }

    /// The battle number the next battle has (1-based).
    pub fn next_fight(&self) -> u32 {
        self.fight + 1
    }

    pub fn boss_next(&self) -> bool {
        self.next_fight().is_multiple_of(BOSS_EVERY)
    }

    /// Who goes into battle: the army without the broken, the leader first, then the rest in their order as long as
    /// the deployment zone holds them (the others wait in reserve), the artifacts on them; and for each, its
    /// member's index.
    pub fn fighters(&self) -> (Vec<Template>, Vec<usize>) {
        let mut out = vec![];
        let mut idx = vec![];
        let mut used = 0;
        let order = (0..self.army.len()).filter(|&i| self.is_leader(&self.army[i])).chain((0..self.army.len()).filter(|&i| !self.is_leader(&self.army[i])));
        for i in order {
            let m = &self.army[i];
            if m.broken {
                continue;
            }
            let c = room_cost(&m.t);
            if used + c > ROOM {
                continue;
            }
            used += c;
            out.push(self.body(m));
            idx.push(i);
        }
        (out, idx)
    }

    /// A member as it goes into battle: its modules, its breed's mutations, the artifacts on it.
    pub fn body(&self, m: &Member) -> Template {
        let mut t = m.t.clone();
        for g in self.growth.iter().filter_map(|k| data::growth_by_key(k)) {
            if self.is_leader(m) {
                g.leader.apply(&mut t);
            } else {
                g.army.apply(&mut t);
            }
        }
        let finds = data::finds();
        for (j, key) in m.mods.iter().enumerate() {
            if let Some(f) = finds.modules.iter().find(|f| &f.key == key) {
                let had = t.abilities.len();
                f.give.apply(&mut t);
                t.mods.push((key.clone(), m.level(j)));
                // a level above I: what the module gave a round sooner and a die bigger — or, with nothing of that
                // to raise, a harder blow
                for _ in 1..m.level(j) {
                    if t.abilities[had..].iter().any(|a| a.levels()) {
                        for a in &mut t.abilities[had..] {
                            *a = a.level_up();
                        }
                    } else {
                        t.bonus += 1;
                    }
                }
            }
        }
        // the swarm's mutations onto every body of it (not the leader), a form's evolutions onto that form; the
        // leader's own mutations (the Devourer's) onto the leader alone
        if self.class == Class::Swarm {
            let lead = self.is_leader(m);
            let form = form_of(&m.t).to_string();
            for key in self.mutations_of(&form) {
                if let Some(mu) = finds.mutations.iter().find(|x| &x.key == key).filter(|mu| mu.personal == lead) {
                    mu.give.apply(&mut t);
                }
            }
        }
        for a in &self.artifacts {
            a.apply(&mut t);
        }
        if self.is_leader(m) {
            // Память роя: the Hive Mind brings what the swarm remembers
            for &k in &self.memory {
                t.traits.push(Trait::Knows { k });
            }
            // Ты — то, что ты ешь: what the Devourer has eaten enough of is in him now
            for (k, &n) in self.diet.iter().enumerate() {
                if n >= DIET_STEP {
                    diet_gift(k, &mut t);
                }
            }
            // Пандемия: the Plague's world is sick — the more battles won, the more of the enemy come infected
            if t.has(Trait::Contagion) && self.stats.won >= PANDEMIC_EVERY {
                t.abilities.push(Ability::Pandemic { n: self.stats.won / PANDEMIC_EVERY });
            }
        }
        // the Devourer is hungry at the start of a run, till its swarm has killed enough
        let fed = data::rules().devourer_fed;
        if self.is_leader(m) && t.has(Trait::Grows) && self.stats.kills < fed {
            t.traits.push(Trait::Hungry { left: fed - self.stats.kills });
        }
        t
    }

    /// How many modules a golem takes (its cells): the Father of the Colossus four, a big frame three, the rest two.
    pub fn cells(&self, m: &Member) -> usize {
        let own = self.is_leader(m);
        let more: usize = self.growth.iter().filter_map(|k| data::growth_by_key(k)).map(|g| g.cells + if own { g.own_cells } else { 0 }).sum();
        more + match data::unit_key(&m.t.name) {
            Some("otets_kolossa") => 4,
            _ if m.t.size >= 5 => 3,
            _ => 2,
        }
    }

    // ---------------------------------------------------------------- leadership and the swarm's limit

    /// Bosses beaten so far.
    fn bosses_won(&self) -> u32 {
        self.fight / BOSS_EVERY
    }

    /// The Foundry's leadership: how much the army may hold — the leader's own at the start, more with every battle
    /// won and every boss (the Father of the Colossus's stays as it is).
    pub fn lead_cap(&self) -> u32 {
        let r = data::rules();
        let key = self.leader_key();
        let start = r.lead_start.get(key).copied().unwrap_or(10);
        if r.lead_fixed.iter().any(|k| k == key) {
            return start;
        }
        start + r.lead_fight * self.fight + r.lead_boss * self.bosses_won()
    }

    /// What a body costs in leadership: a golem by its kind, a smaller frame one less; leaders and summons nothing.
    pub fn lead_cost(t: &Template) -> u32 {
        let Some(key) = data::unit_key(&t.name) else { return 0 };
        let Some(&c) = data::rules().lead_cost.get(key) else { return 0 };
        c.saturating_sub(data::unit(key).size.saturating_sub(t.size))
    }

    /// The leadership the army holds now (the broken too: they are still the army's).
    pub fn lead_used(&self) -> u32 {
        self.army.iter().filter(|m| !self.is_leader(m)).map(|m| Self::lead_cost(&m.t)).sum()
    }

    /// The swarm's limit in points: the leader's own at the start, more with every battle won and every boss.
    pub fn limit(&self) -> u32 {
        let r = data::rules();
        let start = r.limit_start.get(self.leader_key()).copied().unwrap_or(100);
        start + r.limit_fight * self.fight + r.limit_boss * self.bosses_won()
    }

    /// What a body of the swarm costs of its limit: a worker 1, a soldier 3, a giant soldier 6.
    pub fn points(t: &Template) -> u32 {
        match t.size {
            0 | 1 => 1,
            2 => 3,
            3 => 6,
            _ => 10,
        }
    }

    /// The points the swarm holds now (its leader is free).
    pub fn points_used(&self) -> u32 {
        self.army.iter().filter(|m| !self.is_leader(m)).map(|m| Self::points(&m.t)).sum()
    }

    /// Whether these bodies can join: the Foundry's leadership must hold them; the swarm takes everything (and eats
    /// the extra — `trim`).
    pub fn can_recruit(&self, units: &[Template]) -> bool {
        match self.class {
            Class::Foundry => self.lead_used() + units.iter().map(Self::lead_cost).sum::<u32>() <= self.lead_cap(),
            Class::Swarm => true,
        }
    }

    /// The swarm over its limit eats the extra: workers before soldiers, the commonest kind first, the youngest of it
    /// first (CONCEPT.md, «Выводок», the selection), every `eaten_per_biomass` points a unit of biomass. How many
    /// were eaten.
    pub fn trim(&mut self) -> usize {
        if self.class != Class::Swarm {
            return 0;
        }
        let limit = self.limit();
        let mut used = self.points_used();
        let mut eaten = 0;
        let mut pts = 0;
        while used > limit {
            // the kind to eat from: the cheapest, then the commonest
            let mut count: std::collections::BTreeMap<(u32, &str), usize> = Default::default();
            for m in self.army.iter().filter(|m| !self.is_leader(m)) {
                *count.entry((Self::points(&m.t), &*m.t.name)).or_default() += 1;
            }
            let Some(((_, name), _)) = count.iter().min_by_key(|((p, _), n)| (*p, std::cmp::Reverse(**n))) else { break };
            let name = name.to_string();
            let Some(i) = (0..self.army.len()).rev().find(|&i| !self.is_leader(&self.army[i]) && *self.army[i].t.name == *name) else { break };
            let p = Self::points(&self.army[i].t);
            self.army.remove(i);
            used -= p;
            pts += p;
            eaten += 1;
        }
        self.earn((pts / data::rules().eaten_per_biomass.max(1)) as i32);
        eaten
    }

    /// The mutations a form's bodies carry: the whole swarm's, then its own (evolutions).
    pub fn mutations_of<'a>(&'a self, form: &'a str) -> impl Iterator<Item = &'a String> + 'a {
        self.breeds.iter().filter(move |(f, _)| f == SWARM || f == form).map(|(_, k)| k)
    }

    /// The swarm's mutations: what its genome holds.
    pub fn genome(&self) -> usize {
        self.breeds.iter().filter(|(f, _)| f == SWARM).count()
    }

    /// Whether the genome holds no more.
    pub fn genome_full(&self) -> bool {
        self.genome() >= data::rules().genome
    }

    /// Whether the whole swarm has a mutation.
    pub fn has_mutation(&self, key: &str) -> bool {
        self.breeds.iter().any(|(f, k)| f == SWARM && k == key)
    }

    /// The leader's key in units.ron.
    pub fn leader_key(&self) -> &'static str {
        self.army.iter().find(|m| self.is_leader(m)).and_then(|m| data::unit_key(&m.t.name)).unwrap_or("")
    }

    /// Two ways for the leader to grow, of those not taken yet (fewer when fewer are left).
    pub fn growth_offer(&mut self) -> Vec<String> {
        let mut left: Vec<String> = data::growth(self.leader_key()).iter().map(|g| g.key.clone()).filter(|k| !self.growth.contains(k)).collect();
        let mut out = vec![];
        while out.len() < 2 && !left.is_empty() {
            let i = self.roll(left.len());
            out.push(left.remove(i));
        }
        out
    }

    /// The leader grows: for good, and the bodies it brings join the army.
    pub fn grow(&mut self, key: &str) {
        let Some(g) = data::growth_by_key(key) else { return };
        if self.growth.iter().any(|k| k == key) {
            return;
        }
        self.growth.push(key.to_string());
        for u in &g.units {
            self.add(data::unit(u));
        }
    }

    /// Whether a module can go on a member: the module made for its frame (or for any), a cell free, not on it yet.
    pub fn fits(&self, i: usize, key: &str) -> bool {
        let m = &self.army[i];
        let Some(f) = data::finds().modules.iter().find(|f| f.key == key) else { return false };
        let frame = data::unit_key(&m.t.name).unwrap_or("");
        (f.frames.is_empty() || f.frames.iter().any(|x| x == frame)) && m.mods.len() < self.cells(m) && !m.mods.iter().any(|x| x == key) && (m.t.golem || !f.frames.is_empty())
    }

    /// The breeds of the army (not the leader), each once.
    pub fn forms(&self) -> Vec<String> {
        let mut out: Vec<String> = vec![];
        for m in &self.army {
            if self.is_leader(m) {
                continue;
            }
            let f = form_of(&m.t).to_string();
            if !out.contains(&f) {
                out.push(f);
            }
        }
        out
    }

    /// Where a find can go: the golems a module fits; a found mutation the whole swarm (`SWARM`, one target — nothing to
    /// pick), an evolution its form; none for bodies (they join).
    /// Whether a module can be raised a level on a member: it is on it, below III (taking it again is the upgrade).
    pub fn raises(&self, i: usize, key: &str) -> bool {
        let m = &self.army[i];
        m.mods.iter().position(|x| x == key).is_some_and(|j| m.level(j) < MAX_LEVEL)
    }

    pub fn targets(&self, o: &Offer) -> Vec<Target> {
        match &o.find {
            Find::Units => vec![],
            Find::Module(k) => (0..self.army.len()).filter(|&i| self.fits(i, k) || self.raises(i, k)).map(Target::Member).collect(),
            Find::Mutation(k) => match data::finds().mutations.iter().find(|m| &m.key == k).and_then(|m| m.form.clone()) {
                // an evolution: its own form, if the swarm has it and not this one yet
                Some(only) => self
                    .forms()
                    .into_iter()
                    .filter(|f| *f == only && !self.breeds.iter().any(|(x, y)| x == f && y == k))
                    .map(Target::Form)
                    .collect(),
                // a found mutation: the whole swarm at once, nothing to choose
                None if !self.has_mutation(k) && !self.genome_full() => vec![Target::Form(SWARM.to_string())],
                None => vec![],
            },
        }
    }

    /// A find taken: bodies join; a module goes into a golem's cell; a mutation onto a breed. False if it can't go
    /// where it was asked.
    pub fn take_find(&mut self, o: &Offer, to: Option<&Target>) -> bool {
        match (&o.find, to) {
            (Find::Units, _) => {
                if !self.can_recruit(&o.units) {
                    return false;
                }
                self.recruit(o);
                true
            }
            (Find::Module(k), Some(Target::Member(i))) if *i < self.army.len() && self.raises(*i, k) => {
                let m = &mut self.army[*i];
                let j = m.mods.iter().position(|x| x == k).unwrap();
                let lv = m.level(j) + 1;
                m.set_level(j, lv);
                true
            }
            (Find::Module(k), Some(Target::Member(i))) if *i < self.army.len() && self.fits(*i, k) => {
                self.army[*i].put(k.clone(), 1);
                true
            }
            (Find::Mutation(k), Some(to @ Target::Form(f))) if self.targets(o).contains(to) => {
                self.breeds.push((f.clone(), k.clone()));
                true
            }
            _ => false,
        }
    }

    /// A form's evolutions (CONCEPT.md, «Эволюция форм»).
    pub fn evolutions(form: &str) -> Vec<&'static data::MutationFind> {
        data::finds().mutations.iter().filter(|m| m.form.as_deref() == Some(form)).collect()
    }

    /// What the next evolution of a form costs: each one more than the last.
    pub fn evo_price(&self, form: &str) -> i32 {
        let had = self.breeds.iter().filter(|(f, k)| f == form && Run::evolutions(form).iter().any(|e| &e.key == k)).count();
        EVO_PRICE + EVO_STEP * had as i32
    }

    /// A form evolved: every body of it, now and to come, for biomass.
    pub fn evolve(&mut self, form: &str, key: &str) -> bool {
        let price = self.evo_price(form);
        let ok = self.class == Class::Swarm
            && self.money >= price
            && self.forms().iter().any(|f| f == form)
            && Run::evolutions(form).iter().any(|e| e.key == key)
            && !self.breeds.iter().any(|(f, k)| f == form && k == key);
        if ok {
            self.money -= price;
            self.breeds.push((form.to_string(), key.to_string()));
        }
        ok
    }

    /// The workshop at the camp: a module moved from one golem to another (free) — where it fits, a cell free.
    pub fn move_module(&mut self, from: usize, j: usize, to: usize) -> bool {
        if from == to || from >= self.army.len() || to >= self.army.len() || j >= self.army[from].mods.len() {
            return false;
        }
        let key = self.army[from].mods[j].clone();
        if !self.fits(to, &key) {
            return false;
        }
        let (key, lv) = self.army[from].take_off(j);
        self.army[to].put(key, lv);
        true
    }

    /// Whether a module can be melted into another: both there, not the same, the other below III, on golems of one
    /// frame, the metal there.
    pub fn can_melt(&self, from: usize, j: usize, to: usize, k: usize) -> bool {
        let (Some(a), Some(b)) = (self.army.get(from), self.army.get(to)) else { return false };
        j < a.mods.len() && k < b.mods.len() && !(from == to && j == k) && b.level(k) < MAX_LEVEL && a.t.name == b.t.name && self.money >= MELT
    }

    /// The workshop's crucible: a module melted down, its metal another module's next level (for `MELT` metal).
    pub fn melt(&mut self, from: usize, j: usize, to: usize, k: usize) -> bool {
        if !self.can_melt(from, j, to, k) {
            return false;
        }
        self.money -= MELT;
        let lv = self.army[to].level(k) + 1;
        self.army[to].set_level(k, lv);
        self.army[from].take_off(j);
        true
    }

    pub fn is_leader(&self, m: &Member) -> bool {
        m.id == self.leader_id
    }

    pub fn broken(&self) -> usize {
        self.army.iter().filter(|m| m.broken).count()
    }

    /// Whether `a` wins at least half of up to `tries` battles against `b` (each on a seed of the run's own). The
    /// battles go eight at a time on every core, and stop as soon as one side is clearly ahead — a big army measured
    /// against a small one is not played forty times; the same seeds, the same answer.
    fn holds(&mut self, a: &[Template], b: &[Template], tries: u32) -> bool {
        use rayon::prelude::*;
        let base = self.rng.next_u64();
        let (mut won, mut played) = (0u32, 0u32);
        while played < tries {
            let n = (tries - played).min(8);
            won += (played..played + n)
                .into_par_iter()
                .map(|k| {
                    let mut bt = Battle::new(base.wrapping_add(k as u64 * 7919));
                    bt.add_armies(a, b);
                    u32::from(bt.run().winner == Some(0))
                })
                .sum::<u32>();
            played += n;
            let lost = played - won;
            if won.abs_diff(lost) > 6 {
                break;
            }
        }
        won * 2 >= played
    }

    /// How strong the enemy of a battle is, in the class's reference army (golems / swarm points): the difficulty
    /// curve of the player's class
    /// (curve.ron) by the battle's number, with a dangerous road, an elite or a boss on top. The same in every run —
    /// the player's army has no say.
    pub fn budget(class: Class, fight: u32, kind: Kind, danger: u8) -> f32 {
        let c = data::curve();
        let row = match class {
            Class::Foundry => &c.foundry,
            Class::Swarm => &c.swarm,
        };
        let base = row[(fight.max(1) as usize - 1).min(row.len() - 1)];
        base * match (kind, danger) {
            (Kind::Boss, _) => c.boss,
            (Kind::Elite, _) => c.elite,
            (_, 2) => c.danger,
            _ => 1.0,
        }
    }

    /// The enemy for a battle of `kind`: a base (a leader's army for a boss) and a ladder of additions; the longest
    /// prefix that the class's reference army of the curve's size still beats half the time — as strong as the
    /// curve says, whatever the player brings.
    fn enemy(&mut self, kind: Kind, danger: u8) -> (Vec<Template>, String) {
        let b = Self::budget(self.class, self.next_fight(), kind, danger);
        self.enemy_of(kind, b)
    }

    /// A class's own reference army of `budget` — the curve's measure, the army a run's enemy is held against: the
    /// Foundry's, Forges (the golem in the middle of the class, no modules), a fraction of one as a Forge with that
    /// share of its health; the swarm's, `budget` points of ants, a soldier in every seven bodies.
    pub fn reference(class: Class, budget: f32) -> Vec<Template> {
        match class {
            Class::Foundry => {
                // a Forge — the golem in the middle of the class — and a part of one: its health that share
                let whole = budget.max(0.0).floor() as usize;
                let mut out: Vec<Template> = (0..whole).map(|_| data::unit("gorn")).collect();
                let part = budget - whole as f32;
                if part > 0.05 || out.is_empty() {
                    let mut g = data::unit("gorn");
                    g.hp = ((g.hp as f32 * part.max(0.1)).round() as i32).max(5);
                    out.push(g);
                }
                out
            }
            Class::Swarm => {
                let want = budget.round().max(1.0) as u32;
                let (mut out, mut pts) = (vec![], 0);
                while pts < want {
                    let soldier = out.len() % 7 == 6;
                    let t = data::swarm(if soldier { Caste::Soldier } else { Caste::Worker }, Form::Ant);
                    pts += Self::points(&t);
                    out.push(t);
                }
                out
            }
        }
    }

    /// An enemy of `kind` as strong as `budget` of the class's reference army (the balance tools ask for one of
    /// any strength).
    pub fn enemy_of(&mut self, kind: Kind, budget: f32) -> (Vec<Template>, String) {
        let reference = Self::reference(self.class, budget);
        // a boss: the other class's leader, then its own army a step at a time, then more of its kind — fitted like
        // any enemy (a whole start army can be more than the curve asks for yet)
        let mut ladder: Vec<Vec<Template>> = vec![];
        let (base, key): (Vec<Template>, String) = if kind == Kind::Boss {
            let leaders = self.class.other().leaders();
            let k = leaders[self.roll(4)];
            let mut army = data::army(k);
            let lead = army.iter().position(|t| t.has(Trait::Leader)).or_else(|| (0..army.len()).max_by_key(|&i| army[i].size)).unwrap_or(0);
            let leader = army.remove(lead);
            let mut small: Vec<Template> = vec![];
            for t in army {
                if t.size <= 2 {
                    small.push(t);
                    if small.len() == 3 {
                        ladder.push(std::mem::take(&mut small));
                    }
                } else {
                    ladder.push(vec![t]);
                }
            }
            if !small.is_empty() {
                ladder.push(small);
            }
            (vec![leader], k.to_string())
        } else {
            (vec![], if self.class == Class::Foundry { "swarm".to_string() } else { "golems".to_string() })
        };
        // the ladder's first step is the weakest enemy there can be: if the reference cannot beat it (a Guard against
        // ants that cannot get through its iron), a few other ladders are tried, the first one it can is kept
        let lead_steps = ladder.len();
        let mut tail = self.ladder(kind, LADDER);
        for _ in 0..4 {
            if lead_steps > 0 || !base.is_empty() {
                break;
            }
            if self.holds(&reference, &tail[0], FIT_TRIES) {
                break;
            }
            tail = self.ladder(kind, LADDER);
        }
        ladder.extend(tail);
        // no more than the deployment zone holds — those that find no room would not fight, and the fitting would
        // count them
        let mut used: i32 = base.iter().map(room_cost).sum();
        let mut keep = 0;
        for step in &ladder {
            let c: i32 = step.iter().map(room_cost).sum();
            if used + c > ROOM {
                break;
            }
            used += c;
            keep += 1;
        }
        ladder.truncate(keep.max(1));
        let with = |n: usize| -> Vec<Template> {
            let mut a = base.clone();
            for step in &ladder[..n] {
                a.extend(step.iter().cloned());
            }
            a
        };
        // the smallest army is one step (a boss: its leader alone); the longest prefix the reference still beats
        // half the time — first by doubling (a small one is never measured against hundreds), then by halving
        let (mut lo, mut hi) = (if base.is_empty() { 1 } else { 0 }, ladder.len());
        let mut step = 1;
        while lo < hi {
            let n = (lo + step).min(hi);
            if self.holds(&reference, &with(n), FIT_TRIES) {
                lo = n;
                step *= 2;
            } else {
                hi = n - 1;
                break;
            }
        }
        while lo < hi {
            let mid = (lo + hi).div_ceil(2);
            if self.holds(&reference, &with(mid), FIT_TRIES) {
                lo = mid;
            } else {
                hi = mid - 1;
            }
        }
        (with(lo), key)
    }

    /// Additions to an enemy army, one step each, mostly small: for the swarm a flock of a form (workers, now and
    /// then a soldier), for the Foundry a golem of the pool with a module of its kind.
    fn ladder(&mut self, kind: Kind, n: usize) -> Vec<Vec<Template>> {
        let mut out = vec![];
        let elite = kind != Kind::Fight;
        match self.class.other() {
            Class::Swarm => {
                let forms = data::FORMS;
                let main = forms[self.roll(forms.len())];
                for k in 0..n {
                    let soldier = (elite && k % 3 == 2) || k % 5 == 4;
                    let form = if k % 2 == 0 { Form::Ant } else if self.roll(3) == 0 { forms[self.roll(forms.len())] } else { main };
                    let c = if soldier { Caste::Soldier } else { Caste::Worker };
                    let count = if soldier { 1 } else { 3 };
                    out.push((0..count).map(|_| data::swarm(c, form)).collect());
                }
            }
            Class::Foundry => {
                for k in 0..n {
                    let g = self.golem(elite || k > 3);
                    out.push(vec![g]);
                }
            }
        }
        out
    }

    /// A golem of the pool, maybe a module of its kind on it.
    fn golem(&mut self, module: bool) -> Template {
        let pool: [(&str, &[&str]); 5] = [
            ("strazh", &[]),
            ("mudrets", &["peregruzka", "grozovaya_katushka", "ognenny_shar"]),
            ("gorn", &[]),
            ("orudie", &["mortira", "golova_katapulta"]),
            ("mekhanik", &["remont"]),
        ];
        let (key, mods) = pool[self.roll(pool.len())];
        let mut t = data::unit(key);
        if !mods.is_empty() && (module || self.roll(2) == 0) {
            t = t.with(data::module(mods[self.roll(mods.len())]));
        }
        if key == "strazh" && module {
            t = t.with(Ability::Intercept);
        }
        t
    }

    /// A golem of the pool the leadership still holds (a few draws), if there is room for one at all.
    fn golem_fitting(&mut self, module: bool) -> Option<Template> {
        let free = self.lead_cap().saturating_sub(self.lead_used());
        (0..12).map(|_| self.golem(module)).find(|g| Self::lead_cost(g) <= free)
    }

    /// The roads of the next fork. Before a boss: the camp or the trader, then the boss alone. Otherwise two battles
    /// (an elite among them from the third battle on) and, if no stop was taken since the last battle, a stop.
    pub fn fork(&mut self) {
        self.path.clear();
        if self.over.is_some() {
            return;
        }
        let fight = self.next_fight();
        if self.boss_next() {
            if !self.stopped && fight > 1 {
                let (a, b) = (self.stop(Kind::Camp), self.stop(Kind::Merchant));
                self.path.push(a);
                self.path.push(b);
            } else {
                let (enemy, key) = self.enemy(Kind::Boss, 3);
                self.path.push(Node { kind: Kind::Boss, enemy, enemy_key: key, reward: 25 + fight as i32, event: 0, danger: 3 });
            }
            return;
        }
        // two battles: the usual one and a harder one — an elite (an artifact) from the third battle on, else a
        // dangerous road (more currency, a rarer find)
        let elite = fight >= 3 && self.roll(2) == 0;
        for k in 0..2 {
            let kind = if k == 1 && elite { Kind::Elite } else { Kind::Fight };
            let danger = if k == 1 { 2 } else { 1 };
            let (enemy, key) = self.enemy(kind, danger);
            let reward = match (kind, danger) {
                (Kind::Elite, _) => 14,
                (_, 2) => 11,
                _ => 7,
            } + fight as i32 / 2;
            self.path.push(Node { kind, enemy, enemy_key: key, reward, event: 0, danger });
        }
        if !self.stopped && fight > 1 {
            let kind = [Kind::Merchant, Kind::Event, Kind::Event, Kind::Camp][self.roll(4)];
            let stop = self.stop(kind);
            self.path.push(stop);
        }
    }

    fn stop(&mut self, kind: Kind) -> Node {
        let mut event = 0;
        if kind == Kind::Event {
            let fit: Vec<usize> = (0..EVENTS.len()).filter(|&i| EVENTS[i].1.is_none_or(|c| c == self.class)).collect();
            event = fit[self.roll(fit.len())];
        }
        Node { kind, enemy: vec![], enemy_key: String::new(), reward: 0, event, danger: 0 }
    }

    /// A stop taken: the next fork has battles only.
    pub fn left_stop(&mut self) {
        self.stopped = true;
        self.fork();
    }

    pub fn battle_seed(&mut self) -> u64 {
        self.rng.next_u64()
    }

    /// After a battle of `node`: the losses stay, the spoils are given out (to take one by one).
    pub fn after_battle(&mut self, node: &Node, res: &BattleResult) -> Vec<Reward> {
        let (_, idx) = self.fighters();
        let mut gone = vec![];
        let mut fell: Vec<Template> = vec![];
        for &d in &res.dead {
            let Some(&m) = idx.get(d) else { continue };
            if self.is_leader(&self.army[m]) {
                continue; // a leader always comes back
            }
            match self.class {
                Class::Foundry => self.army[m].broken = true,
                Class::Swarm => {
                    fell.push(self.army[m].t.clone());
                    gone.push(m);
                }
            }
            self.stats.lost += 1;
        }
        gone.sort_unstable();
        for m in gone.into_iter().rev() {
            self.army.remove(m);
        }
        self.stats.kills += res.kills;
        self.stopped = false;
        self.learn(res);
        if !res.won {
            self.over = Some(false);
            self.path.clear();
            return vec![];
        }
        self.fight += 1;
        self.stats.won += 1;
        let mut rewards = vec![Reward::Money(node.reward)];
        match self.class {
            Class::Foundry if self.broken() > 0 => rewards.push(Reward::Repair(2 * self.broken() as i32)),
            Class::Swarm => {
                // everything hatches (CONCEPT.md, «Выводок»): the fallen again, of their own kind, and clutches of
                // workers past the limit — the swarm overflows it and eats the extra (a body is nothing, the limit and
                // the breed are everything)
                let mut brood: Vec<Template> = fell.clone();
                let mut pts: u32 = self.points_used() + brood.iter().map(Self::points).sum::<u32>();
                let want = self.limit() + data::rules().clutch as u32;
                while pts < want {
                    brood.push(data::swarm(Caste::Worker, Form::Ant));
                    pts += 1;
                }
                rewards.push(Reward::Brood(brood));
            }
            _ => {}
        }
        if node.kind == Kind::Boss && self.fight < FIGHTS {
            let g = self.growth_offer();
            if !g.is_empty() {
                rewards.push(Reward::Growth(g));
            }
        }
        let find = self.find(3, node.kind == Kind::Boss || node.danger >= 2);
        rewards.push(Reward::Find(find));
        if node.kind != Kind::Fight {
            rewards.push(Reward::Artifact(self.new_artifact()));
        }
        if self.fight >= FIGHTS {
            self.over = Some(true);
        }
        rewards
    }

    /// What the leader takes from a battle for the rest of the run: the Hive Mind remembers the kind of enemy that
    /// killed the most of the swarm (Память роя), the Devourer keeps count of what it ate (Ты — то, что ты ешь).
    fn learn(&mut self, res: &BattleResult) {
        let lead = self.army.iter().find(|m| self.is_leader(m)).map(|m| m.t.clone());
        let Some(lead) = lead else { return };
        if lead.has(Trait::HiveMind) {
            if let Some(&(k, _)) = res.foe_kills.iter().filter(|(k, _)| !self.memory.contains(k)).max_by_key(|(k, n)| (*n, std::cmp::Reverse(*k))) {
                self.memory.push(k);
                if self.memory.len() > MEMORY {
                    self.memory.remove(0);
                }
            }
        }
        if lead.has(Trait::Grows) {
            self.diet.resize(crate::model::KNOWN.len(), 0);
            for &k in &res.eaten {
                self.diet[k as usize] += 1;
            }
        }
    }

    /// Spoils taken: currency, an artifact (a find is taken with `recruit`).
    /// Whether it can be taken now (a repair needs the metal).
    pub fn can_take(&self, r: &Reward) -> bool {
        match r {
            Reward::Repair(p) => self.money >= *p,
            _ => true,
        }
    }

    pub fn take(&mut self, r: &Reward) {
        match r {
            Reward::Money(n) => self.earn(*n),
            Reward::Repair(p) => {
                if self.money >= *p {
                    self.money -= p;
                    self.army.iter_mut().for_each(|m| m.broken = false);
                }
            }
            Reward::Brood(ts) => {
                for t in ts {
                    self.add(t.clone());
                }
                self.trim();
            }
            Reward::Artifact(a) => self.artifacts.push(*a),
            Reward::Find(_) | Reward::Growth(_) => {}
        }
    }

    fn earn(&mut self, n: i32) {
        self.money = (self.money + n).max(0);
        if n > 0 {
            self.stats.earned += n;
        }
    }

    /// The find passed over: a little currency instead (the Foundry melts it down, the swarm eats it).
    pub fn pass_find(&mut self) -> i32 {
        self.earn(3);
        3
    }

    pub fn recruit(&mut self, o: &Offer) {
        for t in &o.units {
            self.add(t.clone());
        }
        self.trim();
    }

    fn new_artifact(&mut self) -> Artifact {
        let free: Vec<Artifact> = Artifact::ALL.iter().copied().filter(|a| !self.artifacts.contains(a)).collect();
        if free.is_empty() {
            return Artifact::ALL[self.roll(Artifact::ALL.len())];
        }
        free[self.roll(free.len())]
    }

    /// `n` finds of the player's class, different from each other: a module or a mutation (as long as the army has
    /// somewhere to put it) for every two of three, bodies for the rest.
    pub fn find(&mut self, n: usize, rare: bool) -> Vec<Offer> {
        let mut out: Vec<Offer> = vec![];
        let mut guard = 0;
        while out.len() < n && guard < 60 {
            guard += 1;
            // bodies only if the Foundry's leadership has room for the cheapest golem; the swarm finds a mutation
            // seldom — one, after an elite or a boss — and bodies of its forms otherwise
            let room = self.class == Class::Swarm || self.lead_cap() >= self.lead_used() + 3;
            let want_part = match self.class {
                Class::Foundry => out.len() % 3 != 2 || !room,
                Class::Swarm => rare && out.is_empty(),
            };
            // a part, if there is a new one to offer; else bodies
            let part = if want_part { self.part().filter(|p| out.iter().all(|x| x.key != p.key)) } else { None };
            let o = part.unwrap_or_else(|| self.offer(rare));
            if out.iter().all(|x| x.key != o.key) {
                out.push(o);
            }
        }
        out
    }

    /// A module (the Foundry) or a mutation (the swarm) the army can take now, if there is one.
    fn part(&mut self) -> Option<Offer> {
        let finds = data::finds();
        match self.class {
            Class::Foundry => {
                let fit: Vec<&str> =
                    finds.modules.iter().filter(|f| (0..self.army.len()).any(|i| self.fits(i, &f.key) || self.raises(i, &f.key))).map(|f| f.key.as_str()).collect();
                if fit.is_empty() {
                    return None;
                }
                let k = fit[self.roll(fit.len())].to_string();
                Some(Offer { key: k.clone(), units: vec![], price: 10 + self.roll(5) as i32, find: Find::Module(k) })
            }
            Class::Swarm => {
                let leader = self.leader_key();
                // the common pool and the leader's own; evolutions are bought, not found
                let fit: Vec<&str> = finds
                    .mutations
                    .iter()
                    .filter(|m| m.form.is_none() && m.leader.as_deref().is_none_or(|l| l == leader))
                    .filter(|m| !self.has_mutation(&m.key))
                    .map(|m| m.key.as_str())
                    .collect();
                if fit.is_empty() || self.genome_full() {
                    return None;
                }
                let k = fit[self.roll(fit.len())].to_string();
                Some(Offer { key: k.clone(), units: vec![], price: 9 + self.roll(5) as i32, find: Find::Mutation(k) })
            }
        }
    }

    fn offer(&mut self, rare: bool) -> Offer {
        match self.class {
            Class::Foundry => {
                let module = rare || self.roll(3) == 0;
                let g = match self.golem_fitting(module) {
                    Some(g) => g,
                    None => self.golem(module),
                };
                let key = data::unit_key(&g.name).unwrap_or("golem").to_string();
                let price = 8 + g.size as i32 + g.abilities.len() as i32 * 2;
                Offer { key, units: vec![g], price, find: Find::Units }
            }
            Class::Swarm => {
                let form = data::FORMS[self.roll(data::FORMS.len())];
                let soldier = rare || self.roll(3) == 0;
                let (c, n) = if soldier { (Caste::Soldier, 1 + self.roll(2)) } else { (Caste::Worker, 3 + self.roll(3)) };
                let units: Vec<Template> = (0..n).map(|_| data::swarm(c, form)).collect();
                let key = format!("{form:?}.{}", if soldier { "soldier" } else { "worker" });
                let price = units.len() as i32 * if soldier { 4 } else { 2 };
                Offer { key, units, price, find: Find::Units }
            }
        }
    }

    pub fn shop(&mut self) -> Shop {
        let mut offers: Vec<(Offer, bool)> = vec![];
        for _ in 0..8 {
            if offers.len() >= 4 {
                break;
            }
            // the Foundry's modules in the last two places; the Hive sells one mutation at most
            let wants = match self.class {
                Class::Foundry => offers.len() >= 2,
                Class::Swarm => offers.len() == 2,
            };
            let part = if wants { self.part().filter(|p| offers.iter().all(|(x, _)| x.key != p.key)) } else { None };
            let o = part.unwrap_or_else(|| self.offer(false));
            if offers.iter().all(|(x, _)| x.key != o.key) {
                offers.push((o, false));
            }
        }
        let mut artifacts = vec![];
        for _ in 0..2 {
            let a = self.new_artifact();
            if !artifacts.iter().any(|(x, _, _)| *x == a) {
                let price = 16 + self.roll(8) as i32;
                artifacts.push((a, price, false));
            }
        }
        let service = match self.class {
            Class::Foundry => 2 * self.broken().max(1) as i32,
            Class::Swarm => 6,
        };
        Shop { offers, artifacts, service, service_used: false }
    }

    /// A good bought: bodies join; a module or a mutation goes where `to` says (and is not sold if it can't).
    pub fn buy_offer(&mut self, shop: &mut Shop, i: usize, to: Option<&Target>) -> bool {
        let Some((o, sold)) = shop.offers.get(i).cloned() else { return false };
        if sold || self.money < o.price {
            return false;
        }
        if !self.take_find(&o, to) {
            return false;
        }
        self.money -= o.price;
        shop.offers[i].1 = true;
        true
    }

    pub fn buy_artifact(&mut self, shop: &mut Shop, i: usize) -> bool {
        let Some(&(a, price, sold)) = shop.artifacts.get(i) else { return false };
        if sold || self.money < price {
            return false;
        }
        self.money -= price;
        self.artifacts.push(a);
        shop.artifacts[i].2 = true;
        true
    }

    /// The trader's service: every broken golem mended (Foundry), a clutch of workers (swarm).
    pub fn buy_service(&mut self, shop: &mut Shop) -> bool {
        if shop.service_used || self.money < shop.service {
            return false;
        }
        if self.class == Class::Foundry && self.broken() == 0 {
            return false;
        }
        self.money -= shop.service;
        self.service_effect();
        shop.service_used = true;
        true
    }

    fn service_effect(&mut self) {
        match self.class {
            Class::Foundry => self.army.iter_mut().for_each(|m| m.broken = false),
            Class::Swarm => {
                for _ in 0..4 {
                    self.add(data::swarm(Caste::Worker, Form::Ant));
                }
                self.trim();
            }
        }
    }

    /// The camp's first choice: rest — every broken golem mended (Foundry), a clutch of workers hatched (swarm).
    pub fn camp_rest(&mut self) -> usize {
        match self.class {
            Class::Foundry => {
                let n = self.broken();
                self.army.iter_mut().for_each(|m| m.broken = false);
                n
            }
            Class::Swarm => {
                let n = 4 + self.fight as usize / 3;
                for _ in 0..n {
                    self.add(data::swarm(Caste::Worker, Form::Ant));
                }
                self.trim();
                n
            }
        }
    }

    /// The camp's second choice: temper one golem (+a quarter of its health, +1 to its blow) / breed a form (all of
    /// that name +2 health, +1 to the blow).
    pub fn camp_upgrade(&mut self, member: usize) {
        let name = self.army[member].t.name.clone();
        let one = self.class == Class::Foundry;
        for (i, m) in self.army.iter_mut().enumerate() {
            if (one && i == member) || (!one && m.t.name == name) {
                m.t.hp += if one { (m.t.hp + 3) / 4 } else { 2 };
                m.t.bonus += 1;
            }
        }
    }

    /// An event's option taken; returns how much currency changed (for the game to say).
    pub fn event_choose(&mut self, event: usize, option: usize) -> Option<Artifact> {
        let eff = EVENTS[event].2[option];
        match eff {
            Effect::Money(n) => self.earn(n),
            Effect::BuyArtifact(p) => {
                if self.money >= p {
                    self.money -= p;
                    let a = self.new_artifact();
                    self.artifacts.push(a);
                    return Some(a);
                }
            }
            Effect::TradeUnit => {
                let pick: Vec<usize> = (0..self.army.len()).filter(|&i| !self.is_leader(&self.army[i])).collect();
                if !pick.is_empty() {
                    let i = pick[self.roll(pick.len())];
                    self.army.remove(i);
                    let a = self.new_artifact();
                    self.artifacts.push(a);
                    return Some(a);
                }
            }
            Effect::Hurt(n) => {
                self.earn(n);
                match self.class {
                    Class::Foundry => {
                        let pick: Vec<usize> = (0..self.army.len()).filter(|&i| !self.is_leader(&self.army[i]) && !self.army[i].broken).collect();
                        if !pick.is_empty() {
                            let i = pick[self.roll(pick.len())];
                            self.army[i].broken = true;
                        }
                    }
                    Class::Swarm => {
                        for _ in 0..3 {
                            let pick: Vec<usize> = (0..self.army.len()).filter(|&i| !self.is_leader(&self.army[i])).collect();
                            if pick.len() > 1 {
                                let i = pick[self.roll(pick.len())];
                                self.army.remove(i);
                            }
                        }
                    }
                }
            }
            Effect::Join => match self.class {
                Class::Foundry => match self.golem_fitting(false) {
                    Some(g) => self.add(g),
                    None => self.earn(10),
                },
                Class::Swarm => self.service_effect(),
            },
            Effect::Recruit => match self.class {
                Class::Foundry => match self.golem_fitting(false) {
                    Some(g) => self.add(g),
                    None => self.earn(10),
                },
                Class::Swarm => {
                    let form = data::FORMS[self.roll(data::FORMS.len())];
                    self.add(data::swarm(Caste::Soldier, form));
                    self.trim();
                }
            },
            Effect::Feast => {
                for m in &mut self.army {
                    m.t.hp += 2;
                }
            }
            Effect::Leave => {}
        }
        None
    }

    /// Whether an event's option can be taken now (enough currency, someone to give).
    pub fn event_can(&self, event: usize, option: usize) -> bool {
        match EVENTS[event].2[option] {
            Effect::BuyArtifact(p) => self.money >= p,
            Effect::Money(n) => n >= 0 || self.money >= -n,
            Effect::TradeUnit => self.army.iter().any(|m| !self.is_leader(m)),
            // a golem joins only if the leadership holds the cheapest one
            Effect::Join | Effect::Recruit if self.class == Class::Foundry => self.lead_cap() >= self.lead_used() + 3,
            _ => true,
        }
    }
}

/// Plays a battle of the run out (no log): the result for `after_battle`.
pub fn play(me: &[Template], enemy: &[Template], seed: u64) -> BattleResult {
    let mut bt = Battle::new(seed);
    bt.add_armies(me, enemy);
    let o = bt.run();
    result_of(&bt, o.winner)
}

/// What a finished battle did: who of side 0's army (by its index in the army) was killed, how many of side 1 fell.
pub fn result_of(bt: &Battle, winner: Option<u8>) -> BattleResult {
    let dead = bt.units.iter().filter(|u| u.side == 0 && !u.alive).filter_map(|u| u.src).collect();
    let kills = bt.units.iter().filter(|u| u.side == 1 && !u.alive && u.t.is_army()).count() as u32;
    let mut foe_kills: Vec<(u8, u32)> = vec![];
    for u in bt.units.iter().filter(|u| u.side == 1 && u.kills > 0) {
        if let Some(k) = u.kind {
            match foe_kills.iter_mut().find(|e| e.0 == k) {
                Some(e) => e.1 += u.kills,
                None => foe_kills.push((k, u.kills)),
            }
        }
    }
    let eaten = bt.eaten[0].iter().filter_map(|&t| bt.units[t].kind).collect();
    BattleResult { won: winner == Some(0), dead, kills, foe_kills, eaten }
}

/// How many of a kind the Devourer eats in a run before it is in him (Ты — то, что ты ешь).
pub const DIET_STEP: u32 = 5;
/// Пандемия: one more of the enemy infected as the battle begins for every this many battles won.
pub const PANDEMIC_EVERY: u32 = 3;
/// Память роя: how many kinds the swarm remembers at once (a new one pushes the oldest out).
pub const MEMORY: usize = 3;

/// What a kind eaten enough of gives the Devourer (`model::KNOWN` index): a Guard's or a Mason's iron — armor; a
/// Sage's coils — its bite shocks; a Forge's coals — it sets those beside it alight; a Gun's steel — teeth +2; a
/// Mechanic's oil — health; a leader — health and a harder bite.
pub fn diet_gift(k: usize, t: &mut Template) {
    match crate::model::KNOWN.get(k).copied() {
        Some("strazh" | "kamenshchik") => t.armor += 1,
        Some("mudrets") => t.dmg = crate::model::Dmg::Shock,
        Some("gorn") => {
            if !t.has(Trait::ZharGorna) {
                t.traits.push(Trait::ZharGorna);
            }
        }
        Some("orudie") => t.bonus += 2,
        Some("mekhanik") => t.hp += 15,
        Some(_) => {
            t.hp += 20;
            t.bonus += 1;
        }
        None => {}
    }
}
