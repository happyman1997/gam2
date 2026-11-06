//! Runs every scenario many times and prints win rates.
//! `cargo run --release --bin balance -- 2000`

use sim::data::*;
use sim::fight;
use sim::model::Template;

struct Row {
    name: String,
    a_win: f32,
    b_win: f32,
    draw: f32,
    rounds: f32,
    a_hp: f32,
}

fn run(name: &str, a: &[Template], b: &[Template], n: u64) -> Row {
    let (mut wa, mut wb, mut dr, mut rounds, mut hp) = (0u64, 0u64, 0u64, 0u64, 0f32);
    for seed in 0..n {
        let o = fight(a, b, seed);
        match o.winner {
            Some(0) => {
                wa += 1;
                hp += o.hp_left[0];
            }
            Some(_) => wb += 1,
            None => dr += 1,
        }
        rounds += o.rounds as u64;
    }
    let p = |x: u64| 100.0 * x as f32 / n as f32;
    Row {
        name: name.to_string(),
        a_win: p(wa),
        b_win: p(wb),
        draw: p(dr),
        rounds: rounds as f32 / n as f32,
        a_hp: if wa > 0 { 100.0 * hp / wa as f32 } else { 0.0 },
    }
}

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(2000);
    let workers = |k| many(rabochaya(), k);
    let metal_answer = {
        let mut v = many(rabochaya(), 12);
        v.extend(many(zhuk(), 6));
        v.extend(many(kislotnik(), 4));
        v
    };
    let scenarios: Vec<(&str, Vec<Template>, Vec<Template>)> = vec![
        ("Страж против 10 рабочих", vec![strazh()], workers(10)),
        ("Молот против 10 рабочих", vec![molot()], workers(10)),
        ("Горн против 10 рабочих", vec![gorn()], workers(10)),
        ("Орудие против 10 рабочих", vec![orudie()], workers(10)),
        ("Страж против 4 солдат", vec![strazh()], many(soldat(), 4)),
        ("Молот против 4 солдат", vec![molot()], many(soldat(), 4)),
        ("Молот против 4 воинов", vec![molot()], many(voin(), 4)),
        ("Молот и Орудие против 25 рабочих", vec![molot(), orudie()], workers(25)),
        ("Страж и Механик против 25 рабочих", vec![strazh(), mekhanik()], workers(25)),
        ("Страж и Механик: рабочие, жуки, кислотники", vec![strazh(), mekhanik()], metal_answer),
        ("Старт Отца колосса против роя", start_otets(), swarm_start()),
        ("Старт Изобретателя против роя", start_izobretatel(), swarm_start()),
        ("Старт Маньяка против роя", start_manyak(), swarm_start()),
        ("Старт Зодчего против роя", start_zodchiy(), swarm_start()),
        ("Старт Отца колосса против 8 воинов", start_otets(), humans_squad()),
        ("Старт Изобретателя против 8 воинов", start_izobretatel(), humans_squad()),
        ("Старт Маньяка против 8 воинов", start_manyak(), humans_squad()),
        ("Старт Зодчего против 8 воинов", start_zodchiy(), humans_squad()),
        ("Для сравнения: рой старта против 8 воинов", swarm_start(), humans_squad()),
    ];
    println!("{} боёв на сценарий\n", n);
    println!("| Сценарий | Литейщик | Противник | Ничья | Раундов | Осталось прочности у победившего Литейщика |");
    println!("|---|---|---|---|---|---|");
    for (name, a, b) in scenarios {
        let r = run(name, &a, &b, n);
        println!(
            "| {} | {:.0}% | {:.0}% | {:.0}% | {:.1} | {:.0}% |",
            r.name, r.a_win, r.b_win, r.draw, r.rounds, r.a_hp
        );
    }

    // How many enemies make the fight even (side 0 wins about half)?
    println!("\nРавный бой: сколько врагов нужно, чтобы армия выигрывала около половины боёв\n");
    println!("| Армия | Рабочих | Солдат | Воинов |");
    println!("|---|---|---|---|");
    let armies: Vec<(&str, Vec<Template>)> = vec![
        ("Страж", vec![strazh()]),
        ("Молот", vec![molot()]),
        ("Горн", vec![gorn()]),
        ("Орудие", vec![orudie()]),
        ("Молот и Орудие (лидерство 10)", vec![molot(), orudie()]),
        ("Страж и Механик (лидерство 10)", vec![strazh(), mekhanik()]),
        ("Старт Отца колосса", start_otets()),
        ("Старт Изобретателя", start_izobretatel()),
        ("Старт Маньяка", start_manyak()),
        ("Старт Зодчего", start_zodchiy()),
    ];
    let m = (n / 4).max(100);
    for (name, a) in armies {
        let even = |t: fn() -> Template, cap: usize| -> String {
            // smallest k with win rate <= 50%
            let (mut lo, mut hi) = (1usize, cap);
            if run("", &a, &many(t(), hi), m).a_win > 50.0 {
                return format!("больше {}", cap);
            }
            while lo < hi {
                let mid = (lo + hi) / 2;
                if run("", &a, &many(t(), mid), m).a_win > 50.0 {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            format!("{}", lo)
        };
        println!("| {} | {} | {} | {} |", name, even(rabochaya, 300), even(soldat, 160), even(voin, 80));
    }
}
