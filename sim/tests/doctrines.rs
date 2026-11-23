//! The swarm's mutations (doctrines): each changes how the whole swarm fights, and each has its price.

use sim::battle::Battle;
use sim::data::*;
use sim::model::{mitigate, Dmg, Template, Trait};
use sim::Event;

fn with(t: Template, tr: Trait) -> Template {
    t.with_trait(tr)
}

fn hits_by(bt: &Battle, a: usize) -> usize {
    bt.log.as_ref().unwrap().iter().filter(|e| matches!(e, Event::Hit { a: x, .. } if *x == a)).count()
}

/// Клеевой рой: no body of it lives on below half its health — it bursts, and the enemy beside it is stuck.
#[test]
fn glue_bursts_and_sticks() {
    let mut glued = 0;
    for seed in 0..10 {
        let mut bt = Battle::new(seed).with_log();
        bt.add_armies(&many(with(soldat(), Trait::GlueBurst), 16), &[strazh(), mudrets()]);
        while bt.step().is_none() {
            for u in bt.units.iter().filter(|u| u.present() && u.t.has(Trait::GlueBurst)) {
                assert!(u.hp * 2 >= u.t.hp, "a glue body lives on below half: {}/{}", u.hp, u.t.hp);
            }
        }
        glued += bt.log.as_ref().unwrap().iter().filter(|e| matches!(e, Event::Glue { .. })).count();
    }
    assert!(glued > 0, "no enemy was ever stuck in glue");
}

/// Мошкара: every second fallen body turns into a midge cloud; a cloud is no army — a side of clouds alone has lost;
/// it thins out after two rounds.
#[test]
fn midges_rise_from_the_fallen() {
    let mut bt = Battle::new(3).with_log();
    bt.add_armies(&many(with(rabochaya(), Trait::Midges), 2), &[strazh()]);
    let o = bt.run();
    let cloud = bt.units.iter().position(|u| u.t.has(Trait::Cloud));
    assert!(cloud.is_some(), "the fallen body left no cloud");
    assert_eq!(o.winner, Some(1), "the cloud alone held the field");
    // a cloud standing alone thins out
    let mut bt = Battle::new(1);
    let c = bt.place(0, unit("moshkara"), 2, 2);
    bt.place(0, strazh(), 2, 20);
    bt.place(1, strazh(), 33, 20);
    for _ in 0..5 {
        bt.step();
    }
    assert!(!bt.units[c].alive, "the cloud is still there after five rounds");
}

/// The cloud stings past any armor, and a shooter it stands on sees nothing to shoot.
#[test]
fn a_cloud_stings_through_armor_and_blinds() {
    let mut bt = Battle::new(2).with_log();
    let g = bt.place(1, strazh(), 10, 10);
    let c = bt.place(0, unit("moshkara"), 9, 10);
    bt.place(0, strazh(), 2, 25); // the army the cloud belongs to (a cloud alone has lost)
    bt.step();
    let stung = bt.log.as_ref().unwrap().iter().any(|e| matches!(e, Event::Hit { a, t, dmg } if *a == c && *t == g && *dmg > 0));
    assert!(stung, "the cloud did not get through the Guard's armor");
    // a sage with a cloud on it: no spell at the worker in its range
    let mut bt = Battle::new(2).with_log();
    let m = bt.place(1, mudrets(), 10, 10);
    bt.place(0, unit("moshkara"), 9, 10);
    bt.place(0, rabochaya(), 7, 14);
    for _ in 0..2 {
        bt.step();
    }
    assert_eq!(hits_by(&bt, m), 0, "the sage shot through the cloud");
    // fire burns a cloud threefold
    let c = unit("moshkara");
    assert_eq!(mitigate(1, Dmg::Fire, &c, 0, false, false), 3);
}

/// Паутина: on its spinning round a body spins instead of striking; the enemy in the web spends two actions tearing
/// free; fire runs along the web onto the spinners.
#[test]
fn the_web_holds_and_burns() {
    let mut bt = Battle::new(4).with_log();
    let g = bt.place(1, strazh(), 10, 10);
    let w = bt.place(0, with(rabochaya(), Trait::Spinner), 9, 10);
    bt.step(); // round 1: the worker spins, the Guard, stuck, struggles
    assert_eq!(hits_by(&bt, w), 0, "the spinner struck on its spinning round");
    assert_eq!(hits_by(&bt, g), 0, "the Guard struck from the web");
    bt.step(); // round 2: the Guard tears free
    assert_eq!(hits_by(&bt, g), 0, "the Guard struck while tearing free");
    bt.step(); // round 3: free
    assert!(hits_by(&bt, g) > 0, "the Guard stayed stuck after tearing free");
    // a clump of spinners at a forge: the forge's heat sets one alight, the web carries it to the others
    let mut bt = Battle::new(4);
    bt.place(1, gorn(), 10, 10);
    let ws: Vec<usize> = (0..6).map(|k| bt.place(0, with(rabochaya(), Trait::Spinner), 8, 9 + k / 2)).collect();
    bt.step();
    let burning = ws.iter().filter(|&&k| bt.units[k].burn > 0 || !bt.units[k].alive).count();
    assert!(burning >= 3, "the fire did not run along the web: {burning} of {}", ws.len());
}

