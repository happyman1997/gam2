//! The battle: rounds and phases as in docs/CONCEPT.md («Ходы», «Удар и числа»).

use crate::model::{Ability, Dmg, Template, Trait};
use crate::rng::Rng;
use std::cmp::Reverse;

pub const W: i32 = 18;
pub const H: i32 = 14;
pub const EXHAUSTION_FROM: u32 = 50;
pub const MAX_ROUNDS: u32 = 150;
/// Deployment zone depth for each side.
const ZONE: i32 = 6;

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
    /// Round the unit appeared in: summons do not act in it.
    pub born: u32,
    pub charged: bool,
    pub kills: u32,
    pub growth: u32,
    pub last_meal: u32,
    /// Side whose larvae hatch from this unit when it dies (Чума).
    pub infected: Option<u8>,
    pub curled: bool,
    /// Silent (no spells, no modules) up to and including this round (Замыкание).
    pub silenced_until: u32,
    /// Hits twice as hard in this round (Перегрузка).
    pub overloaded: u32,
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
}

impl Grid {
    fn new() -> Self {
        Grid { used: vec![0; (W * H) as usize], side: vec![-1; (W * H) as usize] }
    }
    fn idx(x: i32, y: i32) -> usize {
        (y * W + x) as usize
    }
    fn can_place(&self, side: u8, size: u32, x: i32, y: i32) -> bool {
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
                if self.used[i] + c > 4 {
                    return false;
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
}

pub struct Battle {
    pub units: Vec<Unit>,
    grid: Grid,
    rng: Rng,
    pub round: u32,
    pub log: Option<Vec<Event>>,
    /// Target marked by each side's Hive Mind.
    mark: [Option<usize>; 2],
}

impl Battle {
    pub fn new(seed: u64) -> Self {
        Battle { units: vec![], grid: Grid::new(), rng: Rng::new(seed), round: 0, log: None, mark: [None, None] }
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

    /// Default formation: melee at the front of the zone, ranged and support at the back,
    /// rows filled from the middle outwards. Side 0 stands on the left, side 1 on the right.
    pub fn add_army(&mut self, side: u8, army: &[Template]) {
        for t in army {
            let f = footprint(t.size);
            let back = t.range > 1 || t.has(Trait::NoAttack);
            let mut cols: Vec<i32> = if side == 0 { (0..=ZONE - f).collect() } else { (W - ZONE..=W - f).collect() };
            // front first for melee; for side 0 the front is the right edge of the zone
            let front_first = !back;
            if (side == 0) == front_first {
                cols.reverse();
            }
            let mid = (H - f) / 2;
            let mut rows = vec![mid];
            for k in 1..H {
                for y in [mid - k, mid + k] {
                    if y >= 0 && y + f <= H {
                        rows.push(y);
                    }
                }
            }
            let mut placed = false;
            'outer: for &x in &cols {
                for &y in &rows {
                    if self.grid.can_place(side, t.size, x, y) {
                        self.place(side, t.clone(), x, y);
                        placed = true;
                        break 'outer;
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
            born: self.round,
            charged: false,
            kills: 0,
            growth: 0,
            last_meal: self.round,
            infected: None,
            curled: false,
            silenced_until: 0,
            overloaded: 0,
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
                    if best.map_or(true, |b| d < b.0) {
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
        for u in &self.units {
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
        for u in &self.units {
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
                if !self.units[i].present() || self.units[i].t.speed < step {
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
                    if best.map_or(true, |b| d < b.0) {
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
        let (tx, ty, tf) = {
            let t = &self.units[tj];
            (t.x, t.y, t.fp())
        };
        self.grid.sub(size, x, y);
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
        if (best.2, best.3) != (x, y) {
            self.move_to(i, best.2, best.3);
        } else {
            self.grid.add(side, size, x, y);
        }
    }

    /// Expects the unit already lifted off the grid.
    fn move_to(&mut self, i: usize, x: i32, y: i32) {
        let (side, size) = (self.units[i].side, self.units[i].t.size);
        self.units[i].x = x;
        self.units[i].y = y;
        self.grid.add(side, size, x, y);
        self.ev(Event::Move { u: i, x, y });
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
        let powered = self.powered(i);
        let every_of = |every: u32, dmg: Dmg| if powered && matches!(dmg, Dmg::Fire | Dmg::Shock) { (every - 1).max(1) } else { every };
        let abilities = self.units[i].t.abilities.clone();
        for ab in abilities {
            match ab {
                Ability::Overload { every } if round % every == 0 => {
                    let side = self.units[i].side;
                    let ally = (0..self.units.len())
                        .filter(|&k| k != i && self.units[k].side == side && self.units[k].present() && self.units[k].t.golem)
                        .filter(|&k| !self.units[k].t.has(Trait::NoAttack) && self.dist(i, k) <= 1)
                        .max_by_key(|&k| (self.units[k].t.die as i32 + 2 * self.units[k].t.bonus, Reverse(k)));
                    if let Some(k) = ally {
                        self.units[k].overloaded = round;
                        return;
                    }
                }
                Ability::Fireball { every, die, bonus, range } if round % every_of(every, Dmg::Fire) == 0 => {
                    if let Some(tj) = self.ranged_target(i, range) {
                        let victims: Vec<usize> = self.enemies_of(i).filter(|&v| self.dist(v, tj) <= 1).collect();
                        for v in victims {
                            let raw = self.rng.damage(die, bonus);
                            hits.push(Hit { attacker: i, target: v, raw, dmg: Dmg::Fire, ignite: true, ..Default::default() });
                        }
                        return;
                    }
                }
                Ability::Repair { every, amount } if round % every == 0 => {
                    if self.repair(i, amount) {
                        return;
                    }
                }
                Ability::Volley { every, die, bonus, dmg } if round % every_of(every, dmg) == 0 => {
                    if let Some(tj) = self.ranged_target(i, self.units[i].t.range) {
                        let victims: Vec<usize> = self.enemies_of(i).filter(|&v| self.dist(v, tj) <= 1).collect();
                        for v in victims {
                            let raw = self.rng.damage(die, bonus);
                            hits.push(Hit { attacker: i, target: v, raw, dmg, ..Default::default() });
                        }
                        return;
                    }
                }
                Ability::Flash { every } if round % every == 0 => {
                    let adj = self.adjacent_enemies(i);
                    if !adj.is_empty() {
                        for j in adj {
                            self.units[j].blind_until = round + 1;
                            self.ev(Event::Blind { t: j });
                        }
                        return;
                    }
                }
                Ability::Brood { every, n } if round % every == 0 => {
                    let (side, x, y) = (self.units[i].side, self.units[i].x, self.units[i].y);
                    for _ in 0..n {
                        let mut larva = crate::data::rabochaya();
                        larva.name = "Личинка".into();
                        self.spawn(side, larva, x, y);
                    }
                }
                Ability::Mark { every } if round % every == 0 => {
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
                Ability::Bolt { every, die, bonus, dmg, range } if round % every_of(every, dmg) == 0 => {
                    let target = if range <= 1 { self.melee_target(i) } else { self.ranged_target(i, range) };
                    if let Some(tj) = target {
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
        let probivnoy = self.units[i].t.has(Trait::Probivnoy);
        if self.units[i].t.has(Trait::Caster) {
            // a spell: no secondary weapon; in melee it goes off one time in four; full power at any range
            if !self.adjacent_enemies(i).is_empty() && self.rng.die(4) != 1 {
                return;
            }
            let Some(j) = self.ranged_target(i, range) else { return };
            let raw = self.rng.damage(die, bonus);
            hits.push(Hit { attacker: i, target: j, raw, dmg, ..Default::default() });
            return;
        }
        if range > 1 {
            let adj = self.adjacent_enemies(i);
            if !adj.is_empty() {
                if self.units[i].t.has_ability(|a| *a == Ability::PointBlank) {
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
            let Some(j) = self.ranged_target(i, range) else { return };
            let mut raw = self.rng.damage(die, bonus);
            let far_half = self.dist(i, j) > (range as i32 + 1) / 2;
            if far_half && !self.units[i].t.has(Trait::Navodka) {
                raw = (raw + 1) / 2;
            }
            let (venom, infect) = self.blow_effects(i);
            hits.push(Hit { attacker: i, target: j, raw, dmg, probivnoy, venom, infect, ..Default::default() });
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

    /// A melee blow; trampling (size bigger by 2+) hits everyone in the target's cell.
    fn melee_blow(&mut self, i: usize, j: usize, hits: &mut Vec<Hit>) {
        let (die, bonus, dmg, size) = {
            let t = &self.units[i].t;
            (t.die, t.bonus, t.dmg, t.size)
        };
        let probivnoy = self.units[i].t.has(Trait::Probivnoy);
        let tj = &self.units[j];
        let victims: Vec<usize> = if size >= tj.t.size + 2 && tj.fp() == 1 {
            let (cx, cy) = (tj.x, tj.y);
            self.enemies_of(i).filter(|&v| self.units[v].fp() == 1 && self.units[v].x == cx && self.units[v].y == cy).collect()
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
        let charge = self.units[i].t.has(Trait::Charge) && !self.units[i].charged;
        self.units[i].charged = true;
        let (venom, infect) = self.blow_effects(i);
        for v in victims {
            let mut raw = self.rng.damage(die, bonus + extra);
            if charge {
                raw = raw * 3 / 2;
            }
            hits.push(Hit { attacker: i, target: v, raw, dmg, probivnoy, melee: true, knock: charge, venom, infect, ignite: false });
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
        crate::model::mitigate(raw, dmg, &t.t, t.armor, t.stunned, probivnoy)
    }

    fn apply(&mut self, h: Hit) {
        let mut t = h.target;
        if !self.units[t].present() {
            return; // already dead: the blow is wasted
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
        let raw = if self.units[h.attacker].overloaded == self.round { h.raw * 2 } else { h.raw };
        let mut d = self.calc(t, raw, h.dmg, h.probivnoy);
        if d > 0 && self.units[t].plates > 0 {
            self.units[t].plates -= 1;
            d = 0;
            self.ev(Event::Absorbed { t });
        }
        if h.dmg == Dmg::Acid {
            let strip = self.units[t].t.armor_type.acid_strip();
            self.units[t].armor = (self.units[t].armor - strip).max(0);
            self.short_circuit(t);
        }
        if h.ignite && !self.units[t].t.armor_type.immune(Dmg::Fire) {
            self.units[t].burn = 3;
        }
        self.units[t].hp -= d;
        self.ev(Event::Hit { a: h.attacker, t, dmg: d });
        let a = h.attacker;
        if d > 0 && !self.units[t].t.has(Trait::PoisonImmune) {
            if h.venom > 0 {
                self.units[t].poison += self.rng.die(h.venom) as i32;
            }
            if h.infect {
                self.units[t].infected = Some(self.units[a].side);
            }
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
        if self.units[t].hp <= 0 {
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
        let round = self.round;
        let u = &mut self.units[a];
        u.last_meal = round;
        if u.t.has(Trait::Devour) {
            u.hp = (u.hp + (u.t.hp / 4).max(1)).min(u.t.hp);
        }
        if u.t.has(Trait::Grows) {
            u.kills += 1;
            if u.kills % 2 == 0 && u.growth < 2 {
                u.growth += 1;
                let gain = u.t.hp * 2 / 5;
                u.t.hp += gain;
                u.hp += gain;
            }
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
        // a barrel bursts with acid on everyone adjacent
        if let Some(die) = self.units[t].t.traits.iter().find_map(|x| if let Trait::BurstAcid { die } = x { Some(*die) } else { None }) {
            let near: Vec<usize> = (0..self.units.len()).filter(|&k| k != t && self.units[k].present() && self.dist(k, t) <= 1).collect();
            for k in near {
                let raw = self.rng.damage(die, 0);
                let d = self.calc(k, raw, Dmg::Acid, false);
                let strip = self.units[k].t.armor_type.acid_strip();
                self.units[k].armor = (self.units[k].armor - strip).max(0);
                self.short_circuit(k);
                self.units[k].hp -= d;
                self.ev(Event::Hit { a: t, t: k, dmg: d });
                if self.units[k].hp <= 0 {
                    self.kill(k);
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
            // the Devourer starves without a kill for 3 rounds
            if self.units[j].present() && self.units[j].t.has(Trait::Grows) && self.round >= self.units[j].last_meal + 3 {
                let loss = (self.units[j].t.hp / 10).max(1);
                self.units[j].hp -= loss;
                if self.units[j].hp <= 0 {
                    self.kill(j);
                }
            }
        }
        let n = self.units.len();
        for j in 0..n {
            if self.units[j].present() && self.units[j].burn > 0 {
                self.units[j].burn -= 1;
                let d = self.calc(j, 3, Dmg::Fire, false);
                self.units[j].hp -= d;
                self.ev(Event::Burn { t: j, dmg: d });
                if self.units[j].hp <= 0 {
                    self.kill(j);
                }
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
    bt.add_army(0, a);
    bt.add_army(1, b);
    bt.run()
}
