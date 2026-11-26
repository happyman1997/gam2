//! The battle as the game shows it: the simulation runs it round by round (sim: two armies and a seed in, events
//! out), and the playback turns each round into frames — first everyone walks, then the blows land one after
//! another, each with its effect and its number; the killed lie where they fell.

use sim::data::{start_izobretatel, start_pozhiratel};
use sim::model::{Template, Trait, Weather};
use crate::text::t as t_;
use sim::{Battle, Event, Outcome};

pub const FR: i32 = 30; // frames a round takes at ×1 (24 fps)
pub const MOVE: i32 = 10; // of them, walking
pub const CW: f32 = 50.0;
pub const CH: f32 = 34.0;
/// Where cell (0, 0) begins on the field's picture (render::FW×FH): the 36×30 cells in the middle of its width.
pub const X0: f32 = 60.0;
pub const Y0: f32 = 46.0;

#[derive(Clone)]
pub struct UnitInfo {
    pub name: String,
    pub side: u8,
    pub fp: i32,
    /// The simulation's size: in one cell stand four of size 1 or two of size 2, never mixed.
    pub size: u32,
    pub max_hp: i32,
    pub leader: bool,
    /// A body of the Foundry (a golem, a leader of the forge), not of the swarm: it walks heavily, rings, breaks.
    pub machine: bool,
    /// A midge cloud (Мошкара): no body, no corpse, not counted as the army.
    pub cloud: bool,
    /// A ghost of the Hive Mind's mirage: see-through, not counted.
    pub ghost: bool,
    /// A fallen machine worked by larvae (Кукловод): sickly, not counted.
    pub puppet: bool,
    /// The modules on a golem with their levels (finds.ron keys): drawn over its body.
    pub mods: Vec<(String, u8)>,
    /// A wall of the Architect's: a block of masonry, not a body.
    pub wall: bool,
}

#[derive(Clone, Copy, Default)]
pub struct State {
    pub x: i32,
    pub y: i32,
    pub present: bool,
    pub alive: bool,
    pub hp: i32,
    pub growth: u32,
    /// What is on it now, `S_*` bits: burning, poisoned, stunned… (drawn as glyphs over its head, fire on its body).
    pub flags: u16,
}

pub const S_BURN: u16 = 1;
pub const S_POISON: u16 = 1 << 1;
pub const S_STUN: u16 = 1 << 2;
pub const S_FEAR: u16 = 1 << 3;
pub const S_MARK: u16 = 1 << 4;
pub const S_INFECT: u16 = 1 << 5;
pub const S_HOOK: u16 = 1 << 6;
pub const S_BLIND: u16 = 1 << 7;
pub const S_GLUE: u16 = 1 << 8;
pub const S_WEB: u16 = 1 << 9;
pub const S_SHRED: u16 = 1 << 10;
pub const S_STALL: u16 = 1 << 11;
pub const S_HUNGRY: u16 = 1 << 12;
/// The glyph of each state, in the order they stand in a row over a head (the worst first).
pub const STATUS_GLYPHS: [(u16, &str); 13] = [
    (S_HUNGRY, "status/hunger"),
    (S_BURN, "status/burn"),
    (S_STUN, "status/stun"),
    (S_FEAR, "status/fear"),
    (S_MARK, "status/mark"),
    (S_HOOK, "status/hook"),
    (S_INFECT, "status/infected"),
    (S_POISON, "status/poison"),
    (S_BLIND, "status/blind"),
    (S_GLUE, "status/glued"),
    (S_WEB, "status/web"),
    (S_STALL, "status/stall"),
    (S_SHRED, "status/shred"),
];

pub struct Round {
    pub before: Vec<State>,
    pub after: Vec<State>,
    pub events: Vec<Event>,
    /// The web and the honey on the field as the round ends, cell by cell (`y * W + x`): whose, -1 none; empty when
    /// the field has none.
    pub web: Vec<i8>,
    pub honey: Vec<i8>,
    /// What each side's swarm has taken up from the machines it broke (Мимикрия), `sim::battle::MIMIC_*`.
    pub mimic: [u8; 2],
    /// The ground as the round ends, cell by cell: spilt oil and slime (`sim::battle::OIL`, `GOO`), how long the oil
    /// still burns, the earthquake's cracks (1); empty when the field has none.
    pub ground: Vec<u8>,
    pub flames: Vec<u8>,
    pub rift: Vec<u8>,
}

pub struct Record {
    pub units: Vec<UnitInfo>,
    pub rounds: Vec<Round>,
    pub outcome: Outcome,
    pub seed: u64,
    /// The frame each unit was killed on (for a corpse's age).
    pub died_at: Vec<Option<i32>>,
    /// What the battle did to side 0's army (who of it fell, by its place in the army) and how many of side 1 fell.
    pub dead0: Vec<usize>,
    pub kills1: u32,
    /// How many each unit killed in the battle (for its summary).
    pub kills: Vec<u32>,
    /// The ground it is fought on: 0 an ordinary fight's, 1 an elite's, 2 a boss's.
    pub ground: usize,
    /// What the leaders take from it for the run (Память роя, Ты — то, что ты ешь): `run::BattleResult`'s.
    pub foe_kills: Vec<(u8, u32)>,
    pub eaten: Vec<u8>,
    /// The sky over it.
    pub weather: Weather,
    /// What its elite enemy is besides its numbers (set by the run's road).
    pub affix: sim::model::Affix,
}

