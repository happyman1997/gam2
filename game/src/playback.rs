//! The battle as the game shows it: the simulation runs it round by round (sim: two armies and a seed in, events
//! out), and the playback turns each round into frames — first everyone walks, then the blows land one after
//! another, each with its effect and its number; the killed lie where they fell.

use sim::data::{start_izobretatel, start_pozhiratel};
use sim::model::Trait;
use sim::{Battle, Event, Outcome};

pub const FR: i32 = 30; // frames a round takes at ×1 (24 fps)
pub const MOVE: i32 = 10; // of them, walking
pub const CW: f32 = 50.0;
pub const CH: f32 = 34.0;
pub const X0: f32 = 30.0;
pub const Y0: f32 = 46.0;

#[derive(Clone)]
pub struct UnitInfo {
    pub name: String,
    pub side: u8,
    pub fp: i32,
    pub max_hp: i32,
    pub leader: bool,
}

#[derive(Clone, Copy, Default)]
pub struct State {
    pub x: i32,
    pub y: i32,
    pub present: bool,
    pub alive: bool,
    pub hp: i32,
    pub growth: u32,
}

pub struct Round {
    pub before: Vec<State>,
    pub after: Vec<State>,
    pub events: Vec<Event>,
}

pub struct Record {
    pub units: Vec<UnitInfo>,
    pub rounds: Vec<Round>,
    pub outcome: Outcome,
    pub seed: u64,
}

fn states(bt: &Battle) -> Vec<State> {
    bt.units
        .iter()
        .map(|u| State { x: u.x, y: u.y, present: u.on_field, alive: u.alive, hp: u.hp, growth: u.growth })
        .collect()
}

fn infos(bt: &Battle) -> Vec<UnitInfo> {
    bt.units
        .iter()
        .map(|u| UnitInfo {
            name: u.t.name.to_string(),
            side: u.side,
            fp: u.fp(),
            max_hp: u.t.hp,
            // the Foundry's human leaders don't carry the Leader trait in the simulation yet; the game knows them
            leader: u.t.has(Trait::Leader) || matches!(u.t.name.as_ref(), "Изобретатель" | "Маньяк" | "Зодчий" | "Отец колосса"),
        })
        .collect()
}

/// The demo's battle: the Inventor's start (left) against the Devourer's (right).
pub fn record(seed: u64) -> Record {
    let mut bt = Battle::new(seed).with_log();
    bt.add_armies(&start_izobretatel(), &start_pozhiratel());
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
        rounds.push(Round { before, after, events });
        if let Some(o) = done {
            break o;
        }
    };
    Record { units: infos(&bt), rounds, outcome, seed }
}

/// What a frame shows of one unit.
pub struct Shown {
    pub id: usize,
    pub x: f32,
    pub y: f32,
    pub pose: Pose,
}

