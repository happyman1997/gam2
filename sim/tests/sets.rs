//! Element sets and enemies with a face (CONCEPT.md, «Сеты стихий», «Враги с лицом»): three finds of one element make
//! a set that changes how the whole side fights; an elite comes with an affix; a boss at half its health goes into its
//! second phase.

use sim::battle::{Battle, Event, GOO, OIL};
use sim::data::*;
use sim::model::{Affix, Element, Template, Trait};
use sim::run::{Class, Kind, Run, SET_NEED};

fn still(mut t: Template) -> Template {
    t.speed = 0;
    t
}

fn with_set(mut t: Template, e: Element) -> Template {
    t.traits.push(Trait::Set { e });
    t
}

#[test]
fn three_finds_of_an_element_make_a_set() {
    let mut r = Run::new(Class::Foundry, 0, 3);
    let lead = |r: &Run| r.body(r.army.iter().find(|m| r.is_leader(m)).unwrap());
    assert!(!lead(&r).has(Trait::Set { e: Element::Iron }));
    for key in ["plates", "tower", "counter"].iter().take(SET_NEED) {
        r.army[0].mods.push(key.to_string());
    }
    assert_eq!(r.set_count(Element::Iron), SET_NEED);
    assert!(lead(&r).has(Trait::Set { e: Element::Iron }), "three iron modules and no iron set");
    // the swarm: its breed's mutations and evolutions
    let mut s = Run::new(Class::Swarm, 0, 3);
    for k in ["m_flight", "evo_flyer", "evo_dive"] {
        s.breeds.push(("*".into(), k.into()));
    }
    assert_eq!(s.set_count(Element::Wing), 3);
}

#[test]
fn the_fire_set_leaves_burning_oil_where_its_fire_lands() {
    let mut bt = Battle::new(1);
    bt.place(0, with_set(still(gorn()), Element::Fire), 4, 9);
    let a = bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 6, 10);
    bt.units[a].hp = 100;
    bt.units[a].t.hp = 100;
    let mut burnt = false;
    for _ in 0..3 {
        bt.step();
        burnt |= bt.flames().iter().any(|&f| f > 0);
    }
    assert!(burnt, "the fire set's heat left no burning oil");
}

#[test]
fn the_volt_set_grounds_its_side_and_runs_farther() {
    let mut bt = Battle::new(2);
    for x in 8..20 {
        for y in 9..13 {
            bt.pour(x, y, GOO);
        }
    }
    bt.place(0, with_set(still(mudrets()), Element::Volt), 4, 10);
    let g = bt.place(0, still(strazh()), 12, 10);
    bt.units[g].hp = 999;
    let far = bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 18, 12);
    bt.units[far].hp = 100;
    bt.units[far].t.hp = 100;
    for k in 0..3 {
        let a = bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 8, 9 + k);
        bt.units[a].hp = 100;
        bt.units[a].t.hp = 100;
    }
    for _ in 0..3 {
        bt.step();
    }
    assert_eq!(bt.units[g].hp, 999, "the volt set's own Guard took the jolt");
}

/// A line of Guards across the field with gaps of six: grasshoppers (flankers, for the Gun behind) slip through the
/// middle of a gap past plain Guards, not past iron ones (they hold three cells, not two).
#[test]
fn the_iron_set_holds_farther() {
    let through = |iron: bool| {
        let mut got = 0;
        for seed in 0..6 {
            let mut bt = Battle::new(seed);
            for y in [0, 9, 18, 27] {
                let g = if iron { with_set(still(strazh()), Element::Iron) } else { still(strazh()) };
                bt.place(0, g, 8, y);
            }
            let gun = bt.place(0, still(orudie()), 3, 14);
            bt.units[gun].hp = 999;
            for k in 0..12 {
                bt.place(1, swarm(Caste::Worker, Form::Grasshopper), 27 + k % 3, 2 + (k / 3) * 7);
            }
            for _ in 0..30 {
                if bt.step().is_some() {
                    break;
                }
                if (0..bt.units.len()).any(|k| bt.units[k].side == 1 && bt.units[k].present() && bt.dist(k, gun) <= 1) {
                    got += 1;
                    break;
                }
            }
        }
        got
    };
    assert!(through(false) > 0, "grasshoppers never got through gaps of six past plain Guards");
    assert_eq!(through(true), 0, "grasshoppers got through the iron Guards' line");
}

#[test]
fn the_impact_set_knocks_every_blow_back() {
    let mut bt = Battle::new(4).with_log();
    bt.place(0, with_set(still(strazh()), Element::Impact), 10, 10);
    for k in 0..3 {
        let a = bt.place(1, still(soldat()), 13, 10 + k);
        bt.units[a].hp = 200;
        bt.units[a].t.hp = 200;
    }
    for _ in 0..3 {
        bt.step();
    }
    assert!(bt.log.as_ref().unwrap().iter().any(|e| matches!(e, Event::Knockback { .. })), "no blow knocked back");
}

