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
    /// The swarm's breeds and their mutations: (form, mutation key); every body of the form has them.
    #[serde(default)]
    pub breeds: Vec<(String, String)>,
    /// How the leader has grown after the bosses (keys of growth.ron).
    #[serde(default)]
    pub growth: Vec<String>,
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
        let form = form_of(&m.t).to_string();
        for (f, key) in &self.breeds {
            if *f == form {
                if let Some(mu) = finds.mutations.iter().find(|x| &x.key == key) {
                    mu.give.apply(&mut t);
                }
            }
        }
        for a in &self.artifacts {
            a.apply(&mut t);
        }
        t
    }

    /// How many modules a golem takes (its cells): the Father of the Colossus four, a big frame three, the rest two.
    pub fn cells(&self, m: &Member) -> usize {
        let more: usize = self.growth.iter().filter_map(|k| data::growth_by_key(k)).map(|g| g.cells).sum();
        more + match data::unit_key(&m.t.name) {
            Some("otets_kolossa") => 4,
            _ if m.t.size >= 5 => 3,
            _ => 2,
        }
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

    /// Where a find can go: the golems a module fits, the breeds without this mutation; none for bodies (they join).
    /// Whether a module can be raised a level on a member: it is on it, below III (taking it again is the upgrade).
    pub fn raises(&self, i: usize, key: &str) -> bool {
        let m = &self.army[i];
        m.mods.iter().position(|x| x == key).is_some_and(|j| m.level(j) < MAX_LEVEL)
    }

    pub fn targets(&self, o: &Offer) -> Vec<Target> {
        match &o.find {
            Find::Units => vec![],
            Find::Module(k) => (0..self.army.len()).filter(|&i| self.fits(i, k) || self.raises(i, k)).map(Target::Member).collect(),
            Find::Mutation(k) => self.forms().into_iter().filter(|f| !self.breeds.iter().any(|(x, y)| x == f && y == k)).map(Target::Form).collect(),
        }
    }

    /// A find taken: bodies join; a module goes into a golem's cell; a mutation onto a breed. False if it can't go
    /// where it was asked.
    pub fn take_find(&mut self, o: &Offer, to: Option<&Target>) -> bool {
        match (&o.find, to) {
            (Find::Units, _) => {
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
            (Find::Mutation(k), Some(Target::Form(f))) if !self.breeds.iter().any(|(x, y)| x == f && y == k) => {
                self.breeds.push((f.clone(), k.clone()));
                true
            }
            _ => false,
        }
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

    /// The share of `tries` battles the player's army wins against `enemy`.
    fn win_rate(&mut self, enemy: &[Template], tries: u32) -> f32 {
        let (me, _) = self.fighters();
        let base = self.rng.next_u64();
        let mut won = 0;
        for k in 0..tries {
            let mut bt = Battle::new(base.wrapping_add(k as u64 * 7919));
            bt.add_armies(&me, enemy);
            if bt.run().winner == Some(0) {
                won += 1;
            }
        }
        won as f32 / tries as f32
    }

    /// The enemy for a battle of `kind`: a base (a leader's army for a boss) and a ladder of additions; the longest
    /// prefix the player still beats `target` of the time.
    fn enemy(&mut self, kind: Kind, danger: u8) -> (Vec<Template>, String) {
        let fight = self.next_fight();
        // one battle lost ends the run: each must be won nearly always, the risk is in what it costs; a dangerous
        // road a little less
        let target = match (kind, danger) {
            (Kind::Boss, _) => 0.75,
            (Kind::Elite, _) => 0.85,
            (_, 2) => 0.9 - 0.004 * fight as f32,
            _ => 0.97 - 0.004 * fight as f32,
        };
        // a boss: the other class's leader, then its own army a step at a time, then more of its kind — fitted like
        // any enemy (a whole start army can be more than a small army can beat)
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
        // the ladder's first step decides the weakest enemy there can be: if the player can't beat it often enough
        // (a Guard against ants that can't get through its iron), a few other ladders are tried and the one whose
        // first step is beaten most often is kept
        let lead_steps = ladder.len();
        let mut best: Option<(f32, Vec<Vec<Template>>)> = None;
        for _ in 0..4 {
            let mut l = ladder.clone();
            l.extend(self.ladder(kind, 28));
            let mut first = base.clone();
            if base.is_empty() || lead_steps == 0 {
                first.extend(l[0].iter().cloned());
            }
            let rate = self.win_rate(&first, 12);
            if best.as_ref().is_none_or(|(r, _)| rate > *r) {
                best = Some((rate, l));
            }
            if rate >= target {
                break;
            }
        }
        let mut ladder = best.map(|b| b.1).unwrap_or_default();
        // no more than the deployment zone holds — those that find no room would not fight, and the fitting would
        // count them
        let room = ROOM;
        let cost = room_cost;
        let mut used: i32 = base.iter().map(cost).sum();
        let mut keep = 0;
        for step in &ladder {
            let c: i32 = step.iter().map(cost).sum();
            if used + c > room {
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
        // the smallest army is one step (a boss: its own army); find the longest prefix still beaten often enough
        let (mut lo, mut hi) = (if base.is_empty() { 1 } else { 0 }, ladder.len());
        while lo < hi {
            let mid = (lo + hi).div_ceil(2);
            if self.win_rate(&with(mid), 24) >= target {
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
                // two of every three that fell hatch again, and at least four workers
                let mut brood: Vec<Template> = fell.iter().enumerate().filter(|(i, _)| i % 3 != 2).map(|(_, t)| t.clone()).collect();
                while brood.len() < 4 {
                    brood.push(data::swarm(Caste::Worker, Form::Ant));
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
            let want_part = out.len() % 3 != 2;
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
                let fit: Vec<&str> = finds.modules.iter().filter(|f| (0..self.army.len()).any(|i| self.fits(i, &f.key))).map(|f| f.key.as_str()).collect();
                if fit.is_empty() {
                    return None;
                }
                let k = fit[self.roll(fit.len())].to_string();
                Some(Offer { key: k.clone(), units: vec![], price: 10 + self.roll(5) as i32, find: Find::Module(k) })
            }
            Class::Swarm => {
                let forms = self.forms();
                let fit: Vec<&str> = finds
                    .mutations
                    .iter()
                    .filter(|m| forms.iter().any(|f| !self.breeds.iter().any(|(x, y)| x == f && *y == m.key)))
                    .map(|m| m.key.as_str())
                    .collect();
                if fit.is_empty() {
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
                let g = self.golem(module);
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
            let part = if offers.len() >= 2 { self.part().filter(|p| offers.iter().all(|(x, _)| x.key != p.key)) } else { None };
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
                Class::Foundry => {
                    let g = self.golem(false);
                    self.add(g);
                }
                Class::Swarm => self.service_effect(),
            },
            Effect::Recruit => match self.class {
                Class::Foundry => {
                    let g = self.golem(false);
                    self.add(g);
                }
                Class::Swarm => {
                    let form = data::FORMS[self.roll(data::FORMS.len())];
                    self.add(data::swarm(Caste::Soldier, form));
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
    let kills = bt.units.iter().filter(|u| u.side == 1 && !u.alive).count() as u32;
    BattleResult { won: winner == Some(0), dead, kills }
}
