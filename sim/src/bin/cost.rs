//! Cost curve: every unit's strength measured in fighters of the reference squad.
//!
//! For each unit: its value without a battle (effective health × damage per round against the
//! reference squad) and how many reference fighters it beats half of the time in the simulation.
//! Then the exponent e in  strength ≈ c · (value / value of a reference fighter)^e  is fitted:
//! e = 1 is Lanchester's linear law, e = 0.5 the square law.
//!
//! `cargo run --release --bin cost -- 300`

use rayon::prelude::*;
use sim::data::*;
use sim::fight;
use sim::model::{Template, Trait};
use sim::power::{edpr, ehp, value};

const MAX_N: usize = 84; // the reference zone holds 6 × 14 humans

fn win_rate(a: &[Template], b: &[Template], m: u64) -> f64 {
    let wins: u64 = (0..m)
        .into_par_iter()
        .map(|seed| if fight(a, b, seed).winner == Some(0) { 1 } else { 0 })
        .sum();
    wins as f64 / m as f64
}

/// Smallest n of reference fighters that `group` no longer beats more than half of the time.
fn even(group: &[Template], m: u64) -> Option<usize> {
    if win_rate(group, &etalon(MAX_N), m) > 0.5 {
        return None;
    }
    let (mut lo, mut hi) = (1usize, MAX_N);
    while lo < hi {
        let mid = (lo + hi) / 2;
        if win_rate(group, &etalon(mid), m) > 0.5 {
            lo = mid + 1;
        } else {
            hi = mid;
        }
    }
    Some(lo)
}

fn main() {
    let m: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(300);
    let reference = etalon_types();
    let v_ref = reference.iter().map(|t| value(t, &reference)).sum::<f64>() / reference.len() as f64;
    let units: Vec<(Template, Option<u32>)> = vec![
        (rabochaya(), None),
        (soldat(), None),
        (zhuk(), None),
        (voin(), None),
        (kamenshchik(), None),
        (izobretatel(), None),
        (manyak(), None),
        (zodchiy(), None),
        (orudie(), Some(5)),
        (molot(), Some(5)),
        (gorn(), Some(5)),
        (strazh(), Some(7)),
        (otets_kolossa(), None),
    ];
    println!("Эталонный отряд: копейщик, мечник, булавщик, лучник (размер 3, здоровье 10–12). {} боёв на шаг.\n", m);
    println!("| Юнит | Размер | Эфф. здоровье | Урон за раунд | Ценность | Ценность в эталонах | Сила в бою, эталонов | Лидерство |");
    println!("|---|---|---|---|---|---|---|---|");
    let mut fit = vec![];
    for (t, lead) in &units {
        if t.has(Trait::NoAttack) {
            continue;
        }
        let k = if t.size <= 3 { 4 } else { 1 };
        let group = vec![t.clone(); k];
        let v = value(t, &reference);
        let n = even(&group, m);
        let strength = n.map(|n| n as f64 / k as f64);
        if let Some(s) = strength {
            fit.push(((v / v_ref).ln(), s.ln()));
        }
        println!(
            "| {} | {} | {:.0} | {:.1} | {:.0} | {:.2} | {} | {} |",
            t.name,
            t.size,
            ehp(t, &reference),
            edpr(t, &reference),
            v,
            v / v_ref,
            strength.map(|s| format!("{:.2}", s)).unwrap_or(format!("больше {}", MAX_N)),
            lead.map(|l| l.to_string()).unwrap_or("—".into())
        );
    }
    // least squares: ln(strength) = e * ln(value ratio) + c
    let nf = fit.len() as f64;
    let (sx, sy) = (fit.iter().map(|p| p.0).sum::<f64>(), fit.iter().map(|p| p.1).sum::<f64>());
    let (sxx, sxy) = (fit.iter().map(|p| p.0 * p.0).sum::<f64>(), fit.iter().map(|p| p.0 * p.1).sum::<f64>());
    let e = (nf * sxy - sx * sy) / (nf * sxx - sx * sx);
    let c = (sy - e * sx) / nf;
    let r2 = {
        let mean = sy / nf;
        let ss_tot: f64 = fit.iter().map(|p| (p.1 - mean).powi(2)).sum();
        let ss_res: f64 = fit.iter().map(|p| (p.1 - (e * p.0 + c)).powi(2)).sum();
        1.0 - ss_res / ss_tot
    };
    println!(
        "\nКривая: сила ≈ {:.2} · (ценность / ценность эталона)^{:.2}, R² = {:.2}. Ценность эталонного бойца {:.0}.",
        c.exp(),
        e,
        r2,
        v_ref
    );
}
