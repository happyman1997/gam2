//! Whole runs played by a simple bot (the first road, every spoil taken, the first find, an evolution when it can,
//! what it can afford at the trader, the first event option it can take, rest at camp): a run goes from the first battle to its end for every
//! leader of both classes; the forks are quick enough to build between screens.

use sim::run::{self, Class, Kind, Reward, Run};
use std::time::Instant;

fn play_run(class: Class, leader: usize, seed: u64) -> (Run, f64) {
    let mut r = Run::new(class, leader, seed);
    let mut fork_secs = 0.0f64;
    let mut steps = 0;
    while r.over.is_none() {
        steps += 1;
        assert!(steps < 200, "a run that does not end");
        assert!(!r.path.is_empty(), "a fork with no road");
        let node = r.path[0].clone();
        match node.kind {
            k if k.is_battle() => {
                assert!(!node.enemy.is_empty(), "a battle with no enemy");
                let (me, _) = r.fighters();
                let seed = r.battle_seed();
                let res = run::play(&me, &node.enemy, seed);
                let rewards = r.after_battle(&node, &res);
                for rw in &rewards {
                    match rw {
                        Reward::Find(offers) => {
                            assert_eq!(offers.len(), 3);
                            // the first find that can go somewhere: bodies join, a part onto its first target
                            for o in offers {
                                let to = r.targets(o).into_iter().next();
                                if (o.find == run::Find::Units || to.is_some()) && r.take_find(o, to.as_ref()) {
                                    break;
                                }
                            }
                        }
                        Reward::Growth(keys) => {
                            assert!(node.kind == Kind::Boss, "a leader grows after a boss only");
                            assert_eq!(keys.len(), 2);
                            assert!(keys[0] != keys[1]);
                            r.grow(&keys[0]);
                        }
                        other => {
                            if r.can_take(other) {
                                r.take(other)
                            }
                        }
                    }
                }
                // the swarm: an evolution for the first form that has one left, when the biomass is there
                for f in r.forms() {
                    if let Some(e) = Run::evolutions(&f).iter().find(|e| !r.breeds.iter().any(|(x, k)| *x == f && k == &e.key)) {
                        if r.evolve(&f, &e.key) {
                            break;
                        }
                    }
                }
                let t = Instant::now();
                r.fork();
                fork_secs = fork_secs.max(t.elapsed().as_secs_f64());
            }
            Kind::Merchant => {
                let mut shop = r.shop();
                for i in 0..shop.offers.len() {
                    let to = r.targets(&shop.offers[i].0).into_iter().next();
                    r.buy_offer(&mut shop, i, to.as_ref());
                }
                r.buy_service(&mut shop);
                r.left_stop();
            }
            Kind::Event => {
                let opt = (0..3).find(|&o| r.event_can(node.event, o)).unwrap();
                r.event_choose(node.event, opt);
                r.left_stop();
            }
            Kind::Camp => {
                r.camp_rest();
                r.left_stop();
            }
            _ => unreachable!(),
        }
    }
    (r, fork_secs)
}

#[test]
fn runs_end() {
    for class in [Class::Foundry, Class::Swarm] {
        for leader in 0..4 {
            let (r, fork) = play_run(class, leader, 11 + leader as u64);
            let mods: usize = r.army.iter().map(|m| m.mods.len()).sum();
            eprintln!("  modules on golems {mods}, breeds mutated {}, leader grown {:?}", r.breeds.len(), r.growth);
            eprintln!(
                "{class:?} {}: {} after {} battles, army {}, money {}, artifacts {}, slowest fork {:.2} s",
                class.leaders()[leader],
                if r.over == Some(true) { "won" } else { "lost" },
                r.stats.won,
                r.army.len(),
                r.money,
                r.artifacts.len(),
                fork
            );
            assert!(r.army.iter().any(|m| r.is_leader(m)), "the leader is never lost");
            // past the first boss, the leader has grown
            if r.stats.won >= 5 {
                assert!(!r.growth.is_empty(), "a boss beaten and the leader the same");
            }
            // every module sits on a golem it fits, within its cells
            for m in &r.army {
                assert!(m.mods.len() <= r.cells(m), "{} carries more modules than it has cells", m.t.name);
            }
        }
    }
}

#[test]
fn saves_and_loads() {
    let r = Run::new(Class::Swarm, 2, 5);
    let s = serde_json::to_string(&r).unwrap();
    let back: Run = serde_json::from_str(&s).unwrap();
    assert_eq!(back.army.len(), r.army.len());
    assert_eq!(back.path.len(), r.path.len());
}

