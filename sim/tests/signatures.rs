//! Each leader's own wild thing does what it says in a battle (CONCEPT.md, «Лидеры»): the Colossus hurls enemies, the
//! Inventor's net shocks whoever stands between his golems, the Maniac bolts trophies on, the Architect's walls rise and
//! his army waits behind them, the Mother's larvae turn into the form that kills, the Hive Mind swaps a shooter into the
//! swarm, the Devourer swallows whole, the Plague's infection spreads on its own.

use sim::battle::{Cast, Event};
use sim::data::*;
use sim::model::{Template, Trait};
use sim::Battle;

/// Battles of `a` (left) against `b` (right) over `seeds`, with their logs.
fn battles(a: &[Template], b: &[Template], seeds: u64) -> Vec<Battle> {
    (0..seeds)
        .map(|seed| {
            let mut bt = Battle::new(seed).with_log();
            bt.add_armies(a, b);
            bt.run();
            bt
        })
        .collect()
}

fn log_has(bt: &Battle, f: impl Fn(&Event) -> bool) -> bool {
    bt.log.as_ref().unwrap().iter().any(f)
}

#[test]
fn the_colossus_hurls_them_into_their_own() {
    let mut thrown = 0;
    for bt in battles(&start_otets(), &army("start_matka"), 10) {
        for e in bt.log.as_ref().unwrap() {
            if let Event::Thrown { u, t, x, y, .. } = *e {
                thrown += 1;
                // it lands among its own, away from the Colossus
                let (cx, cy) = (bt.units[u].x, bt.units[u].y);
                assert!(sim::battle::rect_dist(x, y, bt.units[t].fp(), cx, cy, bt.units[u].fp()) >= 1);
            }
        }
    }
    assert!(thrown >= 8, "thrown only {thrown} times in 10 battles");
}

#[test]
fn the_net_shocks_who_stands_between_and_dies_with_the_inventor() {
    let still = |mut t: Template| {
        t.speed = 0;
        t
    };
    let mut bt = Battle::new(1).with_log();
    let inv = bt.place(0, still(izobretatel()), 2, 10);
    bt.place(0, still(strazh()), 8, 2);
    bt.place(0, still(strazh()), 8, 8);
    // an ant right between the two Guards (their middles are rows 3 and 9): on the line
    let ant = bt.place(1, swarm(Caste::Worker, Form::Ant), 9, 6);
    bt.units[ant].t.speed = 0;
    bt.units[ant].t.traits.retain(|t| *t != Trait::Staya);
    bt.step();
    assert!(log_has(&bt, |e| matches!(e, Event::Arc { .. })), "no lightning between the golems");
    assert!(bt.units[ant].hp < bt.units[ant].t.hp, "the ant between them took nothing");
    bt.units[inv].hp = 0;
    bt.units[inv].alive = false;
    let n = bt.log.as_ref().unwrap().len();
    bt.step();
    assert!(!bt.log.as_ref().unwrap()[n..].iter().any(|e| matches!(e, Event::Arc { .. })), "the net runs on without the Inventor");
}

#[test]
fn the_maniac_bolts_trophies_on() {
    let mut got = 0;
    for bt in battles(&start_manyak(), &army("start_matka"), 10) {
        if log_has(&bt, |e| matches!(e, Event::Cast { kind: Cast::Trophy, .. })) {
            got += 1;
        }
    }
    assert!(got >= 8, "trophies in only {got} of 10 battles");
    // a wasp's wings make the golem fly
    let mut bt = Battle::new(3);
    // the Maniac under the Guard, the wasp beside the Guard — three cells from him
    let m = bt.place(0, manyak(), 6, 13);
    let g = bt.place(0, strazh(), 6, 10);
    let wasp = bt.place(1, swarm(Caste::Worker, Form::Wasp), 9, 10);
    bt.units[wasp].hp = 1;
    bt.place(1, swarm(Caste::Worker, Form::Ant), 30, 2);
    for _ in 0..4 {
        bt.step();
        if bt.units[g].t.has(Trait::Flyer) {
            break;
        }
    }
    let _ = m;
    assert!(!bt.units[wasp].alive && bt.units[g].t.has(Trait::Flyer), "the Guard did not take the wasp's wings");
}