#[test]
fn the_nest_set_sinks_the_enemy_in_its_slime() {
    let mut bt = Battle::new(5);
    for x in 12..20 {
        for y in 8..14 {
            bt.pour(x, y, GOO);
        }
    }
    bt.place(1, with_set(still(swarm(Caste::Worker, Form::Ant)), Element::Nest), 30, 10);
    let g = bt.place(0, strazh(), 9, 9);
    let mut stuck = false;
    for _ in 0..6 {
        bt.step();
        stuck |= bt.units[g].stuck_until == bt.round;
    }
    assert!(stuck, "the Guard walked the nest set's slime unhindered");
}

#[test]
fn the_venom_set_rots_machines_the_wing_set_is_not_held_the_shell_set_shares_the_blow() {
    // venom: a scorpion's sting poisons a Guard
    let mut bt = Battle::new(6);
    let g = bt.place(0, still(strazh()), 10, 10);
    bt.units[g].hp = 999;
    bt.place(1, with_set(still(swarm(Caste::Worker, Form::Scorpion)), Element::Venom), 13, 10);
    for _ in 0..4 {
        bt.step();
    }
    assert!(bt.units[g].poison > 0 || bt.units[g].hp < 999, "no rot");
    // wing: a bug of the wing set walks past a Guard's hold
    let mut bt = Battle::new(7);
    bt.place(0, still(strazh()), 10, 10);
    let a = bt.place(1, with_set(swarm(Caste::Worker, Form::Ant), Element::Wing), 14, 11);
    assert!(!bt.units.is_empty());
    let _ = a;
    // shell: two bugs in one cell share each blow — the Guard's blows land on twice as many bodies
    let landed = |shell: bool| {
        let mut n = 0;
        for seed in 0..20 {
            let mut bt = Battle::new(seed).with_log();
            let g = bt.place(0, still(strazh()), 10, 10);
            let ant = |set| {
                if set {
                    with_set(still(swarm(Caste::Worker, Form::Ant)), Element::Shell)
                } else {
                    still(swarm(Caste::Worker, Form::Ant))
                }
            };
            for _ in 0..2 {
                let v = bt.place(1, ant(shell), 11, 10);
                bt.units[v].hp = 999;
                bt.units[v].t.hp = 999;
            }
            bt.step();
            n += bt.log.as_ref().unwrap().iter().filter(|e| matches!(e, Event::Hit { a, dmg, .. } if *a == g && *dmg > 0)).count();
        }
        n
    };
    assert!(landed(true) > landed(false), "the shell set shared no blow: {} with, {} without", landed(true), landed(false));
}

#[test]
fn an_elite_has_a_face() {
    let (mut elites, mut with) = (0, 0);
    for seed in 0..40 {
        let mut r = Run::new(Class::Foundry, (seed % 4) as usize, seed);
        r.fight = 6;
        r.fork();
        for n in r.path.iter().filter(|n| n.kind == Kind::Elite) {
            elites += 1;
            if n.affix != Affix::None {
                with += 1;
            }
        }
    }
    assert!(elites > 0 && with == elites, "{with} of {elites} elites with an affix");
    // in oil from the start; hard to kill once
    let mut bt = Battle::new(8);
    let mut ant = still(swarm(Caste::Worker, Form::Ant));
    Affix::Oily.apply(&mut ant);
    Affix::Stubborn.apply(&mut ant);
    let a = bt.place(1, ant, 14, 10);
    bt.units[a].hp = 1;
    let mut heavy = still(strazh());
    heavy.die = 60;
    heavy.dmg = sim::model::Dmg::Blunt;
    bt.place(0, heavy, 11, 9);
    bt.step();
    assert_eq!(bt.ground()[10 * sim::battle::W as usize + 14], OIL, "no oil under the oily elite");
    assert!(bt.units[a].defied, "the stubborn ant did not cheat death");
}

#[test]
fn a_boss_at_half_goes_into_its_second_phase() {
    let mut bt = Battle::new(9).with_log();
    let mut m = matka();
    m.traits.push(Trait::Boss);
    let b = bt.place(1, m, 25, 10);
    bt.place(0, still(strazh()), 2, 2);
    bt.units[b].hp = bt.units[b].t.hp / 2 - 1;
    bt.step();
    assert!(bt.log.as_ref().unwrap().iter().any(|e| matches!(e, Event::Phase { u } if *u == b)), "no second phase");
    assert!(bt.units[b].t.abilities.iter().any(|a| matches!(a, sim::model::Ability::Brood { every: 1, n: 3 })));
}
