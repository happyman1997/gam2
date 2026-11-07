//! Strength of a unit without a battle: expected damage and effective health against the
//! reference squad. Value = effective health × damage per round (Lanchester's fighting value).

use crate::model::{mitigate, Ability, Template, Trait};

/// Distribution of an open-ended roll "1–die +bonus": (value, probability); the maximum rolls again.
pub fn roll_dist(die: u32, bonus: i32) -> Vec<(i32, f64)> {
    fn rec(die: u32, base: i32, p: f64, depth: u32, bonus: i32, out: &mut Vec<(i32, f64)>) {
        for r in 1..=die as i32 {
            let pr = p / die as f64;
            if r == die as i32 && die > 1 && depth < 5 {
                rec(die, base + r, pr, depth + 1, bonus, out);
            } else {
                out.push(((base + r + bonus).max(0), pr));
            }
        }
    }
    if die == 0 {
        return vec![(bonus.max(0), 1.0)];
    }
    let mut out = vec![];
    rec(die, 0, 1.0, 0, bonus, &mut out);
    out
}

pub fn mean_raw(die: u32, bonus: i32) -> f64 {
    roll_dist(die, bonus).iter().map(|(v, p)| *v as f64 * p).sum()
}

/// Expected damage of one blow of `a` against `t`.
pub fn expected_hit(a: &Template, t: &Template) -> f64 {
    let probivnoy = a.has(Trait::Probivnoy);
    roll_dist(a.die, a.bonus)
        .iter()
        .map(|(v, p)| p * mitigate(*v, a.dmg, t, t.armor, false, probivnoy) as f64)
        .sum()
}

pub fn attacks_per_round(a: &Template) -> f64 {
    if a.has(Trait::NoAttack) {
        0.0
    } else if a.abilities.contains(&Ability::Flail) {
        2.0
    } else {
        1.0
    }
}

/// Damage per round against the reference targets (average).
pub fn edpr(a: &Template, targets: &[Template]) -> f64 {
    let per: f64 = targets.iter().map(|t| expected_hit(a, t)).sum::<f64>() / targets.len() as f64;
    per * attacks_per_round(a)
}

/// Health divided by the share of the reference attackers' damage that gets through.
pub fn ehp(t: &Template, attackers: &[Template]) -> f64 {
    let raw: f64 = attackers.iter().map(|a| mean_raw(a.die, a.bonus)).sum::<f64>() / attackers.len() as f64;
    let got: f64 = attackers.iter().map(|a| expected_hit(a, t)).sum::<f64>() / attackers.len() as f64;
    t.hp as f64 * raw / got.max(0.05)
}

/// Fighting value against the reference squad.
pub fn value(t: &Template, reference: &[Template]) -> f64 {
    ehp(t, reference) * edpr(t, reference)
}
