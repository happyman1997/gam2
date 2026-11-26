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

#[test]
fn spit_glues_and_poisons_but_not_machines() {
    // a spitter three cells from a worker and from a Guard: on round 2 it spits at one of them
    let mut bt = Battle::new(5).with_log();
    let sp = bt.place(1, swarm(Caste::Worker, Form::Spitter), 12, 5);
    let w = bt.place(0, rabochaya(), 9, 5);
    for _ in 0..2 {
        bt.step();
    }
    let log = bt.log.clone().unwrap();
    let glued = log.iter().find_map(|e| if let Event::Glue { t } = e { Some(*t) } else { None });
    assert_eq!(glued, Some(w), "the spit lands on the worker within range");
    let (x0, y0) = (bt.units[w].x, bt.units[w].y);
    bt.step(); // round 3: glued — it cannot walk toward the spider
    assert_eq!((bt.units[w].x, bt.units[w].y), (x0, y0));
    assert!(bt.units[w].poison > 0 || bt.units[w].hp < bt.units[w].t.hp, "the poison takes hold");
    let _ = sp;
    // a machine: glued all the same, no poison
    let mut bt = Battle::new(5).with_log();
    bt.place(1, swarm(Caste::Worker, Form::Spitter), 14, 5);
    let g = bt.place(0, strazh(), 9, 4);
    for _ in 0..2 {
        bt.step();
    }
    let log = bt.log.clone().unwrap();
    assert!(log.iter().any(|e| matches!(e, Event::Glue { t } if *t == g)), "the glue holds a machine too");
    assert_eq!(bt.units[g].poison, 0, "poison does nothing to a machine");
}

/// Flanking: a crowd bigger than the enemy's front can hold goes round its flanks to its back (a blow there is no
/// harder than any other: the back blow is gone) — before, the crowd queued up in front.
/// Удержание: a line of Guards standing fast across the whole field, the gaps between them no wider than four cells,
/// keeps a crowd of the swarm off the Gun behind it — the crowd comes up to the Guards and fights them, none slips
/// between them, not even the flankers that run for the archers. Wasps are not held: they fly over the line to it.
#[test]
fn a_line_holds_the_crowd() {
    let still = |mut t: sim::model::Template| {
        t.speed = 0;
        t
    };
    let mut wasps = 0;
    for form in [Form::Ant, Form::Grasshopper, Form::Wasp] {
        for seed in 0..10 {
            let mut bt = Battle::new(seed);
            for y in [0, 7, 14, 21, 27] {
                bt.place(0, still(strazh()), 8, y);
            }
            let gun = bt.place(0, still(orudie()), 3, 14);
            for k in 0..24 {
                bt.place(1, swarm(Caste::Worker, form), 26 + k % 4, 3 + (k / 4) * 4);
            }
            for _ in 0..40 {
                if bt.step().is_some() {
                    break;
                }
                let at = (0..bt.units.len()).any(|k| bt.units[k].side == 1 && bt.units[k].present() && bt.dist(k, gun) <= 1);
                if form == Form::Wasp {
                    if at {
                        wasps += 1;
                        break;
                    }
                } else {
                    assert!(!at, "{:?} got through the line to the Gun (seed {seed}, round {})", form, bt.round);
                }
            }
        }
    }
    assert!(wasps >= 5, "wasps flew over the line to the Gun in only {wasps} of 10 battles");
}

/// A crowd still surrounds a lone Guard: Удержание keeps it from slipping past him, not from coming round him from
/// afar — those that come up later take the free places at his back.
#[test]
fn a_crowd_still_gets_round_a_lone_guard() {
    let (mut reached, mut battles) = (0, 0);
    for seed in 0..20 {
        let mut bt = Battle::new(seed);
        bt.add_armies(&many(soldat(), 24), &[strazh()]);
        let g = bt.units.iter().position(|u| u.side == 1).unwrap();
        let mut back = false;
        loop {
            let done = bt.step();
            // one of the crowd beside the Guard on its own army's side (the right: the far side faces left) — the
            // round that ends the battle too: the crowd often gets round just as the Guard falls
            let (gx, gf) = (bt.units[g].x, bt.units[g].fp());
            back |= (0..bt.units.len()).any(|k| bt.units[k].side == 0 && bt.units[k].present() && bt.dist(k, g) <= 1 && bt.units[k].x >= gx + gf);
            if done.is_some() {
                break;
            }
        }
        battles += 1;
        reached += back as i32;
    }
    assert!(reached * 2 >= battles, "the back reached in only {reached} of {battles} battles");
}

/// The field holds hundreds: 600 of the swarm and 60 golems all stand on it, each in its own side's zone; an army of
/// the usual size stands as it always did — in a block of 6×14 in the middle of the field's height, at the front of
/// its zone — and a big one plays to its end.
#[test]
fn the_field_holds_hundreds() {
    use sim::battle::{BLOCK, H, W, ZONE};
    let swarm: Vec<_> = (0..600).map(|k| swarm(if k % 6 == 5 { Caste::Soldier } else { Caste::Worker }, FORMS[k % FORMS.len()])).collect();
    let golems: Vec<_> = (0..60).map(|k| [strazh(), mudrets(), gorn(), orudie(), mekhanik()][k % 5].clone()).collect();
    let mut bt = Battle::new(5);
    bt.add_armies(&golems, &swarm);
    assert_eq!(bt.units.iter().filter(|u| u.side == 0).count(), 60, "golems left out");
    assert_eq!(bt.units.iter().filter(|u| u.side == 1).count(), 600, "the swarm left out");
    for u in &bt.units {
        let f = sim::battle::footprint(u.t.size);
        let zone = if u.side == 0 { 0..ZONE } else { W - ZONE..W };
        assert!(zone.contains(&u.x) && zone.contains(&(u.x + f - 1)), "{} out of its zone at {}", u.t.name, u.x);
    }
    let o = bt.run();
    assert!(o.rounds > 0);
    // the usual: small armies (two starts of the Foundry) in the old zone's block, middle rows, front columns; a start
    // of the swarm is a crowd now and takes a bigger block
    let mut bt = Battle::new(5);
    bt.add_armies(&start_zodchiy(), &start_manyak());
    let (top, bottom) = ((H - BLOCK.1) / 2, (H - BLOCK.1) / 2 + BLOCK.1);
    for u in &bt.units {
        let f = sim::battle::footprint(u.t.size);
        assert!(u.y >= top && u.y + f <= bottom, "{} at row {} — out of the block {top}..{bottom}", u.t.name, u.y);
        let depth = if u.side == 0 { ZONE - u.x } else { u.x + f - (W - ZONE) };
        assert!(depth <= BLOCK.0, "{} {depth} deep — out of the block", u.t.name);
    }
}
