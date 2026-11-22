//! Whole runs by a simple bot, many per leader: how often a run is won, where it is lost, how strong the army grows
//! (in reference fighters), and how full the enemy's side gets. Two bots: one takes every find, one passes them all.
//! `cargo run --release --bin runs -- 40`

use rayon::prelude::*;
use sim::data;
use sim::model::Template;
use sim::run::{self, Class, Kind, Reward, Run, ROOM};

fn etalons(me: &[Template]) -> usize {
    let win = |k: usize| -> f32 {
        let e = data::etalon(k);
        (0..120u64).filter(|&s| run::play(me, &e, 1000 + s).won).count() as f32 / 120.0
    };
    // no more than the enemy's zone holds
    let cap = (ROOM / run::room_cost(&data::etalon(1)[0])) as usize;
    // by doubling, then halving: a small army is never measured against hundreds
    let (mut lo, mut hi) = (1usize, cap);
    let mut n = 2;
    while n < cap && win(n) > 0.5 {
        lo = n + 1;
        n *= 2;
    }
    hi = hi.min(n);
    while lo < hi {
        let mid = (lo + hi) / 2;
        if win(mid) > 0.5 {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    lo
}

struct Out {
    won: bool,
    battles: u32,
    lost_at: Option<(u32, Kind, u8)>,
    /// The army's strength before each boss (fights 5, 10, 15), for the bosses reached.
    boss: Vec<usize>,
    full: u32,
    seen: u32,
}

fn play(class: Class, leader: usize, seed: u64, takes: bool) -> Out {
    let mut r = Run::new(class, leader, seed);
    let mut boss = vec![];
    let (mut full, mut seen) = (0, 0);
    let mut lost_at = None;
    while r.over.is_none() {
        let node = r.path[0].clone();
        match node.kind {
            k if k.is_battle() => {
                let room: i32 = node.enemy.iter().map(run::room_cost).sum();
                seen += 1;
                if room * 10 >= ROOM * 9 {
                    full += 1;
                }
                let (me, _) = r.fighters();
                if node.kind == Kind::Boss {
                    boss.push(etalons(&me));
                }
                let res = run::play(&me, &node.enemy, r.battle_seed());
                if !res.won {
                    lost_at = Some((r.next_fight(), node.kind, node.danger));
                }
                let rewards = r.after_battle(&node, &res);
                for rw in &rewards {
                    match rw {
                        Reward::Find(offers) => {
                            let mut took = false;
                            if takes {
                                for o in offers {
                                    let to = r.targets(o).into_iter().next();
                                    if (o.find == run::Find::Units || to.is_some()) && r.take_find(o, to.as_ref()) {
                                        took = true;
                                        break;
                                    }
                                }
                            }
                            if !took {
                                r.pass_find();
                            }
                        }
                        Reward::Growth(keys) => r.grow(&keys[0]),
                        other => {
                            if r.can_take(other) {
                                r.take(other)
                            }
                        }
                    }
                }
                if takes {
                    for f in r.forms() {
                        if let Some(e) = Run::evolutions(&f).iter().find(|e| !r.breeds.iter().any(|(x, k)| *x == f && k == &e.key)) {
                            if r.evolve(&f, &e.key) {
                                break;
                            }
                        }
                    }
                }
                r.fork();
            }
            Kind::Merchant => {
                let mut shop = r.shop();
                if takes {
                    for i in 0..shop.offers.len() {
                        let to = r.targets(&shop.offers[i].0).into_iter().next();
                        r.buy_offer(&mut shop, i, to.as_ref());
                    }
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
    Out { won: r.over == Some(true), battles: r.stats.won, lost_at, boss, full, seen }
}

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(40);
    println!("| Лидер | Бот | Походов выиграно | Боёв в среднем | Сила к боссам 5 / 10 / 15 | Враг упёрся в зону | Где проиграны |");
    println!("|---|---|---|---|---|---|---|");
    let names = ["Отец колосса", "Изобретатель", "Маньяк", "Зодчий", "Матка", "Разум улья", "Пожиратель", "Чума"];
    for class in [Class::Foundry, Class::Swarm] {
        for leader in 0..4 {
            for takes in [true, false] {
                let outs: Vec<Out> = (0..n).into_par_iter().map(|s| play(class, leader, 7000 + s * 31, takes)).collect();
                let won = outs.iter().filter(|o| o.won).count();
                let battles = outs.iter().map(|o| o.battles as f32).sum::<f32>() / n as f32;
                let at = |b: usize| -> String {
                    let v: Vec<f32> = outs.iter().filter_map(|o| o.boss.get(b)).map(|&x| x as f32).collect();
                    if v.is_empty() { "—".into() } else { format!("{:.0}", v.iter().sum::<f32>() / v.len() as f32) }
                };
                let full: u32 = outs.iter().map(|o| o.full).sum();
                let seen: u32 = outs.iter().map(|o| o.seen).sum();
                let mut lost: Vec<String> = outs
                    .iter()
                    .filter_map(|o| o.lost_at)
                    .map(|(f, k, d)| format!("{f}{}", match (k, d) { (Kind::Boss, _) => "Б", (Kind::Elite, _) => "Э", (_, 2) => "о", _ => "" }))
                    .collect();
                lost.sort();
                println!(
                    "| {} | {} | {}/{} | {:.1} | {} / {} / {} | {:.0}% | {} |",
                    names[if class == Class::Foundry { leader } else { 4 + leader }],
                    if takes { "берёт" } else { "пропускает" },
                    won,
                    n,
                    battles,
                    at(0),
                    at(1),
                    at(2),
                    100.0 * full as f32 / seen.max(1) as f32,
                    lost.join(" ")
                );
            }
        }
    }
}
