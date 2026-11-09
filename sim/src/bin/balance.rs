//! Runs every scenario many times and prints win rates.
//! `cargo run --release --bin balance -- 2000`

use rayon::prelude::*;
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
    let outcomes: Vec<_> = (0..n).into_par_iter().map(|seed| fight(a, b, seed)).collect();
    for o in outcomes {
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
        ("Мудрец против 10 рабочих", vec![mudrets()], workers(10)),
        ("Горн против 10 рабочих", vec![gorn()], workers(10)),
        ("Орудие против 10 рабочих", vec![orudie()], workers(10)),
        ("Страж против 4 солдат", vec![strazh()], many(soldat(), 4)),
        ("Мудрец против 4 солдат", vec![mudrets()], many(soldat(), 4)),
        ("Мудрец против 4 воинов", vec![mudrets()], many(voin(), 4)),
        ("Страж и Мудрец против 25 рабочих", vec![strazh(), mudrets()], workers(25)),
        ("Страж и Мудрец: рабочие, жуки, кислотники", vec![strazh(), mudrets()], {
            let mut v = many(rabochaya(), 12);
            v.extend(many(zhuk(), 6));
            v.extend(many(kislotnik(), 4));
            v
        }),
        ("Страж и Механик против 25 рабочих", vec![strazh(), mekhanik()], workers(25)),
        ("Страж и Механик: рабочие, жуки, кислотники", vec![strazh(), mekhanik()], metal_answer),
        ("Старт Отца колосса против 8 воинов", start_otets(), humans_squad()),
        ("Старт Изобретателя против 8 воинов", start_izobretatel(), humans_squad()),
        ("Старт Маньяка против 8 воинов", start_manyak(), humans_squad()),
        ("Старт Зодчего против 8 воинов", start_zodchiy(), humans_squad()),
        ("Старт Отца колосса против старта Матки", start_otets(), start_matka()),
        ("Старт Отца колосса против старта Разума улья", start_otets(), start_razum()),
        ("Старт Отца колосса против старта Пожирателя", start_otets(), start_pozhiratel()),
        ("Старт Отца колосса против старта Кукушки", start_otets(), start_kukushka()),
        ("Старт Изобретателя против старта Матки", start_izobretatel(), start_matka()),
        ("Старт Изобретателя против старта Разума улья", start_izobretatel(), start_razum()),
        ("Старт Изобретателя против старта Пожирателя", start_izobretatel(), start_pozhiratel()),
        ("Старт Изобретателя против старта Кукушки", start_izobretatel(), start_kukushka()),
        ("Старт Маньяка против старта Матки", start_manyak(), start_matka()),
        ("Старт Маньяка против старта Разума улья", start_manyak(), start_razum()),
        ("Старт Маньяка против старта Пожирателя", start_manyak(), start_pozhiratel()),
        ("Старт Маньяка против старта Кукушки", start_manyak(), start_kukushka()),
        ("Старт Зодчего против старта Матки", start_zodchiy(), start_matka()),
        ("Старт Зодчего против старта Разума улья", start_zodchiy(), start_razum()),
        ("Старт Зодчего против старта Пожирателя", start_zodchiy(), start_pozhiratel()),
        ("Старт Зодчего против старта Кукушки", start_zodchiy(), start_kukushka()),
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
    println!("| Армия | Эталонов | Рабочих | Солдат |");
    println!("|---|---|---|---|");
    let armies: Vec<(&str, Vec<Template>)> = vec![
        ("Мудрец и Орудие (лидерство 10)", vec![mudrets(), orudie()]),
        ("Страж и Мудрец (лидерство 12)", vec![strazh(), mudrets()]),
        ("Страж и Механик (лидерство 10)", vec![strazh(), mekhanik().with(remont())]),
        ("Старт Отца колосса", start_otets()),
        ("Старт Изобретателя", start_izobretatel()),
        ("Старт Маньяка", start_manyak()),
        ("Старт Зодчего", start_zodchiy()),
        ("Старт Матки", start_matka()),
        ("Старт Разума улья", start_razum()),
        ("Старт Пожирателя", start_pozhiratel()),
        ("Старт Кукушки", start_kukushka()),
    ];
    let m = (n / 4).max(100);
    for (name, a) in armies {
        let even = |make: &dyn Fn(usize) -> Vec<Template>, cap: usize| -> String {
            let (mut lo, mut hi) = (1usize, cap);
            if run("", &a, &make(hi), m).a_win > 50.0 {
                return format!("больше {}", cap);
            }
            while lo < hi {
                let mid = (lo + hi) / 2;
                if run("", &a, &make(mid), m).a_win > 50.0 {
                    lo = mid + 1;
                } else {
                    hi = mid;
                }
            }
            format!("{}", lo)
        };
        println!(
            "| {} | {} | {} | {} |",
            name,
            even(&|k| etalon(k), 84),
            even(&|k| many(rabochaya(), k), 300),
            even(&|k| many(soldat(), k), 160)
        );
    }
}