/// A save from before the modules had levels and the leader grew: it still loads, every module at level I.
#[test]
fn an_older_save_loads() {
    use sim::run::{Find, Offer, Target};
    let mut r = Run::new(Class::Foundry, 1, 5);
    let i = r.army.iter().position(|m| m.t.golem).unwrap();
    assert!(r.take_find(&Offer { key: "flail".into(), units: vec![], price: 0, find: Find::Module("flail".into()) }, Some(&Target::Member(i))));
    let mut v: serde_json::Value = serde_json::to_value(&r).unwrap();
    v.as_object_mut().unwrap().remove("growth");
    for m in v["army"].as_array_mut().unwrap() {
        m.as_object_mut().unwrap().remove("levels");
    }
    let back: Run = serde_json::from_value(v).expect("an older save");
    assert!(back.growth.is_empty());
    assert_eq!(back.army[i].mods, vec!["flail".to_string()]);
    assert_eq!(back.army[i].level(0), 1);
}

/// Every way a leader can grow changes something: the leader's battle body, the rest of the army's, the cells, or the
/// army itself.
#[test]
fn every_growth_does_something() {
    for class in [Class::Foundry, Class::Swarm] {
        for leader in 0..4 {
            let base = Run::new(class, leader, 3);
            let key = base.leader_key();
            let list = sim::data::growth(key);
            assert!(list.len() >= 2, "{key}: fewer than two growths");
            let look = |r: &Run| {
                let bodies: Vec<String> = r.army.iter().map(|m| format!("{:?}", r.body(m))).collect();
                let cells: Vec<usize> = r.army.iter().map(|m| r.cells(m)).collect();
                (bodies, cells, r.army.len())
            };
            for g in list {
                let mut r = base.clone();
                r.grow(&g.key);
                assert_eq!(r.growth, vec![g.key.clone()]);
                assert!(look(&r) != look(&base), "{key}: {} changes nothing", g.key);
                // taken once only
                r.grow(&g.key);
                assert_eq!(r.growth.len(), 1);
            }
            // all of them taken: each still there (a second of one kind adds to the first)
            let mut all = base.clone();
            for g in list {
                all.grow(&g.key);
            }
            for g in list {
                let mut one = base.clone();
                one.grow(&g.key);
                let leader = |r: &Run| r.body(r.army.iter().find(|m| r.is_leader(m)).unwrap());
                for a in &leader(&one).abilities {
                    let kept = leader(&all).abilities.iter().any(|b| std::mem::discriminant(a) == std::mem::discriminant(b) && a.every().unwrap_or(0) >= b.every().unwrap_or(0));
                    assert!(kept, "{key}: {} lost with the others taken", g.key);
                }
            }
            // two offered, both different, none taken already
            let mut r = base.clone();
            let first = r.growth_offer();
            assert_eq!(first.len(), 2);
            r.grow(&first[0]);
            let second = r.growth_offer();
            assert!(!second.contains(&first[0]));
        }
    }
}

/// The workshop: a module taken again is a level up (to III, then no more); a module moves between golems where it
/// fits, its level with it; melted into another of the same frame, it raises that one for its metal.
#[test]
fn modules_level_move_and_melt() {
    use sim::run::{Find, Offer, Target, MAX_LEVEL, MELT};
    // the Inventor's army: Мудрец, Орудие, Механик — small frames with two cells each
    let mut r = Run::new(Class::Foundry, 1, 9);
    let mech = r.army.iter().position(|m| m.t.name == "Механик").unwrap();
    let gun = r.army.iter().position(|m| m.t.name == "Орудие").unwrap();
    let flail = Offer { key: "flail".into(), units: vec![], price: 0, find: Find::Module("flail".into()) };
    let base = r.body(&r.army[mech]).bonus;
    assert!(r.take_find(&flail, Some(&Target::Member(mech))));
    assert_eq!(r.army[mech].level(0), 1);
    // the same again on it: level II, then III; then no more room for it there
    assert!(r.targets(&flail).contains(&Target::Member(mech)));
    assert!(r.take_find(&flail, Some(&Target::Member(mech))));
    assert!(r.take_find(&flail, Some(&Target::Member(mech))));
    assert_eq!(r.army[mech].level(0), MAX_LEVEL);
    assert_eq!(r.army[mech].mods.len(), 1);
    assert!(!r.raises(mech, "flail"));
    // a flail has no numbers to raise: each level is a harder blow
    assert_eq!(r.body(&r.army[mech]).bonus, base + 2);
    // a mortar levelled: a round sooner, a die bigger
    let mortar = Offer { key: "mortar".into(), units: vec![], price: 0, find: Find::Module("mortar".into()) };
    assert!(r.take_find(&mortar, Some(&Target::Member(gun))));
    let at1 = r.body(&r.army[gun]).abilities.clone();
    assert!(r.take_find(&mortar, Some(&Target::Member(gun))));
    let at2 = r.body(&r.army[gun]).abilities.clone();
    assert_ne!(at1, at2, "a mortar at level II the same as at I");
    // moved to the gun (any frame takes a flail), its level with it
    assert!(r.move_module(mech, 0, gun));
    assert!(r.army[mech].mods.is_empty());
    let j = r.army[gun].mods.iter().position(|k| k == "flail").unwrap();
    assert_eq!(r.army[gun].level(j), MAX_LEVEL);
    // the gun's cells are full now: nothing more moves onto it
    assert!(r.take_find(&flail, Some(&Target::Member(mech))));
    assert!(!r.move_module(mech, 0, gun));
    // melting needs one frame: the mechanic's flail can't go into the gun's mortar
    let m = r.army[gun].mods.iter().position(|k| k == "mortar").unwrap();
    r.money = 10;
    assert!(!r.can_melt(mech, 0, gun, m));
    // on one golem it can: the gun's flail into its mortar (II → III), the flail gone, the metal paid
    let f = r.army[gun].mods.iter().position(|k| k == "flail").unwrap();
    assert!(r.melt(gun, f, gun, m));
    assert_eq!(r.money, 10 - MELT);
    assert_eq!(r.army[gun].mods, vec!["mortar".to_string()]);
    assert_eq!(r.army[gun].level(0), MAX_LEVEL);
    // with no metal there is no melting
    r.money = 0;
    assert!(!r.can_melt(mech, 0, mech, 0));
}

