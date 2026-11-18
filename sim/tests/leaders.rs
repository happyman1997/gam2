//! The Foundry leaders' own abilities do something in a battle: the Colossus's quake stuns, the Inventor's augments
//! make the modules near it a level stronger, the Maniac screws modules onto the golems beside it.

use sim::data::*;
use sim::model::Ability;
use sim::Battle;

fn count<F: Fn(&Battle) -> bool>(army: fn() -> Vec<sim::model::Template>, rounds: u32, seeds: u64, f: F) -> u64 {
    let mut n = 0;
    for seed in 0..seeds {
        let mut bt = Battle::new(seed);
        bt.add_armies(&army(), &swarm_start());
        for _ in 0..rounds {
            if bt.step().is_some() {
                break;
            }
            if f(&bt) {
                n += 1;
                break;
            }
        }
    }
    n
}

#[test]
fn the_quake_stuns() {
    let n = count(start_otets, 12, 40, |bt| bt.units.iter().any(|u| u.side == 1 && u.present() && u.stunned));
    assert!(n >= 20, "stunned in only {n} of 40 battles");
}

#[test]
fn augments_level_the_modules_up() {
    let base: Vec<Ability> = start_izobretatel().iter().flat_map(|t| t.abilities.clone()).collect();
    let n = count(start_izobretatel, 1, 20, |bt| {
        let now: Vec<Ability> = bt.units.iter().filter(|u| u.side == 0 && u.src.is_some()).flat_map(|u| u.t.abilities.clone()).collect();
        now != base
    });
    assert_eq!(n, 20, "modules levelled up in only {n} of 20 battles");
}

#[test]
fn the_maniac_screws_modules_on() {
    let start = |bt: &Battle| bt.units.iter().filter(|u| u.side == 0).map(|u| u.t.abilities.len() as u32 + u.plates).sum::<u32>();
    let before = {
        let mut bt = Battle::new(0);
        bt.add_armies(&start_manyak(), &swarm_start());
        start(&bt)
    };
    let n = count(start_manyak, 9, 40, |bt| start(bt) > before);
    assert!(n >= 10, "a module screwed on in only {n} of 40 battles");
}
