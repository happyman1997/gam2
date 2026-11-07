use sim::battle::{fight, Battle};
use sim::data::*;
use sim::model::Dmg;
use sim::Event;

#[test]
fn same_seed_same_battle() {
    let a = vec![molot(), orudie()];
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
    bt.place(0, molot(), 5, 5);
    for _ in 0..4 {
        bt.place(1, rabochaya(), 7, 5);
    }
    let _ = bt.run();
    let log = bt.log.unwrap();
    // first blow of Молот (unit 0) in the battle hits all four workers in the cell
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