fn states(bt: &Battle) -> Vec<State> {
    let r = bt.round;
    bt.units
        .iter()
        .enumerate()
        .map(|(i, u)| {
            let mut flags = 0;
            for (on, bit) in [
                (u.burn > 0, S_BURN),
                (u.poison > 0, S_POISON),
                (u.stunned, S_STUN),
                (u.fleeing, S_FEAR),
                (bt.marked(i), S_MARK),
                (u.infected.is_some(), S_INFECT),
                (u.hooked.is_some(), S_HOOK),
                // the timed ones hold through the round they were set for (0: never set)
                (u.blind_until >= r && u.blind_until > 0, S_BLIND),
                (u.glued_until >= r && u.glued_until > 0, S_GLUE),
                (u.struggling, S_WEB),
                // corrosion is for the rest of the battle: the round it last bit, MAX if never
                (u.corroded != u32::MAX, S_SHRED),
                (u.silenced_until >= r && u.silenced_until > 0, S_STALL),
                (bt.starving(i), S_HUNGRY),
            ] {
                if on && u.alive {
                    flags |= bit;
                }
            }
            State { x: u.x, y: u.y, present: u.on_field, alive: u.alive, hp: u.hp, growth: u.growth, flags }
        })
        .collect()
}

fn infos(bt: &Battle) -> Vec<UnitInfo> {
    bt.units
        .iter()
        .map(|u| UnitInfo {
            name: u.t.name.to_string(),
            side: u.side,
            fp: u.fp(),
            size: u.t.size,
            max_hp: u.t.hp,
            // the leaders; the Foundry's human leaders also by name, as older records may lack the trait
            leader: u.t.has(Trait::Leader) || matches!(u.t.name.as_ref(), "Изобретатель" | "Маньяк" | "Зодчий" | "Отец колосса"),
            machine: u.t.golem || matches!(u.t.name.as_ref(), "Изобретатель" | "Маньяк" | "Зодчий" | "Отец колосса"),
            cloud: u.t.has(Trait::Cloud),
            ghost: u.t.has(Trait::Ghost),
            puppet: u.t.has(Trait::Puppet),
            mods: u.t.mods.clone(),
            wall: u.t.has(Trait::Wall),
        })
        .collect()
}

/// The demo's battle: the Inventor's start (left) against the Devourer's (right).
pub fn record(seed: u64) -> Record {
    record_of(seed, &start_izobretatel(), &start_pozhiratel())
}

/// A battle of army `a` (left) against army `b` (right), round by round.
pub fn record_of(seed: u64, a: &[Template], b: &[Template]) -> Record {
    record_in(seed, a, b, Weather::Clear)
}

/// The same under a sky (a road's weather).
pub fn record_in(seed: u64, a: &[Template], b: &[Template], weather: Weather) -> Record {
    let mut bt = Battle::new(seed).with_log().with_weather(weather);
    bt.add_armies(a, b);
    let mut rounds = vec![];
    let outcome = loop {
        let before = states(&bt);
        let n0 = bt.log.as_ref().map(|l| l.len()).unwrap_or(0);
        let done = bt.step();
        let mut before = before;
        let after = states(&bt);
        while before.len() < after.len() {
            let mut s = after[before.len()]; // born this round: it appears where it hatched
            s.present = false;
            before.push(s);
        }
        let events = bt.log.as_ref().map(|l| l[n0..].to_vec()).unwrap_or_default();
        let layer = |l: &[i8]| if l.iter().any(|&c| c != -1) { l.to_vec() } else { vec![] };
        // the battle notes what any side would take up from a machine; only a side with Мимикрия does
        let mimic = |side: u8| if bt.units.iter().any(|u| u.side == side && u.t.has(Trait::Mimic)) { bt.mimicry(side) } else { 0 };
        let bytes = |l: &[u8]| if l.iter().any(|&c| c != 0) { l.to_vec() } else { vec![] };
        let rift: Vec<u8> = bt.rift().iter().map(|&c| c as u8).collect();
        rounds.push(Round {
            before,
            after,
            events,
            web: layer(bt.web()),
            honey: layer(bt.honey()),
            mimic: [mimic(0), mimic(1)],
            ground: bytes(bt.ground()),
            flames: bytes(bt.flames()),
            rift: bytes(&rift),
        });
        if let Some(o) = done {
            break o;
        }
    };
    // the rounds before a unit was summoned don't know it: there it is not on the field yet
    for r in &mut rounds {
        r.before.resize(bt.units.len(), State::default());
        r.after.resize(bt.units.len(), State::default());
    }
    let res = sim::run::result_of(&bt, outcome.winner);
    let kills = bt.units.iter().map(|u| u.kills).collect();
    let mut rec = Record {
        units: infos(&bt),
        rounds,
        outcome,
        seed,
        died_at: vec![],
        dead0: res.dead,
        kills1: res.kills,
        kills,
        ground: 0,
        foe_kills: res.foe_kills,
        eaten: res.eaten,
        weather,
        affix: sim::model::Affix::None,
    };
    rec.died_at = vec![None; rec.units.len()];
    for r in 0..rec.rounds.len() {
        for m in rec.moments(r) {
            if let Event::Kill { t } = m.ev {
                rec.died_at[t].get_or_insert(m.frame);
            }
        }
    }
    rec
}

