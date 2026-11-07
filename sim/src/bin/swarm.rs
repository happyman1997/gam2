//! Strength of every Swarm form and caste in reference fighters; with `tune` suggests health to hit
//! the price (a worker is 1 point ≈ 0.33 of a fighter, a soldier 3 points ≈ 1 fighter).
//! `cargo run --release --bin swarm -- 300 [tune]`

use rayon::prelude::*;
use sim::data::*;
use sim::fight;
use sim::model::Template;

const MAX_N: usize = 84;

fn win_rate(a: &[Template], b: &[Template], m: u64) -> f64 {
    let wins: u64 = (0..m).into_par_iter().map(|s| (fight(a, b, s).winner == Some(0)) as u64).sum();
    wins as f64 / m as f64
}

fn strength(group: &[Template], m: u64) -> f64 {
    if win_rate(group, &etalon(MAX_N), m) > 0.5 {
        return MAX_N as f64;
    }
    let (mut lo, mut hi) = (0usize, MAX_N);
    while lo + 1 < hi {
        let mid = (lo + hi) / 2;
        if win_rate(group, &etalon(mid), m) > 0.5 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    let wl = if lo == 0 { 1.0 } else { win_rate(group, &etalon(lo), m) };
    let wh = win_rate(group, &etalon(hi), m);
    lo as f64 + ((wl - 0.5) / (wl - wh).max(1e-9)).clamp(0.0, 1.0)
}

fn main() {
    let m: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(300);
    let tune = std::env::args().any(|a| a == "tune");
    println!("| Форма | Рабочая, эталонов (цель 0,33) | Солдат, эталонов (цель 1,0) |");
    println!("|---|---|---|");
    let mut hp = SWARM_HP;
    for (fi, f) in FORMS.iter().enumerate() {
        let mut cells = vec![];
        for (ci, c) in [Caste::Worker, Caste::Soldier].iter().enumerate() {
            let target = if ci == 0 { 0.33 } else { 1.0 };
            let k = if ci == 0 { 16 } else { 8 };
            let mut t = swarm(*c, *f);
            let mut s = strength(&vec![t.clone(); k], m) / k as f64;
            if tune {
                for _ in 0..3 {
                    // strength grows about as the square root of health × damage
                    let factor = (target / s.max(0.05)).powf(1.9).clamp(0.4, 2.5);
                    t.hp = ((t.hp as f64 * factor).round() as i32).max(1);
                    s = strength(&vec![t.clone(); k], m) / k as f64;
                }
                hp[ci][fi] = t.hp;
            }
            cells.push(format!("{:.2} (здоровье {})", s, t.hp));
        }
        println!("| {} | {} | {} |", f.name(), cells[0], cells[1]);
    }
    if tune {
        println!("\nSWARM_HP = {:?}", hp);
    }
}
