//! The battle: rounds and phases as in docs/CONCEPT.md («Ходы», «Удар и числа»).

use crate::model::{Ability, Dmg, Template, Trait};
use crate::rng::Rng;
use std::cmp::Reverse;
use std::collections::VecDeque;

/// The field: wide and tall enough for armies of hundreds (a side's zone holds 450 cells, four small bodies to a
/// cell); the no man's land between the zones is 6 cells, as it always was, so armies meet as soon as before.
pub const W: i32 = 36;
pub const H: i32 = 30;
pub const EXHAUSTION_FROM: u32 = 50;
pub const MAX_ROUNDS: u32 = 150;
/// Deployment zone depth for each side.
pub const ZONE: i32 = 15;
/// The block an army of the usual size stands in: as deep and as tall as the whole zone once was. A bigger army
/// widens it in the same proportions, up to the whole zone.
pub const BLOCK: (i32, i32) = (6, 14);

/// What a mimic swarm has taken up from the machines it saw fall (Мимикрия).
pub const MIMIC_SHOCK: u8 = 1;
pub const MIMIC_FIRE: u8 = 2;
pub const MIMIC_SHELL: u8 = 4;
pub const MIMIC_BLUNT: u8 = 8;
pub const MIMIC_MEND: u8 = 16;
pub const MIMIC_EDGE: u8 = 32;

/// Side length of the square a unit occupies.
pub fn footprint(size: u32) -> i32 {
    match size {
        0..=4 => 1,
        5 => 2,
        6 => 3,
        _ => 4,
    }
}

/// Share of a cell (out of 4): size 1 — up to 4 per cell, size 2 — up to 2, bigger — alone.
fn cell_cost(size: u32) -> u8 {
    match size {
        1 => 1,
        2 => 2,
        _ => 4,
    }
}

pub fn rect_dist(ax: i32, ay: i32, af: i32, bx: i32, by: i32, bf: i32) -> i32 {
    let dx = (bx - (ax + af - 1)).max(ax - (bx + bf - 1)).max(0);
    let dy = (by - (ay + af - 1)).max(ay - (by + bf - 1)).max(0);
    dx.max(dy)
}

fn center_d2(ax: i32, ay: i32, af: i32, bx: i32, by: i32, bf: i32) -> i32 {
    let (acx, acy) = (2 * ax + af - 1, 2 * ay + af - 1);
    let (bcx, bcy) = (2 * bx + bf - 1, 2 * by + bf - 1);
    (acx - bcx).pow(2) + (acy - bcy).pow(2)
}

/// What a unit is for, read from its numbers and traits — where the automatic formation stands it.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Role {
    /// A big leader who fights in melee and keeps up (Пожиратель): first, in the middle of the front.
    LeaderFront,
    /// Any other leader — shoots, lays, is slow or small (Матка, Разум улья, Чума): the middle of the back
    /// rank, taken before the shooters fill it.
    LeaderBack,
    /// Holds the line: a shield, thorns, curling up, heavy armour.
    Front,
    /// Melee that deals the damage: the front, beside the shields.
    Strike,
    /// Flies, leaps or runs fast: the ends of the front.
    Flank,
    /// Does not attack, mends or feeds the others: just behind the front.
    Support,
    /// Shoots or casts: the back ranks.
    Ranged,
}

pub fn role(t: &Template) -> Role {
    if t.has(Trait::Leader) {
        return if t.range <= 1 && t.speed >= 2 && t.size >= 5 && !t.has(Trait::NoAttack) { Role::LeaderFront } else { Role::LeaderBack };
    }
    if t.range > 1 || t.has(Trait::Caster) {
        Role::Ranged
    } else if t.has(Trait::NoAttack) {
        Role::Support
    } else if t.has(Trait::Flyer) || t.has(Trait::Leap) || t.speed >= 4 {
        Role::Flank
    } else if t.has(Trait::Zaslon)
        || t.has(Trait::CurlUp)
        || t.traits.iter().any(|x| matches!(x, Trait::Thorns { .. }))
        || t.armor >= 4
    {
        Role::Front
    } else {
        Role::Strike
    }
}

const DIRS: [(i32, i32); 8] = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)];

#[derive(Clone, Debug)]
pub struct Unit {
    pub id: usize,
    pub side: u8,
    pub t: Template,
    pub x: i32,
    pub y: i32,
    pub hp: i32,
    pub armor: i32,
    pub alive: bool,
    pub on_field: bool,
    pub fleeing: bool,
    pub stunned: bool,
    pub burn: u32,
    pub plates: u32,
    pub intercept_used: bool,
    /// Poison still to come; 10% of it (at least 1) each round.
    pub poison: i32,
    /// Attacks miss up to and including this round (Вспышка светляка).
    pub blind_until: u32,
    /// The round acid last ate at its armor (one point a round at most, however many hit it).
    pub corroded: u32,
    /// Round the unit appeared in: summons do not act in it.
    pub born: u32,
    pub charged: bool,
    pub kills: u32,
    /// Enemies the Devourer has eaten this battle — its own kills and every enemy that fell beside it.
    pub meals: u32,
    /// Its place in the army it was deployed from (None for one summoned in the battle).
    pub src: Option<usize>,
    pub growth: u32,
    pub last_meal: u32,
    /// Side whose larvae hatch from this unit when it dies (Чума).
    pub infected: Option<u8>,
    pub curled: bool,
    /// Silent (no spells, no modules) up to and including this round (Замыкание).
    pub silenced_until: u32,
    /// Hits twice as hard in this round (Перегрузка).
    pub overloaded: u32,
    /// Glued to its cell: cannot walk up to and including this round (Плевок паука).
    pub glued_until: u32,
    /// Has split once already (Почкование): a body buds only the first time it is wounded.
    pub budded: bool,
    /// Half torn out of the enemy's web: the next action frees it.
    pub struggling: bool,
    /// Marked by a puppeteer's blow (Кукловод): falling, it rises for that side.
    pub hooked: Option<u8>,
}

impl Unit {
    pub fn fp(&self) -> i32 {
        footprint(self.t.size)
    }
    pub fn present(&self) -> bool {
        self.alive && self.on_field
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum Event {
    Round(u32),
    Move { u: usize, x: i32, y: i32 },
    Hit { a: usize, t: usize, dmg: i32 },
    Absorbed { t: usize },
    Kill { t: usize },
    Flee { t: usize },
    Left { t: usize },
    Heal { u: usize, t: usize, amount: i32 },
    Knockback { t: usize },
    Burn { t: usize, dmg: i32 },
    Poison { t: usize, dmg: i32 },
    Summon { u: usize },
    Mark { t: usize },
    Blind { t: usize },
    Glue { t: usize },
    /// Stunned: skips its next attack (Сотрясение).
    Stun { t: usize },
    /// A melee blow from behind the target (its back, away from the enemy it faces): half as hard again.
    Rear { t: usize },
    /// A module or a form's gift goes off: who, which, and on whom (an enemy it aims at, an ally it serves, or itself
    /// for what spreads round it). Only for the picture: its hits, heals and states come as their own events.
    Cast { u: usize, kind: Cast, t: usize },
}

/// What goes off in an `Event::Cast`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Cast {
    /// Перегрузка: the ally hits twice as hard this round.
    Overload,
    /// Огненный шар: on the target's cell and round it.
    Fireball,
    /// Сотрясение: the ground round the caster.
    Quake,
    /// Маньяк: a module bolted on an ally.
    Tinker,
    /// Мортира: a shell on the target's cell and round it.
    Volley,
    /// Светляк: a flash round itself.
    Flash,
    /// Паук-плевун: a gob on the target.
    Spit,
    /// Грозовая катушка, Голова-катапульта: one bolt or stone at the target.
    Bolt,
    /// Картечь: a blast at the enemies beside it.
    PointBlank,
    /// The Devourer eats one fallen beside it (`t`: the eaten).
    Devour,
    /// The Devourer at its third stage tramples all small ones beside it with one blow.
    Trample,
}

#[derive(Clone, Debug)]
pub struct Outcome {
    /// `Some(side)` or `None` for a draw (both gone, or the round limit).
    pub winner: Option<u8>,
    pub rounds: u32,
    /// Share of the side's total health left on living units.
    pub hp_left: [f32; 2],
}

struct Grid {
    used: Vec<u8>,
    side: Vec<i8>,
    /// The size of those sharing a cell: small ones and big ones never stand in one cell together.
    size: Vec<u8>,
}

impl Grid {
    fn new() -> Self {
        Grid { used: vec![0; (W * H) as usize], side: vec![-1; (W * H) as usize], size: vec![0; (W * H) as usize] }
    }
    fn idx(x: i32, y: i32) -> usize {
        (y * W + x) as usize
    }
    fn can_place(&self, side: u8, size: u32, x: i32, y: i32) -> bool {
        self.can_place_cap(side, size, x, y, 4)
    }
    /// As can_place, with at most `cap` of a cell taken (two small ones to a cell against area blows).
    fn can_place_cap(&self, side: u8, size: u32, x: i32, y: i32, cap: u8) -> bool {
        let f = footprint(size);
        let c = cell_cost(size);
        if x < 0 || y < 0 || x + f > W || y + f > H {
            return false;
        }
        for yy in y..y + f {
            for xx in x..x + f {
                let i = Grid::idx(xx, yy);
                if self.side[i] != -1 && self.side[i] != side as i8 {
                    return false;
                }
                if self.used[i] + c > cap.max(c) {
                    return false;
                }
                if self.used[i] > 0 && self.size[i] != size as u8 {
                    return false; // a big one does not squeeze in among small ones, nor small ones among big
                }
            }
        }
        true
    }
    fn add(&mut self, side: u8, size: u32, x: i32, y: i32) {
        let f = footprint(size);
        for yy in y..y + f {
            for xx in x..x + f {
                let i = Grid::idx(xx, yy);
                self.used[i] += cell_cost(size);
                self.side[i] = side as i8;
                self.size[i] = size as u8;
            }
        }
    }
    fn sub(&mut self, size: u32, x: i32, y: i32) {
        let f = footprint(size);
        for yy in y..y + f {
            for xx in x..x + f {
                let i = Grid::idx(xx, yy);
                self.used[i] -= cell_cost(size);
                if self.used[i] == 0 {
                    self.side[i] = -1;
                    self.size[i] = 0;
                }
            }
        }
    }
}

#[derive(Default)]
struct Hit {
    attacker: usize,
    target: usize,
    raw: i32,
    dmg: Dmg,
    probivnoy: bool,
    melee: bool,
    knock: bool,
    venom: u32,
    infect: bool,
    ignite: bool,
    /// The blow stuns: the target skips its next attack (not the unstoppable).
    stun: bool,
}

pub struct Battle {
    pub units: Vec<Unit>,
    grid: Grid,
    rng: Rng,
    pub round: u32,
    pub log: Option<Vec<Event>>,
    /// Target marked by each side's Hive Mind.
    mark: [Option<usize>; 2],
    /// The way-finding's own scratch (kept to spare an allocation a step): what each place costs to fight from, the
    /// first step of the way to each place.
    aim: Vec<u8>,
    first: Vec<(i32, i32)>,
    /// Bodies that died live-bearing, per side: every third gives a larva (a whole swarm of them would double itself).
    births: [u32; 2],
    /// Midge bodies fallen, per side: every third becomes a cloud.
    clouds: [u32; 2],
    /// Budding bodies killed by their first wound, per side: every third lets a bud away.
    buds: [u32; 2],
    /// What each side's mimics have taken up from the last machine they broke (Мимикрия): one of `MIMIC_*`.
    mimicry: [u8; 2],
    /// The web on each cell: the side that spun it, -1 none (Паутина).
    web: Vec<i8>,
    /// The honey on each cell: the side whose dead flooded it, -1 none (Медовые соты).
    honey: Vec<i8>,
}

impl Battle {
    pub fn new(seed: u64) -> Self {
        let n = (W * H) as usize;
        Battle {
            units: vec![],
            grid: Grid::new(),
            rng: Rng::new(seed),
            round: 0,
            log: None,
            mark: [None, None],
            aim: vec![],
            first: vec![],
            births: [0, 0],
            clouds: [0, 0],
            buds: [0, 0],
            mimicry: [0, 0],
            web: vec![-1; n],
            honey: vec![-1; n],
        }
    }