/// What a frame shows of one unit.
pub struct Shown {
    pub id: usize,
    pub x: f32,
    pub y: f32,
    pub pose: Pose,
    /// The cell it stands in at the end of the round (small ones share a cell, spread over its four places).
    pub cell: (i32, i32),
    /// The frame it was killed on, if that was this round (the fall is still playing).
    pub dead_at: Option<i32>,
}

#[derive(Clone, Copy, PartialEq)]
pub enum Pose {
    Idle,
    Attack,
    Dead,
    /// Walking: a running step count; the drawing picks the frame of the walk from it.
    Walk(u8),
}

/// Something that happens at a moment in a round: a blow, a kill, a heal, a summon...
pub struct Moment {
    pub frame: i32,
    pub ev: Event,
}

#[derive(Clone, Copy, PartialEq)]
pub enum NumStyle {
    Hit,
    Crit,
    Hurt,
    Heal,
    Poison,
    Miss,
    /// A state put on it (оглушён): its own line, not merged with the blows' numbers.
    Status,
}

pub struct Number {
    pub text: String,
    pub style: NumStyle,
    /// The ground point of the unit it is about (the drawing puts it over the head, clear of the body).
    pub x: f32,
    pub y: f32,
    pub start: i32,
    /// The unit it is about.
    pub t: usize,
    /// Its place among the numbers over the same unit at the same time (0, 1, 2…): they stack, not cover each other.
    pub k: i32,
    /// The damage it shows (blows on one unit in quick succession add up into one number).
    pub value: i32,
    /// The frame it is gone by at the latest (when the next blow's sum takes its place).
    pub end: i32,
}

pub struct Cue {
    pub frame: i32,
    pub name: &'static str,
    pub gain: f32,
    pub x: f32,
}

pub struct Effect {
    pub name: &'static str,
    pub x: f32,
    pub y: f32,
    pub start: i32,
    /// A bolt: from whom to whom (drawn from the attacker's emit point to the target's body, not a sheet).
    pub link: Option<(usize, usize)>,
    /// Faces left (a sheet drawn facing right, mirrored).
    pub flip: bool,
    /// A missile: it flies from here to (x, y) over `FLY` frames from `start` (the fireball, the gob, the stone).
    pub from: Option<(f32, f32)>,
}

/// Frames a missile is in the air.
pub const FLY: i32 = 8;

impl Record {
    pub fn frames(&self) -> i32 {
        self.rounds.len() as i32 * FR
    }

    /// When each event of a round lands: the walk first, then the blows one after another.
    pub fn moments(&self, r: usize) -> Vec<Moment> {
        let evs: Vec<&Event> = self.rounds[r].events.iter().filter(|e| !matches!(e, Event::Round(_) | Event::Move { .. })).collect();
        let n = evs.len().max(1) as i32;
        let span = FR - MOVE - 4;
        evs.into_iter()
            .enumerate()
            .map(|(k, e)| Moment { frame: r as i32 * FR + MOVE + 2 + span * k as i32 / n, ev: e.clone() })
            .collect()
    }

    /// The ground point of a unit standing at (x, y) with footprint fp.
    pub fn spot(x: i32, y: i32, fp: i32) -> (f32, f32) {
        (X0 + (x as f32 + fp as f32 / 2.0) * CW, Y0 + (y as f32 + fp as f32 * 0.72) * CH)
    }

    /// Every unit as frame `ff` shows it: where it stands (walking in the first part of a round, between frames
    /// too, for a smooth video), its pose; the killed lie where they fell, the fled are gone.
    pub fn shown(&self, ff: f32) -> Vec<Shown> {
        let f = (ff as i32).clamp(0, self.frames() - 1);
        let r = (f / FR) as usize;
        let ph = f % FR;
        let round = &self.rounds[r];
        let ms = self.moments(r);
        let mut out = vec![];
        let walked = if ff as i32 == f { ff - (r as i32 * FR) as f32 } else { ph as f32 };
        let t = (walked / MOVE as f32).clamp(0.0, 1.0);
        let e = 1.0 - (1.0 - t) * (1.0 - t);
        for (id, info) in self.units.iter().enumerate() {
            let (b, a) = (round.before[id], round.after[id]);
            let killed_at = ms.iter().find(|m| matches!(m.ev, Event::Kill { t } if t == id)).map(|m| m.frame);
            // summoned, or out of the belly that swallowed it: it appears there and then
            let born_at = ms.iter().find(|m| matches!(m.ev, Event::Summon { u } if u == id) || matches!(m.ev, Event::Burst { t } if t == id)).map(|m| m.frame);
            // swallowed, or pupated into another: gone at that moment, no corpse
            let gone_at = ms.iter().find(|m| matches!(m.ev, Event::Swallow { t, .. } if t == id) || matches!(m.ev, Event::Morph { from, .. } if from == id)).map(|m| m.frame);
            // hurled, or swapped in a flash: where it stood when it happened, and when
            let jump = ms.iter().find_map(|m| match m.ev {
                Event::Thrown { t, fx, fy, .. } if t == id => Some((m.frame, fx, fy, true)),
                Event::Swap { a, ax, ay, .. } if a == id => Some((m.frame, ax, ay, false)),
                Event::Swap { b, bx, by, .. } if b == id => Some((m.frame, bx, by, false)),
                _ => None,
            });
            if !b.present && !a.present {
                continue; // fled off the field, or not summoned yet
            }
            if !b.alive && !a.alive {
                let (x, y) = Self::spot(a.x, a.y, info.fp); // killed earlier: it lies where it fell
                out.push(Shown { id, x, y, pose: Pose::Dead, cell: (a.x, a.y), dead_at: None });
                continue;
            }
            if let Some(bf) = born_at {
                if f < bf {
                    continue;
                }
            }
            if let Some(g) = gone_at {
                if f >= g {
                    continue;
                }
            }
            let (bx, by) = Self::spot(b.x, b.y, info.fp);
            let (ax, ay) = Self::spot(a.x, a.y, info.fp);
            let (mut x, mut y) = if born_at.is_some() { (ax, ay) } else { (bx + (ax - bx) * e, by + (ay - by) * e) };
            if let Some((jf, jx, jy, thrown)) = jump {
                // it walks to where it is grabbed (or swapped from), then flies in an arc (or is just there)
                let (gx, gy) = Self::spot(jx, jy, info.fp);
                if f < jf {
                    (x, y) = (bx + (gx - bx) * e, by + (gy - by) * e);
                } else if thrown && f < jf + FLY {
                    let q = (f - jf) as f32 / FLY as f32;
                    (x, y) = (gx + (ax - gx) * q, gy + (ay - gy) * q - 90.0 * 4.0 * q * (1.0 - q));
                } else {
                    (x, y) = (ax, ay);
                }
            }
            let morphed = gone_at.is_some() && !a.alive;
            let dead = !morphed && (killed_at.map(|k| f >= k).unwrap_or(false) || (!a.alive && killed_at.is_none() && ph >= MOVE));
            if !a.present && !dead && ph >= MOVE && gone_at.is_none() {
                continue;
            }
            let attacking = ms.iter().any(|m| matches!(m.ev, Event::Hit { a: at, .. } if at == id) && (f - m.frame).abs() <= 4);
            let walking = (b.x, b.y) != (a.x, a.y) && walked < MOVE as f32;
            let pose = if dead {
                Pose::Dead
            } else if attacking {
                Pose::Attack
            } else if walking {
                Pose::Walk(((ff / 1.25) as i32).rem_euclid(8) as u8)
            } else {
                Pose::Idle
            };
            out.push(Shown { id, x, y, pose, cell: (a.x, a.y), dead_at: killed_at.filter(|_| dead) });
        }
        out
    }

