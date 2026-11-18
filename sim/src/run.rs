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
}


/// Something to take into the army: a golem, a flock of the swarm. `key` names it for the game (the portrait, the
/// name): a unit's key in units.ron, or «form.caste» of the swarm.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Offer {
    pub key: String,
    pub units: Vec<Template>,
    pub price: i32,
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
    ("deserter", None, [Effect::Join, Effect::Money(6), Effect::Leave]),
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
        self.army.push(Member { id: self.next_id, t, broken: false });
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
        self.next_fight() % BOSS_EVERY == 0
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
            let mut t = m.t.clone();
            for a in &self.artifacts {
                a.apply(&mut t);
            }
            out.push(t);
            idx.push(i);
        }
        (out, idx)
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
    fn enemy(&mut self, kind: Kind) -> (Vec<Template>, String) {
        let fight = self.next_fight();
        // one battle lost ends the run: each must be won nearly always, the risk is in what it costs
        let target = match kind {
            Kind::Boss => 0.75,
            Kind::Elite => 0.85,
            _ => 0.97 - 0.004 * fight as f32,
        };
        let (base, key) = if kind == Kind::Boss {
            let leaders = self.class.other().leaders();
            let k = leaders[self.roll(4)];
            (data::army(k), k.to_string())
        } else {
            (vec![], if self.class == Class::Foundry { "swarm".to_string() } else { "golems".to_string() })
        };
        let mut ladder = self.ladder(kind, 28);
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
            let mid = (lo + hi + 1) / 2;
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
                let (enemy, key) = self.enemy(Kind::Boss);
                self.path.push(Node { kind: Kind::Boss, enemy, enemy_key: key, reward: 25 + fight as i32, event: 0 });
            }
            return;
        }
        let elite = fight >= 3 && self.roll(2) == 0;
        for k in 0..2 {
            let kind = if k == 1 && elite { Kind::Elite } else { Kind::Fight };
            let (enemy, key) = self.enemy(kind);
            let reward = if kind == Kind::Elite { 14 } else { 7 } + fight as i32 / 2;
            self.path.push(Node { kind, enemy, enemy_key: key, reward, event: 0 });
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
        Node { kind, enemy: vec![], enemy_key: String::new(), reward: 0, event }
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
        let find = self.find(3, node.kind == Kind::Boss);
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
            Reward::Find(_) => {}
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

    /// `n` recruits of the player's class, different from each other.
    pub fn find(&mut self, n: usize, rare: bool) -> Vec<Offer> {
        let mut out: Vec<Offer> = vec![];
        let mut guard = 0;
        while out.len() < n && guard < 50 {
            guard += 1;
            let o = self.offer(rare);
            if out.iter().all(|x| x.key != o.key) {
                out.push(o);
            }
        }
        out
    }

    fn offer(&mut self, rare: bool) -> Offer {
        match self.class {
            Class::Foundry => {
                let module = rare || self.roll(3) == 0;
                let g = self.golem(module);
                let key = data::unit_key(&g.name).unwrap_or("golem").to_string();
                let price = 8 + g.size as i32 + g.abilities.len() as i32 * 2;
                Offer { key, units: vec![g], price }
            }
            Class::Swarm => {
                let form = data::FORMS[self.roll(data::FORMS.len())];
                let soldier = rare || self.roll(3) == 0;
                let (c, n) = if soldier { (Caste::Soldier, 1 + self.roll(2)) } else { (Caste::Worker, 3 + self.roll(3)) };
                let units: Vec<Template> = (0..n).map(|_| data::swarm(c, form)).collect();
                let key = format!("{form:?}.{}", if soldier { "soldier" } else { "worker" });
                let price = units.len() as i32 * if soldier { 4 } else { 2 };
                Offer { key, units, price }
            }
        }
    }

    pub fn shop(&mut self) -> Shop {
        let offers = self.find(4, false).into_iter().map(|o| (o, false)).collect();
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

    pub fn buy_offer(&mut self, shop: &mut Shop, i: usize) -> bool {
        let Some((o, sold)) = shop.offers.get(i).cloned() else { return false };
        if sold || self.money < o.price {
            return false;
        }
        self.money -= o.price;
        self.recruit(&o);
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