#[derive(Clone, Copy, PartialEq)]
pub enum Pose {
    Idle,
    Attack,
    Dead,
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
}

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
            let born_at = ms.iter().find(|m| matches!(m.ev, Event::Summon { u } if u == id)).map(|m| m.frame);
            if !b.alive && !a.alive {
                let (x, y) = Self::spot(a.x, a.y, info.fp); // killed earlier: it lies where it fell
                out.push(Shown { id, x, y, pose: Pose::Dead });
                continue;
            }
            if !b.present && !a.present {
                continue; // fled off the field
            }
            if let Some(bf) = born_at {
                if f < bf {
                    continue;
                }
            }
            let (bx, by) = Self::spot(b.x, b.y, info.fp);
            let (ax, ay) = Self::spot(a.x, a.y, info.fp);
            let (x, y) = (bx + (ax - bx) * e, by + (ay - by) * e);
            let dead = killed_at.map(|k| f >= k).unwrap_or(false) || (!a.alive && killed_at.is_none() && ph >= MOVE);
            if !a.present && !dead && ph >= MOVE {
                continue;
            }
            let attacking = ms.iter().any(|m| matches!(m.ev, Event::Hit { a: at, .. } if at == id) && (f - m.frame).abs() <= 4);
            let pose = if dead { Pose::Dead } else if attacking { Pose::Attack } else { Pose::Idle };
            out.push(Shown { id, x, y, pose });
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
                u.side == 0 && round.before[i].alive && (round.before[i].x, round.before[i].y) != (round.after[i].x, round.after[i].y)
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
                        let name = if dmg <= 0 {
                            "miss"
                        } else {
                            match att.name.as_str() {
                                "Мудрец" | "Изобретатель" => "zap",
                                "Орудие" => {
                                    if last_volley.map(|(v, fr)| v == a && (m.frame - fr) < 6).unwrap_or(false) {
                                        continue;
                                    }
                                    last_volley = Some((a, m.frame));
                                    "blast"
                                }
                                _ if att.side == 1 => "bite",
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
                        let name = if self.units[t].side == 1 { "squish" } else { "break" };
                        out.push(Cue { frame: m.frame, name, gain: 0.0, x: at(t) });
                        if self.units[t].side == 1 {
                            out.push(Cue { frame: m.frame + 2, name: "death_rattle", gain: 0.0, x: at(t) });
                        }
                    }
                    Event::Heal { t, .. } => out.push(Cue { frame: m.frame, name: "heal", gain: 0.0, x: at(t) }),
                    Event::Absorbed { t } => out.push(Cue { frame: m.frame, name: "miss", gain: 0.0, x: at(t) }),
                    _ => {}
                }
            }
        }
        let end = if self.outcome.winner == Some(1) { "win" } else { "lose" };
        out.push(Cue { frame: self.frames() + 2, name: end, gain: 0.0, x: 480.0 });
        out.sort_by_key(|c| c.frame);
        out
    }

    /// The numbers and effects of the whole battle, each with the frame it starts on.
    pub fn sparks(&self) -> (Vec<Number>, Vec<Effect>) {
        let mut nums = vec![];
        let mut fx = vec![];
        for r in 0..self.rounds.len() {
            let after = &self.rounds[r].after;
            let mut last_volley: Option<(usize, i32)> = None;
            for m in self.moments(r) {
                let at = |id: usize| {
                    let s = after[id];
                    Self::spot(s.x, s.y, self.units[id].fp)
                };
                match m.ev {
                    Event::Hit { a, t, dmg } => {
                        let (x, y) = at(t);
                        let att = &self.units[a];
                        let swarm_hits = att.side == 1;
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
                        let text = match style {
                            NumStyle::Miss => "мимо".to_string(),
                            NumStyle::Crit => format!("{value}!"),
                            NumStyle::Hurt => format!("-{value}"),
                            _ => format!("{value}"),
                        };
                        nums.push(Number { text, style, x, y, start: m.frame, t, k: 0, value, end: i32::MAX });
                        let name: &'static str = match att.name.as_str() {
                            "Мудрец" | "Изобретатель" => "zap-hit",
                            "Орудие" => {
                                // a volley: one blast over the cell for all the hits it makes at once
                                if last_volley.map(|(v, fr)| v == a && (m.frame - fr) < 6).unwrap_or(false) {
                                    continue;
                                }
                                last_volley = Some((a, m.frame));
                                "small-explosion"
                            }
                            _ => "hit-spark",
                        };
                        fx.push(Effect { name, x, y: if name == "hit-spark" { y - 14.0 } else { y }, start: m.frame });
                    }
                    Event::Heal { t, amount, .. } => {
                        let (x, y) = at(t);
                        nums.push(Number { text: format!("+{amount}"), style: NumStyle::Heal, x, y, start: m.frame, t, k: 0, value: amount, end: i32::MAX });
                        fx.push(Effect { name: "heal", x, y, start: m.frame });
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
                        nums.push(Number { text: "мимо".into(), style: NumStyle::Miss, x, y, start: m.frame, t, k: 0, value: 0, end: i32::MAX });
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