    /// The web on the field, cell by cell (`y * W + x`): the side that spun it, -1 none.
    pub fn web(&self) -> &[i8] {
        &self.web
    }

    /// The honey on the field, cell by cell: the side whose dead flooded it, -1 none.
    pub fn honey(&self) -> &[i8] {
        &self.honey
    }

    /// What side `side`'s mimics have taken up (`MIMIC_*` bits).
    pub fn mimicry(&self, side: u8) -> u8 {
        self.mimicry[side as usize % 2]
    }

    /// Whether the Hive Mind of either side has marked this unit.
    pub fn marked(&self, i: usize) -> bool {
        self.mark.contains(&Some(i))
    }

    /// Whether this Devourer starves now: no meal for 3 rounds (hungry at the start of a run: 2) — it loses health
    /// each round until it eats.
    pub fn starving(&self, j: usize) -> bool {
        let u = &self.units[j];
        let hungry = u.t.traits.iter().any(|x| matches!(x, Trait::Hungry { .. }));
        let after = if hungry { 2 } else { 3 };
        u.present() && u.t.has(Trait::Grows) && u.t.has(Trait::Leader) && self.round >= u.last_meal + after
    }

    /// The kind of a mimic's blow: lightning taken up from a sage, a blunt blow from a gun, else its own.
    fn mimic_dmg(&self, i: usize, dmg: Dmg) -> Dmg {
        if !self.units[i].t.has(Trait::Mimic) {
            return dmg;
        }
        let m = self.mimicry[self.units[i].side as usize % 2];
        if m & MIMIC_SHOCK != 0 {
            Dmg::Shock
        } else if m & MIMIC_BLUNT != 0 {
            Dmg::Blunt
        } else {
            dmg
        }
    }

    /// The cells a unit stands on.
    fn cells_of(&self, i: usize) -> impl Iterator<Item = usize> {
        let (x, y, f) = (self.units[i].x, self.units[i].y, self.units[i].fp());
        (y..y + f).flat_map(move |yy| (x..x + f).map(move |xx| Grid::idx(xx, yy)))
    }

    /// Whether a unit stands on something of its enemy's (web or honey) in `layer`.
    fn on_enemy(&self, i: usize, layer: &[i8]) -> bool {
        let side = self.units[i].side as i8;
        self.cells_of(i).any(|c| layer[c] != -1 && layer[c] != side)
    }

    pub fn with_log(mut self) -> Self {
        self.log = Some(vec![]);
        self
    }

    fn ev(&mut self, e: Event) {
        if let Some(l) = &mut self.log {
            l.push(e);
        }
    }

    /// Places one army with nothing to read about the enemy (tests, traces).
    pub fn add_army(&mut self, side: u8, army: &[Template]) {
        self.deploy(side, army, &[]);
    }

    /// Both armies, each reading the other: there is no deployment screen, the game stands the armies itself.
    pub fn add_armies(&mut self, a: &[Template], b: &[Template]) {
        self.deploy(0, a, b);
        self.deploy(1, b, a);
    }