    /// The hp and growth of a unit as frame f shows them (after the round's blows once they have landed).
    pub fn state_at(&self, id: usize, f: i32) -> State {
        let f = f.clamp(0, self.frames() - 1);
        let r = (f / FR) as usize;
        if f % FR >= FR - 4 {
            self.rounds[r].after[id]
        } else {
            self.rounds[r].before[id]
        }
    }

    /// The sounds of the whole battle, each with its frame: blows by who strikes whom (a creature's jaws and the
    /// golem ringing under them, a golem's blow crunching a body, a discharge, the mortar's blast — once a volley),
    /// the killed (a wet squish and a low rattle for a creature, a mechanical blast for a golem), a heal (steam), a miss;
    /// the golems' heavy steps when they walk; the jingle at the end. The swarm's chirring under it all is a loop
    /// (audio.rs), not a cue.
    pub fn cues(&self) -> Vec<Cue> {
        let mut out = vec![];
        for r in 0..self.rounds.len() {
            let round = &self.rounds[r];
            let walked = self.units.iter().enumerate().any(|(i, u)| {
                u.machine && round.before[i].alive && (round.before[i].x, round.before[i].y) != (round.after[i].x, round.after[i].y)
            });
            if walked {
                out.push(Cue { frame: r as i32 * FR + 1, name: "step", gain: 0.0, x: 200.0 });
                out.push(Cue { frame: r as i32 * FR + 6, name: "step", gain: -2.0, x: 220.0 });
            }
            let mut last_volley: Option<(usize, i32)> = None;
            for m in self.moments(r) {
                let at = |id: usize| Self::spot(round.after[id].x, round.after[id].y, self.units[id].fp).0;
                match m.ev {
                    Event::Hit { a, t, dmg } => {
                        let att = &self.units[a];
                        if matches!(att.name.as_str(), "Мудрец" | "Изобретатель") {
                            // the discharge sounds as the bolt leaves the staff (it flies three frames), hit or miss
                            out.push(Cue { frame: m.frame - 3, name: "zap", gain: 0.0, x: (at(a) + at(t)) / 2.0 });
                            continue;
                        }
                        let name = if dmg <= 0 {
                            "miss"
                        } else {
                            match att.name.as_str() {
                                "Орудие" => {
                                    if last_volley.map(|(v, fr)| v == a && (m.frame - fr) < 6).unwrap_or(false) {
                                        continue;
                                    }
                                    last_volley = Some((a, m.frame));
                                    // the barrel fires as the gun rears up, the shell bursts a moment later
                                    out.push(Cue { frame: m.frame - 4, name: "shot", gain: 0.0, x: at(a) });
                                    "blast"
                                }
                                _ if !att.machine => "bite",
                                _ => "hit_flesh",
                            }
                        };
                        out.push(Cue { frame: m.frame, name, gain: 0.0, x: at(t) });
                        if name == "bite" && !self.units[t].leader {
                            // the jaws land on metal: the golem rings
                            out.push(Cue { frame: m.frame + 1, name: "hit_metal", gain: 0.0, x: at(t) });
                        }
                    }
                    Event::Kill { t } => {
                        let name = if !self.units[t].machine { "squish" } else { "break" };
                        out.push(Cue { frame: m.frame, name, gain: 0.0, x: at(t) });
                        if !self.units[t].machine {
                            out.push(Cue { frame: m.frame + 2, name: "death_rattle", gain: 0.0, x: at(t) });
                        }
                    }
                    Event::Heal { t, .. } => out.push(Cue { frame: m.frame, name: "heal", gain: 0.0, x: at(t) }),
                    Event::Absorbed { t } => out.push(Cue { frame: m.frame, name: "miss", gain: 0.0, x: at(t) }),
                    // the hurled one comes down with a crash
                    Event::Thrown { t, .. } => out.push(Cue { frame: m.frame + FLY, name: "blast", gain: 0.0, x: at(t) }),
                    Event::Arc { a, .. } | Event::Swap { a, .. } => out.push(Cue { frame: m.frame, name: "zap", gain: -4.0, x: at(a) }),
                    Event::Swallow { u, .. } => out.push(Cue { frame: m.frame, name: "bite", gain: 0.0, x: at(u) }),
                    Event::Burst { t } | Event::Morph { to: t, .. } => out.push(Cue { frame: m.frame, name: "squish", gain: 0.0, x: at(t) }),
                    // the sky splits: the crack of a strike, the thunder after it
                    Event::Strike { t } => {
                        out.push(Cue { frame: m.frame, name: "zap", gain: 2.0, x: at(t) });
                        out.push(Cue { frame: m.frame + 2, name: "blast", gain: -2.0, x: at(t) });
                    }
                    Event::Rift { .. } => out.push(Cue { frame: m.frame, name: "blast", gain: 0.0, x: 480.0 }),
                    Event::Bump { b, .. } => out.push(Cue { frame: m.frame, name: "hit_flesh", gain: -2.0, x: at(b) }),
                    Event::Surge { t } => out.push(Cue { frame: m.frame, name: "zap", gain: 0.0, x: at(t) }),
                    Event::Phase { u } => out.push(Cue { frame: m.frame, name: "blast", gain: 2.0, x: at(u) }),
                    // the habits: time turned back, a cocoon spun, the banner raised, the bell rung
                    Event::Rewind { t } | Event::Banner { u: t } => out.push(Cue { frame: m.frame, name: "heal", gain: 0.0, x: at(t) }),
                    Event::Cocoon { t } => out.push(Cue { frame: m.frame, name: "squish", gain: 0.0, x: at(t) }),
                    Event::Bell { u } => out.push(Cue { frame: m.frame, name: "zap", gain: -2.0, x: at(u) }),
                    _ => {}
                }
            }
        }
        let end = if self.outcome.winner == Some(1) { "win" } else { "lose" };
        out.push(Cue { frame: self.frames() + 2, name: end, gain: 0.0, x: 480.0 });
        out.sort_by_key(|c| c.frame);
        // a volley that kills five at once: two deaths are heard, the rest would only be a wall of noise; a second
        // blow of a kind within a third of a second comes a little quieter
        let cap = |n: &str| match n {
            "squish" | "death_rattle" | "break" | "miss" | "blast" | "shot" => 2,
            "bite" | "hit_metal" | "hit_flesh" | "zap" => 3,
            _ => usize::MAX,
        };
        let mut kept: Vec<Cue> = vec![];
        for c in out {
            let near = kept.iter().rev().take_while(|k| c.frame - k.frame < 8).filter(|k| k.name == c.name).count();
            if near >= cap(c.name) {
                continue;
            }
            kept.push(Cue { gain: c.gain - 3.0 * near as f32, ..c });
        }
        kept
    }

