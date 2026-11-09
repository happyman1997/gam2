use sim::battle::{fight, Battle};
use sim::data::*;
use sim::model::{Dmg, Trait};
use sim::Event;

#[test]
fn same_seed_same_battle() {
    let a = vec![strazh(), mudrets()];
    let b = many(rabochaya(), 25);
    let run = |seed| {
        let mut bt = Battle::new(seed).with_log();
        bt.add_army(0, &a);
        bt.add_army(1, &b);
        let o = bt.run();
        (o.winner, o.rounds, bt.log.unwrap())
    };
    assert_eq!(run(7), run(7));
    assert_ne!(run(7).2, run(8).2);
}

#[test]
fn armor_and_resistance() {
    let mut bt = Battle::new(1);
    let s = bt.place(0, strazh(), 2, 2);
    // a worker's bite (pierce) against armor 4 and cast metal (holds pierce)
    assert_eq!(bt.calc(s, 4, Dmg::Pierce, false), 0);
    assert_eq!(bt.calc(s, 8, Dmg::Pierce, false), 2); // (8 - 4) / 2
    assert_eq!(bt.calc(s, 8, Dmg::Blunt, false), 4); // blunt is not held
    assert_eq!(bt.calc(s, 8, Dmg::Blunt, true), 6); // Пробивной: half armor
    // fire ignores armor, the Foundry takes a quarter, at least 1
    assert_eq!(bt.calc(s, 3, Dmg::Fire, false), 1);
    // metal conducts lightning
    assert_eq!(bt.calc(s, 10, Dmg::Shock, false), 9); // (10 - 4) * 1.5
}

#[test]
fn chitin_breaks_under_blunt() {
    let mut bt = Battle::new(1);
    let w = bt.place(1, soldat(), 10, 5);
    assert_eq!(bt.calc(w, 6, Dmg::Blunt, false), 10); // 6 * 2 - 2
    assert_eq!(bt.calc(w, 6, Dmg::Slash, false), 2); // (6 - 2) / 2
}

#[test]
fn trample_hits_the_whole_cell() {
    let mut bt = Battle::new(3).with_log();
    let mut g = gorn(); // a size-5 melee golem; without its fire, so only blows count
    g.traits.retain(|t| *t != Trait::ZharGorna);
    bt.place(0, g, 5, 5);
    for _ in 0..4 {
        bt.place(1, rabochaya(), 7, 5);
    }
    let _ = bt.run();
    let log = bt.log.unwrap();
    // the golem's first blow in the battle hits all four workers in the cell
    let first_round_hits = log
        .iter()
        .skip_while(|e| !matches!(e, Event::Hit { a: 0, .. }))
        .take_while(|e| !matches!(e, Event::Round(_)))
        .filter(|e| matches!(e, Event::Hit { a: 0, .. }))
        .count();
    assert_eq!(first_round_hits, 4);
}

#[test]
fn exhaustion_ends_every_battle() {
    // two sides that never attack still finish before the round limit
    let o = fight(&[mekhanik()], &[mekhanik()], 5);
    assert!(o.rounds < sim::battle::MAX_ROUNDS);
}

#[test]
fn caster_spell_and_short_circuit() {
    // the mage fires at range at full power; acid silences it for 2 rounds
    let mut bt = Battle::new(2).with_log();
    let m = bt.place(0, mudrets(), 2, 5);
    bt.place(1, zhuk(), 8, 5); // slow: after its 2 steps it is 3 cells off, in the spell's range of 4
    let _ = bt.step();
    let log = bt.log.clone().unwrap();
    assert!(log.iter().any(|e| matches!(e, Event::Hit { a, .. } if *a == m)), "the spell reaches 4 cells");
    let mut bt = Battle::new(2);
    let m = bt.place(0, mudrets(), 2, 5);
    bt.place(1, kislotnik(), 7, 5); // a spitter: it comes within its range of 2 and spits acid
    for _ in 0..3 {
        let _ = bt.step();
    }
    assert!(bt.units[m].silenced_until > 0, "acid shorts the windings");
}