    /// The automatic formation («Авторасстановка» in CONCEPT.md). Every unit gets a role from its numbers and
    /// traits; the roles stand in ranks from the front of the zone, rows filled from the middle outwards,
    /// flankers from the edges inwards; against area blows the small ones stand two to a cell instead of four.
    /// A kind of unit (a flock) is placed in one run, so it stands together.
    pub fn deploy(&mut self, side: u8, army: &[Template], enemy: &[Template]) {
        let area = enemy.iter().any(|t| t.has_ability(|a| matches!(a, Ability::Volley { .. })));
        // the block the army stands in: the cells it needs (a little more — kinds don't share a cell), in a block of
        // the usual proportions, at least the usual size, at most the zone; in the middle of the field's height
        let need: f32 = army
            .iter()
            .map(|t| match t.size {
                1 => if area { 0.5 } else { 0.25 },
                2 => 0.5,
                s => (footprint(s) * footprint(s)) as f32,
            })
            .sum::<f32>()
            * 1.2;
        let grow = (need / (BLOCK.0 * BLOCK.1) as f32).sqrt().max(1.0);
        let depth = ((BLOCK.0 as f32 * grow).ceil() as i32).clamp(BLOCK.0, ZONE);
        let tall = ((BLOCK.1 as f32 * grow).ceil() as i32).clamp(BLOCK.1, H);
        let (top, bottom) = ((H - tall) / 2, (H - tall) / 2 + tall);
        let mut order: Vec<(Role, usize)> = army.iter().enumerate().map(|(i, t)| (role(t), i)).collect();
        // leaders first (theirs are the middles), then the front and the strikers, the flanks, support, shooters; within a role the
        // toughest first; a kind together
        order.sort_by_key(|&(r, i)| (r, Reverse(army[i].armor * 4 + army[i].hp), army[i].name.clone()));
        for (r, i) in order {
            let t = &army[i];
            let f = footprint(t.size);
            let cap = if area && t.size == 1 { 2 } else { 4 };
            // ranks from the front of the block (side 0's front is its right edge); the rest of the zone behind it
            let d = depth.max(f);
            let ranks: Vec<i32> = match r {
                Role::LeaderFront | Role::Front | Role::Strike | Role::Flank => (0..d - f + 1).collect(),
                Role::Support => (1..d - f + 1).chain(0..1).collect(),
                Role::Ranged | Role::LeaderBack => (0..d - f + 1).rev().collect(),
            };
            let ranks: Vec<i32> = ranks.into_iter().chain(d - f + 1..ZONE - f + 1).collect();
            let cols: Vec<i32> = ranks.iter().map(|&k| if side == 0 { ZONE - f - k } else { W - ZONE + k }).collect();
            // rows from the middle outwards, those of the block first, then the rest of the zone's height
            let mid = (H - f) / 2;
            let mut rows = vec![mid];
            for k in 1..H {
                for y in [mid - k, mid + k] {
                    if y >= 0 && y + f <= H {
                        rows.push(y);
                    }
                }
            }
            let in_block = |y: i32| y >= top && y + f <= bottom;
            rows.sort_by_key(|&y| !in_block(y));
            if r == Role::Flank {                       // from the block's edges inwards, top and bottom in turn
                let (a, b) = (top, bottom - f);
                rows.sort_by_key(|&y| (!in_block(y), (y - a).min(b - y), y - a > b - y));
            }
            let mut placed = false;
            'outer: for &x in &cols {
                for &y in &rows {
                    if self.grid.can_place_cap(side, t.size, x, y, cap) {
                        let id = self.place(side, t.clone(), x, y);
                        self.units[id].src = Some(i);
                        placed = true;
                        break 'outer;
                    }
                }
            }
            if !placed {
                'any: for &x in &cols {
                    for &y in &rows {
                        if self.grid.can_place(side, t.size, x, y) {
                            let id = self.place(side, t.clone(), x, y);
                            self.units[id].src = Some(i);
                            placed = true;
                            break 'any;
                        }
                    }
                }
            }
            if !placed {
                eprintln!("no room for {} on side {}", t.name, side);
            }
        }
    }

    pub fn place(&mut self, side: u8, t: Template, x: i32, y: i32) -> usize {
        let id = self.units.len();
        let plates = t
            .abilities
            .iter()
            .find_map(|a| if let Ability::Plates(n) = a { Some(*n) } else { None })
            .unwrap_or(0);
        self.grid.add(side, t.size, x, y);
        self.units.push(Unit {
            id,
            side,
            hp: t.hp,
            armor: t.armor,
            t,
            x,
            y,
            alive: true,
            on_field: true,
            fleeing: false,
            stunned: false,
            burn: 0,
            plates,
            intercept_used: false,
            poison: 0,
            blind_until: 0,
            corroded: u32::MAX,
            born: self.round,
            charged: false,
            kills: 0,
            meals: 0,
            src: None,
            growth: 0,
            last_meal: self.round,
            infected: None,
            curled: false,
            silenced_until: 0,
            overloaded: 0,
            glued_until: 0,
            budded: false,
            struggling: false,
            hooked: None,
        });
        id
    }

    fn allies_adjacent(&self, i: usize) -> usize {
        let side = self.units[i].side;
        (0..self.units.len())
            .filter(|&k| k != i && self.units[k].side == side && self.units[k].present() && self.dist(i, k) <= 1)
            .count()
    }

    /// Morale with «Стая» and the Hive Mind.
    fn morale_of(&self, j: usize) -> u32 {
        let u = &self.units[j];
        let base = u.t.morale_eff();
        if !u.t.has(Trait::Staya) {
            return base;
        }
        let side = u.side;
        let hive = (0..self.units.len()).any(|k| self.units[k].side == side && self.units[k].present() && self.units[k].t.has(Trait::HiveMind));
        base + if hive { 4 } else { self.allies_adjacent(j).min(4) as u32 }
    }

    /// Free spot for a unit of `size` near `(x, y)`, closest first.
    fn free_spot_near(&self, side: u8, size: u32, x: i32, y: i32, radius: i32) -> Option<(i32, i32)> {
        let mut best: Option<(i32, i32, i32)> = None;
        for dy in -radius..=radius {
            for dx in -radius..=radius {
                let (nx, ny) = (x + dx, y + dy);
                if self.grid.can_place(side, size, nx, ny) {
                    let d = dx * dx + dy * dy;
                    if best.is_none_or(|b| d < b.0) {
                        best = Some((d, nx, ny));
                    }
                }
            }
        }
        best.map(|b| (b.1, b.2))
    }

    fn spawn(&mut self, side: u8, t: Template, x: i32, y: i32) -> Option<usize> {
        let (nx, ny) = self.free_spot_near(side, t.size, x, y, 2)?;
        let id = self.place(side, t, nx, ny);
        self.ev(Event::Summon { u: id });
        Some(id)
    }

    pub fn dist(&self, i: usize, j: usize) -> i32 {
        let (a, b) = (&self.units[i], &self.units[j]);
        rect_dist(a.x, a.y, a.fp(), b.x, b.y, b.fp())
    }

    fn enemies_of(&self, i: usize) -> impl Iterator<Item = usize> + '_ {
        let side = self.units[i].side;
        (0..self.units.len()).filter(move |&j| self.units[j].side != side && self.units[j].present())
    }

    fn nearest_enemy(&self, i: usize) -> Option<(usize, i32)> {
        self.enemies_of(i).map(|j| (j, self.dist(i, j))).min_by_key(|&(j, d)| (d, j))
    }

    // ---------------------------------------------------------------- the round
    pub fn run(&mut self) -> Outcome {
        loop {
            if let Some(o) = self.step() {
                return o;
            }
        }
    }

    /// One round; `Some` when the battle is over.
    pub fn step(&mut self) -> Option<Outcome> {
        self.round += 1;
        self.ev(Event::Round(self.round));
        if self.round > MAX_ROUNDS {
            return Some(self.outcome(None));
        }
        self.exhaustion();
        if let Some(o) = self.check_end() {
            return Some(o);
        }
        if self.round == 1 {
            self.battle_begins();
        }
        self.movement();
        self.fear();
        self.attacks();
        if let Some(o) = self.check_end() {
            return Some(o);
        }
        self.persistent();
        self.check_end()
    }

    fn outcome(&self, winner: Option<u8>) -> Outcome {
        let mut left = [0f32; 2];
        let mut total = [0f32; 2];
        for u in self.units.iter().filter(|u| u.t.is_army()) {
            total[u.side as usize] += u.t.hp as f32;
            if u.alive {
                left[u.side as usize] += u.hp.max(0) as f32;
            }
        }
        Outcome {
            winner,
            rounds: self.round,
            hp_left: [left[0] / total[0].max(1.0), left[1] / total[1].max(1.0)],
        }
    }

    fn check_end(&self) -> Option<Outcome> {
        let mut present = [0; 2];
        // a midge cloud, a ghost, a puppet are no army: a side of them alone has lost
        for u in self.units.iter().filter(|u| u.t.is_army()) {
            if u.present() {
                present[u.side as usize] += 1;
            }
        }
        match (present[0], present[1]) {
            (0, 0) => Some(self.outcome(None)),
            (0, _) => Some(self.outcome(Some(1))),
            (_, 0) => Some(self.outcome(Some(0))),
            _ => None,
        }
    }

    /// From round 50: everyone takes growing damage past armor.
    fn exhaustion(&mut self) {
        if self.round < EXHAUSTION_FROM {
            return;
        }
        let d = (self.round - EXHAUSTION_FROM + 1) as i32;
        for i in 0..self.units.len() {
            if self.units[i].present() {
                self.units[i].hp -= d;
                if self.units[i].hp <= 0 {
                    self.kill(i);
                }
            }
        }
    }

    // ---------------------------------------------------------------- movement
    fn movement(&mut self) {
        if self.round == 1 {
            for i in 0..self.units.len() {
                if self.units[i].present() && self.units[i].t.has(Trait::Leap) {
                    self.leap(i);
                }
                if self.units[i].present() && self.units[i].t.has(Trait::Changeling) {
                    let side = self.units[i].side;
                    if let Some(w) = (0..self.units.len()).find(|&k| {
                        self.units[k].side == side && self.units[k].present() && self.units[k].t.size == 1 && !self.units[k].t.has(Trait::Leader)
                    }) {
                        self.leap(w);
                    }
                }
            }
        }
        for step in 1..=3u32 {
            for i in 0..self.units.len() {
                if !self.units[i].present() || self.units[i].t.speed < step || self.units[i].glued_until >= self.round {
                    continue;
                }
                if self.units[i].t.has(Trait::Flyer) && !self.units[i].fleeing {
                    if step == 1 {
                        self.fly(i);
                    }
                    continue;
                }
                self.step_unit(i);
            }
        }
    }

    /// Jump next to the farthest enemy within 6 cells (into the back rows).
    fn leap(&mut self, i: usize) {
        let Some(tj) = self.enemies_of(i).filter(|&j| self.dist(i, j) <= 6).max_by_key(|&j| (self.dist(i, j), Reverse(j))) else { return };
        let (side, size, x, y, f) = {
            let u = &self.units[i];
            (u.side, u.t.size, u.x, u.y, u.fp())
        };
        let (tx, ty, tf) = (self.units[tj].x, self.units[tj].y, self.units[tj].fp());
        self.grid.sub(size, x, y);
        let mut best: Option<(i32, i32, i32)> = None;
        for ny in ty - f..=ty + tf {
            for nx in tx - f..=tx + tf {
                if rect_dist(nx, ny, f, tx, ty, tf) == 1 && self.grid.can_place(side, size, nx, ny) {
                    let d = center_d2(nx, ny, f, tx, ty, tf);
                    if best.is_none_or(|b| d < b.0) {
                        best = Some((d, nx, ny));
                    }
                }
            }
        }
        match best {
            Some((_, nx, ny)) => self.move_to(i, nx, ny),
            None => self.grid.add(side, size, x, y),
        }
    }

    /// Flyers go over everyone: archers and leaders first, otherwise the nearest enemy.
    fn fly(&mut self, i: usize) {
        if self.enemies_of(i).any(|j| self.dist(i, j) <= 1) {
            return;
        }
        let pri = |b: &Battle, j: usize| b.units[j].t.range > 1 || b.units[j].t.has(Trait::Leader);
        let Some(tj) = self.enemies_of(i).min_by_key(|&j| (!pri(self, j), self.dist(i, j), j)) else { return };
        let (side, size, x, y, f, speed) = {
            let u = &self.units[i];
            (u.side, u.t.size, u.x, u.y, u.fp(), u.t.speed as i32)
        };
        let (tx, ty, tf) = (self.units[tj].x, self.units[tj].y, self.units[tj].fp());
        self.grid.sub(size, x, y);
        let mut best = (rect_dist(x, y, f, tx, ty, tf), center_d2(x, y, f, tx, ty, tf), x, y);
        for dy in -speed..=speed {
            for dx in -speed..=speed {
                let (nx, ny) = (x + dx, y + dy);
                if self.grid.can_place(side, size, nx, ny) {
                    let key = (rect_dist(nx, ny, f, tx, ty, tf), center_d2(nx, ny, f, tx, ty, tf));
                    if key < (best.0, best.1) {
                        best = (key.0, key.1, nx, ny);
                    }
                }
            }
        }
        if (best.2, best.3) != (x, y) {
            self.move_to(i, best.2, best.3);
        } else {
            self.grid.add(side, size, x, y);
        }
    }

    fn step_unit(&mut self, i: usize) {
        let (side, size, x, y, f) = {
            let u = &self.units[i];
            (u.side, u.t.size, u.x, u.y, u.fp())
        };
        if self.units[i].fleeing {
            self.grid.sub(size, x, y);
            let dir = if side == 0 { -1 } else { 1 };
            let nx = x + dir;
            if nx < 0 || nx + f > W {
                self.units[i].on_field = false;
                self.ev(Event::Left { t: i });
                return;
            }
            for (cx, cy) in [(nx, y), (nx, y - 1), (nx, y + 1), (x, y - 1), (x, y + 1)] {
                if self.grid.can_place(side, size, cx, cy) {
                    self.move_to(i, cx, cy);
                    return;
                }
            }
            self.grid.add(side, size, x, y);
            return;
        }
        let Some((tj, d)) = self.nearest_enemy(i) else { return };
        let reach = self.units[i].t.range.max(1) as i32;
        if d <= reach {
            return;
        }
        // a leader who stands at the back is no tank: he stays behind his army while it stands, steps out only to
        // meet an enemy that has come within two cells, or when no one of his is left
        if role(&self.units[i].t) == Role::LeaderBack && d > reach + 1 {
            let guarded = (0..self.units.len()).any(|k| {
                k != i && self.units[k].side == side && self.units[k].present() && !self.units[k].t.has(Trait::Leader)
            });
            if guarded {
                return;
            }
        }
        let (tx, ty, tf) = {
            let t = &self.units[tj];
            (t.x, t.y, t.fp())
        };
        self.grid.sub(size, x, y);
        // a flanker (fast, on the wings) goes round the line for the archers and the leader behind it
        if role(&self.units[i].t) == Role::Flank && d > reach {
            let back: Vec<usize> = self.enemies_of(i).filter(|&j| self.units[j].t.range > 1 || self.units[j].t.has(Trait::Leader)).collect();
            if let Some((nx, ny)) = self.way_round(i, x, y, &back, reach, 16) {
                self.move_to(i, nx, ny);
                return;
            }
        }
        // close to the fight, a melee fighter picks where to strike from: round the enemy's flank or to its back when
        // that is not much longer than straight into its front
        if reach == 1 && d <= 4 && !self.units[i].fleeing {
            let all: Vec<usize> = self.enemies_of(i).filter(|&j| self.dist(i, j) <= 8).collect();
            if let Some((nx, ny)) = self.way_round(i, x, y, &all, reach, 8) {
                self.move_to(i, nx, ny);
                return;
            }
        }
        let mut best = (d, center_d2(x, y, f, tx, ty, tf), x, y);
        for (dx, dy) in DIRS {
            let (nx, ny) = (x + dx, y + dy);
            if !self.grid.can_place(side, size, nx, ny) {
                continue;
            }
            let key = (rect_dist(nx, ny, f, tx, ty, tf), center_d2(nx, ny, f, tx, ty, tf));
            if key < (best.0, best.1) {
                best = (key.0, key.1, nx, ny);
            }
        }
        // the way ahead shut (its own in front, the enemy's line too thick): round them to the flank — the
        // shortest way to a free place next to any enemy
        if best.0 >= d {
            let all: Vec<usize> = self.enemies_of(i).collect();
            if let Some((nx, ny)) = self.way_round(i, x, y, &all, reach, 12) {
                self.move_to(i, nx, ny);
                return;
            }
        }
        if (best.2, best.3) != (x, y) {
            self.move_to(i, best.2, best.3);
        } else {
            self.grid.add(side, size, x, y);
        }
    }

    /// Where to go to fight: the first step of the best way (eight directions, round everyone in the way) to a place
    /// within `reach` of one of `goals`, no longer than `limit` steps; a place at an enemy's back counts as the
    /// nearest, at its side one step farther, at its front three (so a unit goes round when that is up to two or three
    /// steps longer — it flanks). None if no place can be reached. The unit is off the grid.
    fn way_round(&mut self, i: usize, x: i32, y: i32, goals: &[usize], reach: i32, limit: i32) -> Option<(i32, i32)> {
        if goals.is_empty() {
            return None;
        }
        let (side, size, f) = (self.units[i].side, self.units[i].t.size, self.units[i].fp());
        let n = (W * H) as usize;
        let mut aim = std::mem::take(&mut self.aim);
        let mut first = std::mem::take(&mut self.first);
        aim.clear();
        aim.resize(n, u8::MAX);
        first.clear();
        first.resize(n, (-1, -1));
        // what a place next to an enemy costs, by where it is on the enemy: its back 0, its side 1, its front 3
        for &j in goals {
            let t = &self.units[j];
            let (tf, tx, ty) = (t.fp(), t.x, t.y);
            for ny in (ty - f - reach + 1).max(0)..=(ty + tf + reach - 1).min(H - f) {
                for nx in (tx - f - reach + 1).max(0)..=(tx + tf + reach - 1).min(W - f) {
                    if rect_dist(nx, ny, f, tx, ty, tf) <= reach {
                        let c = nx as f32 + f as f32 / 2.0;
                        let (back, front) = if t.side == 0 { (c <= tx as f32, c >= (tx + tf) as f32) } else { (c >= (tx + tf) as f32, c <= tx as f32) };
                        let cost = if back { 0 } else if front { 3 } else { 1 };
                        let k = Grid::idx(nx, ny);
                        aim[k] = aim[k].min(cost);
                    }
                }
            }
        }
        let mut best: Option<(i32, (i32, i32))> = None;
        first[Grid::idx(x, y)] = (x, y);
        let mut queue = VecDeque::from([(x, y, 0)]);
        while let Some((cx, cy, depth)) = queue.pop_front() {
            // nothing farther can beat what is found
            if depth >= limit || best.is_some_and(|b| depth + 1 >= b.0) {
                break;
            }
            for (dx, dy) in DIRS {
                let (nx, ny) = (cx + dx, cy + dy);
                if nx < 0 || ny < 0 || nx + f > W || ny + f > H || first[Grid::idx(nx, ny)].0 >= 0 {
                    continue;
                }
                if !self.grid.can_place(side, size, nx, ny) {
                    first[Grid::idx(nx, ny)] = (-2, -2);
                    continue;
                }
                let step = if depth == 0 { (nx, ny) } else { first[Grid::idx(cx, cy)] };
                first[Grid::idx(nx, ny)] = step;
                let c = aim[Grid::idx(nx, ny)];
                if c != u8::MAX {
                    let total = depth + 1 + c as i32;
                    if best.is_none_or(|b| total < b.0) {
                        best = Some((total, step));
                    }
                    continue; // a place to fight from: no need to go through it
                }
                queue.push_back((nx, ny, depth + 1));
            }
        }
        self.aim = aim;
        self.first = first;
        best.map(|b| b.1)
    }

    /// Whether `i` stands behind `j`: beyond the back of `j`, away from the enemy its side faces (the near side
    /// faces right).
    fn behind(&self, i: usize, j: usize) -> bool {
        let (a, t) = (&self.units[i], &self.units[j]);
        let ac = a.x as f32 + a.fp() as f32 / 2.0;
        if t.side == 0 {
            ac <= t.x as f32
        } else {
            ac >= (t.x + t.fp()) as f32
        }
    }

    /// Expects the unit already lifted off the grid.
    fn move_to(&mut self, i: usize, x: i32, y: i32) {
        let (side, size) = (self.units[i].side, self.units[i].t.size);
        self.units[i].x = x;
        self.units[i].y = y;
        self.grid.add(side, size, x, y);
        self.ev(Event::Move { u: i, x, y });
        // walked into the enemy's web: stuck, no farther this round (and it tears free instead of its next blow)
        if self.on_enemy(i, &self.web) {
            self.units[i].glued_until = self.units[i].glued_until.max(self.round);
        }
    }

    // ---------------------------------------------------------------- fear
    fn fear(&mut self) {
        let sources: Vec<(usize, u32, u32)> = (0..self.units.len())
            .filter(|&i| self.units[i].present() && !self.units[i].fleeing)
            .filter_map(|i| self.units[i].t.fear().map(|(die, r)| (i, die, r)))
            .collect();
        for (i, die, radius) in sources {
            let victims: Vec<usize> = self.enemies_of(i).filter(|&j| self.dist(i, j) <= radius as i32).collect();
            for j in victims {
                self.fear_check(j, die);
            }
        }
    }

    fn fear_check(&mut self, j: usize, die: u32) {
        let u = &self.units[j];
        if !u.present() || u.fleeing {
            return;
        }
        let morale = self.morale_of(j);
        if self.rng.die(die) > morale {
            self.units[j].fleeing = true;
            self.ev(Event::Flee { t: j });
        }
    }

    /// What happens as the battle begins, the armies stood: the Inventor's augments.
    fn battle_begins(&mut self) {
        // the Hive Mind's mirage: every second body of the swarm gets a ghost twin beside it
        let mirage: Vec<usize> = (0..self.units.len()).filter(|&i| self.units[i].present() && self.units[i].t.has(Trait::Mirage)).collect();
        for (n, i) in mirage.into_iter().enumerate() {
            if n % 2 != 0 {
                continue;
            }
            let mut ghost = self.units[i].t.clone();
            ghost.traits.retain(|t| matches!(t, Trait::Flyer | Trait::Leap));
            ghost.traits.extend([Trait::Ghost, Trait::NoAttack, Trait::Mindless]);
            ghost.abilities.clear();
            ghost.hp = 1;
            let (side, x, y) = (self.units[i].side, self.units[i].x, self.units[i].y);
            self.spawn(side, ghost, x, y);
        }
        for i in 0..self.units.len() {
            if !self.units[i].present() || !self.units[i].t.abilities.contains(&Ability::Augment) {
                continue;
            }
            let side = self.units[i].side;
            let allies: Vec<usize> =
                (0..self.units.len()).filter(|&k| k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.golem && self.dist(i, k) <= 2).collect();
            for k in allies {
                let up: Vec<Ability> = self.units[k].t.abilities.iter().map(|a| a.level_up()).collect();
                self.units[k].t.abilities = up;
            }
        }
    }

    // ---------------------------------------------------------------- attacks
    fn attacks(&mut self) {
        for u in &mut self.units {
            u.intercept_used = false;
        }
        let mut order: Vec<usize> = (0..self.units.len()).filter(|&i| self.units[i].present() && !self.units[i].fleeing).collect();
        order.sort_by_key(|&i| (Reverse(self.units[i].t.init), i));
        let mut k = 0;
        while k < order.len() {
            let init = self.units[order[k]].t.init;
            let group: Vec<usize> = order[k..].iter().copied().take_while(|&i| self.units[i].t.init == init).collect();
            let mut hits = vec![];
            for &i in &group {
                let u = &self.units[i];
                if !u.present() || u.fleeing {
                    continue;
                }
                if u.stunned {
                    self.units[i].stunned = false;
                    continue;
                }
                if (u.born == self.round && self.round > 0) || u.blind_until >= self.round || u.curled {
                    continue;
                }
                if self.resonates(i) {
                    continue; // the swarm's chirr shakes it: no blow this round
                }
                if self.on_enemy(i, &self.web) {
                    // stuck in the enemy's web: two actions go on tearing free
                    if !self.units[i].struggling {
                        self.units[i].struggling = true;
                        continue;
                    }
                    self.units[i].struggling = false;
                    let side = self.units[i].side as i8;
                    let cells: Vec<usize> = self.cells_of(i).collect();
                    for c in cells {
                        if self.web[c] != side {
                            self.web[c] = -1;
                        }
                    }
                    continue;
                }
                self.act(i, &mut hits);
            }
            for h in hits {
                self.apply(h);
            }
            k += group.len();
        }
    }

    /// An adjacent ally with Питание: fire and lightning modules recharge a round sooner.
    fn powered(&self, i: usize) -> bool {
        let side = self.units[i].side;
        (0..self.units.len()).any(|k| {
            k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.has(Trait::Pitanie) && self.dist(i, k) <= 1
        })
    }

    fn act(&mut self, i: usize, hits: &mut Vec<Hit>) {
        let round = self.round;
        if self.units[i].silenced_until >= round {
            return; // Замыкание: the windings are shorted
        }
        // a spinner spins every fourth round: to catch an enemy beside it not in the web yet, or when it has nothing to
        // strike at anyway (a shooter with a target in range shoots, one beside webbed enemies strikes them)
        if self.units[i].t.has(Trait::Spinner) && round % 4 == 1 {
            let adj = self.adjacent_enemies(i);
            let fresh = adj.iter().any(|&j| !self.on_enemy(j, &self.web));
            let idle = adj.is_empty() && (self.units[i].t.range <= 1 || self.ranged_target(i, self.units[i].t.range).is_none());
            if fresh || idle {
                self.spin(i);
                return;
            }
        }
        let powered = self.powered(i);
        let every_of = |every: u32, dmg: Dmg| if powered && matches!(dmg, Dmg::Fire | Dmg::Shock) { (every - 1).max(1) } else { every };
        let abilities = self.units[i].t.abilities.clone();
        for ab in abilities {
            match ab {
                Ability::Overload { every } if round.is_multiple_of(every) => {
                    let side = self.units[i].side;
                    let ally = (0..self.units.len())
                        .filter(|&k| k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.golem)
                        .filter(|&k| !self.units[k].t.has(Trait::NoAttack) && self.dist(i, k) <= 1)
                        .max_by_key(|&k| (self.units[k].t.die as i32 + 2 * self.units[k].t.bonus, Reverse(k)));
                    if let Some(k) = ally {
                        self.units[k].overloaded = round;
                        self.ev(Event::Cast { u: i, kind: Cast::Overload, t: k });
                        return;
                    }
                }
                Ability::Fireball { every, die, bonus, range } if round.is_multiple_of(every_of(every, Dmg::Fire)) => {
                    if let Some(tj) = self.ranged_target(i, range) {
                        self.ev(Event::Cast { u: i, kind: Cast::Fireball, t: tj });
                        let victims: Vec<usize> = self.enemies_of(i).filter(|&v| self.dist(v, tj) <= 1).collect();
                        for v in victims {
                            let raw = self.rng.damage(die, bonus);
                            hits.push(Hit { attacker: i, target: v, raw, dmg: Dmg::Fire, ignite: true, ..Default::default() });
                        }
                        return;
                    }
                }
                Ability::Repair { every, amount } if round.is_multiple_of(every) => {
                    if self.repair(i, amount) {
                        return;
                    }
                }
                Ability::Quake { every, die, bonus, radius } if round.is_multiple_of(every) => {
                    // the ground shakes: those in the air feel nothing
                    let victims: Vec<usize> = self.enemies_of(i).filter(|&v| self.dist(i, v) <= radius as i32 && !self.units[v].t.has(Trait::Flyer)).collect();
                    if !victims.is_empty() {
                        self.ev(Event::Cast { u: i, kind: Cast::Quake, t: i });
                        for v in victims {
                            let raw = self.rng.damage(die, bonus);
                            let stun = self.units[v].t.size <= 2;
                            hits.push(Hit { attacker: i, target: v, raw, dmg: Dmg::Blunt, melee: true, stun, ..Default::default() });
                        }
                        return;
                    }
                }
                Ability::Tinker { every } if round.is_multiple_of(every) => {
                    let side = self.units[i].side;
                    let near: Vec<usize> =
                        (0..self.units.len()).filter(|&k| k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.golem && self.dist(i, k) <= 2).collect();
                    if !near.is_empty() {
                        let k = near[self.rng.die(near.len() as u32) as usize - 1];
                        self.ev(Event::Cast { u: i, kind: Cast::Tinker, t: k });
                        match self.rng.die(4) {
                            1 => self.units[k].t.abilities.push(Ability::Flail),
                            2 => self.units[k].t.abilities.push(Ability::Bolt { every: 2, die: 6, bonus: 2, dmg: Dmg::Blunt, range: 3 }),
                            3 => self.units[k].plates += 2,
                            _ => self.units[k].t.abilities.push(Ability::Repair { every: 2, amount: 3 }),
                        }
                    }
                }
                Ability::Volley { every, die, bonus, dmg } if round.is_multiple_of(every_of(every, dmg)) => {
                    if let Some(tj) = self.ranged_target(i, self.units[i].t.range) {
                        self.ev(Event::Cast { u: i, kind: Cast::Volley, t: tj });
                        let victims: Vec<usize> = self.enemies_of(i).filter(|&v| self.dist(v, tj) <= 1).collect();
                        for v in victims {
                            let raw = self.rng.damage(die, bonus);
                            hits.push(Hit { attacker: i, target: v, raw, dmg, ..Default::default() });
                        }
                        return;
                    }
                }
                Ability::Flash { every } if round.is_multiple_of(every) => {
                    let adj = self.adjacent_enemies(i);
                    if !adj.is_empty() {
                        self.ev(Event::Cast { u: i, kind: Cast::Flash, t: i });
                        // eyes dazzled once see again for a while: no one stays blind all battle under a cloud of
                        // fireflies
                        for j in adj {
                            if self.units[j].blind_until + 2 < round {
                                self.units[j].blind_until = round + 1;
                                self.ev(Event::Blind { t: j });
                            }
                        }
                        return;
                    }
                }
                Ability::Spit { every, die } if round.is_multiple_of(every) => {
                    if let Some(tj) = self.ranged_target(i, self.units[i].t.range) {
                        self.ev(Event::Cast { u: i, kind: Cast::Spit, t: tj });
                        self.units[tj].glued_until = round + 1;
                        if !self.units[tj].t.has(Trait::PoisonImmune) {
                            self.units[tj].poison += self.rng.die(die) as i32;
                        }
                        self.ev(Event::Glue { t: tj });
                        return;
                    }
                }
                Ability::Brood { every, n } if round.is_multiple_of(every) => {
                    let (side, x, y) = (self.units[i].side, self.units[i].x, self.units[i].y);
                    for _ in 0..n {
                        let mut larva = crate::data::rabochaya();
                        larva.name = "Личинка".into();
                        self.spawn(side, larva, x, y);
                    }
                }
                Ability::Mark { every } if round.is_multiple_of(every) => {
                    let side = self.units[i].side as usize;
                    let target = self.enemies_of(i).max_by_key(|&j| {
                        let t = &self.units[j].t;
                        (t.die as i32 + 2 * t.bonus, Reverse(j))
                    });
                    self.mark[side] = target;
                    if let Some(t) = target {
                        self.ev(Event::Mark { t });
                    }
                }
                Ability::Bolt { every, die, bonus, dmg, range } if round.is_multiple_of(every_of(every, dmg)) => {
                    let target = if range <= 1 { self.melee_target(i) } else { self.ranged_target(i, range) };
                    if let Some(tj) = target {
                        self.ev(Event::Cast { u: i, kind: Cast::Bolt, t: tj });
                        let raw = self.rng.damage(die, bonus);
                        hits.push(Hit { attacker: i, target: tj, raw, dmg, ..Default::default() });
                        return;
                    }
                }
                _ => {}
            }
        }
        if self.units[i].t.has(Trait::NoAttack) {
            return;
        }
        self.normal_attack(i, hits);
    }

    /// Мимикрия: a machine broken below half its health or fallen — its enemy's mimics take up its weapon, in place of
    /// the one they had.
    fn take_apart(&mut self, t: usize) {
        let u = &self.units[t];
        if !(u.t.golem || matches!(u.t.name.as_ref(), "Изобретатель" | "Маньяк" | "Зодчий" | "Отец колосса")) || u.t.has(Trait::Puppet) {
            return;
        }
        let took = match crate::data::unit_key(&u.t.name) {
            Some("mudrets" | "izobretatel") => MIMIC_SHOCK,
            Some("gorn") => MIMIC_FIRE,
            Some("strazh" | "kamenshchik" | "zodchiy") => MIMIC_SHELL,
            Some("orudie" | "otets_kolossa") => MIMIC_BLUNT,
            Some("mekhanik") => MIMIC_MEND,
            Some("manyak") => MIMIC_EDGE,
            _ => 0,
        };
        // one weapon at a time: the last machine broken (a mimic copies, it does not hoard)
        if took != 0 {
            self.mimicry[1 - u.side as usize % 2] = took;
        }
    }

    /// Стрекот: every second round an enemy with four or more chirring bodies beside it shakes with their chirr (metal
    /// rings with it) and loses its blow.
    fn resonates(&self, i: usize) -> bool {
        if !self.round.is_multiple_of(2) {
            return false;
        }
        let side = self.units[i].side;
        (0..self.units.len())
            .filter(|&k| self.units[k].side != side && self.units[k].present() && self.units[k].t.has(Trait::Chirr) && self.dist(i, k) <= 1)
            .take(4)
            .count()
            >= 4
    }

    /// Паутина: a web on the unit's cells and every cell round them, the enemy's too (who stands there is stuck).
    fn spin(&mut self, i: usize) {
        let (x, y, f, side) = (self.units[i].x, self.units[i].y, self.units[i].fp(), self.units[i].side as i8);
        for yy in (y - 1).max(0)..(y + f + 1).min(H) {
            for xx in (x - 1).max(0)..(x + f + 1).min(W) {
                self.web[Grid::idx(xx, yy)] = side;
            }
        }
    }

    /// Fire on a unit standing in a web: the web flares up and the fire runs along it, two cells at most, setting
    /// alight everyone on the burning threads, the spinners too.
    fn web_fire(&mut self, t: usize) {
        let seeds: Vec<usize> = self.cells_of(t).filter(|&c| self.web[c] != -1).collect();
        if seeds.is_empty() {
            return;
        }
        let mut burnt = vec![false; self.web.len()];
        let mut queue: VecDeque<(usize, u32)> = VecDeque::new();
        for c in seeds {
            burnt[c] = true;
            self.web[c] = -1;
            queue.push_back((c, 0));
        }
        while let Some((c, depth)) = queue.pop_front() {
            if depth >= 2 {
                continue;
            }
            let (cx, cy) = ((c as i32) % W, (c as i32) / W);
            for (dx, dy) in DIRS {
                let (nx, ny) = (cx + dx, cy + dy);
                if nx < 0 || ny < 0 || nx >= W || ny >= H {
                    continue;
                }
                let k = Grid::idx(nx, ny);
                if self.web[k] != -1 && !burnt[k] {
                    burnt[k] = true;
                    self.web[k] = -1;
                    queue.push_back((k, depth + 1));
                }
            }
        }
        for k in 0..self.units.len() {
            if self.units[k].present() && !self.units[k].t.armor_type.immune(Dmg::Fire) && self.cells_of(k).any(|c| burnt[c]) {
                self.units[k].burn = self.units[k].burn.max(3);
            }
        }
    }

    fn adjacent_enemies(&self, i: usize) -> Vec<usize> {
        let mut v: Vec<usize> = self.enemies_of(i).filter(|&j| self.dist(i, j) <= 1).collect();
        v.sort_by_key(|&j| (self.units[j].hp, j));
        v
    }

    fn melee_target(&self, i: usize) -> Option<usize> {
        let adj = self.adjacent_enemies(i);
        let mark = self.mark[self.units[i].side as usize];
        let flyer = self.units[i].t.has(Trait::Flyer);
        adj.iter()
            .copied()
            .find(|&j| self.units[j].t.has(Trait::Zaslon))
            .or_else(|| adj.iter().copied().find(|&j| Some(j) == mark))
            .or_else(|| if flyer { adj.iter().copied().find(|&j| self.units[j].t.range > 1 || self.units[j].t.has(Trait::Leader)) } else { None })
            .or(adj.first().copied())
    }

    fn ranged_target(&self, i: usize, range: u32) -> Option<usize> {
        // a midge cloud on the shooter: it sees nothing to aim at
        if self.enemies_of(i).any(|j| self.units[j].t.has(Trait::Cloud) && self.dist(i, j) <= 1) {
            return None;
        }
        let far = self.units[i].t.has(Trait::Navodka);
        self.enemies_of(i)
            .map(|j| (j, self.dist(i, j)))
            .filter(|&(_, d)| d <= range as i32)
            .min_by_key(|&(j, d)| (!self.units[j].t.has(Trait::Glow), if far { -d } else { d }, self.units[j].hp, j))
            .map(|(j, _)| j)
    }

    fn normal_attack(&mut self, i: usize, hits: &mut Vec<Hit>) {
        let (die, bonus, dmg, range) = {
            let t = &self.units[i].t;
            (t.die, t.bonus, t.dmg, t.range)
        };
        let dmg = self.mimic_dmg(i, dmg);
        let probivnoy = self.units[i].t.has(Trait::Probivnoy);
        if self.units[i].t.has(Trait::Caster) {
            // a spell: no secondary weapon; in melee it goes off one time in four; full power at any range
            if !self.adjacent_enemies(i).is_empty() && self.rng.die(4) != 1 {
                return;
            }
            let Some(j) = self.ranged_target(i, range) else { return };
            let raw = self.rng.damage(die, bonus);
            hits.push(Hit { attacker: i, target: j, raw, dmg, ..Default::default() });
            // lightning leaps on to two more enemies beside the target, at half its power (CONCEPT.md, «Молния»)
            if dmg == Dmg::Shock {
                for v in self.beside(i, j, 2) {
                    hits.push(Hit { attacker: i, target: v, raw: (raw + 1) / 2, dmg, ..Default::default() });
                }
            }
            return;
        }
        if range > 1 {
            let adj = self.adjacent_enemies(i);
            if !adj.is_empty() {
                if self.units[i].t.has_ability(|a| *a == Ability::PointBlank) {
                    self.ev(Event::Cast { u: i, kind: Cast::PointBlank, t: adj[0] });
                    for &j in adj.iter().take(3) {
                        let raw = self.rng.damage(die, bonus);
                        hits.push(Hit { attacker: i, target: j, raw, dmg, probivnoy, melee: true, ..Default::default() });
                    }
                } else {
                    // secondary weapon: half power, blunt
                    let raw = (self.rng.damage(die, bonus) + 1) / 2;
                    hits.push(Hit { attacker: i, target: adj[0], raw, dmg: Dmg::Blunt, probivnoy, melee: true, ..Default::default() });
                }
                return;
            }
            if self.units[i].t.has(Trait::Spitter) {
                return; // between its spits the spider does not shoot
            }
            let Some(j) = self.ranged_target(i, range) else { return };
            let mut raw = self.rng.damage(die, bonus);
            let far_half = self.dist(i, j) > (range as i32 + 1) / 2;
            if far_half && !self.units[i].t.has(Trait::Navodka) {
                raw = (raw + 1) / 2;
            }
            let (venom, infect) = self.blow_effects(i);
            hits.push(Hit { attacker: i, target: j, raw, dmg, probivnoy, venom, infect, ..Default::default() });
            // a heavy shot (blunt, from one bigger by 2+) lands on the whole cell of small ones, as a trampling does
            if dmg == Dmg::Blunt && self.units[i].t.size >= self.units[j].t.size + 2 && self.units[j].fp() == 1 {
                let (cx, cy) = (self.units[j].x, self.units[j].y);
                let more: Vec<usize> = self
                    .enemies_of(i)
                    .filter(|&v| v != j && self.units[v].fp() == 1 && self.units[v].x == cx && self.units[v].y == cy && !self.units[v].t.has(Trait::Flyer))
                    .collect();
                for v in more {
                    hits.push(Hit { attacker: i, target: v, raw, dmg, probivnoy, ..Default::default() });
                }
            }
            return;
        }
        let Some(j) = self.melee_target(i) else { return };
        self.melee_blow(i, j, hits);
        if self.units[i].t.has(Trait::TwinBlades) {
            let j2 = self.adjacent_enemies(i).into_iter().find(|&x| x != j).unwrap_or(j);
            self.melee_blow(i, j2, hits);
        }
        if self.units[i].t.has_ability(|a| *a == Ability::Flail) {
            if let Some(&j2) = self.adjacent_enemies(i).iter().find(|&&x| x != j) {
                self.melee_blow(i, j2, hits);
            }
        }
    }

    /// Up to `n` enemies of `i` standing right beside `j` (not `j`): where a leaping bolt goes on to.
    fn beside(&self, i: usize, j: usize, n: usize) -> Vec<usize> {
        let (jx, jy, jf) = (self.units[j].x, self.units[j].y, self.units[j].fp());
        self.enemies_of(i)
            .filter(|&v| v != j && rect_dist(jx, jy, jf, self.units[v].x, self.units[v].y, self.units[v].fp()) <= 1)
            .take(n)
            .collect()
    }

    /// A melee blow; trampling (size bigger by 2+) hits everyone in the target's cell.
    fn melee_blow(&mut self, i: usize, j: usize, hits: &mut Vec<Hit>) {
        let (die, bonus, dmg, size) = {
            let t = &self.units[i].t;
            (t.die, t.bonus, t.dmg, t.size)
        };
        let dmg = self.mimic_dmg(i, dmg);
        let mimic = if self.units[i].t.has(Trait::Mimic) { self.mimicry[self.units[i].side as usize % 2] } else { 0 };
        let probivnoy = self.units[i].t.has(Trait::Probivnoy);
        let tj = &self.units[j];
        // the Devourer at its third stage, the Colossus's size: the blow tramples every enemy of size 5 or less beside it
        let colossal = self.units[i].t.has(Trait::ThirdStage) && self.units[i].growth >= 3;
        // a flyer is not trampled: it is over the blow, not under the foot
        let victims: Vec<usize> = if colossal {
            let mut v = vec![j];
            v.extend(self.adjacent_enemies(i).into_iter().filter(|&k| k != j && self.units[k].t.size <= 5));
            if v.len() > 1 {
                self.ev(Event::Cast { u: i, kind: Cast::Trample, t: i });
            }
            v
        } else if size >= tj.t.size + 2 && tj.fp() == 1 {
            let (cx, cy) = (tj.x, tj.y);
            self.enemies_of(i)
                .filter(|&v| v == j || (self.units[v].fp() == 1 && self.units[v].x == cx && self.units[v].y == cy && !self.units[v].t.has(Trait::Flyer)))
                .collect()
        } else {
            vec![j]
        };
        let mut extra = 0;
        if self.units[i].t.has(Trait::Stroy) && self.allies_adjacent(i) >= 3 {
            extra += 1;
        }
        if Some(j) == self.mark[self.units[i].side as usize] {
            extra += 1;
        }
        extra += 2 * self.units[i].growth as i32;
        // the Maniac's edge +2; a Forge's fire: it sets alight and +1
        if mimic & MIMIC_EDGE != 0 {
            extra += 2;
        }
        if mimic & MIMIC_FIRE != 0 {
            extra += 1;
        }
        let charge = self.units[i].t.has(Trait::Charge) && !self.units[i].charged;
        self.units[i].charged = true;
        let (venom, infect) = self.blow_effects(i);
        for v in victims {
            let mut raw = self.rng.damage(die, bonus + extra);
            if charge {
                raw = raw * 3 / 2;
            }
            // a blow in the back, or at one caught in its web: half as hard again
            if self.behind(i, v) {
                raw = raw * 3 / 2;
                self.ev(Event::Rear { t: v });
            } else if self.on_enemy(v, &self.web) && self.units[v].side != self.units[i].side {
                raw = raw * 3 / 2;
            }
            hits.push(Hit { attacker: i, target: v, raw, dmg, probivnoy, melee: true, knock: charge, venom, infect, ignite: mimic & MIMIC_FIRE != 0, stun: false });
        }
    }

    fn blow_effects(&self, i: usize) -> (u32, bool) {
        let t = &self.units[i].t;
        let venom = t.traits.iter().find_map(|x| if let Trait::Venom { die } = x { Some(*die) } else { None }).unwrap_or(0);
        (venom, t.has(Trait::Infects))
    }

    fn repair(&mut self, i: usize, amount: i32) -> bool {
        let side = self.units[i].side;
        let best = (0..self.units.len())
            .filter(|&k| k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.golem)
            .filter(|&k| self.dist(i, k) <= 1 && self.units[k].hp < self.units[k].t.hp)
            .max_by_key(|&k| (self.units[k].t.hp - self.units[k].hp, Reverse(k)));
        let Some(k) = best else { return false };
        let heal = amount.min(self.units[k].t.hp - self.units[k].hp);
        self.units[k].hp += heal;
        self.ev(Event::Heal { u: i, t: k, amount: heal });
        true
    }

    /// Damage after vulnerability, stun, armor, resistance and elemental resistance.
    pub fn calc(&self, target: usize, raw: i32, dmg: Dmg, probivnoy: bool) -> i32 {
        let t = &self.units[target];
        // a mimic that broke a Guard: its shell two points harder
        let shell = 2 * (t.t.has(Trait::Mimic) && self.mimicry[t.side as usize % 2] & MIMIC_SHELL != 0) as i32;
        crate::model::mitigate(raw, dmg, &t.t, t.armor + shell, t.stunned, probivnoy)
    }

    fn apply(&mut self, h: Hit) {
        let mut t = h.target;
        if !self.units[t].present() {
            return; // already dead: the blow is wasted
        }
        if self.units[t].t.has(Trait::Ghost) {
            // a ghost of the mirage: the blow goes through it, and it melts away
            self.ev(Event::Hit { a: h.attacker, t, dmg: 0 });
            self.kill(t);
            return;
        }
        if self.units[t].t.golem {
            let side = self.units[t].side;
            let guard = (0..self.units.len()).find(|&k| {
                k != t
                    && self.units[k].side == side
                    && self.units[k].present()
                    && !self.units[k].intercept_used
                    && self.units[k].t.has_ability(|a| *a == Ability::Intercept)
                    && self.dist(k, t) <= 1
            });
            if let Some(k) = guard {
                self.units[k].intercept_used = true;
                t = k;
            }
        }
        let mut raw = if self.units[h.attacker].overloaded == self.round { h.raw * 2 } else { h.raw };
        // standing in the enemy's honey: the blow sticks and lands weaker
        if self.on_enemy(h.attacker, &self.honey) {
            raw -= raw / 2;
        }
        // a midge cloud stings past any armor and anything it is made of
        let mut d = if self.units[h.attacker].t.has(Trait::Cloud) && !self.units[t].t.armor_type.immune(h.dmg) {
            raw
        } else {
            self.calc(t, raw, h.dmg, h.probivnoy)
        };
        if d > 0 && self.units[t].plates > 0 {
            self.units[t].plates -= 1;
            d = 0;
            self.ev(Event::Absorbed { t });
        }
        if h.dmg == Dmg::Acid {
            self.corrode(t);
            self.short_circuit(t);
        }
        if h.ignite && !self.units[t].t.armor_type.immune(Dmg::Fire) {
            self.units[t].burn = 3;
        }
        if h.dmg == Dmg::Fire || h.ignite {
            self.web_fire(t);
        }
        self.units[t].hp -= d;
        self.ev(Event::Hit { a: h.attacker, t, dmg: d });
        if h.stun && d > 0 && self.units[t].hp > 0 && !self.units[t].t.has(Trait::Unstoppable) {
            self.units[t].stunned = true;
            self.ev(Event::Stun { t });
        }
        let a = h.attacker;
        if d > 0 && h.venom > 0 && !self.units[t].t.has(Trait::PoisonImmune) {
            self.units[t].poison += self.rng.die(h.venom) as i32;
        }
        // a parasite takes in a machine too: it nests in the works
        if d > 0 && h.infect && self.units[t].infected.is_none() {
            self.units[t].infected = Some(self.units[a].side);
        }
        // a puppeteer's blow hooks it: falling, it rises for the puppeteers
        if d > 0 && self.units[a].t.has(Trait::Puppeteer) {
            self.units[t].hooked = Some(self.units[a].side);
        }
        if h.melee && self.units[a].present() {
            if let Some(die) = self.units[t].t.traits.iter().find_map(|x| if let Trait::Thorns { die } = x { Some(*die) } else { None }) {
                let raw = self.rng.damage(die, 0);
                let back = self.calc(a, raw, Dmg::Pierce, false);
                self.units[a].hp -= back;
                self.ev(Event::Hit { a: t, t: a, dmg: back });
                if self.units[a].hp <= 0 {
                    self.kill(a);
                }
            }
        }
        let crushing = d * 2 > self.units[t].t.hp;
        if self.units[t].hp * 2 < self.units[t].t.hp {
            self.take_apart(t);
        }
        if self.units[t].hp <= 0 {
            // killed by its first wound: every third one still lets a small bud away, with a quarter of the health
            if self.units[t].t.has(Trait::Buds) && !self.units[t].budded {
                let side = self.units[t].side as usize % 2;
                self.buds[side] += 1;
                if self.buds[side].is_multiple_of(3) {
                    self.bud(t, self.units[t].t.hp / 4);
                }
            }
            self.kill(t);
            self.on_kill(a);
        } else {
            let pushable = self.units[t].t.size <= self.units[a].t.size && !self.units[t].t.has(Trait::Unstoppable);
            if (crushing || h.knock) && pushable {
                self.knockback(t, a);
            }
            let u = &self.units[t];
            if u.t.has(Trait::CurlUp) && !u.curled && u.hp * 2 < u.t.hp {
                self.units[t].curled = true;
                self.units[t].armor += 3;
            }
            if d > 0 {
                self.wounded(t);
            }
        }
        if crushing {
            let side = self.units[t].side;
            let neighbours: Vec<usize> = (0..self.units.len())
                .filter(|&k| k != t && self.units[k].side == side && self.units[k].present() && self.dist(k, t) <= 1)
                .collect();
            for k in neighbours {
                self.fear_check(k, 7);
            }
        }
    }

    /// What a wound does to a body that lives through it: a budding one splits.
    fn wounded(&mut self, t: usize) {
        let u = &self.units[t];
        if !u.present() {
            return;
        }
        if u.t.has(Trait::Buds) && !u.budded && u.hp >= 2 {
            let half = self.units[t].hp / 2;
            if self.bud(t, half) {
                self.units[t].hp -= half;
            }
        }
    }

    /// Почкование: a bud with `hp` steps out beside the body; neither buds again. False if there is no room.
    fn bud(&mut self, t: usize, hp: i32) -> bool {
        self.units[t].budded = true;
        if hp < 1 {
            return false;
        }
        let mut bud = self.units[t].t.clone();
        bud.traits.retain(|x| *x != Trait::Buds);
        let (side, x, y) = (self.units[t].side, self.units[t].x, self.units[t].y);
        match self.spawn(side, bud, x, y) {
            Some(b) => {
                self.units[b].hp = hp;
                self.units[b].budded = true;
                true
            }
            None => false,
        }
    }

    /// Acid eats at the armor: a point a round at most, however many hit — a crowd of barrels wears a golem down,
    /// it does not strip it bare at once.
    fn corrode(&mut self, t: usize) {
        if self.units[t].corroded != self.round {
            self.units[t].corroded = self.round;
            let strip = self.units[t].t.armor_type.acid_strip();
            self.units[t].armor = (self.units[t].armor - strip).max(0);
        }
    }

    /// Замыкание: acid on the windings silences the unit for 2 rounds.
    fn short_circuit(&mut self, t: usize) {
        if self.units[t].t.has(Trait::Zamykanie) {
            self.units[t].silenced_until = self.round + 2;
        }
    }

    fn knockback(&mut self, t: usize, a: usize) {
        let (ut, ua) = (&self.units[t], &self.units[a]);
        let sx = ((2 * ut.x + ut.fp()) - (2 * ua.x + ua.fp())).signum();
        let sy = ((2 * ut.y + ut.fp()) - (2 * ua.y + ua.fp())).signum();
        if sx == 0 && sy == 0 {
            return;
        }
        let (side, size, x, y) = (ut.side, ut.t.size, ut.x, ut.y);
        self.grid.sub(size, x, y);
        for (cx, cy) in [(x + sx, y + sy), (x + sx, y), (x, y + sy)] {
            if (cx, cy) != (x, y) && self.grid.can_place(side, size, cx, cy) {
                self.move_to(t, cx, cy);
                self.ev(Event::Knockback { t });
                return;
            }
        }
        self.grid.add(side, size, x, y);
    }

    /// The killer eats («Пожирание») and the Devourer grows.
    fn on_kill(&mut self, a: usize) {
        if !self.units[a].present() {
            return;
        }
        self.units[a].kills += 1;
        // the Devourer has already eaten it in `kill` (whatever falls beside it is its meal, its own kill too)
        if !(self.units[a].t.has(Trait::Grows) && self.units[a].t.has(Trait::Leader)) {
            self.eat(a);
        }
    }

    /// A meal: the killer eats («Пожирание» heals a quarter), the Devourer is fed and grows on every second one —
    /// twice, or thrice with its third stage.
    fn eat(&mut self, a: usize) {
        let round = self.round;
        let u = &mut self.units[a];
        u.last_meal = round;
        if u.t.has(Trait::Devour) {
            u.hp = (u.hp + (u.t.hp / 4).max(1)).min(u.t.hp);
        }
        u.meals += 1;
        // the third stage: grows on every meal, not every second, and one stage further
        let (stages, every) = if u.t.has(Trait::ThirdStage) { (3, 1) } else { (2, 2) };
        if u.t.has(Trait::Grows) && u.t.has(Trait::Leader) && u.meals.is_multiple_of(every) && u.growth < stages {
            u.growth += 1;
            let gain = u.t.hp / 2;
            u.t.hp += gain;
            u.hp += gain;
        }
    }

    fn kill(&mut self, t: usize) {
        let u = &self.units[t];
        if !u.alive {
            return;
        }
        let (size, x, y, side) = (u.t.size, u.x, u.y, u.side);
        if u.on_field {
            self.grid.sub(size, x, y);
        }
        self.units[t].alive = false;
        self.ev(Event::Kill { t });
        // a barrel bursts with acid on the enemies adjacent
        if let Some(die) = self.units[t].t.traits.iter().find_map(|x| if let Trait::BurstAcid { die } = x { Some(*die) } else { None }) {
            // on the enemies beside it only: a whole breed that bursts (a mutation) must not eat its own crowd
            let near: Vec<usize> = self.enemies_of(t).filter(|&k| self.dist(k, t) <= 1).collect();
            for k in near {
                let raw = self.rng.damage(die, 0);
                // a splash: it burns, but does not eat at the armor — that is the barrel's spit (a whole swarm that
                // bursts stripped every golem bare)
                let d = self.calc(k, raw, Dmg::Acid, false);
                self.short_circuit(k);
                self.units[k].hp -= d;
                self.ev(Event::Hit { a: t, t: k, dmg: d });
                if self.units[k].hp <= 0 {
                    self.kill(k);
                }
            }
        }
        // a honey body floods its cells and the cells round them
        if self.units[t].t.has(Trait::Honey) {
            let f = footprint(size);
            for yy in (y - 1).max(0)..(y + f + 1).min(H) {
                for xx in (x - 1).max(0)..(x + f + 1).min(W) {
                    self.honey[Grid::idx(xx, yy)] = side as i8;
                }
            }
        }
        // every third midge body that falls crumbles into a cloud, unless it burnt
        if self.units[t].t.has(Trait::Midges) && self.units[t].burn == 0 {
            let c = &mut self.clouds[side as usize % 2];
            *c += 1;
            if c.is_multiple_of(3) {
                self.spawn(side, crate::data::unit("moshkara"), x, y);
            }
        }
        // an enemy that falls beside the Devourer is its meal: the swarm brings a machine down, the beast eats it (the
        // killer's own meal is counted in on_kill; the Devourer does not eat its own swarm)
        if self.units[t].t.is_army() {
            let eaters: Vec<usize> = (0..self.units.len())
                .filter(|&k| self.units[k].side != side && self.units[k].present() && self.units[k].t.has(Trait::Grows) && self.units[k].t.has(Trait::Leader))
                .filter(|&k| self.dist(k, t) <= 1)
                .collect();
            for k in eaters {
                self.ev(Event::Cast { u: k, kind: Cast::Devour, t });
                self.eat(k);
            }
        }
        // a cloud and a ghost leave nothing behind
        if self.units[t].t.has(Trait::Cloud) || self.units[t].t.has(Trait::Ghost) {
            self.units[t].on_field = false;
        }
        // a mimic swarm takes up the weapon of a machine it sees fall
        self.take_apart(t);
        // a viviparous body lets out one larva of its own side
        if self.units[t].t.has(Trait::Viviparous) {
            let b = &mut self.births[side as usize % 2];
            *b += 1;
            if b.is_multiple_of(3) {
                let mut larva = crate::data::rabochaya();
                larva.name = "Личинка".into();
                self.spawn(side, larva, x, y);
            }
        }
        // an infected machine rises for the puppeteers: larvae work its hull, a quarter of its health left (it falls
        // apart in two rounds, and only then do the larvae come out)
        if let Some(by) = self.units[t].hooked.or(self.units[t].infected) {
            let puppeteers = self.units.iter().any(|u| u.side == by && u.present() && u.t.has(Trait::Puppeteer));
            if puppeteers && self.units[t].t.golem && !self.units[t].t.has(Trait::Puppet) {
                let mut hull = self.units[t].t.clone();
                hull.traits.push(Trait::Puppet);
                hull.abilities.clear(); // larvae work the hull and its weapon, not its modules
                let quarter = (hull.hp / 4).max(1);
                if let Some(p) = self.spawn(by, hull, x, y) {
                    self.units[p].hp = quarter;
                    self.units[p].infected = Some(by);
                    return;
                }
            }
        }
        // larvae hatch from an infected body
        if let Some(by) = self.units[t].infected {
            for _ in 0..2 {
                let mut larva = crate::data::rabochaya();
                larva.name = "Личинка".into();
                self.spawn(by, larva, x, y);
            }
        }
        // a swarm without its leader panics
        if self.units[t].t.has(Trait::Leader) {
            let panicking: Vec<usize> = (0..self.units.len())
                .filter(|&k| self.units[k].side == side && self.units[k].present() && self.units[k].t.has(Trait::Staya))
                .collect();
            for k in panicking {
                self.fear_check(k, 9);
            }
        }
    }

    // ---------------------------------------------------------------- lasting effects
    fn persistent(&mut self) {
        let n = self.units.len();
        for i in 0..n {
            if self.units[i].present() && self.units[i].t.has(Trait::ZharGorna) {
                // one adjacent enemy per round: the first that is not burning yet
                let adj = self.adjacent_enemies(i);
                if let Some(&j) = adj.iter().find(|&&j| self.units[j].burn == 0).or(adj.first()) {
                    self.units[j].burn = 3;
                }
            }
        }
        for j in 0..self.units.len() {
            if self.units[j].present() && self.units[j].poison > 0 {
                let d = ((self.units[j].poison + 9) / 10).max(1).min(self.units[j].poison);
                self.units[j].poison -= d;
                self.units[j].hp -= d;
                self.ev(Event::Poison { t: j, dmg: d });
                if self.units[j].hp <= 0 {
                    self.kill(j);
                }
            }
            // the Devourer starves without a meal for 3 rounds, a tenth of its health a round; hungry at the start of a
            // run, from the 2nd round and a fifth
            let hungry = self.units[j].t.traits.iter().any(|x| matches!(x, Trait::Hungry { .. }));
            let part = if hungry { 5 } else { 10 };
            if self.starving(j) {
                let loss = (self.units[j].t.hp / part).max(1);
                self.units[j].hp -= loss;
                if self.units[j].hp <= 0 {
                    self.kill(j);
                }
            }
        }
        let n = self.units.len();
        for j in 0..n {
            if self.units[j].present() && self.units[j].burn > 0 {
                self.web_fire(j);
                self.units[j].burn -= 1;
                let d = self.calc(j, 3, Dmg::Fire, false);
                self.units[j].hp -= d;
                self.ev(Event::Burn { t: j, dmg: d });
                if self.units[j].hp <= 0 {
                    self.kill(j);
                }
            }
        }
        // a parasite grows in its host: every third round a larva of its side crawls out of it
        if self.round.is_multiple_of(3) {
            let hosts: Vec<(usize, u8)> = (0..n).filter(|&i| self.units[i].present()).filter_map(|i| self.units[i].infected.map(|by| (i, by))).collect();
            for (i, by) in hosts {
                let mut larva = crate::data::rabochaya();
                larva.name = "Личинка".into();
                let (x, y) = (self.units[i].x, self.units[i].y);
                self.spawn(by, larva, x, y);
            }
        }
        // honey: a wounded body next to its own mends a point
        let mending: Vec<usize> = (0..n)
            .filter(|&i| {
                let u = &self.units[i];
                u.present() && u.t.has(Trait::Honey) && u.hp < u.t.hp
            })
            .filter(|&i| {
                let side = self.units[i].side;
                (0..n).any(|k| k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.has(Trait::Honey) && self.dist(i, k) <= 1)
            })
            .collect();
        for i in mending {
            self.units[i].hp = (self.units[i].hp + 2).min(self.units[i].t.hp);
        }
        // a puppet machine falls apart after two rounds
        for i in 0..n {
            if self.units[i].present() && self.units[i].t.has(Trait::Puppet) && self.round >= self.units[i].born + 2 {
                self.kill(i);
            }
        }
        // mimics that broke a Mechanic mend two points
        for i in 0..n {
            let u = &self.units[i];
            if u.present() && u.t.has(Trait::Mimic) && self.mimicry[u.side as usize % 2] & MIMIC_MEND != 0 && u.hp < u.t.hp {
                self.units[i].hp = (u.hp + 2).min(u.t.hp);
            }
        }
        // a midge cloud thins out after two rounds
        for i in 0..n {
            if self.units[i].present() && self.units[i].t.has(Trait::Cloud) && self.round >= self.units[i].born + 2 {
                let (size, x, y) = (self.units[i].t.size, self.units[i].x, self.units[i].y);
                self.grid.sub(size, x, y);
                self.units[i].alive = false;
                self.units[i].on_field = false;
                self.ev(Event::Left { t: i });
            }
        }
        for i in 0..n {
            if self.units[i].present() && self.units[i].t.has(Trait::Naladka) {
                let side = self.units[i].side;
                let mates: Vec<usize> = (0..n)
                    .filter(|&k| k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.golem)
                    .filter(|&k| self.dist(i, k) <= 1)
                    .collect();
                for k in mates {
                    if self.units[k].hp < self.units[k].t.hp {
                        self.units[k].hp += 1;
                    }
                }
            }
        }
    }
}

/// One battle: side 0 against side 1 with a seed.
pub fn fight(a: &[Template], b: &[Template], seed: u64) -> Outcome {
    let mut bt = Battle::new(seed);
    bt.add_armies(a, b);
    bt.run()
}
