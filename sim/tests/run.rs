//! Whole runs played by a simple bot (the first road, every spoil taken, the first find, what it can afford at the
//! trader, the first event option it can take, rest at camp): a run goes from the first battle to its end for every
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