/// Медовые соты: a wounded body next to its own mends two a round; a fallen one floods the cells round it with honey, and an
/// enemy blow from the honey lands weaker.
#[test]
fn honey_mends_and_floods() {
    let mut bt = Battle::new(6);
    let a = bt.place(0, with(soldat(), Trait::Honey), 2, 10);
    let b = bt.place(0, with(soldat(), Trait::Honey), 3, 10);
    bt.place(1, strazh(), 33, 10);
    bt.units[a].hp -= 5;
    bt.units[a].glued_until = 9;
    bt.units[b].glued_until = 9;
    bt.step();
    assert_eq!(bt.units[a].hp, bt.units[a].t.hp - 3, "no mending next to its own");
    // a fallen honey body floods its cells and the cells round them
    let mut bt = Battle::new(6);
    bt.add_armies(&many(with(rabochaya(), Trait::Honey), 12), &[strazh()]);
    bt.run();
    assert!(bt.honey().contains(&0), "the fallen left no honey");
    let _ = b;
}

/// Ржавчина's price: a soft body — its armor does not count, fire burns double.
#[test]
fn rust_softens_the_body() {
    let s = with(soldat(), Trait::SoftBody);
    let plain = soldat();
    assert!(plain.armor > 0);
    assert_eq!(mitigate(6, Dmg::Slash, &s, s.armor, false, false), mitigate(6, Dmg::Slash, &plain, 0, false, false));
    assert_eq!(mitigate(3, Dmg::Fire, &s, s.armor, false, false), 2 * mitigate(3, Dmg::Fire, &plain, plain.armor, false, false));
}

/// Почкование: the first wound splits a body — a bud with half the health left; neither buds again.
#[test]
fn budding_splits_once() {
    let mut buds = 0;
    for seed in 0..6 {
        let mut bt = Battle::new(seed).with_log();
        bt.add_armies(&many(with(soldat(), Trait::Buds), 10), &[kamenshchik(), kamenshchik()]);
        bt.run();
        let born: Vec<usize> = bt.units.iter().filter(|u| u.side == 0 && u.src.is_none()).map(|u| u.id).collect();
        for &b in &born {
            assert!(!bt.units[b].t.has(Trait::Buds), "a bud that can bud again");
        }
        buds += born.len();
        assert!(born.len() <= 10, "a body budded more than once");
    }
    assert!(buds > 0, "no body ever budded");
}

/// Единый разум: the swarm never flees, however frightening the enemy.
#[test]
fn one_mind_never_flees() {
    let (mut plain, mut one) = (0, 0);
    for seed in 0..8 {
        for (mind, count) in [(false, &mut plain), (true, &mut one)] {
            let w = if mind { with(rabochaya(), Trait::OneMind) } else { rabochaya() };
            let mut bt = Battle::new(seed).with_log();
            bt.add_armies(&many(w, 30), &[otets_kolossa()]);
            bt.run();
            *count += bt.log.as_ref().unwrap().iter().filter(|e| matches!(e, Event::Flee { .. })).count();
        }
    }
    assert!(plain > 0, "the plain swarm never fled the colossus (no test)");
    assert_eq!(one, 0, "one mind fled");
}

/// Крылатый рой: a flyer in a cell of small ones is not trampled with them — the big blow takes only its target.
#[test]
fn flyers_are_not_trampled() {
    for flyer in [false, true] {
        let mut bt = Battle::new(8).with_log();
        let g = bt.place(1, otets_kolossa(), 10, 10);
        let w = if flyer { with(rabochaya(), Trait::Flyer) } else { rabochaya() };
        let ws: Vec<usize> = (0..4).map(|_| bt.place(0, w.clone(), 9, 10)).collect();
        bt.step();
        let hit = ws.iter().filter(|&&k| bt.log.as_ref().unwrap().iter().any(|e| matches!(e, Event::Hit { a, t, .. } if *a == g && *t == k))).count();
        if flyer {
            assert!(hit <= 1, "the colossus trampled {hit} flyers at once");
        } else {
            assert!(hit > 1, "the colossus did not trample the cell");
        }
    }
}

/// Кровь Пожирателя in a breed: a body grows on what it bites out (6, then 12), not on kills.
#[test]
fn devourer_blood_grows_on_what_it_eats() {
    // a Mechanic does not strike back: the beetle bites in peace
    let mut bt = Battle::new(2);
    let g = bt.place(1, mekhanik(), 10, 10);
    let b = bt.place(0, with(zhuk(), Trait::Grows), 9, 10);
    let hp0 = bt.units[b].t.hp;
    for _ in 0..12 {
        if bt.step().is_some() || bt.units[b].fed >= 6 {
            break;
        }
    }
    assert!(bt.units[b].fed >= 6 && bt.units[b].growth >= 1, "fed {} growth {}", bt.units[b].fed, bt.units[b].growth);
    assert!(bt.units[b].t.hp > hp0);
    let _ = g;
}

/// Стрекот: every second round an enemy with three chirring bodies beside it — a machine too — loses its blow.
#[test]
fn the_chirr_shakes_the_surrounded() {
    let mut bt = Battle::new(5).with_log();
    let g = bt.place(1, strazh(), 10, 10);
    for (x, y) in [(9, 10), (9, 11), (12, 10)] {
        let k = bt.place(0, with(soldat(), Trait::Chirr), x, y);
        bt.units[k].hp = 999; // they must outlive the Guard's blows
        bt.units[k].t.hp = 999;
    }
    bt.step();
    let before = hits_by(&bt, g);
    assert!(before > 0, "the Guard never struck");
    bt.step(); // round 2: it shakes
    assert_eq!(hits_by(&bt, g), before, "the Guard struck through the chirr");
    bt.step(); // round 3: free of it
    assert!(hits_by(&bt, g) > before, "the Guard stayed shaken");
}
