//! The state of one battle after a given round, as JSON (for drawing a screenshot).
//! `cargo run --release --bin snapshot -- <scenario> <seed> <round>`

use sim::data::*;
use sim::{Battle, Event};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let which = args.get(1).map(String::as_str).unwrap_or("zodchiy");
    let seed: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(1);
    let upto: u32 = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(4);
    let (title, a, b) = match which {
        "otets" => ("Старт Отца колосса против роя", start_otets(), swarm_start()),
        "izobretatel" => ("Старт Изобретателя против роя", start_izobretatel(), swarm_start()),
        "manyak" => ("Старт Маньяка против роя", start_manyak(), swarm_start()),
        "molot_orudie" => ("Молот и Орудие против 25 рабочих", vec![molot(), orudie()], many(rabochaya(), 25)),
        _ => ("Старт Зодчего против роя", start_zodchiy(), swarm_start()),
    };
    let mut bt = Battle::new(seed).with_log();
    bt.add_army(0, &a);
    bt.add_army(1, &b);
    let mut over = false;
    while bt.round < upto {
        if bt.step().is_some() {
            over = true;
            break;
        }
    }
    let log = bt.log.clone().unwrap();
    let start = log.iter().rposition(|e| matches!(e, Event::Round(_))).unwrap_or(0);
    let last = &log[start..];
    let mut hits = vec![];
    let mut kills = vec![];
    let mut absorbed = vec![];
    for e in last {
        match e {
            Event::Hit { a, t, dmg } => hits.push(format!("[{},{},{}]", a, t, dmg)),
            Event::Kill { t } => kills.push(t.to_string()),
            Event::Absorbed { t } => absorbed.push(t.to_string()),
            _ => {}
        }
    }
    let units: Vec<String> = bt
        .units
        .iter()
        .map(|u| {
            format!(
                "{{\"id\":{},\"name\":\"{}\",\"side\":{},\"x\":{},\"y\":{},\"size\":{},\"hp\":{},\"max\":{},\"alive\":{},\"on_field\":{},\"fleeing\":{},\"burn\":{}}}",
                u.id, u.t.name, u.side, u.x, u.y, u.t.size, u.hp, u.t.hp, u.alive, u.on_field, u.fleeing, u.burn
            )
        })
        .collect();
    println!(
        "{{\"title\":\"{}\",\"seed\":{},\"round\":{},\"over\":{},\"units\":[{}],\"hits\":[{}],\"kills\":[{}],\"absorbed\":[{}]}}",
        title,
        seed,
        bt.round,
        over,
        units.join(","),
        hits.join(","),
        kills.join(","),
        absorbed.join(",")
    );
}
