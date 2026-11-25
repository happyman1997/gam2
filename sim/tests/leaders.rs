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

/// Живородящая: a body that dies lets out one larva of its side, and the larva does not carry it on — no flood.
#[test]
fn viviparous_lets_out_one_larva() {
    use sim::model::Trait;
    use sim::Event;
    let mut ants = many(rabochaya(), 8);
    for a in &mut ants {
        a.traits.push(Trait::Viviparous);
    }
    let mut bt = Battle::new(2).with_log();
    bt.add_armies(&ants, &start_otets());
    bt.run();
    let log = bt.log.as_ref().unwrap();
    let deaths = log.iter().filter(|e| matches!(e, Event::Kill { t } if bt.units[*t].side == 0 && bt.units[*t].t.has(Trait::Viviparous))).count();
    let larvae: Vec<usize> = log.iter().filter_map(|e| if let Event::Summon { u } = e { Some(*u) } else { None }).filter(|&u| bt.units[u].side == 0).collect();
    assert!(!larvae.is_empty(), "no larva from {deaths} viviparous deaths");
    assert!(larvae.len() <= deaths, "{} larvae from {deaths} deaths", larvae.len());
    assert!(larvae.iter().all(|&u| !bt.units[u].t.has(Trait::Viviparous)), "a larva viviparous too");
}

/// The Devourer is hungry at the start of a run: till its swarm has killed 30 enemies it starves from the 2nd round
/// without a kill, a fifth of its health a round; fed, from the 3rd round and a tenth.
#[test]
fn the_devourer_is_hungry_at_the_start() {
    use sim::model::Trait;
    use sim::run::{Class, Run};
    let mut r = Run::new(Class::Swarm, 2, 1);
    let lead = r.army.iter().position(|m| r.is_leader(m)).unwrap();
    let fed = sim::data::rules().devourer_fed;
    assert!(r.body(&r.army[lead]).traits.contains(&Trait::Hungry { left: fed }), "not hungry at the start");
    r.stats.kills = fed - 5;
    assert!(r.body(&r.army[lead]).traits.contains(&Trait::Hungry { left: 5 }));
    r.stats.kills = fed;
    let sated = r.body(&r.army[lead]);
    assert!(!sated.traits.iter().any(|t| matches!(t, Trait::Hungry { .. })), "still hungry when fed");
    // in battle, with no prey in reach: the hungry one loses health sooner and faster
    let hungry = r.army[lead].t.clone().with_trait(Trait::Hungry { left: 10 });
    let lost = |t: sim::model::Template| {
        let mut bt = sim::Battle::new(1);
        let d = bt.place(0, t, 2, 10);
        bt.units[d].glued_until = 99; // it stays where it is, far from the enemy
        bt.place(1, sim::data::strazh(), 33, 10);
        bt.place(0, sim::data::rabochaya(), 2, 20);
        for _ in 0..4 {
            bt.step();
        }
        bt.units[d].t.hp - bt.units[d].hp
    };
    let (h, s) = (lost(hungry), lost(sated));
    assert!(h > s && s > 0, "hungry lost {h}, fed lost {s}");
}
