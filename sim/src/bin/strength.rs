//! Strength of one unit in reference fighters, with stat overrides — for tuning numbers.
//!
//! `cargo run --release --bin strength -- molot hp=63 die=8 bonus=4 armor=3 [+plates] [+flail] [+remont] [pair=strazh] [m=400]`
//! With `pair=X` it prints the contribution: strength(X + unit) − strength(X).

use rayon::prelude::*;
use sim::data::*;
use sim::fight;
use sim::model::{Ability, Template};
use sim::power::{edpr, ehp, value};

const MAX_N: usize = 84;

fn base(key: &str) -> Template {
    match key {
        "molot" => molot(),
        "orudie" => orudie(),
        "gorn" => gorn(),
        "strazh" => strazh(),
        "mekhanik" => mekhanik(),
        "kamenshchik" => kamenshchik(),
        "otets" => otets_kolossa(),
        "izobretatel" => izobretatel(),
        "manyak" => manyak(),
        "zodchiy" => zodchiy(),
        "rabochaya" => rabochaya(),
        "soldat" => soldat(),
        "zhuk" => zhuk(),
        _ => voin(),
    }
}

fn win_rate(a: &[Template], b: &[Template], m: u64) -> f64 {
    let wins: u64 = (0..m).into_par_iter().map(|s| (fight(a, b, s).winner == Some(0)) as u64).sum();
    wins as f64 / m as f64
}

/// Reference fighters this group ties with (fractional: interpolated between n and n+1).
fn strength(group: &[Template], m: u64) -> f64 {
    let (mut lo, mut hi) = (0usize, MAX_N);
    if win_rate(group, &etalon(MAX_N), m) > 0.5 {
        return MAX_N as f64;
    }
    while lo + 1 < hi {
        let mid = (lo + hi) / 2;
        if win_rate(group, &etalon(mid), m) > 0.5 {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    // lo wins, hi does not: interpolate on the win rates
    let (wl, wh) = (if lo == 0 { 1.0 } else { win_rate(group, &etalon(lo), m) }, win_rate(group, &etalon(hi), m));
    lo as f64 + ((wl - 0.5) / (wl - wh).max(1e-9)).clamp(0.0, 1.0)
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut t = base(args.first().map(String::as_str).unwrap_or("molot"));
    let mut m = 400u64;
    let mut pair: Option<Template> = None;
    for a in &args[1..] {
        if let Some((k, v)) = a.split_once('=') {
            match k {
                "hp" => t.hp = v.parse().unwrap(),
                "die" => t.die = v.parse().unwrap(),
                "bonus" => t.bonus = v.parse().unwrap(),
                "armor" => t.armor = v.parse().unwrap(),
                "init" => t.init = v.parse().unwrap(),
                "speed" => t.speed = v.parse().unwrap(),
                "m" => m = v.parse().unwrap(),
                "pair" => pair = Some(base(v)),
                "remont" => t.abilities.push(Ability::Repair { every: 2, amount: v.parse().unwrap() }),
                _ => panic!("unknown {}", k),
            }
        } else {
            match a.as_str() {
                "+plates" => t.abilities.push(Ability::Plates(3)),
                "+flail" => t.abilities.push(Ability::Flail),
                "+remont" => t.abilities.push(remont()),
                "+intercept" => t.abilities.push(Ability::Intercept),
                _ => panic!("unknown {}", a),
            }
        }
    }
    let reference = etalon_types();
    let v_ref = reference.iter().map(|r| value(r, &reference)).sum::<f64>() / reference.len() as f64;
    let v = value(&t, &reference);
    let by_curve = 1.04 * (v / v_ref).powf(0.58);
    let k = if t.size <= 3 { 4 } else { 1 };
    let measured = match &pair {
        Some(p) => {
            let mut g = vec![p.clone()];
            g.extend(vec![t.clone(); k]);
            (strength(&g, m) - strength(&[p.clone()], m)) / k as f64
        }
        None => strength(&vec![t.clone(); k], m) / k as f64,
    };
    println!(
        "{}: здоровье {} удар 1–{} +{} броня {} | эфф. здоровье {:.0}, урон за раунд {:.1}, по кривой {:.1}, в бою {:.1} эталона",
        t.name, t.hp, t.die, t.bonus, t.armor, ehp(&t, &reference), edpr(&t, &reference), by_curve, measured
    );
}
