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

struct Hit {
    attacker: usize,
    target: usize,
    raw: i32,
    dmg: Dmg,
    probivnoy: bool,
}

pub struct Battle {
    pub units: Vec<Unit>,
    grid: Grid,
    rng: Rng,
    pub round: u32,
    pub log: Option<Vec<Event>>,
}

impl Battle {
    pub fn new(seed: u64) -> Self {
        Battle { units: vec![], grid: Grid::new(), rng: Rng::new(seed), round: 0, log: None }
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
        });
        id
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
        for step in 1..=3u32 {
            for i in 0..self.units.len() {
                if self.units[i].present() && self.units[i].t.speed >= step {
                    self.step_unit(i);
                }
            }
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
        let morale = u.t.morale_eff();
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
                self.act(i, &mut hits);
            }
            for h in hits {
                self.apply(h);
            }
            k += group.len();
        }
    }

    fn act(&mut self, i: usize, hits: &mut Vec<Hit>) {
        let round = self.round;
        let abilities = self.units[i].t.abilities.clone();
        for ab in abilities {
            match ab {
                Ability::Repair { every, amount } if round % every == 0 => {
                    if self.repair(i, amount) {
                        return;
                    }
                }
                Ability::Volley { every, die, bonus, dmg } if round % every == 0 => {
                    if let Some(tj) = self.ranged_target(i, self.units[i].t.range) {
                        let victims: Vec<usize> = self.enemies_of(i).filter(|&v| self.dist(v, tj) <= 1).collect();
                        for v in victims {
                            let raw = self.rng.damage(die, bonus);
                            hits.push(Hit { attacker: i, target: v, raw, dmg, probivnoy: false });
                        }
                        return;
                    }
                }
                Ability::Bolt { every, die, bonus, dmg, range } if round % every == 0 => {
                    let target = if range <= 1 { self.melee_target(i) } else { self.ranged_target(i, range) };
                    if let Some(tj) = target {
                        let raw = self.rng.damage(die, bonus);
                        hits.push(Hit { attacker: i, target: tj, raw, dmg, probivnoy: false });
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
        adj.iter().copied().find(|&j| self.units[j].t.has(Trait::Zaslon)).or(adj.first().copied())
    }

    fn ranged_target(&self, i: usize, range: u32) -> Option<usize> {
        let far = self.units[i].t.has(Trait::Navodka);
        self.enemies_of(i)
            .map(|j| (j, self.dist(i, j)))
            .filter(|&(_, d)| d <= range as i32)
            .min_by_key(|&(j, d)| (if far { -d } else { d }, self.units[j].hp, j))
            .map(|(j, _)| j)
    }

    fn normal_attack(&mut self, i: usize, hits: &mut Vec<Hit>) {
        let (die, bonus, dmg, range) = {
            let t = &self.units[i].t;
            (t.die, t.bonus, t.dmg, t.range)
        };
        let probivnoy = self.units[i].t.has(Trait::Probivnoy);
        if range > 1 {
            let adj = self.adjacent_enemies(i);
            if !adj.is_empty() {
                if self.units[i].t.has_ability(|a| *a == Ability::PointBlank) {
                    for &j in adj.iter().take(3) {
                        let raw = self.rng.damage(die, bonus);
                        hits.push(Hit { attacker: i, target: j, raw, dmg, probivnoy });
                    }
                } else {
                    // secondary weapon: half power, blunt
                    let raw = (self.rng.damage(die, bonus) + 1) / 2;
                    hits.push(Hit { attacker: i, target: adj[0], raw, dmg: Dmg::Blunt, probivnoy });
                }
                return;
            }
            let Some(j) = self.ranged_target(i, range) else { return };
            let mut raw = self.rng.damage(die, bonus);
            let far_half = self.dist(i, j) > (range as i32 + 1) / 2;
            if far_half && !self.units[i].t.has(Trait::Navodka) {
                raw = (raw + 1) / 2;
            }
            hits.push(Hit { attacker: i, target: j, raw, dmg, probivnoy });
            return;
        }
        let Some(j) = self.melee_target(i) else { return };
        self.melee_blow(i, j, hits);
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
        for v in victims {
            let raw = self.rng.damage(die, bonus);
            hits.push(Hit { attacker: i, target: v, raw, dmg, probivnoy });
        }
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
        let at = t.t.armor_type;
        if at.immune(dmg) || (dmg == Dmg::Poison && t.t.has(Trait::PoisonImmune)) {
            return 0;
        }
        let mut d = raw;
        if at.weak_to(dmg) {
            d *= 2;
        }
        if t.stunned {
            d += 1;
        }
        if dmg != Dmg::Fire && dmg != Dmg::Poison {
            let mut arm = t.armor.max(0);
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
        if dmg == Dmg::Fire && t.t.has(Trait::FireResist75) {
            d = (d / 4).max(1);
        }
        if dmg == Dmg::Shock && at.metal() {
            d = d * 3 / 2;
        }
        d.max(0)
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
        let mut d = self.calc(t, h.raw, h.dmg, h.probivnoy);
        if d > 0 && self.units[t].plates > 0 {
            self.units[t].plates -= 1;
            d = 0;
            self.ev(Event::Absorbed { t });
        }
        if h.dmg == Dmg::Acid {
            let strip = self.units[t].t.armor_type.acid_strip();
            self.units[t].armor = (self.units[t].armor - strip).max(0);
        }
        self.units[t].hp -= d;
        self.ev(Event::Hit { a: h.attacker, t, dmg: d });
        let crushing = d * 2 > self.units[t].t.hp;
        if self.units[t].hp <= 0 {
            self.kill(t);
        } else if crushing && self.units[t].t.size <= self.units[h.attacker].t.size && !self.units[t].t.has(Trait::Unstoppable) {
            self.knockback(t, h.attacker);
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

    fn kill(&mut self, t: usize) {
        let u = &self.units[t];
        let (size, x, y) = (u.t.size, u.x, u.y);
        if u.on_field {
            self.grid.sub(size, x, y);
        }
        self.units[t].alive = false;
        self.ev(Event::Kill { t });
    }

    // ---------------------------------------------------------------- lasting effects
    fn persistent(&mut self) {
        let n = self.units.len();
        for i in 0..n {
            if self.units[i].present() && self.units[i].t.has(Trait::ZharGorna) {
                let adj = self.adjacent_enemies(i);
                for j in adj {
                    self.units[j].burn = 3;
                }
            }
        }
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
