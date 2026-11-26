//! The field is no stage but a party to the fight: the fallen leave oil and slime, fire runs along the oil, lightning
//! through the slime, the knocked-back bowl the others over, and the sky and the earth have their say (a storm, an
//! earthquake, the night).

use sim::battle::{Battle, Cast, Event, GOO, OIL};
use sim::data::*;
use sim::model::{Dmg, Template, Weather};

fn still(mut t: Template) -> Template {
    t.speed = 0;
    t
}

fn log(bt: &Battle) -> &[Event] {
    bt.log.as_ref().unwrap()
}

#[test]
fn the_fallen_leave_oil_and_slime() {
    let mut bt = Battle::new(1);
    let g = bt.place(0, still(strazh()), 5, 5);
    let a = bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 20, 5);
    for u in [g, a] {
        bt.units[u].hp = 1;
    }
    // something kills them both: a heavy blow each from a neighbour
    let mut heavy = still(soldat());
    heavy.die = 60;
    bt.place(1, heavy.clone(), 8, 5);
    heavy.dmg = Dmg::Blunt;
    bt.place(0, still(heavy), 21, 5);
    bt.step();
    let ground = bt.ground();
    assert_eq!(ground[5 * sim::battle::W as usize + 5], OIL, "a broken Guard spills no oil");
    assert_eq!(ground[5 * sim::battle::W as usize + 20], GOO, "a fallen ant leaves no slime");
}

#[test]
fn fire_runs_along_the_oil() {
    let mut bt = Battle::new(2).with_log();
    for x in 6..14 {
        bt.pour(x, 10, OIL);
    }
    // a Forge's heat sets the ant at the oil's end alight; the fire runs to the ant at its other end
    bt.place(0, still(gorn()), 4, 9);
    let near = bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 6, 10);
    let far = bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 13, 10);
    for u in [near, far] {
        bt.units[u].hp = 100;
        bt.units[u].t.hp = 100;
    }
    let mut far_burnt = false;
    for _ in 0..12 {
        bt.step();
        far_burnt |= bt.units[far].burn > 0;
    }
    assert!(bt.units[near].burn > 0 || bt.units[near].hp < 100, "the Forge did not set the near one alight");
    assert!(far_burnt, "the fire did not run along the oil to the far one");
}

#[test]
fn lightning_runs_through_the_slime() {
    let mut bt = Battle::new(3).with_log();
    for x in 10..14 {
        for y in 10..12 {
            bt.pour(x, y, GOO);
        }
    }
    bt.place(0, still(mudrets()), 6, 10);
    let ants: Vec<usize> = (0..4).map(|k| bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 10 + k, 10)).collect();
    for &a in &ants {
        bt.units[a].hp = 100;
        bt.units[a].t.hp = 100;
    }
    for _ in 0..3 {
        bt.step();
    }
    assert!(log(&bt).iter().any(|e| matches!(e, Event::Surge { .. })), "no jolt ran through the slime");
    let hurt = ants.iter().filter(|&&a| bt.units[a].hp < 100).count();
    assert!(hurt >= 3, "the jolt reached only {hurt} of the 4 in the slime");
}

#[test]
fn the_knocked_back_bowl_the_others_over() {
    let mut bumps = 0;
    for seed in 0..10 {
        let mut bt = Battle::new(seed).with_log();
        bt.add_armies(&start_otets(), &army("start_matka"));
        bt.run();
        bumps += log(&bt).iter().filter(|e| matches!(e, Event::Bump { .. })).count();
    }
    assert!(bumps >= 10, "only {bumps} bodies bowled over in 10 battles");
}

#[test]
fn the_storm_strikes_the_iron_first() {
    let (mut on_iron, mut on_flesh) = (0, 0);
    for seed in 0..20 {
        let mut bt = Battle::new(seed).with_log().with_weather(Weather::Storm);
        let g = bt.place(0, still(strazh()), 3, 3);
        for k in 0..6 {
            bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 30, 2 + k * 4);
        }
        bt.units[g].hp = 999;
        for _ in 0..3 {
            bt.step();
        }
        for e in log(&bt) {
            if let Event::Strike { t } = *e {
                if t == g {
                    on_iron += 1;
                } else {
                    on_flesh += 1;
                }
            }
        }
    }
    // one Guard against six ants: by size alone it would draw a third of the strikes; iron draws more than half
    assert!(on_iron > on_flesh, "the Guard drew {on_iron} strikes, the six ants {on_flesh}");
}

#[test]
fn the_earth_splits_and_the_crack_holds() {
    let mut bt = Battle::new(4).with_log().with_weather(Weather::Quake);
    bt.add_armies(&start_zodchiy(), &army("start_matka"));
    for _ in 0..8 {
        if bt.step().is_some() {
            break;
        }
    }
    let rifts = log(&bt).iter().filter(|e| matches!(e, Event::Rift { .. })).count();
    assert!(rifts >= 1, "no crack in 8 rounds of an earthquake");
    assert!(bt.rift().iter().any(|&c| c));
}

#[test]
fn at_night_a_shooter_sees_only_what_burns() {
    let shots = |weather: Weather, burning: bool| {
        let mut bt = Battle::new(5).with_weather(weather);
        bt.place(0, still(orudie()), 3, 10);
        let a = bt.place(1, still(swarm(Caste::Worker, Form::Ant)), 7, 10);
        bt.units[a].hp = 100;
        bt.units[a].t.hp = 100;
        if burning {
            bt.units[a].burn = 9;
            bt.units[a].t.armor_type = sim::model::ArmorType::Flame; // it burns, and the fire does not hurt it
        }
        bt.step();
        bt.units[a].hp < 100
    };
    assert!(shots(Weather::Clear, false), "by day the Gun does not hit an ant 3 cells off");
    assert!(!shots(Weather::Night, false), "at night the Gun hits an ant it cannot see");
    assert!(shots(Weather::Night, true), "at night the Gun does not hit a burning ant");
    let _ = Cast::Lay;
}
