//! The difficulty curve's footing: each leader's start army against enemies of the run of each strength (in the
//! class's reference army, as curve.ron counts them: golems for the Foundry, swarm points for the swarm) — how often it wins, and the strength it beats half the time
//! (the «50 %» column: the start's worth in the curve's own measure).
//! `cargo run --release --bin curve -- 30 [foundry|swarm]`

use rayon::prelude::*;
use sim::run::{self, Class, Kind, Run};

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(30);
    let names = ["Отец колосса", "Изобретатель", "Маньяк", "Зодчий", "Матка", "Разум улья", "Пожиратель", "Чума"];
    // `foundry` or `swarm` after the count: that class only
    let only = std::env::args().nth(2);
    for (ci, class) in [Class::Foundry, Class::Swarm].into_iter().enumerate() {
        if only.as_deref().is_some_and(|o| o != ["foundry", "swarm"][ci]) {
            continue;
        }
        let budgets: Vec<f32> = match class {
            Class::Foundry => (1..=14).map(|b| b as f32 * 0.5).collect(),
            Class::Swarm => (1..=14).map(|b| b as f32 * 20.0).collect(),
        };
        print!("\n| Старт против врага силой |");
        for b in &budgets {
            print!(" {b} |");
        }
        println!(" 50 % |");
        println!("|---|{}---|", "---|".repeat(budgets.len()));
        for leader in 0..4 {
            print!("| {} |", names[ci * 4 + leader]);
            let mut rates = vec![];
            for &b in &budgets {
                // 8 enemies of this strength (each a run's own draw), `n` battles against each
                let won: u64 = (0..8u64)
                    .into_par_iter()
                    .map(|e| {
                        let mut r = Run::new(class, leader, 500 + e * 13);
                        let (enemy, _) = r.enemy_of(Kind::Fight, b);
                        let (me, _) = r.fighters();
                        (0..n).filter(|&s| run::play(&me, &enemy, 9000 + s).won).count() as u64
                    })
                    .sum();
                let rate = won as f32 / (8 * n) as f32;
                rates.push(rate);
                print!(" {:.0}% |", 100.0 * rate);
            }
            // where the win rate first falls through one half, between the two budgets around it
            let half = (1..rates.len()).find(|&k| rates[k] < 0.5 && rates[k - 1] >= 0.5).map(|k| {
                let (r0, r1) = (rates[k - 1], rates[k]);
                budgets[k - 1] + (budgets[k] - budgets[k - 1]) * (r0 - 0.5) / (r0 - r1).max(1e-6)
            });
            match half {
                Some(h) => println!(" {h:.1} |"),
                None if rates[0] < 0.5 => println!(" < {:.0} |", budgets[0]),
                None => println!(" > {:.0} |", budgets[budgets.len() - 1]),
            }
        }
    }
}
