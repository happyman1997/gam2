//! The difficulty curve's footing: each leader's start army against enemies of the run of each strength (in
//! reference fighters, as curve.ron counts them) — how often it wins. `cargo run --release --bin curve -- 40`

use rayon::prelude::*;
use sim::run::{self, Class, Kind, Run};

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(40);
    let budgets: Vec<f32> = (2..=20).step_by(2).map(|b| b as f32).collect();
    let names = ["Отец колосса", "Изобретатель", "Маньяк", "Зодчий", "Матка", "Разум улья", "Пожиратель", "Чума"];
    print!("| Старт против врага силой |");
    for b in &budgets {
        print!(" {b:.0} |");
    }
    println!();
    println!("|---|{}", "---|".repeat(budgets.len()));
    for (ci, class) in [Class::Foundry, Class::Swarm].into_iter().enumerate() {
        for leader in 0..4 {
            print!("| {} |", names[ci * 4 + leader]);
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
                print!(" {:.0}% |", 100.0 * won as f32 / (8 * n) as f32);
            }
            println!();
        }
    }
}