#[test]
fn the_architects_walls_rise_and_his_army_waits_behind_them() {
    let mut bt = Battle::new(2).with_log();
    bt.add_armies(&start_zodchiy(), &army("start_matka"));
    let start: Vec<(i32, i32)> = bt.units.iter().filter(|u| u.side == 0).map(|u| (u.x, u.y)).collect();
    bt.step();
    let walls = bt.units.iter().filter(|u| u.side == 0 && u.t.has(Trait::Wall)).count();
    assert_eq!(walls, 8, "the blueprint's walls");
    // the enemy far off: no one of his has moved
    let moved = bt.units.iter().filter(|u| u.side == 0).take(start.len()).zip(&start).any(|(u, s)| (u.x, u.y) != *s);
    assert!(!moved, "the garrison walked out with the enemy far");
    // walls are no army: a side of walls alone has lost
    let mut lone = Battle::new(1);
    lone.place(0, unit("stena"), 5, 5);
    lone.place(1, swarm(Caste::Worker, Form::Ant), 20, 5);
    assert_eq!(lone.run().winner, Some(1));
    // masons lay more
    let laid = battles(&start_zodchiy(), &army("start_matka"), 6)
        .iter()
        .filter(|bt| log_has(bt, |e| matches!(e, Event::Cast { u, kind: Cast::Lay, .. } if bt.units[*u].t.name == "Каменщик")))
        .count();
    assert!(laid >= 3, "masons laid walls in only {laid} of 6 battles");
}

#[test]
fn the_mothers_larvae_turn_into_the_killers() {
    let mut morphs = 0;
    for bt in battles(&start_zodchiy(), &army("start_matka"), 10) {
        for e in bt.log.as_ref().unwrap() {
            if let Event::Morph { from, to } = *e {
                morphs += 1;
                assert_eq!(bt.units[from].t.name, "Личинка");
                assert_ne!(bt.units[to].t.name, "Личинка");
            }
        }
    }
    assert!(morphs >= 10, "only {morphs} larvae turned in 10 battles");
}

#[test]
fn the_hive_mind_swaps_a_shooter_into_the_swarm() {
    let mut swapped = 0;
    for bt in battles(&start_zodchiy(), &army("start_razum"), 10) {
        for e in bt.log.as_ref().unwrap() {
            if let Event::Swap { a, b, .. } = *e {
                swapped += 1;
                assert_eq!(bt.units[a].side, 1);
                assert_eq!(bt.units[b].side, 0);
            }
        }
    }
    assert!(swapped >= 5, "swapped only {swapped} times in 10 battles");
}

#[test]
fn the_devourer_swallows_whole_and_it_bursts_out() {
    let mut bt = Battle::new(4).with_log();
    let d = bt.place(1, pozhiratel(), 10, 10);
    let mason = bt.place(0, kamenshchik(), 9, 10);
    bt.units[mason].hp = 200;
    bt.units[mason].t.hp = 200;
    bt.place(0, strazh(), 2, 20);
    let mut inside = false;
    for _ in 0..3 {
        bt.step();
        inside |= bt.units[mason].inside == Some(d);
    }
    assert!(inside, "the mason was not swallowed");
    assert!(bt.units[mason].hp < 200, "not digested");
    // the Devourer falls with it inside: it bursts out
    if bt.units[mason].inside.is_some() {
        bt.units[d].hp = 1;
        for _ in 0..3 {
            bt.step();
            if !bt.units[d].alive {
                break;
            }
        }
        if !bt.units[d].alive && bt.units[mason].alive {
            assert!(bt.units[mason].present(), "it did not burst out");
            assert!(log_has(&bt, |e| matches!(e, Event::Burst { .. })));
        }
    }
}

#[test]
fn the_plague_spreads_on_its_own() {
    let mut bt = Battle::new(5).with_log();
    bt.place(1, kukushka(), 30, 10);
    let a = bt.place(0, strazh(), 5, 5);
    let b = bt.place(0, strazh(), 8, 5);
    bt.units[a].infected = Some(1);
    for u in [a, b] {
        bt.units[u].t.speed = 0;
    }
    for _ in 0..6 {
        bt.step();
    }
    assert_eq!(bt.units[b].infected, Some(1), "the infection did not pass to the Guard beside");
    assert!(log_has(&bt, |e| matches!(e, Event::Cast { kind: Cast::Contagion, .. })));
}
