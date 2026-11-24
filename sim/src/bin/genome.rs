//! The genome stand: what each mutation of the swarm (a doctrine on the whole swarm) is worth. The leader's start army
//! with one mutation against Foundry armies of a growing budget (12 steps from 80, ×1.12 each; 6 armies, 16 seeds
//! each): the budget it wins half its battles at, and its mean win rate over the whole ladder (a mutation that shows
//! in the hard fights moves the second more) — each against the army without mutations. A leader's own pool only with
//! that leader. Changes are printed to the nearest 5 % (the stand's noise is 5–10 %). With `--late`: a swarm of the run's second half (the start's bodies three times over) against armies
//! from 300 (6 steps, ×1.15; 4 armies, 8 seeds) — a mutation that grows with the swarm shows there, not at the start.
//! `cargo run --release --bin genome -- <leader 0–3> [--late] [keys…]`

use rayon::prelude::*;
use sim::run::{self, Class, Kind, Run, SWARM};
/// The budget where the army wins half its battles, and its mean win rate over the whole ladder (a mutation that
/// shows in the hard fights more than at the half moves the second more).
fn half(me: &[sim::model::Template], enemies: &[(f32, Vec<Vec<sim::model::Template>>)], seeds: u64) -> (f32, f32) {
    let rates: Vec<(f32, f32)> = enemies
        .iter()
        .map(|(b, es)| {
            let won: usize = es.par_iter().map(|e| (0..seeds).filter(|&s| run::play(me, e, 9000 + s).won).count()).sum();
            (*b, won as f32 / (seeds as f32 * es.len() as f32))
        })
        .collect();
    let mean = rates.iter().map(|r| r.1).sum::<f32>() / rates.len() as f32;
    for w in rates.windows(2) {
        let ((b0, r0), (b1, r1)) = (w[0], w[1]);
        if r0 >= 0.5 && r1 < 0.5 {
            return (b0 + (b1 - b0) * (r0 - 0.5) / (r0 - r1).max(1e-6), mean);
        }
    }
    (if rates[0].1 < 0.5 { rates[0].0 } else { rates[rates.len() - 1].0 }, mean)
}
/// A change in per cent to the nearest 5: the stand's noise is 5–10 %, finer figures mean nothing.
fn round5(p: f32) -> i32 {
    (p / 5.0).round() as i32 * 5
}

/// The army that goes into battle: the start's, or with `late` its bodies three times over (the leader once).
fn army(r: &Run, late: bool) -> Vec<sim::model::Template> {
    let f = r.fighters().0;
    if !late {
        return f;
    }
    let mut out = f.clone();
    for t in f.iter().filter(|t| !t.has(sim::model::Trait::Leader)) {
        out.push(t.clone());
        out.push(t.clone());
    }
    out
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let leader: usize = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(0);
    let late = args.iter().any(|a| a == "--late");
    let wanted: Vec<&String> = args.iter().skip(2).filter(|a| *a != "--late").collect();
    let (steps, from, step, armies, seeds) = if late { (6, 300.0, 1.15f32, 4u64, 8) } else { (12, 80.0, 1.12f32, 6u64, 16) };
    let budgets: Vec<f32> = (0..steps).map(|k| from * step.powi(k)).collect();
    let enemies: Vec<(f32, Vec<Vec<sim::model::Template>>)> = budgets
        .iter()
        .map(|&b| (b, (0..armies).map(|e| Run::new(Class::Swarm, leader, if late { 700 } else { 500 } + e * 13).enemy_of(Kind::Fight, b).0).collect()))
        .collect();
    let base = Run::new(Class::Swarm, leader, 1);
    let (h0, m0) = half(&army(&base, late), &enemies, seeds);
    println!("{}: без мутаций {:.0}, побед в среднем {:.2}", base.leader_key(), h0, m0);
    let own = base.leader_key();
    let keys: Vec<String> = sim::data::finds()
        .mutations
        .iter()
        .filter(|m| m.form.is_none() && m.leader.as_deref().is_none_or(|l| l == own))
        // only these, if named after the leader: `genome 1 m_strider m_onemind`
        .filter(|m| wanted.is_empty() || wanted.iter().any(|a| **a == m.key))
        .map(|m| m.key.clone())
        .collect();
    for k in keys {
        let mut r = Run::new(Class::Swarm, leader, 1);
        r.breeds.push((SWARM.to_string(), k.clone()));
        let (h, m) = half(&army(&r, late), &enemies, seeds);
        println!("{k}: {:.0} ({:+}%), побед {:.2} ({:+}%)", h, round5(100.0 * (h / h0 - 1.0)), m, round5(100.0 * (m / m0 - 1.0)));
    }
}