    /// The numbers and effects of the whole battle, each with the frame it starts on.
    pub fn sparks(&self) -> (Vec<Number>, Vec<Effect>) {
        let mut nums = vec![];
        let mut fx = vec![];
        for r in 0..self.rounds.len() {
            let after = &self.rounds[r].after;
            let mut last_volley: Option<(usize, i32)> = None;
            // who cast something this round: its hits are shown by the cast's own effect, not a spark each
            let mut cast_by: Vec<usize> = vec![];
            // the Inventor's net has run this round: his hits from now on are its jolts, not bolts from his glove
            let mut netted: Vec<usize> = vec![];
            for m in self.moments(r) {
                let at = |id: usize| {
                    let s = after[id];
                    Self::spot(s.x, s.y, self.units[id].fp)
                };
                match m.ev {
                    Event::Hit { a, t, dmg } => {
                        // a blow inside a belly: nothing to show where it is digested
                        if !after[t].present && after[t].alive {
                            continue;
                        }
                        let (x, y) = at(t);
                        let att = &self.units[a];
                        let swarm_hits = !att.machine;
                        let style = if dmg <= 0 {
                            NumStyle::Miss
                        } else if swarm_hits && dmg >= 10 {
                            NumStyle::Crit
                        } else if swarm_hits {
                            NumStyle::Hit
                        } else {
                            NumStyle::Hurt
                        };
                        // blows on one unit in quick succession: one number that grows and pops again with each
                        // (a second miss replaces the first)
                        let kin = |p: NumStyle| p == style || matches!((p, style), (NumStyle::Hit, NumStyle::Crit) | (NumStyle::Crit, NumStyle::Hit));
                        let prev = nums.iter().rposition(|n: &Number| n.t == t && n.end > m.frame && m.frame - n.start < 14 && kin(n.style));
                        if let Some(j) = prev {
                            nums[j].end = m.frame;
                        }
                        let (value, style) = match prev {
                            Some(j) if style != NumStyle::Miss => {
                                (nums[j].value + dmg, if nums[j].style == NumStyle::Crit { NumStyle::Crit } else { style })
                            }
                            _ => (dmg.max(0), style),
                        };
                        // a sum never shows more than the unit had: three shells into one ant are not "−86"
                        let value = value.min(self.units[t].max_hp.max(1));
                        let text = match style {
                            NumStyle::Miss => t_("num.miss"),
                            NumStyle::Crit => format!("{value}!"),
                            NumStyle::Hurt => format!("-{value}"),
                            _ => format!("{value}"),
                        };
                        nums.push(Number { text, style, x, y, start: m.frame, t, k: 0, value, end: i32::MAX });
                        if cast_by.contains(&a) {
                            continue;
                        }
                        if netted.contains(&a) {
                            fx.push(Effect { name: "zap-hit", x, y: y - 14.0, start: m.frame, link: None, flip: false, from: None });
                            continue;
                        }
                        let name: &'static str = match att.name.as_str() {
                            "Мудрец" | "Изобретатель" => {
                                fx.push(Effect { name: "bolt", x, y, start: m.frame, link: Some((a, t)), flip: false, from: None });
                                "zap-hit"
                            }
                            "Орудие" => {
                                // a volley: one blast over the cell for all the hits it makes at once
                                if last_volley.map(|(v, fr)| v == a && (m.frame - fr) < 6).unwrap_or(false) {
                                    continue;
                                }
                                last_volley = Some((a, m.frame));
                                "small-explosion"
                            }
                            // the swarm with a Sage's or an Inventor's current in its bite (Мимикрия): its bites crackle
                            _ if !att.machine && self.rounds[r].mimic[att.side as usize % 2] & sim::battle::MIMIC_SHOCK != 0 && (a + t) % 3 == 0 => "zap-hit",
                            _ => "hit-spark",
                        };
                        fx.push(Effect { name, x, y: if name == "hit-spark" { y - 14.0 } else { y }, start: m.frame, link: None, flip: false, from: None });
                    }
                    Event::Cast { u, kind, t } => {
                        use sim::Cast;
                        // what the cast's own effect shows in place of a spark a blow (a fireball's burst, a shell's,
                        // the quake's, a bolt, the grapeshot, the trample); the rest go off besides its blows
                        if matches!(kind, Cast::Fireball | Cast::Volley | Cast::Quake | Cast::Bolt | Cast::PointBlank | Cast::Trample) {
                            cast_by.push(u);
                        }
                        let (tx, ty) = at(t);
                        let (ux, uy) = at(u);
                        let left = tx < ux;
                        let fx_at = |name, x, y, start, flip| Effect { name, x, y, start, link: None, flip, from: None };
                        match kind {
                            Cast::Fireball => {
                                fx.push(Effect { name: "fireball", x: tx, y: ty - 16.0, start: m.frame, link: None, flip: left, from: Some((ux, uy - 40.0)) });
                                fx.push(fx_at("small-explosion", tx, ty, m.frame + FLY, false));
                            }
                            Cast::Volley => fx.push(fx_at("small-explosion", tx, ty, m.frame + 2, false)),
                            Cast::Quake => fx.push(fx_at("ground-slam", ux, uy, m.frame, false)),
                            Cast::Overload | Cast::Tinker => {
                                fx.push(Effect { name: "bolt", x: tx, y: ty, start: m.frame, link: Some((u, t)), flip: false, from: None });
                                fx.push(fx_at("zap-hit", tx, ty - 20.0, m.frame, false));
                            }
                            Cast::Flash => fx.push(fx_at("mana-burst", ux, uy, m.frame, false)),
                            Cast::Spit => {
                                fx.push(Effect { name: "gob", x: tx, y: ty - 8.0, start: m.frame, link: None, flip: left, from: Some((ux, uy - 10.0)) });
                                fx.push(fx_at("acid-splash", tx, ty, m.frame + FLY, false));
                            }
                            Cast::Bolt => {
                                if (tx - ux).abs() + (ty - uy).abs() > 1.6 * CW {
                                    // the catapult's stone, thrown in an arc
                                    fx.push(Effect { name: "stone", x: tx, y: ty - 10.0, start: m.frame, link: None, flip: left, from: Some((ux, uy - 50.0)) });
                                    fx.push(fx_at("hit-spark", tx, ty - 14.0, m.frame + FLY, false));
                                } else {
                                    fx.push(Effect { name: "bolt", x: tx, y: ty, start: m.frame, link: Some((u, t)), flip: false, from: None });
                                    fx.push(fx_at("zap-hit", tx, ty - 20.0, m.frame, false));
                                }
                            }
                            Cast::PointBlank => fx.push(fx_at("muzzle-shotgun", ux, uy - 6.0, m.frame, left)),
                            // the Devourer's jaws close on the fallen: blood where it lay
                            Cast::Devour => fx.push(fx_at("devour-splash", tx, ty, m.frame + 2, false)),
                            // its third stage: one blow, and all the small ones round it are under its feet
                            Cast::Trample => fx.push(fx_at("ground-slam", ux, uy, m.frame, false)),
                            // the Forge breathes its heat on the one it sets alight
                            Cast::Kindle => fx.push(fx_at("fire-breath", ux, uy - 34.0, m.frame, left)),
                            // the hurled one comes down: the ground bursts where it lands
                            Cast::Hurl => fx.push(fx_at("ground-slam", tx, ty, m.frame + FLY, false)),
                            // a part torn off the fallen, bolted on the golem with a spark
                            Cast::Trophy => {
                                fx.push(Effect { name: "bolt", x: tx, y: ty, start: m.frame, link: Some((u, t)), flip: false, from: None });
                                fx.push(fx_at("hit-spark", tx, ty - 20.0, m.frame, false));
                                nums.push(Number { text: t_("num.trophy"), style: NumStyle::Status, x: tx, y: ty, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
                            }
                            // the sickness passes on: a green puff on the newly infected
                            Cast::Contagion => fx.push(fx_at("acid-splash", tx, ty - 6.0, m.frame, false)),
                            // a wall rises: a mason's with a thud of its own, the blueprint's all at once, with dust
                            Cast::Lay if self.units[u].name == "Каменщик" => fx.push(fx_at("ground-slam", tx, ty, m.frame, false)),
                            Cast::Lay => fx.push(fx_at("hit-spark", tx, ty - 10.0, m.frame, false)),
                        }
                    }
                    Event::Arc { a, b } => {
                        netted.push(a);
                        netted.push(b);
                        // the Inventor's hits after the net are its jolts (he is one of its ends or not)
                        if let Some(inv) = self.units.iter().position(|u| u.name == "Изобретатель" && u.side == self.units[a].side) {
                            netted.push(inv);
                        }
                        let (x, y) = at(b);
                        fx.push(Effect { name: "tesla", x, y, start: m.frame, link: Some((a, b)), flip: false, from: None });
                    }
                    Event::Swallow { u, t } => {
                        let (x, y) = Self::spot(self.rounds[r].before[t].x, self.rounds[r].before[t].y, self.units[t].fp);
                        let _ = u;
                        fx.push(Effect { name: "devour-splash", x, y, start: m.frame, link: None, flip: false, from: None });
                        nums.push(Number { text: t_("num.swallowed"), style: NumStyle::Status, x, y, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
                    }
                    Event::Burst { t } => {
                        let (x, y) = at(t);
                        fx.push(Effect { name: "devour-splash", x, y, start: m.frame, link: None, flip: false, from: None });
                    }
                    Event::Morph { from, .. } => {
                        let st = self.rounds[r].before[from];
                        let (x, y) = Self::spot(st.x, st.y, self.units[from].fp);
                        fx.push(Effect { name: "acid-splash", x, y: y - 4.0, start: m.frame, link: None, flip: false, from: None });
                    }
                    // lightning from the sky, its number on the one it struck
                    Event::Strike { t } => {
                        let (x, y) = at(t);
                        fx.push(Effect { name: "sky", x, y, start: m.frame, link: None, flip: false, from: None });
                        fx.push(Effect { name: "zap-hit", x, y: y - 14.0, start: m.frame + 1, link: None, flip: false, from: None });
                    }
                    Event::Nature { t, dmg } => {
                        let (x, y) = at(t);
                        nums.push(Number { text: format!("-{dmg}"), style: NumStyle::Hurt, x, y, start: m.frame, t, k: 0, value: dmg, end: i32::MAX });
                    }
                    // the earth splits along a column: dust bursting up all along it
                    Event::Rift { x } => {
                        for row in (0..sim::battle::H).step_by(4) {
                            let (sx, sy) = Self::spot(x, row, 1);
                            fx.push(Effect { name: "ground-slam", x: sx, y: sy, start: m.frame + row / 4, link: None, flip: false, from: None });
                        }
                    }
                    // Кегли: a thump where they crash, and a word for it
                    Event::Bump { b, .. } => {
                        let (x, y) = at(b);
                        fx.push(Effect { name: "hit-spark", x, y: y - 10.0, start: m.frame, link: None, flip: false, from: None });
                        nums.push(Number { text: t_("num.bump"), style: NumStyle::Status, x, y, start: m.frame, t: b, k: 0, value: 0, end: i32::MAX });
                    }
                    Event::Surge { t } => {
                        let (x, y) = at(t);
                        fx.push(Effect { name: "zap-hit", x, y: y - 6.0, start: m.frame, link: None, flip: false, from: None });
                    }
                    // a boss's second phase: a burst round it and a word for it
                    Event::Phase { u } => {
                        let (x, y) = at(u);
                        fx.push(Effect { name: "mana-burst", x, y: y - 20.0, start: m.frame, link: None, flip: false, from: None });
                        fx.push(Effect { name: "ground-slam", x, y, start: m.frame + 2, link: None, flip: false, from: None });
                        nums.push(Number { text: t_("num.phase"), style: NumStyle::Status, x, y, start: m.frame, t: u, k: 0, value: 0, end: i32::MAX });
                    }
                    Event::Defy { t } => {
                        let (x, y) = at(t);
                        nums.push(Number { text: t_("num.defy"), style: NumStyle::Status, x, y, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
                    }
                    // Песочные часы: its time turns back
                    Event::Rewind { t } => {
                        let (x, y) = at(t);
                        fx.push(Effect { name: "mana-burst", x, y: y - 10.0, start: m.frame, link: None, flip: false, from: None });
                        nums.push(Number { text: t_("num.rewind"), style: NumStyle::Status, x, y, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
                    }
                    // Кокон: the Plague pupates
                    Event::Cocoon { t } => {
                        let (x, y) = at(t);
                        fx.push(Effect { name: "acid-splash", x, y: y - 6.0, start: m.frame, link: None, flip: false, from: None });
                        nums.push(Number { text: t_("num.cocoon"), style: NumStyle::Status, x, y, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
                    }
                    // Знамя: the banner rises over the one that picked it up
                    Event::Banner { u } => {
                        let (x, y) = at(u);
                        fx.push(Effect { name: "mana-burst", x, y: y - 20.0, start: m.frame, link: None, flip: false, from: None });
                        nums.push(Number {
                            text: t_("num.banner"),
                            style: NumStyle::Status,
                            x,
                            y,
                            start: m.frame,
                            t: u,
                            k: 0,
                            value: 0,
                            end: i32::MAX,
                        });
                    }
                    // Колокол: a ring of sound round the leader
                    Event::Bell { u } => {
                        let (x, y) = at(u);
                        fx.push(Effect { name: "ground-slam", x, y, start: m.frame, link: None, flip: false, from: None });
                        nums.push(Number {
                            text: t_("num.bell"),
                            style: NumStyle::Status,
                            x,
                            y,
                            start: m.frame,
                            t: u,
                            k: 0,
                            value: 0,
                            end: i32::MAX,
                        });
                    }
                    Event::Swap { a, b, ax, ay, bx, by } => {
                        for (id, ox, oy) in [(a, ax, ay), (b, bx, by)] {
                            let (x, y) = Self::spot(ox, oy, self.units[id].fp);
                            fx.push(Effect { name: "mana-burst", x, y, start: m.frame, link: None, flip: false, from: None });
                            let (nx, ny) = at(id);
                            fx.push(Effect { name: "mana-burst", x: nx, y: ny, start: m.frame + 1, link: None, flip: false, from: None });
                        }
                        let (x, y) = at(b);
                        nums.push(Number { text: t_("num.swapped"), style: NumStyle::Status, x, y, start: m.frame, t: b, k: 0, value: 0, end: i32::MAX });
                    }
                    Event::Heal { t, amount, .. } => {
                        let (x, y) = at(t);
                        nums.push(Number { text: format!("+{amount}"), style: NumStyle::Heal, x, y, start: m.frame, t, k: 0, value: amount, end: i32::MAX });
                        fx.push(Effect { name: "heal", x, y, start: m.frame, link: None, flip: false, from: None });
                    }
                    Event::Poison { t, dmg } | Event::Burn { t, dmg } => {
                        let (x, y) = at(t);
                        nums.push(Number { text: format!("{dmg}"), style: NumStyle::Poison, x, y, start: m.frame, t, k: 0, value: dmg, end: i32::MAX });
                    }
                    Event::Absorbed { t } => {
                        let (x, y) = at(t);
                        if let Some(j) = nums.iter().rposition(|n: &Number| n.t == t && n.style == NumStyle::Miss && m.frame - n.start < 14) {
                            nums[j].end = m.frame;
                        }
                        nums.push(Number { text: t_("num.miss"), style: NumStyle::Miss, x, y, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
                    }
                    Event::Stun { t } => {
                        let (x, y) = at(t);
                        nums.push(Number { text: t_("num.stun"), style: NumStyle::Status, x, y, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
                    }
                    _ => {}
                }
            }
        }
        // numbers over one unit close in time take the next place up
        for i in 0..nums.len() {
            let busy = (0..i)
                .filter(|&j| nums[j].t == nums[i].t && nums[i].start - nums[j].start < 14 && nums[j].end > nums[i].start)
                .map(|j| nums[j].k)
                .collect::<Vec<_>>();
            nums[i].k = (0..).find(|k| !busy.contains(k)).unwrap_or(0);
        }
        (nums, fx)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sim::data;

    /// A swarm without Мимикрия takes nothing up from the machines it breaks: no weapon under its count, no crackle in
    /// its bites; with it, it does.
    #[test]
    fn mimicry_only_for_a_swarm_that_has_it() {
        let forges: Vec<Template> = (0..4).map(|_| data::gorn()).collect();
        let plain = record_of(5, &forges, &data::start_matka());
        assert!(plain.rounds.iter().all(|r| r.mimic == [0, 0]), "a swarm without Мимикрия took a weapon up");
        let mut mimics = data::start_matka();
        for t in &mut mimics {
            if !t.has(Trait::Leader) {
                t.traits.push(Trait::Mimic);
            }
        }
        let with = record_of(5, &forges, &mimics);
        assert!(with.rounds.iter().any(|r| r.mimic[1] != 0), "the swarm with Мимикрия took nothing up from the forges");
    }

    /// The Forge's flame is shown when its heat sets someone alight, once each time — not on its every punch.
    #[test]
    fn the_forge_breathes_when_it_kindles() {
        let forges: Vec<Template> = (0..3).map(|_| data::gorn()).collect();
        let rec = record_of(9, &forges, &data::start_matka());
        let kindles = rec.rounds.iter().flat_map(|r| r.events.iter()).filter(|e| matches!(e, Event::Cast { kind: sim::Cast::Kindle, .. })).count();
        let punches = rec.rounds.iter().flat_map(|r| r.events.iter()).filter(|e| matches!(e, Event::Hit { a, .. } if rec.units[*a].name == "Горн")).count();
        let (_, fx) = rec.sparks();
        let breaths = fx.iter().filter(|e| e.name == "fire-breath").count();
        assert!(kindles > 0 && punches > kindles, "kindles {kindles}, punches {punches}");
        assert_eq!(breaths, kindles, "a breath for each kindling, not for each of {punches} punches");
    }
}