/// The swarm: evolutions are a form's own and bought with biomass, dearer each time, never found; a leader's own
/// mutations come only with that leader, the common ones with any.
#[test]
fn evolutions_and_leader_pools() {
    use sim::run::{Find, EVO_PRICE, EVO_STEP};
    // every leader of the swarm: what its finds offer, over many
    let mut seen: Vec<Vec<String>> = vec![];
    for leader in 0..4 {
        let mut r = Run::new(Class::Swarm, leader, 4);
        let mut keys = vec![];
        for _ in 0..200 {
            for o in r.find(3, false) {
                if let Find::Mutation(k) = o.find {
                    keys.push(k);
                }
            }
        }
        keys.sort();
        keys.dedup();
        let own = r.leader_key().to_string();
        for k in &keys {
            let m = sim::data::finds().mutations.iter().find(|m| &m.key == k).unwrap();
            assert!(m.form.is_none(), "{k}: an evolution offered as a find");
            assert!(m.leader.as_deref().is_none_or(|l| l == own), "{k}: another leader's mutation with {own}");
        }
        assert!(keys.iter().any(|k| sim::data::finds().mutations.iter().any(|m| &m.key == k && m.leader.as_deref() == Some(own.as_str()))), "{own}: its own pool never offered");
        seen.push(keys);
    }
    // evolutions: the ant's, bought dearer each time; another form's not for the ant; no biomass, no evolution
    let mut r = Run::new(Class::Swarm, 0, 4);
    let ant = "Муравей";
    assert!(r.forms().iter().any(|f| f == ant));
    r.money = 100;
    assert_eq!(r.evo_price(ant), EVO_PRICE);
    assert!(!r.evolve(ant, "evo_syringe"), "a wasp's evolution on the ant");
    assert!(r.evolve(ant, "evo_formic"));
    assert!(!r.evolve(ant, "evo_formic"), "the same evolution twice");
    assert_eq!(r.money, 100 - EVO_PRICE);
    assert_eq!(r.evo_price(ant), EVO_PRICE + EVO_STEP);
    // the ants are acid now, in battle
    let m = r.army.iter().find(|m| sim::run::form_of(&m.t) == ant && !r.is_leader(m)).unwrap();
    assert_eq!(r.body(m).dmg, sim::model::Dmg::Acid);
    r.money = EVO_PRICE + EVO_STEP - 1;
    assert!(!r.evolve(ant, "evo_phalanx"), "an evolution without the biomass for it");
}

/// «Ещё ячейка» of the Father of the Colossus is his alone; «Ещё аугмент» of the Inventor is every golem's.
#[test]
fn growth_cells_go_where_they_say() {
    use sim::run::{Find, Offer};
    let mut r = Run::new(Class::Foundry, 0, 3);
    r.recruit(&Offer { key: "strazh".into(), units: vec![sim::data::strazh()], price: 0, find: Find::Units });
    let lead = r.army.iter().position(|m| r.is_leader(m)).unwrap();
    let other = r.army.iter().position(|m| !r.is_leader(m) && m.t.golem).unwrap();
    let (l0, o0) = (r.cells(&r.army[lead]), r.cells(&r.army[other]));
    r.grow("colossus_cell");
    assert_eq!(r.cells(&r.army[lead]), l0 + 1);
    assert_eq!(r.cells(&r.army[other]), o0, "the colossus's cell went to another golem");
    let mut r = Run::new(Class::Foundry, 1, 3);
    let before: Vec<usize> = r.army.iter().filter(|m| m.t.golem).map(|m| r.cells(m)).collect();
    r.grow("inventor_cells");
    let after: Vec<usize> = r.army.iter().filter(|m| m.t.golem).map(|m| r.cells(m)).collect();
    assert!(before.iter().zip(&after).all(|(b, a)| a == &(b + 1)));
}
