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
                            r.recruit(&offers[0]);
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
                    r.buy_offer(&mut shop, i);
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
